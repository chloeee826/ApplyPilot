import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from evals.agent_match_eval import (
    BLIND_V1_CASES,
    DEVELOPMENT_CASES,
    VALIDATION_CASES,
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


def test_validation_dataset_has_independent_source_provenance() -> None:
    assert len(VALIDATION_CASES) == 12
    assert {case.name for case in DEVELOPMENT_CASES}.isdisjoint(
        case.name for case in VALIDATION_CASES
    )
    assert len({case.source_company for case in VALIDATION_CASES}) >= 5

    for case in VALIDATION_CASES:
        assert case.source_company
        assert case.source_role
        assert case.source_url
        assert urlparse(case.source_url).scheme == "https"
        assert case.accessed_on == "2026-10-09"
        assert case.expected_matches.isdisjoint(case.expected_gaps)
        assert case.expected_matches | case.expected_gaps == set(case.job_skills)


def test_validation_agent_meets_v3_quality_baseline() -> None:
    result = evaluate_demo_agent(VALIDATION_CASES)

    assert result.cases == len(VALIDATION_CASES)
    assert result.schema_valid_rate == 1.0
    assert result.required_tool_completion_rate == 1.0
    assert result.match_precision == 1.0
    assert result.match_recall == 1.0
    assert result.gap_precision == 1.0
    assert result.gap_recall == 1.0
    assert result.exact_match_rate == 1.0
    assert result.project_evidence_grounded_rate == 1.0


def test_blind_v1_dataset_is_frozen_with_independent_provenance() -> None:
    assert len(BLIND_V1_CASES) == 12
    assert len({case.source_company for case in BLIND_V1_CASES}) == 12
    assert {case.name for case in DEVELOPMENT_CASES}.isdisjoint(
        case.name for case in BLIND_V1_CASES
    )
    assert {case.name for case in VALIDATION_CASES}.isdisjoint(
        case.name for case in BLIND_V1_CASES
    )
    assert {case.source_company for case in VALIDATION_CASES}.isdisjoint(
        case.source_company for case in BLIND_V1_CASES
    )

    for case in BLIND_V1_CASES:
        assert case.source_company
        assert case.source_role
        assert case.source_url
        assert case.accessed_on == "2026-10-09"
        assert case.expected_matches | case.expected_gaps == set(case.job_skills)


def test_blind_v1_historical_baseline_pins_the_frozen_dataset() -> None:
    eval_root = Path(__file__).parents[1] / "evals"
    dataset_path = eval_root / "data" / "agent_match_blind_v1_cases.json"
    result_path = eval_root / "results" / "agent_match_blind_v1_baseline.json"
    baseline = json.loads(result_path.read_text(encoding="utf-8"))

    assert baseline["labels_frozen_before_first_run"] is True
    assert baseline["agent_version"] == "demo-evidence-v3"
    assert baseline["skill_ontology_version"] == "skills-v1"
    assert baseline["cases"] == 12
    assert baseline["source_companies"] == 12
    assert baseline["match_precision"] == 1.0
    assert baseline["match_recall"] == 0.875
    assert baseline["dataset_sha256"] == hashlib.sha256(
        dataset_path.read_bytes()
    ).hexdigest()


def test_former_blind_split_improves_with_safe_aliases_only() -> None:
    result = evaluate_demo_agent(BLIND_V1_CASES)
    assert result.match_precision == 1.0
    assert result.match_recall == 0.975
    assert result.exact_match_cases == 10
    assert dict(result.missed_matches) == {"react query": 1, "apollo": 1}
    assert result.schema_valid_rate == 1.0
    assert result.required_tool_completion_rate == 1.0
