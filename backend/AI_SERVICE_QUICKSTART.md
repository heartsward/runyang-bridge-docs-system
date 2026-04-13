# AI服务快速开始指南

## 1. 安装依赖

```bash
cd backend
pip install -r requirements-windows.txt
```

主要依赖：
- `httpx>=0.24.0` - AI服务HTTP客户端
- `jieba>=0.42.1` - 中文文本处理和关键词提取
- `pydantic>=2.0.0` - 配置管理
- `pydantic-settings>=2.0.0` - 环境变量加载

## 2. 配置AI API密钥

在 `backend` 目录下创建或编辑 `.env` 文件：

### 最简配置（使用OpenAI）
```env
# AI服务配置
AI_DEFAULT_PROVIDER=openai
AI_OPENAI_API_KEY=your_openai_api_key_here
AI_OPENAI_MODEL=gpt-4o-mini

# 限流配置
AI_RATE_LIMIT_ENABLED=true
AI_RATE_LIMIT_REQUESTS=10
AI_RATE_LIMIT_PER_USER=5

# 缓存配置
AI_CACHE_STRATEGY=memory
AI_CACHE_TTL=3600

# 降级配置
AI_FALLBACK_ENABLED=true
AI_FALLBACK_TO_TRADITIONAL=true
```

### 完整配置示例
```env
# ========== OpenAI配置 ==========
AI_DEFAULT_PROVIDER=openai
AI_OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AI_OPENAI_API_URL=https://api.openai.com/v1/chat/completions
AI_OPENAI_MODEL=gpt-4o-mini
AI_OPENAI_MAX_TOKENS=2000
AI_OPENAI_TEMPERATURE=0.3

# ========== Anthropic配置 ==========
AI_ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
AI_ANTHROPIC_API_URL=https://api.anthropic.com/v1/messages
AI_ANTHROPIC_MODEL=claude-3-haiku-20240307

# ========== 阿里云通义配置 ==========
AI_ALIBABA_API_KEY=sk-xxxxxxxxxxxxxxxx
AI_ALIBABA_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_ALIBABA_MODEL=qwen-plus

# ========== 智谱AI配置 ==========
AI_ZHIPU_API_KEY=xxxxxxxxxxxxxxxxxxxx
AI_ZHIPU_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
AI_ZHIPU_MODEL=glm-4-flash

# ========== MiniMax配置 ==========
AI_MINIMAX_API_KEY=xxxxxxxxxxxxxxxx
AI_MINIMAX_API_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
AI_MINIMAX_MODEL=abab5.5-chat
AI_MINIMAX_GROUP_ID=xxxxxxxx

# ========== 通用配置 ==========
AI_MAX_RETRIES=3
AI_TIMEOUT=30

# ========== 限流配置 ==========
AI_RATE_LIMIT_ENABLED=true
AI_RATE_LIMIT_REQUESTS=10
AI_RATE_LIMIT_PER_USER=5

# ========== 缓存配置 ==========
AI_CACHE_STRATEGY=memory
AI_CACHE_TTL=3600

# ========== 成本控制 ==========
AI_COST_LIMIT_ENABLED=false
AI_COST_LIMIT_DAILY=10.0

# ========== 降级配置 ==========
AI_FALLBACK_ENABLED=true
AI_FALLBACK_TO_TRADITIONAL=true
```

## 3. 测试AI连接

启动后端服务：
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

测试AI提取功能（使用curl或Postman）：
```bash
curl -X POST "http://localhost:8002/api/v1/assets/file-extract" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@设备清单.xlsx" \
  -F "use_ai=true" \
  -F "provider=openai"
```

## 4. 推荐的AI提供商配置

### 开发测试阶段
使用便宜快速的模型：
- OpenAI: `gpt-4o-mini` (便宜，快速)
- 智谱AI: `glm-4-flash` (国产，超便宜)
- MiniMax: `abab5.5-chat` (最便宜)

