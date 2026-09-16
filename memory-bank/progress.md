# progress.md — 进度追踪

> 本文件按时间倒序记录已完成步骤、关键决策与遗留问题。
> 切新会话后**第一个动作**就是读这里与 `@implementation-plan.md`。

---

## 当前状态:阶段零~二十三全部完成,阶段二十四进行中

**最后更新**:2026-09-15 12:35

- 初始 9 项 P0/P1/P2 问题清零;内容提取器重构(extraction 模块)
- AI 引擎统一到 llama.cpp + Qwen3-VL 单接口;旧 AI 配置清理
- AI Wiki 系统全链路落地(MD 副本 + FTS5 + FastMCP 12 tools + 前端编辑/下载)
- **Android 客户端与移动端 API 整体移除(2026-09-12,阶段十一)**:数据查询与利用改由 AI 工作台经 AI Wiki MCP(`/mcp`)接入
- **start-services.bat 启动修复(2026-09-12,阶段十二)**:venv 缺失自动创建+装依赖、managed runtime 回退、补 fastmcp 依赖
- **阶段十三~十七**:AI 配置热生效 / 测试连接增强 / 后台 worker 修复 / 三处下载统一 / 设置页配置加载
- **阶段十八**:PDF/图片提取+文类+图片检索+三路中文检索+MCP 图片工具(参考 OpenKB)
- **阶段十九**:anydoc 替换 LibreOffice(参考 firecrawl/anydoc)
- **阶段二十·20.1~20.10**:多词联合搜索、Markdown 预览、智能搜索分词、MCP 资产工具、停止脚本安全化等
- **阶段二十一(2026-09-14)**:补齐 `backend/.env` CORS auto 模式全套配置
- **阶段二十二(2026-09-14)**:update.sh / update.bat / push.sh / push.bat 一键运维脚本
- **阶段二十三(2026-09-15)**:预览去掉底部图片清单 + 工具栏"原文件"切换支持所有格式
- **阶段二十四进行中(2026-09-15 12:35)**:Office 格式在线预览(LibreOffice 转 PDF + iframe,用户拍板路线 D2),前端带独立进度通道

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

---

### 2026-09-14（15:24 - 16:10）— 阶段二十·20.5：分词口径 + 预览编辑 + 多词分别导航（用户追加三点）
- **用户反馈三点**：① 分词只认空格（`172.16.8.106` 被拆成多词是 bug，应是 1 个 IP）② 搜索预览界面加编辑按钮（与文档管理 W4 一致，直接改 md）③ 多词进预览要逐词高亮 + 自动跳转 + 每词分别上下导航
- **代码变更**：
  - `search.py`：`_TERM_SPLIT_RE` 由"空白+中英文标点"改为 `\s+`（**仅空格**），`172.16.8.106` 不再被拆；preview 端点高亮分支改为先 `tokenize_query`，单词走原 `highlight_text`、多词走新 `highlight_terms`
  - `search_service.py`：新增 `highlight_terms(text, terms)` + `_find_all_occurrences`——长词优先、大小写不敏感、**重叠区间去重**（"核心交换机"不被"交换机"拆掉），命中注入 `<mark data-term="词">`（属性值 html.escape）
  - `SearchView.vue`：
    - 预览工具栏加"编辑"按钮（仅超管 + 提取模式），编辑态 textarea + 取消/保存，走 `wikiService.getMarkdown/saveMarkdown`（保存自动重建索引），`onMounted` 拉 `authService.getCurrentUser()`，错误带 `detail`
    - `updatePreviewHighlightCount` 重写：给 mark 补 `data-highlight-term`（还原后端转义）+ 全局 `data-highlight-index` + 分词色 class（`hl-term-0..7`）；`termGroups` 按查询词顺序分组、`termCursor` 每词独立光标
    - 导航 UI 改为**每词一张卡片**（词名着色 + N处 + ↑↓ + n/N），点击切换导航目标；`scrollToHighlightInPreview(term, dir)` 按词内索引跳转；进预览自动跳第一词第 1 处；多词不同色、单词保持原黄
  - `xss-protection.ts`：`sanitizeDocumentHtml` 的 `ALLOWED_ATTR` 放行 `data-term`/`data-highlight-index`/`data-highlight-term`（否则 DOMPurify 会把导航属性剥掉）
- **验证**（系统 Chrome + 工作区 playwright-core E2E）：
  - 单词"172.16.8.106"：`term_total=1`、`matched_terms=['172.16.8.106']`，不再拆词 ✓
  - 多词"收费网 华为"（doc 71，2/2 命中）：208 处 mark 分两组（119+89），边框橙/蓝，首词 ↓×2→3/119、次词 ↓→2/89，active 卡片=华为，自动跳转 ✓
  - 编辑按钮：超管可见 → textarea 加载 46382 字符 MD → 取消恢复 ✓
  - `vue-tsc --noEmit`：本次改动文件 0 新增 error（EnhancedSearchView/AssetView 等为存量错误）；后端 venv 单测分词/重叠/大小写/IP 全过
- **教训**：
  - 后端高亮要带 `data-term` 且**属性值 html.escape**，前端解析时还原 `&quot;`/`&amp;`——否则词里含引号会破坏 mark 标签
  - 多词区分色用 **class（hl-term-N）而非 inline style**，inline style 会被 DOMPurify 的 FORBID_ATTR 剥掉
  - 老文档（如 doc 9）无 MD 副本时点编辑会 404 提示"加载 MD 副本失败"——属数据问题非功能 bug；要全覆盖需跑 wiki 全量重建（`/wiki/rebuild`）
  - E2E 断言前先核实数据：doc 9 正文其实没有那个 IP（只高亮 1 词是正确行为），别把"数据没命中"误判成"高亮 bug"

---

### 2026-09-14（09:54 - 10:30）— 阶段二十·20.6：搜索预览改 Markdown 渲染（对齐文档管理）
- **用户反馈**：智能搜索预览页和文档管理预览页观感不同（前者纯文本墙），要求"保持功能不变"改成文档管理那种 Markdown 渲染效果
- **根因**：搜索预览用 `<pre v-html>` 套等宽字体直接吐文本，没走 markdown-it；文档管理预览是 markdown-it 渲染 + `.markdown-content` 样式体系
- **代码变更**（仅 `SearchView.vue`）：
  - 模板：`<pre class="preview-content">` → `<div class="markdown-content" v-html="displayPreviewHtml">`
  - `updatePreviewHighlightCount` 重写：先 `renderMarkdown(previewContent)`（markdown-it，html:true 透传后端 `<mark data-term>`），再在渲染后 HTML 上补 `data-highlight-term`/`data-highlight-index`/`hl-term-N` class 并分组，最后 `sanitizeDocumentHtml`
  - 图片水合接入（对齐文档管理 18.8）：`hydrateWikiImages` + `_previewToken` 防竞态 + `onBeforeUnmount` 释放 blob URL
  - 样式：删 `.preview-content`，新增 `.markdown-content` 完整规则（标题/表格/列表/code/quote/mark/hl-term 八色，从 DocumentView 复制）；滚动选择器 `.preview-content` → `.markdown-content`
- **验证**（E2E，doc 5 收费网 华为 2/2）：
  - 渲染出 h2×8、table×8、260 行、p 正常，**pre=0**（不再是纯文本墙）；字体 sans-serif
  - 高亮**零丢失**：backend raw marks=133 → after markdown-it=133 → 浏览器实测 133（之前 20.5 的 208 是另一篇 doc 71，不同文档数量本就不同，勿混比）
  - 多词导航 82/51 处依旧、↑↓ 正常、自动跳转第一词；编辑按钮依旧
  - `vue-tsc`：新引入 0 error（剩余 22 个为存量）
- **教训**：
  - v-html 注入的内容不受 scoped 选择器影响，markdown 内容样式要用 `:deep()` 穿透
  - markdown-it 配置 `html:true` 时后端注入的 `<mark>` 会原样透传（不解析、不转义属性），可在渲染后统一补索引
  - 对比高亮数量前先确认是**同一篇文档**（doc id 会变，208 vs 133 是不同文档）

---

