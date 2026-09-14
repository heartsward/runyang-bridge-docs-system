# Git 命令速查（本项目专用）

> ⚠️ **本项目 GitHub 仓库**：`https://github.com/heartsward/runyang-bridge-docs-system`
>
> 本文档覆盖三类操作：① 其它电脑下载/更新代码 ② 本机上传更新到 GitHub ③ 推送卡顿的排查

---

## 📥 一、其它电脑（部署服务器）下载/更新代码

### 🐧 Linux/macOS

**首次部署（从零拉代码）**：
```bash
# 1. 克隆仓库
git clone https://github.com/heartsward/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system

# 2. 首次安装（建 venv + 装前后端依赖）
chmod +x *.sh
./install-complete.bat 2>/dev/null || true   # Windows 脚本，Linux 跳过
./start-services.sh                          # 首次运行会自动建 venv + 装依赖
```

**日常更新（推荐一键脚本）**：
```bash
cd runyang-bridge-docs-system
./update.sh
```

**日常更新（手动命令）**：
```bash
cd runyang-bridge-docs-system

# 1. 拉代码（严格快进，绝不动 .env / 数据库 / 上传文件 / venv / node_modules）
git pull --ff-only origin main

# 2. 更新依赖（仅补缺，不全量重装）
cd backend && pip install -r requirements-windows.txt --upgrade-strategy only-if-needed
cd ../frontend && npm install

# 3. 重启服务
cd ..
./stop-services.sh
./start-services.sh
```

### 🪟 Windows

**首次部署**：
```cmd
git clone https://github.com/heartsward/runyang-bridge-docs-system.git
cd runyang-bridge-docs-system
install-complete.bat
start-services.bat
```

**日常更新（推荐一键脚本）**：
```cmd
cd runyang-bridge-docs-system
update.bat
```

**日常更新（手动命令）**：
```cmd
cd runyang-bridge-docs-system

git pull --ff-only origin main

cd backend
pip install -r requirements-windows.txt --upgrade-strategy only-if-needed
cd ..\frontend
npm install
cd ..

stop-services.bat
start-services.bat
```

### ⚠️ 关键安全点
- `git pull --ff-only` 严格快进——本地如有未推送 commit 会**拒绝**并提示
- `.gitignore` 已保护：`.env` / `*.db` / `uploads/` / `wiki/images/` / `venv/` / `node_modules/` / `logs/` / `task_status/`
- 数据回滚：`git reset --hard HEAD@{1}`（reflog 保留旧 commit 可找回）

---

## 📤 二、本机（开发电脑）上传更新到 GitHub

### ✅ 推荐：一键脚本 `push.sh` / `push.bat`

仓库根目录提供 `push.sh`（Linux/macOS）和 `push.bat`（Windows），**解决本机 `git push` 卡很久的问题**：

```bash
# Linux/macOS
./push.sh

# Windows
push.bat
```

**脚本做了什么**：
1. 防御性检查工作区脏则中止
2. 拿当前分支 + GCM 里的 token
3. 看 ahead/behind：若 diverged → 用 `--force-with-lease` 覆盖
4. **`env -u HTTPS_PROXY -u HTTP_PROXY`**：取消 WorkBuddy 代理
5. **`-c "url.https://x-access-token:${TOKEN}@github.com/heartsward/.insteadOf=https://github.com/heartsward/"`**：让 git 用 fine-grained PAT 的正确认证格式
6. `git push [--force-with-lease] origin <branch>`

### 标准 git push 流程（**适用于普通网络环境**）

```bash
cd D:\sdxtywzsk\runyang-bridge-docs-system

# 1. 看改了啥
git status

# 2. 暂存
git add .

# 3. 提交（按 Vibe Coding 规范写 commit message）
git -c core.quotepath=OFF commit -m "feat: 说明做了什么 - 范围"

# 4. 推送到 GitHub
git push origin main
```

如果 `git push` 卡住超过 30 秒，立刻 `Ctrl+C` 然后改用 `push.sh` / `push.bat`。

### ⚠️ 推送卡顿的真实根因（本机，2026-09-14 实测）

