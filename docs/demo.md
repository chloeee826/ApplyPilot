# ApplyPilot portfolio release

ApplyPilot helps one candidate organize resume/project evidence, save target roles,
track application progress, and generate a role-specific preparation report with
inspectable sources. It currently works with saved job descriptions; it does not
discover jobs online or submit applications.

## Run the complete product

From the repository root with Docker Desktop running:

```bash
docker compose up --build -d
```

Open http://127.0.0.1:8008 and create an account. Optionally seed synthetic evidence:
`docker compose exec app python -m scripts.seed_demo --email YOUR_EMAIL`.
The single app container serves React and `/api/*`.
PostgreSQL is a separate container with a named volume. The database port `5544`
and application port `8008` are bound to `127.0.0.1`. Neither environment receives
an OpenAI key by default. Seeding is idempotent and updates the named demo records,
so do not edit the demo records expecting seeding to preserve those edits.

Existing pre-auth records remain stored but hidden. See the explicit local
ownership-assignment steps in [authentication](authentication.md); first signup
never claims them automatically. Use a unique password: email verification and
password recovery are not implemented in this MVP.

Stop using `docker compose down`; data stays in the named volume. If the default
Docker Compose command is missing on macOS, Docker Desktop's bundled binary is
`/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose`. Older
installation symlinks can point to removed AppTranslocation paths; repair them
through the normal Docker Desktop installation rather than deleting your settings.

## Five-minute walkthrough

1. **Check fit → Your resume:** choose the saved profile or upload a text-layer PDF,
   correct the draft, and confirm it. Preview alone saves nothing.
2. **Target job:** enter the company, role title, and original JD, then click
   **Analyze my fit**. This runs the rules-based evidence check, not OpenAI.
3. **Your results:** inspect skill evidence coverage, role-specific missing evidence
   and JD excerpts. Expand supporting sources to see the original saved snapshots.
4. **Refresh:** the result URL contains the run ID, and reload retrieves the same
   persisted report. **Check another job** keeps the profile but starts a new role.
5. **Jobs:** track application status, search/filter saved roles, or edit a JD.
6. **Reports:** review history. Advanced execution settings allow a fresh run on an
   analyzed saved job. After edits, old reports retain their snapshots and show a
   freshness warning; re-analyze and generate a fresh report when needed.

The one-click endpoint saves the job, application, deterministic analysis, and
report in one transaction. Repeating the same request ID with unchanged inputs
returns the original result instead of duplicating records. Changed evidence or
inputs require a new check. A failed transaction rolls back partial writes. No paid
LLM request is made on this main path, even when an API key is configured.
Candidate editing remains under `/candidate`; the old summary is under `/overview`.

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

From `backend`, `python -m scripts.verify_runtime --email YOUR_EMAIL` prompts for
the demo account password without echoing it, signs in, checks production page routes,
creates one demo report, reads its sources, and prints a run ID and digest. After
`docker compose restart app` and a healthy status, re-run it with `--run-id ID`
and `--expected-digest HASH` to verify unchanged report content. Use only the
dedicated local Compose workspace. A successful local build, real PostgreSQL test,
and restart comparison are recorded in `docs/release-verification.md`.

## Metrics and limitations

The Agent Match report displays `coverage-v1`: supported unique extracted job
skills divided by all unique extracted job skills, multiplied by 100. Aliases
count once, each skill has equal weight, and profile/project support comes from
the run snapshots. Coverage is calculated independently of model-written match
claims. Missing evidence cards identify the saved role/company and quote related
JD sentences where available. Zero extracted skills or incomplete snapshots do not
produce a numeric score; failed runs have no score. Stale reports show a historical
input warning. The formula and current source ontology are displayed in the UI.

This is technical evidence coverage, not overall qualification or hiring probability.
It does not score proficiency, years of experience, seniority, education, or
requirement priority. Parser omissions affect the denominator, so review the full
JD. Missing saved support does not mean the candidate lacks that skill.

The parser benchmark contains 20 synthetic cases: 98.57% precision and 74.19%
recall. Deterministic matching has 36 curated cases. The preserved v3 first run
on the final 12 cases had 100% precision and 87.50% recall. After observed failures
guided v4 changes, recall reached 97.50% with 100% precision on that same data.
That improvement is validation performance, not a new blind score or live-model
accuracy. Two ambiguous labels remain unresolved.

The OpenAI bounded tool loop is implemented and fake-client-tested. Successful
live execution, live-model latency/token usage, production traffic, and real-user
outcomes remain unverified. Phase 30 waits for explicit API spending approval.

This local portfolio MVP now has accounts and application-level user isolation;
it is not an audited production identity service. Do not publish real resumes
without the operational and security review described in [authentication](authentication.md). OCR, DOCX,
live job discovery, automatic applications, and iOS are outside this release.
The frontend loads all API pages into shared memory and filters locally; offset
pagination can shift during concurrent writes. A larger/multi-user version needs
server-side query/filtering, stable cursors and a broader migration process.

## Interview explanation

“I built the workflow from resume review to stored job-match reports. The backend
controls four read-only evidence tools, validates structured results, and saves
both completed and failed runs. I added source snapshots so a recommendation can
be inspected even after the candidate edits their profile. Evaluation uses frozen
datasets and versioned baselines, and browser tests exercise the user journey.”

Be explicit when discussing deterministic demo output versus the optional LLM
integration. Repository claims and evidence are tracked in `docs/resume-evidence.md`.
