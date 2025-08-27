import apiService from './api'
import type { 
  Asset, 
  AssetCreate, 
  AssetUpdate, 
  AssetSearchQuery,
  AssetExtractRequest,
  AssetExtractResult,
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
    if (query.tags) {
      query.tags.forEach(tag => params.append('tags', tag))
    }
    
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

  // 从文档提取资产
  async extractAssetsFromDocument(request: AssetExtractRequest): Promise<AssetExtractResult> {
    const response = await apiService.post<AssetExtractResult>(`${this.baseURL}/extract`, request)
    return response
  }

  // 获取文档相关的资产
  async getAssetsByDocument(documentId: number): Promise<Asset[]> {
    const response = await apiService.get<Asset[]>(`${this.baseURL}/document/${documentId}`)
    return response
  }

  // 批量创建资产
  async bulkCreateAssets(assets: AssetCreate[]): Promise<Asset[]> {
    const response = await apiService.post<Asset[]>(`${this.baseURL}/bulk-create`, assets)
    return response
  }

  // 合并资产
  async mergeAssets(sourceIds: number[], targetId?: number): Promise<Asset> {
    const response = await apiService.post<Asset>(`${this.baseURL}/merge`, {
      source_ids: sourceIds,
      target_id: targetId,
      merge_strategy: 'smart'
    })
    return response
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

  // 获取网络位置显示名称
  getNetworkLocationName(location: string): string {
    const locationNames: Record<string, string> = {
      office: '办公网',
      monitoring: '监控网',
      billing: '收费网'
    }
    return locationNames[location] || location
  }

  // 获取网络位置颜色
  getNetworkLocationColor(location: string): 'success' | 'warning' | 'error' | 'default' | 'primary' | 'info' {
    const locationColors: Record<string, 'success' | 'warning' | 'error' | 'default' | 'primary' | 'info'> = {
      office: 'primary',
      monitoring: 'success', 
      billing: 'warning'
    }
    return locationColors[location] || 'default'
  }
}

export const assetService = new AssetService()