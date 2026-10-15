import type { Job, JobCreate } from '../types/job'
import { apiFetch, listAllPages, parseResponse } from './client'

export async function listJobs(): Promise<Job[]> {
  return listAllPages<Job>('/api/jobs')
}

export async function updateJob(id: string, job: JobCreate): Promise<Job> {
  return parseResponse<Job>(await apiFetch(`/api/jobs/${id}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(job),
  }))
}

export async function createJob(job: JobCreate): Promise<Job> {
  const response = await apiFetch('/api/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(job),
  })

  return parseResponse<Job>(response)
}
