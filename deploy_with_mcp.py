#!/usr/bin/env python3
"""
使用AI Builders平台部署服务
通过MCP工具获取token并执行部署
"""
import requests
import json
import sys

# 从MCP工具获取的token
TOKEN = "sk_fcc72e98_34f93b167d98d33505f4b5b447e9f4571fa7"

# API配置 - 根据OpenAPI规范，base URL应该是 space.ai-builders.com/backend
API_BASE_URL = "https://space.ai-builders.com/backend"
DEPLOYMENT_ENDPOINT = f"{API_BASE_URL}/v1/deployments"

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
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    print("=" * 60)
    print("🚀 开始部署中国历史五千年网站")
    print("=" * 60)
    print(f"📦 仓库地址: {DEPLOYMENT_CONFIG['repo_url']}")
    print(f"🏷️  服务名称: {DEPLOYMENT_CONFIG['service_name']}")
    print(f"🌿 分支: {DEPLOYMENT_CONFIG['branch']}")
    print(f"🔌 端口: {DEPLOYMENT_CONFIG['port']}")
    print(f"🌐 API端点: {DEPLOYMENT_ENDPOINT}")
    print("-" * 60)
    
    try:
        print("📡 正在发送部署请求...")
        response = requests.post(
            DEPLOYMENT_ENDPOINT,
            headers=headers,
            json=DEPLOYMENT_CONFIG,
            timeout=30,
            allow_redirects=True
        )
        
        print(f"📊 HTTP状态码: {response.status_code}")
        print(f"📄 响应头: {dict(response.headers)}")
        
        # 尝试解析JSON响应
        try:
            response_data = response.json()
            print("\n📋 响应内容:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            if response.status_code == 202:
                print("\n" + "=" * 60)
                print("✅ 部署请求已成功提交！")
                print("=" * 60)
                
                if "service_url" in response_data:
                    print(f"🌐 服务URL: {response_data['service_url']}")
                if "status" in response_data:
                    print(f"📊 状态: {response_data['status']}")
                if "deployment_prompt_url" in response_data:
                    print(f"📖 部署文档: {response_data['deployment_prompt_url']}")
                
                print("\n⏳ 部署通常需要5-10分钟完成")
                print("💡 您可以通过以下命令查询部署状态:")
                print(f"   curl -X GET \"{API_BASE_URL}/v1/deployments/{DEPLOYMENT_CONFIG['service_name']}\" \\")
                print(f"     -H \"Authorization: Bearer $AI_BUILDER_TOKEN\"")
                return True
            else:
                print(f"\n❌ 部署失败 (状态码: {response.status_code})")
                if "detail" in response_data:
                    print(f"错误详情: {response_data['detail']}")
                return False
                
        except json.JSONDecodeError:
            print(f"\n⚠️  响应不是JSON格式")
            print(f"响应内容: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ 连接错误: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求错误: {e}")
        return False

if __name__ == "__main__":
    success = deploy()
    sys.exit(0 if success else 1)

