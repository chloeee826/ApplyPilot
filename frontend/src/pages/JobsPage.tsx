import { useState, type FormEvent } from 'react'
import { JobEditor } from '../components/JobEditor'

import { PageGuide } from '../components/PageGuide'
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
  onEditJob: (jobId: string, values: JobCreate) => Promise<void>
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
  onEditJob,
  onFieldChange,
  onStatusChange,
  onSubmit,
  updatingApplicationId,
}: JobsPageProps) {
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(0)
  const filtered = jobs.filter((job) => {
    const application = applications.find((item) => item.job_id === job.id)
    const text = `${job.company_name} ${job.title} ${job.location ?? ''}`.toLowerCase()
    return text.includes(query.trim().toLowerCase()) && (statusFilter === 'all' || application?.status === statusFilter)
  })
  const pages = Math.max(1, Math.ceil(filtered.length / 5))
  const activePage = Math.min(page, pages - 1)
  const visible = filtered.slice(activePage * 5, activePage * 5 + 5)
  return (
    <>
      <header className="page-header">
        <p className="eyebrow">Steps 2–3 · Job application tracker</p>
        <h1>Jobs</h1>
        <p>
          Save target roles, move applications through the pipeline, and turn job
          descriptions into structured requirements.
        </p>
        <PageGuide
          label="Job tracking workflow"
          items={[
            { title: 'Save', description: 'Store the original job posting.' },
            { title: 'Track', description: 'Update the application pipeline status.' },
            { title: 'Analyze', description: 'Extract skills and role requirements.' },
          ]}
        />
      </header>

      <section className="workspace" aria-label="Job workspace">
        <form className="job-form" onSubmit={onSubmit}>
          <div className="section-heading">
            <p className="step-label">Step 2 · Save a role</p>
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
              <p className="step-label">Step 3 · Track and analyze</p>
              <h2 id="saved-jobs-heading">Saved jobs</h2>
            </div>
            <span className="job-count">{jobs.length}</span>
          </div>

          <div className="job-filters">
            <label>Search saved jobs<input type="search" placeholder="Company, role, or location" value={query}
              onChange={(event) => { setQuery(event.target.value); setPage(0) }} /></label>
            <label>Filter by status<select value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(0) }}>
              <option value="all">All statuses</option>
              {applicationStatuses.map((value) => <option key={value} value={value}>{value}</option>)}
            </select></label>
          </div>
          {!isLoading && jobs.length > 0 && filtered.length === 0 && <p className="empty-state">No jobs match these filters. Try another search or status.</p>}

          {isLoading && <p className="empty-state">Loading saved jobs…</p>}

          {!isLoading && jobs.length === 0 && (
            <div className="empty-state">
              <p>No saved jobs yet.</p>
              <span>Add your first target role using the form.</span>
            </div>
          )}

          <div className="job-list">
            {visible.map((job) => {
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
                  <JobEditor job={job} onSave={onEditJob} />
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
          {filtered.length > 0 && <nav className="job-pagination" aria-label="Saved job pages">
            <button className="analysis-button" disabled={activePage === 0} onClick={() => setPage(activePage - 1)}>Previous page</button>
            <span aria-live="polite">Page {activePage + 1} of {pages} · {filtered.length} matching jobs</span>
            <button className="analysis-button" disabled={activePage + 1 >= pages} onClick={() => setPage(activePage + 1)}>Next page</button>
          </nav>}
        </section>
      </section>
    </>
  )
}
