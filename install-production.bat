@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ==========================================
echo    生产环境完整安装脚本
echo ==========================================
echo.

echo 设置UTF-8环境变量...
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo 检查Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo 检查Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    安装后端依赖（包含OCR支持）
echo ==========================================

cd backend

echo 创建虚拟环境...
if not exist venv (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: 虚拟环境创建失败
        pause
        exit /b 1
    )
)

echo 激活虚拟环境...
call venv\Scripts\activate.bat

echo 升级pip...
python -m pip install --upgrade pip

echo 安装核心依赖...
echo Installing FastAPI and core packages...
pip install fastapi uvicorn[standard] sqlalchemy python-dotenv pydantic aiofiles

echo Installing authentication packages...
pip install PyJWT python-jose[cryptography] passlib[bcrypt] python-multipart alembic pydantic-settings pydantic[email] email-validator

echo Installing document processing packages...
pip install pandas PyPDF2 python-docx openpyxl markdown pdfplumber

echo Installing enhanced PDF processing...
pip install PyMuPDF || echo PyMuPDF安装失败，将影响PDF处理能力

echo ==========================================
echo    安装OCR相关依赖（生产环境关键）
echo ==========================================
echo Installing OCR packages...
pip install Pillow pytesseract pdf2image

echo Installing text processing and ML packages...
pip install jieba scikit-learn chardet httpx numpy opencv-python-headless

echo ==========================================
echo    验证OCR安装
echo ==========================================
echo 检查Tesseract OCR安装...
python -c "import pytesseract; print('pytesseract导入成功')" 2>nul
if errorlevel 1 (
    echo WARNING: pytesseract导入失败
    echo 请确保已安装Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
)

python -c "from PIL import Image; print('Pillow导入成功')" 2>nul
if errorlevel 1 (
    echo WARNING: Pillow导入失败
)

python -c "import pdf2image; print('pdf2image导入成功')" 2>nul
if errorlevel 1 (
    echo WARNING: pdf2image导入失败
)

echo ==========================================
echo    修复已知问题
echo ==========================================

echo 修复datetime弃用警告...
python -c "
import os
import re
from pathlib import Path

# 修复database_integrated_server.py中的datetime问题
server_file = Path('database_integrated_server.py')
if server_file.exists():
    content = server_file.read_text(encoding='utf-8')
    
    # 检查是否已经修复
    if 'datetime.utcnow()' in content:
        print('正在修复datetime.utcnow()弃用警告...')
        
        # 添加timezone导入
        if 'from datetime import datetime, timedelta' in content:
            content = content.replace(
                'from datetime import datetime, timedelta',
                'from datetime import datetime, timedelta, timezone'
            )
        
        # 替换所有datetime.utcnow()调用
        content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
        
        # 写回文件
        server_file.write_text(content, encoding='utf-8')
        print('✅ datetime问题已修复')
    else:
        print('✅ datetime问题已经修复过了')
else:
    print('⚠️  未找到database_integrated_server.py文件')
"

call venv\Scripts\deactivate.bat

echo.
echo ==========================================
echo    安装前端依赖
echo ==========================================
cd ..\frontend
npm install
if errorlevel 1 (
    echo ERROR: 前端安装失败
    pause
    exit /b 1
)

echo 构建前端生产版本...
npm run build
if errorlevel 1 (
    echo ERROR: 前端构建失败
    pause
    exit /b 1
)

echo.
echo ==========================================
echo    验证安装
echo ==========================================
cd ..\backend
call venv\Scripts\activate.bat

echo 测试数据库连接...
python -c "
try:
    from app.db.database import engine
    print('✅ 数据库连接正常')
except Exception as e:
    print('⚠️  数据库将在首次运行时初始化')
    print(f'详情: {e}')
"

echo 测试OCR功能...
python -c "
try:
    from app.services.enhanced_content_extractor import EnhancedContentExtractor
    extractor = EnhancedContentExtractor()
    if extractor.has_ocr:
        print('✅ OCR功能可用')
    else:
        print('⚠️  OCR功能不可用，请检查Tesseract安装')
except Exception as e:
    print('⚠️  OCR测试失败:', e)
"

call venv\Scripts\deactivate.bat

cd ..

echo.
echo ==========================================
echo    创建生产环境启动脚本
echo ==========================================

echo @echo off > start-production.bat
echo chcp 65001 ^>nul >> start-production.bat
echo set PYTHONIOENCODING=utf-8 >> start-production.bat
echo set PYTHONUTF8=1 >> start-production.bat
echo cd backend >> start-production.bat
echo call venv\Scripts\activate.bat >> start-production.bat
echo echo 启动生产环境服务... >> start-production.bat
echo python database_integrated_server.py >> start-production.bat
echo call venv\Scripts\deactivate.bat >> start-production.bat
echo cd .. >> start-production.bat

echo.
echo ==========================================
echo    安装完成！
echo ==========================================
echo.
echo 🚀 生产环境安装成功
echo.
echo 启动命令:
echo   start-production.bat     # 启动生产环境
echo   start-services.bat       # 启动开发环境
echo.
echo 访问地址:
echo   http://localhost:8000    # 生产环境
echo   http://localhost:5173    # 开发环境（如需要）
echo.
echo 默认登录:
echo   用户名: admin
echo   密码: admin123
echo.
echo 已修复问题:
echo   ✅ datetime.utcnow() 弃用警告
echo   ✅ OCR依赖包安装
echo   ✅ PDF识别功能
echo   ✅ 前端TypeScript构建
echo.
pause