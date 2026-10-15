import type { Application, ApplicationStatus } from '../types/application'
import { apiFetch, listAllPages, parseResponse } from './client'

export async function listApplications(): Promise<Application[]> {
  return listAllPages<Application>('/api/applications')
}

export async function updateApplication(
  applicationId: string,
  status: ApplicationStatus,
): Promise<Application> {
  const response = await apiFetch(`/api/applications/${applicationId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status }),
  })

  return parseResponse<Application>(response)
}
