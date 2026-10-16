/**
 * Markdown 渲染工具（29.1：装 anchor + highlight 插件 + breaks:true）
 *
 * 设计：
 * - 单例 markdown-it 实例
 * - 装 markdown-it-anchor → heading 自动加 id（支撑 [text](#anchor) 锚链接）
 * - 装 highlight.js → 代码块语法高亮（GitHub Dark 精简主题见 assets/markdown.css）
 * - breaks:true → md 源里单换行变 <br>（修"特殊字符忽大忽小"——硬回车不被合并）
 * - renderMarkdown(md) → 直接返回 HTML（无 sanitize，仅供受信任源用）
 * - renderDocumentMarkdown(md, options) → render + DOMPurify sanitize（用于后端内容）
 *   - options.highlightKeyword 会在渲染前注入 mark 占位符
 *   - 占位符经 markdown-it 渲染后被替换为真 <mark>（避开 markdown-it 转义）
 */
import MarkdownIt from 'markdown-it'
import markdownItAnchor from 'markdown-it-anchor'
import hljs from 'highlight.js'
import { sanitizeDocumentHtml } from './xss-protection'

let _mdInstance: MarkdownIt | null = null

function getMd(): MarkdownIt {
  if (!_mdInstance) {
    _mdInstance = new MarkdownIt({
      linkify: true,
      // 29.1：false → true 让 md 源里的单换行变 <br>，与 IDE/编辑器直观一致
      // 修"特殊字符忽大忽小"——之前单换行被合并成空格，导致硬回车/缩进丢失
      breaks: true,
      typographer: false,  // 关闭 typographer 避免对中文破折号/引号做自动替换干扰阅读
      html: true,
      // 29.1：装 highlight.js 处理 ```lang 代码块；未指定 lang 时原样透传
      highlight: (str: string, lang: string): string => {
        if (lang && hljs.getLanguage(lang)) {
          try {
            const result = hljs.highlight(str, { language: lang, ignoreIllegals: true })
            return `<pre class="hljs"><code class="language-${lang}">${result.value}</code></pre>`
          } catch {
            // 高亮失败时降级为普通 <pre><code>
          }
        }
        // 无 lang 或语言不支持 → 转义后包裹（防止 XSS 注入）
        return `<pre class="hljs"><code>${_mdInstance!.utils.escapeHtml(str)}</code></pre>`
      },
    })

    // 29.1：装 anchor 插件 → 自动给 heading 加 id（[text](#anchor) 跳转锚点的前提）
    // 默认 slugify 已够用（中文用 pinyin 或去特殊字符；GitHub 风格）
    _mdInstance.use(markdownItAnchor, {
      // 自定义 slugify：保留中文、英文、数字、连字符（适合中文文档）
      slugify: (s: string): string => {
        return s
          .trim()
          .toLowerCase()
          // 去标点（保留中文、英文、数字、空格、连字符）
          .replace(/[^\u4e00-\u9fa5a-z0-9\s-]/gi, '')
          // 空白转连字符
          .replace(/\s+/g, '-')
          // 去重连续连字符
          .replace(/-+/g, '-')
          // 去首尾连字符
          .replace(/^-+|-+$/g, '')
          // 截断避免过长
          .slice(0, 64)
      },
    })
  }
  return _mdInstance
}

/** 占位符前缀（避开 markdown-it 转义，因为是控制字符+ASCII） */
const HIGHLIGHT_PLACEHOLDER_PREFIX = '\u0091H_'

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 在 Markdown 源中注入高亮占位符
 * 占位符格式：\u0091H_<index>_<keyword>\u0091
 */
function injectHighlightPlaceholders(md: string, keyword: string): { text: string; count: number } {
  if (!keyword) return { text: md, count: 0 }
  const regex = new RegExp(`(${escapeRegex(keyword)})`, 'gi')
  let count = 0
  const text = md.replace(regex, (match) => {
    const placeholder = `${HIGHLIGHT_PLACEHOLDER_PREFIX}${count}${HIGHLIGHT_PLACEHOLDER_PREFIX === '\u0091H_' ? match : match}`
    count++
    return placeholder
  })
  return { text, count }
}

/**
 * 渲染后把占位符替换为真 <mark> 标签
 */
function placeholdersToMark(html: string): string {
  // 占位符经 markdown-it 渲染后会变成纯文本（H_0_, H_1_...）
  // 这里替换为 <mark data-highlight-index="N">
  return html.replace(/H_(\d+)_/g, (_, idx) => `<mark data-highlight-index="${idx}">`)
}

/**
 * 直接渲染 Markdown 为 HTML（不做 sanitize）
 */
export function renderMarkdown(md: string): string {
  if (!md) return ''
  try {
    return getMd().render(md)
  } catch (e) {
    console.error('Markdown render failed:', e)
    return md
  }
}

/**
 * 渲染文档内容：可选高亮注入 → render → 占位符替换 → sanitize
 *
 * @param md Markdown 源
 * @param options.highlightKeyword 关键词（可选，注入高亮）
 */
export function renderDocumentMarkdown(
  md: string,
  options: { highlightKeyword?: string } = {},
): { html: string; highlightCount: number } {
  if (!md) return { html: '', highlightCount: 0 }

  let source = md
  let highlightCount = 0

  if (options.highlightKeyword) {
    const injected = injectHighlightPlaceholders(source, options.highlightKeyword)
    source = injected.text
    highlightCount = injected.count
  }

  let html: string
  try {
    html = getMd().render(source)
  } catch (e) {
    console.error('Markdown render failed:', e)
    html = source
  }

  // 占位符 → 真 <mark>
  if (highlightCount > 0) {
    html = placeholdersToMark(html)
  }

  // sanitize（DOMPurify 接受 colspan/rowspan/<mark>/<span class hljs-*>/data-*/id，详见 xss-protection.ts）
  const sanitized = sanitizeDocumentHtml(html)
  return { html: sanitized, highlightCount }
}

/** 仅 HTML 输出（无 metadata），保留向后兼容 */
export function renderDocumentMarkdownHtml(md: string): string {
  return renderDocumentMarkdown(md).html
}

/** 调试用：返回 markdown-it 实例 */
export function _getMarkdownIt() {
  return getMd()
}
