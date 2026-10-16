import './assets/main.css'
import './assets/markdown.css'  // 29.1：全局 Markdown 渲染样式（标题/字体/代码块/表格/链接等）

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(naive)

app.mount('#app')
