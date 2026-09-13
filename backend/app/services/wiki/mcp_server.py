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
                  doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """在 AI Wiki 知识库中搜索文档

        Args:
            query: 搜索关键词（可空，配合 tag 单独过滤）
            top_k: 返回最多几个文档（默认 5）
            tag: 按标签过滤（如 "网络安全"）
            doc_type: 按类型过滤（如 "pdf"、"docx"）

        Returns:
            文档列表，每个含 doc_id / path / title / snippet
        """
        return idx.search(query, top_k=top_k, tag=tag, doc_type=doc_type)

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