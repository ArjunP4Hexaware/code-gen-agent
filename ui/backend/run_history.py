"""post67: the record behind the live-run confirm dialog.

The last ``demo.run_history_size`` live runs per conventions profile — calls,
live-call seconds (the MODEL USAGE line's), wall-clock and measured tokens /
cost — kept in the state role as ``live_run_history.json``. The dialog shows
ranges FROM this record, never a constant: "no history yet" when it is
empty, no dollar figure when no run reported tokens (or the price table has
no row for the model). Cost = tokens x ``reasoning.prices``; never calls x
a constant.

Wall-clock runs from the run's start to its end, minus the time it waited
for the person (a pairing / layout dialog) — what a user waits for, which is
the dialog's headline. Only completed live runs (done / needs_answers) are
recorded: a failed run's time says nothing about the next one.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from codegen.reasoning.usage import LIVE_PROVIDERS, TOKEN_FIELDS
from ui.backend.service import STATE_DIR

HISTORY_FILE = "live_run_history.json"
HISTORY_PATH = STATE_DIR / HISTORY_FILE
# At least this many runs before the range drops the single fastest and
# slowest one ("typically"); fewer runs show their full spread.
TRIM_FROM = 5


def is_live(usage: dict) -> bool:
    return any(p in LIVE_PROVIDERS for p in str(usage.get("provider") or "").split("+"))


def run_entry(*, label: str | None, model_usage: list[dict], wall_seconds: float,
              prices=None) -> dict | None:
    """One run's record from its ``model_usage`` (StageUsage.as_dict per stage);
    None for a run no live provider answered (mock, replay)."""
    live = [u for u in model_usage if is_live(u)]
    if not live:
        return None
    calls = sum(int(u.get("calls") or 0) for u in live)
    tokens = {name: sum(int(u.get(name) or 0) for u in live) for name in TOKEN_FIELDS}
    # Tokens exist when the calls reported them; a run with no call costs nothing.
    measured = calls == 0 or tokens["input_tokens"] + tokens["output_tokens"] > 0
    cost = None
    if calls == 0:
        cost = 0.0
    elif measured and prices is not None:
        parts = [prices.cost_usd(u.get("model"), **{n: int(u.get(n) or 0) for n in TOKEN_FIELDS})
                 for u in live if int(u.get("calls") or 0)]
        cost = None if any(p is None for p in parts) else round(sum(parts), 4)
    return {
        "label": label,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "calls": calls,
        "model_seconds": round(sum(float(u.get("seconds") or 0.0) for u in live), 1),
        "wall_seconds": round(wall_seconds, 1),
        **tokens,
        "tokens_measured": measured,
        "cost_usd": cost,
    }


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
    """What the dialog shows for ``profile``: ranges over its recorded runs."""
    costed = [e for e in entries if e.get("cost_usd") is not None]
    return {
        "profile": profile,
        "runs": len(entries),
        "wall_seconds": typical_range([e["wall_seconds"] for e in entries]),
        "model_seconds": typical_range([e["model_seconds"] for e in entries]),
        "calls": typical_range([e["calls"] for e in entries]),
        # dollars only from runs whose tokens were measured and priced
        "cost_usd": typical_range([e["cost_usd"] for e in costed]),
        "cost_runs": len(costed),
        "prices_as_of": prices.as_of if prices is not None and costed else None,
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
        with self._lock:
            return list(self._load()["profiles"].get(profile) or [])

    def view(self, profile: str) -> dict:
        return summary(self.entries(profile), profile=profile,
                       prices=self._config().reasoning.prices)

    def record(self, profile: str, entry: dict) -> None:
        from ui.backend import stores as ui_stores

        config = self._config()
        keep = config.demo.run_history_size
        with self._lock:
            data = self._load()
            runs = [*(data["profiles"].get(profile) or []), entry][-keep:]
            data["profiles"][profile] = runs
            text = json.dumps(data, indent=2, sort_keys=True) + "\n"
        path = Path(ui_stores.state_local_path(config, HISTORY_FILE, HISTORY_PATH))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        ui_stores.push_state(config, HISTORY_FILE)


__all__ = ["HISTORY_FILE", "LiveRunHistory", "run_entry", "summary", "typical_range"]
