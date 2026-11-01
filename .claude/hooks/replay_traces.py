#!/usr/bin/env python3
"""Replay recorded hook traces through a detector variant and list the firings it
would have produced: the hook's oracle, the counterpart of the skill's replay evals.

A variant is
- the current detector (default: spiral_detector.py next to this file),
- another module (--variant PATH: a copy of spiral_detector.py with changed logic;
  it must keep ``step`` and ``_fresh_state``), and/or
- a flag set (--set NAME=VALUE, repeatable: override a module constant, such as
  SIGNAL_B_EDITS_WHILE_FAILING=5; values parse as JSON, else as text; an unknown name
  is an error).
--compare PATH (with --compare-set) replays a second variant and prints the firings
only one of the two produced, so the current logic and a candidate can be compared
on real history.

Replay follows the live hook exactly: state is per repo, and a new session_id starts
a fresh state. It reads traces only and writes nothing.

Usage:
  python replay_traces.py [--traces DIR] [--repo NAME ...] [--since YYYY-MM-DD]
                          [--variant PATH] [--set NAME=VALUE ...]
                          [--compare PATH] [--compare-set NAME=VALUE ...] [--json]
"""

from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
CURRENT = HERE / "spiral_detector.py"
_counter = itertools.count()


def load_detector(path: Path = CURRENT, overrides: dict[str, object] | None = None) -> ModuleType:
    """Load a detector module from ``path`` (a fresh copy each call) and apply overrides."""
    name = f"spiral_detector_variant_{next(_counter)}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"replay_traces: cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for key, value in (overrides or {}).items():
        if not hasattr(module, key):
            raise SystemExit(f"replay_traces: {path.name} has no setting {key!r}")
        setattr(module, key, value)
    for needed in ("step", "_fresh_state"):
        if not hasattr(module, needed):
            raise SystemExit(f"replay_traces: {path.name} lacks {needed}()")
    return module


def parse_sets(items: list[str]) -> dict[str, object]:
    out: dict[str, object] = {}
    for item in items:
        key, sep, raw = item.partition("=")
        if not sep or not key:
            raise SystemExit(f"replay_traces: --set wants NAME=VALUE, got {item!r}")
        try:
            out[key] = json.loads(raw)
        except ValueError:
            out[key] = raw
    return out


def load_traces(
    trace_dir: Path, repos: list[str] | None = None, since: str | None = None
) -> dict[str, list[dict]]:
    """{repo: records in file order} from traces/<repo>.jsonl."""
    traces: dict[str, list[dict]] = {}
    for path in sorted(trace_dir.glob("*.jsonl")):
        repo = path.stem
        if repos and repo not in repos:
            continue
        recs = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if since and rec.get("ts", "") < since:
                continue
            recs.append(rec)
        traces[repo] = recs
    return traces


def replay(detector: ModuleType, traces: dict[str, list[dict]]) -> list[dict]:
    """The firings ``detector`` produces over ``traces``, shaped like fires.jsonl lines."""
    firings: list[dict] = []
    for repo, recs in traces.items():
        state = None
        for rec in recs:
            session = str(rec.get("session_id") or "")
            if state is None or state.get("session_id") != session:
                state = detector._fresh_state(session)
            for signal, _, fields in detector.step(state, rec):
                firings.append({"ts": rec.get("ts", ""), "repo": repo, "signal": signal,
                                **fields})
    return sorted(firings, key=lambda f: (f["ts"], f["repo"], f["signal"]))


def _ident(firing: dict) -> tuple:
    return (firing["ts"], firing["repo"], firing["signal"],
            firing.get("command") or firing.get("file"))


def compare(base: list[dict], candidate: list[dict]) -> tuple[list[dict], list[dict]]:
    """(firings only in base, firings only in candidate)."""
    a, b = {_ident(f) for f in base}, {_ident(f) for f in candidate}
    return ([f for f in base if _ident(f) not in b], [f for f in candidate if _ident(f) not in a])


def _line(f: dict) -> str:
    where = f.get("command") or f.get("file")
    return (f"{f['ts']}  {f['repo']}  ({f['signal']})  {where}  "
            f"sig={f.get('signature', '')} basis={f.get('signature_basis', '')}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--traces", type=Path, default=None,
                        help="trace folder (default: <spiral-breaker home>/traces)")
    parser.add_argument("--repo", action="append", default=None)
    parser.add_argument("--since", default=None, help="YYYY-MM-DD (UTC)")
    parser.add_argument("--variant", type=Path, default=CURRENT)
    parser.add_argument("--set", dest="sets", action="append", default=[])
    parser.add_argument("--compare", type=Path, default=None)
    parser.add_argument("--compare-set", dest="compare_sets", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    base = load_detector(args.variant, parse_sets(args.sets))
    trace_dir = args.traces or base.default_home() / base.TRACE_DIR
    traces = load_traces(trace_dir, args.repo, args.since)
    firings = replay(base, traces)

    if args.compare is None and not args.compare_sets:
        if args.json:
            print(json.dumps(firings, indent=2, sort_keys=True))
        else:
            events = sum(len(r) for r in traces.values())
            print(f"{events} traced event(s) in {len(traces)} repo(s); "
                  f"{len(firings)} firing(s)")
            for f in firings:
                print(_line(f))
        return 0

    candidate = load_detector(args.compare or args.variant, parse_sets(args.compare_sets))
    only_base, only_cand = compare(firings, replay(candidate, traces))
    if args.json:
        print(json.dumps({"only_base": only_base, "only_candidate": only_cand},
                         indent=2, sort_keys=True))
    else:
        print(f"base: {len(firings)} firing(s); only in base: {len(only_base)}; "
              f"only in candidate: {len(only_cand)}")
        for f in only_base:
            print("- " + _line(f))
        for f in only_cand:
            print("+ " + _line(f))
    return 0


if __name__ == "__main__":
    sys.exit(main())
