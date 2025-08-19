// API请求和响应类型定义

export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  department?: string
  position?: string
  phone?: string
  is_active: boolean
  is_superuser: boolean
  avatar_url?: string
  created_at: string
  updated_at?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
  department?: string
  position?: string
  phone?: string
}

export interface Document {
  id: number
  title: string
  description?: string
  content?: string
  file_path?: string
  file_name?: string
  file_size?: number
  file_type?: string
  mime_type?: string
  category_id?: number
  tags: string[]
  status: string
  is_public: boolean
  view_count: number
  download_count: number
  // 内容提取状态
  content_extracted?: boolean | null
  content_extraction_error?: string | null
  ai_summary?: string
  ai_tags?: string[]
  confidence_score?: number
  version: string
  parent_id?: number
  owner_id: number
  created_at: string
  updated_at?: string
}

export interface DocumentCreate {
  title: string
  description?: string
  content?: string
  category_id?: number
  tags?: string[]
  status?: string
  is_public?: boolean
}

export interface DocumentUpdate {
  title?: string
  description?: string
  content?: string
  category_id?: number
  tags?: string[]
  status?: string
  is_public?: boolean
}

export interface Category {
  id: number
  name: string
  description?: string
  color?: string
  icon?: string
  parent_id?: number
  sort_order: number
  is_active: boolean
  creator_id?: number
  created_at: string
  updated_at?: string
  document_count?: number
}

export interface CategoryCreate {
  name: string
  description?: string
  color?: string
  icon?: string
  parent_id?: number
  sort_order?: number
  is_active?: boolean
}

export interface CategoryStatistics {
  categories: Category[]
  uncategorized_count: number
  total_categories: number
}

export interface SearchQuery {
  query: string
  category_id?: number
  tags?: string[]
  file_type?: string
  date_from?: string
  date_to?: string
  page?: number
  per_page?: number
}

export interface SearchResult {
  id: number
  title: string
  description?: string
  content_snippet: string
  category?: Category
  tags: string[]
  file_type?: string
  score: number
  created_at: string
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  per_page: number
  pages: number
  query_time: number
}

export interface ApiError {
  detail: string
  status_code?: number
}