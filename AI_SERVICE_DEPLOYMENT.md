# AI服务架构部署总结

## ✅ 已完成的工作

### 1. 创建AI服务核心架构

```
backend/app/services/ai/
├── __init__.py
├── ai_config.py                  # 支持5个AI提供商的配置管理
├── ai_service.py                 # 统一的AI服务入口
├── providers/                      # AI提供商适配器
│   ├── __init__.py
│   ├── base_provider.py          # 基础接口
│   ├── openai_provider.py        # OpenAI适配器
│   ├── anthropic_provider.py     # Anthropic适配器
│   ├── alibaba_provider.py      # 阿里云通义适配器
│   ├── zhipu_provider.py        # 智谱AI适配器
│   └── minimax_provider.py       # MiniMax适配器 ⭐
├── extractors/                     # AI提取器
│   ├── __init__.py
│   ├── asset_extractor.py       # 资产信息提取
│   └── document_analyzer.py   # 文档分析器
└── utils/                          # 工具类
    ├── __init__.py
    ├── rate_limiter.py        # 限流器
    ├── cache_manager.py       # 缓存管理器
    └── cost_tracker.py         # 成本追踪器
```

### 2. 修改现有API端点

#### 资产提取端点 (`backend/app/api/endpoints/assets.py`)

**修改的端点：**
- `POST /api/v1/assets/file-extract` - 新增 `use_ai` 和 `ai_provider` 参数
- `POST /api/v1/assets/file-extract/single-confirm` - 新增单条确认端点

**新增的端点：**
- `GET /api/v1/assets/ai/providers` - 获取可用的AI提供商列表
- `GET /api/v1/assets/ai/stats` - 获取AI使用统计

#### 核心功能：**
- ✅ 支持AI模式和传统模式切换
- ✅ 自动检测设备名称冲突
- ✅ 支持逐条确认（新建或更新）
- ✅ AI失败时自动降级到传统方法

### 3. 新增文档分析端点 (`backend/app/api/endpoints/documents.py`)

**新增的端点：**
- `POST /api/v1/documents/{document_id}/analyze` - AI文档分析
  - analysis_type: full | summary | keywords | classification
- `GET /api/v1/documents/ai/providers` - 获取AI提供商列表
- `GET /api/v1/documents/ai/stats` - 获取AI使用统计

**支持的分析类型：**
- **full**: 完整分析（摘要、关键词、标签、重要要点、相关主题）
- **summary**: 仅提取摘要（100-150字）
- **keywords**: 提取关键词（5-8个）
- **classification**: 文档分类（运维文档、技术文档等）

### 4. 配置文件更新

#### 修改的文件：
1. `backend/requirements-windows.txt` - 添加了 `httpx>=0.24.0` 和 `jieba>=0.42.1`

2. `backend/.env.template` - 新增AI服务配置部分

### 5. 支持的AI提供商

| 提供商 | 模型 | 特点 | 输入价格 | 输出价格 |
|---------|------|----------|----------|------------|
| OpenAI | gpt-4o-mini | 性价比高，响应快 | $0.00015/K | $0.0006/K |
| Anthropic | claude-3-haiku | 快速，便宜 | $0.00025/K | $0.00125/K |
| 阿里云 | qwen-plus | 中文优化 | $0.0002/K | $0.0006/K |
| 智谱AI | glm-4-flash | 国产，便宜 | $0.00015/K | $0.0006/K |
| MiniMax | abab5.5-chat | 最便宜 | $0.00002/K | $0.00002/K |

## 🚀 部署步骤

### 1. 安装依赖

```bash
cd backend
pip install -r requirements-windows.txt
```

### 2. 配置环境变量

复制 `.env.template` 为 `.env` 并配置至少一个AI提供商：

#### 最简配置（使用OpenAI）
```env
AI_DEFAULT_PROVIDER=openai
AI_OPENAI_API_KEY=your_openai_api_key_here
AI_OPENAI_MODEL=gpt-4o-mini
AI_OPENAI_MAX_TOKENS=2000
AI_OPENAI_TEMPERATURE=0.3
```

#### 使用智谱AI（推荐）
```env
AI_DEFAULT_PROVIDER=zhipu
AI_ZHIPU_API_KEY=your_zhipu_api_key_here
AI_ZHIPU_MODEL=glm-4-flash
```

#### 使用MiniMax（最便宜）
```env
AI_DEFAULT_PROVIDER=minimax
AI_MINIMAX_API_KEY=your_minimax_api_key_here
AI_MINIMAX_MODEL=abab5.5-chat
AI_MINIMAX_GROUP_ID=your_group_id
```

### 3. 测试AI连接

启动服务后，测试AI连接：

```bash
# 测试资产提取
curl -X POST "http://localhost:8002/api/v1/assets/file-extract" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@设备清单.xlsx" \
  -F "use_ai=true" \
  -F "provider=openai"
```