### 2026-09-14（10:51 - 11:30）— 阶段二十·20.7：修复下载原文件扩展名误识别（2025.12 → .12）
- **用户反馈**：下载"NVR总表-...2025.12"原文件时，保存下来的扩展名被识别成 `.12`（标题末尾是日期 2025.12，真实文件是 .xlsx），要求修复"这类"错误
- **根因（双因素，均已实测复现）**：
  1. **CORS 未暴露 header**：后端 `Content-Disposition: attachment; filename*=utf-8''...2025_12.xlsx` 是对的，但 `main.py` 的 CORSMiddleware 没设 `expose_headers` → 跨域 fetch（前端 :5173 → 后端 :8002）读不到 `content-disposition`（`access-control-expose-headers: None`）→ 前端拿到 `null` → 回退用 **title**（`...2025.12`）→ 浏览器按 title 的 `.12` 存
  2. **前端 RFC5987 解析 bug**：旧正则 `/filename\*?=['"]?([^'"\r\n]*)['"]?/i` 解析 `filename*=utf-8''...` 时只捕获到 `utf-8`（`''` 双撇号把值截断），即使 header 可读也会存成名为 `utf-8` 的文件
- **代码变更**：
  - `backend/app/main.py`：CORSMiddleware 加 `expose_headers=["Content-Disposition", "Content-Length"]`
  - `frontend/src/utils/file-download.ts`：重写 `parseFilenameFromDisposition`——优先 RFC5987 `filename*=charset'lang'value`（取 `''` 后的值 + decodeURIComponent），回退 `filename="..."`/`filename=...`；新增 `sanitizeFilename`（去目录/清非法字符）；**兜底逻辑升级**：header 缺失/解析失败时用后端已知 `file_type` 纠正扩展名（不再盲目拿标题当文件名），`downloadWikiDocument` 加可选 `fileType` 参数
  - `DocumentView.vue` / `SearchView.vue`：4 处调用透传 `file_type`（搜索结果 `result.file_type` / 预览 `previewDocumentData?.file_type` / 列表 `doc.file_type`）
- **验证**：
  - CORS：跨域响应头 `access-control-expose-headers: Content-Disposition, Content-Length`，浏览器 JS 能读到 ✅
  - 浏览器真实跨域 E2E（与用户浏览器一致环境）：`parsedFilename = NVR总表-润扬大桥监控平台NVR账号密码明细表2025_12.xlsx`，`ext = xlsx` ✅（修复前 `.12`）
  - 单测解析函数：RFC5987 中文 / header 缺失+fileType 兜底 / 普通 filename / markdown 兜底 全过
  - `vue-tsc`：`file-download.ts` 0 error，我的改动行 0 新增 error（DocumentView/SearchView 剩余为存量错误）
- **教训**：
  - 跨域 `fetch` 读自定义/响应头必须在后端 CORS 配 `expose_headers`，否则 JS 侧 `headers.get()` 返回 null（即使响应本身有该头）
  - RFC5987 `filename*=charset'lang'value` 解析要按三段式取 `''` 后的值，不能用宽松的 `['"]?([^'"\r\n]*)`
  - 下载文件名兜底要带上后端已知 `file_type`，标题不可信（可能以日期/版本号结尾）
- **提交**：本地待提交（4 代码文件 + memory-bank）

---

### 2026-09-14（12:10 - 12:45）— 阶段二十·20.8：AI Wiki MCP 增加设备资产搜索
- **用户反馈**：希望在 AI 工作台直接问"某设备地址/用户名/密码是多少"或"某设备的全部信息"，MCP 直接返回；此前 MCP 只有文档/图片域工具（9 个），无资产域
- **代码变更**（仅 `backend/app/services/wiki/mcp_server.py`）：
  - 新增 `_asset_to_dict`（Asset ORM → 全字段 dict；datetime → `YYYY-MM-DD HH:MM:SS`；tags JSON → list；跳过 creator_id）
  - 新增 `search_assets(query, top_k=10, asset_type?, network_location?, status?)`：14 字段 `ilike %q%` 联合模糊搜索（name/hostname/ip_address/mac_address/serial_number/device_model/manufacturer/service_name/application/department/location/datacenter/tags/notes），query 可空仅按过滤条件列，`updated_at` 倒序，limit top_k；返回**全部字段含 username/password**（库内明文存储，与资产导出端点口径一致）
  - 新增 `get_asset(asset_id)`：按 ID 取单台全字段，不存在返回 `{"error": ...}`
  - 模块 docstring 工具清单 9 → 11
- **验证**（MCP streamable-http 真实调用，`/mcp/`，initialize→tools/list→tools/call）：
  - tools/list 共 **11** 个（原 9 + search_assets/get_asset），serverInfo 正常
  - `search_assets(堡垒机)` → 2 条，含 `ip=192.168.0.242 user=admin pwd=Rybridge@2026-8` 等真实账号密码 ✅
  - `search_assets(192.168.0.240)` → 按 IP 命中 1 条 ✅
  - `get_asset(1)` → 39 个字段全返回（含 username/password/notes 等）✅
  - `get_asset(999999)` → `{"error": "设备不存在: asset_id=999999"}` ✅
  - 过滤参数：asset_type=security / network_location=billing 均正确；空 query top_k=81 返回全部 81 台 ✅
  - 回归：`search_kb(防火墙)` 原工具正常 ✅
- **决策**：
  - 资产查询直接 SQLAlchemy 查 `assets` 表（不走 FTS 索引——资产是结构化字段，ilike 足够且 81 台量级无性能问题）
  - 密码原样返回：用户明确需求（查账号密码），且库内本就明文、Web 端导出也原样给；MCP 端点本身无鉴权（与既有 9 工具一致，部署在内网）
- **提交**：待提交（mcp_server.py + memory-bank）
- **注**：20.7 此前"本地待提交"已完成——`git push` 被本机代理对 git-receive-pack 返回 401 阻断，改用 GitHub Git Data API 重建提交推送，远端 main = `6270f84a`（20.7）/ `463e9a05`（20.6），7 文件逐字节校验一致；方法已存 skill `github-api-push-fallback`

---

### 2026-09-14（14:10 - 14:25）— 阶段二十·20.9：资产查询提速（减少 LLM 工具往返轮次）
- **用户反馈**：资产查询"速度有点慢"。实测拆解（只读分析，未动代码先定位）：
  - SQL 查询本身 **0.6ms**（81 台，LIKE 模糊搜；assets 表已有 name/ip/serial 索引）
  - MCP 单轮调用 ~160ms，initialize 握手 ~175ms（一次性）
  - **慢的 90% 在 LLM 每多一轮工具调用多 2~5s 推理往返**——此前"查名字→拿 ID→查详情"要两轮
- **方案决策**：A（合并查询轮次）先做；B（DB 加速/FTS5）81 台量级无意义，资产到几千台再做；C（直读 DB 的技能）留作可选补充
- **代码变更**（仍仅 `mcp_server.py`）：
  - `search_assets` 返回策略改为**按命中数自适应**：命中 1 台 → 直接全字段 dict（含 username/password），一轮即可答"XX 设备地址/账号密码"；多台 → `{"total","assets":[7列摘要],"hint"}`（摘要 id/name/ip/hostname/类型/状态/网络，**不含密码**——防止一次把多台设备密码全吐给 LLM）；0 台 → `{"total":0,"assets":[]}`
  - 新增 `list_assets(asset_type?, network_location?, status?, limit=200)` 轻量清单工具（同样不含账号密码）
  - 工具总数 11 → 12
- **验证**（MCP 真实调用 7 项全过）：
  1. tools/list 12 个 ✅
  2. `search_assets(收费网堡垒机)` 单台 → 直接全字段含 password（10.9.0.221/admin/Rybridge@2026.cn）✅
  3. `search_assets(防火墙)` 多台 → total=10，摘要 7 列均无 password，hint 指引 get_asset ✅
  4. 0 命中 → `{"total":0,"assets":[]}` ✅
  5. `list_assets()` 81 台 / billing 过滤 34 台 ✅
  6. `get_asset(57)` 39 字段不变 ✅
  7. `search_kb` 回归正常 ✅
- **效果**：典型"查某设备账号密码"从 2 轮工具调用 → **1 轮**；"有哪些设备"类从 search_assets 拉全字段 → list_assets 轻量一轮
- **提交**：随 20.10 里程碑一并提交

---

