/**
 * 统一文档下载工具
 *
 * 文档管理的三个下载点（预览中下载 / 列表行下载 / 智能搜索结果下载）
 * 全部委托本函数，保证交互与后端调用逻辑完全一致：
 *   - 端点：GET /api/v1/wiki/download/{docId}?type={original|markdown}
 *   - 后端 wiki 端点：type=original 下载原文件；type=markdown 下载 MD 副本
 *     （无 MD 副本时回退到数据库已提取内容）
 *   - 文件名：优先取后端 Content-Disposition；否则按类型兜底
 *
 * 返回实际下载的文件名（成功）。失败时抛 Error（detail 来自后端）。
 */

export type DownloadType = 'original' | 'markdown'

function resolveApiBaseUrl(): string {
  const currentHost = window.location.hostname
  const currentProtocol = window.location.protocol
  const envBaseUrl = (import.meta as any).env?.VITE_API_BASE_URL
  if (envBaseUrl) {
    return envBaseUrl.endsWith('/api/v1') ? envBaseUrl : `${envBaseUrl}/api/v1`
  }
  if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
    return `${currentProtocol}//${currentHost}:8002`
  }
  return 'http://localhost:8002'
}

function parseFilenameFromDisposition(
  contentDisposition: string | null,
  fallback: string,
  type: DownloadType
): string {
  if (contentDisposition) {
    const match = contentDisposition.match(/filename\*?=['"]?([^'"\r\n]*)['"]?/i)
    if (match && match[1]) {
      try {
        return decodeURIComponent(match[1])
      } catch {
        return match[1]
      }
    }
  }
  // 兜底：markdown 强制 .md 扩展名
  if (type === 'markdown' && !fallback.toLowerCase().endsWith('.md')) {
    return fallback.replace(/\.[^.]+$/, '') + '.md'
  }
  return fallback
}

export async function downloadWikiDocument(
  docId: number,
  type: DownloadType = 'original',
  fallbackTitle: string
): Promise<string> {
  const token = localStorage.getItem('access_token')
  const baseUrl = resolveApiBaseUrl()

  const response = await fetch(`${baseUrl}/api/v1/wiki/download/${docId}?type=${type}`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${token}` },
  })

  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const errBody = await response.json()
      if (errBody?.detail) detail = errBody.detail
    } catch {
      /* 忽略 JSON 解析失败，用默认 detail */
    }
    throw new Error(detail)
  }

  const blob = await response.blob()
  const objectUrl = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl

  const filename = parseFilenameFromDisposition(
    response.headers.get('content-disposition'),
    fallbackTitle || `document_${docId}`,
    type
  )
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(objectUrl)

  return filename
}

/**
 * 阶段十八·18.8：带 JWT 拉取 wiki 图片 → 返回 blob URL
 *
 * 图片端点 GET /api/v1/wiki/images/{docId}/{filename} 需要 Authorization 头，
 * <img src> 带不了头，所以前端用 fetch → blob → objectURL 的方式加载。
 * 失败返回 null（调用方保留原 src 或显示占位）。
 */
export async function fetchWikiImageUrl(
  docId: number,
  filename: string
): Promise<string | null> {
  const token = localStorage.getItem('access_token')
  const baseUrl = resolveApiBaseUrl()
  try {
    const response = await fetch(
      `${baseUrl}/api/v1/wiki/images/${docId}/${encodeURIComponent(filename)}`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
    if (!response.ok) return null
    const blob = await response.blob()
    return window.URL.createObjectURL(blob)
  } catch (e) {
    console.warn('[wiki-image] 拉取失败:', filename, e)
    return null
  }
}

/**
 * 阶段十八·18.8：把渲染后 HTML 里 src="images/{docId}/{file}" 的 <img>
 * 批量替换为带 token 的 blob URL。返回 { html, revoke }（revoke 释放 blob）。
 */
export async function hydrateWikiImages(
  html: string,
  docId: number
): Promise<{ html: string; revoke: () => void }> {
  const blobUrls: string[] = []
  if (!html || !html.includes('images/')) {
    return { html, revoke: () => {} }
  }

  // 匹配 src="images/{docId}/{filename}"（仅处理当前文档的图，避免误伤）
  const re = new RegExp(
    `src="(images/${docId}/([A-Za-z0-9._-]+))"`,
    'g'
  )
  const matches = [...html.matchAll(re)]
  if (!matches.length) return { html, revoke: () => {} }

  let out = html
  for (const m of matches) {
    const relPath = m[1] // images/{docId}/{file}
    const filename = relPath.split('/').pop() || ''
    const blobUrl = await fetchWikiImageUrl(docId, filename)
    if (blobUrl) {
      blobUrls.push(blobUrl)
      out = out.split(`src="${relPath}"`).join(`src="${blobUrl}"`)
    }
  }
  return {
    html: out,
    revoke: () => blobUrls.forEach((u) => window.URL.revokeObjectURL(u)),
  }
}
