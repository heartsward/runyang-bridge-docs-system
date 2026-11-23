# -*- coding: utf-8 -*-
"""
数据可见性辅助（32.1）

权限模型：
- 管理员（is_superuser）：看到并管理全部文档/资产
- 普通用户：只看到 自己创建的（owner_id/creator_id == self）
  + 管理员分享给自己的（shares 表，只读）
- 被分享条目：只读——列表/详情/搜索可见，编辑/删除/再分享一律 403
"""
from typing import Optional

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import Session

from app.models.share import Share
from app.models.user import User


def _shared_item_ids_subquery(user_id: int, item_type: str):
    """当前用户被分享的 item_id 子查询"""
    return (
        select(Share.item_id)
        .where(Share.shared_with_id == user_id, Share.item_type == item_type)
        .scalar_subquery()
    )


# —— 模型延迟导入（避免调用方循环导入），下面按 _doc_model/_asset_model 取模型 ——

def _doc_model():
    from app.models.document import Document
    return Document


def Document_owner_eq(user_id: int):
    Document = _doc_model()
    return Document.owner_id == user_id


def Document_id_in_shared(user_id: int):
    Document = _doc_model()
    return Document.id.in_(_shared_item_ids_subquery(user_id, "document"))


def _asset_model():
    from app.models.asset import Asset
    return Asset


def Asset_creator_eq(user_id: int):
    Asset = _asset_model()
    return Asset.creator_id == user_id


def Asset_id_in_shared(user_id: int):
    Asset = _asset_model()
    return Asset.id.in_(_shared_item_ids_subquery(user_id, "asset"))


def visible_documents_filter(current_user: User):
    """文档列表过滤：管理员 None（全量）；普通用户=自有 ∪ 被分享"""
    if current_user.is_superuser:
        return None
    return or_(
        Document_owner_eq(current_user.id),
        Document_id_in_shared(current_user.id),
    )


def visible_assets_filter(current_user: User):
    """资产列表过滤：管理员 None（全量）；普通用户=自有 ∪ 被分享"""
    if current_user.is_superuser:
        return None
    return or_(
        Asset_creator_eq(current_user.id),
        Asset_id_in_shared(current_user.id),
    )


def is_shared_with(db: Session, user_id: int, item_type: str, item_id: int) -> bool:
    """该条目是否已分享给该用户（只读可见）"""
    return db.query(Share).filter(
        Share.item_type == item_type,
        Share.item_id == item_id,
        Share.shared_with_id == user_id,
    ).first() is not None


def can_modify(current_user: User, owner_id: int) -> bool:
    """能否修改/删除：管理员 或 归属者本人。被分享者（只读）不在此列——
    调用方先判 owner/superuser，分享可见性只用于读。"""
    return current_user.is_superuser or owner_id == current_user.id


def ensure_document_readable(db: Session, current_user: User, document) -> None:
    """详情/预览读权限：管理员 / owner / 被分享 → 放行；否则 404（不泄露存在性）"""
    from fastapi import HTTPException
    if current_user.is_superuser or document.owner_id == current_user.id:
        return
    if is_shared_with(db, current_user.id, "document", document.id):
        return
    raise HTTPException(status_code=404, detail="文档不存在")


def ensure_asset_readable(db: Session, current_user: User, asset) -> None:
    """详情读权限：管理员 / creator / 被分享 → 放行；否则 404"""
    from fastapi import HTTPException
    if current_user.is_superuser or asset.creator_id == current_user.id:
        return
    if is_shared_with(db, current_user.id, "asset", asset.id):
        return
    raise HTTPException(status_code=404, detail="资产不存在")
