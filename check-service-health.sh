#!/bin/bash
# 润扬大桥运维文档管理系统 - 服务健康检查脚本 (Linux/macOS)

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

echo_step() {
    echo -e "${CYAN}[步骤 $1]${NC} $2"
}

# 清屏并显示标题
clear
echo "===================================================="
echo "     润扬大桥运维文档管理系统 - 服务健康检查"
echo "===================================================="
echo

echo_info "正在检查服务运行状态..."
echo

# 步骤1: 检查后端服务
echo_step "1/3" "检查后端服务 (端口 8002)..."
if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo_success "后端服务正在运行"
    BACKEND_STATUS="运行中"
    BACKEND_PID=$(lsof -Pi :8002 -sTCP:LISTEN -t)
else
    echo_error "后端服务未运行 (端口 8002 未监听)"
    BACKEND_STATUS="停止"
    BACKEND_PID=""
fi

# 步骤2: 检查前端服务
echo_step "2/3" "检查前端服务 (端口 5173)..."
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo_success "前端服务正在运行"
    FRONTEND_STATUS="运行中"
    FRONTEND_PID=$(lsof -Pi :5173 -sTCP:LISTEN -t)
else
    echo_error "前端服务未运行 (端口 5173 未监听)"
    FRONTEND_STATUS="停止"
    FRONTEND_PID=""
fi

# 步骤3: API健康检查
echo_step "3/3" "检查API健康状态..."
if curl -s --max-time 5 http://localhost:8002 >/dev/null 2>&1; then
    echo_success "后端API响应正常"
    API_STATUS="正常"
else
    echo_warning "后端API响应异常或超时"
    API_STATUS="异常"
fi

echo
echo "===================================================="
echo "                   检查结果"
echo "===================================================="
echo

echo_info "服务状态:"
echo "  后端服务 (8002): $BACKEND_STATUS"
if [ -n "$BACKEND_PID" ]; then
    echo "    进程PID: $BACKEND_PID"
fi
echo "  前端服务 (5173): $FRONTEND_STATUS"
if [ -n "$FRONTEND_PID" ]; then
    echo "    进程PID: $FRONTEND_PID"
fi
echo "  API健康状态:     $API_STATUS"

echo
echo_info "访问地址:"
echo "  前端界面: http://localhost:5173"
echo "  后端API:  http://localhost:8002"
echo "  API文档:  http://localhost:8002/docs"
echo

# 总体状态判断
if [ "$BACKEND_STATUS" = "运行中" ] && [ "$FRONTEND_STATUS" = "运行中" ]; then
    echo_success "总体状态: 系统运行正常 ✓"
else
    echo_error "总体状态: 系统部分服务异常 ✗"
    echo
    echo_info "解决建议:"
    if [ "$BACKEND_STATUS" != "运行中" ]; then
        echo "  - 启动后端: cd backend && python database_integrated_server.py"
    fi
    if [ "$FRONTEND_STATUS" != "运行中" ]; then
        echo "  - 启动前端: cd frontend && npm run dev"
    fi
    echo "  - 或运行: ./start-production.sh"
fi

# 检查日志文件
echo
echo_info "日志文件状态:"
if [ -f "logs/backend.log" ]; then
    BACKEND_LOG_SIZE=$(du -h logs/backend.log | cut -f1)
    echo "  后端日志: logs/backend.log ($BACKEND_LOG_SIZE)"
else
    echo "  后端日志: 不存在"
fi

if [ -f "logs/frontend.log" ]; then
    FRONTEND_LOG_SIZE=$(du -h logs/frontend.log | cut -f1)
    echo "  前端日志: logs/frontend.log ($FRONTEND_LOG_SIZE)"
else
    echo "  前端日志: 不存在"
fi

echo
echo_info "最近错误 (如果有):"
if [ -f "logs/backend.log" ]; then
    echo "=== 后端最近错误 ==="
    tail -5 logs/backend.log | grep -i error || echo "  无错误"
fi
if [ -f "logs/frontend.log" ]; then
    echo "=== 前端最近错误 ==="
    tail -5 logs/frontend.log | grep -i error || echo "  无错误"
fi

echo