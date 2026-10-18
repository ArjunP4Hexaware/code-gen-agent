"""post67: the record behind the live-run confirm dialog.

The last ``demo.run_history_size`` live runs per (conventions profile,
generate outcome) — calls, live-call seconds (the MODEL USAGE line's),
wall-clock and measured tokens / cost — kept in the state role as
``live_run_history.json``. The dialog shows ranges FROM this record, never a
constant. Its range comes from COMPLETED runs only (PASS /
PASS_WITH_OPEN_INPUTS), "no history yet for completed runs" under
``MIN_COMPLETED`` of them; runs that STOPPED (NEEDS_ANSWERS / GATE_FAIL) are
kept and shown as a second line when they exist. CRASHED and FAIL runs (and
runs that ended with no outcome) are not recorded. No dollar figure when no
run reported tokens (or the price table has no row for the model). Cost =
tokens x ``reasoning.prices`` — the workspace's FM API rate when it has the
model, else the Anthropic list price; never calls x a constant.

Wall-clock runs from the run's start to its end, minus the time it waited
for the person (a pairing / layout dialog) — what a user waits for, which is
the dialog's headline.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from codegen.config import PRICE_BASIS_LIST, PRICE_BASIS_WORKSPACE
from codegen.reasoning.usage import LIVE_PROVIDERS, TOKEN_FIELDS
from ui.backend.service import STATE_DIR

HISTORY_FILE = "live_run_history.json"
HISTORY_PATH = STATE_DIR / HISTORY_FILE
# At least this many runs before the range drops the single fastest and
# slowest one ("typically"); fewer runs show their full spread.
TRIM_FROM = 5
# Generate outcomes (codegen.run_stages.OUTCOMES) the record keeps: the
# dialog's range comes from the completed ones, the stopped ones are a second line.
COMPLETED_OUTCOMES = ("PASS", "PASS_WITH_OPEN_INPUTS")
STOPPED_OUTCOMES = ("NEEDS_ANSWERS", "GATE_FAIL")
# Fewer completed runs than this = "no history yet for completed runs".
MIN_COMPLETED = 3


def is_live(usage: dict) -> bool:
    return any(p in LIVE_PROVIDERS for p in str(usage.get("provider") or "").split("+"))


def _stages(live: list[dict]) -> list[dict]:
    """What pricing needs per live stage that sent calls: who answered, which
    model, its tokens."""
    return [{"provider": u.get("provider"), "model": u.get("model"),
             "calls": int(u.get("calls") or 0),
             **{n: int(u.get(n) or 0) for n in TOKEN_FIELDS}}
            for u in live if int(u.get("calls") or 0)]


def entry_cost(entry: dict, prices) -> dict | None:
    """A recorded run priced at ``prices`` (the CURRENT table — a rate filled
    in later applies to the runs already recorded): {cost_usd, basis, sources,
    fmapi}; None when its tokens were not measured or a model has no row.
    basis = workspace only when every call was priced at the workspace's rate;
    a run with no call costs 0 at any basis (None)."""
    if not entry.get("calls"):
        return {"cost_usd": 0.0, "basis": None, "sources": [], "fmapi": False}
    stages = entry.get("stages")
    if not entry.get("tokens_measured") or not stages or prices is None:
        return None
    total, bases, sources = 0.0, set(), []
    for stage in stages:
        found = prices.rate(stage.get("provider"), stage.get("model"))
        if found is None:
            return None
        price, basis = found
        total += price.cost_usd(**{n: int(stage.get(n) or 0) for n in TOKEN_FIELDS})
        bases.add(basis)
        if price.source not in sources:
            sources.append(price.source)
    return {"cost_usd": round(total, 4),
            "basis": PRICE_BASIS_WORKSPACE if bases == {PRICE_BASIS_WORKSPACE}
            else PRICE_BASIS_LIST,
            "sources": sources,
            "fmapi": any(s.get("provider") == "databricks_fmapi" for s in stages)}


def run_entry(*, label: str | None, model_usage: list[dict], wall_seconds: float,
              outcome: str | None, prices=None) -> dict | None:
    """One run's record from its ``model_usage`` (StageUsage.as_dict per stage);
    None for a run no live provider answered (mock, replay) and for an outcome
    the record does not keep (CRASHED, FAIL, none)."""
    live = [u for u in model_usage if is_live(u)]
    if not live or outcome not in (*COMPLETED_OUTCOMES, *STOPPED_OUTCOMES):
        return None
    calls = sum(int(u.get("calls") or 0) for u in live)
    tokens = {name: sum(int(u.get(name) or 0) for u in live) for name in TOKEN_FIELDS}
    entry = {
        "label": label,
        "outcome": outcome,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "calls": calls,
        "model_seconds": round(sum(float(u.get("seconds") or 0.0) for u in live), 1),
        "wall_seconds": round(wall_seconds, 1),
        **tokens,
        # tokens exist when the calls reported them
        "tokens_measured": calls == 0 or tokens["input_tokens"] + tokens["output_tokens"] > 0,
        "stages": _stages(live),
    }
    cost = entry_cost(entry, prices)
    entry["cost_usd"] = cost["cost_usd"] if cost else None       # as priced when recorded
    entry["cost_basis"] = cost["basis"] if cost else None
    return entry


def typical_range(values: list[float]) -> dict | None:
    """{low, high} over ``values``; from TRIM_FROM values on, the single lowest
    and highest are left out."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) >= TRIM_FROM:
        ordered = ordered[1:-1]
    return {"low": ordered[0], "high": ordered[-1]}


