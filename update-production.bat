@echo off
chcp 65001 >nul
echo ==========================================
echo    生产环境安全更新脚本
echo ==========================================
echo.

set BACKUP_DIR=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set BACKUP_DIR=%BACKUP_DIR: =0%

echo 1. 创建备份目录: %BACKUP_DIR%
mkdir %BACKUP_DIR%

echo.
echo 2. 备份当前配置和数据...
if exist "backend\yunwei_docs.db" (
    copy "backend\yunwei_docs.db" "%BACKUP_DIR%\yunwei_docs.db.backup"
    echo   ✓ 数据库已备份
)

if exist "backend\users_data.json" (
    copy "backend\users_data.json" "%BACKUP_DIR%\users_data.json.backup"
    echo   ✓ 用户数据已备份
)

if exist "backend\assets_data.json" (
    copy "backend\assets_data.json" "%BACKUP_DIR%\assets_data.json.backup"
    echo   ✓ 资产数据已备份
)

if exist "backend\.env" (
    copy "backend\.env" "%BACKUP_DIR%\.env.backup"
    echo   ✓ 环境配置已备份
)

if exist "backend\logs" (
    xcopy "backend\logs" "%BACKUP_DIR%\logs\" /E /I >nul 2>&1
    echo   ✓ 日志文件已备份
)

echo.
echo 3. 停止当前服务...
call stop-services.bat >nul 2>&1

echo.
echo 4. 拉取最新代码...
git status
echo.
echo 当前分支状态：
git log --oneline -3

echo.
echo 准备更新，按任意键继续（Ctrl+C 取消）...
pause >nul

git fetch origin
git pull origin main

if errorlevel 1 (
    echo ERROR: Git更新失败
    echo 请检查网络连接或Git配置
    pause
    exit /b 1
)

echo.
echo 5. 检查更新内容...
git log --oneline -5

echo.
echo 6. 更新Python依赖（如有需要）...
cd backend

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    
    echo 检查是否需要安装新依赖...
    python -c "
try:
    import pytesseract, pdf2image
    from PIL import Image
    print('OCR依赖检查: 正常')
except ImportError as e:
    print(f'需要安装依赖: {e}')
    "
    
    echo 运行datetime修复...
    python fix_datetime.py
    
    call venv\Scripts\deactivate.bat
) else (
    echo WARNING: 虚拟环境不存在，请检查安装
)

cd ..

echo.
echo 7. 更新前端（如有需要）...
cd frontend
if exist node_modules (
    echo 检查前端依赖...
    npm run build >nul 2>&1
    if errorlevel 1 (
        echo 重新构建前端...
        npm install
        npm run build
    ) else (
        echo 前端构建正常
    )
) else (
    echo WARNING: 前端依赖不存在，请检查安装
)
cd ..

echo.
echo 8. 验证修复...
echo 测试OCR功能...
python diagnose-ocr.py | findstr "结论\|OCR功能\|乱码检测"

echo.
echo 9. 启动服务...
if exist start-production.bat (
    echo 使用生产环境启动...
    start /min start-production.bat
    echo 服务已启动，等待5秒...
    timeout /t 5 /nobreak >nul
) else (
    echo 使用开发环境启动...
    start /min start-services.bat
    echo 服务已启动，等待5秒...
    timeout /t 5 /nobreak >nul
)

echo.
echo 10. 验证服务状态...
echo 检查后端服务...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo WARNING: 后端服务可能未正常启动
    echo 请检查日志：backend\logs\
) else (
    echo ✓ 后端服务正常
)

echo.
echo ==========================================
echo    更新完成！
echo ==========================================
echo.
echo 备份位置: %BACKUP_DIR%
echo 服务地址: http://localhost:8000
echo 前端地址: http://localhost:5173 (如果使用开发模式)
echo.
echo 更新内容:
echo - 修复PDF乱码检测算法
echo - 提高OCR触发灵敏度
echo - 改进乱码识别准确性
echo.
echo 如遇问题，可使用以下命令回滚:
echo   git reset --hard HEAD~1
echo   复制备份文件回原位置
echo.
pause