<template>
  <PageLayout title="智能搜索">
        <n-space vertical size="large">
          <!-- 搜索框 -->
          <n-card>
            <n-space vertical>
              <n-input
                v-model:value="searchQuery"
                size="large"
                placeholder="输入关键词搜索文档内容..."
                clearable
                @keydown.enter="handleSearch"
                @input="handleInputChange"
              >
                <template #prefix>
                  <n-icon :component="SearchOutline" />
                </template>
                <template #suffix>
                  <n-button 
                    type="primary" 
                    @click="handleSearch" 
                    :loading="searching"
                    style="background-color: #18a058; border-color: #18a058; color: white;"
                  >
                    搜索
                  </n-button>
                </template>
              </n-input>
              
              <!-- 高级搜索选项 -->
              <n-collapse>
                <n-collapse-item title="高级搜索" name="advanced">
                  <n-grid cols="1 s:2 m:3" responsive="screen" :x-gap="12" :y-gap="12">
                    <n-grid-item>
                      <n-form-item label="搜索范围">
                        <n-text>仅搜索文档内容</n-text>
                      </n-form-item>
                    </n-grid-item>
                    <n-grid-item>
                      <n-form-item label="文档类型">
                        <n-select
                          v-model:value="filters.type"
                          :options="documentTypes"
                          placeholder="全部类型"
                          clearable
                        />
                      </n-form-item>
                    </n-grid-item>
                    <n-grid-item>
                      <n-form-item label="创建时间">
                        <n-date-picker
                          v-model:value="filters.dateRange"
                          type="daterange"
                          placeholder="选择时间范围"
                          clearable
                        />
                      </n-form-item>
                    </n-grid-item>
                    <n-grid-item>
                      <n-form-item label="排序方式">
                        <n-select
                          v-model:value="filters.sortBy"
                          :options="sortOptions"
                          placeholder="相关度"
                        />
                      </n-form-item>
                    </n-grid-item>
                  </n-grid>
                </n-collapse-item>
              </n-collapse>
            </n-space>
          </n-card>

          <!-- 搜索统计 -->
          <div v-if="searchResults.length > 0">
            <n-space justify="space-between" align="center">
              <n-text depth="3">
                找到 {{ totalResults }} 个相关文档 (耗时 {{ searchTime }}ms)
              </n-text>
              <n-space>
                <n-tag type="primary">
                  文档 ({{ documentResults.length }})
                </n-tag>
              </n-space>
            </n-space>
          </div>

          <!-- 搜索建议 -->
          <n-card v-if="searchSuggestions.length > 0 && !hasSearched" title="搜索建议">
            <n-space>
              <n-tag
                v-for="suggestion in searchSuggestions"
                :key="suggestion"
                clickable
                @click="searchQuery = suggestion; handleSearch()"
              >
                {{ suggestion }}
              </n-tag>
            </n-space>
          </n-card>
          
          <!-- 搜索实时建议 -->
          <n-card v-if="inputSuggestions.length > 0 && searchQuery.length >= 2 && !hasSearched" title="相关建议">
            <n-space>
              <n-tag
                v-for="suggestion in inputSuggestions"
                :key="suggestion"
                clickable
                size="small"
                @click="searchQuery = suggestion; handleSearch()"
              >
                {{ suggestion }}
              </n-tag>
            </n-space>
          </n-card>

          <!-- 搜索结果统计 -->
          <n-card v-if="searchResults.length > 0" class="search-stats">
            <n-space justify="space-between" align="center">
              <n-space align="center">
                <n-text strong>搜索结果统计：</n-text>
                <n-tag type="info" size="small">
                  共{{ searchStats.total_matches }}条
                </n-tag>
                <n-tag type="success" size="small" v-if="searchStats.content_matches > 0">
                  内容匹配{{ searchStats.content_matches }}条
                </n-tag>
                <n-tag type="warning" size="small" v-if="searchStats.title_matches > 0">
                  标题匹配{{ searchStats.title_matches }}条
                </n-tag>
                <n-tag type="default" size="small" v-if="searchStats.description_matches > 0">
                  描述匹配{{ searchStats.description_matches }}条
                </n-tag>
              </n-space>
              <n-text depth="3" style="font-size: 12px;">
                按优先级排序：内容 > 标题 > 描述
              </n-text>
            </n-space>
          </n-card>

          <!-- 搜索结果 -->
          <n-space v-if="searchResults.length > 0" vertical size="medium">
            <!-- 文档结果 -->
            <n-card
              v-for="result in displayResults"
              :key="`${result.type}-${result.id}`"
              hoverable
              @click="previewDocument(result)"
              style="cursor: pointer"
            >
              <template #header>
                <n-space justify="space-between" align="center">
                  <n-space align="center">
                    <n-icon :component="DocumentTextOutline" />
                    <n-h4>{{ result.title }}</n-h4>
                  </n-space>
                  <n-space>
                    <n-tag :type="getResultTypeColor(result)" size="small">
                      {{ getResultTypeLabel(result) }}
                    </n-tag>
                    <n-tag :type="getMatchTypeColor(result)" size="small" v-if="result.match_type">
                      {{ getMatchTypeLabel(result) }}
                    </n-tag>
                    <n-text depth="3" v-if="result.score">相关度: {{ Math.round(result.score * 100) }}%</n-text>
                    <n-text depth="3" v-if="result.match_count">匹配: {{ result.match_count }}处</n-text>
                  </n-space>
                </n-space>
              </template>
              
              <n-space vertical>
                <!-- 文档高亮片段 -->
                <div v-if="result.highlighted_snippets && result.highlighted_snippets.length > 0" class="highlight-container">
                  <div v-for="(snippet, idx) in result.highlighted_snippets.slice(0, 3)" :key="idx" class="highlight-item">
                    <!-- 显示匹配类型标识 -->
                    <n-space align="center" style="margin-bottom: 4px;">
                      <n-tag 
                        :type="getSnippetTagType(snippet.type)" 
                        size="tiny"
                        style="font-size: 10px;"
                      >
                        {{ snippet.label }}
                      </n-tag>
                    </n-space>
                    <div v-html="sanitizeHighlightHtml(snippet.text)" class="highlight-text"></div>
                  </div>
                </div>
                <!-- 兼容旧版本的highlights -->
                <div v-else-if="result.highlights" class="highlight-container">
                  <div v-for="(highlight, idx) in result.highlights.slice(0, 3)" :key="idx" class="highlight-item">
                    <n-text depth="3" style="font-size: 11px;" v-if="result.match_type === 'content'">
                      第 {{ highlight.line_number }} 行:
                    </n-text>
                    <n-text depth="3" style="font-size: 11px;" v-else-if="result.match_type === 'title'">
                      匹配位置:
                    </n-text>
                    <div v-html="sanitizeHighlightHtml(highlight.text)" class="highlight-text"></div>
                  </div>
                </div>
                
                <n-space justify="space-between">
                  <n-text depth="3">{{ formatDate(result.updated_at) }}</n-text>
                  <n-space>
                    <n-button size="small" @click.stop="previewDocument(result)">
                      预览内容
                    </n-button>
                    <n-button 
                      size="small" 
                      type="primary" 
                      @click.stop="downloadDocument(result.id)"
                      style="background-color: #18a058; border-color: #18a058; color: white;"
                    >
                      下载
                    </n-button>
                  </n-space>
                </n-space>
              </n-space>
            </n-card>
          </n-space>

          <!-- 无结果提示 -->
          <n-empty
            v-if="hasSearched && searchResults.length === 0"
            description="未找到相关文档"
            style="margin-top: 60px"
          >
            <template #extra>
              <n-button @click="clearSearch">清空搜索</n-button>
            </template>
          </n-empty>
        </n-space>
  </PageLayout>

    <!-- 文档预览模态框 -->
    <n-modal v-model:show="showPreviewModal" preset="card" style="width: 90%; height: 85%; max-width: 1200px;" :title="previewTitle">
      <div v-if="previewContent">
        <!-- 文档信息行 -->
        <n-space justify="space-between" align="center" style="margin-bottom: 12px;">
          <n-space>
            <n-tag :type="getFileTypeColor(previewDocumentData?.file_type)">
              {{ previewDocumentData?.file_type?.toUpperCase() || 'TXT' }}
            </n-tag>
            <n-text depth="3" v-if="previewDocumentData?.file_size">
              文件大小: {{ formatFileSize(previewDocumentData.file_size) }}
            </n-text>
            <n-tag 
              type="success" 
              size="small"
              v-if="previewDocumentData?.content_extracted"
            >
              预处理内容
            </n-tag>
          </n-space>
          <n-space>
            <n-button size="small" @click="copyContent" v-if="!previewDocumentData?.is_pdf_original">
              <template #icon>
                <n-icon :component="CopyOutline" />
              </template>
              复制内容
            </n-button>
            <n-button 
              size="small" 
              type="primary" 
              @click="downloadDocument(previewDocumentData?.document_id)"
              style="background-color: #18a058; border-color: #18a058; color: white;"
            >
              <template #icon>
                <n-icon :component="DownloadOutline" />
              </template>
              下载文件
            </n-button>
          </n-space>
        </n-space>
        
        
        <!-- 提取状态提示 -->
        <n-alert 
          v-if="previewDocumentData?.content_extraction_error" 
          type="warning" 
          style="margin-bottom: 12px;"
          :show-icon="false"
        >
          <n-text style="font-size: 12px;">
            预处理失败: {{ previewDocumentData.content_extraction_error }}
          </n-text>
        </n-alert>
        
        <n-divider style="margin: 12px 0;" />
        
        <!-- 预览模式切换 (仅对OCR提取的图片和PDF显示) -->
        <n-space align="center" style="margin-bottom: 16px;" v-if="shouldShowViewToggle(previewDocumentData)">
          <n-radio-group v-model:value="previewMode" size="small">
            <n-radio-button value="extracted">提取内容</n-radio-button>
            <n-radio-button value="original">原文件</n-radio-button>
          </n-radio-group>
        </n-space>
        
        <!-- 提取内容模式 -->
        <n-scrollbar 
          v-if="previewMode === 'extracted' || !shouldShowViewToggle(previewDocumentData)"
          style="max-height: 60vh;"
        >
          <pre v-html="sanitizeDocumentHtml(previewContent)" class="preview-content"></pre>
        </n-scrollbar>
        
        <!-- 原文件模式 (仅对支持的文件类型显示) -->
        <div v-else-if="shouldShowViewToggle(previewDocumentData) && previewMode === 'original'" class="original-file-preview" style="height: 60vh;">
          <!-- PDF 文件使用 iframe 预览 -->
          <iframe 
            v-if="isPDFFile(previewDocumentData)"
            :src="getFileUrl(previewDocumentData)" 
            style="width: 100%; height: 100%; border: none; border-radius: 4px;"
            title="PDF预览"
          ></iframe>
          
          <!-- 图片文件预览 -->
          <div v-else-if="isImageFile(previewDocumentData?.file_type)" style="text-align: center; height: 100%; display: flex; align-items: center; justify-content: center;">
            <img 
              :src="getFileUrl(previewDocumentData)" 
              style="max-width: 100%; max-height: 100%; object-fit: contain;"
              :alt="previewDocumentData.title"
            />
          </div>
          
          <!-- 其他文件类型显示下载信息 -->
          <div v-else class="file-download-info">
            <n-empty description="此文件类型不支持在线预览">
              <template #extra>
                <n-space vertical align="center">
                  <n-text>文件名：{{ previewDocumentData.title }}</n-text>
                  <n-text depth="3">文件大小：{{ formatFileSize(previewDocumentData.file_size) }}</n-text>
                  <n-button type="primary" @click="downloadDocument(previewDocumentData?.document_id)">
                    <template #icon>
                      <n-icon><DownloadOutline /></n-icon>
                    </template>
                    下载文件
                  </n-button>
                </n-space>
              </template>
            </n-empty>
          </div>
        </div>
      </div>
      <div v-else-if="previewLoading" style="text-align: center; padding: 40px;">
        <n-spin size="large" />
        <div style="margin-top: 16px;">加载中...</div>
      </div>
    </n-modal>
    
    <!-- 资产详情模态框已移除 - 智能搜索现在只支持文档搜索 -->
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useSafeHtml } from '@/utils/xss-protection'
import {
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NSpace,
  NH2,
  NH3,
  NH4,
  NInput,
  NButton,
  NIcon,
  NCard,
  NTag,
  NText,
  NEmpty,
  NCollapse,
  NCollapseItem,
  NGrid,
  NGridItem,
  NFormItem,
  NSelect,
  NDatePicker,
  NRadioGroup,
  NRadio,
  NModal,
  NDivider,
  NScrollbar,
  NDescriptions,
  NDescriptionsItem,
  NSpin,
  NAlert,
  useMessage
} from 'naive-ui'
import {
  SearchOutline,
  DocumentTextOutline,
  CopyOutline,
  DownloadOutline
} from '@vicons/ionicons5'
import PageLayout from '../components/PageLayout.vue'
import { apiService } from '@/services/api'

