"""Render one feed's generation report.

Markdown into ``reports/<feed_slug>.md`` plus a one-line console summary.
Deterministic like everything else: no timestamps, content depends only on
the run's inputs and results. Reports show contract text and column names —
never data values — so there is no PHI egress here by construction.
"""

from __future__ import annotations

import re
from pathlib import Path

from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.gate.verdict import GateResult
from codegen.reasoning.engine import RuleCandidate
from codegen.reasoning.usage import StageUsage, report_lines
from codegen.rules.compiler import RuleOutcome

# post159 (P1-5, APP-MD-1 / APP-XSS-2): document and model text reaches the
# report and the notebook review cell as markdown that VS Code / a Databricks
# notebook render UNSANITISED. md_inline() keeps it one inert line of text:
# only the characters that would start structure are touched, so ordinary text
# ("a -> b", "AT&T", "amount < 5") is unchanged - no backslash on every '*'.
_LINE_BREAKS = re.compile(r"[\r\n\v\f\x85\u2028\u2029]+")
# '<' that would open a tag, a comment, a declaration or an autolink
_TAG_OPEN = re.compile(r"<(?=[A-Za-z/!?])")
# '&' that would be read as an entity reference
_ENTITY = re.compile(r"&(?=#[0-9]+;|#[xX][0-9A-Fa-f]+;|[A-Za-z][A-Za-z0-9]*;)")
# a forged verdict line: '**Verdict' / '__Verdict' anywhere
_VERDICT = re.compile(r"(\*\*|__)(?=\s*verdict)", re.IGNORECASE)
# an ordered-list start ('1.' / '1)'), and a line that would open any other
# block: heading, quote, list item, fence, thematic break / setext underline,
# link reference definition
_ORDERED = re.compile(r"(\d{1,9})[.)](?=[ \t]|$)")
_BLOCK_START = re.compile(
    r"#|>|[-+*](?=[ \t]|$)|`{3,}|~{3,}|\[|"
    r"([-*_])(?:[ \t]*\1){2,}[ \t]*$|=+[ \t]*$")


def md_inline(text: object, *, line_start: bool = True) -> str:
    """One line of document / model text made inert for a markdown viewer.

    CR / LF and the other line breaks collapse to one space; a '<' opening a
    tag / comment / autolink and an '&' opening an entity are escaped; link
    and image syntax (``](``, ``![``, ``][``) and a ``**Verdict`` are
    neutralised; with ``line_start`` (the text begins a line, a list item or a
    quote), a block start (``#``, ``>``, ``-``/``*``/``+``, ``1.``, a fence, a
    rule, ``[``) gets ONE backslash. Every other character is left alone."""
    if text is None:
        return ""
    value = _LINE_BREAKS.sub(" ", str(text))
    value = _ENTITY.sub("&amp;", value)
    value = _TAG_OPEN.sub("&lt;", value)
    value = _VERDICT.sub(lambda m: "\\" + m.group(1)[0] + "\\" + m.group(1)[1], value)
    value = value.replace("](", "]\\(").replace("![", "!\\[").replace("][", "]\\[")
    if line_start:
        value = value.lstrip(" \t")
        ordered = _ORDERED.match(value)
        if ordered:         # '\1.' is no escape: the backslash goes before the '.'
            value = value[:ordered.end(1)] + "\\" + value[ordered.end(1):]
        elif _BLOCK_START.match(value):
            value = "\\" + value
    return value


def md_fence(code: str, info: str = "") -> list[str]:
    """A fenced code block that ``code`` cannot close: the fence is a backtick
    run one longer than the longest run inside it (at least three)."""
    longest = max((len(run) for run in re.findall(r"`+", code)), default=0)
    fence = "`" * max(3, longest + 1)
    return [fence + info, code.rstrip(), fence]


