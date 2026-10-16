<template>
  <PageLayout title="智能搜索">
        <n-space vertical size="large">
          <!-- 搜索框 -->
          <n-card>
            <n-space vertical>
              <n-input
                v-model:value="searchQuery"
                size="large"
                placeholder="输入关键词搜索，多个词用空格分隔（如：交换机 配置）"
                clearable
                @keydown.enter="handleSearch"
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
                    <!-- 阶段二十：多词联合搜索 — 显示命中词数（单词查询不显示） -->
                    <n-tag type="success" size="small" v-if="result.term_total && result.term_total > 1">
                      命中 {{ (result.matched_terms || []).length }}/{{ result.term_total }} 词
                    </n-tag>
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
                    <n-dropdown
                      trigger="click"
                      :options="downloadMenuOptions"
                      @select="(key: string) => downloadDocument(result.id, key, result.title, result.file_type)"
                    >
                      <n-button
                        size="small"
                        type="primary"
                        style="background-color: #18a058; border-color: #18a058; color: white;"
                      >
                        下载
                      </n-button>
                    </n-dropdown>
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
    <!-- 27.12：预览弹窗尺寸对齐 DocumentView（原 90%/85%/max-1200 偏小） -->
    <n-modal v-model:show="showPreviewModal" preset="card" style="width: 98%; height: 95%; max-width: none; min-width: 1200px;" :title="previewTitle">
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
            <!-- 编辑（与文档管理一致：仅超管，编辑 MD 副本，保存自动重建索引） -->
            <n-button
              v-if="currentUser?.is_superuser && previewMode === 'extracted'"
              size="small"
              type="primary"
              style="background-color: #18a058; border-color: #18a058; color: white;"
              @click="togglePreviewEdit"
              :loading="savingPreviewEdit"
            >
              <template #icon>
                <n-icon :component="PencilOutline" />
              </template>
              {{ previewEditMode ? '退出编辑' : '编辑' }}
            </n-button>
            <n-dropdown
              trigger="click"
              :options="downloadMenuOptions"
              @select="(key: string) => downloadDocument(previewDocumentData?.document_id, key, previewDocumentData?.title, previewDocumentData?.file_type)"
            >
              <n-button
                size="small"
                type="primary"
                style="background-color: #18a058; border-color: #18a058; color: white;"
              >
                <template #icon>
                  <n-icon :component="DownloadOutline" />
                </template>
                下载文件
              </n-button>
            </n-dropdown>
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
        
        <!-- 阶段二十三·23.2：所有格式都显示"提取内容/原文件"切换；右上角对齐 -->
        <div
          v-if="shouldShowViewToggle(previewDocumentData)"
          style="display: flex; justify-content: flex-end; margin-bottom: 16px;"
        >
          <n-radio-group v-model:value="previewMode" size="small">
            <n-radio-button value="extracted">提取内容</n-radio-button>
            <n-radio-button value="original">原文件</n-radio-button>
          </n-radio-group>
        </div>
        
        <!-- 编辑模式操作栏 -->
        <n-space align="center" style="margin-bottom: 16px;" v-if="previewEditMode">
          <n-text depth="3" style="font-size: 12px;">正在编辑 Markdown 副本，保存后自动重建索引</n-text>
          <n-space>
            <n-button size="small" @click="cancelPreviewEdit">取消</n-button>
            <n-button size="small" type="primary" @click="savePreviewEdit" :loading="savingPreviewEdit">
              保存
            </n-button>
          </n-space>
        </n-space>

        <!-- 29.5：搜索高亮导航——拆成两部分：
             1) 顶部全局"共 N 处 / ↑↓ / 当前位置"由 MarkdownPreviewBody 组件内部渲染
             2) 多词分组卡片（按词跳转二级入口）保留在 SearchView 自己,用 slot 注入组件 -->
        <div v-if="!previewEditMode && previewMode === 'extracted' && searchQuery && termGroups.length > 0" style="margin-bottom: 16px;">
          <n-space align="center" size="small" wrap>
            <div
              v-for="group in termGroups"
              :key="group.term"
              class="term-nav-item"
              :class="{ 'term-nav-active': activeNavTerm === group.term }"
              :style="{ borderColor: getTermColor(group.term) }"
              @click="selectNavTerm(group.term)"
            >
              <span class="term-nav-label" :style="{ color: getTermColor(group.term) }">
                {{ group.term }}
              </span>
              <span class="term-nav-count">{{ group.count }}处</span>
              <n-button-group size="tiny">
                <n-button
                  @click.stop="scrollToHighlightInPreview(group.term, -1)"
                  :disabled="group.count > 1 && getTermCursor(group.term) <= 0"
                >↑</n-button>
                <n-button
                  @click.stop="scrollToHighlightInPreview(group.term, 1)"
                  :disabled="group.count > 1 && getTermCursor(group.term) >= group.count - 1"
                >↓</n-button>
              </n-button-group>
              <span class="term-nav-pos">
                {{ getTermCursor(group.term) + 1 }} / {{ group.count }}
              </span>
            </div>
          </n-space>
        </div>

        <!-- 编辑模式：textarea 直接编辑 Markdown 副本 -->
        <n-input
          v-if="previewEditMode"
          v-model:value="previewEditContent"
          type="textarea"
          :autosize="{ minRows: 15, maxRows: 30 }"
          placeholder="编辑 Markdown 内容..."
          style="font-family: 'Consolas', 'Monaco', monospace; font-size: 13px;"
        />
        <!-- 29.5：提取内容模式——使用共享 MarkdownPreviewBody 组件
             SearchView 走 mode='html' 模式:displayPreviewHtml 已包含渲染+mark 注入+图片水合
             组件职责:补 data-highlight-index + 全局 ↑↓ + Ctrl+F 焦点 + 链接 native 跳转 -->
        <MarkdownPreviewBody
          v-else-if="previewMode === 'extracted' || !shouldShowViewToggle(previewDocumentData)"
          ref="markdownBodyRef"
          mode="html"
          :html="displayPreviewHtml"
          :keyword="searchQuery"
          :max-height="'60vh'"
          :show-highlight-nav="true"
        />
        
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
                  <n-dropdown
                    trigger="click"
                    :options="downloadMenuOptions"
                    @select="(key: string) => downloadDocument(previewDocumentData?.document_id, key, previewDocumentData?.title, previewDocumentData?.file_type)"
                  >
                    <n-button type="primary">
                      <template #icon>
                        <n-icon><DownloadOutline /></n-icon>
                      </template>
                      下载文件
                    </n-button>
                  </n-dropdown>
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
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
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
  NDescriptions,
  NDescriptionsItem,
  NSpin,
  NAlert,
  NRadioButton,
  useMessage
} from 'naive-ui'
import {
  SearchOutline,
  DocumentTextOutline,
  CopyOutline,
  DownloadOutline,
  PencilOutline
} from '@vicons/ionicons5'
import PageLayout from '../components/PageLayout.vue'
import MarkdownPreviewBody from '../components/MarkdownPreviewBody.vue'  // 29.5:共享预览核心
import { apiService } from '@/services/api'
import { authService } from '@/services'
import { wikiService } from '@/services/wiki'
import type { User } from '@/types/api'
import { downloadWikiDocument, hydrateWikiImages } from '@/utils/file-download'
import { renderMarkdown } from '@/utils/markdown-renderer'

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
  match_type?: 'content' | 'title' | 'description'
  // 阶段二十：多词联合搜索（后端返回命中的词与总词数）
  matched_terms?: string[]
  term_total?: number
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


