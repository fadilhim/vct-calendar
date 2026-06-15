#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT_DIR/logs"
LOG_FILE="$LOG_DIR/update-calendar.log"
LOCK_FILE="$ROOT_DIR/.calendar-update.lock"
CALENDAR_FILE="${CALENDAR_FILE:-vct-2026.ics}"
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"
STAGES=(kickoff masters stage1 stage2 champions)

mkdir -p "$LOG_DIR"
exec >>"$LOG_FILE" 2>&1

if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK_FILE"
  if ! flock -n 9; then
    echo "[$(date -Is)] Another calendar update is already running; exiting."
    exit 0
  fi
fi

log() {
  echo "[$(date -Is)] $*"
}

abort() {
  log "ERROR: $*"
  exit 1
}

cd "$ROOT_DIR"

log "Starting calendar update job"

[[ -x "$PYTHON_BIN" ]] || abort "Python executable not found at $PYTHON_BIN. Create the venv and install requirements first."
[[ -f "$CALENDAR_FILE" ]] || abort "Calendar file $CALENDAR_FILE not found."

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || abort "Not inside a git work tree."

current_branch="$(git branch --show-current)"
[[ "$current_branch" == "$BRANCH" ]] || abort "Expected branch $BRANCH, but checkout is on $current_branch."

if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  git status --short --untracked-files=all
  abort "Working tree is not clean before update; refusing to commit unrelated changes."
fi

log "Fetching latest $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"
git pull --ff-only "$REMOTE" "$BRANCH"

log "Refreshing all known stages: ${STAGES[*]}"
"$PYTHON_BIN" update_calendar.py \
  --stage kickoff \
  --stage masters \
  --stage stage1 \
  --stage stage2 \
  --stage champions

changed_files="$(git diff --name-only)"
if [[ -z "$changed_files" ]]; then
  log "No calendar changes to push"
  log "Calendar update job finished successfully"
  exit 0
fi

if [[ "$changed_files" != "$CALENDAR_FILE" ]]; then
  git status --short
  abort "Unexpected files changed: $changed_files"
fi

log "Committing updated $CALENDAR_FILE"
git add "$CALENDAR_FILE"
git commit -m "chore: update calendar" -- "$CALENDAR_FILE"

log "Pushing $BRANCH to $REMOTE"
git push "$REMOTE" "$BRANCH"

log "Calendar update job finished successfully"
