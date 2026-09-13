"""
图片提取器（阶段九：统一 VLM 优先）

改进点：
1. 阶段九：统一多模态 VLM（Qwen3-VL）作为主路径 — OCR + 视觉理解
2. 阶段四：PaddleOCR（本地）作为高速兜底
3. 阶段一：pytesseract 作为最后兜底
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

from .base import BaseExtractor
from .models import ExtractionResult

logger = logging.getLogger(__name__)


class ImageExtractor(BaseExtractor):
    SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg"]

    def __init__(self):
        super().__init__()
        self._paddleocr = None

    def extract(self, file_path: str) -> ExtractionResult:
        try:
            self._check_file(file_path)
        except FileNotFoundError as e:
            return ExtractionResult(error=str(e))

        # 阶段九：统一 VLM 多模态优先（OCR + 视觉理解一体化）
        md, engine, error = self._extract_with_unified_vlm(file_path)
        if md:
            filename = Path(file_path).name
            return ExtractionResult(
                markdown=f"## 图片解析：{filename}\n\n{md.strip()}\n",
                json_data={
                    "format": "image",
                    "filename": filename,
                    "engine": engine,
                    "char_count": len(md),
                },
            )

        # 兜底链：PaddleOCR → tesseract
        logger.info(f"VLM 不可用，降级到 OCR 链: {file_path}")

        from app.core.config import settings
        engine = getattr(settings, 'OCR_ENGINE', 'tesseract')

        if engine == 'paddleocr' or getattr(settings, 'AI_OCR_ENABLED', False):
            text, error = self._extract_with_paddleocr(file_path)
        else:
            text, error = self._extract_with_tesseract(file_path)

        if not text:
            return ExtractionResult(
                error=error or f"VLM/OCR 都失败",
                json_data={"format": "image", "engine": "all_failed", "filename": Path(file_path).name},
            )

        filename = Path(file_path).name
        markdown = f"## 图片 OCR：{filename}（引擎：{engine}）\n\n{text}\n"

        return ExtractionResult(
            markdown=markdown,
            json_data={
                "format": "image",
                "filename": filename,
                "engine": engine,
                "char_count": len(text),
            },
        )

    def _extract_with_unified_vlm(self, file_path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """统一 VLM 多模态（OCR + 视觉理解）"""
        from app.core.config import settings

        if not getattr(settings, 'AI_SERVICE_ENABLED', False):
            return None, None, None

        if not getattr(settings, 'AI_FALLBACK_TO_LOCAL', True):
            # 用户明确不要 fallback，但仍尝试一次 VLM
            try:
                from app.services.extraction.ai_client import get_unified_ai_client
                client = get_unified_ai_client()
                with open(file_path, "rb") as f:
                    img_bytes = f.read()
                md, error = client.vision_parse([img_bytes])
                if md:
                    return md, "unified-ai", None
            except Exception as e:
                logger.exception(f"VLM 调用异常: {e}")
            return None, None, None

        try:
            from app.services.extraction.ai_client import get_unified_ai_client
            client = get_unified_ai_client()
            with open(file_path, "rb") as f:
                img_bytes = f.read()
            md, error = client.vision_parse([img_bytes])
            if md:
                return md, "unified-ai", None
            logger.warning(f"VLM 提取失败: {error}")
            return None, None, error
        except Exception as e:
            logger.exception(f"VLM 调用异常: {e}")
            return None, None, str(e)

    def _extract_with_paddleocr(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """PaddleOCR 提取（远端服务优先，本地兜底）"""
        from app.core.config import settings

        # 阶段五：远端服务优先
        if getattr(settings, 'AI_OCR_ENABLED', False):
            try:
                from app.services.extraction.ai_client import get_ocr_client
                client = get_ocr_client()
                text, error = client.ocr(file_path)
                if text:
                    return text, None
                logger.warning(f"PaddleOCR 远端失败: {error}")
            except Exception as e:
                logger.exception(f"PaddleOCR 远端异常: {e}")

        if not getattr(settings, 'AI_FALLBACK_TO_LOCAL', True):
            return None, "PaddleOCR 远端不可用且未启用本地 fallback"

        # 本地 PaddleOCR
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            return None, "paddleocr 未安装，请 pip install paddleocr paddlepaddle"

        try:
            if self._paddleocr is None:
                lang = getattr(settings, 'PADDLEOCR_LANG', 'ch')
                self._paddleocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

            result = self._paddleocr.ocr(file_path, cls=True)
            text = ""
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) >= 2:
                        text += line[1][0] + "\n"
            return (text.strip() or None, None)
        except Exception as e:
            logger.exception(f"本地 PaddleOCR 失败: {file_path}")
            return None, str(e)

    def _extract_with_tesseract(self, file_path: str) -> Tuple[Optional[str], Optional[str]]:
        """pytesseract 提取（兜底）"""
        try:
            import pytesseract
            from PIL import Image

            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang="chi_sim+eng")
            return (text.strip() or None, None)
        except ImportError:
            return None, "pytesseract/Pillow 未安装"
        except Exception as e:
            return None, str(e)