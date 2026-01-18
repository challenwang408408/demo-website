from fastapi import FastAPI, Path, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import requests
import os
import json as json_lib
import logging
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import uuid

# 加载环境变量
load_dotenv()

# 配置日志
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"chat_agentic_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

logger = logging.getLogger(__name__)

# AI Builder Space 配置
AI_BUILDER_BASE_URL = "https://space.ai-builders.com/backend/v1"
AI_BUILDER_CHAT_ENDPOINT = f"{AI_BUILDER_BASE_URL}/chat/completions"
AI_BUILDER_SEARCH_ENDPOINT = f"{AI_BUILDER_BASE_URL}/search/"

app = FastAPI(
    title="hello",
    description="""
    ## Hello API 接口文档
    
    这是一个简单的问候接口，用于测试和演示 FastAPI 的使用。
    
    ### 功能特点
    - 支持中文和英文名字
    - 支持拼音输入
    - 返回友好的问候消息
    
    ### 使用场景
    - API 测试
    - 学习 FastAPI
    - 快速验证服务是否正常运行
    """,
    version="1.0.0",
    contact={
        "name": "API 支持",
        "email": "support@example.com",
    },
)

# 挂载静态文件
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 对话历史存储目录
CHAT_HISTORY_DIR = "chat_history"
if not os.path.exists(CHAT_HISTORY_DIR):
    os.makedirs(CHAT_HISTORY_DIR)

# 对话历史索引文件
CHAT_INDEX_FILE = os.path.join(CHAT_HISTORY_DIR, "index.json")

def load_chat_index():
    """加载对话索引"""
    if os.path.exists(CHAT_INDEX_FILE):
        try:
            with open(CHAT_INDEX_FILE, 'r', encoding='utf-8') as f:
                return json_lib.load(f)
        except Exception as e:
            logger.error(f"加载对话索引失败: {e}")
            return []
    return []

def save_chat_index(index):
    """保存对话索引"""
    try:
        with open(CHAT_INDEX_FILE, 'w', encoding='utf-8') as f:
            json_lib.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存对话索引失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存对话索引失败: {e}")

def get_chat_file_path(chat_id):
    """获取对话文件的路径"""
    return os.path.join(CHAT_HISTORY_DIR, f"{chat_id}.json")

def generate_title_from_message(message: str) -> str:
    """根据用户消息生成标题"""
    # 简单实现：取前30个字符作为标题
    title = message.strip()
    if len(title) > 30:
        title = title[:30] + "..."
    return title if title else "新对话"

