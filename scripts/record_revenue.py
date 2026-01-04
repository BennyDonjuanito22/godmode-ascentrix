#!/usr/bin/env python3
"""CLI helper to append entries to finance/ledger.jsonl."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

API_URL = "http://127.0.0.1:5051/finance/ledger"


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8") or "{}"
            return json.loads(body)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ledger API error: {exc.status} {exc.reason}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a revenue event in the ledger.")
    parser.add_argument("--amount", type=float, required=True, help="Amount received (positive or negative).")
    parser.add_argument("--currency", type=str, default="USD", help="Currency code (default: USD).")
    parser.add_argument("--source", type=str, required=True, help="Source platform, e.g., stripe, shopify.")
    parser.add_argument("--funnel", type=str, required=True, help="Funnel identifier (B1, B2, ...).")
    parser.add_argument("--notes", type=str, default="", help="Optional notes about the transaction.")
    parser.add_argument("--api", type=str, default=API_URL, help=f"Ledger endpoint (default: {API_URL}).")
    args = parser.parse_args()

    payload = {
        "amount": args.amount,
        "currency": args.currency,
        "source": args.source,
        "funnel": args.funnel,
        "notes": args.notes or f"Recorded via CLI at {time.strftime('%Y-%m-%d %H:%M:%S')}",
    }
    response = post_json(args.api, payload)
    print("Recorded:", json.dumps(payload))
    if response:
        print("Server response:", response)


if __name__ == "__main__":
    main()
