#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试OCR处理过程
"""
import sys
import os
import logging
from pathlib import Path

# 设置详细日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加后端路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_extractor_initialization():
    """测试提取器初始化"""
    print("=" * 60)
    print("测试提取器初始化")
    print("=" * 60)
    
    from app.services.enhanced_content_extractor import EnhancedContentExtractor
    
    extractor = EnhancedContentExtractor()
    print(f"OCR available: {extractor.has_ocr}")
    
    # 检查tesseract路径设置
    import pytesseract
    print(f"Current tesseract_cmd: {pytesseract.pytesseract.tesseract_cmd}")
    
    return extractor

def test_garbled_detection(extractor):
    """测试乱码检测"""
    print("\n" + "=" * 60)
    print("测试乱码检测")
    print("=" * 60)
    
    test_texts = [
        {
            "name": "正常中文",
            "text": "这是正常的中文文档内容，包含完整的句子和词汇。",
            "expected": False
        },
        {
            "name": "实际乱码",
            "text": "[第1页] 8LA5 AP CE RMLAN5 CE 5RE R1 (2025) 2 5 FEF HAA 1P",
            "expected": True
        }
    ]
    
    for test in test_texts:
        result = extractor._is_garbled_text(test["text"])
        status = "PASS" if result == test["expected"] else "FAIL"
        print(f"{test['name']}: {status} (detected: {result}, expected: {test['expected']})")

def test_ocr_direct():
    """直接测试OCR功能"""
    print("\n" + "=" * 60)
    print("直接测试OCR功能")
    print("=" * 60)
    
    import pytesseract
    from PIL import Image, ImageDraw
    
    # 确保使用正确路径
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # 创建测试图像（模拟PDF页面）
    test_img = Image.new('RGB', (400, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(test_img)
    
    # 添加英文和数字（模拟乱码情况）
    draw.text((20, 50), "8LA5 AP CE RMLAN5 CE 5RE R1", fill=(0, 0, 0))
    draw.text((20, 100), "Hello World 2025", fill=(0, 0, 0))
    
    # 使用与系统相同的OCR配置
    try:
        result = pytesseract.image_to_string(
            test_img,
            lang='chi_sim+eng',
            config='--psm 3 --oem 3'
        )
        print(f"OCR Result: '{result.strip()}'")
        return True
    except Exception as e:
        print(f"OCR Error: {e}")
        return False

def test_pdf_processing_simulation():
    """模拟PDF处理过程"""
    print("\n" + "=" * 60)
    print("模拟PDF处理过程")
    print("=" * 60)
    
    # 模拟从PDF提取的乱码文本
    simulated_pdf_text = "[第1页] 8LA5 AP CE RMLAN5 CE 5RE R1 (2025) 2 5 FEF HAA 1P 2025"
    
    from app.services.enhanced_content_extractor import EnhancedContentExtractor
    extractor = EnhancedContentExtractor()
    
    print(f"Original extracted text: '{simulated_pdf_text}'")
    
    # 测试乱码检测
    is_garbled = extractor._is_garbled_text(simulated_pdf_text)
    print(f"Garbled detection: {is_garbled}")
    
    if is_garbled and extractor.has_ocr:
        print("Would trigger OCR processing...")
        
        # 模拟OCR处理（如果有实际PDF文件）
        print("OCR processing would be called here")
        return True
    else:
        if not is_garbled:
            print("Text not detected as garbled - OCR would NOT be triggered")
        if not extractor.has_ocr:
            print("OCR not available - OCR would NOT be triggered")
        return False

def main():
    """主函数"""
    print("OCR处理流程测试")
    
    # 测试1: 初始化
    extractor = test_extractor_initialization()
    
    # 测试2: 乱码检测
    test_garbled_detection(extractor)
    
    # 测试3: 直接OCR
    ocr_works = test_ocr_direct()
    
    # 测试4: 模拟处理流程
    would_trigger_ocr = test_pdf_processing_simulation()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"OCR初始化: {'PASS' if extractor.has_ocr else 'FAIL'}")
    print(f"OCR功能: {'PASS' if ocr_works else 'FAIL'}")
    print(f"乱码检测和OCR触发: {'PASS' if would_trigger_ocr else 'FAIL'}")
    
    if extractor.has_ocr and ocr_works and would_trigger_ocr:
        print("\n结论: OCR功能应该正常工作")
        print("如果生产环境仍然出现乱码，可能的原因:")
        print("1. PDF文件本身的图像质量问题")
        print("2. OCR配置参数需要调优")
        print("3. 日志中可能有具体的错误信息")
    else:
        print("\n结论: OCR功能存在问题，需要修复")

if __name__ == "__main__":
    main()