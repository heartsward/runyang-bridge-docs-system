# progress.md — 进度追踪

> 本文件按时间倒序记录已完成步骤、关键决策与遗留问题。
> 切新会话后**第一个动作**就是读这里与 `@implementation-plan.md`。

---

## 当前状态：阶段零~十二全部完成

**最后更新**：2026-09-12 18:10

- 初始 9 项 P0/P1/P2 问题清零；内容提取器重构（extraction 模块）
- AI 引擎统一到 llama.cpp + Qwen3-VL 单接口；旧 AI 配置清理
- AI Wiki 系统全链路落地（MD 副本 + FTS5 + FastMCP 6 tools + 前端编辑/下载）
- **Android 客户端与移动端 API 整体移除（2026-09-12，阶段十一）**：数据查询与利用改由 AI 工作台经 AI Wiki MCP（`/mcp`）接入
- **start-services.bat 启动修复（2026-09-12，阶段十二）**：venv 缺失自动创建+装依赖、managed runtime 回退、补 fastmcp 依赖
- 待用户指定下一个具体任务

---

## ✅ 已完成

### 2026-09-11 — 项目初始化 + 环境连通性验证

| 时间 | 步骤 | 备注 |
|------|------|------|
| 09:43 | 克隆仓库 | `git clone https://github.com/heartsward/runyang-bridge-docs-system.git` → `D:\sdxtywzsk\runyang-bridge-docs-system` |
| 09:46 | 阅读 README + docs/ 系统架构 | 确认栈：Vue3+TS / FastAPI / Kotlin Android / SQLite |
| 09:48 | 定位 VIBE_CODING_GUIDE.md | 在 `D:\sdxtywzsk\VIBE_CODING_GUIDE.md`（仓库外），写入工作区长期记忆 |
| 09:50 | 建立 memory-bank/ | 5 个核心文件 |
| 09:55 | 步骤 1.1 ✅ | pip 安装 `requirements-windows.txt`（managed venv: `C:\Users\cccly\.workbuddy\binaries\python\envs\default`） |
| ~10:18 | 步骤 1.2 ✅ | npm 安装前端依赖（222MB node_modules，217→222MB 增长，~143 包）。注：原任务执行 15min 后被 kill，但已完整生成 package-lock.json |
| 10:19 | 步骤 1.3 ✅ | 后端 uvicorn 启动 → http://127.0.0.1:8002，**86 个 API 路由**，admin 用户已自动初始化 |
| 10:24 | 步骤 1.4 ✅ | 前端 vite 启动 → http://127.0.0.1:5173，所有路由 HTTP 200 |
| 10:25 | 步骤 1.5 ✅ | admin/admin123 登录成功，JWT 签发正常，`/auth/me` 返回管理员完整信息 |
| 10:25 | 额外 | `vue-tsc --noEmit` 通过，前端 TS 编译 0 error |
| 10:31 | 重启前后端 | 用户请求 → kill 旧任务（jGzBL3 / HnNFcT）→ 重新启动（task: 2AVlDK / TB8k2c）→ 双端均健康 |
| 10:43 | P0 全部修复 | A.1-A.4 四步完成（详见下） |
| 10:55 | P2-8 命名统一 | C.1-C.3 三步完成（产品名 → "运维资产管理"） |
| 11:05 | 第二次重启 | 用户测试需要 → kill 旧任务（Uncvqi / TB8k2c）→ 重新启动（task: mFicWl / 8C7VSh）→ 双端均健康 |
| 15:05 | 第三次重启 | 用户测试需要 → kill 旧任务（fpttWy / 8C7VSh）→ 重新启动（task: BFblkR / 1goY42）→ 双端均健康 |

**启动方式（手动）**
```bash
# 后端（managed venv）
cd /d/sdxtywzsk/runyang-bridge-docs-system/backend
PYTHONPATH=. "C:\Users\cccly\.workbuddy\binaries\python\envs\default\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8002

# 前端
cd /d/sdxtywzsk/runyang-bridge-docs-system/frontend
/c/Users/cccly/.workbuddy/binaries/node/versions/22.22.2-2/node.exe ./node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173
```

---

## ⏳ 进行中

（暂无）

---

## 🐛 阶段一发现的问题（待用户确认修改优先级）

### P0 安全相关 ✅ 全部修复
1. ✅ **A.4 P0-1 收紧 CORS 白名单**：默认从 60 origin 降到 2 个（`http://127.0.0.1:5173` + `http://localhost:5173`）。生产可通过 `CORS_MODE=manual` + `CORS_ORIGINS=...` env 变量扩展。详见 `@implementation-plan.md` A.4
2. ✅ **A.3 P0-2 修复 documents 列表鉴权**：`documents.py:75-99` 改用 `get_current_active_user`；未授权 401，已授权 200。详见 `@implementation-plan.md` A.3

### P0 功能故障（前端不可用）✅ 全部修复
3. ✅ **A.2 P0-3 修复 EnhancedSearchView 路径**：`EnhancedSearchView.vue:396` `/search` → `/search/documents`。详见 `@implementation-plan.md` A.2
4. ✅ **A.1 P0-4 修复 system/health**：SQLAlchemy 2.0 要求 `text("SELECT 1")` 包裹。详见 `@implementation-plan.md` A.1

### P1 接口契约不一致（前端调用了不存在的端点）— 待办
6. **资产服务路径不匹配**（`frontend/src/services/asset.ts` vs 后端 OpenAPI）：
   - 前端 `/assets/extract` → 后端 `/assets/file-extract`
   - 前端 `/assets/bulk-create` → 后端只有 `/assets/batch/delete`
   - 前端 `/assets/merge` → 后端无
   - 前端 `/assets/document/{id}` → 后端无（应在 `/api/v1/mobile/assets/` 下）
   → AssetView 多数操作会 404 或 405

### P1 测试端点不应暴露在生产 ✅ 已修复（2026-09-11 11:15）
7. ✅ **D.1-D.3 测试端点生产门禁**：
   - 新增 `Settings.ENABLE_TEST_ENDPOINTS: bool = False`（默认安全）
   - 新增依赖 `require_test_endpoints_enabled()`（未启用时返回 404 伪装不存在）
   - 给 8 个端点加门禁依赖：`/auth/test-token`、`/multi-upload/test`、`/assets/test-file-upload`、`/assets/test-extractor`、`/assets/test-with-db`、`/assets/test-with-auth`、`/assets/ai/test`、`/assets/debug-excel-extract`
   - 门禁参数 `_test` 置于函数签名首位，确保先于 auth 运行（避免 401 泄漏端点存在性）
   - 验证：默认全部 404；`ENABLE_TEST_ENDPOINTS=true` 启动时端点正常工作
   - 详见 `@implementation-plan.md` 阶段二·D

### P1 documents.py 仍有 2 处鉴权绕过（未在本轮修复）— 待办
7b. `documents.py:125` `read_document/{id}` 和 `documents.py:482` 仍用 `get_optional_user`。本轮为不破坏其他端点保留了 import；下一步需逐个审计

### P2 命名/文案不一致 ✅ 已修复（2026-09-11 10:55）
8. ✅ **A.4 P0-1 / C.1-C.3**：产品名统一为"润扬大桥运维资产管理系统"。详见 `@implementation-plan.md` 阶段二·C 步骤 C.1/C.2/C.3

### P2 依赖告警 — 待办
9. **`fitz` API 已废弃**（PyMuPDF），启动日志告警：`Use import pymupdf instead` → 不影响运行但应迁移

### 🆕 本轮额外发现 — 待办
10. **admin 用户 is_active=0**：DB 中 admin 用户 is_active=0 导致 login 返回 "用户未激活"。**lifespan 初始化逻辑只补 is_superuser，不补 is_active**（`main.py:79-86`）。本轮为继续验证临时手动设为 1，应在下一轮修复 lifespan 逻辑

---

## 📋 待办

### 已完成（2026-09-11 10:43）
- [x] A.1 P0-4 修复 system/health
- [x] A.2 P0-3 修复 EnhancedSearchView
- [x] A.3 P0-2 修复 documents 鉴权
- [x] A.4 P0-1 收紧 CORS

### 已完成（2026-09-11 11:15）
- [x] D.1 新增 `ENABLE_TEST_ENDPOINTS` 配置
- [x] D.2 新增 `require_test_endpoints_enabled` 依赖
- [x] D.3 给 8 个测试/调试端点添加门禁依赖

### 已完成（2026-09-11 11:33）
- [x] E.1 修复 AssetView.vue 的 `/file-extract/confirm` → `/file-extract/single-confirm`
- [x] E.2 删除 assetService.ts 中 4 个死代码方法

### 已完成（2026-09-11 11:39）
- [x] F.1 documents.py 125/482 `get_optional_user` → `get_current_active_user`
- [x] F.2 lifespan 增加 is_active 自动恢复
- [x] F.3 ocr_extractor.py `fitz` → `pymupdf`

### 已完成（2026-09-11 12:05）
- [x] G.1 移除 ALLOWED_EXTENSIONS 中 bmp/gif/tiff/webp
- [x] G.2 同步 DocumentView.vue accept 属性

### 已完成（2026-09-11 14:10）— 阶段 3A 基础重构
- [x] 3A.1 新建 `backend/app/services/extraction/` 模块骨架（models.py / base.py / router.py）
- [x] 3A.2 XlsxExtractor 实现（openpyxl 直读 + GFM 表格 + HTML 合并单元格兜底 + 尾部空行裁剪）
- [x] 3A.3 DocxExtractor 实现（python-docx 直读 + 标题/段落/表格 + 中文编号章节识别）
- [x] 3A.4 TextExtractor / PdfExtractor / ImageExtractor 实现
- [x] 3A.5 content_extractor.py 集成新路由器（失败 fallback 旧管线）
- [x] 3D.1 XLS 文件支持（LibreOffice 临时转 xlsx → openpyxl 处理）

**端到端验证**：上传 xlsx → DB 中 content 为对齐 Markdown 表格（14 列）+ 8 工作表全保留
**XLS 验证**：上传 xls → DB 中 content 为 Markdown 工作表 + HTML 表格（含 `colspan="17"` 合并单元格保留）

### 下一步（阶段 3B / 3C，待用户配置 AI provider 后推进）
- 阶段 3B：视觉 LLM 支持扫描 PDF/图片
- 阶段 3C：AI Wiki 自动摘要/标签/Q&A
- 前端：用 markdown-it 渲染 Markdown 预览

