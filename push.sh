#!/usr/bin/env bash
# 一键把本地 commit 推送到 GitHub
# 用法: ./push.sh
#
# 设计原则：
# - 解决"git push 卡很久"问题：WorkBuddy 代理对 git smart-HTTP 返回 401 + GCM 默认走 Basic Auth
#   也被 GitHub fine-grained PAT 拒；改用 `url.x-access-token:TOKEN@github.com/.insteadOf`
#   让 git 知道走 token 格式，401 问题秒解
# - 解决"本地领先 / 远端领先 diverged"问题：用 `git push --force-with-lease` 而不是 `git push`
#   （之前用 Git Data API 推的 commit 会让远端 SHA 与本地不同，但内容一致；force-with-lease
#   比 --force 安全：若远端被其他人/进程更新过则拒绝覆盖）
# - 默认 push 当前分支（不是 main），避免误推其它分支
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=========================================="
echo "  Runyang Bridge System - Push to GitHub"
echo "=========================================="
echo

# ---- 0. 防御性检查：工作区必须干净（先 commit 再 push）----
if ! git diff --quiet HEAD 2>/dev/null || ! git diff --cached --quiet HEAD 2>/dev/null; then
    echo "WARN: 工作区有未提交改动。"
    echo "       请先 'git add .' + 'git commit -m \"...\"' 再跑 push.sh"
    echo "       （不想 commit？回滚用 'git restore .'）"
    exit 1
fi

# ---- 1. 拿当前分支 ----
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "分支: $BRANCH"
echo

# ---- 2. 拿 token（从 git credential helper，跟 update.sh 一致）----
TOKEN=$(printf "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null | grep '^password=' | cut -d= -f2-)
if [ -z "$TOKEN" ]; then
    echo "ERROR: 拿不到 GitHub token。"
    echo "       请先用 GitHub CLI 登录（gh auth login）或在 Windows 凭据管理器里加 token。"
    exit 1
fi
echo "Token: ${TOKEN:0:10}... (长度 ${#TOKEN})"
echo

# ---- 3. 看本地有几个 commit 待推 ----
AHEAD=$(git rev-list --count "origin/${BRANCH}..HEAD" 2>/dev/null || echo "?")
BEHIND=$(git rev-list --count "HEAD..origin/${BRANCH}" 2>/dev/null || echo "?")
echo "ahead=$AHEAD  behind=$BEHIND"

# ---- 4. 如果 diverged（Git Data API 推送历史常见），用 --force-with-lease ----
PUSH_FLAGS=""
if [ "$AHEAD" != "0" ] && [ "$BEHIND" != "0" ]; then
    echo "检测到 diverged（ahead=$AHEAD, behind=$BEHIND）→ 用 --force-with-lease 覆盖远端"
    PUSH_FLAGS="--force-with-lease"
elif [ "$BEHIND" != "0" ] && [ "$BEHIND" != "?" ]; then
    echo "WARN: 远端领先 $BEHIND 个 commit（你本地没这些更新）。"
    echo "       建议先 'git pull --rebase origin $BRANCH' 整合，再 push。"
    echo "       或者强制覆盖（确认远端没人推过新东西）：'git push --force-with-lease origin $BRANCH'"
    PUSH_FLAGS="--force-with-lease"
fi

# ---- 5. 取消代理 + 用 x-access-token URL 推送 ----
echo
echo "推送中..."
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy \
    git -c credential.helper= \
    -c "url.https://x-access-token:${TOKEN}@github.com/heartsward/.insteadOf=https://github.com/heartsward/" \
    push $PUSH_FLAGS origin "$BRANCH"

RC=$?
echo
if [ $RC -eq 0 ]; then
    NEW_SHA=$(git rev-parse HEAD)
    echo "=========================================="
    echo "  PUSHED_OK"
    echo "=========================================="
    echo "新远端 HEAD: $NEW_SHA"
    echo "GitHub: https://github.com/heartsward/runyang-bridge-docs-system"
else
    echo "=========================================="
    echo "  PUSH_FAIL (exit=$RC)"
    echo "=========================================="
    echo "排查建议："
    echo "  1. 网络: env -u HTTPS_PROXY git ls-remote https://github.com/heartsward/runyang-bridge-docs-system.git HEAD"
    echo "  2. Token 权限: 必须是 fine-grained PAT 且勾选 Contents: Read+Write"
    echo "  3. 如远端被保护（main 需 PR），换到其它分支或联系仓库管理员"
fi
exit $RC
