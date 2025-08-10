#!/bin/bash
# 润扬大桥运维文档管理系统 - 版本更新发布脚本 (Linux/macOS)

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

# 清屏并显示标题
clear
echo "===================================================="
echo "     润扬大桥运维文档管理系统 - 版本更新发布"
echo "===================================================="
echo

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo_error "当前目录不是Git仓库"
    exit 1
fi

# 步骤1: 检查Git状态
echo_step "1/6" "检查Git状态..."
if [ -n "$(git status --porcelain)" ]; then
    echo_info "发现未提交的更改："
    git status --short
    echo
    read -p "是否继续提交这些更改? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo_info "用户取消操作"
        exit 1
    fi
else
    echo_info "工作目录干净，无未提交更改"
fi

# 步骤2: 获取版本信息
echo
echo_step "2/6" "获取版本信息..."
echo "请选择版本类型："
echo "  1) patch  - 补丁版本 (bug修复)"
echo "  2) minor  - 功能版本 (新功能)"
echo "  3) major  - 重大版本 (重大更改)"
read -p "请选择 [1-3, 默认1]: " VERSION_TYPE

case $VERSION_TYPE in
    1|"")
        VERSION_NAME="patch"
        VERSION_DESC="补丁版本"
        ;;
    2)
        VERSION_NAME="minor"
        VERSION_DESC="功能版本"
        ;;
    3)
        VERSION_NAME="major"
        VERSION_DESC="重大版本"
        ;;
    *)
        VERSION_NAME="patch"
        VERSION_DESC="补丁版本"
        echo_info "无效选择，默认为补丁版本"
        ;;
esac

# 获取更新说明
echo
read -p "请输入本次更新的简要说明: " UPDATE_DESC
if [ -z "$UPDATE_DESC" ]; then
    UPDATE_DESC="常规更新和优化"
fi

# 步骤3: 添加所有更改到暂存区
echo
echo_step "3/6" "添加更改到暂存区..."
git add .
if [ $? -ne 0 ]; then
    echo_error "添加文件到暂存区失败"
    exit 1
fi

# 步骤4: 创建提交
echo
echo_step "4/6" "创建提交..."
git commit -m "$(cat <<EOF
feat: $UPDATE_DESC

- ${VERSION_DESC}更新
- 系统功能优化和bug修复
- 文档和配置更新

🚀 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

if [ $? -ne 0 ]; then
    echo_error "提交失败"
    exit 1
fi

# 步骤5: 创建版本标签
echo
echo_step "5/6" "创建版本标签..."
COMMIT_COUNT=$(git rev-list --count HEAD)
TAG_NAME="v1.0.$COMMIT_COUNT"
git tag -a "$TAG_NAME" -m "${VERSION_DESC}: $UPDATE_DESC"
echo_success "创建版本标签: $TAG_NAME"

# 步骤6: 推送到远程仓库
echo
echo_step "6/6" "推送到GitHub..."
echo_info "推送代码到远程仓库..."
git push origin main
if [ $? -ne 0 ]; then
    echo_error "推送代码失败"
    exit 1
fi

echo_info "推送标签到远程仓库..."
git push origin "$TAG_NAME"
if [ $? -ne 0 ]; then
    echo_warning "推送标签失败，但代码已成功推送"
fi

echo
echo "===================================================="
echo "                  发布成功！"
echo "===================================================="
echo
echo_success "版本信息:"
echo "  版本标签: $TAG_NAME"
echo "  版本类型: $VERSION_DESC"
echo "  更新说明: $UPDATE_DESC"
echo
echo_info "远程仓库已更新，部署服务器可以拉取最新版本"
echo
echo_info "生产服务器更新命令:"
echo "  Windows: deploy-update.bat"
echo "  Linux:   ./deploy-update.sh"
echo