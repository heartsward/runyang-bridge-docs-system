from fastapi import APIRouter

api_router = APIRouter()

# 临时禁用有问题的路由，使用直接API替代
try:
    from app.api.endpoints import auth, documents, upload, upload_multiple, assets, search, categories, settings, tasks, analytics
    
    # 包含核心路由
    api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
    api_router.include_router(documents.router, prefix="/documents", tags=["文档"])
    api_router.include_router(upload.router, prefix="/upload", tags=["文件上传"])
    api_router.include_router(upload_multiple.router, prefix="/multi-upload", tags=["多文件上传"])
    api_router.include_router(assets.router, prefix="/assets", tags=["设备资产"])
    api_router.include_router(search.router, prefix="/search", tags=["智能搜索"])
    api_router.include_router(categories.router, prefix="/categories", tags=["分类管理"])
    api_router.include_router(settings.router, prefix="/settings", tags=["用户设置"])
    api_router.include_router(tasks.router, prefix="/tasks", tags=["后台任务"])
    api_router.include_router(analytics.router, prefix="/analytics", tags=["数据分析"])
        
except Exception as e:
    print(f"警告：API路由加载失败: {e}")
    # 至少包含认证路由
    try:
        from app.api.endpoints import auth
        api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
    except Exception as auth_error:
        print(f"错误：无法加载认证路由: {auth_error}")