"""Layer 2 as its own stage, after emit (post76).

D1 post73 pair_11 (556 s, five feeds): Layer 2 asked one request per unmapped
rule per feed, inside each feed's generate, before its files were written.
Now:

- ONE request per feed (``reasoning.engine.reason_over_packs`` →
  ``complete_batch``), every answer grounding-checked against its own rule;
- the stage runs AFTER the run's outcome: ``generate`` writes every feed's
  files, the gate verdict, the report and ``CODEGEN_STAGES.json`` without a
  model call;
- candidates never affect the verdict: ``gate.compute_verdict`` takes none (an
  unmapped rule is the same gate flag in every mode); what Layer 2 finds is an
  INFORMATIONAL flag (:func:`info_flags`: ``unimplemented_rule_has_candidate``,
  ``layer2_candidate_not_grounded``, ``layer2_provider_failed``) in the report
  and the manifest, never pass/fail;
- the v2 notebook's executable cells are the same in every mode: only its
  TRAILING review ``%md`` differs, (re-)emitted here
  (``emit.notebook_v2.with_review``);
- ``--layer2 now | defer | skip`` (``reasoning.layer2_cli`` default ``now``,
  the App's ``reasoning.layer2_app`` default ``defer``):

  * ``now``   — the stage asks the model after the outcome is written and adds
    its candidates to ``candidates.json``, the report and the notebook's
    trailing review cell (before the command returns);
  * ``defer`` — nothing asked; ``<feed>/candidates/layer2_pending.json`` keeps
    the feed's rule packs (contract text only), the report and the App say
    "review candidates: pending"; ``codegen layer2 --output DIR`` (or the
    App's review panel) asks later and re-emits the notebook then;
  * ``skip``  — nothing asked, nothing kept; the rules stay unmapped for review.

The manifest says what happened, counts only: ``layer2: {mode,
review_candidates, feeds: [{n, of, review_candidates, rules, calls, failed,
seconds, flags}]}`` and each feed entry's ``review_candidates`` — ``pending |
done | skipped`` (``none``: no unmapped rule)."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

MODES = ("now", "defer", "skip")
PENDING_FILE = "layer2_pending.json"
CANDIDATES_DIR = "candidates"

# a feed's review_candidates (the manifest) by what its stage did
_REVIEW = {"done": "done", "deferred": "pending", "skipped": "skipped", "none": "none"}
INFO_KINDS = ("unimplemented_rule_has_candidate", "layer2_candidate_not_grounded",
              "layer2_provider_failed")

# the report's line under the candidates heading while the stage has not asked
_NOTES = {
    "pending": "Layer 2: {n} unmapped rule(s) — the Layer-2 stage runs after the run's "
               "outcome is written; its candidates are added here.",
    "deferred": "Layer 2: {n} unmapped rule(s) — review candidates: pending (--layer2 "
                "defer). `codegen layer2 --output <output dir>` or the App's review panel "
                "asks the model.",
    "skipped": "Layer 2: {n} unmapped rule(s) — skipped (--layer2 skip): no candidate; the "
               "rules stay unmapped for review.",
}


def note(state: str, rules: int) -> str | None:
    """The report's Layer-2 line for a stage that has not asked (None once it has)."""
    return _NOTES[state].format(n=rules) if rules and state in _NOTES else None


@dataclass
class Layer2Job:
    """One feed's Layer-2 work, built by ``cli.generate_feed_result``."""

    feed_id: str
    feed_slug: str
    packs: list                          # reasoning.schema.ContextPack, one per rule
    confirm: list                        # the deterministic review items written at generate
    feed_dir: Path
    report_path: Path
    replay: list | None = None           # recorded candidates (no provider asked)
    n: int = 0                           # the feed's position (manifest feeds[].n / of)
    of: int = 0
    out_root: Path | None = None
    extra: dict = field(default_factory=dict)

    @property
    def rules(self) -> int:
        return len(self.packs)


def write_candidates(candidates: list, feed_dir: Path) -> Path | None:
    """Layer-2 output goes here — a review artifact, never a generated module."""
    if not candidates:
        return None
    artifact_dir = feed_dir / CANDIDATES_DIR
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = artifact_dir / "candidates.json"
    payload = []
    for candidate in candidates:
        entry = candidate.model_dump()
        if entry.get("kind") == "layer2":
            # Default-kind entries serialize exactly as before the segmented
            # dialect landed — flat candidates.json stays byte-identical.
            entry.pop("kind", None)
            entry.pop("detail", None)
            entry.pop("citation", None)
        payload.append(entry)
    artifact_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    return artifact_path


def info_flags(candidates: list) -> list[str]:
    """Layer 2's findings as INFORMATIONAL flags (post76) — never the verdict."""
    flags = []
    for c in candidates:
        if getattr(c, "kind", "layer2") != "layer2":
            continue
        notes = "; ".join(c.failure_notes)
        if c.response is None:
            flags.append(f"layer2_provider_failed:{c.rule_text!r} — {notes}")
        elif not c.grounded:
            flags.append(f"layer2_candidate_not_grounded:{c.rule_text!r} — {notes}")
        else:
            flags.append(f"unimplemented_rule_has_candidate:{c.rule_text!r} — a "
                         f"{c.response.classification} candidate awaits review")
    return flags


