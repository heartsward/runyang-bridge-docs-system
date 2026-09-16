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

-- 阶段十八·18.2：图片索引（wiki/images/{doc_id}/ 下每张图一行）
CREATE TABLE IF NOT EXISTS wiki_images (
    doc_id INTEGER,
    file TEXT,
    page INTEGER DEFAULT 0,
    caption TEXT,
    rel_path TEXT,
    size INTEGER DEFAULT 0,
    PRIMARY KEY (doc_id, file)
);

-- 图片全文索引（caption + 文件名 + 所属文档标题；trigram 支持中文子串）
CREATE VIRTUAL TABLE IF NOT EXISTS images_fts USING fts5(
    doc_id UNINDEXED,
    file UNINDEXED,
    page UNINDEXED,
    rel_path UNINDEXED,
    search_text,
    tokenize='trigram'
);

-- 阶段十八·18.4：中文 trigram 全文索引（与 docs_fts 双路合并）
-- 实测（SQLite 3.53）：trigram 按 Unicode 字符计，中文查询需 ≥3 字才命中；
-- 1-2 字中文走 doc_text 表 LIKE 兜底
CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts_zh USING fts5(
    doc_id UNINDEXED,
    path,
    title,
    content,
    tags,
    doc_type,
    tokenize='trigram'
);

