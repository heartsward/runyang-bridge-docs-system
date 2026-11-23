# -*- coding: utf-8 -*-
"""32.3：验证码通道（REST 也认管理员统一码/个人码，取代 API_TOKEN/api_client）

覆盖：
1. resolve_user_by_token：统一码→第一个启用超管；个人码→该用户；禁用用户→None；错码→None
2. get_current_user 双通道：Bearer=统一码 → 返回真实超管 User（走 REST 依赖）
3. 普通用户个人码走 REST：返回该普通用户；写别人资产 → 403（32.1 隔离在 REST 也生效）
4. JWT 通道不受影响（验证码不匹配时回落 JWT）
5. api_client/API_TOKEN 已移除：config 不再有这三个字段；相关端点保护块已删
"""
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND))

from app.db.database import Base  # noqa: E402
from app.models.asset import Asset as AssetModel  # noqa: E402
from app.models.user import User as UserModel  # noqa: E402
from app.models.share import Share  # noqa: E402
from app.models.system_config import SystemConfig  # noqa: E402
from app.core import deps  # noqa: E402
from app.core import mcp_auth  # noqa: E402
from app.core.security import create_access_token  # noqa: E402


@pytest.fixture
def ctx():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[AssetModel.__table__, UserModel.__table__, Share.__table__, SystemConfig.__table__],
    )
    Session = sessionmaker(bind=engine)
    db = Session()

    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    alice = UserModel(username="alice", email="a@t.local", hashed_password="x",
                      is_active=True, is_superuser=False,
                      mcp_token="alice-rest-code-001")
    bob = UserModel(username="bob", email="b@t.local", hashed_password="x",
                    is_active=True, is_superuser=False,
                    mcp_token="bob-rest-code-002")
    db.add_all([admin, alice, bob])
    db.flush()
    a_alice = AssetModel(name="alice-sw", asset_type="network", creator_id=alice.id)
    db.add(a_alice)
    db.commit()
    admin_code = mcp_auth.get_or_create_admin_token(db)

    app = FastAPI()
    from app.api.endpoints import assets as assets_ep
    app.include_router(assets_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)

    # 不 override get_current_active_user —— 让真实认证链（验证码/JWT 双通道）跑起来
    with TestClient(app) as c:
        yield {"c": c, "db": db, "admin": admin, "alice": alice, "bob": bob,
               "admin_code": admin_code, "a_alice": a_alice}
    db.close()


# ---------- 1. resolve_user_by_token ----------

def test_resolve_admin_code_to_real_user(ctx):
    u = mcp_auth.resolve_user_by_token(ctx["db"], "Bearer " + ctx["admin_code"])
    assert u is not None and u.username == "adm" and u.is_superuser


def test_resolve_personal_code(ctx):
    u = mcp_auth.resolve_user_by_token(ctx["db"], ctx["alice"].mcp_token)
    assert u is not None and u.id == ctx["alice"].id
    # 禁用用户 → None
    ctx["bob"].is_active = False
    ctx["db"].commit()
    assert mcp_auth.resolve_user_by_token(ctx["db"], ctx["bob"].mcp_token) is None


def test_resolve_bad_token_none(ctx):
    assert mcp_auth.resolve_user_by_token(ctx["db"], None) is None
    assert mcp_auth.resolve_user_by_token(ctx["db"], "Bearer nope") is None


# ---------- 2/3. REST 认证链 ----------

def test_rest_admin_code_full_access(ctx):
    c = ctx["c"]
    r = c.get("/api/v1/assets/", headers={"Authorization": "Bearer " + ctx["admin_code"]})
    assert r.status_code == 200
    names = {a["name"] for a in r.json()["items"]}
    assert "alice-sw" in names  # 管理员见全部


def test_rest_personal_code_scoped(ctx):
    c = ctx["c"]
    auth = {"Authorization": "Bearer " + ctx["alice"].mcp_token}
    r = c.get("/api/v1/assets/", headers=auth)
    assert r.status_code == 200
    assert {a["name"] for a in r.json()["items"]} == {"alice-sw"}

    # bob 的码看不到 alice 的资产；写也 403/404
    r = c.put(f"/api/v1/assets/{ctx['a_alice'].id}",
              json={"device_model": "hack"},
              headers={"Authorization": "Bearer " + ctx["bob"].mcp_token})
    assert r.status_code == 403


def test_rest_jwt_still_works(ctx):
    """JWT 通道未被验证码通道破坏：错验证码回落 JWT"""
    c = ctx["c"]
    jwt = create_access_token(subject={"sub": "alice"})
    r = c.get("/api/v1/assets/", headers={"Authorization": "Bearer " + jwt})
    assert r.status_code == 200
    assert {a["name"] for a in r.json()["items"]} == {"alice-sw"}


def test_rest_no_auth_401_or_403(ctx):
    r = ctx["c"].get("/api/v1/assets/")
    assert r.status_code in (401, 403)


# ---------- 5. 旧通道已移除 ----------

def test_api_token_config_removed():
    from app.core.config import settings as st
    for attr in ("API_TOKEN", "API_TOKEN_ENABLED", "API_SERVICE_USERNAME"):
        assert not hasattr(st, attr), f"{attr} 应已移除"


def test_settings_ep_no_service_account_guard(ctx):
    """保留名保护已删：现在可以用 api_client 这个名字建普通账号（不再是保留名）"""
    from app.api.endpoints import settings as settings_ep
    c = ctx["c"]
    # 单独挂 settings 路由验证创建不再被保留名拦截
    app2 = FastAPI()
    app2.include_router(settings_ep.router, prefix="/api/v1/settings")
    app2.dependency_overrides[deps.get_db] = lambda: (yield ctx["db"])
    from app.api.endpoints.settings import get_current_active_user
    app2.dependency_overrides[get_current_active_user] = lambda: ctx["admin"]
    with TestClient(app2) as c2:
        r = c2.post("/api/v1/settings/users", json={
            "username": "api_client", "email": "x@x.x", "password": "pw123456",
        })
        # 不再有"保留名"400；能建（或用户名已存在400——但绝不是保留名报错）
        assert r.status_code == 200, r.text
