# @implementation-plan.md — 分步实施计划

> ⚠️ AI 在写任何代码前必须完整阅读本文件。
> 依据：`VIBE_CODING_GUIDE.md` 阶段三。
> **本计划不含代码**，只写小而具体、可审计、可执行的指令；每一步都必须有验证。

---

## 阶段零：已完成（基线）

- ✅ 克隆仓库到 `D:\sdxtywzsk\runyang-bridge-docs-system`
- ✅ 阅读 README、docs/ 系统架构文档、开发者文档
- ✅ 定位 `VIBE_CODING_GUIDE.md` 并写入工作区长期记忆
- ✅ 建立 `memory-bank/` 及 5 个核心文件（@architecture / @PRD / @tech-stack / @implementation-plan / progress）

---

## 阶段一：环境与连通性验证（首次启动前必做）

### 步骤 1.1 — 验证后端依赖可装
- **做什么**：在 `backend/` 执行 `pip install -r requirements.txt`（Windows 用 `requirements-windows.txt`）
- **怎么验**：`pip list | grep -E "fastapi|sqlalchemy|pyjwt|bcrypt|pypdf2|python-docx|openpyxl"` 全部存在
- **通过标准**：无 ImportError；版本号与 `@tech-stack.md` 一致

### 步骤 1.2 — 验证前端依赖可装
- **做什么**：在 `frontend/` 执行 `npm install`
- **怎么验**：`npm run type-check` 通过；`node_modules` 含 `vue@^3.5`、`naive-ui@^2.42`、`vite@^7`
- **通过标准**：TS 编译 0 error

### 步骤 1.3 — 启动后端 + 探活
- **做什么**：`uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload`
- **怎么验**：`curl http://localhost:8002/docs` 返回 200；`curl http://localhost:8002/api/v1/auth/login -X POST -d '{}'` 收到结构化 422
- **通过标准**：进程不退出；OpenAPI JSON 可见

### 步骤 1.4 — 启动前端 + 探活
- **做什么**：`npm run dev`
- **怎么验**：浏览器访问 `http://localhost:5173` 看到 Welcome 页；F12 Network 无 4xx
- **通过标准**：登录页 `/login` 可渲染

### 步骤 1.5 — 默认管理员登录
- **做什么**：用 `admin` / `admin123` 登录
- **怎么验**：拿到 JWT；可访问 `/documents`
- **通过标准**：登录后所有需要 `requiresAuth` 的页面可达

---

## 阶段二：理解性冒烟（不写代码，只读 + 验证）

> 这一阶段目标：让 AI 与你**对每个核心模块的工作机制**达成一致理解。

### 步骤 2.1 — 走通"上传文档 → 搜索 → 预览"链路
- **做什么**：手动上传一个测试 PDF；触发全文搜索；点击预览
- **怎么验**：能看到提取出的中文内容；搜索关键词命中；预览页正常
- **产出**：在 `progress.md` 记录每一步的实际表现（如有异常，先列问题再继续）

### 步骤 2.2 — 走通"上传 Excel → 资产抽取 → 列表"链路
- **做什么**：上传一份设备台账 Excel；调用 `/api/v1/assets/file-extract`；写入资产列表
- **怎么验**：列表展示新资产；字段（类型、部门、状态）抽取正确
- **产出**：记录抽取准确率与失败用例

### 步骤 2.3 — AI 功能冒烟
- **做什么**：在 AI 配置页选择一个 Provider，填入 Key，调用一次资产抽取
- **怎么验**：成功返回结构化 JSON；记录耗时、token 消耗、成本
- **产出**：写入 `progress.md` 的"AI 现状"小节

---

## 阶段三：实施规划（按需启动具体任务）

> 真实修改任务在启动前必须先**把对应的小步骤加入本文件**（含"做什么 / 怎么验 / 通过标准"三段），再让 AI 执行。
> 严禁让 AI 跳过本步骤直接动手。

### 模板：新增任务 X 的子步骤

```markdown
### 步骤 X.Y — [任务名]
- **做什么**：[一句话，明确文件/模块边界]
- **能改什么**：[白名单：哪些文件、哪些接口]
- **不能改什么**：[黑名单：模型结构、JWT、admin 账户、CORS 白名单等]
- **怎么验**：[测试命令 / 浏览器步骤 / curl]
- **通过标准**：[明确可观察的成功标志]
- **回退方案**：[如何 git reset / 还原文件]
```

### 待办池（按优先级排，后续按需展开）
- P1 修复某个 bug（待你指定）
- P1 新增某个功能（待你指定）
- P2 AI Provider 接入（如新增某模型）
- P2 性能优化（搜索/上传）
- P3 Android 端某个模块补全
- P3 文档完善

---

## 阶段二·A：P0 安全/功能故障修复（用户批准于 2026-09-11 10:37）

> 严格按"一次只改一个模块"原则，**4 个子步骤串行执行**，每步完成后跑验证再进入下一步。

### 步骤 A.1 — P0-4 修复 `/api/v1/system/health` 的 SQLAlchemy 2.0 报错
- **做什么**：定位 `backend/app/api/endpoints/system.py` 中执行 `SELECT 1` 的位置，改用 `text("SELECT 1")` 显式包裹
- **能改什么**：仅 `backend/app/api/endpoints/system.py` 的 SQL 执行语句
- **不能改什么**：健康检查的 URL/响应结构（避免前端误判）；不引入新依赖
- **怎么验**：
  1. 重启后端
  2. `curl http://127.0.0.1:8002/api/v1/system/health` 返回 `{"status":"healthy", ...}` 而不是 `unhealthy`
  3. 检查后端启动日志无 `Textual SQL expression` 警告
- **通过标准**：`status == "healthy"`，启动日志无 SQLAlchemy 警告
- **回退方案**：`git checkout HEAD -- backend/app/api/endpoints/system.py`

### 步骤 A.2 — P0-3 修复 EnhancedSearchView 的搜索路径
- **做什么**：`frontend/src/views/EnhancedSearchView.vue:396` 调用 `/search`，改为 `/search/documents`
- **能改什么**：仅该文件中的 API 路径字符串
- **不能改什么**：不动 SearchView.vue（它已正确）；不改 query 参数结构
- **怎么验**：
  1. 浏览器访问 `/search`（EnhancedSearchView），输入关键词点搜索
  2. 浏览器 DevTools Network 看到请求 `GET /api/v1/search/documents?q=...` 返回 200
  3. 结果正常展示
- **通过标准**：搜索功能可用；devtools 无 404
- **回退方案**：`git checkout HEAD -- frontend/src/views/EnhancedSearchView.vue`

### 步骤 A.3 — P0-2 修复 documents 列表端点绕过鉴权
- **做什么**：`backend/app/api/endpoints/documents.py:75-99` 的 `read_documents()` 把 `Depends(get_optional_user)` 改为 `Depends(get_current_active_user)`
- **能改什么**：仅该端点的依赖项
- **不能改什么**：
  - 不动 `create_document` 等其他端点（它们已经用 `get_current_active_user`）
  - 不动文档 schema / 模型
  - 不影响已有合法调用方（所有受保护页面都带 token）
- **怎么验**：
  1. 重启后端
  2. 无 token 请求 `GET /api/v1/documents/` → 期望 `401 Not authenticated`
  3. 带 admin token 请求 → 期望 200 + 列表 JSON
- **通过标准**：未授权访问被拒；已授权访问不受影响
- **回退方案**：`git checkout HEAD -- backend/app/api/endpoints/documents.py`

### 步骤 A.4 — P0-1 收紧 CORS 白名单
- **做什么**：检查 `backend/app/core/config.py` 的 CORS 配置逻辑，关闭"自动嗅探本机 IP + 60 个端口"行为
  - 方案 A（推荐，开发友好）：保留白名单 = `localhost:5173` + `127.0.0.1:5173` + 当前本机IP（手动指定） + 移除自动嗅探
  - 方案 B（最严格）：仅 `localhost:5173` + `127.0.0.1:5173`，生产环境用 env 变量扩展
- **能改什么**：`backend/app/core/config.py` 中与 CORS 相关的逻辑
- **不能改什么**：
  - 不动 CORS 中间件注册（`main.py` 的 `add_middleware`）
  - 不动 API 路由
  - 不影响 HTTPS 协议支持（保留 http+https 双协议仅在明确端口）
- **怎么验**：
  1. 重启后端，启动日志看到 CORS 源 ≤ 5 个
  2. `curl -H "Origin: http://localhost:5173" -I http://127.0.0.1:8002/api/v1/auth/login` 看到 `Access-Control-Allow-Origin`
  3. `curl -H "Origin: http://evil.com" -I ...` **不返回** `Access-Control-Allow-Origin: http://evil.com`
  4. 前端登录功能仍正常
- **通过标准**：CORS 源收紧，合法 origin 仍放行，非法 origin 拒绝
- **回退方案**：`git checkout HEAD -- backend/app/core/config.py`

---

## 阶段二·B：P1/P2 待用户下一轮指令再展开

（占位，本轮不执行）

---

## 阶段二·C：P2-8 产品命名统一（用户批准于 2026-09-11 10:52）

### 决策
- **目标产品名**：`润扬大桥运维资产管理系统`（去掉"文档"二字）
- **范围**（用户确认 2026-09-11 10:52）：仅 **运行时 + memory-bank**
  - ✅ `backend/` （Python 代码中的项目名/响应消息）
  - ✅ `frontend/` （HTML/Vue 中的 title、欢迎语等用户可见字符串）
  - ✅ `memory-bank/`（4 个 @*.md + progress.md）
  - ❌ 不动 `docs/`、`android/`、根目录 `README.md` 与顶层其他 .md

### 步骤 C.1 — 后端命名替换
- **做什么**：将 `backend/` 下 Python 文件中所有 `"润扬大桥运维文档管理系统"` / `"运维文档管理系统"` / `"运维文档"` → 替换为 `"润扬大桥运维资产管理系统"` / `"运维资产管理系统"` / `"运维资产"`
- **能改什么**：字符串常量、响应消息、日志信息
- **不能改什么**：
  - 不动 SQL schema / Pydantic 字段
  - 不动 API 路径、URL、路由前缀
  - 不动 import / 函数名 / 变量名（除非是项目名常量）
- **范围文件**（基于 grep）：
  - `backend/app/main.py`（如有）
  - `backend/app/core/config.py` 的 `PROJECT_NAME`
  - `backend/app/api/endpoints/system.py` 的 `server_name` 等
  - `backend/app/services/smart_text_processor.py`
  - `backend/app/services/document_analyzer.py`
  - `backend/app/services/ai/extractors/document_analyzer.py`
- **怎么验**：
  1. 重启后端
  2. `curl http://127.0.0.1:8002/api/v1/system/info` → `data.system.server_name` 应为"润扬大桥运维资产管理系统"
  3. `curl http://127.0.0.1:8002/health` → `service` 字段同步更新
  4. `grep -rn "运维文档" backend/app/` 应无业务匹配（注释除外）
- **通过标准**：运行时响应体现新名；启动日志使用新名
- **回退方案**：`git checkout HEAD -- backend/app/`

### 步骤 C.2 — 前端命名替换
- **做什么**：将 `frontend/` 下文件中"运维文档管理系统" → "运维资产管理系统"
- **能改什么**：`frontend/index.html` 的 `<title>`/`<meta description>`、Vue 视图中的标题/欢迎语
- **不能改什么**：
  - 不动路由 path / 组件名
  - 不动 API base URL
  - 不动功能代码
- **范围文件**（基于 grep）：
  - `frontend/index.html`
  - `frontend/src/views/WelcomeView.vue`
  - `frontend/src/views/LoginView.vue`
  - `frontend/src/views/RegisterView.vue`
  - `frontend/src/components/NavigationMenu.vue`
  - `frontend/src/components/EnhancedLayout.vue`
- **怎么验**：
  1. Vite HMR 自动加载
  2. 浏览器访问 `http://127.0.0.1:5173/` → 标签页 title 显示"润扬大桥运维资产管理系统"
  3. `curl http://127.0.0.1:5173/ | grep -i "title"` 验证 HTML title
  4. `grep -rn "运维文档" frontend/src/` 应无匹配（注释除外）
- **通过标准**：浏览器 title 与 HTML 元数据统一
- **回退方案**：`git checkout HEAD -- frontend/`

### 步骤 C.3 — memory-bank 同步
- **做什么**：`memory-bank/@architecture.md`、`@product-requirements-document.md`、`progress.md` 中的"运维文档管理系统"全部 → "运维资产管理系统"
- **能改什么**：文档正文
- **不能改什么**：不动 `@architecture.md` 的"能改/不能改"边界描述（除非原本提及产品名）
- **怎么验**：`grep -rn "运维文档" memory-bank/` 应无匹配
- **通过标准**：memory-bank 文档与代码一致

---

## 阶段二·D：P1-7 测试端点生产门禁（用户批准于 2026-09-11 11:08）

### 决策
- **目标**：把 8 个测试/调试端点用 `ENABLE_TEST_ENDPOINTS` 环境变量门禁
- **默认行为**：生产环境 `ENABLE_TEST_ENDPOINTS=False`（默认安全）；开发环境设 `ENABLE_TEST_ENDPOINTS=true`
- **实现策略**：新增可复用依赖 `require_test_endpoints_enabled`，未启用时返回 **404（伪装成不存在）** 比 403 更安全（避免暴露端点存在性）

### 步骤 D.1 — 新增配置项 `ENABLE_TEST_ENDPOINTS`
- **做什么**：在 `backend/app/core/config.py` 增加 `ENABLE_TEST_ENDPOINTS: bool = False`（默认关闭）
- **能改什么**：仅 Settings 类
- **不能改什么**：其他 CORS/JWT 等配置
- **怎么验**：`python -c "from app.core.config import settings; print(settings.ENABLE_TEST_ENDPOINTS)"` 输出 `False`
- **通过标准**：默认安全
- **回退方案**：`git checkout HEAD -- backend/app/core/config.py`

### 步骤 D.2 — 新增依赖 `require_test_endpoints_enabled`
- **做什么**：在 `backend/app/core/deps.py` 增加依赖函数，未启用时抛 `HTTPException(status_code=404)`
- **能改什么**：仅 `deps.py`
- **不能改什么**：已有依赖函数（`get_db` / `get_current_active_user` 等）
- **怎么验**：单独 import 不报错；调用时按 `settings.ENABLE_TEST_ENDPOINTS` 决定返回 200/404
- **通过标准**：复用、可单独测试
- **回退方案**：`git checkout HEAD -- backend/app/core/deps.py`

### 步骤 D.3 — 给 8 个测试/调试端点添加依赖
- **做什么**：在以下端点的函数签名上加 `Depends(require_test_endpoints_enabled)`：
  1. `backend/app/api/endpoints/assets.py:1219` POST `/test-file-upload`
  2. `backend/app/api/endpoints/assets.py:1253` POST `/test-with-db`
  3. `backend/app/api/endpoints/assets.py:1293` POST `/test-with-auth`
  4. `backend/app/api/endpoints/assets.py:1335` POST `/test-extractor`
  5. `backend/app/api/endpoints/assets.py:1910` POST `/ai/test`
  6. `backend/app/api/endpoints/assets.py:2623` POST `/debug-excel-extract`
  7. `backend/app/api/endpoints/auth.py:86` POST `/test-token`
  8. `backend/app/api/endpoints/upload_multiple.py:50` GET `/test`
- **能改什么**：仅这 8 个端点的依赖项；`from app.core.deps import` 增加新依赖
- **不能改什么**：
  - 不动其他"非测试"端点（即便命名相似）
  - 不删除这些端点（仅门禁）
  - 不修改端点的业务逻辑
- **怎么验**：
  1. 重启后端
  2. 默认配置（`ENABLE_TEST_ENDPOINTS=False`）：
     - 上述 8 个端点 POST/GET → 期望 404
  3. 设置 `ENABLE_TEST_ENDPOINTS=true` 重启：
     - 同样的端点 → 期望进入业务逻辑（不一定成功，因为可能缺数据，但不再是 404）
- **通过标准**：生产默认安全；开发可显式启用
- **回退方案**：`git checkout HEAD -- backend/app/api/endpoints/`

---

## 阶段二·E：P1-6 资产接口契约（用户批准于 2026-09-11 11:29）

### 调研结论（精确清单）

**AssetView.vue 直接 fetch 调用**（7 处）：
| # | 前端路径 | 后端路径 | 状态 |
|---|---------|---------|------|
| 1 | `GET /system-config/network-locations` | 同 | ✅ |
| 2 | `PUT /system-config/network-locations` | 同 | ✅ |
| 3 | `POST /assets/file-extract` | 同 | ✅ |
| 4 | `POST /assets/file-extract/confirm` | `/assets/file-extract/single-confirm` | ❌ 路径错 |
| 5 | `POST /assets/file-extract/single-confirm` | 同 | ✅ |
| 6 | `POST /assets/batch/delete` | 同 | ✅ |
| 7 | `POST /assets/export` | 同 | ✅ |

**assetService.ts 中的方法**（实际使用情况）：
| 方法 | 路径 | 调用方 | 状态 |
|------|------|--------|------|
| `searchAssets` | `GET /assets/?params` | AssetView ✅ | ✅ |
| `getStatistics` | `GET /assets/statistics` | AssetView ✅ | ✅ |
| `getAsset` | `GET /assets/{id}` | AssetView ✅ | ✅ |
| `createAsset` | `POST /assets` | AssetView ✅ | ✅ |
| `updateAsset` | `PUT /assets/{id}` | AssetView ✅ | ✅ |
| `deleteAsset` | `DELETE /assets/{id}` | AssetView ✅ | ✅ |
| `extractAssetsFromDocument` | `POST /assets/extract` | **无调用方** | ❌ 死代码 |
| `getAssetsByDocument` | `GET /assets/document/{id}` | **无调用方** | ❌ 死代码 |
| `bulkCreateAssets` | `POST /assets/bulk-create` | **无调用方** | ❌ 死代码 |
| `mergeAssets` | `POST /assets/merge` | **无调用方** | ❌ 死代码 |

### 步骤 E.1 — 修正 AssetView.vue 的 `/file-extract/confirm` 错路径
- **做什么**：`frontend/src/views/AssetView.vue:2011` `/file-extract/confirm` → `/file-extract/single-confirm`
- **能改什么**：仅该文件 1 处 URL 字符串
- **不能改什么**：
  - 不动其他 6 处 fetch 调用（均正确）
  - 不重构 fetch 调用为 apiService（避免改动面扩大）
- **怎么验**：
  1. Vite HMR 自动加载
  2. 浏览器 AssetView 触发"确认提取"操作 → DevTools Network 显示请求 `/api/v1/assets/file-extract/single-confirm` 返回 200/业务码
- **通过标准**：错路径调用全部消失
- **回退方案**：`git checkout HEAD -- frontend/src/views/AssetView.vue`

### 步骤 E.2 — 删除 assetService.ts 中 4 个死代码方法
- **做什么**：删除 `extractAssetsFromDocument` / `getAssetsByDocument` / `bulkCreateAssets` / `mergeAssets` 4 个方法（含对应类型 import 如 `AssetExtractRequest` / `AssetExtractResult` 若不再使用）
- **能改什么**：仅 `frontend/src/services/asset.ts`
- **不能改什么**：
  - 不动 assetService 中其他方法
  - 不动 AssetView（已确认不使用这 4 个）
  - 不删除 `frontend/src/types/asset.ts` 中对应类型定义（可能被其他地方引用，宁可保留）
