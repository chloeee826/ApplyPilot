export type AgentRunStatus = 'running' | 'completed' | 'failed'

export interface AgentToolTrace {
  name: string
  call_id: string
  arguments: Record<string, unknown>
  output: Record<string, unknown>
}

export interface AgentRunCreate {
  job_id: string
  profile_id: string
  mode?: 'openai' | 'demo'
}

export interface SkillCoverage {
  version: string
  role_title: string
  company_name: string
  candidate_name: string
  supported_count: number
  total_count: number
  percentage: number | null
  supported: NonNullable<AgentRun['matched_skill_evidence']>
  gaps: { skill: string; excerpts: string[] }[]
}

export interface AgentRun {
  id: string
  job_id: string
  profile_id: string
  status: AgentRunStatus
  model: string
  summary: string | null
  matched_skills: string[]
  matched_skill_evidence?: {
    skill: string
    sources: {
      source_type: 'profile' | 'project'
      source_id: string
      source_name: string
      original_skill: string
      description?: string | null
      technologies?: string[]
      highlights?: string[]
    }[]
  }[]
  evidence_ontology_version?: string
  skill_gaps: string[]
  project_evidence: string[]
  interview_focus: string[]
  tool_trace: AgentToolTrace[]
  error: string | null
  created_at: string
  completed_at: string | null
  context_status?: 'unchanged' | 'changed' | 'unavailable'
  changed_sources?: string[]
  skill_coverage?: SkillCoverage | null
}