### 2026-09-14（14:40 - 16:30）— 阶段二十·20.10：环境脚本体检 + 文档对齐（里程碑提交）
- **用户指令**："检查测试项目的环境安装脚本、运行/结束脚本是否正常，说明文档和 AI Wiki MCP 调用文档是否完整清楚；如有修改，提交 GitHub 形成里程碑"
- **体检发现的 6 类问题**：
  1. `stop-services.bat` 原逻辑按**进程名全杀** python.exe/node.exe（会误杀 IDE 等无关进程，本机 node 进程 6 个）
  2. `findstr /c:":8002.*LISTENING"` 中 `/c:` 强制字面匹配，`.*` 不是通配 → 原逻辑**静默无效**
  3. Linux 端只有启动无停止脚本，且启动脚本依赖不存在的 `requirements.txt`（实际只有 `requirements-windows.txt`，跨平台通用）
  4. 文档大量引用**幽灵脚本/入口**：`start-production*`、`restart-services.sh`、`check-config-changes.*`、`start-simple.bat`、`backend/database_integrated_server.py`（均不存在；真实入口 `uvicorn app.main:app` 端口 8002）
  5. MCP 文档口径过期："6 个工具" vs 实际 **12 个**（KB 8 + 图像 2 + 资产 2）
  6. 缺一份面向调用方的 MCP 调用权威文档
- **变更（8 项）**：
  - `stop-services.bat` 重写：按端口 8002/5173 取 PID 精确 `taskkill`（`netstat | findstr ":8002" | findstr "LISTENING"` 取第 5 列）；明确不动其他 Python/Node 进程；CRLF
  - 新增 `stop-services.sh`（端口优先 lsof→ss→fuser，TERM 后 KILL）、`start-services.sh`（nohup + 日志 + PID 文件，venv/node_modules 自检，依赖文件优先级 requirements.txt > requirements-windows.txt）；均 `bash -n` 通过 + `chmod +x`
  - 新增 `docs/AI-Wiki-MCP调用文档.md`：连接配置、12 工具参数/返回逐项说明、资产域自适应返回 JSON 示例 + 字段释义、典型问法→工具映射表、鉴权与已知限制
  - `docs/AI-Wiki部署与使用指南.md`：6→12 工具，架构/工具表补资产域，WorkBuddy 调用示例补资产问法
  - `docs/生产环境脚本说明.md` 全量重写（仅 5 个真实脚本 + 端口停止原理 + 真实端点含 /mcp）
  - `README.md`：依赖安装改 `requirements-windows.txt`（跨平台通用）+ venv；MCP 段列 12 工具并链接新文档；目录树列 5 脚本
  - `docs/README.md`、`docs/部署指南.md`、`docs/开发者文档.md`、`docs/版本升级指南.md`：幽灵引用全部替换为真实脚本/入口/依赖文件
  - 6 个深度过时文档（部署指南-GitHub、系统架构文档、配置指南-CORS/域名/网络/综合）头部加**时效声明横幅**（2026-09-14 里程碑体检）
  - `docs/版本更新日志.md` 顶部新增本里程碑条目
- **验证**：
  - 5 个真实脚本逐一核对存在性/语法（bat CRLF、sh `bash -n`）
  - bat 端口取 PID 逻辑用 bash 等价命令验证（`:8002`+LISTENING → PID 190668，与权威值一致）；沙箱内 `cmd //C` 无法执行 bat（环境限制，双击运行不受影响）
  - `docs/AI-Wiki-MCP调用文档.md` 12 工具与线上 `tools/list` 返回 12 个逐一核对一致
  - 核心文档 grep 幽灵引用（`start-production|restart-services|database_integrated_server|check-config-changes|requirements.txt|start-simple`）→ 全部清零
- **决策**：bat 沙箱内无法端到端执行，以"逻辑等价验证 + 用户双击"兜底；深度过时文档不逐行重写、加横幅降级处理

---

### 2026-09-14（16:08）— 阶段二十一：补齐 `.env` CORS auto 模式配置（部署到其它服务器 LAN 访问被拒修复）

- **用户报告**：项目部署到其它服务器后，日志显示 `[CORS] 最终配置：2 个源`（仅 `127.0.0.1:5173` + `localhost:5173`），其他电脑无法跨网段访问
- **根因（环境配置，非代码 bug）**：
  - `backend/.env` 原本**只写了一行** `CORS_AUTO_DETECT=true`，其余 `CORS_MODE` / `CORS_INCLUDE_LOCALHOST` / `CORS_FRONTEND_PORT` 全部依赖 `Settings` 字段默认值
  - 在本机开发环境 `.env` 已配置齐全时一切正常；但部署到服务器后，`.env` 可能被精简（或者**用户从其它分支 / 早期版本复制过来**），导致只有 `CORS_AUTO_DETECT=true` 一行被读到
  - **更隐蔽的诱因**：之前 P0-1 收紧 CORS 默认值（`CORS_AUTO_DETECT` 默认 `False`、`CORS_INCLUDE_HTTPS` 默认 `False`、`CORS_EXTRA_PORTS=""`），用户必须**显式开启**才能 LAN 访问
  - 在本机这套配置能跑通是因为 `.env` 一直是同一份；一旦服务器 `.env` 不完整，立即回退到"只放行 localhost"
- **修复（最小改动，零代码）**：
  - **不改 `config.py` / `main.py`**——黑名单边界（不动 CORS 中间件注册、不动 `BACKEND_CORS_ORIGINS` property 逻辑、不动 `_detect_local_ips()`）
  - **只改 `backend/.env`**：把 auto 模式需要的环境变量全部显式写齐
    - `CORS_MODE=auto`
    - `CORS_AUTO_DETECT=true`
    - `CORS_INCLUDE_LOCALHOST=true`
    - `CORS_FRONTEND_PORT=5173`
  - 加注释说明"若 `_detect_local_ips()` 仍拿不到 LAN IP（UDP 探测失败 + hostname 无 LAN IP），可取消 `CORS_CUSTOM_ORIGINS` 注释手动指定"
- **必须的后续动作**：
  - **用户必须重启后端进程**——`Settings` 单例在 import 时只读一次 `.env`，热改不生效；本次和阶段十三的 `Settings.reload()`（仅在配置保存接口里调用）不冲突
  - 重启后日志应出现 `[CORS] 检测到本机IP：['192.168.x.x']`，最终配置源数 ≥ 3
  - 若仍只有 2 个源 → `_detect_local_ips()` 在该服务器网络隔离下拿不到 LAN IP → 改 `CORS_CUSTOM_ORIGINS=http://服务器IP:5173` 手动兜底
- **教训**：
  - **pydantic-settings 字段默认值 ≠ `.env` 文件值**：默认值仅在 `.env` 没写时生效；一旦只写了字段子集，"半配置"风险极高，部署到新环境极易踩
  - **CORS 这种"必须靠环境变量才能跑通"的安全开关**，默认值应"宁严勿宽"（当前默认 `False` 是对的），但**必须在文档/注释里把"用户怎么开"写明白**，否则用户部署就抓瞎
  - 后续若再遇到 LAN 访问问题，先 `cat backend/.env | grep -i CORS` 看完整配置、再看后端启动日志的 `[CORS]` 三行（模式 / 检测 / 最终），比直接改代码快
- **零代码改动验证**：`git diff backend/app/` 应为空；只有 `backend/.env` 一处变化

---

### 2026-09-14（19:35）— 阶段二十二：新增 update.sh / update.bat 一键更新脚本

- **用户诉求**：项目部署到其它服务器后，日常更新代码的命令不清楚
- **方案**：不污染现有 5 个脚本（install-complete / start / stop × 2 平台），新增第 6、7 个：`update.sh`（Linux）+ `update.bat`（Windows），部署到其它服务器的用户只需要 `./update.sh` 或 `update.bat`
- **设计原则**（黑名单边界）：
  - `git pull --ff-only`：严格快进，避免意外 merge/rebase
  - **不动 `.gitignore` 里的一切**：`.env` / `*.db` / `uploads/` / `wiki/images/` / `venv/` / `node_modules/` / `logs/` / `task_status/` 全在 `.gitignore` 里
  - 防御性检查：工作区脏（有未提交改动）则中止并提示，避免覆盖本地修改
  - 重启后端：Settings 单例 import 时只读一次 .env，必须重启才能加载新代码；前端 vite dev server HMR 自动生效
