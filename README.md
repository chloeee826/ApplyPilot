# ApplyPilot

ApplyPilot is an agentic job search MVP for application tracking, evidence-backed
role analysis, and interview preparation. It uses React, TypeScript, FastAPI,
PostgreSQL, and an optional OpenAI tool-calling workflow.

## Current status

The repository currently contains a tested full-stack foundation with:

- a FastAPI `GET /health` liveness endpoint;
- a validated `POST /jobs` endpoint;
- paginated job listing, detail retrieval, and partial updates;
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
- schema-validated job-match recommendations covering matched skills, skill
  gaps, relevant project evidence, and interview focus areas;
- persistent agent runs with running, completed, and failed states plus a tool
  trace that makes each evidence lookup inspectable;
- API endpoints for starting, listing, and retrieving agent runs;
- a React agent workspace for selecting analyzed jobs and candidate profiles,
  starting runs, and reviewing matched skills, gaps, project evidence, interview
  focus areas, run history, and actionable failure states;
- an explicitly labelled deterministic demo mode that runs the same four evidence
  tools and persists a successful recommendation without external API credits;
- a responsive product shell with routed Overview, Jobs, Candidate, and Agent
  Match workspaces, including database-backed readiness metrics and recent roles;
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
3. Open `http://127.0.0.1:5173/agent`, keep **Deterministic demo** selected, and
   run Agent Match.
4. Review the persisted recommendation, skill gaps, project evidence, four-tool
   trace count, and run history. Refreshing the browser reloads the saved run from
   PostgreSQL.

To use your own evidence instead, open `/candidate`, upload a text-based PDF
resume of up to 5 MB, review every extracted profile and project field, and
confirm the import. Scanned-image PDFs require OCR and are not supported yet.
Then save and analyze a real job description under `/jobs`.

Choose **OpenAI agent** only when `OPENAI_API_KEY` is configured. This path runs
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

From the `frontend` directory:

```bash
npm run build
npm run lint
```
