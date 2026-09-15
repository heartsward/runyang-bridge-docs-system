# -*- coding: utf-8 -*-
"""批量预热 PDF 预览缓存（阶段二十四）

把库里所有 Office 文档（.doc/.docx/.xls/.xlsx/.ppt/.pptx/.odt/.ods/.odp/.rtf/.epub）
一次性走 LibreOffice 转 PDF 并缓存到 backend/cache/converted_pdfs/{doc_id}.pdf。

运行方式（在仓库根目录）：
    cd backend && ./venv/Scripts/python ../scripts/batch_convert_previews.py

参数：
    --doc-id N          只转指定文档 ID（可多次传，转多个）
    --force             忽略已有缓存，强制重新转换
    --dry-run           只列出待转换文档，不真转
    --limit N           最多转 N 个（默认不限；防止一次跑太多）
    --skip-missing      跳过文件不存在的（默认是这种情况会报错）
    --workers N         并发数（默认 1；LibreOffice 不允许多实例，串行最稳）

输出：
    进度逐文档打印 + 末尾汇总表格（总数 /新转 /已缓存 /失败 /跳过 /总耗时）

退出码：
    0 全部成功（或 dry-run）
    1 有失败

依赖：
    - LibreOffice 已装（探测路径在 .env LIBREOFFICE_BIN_PATH 或系统 PATH）
    - 后端 venv 已激活（用 ./venv/Scripts/python 跑）
"""
import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 让脚本能 import backend.app.*
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def parse_args():
    p = argparse.ArgumentParser(
        description="批量 PDF 预览预热（阶段二十四）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--doc-id", type=int, action="append",
                   help="只转指定 doc_id（可多次传）")
    p.add_argument("--force", action="store_true",
                   help="忽略已有缓存，强制重转")
    p.add_argument("--dry-run", action="store_true",
                   help="只列出待转换文档，不真转")
    p.add_argument("--limit", type=int, default=0,
                   help="最多转 N 个（0 = 不限）")
    p.add_argument("--skip-missing", action="store_true",
                   help="跳过文件不存在的（默认会报错）")
    p.add_argument("--workers", type=int, default=1,
                   help="并发数（默认 1；LibreOffice 不允许多实例，串行最稳）")
    return p.parse_args()


def fetch_targets(args):
    """从数据库查所有 Office 类型文档"""
    from sqlalchemy import text
    from app.db.database import engine
    from app.services.preview_converter import SUPPORTED_OFFICE_TYPES

    # 把 ".docx" -> "docx" 作为白名单
    exts = [e.lstrip(".") for e in SUPPORTED_OFFICE_TYPES]
    # SQLAlchemy 数组参数：file_type IN :exts 必须配合 bindparam 才能展开；
    # 用 OR 链式拼接最稳，避免动态绑定方言差异
    ext_or = " OR ".join([f"file_type = :ext_{i}" for i in range(len(exts))])
    params = {f"ext_{i}": e for i, e in enumerate(exts)}

    where_clauses = [f"({ext_or})"]
    if args.doc_id:
        # SQLite 不支持 IN 单参数展开（要 IN (?, ?, ...)），按个数展开
        id_placeholders = ", ".join([f":id_{i}" for i in range(len(args.doc_id))])
        where_clauses.append(f"id IN ({id_placeholders})")
        for i, did in enumerate(args.doc_id):
            params[f"id_{i}"] = did

    where_sql = "WHERE " + " AND ".join(where_clauses)

    sql = text(f"""
        SELECT id, title, file_name, file_path, file_type, file_size
        FROM documents
        {where_sql}
        ORDER BY id ASC
    """)

    rows = []
    with engine.connect() as conn:
        result = conn.execute(sql, params)
        for r in result:
            rows.append({
                "id": r[0],
                "title": r[1],
                "file_name": r[2],
                "file_path": r[3],
                "file_type": r[4],
                "file_size": r[5],
            })
    return rows


def fmt_size(n):
    if not n:
        return "0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_dur(sec):
    if sec < 60:
        return f"{sec:.1f}s"
    m, s = divmod(sec, 60)
    return f"{int(m)}m{s:.0f}s"


