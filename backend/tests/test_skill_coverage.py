from app.services.skill_coverage import calculate_coverage


def trace(skills, candidate_skills, technologies=None, description="Build Python. Docker preferred."):
    return [
        {"name": "get_job", "output": {"id": "j1", "title": "Backend Engineer",
            "company_name": "Example Co", "description": description}},
        {"name": "get_job_analysis", "output": {"skills": skills}},
        {"name": "get_candidate_profile", "output": {"id": "p1", "full_name": "Candidate", "skills": candidate_skills}},
        {"name": "list_candidate_projects", "output": {"projects": [] if technologies is None else [
            {"id": "project1", "name": "API", "technologies": technologies}] }},
    ]


def test_coverage_uses_unique_skills_and_project_aliases():
    coverage = calculate_coverage(trace(["Python", "Postgres", "PostgreSQL", "Docker"], ["Python"], ["PostgreSQL"]), "j1", "p1")
    assert coverage.total_count == 3
    assert coverage.supported_count == 2
    assert coverage.percentage == 66.7
    assert coverage.supported[1].sources[0].source_type == "project"
    assert coverage.gaps[0].skill == "Docker"
    assert coverage.gaps[0].excerpts == ["Docker preferred."]
    assert coverage.role_title == "Backend Engineer"


def test_no_extracted_skills_has_no_score():
    coverage = calculate_coverage(trace([], ["Python"]), "j1", "p1")
    assert coverage.percentage is None
    assert coverage.total_count == 0


def test_false_friend_and_jd_excerpt_do_not_match_javascript_to_java():
    coverage = calculate_coverage(trace(["Java"], ["JavaScript"], description="Build JavaScript interfaces. Java is required."), "j1", "p1")
    assert coverage.percentage == 0
    assert coverage.gaps[0].excerpts == ["Java is required."]


def test_missing_or_wrong_scoped_snapshots_have_no_score():
    assert calculate_coverage([], "j1", "p1") is None
    assert calculate_coverage(trace(["Python"], ["Python"]), "other-job", "p1") is None
    assert calculate_coverage(trace(["Python"], ["Python"]), "j1", "other-profile") is None


def test_model_match_claim_does_not_determine_score():
    # No final model claims enter the scoring function.
    coverage = calculate_coverage(trace(["Docker"], ["Python"]), "j1", "p1")
    assert coverage.percentage == 0
    assert coverage.supported == []
    full = calculate_coverage(trace(["Python"], ["Python"]), "j1", "p1")
    assert full.percentage == 100
    assert full.gaps == []
