#!/usr/bin/env bash
# VPS hourly recorder — the reliable replacement for GitHub's scheduled Action.
#
# Why this exists: the record-hourly GitHub Action fired on schedule once in ~15 hours against an
# hourly cron (2026-10-01). GitHub throttles/skips scheduled runs on private repos, and every missed
# hour of liquidation/OI/funding data is gone permanently. A plain cron on the VPS does not get skipped.
#
# This mirrors .github/workflows/record-hourly.yml EXACTLY — same collectors, same order, same commit.
# It honours CLAUDE.md with no exceptions: read-only public endpoints, the two data-only keys, NO
# exchange keys, NO orders, raw/ append-only.
#
# One-time setup:
#   1. Put your two READ-ONLY data keys in ~/.config/database-recorder.env (created below if missing).
#   2. Run:  bash collectors/vps_recorder_setup.sh --install
#   3. Confirm:  crontab -l   (you should see the record-hourly line)
#      and after the next :07, check:  tail ~/database-recorder.log
#
# Run the chain once by hand (no cron):  bash collectors/vps_recorder_setup.sh --once
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/database}"
REPO_URL="${REPO_URL:-https://github.com/clay10fields/database.git}"
ENV_FILE="${ENV_FILE:-$HOME/.config/database-recorder.env}"
LOG="${LOG:-$HOME/database-recorder.log}"
BRANCH="main"

ensure_env () {
  if [[ ! -f "$ENV_FILE" ]]; then
    mkdir -p "$(dirname "$ENV_FILE")"
    cat > "$ENV_FILE" <<'EOF'
# Read-only market-data keys ONLY (see collectors/SECRETS.md). NO exchange keys, ever.
COINALYZE_API_KEY=
COINGECKO_API_KEY=
EOF
    chmod 600 "$ENV_FILE"
    echo "Created $ENV_FILE — put your two read-only keys in it, then re-run." >&2
    exit 1
  fi
}

run_once () {
  ensure_env
  set -a; # shellcheck disable=SC1090
  source "$ENV_FILE"; set +a
  if [[ ! -d "$REPO_DIR/.git" ]]; then
    git clone "$REPO_URL" "$REPO_DIR"
  fi
  cd "$REPO_DIR"
  git checkout -q "$BRANCH"
  git pull -q --rebase --autostash origin "$BRANCH" || true

  # Same steps as the workflow. continue-on-error on the collectors: one dead venue must not
  # stop the others or the commit. resample/signals/paper_books run regardless.
  python3 collectors/coinalyze_hourly.py  --out raw/coinalyze_1h   || echo "WARN coinalyze failed"
  python3 collectors/kraken_hourly.py     --out raw/kraken_1h      || echo "WARN kraken failed"
  python3 collectors/coinbase_hourly.py   --out raw/coinbase_1h    || echo "WARN coinbase failed"
  python3 collectors/binance_us_hourly.py --out raw/binance_us_1h  || echo "WARN binance_us failed"
  python3 collectors/kalshi_hourly.py     --out raw/kalshi_1h      || echo "WARN kalshi failed"
  python3 collectors/resample.py
  python3 collectors/signals.py      || echo "WARN signals failed"
  python3 collectors/paper_books.py  || echo "WARN paper_books failed"

  git config user.name  "database-recorder"
  git config user.email "recorder@users.noreply.github.com"
  git add raw/coinalyze_1h raw/kraken_1h raw/coinbase_1h raw/binance_us_1h raw/kalshi_1h derived
  git diff --cached --quiet || git commit -qm "record: $(date -u +%Y-%m-%dT%H:%MZ)"
  git pull -q --rebase --autostash origin "$BRANCH" && git push -q origin "$BRANCH"
  echo "record ok $(date -u +%Y-%m-%dT%H:%MZ)"
}

install_cron () {
  ensure_env
  local self; self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  local line="7 * * * * /usr/bin/env bash $self --once >> $LOG 2>&1"
  # idempotent: drop any prior record line, add this one
  ( crontab -l 2>/dev/null | grep -v "vps_recorder_setup.sh --once" ; echo "$line" ) | crontab -
  echo "Installed hourly cron (minute :07). Logs -> $LOG"
  echo "Verify with: crontab -l"
}

case "${1:---once}" in
  --install) install_cron ;;
  --once)    run_once ;;
  *) echo "usage: $0 [--install | --once]" >&2; exit 2 ;;
esac
