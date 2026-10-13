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
    const response = await fetch(`${path}?limit=${pageSize}&offset=${offset}`)
    const page = await parseResponse<T[]>(response)
    const previousCount = records.size
    for (const item of page) records.set(item.id, item)
    if (page.length < pageSize) return [...records.values()]
    if (records.size === previousCount) throw new Error('Pagination did not advance. Refresh the workspace.')
  }
}
