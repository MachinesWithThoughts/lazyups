#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: 'uv' executable not found in PATH. Install uv from https://docs.astral.sh/uv/" >&2
  exit 127
fi

TS="$(date +%Y%m%d-%H%M%S)"
REPORT="preflight--${TS}.txt"

FAILURES=0

run_check() {
  local name="$1"
  shift

  {
    echo
    echo "============================================================"
    echo "CHECK: ${name}"
    echo "CMD: $*"
    echo "TIME: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "============================================================"
  } >>"$REPORT"

  if "$@" >>"$REPORT" 2>&1; then
    echo "[PASS] ${name}" | tee -a "$REPORT"
  else
    local code=$?
    echo "[FAIL] ${name} (exit ${code})" | tee -a "$REPORT"
    FAILURES=$((FAILURES + 1))
  fi
}

{
  echo "LazyUPS Preflight Report"
  echo "Generated: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "Repo: $SCRIPT_DIR"
  echo "Report: $REPORT"
} >"$REPORT"

run_check "Runtime validation" ./run-code-validations.sh --validate-runtime
run_check "Screens validation" ./run-code-validations.sh --validate-screens
run_check "Pytest" uv run pytest -q
run_check "Ruff" uv run ruff check .
run_check "Mypy" uv run mypy

{
  echo
  echo "============================================================"
  echo "SUMMARY"
  echo "============================================================"
  if [ "$FAILURES" -eq 0 ]; then
    echo "Overall: PASS"
  else
    echo "Overall: FAIL (${FAILURES} check(s) failed)"
  fi
  echo "Finished: $(date '+%Y-%m-%d %H:%M:%S %Z')"
} | tee -a "$REPORT"

echo "Report written to: $REPORT"

if [ "$FAILURES" -ne 0 ]; then
  exit 1
fi
