# @architecture.md — 文件架构（关键文件）

> ⚠️ AI 在本项目下写**任何代码前必须完整阅读本文件**。
> 依据：`D:\sdxtywzsk\VIBE_CODING_GUIDE.md` 阶段二"必须强调的规则（标记为 Always）"。
> 本文件列出仓库中**每个目录与关键文件的职责**，便于后续修改时快速定位。

---

## 仓库根

```
runyang-bridge-docs-system/
├── README.md              # 项目说明（用户视角）
├── AI_FEATURE_CHECKLIST.md
├── AI_SERVICE_DEPLOYMENT.md
├── FRONTEND_AI_INTEGRATION.md
├── .claude/settings.local.json
├── .mcp.json              # promptx-local MCP 服务
├── install-complete.bat / start-services.bat / stop-services.bat
├── backend/               # FastAPI 后端（含 AI Wiki MCP server，挂载 /mcp）
├── frontend/              # Vue 3 前端
├── docs/                  # 项目级文档（API、架构、部署等）
└── memory-bank/           # ⭐ Vibe Coding 记忆库（本目录）
```

> **2026-09-12 变更**：`android/` 目录及后端移动端 API（mobile 端点/schema/JWT 函数）已整体移除（阶段十一）。
> 数据查询与利用改由 AI 工作台（如 WorkBuddy）通过 **AI Wiki MCP**（`http://<host>:8002/mcp`，**12 个 tools**：KB 8 + 图像 2 + 资产 2，见 `docs/AI-Wiki-MCP调用文档.md`）接入。
>
> **2026-09-12 变更（阶段十五）**：修复 `main.py` 挂载 MCP 时用 `app.router.lifespan_context = mcp_app.lifespan` **整体覆盖**主应用 lifespan 导致后台提取 worker 永不启动（上传卡 pending）的 P0 回归。
> 现改为：模块级 `mcp_lifespan`（默认空），MCP 挂载成功块里 `mcp_lifespan = mcp_app.lifespan`；主 `lifespan` 内 `async with mcp_lifespan(app)` 执行原 3 步（bcrypt/默认用户/后台 worker）。**改 `main.py` 后需手动重启后端**（本机 8002 无 supervisor 自动重生）。
>
> **2026-09-12 变更（阶段十三）**：统一 AI 服务配置"保存后立即生效"——`Settings` 新增 `reload()`（写 .env 后热刷新内存单例），`extraction_config.py` PUT 写完 .env 调 `settings.reload()`，无需重启。
> 新增配置项 `AI_ALL_FORMATS_AI`（默认 false）：开启后**所有格式**文档（docx/xlsx/txt 等）都"本地引擎先出 md → 统一 AI 规整为最终 md"，AI 失败按 `AI_FALLBACK_TO_LOCAL` 降级本地；关闭则仅 PDF+图片 走 AI。
> 收口位置：`backend/app/services/extraction/router.py`（`_refine_with_ai`）+ `ai_client.py`（`UnifiedAIClient.parse_text`）。
>
> **2026-09-13 变更（阶段十六）**：统一三处文档下载点（预览 / 列表行 / 搜索结果）为"原文件 / Markdown"二选一。
> 后端 `wiki.py` 补 `from pathlib import Path`（此前缺 import 致原文件下载 500），markdown 分支加"无 `wiki/{id}.md` 副本 → 回退 DB `content` 拼 Response"兜底。
> 前端新增共享工具 `frontend/src/utils/file-download.ts`（`downloadWikiDocument(docId, type, fallbackTitle)`），`DocumentView.vue` + `SearchView.vue` 三处按钮全部改为 `NDropdown` + 委托该工具，统一打到 `GET /api/v1/wiki/download/{id}?type=original|markdown`。
>
> **2026-09-13 变更（阶段十七）**：修复 `SettingsView.vue` `onMounted` 遗漏 `loadExtractionConfig()` 调用（阶段十三重构删旧 `loadAIConfig()` 时未补新调用）→ 设置页打开时 AI 配置从不拉取、停在默认值（误报"恢复默认"）。现 onMounted 内直接调 `loadExtractionConfig()`。后端配置一直安全，无需改动。

