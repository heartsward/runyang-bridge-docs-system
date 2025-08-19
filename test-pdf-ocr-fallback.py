#!/usr/bin/env python3
"""
测试PDF OCR回退机制
"""
import sys
import os
import logging

# 设置详细日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 添加后端路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.enhanced_content_extractor import EnhancedContentExtractor

def test_pdf_processing(pdf_path):
    """测试PDF处理完整流程"""
    print("=" * 80)
    print(f"测试PDF文件: {pdf_path}")
    print("=" * 80)
    
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    # 创建增强内容提取器
    extractor = EnhancedContentExtractor()
    
    print(f"\n📊 系统状态:")
    print(f"   OCR功能: {'✅ 可用' if extractor.has_ocr else '❌ 不可用'}")
    
    print(f"\n🔍 开始处理文档...")
    
    # 提取内容
    content, error = extractor.extract_content(pdf_path)
    
    print(f"\n📋 处理结果:")
    if error:
        print(f"   错误: {error}")
    
    if content:
        content_length = len(content)
        print(f"   内容长度: {content_length} 字符")
        
        # 显示前500字符
        print(f"\n📄 内容预览 (前500字符):")
        print("-" * 50)
        print(content[:500])
        if content_length > 500:
            print("...")
        print("-" * 50)
        
        # 检查是否是乱码
        is_garbled = extractor._is_garbled_text(content)
        print(f"\n🔍 乱码检测结果: {'❌ 检测到乱码' if is_garbled else '✅ 正常文本'}")
        
        # 如果检测到乱码，说明OCR回退可能没有生效
        if is_garbled:
            print("⚠️  警告: 检测到乱码，OCR回退机制可能没有正常工作")
            print("💡 建议检查:")
            print("   - Tesseract OCR是否正确安装")
            print("   - OCR触发逻辑是否正确")
            print("   - 日志中是否有OCR处理信息")
        else:
            print("✅ 文本正常，处理成功")
    else:
        print("   ❌ 未提取到内容")
    
    # 显示性能统计
    stats = extractor.get_performance_stats()
    print(f"\n📈 性能统计:")
    print(f"   总提取次数: {stats['total_extractions']}")
    print(f"   成功次数: {stats['successful_extractions']}")
    print(f"   失败次数: {stats['failed_extractions']}")
    print(f"   平均处理时间: {stats['average_processing_time']:.2f}秒")
    
    # 显示回退状态
    fallback_status = extractor.get_fallback_status()
    print(f"\n🔄 智能回退状态:")
    print(f"   简单模式: {'已启用' if fallback_status['config']['use_simple_mode'] else '未启用'}")
    print(f"   连续失败次数: {fallback_status['config']['consecutive_failures']}")

def main():
    if len(sys.argv) < 2:
        print("用法: python test-pdf-ocr-fallback.py <PDF文件路径>")
        print("\n示例:")
        print("  python test-pdf-ocr-fallback.py backend/uploads/test.pdf")
        print("  python test-pdf-ocr-fallback.py \"C:/path/to/your/file.pdf\"")
        return
    
    pdf_path = sys.argv[1]
    test_pdf_processing(pdf_path)

if __name__ == "__main__":
    main()