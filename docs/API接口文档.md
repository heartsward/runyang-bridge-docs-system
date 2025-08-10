# 润扬大桥运维文档管理系统 - API接口文档

## 📋 目录
- [接口概述](#接口概述)
- [认证鉴权](#认证鉴权)
- [用户管理](#用户管理)
- [文档管理](#文档管理)
- [搜索功能](#搜索功能)
- [资产管理](#资产管理)
- [数据分析](#数据分析)
- [任务管理](#任务管理)
- [错误码](#错误码)

## 🌐 接口概述

### 基础信息
- **基础URL**: `http://localhost:8002`
- **API版本**: `v1`
- **请求格式**: `JSON` / `multipart/form-data`
- **响应格式**: `JSON`
- **字符编码**: `UTF-8`

### 通用请求头
```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

### 通用响应格式
**成功响应**:
```json
{
  "data": {},
  "message": "操作成功"
}
```

**错误响应**:
```json
{
  "detail": "错误描述信息"
}
```

## 🔐 认证鉴权

### 用户登录
**接口**: `POST /api/v1/auth/login`

**请求参数**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应数据**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

**说明**: 
- Token有效期24小时
- 需在请求头中携带: `Authorization: Bearer <access_token>`

### 获取当前用户信息
**接口**: `GET /api/v1/auth/me`

**请求头**:
```http
Authorization: Bearer <access_token>
```

**响应数据**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@system.com",
  "full_name": "系统管理员",
  "department": "技术部",
  "position": "系统管理员",
  "phone": "13800138000",
  "is_active": true,
  "is_superuser": true
}
```

## 👥 用户管理

### 获取用户列表 (仅管理员)
**接口**: `GET /api/v1/settings/users`

**请求头**:
```http
Authorization: Bearer <admin_token>
```

**响应数据**:
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@system.com",
    "full_name": "系统管理员",
    "department": "技术部",
    "position": "系统管理员",
    "phone": "13800138000",
    "is_active": true,
    "is_superuser": true,
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

### 创建用户 (仅管理员)
**接口**: `POST /api/v1/settings/users`

**请求头**:
```http
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**请求参数**:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "新用户",
  "department": "技术部",
  "position": "工程师",
  "phone": "13800138001",
  "is_superuser": false
}
```

**响应数据**:
```json
{
  "id": 3,
  "username": "newuser",
  "email": "user@example.com",
  "full_name": "新用户",
  "department": "技术部",
  "position": "工程师",
  "phone": "13800138001",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2024-01-01T12:00:00Z"
}
```

### 更新用户 (仅管理员)
**接口**: `PUT /api/v1/settings/users/{user_id}`

**请求参数**:
```json
{
  "email": "newemail@example.com",
  "full_name": "更新的用户名",
  "department": "业务部",
  "position": "主管",
  "phone": "13800138002",
  "is_active": true,
  "is_superuser": false,
  "password": "newpassword123"
}
```

### 删除用户 (仅管理员)
**接口**: `DELETE /api/v1/settings/users/{user_id}`

**响应数据**:
```json
{
  "message": "用户 username 删除成功"
}
```

## 📚 文档管理

### 上传文档 (仅管理员)
**接口**: `POST /api/v1/upload`

**请求头**:
```http
Authorization: Bearer <admin_token>
Content-Type: multipart/form-data
```

**请求参数**:
```
file: <文件对象>
title: "文档标题"
description: "文档描述"
category_id: 1
tags: "标签1,标签2,标签3"
```

**文件类型限制**:
- 文档类: `.pdf`, `.doc`, `.docx`, `.txt`, `.md`
- 表格类: `.xls`, `.xlsx`, `.csv`
- 图片类: `.jpg`, `.jpeg`, `.png`
- 文件大小: 最大10MB

**响应数据**:
```json
{
  "id": 1,
  "title": "文档标题",
  "description": "文档描述",
  "file_name": "document.pdf",
  "file_size": 1048576,
  "file_type": "pdf",
  "tags": ["标签1", "标签2", "标签3"],
  "status": "published",
  "content_extracted": null,
  "ai_summary": null,
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": null,
  "owner": {
    "username": "admin",
    "full_name": "系统管理员"
  }
}
```

### 检查文件名是否存在
**接口**: `GET /api/v1/documents/check-filename`

**请求参数**:
```
filename: "document.pdf"
```

**响应数据**:
```json
{
  "exists": false,
  "count": 0,
  "existing_documents": []
}
```

### 获取文档列表
**接口**: `GET /api/v1/documents`

**请求参数**:
```
skip: 0          # 跳过记录数
limit: 100       # 返回记录数限制
```

**响应数据**:
```json
{
  "items": [
    {
      "id": 1,
      "title": "文档标题",
      "description": "文档描述",
      "file_name": "document.pdf",
      "file_size": 1048576,
      "file_type": "pdf",
      "tags": ["标签1", "标签2"],
      "status": "published",
      "content_extracted": true,
      "ai_summary": "文档摘要",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:30:00Z",
      "owner": {
        "username": "admin",
        "full_name": "系统管理员"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 100
}
```

### 获取文档详情
**接口**: `GET /api/v1/documents/{document_id}`

**响应数据**:
```json
{
  "id": 1,
  "title": "文档标题",
  "description": "文档描述",
  "file_name": "document.pdf",
  "file_size": 1048576,
  "file_type": "pdf",
  "tags": ["标签1", "标签2"],
  "status": "published",
  "content_extracted": true,
  "ai_summary": "文档摘要",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z",
  "owner": {
    "username": "admin",
    "full_name": "系统管理员"
  }
}
```

### 预览文档内容
**接口**: `GET /api/v1/search/preview/{document_id}`

**请求参数**:
```
highlight: "关键词"    # 可选，高亮关键词
page: 1               # 页码
page_size: 5000       # 每页字符数
```

**响应数据**:
```json
{
  "content": "文档内容...",
  "page": 1,
  "total_pages": 3,
  "status": "success",
  "highlight": "关键词",
  "content_source": "extracted",
  "document_info": {
    "title": "文档标题",
    "file_type": "pdf",
    "file_size": 1048576,
    "content_extracted": true
  }
}
```

### 下载文档
**接口**: `GET /api/v1/documents/{document_id}/download`

**响应**: 文件流下载

### 更新文档 (仅管理员)
**接口**: `PUT /api/v1/documents/{document_id}`

**请求参数**:
```
title: "新标题"
description: "新描述"
tags: "新标签1,新标签2"
```

**响应数据**:
```json
{
  "id": 1,
  "title": "新标题",
  "description": "新描述",
  "tags": ["新标签1", "新标签2"],
  "updated_at": "2024-01-01T13:00:00Z"
}
```

### 删除文档 (仅管理员)
**接口**: `DELETE /api/v1/documents/{document_id}`

**响应数据**:
```json
{
  "message": "文档删除成功",
  "id": 1
}
```

## 🔍 搜索功能

### 智能搜索 (POST)
**接口**: `POST /api/v1/search`

**请求参数**:
```json
{
  "query": "服务器配置",
  "file_types": ["pdf", "doc"],
  "max_results": 20
}
```

**响应数据**:
```json
{
  "results": [
    {
      "id": 1,
      "title": "服务器配置指南",
      "description": "详细的服务器配置说明",
      "content_snippet": "...服务器配置参数...",
      "category": {
        "id": 1,
        "name": "技术文档"
      },
      "tags": ["服务器", "配置"],
      "score": 4.5,
      "created_at": "2024-01-01T12:00:00Z",
      "file_type": "pdf",
      "file_size": 1048576,
      "matches": ["内容", "标题"],
      "content_extracted": true
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1,
  "query_time": 0.123,
  "query": "服务器配置"
}
```

### 文档搜索 (GET)
**接口**: `GET /api/v1/search/documents`

**请求参数**:
```
q: "关键词"          # 搜索关键词
doc_type: "pdf"      # 文档类型过滤
limit: 20            # 返回结果数量
offset: 0            # 结果偏移量
```

**响应数据**:
```json
{
  "query": "关键词",
  "total": 5,
  "limit": 20,
  "offset": 0,
  "results": [
    {
      "id": 1,
      "title": "文档标题",
      "description": "文档描述",
      "category": {
        "id": 1,
        "name": "技术文档"
      },
      "tags": ["标签1", "标签2"],
      "score": 4.5,
      "created_at": "2024-01-01T12:00:00Z",
      "file_type": "pdf",
      "file_size": 1048576,
      "matches": ["内容"],
      "match_type": "content",
      "match_priority": 1,
      "highlighted_snippets": [
        {
          "type": "content",
          "text": "包含<mark class=\"highlight\">关键词</mark>的内容片段",
          "label": "文档内容"
        }
      ],
      "content_extracted": true
    }
  ],
  "statistics": {
    "content_matches": 3,
    "title_matches": 1,
    "description_matches": 1,
    "total_matches": 5
  }
}
```

### 搜索建议
**接口**: `GET /api/v1/search/suggestions`

**响应数据**:
```json
{
  "suggestions": [
    "服务器配置",
    "网络设备",
    "安全策略",
    "备份方案",
    "监控系统",
    "故障处理",
    "系统维护"
  ]
}
```

## 🏗️ 资产管理

### 获取资产列表
**接口**: `GET /api/v1/assets`

**请求参数**:
```
query: "搜索关键词"           # 可选
asset_type: "server"         # 资产类型
status: "active"             # 资产状态
department: "技术部"         # 部门
network_location: "office"   # 网络位置
page: 1                      # 页码
per_page: 20                 # 每页数量
```

**响应数据**:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Web服务器01",
      "asset_type": "server",
      "device_model": "Dell PowerEdge R730",
      "ip_address": "192.168.1.100",
      "hostname": "web-server-01",
      "username": "admin",
      "password": "admin123",
      "network_location": "office",
      "department": "技术部",
      "status": "active",
      "notes": "主要Web服务器",
      "tags": ["production", "web"],
      "created_at": "2024-01-10T08:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### 获取资产详情
**接口**: `GET /api/v1/assets/{asset_id}`

**响应数据**:
```json
{
  "id": 1,
  "name": "Web服务器01",
  "asset_type": "server",
  "device_model": "Dell PowerEdge R730",
  "ip_address": "192.168.1.100",
  "hostname": "web-server-01",
  "username": "admin",
  "password": "admin123",
  "network_location": "office",
  "department": "技术部",
  "status": "active",
  "notes": "主要Web服务器",
  "tags": ["production", "web"],
  "created_at": "2024-01-10T08:00:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 创建资产 (仅管理员)
**接口**: `POST /api/v1/assets`

**请求参数**:
```json
{
  "name": "新服务器",
  "asset_type": "server",
  "device_model": "Dell PowerEdge R740",
  "ip_address": "192.168.1.200",
  "hostname": "new-server-01",
  "username": "admin",
  "password": "password123",
  "network_location": "office",
  "department": "技术部",
  "status": "active",
  "notes": "新增服务器",
  "tags": ["new", "server"]
}
```

**响应数据**:
```json
{
  "id": 6,
  "name": "新服务器",
  "asset_type": "server",
  "device_model": "Dell PowerEdge R740",
  "ip_address": "192.168.1.200",
  "hostname": "new-server-01",
  "username": "admin",
  "password": "password123",
  "network_location": "office",
  "department": "技术部",
  "status": "active",
  "notes": "新增服务器",
  "tags": ["new", "server"],
  "created_at": "2024-01-01T14:00:00Z",
  "updated_at": "2024-01-01T14:00:00Z"
}
```

### 更新资产 (仅管理员)
**接口**: `PUT /api/v1/assets/{asset_id}`

**请求参数**: 同创建资产

### 删除资产 (仅管理员)
**接口**: `DELETE /api/v1/assets/{asset_id}`

**响应数据**:
```json
{
  "message": "资产 'Web服务器01' 删除成功",
  "id": 1
}
```

### 资产统计信息
**接口**: `GET /api/v1/assets/statistics`

**响应数据**:
```json
{
  "total_count": 5,
  "by_type": {
    "server": 2,
    "network": 1,
    "storage": 1,
    "security": 1
  },
  "by_status": {
    "active": 4,
    "maintenance": 1
  },
  "by_environment": {},
  "by_department": {
    "技术部": 3,
    "网络部": 1,
    "安全部": 1
  },
  "recent_additions": 2,
  "pending_maintenance": 1
}
```

### 记录资产查看
**接口**: `POST /api/v1/assets/{asset_id}/view-details`

**响应数据**:
```json
{
  "asset_id": 1,
  "viewed_at": "2024-01-01T14:30:00Z",
  "view_count": 5,
  "message": "资产详情查看已记录"
}
```

### 导出资产数据 (仅管理员)
**接口**: `POST /api/v1/assets/export`

**请求参数**:
```json
{
  "asset_ids": [1, 2, 3],
  "format": "excel",
  "fields": ["name", "ip_address", "status"]
}
```

**响应**: Excel/CSV文件下载

### 从文档提取资产 (仅管理员)
**接口**: `POST /api/v1/assets/extract`

**请求参数**:
```json
{
  "document_id": 1,
  "auto_merge": true,
  "merge_threshold": 80
}
```

**响应数据**:
```json
{
  "extracted_count": 2,
  "merged_count": 0,
  "assets": [
    {
      "id": 7,
      "name": "提取的服务器01",
      "asset_type": "server",
      "ip_address": "192.168.1.201",
      "confidence_score": 85,
      "is_merged": false
    }
  ],
  "errors": []
}
```

## 📊 数据分析

### 系统统计信息 (仅管理员)
**接口**: `GET /api/v1/analytics/stats`

**响应数据**:
```json
{
  "total_documents": 25,
  "total_assets": 6,
  "active_assets": 5,
  "maintenance_assets": 1,
  "recent_assets": 3,
  "total_users": 2,
  "total_searches": 156,
  "total_document_views": 89,
  "total_asset_views": 34,
  "recent_uploads": 8,
  "system_status": "healthy",
  "userActivityStats": [
    {
      "userId": 1,
      "username": "系统管理员",
      "department": "技术部",
      "documentViews": 45,
      "searches": 23,
      "assetViews": 12,
      "lastActivity": "2024-01-01T14:30:00Z",
      "documentAccess": [
        {
          "documentId": 1,
          "documentTitle": "服务器配置指南",
          "accessCount": 15,
          "lastAccess": "2024-01-01T14:00:00Z"
        }
      ],
      "assetAccess": [
        {
          "assetId": 1,
          "assetName": "Web服务器01",
          "accessCount": 8,
          "lastAccess": "2024-01-01T13:30:00Z"
        }
      ]
    }
  ],
  "searchKeywords": [
    {
      "keyword": "服务器配置",
      "count": 45,
      "growth": 15
    }
  ],
  "user_activity_log": []
}
```

### AI智能分析 (仅管理员)
**接口**: `GET /api/v1/analytics/ai-analysis`

**响应数据**:
```json
{
  "analysis_time": "2024-01-01T15:00:00Z",
  "insights": [
    {
      "type": "document_access",
      "title": "文档访问热点分析",
      "content": "文档 \"服务器配置指南\" 是最受关注的文档，被访问了 15 次。",
      "priority": "info"
    }
  ],
  "recommendations": [
    {
      "type": "content_optimization",
      "title": "优化文档内容",
      "content": "发现 3 个文档未被访问，建议检查内容相关性和搜索标签。",
      "action": "审查未使用文档"
    }
  ],
  "risk_alerts": [
    {
      "type": "high_maintenance_ratio",
      "title": "设备维护率偏高",
      "content": "当前有 1/6 (16.7%) 设备处于维护状态，建议制定预防性维护计划。",
      "severity": "high",
      "recommended_action": "制定预防性维护策略"
    }
  ],
  "performance_metrics": {
    "document_utilization": 0.8,
    "asset_monitoring_coverage": 0.83,
    "search_diversity": 12,
    "user_engagement": 156
  }
}
```

### 清空统计数据 (仅管理员)
**接口**: `POST /api/v1/analytics/clear-stats`

**响应数据**:
```json
{
  "success": true,
  "message": "用户活动统计数据已清空",
  "backup_info": {
    "user_activity_log_count": 156,
    "search_keywords_count": 12,
    "document_views_count": 25,
    "asset_views_count": 8,
    "cleared_at": "2024-01-01T15:30:00Z",
    "cleared_by": "admin"
  }
}
```

## ⚙️ 任务管理

### 获取任务列表
**接口**: `GET /api/v1/tasks`

**响应数据**:
```json
{
  "items": [
    {
      "id": "extract_1_1704110400",
      "type": "content_extraction",
      "status": "completed",
      "progress": 100,
      "created_at": "2024-01-01T12:00:00Z",
      "document_title": "服务器配置指南"
    }
  ],
  "total": 1
}
```

### 获取任务状态
**接口**: `GET /api/v1/tasks/{task_id}`

**响应数据**:
```json
{
  "task_id": "extract_1_1704110400",
  "task_type": "content_extraction",
  "document_id": 1,
  "file_path": "./uploads/document.pdf",
  "title": "服务器配置指南",
  "status": "completed",
  "created_at": "2024-01-01T12:00:00Z",
  "started_at": "2024-01-01T12:00:05Z",
  "completed_at": "2024-01-01T12:00:30Z",
  "error": null,
  "progress": 100
}
```

### 获取文档提取状态
**接口**: `GET /api/v1/tasks/document/{document_id}/extraction-status`

**响应数据**:
```json
{
  "task_id": "extract_1_1704110400",
  "status": "completed",
  "progress": 100,
  "error": null,
  "created_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:00:30Z"
}
```

## 📂 其他接口

### 系统健康检查
**接口**: `GET /health`

**响应数据**:
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "database": "yunwei_docs_clean.db",
  "services": {
    "content_extractor": true,
    "search_service": true,
    "document_analyzer": true,
    "task_manager": true
  }
}
```

### 系统信息
**接口**: `GET /`

**响应数据**:
```json
{
  "message": "运维文档管理系统后端API - 数据库集成版",
  "status": "running",
  "version": "2.1.0",
  "database": "yunwei_docs_clean.db",
  "features": [
    "用户认证",
    "文档上传",
    "内容提取",
    "智能搜索",
    "标签管理",
    "资产管理",
    "数据持久化"
  ]
}
```

### 获取分类列表
**接口**: `GET /api/v1/categories`

**响应数据**:
```json
[
  {
    "id": 1,
    "name": "技术文档",
    "description": "技术相关文档",
    "color": "#2563eb",
    "icon": "DocumentTextOutline",
    "sort_order": 1,
    "is_active": true
  }
]
```

## ❌ 错误码

### HTTP状态码
- `200` - 请求成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未认证或认证失败
- `403` - 权限不足
- `404` - 资源不存在
- `422` - 数据验证失败
- `500` - 服务器内部错误

### 业务错误码
```json
{
  "detail": "用户名或密码错误"
}
```

**常见错误信息**:
- `"未认证或token无效"` - Token过期或无效
- `"需要管理员权限"` - 当前用户权限不足
- `"文档不存在"` - 请求的文档ID不存在
- `"不支持的文件类型"` - 上传的文件类型不被支持
- `"文件大小超过限制"` - 上传文件超过10MB限制
- `"用户名已存在"` - 创建用户时用户名重复
- `"资产ID不存在"` - 请求的资产ID不存在

### 错误处理建议
1. **401错误**: 重新登录获取新Token
2. **403错误**: 检查用户权限，联系管理员
3. **404错误**: 确认请求的资源ID正确
4. **422错误**: 检查请求参数格式和必填字段
5. **500错误**: 联系技术支持，查看服务器日志

---

*API接口文档版本: 1.0.0*  
*最后更新: 2024年*