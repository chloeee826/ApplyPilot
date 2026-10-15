# ApplyPilot

ApplyPilot is an agentic job search MVP for application tracking, evidence-backed
role analysis, and interview preparation. It uses React, TypeScript, FastAPI,
PostgreSQL, and an optional OpenAI tool-calling workflow.

## Local portfolio demo

With Docker Desktop running, from the repository root:

```bash
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo
```

Open **http://127.0.0.1:8008**. This is the complete product, not just the API.
The Compose database uses a named volume and loopback-only ports. Demo mode has
zero model API cost. `docker compose down` stops this workspace while preserving
its volume. Do not use `down -v` if you want to keep your records. These are local
demo credentials; this configuration is not a public multi-user deployment.

See [the five-minute demo and release checklist](docs/demo.md) for a walkthrough,
verification commands, known limitations, and interview explanations.

## Current status

The repository currently contains a tested full-stack foundation with:

- a FastAPI `GET /health` liveness endpoint;
- a validated `POST /jobs` endpoint;
- paginated job listing, detail retrieval, and partial updates;
- saved-role editing, company/title/location search, status filtering, and five-card
  UI pages; shared workspace loading follows all bounded API pages;
- SQLAlchemy job persistence in PostgreSQL;
- isolated unit tests and an opt-in PostgreSQL integration test;
- a React and TypeScript frontend;
- a frontend health-check action backed by React state;
- a responsive job creation form and PostgreSQL-backed job list;
- automatic application creation when a job is saved;
- a validated application pipeline with saved, applied, interviewing, offer,
  rejected, and withdrawn statuses;
- persistent application status updates from the React workspace;
- PostgreSQL-backed candidate profiles with structured skill lists;
- project evidence records with technologies and concrete highlights;
- a safe, in-memory PDF resume preview that validates uploads and returns
  reviewable profile and project drafts without storing the original file;
- a React candidate workflow for editing or removing extracted evidence before
  any data is persisted;
- an atomic candidate-import endpoint that saves the confirmed profile and
  projects together and updates matching project names on repeated imports;
- a versioned rule-based job-description parser that extracts skills,
  requirements, preferred qualifications, and responsibilities;
- persistent structured job analyses with automatic invalidation when a job
  description changes;
- frontend controls for creating, refreshing, and reviewing job analyses;
- an optional OpenAI Structured Outputs parser using a Pydantic response schema;
- automatic fallback to the deterministic parser when an API key is absent or
  the model request does not return a usable structured result;
- a repeatable, 20-case synthetic parser benchmark spanning backend, frontend,
  mobile, platform, data, machine-learning, AI, quality, and security roles;
- a bounded OpenAI Responses API tool-calling loop with four read-only tools
  for jobs, job analyses, candidate profiles, and project evidence;
- a repeatable agent-quality benchmark with separate development and sourced
  validation cases, covering schema validity, required-tool completion,
  skill-match precision and recall, gap detection, and grounded project evidence;
- schema-validated job-match recommendations covering matched skills, skill
  gaps, relevant project evidence, and interview focus areas;
- persistent agent runs with running, completed, and failed states plus a tool
  trace that makes each evidence lookup inspectable;
- per-skill supporting profile/project sources derived from persisted run snapshots,
  preserving original technology labels and identifying matches with missing support;
- expandable source details showing saved profile summaries or project descriptions,
  technologies, and highlights without navigating away from the recommendation;
- report freshness checks comparing stored snapshots with current job, analysis,
  profile, and project data, while preserving the original report;
- a role-specific skill evidence coverage score, grounded in saved snapshots rather
  than model claims, with missing-evidence cards showing related original JD excerpts;
- API endpoints for starting, listing, and retrieving agent runs;
- a React agent workspace for selecting analyzed jobs and candidate profiles,
  starting runs, and reviewing matched skills, gaps, project evidence, interview
  focus areas, run history, and actionable failure states;
- an explicitly labelled deterministic demo mode that runs the same four evidence
  tools and persists a successful recommendation without external API credits;
- a three-step home flow: review resume evidence, paste a target job, and inspect
  a saved role-specific report; one rules-based action saves all related records
  atomically, with request IDs preventing duplicate records on retries;
- secondary Jobs and Reports workspaces, with candidate editing and the workspace
  overview available separately; advanced execution settings stay out of the main flow;
