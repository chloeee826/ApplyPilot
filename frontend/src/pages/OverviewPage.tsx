import { Link } from 'react-router-dom'

import type { Application } from '../types/application'
import type { CandidateProfile } from '../types/candidate'
import type { Job } from '../types/job'
import type { JobAnalysis } from '../types/jobAnalysis'

interface OverviewPageProps {
  analyses: JobAnalysis[]
  applications: Application[]
  isLoading: boolean
  jobs: Job[]
  profiles: CandidateProfile[]
}

export function OverviewPage({
  analyses,
  applications,
  isLoading,
  jobs,
  profiles,
}: OverviewPageProps) {
  const activeApplications = applications.filter(
    (application) => !['rejected', 'withdrawn'].includes(application.status),
  ).length
  const analyzedJobIds = new Set(analyses.map((analysis) => analysis.job_id))
  const nextJob = jobs.find((job) => !analyzedJobIds.has(job.id))

  return (
    <>
      <header className="page-header overview-header">
        <p className="eyebrow">Agentic job search workspace</p>
        <h1>Make every application evidence-backed.</h1>
        <p>
          Track target roles, organize your strongest project evidence, and use an AI
          agent to prepare a grounded match strategy.
        </p>
        <div className="header-actions">
          <Link className="primary-link" to="/jobs">
            Add a target job
          </Link>
          <Link className="secondary-link" to="/agent">
            Open Agent Match
          </Link>
        </div>
      </header>

      <section className="metric-grid" aria-label="Workspace summary">
        <article className="metric-card metric-blue">
          <span>Saved roles</span>
          <strong>{isLoading ? '—' : jobs.length}</strong>
          <p>Job descriptions stored in your workspace</p>
        </article>
        <article className="metric-card metric-sage">
          <span>Active pipeline</span>
          <strong>{isLoading ? '—' : activeApplications}</strong>
          <p>Applications still in progress</p>
        </article>
        <article className="metric-card metric-cream">
          <span>Analyzed roles</span>
          <strong>{isLoading ? '—' : analyses.length}</strong>
          <p>Structured requirement sets ready for matching</p>
        </article>
      </section>

      <section className="overview-grid">
        <article className="overview-card">
          <div className="section-heading compact-heading">
            <p className="step-label">Workspace readiness</p>
            <h2>Your next best action</h2>
          </div>
          {profiles.length === 0 ? (
            <>
              <h3>Create your candidate profile</h3>
              <p>The agent needs your skills and project evidence before it can match you.</p>
              <Link to="/candidate">Build candidate profile →</Link>
            </>
          ) : nextJob ? (
            <>
              <h3>Analyze {nextJob.company_name}</h3>
              <p>
                Turn the {nextJob.title} posting into structured skills and requirements.
              </p>
              <Link to="/jobs">Analyze job description →</Link>
            </>
          ) : jobs.length === 0 ? (
            <>
              <h3>Save your first target role</h3>
              <p>Add a real job description to start building your application pipeline.</p>
              <Link to="/jobs">Add a job →</Link>
            </>
          ) : (
            <>
              <h3>Your evidence is ready</h3>
              <p>Run a job-match workflow using your saved profile and analyzed role.</p>
              <Link to="/agent">Run Agent Match →</Link>
            </>
          )}
        </article>

        <article className="overview-card recent-roles">
          <div className="section-heading compact-heading">
            <p className="step-label">Recent activity</p>
            <h2>Latest target roles</h2>
          </div>
          {jobs.length === 0 ? (
            <p className="overview-empty">Your recently saved roles will appear here.</p>
          ) : (
            <div className="recent-role-list">
              {jobs.slice(0, 3).map((job) => {
                const application = applications.find(
                  (candidate) => candidate.job_id === job.id,
                )
                return (
                  <div key={job.id}>
                    <span>{job.company_name}</span>
                    <strong>{job.title}</strong>
                    <small>{application?.status ?? 'saved'}</small>
                  </div>
                )
              })}
            </div>
          )}
          <Link to="/jobs">View complete pipeline →</Link>
        </article>
      </section>
    </>
  )
}
