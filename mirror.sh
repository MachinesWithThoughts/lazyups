#!/usr/bin/env bash
set -euo pipefail

# Mirror LazyUPS to public repo remote.
#
# Usage:
#   ./mirror.sh                                # bootstrap remote + push main + tags (default)
#   ./mirror.sh --main-only                    # push only main
#   ./mirror.sh --all                          # push all branches + tags
#   ./mirror.sh --force                        # force-push selected refs
#   ./mirror.sh --dry-run                      # show what would be pushed
#   ./mirror.sh                                # push main+tags and mirror latest release (default)
#   ./mirror.sh --create-release <tag>         # create/update public GitHub release for tag
#   ./mirror.sh --create-latest-release        # create/update release for latest local tag

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REMOTE_NAME="public"
REMOTE_URL="git@github-tamclaw-tamclaw__lazyups-machineswiththoughts:machineswiththoughts/lazyups.git"
PUBLIC_REPO="MachinesWithThoughts/lazyups"
PRIVATE_REPO="tamclaw1000/lazyups"

PUSH_MAIN=true
PUSH_TAGS=true
PUSH_ALL=false
FORCE=false
DRY_RUN=false
CREATE_RELEASE_TAG=""
CREATE_LATEST_RELEASE=true

for arg in "$@"; do
  case "$arg" in
    --main-only)
      PUSH_MAIN=true
      PUSH_TAGS=false
      PUSH_ALL=false
      ;;
    --with-tags)
      PUSH_MAIN=true
      PUSH_TAGS=true
      PUSH_ALL=false
      ;;
    --all)
      PUSH_ALL=true
      PUSH_MAIN=false
      PUSH_TAGS=true
      ;;
    --force)
      FORCE=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --create-latest-release)
      CREATE_LATEST_RELEASE=true
      ;;
    --create-release)
      shift
      CREATE_RELEASE_TAG="${1:-}"
      if [[ -z "$CREATE_RELEASE_TAG" ]]; then
        echo "Error: --create-release requires a tag (e.g. v01.02.00)" >&2
        exit 2
      fi
      ;;
    --help|-h)
      sed -n '1,24p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not inside a git repository" >&2
  exit 1
fi

# Ensure mirror remote exists and is correct.
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  current_url="$(git remote get-url "$REMOTE_NAME")"
  if [[ "$current_url" != "$REMOTE_URL" ]]; then
    echo "Updating remote '$REMOTE_NAME' URL"
    git remote set-url "$REMOTE_NAME" "$REMOTE_URL"
  fi
else
  echo "Adding remote '$REMOTE_NAME'"
  git remote add "$REMOTE_NAME" "$REMOTE_URL"
fi

echo "Verifying remote access..."
git ls-remote "$REMOTE_NAME" >/dev/null

push_flags=()
$FORCE && push_flags+=(--force)
$DRY_RUN && push_flags+=(--dry-run)

git fetch origin --prune >/dev/null 2>&1 || true

run_push() {
  local desc="$1"
  shift
  local log_file
  log_file="$(mktemp)"

  echo "$desc"
  if git push "$@" 2>"$log_file"; then
    rm -f "$log_file"
    return 0
  fi

  cat "$log_file" >&2
  if ! $FORCE && grep -qiE "\[rejected\].*\(fetch first\)|non-fast-forward" "$log_file"; then
    echo >&2
    echo "Mirror push rejected (non-fast-forward)." >&2
    echo "If this mirror remote should be overwritten, rerun with:" >&2
    echo "  ./mirror.sh --force" >&2
  fi
  rm -f "$log_file"
  exit 1
}

if $PUSH_ALL; then
  run_push "Pushing all branches to $REMOTE_NAME..." "${push_flags[@]}" "$REMOTE_NAME" --all
else
  if $PUSH_MAIN; then
    run_push "Pushing main to $REMOTE_NAME..." "${push_flags[@]}" "$REMOTE_NAME" main
  fi
fi

if $PUSH_TAGS; then
  run_push "Pushing tags to $REMOTE_NAME..." "${push_flags[@]}" "$REMOTE_NAME" --tags
fi

if $CREATE_LATEST_RELEASE; then
  CREATE_RELEASE_TAG="$(git tag --sort=-v:refname | head -n 1)"
fi

if [[ -n "$CREATE_RELEASE_TAG" ]]; then
  if ! command -v gh >/dev/null 2>&1; then
    echo "Error: gh is required for --create-release/--create-latest-release" >&2
    exit 1
  fi

  echo "Creating/updating public release for tag $CREATE_RELEASE_TAG..."

  if gh release view "$CREATE_RELEASE_TAG" --repo "$PUBLIC_REPO" >/dev/null 2>&1; then
    echo "Release already exists in $PUBLIC_REPO: $CREATE_RELEASE_TAG"
  else
    NOTES=""
    if gh release view "$CREATE_RELEASE_TAG" --repo "$PRIVATE_REPO" >/dev/null 2>&1; then
      NOTES="$(gh release view "$CREATE_RELEASE_TAG" --repo "$PRIVATE_REPO" --json body --jq .body)"
    fi

    if [[ -z "$NOTES" ]]; then
      NOTES="Mirrored release for $CREATE_RELEASE_TAG"
    fi

    gh release create "$CREATE_RELEASE_TAG" \
      --repo "$PUBLIC_REPO" \
      --title "$CREATE_RELEASE_TAG" \
      --notes "$NOTES" >/dev/null

    echo "Created release: https://github.com/$PUBLIC_REPO/releases/tag/$CREATE_RELEASE_TAG"
  fi
fi

echo "Verifying mirrored refs (summary)..."
head_count="$(git ls-remote --heads "$REMOTE_NAME" | wc -l | tr -d ' ')"
tag_count="$(git ls-remote --tags "$REMOTE_NAME" | wc -l | tr -d ' ')"
echo "- Heads on $REMOTE_NAME: $head_count"
echo "- Tag refs on $REMOTE_NAME: $tag_count"

echo "Mirror push complete."
