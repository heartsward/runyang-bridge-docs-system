#!/usr/bin/env bash
# 更新本项目代码并重启服务（不破坏 .env / 数据库 / 上传文件）
# 用法: ./update.sh
#
# 设计原则：
# - git pull --ff-only：严格快进，避免意外 merge/rebase 覆盖本地分支
# - 保护本地数据：.env、*.db、uploads/、logs/、venv/、node_modules/ 全部在 .gitignore 里，
#   git pull 不会动它们
# - 防御性检查：工作区脏（未提交改动）则中止并提示，避免覆盖本地修改
# - 重启后端：Settings 单例 import 时只读一次 .env，必须重启才能加载新代码；
#   前端 vite dev server HMR 自动生效，无需重启
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=========================================="
echo "  Runyang Bridge System - Update"
echo "=========================================="
echo "工作区: $ROOT"
echo

# ---- 1. 防御性检查：工作区必须干净 ----
if ! git diff --quiet HEAD 2>/dev/null; then
    echo "ERROR: 工作区有未提交改动，拒绝 pull。"
    echo "       请先 'git status' 查看，改完后 'git stash' 或 'git commit' 再重跑。"
    exit 1
fi
if ! git diff --cached --quiet HEAD 2>/dev/null; then
    echo "ERROR: 工作区有已暂存未提交改动，拒绝 pull。"
    echo "       请先 'git status' 查看。"
    exit 1
fi

# ---- 2. 备份 .env（防御性：极端情况下可能被误改）----
ENV_FILE="backend/.env"
ENV_BACKUP=""
if [ -f "$ENV_FILE" ]; then
    ENV_BACKUP="$ENV_FILE.update.bak.$(date +%Y%m%d_%H%M%S)"
    cp "$ENV_FILE" "$ENV_BACKUP"
    echo "[1/5] 已备份 $ENV_FILE -> $ENV_BACKUP"
else
    echo "[1/5] $ENV_FILE 不存在，跳过备份"
fi

# ---- 3. 拉取最新代码 ----
echo "[2/5] 拉取最新代码（git pull --ff-only origin main）..."
if ! git pull --ff-only origin main; then
    echo
    echo "ERROR: git pull 失败。"
    echo "  可能原因："
    echo "    - 远端拒绝 fast-forward（本地有未推送 commit）→ 用 'git status' 看"
    echo "    - 网络/认证问题 → 用 'git fetch origin main' 单独诊断"
    if [ -n "$ENV_BACKUP" ] && [ -f "$ENV_BACKUP" ]; then
        echo "  .env 备份在 $ENV_BACKUP，可手动恢复"
    fi
    exit 1
fi
NEW_SHA=$(git rev-parse --short HEAD)
echo "      当前 HEAD: $NEW_SHA"

# ---- 4. 更新 Python 依赖（如 requirements 有变化）----
echo "[3/5] 检查后端依赖..."
cd "$ROOT/backend"
if [ -x "venv/bin/python" ]; then
    # 后端 venv 已建：按需装新依赖
    REQ_FILE="requirements.txt"
    [ ! -f "$REQ_FILE" ] && REQ_FILE="requirements-windows.txt"
    if [ -f "$REQ_FILE" ]; then
        echo "      pip install -r $REQ_FILE（--upgrade-strategy only-if-needed）"
        venv/bin/python -m pip install -r "$REQ_FILE" --upgrade-strategy only-if-needed --disable-pip-version-check -q 2>&1 | tail -3
    fi
else
    echo "      venv 不存在，跳过（首次部署请先运行 install-complete.bat 或 ./start-services.sh）"
fi

# ---- 5. 更新前端依赖 ----
echo "[4/5] 检查前端依赖..."
cd "$ROOT/frontend"
if [ -d "node_modules" ]; then
    echo "      npm install（仅补缺，不全量）"
    npm install --no-audit --no-fund -q 2>&1 | tail -3
else
    echo "      node_modules 不存在，跳过（首次部署请先运行 install-complete.bat 或 ./start-services.sh）"
fi

# ---- 6. 重启后端（前端 vite dev server HMR 自动生效，无需重启）----
echo "[5/5] 重启后端..."
cd "$ROOT"

# 优先用 stop-services.sh + start-services.sh（统一端口停止逻辑）
if [ -x "./stop-services.sh" ]; then
    ./stop-services.sh >/dev/null 2>&1
fi

# 给后端一点时间释放端口
sleep 2

if [ -x "./start-services.sh" ]; then
    ./start-services.sh
else
    echo "WARN: ./start-services.sh 不存在或无执行权限，跳过启动"
    echo "      请手动启动后端"
fi

echo
echo "=========================================="
echo "  Update Complete!"
echo "=========================================="
echo "HEAD: $NEW_SHA"
echo "日志: logs/backend.log  logs/frontend.log"
echo "回滚（如需）: git reset --hard HEAD@{1}  （恢复 pull 前的代码）"
if [ -n "$ENV_BACKUP" ] && [ -f "$ENV_BACKUP" ]; then
    echo ".env 备份: $ENV_BACKUP"
fi
echo
