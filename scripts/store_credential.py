#!/usr/bin/env python3
"""
Simple CLI for adding credentials to the God Mode vault.

Usage:
  python scripts/store_credential.py \
      --service TikTok \
      --username user@example.com \
      --password 'secret' \
      --url https://tiktok.com/login

If --password is omitted a secure password will be generated.
"""

import argparse
import getpass
import json
import os
import sys
from urllib import request


def main() -> int:
    parser = argparse.ArgumentParser(description="Store login credentials in the God Mode vault.")
    parser.add_argument("--service", required=True, help="Service or platform name.")
    parser.add_argument("--username", required=True, help="Username or email for the account.")
    parser.add_argument("--password", help="Password (prompted securely if omitted).")
    parser.add_argument("--url", help="Login URL.")
    parser.add_argument("--notes", help="Optional notes.")
    parser.add_argument("--tags", nargs="*", help="Optional tags.")
    api_port = os.environ.get("GODMODE_API_PORT_HOST", "5051")
    api_default = os.environ.get("GODMODE_API_URL", f"http://127.0.0.1:{api_port}")
    parser.add_argument("--api", default=api_default,
                        help="Base API URL (default: %(default)s)")
    args = parser.parse_args()

    password = args.password
    if not password:
        try:
            password = getpass.getpass("Password (leave blank to auto-generate): ")
        except KeyboardInterrupt:
            return 1
        if not password:
            password = _generate_password(args.api)

    payload = {
        "service": args.service,
        "username": args.username,
        "password": password,
        "url": args.url,
        "notes": args.notes,
        "tags": args.tags or [],
    }
    data = json.dumps(payload).encode("utf-8")
    url = args.api.rstrip("/") + "/vault/credentials"
    req = request.Request(url, method="POST", data=data, headers={"Content-Type": "application/json"})
    token = os.environ.get("GODMODE_PHONE_TOKEN")
    if token:
        req.add_header("X-Godmode-Token", token)
    with request.urlopen(req) as resp:
        if resp.status >= 300:
            print(f"Error: {resp.status} {resp.reason}", file=sys.stderr)
            return 1
        result = json.loads(resp.read().decode("utf-8"))
        cred = result.get("credential", {})
        print("Credential stored.")
        print(f"Service : {cred.get('service')}")
        print(f"Username: {cred.get('username')}")
        print(f"Password: {cred.get('password')}")
        return 0


def _generate_password(base_url: str) -> str:
    url = base_url.rstrip("/") + "/vault/generate"
    req = request.Request(url, method="POST")
    token = os.environ.get("GODMODE_PHONE_TOKEN")
    if token:
        req.add_header("X-Godmode-Token", token)
    with request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("password", "")


if __name__ == "__main__":
    raise SystemExit(main())
