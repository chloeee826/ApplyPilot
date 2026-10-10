from evals.agent_match_eval import CASES, evaluate_demo_agent


def test_demo_agent_meets_quality_baseline() -> None:
    result = evaluate_demo_agent()

    assert result.cases == len(CASES) == 12
    assert result.schema_valid_rate == 1.0
    assert result.required_tool_completion_rate == 1.0
    assert result.project_evidence_grounded_rate == 1.0
    assert result.match_precision == 1.0
    assert result.match_recall >= 0.80
    assert result.gap_precision >= 0.50
    assert result.gap_recall == 1.0
    assert result.exact_match_rate >= 0.65


def test_agent_benchmark_retains_alias_failures() -> None:
    result = evaluate_demo_agent()

    missed = dict(result.missed_matches)
    assert missed["postgres"] == 1
    assert missed["react.js"] == 1
    assert missed["node.js"] == 1
    assert missed["rest api"] == 1