interface DocumentSearchResult {
  id: number
  title: string
  file_type: string
  file_path: string
  score: number
  match_count: number
  highlights: Array<{
    text: string
    line_number: number
  }>
  updated_at: string
  type: 'document'
  match_type?: 'content' | 'title'
}

// 资产搜索相关接口已移除

type SearchResult = DocumentSearchResult

interface PreviewData {
  document_id: number
  title: string
  file_type: string
  content: string
  content_extracted: boolean
  content_extraction_error?: string
  original_length: number
  is_truncated: boolean
  file_size: number
  view_mode?: string
  is_pdf_original?: boolean
  supports_dual_mode?: boolean
}

const message = useMessage()
const searchQuery = ref('')
const searching = ref(false)
const hasSearched = ref(false)
const searchTime = ref(0)
const totalResults = ref(0)

// 搜索统计信息
const searchStats = ref({
  total_matches: 0,
  content_matches: 0,
  title_matches: 0,
  description_matches: 0
})

// 预览相关
const showPreviewModal = ref(false)
const previewLoading = ref(false)
const previewContent = ref('')
const previewDocumentData = ref<PreviewData | null>(null)
const previewMode = ref<'extracted' | 'original'>('extracted')

// 搜索结果
const documentResults = ref<DocumentSearchResult[]>([])
const inputSuggestions = ref<string[]>([])

