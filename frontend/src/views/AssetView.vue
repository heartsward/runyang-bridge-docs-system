<template>
  <PageLayout title="设备资产管理">
    <template #header-actions>
      <n-input
        v-model:value="searchQuery"
        placeholder="搜索设备..."
        style="width: 300px"
        clearable
        @update:value="handleSearch"
      >
        <template #prefix>
          <n-icon :component="SearchOutline" />
        </template>
      </n-input>
      <n-button v-if="currentUser?.is_superuser" type="primary" @click="showCreateModal = true" style="background-color: #2563eb; border-color: #2563eb;">
        <template #icon>
          <n-icon :component="AddOutline" />
        </template>
        添加设备
      </n-button>
      <n-button v-if="currentUser?.is_superuser" @click="showExtractModal = true">
        <template #icon>
          <n-icon :component="DocumentTextOutline" />
        </template>
        从文件提取
      </n-button>
      <n-button v-if="currentUser?.is_superuser" type="error" @click="handleBulkDelete" :disabled="selectedAssets.length === 0">
        <template #icon>
          <n-icon :component="TrashOutline" />
        </template>
        批量删除 ({{ selectedAssets.length }})
      </n-button>
      <n-button v-if="currentUser?.is_superuser" type="success" @click="showExportModal = true" :disabled="selectedAssets.length === 0">
        <template #icon>
          <n-icon :component="DownloadOutline" />
        </template>
        导出资产 ({{ selectedAssets.length }})
      </n-button>
    </template>

    <!-- 统计卡片 -->
    <n-grid cols="1 s:2 m:4" responsive="screen" :x-gap="16" :y-gap="16" style="margin-bottom: 24px;">
      <n-grid-item>
        <n-card>
          <n-statistic label="总设备数" :value="realTimeStatistics.total_count">
            <template #prefix>
              <n-icon :component="HardwareChipOutline" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="在用设备" :value="realTimeStatistics.by_status?.active || 0" value-style="color: #18a058;">
            <template #prefix>
              <n-icon :component="CheckmarkCircleOutline" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="维护中" :value="realTimeStatistics.by_status?.maintenance || 0" value-style="color: #f0a020;">
            <template #prefix>
              <n-icon :component="ConstructOutline" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card>
          <n-statistic label="最近新增" :value="realTimeStatistics.recent_additions" value-style="color: #2080f0;">
            <template #prefix>
              <n-icon :component="TrendingUpOutline" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 筛选器和排序 -->
    <n-card style="margin-bottom: 16px;">
      <n-space vertical size="medium">
        <!-- 第一行：筛选器 -->
        <n-space>
          <n-select
            v-model:value="filters.asset_type"
            placeholder="设备类型"
            :options="assetTypeOptions"
            clearable
            style="width: 150px"
            @update:value="handleSearch"
          />
          <n-select
            v-model:value="filters.status"
            placeholder="状态"
            :options="assetStatusOptions"
            clearable
            style="width: 120px"
            @update:value="handleSearch"
          />
          <n-select
            v-model:value="filters.department"
            placeholder="部门"
            :options="departmentOptions"
            clearable
            style="width: 120px"
            @update:value="handleDepartmentFilter"
          />
          <n-select
            v-model:value="filters.network_location"
            placeholder="所处网络"
            :options="networkLocationOptions"
            clearable
            style="width: 120px"
            @update:value="handleSearch"
          />
        </n-space>
        
        <!-- 第二行：排序选项 -->
        <n-space align="center">
          <n-text depth="3" style="white-space: nowrap;">排序方式:</n-text>
          <n-select
            v-model:value="sortConfig.sortBy"
            placeholder="排序字段"
            :options="sortByOptions"
            style="width: 150px"
            @update:value="handleSortChange"
          />
          <n-select
            v-model:value="sortConfig.sortOrder"
            :options="sortOrderOptions"
            style="width: 100px"
            @update:value="handleSortChange"
          />
        </n-space>
      </n-space>
    </n-card>

    <!-- 设备列表 -->
    <div v-if="loading" style="text-align: center; padding: 40px;">
      <n-spin size="large" />
      <div style="margin-top: 16px;">
        <n-text depth="3">加载中...</n-text>
      </div>
    </div>

    <div v-else-if="assets.length === 0" style="text-align: center; padding: 40px;">
      <n-empty description="暂无设备资产">
        <template #extra>
          <n-space>
            <n-button type="primary" @click="showCreateModal = true" style="background-color: #2563eb; border-color: #2563eb; color: white;">
              <template #icon>
                <n-icon :component="AddOutline" />
              </template>
              添加第一个设备
            </n-button>
            <n-button @click="showExtractModal = true">
              <template #icon>
                <n-icon :component="DocumentTextOutline" />
              </template>
              从文档提取
            </n-button>
          </n-space>
        </template>
      </n-empty>
    </div>

    <div v-else>
      <n-data-table
        :columns="columns"
        :data="assets"
        :pagination="pagination"
        :loading="loading"
        :row-key="(row: Asset) => row.id"
        :checked-row-keys="selectedAssets.map(asset => asset.id)"
        @update:checked-row-keys="handleSelectionChange"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </div>
  </PageLayout>

    <!-- 创建/编辑设备模态框 -->
    <n-modal v-model:show="showCreateModal" preset="card" style="width: 800px" :title="editingAsset ? '编辑设备' : '添加设备'">
      <n-form ref="formRef" :model="assetForm" :rules="rules" label-placement="left" label-width="120px">
        <n-grid cols="1 s:2" responsive="screen" :x-gap="16">
          <n-grid-item>
            <n-form-item label="设备名称" path="name">
              <n-input v-model:value="assetForm.name" placeholder="请输入设备名称" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="设备类型" path="asset_type">
              <n-select v-model:value="assetForm.asset_type" :options="assetTypeOptions" placeholder="请选择设备类型" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="IP地址" path="ip_address">
              <n-input v-model:value="assetForm.ip_address" placeholder="请输入IP地址" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="主机名" path="hostname">
              <n-input v-model:value="assetForm.hostname" placeholder="请输入主机名" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="用户名" path="username">
              <n-input v-model:value="assetForm.username" placeholder="请输入用户名" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="密码" path="password">
              <n-input v-model:value="assetForm.password" type="password" placeholder="请输入密码" show-password-on="click" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="设备型号" path="device_model">
              <n-input v-model:value="assetForm.device_model" placeholder="请输入设备型号" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="所处网络" path="network_location">
              <n-select v-model:value="assetForm.network_location" :options="networkLocationOptions" placeholder="请选择所处网络" />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="部门" path="department">
              <n-select
                v-model:value="assetForm.department"
                :options="departmentOptions"
                placeholder="请选择部门或输入新部门"
                filterable
                tag
                clearable
              />
            </n-form-item>
          </n-grid-item>
          <n-grid-item>
            <n-form-item label="状态" path="status">
              <n-select v-model:value="assetForm.status" :options="assetStatusOptions" placeholder="请选择状态" />
            </n-form-item>
          </n-grid-item>
        </n-grid>
        <n-form-item label="备注" path="notes">
          <n-input v-model:value="assetForm.notes" type="textarea" placeholder="请输入备注" :rows="3" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ editingAsset ? '更新' : '创建' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 从文件提取设备模态框 -->
    <n-modal v-model:show="showExtractModal" preset="card" style="width: 600px" title="从文件提取设备">
      <n-form ref="extractFormRef" :model="extractForm">
        <n-form-item label="选择文件">
          <n-upload
            ref="uploadRef"
            v-model:file-list="fileList"
            :max="1"
            :show-file-list="true"
            accept=".txt,.csv,.xlsx,.xls,.json,.md"
            @before-upload="handleBeforeUpload"
          >
            <n-upload-dragger>
              <div style="margin-bottom: 12px">
                <n-icon size="48" :depth="3">
                  <DocumentTextOutline />
                </n-icon>
              </div>
              <n-text style="font-size: 16px">点击或者拖动文件到该区域来上传</n-text>
              <n-p depth="3" style="margin: 8px 0 0 0">
                支持格式：TXT、CSV、Excel、JSON、Markdown
                <br>
                单个文件大小不超过10MB
              </n-p>
            </n-upload-dragger>
          </n-upload>
        </n-form-item>
        <n-form-item label="自动合并">
          <n-switch v-model:value="extractForm.auto_merge" />
          <n-text depth="3" style="margin-left: 8px;">自动合并相似的设备信息</n-text>
        </n-form-item>
        <n-form-item label="合并阈值" v-if="extractForm.auto_merge">
          <n-slider v-model:value="extractForm.merge_threshold" :min="60" :max="100" :step="5" />
          <n-text depth="3">{{ extractForm.merge_threshold }}%</n-text>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showExtractModal = false">取消</n-button>
          <n-button type="primary" @click="handleExtract" :loading="extracting" :disabled="fileList.length === 0">
            开始提取
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 提取结果模态框 -->
    <n-modal v-model:show="showExtractResult" preset="card" style="width: 800px" title="提取结果确认">
      <div v-if="extractResult">
        <n-alert type="info" style="margin-bottom: 16px;">
          <template #header>文件提取完成</template>
          请确认是否要将以下提取的设备信息保存到数据库中
        </n-alert>
        
        <n-alert v-if="extractResult.errors && extractResult.errors.length > 0" type="warning" style="margin-bottom: 16px;">
          <template #header>提取过程中遇到问题</template>
          <ul>
            <li v-for="error in extractResult.errors" :key="error">{{ error }}</li>
          </ul>
        </n-alert>
        
        <n-descriptions bordered :column="2" style="margin-bottom: 16px;">
          <n-descriptions-item label="提取数量">{{ extractResult.extracted_count || extractResult.assets.length }}</n-descriptions-item>
          <n-descriptions-item label="待确认创建">{{ extractResult.assets.length }}</n-descriptions-item>
          <n-descriptions-item label="冲突数量">{{ extractResult.assets.filter(asset => asset.conflicts && asset.conflicts.length > 0).length }}</n-descriptions-item>
        </n-descriptions>

        <n-h4>待创建的设备列表</n-h4>
        <n-data-table :columns="extractConfirmColumns" :data="extractResult.assets" max-height="400" />
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showExtractResult = false">取消</n-button>
          <n-button type="primary" @click="confirmExtractedAssets" :loading="confirming">
            确认创建 {{ extractResult?.assets.length || 0 }} 个设备
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 设备详情查看模态框 -->
    <n-modal v-model:show="showViewModal" preset="card" style="width: 700px" title="设备详情">
      <div v-if="viewingAsset">
        <n-space vertical size="large">
          <div style="text-align: center; margin-bottom: 20px;">
            <n-h3 style="margin: 0;">{{ viewingAsset.name }}</n-h3>
            <n-text depth="3">{{ viewingAsset.ip_address || '无IP地址' }}</n-text>
          </div>
          
          <n-tabs type="line" animated>
            <!-- 基本信息标签页 -->
            <n-tab-pane name="basic" tab="基本信息">
              <n-descriptions bordered :column="2">
                <n-descriptions-item label="设备名称">
                  {{ viewingAsset.name }}
                </n-descriptions-item>
                <n-descriptions-item label="设备类型">
                  {{ getAssetTypeLabel(viewingAsset.asset_type) }}
                </n-descriptions-item>
                <n-descriptions-item label="IP地址">
                  {{ viewingAsset.ip_address || '未设置' }}
                </n-descriptions-item>
                <n-descriptions-item label="主机名">
                  {{ viewingAsset.hostname || '未设置' }}
                </n-descriptions-item>
                <n-descriptions-item label="设备型号">
                  {{ viewingAsset.device_model || '未设置' }}
                </n-descriptions-item>
                <n-descriptions-item label="所处网络">
                  {{ getNetworkLocationLabel(viewingAsset.network_location) }}
                </n-descriptions-item>
                <n-descriptions-item label="所属部门">
                  {{ viewingAsset.department || '未设置' }}
                </n-descriptions-item>
                <n-descriptions-item label="状态">
                  <n-tag :type="getStatusType(viewingAsset.status)">
                    {{ getAssetStatusLabel(viewingAsset.status) }}
                  </n-tag>
                </n-descriptions-item>
                <n-descriptions-item label="备注信息" span="2">
                  <div v-if="viewingAsset.notes && viewingAsset.notes.trim()">
                    {{ viewingAsset.notes }}
                  </div>
                  <n-text depth="3" v-else>未设置</n-text>
                </n-descriptions-item>
                <n-descriptions-item label="创建时间" span="2">
                  {{ formatDateTime(viewingAsset.created_at) }}
                </n-descriptions-item>
                <n-descriptions-item label="更新时间" span="2" v-if="viewingAsset.updated_at">
                  {{ formatDateTime(viewingAsset.updated_at) }}
                </n-descriptions-item>
              </n-descriptions>
            </n-tab-pane>

            <!-- 登录凭据标签页 -->
            <n-tab-pane name="credentials" tab="登录凭据">
              <n-form label-placement="left" label-width="80px">
                <n-form-item label="用户名">
                  <n-text code v-if="viewingAsset.username">{{ viewingAsset.username }}</n-text>
                  <n-text depth="3" v-else>未设置</n-text>
                </n-form-item>
                <n-form-item label="密码">
                  <n-input
                    v-if="viewingAsset.password"
                    :value="viewingAsset.password"
                    type="password"
                    readonly
                    show-password-on="click"
                    style="max-width: 250px;"
                    autocomplete="off"
                  />
                  <n-text depth="3" v-else>未设置</n-text>
                </n-form-item>
                <n-form-item label="SSH密钥" v-if="viewingAsset.ssh_key">
                  <n-input
                    :value="viewingAsset.ssh_key"
                    type="textarea"
                    readonly
                    :rows="4"
                    style="max-width: 400px;"
                  />
                </n-form-item>
              </n-form>
            </n-tab-pane>

          </n-tabs>
        </n-space>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showViewModal = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 资产导出模态框 -->
    <n-modal v-model:show="showExportModal" preset="card" style="width: 600px" title="导出资产数据">
      <div>
        <n-alert type="info" style="margin-bottom: 16px;">
          已选择 {{ selectedAssets.length }} 个资产进行导出
        </n-alert>
        
        <n-form label-placement="left" label-width="120px">
          <n-form-item label="导出格式">
            <n-radio-group v-model:value="exportFormat">
              <n-space>
                <n-radio value="excel">Excel (.xlsx)</n-radio>
                <n-radio value="csv">CSV (.csv)</n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
          
          <n-form-item label="包含字段">
            <div style="margin-bottom: 8px;">
              <n-button size="small" @click="selectAllFields">全选</n-button>
              <n-button size="small" @click="clearAllFields" style="margin-left: 8px;">清空</n-button>
              <n-button size="small" @click="selectBasicFields" style="margin-left: 8px;">基本字段</n-button>
            </div>
            <n-checkbox-group v-model:value="exportFields">
              <n-grid cols="2" responsive="screen" :x-gap="8" :y-gap="4">
                <n-grid-item>
                  <n-checkbox value="name">设备名称</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="asset_type">设备类型</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="ip_address">IP地址</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="hostname">主机名</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="username">用户名</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="password">密码</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="device_model">设备型号</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="network_location">所处网络</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="department">所属部门</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="status">状态</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="notes">备注</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="created_at">创建时间</n-checkbox>
                </n-grid-item>
                <n-grid-item>
                  <n-checkbox value="updated_at">更新时间</n-checkbox>
                </n-grid-item>
              </n-grid>
            </n-checkbox-group>
          </n-form-item>
        </n-form>
        
        <div style="margin-top: 16px;">
          <n-text depth="3">
            将导出 {{ selectedAssets.length }} 个资产的数据，包含选中的字段信息。
          </n-text>
        </div>
      </div>
      
      <template #footer>
        <n-space justify="end">
          <n-button @click="showExportModal = false">取消</n-button>
          <n-button type="primary" @click="handleExport" :loading="exporting">
            <template #icon>
              <n-icon :component="DownloadOutline" />
            </template>
            导出
          </n-button>
        </n-space>
      </template>
    </n-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, h } from 'vue'
