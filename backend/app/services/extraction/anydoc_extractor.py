# -*- coding: utf-8 -*-
"""
anydoc 提取器（阶段十九·19.1）

纯 Rust 文档转换器（firecrawl/anydoc）：14 种 office/PDF 格式 → 干净 GFM Markdown，
中位 <5ms，无外部进程依赖（替代旧 LibreOffice soffice 链路）。

支持的扩展名（anydoc 0.2.x 全量）：
  Word:       .doc .docx .docm
  PowerPoint: .ppt .pps .pot .pptx .pptm .ppsx .ppsm
  Excel:      .xls .xlsx .xlsm .xlsb
  OpenDoc:    .odt .ods .odp
  其他:       .rtf .epub .csv .pdf

行为约定：
- 成功 → ExtractionResult(markdown=..., json_data={format, engine:"anydoc", char_count})
- 失败/空/极短 → ExtractionResult(error=...)，**不抛异常**，由 router 决定降级路径
  （PDF 空内容通常 = 扫描件 → 降级多模态 AI；office 失败 → 降级本地引擎安全网）
"""
import logging
import time
from pathlib import Path
from typing import List

from .base import BaseExtractor
from .models import ExtractionResult

logger = logging.getLogger(__name__)

try:
    import anydoc as _anydoc
    ANYDOC_AVAILABLE = True
except ImportError:
    _anydoc = None
    ANYDOC_AVAILABLE = False

# 低于此字数视为"空内容"（扫描件 PDF 文本层提取不出东西时的典型表现）
MIN_CONTENT_LEN = 20


class AnyDocExtractor(BaseExtractor):
    """anydoc 统一文档提取器（阶段十九：所有文档格式的首选引擎）"""

    SUPPORTED_EXTENSIONS: List[str] = [
        # Word
        ".doc", ".docx", ".docm",
        # PowerPoint
        ".ppt", ".pps", ".pot", ".pptx", ".pptm", ".ppsx", ".ppsm",
        # Excel
        ".xls", ".xlsx", ".xlsm", ".xlsb",
        # OpenDocument
        ".odt", ".ods", ".odp",
        # 其他
        ".rtf", ".epub", ".csv", ".pdf",
    ]

    def extract(self, file_path: str) -> ExtractionResult:
        if not ANYDOC_AVAILABLE:
            return ExtractionResult(
                error="anydoc 未安装（pip install firecrawl-anydoc）"
            )
        try:
            path_str = self._check_file(file_path)  # 返回 str
        except FileNotFoundError as e:
            return ExtractionResult(error=str(e))
        path = Path(path_str)

        ext = path.suffix.lower().lstrip(".")
        t0 = time.time()
        try:
            md = _anydoc.to_markdown(path_str)
        except Exception as e:
            logger.warning(f"[AnyDoc] 转换失败 {path.name}: {type(e).__name__}: {e}")
            return ExtractionResult(
                error=f"anydoc 转换失败: {e}",
                json_data={"format": ext, "engine": "anydoc"},
            )

        md = (md or "").strip()
        elapsed_ms = (time.time() - t0) * 1000

        if len(md) < MIN_CONTENT_LEN:
            # 空/极短内容：PDF 多为扫描件（需 OCR），office 文件可能加密/损坏
            logger.info(
                f"[AnyDoc] 内容为空（{len(md)} 字），判定失败以便降级: {path.name}"
            )
            return ExtractionResult(
                error=f"anydoc 提取内容为空（{len(md)} 字），需降级处理",
                json_data={
                    "format": ext,
                    "engine": "anydoc",
                    "empty": True,
                },
            )

        logger.info(f"[AnyDoc] {path.name} → {len(md)} 字符 ({elapsed_ms:.1f}ms)")
        return ExtractionResult(
            markdown=md,
            json_data={
                "format": ext,
                "engine": "anydoc",
                "char_count": len(md),
                "elapsed_ms": round(elapsed_ms, 1),
            },
        )
