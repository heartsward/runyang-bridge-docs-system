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

/** 取文件名最后一段 + 清理非法字符（防止路径分隔符 / 系统非法字符混入） */
function sanitizeFilename(name: string): string {
  // 去掉目录部分（只保留最后一个 / 或 \ 之后的段）
  const seg = name.replace(/.*[\\/]/, '')
  // 去掉 Windows/常见非法字符，折叠空白
  return seg.replace(/[\\/:*?"<>|\u0000-\u001f]/g, '_').replace(/\s+/g, ' ').trim()
}

function parseFilenameFromDisposition(
  contentDisposition: string | null,
  fallback: string,
  type: DownloadType,
  fileType?: string
): string {
  if (contentDisposition) {
    // 1) RFC 5987 优先：filename*=charset'lang'value（value 为百分号编码，如 utf-8''xxx.xlsx）
    //    旧正则 /filename\*?=['"]?([^'"\r\n]*)/ 在此处只捕获到 charset（"utf-8"），
    //    因为 `''` 双撇号把值截断了 —— 这里用 `charset'lang'value` 三段式精确取值
    const extMatch = contentDisposition.match(/filename\*\s*=\s*([^']+)'[^']*'([^;]+)/i)
    if (extMatch && extMatch[2]) {
      try {
        const decoded = decodeURIComponent(extMatch[2].trim())
        const clean = sanitizeFilename(decoded)
        if (clean) return clean
      } catch {
        /* 解码失败 → 走下面的回退 */
      }
    }
    // 2) 普通 filename="..." 或 filename=...
    const plainMatch = contentDisposition.match(/filename\s*=\s*"?([^";\r\n]+)"?/i)
    if (plainMatch && plainMatch[1]) {
      const clean = sanitizeFilename(plainMatch[1].trim())
      if (clean) return clean
    }
  }
  // 兜底：header 缺失/解析失败时，用后端已知 file_type 纠正扩展名，
  // 避免直接拿标题（可能以日期结尾，如 "xxx2025.12"）当文件名导致扩展名错乱
  // 注意：调用方已保证 fallback 非空（fallbackTitle || `document_${docId}`）
  const base = fallback
  if (type === 'markdown') {
    return base.replace(/\.[^.]+$/, '') + '.md'
  }
  const ext = (fileType || '').trim().toLowerCase()
  if (!ext) return base
  // 标题本身已以正确扩展名结尾则保留，否则补上 .ext
  if (base.toLowerCase().endsWith('.' + ext)) return base
  return base.replace(/\.[^.]+$/, '') + '.' + ext
}

export async function downloadWikiDocument(
  docId: number,
  type: DownloadType = 'original',
  fallbackTitle: string,
  fileType?: string
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
    type,
    fileType
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