-- 正文普通表（供 1-2 字中文 LIKE 兜底检索）
CREATE TABLE IF NOT EXISTS doc_text (
    doc_id INTEGER PRIMARY KEY,
    text TEXT
);
"""

# 旧库迁移用（CREATE VIRTUAL TABLE IF NOT EXISTS 已覆盖新表；
# doc_meta.doc_category 列用 ALTER 兼容）
MIGRATE_STATEMENTS = [
    "ALTER TABLE doc_meta ADD COLUMN doc_category TEXT",
]

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
            # 旧库迁移：doc_meta 加 doc_category 列（已存在则忽略）
            for stmt in MIGRATE_STATEMENTS:
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass  # duplicate column name 等，忽略
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
        doc_category = fm.get("doc_category", "")  # 阶段十八·18.5：业务分类
        mtime = path.stat().st_mtime

        with self._conn() as conn:
            # 写 meta
            conn.execute(
                """INSERT OR REPLACE INTO doc_meta
                   (doc_id, path, title, mtime, doc_type, frontmatter_json, doc_category)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    doc_id, str(path), title,
                    mtime, doc_type,
                    str(fm),
                    doc_category,
                ),
            )

            # 重建 FTS5 文档（unicode61：英文/术语）
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

            # 阶段十八·18.4：trigram 索引（中文 ≥3 字）+ 正文表（1-2 字 LIKE 兜底）
            conn.execute("DELETE FROM docs_fts_zh WHERE doc_id = ?", (doc_id,))
            conn.execute(
                """INSERT INTO docs_fts_zh (doc_id, path, title, content, tags, doc_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    doc_id, str(path), title,
                    body,
                    " ".join(tags),
                    doc_type,
                ),
            )
            conn.execute(
                "INSERT OR REPLACE INTO doc_text (doc_id, text) VALUES (?, ?)",
                (doc_id, body),
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

    def remove_doc(self, doc_id: int) -> Dict[str, int]:
        """级联删除某文档的全部索引条目（27.8：界面删除文档时调用）

        覆盖 8 张表：docs_fts / docs_fts_zh / doc_meta / doc_tags /
        doc_links（双向）/ doc_text / wiki_images / images_fts。
        FTS5 表的 doc_id 是 UNINDEXED 存储列，可按值 DELETE。
        返回各表删除行数（调试用）。
        """
        counts: Dict[str, int] = {}
        with self._conn() as conn:
            for table in ("docs_fts", "docs_fts_zh", "doc_meta",
                          "doc_tags", "doc_text", "wiki_images", "images_fts"):
                cur = conn.execute(f"DELETE FROM {table} WHERE doc_id=?", (doc_id,))
                counts[table] = cur.rowcount
            cur = conn.execute(
                "DELETE FROM doc_links WHERE src_doc_id=? OR dst_doc_id=?",
                (doc_id, doc_id),
            )
            counts["doc_links"] = cur.rowcount
            conn.commit()
        logger.info(f"已级联删除文档 {doc_id} 的索引条目: {counts}")
        return counts

    def search(
        self,
        query: str,
        top_k: int = 5,
        tag: Optional[str] = None,
        doc_type: Optional[str] = None,
        doc_category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """关键词检索（返回 top_k 个文档摘要）

        阶段十八·18.4：三路合并（实测 trigram 中文需 ≥3 字才命中）：
        1. docs_fts (unicode61) MATCH —— 英文/术语
        2. docs_fts_zh (trigram) MATCH —— 中文 ≥3 字
        3. doc_text LIKE —— 中文 1-2 字兜底（LIKE 对任意长度有效）
        结果按 doc_id 去重合并；每项附 images 计数（18.6）。
        """
        if not query and not tag and not doc_category:
            return []

        results: List[Dict[str, Any]] = []
        seen: Dict[int, Dict[str, Any]] = {}

        with self._conn() as conn:
            if query:
                q = query.strip()

                # 路 1：unicode61 MATCH（英文/术语/数字）
                fts_query = f'"{q.replace(chr(34), chr(34) * 2)}"'
                try:
                    rows = conn.execute(
                        """SELECT doc_id, path, title,
                                  snippet(docs_fts, 3, '...', '...', '...', 12) as snip
                           FROM docs_fts WHERE docs_fts MATCH ?
                           ORDER BY rank LIMIT ?""",
                        (fts_query, top_k * 3),
                    ).fetchall()
                    for r in rows:
                        self._merge_result(seen, r["doc_id"], r["path"], r["title"], r["snip"], 1.0)
                except sqlite3.OperationalError as e:
                    logger.warning(f"FTS unicode61 检索失败: {e}")

                # 路 2：trigram MATCH（中文 ≥3 字 / 任意 ≥3 字符）
                if len(q) >= 3:
                    try:
                        zh_query = f'"{q.replace(chr(34), chr(34) * 2)}"'
                        rows = conn.execute(
                            """SELECT doc_id, path, title,
                                      snippet(docs_fts_zh, 3, '...', '...', '...', 12) as snip
                               FROM docs_fts_zh WHERE docs_fts_zh MATCH ?
                               ORDER BY rank LIMIT ?""",
                            (zh_query, top_k * 3),
                        ).fetchall()
                        for r in rows:
                            self._merge_result(seen, r["doc_id"], r["path"], r["title"], r["snip"], 1.0)
                    except sqlite3.OperationalError as e:
                        logger.warning(f"FTS trigram 检索失败: {e}")

                # 路 3：LIKE 兜底（1-2 字中文等短词）
                if len(q) <= 2 or not seen:
                    like_q = f"%{q}%"
                    rows = conn.execute(
                        """SELECT m.doc_id, m.path, m.title,
                                  substr(t.text, 1, 120) as snip
                           FROM doc_text t JOIN doc_meta m ON t.doc_id = m.doc_id
                           WHERE t.text LIKE ? OR m.title LIKE ?
                           LIMIT ?""",
                        (like_q, like_q, top_k * 3),
                    ).fetchall()
                    for r in rows:
                        self._merge_result(seen, r["doc_id"], r["path"], r["title"], r["snip"], 0.8)
            else:
                # 只按 tag / category 筛选
                where = "1=1"
                params: List[Any] = []
                if tag:
                    where += " AND m.doc_id IN (SELECT doc_id FROM doc_tags WHERE tag = ?)"
                    params.append(tag)
                if doc_category:
                    where += " AND m.doc_category = ?"
                    params.append(doc_category)
                rows = conn.execute(
                    f"""SELECT m.doc_id, m.path, m.title FROM doc_meta m
                        WHERE {where} ORDER BY m.mtime DESC LIMIT ?""",
                    params + [top_k * 3],
                ).fetchall()
                for r in rows:
                    self._merge_result(seen, r["doc_id"], r["path"], r["title"] or "", "", 1.0)

            # 每项附图片计数（阶段十八·18.6：让 AI 知道"这篇有图可取"）
            for item in seen.values():
                row = conn.execute(
                    "SELECT COUNT(*) FROM wiki_images WHERE doc_id = ?",
                    (item["doc_id"],),
                ).fetchone()
                item["images"] = row[0] if row else 0

        results = list(seen.values())
        if tag or doc_type or doc_category:
            results = [r for r in results
                       if self._match_filter(r["doc_id"], tag, doc_type, doc_category)]
        return results[:top_k]

    @staticmethod
    def _merge_result(seen: Dict[int, Dict[str, Any]], doc_id, path, title, snippet, score):
        """多路结果去重合并（保留更高 score 与首个非空 snippet）"""
        if doc_id in seen:
            item = seen[doc_id]
            item["score"] = max(item["score"], score)
            if not item["snippet"] and snippet:
                item["snippet"] = snippet
            return
        seen[doc_id] = {
            "doc_id": doc_id,
            "path": path,
            "title": title or "",
            "snippet": snippet or "",
            "score": score,
        }

    def _match_filter(self, doc_id: int, tag: Optional[str], doc_type: Optional[str],
                      doc_category: Optional[str] = None) -> bool:
        with self._conn() as conn:
            if tag:
                r = conn.execute(
                    "SELECT 1 FROM doc_tags WHERE doc_id = ? AND tag = ?",
                    (doc_id, tag),
                ).fetchone()
                if not r:
                    return False
            meta = conn.execute(
                "SELECT doc_type, doc_category FROM doc_meta WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            if not meta:
                return False
            if doc_type and meta["doc_type"] != doc_type:
                return False
            if doc_category and (meta["doc_category"] or "") != doc_category:
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
            # 阶段十八·18.6：附加图片列表
            img_rows = conn.execute(
                "SELECT file, page, caption, rel_path, size FROM wiki_images WHERE doc_id = ? ORDER BY page, file",
                (doc_id,),
            ).fetchall()
            meta["images"] = [dict(r) for r in img_rows]
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

    # ---- 阶段十八·18.2 / 18.6：图片索引 ----
    def add_image(self, doc_id: int, file: str, page: int = 0, caption: str = "",
                  rel_path: str = "", size: int = 0) -> None:
        """登记一张图片（落盘后调用）；caption 进 images_fts 全文索引"""
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO wiki_images
                   (doc_id, file, page, caption, rel_path, size)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (doc_id, file, page, caption, rel_path, size),
            )
            conn.execute("DELETE FROM images_fts WHERE doc_id = ? AND file = ?", (doc_id, file))
            title_row = conn.execute(
                "SELECT title FROM doc_meta WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            title = title_row["title"] if title_row else ""
            search_text = f"{caption} {file} {title}"
            conn.execute(
                """INSERT INTO images_fts (doc_id, file, page, rel_path, search_text)
                   VALUES (?, ?, ?, ?, ?)""",
                (doc_id, file, page, rel_path, search_text),
            )

    def update_image_caption(self, doc_id: int, file: str, caption: str) -> None:
        """AI 描述异步就绪后回填 caption 并刷新 FTS"""
        with self._conn() as conn:
            conn.execute(
                "UPDATE wiki_images SET caption = ? WHERE doc_id = ? AND file = ?",
                (caption, doc_id, file),
            )
            conn.execute("DELETE FROM images_fts WHERE doc_id = ? AND file = ?", (doc_id, file))
            title_row = conn.execute(
                "SELECT title FROM doc_meta WHERE doc_id = ?", (doc_id,)
            ).fetchone()
            title = title_row["title"] if title_row else ""
            search_text = f"{caption} {file} {title}"
            conn.execute(
                """INSERT INTO images_fts (doc_id, file, page, rel_path, search_text)
                   VALUES (?, ?, ?, ?, ?)""",
                (doc_id, file, 0, f"images/{doc_id}/{file}", search_text),
            )

    def get_doc_images(self, doc_id: int) -> List[Dict[str, Any]]:
        """列出某文档的全部已索引图片"""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT doc_id, file, page, caption, rel_path, size
                   FROM wiki_images WHERE doc_id = ?
                   ORDER BY page, file""",
                (doc_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def search_images(self, query: str, top_k: int = 10,
                      doc_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """图片全文检索（caption + 文件名 + 所属文档标题）

        实测 trigram 中文需 ≥3 字：≥3 字走 MATCH，否则 LIKE 兜底。
        """
        q = (query or "").strip()
        if not q:
            return []
        with self._conn() as conn:
            rows = []
            if len(q) >= 3:
                try:
                    rows = conn.execute(
                        """SELECT doc_id, file, page, rel_path,
                                  snippet(images_fts, 4, '...', '...', '...', 30) as snip
                           FROM images_fts WHERE images_fts MATCH ?
                           ORDER BY rank LIMIT ?""",
                        (f'"{q.replace(chr(34), chr(34) * 2)}"', top_k),
                    ).fetchall()
                except sqlite3.OperationalError as e:
                    logger.warning(f"图片 FTS 检索失败: {e}")
            if not rows:
                like_q = f"%{q}%"
                rows = conn.execute(
                    """SELECT w.doc_id, w.file, w.page, w.rel_path, w.caption as snip
                       FROM wiki_images w
                       WHERE w.caption LIKE ? OR w.file LIKE ?
                       LIMIT ?""",
                    (like_q, like_q, top_k),
                ).fetchall()
            results = []
            for r in rows:
                if doc_id is not None and r["doc_id"] != doc_id:
                    continue
                meta = conn.execute(
                    "SELECT title FROM doc_meta WHERE doc_id = ?", (r["doc_id"],)
                ).fetchone()
                results.append({
                    "doc_id": r["doc_id"],
                    "title": meta["title"] if meta else "",
                    "file": r["file"],
                    "page": r["page"],
                    "rel_path": r["rel_path"],
                    "caption": (r["snip"] or ""),
                })
            return results[:top_k]

    def list_categories(self) -> List[Dict[str, Any]]:
        """列出所有业务分类及文档数（阶段十八·18.5）"""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT COALESCE(NULLIF(doc_category, ''), '其他') AS doc_category,
                          COUNT(*) AS doc_count
                   FROM doc_meta
                   GROUP BY doc_category
                   ORDER BY doc_count DESC"""
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