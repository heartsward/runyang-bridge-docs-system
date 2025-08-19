@echo off
chcp 65001 >nul
echo ==========================================
echo    快速更新脚本（仅代码更新）
echo ==========================================
echo.

echo 1. 停止服务...
call stop-services.bat >nul 2>&1

echo.
echo 2. 更新代码...
git pull origin main

if errorlevel 1 (
    echo ERROR: 更新失败
    pause
    exit /b 1
)

echo.
echo 3. 运行修复脚本...
cd backend
python fix_datetime.py
cd ..

echo.
echo 4. 重启服务...
if exist start-production.bat (
    start /min start-production.bat
) else (
    start /min start-services.bat
)

echo.
echo 更新完成！服务已重启
echo 访问: http://localhost:8000
echo.
pause