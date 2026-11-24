# -*- coding: utf-8 -*-
"""32.6 修复：assets.serial_number 空串撞 UNIQUE 约束

背景：serial_number 列带 UNIQUE 约束（防真实序列号重复）。SQLite 中多个 NULL
可共存、多个空串('')只允许一个。此前该列界面不暴露、恒为 NULL 相安无事；
32.5 把扩展字段补进表单后，"未填"以前端空串落库，第二条空 serial 即触发
IntegrityError（陈工实测 PUT /assets/87 报 500）。

本迁移：把所有 serial_number='' 归一为 NULL（幂等）。只清 serial_number
（唯一约束列），其它列空串无害不动，避免多余变更。

用法（项目 backend/ 目录）：
    venv/Scripts/python.exe fix_empty_serial.py
"""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).parent / "yunwei_docs.db"


def main() -> int:
    if not DB.exists():
        print(f"[错误] 数据库不存在: {DB}")
        return 1
    conn = sqlite3.connect(DB)
    try:
        before = conn.execute(
            "SELECT COUNT(*) FROM assets WHERE serial_number = ''").fetchone()[0]
        # 防御：如果存在多个不同非空重复 serial（理论不可能，UNIQUE 拦着），先报告
        dup = conn.execute(
            "SELECT serial_number, COUNT(*) FROM assets "
            "WHERE serial_number IS NOT NULL AND serial_number <> '' "
            "GROUP BY serial_number HAVING COUNT(*) > 1").fetchall()
        if dup:
            print(f"[警告] 存在重复非空序列号（UNIQUE 异常状态？）: {dup}")

        cur = conn.execute(
            "UPDATE assets SET serial_number = NULL WHERE serial_number = ''")
        conn.commit()
        after = conn.execute(
            "SELECT COUNT(*) FROM assets WHERE serial_number = ''").fetchone()[0]
        print(f"[OK] serial_number 空串归一: {before} 行 -> 剩余 {after} 行（改动 {cur.rowcount}）")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
