# -*- coding: utf-8 -*-
"""27.16 端到端验收：MD 编辑保存链路

覆盖两个用户实测 bug（存储层单测在 backend/tests/test_wiki_markdown_roundtrip.py，
这里补 API 层——预览端点与 DB 回写）：

A. `GET /api/v1/wiki/doc/{id}/markdown` 只返回**正文**（不再带 frontmatter）
B. `PUT` 保存后 `documents.content` 被回写 → `GET /api/v1/search/preview` 能看到改动
C. 连续保存 3 次，MD 文件里 frontmatter 恒为 **1 段**（不再逐次累积）
D. 正文逐字节保持一致

跑完会把 MD 文件和 DB content **恢复原样**。

用法
----
    # 默认打本机 8002
    python scripts/e2e_wiki_markdown_edit.py

    # 打别处（如线上）
    python scripts/e2e_wiki_markdown_edit.py --base http://192.168.66.126:8002

    # 指定账号 / 文档
    python scripts/e2e_wiki_markdown_edit.py --user admin --password admin123 --doc-id 1

注意：会挑一个「有 MD 副本 + DB 里有记录」的文档做临时改动，结束后还原；
建议在非生产库上跑，或至少确认脚本能正常走完恢复流程。
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).parent.parent / "backend"
DB_PATH = BACKEND / "yunwei_docs.db"
WIKI_DIR = BACKEND / "wiki"

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.DOTALL)


def make_opener():
    """绕过 HTTP_PROXY：本机常配了代理，回环请求会被拦成 502"""
    for k in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
              "all_proxy", "ALL_PROXY"):
        os.environ.pop(k, None)
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def call(opener, method, url, token=None, body=None, timeout=60):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def login(opener, base, user, password):
    data = urllib.parse.urlencode({"username": user, "password": password}).encode()
    req = urllib.request.Request(base + "/api/v1/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with opener.open(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))["access_token"]


def count_blocks(text):
    n, rest = 0, text
    while True:
        m = FM_RE.match(rest)
        if not m:
            return n
        n += 1
        rest = rest[m.end():]


def main():
    ap = argparse.ArgumentParser(description="27.16 MD 编辑保存链路 e2e")
    ap.add_argument("--base", default="http://127.0.0.1:8002")
    ap.add_argument("--user", default="admin")
    ap.add_argument("--password", default="admin123")
    ap.add_argument("--doc-id", type=int, default=None, help="指定文档（默认自动挑一个）")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    opener = make_opener()
    token = login(opener, base, args.user, args.password)
    print(f"登录 OK -> {base}")

    if not DB_PATH.exists():
        print(f"ERROR: 找不到数据库 {DB_PATH}")
        return 1
    conn = sqlite3.connect(str(DB_PATH))
    db_content = {r[0]: r[1] for r in conn.execute("SELECT id, content FROM documents")}

    if args.doc_id:
        target = args.doc_id
    else:
        cands = sorted(int(p.stem) for p in WIKI_DIR.glob("*.md") if p.stem.isdigit())
        target = next((i for i in cands if i in db_content), None)
    if target is None or target not in db_content:
        print("找不到同时具备 MD 副本和 DB 记录的文档，无法验收")
        conn.close()
        return 1

    md_path = WIKI_DIR / f"{target}.md"
    if not md_path.exists():
        print(f"ERROR: MD 副本不存在 {md_path}")
        conn.close()
        return 1

    orig_md = md_path.read_text(encoding="utf-8")
    orig_db = db_content[target]
    print(f"目标文档 doc_id={target}（md {len(orig_md)} 字节 / db content {len(orig_db or '')} 字符）")

    fails = []
    try:
        # ---- A ----
        got = call(opener, "GET", f"{base}/api/v1/wiki/doc/{target}/markdown", token)
        content = got.get("content", "")
        if content.startswith("---"):
            fails.append("A：GET 仍返回 frontmatter")
            print("A  x GET 仍带 frontmatter")
        else:
            print(f"A  v GET 只回正文（{len(content)} 字符），"
                  f"frontmatter 单独返回 {len(got.get('frontmatter', ''))} 字符")

        # ---- B / C / D ----
        marker = "E2E_27.16_MARKER"
        body_new = content.rstrip("\n") + f"\n\n{marker}\n"
        for i in range(1, 4):
            r = call(opener, "PUT", f"{base}/api/v1/wiki/doc/{target}/markdown",
                     token, {"content": body_new})
            n = count_blocks(md_path.read_text(encoding="utf-8"))
            print(f"   第 {i} 次保存 -> frontmatter {n} 段, "
                  f"content_synced={r.get('content_synced')}")
            if not r.get("success"):
                fails.append(f"第 {i} 次保存失败: {r}")
            if n != 1:
                fails.append(f"C：第 {i} 次保存后 frontmatter {n} 段")
            if not r.get("content_synced"):
                fails.append(f"B：第 {i} 次保存未回写 DB content")

        prev = call(opener, "GET",
                    f"{base}/api/v1/search/preview/{target}"
                    "?format_mode=formatted&source=auto", token)
        if marker in (prev.get("content") or ""):
            print(f"B  v 预览端点可见改动（content_source={prev.get('content_source')}）")
        else:
            fails.append("B：预览端点看不到改动")
            print(f"B  x 预览仍是老内容（content_source={prev.get('content_source')}）")

        cur = md_path.read_text(encoding="utf-8")
        while FM_RE.match(cur):
            cur = cur[FM_RE.match(cur).end():]
        if cur.lstrip("\r\n") == body_new.strip("\r\n") + "\n":
            print("D  v 正文逐字节一致")
        else:
            fails.append("D：正文被改动")
            print(f"D  x 正文不一致\n  期望: {body_new[-60:]!r}\n  实际: {cur[-60:]!r}")
    finally:
        md_path.write_text(orig_md, encoding="utf-8")
        conn.execute("UPDATE documents SET content = ? WHERE id = ?", (orig_db, target))
        conn.commit()
        conn.close()
        print(f"\n已恢复 doc {target} 的 md 与 DB content")

    if fails:
        print("\n=== 失败项 ===")
        for f in fails:
            print("  -", f)
        return 1
    print("=== 全部通过 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
