"""Call a deployed App's API with the OAuth profile (the DEFAULT PAT is refused).

    python -I tools/check/app_api.py <app> GET /api/demo/status [--field state]
    python -I tools/check/app_api.py <app> POST /api/demo/workbook '{"name": "..."}'

<app> = the Databricks App name (codegen-agent / codegen-agent-staging); its URL is read
from `databricks apps get`. Env: CODEGEN_OAUTH_CFG (default /tmp/cgs/oauth.cfg),
CODEGEN_OAUTH_PROFILE (default codegen-oaut). A run on an App is LIVE (client documents
go to the model): report pair / outcome / counts only."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

CFG = os.environ.get("CODEGEN_OAUTH_CFG", "/tmp/cgs/oauth.cfg")
PROFILE = os.environ.get("CODEGEN_OAUTH_PROFILE", "codegen-oaut")


def _cli(*args: str) -> dict:
    out = subprocess.run(["databricks", *args, "-p", PROFILE, "-o", "json"], check=True,
                         capture_output=True, text=True,
                         env={**os.environ, "DATABRICKS_CONFIG_FILE": CFG})
    return json.loads(out.stdout)


def client(app: str):
    url = _cli("apps", "get", app)["url"].rstrip("/")
    token = _cli("auth", "token")["access_token"]

    def call(method: str, path: str, body: dict | None = None, timeout: int = 60):
        req = urllib.request.Request(
            url + path, method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return r.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode(errors="replace")[:500]
    return call


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    field = None
    if "--field" in argv:
        i = argv.index("--field")
        field, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    app, method, path = argv[:3]
    body = json.loads(argv[3]) if len(argv) > 3 else None
    status, data = client(app)(method.upper(), path, body)
    if field is not None:
        if status != 200 or not isinstance(data, dict):
            return 1
        print(data.get(field) if data.get(field) is not None else "")
        return 0
    print(status)
    print(json.dumps(data, indent=1)[:int(os.environ.get("APP_API_CHARS", "4000"))])
    return 0 if status < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
