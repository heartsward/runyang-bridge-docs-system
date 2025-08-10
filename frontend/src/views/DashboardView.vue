<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" class="stats-grid">
      <n-grid-item :span="1">
        <n-card class="stat-card">
          <template #header>
            <div class="stat-header">
              <n-icon size="24" color="#1890ff">
                <FileTextOutlined />
              </n-icon>
              <span>文档总数</span>
            </div>
          </template>
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalDocuments }}</div>
            <div class="stat-trend">
              <n-icon :color="stats.documentTrend > 0 ? '#52c41a' : '#ff4d4f'">
                <ArrowUpOutlined v-if="stats.documentTrend > 0" />
                <ArrowDownOutlined v-else />
              </n-icon>
              <span>{{ Math.abs(stats.documentTrend) }}%</span>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item :span="1">
        <n-card class="stat-card">
          <template #header>
            <div class="stat-header">
              <n-icon size="24" color="#52c41a">
                <DesktopOutlined />
              </n-icon>
              <span>资产设备</span>
            </div>
          </template>
          <div class="stat-content">
            <div class="stat-number">{{ stats.totalAssets }}</div>
            <div class="stat-trend">
              <n-icon :color="stats.assetTrend > 0 ? '#52c41a' : '#ff4d4f'">
                <ArrowUpOutlined v-if="stats.assetTrend > 0" />
                <ArrowDownOutlined v-else />
              </n-icon>
              <span>{{ Math.abs(stats.assetTrend) }}%</span>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item :span="1">
        <n-card class="stat-card">
          <template #header>
            <div class="stat-header">
              <n-icon size="24" color="#fa8c16">
                <UserOutlined />
              </n-icon>
              <span>活跃用户</span>
            </div>
          </template>
          <div class="stat-content">
            <div class="stat-number">{{ stats.activeUsers }}</div>
            <div class="stat-trend">
              <n-icon :color="stats.userTrend > 0 ? '#52c41a' : '#ff4d4f'">
                <ArrowUpOutlined v-if="stats.userTrend > 0" />
                <ArrowDownOutlined v-else />
              </n-icon>
              <span>{{ Math.abs(stats.userTrend) }}%</span>
            </div>
          </div>
        </n-card>
      </n-grid-item>
      
      <n-grid-item :span="1">
        <n-card class="stat-card">
          <template #header>
            <div class="stat-header">
              <n-icon size="24" color="#722ed1">
                <EyeOutlined />
              </n-icon>
              <span>今日访问</span>
            </div>
          </template>
          <div class="stat-content">
            <div class="stat-number">{{ stats.todayViews }}</div>
            <div class="stat-trend">
              <n-icon :color="stats.viewTrend > 0 ? '#52c41a' : '#ff4d4f'">
                <ArrowUpOutlined v-if="stats.viewTrend > 0" />
                <ArrowDownOutlined v-else />
              </n-icon>
              <span>{{ Math.abs(stats.viewTrend) }}%</span>
            </div>
          </div>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 主要内容区域 -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" class="content-grid">
      <!-- 快捷操作 -->
      <n-grid-item>
        <n-card title="快捷操作" class="quick-actions-card">
          <n-space vertical size="large">
            <n-button
              type="primary"
              size="large"
              block
              @click="$router.push('/documents')"
            >
              <template #icon>
                <n-icon><PlusOutlined /></n-icon>
              </template>
              上传文档
            </n-button>
            
            <n-button
              type="success"
              size="large"
              block
              @click="$router.push('/assets')"
            >
              <template #icon>
                <n-icon><DesktopOutlined /></n-icon>
              </template>
              添加资产
            </n-button>
            
            <n-button
              size="large"
              block
              @click="$router.push('/search')"
            >
              <template #icon>
                <n-icon><SearchOutlined /></n-icon>
              </template>
              搜索内容
            </n-button>
          </n-space>
        </n-card>
      </n-grid-item>

      <!-- 最近文档 -->
      <n-grid-item>
        <n-card title="最近文档" class="recent-docs-card">
          <n-list>
            <n-list-item
              v-for="doc in recentDocuments"
              :key="doc.id"
              class="recent-item"
              @click="viewDocument(doc.id)"
            >
              <template #prefix>
                <n-icon color="#1890ff">
                  <FileTextOutlined />
                </n-icon>
              </template>
              <n-thing>
                <template #header>
                  <span class="doc-title">{{ doc.title }}</span>
                </template>
                <template #description>
                  <span class="doc-time">{{ formatTime(doc.created_at) }}</span>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
          
          <template #action>
            <n-button text @click="$router.push('/documents')">
              查看全部
            </n-button>
          </template>
        </n-card>
      </n-grid-item>

      <!-- 最近资产 -->
      <n-grid-item>
        <n-card title="最近资产" class="recent-assets-card">
          <n-list>
            <n-list-item
              v-for="asset in recentAssets"
              :key="asset.id"
              class="recent-item"
              @click="viewAsset(asset.id)"
            >
              <template #prefix>
                <n-icon :color="getAssetStatusColor(asset.status)">
                  <DesktopOutlined />
                </n-icon>
              </template>
              <n-thing>
                <template #header>
                  <span class="asset-name">{{ asset.name }}</span>
                </template>
                <template #description>
                  <n-tag :type="getAssetStatusType(asset.status)" size="small">
                    {{ getAssetStatusText(asset.status) }}
                  </n-tag>
                  <span class="asset-ip">{{ asset.ip_address }}</span>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
          
          <template #action>
            <n-button text @click="$router.push('/assets')">
              查看全部
            </n-button>
          </template>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 系统状态和图表 -->
    <n-grid :cols="2" :x-gap="16" :y-gap="16" class="charts-grid">
      <!-- 系统状态 -->
      <n-grid-item>
        <n-card title="系统状态" class="system-status-card">
          <n-space vertical size="medium">
            <div class="status-item">
              <span class="status-label">数据库连接</span>
              <n-tag :type="systemStatus.database ? 'success' : 'error'">
                {{ systemStatus.database ? '正常' : '异常' }}
              </n-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">缓存系统</span>
              <n-tag :type="systemStatus.cache ? 'success' : 'warning'">
                {{ systemStatus.cache ? '正常' : '警告' }}
              </n-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">文件存储</span>
              <n-tag :type="systemStatus.storage ? 'success' : 'error'">
                {{ systemStatus.storage ? '正常' : '异常' }}
              </n-tag>
            </div>
            
            <div class="status-item">
              <span class="status-label">搜索引擎</span>
              <n-tag :type="systemStatus.search ? 'success' : 'warning'">
                {{ systemStatus.search ? '正常' : '离线' }}
              </n-tag>
            </div>
          </n-space>
        </n-card>
      </n-grid-item>

      <!-- 热门搜索 -->
      <n-grid-item>
        <n-card title="热门搜索" class="popular-search-card">
          <n-list>
            <n-list-item
              v-for="(keyword, index) in popularKeywords"
              :key="keyword.word"
              class="search-item"
              @click="searchKeyword(keyword.word)"
            >
              <template #prefix>
                <n-tag :type="index < 3 ? 'warning' : 'default'" round>
                  {{ index + 1 }}
                </n-tag>
              </template>
              <n-thing>
                <template #header>
                  <span class="keyword">{{ keyword.word }}</span>
                </template>
                <template #description>
                  <span class="search-count">{{ keyword.count }} 次搜索</span>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>
        </n-card>
      </n-grid-item>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NGrid,
  NGridItem,
  NCard,
  NIcon,
  NList,
  NListItem,
  NThing,
  NTag,
  NButton,
  NSpace,
  useMessage
} from 'naive-ui'
import {
  FileTextOutlined,
  DesktopOutlined,
  UserOutlined,
  EyeOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlusOutlined,
  SearchOutlined
} from '@vicons/antd'
import { apiService } from '@/services'

