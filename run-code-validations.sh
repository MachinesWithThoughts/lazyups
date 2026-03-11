#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: 'uv' executable not found in PATH. Install uv from https://docs.astral.sh/uv/" >&2
    exit 127
fi

show_help() {
    cat <<'EOF'
LazyUPS validation runner

Usage:
  ./run-code-validations.sh [OPTIONS]

Options:
  --help                      Show this message and exit.
  --validate-runtime          Import-check the runtime environment.
  --validate-screens          Cycle through all screens (2s each) headlessly.
  --validation-screens LIST   Comma-separated subset to use with --validate-screens.
EOF
}

VALIDATE_RUNTIME=false
VALIDATE_SCREENS=false
VALIDATION_SCREENS_VALUE=""
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
        --help)
            SHOW_HELP=true
            ;;
        *)
            echo "Error: unsupported validation argument: $1" >&2
            exit 1
            ;;
    esac
    shift
done

if "$SHOW_HELP"; then
    show_help
    exit 0
fi

if ! "$VALIDATE_RUNTIME" && ! "$VALIDATE_SCREENS"; then
    echo "Error: no validation mode selected. Use --validate-runtime and/or --validate-screens." >&2
    exit 1
fi

if "$VALIDATE_RUNTIME"; then
    uv run python -m lazyups.validation runtime
fi

if "$VALIDATE_SCREENS"; then
    if [[ -n "${VALIDATION_SCREENS_VALUE}" ]]; then
        IFS=',' read -r -a SCREEN_LIST <<<"${VALIDATION_SCREENS_VALUE}"
        uv run python -m lazyups.validation screens "${SCREEN_LIST[@]}" --delay 2
    else
        uv run python -m lazyups.validation screens --delay 2
    fi
fi
