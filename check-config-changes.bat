@echo off
chcp 65001 > nul
cls
echo ====================================================
echo     润扬大桥运维文档管理系统 - 配置变更检测工具
echo ====================================================
echo.

REM 检查是否在Git仓库中
if not exist ".git" (
    echo [错误] 当前目录不是Git仓库
    pause
    exit /b 1
)

echo [信息] 正在检测配置文件变更...
echo.

REM 检查后端配置变更
echo [步骤 1/3] 检查后端配置文件...
if exist "backend\.env.example" (
    if exist "backend\.env" (
        fc /N "backend\.env.example" "backend\.env" > nul 2>&1
        if errorlevel 1 (
            echo [发现] 后端配置文件有差异
            echo ----------------------------------------
            echo 模板文件: backend\.env.example
            echo 当前配置: backend\.env
            echo ----------------------------------------
            
            REM 显示具体差异
            echo [详细对比]:
            fc "backend\.env.example" "backend\.env" 2>nul | findstr /V "正在比较文件" | findstr /V "FC: 找不到差异"
            
            echo.
            echo [建议操作]:
            echo 1. 检查新增的配置项
            echo 2. 更新您的 .env 文件
            echo 3. 重新启动服务以应用配置
            echo.
        ) else (
            echo [OK] 后端配置文件无差异
        )
    ) else (
        echo [警告] 未找到后端配置文件 backend\.env
        echo [建议] 从模板创建: copy backend\.env.example backend\.env
    )
) else (
    echo [警告] 未找到后端配置模板文件
)

echo.

REM 检查前端配置变更
echo [步骤 2/3] 检查前端配置文件...
if exist "frontend\.env.example" (
    if exist "frontend\.env" (
        fc /N "frontend\.env.example" "frontend\.env" > nul 2>&1
        if errorlevel 1 (
            echo [发现] 前端配置文件有差异
            echo ----------------------------------------
            echo 模板文件: frontend\.env.example
            echo 当前配置: frontend\.env
            echo ----------------------------------------
            
            REM 显示具体差异
            echo [详细对比]:
            fc "frontend\.env.example" "frontend\.env" 2>nul | findstr /V "正在比较文件" | findstr /V "FC: 找不到差异"
            
            echo.
            echo [建议操作]:
            echo 1. 检查新增的配置项
            echo 2. 更新您的 .env 文件
            echo 3. 重新构建前端: npm run build
            echo.
        ) else (
            echo [OK] 前端配置文件无差异
        )
    ) else (
        echo [警告] 未找到前端配置文件 frontend\.env
        echo [建议] 从模板创建: copy frontend\.env.example frontend\.env
    )
) else (
    echo [警告] 未找到前端配置模板文件
)

echo.

REM 检查依赖文件变更
echo [步骤 3/3] 检查依赖文件变更...

REM 检查Python依赖
if exist "backend\requirements.txt" (
    git diff HEAD~1 backend\requirements.txt > nul 2>&1
    if not errorlevel 1 (
        echo [发现] Python依赖文件有更新
        echo [建议] 更新依赖: cd backend ^&^& pip install -r requirements.txt
    ) else (
        echo [OK] Python依赖无变更
    )
) else (
    echo [警告] 未找到Python依赖文件
)

REM 检查Node.js依赖
if exist "frontend\package.json" (
    git diff HEAD~1 frontend\package.json > nul 2>&1
    if not errorlevel 1 (
        echo [发现] Node.js依赖文件有更新
        echo [建议] 更新依赖: cd frontend ^&^& npm install
    ) else (
        echo [OK] Node.js依赖无变更
    )
) else (
    echo [警告] 未找到Node.js依赖文件
)

echo.
echo ====================================================
echo                   检测完成！
echo ====================================================
echo.

REM 提供快捷操作选项
echo [快捷操作]:
echo 1. 从模板重新创建配置文件
echo 2. 显示详细的配置差异
echo 3. 退出
echo.
choice /C 123 /M "请选择操作" /T 30 /D 3

if errorlevel 3 goto :end
if errorlevel 2 goto :show_diff
if errorlevel 1 goto :recreate_config

:recreate_config
echo.
echo [执行] 重新创建配置文件...
if exist "backend\.env.example" (
    copy /y "backend\.env.example" "backend\.env" > nul
    echo [成功] 后端配置文件已重新创建
)
if exist "frontend\.env.example" (
    copy /y "frontend\.env.example" "frontend\.env" > nul
    echo [成功] 前端配置文件已重新创建
)
echo [警告] 请检查并修改必要的配置项 (如SECRET_KEY等)
goto :end

:show_diff
echo.
echo [详细差异对比]:
echo.
if exist "backend\.env.example" if exist "backend\.env" (
    echo === 后端配置差异 ===
    fc "backend\.env.example" "backend\.env" 2>nul
    echo.
)
if exist "frontend\.env.example" if exist "frontend\.env" (
    echo === 前端配置差异 ===
    fc "frontend\.env.example" "frontend\.env" 2>nul
    echo.
)

:end
echo.
pause