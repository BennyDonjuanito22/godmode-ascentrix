"""CLI entry point to run the God Mode agent.

This script instantiates ``GodModeAgent`` with a user‑specified goal and
prints the resulting report.  It can be invoked directly from the host
machine or from within a Docker container.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ENV_ROOT = os.environ.get("GODMODE_REPO_ROOT")
REPO_ROOT = Path(ENV_ROOT).resolve() if ENV_ROOT else SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from api.agent_shell import GodModeAgent  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the God Mode agent")
    parser.add_argument("goal", metavar="GOAL", type=str,
                        help="Description of what the agent should accomplish")
    parser.add_argument(
        "--repo-root",
        dest="repo_root",
        type=str,
        default=None,
        help="Path to the repository root (default: project root detected from this script)",
    )
    args = parser.parse_args()

    repo_root = args.repo_root or os.fspath(REPO_ROOT)
    agent = GodModeAgent(goal=args.goal, repo_root=repo_root)
    result = agent.run()
    print(result)


if __name__ == "__main__":
    main()
