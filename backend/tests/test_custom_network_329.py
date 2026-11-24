# -*- coding: utf-8 -*-
"""32.9：自定义网络（如"互联网"）/自定义类型（如"信息系统"）筛选不再 422

原 network_location 查询参数类型是 NetworkLocation 枚举，用户新增自定义网络
（存的是中文字面值"互联网"）后，下拉选它筛选 → FastAPI 校验失败 422。
改 Optional[str] 后放行；同时验证筛选命中正确。
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
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    db.add(admin)
    db.flush()
    db.add_all([
        AssetModel(name="公网门户", asset_type="信息系统", network_location="互联网",
                   creator_id=admin.id, ip_address="222.1.1.1"),
        AssetModel(name="内网OA", asset_type="信息系统", network_location="office",
                   creator_id=admin.id, ip_address="192.168.0.24"),
        AssetModel(name="交换机", asset_type="network", network_location="monitoring",
                   creator_id=admin.id, ip_address="192.168.1.1"),
    ])
    db.commit()
    app = FastAPI()
    from app.api.endpoints import assets as asset_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: admin
    with TestClient(app) as c:
        yield {"c": c, "admin": admin}
    db.close()


def test_filter_custom_network_internet(ctx):
    r = ctx["c"].get("/api/v1/assets/", params={"network_location": "互联网"})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert len(items) == 1 and items[0]["name"] == "公网门户"


def test_filter_enum_still_works(ctx):
    for loc, want in [("office", 1), ("monitoring", 1)]:
        r = ctx["c"].get("/api/v1/assets/", params={"network_location": loc})
        assert r.status_code == 200 and len(r.json()["items"]) == want


def test_filter_custom_asset_type(ctx):
    r = ctx["c"].get("/api/v1/assets/", params={"asset_type": "信息系统"})
    assert r.status_code == 200 and len(r.json()["items"]) == 2


def test_filter_combined_custom(ctx):
    r = ctx["c"].get("/api/v1/assets/", params={"asset_type": "信息系统", "network_location": "互联网"})
    assert r.status_code == 200 and len(r.json()["items"]) == 1
