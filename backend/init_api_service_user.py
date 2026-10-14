#!/usr/bin/env python3
"""
阶段二十八：初始化 API 服务账号（配合固定令牌认证通道）

背景：
    此前 AI 工作台 / 脚本做写操作（上传、改台账、改文档）都要用 admin 账号密码
    换 JWT，与人工登录混在同一身份里，审计分不清"是人还是脚本"，且默认密码
    admin/admin123 一旦改了脚本就全断。
    本脚本建一个**专用服务账号**（默认 api_client），后端用固定令牌
    （.env 里的 API_TOKEN）认证后映射到它，实现身份隔离 + 可单独撤销。

关键设计：
    服务账号的密码是**每次运行随机生成**的（不落盘、不打印），
    等于把"密码登录"这条路对服务账号彻底封死——只有固定令牌能用它。
    这样即使有人拿到用户名，也没法用密码登录 Web 界面。

用法：
    python init_api_service_user.py                # 创建/校验 api_client（超管）
    python init_api_service_user.py --username rwbot   # 自定义用户名
    python init_api_service_user.py --no-superuser     # 不给超管（只能改台账，不能上传）
    python init_api_service_user.py --check            # 只检查是否存在，不创建
    python init_api_service_user.py --gen-token        # 只打印一个强随机令牌（配 .env 用）

配套 .env（三个键，缺一不生效）：
    API_TOKEN_ENABLED=true
    API_TOKEN=<上面 --gen-token 生成的串>
    API_SERVICE_USERNAME=api_client
"""
import argparse
import secrets
import sys

from sqlalchemy.orm import Session

from app.db.database import engine
from app.models.user import User
from app.core.security import get_password_hash
from app.core.config import settings


def gen_token() -> str:
    """生成强随机 API 令牌（secrets 走 OS CSPRNG）"""
    return secrets.token_urlsafe(32)


def ensure_service_user(username: str, is_superuser: bool) -> int:
    """创建服务账号（幂等）。返回用户 id。"""
    db = Session(bind=engine)
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            if not existing.is_superuser and is_superuser:
                print(f"⚠️  服务账号 '{username}' 存在但缺超管权限，正在修复...")
                existing.is_superuser = True
                db.add(existing)
                db.commit()
                print("✅ 超管权限已补齐")
            elif existing.is_superuser and not is_superuser:
                print(f"⚠️  服务账号 '{username}' 当前是超管，本次要求非超管，正在降级...")
                existing.is_superuser = False
                db.add(existing)
                db.commit()
                print("✅ 已降级为非超管（上传类操作将返回 403）")
            if not existing.is_active:
                print(f"⚠️  服务账号 '{username}' 处于禁用状态，正在启用...")
                existing.is_active = True
                db.add(existing)
                db.commit()
                print("✅ 已启用")
            print(f"✓ 服务账号已存在：{username} (id={existing.id}, "
                  f"superuser={existing.is_superuser}, active={existing.is_active})")
            return existing.id

        # 随机密码：不落盘不打印 → 密码登录路径事实上封死
        new_user = User(
            username=username,
            email=f"{username}@api.internal",
            hashed_password=get_password_hash(secrets.token_urlsafe(24)),
            full_name="API 服务账号（固定令牌专用）",
            department="系统",
            position="API Client",
            is_active=True,
            is_superuser=is_superuser,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✓ 服务账号创建成功")
        print(f"  用户名: {username}")
        print(f"  id:     {new_user.id}")
        print(f"  超管:   {new_user.is_superuser}")
        print(f"  密码:   随机生成且未保存 —— 该账号【不能】用密码登录，只能走固定令牌")
        return new_user.id

    except Exception as e:
        print(f"✗ 服务账号创建失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_service_user(username: str) -> bool:
    with Session(bind=engine) as db:
        u = db.query(User).filter(User.username == username).first()
        if u is None:
            print(f"✗ 服务账号 '{username}' 不存在 —— 运行本脚本（不带 --check）创建")
            return False
        print(f"✓ 服务账号存在：{username} (id={u.id}, superuser={u.is_superuser}, active={u.is_active})")
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 API 服务账号（固定令牌通道）")
    parser.add_argument("--username", default=settings.API_SERVICE_USERNAME,
                        help=f"服务账号用户名（默认取 .env 的 API_SERVICE_USERNAME={settings.API_SERVICE_USERNAME}）")
    parser.add_argument("--no-superuser", action="store_true",
                        help="不给超管权限（能改设备台账，但上传/删除会 403）")
    parser.add_argument("--check", action="store_true", help="只检查，不创建")
    parser.add_argument("--gen-token", action="store_true", help="只打印一个强随机令牌后退出")
    args = parser.parse_args()

    if args.gen_token:
        print(gen_token())
        return 0

    if args.check:
        return 0 if check_service_user(args.username) else 1

    print(f"正在初始化 API 服务账号 '{args.username}' ...")
    ensure_service_user(args.username, is_superuser=not args.no_superuser)

    print()
    print("下一步（配 backend/.env，三个键都要）：")
    print("  API_TOKEN_ENABLED=true")
    print(f"  API_TOKEN=<python init_api_service_user.py --gen-token 的输出>")
    print(f"  API_SERVICE_USERNAME={args.username}")
    print("配完重启后端即生效；脚本侧把令牌放环境变量 WIKI_API_TOKEN 即可免登录。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
