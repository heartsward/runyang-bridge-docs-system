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
    
    <!-- 阶段七：统一 AI 多模态服务 -->
    <n-card title="统一 AI 多模态服务（文档提取）" style="margin-bottom: 24px;">
      <template #header-extra>
        <n-space>
          <n-button size="small" @click="loadExtractionConfig" :loading="loadingExtractionConfig">
            <template #icon><n-icon><RefreshOutline /></n-icon></template>
            刷新
          </n-button>
          <n-button type="primary" size="small" @click="testExtractionConnection" :loading="testingExtractionConfig">
            <template #icon><n-icon><FlashOutline /></n-icon></template>
            测试连接
          </n-button>
        </n-space>
      </template>

      <n-alert v-if="extractionConfigRestartRequired" type="warning" :show-icon="true" style="margin-bottom: 16px;">
        配置已保存到 .env，但需重启后端服务才能生效。
      </n-alert>

      <n-alert type="info" :show-icon="true" style="margin-bottom: 16px;">
        一个多模态模型（如 Qwen3-VL / Qwen2.5-VL）可处理 PDF / 图片，开启"所有格式"后也可规整 Word/Excel/文本。
        推荐本地用 <strong>llama.cpp</strong> server 或 <strong>vLLM</strong>，或在线 DashScope。保存后<strong>立即生效</strong>，无需重启。
      </n-alert>

      <!-- 总开关 -->
      <n-form-item label="启用 AI 服务">
        <n-switch v-model:value="extractionConfig.ai_service_enabled" />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">
            文档转换由 anydoc 引擎负责（毫秒级，全格式）；
            关闭时扫描件/图片不再调用多模态 AI 识别，仅做本地文本层提取
          </n-text>
        </template>
      </n-form-item>

      <!-- Provider 选择 -->
      <n-form-item label="服务类型">
        <n-select
          v-model:value="extractionConfig.ai_service_provider"
          :options="[
            { label: 'OpenAI 兼容（llama.cpp server / vLLM / DashScope）', value: 'openai' },
            { label: 'Ollama（本地）', value: 'ollama' },
          ]"
          style="width: 360px;"
          :disabled="!extractionConfig.ai_service_enabled"
        />
      </n-form-item>

      <!-- 服务地址 -->
      <n-form-item label="服务地址">
        <n-input
          v-model:value="extractionConfig.ai_service_url"
          placeholder="http://localhost:8080/v1"
          style="width: 500px;"
          :disabled="!extractionConfig.ai_service_enabled"
        />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">
            常见：llama.cpp <code>http://localhost:8080/v1</code> | Ollama <code>http://localhost:11434</code> |
            DashScope <code>https://dashscope.aliyuncs.com/compatible-mode/v1</code>
          </n-text>
        </template>
      </n-form-item>

      <!-- 模型名 -->
      <n-form-item label="模型名">
        <n-input
          v-model:value="extractionConfig.ai_service_model"
          placeholder="qwen3-vl-8b"
          style="width: 300px;"
          :disabled="!extractionConfig.ai_service_enabled"
        />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">
            llama.cpp 不严格校验，任意字符串均可；Ollase 用实际 tag 名
          </n-text>
        </template>
      </n-form-item>

      <!-- API Key（仅在线服务需要） -->
      <n-form-item label="API Key（仅在线服务需要）">
        <n-input
          v-model:value="extractionConfig.ai_service_api_key"
          type="password"
          show-password-on="click"
          placeholder="本地服务留空"
          style="width: 500px;"
          :disabled="!extractionConfig.ai_service_enabled"
        />
      </n-form-item>

      <!-- 超时 -->
      <n-form-item label="调用超时（秒）">
        <n-input-number
          v-model:value="extractionConfig.ai_service_timeout"
          :min="10"
          :max="600"
          :step="10"
          style="width: 200px;"
        />
      </n-form-item>

      <!-- 降级 -->
      <n-form-item label="AI 失败时降级到本地引擎">
        <n-switch v-model:value="extractionConfig.ai_fallback_to_local" />
        <template #feedback>
          <n-text depth="3" style="font-size: 12px;">推荐开启：服务挂了不至于文档全失败</n-text>
        </template>
      </n-form-item>

      <!-- 测试结果（阶段十四：含模型名校验） -->
      <div v-if="extractionTestResult" style="margin-top: 16px;">
        <template v-if="aiServiceTest">
          <n-alert
            :type="aiServiceTest.reachable ? (aiServiceTest.model && !aiServiceTest.model.found ? 'warning' : 'success') : 'error'"
            :show-icon="true"
            style="margin-bottom: 8px;"
          >
            <div>服务地址：<code>{{ aiServiceTest.endpoint || extractionConfig.ai_service_url }}</code>
              — {{ aiServiceTest.reachable ? `可达（HTTP ${aiServiceTest.status}` : '不可达' }}</div>
          </n-alert>
          <n-alert v-if="aiServiceTest.model" :type="aiServiceTest.model.found ? 'success' : 'error'" :show-icon="true" style="margin-bottom: 8px;">
            <div v-if="aiServiceTest.model.found">
              模型 <code>{{ aiServiceTest.model.requested }}</code> 在服务中已加载，可用。
            </div>
            <template v-else>
              <div>未在服务中找到模型 <code>{{ aiServiceTest.model.requested }}</code>。</div>
              <div v-if="aiServiceTest.model.hint" style="margin-top: 4px; font-size: 12px;">{{ aiServiceTest.model.hint }}</div>
              <div v-if="aiServiceTest.model.available_models.length" style="margin-top: 6px; font-size: 12px;">
                服务实际加载的模型（点击填入"模型名"）：
                <div style="margin-top: 4px;">
                  <n-tag
                    v-for="m in aiServiceTest.model.available_models"
                    :key="m"
                    size="small"
                    style="cursor: pointer; margin: 2px 4px 2px 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis;"
                    @click="extractionConfig.ai_service_model = m"
                  >
                    {{ m }}
                  </n-tag>
                </div>
              </div>
            </template>
          </n-alert>
          <n-alert v-else-if="!aiServiceTest.reachable" type="error" :show-icon="true">
            连接失败：{{ aiServiceTest.error || `HTTP ${aiServiceTest.status}` }}
          </n-alert>
        </template>
        <n-alert v-else type="info" :show-icon="true">AI 服务未启用，未执行连接测试。</n-alert>
      </div>

      <!-- 保存 -->
      <div style="margin-top: 24px;">
        <n-button
          type="primary"
          @click="saveExtractionConfig"
          :loading="savingExtractionConfig"
        >
          保存 AI 服务配置
        </n-button>
      </div>
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
  FlashOutline
} from '@vicons/ionicons5'
import PageLayout from '@/components/PageLayout.vue'
import { settingsService, authService } from '@/services'
import { RefreshOutline } from '@vicons/ionicons5'
import {
  extractionConfigService,
  type ExtractionConfig,
  type TestResult as ExtractionTestResult,
} from '@/services/extraction-config'

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

