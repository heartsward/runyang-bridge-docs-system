# -*- coding: utf-8 -*-
"""
分类CRUD操作
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.document import Category
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category(db: Session, category_id: int, user_id: int) -> Optional[Category]:
    """获取单个分类"""
    return db.query(Category).filter(
        Category.id == category_id,
        or_(Category.creator_id == user_id, Category.creator_id.is_(None))  # 允许访问公共分类
    ).first()


def get_categories(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    parent_id: Optional[int] = None,
    include_inactive: bool = False
) -> List[Category]:
    """获取分类列表"""
    query = db.query(Category).filter(
        or_(Category.creator_id == user_id, Category.creator_id.is_(None))
    )
    
    if parent_id is not None:
        query = query.filter(Category.parent_id == parent_id)
    
    if not include_inactive:
        query = query.filter(Category.is_active == True)
    
    return query.order_by(Category.sort_order, Category.name).offset(skip).limit(limit).all()


def get_category_tree(db: Session, user_id: int) -> List[Category]:
    """获取分类树结构"""
    # 先获取所有根分类
    root_categories = db.query(Category).filter(
        Category.parent_id.is_(None),
        or_(Category.creator_id == user_id, Category.creator_id.is_(None)),
        Category.is_active == True
    ).order_by(Category.sort_order, Category.name).all()
    
    # 递归加载子分类
    def load_children(category: Category):
        children = db.query(Category).filter(
            Category.parent_id == category.id,
            or_(Category.creator_id == user_id, Category.creator_id.is_(None)),
            Category.is_active == True
        ).order_by(Category.sort_order, Category.name).all()
        
        for child in children:
            load_children(child)
        
        category.children = children
    
    for category in root_categories:
        load_children(category)
    
    return root_categories


def create_category(db: Session, category: CategoryCreate, user_id: int) -> Category:
    """创建分类"""
    db_category = Category(
        name=category.name,
        description=category.description,
        color=category.color,
        icon=category.icon,
        parent_id=category.parent_id,
        sort_order=category.sort_order,
        creator_id=user_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(
    db: Session, 
    category_id: int, 
    category_update: CategoryUpdate, 
    user_id: int
) -> Optional[Category]:
    """更新分类"""
    db_category = db.query(Category).filter(
        Category.id == category_id,
        Category.creator_id == user_id  # 只允许创建者修改
    ).first()
    
    if not db_category:
        return None
    
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int, user_id: int) -> bool:
    """删除分类（软删除）"""
    db_category = db.query(Category).filter(
        Category.id == category_id,
        Category.creator_id == user_id
    ).first()
    
    if not db_category:
        return False
    
    # 检查是否有子分类
    has_children = db.query(Category).filter(Category.parent_id == category_id).first()
    if has_children:
        return False  # 有子分类时不允许删除
    
    # 检查是否有关联文档
    if db_category.documents:
        # 有关联文档时，将文档的分类设为None
        for doc in db_category.documents:
            doc.category_id = None
    
    # 软删除
    db_category.is_active = False
    db.commit()
    return True


def get_category_statistics(db: Session, user_id: int) -> dict:
    """获取分类统计信息"""
    from app.models.document import Document
    
    # 获取各分类的文档数量
    categories_with_count = db.query(
        Category.id,
        Category.name,
        Category.color,
        db.func.count(Document.id).label('document_count')
    ).outerjoin(Document).filter(
        or_(Category.creator_id == user_id, Category.creator_id.is_(None)),
        Category.is_active == True
    ).group_by(Category.id, Category.name, Category.color).all()
    
    # 未分类文档数量
    uncategorized_count = db.query(Document).filter(
        Document.owner_id == user_id,
        Document.category_id.is_(None)
    ).count()
    
    return {
        "categories": [
            {
                "id": cat.id,
                "name": cat.name,
                "color": cat.color,
                "document_count": cat.document_count
            }
            for cat in categories_with_count
        ],
        "uncategorized_count": uncategorized_count,
        "total_categories": len(categories_with_count)
    }


def move_category(
    db: Session, 
    category_id: int, 
    new_parent_id: Optional[int], 
    user_id: int
) -> Optional[Category]:
    """移动分类到新的父分类"""
    db_category = db.query(Category).filter(
        Category.id == category_id,
        Category.creator_id == user_id
    ).first()
    
    if not db_category:
        return None
    
    # 检查新父分类是否存在且有权限访问
    if new_parent_id is not None:
        new_parent = db.query(Category).filter(
            Category.id == new_parent_id,
            or_(Category.creator_id == user_id, Category.creator_id.is_(None))
        ).first()
        if not new_parent:
            return None
        
        # 检查是否会形成循环引用
        if _would_create_cycle(db, category_id, new_parent_id):
            return None
    
    db_category.parent_id = new_parent_id
    db.commit()
    db.refresh(db_category)
    return db_category


def _would_create_cycle(db: Session, category_id: int, new_parent_id: int) -> bool:
    """检查移动分类是否会创建循环引用"""
    current_id = new_parent_id
    while current_id is not None:
        if current_id == category_id:
            return True
        
        parent = db.query(Category).filter(Category.id == current_id).first()
        current_id = parent.parent_id if parent else None
    
    return False