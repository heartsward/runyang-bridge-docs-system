#!/bin/bash

# 润扬大桥运维文档管理系统 - Linux停止生产服务脚本
# 作者: Claude Code
# 版本: 1.0.0

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN} 润扬大桥运维文档管理系统 - 停止生产服务${NC}"
echo -e "${BLUE}====================================================${NC}"
echo

echo -e "${CYAN}[$(date '+%H:%M:%S')] 开始停止所有服务...${NC}"
echo

# 函数：检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 函数：终止进程
kill_process() {
    local pid=$1
    local name=$2
    
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "${BLUE}[信息] 终止进程 $name (PID: $pid)${NC}"
        kill -TERM $pid
        sleep 2
        
        # 如果进程仍然存在，强制终止
        if ps -p $pid > /dev/null 2>&1; then
            echo -e "${YELLOW}[警告] 进程 $pid 未响应TERM信号，使用KILL信号${NC}"
            kill -KILL $pid
            sleep 1
        fi
        
        # 检查进程是否已终止
        if ! ps -p $pid > /dev/null 2>&1; then
            echo -e "${GREEN}[成功] 进程 $name ($pid) 已终止${NC}"
            return 0
        else
            echo -e "${RED}[错误] 无法终止进程 $name ($pid)${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}[信息] 进程 $name ($pid) 不存在或已终止${NC}"
        return 0
    fi
}

# ============= 从PID文件停止服务 =============
echo -e "${CYAN}[步骤 1/4] 从PID文件停止服务...${NC}"

# 停止后端服务
if [ -f "$ROOT_DIR/logs/backend.pid" ]; then
    BACKEND_PID=$(cat "$ROOT_DIR/logs/backend.pid" 2>/dev/null)
    if [ ! -z "$BACKEND_PID" ]; then
        kill_process $BACKEND_PID "后端服务"
    fi
    rm -f "$ROOT_DIR/logs/backend.pid"
else
    echo -e "${YELLOW}[信息] 未找到后端PID文件${NC}"
fi

# 停止前端服务
if [ -f "$ROOT_DIR/logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$ROOT_DIR/logs/frontend.pid" 2>/dev/null)
    if [ ! -z "$FRONTEND_PID" ]; then
        kill_process $FRONTEND_PID "前端服务"
    fi
    rm -f "$ROOT_DIR/logs/frontend.pid"
else
    echo -e "${YELLOW}[信息] 未找到前端PID文件${NC}"
fi

# ============= 通过进程名停止服务 =============
echo
echo -e "${CYAN}[步骤 2/4] 通过进程名停止剩余服务...${NC}"

# 停止Python后端进程
PYTHON_PIDS=$(pgrep -f "python.*database_integrated_server.py" 2>/dev/null)
if [ ! -z "$PYTHON_PIDS" ]; then
    echo -e "${BLUE}[信息] 发现Python后端进程: $PYTHON_PIDS${NC}"
    for pid in $PYTHON_PIDS; do
        kill_process $pid "Python后端"
    done
else
    echo -e "${GREEN}✅ 未发现运行中的Python后端进程${NC}"
fi

# 停止Node.js前端进程
NODE_PIDS=$(pgrep -f "(vite.*dev|npm.*run.*dev)" 2>/dev/null)
if [ ! -z "$NODE_PIDS" ]; then
    echo -e "${BLUE}[信息] 发现Node.js前端进程: $NODE_PIDS${NC}"
    for pid in $NODE_PIDS; do
        kill_process $pid "Node.js前端"
    done
else
    echo -e "${GREEN}✅ 未发现运行中的Node.js前端进程${NC}"
fi

# ============= 通过端口停止服务 =============
echo
echo -e "${CYAN}[步骤 3/4] 通过端口停止占用进程...${NC}"

# 停止占用8002端口的进程
if check_port 8002; then
    PORT_8002_PID=$(lsof -t -i:8002 2>/dev/null)
    if [ ! -z "$PORT_8002_PID" ]; then
        echo -e "${BLUE}[信息] 发现占用端口8002的进程: $PORT_8002_PID${NC}"
        for pid in $PORT_8002_PID; do
            kill_process $pid "端口8002占用进程"
        done
    fi
else
    echo -e "${GREEN}✅ 端口8002已释放${NC}"
fi

