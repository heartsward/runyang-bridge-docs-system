import { createRouter, createWebHistory } from 'vue-router'
import WelcomeView from '../views/WelcomeView.vue'
import DocumentView from '../views/DocumentView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'welcome',
      component: WelcomeView,
      meta: { requiresAuth: false }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresGuest: true }
    },
    {
      path: '/documents',
      name: 'documents',
      component: DocumentView,
      meta: { requiresAuth: true }
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('../views/SearchView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: () => import('../views/AnalyticsView.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/assets',
      name: 'assets',
      component: () => import('../views/AssetView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/categories',
      name: 'categories',
      component: () => import('../views/CategoryView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { requiresAuth: true }
    },
  ],
})

// Import authService for route guards
import { authService } from '@/services'

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest)
  
  console.log('路由守卫检查:', {
    path: to.path,
    requiresAuth,
    requiresAdmin,
    requiresGuest,
    isAuthenticated: authService.isAuthenticated()
  })
  
  if (requiresGuest && authService.isAuthenticated()) {
    // 如果路由需要访客状态，但用户已登录，重定向到文档页面
    console.log('已登录用户访问访客页面，重定向到文档页面')
    next('/documents')
    return
  }
  
  if (requiresAuth && !authService.isAuthenticated()) {
    // 如果路由需要认证，但用户未登录，重定向到登录页面
    console.log('未登录用户访问需要认证的页面，重定向到登录页面')
    next('/login')
    return
  }
  
  if (requiresAdmin) {
    try {
      // 如果路由需要管理员权限，检查用户权限
      if (!authService.isAuthenticated()) {
        console.log('未登录用户访问管理员页面，重定向到登录页面')
        next('/login')
        return
      }
      
      const user = await authService.getCurrentUser()
      console.log('检查管理员权限:', user?.is_superuser)
      
      if (!user?.is_superuser) {
        // 普通用户尝试访问管理员页面，重定向到文档页面并显示错误
        console.warn('普通用户尝试访问管理员页面:', to.path)
        next('/documents')
        return
      }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，清除token并重定向到登录页面
      authService.logout()
      next('/login')
      return
    }
  }
  
  console.log('路由守卫通过，允许访问')
  next()
})

export default router
