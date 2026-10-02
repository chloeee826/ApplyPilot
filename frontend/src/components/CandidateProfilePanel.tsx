import { useEffect, useState, type FormEvent } from 'react'

import {
  createProfile,
  createProject,
  listProfiles,
  listProjects,
} from '../api/profiles'
import type {
  CandidateProfile,
  CandidateProfileCreate,
  CandidateProject,
  CandidateProjectCreate,
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

export function CandidateProfilePanel() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null)
  const [projects, setProjects] = useState<CandidateProject[]>([])
  const [profileForm, setProfileForm] = useState<ProfileForm>(emptyProfileForm)
  const [projectForm, setProjectForm] = useState<ProjectForm>(emptyProjectForm)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

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

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)

    const payload: CandidateProfileCreate = {
      full_name: profileForm.fullName.trim(),
      summary: profileForm.summary.trim(),
      skills: commaSeparatedItems(profileForm.skills),
    }
    if (profileForm.headline.trim()) payload.headline = profileForm.headline.trim()

    try {
      const savedProfile = await createProfile(payload)
      setProfile(savedProfile)
      setProfileForm(emptyProfileForm)
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'Could not create profile',
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
    } catch (submitError) {
      setError(
        submitError instanceof Error ? submitError.message : 'Could not add project',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return <section className="profile-panel empty-state">Loading candidate data…</section>
  }

  return (
    <section className="profile-panel" aria-labelledby="candidate-profile-heading">
      <div className="section-heading">
        <p className="step-label">03 · Build the evidence base</p>
        <h2 id="candidate-profile-heading">Candidate profile</h2>
        <p>Give future agent recommendations a factual source to retrieve from.</p>
      </div>

      {error && <p className="error-message">{error}</p>}

      {!profile ? (
        <form className="profile-form" onSubmit={handleProfileSubmit}>
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
          <button className="primary-button" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Saving…' : 'Create profile'}
          </button>
        </form>
      ) : (
        <div className="candidate-layout">
          <div>
            <article className="profile-card">
              <p className="profile-label">Active candidate</p>
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
