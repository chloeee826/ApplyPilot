from evals.job_parser_eval import CASES, evaluate_rules_parser


def test_rules_parser_meets_baseline_skill_evaluation() -> None:
    result = evaluate_rules_parser()

    assert result.cases == len(CASES) == 20
    assert result.precision >= 0.95
    assert result.recall >= 0.65
    assert result.exact_match_rate >= 0.20
