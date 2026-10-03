# ApplyPilot

ApplyPilot is a work-in-progress agentic job search platform for application
tracking, role analysis, and interview preparation. The planned stack is React,
TypeScript, FastAPI, PostgreSQL, and LLM tool calling.

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
- a React candidate workspace for creating and reloading profile evidence;
- a versioned rule-based job-description parser that extracts skills,
  requirements, preferred qualifications, and responsibilities;
- persistent structured job analyses with automatic invalidation when a job
  description changes;
- frontend controls for creating, refreshing, and reviewing job analyses;
- an optional OpenAI Structured Outputs parser using a Pydantic response schema;
- automatic fallback to the deterministic parser when an API key is absent or
  the model request does not return a usable structured result;
- a repeatable parser baseline evaluation covering backend, frontend, mobile,
  and platform job descriptions;
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
- a Vite development proxy connecting the frontend to FastAPI;
- pinned backend and frontend dependencies.

The OpenAI structured-output and tool-calling integrations are implemented and
tested with fake clients, but a live model request has not yet been verified
with a real API key. The current agent uses stored application data only; live
job search is not implemented yet.

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
repository. Agent runs require an API key because their purpose is to exercise
the model-driven tool loop. A failed or unconfigured run is still persisted so
its status and error can be inspected later.

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
development, Vite proxies `/health`, `/jobs`, `/job-analyses`, `/applications`,
`/profiles`, and `/agent-runs` requests to the FastAPI server on port `8000`.

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

From the `frontend` directory:

```bash
npm run build
npm run lint
```
