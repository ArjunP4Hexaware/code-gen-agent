"""The emit stages of one ``codegen generate`` run (D1 post51, 2026-10-15).

The post51 12-pair report showed DDL / IIG workbook / DML emit as PASS on pairs
whose Generate stage FAILED (pairs 03 / 04 / 07 even carried pair_02's exact
unpopulated-cell counts: a workbook the run never wrote for them). Rule since
post52:

- an emit stage is ``SKIPPED`` — never ``PASS`` — when any upstream stage of the
  run failed (a contract mismatch, a template gap, a gate verdict FAIL, an
  uncaught error); the exit code is unchanged;
- every emit artefact a FAILED feed wrote or rewrote in this run (its DDL text /
  SQL, its IIG workbook, its insert SQL / workbook) is deleted — no partial
  workbook is left for a reader to score;
- ``<output root>/CODEGEN_STAGES.json`` records the run's stage statuses and the
  artefacts it actually wrote (paths relative to the output root — feed slugs:
  an ACFC-side file, never pushed). A reader scores ONLY those files, never a
  glob of the output folder, which other pairs' runs share.

STABLE (2026-10-15) for the harness: :data:`STAGES_FILE`, :data:`EMIT_STAGES`,
:func:`read_stage_manifest`.
"""

from __future__ import annotations

import json
from pathlib import Path

STAGES_FILE = "CODEGEN_STAGES.json"
EMIT_STAGES = ("ddl_emit", "iig_emit", "dml_emit")
SKIPPED_UPSTREAM = "upstream stage generate failed"
SKIPPED_NOT_WRITTEN = "not produced by the selected output mode"

Snapshot = dict[Path, tuple[int, int]]


def emit_stage(path: Path) -> str | None:
    """Which emit stage a generated file belongs to (None: not an emit artefact
    — the notebook pipeline modules, reports, candidates, the README)."""
    name = path.name.lower()
    if path.suffix.lower() == ".xlsx":
        return "dml_emit" if "insert" in name else "iig_emit"
    if path.suffix.lower() == ".sql":
        return "dml_emit" if "insert" in name else "ddl_emit"
    if path.suffix.lower() == ".txt" and ("ddl" in name or "table_creation" in name):
        return "ddl_emit"
    return None


def snapshot(root: Path) -> Snapshot:
    """(mtime_ns, size) of every file under ``root`` (empty when absent)."""
    if not root.is_dir():
        return {}
    out: Snapshot = {}
    for path in root.rglob("*"):
        if path.is_file():
            stat = path.stat()
            out[path] = (stat.st_mtime_ns, stat.st_size)
    return out


def written_since(root: Path, before: Snapshot) -> dict[str, list[Path]]:
    """The emit artefacts under ``root`` created or rewritten since ``before``,
    by stage."""
    found: dict[str, list[Path]] = {stage: [] for stage in EMIT_STAGES}
    for path, stamp in sorted(snapshot(root).items()):
        stage = emit_stage(path)
        if stage is not None and before.get(path) != stamp:
            found[stage].append(path)
    return found


def remove_partial(root: Path, before: Snapshot) -> int:
    """Delete the emit artefacts a failed feed wrote or rewrote; the count."""
    removed = 0
    for paths in written_since(root, before).values():
        for path in paths:
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def stage_statuses(failed: bool, needs_answers: bool,
                   written: dict[str, list[Path]]) -> dict[str, dict[str, str]]:
    """``generate`` + the three emit stages, each ``{"status": ..., "reason": ...}``."""
    statuses = {"generate": {"status": "FAIL" if failed else
                             "NEEDS_ANSWERS" if needs_answers else "PASS"}}
    for stage in EMIT_STAGES:
        if failed:
            statuses[stage] = {"status": "SKIPPED", "reason": SKIPPED_UPSTREAM}
        elif written.get(stage):
            statuses[stage] = {"status": "PASS"}
        else:
            statuses[stage] = {"status": "SKIPPED", "reason": SKIPPED_NOT_WRITTEN}
    return statuses


def write_stage_manifest(out_root: Path, *, command: str, exit_code: int,
                         statuses: dict[str, dict[str, str]], feeds: list[dict]) -> Path:
    """``<out_root>/CODEGEN_STAGES.json`` — rewritten by every generate run."""
    out_root.mkdir(parents=True, exist_ok=True)
    path = out_root / STAGES_FILE
    payload = {"command": command, "exit": exit_code, "stages": statuses, "feeds": feeds}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def feed_entry(out_root: Path, n: int, of: int, status: str,
               written: dict[str, list[Path]], removed: int = 0) -> dict:
    """One feed's manifest entry (position, verdict, the artefacts it kept)."""
    return {"n": n, "of": of, "status": status, "removed": removed,
            "artefacts": {stage: [p.relative_to(out_root).as_posix() for p in paths]
                          for stage, paths in written.items()}}


def read_stage_manifest(out_root: str | Path) -> dict | None:
    """The last generate run's manifest under ``out_root`` (None when absent)."""
    path = Path(out_root) / STAGES_FILE
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["EMIT_STAGES", "SKIPPED_NOT_WRITTEN", "SKIPPED_UPSTREAM", "STAGES_FILE",
           "emit_stage", "feed_entry", "read_stage_manifest", "remove_partial", "snapshot",
           "stage_statuses", "write_stage_manifest", "written_since"]