def md_code_span(text: str) -> str:
    """Inline code ``text`` cannot close (one line)."""
    value = _LINE_BREAKS.sub(" ", text)
    longest = max((len(run) for run in re.findall(r"`+", value)), default=0)
    ticks = "`" * (longest + 1)
    pad = " " if value.startswith("`") or value.endswith("`") else ""
    return f"{ticks}{pad}{value}{pad}{ticks}"


def md_cell(text: str | None) -> str:
    """Escape a value for a markdown table cell (md_inline, then '|')."""
    if text is None:
        return ""
    return md_inline(text, line_start=False).replace("|", "\\|")



def _contracts_section(spec: ResolvedFeedSpec) -> list[str]:
    synthetic = " **(SYNTHETIC stand-in)**" if spec.sttm_is_synthetic else ""
    return [
        "## Contracts",
        "",
        f"- FRD: {md_code_span(spec.frd_contract_name)} — sha256 `{spec.frd_contract_sha256}`",
        f"- STTM: {md_code_span(spec.sttm_contract_name)} — sha256 "
        f"`{spec.sttm_contract_sha256}`{synthetic}",
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
        lines.append(f"- {md_code_span(path.relative_to(out_root).as_posix())}")
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
            f"| {index} | {outcome.classification} | {md_cell(outcome.feature)} "
            f"| {md_cell(outcome.rule_text)} | {md_cell(outcome.grounding)} "
            f"| {md_cell(outcome.notes)} |"
        )
    lines.append("")
    return lines


CANDIDATES_HEADING = "## Layer-2 candidates (review required — never auto-merged)"
LAYER2_USAGE_PREFIX = "- Layer 2 (rule reasoning): "
# post159 (P1-5): the candidates section is bounded by these two lines, so
# rewrite_layer2 never depends on the next '## ' line (document / model text
# cannot write either: md_inline escapes the '<' of '<!--'; a code_candidate
# can, inside its fence, so the section is the FIRST begin to the LAST end).
LAYER2_BEGIN = "<!-- codegen:layer2-candidates:begin -->"
LAYER2_END = "<!-- codegen:layer2-candidates:end -->"
# a report written before the sentinels: its section ends at the first of
# the headings generate writes after it (never at a forged '## ' line)
_AFTER_CANDIDATES = ("## Model usage", "## Gate")
WITHHELD = ("- Withheld: the model's rationale, citations and code - a citation failed "
            "grounding (`candidates/candidates.json` keeps the answer for review)")


def _candidates_section(candidates: list[RuleCandidate],
                        layer2_note: str | None = None,
                        info_flags: list[str] | None = None) -> list[str]:
    return [LAYER2_BEGIN, *_candidates_body(candidates, layer2_note, info_flags),
            LAYER2_END, ""]


