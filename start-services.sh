#!/bin/bash

echo "=========================================="
echo "   润扬大桥运维文档管理系统 - 启动服务"
echo "=========================================="
echo

echo "[检查] 验证环境..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python环境异常，请先运行 ./install-environment.sh"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js环境异常，请先运行 ./install-environment.sh"
    exit 1
fi

echo "✅ 环境检查通过"

# 确定Python命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo
echo "[1/3] 启动后端API服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 找不到虚拟环境，请先运行 ./install-environment.sh"
    exit 1
fi

if [ ! -f database_integrated_server.py ]; then
    echo "❌ 找不到后端服务文件"
    exit 1
fi

echo "正在启动后端服务 (端口: 8002)..."
# 创建logs目录
mkdir -p ../logs
# 激活虚拟环境并启动服务
nohup bash -c "source venv/bin/activate && python database_integrated_server.py" > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

if [ $? -eq 0 ]; then
    echo $BACKEND_PID > ../logs/backend.pid
    echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 等待后端启动
sleep 5

echo
echo "[2/3] 启动前端开发服务..."
cd ../frontend
if [ ! -f package.json ]; then
    echo "❌ 找不到前端配置文件"
    exit 1
fi

echo "正在启动前端服务 (端口: 5173)..."
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

if [ $? -eq 0 ]; then
    echo $FRONTEND_PID > ../logs/frontend.pid
    echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
else
    echo "❌ 前端服务启动失败"
    exit 1
fi

# 等待前端启动
sleep 3

echo
echo "[3/3] 服务启动完成！"
echo

cd ..

echo "=========================================="
echo "   🎉 服务已启动！"
echo "=========================================="
echo
echo "📍 访问地址:"
echo "   前端界面: http://localhost:5173"
echo "   后端API:  http://localhost:8002"
echo "   API文档:  http://localhost:8002/docs"
echo
echo "🔐 默认登录:"
echo "   管理员: admin / admin123"
echo "   用户:   user / user123"
echo
echo "💡 提示:"
echo "   - 服务已在后台运行"
echo "   - 日志文件在 logs/ 目录"
echo "   - 使用 ./stop-services.sh 停止服务"
echo

# 检查服务是否正常启动
echo "[检查] 等待服务完全启动..."
sleep 10

echo "检查后端服务状态..."
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "⚠️  后端服务可能启动中，请稍等片刻"
    echo "   查看日志: tail -f logs/backend.log"
fi

echo "检查前端服务状态..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ 前端服务启动成功"
else
    echo "⚠️  前端服务可能启动中，请稍等片刻"
    echo "   查看日志: tail -f logs/frontend.log"
fi

echo
echo "📊 进程信息:"
echo "   后端PID: $BACKEND_PID (保存在 logs/backend.pid)"
echo "   前端PID: $FRONTEND_PID (保存在 logs/frontend.pid)"
echo
echo "🚀 系统启动完成！请在浏览器中访问 http://localhost:5173"

# 如果在桌面环境中，尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    sleep 2
    xdg-open http://localhost:5173 &> /dev/null
elif command -v open &> /dev/null; then
    sleep 2
    open http://localhost:5173 &> /dev/null
fi