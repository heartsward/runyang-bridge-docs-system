#!/usr/bin/env python3
"""
admin用户权限修复脚本
直接修复数据库中admin用户的管理员权限
"""
import sqlite3
import os
import sys

def fix_admin_permission():
    """修复admin用户的管理员权限"""
    db_path = 'yunwei_docs.db'
    
    print("=== admin用户权限修复工具 ===\n")
    
    # 检查数据库文件
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在:", os.path.abspath(db_path))
        print("请先运行后端服务创建数据库")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查admin用户是否存在
        print("=== 1. 检查admin用户 ===")
        cursor.execute("SELECT username, is_superuser FROM users WHERE username='admin';")
        admin_info = cursor.fetchone()
        
        if not admin_info:
            print("❌ admin用户不存在，无法修复")
            print("建议重启后端服务以创建admin用户")
            return False
            
        username, current_superuser = admin_info
        print(f"✅ 找到用户: {username}")
        print(f"当前权限: {'管理员' if current_superuser else '普通用户'}")
        
        # 2. 检查是否需要修复
        if current_superuser:
            print("✅ admin用户已经具有管理员权限，无需修复")
            return True
            
        # 3. 执行权限修复
        print("\n=== 2. 执行权限修复 ===")
        print("正在将admin用户设置为管理员...")
        
        cursor.execute("UPDATE users SET is_superuser = ? WHERE username = ?", (True, 'admin'))
        
        # 检查是否有行被更新
        if cursor.rowcount == 0:
            print("❌ 更新失败：没有行被修改")
            return False
            
        # 提交事务
        conn.commit()
        print(f"✅ 成功更新 {cursor.rowcount} 行数据")
        
        # 4. 验证修复结果
        print("\n=== 3. 验证修复结果 ===")
        cursor.execute("SELECT username, email, is_superuser FROM users WHERE username='admin';")
        result = cursor.fetchone()
        
        if result:
            username, email, is_superuser = result
            print(f"用户名: {username}")
            print(f"邮箱: {email}")
            print(f"权限: {'✅ 管理员' if is_superuser else '❌ 普通用户'}")
            
            if is_superuser:
                print("\n🎉 修复成功！admin用户现在具有管理员权限")
                print("请重新登录测试权限是否正常显示")
                return True
            else:
                print("\n❌ 修复失败：权限仍然不正确")
                return False
        else:
            print("❌ 验证失败：无法获取admin用户信息")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def add_superuser_field():
    """如果is_superuser字段不存在，添加该字段"""
    db_path = 'yunwei_docs.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否存在
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        has_superuser = any(col[1] == 'is_superuser' for col in columns)
        
        if not has_superuser:
            print("=== 添加is_superuser字段 ===")
            print("检测到缺少is_superuser字段，正在添加...")
            
            # 添加字段
            cursor.execute("ALTER TABLE users ADD COLUMN is_superuser BOOLEAN DEFAULT FALSE;")
            conn.commit()
            
            print("✅ is_superuser字段添加成功")
            return True
        else:
            print("✅ is_superuser字段已存在")
            return True
            
    except sqlite3.Error as e:
        print(f"❌ 添加字段失败: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    try:
        print("开始admin权限修复流程...\n")
        
        # 1. 确保is_superuser字段存在
        if not add_superuser_field():
            print("❌ 无法添加必要字段，修复失败")
            sys.exit(1)
        
        # 2. 修复admin权限
        success = fix_admin_permission()
        
        print(f"\n{'='*50}")
        if success:
            print("✅ 修复完成！请重新登录测试")
            print("如果前端仍显示普通用户，请检查前端权限逻辑")
        else:
            print("❌ 修复失败，请检查错误信息")
            print("建议运行诊断脚本: python diagnose_database.py")
        print(f"{'='*50}")
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n修复脚本执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()