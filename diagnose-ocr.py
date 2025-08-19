#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR功能诊断脚本
"""
import sys
import os
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_ocr_dependencies():
    """测试OCR依赖"""
    print("=" * 60)
    print("OCR依赖测试")
    print("=" * 60)
    
    # 测试Python包
    try:
        import pytesseract
        print("✓ pytesseract: Available")
    except ImportError:
        print("✗ pytesseract: NOT AVAILABLE")
        return False
    
    try:
        from PIL import Image
        print("✓ Pillow: Available")
    except ImportError:
        print("✗ Pillow: NOT AVAILABLE")
        return False
    
    try:
        import pdf2image
        print("✓ pdf2image: Available")
    except ImportError:
        print("✗ pdf2image: NOT AVAILABLE")
        return False
        
    try:
        import fitz
        print("✓ PyMuPDF: Available")
    except ImportError:
        print("✗ PyMuPDF: NOT AVAILABLE")
        return False
    
    return True

def test_tesseract_executable():
    """测试Tesseract可执行程序"""
    print("\n" + "=" * 60)
    print("Tesseract可执行程序测试")
    print("=" * 60)
    
    import pytesseract
    from PIL import Image
    
    # 测试常见路径
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        "tesseract"
    ]
    
    working_path = None
    for path in possible_paths:
        try:
            if path != "tesseract":
                if not os.path.exists(path):
                    print(f"✗ {path}: File not found")
                    continue
            
            pytesseract.pytesseract.tesseract_cmd = path
            test_img = Image.new('RGB', (100, 30), color=(255, 255, 255))
            result = pytesseract.image_to_string(test_img, config='--psm 8')
            print(f"✓ {path}: Working")
            working_path = path
            break
        except Exception as e:
            print(f"✗ {path}: Error - {e}")
    
    return working_path

def test_tesseract_languages():
    """测试Tesseract语言支持"""
    print("\n" + "=" * 60)
    print("Tesseract语言支持测试")
    print("=" * 60)
    
    import pytesseract
    
    try:
        languages = pytesseract.get_languages()
        print(f"Available languages: {languages}")
        
        critical_langs = ['eng', 'chi_sim']
        for lang in critical_langs:
            if lang in languages:
                print(f"✓ {lang}: Available")
            else:
                print(f"✗ {lang}: NOT AVAILABLE - This will cause OCR failure!")
                
        return 'chi_sim' in languages and 'eng' in languages
        
    except Exception as e:
        print(f"✗ Language check failed: {e}")
        return False

def test_ocr_functionality():
    """测试OCR实际功能"""
    print("\n" + "=" * 60)
    print("OCR功能测试")
    print("=" * 60)
    
    import pytesseract
    from PIL import Image, ImageDraw, ImageFont
    
    # 创建测试图像
    test_img = Image.new('RGB', (300, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(test_img)
    
    # 添加英文文本
    draw.text((10, 10), "Hello World 123", fill=(0, 0, 0))
    draw.text((10, 50), "Test OCR Function", fill=(0, 0, 0))
    
    # 测试不同语言配置
    test_configs = [
        ('eng', '--psm 6 --oem 3'),
        ('chi_sim+eng', '--psm 6 --oem 3'),
        ('chi_sim+eng', '--psm 3 --oem 3'),
    ]
    
    for lang, config in test_configs:
        try:
            result = pytesseract.image_to_string(test_img, lang=lang, config=config)
            print(f"✓ Lang={lang}, Config={config}")
            print(f"  Result: '{result.strip()}'")
        except Exception as e:
            print(f"✗ Lang={lang}, Config={config}: {e}")

def test_enhanced_extractor():
    """测试增强提取器"""
    print("\n" + "=" * 60)
    print("增强提取器测试")
    print("=" * 60)
    
    sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
    
    try:
        from app.services.enhanced_content_extractor import EnhancedContentExtractor
        
        extractor = EnhancedContentExtractor()
        print(f"Enhanced extractor OCR status: {extractor.has_ocr}")
        
        # 测试乱码检测
        test_text = "[第1页] 8LA5 AP CE RMLAN5 CE 5RE R1"
        is_garbled = extractor._is_garbled_text(test_text)
        print(f"Garbled text detection: {is_garbled}")
        
        return extractor.has_ocr
        
    except Exception as e:
        print(f"Enhanced extractor test failed: {e}")
        return False

def main():
    """主函数"""
    print("OCR功能完整诊断")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # 测试1: 依赖包
    total_tests += 1
    if test_ocr_dependencies():
        success_count += 1
    
    # 测试2: Tesseract可执行程序
    total_tests += 1
    if test_tesseract_executable():
        success_count += 1
    
    # 测试3: 语言支持
    total_tests += 1
    if test_tesseract_languages():
        success_count += 1
    
    # 测试4: OCR功能
    total_tests += 1
    try:
        test_ocr_functionality()
        success_count += 1
    except:
        pass
    
    # 测试5: 增强提取器
    total_tests += 1
    if test_enhanced_extractor():
        success_count += 1
    
    print("\n" + "=" * 60)
    print("诊断结果总结")
    print("=" * 60)
    print(f"通过测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✓ 所有OCR功能正常")
    else:
        print("✗ OCR功能存在问题，请检查上述失败的测试项")
        print("\n建议解决方案:")
        print("1. 确保Tesseract已正确安装")
        print("2. 下载并安装中文语言包 (chi_sim)")
        print("3. 检查Tesseract在系统PATH中")
    
    print("=" * 60)

if __name__ == "__main__":
    main()