def main():
    args = parse_args()

    print("=" * 72)
    print("批量 PDF 预览预热（阶段二十四）")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 72)

    # 探测 LibreOffice
    from app.services.preview_converter import (
        get_preview_converter,
    )
    converter = get_preview_converter()
    if not converter.is_available:
        print(f"❌ LibreOffice 不可用: {converter.soffice_path or '未找到'}")
        print("   参见 docs/环境安装-LibreOffice.md 安装后重跑")
        sys.exit(2)
    print(f"✅ LibreOffice 已就绪: {converter.soffice_path}")

    # 查数据库
    try:
        rows = fetch_targets(args)
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        sys.exit(1)
    print(f"📚 库里候选文档: {len(rows)} 条")
    if not rows:
        print("   (无 Office 文档可处理)")
        return 0

    # 应用 limit
    if args.limit > 0 and len(rows) > args.limit:
        print(f"   ⚠️ 应用 --limit {args.limit}, 只处理前 {args.limit} 条")
        rows = rows[:args.limit]

    # 进度统计
    stats = {
        "new_convert": [],   # 首次转换成功
        "cached": [],        # 已命中缓存
        "failed": [],        # 失败
        "missing": [],       # 文件不存在
        "unsupported": [],   # 不支持的扩展名
    }

    total_t0 = time.monotonic()

    for idx, doc in enumerate(rows, 1):
        doc_id = doc["id"]
        title = (doc["title"] or "")[:40]
        ext = (doc["file_type"] or "").lower().lstrip(".")
        path = doc["file_path"]

        # 1) 扩展名预过滤（理论上 fetch_targets 已过滤，留个兜底）
        from app.services.preview_converter import is_supported_office_type
        if not is_supported_office_type(ext):
            stats["unsupported"].append((doc_id, ext))
            continue

        # 2) 文件存在检查
        if not path or not os.path.exists(path):
            if args.skip_missing:
                stats["missing"].append((doc_id, path))
                print(f"[{idx}/{len(rows)}] ⏭️  doc {doc_id}: 文件不存在 (跳过)")
                continue
            else:
                stats["missing"].append((doc_id, path))
                print(f"[{idx}/{len(rows)}] ❌  doc {doc_id}: 文件不存在 ({path})")
                continue

        # 3) dry-run
        if args.dry_run:
            cached = converter.get_cached_pdf(doc_id)
            if cached and not args.force:
                tag = "已缓存"
                stats["cached"].append((doc_id, 0))
            else:
                tag = "将转换"
                stats["new_convert"].append((doc_id, 0))
            print(f"[{idx}/{len(rows)}] 🔍 doc {doc_id} [{title}] (.{ext}, {fmt_size(doc['file_size'])}) — {tag}")
            continue

        # 4) 真转换
        # 先检查缓存（除非 --force）
        if not args.force:
            cached = converter.get_cached_pdf(doc_id)
            if cached:
                stats["cached"].append((doc_id, 0))
                print(f"[{idx}/{len(rows)}] ⚡ doc {doc_id} [{title}] (.{ext}) — 已命中缓存 ({fmt_size(cached.stat().st_size)})")
                continue
        else:
            # --force 模式：先清掉旧缓存（convert_blocking 内部还会判 mtime）
            converter.invalidate_cache(doc_id)

        t0 = time.monotonic()
        try:
            pdf_path = converter.convert_blocking(
                doc_id=doc_id, file_path=path, file_type=ext
            )
            elapsed = time.monotonic() - t0
            stats["new_convert"].append((doc_id, elapsed))
            print(f"[{idx}/{len(rows)}] ✅ doc {doc_id} [{title}] (.{ext}, {fmt_size(doc['file_size'])}) → {fmt_size(pdf_path.stat().st_size)} PDF ({fmt_dur(elapsed)})")
        except Exception as e:
            elapsed = time.monotonic() - t0
            stats["failed"].append((doc_id, str(e), elapsed))
            print(f"[{idx}/{len(rows)}] ❌ doc {doc_id} [{title}] (.{ext}) — 失败 ({fmt_dur(elapsed)}): {e}")

    total_elapsed = time.monotonic() - total_t0

    # 汇总
    print()
    print("=" * 72)
    print("汇总")
    print("=" * 72)
    print(f"  候选总数:   {len(rows)} 条")
    print(f"  ✅ 新转成功: {len(stats['new_convert'])} 条 (累计 {fmt_dur(sum(s[1] for s in stats['new_convert']))})")
    print(f"  ⚡ 已缓存:   {len(stats['cached'])} 条")
    print(f"  ⏭️  文件缺失:{len(stats['missing'])} 条")
    print(f"  🚫 非Office: {len(stats['unsupported'])} 条")
    print(f"  ❌ 失败:     {len(stats['failed'])} 条")
    print(f"  总耗时:     {fmt_dur(total_elapsed)}")

    if stats["failed"]:
        print()
        print("失败明细:")
        for doc_id, err, elapsed in stats["failed"]:
            err_short = err[:100] + ("..." if len(err) > 100 else "")
            print(f"  doc {doc_id}: {err_short} ({fmt_dur(elapsed)})")

    # 失败非零 → 退出码 1
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())