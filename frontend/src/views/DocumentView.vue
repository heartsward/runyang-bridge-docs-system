<template>
  <PageLayout title="润扬大桥运维文档管理系统">
    <template #header-actions>
      <n-input
        v-model:value="searchQuery"
        placeholder="搜索文档..."
        style="width: 300px"
        clearable
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>
      <n-button 
        v-if="currentUser?.is_superuser" 
        type="primary" 
        @click="showUploadModal = true"
        style="color: white; background-color: #18a058;"
      >
        <template #icon>
          <n-icon :component="CloudUploadOutline" />
        </template>
        上传文档
      </n-button>
    </template>

    <!-- 统计信息和标签筛选 -->
    <n-card style="margin-bottom: 24px;">
      <n-space vertical size="medium">
        <!-- 第一行：统计信息 -->
        <n-space justify="space-between" align="center">
          <n-statistic label="总文档数" :value="statistics.total_count">
            <template #prefix>
              <n-icon :component="DocumentTextOutline" />
            </template>
          </n-statistic>
        </n-space>
        
        <!-- 第二行：标签筛选 -->
        <div v-if="allTags.length > 0">
          <n-space align="center" wrap>
            <n-text depth="3" style="white-space: nowrap;">按标签筛选:</n-text>
            <n-space wrap>
              <n-tag 
                v-for="tag in allTags.slice(0, 10)" 
                :key="tag" 
                size="small" 
                type="default"
                :style="{
                  cursor: 'pointer',
                  backgroundColor: selectedTags.includes(tag) ? '#e8f4fd' : '',
                  borderColor: selectedTags.includes(tag) ? '#409eff' : '',
                  color: selectedTags.includes(tag) ? '#409eff' : '',
                  fontWeight: selectedTags.includes(tag) ? 'bold' : 'normal',
                  transition: 'all 0.3s ease'
                }"
                @click="toggleTagFilter(tag)"
              >
                {{ tag }} ({{ getTagCount(tag) }})
              </n-tag>
              <n-button size="tiny" type="error" @click="clearTagFilters" v-if="selectedTags.length > 0">
                清除筛选 ({{ selectedTags.length }})
              </n-button>
            </n-space>
          </n-space>
          <!-- 显示当前筛选状态 -->
          <div v-if="selectedTags.length > 0" style="margin-top: 8px;">
            <n-text depth="2" style="font-size: 12px;">
              当前筛选: {{ selectedTags.join(' + ') }} 
              (显示 {{ filteredDocuments.length }} 个文档)
            </n-text>
          </div>
        </div>
      </n-space>
    </n-card>

    <!-- 文档列表 -->
    <div v-if="loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
      <div style="margin-top: 16px;">
        <n-text depth="3">加载中...</n-text>
      </div>
    </div>

    <div v-else-if="filteredDocuments.length === 0" style="text-align: center; padding: 40px;">
      <n-empty description="暂无文档">
        <template #extra>
          <n-button 
            v-if="currentUser?.is_superuser" 
            type="primary" 
            @click="showUploadModal = true"
            style="color: white; background-color: #18a058;"
          >
            <template #icon>
              <n-icon :component="CloudUploadOutline" />
            </template>
            上传第一个文档
          </n-button>
        </template>
      </n-empty>
    </div>

    <div v-else>
      <n-data-table
        :columns="columns"
        :data="filteredDocuments"
        :pagination="{
          page: pagination.page,
          pageSize: pagination.pageSize,
          itemCount: filteredDocuments.length,
          showSizePicker: true,
          pageSizes: [10, 20, 50, 100],
          showQuickJumper: true,
          prefix: ({ itemCount }) => `共 ${itemCount} 个文档`
        }"
        :loading="loading"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>
  </PageLayout>

  <!-- 上传文档模态框 -->
  <n-modal v-model:show="showUploadModal" preset="card" style="width: 800px" title="上传文档">
    <n-form ref="formRef" :model="uploadForm" :rules="rules">
      <n-form-item label="文档标题" path="title" v-show="fileList.length <= 1">
        <n-input 
          v-model:value="uploadForm.title" 
          placeholder="请输入文档标题（选择文件后会自动填充）" 
          clearable
        />
      </n-form-item>
      <n-alert type="info" v-show="fileList.length > 1" style="margin-bottom: 16px;">
        批量上传模式：将使用文件名作为文档标题，统一描述和标签将应用于所有文档
      </n-alert>
      <n-form-item label="标签" path="tags">
        <n-select
          v-model:value="uploadForm.tags"
          multiple
          filterable
          tag
          :options="tagOptions"
          placeholder="选择已有标签或输入新标签"
          :show-arrow="false"
          :max-tag-count="3"
        />
        <n-text depth="3" style="font-size: 12px; margin-top: 4px;">
          可以选择已有标签或输入新标签，支持多选
        </n-text>
      </n-form-item>
      <n-form-item label="描述" path="description">
        <n-input
          v-model:value="uploadForm.description"
          type="textarea"
          placeholder="请输入统一描述（单文件时可留空，批量上传时作为默认描述）"
          :rows="3"
        />
      </n-form-item>
      <n-form-item label="文档文件">
        <n-upload
          :file-list="fileList"
          multiple
          @update:file-list="handleFileChange"
          accept=".pdf,.doc,.docx,.txt,.md,.xls,.xlsx,.csv"
        >
          <n-button>
            <template #icon>
              <n-icon>
                <svg viewBox="0 0 24 24">
                  <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
              </n-icon>
            </template>
            选择文件（支持多文件）
          </n-button>
        </n-upload>
        <n-text depth="3" style="font-size: 12px; margin-top: 4px;">
          支持格式：PDF、DOC、DOCX、TXT、MD、XLS、XLSX、CSV，支持多文件同时选择
        </n-text>
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showUploadModal = false">取消</n-button>
        <n-button type="primary" @click="uploadDocument" :loading="uploading">
          上传
        </n-button>
      </n-space>
    </template>
  </n-modal>

  <!-- 文档预览模态框 -->
  <n-modal v-model:show="showPreviewModal" preset="card" style="width: 90%; height: 85%; max-width: 1200px;" :title="`预览文档 - ${currentDocument?.title || ''}`">
    <div v-if="previewLoading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
      <div style="margin-top: 16px;">加载中...</div>
    </div>
    <div v-else>
      <n-scrollbar style="max-height: 70vh;">
        <pre style="white-space: pre-wrap; word-wrap: break-word; font-family: monospace; font-size: 13px; line-height: 1.8; padding: 16px; background-color: #fafafa; border-radius: 4px;">{{ previewContent }}</pre>
      </n-scrollbar>
    </div>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showPreviewModal = false">关闭</n-button>
        <n-button type="primary" @click="downloadDocument(currentDocument!)" v-if="currentDocument">下载</n-button>
      </n-space>
    </template>
  </n-modal>

  <!-- 文档详情模态框 -->
  <n-modal v-model:show="showDetailModal" preset="card" style="width: 600px;" :title="`文档详情 - ${currentDocument?.title || ''}`">
    <div v-if="currentDocument">
      <n-descriptions bordered :column="1">
        <n-descriptions-item label="文档标题">{{ currentDocument.title }}</n-descriptions-item>
        <n-descriptions-item label="文档描述">{{ currentDocument.description || '暂无描述' }}</n-descriptions-item>
        <n-descriptions-item label="文件类型">{{ currentDocument.file_type?.toUpperCase() || 'TXT' }}</n-descriptions-item>
        <n-descriptions-item label="文件大小">{{ formatFileSize(currentDocument.file_size) }}</n-descriptions-item>
        <n-descriptions-item label="标签">
          <n-space v-if="currentDocument.tags && currentDocument.tags.length > 0">
            <n-tag v-for="tag in currentDocument.tags" :key="tag" size="small" type="info">{{ tag }}</n-tag>
          </n-space>
          <span v-else>暂无标签</span>
        </n-descriptions-item>
        <n-descriptions-item label="AI摘要" v-if="currentDocument.ai_summary">
          <n-text>{{ currentDocument.ai_summary }}</n-text>
        </n-descriptions-item>
        <n-descriptions-item label="创建时间">{{ formatDate(currentDocument.created_at) }}</n-descriptions-item>
        <n-descriptions-item label="更新时间">{{ formatDate(currentDocument.updated_at) }}</n-descriptions-item>
      </n-descriptions>
    </div>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showDetailModal = false">关闭</n-button>
        <n-button type="primary" @click="previewDocument(currentDocument!)" v-if="currentDocument">预览</n-button>
        <n-button type="info" @click="downloadDocument(currentDocument!)" v-if="currentDocument">下载</n-button>
      </n-space>
    </template>
  </n-modal>

  <!-- 文件名冲突解决模态框 -->
  <n-modal v-model:show="showConflictModal" preset="card" style="width: 700px;" title="文件名冲突处理">
    <div v-if="conflictFiles.length > 0">
      <n-alert type="warning" style="margin-bottom: 16px;">
        <template #header>发现文件名冲突</template>
        以下文件名已存在于系统中，请选择处理方式：
      </n-alert>
      
      <n-space vertical size="medium">
        <div v-for="(conflict, index) in conflictFiles" :key="index" style="border: 1px solid #f0f0f0; border-radius: 8px; padding: 16px;">
          <n-space vertical size="small">
            <!-- 冲突文件信息 -->
            <div>
              <n-text strong>{{ conflict.originalName }}</n-text>
              <n-tag type="error" size="small" style="margin-left: 8px;">
                已存在 {{ conflict.count }} 个同名文档
              </n-tag>
            </div>
            
            <!-- 现有文档列表 -->
            <div v-if="conflict.existingDocuments && conflict.existingDocuments.length > 0">
              <n-text depth="3" style="font-size: 12px;">现有同名文档：</n-text>
              <div style="margin-left: 16px; margin-top: 4px;">
                <div v-for="doc in conflict.existingDocuments" :key="doc.id" style="font-size: 12px; color: #666; margin-bottom: 2px;">
                  • {{ doc.title }} ({{ formatDate(doc.created_at) }})
                </div>
              </div>
            </div>
            
            <!-- 处理选项 -->
            <n-space align="center">
              <n-radio-group v-model:value="conflict.action" size="small">
                <n-space>
                  <n-radio value="auto">自动重命名</n-radio>
                  <n-radio value="manual">手动重命名</n-radio>
                  <n-radio value="overwrite">覆盖上传</n-radio>
                </n-space>
              </n-radio-group>
            </n-space>
            
            <!-- 手动重命名输入框 -->
            <div v-if="conflict.action === 'manual'">
              <n-input 
                v-model:value="conflict.newName" 
                placeholder="请输入新的文件名"
                style="margin-top: 8px;"
                @blur="validateNewFilename(conflict)"
              />
              <n-text v-if="conflict.nameError" type="error" style="font-size: 12px; margin-top: 4px;">
                {{ conflict.nameError }}
              </n-text>
            </div>
            
            <!-- 预览信息 -->
            <div style="background-color: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 12px;">
              <n-text depth="2">
                处理方式: 
                <span v-if="conflict.action === 'auto'">
                  系统将自动生成唯一文件名（如: <strong>{{ getAutoRenameExample(conflict.originalName) }}</strong>）
                </span>
                <span v-else-if="conflict.action === 'manual'">使用新文件名: {{ conflict.newName || '请输入新文件名' }}</span>
                <span v-else-if="conflict.action === 'overwrite'" style="color: #d03050;">⚠️ 将覆盖现有文档（谨慎操作）</span>
              </n-text>
            </div>
          </n-space>
        </div>
      </n-space>
    </div>
    
    <template #footer>
      <n-space justify="end">
        <n-button @click="cancelConflictResolution">取消上传</n-button>
        <n-button type="primary" @click="applyConflictResolution" :disabled="!canProceedWithConflictResolution">
          应用并继续上传
        </n-button>
      </n-space>
    </template>
  </n-modal>

  <!-- 编辑文档模态框 -->
  <n-modal v-model:show="showEditModal" preset="card" style="width: 600px;" :title="`编辑文档 - ${currentDocument?.title || ''}`">
    <n-form ref="editFormRef" :model="editForm" :rules="rules" v-if="currentDocument">
      <n-form-item label="文档标题" path="title">
        <n-input v-model:value="editForm.title" placeholder="请输入文档标题" />
      </n-form-item>
      <n-form-item label="标签管理" path="tags">
        <n-select
          v-model:value="editForm.tags"
          multiple
          filterable
          tag
          :options="tagOptions"
          placeholder="选择已有标签或输入新标签"
          :show-arrow="false"
          :max-tag-count="5"
        />
        <n-text depth="3" style="font-size: 12px; margin-top: 4px;">
          可以选择已有标签或输入新标签，支持多选
        </n-text>
      </n-form-item>
      <n-form-item label="文档描述" path="description">
        <n-input
          v-model:value="editForm.description"
          type="textarea"
          placeholder="请输入文档描述"
          :rows="3"
        />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="saveDocumentEdit" :loading="editLoading">保存</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, h, watch } from 'vue'
