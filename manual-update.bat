@echo off
chcp 65001 >nul
echo ==========================================
echo    手动更新脚本（无需Git）
echo ==========================================
echo.

set BACKUP_DIR=backup_manual_%date:~0,4%%date:~5,2%%date:~8,2%
set BACKUP_DIR=%BACKUP_DIR: =0%

echo 此脚本适用于无Git环境的手动更新
echo.

echo 第一步：创建备份
mkdir %BACKUP_DIR% 2>nul

if exist "backend\yunwei_docs.db" (
    copy "backend\yunwei_docs.db" "%BACKUP_DIR%\"
    echo ✓ 数据库已备份
)

if exist "backend\users_data.json" (
    copy "backend\users_data.json" "%BACKUP_DIR%\"
    echo ✓ 用户数据已备份
)

if exist "backend\assets_data.json" (
    copy "backend\assets_data.json" "%BACKUP_DIR%\"
    echo ✓ 资产数据已备份
)

echo.
echo 第二步：停止当前服务
call stop-services.bat >nul 2>&1
echo ✓ 服务已停止

echo.
echo ==========================================
echo 现在需要手动操作：
echo ==========================================
echo.
echo 1. 打开浏览器访问:
echo    https://github.com/heartsward/runyang-bridge-docs-system
echo.
echo 2. 点击绿色的 "Code" 按钮
echo.
echo 3. 选择 "Download ZIP"
echo.
echo 4. 下载完成后，解压ZIP文件
echo.
echo 5. 将以下关键文件复制到当前目录，覆盖原文件:
echo    - backend\app\services\enhanced_content_extractor.py
echo    - backend\fix_datetime.py
echo    - diagnose-ocr.py
echo    - test-ocr-processing.py
echo.
echo 6. 完成文件复制后，按任意键继续...
pause

echo.
echo 第三步：应用修复
if exist "backend\fix_datetime.py" (
    cd backend
    python fix_datetime.py
    cd ..
    echo ✓ datetime修复已应用
) else (
    echo ⚠ 警告：fix_datetime.py文件未找到，请确保已正确复制
)

echo.
echo 第四步：验证修复
if exist "diagnose-ocr.py" (
    echo 测试OCR功能...
    python diagnose-ocr.py | findstr "结论"
) else (
    echo ⚠ 警告：diagnose-ocr.py文件未找到
)

echo.
echo 第五步：重启服务
if exist start-production.bat (
    start /min start-production.bat
    echo ✓ 生产服务已启动
) else (
    start /min start-services.bat
    echo ✓ 开发服务已启动
)

echo.
echo ==========================================
echo 手动更新完成！
echo ==========================================
echo.
echo 备份位置: %BACKUP_DIR%
echo 服务地址: http://localhost:8000
echo.
echo 请测试PDF文档上传，验证乱码问题是否解决
echo.
pause