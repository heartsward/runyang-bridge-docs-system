#!/bin/bash

echo "=========================================="
echo "   润扬大桥运维文档管理系统 - 环境安装"
echo "=========================================="
echo

echo "[1/6] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python未安装，请先安装Python 3.8或更高版本"
        echo "   Ubuntu/Debian: sudo apt-get install python3 python3-pip"
        echo "   CentOS/RHEL: sudo yum install python3 python3-pip"
        echo "   macOS: brew install python3"
        exit 1
    else
        python --version
        PYTHON_CMD="python"
    fi
else
    python3 --version
    PYTHON_CMD="python3"
fi

echo
echo "[2/6] 检查Node.js环境..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js 16或更高版本"
    echo "   官网下载: https://nodejs.org/"
    echo "   或使用包管理器安装"
    exit 1
fi
node --version
npm --version

echo
echo "[3/6] 创建Python虚拟环境并安装后端依赖..."
cd backend

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 虚拟环境创建失败，请确保安装了python3-venv"
        echo "   运行: sudo apt install python3-venv"
        exit 1
    fi
    echo "✅ 虚拟环境创建成功"
fi

# 激活虚拟环境并安装依赖
if [ -f requirements.txt ]; then
    echo "激活虚拟环境并安装依赖..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo "❌ 后端依赖安装失败"
        deactivate
        exit 1
    fi
    echo "✅ 后端依赖安装成功"
    deactivate
else
    echo "❌ 找不到requirements.txt文件"
    exit 1
fi

echo
echo "[4/6] 安装前端Node.js依赖..."
cd ../frontend
if [ -f package.json ]; then
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 前端依赖安装失败"
        exit 1
    fi
    echo "✅ 前端依赖安装成功"
else
    echo "❌ 找不到package.json文件"
    exit 1
fi

echo
echo "[5/6] 检查LibreOffice安装..."
if command -v libreoffice &> /dev/null; then
    echo "✅ LibreOffice已安装"
else
    echo "⚠️  LibreOffice未安装，部分文档提取功能可能不可用"
    echo "   建议安装LibreOffice以支持Word、Excel文档内容提取"
    echo "   Ubuntu/Debian: sudo apt-get install libreoffice"
    echo "   CentOS/RHEL: sudo yum install libreoffice"
    echo "   macOS: brew install --cask libreoffice"
fi

echo
echo "[6/6] 初始化数据库..."
cd ../backend
source venv/bin/activate
python -c "
from app.db.database import engine
from app.models import user, document, asset
try:
    user.Base.metadata.create_all(bind=engine)
    document.Base.metadata.create_all(bind=engine) 
    asset.Base.metadata.create_all(bind=engine)
    print('✅ 数据库初始化成功')
except Exception as e:
    print(f'❌ 数据库初始化失败: {e}')
"
deactivate

cd ..

echo
echo "=========================================="
echo "   🎉 环境安装完成！"
echo "=========================================="
echo
echo "💡 接下来请运行以下命令启动服务:"
echo "   ./start-services.sh     # 启动前后端服务"
echo
echo "📖 更多信息请查看: docs/部署指南.md"
echo

# 给脚本添加执行权限
chmod +x start-services.sh 2>/dev/null || true