# -*- coding: utf-8 -*-
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_active_user
from app.crud.asset import asset as asset_crud
from app.models.user import User
from app.schemas.asset import AssetExtractResult
from app.services.enhanced_asset_extractor import EnhancedAssetExtractor

router = APIRouter()

@router.post("/upload", response_model=AssetExtractResult, summary="从本地文件提取资产")
async def extract_assets_from_file(
    file: UploadFile = File(...),
    auto_merge: bool = Form(True),
    merge_threshold: int = Form(80),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """从本地文件中提取设备资产信息"""
    # 验证文件类型
    allowed_types = ['txt', 'csv', 'xlsx', 'xls', 'json', 'md']
    file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型。支持的类型: {', '.join(allowed_types)}"
        )
    
    # 限制文件大小 (10MB)
    max_size = 10 * 1024 * 1024
    if file.size and file.size > max_size:
        raise HTTPException(status_code=400, detail="文件大小不能超过10MB")
    
    try:
        # 读取文件内容
        file_content = await file.read()
        
        # 初始化增强版资产提取器
        extractor = EnhancedAssetExtractor()
        
        # 从文件中提取资产信息
        raw_assets = extractor.extract_from_file(
            file_path=file.filename,
            file_content=file_content,
            file_type=file_ext
        )
        
        if not raw_assets:
            return AssetExtractResult(
                extracted_count=0,
                merged_count=0,
                assets=[],
                errors=["未能从文件中提取到有效的资产信息"]
            )
        
        errors = []
        final_assets = []
        
        # 自动合并相似资产
        if auto_merge and len(raw_assets) > 1:
            merged_assets, merge_groups = extractor.merge_similar_assets(raw_assets, merge_threshold)
            merged_count = len(merge_groups)
        else:
            merged_assets = raw_assets
            merged_count = 0
        
        # 转换为AssetCreate对象并创建资产
        for i, asset_data in enumerate(merged_assets):
            try:
                # 设置数据来源
                asset_data['source_file'] = file.filename
                asset_data['notes'] = asset_data.get('notes', '') + f" [从文件 {file.filename} 提取]"
                
                # 转换为AssetCreate对象
                asset_create = extractor.convert_to_asset_create(asset_data)
                
                # 检查是否存在相似资产
                similar_assets = asset_crud.find_similar_assets(db=db, asset=asset_create, threshold=90)
                if similar_assets:
                    errors.append(f"资产 {asset_create.name} 与现有资产相似，已跳过创建")
                    continue
                
                # 创建资产
                created_asset = asset_crud.create_with_merge_info(
                    db=db,
                    obj_in=asset_create,
                    creator_id=current_user.id,
                    merged_from=asset_data.get('merged_from') if asset_data.get('is_merged') else None
                )
                
                final_assets.append(created_asset)
                
            except Exception as e:
                errors.append(f"创建资产时发生错误: {str(e)}")
                continue
        
        return AssetExtractResult(
            extracted_count=len(raw_assets),
            merged_count=merged_count,
            assets=final_assets,
            errors=errors
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理文件时发生错误: {str(e)}"
        )