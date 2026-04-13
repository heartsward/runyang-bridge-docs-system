# AI服务模块

这是一个通用的AI服务架构，支持多个AI提供商，用于资产提取和文档分析。

## 功能特性

- ✅ **多提供商支持**: OpenAI, Anthropic, 阿里云通义, 智谱AI, MiniMax
- ✅ **智能降级**: AI失败时自动切换到传统提取方法
- ✅ **限流保护**: 全局限流和用户级别限流
- ✅ **缓存机制**: 内存缓存和Redis缓存支持
- ✅ **成本追踪**: 实时追踪AI使用成本
- ✅ **统一接口**: 所有提供商使用相同的API接口

## 配置说明

在 `.env` 文件中添加以下配置：

### 默认提供商
```env
AI_DEFAULT_PROVIDER=openai
```

可选值: `openai`, `anthropic`, `alibaba`, `zhipu`, `minimax`

### OpenAI配置
```env
AI_OPENAI_API_KEY=your_openai_api_key_here
AI_OPENAI_API_URL=https://api.openai.com/v1/chat/completions
AI_OPENAI_MODEL=gpt-4o-mini
AI_OPENAI_MAX_TOKENS=2000
AI_OPENAI_TEMPERATURE=0.3
```

### Anthropic配置
```env
AI_ANTHROPIC_API_KEY=your_anthropic_api_key_here
AI_ANTHROPIC_API_URL=https://api.anthropic.com/v1/messages
AI_ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### 阿里云通义配置
```env
AI_ALIBABA_API_KEY=your_alibaba_api_key_here
AI_ALIBABA_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
AI_ALIBABA_MODEL=qwen-plus
```

### 智谱AI配置
```env
AI_ZHIPU_API_KEY=your_zhipu_api_key_here
AI_ZHIPU_API_URL=https://open.bigmodel.cn/api/paas/v4/chat/completions
AI_ZHIPU_MODEL=glm-4-flash
```

### MiniMax配置
```env
AI_MINIMAX_API_KEY=your_minimax_api_key_here
AI_MINIMAX_API_URL=https://api.minimax.chat/v1/text/chatcompletion_v2
AI_MINIMAX_MODEL=abab5.5-chat
AI_MINIMAX_GROUP_ID=your_group_id
```

### 通用配置
```env
AI_MAX_RETRIES=3
AI_TIMEOUT=30

# 限流配置
AI_RATE_LIMIT_ENABLED=true
AI_RATE_LIMIT_REQUESTS=10
AI_RATE_LIMIT_PER_USER=5

# 缓存配置
AI_CACHE_STRATEGY=memory
AI_CACHE_TTL=3600

# 成本控制
AI_COST_LIMIT_ENABLED=false
AI_COST_LIMIT_DAILY=10.0

# 降级配置
AI_FALLBACK_ENABLED=true
AI_FALLBACK_TO_TRADITIONAL=true
```

## 使用方法

### 资产提取示例

```python
from app.services.ai.extractors.asset_extractor import AIAssetExtractor

extractor = AIAssetExtractor()

# 从文本提取资产
assets = await extractor.extract_from_text(text, provider="openai")

# 从文件提取资产
assets = await extractor.extract_from_file(
    file_path="设备清单.xlsx",
    file_content=file_bytes,
    file_type="xlsx",
    provider="openai"
)
```

### 文档分析示例

```python
from app.services.ai.extractors.document_analyzer import DocumentAnalyzer

analyzer = DocumentAnalyzer()

# 完整分析
result = await analyzer.analyze_document(
    title="运维手册",
    content="文档内容...",
    analysis_type="full"
)

# 仅提取摘要
result = await analyzer.analyze_document(
    title="运维手册",
    content="文档内容...",
    analysis_type="summary"
)
```

### AI服务统一接口

```python
from app.services.ai.ai_service import ai_service
from app.services.ai.providers.base_provider import AIMessage

messages = [
    AIMessage(role="user", content="你好，请帮我分析以下内容...")
]

response = await ai_service.chat(
    messages=messages,
    provider="openai",
    use_cache=True,
    user_id=123
)

print(response.content)
print(response.usage)
```

## API提供商对比

| 提供商 | 模型 | 输入价格 | 输出价格 | 特点 |
|---------|------|----------|----------|------|
| OpenAI | gpt-4o-mini | $0.00015/1K | $0.0006/1K | 性价比高，响应快 |
| OpenAI | gpt-4o | $0.005/1K | $0.015/1K | 最强性能 |
| Anthropic | claude-3-haiku | $0.00025/1K | $0.00125/1K | 快速，便宜 |
| 阿里云 | qwen-plus | $0.0002/1K | $0.0006/1K | 中文优化 |
| 智谱AI | glm-4-flash | $0.00015/1K | $0.0006/1K | 国产，便宜 |
| MiniMax | abab5.5-chat | $0.00002/1K | $0.00002/1K | 超便宜 |

## 部署检查清单

- [ ] 在 `.env` 文件中配置AI API密钥
- [ ] 确认 `httpx` 已安装（`pip install httpx`）
- [ ] 确认 `jieba` 已安装（`pip install jieba`，用于关键词提取）
- [ ] 测试AI连接是否正常
- [ ] 检查限流和缓存配置
- [ ] 验证成本追踪功能

## 故障排除

### AI连接失败
1. 检查API密钥是否正确
2. 确认网络连接正常
3. 查看服务器日志获取详细错误信息
4. 尝试切换到其他提供商

### 提取结果不理想
1. 启用 `AI_FALLBACK_TO_TRADITIONAL=true` 使用传统方法
2. 调整 `AI_TEMPERATURE` 参数（0.0-1.0，越高越随机）
3. 检查文档内容是否包含足够的信息

### 成本控制
- 设置 `AI_COST_LIMIT_ENABLED=true`
- 设置 `AI_COST_LIMIT_DAILY` 控制每日预算
- 定期查看 `ai_service.get_cost_stats()` 监控使用情况

## 成本优化建议

1. **优先使用便宜模型**: gpt-4o-mini、glm-4-flash
2. **启用缓存**: 相同请求使用缓存结果
3. **精确Prompt**: 明确说明输出格式，减少重复
4. **限制输出长度**: 设置合适的 `max_tokens` 值
5. **批量处理**: 将多个小请求合并为一个大请求

## 许可证

MIT License
