<template>
  <PageLayout title="润扬大桥运维数据分析">
    <template #header-actions>
      <div class="smart-highway-badge">智慧高速</div>
      <div class="craftsman-badge">匠心运维</div>
      <n-button @click="refreshData" type="info" :loading="loading" class="runyang-button-secondary">
        <template #icon>
          <n-icon :component="RefreshOutline" />
        </template>
        刷新数据
      </n-button>
      <n-button @click="exportReport" type="primary" class="runyang-button-primary">
        <template #icon>
          <n-icon :component="DownloadOutline" />
        </template>
        导出报告
      </n-button>
      <n-button @click="clearStats" type="error" :loading="clearingStats" v-if="currentUser?.is_superuser">
        <template #icon>
          <n-icon :component="TrashOutline" />
        </template>
        清空统计
      </n-button>
    </template>
            <!-- 核心统计卡片 - 智慧高速风格 -->
            <n-grid cols="1 s:2 m:4" responsive="screen" :x-gap="16" :y-gap="16" style="margin-bottom: 24px;">
              <n-grid-item>
                <div class="runyang-statistic craftsman-pattern">
                  <div class="number">{{ loading ? '-' : statistics.totalDocuments }}</div>
                  <div class="label">
                    <n-icon :component="DocumentOutline" size="16" style="margin-right: 4px;" />
                    文档总数
                  </div>
                </div>
              </n-grid-item>
              <n-grid-item>
                <div class="runyang-statistic craftsman-pattern">
                  <div class="number">{{ loading ? '-' : statistics.totalAssets }}</div>
                  <div class="label">
                    <n-icon :component="HardwareChipOutline" size="16" style="margin-right: 4px;" />
                    设备资产
                  </div>
                </div>
              </n-grid-item>
              <n-grid-item>
                <div class="runyang-statistic craftsman-pattern">
                  <div class="number">{{ loading ? '-' : statistics.documentViews }}</div>
                  <div class="label">
                    <n-icon :component="EyeOutline" size="16" style="margin-right: 4px;" />
                    文档访问
                  </div>
                </div>
              </n-grid-item>
              <n-grid-item>
                <div class="runyang-statistic craftsman-pattern runyang-pulse">
                  <div class="number">{{ loading ? '-' : statistics.activeUsers }}</div>
                  <div class="label">
                    <n-icon :component="PersonOutline" size="16" style="margin-right: 4px;" />
                    活跃用户
                  </div>
                </div>
              </n-grid-item>
            </n-grid>

            <!-- 用户活动热度统计 -->
            <n-card class="runyang-card runyang-decoration" :loading="loading" style="margin-bottom: 24px;">
              <template #header>
                <n-space align="center">
                  <n-icon :component="PersonOutline" size="20" style="color: var(--runyang-primary);" />
                  <span style="color: var(--runyang-primary); font-weight: 600;">用户活动热度统计</span>
                  <div class="craftsman-badge">工匠精神</div>
                </n-space>
              </template>
              <n-collapse>
                <n-collapse-item v-for="(user, index) in userActivityStats" :key="user.userId" :name="user.userId.toString()">
                  <template #header>
                    <n-space align="center">
                      <n-tag :type="index < 3 ? 'warning' : 'default'" size="small">
                        第{{ index + 1 }}名
                      </n-tag>
                      <n-text strong>{{ user.username }}</n-text>
                      <n-tag type="info" size="small">文档{{ user.documentViews }}次</n-tag>
                      <n-tag type="success" size="small">资产{{ user.assetViews }}次</n-tag>
                    </n-space>
                  </template>
                  
                  <n-grid cols="1 s:1 m:2" responsive="screen" :x-gap="16" :y-gap="16">
                    <!-- 文档访问详情 -->
                    <n-grid-item>
                      <n-card size="small" title="文档访问详情">
                        <n-list v-if="user.documentAccess && user.documentAccess.length > 0">
                          <n-list-item v-for="doc in user.documentAccess" :key="doc.documentId">
                            <n-space justify="space-between" align="center">
                              <div>
                                <n-text>{{ doc.documentTitle }}</n-text>
                                <n-text depth="3" style="font-size: 12px; margin-left: 8px;">
                                  最后访问: {{ formatDate(doc.lastAccess) }}
                                </n-text>
                              </div>
                              <n-tag type="info" size="small">{{ doc.accessCount }}次</n-tag>
                            </n-space>
                          </n-list-item>
                        </n-list>
                        <n-empty v-else description="暂无文档访问记录" size="small" />
                      </n-card>
                    </n-grid-item>
                    
                    <!-- 资产查看详情 -->
                    <n-grid-item>
                      <n-card size="small" title="资产查看详情">
                        <n-list v-if="user.assetAccess && user.assetAccess.length > 0">
                          <n-list-item v-for="asset in user.assetAccess" :key="asset.assetId">
                            <n-space justify="space-between" align="center">
                              <div>
                                <n-text>{{ asset.assetName }}</n-text>
                                <n-text depth="3" style="font-size: 12px; margin-left: 8px;">
                                  最后查看: {{ formatDate(asset.lastAccess) }}
                                </n-text>
                              </div>
                              <n-tag type="success" size="small">{{ asset.accessCount }}次</n-tag>
                            </n-space>
                          </n-list-item>
                        </n-list>
                        <n-empty v-else description="暂无资产查看记录" size="small" />
                      </n-card>
                    </n-grid-item>
                  </n-grid>
                </n-collapse-item>
              </n-collapse>
            </n-card>
            
            <!-- 搜索关键词排行榜 -->
            <n-card class="runyang-card runyang-decoration" :loading="loading" style="margin-bottom: 24px;">
              <template #header>
                <n-space align="center">
                  <n-icon :component="SearchOutline" size="20" style="color: var(--runyang-primary);" />
                  <span style="color: var(--runyang-primary); font-weight: 600;">搜索关键词排行榜</span>
                  <div class="smart-highway-badge">数据洞察</div>
                </n-space>
              </template>
              <n-table :bordered="false" :single-line="false" class="runyang-table">
                <thead>
                  <tr>
                    <th>排名</th>
                    <th>关键词</th>
                    <th>搜索次数</th>
                    <th>热度</th>
                    <th>最近搜索</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(keyword, index) in searchKeywords" :key="keyword.word">
                    <td>
                      <n-tag :type="index < 3 ? 'warning' : 'default'" size="small">
                        {{ index + 1 }}
                      </n-tag>
                    </td>
                    <td>
                      <n-text strong>{{ keyword.word }}</n-text>
                    </td>
                    <td>
                      <n-tag type="info" size="small">{{ keyword.count }}次</n-tag>
                    </td>
                    <td>
                      <n-progress
                        type="line"
                        :percentage="Math.min(100, (keyword.count / searchKeywords[0].count) * 100)"
                        :height="16"
                        :border-radius="8"
                        status="success"
                      />
                    </td>
                    <td>{{ formatDate(keyword.lastSearch) }}</td>
                  </tr>
                </tbody>
              </n-table>
            </n-card>
            
            <!-- AI分析建议 -->
            <n-card class="runyang-card runyang-decoration" :loading="aiAnalysisLoading">
              <template #header>
                <n-space align="center">
                  <n-icon :component="SearchOutline" size="20" style="color: var(--runyang-primary);" />
                  <span style="color: var(--runyang-primary); font-weight: 600;">AI智能分析建议</span>
                  <div class="smart-highway-badge">智慧分析</div>
                </n-space>
              </template>
              <template #header-extra>
                <n-button @click="generateAIAnalysis" type="primary" size="small" :loading="aiAnalysisLoading" class="runyang-button-primary">
                  <template #icon>
                    <n-icon :component="SearchOutline" />
                  </template>
                  生成分析
                </n-button>
              </template>
              <div v-if="aiAnalysis">
                <div v-if="aiAnalysis.generated_at" style="margin-bottom: 16px;">
                  <n-text depth="2" style="font-size: 12px;">
                    分析时间: {{ formatDate(aiAnalysis.generated_at) }}
                    <span v-if="aiAnalysis.suggestions">
                      | 共生成{{ aiAnalysis.suggestions.length }}条建议
                    </span>
                  </n-text>
                </div>
                <div v-for="(suggestion, index) in aiAnalysis.suggestions" :key="index" style="margin-bottom: 16px;">
                  <n-card size="small">
                    <template #header>
                      <n-space align="center">
                        <span>{{ suggestion.title }}</span>
                        <n-tag 
                          :type="suggestion.priority === 'high' ? 'error' : suggestion.priority === 'medium' ? 'warning' : 'info'" 
                          size="small"
                        >
                          {{ suggestion.priority === 'high' ? '高优先级' : suggestion.priority === 'medium' ? '中优先级' : '低优先级' }}
                        </n-tag>
                        <n-tag 
                          v-if="suggestion.type" 
                          type="info" 
                          size="small"
                        >
                          {{ getTypeLabel(suggestion.type) }}
                        </n-tag>
                      </n-space>
                    </template>
                    <p style="margin-bottom: 12px;">{{ suggestion.description }}</p>
                    <div v-if="suggestion.actions && suggestion.actions.length > 0">
                      <n-text depth="2" style="font-weight: 600;">建议措施：</n-text>
                      <ul style="margin: 8px 0; padding-left: 20px;">
                        <li v-for="(action, actionIndex) in suggestion.actions" :key="actionIndex" style="margin-bottom: 4px;">
                          {{ action }}
                        </li>
                      </ul>
                    </div>
                    <div v-if="suggestion.metrics" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f0f0;">
                      <n-text depth="3" style="font-size: 12px;">
                        相关数据: 
                        <span v-for="(value, key) in suggestion.metrics" :key="key" style="margin-right: 12px;">
                          {{ getMetricLabel(key) }}: {{ value }}
                        </span>
                      </n-text>
                    </div>
                  </n-card>
                </div>
              </div>
              <n-empty v-else description="点击生成分析按钮获取AI运维建议" />
            </n-card>
  </PageLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NSpace,
  NH2,
  NButton,
  NIcon,
  NGrid,
  NGridItem,
  NCard,
  NStatistic,
  NTable,
  NTag,
  NText,
  NEmpty,
  NProgress,
  NCollapse,
  NCollapseItem,
  NList,
  NListItem,
  useMessage
} from 'naive-ui'
import {
  DocumentOutline,
  SearchOutline,
  PersonOutline,
  DownloadOutline,
  RefreshOutline,
  HardwareChipOutline,
  EyeOutline,
  TrashOutline
} from '@vicons/ionicons5'
import PageLayout from '../components/PageLayout.vue'
import { documentService } from '@/services/document'
import { assetService } from '@/services/asset'
import { analyticsService } from '@/services/analytics'
import { authService } from '@/services/auth'
import apiService from '@/services/api'
import { useDialog } from 'naive-ui'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const aiAnalysisLoading = ref(false)
const clearingStats = ref(false)

