import apiService from './api'
import type { User, LoginRequest, LoginResponse, RegisterRequest } from '@/types/api'

class AuthService {
  // 用户登录
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // FastAPI OAuth2PasswordRequestForm 需要form-data格式
      const formData = new URLSearchParams()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)
      
      // 获取API基础URL
      const currentHost = window.location.hostname
      const currentProtocol = window.location.protocol
      let baseUrl = 'http://localhost:8002'
      
      if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        baseUrl = `${currentProtocol}//${currentHost}:8002`
      }
      
      // 使用formData发送请求
      const response = await fetch(`${baseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error('登录错误响应:', errorText)
        throw new Error(`登录失败: ${response.status} - ${response.statusText}`)
      }
      
      const data: LoginResponse = await response.json()
      
      // 保存token
      if (data.access_token) {
        apiService.setToken(data.access_token)
      }
      
      return data
    } catch (error: any) {
      console.error('登录失败:', error)
      throw new Error(error.message || '用户名或密码错误，请检查后重试')
    }
  }

  // 用户注册
  async register(userData: RegisterRequest): Promise<User> {
    return await apiService.post<User>('/auth/register', userData)
  }

  // 获取当前用户信息
  async getCurrentUser(): Promise<User> {
    return await apiService.get<User>('/auth/me')
  }

  // 测试token有效性
  async testToken(): Promise<User> {
    return await apiService.post<User>('/auth/test-token')
  }

  // 用户登出
  logout() {
    apiService.clearAuth()
  }

  // 修改密码
  async changePassword(passwordData: { current_password: string; new_password: string }): Promise<{ message: string }> {
    return await apiService.post<{ message: string }>('/auth/change-password', passwordData)
  }

  // 获取当前token
  getToken(): string | null {
    return apiService.getToken()
  }

  // 检查是否已登录
  isAuthenticated(): boolean {
    return !!apiService.getToken()
  }
}

export const authService = new AuthService()
export default authService