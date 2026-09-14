"""
Wiki MCP Server（阶段十·W3）

FastMCP 暴露 11 个 tools 给 WorkBuddy：
- search_kb：关键词检索
- get_doc：取单文档元数据
- get_doc_content：取 MD 副本内容（供 WorkBuddy 阅读）
- list_backlinks：反向链接
- list_tags：浏览标签
- generate_report：按标签/查询生成报告骨架
- get_doc_images / search_images：文档图片检索（阶段十八）
- list_categories：业务分类浏览（阶段十八）
- search_assets：设备资产搜索（阶段二十·20.8；20.9 起命中唯一直接返回全字段含账号密码，一轮作答）
- get_asset：单台设备全部信息（阶段二十·20.8）
- list_assets：设备资产轻量清单（阶段二十·20.9，不含账号密码）

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


def _asset_to_dict(asset) -> Dict[str, Any]:
    """Asset ORM 对象 → 全部字段字典（阶段二十·20.8）

    - datetime 转 "YYYY-MM-DD HH:MM:SS" 字符串（避免序列化问题）
    - tags JSON 字符串解析为 list
    - 含 username/password：与资产导出端点口径一致（库内明文存储，原样返回）
    """
    import json as _json
    from datetime import datetime as _dt

    out: Dict[str, Any] = {}
    for col in asset.__table__.columns:
        if col.name == "creator_id":
            continue  # 无业务含义
        v = getattr(asset, col.name)
        if isinstance(v, _dt):
            v = v.strftime("%Y-%m-%d %H:%M:%S")
        out[col.name] = v
    if isinstance(out.get("tags"), str):
        try:
            out["tags"] = _json.loads(out["tags"])
        except Exception:
            pass  # 非 JSON 格式则保留原字符串
    return out


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

    # ============ 设备资产域（阶段二十·20.8） ============
    # 直接查 assets 表（与资产导出端点同一数据源、同一口径）。
    # 密码为明文存储（库内本就不加密），按用户明确要求原样返回。

    def _search_assets_impl(query: str, top_k: int, asset_type: Optional[str],
                            network_location: Optional[str], status: Optional[str]):
        from sqlalchemy import or_, desc as _desc
        from app.models.asset import Asset
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            q = db.query(Asset)
            if query:
                term = f"%{query}%"
                q = q.filter(or_(
                    Asset.name.ilike(term),
                    Asset.hostname.ilike(term),
                    Asset.ip_address.ilike(term),
                    Asset.mac_address.ilike(term),
                    Asset.serial_number.ilike(term),
                    Asset.device_model.ilike(term),
                    Asset.manufacturer.ilike(term),
                    Asset.service_name.ilike(term),
                    Asset.application.ilike(term),
                    Asset.department.ilike(term),
                    Asset.location.ilike(term),
                    Asset.datacenter.ilike(term),
                    Asset.tags.ilike(term),
                    Asset.notes.ilike(term),
                ))
            if asset_type:
                q = q.filter(Asset.asset_type == asset_type)
            if network_location:
                q = q.filter(Asset.network_location == network_location)
            if status:
                q = q.filter(Asset.status == status)
            rows = q.order_by(_desc(Asset.updated_at)).limit(top_k).all()
            return [_asset_to_dict(a) for a in rows]
        finally:
            db.close()

    def _get_asset_impl(asset_id: int):
        from app.models.asset import Asset
        from app.db.database import SessionLocal

        db = SessionLocal()
        try:
            a = db.query(Asset).filter(Asset.id == asset_id).first()
            return _asset_to_dict(a) if a else None
        finally:
            db.close()

    # 摘要字段：多台命中时只返回这几列（返回体小 → LLM 处理快）；
    # 不含 username/password —— 账号密码只在"确认了具体哪台"后给
    #（search_assets 唯一命中 / get_asset），避免一次把多台设备的密码全吐出来。
    _SUMMARY_FIELDS = ("id", "name", "ip_address", "hostname",
                       "asset_type", "status", "network_location")

    def _asset_summary(a: Dict[str, Any]) -> Dict[str, Any]:
        return {k: a.get(k) for k in _SUMMARY_FIELDS}

    @mcp_instance.tool()
    def search_assets(query: str = "", top_k: int = 10,
                      asset_type: Optional[str] = None,
                      network_location: Optional[str] = None,
                      status: Optional[str] = None) -> Dict[str, Any]:
        """搜索设备资产（查地址 / 账号密码 / 设备信息的主入口）。

        支持按设备名、IP、主机名、序列号、型号、厂商、服务名、应用、部门、
        位置、数据中心、MAC、标签、备注等任意字段模糊匹配（query 可空，
        空时按过滤条件列出资产）。

        返回按命中数自适应（**为减少往返设计**）：
        - 命中 1 台 → 直接返回该设备**全部字段**（含 username/password），
          一次调用即可回答"XX 设备的地址/账号密码是多少"
        - 命中 ≥2 台 → 返回 {"total", "assets": [摘要], "hint"}，摘要只含
          id/name/ip_address/hostname/asset_type/status/network_location，
          需要某台详情（含密码）时用 get_asset(id) 再取
        - 命中 0 台 → {"total": 0, "assets": []}

        全字段说明（唯一命中时返回）：
            - name 设备名 / asset_type 类型 / device_model 型号 / manufacturer 厂商
            - ip_address 地址 / mac_address / hostname 主机名 / port / network_location 所处网络
            - username 用户名 / password 密码 / ssh_key SSH密钥
            - location 物理位置 / rack_position 机柜 / datacenter 数据中心
            - os_version / cpu / memory / storage 配置
            - status 状态 / department 部门 / service_name 服务 / application 应用 / purpose 用途
            - purchase_date / warranty_expiry / last_maintenance / next_maintenance
            - notes 备注 / tags 标签 / source_file 来源文件 / source_document_id
            - id / created_at / updated_at

        Args:
            query: 搜索关键词（如设备名"核心交换机"、IP "172.16.8.106"）
            top_k: 最多返回几条（默认 10）
            asset_type: 按类型过滤（server/network/storage/security/database/application/other 及中文类型如"信息系统"）
            network_location: 按所处网络过滤（office 办公网/monitoring 监控网/billing 收费网/other）
            status: 按状态过滤（active 在用/inactive 停用/maintenance 维护中/retired 已退役）
        """
        rows = _search_assets_impl(query, top_k, asset_type, network_location, status)
        if len(rows) == 1:
            return rows[0]
        return {
            "total": len(rows),
            "assets": [_asset_summary(r) for r in rows],
            "hint": "多台命中：以上为摘要。要某台的全部信息（含账号密码）请调 get_asset(asset_id)。"
                    if rows else "无匹配设备。可换关键词（名称/IP/型号）或去掉 query 只用过滤条件。",
        }

    @mcp_instance.tool()
    def list_assets(asset_type: Optional[str] = None,
                    network_location: Optional[str] = None,
                    status: Optional[str] = None,
                    limit: int = 200) -> List[Dict[str, Any]]:
        """列出设备资产清单（轻量，**不含账号密码**）。

        用于"有哪些设备 / 收费网都有什么 / 安全设备列表"这类概览问题。
        每台只返回摘要字段：id / name / ip_address / hostname /
        asset_type / status / network_location。
        查某台的账号密码请用 search_assets（精确到一台时直接给全字段）
        或 get_asset(id)。

        Args:
            asset_type: 按类型过滤（可选）
            network_location: 按所处网络过滤（office/monitoring/billing/other，可选）
            status: 按状态过滤（active/inactive/maintenance/retired，可选）
            limit: 最多返回多少台（默认 200）

        Returns:
            [{"id","name","ip_address","hostname","asset_type","status","network_location"}]
        """
        rows = _search_assets_impl("", limit, asset_type, network_location, status)
        return [_asset_summary(r) for r in rows]

    @mcp_instance.tool()
    def get_asset(asset_id: int) -> Dict[str, Any]:
        """按 ID 取单台设备的**全部信息**（字段含义见 search_assets 返回值说明）。

        Args:
            asset_id: 设备 ID（可先用 search_assets 按名称/IP 查到）

        Returns:
            单台设备全部字段（含 username / password）；不存在时返回 {"error": ...}
        """
        a = _get_asset_impl(asset_id)
        if not a:
            return {"error": f"设备不存在: asset_id={asset_id}"}
        return a

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