# -*- coding: utf-8 -*-
"""32.8：删除用户自动取消共享 + 用户管理一键取消（文档/资产分开）

1. DELETE /settings/users/{id} → 该用户全部 Share 行清空、用户删除、返回 shares_cancelled
2. GET  /settings/users → share_doc_count / share_asset_count 分列计数
3. DELETE /settings/users/{id}/shares?item_type=document → 只清文档共享，资产保留
4. DELETE /settings/users/{id}/shares（不带类型）→ 全清
5. 非管理员调用 → 403
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
from app.models.share import Share  # noqa: E402
from app.models.user import User as UserModel  # noqa: E402
from app.core import deps  # noqa: E402


@pytest.fixture
def ctx():
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False}, poolclass=StaticPool)
    import app.models  # noqa: F401  # 触发全部模型注册
    Base.metadata.create_all(bind=engine)  # 建全表：delete_user 的 ORM 级联会触碰各关系表
    Session = sessionmaker(bind=engine)
    db = Session()
    admin = UserModel(username="adm", email="adm@t.local", hashed_password="x",
                      is_active=True, is_superuser=True)
    normal = UserModel(username="usr", email="usr@t.local", hashed_password="x",
                       is_active=True, is_superuser=False)
    other = UserModel(username="oth", email="oth@t.local", hashed_password="x",
                      is_active=True, is_superuser=False)
    db.add_all([admin, normal, other])
    db.flush()
    # normal：2 篇文档 + 2 项资产被分享；other：2 项资产被分享
    for i in (1, 2):
        db.add(Share(item_type="document", item_id=i, shared_by_id=admin.id,
                     shared_with_id=normal.id))
        db.add(Share(item_type="asset", item_id=i, shared_by_id=admin.id,
                     shared_with_id=normal.id))
        db.add(Share(item_type="asset", item_id=10 + i, shared_by_id=admin.id,
                     shared_with_id=other.id))
    db.commit()

    app = FastAPI()
    from app.api.endpoints import settings as settings_ep
    app.include_router(settings_ep.router, prefix="/api/v1/settings")

    box = {"actor": admin}  # 各测试前设置当前登录者
    app.dependency_overrides[deps.get_db] = lambda: (yield db)
    app.dependency_overrides[deps.get_current_active_user] = lambda: box["actor"]
    with TestClient(app) as c:
        yield {"c": c, "db": db, "admin": admin, "normal": normal, "other": other, "box": box}
    db.close()


def _shares_of(db, uid):
    return db.query(Share).filter(Share.shared_with_id == uid).count()


def test_list_users_has_share_counts(ctx):
    ctx["box"]["actor"] = ctx["admin"]
    users = ctx["c"].get("/api/v1/settings/users").json()
    by_name = {u["username"]: u for u in users}
    assert by_name["usr"]["share_doc_count"] == 2
    assert by_name["usr"]["share_asset_count"] == 2
    assert by_name["oth"]["share_doc_count"] == 0
    assert by_name["oth"]["share_asset_count"] == 2


def test_delete_user_cancels_all_shares(ctx):
    ctx["box"]["actor"] = ctx["admin"]
    uid = ctx["normal"].id
    assert _shares_of(ctx["db"], uid) == 4
    r = ctx["c"].delete(f"/api/v1/settings/users/{uid}")
    assert r.status_code == 200, r.text
    assert r.json()["shares_cancelled"] == 4
    assert _shares_of(ctx["db"], uid) == 0
    assert ctx["db"].query(UserModel).filter(UserModel.id == uid).first() is None
    # 其他用户的分享不受影响
    assert _shares_of(ctx["db"], ctx["other"].id) == 2


def test_cancel_shares_by_type(ctx):
    ctx["box"]["actor"] = ctx["admin"]
    uid = ctx["normal"].id
    r = ctx["c"].delete(f"/api/v1/settings/users/{uid}/shares", params={"item_type": "document"})
    assert r.status_code == 200 and r.json()["cancelled"] == 2
    # 只剩资产分享
    assert _shares_of(ctx["db"], uid) == 2
    r2 = ctx["c"].delete(f"/api/v1/settings/users/{uid}/shares")
    assert r2.json()["cancelled"] == 2
    assert _shares_of(ctx["db"], uid) == 0


def test_cancel_shares_forbidden_for_non_admin(ctx):
    ctx["box"]["actor"] = ctx["normal"]
    r = ctx["c"].delete(f"/api/v1/settings/users/{ctx['other'].id}/shares")
    assert r.status_code == 403