@app.get("/")
async def root():
    """返回前端页面"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Please access /static/index.html"}


class HelloResponse(BaseModel):
    """响应模型"""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello 鸭哥"
            }
        }


@app.get(
    "/hello/{name}",
    summary="问候接口",
    description="根据输入的名字返回问候消息，支持中文、英文和拼音。",
    response_description="成功返回问候消息",
    responses={
        200: {
            "description": "成功响应",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Hello 鸭哥"
                    }
                }
            }
        },
        422: {
            "description": "参数验证错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["path", "name"],
                                "msg": "field required",
                                "type": "value_error.missing"
                            }
                        ]
                    }
                }
            }
        }
    },
    tags=["问候"]
)
async def hello(
    name: str = Path(
        ...,
        description="要问候的名字，支持中文、英文或拼音",
        example="鸭哥",
        min_length=1,
        max_length=50
    )
) -> HelloResponse:
    """
    返回 Hello + 名字的接口
    
    Args:
        name: 输入的名字，可以是中文、英文或拼音
        
    Returns:
        HelloResponse: 包含问候消息的响应对象
        
    Raises:
        422: 当参数验证失败时
    """
    return HelloResponse(message=f"Hello {name}")


# Chat 相关的模型定义
class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = "user"
    content: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "你好，请介绍一下你自己"
            }
        }


class ChatRequest(BaseModel):
    """Chat 请求模型"""
    message: str
    model: Optional[str] = "gpt-5"
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好，请介绍一下你自己",
                "model": "gpt-5",
                "temperature": 1.0
            }
        }


class ChatResponse(BaseModel):
    """Chat 响应模型"""
    message: str
    model: str
    usage: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "你好！我是 GPT-5，一个 AI 助手...",
                "model": "gpt-5",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }
        }


def _execute_single_tool_call(tool_call: dict) -> tuple:
    """
    执行单个工具调用
    
    Args:
        tool_call: 工具调用对象
        
    Returns:
        tuple: (tool_call_id, search_content)
    """
    function_name = tool_call["function"]["name"]
    tool_call_id = tool_call["id"]
    
    logger.info("=" * 80)
    logger.info(f"🔧 开始执行工具调用")
    logger.info(f"   工具ID: {tool_call_id}")
    logger.info(f"   工具名称: {function_name}")
    
    if function_name == "search":
        try:
            function_args = json_lib.loads(tool_call["function"]["arguments"])
            keyword = function_args.get("keyword")
            max_results = function_args.get("max_results", 6)
            
            logger.info(f"   工具参数:")
            logger.info(f"     - keyword: {keyword}")
            logger.info(f"     - max_results: {max_results}")
            
            if not keyword:
                search_content = "错误: 搜索关键字不能为空。"
                logger.warning(f"   ⚠️ 搜索关键字为空")
            else:
                # 执行搜索
                try:
                    logger.info(f"   🔍 正在执行搜索...")
                    search_result = _execute_search(keyword, max_results)
                    
                    # 格式化搜索结果
                    results = []
                    if "queries" in search_result and len(search_result["queries"]) > 0:
                        query_result = search_result["queries"][0]
                        if "response" in query_result and "results" in query_result["response"]:
                            results = query_result["response"]["results"]
                    
                    logger.info(f"   ✅ 搜索完成，找到 {len(results)} 个结果")
                    
                    # 构建搜索结果文本
                    search_content = f"搜索关键字: {keyword}\n\n"
                    if results:
                        search_content += f"找到 {len(results)} 个结果:\n\n"
                        for i, result in enumerate(results[:5], 1):  # 只取前5个结果
                            title = result.get('title', 'N/A')
                            url = result.get('url', 'N/A')
                            search_content += f"{i}. {title}\n"
                            search_content += f"   URL: {url}\n"
                            content = result.get('content', '')
                            if content:
                                # 限制内容长度
                                content_preview = content[:300] + "..." if len(content) > 300 else content
                                search_content += f"   内容: {content_preview}\n"
                            search_content += "\n"
                            
                            # 记录每个搜索结果
                            logger.info(f"     结果 {i}: {title}")
                            logger.info(f"       URL: {url}")
                    else:
                        search_content += "未找到相关结果。\n"
                        logger.warning(f"   ⚠️ 未找到搜索结果")
                    
                    logger.info(f"   📄 搜索结果内容长度: {len(search_content)} 字符")
                except Exception as e:
                    search_content = f"搜索失败: {str(e)}"
                    logger.error(f"   ❌ 搜索执行失败: {str(e)}")
        except Exception as e:
            search_content = f"解析搜索参数失败: {str(e)}"
            logger.error(f"   ❌ 解析工具参数失败: {str(e)}")
    else:
        search_content = f"未知的工具类型: {function_name}"
        logger.warning(f"   ⚠️ 未知的工具类型: {function_name}")
    
    logger.info(f"✅ 工具调用完成")
    logger.info("=" * 80)
    
    return tool_call_id, search_content


def _execute_search(keyword: str, max_results: int = 6) -> dict:
    """
    内部函数：执行搜索并返回结果
    
    Args:
        keyword: 搜索关键字
        max_results: 最大结果数
        
    Returns:
        dict: 搜索结果
        
    Raises:
        Exception: 当搜索失败时
    """
    token = os.getenv("AI_BUILDER_TOKEN")
    if not token:
        raise Exception("AI_BUILDER_TOKEN 未配置")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    max_results = max(1, min(20, max_results))
    payload = {
        "keywords": [keyword],
        "max_results": max_results
    }
    
    try:
        response = requests.post(
            AI_BUILDER_SEARCH_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"搜索请求失败: {str(e)}")


@app.post(
    "/chat",
    summary="Chat 聊天接口（Agentic Loop）",
    description="接收用户消息，模型可自动调用 search 工具获取信息，然后生成最终答案。",
    response_description="返回 AI 助手的回复",
    responses={
        200: {
            "description": "成功响应",
            "content": {
                "application/json": {
                    "example": {
                        "message": "你好！我是 GPT-5，一个 AI 助手...",
                        "model": "gpt-5",
                        "usage": {
                            "prompt_tokens": 10,
                            "completion_tokens": 20,
                            "total_tokens": 30
                        }
                    }
                }
            }
        },
        400: {
            "description": "请求错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "AI_BUILDER_TOKEN 未配置"
                    }
                }
            }
        },
        500: {
            "description": "服务器错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "转发请求失败: Connection error"
                    }
                }
            }
        }
    },
    tags=["聊天"]
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Chat 聊天接口，实现 Agentic Loop：支持工具调用（search）
    
    Args:
        request: Chat 请求对象，包含用户消息和参数
        
    Returns:
        ChatResponse: 包含 AI 回复的响应对象
        
    Raises:
        400: 当 AI_BUILDER_TOKEN 未配置时
        500: 当转发请求失败时
    """
    # 获取认证 token
    token = os.getenv("AI_BUILDER_TOKEN")
    if not token:
        raise HTTPException(
            status_code=400,
            detail="AI_BUILDER_TOKEN 未配置，请在 .env 文件中设置 AI_BUILDER_TOKEN"
        )
    
    # 构建请求到 AI Builder Space
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 定义 search 工具
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
    
    # 构建消息列表
    messages = [
        {
            "role": "user",
            "content": request.message
        }
    ]
    
    # GPT-5 模型特殊处理：temperature 固定为 1.0，使用 max_completion_tokens
    base_payload = {
        "model": request.model,
        "messages": messages,
        "temperature": 1.0 if request.model == "gpt-5" else (request.temperature or 0.7),
        "tools": [search_tool]
    }
    
    # GPT-5 使用 max_completion_tokens 而不是 max_tokens
    if request.max_tokens:
        if request.model == "gpt-5":
            base_payload["max_completion_tokens"] = request.max_tokens
        else:
            base_payload["max_tokens"] = request.max_tokens
    
    try:
        # Agentic Loop: 最多允许三轮工具调用
        max_tool_rounds = 3
        tool_round = 0
        total_usage = None
        
        logger.info("=" * 80)
        logger.info("🚀 开始 Agentic Loop")
        logger.info(f"   用户消息: {request.message}")
        logger.info(f"   模型: {request.model}")
        logger.info(f"   最大工具调用轮数: {max_tool_rounds}")
        logger.info("=" * 80)
        
        while tool_round <= max_tool_rounds:
            logger.info("")
            logger.info(f"📊 第 {tool_round + 1} 轮交互")
            logger.info(f"   当前工具调用轮数: {tool_round}/{max_tool_rounds}")
            
            # 发送请求到 AI Builder Space
            logger.info("   📤 发送请求到 AI Builder Space...")
            response = requests.post(
                AI_BUILDER_CHAT_ENDPOINT,
                headers=headers,
                json=base_payload,
                timeout=120
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "choices" not in data or len(data["choices"]) == 0:
                raise HTTPException(
                    status_code=500,
                    detail="AI Builder Space 返回了无效的响应格式"
                )
            
            choice = data["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason")
            tool_calls = message.get("tool_calls")
            
            logger.info("   ✅ 收到模型响应")
            logger.info(f"   Finish reason: {finish_reason}")
            
            # 累计 token 使用量
            if data.get("usage"):
                if total_usage is None:
                    total_usage = data["usage"].copy()
                else:
                    total_usage["prompt_tokens"] += data["usage"].get("prompt_tokens", 0)
                    total_usage["completion_tokens"] += data["usage"].get("completion_tokens", 0)
                    total_usage["total_tokens"] += data["usage"].get("total_tokens", 0)
                
                logger.info(f"   本轮 Token 使用: {data['usage'].get('total_tokens', 0)}")
                logger.info(f"   累计 Token 使用: {total_usage.get('total_tokens', 0)}")
            
            # 检查是否有工具调用
            has_tool_calls = tool_calls and len(tool_calls) > 0
            
            if has_tool_calls:
                logger.info(f"   🔧 检测到 {len(tool_calls)} 个工具调用")
                for i, tc in enumerate(tool_calls, 1):
                    logger.info(f"      工具调用 {i}: {tc['function']['name']}")
                    logger.info(f"        参数: {tc['function']['arguments']}")
            else:
                logger.info("   💬 模型直接生成回复，无工具调用")
            
            # 如果达到最大轮数，强制不调用工具，生成最终答案
            if tool_round >= max_tool_rounds:
                logger.info("")
                logger.info("⚠️  已达到最大工具调用轮数，强制生成最终答案")
                logger.info("   设置 tool_choice='none'，移除工具定义")
                
                # 强制生成最终答案（无论是否有工具调用）
                # 移除工具定义，强制生成答案
                final_payload = {
                    **base_payload,
                    "messages": messages,
                    "tool_choice": "none"
                }
                # 移除 tools 字段
                final_payload.pop("tools", None)
                
                logger.info("   📤 发送最终生成请求...")
                final_response = requests.post(
                    AI_BUILDER_CHAT_ENDPOINT,
                    headers=headers,
                    json=final_payload,
                    timeout=120
                )
                
                final_response.raise_for_status()
                final_data = final_response.json()
                
                if "choices" in final_data and len(final_data["choices"]) > 0:
                    final_message = final_data["choices"][0]["message"]
                    final_content = final_message.get("content", "")
                    
                    # 累计最终回复的 token 使用量
                    if final_data.get("usage"):
                        total_usage["prompt_tokens"] += final_data["usage"].get("prompt_tokens", 0)
                        total_usage["completion_tokens"] += final_data["usage"].get("completion_tokens", 0)
                        total_usage["total_tokens"] += final_data["usage"].get("total_tokens", 0)
                    
                    logger.info("")
                    logger.info("=" * 80)
                    logger.info("✅ Agentic Loop 完成")
                    logger.info(f"   最终答案长度: {len(final_content)} 字符")
                    logger.info(f"   总 Token 使用: {total_usage.get('total_tokens', 0)}")
                    logger.info(f"      - Prompt tokens: {total_usage.get('prompt_tokens', 0)}")
                    logger.info(f"      - Completion tokens: {total_usage.get('completion_tokens', 0)}")
                    logger.info("=" * 80)
                    
                    # 打印完整的消息历史
                    logger.info("")
                    logger.info("=" * 80)
                    logger.info("📋 完整消息历史")
                    logger.info("=" * 80)
                    
                    # 1. 初始用户消息
                    if messages and messages[0].get("role") == "user":
                        logger.info("")
                        logger.info("1️⃣ 初始用户消息:")
                        logger.info(f"   {json_lib.dumps(messages[0], ensure_ascii=False, indent=2)}")
                    
                    # 2. 遍历所有消息，按顺序显示 assistant 的 tool_calls 和 tool 的结果
                    msg_index = 2
                    for msg in messages[1:]:  # 跳过第一条用户消息
                        if msg.get("role") == "assistant" and msg.get("tool_calls"):
                            logger.info("")
                            logger.info(f"{msg_index}️⃣ Assistant 工具调用:")
                            logger.info(f"   {json_lib.dumps(msg, ensure_ascii=False, indent=2)}")
                            msg_index += 1
                        elif msg.get("role") == "tool":
                            logger.info("")
                            logger.info(f"{msg_index}️⃣ 工具搜索结果:")
                            tool_result_display = {
                                "role": msg.get("role"),
                                "tool_call_id": msg.get("tool_call_id"),
                                "content": msg.get("content", "")
                            }
                            logger.info(f"   {json_lib.dumps(tool_result_display, ensure_ascii=False, indent=2)}")
                            msg_index += 1
                    
                    # 3. 最终 assistant 消息
                    logger.info("")
                    logger.info(f"{msg_index}️⃣ 最终 Assistant 回复:")
                    final_message_display = {
                        "role": "assistant",
                        "content": final_content
                    }
                    logger.info(f"   {json_lib.dumps(final_message_display, ensure_ascii=False, indent=2)}")
                    
                    logger.info("")
                    logger.info("=" * 80)
                    
                    return ChatResponse(
                        message=final_content,
                        model=final_data.get("model", request.model),
                        usage=total_usage
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="AI Builder Space 返回了无效的响应格式"
                    )
            
            # 如果有工具调用且未达到最大轮数
            if has_tool_calls:
                tool_round += 1
                logger.info(f"   🔄 进入工具调用阶段（第 {tool_round} 轮）")
                
                # 添加 assistant 消息（包含工具调用）
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                })
                
                # 并行执行所有工具调用
                logger.info(f"   ⚡ 开始并行执行 {len(tool_calls)} 个工具调用...")
                tool_results = {}
                with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
                    # 提交所有工具调用任务
                    future_to_tool_call = {
                        executor.submit(_execute_single_tool_call, tool_call): tool_call 
                        for tool_call in tool_calls
                    }
                    
                    # 收集结果
                    for future in as_completed(future_to_tool_call):
                        tool_call_id, search_content = future.result()
                        tool_results[tool_call_id] = search_content
                
                logger.info(f"   ✅ 所有工具调用完成，共 {len(tool_results)} 个结果")
                
                # 按工具调用的顺序添加工具结果
                for tool_call in tool_calls:
                    tool_call_id = tool_call["id"]
                    search_content = tool_results.get(tool_call_id, "工具调用失败")
                    
                    logger.info(f"   📝 添加工具结果到消息列表 (ID: {tool_call_id[:20]}...)")
                    
                    messages.append({
                        "role": "tool",
                        "content": search_content,
                        "tool_call_id": tool_call_id
                    })
                
                # 更新 payload，准备下一轮
                base_payload["messages"] = messages
                logger.info(f"   ➡️  准备进入下一轮交互...")
                # 继续允许工具调用（如果还有轮数）
                
            else:
                # 没有工具调用，直接返回回复
                message_content = message.get("content", "")
                
                logger.info("")
                logger.info("=" * 80)
                logger.info("✅ Agentic Loop 完成（无工具调用）")
                logger.info(f"   最终答案长度: {len(message_content)} 字符")
                logger.info(f"   总 Token 使用: {total_usage.get('total_tokens', 0) if total_usage else 0}")
                logger.info("=" * 80)
                
                # 打印完整的消息历史（无工具调用的情况）
                logger.info("")
                logger.info("=" * 80)
                logger.info("📋 完整消息历史")
                logger.info("=" * 80)
                
                # 1. 初始用户消息
                if messages and messages[0].get("role") == "user":
                    logger.info("")
                    logger.info("1️⃣ 初始用户消息:")
                    logger.info(f"   {json_lib.dumps(messages[0], ensure_ascii=False, indent=2)}")
                
                # 2. 最终 assistant 消息（无工具调用）
                logger.info("")
                logger.info("2️⃣ 最终 Assistant 回复（无工具调用）:")
                final_message_display = {
                    "role": "assistant",
                    "content": message_content
                }
                logger.info(f"   {json_lib.dumps(final_message_display, ensure_ascii=False, indent=2)}")
                
                logger.info("")
                logger.info("=" * 80)
                
                return ChatResponse(
                    message=message_content,
                    model=data.get("model", request.model),
                    usage=total_usage
                )
        
        # 如果循环结束（理论上不应该到达这里）
        logger.error("❌ Agentic Loop 异常结束")
        raise HTTPException(
            status_code=500,
            detail="Agentic Loop 异常结束"
        )
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ 请求失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"转发请求失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ 处理错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"处理请求时发生错误: {str(e)}"
        )


