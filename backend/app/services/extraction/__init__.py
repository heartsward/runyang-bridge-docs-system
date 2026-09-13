"""
文档内容提取服务（新架构）

按 VIBE_CODING_GUIDE.md 阶段 3A 设计：
- 按文件格式分发到不同 extractor
- 每个 extractor 输出 Markdown + 结构化 JSON
- Markdown 用于前端预览；JSON 用于搜索/Q&A/AI Wiki
"""
from .models import ExtractionResult
from .base import BaseExtractor
from .router import ExtractionRouter

__all__ = [
    "ExtractionResult",
    "BaseExtractor",
    "ExtractionRouter",
]