import {
  NSpace,
  NInput,
  NButton,
  NIcon,
  NCard,
  NTag,
  NText,
  NModal,
  NForm,
  NFormItem,
  NSelect,
  NUpload,
  NSpin,
  NEmpty,
  NDataTable,
  NStatistic,
  NScrollbar,
  NDescriptions,
  NDescriptionsItem,
  NProgress,
  NAlert,
  NRadioGroup,
  NRadio,
  useMessage,
  useDialog
} from 'naive-ui'
import { SearchOutline, CloudUploadOutline, DocumentTextOutline, SparklesOutline } from '@vicons/ionicons5'
import PageLayout from '../components/PageLayout.vue'
import { documentService, uploadService, authService, taskService, analyticsService } from '@/services'
import type { Document, Category, User } from '@/types/api'
import apiService from '@/services/api'
import { debounce } from '@/utils'

const message = useMessage()
const dialog = useDialog()
const searchQuery = ref('')
const debouncedSearchQuery = ref('')
const showUploadModal = ref(false)
const showConflictModal = ref(false)
const uploading = ref(false)
const loading = ref(false)
const selectedTags = ref<string[]>([])
const conflictFiles = ref<any[]>([])

// 当前用户状态
const currentUser = ref<User | null>(null)

// 预览和详情相关
const showPreviewModal = ref(false)
const showDetailModal = ref(false)
const showEditModal = ref(false)
const previewContent = ref('')
const previewLoading = ref(false)
const currentDocument = ref<Document | null>(null)
const editLoading = ref(false)

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0
})

