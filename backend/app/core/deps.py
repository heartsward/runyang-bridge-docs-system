import hmac
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


def _authenticate_api_token(token: str, db: Session) -> Optional[User]:
    """阶段二十八：API 固定令牌通道（服务账号）。

    - 开关关闭 / 未配置令牌 → 返回 None（调用方继续走 JWT）
    - 令牌匹配（hmac.compare_digest 防时序攻击）→ 返回服务账号 User
    - 令牌匹配但服务账号缺失/被禁用 → 直接 401（不回落 JWT，
      否则报"无效的认证凭据"会误导排查）
    """
    if not settings.API_TOKEN_ENABLED or not settings.API_TOKEN:
        return None
    if not hmac.compare_digest(token.encode("utf-8", "surrogatepass"),
                               settings.API_TOKEN.encode("utf-8", "surrogatepass")):
        return None

    user = crud_user.get_by_username(db, username=settings.API_SERVICE_USERNAME)
    if user is None:
        logger.warning(
            f"[API_TOKEN] 令牌命中但服务账号 '{settings.API_SERVICE_USERNAME}' 不存在，"
            f"请先运行 init_api_service_user.py"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API 令牌有效但服务账号 '{settings.API_SERVICE_USERNAME}' 不存在（请先运行 init_api_service_user.py）",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not crud_user.is_active(user):
        logger.warning(f"[API_TOKEN] 服务账号 '{user.username}' 已被禁用，拒绝访问")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API 服务账号已被禁用",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"[API_TOKEN] 固定令牌认证通过 → 服务账号 {user.username} (id={user.id})")
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

    两条认证通道（阶段二十八）：
    1. API 固定令牌（Bearer == settings.API_TOKEN）→ 服务账号（审计可区分脚本/人工）
    2. JWT（账号密码登录签发，24h 过期）→ users 表按 sub 查用户
    """
    # 通道 1：API 固定令牌（命中直接返回；配置错误会抛 401）
    api_user = _authenticate_api_token(credentials.credentials, db)
    if api_user is not None:
        return api_user

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

    # 通道 1：API 固定令牌（optional 场景下命中服务账号即返回；配置错误吞掉不阻断匿名）
    try:
        api_user = _authenticate_api_token(credentials.credentials, db)
        if api_user is not None:
            return api_user
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