// 初始化为硬编码列表，确保下拉框始终有选项
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
const extractionConfig = ref<ExtractionConfig>({
  ai_service_enabled: false,
  ai_service_provider: 'openai',
  ai_service_url: 'http://localhost:8080/v1',
  ai_service_model: 'qwen3-vl-8b',
  ai_service_api_key: '',
  ai_service_timeout: 120,
  ai_fallback_to_local: true,
  ai_ocr_enabled: false,
  ai_ocr_service_url: 'http://localhost:8001',
})
const loadingExtractionConfig = ref(false)
const savingExtractionConfig = ref(false)
const testingExtractionConfig = ref(false)
const extractionConfigRestartRequired = ref(false)
const extractionTestResult = ref<ExtractionTestResult | null>(null)

// 阶段十四：AI 服务测试结果的 ai_service 块（含模型名校验）
const aiServiceTest = computed(() => extractionTestResult.value?.results?.ai_service ?? null)

const loadExtractionConfig = async () => {
  loadingExtractionConfig.value = true
  try {
    extractionConfig.value = await extractionConfigService.getConfig()
    extractionConfigRestartRequired.value = false
  } catch (e: any) {
    message.error('加载 AI 引擎配置失败：' + (e?.message || '未知错误'))
  } finally {
    loadingExtractionConfig.value = false
  }
}

const saveExtractionConfig = async () => {
  savingExtractionConfig.value = true
  try {
    const result = await extractionConfigService.updateConfig(extractionConfig.value)
    if (result.restart_required) {
      extractionConfigRestartRequired.value = true
      message.warning(result.message)
    } else {
      message.success('配置已保存')
    }
  } catch (e: any) {
    message.error('保存失败：' + (e?.message || '未知错误'))
  } finally {
    savingExtractionConfig.value = false
  }
}

const testExtractionConnection = async () => {
  testingExtractionConfig.value = true
  extractionTestResult.value = null
  try {
    const result = await extractionConfigService.testConnection(extractionConfig.value)
    extractionTestResult.value = result
    message.success('测试完成（详见下方结果）')
  } catch (e: any) {
    message.error('测试失败：' + (e?.message || '未知错误'))
  } finally {
    testingExtractionConfig.value = false
  }
}

onMounted(() => {
  console.log('SettingsView mounted')

  // 直接加载AI相关数据，不依赖于用户登录状态
  // 阶段十七修复：重构后遗漏了配置加载调用，导致设置页打开时 AI 配置从不拉取、
  // 一直停留在默认值（用户配置的 enabled/url/model 实际安全存于后端）。补上加载。
  loadExtractionConfig()

  loadCurrentUser().then(() => {
    if (currentUser.value?.is_superuser) {
      loadUsers()
    }
  }).catch((error) => {
    console.error('加载用户信息失败:', error)
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