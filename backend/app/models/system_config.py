# -*- coding: utf-8 -*-
"""
系统配置数据库模型
用于存储可自定义的系统选项，如设备类型、部门等
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False, comment="配置键名")
    value = Column(Text, nullable=False, comment="配置值(JSON格式)")
    description = Column(String(500), nullable=True, comment="配置描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
