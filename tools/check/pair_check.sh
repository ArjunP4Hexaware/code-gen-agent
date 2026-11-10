#!/usr/bin/env bash
# The 12-pair check (AGENTS.md "Proving a fix"): the container harness, MOCK, framework
# mode, on every real pair - the old tree vs the new one, comparing outcomes and the
# artefacts' hashes. Kinds and counts only are printed; the client copies stay under
# $PAIR_CHECK_DIR (default /tmp/t/pairs) and `cleanup` deletes them.
#
#   tools/check/pair_check.sh run [<old-sha>]   # prepare + both sides + compare + classify
#   tools/check/pair_check.sh compare           # re-print the comparison
#   tools/check/pair_check.sh cleanup           # delete the copies + the worktree
#
# <old-sha> defaults to HEAD~1 (resolved with git rev-parse - never type a sha).
# The NEW side is this checkout's committed HEAD (run it on a clean src/ + config/).
# Cache: a finished side is kept under $PAIR_CHECK_DIR/cache/<tree>, keyed by its code
# TREE (src/ + config/ + scripts/), so the next version's OLD side is this version's NEW
# one - not re-run. Each side warms its layout cache (pair 1) before the full run.
# Needs: the Databricks CLI login (Workspace + volume reads), .venv-d1.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RP="${PAIR_CHECK_DIR:-/tmp/t/pairs}"
PY="$REPO/.venv-d1/bin/python"
TOOLS="$REPO/tools/check"
PAIRS="${PAIR_CHECK_PAIRS:-1,2,3,4,5,6,7,8,9,10,11,12}"
PROFILE="${DATABRICKS_PROFILE_ARG:-}"         # e.g. "--profile DEFAULT"; empty = the default

tree_key() {   # the code tree a run depends on (docs-only commits share a key)
  git -C "$1" rev-parse "HEAD:src" "HEAD:config" "HEAD:scripts" | sha1sum | cut -c1-16
}

prepare() {
  mkdir -p "$RP"
  if [ ! -d "$RP/pairs" ]; then
    me=$(databricks current-user me $PROFILE -o json | python3 -c "import sys,json;print(json.load(sys.stdin)['userName'])")
    databricks workspace export-dir "/Workspace/Users/$me/frd_sttm_pairs" "$RP/pairs" $PROFILE >/dev/null
  fi
  if [ ! -d "$RP/state_src" ]; then
    mkdir -p "$RP/state_src"
    for sub in environments overlays leakgate answers; do
      databricks fs cp -r "dbfs:/Volumes/d1_dlk/codegen/state/$sub" "$RP/state_src/$sub" $PROFILE >/dev/null
    done
  fi
  echo "pairs: $(ls "$RP/pairs" | wc -l) dirs; state subdirs: $(ls "$RP/state_src" | wc -l)"
}

run_side() {   # run_side <side> <tree dir>; reuses the cache for that tree
  local side=$1 tree=$2 key; key=$(tree_key "$tree")
  rm -rf "$RP/work_$side" "$RP/out_$side"
  if [ -d "$RP/cache/$key/work" ]; then
    cp -r "$RP/cache/$key/work" "$RP/work_$side"; cp -r "$RP/cache/$key/out" "$RP/out_$side"
    echo "$side: cached (tree $key)"; return
  fi
  rm -rf "$RP/state_$side"; cp -r "$RP/state_src" "$RP/state_$side"
  for pass in warm full; do
    local pairs=$PAIRS; [ "$pass" = warm ] && pairs=1
    rm -rf "$RP/out_$side" "$RP/work_$side"
    ( cd /tmp && PYTHONUTF8=1 CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example \
        "$PY" "$tree/scripts/container_harness.py" --pairs-dir "$RP/pairs" \
        --state-dir "$RP/state_$side" --out "$RP/out_$side" --work "$RP/work_$side" \
        --pairs "$pairs" --dry-run --output-mode framework ) > "$RP/harness_${side}_$pass.log" 2>&1 \
        || echo "harness $side $pass exit $? (see $RP/harness_${side}_$pass.log)"
  done
  mkdir -p "$RP/cache/$key"; rm -rf "$RP/cache/$key/work" "$RP/cache/$key/out"
  cp -r "$RP/work_$side" "$RP/cache/$key/work"; cp -r "$RP/out_$side" "$RP/cache/$key/out"
  echo "$side: ran (tree $key)"
}

compare() {
  python3 -I "$TOOLS/outcomes.py" "$RP/out_old" "$RP/out_new"
  "$REPO/.venv/bin/python" -I "$TOOLS/classify.py" "$RP/work_old" "$RP/work_new"
}

case "${1:-}" in
run)
  old_sha=$(git -C "$REPO" rev-parse "${2:-HEAD~1}")
  if [ -n "$(git -C "$REPO" status --porcelain -- src config scripts)" ]; then
    echo "src/ config/ scripts/ have uncommitted changes - commit first (the NEW side is HEAD)"
    exit 2
  fi
  prepare
  if [ ! -d "$RP/old" ] || [ "$(git -C "$RP/old" rev-parse HEAD 2>/dev/null)" != "$old_sha" ]; then
    git -C "$REPO" worktree remove --force "$RP/old" >/dev/null 2>&1 || true
    git -C "$REPO" worktree add --detach "$RP/old" "$old_sha" >/dev/null 2>&1
  fi
  echo "old = $(git -C "$RP/old" rev-parse --short HEAD), new = $(git -C "$REPO" rev-parse --short HEAD)"
  run_side old "$RP/old"
  run_side new "$REPO"
  compare
  ;;
compare) compare ;;
cleanup)
  git -C "$REPO" worktree remove --force "$RP/old" >/dev/null 2>&1 || true
  git -C "$REPO" worktree prune
  rm -rf "$RP"
  echo "cleaned: $( [ -e "$RP" ] && echo still-there || echo gone )"
  ;;
*) sed -n '2,17p' "$0"; exit 2 ;;
esac
