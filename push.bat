@echo off
REM ==========================================================
REM  Runyang Bridge System - Push to GitHub
REM  一键把本地 commit 推送到 GitHub
REM  用法: push.bat
REM
REM  解决两个问题：
REM  1. "git push 卡很久" → WorkBuddy 代理对 git smart-HTTP 返回 401
REM     + GCM 默认 Basic Auth 被 fine-grained PAT 拒
REM     → 改用 url.x-access-token:TOKEN@github.com/.insteadOf + 取消代理
REM  2. "本地与远端 SHA 不同" → 之前用 Git Data API 推的 commit 会让远端 SHA 与本地不同
REM     → 用 --force-with-lease 安全覆盖（比 --force 安全）
REM ==========================================================
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ==========================================
echo   Runyang Bridge System - Push to GitHub
echo ==========================================
echo.

REM ---- 0. 防御性检查：工作区必须干净 ----
git diff --quiet HEAD >nul 2>&1
if not errorlevel 1 goto _check_staged
echo WARN: 工作区有未提交改动。
echo        请先 'git add .' + 'git commit -m "..."' 再跑 push.bat
exit /b 1

:_check_staged
git diff --cached --quiet HEAD >nul 2>&1
if not errorlevel 1 goto _get_branch
echo WARN: 工作区有已暂存未提交改动。
exit /b 1

REM ---- 1. 当前分支 ----
:_get_branch
for /f "delims=" %%I in ('git rev-parse --abbrev-ref HEAD') do set "BRANCH=%%I"
echo 分支: !BRANCH!
echo.

REM ---- 2. 拿 token（走 GCM）----
REM 用 powershell 调 git credential fill 拿 password=
set "TOKEN="
for /f "delims=" %%T in ('powershell -NoProfile -Command "$env:GIT_TERMINAL_PROMPT='0'; $p = git credential fill; foreach ($line in $p -split \"`n\") { if ($line -like 'password=*') { $line.Substring(9) } }"') do set "TOKEN=%%T"

if "!TOKEN!"=="" (
    echo ERROR: 拿不到 GitHub token。
    echo        请先用 GitHub CLI 登录（gh auth login）或在 Windows 凭据管理器里加 token。
    exit /b 1
)

REM 用 powershell 算 token 长度（cmd 不擅长字符串长度）
for /f "delims=" %%L in ('powershell -NoProfile -Command "!TOKEN!.Length"') do set "TOKLEN=%%L"
echo Token: !TOKEN:~0,10!... (长度 !TOKLEN!)
echo.

REM ---- 3. 看 ahead/behind ----
for /f "delims=" %%I in ('git rev-list --count "origin/!BRANCH!..HEAD"') do set "AHEAD=%%I"
for /f "delims=" %%I in ('git rev-list --count "HEAD..origin/!BRANCH!"') do set "BEHIND=%%I"
echo ahead=!AHEAD!  behind=!BEHIND!

REM ---- 4. 决定 push flags ----
set "PUSH_FLAGS="
if not "!AHEAD!"=="0" if not "!BEHIND!"=="0" (
    echo 检测到 diverged -^> 用 --force-with-lease 覆盖远端
    set "PUSH_FLAGS=--force-with-lease"
) else if not "!BEHIND!"=="0" (
    echo WARN: 远端领先 !BEHIND! 个 commit。
    echo        建议先 'git pull --rebase origin !BRANCH!' 整合，再 push。
    set "PUSH_FLAGS=--force-with-lease"
)

echo.
echo 推送中...

REM ---- 5. 取消代理 + 用 x-access-token URL 推送 ----
powershell -NoProfile -Command ^
    "$env:HTTPS_PROXY=''; $env:HTTP_PROXY=''; $env:https_proxy=''; $env:http_proxy='';" ^
    "$env:GIT_TERMINAL_PROMPT='0';" ^
    "& git -c credential.helper= -c 'url.https://x-access-token:' + $env:TOKEN + '@github.com/heartsward/.insteadOf=https://github.com/heartsward/' push $env:PUSH_FLAGS origin $env:BRANCH"

set "RC=%ERRORLEVEL%"
echo.

if "!RC!"=="0" (
    echo ==========================================
    echo   PUSHED_OK
    echo ==========================================
    for /f "delims=" %%I in ('git rev-parse HEAD') do echo 新远端 HEAD: %%I
    echo GitHub: https://github.com/heartsward/runyang-bridge-docs-system
) else (
    echo ==========================================
    echo   PUSH_FAIL ^(exit=!RC!^)
    echo ==========================================
    echo 排查建议：
    echo   1. 网络: env -u HTTPS_PROXY git ls-remote https://github.com/heartsward/runyang-bridge-docs-system.git HEAD
    echo   2. Token 权限: 必须是 fine-grained PAT 且勾选 Contents: Read+Write
    echo   3. 如远端被保护（main 需 PR），换到其它分支或联系仓库管理员
)

endlocal & exit /b !RC!
