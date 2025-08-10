import apiService from './api'
import type { 
  Document, 
  DocumentCreate, 
  DocumentUpdate,
  Category,
  CategoryCreate,
  SearchQuery,
  SearchResponse
} from '@/types/api'

class DocumentService {
  // 文档相关API
  
  // 获取文档列表
  async getDocuments(params?: {
    skip?: number
    limit?: number
    category_id?: number
    status?: string
  }): Promise<Document[]> {
    const queryParams = new URLSearchParams()
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    if (params?.category_id) queryParams.append('category_id', params.category_id.toString())
    if (params?.status) queryParams.append('status', params.status)
    
    const url = `/documents?${queryParams.toString()}`
    const response = await apiService.get<{items: Document[], total: number}>(url)
    return response.items || []
  }

  // 获取所有文档
  async getAllDocuments(): Promise<Document[]> {
    const response = await apiService.get<{items: Document[], total: number}>('/documents?limit=1000')
    return response.items || []
  }

  // 创建文档
  async createDocument(documentData: DocumentCreate): Promise<Document> {
    return await apiService.post<Document>('/documents/', documentData)
  }

  // 获取文档详情
  async getDocument(id: number): Promise<Document> {
    return await apiService.get<Document>(`/documents/${id}`)
  }

  // 更新文档
  async updateDocument(id: number, documentData: DocumentUpdate): Promise<Document> {
    // 后端期望form data格式，需要转换
    const formData = new FormData()
    formData.append('title', documentData.title || '')
    formData.append('description', documentData.description || '')
    
    // 处理tags - 后端期望逗号分隔的字符串
    if (documentData.tags && Array.isArray(documentData.tags)) {
      formData.append('tags', documentData.tags.join(','))
    } else {
      formData.append('tags', '')
    }
    
    // 使用putForm方法发送form data的PUT请求
    return await apiService.putForm<Document>(`/documents/${id}`, formData)
  }

  // 删除文档
  async deleteDocument(id: number): Promise<{ message: string }> {
    return await apiService.delete<{ message: string }>(`/documents/${id}`)
  }

  // 搜索文档
  async searchDocuments(query: string, params?: {
    skip?: number
    limit?: number
  }): Promise<Document[]> {
    const queryParams = new URLSearchParams()
    queryParams.append('q', query)  // 后端期望的是 'q' 参数
    if (params?.skip !== undefined) queryParams.append('offset', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    
    const url = `/search/documents?${queryParams.toString()}`
    const response = await apiService.get<{results: Document[], total: number}>(url)
    return response.results || []
  }

  // 获取热门文档
  async getPopularDocuments(limit: number = 10): Promise<Document[]> {
    return await apiService.get<Document[]>(`/documents/popular/?limit=${limit}`)
  }

  // 分类相关API
  
  // 获取分类列表
  async getCategories(params?: {
    skip?: number
    limit?: number
  }): Promise<Category[]> {
    const queryParams = new URLSearchParams()
    if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString())
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString())
    
    const url = `/documents/categories/?${queryParams.toString()}`
    return await apiService.get<Category[]>(url)
  }

  // 创建分类
  async createCategory(categoryData: CategoryCreate): Promise<Category> {
    return await apiService.post<Category>('/documents/categories/', categoryData)
  }

  // 更新分类
  async updateCategory(id: number, categoryData: Partial<CategoryCreate>): Promise<Category> {
    return await apiService.put<Category>(`/documents/categories/${id}`, categoryData)
  }

  // 删除分类
  async deleteCategory(id: number): Promise<{ message: string }> {
    return await apiService.delete<{ message: string }>(`/documents/categories/${id}`)
  }
}

export const documentService = new DocumentService()
export default documentService