def send_sse_event(data: dict):
    """发送 SSE 事件"""
    json_str = json_lib.dumps(data, ensure_ascii=False)
    return f"data: {json_str}\n\n"


def stream_chat_response(chat_history: List[dict], model: str = "gpt-5"):
    """
    流式返回聊天响应，使用 Server-Sent Events
    支持对话历史，保持上下文连贯性
    
    Args:
        chat_history: 对话历史列表，格式为 [{"role": "user", "content": "..."}, ...]
        model: 模型名称
    """
    try:
        # 发送开始日志
        yield send_sse_event({
            "type": "log",
            "content": "🚀 开始处理你的问题..."
        })
        
        # 获取认证 token
        token = os.getenv("AI_BUILDER_TOKEN")
        if not token:
            yield send_sse_event({
                "type": "error",
                "message": "AI_BUILDER_TOKEN 未配置"
            })
            return
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 定义 search 工具
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
        
        # 使用传入的对话历史
        messages = chat_history.copy()
        
        base_payload = {
            "model": model,
            "messages": messages,
            "temperature": 1.0 if model == "gpt-5" else 0.7,
            "tools": [search_tool]
        }
        
        max_tool_rounds = 3
        tool_round = 0
        
        while tool_round <= max_tool_rounds:
            # 发送日志：正在经过 LLM
            if tool_round == 0:
                yield send_sse_event({
                    "type": "log",
                    "content": "🧠 正在经过 LLM 分析问题..."
                })
            else:
                yield send_sse_event({
                    "type": "log",
                    "content": f"🧠 正在经过 LLM 处理（第 {tool_round + 1} 轮）..."
                })
            
            # 发送请求
            response = requests.post(
                AI_BUILDER_CHAT_ENDPOINT,
                headers=headers,
                json=base_payload,
                timeout=120
            )
            
            response.raise_for_status()
            data = response.json()
            
            if "choices" not in data or len(data["choices"]) == 0:
                yield send_sse_event({
                    "type": "error",
                    "message": "AI Builder Space 返回了无效的响应格式"
                })
                return
            
            choice = data["choices"][0]
            message_obj = choice["message"]
            finish_reason = choice.get("finish_reason")
            tool_calls = message_obj.get("tool_calls")
            
            has_tool_calls = tool_calls and len(tool_calls) > 0
            
            # 如果达到最大轮数，强制生成最终答案
            if tool_round >= max_tool_rounds:
                yield send_sse_event({
                    "type": "log",
                    "content": "⚠️ 已达到最大工具调用轮数，正在生成最终答案..."
                })
                
                final_payload = {
                    **base_payload,
                    "messages": messages,
                    "tool_choice": "none"
                }
                final_payload.pop("tools", None)
                
                final_response = requests.post(
                    AI_BUILDER_CHAT_ENDPOINT,
                    headers=headers,
                    json=final_payload,
                    timeout=120
                )
                
                final_response.raise_for_status()
                final_data = final_response.json()
                
                if "choices" in final_data and len(final_data["choices"]) > 0:
                    final_message = final_data["choices"][0]["message"]
                    final_content = final_message.get("content", "")
                    
                    # 发送最终内容
                    yield send_sse_event({
                        "type": "complete",
                        "content": final_content
                    })
                    return
                else:
                    yield send_sse_event({
                        "type": "error",
                        "message": "生成最终答案失败"
                    })
                    return
            
            # 如果有工具调用
            if has_tool_calls:
                tool_round += 1
                
                yield send_sse_event({
                    "type": "log",
                    "content": f"🔧 正在调用第 {tool_round} 轮工具（共 {len(tool_calls)} 个工具）..."
                })
                
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                })
                
                # 并行执行工具调用
                tool_results = {}
                with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
                    futures = {
                        executor.submit(_execute_single_tool_call, tool_call): tool_call 
                        for tool_call in tool_calls
                    }
                    
                    for i, future in enumerate(as_completed(futures), 1):
                        tool_call = futures[future]
                        function_args = json_lib.loads(tool_call["function"]["arguments"])
                        keyword = function_args.get("keyword", "")
                        
                        yield send_sse_event({
                            "type": "log",
                            "content": f"🔍 正在搜索: {keyword}"
                        })
                        
                        tool_call_id, search_content = future.result()
                        tool_results[tool_call_id] = search_content
                        
                        yield send_sse_event({
                            "type": "log",
                            "content": f"✅ 搜索完成 ({i}/{len(tool_calls)})"
                        })
                
                # 添加工具结果
                for tool_call in tool_calls:
                    tool_call_id = tool_call["id"]
                    search_content = tool_results.get(tool_call_id, "工具调用失败")
                    
                    messages.append({
                        "role": "tool",
                        "content": search_content,
                        "tool_call_id": tool_call_id
                    })
                
                base_payload["messages"] = messages
                
            else:
                # 没有工具调用，直接返回回复
                message_content = message_obj.get("content", "")
                
                yield send_sse_event({
                    "type": "complete",
                    "content": message_content
                })
                return
                
    except Exception as e:
        logger.error(f"流式响应错误: {str(e)}")
        yield send_sse_event({
            "type": "error",
            "message": f"处理请求时发生错误: {str(e)}"
        })


