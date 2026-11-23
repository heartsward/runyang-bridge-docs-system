# -*- coding: utf-8 -*-
"""
分享API端点（32.1）

管理员把指定文档/资产分享给某个用户 → 被分享者**只读**可见。
- POST   /shares/            管理员创建分享（item_type + item_id + user_id）
- DELETE /shares/{share_id}  管理员撤销分享
- GET    /shares/by-item     查某条目已分享给哪些用户（管理员，弹窗回显）
- GET    /shares/mine        当前用户被分享的条目（前端可显示"来自分享"标记）
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.models.share import Share
from app.models.user import User

router = APIRouter()


class ShareCreate(BaseModel):
    item_type: str = Field(..., description="document | asset")
    item_id: int = Field(..., description="文档/资产ID")
    user_id: int = Field(..., description="被分享用户ID")


class ShareOut(BaseModel):
    id: int
    item_type: str
    item_id: int
    shared_by_id: int
    shared_with_id: int
    shared_with_username: Optional[str] = None

    class Config:
        from_attributes = True


def _check_item_exists(db: Session, item_type: str, item_id: int):
    if item_type == "document":
        from app.models.document import Document
        return db.query(Document).filter(Document.id == item_id).first() is not None
    if item_type == "asset":
        from app.models.asset import Asset
        return db.query(Asset).filter(Asset.id == item_id).first() is not None
    return False


@router.post("/", response_model=ShareOut, summary="创建分享（仅管理员）")
async def create_share(
    payload: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以分享文档或资产")

    if payload.item_type not in ("document", "asset"):
        raise HTTPException(status_code=400, detail="item_type 必须是 document 或 asset")

    target = db.query(User).filter(User.id == payload.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="被分享用户不存在")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能分享给自己（管理员本来就能看到全部）")

    if not _check_item_exists(db, payload.item_type, payload.item_id):
        raise HTTPException(status_code=404, detail="文档或资产不存在")

    existing = db.query(Share).filter(
        Share.item_type == payload.item_type,
        Share.item_id == payload.item_id,
        Share.shared_with_id == payload.user_id,
    ).first()
    if existing:
        return ShareOut(
            id=existing.id, item_type=existing.item_type, item_id=existing.item_id,
            shared_by_id=existing.shared_by_id, shared_with_id=existing.shared_with_id,
            shared_with_username=target.username,
        )

    share = Share(
        item_type=payload.item_type,
        item_id=payload.item_id,
        shared_by_id=current_user.id,
        shared_with_id=payload.user_id,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return ShareOut(
        id=share.id, item_type=share.item_type, item_id=share.item_id,
        shared_by_id=share.shared_by_id, shared_with_id=share.shared_with_id,
        shared_with_username=target.username,
    )


# 注意路由顺序：具体路径 /by-item 必须在 /{share_id} 之前注册，
# 否则 FastAPI 会把 "by-item" 当 share_id 去 int 解析 → 422（32.4 实测踩坑）

@router.delete("/by-item", summary="一键撤销条目全部分享（仅管理员，32.4）")
async def delete_shares_by_item(
    item_type: str = Query(..., description="document | asset"),
    item_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """把该文档/资产分享给所有人的记录一次清空（分享弹窗「一键取消所有分享」）"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以撤销分享")
    if item_type not in ("document", "asset"):
        raise HTTPException(status_code=400, detail="item_type 必须是 document 或 asset")
    n = db.query(Share).filter(
        Share.item_type == item_type, Share.item_id == item_id
    ).delete()
    db.commit()
    return {"message": f"已撤销 {n} 条分享", "deleted": n}


@router.delete("/{share_id}", summary="撤销分享（仅管理员）")
async def delete_share(
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以撤销分享")
    share = db.query(Share).filter(Share.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享记录不存在")
    db.delete(share)
    db.commit()
    return {"message": "分享已撤销", "share_id": share_id}


@router.get("/by-item", response_model=List[ShareOut], summary="查询条目已分享用户（仅管理员）")
async def shares_by_item(
    item_type: str = Query(...),
    item_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以查看分享记录")
    rows = db.query(Share, User.username).outerjoin(
        User, User.id == Share.shared_with_id
    ).filter(
        Share.item_type == item_type, Share.item_id == item_id
    ).all()
    return [
        ShareOut(
            id=s.id, item_type=s.item_type, item_id=s.item_id,
            shared_by_id=s.shared_by_id, shared_with_id=s.shared_with_id,
            shared_with_username=u,
        )
        for s, u in rows
    ]


@router.get("/mine", response_model=List[ShareOut], summary="我被分享的条目")
async def my_shares(
    item_type: Optional[str] = Query(None, description="document | asset，可选过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = db.query(Share).filter(Share.shared_with_id == current_user.id)
    if item_type:
        q = q.filter(Share.item_type == item_type)
    rows = q.all()
    return [
        ShareOut(
            id=s.id, item_type=s.item_type, item_id=s.item_id,
            shared_by_id=s.shared_by_id, shared_with_id=s.shared_with_id,
        )
        for s in rows
    ]
