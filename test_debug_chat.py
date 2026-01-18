#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 Chat API 的工具调用情况
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 直接调用 AI Builder Space API 来测试工具调用
AI_BUILDER_BASE_URL = "https://space.ai-builders.com/backend/v1"
AI_BUILDER_CHAT_ENDPOINT = f"{AI_BUILDER_BASE_URL}/chat/completions"
token = os.getenv("AI_BUILDER_TOKEN")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

search_tool = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "搜索网络获取最新信息和实时数据。当用户询问关于最近发生的事件、最新新闻、当前信息、实时数据或需要网络搜索才能回答的问题时，必须使用此工具。如果问题涉及'最近'、'最新'、'现在'、'当前'等时间相关的词汇，或者涉及你不知道的最新信息，都应该调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "要搜索的关键字，应该包含问题的核心信息"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大返回结果数，默认6，最大20",
                    "default": 6,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["keyword"]
        }
    }
}

payload = {
    "model": "gpt-5",
    "messages": [
        {
            "role": "user",
            "content": "腾讯最近招了一个openai来的ai大牛，叫什么名字"
        }
    ],
    "temperature": 1.0,
    "tools": [search_tool]
}

print("发送请求到 AI Builder Space...")
print(f"工具定义: {json.dumps(search_tool, ensure_ascii=False, indent=2)}")
print()

response = requests.post(
    AI_BUILDER_CHAT_ENDPOINT,
    headers=headers,
    json=payload,
    timeout=120
)

response.raise_for_status()
data = response.json()

print("响应结果:")
print(json.dumps(data, ensure_ascii=False, indent=2))
print()

choice = data["choices"][0]
message = choice["message"]
finish_reason = choice.get("finish_reason")
tool_calls = message.get("tool_calls")

print(f"Finish reason: {finish_reason}")
print(f"Tool calls: {tool_calls}")
print(f"Message content: {message.get('content', 'None')}")