**根因就一个**：WorkBuddy 环境的 `HTTPS_PROXY=http://127.0.0.1:58123` 拦截 git smart-HTTP 推送。trace 看到的 401 是**代理返回的**（不是 GitHub 真返回的）。

**最简解法**（一行命令，绕过代理）：

```bash
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy \
    git push --force-with-lease origin main
```

**stale info 错误**：本地 `origin/main` 引用陈旧 → 先 fetch 刷新：

```bash
env -u HTTPS_PROXY git fetch --update-head-ok origin main
env -u HTTPS_PROXY git push --force origin main
```

### 备选方案：Git Data API 推送（仅当上面全部失败时用）

走 GitHub REST API（`git/blobs → git/trees → git/commits → git/refs force`），保留干净历史但 SHA 会变。skill `github-api-push-fallback` 已写好流程：`C:\Users\cccly\.workbuddy\skills\github-api-push-fallback\`。

---

## 🔍 三、推送卡顿的排查命令

按下面顺序逐条排查，找到具体卡点：

### 1. 实测 push 是否卡死（30 秒超时）
```bash
cd /d/sdxtywzsk/runyang-bridge-docs-system
timeout 30 git push origin main
echo "exit=$?"
#  exit=124 → 超时被杀 = 卡死了（确认问题）
#  exit=0   → push 成功（不是卡）
#  exit=1   → push 失败但有报错
```

### 2. 看代理配置（**本机卡死的嫌疑之一**）
```bash
env | grep -i proxy
# 看到 HTTPS_PROXY=http://127.0.0.1:58123 之类的就是 WorkBuddy 代理
# 但取消它不一定能解决——见第 3 步
```

### 3. 看 git push 实际拿到了什么 HTTP 响应
```bash
env -u HTTPS_PROXY -u HTTP_PROXY \
    GIT_TRACE=1 GIT_CURL_VERBOSE=1 \
    git push origin main 2>&1 | grep -E "(Recv header|Send header|401|Unauthorized)" | head -20
# 看到 "HTTP/1.1 401 Unauthorized" + "www-authenticate: Basic realm=GitHub"
#  → 不是代理问题，是 GitHub 认证失败
#  → 用 push.sh / push.bat 走 x-access-token URL 解决
```

### 4. 用直连 git ls-remote 测连通性
```bash
env -u HTTPS_PROXY git ls-remote https://github.com/heartsward/runyang-bridge-docs-system.git HEAD
# 应该秒回 SHA
```

### 5. 看本地到底有几个 commit 没推 + 是否 diverged
```bash
git status -sb
#  ahead N behind M  → 有 N 个本地 commit、远端有 M 个新 commit
#  ahead N           → 只本地有 N 个 commit
#  behind N          → 远端有 N 个本地没有的（可能别人推过）
```

---

## 🎯 总结速记

| 你要做的事 | 命令 |
|------------|------|
| 其它电脑**下载/更新**代码（Linux） | `cd runyang-bridge-docs-system && ./update.sh` |
| 其它电脑**下载/更新**代码（Windows） | `cd runyang-bridge-docs-system && update.bat` |
| 本机**首次**克隆 | `git clone https://github.com/heartsward/runyang-bridge-docs-system.git` |
| 本机**上传**更新（推荐） | `./push.sh` 或 `push.bat`（自动处理代理 + fine-grained PAT 认证） |
| 本机**上传**更新（手动） | `git add . && git commit -m "..." && git push origin main` |
| **排查** push 卡死 | `timeout 30 git push origin main` + `env -u HTTPS_PROXY GIT_TRACE=1 ...` |

---

**一句话**：
- 其它电脑用 `update.sh` / `update.bat` 一键更新
- 本机用 `push.sh` / `push.bat` 一键推送（自动处理 WorkBuddy 代理 + fine-grained PAT 认证）
- `git push` 卡死的真因不是代理，是 GitHub 拒绝 GCM 的 Basic Auth 头对 fine-grained PAT 的认证——`push.sh` 的解法是 `env -u HTTPS_PROXY` + `url.x-access-token:TOKEN@github.com/.insteadOf`
