"""Non-blocking owed inputs (2026-10-14, D1 post44).

Two kinds of owed answer line, never mixed:

- ``QUESTION`` / ``UNRESOLVED`` — a BLOCKING gap: the run cannot complete the feed
  without it (exit 3 where the stage holds the feed back). The ACFC harness's
  NEEDS_ANSWERS is triggered by these lines only.
- ``INPUT_NEEDED`` — a value the workbook is written without (the cell stays
  empty, or a named default is written), e.g. ACTIVE_START_DATE, the per-RFC
  go-live date (``metadata.templates.<t>.owed_cells``). Exit 0; listed under
  ``inputs:`` in answers_template.yaml; a value given there fills the cell when
  ``generate`` reruns with ``--answers``. The App shows them as a non-blocking
  banner.

2026-10-14 (post47) — two scopes:

- RUN-level (``run.<name>``): the run's environment (``run.environment``, and
  ``run.environment.<key>`` per key a custom environment leaves unset) and the
  owed cells marked ``scope: run`` (APPLICATION_NAME, EMAIL_TO). Printed ONCE
  per run in one block before any feed, one block at the top of every feed
  report, ``inputs.run`` in the answers file; an answer applies to every feed.
- FEED-level (``feeds.<feed>.<name>``): ACTIVE_START_DATE, the DQ INPUT_PARAMs —
  ``inputs.feeds.<feed>``. The older flat ``feeds[<i>].<name>`` keys still read.

Used by the CLI (``codegen generate``) and the App (``status.inputs_needed``).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

INPUT_LABEL = "INPUT_NEEDED"
INPUTS_SECTION = "inputs"
RUN = "run"
FEED = "feed"
_RUN_KEY_RE = re.compile(r"INPUT_NEEDED (run\.[\w.]+)")
# a feed-level owed NOTE's input name (rule 1: per flow, pipeline_name.<flow>)
_FEED_KEY_RE = re.compile(r"INPUT_NEEDED feeds\.<feed>\.([\w.]+?):")


@dataclass(frozen=True)
class OwedInput:
    key: str          # run.<name> | feeds.<feed>.<name>: the answers file's inputs key
    question: str
    feed: str         # the feed_id the cell belongs to ("" for a run-level input)
    scope: str = FEED

    def as_dict(self) -> dict:
        return {"key": self.key, "question": self.question, "feed": self.feed,
                "scope": self.scope}


def run_key(name: str) -> str:
    return f"{RUN}.{name}"


def feed_key(feed_id: str, name: str) -> str:
    return f"feeds.{feed_id}.{name}"


def frd_feed_index(frd_path: Path | None, feed_id: str, config) -> int | str:
    """The feed's position in the FRD contract (the legacy key's feeds[<i>]);
    its feed_id when no FRD feed names it (or the contract cannot be read)."""
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


def answers_for(inputs: dict[str, str], index: int | str,
                feed_id: str | None = None) -> dict[str, str]:
    """One feed's ``inputs:`` values by FAQ companion name: the run-level answers
    (``run.<name>``, every feed; the environment keys excluded), then the
    feed's own (legacy ``feeds[<i>].<name>``, then ``feeds.<feed>.<name>``)."""
    out = {key[len(RUN) + 1:]: value for key, value in inputs.items()
           if key.startswith(f"{RUN}.") and not key.startswith(f"{RUN}.environment")}
    for prefix in (f"feeds[{index}].", *([f"feeds.{feed_id}."] if feed_id else [])):
        # a per-flow key <faq>.<flow> (rule 1: pipeline_name.file_to_stg) is the
        # FAQ companion <faq>_<flow>
        out.update({key[len(prefix):].replace(".", "_"): value
                    for key, value in inputs.items() if key.startswith(prefix)})
    return out


def _template(config, output_mode, iig_template):
    """The IIG template a framework run fills (None: no owed cells apply)."""
    from codegen.output_modes import output_parts

    if "framework" not in output_parts(output_mode if output_mode else config.output.mode):
        return None
    return config.metadata.templates.get(iig_template or config.metadata.template)


