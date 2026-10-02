from types import SimpleNamespace

from app.services.llm_job_parser import (
    LLMJobAnalysis,
    parse_job_description_with_fallback,
    parse_job_description_with_llm,
)


class FakeResponses:
    def __init__(self, parsed: LLMJobAnalysis | None) -> None:
        self.parsed = parsed
        self.request: dict[str, object] | None = None

    def parse(self, **kwargs: object):
        self.request = kwargs
        return SimpleNamespace(output_parsed=self.parsed)


class FakeClient:
    def __init__(self, parsed: LLMJobAnalysis | None) -> None:
        self.responses = FakeResponses(parsed)


class FailingResponses:
    def parse(self, **_: object):
        raise RuntimeError("Simulated unavailable model")


class FailingClient:
    responses = FailingResponses()


def test_llm_parser_uses_structured_output_schema() -> None:
    client = FakeClient(
        LLMJobAnalysis(
            skills=["Python", "Python", " PostgreSQL "],
            requirements=["3 years of backend experience."],
            preferred_qualifications=["AWS experience is preferred."],
            responsibilities=["Build reliable APIs."],
        )
    )

    parsed = parse_job_description_with_llm(
        "A backend engineering job.",
        client=client,
        model="test-model",
    )

    assert parsed.skills == ["Python", "PostgreSQL"]
    assert parsed.responsibilities == ["Build reliable APIs."]
    assert client.responses.request is not None
    assert client.responses.request["model"] == "test-model"
    assert client.responses.request["text_format"] is LLMJobAnalysis


def test_auto_parser_records_llm_model_version() -> None:
    client = FakeClient(
        LLMJobAnalysis(
            skills=["Python"],
            requirements=[],
            preferred_qualifications=[],
            responsibilities=["Build APIs."],
        )
    )

    parsed, version = parse_job_description_with_fallback(
        "Build APIs with Python.",
        client=client,
        model="test-model",
    )

    assert parsed.skills == ["Python"]
    assert version == "llm-v1:test-model"


def test_auto_parser_uses_rules_without_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    parsed, version = parse_job_description_with_fallback(
        "Build REST APIs with Python."
    )

    assert parsed.skills == ["Python", "REST APIs"]
    assert version == "rules-v1"


def test_auto_parser_falls_back_when_llm_returns_no_output() -> None:
    parsed, version = parse_job_description_with_fallback(
        "Build REST APIs with Python.",
        client=FakeClient(None),
        model="test-model",
    )

    assert parsed.skills == ["Python", "REST APIs"]
    assert version == "rules-v1"


def test_auto_parser_falls_back_when_llm_request_fails() -> None:
    parsed, version = parse_job_description_with_fallback(
        "Build REST APIs with Python.",
        client=FailingClient(),
        model="test-model",
    )

    assert parsed.skills == ["Python", "REST APIs"]
    assert version == "rules-v1"
