#!/usr/bin/env python3
"""Quick validation script for Blitz activation + opportunity pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.task_store import load_tasks_unlocked  # noqa: E402
from godmode.blitz import opportunities  # noqa: E402


def _request(method: str, url: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    data = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method.upper())
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=15) as handle:  # noqa: S310
        body = handle.read().decode("utf-8")
        return json.loads(body) if body else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test Blitz activation & opportunity wiring.")
    api_port = os.environ.get("GODMODE_API_PORT_HOST", "5051")
    api_default = os.environ.get("GODMODE_API_URL", f"http://127.0.0.1:{api_port}")
    parser.add_argument("--base-url", default=api_default, help="API base URL")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    try:
        activation = _request("POST", f"{base}/api/mode/blitz_all_out_1/activate")
        print(f"[OK] Blitz mode activated: {activation.get('mode')}")
    except urllib.error.URLError as exc:  # noqa: PERF203
        print(f"[FAIL] Unable to activate Blitz mode via API: {exc}", file=sys.stderr)
        sys.exit(1)

    created = opportunities.sync_funnels_to_opportunities()
    if created:
        print(f"[OK] Registered {created} funnel-backed opportunities.")
    else:
        print("[INFO] No new funnel opportunities were registered (may already exist).")

    try:
        op_data = _request("GET", f"{base}/api/blitz/opportunities")
        print(f"[OK] API returned {len(op_data.get('items', []))} Blitz opportunities.")
    except urllib.error.URLError as exc:
        print(f"[FAIL] Unable to fetch Blitz opportunities: {exc}", file=sys.stderr)
        sys.exit(1)

    tasks = load_tasks_unlocked()
    blitz_tasks = [task for task in tasks if task.get("type") == "blitz_campaign"]
    if blitz_tasks:
        print(f"[OK] {len(blitz_tasks)} blitz_campaign task(s) detected in roadmap.")
    else:
        print("[WARN] No blitz_campaign tasks present. Run autopilot after activating Blitz.")

    status = _request("GET", f"{base}/api/blitz/status")
    print(
        f"[OK] Blitz status totals → income: ${status.get('total_blitz_income', 0):,.2f}, "
        f"BOA: ${status.get('total_deposited_to_boa', 0):,.2f}, "
        f"3rd-party: ${status.get('total_confirmed_third_party', 0):,.2f}"
    )


if __name__ == "__main__":
    main()
