"""
提取器抽象基类
"""
import logging
from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from .models import ExtractionResult

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """
    所有格式提取器的基类

    实现 extract() 时应：
    1. 优先输出 Markdown（用于前端预览）
    2. 同时输出结构化 JSON（用于 AI Wiki / Q&A）
    3. 错误不致命时写入 warnings，致命错误设置 error 字段
    """

    # 该 extractor 支持的文件扩展名（小写，含点）
    SUPPORTED_EXTENSIONS: List[str] = []

    def can_handle(self, file_path: str) -> bool:
        """检查是否能处理此文件"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS

    @abstractmethod
    def extract(self, file_path: str) -> ExtractionResult:
        """
        提取文件内容

        Returns:
            ExtractionResult: 含 markdown + json_data
        """
        raise NotImplementedError

    @staticmethod
    def _check_file(file_path: str) -> str:
        """
        校验文件存在并返回绝对路径

        Raises:
            FileNotFoundError
        """
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        return str(p.resolve())