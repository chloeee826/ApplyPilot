import { useEffect, useState, type FormEvent } from 'react'
import { Navigate, NavLink, Route, Routes } from 'react-router-dom'

import { listAgentRuns } from './api/agentRuns'
import { listApplications, updateApplication } from './api/applications'
import { analyzeJob, listJobAnalyses } from './api/jobAnalyses'
import { createJob, listJobs, updateJob } from './api/jobs'
import { listProfiles } from './api/profiles'
import './App.css'
import { AgentWorkspace } from './components/AgentWorkspace'
import { CandidateProfilePanel } from './components/CandidateProfilePanel'
import { PageGuide } from './components/PageGuide'
import { JobsPage } from './pages/JobsPage'
import { OverviewPage } from './pages/OverviewPage'
import { FitCheckPage } from './pages/FitCheckPage'
import type { FitCheckResult } from './api/fitChecks'
import type { Application, ApplicationStatus } from './types/application'
import type { AgentRun } from './types/agentRun'
import type { CandidateProfile } from './types/candidate'
import type { Job, JobCreate } from './types/job'
import type { JobAnalysis } from './types/jobAnalysis'

const emptyForm: JobCreate = {
  company_name: '',
  title: '',
  description: '',
  location: '',
  source_url: '',
}

const navigation = [
  { label: 'Check fit', marker: '01', to: '/' },
  { label: 'Jobs', marker: '02', to: '/jobs' },
  { label: 'Reports', marker: '03', to: '/agent' },
]

function upsert<T extends { id: string }>(items: T[], saved: T): T[] {
  return [saved, ...items.filter((item) => item.id !== saved.id)]
}

