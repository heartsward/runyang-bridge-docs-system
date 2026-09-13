"""
提取路由器：按文件扩展名分发到对应 extractor

新架构入口（阶段 3A）：
- XLSX/XLS → XlsxExtractor（openpyxl 直读，**关键改进：修错位**）
- DOCX/DOC → DocxExtractor（python-docx 直读）
- 文本类 (.txt/.md/.csv/.json/...) → TextExtractor
- PDF → PdfExtractor（LibreOffice + 后处理）
- 图片 → ImageExtractor（OCR）
- 兜底 → 旧 SearchService.extract_file_content
"""
import logging
from typing import Optional
from pathlib import Path

from .models import ExtractionResult
from .base import BaseExtractor
from .xlsx_extractor import XlsxExtractor
from .docx_extractor import DocxExtractor
from .text_extractor import TextExtractor
from .pdf_extractor import PdfExtractor
from .image_extractor import ImageExtractor

logger = logging.getLogger(__name__)


class ExtractionRouter:
    """文件格式路由器"""

    def __init__(self):
        self._extractors: list[BaseExtractor] = [
            XlsxExtractor(),
            DocxExtractor(),
            TextExtractor(),
            PdfExtractor(),
            ImageExtractor(),
        ]

    def extract(self, file_path: str) -> ExtractionResult:
        """
        按扩展名分发到对应 extractor

        阶段四：不再 fallback 到旧管线（旧 LibreOffice 管线已删除）。
        阶段十三：AI_ALL_FORMATS_AI=true 时，**所有格式**（含 docx/xlsx/txt）都先用
                 本地引擎拿到一份文本表示，再交给统一 AI 整理为最终 Markdown；
                 AI 失败按 AI_FALLBACK_TO_LOCAL 决定是否回退到本地结果。
        PDF/图片：其自身 extractor 内部已做"AI 优先 + 降级"，路由器不再二次套 AI，
                 直接走本地分发（保持既有行为不变）。
        """
        # 找到能处理的 extractor
        extractor = self._find_extractor(file_path)
        if extractor is None:
            return ExtractionResult(
                error=f"没有 extractor 支持该文件: {Path(file_path).suffix}",
            )

        # PDF/图片 走原路径（其内部已含 AI 优先 + 降级）
        is_image_format = type(extractor).__name__ in ("PdfExtractor", "ImageExtractor")
        if is_image_format:
            logger.info(f"[ExtractionRouter] 使用 {type(extractor).__name__}: {file_path}")
            return self._run_local(extractor, file_path)

        from app.core.config import settings
        all_formats = getattr(settings, "AI_ALL_FORMATS_AI", False)
        ai_enabled = getattr(settings, "AI_SERVICE_ENABLED", False)

        # 全格式 AI 开启：本地引擎先出一份 md（作为 AI 输入 + 降级兜底），再让 AI 规整
        if all_formats and ai_enabled:
            logger.info(f"[ExtractionRouter] 全格式 AI 模式: 本地引擎 → AI 规整: {file_path}")
            local_result = self._run_local(extractor, file_path)
            if local_result.is_success:
                ai_result = self._refine_with_ai(local_result, extractor, file_path)
                if ai_result is not None:
                    return ai_result
                # AI 失败：fallback 开关决定回退本地 or 报错
                if not getattr(settings, "AI_FALLBACK_TO_LOCAL", True):
                    return ExtractionResult(
                        error="AI 提取失败且已禁用本地降级",
                        json_data={"format": (local_result.json_data or {}).get("format")},
                    )
                logger.info(f"[ExtractionRouter] AI 失败，回退本地引擎: {file_path}")
                return local_result
            # 本地引擎也失败 → 直接返回本地错误
            return local_result

        logger.info(f"[ExtractionRouter] 使用 {type(extractor).__name__}: {file_path}")
        return self._run_local(extractor, file_path)

    def _run_local(self, extractor: "BaseExtractor", file_path: str) -> ExtractionResult:
        """跑本地引擎（原分发逻辑，保留异常兜底）"""
        try:
            return extractor.extract(file_path)
        except Exception as e:
            logger.exception(f"[ExtractionRouter] {type(extractor).__name__} 抛异常: {e}")
            return ExtractionResult(error=f"提取异常 ({type(extractor).__name__}): {e}")

    def _refine_with_ai(
        self,
        local_result: ExtractionResult,
        extractor: "BaseExtractor",
        file_path: str,
    ) -> Optional[ExtractionResult]:
        """阶段十三：把本地引擎已提取的 Markdown 交给统一 AI 整理/规整。

        返回:
          - ExtractionResult（AI 成功，engine=unified-ai）
          - None（AI 未启用/失败 → 调用方按 fallback 开关决定回退本地）
        """
        try:
            from app.services.extraction.ai_client import get_unified_ai_client
            client = get_unified_ai_client()
            if not client.is_enabled():
                return None
            md, error = client.parse_text(local_result.markdown)
            if md:
                fmt = (local_result.json_data or {}).get("format", Path(file_path).suffix.lstrip("."))
                return ExtractionResult(
                    markdown=md,
                    json_data={
                        "format": fmt,
                        "engine": "unified-ai",
                        "ai_provider": client.provider,
                        "ai_model": client.model,
                        "char_count": len(md),
                    },
                )
            logger.warning(f"[ExtractionRouter] 全格式 AI 规整失败: {error}")
        except Exception as e:
            logger.exception(f"[ExtractionRouter] 全格式 AI 规整异常: {e}")
        return None

    def _find_extractor(self, file_path: str) -> Optional[BaseExtractor]:
        for ext in self._extractors:
            if ext.can_handle(file_path):
                return ext
        return None