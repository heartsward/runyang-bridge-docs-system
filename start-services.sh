#!/usr/bin/env bash
# 启动本项目服务（开发模式）：后端 :8002 + 前端 :5173
# 用法: ./start-services.sh
# 首次运行会自动创建 venv / node_modules 并安装依赖。
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

echo "=========================================="
echo "  Runyang Bridge System - Service Launcher"
echo "=========================================="

# ---- 探测 Python（PATH 优先，回退 WorkBuddy 受管运行时）----
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    for v in "$HOME/.workbuddy/binaries/python/versions/3."*/python*; do
        [ -x "$v" ] && PYTHON_BIN="$v" && break
    done
fi
if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found. Please install Python 3.8+ first."
    exit 1
fi
echo "Python found: $PYTHON_BIN"

# ---- 探测 Node（PATH 优先，回退 WorkBuddy 受管运行时）----
if ! command -v node >/dev/null 2>&1; then
    for v in "$HOME/.workbuddy/binaries/node/versions/"*/node; do
        [ -x "$v" ] && export PATH="$(dirname "$v"):$PATH" && break
    done
fi
if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: Node.js not found. Please install Node.js 16+ first."
    exit 1
fi
echo "Node.js found: $(node --version)"

# ---- 后端：venv + 依赖（首次自动安装）----
cd "$BACKEND"
if [ ! -x "venv/bin/python" ]; then
    echo "Creating backend virtual environment..."
    "$PYTHON_BIN" -m venv venv
    echo "Installing backend dependencies..."
    venv/bin/python -m pip install --upgrade pip --disable-pip-version-check
    # 依赖文件优先级：requirements.txt（通用）> requirements-windows.txt（完整清单，实际跨平台）
    if [ -f requirements.txt ]; then
        venv/bin/python -m pip install -r requirements.txt --disable-pip-version-check
    else
        venv/bin/python -m pip install -r requirements-windows.txt --disable-pip-version-check
    fi
fi
echo "Starting backend on :8002 ..."
nohup venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 \
    > "$LOG_DIR/backend.log" 2>&1 &
echo $! > "$LOG_DIR/backend.pid"

# ---- 前端：node_modules + dev server ----
cd "$FRONTEND"
if [ ! -d node_modules ]; then
    echo "Installing frontend dependencies..."
    npm install || { echo "ERROR: Frontend dependency installation failed"; exit 1; }
fi
echo "Starting frontend on :5173 ..."
nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
echo $! > "$LOG_DIR/frontend.pid"

sleep 3
echo
echo "=========================================="
echo "  System Started!"
echo "=========================================="
echo "Frontend:      http://localhost:5173"
echo "Backend API:   http://localhost:8002/docs"
echo "Health:        http://localhost:8002/health"
echo "AI Wiki MCP:   http://localhost:8002/mcp"
echo "Logs:          $LOG_DIR/{backend,frontend}.log"
echo "Default Login: admin / admin123"
echo
echo "停止服务: ./stop-services.sh"
