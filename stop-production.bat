@echo off
chcp 65001 > nul
cls

echo ====================================================
echo 润扬大桥运维文档管理系统 - 停止生产服务
echo ====================================================
echo.

echo [%time%] 开始停止所有服务...
echo.

:: ============= 停止Python后端服务 =============
echo [步骤 1/3] 停止Python后端服务...

:: 查找并终止Python进程
for /f "tokens=2 delims=," %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "python.exe"') do (
    set "pid=%%i"
    set pid=!pid:"=!
    echo [信息] 发现Python进程 PID: !pid!
    taskkill /pid !pid! /f > nul 2>&1
    if not errorlevel 1 (
        echo [成功] Python进程 !pid! 已终止
    )
)

:: 检查特定端口的进程
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8002 "') do (
    set "pid=%%i"
    if not "!pid!"=="" (
        echo [信息] 终止占用端口8002的进程 PID: !pid!
        taskkill /pid !pid! /f > nul 2>&1
        if not errorlevel 1 (
            echo [成功] 端口8002进程已终止
        )
    )
)

:: ============= 停止Node.js前端服务 =============
echo.
echo [步骤 2/3] 停止Node.js前端服务...

:: 查找并终止Node.js进程
for /f "tokens=2 delims=," %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| findstr "node.exe"') do (
    set "pid=%%i"
    set pid=!pid:"=!
    echo [信息] 发现Node.js进程 PID: !pid!
    taskkill /pid !pid! /f > nul 2>&1
    if not errorlevel 1 (
        echo [成功] Node.js进程 !pid! 已终止
    )
)

:: 检查前端端口的进程
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":5173 "') do (
    set "pid=%%i"
    if not "!pid!"=="" (
        echo [信息] 终止占用端口5173的进程 PID: !pid!
        taskkill /pid !pid! /f > nul 2>&1
        if not errorlevel 1 (
            echo [成功] 端口5173进程已终止
        )
    )
)

:: ============= 清理临时文件 =============
echo.
echo [步骤 3/3] 清理临时文件...

:: 清理后端临时文件
if exist "backend\task_status\*" (
    del /q "backend\task_status\*" > nul 2>&1
    echo [信息] 已清理后端临时状态文件
)

:: 清理日志锁文件
if exist "backend\logs\*.lock" (
    del /q "backend\logs\*.lock" > nul 2>&1
    echo [信息] 已清理日志锁文件
)

:: ============= 检查服务状态 =============
echo.
echo ====================================================
echo                   服务停止结果
echo ====================================================
echo.

:: 检查后端端口状态
netstat -an | findstr ":8002 " > nul
if errorlevel 1 (
    echo ✅ 后端服务 (端口8002) 已停止
) else (
    echo ❌ 后端服务 (端口8002) 仍在运行
)

:: 检查前端端口状态
netstat -an | findstr ":5173 " > nul
if errorlevel 1 (
    echo ✅ 前端服务 (端口5173) 已停止
) else (
    echo ❌ 前端服务 (端口5173) 仍在运行
)

echo.
echo ====================================================
echo                   清理完成
echo ====================================================
echo.

:: 检查是否还有相关进程
set "has_python=0"
set "has_node=0"

tasklist /fi "imagename eq python.exe" | findstr "python.exe" > nul
if not errorlevel 1 set "has_python=1"

tasklist /fi "imagename eq node.exe" | findstr "node.exe" > nul
if not errorlevel 1 set "has_node=1"

if %has_python%==1 (
    echo ⚠️  警告: 仍有Python进程在运行（可能是其他应用）
)

if %has_node%==1 (
    echo ⚠️  警告: 仍有Node.js进程在运行（可能是其他应用）
)

if %has_python%==0 if %has_node%==0 (
    echo ✅ 所有润扬大桥系统相关服务已完全停止
)

echo.
echo ====================================================
echo                   操作指南
echo ====================================================
echo.
echo 🔄 重新启动系统: 运行 start-production.bat 或 start-production-simple.bat
echo 🔍 检查服务状态: 运行 check-service-health.bat
echo 📝 查看系统日志: 检查 backend\logs\ 目录
echo 🗃️  数据库备份: backend\yunwei_docs.db
echo.

echo [%time%] 服务停止操作完成！
echo.
echo 按任意键退出...
pause > nul