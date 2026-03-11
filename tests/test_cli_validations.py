"""Ensure CLI validation commands succeed."""

from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT_ROOT / "run.sh"


def run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(RUNNER), *args],
        cwd=PROJECT_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def test_validate_runtime_runs() -> None:
    result = run_command("--validate-runtime")
    assert result.returncode == 0, result.stderr


def test_validate_screens_runs() -> None:
    result = run_command("--validate-screens")
    assert result.returncode == 0, result.stderr


def test_validate_specific_screens_runs() -> None:
    result = run_command("--validate-screens", "--validation-screens", "settings")
    assert result.returncode == 0, result.stderr
