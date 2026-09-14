@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title Stop Services - Runyang Bridge System

echo.
echo ==========================================
echo   Stopping Services (port-based)...
echo ==========================================
echo.
echo 只停止本项目占用的端口（8002 后端 / 5173 前端），
echo 不会触碰机器上其他 Python / Node.js 进程（如 IDE）。
echo.

set "STOPPED=0"

for %%P in (8002 5173) do (
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr ":%%P" ^| findstr "LISTENING"') do (
        echo [Port %%P] stopping PID %%A ...
        taskkill /pid %%A /f >nul 2>&1
        if !errorlevel!==0 (
            echo   OK
            set /a STOPPED+=1
        ) else (
            echo   already exited (ignored)
        )
    )
)

echo.
if %STOPPED%==0 (
    echo Note: nothing listening on 8002/5173, services not running.
) else (
    echo Stopped %STOPPED% service process(es).
)

echo.
echo ==========================================
echo   DONE
echo ==========================================
echo.
echo Verify ports freed: netstat -ano ^| findstr ":8002 :5173"
echo Restart:            start-services.bat
echo.
pause >nul
endlocal
