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

from codegen.config import is_placeholder

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
    # post59: a defaulted input's three-way choice (codegen.input_choices) —
    # the options, the proposal (never applied until chosen) and its template;
    # ``tokens`` = the placeholder values the App's live preview renders with
    options: tuple[str, ...] = ()
    proposed: str = ""
    template: str = ""
    tokens: tuple[tuple[str, str], ...] = ()
    # post61: ``profile_default`` = the profile's value was written (``applied``):
    # shown as changeable, NOT an open input (a NOTE line, not INPUT_NEEDED)
    kind: str = ""
    applied: str = ""

    @property
    def is_open(self) -> bool:
        return not self.applied

    def as_dict(self) -> dict:
        out = {"key": self.key, "question": self.question, "feed": self.feed,
               "scope": self.scope}
        if self.kind:
            out["kind"] = self.kind
        if self.applied:
            out["applied"] = self.applied
        if self.options:
            from codegen.input_choices import PLACEHOLDER_LABEL, is_placeholder_template

            out.update(options=list(self.options), proposed=self.proposed,
                       template=self.template, tokens=dict(self.tokens),
                       placeholder=(PLACEHOLDER_LABEL if is_placeholder_template(self.template)
                                    else ""))
        return out


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
    """The run's IIG template (None: no owed cells apply). post68: one input
    set whatever the output mode — a notebook run owes, asks and applies the
    same inputs as a framework run (``output_mode`` is kept for the callers)."""
    del output_mode
    return config.metadata.templates.get(iig_template or config.metadata.template)


def owed_inputs(spec, config, *, index: int | str | None = None, faq, output_mode=None,
                iig_template: str | None = None, resolved=None,
                profile=None) -> list[OwedInput]:
    """The FEED-level IIG cells of ``spec`` the workbook is written without
    (feed-scoped owed_cells the FAQ / answers leave unanswered) — a template
    that names owed cells (post68: any output mode). post59: ``resolved``
    (codegen.input_choices.resolve_feed) adds each defaulted input's proposal
    and its options."""
    from codegen.metadata_template import owed_questions

    tpl = _template(config, output_mode, iig_template)
    if tpl is None or not tpl.owed_cells:
        return []
    by_key = {r.key: r for r in resolved or []}
    out = []
    for name, question in owed_questions(tpl, faq, _default_tokens(spec), scope=FEED):
        item = by_key.get(name)
        out.append(_with_choice(OwedInput(feed_key(spec.feed_id, name), question,
                                          spec.feed_id), item, spec, profile, tpl, faq))
    # post70: TGT_PRIMARY_KEY proposed from an explicit key signal, not chosen
    out += [_with_choice(OwedInput(feed_key(spec.feed_id, r.key), KEY_QUESTION, spec.feed_id),
                         r, spec, profile, tpl, faq)
            for r in resolved or [] if r.key == "primary_key" and r.source == "blank"
            and not r.chosen and r.proposal.value]
    # post61: the feed's profile defaults written (notebook names, the
    # SRC_FILE_NAME style) — shown as changeable, not open
    out += [_with_choice(OwedInput(feed_key(spec.feed_id, r.key), _PROFILE_QUESTIONS.get(
        r.key.split(".", 1)[0], r.key), spec.feed_id), r, spec, profile, tpl, faq)
        for r in resolved or [] if r.applied and not _is_run_key(r.key, tpl)]
    return out


KEY_QUESTION = "the detail table's key (TGT_PRIMARY_KEY)"

# post61: what a feed-level profile default is (its NOTE line / the panel)
_PROFILE_QUESTIONS = {
    "notebook_name": "the notebook name (DATABRICKS_NOTEBOOK_NAME) of this leg",
    "pipeline_name": "the pipeline name (PIPELINE_NAME) of this flow — from the naming "
                     "convention (pipeline_name_autoset)",
    "src_file_name_style": "the ADLS SRC_FILE_NAME style (pattern | prefix_star | "
                           "prefix_middle)",
}


def _is_run_key(key: str, tpl) -> bool:
    from codegen import input_choices as ic

    return any(d.key == key and d.scope == RUN for d in ic.defaulted_inputs(tpl))


def _with_choice(owed: OwedInput, item, spec, profile, tpl, faq) -> OwedInput:
    """``owed`` carrying ``item``'s proposal and options (post59)."""
    if item is None:
        return owed
    from dataclasses import replace

    from codegen import input_choices as choices

    options = tuple(o for o in choices.CHOICES
                    if not (o == "leave_blank" and item.key in ("email_statuses",
                                                                choices.SRC_FILE_NAME_STYLE)))
    tokens: dict[str, str] = {}
    if spec is not None and profile is not None:
        tokens = choices.feed_tokens(spec, tpl, faq)
        flow = item.key.split(".", 1)[1] if item.key.startswith(choices.PIPELINE) else ""
        if flow:
            tokens = choices.flow_tokens(tokens, spec, profile, flow)
    return replace(owed, question=f"{owed.question} — {choices.proposal_text(item)}",
                   options=options, proposed=item.proposal.value,
                   template=item.proposal.template, tokens=tuple(sorted(tokens.items())),
                   kind=item.kind, applied=item.value if item.applied else "")