> **2026-09-14 变更（阶段二十·20.7）**：修复"下载原文件扩展名被误识别"（如标题以日期 `2025.12` 结尾 → 存成 `.12`）。
> 双因素根因：① `main.py` CORSMiddleware 未设 `expose_headers`，跨域 fetch（:5173→:8002）JS 读不到 `Content-Disposition`（读为 null）→ 前端回退用标题当文件名；② `file-download.ts` 旧正则解析 `filename*=utf-8''...` 只截到 `utf-8`。
> 现：`main.py` CORS 加 `expose_headers=["Content-Disposition","Content-Length"]`（**改 main.py 后需手动重启后端**）；`file-download.ts` 重写 `parseFilenameFromDisposition`（RFC5987 优先 + 普通 filename + 新增 `sanitizeFilename`；header 缺失/解析失败时用后端 `file_type` 纠正扩展名兜底，markdown 强制 `.md`），`downloadWikiDocument` 增加 `fileType?` 参数；`DocumentView.vue` / `SearchView.vue` 三处调用透传 `file_type`。

> **2026-09-14 变更（阶段二十一）**：补齐 `.env` CORS auto 模式全套配置——部署到其它服务器时 `.env` 若被精简（只剩 `CORS_AUTO_DETECT=true` 一行），其他字段依赖 `Settings` 默认值回退到"只放行 localhost"，其他电脑无法 LAN 访问。**零代码改动**，只在 `backend/.env` 把 `CORS_MODE=auto` / `CORS_AUTO_DETECT=true` / `CORS_INCLUDE_LOCALHOST=true` / `CORS_FRONTEND_PORT=5173` 全部显式写齐。**用户必须重启后端进程**（`Settings` 单例 import 时只读一次 `.env`），重启后日志应出现 `[CORS] 检测到本机IP：[...]` 且最终配置源数 ≥ 3。若仍只有 2 个源（说明 `_detect_local_ips()` 在该服务器网络隔离下拿不到 LAN IP），可取消 `CORS_CUSTOM_ORIGINS` 注释手动指定 `http://<服务器IP>:5173` 兜底。

> **2026-09-14 变更（阶段二十二）**：新增 `update.sh`（Linux）/ `update.bat`（Windows）一键更新脚本——部署到其它服务器后日常更新代码用。流程：防御性检查（工作区脏则中止）→ 备份 `.env` → `git pull --ff-only origin main` → 后端 `pip install --upgrade-strategy only-if-needed` → 前端 `npm install` → 重启后端（前端 vite dev HMR 自动生效）。**严格快进 + 不动 `.gitignore` 里的一切**（`.env` / 数据库 / 上传文件 / venv / node_modules / 日志 / 图片库），所以本地数据零风险。回滚命令 `git reset --hard HEAD@{1}`。`docs/部署指南.md` "版本更新"段同步加脚本入口。

> **2026-09-14 变更（阶段二十二·完整版）**：用户反馈"上传更新会卡很久"——调研后**找到推送卡死的真正根因**：WorkBuddy 代理 + Git Credential Manager 的 Basic Auth 头被 GitHub fine-grained PAT 拒绝（不只是代理问题，GIT_TRACE 显示服务器返回真 `401 Unauthorized`）。**新增 `push.sh` / `push.bat` 一键推送脚本**：解法 = `env -u HTTPS_PROXY -u HTTP_PROXY` 取消代理 + `-c "url.https://x-access-token:${TOKEN}@github.com/heartsward/.insteadOf=..."` 让 git 用 fine-grained PAT 的正确认证格式 + `--force-with-lease` 处理之前 Git Data API 推送造成的 diverged 状态。**实测 push.sh 一键成功**（远端 main 从 `a339aed1` → `dba330d`，ahead 2 commit）。`GIT-COMMANDS.md` 同步加入完整命令速查（其它电脑下载 / 本机 push / push 卡顿排查）。脚本与文档清单从 7 个扩到 9 个真实脚本 + 1 个命令速查。

