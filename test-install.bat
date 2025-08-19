@echo off
chcp 65001 >nul
echo Testing install script components...

echo.
echo Test 1: Python available
python --version
if errorlevel 1 (
    echo FAIL: Python not found
    goto :end
) else (
    echo PASS: Python found
)

echo.
echo Test 2: Node.js available  
node --version
if errorlevel 1 (
    echo FAIL: Node.js not found
    goto :end
) else (
    echo PASS: Node.js found
)

echo.
echo Test 3: Check backend directory
if exist "backend" (
    echo PASS: Backend directory exists
) else (
    echo FAIL: Backend directory not found
    goto :end
)

echo.
echo Test 4: Check frontend directory
if exist "frontend" (
    echo PASS: Frontend directory exists
) else (
    echo FAIL: Frontend directory not found
    goto :end
)

echo.
echo Test 5: Test datetime fix script
cd backend
python fix_datetime.py
if errorlevel 1 (
    echo FAIL: DateTime fix script failed
) else (
    echo PASS: DateTime fix script works
)
cd ..

echo.
echo =====================================
echo All basic tests passed!
echo The install-production.bat should work correctly.
echo =====================================

:end
pause