- **怎么验**：
  1. `grep -rn "extractAssetsFromDocument\|getAssetsByDocument\|bulkCreateAssets\|mergeAssets" frontend/src/` 应无匹配
  2. Vite HMR 加载后 `assetService.searchAssets` 等正常方法仍可用
  3. `npx vue-tsc --noEmit` 不报错（类型检查通过）
- **通过标准**：奥卡姆剃刀；前端 bundle 略小；无新调用方报错
- **回退方案**：`git checkout HEAD -- frontend/src/services/asset.ts`

---

## 阶段二·F：剩余 P1-7b / 新发现-10 / P2-9（用户批准于 2026-09-11 11:35）

### 步骤 F.1 — P1-7b 修复 documents.py 2 处鉴权绕过
- **做什么**：`backend/app/api/endpoints/documents.py` 两处 `Depends(get_optional_user)` → `Depends(get_current_active_user)`
  - line 125：`read_document(document_id)` GET 文档详情
  - line 482：`download_document(document_id)` GET 下载文档
- **能改什么**：仅这两个端点的依赖
- **不能改什么**：
  - 不动该文件中其他用 `get_optional_user` 的端点（如有）
  - 不动 endpoint 业务逻辑
- **怎么验**：
  1. 重启后端
  2. 无 token 访问 `GET /api/v1/documents/1` → 期望 401
  3. 无 token 访问 `GET /api/v1/documents/1/download` → 期望 401
  4. 带 admin token → 期望 200
- **通过标准**：与其他需鉴权的端点行为一致
- **回退方案**：`git checkout HEAD -- backend/app/api/endpoints/documents.py`

### 步骤 F.2 — 新发现-10 lifespan 修复 admin is_active 自动恢复
- **做什么**：`backend/app/main.py:79-86` 在现有 `is_superuser` 检查旁边加 `is_active` 检查与恢复
- **能改什么**：仅 `init_default_users` 函数
- **不能改什么**：
  - 不创建其他用户（仅 admin）
  - 不改密码
- **怎么验**：
  1. 启动后端
  2. 手动把 admin `is_active` 设为 0：`python -c "..."` SQL 更新
  3. 重启后端 → 启动日志应打印"修复"信息
  4. DB 检查 `is_active=1` 恢复
- **通过标准**：再次重启能自动恢复被禁用的 admin
- **回退方案**：`git checkout HEAD -- backend/app/main.py`

### 步骤 F.3 — P2-9 迁移 `fitz` → `pymupdf`
- **做什么**：`backend/app/services/ocr_extractor.py`：
  - `import fitz` → `import pymupdf`
  - `fitz = None` fallback → `pymupdf = None` fallback
  - `fitz.open(...)` → `pymupdf.open(...)`
  - `fitz.Matrix(...)` → `pymupdf.Matrix(...)`
- **能改什么**：仅 `ocr_extractor.py`
- **不能改什么**：
  - 不动其他文件（fitz 仅在此处使用）
  - 不动 OCR 业务逻辑
- **怎么验**：
  1. 重启后端
  2. 启动日志无 `fitz is deprecated` 警告
  3. `grep -rn "import fitz\|fitz\\.\\|fitz =" backend/` 应无匹配（除注释）
- **通过标准**：迁移后无废弃告警；功能等价
- **回退方案**：`git checkout HEAD -- backend/app/services/ocr_extractor.py`

---

## 阶段二·G：去掉上传接口不支持的图片格式（用户批准于 2026-09-11 12:00）

### 测试发现
| 格式 | 上传结果 | 原因 |
|------|---------|------|
| .md / .txt / .csv | ✅ 通过 | 普通文本走 `_validate_text_file` |
| .pdf | ✅ 通过 | `%PDF` 魔术字节 |
| .png / .jpg | ✅ 通过 | 已纳入 MAGIC_SIGNATURES |
| .docx / .xlsx | ✅ 通过 | `PK\x03\x04` 魔术字节 |
| .doc / .xls | ✅ 通过 | OLE `\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1` |
| **.bmp / .gif / .tiff / .webp** | ❌ 400 | ALLOWED_EXTENSIONS 允许但 MAGIC_SIGNATURES 未收录，validate_file_content 返回 False |

### 决策
移除 4 个图片格式（bmp / gif / tiff / webp）的服务端与前端支持。
保留 .png / .jpg / .jpeg 作为唯一图片格式。

### 步骤 G.1 — 后端从 ALLOWED_EXTENSIONS 移除 4 个格式
- **做什么**：`backend/app/core/config.py:37` `ALLOWED_EXTENSIONS` 字符串中移除 `,bmp,tiff,gif,webp`
- **能改什么**：仅该配置字符串
- **不能改什么**：不动 MAGIC_SIGNATURES（这 4 个本来就没收录）
- **怎么验**：
  1. 重启后端
  2. 上传 `.bmp` / `.gif` / `.tiff` / `.webp` → 期望 400 "不支持的文件类型"
  3. 上传 `.png` / `.jpg` → 期望 200（确认未误删）
- **通过标准**：4 个坏格式被 allowed_file() 在第一关拦截，不再到魔术字节检查
- **回退方案**：`git checkout HEAD -- backend/app/core/config.py`

### 步骤 G.2 — 前端 accept 属性同步
- **做什么**：`frontend/src/views/DocumentView.vue:164` `accept="..."` 中移除 `.bmp,.tiff,.gif,.webp`
- **能改什么**：仅该行 HTML 属性
- **不能改什么**：
  - 不动 `imageExtensions` 数组（line 1688）—— 仅用作预览判断，已上传文件类型不影响
  - 不动其他 accept 属性（如有）
- **怎么验**：
  1. Vite HMR 自动加载
  2. 浏览器 DevTools 检查 DocumentView 上传按钮 `accept` 不再含被删格式
- **通过标准**：UI 文件选择器不再显示被删格式
- **回退方案**：`git checkout HEAD -- frontend/src/views/DocumentView.vue`

---

## 阶段二·H：修复文本文件验证误判（用户报告于 2026-09-11 12:43）

### 根因分析

实测 `C:\Users\cccly\Desktop\ollama配置.md`（普通 UTF-8 中文 Markdown）失败：

```
读取前 512 字节后依次尝试解码：
  utf-8 : FAILED — 但错误是 "unexpected end of data at position 510-511"
          （末尾正好是中文 3 字节字符被截断，不是真"非 UTF-8"）
  ascii : FAILED — 中文不在 ASCII 范围
  gbk   : FAILED — 字节模式冲突
  utf-16: "成功" 解码出 256 字符，但 printable ratio = 79.69% < 80%
  → 最终被 _is_safe_binary_content 再次判失败 → 整文件被拒
```

受影响文件（验证后中文 .md 普遍触发）：
- `ollama配置.md` → 79.69% 失败
- `VIBE_CODING_GUIDE.md` → 75.39% 失败（**我们自己的指南都会失败**）
- `FRONTEND_AI_INTEGRATION.md` → 75.00% 失败

### 根因 3 处（`upload.py:89-167`）

1. **`_validate_text_file`** 的 4 种编码按顺序尝试。utf-8 失败是因为末尾截断（不是真非 utf-8），但代码把它当成"不是 utf-8"。
2. **utf-16 fallback 误匹配**：UTF-16 LE 实际是按 2 字节一组解读随机二进制，偶然"成功"且能算出 printable ratio；但解码出的内容毫无意义，会污染验证结果。
3. **80% printable 阈值**对中文 Markdown 太严格（含 `> `、`[]()` 等 markdown 标记 + 中英文混合 + 表格符号等）。

### 步骤 H.1 — 修复 `_validate_text_file` 与 `_is_safe_binary_content`
- **做什么**：`backend/app/api/endpoints/upload.py` `_validate_text_file` 重写：
  1. **UTF-8 优先**：用 `errors='replace'` 解码（即使末尾有坏字节也能得到内容）
  2. **GBK fallback**：UTF-8 失败时试 GBK（中文 Windows 系统常见）
  3. **移除 utf-16 误匹配**：utf-16 需要有 BOM 才尝试（避免随机字节被解读成 utf-16）
  4. **降低阈值**：把 80% 改为 **70%**（足够排除明显二进制，但接受含表格/标记的中文 Markdown）
  5. `_is_safe_binary_content` 移除（不再需要，因为文本判断已稳健）
- **能改什么**：仅 `_validate_text_file` 函数与 `_is_safe_binary_content` 调用
- **不能改什么**：
  - 不动 `validate_file_content` 函数整体签名
  - 不动 `MAGIC_SIGNATURES`（已正确）
  - 不动 `allowed_file`（已正确）
- **怎么验**：
  1. 重启后端
  2. 上传 `ollama配置.md` → 期望 200
  3. 上传 `VIBE_CODING_GUIDE.md` → 期望 200
  4. 上传测试用空文件 → 期望 400（保持）
  5. 上传纯控制字符文件 → 期望 400（保持）
  6. 上传 .md 含 `<script>` 字样的纯文本 → 期望 200（避免误杀合法文本）
  7. 上传真正的危险文件（如 `<?php` 头）→ 期望 400（保持安全）
- **通过标准**：中文为主的 .md / .txt 能上传；明确危险的二进制被拒
- **回退方案**：`git checkout HEAD -- backend/app/api/endpoints/upload.py`

---

## 阶段三：内容提取器重大升级（用户批准于 2026-09-11 13:50）

### 决策
- **架构**：完整三阶段（基础重构 + AI 视觉 + AI Wiki）
- **部署**：新代码全面替换旧代码（旧路径保留为 fallback）
- **AI provider**：现有5 个 provider API key 都为空 → 需要配置才能用阶段 2/3

### 阶段 3A — 基础重构（零 AI 成本，立刻可做）

#### 步骤 3A.1 — 新建 extraction 模块骨架
- **做什么**：在 `backend/app/services/extraction/` 创建新模块：
  - `__init__.py` — package 导出
  - `base.py` — `BaseExtractor` 抽象类，定义接口 `extract(file_path) -> ExtractionResult`
  - `models.py` — `ExtractionResult` dataclass（markdown: str, json_data: dict, warnings: list, fallback_used: bool）
  - `router.py` — `ExtractionRouter` 按扩展名分发
- **能改什么**：仅新建 `services/extraction/` 目录
- **不能改什么**：
  - 不动现有 `content_extractor.py` / `search_service.py`
  - 不动 `ai/` 子系统
  - 不动任何 API 端点
- **怎么验**：`python -c "from app.services.extraction import ExtractionRouter; print(ExtractionRouter())"` 不报错
- **回退方案**：`rm -rf backend/app/services/extraction/`

#### 步骤 3A.2 — 实现 XLSX/XLS extractor（核心：修错位）
- **做什么**：`backend/app/services/extraction/xlsx_extractor.py`
  - 用 `openpyxl` 直接读工作簿（不经过 LibreOffice）
  - 每个工作表 → 重建合并单元格 → 输出 Markdown GFM 表格
  - 合并单元格 fallback 到 HTML `<table>`（保持视觉结构）
  - 多工作表用 `## 工作表名` 分隔
- **能改什么**：仅新建该文件
- **不能改什么**：
  - 不动 LibreOffice 调用代码（PDF/PPT 仍需要）
  - 不改 schema
- **怎么验**：
  1. 上传一个真实有合并单元格、含中文表头的 .xlsx
  2. 检查数据库 `documents.content` 字段：是 Markdown 表格而非错位 TXT
  3. 前端预览：表格对齐、合并单元格显示正确
- **通过标准**：用户能直接看到表格对得齐；含合并单元格的表也能正常显示
- **回退方案**：`rm backend/app/services/extraction/xlsx_extractor.py`

#### 步骤 3A.3 — 实现 DOCX/DOC extractor
- **做什么**：`backend/app/services/extraction/docx_extractor.py`
  - 用 `python-docx` 直读 paragraphs、tables、headings
  - 标题层级（Heading 1/2/3）→ Markdown `#`/`##`/`###`
  - 表格 → Markdown GFM
  - 列表 → Markdown `-`/`1.`
- **验证**：上传 .docx 看结构化是否正确
- **回退**：`rm` 同上

#### 步骤 3A.4 — 实现 Text/PDF/Image extractor
- **做什么**：补齐其余格式
  - `text_extractor.py` — 文本类（.txt/.md/.csv/.json）直读 + UTF-8 清理 + Markdown 头识别
  - `pdf_extractor.py` — 复用 LibreOffice + 后处理（清理连续空行、合并截断段落）
  - `image_extractor.py` — 包装现有 OCRExtractor，返回 Markdown（图片说明）
- **回退**：`rm` 同上

#### 步骤 3A.5 — 路由器集成 + 替换主调用
- **做什么**：
  - `router.py` 集成所有 extractor
  - 修改 `content_extractor.py` 的 `extract_content` 让其调用新 router（保留向后兼容）
  - 修改 `search_service.extract_file_content` 让其也走新 router
- **能改什么**：`content_extractor.py` / `search_service.py`
- **不能改什么**：
  - 保留旧方法作为 fallback（router 失败时调用）
  - API 端点不变
- **怎么验**：
  1. 重启后端
  2. 上传各格式 → DB 中 content 字段是干净 Markdown
  3. 前端预览看到对齐的表格、结构化标题
- **通过标准**：用户最关心的 XLSX 错位问题彻底修复；其他格式预览质量也明显提升

### 阶段 3B — AI 视觉层（需配置 provider）

#### 步骤 3B.1 — 新增视觉模型配置支持
- **做什么**：`backend/app/core/config.py` 增加：
  - `AI_VISION_MODEL`（默认空，启用时设置如 `qwen-vl-plus` / `glm-4v-plus`）
  - `AI_VISION_PROVIDER`（如 `alibaba` / `zhipu`）
- **能改**：仅 config.py
- **不能改**：不动现有 provider 列表（避免破坏向后兼容）
- **验证**：`/api/v1/settings/ai-config` 显示新字段
- **回退**：`git checkout HEAD -- backend/app/core/config.py`

#### 步骤 3B.2 — PDF/图片走视觉 LLM（fallback 链）
- **做什么**：在 `router.py` 加重试链：
  1. 先试 LibreOffice/OCR 直读
  2. 提取失败或内容为空时，调视觉 LLM（截图或整页送入）
  3. LLM 输出 Markdown
- **能改**：router.py + 新增 `vision_extractor.py`
- **不能改**：LLM 调用必须用现有 `AIService`（不能新引入 SDK）
- **验证**：上传扫描 PDF → DB 存的是 LLM 生成的 Markdown
- **回退**：vision 部分 feature flag 控制，默认关闭

### 阶段 3C — AI Wiki 体验

#### 步骤 3C.1 — 文档入库自动摘要 + 标签
- **做什么**：上传后异步任务调 LLM 生成：
  - 摘要（≤200 字）
  - 标签（3-5 个关键词）
  - 文档类型分类（运维手册 / 配置 / 故障 / 设备档案）
- **存储**：`documents.summary` / `documents.tags` / `documents.doc_type` 新增字段
- **能改**：`models/document.py` 加字段；`tasks`/后台任务调 LLM
- **不能改**：不动 schema 既有字段；不删除任何已有列
- **验证**：上传后查看 summary/tags 字段自动填充
- **回退**：迁移不写，LLM 失败留空

#### 步骤 3C.2 — 搜索结果展示 AI 增强
- **做什么**：`/api/v1/search/` 返回结构新增：
  - `ai_summary`：命中片段的上下文摘要
  - `relevance_explanation`：为什么这条结果相关
- **能改**：`search_service.py` + search endpoint
- **不能改**：不影响现有 `items` / `total` 字段
- **验证**：搜索时返回带 ai_summary 的 JSON

#### 步骤 3C.3 — 文档 Q&A 端点（基础 RAG）
- **做什么**：新增 `POST /api/v1/documents/{id}/qa` 接受 `{"question": "..."}`
  - 检索文档全文 → 拼上下文 → 调 LLM 生成答案
  - 返回 `{"answer": "...", "sources": ["..."]}`
- **能改**：新建 endpoint + service
- **不能改**：不影响其他文档端点
- **验证**：调用新端点能根据文档内容回答问题

---

## 阶段 3D：修复 .xls 提取（用户报告于 2026-09-11 14:33）

### 根因
- `_extract_xls_legacy()` 依赖 `xlrd`，但 `xlrd >= 2.0` 已不再支持 `.xls`
- `import xlrd` 失败 → 返回错误 → router fallback 到旧管线（LibreOffice→TXT）
- 结果：`.xls` 文件预览是 LibreOffice 输出的 TXT（"=== 工作表: Sheet1 ==="），没有 Markdown 表格

### 步骤 3D.1 — .xls 转 .xlsx 走新管线
- **做什么**：`xlsx_extractor.py` 的 `_extract_xls_legacy()` 改为：
  1. 用 LibreOffice 把 `.xls` 转 `.xlsx`（临时目录）
  2. 用 openpyxl 处理转换后的 `.xlsx`
  3. 清理临时文件
- **能改**：仅 `xlsx_extractor.py` 的 `_extract_xls_legacy()` 方法
- **不能改**：
  - 不引入 xlrd 依赖
  - 不改 openpyxl 调用逻辑
- **怎么验**：
  1. 上传 `.xls` 文件
  2. DB 存的是 Markdown 表格（对齐），不再有 "=== 工作表: Sheet1 ===" 旧格式
  3. 后端日志应看到 LibreOffice 调用 + openpyxl 解析
- **通过标准**：`.xls` 提取输出与 `.xlsx` 一致质量
- **回退方案**：`git checkout HEAD -- backend/app/services/extraction/xlsx_extractor.py`

### 步骤 3D.2 — 修复 `_render_html_table` 跳过所有非合并格子的 bug（用户报告于 2026-09-11 15:07）
- **现象**：`交换机统计0723.xls` 提取后只有 4 个非空单元格（"镇江南收费站"等合并格子的主格值），其他所有非合并数据（B-F 列的设备名/IP/账号/密码等）完全丢失
- **根因**：
  ```python
  if merge_owner.get((r_idx, c_idx)) != (r_idx, c_idx):  # BUG
      continue
  ```
  对**未合并**的格子，`merge_owner.get(...)` 返回 `None`，`None != (r, c)` 是 True → continue 被触发 → 所有非合并格子被错误跳过
- **修复**：用 `merge_owner.get((r, c), (r, c)) != (r, c)` —— 默认值返回 (r, c) 自身，对未合并格子比较结果为 False（不跳过）
- **能改**：仅 `xlsx_extractor.py` 的 `_render_html_table` 静态方法
- **不能改**：
  - 不动 `_process_sheet` / `_extract_xls_legacy` 等
  - 不动 JSON 数据（rows 数组已经完整）
- **怎么验**：
  1. 重启后端
  2. 删除旧测试文档（或重新上传）
  3. 上传 `交换机统计0723.xls` → DB content 包含全部 25 行 × 6 列数据
  4. 用 grep `非空单元格` 验证数量 ≥ 30（原 4）
- **通过标准**：所有非合并数据完整保留
- **回退方案**：`git checkout HEAD -- backend/app/services/extraction/xlsx_extractor.py`

---