// 搜索高亮导航相关（阶段二十·20.5：多词分别导航）
// termGroups: 按查询顺序 [{ term, count, indexes: 全局 mark 索引[] }]
const termGroups = ref<Array<{ term: string; count: number; indexes: number[] }>>([])
const currentHighlightIndex = ref(0)
// 每个词当前导航到的位置（term → 该词 indexes 中的下标）
const termCursor = ref<Record<string, number>>({})

// 29.11 修：MarkdownPreviewBody 的模板 ref 必须声明同名变量才能绑定
// （29.5 漏声明 → watch 里 markdownBodyRef.value 抛 ReferenceError → Ctrl+F 焦点迁移失效）
const markdownBodyRef = ref<{ focusForFind?: () => void } | null>(null)

// 编辑模式相关（与文档管理 W4 一致：仅超管可编辑 MD 副本）
const currentUser = ref<User | null>(null)
const previewEditMode = ref(false)
const previewEditContent = ref('')
const savingPreviewEdit = ref(false)

// 总高亮数（所有词命中数之和）
const highlightedCount = computed(() => termGroups.value.reduce((sum, g) => sum + g.count, 0))

// 搜索结果
const documentResults = ref<DocumentSearchResult[]>([])

// XSS防护
const { sanitizeHighlightHtml, sanitizeDocumentHtml } = useSafeHtml()

