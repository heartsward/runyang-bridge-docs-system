# -*- coding: utf-8 -*-
"""
语音查询API端点
支持自然语言查询文档和资产数据
"""
import time
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.deps import get_db, get_current_active_user, get_optional_user
from app.models.user import User
from app.models.document import Document
from app.models.asset import Asset
from app.schemas.voice import (
    VoiceQueryRequest, VoiceQueryResponse, VoiceParseRequest, VoiceParseResponse,
    VoiceSuggestRequest, VoiceSuggestResponse, VoiceQueryResult, 
    VoiceSearchFilter, VoiceQueryIntent, format_unified_results
)
from app.core.nlp_processor import nlp_processor
from app.core.search_engine import search_engine, SearchFilter, SearchOptions, SearchType, SortCriteria

router = APIRouter()


@router.post("/query", response_model=VoiceQueryResponse, summary="语音查询接口")
async def voice_query(
    query_request: VoiceQueryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    处理语音查询请求
    - 解析自然语言查询意图
    - 执行跨表搜索（文档+资产）
    - 返回统一格式结果
    """
    start_time = time.time()
    
    try:
        # 解析查询意图
        intent = parse_query_intent(query_request.query_text)
        
        # 构建统一搜索过滤器
        search_filter = build_unified_search_filter(intent, query_request.filters)
        
        # 构建搜索选项
        search_options = SearchOptions(
            limit=query_request.limit,
            sort_by=get_sort_criteria_from_intent(intent),
            include_content=True,
            include_metadata=True,
            highlight=True,
            fuzzy_search=True
        )
        
        # 使用统一搜索引擎执行搜索
        search_result = search_engine.search(
            query=query_request.query_text,
            db=db,
            filters=search_filter,
            options=search_options
        )
        
        # 转换为语音API格式
        voice_results = convert_search_results_to_voice_format(search_result.items)
        
        # 构建响应
        response_time = f"{search_result.search_time_ms}ms"
        
        result = VoiceQueryResult(
            query=query_request.query_text,
            intent=intent,
            total_results=search_result.total_count,
            search_time=response_time,
            results=voice_results,
            suggestions=search_result.suggestions,
            filters_applied=search_filter.__dict__ if search_filter else {}
        )
        
        return VoiceQueryResponse(
            success=True,
            message="语音查询成功",
            data=result,
            statistics={
                "documents_found": sum(1 for r in voice_results if r.get("type") == "document"),
                "assets_found": sum(1 for r in voice_results if r.get("type") == "asset"),
                "average_relevance": sum(r.get("relevance_score", 0) for r in voice_results) / len(voice_results) if voice_results else 0,
                "search_coverage": "high" if search_result.total_count >= 10 else "medium" if search_result.total_count >= 5 else "low",
                "query_complexity": "moderate"
            },
            meta={
                "response_time": response_time,
                "server_time": datetime.utcnow().isoformat() + "Z",
                "cached": False,
                "facets": search_result.facets,
                "did_you_mean": search_result.did_you_mean
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语音查询失败: {str(e)}"
        )


@router.post("/parse", response_model=VoiceParseResponse, summary="解析查询意图")
async def voice_parse(
    parse_request: VoiceParseRequest
):
    """
    解析自然语言查询意图
    - 提取查询关键词
    - 识别查询类型（文档/资产/混合）
    - 解析过滤条件
    """
    try:
        intent = parse_query_intent(parse_request.query_text)
        
        return VoiceParseResponse(
            success=True,
            message="查询意图解析成功",
            data={
                "intent": intent,
                "confidence": calculate_intent_confidence(intent),
                "parsed_keywords": intent.keywords,
                "suggested_filters": suggest_filters_for_intent(intent)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询意图解析失败: {str(e)}"
        )


@router.post("/suggest", response_model=VoiceSuggestResponse, summary="获取查询建议")
async def voice_suggest(
    suggest_request: VoiceSuggestRequest,
    db: Session = Depends(get_db)
):
    """
    基于输入文本提供查询建议
    """
    try:
        suggestions = []
        
        # 生成基于历史的建议
        if suggest_request.include_history:
            suggestions.extend(get_historical_suggestions(db, suggest_request.partial_query))
        
        # 生成基于内容的建议
        if suggest_request.include_content:
            suggestions.extend(get_content_based_suggestions(db, suggest_request.partial_query))
        
        # 生成模板建议
        template_suggestions = get_template_suggestions(suggest_request.partial_query)
        suggestions.extend(template_suggestions)
        
        # 去重并排序
        unique_suggestions = list(dict.fromkeys(suggestions))[:suggest_request.limit]
        
        return VoiceSuggestResponse(
            success=True,
            message="查询建议生成成功",
            data={
                "suggestions": unique_suggestions,
                "total_count": len(unique_suggestions),
                "templates": template_suggestions[:5]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询建议生成失败: {str(e)}"
        )


# ============= 核心处理函数 =============

def parse_query_intent(query_text: str) -> VoiceQueryIntent:
    """解析自然语言查询意图 - 使用增强的NLP处理器"""
    # 使用增强的NLP处理器
    nlp_intent = nlp_processor.process_query(query_text)
    
    # 转换为API格式
    return VoiceQueryIntent(
        original_query=query_text,
        query_type=nlp_intent.target_type,
        keywords=[entity.text for entity in nlp_intent.entities if not entity.entity_type.startswith(('TIME_', 'QUANTITY_'))],
        date_range=convert_time_constraints_to_range(nlp_intent.time_constraints),
        file_types=nlp_intent.filters.get('file_types', []),
        asset_types=nlp_intent.filters.get('asset_types', []),
        status_filters=nlp_intent.filters.get('status', []),
        sort_by=nlp_intent.sort_criteria or "relevance",
        confidence=nlp_intent.confidence
    )


def convert_time_constraints_to_range(time_constraints: Optional[Dict]) -> Optional[Dict[str, str]]:
    """将NLP处理器的时间约束转换为API格式"""
    if not time_constraints:
        return None
    
    return {
        "start": time_constraints["start"].isoformat(),
        "end": time_constraints["end"].isoformat()
    }


def build_unified_search_filter(intent: VoiceQueryIntent, additional_filters: Optional[Dict] = None) -> SearchFilter:
    """构建统一搜索引擎的搜索过滤器"""
    # 确定搜索类型
    if intent.query_type == "documents":
        search_type = SearchType.DOCUMENTS
    elif intent.query_type == "assets":
        search_type = SearchType.ASSETS
    else:
        search_type = SearchType.MIXED
    
    # 构建时间范围
    date_range = None
    if intent.date_range:
        date_range = {
            "start": datetime.fromisoformat(intent.date_range["start"].replace('Z', '')),
            "end": datetime.fromisoformat(intent.date_range["end"].replace('Z', ''))
        }
    
    # 创建过滤器
    search_filter = SearchFilter(
        keywords=intent.keywords,
        search_type=search_type,
        file_types=intent.file_types,
        asset_types=intent.asset_types,
        status_filters=intent.status_filters,
        date_range=date_range
    )
    
    # 应用额外过滤器
    if additional_filters:
        if additional_filters.get('tags'):
            search_filter.tags = additional_filters['tags']
        if additional_filters.get('categories'):
            search_filter.categories = additional_filters['categories']
        if additional_filters.get('locations'):
            search_filter.locations = additional_filters['locations']
        if additional_filters.get('authors'):
            search_filter.authors = additional_filters['authors']
    
    return search_filter


def get_sort_criteria_from_intent(intent: VoiceQueryIntent) -> SortCriteria:
    """从查询意图获取排序标准"""
    sort_mapping = {
        "relevance": SortCriteria.RELEVANCE,
        "date_desc": SortCriteria.DATE_DESC,
        "date_asc": SortCriteria.DATE_ASC,
        "views_desc": SortCriteria.VIEWS_DESC,
        "views_asc": SortCriteria.VIEWS_ASC,
        "title_asc": SortCriteria.TITLE_ASC,
        "title_desc": SortCriteria.TITLE_DESC,
        "size_desc": SortCriteria.SIZE_DESC,
        "size_asc": SortCriteria.SIZE_ASC
    }
    
    return sort_mapping.get(intent.sort_by, SortCriteria.RELEVANCE)


def convert_search_results_to_voice_format(search_items) -> List[Dict[str, Any]]:
    """将统一搜索引擎的结果转换为语音API格式"""
    voice_results = []
    
    for item in search_items:
        voice_result = {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "type": item.result_type,
            "relevance_score": item.relevance_score,
            "created_at": item.created_at.isoformat() if item.created_at else "",
            "metadata": item.metadata or {}
        }
        
        # 添加文档特定字段
        if item.result_type == "document":
            voice_result.update({
                "file_type": item.file_type,
                "file_size": item.file_size,
                "file_size_display": format_file_size_display(item.file_size) if item.file_size else None,
                "view_count": item.view_count,
                "download_url": item.metadata.get("download_url") if item.metadata else None,
                "tags": item.tags or [],
                "author": item.author
            })
        
        # 添加资产特定字段
        elif item.result_type == "asset":
            voice_result.update({
                "asset_type": item.asset_type,
                "status": item.status,
                "status_display": get_status_display_name(item.status),
                "location": item.location,
                "ip_address": item.ip_address,
                "health_score": item.health_score,
                "last_check": item.last_check.isoformat() if item.last_check else None,
                "tags": item.tags or []
            })
        
        # 添加高亮信息
        if hasattr(item, 'highlights') and item.highlights:
            voice_result["highlights"] = item.highlights
        
        voice_results.append(voice_result)
    
    return voice_results


def format_file_size_display(size_bytes: Optional[int]) -> str:
    """格式化文件大小显示"""
    if not size_bytes:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s}{size_names[i]}"


def get_status_display_name(status: Optional[str]) -> str:
    """获取状态显示名称"""
    status_map = {
        "active": "运行中",
        "inactive": "已停用",
        "maintenance": "维护中",
        "error": "异常",
        "retired": "已退役",
        "published": "已发布",
        "draft": "草稿",
        "archived": "已归档"
    }
    
    return status_map.get(status, status or "未知")


def extract_keywords(query_text: str) -> List[str]:
    """提取查询关键词"""
    # 去除常用停用词
    stop_words = {
        "的", "是", "在", "有", "和", "与", "或", "但", "而", "了", "着", "过", "来", "去",
        "给", "把", "被", "让", "使", "由", "为", "从", "到", "向", "往", "对", "关于",
        "查找", "搜索", "寻找", "找", "显示", "列出", "获取", "查看", "我要", "我想",
        "请", "帮我", "帮助", "什么", "哪些", "怎么", "如何"
    }
    
    # 基础分词（简化实现）
    import re
    words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', query_text)
    
    # 过滤停用词和短词
    keywords = [word for word in words if word not in stop_words and len(word) > 1]
    
    return keywords[:10]  # 限制关键词数量


def determine_query_type(query_lower: str) -> str:
    """判断查询类型"""
    document_indicators = ["文档", "文件", "报告", "手册", "说明", "记录", "pdf", "doc", "docx"]
    asset_indicators = ["设备", "资产", "服务器", "主机", "网络", "交换机", "路由器", "硬件"]
    
    doc_score = sum(1 for indicator in document_indicators if indicator in query_lower)
    asset_score = sum(1 for indicator in asset_indicators if indicator in query_lower)
    
    if doc_score > asset_score:
        return "documents"
    elif asset_score > doc_score:
        return "assets" 
    else:
        return "mixed"


def extract_date_range(query_lower: str) -> Optional[Dict[str, str]]:
    """提取时间范围"""
    # 时间关键词映射
    time_patterns = {
        "今天": 0,
        "昨天": 1,
        "本周": 7,
        "上周": 14,
        "本月": 30,
        "上月": 60,
        "今年": 365,
        "去年": 730
    }
    
    for pattern, days in time_patterns.items():
        if pattern in query_lower:
            from datetime import datetime, timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            return {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
    
    return None


def extract_file_types(query_lower: str) -> List[str]:
    """提取文件类型"""
    file_type_patterns = {
        r'\bpdf\b': 'pdf',
        r'\bdoc\b|word': 'doc',
        r'\bxls\b|excel': 'xls',
        r'\btxt\b|文本': 'txt',
        r'\bppt\b|幻灯片': 'ppt',
        r'\bimg\b|图片|jpg|png': 'image'
    }
    
    found_types = []
    for pattern, file_type in file_type_patterns.items():
        if re.search(pattern, query_lower):
            found_types.append(file_type)
    
    return found_types


def extract_asset_types(query_lower: str) -> List[str]:
    """提取资产类型"""
    asset_type_patterns = {
        r'服务器|主机|server': 'server',
        r'网络|交换机|路由器|network': 'network',
        r'存储|storage': 'storage',
        r'安全|防火墙|security': 'security',
        r'监控|monitor': 'monitor'
    }
    
    found_types = []
    for pattern, asset_type in asset_type_patterns.items():
        if re.search(pattern, query_lower):
            found_types.append(asset_type)
    
    return found_types


def extract_status_filters(query_lower: str) -> List[str]:
    """提取状态过滤条件"""
    status_patterns = {
        r'正常|运行|active': 'active',
        r'故障|错误|异常|error': 'error',
        r'维护|maintenance': 'maintenance',
        r'停用|inactive': 'inactive'
    }
    
    found_statuses = []
    for pattern, status in status_patterns.items():
        if re.search(pattern, query_lower):
            found_statuses.append(status)
    
    return found_statuses


def determine_sort_preference(query_lower: str) -> str:
    """判断排序偏好"""
    if any(word in query_lower for word in ["最新", "最近", "新", "recent"]):
        return "date_desc"
    elif any(word in query_lower for word in ["最旧", "最早", "oldest"]):
        return "date_asc"
    elif any(word in query_lower for word in ["热门", "访问", "popular"]):
        return "views_desc"
    else:
        return "relevance"


def calculate_base_confidence(query_lower: str) -> float:
    """计算基础置信度"""
    # 基于查询长度和结构化程度
    word_count = len(query_lower.split())
    
    if word_count < 2:
        return 0.3
    elif word_count < 5:
        return 0.7
    else:
        return 0.9


def build_search_filter(intent: VoiceQueryIntent, additional_filters: Optional[Dict] = None) -> VoiceSearchFilter:
    """构建搜索过滤器"""
    return VoiceSearchFilter(
        keywords=intent.keywords,
        query_type=intent.query_type,
        date_range=intent.date_range,
        file_types=intent.file_types,
        asset_types=intent.asset_types,
        status_filters=intent.status_filters,
        sort_by=intent.sort_by,
        additional=additional_filters or {}
    )


def search_documents(db: Session, search_filter: VoiceSearchFilter, limit: int = 20) -> List[Dict]:
    """搜索文档"""
    if search_filter.query_type == "assets":
        return []
    
    query = db.query(Document)
    
    # 关键词搜索
    if search_filter.keywords:
        keyword_filters = []
        for keyword in search_filter.keywords:
            keyword_filters.append(
                or_(
                    Document.title.contains(keyword),
                    Document.description.contains(keyword),
                    Document.content.contains(keyword)
                )
            )
        query = query.filter(or_(*keyword_filters))
    
    # 文件类型过滤
    if search_filter.file_types:
        query = query.filter(Document.file_type.in_(search_filter.file_types))
    
    # 时间范围过滤
    if search_filter.date_range:
        from datetime import datetime
        start_date = datetime.fromisoformat(search_filter.date_range["start"].replace('Z', ''))
        end_date = datetime.fromisoformat(search_filter.date_range["end"].replace('Z', ''))
        query = query.filter(Document.created_at.between(start_date, end_date))
    
    # 状态过滤
    query = query.filter(Document.status == "published")
    
    # 排序
    if search_filter.sort_by == "date_desc":
        query = query.order_by(Document.created_at.desc())
    elif search_filter.sort_by == "date_asc":
        query = query.order_by(Document.created_at.asc())
    elif search_filter.sort_by == "views_desc":
        query = query.order_by(Document.view_count.desc())
    
    documents = query.limit(limit).all()
    
    # 转换为字典格式
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "type": "document",
            "content": doc.description or doc.content[:200] if doc.content else "",
            "file_type": doc.file_type,
            "created_at": doc.created_at.isoformat() if doc.created_at else "",
            "view_count": doc.view_count or 0,
            "relevance_score": calculate_relevance_score(doc, search_filter.keywords)
        }
        for doc in documents
    ]


def search_assets(db: Session, search_filter: VoiceSearchFilter, limit: int = 20) -> List[Dict]:
    """搜索资产（简化实现，返回模拟数据）"""
    if search_filter.query_type == "documents":
        return []
    
    # 这里应该查询实际的资产数据，目前返回示例数据
    sample_assets = [
        {
            "id": 1,
            "name": "主服务器-001",
            "type": "asset",
            "asset_type": "server",
            "status": "active",
            "location": "数据中心A",
            "ip_address": "192.168.1.10",
            "health_score": 95,
            "created_at": "2024-01-15T08:30:00Z",
            "relevance_score": 0.9
        },
        {
            "id": 2,
            "name": "网络交换机-001", 
            "type": "asset",
            "asset_type": "network",
            "status": "maintenance",
            "location": "网络机房B",
            "ip_address": "192.168.1.1",
            "health_score": 78,
            "created_at": "2024-02-01T14:20:00Z",
            "relevance_score": 0.8
        }
    ]
    
    # 应用过滤器
    filtered_assets = []
    for asset in sample_assets:
        # 关键词匹配
        if search_filter.keywords:
            matches = any(keyword in asset["name"] for keyword in search_filter.keywords)
            if not matches:
                continue
        
        # 资产类型过滤
        if search_filter.asset_types and asset["asset_type"] not in search_filter.asset_types:
            continue
        
        # 状态过滤
        if search_filter.status_filters and asset["status"] not in search_filter.status_filters:
            continue
        
        filtered_assets.append(asset)
    
    return filtered_assets[:limit]


def calculate_relevance_score(document, keywords: List[str]) -> float:
    """计算文档相关性得分"""
    if not keywords:
        return 0.5
    
    score = 0.0
    content = f"{document.title} {document.description or ''} {document.content or ''}"
    content_lower = content.lower()
    
    for keyword in keywords:
        if keyword.lower() in document.title.lower():
            score += 0.3  # 标题匹配权重最高
        elif keyword.lower() in (document.description or "").lower():
            score += 0.2  # 描述匹配权重中等
        elif keyword.lower() in content_lower:
            score += 0.1  # 内容匹配权重最低
    
    return min(score, 1.0)


def generate_search_suggestions(query_text: str, intent: VoiceQueryIntent) -> List[str]:
    """生成搜索建议"""
    suggestions = []
    
    # 基于查询类型的建议
    if intent.query_type == "documents":
        suggestions.extend([
            f"查找{query_text}相关的PDF文档",
            f"显示最近创建的{query_text}文件",
            f"搜索{query_text}的操作手册"
        ])
    elif intent.query_type == "assets":
        suggestions.extend([
            f"显示{query_text}设备的运行状态",
            f"查找{query_text}资产的维护记录",
            f"搜索{query_text}相关的网络设备"
        ])
    else:
        suggestions.extend([
            f"全局搜索{query_text}",
            f"查找{query_text}相关的所有信息",
            f"显示{query_text}的详细资料"
        ])
    
    return suggestions[:5]


def calculate_intent_confidence(intent: VoiceQueryIntent) -> float:
    """计算意图置信度"""
    score = intent.confidence
    
    # 根据提取的信息数量调整置信度
    if intent.date_range:
        score += 0.1
    if intent.file_types:
        score += 0.1
    if intent.asset_types:
        score += 0.1
    if intent.status_filters:
        score += 0.1
    
    return min(score, 1.0)


def suggest_filters_for_intent(intent: VoiceQueryIntent) -> Dict[str, Any]:
    """为查询意图建议过滤器"""
    suggestions = {}
    
    if intent.query_type == "documents":
        suggestions["file_types"] = ["pdf", "doc", "docx", "txt"]
        suggestions["sort_options"] = ["最新", "最旧", "最相关"]
    elif intent.query_type == "assets":
        suggestions["asset_types"] = ["server", "network", "storage", "security"]
        suggestions["status_options"] = ["正常", "维护", "异常"]
    
    suggestions["time_ranges"] = ["今天", "本周", "本月", "今年"]
    
    return suggestions


def get_historical_suggestions(db: Session, partial_query: str) -> List[str]:
    """获取基于历史查询的建议"""
    # 简化实现，实际应该从查询日志中获取
    return [
        f"{partial_query}文档",
        f"{partial_query}设备状态",
        f"{partial_query}维护记录"
    ]


def get_content_based_suggestions(db: Session, partial_query: str) -> List[str]:
    """获取基于内容的建议"""
    # 简化实现，实际应该基于文档内容分析
    return [
        f"查找{partial_query}相关文档",
        f"搜索{partial_query}操作手册",
        f"显示{partial_query}技术资料"
    ]


def get_template_suggestions(partial_query: str) -> List[str]:
    """获取模板建议 - 使用增强的NLP处理器"""
    # 使用NLP处理器生成智能建议
    nlp_suggestions = nlp_processor.get_query_suggestions(partial_query)
    
    # 添加基础模板
    basic_templates = [
        f"显示所有{partial_query}",
        f"查找最新的{partial_query}",
        f"搜索{partial_query}状态",
        f"获取{partial_query}详细信息",
        f"列出{partial_query}相关资源"
    ]
    
    # 合并并去重
    all_suggestions = nlp_suggestions + basic_templates
    unique_suggestions = list(dict.fromkeys(all_suggestions))
    
    return unique_suggestions[:10]