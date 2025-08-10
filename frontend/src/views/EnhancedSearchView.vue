<template>
  <div class="search-view">
    <!-- 搜索头部 -->
    <div class="search-header">
      <n-card>
        <div class="search-form">
          <n-input-group>
            <n-input
              v-model:value="searchQuery"
              placeholder="搜索文档、资产或其他内容..."
              size="large"
              clearable
              @keyup.enter="performSearch"
            >
              <template #prefix>
                <n-icon>
                  <SearchOutlined />
                </n-icon>
              </template>
            </n-input>
            <n-button type="primary" size="large" @click="performSearch" :loading="searching">
              搜索
            </n-button>
          </n-input-group>
          
          <!-- 高级搜索选项 -->
          <div class="search-options">
            <n-space>
              <n-select
                v-model:value="searchType"
                :options="searchTypeOptions"
                placeholder="搜索类型"
                style="width: 120px"
              />
              <n-select
                v-model:value="searchMode"
                :options="searchModeOptions"
                placeholder="搜索模式"
                style="width: 120px"
              />
              <n-date-picker
                v-model:value="dateRange"
                type="daterange"
                placeholder="时间范围"
                clearable
              />
              <n-button quaternary @click="showAdvancedSearch = !showAdvancedSearch">
                <template #icon>
                  <n-icon>
                    <FilterOutlined />
                  </n-icon>
                </template>
                高级筛选
              </n-button>
            </n-space>
          </div>
          
          <!-- 高级搜索面板 -->
          <n-collapse-transition :show="showAdvancedSearch">
            <n-card class="advanced-search" size="small">
              <n-grid :cols="3" :x-gap="16">
                <n-grid-item>
                  <n-form-item label="文件类型">
                    <n-select
                      v-model:value="fileTypes"
                      :options="fileTypeOptions"
                      multiple
                      placeholder="选择文件类型"
                    />
                  </n-form-item>
                </n-grid-item>
                <n-grid-item>
                  <n-form-item label="分类">
                    <n-select
                      v-model:value="categories"
                      :options="categoryOptions"
                      multiple
                      placeholder="选择分类"
                    />
                  </n-form-item>
                </n-grid-item>
                <n-grid-item>
                  <n-form-item label="标签">
                    <n-dynamic-tags v-model:value="tags" />
                  </n-form-item>
                </n-grid-item>
              </n-grid>
            </n-card>
          </n-collapse-transition>
        </div>
      </n-card>
    </div>

    <!-- 搜索结果 -->
    <div class="search-results">
      <n-tabs v-model:value="activeTab" type="line" animated>
        <n-tab-pane name="all" tab="全部">
          <div class="search-summary">
            <span v-if="searchResults.total > 0">
              找到 {{ searchResults.total }} 个结果
            </span>
            <span v-else-if="searchQuery && !searching">
              未找到相关结果
            </span>
          </div>
          
          <n-list v-if="searchResults.items.length > 0">
            <n-list-item
              v-for="item in searchResults.items"
              :key="`${item.type}-${item.id}`"
              class="search-result-item"
            >
              <template #prefix>
                <n-icon size="20" :color="getItemTypeColor(item.type)">
                  <component :is="getItemTypeIcon(item.type)" />
                </n-icon>
              </template>
              
              <n-thing>
                <template #header>
                  <div class="result-header">
                    <n-button text @click="openItem(item)">
                      <span class="result-title" v-html="item.title"></span>
                    </n-button>
                    <n-tag :type="getItemTypeTagType(item.type)" size="small">
                      {{ getItemTypeText(item.type) }}
                    </n-tag>
                  </div>
                </template>
                
                <template #description>
                  <div class="result-description">
                    <div v-if="item.description" class="result-excerpt" v-html="item.description"></div>
                    <div class="result-meta">
                      <span v-if="item.created_at">{{ formatDate(item.created_at) }}</span>
                      <span v-if="item.file_type" class="file-type">{{ item.file_type.toUpperCase() }}</span>
                      <span v-if="item.ip_address" class="ip-address">{{ item.ip_address }}</span>
                    </div>
                  </div>
                </template>
              </n-thing>
              
              <template #suffix>
                <n-space>
                  <n-button size="small" @click="previewItem(item)">
                    <template #icon>
                      <n-icon><EyeOutlined /></n-icon>
                    </template>
                  </n-button>
                  <n-button size="small" @click="shareItem(item)">
                    <template #icon>
                      <n-icon><ShareAltOutlined /></n-icon>
                    </template>
                  </n-button>
                </n-space>
              </template>
            </n-list-item>
          </n-list>
          
          <!-- 空状态 -->
          <n-empty
            v-else-if="searchQuery && !searching"
            description="未找到相关内容"
            size="large"
          >
            <template #extra>
              <n-button @click="clearSearch">清空搜索</n-button>
            </template>
          </n-empty>
          
          <!-- 分页 -->
          <div v-if="searchResults.total > pageSize" class="pagination">
            <n-pagination
              v-model:page="currentPage"
              :page-count="Math.ceil(searchResults.total / pageSize)"
              :page-size="pageSize"
              show-size-picker
              :page-sizes="[10, 20, 50]"
              show-quick-jumper
              @update:page="handlePageChange"
              @update:page-size="handlePageSizeChange"
            />
          </div>
        </n-tab-pane>
        
        <n-tab-pane name="documents" tab="文档">
          <document-search-results
            :results="documentResults"
            :loading="searching"
            @open="openItem"
            @preview="previewItem"
          />
        </n-tab-pane>
        
        <n-tab-pane name="assets" tab="资产">
          <asset-search-results
            :results="assetResults"
            :loading="searching"
            @open="openItem"
            @preview="previewItem"
          />
        </n-tab-pane>
      </n-tabs>
    </div>

    <!-- 预览模态框 -->
    <n-modal v-model:show="showPreview" preset="card" style="width: 800px">
      <template #header>
        {{ previewItem?.title }}
      </template>
      <div v-if="previewItem" class="preview-content">
        <!-- 文档预览 -->
        <div v-if="previewItem.type === 'document'" class="document-preview">
          <div class="preview-meta">
            <n-descriptions :column="2" size="small">
              <n-descriptions-item label="文件类型">
                {{ previewItem.file_type }}
              </n-descriptions-item>
              <n-descriptions-item label="创建时间">
                {{ formatDate(previewItem.created_at) }}
              </n-descriptions-item>
              <n-descriptions-item label="文件大小">
                {{ formatFileSize(previewItem.file_size) }}
              </n-descriptions-item>
              <n-descriptions-item label="查看次数">
                {{ previewItem.view_count || 0 }}
              </n-descriptions-item>
            </n-descriptions>
          </div>
          <n-divider />
          <div class="preview-text">
            {{ previewItem.content || previewItem.description || '无可预览内容' }}
          </div>
        </div>
        
        <!-- 资产预览 -->
        <div v-else-if="previewItem.type === 'asset'" class="asset-preview">
          <n-descriptions :column="2" size="small">
            <n-descriptions-item label="设备类型">
              {{ previewItem.asset_type }}
            </n-descriptions-item>
            <n-descriptions-item label="IP地址">
              {{ previewItem.ip_address }}
            </n-descriptions-item>
            <n-descriptions-item label="主机名">
              {{ previewItem.hostname }}
            </n-descriptions-item>
            <n-descriptions-item label="状态">
              <n-tag :type="getAssetStatusType(previewItem.status)">
                {{ getAssetStatusText(previewItem.status) }}
              </n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="所属部门">
              {{ previewItem.department }}
            </n-descriptions-item>
            <n-descriptions-item label="备注">
              {{ previewItem.notes || '无' }}
            </n-descriptions-item>
          </n-descriptions>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  NCard,
  NInput,
  NInputGroup,
  NButton,
  NIcon,
  NSpace,
  NSelect,
  NDatePicker,
  NCollapseTransition,
  NGrid,
  NGridItem,
  NFormItem,
  NDynamicTags,
  NTabs,
  NTabPane,
  NList,
  NListItem,
  NThing,
  NTag,
  NEmpty,
  NPagination,
  NModal,
  NDescriptions,
  NDescriptionsItem,
  NDivider,
  useMessage
} from 'naive-ui'
import {
  SearchOutlined,
  FilterOutlined,
  EyeOutlined,
  ShareAltOutlined,
  FileTextOutlined,
  DesktopOutlined,
  FolderOutlined
} from '@vicons/antd'
import { apiService } from '@/services'

