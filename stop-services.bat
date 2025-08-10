@echo off
chcp 65001 > nul
cls
echo ====================================================
echo        润扬大桥运维文档管理系统 - 停止服务
echo ====================================================
echo.

echo [信息] 正在停止润扬大桥运维文档管理系统服务...
echo.

REM 停止前端服务 (端口 5173)
echo [步骤 1/2] 停止前端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    echo [信息] 终止前端进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM 停止后端服务 (端口 8002)
echo [步骤 2/2] 停止后端服务...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8002" ^| find "LISTENING"') do (
    echo [信息] 终止后端进程 PID: %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM 停止可能残留的Python和Node进程
echo.
echo [信息] 清理残留进程...
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq 润扬大桥运维系统-后端*" >nul 2>&1
taskkill /F /IM "node.exe" /FI "WINDOWTITLE eq 润扬大桥运维系统-前端*" >nul 2>&1
taskkill /F /IM "cmd.exe" /FI "WINDOWTITLE eq 润扬大桥运维系统-*" >nul 2>&1

echo.
echo ====================================================
echo                   停止完成！
echo ====================================================
echo.
echo [信息] 润扬大桥运维文档管理系统服务已全部停止
echo.
pause