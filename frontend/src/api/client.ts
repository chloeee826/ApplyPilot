export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers)
  if (!['GET', 'HEAD', 'OPTIONS'].includes(options.method?.toUpperCase() ?? 'GET')) {
    headers.set('X-ApplyPilot-Request', '1')
  }
  const response = await fetch(path, { ...options, headers, credentials: 'same-origin' })
  if (response.status === 401 && !path.startsWith('/api/auth/')) {
    window.dispatchEvent(new Event('applypilot-session-expired'))
  }
  return response
}

export async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail =
      typeof body?.detail === 'string'
        ? body.detail
        : typeof body?.detail?.message === 'string'
          ? body.detail.message
          : 'Request failed'
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}

// A personal workspace keeps shared data in memory, but never silently truncates
// it to the API's first page. The server bounds each individual request to 100.
export async function listAllPages<T extends { id: string }>(path: string): Promise<T[]> {
  const records = new Map<string, T>()
  const pageSize = 100
  for (let offset = 0; ; offset += pageSize) {
    const response = await apiFetch(`${path}?limit=${pageSize}&offset=${offset}`)
    const page = await parseResponse<T[]>(response)
    const previousCount = records.size
    for (const item of page) records.set(item.id, item)
    if (page.length < pageSize) return [...records.values()]
    if (records.size === previousCount) throw new Error('Pagination did not advance. Refresh the workspace.')
  }
}
