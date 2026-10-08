import json
import os
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import CandidateProfile, CandidateProject
from app.models.job import Job
from app.models.job_analysis import JobAnalysis


DEFAULT_AGENT_MODEL = "gpt-4o-mini"
DEMO_AGENT_MODEL = "demo-evidence-v1"
MAX_AGENT_STEPS = 6


class AgentConfigurationError(RuntimeError):
    """Raised when required agent configuration is missing."""


class AgentExecutionError(RuntimeError):
    """Raised when an agent run cannot produce a valid result."""


class JobMatchRecommendation(BaseModel):
    """Schema for the agent's final recommendation."""

    summary: str = Field(description="A concise, evidence-based fit assessment.")
    matched_skills: list[str] = Field(
        description="Skills supported by both the job and candidate evidence."
    )
    skill_gaps: list[str] = Field(
        description="Job skills or requirements not supported by candidate evidence."
    )
    project_evidence: list[str] = Field(
        description="Specific candidate project evidence relevant to this job."
    )
    interview_focus: list[str] = Field(
        description="Topics the candidate should prepare for an interview."
    )


@dataclass
class AgentResult:
    recommendation: JobMatchRecommendation
    tool_trace: list[dict[str, object]]
    model: str


class ResponsesClient(Protocol):
    def parse(self, **kwargs: object) -> object: ...


class OpenAIClient(Protocol):
    responses: ResponsesClient


