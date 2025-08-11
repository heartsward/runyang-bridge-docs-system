import apiService from './api'
import type { User, LoginRequest, LoginResponse, RegisterRequest } from '@/types/api'

class AuthService {
  // 用户登录
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      // 使用动态API服务进行登录
      const response = await apiService.post<LoginResponse>('/auth/login', {
        username: credentials.username,
        password: credentials.password
      })
      
      // 保存token
      if (response.access_token) {
        apiService.setToken(response.access_token)
      }
      
      return response
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