// XSS防护
const { sanitizeHighlightHtml, sanitizeDocumentHtml } = useSafeHtml()

const filters = ref({
  searchScope: 'all',
  type: null,
  dateRange: null,
  sortBy: 'relevance'
})

const searchResults = computed<SearchResult[]>(() => {
  return documentResults.value
})

const displayResults = computed(() => {
  return searchResults.value.slice(0, 20) // 限制显示数量
})

const previewTitle = computed(() => {
  return previewDocumentData.value ? previewDocumentData.value.title : '文档预览'
})

const searchSuggestions = ref(['Nginx配置', '数据库优化', '监控告警', '故障排查', '部署文档', 'API文档', '运维手册', '技术规范'])

// 搜索范围选项已移除 - 现在只搜索文档

const documentTypes = [
  { label: 'TXT文本', value: 'txt' },
  { label: 'Markdown', value: 'md' },
  { label: 'JSON数据', value: 'json' },
  { label: 'CSV表格', value: 'csv' },
  { label: 'Excel表格', value: 'xlsx' },
  { label: '其他', value: 'other' }
]

const sortOptions = [
  { label: '相关度', value: 'relevance' },
  { label: '创建时间', value: 'created' },
  { label: '更新时间', value: 'updated' },
  { label: '标题', value: 'title' }
]