### 4. 启动服务

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## 🎯 API使用示例

### 资产提取

#### 使用AI提取资产
```bash
curl -X POST "http://localhost:8002/api/v1/assets/file-extract" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@设备清单.xlsx" \
  -F "use_ai=true" \
  -F "provider=openai" \
  -F "auto_merge=false" \
  -F "merge_threshold=80"
```

#### 逐条确认资产
```bash
curl -X POST "http://localhost:8002/api/v1/assets/file-extract/single-confirm" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "服务器1",
    "asset_type": "server",
    "ip_address": "192.168.1.1",
    "hostname": "server1",
    "network_location": "office",
    "status": "active"
  }'
```

### 文档分析

#### AI完整分析
```bash
curl -X POST "http://localhost:8002/api/v1/documents/1/analyze" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "analysis_type=full" \
  -F "use_ai=true" \
  -F "provider=openai"
```

#### 仅提取摘要
```bash
curl -X POST "http://localhost:8002/api/v1/documents/1/analyze" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "analysis_type=summary" \
  -F "use_ai=true" \
  -F "provider=openai"
```

### 查看AI提供商列表

```bash
curl -X GET "http://localhost:8002/api/v1/assets/ai/providers" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 查看AI使用统计

```bash
curl -X GET "http://localhost:8002/api/v1/assets/ai/stats" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 📊 成本控制

### 配置建议

1. **开发/测试阶段**：
   - 使用便宜的模型：`gpt-4o-mini` 或 `glm-4-flash`
   - 启用缓存：`AI_CACHE_STRATEGY=memory`
   - 设置合理的限流：`AI_RATE_LIMIT_PER_USER=5`

2. **生产环境**：
   - 根据需求选择模型
   - 启用成本限制：`AI_COST_LIMIT_ENABLED=true`
   - 设置每日预算：`AI_COST_LIMIT_DAILY=10.0`
   - 考虑使用多个提供商分担负载

3. **成本优化**：
   - 启用缓存避免重复请求
   - 使用合适的 `max_tokens` 参数
   - 优先使用国产模型（智谱、MiniMax）

## 🔧 故障排除

### AI连接失败
1. 检查API密钥是否正确
2. 检查网络连接是否正常
3. 查看服务器日志获取详细错误信息
4. 尝试切换到其他提供商

### 提取结果不理想
1. 启用降级：`AI_FALLBACK_TO_TRADITIONAL=true`
2. 调整 `AI_TEMPERATURE`（0.0-0.7，越高越随机）
3. 检查文档内容是否包含足够的信息
4. 提供更清晰的Prompt说明

### 前端集成建议

#### 资产管理页面
- 添加AI模式开关
- 添加AI提供商选择器
- 实现逐条确认的UI流程
- 显示AI提取进度和结果

#### 文档管理页面
- 添加"AI分析"按钮
- 显示分析结果（摘要、关键词、分类）
- 支持查看AI使用统计

## 🎉 下一步

### 基础功能（已完成）
- ✅ AI服务架构
- ✅ 5个AI提供商支持
- ✅ 资产提取（AI + 传统）
- ✅ 文档分析功能
- ✅ 限流、缓存、成本追踪
- ✅ API端点集成

### 前端集成（待进行）
- [ ] 添加AI模式选择到资产提取页面
- [ ] 实现逐条确认的弹窗流程
- [ ] 添加AI分析按钮到文档管理页面
- [ ] 实现分析结果展示UI

### 高级功能（可选）
- [ ] 实现AI提供商配置页面
- [ ] 添加AI使用统计仪表板
- [ ] 支持自定义Prompt模板
- [ ] 实现批量AI处理队列
- [ ] 添加AI使用成本告警

---

**部署检查清单：**

- [ ] 在 `.env` 中配置AI API密钥
- [ ] 确认已安装所有依赖
- [ ] 测试AI连接是否正常
- [ ] 启动后端服务
- [ ] 测试AI提取功能
- [ ] 测试文档分析功能
- [ ] 查看API响应是否正常
- [ ] 检查成本追踪是否工作
- [ ] 验证缓存是否生效
- [ ] 测试降级机制

**注意事项：**

1. ⚠️ API密钥不要提交到代码库
2. ⚠️ 生产环境务必配置成本限制
3. ⚠️ 定期检查AI使用量，避免超支
4. ⚠️ 测试环境建议使用便宜模型
5. ⚠️ 重要信息请使用HTTPS加密传输

---

**技术栈：**
- 后端：Python 3.10+ / FastAPI
- AI服务：支持5个提供商
- 前端：Vue.js + Naive UI
- AI能力：智能资产提取 + 文档分析
- 降级：传统规则提取

**开始使用AI服务：**
1. 配置 `.env` 文件中的AI API密钥
2. 重启后端服务
3. 在前端选择AI模式提取或分析
4. 享受智能化带来的效率提升！