// 当前用户
const currentUser = ref(null)

// 核心统计数据
const statistics = ref({
  totalDocuments: 0,
  totalAssets: 0,
  documentViews: 0,
  assetViews: 0,
  activeUsers: 0
})

// 用户活动统计数据 - 从数据库动态加载
const userActivityStats = ref([])

// 搜索关键词排行数据 - 从数据库动态加载
const searchKeywords = ref([])

// AI分析结果
const aiAnalysis = ref(null)

// 加载AI分析
const loadAiAnalysis = async () => {
  aiAnalysisLoading.value = true
  try {
    const analysisData = await analyticsService.getAIAnalysis()
    
    // 转换后端数据格式为前端需要的格式
    aiAnalysis.value = {
      generated_at: analysisData.analysis_time,
      suggestions: [
        // 合并insights和recommendations为suggestions
        ...analysisData.insights.map(insight => ({
          title: insight.title,
          description: insight.content,
          priority: insight.priority === 'high' ? 'high' : insight.priority === 'warning' ? 'medium' : 'low',
          type: getTypeMapping(insight.type),
          actions: [],
          metrics: {}
        })),
        ...analysisData.recommendations.map(rec => ({
          title: rec.title,
          description: rec.content,
          priority: 'medium',
          type: getTypeMapping(rec.type),
          actions: [rec.action || '执行相关操作'],
          metrics: analysisData.performance_metrics || {}
        }))
      ]
    }
  } catch (error) {
    console.error('AI分析加载失败:', error)
    // 提供默认分析结果
    aiAnalysis.value = {
      generated_at: new Date().toISOString(),
      suggestions: [
        {
          title: "分析服务暂时不可用",
          description: "无法连接到AI分析服务，请稍后重试。",
          priority: "medium",
          type: "system",
          actions: ["检查网络连接", "稍后重试"],
          metrics: {}
        },
        {
          title: "系统维护建议",
          description: "建议定期检查系统组件连接状态。",
          priority: "low",
          type: "system",
          actions: ["检查系统连接", "进行系统维护"],
          metrics: {}
        }
      ]
    }
  } finally {
    aiAnalysisLoading.value = false
  }
}

