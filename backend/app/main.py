from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api_v1 import api_router
from app.core.config import settings
from app.db.database import engine
from app.models import user, document, asset

# 创建数据库表
user.Base.metadata.create_all(bind=engine)
document.Base.metadata.create_all(bind=engine)
asset.Base.metadata.create_all(bind=engine)

# 启动后台任务处理器
def startup_background_tasks():
    try:
        from app.services.background_tasks import start_background_tasks
        start_background_tasks()
        print("后台任务处理器已启动")
    except Exception as e:
        print(f"后台任务处理器启动失败: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="运维文档管理系统后端API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加启动事件
@app.on_event("startup")
async def startup_event():
    startup_background_tasks()

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
        host="127.0.0.1",
        port=8000,
        reload=False
    )