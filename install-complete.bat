@echo off
chcp 65001 >nul

echo ==========================================
echo    Windows Complete Install Script
echo ==========================================
echo.

echo Checking Python...
set "PYTHON_EXE="
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
) else (
    for /d %%V in ("%USERPROFILE%\.workbuddy\binaries\python\versions\3.*") do if exist "%%V\python.exe" set "PYTHON_EXE=%%V\python.exe"
)
if not defined PYTHON_EXE (
    echo ERROR: Python not found
    pause
    exit /b 1
)
echo Using Python: %PYTHON_EXE%

echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found
    pause
    exit /b 1
)

echo.
echo Installing backend dependencies...
cd backend

echo Creating virtual environment...
if not exist venv (
    %PYTHON_EXE% -m venv venv
    if errorlevel 1 (
        echo ERROR: Virtual environment creation failed
        pause
        exit /b 1
    )
)

if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment is broken, please delete backend\venv and retry
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
venv\Scripts\python -m pip install --upgrade pip >nul

echo Installing from requirements file...
if exist "requirements-windows.txt" (
    echo Using Windows full requirements...
    pip install -r requirements-windows.txt --disable-pip-version-check
) else if exist "requirements-windows-basic.txt" (
    echo Using Windows basic requirements...
    pip install -r requirements-windows-basic.txt --disable-pip-version-check
) else if exist "requirements-production.txt" (
    echo Using production requirements...
    pip install -r requirements-production.txt --disable-pip-version-check
) else (
    echo Using standard requirements...
    pip install -r requirements.txt --disable-pip-version-check
)

if errorlevel 1 (
    echo Package installation had some issues, trying manual installation...
    
    echo Installing core packages...
    pip install fastapi uvicorn sqlalchemy python-dotenv pydantic aiofiles
    
    echo Installing auth packages...
    pip install PyJWT python-jose[cryptography] passlib[bcrypt] python-multipart alembic pydantic-settings pydantic[email] email-validator
    
    echo Installing document processing...
    pip install pandas PyPDF2 python-docx openpyxl Pillow markdown pdfplumber
    
    echo Installing text processing...
    pip install jieba scikit-learn chardet httpx
    
    echo Installing PDF enhancement...
    pip install PyMuPDF || echo PyMuPDF failed, continuing...
    
    echo Installing OCR packages for production...
    pip install pytesseract>=0.3.10 pdf2image>=1.16.0 opencv-python-headless>=4.7.0 || echo OCR packages failed, continuing...
    
    echo Installing additional packages...
    pip install numpy>=1.21.0 || echo NumPy failed, continuing...
)

echo.
echo Verifying core dependencies...
venv\Scripts\python -c "import fastapi, uvicorn, sqlalchemy, jose, passlib, pydantic; print('OK core web/auth deps')" 2>nul || (
    echo [WARN] core deps import failed, please check pip output above
)

venv\Scripts\python -c "import yaml, fastmcp; print('OK AI Wiki MCP deps')" 2>nul || (
    echo [WARN] yaml or fastmcp missing, installing...
    venv\Scripts\python -m pip install PyYAML fastmcp
)

venv\Scripts\python -c "import pytesseract; print('OK pytesseract')" 2>nul || (
    echo [WARN] pytesseract missing, installing...
    venv\Scripts\python -m pip install pytesseract
)

venv\Scripts\python -c "import cv2; print('OK opencv')" 2>nul || (
    echo [WARN] opencv missing, installing...
    venv\Scripts\python -m pip install opencv-python-headless
)

echo.
echo Verifying app startup...
venv\Scripts\python -c "from app.main import app; paths=[getattr(r,'path','') for r in app.routes]; print('OK: app.main imports; /mcp mounted' if any('mcp' in p for p in paths) else 'WARN: app.main imports but /mcp NOT mounted')" 2>&1
if errorlevel 1 (
    echo [WARN] app import check failed, check pip output above
)

call venv\Scripts\deactivate.bat

echo.
echo Installing frontend dependencies...
cd ..\frontend
npm install
if errorlevel 1 (
    echo ERROR: Frontend installation failed
    pause
    exit /b 1
)

echo.
echo Testing database connection...
cd ..\backend
venv\Scripts\python -c "from app.db.database import engine; print('Database connection OK')" 2>nul
if errorlevel 1 (
    echo Database will be initialized on first run
)
call venv\Scripts\deactivate.bat

cd ..

echo.
echo ==========================================
echo    Installation Complete!
echo ==========================================
echo.
echo Run: start-services.bat
echo Visit: http://localhost:5173
echo Login: admin / admin123
echo.
pause