# @tech-stack.md — 技术栈

> ⚠️ AI 在写任何代码前必须完整阅读本文件。
> 依据：`VIBE_CODING_GUIDE.md` 阶段二，要求"最简单但最健壮"的栈。
> 本栈以仓库**实际依赖**为准（README 声明 + 文件实际 import 校验），不引入未经评估的新依赖。

---

## 一、栈总览

```
┌──────────────┐   HTTP/JSON   ┌───────────────────┐   SQLAlchemy   ┌──────────┐
│  Frontend    │ ────────────▶ │     Backend       │ ─────────────▶ │  SQLite  │
│ Vue 3 + TS   │               │    FastAPI        │                │ (本地)   │
│ + Naive UI   │ ◀──────────── │    + Python       │ ◀───────────── │          │
└──────────────┘               │  ┌─────────────┐  │                └──────────┘
       │                       │  │ AI Wiki MCP │  │  FTS5 索引
       │ 浏览器                 │  │ ( /mcp )    │  │
       ▼                       │  └──────┬──────┘  │
┌──────────────┐               │         │ HTTP    │
│ AI 工作台     │ ──MCP──▶      │         ▼         │
│ (WorkBuddy)  │  数据查询      │  ┌──────────────┐ │
│              │  与利用        │  │  统一多模态AI │ │
└──────────────┘               │  │ llama.cpp +  │ │
                               │  │ Qwen3-VL     │ │
                               │  └──────────────┘ │
                               └───────────────────┘
```

---

## 二、前端 (frontend/)

| 项 | 选型 | 版本要求 | 备注 |
|----|------|----------|------|
| 框架 | Vue 3 | 3.5+ | Composition API |
| 语言 | TypeScript | 5.8+ | 严格类型 |
| 构建 | Vite | 7.0+ | 端口 5173 |
| UI 库 | Naive UI | 2.42+ |  |
| 状态 | Pinia | 最新 |  |
| 路由 | Vue Router | 4 | `meta.requiresAuth / requiresGuest` 控制守卫 |
| HTTP | Axios | 最新 | 拦截器统一处理 token 与错误 |
| 图标 | @vicons/ionicons5 + @vicons/antd |  |  |
| XSS 防护 | 自实现 utils/xss-protection.ts |  | 不引入 DOMPurify 减小体积 |

**为什么选这个栈**
- Vue 3 + Vite 启动快、HMR 体验好
- Naive UI 自带 TypeScript 类型与暗色主题，省去自研样式
- Pinia 取代 Vuex，API 更简洁

**严禁随意引入**
- ❌ 新的 UI 库（Element Plus、Ant Design Vue）— 改样式需统一协调
- ❌ 新的状态管理（Vuex、Redux）
- ❌ 新的 HTTP 客户端（fetch 包装、ky、umi-request）
- ❌ jQuery / Lodash 全量（按需 import）

---

## 三、后端 (backend/)

| 项 | 选型 | 备注 |
|----|------|------|
| 语言 | Python | 3.8+（推荐 3.9+） |
| 框架 | FastAPI | 0.104+ |
| ORM | SQLAlchemy | 2.0（同步） |
| 数据库 | SQLite | 本地文件，**生产可迁 PostgreSQL** |
| 认证 | PyJWT | 24h 过期 |
| 密码 | Bcrypt |  |
| 异步 | AsyncIO（仅在 I/O 密集处） | 数据库同步 |
| 校验 | Pydantic | V2 |
| Web 服务器 | Uvicorn | ASGI，端口 8002 |
| 文档处理 | PyPDF2 + python-docx + openpyxl + LibreOffice | LibreOffice 必需 |
| OCR | Tesseract（可选） |  |
| 跨域 | FastAPI CORS | 白名单 |

**目录规则**
```
backend/app/
├── api/            # 路由（薄）
│   ├── api_v1.py   # 聚合
│   └── endpoints/  # 各模块端点
├── core/           # 基础设施（config、security、deps、cache、search_engine）
├── crud/           # 数据库 CRUD
├── models/         # SQLAlchemy 模型
├── schemas/        # Pydantic 模式
├── services/       # 业务服务
│   └── ai/         # AI 子系统
├── db/             # engine、Session、Base
└── utils/          # 纯函数工具
```

**严禁随意引入**
- ❌ 新的 ORM（Django ORM、Tortoise、Peewee）
- ❌ 切换到 MongoDB / Redis（除非明确性能瓶颈论证）
- ❌ 新增重量级框架（Celery、dramatiq）— 优先用 `services/background_tasks.py` + 状态文件
- ❌ 新 AI Provider 必须先实现 `services/ai/providers/base_provider.py` 接口

---

## 四、AI 子系统 (backend/app/services/ai/)

设计：**Provider 抽象 + 工具能力**

```
ai/
├── base_provider.py       # 抽象接口（必须实现 chat/embed/stream）
├── providers/
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── alibaba_provider.py
│   ├── zhipu_provider.py
│   └── MiniMax_provider.py
├── ai_config.py / ai_config_service.py
├── extractors/
│   ├── asset_extractor.py
│   └── document_analyzer.py
└── utils/
    ├── cache_manager.py
    ├── rate_limiter.py
    └── cost_tracker.py
```