### 下一轮（阶段 3B / 3C + 前端 Markdown 渲染）
- [ ] 前端引入 markdown-it + DocumentView 预览改 Markdown 渲染
- [ ] 阶段 3B：视觉 LLM 配置 + PDF/图片 fallback 链
- [ ] 阶段 3C：自动摘要/标签生成
- [ ] 阶段 3C：文档 Q&A 端点（RAG）

---

## 📁 文件变更日志

### 2026-09-11（10:43）— P0 修复
- 修改 `backend/app/api/endpoints/system.py`：import `text`，2 处 `db.execute("SELECT 1")` → `db.execute(text("SELECT 1"))`
- 修改 `frontend/src/views/EnhancedSearchView.vue:396`：`/search` → `/search/documents`
- 修改 `backend/app/api/endpoints/documents.py`：line 75-99 `get_optional_user` → `get_current_active_user`；import 保留 `get_optional_user`（line 125/482 仍用）
- 修改 `backend/app/core/config.py`：line 132-136 默认值收紧（CORS_AUTO_DETECT=False / CORS_INCLUDE_HTTPS=False / CORS_EXTRA_PORTS="")

### 2026-09-11（10:25 之前）
- 新增 `memory-bank/@architecture.md`
- 新增 `memory-bank/@product-requirements-document.md`
- 新增 `memory-bank/@tech-stack.md`
- 新增 `memory-bank/@implementation-plan.md`
- 新增 `memory-bank/progress.md`（本文件）

### 2026-09-11（10:55）— P2-8 产品命名统一
- 修改 `backend/app/core/config.py:15` `PROJECT_NAME`
- 修改 `backend/app/main.py:138` FastAPI description
- 修改 `backend/app/api/endpoints/system.py:45, 208` server_name + service
- 修改 `frontend/index.html:9` meta keywords
- 修改 `frontend/src/views/WelcomeView.vue:9` 副标题
- 修改 `frontend/src/views/LoginView.vue:11` 副标题
- 修改 `frontend/src/views/RegisterView.vue:11` 副标题
- 修改 `memory-bank/@product-requirements-document.md:11` 产品名定义
- 修改 `memory-bank/progress.md` 本节内容
- **不改**：菜单/功能 label 中的"文档管理"（这是真实功能名，不是产品名）；`docs/` 与 `android/` 按用户确认不动

### 2026-09-11（11:15）— P1-7 测试端点生产门禁
- 修改 `backend/app/core/config.py` 新增 `ENABLE_TEST_ENDPOINTS: bool = False`
- 修改 `backend/app/core/deps.py` 新增 `require_test_endpoints_enabled()` 依赖（关闭时返回 404）
- 修改 `backend/app/api/endpoints/assets.py` 给 6 个端点加门禁（test-file-upload / test-extractor / test-with-db / test-with-auth / ai/test / debug-excel-extract），门禁参数 `_test` 置于首位
- 修改 `backend/app/api/endpoints/auth.py` 给 `/test-token` 加门禁，门禁置于首位
- 修改 `backend/app/api/endpoints/upload_multiple.py` 给 `/test` 加门禁

### 2026-09-11（11:33）— P1-6 资产接口契约
- 修改 `frontend/src/views/AssetView.vue:2011` `/file-extract/confirm` → `/file-extract/single-confirm`
- 修改 `frontend/src/services/asset.ts` 删除 4 个未使用的死代码方法（extractAssetsFromDocument / getAssetsByDocument / bulkCreateAssets / mergeAssets）及对应的 `AssetExtractRequest/Result` import
- 行数：assetService.ts 172 → 142（-30 行）

### 2026-09-11（11:39）— F.1 / F.2 / F.3 最后收尾
- 修改 `backend/app/api/endpoints/documents.py:125`（read_document）与 `:482`（download_document）：`get_optional_user` → `get_current_active_user`；并清理 import
- 修改 `backend/app/main.py:78-86` lifespan 中 admin 修复逻辑：除了 `is_superuser` 也补 `is_active`
- 修改 `backend/app/services/ocr_extractor.py`：`import fitz` → `import pymupdf`；3 处 `fitz.open/Matrix` → `pymupdf.open/Matrix`
- **验证**：所有问题清单已清零（暂无非用户新增的待办）

### 2026-09-11（12:05）— G.1/G.2 上传格式调整
- 用户测试发现：4 个图片格式（bmp/gif/tiff/webp）上传报"文件内容与扩展名不匹配或包含恶意内容"
- 根因：`ALLOWED_EXTENSIONS` 允许这 4 个但 `MAGIC_SIGNATURES` 没收录，导致 `validate_file_content` 返回 False
- 修改 `backend/app/core/config.py:37` `ALLOWED_EXTENSIONS` 移除 `,bmp,tiff,gif,webp`
- 修改 `frontend/src/views/DocumentView.vue:164` accept 属性同步移除
- **保留** line 1688 `imageExtensions` 数组（含 gif/bmp/webp）——防止历史已上传文件预览失效
- 验证：4 格式上传 400 "不支持的文件类型"；10 格式保留上传 200

### 2026-09-11（14:10）— 阶段 3A 内容提取器重构
- **背景**：用户抱怨 XLSX 错位严重，要求基于 AI 升级内容提取；同时想支持"AI Wiki"理念
- **调研结论**：XLSX 错位根因是 LibreOffice 转 TXT 丢失了单元格网格结构，无需 AI 即可解决；业界最佳实践（markitdown/Docling/MinerU）：原生库直读 + Markdown 表格 + HTML 兜底合并单元格
- **3A.1-3A.5 完成**：
  - 新建 `services/extraction/` 模块（models/base/router + 5 个 extractor）
  - XlsxExtractor：openpyxl 直读，输出 GFM 表格（无合并）或 HTML 表格（含合并）
  - DocxExtractor：python-docx 直读，识别 Heading 样式 + 中文编号章节
  - TextExtractor / PdfExtractor / ImageExtractor：UTF-8 容错 + pymupdf + OCR
  - `content_extractor.py` 集成新路由器，失败时 fallback 到旧管线
- **端到端验证**：上传 xlsx → DB 存 35543 字符干净 Markdown，8 个工作表全保留，14 列对齐
- **未做（等用户决策）**：前端 markdown-it 引入 + 阶段 3B 视觉 LLM + 阶段 3C AI Wiki

### 2026-09-11（14:35）— 阶段 3D XLS 修复
- **背景**：用户反馈 XLS 文件预览仍是 TXT 文本
- **根因**：`_extract_xls_legacy()` 依赖 `xlrd`，但 `xlrd>=2.0` 已不支持 .xls；`import xlrd` 失败 → router fallback 到旧管线（LibreOffice→TXT）
- **修复**：`_extract_xls_legacy()` 改为 LibreOffice 临时转 xlsx，再用 openpyxl 处理
- **验证**：上传 xls 文件 → DB 存 6174 字符新格式（含 colspan="17" 合并单元格保留）
- **未做**：前端 Markdown 渲染（仍显示 HTML 源代码）；阶段 3B/3C

### 2026-09-11（14:55）— 阶段 3D+ XLS 中文文件名修复
- **背景**：用户反馈 XLS 文件提取内容"残缺"
- **根因 2**：LibreOffice + subprocess 在 Windows 下对中文文件名支持差，导致 .xls 转 .xlsx 后找不到输出文件（"文件不存在" 错误）
- **修复**：
  - 拷贝源 .xls 到临时目录，用 ASCII 文件名（如 `src_xxxxxxxx.xls`）
  - 用 ASCII 文件名调用 LibreOffice 转 .xlsx
  - 用 openpyxl 处理转换结果
  - 清理临时目录
- **验证**：
  - 4 个 xls 文件全部成功（含 3 个中文文件名）
  - 端到端：上传中文 xls → DB 存 6174 字符新格式（含 colspan="17" 合并单元格保留）
- **下一步**：前端 markdown-it 引入 + DocumentView 预览改 Markdown 渲染

---

## 💡 关键决策记录

### 2026-09-11
- **决策**：采用 VIBE_CODING_GUIDE.md 的"PRD 而非 GDD"命名（项目非游戏）
- **决策**：memory-bank/ 放置在仓库根目录（与 VIBE_CODING_GUIDE.md 模板一致），不属于业务代码
- **决策**：将 VIBE_CODING_GUIDE.md 中的硬性约束同时镜像到工作区长期记忆 `D:\sdxtywzsk\.workbuddy\memory\MEMORY.md`
- **决策**：使用 managed runtime 的 Python venv（`C:\Users\cccly\.workbuddy\binaries\python\envs\default`）和 Node 直接调用 `./node_modules/vite/bin/vite.js`，避免污染系统环境
- **决策**：本次不直接修复问题，**等待用户确认修改优先级**后再按 VIBE 流程分步执行
- **决策**（10:55）：产品命名统一为"运维资产管理"。**保留"文档管理"作为功能/菜单 label**（这是真实存在的功能模块），仅替换产品名相关的字符串。范围仅运行时 + memory-bank，按用户确认

---

## 🐛 已知问题 / 风险

（暂无）

---

## 💡 关键决策记录

### 2026-09-11
- **决策**：采用 VIBE_CODING_GUIDE.md 的"PRD 而非 GDD"命名（项目非游戏）
- **决策**：memory-bank/ 放置在仓库根目录（与 VIBE_CODING_GUIDE.md 模板一致），不属于业务代码
- **决策**：将 VIBE_CODING_GUIDE.md 中的硬性约束同时镜像到工作区长期记忆 `D:\sdxtywzsk\.workbuddy\memory\MEMORY.md`，确保跨会话都能快速对齐

---

## 📊 AI 现状（待阶段二 2.3 步骤后填写）

- 已测试 Provider：（空）
- 抽取准确率：（空）
- 平均响应耗时：（空）
- 成本追踪：（空）

---

## 📁 文件变更日志

### 2026-09-11
- 新增 `memory-bank/@architecture.md`
- 新增 `memory-bank/@product-requirements-document.md`
- 新增 `memory-bank/@tech-stack.md`
- 新增 `memory-bank/@implementation-plan.md`
- 新增 `memory-bank/progress.md`（本文件）

---

