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

### 标准 git push 流程（**适用于你的开发电脑 + 正常网络环境**）

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

### ⚠️ 本机 `git push` 卡死时的等价命令

**根因**：本机 git push 受 WorkBuddy 代理（`HTTPS_PROXY=http://127.0.0.1:58123`）阻断——代理对 git smart-HTTP 的 `git-receive-pack` 返回 401，导致进程一直等响应、超时被杀（实测 `timeout 30 git push origin main` 30 秒后 exit 124 无任何输出）。

**等价推送命令（用 GitHub REST API，绕开代理对 git 协议的阻断）**：

```bash
# 用之前已经写好的脚本（在 skill github-api-push-fallback 里）
# 但你需要为每次推送改 BASE_SHA / LOCAL_COMMITS——这是个 50 行 Python 脚本

# 简化版（一次推送单个 commit）：
python push_one_commit.py
```

更详细的脚本见 `C:\Users\cccly\.workbuddy\skills\github-api-push-fallback\SKILL.md` 和它的 `scripts/push_commits.py`。

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

### 2. 看代理配置（**本机卡死的最大嫌疑**）
```bash
env | grep -i proxy
# 看到 HTTPS_PROXY=http://127.0.0.1:58123 之类的就是代理
# WorkBuddy 环境的代理对 git smart-HTTP 协议返回 401
```

### 3. 看 git 是否配了走代理
```bash
git config --global --get-regexp 'http\.|https\.'
git config --get-regexp 'http\.|https\.'
```

### 4. 看连通性
```bash
# REST API（应该快）
curl -s -o /dev/null -w "API: %{http_code} | %{time_total}s\n" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/heartsward/runyang-bridge-docs-system"

# git 协议（用代理时可能卡）
git ls-remote https://github.com/heartsward/runyang-bridge-docs-system.git HEAD
```

### 5. 看本地到底有几个 commit 没推
```bash
git status -sb
#  ahead N → 有 N 个 commit 没推
```

### 6. 卡顿时立刻用的 GitHub MCP 替代推送
WorkBuddy 已连接 `github` MCP，可以用它直接 push 文件（不依赖 git 协议），但**它不会保留你的 commit 历史**——只对单文件 / 少量文件改动好用。

---

## 🎯 总结速记

| 你要做的事 | 命令 |
|------------|------|
| 其它电脑**下载/更新**代码（Linux） | `cd runyang-bridge-docs-system && ./update.sh` |
| 其它电脑**下载/更新**代码（Windows） | `cd runyang-bridge-docs-system && update.bat` |
| 本机**首次**克隆 | `git clone https://github.com/heartsward/runyang-bridge-docs-system.git` |
| 本机**上传**更新（标准流程） | `git add . && git commit -m "..." && git push origin main` |
| 本机**上传**更新（push 卡死时） | 用 `github-api-push-fallback` skill 走 Git Data API |
| **排查** push 卡死 | `timeout 30 git push origin main` → 看 exit code 和 `env \| grep proxy` |

---

**一句话**：其它电脑用 `update.sh` / `update.bat` 一键更新；本机开发完用 `git push origin main` 上传；本机 push 卡死是因为 WorkBuddy 代理对 git 协议返回 401，必须用 GitHub REST API（Git Data API 走 `blobs→trees→commits→refs`）绕开。