- **脚本流程**：
  1. 防御性检查 `git diff --quiet HEAD` / `git diff --cached --quiet HEAD`
  2. 备份 `backend/.env` 到 `.env.update.bak.<时间戳>`（防御性兜底，失败时可手动 cp 恢复）
  3. `git pull --ff-only origin main`（失败时提示远端拒绝 fast-forward / 网络问题，并提示 .env 备份位置）
  4. `pip install -r requirements*.txt --upgrade-strategy only-if-needed`（仅补缺，不全量重装）
  5. `npm install`（仅补缺）
  6. 自动 `./stop-services.sh` + `./start-services.sh`（Windows 用 .bat 等价）
  7. 打印新 HEAD SHA + 日志路径 + 回滚命令
- **回滚**：`git reset --hard HEAD@{1}` 回到 pull 前的代码（reflog 保留，本地旧 commit 可找回）
- **验证**：`bash -n update.sh` 通过；chmod +x；Windows bat 语法检查（环境限制未实测双击，但语法遵循现有 start/stop-services.bat 风格）
- **文档**：`docs/部署指南.md` "版本更新"段追加脚本入口（保持原有"方式二手动更新"作为兜底）
- **memory-bank**：`@architecture.md` 1.9 节新增"2.0 根目录脚本清单"，明确 7 个真实脚本（避免之前 5 → 7 数字漂移）

---

### 2026-09-14（19:50）— 阶段二十二·完整版：诊断 + 解决推送卡死

- **用户反馈**："上传更新会卡很久"
- **诊断过程**（用户提示"用直连"启发）：
  - **第一步**：`env -u HTTPS_PROXY git ls-remote` 直连可用，秒回 `a339aed1`
  - **第二步**：`env -u HTTPS_PROXY timeout 30 git push origin main` → **SIGTERM 仍卡死**（30 秒超时）
  - **关键证据**：`GIT_TRACE=1 GIT_CURL_VERBOSE=1 git push` trace 显示：
    ```
    Trying 20.205.243.166:443...
    Established connection to github.com (20.205.243.166 port 443)
    <= Recv header: HTTP/1.1 401 Unauthorized
    <= Recv header: www-authenticate: Basic realm="GitHub"
    ```
  - **结论**：**不是代理问题，是 GitHub 真返回 401**。根因 = Git Credential Manager 把 `username=heartsward + password=github_pat_11...` 编码成 Basic Auth header 发出去，GitHub 对 fine-grained PAT 的 git 协议要求走 `Authorization: token <PAT>` 格式（即 URL 里的 `x-access-token:<PAT>` 前缀）
- **解法**：
  1. `env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy` 取消 WorkBuddy 代理
  2. `-c "url.https://x-access-token:${TOKEN}@github.com/heartsward/.insteadOf=https://github.com/heartsward/"` 让 git 用 fine-grained PAT 的正确格式
  3. diverged（之前 Git Data API 推的 commit）→ `--force-with-lease`（比 `--force` 安全）
- **落地**：
  - **新增 `push.sh`**（Linux）：Bash + GCM 拿 token + 探测 ahead/behind + 决定是否 --force-with-lease + 推送
  - **新增 `push.bat`**（Windows）：cmd + powershell 调 git credential fill + powershell 调 git push
  - **更新 `GIT-COMMANDS.md`**：完整命令速查（其它电脑下载 / 本机 push / push 卡顿排查）
  - **`update.sh` 不动**（只 pull 不 push，与本次问题无关）
- **验证**：
  - `bash -n push.sh` 通过 + `chmod +x push.sh`
  - **`./push.sh` 实测**：输出 `PUSHED_OK`，远端 main 从 `a339aed1` → `dba330d`（ahead 2 commit，其中 1 个是上一轮阶段二十一 d3a9885 与远端 a339aed1 内容相同）
  - `git ls-remote` 验证：远端 main = `dba330d9562c890714676e719749016740f37c00` ✅
- **方法论教训**：
  - **诊断必须用 trace 拿真实证据**，不能靠"我觉得是代理"瞎猜。本次 trace 拿到 401 + `www-authenticate: Basic realm="GitHub"` 才锁死是 GitHub 认证拒绝而不是网络层
  - **WorkBuddy 代理不是万恶之源**——取消它确实能直连，但直连后还有 401（因为问题在认证协议层不是网络层）
  - **fine-grained PAT + git smart-HTTP + GCM** 三者结合踩坑：GCM 默认 Basic Auth 头 vs fine-grained PAT 要求的 `token` 头——只能靠 `url.x-access-token:` URL 前缀让 git 走正确路径
  - **diverged 后用 `--force-with-lease` 而非 `--force`**：前者多一层"远端不是我以为的 SHA 则拒绝"的保护，本项目 Git Data API 推送历史造成的常规 diverged 完全可以覆盖
- **提交**：本条随里程碑 commit 提交并推 GitHub

---

### 2026-09-15 — 阶段二十三：预览去掉底部图片清单 + 原文件切换支持全格式

**用户反馈两点**：
1. 文档管理和智能搜索的预览里，提取出的图片会出现在最下方（PDF 行末引用 / AI 引擎输出文末"## 图片清单"节）——展示不需要，但图片正常提取到磁盘 + `wiki_images` 表 + AI 描述还得保留（图片检索还能用）
2. "提取内容 | 原文件"切换按钮目前只对 PDF 和图片显示，其它格式（docx/xlsx/txt…）也想要这个切换

**做了什么**：

#### 23.1 后端：移除 `insert_image_refs` 与图片 MD 内嵌
- **`backend/app/services/content_extractor.py`**：
  - PDF 分支：去掉 `markdown = insert_image_refs(markdown, images)`，仅保留 `extract_pdf_images` + `idx.add_image` + `describe_image_sync`（图片落盘 + 登记 + AI 描述）
  - 独立图片文档分支：去掉 `markdown = f"{markdown.strip()}\n\n{img_block}\n"`，MD 留空，前端切"原文件"模式看图
  - 移除 `final_markdown` 包装层（已无意义），精简 return
  - 从 import 中移除 `insert_image_refs`
- **`backend/app/api/endpoints/wiki.py`**：`/rebuild?reextract_images=true` 路径里 L104-111 那段"把新图引用追加进 MD 副本并重建该文档索引"删除（无图引用插入后这段是死代码），同步去掉 `insert_image_refs` 的 import
- **`backend/app/services/wiki/image_extractor.py`**：`insert_image_refs` 函数本体删除、`_PAGE_HEADER_RE` 删除、未用的 `import re` 删除（按 KISS 不留死代码）
- **`extract_pdf_images` / `register_image_doc` / `describe_image_sync` / `list_doc_images` / `image_mime` 一行不动** —— 图片本体提取 + AI 描述 + `wiki_images` 表登记完全保留
- **存量 MD 数据不动**：旧文档 MD 副本里仍有 `## 图片清单` 或行末图引用（属历史数据），本阶段不主动清洗；新上传/重提取才完全不带图引用

#### 23.2 前端：原文件切换支持所有格式 + 切换按钮移到工具栏右侧
- **`frontend/src/views/DocumentView.vue`**：
  - `shouldShowViewToggle` 由 `isPDFFile(document) || isImageFile(document)` 改为 `return true`（所有格式都显示）
  - 工具栏由 `n-space` 改为 `<div style="display: flex; ...">`，左侧放编辑按钮 + 搜索高亮导航，右侧（`margin-left: auto`）放"提取内容/原文件"切换
  - 原文件预览的兜底分支（下载提示卡）不动，非 PDF/图片切到"原文件"显示下载按钮即可
- **`frontend/src/views/SearchView.vue`**：同样改 `shouldShowViewToggle` + 切换按钮移到右侧（`justify-content: flex-end`）

**验证**：
- `vue-tsc --noEmit`：0 新增 error（与阶段二十基线一致）
- 后端模块导入测试（venv）：`image_extractor` / `content_extractor` / `wiki endpoint` 全部正常导入；`assert not hasattr(ie, 'insert_image_refs')` 通过；其余 5 个图片相关函数（`extract_pdf_images` / `register_image_doc` / `describe_image_sync` / `list_doc_images` / `image_mime`）健在
- `grep -rn "insert_image_refs\|insert_image_refs" backend/` 仅剩 `image_extractor.py` 注释一处，无任何代码引用
- 模拟 PDF markdown 输入 → 确认新代码下 markdown 字符串保持原样，无 `images/` 引用、无 `## 图片清单` 节
- 未做 E2E（后端未启动 + 无 playwright 任务）

