#!/bin/bash
# 润扬大桥运维文档管理系统 - 生产模式启动脚本 (Linux/macOS)

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

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 清屏并显示标题
clear
echo "===================================================="
echo "      润扬大桥运维文档管理系统 - 生产模式启动"
echo "===================================================="
echo

# 检查Python环境
echo_info "检查Python环境..."
if ! command_exists python3; then
    if ! command_exists python; then
        echo_error "未找到 Python，请先安装 Python 3.8+ 版本"
        echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        echo "CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "macOS: brew install python3"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 检查Python版本
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}' | cut -d. -f1-2)
echo_success "发现 Python $PYTHON_VERSION"

# 检查Node.js环境
echo_info "检查Node.js环境..."
if ! command_exists node; then
    echo_error "未找到 Node.js，请先安装 Node.js 16+ 版本"
    echo "Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "CentOS/RHEL: curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo yum install -y nodejs"
    echo "macOS: brew install node"
    exit 1
fi

NODE_VERSION=$(node --version)
echo_success "发现 Node.js $NODE_VERSION"

# 检查npm
if ! command_exists npm; then
    echo_error "未找到 npm，请确保 Node.js 正确安装"
    exit 1
fi

# 检查LibreOffice环境
echo_info "检查LibreOffice环境..."
LIBREOFFICE_FOUND=false

# 检查常见的LibreOffice安装路径
if command_exists libreoffice; then
    echo_success "发现LibreOffice (命令行可用)"
    LIBREOFFICE_FOUND=true
elif command_exists soffice; then
    echo_success "发现LibreOffice (soffice命令可用)"
    LIBREOFFICE_FOUND=true
elif [ -f "/usr/bin/libreoffice" ]; then
    echo_success "发现LibreOffice (/usr/bin/libreoffice)"
    LIBREOFFICE_FOUND=true
elif [ -f "/usr/bin/soffice" ]; then
    echo_success "发现LibreOffice (/usr/bin/soffice)"
    LIBREOFFICE_FOUND=true
elif [ -f "/opt/libreoffice/program/soffice" ]; then
    echo_success "发现LibreOffice (/opt/libreoffice)"
    LIBREOFFICE_FOUND=true
elif [ -d "/Applications/LibreOffice.app" ]; then
    echo_success "发现LibreOffice (macOS应用)"
    LIBREOFFICE_FOUND=true
fi

if [ "$LIBREOFFICE_FOUND" = false ]; then
    echo_warning "未找到 LibreOffice，文档内容提取功能将受限"
    echo
    echo_info "LibreOffice 用于提取Word、Excel等文档内容，建议安装："
    
    # 根据操作系统提供不同的安装指导
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS:"
        echo "  1. 访问 https://www.libreoffice.org/download/download/"
        echo "  2. 或使用 Homebrew: brew install --cask libreoffice"
    elif [[ -f /etc/debian_version ]]; then
        echo "Ubuntu/Debian:"
        echo "  sudo apt update && sudo apt install libreoffice"
    elif [[ -f /etc/redhat-release ]]; then
        echo "CentOS/RHEL/Fedora:"
        echo "  sudo yum install libreoffice 或 sudo dnf install libreoffice"
    else
        echo "Linux:"
        echo "  使用包管理器安装: libreoffice"
        echo "  或访问: https://www.libreoffice.org/download/download/"
    fi
    
    echo
    echo_warning "是否继续启动？文档提取功能可能无法正常工作。"
    read -p "继续启动? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo_info "请安装LibreOffice后重新运行脚本"
        exit 1
    fi
    echo_info "继续启动，但文档提取功能可能受限"
fi

echo_info "正在启动润扬大桥运维文档管理系统..."
echo

# 步骤1: 安装Python依赖
echo_info "[步骤 1/6] 检查Python依赖..."
cd "$PROJECT_ROOT/backend" || {
    echo_error "无法找到 backend 目录"
    exit 1
}

if [ ! -f "requirements.txt" ]; then
    echo_error "未找到 backend/requirements.txt 文件"
    exit 1
fi

echo_info "安装Python依赖包..."
if command_exists pip3; then
    pip3 install -r requirements.txt
elif command_exists pip; then
    pip install -r requirements.txt
