# -*- coding: utf-8 -*-
"""创建AI配置表"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.deps import get_db
from app.models.ai_config import AIUserConfig

def create_table():
    db_gen = get_db()
    db = next(db_gen)

    print("正在创建AI配置表...")
    try:
        AIUserConfig.metadata.create_all(db.bind, checkfirst=True)
        db.commit()
        db.close()
        print("[OK] AI配置表创建成功")
        return True
    except Exception as e:
        print(f"[ERROR] 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    create_table()
    print("\n重启后端服务: uvicorn app.main:app --reload")