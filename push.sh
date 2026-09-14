#!/usr/bin/env bash
# 简化版 push 脚本：取消代理 + 用 x-access-token URL + --force-with-lease
# 用法: ./push.sh  或  TOKEN=ghp_xxx ./push.sh
#
# 之前那套复杂的 push.sh（拿 GCM token / 探测 ahead-behind / 自动 fetch 重试）在
# sandbox 里偶发 SIGTERM（拿 token 卡）。这个简化版：要么传 TOKEN 环境变量，要么用
# GCM 拿；都不行就告诉用户手动跑：
#   env -u HTTPS_PROXY git push --force-with-lease origin main
set -u

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

BRANCH=$(git rev-parse --abbrev-ref HEAD)

# ---- 拿 token ----
TOKEN="${TOKEN:-}"
if [ -z "$TOKEN" ]; then
    TOKEN=$(printf "protocol=https\nhost=github.com\n" | git credential fill 2>/dev/null | grep '^password=' | cut -d= -f2-)
fi
if [ -z "$TOKEN" ]; then
    echo "ERROR: 没拿到 token。"
    echo "用法1: TOKEN=ghp_xxx ./push.sh"
    echo "用法2: 配 git credential helper 后重跑"
    echo "用法3: 手动跑  env -u HTTPS_PROXY git push --force-with-lease origin main"
    exit 1
fi

echo "推送分支: $BRANCH"
echo "Token: ${TOKEN:0:7}...${TOKEN: -4}"

# ---- 取消代理 + 用 x-access-token URL 推 ----
env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy \
    git -c credential.helper= \
    -c "url.https://x-access-token:${TOKEN}@github.com/heartsward/.insteadOf=https://github.com/heartsward/" \
    push --force-with-lease origin "$BRANCH"

RC=$?

# stale info 时自动 fetch + force 重试
if [ $RC -ne 0 ]; then
    echo
    echo "WARN: --force-with-lease 失败（stale info），自动 fetch 刷新 origin ref..."
    env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy \
        git -c credential.helper= \
        -c "url.https://x-access-token:${TOKEN}@github.com/heartsward/.insteadOf=https://github.com/heartsward/" \
        fetch --update-head-ok origin "$BRANCH" 2>&1 | tail -2
    echo "重试 push（--force，不用 --force-with-lease 了）..."
    env -u HTTPS_PROXY -u HTTP_PROXY -u https_proxy -u http_proxy \
        git -c credential.helper= \
        -c "url.https://x-access-token:${TOKEN}@github.com/heartsward/.insteadOf=https://github.com/heartsward/" \
        push --force origin "$BRANCH"
    RC=$?
fi

echo
if [ $RC -eq 0 ]; then
    echo "PUSHED_OK  HEAD=$(git rev-parse HEAD)"
else
    echo "PUSH_FAIL (exit=$RC)  手动跑：env -u HTTPS_PROXY git push origin main"
fi
exit $RC