## 阶段 3E：前端 Markdown 渲染（用户批准于 2026-09-11 15:23）

### 背景
后端阶段 3A 已输出 Markdown 格式（`## 工作表：` + GFM 表格 + HTML 表格 fallback），
但前端 `DocumentView` 的预览只用 `sanitizeDocumentHtml` 当 HTML 处理 → Markdown 文本原样显示，不渲染。

### 决策
- **新依赖**：`markdown-it`（MIT 协议，社区最广泛，体积小）
- **不需要** Marked / Markdown-it-py / 其它（Vue 生态中 markdown-it 是事实标准）
- **保留** DOMPurify sanitize（先 render → 再 sanitize 防 XSS）

### 步骤 3E.1 — 安装 markdown-it
- **做什么**：`frontend/` 下 `npm install markdown-it @types/markdown-it`
- **能改**：仅 `frontend/package.json` + `package-lock.json`
- **不能改**：不动 `@tech-stack.md` "严禁引入"清单（markdown-it 不在那）
- **怎么验**：`./node_modules/markdown-it/package.json` 存在
- **通过标准**：`grep markdown-it frontend/package.json` 命中
- **回退方案**：`npm uninstall markdown-it @types/markdown-it`

### 步骤 3E.2 — 创建 Markdown 渲染 composable
- **做什么**：新建 `frontend/src/utils/markdown-renderer.ts`
  - 单例 MarkdownIt 实例（启用 GFM `linkify: true`）
  - `renderMarkdown(md: string): string` 方法
  - `renderDocumentMarkdown(md: string): string` 方法（先 render 再 DOMPurify sanitize）
- **能改**：仅新建文件
- **不能改**：
  - 不修改 `xss-protection.ts`（sanitize 函数保留独立）
  - 不引入除 markdown-it 和已有 dompurify 外的新依赖
- **怎么验**：
  1. `node -e "import('./src/utils/markdown-renderer.ts').then(m => console.log(m.renderDocumentMarkdown('# hi')))"` 输出 `<h1>hi</h1>`
  2. `console.log(renderDocumentMarkdown('| a | b |\n| - | - |\n| 1 | 2 |'))` 输出 `<table>...`
- **通过标准**：表格、标题、列表、代码块全部正确渲染
- **回退方案**：`rm src/utils/markdown-renderer.ts`

### 步骤 3E.3 — DocumentView 预览切换到 Markdown 渲染
- **做什么**：`frontend/src/views/DocumentView.vue:225-231` 预览容器：
  - 替换 `<pre v-html="sanitizeDocumentHtml(previewContent)">` → `<div v-html="renderDocumentMarkdown(previewContent)">`
  - 替换 CSS class `preview-content-table` → 新 class `markdown-content`
- **能改**：仅 DocumentView.vue 的预览部分
- **不能改**：
  - 不动其他文档视图（EnhancedSearchView 等）
  - 不动 `previewContent` 的数据流（仍用同一变量）
  - 不动高亮逻辑（高亮在 sanitize 之前注入到 `<mark>`）
- **怎么验**：
  1. Vite HMR 自动加载
  2. 浏览器预览 `交换机统计0723.xls`：表格对齐渲染（不再显示 `| ... |` 字面文本）
  3. 预览 `润扬大桥设备资产清单.xlsx`：HTML 表格（含 rowspan/colspan）正确渲染
  4. 预览 `.md` 文件：标题、列表、代码块、表格全部渲染
- **通过标准**：用户能看到真正的表格（不是字面 Markdown 文本）
- **回退方案**：`git checkout HEAD -- frontend/src/views/DocumentView.vue`

---

## 阶段四：删除旧管线 + 接入 MinerU/PaddleOCR（用户批准于 2026-09-11 15:58）

### 决策
- **PDF/图片路径**：MinerU 3.4（中文 SOTA，Apache-2.0 + 商业附加条款）+ PaddleOCR-VL-1.6 备用
- **旧管线**：一键删除（不再保留 fallback）
- **本次不实现 AI 调用本身**（需 GPU + MinerU 安装），但完成：
  1. 删除旧代码
  2. 集成接口骨架（environment-driven开关 + 文档）
  3. PdfExtractor/ImageExtractor 升级章节识别/页眉页脚去除
  4. 端到端验证（用现有依赖如 pymupdf 的强化版 + pytesseract 升级到 PP-OCR 路径）

### 步骤 4.1 — 删除旧管线代码（fallback 路径）
- **做什么**：
  - `backend/app/services/content_extractor.py`：删除 `_fallback` 逻辑（新路由器失败时直接返回错误，不再走旧管线）
  - `backend/app/services/extraction/router.py`：删除 `_fallback` 方法
  - `backend/app/services/search_service.py`：**保留**搜索逻辑，但删除 `extract_file_content` 这个 LibreOffice 转 TXT的方法（删除 ~150 行 + helper methods）
  - 前端：`DocumentView.vue` 中的 fallback 提示代码（"旧管线"提示）
- **能改**：上述 3 个文件
- **不能改**：
  - 不动 `search_service.py` 的搜索逻辑（只删提取部分）
  - 不动 XlsxExtractor/DocxExtractor/TextExtractor（新管线工作良好）
- **怎么验**：
  1. 后端启动无 ImportError
  2. 上传 xlsx/docx/md 仍走新路由器
  3. 故意上传损坏文件 → 报明确错误（不再 fallback 到残缺内容）
- **通过标准**：旧代码完全清除；新代码独立运行
- **回退方案**：`git checkout HEAD -- backend/app/services/content_extractor.py backend/app/services/extraction/router.py backend/app/services/search_service.py`

### 步骤 4.2 — PdfExtractor 增强（章节识别 + 页眉页脚去除）
- **做什么**：`backend/app/services/extraction/pdf_extractor.py`：
  - 用 pymupdf 提取每页文本时，检测**章节标题模式**：
    - `第X章`、`第X节`、`\d+\.\d+`、大写单词行等
  - 用正则**识别并去除页眉/页脚**：
    - 页码模式：`\d+ / \d+`、`第 \d+ 页`
    - 重复行（顶部/底部连续出现2+次）
  - 输出更结构化的 Markdown：`# 第一章 ...` `## 1.1 ...`
  - 提取文档元数据（标题、作者、创建日期）作为 JSON
- **能改**：仅 `pdf_extractor.py`
- **不能改**：
  - 不动 `_check_file`/异常处理
  - 不动 router.py
- **怎么验**：
  1. 上传一个中文 PDF（项目里没找到 → 让用户上传一个测试）
  2. 输出含 `# 第X章` 标题，页眉页脚被去除
  3. 章节 JSON 包含页码范围
- **通过标准**：章节识别 ≥ 70%（人工抽查 5 个标题，3+ 正确）
- **回退方案**：`git checkout HEAD -- backend/app/services/extraction/pdf_extractor.py`

### 步骤 4.3 — PdfExtractor 接入 PaddleOCR（CPU 友好备用）
- **做什么**：
  - 新增 `_extract_with_paddleocr()` 方法（在 pymupdf 提取文字为空时fallback，常见于扫描件PDF）
  - 需要 `paddleocr` 包 → `requirements-windows.txt` 新增 `paddleocr>=2.7` + `paddlepaddle>=2.5`
  - 如果未安装 paddleocr → `_extract_with_paddleocr` 返回None，记录 warning
- **能改**：
  - `backend/app/services/extraction/pdf_extractor.py`
  - `backend/requirements-windows.txt`
- **不能改**：
  - 不替换 PaddleOCR 为 MinerU（两者并存，PaddleOCR 是 CPU 备用；MinerU 是 GPU 主路径但本次不实现调用）
  - 不动 router
- **怎么验**：
  1. 重启后端
  2. 上传扫描件 PDF → pymupdf 提取为空 → 自动调用 PaddleOCR
  3. 提取出中文文字
- **通过标准**：扫描件 PDF 不再报"无可提取文本"
- **回退方案**：`git checkout HEAD -- backend/app/services/extraction/pdf_extractor.py backend/requirements-windows.txt`

### 步骤 4.4 — ImageExtractor 接入 PaddleOCR（中文 OCR 增强）
- **做什么**：
  - `backend/app/services/extraction/image_extractor.py` 的 `_extract_image` 改为优先 PaddleOCR（中文识别率更高），pytesseract 兜底
  - 添加"中文识别率提升"模式：PaddleOCR `lang='ch'`
- **能改**：仅 `image_extractor.py`
- **不能改**：不动接口签名（`SUPPORTED_EXTENSIONS` 保持）
- **怎么验**：
  1. 上传中文图片（项目里有 `收费网拓扑1.png`）
  2. OCR 提取中文文本
- **通过标准**：OCR 输出的中文正确率明显优于 pytesseract（人工抽查）
- **回退方案**：`git checkout HEAD -- backend/app/services/extraction/image_extractor.py`

### 步骤 4.5 — 环境变量配置 MinerU/PaddleOCR 开关
- **做什么**：`backend/app/core/config.py` 增加：
  - `PDF_ENGINE`: str = "pymupdf"  # 可选 "pymupdf" / "mineru"
  - `OCR_ENGINE`: str = "tesseract"  # 可选 "tesseract" / "paddleocr"
  - `MINERU_DEVICE`: str = "cuda"  # GPU/CPU
  - `MINERU_ENABLED`: bool = False  # 默认关闭，等用户装好 MinerU 再开
- **能改**：仅 `config.py`
- **不能改**：不动其他 settings
- **怎么验**：
  1. 后端启动日志输出当前引擎选择
  2. 通过 env 变量切换：`PDF_ENGINE=mineru uvicorn ...`
  3. 切换失败时不影响默认 pymupdf 路径
- **通过标准**：env 切换不报错
- **回退方案**：`git checkout HEAD -- backend/app/core/config.py`

### 步骤 4.6 — 端到端验证 + 文档更新
- **做什么**：
  - 重启后端
  - 上传测试用例：xlsx + 中文图片（已有）+ PDF（找用户一个）
  - 在 `@tech-stack.md` 中增加：
    - "PDF 提取支持 pymupdf / mineru 切换"
    - "OCR 支持 tesseract / paddleocr 切换"
- **能改**：
  - `backend/app/services/extraction/pdf_extractor.py`（验证）
  - `memory-bank/@tech-stack.md`（文档）
- **不能改**：不动其他模块
- **怎么验**：
  1. 4 个核心场景都通过
  2. memory-bank 更新
- **通过标准**：所有场景 E2E 通过
- **回退方案**：N/A（验证步骤）

---

## 阶段五：AI 引擎解耦为远程服务（用户批准于 2026-09-11 16:40）

### 架构（用户确认）

```
┌─────────────────────┐
│  本应用服务器         │
│  (FastAPI 后端)      │
│                     │
│  PdfExtractor        │──HTTP──▶  ┌──────────────────────────┐
│  ImageExtractor      │          │  AI 服务服务器（GPU）        │
│  DocxExtractor       │          │                          │
│  XlsxExtractor       │          │  ├─ PaddleOCR-Server :8001 │
│  TextExtractor       │          │  ├─ MinerU-Server    :8002 │
│                     │          │  └─ vLLM (Qwen2.5-VL) :8000 │
└─────────────────────┘          └──────────────────────────┘
   (本机 CPU)                        (远端 GPU)
```

**优势**：
- 本应用无需 GPU（CPU 即可）
- AI 引擎独立升级不影响主应用
- 多个应用可共用一套 AI 服务
- 失败 fallback 友好（AI 挂了降级到本地 tesseract/pymupdf）

### 步骤 5.1 — 后端配置加 AI 服务 URL（环境变量）
- **做什么**：`backend/app/core/config.py` 新增：
  - `AI_OCR_SERVICE_URL: str = "http://localhost:8001"`（PaddleOCR 服务地址）
  - `AI_OCR_ENABLED: bool = False`
  - `AI_PDF_SERVICE_URL: str = "http://localhost:8002"`（MinerU 服务地址）
  - `AI_PDF_ENABLED: bool = False`
  - `AI_VLM_SERVICE_URL: str = "http://localhost:8000/v1"`（vLLM OpenAI 兼容）
  - `AI_VLM_ENABLED: bool = False`
  - `AI_SERVICE_TIMEOUT: int = 120`（秒，AI 调用超时）
- **能改**：仅 config.py
- **不能改**：不动其他 settings
- **验证**：`python -c "from app.core.config import settings; print(settings.AI_OCR_SERVICE_URL)"`
- **通过标准**：新字段可读
- **回退**：`git checkout HEAD -- backend/app/core/config.py`

### 步骤 5.2 — 写 AI 服务客户端封装
- **做什么**：新建 `backend/app/services/extraction/ai_client.py`：
  - `class PaddleOCRClient`：通过 HTTP 调用远端 PaddleOCR-Server；返回 (text, error)
  - `class MinerUClient`：通过 HTTP 调用远端 MinerU-Server；返回 (markdown, error)
  - `class VLMClient`：通过 OpenAI 兼容协议调用 vLLM（用于图片理解 / 复杂 PDF 兜底）
  - 通用 `requests.post` + 超时 + 重试 + 健康检查
- **能改**：仅新建文件
- **不能改**：
  - 不依赖 paddleocr / mineru / vllm Python 包（仅 HTTP）
  - 不修改既有 extractor（下一步才接入）
- **验证**：单元测试 `python -c "from app.services.extraction.ai_client import PaddleOCRClient; print(PaddleOCRClient().url)"`
- **通过标准**：客户端实例化不报错
- **回退**：`rm backend/app/services/extraction/ai_client.py`

### 步骤 5.3 — PdfExtractor 接入 AI 服务
- **做什么**：`backend/app/services/extraction/pdf_extractor.py` 调整：
  - pymupdf 提取为空时，**优先**调用远端 PaddleOCR-Server（HTTP），本地 PaddleOCR 兜底
  - 如果 `AI_PDF_ENABLED=true`，调用远端 MinerU-Server
  - 增加 `AI_SERVICE_TIMEOUT` 超时控制
- **能改**：仅 `pdf_extractor.py`
- **不能改**：不动接口签名（保持向后兼容）
- **验证**：
  1. AI_OCR_ENABLED=False（默认）→ 走本地 PaddleOCR / pymupdf（与之前一致）
  2. AI_OCR_ENABLED=True + AI_OCR_SERVICE_URL=http://... → 调用远端
  3. 远端不可达 → 优雅降级到本地，不报错
- **通过标准**：本地/远端切换不报错
- **回退**：`git checkout HEAD -- backend/app/services/extraction/pdf_extractor.py`

### 步骤 5.4 — ImageExtractor 接入 AI 服务
- **做什么**：同 5.3，但作用于 `image_extractor.py`
- **验证**：同上
- **回退**：`git checkout HEAD -- backend/app/services/extraction/image_extractor.py`

### 步骤 5.5 — 文档与启动脚本
- **做什么**：
  - `memory-bank/@tech-stack.md` 新增"AI 引擎服务化"章节（含架构图）
  - 新建 `scripts/start_ai_services.sh`（启动 PaddleOCR/MinerU/vLLM 容器）
  - 新建 `docs/AI服务部署.md`（用户部署 AI 服务的操作指南）
- **能改**：上述 3 个文件
- **验证**：脚本 dry-run 验证语法
- **回退**：删除新建文件

### 步骤 5.6 — 端到端验证（本地 mock）
- **做什么**：启动后端，验证：
  - 默认（AI_*_ENABLED=False）行为不变
  - 切换 AI_*_ENABLED=True 且 URL 不可达时降级到本地
  - 网络可达时调用 AI 服务（可选：起个 mock HTTP 服务测）
- **验证**：所有场景不报错
- **回退**：N/A（验证步骤）

---

## 阶段六：AI 服务配置加入前端系统设置（用户批准于 2026-09-11 16:52）

### 决策
- **新增 AI 服务设置页**（与现有 AI 通用配置并存）
- 范围：**远程 AI 引擎配置**（PaddleOCR/MinerU/vLLM）—— 阶段五新增的 8 个 settings
- 现有 AI 通用配置不动（OpenAI/Anthropic/通义等 LLM 提供商）

### 步骤 6.1 — 后端新增配置读写 API
- **做什么**：
  - `backend/app/api/endpoints/system_config.py`（新建）或扩展现有 `settings.py` 端点：
    - `GET /api/v1/settings/extraction-config`：返回当前 AI 引擎配置（含敏感 URL，但不包含 key/secret）
    - `PUT /api/v1/settings/extraction-config`：更新配置
  - 配置存 DB（新增表 `system_extraction_config`）或返回当前 Settings 默认值
  - **写操作时重启提示**：配置只保存到 .env 提示，不重启服务（避免影响正在运行的上传）
- **能改**：
  - 新建 `backend/app/api/endpoints/extraction_config.py`
  - `backend/app/api/api_v1.py` 注册
- **不能改**：
  - 不动 `backend/app/core/config.py` 的 settings 类（用现有 settings）
  - 不动现有 LLM AI 配置端点
- **怎么验**：
  1. `curl GET /api/v1/settings/extraction-config` → 返回当前 AI_* 配置（read-only）
  2. `curl PUT /api/v1/settings/extraction-config -d {json}` → 返回 200 + 提示需重启
- **通过标准**：API 读写正常；前端可调用
- **回退**：`rm backend/app/api/endpoints/extraction_config.py`

### 步骤 6.2 — 前端 settings.ts 服务新增
- **做什么**：`frontend/src/services/extraction-config.ts`（新建）：
  - `getExtractionConfig()` → Promise<ExtractionConfig>
  - `updateExtractionConfig(cfg)` → Promise<{restart_required: boolean}>
  - 类型定义（与后端 settings 字段一致）
- **能改**：仅新建文件
- **不能改**：不动其他 services
- **验证**：`vue-tsc --noEmit` 0 error
- **回退**：`rm frontend/src/services/extraction-config.ts`

### 步骤 6.3 — SettingsView.vue 新增"AI 引擎服务"卡片
- **做什么**：在 `frontend/src/views/SettingsView.vue` 现有"AI 服务配置"卡片**下方**新增一张卡片：
  - 标题："AI 引擎服务（远程提取）"
  - 字段：
    - OCR 服务开关 + URL（占位）
    - PDF 服务开关 + URL（占位）
    - VLM 服务开关 + URL + 模型名
    - 调用超时（秒，默认 120）
    - 失败回退本地开关
    - "测试连接" 按钮（命中三个 URL 的 /health 端点）
  - 副标题/反馈：提示重启应用生效
- **能改**：仅 SettingsView.vue（新增一块，不动现有 LLM 配置卡片）
- **不能改**：
  - 不动现有"AI 服务配置"卡片（OpenAI/Claude 等）
  - 不动其他视图
- **验证**：
  1. Vite HMR 自动加载
  2. 浏览器硬刷新 SettingsView → 看到新卡片
  3. 输入 AI 服务 URL → 点击"测试连接" → 显示"成功/失败"
- **通过标准**：UI 显示 + 写 API 调用成功
- **回退**：`git checkout HEAD -- frontend/src/views/SettingsView.vue`

### 步骤 6.4 — 端到端验证
- **做什么**：
  1. 后端启动
  2. 前端 GET 拉取当前 config
  3. 前端 PUT 修改 AI_OCR_SERVICE_URL → 验证响应
  4. curl 测试同样的接口
- **验证**：前后端联通
- **回退**：N/A

---

