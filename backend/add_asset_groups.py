# -*- coding: utf-8 -*-
"""幂等迁移脚本：为 assets 表新增 groups（自定义分组）列。

与 add_commissioning_date.py 同套路：项目无 alembic，create_all 不给存量表加列，
每台存量库（本地 / 126 生产）部署新代码后需手动执行一次本脚本。

用法（在 backend 目录下）：
    python add_asset_groups.py

可重复执行；列已存在时输出提示并跳过。
"""
import os
import sqlite3
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yunwei_docs.db")


def main() -> int:
    if not os.path.exists(DB_PATH):
        print(f"[错误] 数据库文件不存在: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(assets)").fetchall()]
        if "groups" in cols:
            print("[跳过] assets.groups 已存在，无需迁移。")
            return 0
        # groups 在部分 SQL 方言是关键字，建列时加引号保险
        cur.execute('ALTER TABLE assets ADD COLUMN "groups" TEXT')
        conn.commit()
        print('[完成] 已新增 assets.groups (TEXT, JSON 字符串数组)')
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
