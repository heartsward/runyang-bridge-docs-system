// 设备资产相关类型定义

export enum AssetStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive', 
  MAINTENANCE = 'maintenance',
  RETIRED = 'retired'
}

export enum AssetType {
  SERVER = 'server',
  NETWORK = 'network',
  STORAGE = 'storage',
  SECURITY = 'security',
  DATABASE = 'database',
  APPLICATION = 'application',
  OTHER = 'other'
}

export enum NetworkLocation {
  OFFICE = 'office',
  MONITORING = 'monitoring',
  BILLING = 'billing',
  OTHER = 'other'
}

export interface Asset {
  id: number
  name: string
  asset_type: AssetType
  device_model?: string
  manufacturer?: string
  serial_number?: string
  
  // 网络信息
  ip_address?: string
  mac_address?: string
  hostname?: string
  port?: number
  network_location: string
  
  // 认证信息
  username?: string
  password?: string
  ssh_key?: string
  
  // 位置和环境信息
  location?: string
  rack_position?: string
  datacenter?: string
  
  // 配置信息
  os_version?: string
  system_version?: string  // 32.7：界面显示为「应用版本」（原系统型号及版本）
  middleware_version?: string  // 32.7 新增：中间件版本
  cpu?: string
  memory?: string
  storage?: string
  
  // 状态和管理信息
  status: AssetStatus
  department?: string
  
  // 业务信息
  service_name?: string  // 32.7：界面显示为「信息系统名称」（原服务名称）
  application?: string   // 32.7：界面移除，数据列保留
  purpose?: string
  
  // 运维责任（32.7 新增）
  dev_company?: string
  ops_company?: string
  contact_person?: string
  contact_phone?: string
  
  // 维护信息
  purchase_date?: string
  commissioning_date?: string
  warranty_expiry?: string
  last_maintenance?: string
  next_maintenance?: string
  
  // 备注和标签
  notes?: string
  tags?: string[]
  groups?: string[]
  
  // 数据来源
  source_file?: string
  source_document_id?: number
  
  // 自动合并信息
  is_merged: boolean
  merged_from?: number[]
  confidence_score: number
  
  // 时间戳
  created_at: string
  updated_at?: string
  creator_id: number

  // 32.4：分享状态（列表注入）
  shared?: boolean | null
  shared_count?: number | null
  // 32.11：所有人用户名（=creator 用户名；后端仅对管理员注入）
  creator_username?: string | null
  // 32.12：creator 是否超管（前端把多管理员聚合显示"管理员"）
  creator_is_superuser?: boolean | null
}

export interface AssetCreate {
  name: string
  asset_type: AssetType
  device_model?: string
  manufacturer?: string
  serial_number?: string
  ip_address?: string
  mac_address?: string
  hostname?: string
  port?: number
  network_location: string
  username?: string
  password?: string
  ssh_key?: string
  location?: string
  rack_position?: string
  datacenter?: string
  os_version?: string
  system_version?: string
  middleware_version?: string  // 32.7
  cpu?: string
  memory?: string
  storage?: string
  status?: AssetStatus
  department?: string
  service_name?: string
  application?: string
  purpose?: string
  // 32.7 运维责任
  dev_company?: string
  ops_company?: string
  contact_person?: string
  contact_phone?: string
  purchase_date?: string
  commissioning_date?: string
  warranty_expiry?: string
  last_maintenance?: string
  next_maintenance?: string
  notes?: string
  tags?: string[]
  groups?: string[]
  // 32.10/32.11：所有权转移（仅管理员 PUT 生效）
  creator_id?: number
  source_file?: string
  source_document_id?: number
  confidence_score?: number
}

export interface AssetUpdate {
  name?: string
  asset_type?: AssetType
  device_model?: string
  manufacturer?: string
  serial_number?: string
  ip_address?: string
  mac_address?: string
  hostname?: string
  port?: number | null   // 32.5：null=显式清空
  network_location?: string
  username?: string
  password?: string
  ssh_key?: string
  location?: string
  rack_position?: string
  datacenter?: string
  os_version?: string
  system_version?: string
  middleware_version?: string  // 32.7
  cpu?: string
  memory?: string
  storage?: string
  status?: AssetStatus
  department?: string
  service_name?: string
  application?: string
  purpose?: string
  // 32.7 运维责任
  dev_company?: string
  ops_company?: string
  contact_person?: string
  contact_phone?: string
  purchase_date?: string | null   // 32.5：null=显式清空该日期
  commissioning_date?: string | null
  warranty_expiry?: string | null
  last_maintenance?: string | null
  next_maintenance?: string | null
  notes?: string
  tags?: string[]
  groups?: string[]
  confidence_score?: number
  // 32.10/32.11：所有权转移（仅管理员 PUT 生效）
  creator_id?: number
}

export interface AssetSearchQuery {
  query?: string
  asset_type?: AssetType
  status?: AssetStatus
  ip_address?: string
  department?: string
  network_location?: string
  group?: string
  tags?: string[]
  share_filter?: 'shared' | 'unshared'  // 32.4：分享状态筛选
  owner?: string  // 32.12：所有人筛选（'管理员' 或用户名，仅管理员）
  sort_by?: string
  sort_order?: 'asc' | 'desc'
  page?: number
  per_page?: number
}

export interface AssetExtractRequest {
  document_id: number
  auto_merge?: boolean
  merge_threshold?: number
}

export interface AssetExtractResult {
  extracted_count: number
  merged_count: number
  assets: Asset[]
  errors: string[]
}

export interface AssetStatistics {
  total_count: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  by_environment: Record<string, number>
  by_department: Record<string, number>
  recent_additions: number
  pending_maintenance: number
}