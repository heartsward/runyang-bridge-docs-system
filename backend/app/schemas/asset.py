# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.models.asset import AssetStatus, AssetType, NetworkLocation


class AssetBase(BaseModel):
    """资产基础模型"""
    name: str = Field(..., description="设备名称")
    asset_type: AssetType = Field(..., description="资产类型")
    device_model: Optional[str] = Field(None, description="设备型号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    serial_number: Optional[str] = Field(None, description="序列号")
    
    # 网络信息
    ip_address: Optional[str] = Field(None, description="IP地址")
    mac_address: Optional[str] = Field(None, description="MAC地址")
    hostname: Optional[str] = Field(None, description="主机名")
    port: Optional[int] = Field(None, description="端口号")
    network_location: NetworkLocation = Field(NetworkLocation.OFFICE, description="所处网络")
    
    # 认证信息
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    ssh_key: Optional[str] = Field(None, description="SSH密钥")
    
    # 位置和环境信息
    location: Optional[str] = Field(None, description="物理位置")
    rack_position: Optional[str] = Field(None, description="机柜位置")
    datacenter: Optional[str] = Field(None, description="数据中心")
    
    # 配置信息
    os_version: Optional[str] = Field(None, description="操作系统版本")
    cpu: Optional[str] = Field(None, description="CPU信息")
    memory: Optional[str] = Field(None, description="内存信息")
    storage: Optional[str] = Field(None, description="存储信息")
    
    # 状态和管理信息
    status: AssetStatus = Field(AssetStatus.ACTIVE, description="资产状态")
    department: Optional[str] = Field(None, description="所属部门")
    
    # 业务信息
    service_name: Optional[str] = Field(None, description="服务名称")
    application: Optional[str] = Field(None, description="应用程序")
    purpose: Optional[str] = Field(None, description="用途说明")
    
    # 维护信息
    purchase_date: Optional[datetime] = Field(None, description="采购日期")
    warranty_expiry: Optional[datetime] = Field(None, description="保修到期日期")
    last_maintenance: Optional[datetime] = Field(None, description="上次维护时间")
    next_maintenance: Optional[datetime] = Field(None, description="下次维护时间")
    
    # 备注和标签
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")
    
    # 数据来源
    source_file: Optional[str] = Field(None, description="数据来源文件")
    source_document_id: Optional[int] = Field(None, description="来源文档ID")
    
    # 自动合并信息
    confidence_score: int = Field(100, description="数据置信度(0-100)")

    @validator('tags', pre=True)
    def parse_tags(cls, v):
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v


class AssetCreate(AssetBase):
    """创建资产模型"""
    pass


class AssetUpdate(BaseModel):
    """更新资产模型"""
    name: Optional[str] = None
    asset_type: Optional[AssetType] = None
    device_model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    network_location: Optional[NetworkLocation] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    location: Optional[str] = None
    rack_position: Optional[str] = None
    datacenter: Optional[str] = None
    os_version: Optional[str] = None
    cpu: Optional[str] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    status: Optional[AssetStatus] = None
    department: Optional[str] = None
    service_name: Optional[str] = None
    application: Optional[str] = None
    purpose: Optional[str] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    confidence_score: Optional[int] = None


class Asset(AssetBase):
    """完整资产模型"""
    id: int
    is_merged: bool = False
    merged_from: Optional[List[int]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_id: int

    class Config:
        from_attributes = True

    @validator('merged_from', pre=True)
    def parse_merged_from(cls, v):
        if isinstance(v, str) and v:
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v


class AssetSearchQuery(BaseModel):
    """资产搜索查询模型"""
    query: Optional[str] = Field(None, description="搜索关键词")
    asset_type: Optional[AssetType] = Field(None, description="资产类型")
    status: Optional[AssetStatus] = Field(None, description="资产状态")
    ip_address: Optional[str] = Field(None, description="IP地址")
    department: Optional[str] = Field(None, description="部门")
    network_location: Optional[NetworkLocation] = Field(None, description="所处网络")
    tags: Optional[List[str]] = Field(None, description="标签")
    page: int = Field(1, ge=1, description="页码")
    per_page: int = Field(20, ge=1, le=100, description="每页数量")


class AssetExtractRequest(BaseModel):
    """资产提取请求模型"""
    document_id: int = Field(..., description="文档ID")
    auto_merge: bool = Field(True, description="是否自动合并相似设备")
    merge_threshold: int = Field(80, ge=0, le=100, description="合并相似度阈值")


class AssetExtractResult(BaseModel):
    """资产提取结果模型"""
    extracted_count: int = Field(..., description="提取到的资产数量")
    merged_count: int = Field(..., description="合并的资产数量")
    assets: List[Asset] = Field(..., description="提取的资产列表")
    errors: List[str] = Field(default_factory=list, description="提取过程中的错误")


class AssetMergeRequest(BaseModel):
    """资产合并请求模型"""
    source_ids: List[int] = Field(..., description="要合并的源资产ID列表")
    target_id: Optional[int] = Field(None, description="目标资产ID(如果不指定则创建新资产)")
    merge_strategy: str = Field("smart", description="合并策略: smart/newest/manual")


class AssetBulkImportRequest(BaseModel):
    """资产批量导入请求模型"""
    file_content: str = Field(..., description="文件内容(base64编码)")
    file_type: str = Field(..., description="文件类型: csv/xlsx/json")
    mapping: Dict[str, str] = Field(..., description="字段映射关系")
    auto_merge: bool = Field(True, description="是否自动合并")


class AssetStatistics(BaseModel):
    """资产统计模型"""
    total_count: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_network_location: Dict[str, int]
    by_department: Dict[str, int]
    recent_additions: int  # 最近30天新增
    pending_maintenance: int  # 待维护数量