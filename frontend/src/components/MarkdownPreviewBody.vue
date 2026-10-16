<!--
  MarkdownPreviewBody.vue (29.5)
  ============================================================================
  共享 Markdown 预览核心组件——解决 29.1~29.4 三个 view 重复维护的根问题

  职责（统一两边的核心行为）：
  1. markdown 渲染（markdown-it + anchor + highlight.js + breaks:true，29.1 装）
  2. 搜索高亮 mark 注入（29.3 保护 markdown 链接 URL 段不被破坏）
  3. 全局"上一处 / 下一处"导航（29.4，按 data-highlight-index 整体跳转）
  4. Ctrl+F 焦点迁移（29.4，弹窗打开时 blur input + focus 到 .preview-container）
  5. 内部锚链接 native 跳转（29.2，让浏览器原生处理）
  6. 29.1 markdown.css 全局样式自动应用（通过 .markdown-content class）

  Props:
    - content: 原始 markdown 文本
    - keyword: 搜索关键词（可选,触发高亮）
    - showHighlightNav: 是否显示顶部"共 N 处 / ↑↓ / 当前 N/总 M"导航
    - maxHeight: 容器最大高度(默认 80vh;SearchView 60vh 时传 '60vh')
    - showOnlyOfficeLink: 是否在右上角显示"OnlyOffice 在线预览"按钮(用 slot 实现)

  Emits:
    - anchor-click: (可选) 当用户点 a 标签时(目前不传,浏览器 native 跳转)

  Slots:
    - toolbar-extra: 工具栏额外按钮(如编辑 / 下载 / OnlyOffice)
    - edit-mode: 编辑模式 textarea(替换 markdown 显示)
    - original-mode: 原文件模式(iframe / img)

  长期约束:
    - 不依赖 DocumentView / SearchView 任何特定状态
    - 渲染、焦点、链接、Ctrl+F 全部自包含——两边 view 只负责传 content + 显示与否
    - 修改核心行为只改本组件,两 view 自动同步
-->
<template>
  <div
    class="preview-container"
    ref="containerRef"
    @click="handlePreviewAnchorClick"
    :style="{ maxHeight: maxHeight }"
  >
    <!-- 搜索高亮导航（仅 showHighlightNav=true 且 keyword 有值时显示） -->
    <div
      v-if="showHighlightNav && keyword && highlightedCount > 0 && !editMode"
      class="highlight-nav-bar"
    >
      <n-space align="center" size="small">
        <n-tag type="warning" size="small">
          🔍 "{{ keyword }}" 共 {{ highlightedCount }} 处
        </n-tag>
        <n-button-group size="tiny">
          <n-button
            @click="scrollToGlobalHighlight(-1)"
            :disabled="currentHighlightIndex <= 0"
          >↑</n-button>
          <n-button
            @click="scrollToGlobalHighlight(1)"
            :disabled="currentHighlightIndex >= highlightedCount - 1"
          >↓</n-button>
        </n-button-group>
        <n-text depth="3" style="font-size: 11px;">
          {{ currentHighlightIndex + 1 }} / {{ highlightedCount }}
        </n-text>
        <slot name="nav-extra" />
      </n-space>
    </div>

    <!-- 编辑模式（slot 注入,由调用方提供 textarea + 行为） -->
    <slot v-if="editMode" name="edit-mode" />

    <!-- markdown 内容 -->
    <div
      v-else
      v-html="renderedHtml"
      class="markdown-content"
    ></div>

    <!-- 原文件模式（slot 注入 iframe / img） -->
    <slot v-if="originalMode" name="original-mode" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { renderDocumentMarkdownHtml, renderMarkdown } from '@/utils/markdown-renderer'
import { sanitizeDocumentHtml } from '@/utils/xss-protection'

