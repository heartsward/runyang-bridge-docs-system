# -*- coding: utf-8 -*-
"""
语音查询API数据模型
支持自然语言查询的数据结构定义
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from datetime import datetime


class VoiceBaseResponse(BaseModel):
    """语音API统一响应基类"""
    success: bool = True
    code: int = 200
    message: str = "请求成功"


class VoiceQueryIntent(BaseModel):
    """查询意图解析结果"""
    original_query: str
    query_type: str  # documents, assets, mixed
    keywords: List[str]
    date_range: Optional[Dict[str, str]] = None
    file_types: List[str] = []
    asset_types: List[str] = []
    status_filters: List[str] = []
    sort_by: str = "relevance"  # relevance, date_desc, date_asc, views_desc
    confidence: float = 0.5


class VoiceSearchFilter(BaseModel):
    """语音搜索过滤器"""
    keywords: List[str] = []
    query_type: str = "mixed"
    date_range: Optional[Dict[str, str]] = None
    file_types: List[str] = []
    asset_types: List[str] = []
    status_filters: List[str] = []
    sort_by: str = "relevance"
    additional: Dict[str, Any] = {}


class VoiceSearchResultItem(BaseModel):
    """统一搜索结果项"""
    id: int
    title: str
    type: str  # document, asset
    content: str
    relevance_score: float
    created_at: str
    metadata: Dict[str, Any] = {}
    
    # 文档特定字段
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    view_count: Optional[int] = None
    download_url: Optional[str] = None
    
    # 资产特定字段
    asset_type: Optional[str] = None
    status: Optional[str] = None
    status_display: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    health_score: Optional[int] = None


class VoiceQueryResult(BaseModel):
    """语音查询结果"""
    query: str
    intent: VoiceQueryIntent
    total_results: int
    search_time: str
    results: List[VoiceSearchResultItem]
    suggestions: List[str] = []
    filters_applied: Dict[str, Any] = {}
    related_queries: List[str] = []


class VoiceStatistics(BaseModel):
    """语音查询统计信息"""
    documents_found: int
    assets_found: int
    average_relevance: float
    search_coverage: str  # high, medium, low
    query_complexity: str  # simple, moderate, complex


# ============= 请求模型 =============

class VoiceQueryRequest(BaseModel):
    """语音查询请求"""
    query_text: str
    query_id: Optional[str] = None  # 用于跟踪查询会话
    limit: int = 20
    include_suggestions: bool = True
    filters: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None  # 上下文信息


class VoiceParseRequest(BaseModel):
    """查询意图解析请求"""
    query_text: str
    context: Optional[Dict[str, Any]] = None


class VoiceSuggestRequest(BaseModel):
    """查询建议请求"""
    partial_query: str
    limit: int = 10
    include_history: bool = True
    include_content: bool = True
    user_preferences: Optional[Dict[str, Any]] = None


class VoiceFeedbackRequest(BaseModel):
    """查询反馈请求"""
    query_id: str
    feedback_type: str  # positive, negative, irrelevant
    selected_results: List[int] = []
    comments: Optional[str] = None


# ============= 响应模型 =============

class VoiceQueryResponse(VoiceBaseResponse):
    """语音查询响应"""
    data: VoiceQueryResult
    statistics: Optional[VoiceStatistics] = None
    meta: Dict[str, Any] = {}


class VoiceParseResponse(VoiceBaseResponse):
    """查询意图解析响应"""
    data: Dict[str, Any]


class VoiceSuggestResponse(VoiceBaseResponse):
    """查询建议响应"""
    data: Dict[str, Any]


class VoiceAnalyticsResponse(VoiceBaseResponse):
    """语音查询分析响应"""
    data: Dict[str, Any]


# ============= 辅助函数 =============

def format_unified_results(documents: List[Dict], assets: List[Dict], query: str) -> List[VoiceSearchResultItem]:
    """将文档和资产结果统一格式化"""
    unified_results = []
    
    # 处理文档结果
    for doc in documents:
        result_item = VoiceSearchResultItem(
            id=doc["id"],
            title=doc["title"],
            type="document",
            content=doc["content"],
            relevance_score=doc["relevance_score"],
            created_at=doc["created_at"],
            file_type=doc.get("file_type"),
            view_count=doc.get("view_count"),
            download_url=f"/api/v1/documents/{doc['id']}/download",
            metadata={
                "source": "document",
                "file_size_display": format_file_size(doc.get("file_size", 0)) if doc.get("file_size") else None
            }
        )
        unified_results.append(result_item)
    
    # 处理资产结果
    for asset in assets:
        status_info = get_asset_status_display(asset.get("status", "unknown"))
        
        result_item = VoiceSearchResultItem(
            id=asset["id"],
            title=asset["name"],
            type="asset",
            content=f"资产类型: {asset.get('asset_type', 'unknown')}, 位置: {asset.get('location', 'unknown')}",
            relevance_score=asset["relevance_score"],
            created_at=asset["created_at"],
            asset_type=asset.get("asset_type"),
            status=asset.get("status"),
            status_display=status_info["display"],
            location=asset.get("location"),
            ip_address=asset.get("ip_address"),
            health_score=asset.get("health_score"),
            metadata={
                "source": "asset",
                "status_color": status_info["color"],
                "status_icon": status_info["icon"]
            }
        )
        unified_results.append(result_item)
    
    # 按相关性排序
    unified_results.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return unified_results


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


def get_asset_status_display(status: str) -> Dict[str, str]:
    """获取资产状态显示信息"""
    status_map = {
        "active": {"display": "运行中", "icon": "check_circle", "color": "#00C851"},
        "inactive": {"display": "已停用", "icon": "cancel", "color": "#6c757d"},
        "maintenance": {"display": "维护中", "icon": "build", "color": "#ff8800"},
        "error": {"display": "异常", "icon": "error", "color": "#dc3545"},
        "retired": {"display": "已退役", "icon": "archive", "color": "#6f42c1"}
    }
    return status_map.get(status, {"display": status, "icon": "help", "color": "#6c757d"})


def calculate_query_statistics(results: List[VoiceSearchResultItem]) -> VoiceStatistics:
    """计算查询统计信息"""
    documents_count = sum(1 for r in results if r.type == "document")
    assets_count = sum(1 for r in results if r.type == "asset")
    
    if results:
        avg_relevance = sum(r.relevance_score for r in results) / len(results)
    else:
        avg_relevance = 0.0
    
    # 判断搜索覆盖度
    total_results = len(results)
    if total_results >= 10:
        coverage = "high"
    elif total_results >= 5:
        coverage = "medium"
    else:
        coverage = "low"
    
    return VoiceStatistics(
        documents_found=documents_count,
        assets_found=assets_count,
        average_relevance=round(avg_relevance, 2),
        search_coverage=coverage,
        query_complexity="moderate"  # 可以基于查询复杂度算法计算
    )


def generate_related_queries(original_query: str, intent: VoiceQueryIntent) -> List[str]:
    """生成相关查询建议"""
    related = []
    
    # 基于关键词生成相关查询
    for keyword in intent.keywords[:3]:  # 取前3个关键词
        if keyword != original_query:
            related.append(f"查找{keyword}的详细信息")
            related.append(f"显示{keyword}相关资源")
    
    # 基于查询类型生成相关查询
    if intent.query_type == "documents":
        related.append("最近更新的文档")
        related.append("热门文档排行")
    elif intent.query_type == "assets":
        related.append("设备健康状况")
        related.append("资产维护计划")
    
    return related[:5]


def extract_query_context(query_text: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
    """提取查询上下文信息"""
    context = {
        "query_length": len(query_text),
        "word_count": len(query_text.split()),
        "has_time_reference": any(word in query_text.lower() for word in ["今天", "昨天", "本周", "最近"]),
        "has_status_reference": any(word in query_text.lower() for word in ["正常", "异常", "维护", "故障"]),
        "query_complexity": "simple" if len(query_text.split()) <= 3 else "complex"
    }
    
    if user_context:
        context.update(user_context)
    
    return context


def build_search_summary(results: List[VoiceSearchResultItem], query: str) -> str:
    """构建搜索结果摘要"""
    total = len(results)
    documents = sum(1 for r in results if r.type == "document")
    assets = sum(1 for r in results if r.type == "asset")
    
    if total == 0:
        return f"未找到与'{query}'相关的结果"
    
    summary_parts = []
    
    if documents > 0:
        summary_parts.append(f"{documents}个文档")
    
    if assets > 0:
        summary_parts.append(f"{assets}个资产")
    
    summary = f"找到{total}个结果：" + "、".join(summary_parts)
    
    # 添加最相关结果的预览
    if results:
        top_result = results[0]
        summary += f"，最相关的是：{top_result.title}"
    
    return summary


def validate_voice_query(query_text: str) -> Dict[str, Any]:
    """验证语音查询的有效性"""
    validation = {
        "is_valid": True,
        "issues": [],
        "suggestions": []
    }
    
    # 检查查询长度
    if len(query_text.strip()) < 2:
        validation["is_valid"] = False
        validation["issues"].append("查询过短")
        validation["suggestions"].append("请输入至少2个字符的查询")
    
    if len(query_text) > 200:
        validation["issues"].append("查询过长")
        validation["suggestions"].append("请简化查询内容")
    
    # 检查是否包含有效关键词
    import re
    if not re.search(r'[\u4e00-\u9fff]|[a-zA-Z0-9]', query_text):
        validation["is_valid"] = False
        validation["issues"].append("查询不包含有效字符")
        validation["suggestions"].append("请输入中文或英文查询")
    
    return validation