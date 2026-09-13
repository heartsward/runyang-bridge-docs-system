# -*- coding: utf-8 -*-
"""
提取路由器：按文件扩展名分发到对应 extractor

阶段十九（anydoc 替换 LibreOffice）后的引擎优先级链：

    图片（png/jpg/bmp/webp/gif...）
        → ImageExtractor（多模态 AI 优先 + OCR 兜底，内部已含降级）
    anydoc 支持的 21 个文档格式（doc/docx/xls/xlsx/ppt/odt/rtf/epub/csv/pdf...）
        ① AnyDocExtractor（anydoc，纯 Rust，<5ms，首选）
        ② 失败/空内容 → 降级本地引擎：
             PDF  → PdfExtractor（多模态 AI 优先 + pymupdf 本地兜底）
             其他 → Xlsx/Docx/Text（安全网）
        ③ 本地也失败 → 报错（语义与阶段四起一致）
    anydoc 不覆盖的格式（.txt/.md/.json 等纯文本）
        → 直接本地引擎（TextExtractor）

历史：
- 阶段 3A：按扩展名分发到各 extractor
- 阶段四：删除旧 LibreOffice 管线
- 阶段十三：AI_ALL_FORMATS_AI 全格式 AI 规整（阶段十九起移除——anydoc 输出已是
  高质量 GFM，不再需要"全格式 AI 规整"开关）
- 阶段十九：anydoc 成为所有文档格式首选引擎，LibreOffice 链路彻底退役
"""
import logging
from typing import Optional
from pathlib import Path

from .models import ExtractionResult
from .base import BaseExtractor
from .anydoc_extractor import AnyDocExtractor
from .xlsx_extractor import XlsxExtractor
from .docx_extractor import DocxExtractor
from .text_extractor import TextExtractor
from .pdf_extractor import PdfExtractor
from .image_extractor import ImageExtractor

logger = logging.getLogger(__name__)


class ExtractionRouter:
    """文件格式路由器（anydoc 优先 + 本地引擎安全网 + AI 兜底）"""

    def __init__(self):
        self.anydoc = AnyDocExtractor()
        self._local_extractors: list[BaseExtractor] = [
            XlsxExtractor(),
            DocxExtractor(),
            TextExtractor(),
            PdfExtractor(),
            ImageExtractor(),
        ]

    def extract(self, file_path: str) -> ExtractionResult:
        """图片走 ImageExtractor；其余先 anydoc，失败降级本地引擎（PDF 本地引擎内含多模态 AI 优先）"""
        ext = Path(file_path).suffix.lower()
        local_extractor = self._find_local_extractor(file_path)

        # 1) 图片：anydoc 不处理图片文档，直接走 ImageExtractor（内部含多模态 AI 优先 + OCR 兜底）
        if type(local_extractor).__name__ == "ImageExtractor":
            logger.info(f"[ExtractionRouter] 图片 → ImageExtractor: {file_path}")
            return self._run(local_extractor, file_path)

        # 2) anydoc 支持的文档格式：首选 anydoc
        if self.anydoc.can_handle(file_path):
            anydoc_result = self._run(self.anydoc, file_path)
            if anydoc_result.is_success:
                return anydoc_result
            logger.info(
                f"[ExtractionRouter] anydoc 未成功（{anydoc_result.error}），降级本地引擎: {file_path}"
            )

        # 3) 降级：本地引擎（PDF 的本地引擎内部 = 多模态 AI 优先 + pymupdf 兜底）
        if local_extractor is None:
            return ExtractionResult(error=f"没有 extractor 支持该文件: {ext}")
        logger.info(f"[ExtractionRouter] 降级使用 {type(local_extractor).__name__}: {file_path}")
        return self._run(local_extractor, file_path)

    def _run(self, extractor: "BaseExtractor", file_path: str) -> ExtractionResult:
        """跑一个 extractor（异常兜底，不抛出）"""
        try:
            return extractor.extract(file_path)
        except Exception as e:
            logger.exception(f"[ExtractionRouter] {type(extractor).__name__} 抛异常: {e}")
            return ExtractionResult(error=f"提取异常 ({type(extractor).__name__}): {e}")

    def _find_local_extractor(self, file_path: str) -> Optional[BaseExtractor]:
        """在本地引擎列表里找能处理的 extractor（不含 anydoc）"""
        for ext in self._local_extractors:
            if ext.can_handle(file_path):
                return ext
        return None
