"""
Wiki MD 副本存储（阶段十）

每个上传的文档在 `backend/wiki/{doc_id}.md` 保存一份 Markdown 副本，
包含 frontmatter（标题/标签/关联）和正文内容。
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Wiki 副本目录（与代码同树，方便备份）
# storage.py 路径：backend/app/services/wiki/storage.py
# parent.parent.parent.parent = backend/
WIKI_DIR = Path(__file__).parent.parent.parent.parent / "wiki"


def build_frontmatter(
    title: str,
    source_file: str,
    doc_type: str,
    tags: List[str],
    related: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """构建 YAML frontmatter"""
    meta: Dict[str, Any] = {
        "title": title,
        "source_file": source_file,
        "doc_type": doc_type,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
        "tags": tags,
        "related": related or [],
    }
    if extra:
        meta.update(extra)
    yaml_str = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)
    return f"---\n{yaml_str}---\n\n"


def sanitize_title(raw: str) -> str:
    """清理标题（去前后空格、限制长度）"""
    if not raw:
        return ""
    raw = raw.strip()
    # 去掉文件扩展名
    raw = re.sub(r"\.[a-zA-Z0-9]+$", "", raw)
    return raw[:80]


def derive_fallback_tags(filename: str, content: str) -> List[str]:
    """AI 失败时的启发式标签"""
    tags: List[str] = []
    # 文件名中的关键词（简单规则）
    name = filename.lower()
    if "网络安全" in filename or "安全" in filename:
        tags.append("网络安全")
    if "网络拓扑" in filename or "拓扑" in filename:
        tags.append("网络拓扑")
    if "ip" in name or "地址" in filename:
        tags.append("IP地址")
    if "监控" in filename:
        tags.append("监控")
    if "收费" in filename:
        tags.append("收费")
    if "办公" in filename:
        tags.append("办公网")
    if "docx" in filename or filename.endswith(".doc"):
        tags.append("Word 文档")
    if "xlsx" in filename or filename.endswith(".xls"):
        tags.append("Excel 表格")
    if "pdf" in filename:
        tags.append("PDF 文档")
    if "md" in filename:
        tags.append("Markdown")
    if "png" in filename or "jpg" in filename or "jpeg" in filename:
        tags.append("图片")
    # 兜底
    if not tags:
        tags.append("未分类")
    return tags[:5]


class WikiStorage:
    """MD 副本存储管理"""

    def __init__(self, wiki_dir: Path = WIKI_DIR):
        self.wiki_dir = Path(wiki_dir)
        self.wiki_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, doc_id: int) -> Path:
        return self.wiki_dir / f"{doc_id}.md"

    def exists(self, doc_id: int) -> bool:
        return self.get_path(doc_id).exists()

    def read(self, doc_id: int) -> Optional[str]:
        """读取 MD 副本（如不存在返回 None）"""
        p = self.get_path(doc_id)
        if not p.exists():
            return None
        try:
            return p.read_text(encoding="utf-8")
        except Exception as e:
            logger.exception(f"读取 wiki MD 副本失败 {p}: {e}")
            return None

    def write(
        self,
        doc_id: int,
        title: str,
        source_file: str,
        doc_type: str,
        tags: List[str],
        markdown_body: str,
        related: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """写入 MD 副本（含 frontmatter）"""
        path = self.get_path(doc_id)
        frontmatter = build_frontmatter(
            title=title,
            source_file=source_file,
            doc_type=doc_type,
            tags=tags,
            related=related,
            extra=extra,
        )
        # 用 heading # 作为正文标题（markdown 渲染更清晰）
        heading_line = f"# {title}\n\n" if title else ""
        full_content = frontmatter + heading_line + markdown_body.strip() + "\n"
        path.write_text(full_content, encoding="utf-8")
        logger.info(f"已写入 MD 副本: {path} ({len(full_content)} chars)")
        return path

    def update(
        self,
        doc_id: int,
        new_markdown_body: str,
    ) -> Optional[Path]:
        """更新 MD 副本（用户从预览编辑器保存时调用）

        保留原 frontmatter，只替换正文（heading 之后）。
        如 MD 不存在返回 None。
        """
        path = self.get_path(doc_id)
        if not path.exists():
            return None
        existing = path.read_text(encoding="utf-8")
        # 提取 frontmatter（保留）
        m = re.match(r"^---\n(.*?)\n---\n", existing, re.DOTALL)
        if not m:
            # 旧文件无 frontmatter，覆盖写
            frontmatter = ""
        else:
            frontmatter = existing[: m.end()]

        # 保留 heading
        body_match = re.search(r"^#\s+.+\n+", new_markdown_body, re.MULTILINE)
        if body_match:
            heading = new_markdown_body[: body_match.end()]
            rest = new_markdown_body[body_match.end():]
        else:
            heading = ""
            rest = new_markdown_body

        path.write_text(frontmatter + heading + rest, encoding="utf-8")
        logger.info(f"已更新 MD 副本: {path}")
        return path

    def list_all(self) -> List[Path]:
        """列出所有 MD 副本"""
        return sorted(self.wiki_dir.glob("*.md"))

    def delete(self, doc_id: int) -> bool:
        """删除 MD 副本"""
        p = self.get_path(doc_id)
        if p.exists():
            try:
                p.unlink()
                return True
            except Exception as e:
                logger.exception(f"删除 MD 副本失败 {p}: {e}")
                return False
        return False