def owed_inputs(spec, config, *, index: int | str | None = None, faq, output_mode=None,
                iig_template: str | None = None) -> list[OwedInput]:
    """The FEED-level IIG cells of ``spec`` the workbook is written without
    (feed-scoped owed_cells the FAQ / answers leave unanswered) — framework
    output with a template that names owed cells only."""
    from codegen.metadata_template import owed_questions

    tpl = _template(config, output_mode, iig_template)
    if tpl is None or not tpl.owed_cells:
        return []
    return [OwedInput(feed_key(spec.feed_id, name), question, spec.feed_id)
            for name, question in owed_questions(tpl, faq, _default_tokens(spec),
                                                 scope=FEED)]


def run_owed_inputs(config, inputs: dict[str, str] | None, *, output_mode=None,
                    iig_template: str | None = None) -> list[OwedInput]:
    """The RUN-level owed cells (``scope: run``) the answers file's
    ``inputs.run`` leaves unanswered — one item for the whole run."""
    from codegen.metadata_template import owed_questions

    tpl = _template(config, output_mode, iig_template)
    if tpl is None or not tpl.owed_cells:
        return []
    answered = {key for key, value in (inputs or {}).items() if str(value).strip()}
    items = [OwedInput(run_key(name), question, "", RUN)
             for name, question in owed_questions(tpl, None, scope=RUN)
             if run_key(name) not in answered]
    rule = tpl.email_status_input
    if rule is not None and run_key(rule.faq) not in answered:
        # 2026-10-14 (framework owner): the email status set, default all four
        statuses = [str(r.get("STATUS") or "") for r in
                    tpl.template_rows.get("EMAIL_TEMPLATE_CONFIG") or []]
        items.append(OwedInput(run_key(rule.faq), f"{rule.question} — written with the "
                               f"default {rule.default or 'all four'!r}: "
                               f"{', '.join(statuses)}", "", RUN))
    return items


def environment_inputs(config, *, output_mode=None,
                       iig_template: str | None = None) -> list[OwedInput]:
    """The run's environment inputs: ``run.environment`` when the default was
    assumed, ``run.environment.<key>`` per key the environment leaves unset (a
    custom one: missing; a named one under provider=mock: blank / placeholder).
    Only framework runs whose IIG template has environment cells."""
    from codegen import environments as envs

    tpl = _template(config, output_mode, iig_template)
    if tpl is None or not tpl.environment_cells:
        return []
    env = envs.run_environment(config)
    if env is None:
        return []
    # post47b: a named environment's unset keys too (provider=mock; live failed)
    assumed = ([OwedInput(envs.INPUT_KEY, envs.assumed_question(config, env), "", RUN)]
               if env.source == "default" else [])
    return [*assumed, *(OwedInput(key, question, "", RUN)
                        for key, question in envs.unset_items(config))]


def _default_tokens(spec) -> dict:
    """The tokens an owed cell's default may name (D1 post45: {source} — the
    feed's SOURCE, APPLICATION_NAME's default)."""
    from codegen.metadata_sheet import _feed_from_spec
    from codegen.metadata_template import _source_value

    return {"source": _source_value(_feed_from_spec(spec))}


def input_line(item: OwedInput) -> str:
    from codegen.cli import answer_line

    if item.scope == RUN:
        return answer_line(INPUT_LABEL, item.key,
                           f"{item.question} (run-level, once for every feed; not blocking — "
                           "give it under inputs.run and rerun generate --answers)")
    return answer_line(INPUT_LABEL, item.key,
                       f"{item.question} (feed {item.feed}; not blocking — the workbook is "
                       "written without it, the cell empty or with the default named; give "
                       f"it under inputs.feeds.{item.feed} and rerun generate --answers)")


def run_block_lines(items: list[OwedInput]) -> list[str]:
    """The console's run-level block: one header line, then one INPUT_NEEDED
    line per run-level input (nothing when there is none)."""
    if not items:
        return []
    return [f"{'NOTE':<15}run inputs — {len(items)} run-level input(s) needed, once for the "
            "whole run (answers file inputs.run):", *(input_line(i) for i in items)]


def template_items(items: list[OwedInput]) -> list:
    from codegen.layout.answers_template import TemplateItem

    return [TemplateItem(i.key, i.question if i.scope == RUN else f"{i.question} (feed {i.feed})",
                         [], INPUTS_SECTION) for i in items]