else
    echo_error "未找到 pip，请先安装 pip"
    exit 1
fi

if [ $? -ne 0 ]; then
    echo_error "Python依赖安装失败"
    exit 1
fi

# 步骤2: 安装Node.js依赖
echo
echo_info "[步骤 2/6] 检查Node.js依赖..."
cd "$PROJECT_ROOT/frontend" || {
    echo_error "无法找到 frontend 目录"
    exit 1
}

if [ ! -f "package.json" ]; then
    echo_error "未找到 frontend/package.json 文件"
    exit 1
fi

echo_info "安装Node.js依赖包..."
npm install
if [ $? -ne 0 ]; then
    echo_error "Node.js依赖安装失败"
    exit 1
fi

# 步骤3: 配置生产环境
echo
echo_info "[步骤 3/6] 配置生产环境..."
cd "$PROJECT_ROOT/backend"

# 优先使用环境配置模板
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo_success "已从模板创建后端环境配置文件"
        echo_warning "请编辑 backend/.env 文件，修改SECRET_KEY等重要配置"
    elif [ -f ".env.production" ]; then
        cp .env.production .env
        echo_success "后端生产环境配置已应用"
    else
        echo_warning "未找到环境配置文件，请手动创建 .env"
    fi
else
    echo_info "后端环境配置文件已存在"
fi

cd "$PROJECT_ROOT/frontend"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo_success "已从模板创建前端环境配置文件"
    elif [ -f ".env.production" ]; then
        cp .env.production .env
        echo_success "前端生产环境配置已应用"
    else
        echo_warning "未找到环境配置文件，请手动创建 .env"
    fi
else
    echo_info "前端环境配置文件已存在"
fi

# 步骤4: 构建前端
echo
echo_info "[步骤 4/6] 构建前端应用..."
npm run build
if [ $? -ne 0 ]; then
    echo_error "前端构建失败"
    exit 1
fi
echo_success "前端构建完成"

# 步骤5: 启动后端服务
echo
echo_info "[步骤 5/6] 启动后端服务..."
cd "$PROJECT_ROOT/backend"
echo_info "正在启动后端服务 (端口: 8002)..."

# 检查端口是否被占用
if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null; then
    echo_warning "端口 8002 已被占用，尝试终止现有进程..."
    kill -9 $(lsof -ti:8002) 2>/dev/null || true
    sleep 2
fi

# 在后台启动后端服务
nohup $PYTHON_CMD database_integrated_server.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid

# 等待后端启动
echo_info "等待后端服务启动..."
sleep 5

# 检查后端是否成功启动
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo_success "后端服务启动成功 (PID: $BACKEND_PID)"
else
    echo_error "后端服务启动失败"
    exit 1
fi

# 步骤6: 启动前端服务
echo
echo_info "[步骤 6/6] 启动前端服务..."
cd "$PROJECT_ROOT/frontend"
echo_info "正在启动前端服务 (端口: 5173)..."

# 检查端口是否被占用
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null; then
    echo_warning "端口 5173 已被占用，尝试终止现有进程..."
    kill -9 $(lsof -ti:5173) 2>/dev/null || true
    sleep 2
fi

# 在后台启动前端服务
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid

# 等待前端启动
echo_info "等待前端服务启动..."
sleep 3

echo
echo "===================================================="
echo "                   启动完成！"
echo "===================================================="
echo
echo_success "系统访问地址:"
echo "  前端界面: http://localhost:5173"
echo "  后端API:  http://localhost:8002"
echo "  API文档:  http://localhost:8002/docs"
echo
echo_success "默认登录账户:"
echo "  用户名: admin"
echo "  密码:   admin123"
echo
echo_warning "注意: 首次登录后请立即修改默认密码"
echo
echo_info "进程信息:"
echo "  后端进程 PID: $BACKEND_PID"
echo "  前端进程 PID: $FRONTEND_PID"
echo
echo_info "日志文件位置:"
echo "  后端日志: $PROJECT_ROOT/logs/backend.log"
echo "  前端日志: $PROJECT_ROOT/logs/frontend.log"
echo
echo_info "停止服务命令:"
echo "  ./stop-services.sh"
echo
echo_success "系统已在后台运行，可以关闭此终端"