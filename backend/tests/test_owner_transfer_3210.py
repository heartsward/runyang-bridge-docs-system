# -*- coding: utf-8 -*-
"""32.10：资产所有权转移（PUT creator_id）

- 管理员可把资产 creator_id 改给其他用户（目标存在即可）→ 被转移者获得修改权
- 普通创建者不能把资产转给别人（只有管理员能转）
- 目标用户不存在 → 404
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
from app.core import deps  # noqa: E402


@pytest.fixture
def ctx():
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False}, poolclass=StaticPool)
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    yyb = UserModel(username="yyb", email="yyb@t.local", hashed_password="x",
                    is_active=True, is_superuser=False)
    other = UserModel(username="oth", email="oth@t.local", hashed_password="x",
                      is_active=True, is_superuser=False)
    db.add_all([admin, yyb, other])
    db.flush()
    a = AssetModel(name="综合电力监控系统", asset_type="信息系统", creator_id=admin.id)
    db.add(a)
    db.commit()

    box = {"actor": admin}
    app = FastAPI()
    from app.api.endpoints import assets as asset_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: box["actor"]
    with TestClient(app) as c:
        yield {"c": c, "db": db, "a": a, "yyb": yyb, "admin": admin, "other": other, "box": box}
    db.close()


def test_admin_transfers_owner(ctx):
    r = ctx["c"].put(f"/api/v1/assets/{ctx['a'].id}", json={"creator_id": ctx["yyb"].id})
    assert r.status_code == 200, r.text
    assert r.json()["creator_id"] == ctx["yyb"].id


def test_transferred_user_can_edit(ctx):
    ctx["c"].put(f"/api/v1/assets/{ctx['a'].id}", json={"creator_id": ctx["yyb"].id})
    ctx["box"]["actor"] = ctx["yyb"]
    r = ctx["c"].put(f"/api/v1/assets/{ctx['a'].id}", json={"purpose": "yyb 改的"})
    assert r.status_code == 200, r.text
    assert r.json()["purpose"] == "yyb 改的"


def test_non_admin_creator_cannot_transfer(ctx):
    ctx["c"].put(f"/api/v1/assets/{ctx['a'].id}", json={"creator_id": ctx["yyb"].id})
    ctx["box"]["actor"] = ctx["yyb"]
    r = ctx["c"].put(f"/api/v1/assets/{ctx['a'].id}", json={"creator_id": ctx["other"].id})
    assert r.status_code == 403
    assert ctx["db"].query(AssetModel).filter(AssetModel.id == ctx["a"].id).first().creator_id == ctx["yyb"].id


def test_target_user_not_found(ctx):
    r = ctx["c"].put(f"/api/v1/assets/{ctx['a'].id}", json={"creator_id": 999})
    assert r.status_code == 404
