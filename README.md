# FastAPI Hello 接口

一个简单的 FastAPI 应用，提供 Hello 接口。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
uvicorn main:app --reload
```

应用将在 `http://127.0.0.1:8000` 启动。

## API 文档

启动应用后，可以访问：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 使用示例

### GET 请求

```bash
curl http://127.0.0.1:8000/hello/World
```

响应：
```json
{
  "message": "Hello World"
}
```
