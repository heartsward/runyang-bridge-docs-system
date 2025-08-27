#!/usr/bin/env python3
"""
初始化默认用户脚本
创建系统默认的管理员用户：admin/admin123
"""
from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.user import User
from app.core.security import get_password_hash
from app.crud.user import user as crud_user
from app.schemas.user import UserCreate

def init_default_users():
    """初始化默认用户"""
    db = Session(bind=engine)
    
    try:
        # 检查admin用户是否已存在
        existing_admin = crud_user.get_by_username(db, username="admin")
        if existing_admin:
            print("✓ 管理员用户已存在")
            return
        
        # 创建默认管理员用户
        admin_user = UserCreate(
            username="admin",
            email="admin@system.com",
            password="admin123",
            full_name="系统管理员",
            department="技术部",
            position="系统管理员",
            phone="13800138000",
            is_active=True
        )
        
        # 创建用户
        created_user = crud_user.create(db, obj_in=admin_user)
        
        # 设置为超级用户
        created_user.is_superuser = True
        db.add(created_user)
        db.commit()
        
        print(f"✓ 默认管理员用户创建成功")
        print(f"  用户名: admin")
        print(f"  密码: admin123")
        print(f"  邮箱: admin@system.com")
        
    except Exception as e:
        print(f"✗ 用户创建失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("正在初始化默认用户...")
    init_default_users()
    print("初始化完成！")