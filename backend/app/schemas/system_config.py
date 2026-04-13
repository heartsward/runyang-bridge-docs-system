# -*- coding: utf-8 -*-
"""
系统配置Pydantic模式
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SystemConfigBase(BaseModel):
    """系统配置基础模式"""
    key: str
    value: str
    description: Optional[str] = None


class SystemConfigCreate(SystemConfigBase):
    """创建系统配置"""
    pass


class SystemConfigUpdate(BaseModel):
    """更新系统配置"""
    value: str
    description: Optional[str] = None


class SystemConfigResponse(SystemConfigBase):
    """系统配置响应"""
    id: int

    class Config:
        from_attributes = True


class SystemOptionsResponse(BaseModel):
    """系统选项响应（用于前端下拉框）"""
    asset_types: List[Dict[str, str]] = []
    departments: List[str] = []
