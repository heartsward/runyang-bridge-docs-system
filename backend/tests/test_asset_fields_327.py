# -*- coding: utf-8 -*-
"""32.7：运维责任新列 + 扩展字段搜索覆盖回归

1. PUT 写入 5 个新列 → 200 且回读正确
2. 搜索命中：联系人/联系电话/开发单位/运维单位/中间件版本/信息系统名称/应用版本/序列号/MAC
3. 搜索仍保持"词间 AND、字段间 OR"语义（两词组合命中同一行）
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
    a1 = AssetModel(name="防火墙A", asset_type="security", creator_id=admin.id,
                    service_name="路网管控平台", system_version="V6.0.1",
                    middleware_version="Tomcat9.0.85", dev_company="江苏智行科技",
                    ops_company="润扬运维中心", contact_person="赵工",
                    contact_phone="13900001111", serial_number="SN-AAA-001",
                    mac_address="00:1A:2B:3C:4D:5E")
    a2 = AssetModel(name="服务器B", asset_type="server", creator_id=admin.id)
    db.add_all([a1, a2])
    db.commit()

    app = FastAPI()
    from app.api.endpoints import assets as asset_ep
    app.include_router(asset_ep.router, prefix="/api/v1/assets")
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: admin
    with TestClient(app) as c:
        yield {"c": c, "db": db, "a1": a1, "a2": a2}
    db.close()


def test_put_writes_new_columns(ctx):
    c, a2 = ctx["c"], ctx["a2"]
    r = c.put(f"/api/v1/assets/{a2.id}", json={
        "middleware_version": "Nginx1.24", "dev_company": "XX科技",
        "ops_company": "YY中心", "contact_person": "钱工", "contact_phone": "0514-88888888"})
    assert r.status_code == 200, r.text
    j = r.json()
    assert (j["middleware_version"], j["dev_company"], j["ops_company"],
            j["contact_person"], j["contact_phone"]) == (
        "Nginx1.24", "XX科技", "YY中心", "钱工", "0514-88888888")


@pytest.mark.parametrize("keyword,hit", [
    ("赵工", 1), ("13900001111", 1), ("江苏智行", 1), ("润扬运维", 1),
    ("Tomcat9", 1), ("路网管控平台", 1), ("V6.0.1", 1), ("SN-AAA-001", 1),
    ("00:1A:2B", 1),
])
def test_search_covers_ext_fields(ctx, keyword, hit):
    items = ctx["c"].get("/api/v1/assets/", params={"search": keyword}).json()["items"]
    assert len(items) == hit, f"{keyword} 应命中 {hit} 条，实际 {len(items)}"


def test_search_multi_term_and(ctx):
    # 词间 AND：两词分别命中不同列、同一行 → 命中 1
    items = ctx["c"].get("/api/v1/assets/", params={"search": "赵工 Tomcat"}).json()["items"]
    assert len(items) == 1
    # 跨行不匹配
    items = ctx["c"].get("/api/v1/assets/", params={"search": "服务器B 赵工"}).json()["items"]
    assert len(items) == 0
