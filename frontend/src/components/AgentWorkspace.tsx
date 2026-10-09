import { useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'

import { createAgentRun, listAgentRuns } from '../api/agentRuns'
import type { AgentRun } from '../types/agentRun'
import type { CandidateProfile } from '../types/candidate'
import type { Job } from '../types/job'
import type { JobAnalysis } from '../types/jobAnalysis'

interface AgentWorkspaceProps {
  jobs: Job[]
  analyses: JobAnalysis[]
  profiles: CandidateProfile[]
  runs: AgentRun[]
  isLoading: boolean
  onRunsChange: (runs: AgentRun[]) => void
}

interface ResultListProps {
  emptyMessage: string
  items: string[]
  title: string
  tone?: 'positive' | 'gap'
}

function ResultList({ emptyMessage, items, title, tone }: ResultListProps) {
  return (
    <section className={`agent-result-group ${tone ? `result-${tone}` : ''}`}>
      <h4>{title}</h4>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>{emptyMessage}</p>
      )}
    </section>
  )
}

export function AgentWorkspace({
  jobs,
  analyses,
  profiles,
  runs,
  isLoading,
  onRunsChange,
}: AgentWorkspaceProps) {
  const [selectedJobId, setSelectedJobId] = useState('')
  const [selectedProfileId, setSelectedProfileId] = useState('')
  const [executionMode, setExecutionMode] = useState<'demo' | 'openai'>('demo')
  const [activeRunId, setActiveRunId] = useState<string | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const effectiveJobId = selectedJobId || jobs[0]?.id || ''
  const effectiveProfileId = selectedProfileId || profiles[0]?.id || ''
  const selectedAnalysis = analyses.find(
    (analysis) => analysis.job_id === effectiveJobId,
  )
  const activeRun = useMemo(
    () => runs.find((run) => run.id === activeRunId) ?? runs[0] ?? null,
    [activeRunId, runs],
  )

  async function handleRun(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!effectiveJobId || !effectiveProfileId || !selectedAnalysis) return

    setIsRunning(true)
    setError(null)

    try {
      const savedRun = await createAgentRun({
        job_id: effectiveJobId,
        profile_id: effectiveProfileId,
        mode: executionMode,
      })
      onRunsChange([savedRun, ...runs])
      setActiveRunId(savedRun.id)
    } catch (runError) {
      setError(
        runError instanceof Error ? runError.message : 'Could not complete agent run',
      )
      try {
        const savedRuns = await listAgentRuns()
        onRunsChange(savedRuns)
        setActiveRunId(savedRuns[0]?.id ?? null)
      } catch {
        // Keep the original agent error visible if refreshing failed runs also fails.
      }
    } finally {
      setIsRunning(false)
    }
  }

  const canRun = Boolean(
    effectiveJobId && effectiveProfileId && selectedAnalysis && !isRunning,
  )

  return (
    <section className="agent-panel" aria-labelledby="agent-workspace-heading">
      <div className="section-heading agent-section-heading">
        <div>
          <p className="step-label">04 · Generate a recommendation</p>
          <h2 id="agent-workspace-heading">Job-match agent</h2>
          <p>
            The workflow retrieves saved evidence through controlled tools before it
            recommends what to emphasize and prepare.
          </p>
        </div>
        <span className="agent-run-count">
          {runs.length} {runs.length === 1 ? 'run' : 'runs'}
        </span>
      </div>

      <div className="agent-layout">
        <form className="agent-controls" onSubmit={handleRun}>
          <label>
            Target job
            <select
              value={effectiveJobId}
              onChange={(event) => setSelectedJobId(event.target.value)}
              disabled={jobs.length === 0}
            >
              {jobs.length === 0 && <option value="">No saved jobs</option>}
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.company_name} · {job.title}
                </option>
              ))}
            </select>
          </label>

          <label>
            Candidate profile
            <select
              value={effectiveProfileId}
              onChange={(event) => setSelectedProfileId(event.target.value)}
              disabled={profiles.length === 0}
            >
              {profiles.length === 0 && <option value="">No candidate profile</option>}
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.full_name}
                  {profile.headline ? ` · ${profile.headline}` : ''}
                </option>
              ))}
            </select>
          </label>

          <label>
            Execution mode
            <select
              value={executionMode}
              onChange={(event) =>
                setExecutionMode(event.target.value as 'demo' | 'openai')
              }
            >
              <option value="demo">Deterministic demo</option>
              <option value="openai">OpenAI agent</option>
            </select>
          </label>

          <div className="agent-readiness" aria-live="polite">
            <span className={selectedAnalysis ? 'ready' : 'missing'}>
              {selectedAnalysis ? 'Analysis ready' : 'Analyze this job first'}
            </span>
            <span className={effectiveProfileId ? 'ready' : 'missing'}>
              {effectiveProfileId ? 'Profile ready' : 'Create a profile first'}
            </span>
          </div>

          <button className="primary-button" type="submit" disabled={!canRun}>
            {isRunning ? 'Running agent…' : 'Run job-match agent'}
          </button>

          {executionMode === 'demo' ? (
            <p className="agent-note">
              Demo mode calls the same four evidence tools and persists the run, but
              uses deterministic matching instead of an LLM.
            </p>
          ) : (
            <p className="agent-note">
              OpenAI mode requires <code>OPENAI_API_KEY</code>. Failed runs are saved
              for debugging instead of being replaced with fake AI results.
            </p>
          )}
        </form>

        <div className="agent-output" aria-live="polite">
          {error && <p className="error-message agent-error">{error}</p>}
          {isLoading && <p className="empty-state">Loading agent history…</p>}
          {!isLoading && !activeRun && (
            <div className="empty-state">
              <p>No agent recommendations yet.</p>
              {profiles.length === 0 ? (
                <span>
                  Start by <Link to="/candidate">creating candidate evidence</Link>.
                </span>
              ) : jobs.length === 0 ? (
                <span>
                  Continue by <Link to="/jobs">saving a target job</Link>.
                </span>
              ) : !selectedAnalysis ? (
                <span>
                  <Link to="/jobs">Analyze the selected job</Link> before running the agent.
                </span>
              ) : (
                <span>Your evidence is ready. Start the first run.</span>
              )}
            </div>
          )}

          {activeRun && (
            <article className="agent-result-card">
              <div className="agent-result-heading">
                <div>
                  <p className="agent-result-label">
                    {activeRun.model === 'demo-evidence-v1'
                      ? 'Deterministic demo result'
                      : 'Latest selected run'}
                  </p>
                  <h3>{activeRun.status === 'completed' ? 'Recommendation' : 'Run details'}</h3>
                </div>
                <span className={`run-status run-status-${activeRun.status}`}>
                  {activeRun.status}
                </span>
              </div>

              {activeRun.status === 'failed' ? (
                <div className="agent-failure">
                  <h4>The run was saved, but it did not complete.</h4>
                  <p>{activeRun.error || 'The model did not return a usable result.'}</p>
                </div>
              ) : (
                <>
                  <p className="agent-summary">{activeRun.summary}</p>
                  <div className="agent-result-grid">
                    <ResultList
                      title="Matched skills"
                      items={activeRun.matched_skills}
                      emptyMessage="No supported matches were returned."
                      tone="positive"
                    />
                    <ResultList
                      title="Skill gaps"
                      items={activeRun.skill_gaps}
                      emptyMessage="No evidence gaps were returned."
                      tone="gap"
                    />
                    <ResultList
                      title="Project evidence"
                      items={activeRun.project_evidence}
                      emptyMessage="No relevant project evidence was returned."
                    />
                    <ResultList
                      title="Interview focus"
                      items={activeRun.interview_focus}
                      emptyMessage="No interview topics were returned."
                    />
                  </div>
                </>
              )}

              <footer className="agent-result-meta">
                <span>{activeRun.model}</span>
                <span>
                  {activeRun.tool_trace.length} evidence tool call
                  {activeRun.tool_trace.length === 1 ? '' : 's'}
                </span>
              </footer>
            </article>
          )}

          {runs.length > 1 && (
            <div className="run-history">
              <h3>Recent runs</h3>
              <div>
                {runs.slice(0, 5).map((run) => {
                  const job = jobs.find((candidate) => candidate.id === run.job_id)
                  return (
                    <button
                      key={run.id}
                      type="button"
                      className={run.id === activeRun?.id ? 'active' : ''}
                      onClick={() => setActiveRunId(run.id)}
                    >
                      <span>{job ? `${job.company_name} · ${job.title}` : 'Saved run'}</span>
                      <small>{run.status}</small>
                    </button>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
