from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.candidate import CandidateProfile, CandidateProject
from app.models.job import Job
from app.models.job_analysis import JobAnalysis
from app.services.job_match_agent import (
    AGENT_TOOLS,
    DEMO_AGENT_MODEL,
    AgentConfigurationError,
    AgentExecutionError,
    JobMatchRecommendation,
    run_demo_job_match_agent,
    run_job_match_agent,
)


class FakeResponses:
    def __init__(self, responses: list[object]) -> None:
        self._responses = iter(responses)
        self.requests: list[dict[str, object]] = []

    def parse(self, **kwargs: object) -> object:
        self.requests.append(kwargs)
        return next(self._responses)


class FakeOpenAI:
    def __init__(self, responses: list[object]) -> None:
        self.responses = FakeResponses(responses)


def function_call(name: str, call_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        type="function_call",
        name=name,
        call_id=call_id,
        arguments="{}",
    )


@pytest.fixture
def seeded_session() -> tuple[Session, Job, CandidateProfile]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = Session(engine)

    job = Job(
        company_name="Example Co",
        title="Backend Engineer",
        description="Build Python APIs with PostgreSQL.",
    )
    profile = CandidateProfile(
        full_name="Chloe Example",
        headline="Software Engineer",
        summary="Builds full-stack products.",
        skills=["Python", "TypeScript"],
    )
    session.add_all([job, profile])
    session.flush()
    session.add_all(
        [
            JobAnalysis(
                job_id=job.id,
                skills=["Python", "PostgreSQL"],
                requirements=["Experience building APIs"],
                preferred_qualifications=[],
                responsibilities=["Build backend services"],
                parser_version="rules-v1",
            ),
            CandidateProject(
                profile_id=profile.id,
                name="ApplyPilot",
                description="A job search platform.",
                technologies=["Python", "FastAPI", "PostgreSQL"],
                highlights=["Built persistent job tracking."],
            ),
        ]
    )
    session.commit()

    yield session, job, profile

    session.close()
    engine.dispose()


def test_agent_executes_all_tools_and_returns_structured_result(
    seeded_session: tuple[Session, Job, CandidateProfile],
) -> None:
    session, job, profile = seeded_session
    first_response = SimpleNamespace(
        output=[
            function_call("get_job", "call-job"),
            function_call("get_job_analysis", "call-analysis"),
            function_call("get_candidate_profile", "call-profile"),
            function_call("list_candidate_projects", "call-projects"),
        ],
        output_parsed=None,
    )
    recommendation = JobMatchRecommendation(
        summary="Strong Python match with a PostgreSQL evidence gap.",
        matched_skills=["Python"],
        skill_gaps=["PostgreSQL"],
        project_evidence=["ApplyPilot uses FastAPI and PostgreSQL."],
        interview_focus=["Explain database design decisions."],
    )
    final_response = SimpleNamespace(output=[], output_parsed=recommendation)
    client = FakeOpenAI([first_response, final_response])

    result = run_job_match_agent(
        session,
        job.id,
        profile.id,
        client=client,
        model="test-model",
    )

    assert result.recommendation == recommendation
    assert result.model == "test-model"
    assert [item["name"] for item in result.tool_trace] == [
        "get_job",
        "get_job_analysis",
        "get_candidate_profile",
        "list_candidate_projects",
    ]
    assert result.tool_trace[3]["output"]["projects"][0]["name"] == "ApplyPilot"
    assert len(client.responses.requests) == 2
    second_input = client.responses.requests[1]["input"]
    assert any(
        isinstance(item, dict) and item.get("type") == "function_call_output"
        for item in second_input
    )


def test_demo_agent_uses_all_stored_evidence_without_an_api_key(
    seeded_session: tuple[Session, Job, CandidateProfile],
) -> None:
    session, job, profile = seeded_session

    result = run_demo_job_match_agent(session, job.id, profile.id)

    assert result.model == DEMO_AGENT_MODEL
    assert result.recommendation.matched_skills == ["Python", "PostgreSQL"]
    assert result.recommendation.skill_gaps == []
    assert result.recommendation.project_evidence == [
        "ApplyPilot: Built persistent job tracking. (supports Python, PostgreSQL)."
    ]
    assert [item["name"] for item in result.tool_trace] == [
        "get_job",
        "get_job_analysis",
        "get_candidate_profile",
        "list_candidate_projects",
    ]
    assert result.recommendation.summary.startswith("Stored evidence supports 2 of 2")


def test_tool_definitions_are_strict_and_scoped() -> None:
    assert {tool["name"] for tool in AGENT_TOOLS} == {
        "get_job",
        "get_job_analysis",
        "get_candidate_profile",
        "list_candidate_projects",
    }
    assert all(tool["strict"] is True for tool in AGENT_TOOLS)
    assert all(tool["parameters"]["additionalProperties"] is False for tool in AGENT_TOOLS)


def test_agent_rejects_unknown_tool(
    seeded_session: tuple[Session, Job, CandidateProfile],
) -> None:
    session, job, profile = seeded_session
    client = FakeOpenAI(
        [
            SimpleNamespace(
                output=[function_call("delete_everything", "call-unsafe")],
                output_parsed=None,
            )
        ]
    )

    with pytest.raises(AgentExecutionError, match="Unknown agent tool"):
        run_job_match_agent(session, job.id, profile.id, client=client)


def test_agent_stops_at_step_limit(
    seeded_session: tuple[Session, Job, CandidateProfile],
) -> None:
    session, job, profile = seeded_session
    client = FakeOpenAI(
        [
            SimpleNamespace(
                output=[function_call("get_job", str(uuid4()))],
                output_parsed=None,
            )
        ]
    )

    with pytest.raises(AgentExecutionError, match="step limit"):
        run_job_match_agent(
            session,
            job.id,
            profile.id,
            client=client,
            max_steps=1,
        )


def test_agent_requires_api_key_without_injected_client(
    seeded_session: tuple[Session, Job, CandidateProfile],
) -> None:
    session, job, profile = seeded_session

    with pytest.raises(AgentConfigurationError, match="OPENAI_API_KEY"):
        run_job_match_agent(session, job.id, profile.id, api_key="")


def test_agent_cannot_skip_required_evidence_tools(
    seeded_session: tuple[Session, Job, CandidateProfile],
) -> None:
    session, job, profile = seeded_session
    client = FakeOpenAI(
        [
            SimpleNamespace(
                output=[],
                output_parsed=JobMatchRecommendation(
                    summary="Unsupported conclusion.",
                    matched_skills=[],
                    skill_gaps=[],
                    project_evidence=[],
                    interview_focus=[],
                ),
            )
        ]
    )

    with pytest.raises(AgentExecutionError, match="did not call required tools"):
        run_job_match_agent(session, job.id, profile.id, client=client)
