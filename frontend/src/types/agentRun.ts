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

export interface AgentRun {
  id: string
  job_id: string
  profile_id: string
  status: AgentRunStatus
  model: string
  summary: string | null
  matched_skills: string[]
  skill_gaps: string[]
  project_evidence: string[]
  interview_focus: string[]
  tool_trace: AgentToolTrace[]
  error: string | null
  created_at: string
  completed_at: string | null
}