const getResultTypeColor = (result: SearchResult): 'default' | 'error' | 'primary' | 'info' | 'success' | 'warning' => {
  const fileType = result.file_type?.toLowerCase()
  return getFileTypeColor(fileType)
}

const getResultTypeLabel = (result: SearchResult) => {
  const fileType = result.file_type?.toUpperCase()
  return fileType || '文档'
}

const getFileTypeColor = (fileType?: string): 'default' | 'error' | 'primary' | 'info' | 'success' | 'warning' => {
  const colors: Record<string, 'default' | 'error' | 'primary' | 'info' | 'success' | 'warning'> = {
    txt: 'default',
    md: 'primary',
    json: 'info',
    csv: 'warning',
    xlsx: 'success',
    py: 'error',
    js: 'warning'
  }
  return colors[fileType?.toLowerCase() || ''] || 'default'
}

const getMatchTypeColor = (result: SearchResult): 'default' | 'error' | 'primary' | 'info' | 'success' | 'warning' => {
  if (result.match_type === 'content') {
    return 'success'
  } else if (result.match_type === 'title') {
    return 'warning'
  }
  return 'default'
}

const getMatchTypeLabel = (result: SearchResult) => {
  if (result.match_type === 'content') {
    return '正文匹配'
  } else if (result.match_type === 'title') {
    return '标题匹配'
  }
  return '未知'
}

