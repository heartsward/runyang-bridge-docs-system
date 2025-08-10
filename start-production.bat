@echo off
chcp 65001 > nul
cls
echo ====================================================
echo        润扬大桥运维文档管理系统 - 生产模式启动
echo ====================================================
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

REM 检查LibreOffice环境
echo [信息] 检查LibreOffice环境...
set LIBREOFFICE_FOUND=0

if exist "C:\Program Files\LibreOffice\program\soffice.exe" (
    set LIBREOFFICE_FOUND=1
    echo [成功] 发现LibreOffice (64位版本)
) else if exist "C:\Program Files (x86)\LibreOffice\program\soffice.exe" (
    set LIBREOFFICE_FOUND=1
    echo [成功] 发现LibreOffice (32位版本)
) else (
    soffice --version >nul 2>&1
    if not errorlevel 1 (
        set LIBREOFFICE_FOUND=1
        echo [成功] 发现LibreOffice (环境变量)
    )
)

if %LIBREOFFICE_FOUND%==0 (
    echo [警告] 未找到 LibreOffice，文档内容提取功能将受限
    echo.
    echo LibreOffice 用于提取Word、Excel等文档内容，建议安装：
    echo 1. 访问 https://www.libreoffice.org/download/download/
    echo 2. 下载并安装最新版本的LibreOffice
    echo 3. 重新运行此脚本
    echo.
    choice /C YN /M "是否继续启动系统 (Y=是, N=退出安装LibreOffice)" /T 10 /D Y
    if errorlevel 2 (
        echo [信息] 请安装LibreOffice后重新运行
        pause
        exit /b 1
    )
    echo [信息] 继续启动，但文档提取功能可能无法正常工作
)

echo [信息] 正在启动润扬大桥运维文档管理系统...
echo.

REM 检查并安装Python依赖
echo [步骤 1/6] 检查Python依赖...
cd /d "%~dp0backend"
if not exist requirements.txt (
    echo [错误] 未找到 backend/requirements.txt 文件
    pause
    exit /b 1
)

echo [信息] 安装Python依赖包...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] Python依赖安装失败
    pause
    exit /b 1
)

REM 检查并安装Node.js依赖
echo.
echo [步骤 2/6] 检查Node.js依赖...
cd /d "%~dp0frontend"
if not exist package.json (
    echo [错误] 未找到 frontend/package.json 文件
    pause
    exit /b 1
)

echo [信息] 安装Node.js依赖包...
npm install
if errorlevel 1 (
    echo [错误] Node.js依赖安装失败
    pause
    exit /b 1
)

REM 复制生产环境配置
echo.
echo [步骤 3/6] 配置生产环境...
cd /d "%~dp0backend"

REM 优先使用环境配置模板
if not exist .env (
    if exist .env.example (
        copy /y .env.example .env > nul
        echo [成功] 已从模板创建后端环境配置文件
        echo [警告] 请编辑 backend\.env 文件，修改SECRET_KEY等重要配置
    ) else if exist .env.production (
        copy /y .env.production .env > nul
        echo [信息] 后端生产环境配置已应用
    ) else (
        echo [警告] 未找到环境配置文件，请手动创建 .env
    )
) else (
    echo [信息] 后端环境配置文件已存在
)

cd /d "%~dp0frontend"
if not exist .env (
    if exist .env.example (
        copy /y .env.example .env > nul
        echo [成功] 已从模板创建前端环境配置文件
    ) else if exist .env.production (
        copy /y .env.production .env > nul
        echo [信息] 前端生产环境配置已应用
    ) else (
        echo [警告] 未找到环境配置文件，请手动创建 .env
    )
) else (
    echo [信息] 前端环境配置文件已存在
)

REM 构建前端
echo.
echo [步骤 4/6] 构建前端应用...
npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    pause
    exit /b 1
)
echo [信息] 前端构建完成

REM 启动后端服务
echo.
echo [步骤 5/6] 启动后端服务...
cd /d "%~dp0backend"
echo [信息] 正在启动后端服务 (端口: 8002)...
start "润扬大桥运维系统-后端" cmd /k "python database_integrated_server.py"

REM 等待后端启动
timeout /t 3 > nul

REM 启动前端服务
echo.
echo [步骤 6/6] 启动前端服务...
cd /d "%~dp0frontend"
echo [信息] 正在启动前端服务 (端口: 5173)...
start "润扬大桥运维系统-前端" cmd /k "npm run dev"

echo.
echo ====================================================
echo                   启动完成！
echo ====================================================
echo.
echo 系统访问地址:
echo   前端界面: http://localhost:5173
echo   后端API:  http://localhost:8002
echo   API文档:  http://localhost:8002/docs
echo.
echo 默认登录账户:
echo   用户名: admin
echo   密码:   admin123
echo.
echo 注意: 首次登录后请立即修改默认密码
echo.
echo [提示] 按任意键关闭启动脚本...
pause > nul