## 阶段七：合并为统一多模态模型（用户批准于 2026-09-11 17:04）

### 决策（用户隐含批准）
- **路线**：**Qwen3-VL 本地化**（**llama.cpp OpenAI 兼容 server**）
- 用户本地模型用 **llama.cpp 部署**（已有 `ollama配置.md` 但实际用 llama.cpp）
- llama.cpp 自带 `llama-server` 提供 OpenAI 兼容 `/v1/chat/completions` 端点（自动启用 `--oai-like` 或 `--chat-template`）
- 一个多模态模型替代 PaddleOCR + MinerU + vLLM

### 架构（简化后）

```
┌─────────────────────┐
│  主应用服务器         │
│  (FastAPI + Vue)     │
│                     │
│  PdfExtractor        │──HTTP──▶  ┌──────────────────────────┐
│  ImageExtractor      │          │  Ollama (本地)            │
│  (新：统一接口)       │          │                          │
└─────────────────────┘          │  qwen3-vl:latest           │
   (本机 CPU)                   │  POST /api/chat           │
                                │  (OpenAI 兼容)            │
                                └──────────────────────────┘
```

**可选**：PaddleOCR-Server 作为高速页面的兜底（CPU 便宜，省 Qwen3-VL token）。

### 步骤 7.1 — VLMClient 支持 Ollama 兼容 API
- **做什么**：`backend/app/services/extraction/ai_client.py` 的 `VLMClient`：
  - 增加 `provider` 字段：`ollama`（默认）/ `openai`
  - Ollama 模式：`POST {url}/api/chat`（不是 OpenAI 兼容）
  - 提示词固定为"文档解析"专用 prompt（输出 Markdown）
  - 多模态：image（base64 或 URL）
- **能改**：仅 `ai_client.py`
- **不能改**：
  - 不动 PaddleOCRClient / MinerUClient
  - 不破坏 VLMClient 现有接口
- **验证**：
  - 调用 ollama 服务（如果跑着）→ 返回 markdown
  - 失败 → 降级
- **通过标准**：代码 import 不报错；provider=ollama/openai 都可切换
- **回退**：`git checkout HEAD -- backend/app/services/extraction/ai_client.py`

### 步骤 7.2 — PdfExtractor 接入统一多模态 VLM
- **做什么**：`backend/app/services/extraction/pdf_extractor.py`：
  - 新增 `_extract_with_vlm(file_path)`：用 pymupdf 把每页转图片，逐页/分块调 VLM
  - VLM 优先 → pymupdf 文本提取 → PaddleOCR（可选）
  - 文档分块（每 5 页一组避免上下文爆炸）
- **能改**：仅 `pdf_extractor.py`
- **验证**：扫描件 PDF → VLM 提取 → 干净 Markdown
- **回退**：保留原 pymupdf 路径

### 步骤 7.3 — ImageExtractor 用 VLM（OCR 升级）
- **做什么**：`backend/app/services/extraction/image_extractor.py`：
  - 默认走 VLM（图像理解更强）
  - 可选 PaddleOCR 作为快速路径
- **验证**：图片 OCR 准确率明显提升

### 步骤 7.4 — 简化 config.py + 前端设置
- **做什么**：
  - config.py 简化：移除 MinerU 相关配置（保留 PaddleOCR 作为可选）
  - 前端 SettingsView：把"AI 引擎服务"卡片改名"多模态 AI 服务"，只显示 1 个 Ollama URL + 开关
- **验证**：UI 更简洁

### 步骤 7.5 — 文档更新
- **做什么**：
  - `docs/AI服务部署.md` 改写：推荐 Ollama + Qwen3-VL 部署
  - `scripts/start_ai_services.sh` 简化：只启动 Ollama 即可
- **验证**：文档一致性

---

---

## 阶段四：交付前自检

- [ ] 所有改动步骤已在 `progress.md` 标记完成
- [ ] `@architecture.md` 已同步（如新增/删除文件）
- [ ] `@tech-stack.md` 已同步（如新增依赖）
- [ ] `@product-requirements-document.md` 已同步（如果需求变更）
- [ ] 跑通后端 + 前端 + 关键链路
- [ ] Commit 信息遵循 VIBE_CODING_GUIDE 提交规范
- [ ] 不携带临时文件/日志/数据库
- [ ] 提交说明含验证步骤与潜在风险

---

## 阶段五：何时切新会话

依据 `VIBE_CODING_GUIDE.md` 阶段"AI 会话管理"：
- 代码量 > 2000 行
- 上下文变混乱
- 进入新大功能模块
- AI 出现重复或遗忘

切前：先把当前进度写到 `progress.md`；新会话从 `@implementation-plan.md + progress.md` 恢复。

---

_生成时间：2026-09-11_
_本文件会被持续更新；每次新增任务前先把对应子步骤补到这里_
---

## 阶段八：移除旧 AI 服务配置（用户批准于 2026-09-11 17:44）

### 决策
- 阶段七已将 AI 引擎统一到 llama.cpp/Qwen3-VL 单接口
- 旧"AI 服务配置"卡片（OpenAI/Anthropic/通义等 5 个 LLM Provider）已无意义
- 旧"AI 使用统计"卡片的数据来源也是 5 个 Provider，与新架构不符
- **完全删除前端卡片** + **后端对应端点**（`/assets/ai/*`） + **前端 ai.ts service**

### 步骤 8.1 — 前端删除旧 AI 卡片
- **做什么**：`frontend/src/views/SettingsView.vue`：
  - 删除 `<n-card title="AI服务配置">` 整块（line 31-178）
  - 删除 `<n-card title="AI使用统计">` 整块（line 306-371）
- **验证**：vue-tsc 0 error；浏览器 SettingsView 无旧卡片

### 步骤 8.2 — 前端删除旧 AI state/imports/handlers
- **做什么**：SettingsView.vue 同步删除：
  - import：`getAIProviders` / `getAIStats` / `getAIConfigAPI` / `saveAIConfigAPI` / `testAIConnectionAPI` / `AIProvider` / `AIStats` / `AIConfig` / `AIProviderConfig`
  - state：`hardcodedProviders` / `aiProviders` / `aiConfig` / `aiStats` / `loadingAIStats` / `testingAI` / `savingAIConfig` / `showProviderConfig`
  - handlers：`loadAIProviders` / `loadAIConfig` / `saveAIConfig` / `testAIConnection` / `loadAIStats` / `handleProviderChange` / `getCurrentProviderConfig`
  - helpers：`providerDisplayNames` / `defaultUrls` / `defaultModels` / `providerOptions`
  - onMounted 中：`loadAIProviders()` / `loadAIConfig()` / `loadAIStats()` 调用

### 步骤 8.3 — 前端删除 services/ai.ts
- **做什么**：`rm frontend/src/services/ai.ts`（完全删除整个文件）

### 步骤 8.4 — 后端删除 /assets/ai/* 端点
- **做什么**：`backend/app/api/endpoints/assets.py`：
  - 删除 `@router.get("/ai/providers")` 整块（line 1727-1866）
  - 删除 `@router.get("/ai/stats")` 整块（line 1867-1910）
  - 删除 `@router.post("/ai/test")` 整块

### 步骤 8.5 — 后端检查其他 AI 引用
- **做什么**：grep `ai/\|/ai/test\|/ai/providers\|/ai/stats` 排除阶段七的 `/settings/extraction-config`

### 步骤 8.6 — 后端移除 AI 相关后端服务
- **做什么**：检查并清理 `backend/app/services/ai/` 目录
- **决定（用户隐含批准）**：
  - **删除**：`/api/v1/assets/ai/*`、`/api/v1/documents/ai/*`（前端不再调用）
  - **删除**：`frontend/src/services/ai.ts`（无引用）
  - **删除**：`frontend/src/views/AssetView.vue` 中的"AI提供商"下拉选
  - **保留**：`backend/app/services/ai/`（DocumentAnalyzer、AssetExtractor 是核心 AI 分析能力）
  - **保留**：`backend/AI_SERVICE_QUICKSTART.md`（说明文档）
  - **理由**：这些是 LLM 分析能力（摘要/抽取/分类），与新架构不冲突；只是不再让用户在前端选 provider

---

## 阶段十：AI Wiki 系统（用户批准于 2026-09-11 19:17）

### 用户决策（已确认）
- ✅ 框架：MD 副本 + SQLite FTS5 索引 + FastMCP 暴露
- ❌ 暂不上向量库，**只 FTS5**
- ✅ **合并主应用**（不独立进程）
- ✅ MD 副本放**独立目录**（`backend/wiki/`）
- ✅ **方案 A**：HTTP transport（`fastmcp.http_app()` 挂载到 FastAPI `/mcp`）
  - 理由：支持并发查询（生成报告时多文档并发拉取）、支持流式、调试友好
- ✅ **Q2 MD 副本路径**：`backend/wiki/{doc_id}.md`（选项 1，与代码同树，方便备份）
- ✅ **Q3 编辑 UI**：选项 2 = textarea + Markdown 工具栏（零依赖）
- ✅ **Q4 AI 生成**：所有文档都用 AI 生成 title/tags（即使 .md/.txt 也调一次）

### 用户新增需求
1. **文档预览可编辑**：在 DocumentView 预览界面加"编辑"按钮（类似飞书/Notion）
2. **保存同步到 MD 文件**：不影响原文件（只改 MD 副本）
3. **下载可选**：下载按钮提供"原文件 / MD"两个选项
4. **索引与提取并行**：用部署的 AI 大模型同时做
   - 标题提取（基于文件名 + VLM 分析）
   - 标签生成（3-5 个关键词）
   - 关联文件建议（related files）

### 阶段十·步骤 10.1 — 后端：MD 副本 + frontmatter 自动生成
- **做什么**：
  - 新建 `backend/app/services/wiki/storage.py`：MD 副本管理
  - 路径：`backend/wiki/{doc_id}.md`（独立目录）
  - 文件结构：
    ```markdown
    ---
    title: <文件名或 AI 生成>
    source_file: <原文件名>
    doc_type: pdf|docx|xlsx|...
    extracted_at: 2026-09-11T19:17:32
    tags: [tag1, tag2, tag3]
    related: []
    ---

    # <title>

    <提取的 Markdown 内容>
    ```
  - 修改 `content_extractor.py`：`extract_content` 后立即调 `wiki_storage.save_markdown()` 保存副本
  - **索引构建与提取并行**：复用已部署的 `UnifiedAIClient`，prompt 让模型同时返回 `{title, tags}`
  - **Q4 = 所有文档都用 AI 生成 title/tags**（包括 .md/.txt）：
    - 新 prompt：`你是文档元数据生成器。请分析以下文档内容，输出 JSON：{"title": "...", "tags": ["...", "..."]}（3-5 个关键词）`
    - 仅在 `enable_ai_metadata=True` 时调用（用户 SettingsView 可关）
  - **Q5 = AI 元数据生成开关**（用户 2026-09-11 19:30 确认）：
    - 后端 config.py 新增 `AI_METADATA_ENABLED: bool = True`（默认开启）
    - 前端 SettingsView（统一 AI 多模态卡片）加 `<n-switch v-model:value="extractionConfig.ai_metadata_enabled" />`
    - API schema 同步加字段；保存到 .env `AI_METADATA_ENABLED=true|false`
    - 调用前 `if AI_METADATA_ENABLED and AI_SERVICE_ENABLED` 才调 AI
- **能改**：新建 wiki 模块 + 改 content_extractor + config + SettingsView
- **验证**：上传 PDF → 后端 log 显示 `wiki/{id}.md` 已保存；frontmatter 字段正确
- **回退**：删除 wiki 模块 + 撤回 content_extractor 修改

### 阶段十·步骤 10.2 — 后端：SQLite FTS5 索引
- **做什么**：
  - 新建 `backend/app/services/wiki/index.py`：`WikiIndex` 类
  - 表结构（SQLite）：
    ```sql
    CREATE VIRTUAL TABLE docs_fts USING fts5(
        doc_id UNINDEXED, path, title, content, tags, doc_type,
        tokenize='unicode61'
    );
    CREATE TABLE doc_meta(doc_id PRIMARY KEY, path, title, mtime, doc_type, frontmatter_json);
    CREATE TABLE tags(name PRIMARY KEY);
    CREATE TABLE doc_tags(doc_id, tag_name, PRIMARY KEY(doc_id, tag_name));
    CREATE TABLE links(src_doc_id, dst_doc_id, anchor);
    CREATE TABLE doc_links(src_doc_id, dst_doc_id, anchor);  -- 反向
    ```
  - `WikiIndex.index_doc(doc_id)`：把文档内容插入 FTS5 + 抽取 `[[wikilink]]` 和 `#tag`
  - `WikiIndex.rebuild_all()`：扫 `wiki/` 全量重建
  - 调用时机：上传后 / 编辑保存后 / 启动时全量重建
- **验证**：上传后立即查询 `SELECT * FROM docs_fts WHERE docs_fts MATCH '收费网' LIMIT 5` 返回该文档
- **回退**：删除 wiki/index.py

### 阶段十·步骤 10.3 — 后端：MCP tools 暴露
- **做什么**：
  - 在主应用集成 `fastmcp`（`pip install fastmcp`）
  - 注册 6 个 tools：`search_kb` / `get_doc` / `list_backlinks` / `analyze_topic` / `generate_report` / `list_tags`
  - 暴露端点：默认 HTTP（路径待定；stdio 也可作为 WorkBuddy 配置选项）
- **关键决策**：合并主应用 → MCP server 复用 FastAPI lifespan + uvicorn
  - 方案 A：用 `fastmcp.http_app()` 挂载到主 FastAPI（推荐）
  - 方案 B：MCP server 独立子进程，但共用同一 SQLite（更复杂）
- **验证**：WorkBuddy 配置 MCP 后能调用 6 个 tools
- **回退**：删除 wiki/mcp_server.py

### 阶段十·步骤 10.4 — 前端：DocumentView 可编辑预览
- **做什么**：
  - 预览模态框加"编辑"按钮（仅编辑模式下可点）
  - 切换到 textarea（monaco editor 或简单 textarea + markdown-it 反向渲染）
  - "保存"按钮 → 调 `PUT /api/v1/documents/{id}/markdown` → 后端保存到 wiki/{id}.md → 重建该文档索引
  - "取消"按钮 → 退出编辑模式
- **能改**：DocumentView.vue 预览模态框
- **验证**：编辑 → 保存 → 重新预览看到改动 → DB 的 content 也更新
- **回退**：删除"编辑"按钮

### 阶段十·步骤 10.5 — 前端：下载选择原文件 / MD
- **做什么**：
  - 预览模态框"下载"按钮改为下拉菜单：
    - "下载原文件（xxx.pdf）"
    - "下载 Markdown（xxx.md）"
  - 后端新增 `GET /api/v1/documents/{id}/download?type=original|markdown`
- **验证**：点击 2 种下载都成功返回对应文件
- **回退**：恢复单一下载按钮

### 阶段十·步骤 10.6 — 端到端验证
- **做什么**：
  1. 上传 PDF → 后端日志显示 MD 已保存 + FTS5 索引已建
  2. DocumentView 预览 → 点编辑 → 改标题 → 保存 → DB 和 wiki/{id}.md 都更新
  3. 下载按钮 2 种都成功
  4. MCP tools（手动 curl）：`search_kb("收费网")` 返回正确文档列表
- **通过标准**：所有 4 个流程不报错
- **回退**：N/A

---

## 阶段十一：移除 Android 模块与移动端 API（用户批准于 2026-09-12 16:00）

### 决策（用户原话）
> "把 android 模块的相关代码全部删除，后期会用 AI 工作台接入 wiki 的 MCP 做数据查询和利用，不需要安卓客户端了"

- **范围**：Android 客户端目录 + 后端移动端专属 API/Schema/JWT 函数 + 相关文档章节
- **数据访问新路线**：WorkBuddy 等 AI 工作台通过 AI Wiki 的 MCP（`/mcp`，6 个 tools）查询与利用数据，替代 Android 客户端
- **边界说明**（涉及"不能改"清单的例外，已获用户指令授权）：
  - `backend/app/core/security.py` 仅删除 mobile 专属函数与 "mobile" token 类型分支；**access/refresh 通用 JWT 逻辑不动**
  - 不动数据库表结构、CORS、admin 账户、上传白名单
  - `create_refresh_token` / `verify_refresh_token` 属通用 JWT 工具，保守保留（非 android 专属命名）

### 调研结论（关联面清单，2026-09-12 16:05 完成）
| 类别 | 文件/位置 | 动作 |
|------|----------|------|
| Android 客户端 | `android/`（88 个 git 跟踪文件） | 整目录删除 |
| 后端移动端点 | `backend/app/api/endpoints/mobile.py`（8 端点） | 删除 |
| 后端移动 Schema | `backend/app/schemas/mobile.py` | 删除（system.py 依赖先处理） |
| 路由注册 | `backend/app/api/api_v1.py` mobile import + include_router | 删除两行 |
| JWT | `backend/app/core/security.py`：`create_mobile_tokens` / `validate_device_token` / `extract_user_id_from_token` + `create_access_token` 的 mobile 分支 + `verify_token` 白名单的 "mobile" | 删除 |
| 系统信息 | `backend/app/api/endpoints/system.py`：`MobileBaseResponse` import、`mobile_api` 特性、`mobile_config`、mobile 端点列表、`mobile_features` | 清理，`SystemInfoResponse` 改用 `BaseModel` |
| 文档 | `docs/Android应用架构设计.md` / `docs/Android应用测试方案.md` / `docs/移动端API设计方案.md` | 删除 |
| 文档 | `docs/生产环境脚本说明.md` 移动端 API 端点章节 | 删除章节 |
| 文档 | 根 `README.md` 移动端相关小节（功能特性/技术栈/项目结构/更新日志） | 清理 |
| 前端 | 无引用（grep 确认 0 匹配） | 不动 |

### 步骤 K.1 — 删除 android/ 目录与后端移动端文件
- **做什么**：删除 `android/` 整目录；删除 `backend/app/api/endpoints/mobile.py` 与 `backend/app/schemas/mobile.py`
- **能改什么**：仅上述文件
- **不能改什么**：不动 `backend/app/schemas/` 其他文件；不动 `endpoints/` 其他端点
- **怎么验**：`ls android` 报不存在；`ls backend/app/api/endpoints/mobile.py` 报不存在
- **回退方案**：`git checkout HEAD -- android/` + `git checkout HEAD -- backend/app/api/endpoints/mobile.py backend/app/schemas/mobile.py`（android/ 全部 git 跟踪，可完整恢复）

### 步骤 K.2 — 断开 mobile 引用（api_v1.py / security.py / system.py）
- **做什么**：
  1. `api_v1.py`：删除 import 行中的 `mobile` 与 `include_router(mobile.router, ...)` 行
  2. `security.py`：删除 `create_mobile_tokens` / `validate_device_token` / `extract_user_id_from_token` 三个函数；`create_access_token` 删除 `elif token_type == "mobile"` 分支；`verify_token` 白名单 `["access", "refresh", "mobile"]` → `["access", "refresh"]`
  3. `system.py`：删除 `from app.schemas.mobile import MobileBaseResponse`；`SystemInfoResponse` 改继承 `pydantic.BaseModel`；`/info` 响应删除 `mobile_config` 字段与 `mobile_api` 特性标记、`api_endpoints` 中 mobile 端点列表、`/version` 的 `mobile_api` 版本、`/capabilities` 的 `mobile_features` 块
