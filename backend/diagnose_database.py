#!/usr/bin/env python3
"""
数据库诊断脚本
检查admin用户权限问题的根本原因
"""
import sqlite3
import os
import sys

def diagnose_database():
    """诊断数据库和admin用户权限问题"""
    db_path = 'yunwei_docs.db'
    
    print("=== 润扬大桥系统数据库诊断工具 ===\n")
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在:", os.path.abspath(db_path))
        print("请先启动后端服务以创建数据库")
        return False
    
    print(f"✅ 数据库文件存在: {os.path.abspath(db_path)}")
    print(f"数据库大小: {os.path.getsize(db_path)} 字节\n")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. 检查users表是否存在
        print("=== 1. 检查数据库表结构 ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ users表不存在")
            return False
            
        print("✅ users表存在")
        
        # 2. 检查表结构
        print("\n=== 2. users表结构分析 ===")
        cursor.execute("PRAGMA table_info(users);")
        columns = cursor.fetchall()
        
        print("表字段:")
        has_superuser_field = False
        for col in columns:
            col_id, name, col_type, not_null, default_val, primary_key = col
            is_key = " (主键)" if primary_key else ""
            default_info = f" 默认值: {default_val}" if default_val is not None else ""
            print(f"  [{col_id}] {name} ({col_type}){is_key}{default_info}")
            
            if name == 'is_superuser':
                has_superuser_field = True
        
        if not has_superuser_field:
            print("\n❌ 关键问题: is_superuser字段不存在!")
            print("这可能是admin权限问题的根本原因")
        else:
            print("\n✅ is_superuser字段存在")
        
        # 3. 检查用户数据
        print("\n=== 3. 用户数据分析 ===")
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"用户总数: {user_count}")
        
        if user_count == 0:
            print("❌ 数据库中没有任何用户")
            return False
        
        # 4. 检查admin用户
        print("\n=== 4. admin用户详细信息 ===")
        cursor.execute("SELECT * FROM users WHERE username='admin';")
        admin_data = cursor.fetchone()
        
        if not admin_data:
            print("❌ admin用户不存在")
            print("建议重启后端服务以创建默认admin用户")
            return False
            
        print("✅ admin用户存在")
        
        # 根据表结构显示用户信息
        column_names = [col[1] for col in columns]
        print("admin用户详细信息:")
        for i, value in enumerate(admin_data):
            if i < len(column_names):
                col_name = column_names[i]
                if col_name == 'is_superuser':
                    status = "✅ 管理员" if value else "❌ 普通用户"
                    print(f"  {col_name}: {value} ({status})")
                elif col_name == 'hashed_password':
                    print(f"  {col_name}: {'*' * 20} (已加密)")
                elif col_name in ['created_at', 'updated_at']:
                    print(f"  {col_name}: {value}")
                else:
                    print(f"  {col_name}: {value}")
        
        # 5. 权限问题诊断
        print("\n=== 5. 权限问题诊断结果 ===")
        if has_superuser_field:
            superuser_value = None
            for i, col_name in enumerate(column_names):
                if col_name == 'is_superuser':
                    superuser_value = admin_data[i]
                    break
            
            if superuser_value:
                print("✅ admin用户具有管理员权限")
                print("如果前端显示为普通用户，问题可能在前端权限检查逻辑")
            else:
                print("❌ 关键问题: admin用户缺少管理员权限!")
                print("is_superuser字段值为False或0")
                print("建议运行修复脚本: python fix_admin_permission.py")
        else:
            print("❌ 严重问题: 数据库表缺少is_superuser字段")
            print("需要手动添加字段或重建数据库")
        
        # 6. 所有用户权限概览
        if has_superuser_field:
            print("\n=== 6. 所有用户权限概览 ===")
            cursor.execute("SELECT username, email, is_superuser FROM users;")
            all_users = cursor.fetchall()
            for user in all_users:
                username, email, is_super = user
                role = "管理员" if is_super else "普通用户"
                print(f"  {username} ({email}) - {role}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """主函数"""
    try:
        success = diagnose_database()
        
        print(f"\n{'='*50}")
        if success:
            print("✅ 诊断完成! 请查看上述结果解决权限问题")
        else:
            print("❌ 诊断发现严重问题，请根据提示进行修复")
        print(f"{'='*50}")
        
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n诊断脚本执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()