> **2026-09-15 变更（阶段二十三）**：① 预览去掉"提取的图片"展示但保留图片提取：`content_extractor.py` 提取流程不再调 `insert_image_refs`、独立图片文档不再把图引用拼到 MD；`wiki.py` `/rebuild?reextract_images=true` 路径不再写 MD；`image_extractor.py` 删除 `insert_image_refs` 函数 + `_PAGE_HEADER_RE` + 未用的 `import re`。图片本体仍走 `extract_pdf_images` / `register_image_doc` 落盘 + `idx.add_image` 入 `wiki_images` 表 + `describe_image_sync` AI 中文描述——图片域 MCP（`get_doc_images` / `search_images`）继续可用。② 预览工具栏右侧增加"提取内容/原文件"切换：所有格式都显示（之前仅 PDF/图片），非 PDF/图片切到"原文件"模式降级为下载提示卡；`DocumentView.vue` / `SearchView.vue` 的 `shouldShowViewToggle` 改为 `return true`，工具栏由 `n-space`（toggle 左）改为 flex 布局（toggle 右，`margin-left:auto`）。

> **2026-09-15 变更（阶段二十四）**：Office 格式在线预览（LibreOffice 转 PDF + iframe）。
> - 新增 `backend/app/services/preview_converter.py`（单例 + 路径探测 + 缓存 + 文件锁 + 独立进度状态）
>   - soffice 路径探测顺序：`.env LIBREOFFICE_BIN_PATH` → 平台标准路径 → `PATH` 兜底
>   - 缓存：`backend/cache/converted_pdfs/{doc_id}.pdf`，按 doc_id + 源文件 mtime 比对失效（覆盖上传自动重转）
>   - 进度状态（独立通道）：`task_status/preview_convert_{doc_id}.json`，与内容提取 `extract_{doc_id}_*.json` 完全分离
>   - 文件锁：进程内 `threading.Lock` + 跨进程 `fcntl.flock`（Linux/macOS）/ `msvcrt.locking`（Windows）/ noop fallback
>   - 支持：.doc/.docx/.xls/.xlsx/.ppt/.pptx/.odt/.ods/.odp/.rtf/.epub/.csv（14 种）
>   - **关键踩坑**：soffice 转换在 TemporaryDirectory with 块中，`return pdf_out` 后 `__exit__` 会清理目录 → 改为返回 `bytes` 内容由外层写缓存（已修复，实测 7.4s 转换 53KB xlsx → 733KB PDF）
> - 新增 3 个端点：`GET /api/v1/documents/{id}/converted-pdf`（返回 inline PDF，缓存命中秒出；缓存未命中同步触发）、`GET /api/v1/documents/{id}/conversion-status`（前端轮询，独立于 `/tasks/document/{id}/extraction-status`）、`POST /api/v1/documents/{id}/convert`（后台预热）
> - 前端 `DocumentView.vue` / `SearchView.vue` 增加"Office 文档分支"：`isOfficeFile()` 判断 → loading 覆盖层（带 elapsed 计时 + "与内容提取独立"提示）→ iframe 显示 PDF；失败 fallback 到下载卡
> - `Settings` 新增 `LIBREOFFICE_BIN_PATH`（可选自定义）+ `PREVIEW_CONVERT_TIMEOUT`（默认 120s）
> - `.gitignore` 加 `backend/cache/`（运行时缓存不入版本库）
> - 重写 `docs/环境安装-LibreOffice.md`（阶段十九前是讲"内容提取"；本次改为讲"PDF 预览转换"，明确边界与 anydoc 解耦）

