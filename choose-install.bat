@echo off
chcp 65001 >nul

echo ==========================================
echo    Windows Installation Options
echo ==========================================
echo.
echo Choose your installation type:
echo.
echo 1. Basic Install     - Core functionality only (Fastest)
echo 2. Complete Install  - All features included (Recommended)
echo 3. Enhanced Install  - With OCR and advanced features (Largest)
echo.
set /p choice=Enter your choice (1/2/3): 

if "%choice%"=="1" (
    echo Starting basic installation...
    call install-basic.bat
) else if "%choice%"=="2" (
    echo Starting complete installation...
    call install-complete.bat
) else if "%choice%"=="3" (
    echo Starting enhanced installation...
    call install-enhanced-full.bat
) else (
    echo Invalid choice. Running complete installation...
    call install-complete.bat
)

echo.
echo Installation finished!
pause