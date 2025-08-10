#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门搜索2025年的目标文档
"""
import os
import sys
import glob

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from app.services.advanced_pdf_extractor import AdvancedPDFExtractor

def search_2025_document():
    """专门搜索2025年的文档"""
    
    upload_dir = "uploads"
    pdf_files = glob.glob(os.path.join(upload_dir, "*.pdf"))
    print(f"总共 {len(pdf_files)} 个PDF文件")
    
    extractor = AdvancedPDFExtractor()
    
    # 更精确的关键词匹配
    target_2025_keywords = ["2025", "镇等保办"]  # 最关键的2025年标识词
    general_keywords = ["网络", "数据安全", "监督检查"]
    
    found_2025_docs = []
    
    # 搜索所有PDF文件
    for i, pdf_file in enumerate(pdf_files):
        filename = os.path.basename(pdf_file)
        print(f"\n[{i+1}/{len(pdf_files)}] {filename[:20]}...")
        
        try:
            # 快速分析
            analysis = extractor._analyze_pdf_document(pdf_file)
            
            # 只处理有文本内容的文档
            if analysis.get('text_extraction_rate', 0) > 0.05:
                content, error = extractor._fast_text_extraction(pdf_file)
                
                if content:
                    # 检查是否包含2025关键词
                    has_2025 = any(kw in content for kw in target_2025_keywords)
                    has_general = any(kw in content for kw in general_keywords)
                    
                    if has_2025 and has_general:
                        print(f"  *** 找到2025年目标文档! ***")
                        found_keywords = [kw for kw in target_2025_keywords + general_keywords if kw in content]
                        print(f"  关键词: {found_keywords}")
                        
                        # 显示文档开头
                        lines = content.split('\n')[:15]
                        print("  文档开头:")
                        for j, line in enumerate(lines, 1):
                            if line.strip() and len(line.strip()) > 5:
                                print(f"    {j:2d}: {line.strip()[:90]}")
                                if j >= 10:  # 只显示前10行有效内容
                                    break
                        
                        found_2025_docs.append((pdf_file, found_keywords, content[:500]))
                        
                        # 如果找到"镇等保办"这个特征词，很可能就是目标文档
                        if "镇等保办" in content:
                            print(f"\n  >>> 高度匹配! 包含'镇等保办' <<<")
                            print(f"  文档路径: {pdf_file}")
                            return pdf_file
                            
                    elif has_2025:
                        print(f"  包含2025，但缺少其他关键词")
                        preview = content[:150].replace('\n', ' ')
                        print(f"  内容: {preview}...")
                        
                    elif has_general:
                        print(f"  包含安全相关词汇，但非2025年文档")
                        
                else:
                    print(f"  提取失败: {error[:50]}...")
            else:
                print(f"  跳过(图像文档或无文本)")
                
        except Exception as e:
            print(f"  处理异常: {str(e)[:50]}...")
    
    # 汇总结果
    print(f"\n=== 搜索结果汇总 ===")
    if found_2025_docs:
        print(f"找到 {len(found_2025_docs)} 个2025年相关文档:")
        for i, (filepath, keywords, preview) in enumerate(found_2025_docs, 1):
            filename = os.path.basename(filepath)
            print(f"{i}. {filename}")
            print(f"   关键词: {keywords}")
            print(f"   预览: {preview[:100].replace(chr(10), ' ')}...")
            print()
    else:
        print("未找到2025年目标文档")
        
        # 列出找到的其他相关文档
        print("\n其他可能相关的文档:")
        general_docs = []
        
        for pdf_file in pdf_files[:10]:  # 重新检查前10个
            try:
                analysis = extractor._analyze_pdf_document(pdf_file)
                if analysis.get('text_extraction_rate', 0) > 0.1:
                    content, _ = extractor._fast_text_extraction(pdf_file)
                    if content and any(kw in content for kw in general_keywords):
                        general_docs.append(pdf_file)
            except:
                continue
                        
        for doc in general_docs[:3]:
            print(f"  - {os.path.basename(doc)}")

if __name__ == "__main__":
    search_2025_document()