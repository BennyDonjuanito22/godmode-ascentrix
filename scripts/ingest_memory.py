#!/usr/bin/env python3
"""CLI helper to ingest design docs and notes into vector memory."""

from __future__ import annotations

import argparse

import requests

API_URL = "http://127.0.0.1:5051/memory/ingest"


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger vector memory ingestion via the API.")
    parser.add_argument("--api", type=str, default=API_URL, help=f"Endpoint to call (default: {API_URL})")
    args = parser.parse_args()

    resp = requests.post(args.api, timeout=20)
    resp.raise_for_status()
    print("Ingestion complete:", resp.json())


if __name__ == "__main__":
    main()
