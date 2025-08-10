#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分析API数据是否正确
"""
import requests
import json
import sys

# Windows控制台编码问题修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_analytics_api():
    """测试分析API接口"""
    base_url = "http://localhost:8002"
    
    # 测试登录
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # 登录获取token (使用JSON)
        login_response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"❌ 登录失败: {login_response.status_code}")
            return
            
        token = login_response.json().get("access_token")
        if not token:
            print("❌ 未获取到访问令牌")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # 测试分析统计API
        stats_response = requests.get(f"{base_url}/api/v1/analytics/stats", headers=headers)
        if stats_response.status_code != 200:
            print(f"❌ 获取统计数据失败: {stats_response.status_code}")
            return
            
        stats_data = stats_response.json()
        
        print("📊 分析统计数据测试结果:")
        print(f"  总文档数: {stats_data.get('total_documents', 'N/A')}")
        print(f"  总资产数: {stats_data.get('total_assets', 'N/A')}")
        print(f"  总用户数: {stats_data.get('total_users', 'N/A')}")
        print(f"  总搜索次数: {stats_data.get('total_searches', 'N/A')}")
        print(f"  文档查看次数: {stats_data.get('total_document_views', 'N/A')}")
        print(f"  资产查看次数: {stats_data.get('total_asset_views', 'N/A')}")
        print(f"  系统状态: {stats_data.get('system_status', 'N/A')}")
        
        # 验证是否还有硬编码数据
        problems = []
        if stats_data.get('total_documents') == 15:
            problems.append("文档数仍为硬编码值15")
        if stats_data.get('total_assets') == 6:
            problems.append("资产数仍为硬编码值6")
        if stats_data.get('total_searches') == 156 or stats_data.get('total_searches') == 125:
            problems.append("搜索次数仍为硬编码值")
            
        if problems:
            print("⚠️  发现的问题:")
            for problem in problems:
                print(f"    - {problem}")
        else:
            print("✅ 数据看起来正确，没有发现硬编码问题")
            
        # 检查用户活动统计
        user_stats = stats_data.get('userActivityStats', [])
        print(f"\n👥 用户活动统计: {len(user_stats)} 个用户")
        
        # 检查搜索关键词
        search_keywords = stats_data.get('searchKeywords', [])
        print(f"🔍 搜索关键词: {len(search_keywords)} 个关键词")
        
        if search_keywords:
            print("    搜索关键词列表:")
            for kw in search_keywords[:3]:
                print(f"      - {kw.get('keyword')}: {kw.get('count')}次")
        
        print(f"\n📝 完整数据 (前100字符): {str(stats_data)[:100]}...")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到后端服务，请确保服务正在运行")
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_analytics_api()