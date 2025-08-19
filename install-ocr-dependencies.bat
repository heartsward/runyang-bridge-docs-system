@echo off
chcp 65001 >nul

echo ==========================================
echo    OCR依赖包安装脚本
echo ==========================================
echo.

echo 此脚本将安装PDF乱码修复所需的OCR依赖包
echo.

echo 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 检查虚拟环境...
if exist "backend\venv\Scripts\activate.bat" (
    echo 使用虚拟环境...
    cd backend
    call venv\Scripts\activate.bat
) else (
    echo 使用全局Python环境...
)

echo.
echo 升级pip...
python -m pip install --upgrade pip

echo.
echo 安装OCR核心依赖...
echo 1. 安装pytesseract（OCR引擎接口）...
pip install pytesseract>=0.3.10

if errorlevel 1 (
    echo pytesseract安装失败，尝试替代方法...
    pip install --no-cache-dir pytesseract
)

echo.
echo 2. 安装pdf2image（PDF转图像）...
pip install pdf2image>=1.16.0

if errorlevel 1 (
    echo pdf2image安装失败，尝试替代方法...
    pip install --no-cache-dir pdf2image
)

echo.
echo 3. 安装opencv-python-headless（图像处理）...
pip install opencv-python-headless>=4.7.0

if errorlevel 1 (
    echo opencv安装失败，尝试替代方法...
    pip install --no-cache-dir opencv-python-headless
)

echo.
echo 4. 安装numpy（数值计算）...
pip install numpy>=1.21.0

echo.
echo 验证安装结果...
echo ==========================================

python -c "
try:
    import pytesseract
    print('✓ pytesseract: 安装成功')
except ImportError:
    print('✗ pytesseract: 安装失败')

try:
    import pdf2image
    print('✓ pdf2image: 安装成功')
except ImportError:
    print('✗ pdf2image: 安装失败')

try:
    import cv2
    print('✓ opencv: 安装成功')
except ImportError:
    print('✗ opencv: 安装失败')

try:
    import numpy
    print('✓ numpy: 安装成功')
except ImportError:
    print('✗ numpy: 安装失败')
"

echo.
echo ==========================================
echo 检查Tesseract程序...

if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo ✓ Tesseract程序已安装: C:\Program Files\Tesseract-OCR\tesseract.exe
) else (
    echo ⚠ Tesseract程序未找到
    echo.
    echo 需要安装Tesseract OCR程序:
    echo 1. 访问: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. 下载Windows安装包
    echo 3. 安装到默认路径: C:\Program Files\Tesseract-OCR\
    echo.
)

if exist "backend\venv\Scripts\activate.bat" (
    call venv\Scripts\deactivate.bat
    cd ..
)

echo.
echo ==========================================
echo OCR依赖安装完成！
echo ==========================================
echo.
echo 接下来请运行 diagnose-ocr.py 验证OCR功能
echo.
pause