// 文档统计
const statistics = ref({
  total_count: 0
})

const uploadForm = ref({
  title: '',
  description: '',
  tags: [] as string[]
})

const editForm = ref({
  title: '',
  description: '',
  tags: [] as string[]
})

const fileList = ref<any[]>([])

const rules = {
  title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }]
}

const documents = ref<Document[]>([])


const allTags = computed(() => {
  const tagSet = new Set<string>()
  documents.value.forEach(doc => {
    if (doc.tags && Array.isArray(doc.tags)) {
      doc.tags.forEach(tag => tagSet.add(tag))
    }
  })
  return Array.from(tagSet).sort()
})

const tagOptions = computed(() => {
  return allTags.value.map(tag => ({
    label: tag,
    value: tag
  }))
})

// 使用防抖搜索优化性能

const debouncedUpdateSearch = debounce((query: string) => {
  debouncedSearchQuery.value = query
}, 300)

// 监听搜索输入，应用防抖
watch(searchQuery, (newQuery) => {
  debouncedUpdateSearch(newQuery)
})

const filteredDocuments = computed(() => {
  let filtered = documents.value
  
  // 按搜索关键词过滤 - 使用防抖后的查询
  if (debouncedSearchQuery.value) {
    const query = debouncedSearchQuery.value.toLowerCase()
    filtered = filtered.filter(doc =>
      doc.title.toLowerCase().includes(query) ||
      (doc.description && doc.description.toLowerCase().includes(query))
    )
  }
  
  // 按标签过滤
  if (selectedTags.value.length > 0) {
    filtered = filtered.filter(doc => {
      if (!doc.tags || !Array.isArray(doc.tags)) return false
      return selectedTags.value.every(selectedTag => doc.tags.includes(selectedTag))
    })
  }
  
  return filtered
})

