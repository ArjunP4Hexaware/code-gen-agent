"""Layer-2 failures on the log — D1-only diagnostics (2026-10-14).

The layout recognizer's RAW mechanism (post43, ``layout.resolve.
_log_raw_responses``) for Layer 2: every failed attempt of a live provider
(:class:`codegen.reasoning.providers.ask.AttemptFailure`) prints

    LAYER2 FAILED  <feed> request <n> attempt <k>/<m>: <reason>
    RAW (D1 only)  layer2 <feed> request <n> attempt <k>, first 500 chars: '…'
    NOTE           layer2 <feed> request <n>: max_tokens <a> -> <b> (…)

on stderr and writes ``<state>/rejections/layer2_<feed>.raw.json`` in the
state role. The reason names no response text; the RAW line and the file do
(a model can quote the contract it was shown) — they stay on the workspace
that ran them: never a report, ``candidates.json`` or a tracked file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from codegen.layout.model import RAW_LOG_CHARS


def failure_lines(feed: str, failures) -> list[str]:
    lines: list[str] = []
    for f in failures:
        outcome = "answered on retry" if f.recovered else "failed"
        lines.append(f"{'LAYER2 FAILED':<15}{feed} request {f.request} attempt "
                     f"{f.attempt}/{f.attempts} ({outcome}): {f.reason}")
        if f.raw:
            lines.append(f"{'RAW (D1 only)':<15}layer2 {feed} request {f.request} attempt "
                         f"{f.attempt}, first {RAW_LOG_CHARS} chars: {f.raw!r}")
        if f.raised_to is not None:
            lines.append(f"{'NOTE':<15}layer2 {feed} request {f.request}: max_tokens "
                         f"{f.max_tokens} -> {f.raised_to} for the retry (the response "
                         "ended inside the JSON object)")
    return lines


def log_layer2_failures(provider, feed: str, config, base_dir: Path,
                        stream=None) -> Path | None:
    """Print every failed attempt of ``provider`` (stderr) and store them in
    the state role. Nothing to say (a mock, no failure) = no output."""
    failures = list(getattr(provider, "failures", None) or [])
    if not failures:
        return None
    stream = stream if stream is not None else sys.stderr
    for line in failure_lines(feed, failures):
        print(line, file=stream)
    payload = {"feed": feed, "provider": getattr(provider, "name", None),
               "chars": RAW_LOG_CHARS, "failures": [f.as_dict() for f in failures]}
    data = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    try:
        from codegen.storage import open_storage

        state = open_storage(config, Path(base_dir)).state
        return state.write_bytes(f"rejections/layer2_{feed}.raw.json", data)
    except Exception as exc:  # noqa: BLE001 — diagnostics never fail a run
        print(f"{'WARN':<15}layer2 failures not stored: {exc}", file=stream)
        return None


__all__ = ["failure_lines", "log_layer2_failures"]
