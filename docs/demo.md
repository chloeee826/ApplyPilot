# ApplyPilot portfolio release

ApplyPilot helps one candidate organize resume/project evidence, save target roles,
track application progress, and generate a role-specific preparation report with
inspectable sources. It currently works with saved job descriptions; it does not
discover jobs online or submit applications.

## Run the complete product

From the repository root with Docker Desktop running:

```bash
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo
```

Open http://127.0.0.1:8008. The single app container serves React and `/api/*`.
PostgreSQL is a separate container with a named volume. The database port `5544`
and application port `8008` are bound to `127.0.0.1`. Neither environment receives
an OpenAI key by default. Seeding is idempotent and updates the named demo records,
so do not edit the demo records expecting seeding to preserve those edits.

Stop using `docker compose down`; data stays in the named volume. If the default
Docker Compose command is missing on macOS, Docker Desktop's bundled binary is
`/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose`. Older
installation symlinks can point to removed AppTranslocation paths; repair them
through the normal Docker Desktop installation rather than deleting your settings.

## Five-minute walkthrough

1. **Overview:** follow the four-step journey. Counts come from saved records.
2. **Candidate:** review the seeded profile and projects. Alternatively upload a
   text-layer PDF, correct the draft, and confirm it. Preview alone saves nothing.
3. **Jobs:** save a role or inspect the seeded role. Update its application status.
   Search by company/title/location, filter by status, and move through UI pages.
4. **Analyze:** inspect extracted skills, requirements, and responsibilities.
5. **Agent Match:** choose the role/profile, keep deterministic demo selected, and
   run. Inspect matches and gaps; expand a source to see saved project details.
6. **Refresh:** the stored report loads again from PostgreSQL.
7. **Edit and regenerate:** change the job description, observe invalidated analysis
   and an older-report warning, re-analyze, then run a fresh report. History remains.

Profile skills and project highlights are candidate-provided evidence, not verified
proficiency. The original snapshot stays fixed, while read-time source annotation
uses the ontology version displayed in the report. Context freshness compares the
four stored tool outputs with current inputs; incomplete old traces show unknown
freshness. Restoring identical inputs can make them unchanged again; this checks
content equality, not an immutable audit of every edit.

## Verification

Backend (from `backend`, with the virtual environment active):

```bash
pytest -q
python -m evals.job_parser_eval
python -m evals.agent_match_eval
```

Browser (from `frontend`):

```bash
npm run build
npm run lint
npm run test:e2e
```

The browser suite owns temporary SQLite data on ports `8011`/`5181`; it does not
reuse an existing server. It clears `OPENAI_API_KEY` in its backend process. Its
PDF fixture is authored synthetic content and exercises real PDF extraction.
No real resume files are committed. The tests have one sequential workspace and
fail without retries. Failed traces/screenshots remain local and Git-ignored.

Dedicated Compose PostgreSQL integration verification:

```bash
DATABASE_URL=postgresql+psycopg://applypilot:applypilot_local_demo@127.0.0.1:5544/applypilot RUN_POSTGRES_TESTS=1 .venv/bin/python -m pytest -q
```

Run that command only against the local Compose demo database. The opt-in test
creates and removes its own records. SQLite browser tests do not by themselves
prove PostgreSQL persistence or container-restart behavior.

From `backend`, `python -m scripts.verify_runtime` checks production page routes,
creates one demo report, reads its sources, and prints a run ID and digest. After
`docker compose restart app` and a healthy status, re-run it with `--run-id ID`
and `--expected-digest HASH` to verify unchanged report content. Use only the
dedicated local Compose workspace. A successful local build, real PostgreSQL test,
and restart comparison are recorded in `docs/release-verification.md`.

## Metrics and limitations

The parser benchmark contains 20 synthetic cases: 98.57% precision and 74.19%
recall. Deterministic matching has 36 curated cases. The preserved v3 first run
on the final 12 cases had 100% precision and 87.50% recall. After observed failures
guided v4 changes, recall reached 97.50% with 100% precision on that same data.
That improvement is validation performance, not a new blind score or live-model
accuracy. Two ambiguous labels remain unresolved.

The OpenAI bounded tool loop is implemented and fake-client-tested. Successful
live execution, live-model latency/token usage, production traffic, and real-user
outcomes remain unverified. Phase 30 waits for explicit API spending approval.

This is a local single-user portfolio MVP. It lacks authentication and tenant
isolation; do not publish a real resume workspace as a public service. OCR, DOCX,
live job discovery, automatic applications, and iOS are outside this release.
The frontend loads all API pages into shared memory and filters locally; offset
pagination can shift during concurrent writes. A larger/multi-user version needs
server-side query/filtering, stable cursors, authentication, and schema migrations.

## Interview explanation

“I built the workflow from resume review to stored job-match reports. The backend
controls four read-only evidence tools, validates structured results, and saves
both completed and failed runs. I added source snapshots so a recommendation can
be inspected even after the candidate edits their profile. Evaluation uses frozen
datasets and versioned baselines, and browser tests exercise the user journey.”

Be explicit when discussing deterministic demo output versus the optional LLM
integration. Repository claims and evidence are tracked in `docs/resume-evidence.md`.