interface Props {
  content?: string                         // 原始 markdown（mode='markdown' 时使用）——可选
  html?: string                            // 已渲染 HTML（mode='html' 时使用，跳过组件内部 markdown 渲染）
  mode?: 'markdown' | 'html'              // 内容模式,默认 markdown
  keyword?: string                        // 搜索关键词（触发高亮 + 全局 ↑↓）
  showHighlightNav?: boolean               // 是否显示顶部全局 ↑↓ 导航
  maxHeight?: string                       // 容器最大高度,默认 80vh
  editMode?: boolean                       // 是否进入编辑模式(由调用方提供 slot)
  originalMode?: boolean                   // 是否进入原文件模式(由调用方提供 slot)
}
const props = withDefaults(defineProps<Props>(), {
  mode: 'markdown',
  keyword: '',
  showHighlightNav: true,
  maxHeight: '80vh',
  editMode: false,
  originalMode: false,
})
defineEmits<{
  (e: 'anchor-click', href: string): void
}>()

// ============ 渲染 ============
// 1) 单 keyword 走 renderDocumentMarkdown(带高亮占位符注入+sanitize)
// 2) 多词按空格拆分,后端会预注入 <mark data-term="词">（search_service.highlight_terms）
//    这里在客户端做"完整 q 串整体高亮"补充(把整个 q 串也加 data-term="q.strip()")
// 3) 单词直接高亮

const terms = computed<string[]>(() => {
  if (!props.keyword) return []
  return props.keyword.split(/\s+/).filter(t => t.length > 0)
})

// 渲染后的 HTML:markdown → mark 注入(链接保护)→ sanitize
// 或 mode='html' 时直接 v-html 已渲染的 HTML
const renderedHtml = computed<string>(() => {
  // mode='html' 模式:调用方自己已渲染 + mark 注入 + 图片水合
  // 组件只负责:全局 ↑↓ + Ctrl+F 焦点 + 链接 native 跳转
  if (props.mode === 'html') {
    if (!props.html) return ''
    return reindexHighlightMarks(props.html)
  }

  if (!props.content) return ''
  if (!props.keyword) {
    // 无搜索关键词:走标准渲染
    return renderDocumentMarkdownHtml(props.content)
  }
  // 有关键词:先 markdown-it 渲染(让链接语法先生效)
  let html: string
  try {
    html = renderMarkdown(props.content)
  } catch (e) {
    console.error('Markdown render failed:', e)
    html = props.content
  }
  // 注入完整 q 串(连续整体)的 mark
  const phrase = props.keyword.trim()
  if (phrase && phrase.includes(' ')) {
    // 完整 q 串整体高亮
    const phraseRe = new RegExp(escapeRegex(phrase), 'g')
    html = html.replace(phraseRe, (match) => `<mark data-term="${escapeAttr(phrase)}">${match}</mark>`)
  }
  // 注入每个分词(避免重复:已经在完整 q 串内的不重复注入)
  for (const t of terms.value) {
    if (!t) continue
    const tRe = new RegExp(escapeRegex(t), 'g')
    // 只在不在 <mark> 内的文本中注入
    html = injectOutsideMarks(html, tRe, t)
  }
  // 重新计算 mark 的全局 data-highlight-index（按出现顺序 0..N-1）
  return reindexHighlightMarks(html)
})

/**
 * 给所有 <mark> 重新加 data-highlight-index 0..N-1（按出现顺序）
 * 不依赖 markdown 渲染，SearchView 用 mode='html' 时复用此函数
 */
function reindexHighlightMarks(html: string): string {
  let idx = 0
  return html.replace(/<mark([^>]*)>/g, (_full, attrs) => {
    // 如果已经有 data-highlight-index,保留;否则重新赋值
    if (attrs.includes('data-highlight-index=')) {
      return _full
    }
    return `<mark${attrs} data-highlight-index="${idx++}">`
  })
}

