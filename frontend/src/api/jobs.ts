import type { Job, JobCreate } from '../types/job'
import { parseResponse } from './client'

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
