#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Search API 接口
"""

import requests
import json

# API 基础 URL
BASE_URL = "http://127.0.0.1:8000"

def test_search_api(keyword: str, max_results: int = 6):
    """
    测试 search 接口
    
    Args:
        keyword: 搜索关键字
        max_results: 最大结果数，默认 6
    """
    url = f"{BASE_URL}/search"
    
    payload = {
        "keyword": keyword,
        "max_results": max_results
    }
    
    print(f"\n{'='*50}")
    print(f"搜索关键字: {keyword}")
    print(f"最大结果数: {max_results}")
    print(f"请求 URL: {url}")
    print(f"{'='*50}")
    
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
            
            print(f"\n搜索结果摘要:")
            print(f"  - 关键字: {data.get('keyword', 'N/A')}")
            print(f"  - 结果数量: {len(data.get('results', []))}")
            if data.get('combined_answer'):
                print(f"  - 综合答案: {data['combined_answer'][:100]}...")
            
            # 显示前3个结果
            results = data.get('results', [])
            if results:
                print(f"\n前 {min(3, len(results))} 个搜索结果:")
                for i, result in enumerate(results[:3], 1):
                    print(f"\n  [{i}] {result.get('title', 'N/A')}")
                    print(f"      URL: {result.get('url', 'N/A')}")
                    if result.get('content'):
                        content = result['content'][:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                        print(f"      内容: {content}")
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
    # 测试搜索"人工智能"
    test_search_api("人工智能", max_results=5)
    
    print(f"\n{'='*50}")
    print("测试完成！")
    print(f"{'='*50}\n")