import {
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NSpace,
  NH2,
  NH4,
  NInput,
  NButton,
  NIcon,
  NGrid,
  NGridItem,
  NCard,
  NStatistic,
  NSelect,
  NDataTable,
  NEmpty,
  NSpin,
  NModal,
  NForm,
  NFormItem,
  NSwitch,
  NSlider,
  NAlert,
  NDescriptions,
  NDescriptionsItem,
  NTag,
  NText,
  NRadioGroup,
  NRadio,
  NCheckboxGroup,
  NCheckbox,
  NUpload,
  NUploadDragger,
  NP,
  useMessage,
  useDialog,
  type DataTableColumns,
  type FormInst,
  type UploadFileInfo
} from 'naive-ui'
import {
  SearchOutline,
  AddOutline,
  DocumentTextOutline,
  HardwareChipOutline,
  CheckmarkCircleOutline,
  ConstructOutline,
  TrendingUpOutline,
  CreateOutline,
  TrashOutline,
  EyeOutline,
  DownloadOutline,
  CopyOutline
} from '@vicons/ionicons5'
import PageLayout from '../components/PageLayout.vue'
import { assetService, documentService, authService } from '@/services'
import apiService from '@/services/api'
import type { Asset, AssetCreate, AssetExtractRequest, AssetExtractResult, AssetStatistics } from '@/types/asset'
import { AssetType, AssetStatus } from '@/types/asset'
import type { Document, User } from '@/types/api'
import { debounce } from '@/utils'

