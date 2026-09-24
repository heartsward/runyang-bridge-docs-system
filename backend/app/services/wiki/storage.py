"""
Wiki MD 副本存储（阶段十）

每个上传的文档在 `backend/wiki/{doc_id}.md` 保存一份 Markdown 副本，
包含 frontmatter（标题/标签/关联）和正文内容。
"""
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# Wiki 副本目录（与代码同树，方便备份）
# storage.py 路径：backend/app/services/wiki/storage.py
# parent.parent.parent.parent = backend/
WIKI_DIR = Path(__file__).parent.parent.parent.parent / "wiki"

# 匹配**文件开头**的一段 YAML frontmatter（非贪婪：遇到第一个结束分隔线就停）
# 兼容 \r\n 与分隔线后的空白；用 \A 锚定开头，避免匹配到正文里的 --- 分隔线
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.DOTALL)


def split_frontmatter(text: str) -> Tuple[str, str]:
    """切成 (frontmatter 原文, 正文)。

    frontmatter 原文含首尾 `---` 分隔线和结尾换行；正文已去掉紧随其后的空行。
    没有 frontmatter 时返回 ("", 原文)。
    """
    text = text or ""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return "", text
    return m.group(0), text[m.end():].lstrip("\r\n")


def strip_frontmatter_blocks(text: str) -> Tuple[str, str]:
    """剥离开头**连续多段** frontmatter，返回 (第一段原文, 纯正文)。

    历史脏数据里同一个文件可能存在多段（保存一次多一段）。正文只保留
    最后一段之后的内容，frontmatter 只认第一段。
    """
    first_fm = ""
    rest = text or ""
    while True:
        fm, body = split_frontmatter(rest)
        if not fm:
            break
        if not first_fm:
            first_fm = fm
        rest = body
    return first_fm, rest


def join_frontmatter(frontmatter: str, body: str) -> str:
    """按统一版式拼回文件：`---\\n<yaml>---\\n\\n<正文>\\n`"""
    body = (body or "").strip("\r\n")
    if not frontmatter:
        return body + "\n" if body else ""
    if not frontmatter.endswith("\n"):
        frontmatter += "\n"
    return f"{frontmatter}\n{body}\n"


def build_frontmatter(
    title: str,
    source_file: str,
    doc_type: str,
    tags: List[str],
    related: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
    doc_category: str = "",
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
    # 阶段十八·18.5：业务分类（受控词表）
    if doc_category:
        meta["doc_category"] = doc_category
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
        doc_category: str = "",
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
            doc_category=doc_category,
        )
        # 用 heading # 作为正文标题（markdown 渲染更清晰）
        heading_line = f"# {title}\n\n" if title else ""
        full_content = frontmatter + heading_line + markdown_body.strip() + "\n"
        path.write_text(full_content, encoding="utf-8")
        logger.info(f"已写入 MD 副本: {path} ({len(full_content)} chars)")
        return path

    def read_body(self, doc_id: int) -> Optional[str]:
        """读取 MD 正文（剥离全部 frontmatter，保留 `# 标题` 行）"""
        content = self.read(doc_id)
        if content is None:
            return None
        _fm, body = strip_frontmatter_blocks(content)
        return body

    def update(
        self,
        doc_id: int,
        new_markdown_body: str,
    ) -> Optional[Path]:
        """更新 MD 副本（用户从预览编辑器保存时调用）

        幂等保证（27.16 修复）：无论传进来的是"纯正文"还是"带 frontmatter 的全文"，
        落盘后文件里**只会有一段** frontmatter。

        历史 bug：`GET /wiki/doc/{id}/markdown` 返回的是全文（含 frontmatter），
        编辑器保存时把全文原样传回，这里又把磁盘上的 frontmatter 再拼一次
        → 每保存一次就多一段重复的 title/source_file/doc_type；
        多出来的那段还会被当成正文进 FTS 索引（污染检索）。

        如 MD 不存在返回 None。
        """
        path = self.get_path(doc_id)
        if not path.exists():
            return None

        existing = path.read_text(encoding="utf-8")
        disk_fm, disk_body = strip_frontmatter_blocks(existing)

        # 传回的内容可能自带 meta（历史行为），先剥离**全部** meta 块（含已累积的多段）
        incoming_fm, incoming_body = strip_frontmatter_blocks(new_markdown_body)

        # frontmatter 以磁盘为准：元信息由系统维护，不让编辑器写坏；
        # 磁盘上没有（旧文件）才退回用传入的
        frontmatter = disk_fm or incoming_fm
        body = incoming_body if incoming_body.strip() else disk_body

        path.write_text(join_frontmatter(frontmatter, body), encoding="utf-8")
        logger.info(
            f"已更新 MD 副本: {path}（frontmatter 1 段，正文 {len(body)} 字符）"
        )
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