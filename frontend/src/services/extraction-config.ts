/**
 * 统一 AI 服务配置（阶段七精简版）
 */
import apiService from './api'

export interface ExtractionConfig {
  ai_service_enabled: boolean
  ai_service_provider: 'ollama' | 'openai'
  ai_service_url: string
  ai_service_model: string
  ai_service_api_key: string
  ai_service_timeout: number
  ai_fallback_to_local: boolean
  // 阶段十三：True=所有格式文档（docx/xlsx/txt 等）也尝试 AI 提取 md；False=仅 PDF+图片
  ai_all_formats_ai: boolean

  // 可选：阶段五的 PaddleOCR 兼容
  ai_ocr_enabled: boolean
  ai_ocr_service_url: string
}

export interface UpdateResult {
  success: boolean
  restart_required: boolean
  message: string
  saved_to?: string
}

export interface AiModelCheck {
  requested: string
  found: boolean
  available_models: string[]
  hint?: string
}

export interface TestResult {
  results: Record<string, {
    reachable: boolean
    status?: number
    error?: string
    endpoint?: string
    model?: AiModelCheck
  }>
}

export const extractionConfigService = {
  async getConfig(): Promise<ExtractionConfig> {
    return await apiService.get<ExtractionConfig>('/settings/extraction-config')
  },

  async updateConfig(cfg: ExtractionConfig): Promise<UpdateResult> {
    return await apiService.put<UpdateResult>('/settings/extraction-config', cfg)
  },

  async testConnection(cfg: ExtractionConfig): Promise<TestResult> {
    return await apiService.post<TestResult>('/settings/extraction-config/test', cfg)
  },
}

export default extractionConfigService