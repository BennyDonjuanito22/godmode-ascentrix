# tests/test_run_builder_practice.py
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import re
import os
import pytest

# Import the functions from the script
import run_builder_practice as rbp


def test_run_kata_success(monkeypatch):
    # Mock subprocess.run to simulate successful kata run
    class Result:
        def __init__(self):
            self.stdout = 'Sample kata passed all tests.\n'
    def mock_run(*args, **kwargs):
        return Result()
    monkeypatch.setattr(subprocess, 'run', mock_run)
    output = rbp.run_kata()
    assert 'Kata output:' in output
    assert 'Sample kata passed all tests.' in output


def test_run_kata_failure(monkeypatch):
    # Mock subprocess.run to raise CalledProcessError
    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0], stderr='Error message')
    monkeypatch.setattr(subprocess, 'run', mock_run)
    output = rbp.run_kata()
    assert 'Kata failed with error:' in output
    assert 'Error message' in output


def test_scan_git_diffs_no_diff(monkeypatch):
    # Mock subprocess.run to return empty diff
    class Result:
        def __init__(self):
            self.stdout = ''
    def mock_run(*args, **kwargs):
        return Result()
    monkeypatch.setattr(subprocess, 'run', mock_run)
    output = rbp.scan_git_diffs()
    assert 'No diffs detected' in output


def test_scan_git_diffs_with_test_changes(monkeypatch):
    # Mock subprocess.run to return a diff with test file and test function changes
    diff_text = (
        'diff --git a/tests/test_example.py b/tests/test_example.py\n'
        '+def test_new_feature():\n'
    )
    class Result:
        def __init__(self):
            self.stdout = diff_text
    def mock_run(*args, **kwargs):
        return Result()
    monkeypatch.setattr(subprocess, 'run', mock_run)
    output = rbp.scan_git_diffs()
    assert 'Changed test file: tests/test_example.py' in output
    assert 'Added/modified test function' in output


def test_log_results_creates_file(tmp_path):
    # Redirect REPORTS_DIR to tmp_path
    original_reports_dir = rbp.REPORTS_DIR
    rbp.REPORTS_DIR = tmp_path

    kata_output = 'Kata output test'
    diff_output = 'Diff output test'
    rbp.log_results(kata_output, diff_output)

    date_str = rbp.datetime.date.today().isoformat()
    report_file = tmp_path / f'builder_practice_{date_str}.md'
    assert report_file.exists()
    content = report_file.read_text(encoding='utf-8')
    assert '# Builder Practice Report' in content
    assert 'Kata Execution' in content
    assert kata_output in content
    assert 'Git Diff Scan' in content
    assert diff_output in content

    # Restore original REPORTS_DIR
    rbp.REPORTS_DIR = original_reports_dir


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__]))
