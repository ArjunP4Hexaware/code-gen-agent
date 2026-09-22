"""Render one feed's generation report.

Markdown into ``reports/<feed_slug>.md`` plus a one-line console summary.
Deterministic like everything else: no timestamps, content depends only on
the run's inputs and results. Reports show contract text and column names —
never data values — so there is no PHI egress here by construction.
"""

from __future__ import annotations

from pathlib import Path

from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.gate.verdict import GateResult
from codegen.reasoning.engine import RuleCandidate
from codegen.reasoning.usage import StageUsage, report_lines
from codegen.rules.compiler import RuleOutcome


def _cell(text: str | None) -> str:
    """Escape a value for a markdown table cell."""
    if text is None:
        return ""
    return text.replace("|", "\\|").replace("\n", " ")


def _contracts_section(spec: ResolvedFeedSpec) -> list[str]:
    synthetic = " **(SYNTHETIC stand-in)**" if spec.sttm_is_synthetic else ""
    return [
        "## Contracts",
        "",
        f"- FRD: `{spec.frd_contract_name}` — sha256 `{spec.frd_contract_sha256}`",
        f"- STTM: `{spec.sttm_contract_name}` — sha256 `{spec.sttm_contract_sha256}`{synthetic}",
        "",
    ]


def _inputs_section(inputs_summary: dict | None) -> list[str]:
    """Three-input model header — mirrors the provenance banner block."""
    if inputs_summary is None:
        return []
    if inputs_summary["dataset_source"] or inputs_summary["dataset_target"]:
        dataset_line = (
            f"source={inputs_summary['dataset_source'] or '?'} "
            f"target={inputs_summary['dataset_target'] or '?'}"
        )
    else:
        dataset_line = "not yet integrated (planned)"
    return [
        "## Inputs (three-input model)",
        "",
        f"- Engineering standards: {inputs_summary['standards_status']}",
        f"- Load-pattern FAQ: {inputs_summary['answered']} answered "
        f"({inputs_summary['from_contract']} from contract), "
        f"{inputs_summary['unknown']} unknown",
        f"- Collibra dataset IDs: {dataset_line}",
        f"- Declared load mode: {inputs_summary['load_mode']} "
        f"(source: {inputs_summary['load_mode_source']})",
        f"- Write behavior in this version: {inputs_summary['writer_behavior']} "
        "(load-mode branching: v2)",
        "",
    ]


def _files_section(written_files: list[Path], out_root: Path) -> list[str]:
    lines = ["## Files emitted", ""]
    for path in written_files:
        lines.append(f"- `{path.relative_to(out_root).as_posix()}`")
    lines.append("")
    return lines


def _rules_section(outcomes: list[RuleOutcome]) -> list[str]:
    lines = [
        "## Validation rules",
        "",
        "| # | Classification | Feature | Rule | Grounding | Notes |",
        "|---|---|---|---|---|---|",
    ]
    for index, outcome in enumerate(outcomes, start=1):
        lines.append(
            f"| {index} | {outcome.classification} | {_cell(outcome.feature)} "
            f"| {_cell(outcome.rule_text)} | {_cell(outcome.grounding)} "
            f"| {_cell(outcome.notes)} |"
        )
    lines.append("")
    return lines


def _candidates_section(candidates: list[RuleCandidate]) -> list[str]:
    lines = ["## Layer-2 candidates (review required — never auto-merged)", ""]
    if not candidates:
        lines += ["None — every rule compiled deterministically.", ""]
        return lines
    for index, candidate in enumerate(candidates, start=1):
        if candidate.kind == "confirm":
            lines += [
                f"### Review item {index} (CONFIRM — document-derived, cited)",
                "",
                f"- {candidate.rule_text}",
            ]
            if candidate.detail:
                lines.append(f"- {candidate.detail}")
            if candidate.citation:
                lines.append(f"- Evidence: > {candidate.citation}")
            lines.append("")
            continue
        grounded = "grounded" if candidate.grounded else "**NOT GROUNDED**"
        lines += [
            f"### Candidate {index} ({candidate.provider}, {grounded})",
            "",
            f"- Rule: {candidate.rule_text}",
        ]
        if candidate.response is None:
            lines.append("- Provider response: **failed** — see notes below")
        else:
            lines += [
                f"- Proposed classification: {candidate.response.classification}",
                f"- Rationale: {candidate.response.rationale}",
                "- Citations:",
            ]
            lines += [f"  - > {citation}" for citation in candidate.response.citations]
            if candidate.response.code_candidate is not None:
                lines += ["", "```python", candidate.response.code_candidate.rstrip(), "```"]
        if candidate.failure_notes:
            lines.append("- Failure notes:")
            lines += [f"  - {note}" for note in candidate.failure_notes]
        lines.append("")
    return lines


