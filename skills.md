# AI Builder 平台部署技能文档

## 概述

本文档记录了在 AI Builder 平台（ai-builders.space）部署 FastAPI 应用的经验、教训和最佳实践。适用于通过 Cursor AI 助手进行项目部署的场景。

## 关键经验教训

### 1. Dockerfile 是必需的（关键！）

**问题**：第一次部署失败，因为只有 `Procfile` 而没有 `Dockerfile`。

**教训**：AI Builder 部署系统**必须**使用 Dockerfile 来构建和运行应用。仅有 Procfile 是不够的。

**解决方案**：每个项目必须在根目录包含一个正确配置的 Dockerfile。

### 2. 自动部署可能不会触发

**问题**：即使代码已推送到 GitHub，自动部署可能不会立即触发或可能失败。

**教训**：不要完全依赖自动部署。如果等待一段时间后仍未更新，应该手动触发部署。

**解决方案**：使用部署 API 手动触发部署，确保使用最新代码。

### 3. 使用现有的 AI_BUILDER_TOKEN

**问题**：最初误以为需要单独的部署 API Key。

**教训**：根据官方文档，学生使用现有的平台 API Key（`AI_BUILDER_TOKEN`），不需要单独的部署 API Key。

**解决方案**：直接使用 `AI_BUILDER_TOKEN` 调用部署 API。

## 部署前检查清单

在部署之前，确保以下所有项目都已准备就绪：

- [ ] **Dockerfile 存在**：项目根目录必须有 Dockerfile
- [ ] **Dockerfile 配置正确**：
  - [ ] 使用 shell form (`sh -c`) 来扩展 PORT 环境变量
  - [ ] CMD 指令使用 `${PORT:-8000}` 语法
  - [ ] 正确暴露端口（EXPOSE 8000）
- [ ] **代码已提交并推送**：所有更改必须已推送到 GitHub
- [ ] **仓库是公开的**：部署系统只能访问公开仓库
- [ ] **没有敏感信息**：确保 `.env`、API keys 等已添加到 `.gitignore`
- [ ] **单进程单端口**：FastAPI 应用必须在一个进程中服务所有内容（API + 静态文件）

## 标准 Dockerfile 模板（FastAPI）

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories (if needed)
RUN mkdir -p logs chat_history

# Expose port (PORT will be set at runtime by Koyeb)
EXPOSE 8000

# Start application using PORT environment variable
# Use shell form (sh -c) to ensure environment variable expansion
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

**关键点**：
- ✅ 使用 `sh -c` 确保环境变量正确扩展
- ✅ 使用 `${PORT:-8000}` 提供默认值
- ✅ 绑定到 `0.0.0.0` 而不是 `127.0.0.1`

## 部署流程

### 步骤 1：准备代码

```bash
# 1. 确保所有更改已提交
git add .
git commit -m "Prepare for deployment"

# 2. 推送到 GitHub
git push origin main
```

### 步骤 2：验证 Dockerfile

确保 Dockerfile 存在且配置正确（参考上面的模板）。

### 步骤 3：调用部署 API

**对于新服务**：
```bash
curl -X POST "https://space.ai-builders.com/backend/v1/deployments" \
  -H "Authorization: Bearer YOUR_AI_BUILDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "repo_url": "https://github.com/your-username/your-repo",
  "service_name": "your-service-name",
  "branch": "main",
  "port": 8000
}'
```

**对于更新现有服务**：
使用相同的 `service_name`，系统会自动更新现有服务：
```bash
curl -X POST "https://space.ai-builders.com/backend/v1/deployments" \
  -H "Authorization: Bearer YOUR_AI_BUILDER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
  "repo_url": "https://github.com/your-username/your-new-repo",
  "service_name": "existing-service-name",  # 使用现有服务名称
  "branch": "main",
  "port": 8000
}'
```

### 步骤 4：等待部署完成

- 部署通常需要 **5-10 分钟**
- 可以在部署门户查看状态
- 如果超过 20 分钟仍显示 "deploying"，联系导师

### 步骤 5：验证部署

访问部署的 URL：`https://your-service-name.ai-builders.space/`

## 服务管理

### 更新现有服务

**方法**：使用相同的 `service_name` 调用部署 API，系统会自动更新。

**优势**：
- 保留相同的 URL
- 不占用新的服务配额
- 简单快捷

### 删除服务

**限制**：无法自行删除服务。

**方法**：联系导师删除服务。

**何时需要**：
- 想要释放配额用于新项目
- 服务不再需要

### 服务配额

