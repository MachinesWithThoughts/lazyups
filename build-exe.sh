#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: 'uv' executable not found in PATH. Install uv from https://docs.astral.sh/uv/" >&2
    exit 127
fi

show_help() {
    cat <<'EOF'
Build a single-file LazyUPS executable (Linux).

Usage:
  ./build-exe.sh [OPTIONS]

Options:
  --clean        Remove previous build/ dist/ and lazyups.spec before building.
  --help         Show this message and exit.
EOF
}

CLEAN=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --clean)
            CLEAN=true
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Error: unsupported argument: $1" >&2
            exit 1
            ;;
    esac
    shift
done

if "$CLEAN"; then
    rm -rf build dist lazyups.spec
fi

uv sync --extra build >/dev/null

uv run pyinstaller \
    --noconfirm \
    --onefile \
    --name lazyups \
    --collect-data lazyups \
    pyinstaller_entrypoint.py

echo "Built executable: $(pwd)/dist/lazyups"
