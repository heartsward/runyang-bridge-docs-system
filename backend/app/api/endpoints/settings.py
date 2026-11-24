# -*- coding: utf-8 -*-
"""
用户设置API端点
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query  # 32.8：Query 用于取消共享端点
from sqlalchemy.orm import Session
from pydantic import BaseModel
from passlib.context import CryptContext

from app.core.deps import get_db, get_current_active_user
from app.core.config import settings
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
    password: str = None  # 添加密码字段

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[str] = None
    # 32.2：MCP 个人验证码（普通用户有值；管理员为 None——用统一码）
    mcp_token: Optional[str] = None
    # 32.8：被分享条目计数（文档/资产分开），管理员用户列表用于显示"取消共享"按钮
    share_doc_count: int = 0
    share_asset_count: int = 0

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

    # 32.8：一次聚合查出每个用户被分享的文档数/资产数（避免 N+1）
    from app.models.share import Share
    from sqlalchemy import func as _func
    share_counts: dict = {}  # user_id -> {'document': n, 'asset': m}
    for uid, itype, cnt in db.query(
        Share.shared_with_id, Share.item_type, _func.count(Share.id)
    ).group_by(Share.shared_with_id, Share.item_type).all():
        share_counts.setdefault(uid, {})[itype] = cnt

    for user in users:
        try:
            sc = share_counts.get(user.id, {})
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
                "created_at": user.created_at.isoformat() if user.created_at else "",
                "mcp_token": user.mcp_token,  # 32.2：管理员界面直接可见各用户码
                "share_doc_count": sc.get("document", 0),    # 32.8
                "share_asset_count": sc.get("asset", 0),     # 32.8
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

    # 32.2：普通用户创建时自动发 MCP 个人验证码；管理员保持 NULL（用统一码）
    if not user_data.is_superuser:
        from app.core.mcp_auth import gen_mcp_token
        db_user.mcp_token = gen_mcp_token()

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
        created_at=db_user.created_at.isoformat() if db_user.created_at else None,
        mcp_token=db_user.mcp_token,
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

    # 32.2：升降级自动切换 MCP 验证码——
    #   普通→管理员：清空个人码（改用统一管理员码）
    #   管理员→普通：自动生成个人码
    old_is_superuser = bool(db_user.is_superuser)

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
        elif field == "password" and value and value.strip():
            # 特殊处理密码字段 - 需要加密存储
            hashed_password = pwd_context.hash(value.strip())
            setattr(db_user, "hashed_password", hashed_password)
            continue  # 跳过设置原始密码

        # 32.2：mcp_token 不允许通过用户编辑表单直接改（防绕过升降级钩子/注入）
        elif field == "mcp_token":
            continue

        # 设置其他字段（跳过空的密码字段）
        if field != "password":
            setattr(db_user, field, value)

    # 32.2：根据升降级结果调整 mcp_token（old_is_superuser 在字段更新前已捕获）
    new_is_superuser = bool(db_user.is_superuser)
    if new_is_superuser and not old_is_superuser:
        db_user.mcp_token = None  # 升级：去掉个人码，用管理员统一码
    elif old_is_superuser and not new_is_superuser:
        from app.core.mcp_auth import gen_mcp_token
        db_user.mcp_token = gen_mcp_token()  # 降级：生成个人码

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
        created_at=db_user.created_at.isoformat() if db_user.created_at else None,
        mcp_token=db_user.mcp_token,
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
    
    # 32.8：删除用户前，先撤销分享给该用户的所有文档/资产（否则留孤儿 Share 行）
    from app.models.share import Share
    cancelled = db.query(Share).filter(Share.shared_with_id == user_id).delete()
    if cancelled:
        print(f"[delete_user] 用户 {user_id} 删除前已自动取消 {cancelled} 条分享")

    db.delete(db_user)
    db.commit()
    
    return {"message": "用户删除成功", "shares_cancelled": cancelled}


@router.delete("/users/{user_id}/shares", summary="一键取消分享给该用户的全部条目（仅管理员，32.8）")
async def cancel_user_shares(
    user_id: int,
    item_type: Optional[str] = Query(None, description="document | asset；不传=两者都取消"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """用户管理界面「取消共享」按钮：撤销分享给该用户的所有文档/资产（可分开调用）。"""
    check_admin_permission(current_user)
    if item_type not in (None, "document", "asset"):
        raise HTTPException(status_code=400, detail="item_type 必须是 document 或 asset")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from app.models.share import Share
    q = db.query(Share).filter(Share.shared_with_id == user_id)
    if item_type:
        q = q.filter(Share.item_type == item_type)
    cancelled = q.delete(synchronize_session=False)
    db.commit()
    return {"message": f"已取消 {cancelled} 条分享", "cancelled": cancelled,
            "item_type": item_type or "all"}


# ============ 32.2：MCP 验证码管理 ============

@router.get("/mcp-token/me", summary="查看我的 MCP 验证码状态")
async def get_my_mcp_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """当前用户的 MCP 调用验证码：
    - 普通用户：返回个人码（mcp_token）
    - 管理员：个人码为空，返回系统统一码（管理员统一用这一个）
    """
    if current_user.is_superuser:
        from app.core.mcp_auth import get_or_create_admin_token
        return {
            "mode": "admin",
            "token": get_or_create_admin_token(db),
            "can_regenerate_personal": False,
            "note": "管理员使用统一 MCP 验证码",
        }
    if not current_user.mcp_token:
        # 兜底：历史普通用户没码（迁移脚本没跑的库）——读取时自动补发
        from app.core.mcp_auth import gen_mcp_token
        current_user.mcp_token = gen_mcp_token()
        db.commit()
        db.refresh(current_user)
    return {
        "mode": "personal",
        "token": current_user.mcp_token,
        "can_regenerate_personal": True,
        "note": "个人 MCP 验证码，可随时重新随机",
    }


@router.post("/mcp-token/me/regenerate", summary="重新随机我的 MCP 验证码")
async def regenerate_my_mcp_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """普通用户重新随机个人码（旧码立即失效）。管理员不适用（用统一码）。"""
    if current_user.is_superuser:
        raise HTTPException(status_code=400, detail="管理员使用统一 MCP 验证码，无个人码可重置")
    from app.core.mcp_auth import gen_mcp_token
    current_user.mcp_token = gen_mcp_token()
    db.commit()
    return {"message": "MCP 验证码已重新生成，旧码立即失效", "token": current_user.mcp_token}


@router.get("/mcp-token/admin", summary="查看管理员统一 MCP 验证码")
async def get_admin_mcp_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """仅管理员：查看统一 MCP 验证码（所有管理员共用）"""
    check_admin_permission(current_user)
    from app.core.mcp_auth import get_or_create_admin_token
    return {"token": get_or_create_admin_token(db)}


@router.post("/mcp-token/admin/regenerate", summary="重置管理员统一 MCP 验证码")
async def regenerate_admin_mcp_token(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """仅管理员：重新随机统一码（所有管理员的 MCP 客户端需同步更换）"""
    check_admin_permission(current_user)
    from app.core.mcp_auth import gen_mcp_token, ADMIN_MCP_TOKEN_KEY
    from app.models.system_config import SystemConfig
    import json
    new_token = gen_mcp_token()
    row = db.query(SystemConfig).filter(SystemConfig.key == ADMIN_MCP_TOKEN_KEY).first()
    if row:
        row.value = json.dumps(new_token, ensure_ascii=False)
    else:
        db.add(SystemConfig(key=ADMIN_MCP_TOKEN_KEY, value=json.dumps(new_token, ensure_ascii=False),
                            description="管理员统一 MCP 调用验证码（32.2）"))
    db.commit()
    return {"message": "管理员统一 MCP 验证码已重置，所有管理员客户端需更换新码", "token": new_token}


@router.post("/mcp-token/users/{user_id}/regenerate", summary="重置指定用户的 MCP 验证码")
async def regenerate_user_mcp_token(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """仅管理员：为某个普通用户重新随机个人码（泄露时应急用）"""
    check_admin_permission(current_user)
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if db_user.is_superuser:
        raise HTTPException(status_code=400, detail="管理员无个人码（用统一码）")
    from app.core.mcp_auth import gen_mcp_token
    db_user.mcp_token = gen_mcp_token()
    db.commit()
    return {"message": f"用户 {db_user.username} 的 MCP 验证码已重置", "token": db_user.mcp_token}

# AI配置相关模型
class AIProviderConfig(BaseModel):
    api_key: str = ""
    api_url: str = ""
    model: str = ""
    group_id: str = ""  # MiniMax专用

class AIProvidersConfig(BaseModel):
    openai: AIProviderConfig = AIProviderConfig(
        api_key="",
        api_url="https://api.openai.com/v1/chat/completions",
        model="gpt-4o-mini"
    )
    anthropic: AIProviderConfig = AIProviderConfig(
        api_key="",
        api_url="https://api.anthropic.com/v1/messages",
        model="claude-3-haiku-20240307"
    )
    alibaba: AIProviderConfig = AIProviderConfig(
        api_key="",
        api_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus"
    )
    zhipu: AIProviderConfig = AIProviderConfig(
        api_key="",
        api_url="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        model="glm-4-flash"
    )
    minimax: AIProviderConfig = AIProviderConfig(
        api_key="",
        api_url="https://api.minimaxi.com/v1/chat/completions",
        model="MiniMax-M2.7",
        group_id=""
    )
    custom: AIProviderConfig = AIProviderConfig(
        api_key="",
        api_url="",
        model=""
    )

class AIConfigData(BaseModel):
    default_provider: str = "openai"
    enabled: bool = True
    fallback_enabled: bool = True
    cost_limit_enabled: bool = False
    daily_cost_limit: float = 10.0
    cache_enabled: bool = True
    cache_ttl: int = 3600
    providers: AIProvidersConfig = AIProvidersConfig()
    
    class Config:
        extra = "allow"  # 允许额外的字段

# AI配置相关端点
@router.get("/ai-config", summary="获取AI配置")
async def get_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取AI配置"""
    from app.services.ai.ai_config_service import AIConfigService
    from app.core.config import settings
    
    providers_config = AIProvidersConfig()
    
    # 优先从数据库读取用户配置
    user_config = AIConfigService.get_user_ai_config(db, current_user.id)
    
    if user_config:
        # 使用数据库中的用户配置
        providers_dict = user_config.get("providers", {})
        
        if "openai" in providers_dict:
            providers_config.openai = AIProviderConfig(
                api_key=providers_dict["openai"].get("api_key", ""),
                api_url=providers_dict["openai"].get("api_url", "https://api.openai.com/v1/chat/completions"),
                model=providers_dict["openai"].get("model", "gpt-4o-mini")
            )
        if "anthropic" in providers_dict:
            providers_config.anthropic = AIProviderConfig(
                api_key=providers_dict["anthropic"].get("api_key", ""),
                api_url=providers_dict["anthropic"].get("api_url", "https://api.anthropic.com/v1/messages"),
                model=providers_dict["anthropic"].get("model", "claude-3-haiku-20240307")
            )
        if "alibaba" in providers_dict:
            providers_config.alibaba = AIProviderConfig(
                api_key=providers_dict["alibaba"].get("api_key", ""),
                api_url=providers_dict["alibaba"].get("api_url", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                model=providers_dict["alibaba"].get("model", "qwen-plus")
            )
        if "zhipu" in providers_dict:
            providers_config.zhipu = AIProviderConfig(
                api_key=providers_dict["zhipu"].get("api_key", ""),
                api_url=providers_dict["zhipu"].get("api_url", "https://open.bigmodel.cn/api/paas/v4/chat/completions"),
                model=providers_dict["zhipu"].get("model", "glm-4-flash")
            )
        if "minimax" in providers_dict:
            providers_config.minimax = AIProviderConfig(
                api_key=providers_dict["minimax"].get("api_key", ""),
                api_url=providers_dict["minimax"].get("api_url", "https://api.minimaxi.com/v1/chat/completions"),
                model=providers_dict["minimax"].get("model", "MiniMax-M2.7"),
                group_id=providers_dict["minimax"].get("group_id", "")
            )
        if "custom" in providers_dict:
            providers_config.custom = AIProviderConfig(
                api_key=providers_dict["custom"].get("api_key", ""),
                api_url=providers_dict["custom"].get("api_url", ""),
                model=providers_dict["custom"].get("model", "")
            )
        
        config_data = AIConfigData(
            default_provider=user_config.get("default_provider", "openai"),
            enabled=user_config.get("enabled", True),
            fallback_enabled=user_config.get("fallback_enabled", True),
            cost_limit_enabled=user_config.get("cost_limit_enabled", False),
            daily_cost_limit=user_config.get("daily_cost_limit", 10.0),
            cache_enabled=user_config.get("cache_enabled", True),
            cache_ttl=user_config.get("cache_ttl", 3600),
            providers=providers_config
        )
    else:
        # 使用settings中的默认配置
        if hasattr(settings, 'AI_OPENAI_API_KEY'):
            providers_config.openai.api_key = settings.AI_OPENAI_API_KEY or ""
        if hasattr(settings, 'AI_OPENAI_API_URL'):
            providers_config.openai.api_url = settings.AI_OPENAI_API_URL or "https://api.openai.com/v1/chat/completions"
        if hasattr(settings, 'AI_OPENAI_MODEL'):
            providers_config.openai.model = settings.AI_OPENAI_MODEL or "gpt-4o-mini"
        
        if hasattr(settings, 'AI_ANTHROPIC_API_KEY'):
            providers_config.anthropic.api_key = settings.AI_ANTHROPIC_API_KEY or ""
        if hasattr(settings, 'AI_ANTHROPIC_API_URL'):
            providers_config.anthropic.api_url = settings.AI_ANTHROPIC_API_URL or "https://api.anthropic.com/v1/messages"
        if hasattr(settings, 'AI_ANTHROPIC_MODEL'):
            providers_config.anthropic.model = settings.AI_ANTHROPIC_MODEL or "claude-3-haiku-20240307"
        
        if hasattr(settings, 'AI_ALIBABA_API_KEY'):
            providers_config.alibaba.api_key = settings.AI_ALIBABA_API_KEY or ""
        if hasattr(settings, 'AI_ALIBABA_ENDPOINT'):
            providers_config.alibaba.api_url = settings.AI_ALIBABA_ENDPOINT or "https://dashscope.aliyuncs.com/compatible-mode/v1"
        if hasattr(settings, 'AI_ALIBABA_MODEL'):
            providers_config.alibaba.model = settings.AI_ALIBABA_MODEL or "qwen-plus"
        
        if hasattr(settings, 'AI_ZHIPU_API_KEY'):
            providers_config.zhipu.api_key = settings.AI_ZHIPU_API_KEY or ""
        if hasattr(settings, 'AI_ZHIPU_API_URL'):
            providers_config.zhipu.api_url = settings.AI_ZHIPU_API_URL or "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        if hasattr(settings, 'AI_ZHIPU_MODEL'):
            providers_config.zhipu.model = settings.AI_ZHIPU_MODEL or "glm-4-flash"
        
        if hasattr(settings, 'AI_MINIMAX_API_KEY'):
            providers_config.minimax.api_key = settings.AI_MINIMAX_API_KEY or ""
        if hasattr(settings, 'AI_MINIMAX_API_URL'):
            providers_config.minimax.api_url = settings.AI_MINIMAX_API_URL or "https://api.minimaxi.com/v1/chat/completions"
        if hasattr(settings, 'AI_MINIMAX_MODEL'):
            providers_config.minimax.model = settings.AI_MINIMAX_MODEL or "MiniMax-M2.7"
        if hasattr(settings, 'AI_MINIMAX_GROUP_ID'):
            providers_config.minimax.group_id = settings.AI_MINIMAX_GROUP_ID or ""
        
        config_data = AIConfigData(
            default_provider=getattr(settings, 'AI_DEFAULT_PROVIDER', 'openai'),
            enabled=getattr(settings, 'ENABLE_AI_ANALYSIS', True),
            fallback_enabled=getattr(settings, 'AI_FALLBACK_ENABLED', True),
            cost_limit_enabled=getattr(settings, 'AI_COST_LIMIT_ENABLED', False),
            daily_cost_limit=getattr(settings, 'AI_COST_LIMIT_DAILY', 10.0),
            cache_enabled=getattr(settings, 'AI_CACHE_STRATEGY', 'memory') != 'none',
            cache_ttl=getattr(settings, 'AI_CACHE_TTL', 3600),
            providers=providers_config
        )
    
    return {
        "success": True,
        "config": config_data
    }

@router.post("/ai-config", summary="保存AI配置")
async def save_ai_config(
    config: AIConfigData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """保存AI配置到数据库"""
    check_admin_permission(current_user)
    
    try:
        from app.services.ai.ai_config_service import AIConfigService
        
        # 准备要保存的配置数据
        config_data = {
            "default_provider": config.default_provider,
            "enabled": config.enabled,
            "fallback_enabled": config.fallback_enabled,
            "cost_limit_enabled": config.cost_limit_enabled,
            "daily_cost_limit": config.daily_cost_limit,
            "cache_enabled": config.cache_enabled,
            "cache_ttl": config.cache_ttl,
            "providers": {
                "openai": {
                    "api_key": config.providers.openai.api_key,
                    "api_url": config.providers.openai.api_url,
                    "model": config.providers.openai.model
                },
                "anthropic": {
                    "api_key": config.providers.anthropic.api_key,
                    "api_url": config.providers.anthropic.api_url,
                    "model": config.providers.anthropic.model
                },
                "alibaba": {
                    "api_key": config.providers.alibaba.api_key,
                    "api_url": config.providers.alibaba.api_url,
                    "model": config.providers.alibaba.model
                },
                "zhipu": {
                    "api_key": config.providers.zhipu.api_key,
                    "api_url": config.providers.zhipu.api_url,
                    "model": config.providers.zhipu.model
                },
                "minimax": {
                    "api_key": config.providers.minimax.api_key,
                    "api_url": config.providers.minimax.api_url,
                    "model": config.providers.minimax.model,
                    "group_id": config.providers.minimax.group_id
                },
                "custom": {
                    "api_key": config.providers.custom.api_key,
                    "api_url": config.providers.custom.api_url,
                    "model": config.providers.custom.model
                }
            }
        }
        
        # 保存到数据库
        AIConfigService.save_user_ai_config(db, current_user.id, config_data)
        
        return {"message": "AI配置保存成功", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存AI配置失败: {str(e)}")