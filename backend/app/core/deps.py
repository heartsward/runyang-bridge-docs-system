from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_token
from app.crud import user as crud_user
from app.db.database import SessionLocal
from app.models.user import User

security = HTTPBearer()


def get_db() -> Generator:
    """获取数据库会话"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前用户"""
    try:
        payload = verify_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = crud_user.get_by_username(db, username=username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前激活用户"""
    if not crud_user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="用户未激活"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前超级用户"""
    if not crud_user.is_superuser(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user


def get_optional_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """获取可选用户（允许匿名）"""
    if not credentials:
        return None

    try:
        payload = verify_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            return None

        user = crud_user.get_by_username(db, username=username)
        return user
    except Exception:
        return None


def get_user_for_iframe(
    db: Session = Depends(get_db),
    token: Optional[str] = None,  # Query 参数 ?token=xxx，由前端 iframe URL 传入
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> User:
    """阶段二十六·26.10：iframe 专用认证

    浏览器原生 iframe 发请求不会带 axios 拦截器注入的 Authorization header，
    因此 converted-pdf 端点必须接受 URL query token 才能正常返回 PDF。
    优先级：Authorization Bearer > query token > 都缺失则 401。
    """
    raw_token = None
    if credentials and credentials.credentials:
        raw_token = credentials.credentials
    elif token and token.strip():
        raw_token = token.strip()

    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail="缺少认证凭据（iframe 需带 token 查询参数）",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(raw_token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="认证凭据无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="token 缺少 sub 字段")

    user = crud_user.get_by_username(db, username=username)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户账户未激活")
    return user


def require_test_endpoints_enabled() -> None:
    """
    测试/调试端点门禁依赖

    当 ENABLE_TEST_ENDPOINTS=False（默认）时返回 404（伪装成端点不存在）
    当 ENABLE_TEST_ENDPOINTS=True 时放行（开发/调试用）

    使用方法：在端点签名上加 `Depends(require_test_endpoints_enabled)`
    """
    if not settings.ENABLE_TEST_ENDPOINTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found",
        )