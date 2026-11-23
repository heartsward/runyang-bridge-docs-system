import logging
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_token
from app.crud import user as crud_user
from app.db.database import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


def _authenticate_mcp_token(token: str, db: Session) -> Optional[User]:
    """32.3：MCP 验证码通道（REST 也认统一码 / 个人码）。

    与 /mcp 端点同一套口径（core.mcp_auth.resolve_user_by_token）：
    - 命中管理员统一码 → 第一个启用的超管账号
    - 命中某用户个人码 → 该用户
    - 未命中 → None（调用方继续走 JWT）

    取代旧的 API_TOKEN→api_client 服务账号通道（阶段二十八）。
    验证码等价于所映射用户的登录权限；可在 UI 一键重置（旧码当场失效）。
    """
    from app.core.mcp_auth import resolve_user_by_token
    user = resolve_user_by_token(db, token)
    if user is not None:
        logger.info(f"[MCP_TOKEN] 验证码认证通过 → 用户 {user.username} (id={user.id})")
    return user


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
    """获取当前用户

    两条认证通道（32.3）：
    1. MCP 验证码（管理员统一码 / 用户个人码，与 /mcp 同口径）→ 映射用户
    2. JWT（账号密码登录签发，24h 过期）→ users 表按 sub 查用户
    """
    # 通道 1：MCP 验证码（命中直接返回；未命中回落 JWT）
    mcp_user = _authenticate_mcp_token(credentials.credentials, db)
    if mcp_user is not None:
        return mcp_user

    # 通道 2：JWT
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

    # 通道 1：MCP 验证码（optional 场景下命中即返回）
    try:
        mcp_user = _authenticate_mcp_token(credentials.credentials, db)
        if mcp_user is not None:
            return mcp_user
    except HTTPException:
        return None

    # 通道 2：JWT
    try:
        payload = verify_token(credentials.credentials)
        username: str = payload.get("sub")
        if username is None:
            return None

        user = crud_user.get_by_username(db, username=username)
        return user
    except Exception:
        return None

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