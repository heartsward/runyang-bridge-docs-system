# -*- coding: utf-8 -*-
import os
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.crud.asset import asset as asset_crud
from app.crud.document import document as document_crud
from app.models.user import User
from app.schemas.asset import (
    Asset, AssetCreate, AssetUpdate, AssetSearchQuery,
    AssetExtractRequest, AssetExtractResult, AssetMergeRequest,
    AssetStatistics
)
from app.services.asset_extractor import AssetExtractor

router = APIRouter()


# @router.get("/", response_model=List[Asset], summary="获取资产列表")
# def get_assets(
#     skip: int = Query(0, ge=0),
#     limit: int = Query(20, ge=1, le=100),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """获取资产列表"""
#     assets = asset_crud.get_multi(db=db, skip=skip, limit=limit)
#     return assets

# 此端点已移动到 assets_simple.py 以修复network_location序列化问题


@router.get("/search", response_model=List[Asset], summary="搜索资产")
def search_assets(
    query: AssetSearchQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """搜索资产"""
    assets = asset_crud.search(db=db, query=query)
    return assets


@router.get("/statistics", response_model=AssetStatistics, summary="获取资产统计")
def get_asset_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取资产统计信息"""
    stats = asset_crud.get_statistics(db=db)
    return AssetStatistics(**stats)


@router.get("/{asset_id}", response_model=Asset, summary="获取资产详情")
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取资产详情"""
    asset_obj = asset_crud.get(db=db, id=asset_id)
    if not asset_obj:
        raise HTTPException(status_code=404, detail="资产不存在")
    return asset_obj


@router.post("/", response_model=Asset, summary="创建资产")
def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新资产"""
    # 检查是否存在相似资产
    similar_assets = asset_crud.find_similar_assets(db=db, asset=asset_in)
    if similar_assets:
        similar_info = [
            {
                "id": a.id,
                "name": a.name,
                "ip_address": a.ip_address,
                "hostname": a.hostname
            }
            for a in similar_assets[:3]  # 只返回前3个相似资产
        ]
        raise HTTPException(
            status_code=409,
            detail={
                "message": "发现相似的资产，建议先检查是否重复",
                "similar_assets": similar_info
            }
        )
    
    asset_obj = asset_crud.create_with_merge_info(
        db=db, obj_in=asset_in, creator_id=current_user.id
    )
    return asset_obj


@router.put("/{asset_id}", response_model=Asset, summary="更新资产")
def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新资产信息"""
    asset_obj = asset_crud.get(db=db, id=asset_id)
    if not asset_obj:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    asset_obj = asset_crud.update(db=db, db_obj=asset_obj, obj_in=asset_in)
    return asset_obj


@router.delete("/{asset_id}", summary="删除资产")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除资产"""
    asset = asset_crud.get(db=db, id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="资产不存在")
    
    asset_crud.remove(db=db, id=asset_id)
    return {"message": "资产删除成功"}


@router.post("/extract", response_model=AssetExtractResult, summary="从文档提取资产")
def extract_assets_from_document(
    request: AssetExtractRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """从文档中提取设备资产信息"""
    # 获取文档
    document = document_crud.get(db=db, id=request.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    if not document_crud.file_path or not os.path.exists(document_crud.file_path):
        raise HTTPException(status_code=400, detail="文档文件不存在")
    
    try:
        # Temporary mock implementation for debugging
        from app.schemas.asset import AssetCreate
        from app.models.asset import AssetType, AssetStatus
        
        # Create a mock asset based on document name  
        from app.models.asset import NetworkLocation
        mock_asset_create = AssetCreate(
            name=f"从{document_crud.title}提取的设备",
            asset_type=AssetType.SERVER,
            device_model="Unknown",
            ip_address="192.168.1.100",
            hostname="extracted-device",
            network_location=NetworkLocation.OFFICE,
            username="admin",
            password="",
            department="IT部门",
            status=AssetStatus.ACTIVE,
            notes=f"从文档 {document_crud.title} 自动提取",
            source_file=document_crud.file_name
        )
        
        # Create the asset in database
        created_asset = asset_crud.create_with_merge_info(
            db=db,
            obj_in=mock_asset_create,
            creator_id=current_user.id
        )
        
        return AssetExtractResult(
            extracted_count=1,
            merged_count=0,
            assets=[created_asset],
            errors=[]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"提取资产信息时发生错误: {str(e)}"
        )


@router.post("/merge", response_model=Asset, summary="合并资产")
def merge_assets(
    request: AssetMergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """合并多个资产"""
    if len(request.source_ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要选择2个资产进行合并")
    
    # 获取源资产
    source_assets = []
    for asset_id in request.source_ids:
        asset = asset_crud.get(db=db, id=asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"资产 {asset_id} 不存在")
        source_assets.append(asset)
    
    # 合并资产数据
    extractor = AssetExtractor()
    asset_dicts = []
    for asset in source_assets:
        asset_dict = {
            'name': asset_crud.name,
            'asset_type': asset_crud.asset_type,
            'device_model': asset_crud.device_model,
            'ip_address': asset_crud.ip_address,
            'hostname': asset_crud.hostname,
            'network_location': asset_crud.network_location,
            'username': asset_crud.username,
            'password': asset_crud.password,
            'department': asset_crud.department,
            'location': asset_crud.location,
            'notes': asset_crud.notes,
            'confidence_score': asset_crud.confidence_score
        }
        asset_dicts.append(asset_dict)
    
    merged_data = extractor._merge_assets(asset_dicts)
    merged_asset_create = extractor.convert_to_asset_create(merged_data)
    
    # 创建合并后的资产
    merged_asset = asset_crud.merge_assets(
        db=db,
        source_ids=request.source_ids,
        target_asset=merged_asset_create,
        creator_id=current_user.id
    )
    
    return merged_asset


@router.get("/document/{document_id}", response_model=List[Asset], summary="获取文档相关的资产")
def get_assets_by_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取从指定文档提取的所有资产"""
    document = document_crud.get(db=db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    assets = asset_crud.get_by_document(db=db, document_id=document_id)
    return assets


@router.post("/bulk-create", response_model=List[Asset], summary="批量创建资产")
def bulk_create_assets(
    assets_in: List[AssetCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """批量创建资产"""
    if len(assets_in) > 1000:
        raise HTTPException(status_code=400, detail="单次最多创建1000个资产")
    
    assets = asset_crud.bulk_create(
        db=db, assets=assets_in, creator_id=current_user.id
    )
    return assets