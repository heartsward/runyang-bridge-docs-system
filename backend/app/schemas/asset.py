# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, validator
from app.models.asset import AssetStatus, AssetType, NetworkLocation


class AssetBase(BaseModel):
    """资产基础模型"""
    name: str = Field(..., description="设备名称")
    asset_type: str = Field(..., description="资产类型")
    device_model: Optional[str] = Field(None, description="设备型号")
    manufacturer: Optional[str] = Field(None, description="制造商")
    serial_number: Optional[str] = Field(None, description="序列号")
    
    # 网络信息
    ip_address: Optional[str] = Field(None, description="IP地址")
    mac_address: Optional[str] = Field(None, description="MAC地址")
    hostname: Optional[str] = Field(None, description="主机名")
    port: Optional[int] = Field(None, description="端口号")
    network_location: str = Field(NetworkLocation.OFFICE, description="所处网络")
    
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
    system_version: Optional[str] = Field(None, description="应用版本（原系统型号及版本）")
    middleware_version: Optional[str] = Field(None, description="中间件版本（32.7新增）")
    cpu: Optional[str] = Field(None, description="CPU信息")
    memory: Optional[str] = Field(None, description="内存信息")
    storage: Optional[str] = Field(None, description="存储信息")
    
    # 状态和管理信息
    status: str = Field("active", description="资产状态")
    department: Optional[str] = Field(None, description="所属部门")
    
    # 业务信息
    service_name: Optional[str] = Field(None, description="信息系统名称（原服务名称）")
    application: Optional[str] = Field(None, description="应用程序（32.7界面移除，列保留）")
    purpose: Optional[str] = Field(None, description="用途说明")
    
    # 运维责任（32.7新增）
    dev_company: Optional[str] = Field(None, description="开发单位")
    ops_company: Optional[str] = Field(None, description="运维单位")
    contact_person: Optional[str] = Field(None, description="联系人")
    contact_phone: Optional[str] = Field(None, description="联系电话")
    
    # 维护信息
    purchase_date: Optional[datetime] = Field(None, description="采购日期")
    commissioning_date: Optional[datetime] = Field(None, description="设备启用日期")
    warranty_expiry: Optional[datetime] = Field(None, description="保修到期日期")
    last_maintenance: Optional[datetime] = Field(None, description="上次维护时间")
    next_maintenance: Optional[datetime] = Field(None, description="下次维护时间")
    
    # 备注和标签
    notes: Optional[str] = Field(None, description="备注")
    tags: Optional[List[str]] = Field(None, description="标签")
    groups: Optional[List[str]] = Field(None, description="自定义分组")
    
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

    @validator('serial_number')
    def empty_serial_to_none(cls, v):
        # 32.6：serial_number 列有 UNIQUE 约束（防真实序列号重复）。
        # SQLite 允许多个 NULL 但只允许一个 ''——表单"未填"发空串会在第二条撞
        # IntegrityError（陈工实测 PUT /assets/87 500）。空串一律归一为 NULL。
        return v.strip() if isinstance(v, str) and v.strip() else None

    @validator('groups', pre=True)
    def parse_groups(cls, v):
        # 兼容三种输入：JSON 字符串（DB 列原值）、逗号分隔串、已是 list
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            if s.startswith('['):
                import json
                try:
                    parsed = json.loads(s)
                    return parsed if isinstance(parsed, list) else []
                except json.JSONDecodeError:
                    return []
            return [g.strip() for g in s.split(',') if g.strip()]
        return v


class AssetCreate(AssetBase):
    """创建资产模型"""
    pass


class AssetUpdate(BaseModel):
    """更新资产模型"""
    name: Optional[str] = None
    asset_type: Optional[str] = None
    device_model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    network_location: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key: Optional[str] = None
    location: Optional[str] = None
    rack_position: Optional[str] = None
    datacenter: Optional[str] = None
    os_version: Optional[str] = None
    system_version: Optional[str] = None
    middleware_version: Optional[str] = None  # 32.7
    cpu: Optional[str] = None
    memory: Optional[str] = None
    storage: Optional[str] = None
    status: Optional[str] = None
    department: Optional[str] = None
    service_name: Optional[str] = None
    application: Optional[str] = None
    purpose: Optional[str] = None
    # 32.7 运维责任
    dev_company: Optional[str] = None
    ops_company: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    purchase_date: Optional[datetime] = None
    commissioning_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    confidence_score: Optional[int] = None
    # 32.10：所有权转移（仅管理员生效，端点里校验）；普通用户传了会被拒绝
    creator_id: Optional[int] = None

    @validator('serial_number')
    def empty_serial_to_none(cls, v):
        # 32.6：同 AssetBase——PUT 也走这里，空串归一 NULL，防撞 UNIQUE
        return v.strip() if isinstance(v, str) and v.strip() else None


class Asset(AssetBase):
    """完整资产模型"""
    id: int
    is_merged: bool = False
    merged_from: Optional[List[int]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    creator_id: int
    # 32.4：分享状态（列表端点注入；True=至少分享给了一个用户）
    shared: Optional[bool] = None
    shared_count: Optional[int] = None
    # 32.11：所有人用户名（=creator 的用户名，列表/详情端点注入；仅前端管理员列展示）
    creator_username: Optional[str] = None
    # 32.12：creator 是否超管（前端据此把多个管理员账号聚合显示为"管理员"）
    creator_is_superuser: Optional[bool] = None

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
    
    @validator('created_at', 'updated_at', pre=True, always=True)
    def ensure_timezone_aware(cls, v):
        """确保时间戳有时区信息（数据库层已处理转换）"""
        if v is None:
            return v
        if isinstance(v, datetime):
            # 如果时间戳已经有时区信息，直接返回
            # BeijingDateTime 类型会自动处理时区转换
            return v
        return v
    
    @validator('purchase_date', 'commissioning_date', 'warranty_expiry', 'last_maintenance', 'next_maintenance', pre=True, always=True)
    def convert_maintenance_dates(cls, v):
        """维护日期时间转换为北京时间"""
        if v is None:
            return v
        if isinstance(v, datetime):
            # 北京时区
            beijing_tz = timezone(timedelta(hours=8))
            if v.tzinfo is None:
                # 无时区信息，假设为UTC时间
                v = v.replace(tzinfo=timezone.utc)
            # 转换为北京时间
            return v.astimezone(beijing_tz)
        return v


class AssetSearchQuery(BaseModel):
    """资产搜索查询模型"""
    query: Optional[str] = Field(None, description="搜索关键词")
    asset_type: Optional[str] = Field(None, description="资产类型")
    status: Optional[str] = Field(None, description="资产状态")
    ip_address: Optional[str] = Field(None, description="IP地址")
    department: Optional[str] = Field(None, description="部门")
    network_location: Optional[str] = Field(None, description="所处网络")
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


class AssetList(BaseModel):
    """资产列表响应模型"""
    items: List[Asset]
    total: int
    page: int
    per_page: int
    pages: int


class AssetSingleConfirmRequest(BaseModel):
    """单个资产确认请求模型"""
    asset_data: Dict[str, Any] = Field(..., description="资产数据")
    is_duplicate: bool = Field(False, description="是否为重复资产")
    existing_id: Optional[int] = Field(None, description="现有资产ID（用于更新）")


class AssetStatistics(BaseModel):
    """资产统计模型"""
    total_count: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_network_location: Dict[str, int]
    by_department: Dict[str, int]
    recent_additions: int  # 最近30天新增
    pending_maintenance: int  # 待维护数量