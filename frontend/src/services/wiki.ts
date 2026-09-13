/**
 * Wiki 前端 service（W4/W5 用）
 */
import apiService from './api'

export interface WikiDocMeta {
  doc_id: number
  path: string
  title: string
  mtime?: string
  doc_type?: string
  frontmatter_json?: string
  tags?: string[]
}

export interface WikiSearchResult {
  doc_id: number
  path: string
  title: string
  snippet: string
}

export interface WikiTag {
  tag: string
  doc_count: number
}

export interface WikiReport {
  report: string
  doc_count: number
  sources: Array<{ doc_id: number; title: string; snippet: string }>
  format: string
}

export const wikiService = {
  async search(q: string, tag?: string, docType?: string, topK = 5) {
    return await apiService.get<{ query: string; results: WikiSearchResult[] }>(
      '/wiki/search',
      { params: { q, tag, doc_type: docType, top_k: topK } }
    )
  },

  async getDoc(docId: number): Promise<WikiDocMeta> {
    return await apiService.get<WikiDocMeta>(`/wiki/doc/${docId}`)
  },

  async getMarkdown(docId: number): Promise<{ doc_id: number; content: string }> {
    return await apiService.get<{ doc_id: number; content: string }>(`/wiki/doc/${docId}/markdown`)
  },

  async saveMarkdown(docId: number, content: string): Promise<{ success: boolean; path: string }> {
    return await apiService.put<{ success: boolean; path: string }>(`/wiki/doc/${docId}/markdown`, { content })
  },

  async rebuildIndex(): Promise<{ total: number; ok: number; fail: number }> {
    return await apiService.post('/wiki/rebuild')
  },

  async listTags(prefix = ''): Promise<{ tags: WikiTag[] }> {
    return await apiService.get('/wiki/tags', { params: { prefix } })
  },

  async listBacklinks(docId: number) {
    return await apiService.get(`/wiki/doc/${docId}/backlinks`)
  },

  async getStats() {
    return await apiService.get('/wiki/stats')
  },

  async generateReport(topic: string, tag?: string, maxDocs = 10): Promise<WikiReport> {
    return await apiService.post<WikiReport>('/wiki/report', { topic, tag, max_docs: maxDocs })
  },

  /**
   * 下载文档（支持 original / markdown）
   */
  async download(docId: number, type: 'original' | 'markdown', filename: string) {
    return await apiService.get<Blob>(
      `/wiki/download/${docId}?type=${type}`,
      { responseType: 'blob' }
    ).then(blob => {
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    })
  },
}

export default wikiService