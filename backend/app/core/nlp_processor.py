# -*- coding: utf-8 -*-
"""
自然语言处理模块
专为中文查询优化的语义理解和意图识别
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class QueryEntity:
    """查询实体"""
    text: str
    entity_type: str  # PERSON, ORG, LOCATION, TIME, EQUIPMENT, etc.
    confidence: float
    start_pos: int
    end_pos: int


@dataclass 
class QueryIntent:
    """增强的查询意图"""
    intent_type: str  # SEARCH, FILTER, SORT, AGGREGATE, etc.
    target_type: str  # document, asset, mixed
    action: str  # find, list, show, count, etc.
    entities: List[QueryEntity]
    filters: Dict[str, Any]
    sort_criteria: Optional[str]
    time_constraints: Optional[Dict[str, datetime]]
    confidence: float


class ChineseNLPProcessor:
    """中文自然语言处理器"""
    
    def __init__(self):
        self.stop_words = self._load_stop_words()
        self.entity_patterns = self._load_entity_patterns()
        self.intent_patterns = self._load_intent_patterns()
        self.synonym_dict = self._load_synonyms()
    
    def process_query(self, query_text: str) -> QueryIntent:
        """处理查询文本，返回结构化意图"""
        # 预处理
        cleaned_query = self._preprocess_text(query_text)
        
        # 实体识别
        entities = self._extract_entities(cleaned_query)
        
        # 意图识别
        intent_type, action = self._identify_intent(cleaned_query)
        
        # 目标类型识别
        target_type = self._identify_target_type(cleaned_query, entities)
        
        # 过滤条件提取
        filters = self._extract_filters(cleaned_query, entities)
        
        # 排序条件提取
        sort_criteria = self._extract_sort_criteria(cleaned_query)
        
        # 时间约束提取
        time_constraints = self._extract_time_constraints(cleaned_query)
        
        # 计算置信度
        confidence = self._calculate_confidence(cleaned_query, entities)
        
        return QueryIntent(
            intent_type=intent_type,
            target_type=target_type,
            action=action,
            entities=entities,
            filters=filters,
            sort_criteria=sort_criteria,
            time_constraints=time_constraints,
            confidence=confidence
        )
    
    def _preprocess_text(self, text: str) -> str:
        """文本预处理"""
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 标准化标点符号
        text = text.replace('？', '?').replace('！', '!')
        text = text.replace('，', ',').replace('。', '.')
        
        # 统一数字格式
        text = re.sub(r'[０-９]', lambda m: str(ord(m.group()) - ord('０')), text)
        
        return text
    
    def _extract_entities(self, text: str) -> List[QueryEntity]:
        """实体识别和抽取"""
        entities = []
        
        # 时间实体
        time_entities = self._extract_time_entities(text)
        entities.extend(time_entities)
        
        # 设备类型实体
        equipment_entities = self._extract_equipment_entities(text)
        entities.extend(equipment_entities)
        
        # 文件类型实体
        file_type_entities = self._extract_file_type_entities(text)
        entities.extend(file_type_entities)
        
        # 状态实体
        status_entities = self._extract_status_entities(text)
        entities.extend(status_entities)
        
        # 位置实体
        location_entities = self._extract_location_entities(text)
        entities.extend(location_entities)
        
        # 人员实体
        person_entities = self._extract_person_entities(text)
        entities.extend(person_entities)
        
        # 数量实体
        quantity_entities = self._extract_quantity_entities(text)
        entities.extend(quantity_entities)
        
        return self._remove_overlapping_entities(entities)
    
    def _extract_time_entities(self, text: str) -> List[QueryEntity]:
        """提取时间相关实体"""
        entities = []
        patterns = {
            r'今天|今日': ('TODAY', 1.0),
            r'昨天|昨日': ('YESTERDAY', 1.0),
            r'明天|明日': ('TOMORROW', 1.0),
            r'本周|这周': ('THIS_WEEK', 0.9),
            r'上周|上星期': ('LAST_WEEK', 0.9),
            r'下周|下星期': ('NEXT_WEEK', 0.9),
            r'本月|这个月': ('THIS_MONTH', 0.9),
            r'上月|上个月': ('LAST_MONTH', 0.9),
            r'下月|下个月': ('NEXT_MONTH', 0.9),
            r'今年|本年': ('THIS_YEAR', 0.8),
            r'去年|上年': ('LAST_YEAR', 0.8),
            r'明年|下年': ('NEXT_YEAR', 0.8),
            r'最近|近期': ('RECENT', 0.7),
            r'最新|新的': ('LATEST', 0.7),
            r'\d{4}年': ('YEAR', 0.8),
            r'\d{1,2}月': ('MONTH', 0.7),
            r'\d{1,2}日|\d{1,2}号': ('DAY', 0.6)
        }
        
        for pattern, (entity_type, confidence) in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(QueryEntity(
                    text=match.group(),
                    entity_type=f'TIME_{entity_type}',
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _extract_equipment_entities(self, text: str) -> List[QueryEntity]:
        """提取设备类型实体"""
        entities = []
        patterns = {
            r'服务器|主机|server': ('SERVER', 0.95),
            r'交换机|网络设备|switch': ('NETWORK_SWITCH', 0.95),
            r'路由器|router': ('ROUTER', 0.95),
            r'防火墙|firewall': ('FIREWALL', 0.9),
            r'存储|storage|磁盘阵列': ('STORAGE', 0.9),
            r'打印机|printer': ('PRINTER', 0.85),
            r'监控|摄像头|camera': ('MONITOR', 0.85),
            r'UPS|不间断电源': ('UPS', 0.9),
            r'空调|制冷|cooling': ('COOLING', 0.8),
            r'机柜|cabinet': ('CABINET', 0.8)
        }
        
        for pattern, (entity_type, confidence) in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(QueryEntity(
                    text=match.group(),
                    entity_type=f'EQUIPMENT_{entity_type}',
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _extract_file_type_entities(self, text: str) -> List[QueryEntity]:
        """提取文件类型实体"""
        entities = []
        patterns = {
            r'PDF|pdf': ('PDF', 1.0),
            r'Word|word|DOC|doc|DOCX|docx': ('WORD', 0.95),
            r'Excel|excel|XLS|xls|XLSX|xlsx': ('EXCEL', 0.95),
            r'PPT|ppt|PowerPoint|powerpoint': ('POWERPOINT', 0.95),
            r'TXT|txt|文本文件': ('TEXT', 0.9),
            r'图片|图像|JPG|jpg|PNG|png|GIF|gif': ('IMAGE', 0.9),
            r'视频|MP4|mp4|AVI|avi': ('VIDEO', 0.85),
            r'音频|MP3|mp3|WAV|wav': ('AUDIO', 0.85),
            r'压缩包|ZIP|zip|RAR|rar': ('ARCHIVE', 0.9)
        }
        
        for pattern, (entity_type, confidence) in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(QueryEntity(
                    text=match.group(),
                    entity_type=f'FILE_{entity_type}',
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _extract_status_entities(self, text: str) -> List[QueryEntity]:
        """提取状态实体"""
        entities = []
        patterns = {
            r'正常|运行|活跃|active': ('ACTIVE', 0.9),
            r'异常|故障|错误|error|问题': ('ERROR', 0.95),
            r'维护|维修|maintenance': ('MAINTENANCE', 0.9),
            r'停用|禁用|inactive|关闭': ('INACTIVE', 0.9),
            r'退役|废弃|retired': ('RETIRED', 0.85),
            r'健康|良好': ('HEALTHY', 0.8),
            r'警告|告警|warning': ('WARNING', 0.85)
        }
        
        for pattern, (entity_type, confidence) in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(QueryEntity(
                    text=match.group(),
                    entity_type=f'STATUS_{entity_type}',
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _extract_location_entities(self, text: str) -> List[QueryEntity]:
        """提取位置实体"""
        entities = []
        patterns = {
            r'数据中心|机房|IDC': ('DATA_CENTER', 0.9),
            r'办公室|办公区': ('OFFICE', 0.8),
            r'一楼|二楼|三楼|\d+楼': ('FLOOR', 0.8),
            r'A区|B区|C区|[A-Z]区': ('ZONE', 0.8),
            r'机柜\d+|柜子\d+': ('RACK', 0.9)
        }
        
        for pattern, (entity_type, confidence) in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(QueryEntity(
                    text=match.group(),
                    entity_type=f'LOCATION_{entity_type}',
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _extract_person_entities(self, text: str) -> List[QueryEntity]:
        """提取人员实体"""
        entities = []
        # 简单的人名模式（可以扩展）
        patterns = {
            r'[\u4e00-\u9fff]{2,3}(?:工程师|经理|主管|负责人)': ('STAFF', 0.8),
            r'管理员|admin': ('ADMIN', 0.9)
        }
        
        for pattern, (entity_type, confidence) in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(QueryEntity(
                    text=match.group(),
                    entity_type=f'PERSON_{entity_type}',
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _extract_quantity_entities(self, text: str) -> List[QueryEntity]:
        """提取数量实体"""
        entities = []
        patterns = {
            r'\d+个': ('COUNT', 0.9),
            r'\d+台': ('DEVICE_COUNT', 0.9),
            r'\d+份': ('DOCUMENT_COUNT', 0.9),
            r'前\d+|最多\d+': ('LIMIT', 0.8),
            r'所有|全部': ('ALL', 0.7)
        }
        
        for pattern, (entity_type, confidence) in patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append(QueryEntity(
                    text=match.group(),
                    entity_type=f'QUANTITY_{entity_type}',
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _remove_overlapping_entities(self, entities: List[QueryEntity]) -> List[QueryEntity]:
        """移除重叠的实体，保留置信度高的"""
        if not entities:
            return entities
        
        # 按位置排序
        entities.sort(key=lambda x: (x.start_pos, -x.confidence))
        
        filtered = []
        last_end = -1
        
        for entity in entities:
            if entity.start_pos >= last_end:
                filtered.append(entity)
                last_end = entity.end_pos
            elif entity.confidence > filtered[-1].confidence:
                # 如果新实体置信度更高，替换前一个
                filtered[-1] = entity
                last_end = entity.end_pos
        
        return filtered
    
    def _identify_intent(self, text: str) -> Tuple[str, str]:
        """识别查询意图"""
        intent_patterns = {
            'SEARCH': {
                'patterns': [r'查找|搜索|寻找|找|search|find'],
                'actions': ['find', 'search']
            },
            'LIST': {
                'patterns': [r'列出|显示|展示|列表|show|list|display'],
                'actions': ['list', 'show']
            },
            'COUNT': {
                'patterns': [r'多少|数量|统计|count|总数'],
                'actions': ['count', 'aggregate']
            },
            'FILTER': {
                'patterns': [r'筛选|过滤|filter|条件'],
                'actions': ['filter']
            },
            'SORT': {
                'patterns': [r'排序|排列|按.*排|sort'],
                'actions': ['sort']
            },
            'DETAIL': {
                'patterns': [r'详情|详细|具体|detail'],
                'actions': ['detail', 'get']
            }
        }
        
        # 匹配意图
        for intent_type, config in intent_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent_type, config['actions'][0]
        
        # 默认为搜索意图
        return 'SEARCH', 'find'
    
    def _identify_target_type(self, text: str, entities: List[QueryEntity]) -> str:
        """识别目标类型"""
        # 基于实体判断
        has_file_entity = any(e.entity_type.startswith('FILE_') for e in entities)
        has_equipment_entity = any(e.entity_type.startswith('EQUIPMENT_') for e in entities)
        
        # 基于关键词判断
        doc_keywords = r'文档|文件|报告|手册|记录|资料|说明|document'
        asset_keywords = r'设备|资产|硬件|主机|服务器|asset|equipment'
        
        has_doc_keyword = bool(re.search(doc_keywords, text, re.IGNORECASE))
        has_asset_keyword = bool(re.search(asset_keywords, text, re.IGNORECASE))
        
        # 决策逻辑
        if (has_file_entity or has_doc_keyword) and not (has_equipment_entity or has_asset_keyword):
            return 'documents'
        elif (has_equipment_entity or has_asset_keyword) and not (has_file_entity or has_doc_keyword):
            return 'assets'
        else:
            return 'mixed'
    
    def _extract_filters(self, text: str, entities: List[QueryEntity]) -> Dict[str, Any]:
        """提取过滤条件"""
        filters = {}
        
        # 基于实体提取过滤条件
        for entity in entities:
            if entity.entity_type.startswith('STATUS_'):
                filters.setdefault('status', []).append(entity.text)
            elif entity.entity_type.startswith('FILE_'):
                filters.setdefault('file_types', []).append(entity.text.lower())
            elif entity.entity_type.startswith('EQUIPMENT_'):
                filters.setdefault('asset_types', []).append(entity.text)
            elif entity.entity_type.startswith('LOCATION_'):
                filters.setdefault('locations', []).append(entity.text)
        
        return filters
    
    def _extract_sort_criteria(self, text: str) -> Optional[str]:
        """提取排序条件"""
        sort_patterns = {
            r'按时间|时间.*排序|最新|newest|latest': 'date_desc',
            r'最早|oldest|按创建时间': 'date_asc',
            r'按访问|热门|popular|访问量': 'views_desc',
            r'按名称|名称.*排序|alphabetical': 'name_asc',
            r'按大小|大小.*排序': 'size_desc'
        }
        
        for pattern, sort_type in sort_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return sort_type
        
        return None
    
    def _extract_time_constraints(self, text: str) -> Optional[Dict[str, datetime]]:
        """提取时间约束"""
        now = datetime.now()
        
        time_mappings = {
            r'今天|今日': (now.replace(hour=0, minute=0, second=0, microsecond=0), now),
            r'昨天|昨日': (now - timedelta(days=1), now - timedelta(days=1) + timedelta(hours=23, minutes=59)),
            r'本周|这周': (now - timedelta(days=now.weekday()), now),
            r'上周': (now - timedelta(days=now.weekday() + 7), now - timedelta(days=now.weekday())),
            r'本月|这个月': (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0), now),
            r'今年|本年': (now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0), now)
        }
        
        for pattern, (start, end) in time_mappings.items():
            if re.search(pattern, text):
                return {'start': start, 'end': end}
        
        return None
    
    def _calculate_confidence(self, text: str, entities: List[QueryEntity]) -> float:
        """计算整体置信度"""
        base_confidence = 0.5
        
        # 基于实体数量和质量调整
        if entities:
            entity_confidence = sum(e.confidence for e in entities) / len(entities)
            base_confidence = (base_confidence + entity_confidence) / 2
        
        # 基于查询长度调整
        word_count = len(text.split())
        if word_count >= 3:
            base_confidence += 0.1
        if word_count >= 5:
            base_confidence += 0.1
        
        # 基于结构化程度调整
        if any(char in text for char in '？?！!'):
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def _load_stop_words(self) -> set:
        """加载停用词"""
        return {
            '的', '是', '在', '有', '和', '与', '或', '但', '而', '了', '着', '过', '来', '去',
            '给', '把', '被', '让', '使', '由', '为', '从', '到', '向', '往', '对', '关于',
            '查找', '搜索', '寻找', '找', '显示', '列出', '获取', '查看', '我要', '我想',
            '请', '帮我', '帮助', '什么', '哪些', '怎么', '如何', '那个', '这个', '那些', '这些'
        }
    
    def _load_entity_patterns(self) -> Dict:
        """加载实体识别模式"""
        # 这里可以扩展更复杂的模式
        return {}
    
    def _load_intent_patterns(self) -> Dict:
        """加载意图识别模式"""
        # 这里可以扩展更复杂的意图模式
        return {}
    
    def _load_synonyms(self) -> Dict:
        """加载同义词字典"""
        return {
            '文档': ['文件', '资料', '档案', '材料'],
            '设备': ['装置', '器材', '硬件', '设施'],
            '服务器': ['主机', '服务机', 'server'],
            '正常': ['运行', '活跃', '健康', 'active'],
            '异常': ['故障', '错误', '问题', 'error']
        }
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """基于NLP分析生成查询建议"""
        suggestions = []
        
        # 基于部分查询生成建议
        if len(partial_query.strip()) >= 2:
            # 添加常见查询模式
            suggestions.extend([
                f"查找{partial_query}相关文档",
                f"显示{partial_query}设备状态", 
                f"搜索{partial_query}的详细信息",
                f"列出所有{partial_query}",
                f"最新的{partial_query}记录"
            ])
        
        return suggestions[:5]
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        """分析查询复杂度"""
        word_count = len(query.split())
        has_time = bool(re.search(r'今天|昨天|本周|最近', query))
        has_condition = bool(re.search(r'并且|或者|除了|不包括', query))
        has_sort = bool(re.search(r'排序|最新|最早|按.*排', query))
        
        complexity_score = 0
        if word_count > 5:
            complexity_score += 1
        if has_time:
            complexity_score += 1  
        if has_condition:
            complexity_score += 2
        if has_sort:
            complexity_score += 1
        
        if complexity_score >= 4:
            complexity = "complex"
        elif complexity_score >= 2:
            complexity = "moderate"
        else:
            complexity = "simple"
        
        return {
            "complexity": complexity,
            "score": complexity_score,
            "word_count": word_count,
            "has_time_constraint": has_time,
            "has_conditional_logic": has_condition,
            "has_sort_requirement": has_sort
        }


# 全局实例
nlp_processor = ChineseNLPProcessor()