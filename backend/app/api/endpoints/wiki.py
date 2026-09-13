"""
Wiki API 端点（阶段十·W2 + W6）

- POST /api/v1/wiki/rebuild：全量重建索引
- GET  /api/v1/wiki/search?q=...&tag=...：检索
- GET  /api/v1/wiki/doc/{id}：取单文档元数据
- GET  /api/v1/wiki/doc/{id}/backlinks：反向链接
- GET  /api/v1/wiki/tags：列出所有标签
- GET  /api/v1/wiki/stats：索引统计
- GET  /api/v1/wiki/doc/{id}/markdown：读取 MD 副本（前端编辑器用）
- PUT  /api/v1/wiki/doc/{id}/markdown：保存 MD 副本（前端编辑器用）
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body

from app.core.deps import get_current_active_user
from app.models.user import User
from app.services.wiki.index import WikiIndex
from app.services.wiki.storage import WikiStorage

logger = logging.getLogger(__name__)

router = APIRouter()


def _index() -> WikiIndex:
    return WikiIndex()


def _storage() -> WikiStorage:
    return WikiStorage()


@router.post("/rebuild", summary="全量重建 Wiki 索引")
async def rebuild(
    current_user: User = Depends(get_current_active_user),
):
    """扫整个 wiki/ 目录重建 FTS5 索引"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="仅管理员可访问")

    idx = _index()
    stats = idx.rebuild_all()
    return {
        "success": True,
        "total": stats.get("total", 0),
        "ok": stats.get("ok", 0),
        "fail": stats.get("fail", 0),
        "tag_count": len(stats.get("tags", set())),
        "link_count": len(stats.get("links", set())),
    }


