from evals.job_parser_eval import CASES, evaluate_rules_parser


def test_rules_parser_meets_baseline_skill_evaluation() -> None:
    result = evaluate_rules_parser()

    assert result.cases == len(CASES) == 4
    assert result.precision == 1.0
    assert result.recall == 1.0
