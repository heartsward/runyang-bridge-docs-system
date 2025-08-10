#!/bin/bash
# 润扬大桥运维文档管理系统 - 生产环境安全更新脚本 (Linux/macOS)

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

echo_step() {
    echo -e "${CYAN}[步骤 $1]${NC} $2"
}

# 错误处理函数
error_exit() {
    echo_error "$1"
    if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
        echo_info "恢复配置文件..."
        [ -f "$BACKUP_DIR/backend.env.backup" ] && cp "$BACKUP_DIR/backend.env.backup" "backend/.env"
        [ -f "$BACKUP_DIR/frontend.env.backup" ] && cp "$BACKUP_DIR/frontend.env.backup" "frontend/.env"
        echo_info "重新启动原版本服务..."
        ./start-production.sh &
    fi
    exit 1
}

# 清屏并显示标题
clear
echo "===================================================="
echo "     润扬大桥运维文档管理系统 - 生产环境安全更新"
echo "===================================================="
echo

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo_error "当前目录不是Git仓库，请确保在项目根目录执行"
    exit 1
fi

# 步骤1: 检查网络连接
echo_step "1/10" "检查网络连接..."
if ! ping -c 1 github.com > /dev/null 2>&1; then
    error_exit "无法连接到GitHub，请检查网络连接"
fi
echo_success "网络连接正常"

# 步骤2: 显示当前版本信息
echo
echo_step "2/10" "显示当前版本信息..."
echo_info "当前版本信息:"
git log -1 --oneline
echo_info "当前分支: $(git branch --show-current)"
echo_info "远程仓库状态:"
git remote -v

# 步骤3: 检查远程更新
echo
echo_step "3/10" "检查远程更新..."
if ! git fetch origin; then
    error_exit "无法从远程仓库获取更新"
fi

# 步骤4: 比较本地和远程版本
UPDATE_COUNT=$(git rev-list HEAD...origin/main --count)
if [ "$UPDATE_COUNT" -eq 0 ]; then
    echo_info "已是最新版本，无需更新"
    read -p "是否强制重新部署? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo_info "退出更新程序"
        exit 0
    fi
else
    echo_info "发现 $UPDATE_COUNT 个新提交，需要更新"
fi

# 步骤4: 显示待更新的内容
echo
echo_step "4/10" "显示待更新内容..."
if [ "$UPDATE_COUNT" -gt 0 ]; then
    echo_info "待更新的提交:"
    git log HEAD..origin/main --oneline
    echo
    read -p "是否继续更新? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo_info "用户取消更新"
        exit 0
    fi
fi

# 步骤5: 创建备份
echo
echo_step "5/10" "创建备份..."
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backup_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"
echo_info "备份当前配置文件..."
[ -f "backend/.env" ] && cp "backend/.env" "$BACKUP_DIR/backend.env.backup"
[ -f "frontend/.env" ] && cp "frontend/.env" "$BACKUP_DIR/frontend.env.backup"
[ -f "yunwei_docs.db" ] && cp "yunwei_docs.db" "$BACKUP_DIR/database.backup"
[ -f "yunwei_docs_clean.db" ] && cp "yunwei_docs_clean.db" "$BACKUP_DIR/database_clean.backup"
echo_success "配置备份已保存到: $BACKUP_DIR"

# 步骤6: 安全停止服务
echo
echo_step "6/10" "安全停止当前服务..."
echo_info "正在优雅地停止服务..."
if [ -f "./stop-services.sh" ]; then
    ./stop-services.sh
else
    echo_warning "未找到停止服务脚本，尝试手动停止..."
    # 手动停止进程
    pkill -f "database_integrated_server.py" 2>/dev/null
    pkill -f "npm.*run.*dev" 2>/dev/null
fi
sleep 3

# 步骤7: 更新代码
echo
echo_step "7/10" "更新代码..."
git stash push -m "Auto-stash before update $(date)"
if ! git pull origin main; then
    echo_error "代码更新失败，正在恢复..."
    git stash pop
    echo_info "重新启动原版本服务..."
    ./start-production.sh &
    exit 1
fi
echo_success "代码更新完成"

# 步骤8: 检查配置文件变更
echo
echo_step "8/10" "检查配置文件变更..."
if [ -f "$BACKUP_DIR/backend.env.backup" ] && [ -f "backend/.env.example" ]; then
    if ! diff "backend/.env.example" "$BACKUP_DIR/backend.env.backup" > /dev/null 2>&1; then
        echo_warning "后端配置模板有更新，请检查以下文件:"
        echo "  新模板: backend/.env.example"
        echo "  当前配置: backend/.env"
        echo_info "请对比并手动更新必要的配置项"
        read -p "按任意键继续..."
    fi
fi

if [ -f "$BACKUP_DIR/frontend.env.backup" ] && [ -f "frontend/.env.example" ]; then
    if ! diff "frontend/.env.example" "$BACKUP_DIR/frontend.env.backup" > /dev/null 2>&1; then
        echo_warning "前端配置模板有更新，请检查以下文件:"
        echo "  新模板: frontend/.env.example"
        echo "  当前配置: frontend/.env"
        echo_info "请对比并手动更新必要的配置项"
        read -p "按任意键继续..."
    fi
fi

# 步骤9: 恢复配置文件
echo
echo_step "9/10" "恢复配置文件..."
if [ -f "$BACKUP_DIR/backend.env.backup" ]; then
    cp "$BACKUP_DIR/backend.env.backup" "backend/.env"
    echo_success "后端配置已恢复"
fi
if [ -f "$BACKUP_DIR/frontend.env.backup" ]; then
    cp "$BACKUP_DIR/frontend.env.backup" "frontend/.env"
    echo_success "前端配置已恢复"
fi

# 步骤10: 重新启动服务
echo
echo_step "10/10" "重新启动服务..."
echo_info "启动更新后的系统..."
./start-production.sh &

# 等待服务启动
echo
echo_info "等待服务启动完成..."
sleep 10

# 验证服务状态
echo_info "验证服务状态..."
if curl -s --max-time 5 http://localhost:8002/health > /dev/null 2>&1; then
    echo_success "后端服务运行正常"
else
    echo_warning "后端服务可能未正常启动，请检查日志"
fi

if curl -s --max-time 5 http://localhost:5173 > /dev/null 2>&1; then
    echo_success "前端服务运行正常"
else
    echo_warning "前端服务可能未正常启动，请检查日志"
fi

echo
echo "===================================================="
echo "                   更新完成！"
echo "===================================================="
echo
echo_success "系统更新详情:"
git log -1 --oneline
echo
echo_info "服务访问地址:"
echo "  前端界面: http://localhost:5173"
echo "  后端API:  http://localhost:8002"
echo "  API文档:  http://localhost:8002/docs"
echo
echo_info "备份文件位置: $BACKUP_DIR"
echo_info "回滚命令: git reset --hard HEAD~1"
echo
echo_success "更新完成！系统已重新启动"