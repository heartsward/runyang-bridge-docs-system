# -*- coding: utf-8 -*-
"""修复 Wiki MD 副本 frontmatter 重复（27.16 配套数据清理）

背景 bug
--------
`storage.update()` 曾把磁盘上的 frontmatter 再拼一次，而前端编辑器加载的是
"全文（含 frontmatter）"，于是每保存一次，文件开头就多一段完全相同的
`title / source_file / doc_type ...`。

本脚本做的事
-----------
把每个 md 文件开头**连续重复**的 frontmatter 块压成一段（只保留第一段），
正文一个字节都不动。另外可选：

- `--sync-db`：把这些文档的 `documents.content` 同步为 MD 正文
  （预览端点读的是 DB content，历史编辑过的文档 DB 里还是老内容）

用法
----
    python scripts/fix_wiki_frontmatter.py                # 只体检，不改任何文件
    python scripts/fix_wiki_frontmatter.py --apply        # 修复文件（先自动备份）
    python scripts/fix_wiki_frontmatter.py --apply --sync-db   # 顺手同步 DB

安全设计
--------
- **默认 dry-run**，必须显式 `--apply` 才落盘
- 落盘前把原文件整份备份到 `backend/wiki/_fm_backup/<时间戳>/`
- 只压"完全重复"的连续 frontmatter 块；正文逐字节保留（脚本内会断言校验）
"""
import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
WIKI_DIR = BACKEND / "wiki"
DB_PATH = BACKEND / "yunwei_docs.db"

sys.path.insert(0, str(BACKEND))

from app.services.wiki.storage import (  # noqa: E402
    join_frontmatter,
    split_frontmatter,
    strip_frontmatter_blocks,
)


def count_blocks(text: str) -> int:
    n, rest = 0, text
    while True:
        fm, body = split_frontmatter(rest)
        if not fm:
            return n
        n += 1
        rest = body


def scan(wiki_dir: Path):
    """返回 [(path, 块数, 原正文, 修复后全文)]，只含需要修的"""
    todo = []
    for p in sorted(wiki_dir.glob("*.md")):
        original = p.read_text(encoding="utf-8")
        n = count_blocks(original)
        if n < 2:
            continue
        fm, body = strip_frontmatter_blocks(original)
        fixed = join_frontmatter(fm, body)
        # 安全校验：正文必须逐字节一致
        _fm2, body2 = strip_frontmatter_blocks(fixed)
        assert body2 == body, f"正文被改动了，拒绝处理: {p}"
        todo.append((p, n, body, fixed))
    return todo


def main():
    ap = argparse.ArgumentParser(description="修复 Wiki MD 副本 frontmatter 重复")
    ap.add_argument("--apply", action="store_true", help="真正写入（默认只体检）")
    ap.add_argument("--sync-db", action="store_true",
                    help="顺带把这些文档的 documents.content 同步为 MD 正文")
    ap.add_argument("--wiki-dir", default=str(WIKI_DIR), help="wiki 目录（默认 backend/wiki）")
    args = ap.parse_args()

    wiki_dir = Path(args.wiki_dir)
    if not wiki_dir.exists():
        print(f"ERROR: wiki 目录不存在: {wiki_dir}")
        return 1

    todo = scan(wiki_dir)
    total = len(list(wiki_dir.glob("*.md")))
    print(f"扫描 {total} 个 md，其中 frontmatter 重复 {len(todo)} 个")
    print()

    if not todo:
        print("无需修复 ✓")
        return 0

    for p, n, _body, fixed in todo:
        before = len(p.read_text(encoding="utf-8"))
        print(f"  {p.name:<10} {n} 段 -> 1 段   省 {before - len(fixed)} 字节")

    if not args.apply:
        print()
        print("（dry-run）加 --apply 才会落盘")
        return 0

    backup_dir = wiki_dir / "_fm_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    for p, _n, _body, fixed in todo:
        shutil.copy2(p, backup_dir / p.name)
        p.write_text(fixed, encoding="utf-8")
    print()
    print(f"已修复 {len(todo)} 个文件，原件备份在 {backup_dir}")

    if args.sync_db:
        if not DB_PATH.exists():
            print(f"WARN: 数据库不存在，跳过 --sync-db: {DB_PATH}")
            return 0
        conn = sqlite3.connect(str(DB_PATH))
        updated = 0
        for p, _n, body, _fixed in todo:
            try:
                doc_id = int(p.stem)
            except ValueError:
                continue
            cur = conn.execute(
                "UPDATE documents SET content = ?, content_extracted = 1,"
                " content_extraction_error = NULL WHERE id = ?",
                (body, doc_id),
            )
            updated += cur.rowcount
        conn.commit()
        conn.close()
        print(f"已同步 documents.content: {updated} 行")
        print("提示：后端有进程内缓存的话，重启后端使其生效")
    return 0


if __name__ == "__main__":
    sys.exit(main())
