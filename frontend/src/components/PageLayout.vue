<template>
  <div class="page-layout">
    <NavigationMenu>
      <n-layout class="page-content">
        <!-- 统一的页面头部 -->
        <n-layout-header bordered class="page-header">
          <n-space justify="space-between" align="center">
            <div class="header-left">
              <n-h2 class="page-title">{{ title }}</n-h2>
            </div>
            <div class="header-right">
              <slot name="header-actions"></slot>
            </div>
          </n-space>
        </n-layout-header>
        
        <!-- 统一的页面内容区域 -->
        <n-layout-content class="page-main">
          <div class="page-container">
            <slot></slot>
          </div>
        </n-layout-content>
      </n-layout>
    </NavigationMenu>
  </div>
</template>

<script setup lang="ts">
import NavigationMenu from './NavigationMenu.vue'
import {
  NLayout,
  NLayoutHeader,
  NLayoutContent,
  NSpace,
  NH2
} from 'naive-ui'

interface Props {
  title: string
}

defineProps<Props>()
</script>

<style scoped>
/* 智慧高速主题色彩 */
:root {
  --runyang-primary: #8B4513;
  --runyang-secondary: #A0522D;
  --runyang-light: #F5F5DC;
  --runyang-accent: #CD853F;
  --runyang-shadow: rgba(139, 69, 19, 0.1);
  --runyang-gradient: linear-gradient(135deg, #F5F5DC 0%, #FAFAFA 100%);
}

.page-layout {
  min-height: 100vh;
  background: linear-gradient(180deg, #FEFEFE 0%, #F8F9FA 100%);
}

.page-content {
  min-height: 100vh;
}

.page-header {
  height: 64px;
  padding: 0 24px;
  background: var(--runyang-gradient);
  box-shadow: 0 2px 8px var(--runyang-shadow);
  border-bottom: 2px solid rgba(139, 69, 19, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.header-left {
  flex: 1;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--runyang-primary);
  letter-spacing: 0.5px;
  position: relative;
}

.page-title::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, var(--runyang-primary) 0%, var(--runyang-accent) 100%);
  border-radius: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-main {
  flex: 1;
  background: linear-gradient(180deg, #FEFEFE 0%, #F8F9FA 100%);
  min-height: calc(100vh - 64px);
  position: relative;
}

.page-main::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, var(--runyang-accent) 50%, transparent 100%);
  opacity: 0.3;
}

.page-container {
  max-width: 100%;
  width: 100%;
  margin: 0;
  padding: 24px;
  box-sizing: border-box;
  position: relative;
}

/* 工匠精神装饰元素 */
.page-container::before {
  content: '';
  position: absolute;
  top: 12px;
  right: 24px;
  width: 40px;
  height: 2px;
  background: linear-gradient(90deg, var(--runyang-primary) 0%, var(--runyang-accent) 100%);
  border-radius: 1px;
  opacity: 0.3;
}

.page-container::after {
  content: '';
  position: absolute;
  top: 20px;
  right: 32px;
  width: 24px;
  height: 2px;
  background: linear-gradient(90deg, var(--runyang-accent) 0%, var(--runyang-secondary) 100%);
  border-radius: 1px;
  opacity: 0.5;
}

/* 全局卡片样式优化 */
:deep(.n-card) {
  border: 1px solid rgba(139, 69, 19, 0.1);
  box-shadow: 0 2px 8px var(--runyang-shadow);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

:deep(.n-card:hover) {
  box-shadow: 0 4px 16px rgba(139, 69, 19, 0.15);
  transform: translateY(-1px);
}

/* 按钮样式优化 */
:deep(.n-button--primary-type) {
  background: linear-gradient(135deg, var(--runyang-primary) 0%, var(--runyang-secondary) 100%);
  border: none;
  box-shadow: 0 2px 4px var(--runyang-shadow);
}

:deep(.n-button--primary-type:hover) {
  background: linear-gradient(135deg, var(--runyang-secondary) 0%, var(--runyang-primary) 100%);
  box-shadow: 0 4px 8px rgba(139, 69, 19, 0.2);
  transform: translateY(-1px);
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .page-container {
    max-width: 100%;
    padding: 20px;
  }
  
  .page-container::before,
  .page-container::after {
    right: 20px;
  }
}

@media (max-width: 768px) {
  .page-container {
    padding: 16px;
  }
  
  .page-header {
    padding: 0 16px;
  }
  
  .page-title {
    font-size: 18px;
  }
  
  .page-container::before,
  .page-container::after {
    right: 16px;
  }
}
</style>