from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Union[str, int, dict], 
    expires_delta: Optional[timedelta] = None,
    token_type: str = "access",
    device_id: Optional[str] = None,
    additional_claims: Optional[Dict[str, Any]] = None
):
    """
    创建JWT访问令牌
    
    Args:
        subject: 用户ID或数据字典
        expires_delta: 过期时间
        token_type: 令牌类型 (access, refresh, mobile)
        device_id: 设备ID (用于移动端绑定)
        additional_claims: 额外的声明
    """
    # 处理主体数据
    if isinstance(subject, dict):
        to_encode = subject.copy()
    else:
        to_encode = {"sub": str(subject)}
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # 根据令牌类型设置默认过期时间
        if token_type == "refresh":
            expire = datetime.utcnow() + timedelta(days=60)  # 刷新令牌60天
        elif token_type == "mobile":
            expire = datetime.utcnow() + timedelta(days=30)  # 移动端30天
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 添加标准声明
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": token_type,
        "jti": str(uuid.uuid4())  # JWT ID，用于令牌管理
    })
    
    # 添加设备绑定
    if device_id:
        to_encode["device_id"] = device_id
    
    # 添加额外声明
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """验证JWT令牌"""
    try:
        # 先尝试作为标准JWT解码
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        # 如果JWT解码失败，尝试作为simple base64 token（用于direct-login）
        try:
            import base64
            import json
            from datetime import datetime
            
            decoded_data = base64.b64decode(token).decode()
            payload = json.loads(decoded_data)
            
            # 检查token是否过期
            if "exp" in payload:
                exp_timestamp = payload["exp"]
                if datetime.now().timestamp() > exp_timestamp:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="令牌已过期",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
            return payload
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据",
                headers={"WWW-Authenticate": "Bearer"},
            )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def generate_password_reset_token(email: str) -> str:
    """生成密码重置令牌"""
    delta = timedelta(hours=1)  # 1小时过期
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email}, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """验证密码重置令牌"""
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return decoded_token["sub"]
    except JWTError:
        return None


def create_refresh_token(user_id: int, device_id: Optional[str] = None) -> str:
    """创建刷新令牌"""
    return create_access_token(
        subject=user_id,
        token_type="refresh",
        device_id=device_id,
        expires_delta=timedelta(days=60)
    )


def verify_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """验证刷新令牌"""
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # 检查令牌类型
        if payload.get("type") != "refresh":
            return None
            
        return payload
    except JWTError:
        return None


def create_mobile_tokens(user_id: int, device_id: Optional[str] = None) -> Dict[str, Any]:
    """创建移动端令牌对（访问令牌 + 刷新令牌）"""
    # 创建访问令牌（30天）
    access_token = create_access_token(
        subject=user_id,
        token_type="mobile",
        device_id=device_id,
        expires_delta=timedelta(days=30)
    )
    
    # 创建刷新令牌（60天）
    refresh_token = create_refresh_token(user_id, device_id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 30 * 24 * 60 * 60,  # 30天的秒数
        "token_type": "bearer"
    }


def validate_device_token(token: str, device_id: str) -> bool:
    """验证令牌是否与指定设备匹配"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_device_id = payload.get("device_id")
        
        # 如果令牌没有设备绑定，允许通过（向后兼容）
        if not token_device_id:
            return True
            
        return token_device_id == device_id
    except JWTError:
        return False


def extract_user_id_from_token(token: str) -> Optional[int]:
    """从令牌中提取用户ID"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except (JWTError, ValueError):
        return None