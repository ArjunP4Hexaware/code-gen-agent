"""The emit stages of one ``codegen generate`` run (D1 post51, 2026-10-15).

Two failure outcomes since post54 (exit code 1 for both):

- ``CRASHED`` — an exception mid-write (a template gap, an uncaught error): the
  feed's partial emit files are deleted and the emit stages are ``SKIPPED``
  (below);
- ``GATE_FAIL`` — every artefact was written, the correctness gate said no: the
  files are KEPT, moved under ``<output>/<feed>/quarantine/`` with a
  ``GATE_FAIL.md`` beside them (failed checks + flag counts per type — no names,
  no values; those are in the ACFC-side full report), the emit stages report
  ``PASS``, and the manifest records ``generate = GATE_FAIL`` with the quarantine
  path — "complete, gate failed, review only". ``tools/iig_diff.py`` can still
  score the quarantined workbook (its build stamp is 3 folders up).

A failure before anything is written (a contract mismatch, no feed matching
``--feed``) is ``FAIL``: emit stages ``SKIPPED``.

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
import re
from pathlib import Path

STAGES_FILE = "CODEGEN_STAGES.json"
EMIT_STAGES = ("ddl_emit", "iig_emit", "dml_emit")
SKIPPED_UPSTREAM = "upstream stage generate failed"
SKIPPED_NOT_WRITTEN = "not produced by the selected output mode"
QUARANTINE_DIR = "quarantine"
GATE_FAIL_FILE = "GATE_FAIL.md"
REVIEW_ONLY = "complete, gate failed, review only"
# generate outcomes, most severe first (a run's status is its worst feed's)
OUTCOMES = ("CRASHED", "FAIL", "GATE_FAIL", "NEEDS_ANSWERS", "PASS")

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
    """(mtime_ns, size) of every file under ``root`` (empty when absent),
    the ``quarantine/`` subtree excluded."""
    if not root.is_dir():
        return {}
    out: Snapshot = {}
    for path in root.rglob("*"):
        if path.is_file() and QUARANTINE_DIR not in path.relative_to(root).parts[:1]:
            stat = path.stat()
            out[path] = (stat.st_mtime_ns, stat.st_size)
    return out


def clear_quarantine(feed_dir: Path) -> None:
    """A feed's previous quarantine goes when the feed is generated again."""
    import shutil

    target = feed_dir / QUARANTINE_DIR
    if target.is_dir():
        shutil.rmtree(target)


def quarantine(feed_dir: Path, before: Snapshot) -> list[Path]:
    """Move every file the feed wrote or rewrote since ``before`` to
    ``<feed_dir>/quarantine/<same relative path>`` (bytes untouched); the new
    paths. Folders left empty by the move are removed."""
    moved: list[Path] = []
    target_root = feed_dir / QUARANTINE_DIR
    for path, stamp in sorted(snapshot(feed_dir).items()):
        if before.get(path) == stamp:
            continue
        target = target_root / path.relative_to(feed_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        path.replace(target)
        moved.append(target)
    for folder in sorted((p for p in feed_dir.rglob("*") if p.is_dir()),
                         key=lambda p: len(p.parts), reverse=True):
        if QUARANTINE_DIR not in folder.relative_to(feed_dir).parts[:1] \
                and not any(folder.iterdir()):
            folder.rmdir()
    return moved


def by_stage(paths: list[Path]) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {stage: [] for stage in EMIT_STAGES}
    for path in paths:
        stage = emit_stage(path)
        if stage is not None:
            found[stage].append(path)
    return found


_FLAG_TYPE = re.compile(r"^([a-z][a-z0-9_]{0,60})(?=[:\s]|$)")


def flag_type(flag: str) -> str:
    """A gate flag's TYPE — its leading vocabulary token (``iig_blank``,
    ``frd_unstated``, …); anything else counts as ``other``. Never its text."""
    match = _FLAG_TYPE.match(flag or "")
    return match.group(1) if match else "other"


def gate_fail_note(gate, n: int, of: int, moved: int) -> str:
    """``GATE_FAIL.md``: what failed, as counts and check names only."""
    from collections import Counter

    failed = [c.name for c in gate.checks if not c.passed and not c.not_run]
    counts = Counter(flag_type(f) for f in gate.flags)
    lines = [
        "# GATE_FAIL — complete, gate failed, review only",
        "",
        f"Feed {n} of {of}: every artefact was written; the correctness gate's verdict is "
        f"FAIL. The {moved} file(s) this run wrote are in this folder, unchanged — review "
        "only, never deploy from here.",
        "",
        "## Failed checks",
        "",
        *([f"- `{name}`" for name in failed] or ["- none (the verdict failed on flags)"]),
        "",
        "## Flags by type",
        "",
        "| Flag type | Count |",
        "| --- | --- |",
        *[f"| `{kind}` | {count} |" for kind, count in sorted(counts.items())],
        "",
        "Names and values are in the full generation report (the run's reports folder, "
        "inside ACFC only); this file carries counts and check names only.",
        "",
    ]
    return "\n".join(lines)


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


def stage_statuses(outcome: str, written: dict[str, list[Path]],
                   quarantined: list[str] | None = None) -> dict[str, dict]:
    """``generate`` + the three emit stages, each ``{"status": ..., ...}``.
    ``outcome`` is one of :data:`OUTCOMES`; the emit stages are SKIPPED only
    after CRASHED / FAIL (a GATE_FAIL run's files are complete)."""
    generate: dict = {"status": outcome}
    if outcome == "GATE_FAIL":
        generate.update(label=REVIEW_ONLY, quarantine=list(quarantined or []))
    statuses: dict[str, dict] = {"generate": generate}
    for stage in EMIT_STAGES:
        if outcome in ("CRASHED", "FAIL"):
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
               written: dict[str, list[Path]], removed: int = 0,
               quarantine_dir: Path | None = None) -> dict:
    """One feed's manifest entry (position, outcome, the artefacts it kept —
    under ``quarantine/`` for a GATE_FAIL feed)."""
    entry = {"n": n, "of": of, "status": status, "removed": removed,
             "artefacts": {stage: [p.relative_to(out_root).as_posix() for p in paths]
                           for stage, paths in written.items()}}
    if quarantine_dir is not None:
        entry["quarantine"] = quarantine_dir.relative_to(out_root).as_posix()
        entry["label"] = REVIEW_ONLY
    return entry


def read_stage_manifest(out_root: str | Path) -> dict | None:
    """The last generate run's manifest under ``out_root`` (None when absent)."""
    path = Path(out_root) / STAGES_FILE
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


__all__ = ["EMIT_STAGES", "GATE_FAIL_FILE", "OUTCOMES", "QUARANTINE_DIR", "REVIEW_ONLY",
           "SKIPPED_NOT_WRITTEN", "SKIPPED_UPSTREAM", "STAGES_FILE", "by_stage",
           "clear_quarantine", "emit_stage", "feed_entry", "flag_type", "gate_fail_note",
           "quarantine", "read_stage_manifest", "remove_partial", "snapshot", "stage_statuses",
           "write_stage_manifest", "written_since"]
