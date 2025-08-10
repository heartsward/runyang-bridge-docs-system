<template>
  <n-layout has-sider>
    <n-layout-sider
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :width="240"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
    >
      <div class="logo-container">
        <div v-if="!collapsed" class="logo-full">
          <img src="/runyang-logo.svg" alt="润扬大桥匠心工作室" class="logo-image" />
          <div class="system-name">
            <div class="main-title">润扬大桥</div>
            <div class="sub-title">运维文档管理系统</div>
          </div>
        </div>
        <div v-else class="logo-collapsed">
          <img src="/runyang-logo.svg" alt="润扬大桥匠心工作室" class="logo-icon" />
        </div>
      </div>
      
      <n-menu
        v-model:value="activeKey"
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        @update:value="handleMenuClick"
      />
      
      <!-- 用户信息区域移至左侧底部 -->
      <div class="user-section">
        <div v-if="userLoading && !collapsed">
          <n-space justify="center">
            <n-spin size="small" />
            <n-text depth="3">加载中...</n-text>
          </n-space>
        </div>
        <div v-else-if="currentUser">
          <n-dropdown :options="userDropdownOptions" @select="handleUserAction" placement="top-start">
            <div class="user-card-sidebar">
              <n-avatar
                round
                :size="collapsed ? 'medium' : 'small'"
                :src="'/runyang-logo.svg'"
                :fallback-src="'/runyang-logo.svg'"
              />
              <div v-if="!collapsed" class="user-text-sidebar">
                <div class="username-sidebar">{{ currentUser.username }}</div>
                <div class="user-role-sidebar">{{ currentUser.is_superuser ? '系统管理员' : '普通用户' }}</div>
              </div>
            </div>
          </n-dropdown>
        </div>
        <div v-else-if="!collapsed && !userLoading">
          <n-space size="small" vertical>
            <n-button type="primary" size="small" @click="$router.push('/login')" block>
              登录
            </n-button>
            <n-button size="small" @click="$router.push('/register')" block>
              注册
            </n-button>
          </n-space>
        </div>
      </div>
    </n-layout-sider>
    <n-layout>
      <n-layout-content>
        <slot />
      </n-layout-content>
    </n-layout>
    
    <!-- 修改密码模态框 -->
    <n-modal v-model:show="showChangePasswordModal" preset="dialog" title="修改密码">
      <n-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules">
        <n-form-item label="当前密码" path="currentPassword">
          <n-input
            v-model:value="passwordForm.currentPassword"
            type="password"
            placeholder="请输入当前密码"
            show-password-on="click"
            autocomplete="current-password"
          />
        </n-form-item>
        <n-form-item label="新密码" path="newPassword">
          <n-input
            v-model:value="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password-on="click"
            autocomplete="new-password"
          />
        </n-form-item>
        <n-form-item label="确认密码" path="confirmPassword">
          <n-input
            v-model:value="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password-on="click"
            autocomplete="new-password"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showChangePasswordModal = false">取消</n-button>
          <n-button type="primary" @click="handleChangePassword" :loading="changingPassword">确认修改</n-button>
        </n-space>
      </template>
    </n-modal>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, h, onMounted, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NH3,
  NIcon,
  NDropdown,
  NAvatar,
  NButton,
  NSpace,
  NModal,
  NForm,
  NFormItem,
  NInput,
  NSpin,
  NText,
  useMessage
} from 'naive-ui'
import {
  DocumentTextOutline,
  SearchOutline,
  BarChartOutline,
  SettingsOutline,
  PersonOutline,
  LogOutOutline,
  HardwareChipOutline
} from '@vicons/ionicons5'
import { authService } from '@/services'
import type { User } from '@/types/api'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const collapsed = ref(false)
const activeKey = ref('documents')
const currentUser = ref<User | null>(null)
const userLoading = ref(true)

