"""
PDF 提取器（阶段七：统一多模态优先）

引擎优先级：
1. 统一多模态 VLM（Ollama qwen3-vl / 在线 DashScope）— 一站式处理所有 PDF
2. pymupdf 文本直读 — 适合纯文本/含数字文本层的 PDF
3. PaddleOCR 兜底 — 适合密集扫描件

特性：
- 章节标题识别（第X章 / Chapter 1 / 1.1 等 8 种模式）→ Markdown # / ##
- 页眉页脚去除（页码模式 + 跨页重复检测）
- 文档元数据提取（标题/作者/创建日期）
- VLM 分块处理（每 5 页一组，避免上下文爆炸）
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from .base import BaseExtractor
from .models import ExtractionResult

logger = logging.getLogger(__name__)

try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


# 章节标题模式（中文 + 英文）
HEADING_PATTERNS = [
    (re.compile(r"^第[一二三四五六七八九十百零\d]+章[\s　　:：]"), 1),
    (re.compile(r"^第[一二三四五六七八九十百零\d]+节[\s　　:：]"), 2),
    (re.compile(r"^[\d]+\.[\d]+(\.[\d]+)?[\s　　]"), 2),
    (re.compile(r"^（[一二三四五六七八九十百零\d]+）[\s　　]"), 3),
    (re.compile(r"^【[^】]+】[\s　　]"), 2),
    (re.compile(r"^第[\d]+章[\s　　:：]"), 1),
    (re.compile(r"^Chapter\s+\d+", re.IGNORECASE), 1),
    (re.compile(r"^Section\s+\d+", re.IGNORECASE), 2),
]

PAGE_NUMBER_PATTERNS = [
    re.compile(r"^\s*-?\s*\d+\s*/\s*\d+\s*-?\s*$"),
    re.compile(r"^\s*第?\s*\d+\s*页\s*$", re.IGNORECASE),
    re.compile(r"^\s*Page\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
]


class PdfExtractor(BaseExtractor):
    SUPPORTED_EXTENSIONS = [".pdf"]
    MAX_PAGES = 500
    VLM_CHUNK_PAGES = 5  # 每组 5 页送 VLM

    def __init__(self):
        super().__init__()
        self._vlm_log = []  # 记录 VLM 调用日志

    def extract(self, file_path: str) -> ExtractionResult:
        if not PYMUPDF_AVAILABLE:
            return ExtractionResult(error="pymupdf 未安装")

        try:
            self._check_file(file_path)
        except FileNotFoundError as e:
            return ExtractionResult(error=str(e))

        from app.core.config import settings
        ai_enabled = getattr(settings, 'AI_SERVICE_ENABLED', False)

        # 阶段七：统一多模态 VLM 优先（如果是 PDF）
        if ai_enabled:
            result = self._extract_with_unified_ai(file_path)
            if result.is_success:
                return result
            logger.warning(f"统一 VLM 失败，降级到 pymupdf: {result.error}")

        # pymupdf 文本直读
        return self._extract_with_pymupdf(file_path)

    def _extract_with_unified_ai(self, file_path: str) -> ExtractionResult:
        """统一多模态 VLM 提取（Ollama qwen3-vl 或 DashScope）"""
        try:
            from app.services.extraction.ai_client import get_unified_ai_client
            client = get_unified_ai_client()
            if not client.is_enabled():
                return ExtractionResult(error="AI_SERVICE_ENABLED=False")

            doc = pymupdf.open(file_path)
            total_pages = min(len(doc), self.MAX_PAGES)
            if len(doc) > self.MAX_PAGES:
                logger.warning(f"PDF 共 {len(doc)} 页，仅处理前 {total_pages} 页")

            metadata = self._extract_metadata(doc)
            chunks_markdown: List[str] = []

            # 分块：每 VLM_CHUNK_PAGES 页一组
            for chunk_start in range(0, total_pages, self.VLM_CHUNK_PAGES):
                chunk_end = min(chunk_start + self.VLM_CHUNK_PAGES, total_pages)
                images = []
                for page_num in range(chunk_start, chunk_end):
                    page = doc.load_page(page_num)
                    # 3x DPI (216 DPI) 保证文字清晰；alpha=False 避免透明背景
                    mat = pymupdf.Matrix(3.0, 3.0)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    images.append(pix.tobytes("png"))

                page_range = f"第 {chunk_start + 1}-{chunk_end} 页"
                md, error = client.vision_parse(images, mime_type="image/png")
                if md:
                    chunks_markdown.append(f"## {page_range}\n\n{md.strip()}\n")
                    logger.info(f"VLM 提取 {page_range} 成功 ({len(md)} chars)")
                else:
                    logger.warning(f"VLM {page_range} 失败: {error}")
                    chunks_markdown.append(f"## {page_range}\n\n[VLM 提取失败：{error}]\n")

            page_count = len(doc)
            doc.close()

            full_markdown = "\n".join(chunks_markdown)
            if not full_markdown.strip():
                return ExtractionResult(error="VLM 返回空 markdown")

            return ExtractionResult(
                markdown=full_markdown,
                json_data={
                    "format": "pdf",
                    "engine": "unified-ai",
                    "ai_provider": client.provider,
                    "ai_model": client.model,
                    "metadata": metadata,
                    "page_count": page_count,
                    "processed_pages": total_pages,
                },
            )
        except Exception as e:
            logger.exception(f"统一 VLM 提取失败: {file_path}")
            return ExtractionResult(error=f"统一 VLM 失败: {e}")

    def _extract_with_pymupdf(self, file_path: str) -> ExtractionResult:
        """pymupdf 文本直读 + 章节识别 + 页眉页脚去除"""
        try:
            doc = pymupdf.open(file_path)
        except Exception as e:
            return ExtractionResult(error=f"打开 PDF 失败: {e}")

        try:
            pages: List[Dict[str, Any]] = []
            full_text_parts: List[str] = []
            metadata = self._extract_metadata(doc)
            warnings: List[str] = []

            total_pages = min(len(doc), self.MAX_PAGES)
            if len(doc) > self.MAX_PAGES:
                warnings.append(f"PDF 共 {len(doc)} 页，仅处理前 {total_pages} 页")

            page_texts: List[str] = []
            for page_num in range(total_pages):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text and text.strip():
                    cleaned = self._clean_page_text(text.strip())
                    page_texts.append(cleaned)
                    pages.append({"page": page_num + 1, "char_count": len(cleaned), "has_text": True})
                else:
                    page_texts.append("")
                    pages.append({"page": page_num + 1, "char_count": 0, "has_text": False})

            # 检测页眉页脚
            header_footer = self._detect_headers_footers(page_texts)
            # 提取章节
            chapters = self._detect_chapters(page_texts)

            for page_idx, text in enumerate(page_texts):
                if not text:
                    continue
                cleaned = self._strip_headers_footers(text, header_footer)
                cleaned = self._apply_chapter_titles(cleaned, chapters, page_idx)
                if cleaned.strip():
                    full_text_parts.append(f"## 第 {page_idx + 1} 页\n\n{cleaned}\n")

            full_markdown = "\n".join(full_text_parts)

            # pymupdf 提取为空时尝试 PaddleOCR
            if not full_markdown.strip():
                logger.info(f"PDF 无文本内容，尝试 PaddleOCR: {file_path}")
                ocr_result = self._extract_with_paddleocr(file_path)
                if ocr_result.is_success:
                    return ocr_result
                warnings.append("pymupdf 与 PaddleOCR 都未提取到内容")
                full_markdown = ocr_result.markdown or ""

            if not full_markdown.strip():
                return ExtractionResult(
                    error="PDF 无可提取文本（可能是扫描件或加密）",
                    json_data={"format": "pdf", "metadata": metadata, "pages": pages},
                    warnings=warnings,
                )

            return ExtractionResult(
                markdown=full_markdown,
                json_data={
                    "format": "pdf",
                    "engine": "pymupdf",
                    "metadata": metadata,
                    "page_count": len(doc),
                    "processed_pages": total_pages,
                    "pages": pages,
                    "chapters": chapters,
                },
                warnings=warnings,
            )
        except Exception as e:
            logger.exception(f"pymupdf 提取失败: {file_path}")
            return ExtractionResult(error=f"PDF 提取失败: {e}")
        finally:
            doc.close()

    def _extract_with_paddleocr(self, file_path: str) -> ExtractionResult:
        """PaddleOCR 兜底（CPU 高速路径）"""
        try:
            from app.services.extraction.ai_client import get_ocr_client
            client = get_ocr_client()
            if not client.is_enabled():
                return ExtractionResult(error="PaddleOCR 未启用且本地 paddleocr 包未装")

            text, error = client.ocr(file_path)
            if text:
                return ExtractionResult(
                    markdown=f"## PDF OCR（远端 PaddleOCR）\n\n{text}\n",
                    json_data={"format": "pdf", "engine": "paddleocr-remote"},
                )
            return ExtractionResult(error=error or "PaddleOCR 返回空")
        except Exception as e:
            return ExtractionResult(error=f"PaddleOCR 失败: {e}")

    # ---- 工具方法（保留：章节识别 / 页眉页脚） ----
    def _extract_metadata(self, doc) -> Dict[str, Any]:
        meta = doc.metadata or {}
        return {
            "title": meta.get("title", "").strip(),
            "author": meta.get("author", "").strip(),
            "subject": meta.get("subject", "").strip(),
            "creator": meta.get("creator", "").strip(),
            "producer": meta.get("producer", "").strip(),
            "creation_date": str(meta.get("creationDate", "")),
            "mod_date": str(meta.get("modDate", "")),
        }

    def _clean_page_text(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    def _is_page_number(self, line: str) -> bool:
        line = line.strip()
        if not line or len(line) > 20:
            return False
        return any(p.match(line) for p in PAGE_NUMBER_PATTERNS)

    def _detect_headers_footers(self, page_texts: List[str]) -> set:
        if not page_texts or len(page_texts) < 3:
            return set()
        first_lines_count, last_lines_count = {}, {}
        threshold = max(3, len(page_texts) * 0.3)
        for text in page_texts:
            if not text:
                continue
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if not lines:
                continue
            for line in lines[:3]:
                first_lines_count[line] = first_lines_count.get(line, 0) + 1
            for line in lines[-3:]:
                last_lines_count[line] = last_lines_count.get(line, 0) + 1
        hf = set()
        for line, cnt in first_lines_count.items():
            if cnt >= threshold and self._is_page_number(line):
                hf.add(line)
        for line, cnt in last_lines_count.items():
            if cnt >= threshold and self._is_page_number(line):
                hf.add(line)
        return hf

    def _strip_headers_footers(self, text: str, hf: set) -> str:
        if not hf:
            return text
        lines = text.split("\n")
        return "\n".join(l for l in lines if l.strip() not in hf)

    def _detect_chapters(self, page_texts: List[str]) -> List[Dict[str, Any]]:
        chapters = []
        current_chapter = None
        chapter_idx = 0
        for page_idx, text in enumerate(page_texts):
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped or len(line_stripped) > 80:
                    continue
                for pattern, level in HEADING_PATTERNS:
                    if pattern.match(line_stripped):
                        if current_chapter:
                            current_chapter["end_page"] = page_idx
                        chapter_idx += 1
                        current_chapter = {
                            "index": chapter_idx, "level": level,
                            "title": line_stripped[:80],
                            "start_page": page_idx + 1, "end_page": page_idx + 1,
                        }
                        chapters.append(current_chapter)
                        break
        if current_chapter:
            current_chapter["end_page"] = len(page_texts)
        return chapters

    def _apply_chapter_titles(self, text: str, chapters, page_idx: int) -> str:
        current_chapter = None
        for ch in chapters:
            if ch["start_page"] <= page_idx + 1 <= ch["end_page"]:
                current_chapter = ch
                break
        if not current_chapter:
            return text
        if current_chapter["start_page"] == page_idx + 1 and current_chapter.get("_inserted") is None:
            marker = "#" * current_chapter["level"]
            text = f"{marker} {current_chapter['title']}\n\n{text}"
            current_chapter["_inserted"] = True
        return text