const router = useRouter()
const message = useMessage()

// 响应式数据
const loading = ref(false)
const stats = ref({
  totalDocuments: 0,
  totalAssets: 0,
  activeUsers: 0,
  todayViews: 0,
  documentTrend: 5.2,
  assetTrend: 3.1,
  userTrend: -1.2,
  viewTrend: 12.5
})

const recentDocuments = ref([])
const recentAssets = ref([])
const systemStatus = ref({
  database: true,
  cache: true,
  storage: true,
  search: false
})
const popularKeywords = ref([])

// 方法
const loadDashboardData = async () => {
  loading.value = true
  try {
    // 加载统计数据
    const analyticsData = await apiService.get('/analytics/stats')
    stats.value = {
      ...stats.value,
      totalDocuments: analyticsData.totalDocuments || 0,
      totalAssets: analyticsData.totalAssets || 0,
      activeUsers: analyticsData.activeUsers || 0,
      todayViews: analyticsData.documentViews + analyticsData.assetViews || 0
    }

    // 加载最近文档
    const documents = await apiService.get('/documents?limit=5')
    recentDocuments.value = documents.slice(0, 5)

    // 加载最近资产
    const assets = await apiService.getUnified('/unified-assets?limit=5')
    recentAssets.value = assets.slice(0, 5)

    // 加载热门搜索关键词
    if (analyticsData.searchKeywords) {
      popularKeywords.value = analyticsData.searchKeywords.slice(0, 8)
    }

  } catch (error) {
    console.error('加载仪表板数据失败:', error)
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

const viewDocument = (id: number) => {
  router.push(`/documents/${id}`)
}

const viewAsset = (id: number) => {
  router.push(`/assets/${id}`)
}

const searchKeyword = (keyword: string) => {
  router.push({
    name: 'search',
    query: { q: keyword }
  })
}

const getAssetStatusColor = (status: string) => {
  const colors = {
    'active': '#52c41a',
    'inactive': '#faad14',
    'maintenance': '#1890ff',
    'retired': '#ff4d4f'
  }
  return colors[status] || '#d9d9d9'
}

const getAssetStatusType = (status: string) => {
  const types = {
    'active': 'success',
    'inactive': 'warning',
    'maintenance': 'info',
    'retired': 'error'
  }
  return types[status] || 'default'
}

const getAssetStatusText = (status: string) => {
  const texts = {
    'active': '在用',
    'inactive': '停用',
    'maintenance': '维护中',
    'retired': '已退役'
  }
  return texts[status] || '未知'
}

const formatTime = (time: string) => {
  return new Date(time).toLocaleDateString()
}

// 生命周期
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard {
  height: 100%;
  overflow-y: auto;
}

.stats-grid {
  margin-bottom: 24px;
}

.stat-card {
  height: 120px;
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

.stat-number {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.content-grid {
  margin-bottom: 24px;
}

.quick-actions-card,
.recent-docs-card,
.recent-assets-card {
  height: 300px;
}

.recent-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.recent-item:hover {
  background-color: #f5f5f5;
}

.doc-title,
.asset-name {
  font-weight: 500;
  color: #333;
}

.doc-time {
  font-size: 12px;
  color: #999;
}

.asset-ip {
  margin-left: 8px;
  font-size: 12px;
  color: #666;
}

.charts-grid {
  margin-bottom: 24px;
}

.system-status-card,
.popular-search-card {
  height: 280px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.status-label {
  font-weight: 500;
}

.search-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.search-item:hover {
  background-color: #f5f5f5;
}

.keyword {
  font-weight: 500;
  color: #333;
}

.search-count {
  font-size: 12px;
  color: #999;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .content-grid,
  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>