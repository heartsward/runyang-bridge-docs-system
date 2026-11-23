# -*- coding: utf-8 -*-
"""权限模型（32.1）回归测试——普通用户自建自见 + 管理员全局 + 分享只读

覆盖：
1. 列表可见性：普通用户只看 自有 + 被分享；管理员看全部
2. 创建：普通用户可创建文档/资产，归属自己
3. 编辑/删除：owner 或管理员放行；非 owner 普通用户 403；被分享者只读（写 403）
4. 分享：仅管理员可分享/撤销；分享后目标用户可读不可写
5. 详情/预览读权限：不可见条目按 404（不泄露存在性）
6. 管理选项：批量删除 / file-extract 仅管理员
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
from app.models.document import (  # noqa: E402
    Document as DocumentModel,
    DocumentView,
    DocumentDownload,
)
from app.models.user import User as UserModel  # noqa: E402
from app.models.share import Share  # noqa: E402
from app.core import deps  # noqa: E402


@pytest.fixture
def ctx():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(
        bind=engine,
        tables=[
            AssetModel.__table__, DocumentModel.__table__, UserModel.__table__,
            Share.__table__, DocumentView.__table__, DocumentDownload.__table__,
        ],
    )
    Session = sessionmaker(bind=engine)
    db = Session()

    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x", is_active=True, is_superuser=True)
    alice = UserModel(username="alice", email="a@t.local", hashed_password="x", is_active=True, is_superuser=False)
    bob = UserModel(username="bob", email="b@t.local", hashed_password="x", is_active=True, is_superuser=False)
    db.add_all([admin, alice, bob])
    db.commit()

    app = FastAPI()
    from app.api.endpoints import documents as doc_ep, assets as asset_ep, shares as share_ep
    app.include_router(doc_ep.router, prefix="/api/v1/documents")
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.include_router(share_ep.router, prefix="/api/v1/shares")

    state = {"user": admin}

    def _override_db():
        yield db
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: state["user"]
    app.dependency_overrides[deps.get_current_user] = lambda: state["user"]

    with TestClient(app) as c:
        yield {"c": c, "admin": admin, "alice": alice, "bob": bob, "state": state}
    db.close()


def _as(ctx, user):
    ctx["state"]["user"] = user


def _mk_asset(ctx, name, ip=None):
    c = ctx["c"]
    body = {"name": name, "asset_type": "server", "network_location": "office"}
    if ip:
        body["ip_address"] = ip
    r = c.post("/api/v1/assets/", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def _mk_doc(ctx, title):
    r = ctx["c"].post("/api/v1/documents/", json={"title": title, "content": f"body of {title}"})
    assert r.status_code == 200, r.text
    return r.json()


# ---------- 1. 列表可见性 + 2. 创建归属 ----------

def test_asset_visibility_matrix(ctx):
    _as(ctx, ctx["alice"])
    a1 = _mk_asset(ctx, "alice-server-1", "10.1.0.1")
    _as(ctx, ctx["bob"])
    a2 = _mk_asset(ctx, "bob-server-2", "10.1.0.2")

    # alice 只看得到自己的
    _as(ctx, ctx["alice"])
    items = ctx["c"].get("/api/v1/assets/").json()["items"]
    names = {a["name"] for a in items}
    assert names == {"alice-server-1"}, names

    # 管理员看到全部
    _as(ctx, ctx["admin"])
    items = ctx["c"].get("/api/v1/assets/").json()["items"]
    names = {a["name"] for a in items}
    assert {"alice-server-1", "bob-server-2"} <= names

    # 创建归属 creator_id
    assert a1["creator_id"] == ctx["alice"].id
    assert a2["creator_id"] == ctx["bob"].id


def test_doc_visibility_matrix(ctx):
    _as(ctx, ctx["alice"])
    _mk_doc(ctx, "alice-doc")
    _as(ctx, ctx["bob"])
    _mk_doc(ctx, "bob-doc")

    _as(ctx, ctx["alice"])
    docs = ctx["c"].get("/api/v1/documents/").json()["items"]
    assert {d["title"] for d in docs} == {"alice-doc"}

    _as(ctx, ctx["admin"])
    docs = ctx["c"].get("/api/v1/documents/").json()["items"]
    assert {d["title"] for d in docs} == {"alice-doc", "bob-doc"}


# ---------- 3. 编辑/删除三态 ----------

def test_asset_update_perm(ctx):
    _as(ctx, ctx["alice"])
    a = _mk_asset(ctx, "perm-a", "10.2.0.1")

    # alice 改自己的 → OK
    r = ctx["c"].put(f"/api/v1/assets/{a['id']}", json={"device_model": "X"})
    assert r.status_code == 200, r.text

    # bob 改 alice 的 → 403
    _as(ctx, ctx["bob"])
    r = ctx["c"].put(f"/api/v1/assets/{a['id']}", json={"device_model": "Y"})
    assert r.status_code == 403

    # admin 改任何 → OK
    _as(ctx, ctx["admin"])
    r = ctx["c"].put(f"/api/v1/assets/{a['id']}", json={"device_model": "Z"})
    assert r.status_code == 200


def test_asset_delete_perm(ctx):
    _as(ctx, ctx["alice"])
    a = _mk_asset(ctx, "del-a", "10.3.0.1")

    _as(ctx, ctx["bob"])
    r = ctx["c"].delete(f"/api/v1/assets/{a['id']}")
    assert r.status_code == 403

    _as(ctx, ctx["alice"])
    r = ctx["c"].delete(f"/api/v1/assets/{a['id']}")
    assert r.status_code == 200


def test_doc_update_delete_perm(ctx):
    _as(ctx, ctx["alice"])
    d = _mk_doc(ctx, "perm-doc")

    _as(ctx, ctx["bob"])
    r = ctx["c"].delete(f"/api/v1/documents/{d['id']}")
    assert r.status_code == 403

    # bob 连详情都读不到（不可见 → 404 不泄露存在性）
    r = ctx["c"].get(f"/api/v1/documents/{d['id']}")
    assert r.status_code == 404

    _as(ctx, ctx["alice"])
    r = ctx["c"].delete(f"/api/v1/documents/{d['id']}")
    assert r.status_code == 200


# ---------- 4. 分享：仅管理员可分享；分享后只读可见 ----------

def test_share_asset_readonly(ctx):
    _as(ctx, ctx["alice"])
    a = _mk_asset(ctx, "share-a", "10.4.0.1")

    # bob 尝试分享 → 403
    _as(ctx, ctx["bob"])
    r = ctx["c"].post("/api/v1/shares/", json={"item_type": "asset", "item_id": a["id"], "user_id": ctx["bob"].id})
    assert r.status_code == 403

    # admin 分享给 bob
    _as(ctx, ctx["admin"])
    r = ctx["c"].post("/api/v1/shares/", json={"item_type": "asset", "item_id": a["id"], "user_id": ctx["bob"].id})
    assert r.status_code == 200, r.text

    # bob 现在可见（列表 + 详情）
    _as(ctx, ctx["bob"])
    items = ctx["c"].get("/api/v1/assets/").json()["items"]
    assert {x["id"] for x in items} == {a["id"]}
    r = ctx["c"].get(f"/api/v1/assets/{a['id']}")
    assert r.status_code == 200

    # 只读：bob 改/删 → 403
    r = ctx["c"].put(f"/api/v1/assets/{a['id']}", json={"device_model": "hack"})
    assert r.status_code == 403
    r = ctx["c"].delete(f"/api/v1/assets/{a['id']}")
    assert r.status_code == 403

    # admin 撤销分享 → bob 再次不可见
    _as(ctx, ctx["admin"])
    shares = ctx["c"].get("/api/v1/shares/by-item", params={"item_type": "asset", "item_id": a["id"]}).json()
    assert len(shares) == 1
    r = ctx["c"].delete(f"/api/v1/shares/{shares[0]['id']}")
    assert r.status_code == 200
    _as(ctx, ctx["bob"])
    items = ctx["c"].get("/api/v1/assets/").json()["items"]
    assert items == []


def test_share_doc_readonly(ctx):
    _as(ctx, ctx["alice"])
    d = _mk_doc(ctx, "share-doc")

    _as(ctx, ctx["admin"])
    r = ctx["c"].post("/api/v1/shares/", json={"item_type": "document", "item_id": d["id"], "user_id": ctx["bob"].id})
    assert r.status_code == 200, r.text

    _as(ctx, ctx["bob"])
    assert ctx["c"].get(f"/api/v1/documents/{d['id']}").status_code == 200
    # 只读：编辑（PUT multipart）与删除都不放行
    r = ctx["c"].delete(f"/api/v1/documents/{d['id']}")
    assert r.status_code == 403


# ---------- 6. 管理选项门禁 ----------

def test_batch_delete_admin_only(ctx):
    _as(ctx, ctx["alice"])
    a = _mk_asset(ctx, "bd-a", "10.5.0.1")
    _as(ctx, ctx["bob"])
    r = ctx["c"].post("/api/v1/assets/batch/delete", json={"asset_ids": [a["id"]]})
    assert r.status_code == 403
    # bob 也删不掉 alice 的单个资产（可见性+所有权双保险）
    assert ctx["c"].delete(f"/api/v1/assets/{a['id']}").status_code in (403, 404)

    _as(ctx, ctx["admin"])
    r = ctx["c"].post("/api/v1/assets/batch/delete", json={"asset_ids": [a["id"]]})
    assert r.status_code == 200, r.text


def test_file_extract_admin_only(ctx):
    _as(ctx, ctx["alice"])
    r = ctx["c"].post(
        "/api/v1/assets/file-extract",
        files={"file": ("t.txt", b"server 10.0.0.1 test", "text/plain")},
    )
    assert r.status_code == 403, r.text
