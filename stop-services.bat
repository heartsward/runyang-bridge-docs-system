@echo off
setlocal

title Stop Services - Runyang Bridge System

echo.
echo ==========================================
echo   Stopping Services...
echo ==========================================
echo.

echo [Step 1/2] Stopping backend services...
echo Looking for Python processes...

REM Stop Python processes
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo table 2^>nul ^| find "python.exe"') do (
    echo Stopping Python process %%i...
    taskkill /pid %%i /f >nul 2>&1
)

REM Also try to stop python3.exe processes
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python3.exe" /fo table 2^>nul ^| find "python3.exe"') do (
    echo Stopping Python3 process %%i...
    taskkill /pid %%i /f >nul 2>&1
)

echo SUCCESS: Backend services stopped

echo.
echo [Step 2/2] Stopping frontend services...
echo Looking for Node.js processes...

REM Stop Node.js processes
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo table 2^>nul ^| find "node.exe"') do (
    echo Stopping Node.js process %%i...
    taskkill /pid %%i /f >nul 2>&1
)

echo SUCCESS: Frontend services stopped

echo.
echo ==========================================
echo   ALL SERVICES STOPPED SUCCESSFULLY
echo ==========================================
echo.
echo Info:
echo - All Python and Node.js processes terminated
echo - Ports 8002 and 5173 are now free
echo - Use start-simple.bat to restart services
echo.

echo Press any key to exit...
pause >nul
endlocal