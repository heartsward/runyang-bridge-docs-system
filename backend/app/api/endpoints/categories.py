# -*- coding: utf-8 -*-
"""
分类管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.crud import category as crud_category
from app.schemas.category import (
    Category, CategoryCreate, CategoryUpdate, CategoryMove,
    CategoryTree, CategoryStatistics, CategoryOption
)

router = APIRouter()


@router.get("/", response_model=List[Category], summary="获取分类列表")
async def get_categories(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    parent_id: Optional[int] = Query(None, description="父分类ID，为空则获取根分类"),
    include_inactive: bool = Query(False, description="是否包含已停用的分类"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取分类列表"""
    categories = crud_category.get_categories(
        db=db, 
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        parent_id=parent_id,
        include_inactive=include_inactive
    )
    
    # 添加文档数量统计
    from app.models.document import Document
    for category in categories:
        category.document_count = db.query(Document).filter(
            Document.category_id == category.id,
            Document.owner_id == current_user.id
        ).count()
    
    return categories


@router.get("/tree", response_model=List[CategoryTree], summary="获取分类树")
async def get_category_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取完整的分类树结构"""
    return crud_category.get_category_tree(db=db, user_id=current_user.id)


@router.get("/options", response_model=List[CategoryOption], summary="获取分类选项")
async def get_category_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用于下拉选择的分类选项列表"""
    categories = crud_category.get_category_tree(db=db, user_id=current_user.id)
    
    def flatten_tree(categories_list: List, level: int = 0) -> List[CategoryOption]:
        options = []
        for category in categories_list:
            option = CategoryOption(
                id=category.id,
                name="  " * level + category.name,  # 用缩进表示层级
                color=category.color,
                icon=category.icon,
                level=level
            )
            options.append(option)
            
            # 递归处理子分类
            if hasattr(category, 'children') and category.children:
                options.extend(flatten_tree(category.children, level + 1))
        
        return options
    
    return flatten_tree(categories)


@router.get("/statistics", response_model=CategoryStatistics, summary="获取分类统计")
async def get_category_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取分类统计信息"""
    return crud_category.get_category_statistics(db=db, user_id=current_user.id)


@router.get("/{category_id}", response_model=Category, summary="获取分类详情")
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取指定分类的详细信息"""
    category = crud_category.get_category(db=db, category_id=category_id, user_id=current_user.id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 添加文档数量
    from app.models.document import Document
    category.document_count = db.query(Document).filter(
        Document.category_id == category.id,
        Document.owner_id == current_user.id
    ).count()
    
    return category


@router.post("/", response_model=Category, summary="创建分类")
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新分类"""
    # 检查父分类是否存在
    if category.parent_id:
        parent = crud_category.get_category(db=db, category_id=category.parent_id, user_id=current_user.id)
        if not parent:
            raise HTTPException(status_code=400, detail="父分类不存在")
    
    # 检查同级分类名称是否重复
    existing = db.query(crud_category.Category).filter(
        crud_category.Category.name == category.name,
        crud_category.Category.parent_id == category.parent_id,
        crud_category.Category.creator_id == current_user.id,
        crud_category.Category.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="同级分类中已存在相同名称的分类")
    
    return crud_category.create_category(db=db, category=category, user_id=current_user.id)


@router.put("/{category_id}", response_model=Category, summary="更新分类")
async def update_category(
    category_id: int,
    category_update: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新分类信息"""
    # 检查分类是否存在
    from app.models.document import Category as CategoryModel
    existing_category = db.query(CategoryModel).filter(
        CategoryModel.id == category_id,
        CategoryModel.creator_id == current_user.id
    ).first()
    if not existing_category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 检查是否为创建者
    if existing_category.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有创建者可以修改分类")
    
    # 如果更新了名称，检查同级是否重复
    if category_update.name and category_update.name != existing_category.name:
        duplicate = db.query(crud_category.Category).filter(
            crud_category.Category.name == category_update.name,
            crud_category.Category.parent_id == existing_category.parent_id,
            crud_category.Category.creator_id == current_user.id,
            crud_category.Category.id != category_id,
            crud_category.Category.is_active == True
        ).first()
        
        if duplicate:
            raise HTTPException(status_code=400, detail="同级分类中已存在相同名称的分类")
    
    updated_category = crud_category.update_category(
        db=db, 
        category_id=category_id, 
        category_update=category_update, 
        user_id=current_user.id
    )
    
    if not updated_category:
        raise HTTPException(status_code=404, detail="更新失败")
    
    return updated_category


@router.post("/{category_id}/move", response_model=Category, summary="移动分类")
async def move_category(
    category_id: int,
    move_data: CategoryMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """移动分类到新的父分类下"""
    moved_category = crud_category.move_category(
        db=db,
        category_id=category_id,
        new_parent_id=move_data.new_parent_id,
        user_id=current_user.id
    )
    
    if not moved_category:
        raise HTTPException(status_code=400, detail="移动失败，可能是权限不足或会形成循环引用")
    
    return moved_category


@router.delete("/{category_id}", summary="删除分类")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除分类（软删除）"""
    success = crud_category.delete_category(db=db, category_id=category_id, user_id=current_user.id)
    
    if not success:
        raise HTTPException(status_code=400, detail="删除失败，可能是权限不足或分类下有子分类")
    
    return {"message": "分类删除成功"}


@router.post("/init-default", summary="初始化默认分类")
async def init_default_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """为当前用户初始化默认的运维分类"""
    default_categories = [
        {
            "name": "服务器管理",
            "description": "服务器配置、维护、监控相关文档",
            "color": "#1890ff",
            "icon": "server-outline",
            "sort_order": 1
        },
        {
            "name": "网络设备",
            "description": "交换机、路由器、防火墙等网络设备文档",
            "color": "#52c41a",
            "icon": "wifi-outline",
            "sort_order": 2
        },
        {
            "name": "数据库",
            "description": "数据库安装、配置、优化、备份文档",
            "color": "#faad14",
            "icon": "library-outline",
            "sort_order": 3
        },
        {
            "name": "应用部署",
            "description": "应用程序部署、配置、更新文档",
            "color": "#722ed1",
            "icon": "cube-outline",
            "sort_order": 4
        },
        {
            "name": "监控告警",
            "description": "监控系统、告警配置、故障排查文档",
            "color": "#f5222d",
            "icon": "pulse-outline",
            "sort_order": 5
        },
        {
            "name": "安全策略",
            "description": "安全配置、权限管理、审计相关文档",
            "color": "#fa541c",
            "icon": "shield-checkmark-outline",
            "sort_order": 6
        },
        {
            "name": "运维工具",
            "description": "运维工具使用说明、脚本、自动化文档",
            "color": "#13c2c2",
            "icon": "construct-outline",
            "sort_order": 7
        },
        {
            "name": "运维手册",
            "description": "操作手册、流程规范、应急预案",
            "color": "#eb2f96",
            "icon": "book-outline",
            "sort_order": 8
        }
    ]
    
    created_count = 0
    for cat_data in default_categories:
        # 检查是否已存在
        existing = db.query(crud_category.Category).filter(
            crud_category.Category.name == cat_data["name"],
            crud_category.Category.creator_id == current_user.id
        ).first()
        
        if not existing:
            category_create = CategoryCreate(**cat_data)
            crud_category.create_category(db=db, category=category_create, user_id=current_user.id)
            created_count += 1
    
    return {"message": f"成功创建 {created_count} 个默认分类"}