import type {
  CandidateProfile,
  CandidateProfileCreate,
  CandidateProject,
  CandidateProjectCreate,
} from '../types/candidate'
import { parseResponse } from './client'

export async function listProfiles(): Promise<CandidateProfile[]> {
  const response = await fetch('/profiles')
  return parseResponse<CandidateProfile[]>(response)
}

export async function createProfile(
  profile: CandidateProfileCreate,
): Promise<CandidateProfile> {
  const response = await fetch('/profiles', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  })
  return parseResponse<CandidateProfile>(response)
}

export async function listProjects(profileId: string): Promise<CandidateProject[]> {
  const response = await fetch(`/profiles/${profileId}/projects`)
  return parseResponse<CandidateProject[]>(response)
}

export async function createProject(
  profileId: string,
  project: CandidateProjectCreate,
): Promise<CandidateProject> {
  const response = await fetch(`/profiles/${profileId}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(project),
  })
  return parseResponse<CandidateProject>(response)
}
