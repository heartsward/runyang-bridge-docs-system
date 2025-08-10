#!/bin/bash
# 润扬大桥运维文档管理系统 - 停止服务脚本 (Linux/macOS)

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 输出带颜色的信息
echo_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

echo_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 清屏并显示标题
clear
echo "===================================================="
echo "      润扬大桥运维文档管理系统 - 停止服务"
echo "===================================================="
echo

echo_info "正在停止润扬大桥运维文档管理系统服务..."
echo

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# 步骤1: 停止前端服务
echo_info "[步骤 1/2] 停止前端服务..."

# 从PID文件停止前端服务
if [ -f "$PROJECT_ROOT/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PROJECT_ROOT/logs/frontend.pid")
    if kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo_info "终止前端进程 PID: $FRONTEND_PID"
        kill -TERM "$FRONTEND_PID" 2>/dev/null
        sleep 2
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo_warning "前端进程未正常退出，强制终止..."
            kill -KILL "$FRONTEND_PID" 2>/dev/null
        fi
        echo_success "前端服务已停止"
    else
        echo_warning "前端进程 (PID: $FRONTEND_PID) 未运行"
    fi
    rm -f "$PROJECT_ROOT/logs/frontend.pid"
else
    echo_info "未找到前端PID文件，尝试通过端口查找..."
    # 通过端口查找并终止进程
    if command -v lsof >/dev/null 2>&1; then
        FRONTEND_PIDS=$(lsof -ti:5173 2>/dev/null)
        if [ -n "$FRONTEND_PIDS" ]; then
            echo_info "发现占用端口5173的进程: $FRONTEND_PIDS"
            echo "$FRONTEND_PIDS" | xargs -r kill -TERM 2>/dev/null
            sleep 2
            echo "$FRONTEND_PIDS" | xargs -r kill -KILL 2>/dev/null
            echo_success "前端服务已通过端口强制停止"
        else
            echo_info "端口5173未被占用"
        fi
    else
        echo_warning "lsof 命令不可用，无法通过端口查找进程"
    fi
fi

# 步骤2: 停止后端服务
echo_info "[步骤 2/2] 停止后端服务..."

# 从PID文件停止后端服务
if [ -f "$PROJECT_ROOT/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$PROJECT_ROOT/logs/backend.pid")
    if kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo_info "终止后端进程 PID: $BACKEND_PID"
        kill -TERM "$BACKEND_PID" 2>/dev/null
        sleep 2
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo_warning "后端进程未正常退出，强制终止..."
            kill -KILL "$BACKEND_PID" 2>/dev/null
        fi
        echo_success "后端服务已停止"
    else
        echo_warning "后端进程 (PID: $BACKEND_PID) 未运行"
    fi
    rm -f "$PROJECT_ROOT/logs/backend.pid"
else
    echo_info "未找到后端PID文件，尝试通过端口查找..."
    # 通过端口查找并终止进程
    if command -v lsof >/dev/null 2>&1; then
        BACKEND_PIDS=$(lsof -ti:8002 2>/dev/null)
        if [ -n "$BACKEND_PIDS" ]; then
            echo_info "发现占用端口8002的进程: $BACKEND_PIDS"
            echo "$BACKEND_PIDS" | xargs -r kill -TERM 2>/dev/null
            sleep 2
            echo "$BACKEND_PIDS" | xargs -r kill -KILL 2>/dev/null
            echo_success "后端服务已通过端口强制停止"
        else
            echo_info "端口8002未被占用"
        fi
    else
        echo_warning "lsof 命令不可用，无法通过端口查找进程"
    fi
fi

# 清理残留进程
echo
echo_info "清理相关残留进程..."

# 查找并终止相关的Python进程
PYTHON_PIDS=$(pgrep -f "database_integrated_server.py" 2>/dev/null)
if [ -n "$PYTHON_PIDS" ]; then
    echo_info "发现相关Python进程: $PYTHON_PIDS"
    echo "$PYTHON_PIDS" | xargs -r kill -TERM 2>/dev/null
    sleep 1
    echo "$PYTHON_PIDS" | xargs -r kill -KILL 2>/dev/null
fi

# 查找并终止相关的Node进程
NODE_PIDS=$(pgrep -f "npm.*run.*dev" 2>/dev/null)
if [ -n "$NODE_PIDS" ]; then
    echo_info "发现相关Node进程: $NODE_PIDS"
    echo "$NODE_PIDS" | xargs -r kill -TERM 2>/dev/null
    sleep 1
    echo "$NODE_PIDS" | xargs -r kill -KILL 2>/dev/null
fi

echo
echo "===================================================="
echo "                   停止完成！"
echo "===================================================="
echo
echo_success "润扬大桥运维文档管理系统服务已全部停止"
echo
echo_info "如需重新启动，请运行: ./start-production.sh"
echo