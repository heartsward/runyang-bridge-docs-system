@echo off
chcp 65001 >nul
echo ==========================================
echo    直接修复脚本（仅核心文件）
echo ==========================================
echo.

echo 本脚本直接应用关键修复，无需下载完整代码
echo.

echo 1. 备份当前文件...
if exist "backend\app\services\enhanced_content_extractor.py" (
    copy "backend\app\services\enhanced_content_extractor.py" "enhanced_content_extractor.py.backup"
    echo ✓ 核心文件已备份
)

echo.
echo 2. 停止服务...
call stop-services.bat >nul 2>&1

echo.
echo 3. 应用核心修复...

echo 创建datetime修复脚本...
(
echo import os
echo import re
echo from pathlib import Path
echo.
echo def fix_datetime_in_file^(file_path^):
echo     if not file_path.exists^(^):
echo         return False
echo     content = file_path.read_text^(encoding='utf-8'^)
echo     if 'datetime.utcnow^(^)' not in content:
echo         return True
echo     if 'from datetime import datetime, timedelta' in content and 'timezone' not in content:
echo         content = content.replace^(
echo             'from datetime import datetime, timedelta',
echo             'from datetime import datetime, timedelta, timezone'
echo         ^)
echo     old_count = content.count^('datetime.utcnow^(^)'^)
echo     content = content.replace^('datetime.utcnow^(^)', 'datetime.now^(timezone.utc^)'^)
echo     file_path.write_text^(content, encoding='utf-8'^)
echo     print^(f'Fixed {old_count} datetime calls in {file_path.name}'^)
echo     return True
echo.
echo files_to_fix = ['database_integrated_server.py']
echo for file_name in files_to_fix:
echo     file_path = Path^(file_name^)
echo     fix_datetime_in_file^(file_path^)
echo print^('DateTime fix completed'^)
) > backend\fix_datetime_simple.py

cd backend
python fix_datetime_simple.py
cd ..

echo ✓ DateTime修复完成

echo.
echo 4. 应用乱码检测修复...
echo 正在修改enhanced_content_extractor.py...

python -c "
import re

# 读取文件
try:
    with open('backend/app/services/enhanced_content_extractor.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 应用修复
    # 1. 降低阈值
    content = re.sub(
        r'is_garbled = garbled_ratio >= 0\.4.*# 40%以上指标异常认为是乱码',
        'is_garbled = garbled_ratio >= 0.3  # 30%以上指标异常认为是乱码（降低阈值）',
        content
    )
    
    # 2. 添加快速检测（如果不存在）
    if '快速检测：明显的乱码模式' not in content:
        # 在适当位置插入快速检测代码
        insert_pos = content.find('# 检测乱码特征')
        if insert_pos > 0:
            quick_detect = '''        # 快速检测：明显的乱码模式
        obvious_garbled_patterns = [
            r'[A-Z0-9]{2,}\s+[A-Z0-9]{2,}\s+[A-Z0-9]{2,}',  # 连续的大写字母数字组合
            r'\b[A-Z]{1,3}[0-9]{1,3}[A-Z]{1,3}\b',           # 字母数字字母模式
            r'\b[0-9][A-Z]{2,}[0-9]\b',                      # 数字字母数字模式
        ]
        
        for pattern in obvious_garbled_patterns:
            if re.search(pattern, clean_text):
                logger.debug(f'快速检测到明显乱码模式: {pattern}')
                return True
        
        '''
            content = content[:insert_pos] + quick_detect + content[insert_pos:]
    
    # 写回文件
    with open('backend/app/services/enhanced_content_extractor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('Garbled detection fix applied successfully')
    
except Exception as e:
    print(f'Error applying fix: {e}')
"

echo ✓ 乱码检测修复完成

echo.
echo 5. 重启服务...
if exist start-production.bat (
    start /min start-production.bat
    echo ✓ 生产服务已启动
) else (
    start /min start-services.bat  
    echo ✓ 开发服务已启动
)

echo.
echo ==========================================
echo 直接修复完成！
echo ==========================================
echo.
echo 关键修复内容：
echo - DateTime弃用警告修复
echo - 乱码检测阈值优化（40% → 30%）
echo - 快速乱码模式检测
echo.
echo 请测试PDF文档上传验证修复效果
echo 备份文件：enhanced_content_extractor.py.backup
echo.
pause