const getTagCount = (tag: string) => {
  return documents.value.filter(doc => 
    doc.tags && Array.isArray(doc.tags) && doc.tags.includes(tag)
  ).length
}

const toggleTagFilter = (tag: string) => {
  const index = selectedTags.value.indexOf(tag)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push(tag)
  }
}

const clearTagFilters = () => {
  selectedTags.value = []
}

// 表格列定义
const columns = [
  {
    title: '文档标题',
    key: 'title',
    width: 200,
    ellipsis: true,
    render: (row: Document) => h(
      'div',
      { 
        style: { cursor: 'pointer' },
        onClick: () => showDocumentDetail(row)
      },
      [
        h('div', { style: { fontWeight: '600', fontSize: '14px', marginBottom: '4px' } }, row.title),
        h('div', { style: { color: '#999', fontSize: '12px', marginBottom: '4px' } }, row.description || '暂无描述'),
        // 显示用户标签
        row.tags && row.tags.length > 0 ? h(
          'div',
          { style: { marginTop: '4px' } },
          row.tags.slice(0, 3).map((tag: string) => 
            h(NTag, {
              size: 'small',
              type: 'info',
              style: { marginRight: '4px', fontSize: '10px' }
            }, {
              default: () => tag
            })
          )
        ) : null,
        // 显示AI摘要（如果有的话）
        row.ai_summary ? h(
          'div',
          { style: { marginTop: '4px', fontSize: '11px', color: '#666', fontStyle: 'italic' } },
          row.ai_summary.length > 50 ? row.ai_summary.substring(0, 50) + '...' : row.ai_summary
        ) : null
      ]
    )
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row: Document) => h(
      NTag,
      { 
        type: 'success', 
        size: 'small' 
      },
      () => '已发布'
    )
  },
  {
    title: '文件类型',
    key: 'file_type',
    width: 80,
    render: (row: Document) => h(
      NTag,
      { size: 'small', type: 'info' },
      () => row.file_type?.toUpperCase() || 'TXT'
    )
  },
  {
    title: '文件大小',
    key: 'file_size',
    width: 90,
    render: (row: Document) => h(
      'span',
      { style: { fontSize: '12px', color: '#666' } },
      formatFileSize(row.file_size)
    )
  },
  {
    title: '内容提取',
    key: 'content_extraction',
    width: 120,
    render: (row: Document) => {
      if (row.content_extracted === true) {
        return h(NTag, { 
          type: 'success',
          size: 'small'
        }, { default: () => '已完成' })
      } else if (row.content_extracted === false) {
        return h(NTag, { 
          type: 'error',
          size: 'small'
        }, { default: () => '失败' })
      } else {
        return h(NTag, { 
          type: 'warning',
          size: 'small'
        }, { default: () => '提取中' })
      }
    }
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 120,
    render: (row: Document) => formatDate(row.created_at)
  },
  {
    title: '操作',
    key: 'actions',
    width: 180,
    render: (row: Document) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, {
          size: 'small',
          type: 'primary',
          style: 'color: white; background-color: #18a058;',
          onClick: () => previewDocument(row)
        }, {
          default: () => '预览'
        }),
        h(NButton, {
          size: 'small',
          type: 'info',
          onClick: () => downloadDocument(row)
        }, {
          default: () => '下载'
        }),
        // 只有管理员才能看到编辑和删除按钮
        ...(currentUser.value?.is_superuser ? [
          h(NButton, {
            size: 'small',
            type: 'warning',
            onClick: () => editDocument(row)
          }, {
            default: () => '编辑'
          }),
          h(NButton, {
            size: 'small',
            type: 'error',
            onClick: () => deleteDocument(row)
          }, {
            default: () => '删除'
          })
        ] : [])
      ]
    })
  }
]

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 格式化文件大小
const formatFileSize = (bytes: number | null | undefined): string => {
  if (!bytes || bytes === 0) return '未知'
  
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  
  if (i === 0) return `${bytes} B`
  
  const size = (bytes / Math.pow(1024, i)).toFixed(1)
  return `${size} ${sizes[i]}`
}

const openUploadModal = () => {
  uploadForm.value = {
    title: '',
    description: '',
    tags: []
  }
  fileList.value = []
  showUploadModal.value = true
}

const handleFileChange = async (files: any[]) => {
  fileList.value = files
  
  if (files.length === 1) {
    // 单文件时自动填充标题
    const fileName = files[0].file.name
    const titleWithoutExt = fileName.replace(/\.[^/.]+$/, '')
    uploadForm.value.title = titleWithoutExt
  } else if (files.length > 1) {
    // 多文件时清空标题，提示批量上传
    uploadForm.value.title = `批量上传 ${files.length} 个文档`
  } else {
    uploadForm.value.title = ''
  }
}

