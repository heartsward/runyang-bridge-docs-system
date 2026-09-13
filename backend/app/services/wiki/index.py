"""
Wiki 索引（阶段十·W2）

SQLite + FTS5 全文索引 + 元数据表 + 链接图。
零向量库，零外部依赖。
"""
import logging
import re
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple

logger = logging.getLogger(__name__)

# 索引 DB 路径（与 MD 副本同树）
INDEX_DIR = Path(__file__).parent.parent.parent.parent / "wiki"
INDEX_DB = INDEX_DIR / "index.db"


# FTS5 索引表
SCHEMA_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
    doc_id UNINDEXED,
    path,
    title,
    content,
    tags,
    doc_type,
    tokenize='unicode61'
);

CREATE TABLE IF NOT EXISTS doc_meta (
    doc_id INTEGER PRIMARY KEY,
    path TEXT NOT NULL,
    title TEXT,
    mtime TEXT,
    doc_type TEXT,
    frontmatter_json TEXT
);

CREATE TABLE IF NOT EXISTS doc_tags (
    doc_id INTEGER,
    tag TEXT,
    PRIMARY KEY (doc_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_doc_tags_tag ON doc_tags(tag);

CREATE TABLE IF NOT EXISTS doc_links (
    src_doc_id INTEGER,
    dst_doc_id INTEGER,
    anchor TEXT,
    PRIMARY KEY (src_doc_id, dst_doc_id, anchor)
);
"""

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
HASHTAG_PATTERN = re.compile(r"(?:^|\s)#([\w\u4e00-\u9fa5/_-]+)")
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class WikiIndex:
    """Wiki 索引管理器"""

    def __init__(self, db_path: Path = INDEX_DB):
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(db_path)
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    @staticmethod
    def parse_frontmatter(content: str) -> Dict[str, Any]:
        """解析 YAML frontmatter"""
        m = FRONTMATTER_PATTERN.match(content)
        if not m:
            return {}
        try:
            import yaml
            return yaml.safe_load(m.group(1)) or {}
        except Exception:
            return {}

    @staticmethod
    def extract_links_and_tags(content: str) -> Tuple[List[str], List[str]]:
        """从 MD 内容抽取 [[wikilink]] 和 #tag"""
        wikilinks = WIKILINK_PATTERN.findall(content)
        wikilinks = [w.strip() for w in wikilinks]
        hashtags = HASHTAG_PATTERN.findall(content)
        hashtags = [t.strip() for t in hashtags]
        return wikilinks, hashtags

    def index_doc(
        self,
        doc_id: int,
        md_path: str,
        force: bool = False,
    ) -> Dict[str, Any]:
        """索引单个文档

        Returns:
            {"tags": [...], "wikilinks": [...], "title": ...}
        """
        path = Path(md_path)
        if not path.exists():
            logger.warning(f"MD 副本不存在，无法索引: {md_path}")
            return {}

        content = path.read_text(encoding="utf-8")
        fm = self.parse_frontmatter(content)
        wikilinks, hashtags = self.extract_links_and_tags(content)

        # 正文（去掉 frontmatter）
        body = FRONTMATTER_PATTERN.sub("", content, count=1)

        title = fm.get("title", "")
        tags = fm.get("tags", []) or []
        doc_type = fm.get("doc_type", "")
        mtime = path.stat().st_mtime

        with self._conn() as conn:
            # 写 meta
            conn.execute(
                """INSERT OR REPLACE INTO doc_meta
                   (doc_id, path, title, mtime, doc_type, frontmatter_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    doc_id, str(path), title,
                    mtime, doc_type,
                    str(fm),
                ),
            )

            # 重建 FTS5 文档
            conn.execute("DELETE FROM docs_fts WHERE doc_id = ?", (doc_id,))
            conn.execute(
                """INSERT INTO docs_fts (doc_id, path, title, content, tags, doc_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    doc_id, str(path), title,
                    body,
                    " ".join(tags),
                    doc_type,
                ),
            )

            # tags 表
            conn.execute("DELETE FROM doc_tags WHERE doc_id = ?", (doc_id,))
            for tag in tags:
                conn.execute(
                    "INSERT OR IGNORE INTO doc_tags (doc_id, tag) VALUES (?, ?)",
                    (doc_id, tag),
                )

            # 解析 wikilinks → 写入 doc_links 表
            # 简化策略：wikilink 文本与其它文档的 title/basename 匹配
            conn.execute("DELETE FROM doc_links WHERE src_doc_id = ?", (doc_id,))
            for wl in wikilinks:
                # 查 title 匹配
                row = conn.execute(
                    "SELECT doc_id FROM doc_meta WHERE title = ? OR path LIKE ?",
                    (wl, f"%{wl}.md"),
                ).fetchone()
                if row:
                    conn.execute(
                        """INSERT OR IGNORE INTO doc_links
                           (src_doc_id, dst_doc_id, anchor) VALUES (?, ?, ?)""",
                        (doc_id, row["doc_id"], wl),
                    )

        logger.info(f"已索引文档 {doc_id}: {md_path} (tags={len(tags)}, links={len(wikilinks)})")

        return {
            "title": title,
            "tags": tags,
            "wikilinks": wikilinks,
            "hashtags": hashtags,
        }

    def rebuild_all(self, wiki_dir: Optional[Path] = None) -> Dict[str, Any]:
        """全量重建索引（扫整个 wiki/ 目录）"""
        wiki_dir = Path(wiki_dir) if wiki_dir else INDEX_DIR
        md_files = sorted(wiki_dir.glob("*.md"))

        stats = {"total": 0, "ok": 0, "fail": 0, "tags": set(), "links": set()}
        for md in md_files:
            try:
                doc_id = int(md.stem)
                stats["total"] += 1
                result = self.index_doc(doc_id, str(md))
                if result:
                    stats["ok"] += 1
                    stats["tags"].update(result.get("tags", []))
                    stats["links"].update(result.get("wikilinks", []))
            except (ValueError, Exception) as e:
                logger.warning(f"索引 {md.name} 失败: {e}")
                stats["fail"] += 1

        logger.info(f"全量重建完成: {stats['ok']}/{stats['total']} 文档")
        return stats

    def search(
        self,
        query: str,
        top_k: int = 5,
        tag: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """关键词检索（返回 top_k 个文档摘要）"""
        if not query and not tag:
            return []

        results: List[Dict[str, Any]] = []

        with self._conn() as conn:
            if query:
                # FTS5 全文检索
                fts_query = query.replace('"', '""')
                rows = conn.execute(
                    """SELECT doc_id, path, title, snippet(docs_fts, 3, '...', '...', '...', 12) as snip
                       FROM docs_fts
                       WHERE docs_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (fts_query, top_k * 2),
                ).fetchall()
                for r in rows:
                    results.append({
                        "doc_id": r["doc_id"],
                        "path": r["path"],
                        "title": r["title"],
                        "snippet": r["snip"],
                        "score": 1.0,
                    })
            else:
                # 只按 tag 筛选
                rows = conn.execute(
                    """SELECT m.doc_id, m.path, m.title
                       FROM doc_meta m
                       JOIN doc_tags t ON m.doc_id = t.doc_id
                       WHERE t.tag = ?
                       ORDER BY m.mtime DESC
                       LIMIT ?""",
                    (tag, top_k),
                ).fetchall()
                for r in rows:
                    results.append({
                        "doc_id": r["doc_id"],
                        "path": r["path"],
                        "title": r["title"] or "",
                        "snippet": "",
                        "score": 1.0,
                    })

        # 进一步按 tag / doc_type 过滤
        if tag or doc_type:
            results = [r for r in results if self._match_filter(r["doc_id"], tag, doc_type)]

        return results[:top_k]

    def _match_filter(self, doc_id: int, tag: Optional[str], doc_type: Optional[str]) -> bool:
        with self._conn() as conn:
            if tag:
                r = conn.execute(
                    "SELECT 1 FROM doc_tags WHERE doc_id = ? AND tag = ?",
                    (doc_id, tag),
                ).fetchone()
                if not r:
                    return False
            if doc_type:
                r = conn.execute(
                    "SELECT doc_type FROM doc_meta WHERE doc_id = ?",
                    (doc_id,),
                ).fetchone()
                if not r or r["doc_type"] != doc_type:
                    return False
        return True

    def get_doc(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """取单文档元数据"""
        with self._conn() as conn:
            r = conn.execute(
                "SELECT * FROM doc_meta WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            if not r:
                return None
            meta = dict(r)
            tags = conn.execute(
                "SELECT tag FROM doc_tags WHERE doc_id = ?", (doc_id,)
            ).fetchall()
            meta["tags"] = [t["tag"] for t in tags]
            return meta

    def list_backlinks(self, doc_id: int) -> List[Dict[str, Any]]:
        """返回链接到该文档的所有文档（反向链接）"""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT l.src_doc_id, l.anchor, m.path, m.title
                   FROM doc_links l
                   JOIN doc_meta m ON l.src_doc_id = m.doc_id
                   WHERE l.dst_doc_id = ?""",
                (doc_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_tags(self, prefix: str = "") -> List[Dict[str, Any]]:
        """列出所有标签（按文档数排序）"""
        with self._conn() as conn:
            if prefix:
                rows = conn.execute(
                    """SELECT tag, COUNT(DISTINCT doc_id) AS doc_count
                       FROM doc_tags
                       WHERE tag LIKE ?
                       GROUP BY tag
                       ORDER BY doc_count DESC""",
                    (prefix + "%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT tag, COUNT(DISTINCT doc_id) AS doc_count
                       FROM doc_tags
                       GROUP BY tag
                       ORDER BY doc_count DESC""",
                ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> Dict[str, Any]:
        with self._conn() as conn:
            docs = conn.execute("SELECT COUNT(*) AS n FROM doc_meta").fetchone()["n"]
            tags = conn.execute("SELECT COUNT(DISTINCT tag) AS n FROM doc_tags").fetchone()["n"]
            links = conn.execute("SELECT COUNT(*) AS n FROM doc_links").fetchone()["n"]
        return {"docs": docs, "tags": tags, "links": links}