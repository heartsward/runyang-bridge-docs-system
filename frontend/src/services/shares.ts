import apiService from './api'

// 32.1：分享（管理员→普通用户只读授权）
export interface ShareOut {
  id: number
  item_type: string
  item_id: number
  shared_by_id: number
  shared_with_id: number
  shared_with_username?: string
}

export class ShareService {
  // 创建分享（仅管理员）
  async share(itemType: 'document' | 'asset', itemId: number, userId: number): Promise<ShareOut> {
    return await apiService.post<ShareOut>('/shares/', {
      item_type: itemType,
      item_id: itemId,
      user_id: userId,
    })
  }

  // 撤销分享（仅管理员）
  async revoke(shareId: number): Promise<{ message: string }> {
    return await apiService.delete<{ message: string }>(`/shares/${shareId}`)
  }

  // 某条目已分享给哪些用户（仅管理员）
  async byItem(itemType: 'document' | 'asset', itemId: number): Promise<ShareOut[]> {
    return await apiService.get<ShareOut[]>('/shares/by-item', {
      params: { item_type: itemType, item_id: itemId },
    })
  }
}

export const shareService = new ShareService()
