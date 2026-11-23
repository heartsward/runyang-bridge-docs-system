# -*- coding: utf-8 -*-
"""
MCP 调用认证与身份（32.2）

MCP 验证码体系：
- 普通用户：每人一个随机个人码（users.mcp_token），前端可见/可重新随机
- 管理员：统一一个系统码（system_configs key=admin_mcp_token，惰性生成）
- 升级（普通→管理员）：自动清空个人码，改用统一码
- 降级（管理员→普通）：自动生成新的个人码

认证链路：MCP 客户端 Bearer <token> → 中间件 authenticate_mcp_token()
→ 命中 admin_mcp_token（hmac 比较）→ 管理员身份；
→ 命中某用户 mcp_token → 该用户身份；→ 否则 None（401）。

身份经 contextvar 传给工具层，工具按 32.1 可见性口径过滤数据。
"""
import hmac
import json
import secrets
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

ADMIN_MCP_TOKEN_KEY = "admin_mcp_token"


@dataclass
class MCPIdentity:
    user_id: int
    username: str
    is_superuser: bool
    # 该 token 属于管理员统一码还是个人码（审计/展示用）
    via: str  # "admin" | "personal"


# 请求级身份（中间件设置，工具读取）
_current_mcp_identity: ContextVar[Optional[MCPIdentity]] = ContextVar(
    "current_mcp_identity", default=None
)


def current_mcp_identity() -> Optional[MCPIdentity]:
    return _current_mcp_identity.get()


def set_current_mcp_identity(ident: Optional[MCPIdentity]):
    return _current_mcp_identity.set(ident)


def reset_current_mcp_identity(token) -> None:
    try:
        _current_mcp_identity.reset(token)
    except ValueError:
        pass


def gen_mcp_token() -> str:
    """随机验证码（24 字节 url-safe ≈ 32 字符）"""
    return secrets.token_urlsafe(24)


def _const_eq(a: str, b: str) -> bool:
    try:
        return hmac.compare_digest(
            (a or "").encode("utf-8", "surrogatepass"),
            (b or "").encode("utf-8", "surrogatepass"),
        )
    except Exception:
        return False


def get_or_create_admin_token(db: Session) -> str:
    """管理员统一 MCP 码：惰性生成并持久化到 system_configs"""
    from app.models.system_config import SystemConfig

    row = db.query(SystemConfig).filter(SystemConfig.key == ADMIN_MCP_TOKEN_KEY).first()
    if row and row.value:
        try:
            val = json.loads(row.value)
            if isinstance(val, str) and val:
                return val
        except Exception:
            pass
        # 兼容旧值/裸字符串
        if row.value.strip():
            return row.value.strip()

    token = gen_mcp_token()
    payload = json.dumps(token, ensure_ascii=False)
    if row:
        row.value = payload
    else:
        db.add(SystemConfig(
            key=ADMIN_MCP_TOKEN_KEY,
            value=payload,
            description="管理员统一 MCP 调用验证码（32.2）",
        ))
    db.commit()
    return token


def _normalize_bearer(bearer: Optional[str]) -> str:
    if not bearer:
        return ""
    token = bearer.strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token


def resolve_user_by_token(db: Session, bearer: Optional[str]):
    """32.3：把 MCP 验证码解析成真实 User（ORM），供 REST 认证通道复用。

    与 authenticate_mcp_token 同一套口径（MCP/REST 通用一个码）：
    - 命中管理员统一码（admin_mcp_token）→ 第一个启用的超管账号
    - 命中某用户 mcp_token → 该用户
    - 不匹配 / 用户被禁用 → None（调用方按未认证处理）

    注：验证码等价的权限 = 所映射用户的完整登录权限（含 REST 写操作）。
    个人码/统一码都能在 UI 一键重置，泄露即换码撤销（旧码当场失效）。
    """
    from app.models.user import User

    token = _normalize_bearer(bearer)
    if not token:
        return None

    # 1) 管理员统一码 → 挂到第一个启用的超管（所有管理员共用这一个码）
    admin_token = get_or_create_admin_token(db)
    if _const_eq(token, admin_token):
        return (
            db.query(User)
            .filter(User.is_superuser == True, User.is_active == True)  # noqa: E712
            .order_by(User.id)
            .first()
        )

    # 2) 个人码 → 该用户（禁用用户不认）
    user = db.query(User).filter(User.mcp_token == token).first()
    if user is not None and not user.is_active:
        return None
    return user


def authenticate_mcp_token(db: Session, bearer: Optional[str]) -> Optional[MCPIdentity]:
    """Bearer → MCPIdentity；任何不匹配返回 None（调用方 401）。

    核心解析委托给 resolve_user_by_token（MCP 与 REST 共用同一认证口径）。
    """
    user = resolve_user_by_token(db, bearer)
    if user is None:
        return None
    return MCPIdentity(
        user_id=user.id,
        username=user.username,
        is_superuser=bool(user.is_superuser),
        via="admin" if user.is_superuser else "personal",
    )


def parse_bearer_header(headers: dict) -> Optional[str]:
    """从（小写化）headers dict 里取 Authorization 头的 token 原文"""
    if not headers:
        return None
    auth = None
    for k, v in headers.items():
        if k and k.lower() == "authorization":
            auth = v
            break
    return auth


class MCPAuthMiddleware:
    """纯 ASGI 认证中间件（32.2）：包裹 FastMCP 的 http_app。

    校验请求头 Bearer token → 认证身份写入 contextvar（工具层读取）。
    认证失败直接回 401 JSON，不进入 MCP 协议层。
    纯 ASGI 实现，不依赖 Starlette/FastAPI API 细节，最稳。
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = {}
        for name, value in scope.get("headers", []) or []:
            try:
                headers[name.decode("latin-1")] = value.decode("latin-1")
            except Exception:
                continue

        bearer = parse_bearer_header(headers)

        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            ident = authenticate_mcp_token(db, bearer)
        finally:
            db.close()

        if ident is None:
            # 401：MCP 客户端会看到认证失败（不进入协议层）
            import json as _json
            body = _json.dumps(
                {"detail": "MCP 认证失败：请提供有效的 Authorization: Bearer <验证码>"},
                ensure_ascii=False,
            ).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    [b"content-type", b"application/json; charset=utf-8"],
                    [b"content-length", str(len(body)).encode("latin-1")],
                    [b"www-authenticate", b"Bearer"],
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        # 认证成功 → 身份进 contextvar（工具层读取），请求结束清理
        token = set_current_mcp_identity(ident)
        # 32.2：清可见集合缓存（防跨请求串数据；下一请求第一次工具调用时重建）
        try:
            from app.services.wiki.mcp_server import reset_visibility_cache
            reset_visibility_cache()
        except Exception:
            pass
        try:
            await self.app(scope, receive, send)
        finally:
            reset_current_mcp_identity(token)
