# -*- coding: utf-8 -*-
"""幂等迁移脚本：为 assets 表新增 commissioning_date（设备启用日期）列。

背景：项目未使用 alembic，启动时 create_all 只建新表、不会给已存在的表加列，
因此存量库（本地 8002 / 生产 126）需要手动执行本脚本补列。

用法（在 backend 目录下）：
    python add_commissioning_date.py

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
        if "commissioning_date" in cols:
            print("[跳过] assets.commissioning_date 已存在，无需迁移。")
            return 0
        cur.execute("ALTER TABLE assets ADD COLUMN commissioning_date DATETIME")
        conn.commit()
        print("[完成] 已新增 assets.commissioning_date (DATETIME)")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
