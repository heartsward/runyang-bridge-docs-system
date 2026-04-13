<template>
  <PageLayout title="系统设置">
    <!-- 用户管理 - 仅管理员可见 -->
    <n-card v-if="currentUser?.is_superuser" title="用户管理" style="margin-bottom: 24px;">
      <template #header-extra>
        <n-button type="primary" @click="showCreateUserModal = true">
          <template #icon>
            <n-icon :component="PersonAddOutline" />
          </template>
          创建用户
        </n-button>
      </template>
      
      <div v-if="usersLoading" style="text-align: center; padding: 40px;">
        <n-spin size="large" />
        <div style="margin-top: 16px;">
          <n-text depth="3">加载用户列表中...</n-text>
        </div>
      </div>
      
      <div v-else>
        <n-data-table
          :columns="userColumns"
          :data="users"
          :pagination="{ pageSize: 10 }"
          :bordered="false"
        />
      </div>
    </n-card>
    
    <!-- AI服务设置 -->
    <n-card title="AI服务配置" style="margin-bottom: 24px;">
      <template #header-extra>
        <n-space>
          <n-button type="primary" size="small" @click="testAIConnection" :loading="testingAI">
            <template #icon>
              <n-icon :component="FlashOutline" />
            </template>
            测试连接
          </n-button>
        </n-space>
      </template>
      
      <!-- AI提供商配置 -->
      <n-form-item label="默认AI提供商">
        <n-select
          v-model:value="aiConfig.default_provider"
          placeholder="选择AI提供商"
          style="width: 300px;"
          :options="providerOptions"
          @update:value="handleProviderChange"
        />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">选择默认使用的AI服务提供商 (共 {{ aiProviders.length }} 个选项)</n-text>
        </template>
      </n-form-item>
      
      <!-- 详细配置按钮 -->
      <n-form-item label="详细配置">
        <n-button @click="showProviderConfig = !showProviderConfig" type="tertiary">
          {{ showProviderConfig ? '收起配置' : '展开配置' }}
        </n-button>
      </n-form-item>
      
      <!-- AI提供商详细配置 -->
      <div v-if="showProviderConfig" style="background: #f5f5f5; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
        <!-- 当前选择提供商的配置 -->
        <n-divider style="margin: 8px 0;">{{ getProviderDisplayName(aiConfig.default_provider) }} 配置</n-divider>
        <n-form-item label="API Key">
          <n-input 
            v-model:value="getCurrentProviderConfig().api_key" 
            type="password" 
            placeholder="请输入API Key"
            show-password-on="click"
            style="width: 400px;"
          />
        </n-form-item>
        <n-form-item label="API URL">
          <n-input 
            v-model:value="getCurrentProviderConfig().api_url" 
            placeholder="请输入API URL"
            style="width: 400px;"
          />
          <template #feedback>
            <n-text depth="3" style="font-size: 12px;">
              {{ getDefaultUrlHint(aiConfig.default_provider) }}
            </n-text>
          </template>
        </n-form-item>
        <n-form-item label="模型">
          <n-input 
            v-model:value="getCurrentProviderConfig().model" 
            placeholder="请输入模型名称"
            style="width: 200px;"
          />
          <template #feedback>
            <n-text depth="3" style="font-size: 12px;">
              {{ getDefaultModelHint(aiConfig.default_provider) }}
            </n-text>
          </template>
        </n-form-item>
        
        <!-- MiniMax特有配置 -->
        <n-form-item v-if="aiConfig.default_provider === 'minimax'" label="Group ID">
          <n-input 
            v-model:value="aiConfig.providers.minimax.group_id" 
            placeholder="请输入Group ID"
            style="width: 200px;"
          />
        </n-form-item>
      </div>
      
      <!-- AI功能开关 -->
      <n-form-item label="启用AI功能">
        <n-switch v-model:value="aiConfig.enabled" />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">启用AI智能提取和分析功能</n-text>
        </template>
      </n-form-item>
      
      <!-- 降级设置 -->
      <n-form-item label="AI失败时降级到传统方法">
        <n-switch v-model:value="aiConfig.fallback_enabled" />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">AI服务失败时自动使用传统方法</n-text>
        </template>
      </n-form-item>
      
      <!-- 成本限制 -->
      <n-form-item label="启用成本限制">
        <n-switch v-model:value="aiConfig.cost_limit_enabled" />
      </n-form-item>
      
      <n-form-item 
        v-if="aiConfig.cost_limit_enabled" 
        label="每日成本限制（美元）"
      >
        <n-input-number 
          v-model:value="aiConfig.daily_cost_limit" 
          :min="0.1"
          :step="0.1"
          :precision="2"
          style="width: 200px;"
        />
      </n-form-item>
      
      <!-- 缓存设置 -->
      <n-form-item label="启用AI缓存">
        <n-switch v-model:value="aiConfig.cache_enabled" />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">缓存AI响应以提高性能</n-text>
        </template>
      </n-form-item>
      
      <n-form-item 
        v-if="aiConfig.cache_enabled"
        label="缓存过期时间（秒）"
      >
        <n-input-number 
          v-model:value="aiConfig.cache_ttl" 
          :min="60"
          :step="60"
          style="width: 200px;"
        />
      </n-form-item>
      
      <!-- 保存AI配置 -->
      <div style="margin-top: 24px;">
        <n-space>
          <n-button type="primary" @click="saveAIConfig" :loading="savingAIConfig">
            保存AI配置
          </n-button>
          <n-button @click="loadAIConfig">
            重置为默认值
          </n-button>
        </n-space>
      </div>
    </n-card>
    
    <!-- AI使用统计 -->
    <n-card title="AI使用统计" style="margin-bottom: 24px;">
      <n-spin :show="loadingAIStats" size="large">
        <template #description>
          <n-text depth="3">加载AI统计数据中...</n-text>
        </template>
        
        <n-descriptions :column="1" bordered>
          <n-descriptions-item label="总成本">
            <n-statistic 
              :value="aiStats.total_cost" 
              :precision="4"
            >
              <template #prefix>
                $
              </template>
              <template #suffix>
                <n-text depth="3" style="font-size: 12px;">USD</n-text>
              </template>
            </n-statistic>
          </n-descriptions-item>
          
          <n-descriptions-item label="总请求数">
            <n-statistic :value="aiStats.request_count" />
          </n-descriptions-item>
          
          <n-descriptions-item label="总Token数">
            <n-statistic :value="aiStats.total_tokens" />
          </n-descriptions-item>
          
          <n-descriptions-item label="今日成本">
            <n-statistic 
              :value="todayCost" 
              :precision="4"
            >
              <template #prefix>
                $
              </template>
            </n-statistic>
          </n-descriptions-item>
        </n-descriptions>
        
        <n-divider style="margin: 16px 0;">各提供商统计</n-divider>
        
          <div v-for="(cost, provider) in Object.entries(aiStats.by_provider)" :key="provider">
            <n-statistic 
              :label="getProviderDisplayName(provider)" 
              :value="cost" 
              :precision="4"
            >
              <template #prefix>
                $
              </template>
            </n-statistic>
          </div>
      </n-spin>
    </n-card>
    
    <!-- 其他设置项可以在这里添加 -->
    <n-card title="其他设置" style="margin-bottom: 24px;">
      <n-empty description="更多设置功能开发中...">
        <template #icon>
          <n-icon :component="SettingsOutline" size="48" />
        </template>
      </n-empty>
    </n-card>
    
    <!-- 创建用户模态框 -->
    <n-modal v-model:show="showCreateUserModal" preset="dialog" title="创建新用户">
      <n-form :model="newUserForm" label-placement="left" label-width="100px">
        <n-form-item label="用户名" required>
          <n-input v-model:value="newUserForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="邮箱" required>
          <n-input v-model:value="newUserForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="密码" required>
          <n-input v-model:value="newUserForm.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="newUserForm.full_name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="newUserForm.department" placeholder="请输入部门" />
        </n-form-item>
        <n-form-item label="职位">
          <n-input v-model:value="newUserForm.position" placeholder="请输入职位" />
        </n-form-item>
        <n-form-item label="电话">
          <n-input v-model:value="newUserForm.phone" placeholder="请输入电话" />
        </n-form-item>
        <n-form-item label="管理员权限">
          <n-switch v-model:value="newUserForm.is_superuser" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showCreateUserModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreateUser">创建</n-button>
        </n-space>
      </template>
    </n-modal>
    
    <!-- 编辑用户模态框 -->
    <n-modal v-model:show="showEditUserModal" preset="dialog" title="编辑用户信息">
      <n-form :model="editUserForm" label-placement="left" label-width="100px">
        <n-form-item label="用户名" required>
          <n-input v-model:value="editUserForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="邮箱" required>
          <n-input v-model:value="editUserForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="editUserForm.full_name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="editUserForm.department" placeholder="请输入部门" />
        </n-form-item>
        <n-form-item label="职位">
          <n-input v-model:value="editUserForm.position" placeholder="请输入职位" />
        </n-form-item>
        <n-form-item label="电话">
          <n-input v-model:value="editUserForm.phone" placeholder="请输入电话" />
        </n-form-item>
        <n-form-item label="账户状态">
          <n-switch v-model:value="editUserForm.is_active" />
          <n-text depth="3" style="margin-left: 8px;">
            {{ editUserForm.is_active ? '激活' : '禁用' }}
          </n-text>
        </n-form-item>
        <n-form-item label="管理员权限">
          <n-switch v-model:value="editUserForm.is_superuser" />
        </n-form-item>
        <n-form-item label="修改密码">
          <n-input 
            v-model:value="editUserForm.password" 
            type="password" 
            placeholder="留空表示不修改密码"
            autocomplete="new-password"
          />
          <template #suffix>
            <n-text depth="3" style="font-size: 12px;">
              可选
            </n-text>
          </template>
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showEditUserModal = false">取消</n-button>
          <n-button type="primary" @click="handleUpdateUser">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </PageLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { 
  NCard,
  NForm,
  NFormItem,
  NRadioGroup,
  NRadio,
  NSpace,
  NText,
  NAlert,
  NEmpty,
  NIcon,
  NSpin,
  NButton,
  NDataTable,
  NModal,
  NInput,
  NSwitch,
  NTag,
  NPopconfirm,
  NSelect,
  NInputNumber,
  NDescriptions,
  NDescriptionsItem,
  NStatistic,
  NDivider,
  useMessage,
  type FormInst
} from 'naive-ui'
import { 
  SettingsOutline, 
  PersonAddOutline, 
  CreateOutline, 
  TrashOutline,
  FlashOutline,
  StatsOutline
} from '@vicons/ionicons5'
import PageLayout from '@/components/PageLayout.vue'
import { settingsService, authService } from '@/services'
import { 
  aiService, 
  getAIProviders, 
  getAIStats, 
  getAIConfig as getAIConfigAPI,
  saveAIConfig as saveAIConfigAPI,
  testAIConnection as testAIConnectionAPI,
  type AIProvider, 
  type AIStats, 
  type AIConfig,
  type AIProviderConfig
} from '@/services/ai'
import type { UserSettings, User, UserCreate, UserUpdate } from '@/services/settings'

