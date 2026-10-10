import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.candidate import CandidateProfile, CandidateProject
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.services.job_match_agent import (
    REQUIRED_TOOL_NAMES,
    JobMatchRecommendation,
    run_demo_job_match_agent,
)


@dataclass(frozen=True)
class ProjectFixture:
    name: str
    description: str
    technologies: tuple[str, ...]
    highlights: tuple[str, ...]


@dataclass(frozen=True)
class AgentEvaluationCase:
    name: str
    category: str
    job_skills: tuple[str, ...]
    candidate_skills: tuple[str, ...]
    projects: tuple[ProjectFixture, ...]
    expected_matches: frozenset[str]
    expected_gaps: frozenset[str]


@dataclass(frozen=True)
class AgentEvaluationResult:
    cases: int
    exact_match_cases: int
    schema_valid_cases: int
    required_tool_complete_cases: int
    expected_matches: int
    predicted_matches: int
    correct_matches: int
    expected_gaps: int
    predicted_gaps: int
    correct_gaps: int
    project_evidence_items: int
    grounded_project_evidence_items: int
    match_precision: float
    match_recall: float
    gap_precision: float
    gap_recall: float
    exact_match_rate: float
    schema_valid_rate: float
    required_tool_completion_rate: float
    project_evidence_grounded_rate: float
    missed_matches: tuple[tuple[str, int], ...]
    incorrect_gaps: tuple[tuple[str, int], ...]


DATASET_PATH = Path(__file__).with_name("data") / "agent_match_cases.json"


def _skill_key(value: str) -> str:
    return " ".join(value.casefold().split())


def _keyed(values: list[str] | tuple[str, ...] | frozenset[str]) -> set[str]:
    return {_skill_key(value) for value in values}


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 1.0


def load_cases(path: Path = DATASET_PATH) -> tuple[AgentEvaluationCase, ...]:
    """Load the version-controlled job/candidate matching benchmark."""
    records = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        AgentEvaluationCase(
            name=record["name"],
            category=record["category"],
            job_skills=tuple(record["job_skills"]),
            candidate_skills=tuple(record["candidate_skills"]),
            projects=tuple(
                ProjectFixture(
                    name=project["name"],
                    description=project["description"],
                    technologies=tuple(project["technologies"]),
                    highlights=tuple(project["highlights"]),
                )
                for project in record["projects"]
            ),
            expected_matches=frozenset(record["expected_matches"]),
            expected_gaps=frozenset(record["expected_gaps"]),
        )
        for record in records
    )


CASES = load_cases()


def _seed_case(db: Session, case: AgentEvaluationCase) -> tuple[Job, CandidateProfile]:
    job = Job(
        company_name="Evaluation Company",
        title=f"{case.category.title()} Engineer",
        description=f"Evaluation case requiring {', '.join(case.job_skills)}.",
    )
    profile = CandidateProfile(
        full_name="Evaluation Candidate",
        headline="Software Engineer",
        summary="Reference-labelled candidate evidence for agent evaluation.",
        skills=list(case.candidate_skills),
    )
    db.add_all([job, profile])
    db.flush()
    db.add(
        JobAnalysis(
            job_id=job.id,
            skills=list(case.job_skills),
            requirements=["Provide evidence for every claimed skill."],
            preferred_qualifications=[],
            responsibilities=["Build reliable software."],
            parser_version="eval-reference-v1",
        )
    )
    db.add_all(
        CandidateProject(
            profile_id=profile.id,
            name=project.name,
            description=project.description,
            technologies=list(project.technologies),
            highlights=list(project.highlights),
        )
        for project in case.projects
    )
    db.commit()
    return job, profile


