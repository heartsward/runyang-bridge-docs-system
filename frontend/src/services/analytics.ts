import api from './api'

export interface DocumentViewRecord {
  document_id: number
  duration?: number
}

export interface AssetViewRecord {
  asset_id: number
  view_type: 'details' | 'credentials'
  duration?: number
}

export interface UserActivityStats {
  userId: number
  username: string
  department: string
  documentViews: number
  searches: number
  assetViews: number
  lastActivity: string
  documentAccess?: any[]
  assetAccess?: any[]
}

export interface SearchKeyword {
  keyword: string
  count: number
  lastSearch: string
}

export interface AnalyticsStats {
  total_documents: number
  total_assets: number
  total_users: number
  total_document_views: number
  total_asset_views: number
  total_searches: number
  userActivityStats: UserActivityStats[]
  searchKeywords: SearchKeyword[]
}

class AnalyticsService {
  private baseURL = '/analytics'

  async getStats(): Promise<AnalyticsStats> {
    return await api.get(`${this.baseURL}/stats`)
  }

  async recordDocumentView(documentId: number, duration?: number): Promise<void> {
    try {
      await api.post(`${this.baseURL}/record-view`, {
        document_id: documentId,
        duration
      })
    } catch (error) {
      console.warn('记录文档访问失败:', error)
    }
  }

  async recordAssetView(assetId: number, viewType: 'details' | 'credentials' = 'details', duration?: number): Promise<void> {
    try {
      await api.post(`${this.baseURL}/record-asset-view`, {
        asset_id: assetId,
        view_type: viewType,
        duration
      })
    } catch (error) {
      console.warn('记录资产访问失败:', error)
    }
  }

  async getAIAnalysis(): Promise<any> {
    return await api.get(`${this.baseURL}/ai-analysis`)
  }

  async getUserActivity(limit = 20, days = 30): Promise<any> {
    return await api.get(`${this.baseURL}/user-activity`, {
      params: { limit, days }
    })
  }
}

export const analyticsService = new AnalyticsService()