- page-level onboarding, actionable empty states, and success feedback for the
  resume-to-recommendation workflow;
- a production application factory that serves the compiled React workspace and
  namespaces JSON endpoints under `/api` without client-route collisions;
- a multi-stage, non-root Docker image with a platform health check and no local
  secrets, virtual environments, tests, or frontend dependencies in the runtime;
- a Vite development proxy connecting the frontend to FastAPI;
- pinned backend and frontend dependencies.

The OpenAI structured-output and tool-calling integrations are implemented and
tested with controlled fake clients, but a live successful model response has not
yet been verified because the configured account has no API credits. Deterministic
demo mode is deliberately identified as non-LLM output. The current agent uses
stored application data only; live job search is not implemented.

## Five-minute MVP demo

No OpenAI key is required for this path:

1. Start PostgreSQL, the backend, and the frontend using the commands below.
2. From the `backend` directory, run `python -m scripts.seed_demo`. The command is
   idempotent, so running it again refreshes the same demo records instead of
   creating duplicates.
3. Open `http://127.0.0.1:5173`. Choose the saved profile or upload a text-based PDF
   and review its extracted evidence before confirming it.
4. Enter the company, role title, and original job description. Click **Analyze my
   fit**. This rules-based path makes no paid AI request.
5. Inspect the evidence coverage score, missing evidence with original JD excerpts,
   and supporting source snapshots. Refresh the result URL to load the same report
   from PostgreSQL. Jobs and Reports remain accessible for tracking and history.

To use your own evidence instead, open `/candidate`, upload a text-based PDF
resume of up to 5 MB, review every extracted profile and project field, and
confirm the import. Scanned-image PDFs require OCR and are not supported yet.
The home flow saves the job, application, analysis, and report together. Advanced
manual job management remains available under `/jobs`.

Under **Reports → Advanced: run a saved job**, choose **OpenAI agent** only when
`OPENAI_API_KEY` is configured. This path runs
the bounded Responses API tool loop; configuration and execution failures are
persisted for inspection instead of being replaced with demo output.

## Run the backend

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
createdb applypilot
export DATABASE_URL=postgresql+psycopg://localhost:5432/applypilot
uvicorn app.main:app --reload
```

`DATABASE_URL` is optional when the local database uses the default URL shown
above. A matching example is available in `backend/.env.example`.

To enable the optional LLM parser, export an OpenAI API key before starting the
server. The model is configurable and defaults to `gpt-4o-mini`:

```bash
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4o-mini
```

Without an API key, or when the model request fails, job analysis continues
with the versioned `rules-v1` fallback. Never commit a real key to the
repository. OpenAI-mode agent runs require an API key; deterministic demo runs
do not. A failed or unconfigured OpenAI run is still persisted so its status and
error can be inspected later.

The API is then available at `http://127.0.0.1:8000`. Its interactive API
documentation is at `http://127.0.0.1:8000/docs`.

## Run the frontend

In a separate terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The frontend is then available at `http://127.0.0.1:5173`. During local
development, the browser sends JSON requests under `/api/*`; Vite removes the
`/api` prefix and proxies them to the FastAPI server on port `8000`. Frontend
pages such as `/jobs` therefore remain separate from API paths such as
`/api/jobs`.

## Build the production container

ApplyPilot can run as one container: Node builds the React application, then
FastAPI serves both the compiled frontend and namespaced `/api/*` endpoints.
The runtime image runs as a non-root user.

```bash
docker build -t applypilot .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://user:password@database:5432/applypilot \
  applypilot
```

A hosted runtime must provide `DATABASE_URL`. `PORT` is optional and defaults to
`8000`; `OPENAI_API_KEY` and `OPENAI_MODEL` are optional because deterministic
demo mode does not require model credits. Configure the platform health check to
request `/health`. The public application, API documentation, and JSON API are
then available at `/`, `/docs`, and `/api/*`, respectively.

Never bake `.env` into the image. `.dockerignore` excludes local secrets,
virtual environments, caches, `node_modules`, and previously generated builds.

## Run the tests

Browser journey checks use an isolated temporary SQLite database and a real
synthetic text-layer PDF. They never load your `.env`, use your personal workspace,
or call OpenAI. Install the browser once, then run:

