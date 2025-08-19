@echo off
chcp 65001 >nul

echo ==========================================
echo    Windows Complete Install Script
echo ==========================================
echo.

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

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
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Virtual environment creation failed
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip >nul

echo Installing from requirements file...
if exist "requirements-windows-basic.txt" (
    echo Using Windows basic requirements...
    pip install -r requirements-windows-basic.txt --disable-pip-version-check
) else if exist "requirements-windows.txt" (
    echo Using Windows full requirements...
    pip install -r requirements-windows.txt --disable-pip-version-check
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
    pip install pytesseract pdf2image opencv-python-headless || echo OCR packages failed, continuing...
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
call venv\Scripts\activate.bat
python -c "from app.db.database import engine; print('Database connection OK')" 2>nul
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