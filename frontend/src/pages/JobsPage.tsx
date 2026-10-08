import type { FormEvent } from 'react'

import type { Application, ApplicationStatus } from '../types/application'
import type { Job, JobCreate } from '../types/job'
import type { JobAnalysis } from '../types/jobAnalysis'

const applicationStatuses: ApplicationStatus[] = [
  'saved',
  'applied',
  'interviewing',
  'offer',
  'rejected',
  'withdrawn',
]

interface JobsPageProps {
  analyses: JobAnalysis[]
  analyzingJobId: string | null
  applications: Application[]
  form: JobCreate
  isLoading: boolean
  isSubmitting: boolean
  jobs: Job[]
  onAnalyzeJob: (jobId: string) => Promise<void>
  onFieldChange: (field: keyof JobCreate, value: string) => void
  onStatusChange: (
    applicationId: string,
    status: ApplicationStatus,
  ) => Promise<void>
  onSubmit: (event: FormEvent<HTMLFormElement>) => Promise<void>
  updatingApplicationId: string | null
}

export function JobsPage({
  analyses,
  analyzingJobId,
  applications,
  form,
  isLoading,
  isSubmitting,
  jobs,
  onAnalyzeJob,
  onFieldChange,
  onStatusChange,
  onSubmit,
  updatingApplicationId,
}: JobsPageProps) {
  return (
    <>
      <header className="page-header">
        <p className="eyebrow">Job application tracker</p>
        <h1>Jobs</h1>
        <p>
          Save target roles, move applications through the pipeline, and turn job
          descriptions into structured requirements.
        </p>
      </header>

      <section className="workspace" aria-label="Job workspace">
        <form className="job-form" onSubmit={onSubmit}>
          <div className="section-heading">
            <p className="step-label">01 · Save a role</p>
            <h2>Add a target job</h2>
            <p>Store the original posting before analyzing it.</p>
          </div>

          <label>
            Company
            <input
              required
              maxLength={120}
              value={form.company_name}
              onChange={(event) => onFieldChange('company_name', event.target.value)}
              placeholder="Example Company"
            />
          </label>

          <label>
            Role title
            <input
              required
              maxLength={120}
              value={form.title}
              onChange={(event) => onFieldChange('title', event.target.value)}
              placeholder="Software Engineer"
            />
          </label>

          <div className="form-row">
            <label>
              Location <span>Optional</span>
              <input
                maxLength={120}
                value={form.location ?? ''}
                onChange={(event) => onFieldChange('location', event.target.value)}
                placeholder="Remote or city"
              />
            </label>

            <label>
              Source URL <span>Optional</span>
              <input
                type="url"
                value={form.source_url ?? ''}
                onChange={(event) => onFieldChange('source_url', event.target.value)}
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
              onChange={(event) => onFieldChange('description', event.target.value)}
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
              const analysis = analyses.find(
                (candidate) => candidate.job_id === job.id,
              )

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
                          void onStatusChange(
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
                    onClick={() => void onAnalyzeJob(job.id)}
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
    </>
  )
}