def summary(entries: list[dict], *, profile: str, prices=None) -> dict:
    """What the dialog shows for ``profile``: ranges over its COMPLETED runs
    (none under MIN_COMPLETED), and ``stopped`` — the NEEDS_ANSWERS /
    GATE_FAIL runs' wall-clock — when there are any.
    Dollars only from runs whose tokens were measured and priced, at ONE basis:
    the workspace's rate when any run has it, else the Anthropic list price."""
    stopped = [e for e in entries if e.get("outcome") in STOPPED_OUTCOMES]
    completed = [e for e in entries if e.get("outcome") in COMPLETED_OUTCOMES]
    view = {
        "profile": profile,
        "runs": len(completed),
        "min_runs": MIN_COMPLETED,
        "stopped": ({"runs": len(stopped),
                     "wall_seconds": typical_range([e["wall_seconds"] for e in stopped])}
                    if stopped else None),
    }
    if len(completed) < MIN_COMPLETED:
        return {**view, "wall_seconds": None, "model_seconds": None, "calls": None,
                "cost_usd": None, "cost_runs": 0, "cost_basis": None, "price_source": None,
                "billed_in_dbus": False}
    entries = completed
    priced = [c for c in (entry_cost(e, prices) for e in entries) if c is not None]
    basis = (PRICE_BASIS_WORKSPACE
             if any(c["basis"] == PRICE_BASIS_WORKSPACE for c in priced)
             else PRICE_BASIS_LIST)
    used = [c for c in priced if c["basis"] in (basis, None)]
    sources = list(dict.fromkeys(s for c in used for s in c["sources"]))
    return {
        **view,
        "wall_seconds": typical_range([e["wall_seconds"] for e in entries]),
        "model_seconds": typical_range([e["model_seconds"] for e in entries]),
        "calls": typical_range([e["calls"] for e in entries]),
        "cost_usd": typical_range([c["cost_usd"] for c in used]),
        "cost_runs": len(used),
        "cost_basis": basis if used else None,
        # each price row's own source, e.g. "anthropic list price, 2026-10-06"
        "price_source": "; ".join(sources) or None,
        # list-priced FM API calls: the workspace is billed in DBUs, not these dollars
        "billed_in_dbus": bool(used) and basis == PRICE_BASIS_LIST
        and any(c["fmapi"] for c in used),
    }


class LiveRunHistory:
    """The record, read from the state role once and kept in memory (the
    status endpoint is polled); each recorded run rewrites the file whole."""

    def __init__(self, config_fn) -> None:
        self._config = config_fn
        self._lock = threading.Lock()
        self._data: dict | None = None

    def _load(self) -> dict:
        from ui.backend import stores as ui_stores

        if self._data is None:
            data: dict = {}
            try:
                path = ui_stores.state_file(self._config(), HISTORY_FILE, HISTORY_PATH)
                if path.exists():
                    data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = {}                       # an unreadable record = no history
            profiles = data.get("profiles") if isinstance(data, dict) else None
            self._data = {"profiles": profiles if isinstance(profiles, dict) else {}}
        return self._data

    def entries(self, profile: str) -> list[dict]:
        """Every kept run for ``profile``, all outcomes, oldest first."""
        with self._lock:
            by_outcome = self._load()["profiles"].get(profile)
            if not isinstance(by_outcome, dict):       # an older record: not keyed by outcome
                return []
            runs = [e for kept in by_outcome.values() if isinstance(kept, list) for e in kept]
        return sorted(runs, key=lambda e: str(e.get("at") or ""))

    def view(self, profile: str) -> dict:
        return summary(self.entries(profile), profile=profile,
                       prices=self._config().reasoning.prices)

    def record(self, profile: str, entry: dict) -> None:
        """Keep ``entry`` under (profile, its outcome): the last N per key."""
        from ui.backend import stores as ui_stores

        config = self._config()
        keep = config.demo.run_history_size
        with self._lock:
            data = self._load()
            by_outcome = data["profiles"].get(profile)
            if not isinstance(by_outcome, dict):
                by_outcome = data["profiles"][profile] = {}
            outcome = entry["outcome"]
            by_outcome[outcome] = [*(by_outcome.get(outcome) or []), entry][-keep:]
            text = json.dumps(data, indent=2, sort_keys=True) + "\n"
        path = Path(ui_stores.state_local_path(config, HISTORY_FILE, HISTORY_PATH))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        ui_stores.push_state(config, HISTORY_FILE)


__all__ = ["COMPLETED_OUTCOMES", "HISTORY_FILE", "MIN_COMPLETED", "STOPPED_OUTCOMES",
           "LiveRunHistory", "entry_cost", "run_entry", "summary", "typical_range"]