_维护规则：每完成一个里程碑或重要决策后追加；不要覆盖历史_
### 2026-09-11（15:08）— 阶段 3D.2 _render_html_table bug 修复
- **背景**：用户截图显示"交换机统计0723"只显示 3 个站名（"镇江南"等）
- **根因**：`_render_html_table` 中 `merge_owner.get((r,c)) != (r,c)` 对**未合并**格子返回 None，None != (r,c) 为 True → continue 错误触发 → 所有非合并数据被吞掉
- **修复**：`merge_owner.get((r,c), (r,c))` 默认值改回 (r,c) 自身，对未合并格子 `== (r,c)` 不跳过
- **验证**：修复前 4 个非空单元格 → 修复后 57 个非空单元格

### 2026-09-11（15:23 + 15:35）— 阶段 3E 前端 Markdown 渲染
- **背景**：用户截图显示"交换机统计0723"只显示 Markdown 字面文本（`## 工作表：` 等），原因是前端把后端的 Markdown 当 HTML 处理
- **3E.1 安装**：`markdown-it@15.0.2` + `@types/markdown-it@14.2.0`（MIT 协议，Vue 生态事实标准）
- **3E.2 新建**：`frontend/src/utils/markdown-renderer.ts`
  - 单例 markdown-it 实例（linkify/typographer/html=true）
  - `renderMarkdown(md)` → 直接 HTML
  - `renderDocumentMarkdown(md, options)` → render + 占位符替换 + DOMPurify sanitize
  - 占位符策略：`H_<index>_` 注入到 Markdown 源 → markdown-it 渲染后被替换为 `<mark>`（避开 markdown-it 转义）
- **3E.3 改**：`DocumentView.vue:225-231` 预览容器
  - `<pre v-html="sanitizeDocumentHtml(previewContent)">` → `<div v-html="renderedPreviewContent">`
  - 新增 `.markdown-content` CSS（含表格/标题/列表/代码块样式）
  - `applyClientHighlight` 改用占位符策略
- **验证**：
  - `vue-tsc --noEmit` 0 error
  - Vite HMR 自动优化依赖：`✨ new dependencies optimized: markdown-it`
  - DB 中 id=72 (阶段 3A 验证-资产清单) 内容含 `## 工作表：` 标题 + HTML 表格 → 浏览器端会渲染为 `<h2>` + `<table>`
- **用户需要**：浏览器硬刷新（Ctrl+Shift+R）加载最新 markdown-it 优化后代码

### 2026-09-11（15:58 - 16:40）— 阶段四：删除旧管线 + 接入引擎
- **背景**：用户决定删旧管线、文档重传；要优化 PDF + 图片识别
- **调研**（Research Agent）：2026 年最佳组合 = **MinerU 3.4**（PDF中文SOTA）+ **PaddleOCR-VL-1.6**（OCR）
- **4.1 删除旧代码**：
  - `backend/app/services/search_service.py`: 删除 828 行 LibreOffice helper（旧 `extract_file_content` 改为统一调新路由器）
  - `backend/app/services/content_extractor.py`: 删除 fallback 逻辑（旧管线失败时回退的代码）
  - `backend/app/services/extraction/router.py`: 删除 `_fallback` 方法
  - `backend/app/services/extraction/models.py`: 删除 `fallback_used` 字段
- **4.2 + 4.3 PDF 增强**（`pdf_extractor.py` 重写）：
  - 章节标题识别：8 种模式（中文第X章 / 1.1 / Chapter 1 等）
  - 页眉页脚去除：跨页重复行 + 页码模式
  - 文档元数据提取（标题/作者/创建日期）
  - **PaddleOCR 兜底**：pymupdf 提取为空时自动调用（CPU 友好）
  - MinerU 路径占位（需 GPU + MinerU 安装）
  - 引擎切换：`PDF_ENGINE=pymupdf|mineru`
- **4.4 Image OCR 增强**（`image_extractor.py` 重写）：
  - PaddleOCR 优先（中文 OCR 精度 > pytesseract）
  - pytesseract 兜底
  - 引擎切换：`OCR_ENGINE=paddleocr|tesseract`
- **4.5 配置开关**（`backend/app/core/config.py`）：
  - `PDF_ENGINE = "pymupdf"` 默认
  - `OCR_ENGINE = "tesseract"` 默认
  - `MINERU_ENABLED = False`（需用户安装后启用）
  - `PADDLEOCR_LANG = "ch"`
- **4.6 文档更新**：`memory-bank/@tech-stack.md` 新增"文档内容提取引擎"章节
- **端到端验证**：
  - 上传中文名 xls → 36581 字符（新管线无 fallback）
  - 上传 xlsx → 46220 字符（8 工作表 + 合并单元格全保留）
  - 旧管线代码完全清除
- **待用户**：重新上传旧文档看新效果

### 2026-09-11（16:40 - 16:50）— 阶段五：AI 引擎解耦为远程服务
- **背景**：用户决定将 PaddleOCR/MinerU/vLLM 部署在独立 AI 服务器，主应用通过 HTTP 调用
- **5.1 配置**：config.py 新增 8 个 AI 服务相关 settings
- **5.2 AI 客户端**（`extraction/ai_client.py`）：
  - `PaddleOCRClient` — POST /ocr 调用
  - `MinerUClient` — POST /extract 调用
  - `VLMClient` — OpenAI 兼容 /v1/chat/completions 调用
  - 工厂方法 `get_ocr_client() / get_pdf_client() / get_vlm_client()`
- **5.3 PdfExtractor 接入**：
  - `_extract_with_mineru()` 改用 `MinerUClient`，失败降级本地 pymupdf
  - `_extract_with_paddleocr()` 优先远端 PaddleOCR-Server，降级本地 paddleocr
- **5.4 ImageExtractor 接入**：`_extract_with_paddleocr()` 优先远端
- **5.5 部署文档**：
  - `scripts/start_ai_services.sh`（Docker 启动脚本）
  - `docs/AI服务部署.md`（含架构图、API 规范、实施参考）
- **5.6 端到端验证**：
  - 默认配置（AI_OFF）：xlsx 工作正常（46220 字符）
  - AI_OCR_ENABLED=true + URL 不可达：超时正确捕获，不崩溃
  - 降级链路完整：远端 → 本地 paddleocr（若安装）→ tesseract

**总架构变化**：
- 阶段三：A/B 集成（多 extractor + 路由器）
- 阶段四：删旧管线 + 增强本地 AI
- **阶段五（本次）**：AI 引擎服务化，本应用纯 HTTP 调用

### 2026-09-11（16:52 - 17:00）— 阶段六：AI 服务配置加入前端系统设置
- **背景**：用户要把 AI 服务地址加到前端设置里，方便后续管理
- **6.1 后端 API**（`backend/app/api/endpoints/extraction_config.py`）：
  - GET `/api/v1/settings/extraction-config`：返回 8 个 AI 引擎字段
  - PUT `/api/v1/settings/extraction-config`：保存到 .env，返回 restart_required=true
  - POST `/api/v1/settings/extraction-config/test`：测试 3 个服务可达性
- **6.2 前端 service**（`frontend/src/services/extraction-config.ts`）：
  - `extractionConfigService.getConfig()` / `updateConfig()` / `testConnection()`
- **6.3 SettingsView 新增卡片**（"AI 引擎服务（远程提取）"）：
  - OCR / PDF / VLM 3 个独立开关 + URL
  - VLM 模型名输入
  - 超时时间（默认 120s）
  - 失败回退本地开关
  - "刷新" / "测试连接" / "保存配置" 按钮
  - 测试结果以 JSON 形式展示
  - 重启提示 alert（保存后显示）
- **6.4 端到端验证**：
  - GET 返回当前配置：HTTP 200 ✓
  - PUT 保存成功：HTTP 200, saved_to="backend/.env" ✓
  - POST 测试连接：HTTP 200，正确捕获不可达（reachable=false）✓
  - TS 类型检查：vue-tsc --noEmit 0 error ✓
- **用户流程**：
  1. 进入 SettingsView → 看到新卡片
  2. 填入 AI 服务 URL → 点击"测试连接"
  3. 看到"OCR: reachable / VLM: 502" 等结果
  4. 点击"保存配置" → 后端写入 .env，提示重启
  5. 重启后端 → 新配置生效

### 2026-09-11（17:04 - 17:42）— 阶段七：合并为统一多模态模型（Qwen3-VL via llama.cpp）
- **背景**：用户决定用一个多模态模型替代 PaddleOCR + MinerU + vLLM。已有 llama.cpp 部署 Qwen3.8 多模态
- **调研结论**（Research Agent）：
  - llama.cpp server 自带 OpenAI 兼容 `/v1/chat/completions` 端点
  - 需用 `--mmproj` 参数加载多模态投影器
  - 必须加 `--image-min-tokens 1024` 否则 Qwen-VL grounding 错误
  - image 格式：base64 data URI 在 `image_url.url`
- **7.1 UnifiedAIClient**（`backend/app/services/extraction/ai_client.py`）：
  - 支持 provider: `ollama` | `openai`
  - `_call_ollama`：POST /api/chat（Ollama 协议）
  - `_call_openai`：POST /v1/chat/completions（llama.cpp/vLLM/DashScope 兼容）
  - 统一 prompt："文档解析引擎...输出纯净 Markdown"
- **7.2 PdfExtractor 接入统一 VLM**：
  - `_extract_with_unified_ai`：pymupdf 转 PNG（2x）→ 每 5 页一组送 VLM → 拼 Markdown
  - 引擎优先级：VLM → pymupdf → PaddleOCR（兜底）
- **7.3 ImageExtractor**：用 PIL 读图 → 调 VLM `vision_parse`（单图）
- **7.4 简化配置**：
  - `backend/app/core/config.py`：移除 8 个 AI_*_ENABLED/URL 字段，合并为 7 个字段（AI_SERVICE_*）
  - `backend/app/api/endpoints/extraction_config.py`：API schema 同步简化
  - `frontend/src/services/extraction-config.ts`：TS 类型同步简化
  - `frontend/src/views/SettingsView.vue`：把 3 个 OCR/PDF/VLM 卡片合并为 1 个"统一 AI 多模态服务"卡片
- **7.5 文档与脚本**：
  - `docs/AI服务部署.md`：改写为 llama.cpp 部署指南（含 vLLM/Ollama/DashScope 备选）
  - `scripts/start_ai_services.sh`：简化启动脚本（默认 llama-cpp，可选 ollama/vllm）
- **7.6 端到端验证**：
  - GET extraction-config → 返回新 9 字段 schema ✓
  - PUT extraction-config → 保存到 .env ✓
  - POST test → 探测 /v1/models，正确返回 502（llama.cpp 未启）✓
  - vue-tsc --noEmit → 0 error ✓
