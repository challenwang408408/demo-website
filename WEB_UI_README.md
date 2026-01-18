# Web UI 使用说明

## 功能特性

### 1. 思考过程可视化
- 用户提问后，显示"正在思考中"的动画
- 实时展示 AI 的思考过程

### 2. 结构化日志展示
实时展示以下信息：
- 🧠 正在经过 LLM 分析问题
- 🔧 正在调用第 X 轮工具
- 🔍 正在搜索关键词
- ✅ 搜索完成
- ⚠️ 达到最大工具调用轮数

### 3. Markdown 渲染
- 自动渲染返回的 Markdown 格式内容
- 支持标题、列表、代码块、表格等格式

## 使用方法

1. **启动服务器**：
   ```bash
   uvicorn main:app --reload
   ```

2. **访问 Web 界面**：
   打开浏览器访问：`http://127.0.0.1:8000`

3. **使用界面**：
   - 在输入框中输入问题
   - 按 Enter 或点击发送按钮
   - 实时查看思考过程和日志
   - 查看最终答案（支持 Markdown 渲染）

## API 端点

### 流式聊天接口
- **URL**: `/api/chat/stream`
- **方法**: GET
- **参数**:
  - `message`: 用户消息（必需）
  - `model`: 模型名称（默认: gpt-5）
- **响应**: Server-Sent Events (SSE) 流式响应

### 响应格式

```json
{
  "type": "log",           // 日志类型
  "content": "🧠 正在经过 LLM..."  // 日志内容
}

{
  "type": "complete",      // 完成类型
  "content": "最终答案..."  // 最终答案内容
}

{
  "type": "error",         // 错误类型
  "message": "错误信息"     // 错误消息
}
```

## 文件结构

```
phase A-fastapi/
├── static/
│   ├── index.html      # 前端页面
│   ├── style.css       # 样式文件
│   └── script.js       # JavaScript 逻辑
├── main.py            # FastAPI 后端
└── logs/              # 日志文件目录
```

## 注意事项

1. 确保服务器正在运行
2. 确保已配置 `AI_BUILDER_TOKEN` 环境变量
3. 浏览器需要支持 Server-Sent Events (SSE)
4. 日志文件保存在 `logs/` 目录下
