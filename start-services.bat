@echo off
chcp 65001 >nul
cls

REM Set UTF-8 environment variables
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set LANG=zh_CN.UTF-8

echo.
echo ==========================================
echo   Runyang Bridge System - Service Launcher
echo ==========================================
echo.
echo Choose startup mode:
echo [1] Development Mode (with hot reload)
echo [2] Production Mode (optimized build)
echo.
set /p mode="Please select mode (1 or 2): "

if "%mode%"=="1" (
    echo Starting in Development Mode...
    set FRONTEND_MODE=dev
    set BACKEND_RELOAD=--reload
) else if "%mode%"=="2" (
    echo Starting in Production Mode...
    set FRONTEND_MODE=preview
    set BACKEND_RELOAD=
) else (
    echo Invalid selection, defaulting to Development Mode...
    set FRONTEND_MODE=dev
    set BACKEND_RELOAD=--reload
)

REM ============================================
REM Detect Python (fall back to WorkBuddy managed runtime)
REM ============================================
set "PYTHON_EXE="
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
) else (
    for /d %%V in ("%USERPROFILE%\.workbuddy\binaries\python\versions\3.*") do if exist "%%V\python.exe" set "PYTHON_EXE=%%V\python.exe"
)
if not defined PYTHON_EXE (
    echo Python not found! Please install Python 3.8+ first.
    pause
    exit /b 1
)
echo Python found: %PYTHON_EXE%

REM ============================================
REM Detect Node.js (fall back to WorkBuddy managed runtime)
REM ============================================
set "NODE_DIR="
node --version >nul 2>&1
if not errorlevel 1 (
    echo Node.js found: node on PATH
) else (
    for /d %%V in ("%USERPROFILE%\.workbuddy\binaries\node\versions\*") do if exist "%%V\node.exe" set "NODE_DIR=%%V"
    if not defined NODE_DIR (
        echo Node.js not found! Please install Node.js 16+ first.
        pause
        exit /b 1
    )
    echo Node.js found: %NODE_DIR%\node.exe
    REM Prepend to PATH so npm works in this and all child windows
    set "PATH=%NODE_DIR%;%PATH%"
)

echo.
echo Starting backend service...
cd backend

REM Auto-create venv and install deps on first run (no manual install step needed)
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found, creating it now...
    "%PYTHON_EXE%" -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo You can try running install-complete.bat manually to repair.
        pause
        exit /b 1
    )
    echo Installing backend dependencies...
    "venv\Scripts\python.exe" -m pip install --upgrade pip --disable-pip-version-check
    if exist "requirements-windows.txt" (
        "venv\Scripts\python.exe" -m pip install -r requirements-windows.txt --disable-pip-version-check
    ) else (
        "venv\Scripts\python.exe" -m pip install -r requirements.txt --disable-pip-version-check
    )
    if errorlevel 1 (
        echo WARNING: Some packages failed to install. The service may not work fully.
    )
)

start "Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 %BACKEND_RELOAD%"

echo Waiting 5 seconds...
timeout /t 5 /nobreak >nul

echo Starting frontend service...
cd ..\frontend

if not exist "node_modules" (
    echo node_modules not found, installing frontend dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Frontend dependency installation failed.
        pause
        exit /b 1
    )
)

if "%FRONTEND_MODE%"=="preview" (
    echo Building production version...
    call npm run build
    if errorlevel 1 (
        echo Build failed! Please check for errors.
        pause
        exit /b 1
    )
    echo Starting production preview...
    start "Frontend" cmd /k "npm run preview"
) else (
    echo Starting development server...
    start "Frontend" cmd /k "npm run dev"
)

echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

cd ..

echo.
echo ==========================================
echo   System Started Successfully!
echo ==========================================
echo.
echo Frontend: http://localhost:5173
echo Backend API: http://localhost:8002/docs
echo System Status: http://localhost:8002/health
echo.
echo Default Login: admin / admin123
echo.

timeout /t 3 /nobreak >nul
start http://localhost:5173

echo Press any key to exit...
pause >nul
