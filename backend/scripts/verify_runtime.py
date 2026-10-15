"""Verify the local Compose demo through HTTP; compare one run after restart."""

import argparse
import hashlib
import json
import os
from getpass import getpass
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, build_opener
from urllib.request import Request, urlopen

CLIENT = build_opener(HTTPCookieProcessor(CookieJar()))


def request(base_url: str, path: str, data: dict | None = None):
    payload = json.dumps(data).encode() if data is not None else None
    with CLIENT.open(Request(
        base_url + path, data=payload,
        headers={"Content-Type": "application/json", "X-ApplyPilot-Request": "1"},
    ), timeout=30) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8008")
    parser.add_argument("--run-id", help="Read an existing run instead of creating one")
    parser.add_argument("--expected-digest", help="Compare the persisted report content")
    parser.add_argument("--email", required=True, help="Existing demo workspace account")
    args = parser.parse_args()
    if not args.url.startswith(("http://127.0.0.1:", "http://localhost:")):
        parser.error("This verification script is restricted to local test workspaces")

    assert request(args.url, "/health") == {"status": "ok"}
    password = os.getenv("APPLYPILOT_VERIFY_PASSWORD") or getpass("Demo account password (not echoed): ")
    request(args.url, "/api/auth/login", {"email": args.email, "password": password})
    for page in ("/", "/jobs", "/candidate", "/agent"):
        with urlopen(args.url + page, timeout=10) as response:
            assert b'<div id="root">' in response.read()

    if args.run_id:
        run = request(args.url, f"/api/agent-runs/{args.run_id}")
    else:
        jobs = request(args.url, "/api/jobs?limit=100")
        profiles = request(args.url, "/api/profiles?limit=100")
        job = next(item for item in jobs if item["company_name"] == "ApplyPilot Demo Co")
        profile = next(item for item in profiles if item["full_name"] == "Demo Candidate")
        run = request(args.url, "/api/agent-runs", {
            "job_id": job["id"], "profile_id": profile["id"], "mode": "demo",
        })

    assert run["status"] == "completed"
    assert run["context_status"] == "unchanged"
    assert len(run["tool_trace"]) == 4
    assert run["matched_skill_evidence"]
    assert all(item["sources"] for item in run["matched_skill_evidence"])
    job = request(args.url, f"/api/jobs/{run['job_id']}")
    assert job["company_name"] == "ApplyPilot Demo Co"
    digest = hashlib.sha256(json.dumps(run, sort_keys=True).encode()).hexdigest()
    if args.expected_digest:
        assert digest == args.expected_digest, "Report changed across container restart"
    print(json.dumps({"run_id": run["id"], "job_id": run["job_id"],
        "report_sha256": digest, "status": "verified"}))
    request_logout = Request(args.url + "/api/auth/logout", method="POST", headers={"X-ApplyPilot-Request": "1"})
    with CLIENT.open(request_logout, timeout=10) as response:
        assert response.status == 204


if __name__ == "__main__":
    main()
