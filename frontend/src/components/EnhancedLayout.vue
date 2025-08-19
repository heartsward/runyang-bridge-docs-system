<template>
  <n-layout class="layout-container">
    <!-- 顶部导航 -->
    <n-layout-header class="header" bordered>
      <div class="header-content">
        <div class="logo-section">
          <n-icon :size="32" color="#1890ff">
            <DatabaseOutlined />
          </n-icon>
          <h2 class="logo-text">润扬大桥运维文档管理系统</h2>
        </div>
        
        <div class="header-actions">
          <!-- 搜索框 -->
          <div class="search-section">
            <n-input
              v-model:value="searchQuery"
              placeholder="搜索文档或资产..."
              clearable
              :style="{ width: '300px' }"
              @keyup.enter="performSearch"
            >
              <template #prefix>
                <n-icon :component="SearchOutlined" />
              </template>
            </n-input>
          </div>
          
          <!-- 用户菜单 -->
          <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect">
            <n-button quaternary circle>
              <template #icon>
                <n-icon>
                  <UserOutlined />
                </n-icon>
              </template>
            </n-button>
          </n-dropdown>
          
          <!-- 主题切换 -->
          <n-button quaternary circle @click="toggleTheme">
            <template #icon>
              <n-icon>
                <component :is="isDark ? SunOutlined : BulbOutlined" />
              </n-icon>
            </template>
          </n-button>
        </div>
      </div>
    </n-layout-header>

    <n-layout has-sider class="main-layout">
      <!-- 侧边栏 -->
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
        <n-menu
          :collapsed="collapsed"
          :collapsed-width="64"
          :collapsed-icon-size="22"
          :options="menuOptions"
          :value="activeMenu"
          @update:value="handleMenuSelect"
        />
      </n-layout-sider>

      <!-- 主内容区域 -->
      <n-layout-content class="content-area">
        <div class="content-header">
          <!-- 面包屑导航 -->
          <n-breadcrumb>
            <n-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :clickable="item.clickable"
              @click="item.clickable && $router.push(item.path)"
            >
              {{ item.label }}
            </n-breadcrumb-item>
          </n-breadcrumb>
          
          <!-- 页面标题和操作 -->
          <div class="page-header">
            <h1 class="page-title">{{ pageTitle }}</h1>
            <div class="page-actions">
              <slot name="page-actions" />
            </div>
          </div>
        </div>

        <!-- 主要内容 -->
        <div class="content-body">
          <router-view />
        </div>
      </n-layout-content>
    </n-layout>

    <!-- 全局加载指示器 -->
    <n-spin :show="globalLoading" class="global-loading">
      <div style="height: 100vh;" />
    </n-spin>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NLayout,
  NLayoutHeader,
  NLayoutSider,
  NLayoutContent,
  NMenu,
  NButton,
  NIcon,
  NInput,
  NDropdown,
  NBreadcrumb,
  NBreadcrumbItem,
  NSpin,
  useMessage,
  useDialog,
  type MenuOption
} from 'naive-ui'
import {
  DatabaseOutlined,
  SearchOutlined,
  UserOutlined,
  SunOutlined,
  BulbOutlined,
  FileTextOutlined,
  DesktopOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
  FolderOutlined,
  DashboardOutlined
} from '@vicons/antd'
import { authService } from '@/services'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const dialog = useDialog()

// 响应式状态
const collapsed = ref(false)
const searchQuery = ref('')
const globalLoading = ref(false)
const isDark = ref(false)
const currentUser = ref<any>(null)

// 计算属性
const activeMenu = computed(() => route.name as string)

const pageTitle = computed(() => {
  const routeMap: Record<string, string> = {
    documents: '文档管理',
    assets: '资产管理',
    analytics: '数据分析',
    categories: '分类管理',
    settings: '系统设置',
    search: '搜索结果'
  }
  return routeMap[route.name as string] || '润扬大桥运维文档管理系统'
})

