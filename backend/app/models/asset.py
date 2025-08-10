# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class AssetStatus(str, enum.Enum):
    """资产状态枚举"""
    ACTIVE = "active"          # 在用
    INACTIVE = "inactive"      # 停用
    MAINTENANCE = "maintenance"  # 维护中
    RETIRED = "retired"        # 已退役


class AssetType(str, enum.Enum):
    """资产类型枚举"""
    SERVER = "server"          # 服务器
    NETWORK = "network"        # 网络设备
    STORAGE = "storage"        # 存储设备
    SECURITY = "security"      # 安全设备
    DATABASE = "database"      # 数据库
    APPLICATION = "application"  # 应用程序
    OTHER = "other"           # 其他


class NetworkLocation(str, enum.Enum):
    """网络位置枚举"""
    OFFICE = "office"          # 办公网
    MONITORING = "monitoring"  # 监控网
    BILLING = "billing"        # 收费网


class Asset(Base):
    """设备资产模型"""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    
    # 基本信息
    name = Column(String(255), nullable=False, index=True, comment="设备名称")
    asset_type = Column(Enum(AssetType), nullable=False, comment="资产类型")
    device_model = Column(String(255), comment="设备型号")
    manufacturer = Column(String(255), comment="制造商")
    serial_number = Column(String(255), unique=True, index=True, comment="序列号")
    
    # 网络信息
    ip_address = Column(String(45), index=True, comment="IP地址")
    mac_address = Column(String(17), comment="MAC地址")
    hostname = Column(String(255), comment="主机名")
    port = Column(Integer, comment="端口号")
    network_location = Column(Enum(NetworkLocation, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=NetworkLocation.OFFICE, comment="所处网络")
    
    # 认证信息
    username = Column(String(255), comment="用户名")
    password = Column(Text, comment="密码(加密存储)")
    ssh_key = Column(Text, comment="SSH密钥")
    
    # 位置和环境信息
    location = Column(String(255), comment="物理位置")
    rack_position = Column(String(50), comment="机柜位置")
    datacenter = Column(String(255), comment="数据中心")
    
    # 配置信息
    os_version = Column(String(255), comment="操作系统版本")
    cpu = Column(String(255), comment="CPU信息")
    memory = Column(String(255), comment="内存信息")
    storage = Column(String(255), comment="存储信息")
    
    # 状态和管理信息
    status = Column(Enum(AssetStatus), default=AssetStatus.ACTIVE, comment="资产状态")
    department = Column(String(255), comment="所属部门")
    
    # 业务信息
    service_name = Column(String(255), comment="服务名称")
    application = Column(String(255), comment="应用程序")
    purpose = Column(Text, comment="用途说明")
    
    # 维护信息
    purchase_date = Column(DateTime, comment="采购日期")
    warranty_expiry = Column(DateTime, comment="保修到期日期")
    last_maintenance = Column(DateTime, comment="上次维护时间")
    next_maintenance = Column(DateTime, comment="下次维护时间")
    
    # 备注和标签
    notes = Column(Text, comment="备注")
    tags = Column(Text, comment="标签(JSON格式)")
    
    # 数据来源
    source_file = Column(String(255), comment="数据来源文件")
    source_document_id = Column(Integer, ForeignKey("documents.id"), comment="来源文档ID")
    
    # 自动合并信息
    is_merged = Column(Boolean, default=False, comment="是否为合并后的记录")
    merged_from = Column(Text, comment="合并来源ID列表(JSON格式)")
    confidence_score = Column(Integer, default=100, comment="数据置信度(0-100)")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    
    # 关系 - 移除back_populates避免循环引用
    creator = relationship("User")
    source_document = relationship("Document")


class AssetExtractRule(Base):
    """资产提取规则模型"""
    __tablename__ = "asset_extract_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    
    # 文件类型匹配
    file_patterns = Column(Text, comment="文件名模式(JSON格式)")
    file_types = Column(Text, comment="支持的文件类型(JSON格式)")
    
    # 字段映射规则
    field_mappings = Column(Text, comment="字段映射规则(JSON格式)")
    extraction_patterns = Column(Text, comment="提取正则表达式(JSON格式)")
    
    # 合并规则
    merge_keys = Column(Text, comment="合并关键字段(JSON格式)")
    merge_threshold = Column(Integer, default=80, comment="合并相似度阈值")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=0, comment="优先级")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建者ID")
    
    # 关系
    creator = relationship("User")