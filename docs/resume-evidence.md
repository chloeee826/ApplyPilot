# ApplyPilot resume evidence

This document separates implemented, verifiable claims from future work. Update it
whenever a resume bullet changes.

## Claim 1: Full-stack product workflow

**Resume wording**

> Built an agentic job-search MVP with React, TypeScript, FastAPI, and PostgreSQL,
> supporting persistent job tracking, application status workflows, candidate
> project evidence, structured role analysis, and routed recommendation views.

**Repository evidence**

- `frontend/src/App.tsx` defines the routed product shell and shared workspace data.
- `frontend/src/pages/JobsPage.tsx` implements job creation, pipeline updates, and
  structured analysis review.
- `frontend/src/components/CandidateProfilePanel.tsx` stores profile and project
  evidence.
- `backend/app/models/` contains the persisted SQLAlchemy entities.
- `backend/tests/test_postgres_integration.py` verifies the API and PostgreSQL path.

## Claim 2: Bounded tool-calling agent

**Resume wording**

> Implemented a bounded OpenAI Responses API agent with four controlled evidence
> tools, required-tool validation, Pydantic structured outputs, and persistent
> completed and failed run traces for inspectable recommendations.

**Repository evidence**

- `backend/app/services/job_match_agent.py` defines the four strict read-only tools,
  bounded loop, call-ID preservation, required-tool enforcement, and output schema.
- `backend/app/routers/agent_runs.py` persists running, completed, and failed states.
- `backend/tests/test_job_match_agent.py` verifies tool execution, structured output,
  unsafe-tool rejection, required-tool validation, and the step limit.
- `backend/tests/test_agent_runs.py` verifies result and failure persistence.

**Limitation**

The real OpenAI request reached the API but could not complete because the account
had insufficient quota. Do not claim production usage or live-model accuracy.

## Claim 3: Measured parser evaluation

**Resume wording**

> Evaluated deterministic skill extraction on 20 synthetic job descriptions with
> 93 labelled technologies, achieving 98.57% precision and 74.19% recall while
> retaining unsupported cases to expose measurable coverage gaps.

**Repository evidence**

- `backend/evals/data/job_parser_cases.json` is the version-controlled dataset.
- `backend/evals/job_parser_eval.py` computes precision, recall, exact-match rate,
  missed labels, and unexpected labels.
- `backend/tests/test_job_parser_evaluation.py` protects the documented baseline.

**Limitation**

The benchmark is curated and synthetic. Do not describe it as production traffic,
real-user accuracy, or business impact.

## Demo-mode boundary

`demo-evidence-v1` runs the same database evidence tools and persistence path but
uses deterministic comparison logic instead of an LLM. It exists to make the MVP
reproducible without API credits and is labelled in both the API result and UI.

## Agent evaluation baseline

The repository includes a version-controlled agent benchmark that measures match
precision and recall, gap detection, structured-output validity, completion of all
four required evidence tools, and whether project-evidence statements identify a
stored project. The dataset intentionally retains common technology-alias failures.

This benchmark currently evaluates the deterministic agent path. Do not describe
its results as live-model quality, real-user outcomes, or a real-job-posting study.

## Not yet claimable

- live job discovery or web search;
- production deployment or real-user adoption;
- successful live OpenAI agent execution;
- latency, conversion, or interview-outcome improvements.
