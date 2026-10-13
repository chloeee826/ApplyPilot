from app.services.match_evidence import explain_matches


def test_sources_preserve_original_alias_and_distinguish_profile_from_projects():
    trace = [
        {"name": "get_candidate_profile", "output": {
            "id": "profile-1", "full_name": "Candidate", "skills": ["Postgres", "JavaScript"]}},
        {"name": "list_candidate_projects", "output": {"projects": [
            {"id": "project-1", "name": "Database API", "technologies": ["PostgreSQL", "Python"]}]}},
    ]
    evidence = explain_matches(["PostgreSQL", "Python", "Java"], trace, "profile-1")
    assert [(s.source_type, s.original_skill) for s in evidence[0].sources] == [
        ("profile", "Postgres"), ("project", "PostgreSQL")]
    assert evidence[1].sources[0].source_id == "project-1"
    assert evidence[2].sources == []


def test_missing_malformed_or_wrong_profile_trace_does_not_invent_support():
    trace = [
        {"name": "get_candidate_profile", "output": {
            "id": "other-profile", "full_name": "Other", "skills": ["Python"]}},
        {"name": "list_candidate_projects", "output": {"projects": [None, {
            "id": "project-1", "name": "Project", "technologies": "Python"}]}},
        {"name": "get_candidate_profile", "output": None},
    ]
    assert explain_matches(["Python"], trace, "profile-1")[0].sources == []
    assert explain_matches(["Python"], [], "profile-1")[0].sources == []


def test_source_details_are_copied_from_snapshot_and_malformed_lists_are_filtered():
    trace = [{"name": "list_candidate_projects", "output": {"projects": [{
        "id": "p1", "name": "API", "description": "Built a database API.",
        "technologies": ["Postgres", 42],
        "highlights": ["Added transaction handling.", None],
    }]}}]
    source = explain_matches(["PostgreSQL"], trace, "profile-1")[0].sources[0]
    assert source.description == "Built a database API."
    assert source.technologies == ["Postgres"]
    assert source.highlights == ["Added transaction handling."]
    assert source.original_skill == "Postgres"


def test_legacy_snapshot_without_details_keeps_its_source():
    trace = [{"name": "get_candidate_profile", "output": {
        "id": "profile-1", "full_name": "Candidate", "skills": ["Python"],
    }}]
    source = explain_matches(["Python"], trace, "profile-1")[0].sources[0]
    assert source.description is None
    assert source.highlights == []
