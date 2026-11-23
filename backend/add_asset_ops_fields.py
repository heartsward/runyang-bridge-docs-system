# -*- coding: utf-8 -*-
"""幂等迁移脚本（32.7）：为 assets 表新增 5 列（中间件版本 + 运维责任四件套）。

与 add_asset_groups.py 同套路：项目无 alembic，create_all 不给存量表加列，
每台存量库（本地 / 126 生产）部署新代码后需手动执行一次本脚本。

新增列：
  middleware_version  TEXT  中间件版本
  dev_company         TEXT  开发单位
  ops_company         TEXT  运维单位
  contact_person      TEXT  联系人
  contact_phone       TEXT  联系电话

用法（在 backend 目录下）：
    venv/Scripts/python.exe add_asset_ops_fields.py
可重复执行；已存在的列跳过。
"""
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yunwei_docs.db")

NEW_COLUMNS = [
    ("middleware_version", "TEXT"),
    ("dev_company", "TEXT"),
    ("ops_company", "TEXT"),
    ("contact_person", "TEXT"),
    ("contact_phone", "TEXT"),
]


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[错误] 数据库文件不存在: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(assets)").fetchall()}
        added = 0
        for name, typ in NEW_COLUMNS:
            if name in cols:
                print(f"[跳过] assets.{name} 已存在")
                continue
            conn.execute(f'ALTER TABLE assets ADD COLUMN "{name}" {typ}')
            added += 1
            print(f'[完成] 已新增 assets.{name} ({typ})')
        conn.commit()
        print(f"[结果] 本次新增 {added} 列，跳过 {len(NEW_COLUMNS) - added} 列")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
