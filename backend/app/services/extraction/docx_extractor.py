"""
DOCX/DOC 提取器 —— 用 python-docx 直读文档结构

设计：
1. 遍历 paragraphs（标题/正文/列表）
2. 遍历 tables（按 Markdown GFM 输出）
3. 标题用 paragraph.style.name 判断 Heading 1/2/3
4. 列表用 paragraph.style.name 判断 List Paragraph
5. 同时输出结构化 JSON（标题、段落、表格分块）
"""
import logging
from typing import List, Dict, Any, Tuple

from .base import BaseExtractor
from .models import ExtractionResult

logger = logging.getLogger(__name__)

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DocxExtractor(BaseExtractor):
    SUPPORTED_EXTENSIONS = [".docx"]

    def extract(self, file_path: str) -> ExtractionResult:
        if not DOCX_AVAILABLE:
            return ExtractionResult(error="python-docx 未安装")

        try:
            self._check_file(file_path)
        except FileNotFoundError as e:
            return ExtractionResult(error=str(e))

        try:
            if file_path.lower().endswith(".doc"):
                return self._extract_doc_legacy(file_path)

            doc = docx.Document(file_path)
            return self._process_document(doc)
        except Exception as e:
            logger.exception(f"DocxExtractor 失败: {file_path}")
            return ExtractionResult(error=f"DOCX 解析失败: {e}")

    def _extract_doc_legacy(self, file_path: str) -> ExtractionResult:
        """旧 .doc 格式需要 LibreOffice 转 docx 或 antiword；这里 fallback"""
        try:
            import subprocess, tempfile
            from pathlib import Path
            with tempfile.TemporaryDirectory() as tmpdir:
                # 用 LibreOffice 转 .doc → .docx
                subprocess.run([
                    "soffice", "--headless", "--convert-to", "docx",
                    "--outdir", tmpdir, file_path
                ], check=True, capture_output=True, timeout=60)
                converted = list(Path(tmpdir).glob("*.docx"))
                if converted:
                    doc = docx.Document(str(converted[0]))
                    return self._process_document(doc)
                return ExtractionResult(error=".doc 转 .docx 失败")
        except Exception as e:
            return ExtractionResult(error=f".doc 解析失败: {e}")

    def _process_document(self, doc) -> ExtractionResult:
        """处理 python-docx Document 对象"""
        blocks: List[Dict[str, Any]] = []
        parts: List[str] = []

        # 按文档顺序遍历段落和表格
        body = doc.element.body
        for child in body.iterchildren():
            if child.tag.endswith("}p"):
                # 段落
                para = None
                for p in doc.paragraphs:
                    if p._element is child:
                        para = p
                        break
                if para is None:
                    continue
                md, block = self._parse_paragraph(para)
                if md:
                    parts.append(md)
                    blocks.append(block)
            elif child.tag.endswith("}tbl"):
                # 表格
                tbl = None
                for t in doc.tables:
                    if t._element is child:
                        tbl = t
                        break
                if tbl is None:
                    continue
                md, block = self._parse_table(tbl)
                parts.append(md)
                blocks.append(block)

        return ExtractionResult(
            markdown="\n\n".join(parts),
            json_data={
                "format": "docx",
                "block_count": len(blocks),
                "blocks": blocks,
            },
        )

    @staticmethod
    def _parse_paragraph(para) -> Tuple[str, Dict[str, Any]]:
        """解析段落：标题/正文/列表"""
        text = para.text.strip()
        if not text:
            return "", {"type": "empty"}

        style_name = para.style.name if para.style else ""
        block: Dict[str, Any] = {"type": "paragraph", "text": text, "style": style_name}

        # 标题
        if style_name.startswith("Heading"):
            try:
                level = int(style_name.replace("Heading ", "").strip())
                level = min(max(level, 1), 6)
            except ValueError:
                level = 1
            md = f"{'#' * level} {text}"
            block["type"] = "heading"
            block["level"] = level
            return md + "\n", block

        # 中文编号章节识别（一是/二是/三是... 或 一、二、三、...）
        import re
        if re.match(r"^[一二三四五六七八九十]+、", text) or re.match(r"^[一二三四五六七八九十]+是", text):
            md = f"## {text}"
            block["type"] = "heading"
            block["level"] = 2
            block["detected_by"] = "chinese_number"
            return md + "\n", block

        # 列表
        if "List" in style_name or text.startswith(("• ", "- ", "* ")):
            # 简化处理：移除 bullet 字符
            clean = text.lstrip("•-* ").strip()
            md = f"- {clean}"
            block["type"] = "list"
            return md + "\n", block

        # 普通段落
        md = text + "\n"
        return md, block

    @staticmethod
    def _parse_table(tbl) -> Tuple[str, Dict[str, Any]]:
        """解析表格：Markdown GFM 表格"""
        if not tbl.rows:
            return "", {"type": "table", "rows": []}

        rows_data: List[List[str]] = []
        for row in tbl.rows:
            cells = []
            for cell in row.cells:
                # 单元格可能含换行，替换为 <br> 或空格
                cell_text = cell.text.replace("\n", " ").replace("|", "\\|").strip()
                cells.append(cell_text)
            rows_data.append(cells)

        if not rows_data:
            return "", {"type": "table", "rows": []}

        col_count = max(len(r) for r in rows_data)
        lines = []
        # 表头
        header = "| " + " | ".join(rows_data[0]) + " |"
        if len(rows_data[0]) < col_count:
            header = header.rstrip(" |") + " |" + " |".join([""] * (col_count - len(rows_data[0]))) + " |"
        lines.append(header)
        lines.append("| " + " | ".join(["---"] * col_count) + " |")
        # 数据行
        for row in rows_data[1:]:
            cells = row[:]
            if len(cells) < col_count:
                cells.extend([""] * (col_count - len(cells)))
            lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines) + "\n", {
            "type": "table",
            "rows": rows_data,
            "row_count": len(rows_data),
        }