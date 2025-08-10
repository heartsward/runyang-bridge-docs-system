from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.deps import get_db, get_current_user
from app.core.security import create_access_token
from app.crud import user as crud_user
from app.schemas.user import Token, User, UserCreate, PasswordChange

router = APIRouter()


@router.post("/login", response_model=Token, summary="用户登录")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    用户登录接口
    """
    user = crud_user.authenticate(
        db, username=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not crud_user.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户未激活"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=User, summary="用户注册")
def register(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
):
    """
    用户注册接口
    """
    # 检查用户名是否已存在
    user = crud_user.get_by_username(db, username=user_in.username)
    if user:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    user = crud_user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="邮箱已被注册",
        )
    
    user = crud_user.create(db, obj_in=user_in)
    return user


@router.get("/me", response_model=User, summary="获取当前用户信息")
def read_users_me(
    current_user: User = Depends(get_current_user),
):
    """
    获取当前用户信息
    """
    return current_user


@router.post("/test-token", response_model=User, summary="测试token")
def test_token(current_user: User = Depends(get_current_user)):
    """
    测试访问令牌
    """
    return current_user


@router.post("/change-password", summary="修改密码")
def change_password(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    password_change: PasswordChange
):
    """
    修改用户密码
    """
    # 验证当前密码
    if not crud_user.authenticate(db, username=current_user.username, password=password_change.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    user_update = {"password": password_change.new_password}
    crud_user.update_password(db, db_obj=current_user, new_password=password_change.new_password)
    
    return {"message": "密码修改成功"}