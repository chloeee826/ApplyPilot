import { Link } from 'react-router-dom'
import type { SkillCoverage } from '../types/agentRun'

export function MatchScorecard({ coverage, stale }: { coverage: SkillCoverage | null | undefined; stale: boolean }) {
  if (!coverage || coverage.percentage === null) return (
    <section className="match-score-card" aria-label="Skill coverage">
      <h4>Score unavailable</h4>
      <p>This report needs complete evidence snapshots and at least one extracted job skill.
        {' '}<Link to="/jobs">Review the job analysis</Link> and generate a new report.</p>
    </section>
  )

  return (
    <>
      <section className="match-score-card" aria-label="Skill coverage">
        <div className="score-ring" style={{ background: `conic-gradient(#8eaccd ${coverage.percentage}%, #dee5d4 0)` }}>
          <div><strong data-testid="coverage-score">{coverage.percentage}%</strong><span>skill coverage</span></div>
        </div>
        <div className="score-explanation">
          <p className="eyebrow">{stale ? 'Historical evidence score · refresh needed' : 'Your evidence × this role'}</p>
          <h4>{coverage.role_title}</h4>
          <p>{coverage.company_name} · {coverage.candidate_name}</p>
          <strong>{coverage.supported_count} of {coverage.total_count} extracted skills have supporting evidence</strong>
          <p>{coverage.gaps.length === 0 ? 'All extracted skills have saved support. Review the other role requirements before applying.' :
            `${coverage.gaps.length} skill${coverage.gaps.length === 1 ? ' needs' : 's need'} stronger evidence for this role.`}</p>
          <p className="score-scope">Covers extracted technical skills only. Review the full JD for requirements the parser may miss.</p>
        </div>
        <details className="score-method">
          <summary>How this score works</summary>
          <p>Supported unique skills ÷ extracted unique job skills × 100. Each skill counts equally;
            known aliases count once. Support comes from the profile and project snapshots saved with this report.</p>
          <p>This measures listed technical evidence, not proficiency, overall job fit, or hiring probability.
            Seniority, years of experience, education, and requirement priority are not scored.
            Parsing can miss skills; review the JD before relying on the score.</p>
          <p>Scoring rules: {coverage.version}. Source matching uses the ontology version shown below.</p>
        </details>
      </section>
      <section className="match-gap-section" aria-label="Missing evidence for this role">
        <div className="gap-section-heading"><h4>What needs evidence for this role</h4><span>{coverage.gaps.length} gap{coverage.gaps.length === 1 ? '' : 's'}</span></div>
        {coverage.gaps.length === 0 ? <p>No gaps among the extracted skills. This is not a guarantee of qualification.</p> : (
          <div className="match-gap-list">
            {coverage.gaps.map((gap) => (
              <article className="match-gap-card" key={gap.skill}>
                <div className="gap-section-heading"><strong>{gap.skill}</strong><span className="gap-badge">No saved evidence</span></div>
                {gap.excerpts.length > 0 ? <div className="gap-excerpts">
                  <p>From {coverage.company_name}’s {coverage.role_title} posting:</p>
                  {gap.excerpts.map((excerpt) => <blockquote key={excerpt}>{excerpt}</blockquote>)}
                </div> : <p>This skill appears in the saved analysis. No matching JD excerpt was found; review the original posting.</p>}
                <p>If you have experience, <Link to="/candidate">add specific profile or project evidence</Link>.
                  Otherwise, prepare an honest gap explanation or build relevant experience.</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  )
}
