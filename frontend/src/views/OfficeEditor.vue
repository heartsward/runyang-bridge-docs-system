<!--
  阶段二十七：OnlyOffice 在线编辑器
  修复：必须把 OnlyOffice SDK (api.js) 作为 <script> 加载到本页执行，
        SDK 内部会自动创建 iframe 加载编辑器。
        之前错误：把 api.js URL 直接当 iframe src，浏览器把 JS 源码渲染成文本。
  流程：
  1. 页面挂载 → 拉后端拿 config dict（已含 document.url / fileType / callbackUrl）
  2. 动态 <script> 加载 DS 的 api.js（DOC_SCRIPT_SRC）
  3. script onload 后用 new DocsAPI.DocEditor('placeholderId', config) 初始化
  4. SDK 自动创建 iframe 加载 DS 编辑器
  5. DS 编辑 → 用户保存 → DS 回调后端 /onlyoffice/callback
-->
<template>
  <PageLayout title="在线编辑">
    <template #header-actions>
      <n-button @click="goBack" type="default" size="small">
        ← 返回文档列表
      </n-button>
    </template>

    <n-spin :show="loading" description="正在加载 OnlyOffice 编辑器…">
      <n-alert
        v-if="error"
        type="error"
        :title="error"
        :show-icon="true"
        style="margin-bottom: 16px;"
      >
        {{ errorDetails }}
        <br />
        <n-text depth="3" style="font-size: 12px;">
          提示：OnlyOffice Document Server 地址 <code>{{ dsUrl || '未配置' }}</code> 必须在浏览器可访问；
          后端回调地址 <code>{{ callbackUrl || '未配置' }}</code> 必须能被 DS 反向访问到。
        </n-text>
      </n-alert>

      <div v-if="docInfo" class="editor-meta">
        <n-text strong>{{ docInfo.title }}</n-text>
        <n-text depth="3" style="margin-left: 12px;">
          ({{ docInfo.file_name }} · {{ docInfo.file_type?.toUpperCase() }})
        </n-text>
        <n-tag
          v-if="saveStatus === 'saved'"
          type="success"
          size="small"
          style="margin-left: 12px;"
        >
          ✓ 已保存
        </n-tag>
        <n-tag
          v-if="saveStatus === 'saving'"
          type="info"
          size="small"
          style="margin-left: 12px;"
        >
          正在保存…
        </n-tag>
      </div>

      <!-- OnlyOffice SDK 会自动创建一个 iframe 插入到这里 -->
      <div id="onlyoffice-editor-container" class="editor-frame-wrapper" />

      <!-- SDK 未加载完成前的 fallback 提示 -->
      <div v-if="!editorInited" style="text-align: center; padding: 60px; color: #999;">
        <n-spin size="large" />
        <div style="margin-top: 16px;">正在连接 OnlyOffice Document Server…</div>
      </div>
    </n-spin>
  </PageLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import apiService from '@/services/api'
import PageLayout from '@/components/PageLayout.vue'

interface DocInfo {
  id: number
  title: string
  file_name: string
  file_type: string
  url: string  // 后端签发的 editor 入口 URL（用于显示信息）
}

interface OOConfig {
  // 后端返回给前端直接用的 config dict（前端 SDK 接受这种格式）
  document: {
    fileType: string
    key: string
    title: string
    url: string
    permissions: Record<string, boolean>
  }
  editorConfig: {
    mode: string
    lang: string
    user: { id: string; name: string }
    callbackUrl: string
    customization: Record<string, any>
  }
  token: string
}

const route = useRoute()
const router = useRouter()
const message = useMessage()

const docId = String(route.params.docId || '')

const loading = ref(true)
const error = ref<string | null>(null)
const errorDetails = ref<string>('')
const docInfo = ref<DocInfo | null>(null)
const dsUrl = ref<string>('')
const callbackUrl = ref<string>('')
const saveStatus = ref<'idle' | 'saving' | 'saved'>('idle')
const editorInited = ref(false)

const EDITOR_PLACEHOLDER_ID = 'onlyoffice-editor-container'

function goBack() {
  router.push('/documents')
}

declare global {
  interface Window {
    DocsAPI?: any
  }
}

// 加载 OnlyOffice SDK JS
function loadOnlyOfficeSdk(dsBaseUrl: string): Promise<void> {
  return new Promise((resolve, reject) => {
    // 如果已经加载过，直接用
    if (window.DocsAPI && typeof window.DocsAPI.DocEditor === 'function') {
      resolve()
      return
    }
    // SDK JS 路径：DS_URL + /web-apps/apps/api/documents/api.js
    const sdkSrc = `${dsBaseUrl.replace(/\/$/, '')}/web-apps/apps/api/documents/api.js`
    const script = document.createElement('script')
    script.src = sdkSrc
    script.async = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`加载 OnlyOffice SDK 失败: ${sdkSrc}`))
    document.head.appendChild(script)
  })
}

function destroyEditor() {
  // SDK 没有提供 destroy API；用最朴素的方式移除占位 div 内的 iframe
  const container = document.getElementById(EDITOR_PLACEHOLDER_ID)
  if (container) {
    container.innerHTML = ''
  }
  editorInited.value = false
}

onMounted(async () => {
  if (!docId) {
    error.value = '无效的文档 ID'
    loading.value = false
    return
  }

  try {
    // 1) 拉 DS 配置（拿 DS URL + 回调 base URL）
    const cfg = await apiService.get<{
      ds_url: string
      callback_base_url: string
    }>('/onlyoffice/config')
    dsUrl.value = cfg.ds_url
    callbackUrl.value = cfg.callback_base_url

    // 2) 拉 editor 配置（含 document.url / fileType / callbackUrl / token）
    const editorResp = await apiService.post<{
      doc_id: number
      file_name: string
      file_type: string
      url: string
      config: OOConfig
    }>(`/onlyoffice/documents/${docId}/url`, {})
    docInfo.value = {
      id: editorResp.doc_id,
      title: editorResp.file_name,
      file_name: editorResp.file_name,
      file_type: editorResp.file_type,
      url: editorResp.url,
    }
    const ooConfig: OOConfig = editorResp.config

    // 3) 加载 SDK JS（首次需要；之后会缓存到 window.DocsAPI）
    await loadOnlyOfficeSdk(cfg.ds_url)
    if (!window.DocsAPI || typeof window.DocsAPI.DocEditor !== 'function') {
      throw new Error('OnlyOffice SDK 加载完成但 DocsAPI 未就绪')
    }

    // 4) 等待 DOM 就绪，初始化编辑器（SDK 会自动插入 iframe 到 container）
    await nextTick()
    window.DocsAPI.DocEditor(EDITOR_PLACEHOLDER_ID, ooConfig)

    editorInited.value = true
    loading.value = false
  } catch (e: any) {
    error.value = '无法加载 OnlyOffice 编辑器'
    errorDetails.value = e?.response?.data?.detail || e?.message || String(e)
    loading.value = false
  }
})

onBeforeUnmount(() => {
  destroyEditor()
})
</script>

<style scoped>
.editor-meta {
  margin-bottom: 12px;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.editor-frame-wrapper {
  width: 100%;
  height: calc(100vh - 220px);
  min-height: 500px;
  border: 1px solid #e0e0e6;
  border-radius: 6px;
  overflow: hidden;
  background-color: #fff;
}

/* OnlyOffice SDK 注入的 iframe 自适应 */
.editor-frame-wrapper :deep(iframe) {
  width: 100% !important;
  height: 100% !important;
  border: none !important;
}
</style>