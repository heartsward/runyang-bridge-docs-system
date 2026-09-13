"""
Wiki MCP Server（阶段十·W3）

FastMCP 暴露 6 个 tools 给 WorkBuddy：
- search_kb：关键词检索
- get_doc：取单文档元数据
- get_doc_content：取 MD 副本内容（供 WorkBuddy 阅读）
- list_backlinks：反向链接
- list_tags：浏览标签
- generate_report：按标签/查询生成报告骨架

Q1 决策：方案 A（HTTP transport via fastmcp.http_app()）
- WorkBuddy 配置："url": "http://localhost:8002/mcp", "transport": "http"
"""
import logging
from typing import Optional, List, Dict, Any

from app.services.wiki.index import WikiIndex
from app.services.wiki.storage import WikiStorage

logger = logging.getLogger(__name__)

# 创建全局实例（main.py 导入）
mcp = None  # 在 main.py 里赋值


def register_tools(mcp_instance):
    """注册 6 个 tools 到 mcp 实例"""
    idx = WikiIndex()
    storage = WikiStorage()

    @mcp_instance.tool()
    def search_kb(query: str = "", top_k: int = 5, tag: Optional[str] = None,
                  doc_type: Optional[str] = None, category: Optional[str] = None,
                  ) -> List[Dict[str, Any]]:
        """在 AI Wiki 知识库中搜索文档

        Args:
            query: 搜索关键词（可空，配合 tag/category 单独过滤）
            top_k: 返回最多几个文档（默认 5）
            tag: 按标签过滤（如 "网络安全"）
            doc_type: 按格式过滤（如 "pdf"、"docx"）
            category: 按业务分类过滤（运维报告/应急预案/操作规程/资产台账/
                      拓扑与配置/会议纪要/培训材料/其他）

        Returns:
            文档列表，每个含 doc_id / path / title / snippet / images（已提取图片数）
        """
        return idx.search(query, top_k=top_k, tag=tag, doc_type=doc_type,
                          doc_category=category)

    @mcp_instance.tool()
    def get_doc(doc_id: int) -> Dict[str, Any]:
        """取单文档的元数据 + tags"""
        meta = idx.get_doc(doc_id)
        if not meta:
            return {"error": f"文档不存在: doc_id={doc_id}"}
        return meta

    @mcp_instance.tool()
    def get_doc_content(doc_id: int, max_chars: int = 50000) -> Dict[str, Any]:
        """取文档的 MD 副本内容（供 WorkBuddy 阅读分析）

        Args:
            doc_id: 文档 ID
            max_chars: 内容最大字符数（防超出 context window）

        Returns:
            {"doc_id": int, "content": str, "truncated": bool, "length": int}
        """
        content = storage.read(doc_id)
        if not content:
            return {"error": f"MD 副本不存在: doc_id={doc_id}"}
        truncated = len(content) > max_chars
        return {
            "doc_id": doc_id,
            "content": content[:max_chars],
            "truncated": truncated,
            "length": len(content),
        }

    @mcp_instance.tool()
    def list_backlinks(doc_id: int) -> List[Dict[str, Any]]:
        """返回链接到该文档的所有文档（反向链接 / 引用关系）

        Args:
            doc_id: 目标文档 ID

        Returns:
            [{"src_doc_id": int, "anchor": str, "path": str, "title": str}]
        """
        return idx.list_backlinks(doc_id)

    @mcp_instance.tool()
    def list_tags(prefix: str = "") -> List[Dict[str, Any]]:
        """列出所有标签（按文档数排序）

        Args:
            prefix: 标签前缀过滤（可选）

        Returns:
            [{"tag": str, "doc_count": int}]
        """
        return idx.list_tags(prefix)

    def _base_url() -> str:
        try:
            from app.core.config import settings
            host = getattr(settings, "WIKI_PUBLIC_HOST", "") or "127.0.0.1"
            port = getattr(settings, "SERVER_PORT", 8002)
            return f"http://{host}:{port}"
        except Exception:
            return "http://127.0.0.1:8002"

    @mcp_instance.tool()
    def get_doc_images(doc_id: int) -> List[Dict[str, Any]]:
        """列出某文档的全部已提取图片（阶段十八·18.6）

        撰写报告/PPT 时，用本工具拿到文档里的图（拓扑图/表格/照片/截图），
        再用返回的 url 下载图片（需带系统 JWT Bearer token）。

        Args:
            doc_id: 文档 ID（来自 search_kb / get_doc）

        Returns:
            [{"file","page","caption","url"}]
            - caption: AI 生成的图片中文描述
            - url: 图片下载地址（GET 需 Authorization: Bearer <token>）
        """
        images = idx.get_doc_images(doc_id)
        base = _base_url()
        for img in images:
            img["url"] = f"{base}/api/v1/wiki/images/{doc_id}/{img['file']}"
        return images

    @mcp_instance.tool()
    def search_images(query: str = "", top_k: int = 10,
                      doc_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """按关键词搜图片（阶段十八·18.6，写报告找图的主入口）

        匹配图片的 AI 中文描述（caption）+ 文件名 + 所属文档标题。
        例：query="网络拓扑" 可找到所有拓扑图；query="机柜" 找到机房照片。

        Args:
            query: 图片内容关键词（中文，≥1 字；≥3 字走全文索引，1-2 字走子串匹配）
            top_k: 返回最多几张（默认 10）
            doc_id: 限定某文档内搜（可选）

        Returns:
            [{"doc_id","title","file","page","caption","url"}]
            - url: 图片下载地址（GET 需 Authorization: Bearer <token>）
        """
        results = idx.search_images(query, top_k=top_k, doc_id=doc_id)
        base = _base_url()
        for r in results:
            r["url"] = f"{base}/api/v1/wiki/images/{r['doc_id']}/{r['file']}"
        return results

    @mcp_instance.tool()
    def list_categories() -> List[Dict[str, Any]]:
        """列出所有业务分类及文档数（阶段十八·18.5）

        受控词表：运维报告/应急预案/操作规程/资产台账/拓扑与配置/会议纪要/培训材料/其他

        Returns:
            [{"doc_category": str, "doc_count": int}]
        """
        return idx.list_categories()

    @mcp_instance.tool()
    def generate_report(topic: str = "", tag: Optional[str] = None,
                       max_docs: int = 10, format: str = "markdown") -> Dict[str, Any]:
        """按主题/标签生成报告骨架

        Args:
            topic: 报告主题（用作查询关键词）
            tag: 限定标签（与 topic 同时生效）
            max_docs: 最多收录多少文档（默认 10）
            format: "markdown" | "summary"

        Returns:
            {"report": str, "doc_count": int, "sources": [...]}
        """
        # 检索相关文档
        docs = idx.search(topic, top_k=max_docs, tag=tag)

        sources = [{"doc_id": d["doc_id"], "title": d["title"], "snippet": d["snippet"]} for d in docs]

        # 生成报告骨架（WorkBuddy 可基于此骨架 + LLM 完善内容）
        lines = []
        title = topic or tag or "未指定主题"
        lines.append(f"# 报告：{title}")
        lines.append("")
        lines.append(f"> 自动生成于 AI Wiki | 共引用 {len(sources)} 个文档")
        lines.append("")

        # 按 tag 分组
        by_tag: Dict[str, List[Dict[str, Any]]] = {}
        for d in docs:
            meta = idx.get_doc(d["doc_id"])
            for t in (meta or {}).get("tags", []):
                by_tag.setdefault(t, []).append(d)

        if by_tag:
            lines.append("## 主题分布")
            for tag_name, tag_docs in by_tag.items():
                lines.append(f"- **{tag_name}**（{len(tag_docs)} 篇）")
            lines.append("")

        lines.append("## 文档列表")
        for i, src in enumerate(sources, 1):
            lines.append(f"### {i}. {src['title']}")
            lines.append(f"> doc_id={src['doc_id']}")
            if src["snippet"]:
                lines.append(f"")
                lines.append(f"```\n{src['snippet'][:300]}\n```")
            lines.append("")

        report = "\n".join(lines)
        return {"report": report, "doc_count": len(sources), "sources": sources, "format": format}