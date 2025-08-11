#!/bin/bash

# 设置UTF-8编码
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

clear

echo "===================================================="
echo "   润扬大桥运维文档管理系统 - 通用部署启动脚本"
echo "===================================================="
echo

# 获取本机IP地址函数
get_local_ip() {
    # 尝试多种方法获取IP
    if command -v hostname >/dev/null 2>&1; then
        local_ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    
    if [ -z "$local_ip" ] && command -v ip >/dev/null 2>&1; then
        local_ip=$(ip route get 1 2>/dev/null | awk '{print $NF;exit}')
    fi
    
    if [ -z "$local_ip" ] && command -v ifconfig >/dev/null 2>&1; then
        local_ip=$(ifconfig | grep -E 'inet.*broadcast' | grep -v '127.0.0.1' | awk '{print $2}' | head -n1)
    fi
    
    if [ -z "$local_ip" ]; then
        local_ip="127.0.0.1"
    fi
    
    echo "$local_ip"
}

# 获取本机IP
LOCAL_IP=$(get_local_ip)
echo "[信息] 自动检测到本机IP: $LOCAL_IP"

# 检查命令行参数
if [ ! -z "$1" ]; then
    LOCAL_IP="$1"
    echo "[信息] 使用指定IP地址: $LOCAL_IP"
fi

echo "[信息] 系统将配置为允许以下访问方式:"
echo "  - 本地访问: http://localhost:5173"
echo "  - 局域网访问: http://$LOCAL_IP:5173"
echo "  - API接口: http://$LOCAL_IP:8002"
echo

# 检查Python环境
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo "[错误] 未找到 Python，请先安装 Python 3.8+ 版本"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "macOS: brew install python3"
    exit 1
fi

# 优先使用python3
PYTHON_CMD="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

# 检查Node.js环境
if ! command -v node >/dev/null 2>&1; then
    echo "[错误] 未找到 Node.js，请先安装 Node.js 16+ 版本"
    echo "下载地址: https://nodejs.org/"
    echo "Ubuntu/Debian: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "CentOS/RHEL: curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash - && sudo yum install -y nodejs"
    echo "macOS: brew install node"
    exit 1
fi

# 设置环境变量 - 使用新的CORS配置系统
export CORS_MODE="auto"
export CORS_ORIGINS="http://$LOCAL_IP:5173,http://$LOCAL_IP:5174,http://$LOCAL_IP:8002"
export CORS_AUTO_DETECT="true"
export CORS_INCLUDE_LOCALHOST="true"
export SERVER_HOST="$LOCAL_IP"

echo "[信息] 环境配置:"
echo "  CORS_MODE=$CORS_MODE"
echo "  CORS_ORIGINS=$CORS_ORIGINS"
echo "  CORS_AUTO_DETECT=$CORS_AUTO_DETECT"
echo "  SERVER_HOST=$SERVER_HOST"
echo

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 安装Python依赖
echo "[步骤 1/6] 安装Python依赖..."
cd "$SCRIPT_DIR/backend"

if [ ! -f "requirements.txt" ]; then
    echo "[错误] 未找到 backend/requirements.txt 文件"
    exit 1
fi

$PYTHON_CMD -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[错误] Python依赖安装失败"
    exit 1
fi

# 安装Node.js依赖
echo
echo "[步骤 2/6] 安装Node.js依赖..."
cd "$SCRIPT_DIR/frontend"

if [ ! -f "package.json" ]; then
    echo "[错误] 未找到 frontend/package.json 文件"
    exit 1
fi

npm install
if [ $? -ne 0 ]; then
    echo "[错误] Node.js依赖安装失败"
    exit 1
fi

# 创建环境配置文件
echo
echo "[步骤 3/6] 配置环境文件..."
cd "$SCRIPT_DIR/backend"

