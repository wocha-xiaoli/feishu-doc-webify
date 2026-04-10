#!/usr/bin/env bash
set -euo pipefail

SITE_DIR=""
REPO=""
VISIBILITY=""
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  publish_github_pages.sh --site-dir <dir> --repo <name> --visibility public|private [--dry-run]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --site-dir)
      SITE_DIR="$2"; shift 2 ;;
    --repo)
      REPO="$2"; shift 2 ;;
    --visibility)
      VISIBILITY="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=1; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$SITE_DIR" || -z "$REPO" || -z "$VISIBILITY" ]]; then
  usage >&2
  exit 2
fi

if [[ "$VISIBILITY" != "public" && "$VISIBILITY" != "private" ]]; then
  echo "--visibility must be public or private" >&2
  exit 2
fi

SITE_DIR="$(cd "$SITE_DIR" && pwd)"
if [[ ! -f "$SITE_DIR/index.html" ]]; then
  echo "Site directory must contain index.html: $SITE_DIR" >&2
  exit 1
fi

run() {
  if [[ "$DRY_RUN" == "1" ]]; then
    printf 'DRY RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

command -v gh >/dev/null || { echo "gh is required" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required" >&2; exit 1; }

if [[ "$DRY_RUN" != "1" ]]; then
  gh auth status >/dev/null
fi

OWNER="${GITHUB_OWNER:-}"
if [[ -z "$OWNER" ]]; then
  if [[ "$DRY_RUN" == "1" ]]; then
    OWNER="DRY_RUN_OWNER"
  else
    OWNER="$(gh api user --jq .login)"
  fi
fi

cd "$SITE_DIR"

if [[ ! -d .git ]]; then
  run git init
  run git branch -M main
fi

run git add .
if [[ "$DRY_RUN" != "1" ]]; then
  if git diff --cached --quiet; then
    echo "No site changes to commit."
  else
    git commit -m "publish Feishu document website"
  fi
else
  run git commit -m "publish Feishu document website"
fi

if [[ "$DRY_RUN" == "1" ]]; then
  run gh repo create "$REPO" "--$VISIBILITY" --source=. --remote=origin --push
  run gh api -X POST "/repos/$OWNER/$REPO/pages" -f 'source[branch]=main' -f 'source[path]=/'
  echo "https://$OWNER.github.io/$REPO/"
  exit 0
fi

if gh repo view "$OWNER/$REPO" >/dev/null 2>&1; then
  git remote remove origin >/dev/null 2>&1 || true
  git remote add origin "https://github.com/$OWNER/$REPO.git"
  git push -u origin main
else
  gh repo create "$REPO" "--$VISIBILITY" --source=. --remote=origin --push
fi

set +e
PAGES_OUTPUT="$(gh api -X POST "/repos/$OWNER/$REPO/pages" -f 'source[branch]=main' -f 'source[path]=/' 2>&1)"
PAGES_STATUS=$?
if [[ $PAGES_STATUS -ne 0 ]]; then
  PAGES_OUTPUT="$(gh api -X PUT "/repos/$OWNER/$REPO/pages" -f 'source[branch]=main' -f 'source[path]=/' 2>&1)"
  PAGES_STATUS=$?
fi
set -e

if [[ $PAGES_STATUS -ne 0 ]]; then
  echo "$PAGES_OUTPUT" >&2
  if [[ "$VISIBILITY" == "private" ]]; then
    echo "Private GitHub Pages may not be available for this account or repository. The script did not switch the repository to public." >&2
  fi
  exit 1
fi

echo "https://$OWNER.github.io/$REPO/"

