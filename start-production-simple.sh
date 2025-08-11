#!/bin/bash

# 润扬大桥运维文档管理系统 - Linux生产环境快速启动脚本
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
echo -e "${CYAN}  润扬大桥运维文档管理系统 - 快速生产启动${NC}"
echo -e "${BLUE}====================================================${NC}"
echo

echo -e "${CYAN}[$(date '+%H:%M:%S')] 开始启动生产环境服务...${NC}"
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

# 函数：等待端口启动
wait_for_port() {
    local port=$1
    local timeout=${2:-30}
    local count=0
    
    echo -e "${YELLOW}等待端口 $port 启动...${NC}"
    while [ $count -lt $timeout ]; do
        if check_port $port; then
            echo -e "${GREEN}✅ 端口 $port 已启动${NC}"
            return 0
        fi
        sleep 1
        ((count++))
        echo -n "."
    done
    echo
    echo -e "${RED}❌ 端口 $port 启动超时${NC}"
    return 1
}

# ============= 启动后端服务 =============
echo -e "${CYAN}[步骤 1/3] 启动后端服务...${NC}"

# 检查后端端口
if check_port 8002; then
    echo -e "${YELLOW}⚠️  端口8002已被占用，尝试停止现有服务...${NC}"
    pkill -f "python.*database_integrated_server.py" 2>/dev/null
    sleep 2
fi

cd "$ROOT_DIR/backend"
echo -e "${BLUE}[信息] 正在启动FastAPI后端服务 (端口: 8002)...${NC}"

# 启动后端服务
nohup python database_integrated_server.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}[成功] 后端服务已启动 (PID: $BACKEND_PID)${NC}"

# 等待后端启动
if wait_for_port 8002 15; then
    echo -e "${GREEN}✅ 后端服务启动成功${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败${NC}"
    exit 1
fi

# ============= 启动前端服务 =============
echo
echo -e "${CYAN}[步骤 2/3] 启动前端服务...${NC}"

# 检查前端端口
if check_port 5173; then
    echo -e "${YELLOW}⚠️  端口5173已被占用，尝试停止现有服务...${NC}"
    pkill -f "vite.*dev" 2>/dev/null
    pkill -f "npm.*run.*dev" 2>/dev/null
    sleep 2
fi

cd "$ROOT_DIR/frontend"
echo -e "${BLUE}[信息] 正在启动Vue前端服务 (端口: 5173)...${NC}"

# 启动前端服务
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}[成功] 前端服务已启动 (PID: $FRONTEND_PID)${NC}"

# 等待前端启动
if wait_for_port 5173 20; then
    echo -e "${GREEN}✅ 前端服务启动成功${NC}"
else
    echo -e "${RED}❌ 前端服务启动失败${NC}"
    exit 1
fi

# ============= 显示系统信息 =============
echo
echo -e "${CYAN}[步骤 3/3] 系统启动完成！${NC}"
echo

echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   服务访问信息${NC}"
echo -e "${BLUE}====================================================${NC}"
echo
echo -e "${GREEN}🌐 前端界面: ${YELLOW}http://localhost:5173${NC}"
echo -e "${GREEN}🔧 后端API:  ${YELLOW}http://localhost:8002${NC}"
echo -e "${GREEN}📚 API文档:  ${YELLOW}http://localhost:8002/docs${NC}"
echo

echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   移动端API端点${NC}"
echo -e "${BLUE}====================================================${NC}"
echo
echo -e "${GREEN}📱 移动端认证: ${YELLOW}http://localhost:8002/api/v1/mobile/auth/login${NC}"
echo -e "${GREEN}📄 文档接口:   ${YELLOW}http://localhost:8002/api/v1/mobile/documents/${NC}"
echo -e "${GREEN}🏢 资产接口:   ${YELLOW}http://localhost:8002/api/v1/mobile/assets/${NC}"
echo -e "${GREEN}🎤 语音查询:   ${YELLOW}http://localhost:8002/api/v1/voice/query${NC}"
echo -e "${GREEN}ℹ️  系统信息:   ${YELLOW}http://localhost:8002/api/v1/system/info${NC}"
echo -e "${GREEN}💚 健康检查:   ${YELLOW}http://localhost:8002/api/v1/system/health${NC}"
echo

echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   系统状态监控${NC}"
echo -e "${BLUE}====================================================${NC}"
echo
echo -e "${GREEN}📊 数据分析:   ${YELLOW}http://localhost:8002/api/v1/analytics/summary${NC}"
echo -e "${GREEN}🔍 搜索接口:   ${YELLOW}http://localhost:8002/api/v1/search/${NC}"
echo -e "${GREEN}⚙️  用户设置:   ${YELLOW}http://localhost:8002/api/v1/settings/profile${NC}"
echo

echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   默认登录信息${NC}"
echo -e "${BLUE}====================================================${NC}"
echo
echo -e "${GREEN}👤 用户名: ${YELLOW}admin${NC}"
echo -e "${GREEN}🔐 密码:   ${YELLOW}admin123${NC}"
echo
echo -e "${RED}⚠️  首次登录后请立即修改默认密码${NC}"
echo

echo -e "${BLUE}====================================================${NC}"
echo

# 保存PID到文件
echo "$BACKEND_PID" > "$ROOT_DIR/logs/backend.pid"
echo "$FRONTEND_PID" > "$ROOT_DIR/logs/frontend.pid"

# 自动打开浏览器（如果有桌面环境）
if command -v xdg-open >/dev/null 2>&1; then
    echo -e "${BLUE}[信息] 是否自动打开浏览器? (y/n, 默认10秒后跳过)${NC}"
    read -t 10 -n 1 -p "打开浏览器? " open_browser
    echo
    if [[ $open_browser =~ ^[Yy]$ ]] || [[ -z $open_browser ]]; then
        echo -e "${BLUE}[信息] 正在打开系统管理界面...${NC}"
        xdg-open "http://localhost:5173" >/dev/null 2>&1 &
        sleep 2
        echo -e "${BLUE}[信息] 正在打开API文档...${NC}"
        xdg-open "http://localhost:8002/docs" >/dev/null 2>&1 &
    fi
fi

echo
echo -e "${BLUE}====================================================${NC}"
echo -e "${CYAN}                   注意事项${NC}"
echo -e "${BLUE}====================================================${NC}"
echo
echo -e "${GREEN}✅ 服务已在后台运行，关闭终端不会停止服务${NC}"
echo -e "${GREEN}🛑 如需停止服务，请运行: ${YELLOW}./stop-production.sh${NC}"
echo -e "${GREEN}🔄 如需重启服务，请先停止后重新运行此脚本${NC}"
echo -e "${GREEN}📝 系统日志位置: ${YELLOW}logs/${NC}"
echo -e "${GREEN}💾 数据库位置: ${YELLOW}backend/yunwei_docs.db${NC}"
echo

# 显示进程信息
echo -e "${CYAN}运行中的服务进程:${NC}"
echo -e "${GREEN}后端服务 PID: ${YELLOW}$BACKEND_PID${NC}"
echo -e "${GREEN}前端服务 PID: ${YELLOW}$FRONTEND_PID${NC}"
echo

echo -e "${CYAN}[$(date '+%H:%M:%S')] 生产环境启动完成！${NC}"
echo

# 返回原目录
cd "$ROOT_DIR"

echo -e "${YELLOW}按 Ctrl+C 退出 (服务将继续在后台运行)${NC}"

# 保持脚本运行以显示日志（可选）
echo -e "${BLUE}[信息] 监控服务状态中... (按 Ctrl+C 退出监控，服务继续运行)${NC}"

# 设置陷阱处理 Ctrl+C
trap 'echo -e "\n${YELLOW}退出监控，服务继续在后台运行${NC}"; exit 0' INT

# 监控服务状态
while true; do
    sleep 30
    
    # 检查后端服务
    if ! check_port 8002; then
        echo -e "${RED}[警告] 后端服务 (端口8002) 可能已停止${NC}"
    fi
    
    # 检查前端服务
    if ! check_port 5173; then
        echo -e "${RED}[警告] 前端服务 (端口5173) 可能已停止${NC}"
    fi
    
    echo -e "${GREEN}[$(date '+%H:%M:%S')] 服务运行正常${NC}"
done