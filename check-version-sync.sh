#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

APP_VERSION="$(python3 - <<'PY'
from pathlib import Path
import re
text = Path('src/lazyups/version.py').read_text(encoding='utf-8')
match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
if not match:
    raise SystemExit('Could not find __version__ in src/lazyups/version.py')
print(match.group(1))
PY
)"

PROJECT_VERSION="$(python3 - <<'PY'
from pathlib import Path
import re
text = Path('pyproject.toml').read_text(encoding='utf-8')
match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
if not match:
    raise SystemExit('Could not find project version in pyproject.toml')
print(match.group(1))
PY
)"

if [[ "$APP_VERSION" != "$PROJECT_VERSION" ]]; then
    echo "Version mismatch:" >&2
    echo "  src/lazyups/version.py: $APP_VERSION" >&2
    echo "  pyproject.toml:       $PROJECT_VERSION" >&2
    exit 1
fi

if git rev-parse --git-dir >/dev/null 2>&1; then
    if LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
        EXPECTED_TAG="v${APP_VERSION}"
        if [[ "$LATEST_TAG" != "$EXPECTED_TAG" ]]; then
            echo "Version/tag mismatch:" >&2
            echo "  app version: $APP_VERSION" >&2
            echo "  latest tag:  $LATEST_TAG" >&2
            echo "  expected:    $EXPECTED_TAG" >&2
            exit 1
        fi
    fi
fi

echo "Version sync OK: $APP_VERSION"
