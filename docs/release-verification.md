# Local verification — October 12, 2026

## Completed

- Phase 28: saved-job editing, search/status filtering, all-page API loading,
  five-card UI pagination, analysis invalidation, report freshness and regeneration.
- Phase 29: five sequential Chromium journey checks passed on an isolated temporary
  SQLite database with a real synthetic PDF; desktop and 390px mobile verified.
- Backend suite with real Compose PostgreSQL integration enabled: 102 passed,
  1 dependency deprecation warning, no skipped tests.
- Frontend production build and lint: passed.
- Parser evaluation: 20 cases, 98.57% precision, 74.19% recall.
- Agent v4 validation: 36 total curated cases; former blind 12-case split retains
  100% precision, 97.50% recall, and 10/12 exact cases.
- Git diff whitespace check: passed. Credential-pattern scan: no matches in
  publishable source. `.env` and browser artifacts remain ignored.
- Compose configuration and actual multi-stage image build: passed.
- App and PostgreSQL containers: healthy; app UID 100 (non-root).
- Production routes `/`, `/jobs`, `/candidate`, `/agent` serve the compiled frontend;
  `/api` endpoints successfully retrieve PostgreSQL-backed records.
- Created a demo report, restarted only the app container, then read the same job
  and report by ID. Report SHA-256 remained identical, including persisted snapshots
  and derived source annotations. Verified with `scripts.verify_runtime`.
- Rebuilt the final image with the verification script and recreated the app
  container; reading the same saved report still produced the identical digest.
- Phase 31 release assets: Compose definition, CI workflow, five-minute demo,
  setup/troubleshooting/limitations and evidence mapping implemented.

## Runtime verified

Docker Desktop was started using its official CLI after GUI control was unavailable.
The engine and standard Compose command became available. Phases 28, 29, and 31
are complete locally. Repeat the local demo with:

```bash
docker compose up --build -d
docker compose exec app python -m scripts.seed_demo
```

Open http://127.0.0.1:8008. `scripts.verify_runtime` creates a demo report and prints
its ID and digest; running it again with `--run-id` and `--expected-digest` verifies
the same content after restarting the app container. This script only accepts
loopback URLs and only creates deterministic demo runs.

The CI workflow has not run remotely because these changes have not been pushed.
Phase 30 real OpenAI verification remains deferred pending API spending approval.
No successful live-model, public deployment, or real-user outcome claim is added.

## October 14 follow-up — evidence scoring and guided UX

- Added `coverage-v1`: unique extracted technical skills with saved profile/project
  support divided by unique extracted skills. Source snapshots, role identity,
  JD excerpts, empty-score states and stale warnings are shown. This is not hiring
  probability, proficiency, or overall qualification.
- Home now guides resume review → target JD → saved report. The main action uses
  deterministic parsing/matching only; OpenAI remains an explicit advanced mode.
- `/fit-checks` saves job, application, analysis and report in one transaction.
  Tests cover retry reuse, changed-input/evidence conflicts, missing profiles and
  rollback after a synthetic mid-transaction failure.
- Backend: 112 passed with real local PostgreSQL integration enabled; one existing
  dependency deprecation warning. Frontend build and lint passed.
- Six sequential Chromium journeys passed, including the guided PDF review to
  result flow, reload persistence, 102-job pagination, errors and 390px mobile.
  Inspected the mobile result screenshot; no horizontal overflow was detected.
- Re-ran parser and deterministic matcher evaluations. Historical numbers above
  were reproduced; v4's 97.50% recall is still validation performance, not blind
  or live-OpenAI accuracy.
- Rebuilt the local Compose product and retrieved the existing PostgreSQL-backed
  report successfully. The new derived coverage field changes the serialized
  report digest, so the earlier release digest must not be reused for comparisons
  across this scoring change. No new across-restart digest claim is made here.
- No paid API call, new public deployment, or real-user outcome was verified.
  User approved the Lark update and Git publication after reviewing these results.

## October 14 follow-up — authentication and authorization

- Checked the actual push-triggered [GitHub Actions run for 1b1e9d2](https://github.com/chloeee826/ApplyPilot/actions/runs/38670842846).
  Backend tests and build/lint succeeded; Chromium failed the 390px horizontal
  overflow assertion in Reports. Added shrinkable grid/flex children and wrapping;
  the local assertion passes. A new Linux remote run is still needed after push.
- Added local email/password accounts, Argon2id hashes, hash-only database sessions,
  eight-hour expiry, rotation/logout revocation, HttpOnly cookies and secure-by-default
  transport. Loopback-only HTTP development explicitly opts out of Secure cookies.
- All business routes now require authentication. Jobs/profiles are owner-bound;
  child records and reports are owner-filtered before pagination. Cross-owner
  references, imports, writes and agent tool reads are denied.
- Added same-origin custom-header write protection (including auth and multipart
  uploads), Origin/Fetch-Metadata checks, no-store private responses, redacted auth
  validation errors, and database-backed account/IP attempt throttles.
- Existing databases receive additive nullable ownership columns/indexes. Legacy
  records remain stored but hidden; assignment requires a chosen existing account
  and explicit local operator confirmation. Seeding is scoped to a chosen account.
- Full backend verification: 132 passed including real PostgreSQL authentication,
  session persistence and cross-user filtering; one existing dependency warning.
- Frontend build/lint passed. Seven Chromium journeys passed, including real signup,
  reload, logout/account-switch isolation and the existing PDF-to-report workflow.
- Rebuilt the local Docker product; both services healthy. Health returns 200 and
  unauthenticated `/api/jobs` returns 401. Inspected the production login screen.
- No paid API request or real-user credential was used for verification. No account
  was created for the human user and legacy data was not assigned automatically.
- Not implemented: verified email, password recovery/change, MFA, administrator roles,
  public deployment or an audited production identity service. See authentication.md.
- User approved the Lark update, commit and push after reviewing this phase.
