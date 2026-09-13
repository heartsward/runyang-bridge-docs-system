/**
 * Markdown 渲染工具
 *
 * 设计：
 * - 单例 markdown-it 实例（启用 GFM/链接识别）
 * - renderMarkdown(md) → 直接返回 HTML（无 sanitize，仅供受信任源用）
 * - renderDocumentMarkdown(md, options) → render + DOMPurify sanitize（用于后端内容）
 *   - options.highlightKeyword 会在渲染前注入 mark 占位符
 *   - 占位符经 markdown-it 渲染后被替换为真 <mark>（避开 markdown-it 转义）
 */
import MarkdownIt from 'markdown-it'
import { sanitizeDocumentHtml } from './xss-protection'

let _mdInstance: MarkdownIt | null = null

function getMd(): MarkdownIt {
  if (!_mdInstance) {
    _mdInstance = new MarkdownIt({
      linkify: true,
      typographer: true,
      breaks: false,
      html: true,
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

  // sanitize（DOMPurify 接受 colspan/rowspan/<mark>，已在 xss-protection.ts 配置）
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