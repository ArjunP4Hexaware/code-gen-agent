"""The answers template (2026-10-13, D1 pair_11): when a stage exits 3
(NEEDS_ANSWERS), every open question is written to ``answers_template.yaml``
beside the stage's output — its key, why it is asked, its candidates and an
EMPTY value. The person fills the values in the workspace and reruns with
``--answers <that file>``: one pass, no copying keys out of the console.

The file is an ordinary answers file (``codegen.layout.answers.load_answers``):
an entry left empty is skipped (its question stays open), ``question`` and
``candidates`` are read as comments. ``layout`` writes the template fresh;
``extract-sttm`` adds its own questions to one ``layout`` wrote beside it, so
the file holds every question of the run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

TEMPLATE_NAME = "answers_template.yaml"
_HEADER = "# codegen answers template"
_ROLE_KEY_PARTS = 3


@dataclass(frozen=True)
class TemplateItem:
    key: str                       # a gaps: key, or sheets[<i>]/<layer>/<role>
    reason: str
    candidates: list[str] = field(default_factory=list)
    section: str = "gaps"          # gaps | answers | inputs (non-blocking, INPUT_NEEDED)
    # 2026-10-14 (D1 pair_12): one value PER FILE (the LOB lookup's question):
    # written as a ``files:`` block, every file a key with an empty value.
    files: list[str] = field(default_factory=list)
    # post57: the sheet a ``sheets[<i>]/...`` key means, as written — a reading
    # aid in this ACFC-side file only (never on stdout).
    sheet_name: str = ""
    # post59: a defaulted input's three-way choice (codegen.input_choices):
    # the options offered, the proposal and its template (reading aids — the
    # choice itself is written empty: proposed is not applied)
    options: list[str] = field(default_factory=list)
    proposed: str = ""
    proposed_template: str = ""
    # post59: a convenience entry (the feed-level pipeline_name choice that
    # covers every flow) — not an input owed, not counted in the header
    shared: bool = False
    # post61: a profile default the run WROTE (its value) — listed so the BSA
    # can change it, not an input owed, not counted in the header
    applied: str = ""


def _q(value: str) -> str:
    """A YAML scalar: JSON strings are valid YAML double-quoted scalars."""
    return json.dumps(value, ensure_ascii=False)


def _answers_entry(item: TemplateItem) -> list[str]:
    from codegen.layout.profile import BAND_LAYER_ROLE, BAND_REF_RE

    sheet, layer, role = item.key.rsplit("/", 2) if item.key.count("/") >= 2 else (
        item.key, "", "")
    lines = [f"  - sheet: {_q(sheet)}", f"    layer: {_q(layer)}", f"    role: {_q(role)}"]
    if item.sheet_name and item.sheet_name != sheet:
        lines.append(f"    sheet_name: {_q(item.sheet_name)}")
    if role == BAND_LAYER_ROLE and BAND_REF_RE.match(layer):
        lines.append('    value: ""                    # source | stage | standard')
    else:
        lines.append('    column: ""                   # header text | 1-based index | letter')
    lines.append(f"    question: {_q(item.reason)}")
    lines.append(f"    candidates: {json.dumps(item.candidates, ensure_ascii=False)}")
    return lines


def _gaps_entry(item: TemplateItem) -> list[str]:
    if item.options:
        from codegen.input_choices import PLACEHOLDERS

        placeholders = " ".join("{" + p + "}" for p in PLACEHOLDERS)
        how = ("profile default, written when left empty" if item.applied
               else f"proposed: {item.options[0]} (applied only when written here)")
        return [f"  {_q(item.key)}:",
                f'    choice: ""                 # {" | ".join(item.options)} — {how}',
                *(['    standard: ""               # naming_standard: a template over '
                   f"{placeholders}"] if "naming_standard" in item.options else []),
                '    value: ""',
                f"    proposed: {_q(item.proposed)}",
                f"    template: {_q(item.proposed_template)}",
                *([f"    applied: {_q(item.applied)}"] if item.applied else []),
                *(["    shared: true               # covers every flow of the feed"]
                  if item.shared else []),
                f"    question: {_q(item.reason)}",
                f"    candidates: {json.dumps(item.candidates, ensure_ascii=False)}"]
    if item.files:
        return [f"  {_q(item.key)}:",
                "    files:",
                *(f'      {_q(name)}: ""' for name in item.files),
                f"    question: {_q(item.reason)}",
                f"    candidates: {json.dumps(item.candidates, ensure_ascii=False)}"]
    return [f"  {_q(item.key)}:",
            '    value: ""',
            f"    question: {_q(item.reason)}",
            f"    candidates: {json.dumps(item.candidates, ensure_ascii=False)}"]


def read_template(path: Path) -> list[TemplateItem]:
    """The items of a template this module wrote (anything else: none)."""
    try:
        body = Path(path).read_text(encoding="utf-8")
    except OSError:
        return []
    if not body.startswith(_HEADER):
        return []
    raw = yaml.safe_load(body) or {}
    items: list[TemplateItem] = []
    for entry in raw.get("answers") or []:
        key = f"{entry.get('sheet')}/{entry.get('layer')}/{entry.get('role')}"
        items.append(TemplateItem(key, str(entry.get("question") or ""),
                                  [str(c) for c in entry.get("candidates") or []], "answers",
                                  sheet_name=str(entry.get("sheet_name") or "")))
    for section in ("gaps", "inputs"):
        block = raw.get(section) or {}
        entries = flatten_inputs(block) if section == "inputs" else block
        for key, entry in entries.items():
            entry = entry if isinstance(entry, dict) else {}
            options = ([o.strip() for o in str(entry.get("_options") or "").split("|")
                        if o.strip()] or (_OPTIONS_READ if "choice" in entry else []))
            items.append(TemplateItem(str(key), str(entry.get("question") or ""),
                                      [str(c) for c in entry.get("candidates") or []], section,
                                      files=[str(f) for f in entry.get("files") or {}],
                                      options=options,
                                      proposed=str(entry.get("proposed") or ""),
                                      proposed_template=str(entry.get("template") or ""),
                                      shared=bool(entry.get("shared")),
                                      applied=str(entry.get("applied") or "")))
    return items


def flatten_inputs(block: dict) -> dict:
    """``inputs:`` -> {flat key: entry}: 2026-10-14 (post47) ``run: {<name>: ...}``
    -> ``run.<name>``, ``feeds: {<feed>: {<name>: ...}}`` -> ``feeds.<feed>.<name>``;
    any other key (the older flat ``feeds[<i>].<name>`` / ``run.environment``)
    as it is."""
    out: dict = {}
    for key, entry in (block or {}).items():
        if key == "run" and isinstance(entry, dict) and not _is_entry(entry):
            out.update({f"run.{name}": value for name, value in entry.items()})
        elif key == "feeds" and isinstance(entry, dict) and not _is_entry(entry):
            for feed, names in entry.items():
                out.update({f"feeds.{feed}.{name}": value
                            for name, value in (names or {}).items()})
        else:
            out[str(key)] = entry
    return out


_OPTIONS_READ = ["use_default", "naming_standard", "leave_blank"]


def _is_entry(entry: dict) -> bool:
    return any(k in entry for k in ("value", "question", "choice", "standard"))


def write_answers_template(path: Path, items: list[TemplateItem], *, stage: str,
                           merge: bool = False) -> Path:
    """Write ``items`` (one per key, first wins) as an answers template.
    ``merge``: keep the questions of a template already at ``path``."""
    path = Path(path)
    ordered: dict[str, TemplateItem] = {}
    for item in [*(read_template(path) if merge else []), *items]:
        ordered.setdefault(item.key, item)
    answers = [i for i in ordered.values() if i.section == "answers"]
    inputs = [i for i in ordered.values() if i.section == "inputs"]
    gaps = [i for i in ordered.values() if i.section not in ("answers", "inputs")]
    owed = [i for i in inputs if not i.shared and not i.applied]
    lines = [f"{_HEADER} — {len(ordered) - len(inputs)} open question(s), "
             f"{len(owed)} input(s) needed, written by {stage}.",
             "# Fill each empty value / column, then rerun the run's stages with",
             "#   --answers <this file>   (layout, extract-sttm and generate read it).",
             "# An entry left empty is skipped: its question stays open.",
             "# `question`, `candidates` and `sheet_name` are for reading only.",
             ""]
    lines.append("answers:" if answers else "answers: []")
    for item in answers:
        lines += _answers_entry(item)
    lines.append("gaps:" if gaps else "gaps: {}")
    for item in gaps:
        lines += _gaps_entry(item)
    if inputs:
        # 2026-10-14 (D1 post44): never blocking — the workbook is written with the
        # cell empty; a value here fills it when generate reruns with --answers.
        # post47: run-level inputs (one value for the whole run) under `run:`,
        # feed-level under `feeds: <feed>:`.
        lines.append("inputs:")
        run = [i for i in inputs if i.key.startswith("run.")]
        if run:
            lines.append("  run:")
            for item in run:
                lines += _indent(_gaps_entry(TemplateItem(
                    item.key[len("run."):], item.reason, item.candidates,
                    options=item.options, proposed=item.proposed,
                    proposed_template=item.proposed_template, applied=item.applied)), 2)
        feeds: dict[str, list[TemplateItem]] = {}
        other = []
        for item in inputs:
            if item.key.startswith("feeds.") and item.key.count(".") >= 2:
                feed, name = item.key[len("feeds."):].split(".", 1)
                feeds.setdefault(feed, []).append(TemplateItem(
                    name, item.reason, item.candidates, options=item.options,
                    proposed=item.proposed, proposed_template=item.proposed_template,
                    shared=item.shared, applied=item.applied))
            elif not item.key.startswith("run."):
                other.append(item)
        if feeds:
            lines.append("  feeds:")
            for feed, entries in feeds.items():
                lines.append(f"    {_q(feed)}:")
                for entry in entries:
                    lines += _indent(_gaps_entry(entry), 4)
        for item in other:          # an older flat key (feeds[<i>].<name>)
            lines += _gaps_entry(item)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


FILES_SUFFIX = ".lob_by_file"


def file_pairs(value: str) -> list[tuple[str, str]]:
    """``<file>=<value>; ...`` (a ``files:`` answer as text) -> ordered pairs."""
    pairs = []
    for part in str(value or "").split(";"):
        name, sep, answer = part.partition("=")
        if sep and name.strip() and answer.strip():
            pairs.append((name.strip(), answer.strip()))
    return pairs


def write_applied_answers(path: Path, gaps: dict[str, str], *, stage: str) -> Path:
    """2026-10-14 (post47): the ``gaps:`` answers a run applied, as an ordinary
    answers file (``--answers`` reads it): a per-file answer (the LOB lookup's
    ``<feed>.lob_by_file``) as its ``files:`` block. EVERY value is written
    quoted — a LOB code ``0100`` unquoted is YAML's number 64."""
    lines = [f"# codegen answers — the gaps answers {stage} applied; every value quoted.",
             "# Rerun the CLI with --answers <this file> to apply the same answers.", "",
             "gaps:" if gaps else "gaps: {}"]
    for key, value in gaps.items():
        lines.append(f"  {_q(key)}:")
        pairs = file_pairs(value) if key.endswith(FILES_SUFFIX) else []
        if pairs:
            lines.append("    files:")
            lines += [f"      {_q(name)}: {_q(answer)}" for name, answer in pairs]
        else:
            lines.append(f"    value: {_q(str(value))}")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def _indent(lines: list[str], width: int) -> list[str]:
    return [" " * width + line for line in lines]


def is_role_key(key: str) -> bool:
    """``sheets[<i>]/<layer>/<role>`` (or ``<sheet>/…``; an answers: entry),
    not a gaps: key."""
    return key.count("/") >= _ROLE_KEY_PARTS - 1 and not key.startswith("feeds[")


__all__ = ["FILES_SUFFIX", "TEMPLATE_NAME", "TemplateItem", "file_pairs", "flatten_inputs",
           "is_role_key", "read_template", "write_applied_answers",
           "write_answers_template"]