def run_job(job: Layer2Job, provider, *, config, base_dir: Path | None = None):
    """Ask ``provider`` about the feed's rules (one request), write the results.
    Returns (every candidate — confirm items first, the usage record)."""
    from codegen.reasoning.engine import reason_over_packs
    from codegen.reasoning.raw_log import log_layer2_failures
    from codegen.reasoning.usage import layer2_usage, replay_usage

    if job.replay is not None:
        candidates = list(job.replay)
        usage = replay_usage(candidates)
    else:
        layer2 = reason_over_packs(job.packs, provider)
        # 2026-10-14: every failed Layer-2 attempt on the log (reason + RAW, D1-only)
        log_layer2_failures(provider, job.feed_slug, config,
                            base_dir if base_dir is not None else Path("."))
        usage = layer2_usage(provider, layer2)
        candidates = [*job.confirm, *layer2]
    _finish(job, candidates, usage, None)
    _drop_pending(job.feed_dir)
    return candidates, usage


def defer_job(job: Layer2Job, out_root: Path | None = None):
    """``--layer2 defer``: the feed's packs kept for a later ask (no model call)."""
    from codegen.reasoning.usage import not_run_usage

    usage = not_run_usage("deferred", job.rules)
    if job.rules:
        folder = job.feed_dir / CANDIDATES_DIR
        folder.mkdir(parents=True, exist_ok=True)
        payload = {"feed_id": job.feed_id, "feed_slug": job.feed_slug, "n": job.n,
                   "of": job.of, "report": _relative(job.report_path, job.feed_dir),
                   "packs": [p.model_dump() for p in job.packs]}
        (folder / PENDING_FILE).write_text(json.dumps(payload, indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    _finish(job, list(job.confirm), usage, note("deferred", job.rules))
    return list(job.confirm), usage


def skip_job(job: Layer2Job):
    """``--layer2 skip``: nothing asked, nothing kept."""
    from codegen.reasoning.usage import not_run_usage

    usage = not_run_usage("skipped", job.rules)
    _finish(job, list(job.confirm), usage, note("skipped", job.rules))
    _drop_pending(job.feed_dir)
    return list(job.confirm), usage


def _finish(job: Layer2Job, candidates: list, usage, layer2_note: str | None) -> None:
    from codegen.emit.notebook_v2 import with_review
    from codegen.report.generation_report import rewrite_layer2

    write_candidates(candidates, job.feed_dir)
    rewrite_layer2(job.report_path, candidates, usage, layer2_note, info_flags(candidates))
    if any(getattr(c, "kind", "layer2") == "layer2" for c in candidates):
        with_review(job.feed_dir, job.feed_slug, candidates)   # the trailing %md only


def clear(feed_dir: Path) -> None:
    """A rerun's start: the feed's previous Layer-2 outputs go (a GATE_FAIL rerun
    must not leave the last run's candidates beside its quarantine)."""
    for name in ("candidates.json", PENDING_FILE):
        path = feed_dir / CANDIDATES_DIR / name
        if path.is_file():
            path.unlink()


def _drop_pending(feed_dir: Path) -> None:
    pending = feed_dir / CANDIDATES_DIR / PENDING_FILE
    if pending.is_file():
        pending.unlink()


def _relative(path: Path, start: Path) -> str:
    try:
        return Path(os.path.relpath(path, start)).as_posix()
    except ValueError:          # another drive (Windows)
        return Path(path).as_posix()


def run_stage(jobs: list[Layer2Job], mode: str, *, config, dry_run: bool,
              base_dir: Path | None = None, out_root: Path | None = None,
              say: Callable[[str], None] | None = print, console: bool = True,
              build=None) -> tuple[dict, dict]:
    """Every feed's Layer 2 in ``mode``; ``out_root``'s manifest gains the
    ``layer2`` block. Returns (that block, {feed_id: (candidates, usage)})."""
    if mode not in MODES:
        raise ValueError(f"--layer2 must be one of {', '.join(MODES)} (got {mode!r})")
    from codegen.run_errors import report_usage

    if build is None:
        from codegen.reasoning import build_provider as build
    results: dict = {}
    rows: list[dict] = []
    for job in jobs:
        if mode == "now" and (job.rules or job.replay is not None):
            provider = None if job.replay is not None else build(config, dry_run)
            candidates, usage = run_job(job, provider, config=config, base_dir=base_dir)
            state = "done"
        elif mode == "defer":
            candidates, usage = defer_job(job, out_root)
            state = "deferred" if job.rules else "none"
        elif mode == "skip":
            candidates, usage = skip_job(job)
            state = "skipped" if job.rules else "none"
        else:                                          # now, nothing to ask
            from codegen.reasoning.usage import StageUsage

            candidates, usage = list(job.confirm), StageUsage(stage="layer2", provider="none")
            state = "none"
        results[job.feed_id] = (candidates, usage)
        rows.append(_row(job, state, usage, candidates))
        if console and say is not None:
            say(f"{'MODEL USAGE':<15} {usage.stage}: {usage.label}")
        if console:
            report_usage(usage)        # post74: the numbers, for the harness report
    block = {"mode": mode, "review_candidates": _overall(rows), "feeds": rows}
    if out_root is not None:
        record(out_root, block)
    return block, results


def _row(job: Layer2Job, state: str, usage, candidates: list) -> dict:
    kinds = [flag.split(":", 1)[0] for flag in info_flags(candidates)]
    return {"n": job.n, "of": job.of, "review_candidates": _REVIEW[state], "rules": job.rules,
            "calls": usage.calls, "failed": usage.failed, "seconds": usage.seconds,
            "flags": {kind: kinds.count(kind) for kind in INFO_KINDS if kind in kinds}}


def _overall(rows: list[dict]) -> str:
    """The run's review_candidates: pending while any feed's is, else done /
    skipped, ``none`` when no feed had an unmapped rule."""
    states = {r["review_candidates"] for r in rows if r["rules"]}
    for state in ("pending", "done", "skipped"):
        if state in states:
            return state
    return "none"


def record(out_root: Path, block: dict) -> None:
    """The manifest's ``layer2`` block and each feed entry's ``review_candidates``
    (CODEGEN_STAGES.json, written by the run)."""
    from codegen import run_stages

    path = Path(out_root) / run_stages.STAGES_FILE
    if not path.is_file():
        return
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["layer2"] = block
    by_position = {(r["n"], r["of"]): r["review_candidates"] for r in block["feeds"]}
    for entry in payload.get("feeds") or []:
        state = by_position.get((entry.get("n"), entry.get("of")))
        if state is not None:
            entry["review_candidates"] = state
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")


def pending_jobs(out_root: Path, *, reports_dir: Path | None = None,
                 only_feed: str | None = None) -> list[Layer2Job]:
    """The deferred feeds under ``out_root`` (``<feed>/candidates/layer2_pending.json``)."""
    from codegen.reasoning.engine import RuleCandidate
    from codegen.reasoning.schema import ContextPack

    jobs: list[Layer2Job] = []
    for pending in sorted(Path(out_root).glob(f"*/{CANDIDATES_DIR}/{PENDING_FILE}")):
        data = json.loads(pending.read_text(encoding="utf-8"))
        if only_feed is not None and data["feed_id"] != only_feed:
            continue
        feed_dir = pending.parent.parent
        existing = feed_dir / CANDIDATES_DIR / "candidates.json"
        confirm = []
        if existing.is_file():
            confirm = [RuleCandidate.model_validate(c) for c in
                       json.loads(existing.read_text(encoding="utf-8"))
                       if c.get("kind", "layer2") != "layer2"]
        report = Path(data["report"])
        report = report if report.is_absolute() else (feed_dir / report).resolve()
        if reports_dir is not None and not report.is_file():
            report = Path(reports_dir) / f"{data['feed_slug']}.md"
        jobs.append(Layer2Job(
            feed_id=data["feed_id"], feed_slug=data["feed_slug"],
            packs=[ContextPack.model_validate(p) for p in data["packs"]], confirm=confirm,
            feed_dir=feed_dir, report_path=report, n=int(data.get("n") or 0),
            of=int(data.get("of") or 0), out_root=Path(out_root)))
    return jobs


def run_pending(out_root: Path, *, config, dry_run: bool, base_dir: Path | None = None,
                only_feed: str | None = None, reports_dir: Path | None = None,
                say: Callable[[str], None] | None = print, console: bool = True,
                build=None) -> tuple[dict, dict]:
    """``codegen layer2`` / the App's review panel: ask the deferred feeds now.
    The manifest's ``layer2`` block is updated for the feeds asked."""
    jobs = pending_jobs(out_root, reports_dir=reports_dir, only_feed=only_feed)
    block, results = run_stage(jobs, "now", config=config, dry_run=dry_run, base_dir=base_dir,
                               out_root=None, say=say, console=console, build=build)
    _merge_record(Path(out_root), block)
    return block, results


def _merge_record(out_root: Path, block: dict) -> None:
    """The asked feeds' rows replace their deferred rows; the status follows."""
    from codegen import run_stages

    manifest = run_stages.read_stage_manifest(out_root) or {}
    previous = manifest.get("layer2") or {"mode": "defer", "feeds": []}
    asked = {(r["n"], r["of"]) for r in block["feeds"]}
    rows = [r for r in previous.get("feeds") or [] if (r.get("n"), r.get("of")) not in asked]
    rows = sorted([*rows, *block["feeds"]], key=lambda r: (r.get("n") or 0))
    record(out_root, {"mode": previous.get("mode", "defer"), "review_candidates": _overall(rows),
                      "feeds": rows})


__all__ = ["INFO_KINDS", "MODES", "PENDING_FILE", "Layer2Job", "clear", "defer_job", "info_flags",
           "note", "pending_jobs", "record", "run_job", "run_pending", "run_stage", "skip_job",
           "write_candidates"]
