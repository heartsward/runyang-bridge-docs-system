# -*- coding: utf-8 -*-
"""
数据分析API端点 - 提供用户活动统计和搜索关键词统计
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from datetime import datetime, timedelta

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.document import Document, DocumentView, SearchLog, AssetView
from app.models.asset import Asset

router = APIRouter()


@router.get("/stats", summary="获取统计数据")
async def get_analytics_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取系统统计信息"""
    try:
        # 基础统计
        total_documents = db.query(Document).count()
        total_assets = db.query(Asset).count()
        total_users = db.query(User).count()
        
        # 文档访问统计
        total_document_views = db.query(DocumentView).count()
        
        # 资产查看统计
        total_asset_views = db.query(AssetView).count()
        
        # 搜索统计
        total_searches = db.query(SearchLog).count()
        
        # 用户活动统计 - 按用户排行
        user_activity_query = db.query(
            User.id.label('userId'),
            User.username,
            User.full_name,
            User.department,
            func.count(DocumentView.id).label('documentViews'),
            func.count(SearchLog.id).label('searches'),
            func.count(AssetView.id).label('assetViews'),
            func.max(func.greatest(
                func.coalesce(DocumentView.created_at, datetime(1970, 1, 1)),
                func.coalesce(SearchLog.created_at, datetime(1970, 1, 1)),
                func.coalesce(AssetView.created_at, datetime(1970, 1, 1))
            )).label('lastActivity')
        ).outerjoin(DocumentView, User.id == DocumentView.user_id) \
         .outerjoin(SearchLog, User.id == SearchLog.user_id) \
         .outerjoin(AssetView, User.id == AssetView.user_id) \
         .group_by(User.id, User.username, User.full_name, User.department) \
         .order_by(desc('documentViews'))
        
        user_activity_stats = []
        for row in user_activity_query.all():
            # 获取具体的文档访问详情
            doc_access = db.query(
                DocumentView.document_id,
                Document.title.label('documentTitle'),
                func.count(DocumentView.id).label('accessCount'),
                func.max(DocumentView.created_at).label('lastAccess')
            ).join(Document, DocumentView.document_id == Document.id) \
             .filter(DocumentView.user_id == row.userId) \
             .group_by(DocumentView.document_id, Document.title) \
             .order_by(desc('accessCount')) \
             .limit(10).all()
            
            # 获取资产访问详情
            asset_access = db.query(
                AssetView.asset_id,
                Asset.name.label('assetName'),
                func.count(AssetView.id).label('accessCount'),
                func.max(AssetView.created_at).label('lastAccess')
            ).join(Asset, AssetView.asset_id == Asset.id) \
             .filter(AssetView.user_id == row.userId) \
             .group_by(AssetView.asset_id, Asset.name) \
             .order_by(desc('accessCount')) \
             .limit(10).all()
            
            user_activity_stats.append({
                "userId": row.userId,
                "username": row.username or row.full_name or f"用户{row.userId}",
                "department": row.department or "未设置",
                "documentViews": row.documentViews or 0,
                "searches": row.searches or 0,
                "assetViews": row.assetViews or 0,
                "lastActivity": row.lastActivity.isoformat() if row.lastActivity else None,
                "documentAccess": [
                    {
                        "documentId": doc.document_id,
                        "documentTitle": doc.documentTitle,
                        "accessCount": doc.accessCount,
                        "lastAccess": doc.lastAccess.isoformat() if doc.lastAccess else None
                    } for doc in doc_access
                ],
                "assetAccess": [
                    {
                        "assetId": asset.asset_id,
                        "assetName": asset.assetName,
                        "accessCount": asset.accessCount,
                        "lastAccess": asset.lastAccess.isoformat() if asset.lastAccess else None
                    } for asset in asset_access
                ]
            })
        
        # 搜索关键词排行
        search_keywords_query = db.query(
            SearchLog.query.label('keyword'),
            func.count(SearchLog.id).label('count'),
            func.max(SearchLog.created_at).label('lastSearch')
        ).group_by(SearchLog.query) \
         .order_by(desc('count')) \
         .limit(20)
        
        search_keywords = [
            {
                "keyword": row.keyword,
                "count": row.count,
                "lastSearch": row.lastSearch.isoformat() if row.lastSearch else None
            }
            for row in search_keywords_query.all()
        ]
        
        return {
            "total_documents": total_documents,
            "total_assets": total_assets,
            "total_users": total_users,
            "total_document_views": total_document_views,
            "total_asset_views": total_asset_views,
            "total_searches": total_searches,
            "userActivityStats": user_activity_stats,
            "searchKeywords": search_keywords
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/user-activity", summary="获取用户活动统计")
async def get_user_activity_stats(
    limit: int = 20,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取用户活动统计详情"""
    try:
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 用户活动统计查询
        user_stats = db.query(
            User.id,
            User.username,
            User.full_name,
            User.department,
            func.count(func.distinct(DocumentView.document_id)).label('unique_docs'),
            func.count(DocumentView.id).label('doc_views'),
            func.count(SearchLog.id).label('searches'),
            func.count(AssetView.id).label('asset_views'),
            func.max(func.greatest(
                func.coalesce(DocumentView.created_at, start_date),
                func.coalesce(SearchLog.created_at, start_date),
                func.coalesce(AssetView.created_at, start_date)
            )).label('last_active')
        ).outerjoin(
            DocumentView, 
            and_(User.id == DocumentView.user_id, DocumentView.created_at >= start_date)
        ).outerjoin(
            SearchLog, 
            and_(User.id == SearchLog.user_id, SearchLog.created_at >= start_date)
        ).outerjoin(
            AssetView, 
            and_(User.id == AssetView.user_id, AssetView.created_at >= start_date)
        ).group_by(User.id, User.username, User.full_name, User.department) \
         .having(func.count(DocumentView.id) + func.count(SearchLog.id) + func.count(AssetView.id) > 0) \
         .order_by(desc('doc_views')) \
         .limit(limit)
        
        results = []
        for user in user_stats.all():
            results.append({
                "user_id": user.id,
                "username": user.username or user.full_name or f"用户{user.id}",
                "department": user.department or "未设置",
                "unique_documents": user.unique_docs,
                "document_views": user.doc_views,
                "searches": user.searches,
                "asset_views": user.asset_views,
                "last_active": user.last_active.isoformat() if user.last_active else None,
                "activity_score": (user.doc_views * 3 + user.searches * 2 + user.asset_views * 4)
            })
        
        return {
            "period_days": days,
            "total_users": len(results),
            "users": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户活动统计失败: {str(e)}")


@router.post("/record-view", summary="记录文档预览访问")
async def record_document_view(
    document_id: int,
    duration: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """记录文档预览访问统计"""
    try:
        # 检查文档是否存在
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 记录访问日志
        view_log = DocumentView(
            document_id=document_id,
            user_id=current_user.id if current_user else None,
            duration=duration
        )
        db.add(view_log)
        
        # 更新文档访问计数
        document.view_count = (document.view_count or 0) + 1
        
        db.commit()
        
        return {
            "message": "文档访问记录成功",
            "document_id": document_id,
            "view_count": document.view_count
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"记录文档访问失败: {str(e)}")


@router.post("/record-asset-view", summary="记录资产查看访问")
async def record_asset_view(
    asset_id: int,
    view_type: str = "details",  # "details" 或 "credentials"
    duration: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """记录资产查看访问统计"""
    try:
        # 检查资产是否存在
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail="资产不存在")
        
        # 记录访问日志
        view_log = AssetView(
            asset_id=asset_id,
            user_id=current_user.id if current_user else None,
            view_type=view_type,
            duration=duration
        )
        db.add(view_log)
        db.commit()
        
        return {
            "message": "资产访问记录成功",
            "asset_id": asset_id,
            "view_type": view_type
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"记录资产访问失败: {str(e)}")


@router.get("/ai-analysis", summary="获取AI分析建议")
async def get_ai_analysis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取基于真实数据的AI分析建议"""
    try:
        # 获取统计数据
        recent_days = 7
        end_date = datetime.now()
        start_date = end_date - timedelta(days=recent_days)
        
        # 热门搜索分析
        top_searches = db.query(
            SearchLog.query,
            func.count(SearchLog.id).label('count')
        ).filter(SearchLog.created_at >= start_date) \
         .group_by(SearchLog.query) \
         .order_by(desc('count')).limit(5).all()
        
        # 热门文档分析
        top_docs = db.query(
            Document.title,
            func.count(DocumentView.id).label('views')
        ).join(DocumentView) \
         .filter(DocumentView.created_at >= start_date) \
         .group_by(Document.id, Document.title) \
         .order_by(desc('views')).limit(5).all()
        
        # 活跃用户分析
        active_users = db.query(func.count(func.distinct(
            func.coalesce(DocumentView.user_id, SearchLog.user_id)
        ))).outerjoin(SearchLog, DocumentView.user_id == SearchLog.user_id) \
         .filter(DocumentView.created_at >= start_date).scalar()
        
        # 生成分析建议
        insights = []
        recommendations = []
        
        if top_searches:
            insights.append({
                "type": "search_trends",
                "title": "热门搜索趋势",
                "content": f"最近{recent_days}天内，'{top_searches[0].query}'是最热门的搜索关键词，被搜索了{top_searches[0].count}次。",
                "priority": "high" if top_searches[0].count > 10 else "medium"
            })
            
            recommendations.append({
                "type": "content_optimization",
                "title": "内容优化建议",
                "content": f"建议针对热门搜索关键词'{top_searches[0].query}'优化相关文档内容。",
                "action": "优化相关文档和标签"
            })
        
        if top_docs:
            insights.append({
                "type": "document_popularity",
                "title": "热门文档分析", 
                "content": f"'{top_docs[0].title}'是最受欢迎的文档，有{top_docs[0].views}次访问。",
                "priority": "medium"
            })
        
        if active_users:
            insights.append({
                "type": "user_engagement",
                "title": "用户活跃度",
                "content": f"最近{recent_days}天有{active_users}位用户活跃使用系统。",
                "priority": "low"
            })
            
            if active_users < 5:
                recommendations.append({
                    "type": "user_engagement",
                    "title": "提高用户参与度",
                    "content": "用户活跃度较低，建议加强系统推广和用户培训。",
                    "action": "组织培训和推广活动"
                })
        
        # 如果没有足够数据，提供默认建议
        if not insights:
            insights.append({
                "type": "system_health",
                "title": "系统运行正常",
                "content": "系统运行状态良好，数据收集正在进行中。",
                "priority": "low"
            })
            
            recommendations.append({
                "type": "data_collection",
                "title": "数据收集建议",
                "content": "建议鼓励用户更多使用系统功能以收集更多分析数据。",
                "action": "增加用户引导和使用提示"
            })
        
        return {
            "analysis_time": datetime.now().isoformat(),
            "period_days": recent_days,
            "insights": insights,
            "recommendations": recommendations,
            "performance_metrics": {
                "total_searches": len(top_searches),
                "active_users": active_users or 0,
                "popular_docs": len(top_docs)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI分析失败: {str(e)}")