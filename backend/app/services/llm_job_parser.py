import os
from typing import Protocol

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

from app.services.job_parser import ParsedJobDescription, parse_job_description


LLM_PARSER_VERSION = "llm-v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class LLMJobAnalysis(BaseModel):
    """Schema the OpenAI response must follow."""

    skills: list[str] = Field(
        description="Canonical technical skills explicitly present in the posting."
    )
    requirements: list[str] = Field(
        description="Required qualifications stated by the employer."
    )
    preferred_qualifications: list[str] = Field(
        description="Qualifications described as preferred, optional, or a bonus."
    )
    responsibilities: list[str] = Field(
        description="Responsibilities and work the candidate would perform."
    )


class ParsedResponse(Protocol):
    output_parsed: LLMJobAnalysis | None


class ResponsesClient(Protocol):
    def parse(self, **kwargs: object) -> ParsedResponse: ...


class OpenAIClient(Protocol):
    responses: ResponsesClient


def _clean_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = item.strip()
        normalized = value.casefold()
        if not value or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(value)
    return cleaned


def parse_job_description_with_llm(
    description: str,
    *,
    client: OpenAIClient | None = None,
    model: str | None = None,
) -> ParsedJobDescription:
    """Use OpenAI Structured Outputs to extract the JobAnalysis contract."""
    openai_client = client or OpenAI(timeout=20.0, max_retries=1)
    selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    response = openai_client.responses.parse(
        model=selected_model,
        input=[
            {
                "role": "system",
                "content": (
                    "Extract only information explicitly present in the job posting. "
                    "Do not infer missing skills or qualifications. Preserve concise "
                    "source wording for requirements and responsibilities."
                ),
            },
            {"role": "user", "content": description},
        ],
        text_format=LLMJobAnalysis,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI returned no parsed job analysis")

    return ParsedJobDescription(
        skills=_clean_items(parsed.skills),
        requirements=_clean_items(parsed.requirements),
        preferred_qualifications=_clean_items(parsed.preferred_qualifications),
        responsibilities=_clean_items(parsed.responsibilities),
    )


def parse_job_description_with_fallback(
    description: str,
    *,
    client: OpenAIClient | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> tuple[ParsedJobDescription, str]:
    """Prefer Structured Outputs and fall back to the deterministic parser."""
    configured_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
    if client is None and not configured_key:
        return parse_job_description(description), "rules-v1"

    try:
        parsed = parse_job_description_with_llm(
            description,
            client=client,
            model=model,
        )
        selected_model = model or os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        return parsed, f"{LLM_PARSER_VERSION}:{selected_model}"
    except (OpenAIError, RuntimeError, ValidationError):
        return parse_job_description(description), "rules-v1"
