# -*- coding: utf-8 -*-
"""
AI文档分析器
使用AI分析文档内容、提取摘要、关键词等
"""
from typing import List, Dict, Any, Optional
from ..ai_service import ai_service, AIMessage, AIResponse
from ..ai_config import ai_config
import json
import logging

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """AI文档分析器"""
    
    def __init__(self):
        self.ai_service = ai_service
    
    async def analyze_document(
        self,
        title: str,
        content: str,
        analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """
        分析文档
        
        Args:
            title: 文档标题
            content: 文档内容
            analysis_type: 分析类型 (full, summary, keywords, classification)
        
        Returns:
            分析结果
        """
        
        analysis_map = {
            "full": self._full_analysis,
            "summary": self._extract_summary,
            "keywords": self._extract_keywords,
            "classification": self._classify_document
        }
        
        analyzer = analysis_map.get(analysis_type, self._full_analysis)
        return await analyzer(title, content)
    
    async def _full_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """完整分析"""
        prompt = f"""请分析以下文档，提取以下信息：

文档标题：{title}

文档内容：
{content[:15000]}

请提取以下信息，以JSON格式返回：
{{
  "summary": "文档摘要（200字以内）",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "category": "分类（运维文档、技术文档、设备文档、配置文档、培训文档、其他）",
  "tags": ["标签1", "标签2"],
  "important_points": ["重要要点1", "重要要点2"],
  "related_topics": ["相关主题1", "相关主题2"]
}}"""
        
        messages = [AIMessage(role="user", content=prompt)]
        from ..ai_config import AIProvider
        response: AIResponse = await self.ai_service.chat(messages)
        
        if response.success:
            try:
                return json.loads(response.content)
            except:
                pass
        
        return self._default_analysis(title, content)
    
    async def _extract_summary(self, title: str, content: str) -> Dict[str, Any]:
        """提取摘要"""
        prompt = f"""请为以下文档生成一个简短的摘要（100-150字）：

标题：{title}
内容：{content[:8000]}

直接输出摘要内容，不要包含其他文字。"""
        
        messages = [AIMessage(role="user", content=prompt)]
        response: AIResponse = await self.ai_service.chat(messages, max_tokens=300)
        
        return {
            "summary": response.content if response.success else "",
            "success": response.success
        }
    
    async def _extract_keywords(self, title: str, content: str) -> Dict[str, Any]:
        """提取关键词"""
        prompt = f"""从以下文档中提取5-8个关键词：

标题：{title}
内容：{content[:5000]}

以JSON数组格式返回：["关键词1", "关键词2", "关键词3", ...]"""
        
        messages = [AIMessage(role="user", content=prompt)]
        response: AIResponse = await self.ai_service.chat(messages, max_tokens=200)
        
        if response.success:
            try:
                keywords = json.loads(response.content)
                return {"keywords": keywords if isinstance(keywords, list) else []}
            except:
                pass
        
        return {"keywords": []}
    
    async def _classify_document(self, title: str, content: str) -> Dict[str, Any]:
        """文档分类"""
        prompt = f"""将以下文档分类到以下类别之一：
- 运维文档
- 技术文档
- 设备文档
- 配置文档
- 培训文档
- 其他

标题：{title}
内容：{content[:3000]}

只返回类别名称，不要其他文字。"""
        
        messages = [AIMessage(role="user", content=prompt)]
        response: AIResponse = await self.ai_service.chat(messages, max_tokens=50)
        
        return {
            "category": response.content.strip() if response.success else "其他",
            "confidence": 0.9 if response.success else 0.0
        }
    
    def _default_analysis(self, title: str, content: str) -> Dict[str, Any]:
        """默认分析（降级方法）"""
        return {
            "summary": content[:200] if content else "",
            "keywords": self._simple_keywords(content),
            "category": "其他",
            "tags": [],
            "important_points": [],
            "related_topics": []
        }
    
    def _simple_keywords(self, text: str) -> List[str]:
        """简单关键词提取"""
        # 使用jieba分词提取高频词
        try:
            import jieba
            from collections import Counter
            
            words = jieba.cut(text)
            # 过滤停用词和短词
            stopwords = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '里'}
            
            filtered_words = [w for w in words if len(w) > 1 and w not in stopwords and w.strip()]
            
            # 统计词频
            word_freq = Counter(filtered_words)
            
            # 返回前5个高频词
            return [word for word, _ in word_freq.most_common(5)]
        except:
            return []