const message = useMessage()
const dialog = useDialog()
const formRef = ref<FormInst | null>(null)
const extractFormRef = ref<FormInst | null>(null)

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const extracting = ref(false)
const confirming = ref(false)
const assets = ref<Asset[]>([])
const currentUser = ref<User | null>(null)
const statistics = ref<AssetStatistics>({
  total_count: 0,
  by_type: {},
  by_status: {},
  by_environment: {},
  by_department: {},
  recent_additions: 0,
  pending_maintenance: 0
})

// 实时计算统计数据，确保数据始终最新
const realTimeStatistics = computed(() => {
  if (assets.value.length === 0) {
    return statistics.value
  }
  
  const totalCount = assets.value.length
  const byStatus = assets.value.reduce((acc, asset) => {
    acc[asset.status] = (acc[asset.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const byType = assets.value.reduce((acc, asset) => {
    acc[asset.asset_type] = (acc[asset.asset_type] || 0) + 1
    return acc
  }, {} as Record<string, number>)
  
  const byDepartment = assets.value.reduce((acc, asset) => {
    if (asset.department) {
      acc[asset.department] = (acc[asset.department] || 0) + 1
    }
    return acc
  }, {} as Record<string, number>)
  
  // 计算最近新增（最近7天）
  const recentDate = new Date()
  recentDate.setDate(recentDate.getDate() - 7)
  const recentAdditions = assets.value.filter(asset => 
    new Date(asset.created_at) > recentDate
  ).length
  
  return {
    total_count: totalCount,
    by_type: byType,
    by_status: byStatus,
    by_environment: {},
    by_department: byDepartment,
    recent_additions: recentAdditions,
    pending_maintenance: byStatus.maintenance || 0
  }
})
const searchQuery = ref('')
const showCreateModal = ref(false)
const showExtractModal = ref(false)
const showExtractResult = ref(false)
const showViewModal = ref(false)
const showExportModal = ref(false)
const editingAsset = ref<Asset | null>(null)
const viewingAsset = ref<Asset | null>(null)
const extractResult = ref<AssetExtractResult | null>(null)
const selectedAssets = ref<Asset[]>([])
const exporting = ref(false)
const exportFormat = ref('excel')
const exportFields = ref(['name', 'asset_type', 'ip_address', 'hostname', 'device_model', 'network_location', 'department', 'status'])
const fileList = ref<UploadFileInfo[]>([])
const uploadRef = ref(null)

// 筛选器
const filters = reactive({
  asset_type: null as AssetType | null,
  status: null as AssetStatus | null,
  department: null as string | null,
  network_location: null as string | null
})

// 排序配置
const sortConfig = reactive({
  sortBy: 'created_at' as string,
  sortOrder: 'desc' as 'asc' | 'desc'
})

// 表单数据
const assetForm = reactive<AssetCreate>({
  name: '',
  asset_type: AssetType.SERVER,
  device_model: '',
  ip_address: '',
  hostname: '',
  username: '',
  password: '',
  network_location: 'office',
  department: '',
  status: AssetStatus.ACTIVE,
  notes: ''
})

const extractForm = reactive({
  auto_merge: true,
  merge_threshold: 80
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  prefix: (info: any) => `共 ${info.itemCount || 0} 条`
})

// 选项数据
const assetTypeOptions = computed(() => 
  Object.values(AssetType).map(type => ({
    label: assetService.getAssetTypeName(type),
    value: type
  }))
)

const assetStatusOptions = computed(() =>
  Object.values(AssetStatus).map(status => ({
    label: assetService.getAssetStatusName(status),
    value: status
  }))
)

const networkLocationOptions = computed(() => [
  { label: '办公网', value: 'office' },
  { label: '监控网', value: 'monitoring' },
  { label: '收费网', value: 'billing' }
])

// 排序字段选项
const sortByOptions = computed(() => [
  { label: '创建时间', value: 'created_at' },
  { label: '更新时间', value: 'updated_at' },
  { label: '设备名称', value: 'name' },
  { label: '设备类型', value: 'asset_type' },
  { label: '所属部门', value: 'department' },
  { label: '所处网络', value: 'network_location' },
  { label: 'IP地址', value: 'ip_address' },
  { label: '状态', value: 'status' }
])

// 排序顺序选项
const sortOrderOptions = computed(() => [
  { label: '降序', value: 'desc' },
  { label: '升序', value: 'asc' }
])

// 从现有资产中获取部门选项
const departmentOptions = computed(() => {
  const departments = new Set<string>()
  assets.value.forEach(asset => {
    if (asset.department && asset.department.trim()) {
      departments.add(asset.department.trim())
    }
  })
  return Array.from(departments).sort().map(dept => ({
    label: dept,
    value: dept
  }))
})

// 表格列定义
const columns: DataTableColumns<Asset> = [
  {
    type: 'selection'
  },
  {
    title: '设备名称',
    key: 'name',
    width: 150,
    ellipsis: true
  },
  {
    title: '类型',
    key: 'asset_type',
    width: 100,
    render: (row) => h(NTag, { size: 'small' }, {
      default: () => assetService.getAssetTypeName(row.asset_type)
    })
  },
  {
    title: 'IP地址',
    key: 'ip_address',
    width: 120
  },
  {
    title: '主机名',
    key: 'hostname',
    width: 150,
    ellipsis: true
  },
  {
    title: '设备型号',
    key: 'device_model',
    width: 120,
    ellipsis: true
  },
  {
    title: '所处网络',
    key: 'network_location',
    width: 100,
    render: (row) => {
      // 检查是否有network_location字段
      if (!row.network_location) {
        return h('span', { style: { color: '#999' } }, '未设置')
      }
      
      const locationName = assetService.getNetworkLocationName(row.network_location)
      const locationColor = assetService.getNetworkLocationColor(row.network_location)
      
      return h(NTag, { 
        size: 'small',
        type: locationColor
      }, {
        default: () => locationName
      })
    }
  },
  {
    title: '部门',
    key: 'department',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row) => h(NTag, { 
      size: 'small',
      type: assetService.getAssetStatusColor(row.status)
    }, {
      default: () => assetService.getAssetStatusName(row.status)
    })
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, {
          size: 'small',
          type: 'primary',
          ghost: true,
          onClick: () => viewAsset(row)
        }, {
          icon: () => h(NIcon, { component: EyeOutline }),
          default: () => '查看'
        }),
        // 只有管理员才能看到编辑、复制和删除按钮
        ...(currentUser.value?.is_superuser ? [
          h(NButton, {
            size: 'small',
            onClick: () => editAsset(row)
          }, {
            icon: () => h(NIcon, { component: CreateOutline }),
            default: () => '编辑'
          }),
          h(NButton, {
            size: 'small',
            type: 'info',
            onClick: () => copyAsset(row.id)
          }, {
            icon: () => h(NIcon, { component: CopyOutline }),
            default: () => '复制'
          }),
          h(NButton, {
            size: 'small',
            type: 'error',
            onClick: () => deleteAsset(row.id)
          }, {
            icon: () => h(NIcon, { component: TrashOutline }),
            default: () => '删除'
          })
        ] : [])
      ]
    })
  }
]

