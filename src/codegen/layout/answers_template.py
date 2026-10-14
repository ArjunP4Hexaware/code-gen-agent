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
    key: str                       # a gaps: key, or <sheet>/<layer>/<role>
    reason: str
    candidates: list[str] = field(default_factory=list)
    section: str = "gaps"          # gaps | answers | inputs (non-blocking, INPUT_NEEDED)


def _q(value: str) -> str:
    """A YAML scalar: JSON strings are valid YAML double-quoted scalars."""
    return json.dumps(value, ensure_ascii=False)


def _answers_entry(item: TemplateItem) -> list[str]:
    from codegen.layout.profile import BAND_LAYER_ROLE, BAND_REF_RE

    sheet, layer, role = item.key.rsplit("/", 2) if item.key.count("/") >= 2 else (
        item.key, "", "")
    lines = [f"  - sheet: {_q(sheet)}", f"    layer: {_q(layer)}", f"    role: {_q(role)}"]
    if role == BAND_LAYER_ROLE and BAND_REF_RE.match(layer):
        lines.append('    value: ""                    # source | stage | standard')
    else:
        lines.append('    column: ""                   # header text | 1-based index | letter')
    lines.append(f"    question: {_q(item.reason)}")
    lines.append(f"    candidates: {json.dumps(item.candidates, ensure_ascii=False)}")
    return lines


def _gaps_entry(item: TemplateItem) -> list[str]:
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
                                  [str(c) for c in entry.get("candidates") or []], "answers"))
    for section in ("gaps", "inputs"):
        for key, entry in (raw.get(section) or {}).items():
            entry = entry if isinstance(entry, dict) else {}
            items.append(TemplateItem(str(key), str(entry.get("question") or ""),
                                      [str(c) for c in entry.get("candidates") or []], section))
    return items


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
    lines = [f"{_HEADER} — {len(ordered) - len(inputs)} open question(s), "
             f"{len(inputs)} input(s) needed, written by {stage}.",
             "# Fill each empty value / column, then rerun the run's stages with",
             "#   --answers <this file>   (layout, extract-sttm and generate read it).",
             "# An entry left empty is skipped: its question stays open.",
             "# `question` and `candidates` are for reading only.",
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
        lines.append("inputs:")
        for item in inputs:
            lines += _gaps_entry(item)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return path


def is_role_key(key: str) -> bool:
    """``<sheet>/<layer>/<role>`` (an answers: entry), not a gaps: key."""
    return key.count("/") >= _ROLE_KEY_PARTS - 1 and not key.startswith("feeds[")


__all__ = ["TEMPLATE_NAME", "TemplateItem", "is_role_key", "read_template",
           "write_answers_template"]