def _candidates_body(candidates: list[RuleCandidate], layer2_note: str | None,
                     info_flags: list[str] | None) -> list[str]:
    lines = [CANDIDATES_HEADING, ""]
    if layer2_note:
        # post76: the Layer-2 stage runs after emit — where the rules stand
        lines += [layer2_note, ""]
    if info_flags:
        # post76: what Layer 2 found — informational, never the verdict
        lines += ["Informational flags (Layer 2 — never the gate verdict):", ""]
        lines += [f"- {md_inline(flag)}" for flag in info_flags]
        lines.append("")
    if not candidates:
        if not layer2_note:
            lines += ["None — every rule compiled deterministically.", ""]
        return lines
    for index, candidate in enumerate(candidates, start=1):
        if candidate.kind == "confirm":
            lines += [
                f"### Review item {index} (CONFIRM — document-derived, cited)",
                "",
                f"- {md_inline(candidate.rule_text)}",
            ]
            if candidate.detail:
                lines.append(f"- {md_inline(candidate.detail)}")
            if candidate.citation:
                lines.append(f"- Evidence: > {md_inline(candidate.citation, line_start=False)}")
            lines.append("")
            continue
        grounded = "grounded" if candidate.grounded else "**NOT GROUNDED**"
        lines += [
            f"### Candidate {index} ({md_inline(candidate.provider, line_start=False)}, "
            f"{grounded})",
            "",
            f"- Rule: {md_inline(candidate.rule_text, line_start=False)}",
        ]
        if candidate.response is None:
            lines.append("- Provider response: **failed** — see notes below")
        elif not candidate.grounded:
            # post159 (P1-5): an ungrounded answer is coordinates + reason only
            lines.append(WITHHELD)
        else:
            lines += [
                f"- Proposed classification: {candidate.response.classification}",
                f"- Rationale: {md_inline(candidate.response.rationale, line_start=False)}",
                "- Citations:",
            ]
            lines += [f"  - > {md_inline(citation)}"
                      for citation in candidate.response.citations]
            if candidate.response.code_candidate is not None:
                lines += ["", *md_fence(candidate.response.code_candidate, "python")]
        if candidate.failure_notes:
            lines.append("- Failure notes:")
            lines += [f"  - {md_inline(note)}" for note in candidate.failure_notes]
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
        f"- Segments found: {md_inline(', '.join(seg.segments_found), line_start=False)}"
        " — row counts: "
        + md_inline(", ".join(f"{k}={v}" for k, v in seg.row_counts.items()),
                    line_start=False),
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
            f"| {md_cell(segment.segment)} | {md_cell(segment.stage_table.qualified_name)} "
            f"| {md_cell(standard)} | {len(segment.fields)} |"
        )
    lines += [
        "",
        f"### Record identification ({md_inline(ident.method, line_start=False)})",
        "",
        "- Trailer: record whose first field equals "
        + md_inline(repr(ident.trailer_marker), line_start=False),
        f"- Header: {md_inline(ident.header_rule, line_start=False)}",
        f"- Detail: {md_inline(ident.detail_rule, line_start=False)}",
        f"- Evidence: > {md_inline(ident.citation, line_start=False)}",
        "",
    ]
    if seg.provenance_notes:
        lines += ["### Provenance notes (each cites its document evidence)", ""]
        for entry in seg.provenance_notes:
            lines.append(f"- {md_inline(entry.note)}")
            lines.append(f"  - Evidence: > {md_inline(entry.citation, line_start=False)}")
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
        lines.append(f"| {check.name} | {result} | {md_cell(check.details)} |")
    lines.append("")
    if gate.flags and gate.verdict == "FAIL":
        # D1 post51 pair_01 (139 flags): grouped by type, the largest first —
        # this report stays inside ACFC; the pushed tier carries the counts.
        from codegen.run_stages import flag_type

        groups: dict[str, list[str]] = {}
        for flag in gate.flags:
            groups.setdefault(flag_type(flag), []).append(flag)
        lines.append(f"Flags by type ({len(gate.flags)}):")
        lines.append("")
        for kind, items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            lines += [f"### {md_code_span(kind)} \u2014 {len(items)}", ""]
            lines += [f"- {md_inline(flag)}" for flag in items]
            lines.append("")
    elif gate.flags:
        lines.append("Flags:")
        lines += [f"- {md_inline(flag)}" for flag in gate.flags]
        lines.append("")
    lines += [f"**Verdict: {gate.verdict}**", ""]
    return lines


