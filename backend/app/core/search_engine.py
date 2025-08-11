# -*- coding: utf-8 -*-
"""
统一搜索引擎
支持跨数据源的智能搜索、排序和过滤
"""
import re
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc
from enum import Enum

from app.models.document import Document
from app.models.asset import Asset
from app.core.nlp_processor import nlp_processor, QueryIntent


class SearchType(Enum):
    """搜索类型枚举"""
    DOCUMENTS = "documents"
    ASSETS = "assets"
    MIXED = "mixed"


class SortCriteria(Enum):
    """排序标准枚举"""
    RELEVANCE = "relevance"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    VIEWS_DESC = "views_desc"
    VIEWS_ASC = "views_asc"
    SIZE_DESC = "size_desc"
    SIZE_ASC = "size_asc"


@dataclass
class SearchFilter:
    """搜索过滤器"""
    keywords: List[str] = field(default_factory=list)
    search_type: SearchType = SearchType.MIXED
    file_types: List[str] = field(default_factory=list)
    asset_types: List[str] = field(default_factory=list)
    status_filters: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    date_range: Optional[Dict[str, datetime]] = None
    size_range: Optional[Dict[str, int]] = None
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    authors: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)


@dataclass
class SearchOptions:
    """搜索选项"""
    sort_by: SortCriteria = SortCriteria.RELEVANCE
    limit: int = 20
    offset: int = 0
    include_content: bool = True
    include_metadata: bool = True
    highlight: bool = True
    fuzzy_search: bool = True
    boost_recent: bool = False
    boost_popular: bool = False


@dataclass
class SearchResultItem:
    """搜索结果项"""
    id: int
    title: str
    content: str
    result_type: str  # document, asset
    relevance_score: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 高亮信息
    highlights: List[str] = field(default_factory=list)
    
    # 文档特定字段
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None
    view_count: Optional[int] = None
    download_count: Optional[int] = None
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    # 资产特定字段
    asset_type: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None
    ip_address: Optional[str] = None
    health_score: Optional[int] = None
    last_check: Optional[datetime] = None


@dataclass
class SearchResult:
    """搜索结果集"""
    items: List[SearchResultItem]
    total_count: int
    search_time_ms: int
    query: str
    filters_applied: SearchFilter
    suggestions: List[str] = field(default_factory=list)
    facets: Dict[str, List[Dict]] = field(default_factory=dict)
    did_you_mean: Optional[str] = None


