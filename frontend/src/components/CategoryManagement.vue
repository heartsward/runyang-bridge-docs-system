<template>
  <div class="category-management">
    <n-space vertical :size="16">
      <!-- 分类统计 -->
      <n-card title="分类统计" size="small">
        <n-space>
          <n-statistic
            label="总分类数"
            :value="statistics.total_categories"
            tabular-nums
          />
          <n-statistic
            label="未分类文档"
            :value="statistics.uncategorized_count"
            tabular-nums
          />
        </n-space>
      </n-card>

      <!-- 操作按钮 -->
      <n-space>
        <n-button type="primary" @click="showCreateModal = true">
          <template #icon>
            <n-icon :component="AddOutline" />
          </template>
          新建分类
        </n-button>
        <n-button @click="initDefaultCategories" :loading="initLoading">
          <template #icon>
            <n-icon :component="LibraryOutline" />
          </template>
          初始化默认分类
        </n-button>
        <n-button @click="loadCategories">
          <template #icon>
            <n-icon :component="RefreshOutline" />
          </template>
          刷新
        </n-button>
      </n-space>

      <!-- 分类列表 -->
      <n-card title="分类列表">
        <div v-if="loading" style="text-align: center; padding: 40px;">
          <n-spin size="large" />
        </div>

        <n-list v-else-if="categories.length > 0">
          <n-list-item
            v-for="category in categories"
            :key="category.id"
            style="padding: 12px 0;"
          >
            <n-space align="center" style="width: 100%;">
              <div
                :style="{
                  width: '12px',
                  height: '12px',
                  backgroundColor: category.color || '#f0f0f0',
                  borderRadius: '50%'
                }"
              ></div>
              
              <n-icon v-if="category.icon" :component="getIconComponent(category.icon)" />
              
              <div style="flex: 1;">
                <n-space vertical size="small">
                  <n-text strong>{{ category.name }}</n-text>
                  <n-text depth="3" v-if="category.description">
                    {{ category.description }}
                  </n-text>
                  <n-tag size="small" :type="category.document_count > 0 ? 'info' : 'default'">
                    {{ category.document_count || 0 }} 个文档
                  </n-tag>
                </n-space>
              </div>
              
              <n-space>
                <n-button size="small" @click="editCategory(category)">
                  <template #icon>
                    <n-icon :component="EditOutline" />
                  </template>
                  编辑
                </n-button>
                <n-button 
                  size="small" 
                  type="error" 
                  @click="confirmDeleteCategory(category)"
                  :disabled="category.document_count > 0"
                >
                  <template #icon>
                    <n-icon :component="TrashOutline" />
                  </template>
                  删除
                </n-button>
              </n-space>
            </n-space>
          </n-list-item>
        </n-list>

        <n-empty v-else description="暂无分类">
          <template #extra>
            <n-button @click="showCreateModal = true">
              创建第一个分类
            </n-button>
          </template>
        </n-empty>
      </n-card>
    </n-space>

    <!-- 创建/编辑分类模态框 -->
    <n-modal v-model:show="showCreateModal" preset="card" style="width: 600px;" :title="editingCategory ? '编辑分类' : '创建分类'">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-placement="left"
        label-width="auto"
      >
        <n-form-item label="分类名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入分类名称" />
        </n-form-item>
        
        <n-form-item label="分类描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="请输入分类描述（可选）"
            :rows="3"
          />
        </n-form-item>
        
        <n-form-item label="分类颜色" path="color">
          <n-color-picker v-model:value="formData.color" :show-alpha="false" />
        </n-form-item>
        
        <n-form-item label="分类图标" path="icon">
          <n-select
            v-model:value="formData.icon"
            :options="iconOptions"
            placeholder="选择图标（可选）"
            clearable
          >
            <template #render-label="{ option }">
              <n-space align="center">
                <n-icon :component="getIconComponent(option.value)" />
                <span>{{ option.label }}</span>
              </n-space>
            </template>
          </n-select>
        </n-form-item>
        
        <n-form-item label="排序顺序" path="sort_order">
          <n-input-number v-model:value="formData.sort_order" :min="0" placeholder="排序顺序" />
        </n-form-item>
      </n-form>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="handleCancel">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ editingCategory ? '更新' : '创建' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NSpace,
  NCard,
  NStatistic,
  NButton,
  NIcon,
  NList,
  NListItem,
  NText,
  NTag,
  NEmpty,
  NSpin,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NColorPicker,
  NInputNumber,
  useMessage,
  useDialog
} from 'naive-ui'
import {
  AddOutline,
  LibraryOutline,
  RefreshOutline,
  CreateOutline as EditOutline,
  TrashOutline,
  ServerOutline,
  WifiOutline,
  LibraryOutline as DatabaseOutline,
  CubeOutline,
  PulseOutline,
  ShieldCheckmarkOutline,
  ConstructOutline,
  BookOutline,
  FolderOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'
import { apiService } from '@/services/api'

interface Category {
  id: number
  name: string
  description?: string
  color?: string
  icon?: string
  sort_order: number
  is_active: boolean
  creator_id?: number
  created_at: string
  updated_at?: string
  document_count?: number
}

interface CategoryStatistics {
  categories: any[]
  uncategorized_count: number
  total_categories: number
}

const emit = defineEmits(['close', 'updated'])
const message = useMessage()
const dialog = useDialog()

// 状态管理
const loading = ref(false)
const initLoading = ref(false)
const submitting = ref(false)
const showCreateModal = ref(false)
const editingCategory = ref<Category | null>(null)

// 数据
const categories = ref<Category[]>([])
const statistics = ref<CategoryStatistics>({
  categories: [],
  uncategorized_count: 0,
  total_categories: 0
})

// 表单数据
const formRef = ref()
const formData = ref({
  name: '',
  description: '',
  color: '#1890ff',
  icon: '',
  sort_order: 0
})

const formRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' },
    { min: 1, max: 100, message: '分类名称长度应在1-100字符之间', trigger: 'blur' }
  ]
}