// 20.6：Markdown 渲染后的 HTML（markdown-it 渲染 + 高亮注入 + sanitize + 图片水合）
// previewHtml = 最终 v-html 展示内容；previewBaseHtml = 水合前的基线
const previewHtml = ref('')
const previewBaseHtml = ref('')
// 图片水合（对齐文档管理：MD 内嵌 images/{docId}/xxx 时带 token 拉 blob URL）
const previewHydratedHtml = ref('')
let _revokePreviewImages: (() => void) | null = null
let _previewToken = 0

const displayPreviewHtml = computed(() => previewHydratedHtml.value || previewHtml.value)

const searchResults = computed<SearchResult[]>(() => {
  return documentResults.value
})

const displayResults = computed(() => {
  return searchResults.value.slice(0, 20) // 限制显示数量
})

const previewTitle = computed(() => {
  return previewDocumentData.value ? previewDocumentData.value.title : '文档预览'
})

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

// 判断是否应该显示视图切换按钮
// 阶段二十六·26.3：只对 4 类显示 — Office 文档（Word/Excel/PPT/CSV）、epub、PDF、图片
// 文本类（.txt/.md）不显示切换按钮（提取内容模式即可）
const shouldShowViewToggle = (document: any): boolean => {
  if (!document) return false
  return isPDFFile(document) || isImageFile(document.file_type)
}


