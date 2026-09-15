<!--
  阶段二十七：OnlyOffice 在线编辑器
  流程：
  1. 页面挂载 → 调 GET /onlyoffice/config 拿 DS URL（前端要可见）
  2. 调 POST /onlyoffice/documents/{id}/url 拿编辑入口 URL（已 base64 编码 config）
  3. <iframe> 嵌入 OnlyOffice 编辑器（src 指向 DS 的 api.js?config=...）
  4. DS 编辑 → 用户点保存 → DS 回调后端 /onlyoffice/callback
  5. 后端覆盖原文件 + 触发重新提取
  6. 用户点关闭 → DS 调 callback status=4 → 不下载，仅提示前端
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
        请确认 OnlyOffice Document Server 已正确部署并允许 HTTP callback。
        <br />
        详细信息：{{ errorDetails }}
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
      </div>

      <div v-if="editorUrl" class="editor-frame-wrapper">
        <iframe
          ref="iframeRef"
          :src="editorUrl"
          class="editor-frame"
          title="OnlyOffice 编辑器"
          allow="fullscreen"
          @load="onIframeLoaded"
        />
      </div>
    </n-spin>
  </PageLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import apiService from '@/services/api'
import PageLayout from '@/components/PageLayout.vue'

interface DocInfo {
  id: number
  title: string
  file_name: string
  file_type: string
  url: string
}

const route = useRoute()
const router = useRouter()
const message = useMessage()

const docId = String(route.params.docId || '')

const loading = ref(true)
const error = ref<string | null>(null)
const errorDetails = ref<string>('')
const editorUrl = ref<string | null>(null)
const docInfo = ref<DocInfo | null>(null)
const saveStatus = ref<'idle' | 'saved'>('idle')

// iframe 加载完成（仅用于清掉 loading spinner）
function onIframeLoaded() {
  loading.value = false
}

function goBack() {
  router.push('/documents')
}

// 监听来自 OnlyOffice iframe 的 postMessage（编辑器会发 save/dirty 等事件）
function onMessage(event: MessageEvent) {
  const data = event.data
  if (typeof data !== 'object' || data === null) return
  // OnlyOffice 通过 window.parent.postMessage 发消息
  // 参考：https://api.onlyoffice.com/editors/callback-handler.html
  const msgType = data.type || data.message
  if (msgType === 'onDocumentStateChange' || msgType === 'onSave') {
    if (data.data === true) {
      saveStatus.value = 'saved'
    }
  }
  // 编辑器要求父页关闭时
  if (msgType === 'onRequestClose' || msgType === 'onReady') {
    // 忽略：让用户手动返回
  }
}

onMounted(async () => {
  if (!docId) {
    error.value = '无效的文档 ID'
    loading.value = false
    return
  }

  // 监听来自 OnlyOffice iframe 的事件
  window.addEventListener('message', onMessage)

  try {
    // 1) 签发编辑入口 URL（后端已生成完整的 base64 config）
    const resp = await apiService.post<DocInfo>(
      `/onlyoffice/documents/${docId}/url`,
      {}
    )
    docInfo.value = resp
    editorUrl.value = resp.url
    // loading 状态在 iframe @load 时清
  } catch (e: any) {
    error.value = '无法获取 OnlyOffice 编辑器入口'
    errorDetails.value = e?.response?.data?.detail || e?.message || String(e)
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('message', onMessage)
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
  border: 1px solid #e0e0e6;
  border-radius: 6px;
  overflow: hidden;
  background-color: #fff;
}

.editor-frame {
  width: 100%;
  height: 100%;
  border: none;
}
</style>