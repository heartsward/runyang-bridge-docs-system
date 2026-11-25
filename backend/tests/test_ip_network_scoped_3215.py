# -*- coding: utf-8 -*-
"""32.15：IP 唯一性 = 同一网络内唯一（不同网络可复用同一 IP）"""
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
    admin = UserModel(username="adm", email="a@t.local", hashed_password="x", is_active=True, is_superuser=True)
    db.add(admin); db.flush()
    # 办公网已有一台 10.0.0.5
    db.add(AssetModel(name="已有服务器", asset_type="server", ip_address="10.0.0.5",
                      network_location="办公网", creator_id=admin.id))
    db.commit()
    box = {"actor": admin}
    app = FastAPI()
    from app.api.endpoints import assets as asset_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: box["actor"]
    with TestClient(app) as c:
        yield {"c": c, "db": db, "admin": admin, "box": box}
    db.close()


def test_create_same_ip_same_network_rejected(ctx):
    r = ctx["c"].post("/api/v1/assets/", json={"name": "冲突机", "asset_type": "server",
                                               "ip_address": "10.0.0.5", "network_location": "办公网"})
    assert r.status_code == 400
    assert "办公网" in r.json()["detail"]


def test_create_same_ip_different_network_ok(ctx):
    r = ctx["c"].post("/api/v1/assets/", json={"name": "监控网同IP", "asset_type": "server",
                                               "ip_address": "10.0.0.5", "network_location": "监控网"})
    assert r.status_code == 200, r.text
    assert r.json()["network_location"] == "监控网"


def test_update_move_network_conflict(ctx):
    # 新建监控网 10.0.0.9
    a = ctx["c"].post("/api/v1/assets/", json={"name": "待迁移", "asset_type": "server",
                                               "ip_address": "10.0.0.9", "network_location": "监控网"}).json()
    # 改成办公网——办公网里已有 10.0.0.9？没有。先造一个
    ctx["c"].post("/api/v1/assets/", json={"name": "办公网占位", "asset_type": "server",
                                           "ip_address": "10.0.0.9", "network_location": "办公网"})
    r = ctx["c"].put(f"/api/v1/assets/{a['id']}", json={"network_location": "办公网"})
    assert r.status_code == 400
    assert "办公网" in r.json()["detail"]


def test_update_ip_same_network_ok(ctx):
    # 改自己 IP 到同网络另一个未占用值
    a = ctx["c"].post("/api/v1/assets/", json={"name": "改IP", "asset_type": "server",
                                               "ip_address": "10.0.0.77", "network_location": "监控网"}).json()
    r = ctx["c"].put(f"/api/v1/assets/{a['id']}", json={"ip_address": "10.0.0.78"})
    assert r.status_code == 200


def test_null_network_group_unique(ctx):
    # 两边都未设网络 → 视为同组，仍不允许重复
    ctx["c"].post("/api/v1/assets/", json={"name": "无网络A", "asset_type": "server", "ip_address": "10.9.9.9"})
    r = ctx["c"].post("/api/v1/assets/", json={"name": "无网络B", "asset_type": "server", "ip_address": "10.9.9.9"})
    assert r.status_code == 400