class UnifiedSearchEngine:
    """统一搜索引擎"""
    
    def __init__(self):
        self.min_search_length = 1
        self.max_results = 1000
        
        # 相关性权重配置
        self.relevance_weights = {
            'title_exact': 10.0,
            'title_partial': 5.0,
            'content_exact': 3.0,
            'content_partial': 1.0,
            'tags_match': 4.0,
            'category_match': 3.0,
            'recent_bonus': 1.5,
            'popular_bonus': 1.2,
            'file_type_match': 2.0
        }
    
    def search(
        self, 
        query: str,
        db: Session,
        filters: Optional[SearchFilter] = None,
        options: Optional[SearchOptions] = None
    ) -> SearchResult:
        """执行统一搜索"""
        start_time = time.time()
        
        # 参数默认值
        if filters is None:
            filters = SearchFilter()
        if options is None:
            options = SearchOptions()
        
        # 预处理查询
        processed_query = self._preprocess_query(query)
        
        # 智能查询分析
        if processed_query:
            nlp_intent = nlp_processor.process_query(query)
            filters = self._enhance_filters_with_nlp(filters, nlp_intent)
        
        # 执行搜索
        results = []
        total_count = 0
        
        if filters.search_type in [SearchType.DOCUMENTS, SearchType.MIXED]:
            doc_results, doc_count = self._search_documents(processed_query, db, filters, options)
            results.extend(doc_results)
            total_count += doc_count
        
        if filters.search_type in [SearchType.ASSETS, SearchType.MIXED]:
            asset_results, asset_count = self._search_assets(processed_query, db, filters, options)
            results.extend(asset_results)
            total_count += asset_count
        
        # 统一排序
        results = self._sort_results(results, options.sort_by, processed_query)
        
        # 应用分页
        paginated_results = results[options.offset:options.offset + options.limit]
        
        # 生成高亮
        if options.highlight and processed_query:
            paginated_results = self._add_highlights(paginated_results, processed_query)
        
        # 生成建议
        suggestions = self._generate_suggestions(query, results)
        
        # 生成分面信息
        facets = self._generate_facets(results) if len(results) < 1000 else {}
        
        # 拼写建议
        did_you_mean = self._generate_spell_suggestion(query) if len(results) < 3 else None
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return SearchResult(
            items=paginated_results,
            total_count=len(results),  # 实际匹配数量
            search_time_ms=search_time_ms,
            query=query,
            filters_applied=filters,
            suggestions=suggestions,
            facets=facets,
            did_you_mean=did_you_mean
        )
    
    def _preprocess_query(self, query: str) -> List[str]:
        """预处理查询文本"""
        if not query or len(query.strip()) < self.min_search_length:
            return []
        
        # 清理和标准化
        cleaned = re.sub(r'\s+', ' ', query.strip())
        
        # 提取搜索词
        # 支持引号括起的短语搜索
        phrases = re.findall(r'"([^"]*)"', cleaned)
        cleaned = re.sub(r'"[^"]*"', '', cleaned)
        
        # 分词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z0-9]+', cleaned)
        
        # 过滤停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '着', '过'}
        words = [word for word in words if word.lower() not in stop_words and len(word) > 1]
        
        # 合并短语和单词
        search_terms = phrases + words
        
        return search_terms[:20]  # 限制搜索词数量
    
    def _enhance_filters_with_nlp(self, filters: SearchFilter, nlp_intent: QueryIntent) -> SearchFilter:
        """使用NLP结果增强搜索过滤器"""
        # 更新搜索类型
        if nlp_intent.target_type == "documents":
            filters.search_type = SearchType.DOCUMENTS
        elif nlp_intent.target_type == "assets":
            filters.search_type = SearchType.ASSETS
        else:
            filters.search_type = SearchType.MIXED
        
        # 合并过滤条件
        if nlp_intent.filters.get('file_types'):
            filters.file_types.extend(nlp_intent.filters['file_types'])
        
        if nlp_intent.filters.get('asset_types'):
            filters.asset_types.extend(nlp_intent.filters['asset_types'])
        
        if nlp_intent.filters.get('status'):
            filters.status_filters.extend(nlp_intent.filters['status'])
        
        if nlp_intent.filters.get('locations'):
            filters.locations.extend(nlp_intent.filters['locations'])
        
        # 时间约束
        if nlp_intent.time_constraints:
            filters.date_range = nlp_intent.time_constraints
        
        return filters
    
    def _search_documents(
        self, 
        search_terms: List[str], 
        db: Session, 
        filters: SearchFilter, 
        options: SearchOptions
    ) -> Tuple[List[SearchResultItem], int]:
        """搜索文档"""
        query = db.query(Document)
        
        # 关键词搜索
        if search_terms:
            keyword_conditions = []
            for term in search_terms:
                term_conditions = [
                    Document.title.contains(term),
                    Document.description.contains(term)
                ]
                if options.include_content:
                    term_conditions.append(Document.content.contains(term))
                
                keyword_conditions.append(or_(*term_conditions))
            
            if keyword_conditions:
                query = query.filter(and_(*keyword_conditions))
        
        # 应用过滤器
        query = self._apply_document_filters(query, filters)
        
        # 获取总数
        total_count = query.count()
        
        # 执行查询（暂时获取所有结果用于相关性排序）
        documents = query.limit(min(self.max_results, 200)).all()
        
        # 转换为搜索结果并计算相关性
        results = []
        for doc in documents:
            relevance_score = self._calculate_document_relevance(doc, search_terms, filters, options)
            
            result_item = SearchResultItem(
                id=doc.id,
                title=doc.title or "",
                content=self._get_content_snippet(doc.description or doc.content or "", search_terms),
                result_type="document",
                relevance_score=relevance_score,
                created_at=doc.created_at or datetime.now(),
                updated_at=doc.updated_at,
                file_type=doc.file_type,
                file_size=doc.file_size,
                file_path=doc.file_path,
                view_count=doc.view_count or 0,
                author=getattr(doc, 'author', None),
                tags=doc.tags or [],
                metadata={
                    "status": doc.status,
                    "category": getattr(doc, 'category', None),
                    "source": "document",
                    "download_url": f"/api/v1/documents/{doc.id}/download" if doc.file_path else None
                }
            )
            results.append(result_item)
        
        return results, total_count
    
    def _search_assets(
        self, 
        search_terms: List[str], 
        db: Session, 
        filters: SearchFilter, 
        options: SearchOptions
    ) -> Tuple[List[SearchResultItem], int]:
        """搜索资产（模拟数据，实际应该查询资产数据库或文件）"""
        # 模拟资产数据
        sample_assets = [
            {
                "id": 1,
                "name": "主服务器-001",
                "description": "核心业务服务器，运行关键应用系统",
                "asset_type": "server",
                "status": "active",
                "location": "数据中心A机房",
                "ip_address": "192.168.1.10",
                "health_score": 95,
                "last_check": datetime.now() - timedelta(hours=1),
                "created_at": datetime(2024, 1, 15, 8, 30),
                "tags": ["核心", "生产环境", "Linux"]
            },
            {
                "id": 2,
                "name": "网络交换机-001",
                "description": "核心网络交换设备，负责内网通信",
                "asset_type": "network",
                "status": "maintenance",
                "location": "网络机房B",
                "ip_address": "192.168.1.1",
                "health_score": 78,
                "last_check": datetime.now() - timedelta(hours=2),
                "created_at": datetime(2024, 2, 1, 14, 20),
                "tags": ["网络", "核心设备"]
            },
            {
                "id": 3,
                "name": "存储阵列-001",
                "description": "高性能存储系统，存储重要业务数据",
                "asset_type": "storage",
                "status": "active",
                "location": "数据中心A机房",
                "ip_address": "192.168.1.20",
                "health_score": 88,
                "last_check": datetime.now() - timedelta(minutes=30),
                "created_at": datetime(2024, 1, 20, 10, 0),
                "tags": ["存储", "生产环境", "SAN"]
            }
        ]
        
        # 应用搜索过滤
        filtered_assets = []
        for asset in sample_assets:
            # 关键词匹配
            if search_terms:
                text_content = f"{asset['name']} {asset['description']} {' '.join(asset['tags'])}"
                matches = any(term.lower() in text_content.lower() for term in search_terms)
                if not matches:
                    continue
            
            # 资产类型过滤
            if filters.asset_types and asset['asset_type'] not in filters.asset_types:
                continue
            
            # 状态过滤
            if filters.status_filters and asset['status'] not in filters.status_filters:
                continue
            
            # 位置过滤
            if filters.locations and not any(loc in asset['location'] for loc in filters.locations):
                continue
            
            # 时间范围过滤
            if filters.date_range:
                asset_date = asset['created_at']
                if asset_date < filters.date_range['start'] or asset_date > filters.date_range['end']:
                    continue
            
            filtered_assets.append(asset)
        
        # 转换为搜索结果
        results = []
        for asset in filtered_assets:
            relevance_score = self._calculate_asset_relevance(asset, search_terms, filters, options)
            
            result_item = SearchResultItem(
                id=asset["id"],
                title=asset["name"],
                content=asset["description"],
                result_type="asset",
                relevance_score=relevance_score,
                created_at=asset["created_at"],
                asset_type=asset["asset_type"],
                status=asset["status"],
                location=asset["location"],
                ip_address=asset["ip_address"],
                health_score=asset["health_score"],
                last_check=asset["last_check"],
                tags=asset["tags"],
                metadata={
                    "source": "asset",
                    "health_status": "健康" if asset["health_score"] >= 90 else "注意" if asset["health_score"] >= 70 else "警告"
                }
            )
            results.append(result_item)
        
        return results, len(filtered_assets)
    
    def _apply_document_filters(self, query, filters: SearchFilter):
        """应用文档特定过滤器"""
        # 文件类型过滤
        if filters.file_types:
            query = query.filter(Document.file_type.in_(filters.file_types))
        
        # 状态过滤
        if filters.status_filters:
            query = query.filter(Document.status.in_(filters.status_filters))
        else:
            # 默认只显示已发布的文档
            query = query.filter(Document.status == "published")
        
        # 标签过滤
        if filters.tags:
            for tag in filters.tags:
                query = query.filter(Document.tags.contains([tag]))
        
        # 作者过滤
        if filters.authors:
            # 假设Document模型有author字段
            pass
        
        # 时间范围过滤
        if filters.date_range:
            query = query.filter(
                Document.created_at.between(
                    filters.date_range['start'], 
                    filters.date_range['end']
                )
            )
        
        # 文件大小过滤
        if filters.size_range:
            if filters.size_range.get('min'):
                query = query.filter(Document.file_size >= filters.size_range['min'])
            if filters.size_range.get('max'):
                query = query.filter(Document.file_size <= filters.size_range['max'])
        
        # 排除关键词
        if filters.exclude_keywords:
            exclude_conditions = []
            for keyword in filters.exclude_keywords:
                exclude_conditions.append(
                    and_(
                        ~Document.title.contains(keyword),
                        ~Document.description.contains(keyword),
                        ~Document.content.contains(keyword)
                    )
                )
            if exclude_conditions:
                query = query.filter(and_(*exclude_conditions))
        
        return query
    
    def _calculate_document_relevance(
        self, 
        document, 
        search_terms: List[str], 
        filters: SearchFilter, 
        options: SearchOptions
    ) -> float:
        """计算文档相关性评分"""
        if not search_terms:
            return 1.0
        
        score = 0.0
        title = (document.title or "").lower()
        content = (document.description or document.content or "").lower()
        tags = [tag.lower() for tag in (document.tags or [])]
        
        for term in search_terms:
            term_lower = term.lower()
            
            # 标题匹配
            if term_lower in title:
                if title == term_lower:
                    score += self.relevance_weights['title_exact']
                else:
                    score += self.relevance_weights['title_partial']
            
            # 内容匹配
            if term_lower in content:
                # 计算匹配密度
                matches = content.count(term_lower)
                content_length = len(content)
                density = matches / max(content_length, 1) * 1000
                score += self.relevance_weights['content_partial'] * (1 + density)
            
            # 标签匹配
            if any(term_lower in tag for tag in tags):
                score += self.relevance_weights['tags_match']
        
        # 时间加权
        if options.boost_recent and document.created_at:
            days_old = (datetime.now() - document.created_at).days
            if days_old < 30:
                score *= self.relevance_weights['recent_bonus']
        
        # 流行度加权
        if options.boost_popular and hasattr(document, 'view_count') and document.view_count:
            popularity_factor = min(document.view_count / 100, 2.0)  # 最多2倍加权
            score *= (1 + popularity_factor * (self.relevance_weights['popular_bonus'] - 1))
        
        # 文件类型匹配加权
        if filters.file_types and document.file_type in filters.file_types:
            score *= self.relevance_weights['file_type_match']
        
        return round(score, 2)
    
    def _calculate_asset_relevance(
        self, 
        asset: Dict, 
        search_terms: List[str], 
        filters: SearchFilter, 
        options: SearchOptions
    ) -> float:
        """计算资产相关性评分"""
        if not search_terms:
            return 1.0
        
        score = 0.0
        name = asset['name'].lower()
        description = asset['description'].lower()
        tags = [tag.lower() for tag in asset.get('tags', [])]
        
        for term in search_terms:
            term_lower = term.lower()
            
            # 名称匹配
            if term_lower in name:
                score += self.relevance_weights['title_partial']
            
            # 描述匹配
            if term_lower in description:
                score += self.relevance_weights['content_partial']
            
            # 标签匹配
            if any(term_lower in tag for tag in tags):
                score += self.relevance_weights['tags_match']
        
        # 健康评分加权
        health_score = asset.get('health_score', 50)
        if health_score >= 90:
            score *= 1.2
        elif health_score < 60:
            score *= 1.3  # 问题设备可能更重要
        
        # 资产类型匹配加权
        if filters.asset_types and asset['asset_type'] in filters.asset_types:
            score *= self.relevance_weights['file_type_match']
        
        return round(score, 2)
    
    def _sort_results(self, results: List[SearchResultItem], sort_by: SortCriteria, query_terms: List[str]) -> List[SearchResultItem]:
        """排序搜索结果"""
        if sort_by == SortCriteria.RELEVANCE:
            results.sort(key=lambda x: x.relevance_score, reverse=True)
        elif sort_by == SortCriteria.DATE_DESC:
            results.sort(key=lambda x: x.created_at, reverse=True)
        elif sort_by == SortCriteria.DATE_ASC:
            results.sort(key=lambda x: x.created_at)
        elif sort_by == SortCriteria.TITLE_ASC:
            results.sort(key=lambda x: x.title.lower())
        elif sort_by == SortCriteria.TITLE_DESC:
            results.sort(key=lambda x: x.title.lower(), reverse=True)
        elif sort_by == SortCriteria.VIEWS_DESC:
            results.sort(key=lambda x: x.view_count or 0, reverse=True)
        elif sort_by == SortCriteria.VIEWS_ASC:
            results.sort(key=lambda x: x.view_count or 0)
        elif sort_by == SortCriteria.SIZE_DESC:
            results.sort(key=lambda x: x.file_size or 0, reverse=True)
        elif sort_by == SortCriteria.SIZE_ASC:
            results.sort(key=lambda x: x.file_size or 0)
        
        return results
    
    def _get_content_snippet(self, content: str, search_terms: List[str], max_length: int = 200) -> str:
        """获取包含搜索词的内容片段"""
        if not content or not search_terms:
            return content[:max_length] if content else ""
        
        content_lower = content.lower()
        
        # 找到第一个搜索词的位置
        first_match_pos = len(content)
        for term in search_terms:
            pos = content_lower.find(term.lower())
            if pos != -1 and pos < first_match_pos:
                first_match_pos = pos
        
        if first_match_pos == len(content):
            # 没有匹配，返回开头
            return content[:max_length]
        
        # 计算片段开始位置
        start_pos = max(0, first_match_pos - 50)
        end_pos = min(len(content), start_pos + max_length)
        
        snippet = content[start_pos:end_pos]
        
        # 添加省略号
        if start_pos > 0:
            snippet = "..." + snippet
        if end_pos < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _add_highlights(self, results: List[SearchResultItem], search_terms: List[str]) -> List[SearchResultItem]:
        """为搜索结果添加高亮信息"""
        for result in results:
            highlights = []
            
            # 在标题中查找高亮
            title_highlights = self._find_highlights(result.title, search_terms)
            highlights.extend([f"标题: {h}" for h in title_highlights])
            
            # 在内容中查找高亮
            content_highlights = self._find_highlights(result.content, search_terms)
            highlights.extend([f"内容: {h}" for h in content_highlights])
            
            result.highlights = highlights[:5]  # 限制高亮数量
        
        return results
    
    def _find_highlights(self, text: str, search_terms: List[str], context_length: int = 30) -> List[str]:
        """在文本中查找高亮片段"""
        highlights = []
        text_lower = text.lower()
        
        for term in search_terms:
            term_lower = term.lower()
            pos = text_lower.find(term_lower)
            
            while pos != -1:
                start = max(0, pos - context_length)
                end = min(len(text), pos + len(term) + context_length)
                
                snippet = text[start:end]
                # 简单高亮标记
                highlighted = snippet.replace(term, f"**{term}**")
                
                if highlighted not in highlights:
                    highlights.append(highlighted)
                
                pos = text_lower.find(term_lower, pos + 1)
                
                if len(highlights) >= 3:  # 每个搜索词最多3个高亮
                    break
        
        return highlights
    
    def _generate_suggestions(self, query: str, results: List[SearchResultItem]) -> List[str]:
        """生成搜索建议"""
        suggestions = []
        
        # 基于结果生成建议
        if len(results) > 0:
            # 基于结果类型
            doc_count = sum(1 for r in results if r.result_type == "document")
            asset_count = sum(1 for r in results if r.result_type == "asset")
            
            if doc_count > 0 and asset_count == 0:
                suggestions.append(f"也搜索{query}相关的设备资产")
            elif asset_count > 0 and doc_count == 0:
                suggestions.append(f"也搜索{query}相关的文档资料")
            
            # 基于文件类型
            file_types = set(r.file_type for r in results if r.file_type)
            for file_type in list(file_types)[:3]:
                suggestions.append(f"只搜索{file_type}类型的{query}")
            
            # 基于时间
            suggestions.append(f"搜索最近的{query}")
            suggestions.append(f"搜索本年的{query}")
        else:
            # 没有结果时的建议
            suggestions.extend([
                f"尝试搜索'{query}'的同义词",
                f"检查'{query}'的拼写",
                f"使用更少的关键词",
                "浏览所有文档",
                "浏览所有设备"
            ])
        
        return suggestions[:5]
    
    def _generate_facets(self, results: List[SearchResultItem]) -> Dict[str, List[Dict]]:
        """生成分面信息（用于高级过滤）"""
        facets = {}
        
        if not results:
            return facets
        
        # 结果类型分面
        type_counts = {}
        for result in results:
            type_counts[result.result_type] = type_counts.get(result.result_type, 0) + 1
        
        facets["类型"] = [{"name": k, "count": v} for k, v in type_counts.items()]
        
        # 文件类型分面
        file_type_counts = {}
        for result in results:
            if result.file_type:
                file_type_counts[result.file_type] = file_type_counts.get(result.file_type, 0) + 1
        
        if file_type_counts:
            facets["文件类型"] = [{"name": k, "count": v} for k, v in file_type_counts.items()]
        
        # 资产类型分面
        asset_type_counts = {}
        for result in results:
            if result.asset_type:
                asset_type_counts[result.asset_type] = asset_type_counts.get(result.asset_type, 0) + 1
        
        if asset_type_counts:
            facets["资产类型"] = [{"name": k, "count": v} for k, v in asset_type_counts.items()]
        
        # 状态分面
        status_counts = {}
        for result in results:
            if result.status:
                status_counts[result.status] = status_counts.get(result.status, 0) + 1
        
        if status_counts:
            facets["状态"] = [{"name": k, "count": v} for k, v in status_counts.items()]
        
        return facets
    
    def _generate_spell_suggestion(self, query: str) -> Optional[str]:
        """生成拼写建议（简化实现）"""
        # 这里可以集成更复杂的拼写检查算法
        common_misspellings = {
            "服务qi": "服务器",
            "文挡": "文档",
            "设bai": "设备",
            "网络shebi": "网络设备"
        }
        
        return common_misspellings.get(query.lower())
    
    def get_search_analytics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """获取搜索分析数据"""
        # 这里可以实现搜索分析逻辑
        return {
            "total_searches": 0,
            "popular_queries": [],
            "search_success_rate": 0.0,
            "avg_results_per_search": 0.0,
            "top_result_types": []
        }


# 全局搜索引擎实例
search_engine = UnifiedSearchEngine()