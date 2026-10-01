import type { Job, JobCreate } from '../types/job'

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : 'Request failed'
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}

export async function listJobs(): Promise<Job[]> {
  const response = await fetch('/jobs')
  return parseResponse<Job[]>(response)
}

export async function createJob(job: JobCreate): Promise<Job> {
  const response = await fetch('/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(job),
  })

  return parseResponse<Job>(response)
}
