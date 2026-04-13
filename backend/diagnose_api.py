#!/usr/bin/env python3
"""
API错误诊断脚本
"""
import requests
import json

BASE_URL = "http://localhost:8002"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[OK] Health check: {response.status_code}")
        print(f"  Response: {response.json()}")
        return True
    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False

def test_login():
    """测试登录"""
    try:
        # 尝试 form data
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            timeout=5
        )
        print(f"[OK] Login (form): {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[FAIL] Login failed: {e}")
        return False

def test_documents():
    """测试文档列表"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents/", timeout=5)
        print(f"[OK] Documents list: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[FAIL] Documents list failed: {e}")
        return False

def test_search():
    """测试搜索"""
    try:
        # 需要先获取token才能测试搜索
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": "admin", "password": "admin123"},
            timeout=5
        )
        token = login_response.json().get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}

        response = requests.get(f"{BASE_URL}/api/v1/search/documents?q=test", headers=headers, timeout=5)
        print(f"[OK] Search: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[FAIL] Search failed: {e}")
        return False

def test_assets():
    """测试资产"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/assets/", timeout=5)
        print(f"[OK] Assets list: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
        else:
            print(f"  Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"[FAIL] Assets list failed: {e}")
        return False

def main():
    print("=" * 60)
    print("API 诊断测试")
    print("=" * 60)
    
    results = []
    
    print("\n1. 健康检查:")
    results.append(test_health())
    
    print("\n2. 登录测试:")
    results.append(test_login())
    
    print("\n3. 文档列表:")
    results.append(test_documents())
    
    print("\n4. 搜索测试:")
    results.append(test_search())
    
    print("\n5. 资产列表:")
    results.append(test_assets())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)

if __name__ == "__main__":
    main()
