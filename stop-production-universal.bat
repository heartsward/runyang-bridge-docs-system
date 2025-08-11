@echo off
chcp 65001 > nul
cls

echo ========================================
echo     润扬大桥运维文档管理系统 - 停止服务
echo ========================================
echo.

echo [信息] 正在停止系统服务...

REM 查找并终止Python进程（后端）
echo [步骤 1/2] 停止后端服务...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq python.exe" /FO TABLE /NH 2^>nul ^| findstr database_integrated_server') do (
    echo [信息] 发现后端进程 PID: %%i
    taskkill /PID %%i /F >nul 2>&1
    if not errorlevel 1 (
        echo [成功] 后端服务已停止
    )
)

REM 查找并终止Node.js进程（前端）
echo [步骤 2/2] 停止前端服务...
for /f "tokens=2" %%i in ('tasklist /FI "IMAGENAME eq node.exe" /FO TABLE /NH 2^>nul ^| findstr "npm run dev\|vite"') do (
    echo [信息] 发现前端进程 PID: %%i
    taskkill /PID %%i /F >nul 2>&1
    if not errorlevel 1 (
        echo [成功] 前端服务已停止
    )
)

REM 清理PID文件
if exist backend.pid del backend.pid >nul 2>&1
if exist frontend.pid del frontend.pid >nul 2>&1

echo.
echo ========================================
echo              服务已停止
echo ========================================
echo.
echo [完成] 所有服务进程已终止
echo [提示] 如需重新启动，请运行 start-production-universal.bat
echo.
pause