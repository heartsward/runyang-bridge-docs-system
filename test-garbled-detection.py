#!/usr/bin/env python3
"""
测试乱码检测功能
"""
import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加后端路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.enhanced_content_extractor import EnhancedContentExtractor

def test_garbled_detection():
    """测试乱码检测功能"""
    extractor = EnhancedContentExtractor()
    
    # 测试用例
    test_cases = [
        {
            "name": "正常中文文本",
            "text": "这是一份正常的中文文档，包含了完整的句子和词汇。文档内容描述了系统的功能和使用方法。",
            "expected": False
        },
        {
            "name": "正常英文文本", 
            "text": "This is a normal English document with complete sentences and vocabulary. The document describes system functionality and usage.",
            "expected": False
        },
        {
            "name": "实际乱码样本",
            "text": "[第1页] 8LA5 AP CE RMLAN5 CE 5RE R1 (2025) 2 5 FEF HAA 1P 2025 AFTER A5E ea 5it. REAR5, AK. 8HEP55, HA8A, 5ER8, A8W, AARR5ERRP 5M: ARATHAA8RE8RR, mMRAAMAER5 be, RAHREERE, AF M85A, REAR. 8A KRARAER, 60RE, AKAM ER, E5HeH AMAA RA PRER5 8A 8ee TE, MARK Lie we",
            "expected": True
        },
        {
            "name": "另一个乱码样本",
            "text": "[第2页] RR ERAAKMEZAR5 HEPREZAR5 EE5 WH, RAMA, FREKEAMAMHEZERR. T5R me AP AAL5 EMRE. ER8 R0M5 8hACK, ARMUMM8KERE, ARRWTRE8K MALAE HE ARE EH = 8A5H",
            "expected": True
        },
        {
            "name": "混合内容",
            "text": "这是一个包含正常文字和乱码的测试: 8LA5 AP CE RMLAN5 但是大部分内容是正常的中文文字，应该不会被误判为乱码。",
            "expected": False
        },
        {
            "name": "短文本",
            "text": "短文本",
            "expected": False
        },
        {
            "name": "大量大写字母",
            "text": "THIS IS ALL UPPERCASE TEXT WITH MANY CAPITAL LETTERS AND NUMBERS 123 456 789 BUT STILL READABLE ENGLISH WORDS",
            "expected": False
        }
    ]
    
    print("=" * 60)
    print("乱码检测功能测试")
    print("=" * 60)
    
    correct = 0
    total = len(test_cases)
    
    for case in test_cases:
        result = extractor._is_garbled_text(case["text"])
        expected = case["expected"]
        status = "✅ 正确" if result == expected else "❌ 错误"
        
        print(f"\n测试: {case['name']}")
        print(f"预期: {'乱码' if expected else '正常'} | 结果: {'乱码' if result else '正常'} | {status}")
        print(f"文本样本: {case['text'][:100]}...")
        
        if result == expected:
            correct += 1
    
    print(f"\n" + "=" * 60)
    print(f"测试结果: {correct}/{total} 正确 ({correct/total*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    test_garbled_detection()