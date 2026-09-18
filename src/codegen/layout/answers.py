"""The answers file and the unresolved-headers report (M8.3) — the layout
dialog for a terminal / a notebook, where no UI can ask.

``answers.yaml`` places unresolved roles by hand. Each entry names a
(document, sheet, role) and the column that carries it, as the header TEXT
(compared in ``normalize`` form) or a 1-based index / column letter:

    answers:
      - document: sttm                 # sttm | vdd
        workbook: STTM_feed.xlsx       # optional: only for this file name
        sheet: "Mapping - Daily File"  # as written in the workbook
        layer: stage                   # optional when (sheet, role) is unambiguous
        role: table
        column: "Target Table Name"    # header text | 3 | "C"
    gaps:                              # choice / layer questions, by question key
      "feeds[0].file_format": {value: "Delimited"}
    pairing:                           # an undecided content pairing
      STTM_feed.xlsx: {frd: FRD_feed.docx, vdd: VDD_feed.xlsx}

Answers only ever address OPEN questions, carry ``source=user`` through the
same merge + validation the dialog's answers take, and an entry that matches
no open question is reported, never applied silently elsewhere.

``unresolved_report`` writes ``unresolved_headers.md``: for each unresolved
role the sheet name as written, the header-row texts and the candidate
columns. STRUCTURAL LABELS ONLY — no data row, no cell value — so the file
can leave the workspace and the strings be added to the synonym tables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from openpyxl.utils import column_index_from_string

from codegen.layout.discover import normalize


class AnswersFileError(ValueError):
    """The answers file is malformed; the message names the entry."""


@dataclass
class AnswersFile:
    entries: list[dict] = field(default_factory=list)
    gaps: dict[str, dict] = field(default_factory=dict)
    pairing: dict[str, dict] = field(default_factory=dict)


_ENTRY_KEYS = {"document", "workbook", "sheet", "layer", "role", "column"}


def load_answers(path: Path) -> AnswersFile:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict) or set(raw) - {"answers", "gaps", "pairing"}:
        raise AnswersFileError(
            f"{path}: expected a mapping with `answers`, `gaps` and / or `pairing`")
    entries = raw.get("answers") or []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict) or set(entry) - _ENTRY_KEYS:
            raise AnswersFileError(f"{path}: answers[{index}] has unknown keys "
                                   f"{sorted(set(entry) - _ENTRY_KEYS)}")
        missing = {"sheet", "role", "column"} - set(entry)
        if missing:
            raise AnswersFileError(f"{path}: answers[{index}] is missing {sorted(missing)}")
        if entry.get("document", "sttm") not in ("sttm", "vdd"):
            raise AnswersFileError(f"{path}: answers[{index}].document must be sttm | vdd "
                                   "(FRD cells are placed with `gaps` / in the dialog)")
    gaps = raw.get("gaps") or {}
    for key, value in gaps.items():
        if not isinstance(value, dict) or not isinstance(value.get("value"), str):
            raise AnswersFileError(f"{path}: gaps[{key!r}] must be {{value: <text>, layer?}}")
    pairing = raw.get("pairing") or {}
    for name, value in pairing.items():
        if not isinstance(value, dict) or set(value) - {"frd", "vdd"}:
            raise AnswersFileError(f"{path}: pairing[{name!r}] must be {{frd?, vdd?}}")
    return AnswersFile(list(entries), dict(gaps), dict(pairing))


def _column_of(entry: dict, question) -> int | None:
    """The 1-based column an entry names, among the question's candidates."""
    wanted = entry["column"]
    columns = {int(c["col"]): str(c.get("header") or "") for c in question.candidates
               if "col" in c}
    if isinstance(wanted, int):
        return wanted if wanted >= 1 else None
    text = str(wanted).strip()
    by_header = [col for col, header in columns.items() if normalize(header) == normalize(text)]
    if len(by_header) == 1:
        return by_header[0]
    if len(by_header) > 1:
        raise AnswersFileError(
            f"header {text!r} names {len(by_header)} columns on sheet {question.sheet!r} "
            f"({sorted(by_header)}) — give the column index instead")
    if text.isalpha() and len(text) <= 3:            # a column letter
        return column_index_from_string(text.upper())
    return None


