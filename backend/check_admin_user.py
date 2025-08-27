#!/usr/bin/env python3
"""
检查admin用户权限脚本
验证admin用户是否具有管理员权限
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.crud.user import user as crud_user

def check_admin_user():
    """检查admin用户权限"""
    db = Session(bind=engine)
    
    try:
        # 查找admin用户
        admin_user = crud_user.get_by_username(db, username="admin")
        
        if not admin_user:
            print("❌ admin用户不存在")
            return
        
        print("✓ 找到admin用户")
        print(f"  ID: {admin_user.id}")
        print(f"  用户名: {admin_user.username}")
        print(f"  邮箱: {admin_user.email}")
        print(f"  全名: {admin_user.full_name}")
        print(f"  部门: {admin_user.department}")
        print(f"  职位: {admin_user.position}")
        print(f"  电话: {admin_user.phone}")
        print(f"  是否激活: {admin_user.is_active}")
        print(f"  是否超级用户: {admin_user.is_superuser}")
        print(f"  创建时间: {admin_user.created_at}")
        
        if admin_user.is_superuser:
            print("✅ admin用户具有管理员权限")
        else:
            print("❌ admin用户缺少管理员权限")
            print("正在修复...")
            
            # 修复权限
            admin_user.is_superuser = True
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print("✅ 管理员权限已修复")
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("正在检查admin用户权限...")
    check_admin_user()
    print("检查完成！")