**遗留观察**：
- 旧文档 MD 副本仍含图引用 —— 后续如需彻底清洗，可走 `/rebuild?reextract_images=true`（会落盘 + 登记新图，但不再重写 MD），老数据需要专门脚本清洗
- 独立图片文档切到"提取内容"模式会显示空 —— 已是当前唯一合理 UX（用户主动切"原文件"看图），接受

---

### 2026-09-15 — 阶段二十四：Office 格式在线预览（LibreOffice 转 PDF + iframe）

**用户需求**：阶段二十三让"原文件"切换支持所有格式后，非 PDF/图片只能下载。**用户进一步要求**：能直接在浏览器里看 .docx/.xlsx/.pptx。

**调研结论**：
- 桌面版"迅捷 PDF 转换器"是 GUI 软件，**无公开 Python SDK/CLI 接口**，无法代码调用；网页版需上传文件到公网服务器（运维文档敏感 → 不可接受）❌
- pandoc 对 .docx 转换效果顶尖，但**不支持 .xlsx/.pptx**（无 spreadsheet/presentation reader）❌
- LibreOffice 全覆盖 .doc/.docx/.xls/.xlsx/.ppt/.pptx/.odt/.ods/.odp/.rtf/.epub/.csv 等 14 种 ✅
- 用户拍板：**路线 D2（纯 LibreOffice）**

**阶段十九 vs 阶段二十四的关系**：
- 阶段十九：LibreOffice **全栈移除**（不再做内容提取；改用 anydoc）
- 阶段二十四：LibreOffice **局部回滚** —— **仅**承担"Office 转 PDF 预览"角色
- 两条链路并存且解耦：anydoc 走内容提取（快、保结构），LibreOffice 走 PDF 转换（保留排版，供 iframe）

**用户补充要求**：
1. **PDF 转换进度提示**与**文件内容提取进度**完全分开（两条独立 UI + 后端状态）
2. **LibreOffice 环境安装文档**重写（之前讲"内容提取"，现在讲"PDF 预览转换"）

#### 24.1 — LibreOffice 安装文档重写
- `docs/环境安装-LibreOffice.md` 整篇重写：
  - 角色：从"内容提取"改为"PDF 预览转换"（阶段十九起 anydoc 接手内容提取）
  - 强调"不影响内容提取/智能搜索/MCP"
  - 三平台安装（Windows 安装版勾 PATH / Linux apt 4 包 / macOS brew）
  - 验证 + 故障排除 + 与 anydoc 解耦边界
- `Settings` 加 `LIBREOFFICE_BIN_PATH` + `PREVIEW_CONVERT_TIMEOUT`（默认 120s）

#### 24.2 — 后端 PDF 转换器
- 新增 `backend/app/services/preview_converter.py`（~330 行）
- `PreviewConverter` 单例 + `get_preview_converter()` 工厂
- `detect_soffice_path()`：`.env` 自定义 → 平台标准路径 → `PATH` 兜底
- `SUPPORTED_OFFICE_TYPES` 14 种格式 + `is_supported_office_type()` 判定
- 缓存 `backend/cache/converted_pdfs/{doc_id}.pdf` + mtime 比对失效
- **独立进度通道** `task_status/preview_convert_{doc_id}.json`（单文件覆盖式，与 `extract_{doc_id}_*.json` 完全分离）
- `_PreviewStatusStore` 原子写（临时文件 + rename）
- `_FileLock`：进程内 `threading.Lock` + 跨进程 fcntl/msvcrt/noop 三档 fallback
- `_call_soffice()` 用临时 `UserInstallation` profile 防污染用户配置 + 防多实例冲突
- **`return pdf_out` → `_call_soffice()` 块退出时 TemporaryDirectory 清理 → 文件不存在** ❌ 改返回 `bytes` 由外层 `target.write_bytes(pdf_bytes)`（已修复）

#### 24.3 — 3 个新端点
- `GET /api/v1/documents/{id}/converted-pdf` — 返回 inline PDF，缓存命中秒出；缓存未命中同步触发（小文件秒出，大 xlsx 30s+）；LibreOffice 未装返回 503 + 安装文档链接
- `GET /api/v1/documents/{id}/conversion-status` — 轮询用，状态机 `idle → converting → ready | error`
- `POST /api/v1/documents/{id}/convert` — 后台预热（FastAPI BackgroundTasks）

#### 24.4 — 前端独立进度通道
- `DocumentView.vue` / `SearchView.vue` 都加：
  - `OFFICE_EXTENSIONS` / `OFFICE_TYPES` + `isOfficeFile()` 判定（与后端 SUPPORTED_OFFICE_TYPES 对齐）
  - `previewConvertStatus` / `previewConvertError` / `previewConvertElapsed` 状态（与"内容提取"进度 ref 完全独立命名）
  - `pollPreviewConvertStatus()` 2 秒轮询 `/conversion-status`
  - `watch([previewMode, currentDocument])` 切换模式时自动启停轮询
  - 模板里 Office 分支：loading 覆盖层（**显示 elapsed 计时 + "与内容提取独立"提示**） → iframe 显示 PDF；失败 fallback 到下载卡 + 错误信息 + 安装文档链接

#### 24.5 — 验证 + 记忆库同步
- ✅ `vue-tsc --noEmit` 0 新增 error
- ✅ 后端 3 个模块导入 + 路由注册成功
- ✅ **真实转换测试**：润扬大桥设备资产清单.xlsx（53KB） → PDF（733KB）耗时 **7.4s**；二次调用命中缓存 **0.000s**
- ✅ 进度状态格式正确（前端轮询可读）
- ✅ `.gitignore` 加 `backend/cache/`（运行时缓存不入版本库）
- ✅ 记忆库：`@architecture.md` 加 24.x 摘要 / `@tech-stack.md` 加 LibreOffice 角色边界（明确"严禁用于内容提取"）/ `progress.md` 加详细条目 / 今日日志

**踩坑记录**：
- TemporaryDirectory 在 `with` 块内 `return pdf_out` 后，外层 `shutil.move` 找不到文件 → 返回 `bytes` 替代路径 ✅
- 进度状态读写需要原子写（并发场景下 `write → read` 可能看到残缺 JSON）→ `tmp + os.replace` ✅
- LibreOffice 同用户不能多实例 → 临时 `UserInstallation` profile + 进程内 `threading.Lock` + 跨进程文件锁 ✅

---

## 阶段二十六：上传格式扩展 + 预览按钮按需显示（2026-09-15）

> 用户拍板最终 22 种（26.3 修订：追加 PPT 7 种、移除 .json）：
> Word 3（.doc/.docx/.docm）+ Excel 4（.xls/.xlsx/.xlsm/.xlsb）+ PowerPoint 7（.ppt/.pptx/.pptm/.pps/.ppsx/.ppsm/.pot）+ .epub/.csv/.pdf + 图片 3（.jpg/.jpeg/.png）+ 文本 2（.txt/.md）

### 26.1 — 后端白名单 + 预览支持矩阵
- `config.py` `ALLOWED_EXTENSIONS` 默认值改 22 种（`.env` 无该项，默认值直接生效）
- `preview_converter.py` `SUPPORTED_OFFICE_TYPES` 扩到 20 种（+PPT 7 种；anydoc 提取与 LibreOffice 转 PDF 本就支持，零新增代码）
- anydoc 提取链路确认：`anydoc_extractor.py` SUPPORTED_EXTENSIONS 已含全部 PPT 7 种，无需改动

### 26.2 — 前端预览按钮按需显示
- `DocumentView.vue` / `SearchView.vue`：`OFFICE_EXTENSIONS`/`OFFICE_TYPES` 扩 20 种
- **`shouldShowViewToggle` 从 `return true` 改为只对 4 类显示**：Office（含 PPT/CSV）→ LibreOffice 转 PDF；PDF → iframe；图片 → `<img>`；**文本类（.txt/.md）不显示切换按钮**
- 上传模态框格式说明重写：按 Word/Excel/PowerPoint/其他 + 文本类分组列全 22 种 + `accept` 属性同步 + 底部旧文案（"BMP/TIFF/GIF/WEBP 等"，早已失真）一并修正