def apply_answers(answers: AnswersFile, questions: list, names: dict[str, str]
                  ) -> tuple[dict, list[str]]:
    """Map the file onto the OPEN ``questions`` → (the resolver's ``answers``
    dict, notes). ``names`` = {"sttm": file name, "vdd": file name} for the
    optional ``workbook`` filter."""
    out: dict = {"sttm": {}, "frd": {}, "vdd": {}, "gaps": {}}
    notes: list[str] = []
    open_role = [q for q in questions if q.kind == "role" and q.document in ("sttm", "vdd")]
    for index, entry in enumerate(answers.entries):
        document = entry.get("document", "sttm")
        if entry.get("workbook") and entry["workbook"] != names.get(document):
            continue
        matches = [q for q in open_role
                   if q.document == document and q.sheet == entry["sheet"]
                   and q.role == entry["role"]
                   and entry.get("layer") in (None, q.layer)]
        if not matches:
            notes.append(f"answers[{index}] ({document} {entry['sheet']!r} {entry['role']}) "
                         "matches no open question — already resolved, or the sheet / role "
                         "name differs")
            continue
        if len(matches) > 1:
            raise AnswersFileError(
                f"answers[{index}]: role {entry['role']!r} is open in several layers of sheet "
                f"{entry['sheet']!r} ({sorted(str(q.layer) for q in matches)}) — add `layer:`")
        column = _column_of(entry, matches[0])
        if column is None:
            raise AnswersFileError(
                f"answers[{index}]: column {entry['column']!r} is neither a candidate header "
                f"of sheet {entry['sheet']!r}, an index nor a column letter")
        out[document][matches[0].key] = column
    open_keys = {q.key for q in questions if q.kind in ("choice", "layer")}
    for key, value in answers.gaps.items():
        if key in open_keys:
            out["gaps"][key] = {"value": value["value"], "layer": value.get("layer"),
                                "source": "user"}
        else:
            notes.append(f"gaps[{key!r}] matches no open question")
    return out, notes


def unresolved_report(questions: list, names: dict[str, str]) -> str:
    """``unresolved_headers.md`` — structural labels only (module docstring)."""
    lines = ["# Unresolved layout roles", "",
             "Structural labels only: sheet names, header-row texts and candidate columns — "
             "no data row and no cell value. Add the header strings to the matching synonym "
             "table (`extractor.discovery` / `extractor.vdd` / `extractor.frd` in a config "
             "overlay), or place the role with an answers file "
             "(`codegen layout --answers answers.yaml`).", ""]
    if not questions:
        return "\n".join([*lines, "Nothing is unresolved.", ""])
    for question in questions:
        document = names.get(question.document, question.document)
        lines.append(f"## {question.document.upper()} · {document}")
        lines.append("")
        lines.append(f"- question key: `{question.key}`")
        if question.sheet is not None:
            lines.append(f"- sheet (as written): `{question.sheet}`")
        if question.layer:
            lines.append(f"- layer / band: `{question.layer}`")
        lines.append(f"- role: `{question.role}` — {question.title or question.reason}")
        if question.kind != "role":
            # choice / layer questions carry document VALUES: name the question only.
            lines.append(f"- kind: `{question.kind}` — answer under `gaps:` with the question key")
            lines.append("")
            continue
        if question.header:
            lines.append("- header row: " + " | ".join(f"`{h}`" for h in question.header))
        labels = [f"`{c.get('col', c.get('table'))}: {c.get('header', c.get('label', ''))}`"
                  for c in question.candidates]
        if labels:
            lines.append("- candidate columns: " + ", ".join(labels))
        lines.append("")
    return "\n".join(lines)
