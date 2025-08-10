<template>
  <div class="category-view">
    <NavigationMenu>
      <n-layout>
        <n-layout-header bordered class="header">
          <n-space justify="space-between" align="center">
            <n-h2>文档分类管理</n-h2>
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
            </n-space>
          </n-space>
        </n-layout-header>
        
        <n-layout-content content-style="padding: 24px;">
          <n-grid cols="1 s:1 m:3 l:4" responsive="screen" :x-gap="16" :y-gap="16">
            <!-- 分类统计卡片 -->
            <n-grid-item>
              <n-card title="分类统计" size="small">
                <n-space vertical>
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
            </n-grid-item>
            
            <!-- 分类树 -->
            <n-grid-item :span="3">
              <n-card title="分类结构" size="small">
                <template #header-extra>
                  <n-space>
                    <n-button size="small" @click="loadCategoryTree">
                      <template #icon>
                        <n-icon :component="RefreshOutline" />
                      </template>
                      刷新
                    </n-button>
                    <n-switch v-model:value="showStatistics" size="small">
                      <template #checked>显示统计</template>
                      <template #unchecked>隐藏统计</template>
                    </n-switch>
                  </n-space>
                </template>
                
                <div v-if="loading" style="text-align: center; padding: 40px;">
                  <n-spin size="large" />
                </div>
                
                <n-tree
                  v-else
                  :data="treeData"
                  :render-prefix="renderPrefix"
                  :render-label="renderLabel"
                  :render-suffix="renderSuffix"
                  expand-on-click
                  :default-expanded-keys="expandedKeys"
                  selectable
                  @update:selected-keys="handleSelect"
                />
                
                <n-empty v-if="!loading && treeData.length === 0" description="暂无分类">
                  <template #extra>
                    <n-button size="small" @click="showCreateModal = true">
                      创建第一个分类
                    </n-button>
                  </template>
                </n-empty>
              </n-card>
            </n-grid-item>
          </n-grid>
        </n-layout-content>
      </n-layout>
    </NavigationMenu>

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
        
        <n-form-item label="父分类" path="parent_id">
          <n-select
            v-model:value="formData.parent_id"
            :options="parentOptions"
            placeholder="选择父分类（可选）"
            clearable
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
    
    <!-- 分类详情模态框 -->
    <n-modal v-model:show="showDetailModal" preset="card" style="width: 500px;" title="分类详情">
      <div v-if="selectedCategory">
        <n-descriptions label-placement="left" :column="1">
          <n-descriptions-item label="分类名称">
            <n-space align="center">
              <div
                v-if="selectedCategory.color"
                :style="{
                  width: '12px',
                  height: '12px',
                  backgroundColor: selectedCategory.color,
                  borderRadius: '50%'
                }"
              ></div>
              <n-icon v-if="selectedCategory.icon" :component="getIconComponent(selectedCategory.icon)" />
              {{ selectedCategory.name }}
            </n-space>
          </n-descriptions-item>
          
          <n-descriptions-item label="分类描述">
            {{ selectedCategory.description || '无描述' }}
          </n-descriptions-item>
          
          <n-descriptions-item label="文档数量">
            <n-tag :type="selectedCategory.document_count > 0 ? 'info' : 'default'">
              {{ selectedCategory.document_count || 0 }} 个文档
            </n-tag>
          </n-descriptions-item>
          
          <n-descriptions-item label="排序顺序">
            {{ selectedCategory.sort_order }}
          </n-descriptions-item>
          
          <n-descriptions-item label="创建时间">
            {{ formatDate(selectedCategory.created_at) }}
          </n-descriptions-item>
          
          <n-descriptions-item label="更新时间">
            {{ formatDate(selectedCategory.updated_at) }}
          </n-descriptions-item>
        </n-descriptions>
      </div>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showDetailModal = false">关闭</n-button>
          <n-button type="primary" @click="editCategory(selectedCategory)">编辑</n-button>
          <n-button type="error" @click="confirmDeleteCategory(selectedCategory)" :disabled="selectedCategory?.document_count > 0">
            删除
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import {
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NSpace,
  NH2,
  NButton,
  NIcon,
  NCard,
  NGrid,
  NGridItem,
  NStatistic,
  NTree,
  NEmpty,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSelect,
  NColorPicker,
  NInputNumber,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NSpin,
  NSwitch,
  useMessage,
  useDialog,
  type TreeOption
} from 'naive-ui'
import {
  AddOutline,
  LibraryOutline,
  RefreshOutline,
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
import NavigationMenu from '../components/NavigationMenu.vue'
import { apiService } from '@/services/api'

interface Category {
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
  children?: Category[]
}

interface CategoryStatistics {
  categories: any[]
  uncategorized_count: number
  total_categories: number
}

const message = useMessage()
const dialog = useDialog()

// 状态管理
const loading = ref(false)
const initLoading = ref(false)
const submitting = ref(false)
const showCreateModal = ref(false)
const showDetailModal = ref(false)
const showStatistics = ref(true)
const editingCategory = ref<Category | null>(null)
const selectedCategory = ref<Category | null>(null)

// 数据
const categoryTree = ref<Category[]>([])
const statistics = ref<CategoryStatistics>({
  categories: [],
  uncategorized_count: 0,
  total_categories: 0
})
const parentOptions = ref<any[]>([])
const expandedKeys = ref<string[]>([])

// 表单数据
const formRef = ref()
const formData = ref({
  name: '',
  description: '',
  parent_id: null,
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

// 树形数据
const treeData = computed<TreeOption[]>(() => {
  return convertToTreeData(categoryTree.value)
})

// 转换为树形数据格式
const convertToTreeData = (categories: Category[]): TreeOption[] => {
  return categories.map(category => ({
    key: category.id.toString(),
    label: category.name,
    categoryData: category,
    children: category.children ? convertToTreeData(category.children) : undefined
  }))
}

// 树节点渲染函数
const renderPrefix = ({ option }: { option: TreeOption }) => {
  const category = option.categoryData as Category
  return h('div', { style: 'display: flex; align-items: center; gap: 4px;' }, [
    category.color ? h('div', {
      style: {
        width: '8px',
        height: '8px',
        backgroundColor: category.color,
        borderRadius: '50%'
      }
    }) : null,
    category.icon ? h(NIcon, { component: getIconComponent(category.icon), size: 16 }) : null
  ])
}

const renderLabel = ({ option }: { option: TreeOption }) => {
  const category = option.categoryData as Category
  return h('span', category.name)
}

const renderSuffix = ({ option }: { option: TreeOption }) => {
  const category = option.categoryData as Category
  if (!showStatistics.value) return null
  
  return h('div', { style: 'display: flex; align-items: center; gap: 8px;' }, [
    h(NTag, { 
      size: 'small', 
      type: category.document_count > 0 ? 'info' : 'default' 
    }, { default: () => `${category.document_count || 0}` }),
    h(NSpace, { size: 4 }, {
      default: () => [
        h(NButton, {
          size: 'tiny',
          quaternary: true,
          onClick: (e: Event) => {
            e.stopPropagation()
            viewCategoryDetail(category)
          }
        }, { default: () => '详情' }),
        h(NButton, {
          size: 'tiny',
          quaternary: true,
          type: 'primary',
          onClick: (e: Event) => {
            e.stopPropagation()
            editCategory(category)
          }
        }, { default: () => '编辑' })
      ]
    })
  ])
}

// 加载分类树
const loadCategoryTree = async () => {
  loading.value = true
  try {
    const [treeResponse, statsResponse, optionsResponse] = await Promise.all([
      apiService.get('/categories/tree'),
      apiService.get('/categories/statistics'),
      apiService.get('/categories/options')
    ])
    
    categoryTree.value = treeResponse
    statistics.value = statsResponse
    parentOptions.value = [
      { label: '无父分类', value: null },
      ...optionsResponse.map((cat: any) => ({
        label: cat.name,
        value: cat.id
      }))
    ]
    
    // 展开所有节点
    expandedKeys.value = treeResponse.map((cat: Category) => cat.id.toString())
    
  } catch (error) {
    console.error('加载分类数据失败:', error)
    message.error('加载分类数据失败')
  } finally {
    loading.value = false
  }
}

// 处理树节点选择
const handleSelect = (keys: string[]) => {
  if (keys.length > 0) {
    const selectedKey = keys[0]
    const findCategory = (categories: Category[], key: string): Category | null => {
      for (const cat of categories) {
        if (cat.id.toString() === key) return cat
        if (cat.children) {
          const found = findCategory(cat.children, key)
          if (found) return found
        }
      }
      return null
    }
    
    const category = findCategory(categoryTree.value, selectedKey)
    if (category) {
      viewCategoryDetail(category)
    }
  }
}

// 查看分类详情
const viewCategoryDetail = (category: Category) => {
  selectedCategory.value = category
  showDetailModal.value = true
}

// 编辑分类
const editCategory = (category: Category) => {
  editingCategory.value = category
  formData.value = {
    name: category.name,
    description: category.description || '',
    parent_id: category.parent_id || null,
    color: category.color || '#1890ff',
    icon: category.icon || '',
    sort_order: category.sort_order
  }
  showDetailModal.value = false
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
      await apiService.post('/categories', formData.value)
      message.success('分类创建成功')
    }
    
    await loadCategoryTree()
    handleCancel()
    
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
    parent_id: null,
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
    showDetailModal.value = false
    await loadCategoryTree()
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
    await loadCategoryTree()
  } catch (error: any) {
    console.error('初始化失败:', error)
    message.error(error.response?.data?.detail || '初始化失败')
  } finally {
    initLoading.value = false
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

onMounted(() => {
  loadCategoryTree()
})
</script>

<style scoped>
.category-view {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  background-color: white;
}
</style>