// 提取结果表格列
const extractColumns: DataTableColumns<Asset> = [
  {
    title: '设备名称',
    key: 'name',
    width: 150
  },
  {
    title: '类型',
    key: 'asset_type',
    width: 100,
    render: (row) => assetService.getAssetTypeName(row.asset_type)
  },
  {
    title: 'IP地址',
    key: 'ip_address',
    width: 120
  },
  {
    title: '置信度',
    key: 'confidence_score',
    width: 80,
    render: (row) => `${row.confidence_score}%`
  },
  {
    title: '是否合并',
    key: 'is_merged',
    width: 80,
    render: (row) => row.is_merged ? '是' : '否'
  }
]

// 提取确认表格列（用于确认界面）
const extractConfirmColumns: DataTableColumns<any> = [
  {
    title: '设备名称',
    key: 'name',
    width: 150
  },
  {
    title: '类型',
    key: 'asset_type',
    width: 100,
    render: (row) => {
      const typeLabels = {
        'server': '服务器',
        'network': '网络设备',
        'storage': '存储设备',
        'security': '安全设备',
        'database': '数据库',
        'application': '应用程序',
        'other': '其他'
      }
      return typeLabels[row.asset_type] || row.asset_type
    }
  },
  {
    title: 'IP地址',
    key: 'ip_address',
    width: 120
  },
  {
    title: '置信度',
    key: 'confidence_score',
    width: 80,
    render: (row) => `${row.confidence_score || 85}%`
  },
  {
    title: '状态',
    key: 'conflicts',
    width: 100,
    render: (row) => {
      if (row.conflicts && row.conflicts.length > 0) {
        return h(NTag, { type: 'error', size: 'small' }, { default: () => '有冲突' })
      }
      return h(NTag, { type: 'success', size: 'small' }, { default: () => '可创建' })
    }
  }
]

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }],
  asset_type: [{ required: true, message: '请选择设备类型', trigger: 'change' }],
  network_location: [{ required: true, message: '请选择所处网络', trigger: 'change' }]
}