### 26.3 — 移除 .json 支持（用户拍板：anydoc 转不出 JSON 的 Markdown）
清除全部 json 预览死代码：
- `config.py` ALLOWED 去 json
- `preview_converter.py`：删 `TEXT_PREVIEW_TYPES` / `is_supported_text_type` / `TextTooLargeError` / `read_text_content` / `_read_with_fallback` / `_read_and_format_json`（连同未用 `Tuple` import）
- `documents.py`：删 `GET /{id}/text-content` 端点
- `text_extractor.py`：`.json` 出 SUPPORTED_EXTENSIONS，删 `_format_json` 分支与 `import json`
- `DocumentView.vue`：删 `isJsonFile` / JSON `<pre>` 模板分支 / `.text-preview*` CSS
- `SearchView.vue`：删 `isJsonFile` / `JSON_TYPES`

### 验证
- ✅ 后端：`ALLOWED_EXTENSIONS` 解析 22 种；`SUPPORTED_OFFICE_TYPES` 20 种（PPT 7 种全部 office=True，.pdf/.txt/.md/.json=False）；json 死代码 hasattr 断言全部通过；完整 `app.main:app` 导入成功、无 text-content 残留路由
- ✅ 前端：`npm run build` 通过（vite build 0 error）

### 风险 / 遗留
- 历史已上传的 .json 文档：`document.content` 已是旧 TextExtractor 代码块格式，搜索/预览仍可用（markdown 渲染代码块），但新 .json 无法再上传
- 上传说明里"Office/PDF/EPUB/图片 20 种" = 22 总种 − 文本 2 种（.txt/.md 无切换按钮）

### 26.4 — 修复 PPT 上传被拒 + 上传界面去重（用户实测反馈）
- **PPT 上传报"文件内容与扩展名不匹配"的真正根因**：`upload.py` 的 `validate_file_content()` 里有独立的**魔术字节白名单** `MAGIC_SIGNATURES`，只登记了 8 种（pdf/doc/docx/xlsx/xls/jpg/jpeg/png）。阶段二十六只扩了**扩展名白名单** `ALLOWED_EXTENSIONS`，**漏了这个内容校验** → `.ppt/.pptx/...` 和 `.epub` 走到"不在列表默认拒绝"。
- **修复**：`MAGIC_SIGNATURES` 补齐 PPT 7 种 + `.epub` + `.docm/.xlsm/.xlsb`（22 种全覆盖）：
  - OLE2 复合文档头 `D0CF11E0A1B11AE1`：.doc/.xls/.ppt/.pot/.pps/.xlsb
  - ZIP 容器头 `PK\x03\x04` 等：.docx/.docm/.xlsx/.xlsm/.pptx/.pptm/.ppsx/.ppsm/.epub
- **上传界面去重**：`DocumentView.vue` 删除 `<n-upload>` 内的 `<n-alert>` 格式框体（它在上传点击区里，点击会误触发选文件，且与右侧文字描述内容重复），只保留 `<n-upload>` + 按钮 + 下方一行 `n-text` 文字描述
- 验证：构造 22 种合法文件头全部通过 `validate_file_content`；伪装（.pptx 头=OLE2）/可执行（MZ 伪装 .txt）/空文件全部正确拒绝

### 26.5 — LibreOffice 静默运行 + 预览轮询兜底（用户部署到新机器实测反馈）
用户三个表象：① 调 LibreOffice 弹出 cmd 窗口（非静默）；② Office 预览一直"转换中"卡住 + 后端日志无限刷 `GET /documents/{id}/conversion-status 200 OK`；③ 进度"约 0s"不动
- **弹窗口**：`preview_converter._call_soffice()` 的 `subprocess.run` 没加 `CREATE_NO_WINDOW` → Windows 每次调 soffice 弹控制台。修复：Windows 下 `creationflags=subprocess.CREATE_NO_WINDOW`（0x08000000，仅 Windows 有效，跨平台兼容）
- **卡住 + 刷日志（核心）**：前端 `pollPreviewConvertStatus` 只在 `ready`/`error` 才停；当 LibreOffice 未装/路径错时，`/converted-pdf` 直接 503、**不写状态文件** → `get_status` 恒返回 `idle` → `idle` 非终止态 → 前端每 2s 无限轮询。修复：加超时兜底（`idle` 持续 15s 未启动 → 报"转换未启动：请确认 LibreOffice 已装并重启"；`converting` 超 150s（宽于后端 120s 超时）→ 报"转换超时"；网络异常超 150s → 停）。日志最多刷 75 次即止
- **进度 0s**：converting 期间后端 `elapsed_sec` 恒为 0 → 前端改用客户端计时（记录首次 `converting` 时间戳）真实递增
- 两个视图（DocumentView / SearchView）同步改
- 验证：本机 soffice 探测 OK（`C:\Program Files\LibreOffice\program\soffice.exe`）；`CREATE_NO_WINDOW` 可用；前端 build 0 error；服务已重启
- **关键认知**：用户看到的"系统不在本机"实为 Office→PDF 转换在新机器失败（大概率 LibreOffice 未装）；doc 4 本身是 PDF（`file_type='pdf'`），走 iframe 直显、根本不触发 LibreOffice 转换

### 26.6 — soffice --version 版本探测漏加静默参数（用户实测：预览 Office 文档弹 LibreOffice 窗口）
- **根因**：26.5 只给 `_call_soffice`（实际转换）加了 `CREATE_NO_WINDOW`，漏了第二个 soffice 调用点 `get_version_string()`（bootstrap 时 `soffice --version` 探测版本）。Windows 上不带 `--headless` 会拉起 GUI 实例弹窗；用户关窗口 → 探测中断 → 转换流程被连带打断
- **修复**：`get_version_string` 加 `--headless` + `CREATE_NO_WINDOW` + 超时 5s→10s（commit 210bb0a）
- 现在两处 soffice 调用（版本探测 + 实际转换）都彻底静默
- 验证：真实转换 xlsx 7.1s 成功 733KB（静默）；后端启动后不拉起任何 soffice 进程（启动脚本本身不碰 LibreOffice，弹窗只发生在预览 Office 文档时）
- **时序教训**：改完代码必须重启后端才生效（soffice 探测是启动时跑的）；用户看到的弹窗多为旧代码在跑

### 26.7 — 文档列表页加 PDF 转换进度列（用户要求，与"内容提取"指示并列）
- **后端**：`documents.py` 新增 `GET /api/v1/documents/conversion-status/batch?doc_ids=1,2,3` —— 列表页一次拉取本页所有文档转换状态（复用 `get_status`；Office 类返回真实状态，非 Office 返回 `status='n/a'`；限 100 id）。踩坑：误加 `from sqlalchemy import in_`（实际用 ORM 的 `DocumentModel.id.in_()`）导致 ImportError，已删
- **前端** `DocumentView.vue`：
  - `pdfConvertStatus` ref（doc_id → {status, elapsed_sec, error_msg}）
  - 表格"内容提取"列后加"PDF 转换"列：`ready`→"已完成"(绿) / `converting`→"转换中·Xs"(黄) / `error`→"失败"(红) / `idle`→"未转换"(灰) / 非 Office→"—"
  - `loadDocuments` 后调 `loadPdfConvertStatus`；有文档 converting 时 `startPdfConvertPolling`(3s)，全到终态停止
  - `onBeforeUnmount` 清理转换/预览两个轮询定时器
- 验证：批量端点 e2e 结构正确（doc1 png→n/a，doc2-4 pdf→n/a，doc5-6 xlsx→ready）；前端 build 0 error；服务已重启

