"""Verify the local Compose demo through HTTP; compare one run after restart."""

import argparse
import hashlib
import json
from urllib.request import Request, urlopen


def request(base_url: str, path: str, data: dict | None = None):
    payload = json.dumps(data).encode() if data is not None else None
    with urlopen(Request(
        base_url + path, data=payload,
        headers={"Content-Type": "application/json"},
    ), timeout=30) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8008")
    parser.add_argument("--run-id", help="Read an existing run instead of creating one")
    parser.add_argument("--expected-digest", help="Compare the persisted report content")
    args = parser.parse_args()
    if not args.url.startswith(("http://127.0.0.1:", "http://localhost:")):
        parser.error("This verification script is restricted to local test workspaces")

    assert request(args.url, "/health") == {"status": "ok"}
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


if __name__ == "__main__":
    main()
