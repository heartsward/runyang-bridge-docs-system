@echo off
chcp 65001 > nul
cls
echo ====================================================
echo     润扬大桥运维文档管理系统 - 版本更新发布
echo ====================================================
echo.

REM 检查是否在Git仓库中
if not exist ".git" (
    echo [错误] 当前目录不是Git仓库
    pause
    exit /b 1
)

REM 检查Git状态
echo [步骤 1/6] 检查Git状态...
git status --porcelain > %TEMP%\git_status.txt
for /f %%i in ("%TEMP%\git_status.txt") do set size=%%~zi
if %size% gtr 0 (
    echo [信息] 发现未提交的更改：
    git status --short
    echo.
    choice /C YN /M "是否继续提交这些更改 (Y=是, N=取消)" /T 30 /D N
    if errorlevel 2 (
        echo [信息] 用户取消操作
        pause
        exit /b 1
    )
) else (
    echo [信息] 工作目录干净，无未提交更改
)

REM 获取版本信息
echo.
echo [步骤 2/6] 获取版本信息...
set /p VERSION_TYPE="请选择版本类型 [1=补丁(patch) 2=功能(minor) 3=重大(major)]: "

if "%VERSION_TYPE%"=="1" (
    set VERSION_NAME=patch
    set VERSION_DESC=补丁版本
) else if "%VERSION_TYPE%"=="2" (
    set VERSION_NAME=minor
    set VERSION_DESC=功能版本
) else if "%VERSION_TYPE%"=="3" (
    set VERSION_NAME=major
    set VERSION_DESC=重大版本
) else (
    set VERSION_NAME=patch
    set VERSION_DESC=补丁版本
    echo [信息] 无效选择，默认为补丁版本
)

REM 获取更新说明
echo.
set /p UPDATE_DESC="请输入本次更新的简要说明: "
if "%UPDATE_DESC%"=="" (
    set UPDATE_DESC=常规更新和优化
)

REM 添加所有更改到暂存区
echo.
echo [步骤 3/6] 添加更改到暂存区...
git add .
if errorlevel 1 (
    echo [错误] 添加文件到暂存区失败
    pause
    exit /b 1
)

REM 生成提交信息
echo.
echo [步骤 4/6] 创建提交...
git commit -m "$(echo feat: %UPDATE_DESC%
echo.
echo - %VERSION_DESC%更新
echo - 系统功能优化和bug修复
echo - 文档和配置更新
echo.
echo 🚀 Generated with [Claude Code](https://claude.ai/code)
echo.
echo Co-Authored-By: Claude ^<noreply@anthropic.com^>)"

if errorlevel 1 (
    echo [错误] 提交失败
    pause
    exit /b 1
)

REM 创建版本标签
echo.
echo [步骤 5/6] 创建版本标签...
for /f "delims=" %%i in ('git rev-list --count HEAD') do set COMMIT_COUNT=%%i
set TAG_NAME=v1.0.%COMMIT_COUNT%
git tag -a %TAG_NAME% -m "%VERSION_DESC%: %UPDATE_DESC%"
echo [成功] 创建版本标签: %TAG_NAME%

REM 推送到远程仓库
echo.
echo [步骤 6/6] 推送到GitHub...
echo [信息] 推送代码到远程仓库...
git push origin main
if errorlevel 1 (
    echo [错误] 推送代码失败
    pause
    exit /b 1
)

echo [信息] 推送标签到远程仓库...
git push origin %TAG_NAME%
if errorlevel 1 (
    echo [警告] 推送标签失败，但代码已成功推送
)

echo.
echo ====================================================
echo                  发布成功！
echo ====================================================
echo.
echo [信息] 版本信息:
echo   版本标签: %TAG_NAME%
echo   版本类型: %VERSION_DESC%
echo   更新说明: %UPDATE_DESC%
echo.
echo [信息] 远程仓库已更新，部署服务器可以拉取最新版本
echo.
echo [提示] 生产服务器更新命令:
echo   Windows: deploy-update.bat
echo   Linux:   ./deploy-update.sh
echo.
pause