// 修改密码相关
const showChangePasswordModal = ref(false)
const changingPassword = ref(false)
const passwordFormRef = ref()
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  currentPassword: {
    required: true,
    message: '请输入当前密码',
    trigger: 'blur'
  },
  newPassword: [
    {
      required: true,
      message: '请输入新密码',
      trigger: 'blur'
    },
    {
      min: 6,
      message: '密码长度不能少于6位',
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    {
      required: true,
      message: '请确认密码',
      trigger: 'blur'
    },
    {
      validator: (rule: any, value: string) => {
        return value === passwordForm.value.newPassword
      },
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

// 动态生成菜单选项，根据用户权限过滤
const menuOptions = computed(() => {
  const baseOptions = [
    {
      label: '文档管理',
      key: 'documents',
      icon: () => h(NIcon, { component: DocumentTextOutline })
    },
    {
      label: '设备资产',
      key: 'assets',
      icon: () => h(NIcon, { component: HardwareChipOutline })
    },
    {
      label: '智能搜索',
      key: 'search',
      icon: () => h(NIcon, { component: SearchOutline })
    },
    {
      label: '系统设置',
      key: 'settings',
      icon: () => h(NIcon, { component: SettingsOutline })
    }
  ]

  // 只有管理员才能看到数据分析模块
  if (currentUser.value?.is_superuser) {
    baseOptions.splice(3, 0, {
      label: '数据分析',
      key: 'analytics',
      icon: () => h(NIcon, { component: BarChartOutline })
    })
  }

  return baseOptions
})

const userDropdownOptions = [
  {
    label: '个人设置',
    key: 'profile',
    icon: () => h(NIcon, { component: PersonOutline })
  },
  {
    label: '修改密码',
    key: 'change-password',
    icon: () => h(NIcon, { component: SettingsOutline })
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, { component: LogOutOutline })
  }
]

const handleMenuClick = (key: string) => {
  activeKey.value = key
  switch (key) {
    case 'documents':
      router.push('/documents')
      break
    case 'assets':
      router.push('/assets')
      break
    case 'search':
      router.push('/search')
      break
    case 'analytics':
      // 只有管理员才能访问数据分析
      if (currentUser.value?.is_superuser) {
        router.push('/analytics')
      } else {
        message.error('您没有权限访问数据分析模块，请联系管理员')
        return
      }
      break
    case 'categories':
      router.push('/categories')
      break
    case 'settings':
      router.push('/settings')
      break
  }
}

const handleUserAction = (key: string) => {
  switch (key) {
    case 'profile':
      // TODO: 实现个人设置页面
      message.info('个人设置功能开发中...')
      break
    case 'change-password':
      showChangePasswordModal.value = true
      break
    case 'logout':
      handleLogout()
      break
  }
}

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value?.validate()
    changingPassword.value = true
    
    console.log('准备修改密码...')
    console.log('当前用户认证状态:', authService.isAuthenticated())
    const token = authService.getToken()
    console.log('当前token:', token ? token.substring(0, 20) + '...' : 'null')
    
    // 调用API修改密码
    const result = await authService.changePassword({
      current_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword
    })
    
    console.log('密码修改结果:', result)
    message.success('密码修改成功')
    showChangePasswordModal.value = false
    
    // 清空表单
    passwordForm.value = {
      currentPassword: '',
      newPassword: '',
      confirmPassword: ''
    }
  } catch (error: any) {
    console.error('修改密码错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message,
      fullError: error
    })
    
    let errorMessage = '密码修改失败'
    if (error.response?.status === 401) {
      errorMessage = '认证失败，请重新登录'
    } else if (error.response?.status === 400) {
      errorMessage = error.response?.data?.detail || '当前密码错误'
    } else if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.message) {
      errorMessage = error.message
    }
    
    message.error(errorMessage)
  } finally {
    changingPassword.value = false
  }
}

const handleLogout = () => {
  authService.logout()
  message.success('已退出登录')
  router.push('/login')
}

const loadCurrentUser = async () => {
  try {
    userLoading.value = true
    if (authService.isAuthenticated()) {
      console.log('开始获取用户信息...')
      currentUser.value = await authService.getCurrentUser()
      console.log('用户信息获取成功:', currentUser.value)
    } else {
      console.log('用户未登录')
      currentUser.value = null
    }
  } catch (error: any) {
    console.error('获取用户信息失败:', error)
    // 如果获取用户信息失败，可能是token过期，直接退出登录
    authService.logout()
    currentUser.value = null
    // 只有在需要认证的页面才跳转到登录页
    if (router.currentRoute.value.meta.requiresAuth) {
      console.log('跳转到登录页面')
      router.push('/login')
    }
  } finally {
    userLoading.value = false
  }
}