const message = useMessage()

// 用户管理相关状态
const currentUser = ref<User | null>(null)
const users = ref<User[]>([])
const usersLoading = ref(false)
const showCreateUserModal = ref(false)
const showEditUserModal = ref(false)
const editingUser = ref<User | null>(null)

// 新用户表单
const newUserForm = ref<UserCreate>({
  username: '',
  email: '',
  password: '',
  full_name: '',
  department: '',
  position: '',
  phone: '',
  is_superuser: false
})

// 编辑用户表单
const editUserForm = ref<UserUpdate>({
  username: '',
  email: '',
  full_name: '',
  department: '',
  position: '',
  phone: '',
  is_active: true,
  is_superuser: false,
  password: ''  // 添加密码字段
})

const rules = {}

// 硬编码的AI提供商列表（作为备选方案）
const hardcodedProviders: AIProvider[] = [
  {
    name: 'openai',
    display_name: 'OpenAI',
    is_available: true,
    description: 'OpenAI GPT系列模型'
  },
  {
    name: 'anthropic',
    display_name: 'Anthropic (Claude)',
    is_available: true,
    description: 'Anthropic Claude系列模型'
  },
  {
    name: 'alibaba',
    display_name: '阿里云通义',
    is_available: true,
    description: '阿里云通义千问系列模型'
  },
  {
    name: 'zhipu',
    display_name: '智谱AI',
    is_available: true,
    description: '智谱AI GLM系列模型'
  },
  {
    name: 'minimax',
    display_name: 'MiniMax',
    is_available: true,
    description: 'MiniMax ABAB系列模型'
  },
  {
    name: 'custom',
    display_name: '自定义',
    is_available: true,
    description: '自定义AI服务提供商'
  }
]

