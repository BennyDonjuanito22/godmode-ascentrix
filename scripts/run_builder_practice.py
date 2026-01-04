#!/usr/bin/env python3
"""Run builder practice: execute kata, scan diffs for regressions, log results."""

import datetime
import subprocess
import sys
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parent.parent
KATA_SCRIPT = REPO_ROOT / "playground" / "katas" / "sample_kata.py"
REPORTS_DIR = REPO_ROOT / "reports"


def run_kata() -> str:
    """Run the kata script and capture output."""
    try:
        result = subprocess.run(
            [sys.executable, str(KATA_SCRIPT)],
            capture_output=True,
            text=True,
            check=True,
        )
        return f"Kata output:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Kata failed with error:\n{e.stderr}"


def scan_git_diffs() -> str:
    """Scan git diffs for regressions by detecting changes in test files or test functions."""
    try:
        diff = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout

        if not diff.strip():
            return "No diffs detected in last commit."

        # Simple heuristic: look for changes in test files or test functions
        regression_lines = []
        test_file_pattern = re.compile(r"^diff --git a/(.*test.*\.py) b/.*")
        test_func_pattern = re.compile(r"^\+.*def test_.*\(.*\):")

        lines = diff.splitlines()
        in_test_file = False
        for line in lines:
            m = test_file_pattern.match(line)
            if m:
                in_test_file = True
                regression_lines.append(f"Changed test file: {m.group(1)}")
                continue
            if in_test_file and test_func_pattern.match(line):
                regression_lines.append(f"Added/modified test function: {line.strip()}")

        if regression_lines:
            regression_report = "Detected potential regressions in tests:\n" + "\n".join(regression_lines)
        else:
            regression_report = "No test-related regressions detected in last commit."

        return f"Git diffs from last commit:\n{diff}\n\n{regression_report}"

    except subprocess.CalledProcessError as e:
        return f"Failed to get git diffs:\n{e.stderr}"


def log_results(kata_output: str, diff_output: str) -> None:
    """Log the practice results under reports/builder_practice_<date>.md."""
    REPORTS_DIR.mkdir(exist_ok=True)
    date_str = datetime.date.today().isoformat()
    report_path = REPORTS_DIR / f"builder_practice_{date_str}.md"

    with report_path.open("a", encoding="utf-8") as f:
        f.write(f"# Builder Practice Report {date_str}\n\n")
        f.write("## Kata Execution\n")
        f.write(kata_output + "\n\n")
        f.write("## Git Diff Scan\n")
        f.write(diff_output + "\n\n")

    print(f"Logged builder practice results to {report_path}")


def main() -> None:
    kata_output = run_kata()
    diff_output = scan_git_diffs()
    log_results(kata_output, diff_output)


if __name__ == "__main__":
    main()
