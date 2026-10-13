import type { JobAnalysis } from '../types/jobAnalysis'
import { listAllPages, parseResponse } from './client'

export async function listJobAnalyses(): Promise<JobAnalysis[]> {
  return listAllPages<JobAnalysis>('/api/job-analyses')
}

export async function analyzeJob(jobId: string): Promise<JobAnalysis> {
  const response = await fetch(`/api/job-analyses/${jobId}`, { method: 'POST' })
  return parseResponse<JobAnalysis>(response)
}
