import { useEffect, useState, type FormEvent } from 'react'

import {
  createProfile,
  createProject,
  extractResume,
  listProfiles,
  listProjects,
  saveCandidateImport,
  updateProfile,
} from '../api/profiles'
import type {
  CandidateProfile,
  CandidateProfileCreate,
  CandidateProject,
  CandidateProjectCreate,
  ResumeExtraction,
} from '../types/candidate'

interface ProfileForm {
  fullName: string
  headline: string
  summary: string
  skills: string
}

interface ProjectForm {
  name: string
  description: string
  technologies: string
  highlights: string
}

interface CandidateProfilePanelProps {
  onProfileSaved?: (profile: CandidateProfile) => void
}

const emptyProfileForm: ProfileForm = {
  fullName: '',
  headline: '',
  summary: '',
  skills: '',
}

const emptyProjectForm: ProjectForm = {
  name: '',
  description: '',
  technologies: '',
  highlights: '',
}

function commaSeparatedItems(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function lineSeparatedItems(value: string): string[] {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

function profileToForm(profile: CandidateProfileCreate): ProfileForm {
  return {
    fullName: profile.full_name,
    headline: profile.headline ?? '',
    summary: profile.summary,
    skills: profile.skills.join(', '),
  }
}

function projectToForm(project: CandidateProjectCreate): ProjectForm {
  return {
    name: project.name,
    description: project.description,
    technologies: project.technologies.join(', '),
    highlights: project.highlights.join('\n'),
  }
}

export function CandidateProfilePanel({ onProfileSaved }: CandidateProfilePanelProps) {
  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [projects, setProjects] = useState<CandidateProject[]>([])
  const [profileForm, setProfileForm] = useState<ProfileForm>(emptyProfileForm)
  const [projectForm, setProjectForm] = useState<ProjectForm>(emptyProjectForm)
  const [selectedResume, setSelectedResume] = useState<File | null>(null)
  const [resumeExtraction, setResumeExtraction] = useState<ResumeExtraction | null>(
    null,
  )
  const [resumeProjectForms, setResumeProjectForms] = useState<ProjectForm[]>([])
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isExtracting, setIsExtracting] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadCandidateData() {
      try {
        const profiles = await listProfiles()
        const savedProfile = profiles[0] ?? null
        if (cancelled) return

        setProfile(savedProfile)
        if (savedProfile) {
          const savedProjects = await listProjects(savedProfile.id)
          if (!cancelled) setProjects(savedProjects)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : 'Could not load candidate profile',
          )
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void loadCandidateData()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleResumeSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedResume) return

    setIsExtracting(true)
    setError(null)
    setNotice(null)
    try {
      const extraction = await extractResume(selectedResume)
      setResumeExtraction(extraction)
      setProfileForm(profileToForm(extraction.profile))
      setResumeProjectForms(extraction.projects.map(projectToForm))
      setIsEditingProfile(true)
    } catch (uploadError) {
      setError(
        uploadError instanceof Error ? uploadError.message : 'Could not read resume',
      )
    } finally {
      setIsExtracting(false)
    }
  }

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setNotice(null)

    const payload: CandidateProfileCreate = {
      full_name: profileForm.fullName.trim(),
      summary: profileForm.summary.trim(),
      skills: commaSeparatedItems(profileForm.skills),
      headline: profileForm.headline.trim() || null,
    }

    try {
      let savedProfile: CandidateProfile
      let savedImportProjects: CandidateProject[] = []
      let importNotice: string | null = null
      if (resumeExtraction) {
        const reviewedProjects: CandidateProjectCreate[] = resumeProjectForms.map(
          (project) => ({
            name: project.name.trim(),
            description: project.description.trim(),
            technologies: commaSeparatedItems(project.technologies),
            highlights: lineSeparatedItems(project.highlights),
          }),
        )
        const result = await saveCandidateImport(
          payload,
          reviewedProjects,
          profile?.id,
        )
        savedProfile = result.profile
        savedImportProjects = result.projects
        importNotice = `Profile saved with ${result.created_project_count} new and ${result.updated_project_count} updated project${result.projects.length === 1 ? '' : 's'}.`
      } else {
        savedProfile = profile
          ? await updateProfile(profile.id, payload)
          : await createProfile(payload)
      }
      setProfile(savedProfile)
      if (savedImportProjects.length > 0) {
        const importedIds = new Set(savedImportProjects.map((project) => project.id))
        setProjects((current) => [
          ...savedImportProjects,
          ...current.filter((project) => !importedIds.has(project.id)),
        ])
      }
      onProfileSaved?.(savedProfile)
      setProfileForm(emptyProfileForm)
      setResumeExtraction(null)
      setResumeProjectForms([])
      setSelectedResume(null)
      setIsEditingProfile(false)
      setNotice(
        importNotice ??
          (profile
            ? 'Reviewed profile fields were saved to your active profile.'
            : 'Candidate profile created from your reviewed draft.'),
      )
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'Could not save profile',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleProjectSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!profile) return

    setIsSubmitting(true)
    setError(null)
    setNotice(null)
    const payload: CandidateProjectCreate = {
      name: projectForm.name.trim(),
      description: projectForm.description.trim(),
      technologies: commaSeparatedItems(projectForm.technologies),
      highlights: lineSeparatedItems(projectForm.highlights),
    }

    try {
      const savedProject = await createProject(profile.id, payload)
      setProjects((current) => [savedProject, ...current])
      setProjectForm(emptyProjectForm)
      setNotice('Project evidence added to the active profile.')
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'Could not add project',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  function startManualEdit() {
    if (!profile) return
    setProfileForm(profileToForm(profile))
    setResumeExtraction(null)
    setResumeProjectForms([])
    setIsEditingProfile(true)
    setError(null)
    setNotice(null)
  }

  function cancelProfileReview() {
    setProfileForm(emptyProfileForm)
    setResumeExtraction(null)
    setResumeProjectForms([])
    setSelectedResume(null)
    setIsEditingProfile(false)
    setError(null)
  }

  if (isLoading) {
    return <section className="profile-panel empty-state">Loading candidate data…</section>
  }

  const showProfileForm = !profile || isEditingProfile

  return (
    <section className="profile-panel" aria-labelledby="candidate-profile-heading">
      <div className="section-heading">
        <p className="step-label">03 · Build the evidence base</p>
        <h2 id="candidate-profile-heading">Candidate profile</h2>
        <p>Import your resume, review the draft, then save trusted evidence.</p>
      </div>

      <article className="resume-import-card">
        <div>
          <p className="profile-label">Recommended starting point</p>
          <h3>Import a resume</h3>
          <p>
            Upload a text-based PDF up to 5 MB. ApplyPilot extracts a draft for
            review—it never saves the original file.
          </p>
        </div>
        <form className="resume-upload-form" onSubmit={handleResumeSubmit}>
          <label>
            PDF resume
            <input
              accept=".pdf,application/pdf"
              required
              type="file"
              onChange={(event) => {
                setSelectedResume(event.target.files?.[0] ?? null)
                setError(null)
                setNotice(null)
              }}
            />
          </label>
          <button
            className="primary-button"
            disabled={!selectedResume || isExtracting}
            type="submit"
          >
            {isExtracting ? 'Extracting…' : 'Create review draft'}
          </button>
        </form>
      </article>

      {error && <p className="error-message">{error}</p>}
      {notice && <p className="success-message">{notice}</p>}

      {showProfileForm && (
        <form className="profile-form review-form" onSubmit={handleProfileSubmit}>
          <div className="review-heading">
            <div>
              <p className="profile-label">
                {resumeExtraction ? 'Resume draft · review required' : 'Manual profile'}
              </p>
              <h3>{profile ? 'Review profile update' : 'Create candidate profile'}</h3>
            </div>
            {resumeExtraction && <span>{resumeExtraction.page_count} page PDF</span>}
          </div>

          {resumeExtraction && (
            <ul className="extraction-warnings" aria-label="Resume extraction warnings">
              {resumeExtraction.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          )}

          <div className="form-row">
            <label>
              Full name
              <input
                required
                maxLength={120}
                value={profileForm.fullName}
                onChange={(event) =>
                  setProfileForm((current) => ({
                    ...current,
                    fullName: event.target.value,
                  }))
                }
                placeholder="Your name"
              />
            </label>
            <label>
              Headline <span>Optional</span>
              <input
                maxLength={160}
                value={profileForm.headline}
                onChange={(event) =>
                  setProfileForm((current) => ({
                    ...current,
                    headline: event.target.value,
                  }))
                }
                placeholder="Software Engineer"
              />
            </label>
          </div>
          <label>
            Professional summary
            <textarea
              required
              rows={4}
              maxLength={2000}
              value={profileForm.summary}
              onChange={(event) =>
                setProfileForm((current) => ({
                  ...current,
                  summary: event.target.value,
                }))
              }
              placeholder="What kinds of products and systems do you build?"
            />
          </label>
          <label>
            Skills <span>Comma separated</span>
            <input
              required
              value={profileForm.skills}
              onChange={(event) =>
                setProfileForm((current) => ({
                  ...current,
                  skills: event.target.value,
                }))
              }
              placeholder="Python, TypeScript, PostgreSQL"
            />
          </label>
          {resumeExtraction && (
            <section
              className="imported-project-review"
              aria-labelledby="project-drafts-heading"
            >
              <div className="project-review-heading">
                <div>
                  <p className="profile-label">Project evidence draft</p>
                  <h3 id="project-drafts-heading">
                    Review {resumeProjectForms.length} extracted project
                    {resumeProjectForms.length === 1 ? '' : 's'}
                  </h3>
                </div>
                <span>Saved in the same transaction</span>
              </div>
              {resumeProjectForms.length === 0 && (
                <p className="empty-project-draft">
                  No compatible project section was detected. You can add project
                  evidence after saving the profile.
                </p>
              )}
              {resumeProjectForms.map((project, index) => (
                <fieldset className="project-draft-card" key={`project-${index}`}>
                  <legend>Project {index + 1}</legend>
                  <button
                    className="remove-project-button"
                    type="button"
                    onClick={() =>
                      setResumeProjectForms((current) =>
                        current.filter((_, projectIndex) => projectIndex !== index),
                      )
                    }
                  >
                    Remove draft
                  </button>
                  <label>
                    Project name
                    <input
                      required
                      maxLength={160}
                      value={project.name}
                      onChange={(event) =>
                        setResumeProjectForms((current) =>
                          current.map((item, projectIndex) =>
                            projectIndex === index
                              ? { ...item, name: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </label>
                  <label>
                    Description
                    <textarea
                      required
                      rows={2}
                      maxLength={2000}
                      value={project.description}
                      onChange={(event) =>
                        setResumeProjectForms((current) =>
                          current.map((item, projectIndex) =>
                            projectIndex === index
                              ? { ...item, description: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </label>
                  <label>
                    Technologies <span>Comma separated</span>
                    <input
                      required
                      value={project.technologies}
                      onChange={(event) =>
                        setResumeProjectForms((current) =>
                          current.map((item, projectIndex) =>
                            projectIndex === index
                              ? { ...item, technologies: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </label>
                  <label>
                    Evidence highlights <span>One per line</span>
                    <textarea
                      required
                      rows={3}
                      value={project.highlights}
                      onChange={(event) =>
                        setResumeProjectForms((current) =>
                          current.map((item, projectIndex) =>
                            projectIndex === index
                              ? { ...item, highlights: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </label>
                </fieldset>
              ))}
            </section>
          )}
          <div className="form-actions">
            <button className="primary-button" disabled={isSubmitting} type="submit">
              {isSubmitting
                ? 'Saving…'
                : profile
                  ? 'Confirm profile update'
                  : 'Confirm and create profile'}
            </button>
            {profile && (
              <button
                className="secondary-button"
                disabled={isSubmitting}
                type="button"
                onClick={cancelProfileReview}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      )}

      {profile && !showProfileForm && (
        <div className="candidate-layout">
          <div>
            <article className="profile-card">
              <div className="profile-card-heading">
                <p className="profile-label">Active candidate</p>
                <button className="text-button" type="button" onClick={startManualEdit}>
                  Edit profile
                </button>
              </div>
              <h3>{profile.full_name}</h3>
              {profile.headline && <p className="profile-headline">{profile.headline}</p>}
              <p>{profile.summary}</p>
              <div className="tag-list" aria-label="Candidate skills">
                {profile.skills.map((skill) => (
                  <span key={skill}>{skill}</span>
                ))}
              </div>
            </article>

            <form className="project-form" onSubmit={handleProjectSubmit}>
              <h3>Add project evidence</h3>
              <label>
                Project name
                <input
                  required
                  maxLength={160}
                  value={projectForm.name}
                  onChange={(event) =>
                    setProjectForm((current) => ({
                      ...current,
                      name: event.target.value,
                    }))
                  }
                  placeholder="ApplyPilot"
                />
              </label>
              <label>
                Description
                <textarea
                  required
                  rows={3}
                  maxLength={2000}
                  value={projectForm.description}
                  onChange={(event) =>
                    setProjectForm((current) => ({
                      ...current,
                      description: event.target.value,
                    }))
                  }
                  placeholder="What did you build?"
                />
              </label>
              <label>
                Technologies <span>Comma separated</span>
                <input
                  required
                  value={projectForm.technologies}
                  onChange={(event) =>
                    setProjectForm((current) => ({
                      ...current,
                      technologies: event.target.value,
                    }))
                  }
                  placeholder="React, FastAPI, PostgreSQL"
                />
              </label>
              <label>
                Evidence highlights <span>One per line</span>
                <textarea
                  required
                  rows={4}
                  value={projectForm.highlights}
                  onChange={(event) =>
                    setProjectForm((current) => ({
                      ...current,
                      highlights: event.target.value,
                    }))
                  }
                  placeholder={'Built a persistent workflow.\nAdded integration tests.'}
                />
              </label>
              <button className="primary-button" disabled={isSubmitting} type="submit">
                {isSubmitting ? 'Saving…' : 'Add project'}
              </button>
            </form>
          </div>

          <div className="project-evidence-list">
            <h3>Project evidence</h3>
            {projects.length === 0 && (
              <p className="empty-state">No project evidence saved yet.</p>
            )}
            {projects.map((project) => (
              <article className="evidence-card" key={project.id}>
                <h3>{project.name}</h3>
                <p>{project.description}</p>
                <div className="tag-list" aria-label={`${project.name} technologies`}>
                  {project.technologies.map((technology) => (
                    <span key={technology}>{technology}</span>
                  ))}
                </div>
                <ul>
                  {project.highlights.map((highlight) => (
                    <li key={highlight}>{highlight}</li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