// AI服务相关状态
// 初始化为硬编码列表，确保下拉框始终有选项
const aiProviders = ref<AIProvider[]>([...hardcodedProviders])
const aiConfig = ref<AIConfig>({
  default_provider: 'openai',
  enabled: true,
  fallback_enabled: true,
  cost_limit_enabled: false,
  daily_cost_limit: 10.0,
  cache_enabled: true,
  cache_ttl: 3600,
  providers: {
    openai: {
      api_key: '',
      api_url: 'https://api.openai.com/v1/chat/completions',
      model: 'gpt-4o-mini'
    },
    anthropic: {
      api_key: '',
      api_url: 'https://api.anthropic.com/v1/messages',
      model: 'claude-3-haiku-20240307'
    },
    alibaba: {
      api_key: '',
      api_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
      model: 'qwen-plus'
    },
    zhipu: {
      api_key: '',
      api_url: 'https://open.bigmodel.cn/api/paas/v4/chat/completions',
      model: 'glm-4-flash'
    },
    minimax: {
      api_key: '',
      api_url: 'https://api.minimaxi.com/v1/chat/completions',
      model: 'MiniMax-M2.7',
      group_id: ''
    },
    custom: {
      api_key: '',
      api_url: '',
      model: ''
    }
  }
})
const aiStats = ref<AIStats>({
  total_cost: 0,
  total_tokens: 0,
  request_count: 0,
  daily_costs: {},
  by_provider: {}
})
const loadingAIStats = ref(false)
const testingAI = ref(false)
const savingAIConfig = ref(false)
const showProviderConfig = ref(false)

