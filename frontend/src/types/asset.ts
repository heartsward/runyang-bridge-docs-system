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
  BILLING = 'billing'
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
  cpu?: string
  memory?: string
  storage?: string
  
  // 状态和管理信息
  status: AssetStatus
  department?: string
  
  // 业务信息
  service_name?: string
  application?: string
  purpose?: string
  
  // 维护信息
  purchase_date?: string
  warranty_expiry?: string
  last_maintenance?: string
  next_maintenance?: string
  
  // 备注和标签
  notes?: string
  tags?: string[]
  
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
  cpu?: string
  memory?: string
  storage?: string
  status?: AssetStatus
  department?: string
  service_name?: string
  application?: string
  purpose?: string
  purchase_date?: string
  warranty_expiry?: string
  last_maintenance?: string
  next_maintenance?: string
  notes?: string
  tags?: string[]
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
  port?: number
  network_location?: string
  username?: string
  password?: string
  ssh_key?: string
  location?: string
  rack_position?: string
  datacenter?: string
  os_version?: string
  cpu?: string
  memory?: string
  storage?: string
  status?: AssetStatus
  department?: string
  service_name?: string
  application?: string
  purpose?: string
  purchase_date?: string
  warranty_expiry?: string
  last_maintenance?: string
  next_maintenance?: string
  notes?: string
  tags?: string[]
  confidence_score?: number
}

export interface AssetSearchQuery {
  query?: string
  asset_type?: AssetType
  status?: AssetStatus
  ip_address?: string
  department?: string
  network_location?: string
  tags?: string[]
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