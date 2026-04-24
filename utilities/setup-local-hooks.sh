#!/usr/bin/env bash
# setup-local-hooks.sh — create local Claude Code hooks and .env stub
# Run once from the repo root after cloning or on a new machine.
# None of the files this creates are committed (.claude/ and .env are gitignored).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "[setup] Working in: $REPO_ROOT"

# ── .env ──────────────────────────────────────────────────────────────────────
if [ -f .env ]; then
  echo "[setup] .env already exists — skipping (edit it manually if needed)"
else
  cat > .env << 'EOF'
# GitHub PAT for workflow_dispatch trigger (used by .claude/hooks/stop.sh)
# Scopes needed: actions:write (fine-grained) or repo+workflow (classic)
# Generate at: https://github.com/settings/tokens
GITHUB_PAT=ghp_REPLACE_ME
EOF
  echo "[setup] Created .env — add your PAT before using the Stop hook"
fi

# ── .claude/settings.local.json ───────────────────────────────────────────────
mkdir -p .claude/hooks

if [ -f .claude/settings.local.json ]; then
  echo "[setup] .claude/settings.local.json already exists — skipping"
else
  cat > .claude/settings.local.json << 'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "command": "git fetch origin main 2>/dev/null && git rebase origin/main --autostash 2>/dev/null && echo '[sync] Rebased onto origin/main' || echo '[sync] Rebase skipped or failed — manual merge may be needed'"
      }
    ],
    "Stop": [
      {
        "command": "bash .claude/hooks/stop.sh"
      }
    ]
  }
}
EOF
  echo "[setup] Created .claude/settings.local.json"
fi

# ── .claude/hooks/stop.sh ─────────────────────────────────────────────────────
if [ -f .claude/hooks/stop.sh ]; then
  echo "[setup] .claude/hooks/stop.sh already exists — skipping"
else
  cat > .claude/hooks/stop.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

source .env 2>/dev/null || true

BRANCH=$(git rev-parse --abbrev-ref HEAD)
git fetch origin main 2>/dev/null

AHEAD=$(git log origin/main..HEAD --oneline 2>/dev/null | wc -l | tr -d ' ')

if [ "$AHEAD" -eq 0 ]; then
  echo "[stop hook] No new commits beyond origin/main — skipping pipeline trigger."
  exit 0
fi

echo "[stop hook] $AHEAD commit(s) ahead of origin/main on branch: $BRANCH"

MAIN_AHEAD=$(git log HEAD..origin/main --oneline 2>/dev/null | wc -l | tr -d ' ')

if [ "$MAIN_AHEAD" -eq 0 ]; then
  echo "[stop hook] Triggering workflow_dispatch on main..."
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    -H "Authorization: token $GITHUB_PAT" \
    -H "Accept: application/vnd.github+json" \
    https://api.github.com/repos/mofro/tarim-shaiel-campaign-frame/actions/workflows/generate-html.yml/dispatches \
    -d '{"ref":"main"}')
  echo "[stop hook] GitHub API response: $HTTP"
  [ "$HTTP" = "204" ] && echo "[stop hook] Pipeline triggered." || echo "[stop hook] Warning: unexpected response $HTTP"
else
  echo "[stop hook] origin/main has $MAIN_AHEAD new commit(s) — diverged. Skipping auto-trigger."
fi
EOF
  chmod +x .claude/hooks/stop.sh
  echo "[setup] Created .claude/hooks/stop.sh"
fi

echo ""
echo "[setup] Done. Next steps:"
echo "  1. Edit .env and replace 'ghp_REPLACE_ME' with your GitHub PAT"
echo "  2. Start a Claude Code session to test the SessionStart hook"
