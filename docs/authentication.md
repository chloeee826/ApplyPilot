# Authentication and workspace authorization

This phase adds local email/password accounts, not Google/OAuth, RBAC or a hosted
identity provider. Email is an unverified login identifier. This remains a local
portfolio product, not a production-ready identity service.

## First use

Start the app and register through **Create an account**. Use a unique 12–128
character password. Registration signs you in. Reload keeps the session; **Sign
out** revokes it server-side and unmounts the private workspace. Signing into a
different account mounts fresh React state. A `401` from a workspace request
returns the UI to sign-in. The UI also rechecks the account when a tab regains focus.

Passwords are stored using Argon2id (19 MiB, two iterations, one lane). The cookie
contains a random 256-bit opaque session token; PostgreSQL stores only its SHA-256
hash and an eight-hour absolute expiry. Successful login rotates the browser's
existing session; logout removes it. No session token is stored in localStorage.

`AUTH_COOKIE_SECURE` defaults to true. The loopback-only Compose configuration and
isolated browser tests explicitly set it to `false` for HTTP development. For
separate native development processes, set this variable in the backend process
environment as shown in `.env.example`; the app does not automatically load `.env`.
Use HTTPS and secure cookies for any non-local deployment.

All browser writes, including login, registration, logout and PDF uploads, require
`X-ApplyPilot-Request: 1`. Browser cross-origin forms cannot set that header, and
the API grants no cross-origin CORS access. If Origin is present it must exactly
match `APP_ORIGINS`; cross-site Fetch Metadata is rejected. Configure the exact
frontend origin when changing ports or hosts. This is a same-origin custom-header
CSRF design; SameSite=Lax is additional protection, not the sole defense.

Login and registration have database-backed fixed-window throttles per account
(10 attempts / 15 minutes) and source IP (20 / 15 minutes), with atomic increments.
Unknown-account and incorrect-password logins share an error and both perform a
password hash verification. Proxy headers are not trusted for client IPs by default.

References: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html),
[session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html),
[CSRF custom-header guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

## Authorization boundaries

- Jobs and candidate profiles have an owner set from the authenticated server-side
  identity, never from client-supplied `owner_id` values.
- Lists filter ownership before pagination. Applications and analyses inherit
  access through the job; projects inherit access through the profile.
- Reports require ownership of both the referenced job and profile. Cross-account
  IDs return the same 404 as missing resources, including updates and imports.
- A run cannot mix one user's job with another user's profile. HTTP tool execution
  rechecks the owner before loading any of the four evidence snapshots. Tool
  arguments cannot override the bound job/profile IDs.
- All business routers, including resume preview and one-click fit checks, require
  authentication. Health and static frontend assets remain public. Private HTTP
  responses are marked `Cache-Control: no-store`.

These are application-level ownership checks, not PostgreSQL row-level-security
policies. There is one account capability level: manage your own workspace.

## Upgrading an existing local database

Startup creates auth tables and performs an additive ownership-column/index
upgrade. It never deletes records or silently assigns old data to the first new
account. Old rows have NULL owners and are hidden from every HTTP account.
Existing reports keep their snapshots. Repeated upgrades are idempotent.

After registering the intended account, a local database operator can preview the
unowned record counts, then explicitly assign **all** unowned jobs/profiles:

```bash
docker compose exec app python -m scripts.assign_legacy --email YOUR_EMAIL
docker compose exec app python -m scripts.assign_legacy --email YOUR_EMAIL --confirm
```

This is a local CLI, not an HTTP endpoint. Confirm only for a known single-user
legacy workspace. It cannot transfer already-owned records and refuses incompatible
cross-owner reports. The initial upgrade is deliberately small; future schema
changes need an expanded migration process, not ad-hoc table recreation.

Alternatively seed synthetic evidence only into a chosen existing account:

```bash
docker compose exec app python -m scripts.seed_demo --email YOUR_EMAIL
```

## Tests and limits

`tests/test_auth.py` uses real credentials, cookie sessions, guards and SQL queries.
It tests anonymous denial, hash-only storage, cookie flags, expiry/revocation,
CSRF headers/origins/uploads, throttling, two-user isolation, cross-resource links,
owner spoofing, and additive legacy upgrades. Opt-in PostgreSQL tests verify real
session persistence and cross-user filtering. Existing business unit tests explicitly
override the workspace identity dependency; those tests alone do not prove auth.
Browser tests register, reload, sign out, switch accounts and verify empty private
workspaces, plus repeat the existing application journeys while signed in.

Not implemented: email verification, password recovery/change, MFA/passkeys,
administrator roles, account deletion, session/device management UI, breached-password
screening or a security audit. A production release also needs HTTPS deployment,
signup/abuse policy, proxy-aware rate limiting, per-user AI cost controls, monitored
backups and operational review. Do not use this phase to claim audited security.
