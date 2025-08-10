#!/bin/bash
# 润扬大桥运维文档管理系统 - 配置变更检测工具 (Linux/macOS)

# 设置脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 输出带颜色的信息
echo_info() {
    echo -e "${BLUE}[信息]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

echo_error() {
    echo -e "${RED}[错误]${NC} $1"
}

echo_found() {
    echo -e "${CYAN}[发现]${NC} $1"
}

echo_step() {
    echo -e "${CYAN}[步骤 $1]${NC} $2"
}

# 清屏并显示标题
clear
echo "===================================================="
echo "     润扬大桥运维文档管理系统 - 配置变更检测工具"
echo "===================================================="
echo

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo_error "当前目录不是Git仓库"
    exit 1
fi

echo_info "正在检测配置文件变更..."
echo

CONFIG_CHANGED=false

# 步骤1: 检查后端配置变更
echo_step "1/3" "检查后端配置文件..."
if [ -f "backend/.env.example" ]; then
    if [ -f "backend/.env" ]; then
        if ! diff -q "backend/.env.example" "backend/.env" > /dev/null 2>&1; then
            echo_found "后端配置文件有差异"
            echo "----------------------------------------"
            echo "模板文件: backend/.env.example"
            echo "当前配置: backend/.env"
            echo "----------------------------------------"
            
            echo -e "${YELLOW}[详细对比]:${NC}"
            diff --unified=0 "backend/.env.example" "backend/.env" | grep -E '^[+-]' | head -20
            
            echo
            echo -e "${GREEN}[建议操作]:${NC}"
            echo "1. 检查新增的配置项"
            echo "2. 更新您的 .env 文件"
            echo "3. 重新启动服务以应用配置"
            echo
            CONFIG_CHANGED=true
        else
            echo_success "后端配置文件无差异"
        fi
    else
        echo_warning "未找到后端配置文件 backend/.env"
        echo_info "建议从模板创建: cp backend/.env.example backend/.env"
        CONFIG_CHANGED=true
    fi
else
    echo_warning "未找到后端配置模板文件"
fi

echo

# 步骤2: 检查前端配置变更  
echo_step "2/3" "检查前端配置文件..."
if [ -f "frontend/.env.example" ]; then
    if [ -f "frontend/.env" ]; then
        if ! diff -q "frontend/.env.example" "frontend/.env" > /dev/null 2>&1; then
            echo_found "前端配置文件有差异"
            echo "----------------------------------------"
            echo "模板文件: frontend/.env.example"
            echo "当前配置: frontend/.env"
            echo "----------------------------------------"
            
            echo -e "${YELLOW}[详细对比]:${NC}"
            diff --unified=0 "frontend/.env.example" "frontend/.env" | grep -E '^[+-]' | head -20
            
            echo
            echo -e "${GREEN}[建议操作]:${NC}"
            echo "1. 检查新增的配置项"
            echo "2. 更新您的 .env 文件"
            echo "3. 重新构建前端: npm run build"
            echo
            CONFIG_CHANGED=true
        else
            echo_success "前端配置文件无差异"
        fi
    else
        echo_warning "未找到前端配置文件 frontend/.env"
        echo_info "建议从模板创建: cp frontend/.env.example frontend/.env"
        CONFIG_CHANGED=true
    fi
else
    echo_warning "未找到前端配置模板文件"
fi

echo

# 步骤3: 检查依赖文件变更
echo_step "3/3" "检查依赖文件变更..."

# 检查Python依赖
if [ -f "backend/requirements.txt" ]; then
    if git diff --quiet HEAD~1 backend/requirements.txt 2>/dev/null; then
        echo_success "Python依赖无变更"
    else
        echo_found "Python依赖文件有更新"
        echo_info "建议更新依赖: cd backend && pip install -r requirements.txt"
        CONFIG_CHANGED=true
    fi
else
    echo_warning "未找到Python依赖文件"
fi

# 检查Node.js依赖
if [ -f "frontend/package.json" ]; then
    if git diff --quiet HEAD~1 frontend/package.json 2>/dev/null; then
        echo_success "Node.js依赖无变更"
    else
        echo_found "Node.js依赖文件有更新"
        echo_info "建议更新依赖: cd frontend && npm install"
        CONFIG_CHANGED=true
    fi
else
    echo_warning "未找到Node.js依赖文件"
fi

echo
echo "===================================================="
echo "                   检测完成！"
echo "===================================================="
echo

# 提供交互式操作选项
if [ "$CONFIG_CHANGED" = true ]; then
    echo -e "${YELLOW}[检测结果]: 发现配置或依赖变更${NC}"
    echo
    echo "[快捷操作]:"
    echo "1. 从模板重新创建配置文件"
    echo "2. 显示详细的配置差异对比"
    echo "3. 自动更新依赖包"
    echo "4. 退出"
    echo
    read -p "请选择操作 [1-4, 默认4]: " choice
    
    case $choice in
        1)
            echo
            echo_info "重新创建配置文件..."
            if [ -f "backend/.env.example" ]; then
                cp "backend/.env.example" "backend/.env"
                echo_success "后端配置文件已重新创建"
            fi
            if [ -f "frontend/.env.example" ]; then
                cp "frontend/.env.example" "frontend/.env"
                echo_success "前端配置文件已重新创建"
            fi
            echo_warning "请检查并修改必要的配置项 (如SECRET_KEY等)"
            ;;
        2)
            echo
            echo -e "${CYAN}[详细差异对比]:${NC}"
            echo
            if [ -f "backend/.env.example" ] && [ -f "backend/.env" ]; then
                echo "=== 后端配置差异 ==="
                diff --unified=3 --color=always "backend/.env.example" "backend/.env" 2>/dev/null || true
                echo
            fi
            if [ -f "frontend/.env.example" ] && [ -f "frontend/.env" ]; then
                echo "=== 前端配置差异 ==="
                diff --unified=3 --color=always "frontend/.env.example" "frontend/.env" 2>/dev/null || true
                echo
            fi
            ;;
        3)
            echo
            echo_info "自动更新依赖包..."
            if [ -f "backend/requirements.txt" ]; then
                echo_info "更新Python依赖..."
                cd backend && pip install -r requirements.txt && cd ..
            fi
            if [ -f "frontend/package.json" ]; then
                echo_info "更新Node.js依赖..."
                cd frontend && npm install && cd ..
            fi
            echo_success "依赖更新完成"
            ;;
        4|"")
            echo_info "退出配置检测工具"
            ;;
        *)
            echo_warning "无效选择，退出"
            ;;
    esac
else
    echo_success "所有配置和依赖都是最新的，无需更新"
fi

echo