const uploadDocument = async () => {
  if (fileList.value.length === 0) {
    message.error('请选择要上传的文件')
    return
  }

  // 检查文件名冲突
  const hasConflicts = await checkFilenameConflicts()
  if (hasConflicts) {
    return // 如果有冲突且用户取消，则停止上传
  }

  uploading.value = true
  
  try {
    // 判断是单文件上传还是多文件上传
    if (fileList.value.length === 1) {
      // 单文件上传
      const fileItem = fileList.value[0]
      const title = fileItem.renamedName ? 
        fileItem.renamedName.replace(/\.[^/.]+$/, '') : // 使用重命名后的标题
        uploadForm.value.title // 使用用户输入的标题
      
      console.log(`单文件上传: 原始名称="${fileItem.file.name}", 重命名="${fileItem.renamedName}", 最终标题="${title}"`)
      
      const result = await uploadService.uploadFile({
        file: fileItem.file,
        title: title,
        description: uploadForm.value.description,
        tags: uploadForm.value.tags.join(',')
      })
      
      message.success('文档上传成功，正在提取内容...')
      
      // 开始监控提取状态
      if (result && result.id) {
        monitorContentExtraction(result.id)
      }
    } else {
      // 多文件上传 - 使用单文件接口逐个上传
      const files = fileList.value.map(item => item.file)
      const results = []
      let successCount = 0
      
      message.info(`开始上传 ${files.length} 个文档...`)
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const fileItem = fileList.value.find(item => item.file === file)
        
        try {
          // 使用重命名后的文件名或原始文件名
          const fileName = fileItem && fileItem.renamedName ? fileItem.renamedName : file.name
          const titleWithoutExt = fileName.replace(/\.[^/.]+$/, '')
          
          console.log(`上传文件: 原始名称="${file.name}", 处理后名称="${fileName}", 标题="${titleWithoutExt}"`)
          
          const result = await uploadService.uploadFile({
            file: file,
            title: titleWithoutExt, // 使用处理后的标题
            description: uploadForm.value.description,
            tags: uploadForm.value.tags.join(',')
          })
          
          results.push(result)
          successCount++
          
          // 开始监控提取状态
          if (result && result.id) {
            monitorContentExtraction(result.id)
          }
          
          message.success(`文档 "${fileName}" 上传成功 (${successCount}/${files.length})`)
          
        } catch (error) {
          const fileName = fileItem && fileItem.renamedName ? fileItem.renamedName : file.name
          console.error(`上传文档 "${fileName}" 失败:`, error)
          message.error(`文档 "${fileName}" 上传失败`)
        }
      }
      
      if (successCount > 0) {
        message.success(`成功上传 ${successCount} 个文档，正在提取内容...`)
      }
    }
    
    showUploadModal.value = false
    uploadForm.value = { title: '', description: '', tags: [] }
    fileList.value = []
    
    // 重新加载文档列表
    await loadDocuments()
    
  } catch (error: any) {
    console.error('文档上传失败:', error)
    message.error('文档上传失败')
  } finally {
    uploading.value = false
  }
}

// 监控内容提取状态
const monitorContentExtraction = async (documentId: number) => {
  const maxAttempts = 30 // 最多检查30次（约5分钟）
  let attempts = 0
  
  const checkStatus = async () => {
    try {
      const status = await taskService.getDocumentExtractionStatus(documentId)
      
      // 检查返回的状态是否有效
      if (!status || typeof status.status === 'undefined') {
        console.warn('提取状态API返回无效数据:', status)
        // 如果返回null或无效数据，可能是文档还没有提取任务，先停止监控
        message.info('文档内容提取任务尚未开始或已完成，请刷新页面查看最新状态')
        return
      }
      
      // 更新文档列表中的对应文档状态
      const docIndex = documents.value.findIndex(doc => doc.id === documentId)
      if (docIndex !== -1) {
        if (status.status === 'completed') {
          documents.value[docIndex].content_extracted = true
          message.success(`文档"${documents.value[docIndex].title}"内容提取完成`)
          return
        } else if (status.status === 'failed') {
          documents.value[docIndex].content_extracted = false
          message.error(`文档"${documents.value[docIndex].title}"内容提取失败: ${status.error || '未知错误'}`)
          return
        } else if (status.status === 'processing' || status.status === 'pending') {
          // 确保在处理中时，状态设置为null（显示"提取中"）
          documents.value[docIndex].content_extracted = null
        }
      }
      
      // 如果还在处理中，继续检查
      if (status.status === 'processing' || status.status === 'pending') {
        attempts++
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 10000) // 10秒后再次检查
        } else {
          message.warning('内容提取超时，请手动刷新页面查看状态')
        }
      }
    } catch (error) {
      console.error('检查提取状态失败:', error)
      attempts++
      if (attempts < maxAttempts) {
        setTimeout(checkStatus, 10000) // 出错后10秒重试
      }
    }
  }
  
  // 开始第一次检查
  setTimeout(checkStatus, 5000) // 5秒后开始检查
}

// 分页处理函数
const handlePageChange = (page: number) => {
  pagination.page = page
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
}

// 更新统计数据
const updateStatistics = () => {
  const docs = documents.value
  statistics.value = {
    total_count: docs.length
  }
  
  // 更新分页总数
  pagination.itemCount = filteredDocuments.value.length
}