def _segmented_section(spec: ResolvedFeedSpec) -> list[str]:
    """Segmented-extraction facts: segments as tables in both layers, the
    document-derived record identification (with its STTM citation), and the
    cited provenance notes. Empty for flat feeds so their reports stay
    byte-identical."""
    seg = spec.segmented_extraction
    if seg is None:
        return []
    ident = seg.identification
    lines = [
        "## Segmented extraction",
        "",
        f"- Segments found: {', '.join(seg.segments_found)} — row counts: "
        + ", ".join(f"{k}={v}" for k, v in seg.row_counts.items()),
        "",
        "### Segment tables (both layers)",
        "",
        "| Segment | Stage table | Standard table | Columns |",
        "|---|---|---|---|",
    ]
    for segment in spec.segments:
        standard = (segment.standard_table.qualified_name
                    if segment.standard_table is not None else "—")
        lines.append(
            f"| {segment.segment} | {segment.stage_table.qualified_name} "
            f"| {standard} | {len(segment.fields)} |"
        )
    lines += [
        "",
        f"### Record identification ({ident.method})",
        "",
        f"- Trailer: record whose first field equals {ident.trailer_marker!r}",
        f"- Header: {ident.header_rule}",
        f"- Detail: {ident.detail_rule}",
        f"- Evidence: > {ident.citation}",
        "",
    ]
    if seg.provenance_notes:
        lines += ["### Provenance notes (each cites its document evidence)", ""]
        for entry in seg.provenance_notes:
            lines.append(f"- {entry.note}")
            lines.append(f"  - Evidence: > {entry.citation}")
        lines.append("")
    return lines


def _gate_section(gate: GateResult) -> list[str]:
    lines = [
        "## Gate",
        "",
        "| Check | Result | Details |",
        "|---|---|---|",
    ]
    for check in gate.checks:
        result = "NOT RUN" if check.not_run else "pass" if check.passed else "**FAIL**"
        lines.append(f"| {check.name} | {result} | {_cell(check.details)} |")
    lines.append("")
    if gate.flags:
        lines.append("Flags:")
        lines += [f"- {flag}" for flag in gate.flags]
        lines.append("")
    lines += [f"**Verdict: {gate.verdict}**", ""]
    return lines


def write_generation_report(
    spec: ResolvedFeedSpec,
    written_files: list[Path],
    outcomes: list[RuleOutcome],
    candidates: list[RuleCandidate],
    gate: GateResult,
    reports_dir: Path,
    out_root: Path,
    inputs_summary: dict | None = None,
    model_usage: list[StageUsage] | None = None,
) -> Path:
    lines: list[str] = [f"# Generation report — {spec.feed_id}", ""]
    lines += _contracts_section(spec)
    lines += _inputs_section(inputs_summary)
    lines += _files_section(written_files, out_root)
    lines += _rules_section(outcomes)
    lines += _segmented_section(spec)
    lines += _candidates_section(candidates)
    # What the run actually did with a model, per stage (codegen.reasoning.usage).
    if model_usage:
        lines += report_lines(model_usage)
    lines += _gate_section(gate)

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{spec.feed_slug}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return report_path


_CONSOLE_DETAIL_LINES = 8


def console_summary(spec: ResolvedFeedSpec, gate: GateResult) -> str:
    checks = ", ".join(
        f"{check.name}={'not-run' if check.not_run else 'ok' if check.passed else 'FAIL'}"
        for check in gate.checks)
    summary = (
        f"{gate.verdict:<15} {spec.feed_id} — "
        f"{len(gate.flags)} flag(s); {checks if checks else 'no checks run'}"
    )
    # M9.1b: a check that failed (or did not run) says WHY on the console — the
    # first lines of its details; the report has the rest. The headline word is
    # the gate verdict, and the exit code follows it (FAIL -> 1, else 0).
    for check in gate.checks:
        if check.passed and not check.not_run:
            continue
        label = "CHECK NOT RUN" if check.not_run else "CHECK FAILED"
        shown = check.details.splitlines()[:_CONSOLE_DETAIL_LINES]
        more = len(check.details.splitlines()) - len(shown)
        summary += f"\n{label:<15} {check.name} — " + "\n                ".join(shown)
        if more > 0:
            summary += f"\n                … {more} more line(s) in the report"
    return summary
