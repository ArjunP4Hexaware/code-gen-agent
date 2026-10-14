"""Non-blocking owed inputs (2026-10-14, D1 post44).

Two kinds of owed answer line, never mixed:

- ``QUESTION`` / ``UNRESOLVED`` — a BLOCKING gap: the run cannot complete the feed
  without it (exit 3 where the stage holds the feed back). The ACFC harness's
  NEEDS_ANSWERS is triggered by these lines only.
- ``INPUT_NEEDED`` — a value the workbook is written without (the cell stays
  empty), e.g. ACTIVE_START_DATE, the per-RFC go-live date
  (``metadata.templates.<t>.owed_cells``). Exit 0; listed under ``inputs:`` in
  answers_template.yaml; a value given there fills the cell when ``generate``
  reruns with ``--answers``. The App shows them as a non-blocking banner.

Used by the CLI (``codegen generate``) and the App (``status.inputs_needed``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

INPUT_LABEL = "INPUT_NEEDED"
INPUTS_SECTION = "inputs"


@dataclass(frozen=True)
class OwedInput:
    key: str          # feeds[<i>].<FAQ companion>, the answers file's inputs: key
    question: str
    feed: str         # the feed_id the cell belongs to

    def as_dict(self) -> dict:
        return {"key": self.key, "question": self.question, "feed": self.feed}


def frd_feed_index(frd_path: Path | None, feed_id: str, config) -> int | str:
    """The feed's position in the FRD contract (the key's feeds[<i>]); its
    feed_id when no FRD feed names it (or the contract cannot be read)."""
    from codegen.resolve.resolver import normalize_feed_name

    try:
        feeds = json.loads(Path(frd_path).read_text(encoding="utf-8")).get("feeds") or []
    except (OSError, TypeError, ValueError):
        return feed_id
    for index, feed in enumerate(feeds):
        name = str(feed.get("feed_name") or "")
        if feed_id in (config.feed_aliases.get(name), normalize_feed_name(name)):
            return index
    return feed_id


def answers_for(inputs: dict[str, str], index: int | str) -> dict[str, str]:
    """The ``inputs:`` values of one feed, by FAQ companion name."""
    prefix = f"feeds[{index}]."
    return {key[len(prefix):]: value for key, value in inputs.items()
            if key.startswith(prefix)}


def owed_inputs(spec, config, *, index: int | str, faq, output_mode=None,
                iig_template: str | None = None) -> list[OwedInput]:
    """The IIG cells of ``spec`` the workbook is written without (owed_cells the
    FAQ / answers leave unanswered) — framework output with a template that
    names owed cells only."""
    from codegen.metadata_template import owed_questions
    from codegen.output_modes import output_parts

    if "framework" not in output_parts(output_mode if output_mode else config.output.mode):
        return []
    tpl = config.metadata.templates.get(iig_template or config.metadata.template)
    if tpl is None or not tpl.owed_cells:
        return []
    return [OwedInput(f"feeds[{index}].{name}", question, spec.feed_id)
            for name, question in owed_questions(tpl, faq)]


def input_line(item: OwedInput) -> str:
    from codegen.cli import answer_line

    return answer_line(INPUT_LABEL, item.key,
                       f"{item.question} (feed {item.feed}; not blocking — the workbook is "
                       "written with the cell empty; give it under inputs: and rerun "
                       "generate --answers)")


def template_items(items: list[OwedInput]) -> list:
    from codegen.layout.answers_template import TemplateItem

    return [TemplateItem(i.key, f"{i.question} (feed {i.feed})", [], INPUTS_SECTION)
            for i in items]


def answers_owed(flags: list[str]) -> tuple[list[str], list[str]]:
    """(blocking questions, inputs needed) a generated feed's gate flags carry:
    a REQUIRED STTM role the run proceeded without (``layout_unresolved:sttm
    <sheet>/<layer>/<role>``) and an owed IIG cell (``iig_owed:<TAB>.<HEADER>``)."""
    from codegen.layout.profile import is_required_role

    questions, inputs = [], []
    for flag in flags:
        if flag.startswith("layout_unresolved:sttm "):
            where = flag[len("layout_unresolved:sttm "):].split(" — ", 1)[0]
            sheet_layer, _sep, role = where.rpartition("/")
            if is_required_role(sheet_layer.rpartition("/")[2], role):
                questions.append(where)
        elif flag.startswith("iig_owed:"):
            inputs.append(flag[len("iig_owed:"):].split(" — ", 1)[0])
    return list(dict.fromkeys(questions)), list(dict.fromkeys(inputs))


def owed_header(flags: list[str]) -> str:
    """The report header line: 'questions: N, inputs needed: M'."""
    questions, inputs = answers_owed(flags)
    line = f"**Answers owed** — questions: {len(questions)}, inputs needed: {len(inputs)}"
    if inputs:
        line += (" (not blocking — the workbook is written with these cells empty: "
                 + ", ".join(inputs) + ")")
    return line


__all__ = ["INPUT_LABEL", "INPUTS_SECTION", "OwedInput", "answers_for", "answers_owed",
           "frd_feed_index", "input_line", "owed_header", "owed_inputs", "template_items"]