// 提供商显示名称映射
const providerDisplayNames: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  alibaba: '阿里云通义',
  zhipu: '智谱AI',
  minimax: 'MiniMax',
  custom: '自定义 (Custom)'
}

// 默认URL提示
const defaultUrls: Record<string, string> = {
  openai: '默认: https://api.openai.com/v1/chat/completions',
  anthropic: '默认: https://api.anthropic.com/v1/messages',
  alibaba: '默认: https://dashscope.aliyuncs.com/compatible-mode/v1',
  zhipu: '默认: https://open.bigmodel.cn/api/paas/v4/chat/completions',
  minimax: '默认: https://api.minimaxi.com/v1/chat/completions',
  custom: '请输入完整的API URL'
}

// 默认模型提示
const defaultModels: Record<string, string> = {
  openai: '推荐: gpt-4o-mini, gpt-4, gpt-3.5-turbo',
  anthropic: '推荐: claude-3-haiku-20240307, claude-3-sonnet-20240229',
  alibaba: '推荐: qwen-plus, qwen-turbo, qwen-max',
  zhipu: '推荐: glm-4-flash, glm-4, glm-3-turbo',
  minimax: '推荐: MiniMax-M2.7, MiniMax-M2.7-highspeed (极速版需特定订阅)',
  custom: '请输入模型名称'
}

// 用户表格列定义
const userColumns = [
  {
    title: '用户名',
    key: 'username',
    width: 120
  },
  {
    title: '邮箱',
    key: 'email',
    width: 200
  },
  {
    title: '姓名',
    key: 'full_name',
    width: 120
  },
  {
    title: '部门',
    key: 'department',
    width: 120
  },
  {
    title: '职位',
    key: 'position',
    width: 120
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row: User) => {
      return h(NTag, {
        type: row.is_active ? 'success' : 'error'
      }, {
        default: () => row.is_active ? '激活' : '禁用'
      })
    }
  },
  {
    title: '权限',
    key: 'is_superuser',
    width: 80,
    render: (row: User) => {
      return h(NTag, {
        type: row.is_superuser ? 'warning' : 'default'
      }, {
        default: () => row.is_superuser ? '管理员' : '普通用户'
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: User) => {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'primary',
            ghost: true,
            onClick: () => handleEditUser(row)
          }, {
            default: () => '编辑',
            icon: () => h(NIcon, { component: CreateOutline })
          }),
          row.is_superuser ? null : h(NPopconfirm, {
            onPositiveClick: () => handleDeleteUser(row)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error',
              ghost: true
            }, {
              default: () => '删除',
              icon: () => h(NIcon, { component: TrashOutline })
            }),
            default: () => '确定删除此用户吗？'
          })
        ].filter(Boolean)
      })
    }
  }
]


