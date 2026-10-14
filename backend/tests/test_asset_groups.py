# -*- coding: utf-8 -*-
"""自定义分组（assets.groups）回归测试（阶段二十八·28.4）

覆盖：
1. schema：AssetBase/AssetUpdate 含 groups；parse_groups 兼容 JSON 串/逗号串/list/空
2. 端点：create/update 时 groups 列表 → JSON 字符串落库；回读为 list
3. 列表端点 group= 筛选：json_each 精确匹配（"区" 不会命中 "核心区"）
4. system-config：asset-groups GET/PUT（含与资产实际分组名合并去重）
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
from app.models.system_config import SystemConfig  # noqa: E402
from app.schemas.asset import AssetBase, AssetUpdate  # noqa: E402
from app.core import deps  # noqa: E402


# ---------- schema 单元 ----------

def test_schema_has_groups():
    assert "groups" in AssetBase.model_fields
    assert "groups" in AssetUpdate.model_fields


def test_parse_groups_variants():
    assert AssetBase(name="x", asset_type="server", groups='["a", "b"]').groups == ["a", "b"]
    assert AssetBase(name="x", asset_type="server", groups="a,b").groups == ["a", "b"]
    assert AssetBase(name="x", asset_type="server", groups=["a"]).groups == ["a"]
    assert AssetBase(name="x", asset_type="server", groups="").groups == []
    assert AssetBase(name="x", asset_type="server", groups=None).groups is None


# ---------- 端点 e2e（隔离内存库） ----------

@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=[AssetModel.__table__, UserModel.__table__, SystemConfig.__table__])
    Session = sessionmaker(bind=engine)
    db = Session()
    u = UserModel(username="tuser", email="tuser@test.local", hashed_password="x", is_active=True, is_superuser=True)
    db.add(u)
    db.commit()

    app = FastAPI()
    from app.api.endpoints import assets as assets_ep, system_config as sc_ep
    app.include_router(assets_ep.router, prefix="/api/v1/assets")
    app.include_router(sc_ep.router, prefix="/api/v1/system-config")

    def _override_db():
        yield db
    # 注意：端点依赖的是 deps.get_db（不是 app.db.database.get_db），
    # override 键必须是端点实际引用的那个函数对象，否则会打到真实库！
    app.dependency_overrides[deps.get_db] = _override_db
    app.dependency_overrides[deps.get_current_active_user] = lambda: u
    app.dependency_overrides[deps.get_current_user] = lambda: u
    with TestClient(app) as c:
        yield c
    db.close()


def _mk(client, name, groups=None):
    body = {"name": name, "asset_type": "server", "network_location": "office"}
    if groups is not None:
        body["groups"] = groups
    r = client.post("/api/v1/assets/", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_create_with_groups_roundtrip(client):
    a = _mk(client, "dev1", groups=["核心区", "机房"])
    assert a["groups"] == ["核心区", "机房"]
    g = client.get(f"/api/v1/assets/{a['id']}").json()["groups"]
    assert g == ["核心区", "机房"]


def test_update_groups(client):
    a = _mk(client, "dev2", groups=["A"])
    r = client.put(f"/api/v1/assets/{a['id']}", json={"groups": ["B", "C"]})
    assert r.status_code == 200, r.text
    assert r.json()["groups"] == ["B", "C"]


def test_group_filter_exact_match(client):
    _mk(client, "core", groups=["核心区"])
    _mk(client, "zone", groups=["区"])
    r = client.get("/api/v1/assets/", params={"group": "区"})
    assert r.status_code == 200, r.text
    names = [x["name"] for x in r.json()["items"]]
    assert names == ["zone"]  # "区" 精确匹配，不命中 "核心区"
    r2 = client.get("/api/v1/assets/", params={"group": "核心区"})
    assert [x["name"] for x in r2.json()["items"]] == ["core"]


def test_asset_groups_config_crud(client):
    r = client.put("/api/v1/system-config/asset-groups", json=["机房", " 机房 ", "外场", ""])
    assert r.status_code == 200, r.text
    assert r.json() == ["外场", "机房"]  # sorted() 按 Unicode 码位：外(U+5916) < 机(U+673A)
    # 资产实际用到的分组名会合并进列表（去重）
    _mk(client, "dev3", groups=["收费网专项"])
    r2 = client.get("/api/v1/system-config/asset-groups")
    assert "机房" in r2.json() and "收费网专项" in r2.json()


def test_delete_group_cascades_to_assets(client):
    # 建两个分组，两台设备分别挂载（其中一台挂两个）
    client.put("/api/v1/system-config/asset-groups", json=["机房", "核心区"])
    a1 = _mk(client, "devA", groups=["机房", "核心区"])
    a2 = _mk(client, "devB", groups=["核心区"])
    a3 = _mk(client, "devC", groups=["机房"])

    r = client.delete("/api/v1/system-config/asset-groups/核心区")
    assert r.status_code == 200, r.text
    assert r.json()["removed_from_assets"] == 2  # devA + devB

    # 设备挂载已级联清理
    assert client.get(f"/api/v1/assets/{a1['id']}").json()["groups"] == ["机房"]
    assert client.get(f"/api/v1/assets/{a2['id']}").json()["groups"] == []
    assert client.get(f"/api/v1/assets/{a3['id']}").json()["groups"] == ["机房"]
    # 分组定义也移除
    assert client.get("/api/v1/system-config/asset-groups").json() == ["机房"]
    # 筛选不再命中
    r2 = client.get("/api/v1/assets/", params={"group": "核心区"})
    assert r2.json()["total"] == 0
