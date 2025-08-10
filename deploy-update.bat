@echo off
chcp 65001 > nul
cls
echo ====================================================
echo     润扬大桥运维文档管理系统 - 生产环境安全更新
echo ====================================================
echo.

REM 检查是否在Git仓库中
if not exist ".git" (
    echo [错误] 当前目录不是Git仓库，请确保在项目根目录执行
    pause
    exit /b 1
)

REM 检查网络连接
echo [步骤 1/10] 检查网络连接...
ping github.com -n 1 > nul
if errorlevel 1 (
    echo [错误] 无法连接到GitHub，请检查网络连接
    pause
    exit /b 1
)
echo [成功] 网络连接正常

REM 显示当前版本信息
echo.
echo [步骤 2/10] 显示当前版本信息...
echo [信息] 当前版本信息:
git log -1 --oneline
echo [信息] 当前分支: 
git branch --show-current
echo [信息] 远程仓库状态:
git remote -v

REM 检查远程更新
echo.
echo [步骤 3/10] 检查远程更新...
git fetch origin
if errorlevel 1 (
    echo [错误] 无法从远程仓库获取更新
    pause
    exit /b 1
)

REM 比较本地和远程版本
for /f "delims=" %%i in ('git rev-list HEAD...origin/main --count') do set UPDATE_COUNT=%%i
if %UPDATE_COUNT%==0 (
    echo [信息] 已是最新版本，无需更新
    choice /C YN /M "是否强制重新部署 (Y=是, N=退出)" /T 10 /D N
    if errorlevel 2 (
        echo [信息] 退出更新程序
        pause
        exit /b 0
    )
) else (
    echo [信息] 发现 %UPDATE_COUNT% 个新提交，需要更新
)

REM 显示待更新的内容
echo.
echo [步骤 4/10] 显示待更新内容...
if %UPDATE_COUNT% gtr 0 (
    echo [信息] 待更新的提交:
    git log HEAD..origin/main --oneline
    echo.
    choice /C YN /M "是否继续更新 (Y=是, N=取消)" /T 30 /D Y
    if errorlevel 2 (
        echo [信息] 用户取消更新
        pause
        exit /b 0
    )
)

REM 创建备份
echo.
echo [步骤 5/10] 创建备份...
set BACKUP_DIR=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir %BACKUP_DIR% 2>nul
echo [信息] 备份当前配置文件...
copy "backend\.env" "%BACKUP_DIR%\backend.env.backup" >nul 2>&1
copy "frontend\.env" "%BACKUP_DIR%\frontend.env.backup" >nul 2>&1
if exist "yunwei_docs.db" copy "yunwei_docs.db" "%BACKUP_DIR%\database.backup" >nul 2>&1
echo [成功] 配置备份已保存到: %BACKUP_DIR%

REM 安全停止服务
echo.
echo [步骤 6/10] 安全停止当前服务...
echo [信息] 正在优雅地停止服务...
call stop-services.bat
timeout /t 2 > nul

REM 更新代码
echo.
echo [步骤 7/10] 更新代码...
git stash push -m "Auto-stash before update %date% %time%"
git pull origin main
if errorlevel 1 (
    echo [错误] 代码更新失败，正在恢复...
    git stash pop
    echo [信息] 重新启动原版本服务...
    call start-production.bat
    pause
    exit /b 1
)
echo [成功] 代码更新完成

REM 检查配置文件变更
echo.
echo [步骤 8/10] 检查配置文件变更...
fc "backend\.env.example" "%BACKUP_DIR%\backend.env.backup" >nul 2>&1
if errorlevel 1 (
    echo [警告] 后端配置模板有更新，请检查以下文件:
    echo   新模板: backend\.env.example
    echo   当前配置: backend\.env
    echo [建议] 请对比并手动更新必要的配置项
    pause
)

fc "frontend\.env.example" "%BACKUP_DIR%\frontend.env.backup" >nul 2>&1
if errorlevel 1 (
    echo [警告] 前端配置模板有更新，请检查以下文件:
    echo   新模板: frontend\.env.example  
    echo   当前配置: frontend\.env
    echo [建议] 请对比并手动更新必要的配置项
    pause
)

REM 恢复配置文件
echo.
echo [步骤 9/10] 恢复配置文件...
if exist "%BACKUP_DIR%\backend.env.backup" (
    copy "%BACKUP_DIR%\backend.env.backup" "backend\.env" >nul
    echo [成功] 后端配置已恢复
)
if exist "%BACKUP_DIR%\frontend.env.backup" (
    copy "%BACKUP_DIR%\frontend.env.backup" "frontend\.env" >nul
    echo [成功] 前端配置已恢复
)

REM 重新启动服务
echo.
echo [步骤 10/10] 重新启动服务...
echo [信息] 启动更新后的系统...
call start-production.bat

REM 等待服务启动
echo.
echo [信息] 等待服务启动完成...
timeout /t 10 > nul

REM 验证服务状态
echo [信息] 验证服务状态...
curl -s http://localhost:8002/health > nul 2>&1
if errorlevel 1 (
    echo [警告] 后端服务可能未正常启动，请检查日志
) else (
    echo [成功] 后端服务运行正常
)

curl -s http://localhost:5173 > nul 2>&1  
if errorlevel 1 (
    echo [警告] 前端服务可能未正常启动，请检查日志
) else (
    echo [成功] 前端服务运行正常
)

echo.
echo ====================================================
echo                   更新完成！
echo ====================================================
echo.
echo [信息] 系统更新详情:
git log -1 --oneline
echo.
echo [信息] 服务访问地址:
echo   前端界面: http://localhost:5173
echo   后端API:  http://localhost:8002  
echo   API文档:  http://localhost:8002/docs
echo.
echo [信息] 备份文件位置: %BACKUP_DIR%
echo [提示] 如有问题可回滚: git reset --hard HEAD~1
echo.
pause