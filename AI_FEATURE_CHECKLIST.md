# AI服务功能清单

## 已完成的工作

### 🎯 核心功能
- ✅ AI服务架构（支持5个提供商）
- ✅ 资产提取器（AI + 传统降级）
- ✅ 文档分析器
- ✅ 限流器、缓存管理器、成本追踪器
- ✅ 统一的AI服务管理器
- ✅ 降级机制（AI失败时自动切换到传统方法）

### 📝 API端点

#### 资产管理
| 端点 | 功能 | 说明 |
|---------|------|----------|----|------|
| `/api/v1/assets/file-extract` | AI/传统提取 | 支持选择AI提供商 |
| `/api/v1/assets/file-extract/single-confirm` | 逐条确认 | 支持新建和编辑两种模式 |
| `/api/v1/assets/ai/providers` | 获取AI提供商列表 | 返回可用提供商和状态 |
| `/api/v1/assets/ai/stats` | AI使用统计 | 获取token使用量和成本 |

#### 文档管理
| 端点 | 功能 | 说明 |
|---------|------|----------|----|------|
| `/api/v1/documents/{id}/analyze` | AI文档分析 | 支持摘要、关键词、分类、完整分析 |

### 🔧 配置文件

#### 已修改的文件
1. `backend/app/services/ai/` - AI服务模块
2. `backend/app/api/endpoints/assets.py` - 资产提取API（已修改）
3. `backend/app/api/endpoints/documents.py` - 文档分析API（已添加）
4. `backend/requirements-windows.txt` - 已更新依赖
5. `backend/.env.template` - AI服务配置模板
6. `backend/AI_SERVICE_DEPLOYMENT.md` - 完整部署文档

### 🚀 支持的AI提供商

| 提供商 | 模型 | 特点 |
|---------|------|----------|----|------|
| OpenAI | gpt-4o-mini | 便宜、快速 |
| Anthropic | claude-3-haiku | 智能、快速 |
| 阿里云 | qwen-plus | 中文优化 |
| 智谱AI | glm-4-flash | 国产、超便宜 |
| MiniMax | abab5.5-chat | 最便宜 |

### 📊 API使用示例

#### 1. 资产提取（使用AI）
```bash
# 使用OpenAI提取
curl -X POST "http://localhost:8002/api/v1/assets/file-extract" \
  -F "file=@设备清单.xlsx" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "use_ai=true" \
  -F "ai_provider=openai"

# 使用MiniMax提取（最便宜）
curl -X POST "http://localhost:8002/api/v1/assets/file-extract" \
  -F "file=@设备清单.xlsx" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "use_ai=true" \
  -F "ai_provider=minimax"
```

#### 2. 查看AI提供商
```bash
curl -X GET "http://localhost:8002/api/v1/assets/ai/providers" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 3. 逐条确认资产
```bash
curl -X POST "http://localhost:8002/api/v1/assets/file-extract/single-confirm" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "服务器1",
    "asset_type": "server",
    "ip_address": "192.168.1.1",
    "hostname": "server1",
    "network_location": "office",
    "status": "active"
  }' \
  -F "is_duplicate=false"
```

#### 4. AI文档分析
```bash
# 完整分析
curl -X POST "http://localhost:8002/api/v1/documents/1/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "analysis_type=full" \
  -F "use_ai=true" \
  -F "ai_provider=openai"

# 仅提取摘要
curl -X POST "http://localhost:8002/api/v1/documents/1/analyze" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "analysis_type=summary" \
  -F "use_ai=true" \
  -F "ai_provider=openai"
```

#### 5. 查看AI使用统计
```bash
curl -X GET "http://localhost:8002/api/v1/assets/ai/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### ⚠️ 待集成到前端

1. 资产管理页面
   - 添加AI提取模式选择器
   - 实现逐条确认的弹窗流程
   - 显示AI提取进度

2. 文档管理页面
   - 添加"AI分析"按钮
   - 显示分析结果（摘要、关键词等）

3. 系统设置页面
   - 添加AI提供商配置
   - 显示AI使用统计
   - 支持切换提供商

### 🔧 配置要求

1. 必须配置至少一个AI提供商的API密钥
2. 推荐：使用OpenAI或MiniMax（最便宜）
3. 可以配置多个提供商用于负载均衡

### 📝 成本优化

- 开发/测试：使用便宜的模型（gpt-4o-mini, abab5.5-chat, glm-4-flash）
- 生产环境：可根据需求选择
- 启用缓存可以减少重复成本
- 设置合理的限流避免滥用

---

**状态：** ✅ AI服务架构已部署完成，可以开始集成到前端
