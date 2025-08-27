@echo off
chcp 65001 >nul
cls

REM 设置UTF-8环境变量
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

echo.
echo Checking Python...
python --version || (
    echo Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo Checking Node.js...
node --version || (
    echo Node.js not found! Please install Node.js 16+
    pause
    exit /b 1
)

echo.
echo Starting backend service...
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found! Please run install-environment.bat first
    pause
    exit /b 1
)

start "Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 %BACKEND_RELOAD%"

echo Waiting 5 seconds...
timeout /t 5 /nobreak >nul

echo Starting frontend service...
cd ..\frontend

if "%FRONTEND_MODE%"=="preview" (
    echo Building production version...
    npm run build
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
echo Frontend: http://localhost:5173 (Development & Production)
echo Backend API: http://localhost:8002/docs
echo System Status: http://localhost:8002/health
echo.
echo Default Login: admin / admin123
echo.

timeout /t 3 /nobreak >nul
start http://localhost:5173

echo Press any key to exit...
pause >nul