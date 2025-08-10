<template>
  <div class="login-view">
    <n-layout content-style="padding: 0; height: 100vh;">
      <n-grid cols="1 s:1 m:2" responsive="screen" style="height: 100%;">
        <!-- 左侧背景 -->
        <n-grid-item style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center;">
          <n-space vertical align="center" style="text-align: center; color: white;">
            <n-icon :component="ServerOutline" size="120" />
            <n-h1 style="color: white; margin: 0;">润扬大桥运维文档管理系统</n-h1>
            <n-text style="color: rgba(255,255,255,0.8); font-size: 18px;">
              智慧高速，工匠精神 - 专业运维文档管理平台
            </n-text>
          </n-space>
        </n-grid-item>
        
        <!-- 右侧登录表单 -->
        <n-grid-item style="display: flex; align-items: center; justify-content: center; padding: 40px;">
          <n-card style="width: 100%; max-width: 400px;" :bordered="false">
            <template #header>
              <n-space vertical align="center">
                <n-h2 style="margin: 0;">用户登录</n-h2>
                <n-text depth="3">请输入您的登录信息</n-text>
              </n-space>
            </template>
            
            <n-form
              ref="formRef"
              :model="loginForm"
              :rules="rules"
              @submit.prevent="handleLogin"
            >
              <n-form-item path="username" label="用户名">
                <n-input
                  v-model:value="loginForm.username"
                  placeholder="请输入用户名"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <n-icon :component="PersonOutline" />
                  </template>
                </n-input>
              </n-form-item>
              
              <n-form-item path="password" label="密码">
                <n-input
                  v-model:value="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  show-password-on="click"
                  autocomplete="current-password"
                  @keydown.enter="handleLogin"
                >
                  <template #prefix>
                    <n-icon :component="LockClosedOutline" />
                  </template>
                </n-input>
              </n-form-item>
              
              <n-form-item>
                <n-space justify="space-between" style="width: 100%;">
                  <n-checkbox v-model:checked="rememberMe">
                    记住我
                  </n-checkbox>
                  <n-button text type="primary">
                    忘记密码？
                  </n-button>
                </n-space>
              </n-form-item>
              
              <n-form-item>
                <n-button
                  type="primary"
                  size="large"
                  style="width: 100%;"
                  :loading="loading"
                  @click="handleLogin"
                >
                  登录
                </n-button>
              </n-form-item>
              
            </n-form>
          </n-card>
        </n-grid-item>
      </n-grid>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  NLayout,
  NGrid,
  NGridItem,
  NCard,
  NSpace,
  NH1,
  NH2,
  NText,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NCheckbox,
  NIcon,
  useMessage,
  type FormInst
} from 'naive-ui'
import {
  ServerOutline,
  PersonOutline,
  LockClosedOutline
} from '@vicons/ionicons5'
import { authService } from '@/services'

const router = useRouter()
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位字符', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    console.log('开始登录处理...', { username: loginForm.username })
    
    const result = await authService.login({
      username: loginForm.username,
      password: loginForm.password
    })
    
    console.log('登录结果:', result)
    
    // 验证登录结果
    if (result && result.access_token) {
      console.log('Token已设置，检查认证状态:', authService.isAuthenticated())
      console.log('Token内容:', authService.getToken()?.substring(0, 20) + '...')
      
      // 小延迟确保token完全设置
      await new Promise(resolve => setTimeout(resolve, 100))
      
      console.log('准备跳转到文档页面...')
      message.success('登录成功')
      
      // 强制跳转到文档管理页面
      await router.push('/documents')
      console.log('跳转完成，当前路径:', router.currentRoute.value.path)
    } else {
      throw new Error('登录失败，未获取到有效的访问令牌')
    }
    
  } catch (error: any) {
    console.error('登录处理失败:', error)
    
    let errorMessage = '登录失败，请检查用户名和密码'
    
    if (error.message) {
      errorMessage = error.message
    } else if (typeof error === 'string') {
      errorMessage = error
    }
    
    message.error(errorMessage)
  } finally {
    loading.value = false
  }
}

</script>

<style scoped>
.login-view {
  height: 100vh;
  overflow: hidden;
}
</style>