def answers_owed(flags: list[str]) -> tuple[list[str], list[str]]:
    """(blocking questions, FEED-level inputs needed) a generated feed's gate
    flags carry: a REQUIRED STTM role the run proceeded without
    (``layout_unresolved:sttm <sheet>/<layer>/<role>``) and an owed feed-level
    IIG cell (``iig_owed:<TAB>.<HEADER>``). Run-level inputs: ``run_inputs_owed``."""
    from codegen.layout.profile import is_required_role

    questions, inputs = [], []
    for flag in flags:
        if flag.startswith("layout_unresolved:sttm "):
            where = flag[len("layout_unresolved:sttm "):].split(" — ", 1)[0]
            sheet_layer, _sep, role = where.rpartition("/")
            if is_required_role(sheet_layer.rpartition("/")[2], role):
                questions.append(where)
        elif flag.startswith("iig_owed:"):
            # by INPUT name (a per-flow cell on two sheets is one input per flow)
            match = _FEED_KEY_RE.search(flag)
            inputs.append(match.group(1) if match
                          else flag.split(":", 1)[1].split(" — ", 1)[0])
        elif flag.startswith("lob_unkeyed:"):
            # 2026-10-14 (D1 pair_12): the feed's ONE file-to-LOB question
            questions.append(flag[len("lob_unkeyed:"):].split(" — ", 1)[0])
    return list(dict.fromkeys(questions)), list(dict.fromkeys(inputs))


def run_inputs_owed(flags: list[str]) -> list[str]:
    """The RUN-level input keys a feed's flags carry: the environment assumed
    (``run.environment``), a custom environment's unset keys
    (``run.environment.<key>``), a run-scoped owed cell (``run.<name>``)."""
    keys = []
    for flag in flags:
        if flag.startswith(("environment_assumed:", "environment_unset:")):
            keys.append(flag.split(":", 1)[1].split(" — ", 1)[0])
        elif flag.startswith("iig_owed_run:"):
            match = _RUN_KEY_RE.search(flag)
            if match:
                keys.append(match.group(1).rstrip("."))
    return list(dict.fromkeys(keys))


def run_questions_owed(flags: list[str]) -> list[str]:
    """The RUN-level QUESTION keys (2026-10-15): a required environment value
    the run's environment leaves unset (``run.environment.<key>``; exit 3)."""
    return list(dict.fromkeys(flag.split(":", 1)[1].split(" — ", 1)[0] for flag in flags
                              if flag.startswith("environment_required:")))


def run_block(flags: list[str]) -> list[str]:
    """The report's run-level block (top of every feed report of the run):
    the run's blocking questions, then its inputs needed; nothing when the run
    owes neither."""
    questions, keys = run_questions_owed(flags), run_inputs_owed(flags)
    lines = []
    if questions:
        lines += [f"**Run questions: {len(questions)}** — required environment values, once "
                  "for the whole run (BLOCKING: exit 3, NEEDS_ANSWERS; answers file "
                  "`inputs.run`, or the environment profile):",
                  *(f"- `{key}`" for key in questions), ""]
    if keys:
        lines += [f"**Run inputs needed: {len(keys)}** — once for the whole run, shared by every "
                  "feed (not blocking; answers file `inputs.run`):",
                  *(f"- `{key}`" for key in keys), ""]
    return lines


def owed_header(flags: list[str]) -> str:
    """The report header line: 'questions: N, inputs needed: M' (feed-level)."""
    questions, inputs = answers_owed(flags)
    line = f"**Answers owed** — questions: {len(questions)}, inputs needed: {len(inputs)}"
    if inputs:
        line += (" (feed-level, not blocking — the workbook is written without them, a cell "
                 "empty or a default assumed: " + ", ".join(inputs) + ")")
    return line


__all__ = ["FEED", "INPUT_LABEL", "INPUTS_SECTION", "RUN", "OwedInput", "answers_for",
           "answers_owed", "environment_inputs", "feed_key", "frd_feed_index", "input_line",
           "owed_header", "owed_inputs", "run_block", "run_block_lines", "run_inputs_owed",
           "run_key", "run_owed_inputs", "template_items"]
