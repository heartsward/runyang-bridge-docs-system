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
import markdownItMultimdTable from 'markdown-it-multimd-table'
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

    // 32.14：MultiMarkdown 表格插件——Excel/Word 转 MD 的表格救星：
    // - 连续空单元格自动 colspan 合并（合并单元格/长标题不再拖出一排幽灵空列）
    // - headerless: 无表头表也能解析；multibody: 空行分隔的多段表体保留
    // - rowspan 不开（'^^' 语法与转换产物无关，开了反而可能误判普通空单元格）
    // 兼容垫片：插件 4.2.3 内部用 md.utils.assign，markdown-it 15 已移除该工具（POC 实测崩溃）
    const anyUtils = _mdInstance.utils as unknown as Record<string, unknown>
    if (typeof anyUtils.assign !== 'function') anyUtils.assign = Object.assign
    _mdInstance.use(markdownItMultimdTable, {
      multiline: false,
      rowspan: false,
      headerless: true,
      multibody: true,
      autolabel: false,
    })

    // 32.16：宽表列被压到一字一行——根因是 CSS（CJK 列 min-content=1字），
    // 见 markdown.css 的 th{white-space:nowrap} + 单元格 min-width 修复，此处无需改渲染。

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
 * 32.14：Excel/Word 转 MD 的表格预处理——把行内"连续空单元格"折叠成
 * MultiMarkdown 的 `||` 合并语法，交给 markdown-it-multimd-table 解析为 colspan。
 * 解决合并单元格变 16 列幽灵空列、把有内容的列挤窄的问题（POC 用 wiki/10.md 实测）。
 * 仅处理表格行（首尾都是 |），跳过围栏代码块内部。
 *
 * 32.14.1 修（陈工反馈"留空的格子被并入相邻格，而不是空格占位"）：
 * 只有 **连续空段 ≥ MIN_MERGE_RUN（4）** 才折叠——Excel 合并单元格/整行大标题
 * 的幽灵空列都是长段；数据里真空字段（如经度/纬度两列留空）保持独立占位，
 * 其窄列由 CSS（:empty 压到 ~16px）处理，不再误合并。
 */
const MIN_MERGE_RUN = 4
function preprocessTableEmptyRuns(mdSrc: string): string {
  const lines = mdSrc.split('\n')
  let inFence = false
  return lines.map(line => {
    const t = line.trim()
    if (t.startsWith('```') || t.startsWith('~~~')) { inFence = !inFence; return line }
    if (inFence) return line
    if (!t.startsWith('|') || !t.endsWith('|')) return line
    // 至少 3 列才处理（两列的普通小表没必要动）
    const inner = t.slice(1, -1)
    const cells = inner.split('|')
    if (cells.length < 3) return line
    const parts: string[] = []
    let i = 0
    while (i < cells.length) {
      const cur = cells[i]
      // 连续空段达到阈值才并入当前单元格（||语法）；不足阈值原样占位
      let empties = 0
      while (i + 1 + empties < cells.length && cells[i + 1 + empties].trim() === '') empties++
      if (empties >= MIN_MERGE_RUN) {
        parts.push('|' + cur + '|'.repeat(empties))
        i += 1 + empties
      } else {
        parts.push('|' + cur)
        i += 1
      }
    }
    // 末尾若原行以 | 结束（我们已 slice 掉），补回闭合 |
    const merged = parts.join('')
    return '|' + merged.slice(1) + '|'
  }).join('\n')
}

/**
 * 直接渲染 Markdown 为 HTML（不做 sanitize）
 */
export function renderMarkdown(md: string): string {
  if (!md) return ''
  try {
    return getMd().render(preprocessTableEmptyRuns(md))
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
    // 32.14：同 renderMarkdown——表格空列折叠预处理
    html = getMd().render(preprocessTableEmptyRuns(source))
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