- **能改什么**：仅上述 3 个文件的 mobile 相关部分
- **不能改什么**：
  - 不动 `create_access_token` 的 access/refresh 逻辑与 `create_refresh_token` / `verify_refresh_token`
  - 不动 `system.py` 的 `/health`、数据库状态、平台信息等非 mobile 字段
  - 不动 CORS / JWT 密钥 / admin 账户
- **怎么验**：
  1. `grep -rn "mobile\|Mobile" backend/app/` 应无业务匹配（注释可留）
  2. 后端可启动无 ImportError
- **回退方案**：`git checkout HEAD -- backend/app/api/api_v1.py backend/app/core/security.py backend/app/api/endpoints/system.py`

### 步骤 K.3 — 清理文档
- **做什么**：
  1. 删除 `docs/Android应用架构设计.md`、`docs/Android应用测试方案.md`、`docs/移动端API设计方案.md`
  2. `docs/生产环境脚本说明.md` 删除"移动端API端点"章节
  3. 根 `README.md`：删除"移动端支持"功能小节、"移动端技术 (Android)"技术栈小节、项目结构中的 `android/` 行、更新日志中"移动端 Android 应用框架"条目；新增一句"数据查询通过 AI Wiki MCP 接入"
- **能改什么**：仅上述文档
- **不能改什么**：不动 docs/ 其他文档；不动 AI Wiki 相关文档
- **怎么验**：`grep -rni "android\|移动端" docs/ README.md` 无残留（AI-Wiki 指南中如提及 MCP 路线可保留）
- **回退方案**：`git checkout HEAD -- docs/ README.md`

### 步骤 K.4 — 端到端验证
- **做什么**：
  1. 重启后端（或 import 验证）
  2. `curl http://127.0.0.1:8002/api/v1/mobile/auth/login -X POST` → 期望 404
  3. `curl http://127.0.0.1:8002/api/v1/system/info` → 期望 200 且响应无 mobile 字段
  4. `curl http://127.0.0.1:8002/health` → 200 healthy
  5. `curl http://127.0.0.1:8002/mcp` 相关 → MCP 仍正常（数据查询新路线可用）
  6. 登录 `/api/v1/auth/login` → 200（JWT 未受影响）
- **通过标准**：mobile 端点全部 404；核心功能（登录/系统信息/健康/MCP）全绿
- **回退方案**：N/A（验证步骤）

### 步骤 K.5 — memory-bank 同步
- **做什么**：
  1. `@architecture.md`：删除 android/ 章节（第 3 节）、mobile 端点与 schemas/mobile 条目；新增"数据查询路线：AI Wiki MCP"说明
  2. `@tech-stack.md`：删除"五、Android"章节
  3. `@product-requirements-document.md`：F6 移动端标记为"已移除（2026-09-12），由 AI Wiki MCP 替代"；非目标加"不再开发移动端客户端"
  4. `progress.md`：记录阶段十一完成
- **怎么验**：`grep -rni "android" memory-bank/@*.md` 仅剩"已移除"说明性文字
- **回退方案**：git checkout 对应文件

---

## 阶段十二：修复 start-services.bat 启动报错（用户报告于 2026-09-12 17:23）

### 根因（实测确认）
1. **直接原因**：`start-services.bat:55` 检查 `backend/venv`，本机不存在（依赖此前装在 managed runtime `C:\Users\cccly\.workbuddy\binaries\python\envs\default`）→ 打印 "Virtual environment not found! Please run install-environment.bat first" 后 `exit /b 1`
2. **深层原因**：提示指向的 `install-environment.bat` 根本不存在（实际是 `install-complete.bat`）；且 `install-complete.bat` 用系统 `python` 建 venv，本机 python/node 不在 Windows 系统 PATH（在 WorkBuddy managed runtime）→ `python -m venv venv` 也会失败
3. 附带：`start-services.bat:55` 用 `if not exist "venv"` 相对路径，依赖 cwd 恰为 backend（52 行 cd 后成立，但健壮性差）

### 决策
- 不依赖"先跑安装脚本"的隐性前提：**venv 缺失时自动创建 + 自动装依赖**（python 找不到时回退 managed runtime）
- 保持脚本结构（dev/prod 双模式、start 窗口）不变，只改"环境检查"段

### 步骤 L.1 — start-services.bat 环境检查改造
- **做什么**：
  1. `python` / `node` 检查保留，但 python 找不到时自动回退 `C:\Users\cccly\.workbuddy\binaries\python\versions\3.13.12\python.exe`（存在即用），仍找不到才报错
  2. `cd backend` 后，`venv` 不存在时**自动安装**：`python -m venv venv` → `venv\Scripts\python -m pip install --upgrade pip` → `venv\Scripts\pip install -r requirements-windows.txt`（无 windows 版则退回 requirements.txt）；失败才 pause + exit
  3. 错误提示中的脚本名 `install-environment.bat` → `install-complete.bat`（保留为提示，不再作为硬前置）
- **能改什么**：仅 `start-services.bat`
- **不能改什么**：dev/prod 双模式逻辑、端口 8002/5173、`start` 启动方式、CORS/JWT 等
- **怎么验**：
  1. 删除/保留 `backend/venv` 两种状态下分别双击运行
  2. venv 缺失时自动完成创建+装依赖并继续启动
  3. 后端 8002 / 前端 5173 均 200
- **回退方案**：`git checkout HEAD -- start-services.bat`

### 步骤 L.2 — install-complete.bat python 回退
- **做什么**：
  1. 开头增加 python 探测：系统 `python` 不可用时回退 managed runtime 路径，并把探测结果存 `PYTHON_EXE` 变量
  2. 所有 `python` 调用改用 `%PYTHON_EXE%`
  3. venv 创建后验证 `venv\Scripts\python.exe` 存在
- **能改什么**：仅 `install-complete.bat`
- **不能改什么**：依赖清单（requirements-windows.txt 不动）
- **怎么验**：干净环境（无 venv）双击运行 → venv 建成 + 依赖装完 + 提示 Installation Complete
- **回退方案**：`git checkout HEAD -- install-complete.bat`

### 步骤 L.3 — 端到端验证
- **做什么**：删 `backend/venv`（安全：纯依赖目录）→ 双击 `start-services.bat`（选 1）→ 观察自动装依赖 → 探活 8002/5173
- **通过标准**：一键启动成功；两服务健康
- **回退方案**：N/A

---

## 阶段十三：修复 AI 服务配置保存不生效 + 补"全格式 AI 提取"开关（用户报告于 2026-09-12 21:16）

### 用户反馈
1. 系统设置里"启用 AI 服务"，填服务地址/模型名后保存，**会自动恢复默认选项**（无法保存）
2. 之前"统一 AI 多模态服务"里加过一个"是否所有格式文档全部使用 AI 提取 md"的功能开关（不开则默认只有 PDF/图片走 AI，AI 失败降级本地引擎），**界面上没看到**（该功能实际从未落地，需补全）

### 根因（实测确认，2026-09-12）
1. **保存不生效（核心 bug）**：`config.py` 的 `settings = Settings()` 在模块 import 时**只加载一次** `.env` 到内存单例。`extraction_config.py` 的 PUT 只把新值**写进 `.env` 文件**（磁盘），但运行中进程的内存 `settings` 从不刷新 → 后续 GET 和真正的 AI 提取（`pdf_extractor`/`image_extractor` 都读 `settings.AI_SERVICE_*`）仍用**旧值**，直到整进程重启。
   - 实测：PUT 写 `.env` 成功，但同一进程紧接着 GET 仍返回旧 url/model。这就是用户看到的"保存后恢复默认"。
   - **修复方向**：PUT 写 `.env` 后**同步刷新内存 `settings`**，让改动**立即生效、无需重启**（比"重启生效"体验好，且消除用户困惑）。
2. **全格式开关缺失**：全仓 grep `AI_ALL_FORMATS`/`all_formats`/`全部格式` 均无命中 → 该功能**从未实现**（用户记忆中的改动已丢失）。需按用户描述补全：
   - 默认（开关关）：仅 **PDF + 图片** 调用统一 AI；AI 失败降级本地引擎
   - 开关开：**所有格式**（docx/xlsx/txt 等）也尝试 AI 提取 md；AI 失败降级本地引擎

### 决策
- 配置持久化沿用 `.env`（现有机制不动），只补"写文件 + 刷内存"双写
- 新增配置项 `AI_ALL_FORMATS_AI`（默认 `false`），走同一 `.env` 读写 + 内存刷新链路
- 全格式 AI 提取统一在 `router.py` 收口（单一入口，避免改 4 个 extractor）：PDF/图片保持各自原 AI 路径；其余格式在 `AI_ALL_FORMATS_AI=true` 时先试 AI（纯文本喂多模态模型），失败/未启用则走原本地引擎
- **能改什么**：`config.py`、`extraction_config.py`、`extraction-config.ts`、`SettingsView.vue`、`router.py`
- **不能改什么**：各 extractor 的本地引擎逻辑（pymupdf/docx/openpyxl/tesseract）、鉴权、`.env` 既有键值、`UnifiedAIClient` 协议

### 步骤 M.1 — 配置内存热刷新（修复"保存不生效"）
- **做什么**：
  1. `config.py`：给 `Settings` 加 `reload()` 方法（从磁盘 `.env` 重读并刷新实例属性）
  2. `extraction_config.py` PUT：写完 `.env` 后调用 `settings.reload()`；响应 `restart_required` 改为 `false`，`message` 改为"配置已保存并立即生效（无需重启）"
- **能改什么**：`config.py`、`extraction_config.py`
- **不能改什么**：`Settings` 既有字段默认值、CORS 逻辑、JWT
- **怎么验**：
  1. 登录后 GET→PUT（改 url/model）→ 同一进程再 GET，**返回值 = 新值**（不再回退）
  2. `python -c` 直接 import 验证 `settings.reload()` 不报错
- **回退方案**：`git checkout HEAD -- backend/app/core/config.py backend/app/api/endpoints/extraction_config.py`

### 步骤 M.2 — 新增"全格式 AI 提取"开关（后端）
- **做什么**：
  1. `config.py`：新增 `AI_ALL_FORMATS_AI: bool = False`（紧跟阶段七统一多模态块）
  2. `extraction_config.py`：`ExtractionConfig` 加 `ai_all_formats_ai`；`_load_from_settings` 读它；PUT 的 `.env` 清理列表 + 写入列表加 `AI_ALL_FORMATS_AI=`
- **能改什么**：`config.py`、`extraction_config.py`
- **不能改什么**：既有字段
- **怎么验**：`python -c` 确认 `settings.AI_ALL_FORMATS_AI` 默认 `False`；PUT 带 `ai_all_formats_ai=true` 后 `.env` 出现 `AI_ALL_FORMATS_AI=true`

### 步骤 M.3 — router 收口"全格式 AI 提取 + 失败降级"
- **做什么**：
  1. `ai_client.py`：给 `UnifiedAIClient` 加 `parse_text(text)` 方法（纯文本喂多模态模型，openai/ollama 两分支，复用 `vision_parse` 的调用骨架但不发图片）
  2. `router.py` `extract()`：找到对应 extractor 后——
     - 若该格式是 PDF/图片：直接走原 extractor（其内部已有 AI 优先 + 降级）
     - 否则（docx/xlsx/txt）且 `AI_ALL_FORMATS_AI=true` 且 `AI_SERVICE_ENABLED=true`：先读原文文本 → `client.parse_text()` 得 md；成功用 AI md（`engine=unified-ai`），失败/未启用则**降级**原 extractor 本地引擎
     - `AI_FALLBACK_TO_LOCAL=false` 且 AI 失败：直接返回 AI 错误（不降级）
- **能改什么**：`ai_client.py`（加方法）、`router.py`
- **不能改什么**：各 extractor 的 `extract()` 本地逻辑、`ExtractionResult` 结构
- **怎么验**：
  1. 开关关：上传 .docx/.xlsx/.txt → `json_data.engine` 为本地引擎（非 unified-ai），结果与现状一致
  2. 开关开 + AI 服务可达：.docx 提取 → `engine=unified-ai`
  3. 开关开 + AI 服务不可达：.docx 提取 → 降级本地引擎，`engine` 为本地，**不报错**
- **回退方案**：`git checkout HEAD -- backend/app/services/extraction/router.py backend/app/services/extraction/ai_client.py`

### 步骤 M.4 — 前端补开关 + 文案
- **做什么**：
  1. `extraction-config.ts`：`ExtractionConfig` 接口加 `ai_all_formats_ai: boolean`
  2. `SettingsView.vue`：
     - 卡片标题 "（PDF + 图片提取）" → 体现"默认 PDF+图片，可扩全部格式"
     - 在"启用 AI 服务"开关下方加一行"所有格式文档也使用 AI 提取 md"开关（`ai_all_formats_ai`），feedback 文案说明：关闭=仅 PDF/图片走 AI，AI 失败降级本地；开启=docx/xlsx/txt 也尝试 AI
     - `extractionConfig` 初始对象加 `ai_all_formats_ai: false`
- **能改什么**：`extraction-config.ts`、`SettingsView.vue`
- **不能改什么**：其他卡片（用户管理/系统信息）
- **怎么验**：`npx vue-tsc --noEmit` 0 error；设置页能看到并操作该开关；保存后刷新仍保持

### 步骤 M.5 — 端到端验证
- **做什么**：后端起（reload 已生效）→ 前端登录 → 设置页保存新地址/模型 → 刷新不恢复默认；开关开/关分别上传 docx 验证 engine
- **通过标准**：保存立即生效不回退；全格式开关开=AI 提取、关=本地、AI 挂=降级
- **回退方案**：各步骤独立回退

---

## 阶段十四：测试连接增强——校验模型名真实可用（用户反馈于 2026-09-12 22:05）

### 用户反馈
系统设置里填新模型后点"测试连接"，输出 `reachable: true, status: 200`（`/v1/models` 端点）。
实测发现隐患：llama.cpp 服务里模型 ID 是**完整路径**（`/home/ubuntu/moxing/.../Qwen3.8-27B-Q8_0.gguf`），
而设置里填的是**短名**（`Qwen3.8-27B-Q8_0`）→ `/chat/completions` 会 404，但旧测试只查 `/models` 通不通，
照样显示可达，**真正的提取请求才会失败**。测试连接必须把模型名一起校验。

### 根因
- `extraction_config.py` 的 `test_extraction_config` 只 `GET /models`（openai）/ `/api/tags`（ollama）判 `status < 500`，
  **不解析返回列表、不比对 model 字段** → "服务可达 ≠ 模型可用"

### 决策
- 测试连接升级：拉模型列表 → 把用户填的 `model` 与列表比对（兼容：完整 ID / 路径尾段 / 短名包含匹配）
- 结果结构向后兼容（保留 `reachable`/`status`），新增 `model` 校验块：`model_found` + `available_models` + `hint`
- 不自动改用户的模型名（避免替用户做决定），但在 hint 里给出"服务里实际加载的模型 ID"，让用户一键可抄
- 顺带：把当前用户配置里的短名修正为服务实际 ID（本次用户明确反馈模型名填错场景）

### 步骤 N.1 — test 端点加模型名校验
- **做什么**：
  1. openai 分支：`GET /models` 后解析 `data[].id`（兼容 `models[].name` / `data[].model`）→ 与 `cfg.ai_service_model` 比对
  2. 比对规则（任一命中即 found）：精确相等 / 路径尾段相等（`/a/b/m.gguf` vs `m.gguf`）/ 去扩展名后相等 / 短名被完整 ID 包含
  3. ollama 分支：`GET /api/tags` 解析 `models[].name` 同样规则
  4. 结果块：`{ reachable, status, model: { requested, found, available: [...], hint? } }`
- **能改什么**：仅 `extraction_config.py` 的 test 端点
- **不能改什么**：GET/PUT 端点、.env 读写、reload 逻辑
- **怎么验**：
  1. 用户真实服务（8081）+ 短名 `Qwen3.8-27B-Q8_0` → `model.found` 应为 false（短名不匹配完整路径），`available` 列出真实 ID，hint 提示
  2. 改成完整路径 ID → `model.found=true`
  3. 服务不可达 → 结构与原来兼容（reachable=false + error）
- **回退方案**：`git checkout HEAD -- backend/app/api/endpoints/extraction_config.py`

### 步骤 N.2 — 前端展示模型校验结果
- **做什么**：`SettingsView.vue` 测试连接结果区，在 `ai_service.model` 存在时：
  - found=true → 绿色提示"模型可用"
  - found=false → 红色提示"模型名未在服务中找到" + 列出 `available_models`（可点击/可复制）+ hint
- **能改什么**：`SettingsView.vue`（测试结果显示区）、`extraction-config.ts`（TestResult 类型补字段）
- **不能改什么**：其他卡片
- **怎么验**：vue-tsc 0 error；测试连接后界面正确显示模型校验结果
- **回退方案**：`git checkout HEAD -- frontend/src/views/SettingsView.vue frontend/src/services/extraction-config.ts`

## 阶段十五：修复后台提取 worker 不运行（用户上传卡在"内容提取中"，用户报告于 2026-09-12 22:30）

### 现象
用户上传"交换机统计0723.xls"后前端一直显示"内容提取中"；后端任务状态 `extract_75_*` 全部
`status=pending, started_at=null, progress=0`（worker 一接手就会先写成 processing/10）。

### 根因（实测确认）
`main.py:162` 的 `app.router.lifespan_context = mcp_app.lifespan`（阶段十·W3 挂 MCP 时引入）
**整体覆盖**了主应用的 `lifespan` 上下文 → 主应用 startup（bcrypt 校验 / 默认用户初始化 /
`startup_background_tasks()` 启动后台提取 worker）**永远不执行**。
- 证据：后端启动日志无任何主 lifespan 的 print（"启动 运维资产管理系统" / "后台任务处理器已启动" 均缺失），
  只有 uvicorn 通用 startup 行；`/mcp` 挂载 print 正常。
- 之前（9-11）上传能成功是因为那台后端进程是在 MCP 代码合并前启动的、worker 存活；
  重启后（带 bug 的新进程）worker 再没起来。
- 附带影响：`init_default_users()` 不跑（admin 缺失时不会自动建）、bcrypt 启动自检不跑。

### 决策
- 不"绕过"覆盖，而是**合并**：主 lifespan 包一层，startup 内先 `async with mcp_app.lifespan(app)`
  再执行主应用三步，yield 后顺序回收 —— 一次 startup 同时满足 MCP 与主应用。
- 回退安全：try/except 保留原挂载 print 语义；若 MCP 初始化异常，主 lifespan 仍要能跑（worker 必须起来）。

### 步骤 P.1 — main.py 合并 lifespan
- **做什么**：
  1. `lifespan` 函数体改为：`async with mcp_lifespan(app):`（mcp_lifespan 为模块级变量，MCP 挂载失败时为 `asynccontextmanager` 空实现）内执行原有 3 步（bcrypt/用户/worker）→ `yield`
  2. 删除 `app.router.lifespan_context = mcp_app.lifespan` 覆盖行（MCP lifespan 改由主 lifespan 内部持有）
  3. 模块级 `mcp_lifespan` 默认空 asynccontextmanager；MCP try 块里赋值为 `mcp_app.lifespan`
