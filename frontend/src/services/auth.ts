import apiService from './api'
import type { User, LoginRequest, LoginResponse, RegisterRequest } from '@/types/api'

class AuthService {
  // 用户登录
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // 发送JSON格式的登录请求
      const response = await fetch('http://localhost:8002/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: credentials.username,
          password: credentials.password
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || '用户名或密码错误')
      }
      
      const loginResult = await response.json()
      
      // 验证登录结果
      if (!loginResult || !loginResult.access_token) {
        throw new Error('登录失败，用户名或密码错误')
      }
      
      // 保存token
      apiService.setToken(loginResult.access_token)
      
      return {
        access_token: loginResult.access_token,
        token_type: loginResult.token_type || 'bearer'
      }
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