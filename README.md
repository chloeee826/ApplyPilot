# ApplyPilot

ApplyPilot is a work-in-progress agentic job search platform for application
tracking, role analysis, and interview preparation. The planned stack is React,
TypeScript, FastAPI, PostgreSQL, and LLM tool calling.

## Current status

The repository currently contains a tested full-stack foundation with:

- a FastAPI `GET /health` liveness endpoint;
- a validated `POST /jobs` endpoint;
- SQLAlchemy job persistence in PostgreSQL;
- isolated unit tests and an opt-in PostgreSQL integration test;
- a React and TypeScript frontend;
- a frontend health-check action backed by React state;
- a Vite development proxy connecting the frontend to FastAPI;
- pinned backend and frontend dependencies.

Job listing and status management, the job form, candidate profiles, job
description analysis, and AI agent features are planned but are not implemented
yet.

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
development, Vite proxies `/health` requests to the FastAPI server on port
`8000`.

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

From the `frontend` directory:

```bash
npm run build
npm run lint
```
