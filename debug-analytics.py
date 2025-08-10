#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试分析API的数据库连接问题
"""
import sys
import os

# Windows控制台编码问题修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from app.db.database import SessionLocal
    from app.models.document import Document
    print("✅ 成功导入数据库模块")
    
    # 测试数据库连接
    db = SessionLocal()
    print("✅ 数据库会话创建成功")
    
    # 测试查询
    count = db.query(Document).count()
    print(f"📊 数据库中的文档数量: {count}")
    
    # 列出表结构
    from app.db.database import engine
    from sqlalchemy import inspect
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📋 数据库表: {tables}")
    
    db.close()
    print("✅ 数据库连接测试完成")
    
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
    import traceback
    traceback.print_exc()