- **限制**：每人最多 2 个服务（默认）
- **检查方式**：通过部署门户或 API 查看
- **配额管理**：联系导师调整配额或删除服务

## 常见问题排查

### 问题 1：部署失败 - "Dockerfile not found"

**原因**：项目根目录缺少 Dockerfile。

**解决**：创建 Dockerfile（参考上面的模板）。

### 问题 2：部署后应用无法启动

**可能原因**：
- Dockerfile 的 CMD 指令使用了错误的格式
- 端口配置错误
- 应用代码硬编码了端口号

**解决**：
- 确保使用 `sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"`
- 确保应用代码从环境变量读取 PORT

### 问题 3：自动部署未触发

**原因**：Git push 后自动部署可能不会立即触发。

**解决**：手动调用部署 API。

### 问题 4：部署成功但页面显示旧内容

**可能原因**：
- 浏览器缓存
- 反向代理未更新

**解决**：
- 清除浏览器缓存
- 等待几分钟让反向代理更新
- 检查部署状态是否为 "healthy"

## 最佳实践

### 1. 代码管理

- ✅ 始终在部署前提交并推送所有更改
- ✅ 使用有意义的 commit 消息
- ✅ 确保 `.gitignore` 正确配置

### 2. Dockerfile 优化

- ✅ 使用多阶段构建（如果适用）减小镜像大小
- ✅ 使用 `--no-cache-dir` 安装依赖
- ✅ 创建必要的目录（如 logs、数据目录）

### 3. 环境变量

- ✅ `AI_BUILDER_TOKEN` 会自动注入，无需手动配置
- ✅ 从环境变量读取配置，不要硬编码
- ✅ 使用 `os.getenv("PORT", "8000")` 读取端口

### 4. 测试

- ✅ 本地测试 Dockerfile：`docker build -t test . && docker run -p 8000:8000 -e PORT=8000 test`
- ✅ 验证应用在指定端口正常启动
- ✅ 检查静态文件是否正确服务

### 5. 监控

- ✅ 部署后检查部署门户的状态
- ✅ 查看部署日志（如果有）
- ✅ 测试所有关键功能

## 部署脚本模板

创建一个可重用的部署脚本：

```bash
#!/bin/bash
# deploy.sh - 部署到 AI Builder 平台

# 配置
SERVICE_NAME="${1:-your-service-name}"
REPO_URL="${2:-https://github.com/your-username/your-repo}"
BRANCH="${3:-main}"
PORT="${4:-8000}"

# 从环境变量或 .env 文件读取 token
if [ -f .env ]; then
    export $(cat .env | grep AI_BUILDER_TOKEN | xargs)
fi

TOKEN="${AI_BUILDER_TOKEN:-your-token-here}"

echo "🚀 开始部署..."
echo "服务名称: $SERVICE_NAME"
echo "仓库: $REPO_URL"
echo "分支: $BRANCH"
echo "端口: $PORT"

curl -X POST "https://space.ai-builders.com/backend/v1/deployments" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
  \"repo_url\": \"$REPO_URL\",
  \"service_name\": \"$SERVICE_NAME\",
  \"branch\": \"$BRANCH\",
  \"port\": $PORT
}"

echo ""
echo "✅ 部署请求已发送，请等待 5-10 分钟"
echo "访问: https://$SERVICE_NAME.ai-builders.space/"
```

**使用方法**：
```bash
chmod +x deploy.sh
./deploy.sh service-name https://github.com/user/repo main 8000
```

## 参考资源

- 部署提示文档：https://www.ai-builders.com/resources/students/deployment-prompt.md
- OpenAPI 规范：https://www.ai-builders.com/resources/students-backend/openapi.json
- 部署门户：检查部署状态和管理服务

## 总结

**关键要点**：
1. ✅ **Dockerfile 是必需的** - 没有 Dockerfile 部署会失败
2. ✅ **手动触发部署更可靠** - 不要完全依赖自动部署
3. ✅ **使用现有服务名称更新** - 可以覆盖现有服务而不占用新配额
4. ✅ **等待 5-10 分钟** - 部署需要时间，请耐心等待
5. ✅ **验证部署** - 部署后检查应用是否正常工作

**快速检查清单**：
- [ ] Dockerfile 存在且配置正确
- [ ] 代码已推送到 GitHub
- [ ] 调用部署 API
- [ ] 等待 5-10 分钟
- [ ] 验证部署成功

---

**最后更新**：2026-01-18
**基于经验**：FastAPI 聊天应用部署到 AI Builder 平台
