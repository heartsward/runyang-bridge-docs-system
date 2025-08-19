@echo off
chcp 65001 >nul
cls

REM 设置UTF-8环境变量
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set LANG=zh_CN.UTF-8

echo.
echo ==========================================
echo   Runyang Bridge System - Quick Start
echo ==========================================
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

start "Backend" cmd /k "call venv\Scripts\activate.bat && python database_integrated_server.py"

echo Waiting 5 seconds...
timeout /t 5 /nobreak >nul

echo Starting frontend service...
cd ..\frontend
start "Frontend" cmd /k "npm run dev"

echo Waiting 3 seconds...
timeout /t 3 /nobreak >nul

cd ..

echo.
echo ==========================================
echo   System Started Successfully!
echo ==========================================
echo.
echo Access at: http://localhost:5173
echo API Docs: http://localhost:8002/docs
echo.
echo Login: admin / admin123
echo.

timeout /t 3 /nobreak >nul
start http://localhost:5173

echo Press any key to exit...
pause >nul