def evaluate_demo_agent(
    cases: tuple[AgentEvaluationCase, ...] = CASES,
) -> AgentEvaluationResult:
    """Evaluate the reproducible agent path against labelled match expectations."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    exact_cases = 0
    schema_valid_cases = 0
    tool_complete_cases = 0
    expected_matches = 0
    predicted_matches = 0
    correct_matches = 0
    expected_gaps = 0
    predicted_gaps = 0
    correct_gaps = 0
    evidence_items = 0
    grounded_evidence_items = 0
    missed_matches: Counter[str] = Counter()
    incorrect_gaps: Counter[str] = Counter()

    try:
        with Session(engine) as db:
            for case in cases:
                job, profile = _seed_case(db, case)
                result = run_demo_job_match_agent(db, job.id, profile.id)
                recommendation = result.recommendation

                JobMatchRecommendation.model_validate(recommendation.model_dump())
                schema_valid_cases += 1

                called_tools = {str(item["name"]) for item in result.tool_trace}
                if called_tools == REQUIRED_TOOL_NAMES:
                    tool_complete_cases += 1

                expected_match_keys = _keyed(case.expected_matches)
                expected_gap_keys = _keyed(case.expected_gaps)
                actual_match_keys = _keyed(recommendation.matched_skills)
                actual_gap_keys = _keyed(recommendation.skill_gaps)

                expected_matches += len(expected_match_keys)
                predicted_matches += len(actual_match_keys)
                correct_matches += len(expected_match_keys & actual_match_keys)
                expected_gaps += len(expected_gap_keys)
                predicted_gaps += len(actual_gap_keys)
                correct_gaps += len(expected_gap_keys & actual_gap_keys)

                if (
                    actual_match_keys == expected_match_keys
                    and actual_gap_keys == expected_gap_keys
                ):
                    exact_cases += 1

                missed_matches.update(expected_match_keys - actual_match_keys)
                incorrect_gaps.update(actual_gap_keys - expected_gap_keys)

                project_names = [project.name.casefold() for project in case.projects]
                for item in recommendation.project_evidence:
                    evidence_items += 1
                    if any(name in item.casefold() for name in project_names):
                        grounded_evidence_items += 1
    finally:
        engine.dispose()

    case_count = len(cases)
    return AgentEvaluationResult(
        cases=case_count,
        exact_match_cases=exact_cases,
        schema_valid_cases=schema_valid_cases,
        required_tool_complete_cases=tool_complete_cases,
        expected_matches=expected_matches,
        predicted_matches=predicted_matches,
        correct_matches=correct_matches,
        expected_gaps=expected_gaps,
        predicted_gaps=predicted_gaps,
        correct_gaps=correct_gaps,
        project_evidence_items=evidence_items,
        grounded_project_evidence_items=grounded_evidence_items,
        match_precision=_ratio(correct_matches, predicted_matches),
        match_recall=_ratio(correct_matches, expected_matches),
        gap_precision=_ratio(correct_gaps, predicted_gaps),
        gap_recall=_ratio(correct_gaps, expected_gaps),
        exact_match_rate=_ratio(exact_cases, case_count),
        schema_valid_rate=_ratio(schema_valid_cases, case_count),
        required_tool_completion_rate=_ratio(tool_complete_cases, case_count),
        project_evidence_grounded_rate=_ratio(
            grounded_evidence_items, evidence_items
        ),
        missed_matches=tuple(missed_matches.most_common()),
        incorrect_gaps=tuple(incorrect_gaps.most_common()),
    )


if __name__ == "__main__":
    result = evaluate_demo_agent()
    print(f"cases={result.cases}")
    print(
        "exact_match="
        f"{result.exact_match_cases}/{result.cases} ({result.exact_match_rate:.2%})"
    )
    print(f"match_precision={result.match_precision:.2%}")
    print(f"match_recall={result.match_recall:.2%}")
    print(f"gap_precision={result.gap_precision:.2%}")
    print(f"gap_recall={result.gap_recall:.2%}")
    print(f"schema_valid={result.schema_valid_rate:.2%}")
    print(f"required_tool_completion={result.required_tool_completion_rate:.2%}")
    print(
        "project_evidence_grounded="
        f"{result.project_evidence_grounded_rate:.2%} "
        f"({result.grounded_project_evidence_items}/{result.project_evidence_items})"
    )
    print(f"missed_matches={dict(result.missed_matches)}")
    print(f"incorrect_gaps={dict(result.incorrect_gaps)}")
