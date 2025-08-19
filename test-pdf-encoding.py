#!/usr/bin/env python3
"""
PDF编码修复测试脚本
"""
import sys
import os

# 添加后端路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.enhanced_pdf_extractor import EnhancedPDFExtractor

def test_pdf_extraction(pdf_path):
    """测试PDF提取功能"""
    print(f"测试PDF文件: {pdf_path}")
    print("=" * 50)
    
    extractor = EnhancedPDFExtractor()
    
    if not extractor.is_pdf_file(pdf_path):
        print("❌ 不是有效的PDF文件")
        return
    
    if not os.path.exists(pdf_path):
        print("❌ 文件不存在")
        return
    
    # 提取内容
    content, error = extractor.extract_pdf_content(pdf_path)
    
    if error:
        print(f"❌ 提取失败: {error}")
        return
    
    if content:
        print("✅ 提取成功!")
        print(f"内容长度: {len(content)} 字符")
        print("前200个字符:")
        print("-" * 30)
        print(content[:200])
        print("-" * 30)
        
        # 检查编码问题
        has_issues = False
        if '�' in content or '\ufffd' in content:
            print("⚠️  发现编码替换字符")
            has_issues = True
        if '???' in content:
            print("⚠️  发现连续问号")
            has_issues = True
            
        if not has_issues:
            print("✅ 没有发现明显的编码问题")
        
    else:
        print("❌ 未提取到内容")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test-pdf-encoding.py <PDF文件路径>")
        print("示例: python test-pdf-encoding.py backend/uploads/test.pdf")
    else:
        pdf_path = sys.argv[1]
        test_pdf_extraction(pdf_path)