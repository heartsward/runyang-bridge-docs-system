#!/bin/bash

echo "=========================================="
echo "   润扬大桥运维文档管理系统 - 停止服务"
echo "=========================================="
echo

echo "[1/2] 停止后端服务..."
if [ -f logs/backend.pid ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "正在停止后端服务 (PID: $BACKEND_PID)..."
        kill -TERM $BACKEND_PID
        sleep 2
        # 如果进程仍然运行，强制终止
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill -KILL $BACKEND_PID
        fi
        echo "✅ 后端服务已停止"
    else
        echo "ℹ️  后端服务未运行"
    fi
    rm -f logs/backend.pid
else
    echo "ℹ️  未找到后端服务PID文件，尝试按进程名停止..."
    pkill -f "python.*database_integrated_server.py" 2>/dev/null && echo "✅ 后端服务已停止" || echo "ℹ️  未找到后端服务进程"
fi

echo
echo "[2/2] 停止前端服务..."
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "正在停止前端服务 (PID: $FRONTEND_PID)..."
        kill -TERM $FRONTEND_PID
        sleep 2
        # 如果进程仍然运行，强制终止
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill -KILL $FRONTEND_PID
        fi
        echo "✅ 前端服务已停止"
    else
        echo "ℹ️  前端服务未运行"
    fi
    rm -f logs/frontend.pid
else
    echo "ℹ️  未找到前端服务PID文件，尝试按进程名停止..."
    pkill -f "npm.*run.*dev" 2>/dev/null && echo "✅ 前端服务已停止" || echo "ℹ️  未找到前端服务进程"
fi

echo
echo "=========================================="
echo "   ✅ 所有服务已停止！"
echo "=========================================="
echo
echo "💡 提示:"
echo "   - 所有相关进程已终止"
echo "   - 端口8002和5173现已释放"
echo "   - 可以使用 ./start-services.sh 重新启动服务"
echo

# 额外清理：停止可能遗留的相关进程
echo "[清理] 检查遗留进程..."
REMAINING_PROCESSES=$(pgrep -f "database_integrated_server\|npm.*dev" | wc -l)
if [ $REMAINING_PROCESSES -gt 0 ]; then
    echo "发现 $REMAINING_PROCESSES 个遗留进程，正在清理..."
    pkill -f "database_integrated_server"
    pkill -f "npm.*dev"
    sleep 1
    echo "✅ 清理完成"
fi