from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_v1 import api_router
from app.core.config import settings
from app.db.database import engine
from app.models import user, document, asset
import os
import warnings

# 设置时区环境变量
os.environ['TZ'] = settings.TIMEZONE

# 验证bcrypt功能并处理版本警告
def verify_bcrypt_functionality():
    """验证bcrypt密码哈希功能是否正常工作"""
    try:
        from app.core.security import get_password_hash, verify_password
        
        # 测试密码哈希和验证功能
        test_password = "test123"
        hashed = get_password_hash(test_password)
        is_valid = verify_password(test_password, hashed)
        
        if is_valid:
            print("OK: bcrypt密码哈希功能正常")
            return True
        else:
            print("ERROR: bcrypt密码验证失败")
            return False
            
    except Exception as e:
        # 检查是否是bcrypt版本警告
        if "bcrypt" in str(e) and "__about__" in str(e):
            print("WARNING: bcrypt版本警告: 新版本bcrypt移除了__about__属性，但功能正常")
            # 尝试直接测试密码功能
            try:
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                test_hash = pwd_context.hash("test123")
                if pwd_context.verify("test123", test_hash):
                    print("OK: bcrypt核心功能验证成功（忽略版本警告）")
                    return True
            except Exception as inner_e:
                print(f"ERROR: bcrypt功能测试失败: {inner_e}")
                return False
        else:
            print(f"ERROR: bcrypt初始化失败: {e}")
            return False

# 创建数据库表
user.Base.metadata.create_all(bind=engine)
document.Base.metadata.create_all(bind=engine)
asset.Base.metadata.create_all(bind=engine)

# 初始化默认用户
def init_default_users():
    """初始化默认用户"""
    try:
        from sqlalchemy.orm import Session
        from app.crud.user import user as crud_user
        from app.schemas.user import UserCreate
        
        db = Session(bind=engine)
        try:
            # 检查admin用户是否已存在
            existing_admin = crud_user.get_by_username(db, username="admin")
            if not existing_admin:
                # 创建默认管理员用户
                admin_user = UserCreate(
                    username="admin",
                    email="admin@system.com",
                    password="admin123",
                    full_name="系统管理员",
                    department="技术部",
                    position="系统管理员",
                    phone="13800138000",
                    is_active=True,
                    is_superuser=True
                )
                
                created_user = crud_user.create(db, obj_in=admin_user)
                print("OK: 默认管理员用户创建成功 (admin/admin123)")
            else:
                # 检查现有admin用户是否具有管理员权限
                if not existing_admin.is_superuser:
                    print("INFO: admin用户存在但缺少管理员权限，正在修复...")
                    existing_admin.is_superuser = True
                    db.add(existing_admin)
                    db.commit()
                    print("OK: admin用户管理员权限已修复")
                else:
                    print("OK: 管理员用户已存在且权限正常")
        finally:
            db.close()
    except Exception as e:
        print(f"WARNING: 用户初始化异常: {e}")
        print("INFO: 管理员用户可能已存在，系统继续启动")

# 启动后台任务处理器
def startup_background_tasks():
    try:
        from app.services.background_tasks import start_background_tasks
        start_background_tasks()
        print("后台任务处理器已启动")
    except Exception as e:
        print(f"后台任务处理器启动失败: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    print("=" * 50)
    print(f"启动 {settings.PROJECT_NAME} v{settings.VERSION}...")
    print("=" * 50)
    
    # 1. 验证bcrypt功能
    print("[1/3] 验证密码哈希功能...")
    bcrypt_ok = verify_bcrypt_functionality()
    
    # 2. 初始化默认用户
    print("[2/3] 初始化用户系统...")
    init_default_users()
    
    # 3. 启动后台任务
    print("[3/3] 启动后台任务...")
    startup_background_tasks()
    
    print("=" * 50)
    if bcrypt_ok:
        print("SUCCESS: 系统启动完成，所有功能正常")
    else:
        print("WARNING: 系统启动完成，但密码功能可能有问题")
    print(f"API文档: http://localhost:8000/docs")
    print(f"健康检查: http://localhost:8000/health")
    print("=" * 50)
    
    yield
    
    # 关闭时执行
    print("应用程序正在关闭...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="运维文档管理系统后端API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """
    根路径，返回API信息
    """
    return {
        "message": f"欢迎使用{settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/health")
def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy", "version": settings.VERSION}

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False
    )