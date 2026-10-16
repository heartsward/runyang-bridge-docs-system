import apiService from './api'
import type {
  Asset,
  AssetCreate,
  AssetUpdate,
  AssetSearchQuery,
  AssetStatistics
} from '@/types/asset'
import { NetworkLocation } from '@/types/asset'

export class AssetService {
  private baseURL = '/assets'

  // 获取资产列表
  async getAllAssets(): Promise<Asset[]> {
    const response = await apiService.get<{items: Asset[], total: number}>(`/assets/`)
    return response.items
  }

  // 搜索资产
  async searchAssets(query: AssetSearchQuery): Promise<Asset[]> {
    const params = new URLSearchParams()
    
    if (query.query) params.append('search', query.query)
    if (query.asset_type) params.append('asset_type', query.asset_type)
    if (query.status) params.append('status', query.status)
    if (query.ip_address) params.append('ip_address', query.ip_address)
    if (query.department) params.append('department', query.department)
    if (query.network_location) params.append('network_location', query.network_location)
    if (query.group) params.append('group', query.group)
    if (query.tags) {
      query.tags.forEach(tag => params.append('tags', tag))
    }
    // 添加排序参数
    if (query.sort_by) params.append('sort_by', query.sort_by)
    if (query.sort_order) params.append('sort_order', query.sort_order)
    
    const response = await apiService.get<{items: Asset[], total: number}>(`/assets/?${params.toString()}`)
    return response.items || []
  }

  // 获取资产统计
  async getStatistics(): Promise<AssetStatistics> {
    const response = await apiService.get<AssetStatistics>(`/assets/statistics`)
    return response
  }

  // 获取资产详情
  async getAsset(id: number): Promise<Asset> {
    const response = await apiService.get<Asset>(`/assets/${id}`)
    return response
  }

  // 创建资产
  async createAsset(asset: AssetCreate): Promise<Asset> {
    const response = await apiService.post<Asset>(this.baseURL, asset)
    return response
  }

  // 更新资产
  async updateAsset(id: number, asset: AssetUpdate): Promise<Asset> {
    const response = await apiService.put<Asset>(`/assets/${id}`, asset)
    return response
  }

  // 删除资产
  async deleteAsset(id: number): Promise<void> {
    await apiService.delete(`${this.baseURL}/${id}`)
  }

  // 获取资产类型显示名称
  getAssetTypeName(type: string): string {
    const typeNames: Record<string, string> = {
      server: '服务器',
      network: '网络设备', 
      storage: '存储设备',
      security: '安全设备',
      database: '数据库',
      application: '应用程序',
      other: '其他'
    }
    return typeNames[type] || type
  }

  // 获取资产状态显示名称
  getAssetStatusName(status: string): string {
    const statusNames: Record<string, string> = {
      active: '在用',
      inactive: '停用',
      maintenance: '维护中',
      retired: '已退役'
    }
    return statusNames[status] || status
  }

  // 获取资产状态颜色
  getAssetStatusColor(status: string): 'success' | 'warning' | 'error' | 'default' {
    const statusColors: Record<string, 'success' | 'warning' | 'error' | 'default'> = {
      active: 'success',
      inactive: 'default',
      maintenance: 'warning',
      retired: 'error'
    }
    return statusColors[status] || 'default'
  }

  // 获取资产类型图标
  getAssetTypeIcon(type: string): string {
    const typeIcons: Record<string, string> = {
      server: '🖥️',
      network: '🌐',
      storage: '💾',
      security: '🛡️',
      database: '🗜️',
      application: '📱',
      other: '📦'
    }
    return typeIcons[type] || '📦'
  }

  // 获取资产类型颜色（30.2：与"所处网络"一致的彩色标签）
  getAssetTypeColor(type: string): 'success' | 'warning' | 'error' | 'info' | 'primary' | 'default' {
    const typeColors: Record<string, 'success' | 'warning' | 'error' | 'info' | 'primary' | 'default'> = {
      server: 'primary',      // 服务器 - 蓝
      network: 'info',        // 网络设备 - 浅蓝
      storage: 'warning',     // 存储设备 - 橙
      security: 'error',      // 安全设备 - 红
      database: 'success',    // 数据库 - 绿
      application: 'default', // 应用程序
      other: 'default'        // 其他
    }
    return typeColors[type] || 'default'
  }

  // 获取部门配色（30.2：部门是自由文本，用 hash 稳定映射到调色板——
  // 同一部门在任何设备行/详情里颜色一致，不同部门颜色区分）
  getDepartmentColor(dept: string): { color: string; borderColor: string; textColor: string } {
    const palette = [
      '#2080f0', '#18a058', '#f0a020', '#d03050', '#7c3aed',
      '#0891b2', '#c2410c', '#4f46e5', '#059669', '#be185d',
    ]
    let hash = 0
    for (let i = 0; i < dept.length; i++) {
      hash = (hash * 31 + dept.charCodeAt(i)) >>> 0
    }
    const fg = palette[hash % palette.length]
    // 浅底（hex+透明度后缀）+ 同色系文字，观感与 naive-ui tag 一致
    return { color: fg + '1f', borderColor: fg + '55', textColor: fg }
  }

  // 获取网络位置显示名称
  getNetworkLocationName(location: string): string {
    const locationNames: Record<string, string> = {
      office: '办公网',
      monitoring: '监控网',
      billing: '收费网',
      other: '其它网络'
    }
    return locationNames[location] || location
  }

  // 获取网络位置颜色
  getNetworkLocationColor(location: string): 'success' | 'warning' | 'error' | 'default' | 'primary' | 'info' {
    const locationColors: Record<string, 'success' | 'warning' | 'error' | 'default' | 'primary' | 'info'> = {
      office: 'success',    // 办公网 - 绿色
      monitoring: 'warning', // 监控网 - 橙色
      billing: 'error',     // 收费网 - 红色
      other: 'info'         // 其它网络 - 蓝色
    }
    return locationColors[location] || 'default'
  }
}

export const assetService = new AssetService()