<script setup lang="ts">
import { RouterView } from 'vue-router'
import { NConfigProvider, zhCN, dateZhCN, NMessageProvider, NDialogProvider } from 'naive-ui'
import { onMounted } from 'vue'

onMounted(() => {
  console.log('App mounted successfully')
})
</script>

<template>
  <NConfigProvider 
    :locale="zhCN"
    :date-locale="dateZhCN"
  >
    <NMessageProvider>
      <NDialogProvider>
        <RouterView />
      </NDialogProvider>
    </NMessageProvider>
  </NConfigProvider>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #f5f5f5;
}

#app {
  height: 100vh;
}
</style>
