#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: 'uv' executable not found in PATH. Install uv from https://docs.astral.sh/uv/" >&2
    exit 127
fi

exec uv run lazyups "$@"
