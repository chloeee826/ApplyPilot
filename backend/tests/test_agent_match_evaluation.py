from urllib.parse import urlparse

from evals.agent_match_eval import (
    DEVELOPMENT_CASES,
    HOLDOUT_CASES,
    evaluate_demo_agent,
)


def test_demo_agent_meets_quality_baseline() -> None:
    result = evaluate_demo_agent(DEVELOPMENT_CASES)

    assert result.cases == len(DEVELOPMENT_CASES) == 12
    assert result.schema_valid_rate == 1.0
    assert result.required_tool_completion_rate == 1.0
    assert result.project_evidence_grounded_rate == 1.0
    assert result.match_precision == 1.0
    assert result.match_recall == 1.0
    assert result.gap_precision == 1.0
    assert result.gap_recall == 1.0
    assert result.exact_match_rate == 1.0


def test_agent_benchmark_resolves_labelled_aliases() -> None:
    result = evaluate_demo_agent(DEVELOPMENT_CASES)

    assert result.missed_matches == ()
    assert result.incorrect_gaps == ()


def test_holdout_dataset_has_independent_source_provenance() -> None:
    assert len(HOLDOUT_CASES) == 12
    assert {case.name for case in DEVELOPMENT_CASES}.isdisjoint(
        case.name for case in HOLDOUT_CASES
    )
    assert len({case.source_company for case in HOLDOUT_CASES}) >= 5

    for case in HOLDOUT_CASES:
        assert case.source_company
        assert case.source_role
        assert case.source_url
        assert urlparse(case.source_url).scheme == "https"
        assert case.accessed_on == "2026-10-09"
        assert case.expected_matches.isdisjoint(case.expected_gaps)
        assert case.expected_matches | case.expected_gaps == set(case.job_skills)


def test_holdout_agent_preserves_safety_invariants() -> None:
    result = evaluate_demo_agent(HOLDOUT_CASES)

    assert result.cases == len(HOLDOUT_CASES)
    assert result.schema_valid_rate == 1.0
    assert result.required_tool_completion_rate == 1.0
    assert result.match_precision == 1.0
    assert result.gap_recall == 1.0