# 停止占用5173端口的进程
if check_port 5173; then
    PORT_5173_PID=$(lsof -t -i:5173 2>/dev/null)
    if [ ! -z "$PORT_5173_PID" ]; then
        echo -e "${BLUE}[信息] 发现占用端口5173的进程: $PORT_5173_PID${NC}"
        for pid in $PORT_5173_PID; do
            kill_process $pid "端口5173占用进程"
        done
    fi
else
    echo -e "${GREEN}✅ 端口5173已释放${NC}"
fi

# ============= 清理临时文件 =============
echo
echo -e "${CYAN}[步骤 4/4] 清理临时文件...${NC}"

# 创建logs目录（如果不存在）
mkdir -p "$ROOT_DIR/logs"

# 清理后端临时文件
if [ -d "$ROOT_DIR/backend/task_status" ]; then
    rm -f "$ROOT_DIR/backend/task_status"/* 2>/dev/null
    echo -e "${GREEN}[信息] 已清理后端临时状态文件${NC}"
fi

# 清理日志锁文件
if [ -f "$ROOT_DIR/backend/logs"/*.lock ]; then
    rm -f "$ROOT_DIR/backend/logs"/*.lock 2>/dev/null
    echo -e "${GREEN}[信息] 已清理日志锁文件${NC}"
fi

# 清理PID文件
rm -f "$ROOT_DIR/logs"/*.pid 2>/dev/null

# ============= 检查服务状态 =============
echo
echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   服务停止结果${NC}"
echo -e "${BLUE}====================================================${NC}"
echo

# 等待进程完全终止
sleep 2

# 检查后端端口状态
if check_port 8002; then
    echo -e "${RED}❌ 后端服务 (端口8002) 仍在运行${NC}"
    REMAINING_8002=$(lsof -t -i:8002 2>/dev/null)
    echo -e "${YELLOW}   仍在运行的PID: $REMAINING_8002${NC}"
else
    echo -e "${GREEN}✅ 后端服务 (端口8002) 已停止${NC}"
fi

# 检查前端端口状态
if check_port 5173; then
    echo -e "${RED}❌ 前端服务 (端口5173) 仍在运行${NC}"
    REMAINING_5173=$(lsof -t -i:5173 2>/dev/null)
    echo -e "${YELLOW}   仍在运行的PID: $REMAINING_5173${NC}"
else
    echo -e "${GREEN}✅ 前端服务 (端口5173) 已停止${NC}"
fi

echo
echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   清理完成${NC}"
echo -e "${BLUE}====================================================${NC}"
echo

# 检查是否还有相关进程
REMAINING_PYTHON=$(pgrep -f "python.*database_integrated_server.py" 2>/dev/null)
REMAINING_NODE=$(pgrep -f "(vite.*dev|npm.*run.*dev)" 2>/dev/null)

if [ ! -z "$REMAINING_PYTHON" ]; then
    echo -e "${YELLOW}⚠️  警告: 仍有Python进程在运行 (PID: $REMAINING_PYTHON)${NC}"
fi

if [ ! -z "$REMAINING_NODE" ]; then
    echo -e "${YELLOW}⚠️  警告: 仍有Node.js进程在运行 (PID: $REMAINING_NODE)${NC}"
fi

if [ -z "$REMAINING_PYTHON" ] && [ -z "$REMAINING_NODE" ] && ! check_port 8002 && ! check_port 5173; then
    echo -e "${GREEN}✅ 所有润扬大桥系统相关服务已完全停止${NC}"
fi

echo
echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   操作指南${NC}"
echo -e "${BLUE}====================================================${NC}"
echo
echo -e "${GREEN}🔄 重新启动系统: ${YELLOW}./start-production.sh 或 ./start-production-simple.sh${NC}"
echo -e "${GREEN}🔍 检查服务状态: ${YELLOW}./check-service-health.sh${NC}"
echo -e "${GREEN}📝 查看系统日志: ${YELLOW}tail -f logs/backend.log 或 logs/frontend.log${NC}"
echo -e "${GREEN}🗃️  数据库备份: ${YELLOW}backend/yunwei_docs.db${NC}"
echo

# 显示系统资源使用情况
if command -v free >/dev/null 2>&1; then
    echo -e "${CYAN}系统资源使用情况:${NC}"
    free -h | head -2
    echo
fi

if command -v df >/dev/null 2>&1; then
    echo -e "${CYAN}磁盘空间使用情况:${NC}"
    df -h . | tail -1
    echo
fi

echo -e "${CYAN}[$(date '+%H:%M:%S')] 服务停止操作完成！${NC}"
echo

# 返回原目录
cd "$ROOT_DIR"