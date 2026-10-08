import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from app.services.job_parser import parse_job_description


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    category: str
    description: str
    expected_skills: frozenset[str]


@dataclass(frozen=True)
class EvaluationResult:
    cases: int
    exact_match_cases: int
    expected_skills: int
    matched_skills: int
    predicted_skills: int
    precision: float
    recall: float
    exact_match_rate: float
    missed_skills: tuple[tuple[str, int], ...]
    unexpected_skills: tuple[tuple[str, int], ...]


DATASET_PATH = Path(__file__).with_name("data") / "job_parser_cases.json"


def load_cases(path: Path = DATASET_PATH) -> tuple[EvaluationCase, ...]:
    """Load the reference-labelled, version-controlled synthetic benchmark."""
    records = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        EvaluationCase(
            name=record["name"],
            category=record["category"],
            description=record["description"],
            expected_skills=frozenset(record["expected_skills"]),
        )
        for record in records
    )


CASES = load_cases()


def evaluate_rules_parser() -> EvaluationResult:
    matched = 0
    expected = 0
    predicted = 0
    exact_matches = 0
    missed: Counter[str] = Counter()
    unexpected: Counter[str] = Counter()

    for case in CASES:
        actual = set(parse_job_description(case.description).skills)
        missing_for_case = case.expected_skills - actual
        unexpected_for_case = actual - case.expected_skills
        matched += len(actual & case.expected_skills)
        expected += len(case.expected_skills)
        predicted += len(actual)
        exact_matches += actual == case.expected_skills
        missed.update(missing_for_case)
        unexpected.update(unexpected_for_case)

    return EvaluationResult(
        cases=len(CASES),
        exact_match_cases=exact_matches,
        expected_skills=expected,
        matched_skills=matched,
        predicted_skills=predicted,
        precision=matched / predicted if predicted else 0,
        recall=matched / expected if expected else 0,
        exact_match_rate=exact_matches / len(CASES) if CASES else 0,
        missed_skills=tuple(missed.most_common()),
        unexpected_skills=tuple(unexpected.most_common()),
    )


if __name__ == "__main__":
    result = evaluate_rules_parser()
    print(f"cases={result.cases}")
    print(f"skills={result.matched_skills}/{result.expected_skills}")
    print(f"precision={result.precision:.2%}")
    print(f"recall={result.recall:.2%}")
    print(
        "exact_match="
        f"{result.exact_match_cases}/{result.cases} ({result.exact_match_rate:.2%})"
    )
    print(f"missed_skills={dict(result.missed_skills)}")
    print(f"unexpected_skills={dict(result.unexpected_skills)}")
