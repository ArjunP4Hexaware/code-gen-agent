#!/usr/bin/env bash
# Deploy an App and prove it (AGENTS.md "Deploying"): the /ship-dev and /ship-staging
# skills run this. Steps: the branch is pushed -> the App is idle -> (staging: the
# identical-tree merge of feature onto main, pushed as a fast-forward) -> deploy (one
# retry: Databricks-side git hiccups are transient) -> on a failed deploy the LAST GOOD
# commit is deployed back at once (a failed deploy takes the App down) -> /api/health
# names the version in pyproject.toml -> the Playwright smoke (Generate + Results 200,
# 0 console errors).
#
#   tools/check/ship.sh dev
#   tools/check/ship.sh staging --approved     # only on Soham's word
#
# Needs: the OAuth profile (CODEGEN_OAUTH_CFG, default /tmp/cgs/oauth.cfg; profile
# CODEGEN_OAUTH_PROFILE, default codegen-oaut - the DEFAULT PAT can deploy but not call
# the App's API), node + dev_bootstrap's Chromium (/tmp/pw, /tmp/pwlibs).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TOOLS="$REPO/tools/check"
export DATABRICKS_CONFIG_FILE="${CODEGEN_OAUTH_CFG:-/tmp/cgs/oauth.cfg}"
PROFILE="${CODEGEN_OAUTH_PROFILE:-codegen-oaut}"
target="${1:-}"; approved="${2:-}"
case "$target" in
  dev)     app=codegen-agent;         branch=feature/multi-table ;;
  staging) app=codegen-agent-staging; branch=main
           [ "$approved" = "--approved" ] || { echo "staging needs --approved (Soham's word)"; exit 2; } ;;
  *) sed -n '2,17p' "$0"; exit 2 ;;
esac
say() { printf '%s %s\n' "[$target]" "$*"; }

git -C "$REPO" fetch -q
head=$(git -C "$REPO" rev-parse HEAD)
[ "$head" = "$(git -C "$REPO" rev-parse origin/feature/multi-table)" ] \
  || { say "HEAD is not origin/feature/multi-table - push (after the suites) first"; exit 1; }
want=$(sed -n 's/^version = "\(.*\)"/\1/p' "$REPO/pyproject.toml")

state=$("$REPO/.venv/bin/python" -I "$TOOLS/app_api.py" "$app" GET /api/demo/status --field state)
case "$state" in
  idle|done|failed|cancelled|"") say "App state: ${state:-unknown} - ok to deploy" ;;
  *) say "App is busy ($state) - someone is running; not deploying"; exit 1 ;;
esac

last_good=$(databricks apps get "$app" -p "$PROFILE" -o json | python3 -c "
import sys, json
d = json.load(sys.stdin).get('active_deployment') or {}
print((d.get('git_source') or {}).get('resolved_commit') or '')")
say "last good commit: ${last_good:-unknown}"

if [ "$target" = staging ]; then
  feature=$(git -C "$REPO" rev-parse origin/feature/multi-table)
  main=$(git -C "$REPO" rev-parse origin/main)
  if [ "$(git -C "$REPO" rev-parse "$feature^{tree}")" = "$(git -C "$REPO" rev-parse "$main^{tree}")" ]; then
    say "main already has feature's tree - no merge"
  else
    ver=$want
    msg=$(printf 'Merge feature/multi-table into main: %s (staging)\n\nCo-Authored-By: Claude <noreply@anthropic.com>\n' "${ver##*.}")
    merge=$(git -C "$REPO" commit-tree "$feature^{tree}" -p "$main" -p "$feature" -m "$msg")
    [ -z "$(git -C "$REPO" diff "$merge" "$feature")" ] || { say "merge tree differs from feature"; exit 1; }
    git -C "$REPO" push -q origin "$merge:refs/heads/main"
    say "main -> $(git -C "$REPO" rev-parse --short "$merge") (identical-tree merge, fast-forward)"
  fi
fi

deploy() {   # deploy <json>; prints "<state> <commit>"
  databricks apps deploy "$app" -p "$PROFILE" --json "$1" -o json 2>&1 | python3 -c "
import sys, json
t = sys.stdin.read()
try:
    d = json.loads(t)
    print((d.get('status') or {}).get('state'), (d.get('git_source') or {}).get('resolved_commit'))
except ValueError:
    print('ERROR', t.strip().splitlines()[-1][:200] if t.strip() else '')"
}
spec="{\"mode\":\"SNAPSHOT\",\"git_source\":{\"branch\":\"$branch\"}}"
result=$(deploy "$spec"); say "deploy: $result"
if [ "${result%% *}" != SUCCEEDED ]; then
  say "retrying once (transient Databricks-side failures are known)"
  result=$(deploy "$spec"); say "deploy: $result"
fi
if [ "${result%% *}" != SUCCEEDED ]; then
  if [ -n "$last_good" ]; then
    say "FAILED - restoring the last good commit $last_good"
    say "restore: $(deploy "{\"mode\":\"SNAPSHOT\",\"git_source\":{\"commit\":\"$last_good\"}}")"
  fi
  say "stop and ask (spiral log 2026-11-06)"; exit 1
fi

url=$(databricks apps get "$app" -p "$PROFILE" -o json | python3 -c "import sys,json;print(json.load(sys.stdin)['url'].rstrip('/'))")
version=""
for _ in $(seq 1 10); do   # ~30 s after a deploy /api/health may answer non-JSON
  version=$("$REPO/.venv/bin/python" -I "$TOOLS/app_api.py" "$app" GET /api/health --field version 2>/dev/null || true)
  [ "$version" = "$want" ] && break
  sleep 15
done
[ "$version" = "$want" ] || { say "health names '$version', expected $want"; exit 1; }
say "health: $version"

export CODEGEN_BEARER
CODEGEN_BEARER=$(databricks auth token -p "$PROFILE" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
export LD_LIBRARY_PATH="/tmp/pwlibs/usr/lib/x86_64-linux-gnu:/tmp/pwlibs/lib/x86_64-linux-gnu"
export PLAYWRIGHT_BROWSERS_PATH=/tmp/pw
shots="${TMPDIR:-/tmp}/ship_$target"; mkdir -p "$shots"
node "$TOOLS/smoke.cjs" "$url/" "$shots/generate.png"
node "$TOOLS/smoke.cjs" "$url/results" "$shots/results.png"
say "OK - $app on $want ($(git -C "$REPO" rev-parse --short "$branch" 2>/dev/null || echo "$branch")), smoke green"
