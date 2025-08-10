from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from app.core.deps import get_db, get_current_active_user, get_optional_user
from app.crud import document as crud_document
from app.models.user import User
from app.schemas.document import (
    Document, DocumentCreate, DocumentUpdate, DocumentList,
    Category, CategoryCreate, CategoryUpdate
)

router = APIRouter()


# 文档相关接口
@router.get("/", response_model=List[Document], summary="获取文档列表")
def read_documents(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取文档列表
    """
    documents = crud_document.get_multi(
        db, skip=skip, limit=limit, 
        category_id=category_id, status=status
    )
    return documents


@router.post("/", response_model=Document, summary="创建文档")
def create_document(
    *,
    db: Session = Depends(get_db),
    document_in: DocumentCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新文档 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能创建文档
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以创建文档")
    
    document = crud_document.create(db=db, obj_in=document_in, owner_id=current_user.id)
    return document


@router.get("/{document_id}", response_model=Document, summary="获取文档详情")
def read_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    获取指定文档的详细信息
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 增加查看次数
    user_id = current_user.id if current_user else None
    crud_document.increment_view_count(db=db, document_id=document_id, user_id=user_id)
    
    return document


@router.put("/{document_id}", response_model=Document, summary="更新文档")
def update_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    document_in: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    更新文档信息
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 检查权限
    if document.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="权限不足")
    
    document = crud_document.update(db=db, db_obj=document, obj_in=document_in)
    return document


@router.delete("/{document_id}", summary="删除文档")
def delete_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """
    删除文档 - 仅管理员可操作
    """
    # 检查权限：只有管理员才能删除文档
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="只有管理员可以删除文档")
    
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    document = crud_document.delete(db=db, id=document_id)
    return {"message": "文档删除成功"}


@router.get("/search/", response_model=List[Document], summary="搜索文档")
def search_documents(
    query: str = Query(..., description="搜索关键词"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    搜索文档
    """
    documents = crud_document.search(db=db, query=query, skip=skip, limit=limit)
    return documents


@router.get("/popular/", response_model=List[Document], summary="获取热门文档")
def read_popular_documents(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    获取热门文档列表
    """
    documents = crud_document.get_popular(db=db, limit=limit)
    return documents


# 分类相关接口
@router.get("/categories/", response_model=List[Category], summary="获取分类列表")
def read_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取分类列表
    """
    categories = crud_document.get_categories(db, skip=skip, limit=limit)
    return categories


@router.post("/categories/", response_model=Category, summary="创建分类")
def create_category(
    *,
    db: Session = Depends(get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    创建新分类
    """
    category = crud_document.create_category(
        db=db, obj_in=category_in, creator_id=current_user.id
    )
    return category


@router.put("/categories/{category_id}", response_model=Category, summary="更新分类")
def update_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_active_user),
):
    """
    更新分类信息
    """
    category = crud_document.get_category(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    category = crud_document.update_category(db=db, db_obj=category, obj_in=category_in)
    return category


@router.delete("/categories/{category_id}", summary="删除分类")
def delete_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """
    删除分类
    """
    category = crud_document.get_category(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    category = crud_document.delete_category(db=db, id=category_id)
    return {"message": "分类删除成功"}


@router.get("/{document_id}/download", summary="下载文档")
def download_document(
    *,
    db: Session = Depends(get_db),
    document_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    下载文档文件
    """
    document = crud_document.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="文档文件不存在")
    
    # 增加下载次数
    user_id = current_user.id if current_user else None
    crud_document.increment_download_count(db=db, document_id=document_id, user_id=user_id)
    
    # 获取文件信息
    filename = os.path.basename(document.file_path)
    
    return FileResponse(
        path=document.file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


# 数据分析统计端点
@router.get("/analytics/stats", summary="获取数据分析统计")
async def get_analytics_stats(
    db: Session = Depends(get_db)
):
    """获取系统数据分析统计信息 - 返回真实数据"""
    from app.models.asset import Asset
    from app.models.document import Document, DocumentView, DocumentDownload, SearchLog, AssetView
    from app.models.user import User
    from sqlalchemy import func, desc
    from datetime import datetime, timedelta
    
    try:
        # 基础统计数据
        total_documents = db.query(Document).count()
        total_assets = db.query(Asset).count()
        total_users = db.query(User).count()
        
        # 文档访问统计 - 从 document_views 表获取
        total_document_views = db.query(DocumentView).count()
        
        # 资产查看统计 - 从 asset_views 表获取
        total_asset_views = db.query(AssetView).count()
        
        # 获取最近30天的活跃用户（有任何操作的用户）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_users_count = db.query(User.id).join(
            DocumentView, User.id == DocumentView.user_id, isouter=True
        ).filter(
            DocumentView.created_at >= thirty_days_ago
        ).distinct().count()
        
        # 用户活动排行榜 - 使用子查询避免笛卡尔积问题
        from sqlalchemy.orm import aliased
        
        # 分别统计每个用户的各类活动次数
        users = db.query(User.id, User.username).all()
        user_activity_stats = []
        
        for user in users:
            # 统计文档查看次数
            doc_views = db.query(func.count(DocumentView.id)).filter(
                DocumentView.user_id == user.id
            ).scalar() or 0
            
            # 统计文档下载次数  
            doc_downloads = db.query(func.count(DocumentDownload.id)).filter(
                DocumentDownload.user_id == user.id
            ).scalar() or 0
            
            # 统计资产查看次数
            asset_views = db.query(func.count(AssetView.id)).filter(
                AssetView.user_id == user.id
            ).scalar() or 0
            
            # 只包含有活动的用户
            if doc_views > 0 or doc_downloads > 0 or asset_views > 0:
                # 创建一个类似于原来查询结果的对象
                class UserActivityStat:
                    def __init__(self, user_id, username, doc_views, doc_downloads, asset_views):
                        self.userId = user_id
                        self.username = username
                        self.documentViews = doc_views
                        self.documentDownloads = doc_downloads  
                        self.assetViews = asset_views
                
                user_activity_stats.append(UserActivityStat(
                    user.id, user.username, doc_views, doc_downloads, asset_views
                ))
        
        # 按总活动量排序
        user_activity_stats.sort(key=lambda x: x.documentViews + x.assetViews, reverse=True)
        user_activity_stats = user_activity_stats[:10]  # 取前10个
        
        # 转换用户活动数据
        user_activities = []
        max_views = user_activity_stats[0].documentViews if user_activity_stats else 1
        
        for user_stat in user_activity_stats:
            if user_stat.documentViews > 0 or user_stat.documentDownloads > 0 or user_stat.assetViews > 0:
                # 获取用户访问的文档详情
                user_docs = db.query(
                    Document.id.label('documentId'),
                    Document.title.label('documentTitle'),
                    func.max(DocumentView.created_at).label('lastAccess'),
                    func.count(DocumentView.id).label('viewCount')
                ).join(
                    DocumentView, Document.id == DocumentView.document_id
                ).filter(
                    DocumentView.user_id == user_stat.userId
                ).group_by(Document.id, Document.title).order_by(
                    desc(func.count(DocumentView.id))
                ).limit(5).all()
                
                document_access = [
                    {
                        'documentId': doc.documentId,
                        'documentTitle': doc.documentTitle,
                        'lastAccess': doc.lastAccess.isoformat() if doc.lastAccess else None,
                        'viewCount': doc.viewCount,
                        'accessCount': doc.viewCount  # 为前端兼容性添加accessCount字段
                    }
                    for doc in user_docs
                ]
                
                # 获取用户查看的资产详情
                user_assets = db.query(
                    Asset.id.label('assetId'),
                    Asset.name.label('assetName'),
                    func.max(AssetView.created_at).label('lastAccess'),
                    func.count(AssetView.id).label('viewCount')
                ).join(
                    AssetView, Asset.id == AssetView.asset_id
                ).filter(
                    AssetView.user_id == user_stat.userId
                ).group_by(Asset.id, Asset.name).order_by(
                    desc(func.count(AssetView.id))
                ).limit(5).all()
                
                asset_access = [
                    {
                        'assetId': asset.assetId,
                        'assetName': asset.assetName,
                        'lastAccess': asset.lastAccess.isoformat() if asset.lastAccess else None,
                        'viewCount': asset.viewCount,
                        'accessCount': asset.viewCount  # 为前端兼容性添加accessCount字段
                    }
                    for asset in user_assets
                ]
                
                total_activity = user_stat.documentViews + user_stat.assetViews
                max_total_views = max_views + (user_activity_stats[0].assetViews if user_activity_stats else 0)
                
                user_activities.append({
                    'userId': user_stat.userId,
                    'username': user_stat.username,
                    'documentViews': user_stat.documentViews,
                    'assetViews': user_stat.assetViews,
                    'documentDownloads': user_stat.documentDownloads,
                    'totalActivity': int((total_activity / max_total_views) * 100) if max_total_views > 0 else 0,
                    'documentAccess': document_access,
                    'assetAccess': asset_access
                })
        
        # 搜索关键词排行榜 - 从 search_logs 表获取
        search_keywords_data = db.query(
            SearchLog.query.label('word'),
            func.count(SearchLog.id).label('count'),
            func.max(SearchLog.created_at).label('lastSearch')
        ).filter(
            SearchLog.query.isnot(None),
            SearchLog.query != ''
        ).group_by(SearchLog.query).order_by(
            desc(func.count(SearchLog.id))
        ).limit(20).all()
        
        search_keywords = [
            {
                'word': keyword.word,
                'count': keyword.count,
                'lastSearch': keyword.lastSearch.isoformat() if keyword.lastSearch else None
            }
            for keyword in search_keywords_data
        ]
        
        return {
            "totalDocuments": total_documents,
            "totalAssets": total_assets,
            "totalUsers": total_users,
            "documentViews": total_document_views,
            "assetViews": total_asset_views,
            "activeUsers": active_users_count,
            "userActivityStats": user_activities,
            "searchKeywords": search_keywords
        }
        
    except Exception as e:
        import traceback
        print(f"获取统计数据失败: {str(e)}")
        traceback.print_exc()
        return {
            "error": f"获取统计数据失败: {str(e)}",
            "totalDocuments": 0,
            "totalAssets": 0,
            "totalUsers": 0,
            "documentViews": 0,
            "assetViews": 0,
            "activeUsers": 0,
            "userActivityStats": [],
            "searchKeywords": []
        }