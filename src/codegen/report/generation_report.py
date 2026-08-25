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


def _gate_section(gate: GateResult) -> list[str]:
    lines = [
        "## Gate",
        "",
        "| Check | Result | Details |",
        "|---|---|---|",
    ]
    for check in gate.checks:
        result = "pass" if check.passed else "**FAIL**"
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
) -> Path:
    lines: list[str] = [f"# Generation report — {spec.feed_id}", ""]
    lines += _contracts_section(spec)
    lines += _inputs_section(inputs_summary)
    lines += _files_section(written_files, out_root)
    lines += _rules_section(outcomes)
    lines += _candidates_section(candidates)
    lines += _gate_section(gate)

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{spec.feed_slug}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return report_path


def console_summary(spec: ResolvedFeedSpec, gate: GateResult) -> str:
    checks = ", ".join(f"{check.name}={'ok' if check.passed else 'FAIL'}" for check in gate.checks)
    return (
        f"{gate.verdict:<15} {spec.feed_id} — "
        f"{len(gate.flags)} flag(s); {checks if checks else 'no checks run'}"
    )