const route = useRoute()
const router = useRouter()
const message = useMessage()

// 响应式数据
const searchQuery = ref('')
const searching = ref(false)
const showAdvancedSearch = ref(false)
const searchType = ref('all')
const searchMode = ref('quick')
const dateRange = ref(null)
const fileTypes = ref([])
const categories = ref([])
const tags = ref([])
const activeTab = ref('all')
const currentPage = ref(1)
const pageSize = ref(20)
const showPreview = ref(false)
const previewItem = ref(null)

const searchResults = ref({
  total: 0,
  items: []
})

const documentResults = ref([])
const assetResults = ref([])

// 选项数据
const searchTypeOptions = [
  { label: '全部', value: 'all' },
  { label: '文档', value: 'documents' },
  { label: '资产', value: 'assets' }
]

const searchModeOptions = [
  { label: '快速搜索', value: 'quick' },
  { label: '精确搜索', value: 'exact' },
  { label: '模糊匹配', value: 'fuzzy' }
]

const fileTypeOptions = [
  { label: 'PDF', value: 'pdf' },
  { label: 'Word文档', value: 'docx' },
  { label: 'Excel表格', value: 'xlsx' },
  { label: '文本文件', value: 'txt' },
  { label: 'Markdown', value: 'md' }
]

const categoryOptions = ref([])