def all_failed_line(usage: StageUsage) -> str:
    """2026-10-14 (D1 pair_12: 5 of 5 Layer-2 calls failed, said only in the
    flags): a live stage where every request failed, in one line."""
    titles = {"layer2": "Layer 2 (rule reasoning)", "layout": "Layout recognizer"}
    return (f"{titles.get(usage.stage, usage.stage)}: every model call failed "
            f"({usage.failed} of {usage.requests} request(s), {usage.calls} call(s)) — "
            "no model proposal in this run; the rules stay unmapped for review. "
            "The reasons are on the run's log (LAYER2 FAILED).")


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
    layer2_note: str | None = None,
) -> Path:
    lines: list[str] = [f"# Generation report — {spec.feed_id}", ""]
    lines += [f"> **WARNING** {all_failed_line(u)}\n" for u in model_usage or ()
              if u.all_failed]
    # 2026-10-14 (D1 post44): blocking questions and non-blocking inputs, counted
    # apart — said whenever the feed owes either (a feed owing nothing: no line)
    from codegen.owed_inputs import answers_owed, owed_header, run_block

    # 2026-10-14 (post47): the run-level inputs (environment, APPLICATION_NAME,
    # EMAIL_TO) in ONE block at the top; the feed's own counted below it
    lines += run_block(list(gate.flags))
    if any(answers_owed(list(gate.flags))):
        lines += [owed_header(list(gate.flags)), ""]
    from codegen.environments import header_line

    environment = header_line(list(gate.flags))     # 2026-10-14: the run's environment
    if environment is not None:
        lines += [environment, ""]
    lines += _contracts_section(spec)
    lines += _inputs_section(inputs_summary)
    lines += _files_section(written_files, out_root)
    lines += _rules_section(outcomes)
    lines += _segmented_section(spec)
    lines += _candidates_section(candidates, layer2_note)
    # What the run actually did with a model, per stage (codegen.reasoning.usage).
    if model_usage:
        lines += report_lines(model_usage)
    lines += _gate_section(gate)

    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / f"{spec.feed_slug}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return report_path


def _candidates_bounds(lines: list[str]) -> tuple[int, int] | None:
    """[start, end) of the report's candidates section. post159: the sentinel
    lines (the FIRST begin to the LAST end — a code_candidate inside its fence
    is the only text that can spell either); a report written before them:
    the heading to the first heading generate writes after it."""
    if LAYER2_BEGIN in lines:
        start = lines.index(LAYER2_BEGIN)
        ends = [i for i in range(start + 1, len(lines)) if lines[i] == LAYER2_END]
        if ends:
            return start, ends[-1] + 1
    if CANDIDATES_HEADING not in lines:
        return None
    start = lines.index(CANDIDATES_HEADING)
    after = [i for i in range(start + 1, len(lines)) if lines[i] in _AFTER_CANDIDATES]
    if after:
        # the blank line before that heading stays (the new section ends with one)
        return start, after[0] - 1 if lines[after[0] - 1] == "" else after[0]
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
               len(lines))
    return start, end - 1 if end > start + 1 and lines[end - 1] == "" else end


def rewrite_layer2(report_path: Path, candidates: list[RuleCandidate], usage: StageUsage,
                   layer2_note: str | None = None,
                   info_flags: list[str] | None = None) -> None:
    """post76: the Layer-2 stage's results written into a feed's report after
    the fact — the candidates section, the Model usage line and the all-failed
    WARNING; every other line stays as generate wrote it. post159: the line
    edits never reach inside the candidates section (a code_candidate line
    could spell the usage prefix)."""
    if not report_path.is_file():
        return
    lines = report_path.read_text(encoding="utf-8").split("\n")
    bounds = _candidates_bounds(lines)
    if bounds is None:
        before, section, after = lines, None, []
    else:
        before, after = lines[:bounds[0]], lines[bounds[1]:]
        section = _candidates_section(candidates, layer2_note, info_flags)[:-1]

    def _edit(part: list[str]) -> list[str]:
        part = [ln for ln in part
                if not ln.startswith("> **WARNING** Layer 2 (rule reasoning)")]
        label = LAYER2_USAGE_PREFIX + usage.label
        return [label if ln.startswith(LAYER2_USAGE_PREFIX) else ln for ln in part]

    before, after = _edit(before), _edit(after)
    if usage.all_failed:
        title = next((i for i, ln in enumerate(before)
                      if ln.startswith("# Generation report")), 0)
        before[title + 2:title + 2] = [f"> **WARNING** {all_failed_line(usage)}", ""]
    lines = [*before, *(section or []), *after]
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


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