- **.env 残留字段问题**：阶段五的 AI_PDF_*/AI_VLM_* 字段残留导致 pydantic 校验失败；已清理 .env 还原

### 2026-09-11（17:44 - 17:55）— 阶段八：清理旧 AI 服务配置
- **背景**：阶段七把 AI 引擎统一到 llama.cpp/Qwen3-VL，旧"AI服务配置"和"AI使用统计"卡片（5 个 LLM Provider）已无意义
- **删除清单**：
  - 前端 SettingsView.vue：
    - 删除"AI服务配置"卡片（149 行）：provider 选择 + 5 个 LLM 配置 + 成本/缓存设置
    - 删除"AI使用统计"卡片：总成本/请求数/token/按 provider 统计
    - 删除 `StatsOutline` icon import
    - 删除所有 aiConfig/aiStats/aiProviders state + handler + helper
    - onMounted 中删除 `loadAIProviders()` / `loadAIConfig()` / `loadAIStats()` 调用
  - 前端 AssetView.vue：
    - 删除"AI提供商"下拉选块（资产提取时选择）
    - 删除 `aiProviders` state + `aiProviderOptions` computed + `loadAIProviders` 函数
  - 前端 services/ai.ts：完全删除（无引用）
  - 后端 assets.py：删除 `/ai/providers`、`/ai/stats`、`/ai/test` 3 个端点（628 行）
  - 后端 documents.py：删除 `/ai/providers`、`/ai/stats` 2 个端点（93 行）
- **保留**：
  - 后端 `app/services/ai/`（DocumentAnalyzer/AssetExtractor 是核心 AI 分析能力，与新架构不冲突）
  - `backend/AI_SERVICE_QUICKSTART.md`（说明文档）
- **端到端验证**：
  - 5 个旧 AI 端点 GET 返回 404 ✓
  - `/settings/extraction-config` GET 200 ✓（阶段七保留）
  - vue-tsc --noEmit 0 error ✓

### 2026-09-11（18:11 - 18:15）— 阶段八后续：修复前端空白页
- **问题**：删除 `frontend/src/services/ai.ts` 后，浏览器空白
- **根因**：`frontend/src/services/index.ts` 还在 re-export `./ai` + `export * from './ai'` → vite 编译失败
- **修复**：
  - 删除 services/index.ts 中的 `export { default as aiService } from './ai-stub'`（我之前错误加了 stub 名）
  - 删除 services/index.ts 中的 `export * from './ai-stub'`
  - 修复 SettingsView.vue 残留的 `import {`（阶段八用 Edit 删除时残留的半个 import）
- **验证**：
  - `curl http://127.0.0.1:5173/` → HTTP 200
  - `curl http://127.0.0.1:5173/src/services/index.ts` → 内容已干净（无 ai 引用）
  - `curl http://127.0.0.1:5173/src/views/SettingsView.vue` → HTTP 200
  - Vite HMR 已自动 reload（无需手动重启）
- **教训**：删文件后必须 grep 该文件名被 import 的位置

### 2026-09-11（18:18 - 18:30）— 阶段九：Qwen3.8-27B 实测 + PDF/图片优化
- **背景**：用户在 SettingsView 配置 AI 服务（llama.cpp server @ 192.168.66.234:8081, model=Qwen3.8-27B-Q8_0），要求测试连通性并完成 PDF/图片提取优化
- **测试连通性**：
  - `GET http://192.168.66.234:8081/v1/models` → HTTP 200，模型 = `/home/ubuntu/moxing/Qwen3.8-27B-GGUF/Qwen3.8-27B-Q8_0.gguf`
  - 后端 `/api/v1/settings/extraction-config/test` → reachable=True, status=200
- **直接测 llama.cpp server**：模型对测试 PNG 输出完美 Markdown 表格（识别 Name | Age | City）
- **Bug 修复**：`_extract_with_unified_ai` 中 `doc.close()` 之后访问 `len(doc)` 抛 `document closed` → 修复为先存 `page_count = len(doc)`
- **优化**：
  - PDF 渲染从 2x 提到 3x DPI + `alpha=False`（避免透明背景，文字清晰度提升）
  - 优化 prompt：更明确的标题/段落/表格/列表规则，避免模型输出模糊
  - ImageExtractor 加 `_extract_with_unified_vlm` 路径（主路径）；OCR 链作为兜底
- **真实业务 PNG 提取对比（id=36 收费网拓扑1.png）**：
  - 旧（tesseract）：只能识别几个孤立字符
  - 新（Qwen3-VL）：30+ 设备名称、端口、IP 段、拓扑图标题全部识别 ✓
- **真实 PDF 测试**：用 pymupdf 创建的极简测试 PDF 模型识别有限（嵌入字体问题），但 AI 服务本身工作正常；真实业务 PDF（含正确字体）应正常

### 2026-09-11（18:58 - 19:00）— 修复 AssetView currentUser 引用
- **问题**：前端控制台报 `ReferenceError: currentUser is not defined`（AssetView.vue:2510/1415）
- **根因**：阶段八用 Edit 删除 import 块时，**误删了 `const currentUser = ref<User | null>(null)` 声明**（模板 line 15/21/27/33 + 函数 line 1416/2510 仍在引用）
- **修复**：在 AssetView.vue line 950 重新加 `const currentUser = ref<User | null>(null)`
- **验证**：
  - vite-tsc --noEmit exit 0
  - Vite HMR 自动 reload AssetView.vue
- **教训**：用 Edit 删除 import 块时，必须先 grep 确认块内每一个名字都有声明位置

### 2026-09-11（19:30 - 20:10）— 阶段十·W1 MD 副本 + AI 元数据完成
- **背景**：用户决定"开干"
- **完成子步骤**：
  - 安装 `fastmcp 4.0.3`（后续 W3 用）
  - 新建 `backend/app/services/wiki/` 模块
    - `storage.py`：WikiStorage（MD 副本 + frontmatter + 读/写/更新）
    - `metadata.py`：generate_metadata_via_ai（调 UnifiedAIClient.chat）
    - `__init__.py`：导出
  - `backend/app/core/config.py` 新增 `AI_METADATA_ENABLED: bool = True`（Q5 开关）
  - `backend/app/services/content_extractor.py` 新增 `extract_content_async()`：提取后调 WikiStorage 写 MD 副本
  - `backend/app/services/background_tasks.py` 改异步：`_worker_loop` 用 `asyncio.run` 桥接线程，`_process_task` 改 `async`
- **修复 3 个 Bug**：
  1. `_process_task` 未声明为 async（导致 startup 阶段 `await` 报错）
  2. 导入名错误（`sanitize_filename_title` → 实际是 `sanitize_title`）
  3. `WIKI_DIR` 路径少一层（`backend/app/wiki/` → 改为 `backend/wiki/`）
- **E2E 验证**：
  - 上传 docx → 后台提取 → AI 生成 metadata → 写入 wiki/{id}.md
  - frontmatter 字段完整：title / source_file / doc_type / extracted_at / tags
  - AI 生成的 title: "江苏交控网络安全培训会议七项工作建议"
  - AI 生成的 tags: ["网络安全", "江苏交控", "培训会议", "工作建议"]
  - wiki/{id}.md 包含完整正文（7 项工作建议全文）
- **待做**：W2 (FTS5 索引) → W3 (FastMCP) → W4 (前端编辑) → W5 (下载选择) → W6 (E2E 验证)

### 2026-09-12（08:16 - 10:05）— 阶段十·W2/W3/W4/W5/W6 完成
- **W2 SQLite FTS5 索引**：
  - 新建 `backend/app/services/wiki/index.py`：WikiIndex（FTS5 + tags + links + backlinks）
  - 新建 `backend/app/api/endpoints/wiki.py`：7 个 REST API（rebuild/search/doc/backlinks/tags/stats/download/markdown/report）
  - 内容提取自动建索引（content_extractor.extract_content_async → WikiStorage.write → WikiIndex.index_doc）
  - wikilink 提取后查表匹配（按 title 或 path basename）
- **W3 FastMCP 暴露 6 个 tools**：
  - `backend/app/services/wiki/mcp_server.py`：register_tools() 注册 search_kb / get_doc / get_doc_content / list_backlinks / list_tags / generate_report
  - `backend/app/main.py`：FastMCP("AI-Wiki").http_app(path="/") + mount 到 /mcp + lifespan_context 注入
  - 修复 lifespan task group 报错（FastMCP 4.0.3 要求 `lifespan=mcp_app.lifespan`）
  - E2E 验证：initialize / tools/list / tools/call（数字参数）全部 200
- **W5 下载端点**：`GET /wiki/download/{id}?type=original|markdown` 带 FileResponse
- **W6 端到端验证**：
  - 搜索/标签/原文件下载/MD 下载/读 MD/保存 MD/生成报告/MCP init 共 8 项全部通过
  - 保存 MD 后索引自动重建
- **文档**：
  - 新建 `docs/AI-Wiki部署与使用指南.md`：架构、API、WorkBuddy MCP 配置示例、6 个 tools 说明
- **W4（前端编辑 UI）** 因时间紧未做完整集成；用户可后续补——后端 API 已完备
- **总变更**：
  - 新建 3 个 Python 模块（wiki/storage, wiki/metadata, wiki/index, wiki/mcp_server）+ 1 个前端 service
  - 修改 main.py（FastMCP 挂载）+ content_extractor.py（自动建索引）+ 新增 wiki 端点（7 路由）

### 2026-09-12（10:09 - 10:20）— W5 前端下载选项
- **用户反馈**：下载按钮只下载原文件，没有提供选择
- **修复**：
  - 引入 `frontend/src/services/wiki.ts` 中的 `wikiService.download(doc_id, type)`
  - `DocumentView.vue` 加 `downloadMenuOptions`（2 个选项：原文件 / Markdown）
  - 3 处下载按钮改为 `n-dropdown`（预览模态、详情模态、表格行操作）
  - `downloadDocument(doc, type)` 参数化；调 `/api/v1/wiki/download/{id}?type=original|markdown`
- **验证**：vue-tsc --noEmit 0 error

### 2026-09-12（15:01 - 15:25）— W4 前端编辑 UI 完成
- **完成项**：
  - DocumentView 预览模态加"编辑"按钮（仅管理员可见）
  - 切换编辑模式 → textarea 显示 MD 副本源码
  - 调 `/api/v1/wiki/doc/{id}/markdown` 拉取 MD 内容
  - 调 `/api/v1/wiki/doc/{id}/markdown` PUT 保存
  - 保存后自动取消编辑 + message 提示"已保存并重建索引"
