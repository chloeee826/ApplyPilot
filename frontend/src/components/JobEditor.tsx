import { useState, type FormEvent } from 'react'
import type { Job, JobCreate } from '../types/job'

export function JobEditor({ job, onSave }: { job: Job; onSave: (id: string, values: JobCreate) => Promise<void> }) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<JobCreate>(job)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await onSave(job.id, {
        company_name: draft.company_name.trim(), title: draft.title.trim(),
        description: draft.description.trim(), location: draft.location?.trim() || null,
        source_url: draft.source_url?.trim() || null,
      })
      setEditing(false)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not save changes.')
    } finally { setSaving(false) }
  }

  if (!editing) return <button className="analysis-button" type="button" onClick={() => {
    setDraft(job); setError(null); setEditing(true)
  }}>Edit job</button>

  return (
    <form className="job-edit-form" onSubmit={save} aria-label={`Edit ${job.title}`}>
      <h4>Edit saved role</h4>
      {(['company_name', 'title', 'location', 'source_url'] as const).map((field) => (
        <label key={field}>
          {{ company_name: 'Edit company', title: 'Edit role title', location: 'Edit location', source_url: 'Edit source URL' }[field]}
          <input type={field === 'source_url' ? 'url' : 'text'} required={field === 'company_name' || field === 'title'}
            maxLength={field === 'source_url' ? 2048 : 120} value={draft[field] ?? ''}
            onChange={(event) => setDraft((current) => ({ ...current, [field]: event.target.value }))} disabled={saving} />
        </label>
      ))}
      <label>Edit job description<textarea required rows={5} value={draft.description} disabled={saving}
        onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))} /></label>
      <p>Changing the description removes its old analysis. Saved reports remain available as history.</p>
      {error && <p role="alert" className="error-message">{error}</p>}
      <div className="job-edit-actions">
        <button className="primary-button" disabled={saving} type="submit">{saving ? 'Saving…' : 'Save changes'}</button>
        <button className="analysis-button" disabled={saving} type="button" onClick={() => setEditing(false)}>Cancel edit</button>
      </div>
    </form>
  )
}