// 显示文档详情
const showDocumentDetail = async (document: Document) => {
  try {
    // 调用后端API获取完整的文档详情，这将自动增加查看次数
    const fullDocument = await documentService.getDocument(document.id)
    currentDocument.value = fullDocument
    showDetailModal.value = true
    
    // 更新本地文档列表中的查看次数
    const index = documents.value.findIndex(doc => doc.id === document.id)
    if (index !== -1) {
      documents.value[index].view_count = fullDocument.view_count
    }
  } catch (error) {
    console.error('获取文档详情失败:', error)
    // 如果API调用失败，仍然显示现有的文档信息
    currentDocument.value = document
    showDetailModal.value = true
    message.error('获取文档详情失败')
  }
}

// 预览文档
const previewDocument = async (document: Document) => {
  currentDocument.value = document
  showPreviewModal.value = true
  previewLoading.value = true
  previewContent.value = ''
  
  const startTime = Date.now()
  
  try {
    // 调用搜索API的预览端点
    const data = await apiService.get(`/search/preview/${document.id}`)
    previewContent.value = data.content || '无法获取文档内容'
    
    // 文档访问统计已在后端预览API中自动记录，无需前端额外调用
  } catch (error) {
    console.error('预览文档失败:', error)
    previewContent.value = '无法获取文档内容'
    message.error('预览失败')
  } finally {
    previewLoading.value = false
  }
}

// 下载文档
const downloadDocument = async (doc: Document) => {
  try {
    // 使用fetch获取文件，然后创建安全的下载
    // 检测当前访问环境，如果是本地访问就使用localhost，避免CORS问题
    const currentHost = window.location.hostname
    let apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002'
    
    // 如果当前访问是localhost但配置的API是其他IP，改为localhost避免CORS
    if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
      apiBaseUrl = 'http://localhost:8002'
    }
    
    const token = localStorage.getItem('access_token')
    
    const response = await fetch(`${apiBaseUrl}/api/v1/documents/${doc.id}/download`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      throw new Error(`下载失败: ${response.status}`)
    }
    
    // 获取文件数据 - 保持原始响应类型
    const blob = await response.blob()
    
    // 创建安全的下载链接
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 尝试从响应头获取文件名，否则使用文档标题
    let filename = doc.title
    const contentDisposition = response.headers.get('content-disposition')
    
    if (contentDisposition) {
      // 更严格的文件名解析
      const filenameMatch = contentDisposition.match(/filename\*?=['"]?([^'"\r\n]*)['"]?/i)
      if (filenameMatch && filenameMatch[1]) {
        filename = decodeURIComponent(filenameMatch[1])
      }
    }
    
    // 如果文件名没有扩展名，尝试从文档的file_path中获取
    if (!filename.includes('.') && doc.file_path) {
      const originalFilename = doc.file_path.split('/').pop() || doc.file_path.split('\\').pop()
      if (originalFilename) {
        filename = originalFilename
      }
    }
    
    link.download = filename
    link.style.display = 'none'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    // 清理URL对象
    window.URL.revokeObjectURL(url)
    
    message.success('下载成功')
  } catch (error) {
    console.error('下载文档失败:', error)
    message.error('下载失败')
  }
}

// 编辑文档
const editDocument = (document: Document) => {
  currentDocument.value = document
  // 填充编辑表单
  editForm.value = {
    title: document.title,
    description: document.description || '',
    tags: document.tags || []
  }
  showEditModal.value = true
}

// 保存文档编辑
const saveDocumentEdit = async () => {
  if (!currentDocument.value) return
  
  editLoading.value = true
  try {
    const updateData = {
      title: editForm.value.title,
      description: editForm.value.description,
      tags: editForm.value.tags
    }
    
    const updatedDocument = await documentService.updateDocument(currentDocument.value.id, updateData)
    
    // 更新本地列表中的文档
    const index = documents.value.findIndex(doc => doc.id === currentDocument.value!.id)
    if (index !== -1) {
      documents.value[index] = { ...documents.value[index], ...updatedDocument }
    }
    
    message.success('文档更新成功')
    showEditModal.value = false
    
    // 更新统计
    updateStatistics()
  } catch (error: any) {
    console.error('更新文档失败:', error)
    message.error('更新文档失败')
  } finally {
    editLoading.value = false
  }
}