const getSnippetTagType = (snippetType: string): 'default' | 'error' | 'primary' | 'info' | 'success' | 'warning' => {
  switch (snippetType) {
    case 'content':
      return 'success'
    case 'title': 
      return 'warning'
    case 'description':
      return 'info'
    case 'filename':
      return 'default'
    default:
      return 'default'
  }
}

const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const isImageFile = (fileType?: string) => {
  if (!fileType) return false
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
  return imageTypes.includes(fileType.toLowerCase())
}

// PDF文件检测函数
const isPDFFile = (document: any): boolean => {
  if (!document) return false
  return document.file_type?.toLowerCase() === 'pdf'
}

// 判断是否应该显示视图切换按钮 (仅对OCR提取的图片和PDF)
const shouldShowViewToggle = (document: any): boolean => {
  if (!document) return false
  // 只有图片和PDF文件显示切换按钮
  return isPDFFile(document) || isImageFile(document.file_type)
}


// 实时输入建议
const handleInputChange = async () => {
  if (searchQuery.value.length >= 2) {
    try {
      const response = await apiService.get('/search/suggestions', {
        params: { q: searchQuery.value }
      })
      inputSuggestions.value = response.suggestions || []
    } catch (error) {
      inputSuggestions.value = []
    }
  } else {
    inputSuggestions.value = []
  }
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  hasSearched.value = true
  inputSuggestions.value = [] // 清空实时建议
  const startTime = Date.now()

  try {
    // 只搜索文档
    const docParams: any = {
      q: searchQuery.value,
      limit: 50
    }
    if (filters.value.type) {
      docParams.doc_type = filters.value.type
    }
    
    console.log('🔍 搜索参数:', docParams)
    
    // 使用统一API
    const response = await apiService.get('/search/documents', { params: docParams })
    documentResults.value = response.results.map((item: any) => ({
      ...item,
      type: 'document'
    }))
    
    // 更新搜索统计信息
    if (response.statistics) {
      searchStats.value = response.statistics
    } else {
      // 兼容旧版API
      searchStats.value = {
        total_matches: response.total || documentResults.value.length,
        content_matches: 0,
        title_matches: 0, 
        description_matches: 0
      }
    }
    
    totalResults.value = documentResults.value.length
    searchTime.value = Date.now() - startTime
    
    if (totalResults.value === 0) {
      message.info('未找到相关结果')
    }
    
  } catch (error) {
    console.error('搜索错误:', error)
    message.error('搜索失败，请重试')
    documentResults.value = []
    totalResults.value = 0
  } finally {
    searching.value = false
  }
}

// 预览文档
const previewDocument = async (doc: DocumentSearchResult) => {
  previewLoading.value = true
  showPreviewModal.value = true
  previewContent.value = ''
  previewMode.value = 'extracted' // 重置预览模式
  
  await loadPreviewContent(doc.id)
}

// 加载预览内容
const loadPreviewContent = async (documentId: number) => {
  try {
    // 使用统一API，添加新参数启用完整内容显示和智能格式化
    const response = await apiService.get(`/search/preview/${documentId}`, {
      params: {
        highlight: searchQuery.value,
        format_mode: 'formatted',  // 启用智能格式化
        max_length: null,          // 移除长度限制
        source: 'auto',            // 自动选择最佳内容源
        view_mode: 'content'       // 默认内容提取模式
      }
    })
    
    previewDocumentData.value = response
    previewContent.value = response.content
    
    // 调试：检查PDF切换功能相关数据
    console.log('文档预览数据:', {
      file_type: response.file_type,
      supports_dual_mode: response.supports_dual_mode,
      is_pdf_original: response.is_pdf_original,
      view_mode: response.view_mode
    })
  } catch (error) {
    console.error('预览文档失败:', error)
    message.error('预览文档失败')
    previewContent.value = '无法加载文档内容'
  } finally {
    previewLoading.value = false
  }
}

// 获取文件URL用于预览
const getFileUrl = (document: any): string => {
  if (!document) return ''
  
  // 动态检测服务器地址，支持多机器访问
  const currentHost = window.location.hostname
  const currentProtocol = window.location.protocol
  let baseUrl = import.meta.env.VITE_API_BASE_URL
  
  // 如果没有环境变量配置，自动推断API地址
  if (!baseUrl) {
    if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
      // 如果是通过IP访问，使用相同IP的8002端口
      baseUrl = `${currentProtocol}//${currentHost}:8002`
    } else {
      // 本地访问使用localhost
      baseUrl = 'http://localhost:8002'
    }
  }
  
  // 确保baseUrl不包含/api/v1后缀，避免重复
  if (baseUrl.endsWith('/api/v1')) {
    baseUrl = baseUrl.replace('/api/v1', '')
  }
  
  return `${baseUrl}/api/v1/search/original/${document.document_id}`
}

