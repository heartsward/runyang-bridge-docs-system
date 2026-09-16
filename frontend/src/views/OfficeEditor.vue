<!--
  阶段二十七·27.2：OnlyOffice 在线预览（只读，不再支持编辑）
  修复：必须把 OnlyOffice SDK (api.js) 作为 <script> 加载到本页执行，
        SDK 内部会自动创建 iframe 加载编辑器。
        之前错误：把 api.js URL 直接当 iframe src，浏览器把 JS 源码渲染成文本。
  流程：
  1. 页面挂载 → 拉后端拿 config dict（已含 document.url / fileType / callbackUrl）
  2. 动态 <script> 加载 DS 的 api.js（DOC_SCRIPT_SRC）
  3. script onload 后用 new DocsAPI.DocEditor('placeholderId', config) 初始化
  4. SDK 用 iframe **替换**（replaceChild）占位 div 加载 DS 预览器（mode=view，无编辑权限）
     → 显式高度必须挂外层 .office-editor-host；iframe height="100%" 属性依赖父级显式高度
-->
<template>
  <PageLayout title="在线预览">
    <template #header-actions>
      <n-button @click="goBack" type="default" size="small">
        ← 返回文档列表
      </n-button>
    </template>

    <n-spin :show="loading" description="正在加载 OnlyOffice 预览…">
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
          ({{ docInfo.file_name }} · {{ docInfo.file_type?.toUpperCase() }} · 只读预览)
        </n-text>
      </div>

      <!-- OnlyOffice SDK 会用 iframe 直接替换占位 div（replaceChild），
           所以高度必须挂在"不会被替换"的外层 host 上，iframe 再撑满 host -->
      <div class="office-editor-host">
        <div id="onlyoffice-editor-container" class="editor-frame-wrapper" />
      </div>

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

let editorInstance: any = null

function destroyEditor() {
  // SDK 的 DocEditor 实例自带 destroyEditor()（api.js 内 _destroyEditor：
  // 解绑事件 + 移除 iframe + 重建占位 div）。优先走官方 API；
  // 兜底按 name="frameEditor" 找 iframe 移除（占位 div 已被 replaceChild 替换，按 id 找不到）
  try {
    if (editorInstance && typeof editorInstance.destroyEditor === 'function') {
      editorInstance.destroyEditor()
      editorInstance = null
      editorInited.value = false
      return
    }
  } catch {
    // 忽略，走兜底
  }
  const host = document.querySelector('.office-editor-host')
  const frame = host?.querySelector('iframe[name="frameEditor"]')
  if (frame) frame.remove()
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

    // 2) 拉预览配置（含 document.url / fileType / callbackUrl / token）
    const editorResp = await apiService.post<{
      doc_id: number
      file_name: string
      file_type: string
      url: string
      config: OOConfig
    }>(`/onlyoffice/documents/${docId}/preview-url`, {})
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

    // 4) 等待 DOM 就绪，初始化编辑器（SDK 会用 iframe **替换**占位 div）
    //    显式传 width/height 100%：iframe 属性按父级（.office-editor-host，
    //    已有 calc 显式高度）解析，100% 才能生效
    await nextTick()
    editorInstance = window.DocsAPI.DocEditor(EDITOR_PLACEHOLDER_ID, {
      ...ooConfig,
      width: '100%',
      height: '100%',
    })

    editorInited.value = true
    loading.value = false
  } catch (e: any) {
    error.value = '无法加载 OnlyOffice 预览'
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

/* 关键：SDK 会 replaceChild 用 iframe 替换占位 div，
   所以显式高度必须挂在这个"不会被替换"的 host 上 */
.office-editor-host {
  width: 100%;
  height: calc(100vh - 190px);
  min-height: 500px;
  border: 1px solid #e0e0e6;
  border-radius: 6px;
  overflow: hidden;
  background-color: #fff;
}

/* 占位 div（被替换前的 loading 态）撑满 host */
.editor-frame-wrapper {
  width: 100%;
  height: 100%;
}

/* SDK 替换进来的 iframe（name="frameEditor"）撑满 host。
   iframe 的 width/height 是 HTML 属性：父级无显式高度时 height="100%"
   会回落到默认 150px——这就是"编辑器只有一小条"的根因 */
.office-editor-host :deep(iframe) {
  width: 100% !important;
  height: 100% !important;
  border: none !important;
}
</style>