/**
 * XSS防护工具函数
 * 使用DOMPurify进行HTML内容净化
 */
import DOMPurify from 'dompurify'

/**
 * 安全地净化HTML内容，防止XSS攻击
 * @param html - 原始HTML内容
 * @param options - DOMPurify选项
 * @returns 净化后的安全HTML内容
 */
export function sanitizeHtml(
  html: string, 
  options: any = {}
): string {
  if (!html || typeof html !== 'string') {
    return ''
  }

  // 默认配置：保留常用的安全标签和属性
  const defaultConfig: any = {
    ALLOWED_TAGS: [
      'p', 'br', 'div', 'span', 'strong', 'b', 'em', 'i', 'u', 
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 
      'a', 'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'blockquote', 'pre', 'code',
      'mark'  // 用于高亮显示
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'src', 'alt', 
      'class', 'style',
      'target', 'rel'
    ],
    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.-]+(?:[^a-z+.-:]|$))/i,
    // 移除危险的属性和标签
    FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'textarea', 'button'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur'],
    // 保持相对URL
    SANITIZE_DOM: true,
    WHOLE_DOCUMENT: false,
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
    RETURN_TRUSTED_TYPE: false,
    ...options
  }

  try {
    return DOMPurify.sanitize(html, defaultConfig) as string
  } catch (error) {
    console.error('HTML sanitization error:', error)
    // 如果净化失败，返回纯文本（移除所有HTML标签）
    return html.replace(/<[^>]*>/g, '')
  }
}

/**
 * 严格模式：只保留纯文本，移除所有HTML标签
 * @param html - 原始HTML内容
 * @returns 纯文本内容
 */
export function sanitizeToText(html: string): string {
  if (!html || typeof html !== 'string') {
    return ''
  }

  try {
    return DOMPurify.sanitize(html, {
      ALLOWED_TAGS: [],
      ALLOWED_ATTR: [],
      KEEP_CONTENT: true
    })
  } catch (error) {
    console.error('Text sanitization error:', error)
    return html.replace(/<[^>]*>/g, '')
  }
}

/**
 * 用于搜索结果高亮的安全净化
 * @param html - 包含高亮标记的HTML
 * @returns 安全的高亮HTML
 */
export function sanitizeHighlightHtml(html: string): string {
  return sanitizeHtml(html, {
    ALLOWED_TAGS: ['span', 'mark', 'strong', 'b', 'em', 'i', 'br'],
    ALLOWED_ATTR: ['class', 'data-highlight-index'],
    FORBID_TAGS: [],
    FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur', 'style']
  })
}

/**
 * 用于文档预览的安全净化（保留更多格式）
 * @param html - 文档内容HTML
 * @returns 安全的文档HTML
 */
export function sanitizeDocumentHtml(html: string): string {
  return sanitizeHtml(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'div', 'span', 'strong', 'b', 'em', 'i', 'u', 'sub', 'sup',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'dl', 'dt', 'dd',
      'a', 'img',
      'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
      'blockquote', 'pre', 'code', 'kbd', 'samp',
      'mark', 'del', 'ins',
      'hr'
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'src', 'alt', 'width', 'height',
      'class', 'colspan', 'rowspan',
      'target', 'rel'
    ],
    // 确保链接安全
    ADD_ATTR: { 'a': { 'rel': 'noopener noreferrer', 'target': '_blank' } },
    SANITIZE_NAMED_PROPS: true
  })
}

/**
 * Vue组合式函数：提供安全的HTML显示功能
 */
export function useSafeHtml() {
  return {
    sanitizeHtml,
    sanitizeToText,
    sanitizeHighlightHtml,
    sanitizeDocumentHtml
  }
}