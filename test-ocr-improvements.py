#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR功能改进测试脚本
用于测试中文字符间距和完整性优化效果
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# 添加backend路径到sys.path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.enhanced_content_extractor import EnhancedContentExtractor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ocr_improvement_test.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def analyze_text_quality(text: str, description: str = ""):
    """分析文本质量"""
    if not text:
        return {"total_chars": 0, "quality": "无内容"}
    
    analysis = {
        "description": description,
        "total_chars": len(text),
        "chinese_chars": len([c for c in text if '\u4e00' <= c <= '\u9fff']),
        "english_chars": len([c for c in text if c.isalpha() and ord(c) < 128]),
        "digit_chars": len([c for c in text if c.isdigit()]),
        "spaces": text.count(' '),
        "lines": len(text.split('\n'))
    }
    
    # 检查常见的间距问题
    spacing_issues = []
    
    # 检查中文字符间的多余空格
    import re
    chinese_with_spaces = re.findall(r'[\u4e00-\u9fff]\s+[\u4e00-\u9fff]', text)
    if chinese_with_spaces:
        spacing_issues.append(f"发现{len(chinese_with_spaces)}处中文字符间多余空格")
        # 显示前几个例子
        examples = chinese_with_spaces[:3]
        spacing_issues.append(f"示例: {', '.join(examples)}")
    
    # 检查常见的分离词汇
    common_separated_words = ['网 络', '安 全', '数 据', '系 统', '信 息', '管 理', '技 术']
    found_separated = [word for word in common_separated_words if word in text]
    if found_separated:
        spacing_issues.append(f"发现被分离的常见词汇: {', '.join(found_separated)}")
    
    analysis["spacing_issues"] = spacing_issues
    
    # 质量评级
    if analysis["total_chars"] == 0:
        quality_grade = "F - 无内容"
    elif len(spacing_issues) == 0:
        quality_grade = "A - 优秀"
    elif len(spacing_issues) <= 2:
        quality_grade = "B - 良好" 
    elif len(spacing_issues) <= 5:
        quality_grade = "C - 一般"
    else:
        quality_grade = "D - 需要改进"
    
    analysis["quality_grade"] = quality_grade
    
    return analysis

def test_ocr_improvements(pdf_file_path: str):
    """测试OCR改进效果"""
    print("=" * 60)
    print("OCR功能改进效果测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试文件: {pdf_file_path}")
    print()
    
    if not os.path.exists(pdf_file_path):
        print(f"❌ 错误: 文件不存在 {pdf_file_path}")
        return False
    
    # 创建增强内容提取器
    extractor = EnhancedContentExtractor()
    
    print("🔍 检查OCR环境...")
    print(f"OCR可用: {'✅ 是' if extractor.has_ocr else '❌ 否'}")
    
    if not extractor.has_ocr:
        print("❌ OCR功能不可用，请先运行 install-ocr-dependencies.bat")
        return False
    
    print()
    print("🚀 开始OCR处理测试...")
    print("-" * 40)
    
    # 记录开始时间
    start_time = time.time()
    
    # 提取内容
    try:
        content, error = extractor.extract_content(pdf_file_path)
        processing_time = time.time() - start_time
        
        print(f"⏱️ 处理时间: {processing_time:.2f}秒")
        print()
        
        if error:
            print(f"❌ 提取错误: {error}")
            return False
        
        if not content:
            print("❌ 未提取到任何内容")
            return False
        
        # 分析提取结果
        print("📊 内容分析结果:")
        print("-" * 40)
        
        analysis = analyze_text_quality(content, "OCR优化后")
        
        print(f"总字符数: {analysis['total_chars']:,}个")
        print(f"中文字符: {analysis['chinese_chars']:,}个 ({analysis['chinese_chars']/analysis['total_chars']*100:.1f}%)")
        print(f"英文字符: {analysis['english_chars']:,}个 ({analysis['english_chars']/analysis['total_chars']*100:.1f}%)")
        print(f"数字字符: {analysis['digit_chars']:,}个 ({analysis['digit_chars']/analysis['total_chars']*100:.1f}%)")
        print(f"空格数量: {analysis['spaces']:,}个")
        print(f"行数: {analysis['lines']:,}行")
        print(f"质量评级: {analysis['quality_grade']}")
        
        print()
        print("🔍 字符间距问题检查:")
        print("-" * 40)
        
        if analysis['spacing_issues']:
            for issue in analysis['spacing_issues']:
                print(f"⚠️ {issue}")
        else:
            print("✅ 未发现明显的字符间距问题")
        
        print()
        print("📄 内容预览 (前500字符):")
        print("-" * 40)
        preview = content[:500] + "..." if len(content) > 500 else content
        print(preview)
        
        print()
        print("📋 改进效果总结:")
        print("-" * 40)
        
        improvements = []
        
        # 基于分析结果评估改进效果
        if not analysis['spacing_issues']:
            improvements.append("✅ 中文字符间距处理正常")
        else:
            improvements.append(f"⚠️ 仍有{len(analysis['spacing_issues'])}个间距问题待优化")
        
        if analysis['chinese_chars'] > 0:
            improvements.append(f"✅ 中文识别率: {analysis['chinese_chars']/analysis['total_chars']*100:.1f}%")
        
        if analysis['total_chars'] >= 1000:
            improvements.append("✅ 内容提取完整性良好")
        elif analysis['total_chars'] >= 500:
            improvements.append("⚠️ 内容可能不够完整")
        else:
            improvements.append("❌ 内容提取不完整")
        
        for improvement in improvements:
            print(improvement)
        
        # 保存详细结果
        result_file = f"ocr_test_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"OCR改进测试结果\n")
            f.write(f"测试时间: {datetime.now()}\n")
            f.write(f"测试文件: {pdf_file_path}\n")
            f.write(f"处理时间: {processing_time:.2f}秒\n\n")
            f.write("分析结果:\n")
            for key, value in analysis.items():
                if key != 'spacing_issues':
                    f.write(f"{key}: {value}\n")
            f.write("\n间距问题:\n")
            for issue in analysis['spacing_issues']:
                f.write(f"{issue}\n")
            f.write(f"\n完整内容:\n{content}")
        
        print()
        print(f"📁 详细结果已保存到: {result_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {str(e)}")
        logger.exception("OCR测试异常")
        return False

def main():
    """主函数"""
    print("OCR功能改进测试工具")
    print("用于验证中文字符间距和完整性优化效果")
    print()
    
    # 获取PDF文件路径
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        pdf_file = input("请输入PDF文件路径: ").strip()
        if not pdf_file:
            print("未提供文件路径，退出测试")
            return
    
    # 执行测试
    success = test_ocr_improvements(pdf_file)
    
    print()
    if success:
        print("✅ OCR改进测试完成")
    else:
        print("❌ OCR改进测试失败")
    
    print()
    input("按任意键退出...")

if __name__ == "__main__":
    main()