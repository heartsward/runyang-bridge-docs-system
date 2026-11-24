# -*- coding: utf-8 -*-
"""32.11：列表/详情注入 creator_username（仅管理员）+ 改派后标注即时更新"""
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
from app.core import deps  # noqa: E402


@pytest.fixture
def ctx():
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False}, poolclass=StaticPool)
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = UserModel(username="heartsward", email="a@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    yyb = UserModel(username="yyb", email="y@t.local", hashed_password="x",
                    is_active=True, is_superuser=False)
    db.add_all([admin, yyb])
    db.flush()
    a1 = AssetModel(name="综合电力监控系统", asset_type="信息系统", creator_id=admin.id)
    a2 = AssetModel(name="yyb自建", asset_type="server", creator_id=yyb.id)
    db.add_all([a1, a2])
    db.commit()

    box = {"actor": admin}
    app = FastAPI()
    from app.api.endpoints import assets as asset_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: box["actor"]
    with TestClient(app) as c:
        yield {"c": c, "db": db, "a1": a1, "a2": a2, "admin": admin, "yyb": yyb, "box": box}
    db.close()


def test_list_injects_creator_username_for_admin(ctx):
    items = ctx["c"].get("/api/v1/assets/").json()["items"]
    m = {i["name"]: i for i in items}
    assert m["综合电力监控系统"]["creator_username"] == "heartsward"
    assert m["yyb自建"]["creator_username"] == "yyb"


def test_list_no_creator_username_for_normal_user(ctx):
    ctx["box"]["actor"] = ctx["yyb"]
    items = ctx["c"].get("/api/v1/assets/").json()["items"]
    # 普通用户只见自己创建的；且响应不带 creator_username（最小权限）
    assert len(items) == 1
    assert items[0].get("creator_username") is None


def test_detail_injects_for_admin(ctx):
    r = ctx["c"].get(f"/api/v1/assets/{ctx['a1'].id}")
    assert r.json()["creator_username"] == "heartsward"


def test_transfer_updates_label(ctx):
    ctx["c"].put(f"/api/v1/assets/{ctx['a1'].id}", json={"creator_id": ctx["yyb"].id})
    r = ctx["c"].get(f"/api/v1/assets/{ctx['a1'].id}")
    assert r.json()["creator_username"] == "yyb"
