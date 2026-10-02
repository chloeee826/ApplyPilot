from dataclasses import dataclass

from app.services.job_parser import parse_job_description


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    description: str
    expected_skills: frozenset[str]


@dataclass(frozen=True)
class EvaluationResult:
    cases: int
    expected_skills: int
    matched_skills: int
    predicted_skills: int
    precision: float
    recall: float


CASES = (
    EvaluationCase(
        name="backend",
        description=(
            "Build REST APIs with Python, FastAPI, SQL, and PostgreSQL. "
            "Experience with Docker and AWS is preferred."
        ),
        expected_skills=frozenset(
            {"Python", "FastAPI", "SQL", "PostgreSQL", "Docker", "AWS", "REST APIs"}
        ),
    ),
    EvaluationCase(
        name="frontend",
        description="Develop React applications using TypeScript and JavaScript.",
        expected_skills=frozenset({"React", "TypeScript", "JavaScript"}),
    ),
    EvaluationCase(
        name="mobile",
        description="Build Android applications with Java and Firebase.",
        expected_skills=frozenset({"Android", "Java", "Firebase"}),
    ),
    EvaluationCase(
        name="platform",
        description="Maintain AWS, Docker, Kubernetes, Git, and CI/CD workflows.",
        expected_skills=frozenset({"AWS", "Docker", "Kubernetes", "Git", "CI/CD"}),
    ),
)


def evaluate_rules_parser() -> EvaluationResult:
    matched = 0
    expected = 0
    predicted = 0

    for case in CASES:
        actual = set(parse_job_description(case.description).skills)
        matched += len(actual & case.expected_skills)
        expected += len(case.expected_skills)
        predicted += len(actual)

    return EvaluationResult(
        cases=len(CASES),
        expected_skills=expected,
        matched_skills=matched,
        predicted_skills=predicted,
        precision=matched / predicted if predicted else 0,
        recall=matched / expected if expected else 0,
    )


if __name__ == "__main__":
    result = evaluate_rules_parser()
    print(f"cases={result.cases}")
    print(f"skills={result.matched_skills}/{result.expected_skills}")
    print(f"precision={result.precision:.2%}")
    print(f"recall={result.recall:.2%}")
