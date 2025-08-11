# 移动端API设计方案

## 🎯 设计目标

为Android移动应用和语音查询系统提供专门优化的API接口，支持：
- 移动端专用的简化数据结构
- 长期Token认证机制
- 语音查询自然语言处理
- 离线缓存友好的数据格式

## 📱 移动端API设计

### 1. 移动端专用路由 `/api/v1/mobile/`

#### 1.1 认证相关
```
POST /api/v1/mobile/auth/login
- 支持长期Token（30天有效期）
- 返回用户基础信息和权限
- 支持设备标识绑定

POST /api/v1/mobile/auth/refresh
- Token自动续期
- 无感知认证更新

GET /api/v1/mobile/auth/profile
- 获取用户简化信息
```

#### 1.2 文档相关
```
GET /api/v1/mobile/documents/
- 分页加载优化
- 预缩略图支持
- 离线缓存标记

GET /api/v1/mobile/documents/{id}
- 简化文档详情
- 移动端适配的内容格式

POST /api/v1/mobile/documents/search
- 移动端搜索优化
- 支持语音搜索参数
- 返回高亮摘要
```

#### 1.3 资产相关
```
GET /api/v1/mobile/assets/
- 资产列表简化版本
- 支持快速筛选
- 状态图标映射

GET /api/v1/mobile/assets/{id}  
- 资产详情移动端适配
- 关键信息优先显示

POST /api/v1/mobile/assets/search
- 资产智能搜索
- 支持条件组合查询
```

### 2. 系统信息接口

```
GET /api/v1/system/info
- 服务器基本信息
- API版本信息
- 支持的功能列表
- 移动端配置参数
```

## 🎤 语音查询API设计

### 1. 语音查询路由 `/api/v1/voice/`

#### 1.1 统一查询接口
```
POST /api/v1/voice/query
{
    "text": "查找最近的服务器维护文档",
    "source": "voice|text",  
    "user_context": {
        "recent_searches": [...],
        "preferences": {...}
    }
}

响应格式：
{
    "success": true,
    "query_type": "document_search",
    "parsed_intent": {
        "action": "search",
        "target": "documents", 
        "filters": {
            "category": "maintenance",
            "asset_type": "server",
            "time_range": "recent"
        }
    },
    "results": {
        "documents": [...],
        "assets": [...],
        "total_count": 15
    },
    "voice_response": "找到15个相关的服务器维护文档，最新的是..."
}
```

#### 1.2 查询解析测试
```
POST /api/v1/voice/parse
- 测试自然语言解析
- 返回解析后的查询参数
- 用于调试和优化
```

#### 1.3 智能建议
```
GET /api/v1/voice/suggest
- 基于历史查询的建议
- 常用查询模板
- 语音输入提示
```

## 🔧 技术实现方案

### 1. 数据结构优化

#### 移动端文档对象
```python
class MobileDocument(BaseModel):
    id: int
    title: str
    summary: str  # 自动生成摘要
    file_type: str
    file_size: str  # 格式化大小 "1.2MB"
    created_at: str  # ISO格式
    category: str
    tags: List[str]
    preview_available: bool
    cached: bool  # 是否已缓存
```

#### 移动端资产对象
```python
class MobileAsset(BaseModel):
    id: int
    name: str
    type: str
    status: str
    status_icon: str  # 状态图标映射
    location: str
    last_check: str
    health_score: int  # 0-100健康评分
    priority: str  # high|medium|low
```

### 2. 自然语言处理模块

#### 查询意图识别
```python
class QueryParser:
    def parse_query(self, text: str) -> QueryIntent:
        """
        解析自然语言查询
        支持的查询类型：
        - 文档搜索："查找xxx文档"
        - 资产查询："显示所有服务器状态"
        - 混合查询："服务器相关的维护文档"
        """
        pass
        
    def extract_filters(self, text: str) -> Dict:
        """
        提取查询过滤条件
        - 时间范围：最近、今天、本月等
        - 类型过滤：服务器、网络设备等
        - 状态筛选：在用、维护中等
        """
        pass
```

### 3. Token管理优化

#### 长期Token策略
```python
# JWT配置更新
MOBILE_TOKEN_EXPIRE_DAYS = 30  # 移动端30天
WEB_TOKEN_EXPIRE_HOURS = 24    # Web端24小时

class TokenManager:
    def create_mobile_token(self, user_id: int, device_id: str) -> str:
        """创建移动端长期Token"""
        
    def refresh_token(self, old_token: str) -> str:  
        """Token自动续期"""
        
    def validate_device(self, token: str, device_id: str) -> bool:
        """验证设备绑定"""
```

## 📊 API响应格式标准化

### 统一响应结构
```json
{
    "success": true,
    "code": 200,
    "message": "请求成功",
    "data": { ... },
    "pagination": {
        "page": 1,
        "size": 20,
        "total": 100
    },
    "meta": {
        "cached": false,
        "response_time": "120ms",
        "api_version": "v1.1"
    }
}
```

### 错误响应格式
```json
{
    "success": false,
    "code": 400,
    "message": "参数错误", 
    "error_detail": "查询参数不能为空",
    "error_code": "INVALID_PARAMS",
    "suggestions": ["请提供搜索关键词", "检查参数格式"]
}
```

## 🚀 实施优先级

### Phase 1: 基础API (本周)
1. 创建移动端路由结构
2. 实现基础认证API
3. 添加系统信息接口
4. 优化CORS配置

### Phase 2: 核心功能 (下周)  
1. 实现文档和资产移动端API
2. 添加搜索功能优化
3. 实现Token管理优化

### Phase 3: 语音查询 (第3周)
1. 创建语音查询API结构
2. 实现自然语言解析
3. 集成统一搜索引擎

### Phase 4: 优化完善 (第4周)
1. 性能优化和缓存
2. 错误处理完善
3. API文档和测试

这个设计方案将为移动端应用和语音查询提供强大而灵活的API支持！