#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动修复华为交换机配置文件的编码问题
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.encoding_detector import EncodingDetector

def main():
    # 华为交换机配置文件路径
    file_path = r"C:\Users\cccly\yunweiruanjian\backend\uploads\25f155f0-cba8-4dab-9070-e950f49df1b7.txt"
    
    print("=" * 60)
    print("华为交换机配置文件编码修复测试")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"错误：文件不存在 - {file_path}")
        return
    
    # 1. 检测当前编码
    print("1. 检测文件编码...")
    encoding, confidence = EncodingDetector.detect_encoding(file_path)
    print(f"   检测结果: {encoding} (置信度: {confidence:.2f})")
    
    # 2. 读取文件内容
    print("\n2. 读取文件内容...")
    content, error = EncodingDetector.read_file_with_encoding(file_path, encoding)
    
    if content:
        print(f"   成功读取，内容长度: {len(content)} 字符")
        print("\n3. 内容预览 (前500字符):")
        print("-" * 50)
        print(content[:500])
        if len(content) > 500:
            print("...")
        print("-" * 50)
        
        # 4. 保存修复后的文件（UTF-8编码）
        output_file = file_path.replace('.txt', '_fixed_utf8.txt')
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"\n4. UTF-8版本已保存到: {output_file}")
            
            # 验证保存的文件
            with open(output_file, 'r', encoding='utf-8') as f:
                verified_content = f.read()
            
            if verified_content == content:
                print("   验证成功：UTF-8文件内容一致")
            else:
                print("   警告：UTF-8文件内容不匹配")
                
        except Exception as e:
            print(f"   保存失败: {str(e)}")
    
    else:
        print(f"   读取失败: {error}")
    
    print("\n" + "=" * 60)
    print("修复完成")
    print("=" * 60)

if __name__ == "__main__":
    main()