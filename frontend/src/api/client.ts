export async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : 'Request failed'
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}
