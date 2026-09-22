#!/usr/bin/env python3
"""Post sample logs to /api/ingest (and burst failed logins to trigger alert)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import urllib.error
import urllib.request

SAMPLES = Path(__file__).resolve().parent


def login(base: str, user: str, password: str) -> str:
    req = urllib.request.Request(
        f"{base}/api/auth/login",
        data=json.dumps({"username": user, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def post_json(base: str, token: str, payload: object) -> dict:
    req = urllib.request.Request(
        f"{base}/api/ingest",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://localhost:8000")
    p.add_argument("--user", default="admin")
    p.add_argument("--password", default="password")
    p.add_argument("--burst", action="store_true", help="Send 3 failed logins to trigger alert")
    p.add_argument("--file", help="JSON/NDJSON file to upload via API (parsed client-side)")
    args = p.parse_args()

    try:
        token = login(args.base, args.user, args.password)
    except urllib.error.URLError as e:
        print(f"Login failed: {e}", file=sys.stderr)
        return 1

    if args.file:
        path = Path(args.file)
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".ndjson" or path.suffix == ".jsonl":
            payload = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            payload = json.loads(text)
        print(post_json(args.base, token, payload))
        return 0

    # Post built-in samples
    for name in ["crowdstrike.json", "aws_cloudtrail.json", "m365_audit.json", "ad_4625.json"]:
        data = json.loads((SAMPLES / name).read_text(encoding="utf-8"))
        print(name, post_json(args.base, token, data))

    if args.burst:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        for i in range(3):
            payload = {
                "tenant": "demoA",
                "source": "api",
                "event_type": "app_login_failed",
                "user": "alice",
                "ip": "203.0.113.7",
                "reason": "wrong_password",
                "@timestamp": now,
            }
            print("burst", i + 1, post_json(args.base, token, payload))
        print("Alert should appear after evaluate (auto every 1 min) or POST /api/alerts/evaluate")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
