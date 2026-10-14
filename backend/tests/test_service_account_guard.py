# -*- coding: utf-8 -*-
"""API 服务账号（api_client）用户管理防护测试（阶段二十八·28.6）

覆盖 settings.py 用户端点新增的保护：
1. 给服务账号设密码 → 400（密码登录通道刻意封死）
2. 服务账号改名 → 400（改名会静默打断固定令牌映射）
3. 其他账号改名成保留名 api_client → 400（防冒名）
4. 创建用户用保留名 → 400
5. 服务账号改备注类字段（full_name/department）→ 放行
6. 普通账号改密码 → 放行（不误伤）
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
from app.models.user import User  # noqa: E402
from app.core import deps  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(deps.settings, "API_SERVICE_USERNAME", "api_client", raising=False)
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = User(username="admin", email="a@a.local", hashed_password="x",
                 is_active=True, is_superuser=True)
    svc = User(username="api_client", email="api_client@api.internal",
               hashed_password="random-hash", is_active=True, is_superuser=True)
    normal = User(username="zhangsan", email="z@z.local", hashed_password="x",
                  is_active=True, is_superuser=False)
    db.add_all([admin, svc, normal])
    db.commit()

    app = FastAPI()
    from app.api.endpoints import settings as settings_ep
    app.include_router(settings_ep.router, prefix="/api/v1/settings")
    # 端点引用的是 settings.py 里 from app.core.deps import get_db / get_current_active_user
    from app.api.endpoints.settings import get_db as ep_get_db, get_current_active_user as ep_cu
    app.dependency_overrides[ep_get_db] = lambda: (yield db)
    app.dependency_overrides[ep_cu] = lambda: admin
    with TestClient(app) as c:
        yield c
    db.close()


def _uid(client, username):
    for u in client.get("/api/v1/settings/users").json():
        if u["username"] == username:
            return u["id"]
    raise AssertionError(f"user {username} not found")


def test_service_account_password_rejected(client):
    r = client.put(f"/api/v1/settings/users/{_uid(client, 'api_client')}",
                   json={"password": "NowIKnowIt123"})
    assert r.status_code == 400
    assert "不允许修改密码" in r.json()["detail"]


def test_service_account_rename_rejected(client):
    r = client.put(f"/api/v1/settings/users/{_uid(client, 'api_client')}",
                   json={"username": "api_client2"})
    assert r.status_code == 400
    assert "不允许改名" in r.json()["detail"]


def test_reserved_name_takeover_rejected(client):
    r = client.put(f"/api/v1/settings/users/{_uid(client, 'zhangsan')}",
                   json={"username": "api_client"})
    assert r.status_code == 400
    assert "保留名" in r.json()["detail"]


def test_create_reserved_name_rejected(client):
    r = client.post("/api/v1/settings/users",
                    json={"username": "api_client", "email": "fake@f.local", "password": "x123456"})
    assert r.status_code == 400
    assert "保留名" in r.json()["detail"]


def test_service_account_other_fields_allowed(client):
    r = client.put(f"/api/v1/settings/users/{_uid(client, 'api_client')}",
                   json={"full_name": "API 服务账号（2026-10 启用）", "password": ""})
    assert r.status_code == 200
    assert r.json()["full_name"] == "API 服务账号（2026-10 启用）"


def test_normal_user_password_change_allowed(client):
    r = client.put(f"/api/v1/settings/users/{_uid(client, 'zhangsan')}",
                   json={"password": "NewPass2026!"})
    assert r.status_code == 200
