# -*- coding: utf-8 -*-
"""MCP 全链路端到端（32.2）：认证中间件 + 工具层隔离

真实挂载结构：FastAPI.mount("/mcp", MCPAuthMiddleware(FastMCP.http_app()))
验证：
1. 不带 / 带错验证码 → 401（进不了 MCP 协议层）
2. 管理员统一码 → 能 initialize + tools/call，search_assets 见全部
3. 普通用户个人码 → 能调用，但 search_assets 只见自己的资产
"""
import json
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
from app.core import mcp_auth  # noqa: E402


@pytest.fixture
def mcp_client():
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

    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    alice = UserModel(username="alice", email="a@t.local", hashed_password="x",
                      is_active=True, is_superuser=False,
                      mcp_token="alice-personal-code-000111")
    db.add_all([admin, alice])
    db.flush()
    a1 = AssetModel(name="alice-router", asset_type="network", ip_address="10.9.0.1",
                    creator_id=alice.id, status="active")
    a2 = AssetModel(name="secret-switch", asset_type="network", ip_address="10.9.0.2",
                    creator_id=999, status="active", username="root", password="s3cret")
    db.add_all([a1, a2])
    db.commit()
    admin_code = mcp_auth.get_or_create_admin_token(db)

    # 中间件与工具层内部都从 app.db.database 延迟导入 SessionLocal——patch 到测试库
    import app.db.database as dbmod
    real_sessionlocal = dbmod.SessionLocal

    class _KeepSession:
        def __call__(self):
            return db
    dbmod.SessionLocal = _KeepSession()
    real_close = db.close
    db.close = lambda: None

    from fastmcp import FastMCP
    from app.services.wiki.mcp_server import register_tools
    from app.core.mcp_auth import MCPAuthMiddleware
    from contextlib import asynccontextmanager

    wiki_mcp = FastMCP("AI-Wiki-Test")
    register_tools(wiki_mcp)
    mcp_inner = wiki_mcp.http_app(path="/")

    # 关键：mount 不会触发子 app 的 lifespan（FastMCP 需要它的 task group 初始化）。
    # 主 app 的 lifespan 里手动 `async with mcp_inner.lifespan(...)`——与 main.py 同款处理。
    @asynccontextmanager
    async def _lifespan(_app):
        async with mcp_inner.lifespan(mcp_inner):
            yield

    app2 = FastAPI(lifespan=_lifespan)
    app2.mount("/mcp", MCPAuthMiddleware(mcp_inner))

    try:
        with TestClient(app2) as c:
            yield {"c": c, "db": db, "alice": alice, "admin": admin,
                   "admin_code": admin_code,
                   "alice_code": "alice-personal-code-000111",
                   "a1": a1, "a2": a2}
    finally:
        dbmod.SessionLocal = real_sessionlocal
        db.close = real_close
        db.close()


def _init_session(c, auth: str):
    """MCP initialize 握手，返回 session id（失败返回 (status, None)）"""
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if auth:
        headers["Authorization"] = auth
    r = c.post("/mcp/", json={
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                   "clientInfo": {"name": "pytest", "version": "1.0"}},
    }, headers=headers)
    if r.status_code != 200:
        return r.status_code, None
    sid = r.headers.get("mcp-session-id")
    # initialized 通知
    h2 = dict(headers)
    if sid:
        h2["mcp-session-id"] = sid
    c.post("/mcp/", json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=h2)
    return 200, sid


def _call_tool(c, auth: str, sid: str, name: str, args: dict):
    headers = {"Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if auth:
        headers["Authorization"] = auth
    if sid:
        headers["mcp-session-id"] = sid
    r = c.post("/mcp/", json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": name, "arguments": args},
    }, headers=headers)
    assert r.status_code == 200, r.text
    # SSE: data: {...}
    payload = None
    for line in r.text.splitlines():
        if line.strip().startswith("data:"):
            payload = json.loads(line.strip()[5:])
            break
    if payload is None:
        payload = r.json()
    result = payload.get("result") or {}
    text = ""
    for part in result.get("content", []):
        if part.get("type") == "text":
            text += part.get("text", "")
    return result, text


def test_missing_token_401(mcp_client):
    c = mcp_client["c"]
    status, sid = _init_session(c, None)
    assert status == 401, "无验证码必须 401"


def test_wrong_token_401(mcp_client):
    status, sid = _init_session(mcp_client["c"], "Bearer totally-wrong-code")
    assert status == 401


def test_personal_token_scoped_results(mcp_client):
    """普通用户个人码：search_assets 只命中自己的资产，看不到别人的密码"""
    c = mcp_client["c"]
    status, sid = _init_session(c, "Bearer " + mcp_client["alice_code"])
    assert status == 200, "个人码握手应成功"

    result, text = _call_tool(c, "Bearer " + mcp_client["alice_code"], sid,
                              "search_assets", {"query": ""})
    data = json.loads(text)
    # 命中 1 台时 FastMCP 直接返回该资产全字段（dict）；≥2 台返回 {"assets":[摘要]}
    if isinstance(data, dict) and "assets" in data:
        ids = [a["id"] for a in data["assets"]]
    elif isinstance(data, dict) and "id" in data:
        ids = [data["id"]]
    else:
        ids = []
    assert mcp_client["a1"].id in ids
    assert mcp_client["a2"].id not in ids
    assert "s3cret" not in text, "绝不能泄露他人资产密码"

    # get_asset 直接取他人资产 → error（按不存在处理）
    _, t2 = _call_tool(c, "Bearer " + mcp_client["alice_code"], sid,
                       "get_asset", {"asset_id": mcp_client["a2"].id})
    assert "error" in t2 or not t2


def test_admin_token_sees_all(mcp_client):
    c = mcp_client["c"]
    status, sid = _init_session(c, "Bearer " + mcp_client["admin_code"])
    assert status == 200

    result, text = _call_tool(c, "Bearer " + mcp_client["admin_code"], sid,
                              "search_assets", {"query": "secret-switch"})
    assert "s3cret" in text, "管理员统一码可见全部资产（含密码）"
