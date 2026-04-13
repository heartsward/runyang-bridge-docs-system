# -*- coding: utf-8 -*-
"""
AI配置数据库模型
用于持久化用户的AI服务配置
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class AIUserConfig(Base):
    """用户AI配置表"""
    __tablename__ = "ai_user_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # AI通用配置
    default_provider = Column(String(50), default="openai")  # openai, anthropic, alibaba, zhipu, minimax, custom
    enabled = Column(Boolean, default=True)
    fallback_enabled = Column(Boolean, default=True)
    cost_limit_enabled = Column(Boolean, default=False)
    daily_cost_limit = Column(Float, default=10.0)
    cache_enabled = Column(Boolean, default=True)
    cache_ttl = Column(Integer, default=3600)

    # 各提供商配置（JSON格式存储）
    providers_config = Column(Text, nullable=True, default=None)  # JSON字符串

    # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="ai_configs")
