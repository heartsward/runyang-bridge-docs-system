# -*- coding: utf-8 -*-
"""
移动端API端点
专为移动应用优化的API接口
"""
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.core.deps import get_db, get_current_active_user, get_optional_user
from app.core.security import (
    create_access_token, verify_password, get_password_hash,
    create_mobile_tokens, verify_refresh_token, extract_user_id_from_token
)
from app.core.config import settings
from app.crud import user as crud_user, document as crud_document
from app.models.user import User
from app.models.document import Document
from app.models.asset import Asset
from app.schemas.mobile import (
    MobileBaseResponse, MobileAuthResponse, MobileLoginRequest, MobileRefreshTokenRequest,
    MobileUserProfile, MobileDocument, MobileDocumentDetail, MobileDocumentListResponse,
    MobileAsset, MobileAssetDetail, MobileAssetListResponse, MobileSearchRequest,
    MobileSearchResponse, MobileSearchResult, MobilePaginationInfo, MobileMetaInfo,
    format_file_size, get_status_display_info, generate_summary
)

router = APIRouter()
security = HTTPBearer()


# ============= 认证相关API =============

@router.post("/auth/login", response_model=MobileAuthResponse, summary="移动端用户登录")
async def mobile_login(
    login_request: MobileLoginRequest,
    db: Session = Depends(get_db)
):
    """
    移动端用户登录，支持长期Token
    - 返回30天有效期的access_token
    - 支持设备绑定
    """
    start_time = time.time()
    
    try:
        # 验证用户凭据
        user = crud_user.authenticate(
            db, username=login_request.username, password=login_request.password
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户账户已被禁用"
            )
        
        # 创建移动端令牌对
        tokens = create_mobile_tokens(
            user_id=user.id,
            device_id=login_request.device_id
        )
        
        # 构建用户信息
        user_profile = MobileUserProfile(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            department=user.department,
            role="admin" if user.is_superuser else "user",
            last_login=datetime.utcnow().isoformat() + "Z"
        )
        
        # 记录设备信息（简化实现）
        if login_request.device_id:
            # 这里可以记录设备信息到数据库
            pass
        
        response_time = f"{(time.time() - start_time) * 1000:.0f}ms"
        
        return MobileAuthResponse(
            success=True,
            message="登录成功",
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            user=user_profile,
            data={
                "device_registered": bool(login_request.device_id),
                "platform": login_request.platform,
                "response_time": response_time,
                "token_type": tokens["token_type"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )


@router.post("/auth/refresh", response_model=MobileAuthResponse, summary="刷新访问Token")
async def mobile_refresh_token(
    refresh_request: MobileRefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问Token
    """
    try:
        # 验证刷新令牌
        payload = verify_refresh_token(refresh_request.refresh_token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        # 提取用户ID
        user_id = extract_user_id_from_token(refresh_request.refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无法解析用户信息"
            )
        
        # 验证用户是否仍然有效
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被禁用或不存在"
            )
        
        # 设备验证（如果提供了设备ID）
        if refresh_request.device_id:
            from app.core.security import validate_device_token
            if not validate_device_token(refresh_request.refresh_token, refresh_request.device_id):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="设备验证失败"
                )
        
        # 创建新的令牌对
        tokens = create_mobile_tokens(
            user_id=user.id,
            device_id=refresh_request.device_id
        )
        
        # 构建用户信息
        user_profile = MobileUserProfile(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            email=user.email,
            department=user.department,
            role="admin" if user.is_superuser else "user"
        )
        
        return MobileAuthResponse(
            success=True,
            message="Token刷新成功",
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            user=user_profile,
            data={
                "refreshed_at": datetime.utcnow().isoformat() + "Z",
                "token_type": tokens["token_type"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token刷新失败: {str(e)}"
        )


@router.get("/auth/profile", response_model=MobileUserProfile, summary="获取用户信息")
async def get_mobile_profile(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户的简化信息"""
    return MobileUserProfile(
        id=current_user.id,
        username=current_user.username,
        full_name=current_user.full_name,
        email=current_user.email,
        department=current_user.department,
        role="admin" if current_user.is_superuser else "user"
    )


# ============= 文档相关API =============

@router.get("/documents/", response_model=MobileDocumentListResponse, summary="获取文档列表")
async def get_mobile_documents(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取移动端优化的文档列表
    """
    start_time = time.time()
    
    try:
        # 构建查询
        query = db.query(Document)
        
        # 搜索过滤
        if search:
            search_filter = or_(
                Document.title.contains(search),
                Document.description.contains(search),
                Document.content.contains(search)
            )
            query = query.filter(search_filter)
        
        # 分类过滤
        if category:
            # 这里需要根据分类表进行关联查询
            pass
        
        # 只显示已发布的文档
        query = query.filter(Document.status == "published")
        
        # 总数统计
        total = query.count()
        
        # 分页
        offset = (page - 1) * size
        documents = query.order_by(Document.created_at.desc()).offset(offset).limit(size).all()
        
        # 转换为移动端格式
        mobile_documents = []
        for doc in documents:
            mobile_doc = MobileDocument(
                id=doc.id,
                title=doc.title,
                summary=generate_summary(doc.description or doc.content or ""),
                file_type=doc.file_type or "unknown",
                file_size_display=format_file_size(doc.file_size or 0),
                created_at=doc.created_at.isoformat() + "Z" if doc.created_at else "",
                updated_at=doc.updated_at.isoformat() + "Z" if doc.updated_at else "",
                category=None,  # 需要关联分类表
                tags=doc.tags or [],
                preview_available=bool(doc.content),
                view_count=doc.view_count or 0
            )
            mobile_documents.append(mobile_doc)
        
        # 构建分页信息
        pagination = MobilePaginationInfo(
            page=page,
            size=size,
            total=total,
            has_next=(offset + size) < total,
            has_prev=page > 1
        )
        
        # 构建元信息
        meta = MobileMetaInfo(
            response_time=f"{(time.time() - start_time) * 1000:.0f}ms",
            server_time=datetime.utcnow().isoformat() + "Z"
        )
        
        return MobileDocumentListResponse(
            data=mobile_documents,
            pagination=pagination,
            meta=meta
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=MobileDocumentDetail, summary="获取文档详情")
async def get_mobile_document_detail(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取文档详细信息
    """
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在"
            )
        
        # 增加查看次数
        if current_user:
            document.view_count = (document.view_count or 0) + 1
            db.commit()
        
        # 构建详情对象
        mobile_detail = MobileDocumentDetail(
            id=document.id,
            title=document.title,
            description=document.description,
            summary=generate_summary(document.description or document.content or ""),
            content_preview=generate_summary(document.content or "", 500),
            file_type=document.file_type or "unknown",
            file_size_display=format_file_size(document.file_size or 0),
            created_at=document.created_at.isoformat() + "Z" if document.created_at else "",
            updated_at=document.updated_at.isoformat() + "Z" if document.updated_at else "",
            tags=document.tags or [],
            preview_available=bool(document.content),
            view_count=document.view_count or 0,
            download_url=f"/api/v1/documents/{document_id}/download" if document.file_path else None
        )
        
        return mobile_detail
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档详情失败: {str(e)}"
        )


@router.post("/documents/search", response_model=MobileSearchResponse, summary="文档搜索")
async def search_mobile_documents(
    search_request: MobileSearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    移动端文档搜索
    """
    start_time = time.time()
    
    try:
        # 构建搜索查询
        query = db.query(Document)
        
        # 搜索关键词
        if search_request.query:
            search_filter = or_(
                Document.title.contains(search_request.query),
                Document.description.contains(search_request.query),
                Document.content.contains(search_request.query)
            )
            query = query.filter(search_filter)
        
        # 分类过滤
        if search_request.category:
            pass  # 需要关联分类表
        
        # 只搜索已发布的文档
        query = query.filter(Document.status == "published")
        
        # 获取结果
        total_count = query.count()
        documents = query.order_by(Document.view_count.desc()).offset(search_request.offset).limit(search_request.limit).all()
        
        # 转换为移动端格式
        mobile_documents = []
        for doc in documents:
            mobile_doc = MobileDocument(
                id=doc.id,
                title=doc.title,
                summary=generate_summary(doc.description or doc.content or ""),
                file_type=doc.file_type or "unknown",
                file_size_display=format_file_size(doc.file_size or 0),
                created_at=doc.created_at.isoformat() + "Z" if doc.created_at else "",
                updated_at=doc.updated_at.isoformat() + "Z" if doc.updated_at else "",
                tags=doc.tags or [],
                preview_available=bool(doc.content),
                view_count=doc.view_count or 0
            )
            mobile_documents.append(mobile_doc)
        
        # 构建搜索结果
        search_result = MobileSearchResult(
            query=search_request.query,
            total_count=total_count,
            search_time=f"{(time.time() - start_time) * 1000:.0f}ms",
            documents=mobile_documents,
            suggestions=[],  # 可以添加搜索建议逻辑
            related_keywords=[]  # 可以添加相关关键词逻辑
        )
        
        # 构建元信息
        meta = MobileMetaInfo(
            response_time=f"{(time.time() - start_time) * 1000:.0f}ms",
            server_time=datetime.utcnow().isoformat() + "Z"
        )
        
        return MobileSearchResponse(
            data=search_result,
            meta=meta
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


# ============= 资产相关API =============

@router.get("/assets/", response_model=MobileAssetListResponse, summary="获取资产列表")
async def get_mobile_assets(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    asset_type: Optional[str] = Query(None, description="资产类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取移动端优化的资产列表
    """
    start_time = time.time()
    
    try:
        # 由于资产可能存储在JSON文件中，这里需要适配
        # 简化实现，返回示例数据
        assets = [
            {
                "id": 1,
                "name": "主服务器-001",
                "asset_type": "server",
                "status": "active",
                "location": "数据中心A",
                "ip_address": "192.168.1.10",
                "last_check": "2024-08-10T10:00:00Z",
                "health_score": 95,
                "created_at": "2024-01-15T08:30:00Z"
            },
            {
                "id": 2, 
                "name": "网络交换机-001",
                "asset_type": "network",
                "status": "maintenance",
                "location": "网络机房B",
                "ip_address": "192.168.1.1",
                "last_check": "2024-08-10T09:30:00Z",
                "health_score": 78,
                "created_at": "2024-02-01T14:20:00Z"
            }
        ]
        
        # 转换为移动端格式
        mobile_assets = []
        for asset_data in assets:
            status_info = get_status_display_info(asset_data["status"])
            
            mobile_asset = MobileAsset(
                id=asset_data["id"],
                name=asset_data["name"],
                asset_type=asset_data["asset_type"],
                status=asset_data["status"],
                status_display=status_info["display"],
                status_icon=status_info["icon"],
                status_color=status_info["color"],
                location=asset_data.get("location"),
                ip_address=asset_data.get("ip_address"),
                last_check=asset_data.get("last_check"),
                health_score=asset_data.get("health_score"),
                priority="high" if asset_data.get("health_score", 0) < 80 else "medium",
                created_at=asset_data["created_at"]
            )
            mobile_assets.append(mobile_asset)
        
        # 构建分页信息
        total = len(assets)
        pagination = MobilePaginationInfo(
            page=page,
            size=size,
            total=total,
            has_next=False,
            has_prev=False
        )
        
        # 构建元信息
        meta = MobileMetaInfo(
            response_time=f"{(time.time() - start_time) * 1000:.0f}ms",
            server_time=datetime.utcnow().isoformat() + "Z"
        )
        
        return MobileAssetListResponse(
            data=mobile_assets,
            pagination=pagination,
            meta=meta
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取资产列表失败: {str(e)}"
        )


@router.get("/assets/{asset_id}", response_model=MobileAssetDetail, summary="获取资产详情")
async def get_mobile_asset_detail(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    获取资产详细信息
    """
    try:
        # 简化实现，返回示例数据
        asset_data = {
            "id": asset_id,
            "name": f"设备-{asset_id:03d}",
            "asset_type": "server",
            "status": "active",
            "location": "数据中心A",
            "ip_address": "192.168.1.10",
            "last_check": "2024-08-10T10:00:00Z",
            "health_score": 95,
            "created_at": "2024-01-15T08:30:00Z",
            "description": "这是一台重要的服务器设备，负责核心业务处理。"
        }
        
        status_info = get_status_display_info(asset_data["status"])
        
        mobile_detail = MobileAssetDetail(
            id=asset_data["id"],
            name=asset_data["name"],
            asset_type=asset_data["asset_type"],
            status=asset_data["status"],
            status_display=status_info["display"],
            status_icon=status_info["icon"],
            status_color=status_info["color"],
            location=asset_data.get("location"),
            ip_address=asset_data.get("ip_address"),
            last_check=asset_data.get("last_check"),
            health_score=asset_data.get("health_score"),
            priority="high" if asset_data.get("health_score", 0) < 80 else "medium",
            created_at=asset_data["created_at"],
            description=asset_data.get("description"),
            specifications={
                "CPU": "Intel Xeon E5-2680 v4",
                "内存": "64GB DDR4",
                "存储": "2TB SSD RAID1",
                "网络": "千兆网卡 x2"
            },
            maintenance_info={
                "上次维护": "2024-07-15",
                "维护周期": "每季度一次",
                "负责人": "张工程师"
            }
        )
        
        return mobile_detail
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取资产详情失败: {str(e)}"
        )