// 方法
const loadAssets = async () => {
  loading.value = true
  try {
    console.log('开始加载所有资产...')
    
    // 使用搜索API，空查询获取所有数据
    const query = {
      query: '',
      page: 1,
      per_page: 1000
    }
    
    const response = await assetService.searchAssets(query)
    console.log('加载资产成功，数量:', response.length)
    
    assets.value = response
    pagination.itemCount = response.length
    
    if (response.length > 0) {
      console.log('第一个资产详情:', response[0])
    }
  } catch (error: any) {
    console.error('加载资产失败:', error)
    message.error(error.message || error.detail || '加载资产失败')
    assets.value = []
    pagination.itemCount = 0
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  // 优化：优先使用本地资产数据实时计算统计，减少网络请求延迟
  if (assets.value.length > 0) {
    // 基于当前assets数据实时计算统计
    const totalCount = assets.value.length
    const byStatus = assets.value.reduce((acc, asset) => {
      acc[asset.status] = (acc[asset.status] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    const byType = assets.value.reduce((acc, asset) => {
      acc[asset.asset_type] = (acc[asset.asset_type] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    const byDepartment = assets.value.reduce((acc, asset) => {
      if (asset.department) {
        acc[asset.department] = (acc[asset.department] || 0) + 1
      }
      return acc
    }, {} as Record<string, number>)
    
    // 计算最近新增（假设最近7天）
    const recentDate = new Date()
    recentDate.setDate(recentDate.getDate() - 7)
    const recentAdditions = assets.value.filter(asset => 
      new Date(asset.created_at) > recentDate
    ).length
    
    statistics.value = {
      total_count: totalCount,
      by_type: byType,
      by_status: byStatus,
      by_environment: {},
      by_department: byDepartment,
      recent_additions: recentAdditions,
      pending_maintenance: byStatus.maintenance || 0
    }
    
    // 异步尝试从服务器获取更准确的统计数据，但不阻塞UI
    try {
      const serverStats = await assetService.getStatistics()
      statistics.value = serverStats
    } catch (error: any) {
      console.log('服务器统计API失败，使用本地计算结果:', error)
    }
  } else {
    // 如果没有资产数据，尝试从服务器获取统计
    try {
      statistics.value = await assetService.getStatistics()
    } catch (error: any) {
      console.log('统计API失败，使用默认值:', error)
      statistics.value = {
        total_count: 0,
        by_type: {},
        by_status: {},
        by_environment: {},
        by_department: {},
        recent_additions: 0,
        pending_maintenance: 0
      }
    }
  }
}

// 创建防抖搜索函数
const debouncedSearch = debounce(async (resetPage = true) => {
  try {
    loading.value = true
    
    // 检查是否有任何实际的搜索条件
    const hasSearchQuery = searchQuery.value && searchQuery.value.trim() !== ''
    const hasFilters = filters.asset_type || filters.status || 
                     filters.department || 
                     filters.network_location
    
    const query = {
      query: searchQuery.value || '',
      asset_type: filters.asset_type || undefined,
      status: filters.status || undefined,
      department: filters.department || undefined,
      network_location: filters.network_location || undefined,
      sort_by: sortConfig.sortBy,
      sort_order: sortConfig.sortOrder,
      page: 1,
      per_page: 1000
    }
    
    // 统一使用搜索API，无论是否有筛选条件
    const searchResults = await assetService.searchAssets(query)
    assets.value = searchResults
    pagination.itemCount = searchResults.length
    
    // 只有在指定重置页码时才重置，否则保持当前页码
    if (resetPage) {
      pagination.page = 1
    }
  } catch (error: any) {
    console.error('搜索失败:', error)
    message.error(error.message || error.detail || '搜索失败')
    // 出错时不清空数据，保持当前状态
  } finally {
    loading.value = false
  }
}, 300)

// 替换原来的handleSearch函数为防抖版本
const handleSearch = (resetPage = true) => debouncedSearch(resetPage)

const handleDepartmentFilter = async (value: string | null) => {
  // 无论选择值还是清空，都调用统一的搜索逻辑
  await handleSearch()
}

// 处理排序变化
const handleSortChange = async () => {
  await handleSearch()
}

const handlePageChange = (page: number) => {
  pagination.page = page
  // 不需要重新加载数据，NaiveUI会自动处理分页
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  // 不需要重新加载数据，NaiveUI会自动处理分页
}

const resetForm = () => {
  Object.assign(assetForm, {
    name: '',
    asset_type: AssetType.SERVER,
    device_model: '',
    ip_address: '',
    hostname: '',
    username: '',
    password: '',
    network_location: 'office',
    department: '',
    status: AssetStatus.ACTIVE,
    notes: ''
  })
  editingAsset.value = null
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (editingAsset.value) {
      // For updates, only send editable fields
      const updateData = {
        name: assetForm.name,
        asset_type: assetForm.asset_type,
        device_model: assetForm.device_model,
        ip_address: assetForm.ip_address,
        hostname: assetForm.hostname,
        username: assetForm.username,
        password: assetForm.password,
        network_location: assetForm.network_location,
        department: assetForm.department,
        status: assetForm.status,
        notes: assetForm.notes
      }
      await assetService.updateAsset(editingAsset.value.id, updateData)
      message.success('设备更新成功')
    } else {
      // For creation, send the full form
      await assetService.createAsset(assetForm)
      message.success('设备创建成功')
    }
    
    showCreateModal.value = false
    resetForm()
    // 创建/编辑后保持当前筛选状态和页码重新搜索
    await handleSearch(false)  // 不重置页码
    await loadStatistics()
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const editAsset = async (asset: Asset) => {
  try {
    // 获取完整的资产详情（包括用户名和密码）
    const fullAsset = await assetService.getAsset(asset.id)
    editingAsset.value = fullAsset
    
    // Only copy editable fields, not timestamps or system fields
    Object.assign(assetForm, {
      id: fullAsset.id,
      name: fullAsset.name,
      asset_type: fullAsset.asset_type,
      device_model: fullAsset.device_model,
      ip_address: fullAsset.ip_address,
      hostname: fullAsset.hostname,
      username: fullAsset.username,
      password: fullAsset.password,
      network_location: fullAsset.network_location,
      department: fullAsset.department,
      status: fullAsset.status,
      notes: fullAsset.notes,
      tags: fullAsset.tags || []
    })
    showCreateModal.value = true
  } catch (error: any) {
    message.error('获取资产详情失败')
  }
}

const viewAsset = async (asset: Asset) => {
  const startTime = Date.now()
  
  try {
    // 获取完整的资产详情（包括用户名和密码）用于显示
    const fullAsset = await assetService.getAsset(asset.id)
    viewingAsset.value = fullAsset
    showViewModal.value = true
    
  } catch (error: any) {
    console.error('查看资产详情失败:', error)
    message.error('获取资产详情失败')
  }
}

const deleteAsset = async (id: number) => {
  // 找到要删除的资产信息
  const asset = assets.value.find(a => a.id === id)
  const assetName = asset ? asset.name : `ID: ${id}`
  
  dialog.warning({
    title: '确认删除',
    content: `确定要删除设备 "${assetName}" 吗？此操作不可撤销。`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await assetService.deleteAsset(id)
        message.success('设备删除成功')
        // 删除后保持当前筛选状态和页码重新搜索
        await handleSearch(false)  // 不重置页码
        await loadStatistics()
      } catch (error: any) {
        message.error(error.detail || '删除失败')
      }
    }
  })
}


const handleBeforeUpload = (data: { file: UploadFileInfo }) => {
  // 检查文件类型
  const allowedTypes = ['txt', 'csv', 'xlsx', 'xls', 'json', 'md']
  const fileExt = data.file.name?.split('.').pop()?.toLowerCase() || ''
  
  if (!allowedTypes.includes(fileExt)) {
    message.error(`不支持的文件类型，支持格式：${allowedTypes.join(', ')}`)
    return false
  }
  
  // 检查文件大小 (10MB)
  const maxSize = 10 * 1024 * 1024
  if (data.file.file && data.file.file.size > maxSize) {
    message.error('文件大小不能超过10MB')
    return false
  }
  
  return true
}

const handleExtract = async () => {
  if (!fileList.value.length || !fileList.value[0].file) {
    message.error('请选择文件')
    return
  }
  
  extracting.value = true
  try {
    // 检查是否已登录
    if (!authService.isAuthenticated()) {
      message.error('请先登录后再使用文件提取功能')
      extracting.value = false
      return
    }
    
    const formData = new FormData()
    formData.append('file', fileList.value[0].file)
    formData.append('auto_merge', extractForm.auto_merge.toString())
    formData.append('merge_threshold', extractForm.merge_threshold.toString())
    
    // 调试信息
    console.log('=== 文件提取调试信息 ===')
    console.log('文件名:', fileList.value[0].file.name)
    console.log('文件大小:', fileList.value[0].file.size)
    console.log('文件类型:', fileList.value[0].file.type)
    console.log('auto_merge:', extractForm.auto_merge.toString())
    console.log('merge_threshold:', extractForm.merge_threshold.toString())
    
    // 使用原来的fetch方法，因为这个是工作的
    const currentHost = window.location.hostname
    const currentProtocol = window.location.protocol
    let apiBaseUrl = import.meta.env.VITE_API_BASE_URL
    
    if (!apiBaseUrl) {
      if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        apiBaseUrl = `${currentProtocol}//${currentHost}:8002`
      } else {
        apiBaseUrl = 'http://localhost:8002'
      }
    }
    
    const token = authService.getToken()
    if (!token) {
      message.error('请先登录')
      extracting.value = false
      return
    }
    
    const response = await fetch(`${apiBaseUrl}/api/v1/assets/file-extract`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '提取失败')
    }
    
    extractResult.value = await response.json()
    showExtractModal.value = false
    showExtractResult.value = true
    
    // 清空文件列表
    fileList.value = []
    
    if (extractResult.value.assets.length > 0) {
      message.success(`成功提取 ${extractResult.value.assets.length} 个设备`)
    } else {
      message.warning('未能提取到有效的设备信息')
    }
  } catch (error: any) {
    console.error('文件提取错误:', error)
    // 处理认证错误
    if (error.response?.status === 401 || error.response?.status === 403) {
      message.error('登录状态已过期，请重新登录后再使用文件提取功能')
    } else {
      message.error(error.message || '提取失败')
    }
  } finally {
    extracting.value = false
  }
}

const refreshAssets = async () => {
  showExtractResult.value = false
  // 刷新后重新加载资产列表
  await loadAssets()
  await loadStatistics()
}

// 确认提取的资产并保存到数据库
const confirmExtractedAssets = async () => {
  if (!extractResult.value || !extractResult.value.assets.length) {
    message.error('没有可确认的资产')
    return
  }
  
  confirming.value = true
  try {
    // 检查是否已登录
    if (!authService.isAuthenticated()) {
      message.error('请先登录后再确认保存')
      confirming.value = false
      return
    }
    
    // 使用原来的fetch方法
    const currentHost = window.location.hostname
    const currentProtocol = window.location.protocol
    let apiBaseUrl = import.meta.env.VITE_API_BASE_URL
    
    if (!apiBaseUrl) {
      if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        apiBaseUrl = `${currentProtocol}//${currentHost}:8002`
      } else {
        apiBaseUrl = 'http://localhost:8002'
      }
    }
    
    const token = authService.getToken()
    
    const response = await fetch(`${apiBaseUrl}/api/v1/assets/file-extract/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(extractResult.value.assets)
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '确认保存失败')
    }
    
    const result = await response.json()
    
    if (result.success) {
      message.success(`成功创建 ${result.saved_count} 个设备${result.error_count > 0 ? `，${result.error_count} 个失败` : ''}`)
      
      if (result.errors && result.errors.length > 0) {
        console.warn('保存过程中的错误:', result.errors)
      }
      
      // 关闭确认对话框并保持筛选状态和页码刷新列表
      showExtractResult.value = false
      await handleSearch(false)  // 不重置页码
      await loadStatistics()
    } else {
      message.error('保存失败')
    }
  } catch (error: any) {
    console.error('确认保存失败:', error)
    message.error(error.message || '确认保存失败')
  } finally {
    confirming.value = false
  }
}

// 复制资产 - 打开添加表单并预填充数据
const copyAsset = async (assetId: number) => {
  try {
    // 获取原始资产的完整信息
    const originalAsset = await assetService.getAsset(assetId)
    
    // 重置表单并设为创建模式
    editingAsset.value = null
    
    // 预填充表单数据，保留包括IP地址在内的所有信息
    Object.assign(assetForm, {
      name: `${originalAsset.name}_副本`,
      asset_type: originalAsset.asset_type,
      device_model: originalAsset.device_model,
      ip_address: originalAsset.ip_address, // 保留IP地址
      hostname: originalAsset.hostname ? `${originalAsset.hostname}_copy` : '',
      username: originalAsset.username,
      password: originalAsset.password,
      network_location: originalAsset.network_location,
      department: originalAsset.department,
      status: 'inactive', // 设置为非活跃状态
      notes: `复制自资产: ${originalAsset.name}`
    })
    
    // 打开创建模态框
    showCreateModal.value = true
    
    message.info('已预填充资产信息，请修改后保存')
  } catch (error: any) {
    message.error('获取资产信息失败')
  }
}

// 批量删除资产
const handleBulkDelete = () => {
  if (selectedAssets.value.length === 0) {
    message.error('请选择要删除的资产')
    return
  }
  
  const assetNames = selectedAssets.value.map(asset => asset.name).join('、')
  
  dialog.warning({
    title: '批量删除确认',
    content: `确定要删除以下 ${selectedAssets.value.length} 个资产吗？\n${assetNames}\n\n此操作不可撤销。`,
    positiveText: '确定删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const assetIds = selectedAssets.value.map(asset => asset.id)
        
        // 使用原来的fetch方法
        const currentHost = window.location.hostname
        const currentProtocol = window.location.protocol
        let apiBaseUrl = import.meta.env.VITE_API_BASE_URL
        
        if (!apiBaseUrl) {
          if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
            apiBaseUrl = `${currentProtocol}//${currentHost}:8002`
          } else {
            apiBaseUrl = 'http://localhost:8002'
          }
        }
        
        const response = await fetch(`${apiBaseUrl}/api/v1/assets/batch/delete`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({ asset_ids: assetIds })
        })
        
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.detail || '删除失败')
        }
        
        const result = await response.json()
        message.success(result.message)
        
        // 清空选择
        selectedAssets.value = []
        
        // 批量删除后保持当前筛选状态和页码重新搜索
        await handleSearch(false)  // 不重置页码
        await loadStatistics()
      } catch (error: any) {
        message.error(error.message || '批量删除失败')
      }
    }
  })
}

