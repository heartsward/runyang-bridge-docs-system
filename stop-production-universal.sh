#!/bin/bash

clear

echo "========================================"
echo "   润扬大桥运维文档管理系统 - 停止服务"
echo "========================================"
echo

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "[信息] 正在停止系统服务..."

# 停止后端服务
echo "[步骤 1/2] 停止后端服务..."
if [ -f "$SCRIPT_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$SCRIPT_DIR/backend.pid")
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "[信息] 发现后端进程 PID: $BACKEND_PID"
        kill $BACKEND_PID
        sleep 2
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "[警告] 后端进程未响应，强制终止"
            kill -9 $BACKEND_PID
        fi
        echo "[成功] 后端服务已停止"
    else
        echo "[信息] 后端服务未运行"
    fi
    rm -f "$SCRIPT_DIR/backend.pid"
else
    # 查找并终止Python进程
    PYTHON_PIDS=$(pgrep -f "database_integrated_server.py")
    if [ ! -z "$PYTHON_PIDS" ]; then
        echo "[信息] 发现后端进程: $PYTHON_PIDS"
        kill $PYTHON_PIDS
        sleep 2
        # 检查是否还在运行，如果是则强制终止
        for pid in $PYTHON_PIDS; do
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid
            fi
        done
        echo "[成功] 后端服务已停止"
    else
        echo "[信息] 未发现运行中的后端服务"
    fi
fi

# 停止前端服务
echo "[步骤 2/2] 停止前端服务..."
if [ -f "$SCRIPT_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$SCRIPT_DIR/frontend.pid")
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "[信息] 发现前端进程 PID: $FRONTEND_PID"
        kill $FRONTEND_PID
        sleep 2
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "[警告] 前端进程未响应，强制终止"
            kill -9 $FRONTEND_PID
        fi
        echo "[成功] 前端服务已停止"
    else
        echo "[信息] 前端服务未运行"
    fi
    rm -f "$SCRIPT_DIR/frontend.pid"
else
    # 查找并终止Node.js进程
    NODE_PIDS=$(pgrep -f "npm run dev\|vite")
    if [ ! -z "$NODE_PIDS" ]; then
        echo "[信息] 发现前端进程: $NODE_PIDS"
        kill $NODE_PIDS
        sleep 2
        # 检查是否还在运行，如果是则强制终止
        for pid in $NODE_PIDS; do
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid
            fi
        done
        echo "[成功] 前端服务已停止"
    else
        echo "[信息] 未发现运行中的前端服务"
    fi
fi

echo
echo "========================================"
echo "            服务已停止"
echo "========================================"
echo
echo "[完成] 所有服务进程已终止"
echo "[提示] 如需重新启动，请运行 ./start-production-universal.sh"
echo