const updateActiveKey = () => {
  const path = route.path
  if (path.startsWith('/documents')) {
    activeKey.value = 'documents'
  } else if (path.startsWith('/assets')) {
    activeKey.value = 'assets'
  } else if (path.startsWith('/search')) {
    activeKey.value = 'search'
  } else if (path.startsWith('/analytics')) {
    activeKey.value = 'analytics'
  } else if (path.startsWith('/categories')) {
    activeKey.value = 'categories'
  } else if (path.startsWith('/settings')) {
    activeKey.value = 'settings'
  }
}

// Watch for route changes to update active key
watch(route, updateActiveKey, { immediate: true })

onMounted(() => {
  loadCurrentUser()
})
</script>

<style scoped>
/* 智慧高速主题色彩 */
:root {
  --runyang-primary: #8B4513;
  --runyang-secondary: #A0522D;
  --runyang-light: #F5F5DC;
  --runyang-accent: #CD853F;
  --runyang-shadow: rgba(139, 69, 19, 0.1);
}

.logo-container {
  border-bottom: 2px solid var(--runyang-primary);
  background: linear-gradient(135deg, var(--runyang-light) 0%, #FAFAFA 100%);
  box-shadow: 0 2px 8px var(--runyang-shadow);
}

.logo-full {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
}

.logo-collapsed {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.logo-image {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(139, 69, 19, 0.2);
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(139, 69, 19, 0.2);
}

.system-name {
  flex: 1;
  text-align: left;
}

.main-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--runyang-primary);
  margin-bottom: 2px;
  letter-spacing: 0.5px;
}

.sub-title {
  font-size: 11px;
  color: var(--runyang-secondary);
  font-weight: 500;
  opacity: 0.9;
}

/* 侧边栏样式调整，确保用户区域在底部 */
:deep(.n-layout-sider) {
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #FEFEFE 0%, #F8F9FA 100%);
  border-right: 2px solid #E8E8E8;
}

:deep(.n-layout-sider .n-menu) {
  flex: 1;
  background: transparent;
}

/* 菜单项样式优化 */
:deep(.n-menu .n-menu-item) {
  margin: 4px 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.n-menu .n-menu-item:hover) {
  background: linear-gradient(135deg, var(--runyang-light) 0%, #E8E8E8 100%);
  box-shadow: 0 2px 4px var(--runyang-shadow);
}

:deep(.n-menu .n-menu-item.n-menu-item--selected) {
  background: linear-gradient(135deg, var(--runyang-primary) 0%, var(--runyang-secondary) 100%);
  color: white;
  box-shadow: 0 4px 8px rgba(139, 69, 19, 0.3);
}

:deep(.n-menu .n-menu-item.n-menu-item--selected .n-menu-item-content-header) {
  color: white;
}

:deep(.n-menu .n-menu-item.n-menu-item--selected .n-icon) {
  color: white;
}

.user-section {
  margin-top: auto;
  padding: 16px;
  border-top: 2px solid var(--runyang-primary);
  background: linear-gradient(135deg, var(--runyang-light) 0%, #FAFAFA 100%);
  box-shadow: 0 -2px 8px var(--runyang-shadow);
}

.user-card-sidebar {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 12px;
  border-radius: 12px;
  transition: all 0.3s ease;
  width: 100%;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(139, 69, 19, 0.2);
}

.user-card-sidebar:hover {
  background: linear-gradient(135deg, #FFFFFF 0%, var(--runyang-light) 100%);
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.2);
  transform: translateY(-1px);
}

.user-text-sidebar {
  flex: 1;
  min-width: 0;
}

.username-sidebar {
  font-size: 13px;
  font-weight: 600;
  color: var(--runyang-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.user-role-sidebar {
  font-size: 11px;
  color: var(--runyang-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}
</style>