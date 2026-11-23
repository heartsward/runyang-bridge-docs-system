# -*- coding: utf-8 -*-
"""32.4：分享状态可视化后端——shared 注入 / share_filter 筛选 / 一键撤销

覆盖：
1. 资产列表注入 shared/shared_count（分享给N人→shared_count=N）
2. 文档列表同样注入
3. 资产 share_filter=shared/unshared 服务端筛选
4. DELETE /shares/by-item 一键撤销该条全部分享（仅管理员）
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


@pytest.fixture
def ctx():
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine, tables=[
        AssetModel.__table__, DocumentModel.__table__, UserModel.__table__,
        Share.__table__, SystemConfig.__table__])
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    u1 = UserModel(username="u1", email="u1@t.local", hashed_password="x", is_active=True)
    u2 = UserModel(username="u2", email="u2@t.local", hashed_password="x", is_active=True)
    db.add_all([admin, u1, u2])
    db.flush()
    shared_a = AssetModel(name="shared-asset", asset_type="server", creator_id=admin.id)
    plain_a = AssetModel(name="plain-asset", asset_type="server", creator_id=admin.id)
    shared_d = DocumentModel(title="shared-doc", owner_id=admin.id)
    plain_d = DocumentModel(title="plain-doc", owner_id=admin.id)
    db.add_all([shared_a, plain_a, shared_d, plain_d])
    db.flush()
    db.add_all([
        Share(item_type="asset", item_id=shared_a.id, shared_by_id=admin.id, shared_with_id=u1.id),
        Share(item_type="asset", item_id=shared_a.id, shared_by_id=admin.id, shared_with_id=u2.id),
        Share(item_type="document", item_id=shared_d.id, shared_by_id=admin.id, shared_with_id=u1.id),
    ])
    db.commit()

    app = FastAPI()
    from app.api.endpoints import assets as asset_ep, documents as doc_ep, shares as share_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.include_router(doc_ep.router, prefix="/api/v1/documents")
    app.include_router(share_ep.router, prefix="/api/v1/shares")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: admin
    with TestClient(app) as c:
        yield {"c": c, "db": db, "admin": admin, "u1": u1, "u2": u2,
               "shared_a": shared_a, "plain_a": plain_a,
               "shared_d": shared_d, "plain_d": plain_d}
    db.close()


def test_asset_list_injects_shared(ctx):
    items = ctx["c"].get("/api/v1/assets/").json()["items"]
    byname = {a["name"]: a for a in items}
    assert byname["shared-asset"]["shared"] is True
    assert byname["shared-asset"]["shared_count"] == 2
    assert byname["plain-asset"]["shared"] is False
    assert byname["plain-asset"]["shared_count"] == 0


def test_doc_list_injects_shared(ctx):
    items = ctx["c"].get("/api/v1/documents/").json()["items"]
    byname = {d["title"]: d for d in items}
    assert byname["shared-doc"]["shared"] is True
    assert byname["shared-doc"]["shared_count"] == 1
    assert byname["plain-doc"]["shared"] is False


def test_asset_share_filter(ctx):
    c = ctx["c"]
    shared = c.get("/api/v1/assets/", params={"share_filter": "shared"}).json()["items"]
    assert {a["name"] for a in shared} == {"shared-asset"}
    unshared = c.get("/api/v1/assets/", params={"share_filter": "unshared"}).json()["items"]
    assert {a["name"] for a in unshared} == {"plain-asset"}


def test_revoke_all_by_item(ctx):
    c = ctx["c"]
    # 一键撤销 shared-asset 的全部分享（2 条）
    r = c.delete("/api/v1/shares/by-item",
                 params={"item_type": "asset", "item_id": ctx["shared_a"].id})
    assert r.status_code == 200, r.text
    assert r.json()["deleted"] == 2
    # 列表回读：变未分享
    a = next(x for x in c.get("/api/v1/assets/").json()["items"] if x["id"] == ctx["shared_a"].id)
    assert a["shared"] is False and a["shared_count"] == 0
    # u1 现在看不到该资产（分享没了）
    # （切用户需 override——简化：直接查 DB 断言 Share 行清空）
    left = ctx["db"].query(Share).filter(Share.item_type == "asset",
                                         Share.item_id == ctx["shared_a"].id).count()
    assert left == 0


def test_revoke_all_admin_only(ctx):
    # 用 u1（普通用户）身份撤销 → 403
    ctx["app_state_u1"] = True
    app2 = FastAPI()
    from app.api.endpoints import shares as share_ep
    app2.include_router(share_ep.router, prefix="/api/v1/shares")
    app2.dependency_overrides[deps.get_db] = lambda: (yield ctx["db"])
    app2.dependency_overrides[deps.get_current_active_user] = lambda: ctx["u1"]
    with TestClient(app2) as c2:
        r = c2.delete("/api/v1/shares/by-item",
                      params={"item_type": "document", "item_id": ctx["shared_d"].id})
        assert r.status_code == 403
