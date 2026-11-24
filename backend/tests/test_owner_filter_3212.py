# -*- coding: utf-8 -*-
"""32.12：所有人筛选（'管理员'聚合/用户名）、按所有人排序（聚合口径）、creator_is_superuser 注入"""
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
    a1 = UserModel(username="heartsward", email="a@t.local", hashed_password="x", is_active=True, is_superuser=True)
    a2 = UserModel(username="admin2", email="b@t.local", hashed_password="x", is_active=True, is_superuser=True)
    yyb = UserModel(username="yyb", email="c@t.local", hashed_password="x", is_active=True, is_superuser=False)
    aaa = UserModel(username="zhangsan", email="d@t.local", hashed_password="x", is_active=True, is_superuser=False)
    db.add_all([a1, a2, yyb, aaa])
    db.flush()
    db.add_all([
        AssetModel(name="A-管理员1建", asset_type="server", creator_id=a1.id),
        AssetModel(name="B-管理员2建", asset_type="server", creator_id=a2.id),
        AssetModel(name="C-yyb建", asset_type="server", creator_id=yyb.id),
        AssetModel(name="D-zhangsan建", asset_type="server", creator_id=aaa.id),
    ])
    db.commit()
    box = {"actor": a1}
    app = FastAPI()
    from app.api.endpoints import assets as asset_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: box["actor"]
    with TestClient(app) as c:
        yield {"c": c, "db": db, "admin1": a1, "yyb": yyb, "box": box}
    db.close()


def _names(items):
    return [i["name"] for i in items]


def test_owner_filter_admin_aggregates(ctx):
    r = ctx["c"].get("/api/v1/assets/", params={"owner": "管理员"})
    assert r.status_code == 200
    items = r.json()["items"]
    # 两个管理员账户建的都聚合命中
    assert set(_names(items)) == {"A-管理员1建", "B-管理员2建"}


def test_owner_filter_by_username(ctx):
    r = ctx["c"].get("/api/v1/assets/", params={"owner": "yyb"})
    assert _names(r.json()["items"]) == ["C-yyb建"]


def test_owner_sort_groups_admins(ctx):
    r = ctx["c"].get("/api/v1/assets/", params={"sort_by": "owner", "sort_order": "asc"})
    assert r.status_code == 200, r.text
    # 聚合排序：两个管理员账户建的必须相邻（同归"管理员"一组），不要求排首位——
    # 排序键是字符串（管理员=汉字码点，yyb/zhangsan=拉丁），asc 下汉字排最后
    names = _names(r.json()["items"])
    ia, ib = names.index("A-管理员1建"), names.index("B-管理员2建")
    assert abs(ia - ib) == 1
    # 升序时拉丁开头用户名应先于汉字"管理员"组
    assert names[0] in ("C-yyb建", "D-zhangsan建")


def test_creator_is_superuser_injected(ctx):
    items = ctx["c"].get("/api/v1/assets/?limit=100").json()["items"]
    m = {i["name"]: i for i in items}
    assert m["A-管理员1建"]["creator_is_superuser"] is True
    assert m["C-yyb建"]["creator_is_superuser"] is False
    assert m["C-yyb建"]["creator_username"] == "yyb"


def test_owner_filter_ignored_for_normal_user(ctx):
    ctx["box"]["actor"] = ctx["yyb"]
    # 普通用户传 owner：后端忽略该筛选（仍只按可见性过滤自己+被分享）
    r = ctx["c"].get("/api/v1/assets/", params={"owner": "管理员"})
    items = r.json()["items"]
    assert all(i["creator_id"] == ctx["yyb"].id for i in items)