// 删除文档
const deleteDocument = (document: Document) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除文档 "${document.title}" 吗？此操作不可撤销。`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await documentService.deleteDocument(document.id)
        message.success('文档删除成功')
        
        // 从本地列表中移除
        const index = documents.value.findIndex(doc => doc.id === document.id)
        if (index !== -1) {
          documents.value.splice(index, 1)
        }
        
        // 更新统计
        updateStatistics()
      } catch (error: any) {
        console.error('删除文档失败:', error)
        message.error('删除文档失败')
      }
    }
  })
}

const loadDocuments = async () => {
  loading.value = true
  try {
    const response = await documentService.getDocuments({ limit: 100 })
    // 检查响应格式，如果是对象且包含items数组，则提取items
    if (response && typeof response === 'object' && 'items' in response) {
      documents.value = (response as any).items || []
    } else if (Array.isArray(response)) {
      documents.value = response
    } else {
      documents.value = []
    }
    updateStatistics()
  } catch (error: any) {
    console.error('加载文档失败:', error)
    documents.value = []
    message.error('加载文档失败，请检查后端服务是否正常运行')
  } finally {
    loading.value = false
  }
}


// 加载当前用户信息
const loadCurrentUser = async () => {
  try {
    currentUser.value = await authService.getCurrentUser()
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

// 检查文件名冲突
const checkFilenameConflicts = async () => {
  const conflictingFiles = []
  
  console.log('=== 开始检查文件名冲突 ===')
  console.log('待检查的文件列表:', fileList.value.map(f => f.file.name))
  
  try {
    for (const fileItem of fileList.value) {
      const filename = fileItem.file.name
      console.log(`检查文件: "${filename}"`)
      
      const result = await apiService.get(`/documents/check-filename?filename=${encodeURIComponent(filename)}`)
      console.log(`文件 "${filename}" 冲突检查结果:`, result)
        
        if (result.exists) {
          console.log(`发现冲突: "${filename}" 已存在 ${result.count} 个`)
          conflictingFiles.push({
            filename,
            count: result.count,
            existingDocuments: result.existing_documents
          })
        } else {
          console.log(`无冲突: "${filename}" 不存在`)
        }
    }
    
    console.log('冲突检查完成，发现冲突文件数量:', conflictingFiles.length)
    if (conflictingFiles.length > 0) {
      console.log('冲突文件详情:', conflictingFiles)
      return await showFilenameConflictDialog(conflictingFiles)
    }
    
    return false // 无冲突
  } catch (error) {
    console.error('检查文件名冲突失败:', error)
    message.warning('无法检查文件名冲突，将继续上传')
    return false
  }
}

// 显示文件名冲突对话框
const showFilenameConflictDialog = async (conflictingFiles) => {
  return new Promise((resolve) => {
    // 初始化冲突文件数据
    conflictFiles.value = conflictingFiles.map(conflict => ({
      originalName: conflict.filename,
      count: conflict.count,
      existingDocuments: conflict.existingDocuments,
      action: 'auto', // 默认选择自动重命名
      newName: '',
      nameError: ''
    }))
    
    // 保存resolve函数，用于在模态框中调用
    window.conflictResolve = resolve
    
    // 显示冲突处理模态框
    showConflictModal.value = true
  })
}

// 验证新文件名
const validateNewFilename = async (conflict) => {
  if (!conflict.newName || conflict.newName.trim() === '') {
    conflict.nameError = '请输入新的文件名'
    return false
  }
  
  if (conflict.newName === conflict.originalName) {
    conflict.nameError = '新文件名不能与原文件名相同'
    return false
  }
  
  // 检查新文件名是否也冲突
  try {
    const result = await apiService.get(`/documents/check-filename?filename=${encodeURIComponent(conflict.newName)}`)
    if (result.exists) {
      conflict.nameError = `文件名 "${conflict.newName}" 也已存在，请选择其他名称`
      return false
    }
  } catch (error) {
    console.error('验证新文件名失败:', error)
  }
  
  conflict.nameError = ''
  return true
}

// 检查是否可以继续处理冲突
const canProceedWithConflictResolution = computed(() => {
  return conflictFiles.value.every(conflict => {
    if (conflict.action === 'manual') {
      return conflict.newName && conflict.newName.trim() !== '' && !conflict.nameError
    }
    return true
  })
})

// 生成自动重命名的文件名 - 异步版本，实时验证数据库
const generateAutoRename = async (originalName, existingDocuments) => {
  const nameParts = originalName.split('.')
  const ext = nameParts.pop()
  const baseName = nameParts.join('.')
  
  // 收集所有已知的现有文件名（用于快速本地检查）
  const existingNames = new Set()
  
  // 添加现有文档的文件名
  if (existingDocuments && existingDocuments.length > 0) {
    existingDocuments.forEach(doc => {
      if (doc.file_name) {
        existingNames.add(doc.file_name)
      }
      // 也检查基于标题生成的可能文件名
      if (doc.title) {
        existingNames.add(`${doc.title}.${ext}`)
      }
    })
  }
  
  // 添加其他冲突文件已经生成的名称
  conflictFiles.value.forEach(c => {
    if (c.generatedName) {
      existingNames.add(c.generatedName)
    }
  })
  
  // 找到合适的后缀数字
  let counter = 1
  let newName = `${baseName}_${counter}.${ext}`
  let maxAttempts = 50 // 防止无限循环
  let attempts = 0
  
  console.log(`开始生成自动重命名: "${originalName}" -> 基础名称: "${baseName}", 扩展名: "${ext}"`)
  console.log(`本地已知冲突文件名:`, Array.from(existingNames))
  
  while (attempts < maxAttempts) {
    attempts++
    
    console.log(`\n--- 尝试第 ${attempts} 次: 检查文件名 "${newName}" ---`)
    console.log(`当前计数器值: ${counter}`)
    
    // 首先检查本地已知冲突
    if (existingNames.has(newName)) {
      console.log(`❌ 本地冲突检测: "${newName}" 已存在于本地缓存，尝试下一个数字`)
      counter++
      newName = `${baseName}_${counter}.${ext}`
      console.log(`递增计数器到: ${counter}, 新文件名: "${newName}"`)
      continue
    }
    
    console.log(`✅ 本地冲突检测: "${newName}" 不在本地缓存中，继续数据库检查`)
    
    // 实时检查数据库是否存在这个文件名
    try {
      const result = await apiService.get(`/documents/check-filename?filename=${encodeURIComponent(newName)}`)
      console.log(`📡 API响应详情:`, result)
      console.log(`🔍 检查冲突: result.exists = ${result.exists}, result.count = ${result.count}`)
      
      if (result.exists === true && result.count > 0) {
        console.log(`❌ 数据库冲突检测: "${newName}" 在数据库中已存在 (${result.count} 个), 尝试下一个数字`)
        // 将这个名称添加到本地缓存，避免重复检查
        existingNames.add(newName)
        counter++
        newName = `${baseName}_${counter}.${ext}`
        console.log(`⬆️ 递增计数器到: ${counter}, 新文件名: "${newName}"`)
        continue
      } else {
        // 找到了不冲突的文件名
        console.log(`✅ 找到唯一文件名: "${newName}" (exists=${result.exists}, count=${result.count})`)
        break
      }
    } catch (error) {
      console.error('验证自动重命名文件名失败:', error)
      // 网络错误，使用当前名称
      console.warn(`网络错误，使用当前名称: "${newName}"`)
      break
    }
  }
  
  if (attempts >= maxAttempts) {
    console.warn(`达到最大尝试次数 (${maxAttempts}), 使用最后生成的名称: "${newName}"`)
  }
  
  console.log(`自动重命名完成: "${originalName}" -> "${newName}"`)
  return newName
}

// 应用冲突解决方案
const applyConflictResolution = async () => {
  try {
    // 第一步：验证所有手动重命名的文件
    for (const conflict of conflictFiles.value) {
      if (conflict.action === 'manual') {
        const isValid = await validateNewFilename(conflict)
        if (!isValid) {
          message.error(`请正确填写文件 "${conflict.originalName}" 的新名称`)
          return
        }
      }
    }
    
    // 第二步：处理自动重命名和应用重命名到文件列表
    for (const conflict of conflictFiles.value) {
      const fileItem = fileList.value.find(item => item.file.name === conflict.originalName)
      if (fileItem) {
        if (conflict.action === 'manual' && conflict.newName) {
          // 手动重命名
          const originalExt = conflict.originalName.split('.').pop()
          const newNameWithExt = conflict.newName.includes('.') ? conflict.newName : `${conflict.newName}.${originalExt}`
          fileItem.renamedName = newNameWithExt
          console.log(`手动重命名: "${conflict.originalName}" -> "${newNameWithExt}"`)
        } else if (conflict.action === 'auto') {
          // 自动重命名 - 现在是异步的
          message.info(`正在为 "${conflict.originalName}" 生成唯一文件名...`)
          const autoName = await generateAutoRename(conflict.originalName, conflict.existingDocuments)
          fileItem.renamedName = autoName
          conflict.generatedName = autoName // 记录生成的名称，避免重复
          console.log(`自动重命名: "${conflict.originalName}" -> "${autoName}"`)
        } else if (conflict.action === 'overwrite') {
          // 覆盖上传，保持原名称，但标记为覆盖
          fileItem.overwriteMode = true
          console.log(`覆盖上传: "${conflict.originalName}"`)
        }
      }
    }
    
    // 第三步：最终验证 - 确保没有重复的新文件名
    const finalValidation = await validateFinalFileNames()
    if (!finalValidation.isValid) {
      message.error(`文件名验证失败: ${finalValidation.errorMessage}`)
      return
    }
    
    // 关闭模态框并继续上传
    showConflictModal.value = false
    message.success('文件名冲突处理完成，开始上传...')
    if (window.conflictResolve) {
      window.conflictResolve(false) // 继续上传
    }
    
  } catch (error) {
    console.error('应用冲突解决方案失败:', error)
    message.error('处理文件名冲突时发生错误，请重试')
  }
}

// 最终验证所有文件名
const validateFinalFileNames = async () => {
  const finalFileNames = []
  const duplicates = []
  
  // 收集所有最终的文件名
  for (const fileItem of fileList.value) {
    const finalName = fileItem.renamedName || fileItem.file.name
    
    // 检查是否有内部重复
    if (finalFileNames.includes(finalName)) {
      duplicates.push(finalName)
    } else {
      finalFileNames.push(finalName)
    }
    
    // 检查数据库中是否存在（除了覆盖模式的文件）
    if (!fileItem.overwriteMode) {
      try {
        const result = await apiService.get(`/documents/check-filename?filename=${encodeURIComponent(finalName)}`)
        if (result.exists) {
          duplicates.push(finalName)
        }
      } catch (error) {
        console.error('最终验证文件名失败:', error)
      }
    }
  }
  
  if (duplicates.length > 0) {
    return {
      isValid: false,
      errorMessage: `以下文件名仍然存在冲突: ${duplicates.join(', ')}`
    }
  }
  
  return {
    isValid: true,
    errorMessage: null
  }
}

// 获取自动重命名示例（用于预览显示）
const getAutoRenameExample = (originalName) => {
  const nameParts = originalName.split('.')
  const ext = nameParts.pop()
  const baseName = nameParts.join('.')
  return `${baseName}_1.${ext}`
}

// 取消冲突解决
const cancelConflictResolution = () => {
  showConflictModal.value = false
  conflictFiles.value = []
  if (window.conflictResolve) {
    window.conflictResolve(true) // 取消上传
  }
}

onMounted(async () => {
  try {
    await Promise.all([
      loadDocuments(),
      loadCurrentUser()
    ])
  } catch (error) {
    console.error('初始化页面失败:', error)
  }
})
</script>

<style scoped>
/* DocumentView specific styles can be added here if needed */
</style>