const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  hasSearched.value = true
  const startTime = Date.now()

  try {
    // 只搜索文档
    const docParams: any = {
      q: searchQuery.value,
      limit: 50
    }

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
  previewEditMode.value = false   // 重置编辑模式
  previewEditContent.value = ''
  
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
    
    // 处理高亮：按词分组统计（阶段二十·20.5）
    updatePreviewHighlightCount()
    
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

// 从查询串按空白分词（与后端 tokenize_query 一致，仅空格分隔）
const splitQueryTerms = (q: string): string[] => {
  const seen = new Set<string>()
  const terms: string[] = []
  for (const p of (q || '').trim().split(/\s+/)) {
    const t = p.slice(0, 30)
    if (t && !seen.has(t)) {
      seen.add(t)
      terms.push(t)
    }
  }
  return terms
}

// 统计预览内容中的高亮，并按词分组（20.5 多词分别导航 / 20.6 Markdown 渲染）
const updatePreviewHighlightCount = () => {
  // 释放上一次图片 blob URL，重置水合结果
  if (_revokePreviewImages) { _revokePreviewImages(); _revokePreviewImages = null }
  previewHydratedHtml.value = ''

  if (!previewContent.value) {
    termGroups.value = []
    previewHtml.value = ''
    currentHighlightIndex.value = 0
    return
  }

  const termOrder = splitQueryTerms(searchQuery.value)
  const phrase = (searchQuery.value || '').trim()

  // 20.6：markdown-it 渲染为语义 HTML（与文档管理一致；后端注入的 <mark data-term> 经 html:true 原样透传）
  let html: string
  try {
    html = renderMarkdown(previewContent.value)
  } catch (e) {
    console.error('Markdown render failed:', e)
    html = `<pre>${previewContent.value}</pre>`
  }

  // 29.11 修：先 sanitize（内部把代码块/inline code 里的 sentinel 还原为真 <mark data-term>），
  // 再统一 reindex——之前先 reindex 导致 sentinel 还原出的 mark 没有 data-highlight-index，
  // 代码块内的高亮无法被 ↑↓ 导航定位（陈工"上下选择的词没出现"）
  html = sanitizeDocumentHtml(html)

  // 29.2：为 <mark> 添加全局索引 + 词归属标记（**不再注入 hl-term-* class**——统一淡黄观感）
  let highlightIndex = 0
  html = html.replace(/<mark([^>]*)>/g, (_full, attrs: string) => {
    let dataTerm = ''
    const m = attrs.match(/data-term="([^"]*)"/)
    if (m) {
      // 后端用 html.escape 转义过属性值，这里还原（仅 &quot; &amp; 两种可能）
      dataTerm = m[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&')
    } else if (termOrder.length === 1) {
      dataTerm = termOrder[0].toLowerCase()
    }
    const dataHighlightTerm = dataTerm
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
    // 29.2：不再注入 hl-term-* colorClass——观感克制优先
    return `<mark${attrs} data-highlight-term="${dataHighlightTerm}" data-highlight-index="${highlightIndex++}">`
  })

  previewHtml.value = html

  // 按查询词顺序分组（命中的词才有组；顺序与用户输入一致）
  const indexByTerm: Record<string, number[]> = {}
  const markRegex = /<mark([^>]*)>/g
  let mm: RegExpExecArray | null
  while ((mm = markRegex.exec(html)) !== null) {
    const attrs = mm[1]
    const termMatch = attrs.match(/data-highlight-term="([^"]*)"/)
    const idxMatch = attrs.match(/data-highlight-index="(\d+)"/)
    if (!termMatch || !idxMatch) continue
    const term = termMatch[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&')
    const idx = parseInt(idxMatch[1], 10)
    ;(indexByTerm[term] = indexByTerm[term] || []).push(idx)
  }

  const groups: Array<{ term: string; count: number; indexes: number[] }> = []
  // 29.11 修：多词查询且后端按整段 phrase 高亮时（data-term="ufw allow from"），
  // 拆词 termOrder 对不上整段 mark → termGroups 为空 → 词卡片/↑↓ 不出现。
  // 优先识别"整段组"：完整 q 串命中时只出一个整段卡片（陈工"整词上下选择"）
  if (termOrder.length >= 2 && phrase) {
    const phraseIndexes = indexByTerm[phrase.toLowerCase()]
    if (phraseIndexes && phraseIndexes.length > 0) {
      phraseIndexes.sort((a, b) => a - b)
      groups.push({ term: phrase, count: phraseIndexes.length, indexes: phraseIndexes })
    }
  }
  if (groups.length === 0) {
    for (const t of termOrder) {
      const key = t.toLowerCase()
      const indexes = indexByTerm[key]
      if (indexes && indexes.length > 0) {
        indexes.sort((a, b) => a - b)
        groups.push({ term: t, count: indexes.length, indexes })
      }
    }
  }
  // 兜底：后端未带 data-term 且多词时（不应发生），把全部 mark 归第一词
  if (groups.length === 0 && highlightIndex > 0) {
    groups.push({ term: termOrder[0] || searchQuery.value, count: highlightIndex, indexes: Array.from({ length: highlightIndex }, (_, i) => i) })
  }

  termGroups.value = groups
  termCursor.value = {}
  groups.forEach(g => { termCursor.value[g.term] = 0 })
  activeNavTerm.value = groups.length > 0 ? groups[0].term : ''
  currentHighlightIndex.value = 0

  // 自动跳转到第一词的首个高亮位置
  if (groups.length > 0) {
    setTimeout(() => scrollToHighlightInPreview(groups[0].term, 0), 150)
  }

  // 图片水合（20.6：MD 内嵌 images/{docId}/xxx 时带 token 拉 blob URL，对齐文档管理）
  hydratePreviewImages()
}

// 图片水合：把渲染后 HTML 里的相对图片路径替换为带 token 的 blob URL（对齐 DocumentView 18.8）
const hydratePreviewImages = async () => {
  const docId = previewDocumentData.value?.document_id
  if (!docId) return
  if (!previewHtml.value || !previewHtml.value.includes('images/')) return
  const token = ++_previewToken
  try {
    const { html, revoke } = await hydrateWikiImages(previewHtml.value, docId)
    // 内容可能已切换（预览了另一篇 / 已退出），丢弃过期结果
    if (token !== _previewToken) {
      revoke()
      return
    }
    previewHydratedHtml.value = html
    _revokePreviewImages = revoke
  } catch (e) {
    console.warn('图片水合失败:', e)
  }
}

// 组件卸载：释放图片 blob URL
onBeforeUnmount(() => {
  if (_revokePreviewImages) { _revokePreviewImages(); _revokePreviewImages = null }
  // 29.3：移除全局 saveSearchState——只在跳到 /office-edit 时存（见下方 onBeforeRouteLeave）
  // 之前 onBeforeUnmount 触发范围过广
})

// 29.3：只在跳到 /office-edit（OnlyOffice 在线预览）时保存搜索状态
onBeforeRouteLeave((to, from) => {
  if (to.name === 'office-edit') {
    saveSearchState()
  }
})

// 29.2：状态保存/恢复——从 /office-edit/:docId 返回时不丢搜索词 + 滚动位置
const SEARCH_STATE_KEY = 'runyang-search-state'

const saveSearchState = (): void => {
  try {
    sessionStorage.setItem(SEARCH_STATE_KEY, JSON.stringify({
      ts: Date.now(),
      scrollTop: window.scrollY,
      searchQuery: searchQuery.value,
    }))
  } catch {
    // 静默
  }
}

const restoreSearchState = (): void => {
  try {
    const raw = sessionStorage.getItem(SEARCH_STATE_KEY)
    if (!raw) return
    const state = JSON.parse(raw)
    if (Date.now() - (state.ts || 0) > 5 * 60 * 1000) {
      sessionStorage.removeItem(SEARCH_STATE_KEY)
      return
    }
    if (state.searchQuery) {
      searchQuery.value = state.searchQuery
      // 29.11 修：debouncedSearchQuery 不存在（29.2 遗留死代码，恢复状态时抛 ReferenceError）
    }
    if (state.scrollTop) {
      nextTick(() => setTimeout(() => {
        window.scrollTo({ top: state.scrollTop, behavior: 'auto' as ScrollBehavior })
      }, 200))
    }
  } catch {
    // 解析失败静默
  }
}

// 当前导航目标词（点击词卡片切换）
const activeNavTerm = ref('')

// 每个词的当前光标位置（1 基显示）
const getTermCursor = (term: string): number => {
  return termCursor.value[term] ?? 0
}

// 选中导航目标词（仅更新选中态，不滚动）
const selectNavTerm = (term: string) => {
  activeNavTerm.value = term
}

// 多词颜色：按查询顺序取色，单词保持默认黄色
const TERM_COLORS = ['#f5a623', '#4a90d9', '#7ed321', '#bd10e0', '#e51400', '#50e3c2', '#b8261b', '#fbc531']
const getTermColor = (term: string): string => {
  if (termGroups.value.length <= 1) return '#f5a623'
  const i = termGroups.value.findIndex(g => g.term === term)
  return TERM_COLORS[i >= 0 ? i % TERM_COLORS.length : 0]
}

// 在预览中滚动到指定词的第 N 处高亮（direction: 相对偏移，0 = 当前位置）
const scrollToHighlightInPreview = (term: string, direction: number) => {
  const group = termGroups.value.find(g => g.term === term)
  if (!group || group.count === 0) return

  activeNavTerm.value = term

  // 计算该词内的新光标位置
  let newCursor = (termCursor.value[term] ?? 0) + direction
  if (newCursor < 0) newCursor = 0
  if (newCursor >= group.count) newCursor = group.count - 1
  termCursor.value[term] = newCursor

  const globalIndex = group.indexes[newCursor]
  currentHighlightIndex.value = globalIndex

  // 查找对应的高亮元素并滚动到视图
  setTimeout(() => {
    const targetMark = document.querySelector(`.markdown-content mark[data-highlight-index="${globalIndex}"]`)
    if (targetMark) {
      // 移除之前的活跃高亮样式
      document.querySelectorAll('.markdown-content mark.active-highlight').forEach(el => {
        el.classList.remove('active-highlight')
      })
      // 添加当前高亮样式
      targetMark.classList.add('active-highlight')
      // 滚动到视图
      targetMark.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
      })
    }
  }, 100)
}

