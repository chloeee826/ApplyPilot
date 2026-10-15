import type {
  CandidateProfile,
  CandidateProfileCreate,
  CandidateImportResult,
  CandidateProject,
  CandidateProjectCreate,
  ResumeExtraction,
} from '../types/candidate'
import { apiFetch, listAllPages, parseResponse } from './client'

export async function listProfiles(): Promise<CandidateProfile[]> {
  return listAllPages<CandidateProfile>('/api/profiles')
}

export async function createProfile(
  profile: CandidateProfileCreate,
): Promise<CandidateProfile> {
  const response = await apiFetch('/api/profiles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  return parseResponse<CandidateProfile>(response)
}

export async function updateProfile(
  profileId: string,
  profile: CandidateProfileCreate,
): Promise<CandidateProfile> {
  const response = await apiFetch(`/api/profiles/${profileId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  return parseResponse<CandidateProfile>(response)
}

export async function extractResume(resume: File): Promise<ResumeExtraction> {
  const formData = new FormData()
  formData.append('resume', resume)

  const response = await apiFetch('/api/resume-extractions', {
    method: 'POST',
    body: formData,
  })
  return parseResponse<ResumeExtraction>(response)
}

export async function saveCandidateImport(
  profile: CandidateProfileCreate,
  projects: CandidateProjectCreate[],
  profileId?: string,
): Promise<CandidateImportResult> {
  const response = await apiFetch('/api/candidate-imports', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      profile_id: profileId ?? null,
      profile,
      projects,
    }),
  })
  return parseResponse<CandidateImportResult>(response)
}

export async function listProjects(profileId: string): Promise<CandidateProject[]> {
  const response = await apiFetch(`/api/profiles/${profileId}/projects`)
  return parseResponse<CandidateProject[]>(response)
}

export async function createProject(
  profileId: string,
  project: CandidateProjectCreate,
): Promise<CandidateProject> {
  const response = await apiFetch(`/api/profiles/${profileId}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  return parseResponse<CandidateProject>(response)
}
