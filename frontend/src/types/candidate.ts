export interface CandidateProfileCreate {
  full_name: string
  headline?: string | null
  summary: string
  skills: string[]
}

export interface CandidateProfile extends CandidateProfileCreate {
  id: string
  created_at: string
}

export interface ResumeExtraction {
  source_filename: string
  parser_version: string
  page_count: number
  character_count: number
  profile: CandidateProfileCreate
  warnings: string[]
}

export interface CandidateProjectCreate {
  name: string
  description: string
  technologies: string[]
  highlights: string[]
}

export interface CandidateProject extends CandidateProjectCreate {
  id: string
  profile_id: string
  created_at: string
}
