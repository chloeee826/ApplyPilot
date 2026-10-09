import type {
  CandidateProfile,
  CandidateProfileCreate,
  CandidateImportResult,
  CandidateProject,
  CandidateProjectCreate,
  ResumeExtraction,
} from '../types/candidate'
import { parseResponse } from './client'

export async function listProfiles(): Promise<CandidateProfile[]> {
  const response = await fetch('/api/profiles')
  return parseResponse<CandidateProfile[]>(response)
}

export async function createProfile(
  profile: CandidateProfileCreate,
): Promise<CandidateProfile> {
  const response = await fetch('/api/profiles', {
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
  const response = await fetch(`/api/profiles/${profileId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  return parseResponse<CandidateProfile>(response)
}

export async function extractResume(resume: File): Promise<ResumeExtraction> {
  const formData = new FormData()
  formData.append('resume', resume)

  const response = await fetch('/api/resume-extractions', {
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
  const response = await fetch('/api/candidate-imports', {
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
  const response = await fetch(`/api/profiles/${profileId}/projects`)
  return parseResponse<CandidateProject[]>(response)
}

export async function createProject(
  profileId: string,
  project: CandidateProjectCreate,
): Promise<CandidateProject> {
  const response = await fetch(`/api/profiles/${profileId}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  return parseResponse<CandidateProject>(response)
}
