#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Chat API 的 Agentic Loop 功能
"""

import requests
import json

# API 基础 URL
BASE_URL = "http://127.0.0.1:8000"

def test_chat_agentic(message: str, model: str = "gpt-5"):
    """
    测试 chat 接口的 Agentic Loop 功能
    
    Args:
        message: 要发送的消息
        model: 使用的模型，默认为 gpt-5
    """
    url = f"{BASE_URL}/chat"
    
    payload = {
        "message": message,
        "model": model
    }
    
    print(f"\n{'='*60}")
    print(f"测试消息: {message}")
    print(f"使用模型: {model}")
    print(f"请求 URL: {url}")
    print(f"{'='*60}")
    
    try:
        # 发送 POST 请求
        response = requests.post(url, json=payload)
        
        # 打印状态码
        print(f"状态码: {response.status_code}")
        
        # 解析 JSON 响应
        if response.status_code == 200:
            data = response.json()
            print(f"\n响应结果:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            print(f"\nAI 最终回复:")
            print(f"{'='*60}")
            print(data.get('message', 'N/A'))
            print(f"{'='*60}")
            
            if data.get('usage'):
                print(f"\nToken 使用情况:")
                print(f"  - Prompt tokens: {data['usage'].get('prompt_tokens', 'N/A')}")
                print(f"  - Completion tokens: {data['usage'].get('completion_tokens', 'N/A')}")
                print(f"  - Total tokens: {data['usage'].get('total_tokens', 'N/A')}")
        else:
            print(f"\n错误响应:")
            print(json.dumps(response.json(), ensure_ascii=False, indent=2))
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务器")
        print("请确保服务器正在运行: uvicorn main:app --reload")
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        print(f"原始响应: {response.text}")

if __name__ == "__main__":
    # 测试需要搜索的问题
    print("\n测试 1: 需要搜索的问题")
    test_chat_agentic("最新的 AI 技术发展如何？", model="gpt-5")
    
    print("\n\n测试 2: 不需要搜索的问题")
    test_chat_agentic("你好，请介绍一下你自己", model="gpt-5")
    
    print(f"\n{'='*60}")
    print("测试完成！")
    print(f"{'='*60}\n")