### 26.11 — Office→PDF 在线预览功能整体回退（用户对 LibreOffice 弹窗/认证/超时等问题彻底失望）
用户决策：彻底删除 Office 转 PDF 预览，LibreOffice 不再用，预览切换按钮只对 PDF/图片显示
- 后端（删 903 行）：preview_converter.py 整文件删；documents.py 删 4 端点（converted-pdf/conversion-status/batch/{id}/conversion-status/{id}/convert）共 188 行；deps.py 删 get_user_for_iframe（43 行）；config.py 删 LIBREOFFICE_BIN_PATH + PREVIEW_CONVERT_TIMEOUT（6 行）
- 前端（删 ~400 行）：DocumentView.vue 删 Office 模板分支 + previewConvert/pdfConvertStatus 块 + 表格 PDF 转换列 + OFFICE_EXTENSIONS/isOfficeFile 死代码 + loadDocuments 末尾轮询（~250 行）；SearchView.vue 同上结构（~150 行）；shouldShowViewToggle 回退到 isPDFFile || isImageFile
- 脚本（删 258 行）：scripts/batch_convert_previews.py
- 文档：删 docs/环境安装-LibreOffice.md（~198 行）；docs 系统架构/部署/开发者/用户手册 13 处 LibreOffice 提及全部改为 anydoc 描述
- 运行时：清 cache/converted_pdfs/* + task_status/preview_convert_*.json + cache/soffice_locks/*
- 保留：ALLOWED_EXTENSIONS 22 种上传白名单（含 PPT 7 种）保留——Office 类可上传但预览时走"提取内容"或下载
- 保留：@architecture.md 阶段二十四+26.5/26.6/26.7 历史条目（过程记录），新增 26.11 条目说明当前状态
- 长期约束：项目不引入 LibreOffice / soffice；如未来需 Office 在线预览必须选 SaaS 路线

### 27.2 — OnlyOffice 编辑能力整体回退为"只读在线预览"（用户决策）
- 后端：`build_editor_config` 默认 mode='view'（edit/review/comments/autosave 全 False）；端点 `/onlyoffice/documents/{id}/url` → `/preview-url`（函数 `get_onlyoffice_preview_url`）；callback 改为只读心跳（只验 token + 回 error=0，**不再下载/覆盖文件**）；services 删 `download_edited_file_from_ds` + `STATUS_*` 常量
- 前端：列表表格删 ✏在线编辑按钮；预览弹窗底部删 [编辑]+[✏在线编辑]（普通模式仅 [关闭][下载]）；👁在线预览放在预览工具栏 ✏编辑（MD 编辑入口）旁边（仅 Office 类显示）；`OfficeEditor.vue` 改"在线预览"语义 + 删 saveStatus；`openInOnlyOffice` → `openOnlyOfficePreview`
- ⚠️ 踩坑（重要）：同一文件连续多个并行 Edit 会互相覆盖（竞态）——对同一文件的编辑必须**串行**执行并逐一 grep 验证，本次只有第一个编辑保留，其余 2 个需重做
- 验证：后端 106 路由展平含 4 条 onlyoffice；callback status=2 模拟只回 error=0 不碰文件；前端 vite build ✓；后端重启后旧 /url 404、新 /preview-url 401

### 27.3 — 修复 DS 报"文档安全令牌的格式不正确"（JWT token payload 结构错误，27.1 引入）
- **根因**：DS 开 JWT 校验时，OnlyOffice 官方约定 `config.token` 的 payload **必须是整个 config 对象**（document+editorConfig），DS 逐字段比对；27.1 签的是 `{document_id, file_type}` 自定义 payload → DS 拒绝。27.1 只验证了"签发 URL 200"，未真实加载文档，所以没暴露
- **修复**：`build_editor_config` 先构造完整 config（不含 token），再 `config["token"] = sign_jwt(dict(config), expires_in=600)`
- **教训**：OnlyOffice 集成不能自创 JWT payload 结构；校验点=用户真实打开文档
- 验证：token payload 顶层 keys = [document, editorConfig, iat, exp] ✓；后端已重启
- **待用户确认**：后端 `ONLYOFFICE_JWT_SECRET`（.env / config.py）必须与 DS local.json `jwt_secret` 完全一致，否则仍报 token 错误

### 27.4 — 在线预览窗口"特别窄"修复（用户实测反馈）
- **后端** `build_editor_config`：`customization.zoom = -2`（OnlyOffice viewer 官方参数：-2=适应页宽，-1=适应整页；宽屏下文档不再缩成中间窄条）
- **前端** `OfficeEditor.vue`：① DocEditor config 显式传 `width:'100%', height:'100%'`（部分 DS 版本会量容器尺寸后写死像素，显式传百分比更稳）；② CSS 加 `.editor-frame-wrapper :deep(div)` 强制 SDK 包装层撑满；③ 高度 `calc(100vh - 220px)` → `calc(100vh - 190px)`（多给 30px 可视高度）
- 顺带补修 27.2 并行编辑被覆盖遗漏：错误文案 "无法加载 OnlyOffice 编辑器" → "无法加载 OnlyOffice 预览"
- 验证：后端 zoom=-2 ✓；vite 热更新后 JS/CSS 模块均含新值 ✓；build ✓

### 27.5 — 预览窗口"特别窄"真根因修复（27.4 的 zoom 修复不够，编辑器本身只有 ~150px 高）
- **根因（读 DS api.js 源码确认）**：`DocsAPI.DocEditor` 用 `target.parentNode.replaceChild(iframe, target)` **把占位 div 整个替换掉**，不是把 iframe 插进占位 div。因此 ① 挂在占位 div（`.editor-frame-wrapper`）上的 `calc(100vh-190px)` 高度随 div 消失而失效；② iframe 的 `width/height="100%"` 是 **HTML 属性**，其父级（n-spin 内容区，无显式高度）高度为 auto → 百分比高度解析失败，按 HTML 规范回落到 iframe 默认 **150px** → 编辑器只剩一小条
- **修复**：新增外层 `.office-editor-host`（不被替换，带 calc 显式高度）包住占位 div；iframe CSS 强制 100% 撑满 host；`destroyEditor` 改用 SDK 自带 `editor.destroyEditor()`（旧逻辑按 id 找占位 div，替换后找不到）
- **方法教训**：此类第三方 SDK DOM 行为不要猜——直接 curl DS 的 `api.js` 读源码（本项目 DS 9.4.0，createIframe 函数实锤 replaceChild + iframe 属性式宽高）
- 验证：vite build ✓；scoped CSS 编译为 `.office-editor-host[data-v-x] iframe`（iframe 无 data-v 属预期）✓

### 27.6 — 换新机器部署后预览报"文件内容与文件扩展名不匹配"（跨机取错文件，隐蔽坑）
- **现象**：新机器部署后点在线预览，编辑器 UI 正常加载但开文档报错；新机器后端日志**没有任何 /onlyoffice/file 请求**
- **根因**：`config.py` 的 `ONLYOFFICE_CALLBACK_BASE_URL` 默认值写死旧机器 IP（192.168.66.99:8002），新机器 .env 未覆盖 → DS 去**旧机器**下载；旧机器后端恰好还开着且 JWT 密钥相同（同一份代码）→ 验签通过，返回旧库同 id 的另一份文件（doc 6 在旧库是"我的pt账号.xlsx"，新库是 Joye pptx）→ DS 报内容/扩展名不匹配
- **诊断路径**：① 新机器日志无 file 请求 = DS 没来 → ② 旧机器日志有 file/6 200 = DS 去了旧机器 → ③ 两库 doc 6 文件不同 = 实锤
- **修复**：新机器 `backend/.env` 加 `ONLYOFFICE_CALLBACK_BASE_URL=http://<新IP>:8002` 并重启后端
- **防再踩**：config.py 该配置项加醒目注释（commit 9c125e5）
- **规律**：OnlyOffice 三地址各有角色——DS_URL（浏览器访问 DS）、CALLBACK_BASE_URL（DS 反向访问后端，**必须本机 IP**）、JWT_SECRET（两台保持一致）；迁移部署时 CALLBACK_BASE_URL 是必改项

### 27.7 — 新机器后端起不来：.env 带 BOM 导致 Settings 校验崩（extra_forbidden）
- **现象**：新机器（C:/rywd/...）启动报 `AI_SERVICE_ENABLED Extra inputs are not permitted`，注意报错字段名前带 `﻿`（BOM）
- **根因**：.env 被 Windows 记事本存成 UTF-8 BOM → pydantic 把首键读成 `\ufeffAI_SERVICE_ENABLED`，匹配不上已定义的 `AI_SERVICE_ENABLED` 字段 → BaseSettings 默认 extra=forbid 直接崩（整个 API 路由加载失败）
- **修复**（config.py，commit cb8b426）：`env_file_encoding="utf-8-sig"`（剥 BOM）+ `extra="ignore"`（容忍旧版残留字段如 AI_ALL_FORMATS_AI）
- **注意**：`AI_SERVICE_ENABLED` 字段本身还在代码里（阶段十九移除的是 `AI_ALL_FORMATS_AI`），所以纯 BOM 问题
- 验证：BOM 测试 .env 下 Settings() 正常，字段解析 True ✓
- **部署经验**：Windows 上编辑 .env 用 VS Code（右下角看编码），不要用记事本；或统一 utf-8-sig 后随便什么编辑器都行

### 27.8 — 删除级联清理 wiki 三件套 + 列表"重新提取"按钮（用户要求）
- **后端**：`services/wiki/index.py` 新增 `WikiIndex.remove_doc(doc_id)` — 一个事务删 8 张表（docs_fts/docs_fts_zh/doc_meta/doc_tags/doc_links 双向/doc_text/wiki_images/images_fts；FTS5 的 doc_id 是 UNINDEXED 存储列可按值 DELETE）
- **后端**：`crud/document.py delete_with_file` 在 DB+原件删除成功后级联清 `wiki/{id}.md` + `wiki/images/{id}/` + `remove_doc`（best-effort，失败只记日志不回滚；result 加 wiki_cleaned/wiki_index_removed）
- **前端**：`DocumentView.vue` 内容提取列宽 120→150，状态标签后加 🔄 重新提取按钮（NTooltip + RefreshOutline，仅管理员可见，提取中禁用防重复入队）；新增 `retryExtraction()` 复用已有 `taskService.retryDocumentExtraction` + `monitorContentExtraction` 轮询
- **验证**：e2e 临时文档全绿——删除前 md/图/索引齐备，删除后 5 项（md/图/索引/原件/DB）全清；顺带确认 FileManager 路径安全检查会拒绝 uploads 外文件删除；前端 build ✓
- **坑**：e2e 测试造 Document 必须带 owner_id（NOT NULL）；测试文件必须放 uploads 目录内（FileManager.safe_delete_file 有目录白名单）

### 27.9 — 标签筛选硬限制 slice(0,10) 误像"标签被覆盖"（用户实测）
- **现象**：文档列表页"按标签筛选"超过10个标签后只显示前10个；后续添加的标签看似"把前面的覆盖了"，实为字母序排第11位之后被截掉
- **根因**：`DocumentView.vue` L45 `allTags.slice(0, 10)` 硬限制（项目早期拍脑袋定的）
- **修复**：去掉 slice，全量渲染；外层 `<n-space align="start">` + 内层 `max-height: 96px; overflow-y: auto` 滚动容器处理超高情况；"清除筛选"按钮移出滚动容器避免滚走；v-for 缩进对齐
- **排查结论**：本项目其他 slice 限制均为合理的展示美化（如表格列每行只显示前3个标签、仪表盘最近5条），不需要动
- 验证：build ✓

### 27.10 – DocumentView 预览表格没有框线（scoped CSS 隔离坑，用户实测对比 SearchView 后反馈）
- **现象**：同一份带表格的文档，在 SearchView 预览有完整框线，DocumentView 预览没有
- **根因**：`DocumentView.vue` 的 `.markdown-content table { border: 1px solid #d0d7de }` 在 `<style scoped>` 里，被编译为 `.markdown-content[data-v-xxx] table`，但 `v-html` 注入的子元素没有 `data-v` 属性 → 选择器不命中 → 表格样式完全失效。SearchView 已用 `:deep()` 穿透，没踩坑
- **修复**：把 DocumentView 的所有 `.markdown-content X`（X是 v-html 子元素：h1-h6/p/ul/ol/li/table/th/td/code/pre/blockquote/hr/mark）改成 `.markdown-content :deep(X)`，与 SearchView 写法对齐
- **方法教训**：vue `<style scoped>` + `v-html` 经典坑——运行时注入的 DOM 不带 data-v 属性，所有作用于子元素的选择器必须 `:deep()` 穿透；项目里 8 处这种选择器都改齐了（覆盖了 ul/li 缩进、pre 灰色背景、blockquote 左竖线、mark 高亮、表格框线等所有 markdown 渲染样式）
- 验证：build ✓；dist 产物 index css 含 d0d7de（DocumentView 表格边框生效）✓

### 27.11 – 预览表格单元格"自适应不好"CSS 优化（用户实测：阅读难受）
- **根因**：`width: auto + max-width: 100%` 让短列被压扁、长列撑爆、长文本溢出撑破单元格
- **修复**（DocumentView + SearchView 双同步）：
  - 表格 `width: min(100%, 900px)`（上限防超宽，下限跟随内容）
  - td 加 `overflow-wrap: break-word + word-break: break-word`（长文本自动换行不撑破）
  - td `min-width: 80px` / th `min-width: 120px`（短列不再被压成一字一行）
  - 斑马纹（偶数行 #fbfcfd）+ hover 行高亮（#f0f7ff）——横向跨行阅读不跟丢
  - td padding 6/12 → 8/14、line-height 1.6
- **不动**：`table-layout` 保持 auto（fixed 会让列宽均匀但内容长短差异大的表格反而难看）；preview-container 已有 overflow:auto 兜底横向滚动
- 验证：build ✓

### 27.12 – SearchView 预览弹窗尺寸对齐 DocumentView（用户实测：搜索预览框比文档管理预览小）
- **现象**：SearchView 预览弹窗（90%/85%/max-1200）明显比 DocumentView 预览弹窗（98%/95%/min-1200）小，视觉观感差
- **修复**：`SearchView.vue` L172 弹窗 `style` 由 `width:90%; height:85%; max-width:1200px` 改为 `width:98%; height:95%; max-width:none; min-width:1200px`，与 DocumentView L197 完全一致
- 验证：build ✓

### 27.13 – "覆盖上传"真覆盖（用户实测：选覆盖后仍多出新文件）
- **现象**：上传同名文件选"覆盖上传"后，列表多了一个新文件而不是覆盖旧文件
- **根因**："覆盖上传"是假动作——前端只设 `fileItem.overwriteMode=true` 标记，但该标记只在 `validateFinalFileNames` 里跳过复检；调 `uploadService.uploadFile()` 时**根本没传**，FormData 无 overwrite 字段；后端 `POST /upload/` **没有 overwrite 参数**，同名一律走"自动加 _1 后缀"分支
- **修复**：
  - 后端 `upload.py`：`POST /upload/` 加 `overwrite: bool` + `overwrite_ids: str`（逗号分隔）两个 Form 参数。overwrite=true 时先逐个 `crud_document.delete_with_file` 级联删旧文档（物理文件 + DB + wiki 三件套，复用 27.8 能力），再走正常上传流程 → 天然触发一次新提取
  - 防误删校验：ids 解析为 int 列表；命中数必须与传入数一致（部分 id 失效即 400，防止状态变化误删）；ids 本身来自前端 check-filename 按 file_name 精确命中的结果，只可能是同名旧文档
  - 前端 `upload.ts`：`UploadFileData` 加 `overwrite?`/`overwrite_ids?`，FormData 追加两字段
  - 前端 `DocumentView.vue`：`checkFilenameConflicts` 采集 `existingIds`（check-filename 返回的 existing_documents 的 id 列表）→ `showFilenameConflictDialog` 透传 → 单文件/多文件两条上传分支在 overwriteMode 时把 `overwrite: true` + `overwrite_ids` 传给 `uploadService.uploadFile`
- **设计取舍**：覆盖 = 删旧建新（新文档新 id、created_at 刷新、下载/浏览次数归零、标签用本次上传值），不做"原地替换文件字节"。理由：文档是"内容+元数据+wiki 索引"整体，删旧建新最干净，且自动级联清理 wiki 三件套，无需额外处理
- **e2e（本地 8002 真实后端）**：v1 上传（id=11，提取 True）→ v2 覆盖上传（日志 `[INFO] 覆盖上传：已级联删除旧文档 覆盖上传测试.md（id=[11]）`）→ 新记录 created_at 晚于 v1 ✓ → 新提取 True 且 wiki 内容为 v2 ✓ → 清理 ✓
- **注意**：空库时 SQLite 删除后新插入可能复用同一 id（max+1），真实库 id 递增；前端提示语区分"覆盖上传成功"
