import type { JobAnalysis } from '../types/jobAnalysis'
import { parseResponse } from './client'

export async function listJobAnalyses(): Promise<JobAnalysis[]> {
  const response = await fetch('/job-analyses')
  return parseResponse<JobAnalysis[]>(response)
}

export async function analyzeJob(jobId: string): Promise<JobAnalysis> {
  const response = await fetch(`/job-analyses/${jobId}`, { method: 'POST' })
  return parseResponse<JobAnalysis>(response)
}