> **2026-09-15 变更（阶段二十六·26.3 最终版）**：上传白名单定为 **22 种** = Word 3（.doc/.docx/.docm）+ Excel 4（.xls/.xlsx/.xlsm/.xlsb）+ PowerPoint 7（.ppt/.pptx/.pptm/.pps/.ppsx/.ppsm/.pot）+ .epub/.csv/.pdf + 图片 3（.jpg/.jpeg/.png）+ 文本 2（.txt/.md）。
> - **`.json` 不支持**（用户拍板：anydoc 无法把 JSON 转 Markdown）→ 清除全部 json 预览代码：`config.py` ALLOWED 去 json；`preview_converter.py` 删 `TEXT_PREVIEW_TYPES`/`is_supported_text_type`/`TextTooLargeError`/`read_text_content`/`_read_with_fallback`/`_read_and_format_json`；`documents.py` 删 `GET /{id}/text-content` 端点；`text_extractor.py` `.json` 出 SUPPORTED_EXTENSIONS、删 `_format_json` 分支
> - `SUPPORTED_OFFICE_TYPES` 扩到 **20 种**（+PPT 7 种）；anydoc 已支持全部 PPT 格式（提取零改动）；LibreOffice 已实测支持 PPT 转 PDF（预览零改动）
> - 前端 `DocumentView.vue`/`SearchView.vue`：`OFFICE_EXTENSIONS`/`OFFICE_TYPES` 扩 20 种；删 `isJsonFile` 及 JSON `<pre>` 分支；**`shouldShowViewToggle` 改为只对 4 类显示**（Office 含 PPT/CSV + epub → LibreOffice 转 PDF；PDF → iframe；图片 → `<img>`），文本类（.txt/.md）不显示切换按钮
> - 上传界面说明文字重写：按 Word/Excel/PowerPoint/其他 + 文本类分组列全 22 种，`accept` 属性同步

---

## 1. backend/ — FastAPI 后端

入口：`backend/app/main.py`，启动端口 **8002**。

### 1.1 `backend/app/api/` — API 路由层
- `api_v1.py` — v1 路由聚合（所有 `/api/v1/*` 都在此注册）
- `endpoints/` — 各功能模块的端点
  | 文件 | 职责 |
  |------|------|
  | `auth.py` | 登录/登出/me |
  | `users.py`（settings 内） | 用户管理 |
  | `documents.py` | 文档 CRUD、获取内容 |
  | `assets.py` | 资产 CRUD、批量、导出、文件提取 |
  | `categories.py` | 文档分类管理 |
  | `search.py` | 全文搜索（阶段二十起支持**多词联合搜索**：`tokenize_query` **仅按空格**分词（IP/URL 等含标点串视为一个词）+ 命中词数加权；`/search/suggestions` 端点已删除；`/search/preview` 多词时调 `search_service.highlight_terms` 注入带 `data-term` 的 `<mark>`） |
  | `upload.py` / `upload_multiple.py` / `file_upload.py` | 单文件 / 多文件上传 |
  | `tasks.py` | 后台任务状态 |
  | `settings.py` | 用户/系统设置 |
  | `system.py` / `system_config.py` | 系统级配置 |
  | `voice.py` | 语音/语音转写 |
  | `encoding_fix.py` | 编码修复工具端点 |

### 1.2 `backend/app/core/` — 核心基础设施
- `config.py` — Settings（Pydantic BaseSettings，DB/JWT/CORS/上传大小等）
- `security.py` — JWT 签发与校验、密码哈希（Bcrypt）
- `deps.py` — FastAPI Depends（current_user、db session 等）
- `cache.py` — 内存缓存
- `search_engine.py` — 搜索引擎实现（内容 > 标题 > 描述的权重排序）
- `nlp_processor.py` — NLP 预处理

### 1.3 `backend/app/crud/` — 数据库 CRUD
- `base.py` — 通用 CRUD 基类
- `user.py` / `document.py` / `asset.py` / `category.py` — 各实体的增删改查

### 1.4 `backend/app/models/` — SQLAlchemy ORM 模型
- `user.py` / `document.py` / `asset.py` / `ai_config.py` / `system_config.py`

### 1.5 `backend/app/schemas/` — Pydantic 数据模式
- `user.py` / `document.py` / `asset.py` / `category.py` / `system_config.py` / `voice.py`

