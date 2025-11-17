#!/usr/bin/env python3
"""
部署脚本 - 使用AI Builders平台部署服务
"""
import requests
import os
import json

# API配置
API_BASE_URL = "https://www.ai-builders.com/resources/students-backend"
DEPLOYMENT_ENDPOINT = f"{API_BASE_URL}/v1/deployments"

# 从环境变量获取token，如果没有则使用提供的token
TOKEN = os.getenv("AI_BUILDER_TOKEN", "sk_fcc72e98_34f93b167d98d33505f4b5b447e9f4571fa7")

# 部署配置
DEPLOYMENT_CONFIG = {
    "repo_url": "https://github.com/challenwang408408/demo-website",
    "service_name": "chinese-history",
    "branch": "main",
    "port": 8000
}

def deploy():
    """部署服务到AI Builders平台"""
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"正在部署服务到: {DEPLOYMENT_CONFIG['repo_url']}")
    print(f"服务名称: {DEPLOYMENT_CONFIG['service_name']}")
    print(f"分支: {DEPLOYMENT_CONFIG['branch']}")
    print(f"端口: {DEPLOYMENT_CONFIG['port']}")
    print("-" * 50)
    
    try:
        response = requests.post(
            DEPLOYMENT_ENDPOINT,
            headers=headers,
            json=DEPLOYMENT_CONFIG,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 202:
            print("\n✅ 部署请求已成功提交！")
            deployment_data = response.json()
            if "service_url" in deployment_data:
                print(f"🌐 服务URL: {deployment_data['service_url']}")
            print("\n⏳ 部署通常需要5-10分钟完成，请稍候...")
        else:
            print(f"\n❌ 部署失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求错误: {e}")

if __name__ == "__main__":
    deploy()