// 29.4：全局"上一处 / 下一处"——按所有 mark 出现位置整体跳转(不按词分组)
// 陈工原话"进入预览后没有按照多词作为一个整体命中进行上下选择,只有第一个词进行上下选择"
// → 顶部加一组全局 ↑↓ 与 DocumentView line 235-242 一致;下方 term-nav-item 卡片保留作为按词跳转二级入口
const scrollToGlobalHighlight = (direction: number) => {
  const total = highlightedCount.value
  if (total === 0) return
  let newIdx = currentHighlightIndex.value + direction
  if (newIdx < 0) newIdx = 0
  if (newIdx >= total) newIdx = total - 1
  currentHighlightIndex.value = newIdx

  setTimeout(() => {
    const targetMark = document.querySelector(`.markdown-content mark[data-highlight-index="${newIdx}"]`)
    if (targetMark) {
      document.querySelectorAll('.markdown-content mark.active-highlight').forEach(el => {
        el.classList.remove('active-highlight')
      })
      targetMark.classList.add('active-highlight')
      targetMark.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, 100)
}

// ===== 编辑模式（与文档管理 W4 一致：MD 副本编辑，保存自动重建索引） =====

// 加载当前用户（判断是否超管）
const loadCurrentUser = async () => {
  try {
    currentUser.value = await authService.getCurrentUser()
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

const togglePreviewEdit = async () => {
  if (previewEditMode.value) {
    cancelPreviewEdit()
    return
  }
  if (!previewDocumentData.value) return
  try {
    const { content } = await wikiService.getMarkdown(previewDocumentData.value.document_id)
    previewEditContent.value = content
    previewEditMode.value = true
  } catch (e: any) {
    message.error('加载 MD 副本失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
  }
}

const cancelPreviewEdit = () => {
  previewEditMode.value = false
  previewEditContent.value = ''
}

const savePreviewEdit = async () => {
  if (!previewDocumentData.value) return
  savingPreviewEdit.value = true
  try {
    const result = await wikiService.saveMarkdown(
      previewDocumentData.value.document_id,
      previewEditContent.value
    )
    if (result.success) {
      message.success('已保存并重建索引')
      cancelPreviewEdit()
      // 重新加载预览（内容已更新）
      await loadPreviewContent(previewDocumentData.value.document_id)
    } else {
      message.error('保存失败')
    }
  } catch (e: any) {
    message.error('保存失败：' + (e?.response?.data?.detail || e?.message || '未知错误'))
  } finally {
    savingPreviewEdit.value = false
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

// 下载文档（阶段十六：与文档管理三个下载点统一——选 原文件 / Markdown，走 wiki 下载端点）
const downloadMenuOptions = [
  { label: '下载原文件', key: 'original' },
  { label: '下载 Markdown（AI 编辑版）', key: 'markdown' },
]

const downloadDocument = async (id: number | undefined, type: 'original' | 'markdown' = 'original', title?: string, fileType?: string) => {
  if (!id) {
    message.error('文档ID无效')
    return
  }
  try {
    // 20.7：透传 file_type，header 缺失时兜底纠正扩展名（避免标题日期尾巴带偏，如 2025.12 → .12）
    await downloadWikiDocument(id, type, title || `document_${id}`, fileType)
    message.success(type === 'markdown' ? 'Markdown 已下载' : '原文件已下载')
  } catch (error: any) {
    console.error('下载失败:', error)
    message.error('下载失败' + (error?.message ? `：${error.message}` : ''))
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  documentResults.value = []
  hasSearched.value = false
  totalResults.value = 0
}

// 组件挂载：加载当前用户（编辑按钮需超管判断）
onMounted(() => {
  loadCurrentUser()
  // 29.2：从 OnlyOffice 返回时恢复搜索词 + 滚动位置
  restoreSearchState()
})

// 29.5：预览弹窗打开时,通知 MarkdownPreviewBody 组件做 Ctrl+F 焦点迁移
// (DocumentView 同样加这个 watch——两边统一,行为一致)
watch(showPreviewModal, async (show) => {
  if (!show) return
  await nextTick()
  setTimeout(() => {
    const body = markdownBodyRef.value as { focusForFind?: () => void } | null
    if (body && typeof body.focusForFind === 'function') {
      body.focusForFind()
    }
  }, 250)
})

// 监听预览模式变化
watch(previewMode, async (newMode) => {
  if (!previewDocumentData.value) return

  // 切换模式时退出编辑
  if (previewEditMode.value) {
    cancelPreviewEdit()
  }

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
      
      // 重新处理高亮
      updatePreviewHighlightCount()
    }
  } catch (error) {
    console.error('切换预览模式失败:', error)
    message.error('切换预览模式失败')
  } finally {
    previewLoading.value = false
  }
})

// 29.2：内部锚链接（[text](#anchor)）→ 不再拦截，**让浏览器 native 处理**。
// 29.1 过度工程：preventDefault + scrollIntoView 反倒干扰了浏览器 native 跳转。
// 现代浏览器原生支持 percent-encoded fragment 匹配中文 id。xss-protection.ts 已对内链
// 移除 target=_blank → 同窗口 native jump。这里仅做外部链接兜底。
const handlePreviewAnchorClick = (e: MouseEvent): void => {
  if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
  const target = e.target as HTMLElement | null
  if (!target) return
  const anchor = target.closest('a') as HTMLAnchorElement | null
  if (!anchor) return
  const href = anchor.getAttribute('href') || ''
  // 内部锚链接（#xxx）→ 放行浏览器 native 跳转
  if (href.startsWith('#')) return
  // 外部链接兜底
  if (!anchor.target || anchor.target === '_self') {
    anchor.target = '_blank'
    anchor.rel = 'noopener noreferrer'
  }
}

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

/* 27.17：预览滚动容器——与文档管理 .preview-container 同款原生 overflow:auto，
   宽表格（资产排查统计表这类多列表）超出容器时出现横向滚动条 */
.preview-container {
  width: 100%;
  max-height: 60vh;
  overflow: auto;
  background-color: #ffffff;
  border-radius: 6px;
}

/* 29.1：.markdown-content 样式已抽到全局 frontend/src/assets/markdown.css（与 DocumentView 共享） */

/* 27.17：搜索预览内 img 限宽——原 .markdown-content :deep(img) 规则，全局化后无需重复 */

/* 多词导航卡片 */
.term-nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border: 1.5px solid #d9d9d9;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  transition: box-shadow 0.15s ease, border-color 0.15s ease;
  user-select: none;
}

.term-nav-item:hover {
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.12);
}

.term-nav-active {
  box-shadow: 0 0 0 2px rgba(24, 160, 88, 0.35);
}

.term-nav-label {
  font-weight: 600;
  font-size: 12px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.term-nav-count {
  font-size: 11px;
  color: #999;
}

.term-nav-pos {
  font-size: 11px;
  color: #666;
  min-width: 40px;
  text-align: right;
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