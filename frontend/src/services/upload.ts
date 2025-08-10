import apiService from './api'
import type { Document } from '@/types/api'

export interface UploadFileData {
  file: File
  title: string
  description?: string
  category_id?: number
  tags?: string
}

class UploadService {
  // 单文件上传
  async uploadFile(data: UploadFileData): Promise<Document> {
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('title', data.title)
    
    if (data.description) {
      formData.append('description', data.description)
    }
    if (data.category_id) {
      formData.append('category_id', data.category_id.toString())
    }
    if (data.tags) {
      formData.append('tags', data.tags)
    }

    return await apiService.upload<Document>('/upload', formData)
  }

  // 多文件上传
  async uploadMultipleFiles(files: File[], options?: {
    category_id?: number
    description?: string
    tags?: string
  }): Promise<Document[]> {
    const formData = new FormData()
    
    files.forEach(file => {
      formData.append('files', file)
    })
    
    if (options?.category_id) {
      formData.append('category_id', options.category_id.toString())
    }
    
    if (options?.description) {
      formData.append('description', options.description)
    }
    
    if (options?.tags) {
      formData.append('tags', options.tags)
    }

    return await apiService.upload<Document[]>('/upload/upload-multiple', formData)
  }

  // 下载文件
  async downloadFile(documentId: number, filename?: string): Promise<void> {
    await apiService.download(`/upload/download/${documentId}`, filename)
  }

  // 验证文件类型
  validateFileType(file: File, allowedTypes: string[] = ['pdf', 'doc', 'docx', 'txt', 'md']): boolean {
    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    return fileExtension ? allowedTypes.includes(fileExtension) : false
  }

  // 验证文件大小 (默认10MB)
  validateFileSize(file: File, maxSizeMB: number = 10): boolean {
    const maxSizeBytes = maxSizeMB * 1024 * 1024
    return file.size <= maxSizeBytes
  }

  // 格式化文件大小
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes'
    
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // 获取文件图标
  getFileIcon(filename: string): string {
    const extension = filename.split('.').pop()?.toLowerCase()
    
    switch (extension) {
      case 'pdf':
        return '📄'
      case 'doc':
      case 'docx':
        return '📝'
      case 'txt':
        return '📃'
      case 'md':
        return '📋'
      case 'jpg':
      case 'jpeg':
      case 'png':
        return '🖼️'
      default:
        return '📄'
    }
  }
}

export const uploadService = new UploadService()
export default uploadService