@router.get("/search", summary="Wiki 全文检索")
async def search(
    q: str = Query("", description="搜索关键词"),
    tag: Optional[str] = Query(None, description="按 tag 过滤"),
    doc_type: Optional[str] = Query(None, description="按文档类型过滤"),
    top_k: int = Query(5, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
):
    idx = _index()
    results = idx.search(q, top_k=top_k, tag=tag, doc_type=doc_type)
    return {"query": q, "tag": tag, "doc_type": doc_type, "results": results}


@router.get("/doc/{doc_id}", summary="获取单文档元数据")
async def get_doc(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
):
    idx = _index()
    meta = idx.get_doc(doc_id)
    if not meta:
        raise HTTPException(status_code=404, detail="文档不存在")
    return meta


@router.get("/doc/{doc_id}/backlinks", summary="反向链接列表")
async def get_backlinks(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
):
    idx = _index()
    return {"doc_id": doc_id, "backlinks": idx.list_backlinks(doc_id)}


@router.get("/tags", summary="列出所有标签")
async def get_tags(
    prefix: str = Query("", description="标签前缀过滤"),
    current_user: User = Depends(get_current_active_user),
):
    idx = _index()
    return {"tags": idx.list_tags(prefix)}


@router.get("/stats", summary="索引统计")
async def get_stats(
    current_user: User = Depends(get_current_active_user),
):
    idx = _index()
    return idx.get_stats()


@router.post("/report", summary="按主题生成报告骨架")
async def make_report(
    payload: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
):
    topic = payload.get("topic", "")
    tag = payload.get("tag")
    max_docs = int(payload.get("max_docs", 10))
    fmt = payload.get("format", "markdown")

    idx = _index()
    docs = idx.search(topic, top_k=max_docs, tag=tag)
    sources = [
        {"doc_id": d["doc_id"], "title": d["title"], "snippet": d["snippet"]}
        for d in docs
    ]

    lines = []
    title = topic or tag or "未指定主题"
    lines.append(f"# 报告：{title}")
    lines.append("")
    lines.append(f"> 自动生成于 AI Wiki | 共引用 {len(sources)} 个文档")
    lines.append("")

    # 按 tag 分组
    by_tag = {}
    for d in docs:
        meta = idx.get_doc(d["doc_id"])
        for t in (meta or {}).get("tags", []):
            by_tag.setdefault(t, []).append(d)

    if by_tag:
        lines.append("## 主题分布")
        for tn, td in by_tag.items():
            lines.append(f"- **{tn}**（{len(td)} 篇）")
        lines.append("")

    lines.append("## 文档列表")
    for i, src in enumerate(sources, 1):
        lines.append(f"### {i}. {src['title']}")
        lines.append(f"> doc_id={src['doc_id']}")
        if src["snippet"]:
            lines.append("")
            lines.append(f"```\n{src['snippet'][:300]}\n```")
        lines.append("")

    return {
        "report": "\n".join(lines),
        "doc_count": len(sources),
        "sources": sources,
        "format": fmt,
    }


@router.get("/download/{doc_id}", summary="下载文档（原文件/MD）")
async def download_doc(
    doc_id: int,
    type: str = Query("original", pattern="^(original|markdown)$"),
    current_user: User = Depends(get_current_active_user),
):
    """下载文档。type=original 下载原文件，type=markdown 下载 MD 副本"""
    from fastapi.responses import FileResponse

    from app.db.database import engine
    from sqlalchemy import text as sa_text

    # 查文档记录
    with engine.connect() as conn:
        row = conn.execute(
            sa_text("SELECT file_path FROM documents WHERE id = :id"),
            {"id": doc_id},
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="文档不存在")

    original_path = Path(row[0])

    if type == "original":
        if not original_path.exists():
            raise HTTPException(status_code=404, detail="原文件不存在")
        # 推断媒体类型
        suffix = original_path.suffix.lower()
        media = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".md": "text/markdown",
            ".txt": "text/plain",
        }.get(suffix, "application/octet-stream")
        return FileResponse(
            path=str(original_path),
            media_type=media,
            filename=original_path.name,
        )

    else:  # markdown
        storage = _storage()
        md_path = storage.get_path(doc_id)
        if md_path.exists():
            return FileResponse(
                path=str(md_path),
                media_type="text/markdown",
                filename=f"{original_path.stem}.md",
            )
        # MD 副本不存在 → 回退到 DB 里已提取的内容（保证下载总能成功）
        from urllib.parse import quote
        from fastapi.responses import Response
        with engine.connect() as conn2:
            row2 = conn2.execute(
                sa_text("SELECT content, title FROM documents WHERE id = :id"),
                {"id": doc_id},
            ).fetchone()
        if not row2 or not row2[0]:
            raise HTTPException(status_code=404, detail="MD 副本与已提取内容均不存在")
        safe_title = "".join(
            c for c in (row2[1] or f"doc_{doc_id}")
            if c.isalnum() or c in (" ", "-", "_", "(", ")", "[", "]", ".")
        ).strip() or f"doc_{doc_id}"
        return Response(
            content=row2[0],
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": (
                    f"attachment; filename*=UTF-8''{quote(f'{safe_title}.md')}"
                )
            },
        )


@router.get("/doc/{doc_id}/markdown", summary="读取 MD 副本内容")
async def get_markdown(
    doc_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """前端编辑器加载内容用"""
    storage = _storage()
    content = storage.read(doc_id)
    if not content:
        raise HTTPException(status_code=404, detail="MD 副本不存在")
    return {"doc_id": doc_id, "content": content}


@router.put("/doc/{doc_id}/markdown", summary="保存 MD 副本内容")
async def save_markdown(
    doc_id: int,
    payload: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
):
    """前端编辑器保存用

    Body: {"content": "...新的 MD 全文..."}
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="仅管理员可保存")

    new_content = payload.get("content", "")
    if not new_content:
        raise HTTPException(status_code=400, detail="content 不能为空")

    storage = _storage()
    path = storage.update(doc_id, new_content)
    if not path:
        raise HTTPException(status_code=404, detail="MD 副本不存在")

    # 重建索引（内容变了）
    try:
        _index().index_doc(doc_id, str(path))
    except Exception as e:
        logger.exception(f"重建索引失败: {e}")

    return {"success": True, "path": str(path)}