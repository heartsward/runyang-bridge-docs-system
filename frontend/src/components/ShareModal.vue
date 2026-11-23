<!--
  ShareModal.vue（32.1）
  管理员把文档/资产分享给指定用户（只读）。
  用法：<ShareModal v-model:show="showShare" :item-type="'document'" :item-id="id" :item-title="title" />
  - 打开时拉取全部用户 + 该条目当前已分享列表
  - 勾选用户 → 分享；已分享用户行内可撤销
-->
<template>
  <n-modal
    :show="show"
    preset="card"
    style="width: 520px"
    :title="`分享「${itemTitle}」`"
    @update:show="(v: boolean) => emit('update:show', v)"
  >
    <n-space vertical size="medium">
      <n-text depth="3">
        被分享的用户只能<strong>查看</strong>该{{ typeLabel }}，不能编辑或删除。仅管理员可分享。
      </n-text>

      <n-form-item label="选择用户" :show-feedback="false">
        <n-select
          v-model:value="selectedUserIds"
          multiple
          filterable
          placeholder="选择一个或多个用户"
          :options="userOptions"
          :loading="loadingUsers"
        />
      </n-form-item>

      <n-button type="primary" :loading="sharing" :disabled="selectedUserIds.length === 0" @click="doShare">
        分享{{ selectedUserIds.length > 0 ? `给 ${selectedUserIds.length} 个用户` : '' }}
      </n-button>

      <n-divider style="margin: 4px 0;">当前已分享（{{ existingShares.length }}）</n-divider>

      <n-empty v-if="existingShares.length === 0" description="尚未分享给任何用户" size="small" />
      <div v-else>
        <!-- 32.4：一键取消该条目的全部分享 -->
        <div class="share-row" style="border-bottom: 1px solid #efeff5; margin-bottom: 4px;">
          <n-text depth="3">共分享给 {{ existingShares.length }} 个用户</n-text>
          <n-popconfirm @positive-click="doRevokeAll">
            <template #trigger>
              <n-button size="tiny" type="error" ghost :loading="revokingAll">
                一键取消所有分享
              </n-button>
            </template>
            将撤销该{{ typeLabel }}对全部 {{ existingShares.length }} 个用户的分享，被分享者立即不可见。确定？
          </n-popconfirm>
        </div>
        <div v-for="s in existingShares" :key="s.id" class="share-row">
          <n-space align="center" size="small">
            <n-icon :component="PersonOutline" />
            <n-text>{{ s.shared_with_username || `用户#${s.shared_with_id}` }}</n-text>
          </n-space>
          <n-button size="tiny" quaternary type="error" :loading="revokingId === s.id" @click="doRevoke(s.id)">
            撤销
          </n-button>
        </div>
      </div>
    </n-space>

    <template #footer>
      <n-space justify="end">
        <n-button @click="emit('update:show', false)">关闭</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NModal, NSpace, NText, NFormItem, NSelect, NButton, NDivider, NEmpty, NIcon, NPopconfirm, useMessage,
} from 'naive-ui'
import { PersonOutline } from '@vicons/ionicons5'
import { shareService, type ShareOut } from '@/services/shares'
import { settingsService } from '@/services/settings'

// 分享目标用户：只用到这几个字段（settingsService.getAllUsers 的 User 与 types/api 的
// User 字段不完全一致，用结构化宽松类型避免 TS 报错）
type ShareUserLite = { id: number; username: string; full_name?: string; is_active?: boolean }

const props = defineProps<{
  show: boolean
  itemType: 'document' | 'asset'
  itemId: number
  itemTitle: string
}>()
const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'changed'): void
}>()

const message = useMessage()
const typeLabel = computed(() => (props.itemType === 'document' ? '文档' : '资产'))

const allUsers = ref<ShareUserLite[]>([])
const loadingUsers = ref(false)
const selectedUserIds = ref<number[]>([])
const existingShares = ref<ShareOut[]>([])
const sharing = ref(false)
const revokingId = ref<number | null>(null)
const revokingAll = ref(false)

const userOptions = computed(() =>
  allUsers.value
    .filter(u => u.is_active)
    .map(u => ({
      label: `${u.username}${u.full_name ? ` (${u.full_name})` : ''}`,
      value: u.id,
    }))
)

const loadAll = async () => {
  loadingUsers.value = true
  try {
    allUsers.value = await settingsService.getAllUsers()
  } catch (e) {
    message.error('加载用户列表失败（仅管理员可分享）')
  } finally {
    loadingUsers.value = false
  }
  try {
    existingShares.value = await shareService.byItem(props.itemType, props.itemId)
    // 已分享的用户默认在多选框里预选（便于追加）
    selectedUserIds.value = existingShares.value.map(s => s.shared_with_id)
  } catch {
    existingShares.value = []
  }
}

watch(() => props.show, (v) => {
  if (v) {
    selectedUserIds.value = []
    existingShares.value = []
    loadAll()
  }
})

const doShare = async () => {
  sharing.value = true
  try {
    for (const uid of selectedUserIds.value) {
      await shareService.share(props.itemType, props.itemId, uid)
    }
    message.success(`已分享给 ${selectedUserIds.value.length} 个用户`)
    await loadAll()
    emit('changed')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '分享失败')
  } finally {
    sharing.value = false
  }
}

// 32.4：一键取消该条目的全部分享
const doRevokeAll = async () => {
  revokingAll.value = true
  try {
    const r = await shareService.revokeAll(props.itemType, props.itemId)
    message.success(r.message || '已取消所有分享')
    await loadAll()
    emit('changed')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '撤销失败')
  } finally {
    revokingAll.value = false
  }
}

const doRevoke = async (shareId: number) => {
  revokingId.value = shareId
  try {
    await shareService.revoke(shareId)
    message.success('已撤销分享')
    await loadAll()
    emit('changed')
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '撤销失败')
  } finally {
    revokingId.value = null
  }
}
</script>

<style scoped>
.share-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 4px;
  border-bottom: 1px solid #efeff5;
}
</style>
