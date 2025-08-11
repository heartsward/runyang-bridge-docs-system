import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import type { ApiError } from '@/types/api'

// API配置 - 动态检测服务器地址
function getApiBaseUrl(): string {
  // 1. 优先使用环境变量配置
  const envApiUrl = import.meta.env.VITE_API_BASE_URL
  if (envApiUrl) {
    return envApiUrl + '/api/v1'
  }
  
  // 2. 从当前访问地址自动推断API地址
  const currentHost = window.location.hostname
  const currentProtocol = window.location.protocol
  
  // 如果是通过IP访问，使用相同IP的8002端口
  if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
    return `${currentProtocol}//${currentHost}:8002/api/v1`
  }
  
  // 3. 默认localhost配置
  return 'http://localhost:8002/api/v1'
}

function getUnifiedBaseUrl(): string {
  const currentHost = window.location.hostname
  const currentProtocol = window.location.protocol
  
  if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
    return `${currentProtocol}//${currentHost}:8002`
  }
  
  return 'http://localhost:8002'
}

const API_BASE_URL = getApiBaseUrl()
const UNIFIED_BASE_URL = getUnifiedBaseUrl() // 统一API端点

console.log('API配置:', { API_BASE_URL, UNIFIED_BASE_URL })


class ApiService {
  private api: AxiosInstance
  private token: string | null = null

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 初始化时从localStorage获取token
    this.token = localStorage.getItem('access_token')
    if (this.token) {
      this.setAuthHeader()
    }

    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      (error) => {
        if (error.response?.status === 401) {
          // Token过期或无效，清除本地存储
          this.clearAuth()
          // 使用Vue Router进行导航，而不是直接操作location
          console.warn('Token已过期，需要重新登录')
        }
        
        // 保留原始error对象的response信息，便于前端处理
        const enhancedError = {
          ...error,
          message: error.response?.data?.detail || error.message || '请求失败',
          response: error.response
        }
        
        return Promise.reject(enhancedError)
      }
    )
  }

  // 设置认证头
  private setAuthHeader() {
    if (this.token) {
      this.api.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
    }
  }

  // 设置token
  setToken(token: string) {
    this.token = token
    localStorage.setItem('access_token', token)
    this.setAuthHeader()
  }

  // 清除认证信息
  clearAuth() {
    this.token = null
    localStorage.removeItem('access_token')
    delete this.api.defaults.headers.common['Authorization']
  }

  // 获取当前token
  getToken() {
    return this.token
  }

  // 基础请求方法
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.post<T>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.put<T>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.delete<T>(url, config)
    return response.data
  }

  // 文件上传方法
  async upload<T>(url: string, formData: FormData): Promise<T> {
    const response = await this.api.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // PUT请求发送form data
  async putForm<T>(url: string, formData: FormData): Promise<T> {
    const response = await this.api.put<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  }

  // 文件下载方法
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.api.get(url, {
      responseType: 'blob',
    })
    
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

}

export const apiService = new ApiService()
export default apiService