const editCurrentAsset = () => {
  if (viewingAsset.value) {
    // 关闭查看弹窗
    showViewModal.value = false
    // 设置为编辑模式
    editAsset(viewingAsset.value)
  }
}

// 处理资产选择变化
const handleSelectionChange = (keys: Array<string | number>) => {
  selectedAssets.value = assets.value.filter(asset => keys.includes(asset.id))
}

// 处理资产导出
const handleExport = async () => {
  if (!selectedAssets.value.length) {
    message.error('请选择要导出的资产')
    return
  }
  
  if (!exportFields.value.length) {
    message.error('请选择要导出的字段')
    return
  }
  
  exporting.value = true
  try {
    const assetIds = selectedAssets.value.map(asset => asset.id)
    
    // 检查是否已登录
    if (!authService.isAuthenticated()) {
      message.error('请先登录后再使用导出功能')
      exporting.value = false
      return
    }
    
    // 导出功能需要处理文件下载，使用apiService的download方法
    const filename = `assets_export_${new Date().getTime()}.${exportFormat.value === 'excel' ? 'xlsx' : 'csv'}`
    
    // 构建查询参数
    const exportData = {
      asset_ids: assetIds,
      format: exportFormat.value,
      fields: exportFields.value
    }
    
    // 使用fetch进行导出（因为需要处理blob响应）
    const currentHost = window.location.hostname
    const currentProtocol = window.location.protocol
    let apiBaseUrl = import.meta.env.VITE_API_BASE_URL
    
    if (!apiBaseUrl) {
      if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
        apiBaseUrl = `${currentProtocol}//${currentHost}:8002`
      } else {
        apiBaseUrl = 'http://localhost:8002'
      }
    }
    
    const token = authService.getToken()
    if (!token) {
      throw new Error('请先登录')
    }
    
    const response = await fetch(`${apiBaseUrl}/api/v1/assets/export`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(exportData)
    })
    
    if (response.ok) {
      // 获取文件blob
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      
      // 创建下载链接
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      // 清理URL对象
      window.URL.revokeObjectURL(url)
      
      message.success(`成功导出 ${selectedAssets.value.length} 个资产`)
      showExportModal.value = false
      
      // 清空选择
      selectedAssets.value = []
    } else {
      const errorData = await response.json()
      throw new Error(errorData.detail || '导出失败')
    }
  } catch (error: any) {
    message.error(error.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

// 监听提取模态框打开状态，清空文件列表
watch(showExtractModal, (newValue) => {
  if (newValue) {
    fileList.value = []
  }
})

// 加载当前用户信息
const loadCurrentUser = async () => {
  try {
    currentUser.value = await authService.getCurrentUser()
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
}

// 辅助方法
const getAssetTypeLabel = (type: string) => {
  const types = {
    server: '服务器',
    network: '网络设备',
    storage: '存储设备',
    security: '安全设备',
    database: '数据库',
    application: '应用程序',
    other: '其他'
  }
  return types[type] || type
}

const getAssetStatusLabel = (status: string) => {
  const statuses = {
    active: '在用',
    inactive: '停用',
    maintenance: '维护中',
    retired: '已退役'
  }
  return statuses[status] || status
}

const getNetworkLocationLabel = (location: string) => {
  const locations = {
    office: '办公网',
    monitoring: '监控网',
    billing: '收费网'
  }
  return locations[location] || location
}

const getStatusType = (status: string) => {
  const types = {
    active: 'success',
    inactive: 'default',
    maintenance: 'warning',
    retired: 'error'
  }
  return types[status] || 'default'
}

const formatDateTime = (dateString: string) => {
  if (!dateString) return '未设置'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 导出字段选择辅助方法（仅包含编辑表单中的字段和时间戳）
const allExportFields = [
  'name', 'asset_type', 'ip_address', 'hostname', 'username', 'password',
  'device_model', 'network_location', 'department', 'status', 'notes',
  'created_at', 'updated_at'
]

const basicExportFields = [
  'name', 'asset_type', 'ip_address', 'hostname', 'device_model',
  'network_location', 'department', 'status', 'created_at'
]

const selectAllFields = () => {
  exportFields.value = [...allExportFields]
}

const clearAllFields = () => {
  exportFields.value = []
}

const selectBasicFields = () => {
  exportFields.value = [...basicExportFields]
}

onMounted(async () => {
  // 优化：先加载资产数据，然后基于资产数据计算统计，避免延迟
  await Promise.all([
    loadAssets(),
    loadStatistics(),
    loadCurrentUser()
  ])
})
</script>

<style scoped>
/* AssetView specific styles can be added here if needed */
</style>