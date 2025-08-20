# -*- coding: utf-8 -*-
"""
用户设置API端点
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext

from app.core.deps import get_db, get_current_active_user
from app.models.user import User

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 用户管理相关模型
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = None
    department: str = None
    position: str = None
    phone: str = None
    is_superuser: bool = False

class UserUpdate(BaseModel):
    username: str = None
    email: str = None
    full_name: str = None
    department: str = None
    position: str = None
    phone: str = None
    is_active: bool = None
    is_superuser: bool = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str = None
    department: str = None
    position: str = None
    phone: str = None
    is_active: bool
    is_superuser: bool
    created_at: str = None

    class Config:
        from_attributes = True


# 权限检查函数
def check_admin_permission(current_user: User):
    """检查用户是否为管理员"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要管理员权限")

# 用户管理端点
@router.get("/users", response_model=List[UserResponse], summary="获取所有用户")
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有用户列表 - 仅管理员可访问"""
    check_admin_permission(current_user)
    
    users = db.query(User).all()
    result = []
    for user in users:
        try:
            user_data = {
                "id": user.id,
                "username": user.username or "",
                "email": user.email or "",
                "full_name": user.full_name or "",
                "department": user.department or "",
                "position": user.position or "",
                "phone": user.phone or "",
                "is_active": bool(user.is_active),
                "is_superuser": bool(user.is_superuser),
                "created_at": user.created_at.isoformat() if user.created_at else ""
            }
            result.append(UserResponse(**user_data))
        except Exception as e:
            print(f"Error processing user {user.id}: {e}")
            continue
    return result

@router.post("/users", response_model=UserResponse, summary="创建新用户")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新用户 - 仅管理员可访问"""
    check_admin_permission(current_user)
    
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    hashed_password = pwd_context.hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        department=user_data.department,
        position=user_data.position,
        phone=user_data.phone,
        is_superuser=user_data.is_superuser,
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        department=db_user.department,
        position=db_user.position,
        phone=db_user.phone,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None
    )

@router.put("/users/{user_id}", response_model=UserResponse, summary="更新用户信息")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新用户信息 - 仅管理员可访问"""
    check_admin_permission(current_user)
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    for field, value in user_data.dict(exclude_unset=True).items():
        if field == "username" and value:
            # 检查用户名是否已被其他用户使用
            existing_user = db.query(User).filter(User.username == value, User.id != user_id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="用户名已被其他用户使用")
        elif field == "email" and value:
            # 检查邮箱是否已被其他用户使用
            existing_user = db.query(User).filter(User.email == value, User.id != user_id).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        full_name=db_user.full_name,
        department=db_user.department,
        position=db_user.position,
        phone=db_user.phone,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None
    )

@router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除用户 - 仅管理员可访问"""
    check_admin_permission(current_user)
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除自己
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")
    
    # 不能删除其他超级管理员
    if db_user.is_superuser:
        raise HTTPException(status_code=400, detail="不能删除管理员账户")
    
    db.delete(db_user)
    db.commit()
    
    return {"message": "用户删除成功"}