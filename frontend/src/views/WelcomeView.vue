<template>
  <div class="welcome-view">
    <!-- 使用原始的WelcomeView，但已登录用户会被重定向到documents页面 -->
    <div class="hero-section">
      <n-space vertical align="center" style="text-align: center; padding: 80px 20px;">
        <n-icon :component="ServerOutline" size="120" color="#667eea" />
        <n-h1 style="font-size: 3rem; margin: 20px 0;">润扬大桥运维文档管理系统</n-h1>
        <n-text style="font-size: 1.2rem; color: #666; margin-bottom: 40px;">
          高效管理运维文档，智能搜索分类，提升运维效率
        </n-text>
        <n-space size="large">
          <n-button type="primary" size="large" @click="handleStartUse">
            开始使用
          </n-button>
          <n-button size="large" @click="handleSearch">
            智能搜索
          </n-button>
        </n-space>
      </n-space>
    </div>

    <div class="features-section">
      <n-layout content-style="padding: 60px 20px;">
        <n-space vertical size="large">
          <n-h2 style="text-align: center; margin-bottom: 40px;">核心功能</n-h2>
          <n-grid cols="1 s:2 m:3" responsive="screen" :x-gap="24" :y-gap="24">
            <n-grid-item>
              <n-card hoverable style="height: 200px; text-align: center;">
                <n-space vertical align="center" style="height: 100%;" justify="center">
                  <n-icon :component="DocumentTextOutline" size="48" color="#2080f0" />
                  <n-h3>文档管理</n-h3>
                  <n-text depth="3">
                    支持多格式文档上传，自动分类整理，版本控制
                  </n-text>
                </n-space>
              </n-card>
            </n-grid-item>
            
            <n-grid-item>
              <n-card hoverable style="height: 200px; text-align: center;">
                <n-space vertical align="center" style="height: 100%;" justify="center">
                  <n-icon :component="SearchOutline" size="48" color="#f0a020" />
                  <n-h3>智能搜索</n-h3>
                  <n-text depth="3">
                    基于Elasticsearch全文检索，NLP智能分类
                  </n-text>
                </n-space>
              </n-card>
            </n-grid-item>
            
            <n-grid-item>
              <n-card hoverable style="height: 200px; text-align: center;">
                <n-space vertical align="center" style="height: 100%;" justify="center">
                  <n-icon :component="BarChartOutline" size="48" color="#d03050" />
                  <n-h3>数据分析</n-h3>
                  <n-text depth="3">
                    使用统计分析，热门文档排行，访问趋势图表
                  </n-text>
                </n-space>
              </n-card>
            </n-grid-item>
          </n-grid>
        </n-space>
      </n-layout>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  NLayout,
  NLayoutContent,
  NSpace,
  NH1,
  NH3,
  NText,
  NButton,
  NIcon,
  NGrid,
  NGridItem,
  NCard,
  NList,
  NListItem
} from 'naive-ui'
import {
  ServerOutline,
  DocumentTextOutline,
  SearchOutline,
  BarChartOutline,
  CloudUploadOutline
} from '@vicons/ionicons5'
import NavigationMenu from '../components/NavigationMenu.vue'
import { authService } from '@/services'

const router = useRouter()

interface RecentDocument {
  id: string
  title: string
  type: string
  lastAccess: string
}

const recentDocuments = ref<RecentDocument[]>([
  {
    id: '1',
    title: 'Nginx配置指南',
    type: '配置文档',
    lastAccess: '2024-01-25'
  },
  {
    id: '2',
    title: '数据库故障排查手册',
    type: '故障排查',
    lastAccess: '2024-01-24'
  },
  {
    id: '3',
    title: '服务器监控报告',
    type: '监控报告',
    lastAccess: '2024-01-23'
  }
])

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const handleStartUse = () => {
  if (authService.isAuthenticated()) {
    router.push('/documents')
  } else {
    router.push('/login')
  }
}

const handleSearch = () => {
  if (authService.isAuthenticated()) {
    router.push('/search')
  } else {
    router.push('/login')
  }
}

const handleAnalytics = () => {
  if (authService.isAuthenticated()) {
    router.push('/analytics')
  } else {
    router.push('/login')
  }
}

const viewDocument = (doc: RecentDocument) => {
  if (authService.isAuthenticated()) {
    console.log('查看文档:', doc.title)
    router.push('/documents')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
.welcome-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.hero-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.features-section {
  background: #f5f5f5;
}
</style>