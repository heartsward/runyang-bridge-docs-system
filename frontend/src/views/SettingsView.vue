<template>
  <PageLayout title="系统设置">
    <!-- 用户管理 - 仅管理员可见 -->
    <n-card v-if="currentUser?.is_superuser" title="用户管理" style="margin-bottom: 24px;">
      <template #header-extra>
        <n-button type="primary" @click="showCreateUserModal = true">
          <template #icon>
            <n-icon :component="PersonAddOutline" />
          </template>
          创建用户
        </n-button>
      </template>
      
      <div v-if="usersLoading" style="text-align: center; padding: 40px;">
        <n-spin size="large" />
        <div style="margin-top: 16px;">
          <n-text depth="3">加载用户列表中...</n-text>
        </div>
      </div>
      
      <div v-else>
        <n-data-table
          :columns="userColumns"
          :data="users"
          :pagination="{ pageSize: 10 }"
          :bordered="false"
        />
      </div>
    </n-card>
    
    <!-- 其他设置项可以在这里添加 -->
    <n-card title="其他设置" style="margin-bottom: 24px;">
      <n-empty description="更多设置功能开发中...">
        <template #icon>
          <n-icon :component="SettingsOutline" size="48" />
        </template>
      </n-empty>
    </n-card>
    
    <!-- 创建用户模态框 -->
    <n-modal v-model:show="showCreateUserModal" preset="dialog" title="创建新用户">
      <n-form :model="newUserForm" label-placement="left" label-width="100px">
        <n-form-item label="用户名" required>
          <n-input v-model:value="newUserForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="邮箱" required>
          <n-input v-model:value="newUserForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="密码" required>
          <n-input v-model:value="newUserForm.password" type="password" placeholder="请输入密码" autocomplete="current-password" />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="newUserForm.full_name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="newUserForm.department" placeholder="请输入部门" />
        </n-form-item>
        <n-form-item label="职位">
          <n-input v-model:value="newUserForm.position" placeholder="请输入职位" />
        </n-form-item>
        <n-form-item label="电话">
          <n-input v-model:value="newUserForm.phone" placeholder="请输入电话" />
        </n-form-item>
        <n-form-item label="管理员权限">
          <n-switch v-model:value="newUserForm.is_superuser" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showCreateUserModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreateUser">创建</n-button>
        </n-space>
      </template>
    </n-modal>
    
    <!-- 编辑用户模态框 -->
    <n-modal v-model:show="showEditUserModal" preset="dialog" title="编辑用户信息">
      <n-form :model="editUserForm" label-placement="left" label-width="100px">
        <n-form-item label="用户名" required>
          <n-input v-model:value="editUserForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="邮箱" required>
          <n-input v-model:value="editUserForm.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="姓名">
          <n-input v-model:value="editUserForm.full_name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="部门">
          <n-input v-model:value="editUserForm.department" placeholder="请输入部门" />
        </n-form-item>
        <n-form-item label="职位">
          <n-input v-model:value="editUserForm.position" placeholder="请输入职位" />
        </n-form-item>
        <n-form-item label="电话">
          <n-input v-model:value="editUserForm.phone" placeholder="请输入电话" />
        </n-form-item>
        <n-form-item label="账户状态">
          <n-switch v-model:value="editUserForm.is_active" />
          <n-text depth="3" style="margin-left: 8px;">
            {{ editUserForm.is_active ? '激活' : '禁用' }}
          </n-text>
        </n-form-item>
        <n-form-item label="管理员权限">
          <n-switch v-model:value="editUserForm.is_superuser" />
        </n-form-item>
        <n-form-item label="修改密码">
          <n-input 
            v-model:value="editUserForm.password" 
            type="password" 
            placeholder="留空表示不修改密码"
            autocomplete="new-password"
          />
          <template #suffix>
            <n-text depth="3" style="font-size: 12px;">
              可选
            </n-text>
          </template>
        </n-form-item>
      </n-form>
      <template #action>
        <n-space>
          <n-button @click="showEditUserModal = false">取消</n-button>
          <n-button type="primary" @click="handleUpdateUser">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </PageLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NCard,
  NForm,
  NFormItem,
  NRadioGroup,
  NRadio,
  NSpace,
  NText,
  NAlert,
  NEmpty,
  NIcon,
  NSpin,
  NButton,
  NDataTable,
  NModal,
  NInput,
  NSwitch,
  NTag,
  NPopconfirm,
  useMessage
} from 'naive-ui'
import { SettingsOutline, PersonAddOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5'
import PageLayout from '@/components/PageLayout.vue'
import { settingsService, authService } from '@/services'
import type { UserSettings, User, UserCreate, UserUpdate } from '@/services/settings'

const message = useMessage()

// 用户管理相关状态
const currentUser = ref<User | null>(null)
const users = ref<User[]>([])
const usersLoading = ref(false)
const showCreateUserModal = ref(false)
const showEditUserModal = ref(false)
const editingUser = ref<User | null>(null)

// 新用户表单
const newUserForm = ref<UserCreate>({
  username: '',
  email: '',
  password: '',
  full_name: '',
  department: '',
  position: '',
  phone: '',
  is_superuser: false
})

// 编辑用户表单
const editUserForm = ref<UserUpdate>({
  username: '',
  email: '',
  full_name: '',
  department: '',
  position: '',
  phone: '',
  is_active: true,
  is_superuser: false,
  password: ''  // 添加密码字段
})

const rules = {}

// 用户表格列定义
const userColumns = [
  {
    title: '用户名',
    key: 'username',
    width: 120
  },
  {
    title: '邮箱',
    key: 'email',
    width: 200
  },
  {
    title: '姓名',
    key: 'full_name',
    width: 120
  },
  {
    title: '部门',
    key: 'department',
    width: 120
  },
  {
    title: '职位',
    key: 'position',
    width: 120
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row: User) => {
      return h(NTag, {
        type: row.is_active ? 'success' : 'error'
      }, {
        default: () => row.is_active ? '激活' : '禁用'
      })
    }
  },
  {
    title: '权限',
    key: 'is_superuser',
    width: 80,
    render: (row: User) => {
      return h(NTag, {
        type: row.is_superuser ? 'warning' : 'default'
      }, {
        default: () => row.is_superuser ? '管理员' : '普通用户'
      })
    }
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row: User) => {
      return h(NSpace, {}, {
        default: () => [
          h(NButton, {
            size: 'small',
            type: 'primary',
            ghost: true,
            onClick: () => handleEditUser(row)
          }, {
            default: () => '编辑',
            icon: () => h(NIcon, { component: CreateOutline })
          }),
          row.is_superuser ? null : h(NPopconfirm, {
            onPositiveClick: () => handleDeleteUser(row)
          }, {
            trigger: () => h(NButton, {
              size: 'small',
              type: 'error',
              ghost: true
            }, {
              default: () => '删除',
              icon: () => h(NIcon, { component: TrashOutline })
            }),
            default: () => '确定删除此用户吗？'
          })
        ].filter(Boolean)
      })
    }
  }
]


