import apiService from './api'

interface UserSettings {
  search_mode: 'quick' | 'full'
}

interface UserSettingsUpdate {
  search_mode: 'quick' | 'full'
}

interface User {
  id: number
  username: string
  email: string
  full_name?: string
  department?: string
  position?: string
  phone?: string
  is_active: boolean
  is_superuser: boolean
  created_at?: string
  mcp_token?: string | null  // 32.2：普通用户 MCP 个人码；管理员为 null（用统一码）
  // 32.8：被分享条目计数（文档/资产分开）
  share_doc_count?: number
  share_asset_count?: number
}

interface UserCreate {
  username: string
  email: string
  password: string
  full_name?: string
  department?: string
  position?: string
  phone?: string
  is_superuser?: boolean
}

interface UserUpdate {
  username?: string
  email?: string
  full_name?: string
  department?: string
  position?: string
  phone?: string
  is_active?: boolean
  is_superuser?: boolean
  password?: string  // 添加密码字段支持
}

// MCP 验证码状态（32.2）
interface McpTokenStatus {
  mode: 'admin' | 'personal'
  token: string
  can_regenerate_personal: boolean
  note?: string
}

// AI配置相关接口
interface AIConfigData {
  default_provider: string
  enabled: boolean
  fallback_enabled: boolean
  cost_limit_enabled: boolean
  daily_cost_limit: number
  cache_enabled: boolean
  cache_ttl: number
}

export class SettingsService {
  /**
   * 获取用户设置
   */
  async getUserSettings(): Promise<UserSettings> {
    try {
      const response = await apiService.get('/settings/')
      console.log('设置API原始响应:', response)
      return response as UserSettings
    } catch (error) {
      console.error('设置API调用失败:', error)
      throw error
    }
  }

  /**
   * 更新用户设置
   */
  async updateUserSettings(settings: UserSettingsUpdate): Promise<UserSettings> {
    try {
      const response = await apiService.put('/settings/', settings)
      console.log('更新设置API响应:', response)
      return response as UserSettings
    } catch (error) {
      console.error('更新设置API调用失败:', error)
      throw error
    }
  }

  /**
   * 获取所有用户 - 仅管理员（使用直接API）
   */
  async getAllUsers(): Promise<User[]> {
    try {
      // 首先尝试原始API
      const response = await apiService.get('/settings/users')
      return response as User[]
    } catch (error) {
      console.log('原始API失败，使用直接API:', error)
      // 如果原始API失败，使用直接API
      const response = await apiService.get('/direct-users')
      return response as User[]
    }
  }

  /**
   * 创建新用户 - 仅管理员（使用直接API）
   */
  async createUser(userData: UserCreate): Promise<User> {
    try {
      // 首先尝试原始API
      const response = await apiService.post('/settings/users', userData)
      return response as User  // 32.2 修基线：原 as UserSettings 类型错
    } catch (error) {
      console.log('原始API失败，使用直接API:', error)
      // 如果原始API失败，使用直接API
      // 使用动态地址检测
      const currentHost = window.location.hostname
      const currentProtocol = window.location.protocol
      let baseUrl = 'http://localhost:8002'
      
      if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        baseUrl = `${currentProtocol}//${currentHost}:8002`
      }
      
      const response = await fetch(`${baseUrl}/direct-users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || '创建用户失败')
      }
      
      return await response.json()
    }
  }

  /**
   * 更新用户信息 - 仅管理员
   */
  async updateUser(userId: number, userData: UserUpdate): Promise<User> {
    // 32.2 修基线：补泛型（原无泛型返回 unknown）
    const response = await apiService.put<User>(`/settings/users/${userId}`, userData)
    return response
  }

  // ============ 32.2：MCP 验证码管理 ============

  /**
   * 查看我的 MCP 验证码状态（普通用户=个人码，管理员=统一码）
   */
  async getMyMcpToken(): Promise<McpTokenStatus> {
    return await apiService.get<McpTokenStatus>('/settings/mcp-token/me')
  }

  /**
   * 重新随机我的 MCP 个人码（普通用户）
   */
  async regenerateMyMcpToken(): Promise<{ message: string; token: string }> {
    return await apiService.post<{ message: string; token: string }>(
      '/settings/mcp-token/me/regenerate'
    )
  }

  /**
   * 查看管理员统一 MCP 码 - 仅管理员
   */
  async getAdminMcpToken(): Promise<{ token: string }> {
    return await apiService.get<{ token: string }>('/settings/mcp-token/admin')
  }

  /**
   * 重置管理员统一 MCP 码 - 仅管理员（所有管理员客户端需同步换码）
   */
  async regenerateAdminMcpToken(): Promise<{ message: string; token: string }> {
    return await apiService.post<{ message: string; token: string }>(
      '/settings/mcp-token/admin/regenerate'
    )
  }

  /**
   * 重置指定普通用户的 MCP 码 - 仅管理员（泄露应急）
   */
  async regenerateUserMcpToken(userId: number): Promise<{ message: string; token: string }> {
    return await apiService.post<{ message: string; token: string }>(
      `/settings/mcp-token/users/${userId}/regenerate`
    )
  }

  /**
   * 删除用户 - 仅管理员（使用直接API）
   */
  async deleteUser(userId: number): Promise<{ message: string; shares_cancelled?: number }> {
    try {
      // 首先尝试原始API
      const response = await apiService.delete(`/settings/users/${userId}`)
      return response as unknown as { message: string; shares_cancelled?: number }  // 32.2 修基线：原 as UserSettings 类型错
    } catch (error) {
      console.log('原始API失败，使用直接API:', error)
      // 如果原始API失败，使用直接API
      // 使用动态地址检测
      const currentHost = window.location.hostname
      const currentProtocol = window.location.protocol
      let baseUrl = 'http://localhost:8002'
      
      if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        baseUrl = `${currentProtocol}//${currentHost}:8002`
      }
      
      const response = await fetch(`${baseUrl}/direct-users/${userId}`, {
        method: 'DELETE'
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || '删除用户失败')
      }
      
      return await response.json()
    }
  }

  /**
   * 32.8：一键取消分享给该用户的全部条目（文档/资产分开传 item_type，不传=全部）
   */
  async cancelUserShares(userId: number, itemType?: 'document' | 'asset'): Promise<{ message: string; cancelled: number }> {
    const response = await apiService.delete<{ message: string; cancelled: number }>(
      `/settings/users/${userId}/shares`,
      { params: itemType ? { item_type: itemType } : {} }
    )
    return response
  }

  /**
   * 获取AI配置
   */
  async getAIConfig(): Promise<AIConfigData> {
    try {
      const response = await apiService.get('/settings/ai-config')
      return response as AIConfigData
    } catch (error) {
      console.error('获取AI配置失败:', error)
      // 返回默认配置
      return {
        default_provider: 'openai',
        enabled: true,
        fallback_enabled: true,
        cost_limit_enabled: false,
        daily_cost_limit: 10.0,
        cache_enabled: true,
        cache_ttl: 3600
      }
    }
  }

  /**
   * 保存AI配置
   */
  async saveAIConfig(config: Partial<AIConfigData>): Promise<void> {
    try {
      await apiService.post('/settings/ai-config', config)
    } catch (error) {
      console.error('保存AI配置失败:', error)
      throw error
    }
  }
}

export const settingsService = new SettingsService()
export default settingsService

// Export interfaces for use in components
export type { UserSettings, UserSettingsUpdate, User, UserCreate, UserUpdate, McpTokenStatus, AIConfigData }