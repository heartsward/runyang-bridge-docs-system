import apiService from './api'

export interface TaskStatus {
  task_id?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string
  created_at?: string
  completed_at?: string
  result?: any
}

export const taskService = {
  // 获取文档的内容提取状态
  async getDocumentExtractionStatus(documentId: number): Promise<TaskStatus | null> {
    try {
      const data = await apiService.get(`/tasks/document/${documentId}/extraction-status`)
      return data as TaskStatus
    } catch (error: any) {
      console.error('获取文档提取状态失败:', error)
      
      // 如果是404错误，返回null表示没有找到状态
      if (error.response?.status === 404) {
        console.warn(`文档 ${documentId} 不存在或没有提取任务`)
        return null
      }
      
      // 对于其他错误，返回null而不是抛出异常
      console.warn('API调用失败，返回null状态')
      return null
    }
  },

  // 重新提取文档内容
  async retryDocumentExtraction(documentId: number) {
    const response = await apiService.post(`/tasks/document/${documentId}/retry-extraction`)
    return response.data
  },

  // 获取任务状态
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await apiService.get(`/tasks/status/${taskId}`)
    return response.data
  }
}

export default taskService