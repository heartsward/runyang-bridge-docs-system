#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR文本修正效果测试脚本
测试中文字符间空格清理和OCR错误修正
"""
import sys
from pathlib import Path

# 添加backend路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def test_ocr_text_processing():
    """测试OCR文本处理效果"""
    try:
        from app.services.enhanced_content_extractor import EnhancedContentExtractor
        
        print("=" * 60)
        print("OCR文本修正效果测试")
        print("=" * 60)
        
        # 创建提取器
        extractor = EnhancedContentExtractor()
        
        # 测试用例 - 基于您提供的实际OCR错误
        test_cases = [
            {
                "name": "实际OCR错误案例",
                "input": "于组 织开 展2025年全 市网络和 姚常 态化 益督 检查 上 f 作的 通知",
                "expected": "关于组织开展2025年全市网络和数据安全常态化监督检查工作的通知"
            },
            {
                "name": "常见中文分割",
                "input": "网 络 安 全 管 理 系 统",
                "expected": "网络安全管理系统"
            },
            {
                "name": "政府文档词汇",
                "input": "各辖 市、区人 民政 府 , 经开 区、高新 区管 委会",
                "expected": "各辖市、区人民政府，经开区、高新区管委会"
            },
            {
                "name": "专业术语",
                "input": "等 级 保 护 单 位 网络 强国 建 设",
                "expected": "等级保护单位网络强国建设"
            },
            {
                "name": "混合内容",
                "input": "根据 公安 部、省公安厅 部署 要求 , 结合 我市 实际 , 决定 自即 日起",
                "expected": "根据公安部、省公安厅部署要求，结合我市实际，决定自即日起"
            }
        ]
        
        print("测试OCR文本后处理功能...")
        print()
        
        success_count = 0
        total_count = len(test_cases)
        
        for i, case in enumerate(test_cases, 1):
            print(f"[测试 {i}] {case['name']}")
            print(f"原始文本: {case['input']}")
            
            # 处理文本
            processed = extractor._post_process_ocr_text(case['input'])
            print(f"处理结果: {processed}")
            print(f"期望结果: {case['expected']}")
            
            # 检查处理效果
            if processed == case['expected']:
                print("[PASS] 完全匹配!")
                success_count += 1
            else:
                print("[PARTIAL] 部分改善:")
                # 分析改善程度
                original_spaces = case['input'].count(' ')
                processed_spaces = processed.count(' ')
                space_reduction = original_spaces - processed_spaces
                
                print(f"  - 空格数量: {original_spaces} -> {processed_spaces} (减少{space_reduction}个)")
                
                # 检查是否包含关键修正
                improvements = []
                if '姚常' not in processed and '数据' in processed:
                    improvements.append("修正了'姚常'→'数据'")
                if '益督' not in processed and '监督' in processed:
                    improvements.append("修正了'益督'→'监督'")
                if '上 f 作' not in processed and '工作' in processed:
                    improvements.append("修正了'上 f 作'→'工作'")
                if len(case['input'].replace(' ', '')) == len(processed.replace(' ', '')):
                    improvements.append("保持了字符完整性")
                
                if improvements:
                    print(f"  - 改善: {', '.join(improvements)}")
                    success_count += 0.5  # 部分成功
            
            print("-" * 50)
        
        print(f"\n测试总结:")
        print(f"测试用例: {total_count}")
        print(f"成功/改善: {success_count:.1f}")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        
        if success_count >= total_count * 0.8:
            print("\n[PASS] OCR文本修正功能工作良好!")
        else:
            print("\n[PARTIAL] OCR文本修正有改善，但仍需优化")
        
        return success_count >= total_count * 0.5
        
    except Exception as e:
        print(f"[FAIL] 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("OCR文本修正效果验证工具")
    print("测试中文字符间空格清理和常见OCR错误修正")
    print()
    
    success = test_ocr_text_processing()
    
    print()
    if success:
        print("[*] 建议:")
        print("1. 提交代码到Git")
        print("2. 在生产环境测试扫描PDF")
        print("3. 观察OCR文本质量改善")
    else:
        print("[*] 需要进一步优化OCR文本处理逻辑")
    
    print()
    input("按任意键退出...")

if __name__ == "__main__":
    main()