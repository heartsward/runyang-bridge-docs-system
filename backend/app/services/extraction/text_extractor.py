"""
文本类文件提取器

设计：
- .md 文件：原样保留（已是 Markdown）
- 其他文本：包成 ``` 围栏的代码块，避免 Markdown 特殊字符被渲染
- 强制 UTF-8 读取（中文 Windows GBK 容错）
- 清理 NUL、控制字符
"""
import logging
from pathlib import Path
from typing import Tuple, Dict, Any

from .base import BaseExtractor
from .models import ExtractionResult

logger = logging.getLogger(__name__)


# 已是 Markdown 格式的文件扩展名
MARKDOWN_EXTS = {".md", ".markdown"}


class TextExtractor(BaseExtractor):
    SUPPORTED_EXTENSIONS = [
        ".txt", ".md", ".csv", ".json", ".xml", ".yml", ".yaml",
        ".log", ".conf", ".cfg", ".ini", ".properties", ".env",
        ".py", ".js", ".ts", ".html", ".css", ".sql",
        ".markdown",
    ]

    def extract(self, file_path: str) -> ExtractionResult:
        try:
            self._check_file(file_path)
        except FileNotFoundError as e:
            return ExtractionResult(error=str(e))

        ext = Path(file_path).suffix.lower()
        is_markdown = ext in MARKDOWN_EXTS

        # 尝试多种编码
        text = self._read_with_fallback(file_path)
        if text is None:
            return ExtractionResult(error="无法解码文本文件")

        # 清理 NUL 字符
        text = text.replace("\x00", "")
        # 控制字符清理（保留 \t \n \r）
        text = "".join(
            ch for ch in text
            if ord(ch) >= 32 or ch in "\t\n\r"
        )

        if is_markdown:
            markdown = text
        else:
            # 包装成代码块（避免特殊字符被渲染）
            lang = ext.lstrip(".") if ext else ""
            markdown = f"```{lang}\n{text}\n```"

        return ExtractionResult(
            markdown=markdown,
            json_data={
                "format": "text",
                "extension": ext,
                "is_markdown": is_markdown,
                "char_count": len(text),
                "line_count": text.count("\n") + 1,
            },
        )

    @staticmethod
    def _read_with_fallback(file_path: str) -> str | None:
        """依次尝试 UTF-8 BOM / UTF-8 / GBK / Latin-1"""
        encodings = ["utf-8-sig", "utf-8", "gbk", "gb18030", "latin-1"]
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                return None
        # 最后用 errors='replace'
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return None