// 类型映射函数
const getTypeMapping = (backendType) => {
  const typeMap = {
    'document_access': 'documentation',
    'asset_monitoring': 'asset_monitoring',
    'security_focus': 'security_management',
    'system_health': 'system',
    'connection_issue': 'system',
    'optimization': 'asset_optimization',
    'maintenance': 'system',
    'documentation': 'documentation',
    'monitoring': 'asset_monitoring',
    'training': 'user_engagement',
    'security_enhancement': 'security_management',
    'content_optimization': 'documentation',
    'high_maintenance_ratio': 'asset_monitoring'
  }
  return typeMap[backendType] || 'system'
}

// 加载所有数据
const loadAnalyticsData = async () => {
  loading.value = true
  try {
    // 使用新的analytics服务获取真实数据
    const analyticsData = await analyticsService.getStats()
    console.log('从analytics服务获取的数据:', analyticsData)
    
    // 更新统计数据
    statistics.value = {
      totalDocuments: analyticsData.total_documents || 0,
      totalAssets: analyticsData.total_assets || 0,
      documentViews: analyticsData.total_document_views || 0,
      assetViews: analyticsData.total_asset_views || 0,
      activeUsers: analyticsData.total_users || 0
    }
    
    // 设置用户活动统计数据
    if (analyticsData.userActivityStats && analyticsData.userActivityStats.length > 0) {
      userActivityStats.value = analyticsData.userActivityStats.map((user, index) => ({
        ...user,
        assetViews: user.assetViews || 0,
        totalActivity: Math.min(100, (user.documentViews + (user.assetViews || 0)) / 5),
        documentAccess: user.documentAccess || [],
        assetAccess: user.assetAccess || []
      }))
    } else {
      // 如果没有真实数据，使用默认数据
      userActivityStats.value = [
        {
          userId: 1,
          username: "运维管理员",
          department: "技术部",
          documentViews: 0,
          searches: 0,
          assetViews: 0,
          lastActivity: new Date().toISOString(),
          totalActivity: 0,
          documentAccess: [],
          assetAccess: []
        }
      ]
    }
    
    // 设置搜索关键词排行榜数据
    if (analyticsData.searchKeywords && analyticsData.searchKeywords.length > 0) {
      searchKeywords.value = analyticsData.searchKeywords.map(item => ({
        word: item.keyword,
        count: item.count,
        lastSearch: item.lastSearch || new Date().toISOString()
      }))
    } else {
      // 如果没有真实数据，使用默认数据
      searchKeywords.value = [
        { word: '暂无搜索数据', count: 0, lastSearch: new Date().toISOString() }
      ]
    }
    
    
    // 自动加载AI分析
    await loadAiAnalysis()
    
  } catch (error) {
    console.error('加载分析数据失败:', error)
    message.error('加载分析数据失败，请检查网络连接或稍后重试')
    
    // 使用基础数据作为后备
    statistics.value = {
      totalDocuments: 0,
      totalAssets: 0,
      documentViews: 0,
      assetViews: 0,
      activeUsers: 0
    }
    
    userActivityStats.value = []
    searchKeywords.value = []
  } finally {
    loading.value = false
  }
}

