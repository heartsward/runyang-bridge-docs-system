#!/usr/bin/env bash
# 停止本项目服务（按端口精确定位，不触碰机器上其他 Python/Node 进程）
# 用法: ./stop-services.sh
set -u

BACKEND_PORT=8002
FRONTEND_PORT=5173

echo "=========================================="
echo "  Stopping Services (port-based)..."
echo "=========================================="
echo "只停止本项目占用的端口（$BACKEND_PORT 后端 / $FRONTEND_PORT 前端）。"
echo "不会触碰机器上其他 Python / Node.js 进程（如 IDE）。"
echo

stop_port() {
    local port="$1" name="$2"
    local pids
    # 优先 lsof；没有则用 ss / fuser 兜底
    if command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -t -iTCP:"$port" -sTCP:LISTEN 2>/dev/null)
    elif command -v ss >/dev/null 2>&1; then
        pids=$(ss -ltnp 2>/dev/null | grep ":$port " | grep -oE 'pid=[0-9]+' | cut -d= -f2 | sort -u)
    else
        pids=$(fuser "$port"/tcp 2>/dev/null | tr -s ' ' '\n')
    fi

    if [ -z "$pids" ]; then
        echo "[$name / 端口 $port] 没有监听进程"
        return 0
    fi

    local stopped=0
    for pid in $pids; do
        echo "[$name / 端口 $port] 停止 PID $pid ..."
        if kill "$pid" 2>/dev/null; then
            sleep 1
            # 没退出再强制
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null
            fi
            echo "  OK"
            stopped=$((stopped + 1))
        else
            echo "  已退出或无法停止（忽略）"
        fi
    done
    return 0
}

stop_port "$BACKEND_PORT" "后端"
stop_port "$FRONTEND_PORT" "前端"

echo
echo "=========================================="
echo "  DONE"
echo "=========================================="
echo
echo "查看端口是否释放:  lsof -i :$BACKEND_PORT -i :$FRONTEND_PORT"
echo "重新启动:          ./start-services.sh"
echo