- **能改什么**：仅 `main.py`
- **不能改什么**：`/mcp` 挂载点、api 路由、CORS
- **怎么验**：
  1. 重启后端 → 启动日志出现"启动 运维资产管理系统" + "后台任务处理器已启动" + "AI Wiki MCP server 已挂载到 /mcp"
  2. `/health` 200；`/mcp` initialize 200（MCP 仍可用）
  3. 重新上传 .xls → 任务状态 5 分钟内走到 processing → completed/failed（不再永久 pending）
- **回退方案**：`git checkout HEAD -- backend/app/main.py`

### 步骤 P.2 — 存量卡死任务清理 + 重触发
- **做什么**：
  1. 清理 `task_status/` 里 3 个卡死的 `extract_75_*` pending 文件（避免前端一直轮询旧任务）
  2. 用 API 触发文档 75 重新提取（或让用户在文档页点"重新提取"），验证全链路
- **通过标准**：新任务 processing → completed（内容入库）或明确 failed（含错误信息）
- **回退方案**：N/A

---

### 步骤 N.3 — 实证验证（用户模型名实际可用，无需改配置）
- **实测结论**（2026-09-12 22:05，真实 completion 调用 max_tokens=1）：
  - 短名 `Qwen3.8-27B-Q8_0` → **HTTP 200**（11.4s，冷加载+首 token）
  - 完整路径 `.../Qwen3.8-27B-Q8_0.gguf` → **HTTP 200**（0.3s，已驻留）
  - → 用户当前配置的短名**真实可用**（llama.cpp 单模型模式接受该名），**无需修改 `.env`**
- **做什么**：
  1. 用新 test 端点跑用户配置 → `model.found=true`（短名命中文件名 stem）
  2. 直接调 `/chat/completions` 验证短名/完整路径均 200（已完成）
  3. 向用户说明：配置可用；短名单模型模式下可用，但完整路径是"多模型/换服务"时最稳的写法，是否改由用户决定
- **通过标准**：测试连接 model 校验通过；真实 completion 200
- **回退方案**：N/A（未改 .env）
- **教训**：判定"模型名是否可用"不能只靠 /models 列表做字符串猜测，**真实 completion 调用才是金标准**；单模型 llama.cpp 对短名/任意名宽容，多模型/严格模式才需精确完整 ID

---

## 阶段十六：统一三个下载点（原文件 / Markdown 二选一 + 修复下载失败）（用户报告于 2026-09-13 09:10）

### 现象
系统内文档下载有 3 个点位，行为不一致且部分失败：
1. **预览中下载**（DocumentView 预览弹窗）— 能弹出"原文件 / MD"选择，但**下载失败**
2. **文档条目右侧下载按钮**（DocumentView 列表行）— 点击**显示失败**，无选择
3. **智能搜索结果下载**（SearchView 结果卡片 / 预览 / 不可预览项）— 走旧端点，无 MD 选择

### 根因（实测确认）
- **后端 500（核心）**：`wiki.py` 的 `download_doc` 用 `Path(row[0])` 拼原文件路径，但**`Path` 从未 import** → `NameError: name 'Path' is not defined` → 任何真实文档的"原文件"下载一律 500。
- **MD 副本缺失**：部分文档（如 doc 70）只有 DB 里 `content` 字段、没有 `wiki/{id}.md` 副本 → markdown 分支 `get_path().exists()` 为假直接 404。
- **前端三处各自实现**：DocumentView 列表行用 `h(NButton)` 无下拉；SearchView 走 `apiService.download('/documents/{id}/download')`（无 MD 选项）；预览弹窗虽有下拉但共用失败的后端。三处逻辑不统一。

### 决策
- 后端只改 `wiki.py`（补 import + MD 副本缺失时回退 DB `content` 拼 Response），**不动**路由/鉴权/上传。
- 前端抽一个**共享工具** `frontend/src/utils/file-download.ts`（`downloadWikiDocument(docId, type, fallbackTitle)`），三个点位**全部**改为：`NDropdown`（原文件 / Markdown）+ 委托该工具 → 行为完全一致。
- 统一打到 wiki 下载端点 `GET /api/v1/wiki/download/{id}?type=original|markdown`（带 Bearer token，blob 触发下载，返回真实文件名）。

### 步骤 16.1 — 后端修复（wiki.py）
- **做什么**：
  1. 顶部补 `from pathlib import Path`
  2. markdown 分支：`md_path.exists()` 为假时，回退读 DB `documents.content` + `title`，拼 `Response(content=..., media_type="text/markdown; charset=utf-8")` + RFC5987 `Content-Disposition`（`filename*=UTF-8''…`）；两者皆无才 404
- **能改什么**：仅 `backend/app/api/endpoints/wiki.py`
- **不能改什么**：下载路由路径、鉴权、`get_path` 逻辑
- **回退方案**：`git checkout -- backend/app/api/endpoints/wiki.py`

### 步骤 16.2 — 前端共享工具（新文件）
- **做什么**：新建 `frontend/src/utils/file-download.ts`
  - `type DownloadType = 'original' | 'markdown'`
  - `resolveApiBaseUrl()`（env `VITE_API_BASE_URL` → 否则 `host:8002`）
  - `parseFilenameFromDisposition(...)`（解析 RFC5987 / 普通 filename）
  - `downloadWikiDocument(docId, type='original', fallbackTitle)` — fetch + Bearer token + blob + `URL.createObjectURL` 触发下载，失败抛带后端 detail 的 Error，成功返回文件名
- **回退方案**：删除该文件

### 步骤 16.3 — DocumentView 三处统一
- **做什么**：
  1. import 补 `NDropdown` + `downloadWikiDocument`
  2. 列表行 `h(NButton)` 改为 `h(NDropdown, { options: downloadMenuOptions, onSelect })`，内部默认按钮仍"下载"
  3. 预览弹窗原有下拉保留，`downloadDocument` 委托 `downloadWikiDocument`
- **能改什么**：`DocumentView.vue`
- **回退方案**：`git checkout -- frontend/src/views/DocumentView.vue`

### 步骤 16.4 — SearchView 三处统一
- **做什么**：
  1. import 补 `downloadWikiDocument` + `downloadMenuOptions`
  2. 结果卡片 / 预览头部 / 不可预览项 3 个按钮全部包 `<n-dropdown>`（原文件 / Markdown）
  3. `downloadDocument(id, type, title)` 委托 `downloadWikiDocument`（替换旧 `apiService.download`）
- **能改什么**：`SearchView.vue`
- **回退方案**：`git checkout -- frontend/src/views/SearchView.vue`

### 验证（端到端，真实登录 token + httpx 测真实字节数）
- `vue-tsc --noEmit` 0 error
- 重启后端（task Rgs9ND）后实测：
  - doc71 original（xlsx，有文件）→ HTTP 200，size 正确，`attachment; filename*=utf-8''…`
  - doc71 markdown（有 MD 副本）→ HTTP 200，size 正确
  - doc70 original（md 文件）→ HTTP 200，size 正确
  - doc70 markdown（**无 MD 副本 → 回退 DB 内容**）→ HTTP 200，内容为 `# Ollama + Open WebUI…`
  - doc999（不存在）→ HTTP 404
- **通过标准**：三个点位均能"原文件 / Markdown"二选一并真实下载成功；无 MD 副本时 markdown 走 DB 内容不 404

### 教训
- `FileResponse` / 拼路径前确认 `Path` 已 import——这类"500 但日志只有一行 NameError"的 bug 极隐蔽，下载类端点必须端到端拉真实字节验证
- 多入口同功能应抽共享 util 收口，避免三处各写各的、改一处漏两处
- markdown 下载要有"MD 副本缺失 → 回退 DB `content`"的兜底，否则早期未生成 wiki 副本的文档会 404

---

## 阶段十七：修复设置页打开时 AI 配置不加载（误报"恢复默认"）（用户报告于 2026-09-13 09:56）

### 现象
用户重启后端后反映：系统设置里 AI 服务"又关闭并恢复默认"。

### 根因（实测 + git diff 确认）
- **后端无问题**：`GET /api/v1/settings/extraction-config` 用有效 token 返回**用户真实配置**（`ai_service_enabled=true` / `http://192.168.66.234:8081/v1` / `Qwen3.8-27B-Q8_0` / `ai_all_formats_ai=true`）；`.env` 文件未变、后端 CWD 正确（`backend/`）、`SECRET_KEY` 为固定串（非随机，重启不会让旧 token 失效）。
- **真根因在前端**：`SettingsView.vue` 的 `onMounted` **遗漏了 `loadExtractionConfig()` 调用**。
  - git diff 证据：阶段十三重构时，旧的 `loadAIConfig()`（在 onMounted 里）被删除，但**未替换**为新的 `loadExtractionConfig()`。
  - 后果：设置页每次打开/刷新，AI 配置**从不从后端拉取**，`extractionConfig` ref 一直停留在初始化默认值（`enabled:false` / `localhost:8080` / `qwen3-vl-8b`）。
  - 用户配置的 enabled/url/model **始终安全存在后端**，只是前端从未去读 → 看起来"恢复默认"。
  - "重启后才发现"是时间巧合：重启前用户可能一直停留在未刷新的页面上（内存里还是上次保存的值），重启后刷新页面才暴露"从未加载"。

### 决策
- 只改 `frontend/src/views/SettingsView.vue` 的 `onMounted`，补一行 `loadExtractionConfig()`（不依赖登录态，直接调）。
- 不动后端、不动 service、不动 .env。

### 步骤 17.1 — onMounted 补加载
- **做什么**：`onMounted` 内 `loadCurrentUser().then(...)` 之前加 `loadExtractionConfig()`
- **能改什么**：仅 `SettingsView.vue` 的 onMounted
- **不能改什么**：`loadExtractionConfig` 函数体、service 层、后端
- **回退方案**：`git checkout -- frontend/src/views/SettingsView.vue`

### 验证
- `vue-tsc --noEmit` 0 error
- 后端 `GET /api/v1/settings/extraction-config`（有效 token）返回用户真实配置（已实测 200 + 正确值）
- 前端 5173 / 后端 8002 均在运行（Vite HMR 生效）
- **通过标准**：刷新设置页后 AI 服务开关为开启、显示用户真实 url/model（不再是 localhost:8080 / qwen3-vl-8b）

### 教训
- 重构"旧加载函数 → 新 service"时，**每个调用点都要同步替换**，尤其 `onMounted` 这类一次性触发处最容易漏
- "配置恢复默认"类问题先验证后端真实返回值（带 token 的 GET），别急着怀疑持久化/重启/CWD——往往是前端根本没拉取
- 前端"显示默认值" ≠ "后端存的是默认值"：ref 的初始化默认值与后端真实值要分开看

---

## 阶段十八：AI Wiki 多模态增强——图片提取 + 文件分类 + 精准检索（参考 OpenKB，用户提出于 2026-09-13 10:56）

