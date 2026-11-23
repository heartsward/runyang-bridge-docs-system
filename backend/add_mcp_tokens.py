# -*- coding: utf-8 -*-
"""幂等迁移脚本：32.2 MCP 用户隔离。

做三件事：
1. users 表新增 mcp_token 列（TEXT，可空，唯一）——create_all 不给存量表加列
2. 给所有**现有普通用户**生成随机个人码（已有值的跳过）
3. 初始化 system_configs 的 admin_mcp_token（管理员统一码，已存在则不动）
   （注：代码里 get_or_create_admin_token 也会惰性生成，这里提前生成便于展示）

用法（backend 目录下）：
    python add_mcp_tokens.py

可重复执行。
"""
import json
import os
import secrets
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

        # 1. users.mcp_token 列
        cols = [r[1] for r in cur.execute("PRAGMA table_info(users)").fetchall()]
        if "mcp_token" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN mcp_token TEXT")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_mcp_token ON users (mcp_token)")
            print("[完成] 已新增 users.mcp_token (TEXT, unique)")
        else:
            print("[跳过] users.mcp_token 已存在")

        # 2. 普通用户补个人码
        rows = cur.execute(
            "SELECT id, username, is_superuser, mcp_token FROM users"
        ).fetchall()
        added = 0
        for uid, uname, is_su, tok in rows:
            if is_su:
                # 管理员：按模型约定保持 NULL（用统一码）
                continue
            if tok:
                continue
            new_tok = secrets.token_urlsafe(24)
            cur.execute("UPDATE users SET mcp_token = ? WHERE id = ?", (new_tok, uid))
            added += 1
            print(f"[补码] 用户 {uname}(id={uid}) 已生成 MCP 个人码")
        print(f"[完成] 普通用户补码 {added} 个")

        # 3. 管理员统一码（system_configs 表由 create_all 建；这里直插惰性生成）
        try:
            has_key = cur.execute(
                "SELECT value FROM system_configs WHERE key = 'admin_mcp_token'"
            ).fetchone()
        except sqlite3.OperationalError:
            has_key = None  # 表还不存在——代码惰性生成兜底
        if has_key is None:
            admin_tok = secrets.token_urlsafe(24)
            try:
                cur.execute(
                    "INSERT INTO system_configs (key, value, description) VALUES (?, ?, ?)",
                    ("admin_mcp_token", json.dumps(admin_tok, ensure_ascii=False),
                     "管理员统一 MCP 调用验证码（32.2）"),
                )
                print(f"[完成] 已初始化管理员统一 MCP 码")
            except sqlite3.OperationalError:
                print("[警告] system_configs 表不存在，管理员码将由服务惰性生成")
        else:
            print("[跳过] admin_mcp_token 已存在")

        conn.commit()
        print("\n迁移完成。MCP 客户端配置需加 Authorization: Bearer <对应验证码>。")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
