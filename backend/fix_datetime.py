#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复datetime.utcnow()弃用警告的脚本
"""
import os
import re
from pathlib import Path

def fix_datetime_in_file(file_path):
    """修复单个文件中的datetime问题"""
    try:
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return False
            
        content = file_path.read_text(encoding='utf-8')
        
        # 检查是否需要修复
        if 'datetime.utcnow()' not in content:
            print(f"File {file_path.name} already fixed")
            return True
        
        print(f"Fixing {file_path.name}...")
        
        # 添加timezone导入
        if 'from datetime import datetime, timedelta' in content and 'timezone' not in content:
            content = content.replace(
                'from datetime import datetime, timedelta',
                'from datetime import datetime, timedelta, timezone'
            )
            print("  - Added timezone import")
        
        # 替换所有datetime.utcnow()调用
        old_count = content.count('datetime.utcnow()')
        content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
        
        # 写回文件
        file_path.write_text(content, encoding='utf-8')
        print(f"  - Replaced {old_count} datetime.utcnow() calls")
        print(f"File {file_path.name} fixed successfully")
        return True
        
    except Exception as e:
        print(f"Failed to fix {file_path.name}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 50)
    print("Fixing datetime.utcnow() deprecation warnings")
    print("=" * 50)
    
    # 需要修复的文件列表
    files_to_fix = [
        'database_integrated_server.py',
    ]
    
    success_count = 0
    total_count = 0
    
    for file_name in files_to_fix:
        file_path = Path(file_name)
        total_count += 1
        
        if fix_datetime_in_file(file_path):
            success_count += 1
    
    print("\n" + "=" * 50)
    print(f"Fix completed: {success_count}/{total_count} files successful")
    
    if success_count == total_count:
        print("All datetime issues fixed successfully")
    else:
        print("Some files failed to fix, please check manually")
    
    print("=" * 50)

if __name__ == "__main__":
    main()