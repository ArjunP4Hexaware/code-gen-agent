#!/usr/bin/env bash
# Local mock App for browser checks. Everything it writes lives under /tmp/t/ui.
# Usage: tools/check/serve_local.sh [port]   (default 8599; state under $LOCAL_APP_DIR,
# default /tmp/t/ui). Stop it with: kill "$(cat "$LOCAL_APP_DIR/server.pid")" - never pkill -f
# a pattern your own command line contains (it kills that shell too).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PORT=${1:-8599}
W="${LOCAL_APP_DIR:-/tmp/t/ui}"
mkdir -p "$W/inputs" "$W/state" "$W/outputs" "$W/codegen-state"
cd "$REPO"
export DATABRICKS_APP_PORT=$PORT          # the container sets 8000; the backend reads this first
export CODEGEN_UI_HOST=127.0.0.1
export CODEGEN_PROVIDER=mock
export CODEGEN_FORCE_MOCK_PROVIDER=1
export CODEGEN_STORAGE_INPUTS="local:$W/inputs"
export CODEGEN_STORAGE_STATE="local:$W/state"
export CODEGEN_STORAGE_OUTPUTS="local:$W/outputs"
export CODEGEN_STATE_DIR="$W/codegen-state"
export CODEGEN_EXTRA_INPUT_DIRS="local:$REPO/fixtures/acfc_shapes/pair_4"   # synthetic pair
export CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example
echo $$ > "$W/server.pid"
exec .venv/bin/python -m uvicorn ui.backend.main:app --host 127.0.0.1 --port "$PORT"
