#!/usr/bin/env bash
# For each task: hidden test must FAIL on <commit>^ and PASS on <commit>.
set -u
REPO=/app/python/source_code/projects/code-gen-agent
PY=$REPO/.venv/bin/python
export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null
export CODEGEN_BLOCK_LIVE_MODEL=1
mkdir -p /tmp/t/eval/oracle
for spec in "t1 6c05d20 tests/test_edo_sfmc_comments.py" "t2 cba0759 tests/test_layout_repeated_band.py" \
            "t3 782bebf tests/test_run_artefacts.py" "t4 4a06ade tests/test_ddl_types_gate.py"; do
  set -- $spec; t=$1 c=$2 test=$3
  for side in parent fixed; do
    wt=/tmp/t/eval/oracle/$t-$side
    ref=$c; [ $side = parent ] && ref=$c^
    git -C $REPO worktree add -q --detach $wt $ref 2>/dev/null
    git -C $REPO show $c:$test > $wt/$test
    sel=""; [ $t = t3 ] && sel="-k a_rerun_that_keeps_no_feed"
    (cd $wt && PYTHONPATH=$wt/src timeout 600 $PY -m pytest -q -p no:cacheprovider $test $sel >/tmp/t/eval/oracle/$t-$side.log 2>&1)
    echo "$t $side rc=$? $(tail -1 /tmp/t/eval/oracle/$t-$side.log)"
    git -C $REPO worktree remove --force $wt
  done
done
