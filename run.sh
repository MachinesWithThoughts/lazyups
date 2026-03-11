#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: 'uv' executable not found in PATH. Install uv from https://docs.astral.sh/uv/" >&2
    exit 127
fi

VENV_DIR="${SCRIPT_DIR}/.venv"
PYTHON_BIN="${VENV_DIR}/bin/python"

export PYTHONPATH="${SCRIPT_DIR}/src${PYTHONPATH:+":${PYTHONPATH}"}"

ensure_environment() {
    uv sync >/dev/null
}

run_python_module() {
    if [[ ! -x "${PYTHON_BIN}" ]]; then
        echo "Error: expected Python interpreter at ${PYTHON_BIN} after uv sync" >&2
        exit 1
    fi
    "${PYTHON_BIN}" -m "$@"
}

validate_runtime() {
    ensure_environment
    run_python_module lazyups.validation runtime
}

validate_screens() {
    ensure_environment
    local delay="2"
    local screens_arg=()
    if [[ -n "${VALIDATION_SCREENS_VALUE:-}" ]]; then
        IFS=',' read -r -a screen_list <<< "${VALIDATION_SCREENS_VALUE}"
        screens_arg=("${screen_list[@]}")
    fi
    run_python_module lazyups.validation screens "${screens_arg[@]}" --delay "${delay}"
}

show_help() {
    cat <<'EOF'
LazyUPS runner script

Usage:
  ./run.sh [OPTIONS]

Options:
  --help                      Show this message and exit.
  --start-screen SCREEN       Launch LazyUPS directly into SCREEN. Valid screens:
                              monitor, details, settings.
  --validate-runtime          Import-check the runtime environment.
  --validate-screens          Cycle through all screens (2s each) headlessly.
  --validation-screens LIST   Comma-separated subset to use with --validate-screens.

Any additional arguments are passed through to the Textual CLI entrypoint
(`python -m lazyups.cli`).
EOF
}

ARGS=()
VALIDATE_RUNTIME=false
VALIDATE_SCREENS=false
VALIDATION_SCREENS_VALUE=""
START_SCREEN_VALUE=""
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --validate-runtime)
            VALIDATE_RUNTIME=true
            ;;
        --validate-screens)
            VALIDATE_SCREENS=true
            ;;
        --validation-screens)
            if [[ $# -lt 2 ]]; then
                echo "Error: --validation-screens requires a comma-separated argument" >&2
                exit 1
            fi
            VALIDATION_SCREENS_VALUE="$2"
            shift
            ;;
        --start-screen)
            if [[ $# -lt 2 ]]; then
                echo "Error: --start-screen requires a screen name" >&2
                exit 1
            fi
            START_SCREEN_VALUE="$2"
            shift
            ;;
        --help)
            SHOW_HELP=true
            ;;
        --)
            shift
            while [[ $# -gt 0 ]]; do
                ARGS+=("$1")
                shift
            done
            break
            ;;
        *)
            ARGS+=("$1")
            ;;
    esac
    shift
done

if "$SHOW_HELP"; then
    show_help
    exit 0
fi

DID_VALIDATION=false

if "$VALIDATE_RUNTIME"; then
    validate_runtime
    DID_VALIDATION=true
fi

if "$VALIDATE_SCREENS"; then
    validate_screens
    DID_VALIDATION=true
fi

# Validation commands are standalone checks; don't launch the main CLI afterward
# unless explicit app arguments were also provided.
if "$DID_VALIDATION" && [[ -z "${START_SCREEN_VALUE}" ]] && [[ ${#ARGS[@]} -eq 0 ]]; then
    exit 0
fi

if [[ -n "${START_SCREEN_VALUE}" ]]; then
    ARGS+=("--start-screen" "${START_SCREEN_VALUE}")
fi

ensure_environment
run_python_module lazyups.cli "${ARGS[@]}"