// 已移除预览来源切换功能，直接使用预处理内容

// 查看资产详情函数已移除

// 复制内容
const copyContent = async () => {
  if (previewContent.value) {
    try {
      // 移除HTML标签
      const textContent = previewContent.value.replace(/<[^>]*>/g, '')
      await navigator.clipboard.writeText(textContent)
      message.success('内容已复制到剪贴板')
    } catch (error) {
      message.error('复制失败')
    }
  }
}

const downloadDocument = async (id: number | undefined) => {
  if (!id) {
    message.error('文档ID无效')
    return
  }
  
  try {
    message.info('开始下载文档...')
    // 实际应该调用下载API
    await apiService.download(`/documents/${id}/download`)
    message.success('下载完成')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  documentResults.value = []
  inputSuggestions.value = []
  hasSearched.value = false
  totalResults.value = 0
  filters.value = {
    searchScope: 'all',
    type: null,
    dateRange: null,
    sortBy: 'relevance'
  }
}

// 搜索范围监听已移除 - 只搜索文档

// 监听预览模式变化
watch(previewMode, async (newMode) => {
  if (!previewDocumentData.value) return
  
  previewLoading.value = true
  
  try {
    if (newMode === 'original') {
      // 原文查看模式，获取PDF/图片文件信息
      const response = await apiService.get(`/search/preview/${previewDocumentData.value.document_id}`, {
        params: {
          view_mode: 'original'
        }
      })
      previewDocumentData.value = response
      previewContent.value = response.content
    } else {
      // 内容提取模式
      const response = await apiService.get(`/search/preview/${previewDocumentData.value.document_id}`, {
        params: {
          view_mode: 'content',
          highlight: searchQuery.value,
          format_mode: 'formatted',
          max_length: null,
          source: 'auto'
        }
      })
      previewDocumentData.value = response
      previewContent.value = response.content
    }
  } catch (error) {
    console.error('切换预览模式失败:', error)
    message.error('切换预览模式失败')
  } finally {
    previewLoading.value = false
  }
})

onMounted(async () => {
  // 初始化搜索建议
  try {
    const response = await apiService.get('/search/suggestions')
    searchSuggestions.value = response.suggestions || searchSuggestions.value
  } catch (error) {
    console.log('获取搜索建议失败')
  }
})
</script>

<style scoped>

.highlight-container {
  background-color: #f8f9fa;
  border-radius: 4px;
  padding: 12px;
  margin: 8px 0;
}

.highlight-item {
  margin-bottom: 8px;
}

.highlight-item:last-child {
  margin-bottom: 0;
}

.highlight-text {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.4;
  white-space: pre-wrap;
  background-color: white;
  padding: 8px;
  border-radius: 2px;
  border-left: 3px solid #18a058;
}

.highlight-text :deep(mark) {
  background-color: #fff3cd;
  color: #856404;
  padding: 1px 2px;
  border-radius: 2px;
  font-weight: 500;
}

/* 资产相关样式已移除 */

.preview-content {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  background-color: #f8f9fa;
  padding: 16px;
  border-radius: 4px;
  margin: 0;
}

.preview-content :deep(mark) {
  background-color: #fff3cd;
  color: #856404;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 500;
}

/* 搜索结果高亮样式 */
.highlight-container {
  margin: 8px 0;
}

.highlight-item {
  margin: 6px 0;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #18a058;
}

.highlight-text {
  font-size: 13px;
  line-height: 1.4;
  color: #333;
}

.highlight-text :deep(.highlight),
.highlight-text :deep(mark) {
  background-color: #ffeb3b;
  color: #333;
  padding: 1px 3px;
  border-radius: 2px;
  font-weight: 600;
  box-shadow: 0 0 0 1px rgba(255, 235, 59, 0.3);
}

.search-stats {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border: 1px solid #e1e7f0;
}

.search-stats :deep(.n-card__content) {
  padding: 12px 16px;
}

/* 原文件预览样式 */
.original-file-preview {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-download-info {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 40px;
}
</style>