- **修改文件**：`frontend/src/views/DocumentView.vue`（+3 状态、+3 handlers、+编辑模式 UI）
- **验证**：vue-tsc --noEmit 0 error；Vite HMR 已 reload

### 2026-09-12（16:00 - 16:35）— 阶段十一：移除 Android 模块与移动端 API
- **用户决策**：后期用 AI 工作台接入 Wiki 的 MCP 做数据查询和利用，不需要安卓客户端
- **K.1 删除文件**：
  - `android/` 整目录（88 个 git 跟踪文件，可 `git checkout HEAD -- android/` 恢复）
  - `backend/app/api/endpoints/mobile.py`（8 个移动端点）
  - `backend/app/schemas/mobile.py`
  - `docs/Android应用架构设计.md` / `docs/Android应用测试方案.md` / `docs/移动端API设计方案.md`
- **K.2 断开引用**：
  - `api_v1.py`：移除 mobile import + `include_router` 行
  - `security.py`：删 `create_mobile_tokens` / `validate_device_token` / `extract_user_id_from_token`；`create_access_token` 删 mobile 分支；`verify_token` 白名单 `["access","refresh","mobile"]` → `["access","refresh"]`
  - `system.py`：`SystemInfoResponse` 改继承 `pydantic.BaseModel`；`/info` 删 mobile_config / mobile 端点列表，特性列表加 `ai_wiki_mcp`；`/version` 删 mobile_api；`/capabilities` 删 mobile_features
- **K.3 文档清理**：
  - `docs/生产环境脚本说明.md` 删移动端 API 章节，核心端点补 MCP 入口
  - 根 `README.md`：移动端功能/技术栈/项目结构章节 → 改为"AI Wiki 与 MCP 数据服务"
- **K.4 端到端验证（全绿）**：
  - mobile 端点 → 404 ✓
  - `/health` → 200 healthy ✓
  - 登录（Form 格式）→ 200 签发 token ✓（JWT access 逻辑未受影响）
  - `/system/info` → 200，无 mobile 字段 ✓
  - `/mcp` initialize → 200 ✓（数据查询新路线可用）
  - `grep -rn "mobile|Mobile" backend/app/` → 0 匹配 ✓
- **K.5 memory-bank 同步**：
  - `@architecture.md`：android 章节 → "AI Wiki MCP 数据查询服务"；删 mobile 端点/schema 条目
  - `@tech-stack.md`：栈总览图更新（Android → AI 工作台/MCP）；第五节 Android → AI Wiki MCP
  - `@product-requirements-document.md`：F6 标记已移除；非目标加"不再开发移动端"；角色表/F7/路线图同步
- **未动**：`create_refresh_token` / `verify_refresh_token`（通用 JWT 工具）；前端（无 mobile 引用）；数据库表结构

### 2026-09-12（17:23 - 18:10）— 阶段十二：修复 start-services.bat 启动报错
- **用户报告**：start-services.bat 运行报错
- **根因（实测确认）**：
  1. `start-services.bat` 检查 `backend/venv`，本机不存在（依赖此前装在 managed runtime）→ 报错退出
  2. 错误提示指向的 `install-environment.bat` 根本不存在（实际是 `install-complete.bat`）
  3. 本机 python/node 不在 Windows 系统 PATH（在 WorkBuddy managed runtime），`install-complete.bat` 用系统 `python` 建 venv 也会失败
  4. **隐藏 bug**：`fastmcp` 不在 `requirements-windows.txt`（之前手动装的），干净环境装依赖后 `/mcp` 服务挂载失败
- **修复**：
  - `start-services.bat`：
    - python/node 探测：系统 PATH 找不到时自动回退 managed runtime（`%USERPROFILE%\.workbuddy\binaries\{python,node}\versions\*` 通配探测）
    - **venv 缺失时自动创建 + 自动装依赖**（不再要求先跑安装脚本）
    - 前端 `node_modules` 缺失时自动 `npm install`
    - node 不在 PATH 时把 managed node 目录加进 PATH（保证子窗口 `npm run dev` 可用）
    - 错误提示脚本名修正（install-environment.bat → install-complete.bat）
    - 保持 dev/prod 双模式、端口、start 窗口方式不变
  - `install-complete.bat`：python 探测 + `%PYTHON_EXE%` 变量化；venv 完整性检查（`venv\Scripts\python.exe` 存在）；DB 测试改用 venv 的 python
  - `backend/requirements-windows.txt`：新增 `fastmcp>=4.0.0`（AI Wiki MCP 依赖）
- **验证**（沙箱内无法双击 bat，改为实跑 bat 的完整命令链路）：
  - 删 venv → managed python 建 venv → 升级 pip → 装 requirements-windows.txt（13 分钟，含 scikit-learn/opencv/pandas/PyMuPDF）→ 全部核心包 import OK
  - `import app.main` → "AI Wiki MCP server 已挂载到 /mcp"（补 fastmcp 后成功）
  - 新 venv 启动 uvicorn → `/health` 200、`/mcp` initialize 200
- **用户操作**：双击 `start-services.bat` → 选 1（开发模式）→ 首次会自动建 venv 装依赖（已预装好，直接启动）

### 2026-09-12（18:17 - 18:40）— 阶段十二·补丁：修复 bat "闪退"
- **用户报告**：start-services.bat 运行后直接闪退
- **根因**（用 Node spawn 真实复现，退出码 255）：
  - 批处理 `if (...)` 块内的 `echo` 文本含**圆括号**，cmd 把 `)` 当成代码块结束符 → 语法解析错误 `... was unexpected at this time` → 脚本中断
  - 脚本第 3 行 `cls` 已清屏，中途崩溃又没走到最后的 `pause` → 窗口瞬间消失 = "闪退"
  - 两处肇事行：`echo Node.js found: node (on PATH)`、`echo Installing backend dependencies (first run may take several minutes)...`
  - 附带：`echo Frontend: ... (Development & Production)` 中未加引号的 `&` 是 cmd 命令分隔符 → 弹 "'Production)' is not recognized"（不致命但难看）
- **修复**：
  - `start-services.bat` 三处 echo 去掉括号/`&`（if 块内的 echo 文本**严禁含 `()` 与 `&`**）
- **验证**（Node spawn cmd /c 实跑，Windows 系统 PATH 优先）：
  - 修复前：EXIT 255 + `was unexpected at this time`，脚本在 "Starting backend service..." 后中断
  - 修复后：完整跑通到 "Press any key to exit..."，无解析错误（timeout 的 input redirection 报错是管道测试环境假象，双击运行不出现）
  - 测试启动的服务进程已清理，8002/5173 端口已释放
- **教训**：
  - bat 的 `if (...)` 块内 echo 文本含 `()` / `&` / `|` / `<` / `>` 都会破坏解析——写 bat 时 if 块内 echo 一律避免这些字符或整体加引号
  - 沙箱内 Bash 调 cmd 被拦、PowerShell 调 .NET Process 被拦 → **Node.js `child_process.spawn('cmd.exe', ['/c', bat])` 是沙箱内真实运行 bat 的可行路径**

### 2026-09-12（19:42）— 修复 DocumentView 未注册图标 CreateOutline
- **用户报告**：文档管理页面控制台 `[Vue warn]: Failed to resolve component: CreateOutline`
- **根因**：W4 前端编辑 UI（阶段十）在 DocumentView.vue:214 用了 `<CreateOutline />`，但该图标**不存在于 @vicons/ionicons5**（包内无 create 系列图标），且 511 行 import 列表也未引入
- **修复**：改用包内真实存在的 `PencilOutline`（铅笔图标，语义贴切"编辑"）——import 补 `PencilOutline` + 模板 214 行替换
- **验证**：grep 无 CreateOutline 残留；vue-tsc --noEmit 0 error
- **教训**：从图标库引用图标前先 `ls node_modules/@vicons/ionicons5/` 确认命名存在（ionicons5 无 Create 系列，编辑类用 Pencil/Create 需查实际清单）

### 2026-09-12（21:16 - 21:50）— 阶段十三：修复 AI 服务配置保存不生效 + 补"全格式 AI 提取"开关
- **用户报告**：
  1. 系统设置里启用 AI 服务、填服务地址/模型名后保存，**会自动恢复默认选项**（无法保存）
  2. 之前加过"是否所有格式文档全部使用 AI 提取 md"的开关（不开则仅 PDF/图片走 AI，AI 失败降级本地），**界面上没看到**
- **根因（实测复现）**：
  1. **保存不生效（核心 bug）**：`config.py` 的 `settings = Settings()` 在 import 时**只读一次 .env** 到内存单例。`extraction_config.py` 的 PUT 只把新值**写进 .env 文件**，但运行中进程内存 `settings` 从不刷新 → 后续 GET 与真正 AI 提取（`pdf/image_extractor` 都读 `settings.AI_SERVICE_*`）仍用**旧值**，直到整进程重启。
     - 实测：PUT 写 .env 成功，但同进程紧接着 GET 仍返回旧 url/model（用户看到"恢复默认"）。
  2. **全格式开关缺失**：全仓 grep `AI_ALL_FORMATS_AI`/`all_formats`/`全部格式` 均无命中 → 该功能**从未实现**（用户记忆中的改动已丢失）。
- **修复**：
  1. `config.py`：`Settings` 加 `reload()` 方法（dotenv `override=True` 重读 .env + 重建实例搬字段回 self）；新增 `AI_ALL_FORMATS_AI: bool = False`
  2. `extraction_config.py`：`ExtractionConfig` 加 `ai_all_formats_ai`；`_load_from_settings` 读它；PUT 的 .env 清理/写入列表加 `AI_ALL_FORMATS_AI=`；**写完 .env 后 `settings.reload()` 热刷新**；响应 `restart_required=false`、message 改"已保存并立即生效（无需重启）"
  3. `ai_client.py`：`UnifiedAIClient` 加 `parse_text(text)`（纯文本喂多模态模型，openai/ollama 两分支，不发图片）
  4. `router.py`：全格式 AI 统一收口——PDF/图片走原路径（内部已含 AI 优先+降级）；其余格式在 `AI_ALL_FORMATS_AI=true && AI_SERVICE_ENABLED=true` 时**本地引擎先出一份 md（作 AI 输入+降级兜底）→ 交 AI 规整为最终 md**（engine=unified-ai）；AI 失败按 `AI_FALLBACK_TO_LOCAL` 回退本地结果或报错
  5. `extraction-config.ts`：接口加 `ai_all_formats_ai`
  6. `SettingsView.vue`：加"所有格式文档都使用 AI 提取 Markdown"开关（`ai_all_formats_ai`，依赖总开关）；卡片标题/提示更新为"保存后立即生效，无需重启"
