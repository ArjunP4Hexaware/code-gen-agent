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

post58: the manifest's ``questions`` lists each open line with ``blocking``. A
QUESTION / UNRESOLVED line is blocking: true (the App's "Answers needed" list and
its "required (blocking)" environment values); an INPUT_NEEDED line is blocking:
false (the App's "not blocking" banner). ``NEEDS_ANSWERS`` (exit 3) = at least
one blocking line is open, whether or not a workbook was written — each feed
entry says ``written: true|false`` so the App can still show the workbook.
``PASS_WITH_OPEN_INPUTS`` (exit 0) = the workbook written and every open line
non-blocking.

STABLE (2026-10-15) for the harness: :data:`STAGES_FILE`, :data:`EMIT_STAGES`,
:data:`OUTCOMES`, :func:`read_stage_manifest`, :func:`pair_outcome` (post58).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

STAGES_FILE = "CODEGEN_STAGES.json"
# post68: notebook_emit = the notebook output (.ipynb, pipeline/*.py, job/*)
EMIT_STAGES = ("ddl_emit", "iig_emit", "dml_emit", "notebook_emit")
SKIPPED_UPSTREAM = "upstream stage generate failed"
SKIPPED_NOT_WRITTEN = "not produced by the selected output mode"
QUARANTINE_DIR = "quarantine"
GATE_FAIL_FILE = "GATE_FAIL.md"
REVIEW_ONLY = "complete, gate failed, review only"
# generate outcomes, most severe first (a run's status is its worst feed's)
OUTCOMES = ("CRASHED", "FAIL", "GATE_FAIL", "NEEDS_ANSWERS", "PASS_WITH_OPEN_INPUTS", "PASS")
# post58: the console labels of an open line, and whether each blocks
OPEN_LINES = {"QUESTION": True, "UNRESOLVED": True, "INPUT_NEEDED": False}

Snapshot = dict[Path, tuple[int, int]]


def emit_stage(path: Path) -> str | None:
    """Which emit stage a generated file belongs to (None: not an emit artefact
    — reports, candidates, the README, the generated tests). post68: the
    notebook output is ``notebook_emit``."""
    if is_notebook_file(path):
        return "notebook_emit"
    name = path.name.lower()
    if path.suffix.lower() == ".xlsx":
        return "dml_emit" if "insert" in name else "iig_emit"
    if path.suffix.lower() == ".sql":
        return "dml_emit" if "insert" in name else "ddl_emit"
    if path.suffix.lower() == ".txt" and ("ddl" in name or "table_creation" in name):
        return "ddl_emit"
    return None


def is_notebook_file(path: Path) -> bool:
    """A file of the notebook output (the assembled ``.ipynb``, the
    ``pipeline/*.py`` modules, the ``job/*`` files)."""
    return path.suffix.lower() == ".ipynb" or path.parent.name in ("pipeline", "job")


def remove_notebook(root: Path, before: Snapshot, *, emit_too: bool) -> int:
    """post68: withhold a feed's notebook output — delete the notebook files it
    wrote or rewrote since ``before`` (and, ``emit_too``, its emit artefacts:
    a notebook-only run whose notebook is withheld keeps nothing deployable);
    the count."""
    removed = 0
    for path, stamp in sorted(snapshot(root).items()):
        if before.get(path) == stamp:
            continue
        if emit_stage(path) == "notebook_emit" or (emit_too and emit_stage(path) is not None):
            path.unlink(missing_ok=True)
            removed += 1
    for folder in sorted((p for p in root.rglob("*") if p.is_dir()),
                         key=lambda p: len(p.parts), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()                         # folders the removal left empty
    return removed


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


def flag_counts(flags) -> dict[str, int]:
    """Gate flags counted per :func:`flag_type`."""
    from collections import Counter

    return dict(Counter(flag_type(f) for f in flags))


def gate_fail_note(gate, n: int, of: int, moved: int) -> str:
    """``GATE_FAIL.md``: what failed, as counts and check names only."""
    failing = [c for c in gate.checks if not c.passed and not c.not_run]
    failed = [c.name for c in failing]
    counts = flag_counts(gate.flags)
    violations = [f"| `{c.name}` | `{kind}` | {count} |" for c in failing
                  for kind, count in sorted(c.violations.items())]
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
        *(["## Failed-check findings by rule", "", "| Check | Rule | Count |",
           "| --- | --- | --- |", *violations, ""] if violations else []),
        "## Flags by type",
        "",
        "| Flag type | Count |",
        "| --- | --- |",
        *[f"| `{kind}` | {count} |" for kind, count in sorted(counts.items())],
        "",
        "Names and values are in the full generation report (the run's reports folder, "
        "inside ACFC only; its Gate section lists the flags grouped by type); this file "
        "carries counts and check names only.",
        "",
        "## Score against the golden (D1 only)",
        "",
        "Before deciding whether the gate or the golden is wrong, diff this folder's IIG "
        "workbook against the pair's golden — per-sheet cell counts on the console, "
        "a scrubbed copy safe to bring home:",
        "",
        "```",
        "python tools/iig_diff.py --golden <the pair's golden IIG .xlsx> "
        "--agent <this folder>/*_IIG.xlsx --out <scratch dir> "
        "--export-scrubbed <scratch dir>/scrubbed",
        "```",
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
    """``generate`` + the emit stages, each ``{"status": ..., ...}``.
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


def open_item(line: str, key: str, *, feed: str | None = None) -> dict:
    """One open console line for the manifest's ``questions`` (post58):
    ``{line, key, scope, blocking}`` — ``scope`` ``feed`` (with the feed id, used
    only to decide the outcome and dropped from the manifest) or ``run``."""
    return {"line": line, "key": key, "scope": "run" if feed is None else "feed",
            "blocking": OPEN_LINES[line], **({"feed": feed} if feed is not None else {})}


def generate_outcome(*, crashed: bool, hard_failed: bool, gate_failed: bool,
                     open_items: list[dict]) -> str:
    """The run's outcome (:data:`OUTCOMES`): NEEDS_ANSWERS when ANY blocking
    line is open, whether or not a workbook was written (a workbook with an
    empty storage account is not deployable); PASS_WITH_OPEN_INPUTS when every
    open line is non-blocking."""
    if crashed:
        return "CRASHED"
    if hard_failed:
        return "FAIL"
    if gate_failed:
        return "GATE_FAIL"
    if any(i["blocking"] for i in open_items):
        return "NEEDS_ANSWERS"
    return "PASS_WITH_OPEN_INPUTS" if open_items else "PASS"


def open_counts(items: list[dict]) -> dict[str, int]:
    """``{"blocking": n, "non_blocking": n}`` over open items."""
    blocking = sum(1 for i in items if i.get("blocking"))
    return {"blocking": blocking, "non_blocking": len(items) - blocking}


def write_stage_manifest(out_root: Path, *, command: str, exit_code: int,
                         statuses: dict[str, dict[str, str]], feeds: list[dict],
                         questions: list[dict] | None = None) -> Path:
    """``<out_root>/CODEGEN_STAGES.json`` — rewritten by every generate run.
    post58: ``questions`` = every open line, ``{line, key, scope, blocking}``."""
    out_root.mkdir(parents=True, exist_ok=True)
    path = out_root / STAGES_FILE
    payload = {"command": command, "exit": exit_code, "stages": statuses, "feeds": feeds,
               "questions": [{k: v for k, v in item.items() if k != "feed"}
                             for item in questions or []]}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def feed_entry(out_root: Path, n: int, of: int, status: str,
               written: dict[str, list[Path]], removed: int = 0,
               quarantine_dir: Path | None = None, iig_cells: dict | None = None,
               withheld: int = 0, nothing_written: bool = False) -> dict:
    """One feed's manifest entry (position, outcome, the artefacts it kept —
    under ``quarantine/`` for a GATE_FAIL feed; post56: ``iig_cells``, the
    feed's IIG cell counts per sheet — open_for_bsa / empty_other /
    template_blanks — from codegen.iig_review.iig_cell_counts)."""
    entry = {"n": n, "of": of, "status": status, "removed": removed,
             # post58: the feed's files were written (a GATE_FAIL feed's under
             # quarantine/) — the App shows them on a NEEDS_ANSWERS run too
             "written": status != "CRASHED" and not nothing_written,
             "artefacts": {stage: [p.relative_to(out_root).as_posix() for p in paths]
                           for stage, paths in written.items()}}
    if withheld:
        # post68: the notebook files a blocking open line withheld
        entry["notebook_withheld"] = withheld
    if quarantine_dir is not None:
        entry["quarantine"] = quarantine_dir.relative_to(out_root).as_posix()
        entry["label"] = REVIEW_ONLY
    if iig_cells:
        entry["iig_cells"] = iig_cells
    return entry


def iig_unpopulated(out_root: str | Path) -> list[dict]:
    """STABLE (the harness reads it in place of its own workbook scan, post56):
    per feed of the last generate run, ``{"n", "of", "status", "iig_cells"}``
    from CODEGEN_STAGES.json — counts only, never names; [] without a manifest."""
    manifest = read_stage_manifest(out_root) or {}
    return [{"n": f.get("n"), "of": f.get("of"), "status": f.get("status"),
             "iig_cells": f.get("iig_cells") or {}} for f in manifest.get("feeds") or []]


def read_stage_manifest(out_root: str | Path) -> dict | None:
    """The last generate run's manifest under ``out_root`` (None when absent)."""
    path = Path(out_root) / STAGES_FILE
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# a codegen step's exit code read alone (no manifest): 0 / 1 / 3
_EXIT_OUTCOME = {0: "PASS", 1: "FAIL", 3: "NEEDS_ANSWERS"}


def pair_outcome(steps: dict[str, int], out_root: str | Path | None = None) -> str:
    """STABLE (post58, the harness summary): one pair's outcome, one of
    :data:`OUTCOMES` — the worst of its codegen steps. ``steps`` maps each step
    the pair ran (``layout``, ``extract-sttm``, ``generate``, …) to its exit
    code. The ``generate`` step is read from ``<out_root>/CODEGEN_STAGES.json``
    when that manifest is this run's (its ``exit`` equals the step's code), so a
    run whose open lines are all non-blocking reads PASS_WITH_OPEN_INPUTS;
    any other step (or generate without a manifest) reads by its exit code
    (0 PASS, 3 NEEDS_ANSWERS, anything else FAIL). A pair that ran nothing is
    FAIL."""
    if not steps:
        return "FAIL"
    found: list[str] = []
    for step, code in steps.items():
        outcome = _EXIT_OUTCOME.get(code, "FAIL")
        if step == "generate" and out_root is not None:
            manifest = read_stage_manifest(out_root) or {}
            status = ((manifest.get("stages") or {}).get("generate") or {}).get("status")
            if manifest.get("exit") == code and status in OUTCOMES:
                outcome = status
        found.append(outcome)
    return min(found, key=OUTCOMES.index)


__all__ = ["EMIT_STAGES", "GATE_FAIL_FILE", "OPEN_LINES", "OUTCOMES", "QUARANTINE_DIR",
           "REVIEW_ONLY", "SKIPPED_NOT_WRITTEN", "SKIPPED_UPSTREAM", "STAGES_FILE", "by_stage",
           "clear_quarantine", "emit_stage", "feed_entry", "flag_counts", "flag_type",
           "gate_fail_note", "generate_outcome", "iig_unpopulated", "open_counts", "open_item",
           "pair_outcome", "quarantine", "read_stage_manifest", "remove_partial", "snapshot",
           "stage_statuses", "write_stage_manifest", "written_since"]
