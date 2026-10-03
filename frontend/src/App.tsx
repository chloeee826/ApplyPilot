import { useEffect, useState, type FormEvent } from 'react'

import { listApplications, updateApplication } from './api/applications'
import { analyzeJob, listJobAnalyses } from './api/jobAnalyses'
import { createJob, listJobs } from './api/jobs'
import { listProfiles } from './api/profiles'
import './App.css'
import { AgentWorkspace } from './components/AgentWorkspace'
import { CandidateProfilePanel } from './components/CandidateProfilePanel'
import type { Application, ApplicationStatus } from './types/application'
import type { CandidateProfile } from './types/candidate'
import type { Job, JobCreate } from './types/job'
import type { JobAnalysis } from './types/jobAnalysis'

const applicationStatuses: ApplicationStatus[] = [
  'saved',
  'applied',
  'interviewing',
  'offer',
  'rejected',
  'withdrawn',
]

const emptyForm: JobCreate = {
  company_name: '',
  title: '',
  description: '',
  location: '',
  source_url: '',
}

function App() {
  const [backendStatus, setBackendStatus] = useState('Not checked')
  const [form, setForm] = useState<JobCreate>(emptyForm)
  const [jobs, setJobs] = useState<Job[]>([])
  const [applications, setApplications] = useState<Application[]>([])
  const [analyses, setAnalyses] = useState<JobAnalysis[]>([])
  const [profiles, setProfiles] = useState<CandidateProfile[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [updatingApplicationId, setUpdatingApplicationId] = useState<string | null>(
    null,
  )
  const [analyzingJobId, setAnalyzingJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadWorkspace() {
      try {
        const [savedJobs, savedApplications, savedAnalyses, savedProfiles] =
          await Promise.all([
            listJobs(),
            listApplications(),
            listJobAnalyses(),
            listProfiles(),
          ])
        if (!cancelled) {
          setJobs(savedJobs)
          setApplications(savedApplications)
          setAnalyses(savedAnalyses)
          setProfiles(savedProfiles)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : 'Could not load jobs')
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

  async function handleAnalyzeJob(jobId: string) {
    setAnalyzingJobId(jobId)
    setError(null)

    try {
      const savedAnalysis = await analyzeJob(jobId)
      setAnalyses((current) => {
        const alreadyExists = current.some(
          (analysis) => analysis.id === savedAnalysis.id,
        )
        return alreadyExists
          ? current.map((analysis) =>
              analysis.id === savedAnalysis.id ? savedAnalysis : analysis,
            )
          : [savedAnalysis, ...current]
      })
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

    const payload: JobCreate = {
      company_name: form.company_name.trim(),
      title: form.title.trim(),
      description: form.description.trim(),
    }

    if (form.location?.trim()) payload.location = form.location.trim()
    if (form.source_url?.trim()) payload.source_url = form.source_url.trim()

    try {
      const savedJob = await createJob(payload)
      const savedApplications = await listApplications()
      setJobs((current) => [savedJob, ...current])
      setApplications(savedApplications)
      setForm(emptyForm)
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'Could not create job',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleStatusChange(
    applicationId: string,
    status: ApplicationStatus,
  ) {
    setUpdatingApplicationId(applicationId)
    setError(null)

    try {
      const updatedApplication = await updateApplication(applicationId, status)
      setApplications((current) =>
        current.map((application) =>
          application.id === updatedApplication.id ? updatedApplication : application,
        ),
      )
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
      const response = await fetch('/health')
      if (!response.ok) throw new Error('Health check failed')
      const data = (await response.json()) as { status: string }
      setBackendStatus(data.status)
    } catch {
      setBackendStatus('Unavailable')
    }
  }

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">Agentic job search workspace</p>
          <h1>ApplyPilot</h1>
          <p className="subtitle">
            Save target roles, build an evidence-backed profile, and prepare with an AI
            agent.
          </p>
        </div>
        <button className="health-button" type="button" onClick={checkBackend}>
          <span className={`status-dot status-${backendStatus.toLowerCase()}`} />
          API: {backendStatus}
        </button>
      </header>

      {error && <p className="error-message">{error}</p>}

      <section className="workspace" aria-label="Job workspace">
        <form className="job-form" onSubmit={handleSubmit}>
          <div className="section-heading">
            <p className="step-label">01 · Save a role</p>
            <h2>Add a target job</h2>
            <p>Store the job description now so ApplyPilot can analyze it later.</p>
          </div>

          <label>
            Company
            <input
              required
              maxLength={120}
              value={form.company_name}
              onChange={(event) => updateField('company_name', event.target.value)}
              placeholder="Example Company"
            />
          </label>

          <label>
            Role title
            <input
              required
              maxLength={120}
              value={form.title}
              onChange={(event) => updateField('title', event.target.value)}
              placeholder="Software Engineer"
            />
          </label>

          <div className="form-row">
            <label>
              Location <span>Optional</span>
              <input
                maxLength={120}
                value={form.location ?? ''}
                onChange={(event) => updateField('location', event.target.value)}
                placeholder="Remote or city"
              />
            </label>

            <label>
              Source URL <span>Optional</span>
              <input
                type="url"
                value={form.source_url ?? ''}
                onChange={(event) => updateField('source_url', event.target.value)}
                placeholder="https://..."
              />
            </label>
          </div>

          <label>
            Job description
            <textarea
              required
              rows={7}
              value={form.description}
              onChange={(event) => updateField('description', event.target.value)}
              placeholder="Paste the responsibilities and qualifications here..."
            />
          </label>

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving…' : 'Save job'}
          </button>
        </form>

        <section className="jobs-panel" aria-labelledby="saved-jobs-heading">
          <div className="section-heading jobs-heading">
            <div>
              <p className="step-label">02 · Review pipeline</p>
              <h2 id="saved-jobs-heading">Saved jobs</h2>
            </div>
            <span className="job-count">{jobs.length}</span>
          </div>

          {isLoading && <p className="empty-state">Loading saved jobs…</p>}

          {!isLoading && jobs.length === 0 && (
            <div className="empty-state">
              <p>No saved jobs yet.</p>
              <span>Add your first target role using the form.</span>
            </div>
          )}

          <div className="job-list">
            {jobs.map((job) => {
              const application = applications.find(
                (candidate) => candidate.job_id === job.id,
              )
              const analysis = analyses.find((candidate) => candidate.job_id === job.id)

              return (
                <article className="job-card" key={job.id}>
                  <div className="job-card-topline">
                    <span>{job.company_name}</span>
                    <time dateTime={job.created_at}>
                      {new Intl.DateTimeFormat('en', {
                        month: 'short',
                        day: 'numeric',
                      }).format(new Date(job.created_at))}
                    </time>
                  </div>
                  <h3>{job.title}</h3>
                  <p>{job.location || 'Location not specified'}</p>
                  {application && (
                    <label className="status-field">
                      Application status
                      <select
                        value={application.status}
                        disabled={updatingApplicationId === application.id}
                        onChange={(event) =>
                          void handleStatusChange(
                            application.id,
                            event.target.value as ApplicationStatus,
                          )
                        }
                      >
                        {applicationStatuses.map((status) => (
                          <option key={status} value={status}>
                            {status.charAt(0).toUpperCase() + status.slice(1)}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  <p className="job-description">{job.description}</p>
                  <button
                    className="analysis-button"
                    type="button"
                    disabled={analyzingJobId === job.id}
                    onClick={() => void handleAnalyzeJob(job.id)}
                  >
                    {analyzingJobId === job.id
                      ? 'Analyzing…'
                      : analysis
                        ? 'Refresh analysis'
                        : 'Analyze description'}
                  </button>
                  {analysis && (
                    <section className="analysis-panel" aria-label="Job analysis">
                      <div className="analysis-heading">
                        <h4>Structured analysis</h4>
                        <span>{analysis.parser_version}</span>
                      </div>
                      <div className="tag-list" aria-label="Extracted skills">
                        {analysis.skills.map((skill) => (
                          <span key={skill}>{skill}</span>
                        ))}
                      </div>
                      {analysis.requirements.length > 0 && (
                        <div className="analysis-group">
                          <h5>Requirements</h5>
                          <ul>
                            {analysis.requirements.map((requirement) => (
                              <li key={requirement}>{requirement}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {analysis.preferred_qualifications.length > 0 && (
                        <div className="analysis-group">
                          <h5>Preferred</h5>
                          <ul>
                            {analysis.preferred_qualifications.map((qualification) => (
                              <li key={qualification}>{qualification}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {analysis.responsibilities.length > 0 && (
                        <div className="analysis-group">
                          <h5>Responsibilities</h5>
                          <ul>
                            {analysis.responsibilities.map((responsibility) => (
                              <li key={responsibility}>{responsibility}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </section>
                  )}
                  {job.source_url && (
                    <a href={job.source_url} target="_blank" rel="noreferrer">
                      View original posting ↗
                    </a>
                  )}
                </article>
              )
            })}
          </div>
        </section>
      </section>

      <CandidateProfilePanel
        onProfileCreated={(profile) =>
          setProfiles((current) => [profile, ...current])
        }
      />

      <AgentWorkspace jobs={jobs} analyses={analyses} profiles={profiles} />
    </main>
  )
}

export default App
