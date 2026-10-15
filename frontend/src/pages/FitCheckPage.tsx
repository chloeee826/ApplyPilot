import { useRef, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { checkFit, type FitCheckResult } from '../api/fitChecks'
import { AgentWorkspace } from '../components/AgentWorkspace'
import { CandidateProfilePanel } from '../components/CandidateProfilePanel'
import type { AgentRun } from '../types/agentRun'
import type { CandidateProfile } from '../types/candidate'
import type { Job, JobCreate } from '../types/job'
import type { JobAnalysis } from '../types/jobAnalysis'

interface Props {
  profiles: CandidateProfile[]
  jobs: Job[]
  analyses: JobAnalysis[]
  runs: AgentRun[]
  isLoading: boolean
  loadError: string | null
  onProfileSaved: (profile: CandidateProfile) => void
  onComplete: (result: FitCheckResult) => void
  onRunsChange: (runs: AgentRun[]) => void
}

export function FitCheckPage(props: Props) {
  const [params, setParams] = useSearchParams()
  const [step, setStep] = useState(1)
  const [selectedProfileId, setSelectedProfileId] = useState('')
  const [draft, setDraft] = useState<JobCreate>({ company_name: '', title: '', description: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const request = useRef<{ signature: string; id: string } | null>(null)
  const profile = props.profiles.find((item) => item.id === selectedProfileId) ?? props.profiles[0]
  const reportId = params.get('run')
  const report = props.runs.find((item) => item.id === reportId)
  const activeStep = reportId ? 3 : step

  function savedProfile(saved: CandidateProfile) {
    props.onProfileSaved(saved)
    setSelectedProfileId(saved.id)
    request.current = null
    setStep(2)
  }

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!profile || busy) return
    setBusy(true)
    setError(null)
    const job = { company_name: draft.company_name.trim(), title: draft.title.trim(), description: draft.description.trim() }
    const signature = JSON.stringify({ job, profile_id: profile.id })
    if (request.current?.signature !== signature) request.current = { signature, id: crypto.randomUUID() }
    try {
      const result = await checkFit(request.current.id, profile.id, job)
      props.onComplete(result)
      setParams({ run: result.report.id })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The check could not complete. Try again.')
    } finally { setBusy(false) }
  }

  function startNew() {
    request.current = null
    setError(null)
    setDraft({ company_name: '', title: '', description: '' })
    setParams({})
    setStep(profile ? 2 : 1)
  }

  return (
    <div className="fit-flow">
      <header className="fit-hero">
        <p className="eyebrow">Your experience. Your next role.</p>
        <h1>How does your resume fit this job?</h1>
        <p>Bring your resume and a job description. See the evidence you have, what needs support, and what to prepare.</p>
      </header>
      <ol className="fit-steps" aria-label="Resume matching steps">
        {['Your resume', 'Target job', 'Your results'].map((label, index) => (
          <li key={label} className={activeStep === index + 1 ? 'current' : activeStep > index + 1 ? 'complete' : ''}
            aria-current={activeStep === index + 1 ? 'step' : undefined}>
            <span>{activeStep > index + 1 ? '✓' : index + 1}</span>{label}
          </li>
        ))}
      </ol>
      {props.isLoading ? <p role="status">Loading your saved workspace…</p> : props.loadError ? (
        <p role="alert">Workspace could not load. Reload the page before starting a check.</p>
      ) : activeStep === 1 ? (
        <section className="flow-step" aria-label="Your resume">
          <h2>Start with your resume</h2>
          <p>Use a saved profile or upload a text-based PDF. You can correct the draft before saving.</p>
          {profile && <article className="flow-profile-choice">
            <div><p className="eyebrow">Saved profile</p><h3>{profile.full_name}</h3>
              <p>{profile.skills.slice(0, 6).join(' · ')}</p></div>
            <button type="button" className="primary-button" onClick={() => setStep(2)}>Use this profile</button>
          </article>}
          {profile ? <details className="flow-edit-profile"><summary>Upload a resume or edit saved evidence</summary>
            <CandidateProfilePanel guided onProfileSaved={savedProfile} />
          </details> : <CandidateProfilePanel guided onProfileSaved={savedProfile} />}
          {props.runs[0] && <Link className="text-button" to={`/?run=${props.runs[0].id}`}>Open your latest report →</Link>}
        </section>
      ) : activeStep === 2 ? (
        <section className="flow-step" aria-label="Target job">
          <button type="button" className="text-button" disabled={busy} onClick={() => setStep(1)}>← Change resume</button>
          <h2>Which role are you considering?</h2>
          <p>Checking evidence from <strong>{profile?.full_name}</strong>. Paste the original posting below.</p>
          <form className="flow-job-form" onSubmit={analyze}>
            <div className="form-row">
              <label>Company<input required maxLength={120} value={draft.company_name} disabled={busy}
                onChange={(event) => setDraft((old) => ({ ...old, company_name: event.target.value }))} placeholder="Company name" /></label>
              <label>Role title<input required maxLength={120} value={draft.title} disabled={busy}
                onChange={(event) => setDraft((old) => ({ ...old, title: event.target.value }))} placeholder="e.g. Backend Engineer" /></label>
            </div>
            <label>Job description<textarea required rows={9} value={draft.description} disabled={busy}
              onChange={(event) => setDraft((old) => ({ ...old, description: event.target.value }))}
              placeholder="Paste the responsibilities and qualifications…" /></label>
            <p className="flow-mode-note">Rules-based evidence check. No paid AI request is made.</p>
            {error && <div role="alert" className="error-message"><p>{error}</p>
              <button type="button" className="text-button" onClick={() => { request.current = null; setError(null) }}>Start a new check with these inputs</button>
            </div>}
            <button type="submit" className="primary-button" disabled={busy || !profile}>
              {busy ? 'Checking your evidence…' : 'Analyze my fit'}
            </button>
            {busy && <p role="status">Saving the role, extracting requirements, and checking saved evidence…</p>}
          </form>
        </section>
      ) : report ? (
        <section aria-label="Your results">
          <div className="flow-result-actions">
            <button type="button" className="secondary-button" onClick={startNew}>Check another job</button>
            <Link to="/jobs">Track this application →</Link>
          </div>
          <AgentWorkspace reportOnly jobs={props.jobs} analyses={props.analyses} profiles={props.profiles}
            runs={[report]} isLoading={false} onRunsChange={props.onRunsChange} />
        </section>
      ) : <section className="flow-step"><h2>Report not found</h2><p>Choose a saved report or start a new check.</p>
        <button type="button" className="primary-button" onClick={startNew}>Start a new check</button><Link to="/agent">View saved reports</Link>
      </section>}
    </div>
  )
}
