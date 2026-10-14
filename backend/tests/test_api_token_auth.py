# -*- coding: utf-8 -*-
"""API 固定令牌认证通道回归测试（阶段二十八）

覆盖 deps.py 新增的服务账号通道，核心断言：
1. 开关关闭 / 令牌未配 / 令牌不匹配 → 返回 None（回落 JWT，不影响原登录）
2. 令牌匹配 + 服务账号存在且激活 → 返回该服务账号 User
3. 令牌匹配但服务账号缺失 → 401（明确提示先建账号，不回落 JWT 以免误导）
4. 令牌匹配但服务账号被禁用 → 401
5. 比对用 hmac.compare_digest（防时序攻击）
6. get_current_user 命中固定令牌时直接返回服务账号，不再走 verify_token
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND))

from app.core import deps  # noqa: E402


API_TOKEN = "test-tok-en_32chars_abcDEF1234567890"


def make_user(username="api_client", is_active=True, is_superuser=True):
    return SimpleNamespace(id=99, username=username, is_active=is_active,
                           is_superuser=is_superuser)


@pytest.fixture
def patch_settings(monkeypatch):
    """默认：开关开、令牌已配、服务账号用户名 api_client"""
    monkeypatch.setattr(deps.settings, "API_TOKEN_ENABLED", True, raising=False)
    monkeypatch.setattr(deps.settings, "API_TOKEN", API_TOKEN, raising=False)
    monkeypatch.setattr(deps.settings, "API_SERVICE_USERNAME", "api_client", raising=False)


# ---------- _authenticate_api_token 单元 ----------

def test_disabled_returns_none(monkeypatch):
    monkeypatch.setattr(deps.settings, "API_TOKEN_ENABLED", False, raising=False)
    assert deps._authenticate_api_token(API_TOKEN, db=None) is None


def test_empty_token_config_returns_none(monkeypatch, patch_settings):
    monkeypatch.setattr(deps.settings, "API_TOKEN", "", raising=False)
    assert deps._authenticate_api_token("anything", db=None) is None


def test_token_mismatch_returns_none(patch_settings):
    # 不匹配 → None，让调用方继续走 JWT
    assert deps._authenticate_api_token("wrong-token", db=None) is None


def test_token_match_returns_service_user(patch_settings, monkeypatch):
    u = make_user()
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: u)
    got = deps._authenticate_api_token(API_TOKEN, db=None)
    assert got is u
    assert got.username == "api_client"


def test_token_match_but_user_missing_raises_401(patch_settings, monkeypatch):
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: None)
    with pytest.raises(HTTPException) as ei:
        deps._authenticate_api_token(API_TOKEN, db=None)
    assert ei.value.status_code == 401
    assert "init_api_service_user" in ei.value.detail


def test_token_match_but_user_inactive_raises_401(patch_settings, monkeypatch):
    u = make_user(is_active=False)
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: u)
    with pytest.raises(HTTPException) as ei:
        deps._authenticate_api_token(API_TOKEN, db=None)
    assert ei.value.status_code == 401
    assert "禁用" in ei.value.detail


def test_compare_digest_used(monkeypatch):
    """确认走 hmac.compare_digest 而非 == （防时序侧信道）"""
    called = {}
    real = deps.hmac.compare_digest

    def spy(a, b):
        called["hit"] = True
        return real(a, b)

    monkeypatch.setattr(deps.settings, "API_TOKEN_ENABLED", True, raising=False)
    monkeypatch.setattr(deps.settings, "API_TOKEN", API_TOKEN, raising=False)
    monkeypatch.setattr(deps.hmac, "compare_digest", spy)
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: make_user())
    monkeypatch.setattr(deps.settings, "API_SERVICE_USERNAME", "api_client", raising=False)

    deps._authenticate_api_token(API_TOKEN, db=None)
    assert called.get("hit") is True


# ---------- get_current_user 集成（两通道优先级） ----------

def test_get_current_user_hits_api_token_skips_jwt(patch_settings, monkeypatch):
    """固定令牌命中 → 直接返回服务账号，verify_token 不应被调用"""
    u = make_user()
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: u)

    def boom(*a, **k):
        raise AssertionError("verify_token 不应在固定令牌命中时被调用")

    monkeypatch.setattr(deps, "verify_token", boom)

    creds = SimpleNamespace(credentials=API_TOKEN)
    got = deps.get_current_user(db=None, credentials=creds)
    assert got is u


def test_get_current_user_falls_back_to_jwt(patch_settings, monkeypatch):
    """令牌不匹配 → 回落 JWT 通道"""
    monkeypatch.setattr(deps.crud_user, "get_by_username",
                        lambda db, username: make_user(username="alice"))
    monkeypatch.setattr(deps, "verify_token", lambda t: {"sub": "alice"})
    creds = SimpleNamespace(credentials="some-jwt-string")
    got = deps.get_current_user(db=None, credentials=creds)
    assert got.username == "alice"


def test_get_current_user_no_token_channel_when_disabled(monkeypatch):
    """开关关闭时，即便 Bearer 等于旧 API_TOKEN 也不走服务账号，回落 JWT"""
    monkeypatch.setattr(deps.settings, "API_TOKEN_ENABLED", False, raising=False)
    monkeypatch.setattr(deps.settings, "API_TOKEN", API_TOKEN, raising=False)
    monkeypatch.setattr(deps, "verify_token", lambda t: {"sub": "bob"})
    monkeypatch.setattr(deps.crud_user, "get_by_username",
                        lambda db, username: make_user(username="bob"))
    creds = SimpleNamespace(credentials=API_TOKEN)
    got = deps.get_current_user(db=None, credentials=creds)
    assert got.username == "bob"


# ---------- get_optional_user ----------

def test_optional_user_api_token(patch_settings, monkeypatch):
    u = make_user()
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: u)
    creds = SimpleNamespace(credentials=API_TOKEN)
    assert deps.get_optional_user(db=None, credentials=creds) is u


def test_optional_user_no_credentials_returns_none(patch_settings):
    assert deps.get_optional_user(db=None, credentials=None) is None


# ---------- e2e：真实 HTTP 层 Bearer 解析 → 依赖注入 → 通道命中 ----------

def _mini_app():
    """最小 FastAPI 应用，只挂 get_current_active_user 依赖，验证端到端链路"""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    # 覆盖 get_db（返回哑对象，get_by_username 已被 monkeypatch 接管）
    app.dependency_overrides[deps.get_db] = lambda: object()

    @app.get("/whoami")
    def whoami(user=deps.Depends(deps.get_current_active_user)):
        return {"username": user.username, "superuser": user.is_superuser}

    return TestClient(app)


def test_e2e_fixed_token_bearer(patch_settings, monkeypatch):
    """Authorization: Bearer <固定令牌> → 端到端返回服务账号"""
    u = make_user()
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: u)
    client = _mini_app()
    r = client.get("/whoami", headers={"Authorization": f"Bearer {API_TOKEN}"})
    assert r.status_code == 200
    assert r.json() == {"username": "api_client", "superuser": True}


def test_e2e_wrong_token_rejected(patch_settings, monkeypatch):
    """错误 Bearer 且无有效 JWT → 401"""
    monkeypatch.setattr(deps.crud_user, "get_by_username", lambda db, username: make_user())
    client = _mini_app()
    r = client.get("/whoami", headers={"Authorization": "Bearer not-a-valid-token"})
    assert r.status_code == 401


def test_e2e_no_auth_header_rejected(patch_settings):
    """无 Authorization 头 → HTTPBearer 直接 403（FastAPI 默认）"""
    client = _mini_app()
    r = client.get("/whoami")
    assert r.status_code in (401, 403)

