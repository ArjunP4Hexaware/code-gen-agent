#!/usr/bin/env bash
# Single-port demo launcher: build the frontend if stale, then serve the
# whole UI (API + built frontend) from one FastAPI process on :8571
# (override with CODEGEN_UI_PORT / DATABRICKS_APP_PORT; see ui/README.md).
set -euo pipefail
cd "$(dirname "$0")"

FRONTEND=ui/frontend
DIST="$FRONTEND/dist"

if [ ! -d "$FRONTEND/node_modules" ]; then
  echo "== npm install (first run) =="
  (cd "$FRONTEND" && npm install)
fi

# Rebuild when no build exists or any source/config input is newer than it.
if [ ! -f "$DIST/index.html" ] || [ -n "$(find "$FRONTEND/src" "$FRONTEND/index.html" "$FRONTEND/package.json" "$FRONTEND/vite.config.ts" -newer "$DIST/index.html" -print -quit)" ]; then
  echo "== frontend build stale — rebuilding =="
  (cd "$FRONTEND" && npm run build)
fi

exec .venv/bin/python -m ui.backend.main
