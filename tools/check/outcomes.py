"""The 12-pair check: per-pair outcome, old vs new (counts only, pair numbers only).

argv: <out_old> <out_new>   (the harness --out dirs; tools/check/pair_check.sh)"""
import collections
import json
import sys
from pathlib import Path


def outcomes(out: Path) -> dict[str, str]:
    reports = [p for p in out.glob("run_*/run_*Z_*.json") if not p.name.endswith(".stub.json")]
    if not reports:
        sys.exit(f"no harness report under {out}")
    pairs = json.loads(reports[0].read_text(encoding="utf-8"))["pairs"]
    if isinstance(pairs, dict):
        pairs = [dict(pair=k, **v) if isinstance(v, dict) else {"pair": k, "outcome": v}
                 for k, v in pairs.items()]
    return {str(p.get("pair") or p.get("name") or p.get("id")):
            p.get("outcome") or p.get("status") for p in pairs}


old, new = outcomes(Path(sys.argv[1])), outcomes(Path(sys.argv[2]))
print("same outcomes:", old == new)
print("old:", dict(collections.Counter(old.values())))
print("new:", dict(collections.Counter(new.values())))
for pair in sorted(old):
    if old[pair] != new.get(pair):
        print(f"  changed: {pair} {old[pair]} -> {new.get(pair)}")
