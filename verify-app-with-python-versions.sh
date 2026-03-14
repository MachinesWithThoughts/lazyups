#!/usr/bin/env bash
set -euo pipefail

# Verify LazyUPS against selected Python versions in isolated environments.
#
# Usage:
#   ./verify-app-with-python-versions.sh                # default: 3.12 3.13 3.14
#   ./verify-app-with-python-versions.sh 3.13 3.14     # custom version list

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is required. Install from https://docs.astral.sh/uv/" >&2
  exit 127
fi

VERSIONS=("$@")
if [[ ${#VERSIONS[@]} -eq 0 ]]; then
  VERSIONS=("3.12" "3.13" "3.14")
fi

OUT_ROOT="python-version-validation"
mkdir -p "$OUT_ROOT"

TOTAL=0
PASSED=0
FAILED=0

run_for_version() {
  local ver="$1"
  local pybin="python${ver}"
  local outdir="$OUT_ROOT/py${ver}"
  local log="$outdir/report.txt"
  local status_file="$outdir/status.txt"

  TOTAL=$((TOTAL + 1))
  mkdir -p "$outdir"

  {
    echo "LazyUPS Python ${ver} verification"
    echo "Generated: $(date)"
    echo "Repo: $REPO_ROOT"
    echo
  } >"$log"

  echo "[INFO] Ensuring Python ${ver} is installed via uv..." | tee -a "$log"
  if ! uv python install "$ver" >>"$log" 2>&1; then
    echo "FAIL" >"$status_file"
    echo "[FAIL] Could not install Python ${ver} via uv" | tee -a "$log"
    FAILED=$((FAILED + 1))
    return
  fi

  if ! command -v "$pybin" >/dev/null 2>&1; then
    echo "FAIL" >"$status_file"
    echo "[FAIL] ${pybin} not found after uv install" | tee -a "$log"
    FAILED=$((FAILED + 1))
    return
  fi

  echo "[INFO] Using $($pybin --version 2>&1)" | tee -a "$log"

  rm -rf "$outdir/venv"
  "$pybin" -m venv "$outdir/venv"
  # shellcheck disable=SC1091
  source "$outdir/venv/bin/activate"

  {
    echo
    echo "== pip install -e .[dev] =="
    pip install -e .[dev]

    echo
    echo "== pytest -q =="
    pytest -q

    echo
    echo "== ruff check . =="
    ruff check .

    echo
    echo "== mypy =="
    mypy

    echo
    echo "== smoke: lazyups --version =="
    lazyups --version
  } >>"$log" 2>&1 || {
    echo "FAIL" >"$status_file"
    echo "[FAIL] Python ${ver} verification failed. See $log"
    deactivate || true
    FAILED=$((FAILED + 1))
    return
  }

  deactivate || true
  echo "PASS" >"$status_file"
  echo "[PASS] Python ${ver} verification passed. Report: $log"
  PASSED=$((PASSED + 1))
}

echo "Running LazyUPS Python compatibility verification..."
for ver in "${VERSIONS[@]}"; do
  run_for_version "$ver"
done

echo
echo "================ SUMMARY ================"
echo "Total:   $TOTAL"
echo "Passed:  $PASSED"
echo "Failed:  $FAILED"
echo "Reports: $OUT_ROOT/py*/report.txt"

if [[ "$FAILED" -ne 0 ]]; then
  exit 1
fi
