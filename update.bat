@echo off
REM ==========================================================
REM  Runyang Bridge System - Update
REM  更新本项目代码并重启服务（不破坏 .env / 数据库 / 上传文件）
REM  用法: update.bat
REM
REM  设计原则：
REM  - git pull --ff-only：严格快进，避免意外 merge/rebase
REM  - 保护本地数据：.env、*.db、uploads/、logs/、venv/、node_modules/ 全部在 .gitignore 里
REM  - 防御性检查：工作区脏则中止并提示
REM  - 重启后端：Settings 单例 import 时只读一次 .env，必须重启
REM ==========================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ==========================================
echo   Runyang Bridge System - Update
echo ==========================================
echo 工作区: %cd%
echo.

REM ---- 1. 防御性检查：工作区必须干净 ----
git diff --quiet HEAD >nul 2>&1
if not errorlevel 1 goto _check_staged
echo ERROR: 工作区有未提交改动，拒绝 pull。
echo        请先 'git status' 查看，改完后 'git stash' 或 'git commit' 再重跑。
exit /b 1

:_check_staged
git diff --cached --quiet HEAD >nul 2>&1
if not errorlevel 1 goto _backup_env
echo ERROR: 工作区有已暂存未提交改动，拒绝 pull。
exit /b 1

REM ---- 2. 备份 .env ----
:_backup_env
set "ENV_FILE=backend\.env"
set "ENV_BACKUP="
if exist "%ENV_FILE%" (
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul ^| find "LocalDateTime"') do set "DATETIME=%%I"
    set "TS=%DATETIME:~0,8%_%DATETIME:~8,6%"
    set "ENV_BACKUP=%ENV_FILE%.update.bak.!TS!"
    copy /Y "%ENV_FILE%" "!ENV_BACKUP!" >nul
    echo [1/5] 已备份 %ENV_FILE% -^> !ENV_BACKUP!
) else (
    echo [1/5] %ENV_FILE% 不存在，跳过备份
)

REM ---- 3. 拉取最新代码 ----
echo [2/5] 拉取最新代码（git pull --ff-only origin main）...
git pull --ff-only origin main
if errorlevel 1 (
    echo.
    echo ERROR: git pull 失败。
    echo   可能原因：
    echo     - 远端拒绝 fast-forward（本地有未推送 commit）-^> 用 'git status' 看
    echo     - 网络/认证问题 -^> 用 'git fetch origin main' 单独诊断
    if defined ENV_BACKUP if exist "!ENV_BACKUP!" echo   .env 备份在 !ENV_BACKUP!，可手动恢复
    exit /b 1
)
for /f "delims=" %%I in ('git rev-parse --short HEAD') do set "NEW_SHA=%%I"
echo       当前 HEAD: !NEW_SHA!

REM ---- 4. 更新 Python 依赖 ----
echo [3/5] 检查后端依赖...
cd /d "%~dp0backend"
if exist "venv\Scripts\python.exe" (
    set "REQ_FILE=requirements.txt"
    if not exist "!REQ_FILE!" set "REQ_FILE=requirements-windows.txt"
    if exist "!REQ_FILE!" (
        echo       pip install -r !REQ_FILE!
        call venv\Scripts\python.exe -m pip install -r "!REQ_FILE!" --upgrade-strategy only-if-needed --disable-pip-version-check -q
    )
) else (
    echo       venv 不存在，跳过（首次部署请先运行 install-complete.bat 或 start-services.bat）
)

REM ---- 5. 更新前端依赖 ----
echo [4/5] 检查前端依赖...
cd /d "%~dp0frontend"
if exist "node_modules" (
    echo       npm install
    call npm install --no-audit --no-fund -q
) else (
    echo       node_modules 不存在，跳过（首次部署请先运行 install-complete.bat 或 start-services.bat）
)

REM ---- 6. 重启后端 ----
echo [5/5] 重启后端...
cd /d "%~dp0"

REM 优先用 stop-services.bat + start-services.bat（统一端口停止逻辑）
if exist "stop-services.bat" (
    call stop-services.bat >nul 2>&1
)

REM 给后端一点时间释放端口
timeout /t 3 /nobreak >nul

if exist "start-services.bat" (
    call start-services.bat
) else (
    echo WARN: start-services.bat 不存在，请手动启动后端
)

echo.
echo ==========================================
echo   Update Complete!
echo ==========================================
echo HEAD: !NEW_SHA!
echo 日志: logs\backend.log  logs\frontend.log
echo 回滚（如需）: git reset --hard HEAD@{1}
if defined ENV_BACKUP if exist "!ENV_BACKUP!" echo .env 备份: !ENV_BACKUP!
echo.

endlocal