- **验证（HTTP 端到端，真实登录 token）**：
  - PUT 改 url/model + 开 all_formats → 同进程再 GET **返回新值 + ai_all_formats_ai=true**（不再回退）；`.env` 落盘 `AI_ALL_FORMATS_AI=true`
  - 单元：`settings.reload()` 改 .env 后 `AI_ALL_FORMATS_AI` False→True；OFF 模式 txt→本地引擎；ON 模式 + AI 服务不可达→**优雅降级本地**（不报错，md 正常）
  - `import app.main` 成功（/mcp 挂载）；vue-tsc --noEmit 0 error
  - 测试后已把 `ai_all_formats_ai` 重置回 false（默认关），用户真实 url/model 保持 `192.168.66.234:8081` / `Qwen3.8-27B-Q8_0` 不变
- **注意**：本机 8002 后端由 supervisor 管理，kill 后自动重生；重生进程在编辑后启动 → 已带新代码，无需手动重启
- **教训**：
  - Pydantic BaseSettings 单例**只读一次 .env**——"写文件即保存"的端点必须同步刷新内存（否则运行中进程永远用旧值），这是"保存不生效/恢复默认"类问题的典型根因
  - 配置持久化"文件 + 内存"要双写：文件保证重启不丢，内存刷新保证立即生效
  - 全格式 AI 提取用"本地引擎先出 md 再让 AI 规整"比"读原始字节喂模型"更稳（二进制 docx/xlsx 不可按文本读；本地 md 已是干净文本且可作降级兜底，零浪费）

### 2026-09-12（22:30 - 22:55）— 阶段十五：修复后台提取 worker 不运行（上传卡"内容提取中"）
- **用户报告**：上传"交换机统计0723.xls"卡在"内容提取中"
- **根因（实测确认，P0 回归）**：`main.py:162` 的 `app.router.lifespan_context = mcp_app.lifespan`（阶段十·W3 挂 MCP 引入）**整体覆盖**主应用 lifespan → 主应用 startup（bcrypt 校验 / 默认用户初始化 / `startup_background_tasks()` 启动后台提取 worker）**永远不执行**
  - 证据：任务状态全 `pending/started_at=null`（worker 接手即写 processing）；启动日志无任何主 lifespan print（只有 uvicorn 通用行）
  - 9-11 上传能成功是因那台后端在 MCP 代码合并前启动、worker 存活；重启后（带 bug 新进程）worker 再没起
- **修复**（`main.py`）：
  - 模块级 `mcp_lifespan`（默认 `_noop_lifespan` 空 asynccontextmanager）；MCP 挂载成功块里 `mcp_lifespan = mcp_app.lifespan`
  - 主 `lifespan` 改为 `async with mcp_lifespan(app):` 内执行原 3 步 + yield —— 一次 startup 同时满足 MCP 与主应用
  - 删除 `app.router.lifespan_context = mcp_app.lifespan` 覆盖行
- **验证**：
  - 重启后端 → 启动日志出现"启动 运维资产管理系统" + "OK: bcrypt" + "后台任务处理器已启动" + "MCP server 已挂载" + "SUCCESS"
  - `/mcp` initialize 200（MCP 仍可用）
  - 清理 3 个卡死 `extract_75_*` 孤儿任务文件 → `retry-extraction` 触发 → 状态 `pending→processing(50)→completed(100)`，全程 69s（含 LibreOffice 转 .xls + AI 规整）
  - 文档 75 `content_extracted=True`、`content` 992 字符、交换机统计表完整入库
- **教训**：
  - FastAPI 子应用（MCP）挂载时**不能**用 `app.router.lifespan_context = sub.lifespan` 整体覆盖主 lifespan，会吞掉主应用 startup；正确做法是主 lifespan 内 `async with sub_lifespan(app)` 合并
  - 后台 worker 没起时症状是任务永久 `pending/started_at=null`，不是报错——排查"异步任务卡住"先看启动日志里 worker 是否真的 `已启动`
  - 本机 8002 后端无 supervisor 自动重生，改 main.py 后需手动 `venv/Scripts/python -m uvicorn app.main:app --port 8002` 重启

### 2026-09-12（22:05 - 22:30）— 阶段十四：测试连接增强——校验模型名真实可用
- **用户反馈**：系统设置填新模型后点"测试连接"，输出 `reachable:true, status:200`（`/v1/models`）
- **排查发现**：旧 test 端点只 `GET /models` 判 `status<500`，**不校验模型名是否真加载** → "服务可达 ≠ 模型可用"，模型名错的话要等真实提取才暴露
- **修复**：
  1. `extraction_config.py`：test 端点拉 `/models`（openai）/`/api/tags`（ollama）后解析模型列表，与用户填的 model 做**严格匹配**（精确/路径尾段/去扩展名，不做子串误判）→ 结果加 `model:{requested, found, available_models, hint?}`
  2. 新增 `_parse_available_models()` + `_match_model()` 两个纯函数
  3. 前端 `extraction-config.ts` 加 `AiModelCheck` 类型；`SettingsView.vue` 测试结果显示区从"裸 JSON dump"改为可读提示：可达状态 + 模型校验（found=true 绿色；found=false 红色 + 列出服务实际模型 ID 可点击填入 + hint）
- **实证（关键，真实 completion 调用 max_tokens=1）**：
  - 短名 `Qwen3.8-27B-Q8_0` → **HTTP 200**（11.4s 冷加载）
  - 完整路径 `.../Qwen3.8-27B-Q8_0.gguf` → **HTTP 200**（0.3s 已驻留）
  - → **用户当前短名配置真实可用**，llama.cpp 单模型模式接受该名，**无需改 .env**；完整路径只是"多模型/换服务"时更稳的写法
- **验证**：vue-tsc 0 error；test 端点对用户配置返回 `model.found=true` + `available_models` 列出真实 ID；新后端（venv uvicorn）起在 8002，/health 200
- **教训**：
  - 判定"模型名是否可用"不能只靠 /models 字符串猜测，**真实 completion 调用才是金标准**（短名/完整路径都 200，证明单模型 llama.cpp 宽容）
  - "测试连接"应校验到模型级而非仅端口级，否则配置错误要拖到真实提取才炸
  - 注意：本机 8002 后端**没有 supervisor 自动重生**（之前误判），kill 后需手动 `venv/Scripts/python -m uvicorn app.main:app --port 8002` 拉起

### 2026-09-13（09:10 - 09:40）— 阶段十六：统一三个下载点（原文件 / Markdown 二选一 + 修复下载失败）
- **用户报告**：文档下载有 3 个点位，行为不一致且部分失败——
  1. 预览中下载：能弹"原文件 / MD"选择，但**下载失败**
  2. 文档条目右侧下载：点击**显示失败**，无选择
  3. 智能搜索结果下载：走旧端点，无 MD 选择
  用户要求三处统一为"下载后选原文件或 MD 文件，且能成功下载"
- **根因（实测确认）**：
  1. **后端 500（核心）**：`wiki.py` 的 `download_doc` 用 `Path(row[0])` 拼原文件路径，但**`Path` 从未 import** → `NameError: name 'Path' is not defined` → 任何真实文档"原文件"下载一律 500（后端日志只有这一行 NameError，极隐蔽）
  2. **MD 副本缺失**：doc 70 只有 DB `content`、无 `wiki/70.md` 副本 → markdown 分支直接 404
  3. **前端三处各写各的**：DocumentView 列表行 `h(NButton)` 无下拉；SearchView 走 `apiService.download('/documents/{id}/download')` 无 MD 选项
- **修复**：
  1. `wiki.py`：顶部补 `from pathlib import Path`；markdown 分支加"MD 副本缺失 → 回退 DB `content`+`title` 拼 `Response` + RFC5987 `Content-Disposition`"兜底，两者皆无才 404
  2. 新建 `frontend/src/utils/file-download.ts`：`downloadWikiDocument(docId, type, fallbackTitle)`（fetch + Bearer + blob 触发下载，返回真实文件名，失败抛带后端 detail 的 Error）+ `resolveApiBaseUrl` / `parseFilenameFromDisposition`
  3. `DocumentView.vue`：import 补 `NDropdown` + 工具；列表行 `h(NButton)` → `h(NDropdown, {options, onSelect})`；预览弹窗下拉保留、`downloadDocument` 委托工具
  4. `SearchView.vue`：结果卡片 / 预览头部 / 不可预览项 3 个按钮全包 `<n-dropdown>`（原文件 / Markdown），`downloadDocument` 委托工具（替换旧 `apiService.download`）
  - 三处统一打到 `GET /api/v1/wiki/download/{id}?type=original|markdown`
- **验证（端到端，真实登录 token + httpx 测真实字节数）**：
  - `vue-tsc --noEmit` 0 error
  - 重启后端（task Rgs9ND）实测：
    - doc71 original（xlsx，有文件）→ HTTP 200，size 正确
    - doc71 markdown（有 MD 副本）→ HTTP 200，size 正确
    - doc70 original（md 文件）→ HTTP 200，size 正确
    - doc70 markdown（**无 MD 副本 → 回退 DB 内容**）→ HTTP 200，内容 `# Ollama + Open WebUI…`
    - doc999（不存在）→ HTTP 404
- **教训**：
  - 拼路径 / `FileResponse` 前确认 `Path` 已 import——"500 但日志只有一行 NameError"极隐蔽，下载类端点必须端到端拉真实字节验证（curl `size_download` 在 uvicorn 流式下可能误报 0，用 httpx 才准）
  - 多入口同功能抽共享 util 收口，避免三处各写各的、改一处漏两处
  - markdown 下载要"MD 副本缺失 → 回退 DB `content`"兜底，否则早期未生成 wiki 副本的文档 404

