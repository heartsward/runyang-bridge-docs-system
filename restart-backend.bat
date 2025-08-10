@echo off
chcp 65001 > nul
echo 重启后端服务...

echo [1/3] 停止现有服务...
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq *backend*" > nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8002" ^| find "LISTENING"') do (
    taskkill /F /PID %%a > nul 2>&1
)

echo [2/3] 等待端口释放...
timeout /t 3 > nul

echo [3/3] 启动新的服务实例...
cd backend
start "Backend Service" cmd /k "python database_integrated_server.py"

echo 完成！后端服务正在重新启动...
timeout /t 2 > nul