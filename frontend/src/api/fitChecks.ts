import { parseResponse } from './client'
import type { AgentRun } from '../types/agentRun'
import type { Application } from '../types/application'
import type { Job, JobCreate } from '../types/job'
import type { JobAnalysis } from '../types/jobAnalysis'

export interface FitCheckResult {
  job: Job
  application: Application
  analysis: JobAnalysis
  report: AgentRun
}

export async function checkFit(requestId: string, profileId: string, job: JobCreate): Promise<FitCheckResult> {
  return parseResponse<FitCheckResult>(await fetch('/api/fit-checks', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ request_id: requestId, profile_id: profileId, job }),
  }))
}