class ChatStreamRequest(BaseModel):
    """流式聊天请求模型"""
    history: List[dict]  # 使用 dict 以支持灵活的消息格式
    model: Optional[str] = "gpt-5"


@app.post("/api/chat/stream")
def chat_stream(request: ChatStreamRequest):
    """
    流式聊天接口，使用 Server-Sent Events
    支持对话历史，保持上下文连贯性
    """
    try:
        # 使用请求中的历史（已经是 dict 格式）
        chat_history = request.history
        
        # 验证历史格式
        if not isinstance(chat_history, list):
            raise ValueError("对话历史必须是数组格式")
        
        # 验证每条消息格式
        for i, msg in enumerate(chat_history):
            if not isinstance(msg, dict):
                raise ValueError(f"对话历史第 {i+1} 条消息格式错误，必须是对象格式")
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"对话历史第 {i+1} 条消息缺少 role 或 content 字段")
        
        # 确保最后一条是用户消息
        if not chat_history or chat_history[-1].get("role") != "user":
            raise ValueError("对话历史必须以用户消息结尾")
        
        logger.info(f"收到流式请求，对话历史长度: {len(chat_history)}")
        
    except ValueError as e:
        logger.error(f"请求验证失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")
    
    return StreamingResponse(
        stream_chat_response(chat_history, request.model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Search 相关的模型定义
class SearchRequest(BaseModel):
    """Search 请求模型"""
    keyword: str
    max_results: Optional[int] = 6
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "人工智能",
                "max_results": 6
            }
        }


