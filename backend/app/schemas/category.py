# -*- coding: utf-8 -*-
"""
分类数据模型
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """分类基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="分类颜色（十六进制）")
    icon: Optional[str] = Field(None, max_length=50, description="分类图标")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: int = Field(0, ge=0, description="排序顺序")


class CategoryCreate(CategoryBase):
    """创建分类模型"""
    pass


class CategoryUpdate(BaseModel):
    """更新分类模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="分类名称")
    description: Optional[str] = Field(None, max_length=500, description="分类描述")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="分类颜色")
    icon: Optional[str] = Field(None, max_length=50, description="分类图标")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: Optional[int] = Field(None, ge=0, description="排序顺序")
    is_active: Optional[bool] = Field(None, description="是否激活")


class CategoryMove(BaseModel):
    """移动分类模型"""
    new_parent_id: Optional[int] = Field(None, description="新的父分类ID")


class Category(CategoryBase):
    """分类响应模型"""
    id: int
    is_active: bool
    creator_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    document_count: Optional[int] = Field(None, description="文档数量")
    
    class Config:
        from_attributes = True


class CategoryTree(Category):
    """分类树形结构模型"""
    children: List['CategoryTree'] = []
    
    class Config:
        from_attributes = True


class CategoryStatistics(BaseModel):
    """分类统计模型"""
    categories: List[dict]
    uncategorized_count: int
    total_categories: int


class CategoryOption(BaseModel):
    """分类选项模型（用于下拉选择）"""
    id: int
    name: str
    color: Optional[str]
    icon: Optional[str]
    level: int = 0  # 层级深度
    
    class Config:
        from_attributes = True


# 更新前向引用
CategoryTree.model_rebuild()