<!--
  McpTokenModal.vue（32.2）
  显示当前用户的 MCP 调用验证码：
  - 普通用户：个人码，可复制、可重新随机（旧码立即失效）
  - 管理员：统一码，可复制；重置入口在系统设置（此处只展示）
  用法：<McpTokenModal v-model:show="showMcp" @changed="..." />
-->
<template>
  <n-modal
    :show="show"
    preset="card"
    style="width: 560px"
    title="MCP 调用验证码"
    @update:show="(v: boolean) => emit('update:show', v)"
  >
    <n-space vertical size="medium">
      <n-alert :type="status?.mode === 'admin' ? 'warning' : 'info'" :bordered="false">
        <template v-if="status?.mode === 'admin'">
          您是<strong>管理员</strong>，使用全系统统一的 MCP 验证码。升为管理员后个人码已自动取消；
          如需重置统一码请到「系统设置 → MCP 验证码」。
        </template>
        <template v-else>
          这是您的<strong>个人</strong> MCP 验证码，调用知识库 MCP（http://…/mcp）时在
          Authorization: Bearer 后填它。可随时重新随机，旧码立即失效。
        </template>
      </n-alert>

      <n-spin v-if="loading" size="small" style="display:block; margin: 16px auto;" />
      <template v-else-if="status">
        <n-input-group>
          <n-input
            :value="revealed ? status.token : mask(status.token)"
            readonly
            style="font-family: 'Consolas', 'Monaco', monospace;"
          />
          <n-button quaternary @click="revealed = !revealed">
            {{ revealed ? '隐藏' : '显示' }}
          </n-button>
          <n-button type="primary" ghost @click="copyToken">复制</n-button>
        </n-input-group>

        <n-space>
          <n-popconfirm
            v-if="status.can_regenerate_personal"
            @positive-click="doRegenerate"
          >
            <template #trigger>
              <n-button type="error" :loading="regenerating">重新随机</n-button>
            </template>
            重新随机后旧码立即失效，所有用旧码的 MCP 客户端都要更换。确定？
          </n-popconfirm>
        </n-space>
      </template>

      <n-text depth="3" style="font-size: 12px;">
        MCP 客户端配置示例：{"url": "http://{{ apiHost }}/mcp", "headers": {"Authorization": "Bearer &lt;验证码&gt;"}}
      </n-text>
    </n-space>

    <template #footer>
      <n-space justify="end">
        <n-button @click="emit('update:show', false)">关闭</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  NModal, NSpace, NAlert, NInput, NInputGroup, NButton, NPopconfirm, NText, NSpin, useMessage,
} from 'naive-ui'
import { settingsService } from '@/services/settings'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'changed'): void
}>()

const message = useMessage()
const loading = ref(false)
const regenerating = ref(false)
const revealed = ref(false)
const status = ref<{ mode: 'admin' | 'personal'; token: string; can_regenerate_personal: boolean; note?: string } | null>(null)

const apiHost = computed(() => `${window.location.hostname}:8002`)

const mask = (t: string) => (t ? t.slice(0, 4) + '•'.repeat(Math.max(t.length - 8, 4)) + t.slice(-4) : '')

const load = async () => {
  loading.value = true
  try {
    status.value = await settingsService.getMyMcpToken()
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '获取 MCP 验证码失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.show, (v) => {
  if (v) { revealed.value = false; load() }
})

const copyToken = async () => {
  if (!status.value?.token) return
  try {
    await navigator.clipboard.writeText(status.value.token)
    message.success('验证码已复制到剪贴板')
  } catch {
    message.error('复制失败，请手动选择复制')
  }
}

const doRegenerate = async () => {
  regenerating.value = true
  try {
    const r = await settingsService.regenerateMyMcpToken()
    message.success(r.message || '已重新随机')
    revealed.value = true
    await load()
    emit('changed')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '重新随机失败')
  } finally {
    regenerating.value = false
  }
}
</script>
