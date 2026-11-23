# -*- coding: utf-8 -*-
"""
分享模型（32.1）

管理员把指定文档/资产分享给某个普通用户：被分享者**只读**可见（不能改删）。
归属模型回顾：
- documents.owner_id / assets.creator_id —— 私有可见性锚点
- shares —— 跨用户的只读可见性授权，管理员发起
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from app.db.database import Base


class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    # 'document' | 'asset'
    item_type = Column(String(20), nullable=False, index=True)
    item_id = Column(Integer, nullable=False, index=True)
    # 分享发起者（管理员）
    shared_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # 被分享者（普通用户，只读）
    shared_with_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 同一条目对同一用户只分享一次
    __table_args__ = (
        UniqueConstraint("item_type", "item_id", "shared_with_id", name="uq_share_item_user"),
    )