### 背景与目标
用户用 AI 工具台（WorkBuddy）通过 `/mcp` 调用 AI Wiki 撰写报告/PPT 时，需要**快速精准地搜到文档内容和图片**（尤其是 PDF 里嵌的图、截图、拓扑图）。
参考项目：[VectifyAI/OpenKB](https://github.com/VectifyAI/OpenKB)（PageIndex 生态，LLM 编译式 wiki + 多模态检索）。

### OpenKB 可借鉴点（已通读源码）
1. **PDF 图片按阅读顺序单独提取**（`openkb/images.py`）：用 pymupdf `page.get_text("dict")` 按 block 遍历，type=1 即图片块 → `Pixmap` 存 PNG，**在 MD 中原位插入 `![alt](相对路径)`**，保留图片在文档中的位置；`_MIN_IMAGE_DIM=32` 过滤图标/噪点。
   - 关键：用 dict-mode 而非 `get_images()`——**能抓到矢量渲染图**（`get_images()` 只拿嵌入位图，会漏图）。
2. **base64 内嵌图 + 相对路径图落盘重写**：markitdown 转换出的 MD 里 `data:image/...;base64` 和相对路径图，统一解码/拷贝到 `images/{doc_name}/`，链接重写为统一前缀，渲染器无关。
3. **图片按文档分目录**：`images/{doc_name}/p{页}_img{n}.png`，命名带页码，天然可溯源。
4. **图片可被 AI 工具台直接"看"**：`read_wiki_image(path)` 返回 base64 data URL，路径限制在 wiki 根内（防穿越）；查询 agent 配 `get_image` 工具，遇到"要看图才能答"的问题才调。
5. **长文档分页存 JSON**（`{page, content, images}[]`）+ PageIndex 树索引——我们暂不引入（PageIndex 是独立重依赖，见"非目标"），但**分页结构值得借鉴**用于"取某几页"。
6. **frontmatter 是单一事实源**：title/tags 写在 MD 头部，检索与展示都读它（我们已具备）。
7. **OpenKB 没做的（我们的机会）**：它**不给图片生成文字描述**（alt 一律 "image"）→ 图片无法被全文搜索命中。我们用现成的多模态 AI 给每张图生成中文描述，检索精度反超。

### 现状差距（实测确认）
| 能力 | 现状 | 差距 |
|------|------|------|
| PDF 内嵌图 | `pdf_extractor.py` 只把**整页渲染**喂 AI 做 OCR/解析，**不单独落盘图片** | 无法按图检索、无法取原图 |
| 独立图片文档 | OCR/AI 出文字描述，**原图未入 wiki 索引** | 搜不到图、取不到图 |
| 图片可检索性 | 零 | MD 里没有任何图片引用 |
| 中文分词 | FTS5 `unicode61` 对**连续中文几乎不分词**（"运维报告"≠"运维"+"报告"） | 中文短词搜索命中率低 |
| 文件"文类" | 只有扩展名 `doc_type`（pdf/docx/xlsx…）+ AI tags | 无业务分类维度（运维报告/应急预案/资产台账/拓扑图…） |
| 检索结果粒度 | 整篇文档 + snippet | 无"命中文档的哪些图"信息 |
| MCP 工具 | 6 个（search_kb/get_doc/get_doc_content/list_backlinks/list_tags/generate_report） | 无取图工具、无按图搜 |

### 决策与边界
- **只增强 wiki 子系统**（`services/wiki/` + `services/extraction/` 的 PDF/图片分支 + `wiki.py` 端点 + MCP tools），**不动**文档主表结构、鉴权、上传流程。
- **零新依赖**：pymupdf 已在 venv（1.28.2）；SQLite 3.53 原生支持 FTS5 `trigram`（已实测）；不引入 PageIndex/向量库（保持"零向量库"架构原则）。
- **图片描述用现成多模态 AI**（`UnifiedAIClient.vision_parse`，用户已配 Qwen 多模态）；AI 不可用时降级：alt 用"第N页图M"，不影响主流程。
- **旧文档不自动重跑**：新增"重建索引"端点，用户按需触发（含图片补提取）。

### 非目标（本次不做）
- ❌ PageIndex 树索引（重依赖 + 外部服务，留作远期）
- ❌ 图片向量/以图搜图（需向量库，违反技术栈红线）
- ❌ PPT 直接生成（MCP 返回结构化素材即可，PPT 由 WorkBuddy 的 tencent-pptx 等 skill 完成）
- ❌ 前端 UI 大改（图片列表只加最小展示，不做图片管理页）

### 步骤 18.1 — 后端：图片提取器（新文件 `services/wiki/image_extractor.py`）
- **做什么**：
  1. 新模块 `extract_pdf_images(pdf_path, doc_id)`：pymupdf dict-mode 遍历，type=1 且宽高 ≥ 32px 的图块 → Pixmap 转 PNG → 存 `wiki/images/{doc_id}/p{页}_img{n}.png`；返回 `[{page, file, rel_path, size}]`
  2. 新模块 `register_image_doc(doc_id, source_path, description)`：独立图片文档（png/jpg 上传）→ 拷贝到 `wiki/images/{doc_id}/`（保留原扩展名），登记进图片表
  3. 命名规范照 OpenKB：`p{页码}_img{序号}.png`（独立图片文档无页码，用 `img1.png`）
- **能改什么**：仅新增该文件
- **不能改什么**：uploads/ 原文件（只读源，拷贝进 wiki）
- **怎么验**：对测试 PDF（含 2+ 张图）跑函数 → `wiki/images/{id}/` 出现 PNG，数量/页码正确；图标类小图被过滤
- **回退方案**：删除新文件

### 步骤 18.2 — 后端：图片描述 + 图片表（`services/wiki/` 扩展）
- **做什么**：
  1. `metadata.py` 加 `describe_image_via_ai(image_path)`：多模态 AI 生成中文描述（≤ 60 字，说明图里是什么：拓扑/表格/截图/设备…）；AI 关闭/失败时回退 `第{N}页图{M}`
  2. `index.py` 加表 `wiki_images(doc_id, file, page, caption, fts 内容列)` + FTS5 虚拟表 `images_fts`（caption + 文件名 + 所属文档 title，**tokenize='trigram'** 解决中文短词）
  3. 图片描述写入后同步进 `images_fts`
- **能改什么**：`metadata.py`、`index.py`（加表/加方法，不删旧表）
- **不能改什么**：`docs_fts`/`doc_meta`/`doc_tags`/`doc_links` 现有结构
- **怎么验**：`describe_image_via_ai` 对样图返回中文描述；断网/AI 关闭时回退文案不抛错；`images_fts` 用中文短词（如"拓扑"）能命中
- **回退方案**：git checkout 两文件

### 步骤 18.3 — 后端：MD 副本内嵌图片引用（`content_extractor.py` 衔接）
- **做什么**：
  1. `extract_content_async` 里，PDF 文档：调 18.1 提取图片 → 在 MD 正文**原图位置**插入 `![{caption}](images/{doc_id}/{file})`（按页码插入到对应位置；pymupdf 文本与图片按 block 顺序，可合并为一次遍历：文本块出 MD、图片块出引用）
  2. 独立图片文档：MD 副本正文 = `![{caption}](images/{doc_id}/img1.png)` + 描述段
  3. 非 PDF 文档（docx/xlsx）本次**不做**内嵌图提取（docx 内嵌图留 18.5 可选扩展），不影响
- **能改什么**：`content_extractor.py`、`extraction/pdf_extractor.py`（输出结构加 images 元数据）、`storage.py`（write 支持含图 MD）
- **不能改什么**：提取主流程的成功/失败语义、DB `documents` 表写入
- **怎么验**：重新提取测试 PDF → `wiki/{id}.md` 里出现 `![...](images/...)` 引用且数量与落盘图一致；`/api/v1/wiki/download/{id}?type=markdown` 下载含图 MD
- **回退方案**：git checkout 三文件

### 步骤 18.4 — 后端：中文分词升级（FTS5 trigram 双索引）
- **做什么**：
  1. `index.py` 新 FTS 表 `docs_fts_zh`（tokenize='trigram'，同列）；`index_doc` 同时写两份
  2. `search()` 改为**双路合并**：unicode61 MATCH（英文/术语）+ trigram（中文子串，查询 <2 字符时跳过 trigram——trigram 要求 ≥3 字节…注意中文 1 字=3 字节，2 字中文=6 字节 OK，1 字中文走 LIKE 兜底），结果按 doc_id 去重合并排序
  3. 旧库迁移：启动时若 `docs_fts_zh` 不存在则建表 + 触发一次 `rebuild_all`
- **能改什么**：仅 `index.py`
- **不能改什么**：MCP tool 签名（search_kb 入参出参不变，只提升内部命中）
- **怎么验**：建 3 篇含"交换机""运维报告"的测试 MD → 搜"运维"、"交换机维"（子串）均命中；英文搜 "OpenAI" 仍命中
- **回退方案**：git checkout index.py

### 步骤 18.5 — 后端：文件业务分类（文类）增强
- **做什么**：
  1. `metadata.py` 的 `METADATA_PROMPT` 加 `doc_category` 字段，**受控词表**：`运维报告 / 应急预案 / 操作规程 / 资产台账 / 拓扑与配置 / 会议纪要 / 培训材料 / 其他`（词表放 config 常量，可扩展）；AI 必须选词表内一项
  2. frontmatter 加 `doc_category`；`doc_meta` 表加列 `doc_category`（启动时 `ALTER TABLE` 兼容旧库）
  3. `search_kb` 加可选参数 `category`；`list_tags` 旁加 `list_categories()`
- **能改什么**：`metadata.py`、`index.py`（加列/加方法）、`mcp_server.py`（参数）、`storage.py`（frontmatter 字段）
- **不能改什么**：现有 tags 语义（category 是新增维度，不替代 tags）
- **怎么验**：重新提取 2 篇（一篇周报一篇拓扑图）→ frontmatter 各有词表内 category；`search_kb(category="应急预案")` 过滤正确
- **回退方案**：git checkout 四文件

### 步骤 18.6 — MCP：新增 2 个工具 + 增强 search_kb
- **做什么**：
  1. 新 tool `get_doc_images(doc_id)`：返回该文档全部图片 `[{file, page, caption, url}]`，`url` 为可下载的 HTTP 地址（`http://<host>:8002/api/v1/wiki/images/{doc_id}/{file}`，host 用请求方可达地址，默认 127.0.0.1）
  2. 新 tool `search_images(query, top_k)`：查 `images_fts`，返回 `[{doc_id, title, page, caption, url}]`——**写报告找图的主入口**
  3. `search_kb` 结果每项加 `images` 计数（该文档有多少张已索引图），让 AI 知道"这篇有图可取"
  4. 新 HTTP 端点 `GET /api/v1/wiki/images/{doc_id}/{filename}`（鉴权 + 路径防穿越，只允许 `wiki/images/` 下）
- **能改什么**：`mcp_server.py`、`wiki.py`
- **不能改什么**：现有 6 个 tool 的行为
- **怎么验**：WorkBuddy 连 `/mcp` → `search_images("网络拓扑")` 返回带 URL 的图列表；用返回 URL 带 token 能下载 PNG（httpx 验字节）
- **回退方案**：git checkout 两文件

### 步骤 18.7 — 端点：重建索引 + 存量补图
- **做什么**：
  1. `POST /api/v1/wiki/rebuild`（admin）：全量 `rebuild_all()` + 对已有 PDF 文档补跑图片提取（`uploads/` 原文件还在的）
  2. 响应返回统计 `{docs, images, failed: [...]}`
- **能改什么**：`wiki.py`
- **不能改什么**：文档主表
- **怎么验**：重启后调一次 rebuild → 统计合理；旧 PDF 文档补出图片与引用
- **回退方案**：git checkout wiki.py

### 步骤 18.8 — 前端（最小改动）
- **做什么**：
  1. 文档预览（MD 渲染）支持 `images/{doc_id}/xxx.png` 相对路径 → 拼成 wiki 图片端点 URL（markdown-renderer.ts 加 base 处理）
  2. 文档详情/预览头部加一行"📷 N 张图片"（读 get_doc_images，点击可单张查看）——**不做**图片管理
- **能改什么**：`markdown-renderer.ts`、`DocumentView.vue`（预览区）
- **不能改什么**：下载/编辑逻辑（阶段十六成果）
- **怎么验**：含图 MD 预览能显示图片；无图文档不显示该入口
- **回退方案**：git checkout 两文件

### 步骤 18.9 — 端到端验收
- **做什么**：
  1. 上传 1 份含 3+ 张图的 PDF（运维报告类）+ 1 张独立 PNG（拓扑图）
  2. WorkBuddy 连 `/mcp` 走完整链路：`search_kb("交换机")` → 命中且带 images 计数 → `get_doc_images` / `search_images("拓扑")` 取图 URL → 下载 PNG 成功 → `get_doc_content` 的 MD 含图引用与描述
  3. 用取回的内容+图片让 WorkBuddy 生成一页 PPT/报告（人工验收可用性）
- **通过标准**：全链路 200 且图片字节正确；中文短词/子串搜索命中；category 过滤生效
- **回退方案**：N/A（验收不改代码）

### 实施顺序与风险
- 顺序：18.1 → 18.2 → 18.3 → 18.4 → 18.5 → 18.6 → 18.7 → 18.8 → 18.9（每步独立可验、可回退）
- 风险 1：pymupdf dict-mode 对**纯矢量图**可能给不出 image 字节（block["image"] 为空）→ 兜底：对含 type=1 但无字节、且页面积占比大的块，用 `page.get_pixmap(clip=block_bbox)` 渲染裁剪（实现时注意只兜底不主用）
- 风险 2：图片描述走多模态 AI 有耗时 → 描述生成放后台任务异步做（先落盘图片+占位 caption，描述好了再更新 FTS），不阻塞 MD 写入
- 风险 3：trigram 索引体积约为 unicode61 的 3-5 倍 → 当前文档量（百级）无压力；量级上来再评估
- 风险 4：MD 内嵌图引用会让"编辑保存"（storage.update）可能误伤图片行 → 18.3 实现时图片引用行加注释标记（HTML 注释 `<!-- img:... -->`）供 update 保护

---

---

## 阶段十九：集成 anydoc 替换 LibreOffice（用户提出于 2026-09-13 15:05）

### 背景与目标
用户要求调研 [firecrawl/anydoc](https://github.com/firecrawl/anydoc)（纯 Rust 文档→GFM Markdown 转换器，Firecrawl 出品），若效果优于现有 LibreOffice 相关链路，则**集成进项目替换 LibreOffice**：所有文件优先用 anydoc 转换，失败或需要 OCR 的文件再走多模态大模型；同时**去除**系统设置里"所有格式文档都使用 AI 提取 Markdown"开关。

### anydoc 研究结论（已浅克隆通读 + 实测）
- **形态**：Rust 库 + Node/Python/WASM 绑定；Python 包 `pip install firecrawl-anydoc`（单 wheel ~3.6MB，cp310-abi3-win_amd64 兼容 venv 的 Python 3.13）
- **API**：`anydoc.to_markdown(path) -> str`（GFM）；`to_markdown_bytes(data, fmt?)`；内容嗅探格式（PDF header/OLE stream/ZIP mimetype），CSV 需给扩展名
- **支持 14 格式**：`.doc/.docx/.docm/.ppt/.pps/.pot/.pptx/.pptm/.ppsx/.ppsm/.xls/.xlsx/.xlsm/.xlsb/.odt/.ods/.odp/.rtf/.epub/.csv/.pdf`
- **实测（真实业务文件）**：
  - `交换机统计0723.xls`（当年 LibreOffice 转 TXT 错位反复修的那个）→ **0.8ms**，6 列表格结构完整、中文站名/账号密码全对
  - `春暖花开燕自来.docx` → 1.0ms 全文段落正确
  - `润扬大桥设备资产清单.xlsx` → 13.2ms，22550 字符，机柜图表格+设备编号保留
- **官方基准**（LLM judge 盲评 482 对）：唯一覆盖全部 14 格式且每种格式得分最高的工具，比次快的工具快一个数量级（中位 <5ms/文档）
- **短板**：PDF 仅文本层提取（pdf-inspector），**扫描件不支持本地 OCR**（只支持 firecrawl 付费 hosted OCR，数据上云，不采用）→ 扫描件走我们自己的多模态 AI
- **结论：全面优于 LibreOffice 链路**（速度、质量、部署重量、Windows 中文文件名坑）。用户的"如果更好"条件满足 → 执行集成

### 现状 LibreOffice 使用点（grep 实测）
| 位置 | 用途 | 处置 |
|------|------|------|
| `extraction/xlsx_extractor.py:_extract_xls_legacy` | .xls → .xlsx（subprocess soffice，ASCII 文件名绕中文坑） | **替换为 anydoc**（anydoc 原生读 .xls，输出 MD） |
| `extraction/docx_extractor.py:49-56` | .doc → .docx（soffice 转 docx 再 python-docx） | **替换为 anydoc**（原生读 .doc） |
| `services/search_service.py` | 文档头注释 + 旧 `extract_file_content` 历史说明 | 更新注释（旧管线阶段四已删） |
| `document_formatter.py:232-241` | "LibreOffice处理" 标识判断（死逻辑残留） | 清理/更新 |
| `api/endpoints/search.py:351` | 注释"LibreOffice已经提供了良好的格式" | 更新注释 |

### 设计：引擎优先级链（新链路）
```
所有文件 → AnyDocExtractor（anydoc 优先）
  ├─ 成功且内容非空 → 直接用（engine=anydoc）
  └─ 失败/空内容 → 按格式降级：
       ├─ PDF → 多模态 AI（vision_parse，现有 _extract_with_unified_ai）→ 失败则 pymupdf 本地兜底
       ├─ 图片 → 多模态 AI（现有 ImageExtractor 不变）
       ├─ 其余 office/文本 → 现有本地引擎（openpyxl/python-docx/TextExtractor 安全网）
       └─ 本地也失败 → 报错（现状语义不变）
```
- **保留 openpyxl/python-docx 作安全网**（不删）：anydoc 成功则用 anydoc；边角格式回归时有兜底，符合"失败再走 AI/本地"的用户要求
- **去除 `AI_ALL_FORMATS_AI` 开关**：anydoc 输出已是高质量 GFM，无需"全格式 AI 规整"；router 的 `all_formats` 分支删除，`AI_FALLBACK_TO_LOCAL` 保留（AI 降级仍需要）
- PDF 文本型（非扫描）：anydoc 直接出文本层 MD（<5ms），比现在"整页渲染喂 VLM（几十秒）"快得多；**空内容**（扫描件）才走多模态 AI——正好满足"失败或需要 OCR 的走多模态"

### 非目标（本次不做）
- ❌ anydoc 的 firecrawl hosted OCR（付费+数据上云，用我们的多模态替代）
- ❌ 删除 openpyxl/python-docx 本地引擎（保留为安全网）
- ❌ 历史文档批量重提取（用户按需重传/重建）
- ❌ 前端其他 UI 改动（只删一个开关）

### 步骤 19.1 — 依赖与基础
- **做什么**：
  1. `backend/requirements-windows.txt` + `requirements.txt` 加 `firecrawl-anydoc>=0.2.4`
  2. 新文件 `backend/app/services/extraction/anydoc_extractor.py`：
     - `AnyDocExtractor(BaseExtractor)`：`can_handle` = 扩展名在 anydoc 14 格式表内（doc/docx/docm/ppt 系/xls 系/odt/ods/odp/rtf/epub/csv/pdf）
     - `extract(path)` → `anydoc.to_markdown(path)`（try/except 全部捕获，失败返回 `ExtractionResult(error=...)`，**不抛异常**）；空/极短（<20 字）也视为失败
     - `json_data`：`{format, engine:"anydoc", char_count}`
- **能改什么**：requirements 两文件、新增 anydoc_extractor.py
- **不能改什么**：现有任何 extractor
- **怎么验**：3 个业务文件（xls/docx/xlsx）转 MD 成功；造一个损坏文件（改 magic 字节）→ 返回 error 不抛
- **回退方案**：删新文件、revert requirements

### 步骤 19.2 — router 接入（anydoc 优先 + 降级）
- **做什么**：
  1. `router.py`：`_extractors` 列表**首位**插入 `AnyDocExtractor()`（优先级最高）
  2. `extract()` 重写分发逻辑：
     - 图片（png/jpg 等，非 anydoc 格式表内）→ 直接 ImageExtractor（现状不变）
     - anydoc 格式：先跑 AnyDocExtractor；成功 → 返回
     - anydoc 失败/空：
       - PDF → `PdfExtractor._extract_with_unified_ai`（多模态）→ 失败 pymupdf 本地
       - 其他 → 现有对应本地引擎（Xlsx/Docx/Text）→ 失败报错
  3. **删除** `AI_ALL_FORMATS_AI` 全格式 AI 规整分支（`all_formats` 判断 + `_refine_with_ai` 调用；`_refine_with_ai` 方法保留或删除均可，倾向删除）
- **能改什么**：`router.py`
- **不能改什么**：PdfExtractor/ImageExtractor 内部逻辑（复用不改）
- **怎么验**：xls→anydoc 直出（json_data.engine=anydoc，耗时 <1s）；损坏 xls→降级本地引擎（openpyxl 也读不了则报错）；PDF 文本型→anydoc 出文本；`AI_ALL_FORMATS_AI` 不再被读取
- **回退方案**：git checkout router.py

### 步骤 19.3 — 清理 LibreOffice 残留
- **做什么**：
  1. `xlsx_extractor.py:_extract_xls_legacy`：保留函数但**内部改走 anydoc**（或 router 已兜住，此函数仅作文档化 fallback；倾向：函数体改为调 anydoc，去掉 soffice subprocess 全部逻辑）
  2. `docx_extractor.py` .doc 分支：去掉 soffice 转 docx 逻辑（router 层 anydoc 已兜住；此分支保留"anydoc 不可用时报清晰错误"）
  3. `search_service.py` / `document_formatter.py` / `search.py` 的 LibreOffice 注释/死逻辑清理
- **能改什么**：上述 4 文件
- **不能改什么**：`_extract_xlsx`（openpyxl 主路径）/`_process_sheet` 等本地引擎核心
- **怎么验**：全仓 grep `soffice` → 仅剩文档说明；.xls/.doc 上传走新链路成功
- **回退方案**：git checkout 4 文件

### 步骤 19.4 — 去除"所有格式 AI 提取"开关
- **做什么**：
  1. `config.py`：删 `AI_ALL_FORMATS_AI` 字段（保留 `AI_SERVICE_ENABLED`/`AI_FALLBACK_TO_LOCAL`）
  2. `api/endpoints/extraction_config.py`：schema/PUT/GET 去掉 `ai_all_formats_ai` 字段（.env 清理列表保留该 key 的删除逻辑，清掉存量）
  3. `backend/.env`：删 `AI_ALL_FORMATS_AI=false` 行
  4. 前端 `extraction-config.ts`：接口去字段；`SettingsView.vue`：删开关 UI（line 67 附近）+ 初始值（line 572 附近）
- **能改什么**：上述 4 文件
- **不能改什么**：AI 服务配置的其他字段（url/model/provider/timeout 等）
- **怎么验**：GET extraction-config 不再返回该字段；设置页无此开关；vue-tsc 0 error；存量 .env 里的 key 被 PUT 后清掉
- **回退方案**：git checkout 4 文件

### 步骤 19.5 — 端到端验收
- **做什么**：
  1. 上传：`交换机统计0723.xls`（anydoc 直读）+ 1 个 docx + 1 个文本型 PDF（anydoc 文本层）→ 全部 engine=anydoc 成功
  2. 上传扫描件/图片类 → 走多模态 AI 成功
  3. 上传损坏文件 → 降级/报错语义正确
  4. 系统设置页确认开关已消失、AI 配置其他项正常
  5. `vue-tsc --noEmit` 0 error；后端重启后 `/health` 200
- **通过标准**：anydoc 优先链路全通；失败降级链路全通；开关无残留（代码+.env+前端）
- **回退方案**：N/A（验收不改代码）

### 实施顺序与风险
- 顺序：19.1 → 19.2 → 19.3 → 19.4 → 19.5
- 风险 1：anydoc 对某些**边角 xls/doc**（老格式/宏/加密）解析可能失败 → 已设计本地引擎安全网 + 报错语义不变
- 风险 2：anydoc 表格对**复杂合并单元格**的 GFM 表达与 openpyxl HTML 表格不同 → 前端 markdown-it 渲染 GFM 表格无问题；HTML 表格（colspan）场景 anydoc 输出为纯 GFM（可能丢失合并关系）→ 若业务发现台账类表格合并丢失，该格式可临时切回本地引擎（router 加白名单开关，本期不做）
- 风险 3：`AI_ALL_FORMATS_AI` 删除后，用户之前若开过该开关（.env=true）行为变化 → .env 当前为 false，无实际影响；PUT 会清掉该 key
- 风险 4：PDF 文本型从"VLM 整页识别"变为"anydoc 文本层" → 排版复杂的 PDF 文本层提取质量可能不如 VLM 渲染识别 → 空/短内容自动降级 VLM 兜住；用户如需强制 VLM 可后续加配置

---

## 阶段二十 — 智能搜索模块优化（2026-09-13，用户拍板方案 A）

> 目标：① 去掉搜索建议 + 高级搜索（用户点名）② 主搜索支持**多词联合搜索**（空格分隔多词，命中词数加权排序）。
> 关键事实（调研实测）：当前 43 篇/611KB，内存全量扫描 ~1.6ms，"不慢"但无多词能力。
> **本期不接 FTS5**：wiki FTS 索引仅覆盖 11/43 篇（33 篇未入索引），作主路会漏召回；当前规模无速度压力（4300 篇才 ~109ms）。FTS 接线留待文档量上千后再做（届时需先解决"新文档自动入 wiki 索引"）。
> 语义搜索（sqlite-vec + BGE-small-zh）列为后续候选，本期不做（需新增 embedding 模型部署）。

### 步骤 20.1 — 前端清理：删搜索建议 + 高级搜索
- **做什么**：
  1. `SearchView.vue` 模板：删"搜索建议"卡（原 L89-100）、"相关建议"卡（原 L102-115）、"高级搜索" n-collapse 面板（原 L30-70，4 项筛选：范围/类型/时间/排序）
  2. 删对应 script 状态与函数：`searchSuggestions`/`inputSuggestions`/`filters`/`documentTypes`/`sortOptions` 及 `handleInputChange`（实时建议 debounce 调用）、`loadSuggestions`（onMounted 里的建议拉取）
  3. 删 `handleSearch` 中 `filters.value.type` 拼 `docParams.doc_type` 的逻辑
- **能改什么**：`SearchView.vue`
- **不能改什么**：搜索结果列表/统计/预览/下载逻辑（阶段十六的下载入口在结果卡片上，不动）
- **怎么验**：`/search` 页无建议卡、无高级面板；搜索功能正常；vue-tsc 0 error
- **回退方案**：git checkout SearchView.vue

### 步骤 20.2 — 后端：删 suggestions 端点 + 多词联合搜索
- **做什么**：
  1. `search.py`：删 `/search/suggestions` 端点（L532-593）
  2. `/search/documents` 重构检索核心：
     - 新增 `tokenize_query(q)`：按空白/中英文标点切词，去重、去空、每词 ≤30 字符；单词时行为与现状一致（连续串匹配）
     - 单词查询：保持现有"整体串正则"语义（召回不降）
     - 多词查询：每词独立在 content/title/description 匹配；文档命中词数 = 各词命中计数；**命中词数多的排前**（同分再按现有 score）；结果附 `matched_terms` 与 `term_total`
     - 打分沿用现有权重（content 0.8+ / title 0.6+ / desc 0.4+），多词时按命中词数加权
  3. `search_service.py` 新增 `search_terms_in_text(text, terms) -> {term: [matches]}`（多词逐行匹配，一次遍历完成所有词，避免每词全文扫描）
- **能改什么**：`search.py`、`search_service.py`
- **不能改什么**：`/preview`、`/original` 端点；SearchLog 记录逻辑；`get_actual_file_path`
- **怎么验**：单文档 404；单词搜索召回与改造前一致（抽 4 个词对比）；多词"交换机 配置"→ 同时含两词排前、只含一词在后、都不含不出现；`matched_terms` 正确
- **回退方案**：git checkout search.py search_service.py

### 步骤 20.3 — 前端：多词结果展示
- **做什么**：
  1. `SearchView.vue` 结果卡片：多词查询时显示"命中 X/Y 个词"标签；高亮从单词改为**每个词都高亮**（预览高亮参数传主串不变，列表卡片内多词高亮前端自行处理）
  2. 搜索框 placeholder 提示多词用法（空格分隔）
- **能改什么**：`SearchView.vue`
- **不能改什么**：预览弹窗（DocumentView 逻辑不动）
- **怎么验**：多词搜索列表卡片显示命中词数标签 + 多词高亮；单词搜索外观与现状一致
- **回退方案**：git checkout SearchView.vue

### 步骤 20.4 — 端到端验收 + 记忆库同步
- **做什么**：
  1. E2E：`/search` 页单词/多词/无结果/中英文混合各测一次；确认建议卡与高级面板消失
  2. 性能：多词查询端到端 < 当前单词查询耗时（43 篇规模下）
  3. `vue-tsc --noEmit` 0 error；后端重启 `/health` 200
  4. 记忆库：`@architecture.md`（search.py 职责更新）、`@product-requirements-document.md`（F2 删"搜索建议/多维筛选"两行，加"多词联合搜索"）、`progress.md`、每日日志
- **通过标准**：清理无残留（前端 UI + 后端端点）；多词搜索可用且排序合理；召回不降；性能不降
- **回退方案**：N/A（验收不改代码）

### 实施顺序与风险
- 顺序：20.1 → 20.2 → 20.3 → 20.4 → 20.5
- 风险 1：多词语义变化（"交换机配置"单串 → 用户加空格变两词）→ 不加空格时行为 100% 不变，只有显式空格/标点才触发多词模式
- 风险 2：`/search/suggestions` 被其他前端位置引用 → 20.1 实施时全仓 grep 确认（已知仅 SearchView 两处）
- 风险 3：多词打分细节（命中词权重）主观 → 用"命中词数为主、score 为辅"的保守排序，不引入新算法

---

### 步骤 20.5 — 分词口径修正 + 预览编辑 + 多词分别导航（2026-09-14，用户追加三点）

> 用户反馈三点：① 分词只认空格（`172.16.8.106` 被拆成多词是 bug，应是 1 个 IP）② 搜索预览界面要能像文档管理一样直接编辑 md ③ 多词进入预览要高亮并自动跳转，且每个词可分别上下跳转。

#### 20.5.1 分词改为仅按空格
- **做什么**：`search.py` 的 `_TERM_SPLIT_RE` 由"空白+中英文标点"改为 `\s+`（仅空白），`tokenize_query` 注释同步
- **能改什么**：`search.py`（`_TERM_SPLIT_RE` + `tokenize_query` docstring）
- **不能改什么**：`search_terms_in_text`、打分、排序逻辑
- **怎么验**：`tokenize_query('172.16.8.106')==['172.16.8.106']`；`tokenize_query('交换机 配置')==['交换机','配置']`
- **回退方案**：git checkout search.py
- **状态**：✅ 完成（venv 单测通过）

#### 20.5.2 预览端点多词高亮（data-term）
- **做什么**：
  1. `search_service.py` 新增 `highlight_terms(text, terms)`：长词优先、大小写不敏感、重叠区间去重，每个命中注入 `<mark data-term="词">`（属性值 html.escape）
  2. `/search/preview` 端点：`highlight` 参数先 `tokenize_query`；单词走原 `highlight_text`（整体串），多词走 `highlight_terms`
- **能改什么**：`search_service.py`、`search.py`（仅 preview 高亮分支）
- **不能改什么**：`highlight_text`（DocumentView 仍在用）、格式化逻辑、查看统计
- **怎么验**：`highlight_terms('核心交换机配置...', ['核心交换机','配置'])` 长词不拆短词；IP 原样高亮；`/search/preview/{id}?highlight="a b"` 返回带 `data-term` 的 mark
- **回退方案**：git checkout search_service.py search.py
- **状态**：✅ 完成（venv 单测 + API 实测通过）

#### 20.5.3 SearchView 预览加编辑（与文档管理 W4 一致）
- **做什么**：
  1. `SearchView.vue` 预览工具栏加"编辑"按钮（`v-if="currentUser?.is_superuser && previewMode==='extracted'"`），图标 PencilOutline
  2. 编辑态：`<n-input type="textarea">` 替换预览内容区；上方"正在编辑 Markdown 副本"提示 + 取消/保存
  3. `togglePreviewEdit`→`wikiService.getMarkdown`；`savePreviewEdit`→`wikiService.saveMarkdown`（后端自动重建索引）→重新 `loadPreviewContent`
  4. `onMounted` 调 `authService.getCurrentUser()`；`previewDocument` 重置编辑态；切模式退出编辑
  5. 错误提示带 `e?.response?.data?.detail`（无 MD 副本时提示清晰）
- **能改什么**：`SearchView.vue`、`xss-protection.ts`（`ALLOWED_ATTR` 加 `data-term`/`data-highlight-index`/`data-highlight-term`）
- **不能改什么**：`wiki.py`（后端编辑端点已存在）、DocumentView 逻辑、下载入口
- **怎么验**：超管登录→搜索→预览→编辑按钮可见→点击出 textarea 加载 MD→取消恢复；非 MD 副本文档点编辑提示"加载 MD 副本失败"（不白屏）
- **回退方案**：git checkout SearchView.vue xss-protection.ts
- **状态**：✅ 完成（E2E：doc 71 编辑加载 46KB MD，取消正常恢复）

#### 20.5.4 多词分别导航
- **做什么**：
  1. `updatePreviewHighlightCount` 重写：给每个 `<mark>` 补 `data-highlight-term`（还原后端转义）+ 全局 `data-highlight-index` + 分词色 class（`hl-term-0..7`）
  2. `termGroups` 按查询词顺序分组 `{term,count,indexes}`；`termCursor` 每词独立光标
  3. 导航 UI：每词一张卡片（词名着色 + N处 + ↑↓ + n/N），点击切换导航目标（`activeNavTerm`）
  4. `scrollToHighlightInPreview(term, dir)` 按词内 indexes 跳转；进入预览自动跳第一词第 1 处
  5. 多词不同色（橙/蓝/绿…）；单词保持原黄色；CSS 加 `.hl-term-*` 与 `.term-nav-*` 样式
- **能改什么**：`SearchView.vue`
- **不能改什么**：后端返回结构、单词高亮外观
- **怎么验**：`收费网 华为`（doc 71，2/2 命中）→ 预览 208 处 mark 分两组（119+89）；两词各自 ↑↓ 独立、颜色不同、自动跳到第一词；E2E 截图核对
- **回退方案**：git checkout SearchView.vue
- **状态**：✅ 完成（E2E 全绿）

### 20.5 验收汇总（2026-09-14）
- E2E（系统 Chrome + 工作区 playwright-core，`/search`）：
  - 多词"收费网 华为"：navCards=2（119处/89处），边框橙/蓝，mark class hl-term-0×119 + hl-term-1×89，首词 ↓×2→3/119，次词 ↓→2/89，active 卡片=华为 ✅
  - 编辑按钮：超管可见 → textarea 加载 46382 字符 MD → 取消恢复 ✅
  - 单词"172.16.8.106"：`term_total=1`、`matched_terms=['172.16.8.106']`（不再拆词）✅
- `vue-tsc --noEmit`：SearchView.vue / xss-protection 改动 0 新增 error（EnhancedSearchView 等为存量错误，与本次无关）
- 后端 venv 单测：分词/重叠去重/大小写/IP 全过
- 遗留观察：部分老文档（如 doc 9）无 MD 副本，点编辑会提示"加载 MD 副本失败"——属数据问题，非功能 bug；如需全覆盖可后续跑 wiki 全量重建

#### 20.6 搜索预览改 Markdown 渲染（对齐文档管理）
- **背景**：搜索预览用 `<pre v-html>` 直接吐文本（等宽字体纯文本墙），文档管理预览是 markdown-it 渲染 + `.markdown-content` 样式。用户要求两者观感一致、功能不变
- **做什么**：
  1. `SearchView.vue` 模板：`<pre class="preview-content">` → `<div class="markdown-content" v-html="previewHtml">`
  2. 新增 `previewHtml` ref；`updatePreviewHighlightCount` 改为：先 `renderMarkdown(previewContent)`（markdown-it，html:true 透传后端 `<mark data-term>`），再在渲染后的 HTML 上补 `data-highlight-term`/`data-highlight-index`/`hl-term-N` class 并分组（mark 属性是纯 ASCII，不会被 markdown-it 转义）
  3. 滚动选择器 `.preview-content mark[...]` → `.markdown-content mark[...]`
  4. 样式：新增全局（`:global`）`.markdown-content` 完整规则（从 DocumentView 复制：标题/表格/列表/code/quote/mark/hl-term 八色）；删除旧的 `.preview-content` 样式
- **能改什么**：`SearchView.vue`（模板内容区 + script 高亮函数 + style）
- **不能改什么**：后端 preview 端点；编辑/下载/复制/原文件模式/导航卡片 UI；`markdown-renderer.ts`
- **怎么验**：E2E 打开 doc 71 预览 → 渲染出 h1/table（不再是 pre 文本墙）；多词导航 119/89 依旧；编辑按钮依旧；vue-tsc 0 新增 error
- **回退方案**：git checkout SearchView.vue

#### 20.7 修复下载原文件扩展名误识别（如 `2025.12` → `.12`）
- **背景**：下载"NVR总表-...2025.12"原文件时，保存下来的扩展名是 `.12`（标题末尾是日期 2025.12，真实文件是 .xlsx）
- **根因（双因素）**：
  1. 后端 `Content-Disposition: attachment; filename*=utf-8''...2025_12.xlsx` 是对的，但 `main.py` 的 CORSMiddleware **没设 `expose_headers`** → 跨域 fetch（前端 :5173 → 后端 :8002）读不到 `content-disposition` → 前端 `parseFilenameFromDisposition` 拿到 `null` → 回退用 **title**（`...2025.12`）→ 浏览器按 title 的 `.12` 存
  2. 前端 `parseFilenameFromDisposition` 正则 `/filename\*?=['"]?([^'"\r\n]*)['"]?/i` 解析 RFC 5987（`filename*=utf-8''...`）时只捕获到 `utf-8`（`''` 双撇号把值截断了），即使 header 可读也会存成名为 `utf-8` 的文件
- **做什么**：
  1. `main.py` CORSMiddleware 加 `expose_headers=["Content-Disposition", "Content-Length"]`
  2. `file-download.ts` 重写 `parseFilenameFromDisposition`：优先解析 RFC 5987 `filename*=charset''value`（取 `''` 之后的值 + decodeURIComponent），回退 `filename="..."` / `filename=...`；markdown 兜底逻辑保留
- **能改什么**：`backend/app/main.py`（CORS 块）、`frontend/src/utils/file-download.ts`
- **不能改什么**：下载端点逻辑（后端 filename 本就正确）、其他 CORS 字段
- **怎么验**：跨域请求响应头含 `access-control-expose-headers: Content-Disposition`；下载 doc 6 保存文件名为 `...2025_12.xlsx`（非 `.12`）；纯 ASCII 文件名/RFC5987 中文文件名均正确
- **回退方案**：git checkout main.py file-download.ts

#### 20.8 AI Wiki MCP 增加设备资产搜索工具
- **背景**：用户希望在 AI 工作台直接问"某设备地址/用户名/密码"或"某设备的全部信息"，MCP 现在只有文档/图片域工具（8 个），缺资产域
- **做什么**（仅 `mcp_server.py` 加 2 个工具，复用 `app.models.asset.Asset` + `SessionLocal`）：
  1. `search_assets(query, top_k=5, asset_type=None, network_location=None, status=None)`：对 name/hostname/ip_address/serial_number/device_model/manufacturer/service_name/application/department/location/datacenter/mac_address/tags/notes 做 `ilike %q%` 联合搜索（query 可空，空时仅按过滤条件列）；返回每条的**全部字段**（含 username/password——密码库内本就明文存储、导出端点也原样返回，口径一致）；datetime 转 `YYYY-MM-DD HH:MM:SS` 字符串；tags JSON 解析成 list
  2. `get_asset(asset_id)`：按 ID 取单台设备全部字段；不存在返回 `{"error": ...}`
  3. 工具 docstring 写明字段含义（ip_address=地址、username/password=账号密码），供 LLM 理解
- **状态**：✅ 完成（MCP 实测：tools/list 11 个；搜"堡垒机"返回 2 条含账号密码；get_asset(1) 39 字段；不存在 ID 返回 error；search_kb 回归正常）
- **能改什么**：`backend/app/services/wiki/mcp_server.py`（新增 2 个 tool + 模块级序列化辅助函数）
- **不能改什么**：现有 8 个工具、`crud/asset.py`、`assets.py` 端点、资产模型；不新增依赖
- **怎么验**：重启后端 → 调 `/mcp` 工具列表含 `search_assets`/`get_asset`（共 10 个）→ 用真实资产名/IP 查询，返回含 username/password 且字段齐全 → 不存在的 ID 返回 error → 原有 8 工具不受影响（search_kb 抽查）
- **回退方案**：git checkout mcp_server.py

#### 20.9 资产查询提速：搜索命中唯一直接返回全字段 + 新增 list_assets
- **背景**：用户反馈资产查询慢。实测拆解：SQL 查询仅 0.6ms（81 台），MCP 单轮 ~160ms；慢的 90% 在 LLM 每多一轮工具调用就多 2~5s 推理往返（"查名字→拿 ID→查详情"两轮）。治本 = 减少工具调用轮次
- **做什么**（仍只改 `mcp_server.py`）：
  1. `search_assets` 返回策略改为**按命中数自适应**：
     - 命中 1 台 → 直接返回**全字段 dict**（含 username/password），LLM 一轮即可答"XX 设备的地址/账号密码"
     - 命中 ≥2 台 → 返回 `{"total", "assets":[精简摘要(id/name/ip_address/hostname/asset_type/status/network_location)], "hint": 提示用 get_asset(id) 取详情}`，返回体小、LLM 处理快
     - 命中 0 台 → `{"total": 0, "assets": []}`
  2. 新增轻量工具 `list_assets(asset_type?, network_location?, status?, limit=200)`：返回全部匹配资产的精简三列+（id/name/ip/类型/状态），供"有哪些设备"类问题，一轮完成
  3. 模块 docstring 工具清单更新（11 → 12）
- **能改什么**：`backend/app/services/wiki/mcp_server.py`
- **不能改什么**：`get_asset`/`_asset_to_dict` 行为、现有文档/图片域工具、DB 结构（不加索引——81 台量级 0.6ms 无意义，资产到几千台再上 FTS5）
- **怎么验**：重启后端 → tools/list 12 个；`search_assets(收费网堡垒机)` 单台→直接全字段含密码；`search_assets(防火墙)` 多台→摘要列表+hint；`search_assets(不存在xyz)` → total 0；`list_assets()` 精简列表；`get_asset(57)` 不变；`search_kb` 回归
- **回退方案**：git checkout mcp_server.py
- **状态**：✅ 完成（MCP 实测 7 项全过：单台命中直接全字段含密码、多台摘要无密码+hint、0 命中、list_assets 81 台、get_asset 不变、search_kb 回归）

#### 20.10 里程碑体检：脚本修复 + Linux 脚本补齐 + 文档对齐
- **背景**：用户要求检查环境安装/运行/停止脚本是否可用、README 与 AI Wiki MCP 调用文档是否完整，修改后提交形成里程碑
- **盘点发现的问题**：
  1. `stop-services.bat` 按进程名杀**全机器**所有 python.exe/node.exe（会误杀 IDE 等无关进程）→ 改按端口 8002/5173 精确定位 PID
  2. `stop-services.bat` 末尾提示"Use start-simple.bat"——该文件不存在
  3. README/部署文档引用 `start-services.sh`/`stop-services.sh`（Linux），仓库里**不存在**（只有 .bat）
  4. `docs/AI-Wiki部署与使用指南.md` 仍写"6 个 tools"，实际 12 个（20.8/20.9 加了资产域）
  5. `docs/生产环境脚本说明.md` 整篇描述 `start-production*.bat/sh`、`stop-production.*`、`restart-services.sh`——**全部不存在**（幽灵文档）
  6. `docs/部署指南.md`/`版本升级指南.md`/`开发者文档.md` 同样引用幽灵脚本
- **做什么**：
  1. 重写 `stop-services.bat`：按端口（8002/5173）找 PID 精确停止 + 明确提示"不会动其他 Python/Node 进程"；实测验证
  2. 新增 `stop-services.sh`（Linux 对应版，端口定位，pgrep 兜底）
  3. 新增 `start-services.sh`（Linux 开发模式启动，与 .bat 行为对齐）
  4. 重写 `docs/AI-Wiki部署与使用指南.md` 的 tools 章节为 12 个（含资产域 search_assets/get_asset/list_assets 用法与返回格式说明、WorkBuddy 调用示例）
  5. 新增 `docs/AI-Wiki-MCP调用文档.md`：完整 12 工具参数/返回/示例/鉴权说明（调用方主文档）
  6. 重写 `docs/生产环境脚本说明.md`：只描述真实存在的 3 个脚本 + 端口定位停止原理 + 故障排除（删除幽灵脚本章节）
  7. 修 `README.md`（Linux 脚本说明、MCP 简介补资产工具）、`docs/部署指南.md`/`版本升级指南.md`/`开发者文档.md` 的幽灵脚本引用
  8. `docs/版本更新日志.md` 记里程碑
- **能改什么**：上述脚本 + 文档；不动后端/前端代码逻辑
- **不能改什么**：`install-complete.bat`/`start-services.bat` 核心逻辑（已实测可用，仅修 stop）；memory-bank 历史进度条目（历史不改写）
- **怎么验**：stop-services.bat 实测（停 8002+5173，IDE 进程不受影响，端口释放）→ 再启动恢复；sh 脚本 bash -n 语法检查；文档中不再出现幽灵脚本名（grep 验证）；MCP 文档 12 工具与 tools/list 实测一致
- **回退方案**：git checkout 涉及文件
- **状态**：✅ 完成（stop-services.bat 按端口重写 + 2 个 Linux 脚本补齐并 bash -n 通过；bat 端口取 PID 逻辑经 bash 等价命令验证——沙箱内 cmd 无法执行 bat 属环境限制，双击运行不受影响；docs/AI-Wiki-MCP调用文档.md 12 工具与线上 tools/list 一致；核心文档幽灵引用 grep 清零；6 个深度过时文档加时效横幅）