function App() {
  const [backendStatus, setBackendStatus] = useState('Not checked')
  const [form, setForm] = useState<JobCreate>(emptyForm)
  const [jobs, setJobs] = useState<Job[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [analyses, setAnalyses] = useState<JobAnalysis[]>([])
  const [profiles, setProfiles] = useState<CandidateProfile[]>([])
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [updatingApplicationId, setUpdatingApplicationId] = useState<string | null>(
    null,
  )
  const [analyzingJobId, setAnalyzingJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [workspaceLoadError, setWorkspaceLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadWorkspace() {
      try {
        const [
          savedJobs,
          savedApplications,
          savedAnalyses,
          savedProfiles,
          savedAgentRuns,
        ] =
          await Promise.all([
            listJobs(),
            listApplications(),
            listJobAnalyses(),
            listProfiles(),
            listAgentRuns(),
          ])
        if (!cancelled) {
          setJobs(savedJobs)
          setApplications(savedApplications)
          setAnalyses(savedAnalyses)
          setProfiles(savedProfiles)
          setAgentRuns(savedAgentRuns)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Could not load jobs')
          setWorkspaceLoadError('Workspace could not load.')
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void loadWorkspace()
    return () => {
      cancelled = true
    }
  }, [])

  function updateField(field: keyof JobCreate, value: string) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function profileSaved(profile: CandidateProfile) {
    setProfiles((current) => upsert(current, profile))
    void refreshRunHistory()
  }

  function fitCheckCompleted(result: FitCheckResult) {
    setJobs((current) => upsert(current, result.job))
    setApplications((current) => upsert(current, result.application))
    setAnalyses((current) => upsert(current, result.analysis))
    setAgentRuns((current) => upsert(current, result.report))
    setError(null)
    setNotice(null)
  }

  async function refreshRunHistory() {
    try { setAgentRuns(await listAgentRuns()) }
    catch { setError('Changes were saved, but report history could not refresh. Reload before reviewing reports.') }
  }

  async function handleEditJob(id: string, values: JobCreate) {
    const previous = jobs.find((job) => job.id === id)
    const saved = await updateJob(id, values)
    setJobs((current) => current.map((job) => job.id === id ? saved : job))
    if (previous?.description !== saved.description) {
      setAnalyses((current) => current.filter((analysis) => analysis.job_id !== id))
    }
    setNotice('Changes saved. Re-analyze a changed description before generating a new report.')
    await refreshRunHistory()
  }

  async function handleAnalyzeJob(jobId: string) {
    setAnalyzingJobId(jobId)
    setError(null)
    setNotice(null)
    try {
      const savedAnalysis = await analyzeJob(jobId)
      setAnalyses((current) => {
        const exists = current.some((analysis) => analysis.id === savedAnalysis.id)
        return exists
          ? current.map((analysis) =>
              analysis.id === savedAnalysis.id ? savedAnalysis : analysis,
            )
          : [savedAnalysis, ...current]
      })
      setNotice('Job analysis is ready. You can now run this role under Reports → Advanced.')
      await refreshRunHistory()
    } catch (analysisError) {
      setError(
        analysisError instanceof Error
          ? analysisError.message
          : 'Could not analyze job description',
      )
    } finally {
      setAnalyzingJobId(null)
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setNotice(null)
    const payload: JobCreate = {
      company_name: form.company_name.trim(),
      title: form.title.trim(),
      description: form.description.trim(),
    }
    if (form.location?.trim()) payload.location = form.location.trim()
    if (form.source_url?.trim()) payload.source_url = form.source_url.trim()

    try {
      const savedJob = await createJob(payload)
      setJobs((current) => [savedJob, ...current])
      setForm(emptyForm)
      setNotice('Job saved. Analyze its description when you are ready to match it.')
      try { setApplications(await listApplications()) }
      catch { setError('Job saved, but application status could not refresh. Reload the workspace.') }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Could not create job')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleStatusChange(applicationId: string, status: ApplicationStatus) {
    setUpdatingApplicationId(applicationId)
    setError(null)
    setNotice(null)
    try {
      const updatedApplication = await updateApplication(applicationId, status)
      setApplications((current) =>
        current.map((application) =>
          application.id === updatedApplication.id ? updatedApplication : application,
        ),
      )
      setNotice('Application status updated.')
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : 'Could not update application status',
      )
    } finally {
      setUpdatingApplicationId(null)
    }
  }

  async function checkBackend() {
    setBackendStatus('Checking...')
    try {
      const response = await fetch('/api/health')
      if (!response.ok) throw new Error('Health check failed')
      const data = (await response.json()) as { status: string }
      setBackendStatus(data.status)
    } catch {
      setBackendStatus('Unavailable')
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink className="brand" to="/" aria-label="ApplyPilot overview">
          <span className="brand-mark">A</span>
          <span>
            <strong>ApplyPilot</strong>
            <small>Job search copilot</small>
          </span>
        </NavLink>

        <nav aria-label="Primary navigation">
          {navigation.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              <span>{item.marker}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p>Evidence in. Better interviews out.</p>
          <NavLink to="/candidate">Candidate library</NavLink>
          <NavLink to="/overview">Workspace summary</NavLink>
          <details><summary>Connection details</summary>
          <button className="health-button" type="button" onClick={checkBackend}>
            <span className={`status-dot status-${backendStatus.toLowerCase()}`} />
            API: {backendStatus}
          </button>
          </details>
        </div>
      </aside>

      <main className="app-content">
        {error && (
          <p className="error-message global-error" role="alert">
            {error}
          </p>
        )}
        {notice && (
          <p className="success-message global-notice" role="status">
            {notice}
          </p>
        )}
        <Routes>
          <Route
            path="/"
            element={<FitCheckPage profiles={profiles} jobs={jobs} analyses={analyses} runs={agentRuns}
              isLoading={isLoading} loadError={workspaceLoadError} onProfileSaved={profileSaved}
              onComplete={fitCheckCompleted} onRunsChange={setAgentRuns} />}
          />
          <Route
            path="/overview"
            element={
              <OverviewPage
                analyses={analyses}
                agentRuns={agentRuns}
                applications={applications}
                isLoading={isLoading}
                jobs={jobs}
                profiles={profiles}
              />
            }
          />
          <Route
            path="/jobs"
            element={
              <JobsPage
                analyses={analyses}
                analyzingJobId={analyzingJobId}
                applications={applications}
                form={form}
                isLoading={isLoading}
                isSubmitting={isSubmitting}
                jobs={jobs}
                onAnalyzeJob={handleAnalyzeJob}
                onEditJob={handleEditJob}
                onFieldChange={updateField}
                onStatusChange={handleStatusChange}
                onSubmit={handleSubmit}
                updatingApplicationId={updatingApplicationId}
              />
            }
          />
          <Route
            path="/candidate"
            element={
              <div className="feature-page">
                <header className="page-header">
                  <p className="eyebrow">Step 1 · Candidate evidence library</p>
                  <h1>Candidate</h1>
                  <p>Give every recommendation a factual source of skills and project evidence.</p>
                  <PageGuide
                    label="Candidate profile workflow"
                    items={[
                      { title: 'Upload', description: 'Choose a text-based PDF resume.' },
                      { title: 'Review', description: 'Correct the extracted profile and projects.' },
                      { title: 'Save', description: 'Create trusted evidence for matching.' },
                    ]}
                  />
                </header>
                <CandidateProfilePanel
                  onProfileSaved={profileSaved}
                  onEvidenceChanged={() => void refreshRunHistory()}
                />
              </div>
            }
          />
          <Route
            path="/agent"
            element={
              <div className="feature-page">
                <header className="page-header">
                  <p className="eyebrow">Your saved checks</p>
                  <h1>Reports</h1>
                  <p>Revisit your results and supporting evidence. <NavLink to="/">Start a new fit check →</NavLink></p>
                </header>
                <AgentWorkspace
                  jobs={jobs}
                  analyses={analyses}
                  profiles={profiles}
                  runs={agentRuns}
                  isLoading={isLoading}
                  onRunsChange={setAgentRuns}
                />
              </div>
            }
          />
          <Route path="*" element={<Navigate replace to="/" />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