// 方法
const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    message.warning('请输入搜索关键词')
    return
  }

  searching.value = true
  
  try {
    const params = {
      q: searchQuery.value,
      type: searchType.value,
      mode: searchMode.value,
      page: currentPage.value,
      size: pageSize.value
    }

    // 添加高级搜索参数
    if (fileTypes.value.length > 0) {
      params.file_types = fileTypes.value.join(',')
    }
    if (categories.value.length > 0) {
      params.categories = categories.value.join(',')
    }
    if (tags.value.length > 0) {
      params.tags = tags.value.join(',')
    }
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }

    const response = await apiService.get('/search', { params })
    
    searchResults.value = {
      total: response.total || 0,
      items: response.items || []
    }

    // 分类结果
    documentResults.value = response.items?.filter(item => item.type === 'document') || []
    assetResults.value = response.items?.filter(item => item.type === 'asset') || []

    // 更新URL
    router.push({
      name: 'search',
      query: { q: searchQuery.value, type: searchType.value }
    })

  } catch (error) {
    console.error('搜索失败:', error)
    message.error('搜索失败')
  } finally {
    searching.value = false
  }
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = { total: 0, items: [] }
  documentResults.value = []
  assetResults.value = []
  currentPage.value = 1
}

const openItem = (item: any) => {
  if (item.type === 'document') {
    router.push(`/documents/${item.id}`)
  } else if (item.type === 'asset') {
    router.push(`/assets/${item.id}`)
  }
}

const previewItem = (item: any) => {
  previewItem.value = item
  showPreview.value = true
}

const shareItem = (item: any) => {
  const url = `${window.location.origin}/${item.type}s/${item.id}`
  navigator.clipboard.writeText(url).then(() => {
    message.success('链接已复制到剪贴板')
  })
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  performSearch()
}

const handlePageSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  performSearch()
}

const getItemTypeIcon = (type: string) => {
  const icons = {
    document: FileTextOutlined,
    asset: DesktopOutlined,
    category: FolderOutlined
  }
  return icons[type] || FileTextOutlined
}

const getItemTypeColor = (type: string) => {
  const colors = {
    document: '#1890ff',
    asset: '#52c41a',
    category: '#fa8c16'
  }
  return colors[type] || '#d9d9d9'
}

const getItemTypeText = (type: string) => {
  const texts = {
    document: '文档',
    asset: '资产',
    category: '分类'
  }
  return texts[type] || '未知'
}

const getItemTypeTagType = (type: string) => {
  const types = {
    document: 'info',
    asset: 'success',
    category: 'warning'
  }
  return types[type] || 'default'
}

const getAssetStatusType = (status: string) => {
  const types = {
    active: 'success',
    inactive: 'warning',
    maintenance: 'info',
    retired: 'error'
  }
  return types[status] || 'default'
}

const getAssetStatusText = (status: string) => {
  const texts = {
    active: '在用',
    inactive: '停用',
    maintenance: '维护中',
    retired: '已退役'
  }
  return texts[status] || '未知'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString()
}

const formatFileSize = (size: number) => {
  if (!size) return '未知'
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index++
  }
  return `${size.toFixed(1)} ${units[index]}`
}

// 生命周期
onMounted(() => {
  // 从URL获取搜索参数
  const query = route.query.q as string
  if (query) {
    searchQuery.value = query
    searchType.value = (route.query.type as string) || 'all'
    performSearch()
  }
})

// 监听路由变化
watch(() => route.query, (newQuery) => {
  if (newQuery.q && newQuery.q !== searchQuery.value) {
    searchQuery.value = newQuery.q as string
    performSearch()
  }
})
</script>

<style scoped>
.search-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.search-header {
  margin-bottom: 24px;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-options {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.advanced-search {
  margin-top: 16px;
}

.search-results {
  flex: 1;
  overflow: hidden;
}

.search-summary {
  padding: 16px 0;
  color: #666;
  font-size: 14px;
}

.search-result-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.search-result-item:hover {
  background-color: #f9f9f9;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.result-title {
  font-weight: 500;
  color: #1890ff;
  cursor: pointer;
}

.result-title:hover {
  text-decoration: underline;
}

.result-description {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.result-excerpt {
  color: #666;
  line-height: 1.5;
}

.result-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}

.file-type,
.ip-address {
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 4px;
}

.pagination {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}

.preview-content {
  max-height: 500px;
  overflow-y: auto;
}

.preview-meta {
  margin-bottom: 16px;
}

.preview-text {
  white-space: pre-wrap;
  line-height: 1.6;
  color: #333;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-form {
    gap: 12px;
  }
  
  .search-options {
    flex-direction: column;
    align-items: stretch;
  }
  
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>