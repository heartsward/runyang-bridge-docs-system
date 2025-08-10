@echo off
chcp 65001 > nul
cls
echo ====================================================
echo     润扬大桥运维文档管理系统 - 服务健康检查
echo ====================================================
echo.

echo [信息] 正在检查服务运行状态...
echo.

REM 检查后端服务
echo [步骤 1/3] 检查后端服务 (端口 8002)...
netstat -an | find ":8002" | find "LISTENING" > nul
if errorlevel 1 (
    echo [错误] 后端服务未运行 (端口 8002 未监听)
    set BACKEND_STATUS=停止
) else (
    echo [成功] 后端服务正在运行
    set BACKEND_STATUS=运行中
)

REM 检查前端服务
echo [步骤 2/3] 检查前端服务 (端口 5173)...
netstat -an | find ":5173" | find "LISTENING" > nul
if errorlevel 1 (
    echo [错误] 前端服务未运行 (端口 5173 未监听)
    set FRONTEND_STATUS=停止
) else (
    echo [成功] 前端服务正在运行
    set FRONTEND_STATUS=运行中
)

REM API健康检查
echo [步骤 3/3] 检查API健康状态...
curl -s --max-time 5 http://localhost:8002 > nul 2>&1
if errorlevel 1 (
    echo [警告] 后端API响应异常或超时
    set API_STATUS=异常
) else (
    echo [成功] 后端API响应正常
    set API_STATUS=正常
)

echo.
echo ====================================================
echo                   检查结果
echo ====================================================
echo.
echo 服务状态:
echo   后端服务 (8002): %BACKEND_STATUS%
echo   前端服务 (5173): %FRONTEND_STATUS%
echo   API健康状态:     %API_STATUS%
echo.
echo 访问地址:
echo   前端界面: http://localhost:5173
echo   后端API:  http://localhost:8002
echo   API文档:  http://localhost:8002/docs
echo.

if "%BACKEND_STATUS%"=="运行中" if "%FRONTEND_STATUS%"=="运行中" (
    echo [总体状态] 系统运行正常 ✓
) else (
    echo [总体状态] 系统部分服务异常 ✗
    echo.
    echo 解决建议:
    if not "%BACKEND_STATUS%"=="运行中" echo - 启动后端: cd backend ^&^& python database_integrated_server.py
    if not "%FRONTEND_STATUS%"=="运行中" echo - 启动前端: cd frontend ^&^& npm run dev
)

echo.
pause