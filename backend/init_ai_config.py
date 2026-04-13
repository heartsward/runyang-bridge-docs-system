"""
初始化AI配置数据库表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.deps import get_db
from app.models.ai_config import AIUserConfig
from app.core.config import settings

def init_ai_config_table():
    """创建AI配置表"""
    print("开始创建AI配置表...")
    
     try:
         # 创建表
         db_gen = get_db()
         db = next(db_gen)

         from app.models.ai_config import AIUserConfig
         AIUserConfig.metadata.create_all(db.bind, checkfirst=True)
         db.commit()
         db.close()
         print("[SUCCESS] AI配置表创建成功！")

         # 验证表是否创建
         from sqlalchemy import inspect
         inspector = inspect(db.bind)
         tables = inspector.get_table_names()

         if 'ai_user_configs' in tables:
             print(f"[INFO] 当前数据库表: {tables}")
         else:
             print("[WARNING] ai_user_configs表未找到")

         # 验证表是否创建
         from sqlalchemy import inspect
         inspector = inspect(db.bind)
         tables = inspector.get_table_names()

         if 'ai_user_configs' in tables:
             print(f"[INFO] 当前数据库表: {tables}")
         else:
             print("[WARNING] ai_user_configs表未找到")
            
    except Exception as e:
        print(f"[ERROR] 创建AI配置表失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_ai_config_table()
