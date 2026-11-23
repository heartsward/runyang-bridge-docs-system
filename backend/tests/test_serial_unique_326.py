# -*- coding: utf-8 -*-
"""32.6：serial_number UNIQUE 撞空串回归（陈工 PUT /assets/87 500）

1. PUT serial_number='' → 200 且落库 NULL（归一 validator）
2. 两条都"未填"serial → 不再撞 UNIQUE
3. 真填重复序列号 → 400 友好文案（非 500）
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


@pytest.fixture
def ctx():
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine, tables=[
        AssetModel.__table__, UserModel.__table__, Share.__table__, SystemConfig.__table__])
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    db.add(admin)
    db.flush()
    a1 = AssetModel(name="a1", asset_type="server", creator_id=admin.id)
    a2 = AssetModel(name="a2", asset_type="server", creator_id=admin.id)
    db.add_all([a1, a2])
    db.commit()

    app = FastAPI()
    from app.api.endpoints import assets as asset_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: admin
    with TestClient(app) as c:
        yield {"c": c, "db": db, "admin": admin, "a1": a1, "a2": a2}
    db.close()


def test_put_empty_serial_normalizes_to_null(ctx):
    c, a1, a2 = ctx["c"], ctx["a1"], ctx["a2"]
    r1 = c.put(f"/api/v1/assets/{a1.id}", json={"department": "x", "serial_number": ""})
    assert r1.status_code == 200 and r1.json()["serial_number"] is None
    # 第二行同样"未填"——旧版此处撞 UNIQUE 500
    r2 = c.put(f"/api/v1/assets/{a2.id}", json={"department": "y", "serial_number": ""})
    assert r2.status_code == 200 and r2.json()["serial_number"] is None


def test_put_real_duplicate_serial_returns_400(ctx):
    c, a1, a2 = ctx["c"], ctx["a1"], ctx["a2"]
    r1 = c.put(f"/api/v1/assets/{a1.id}", json={"serial_number": "SN-DUP-1"})
    assert r1.status_code == 200
    r2 = c.put(f"/api/v1/assets/{a2.id}", json={"serial_number": "SN-DUP-1"})
    assert r2.status_code == 400 and "序列号" in r2.json()["detail"]


def test_create_empty_serial_ok(ctx):
    r = ctx["c"].post("/api/v1/assets/", json={"name": "new", "asset_type": "server",
                                               "serial_number": "  "})
    assert r.status_code == 200 and r.json()["serial_number"] is None
