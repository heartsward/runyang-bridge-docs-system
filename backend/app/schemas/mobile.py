# -*- coding: utf-8 -*-
"""
移动端API数据模型
专为移动应用优化的简化数据结构
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class MobileBaseResponse(BaseModel):
    """移动端API统一响应基类"""
    success: bool = True
    code: int = 200
    message: str = "请求成功"
    
    
class MobilePaginationInfo(BaseModel):
    """移动端分页信息"""
    page: int
    size: int  
    total: int
    has_next: bool
    has_prev: bool


class MobileMetaInfo(BaseModel):
    """移动端响应元信息"""
    cached: bool = False
    response_time: Optional[str] = None
    api_version: str = "v1.1"
    server_time: str


class MobileDocument(BaseModel):
    """移动端文档对象"""
    id: int
    title: str
    summary: str  # 自动生成的摘要，限制在200字内
    file_type: str
    file_size_display: str  # 格式化显示 "1.2MB"
    created_at: str  # ISO格式字符串
    updated_at: str
    category: Optional[str] = None
    tags: List[str] = []
    preview_available: bool = False
    thumbnail_url: Optional[str] = None
    view_count: int = 0
    is_favorite: bool = False  # 用户是否收藏
    
    class Config:
        from_attributes = True


class MobileDocumentDetail(MobileDocument):
    """移动端文档详情"""
    description: Optional[str] = None
    content_preview: str  # 内容预览，限制500字
    download_url: Optional[str] = None
    related_assets: List[Dict[str, Any]] = []  # 相关资产


class MobileAsset(BaseModel):
    """移动端资产对象"""
    id: int
    name: str
    asset_type: str
    status: str
    status_display: str  # 状态显示名称
    status_icon: str  # 状态图标标识
    status_color: str  # 状态颜色 #00FF00
    location: Optional[str] = None
    ip_address: Optional[str] = None
    last_check: Optional[str] = None  # ISO格式
    health_score: Optional[int] = None  # 0-100健康评分
    priority: str = "medium"  # high|medium|low
    created_at: str
    
    class Config:
        from_attributes = True


class MobileAssetDetail(MobileAsset):
    """移动端资产详情"""
    description: Optional[str] = None
    specifications: Dict[str, Any] = {}  # 技术规格
    maintenance_info: Dict[str, Any] = {}  # 维护信息
    related_documents: List[Dict[str, Any]] = []  # 相关文档


class MobileSearchResult(BaseModel):
    """移动端搜索结果"""
    query: str
    total_count: int
    search_time: str  # 搜索耗时
    documents: List[MobileDocument] = []
    assets: List[MobileAsset] = []
    suggestions: List[str] = []  # 搜索建议
    related_keywords: List[str] = []  # 相关关键词


class MobileUserProfile(BaseModel):
    """移动端用户信息"""
    id: int
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    role: str
    avatar_url: Optional[str] = None
    last_login: Optional[str] = None
    preferences: Dict[str, Any] = {}
    
    
class MobileAuthResponse(MobileBaseResponse):
    """移动端认证响应"""
    data: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 2592000  # 30天（秒）
    user: Optional[MobileUserProfile] = None


class MobileDocumentListResponse(MobileBaseResponse):
    """移动端文档列表响应"""
    data: List[MobileDocument]
    pagination: MobilePaginationInfo
    meta: MobileMetaInfo
    

class MobileAssetListResponse(MobileBaseResponse):
    """移动端资产列表响应"""
    data: List[MobileAsset]  
    pagination: MobilePaginationInfo
    meta: MobileMetaInfo


class MobileSearchResponse(MobileBaseResponse):
    """移动端搜索响应"""
    data: MobileSearchResult
    meta: MobileMetaInfo


# 请求模型
class MobileLoginRequest(BaseModel):
    """移动端登录请求"""
    username: str
    password: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    platform: str = "android"  # android|ios


class MobileSearchRequest(BaseModel):
    """移动端搜索请求"""
    query: str
    search_type: str = "all"  # all|documents|assets
    category: Optional[str] = None
    limit: int = 20
    offset: int = 0
    filters: Dict[str, Any] = {}


class MobileRefreshTokenRequest(BaseModel):
    """移动端Token刷新请求"""
    refresh_token: str
    device_id: Optional[str] = None


# 辅助函数
def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s}{size_names[i]}"


def get_status_display_info(status: str) -> Dict[str, str]:
    """获取状态显示信息"""
    status_map = {
        "active": {"display": "运行中", "icon": "check_circle", "color": "#00C851"},
        "inactive": {"display": "已停用", "icon": "cancel", "color": "#6c757d"},
        "maintenance": {"display": "维护中", "icon": "build", "color": "#ff8800"},
        "error": {"display": "异常", "icon": "error", "color": "#dc3545"},
        "retired": {"display": "已退役", "icon": "archive", "color": "#6f42c1"}
    }
    return status_map.get(status, {"display": status, "icon": "help", "color": "#6c757d"})


def generate_summary(content: str, max_length: int = 200) -> str:
    """生成内容摘要"""
    if not content:
        return ""
    # 简单的摘要生成，实际可以集成更复杂的NLP算法
    import re
    # 清理HTML标签和多余空白
    clean_content = re.sub(r'<[^>]+>', '', content)
    clean_content = re.sub(r'\s+', ' ', clean_content).strip()
    
    if len(clean_content) <= max_length:
        return clean_content
    
    # 尝试在句号处截断
    sentences = clean_content.split('。')
    summary = ""
    for sentence in sentences:
        if len(summary + sentence + "。") <= max_length:
            summary += sentence + "。"
        else:
            break
    
    if not summary:
        summary = clean_content[:max_length] + "..."
    
    return summary