# 创建后端环境配置
cat > .env << EOF
# 润扬大桥运维文档管理系统 - 后端配置
PROJECT_NAME=运维文档管理系统
VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-production-secret-key-change-this-in-production
DATABASE_URL=sqlite:///./yunwei_docs.db
CORS_MODE=$CORS_MODE
CORS_ORIGINS=$CORS_ORIGINS
CORS_AUTO_DETECT=$CORS_AUTO_DETECT
CORS_INCLUDE_LOCALHOST=$CORS_INCLUDE_LOCALHOST
EOF

echo "[成功] 后端环境配置已生成"

cd "$SCRIPT_DIR/frontend"

# 创建前端环境配置
cat > .env << EOF
# 润扬大桥运维文档管理系统 - 前端配置
VITE_API_BASE_URL=http://$LOCAL_IP:8002
VITE_APP_TITLE=润扬大桥运维文档管理系统
VITE_APP_VERSION=1.0.0
VITE_MAX_FILE_SIZE=10485760
VITE_BUILD_SOURCEMAP=false
VITE_BUILD_MINIFY=true
EOF

echo "[成功] 前端环境配置已生成"

# 构建前端
echo
echo "[步骤 4/6] 构建前端应用..."
npm run build
if [ $? -ne 0 ]; then
    echo "[错误] 前端构建失败"
    exit 1
fi

# 启动后端服务
echo
echo "[步骤 5/6] 启动后端服务..."
cd "$SCRIPT_DIR/backend"

echo "[信息] 正在启动后端服务..."
export CORS_MODE="$CORS_MODE"
export CORS_ORIGINS="$CORS_ORIGINS"
export CORS_AUTO_DETECT="$CORS_AUTO_DETECT"
export CORS_INCLUDE_LOCALHOST="$CORS_INCLUDE_LOCALHOST"
nohup $PYTHON_CMD database_integrated_server.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

# 创建日志目录
mkdir -p "$SCRIPT_DIR/logs"

echo "[信息] 后端服务已启动 (PID: $BACKEND_PID)"
echo "[信息] 后端日志: $SCRIPT_DIR/logs/backend.log"

# 等待后端启动
echo "[信息] 等待后端服务启动..."
sleep 5

# 启动前端服务
echo
echo "[步骤 6/6] 启动前端服务..."
cd "$SCRIPT_DIR/frontend"

echo "[信息] 正在启动前端开发服务器..."
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "[信息] 前端服务已启动 (PID: $FRONTEND_PID)"
echo "[信息] 前端日志: $SCRIPT_DIR/logs/frontend.log"

# 保存进程ID
echo "$BACKEND_PID" > "$SCRIPT_DIR/backend.pid"
echo "$FRONTEND_PID" > "$SCRIPT_DIR/frontend.pid"

echo
echo "===================================================="
echo "                   启动完成！"
echo "===================================================="
echo
echo "系统访问地址:"
echo "  本地访问:   http://localhost:5173"
echo "  局域网访问: http://$LOCAL_IP:5173"
echo "  后端API:   http://$LOCAL_IP:8002"
echo "  API文档:   http://$LOCAL_IP:8002/docs"
echo
echo "默认登录账户:"
echo "  用户名: admin"
echo "  密码:   admin123"
echo
echo "════════════════════════════════════════════════════"
echo "  使用说明:"
echo "  1. 本机访问: 直接使用 localhost 地址"
echo "  2. 其他电脑访问: 使用 $LOCAL_IP 地址"
echo "  3. 如需指定IP: $0 [IP地址]"
echo "  4. 停止服务: ./stop-production.sh"
echo "  5. 查看日志: tail -f logs/backend.log 或 logs/frontend.log"
echo "  6. 生产部署: 修改backend/.env中的SECRET_KEY"
echo "════════════════════════════════════════════════════"
echo
echo "服务已在后台运行，按 Ctrl+C 退出监控模式（服务继续运行）"
echo

# 监控服务状态
while true; do
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "[警告] 后端服务已停止"
        break
    fi
    
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "[警告] 前端服务已停止"  
        break
    fi
    
    sleep 10
done