// 获取当前用户信息
const loadCurrentUser = async () => {
  try {
    currentUser.value = await authService.getCurrentUser()
  } catch (error) {
    console.error('获取当前用户信息失败:', error)
  }
}

// 加载所有用户
const loadUsers = async () => {
  if (!currentUser.value?.is_superuser) return
  
  try {
    usersLoading.value = true
    users.value = await settingsService.getAllUsers()
  } catch (error: any) {
    console.error('获取用户列表失败:', error)
    message.error('获取用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

// 创建新用户
const handleCreateUser = async () => {
  try {
    await settingsService.createUser(newUserForm.value)
    message.success('用户创建成功')
    showCreateUserModal.value = false
    // 重置表单
    newUserForm.value = {
      username: '',
      email: '',
      password: '',
      full_name: '',
      department: '',
      position: '',
      phone: '',
      is_superuser: false
    }
    // 重新加载用户列表
    loadUsers()
  } catch (error: any) {
    console.error('创建用户失败:', error)
    message.error(error.response?.data?.detail || '创建用户失败')
  }
}

// 编辑用户
const handleEditUser = (user: User) => {
  editingUser.value = user
  editUserForm.value = {
    username: user.username,
    email: user.email,
    full_name: user.full_name || '',
    department: user.department || '',
    position: user.position || '',
    phone: user.phone || '',
    is_active: user.is_active,
    is_superuser: user.is_superuser,
    password: ''  // 密码字段初始为空
  }
  showEditUserModal.value = true
}

// 更新用户信息
const handleUpdateUser = async () => {
  if (!editingUser.value) return
  
  try {
    await settingsService.updateUser(editingUser.value.id, editUserForm.value)
    message.success('用户信息更新成功')
    showEditUserModal.value = false
    editingUser.value = null
    // 重新加载用户列表
    loadUsers()
  } catch (error: any) {
    console.error('更新用户失败:', error)
    message.error(error.response?.data?.detail || '更新用户失败')
  }
}

// 删除用户
  const handleDeleteUser = async (user: User) => {
  if (user.is_superuser) {
    message.error('不能删除管理员账户')
    return
  }
  
  try {
    await settingsService.deleteUser(user.id)
    message.success('用户删除成功')
    // 重新加载用户列表
    loadUsers()
  } catch (error: any) {
    console.error('删除用户失败:', error)
    message.error(error.response?.data?.detail || '删除用户失败')
  }
}

// AI服务相关函数
// 加载AI提供商列表
const loadAIProviders = async () => {
  try {
    console.log('开始加载AI提供商列表...')
    const providers = await getAIProviders()
    console.log('从API获取的AI提供商列表:', providers)

    // 如果API调用成功且返回了数据，使用API数据
    if (providers && providers.length > 0) {
      aiProviders.value = providers
      console.log('使用API返回的提供商列表，数量:', providers.length)

      // 打印每个提供商的详细信息
      providers.forEach((p, index) => {
        console.log(`  提供商 ${index + 1}:`, {
          name: p.name,
          display_name: p.display_name,
          is_available: p.is_available
        })
      })
    } else {
      // API返回空列表，使用硬编码列表
      console.warn('API返回空列表，使用硬编码提供商列表')
      aiProviders.value = hardcodedProviders
      message.warning('API返回空数据，使用本地提供商列表')
    }
  } catch (error: any) {
    console.error('加载AI提供商失败:', error)
    // API失败时使用硬编码列表
    console.warn('使用硬编码提供商列表作为备选方案')
    aiProviders.value = hardcodedProviders
    message.warning('API连接失败，使用本地提供商列表')
  }

  console.log('最终aiProviders.value:', aiProviders.value)
  console.log('最终提供商选项数量:', providerOptions.value.length)
}

// 加载AI配置
const loadAIConfig = async () => {
  try {
    const config = await getAIConfigAPI()
    aiConfig.value = { ...aiConfig.value, ...config }
  } catch (error: any) {
    console.error('加载AI配置失败:', error)
    // 使用默认配置
    message.warning('使用默认AI配置')
  }
}

// 保存AI配置
const saveAIConfig = async () => {
  try {
    savingAIConfig.value = true
    await saveAIConfigAPI(aiConfig.value)
    message.success('AI配置保存成功')
    // 重新加载提供商列表
    await loadAIProviders()
  } catch (error: any) {
    console.error('保存AI配置失败:', error)
    message.error(error.response?.data?.detail || '保存AI配置失败')
  } finally {
    savingAIConfig.value = false
  }
}

// 测试AI连接
const testAIConnection = async () => {
  testingAI.value = true
  try {
    const provider = aiConfig.value.default_provider
    const config = getCurrentProviderConfig()
    
    const result = await testAIConnectionAPI(provider, {
      api_key: config.api_key,
      api_url: config.api_url,
      model: config.model,
      group_id: provider === 'minimax' ? aiConfig.value.providers.minimax.group_id : undefined
    })
    
    if (result.success) {
      message.success(`AI连接测试成功: ${result.message}`)
    } else {
      message.warning(`AI连接测试失败: ${result.message}`)
    }
  } catch (error: any) {
    console.error('测试AI连接失败:', error)
    message.error('AI连接测试失败')
  } finally {
    testingAI.value = false
  }
}

// 加载AI统计
const loadAIStats = async () => {
  try {
    loadingAIStats.value = true
    aiStats.value = await getAIStats()
  } catch (error: any) {
    console.error('加载AI统计失败:', error)
    message.error('加载AI统计数据失败')
  } finally {
    loadingAIStats.value = false
  }
}

// 处理提供商变更
const handleProviderChange = async (provider: string) => {
  aiConfig.value.default_provider = provider
  // 如果是自定义提供商，初始化配置
  if (provider === 'custom' && !aiConfig.value.providers.custom) {
    aiConfig.value.providers.custom = {
      api_key: '',
      api_url: '',
      model: ''
    }
  }
}

// 获取当前提供商的配置
const getCurrentProviderConfig = () => {
  const provider = aiConfig.value.default_provider
  if (provider === 'custom') {
    if (!aiConfig.value.providers.custom) {
      aiConfig.value.providers.custom = {
        api_key: '',
        api_url: '',
        model: ''
      }
    }
    return aiConfig.value.providers.custom
  }
  return aiConfig.value.providers[provider] || {
    api_key: '',
    api_url: '',
    model: ''
  }
}

// 获取默认URL提示
const getDefaultUrlHint = (provider: string) => {
  return defaultUrls[provider] || '请输入API URL'
}

// 获取默认模型提示
const getDefaultModelHint = (provider: string) => {
  return defaultModels[provider] || '请输入模型名称'
}

// 获取提供商显示名称
const getProviderDisplayName = (provider: string) => {
  return providerDisplayNames[provider] || provider
}

// 计算今日成本
const todayCost = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return aiStats.value.daily_costs[today] || 0
})

// 计算提供商选项（用于下拉框）
const providerOptions = computed(() => {
  const options = aiProviders.value.map(provider => ({
    label: provider.display_name,
    value: provider.name
  }))

  // 添加自定义选项（如果不存在）
  if (!options.some(opt => opt.value === 'custom')) {
    options.push({
      label: '自定义',
      value: 'custom'
    })
  }

  console.log('提供商选项列表:', options)
  return options
})

onMounted(() => {
  console.log('SettingsView mounted')
  
  // 直接加载AI相关数据，不依赖于用户登录状态
  loadAIProviders()
  
  loadCurrentUser().then(() => {
    if (currentUser.value?.is_superuser) {
      loadUsers()
    }
    // 加载AI相关数据
    loadAIConfig()
    loadAIStats()
  }).catch((error) => {
    console.error('加载用户信息失败:', error)
    // 即使用户加载失败，也尝试加载AI配置
    loadAIConfig()
    loadAIStats()
  })
})
</script>

<style scoped>
:deep(.n-radio) {
  margin-bottom: 16px;
}

:deep(.n-radio .n-radio__label) {
  padding-left: 12px;
}

/* 确保创建用户按钮的可见性 */
:deep(.n-button.n-button--primary-type) {
  background-color: #18a058 !important;
  color: white !important;
  border-color: #18a058 !important;
}

:deep(.n-button.n-button--primary-type:hover) {
  background-color: #36ad6a !important;
  border-color: #36ad6a !important;
}

:deep(.n-button.n-button--primary-type:active) {
  background-color: #0c7a43 !important;
  border-color: #0c7a43 !important;
}

/* 确保模态框中的按钮也有正确的样式 */
:deep(.n-modal .n-button.n-button--primary-type) {
  background-color: #18a058 !important;
  color: white !important;
  border-color: #18a058 !important;
}
</style>