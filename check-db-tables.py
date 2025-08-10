#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""
import sys
import sqlite3
import os

# Windows控制台编码问题修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 检查数据库文件
db_files = [
    'backend/yunwei_docs.db',
    'backend/yunwei_docs_clean.db'
]

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n📁 数据库文件: {db_file}")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if tables:
                print(f"  📋 表数量: {len(tables)}")
                for table in tables:
                    table_name = table[0]
                    print(f"    - {table_name}")
                    
                    # 获取表中记录数
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        print(f"      记录数: {count}")
                    except Exception as e:
                        print(f"      错误: {e}")
            else:
                print("  ❌ 没有找到任何表")
                
            conn.close()
            
        except Exception as e:
            print(f"  ❌ 连接失败: {e}")
    else:
        print(f"\n❌ 文件不存在: {db_file}")

print("\n✅ 数据库检查完成")