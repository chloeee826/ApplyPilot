import type { Application, ApplicationStatus } from '../types/application'
import { parseResponse } from './client'

export async function listApplications(): Promise<Application[]> {
  const response = await fetch('/api/applications')
  return parseResponse<Application[]>(response)
}

export async function updateApplication(
  applicationId: string,
  status: ApplicationStatus,
): Promise<Application> {
  const response = await fetch(`/api/applications/${applicationId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })

  return parseResponse<Application>(response)
}