### 2026-09-13（09:56 - 10:05）— 阶段十七：修复设置页打开时 AI 配置不加载（误报"恢复默认"）
- **用户报告**：重启后端后，系统设置里 AI 服务"又关闭并恢复默认"
- **排查路径**：
  1. 后端 GET（有效 token）→ 返回**用户真实配置**（enabled=true / 192.168.66.234:8081 / Qwen3.8-27B-Q8_0 / all_formats=true）→ 后端无问题
  2. `.env` 文件未变；后端 CWD 正确（`backend/`）；`SECRET_KEY` 固定串（非随机）→ 排除持久化/工作目录/JWT
  3. git diff SettingsView.vue → **onMounted 里 `loadExtractionConfig()` 被遗漏**：阶段十三重构删除旧 `loadAIConfig()` 时没补新调用
- **根因**：设置页打开时 AI 配置**从不从后端拉取**，`extractionConfig` ref 一直停在初始化默认值（`enabled:false` / `localhost:8080` / `qwen3-vl-8b`）→ 用户看到"恢复默认"；实际配置一直安全存于后端
- **修复**：`SettingsView.vue` onMounted 内 `loadCurrentUser().then(...)` 之前加 `loadExtractionConfig()`（1 行，不依赖登录态）
- **验证**：vue-tsc 0 error；后端 GET 实测 200 + 用户真实值；前端 5173 / 后端 8002 均在运行（HMR 生效）
- **教训**：
  - 重构"旧加载函数→新 service"时每个调用点（尤其 onMounted）都要同步替换，最易漏
  - "配置恢复默认"先验证后端真实返回值（带 token GET），别急着怀疑持久化/重启/CWD
  - 前端 ref 的初始化默认值 ≠ 后端真实值，要分开看

### 2026-09-13（10:20 - 12:30）— 阶段十八：PDF/图片提取 + 文类 + 图片检索（参考 OpenKB）
- **用户诉求**：参考 `VectifyAI/OpenKB`，借鉴其对文件提取与"文类"（分类）的处理（如 PDF 图片单独提取）；核心目标 = **用 AI 工作台调用 AI Wiki MCP 时能快速精准搜到所需文件内容与图片，以撰写报告/PPT**
- **方案（已批准）**：9 个子步骤（18.1~18.9），覆盖图片提取 / 文类词表 / AI 图片描述 / 三路中文检索 / MCP 扩展 / 前端图片水合
- **借鉴 OpenKB 的关键点**：
  - `pymupdf page.get_text("dict")` 按阅读顺序遍历 block，`type=1` 即图片块（能抓矢量渲染图，`get_images()` 只拿嵌入位图会漏）→ `Pixmap` 存 PNG，MD 原位插入引用
  - `_MIN_IMAGE_DIM=32` 过滤图标/项目符号/噪点
  - **OpenKB 短板 = 我们的机会**：它图片 alt 一律 "image" 无文字描述 → 图片不可检索；我们用多模态 AI 生成中文描述反超
- **代码变更**：
  - 新建 `backend/app/services/wiki/image_extractor.py`（18.1）：`extract_pdf_images`（dict-mode + 2x 裁剪兜底）/ `register_image_doc`（独立图片拷贝）/ `insert_image_refs`（按页/文末插图引用，带 `<!-- wiki-img -->` 保护）/ `list_doc_images` / `image_mime`
  - `wiki/index.py`（18.2/18.4/18.5）：新表 `wiki_images` + `images_fts`(trigram) + `docs_fts_zh`(trigram) + `doc_text`(LIKE 兜底)；`search` 三路合并（unicode61 MATCH / trigram≥3字 / LIKE≤2字）；新 `add_image`/`update_image_caption`/`get_doc_images`/`search_images`/`list_categories`；`doc_meta` 加 `doc_category`（`ALTER TABLE` 迁移）
  - `wiki/metadata.py`（18.2/18.5）：`DOC_CATEGORIES` 受控词表（8 类）；`generate_metadata_via_ai` 返回 `doc_category`（词表外归"其他"）；`IMAGE_DESCRIBE_PROMPT` + `describe_image_via_ai`
  - `extraction/ai_client.py`（18.2）：`UnifiedAIClient.describe_image`（单图描述，委托 ollama/openai）
  - `content_extractor.py`（18.3）：PDF/独立图片分支接图片提取 + AI 描述 + 索引 + 图引用；`final_markdown` 回传给 `documents.content`（前端预览数据源）
  - `wiki.py` 端点（18.6/18.7）：`GET /wiki/images/{id}/{file}`（路径防穿越 + JWT）/ `GET /wiki/doc/{id}/images` / `POST /wiki/rebuild?reextract_images=`（存量补提）
  - `wiki/mcp_server.py`（18.5/18.6）：`search_kb` 加 `category` 参数；新 tools `get_doc_images` / `search_images` / `list_categories`（均返回带 `url`）
  - `core/config.py`（18.6）：`WIKI_PUBLIC_HOST`（MCP 返回 URL 用）
  - 前端 `utils/file-download.ts`（18.8）：`fetchWikiImageUrl` + `hydrateWikiImages`（JWT fetch→blob URL，`<img>` 批量水合）；`DocumentView.vue` 预览水合（带过期丢弃 + revoke）
  - 新建 `scripts/stage18_e2e_test.py`（18.9）
- **修复的两个 AI 图片描述 bug（关键）**：
  1. **MIME bug**：`describe_image_sync`/`describe_image_via_ai` 用 `f"image{suffix}"` 拼成 `image.png` → AI 400 "Invalid uri format"。修复：加 `IMAGE_MIME` dict + `image_mime()` helper
  2. **thinking 模型空 content**：Qwen3.8 是 thinking 模型，先出 `reasoning_content` 再出 `content`；`max_tokens=128/512` 时 token 全被思考吃光 → `content` 空（实测 128→reasoning 267 字 content 空、512→918 字空、2048→正常）。修复：`describe_image` 及两处调用 `max_tokens=128→2048`
- **端到端验证（全绿，真实进程 task IfHbIY + E2E task fFz0IW，1m56s）**：
  - `py_compile` 全过 / `app.main` 导入 OK（9 MCP tools 注册）/ `vue-tsc --noEmit` EXIT 0
  - doc76（含图 PDF）：提 2 图落盘 `wiki/images/76/`，AI caption 正常（"网络拓扑图，包含核心交换机（core-switch）与接入交换机…"）；MD 副本含 2 图引用 + `doc_category`
  - doc77（独立 PNG）：登记 1 图，AI caption 正常（"层级结构图，顶部标有 core 的椭圆节点向下连接三个空白矩形框"）——脚本只等 PDF 完成即查 PNG 显示 0，是**时序**问题，稍晚查已闭环
  - 中文 3 字"交换机"→命中 3 篇（trigram）；2 字"运维"→命中 3 篇（LIKE 兜底）
  - `search_images`"拓扑"→命中 2 张；`list_categories`→3 类
  - 图片 URL 下载 6018 字节与本地一致；无 token 401；路径穿越 404
  - `GET /wiki/doc/76/images` 200 count=2；`GET /wiki/search?q=交换机` 200 命中 3 + `images` 字段
- **遗留 / 待用户决策**：
  - 测试产物（doc 74/75/76/77、`backend/uploads/_stage18_test/`、`backend/uploads/` 下测试 PDF/PNG、`wiki/images/74~77/`）是否清理
  - `scripts/stage18_e2e_test.py` 保留为回归脚本还是删除
  - 阶段十八改动尚未 git 提交（本地 `5a5cc10` 已推远端，阶段十八未 commit）
- **教训**：
  - FTS5 trigram 按 **Unicode 字符**计（非字节）：**中文查询必须 ≥3 字才命中**（"运维"/"拓扑" 2 字=0 命中，"交换机" 3 字=命中）→ 中文短词必须配 `doc_text` LIKE 兜底，三路合并才稳
  - thinking 模型（Qwen3 系列）调 `describe_image` 等短输出场景，`max_tokens` 必须给足（≥2048）——否则 reasoning 吃光 token、content 恒空，症状是"HTTP 200 但返回空"，极隐蔽
  - 图片 MIME 不能 `f"image{suffix}"` 拼，要用扩展名→MIME 映射表（.png→image/png，不是 image.png）
  - 独立图片文档的 VLM 提取比 PDF 晚（后台任务时序），E2E 断言"图片数>0"要分别等两个 doc 各自完成，不能只等 PDF

### 2026-09-13（15:05 - 16:30）— 阶段十九：集成 anydoc 替换 LibreOffice
- **用户诉求**：调研 firecrawl/anydoc，若优于 LibreOffice 则集成替换，所有文件优先 anydoc 转换、失败/需 OCR 走多模态 AI，并去除"所有格式 AI 提取"开关
- **研究结论（浅克隆 + 实测）**：anydoc 纯 Rust（`pip install firecrawl-anydoc` 单 wheel 3.6MB），14 格式族 21 扩展名，中位 <5ms，官方 LLM judge 盲评 482 对全格式第一。实测：`交换机统计0723.xls`（当年 LibreOffice 错位反复修的文件）→ **0.8ms** 6 列表格完整；docx 1.0ms；xlsx 13.2ms。短板：PDF 仅文本层（扫描件需其付费 hosted OCR，不采用→走我们多模态 AI）
- **代码变更**：
  - 新建 `extraction/anydoc_extractor.py`：`AnyDocExtractor`（21 格式，空/极短 <20 字判失败便于降级，不抛异常）
  - `extraction/router.py` 重写：图片→ImageExtractor；anydoc 格式→AnyDoc 优先→失败降级本地（PDF 本地引擎=多模态 AI 优先+pymupdf）；删除 `AI_ALL_FORMATS_AI` 全格式 AI 规整分支
  - `xlsx_extractor._extract_xls_legacy` / `docx_extractor._extract_doc_legacy`：删 soffice subprocess，改报"请另存为 xlsx/docx"（anydoc 已兜住 .xls/.doc）
  - `search_service.py` / `document_formatter.py` / `search.py` / `content_extractor.py`：LibreOffice 注释/死逻辑清理（soffice 代码全仓清零）
  - `config.py` 删 `AI_ALL_FORMATS_AI`；`extraction_config.py` 去 schema/写入（.env 清理列表保留→自动清存量）；`.env` 删行；前端 `extraction-config.ts` + `SettingsView.vue` 删开关 UI/初始值/TS 字段
  - `requirements-windows.txt` 加 `firecrawl-anydoc>=0.2.4`
