@echo off
chcp 65001 > nul
cls

echo ====================================================
echo    润扬大桥运维文档管理系统 - 通用部署启动脚本
echo ====================================================
echo.

REM 获取本机IP地址
for /f "tokens=14" %%i in ('ipconfig ^| findstr /C:"IPv4"') do (
    set LOCAL_IP=%%i
    goto :ip_found
)
:ip_found

if "%LOCAL_IP%"=="" (
    for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr "IPv4" ^| findstr -v "127.0.0.1"') do (
        for /f "tokens=1" %%j in ("%%i") do (
            set LOCAL_IP=%%j
            goto :ip_set
        )
    )
)
:ip_set

if "%LOCAL_IP%"=="" set LOCAL_IP=127.0.0.1

REM 去除IP地址前后的空格
for /f "tokens=* delims= " %%a in ("%LOCAL_IP%") do set LOCAL_IP=%%a

echo [信息] 自动检测到本机IP: %LOCAL_IP%

REM 检查命令行参数
if not "%1"=="" (
    set LOCAL_IP=%1
    echo [信息] 使用指定IP地址: %LOCAL_IP%
)

echo [信息] 系统将配置为允许以下访问方式:
echo   - 本地访问: http://localhost:5173
echo   - 局域网访问: http://%LOCAL_IP%:5173
echo   - API接口: http://%LOCAL_IP%:8002
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+ 版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查Node.js环境
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 16+ 版本
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 设置环境变量 - 使用新的CORS配置系统
set CORS_MODE=auto
set CORS_ORIGINS=http://%LOCAL_IP%:5173,http://%LOCAL_IP%:5174,http://%LOCAL_IP%:8002
set CORS_AUTO_DETECT=true
set CORS_INCLUDE_LOCALHOST=true
set SERVER_HOST=%LOCAL_IP%

echo [信息] 环境配置:
echo   CORS_MODE=%CORS_MODE%
echo   CORS_ORIGINS=%CORS_ORIGINS%
echo   CORS_AUTO_DETECT=%CORS_AUTO_DETECT%
echo   SERVER_HOST=%SERVER_HOST%
echo.

REM 检查并安装Python依赖
echo [步骤 1/6] 安装Python依赖...
cd /d "%~dp0backend"
if not exist requirements.txt (
    echo [错误] 未找到 backend/requirements.txt 文件
    pause
    exit /b 1
)

pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] Python依赖安装失败
    pause
    exit /b 1
)

REM 检查并安装Node.js依赖
echo.
echo [步骤 2/6] 安装Node.js依赖...
cd /d "%~dp0frontend"
if not exist package.json (
    echo [错误] 未找到 frontend/package.json 文件
    pause
    exit /b 1
)

npm install
if errorlevel 1 (
    echo [错误] Node.js依赖安装失败
    pause
    exit /b 1
)

REM 创建环境配置文件
echo.
echo [步骤 3/6] 配置环境文件...
cd /d "%~dp0backend"

REM 创建后端环境配置
(
echo # 润扬大桥运维文档管理系统 - 后端配置
echo PROJECT_NAME=运维文档管理系统
echo VERSION=1.0.0
echo DEBUG=false
echo SECRET_KEY=your-production-secret-key-change-this-in-production
echo DATABASE_URL=sqlite:///./yunwei_docs.db
echo CORS_MODE=%CORS_MODE%
echo CORS_ORIGINS=%CORS_ORIGINS%
echo CORS_AUTO_DETECT=%CORS_AUTO_DETECT%
echo CORS_INCLUDE_LOCALHOST=%CORS_INCLUDE_LOCALHOST%
) > .env

echo [成功] 后端环境配置已生成

cd /d "%~dp0frontend"

REM 创建前端环境配置
(
echo # 润扬大桥运维文档管理系统 - 前端配置
echo VITE_API_BASE_URL=http://%LOCAL_IP%:8002
echo VITE_APP_TITLE=润扬大桥运维文档管理系统
echo VITE_APP_VERSION=1.0.0
echo VITE_MAX_FILE_SIZE=10485760
echo VITE_BUILD_SOURCEMAP=false
echo VITE_BUILD_MINIFY=true
) > .env

echo [成功] 前端环境配置已生成

REM 构建前端
echo.
echo [步骤 4/6] 构建前端应用...
npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)

REM 启动后端服务
echo.
echo [步骤 5/6] 启动后端服务...
cd /d "%~dp0backend"
echo [信息] 正在启动后端服务...
start "润扬运维系统-后端-%LOCAL_IP%" cmd /k "set CORS_MODE=%CORS_MODE% && set CORS_ORIGINS=%CORS_ORIGINS% && set CORS_AUTO_DETECT=%CORS_AUTO_DETECT% && set CORS_INCLUDE_LOCALHOST=%CORS_INCLUDE_LOCALHOST% && python database_integrated_server.py"

REM 等待后端启动
echo [信息] 等待后端服务启动...
timeout /t 5 > nul

REM 启动前端服务
echo.
echo [步骤 6/6] 启动前端服务...
cd /d "%~dp0frontend"
echo [信息] 正在启动前端开发服务器...
start "润扬运维系统-前端-%LOCAL_IP%" cmd /k "npm run dev"

echo.
echo ====================================================
echo                   启动完成！
echo ====================================================
echo.
echo 系统访问地址:
echo   本地访问:   http://localhost:5173
echo   局域网访问: http://%LOCAL_IP%:5173
echo   后端API:   http://%LOCAL_IP%:8002
echo   API文档:   http://%LOCAL_IP%:8002/docs
echo.
echo 默认登录账户:
echo   用户名: admin
echo   密码:   admin123
echo.
echo ════════════════════════════════════════════════════
echo   使用说明:
echo   1. 本机访问: 直接使用 localhost 地址
echo   2. 其他电脑访问: 使用 %LOCAL_IP% 地址
echo   3. 如需指定IP: %~nx0 [IP地址]
echo   4. 生产部署: 修改backend\.env中的SECRET_KEY
echo ════════════════════════════════════════════════════
echo.
pause