// 图标选项
const iconOptions = [
  { label: '服务器', value: 'server-outline' },
  { label: '网络', value: 'wifi-outline' },
  { label: '数据库', value: 'library-outline' },
  { label: '应用', value: 'cube-outline' },
  { label: '监控', value: 'pulse-outline' },
  { label: '安全', value: 'shield-checkmark-outline' },
  { label: '工具', value: 'construct-outline' },
  { label: '手册', value: 'book-outline' },
  { label: '文件夹', value: 'folder-outline' },
  { label: '文档', value: 'document-text-outline' }
]

// 获取图标组件
const getIconComponent = (iconName: string) => {
  const iconMap: Record<string, any> = {
    'server-outline': ServerOutline,
    'wifi-outline': WifiOutline,
    'library-outline': DatabaseOutline,
    'cube-outline': CubeOutline,
    'pulse-outline': PulseOutline,
    'shield-checkmark-outline': ShieldCheckmarkOutline,
    'construct-outline': ConstructOutline,
    'book-outline': BookOutline,
    'folder-outline': FolderOutline,
    'document-text-outline': DocumentTextOutline
  }
  return iconMap[iconName] || FolderOutline
}

// 加载分类列表
const loadCategories = async () => {
  loading.value = true
  try {
    console.log('CategoryManagement: 开始加载分类...')
    // 使用简化的分类API
    const [categoriesResponse, statsResponse] = await Promise.all([
      apiService.get('/categories/'),
      apiService.get('/categories/statistics')
    ])
    
    console.log('CategoryManagement 分类响应:', categoriesResponse)
    console.log('CategoryManagement 统计响应:', statsResponse)
    
    categories.value = categoriesResponse || []
    statistics.value = statsResponse || { categories: [], uncategorized_count: 0, total_categories: 0 }
  } catch (error) {
    console.error('加载分类失败:', error)
    message.error('加载分类失败')
  } finally {
    loading.value = false
  }
}

// 编辑分类
const editCategory = (category: Category) => {
  editingCategory.value = category
  formData.value = {
    name: category.name,
    description: category.description || '',
    color: category.color || '#1890ff',
    icon: category.icon || '',
    sort_order: category.sort_order
  }
  showCreateModal.value = true
}

// 处理表单提交
const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    submitting.value = true
    
    if (editingCategory.value) {
      // 更新分类
      await apiService.put(`/categories/${editingCategory.value.id}`, formData.value)
      message.success('分类更新成功')
    } else {
      // 创建分类
      await apiService.post('/categories/', formData.value)
      message.success('分类创建成功')
    }
    
    await loadCategories()
    handleCancel()
    emit('updated')
    
  } catch (error: any) {
    console.error('操作失败:', error)
    message.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 取消操作
const handleCancel = () => {
  showCreateModal.value = false
  editingCategory.value = null
  formData.value = {
    name: '',
    description: '',
    color: '#1890ff',
    icon: '',
    sort_order: 0
  }
  formRef.value?.restoreValidation()
}

// 确认删除分类
const confirmDeleteCategory = (category: Category) => {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除分类"${category.name}"吗？此操作不可恢复。`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: () => deleteCategory(category)
  })
}

// 删除分类
const deleteCategory = async (category: Category) => {
  try {
    await apiService.delete(`/categories/${category.id}`)
    message.success('分类删除成功')
    await loadCategories()
    emit('updated')
  } catch (error: any) {
    console.error('删除失败:', error)
    message.error(error.response?.data?.detail || '删除失败')
  }
}

// 初始化默认分类
const initDefaultCategories = async () => {
  initLoading.value = true
  try {
    const response = await apiService.post('/categories/init-default')
    message.success(response.message)
    await loadCategories()
    emit('updated')
  } catch (error: any) {
    console.error('初始化失败:', error)
    message.error(error.response?.data?.detail || '初始化失败')
  } finally {
    initLoading.value = false
  }
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.category-management {
  min-height: 400px;
}
</style>