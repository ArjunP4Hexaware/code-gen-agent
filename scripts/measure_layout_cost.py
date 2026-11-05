"""Measure a new pair's first layout read on the deployed DEV App, pair by pair.

LIVE: every pair sends its documents to the model (about 5 DBU each). Check the App
is idle first (Soham uses it too). A refresh OVERWRITES each pair's cached layout in
the state role (and tombstones a document it cannot fully place), so back up
`<state>/layout_profiles` first (`databricks workspace export-dir`) and import it
back after (`databricks workspace import-dir --overwrite`). Recipe: docs/RESTART.md.

Inputs (environment): MEASURE_PAIRS_MAP = a JSON {pair_n: {sttm: [..], frd: [..],
vdd: [..]}} built from the pairs folder listing (never committed: it holds document
names); CODEGEN_OAUTH_CFG = the CLI config holding profile `codegen-oaut`;
MEASURE_OUT = where the per-pair JSON (counts only) goes.

Per pair: choose the STTM (check the FRD paired is the pair's, else choose it),
arm the one-shot layout refresh (past every cache = a first read), run live,
proceed past any layout questions with no answers, read the layout stage's
tokens, then Cancel run to clear the page. Writes counts only.
Usage: python measure.py pair_1 pair_2 ...
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

U = "https://codegen-agent-4812116803419068.8.azure.databricksapps.com"
OUT = Path(os.environ.get("MEASURE_OUT", "/tmp/cgs/measure"))
OUT.mkdir(parents=True, exist_ok=True)
PAIRS = json.loads(Path(os.environ.get("MEASURE_PAIRS_MAP", "/tmp/cgs/pairs_map.json"))
                   .read_text(encoding="utf-8"))
RATE_IN, RATE_OUT = 57.143, 285.714


def token() -> str:
    out = subprocess.run(["databricks", "auth", "token", "-p", "codegen-oaut"],
                         env={**os.environ, "DATABRICKS_CONFIG_FILE":
                              os.environ.get("CODEGEN_OAUTH_CFG", "/tmp/cgs/oauth.cfg")},
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)["access_token"]


TOK = {"t": None, "at": 0.0}


def call(method: str, path: str, body=None, timeout=120):
    if time.time() - TOK["at"] > 1200:
        TOK["t"], TOK["at"] = token(), time.time()
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(U + path, data=data, method=method,
                                 headers={"Authorization": f"Bearer {TOK['t']}",
                                          "Content-Type": "application/json"})
    for _attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, json.loads(r.read() or b"null")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")
        except Exception:  # noqa: BLE001 - transient
            time.sleep(5)
    raise RuntimeError(f"{method} {path} kept failing")


def status():
    return call("GET", "/api/demo/status")[1]


def measure(pair: str) -> dict:
    docs = PAIRS[pair]
    sttm = [s for s in docs["sttm"] if "blank" not in s.lower()][0]
    rec = {"pair": pair}
    s = status()
    if s["state"] not in ("idle", "done", "failed", "needs_answers"):
        return {**rec, "skipped": f"App busy: {s['state']}"}
    call("POST", "/api/demo/cancel")
    code, _ = call("POST", "/api/demo/workbook", {"name": sttm})
    if code not in (200, 202):
        return {**rec, "skipped": f"select STTM: HTTP {code}"}
    for _ in range(120):
        s = status()
        if s["selection_job"] and s["selection_job"]["state"] in ("done", "failed"):
            break
        time.sleep(3)
    if s["selection_job"]["state"] != "done":
        return {**rec, "skipped": "STTM selection failed"}
    frd = docs["frd"][0]
    if (s["selection"] or {}).get("frd") != frd:
        code, _ = call("POST", "/api/demo/frd", {"kind": "local", "id": frd})
        s = status()
        rec["frd_chosen_manually"] = True
        if (s["selection"] or {}).get("frd") != frd:
            return {**rec, "skipped": f"FRD not selectable (HTTP {code})"}
    rec["vdd"] = bool((s["selection"] or {}).get("vdd"))
    call("POST", "/api/demo/layout-refresh", {"enabled": True})
    code, body = call("POST", "/api/demo/run-live", {"confirm": True})
    if code not in (200, 202):
        return {**rec, "skipped": f"run-live HTTP {code}: {str(body)[:120]}"}
    t0, pauses = time.time(), 0
    while time.time() - t0 < 1200:
        s = status()
        if s["state"] == "needs_layout":
            pauses += 1
            last = (s.get("stages") or [{}])[-1].get("stage")
            if last == "needs pairing" or pauses > 4:
                call("POST", "/api/demo/cancel")
                return {**rec, "skipped": f"paused at {last} ({pauses}x)"}
            call("POST", "/api/demo/layout-answers", {"answers": {}, "proceed": True})
            time.sleep(3)
            continue
        if s["state"] in ("done", "failed", "needs_answers", "idle"):
            break
        time.sleep(4)
    layout = [u for u in s.get("model_usage") or [] if u.get("stage") == "layout"]
    r = s.get("layout_report") or {}
    rec.update({
        "state": s["state"], "outcome": s.get("outcome"), "pauses": pauses,
        "wall_s": round(time.time() - t0),
        "docs": {k: {"source": (r.get(k) or {}).get("source"),
                     "calls": (r.get(k) or {}).get("provider_calls")}
                 for k in ("sttm", "frd", "vdd") if r.get(k)},
        "needs_answers": len(s.get("needs_answers") or []),
        "error_type": (s.get("error_detail") or {}).get("type"),
    })
    if layout:
        u = layout[0]
        rec.update({"calls": u["calls"], "failed": u.get("failed"), "model_s": u["seconds"],
                    "in": u["input_tokens"], "out": u["output_tokens"],
                    "cache_read": u.get("cache_read_tokens"),
                    "dbu": round((u["input_tokens"] * RATE_IN + u["output_tokens"] * RATE_OUT)
                                 / 1e6, 2)})
    call("POST", "/api/demo/cancel")
    return rec


if __name__ == "__main__":
    for pair in sys.argv[1:]:
        try:
            rec = measure(pair)
        except Exception as exc:  # noqa: BLE001
            rec = {"pair": pair, "skipped": f"{type(exc).__name__}"}
        (OUT / f"{pair}.json").write_text(json.dumps(rec, indent=1))
        print(json.dumps({k: rec.get(k) for k in ("pair", "calls", "in", "out", "dbu",
                                                  "outcome", "state", "skipped")}), flush=True)