**约束**
- 所有 Provider 必须继承 `BaseProvider` 并实现统一接口
- 调用必须经过 `rate_limiter` 与 `cost_tracker`
- 结果必须经过 `cache_manager`（按 key 哈希）

---

## 五、AI Wiki MCP — 数据查询服务（替代原 Android 客户端）

> 2026-09-12 起：Android 客户端已移除（用户决策：由 AI 工作台接入 Wiki MCP 做数据查询与利用）。

| 项 | 选型 | 备注 |
|----|------|------|
| 协议 | MCP (Model Context Protocol) | FastMCP 4.x，HTTP transport |
| 挂载 | `http://<host>:8002/mcp` | 合并进主 FastAPI 应用（`main.py`） |
| 索引 | SQLite FTS5 | `backend/app/services/wiki/index.py` |
| 数据源 | MD 副本 | `backend/wiki/{doc_id}.md` + frontmatter |
| tools | 6 个 | search_kb / get_doc / get_doc_content / list_backlinks / list_tags / generate_report |
| 接入方 | WorkBuddy 等 AI 工作台 | 配置 MCP server 指向 `/mcp` |

**约束**
- MCP server 复用主应用 lifespan，不独立进程
- 不引入向量库（当前仅 FTS5）
- 新增 tool 必须在 `wiki/mcp_server.py` 的 `register_tools` 中注册

---

## 六、数据存储

| 数据 | 存储 |
|------|------|
| 关系数据（用户/文档/资产/AI 配置/系统配置） | SQLite（`yunwei_docs.db` 或 `*_clean.db`） |
| 文件原件与提取内容 | 本地文件系统 `./uploads/` |
| 后台任务状态 | `task_status/` JSON 文件 |
| 缓存 | 内存缓存（`core/cache.py`、`ai/utils/cache_manager.py`） |
| 会话 | JWT（无状态） |
| 日志 | 结构化文件（`log_manager.py`） |

---

## 七、构建与启动

### 开发
```bash
# 后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# 前端
cd frontend
npm run dev   # 端口 5173
```

### Windows 一键
```
start-services.bat
install-complete.bat
stop-services.bat
```

### 生产
- 前端：`npm run build` → 静态产物 + Nginx
- 后端：Gunicorn + UvicornWorker

---

## 八、安全栈

- JWT（24h 自动过期）
- Bcrypt 密码哈希
- CORS 白名单（仅允许前端 dev/prod 域名）
- 文件白名单（PDF/DOC/DOCX/XLSX/XLS/TXT/MD）+ 10MB 上限
- 前端 XSS 过滤（`utils/xss-protection.ts`）
- SQLAlchemy 防注入
- 关键操作审计（`log_manager.py`）

---

## 九、依赖升级策略

1. 升级前必须先在本地 dev 环境跑通单元/集成测试
2. 升级到 major 版本必须更新对应 `@*.md` 中的版本记录
3. AI Provider SDK 升级需校验 `base_provider.py` 接口兼容性
4. 不引入与栈"严禁随意引入"清单冲突的依赖

---

## 十、文档内容提取引擎（阶段四：2026-09-11）

后端文档提取由 `backend/app/services/extraction/` 模块统一处理：

| 格式 | Extractor | 实现方式 |
|------|-----------|---------|
| .xlsx | XlsxExtractor | openpyxl 直读 → GFM 表格（无合并）/ HTML 表格（含合并） |
| .xls | XlsxExtractor | LibreOffice 临时转 xlsx → openpyxl 处理 |
| .docx | DocxExtractor | python-docx 直读 → 标题/段落/表格 |
| .pdf | PdfExtractor | pymupdf 主路径 + PaddleOCR 兜底（扫描件） |
| .png/.jpg/.jpeg | ImageExtractor | PaddleOCR (默认) / pytesseract (兜底) |
| .txt/.md/.csv 等 | TextExtractor | UTF-8/GBK 容错读取 |

**引擎切换**（`backend/app/core/config.py`）：
- `PDF_ENGINE`: `pymupdf` (默认) | `mineru` (需 GPU + MinerU 安装)
- `OCR_ENGINE`: `tesseract` (默认) | `paddleocr` (中文 OCR 精度更高)
- `MINERU_ENABLED`: `False` (默认，待用户配置后启用)
- `PADDLEOCR_LANG`: `ch` (中文模型)

**MinerU 集成（阶段四规划）**：
- MinerU 是 2026 年中文文档提取 SOTA（Apache-2.0 + 商业附加条款）
- 集成代码骨架已就位（`PdfExtractor._extract_with_mineru`），调用需安装 `mineru[all]` + GPU
- 参考：https://github.com/opendatalab/MinerU

**PDF 增强功能**：
- 章节标题识别（第X章、Chapter 1、1.1 等 8 种模式）→ Markdown # / ##
- 页眉页脚去除（页码模式 + 跨页重复检测）
- 文档元数据提取（标题/作者/创建日期）
- JSON 结构化输出（含章节列表、页码范围）

---

_生成时间：2026-09-11_
_下次更新时机：技术栈发生变更后（添加/删除/升级依赖）_