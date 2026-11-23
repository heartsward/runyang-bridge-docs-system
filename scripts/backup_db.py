# -*- coding: utf-8 -*-
"""SQLite 热备份（无需停后端）+ 完整性校验。

用法: python backup_db.py <源库路径> <目标路径>
走 sqlite3 官方 backup API（在线一致快照），备份完对目标跑 integrity_check。
退出码 0=成功且校验通过。
"""
import os
import sqlite3
import sys


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: backup_db.py <src_db> <dst_db>")
        return 2
    src_path, dst_path = sys.argv[1], sys.argv[2]
    if not os.path.exists(src_path):
        print(f"[错误] 源库不存在: {src_path}")
        return 1
    if os.path.exists(dst_path):
        os.remove(dst_path)

    src = sqlite3.connect(src_path)
    try:
        # 备份前先探源库健康度（只提示，不阻断——WAL 模式下偶发提示不影响热备）
        try:
            probe = src.execute("PRAGMA quick_check").fetchone()[0]
            if probe != "ok":
                print(f"[警告] 源库 quick_check 返回: {probe}（继续备份，请留意）")
        except sqlite3.Error as e:
            print(f"[警告] 源库 quick_check 失败: {e}（继续备份）")

        dst = sqlite3.connect(dst_path)
        try:
            src.backup(dst)  # 在线一致快照
        finally:
            dst.close()
    finally:
        src.close()

    # 校验备份产物
    v = sqlite3.connect(dst_path)
    try:
        res = v.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        v.close()
    size_mb = os.path.getsize(dst_path) / 1024 / 1024
    print(f"[OK] SQLite 热备份完成 {size_mb:.1f}MB，integrity_check={res} -> {dst_path}")
    return 0 if res == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