### 1.6 `backend/app/services/` — 业务逻辑服务
- `search_service.py` — 文档内容提取（PDF/Docx/Excel/TXT）+ 搜索（`highlight_text` 单词高亮 / `highlight_terms` 多词高亮带 `data-term`，长词优先+重叠去重 / `search_terms_in_text` 多词单次遍历匹配）
- `content_extractor.py` / `enhanced_asset_extractor.py` / `asset_extractor.py` — 资产/内容提取
- `document_analyzer.py` / `document_formatter.py` — 文档分析与格式化
- `file_manager.py` — 文件读写
- `ocr_extractor.py` — Tesseract OCR
- `image_preprocessor.py` — 图像预处理
- `content_quality_validator.py` / `smart_text_processor.py` — 文本质量与处理
- `streaming_processor.py` / `background_tasks.py` — 流式与后台任务
- `system_monitor.py` / `log_manager.py` — 系统监控与日志
- `ai/` — AI 子系统（providers、extractors、utils、cache、rate_limiter、cost_tracker）
- `wiki/` — ⭐ AI Wiki 子系统（阶段十起）：
  - `storage.py` — MD 副本 + frontmatter 读写
  - `metadata.py` — AI 元数据生成（title/tags/**doc_category**）+ **图片描述**（`IMAGE_DESCRIBE_PROMPT`/`describe_image_via_ai`，阶段十八）
  - `index.py` — FTS5 三路索引（unicode61 + trigram + LIKE 兜底）+ **图片索引**（`wiki_images`/`images_fts`，阶段十八）+ `search`/`get_doc`/`search_images`/`list_categories`
  - `mcp_server.py` — **12 个 MCP tools**（文档域 search_kb/get_doc/get_doc_content/list_backlinks/list_tags/generate_report + 图片域 get_doc_images/search_images/list_categories + **资产域 search_assets/get_asset/list_assets**，阶段二十·20.8/20.9：`search_assets` 14 字段模糊搜索，**返回按命中数自适应**——命中 1 台直接全字段含 username/password（一轮作答），多台返回 7 列摘要+hint（不含密码）；`get_asset` 按 ID 取全字段；`list_assets` 轻量清单不含账号密码）
  - `image_extractor.py` — ⭐ **PDF/图片提取器（阶段十八）**：dict-mode 提图 + 裁剪兜底 + 独立图片登记 + 图引用插入
  - 图片落盘目录：`backend/wiki/images/{doc_id}/`

### 1.7 `backend/app/db/` — 数据库
- `database.py` — engine、SessionLocal
- `base_class.py` — Declarative Base

### 1.8 `backend/app/utils/`
- `encoding_detector.py` / `timezone_utils.py`

### 1.9 顶层文件
- `backend/database_integrated_server.py`（开发者文档中提及，作为另一入口）
- `backend/uploads/`、`backend/task_status/`
- `requirements.txt` / `requirements-windows.txt`

### 2.0 根目录脚本清单（**9 个真实脚本 + 1 个命令速查**）
| 脚本 | 平台 | 用途 |
|------|------|------|
| `install-complete.bat` | Win | 首次部署：建 venv + 装前后端依赖 |
| `start-services.bat` | Win | 启动后端 :8002 + 前端 :5173（按端口定位 PID，安全） |
| `stop-services.bat` | Win | 按端口 8002/5173 精确定位 PID 停止（不误杀其他进程） |
| `start-services.sh` | Linux/macOS | 同 start-services.bat |
| `stop-services.sh` | Linux/macOS | 同 stop-services.bat |
| **`update.sh`** ⭐ | Linux/macOS | **一键更新代码并重启后端**（阶段二十二） |
| **`update.bat`** ⭐ | Win | **一键更新代码并重启后端**（阶段二十二） |
| **`push.sh`** ⭐ | Linux/macOS | **一键推送到 GitHub**（解决 `git push` 卡死问题，阶段二十二） |
| **`push.bat`** ⭐ | Win | **一键推送到 GitHub**（同 push.sh） |
| `GIT-COMMANDS.md` | 通用 | 完整 git 命令速查（其它电脑下载/本机 push/push 卡顿排查） |

---

## 2. frontend/ — Vue 3 前端

入口：`frontend/src/main.ts`，启动端口 **5173**。
Vite 配置：根目录 `vite.config.ts`。

### 2.1 `frontend/src/views/` — 页面视图
| 文件 | 路由 | 权限 | 职责 |
|------|------|------|------|
| `WelcomeView.vue` | `/` | 公开 | 首页 |
| `LoginView.vue` | `/login` | 仅游客 | 登录 |
| `RegisterView.vue` | `/register` | 仅游客 | 注册 |
| `DocumentView.vue` | `/documents` | 需登录 | 文档管理 |
| `SearchView.vue` | `/search` | 需登录 | 搜索（阶段二十起：多词联合搜索 + 预览 Markdown 渲染对齐文档管理 + 多词分别导航 + 超管预览内编辑） |
| `EnhancedSearchView.vue` | (按路由) | 需登录 | 增强搜索（新版） |
| `AssetView.vue` | `/assets` | 需登录 | 资产管理 |
| `CategoryView.vue` | `/categories` | 需登录 | 分类管理 |
| `SettingsView.vue` | `/settings` | 需登录 | 系统/用户设置 |
| `DashboardView.vue` | (按路由) | 需登录 | 仪表盘 |

### 2.2 `frontend/src/components/` — 复用组件
- `NavigationMenu.vue` — 侧边导航
- `PageLayout.vue` / `EnhancedLayout.vue` — 页面布局
- `CategoryManagement.vue` — 分类管理组件

### 2.3 `frontend/src/services/` — API 服务层（按模块拆分）
- `api.ts` — Axios 实例 + 拦截器
- `auth.ts` / `user.ts`
- `document.ts` / `asset.ts` / `category.ts`
- `search.ts`
- `upload.ts` / `task.ts`
- `settings.ts` / `system-config.ts`
- `ai.ts` — AI 功能调用
- `index.ts` — 统一导出

### 2.4 `frontend/src/router/index.ts` — 路由配置
所有路由 `meta.requiresAuth` 或 `requiresGuest` 已在文件内标注。

### 2.5 `frontend/src/types/` — TypeScript 类型
- `api.ts` / `asset.ts` 等

### 2.6 `frontend/src/utils/`
- `index.ts` — 通用工具
- `xss-protection.ts` — 前端 XSS 防护
- `file-download.ts` — ⭐ 三处下载点共享工具（阶段十六）：`downloadWikiDocument(docId, type, fallbackTitle)`，统一走 wiki 下载端点 + Bearer + blob 触发

### 2.7 `frontend/src/assets/` — 静态资源（base.css / main.css / logo.svg）

### 2.8 顶层
- `package.json` / `vite.config.ts` / `tsconfig.json`
- `public/runyang-logo.svg`
- `.env.production`

---

## 3. AI Wiki MCP — 数据查询服务（替代原 Android 客户端）

> 2026-09-12 起：Android 客户端（原 `android/`）已移除。数据查询与利用统一走 AI Wiki MCP。

- 挂载点：`http://<host>:8002/mcp`（FastMCP HTTP transport，见 `main.py`）
- 实现：`backend/app/services/wiki/mcp_server.py`（`register_tools`）
- **11 个 tools**（阶段十八 +3、阶段二十·20.8 +2）：
  - 检索类：`search_kb`（含 `category` 过滤）/ `get_doc` / `get_doc_content` / `list_backlinks` / `list_tags` / `generate_report`
  - 图片类（阶段十八）：`get_doc_images(doc_id)` / `search_images(query, top_k, doc_id?)` / `list_categories()` —— 均返回带 `url` 字段（指向 `GET /wiki/images/{id}/{file}`，需 Bearer token）
  - 资产类（阶段二十·20.8/20.9，数据源 `assets` 表，直接 SQLAlchemy 查询不走 FTS）：
    - `search_assets(query, top_k, asset_type?, network_location?, status?)`：14 字段 `ilike` 模糊搜索。**20.9 起返回按命中数自适应**（提速：单台命中免二次调用）——命中 1 台直接返回全字段 dict（含 username/password）；多台返回 `{"total","assets":[7列摘要],"hint"}`（摘要不含密码，防止一次吐多台设备密码）；0 台返回 `{"total":0,"assets":[]}`
    - `get_asset(asset_id)`：按 ID 取单台全字段，不存在返回 `{"error": ...}`
    - `list_assets(asset_type?, network_location?, status?, limit=200)`：轻量清单（id/name/ip/hostname/类型/状态/网络），**不含账号密码**，供"有哪些设备"类概览问题
    - 密码口径：与资产导出端点一致（库内明文，确认具体哪台后才返回）
- 接入方式：AI 工作台（WorkBuddy 等）配置 MCP server 指向 `/mcp` 即可
- 数据源：`backend/wiki/{doc_id}.md`（MD 副本，含图片引用）+ SQLite FTS5 索引（`wiki/index.py`）+ 图片库（`wiki/images/{doc_id}/`，`wiki_images` 表登记 + AI 中文描述）
- **图片 URL 注意**：MCP 返回的 `url` 用 `WIKI_PUBLIC_HOST` 拼（默认 127.0.0.1，局域网需改服务器 IP）；下载需 `Authorization: Bearer <token>`

---

## 4. docs/ — 项目级文档

> 这些是面向人和子系统的参考资料，**不等同于** `memory-bank/`。新建 memory-bank 文档时不要重复 docs/ 内容，只引用。

| 文档 | 用途 |
|------|------|
| `API接口文档.md` | API 接口字典 |
| `系统架构文档.md` | 系统级架构说明 |
| `开发者文档.md` | 开发环境与项目结构 |
| `用户操作手册.md` | 终端用户使用手册 |
| `部署指南.md` / `部署指南-GitHub.md` | 部署 |
| `配置指南-前端.md` / `-CORS.md` / `-域名.md` / `-网络.md` / `-综合.md` | 各维度配置 |
| `OCR优化说明.md` | OCR 模块说明 |
| `AI服务部署.md` / `AI-Wiki部署与使用指南.md` | AI 引擎与 Wiki MCP 部署 |
| `版本升级指南.md` / `版本更新日志.md` / `系统更新日志.md` | 版本演进 |
| `环境安装-LibreOffice.md` / `生产环境脚本说明.md` | 环境与脚本 |
| `README.md`（docs 内） | 文档目录索引 |

---

## 5. memory-bank/ — 本目录（Vibe Coding 上下文核心）

| 文件 | 用途 | 是否关键 (@) |
|------|------|------------|
| `@architecture.md` | 本文件 — 文件架构 | ✅ |
| `@product-requirements-document.md` | 产品需求 | ✅ |
| `@tech-stack.md` | 技术栈 | ✅ |
| `@implementation-plan.md` | 分步实施计划（不含代码） | ✅ |
| `progress.md` | 进度追踪 | ❌ |
| `feature-*.md`（可选） | 功能实现笔记 | ❌ |

---

## 6. 修改本项目的"动手前"清单

每次准备修改前，先确认：
1. 已读 `@architecture.md`（本文件）+ `@product-requirements-document.md` + `@tech-stack.md`
2. 改动落在哪一个模块（api/endpoints、X service、view、component）已明确
3. 改动是否会触达以下"非可改"边界（如要破坏需先和用户确认）：
   - 数据库表结构（`backend/app/models/`）
   - 鉴权/JWT 配置（`backend/app/core/security.py`、`config.py`）
   - 前端路由 `meta` 权限位（`frontend/src/router/index.ts`）
   - 默认管理员账户（`admin` / `admin123`）
   - 上传大小/扩展名白名单（`config.py`）
4. 改动对应到 `@implementation-plan.md` 哪一步；如未列出，**先更新计划再动手**

---

_生成时间：2026-09-11，基于首次克隆后的实际目录扫描（265 个文件）_
_维护人：开发者在每次重大里程碑后更新本文件_