// 删除了示例数据相关的更新函数
// 待实现：从真实的访问日志表加载用户活动数据

// AI分析功能
const generateAIAnalysis = async () => {
  await loadAiAnalysis()
  if (aiAnalysis.value && aiAnalysis.value.suggestions) {
    message.success(`AI分析完成，生成了${aiAnalysis.value.suggestions.length}条建议`)
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 获取建议类型标签
const getTypeLabel = (type) => {
  const typeLabels = {
    'network_management': '网络管理',
    'security_management': '安全管理',
    'documentation': '文档管理',
    'asset_monitoring': '资产监控',
    'asset_optimization': '资产优化',
    'user_engagement': '用户参与',
    'access_management': '权限管理',
    'security_awareness': '安全意识',
    'system': '系统'
  }
  return typeLabels[type] || type
}

// 获取指标标签
const getMetricLabel = (key) => {
  const metricLabels = {
    'ip_searches': 'IP搜索次数',
    'total_searches': '总搜索次数',
    'security_searches': '安全搜索次数',
    'tutorial_searches': '教程搜索次数',
    'asset_name': '资产名称',
    'view_count': '查看次数',
    'asset_type': '资产类型',
    'unused_assets': '未使用资产',
    'total_assets': '总资产数',
    'active_users': '活跃用户',
    'total_users': '总用户数',
    'admin_count': '管理员数量',
    'security_search_count': '安全搜索总数',
    'unique_security_terms': '安全搜索种类'
  }
  return metricLabels[key] || key
}

const refreshData = async () => {
  await loadAnalyticsData()
  message.success('数据已刷新')
}

const exportReport = () => {
  message.success('报告导出功能开发中...')
}

// 清空统计数据
const clearStats = () => {
  dialog.warning({
    title: '确认清空',
    content: '确定要清空所有用户活动统计数据吗？此操作不可撤销。',
    positiveText: '确定清空',
    negativeText: '取消',
    onPositiveClick: async () => {
      clearingStats.value = true
      try {
        const result = await apiService.post('/analytics/clear-stats')
        message.success('统计数据已清空')
        // 重新加载数据
        await loadAnalyticsData()
      } catch (error) {
        console.error('清空统计数据失败:', error)
        message.error(error.message || '清空统计数据失败')
      } finally {
        clearingStats.value = false
      }
    }
  })
}

// 加载当前用户信息
const loadCurrentUser = async () => {
  try {
    currentUser.value = await authService.getCurrentUser()
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

onMounted(async () => {
  await Promise.all([
    loadAnalyticsData(),
    loadCurrentUser()
  ])
})
</script>

<style scoped>
/* AnalyticsView specific styles */

/* 统计卡片样式 */
.runyang-statistic {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  background: linear-gradient(135deg, #FEFEFE 0%, #F8F9FA 100%);
  border: 2px solid #E8E8E8;
  border-radius: 12px;
  min-height: 120px;
  position: relative;
  transition: all 0.3s ease;
}

.runyang-statistic:hover {
  border-color: var(--runyang-primary);
  box-shadow: 0 4px 16px rgba(139, 69, 19, 0.15);
  transform: translateY(-2px);
}

.runyang-statistic .number {
  font-size: 32px;
  font-weight: 700;
  color: var(--runyang-primary);
  margin-bottom: 8px;
  text-align: center;
  line-height: 1;
  min-width: 80px;
}

.runyang-statistic .label {
  font-size: 14px;
  color: var(--runyang-secondary);
  font-weight: 500;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

/* 工匠精神装饰图案 */
.craftsman-pattern::before {
  content: '';
  position: absolute;
  top: 8px;
  right: 8px;
  width: 16px;
  height: 2px;
  background: linear-gradient(90deg, var(--runyang-primary) 0%, var(--runyang-accent) 100%);
  border-radius: 1px;
  opacity: 0.3;
}

.craftsman-pattern::after {
  content: '';
  position: absolute;
  top: 14px;
  right: 12px;
  width: 8px;
  height: 2px;
  background: linear-gradient(90deg, var(--runyang-accent) 0%, var(--runyang-primary) 100%);
  border-radius: 1px;
  opacity: 0.2;
}

/* 脉动效果 - 使用默认配色 */
.runyang-pulse {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 2px 8px rgba(32, 128, 240, 0.1);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 4px 16px rgba(32, 128, 240, 0.2);
  }
}

/* 卡片样式 */
.runyang-card {
  border: 2px solid #E8E8E8;
  border-radius: 12px;
  background: linear-gradient(135deg, #FEFEFE 0%, #F8F9FA 100%);
  transition: all 0.3s ease;
}

.runyang-card:hover {
  border-color: var(--runyang-primary);
  box-shadow: 0 4px 16px rgba(139, 69, 19, 0.15);
}

/* 装饰边框 - 使用默认配色 */
.runyang-decoration {
  position: relative;
}

.runyang-decoration::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, #2080f0 0%, #18a058 50%, #f0a020 100%);
  border-radius: 14px;
  z-index: -1;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.runyang-decoration:hover::before {
  opacity: 0.1;
}

/* 徽章样式 - 修复文字可见性 */
.smart-highway-badge, .craftsman-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: white !important;
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%) !important;
  box-shadow: 0 2px 4px rgba(24, 160, 88, 0.3) !important;
  position: relative;
  overflow: hidden;
  display: inline-block;
}

/* 徽章悬停效果 */
.smart-highway-badge:hover, .craftsman-badge:hover {
  background: linear-gradient(135deg, #36ad6a 0%, #0c7a43 100%) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(24, 160, 88, 0.4) !important;
  color: white !important;
}

.smart-highway-badge::before, .craftsman-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  transition: left 0.5s ease;
}

.smart-highway-badge:hover::before, .craftsman-badge:hover::before {
  left: 100%;
}

/* 按钮样式 - 修复导出报告和生成分析按钮可见性 */
.runyang-button-primary,
:deep(.runyang-button-primary) {
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%) !important;
  border: none !important;
  box-shadow: 0 2px 4px rgba(24, 160, 88, 0.3) !important;
  transition: all 0.3s ease !important;
  color: white !important;
}

.runyang-button-primary:hover,
:deep(.runyang-button-primary:hover) {
  background: linear-gradient(135deg, #36ad6a 0%, #0c7a43 100%) !important;
  box-shadow: 0 4px 8px rgba(24, 160, 88, 0.4) !important;
  transform: translateY(-1px) !important;
  color: white !important;
}

.runyang-button-primary:active,
:deep(.runyang-button-primary:active) {
  background: linear-gradient(135deg, #0c7a43 0%, #18a058 100%) !important;
  transform: translateY(0px) !important;
  color: white !important;
}

.runyang-button-primary .n-button__content,
.runyang-button-primary span,
:deep(.runyang-button-primary .n-button__content),
:deep(.runyang-button-primary span) {
  color: white !important;
}

/* 确保所有primary类型按钮的可见性 */
:deep(.n-button.n-button--primary-type) {
  background: linear-gradient(135deg, #18a058 0%, #36ad6a 100%) !important;
  border-color: #18a058 !important;
  color: white !important;
}

:deep(.n-button.n-button--primary-type:hover) {
  background: linear-gradient(135deg, #36ad6a 0%, #0c7a43 100%) !important;
  border-color: #36ad6a !important;
  color: white !important;
}

:deep(.n-button.n-button--primary-type .n-button__content),
:deep(.n-button.n-button--primary-type span) {
  color: white !important;
}

.runyang-button-secondary {
  background: linear-gradient(135deg, #2080f0 0%, #409eff 100%) !important;
  border: none !important;
  color: white !important;
  box-shadow: 0 2px 4px rgba(32, 128, 240, 0.3) !important;
  transition: all 0.3s ease !important;
}

.runyang-button-secondary:hover {
  background: linear-gradient(135deg, #409eff 0%, #1c6eeb 100%) !important;
  color: white !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(32, 128, 240, 0.4) !important;
}

.runyang-button-secondary:active {
  background: linear-gradient(135deg, #1c6eeb 0%, #2080f0 100%) !important;
  transform: translateY(0px) !important;
  color: white !important;
}

.runyang-button-secondary .n-button__content,
.runyang-button-secondary span {
  color: white !important;
}

.runyang-button-secondary:hover .n-button__content,
.runyang-button-secondary:hover span {
  color: white !important;
}

/* 表格样式 - 使用默认样式 */
.runyang-table {
  border-radius: 8px;
  overflow: hidden;
}

.runyang-table th {
  font-weight: 600 !important;
  /* 使用默认颜色和背景 */
}

.runyang-table td {
  /* 使用默认颜色和背景 */
}

.runyang-table tr:hover {
  /* 使用默认悬停效果 */
}

.runyang-table tr:hover td {
  /* 使用默认悬停效果 */
}

/* 表格内组件使用默认样式 */
.runyang-table .n-tag {
  /* 使用默认颜色 */
}

.runyang-table .n-text {
  /* 使用默认颜色 */
}

.runyang-table .n-progress {
  /* 使用默认样式 */
}

/* 用户活动统计样式 - 保持基本结构，使用默认颜色 */
.n-collapse-item {
  border: 1px solid #E8E8E8 !important;
  border-radius: 8px !important;
  margin-bottom: 8px !important;
  /* 使用默认背景 */
}

.n-collapse-item .n-collapse-item__header {
  /* 使用默认背景和颜色 */
  padding: 16px !important;
  border-radius: 8px 8px 0 0 !important;
}

.n-collapse-item .n-collapse-item__header .n-tag {
  font-weight: 600 !important;
  /* 使用默认颜色 */
}

.n-collapse-item .n-collapse-item__header .n-text {
  font-weight: 600 !important;
  /* 使用默认颜色 */
}

.n-collapse-item .n-collapse-item__content-wrapper {
  /* 使用默认背景 */
  border-radius: 0 0 8px 8px !important;
}

.n-collapse-item .n-collapse-item__content-inner {
  padding: 16px !important;
}

/* 列表样式 - 使用默认样式 */
.n-list {
  /* 使用默认背景 */
}

.n-list-item {
  padding: 12px 16px !important;
  border-bottom: 1px solid #F0F0F0 !important;
  /* 使用默认文字颜色 */
}

.n-list-item:hover {
  /* 使用默认悬停样式 */
}

.n-list-item .n-text {
  /* 使用默认文字颜色 */
}

.n-list-item .n-tag {
  /* 使用默认标签颜色 */
}

/* 卡片内容 - 使用默认样式 */
.n-card .n-card__content {
  /* 移除强制颜色设置，使用默认样式 */
}

.n-card .n-card__header {
  /* 移除强制颜色设置，使用默认样式 */
}

/* 进度条样式增强 */
.n-progress .n-progress-graph-line-rail {
  background: var(--runyang-light) !important;
}

.n-progress .n-progress-graph-line-fill {
  background: var(--runyang-primary) !important;
}

/* AI分析建议卡片样式 - 使用默认样式 */
.n-card.n-card--size-small {
  /* 使用默认样式 */
}

.n-card.n-card--size-small .n-card__header {
  /* 使用默认样式 */
}

.n-card.n-card--size-small .n-card__content {
  line-height: 1.6 !important;
}

.n-card.n-card--size-small p {
  margin: 0 0 12px 0 !important;
}

.n-card.n-card--size-small ul {
  /* 使用默认样式 */
}

.n-card.n-card--size-small li {
  /* 使用默认样式 */
}

/* 空状态样式 - 使用默认样式 */
.n-empty {
  /* 使用默认颜色 */
}

.n-empty .n-empty__description {
  /* 使用默认颜色 */
}

/* 响应式设计 */
@media (max-width: 768px) {
  .runyang-statistic {
    min-height: 100px;
    padding: 16px 12px;
  }
  
  .runyang-statistic .number {
    font-size: 24px;
  }
  
  .runyang-statistic .label {
    font-size: 12px;
  }
  
  .runyang-table {
    font-size: 12px;
  }
  
  .n-collapse-item .n-collapse-item__header {
    padding: 12px !important;
  }
}
</style>