# 部署说明

## 已完成的工作

✅ 网站开发完成
- 赛博朋克风格的中国历史朝代网站
- 包含完整的时间轴和重点朝代详情页
- 响应式设计，支持移动端

✅ 代码已推送到GitHub
- 仓库地址: https://github.com/challenwang408408/demo-website
- 分支: main
- 所有文件已成功推送

✅ 部署配置完成
- Dockerfile已配置，支持PORT环境变量
- Flask应用已配置为读取PORT环境变量
- requirements.txt已配置

## 部署方式

### 方式一：使用AI Builders平台（推荐）

1. 确保您有有效的 `AI_BUILDER_TOKEN` 环境变量
2. 运行部署脚本：
```bash
export AI_BUILDER_TOKEN="your_token_here"
python3 deploy.py
```

或者直接使用curl命令：
```bash
curl -X POST "https://www.ai-builders.com/resources/students-backend/v1/deployments" \
  -H "Authorization: Bearer $AI_BUILDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/challenwang408408/demo-website",
    "service_name": "chinese-history",
    "branch": "main",
    "port": 8000
  }'
```

部署成功后，您的网站将在以下地址可用：
- https://chinese-history.ai-builders.space

### 方式二：使用Docker本地部署

```bash
# 构建镜像
docker build -t chinese-history .

# 运行容器
docker run -p 8000:8000 -e PORT=8000 chinese-history
```

访问: http://localhost:8000

### 方式三：直接运行Flask应用

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
export PORT=8000
python app.py
```

访问: http://localhost:8000

## 部署信息

- **GitHub仓库**: https://github.com/challenwang408408/demo-website
- **服务名称**: chinese-history
- **分支**: main
- **端口**: 8000

## 注意事项

1. 部署通常需要5-10分钟完成
2. 确保GitHub仓库是公开的
3. 确保所有代码已提交并推送到GitHub
4. 部署后可以通过部署API查询状态

## 查询部署状态

```bash
curl -X GET "https://www.ai-builders.com/resources/students-backend/v1/deployments/chinese-history" \
  -H "Authorization: Bearer $AI_BUILDER_TOKEN"
```

