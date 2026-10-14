# -*- coding: utf-8 -*-
"""幂等迁移脚本：为 assets 表新增 system_version（系统型号及版本）列。

与 add_commissioning_date.py / add_asset_groups.py 同套路：项目无 alembic，
create_all 不给存量表加列，每台存量库（本地 / 126 生产）部署新代码后需手动执行一次。

用法（在 backend 目录下）：
    python add_system_version.py

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
        if "system_version" in cols:
            print("[跳过] assets.system_version 已存在，无需迁移。")
            return 0
        cur.execute("ALTER TABLE assets ADD COLUMN system_version VARCHAR(255)")
        conn.commit()
        print("[完成] 已新增 assets.system_version (VARCHAR(255))")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
