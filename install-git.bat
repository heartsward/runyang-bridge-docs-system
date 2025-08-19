@echo off
chcp 65001 >nul
echo ==========================================
echo    Git安装助手
echo ==========================================
echo.

echo 选项1: 使用winget安装Git (Windows 10/11推荐)
echo winget install --id Git.Git -e --source winget
echo.

echo 选项2: 手动下载安装
echo 访问: https://git-scm.com/download/win
echo 下载并安装Git for Windows
echo.

echo 选项3: 使用便携版Git
echo 1. 下载便携版: https://git-scm.com/download/win (选择Portable)
echo 2. 解压到 C:\git
echo 3. 添加 C:\git\bin 到系统PATH
echo.

echo 安装完成后，重新打开命令行窗口测试:
echo git --version
echo.

echo ==========================================
echo 如果无法安装Git，请使用手动更新方案
echo ==========================================
pause