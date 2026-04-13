# -*- coding: utf-8 -*-
"""
系统配置API端点
用于管理可自定义的系统选项，如设备类型、部门等
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.core.deps import get_db
from app.models.system_config import SystemConfig
from app.models.asset import Asset
from app.schemas.system_config import (
    SystemConfigCreate,
    SystemConfigUpdate,
    SystemConfigResponse,
    SystemOptionsResponse
)
from app.models.user import User
from app.core.deps import get_current_active_user
import json

router = APIRouter()

# 配置键名常量
ASSET_TYPES_KEY = "custom_asset_types"
DEPARTMENTS_KEY = "custom_departments"
NETWORK_LOCATIONS_KEY = "custom_network_locations"

# 默认设备类型
DEFAULT_ASSET_TYPES = [
    {"value": "server", "label": "服务器"},
    {"value": "network", "label": "网络设备"},
    {"value": "storage", "label": "存储设备"},
    {"value": "security", "label": "安全设备"},
    {"value": "database", "label": "数据库"},
    {"value": "application", "label": "应用程序"},
    {"value": "other", "label": "其他"}
]

# 默认网络位置
DEFAULT_NETWORK_LOCATIONS = [
    {"value": "office", "label": "办公网"},
    {"value": "monitoring", "label": "监控网"},
    {"value": "billing", "label": "收费网"},
    {"value": "other", "label": "其它网络"}
]


def get_system_config(db: Session, key: str) -> SystemConfig:
    """获取系统配置，如果不存在则创建"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        # 创建默认配置
        default_value = "[]"
        if key == ASSET_TYPES_KEY:
            default_value = json.dumps(DEFAULT_ASSET_TYPES, ensure_ascii=False)
        
        config = SystemConfig(
            key=key,
            value=default_value,
            description=f"{key} configuration"
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("/options", response_model=SystemOptionsResponse, summary="获取系统选项")
async def get_system_options(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取所有系统选项，包括设备类型和部门"""
    # 获取自定义设备类型
    asset_types_config = get_system_config(db, ASSET_TYPES_KEY)
    custom_asset_types = json.loads(asset_types_config.value) if asset_types_config.value else []
    
    # 获取自定义部门
    departments_config = get_system_config(db, DEPARTMENTS_KEY)
    custom_departments = json.loads(departments_config.value) if departments_config.value else []
    
    # 从现有资产中提取部门
    existing_departments = db.query(Asset.department).filter(
        Asset.department.isnot(None),
        Asset.department != ""
    ).distinct().all()
    existing_depts = [d[0] for d in existing_departments if d[0]]
    
    # 合并部门（去重）
    all_departments = list(set(custom_departments + existing_depts))
    
    return SystemOptionsResponse(
        asset_types=custom_asset_types,
        departments=sorted(all_departments)
    )


@router.get("/asset-types", response_model=List[Dict[str, str]], summary="获取设备类型列表")
async def get_asset_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取设备类型列表"""
    config = get_system_config(db, ASSET_TYPES_KEY)
    return json.loads(config.value) if config.value else []


@router.put("/asset-types", response_model=List[Dict[str, str]], summary="更新设备类型列表")
async def update_asset_types(
    asset_types: List[Dict[str, str]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新设备类型列表"""
    config = get_system_config(db, ASSET_TYPES_KEY)
    config.value = json.dumps(asset_types, ensure_ascii=False)
    db.commit()
    db.refresh(config)
    return json.loads(config.value)


@router.get("/departments", response_model=List[str], summary="获取部门列表")
async def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取部门列表"""
    # 获取自定义部门
    config = get_system_config(db, DEPARTMENTS_KEY)
    custom_departments = json.loads(config.value) if config.value else []
    
    # 从现有资产中提取部门
    existing_departments = db.query(Asset.department).filter(
        Asset.department.isnot(None),
        Asset.department != ""
    ).distinct().all()
    existing_depts = [d[0] for d in existing_departments if d[0]]
    
    # 合并部门（去重）
    all_departments = list(set(custom_departments + existing_depts))
    
    return sorted(all_departments)


@router.put("/departments", response_model=List[str], summary="更新部门列表")
async def update_departments(
    departments: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新部门列表"""
    config = get_system_config(db, DEPARTMENTS_KEY)
    config.value = json.dumps(departments, ensure_ascii=False)
    db.commit()
    db.refresh(config)
    return sorted(json.loads(config.value))


# 所处网络位置API
@router.get("/network-locations", response_model=List[Dict[str, str]], summary="获取所处网络列表")
async def get_network_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取所处网络列表"""
    config = get_system_config(db, NETWORK_LOCATIONS_KEY)
    return json.loads(config.value) if config.value else []


@router.put("/network-locations", response_model=List[Dict[str, str]], summary="更新所处网络列表")
async def update_network_locations(
    network_locations: List[Dict[str, str]],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新所处网络列表"""
    config = get_system_config(db, NETWORK_LOCATIONS_KEY)
    config.value = json.dumps(network_locations, ensure_ascii=False)
    db.commit()
    db.refresh(config)
    return json.loads(config.value)