def run_owed_inputs(config, inputs: dict[str, str] | None, *, output_mode=None,
                    iig_template: str | None = None, choices=None) -> list[OwedInput]:
    """The RUN-level owed cells (``scope: run``) the answers file's
    ``inputs.run`` leaves unanswered — one item for the whole run. post59: a
    run-level choice (``choices``, codegen.input_choices) answers it too; a
    defaulted one carries its options and its proposal's template."""
    from codegen import input_choices as ic
    from codegen.metadata_template import owed_questions

    tpl = _template(config, output_mode, iig_template)
    if tpl is None or not tpl.owed_cells:
        return []
    answered = {key for key, value in (inputs or {}).items() if str(value).strip()}
    answered |= set(choices or {})
    defaulted = {d.key: d for d in ic.defaulted_inputs(tpl) if d.scope == RUN}

    def offered(name: str, question: str) -> OwedInput:
        item = defaulted.get(name)
        if item is None or (item.rule.default and is_placeholder(str(item.rule.default))):
            return OwedInput(run_key(name), question, "", RUN, kind=item.kind if item else "")
        options = tuple(o for o in ic.CHOICES if not (item.statuses and o == "leave_blank"))
        template = str(getattr(item.rule, "default", "") or "")
        return OwedInput(run_key(name), f"{question} — {ic.HOW}", "", RUN, options=options,
                         template=template, kind=item.kind)

    owed = owed_questions(tpl, None, scope=RUN)
    items = [offered(name, question) for name, question in owed
             if run_key(name) not in answered]
    # post61: a run-level profile default (EMAIL_TO from the overlay) is written —
    # shown as changeable, not open
    owed_names = {name for name, _q in owed}
    for item in defaulted.values():
        if (item.kind != ic.PROFILE_DEFAULT or item.statuses or item.name in owed_names
                or run_key(item.key) in answered or not item.rule.default):
            continue
        value = str(item.rule.default)
        items.append(OwedInput(
            run_key(item.key), f"{item.rule.question} — profile default applied: {value!r} "
            f"({item.rule.default_share or 'the conventions profile'}) — {ic.HOW_PROFILE}",
            "", RUN, options=ic.CHOICES, proposed=value, template=value,
            kind=ic.PROFILE_DEFAULT, applied=value))
    rule = tpl.email_status_input
    status_item = defaulted.get(rule.faq) if rule is not None else None
    if (rule is not None and run_key(rule.faq) not in answered and status_item is not None
            and status_item.kind == ic.PROFILE_DEFAULT):
        # post61: the profile's status set (email_status_default, else every
        # template row) is written — shown as changeable, not open
        from codegen.metadata_template import _pick_statuses, email_status_default_label

        statuses = [str(r.get("STATUS") or "") for r in
                    tpl.template_rows.get("EMAIL_TEMPLATE_CONFIG") or []]
        written = _pick_statuses(statuses, tpl.email_status_default) or statuses
        label = email_status_default_label(tpl)
        items.append(OwedInput(
            run_key(rule.faq), f"{rule.question} — profile default applied: "
            f"{', '.join(written)} ({label}) — {ic.HOW_PROFILE}", "", RUN,
            options=("use_default", "naming_standard"), proposed=", ".join(written),
            template=label, kind=ic.PROFILE_DEFAULT, applied=", ".join(written)))
    elif rule is not None and run_key(rule.faq) not in answered:
        # 2026-10-14 (framework owner): the email status set, default all four;
        # 2026-10-15: or the overlay's email_status_default. post59: proposed —
        # unanswered, every template status row is written
        from codegen.metadata_template import _pick_statuses, email_status_default_label

        statuses = [str(r.get("STATUS") or "") for r in
                    tpl.template_rows.get("EMAIL_TEMPLATE_CONFIG") or []]
        proposed = _pick_statuses(statuses, tpl.email_status_default) or statuses
        items.append(OwedInput(
            run_key(rule.faq), f"{rule.question} — every template status written "
            f"({', '.join(statuses)}); proposed {email_status_default_label(tpl)!r}: "
            f"{', '.join(proposed)} — {ic.HOW}", "", RUN,
            options=("use_default", "naming_standard"), proposed=", ".join(proposed),
            template=email_status_default_label(tpl)))
    return items


def environment_inputs(config, *, output_mode=None,
                       iig_template: str | None = None) -> list[OwedInput]:
    """The run's environment inputs: ``run.environment`` when the default was
    assumed, ``run.environment.<key>`` per key the environment leaves unset (a
    custom one: missing; a named one under provider=mock: blank / placeholder).
    Runs whose IIG template has environment cells (post68: any output mode)."""
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

    if not item.is_open:
        # post61: a profile default written — informational, still changeable
        where = "inputs.run" if item.scope == RUN else f"inputs.feeds.{item.feed}"
        return answer_line("NOTE", item.key, f"{item.question} (profile default, not an open "
                                             f"input; to change it: {where})")
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
    needed = sum(1 for i in items if i.is_open)
    applied = len(items) - needed
    return [f"{'NOTE':<15}run inputs — {needed} run-level input(s) needed, once for the "
            "whole run (answers file inputs.run)"
            + (f"; {applied} profile default(s) applied, changeable" if applied else "") + ":",
            *(input_line(i) for i in items)]


def template_items(items: list[OwedInput]) -> list:
    from codegen.layout.answers_template import TemplateItem

    return [TemplateItem(i.key, i.question if i.scope == RUN else f"{i.question} (feed {i.feed})",
                         [], INPUTS_SECTION, options=list(i.options), proposed=i.proposed,
                         proposed_template=i.template, applied=i.applied) for i in items]


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
