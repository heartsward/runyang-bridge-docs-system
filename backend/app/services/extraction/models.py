"""
提取结果数据模型

双产物：
- markdown: 用于前端预览（人类可读）
- json_data: 用于搜索/Q&A/AI Wiki（机器可读）
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ExtractionResult:
    """文档提取结果"""

    # 预览用的 Markdown 内容（人类可读）
    markdown: str = ""

    # 结构化 JSON（机器可读，用于搜索/Q&A/AI Wiki）
    # 结构示例：
    # {
    #   "format": "xlsx",
    #   "sheets": [
    #     {"name": "Sheet1", "rows": [...], "merged_cells": [...]},
    #   ],
    #   "metadata": {...},
    # }
    json_data: Dict[str, Any] = field(default_factory=dict)

    # 提取过程中的警告（不致命）
    warnings: List[str] = field(default_factory=list)

    # 错误信息（如有，markdown 字段会为空）
    error: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return bool(self.markdown) and not self.error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "markdown": self.markdown,
            "json_data": self.json_data,
            "warnings": self.warnings,
            "error": self.error,
            "is_success": self.is_success,
        }