### 生产环境
根据需求选择：
- 追求质量: OpenAI `gpt-4o`
- 追求性价比: OpenAI `gpt-4o-mini`
- 中文优化: 阿里云 `qwen-plus` 或 智谱 `glm-4`
- 成本敏感: MiniMax `abab5.5-chat`

### 各提供商价格对比（2024年）

| 提供商 | 模型 | 输入价格 | 输出价格 | 10K token成本 |
|---------|------|----------|----------|------------|
| OpenAI | gpt-4o-mini | $0.00015/K | $0.0006/K | ~$0.0075 |
| OpenAI | gpt-4o | $0.005/K | $0.015/K | ~$0.20 |
| Anthropic | claude-3-haiku | $0.00025/K | $0.00125/K | ~$0.00375 |
| 阿里云 | qwen-plus | $0.0002/K | $0.0006/K | ~$0.008 |
| 智谱AI | glm-4-flash | $0.00015/K | $0.0006/K | ~$0.0075 |
| MiniMax | abab5.5-chat | $0.00002/K | $0.00002/K | ~$0.0004 |

## 5. 常见问题

### Q1: AI提取失败怎么办？
A: 系统会自动降级到传统提取方法。同时检查：
1. API密钥是否正确
2. 网络连接是否正常
3. 查看服务器日志

### Q2: 如何控制AI使用成本？
A: 在 `.env` 中设置：
```env
AI_COST_LIMIT_ENABLED=true
AI_COST_LIMIT_DAILY=10.0  # 每日10美元
```

### Q3: 提取结果不准确怎么办？
A: 尝试：
1. 调低 `AI_TEMPERATURE`（0.0-0.3，降低随机性）
2. 切换到更强大的模型（如 `gpt-4o`）
3. 提供更清晰、结构化的文档

### Q4: 如何切换AI提供商？
A: 修改 `.env` 中的 `AI_DEFAULT_PROVIDER`，或在代码中指定：
```python
await ai_service.chat(messages, provider="anthropic")
```

## 6. 性能优化建议

1. **启用缓存**: `AI_CACHE_STRATEGY=memory` 减少重复请求
2. **启用限流**: `AI_RATE_LIMIT_ENABLED=true` 防止滥用
3. **使用降级**: `AI_FALLBACK_TO_TRADITIONAL=true` 保证服务可用性
4. **合理设置**: `AI_MAX_TOKENS` 不要设置过高（通常2000足够）

## 7. 下一步

配置完成后，可以：
1. 测试资产提取功能
2. 测试文档分析功能
3. 集成到前端界面
4. 配置自动化的逐条确认流程

## 8. API端点

### 资产提取端点
- `POST /api/v1/assets/file-extract` - 从文件提取资产（支持AI模式）
- `POST /api/v1/assets/file-extract/single-confirm` - 逐条确认资产

### 文档分析端点（待添加）
- `POST /api/v1/documents/{document_id}/analyze` - AI分析文档
  - analysis_type: full | summary | keywords | classification

## 9. 监控和调试

查看AI使用统计：
```python
from app.services.ai.ai_service import ai_service

stats = ai_service.get_cost_stats()
print(stats)
```

日志输出：
- AI请求成功/失败
- 成本追踪
- 缓存命中/未命中
- 限流触发
- 降级触发

## 10. 安全建议

1. ✅ 永远在环境变量中设置API密钥，不要提交到代码库
2. ✅ 使用 `.gitignore` 排除 `.env` 文件
3. ✅ 为每个环境使用不同的API密钥
4. ✅ 定期轮换API密钥
5. ✅ 设置合理的成本限制
6. ✅ 监控异常使用情况

---

**开始使用AI服务之前，请确保：**
1. ✅ 已安装所有依赖
2. ✅ 已配置至少一个AI提供商的API密钥
3. ✅ 已启动后端服务
4. ✅ 已了解成本和计费方式
