import type { AgentRun, AgentRunCreate } from '../types/agentRun'
import { parseResponse } from './client'

export async function listAgentRuns(): Promise<AgentRun[]> {
  const response = await fetch('/agent-runs')
  return parseResponse<AgentRun[]>(response)
}

export async function createAgentRun(request: AgentRunCreate): Promise<AgentRun> {
  const response = await fetch('/agent-runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return parseResponse<AgentRun>(response)
}