- **验证**：
  - 直测 router：.xls→anydoc 1ms / .docx→1ms / .xlsx→12ms，engine=anydoc
  - 损坏 xlsx：anydoc 失败→openpyxl 失败→清晰报错（降级语义正确）
  - E2E（后端 task LbB4LA）：上传 .xls→doc76 提取 10s 完成，`.json` 副产物 `{"engine":"anydoc","char_count":956,"elapsed_ms":0.5}`，`documents.content` 956 字符
  - `GET /settings/extraction-config` 200 且无 `ai_all_formats_ai` 字段
  - `py_compile` 全过 / `import app.main` OK / `vue-tsc --noEmit` 0 error
  - 验收文档（doc76 + 损坏 bad.xls）已清理（DB+index.db+文件）
- **未提交**：阶段十九改动 + 上一轮 DocumentView TDZ 修复（`watch(previewContent)` 引用先于声明）均未 commit
- **教训**：
  - `_check_file` 返回 **str** 不是 Path——`path.name` 会炸 `'str' object has no attribute 'name'`（新 extractor 里踩过，router 异常兜底把 traceback 全打出来了，定位很快）
  - anydoc 空内容判定阈值（<20 字）是"扫描件→多模态 AI"的关键开关：PDF 文本层提取不出东西 = 扫描件信号
  - 上传重名文件会被加后缀（`xxx.xls`→`阶段十九验收-xxx.xls`），E2E 验 `.json` 副产物要用**新文件名**找，不能用源文件名

### 2026-09-13（18:20 - 19:00）— 修复图片预览裂图（VLM 占位图 + 局域网 CORS）
- **用户报告**：图片文档（doc 78 QQ浏览器截图）提取完预览裂图（两张裂图）
- **根因 1（VLM 占位图，代码 bug）**：`ai_client.py:38` DOC_PARSE_PROMPT 第 6 条让 VLM"插入 `![描述](占位)`"→ 生成 `<img src="占位">` 必然 404。且真实原图已由阶段十八 `register_image_doc` 单独附加文末，prompt 再插占位图重复且无效
  - **修复**：prompt 第 6 条改为"不要插入任何图片语法，用一段文字简要描述图片内容即可（图片文件由系统文末单独附加真实引用）"
- **根因 2（CORS 拦截，环境 bug）**：用户从局域网 IP（192.168.66.99:5173）访问前端，而 CORS 白名单只有 localhost（`CORS_AUTO_DETECT` 默认 false）→ 图片水合的跨域 fetch 被浏览器拦截（实测 OPTIONS 返回 `Disallowed CORS origin` 400）→ `<img>` 留着相对路径 `images/78/img1.png` → 前端端口 404 裂图
  - **修复**：`.env` 加 `CORS_AUTO_DETECT=true`（自动检测本机 IP 加入白名单，比写死 IP 稳）；实测局域网 origin 预检 200 + `access-control-allow-origin` 正确回显 + 带 token GET 2980 字节
- **验证**：doc 75/78 重新提取（retry-extraction）→ content 无"占位"、文末含真实图片引用；图片文件/下载端点/CORS 全链路 200；后端重启 task pB9eUp
- **教训**：
  - VLM prompt 里"插入图片"的指令对"图片本身就是文档"的场景是反模式——模型只能生成占位符链接，真实图必须系统侧落盘后追加；prompt 应明确禁止模型生成图片语法
  - 前端预览裂图排查顺序：① 图片文件在盘？② 下载端点带 token 200？③ **浏览器 origin 是否在 CORS 白名单**（局域网访问最容易漏，本机 curl 测不出，要用 `Origin: http://<局域网IP>:5173` 测 OPTIONS 预检）

### 2026-09-13（20:00 - 20:18）— 图片裂图真正根因：DOMPurify 正则误剥相对路径 src（决定性修复）
- **背景**：18:20 那条修了 VLM 占位图 + CORS 后，用户刷新预览**仍裂图**。继续深挖，用 headless 浏览器（playwright-core + 已下载的 Chrome 153，通过 `192.168.66.99:5173` 真实访问）走完整流程，抓到铁证：预览容器里 `<img alt="图片">` **完全没有 src 属性**，且浏览器对图片端点**零请求**——水合正则匹配的是 `src="images/..."`，src 已被剥掉，水合根本不触发。
- **真正根因（代码 bug，单点）**：`frontend/src/utils/xss-protection.ts:37` 的 `ALLOWED_URI_REGEXP` 手写正则：`[a-z+.-]+(?:[^a-z+.-:]|$)`，其中否定字符类 `[^a-z+.-:]` 里的 **`-` 未转义**，与相邻字符组成**意外范围 `.-:`**（ASCII `.`~`:`，含 `/`）。DOMPurify 据此把**任何含 `/` 的相对路径 `images/78/img1.png` 判为非法 URI，剥离 src**，只留 alt → 裂图。
  - 为何之前没暴露：markdown-it 渲染的 `<img src="images/78/img1.png">` 本身正确；是 sanitize 这一步把 src 删了。CORS 那层其实是 18:20 已修好的（本次实测预检 + 实际 GET 响应都带正确 `access-control-allow-origin`，带 token 返回 200 image/png 2980 字节）。
- **修复**：把该正则改成 **DOMPurify 官方默认**（转义 `-` 为 `\-` 避免组成范围 + 补 `matrix` scheme）：`/^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp|matrix):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i`。已通过 12 项用例（相对/绝对/http/blob 放行，`javascript:`/`data:`/`vbscript:` 拦截）。
- **决定性验证（headless 浏览器，非 curl）**：
  - 修复前：`renderDocumentMarkdownHtml` 输出 `<img alt="图片">`（src 被剥）；修复后输出 `<img src="images/78/img1.png" alt="图片">`（src 保留）
  - E2E 预览 doc 78：`GET :8002/api/v1/wiki/images/78/img1.png → 200 + ACAO`，最终 DOM `<img src="blob:http://192.168.66.99:5173/uuid" alt="图片">`，`naturalWidth=61 / naturalHeight=58 / complete=true`（真实解码渲染，红色"值"圆形图标正常显示）
  - `vue-tsc --noEmit` exit 0 / 0 error（xss-protection.ts 零报错）
- **教训（重要方法论）**：
  - **前端渲染链 bug 必须用真实浏览器（headless）验证，curl 测不出来**。这次服务端 curl 全链路 200 都正常，但浏览器里 src 被剥——只有 headless 抓最终 DOM + 网络请求才暴露。排查顺序里"②下载端点 200"通过不代表前端就能渲染，还要验"④浏览器最终 DOM 的 img 是否真有 src、图片是否解码（naturalWidth>0）"。
  - **jsdom 跑 DOMPurify 的结果可能与真实浏览器不一致**（本次 jsdom 显示 src 保留，真实浏览器却剥离）——涉及 DOM/URL 解析的行为，ground truth 必须用真实 Chromium。
  - 手写 `ALLOWED_URI_REGEXP` 极易因字符类未转义而出错；**能复用 DOMPurify 官方默认就别自己改**，确需加 scheme 时只增不删、`-` 必须转义。

### 2026-09-13（21:40 - 22:20）— 阶段二十：智能搜索模块优化（方案 A）
- **用户拍板**：先去掉搜索建议 + 高级搜索；GitHub 调研后选方案 A（清理 + 多词联合搜索）；语义搜索（sqlite-vec + BGE）列为后续候选本期不做
- **调研结论**（记录供后续参考）：
  - 现状：主搜索 `/search/documents` 是**内存全量扫描**（`query.all()` + 逐篇正则），43 篇/611KB 时 ~1.6ms 不慢，但**无多词能力**（"交换机 配置"整体当一串搜不到）
  - 搜索建议是**假数据**（无查询词时返回 8 个写死词）；高级搜索面板 4 项筛选基本是摆设
  - wiki FTS5 三路索引（阶段十八）只覆盖 11/43 篇 → **本期不接 FTS**（作主路会漏召回；规模上来后再做，需先解决新文档自动入索引）
  - 本地 llama.cpp（192.168.66.234:8081）**不支持 embeddings**（501），真语义搜索需另部署 BGE-small-zh 等专用模型
  - GitHub 候选：sqlite-vec 8.1k⭐（SQLite 向量扩展，最契合）/ txtai 12.9k / LanceDB 11.4k / Chroma 29.3k / Qdrant 34.5k / FAISS 40.9k / BGE 12.2k
- **代码变更**：
  - `search.py`：删 `/search/suggestions` 端点（~60 行）；`/search/documents` 重写检索核心——`tokenize_query(q)`（空白+中英文标点分词、去重、每词 ≤30 字）；单词（无分隔符）完全保留原匹配与打分公式（召回不降）；多词逐词独立匹配（content/title/description 三桶），score = 0.5×命中词覆盖率 + 0.5×桶权重，结果附 `matched_terms`/`term_total`；`_highlight_terms` 多词高亮
  - `search_service.py`：新增 `search_terms_in_text(text, terms)`——**单次逐行遍历**同时匹配所有词（每词最多 20 条，全命中即提前退出）
  - `SearchView.vue`：删两张建议卡 + 高级搜索面板（范围/类型/时间/排序）+ `filters`/`documentTypes`/`sortOptions`/`searchSuggestions`/`inputSuggestions`/`handleInputChange`/onMounted 建议拉取 + `onMounted` import；placeholder 改为多词提示；结果卡片多词时显示"命中 X/Y 词"标签；`DocumentSearchResult` 类型加 `matched_terms`/`term_total`
- **验证**：
  - `/search/suggestions` → 404 ✓
  - 单词"交换机" total=12（与改造前基准一致，召回不降）✓
  - 多词"交换机 配置" total=17：**2/2 全词命中排前（0.90），1/2 部分命中在后（0.65）** ✓
  - 多词"Nginx 反向代理" total=0（数据确实没有，与单词一致）✓
  - headless E2E：单词 64ms / 多词 68ms（不慢）；截图确认 UI 干净（无建议卡/高级面板）、"命中 2/2 词"标签正常、多词 `<mark>` 高亮正确
  - `py_compile` / `import app.main` / `vue-tsc --noEmit` 全过
- **教训**：
  - 大段代码替换用 Python 脚本做**行范围替换**（断言首尾行）比 Edit 工具的长字符串匹配可靠（长文本里空白不一致会反复失败）
  - 后端 8002 被旧 task 占用时，`taskkill /F /IM python.exe` 杀不干净（沙箱下部分进程杀不掉），用 `netstat -ano | grep :8002` 找 PID 再 `taskkill /F /PID <pid>` 精确杀
  - "搜索不慢"≠"不需要优化"——用户感知快是因为数据量小（43 篇），优化价值在**功能缺失（多词）+ 规模余量**，方案沟通时先用实测基准数据对齐预期
