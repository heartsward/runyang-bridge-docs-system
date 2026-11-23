# -*- coding: utf-8 -*-
"""备份保留策略：删除过期快照目录，保留最近 N 份 + 天数窗口内全部。

用法: python prune_backups.py <backups_root> [--keep-days 14] [--keep-count 7] [--dry-run]

只处理 backups_root 直接子目录里名字形如 YYYYMMDD_HHMMSS / YYYYMMDD 的快照，
其它目录/文件一律不碰。安全护栏：backups_root 为空/为盘根/不含 backup 关键字则拒绝。
"""
import argparse
import os
import re
import shutil
import sys
from datetime import datetime, timedelta

SNAP_RE = re.compile(r"^(\d{8})(?:_(\d{6}))?$")


def parse_snap(name: str):
    m = SNAP_RE.match(name)
    if not m:
        return None
    d = m.group(1)
    t = m.group(2) or "000000"
    try:
        return datetime.strptime(d + t, "%Y%m%d%H%M%S")
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("backups_root")
    ap.add_argument("--keep-days", type=int, default=14)
    ap.add_argument("--keep-count", type=int, default=7, help="无论如何保留最近多少份（防止误删全空）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.backups_root)
    if not root or root in ("/", "\\") or re.match(r"^[A-Za-z]:\\?$", root):
        print(f"[拒绝] 备份根目录过宽，可能误删：{root}")
        return 1
    if "backup" not in root.lower() and "备份" not in root:
        print(f"[拒绝] 备份根目录路径不含 backup/备份 关键字，为避免误删已中止：{root}")
        print("       请把备份放在名字含 backup 的目录下，例如 D:\\rywd-backup")
        return 1
    if not os.path.isdir(root):
        print(f"[跳过] 备份根目录不存在，无需清理：{root}")
        return 0

    snaps = []
    for name in os.listdir(root):
        full = os.path.join(root, name)
        if not os.path.isdir(full):
            continue
        ts = parse_snap(name)
        if ts is not None:
            snaps.append((ts, name, full))
    snaps.sort(reverse=True)  # 最新在前

    cutoff = datetime.now() - timedelta(days=args.keep_days)
    to_delete, to_keep = [], []
    for i, (ts, name, full) in enumerate(snaps):
        if i < args.keep_count or ts >= cutoff:
            to_keep.append(name)
        else:
            to_delete.append((name, full))

    if not to_delete:
        print(f"[清理] 无需删除（共 {len(snaps)} 份快照，均在保留窗口内）")
        return 0

    for name, full in to_delete:
        if args.dry_run:
            print(f"[dry-run] 将删除: {name}")
            continue
        try:
            shutil.rmtree(full)
            print(f"[已删除] {name}")
        except OSError as e:
            print(f"[删除失败] {name}: {e}")
    print(f"[清理] 保留 {len(to_keep)} 份，删除 {len(to_delete)} 份（keep-days={args.keep_days}, keep-count={args.keep_count}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