// 获取当前用户信息
const loadCurrentUser = async () => {
  try {
    currentUser.value = await authService.getCurrentUser()
  } catch (error) {
    console.error('获取当前用户信息失败:', error)
  }
}

// 加载所有用户
const loadUsers = async () => {
  if (!currentUser.value?.is_superuser) return
  
  try {
    usersLoading.value = true
    users.value = await settingsService.getAllUsers()
  } catch (error: any) {
    console.error('获取用户列表失败:', error)
    message.error('获取用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

// 创建新用户
const handleCreateUser = async () => {
  try {
    await settingsService.createUser(newUserForm.value)
    message.success('用户创建成功')
    showCreateUserModal.value = false
    // 重置表单
    newUserForm.value = {
      username: '',
      email: '',
      password: '',
      full_name: '',
      department: '',
      position: '',
      phone: '',
      is_superuser: false
    }
    // 重新加载用户列表
    loadUsers()
  } catch (error: any) {
    console.error('创建用户失败:', error)
    message.error(error.response?.data?.detail || '创建用户失败')
  }
}

// 编辑用户
const handleEditUser = (user: User) => {
  editingUser.value = user
  editUserForm.value = {
    username: user.username,
    email: user.email,
    full_name: user.full_name || '',
    department: user.department || '',
    position: user.position || '',
    phone: user.phone || '',
    is_active: user.is_active,
    is_superuser: user.is_superuser,
    password: ''  // 密码字段初始为空
  }
  showEditUserModal.value = true
}

// 更新用户信息
const handleUpdateUser = async () => {
  if (!editingUser.value) return
  
  try {
    await settingsService.updateUser(editingUser.value.id, editUserForm.value)
    message.success('用户信息更新成功')
    showEditUserModal.value = false
    editingUser.value = null
    // 重新加载用户列表
    loadUsers()
  } catch (error: any) {
    console.error('更新用户失败:', error)
    message.error(error.response?.data?.detail || '更新用户失败')
  }
}

// 删除用户
const handleDeleteUser = async (user: User) => {
  if (user.is_superuser) {
    message.error('不能删除管理员账户')
    return
  }
  
  try {
    await settingsService.deleteUser(user.id)
    message.success('用户删除成功')
    // 重新加载用户列表
    loadUsers()
  } catch (error: any) {
    console.error('删除用户失败:', error)
    message.error(error.response?.data?.detail || '删除用户失败')
  }
}

onMounted(() => {
  loadCurrentUser().then(() => {
    if (currentUser.value?.is_superuser) {
      loadUsers()
    }
  })
})
</script>

<style scoped>
:deep(.n-radio) {
  margin-bottom: 16px;
}

:deep(.n-radio .n-radio__label) {
  padding-left: 12px;
}

/* 确保创建用户按钮的可见性 */
:deep(.n-button.n-button--primary-type) {
  background-color: #18a058 !important;
  color: white !important;
  border-color: #18a058 !important;
}

:deep(.n-button.n-button--primary-type:hover) {
  background-color: #36ad6a !important;
  border-color: #36ad6a !important;
}

:deep(.n-button.n-button--primary-type:active) {
  background-color: #0c7a43 !important;
  border-color: #0c7a43 !important;
}

/* 确保模态框中的按钮也有正确的样式 */
:deep(.n-modal .n-button.n-button--primary-type) {
  background-color: #18a058 !important;
  color: white !important;
  border-color: #18a058 !important;
}
</style>