const breadcrumbs = computed(() => {
  const crumbs = [{ label: '首页', path: '/', clickable: true }]
  
  if (route.name === 'documents') {
    crumbs.push({ label: '文档管理', path: '/documents', clickable: false })
  } else if (route.name === 'assets') {
    crumbs.push({ label: '资产管理', path: '/assets', clickable: false })
  } else if (route.name === 'analytics') {
    crumbs.push({ label: '数据分析', path: '/analytics', clickable: false })
  } else if (route.name === 'categories') {
    crumbs.push({ label: '分类管理', path: '/categories', clickable: false })
  } else if (route.name === 'settings') {
    crumbs.push({ label: '系统设置', path: '/settings', clickable: false })
  }
  
  return crumbs
})

// 菜单选项
const menuOptions = computed(() => {
  const options: MenuOption[] = [
    {
      label: '工作台',
      key: 'dashboard',
      icon: () => h(NIcon, null, { default: () => h(DashboardOutlined) })
    },
    {
      label: '文档管理',
      key: 'documents',
      icon: () => h(NIcon, null, { default: () => h(FileTextOutlined) })
    },
    {
      label: '资产管理',
      key: 'assets',
      icon: () => h(NIcon, null, { default: () => h(DesktopOutlined) })
    },
    {
      label: '分类管理',
      key: 'categories',
      icon: () => h(NIcon, null, { default: () => h(FolderOutlined) })
    }
  ]

  // 管理员菜单
  if (currentUser.value?.is_superuser) {
    options.push(
      {
        label: '数据分析',
        key: 'analytics',
        icon: () => h(NIcon, null, { default: () => h(BarChartOutlined) })
      },
      {
        label: '系统设置',
        key: 'settings',
        icon: () => h(NIcon, null, { default: () => h(SettingOutlined) })
      }
    )
  }

  return options
})

// 用户菜单选项
const userMenuOptions = computed(() => [
  {
    label: `用户：${currentUser.value?.username || '未知'}`,
    key: 'user-info',
    disabled: true
  },
  {
    type: 'divider',
    key: 'divider'
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogoutOutlined) })
  }
])

// 方法
const handleMenuSelect = (key: string) => {
  router.push(`/${key}`)
}

const handleUserMenuSelect = (key: string) => {
  if (key === 'logout') {
    handleLogout()
  }
}

const handleLogout = () => {
  dialog.warning({
    title: '确认退出',
    content: '确定要退出登录吗？',
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: () => {
      authService.logout()
      router.push('/login')
      message.success('已退出登录')
    }
  })
}

const performSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      name: 'search',
      query: { q: searchQuery.value }
    })
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  // 这里可以添加主题切换逻辑
}

const loadCurrentUser = async () => {
  try {
    currentUser.value = await authService.getCurrentUser()
  } catch (error) {
    console.error('加载用户信息失败:', error)
  }
}

// 生命周期
onMounted(async () => {
  // 加载主题设置
  const savedTheme = localStorage.getItem('theme')
  isDark.value = savedTheme === 'dark'
  
  // 加载当前用户信息
  if (authService.isAuthenticated()) {
    await loadCurrentUser()
  }
})

// 监听路由变化
watch(route, () => {
  // 可以在这里添加路由变化时的逻辑
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.header {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-text {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-section {
  display: flex;
  align-items: center;
}

.main-layout {
  height: calc(100vh - 64px);
}

.content-area {
  padding: 0;
  overflow: hidden;
}

.content-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fff;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.page-actions {
  display: flex;
  gap: 8px;
}

.content-body {
  padding: 24px;
  height: calc(100vh - 64px - 80px);
  overflow-y: auto;
}

.global-loading {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: 12px;
  }
  
  .search-section {
    width: 100%;
  }
  
  .search-section .n-input {
    width: 100% !important;
  }
  
  .content-body {
    padding: 16px;
  }
}

/* 暗色主题支持 */
.dark .content-header {
  background: #1f1f1f;
  border-bottom-color: #333;
}

.dark .logo-text {
  color: #1890ff;
}
</style>