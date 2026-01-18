#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Hello API 接口
"""

import requests
import json

# API 基础 URL
BASE_URL = "http://127.0.0.1:8000"

def test_hello_api(name: str):
    """
    测试 hello 接口
    
    Args:
        name: 要测试的名字
    """
    url = f"{BASE_URL}/hello/{name}"
    
    print(f"\n{'='*50}")
    print(f"测试输入: {name}")
    print(f"请求 URL: {url}")
    print(f"{'='*50}")
    
    try:
        # 发送 GET 请求
        response = requests.get(url)
        
        # 打印状态码
        print(f"状态码: {response.status_code}")
        
        # 打印响应头
        print(f"响应头: {dict(response.headers)}")
        
        # 解析 JSON 响应
        if response.status_code == 200:
            data = response.json()
            print(f"\n响应结果:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            print(f"\n消息内容: {data.get('message', 'N/A')}")
        else:
            print(f"\n错误响应:")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误: 无法连接到服务器")
        print("请确保服务器正在运行: uvicorn main:app --reload")
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        print(f"原始响应: {response.text}")

if __name__ == "__main__":
    # 测试输入"北京"
    test_hello_api("北京")
    
    print(f"\n{'='*50}")
    print("测试完成！")
    print(f"{'='*50}\n")
