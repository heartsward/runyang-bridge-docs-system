# -*- coding: utf-8 -*-
"""MCP 用户隔离（32.2）回归测试

覆盖：
1. token 生成：普通用户创建自动发个人码；管理员为 NULL；注册路径同
2. 认证：个人码→该用户身份；统一码→管理员身份；错误/空→None
3. 升降级钩子：普通→管理员清空个人码；管理员→普通生成个人码
4. MCP 工具层可见性：普通用户身份 search_assets/get_asset 只命中自己+被分享；
   管理员命中全部（直接测可见性 helper + 工具实现函数）
5. 端点门禁：regenerate 普通码仅本人；admin 码仅管理员
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
from app.models.document import Document as DocumentModel  # noqa: E402
from app.models.user import User as UserModel  # noqa: E402
from app.models.share import Share  # noqa: E402
from app.models.system_config import SystemConfig  # noqa: E402
from app.core import deps  # noqa: E402
from app.core import mcp_auth  # noqa: E402


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[AssetModel.__table__, DocumentModel.__table__, UserModel.__table__,
                Share.__table__, SystemConfig.__table__],
    )
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()


@pytest.fixture
def ctx(db_session):
    """带 settings 端点的 TestClient（用户管理 + MCP 码端点）"""
    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    alice = UserModel(username="alice", email="a@t.local", hashed_password="x",
                      is_active=True, is_superuser=False,
                      mcp_token=mcp_auth.gen_mcp_token())
    db_session.add_all([admin, alice])
    db_session.commit()

    app = FastAPI()
    from app.api.endpoints import settings as settings_ep
    app.include_router(settings_ep.router, prefix="/api/v1/settings")

    state = {"user": admin}

    def _db_override():
        yield db_session
    app.dependency_overrides[deps.get_db] = _db_override
    app.dependency_overrides[deps.get_current_active_user] = lambda: state["user"]

    with TestClient(app) as c:
        yield {"c": c, "db": db_session, "admin": admin, "alice": alice, "state": state}


# ---------- 1. token 生成 ----------

def test_personal_token_format_and_uniqueness(db_session):
    t1 = mcp_auth.gen_mcp_token()
    t2 = mcp_auth.gen_mcp_token()
    assert t1 != t2
    assert len(t1) >= 20


def test_user_has_token_in_response(ctx):
    r = ctx["c"].get("/api/v1/settings/users")
    assert r.status_code == 200
    users = {u["username"]: u for u in r.json()}
    assert users["alice"]["mcp_token"]  # 普通用户带码
    assert users["adm"]["mcp_token"] is None  # 管理员无个人码


# ---------- 2. 认证 ----------

def test_authenticate_personal_token(ctx):
    ident = mcp_auth.authenticate_mcp_token(ctx["db"], ctx["alice"].mcp_token)
    assert ident is not None
    assert ident.user_id == ctx["alice"].id
    assert ident.is_superuser is False
    assert ident.via == "personal"


def test_authenticate_admin_token(ctx):
    admin_tok = mcp_auth.get_or_create_admin_token(ctx["db"])
    ident = mcp_auth.authenticate_mcp_token(ctx["db"], "Bearer " + admin_tok)
    assert ident is not None
    assert ident.is_superuser is True
    assert ident.via == "admin"
    # 二次调用复用同一码（幂等，不重复生成）
    assert mcp_auth.get_or_create_admin_token(ctx["db"]) == admin_tok


def test_authenticate_rejects_bad_token(ctx):
    assert mcp_auth.authenticate_mcp_token(ctx["db"], None) is None
    assert mcp_auth.authenticate_mcp_token(ctx["db"], "") is None
    assert mcp_auth.authenticate_mcp_token(ctx["db"], "Bearer nope") is None


# ---------- 3. 升降级钩子 ----------

def test_upgrade_clears_personal_token(ctx):
    r = ctx["c"].put(f"/api/v1/settings/users/{ctx['alice'].id}",
                     json={"is_superuser": True})
    assert r.status_code == 200, r.text
    assert r.json()["mcp_token"] is None
    ctx["db"].refresh(ctx["alice"])
    assert ctx["alice"].mcp_token is None


def test_downgrade_generates_personal_token(ctx):
    r = ctx["c"].put(f"/api/v1/settings/users/{ctx['admin'].id}",
                     json={"is_superuser": False})
    assert r.status_code == 200, r.text
    tok = r.json()["mcp_token"]
    assert tok and len(tok) >= 20
    # 新码能认证出该用户身份
    ident = mcp_auth.authenticate_mcp_token(ctx["db"], tok)
    assert ident and ident.user_id == ctx["admin"].id and ident.is_superuser is False


# ---------- 4. MCP 工具层可见性 ----------

def test_visible_ids_helpers(ctx, monkeypatch):
    """直接测 mcp_server 的可见集合 helper（工具层过滤核心）

    helper 内部用 app.db.database.SessionLocal（函数内延迟导入）——
    monkeypatch 成测试内存库的 session，数据才查得到。
    """
    from app.services.wiki import mcp_server
    import app.db.database as dbmod

    class _KeepSession:
        """SessionLocal() 每次返回同一个 session；close() 置空防 helper 关掉它"""
        def __call__(self):
            return ctx["db"]
    monkeypatch.setattr(dbmod, "SessionLocal", _KeepSession())
    monkeypatch.setattr(ctx["db"], "close", lambda: None)

    # alice 建资产
    a = AssetModel(name="alice-sw", asset_type="network", creator_id=ctx["alice"].id)
    b = AssetModel(name="bob-sw", asset_type="network", creator_id=999)
    ctx["db"].add_all([a, b])
    ctx["db"].flush()  # 先取到自增 id 再建 Share
    # 分享给 alice
    ctx["db"].add(Share(item_type="asset", item_id=b.id,
                        shared_by_id=ctx["admin"].id, shared_with_id=ctx["alice"].id))
    ctx["db"].commit()

    # 管理员身份 → None（不限制）
    ident_admin = mcp_auth.MCPIdentity(user_id=ctx["admin"].id, username="adm",
                                       is_superuser=True, via="admin")
    monkeypatch.setattr(mcp_server, "_current_identity", lambda: ident_admin)
    mcp_server._visibility_cache.set(None)
    assert mcp_server._visible_asset_ids() is None
    assert mcp_server._visible_doc_ids() is None

    # 普通身份 → 自有 + 被分享
    ident_u = mcp_auth.MCPIdentity(user_id=ctx["alice"].id, username="alice",
                                   is_superuser=False, via="personal")
    monkeypatch.setattr(mcp_server, "_current_identity", lambda: ident_u)
    mcp_server._visibility_cache.set(None)
    assert mcp_server._visible_asset_ids() == {a.id, b.id}


# ---------- 5. 端点门禁 ----------

def test_regenerate_endpoints(ctx):
    old_tok = ctx["alice"].mcp_token
    # 管理员重置 alice 的码
    r = ctx["c"].post(f"/api/v1/settings/mcp-token/users/{ctx['alice'].id}/regenerate")
    assert r.status_code == 200, r.text
    new_tok = r.json()["token"]
    assert new_tok and new_tok != old_tok
    ctx["db"].refresh(ctx["alice"])
    assert ctx["alice"].mcp_token == new_tok
    # 旧码失效、新码可用
    assert mcp_auth.authenticate_mcp_token(ctx["db"], "Bearer " + old_tok) is None
    assert mcp_auth.authenticate_mcp_token(ctx["db"], "Bearer " + new_tok) is not None

    # admin 统一码查看 + 重置
    r = ctx["c"].get("/api/v1/settings/mcp-token/admin")
    assert r.status_code == 200 and r.json()["token"]
    r = ctx["c"].post("/api/v1/settings/mcp-token/admin/regenerate")
    assert r.status_code == 200
    assert mcp_auth.authenticate_mcp_token(ctx["db"], "Bearer " + r.json()["token"]).is_superuser


def test_personal_me_endpoints(ctx):
    # 切到 alice
    ctx["state"]["user"] = ctx["alice"]
    old_tok = ctx["alice"].mcp_token
    r = ctx["c"].get("/api/v1/settings/mcp-token/me")
    assert r.status_code == 200
    assert r.json()["mode"] == "personal"
    assert r.json()["can_regenerate_personal"] is True

    r = ctx["c"].post("/api/v1/settings/mcp-token/me/regenerate")
    assert r.status_code == 200
    assert r.json()["token"] != old_tok

    # 管理员调个人码重置 → 400
    ctx["state"]["user"] = ctx["admin"]
    r = ctx["c"].post("/api/v1/settings/mcp-token/me/regenerate")
    assert r.status_code == 400

    # 管理员 /me 返回统一码
    r = ctx["c"].get("/api/v1/settings/mcp-token/me")
    assert r.json()["mode"] == "admin" and r.json()["can_regenerate_personal"] is False


def test_update_user_cannot_inject_mcp_token(ctx):
    """mcp_token 不接受表单直接写入（防绕过钩子）"""
    r = ctx["c"].put(f"/api/v1/settings/users/{ctx['alice'].id}",
                     json={"mcp_token": "evil-injected-token"})
    assert r.status_code == 200
    assert r.json()["mcp_token"] != "evil-injected-token"
    ctx["db"].refresh(ctx["alice"])
    assert ctx["alice"].mcp_token != "evil-injected-token"