```bash
cd frontend
npm ci
npx playwright install chromium
npm run test:e2e
```

Tests start their own backend on `8011` and frontend on `5181` and stop them on
completion. These ports must be free. The six sequential journey checks cover
PDF review/import, job editing and stale reports, persistence after refresh,
102-record pagination and filtering, invalid uploads, failed agent mode, network
failure, and mobile source disclosure. They are one shared synthetic workspace,
not five independent real-user trials. HTML results are written to
`frontend/playwright-report` and failure traces/screenshots to
`frontend/test-results`, both ignored by Git.

`.github/workflows/verify.yml` runs backend tests with a dedicated PostgreSQL
service, frontend build/lint, and Chromium journey checks on pushes and PRs.
Workflow configuration is implemented; a successful remote CI run is only
claimable after it actually runs on GitHub.

From the `backend` directory:

```bash
pytest
```

To include the real PostgreSQL integration test, make sure the local database
is running and use:

```bash
RUN_POSTGRES_TESTS=1 pytest
```

Run the deterministic parser baseline evaluation with:

```bash
python -m evals.job_parser_eval
```

The current `rules-v1` baseline matches 69 of 93 labelled skills with 98.57%
precision, 74.19% recall, and exact skill-set matches on 4 of 20 cases. The
version-controlled benchmark intentionally includes unsupported technologies
and a React Native ambiguity so future parser improvements can be measured
against known gaps instead of an easy perfect score.

Run the deterministic agent-quality baseline with:

```bash
python -m evals.agent_match_eval
```

The agent benchmark includes aliases such as `Postgres` / `PostgreSQL`, `React.js`
/ `React`, and `REST API` / `REST APIs`, plus the false-friend boundary `Java` /
`JavaScript`. The initial exact-name baseline reached 82.61% match recall, 55.56%
gap precision, and 66.67% exact-case accuracy. Versioned canonical skill
normalization raised all three metrics to 100% on the unchanged 12-case benchmark.
The comparison rules live in the reusable, explicitly versioned `skills-v2`
ontology instead of being embedded in UI or request code.
The separate validation split contains 12 additional cases derived from technology
requirements on official Stripe, Airbnb, MongoDB, Atlassian, and Datadog job pages.
It stores only labelled technology combinations and source provenance, not copied
job descriptions, and is reported separately. Its first run was an untouched
holdout baseline that retained 100% match precision, gap recall,
schema validity, and required-tool completion, while reaching 67.86% match recall,
65.38% gap precision, and 8.33% exact-case accuracy. After those observed failures
informed the versioned v3 skill ontology, the split became validation data and
reached 100% match recall, gap precision, and exact-case accuracy. A new unseen
split is required before making a final generalization claim.

Blind v1 freezes 12 further cases from 12 previously unused official company job
pages before running `demo-evidence-v3`. The preserved first run achieved 100%
match precision, 87.50% match recall, 100% gap recall, and 41.67% exact-case
accuracy. Its misses (`NextJS`, `NestJS`, `Google Cloud Platform`, `PydanticAI`,
`TanStack Query`, and `Apollo Client`) remain visible rather than being patched
before reporting. The frozen dataset SHA-256 and historical result are stored under
`backend/evals/results/` so later matcher versions cannot overwrite the baseline.

After review of those failures, `demo-evidence-v4` / `skills-v2` adds four
unambiguous spelling aliases: NextJS, NestJS, Google Cloud Platform, and PydanticAI.
The former blind split is now validation data. On the identical frozen dataset,
match recall increases from 87.50% to 97.50% (+10 percentage points), precision
remains 100%, gap precision increases to 84.62%, and exact cases increase from
5/12 to 10/12. Apollo/Apollo Client and React Query/TanStack Query remain distinct
because a product family or framework-independent library name may not establish
the specific required skill. These cases retain their original labels for historical
comparability, but are flagged as ambiguous; they need annotation review before
being reused for a future independent quality claim.

The CLI reports both current matcher versions and recall change against the saved
baseline, checking the frozen dataset hash first. Source-derived job technology
lists are paired with authored synthetic candidate fixtures; these are small,
developer-curated tests of deterministic matching, not an unbiased estimate of
end-to-end real-user or live-model performance.

From the `frontend` directory:

```bash
npm run build
npm run lint
```