AGENT_TOOLS: list[dict[str, object]] = [
    {
        "type": "function",
        "name": "get_job",
        "description": "Return the stored job posting for this agent run.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_job_analysis",
        "description": "Return structured skills and requirements extracted from the job.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_candidate_profile",
        "description": "Return the candidate's stored profile and skills.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
    {
        "type": "function",
        "name": "list_candidate_projects",
        "description": "Return project evidence stored for the candidate.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        "strict": True,
    },
]
REQUIRED_TOOL_NAMES = {str(tool["name"]) for tool in AGENT_TOOLS}


def _execute_tool(
    name: str,
    *,
    db: Session,
    job_id: UUID,
    profile_id: UUID,
) -> dict[str, object]:
    if name == "get_job":
        job = db.get(Job, job_id)
        if job is None:
            raise AgentExecutionError("Job disappeared during the agent run")
        return {
            "id": str(job.id),
            "company_name": job.company_name,
            "title": job.title,
            "description": job.description,
            "location": job.location,
            "source_url": job.source_url,
        }

    if name == "get_job_analysis":
        analysis = db.scalar(select(JobAnalysis).where(JobAnalysis.job_id == job_id))
        if analysis is None:
            raise AgentExecutionError("Job analysis is required before running the agent")
        return {
            "skills": analysis.skills,
            "requirements": analysis.requirements,
            "preferred_qualifications": analysis.preferred_qualifications,
            "responsibilities": analysis.responsibilities,
            "parser_version": analysis.parser_version,
        }

    if name == "get_candidate_profile":
        profile = db.get(CandidateProfile, profile_id)
        if profile is None:
            raise AgentExecutionError("Candidate profile disappeared during the agent run")
        return {
            "id": str(profile.id),
            "full_name": profile.full_name,
            "headline": profile.headline,
            "summary": profile.summary,
            "skills": profile.skills,
        }

    if name == "list_candidate_projects":
        projects = db.scalars(
            select(CandidateProject)
            .where(CandidateProject.profile_id == profile_id)
            .order_by(CandidateProject.created_at, CandidateProject.id)
        ).all()
        return {
            "projects": [
                {
                    "id": str(project.id),
                    "name": project.name,
                    "description": project.description,
                    "technologies": project.technologies,
                    "highlights": project.highlights,
                }
                for project in projects
            ]
        }

    raise AgentExecutionError(f"Unknown agent tool: {name}")


def _normalized_skill(value: str) -> str:
    return " ".join(value.lower().split())


def run_demo_job_match_agent(
    db: Session,
    job_id: UUID,
    profile_id: UUID,
) -> AgentResult:
    """Run the evidence workflow without an external model for local demos."""
    tool_trace: list[dict[str, object]] = []
    tool_outputs: dict[str, dict[str, object]] = {}

    for index, tool_name in enumerate(
        [
            "get_job",
            "get_job_analysis",
            "get_candidate_profile",
            "list_candidate_projects",
        ],
        start=1,
    ):
        output = _execute_tool(
            tool_name,
            db=db,
            job_id=job_id,
            profile_id=profile_id,
        )
        tool_outputs[tool_name] = output
        tool_trace.append(
            {
                "name": tool_name,
                "call_id": f"demo-call-{index}",
                "arguments": {},
                "output": output,
            }
        )

    analysis = tool_outputs["get_job_analysis"]
    profile = tool_outputs["get_candidate_profile"]
    projects_output = tool_outputs["list_candidate_projects"]

    job_skills = [str(skill) for skill in analysis["skills"]]
    candidate_skills = [str(skill) for skill in profile["skills"]]
    projects = list(projects_output["projects"])
    evidence_skill_keys = {_normalized_skill(skill) for skill in candidate_skills}

    for project in projects:
        evidence_skill_keys.update(
            _normalized_skill(str(technology))
            for technology in project["technologies"]
        )

    matched_skills = [
        skill for skill in job_skills if _normalized_skill(skill) in evidence_skill_keys
    ]
    skill_gaps = [
        skill for skill in job_skills if _normalized_skill(skill) not in evidence_skill_keys
    ]

    project_evidence: list[str] = []
    for project in projects:
        technology_keys = {
            _normalized_skill(str(technology))
            for technology in project["technologies"]
        }
        supported_skills = [
            skill for skill in job_skills if _normalized_skill(skill) in technology_keys
        ]
        if not supported_skills:
            continue

        highlights = [str(item) for item in project["highlights"]]
        evidence_detail = highlights[0] if highlights else str(project["description"])
        project_evidence.append(
            f"{project['name']}: {evidence_detail} "
            f"(supports {', '.join(supported_skills)})."
        )

    interview_focus = [
        f"Prepare evidence or an honest gap explanation for {skill}."
        for skill in skill_gaps[:3]
    ]
    interview_focus.extend(
        f"Be ready to discuss: {requirement}"
        for requirement in list(analysis["requirements"])[:3]
    )

    supported_count = len(matched_skills)
    total_count = len(job_skills)
    summary = (
        f"Stored evidence supports {supported_count} of {total_count} extracted job "
        "skills. Review the listed gaps before applying."
    )

    return AgentResult(
        recommendation=JobMatchRecommendation(
            summary=summary,
            matched_skills=matched_skills,
            skill_gaps=skill_gaps,
            project_evidence=project_evidence,
            interview_focus=interview_focus,
        ),
        tool_trace=tool_trace,
        model=DEMO_AGENT_MODEL,
    )


def run_job_match_agent(
    db: Session,
    job_id: UUID,
    profile_id: UUID,
    *,
    client: OpenAIClient | None = None,
    model: str | None = None,
    api_key: str | None = None,
    max_steps: int = MAX_AGENT_STEPS,
) -> AgentResult:
    """Run a bounded tool-calling loop and return a structured recommendation."""
    configured_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
    if client is None and not configured_key:
        raise AgentConfigurationError("OPENAI_API_KEY is not configured")

    openai_client = client or OpenAI(timeout=30.0, max_retries=1)
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_AGENT_MODEL)
    input_items: list[object] = [
        {
            "role": "user",
            "content": (
                "Evaluate this candidate for the selected job. Use every available "
                "tool before making claims. Base matches and gaps only on stored "
                "evidence, and return a concise recommendation."
            ),
        }
    ]
    tool_trace: list[dict[str, object]] = []

    try:
        for _ in range(max_steps):
            response = openai_client.responses.parse(
                model=selected_model,
                instructions=(
                    "You are ApplyPilot's job-match agent. Retrieve stored context "
                    "through tools. Never invent candidate experience."
                ),
                input=input_items,
                tools=AGENT_TOOLS,
                text_format=JobMatchRecommendation,
                parallel_tool_calls=True,
            )
            output = list(getattr(response, "output", []))
            input_items.extend(output)

            function_calls = [
                item for item in output if getattr(item, "type", None) == "function_call"
            ]
            if not function_calls:
                recommendation = getattr(response, "output_parsed", None)
                if recommendation is None:
                    raise AgentExecutionError("Agent returned no structured recommendation")
                called_tools = {str(item["name"]) for item in tool_trace}
                missing_tools = REQUIRED_TOOL_NAMES - called_tools
                if missing_tools:
                    names = ", ".join(sorted(missing_tools))
                    raise AgentExecutionError(
                        f"Agent did not call required tools: {names}"
                    )
                return AgentResult(
                    recommendation=recommendation,
                    tool_trace=tool_trace,
                    model=selected_model,
                )

            for call in function_calls:
                try:
                    arguments = json.loads(call.arguments or "{}")
                except json.JSONDecodeError as exc:
                    raise AgentExecutionError("Agent returned invalid tool arguments") from exc
                if not isinstance(arguments, dict) or arguments:
                    raise AgentExecutionError(
                        f"Tool {call.name} does not accept arguments"
                    )
                result = _execute_tool(
                    call.name,
                    db=db,
                    job_id=job_id,
                    profile_id=profile_id,
                )
                tool_trace.append(
                    {
                        "name": call.name,
                        "call_id": call.call_id,
                        "arguments": arguments,
                        "output": result,
                    }
                )
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(result),
                    }
                )
    except (OpenAIError, ValidationError) as exc:
        raise AgentExecutionError("OpenAI agent request failed") from exc

    raise AgentExecutionError(f"Agent exceeded the {max_steps}-step limit")
