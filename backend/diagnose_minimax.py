#!/usr/bin/env python3
"""
MiniMax连接诊断工具
帮助排查连接失败的原因
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8002"

def login():
    """登录获取token"""
    print("正在登录...")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"登录失败: {response.text}")

def check_backend():
    """检查后端是否运行"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ 后端服务正常运行")
            return True
    except:
        print("✗ 后端服务未运行")
        return False

def test_minimax_direct(api_key):
    """直接测试MiniMax API（绕过后端）"""
    print("\n" + "=" * 60)
    print("直接测试MiniMax API（不经过后端）")
    print("=" * 60)

    api_url = "https://api.minimaxi.com/v1/chat/completions"
    model = "MiniMax-M2.7"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    test_data = {
        "model": model,
        "messages": [{"role": "user", "content": "你好"}],
        "max_tokens": 10,
        "temperature": 0.7
    }

    try:
        response = requests.post(api_url, json=test_data, headers=headers, timeout=30)
        print(f"HTTP状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✓ 直接连接MiniMax成功！")

            if result.get("choices") and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", message.get("text", ""))
                print(f"AI回复: {content}")
            return True
        else:
            print("✗ 直接连接MiniMax失败")
            print(f"响应: {response.text}")

            try:
                error_data = response.json()
                print(f"\n错误详情: {json.dumps(error_data, ensure_ascii=False, indent=2)}")

                # 检查MiniMax特有错误
                if error_data.get("base_resp"):
                    base_resp = error_data["base_resp"]
                    status_code = base_resp.get('status_code')
                    status_msg = base_resp.get('status_msg')

                    print(f"\nMiniMax状态码: {status_code}")
                    print(f"MiniMax错误信息: {status_msg}")

                    # 常见错误及解决方案
                    error_solutions = {
                        2013: ("模型不存在", "使用正确的模型名称，如: MiniMax-M2.7"),
                        2061: ("计划不支持该模型", "检查您的MiniMax订阅计划是否包含该模型"),
                        1001: ("API Key无效", "检查API Key是否正确"),
                        1002: ("API Key已过期", "更新API Key"),
                        1003: ("余额不足", "充值账户余额"),
                        401: ("认证失败", "检查API Key格式是否为Bearer Token")
                    }

                    if status_code in error_solutions:
                        reason, solution = error_solutions[status_code]
                        print(f"\n可能原因: {reason}")
                        print(f"解决方案: {solution}")

            except:
                pass
            return False

    except requests.exceptions.Timeout:
        print("✗ 请求超时")
        print("\n可能原因:")
        print("- 网络连接问题")
        print("- API服务器响应慢")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ 连接失败: {e}")
        print("\n可能原因:")
        print("- URL不正确")
        print("- DNS解析失败")
        print("- 网络不可达")
        print("- 防火墙阻止连接")
        return False
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        print(f"错误类型: {type(e).__name__}")
        return False

def test_minimax_via_backend(api_key, api_url="https://api.minimaxi.com/v1/chat/completions", model="MiniMax-M2.7", group_id=""):
    """通过后端测试MiniMax连接"""
    print("\n" + "=" * 60)
    print("通过后端测试MiniMax API")
    print("=" * 60)

    token = login()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    config = {
        "api_key": api_key,
        "api_url": api_url,
        "model": model,
        "group_id": group_id
    }

    print(f"配置的API URL: {api_url}")
    print(f"配置的模型: {model}")
    print(f"API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 20 else api_key}")
    print()

    response = requests.post(
        f"{BASE_URL}/api/v1/assets/ai/test",
        json={"provider": "minimax", "config": config},
        headers=headers,
        timeout=30
    )

    print(f"HTTP状态码: {response.status_code}")

    try:
        result = response.json()
        print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result.get("success"):
            print("\n✓ 通过后端连接MiniMax成功！")
            return True
        else:
            print(f"\n✗ 通过后端连接MiniMax失败")
            print(f"错误信息: {result.get('message', '未知错误')}")

            # 分析错误并提供建议
            error_msg = result.get('message', '')

            print("\n诊断建议:")
            if '2013' in str(result) or '不存在' in error_msg:
                print("- 模型名称错误，请确认使用 MiniMax-M2.7")
            elif '2061' in str(result) or '不支持' in error_msg:
                print("- 检查MiniMax订阅计划是否支持该模型")
            elif '401' in str(result) or '认证' in error_msg:
                print("- API Key可能无效或过期")
            elif 'timeout' in str(result).lower() or '超时' in error_msg:
                print("- 网络连接超时，请检查网络")
            else:
                print("- 请检查API Key和URL配置是否正确")

            return False

    except Exception as e:
        print(f"响应解析失败: {e}")
        print(f"原始响应: {response.text}")
        return False

def main():
    print("=" * 60)
    print("MiniMax API 连接诊断工具")
    print("=" * 60)

    # 1. 检查后端
    if not check_backend():
        print("\n请先启动后端服务！")
        return

    # 2. 获取用户输入
    print("\n请输入您的MiniMax API Key")
    api_key = input("API Key: ").strip()

    if not api_key:
        print("✗ API Key不能为空")
        return

    # 3. 直接测试API
    direct_success = test_minimax_direct(api_key)

    # 4. 通过后端测试API
    backend_success = test_minimax_via_backend(api_key)

    # 5. 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)

    if direct_success and backend_success:
        print("✓ 所有测试通过！连接配置正确。")
    elif direct_success and not backend_success:
        print("⚠️  直接API连接成功，但后端连接失败。")
        print("   这可能是后端代码的问题。")
    elif not direct_success and backend_success:
        print("⚠️  直接API连接失败，但后端连接成功。")
        print("   这可能是因为网络路由或代理设置。")
    else:
        print("✗ 所有测试失败。")
        print("   请检查:")
        print("   1. API Key是否正确")
        print("   2. 网络连接是否正常")
        print("   3. MiniMax账户是否有有效订阅")
        print("   4. 防火墙是否阻止了连接")

    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
