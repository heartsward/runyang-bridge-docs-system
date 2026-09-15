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

## 十、文档内容提取引擎（阶段十九更新：2026-09-13）

后端文档提取由 `backend/app/services/extraction/` 模块统一处理。
**阶段十九起 anydoc 为所有文档格式的首选引擎**（纯 Rust，毫秒级，LibreOffice 链路彻底退役）：

```
所有文档 → AnyDocExtractor（anydoc 首选，21 格式）
  ├─ 成功且内容 ≥20 字 → 直接用（engine=anydoc）
  └─ 失败/空 → 降级本地引擎（安全网）：
       .pdf  → PdfExtractor（多模态 AI 优先 + pymupdf 兜底）
       .xlsx/.xls → XlsxExtractor（openpyxl；.xls 本地不支持，报错提示另存）
       .docx/.doc → DocxExtractor（python-docx；.doc 本地不支持，报错提示另存）
       .txt 等 → TextExtractor
       图片  → ImageExtractor（多模态 AI 优先 + OCR 兜底，router 直接分发不经 anydoc）
```

| 格式 | 首选引擎 | 本地安全网 |
|------|---------|-----------|
| .xls/.xlsx/.xlsm/.xlsb | **anydoc** | openpyxl（仅 .xlsx；.xls 不支持） |
| .doc/.docx/.docm | **anydoc** | python-docx（仅 .docx；.doc 不支持） |
| .ppt 系/.odt/.ods/.odp/.rtf/.epub/.csv | **anydoc** | —（无本地引擎，失败即报错） |
| .pdf | **anydoc**（文本层，<5ms） | 多模态 AI（扫描件）→ pymupdf |
| .png/.jpg/.jpeg 等图片 | ImageExtractor（多模态 AI 优先） | tesseract OCR |
| .txt/.md 等纯文本 | TextExtractor（anydoc 不覆盖） | — |

> **阶段二十六·26.3**：上传白名单 `ALLOWED_EXTENSIONS` 定为 22 种（Word 3 + Excel 4 + PPT 7 + .epub/.csv/.pdf + 图片 3 + .txt/.md）。**`.json` 不支持**（anydoc 无法把 JSON 转 Markdown，用户拍板移除）。PPT 7 种（.ppt/.pptx/.pptm/.pps/.ppsx/.ppsm/.pot）提取走 anydoc、"原文件"预览走 LibreOffice 转 PDF，均无需新增代码。

**anydoc 依赖**:`firecrawl-anydoc>=0.2.4`(纯 Rust 单 wheel ~3.6MB,`pip install` 即得,无系统依赖、无需装 LibreOffice)。
来源:https://github.com/firecrawl/anydoc(MIT)。支持 14 格式族 21 扩展名;PDF 仅文本层提取(扫描件走我们的多模态 AI,不用其付费 hosted OCR)。

**引擎切换**(`backend/app/core/config.py`):
- `AI_SERVICE_ENABLED`: 控制扫描件/图片是否走多模态 AI(anydoc 本身不需要 AI)
- `AI_FALLBACK_TO_LOCAL`: AI 失败时是否降级本地
- `PDF_ENGINE` / `OCR_ENGINE` / `MINERU_ENABLED` / `PADDLEOCR_LANG`: 本地引擎内部切换(保留)
- ~~`AI_ALL_FORMATS_AI`~~:**阶段十九已移除**(anydoc 已是全格式首选引擎,"全格式 AI 规整"开关无意义)

**⚠️ LibreOffice 全面禁用（阶段二十六·26.11）**：
- 用户决定回退整个 Office→PDF 预览功能后，**项目中不再使用 LibreOffice / soffice / 任何本地 Office 转 PDF 方案**
- 删除了 `preview_converter.py`、`/converted-pdf` 端点、`OFFICE_EXTENSIONS` 判断、`shouldShowViewToggle` 对 Office 类的判断、`LIBREOFFICE_BIN_PATH` / `PREVIEW_CONVERT_TIMEOUT` 配置等
- 文档处理走"提取内容"模式（anydoc 转 markdown）+ 用户下载原文件查看
- **长期约束**：新功能禁止引入 LibreOffice 依赖；如未来真需要 Office 在线预览，必须选 SaaS 路线（如 OnlyOffice、Collabora Online）

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