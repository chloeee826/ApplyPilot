import { Link } from 'react-router-dom'

import type { AgentRun } from '../types/agentRun'
import type { Application } from '../types/application'
import type { CandidateProfile } from '../types/candidate'
import type { Job } from '../types/job'
import type { JobAnalysis } from '../types/jobAnalysis'

interface OverviewPageProps {
  analyses: JobAnalysis[]
  agentRuns: AgentRun[]
  applications: Application[]
  isLoading: boolean
  jobs: Job[]
  profiles: CandidateProfile[]
}

export function OverviewPage({
  analyses,
  agentRuns,
  applications,
  isLoading,
  jobs,
  profiles,
}: OverviewPageProps) {
  const activeApplications = applications.filter(
    (application) => !['rejected', 'withdrawn'].includes(application.status),
  ).length
  const completedRuns = agentRuns.filter((run) => run.status === 'completed')
  const journeySteps = [
    {
      title: 'Build candidate evidence',
      description: 'Import and review your resume profile and projects.',
      complete: profiles.length > 0,
      to: '/candidate',
    },
    {
      title: 'Save a target job',
      description: 'Store the original posting and track its application status.',
      complete: jobs.length > 0,
      to: '/jobs',
    },
    {
      title: 'Analyze requirements',
      description: 'Extract structured skills and responsibilities from the posting.',
      complete: analyses.length > 0,
      to: '/jobs',
    },
    {
      title: 'Generate a match strategy',
      description: 'Use saved evidence to identify matches, gaps, and interview focus.',
      complete: completedRuns.length > 0,
      to: '/agent',
    },
  ]
  const completedStepCount = journeySteps.filter((step) => step.complete).length
  const currentStepIndex = journeySteps.findIndex((step) => !step.complete)
  const nextStep =
    currentStepIndex === -1
      ? {
          title: 'Review your latest match',
          description:
            'Your first complete workflow is ready. Review the recommendation or run another role.',
          to: '/agent',
          linkLabel: 'View Agent Match',
        }
      : {
          title: journeySteps[currentStepIndex].title,
          description: journeySteps[currentStepIndex].description,
          to: journeySteps[currentStepIndex].to,
          linkLabel: `Continue to step ${currentStepIndex + 1}`,
        }

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
          <Link className="primary-link" to={nextStep.to}>
            {nextStep.linkLabel}
          </Link>
          <Link className="secondary-link" to="/jobs">
            View job pipeline
          </Link>
        </div>
      </header>

      <section className="journey-card" aria-labelledby="journey-heading">
        <div className="journey-heading">
          <div>
            <p className="step-label">Guided demo journey</p>
            <h2 id="journey-heading">From resume to interview strategy</h2>
          </div>
          <span>{isLoading ? 'Loading' : `${completedStepCount} of 4 complete`}</span>
        </div>
        <ol className="journey-steps">
          {journeySteps.map((step, index) => {
            const isCurrent = index === currentStepIndex
            return (
              <li
                className={step.complete ? 'complete' : isCurrent ? 'current' : 'pending'}
                key={step.title}
              >
                <Link to={step.to}>
                  <span className="journey-number">
                    {step.complete ? '✓' : String(index + 1).padStart(2, '0')}
                  </span>
                  <div>
                    <strong>{step.title}</strong>
                    <small>{step.description}</small>
                  </div>
                  <em>{step.complete ? 'Complete' : isCurrent ? 'Next' : 'Later'}</em>
                </Link>
              </li>
            )
          })}
        </ol>
      </section>

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
        <article className="metric-card metric-blue">
          <span>Completed matches</span>
          <strong>{isLoading ? '—' : completedRuns.length}</strong>
          <p>Persistent agent recommendations ready to review</p>
        </article>
      </section>

      <section className="overview-grid">
        <article className="overview-card">
          <div className="section-heading compact-heading">
            <p className="step-label">Workspace readiness</p>
            <h2>Your next best action</h2>
          </div>
          {isLoading ? (
            <p className="overview-empty">Loading workspace readiness…</p>
          ) : (
            <>
              <h3>{nextStep.title}</h3>
              <p>{nextStep.description}</p>
              <Link to={nextStep.to}>{nextStep.linkLabel} →</Link>
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
