// AI服务配置相关接口
import api from './api'

export interface AIProvider {
  name: string
  display_name: string
  is_available: boolean
}

export interface AIStats {
  total_cost: number
  total_tokens: number
  request_count: number
  daily_costs: Record<string, number>
  by_provider: Record<string, number>
}

export interface AIProviderConfig {
  api_key: string
  api_url: string
  model: string
  [key: string]: any  // 支持其他字段，如group_id等
}

export interface AIConfig {
  default_provider: string
  enabled: boolean
  fallback_enabled: boolean
  cost_limit_enabled: boolean
  daily_cost_limit: number
  cache_enabled: boolean
  cache_ttl: number
  providers: {
    openai: AIProviderConfig
    anthropic: AIProviderConfig
    alibaba: AIProviderConfig
    zhipu: AIProviderConfig
    minimax: AIProviderConfig
    custom?: AIProviderConfig
  }
}

// 获取AI提供商列表
export const getAIProviders = async (): Promise<AIProvider[]> => {
  const response = await api.get<{success: boolean, providers: AIProvider[], default_provider: string}>('/assets/ai/providers')
  return response.providers || []
}

// 获取AI使用统计
export const getAIStats = async (): Promise<AIStats> => {
  const response = await api.get<{success: boolean, stats: AIStats}>('/assets/ai/stats')
  return response.stats || {
    total_cost: 0,
    total_tokens: 0,
    request_count: 0,
    daily_costs: {},
    by_provider: {}
  }
}

// 保存AI配置
export const saveAIConfig = async (config: Partial<AIConfig>): Promise<void> => {
  await api.post('/settings/ai-config', config)
}

// 获取AI配置
export const getAIConfig = async (): Promise<AIConfig> => {
  const response = await api.get<{success: boolean, config: AIConfig}>('/settings/ai-config')
  return response.config
}

// 测试AI连接
export const testAIConnection = async (provider: string, config?: {
  api_key: string
  api_url: string
  model: string
  group_id?: string
}): Promise<{success: boolean, message: string}> => {
  const response = await api.post<{success: boolean, message: string}>('/assets/ai/test', { 
    provider,
    config 
  })
  return response
}

// AI服务类
class AIService {
  private provider: string = 'openai'
  private enabled: boolean = true
  private fallbackEnabled: boolean = true
  private costLimitEnabled: boolean = false
  private dailyCostLimit: number = 10.0
  private cacheEnabled: boolean = true
  private cacheTTL: number = 3600

  // 获取当前配置
  getConfig() {
    return {
      provider: this.provider,
      enabled: this.enabled,
      fallbackEnabled: this.fallbackEnabled,
      costLimitEnabled: this.costLimitEnabled,
      dailyCostLimit: this.dailyCostLimit,
      cacheEnabled: this.cacheEnabled,
      cacheTTL: this.cacheTTL
    }
  }

  // 设置配置
  setConfig(config: Partial<{
    provider: string
    enabled: boolean
    fallbackEnabled: boolean
    costLimitEnabled: boolean
    dailyCostLimit: number
    cacheEnabled: boolean
    cacheTTL: number
  }>) {
    if (config.provider !== undefined) this.provider = config.provider
    if (config.enabled !== undefined) this.enabled = config.enabled
    if (config.fallbackEnabled !== undefined) this.fallbackEnabled = config.fallbackEnabled
    if (config.costLimitEnabled !== undefined) this.costLimitEnabled = config.costLimitEnabled
    if (config.dailyCostLimit !== undefined) this.dailyCostLimit = config.dailyCostLimit
    if (config.cacheEnabled !== undefined) this.cacheEnabled = config.cacheEnabled
    if (config.cacheTTL !== undefined) this.cacheTTL = config.cacheTTL
  }
}

// 导出AI服务实例
export const aiService = new AIService()
export default aiService
