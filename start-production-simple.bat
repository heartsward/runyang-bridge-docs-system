@echo off
chcp 65001 > nul
cls

echo ====================================================
echo 润扬大桥运维文档管理系统 - 快速生产启动
echo ====================================================
echo.

:: 设置工作目录
set "ROOT_DIR=%~dp0"

echo [%time%] 开始启动生产环境服务...
echo.

:: ============= 启动后端服务 =============
echo [步骤 1/3] 启动后端服务...
cd /d "%ROOT_DIR%backend"
echo [信息] 正在启动FastAPI后端服务 (端口: 8002)...
start "润扬大桥运维系统-后端" /min cmd /c "python database_integrated_server.py"

:: 等待后端启动
timeout /t 3 /nobreak > nul
echo [成功] 后端服务启动中...

:: ============= 启动前端服务 =============
echo.
echo [步骤 2/3] 启动前端服务...
cd /d "%ROOT_DIR%frontend"
echo [信息] 正在启动Vue前端服务 (端口: 5173)...
start "润扬大桥运维系统-前端" /min cmd /c "npm run dev"

:: 等待前端启动
timeout /t 3 /nobreak > nul
echo [成功] 前端服务启动中...

:: ============= 显示系统信息 =============
echo.
echo [步骤 3/3] 系统启动完成！
echo.
echo ====================================================
echo                   服务访问信息
echo ====================================================
echo.
echo 🌐 前端界面: http://localhost:5173
echo 🔧 后端API:  http://localhost:8002
echo 📚 API文档:  http://localhost:8002/docs
echo.
echo ====================================================
echo                   移动端API端点
echo ====================================================
echo.
echo 📱 移动端认证: http://localhost:8002/api/v1/mobile/auth/login
echo 📄 文档接口:   http://localhost:8002/api/v1/mobile/documents/
echo 🏢 资产接口:   http://localhost:8002/api/v1/mobile/assets/
echo 🎤 语音查询:   http://localhost:8002/api/v1/voice/query
echo ℹ️  系统信息:   http://localhost:8002/api/v1/system/info
echo 💚 健康检查:   http://localhost:8002/api/v1/system/health
echo.
echo ====================================================
echo                   系统状态监控
echo ====================================================
echo.
echo 📊 数据分析:   http://localhost:8002/api/v1/analytics/summary
echo 🔍 搜索接口:   http://localhost:8002/api/v1/search/
echo ⚙️  用户设置:   http://localhost:8002/api/v1/settings/profile
echo.
echo ====================================================
echo                   默认登录信息
echo ====================================================
echo.
echo 👤 用户名: admin
echo 🔐 密码:   admin123
echo.
echo ⚠️  首次登录后请立即修改默认密码
echo.
echo ====================================================
echo.

:: 自动打开浏览器（可选）
echo [信息] 是否自动打开浏览器? (自动跳过 10秒)
choice /C YN /M "打开浏览器 (Y=是, N=否)" /T 10 /D Y
if not errorlevel 2 (
    echo [信息] 正在打开系统管理界面...
    start "" "http://localhost:5173"
    timeout /t 2 /nobreak > nul
    echo [信息] 正在打开API文档...
    start "" "http://localhost:8002/docs"
)

echo.
echo ====================================================
echo                   注意事项
echo ====================================================
echo.
echo ✅ 服务已在后台运行，关闭此窗口不会停止服务
echo 🛑 如需停止服务，请运行: stop-services.bat
echo 🔄 如需重启服务，请先停止后重新运行此脚本
echo 📝 系统日志位置: backend/logs/
echo 💾 数据库位置: backend/yunwei_docs.db
echo.

echo [%time%] 生产环境启动完成！
echo.
echo 按任意键关闭启动脚本（服务将继续运行）...
pause > nul

:: 返回原目录
cd /d "%ROOT_DIR%"