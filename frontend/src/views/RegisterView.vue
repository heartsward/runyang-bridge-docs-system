<template>
  <div class="register-view">
    <n-layout content-style="padding: 0; height: 100vh;">
      <n-grid cols="1 s:1 m:2" responsive="screen" style="height: 100%;">
        <!-- 左侧背景 -->
        <n-grid-item style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center;">
          <n-space vertical align="center" style="text-align: center; color: white;">
            <n-icon :component="ServerOutline" size="120" />
            <n-h1 style="color: white; margin: 0;">润扬大桥运维文档管理系统</n-h1>
            <n-text style="color: rgba(255,255,255,0.8); font-size: 18px;">
              加入我们，开始高效的文档管理之旅
            </n-text>
          </n-space>
        </n-grid-item>
        
        <!-- 右侧注册表单 -->
        <n-grid-item style="display: flex; align-items: center; justify-content: center; padding: 40px;">
          <n-card style="width: 100%; max-width: 500px;" :bordered="false">
            <template #header>
              <n-space vertical align="center">
                <n-h2 style="margin: 0;">用户注册</n-h2>
                <n-text depth="3">创建您的账户</n-text>
              </n-space>
            </template>
            
            <n-form
              ref="formRef"
              :model="registerForm"
              :rules="rules"
              @submit.prevent="handleRegister"
            >
              <n-grid cols="1 s:2" responsive="screen" :x-gap="12">
                <n-grid-item>
                  <n-form-item path="username" label="用户名">
                    <n-input
                      v-model:value="registerForm.username"
                      placeholder="请输入用户名"
                      clearable
                    />
                  </n-form-item>
                </n-grid-item>
                
                <n-grid-item>
                  <n-form-item path="email" label="邮箱">
                    <n-input
                      v-model:value="registerForm.email"
                      placeholder="请输入邮箱"
                      clearable
                    />
                  </n-form-item>
                </n-grid-item>
              </n-grid>
              
              <n-form-item path="full_name" label="姓名">
                <n-input
                  v-model:value="registerForm.full_name"
                  placeholder="请输入真实姓名"
                  clearable
                />
              </n-form-item>
              
              <n-grid cols="1 s:2" responsive="screen" :x-gap="12">
                <n-grid-item>
                  <n-form-item path="department" label="部门">
                    <n-input
                      v-model:value="registerForm.department"
                      placeholder="请输入部门"
                      clearable
                    />
                  </n-form-item>
                </n-grid-item>
                
                <n-grid-item>
                  <n-form-item path="position" label="职位">
                    <n-input
                      v-model:value="registerForm.position"
                      placeholder="请输入职位"
                      clearable
                    />
                  </n-form-item>
                </n-grid-item>
              </n-grid>
              
              <n-form-item path="phone" label="手机号">
                <n-input
                  v-model:value="registerForm.phone"
                  placeholder="请输入手机号"
                  clearable
                />
              </n-form-item>
              
              <n-form-item path="password" label="密码">
                <n-input
                  v-model:value="registerForm.password"
                  type="password"
                  placeholder="请输入密码（至少6位）"
                  show-password-on="click"
                />
              </n-form-item>
              
              <n-form-item path="confirmPassword" label="确认密码">
                <n-input
                  v-model:value="registerForm.confirmPassword"
                  type="password"
                  placeholder="请再次输入密码"
                  show-password-on="click"
                />
              </n-form-item>
              
              <n-form-item>
                <n-checkbox v-model:checked="agreeTerms">
                  我已阅读并同意
                  <n-button text type="primary">服务条款</n-button>
                  和
                  <n-button text type="primary">隐私政策</n-button>
                </n-checkbox>
              </n-form-item>
              
              <n-form-item>
                <n-button
                  type="primary"
                  size="large"
                  style="width: 100%;"
                  :loading="loading"
                  :disabled="!agreeTerms"
                  @click="handleRegister"
                >
                  注册
                </n-button>
              </n-form-item>
              
              <n-form-item>
                <n-space justify="center" style="width: 100%;">
                  <n-text depth="3">已有账号？</n-text>
                  <n-button text type="primary" @click="goToLogin">
                    立即登录
                  </n-button>
                </n-space>
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
import { ServerOutline } from '@vicons/ionicons5'
import { authService } from '@/services'

const router = useRouter()
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const agreeTerms = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  full_name: '',
  department: '',
  position: '',
  phone: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string) => {
        return value === registerForm.password
      },
      message: '两次输入的密码不一致',
      trigger: 'blur'
    }
  ]
}

const handleRegister = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    await authService.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      full_name: registerForm.full_name,
      department: registerForm.department || undefined,
      position: registerForm.position || undefined,
      phone: registerForm.phone || undefined
    })
    
    message.success('注册成功，请登录')
    router.push('/login')
    
  } catch (error: any) {
    console.error('注册失败:', error)
    message.error(error.detail || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-view {
  height: 100vh;
  overflow: auto;
}
</style>