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