class SearchResponse(BaseModel):
    """Search 响应模型"""
    keyword: str
    results: List[dict]
    combined_answer: Optional[str] = None
    errors: Optional[List[dict]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "keyword": "人工智能",
                "results": [
                    {
                        "title": "AI 相关文章",
                        "url": "https://example.com",
                        "content": "文章内容..."
                    }
                ],
                "combined_answer": "综合答案..."
            }
        }


@app.post(
    "/search",
    summary="Search 搜索接口",
    description="接收关键字并转发到 AI Builder Space 的搜索 API，返回网络搜索结果。",
    response_description="返回搜索结果",
    responses={
        200: {
            "description": "成功响应",
            "content": {
                "application/json": {
                    "example": {
                        "keyword": "人工智能",
                        "results": [
                            {
                                "title": "AI 相关文章",
                                "url": "https://example.com",
                                "content": "文章内容..."
                            }
                        ],
                        "combined_answer": "综合答案..."
                    }
                }
            }
        },
        400: {
            "description": "请求错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "AI_BUILDER_TOKEN 未配置"
                    }
                }
            }
        },
        500: {
            "description": "服务器错误",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "转发请求失败: Connection error"
                    }
                }
            }
        }
    },
    tags=["搜索"]
)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Search 搜索接口，转发到 AI Builder Space
    
    Args:
        request: Search 请求对象，包含搜索关键字和最大结果数
        
    Returns:
        SearchResponse: 包含搜索结果的响应对象
        
    Raises:
        400: 当 AI_BUILDER_TOKEN 未配置时
        500: 当转发请求失败时
    """
    # 获取认证 token
    token = os.getenv("AI_BUILDER_TOKEN")
    if not token:
        raise HTTPException(
            status_code=400,
            detail="AI_BUILDER_TOKEN 未配置，请在 .env 文件中设置 AI_BUILDER_TOKEN"
        )
    
    # 构建请求到 AI Builder Space
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 限制 max_results 在有效范围内（1-20）
    max_results = max(1, min(20, request.max_results or 6))
    
    payload = {
        "keywords": [request.keyword],
        "max_results": max_results
    }
    
    try:
        # 转发请求到 AI Builder Space
        response = requests.post(
            AI_BUILDER_SEARCH_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # 检查响应状态
        response.raise_for_status()
        data = response.json()
        
        # 提取搜索结果
        if "queries" in data and len(data["queries"]) > 0:
            # 获取第一个查询的结果（因为我们只发送了一个关键字）
            query_result = data["queries"][0]
            
            # 提取搜索结果列表
            results = []
            if "response" in query_result and "results" in query_result["response"]:
                results = query_result["response"]["results"]
            
            return SearchResponse(
                keyword=request.keyword,
                results=results,
                combined_answer=data.get("combined_answer"),
                errors=data.get("errors")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="AI Builder Space 返回了无效的响应格式"
            )
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"转发请求失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理请求时发生错误: {str(e)}"
        )


# 对话历史相关的模型定义
class ChatHistoryItem(BaseModel):
    """对话历史项"""
    id: str
    title: str
    created_at: str
    updated_at: str

class ChatHistoryDetail(BaseModel):
    """对话历史详情"""
    id: str
    title: str
    history: List[dict]
    created_at: str
    updated_at: str

class CreateChatRequest(BaseModel):
    """创建对话请求"""
    title: Optional[str] = None
    first_message: Optional[str] = None

class UpdateChatTitleRequest(BaseModel):
    """更新对话标题请求"""
    title: str

class SaveChatRequest(BaseModel):
    """保存对话请求"""
    chat_id: Optional[str] = None
    history: List[dict]
    title: Optional[str] = None


@app.get("/api/chats", tags=["对话历史"])
async def get_chat_list():
    """获取对话列表"""
    try:
        index = load_chat_index()
        # 按更新时间倒序排列
        index.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return {"chats": index}
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话列表失败: {e}")


@app.get("/api/chats/{chat_id}", tags=["对话历史"])
async def get_chat_detail(chat_id: str):
    """获取对话详情"""
    try:
        chat_file = get_chat_file_path(chat_id)
        if not os.path.exists(chat_file):
            raise HTTPException(status_code=404, detail="对话不存在")
        
        with open(chat_file, 'r', encoding='utf-8') as f:
            chat_data = json_lib.load(f)
        
        return chat_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取对话详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取对话详情失败: {e}")


@app.post("/api/chats", tags=["对话历史"])
async def create_chat(request: CreateChatRequest):
    """创建新对话"""
    try:
        chat_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # 生成标题
        if request.title:
            title = request.title
        elif request.first_message:
            title = generate_title_from_message(request.first_message)
        else:
            title = "新对话"
        
        chat_data = {
            "id": chat_id,
            "title": title,
            "history": [],
            "created_at": now,
            "updated_at": now
        }
        
        # 保存对话文件
        chat_file = get_chat_file_path(chat_id)
        with open(chat_file, 'w', encoding='utf-8') as f:
            json_lib.dump(chat_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        index = load_chat_index()
        index.append({
            "id": chat_id,
            "title": title,
            "created_at": now,
            "updated_at": now
        })
        save_chat_index(index)
        
        return chat_data
    except Exception as e:
        logger.error(f"创建对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建对话失败: {e}")


@app.put("/api/chats/{chat_id}/title", tags=["对话历史"])
async def update_chat_title(chat_id: str, request: UpdateChatTitleRequest):
    """更新对话标题"""
    try:
        chat_file = get_chat_file_path(chat_id)
        if not os.path.exists(chat_file):
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 更新对话文件
        with open(chat_file, 'r', encoding='utf-8') as f:
            chat_data = json_lib.load(f)
        
        chat_data["title"] = request.title
        chat_data["updated_at"] = datetime.now().isoformat()
        
        with open(chat_file, 'w', encoding='utf-8') as f:
            json_lib.dump(chat_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        index = load_chat_index()
        for item in index:
            if item["id"] == chat_id:
                item["title"] = request.title
                item["updated_at"] = chat_data["updated_at"]
                break
        save_chat_index(index)
        
        return {"success": True, "title": request.title}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新对话标题失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新对话标题失败: {e}")


@app.post("/api/chats/{chat_id}/save", tags=["对话历史"])
async def save_chat(chat_id: str, request: SaveChatRequest):
    """保存对话历史"""
    try:
        chat_file = get_chat_file_path(chat_id)
        now = datetime.now().isoformat()
        
        # 读取或创建对话数据
        if os.path.exists(chat_file):
            with open(chat_file, 'r', encoding='utf-8') as f:
                chat_data = json_lib.load(f)
        else:
            # 创建新对话
            chat_data = {
                "id": chat_id,
                "title": request.title or "新对话",
                "history": [],
                "created_at": now,
                "updated_at": now
            }
            # 添加到索引
            index = load_chat_index()
            index.append({
                "id": chat_id,
                "title": chat_data["title"],
                "created_at": now,
                "updated_at": now
            })
            save_chat_index(index)
        
        # 更新对话数据
        chat_data["history"] = request.history
        chat_data["updated_at"] = now
        
        # 如果没有标题且有历史记录，生成标题
        if not chat_data.get("title") or chat_data["title"] == "新对话":
            if request.history and len(request.history) > 0:
                first_user_message = None
                for msg in request.history:
                    if msg.get("role") == "user":
                        first_user_message = msg.get("content", "")
                        break
                if first_user_message:
                    chat_data["title"] = generate_title_from_message(first_user_message)
        
        # 保存对话文件
        with open(chat_file, 'w', encoding='utf-8') as f:
            json_lib.dump(chat_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引
        index = load_chat_index()
        for item in index:
            if item["id"] == chat_id:
                item["title"] = chat_data["title"]
                item["updated_at"] = now
                break
        save_chat_index(index)
        
        return {"success": True, "chat_id": chat_id, "title": chat_data["title"]}
    except Exception as e:
        logger.error(f"保存对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"保存对话失败: {e}")


@app.delete("/api/chats/{chat_id}", tags=["对话历史"])
async def delete_chat(chat_id: str):
    """删除对话"""
    try:
        chat_file = get_chat_file_path(chat_id)
        if os.path.exists(chat_file):
            os.remove(chat_file)
        
        # 从索引中删除
        index = load_chat_index()
        index = [item for item in index if item["id"] != chat_id]
        save_chat_index(index)
        
        return {"success": True}
    except Exception as e:
        logger.error(f"删除对话失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除对话失败: {e}")