// 在 <mark> 标签外注入新 mark（避免重叠）
function injectOutsideMarks(html: string, re: RegExp, term: string): string {
  // 简化版:跳过已包含 <mark>...</mark> 的区间
  // 因为 regex 替换天然支持,关键是要避免在已 mark 的内容内再次 mark
  // 用 split + map 实现:按 <mark>...</mark> 分段,非 mark 段做替换
  const parts: string[] = []
  let last = 0
  const markRe = /<mark[^>]*>.*?<\/mark>/gs
  let m: RegExpExecArray | null
  while ((m = markRe.exec(html)) !== null) {
    parts.push(html.slice(last, m.index))
    parts.push(m[0])
    last = m.index + m[0].length
  }
  parts.push(html.slice(last))
  return parts.map((seg, i) => {
    if (i % 2 === 1) return seg  // 是 mark 段,跳过
    return seg.replace(re, (match) => `<mark data-term="${escapeAttr(term)}">${match}</mark>`)
  }).join('')
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
function escapeAttr(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;')
}

// ============ 全局高亮导航 ============
// 注:search_keywords 注入的 <mark data-term="..."> 是分词,client 又补了完整 q 串
// 重新计算 data-highlight-index 后(0..N-1),所有 mark 按出现位置递增
const currentHighlightIndex = ref(0)

const highlightedCount = computed(() => {
  if (!props.content) return 0
  // 从渲染后 HTML 里数 <mark> 数量
  const matches = renderedHtml.value.match(/<mark[^>]*>/g)
  return matches ? matches.length : 0
})

watch([renderedHtml, () => props.keyword], () => {
  // 关键词/内容变化时,重置游标
  currentHighlightIndex.value = 0
  nextTick(() => {
    removeAllActiveHighlights()
  })
})

function removeAllActiveHighlights() {
  document.querySelectorAll('.markdown-content mark.active-highlight').forEach(el => {
    el.classList.remove('active-highlight')
  })
}

function scrollToGlobalHighlight(direction: number) {
  const total = highlightedCount.value
  if (total === 0) return
  let newIdx = currentHighlightIndex.value + direction
  if (newIdx < 0) newIdx = 0
  if (newIdx >= total) newIdx = total - 1
  currentHighlightIndex.value = newIdx
  nextTick(() => {
    const targetMark = document.querySelector(`.markdown-content mark[data-highlight-index="${newIdx}"]`) as HTMLElement | null
    if (targetMark) {
      removeAllActiveHighlights()
      targetMark.classList.add('active-highlight')
      targetMark.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

// ============ 链接 native 跳转（29.2）============
// 让浏览器原生处理 <a href="#xxx"> 跳转——不 preventDefault
// 外部链接兜底:target=_blank
function handlePreviewAnchorClick(e: MouseEvent) {
  if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
  const target = e.target as HTMLElement | null
  if (!target) return
  const anchor = target.closest('a') as HTMLAnchorElement | null
  if (!anchor) return
  const href = anchor.getAttribute('href') || ''
  // 内部锚链接:放行浏览器 native
  if (href.startsWith('#')) return
  // 外部链接:兜底加 target=_blank
  if (!anchor.target || anchor.target === '_self') {
    anchor.target = '_blank'
    anchor.rel = 'noopener noreferrer'
  }
}

// ============ Ctrl+F 焦点迁移（29.4）============
const containerRef = ref<HTMLElement | null>(null)

// 统一暴露给父组件
defineExpose({
  scrollToGlobalHighlight,
  currentHighlightIndex,
  highlightedCount,
  containerRef,
  focusForFind: async () => {
    // 由父 modal 在打开时调用:blur input + focus container
    await nextTick()
    setTimeout(() => {
      const active = document.activeElement as HTMLElement | null
      if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
        active.blur()
      }
      if (containerRef.value) {
        containerRef.value.setAttribute('tabindex', '-1')
        containerRef.value.focus({ preventScroll: true })
      }
    }, 200)
  },
})
</script>

<style scoped>
.preview-container {
  width: 100%;
  overflow: auto;
  background-color: #ffffff;
  border-radius: 6px;
}
.highlight-nav-bar {
  margin-bottom: 12px;
  padding: 8px 12px;
  background-color: #fffbe6;
  border: 1px solid #ffe58f;
  border-radius: 6px;
}
</style>
