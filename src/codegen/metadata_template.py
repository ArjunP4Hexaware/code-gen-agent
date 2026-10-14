"""IIG template row builders (M4): rows for a `metadata.templates` layout
other than the default ``iig_v1`` (which stays ``demo.metadata_sheet`` +
``codegen.metadata_sheet``'s builders, byte for byte).

Every cell is either transcribed from an input (STTM / FRD / FAQ, badged
accordingly) or a framework-vocabulary constant / template row the config
carries WITH its citation (badged ``synthetic``); everything else is left
blank and flagged (one ``iig_blank:<TAB>: <HEADER>, …`` flag per sheet) —
never guessed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from codegen.config import Config, MetadataTemplateConfig, is_placeholder
from codegen.contracts.frd import FrdFeed
from codegen.contracts.resolved import ResolvedFeedSpec, ResolvedTable, SegmentSpec
from codegen.contracts.sttm import SttmField
from codegen.contracts.tables import FeedFile
from codegen.gate.derivations import (
    join_location,
    location_scheme,
    normalise_path,
    path_normalised_flag,
)

_TEMPLATE_TOOLTIP = "template constant — {citation}"
_PATH_TOOLTIP = ("synthetic path shape from the template ({citation}); the real "
                 "container/path are assigned at deployment")


def _cell(value, badge: str, tooltip: str | None = None) -> dict:
    from codegen.metadata_sheet import _cell as base_cell

    return base_cell(value, badge, tooltip)


def _const(tpl: MetadataTemplateConfig, tab: str, header: str) -> dict | None:
    value = tpl.constants.get(tab, {}).get(header)
    if value is None:
        return None
    citation = tpl.constant_citations.get(tab, {}).get(header) or tpl.citation
    cell = _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(citation=citation))
    from codegen.environments import env_note

    note = env_note(tpl, tab, header, value)       # 2026-10-14: the run's environment
    if note is not None:
        if not str(value or "").strip():
            cell = _cell("", "needs_template", f"open — {note}")
        cell["badge_entry"]["note"] = note
    return cell


_DERIVED_TOKEN_RE = re.compile(r"\{(\w+)\}")


def _derive(tpl: MetadataTemplateConfig, tab: str, cells: dict, context: dict) -> dict:
    """``derived_cells`` (2026-10-13, the corpus fill rate): each configured
    shape fills its column where the builder left it blank — the tokens from
    ``context``, a NOTE per column (``iig_derived:<TAB>.<HEADER>``, the same
    text on every row so it is said once). A token without a value leaves the
    cell open: nothing is guessed."""
    for header, shape in tpl.derived_cells.get(tab, {}).items():
        current = cells.get(header)
        if current is not None and str(current["value"] if current["value"] is not None
                                       else "").strip():
            continue
        tokens = _DERIVED_TOKEN_RE.findall(shape)
        if any(not str(context.get(t) or "").strip() for t in tokens):
            continue
        value = _DERIVED_TOKEN_RE.sub(lambda m: str(context[m.group(1)]).strip(), shape)
        citation = tpl.derived_citations.get(tab, {}).get(header) or tpl.citation
        what = ("the IIG corpus's dominant constant" if not tokens else
                "; ".join(f"{{{t}}} = {str(context[t]).strip()!r}" for t in tokens))
        cell = _cell(value, "synthetic", f"{shape!r} — {what} ({citation})")
        cell["badge_entry"]["note"] = (
            f"iig_derived:{tab}.{header} — {shape!r} "
            f"({'a constant' if not tokens else 'from ' + ', '.join(tokens)}): the IIG "
            f"corpus fills this column in >90% of rows ({citation})")
        cells[header] = cell
    return cells


def _source_value(feed: FrdFeed) -> str:
    """The {source} token: the SOURCE cell's value; '' when the FRD states no
    source (the docx reader's 'unstated' is a placeholder, never a name)."""
    value = str(_source_cell(feed)["value"] or "").strip()
    return "" if value.lower() == "unstated" else value


_OPEN_OFFER_TOOLTIP = ("open — no input states it; candidate, NOT written (confirm before "
                       "filling): {offer}")


def _with_constants(tpl: MetadataTemplateConfig, tab: str, cells: dict,
                    context: dict | None = None, faq=None) -> dict:
    for header in tpl.constants.get(tab, {}):
        if header not in cells:
            cells[header] = _const(tpl, tab, header)
    # An offered candidate stays a tooltip on the OPEN cell (config open_offers).
    for header, offer in tpl.open_offers.get(tab, {}).items():
        if header not in cells:
            cells[header] = _cell("", "needs_template", _OPEN_OFFER_TOOLTIP.format(offer=offer))
    for header, why in tpl.deliberate_blanks.get(tab, {}).items():
        if header not in cells or cells[header] is None:
            cell = _cell("", "synthetic", f"decided blank — {why}")
            cell["badge_entry"]["deliberate_blank"] = True
            cells[header] = cell
    _corpus(tpl, tab, cells, context or {})
    _owed(tpl, tab, cells, faq, context or {})
    return _placeholders(tab, _pending(tpl, tab, cells))


# A corpus value never replaces what an input states (STTM / FRD / FAQ).
_CORPUS_OVER = frozenset({"synthetic", "from_standards", "needs_template"})
_PATTERNS_REPORT = "tools/iig_fill_rate.py --patterns, D1 post44"


def _corpus_key(values: dict[str, str], key: str) -> str | None:
    """The entry for ``key`` (case-insensitive), else the "*" fallback."""
    found = next((v for k, v in values.items() if k.lower() == key.lower()), None)
    return found if found is not None else values.get("*")


def _corpus(tpl: MetadataTemplateConfig, tab: str, cells: dict, context: dict) -> None:
    """``corpus_cells`` (2026-10-14, D1 post44): the corpus patterns report's
    value — a constant, or by the row's flow / status / frequency (no entry for
    the row's key = decided blank); tokens from ``context`` as derived_cells;
    a ``<<D1:...>>`` placeholder leaves the cell open. Each with a NOTE naming
    the corpus share (iig_corpus / iig_d1_placeholder:<TAB>.<HEADER>)."""
    for header, rule in tpl.corpus_cells.get(tab, {}).items():
        current = cells.get(header)
        if (current is not None and current["badge_entry"]["badge"] not in _CORPUS_OVER
                and str(current["value"] if current["value"] is not None else "").strip()):
            continue
        key = str(context.get(rule.by) or "").strip() if rule.by else ""
        where = f" ({rule.by} {key!r})" if rule.by else ""
        shape = rule.value if rule.by is None else _corpus_key(rule.values, key)
        if shape is None:
            filled = ", ".join(k for k in rule.values if k != "*")
            cell = _cell("", "synthetic", f"decided blank — the IIG corpus fills {header} only "
                                          f"for {rule.by} {filled} ({rule.share})")
            cell["badge_entry"]["deliberate_blank"] = True
            cell["badge_entry"]["note"] = (
                f"iig_corpus:{tab}.{header} — blank for {rule.by} {key!r}: the corpus fills it "
                f"for {filled} only ({rule.share}; {_PATTERNS_REPORT})")
            cells[header] = cell
            continue
        share = _corpus_key(rule.shares, key) if rule.by and rule.shares else None
        share = share or rule.share
        tokens_map = {**tpl.corpus_tokens, **context}
        tokens = _DERIVED_TOKEN_RE.findall(shape)
        filled = shape
        if not is_placeholder(shape):
            if any(not str(tokens_map.get(t) or "").strip() for t in tokens):
                continue
            filled = _DERIVED_TOKEN_RE.sub(
                lambda m, values=tokens_map: str(values[m.group(1)]).strip(), shape)
        if is_placeholder(filled):
            # a value the corpus still scrubs (a G-token): open until the D1 overlay
            todo = rule.todo or "the D1 overlay sets it"
            shown = shape if shape == filled else f"{shape} = {filled}"
            cell = _cell("", "needs_template", f"open — {shown}: {todo} (corpus: {share})")
            cell["badge_entry"]["note"] = (
                f"iig_d1_placeholder:{tab}.{header} — {shown}{where} left blank: TODO {todo} "
                f"(corpus: {share})")
            cells[header] = cell
            continue
        cell = _cell(filled, "synthetic", f"IIG corpus{where}: {shape!r} — {share} "
                                          f"({_PATTERNS_REPORT})")
        note = f"iig_corpus:{tab}.{header} — {shape!r}{where}: {share} ({_PATTERNS_REPORT})"
        offer = _corpus_offer(rule, tokens_map)
        if offer:
            note += offer
        cell["badge_entry"]["note"] = note
        cells[header] = cell


def _corpus_offer(rule, tokens_map: dict) -> str:
    """The NOTE's alternative shape (never written) for a row whose context
    sets ``offer_when`` — e.g. the per-LOB pipeline description."""
    if not rule.offer or not rule.offer_when or not tokens_map.get(rule.offer_when):
        return ""
    offered = _DERIVED_TOKEN_RE.sub(
        lambda m: str(tokens_map.get(m.group(1)) or f"<{m.group(1)}>").strip(), rule.offer)
    return (f"; alternative for a feed that fans out per LOB: {offered!r}"
            + (f" ({rule.offer_share})" if rule.offer_share else "") + " — not written")


def _cell_text(cell: dict | None) -> str:
    return str(cell["value"] if cell is not None and cell["value"] is not None else "")


def _owed(tpl: MetadataTemplateConfig, tab: str, cells: dict, faq,
          context: dict | None = None) -> None:
    """``owed_cells``: the FAQ companion's answer (an answers-file answer rides
    in as one); else the rule's ``default`` written (tokens from ``context``; a
    placeholder leaves it open) or the cell open — a NOTE (iig_owed) either
    way, and the CLI prints the INPUT_NEEDED line. A rule with ``when`` applies
    only to the rows whose cells hold those values."""
    for key, rule in tpl.owed_cells.get(tab, {}).items():
        header = rule.header or key
        if any(_cell_text(cells.get(column)).strip() != value
               for column, value in rule.when.items()):
            continue
        answer = getattr(faq, rule.faq, None) if faq is not None else None
        if answer is not None and answer.source != "unknown" and str(answer.value).strip():
            from codegen.metadata_sheet import _faq_cell as base

            cells[header] = base(answer, f"{rule.question} — answered")
            continue
        how = (f"INPUT_NEEDED feeds[<i>].{rule.faq}: answer under inputs: with generate "
               f"--answers, or the load-pattern FAQ {rule.faq}")
        default = _owed_default(rule, {**tpl.corpus_tokens, **(context or {})})
        if default and not is_placeholder(default):
            share = rule.default_share or "default"
            cell = _cell(default, "synthetic",
                         f"default {default!r} ({share}) — owed: {rule.question}")
            cell["badge_entry"]["note"] = (
                f"iig_owed:{tab}.{key} — {rule.question}; written with the default "
                f"{rule.default!r} = {default!r} ({rule.default_share or 'default'}) ({how})")
            cells[header] = cell
            continue
        shown = f" (default {rule.default!r}, a value the D1 overlay sets)" if default else ""
        cell = _cell("", "needs_template", f"owed: {rule.question}{shown}")
        cell["badge_entry"]["note"] = f"iig_owed:{tab}.{key} — {rule.question}{shown} ({how})"
        cells[header] = cell


def _owed_default(rule, tokens: dict) -> str:
    """The owed rule's default with its tokens filled ('' when a token has no
    value; a placeholder stays a placeholder)."""
    if not rule.default:
        return ""
    if any(not str(tokens.get(t) or "").strip() for t in _DERIVED_TOKEN_RE.findall(rule.default)):
        return ""
    return _DERIVED_TOKEN_RE.sub(lambda m: str(tokens[m.group(1)]).strip(), rule.default)


def owed_questions(tpl: MetadataTemplateConfig, faq,
                   tokens: dict | None = None) -> list[tuple[str, str]]:
    """(FAQ companion, question) of every owed cell the FAQ leaves unanswered;
    a rule with a default says which value was written (``tokens`` fill it)."""
    out: list[tuple[str, str]] = []
    for rules in tpl.owed_cells.values():
        for rule in rules.values():
            answer = getattr(faq, rule.faq, None) if faq is not None else None
            if answer is not None and answer.source != "unknown" and str(answer.value).strip():
                continue
            question = rule.question
            if rule.default:
                value = _owed_default(rule, {**tpl.corpus_tokens, **(tokens or {})})
                question += (f" — written with the default {value!r}"
                             if value and not is_placeholder(value) else
                             f" — default {rule.default!r} (set on D1)")
            if rule.faq not in [name for name, _q in out]:
                out.append((rule.faq, question))
    return out


def _placeholder_owner(value: str) -> str:
    """'the D1 overlay' for <<D1:...>>, 'the QA environment' for <<QA:...>>."""
    match = re.search(r"<<([A-Z][A-Z0-9_]*):", value)
    env = match.group(1) if match else "D1"
    return "the D1 overlay" if env == "D1" else f"the {env} environment's values"


def _placeholders(tab: str, cells: dict) -> dict:
    """Any cell still carrying a ``<<ENV:...>>`` placeholder (a constant, a
    template row, an environment value) is open with a NOTE — the placeholder
    never reaches a cell."""
    for header, cell in cells.items():
        if cell is not None and is_placeholder(cell["value"]):
            owner = _placeholder_owner(str(cell["value"]))
            open_cell = _cell("", "needs_template", f"open — {cell['value']}: {owner} sets it")
            kind = "iig_d1_placeholder" if owner == "the D1 overlay" else "iig_env_placeholder"
            open_cell["badge_entry"]["note"] = (
                f"{kind}:{tab}.{header} — {cell['value']} left blank: TODO {owner} sets it")
            cells[header] = open_cell
    return cells


def _pending(tpl: MetadataTemplateConfig, tab: str, cells: dict) -> dict:
    """``pending_cells`` (2026-10-14): a template constant or derivation is
    taken back to an open cell until the IIG corpus's patterns say how prod
    fills the column; a value an input states (FAQ) stays. One NOTE per column
    (the same text on every row, said once)."""
    for header, why in tpl.pending_cells.get(tab, {}).items():
        current = cells.get(header)
        if current is not None and current["badge_entry"]["badge"] != "synthetic":
            continue
        cell = _cell("", "needs_template", f"open until the corpus patterns report: {why}")
        cell["badge_entry"]["note"] = (
            f"iig_pending:{tab}.{header} — left blank until tools/iig_fill_rate.py "
            f"--patterns says how the IIG corpus fills it: {why}")
        cells[header] = cell
    return cells


def _base_type(dtype: str | None) -> str:
    return re.sub(r"\(.*\)", "", dtype or "").strip()


def _named_sources(fields: list[SttmField]) -> bool:
    """Every STTM source column is a real header (not blank, not 'col<N>')."""
    return bool(fields) and all(
        (f.source_column or "").strip()
        and not re.fullmatch(r"col_?\d+", f.source_column.strip(), re.IGNORECASE)
        for f in fields)


def _recase(value: str, like: str | None) -> str:
    """``value`` in the casing style of ``like`` ('String' -> 'Timestamp',
    'STRING' -> 'TIMESTAMP', 'string' -> 'timestamp')."""
    if not like or not value:
        return value
    if like.isupper():
        return value.upper()
    if like.islower():
        return value.lower()
    return value[:1].upper() + value[1:].lower()


def _family_audit(tpl: MetadataTemplateConfig, stated: list[tuple[str, str]],
                  data: list[SttmField]) -> list[tuple[str, str]]:
    """The IIG's audit columns by the family convention (first real-row
    scorecard, 2026-10-08): the STTM's audit rows (the PRX three), or the
    family's own list in order — a column the STTM types keeps its type, any
    other is String, a column already a data column of the table is not
    repeated. Casing: the template's audit_type_casing, or the data columns'."""
    convention = tpl.family_conventions
    if convention.audit_columns:
        types = {c.upper(): t for c, t in stated}
        data_columns = {f.stage_column.upper() for f in data}
        columns = [(c, types.get(c.upper(), "String")) for c in convention.audit_columns
                   if c.upper() not in data_columns]
    else:
        columns = list(stated)
    if convention.audit_type_case == "data":
        like = next((f.stage_datatype for f in data if f.stage_datatype), None)
        return [(c, _recase(t, like)) for c, t in columns]
    return [(c, tpl.audit_type_casing.get(t, t)) for c, t in columns]


def _audit(spec: ResolvedFeedSpec, tpl: MetadataTemplateConfig) -> list[tuple[str, str]]:
    return _family_audit(tpl, [(a.column, a.datatype) for a in spec.audit_columns],
                         spec.detail_segment.fields)


@dataclass
class _TableGroup:
    """One table the feed defines on the resolved side (multi-table rule 1):
    the segments whose stage table is the same (catalog, schema, table)."""

    stage: ResolvedTable
    standard: ResolvedTable | None
    segments: list[SegmentSpec] = field(default_factory=list)

    @property
    def fields(self) -> list[SttmField]:
        """The table's columns, STTM order, a column shared by its segments once."""
        seen: set[str] = set()
        out: list[SttmField] = []
        for segment in self.segments:
            for f in segment.fields:
                if f.stage_column not in seen:
                    seen.add(f.stage_column)
                    out.append(f)
        return out

    @property
    def is_detail(self) -> bool:
        return any(s.segment == "Detail" for s in self.segments)


def _table_groups(spec: ResolvedFeedSpec) -> list[_TableGroup]:
    """Rule 1 over the resolved segments: one group per distinct stage
    (catalog, schema, table), first-seen order. A group's standard table is
    its segments' (the segmented dialect), else — for a feed with ONE table —
    the feed's standard table."""
    groups: dict[tuple, _TableGroup] = {}
    for segment in spec.segments:
        table = segment.stage_table
        key = (table.catalog, table.schema_name, table.table)
        group = groups.setdefault(key, _TableGroup(stage=table, standard=None))
        group.segments.append(segment)
        if group.standard is None and segment.standard_table is not None:
            group.standard = segment.standard_table
    out = list(groups.values())
    if len(out) == 1 and out[0].standard is None:
        out[0].standard = spec.standard_table
    return out


def _detail_group(groups: list[_TableGroup]) -> _TableGroup:
    """Rule 3: the table holding the Detail segment, else the sole table."""
    return next((g for g in groups if g.is_detail), groups[0])


def _group_audit(group: _TableGroup, spec: ResolvedFeedSpec,
                 tpl: MetadataTemplateConfig) -> list[tuple[str, str]]:
    """The table's audit columns: its segments' own audit rows when every
    segment states them, else the feed's."""
    if all(s.audit_columns for s in group.segments):
        seen: dict[str, str] = {}
        for segment in group.segments:
            for a in segment.audit_columns or []:
                seen.setdefault(a.column, a.datatype)
        return _family_audit(tpl, list(seen.items()), group.fields)
    return _family_audit(tpl, [(a.column, a.datatype) for a in spec.audit_columns],
                         group.fields)


def _feed_files(spec: ResolvedFeedSpec, config: Config) -> list[FeedFile]:
    """Rule 2: the resolver's files, else the spec's patterns expanded now."""
    if spec.files:
        return list(spec.files)
    from codegen.resolve.files import expand_files

    files, _flags = expand_files(spec.file_name_patterns, list(spec.lobs),
                                 config.extractor.lob_tokens, provenance="file pattern")
    return files


def _wildcarded(pattern: str, tpl: MetadataTemplateConfig) -> str:
    """A stated pattern as the framework writes it: each date placeholder of
    ``file_pattern_wildcards`` (longest first, not inside a word) -> '*'."""
    for token in sorted(tpl.file_pattern_wildcards, key=len, reverse=True):
        pattern = re.sub(rf"(?<![A-Za-z]){re.escape(token)}(?![A-Za-z])", "*", pattern)
    return pattern


def _family_citation(tpl: MetadataTemplateConfig) -> str:
    return tpl.family_conventions.citation or "the template's family_conventions"


def _lob_cell(tpl: MetadataTemplateConfig, value: str, why: str) -> dict:
    """LOB by the feed family's convention: "codes" writes ``value`` (a
    per-LOB file's code, else the feed's LOB codes from the FRD / STTM header);
    "blank" leaves it blank — decided by the convention, not an open cell."""
    if tpl.family_conventions.lob == "codes":
        return _cell(value, "from_frd", f"{why} (family convention lob: codes — "
                                        f"{_family_citation(tpl)})")
    cell = _cell("", "from_frd", "family convention lob: blank — "
                                 f"{_family_citation(tpl)}")
    cell["badge_entry"]["deliberate_blank"] = True
    return cell


def _feed_lob(tpl: MetadataTemplateConfig, tab: str, lobs: list[str], why: str) -> dict:
    """ONE LOB for a row that no file keys (2026-10-14): the only LOB, else
    open with a NOTE — never the comma-joined list."""
    from codegen.metadata_sheet import feed_lob_cell

    if tpl.family_conventions.lob != "codes" or len(lobs) <= 1:
        return _lob_cell(tpl, lobs[0] if lobs else "", why)
    return feed_lob_cell(lobs, why, tab)


def _file_lob_cell(tpl: MetadataTemplateConfig, tab: str, file, spec: ResolvedFeedSpec) -> dict:
    """An ADLS row's LOB (2026-10-14, D1 pair_12): the file's own LOB (a LOB
    token expanded, or keyed by the FRD LOB table / the lob_reference / an
    answer — the NOTE names the source); a file the table keys to no single
    LOB stays OPEN (the feed's QUESTION ``lob_by_file`` asks for it); else the
    feed's one LOB. Never the comma-joined list."""
    from codegen.resolve.files import LOB_SOURCES

    if file.lob:
        cell = _lob_cell(tpl, file.lob, f"this file's LOB — {file.provenance}")
        if file.lob_source and tpl.family_conventions.lob == "codes":
            cell["badge_entry"]["note"] = (f"iig_lob:{tab}.LOB — the file's LOB from "
                                           f"{LOB_SOURCES[file.lob_source]}")
        return cell
    unkeyed = spec.lob_question_key and file.pattern in spec.lob_unkeyed
    if unkeyed and tpl.family_conventions.lob == "codes":
        cell = _cell("", "needs_template", f"open — the FRD LOB table keys no single LOB for "
                                           f"this file; QUESTION {spec.lob_question_key}")
        cell["badge_entry"]["note"] = (f"iig_lob:{tab}.LOB — open for {len(spec.lob_unkeyed)} "
                                       f"file(s) the LOB lookup did not key (QUESTION "
                                       f"{spec.lob_question_key})")
        return cell
    return _feed_lob(tpl, tab, list(spec.lobs),
                     "the feed's LOB (FRD / STTM header block) — not a per-LOB file "
                     "(docs/acfc/MULTI_TABLE_DESIGN.md rule 2)")


def _schema_drift_cell(tpl: MetadataTemplateConfig) -> dict:
    """ADLS SCHEMA_DRIFT_FLAG by the feed family's convention (2026-10-09):
    the pair-1 (PRX) family 'N', the SD / CAQH-style family 'Y'."""
    value = tpl.family_conventions.schema_drift_flag
    return _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(
        citation=f"family convention schema_drift_flag: {value} — {_family_citation(tpl)}"))


def _generalized_pattern(files: list[FeedFile], tpl: MetadataTemplateConfig,
                         tokens: list[str]) -> str:
    """One pattern covering every file the feed receives (Chunk A, 2026-10-08:
    STGDELTA OBJECT_NAME is the GENERALIZED file pattern): each stated pattern
    with its LOB token and date placeholders as '*'; several patterns
    generalize position by position over their '_' tokens (a token the
    patterns disagree on is '*'), else to their common leading tokens + '*';
    the extension is kept when they share one."""
    from codegen.resolve.files import lob_token

    wild = []
    for template in dict.fromkeys(f.template for f in files):
        token = lob_token(template, tokens)
        wild.append(_wildcarded(template.replace(token, "*") if token else template, tpl))
    if len(wild) == 1:
        return wild[0]
    split = [(str(PurePosixPath(p).with_suffix("")), PurePosixPath(p).suffix) for p in wild]
    parts = [stem.split("_") for stem, _ext in split]
    if len({len(p) for p in parts}) == 1:
        tokens_out = [p0 if all(p[i] == p0 for p in parts) else "*"
                      for i, p0 in enumerate(parts[0])]
    else:
        tokens_out = []
        for column in zip(*parts, strict=False):
            if len(set(column)) != 1:
                break
            tokens_out.append(column[0])
        tokens_out.append("*")
    collapsed: list[str] = []
    for token in tokens_out:
        if not (token == "*" and collapsed and collapsed[-1] == "*"):
            collapsed.append(token)
    extensions = {ext for _stem, ext in split}
    return "_".join(collapsed) + (extensions.pop() if len(extensions) == 1 else ".*")


def _sequence_cell(index: int, what: str) -> dict:
    """OBJECT_ID by the framework convention: the object's position within
    its group (METADATA_DB_SEMANTICS §5: 'one per input file within the group'
    — 1..n). A convention cell, so it fills the always-blank column."""
    cell = _cell(str(index), "synthetic",
                 f"template constant — framework convention: OBJECT_ID = 1..n within the group "
                 f"(docs/acfc/METADATA_DB_SEMANTICS.md §5); this {what} is object {index}")
    cell["badge_entry"]["convention"] = True
    return cell


def _primary_key(fields: list[SttmField], layer: str) -> list[str]:
    """The band's Primary Key columns (step 1: SttmField.primary_key, the
    Standard band's own when it differs)."""
    if layer == "stage":
        return [f.stage_column for f in fields if f.primary_key]
    return [f.standard_column for f in fields if f.standard_column and (
        f.standard_primary_key if f.standard_primary_key is not None else f.primary_key)]


def _qualified(table) -> str:
    parts = [table.catalog, table.schema_name, table.table]
    return ".".join(p for p in parts if p)


def catalog_mapping_note(table) -> str:
    """Multi-table rule 7: the tooltip citation of a catalog the environment's
    conventions.catalog_map mapped ('' when no map applied)."""
    if getattr(table, "catalog_logical", None) is None:
        return ""
    return (f"; catalog_map {table.catalog_logical} → {table.catalog} (conventions.catalog_map, "
            "the environment overlay)")


def _landing(feed: FrdFeed) -> str | None:
    if not feed.landing_location:
        return None
    if location_scheme(feed.landing_location):
        # M10.2: a location URI is carried through as written (trailing '/'
        # so the path shapes append to it) — never re-rooted or re-spelt.
        return feed.landing_location.strip().rstrip("/") + "/"
    value = feed.landing_location.replace("\\", "/")
    return "/" + value.strip("/") + "/"


def _path_cell(tpl: MetadataTemplateConfig, tab: str, header: str, raw: str, badge: str,
               tooltip: str | None, lowered: str | None = None) -> dict:
    """A derived path cell, normalised (first ACFC run): the input's trailing
    punctuation / doubled separators never reach the cell, and the family's
    ``path_case`` applies to the input-derived segments (``lowered`` = the
    value built from lowercased inputs). Any change leaves a ``path_note``
    with the before / after — a ``path_normalised`` gate flag. A clean path
    is the cell exactly as before."""
    value, changes = normalise_path(lowered if lowered is not None else raw)
    if lowered is not None and lowered != raw:
        changes = ["input segments lowercased (path_case: lower)", *changes]
    cell = _cell(value if changes else raw, badge, tooltip)
    if changes:
        cell["badge_entry"]["path_note"] = path_normalised_flag(f"{tab}.{header}", raw, value,
                                                                changes)
    return cell


def _lower_inputs(tpl: MetadataTemplateConfig, uri: bool) -> bool:
    # A location URI is carried as written (M10.2) — never re-cased.
    return tpl.path_case == "lower" and not uri


def _landing_badge(feed: FrdFeed, folder_badge: str = "from_frd") -> tuple[str, str | None]:
    scheme = location_scheme(feed.landing_location)
    if scheme:
        return "location_uri", f"location URI ({scheme}://) from the FRD ADLS Location"
    return folder_badge, "FRD Structural Metadata → ADLS Location"


_RELATIVE_PLACEHOLDERS = ("{landing_rel}", "{domain_path}")


def _landing_rel(tpl: MetadataTemplateConfig, tab: str, landing: str) -> str:
    """{landing_rel}: the landing minus its leading /<landing container> —
    the path INSIDE the container the files land in. The landing container is
    ADLS_DELTA_INGESTION_DETAILS's SRC_CONTAINER_NAME (the sheet that reads
    the landed files), else the sheet's own: a stage → standard sheet's
    SRC_CONTAINER_NAME is the STAGE container, which the landing never starts
    with (multi-table, pair 4). Unchanged when it does not start so."""
    container = (tpl.constants.get("ADLS_DELTA_INGESTION_DETAILS", {})
                 .get("SRC_CONTAINER_NAME")
                 or tpl.constants.get(tab, {}).get("SRC_CONTAINER_NAME"))
    prefix = f"/{container}/" if container else None
    if prefix and landing.lower().startswith(prefix.lower()):
        return landing[len(prefix) - 1:]
    return landing


def _domain_path(landing_rel: str) -> str:
    """{domain_path}: {landing_rel} minus a leading inbound/ (no leading '/')."""
    return re.sub(r"^/?inbound/", "", landing_rel, flags=re.IGNORECASE).lstrip("/")


def _paths(tpl: MetadataTemplateConfig, tab: str, feed: FrdFeed,
           stage_table: str, reject_table: str) -> dict[str, dict]:
    """Path cells from the template's shapes. Placeholders: {landing} (the
    FRD ADLS Location), {landing_rel} / {domain_path} (see above),
    {stage_table}, {reject_table}. Any shape may be overridden per sheet +
    column in an overlay (SRC_ADLS_PATH included — a shape wins over the
    FRD's plain landing)."""
    landing = _landing(feed)
    if landing is None:
        return {}
    cells = {}
    uri = location_scheme(feed.landing_location)
    landing_rel = _landing_rel(tpl, tab, landing)
    for header, pattern in tpl.path_patterns.get(tab, {}).items():
        if header == "RECYCL_ADLS_PATH":
            continue                     # _recycle_cells: only when a recycle is stated
        if uri and any(p in pattern for p in _RELATIVE_PLACEHOLDERS):
            continue                     # a location URI has no container-relative path
        if uri:
            # M10.2: the shape's segments are appended INSIDE the URI's path
            # — a shape that puts something before {landing} ("/Archive
            # {landing}") cannot prefix a URI, so its literal goes after
            # the URI too, and the cell says so.
            before, _, after = pattern.partition("{landing}")
            value = join_location(
                landing, before, after.format(stage_table=stage_table,
                                              reject_table=reject_table))
            if pattern.endswith(("/", "{landing}")) and not value.endswith("/"):
                value += "/"                     # the shape's own trailing slash
            note = (f"; the template shape {pattern!r} prefixes the landing, which a "
                    "location URI cannot carry — its segments follow the URI instead"
                    if before.strip("/\\") else "")
            cell = _path_cell(tpl, tab, header, value, "synthetic",
                              _path_tooltip(tpl, tab, header, pattern)
                              + f" (location URI base, {uri}://){note}")
            if note:
                cell["badge_entry"]["note"] = (
                    f"iig_path_shape_on_uri:{tab}.{header} — template shape {pattern!r} "
                    "prefixes the landing; on a location URI its segments follow the URI")
            cells[header] = cell
            continue
        value = pattern.format(landing=landing, landing_rel=landing_rel,
                               domain_path=_domain_path(landing_rel),
                               stage_table=stage_table, reject_table=reject_table)
        lowered = (pattern.format(landing=landing.lower(), landing_rel=landing_rel.lower(),
                                  domain_path=_domain_path(landing_rel).lower(),
                                  stage_table=stage_table.lower(),
                                  reject_table=reject_table.lower()).replace("//", "/")
                   if _lower_inputs(tpl, False) else None)
        # A shape's own doubled separator ({landing}/x) was always collapsed
        # silently; the INPUT's punctuation is normalised and flagged.
        cells[header] = _path_cell(tpl, tab, header, value.replace("//", "/"), "synthetic",
                                   _path_tooltip(tpl, tab, header, pattern), lowered)
    return cells


def _path_tooltip(tpl: MetadataTemplateConfig, tab: str, header: str, pattern: str) -> str:
    """The template's own shape cites the template; a shape an overlay
    supplies (path_citations) names the overlay and the shape. Both keep the
    'synthetic path shape' prefix the review copy keys its reason on."""
    citation = tpl.path_citations.get(tab, {}).get(header)
    if citation is None:
        return _PATH_TOOLTIP.format(citation=tpl.citation)
    return (f"synthetic path shape {pattern!r} from {citation}; the real container/path are "
            "assigned at deployment")


def _object_name(pattern: str, tokens: list[str] | None = None,
                 bound: list[str] | None = None) -> str:
    """The pattern's name: extension and wildcards removed, then (first
    real-row scorecard) every TRAILING segment made only of date / time tokens
    (``object_name_strip_tokens``: 'demographics_YYYY_MM.csv' -> 'demographics').
    A segment of ``bound`` tokens alone (``object_name_bound_tokens``: MI, SS)
    is a name, not a time — round 6: 'x_MI_YYYYMMDD_HHMM.psv' -> 'x_MI', as the
    SD prod rows write it. A token inside the name is kept."""
    stem = PurePosixPath(pattern).stem if "." in pattern else pattern
    stem = re.sub(r"_\*|\*_|\*", "", stem)
    if tokens:
        ordered = sorted(tokens, key=len, reverse=True)
        token_re = "|".join(re.escape(t) for t in ordered)
        trailing = re.compile(rf"[_\-. ]((?:{token_re})+)$")
        unbound = set(tokens) - set(bound or [])
        while (match := trailing.search(stem)) is not None and match.start() > 0:
            if not unbound & set(re.findall(token_re, match.group(1))):
                break                                  # a lone '_MI': part of the name
            stem = stem[:match.start()]
    return stem


def _src_file_name_cell(tpl: MetadataTemplateConfig, pattern: str, stated: str,
                        badge: str) -> dict:
    """ADLS SRC_FILE_NAME by the family convention: the pattern (date tokens
    as '*'), or the OBJECT_NAME prefix + '*' (prefix_star — the SD rows)."""
    if tpl.family_conventions.src_file_name == "prefix_star":
        value = _object_name(pattern, tpl.object_name_strip_tokens,
                             tpl.object_name_bound_tokens) + "*"
        return _cell(value, badge, f"stated {stated!r} — the name prefix + '*' (family "
                                   f"convention src_file_name: prefix_star; "
                                   f"{_family_citation(tpl)})")
    return _cell(pattern, badge, f"stated {stated!r}" if pattern != stated else None)


# ---- rule 3: SOURCE ------------------------------------------------------------
_VENDOR_SEPARATOR_RE = re.compile(r"\s*[\u2013\u2014]\s*|\s+-\s+")


def _source_cell(feed: FrdFeed) -> dict:
    """SOURCE = the vendor's display name (first real-row scorecard): a
    trailing vendor id / code after an en-dash or a spaced hyphen ('Vendor C
    \u2013 VC 00000') is dropped; the full label stays in the tooltip. A tail
    that is a word, not a code, is kept."""
    full = (feed.source_system or "").strip()
    parts = list(_VENDOR_SEPARATOR_RE.finditer(full))
    if parts:
        last = parts[-1]
        name, tail = full[:last.start()].strip(), full[last.end():].strip()
        if name and tail and (re.search(r"\d", tail)
                              or re.fullmatch(r"[A-Z0-9_#/. ]{1,15}", tail)):
            return _cell(name, "from_frd", f"vendor display name — the FRD states {full!r} "
                                           f"(trailing vendor id / code {tail!r} dropped)")
    return _cell(feed.source_system, "from_frd")


def _faq_cell(faq, name: str, label: str) -> dict | None:
    from codegen.metadata_sheet import _faq_cell as base

    return base(getattr(faq, name, None), label) if faq is not None else None


def _process_name(faq) -> dict | None:
    return _faq_cell(faq, "process_name", "framework process name (load-pattern FAQ)")


_FREQUENCY_TOKENS = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly",
                     "yearly": "Yearly", "annual": "Yearly", "annually": "Yearly"}
_FREQUENCY_TOKEN_RE = re.compile(r"\b(daily|weekly|monthly|yearly|annual(?:ly)?)\b",
                                 re.IGNORECASE)


def _frequency_token(text: str) -> str | None:
    """One framework frequency token from FRD / FAQ text: the LEADING word
    when it is one ("Monthly Run; … yearly twice" -> Monthly — the run
    cadence leads, as metadata_sheet._frequency_parts reads it), else the
    only token the text names; None when it names none or several."""
    found = [_FREQUENCY_TOKENS[m.group(1).lower()] for m in _FREQUENCY_TOKEN_RE.finditer(text)]
    lead = _FREQUENCY_TOKEN_RE.match(text.strip())
    if lead:
        return _FREQUENCY_TOKENS[lead.group(1).lower()]
    return found[0] if len(set(found)) == 1 else None


_RUN_WORDS_RE = re.compile(r"\b(runs?|running|scheduled?|schedules|refresh(?:ed|es)?)\b",
                           re.IGNORECASE)
_SCHEDULE_TAB = "DATA_FACTORY_PIPELINE_SCHEDULE"


def _run_cadence(feed: FrdFeed, tpl: MetadataTemplateConfig | None) -> tuple[str, str] | None:
    """(token, source) of the PIPELINE RUN cadence: the FRD's run / schedule /
    refresh statements ("Frequency of data refresh – Monthly Run") when they
    name exactly one token, else the schedule inventory's PIPELINE_FREQUENCY
    (template_rows of DATA_FACTORY_PIPELINE_SCHEDULE) when it is one token;
    None when neither states it."""
    found: dict[str, str] = {}
    for mention in getattr(feed, "frequency_mentions", None) or []:
        if not _RUN_WORDS_RE.search(mention):
            continue
        for match in _FREQUENCY_TOKEN_RE.finditer(mention):
            found.setdefault(_FREQUENCY_TOKENS[match.group(1).lower()], mention)
    if len(found) == 1:
        token, mention = next(iter(found.items()))
        return token, f"the FRD's run / schedule statement {mention}"
    stated = {str(row.get("PIPELINE_FREQUENCY")).strip()
              for row in (tpl.template_rows.get(_SCHEDULE_TAB, []) if tpl is not None else [])
              if row.get("PIPELINE_FREQUENCY")}
    tokens = {_frequency_token(v) for v in stated} - {None}
    if len(tokens) == 1:
        return tokens.pop(), (f"the {_SCHEDULE_TAB} inventory's PIPELINE_FREQUENCY "
                              f"{sorted(stated)} (template_rows)")
    return None


def _frequency(feed: FrdFeed, faq, tpl: MetadataTemplateConfig | None = None) -> dict:
    """FREQUENCY / PIPELINE_FREQUENCY as one framework token (Monthly / Daily
    / Weekly / Yearly) = the PIPELINE RUN cadence (2026-10-08 decision: the SD
    rows are Monthly with files delivered twice a year; CAQH's ingestion
    FREQUENCY equals its pipeline schedule frequency). The run cadence comes
    from the FRD's run / schedule statements or the schedule inventory; the
    file-delivery cadence (the FRD Frequency field / its File Details fill /
    the FAQ) goes in the tooltip, and when the two differ the cell is flagged
    frequency_delivery_differs with both. No run cadence stated: the delivery
    cadence, as before. No single token -> left open, never guessed."""
    from codegen.metadata_sheet import _frequency_cell

    cell = _frequency_cell(feed, faq)
    raw = str(cell["value"] or "").strip()
    entry = cell["badge_entry"]
    delivery = _frequency_token(raw) if raw else None
    source = entry.get("tooltip") or ("FRD Descriptive Metadata → Frequency"
                                      if entry["badge"] == "from_frd" else "stated")
    run = _run_cadence(feed, tpl)
    if run is not None:
        token, run_source = run
        noted = (f"; file delivery: stated as {raw!r} ({source})" if raw
                 else "; no file-delivery cadence stated")
        badge = "synthetic" if _SCHEDULE_TAB in run_source else "from_frd"
        cell = _cell(token, badge, f"pipeline run cadence {token!r} — {run_source}{noted}")
        if raw and delivery != token:
            cell["badge_entry"]["note"] = (
                f"frequency_delivery_differs — FREQUENCY {token!r} is the pipeline run cadence "
                f"({run_source}); the files are delivered {raw!r} "
                f"(→ {delivery!r}; {source}) — both kept, the run cadence written")
        return cell
    if not raw:
        return cell
    if delivery is None:
        return _cell("", "needs_template",
                     f"{source}: stated as {raw!r} — no single framework frequency token "
                     "(Monthly / Daily / Weekly / Yearly) and no run / schedule statement; "
                     "left open")
    return (cell if delivery == raw else
            _cell(delivery, entry["badge"],
                  f"{source}: stated as {raw!r} → framework frequency token {delivery!r} "
                  "(no run / schedule statement: the delivery cadence)"))


def _catalog_cell(config: Config, profile, table, layer: str) -> dict | None:
    """The catalog the DDL's three-part name uses (emit.framework._qualify):
    the resolved table's catalog (FRD label, else the STTM band), else the
    conventions profile's default_catalog[layer] (provenance config_default).
    None when no link states one — the cell stays open (or a template /
    overlay constant fills it)."""
    if table.catalog:
        return _cell(table.catalog, "from_frd",
                     f"{layer} catalog: FRD Target Catalog and Schema label / STTM target "
                     "band catalog column (the DDL's three-part name)"
                     + catalog_mapping_note(table))
    from codegen.emit.framework import _config_default_catalog

    default = _config_default_catalog(config, profile, layer) if profile is not None else None
    if not default:
        return None
    return _cell(default, "synthetic",
                 f"{layer} catalog: no FRD / STTM catalog; provenance config_default "
                 f"(conventions default_catalog[{layer}] = {default!r}) — the DDL's "
                 "three-part name uses the same value")


def _load_option_cell(strategy, layer_label: str) -> dict:
    """TGT_LOAD_OPTION in the framework's vocabulary: the FRD Load Strategy
    through the same map TGT_REFRESH_TYPE uses (metadata_sheet
    ._REFRESH_TYPE_BY_STRATEGY: Truncate and Load -> Overwrite); a mapped
    value keeps the FRD's own text in the tooltip."""
    from codegen.metadata_sheet import _REFRESH_TYPE_BY_STRATEGY

    tooltip = f"FRD Structural Metadata → Load Strategy {layer_label}"
    option = _REFRESH_TYPE_BY_STRATEGY.get(strategy, strategy)
    if option != strategy:
        tooltip += (f": FRD states {str(strategy)!r} → framework load option {option!r} "
                    "(reference IIG vocabulary)")
    return _cell(option, "from_frd", tooltip)


_YES_NO = {"yes": "Y", "y": "Y", "true": "Y", "no": "N", "n": "N", "false": "N"}


def _header_flag_cells(spec: ResolvedFeedSpec, faq, tpl: MetadataTemplateConfig) -> dict:
    cells = _faq_header_flag_cells(spec, faq)
    by_format = tpl.file_header_flag_by_format
    kind = "delimited" if spec.delimiter else "fixed_width"
    if "FILE_HEADER_FLAG" not in cells and kind in by_format:
        # 2026-10-14 (D1 post43 item 4): no FAQ answer — the file's format
        # decides, by the family's observed rule (a NOTE, said once).
        value = by_format[kind]
        citation = tpl.file_header_flag_citation or tpl.citation
        cell = _cell(value, "synthetic",
                     f"{kind} file -> FILE_HEADER_FLAG {value!r} ({citation})")
        cell["badge_entry"]["note"] = (
            f"iig_derived:ADLS_DELTA_INGESTION_DETAILS.FILE_HEADER_FLAG — "
            f"{kind} file -> {value!r} (no FAQ has_header answer; {citation})")
        cells["FILE_HEADER_FLAG"] = cell
    return cells


def _faq_header_flag_cells(spec: ResolvedFeedSpec, faq) -> dict:
    """HEADER_FLAG / FILE_HEADER_FLAG / FILE_FOOTER_FLAG — only from a stated
    answer (the FAQ's has_header / has_trailer; the FRD states neither).
    Delimited files: the column-header row -> HEADER_FLAG + FILE_HEADER_FLAG,
    the trailer -> FILE_FOOTER_FLAG, as Y / N. Fixed-width files keep the
    pre-existing reading (HEADER_FLAG = the FAQ answer as given; the FILE_*
    flags open): the golden's flags there do not follow header / trailer
    SEGMENTS (an open framework question), so nothing is derived. Unstated
    -> open (BSA)."""
    header = _faq_cell(faq, "has_header", "load-pattern FAQ answer")
    if not spec.delimiter:
        return {"HEADER_FLAG": header} if header is not None else {}
    cells = {}
    for name, headers in (("has_header", ("HEADER_FLAG", "FILE_HEADER_FLAG")),
                          ("has_trailer", ("FILE_FOOTER_FLAG",))):
        answer = _faq_cell(faq, name, "load-pattern FAQ answer")
        flag = _YES_NO.get(str(answer["value"]).strip().lower()) if answer else None
        if flag is None:
            continue
        for column in headers:
            cells[column] = _cell(flag, answer["badge_entry"]["badge"],
                                  f"{answer['badge_entry'].get('tooltip', '')} — {name} "
                                  f"{answer['value']!r} → {flag}")
    return cells


def _reject_table(tpl: MetadataTemplateConfig, spec: ResolvedFeedSpec, stage_table: str) -> str:
    if tpl.reject_table_suffix is not None:
        return f"{stage_table}{tpl.reject_table_suffix}"
    return spec.errors_table.table


# -- tabs ---------------------------------------------------------------------- #


def _feed_token(feed: FrdFeed, faq) -> tuple[str, str]:
    """{feed} of the pipeline names: the FAQ feed_abbreviation when answered,
    else the feed slug in capitals — (value, its source)."""
    answer = getattr(faq, "feed_abbreviation", None) if faq is not None else None
    if answer is not None and getattr(answer, "source", "unknown") != "unknown":
        return str(answer.value), "load-pattern FAQ feed_abbreviation"
    from codegen.resolve.resolver import normalize_feed_name

    return normalize_feed_name(feed.feed_name).upper(), "the feed slug (no FAQ feed_abbreviation)"


def _pipeline_roles(tab, feed, faq, tpl, extra: dict | None = None) -> list[dict]:
    """Step 5: the four structural rows (grand master -> master -> file-to-
    stage, stage-to-standard). Names from the naming convention, parent by
    position: the top pipeline's parent is 0 (METADATA_DB_SEMANTICS §2), every
    other row's PARENT_PIPELINE_ID is its parent row's PIPELINE_ID — the
    engineer's, so blank, the tooltip naming the row."""
    token, source = _feed_token(feed, faq)
    position = {role.role: index for index, role in enumerate(tpl.pipeline_roles, start=1)}
    citation = tpl.pipeline_roles_citation or tpl.citation
    rows = []
    for role in tpl.pipeline_roles:
        name = role.name.format(feed=token)
        cells = {
            "PIPELINE_NAME": _cell(name, "synthetic",
                                   f"template constant — {citation}: {role.name!r} with "
                                   f"{{feed}} = {token!r} ({source})"),
            "PIPELINE_DESCRIPTION": _cell(role.description, "synthetic",
                                          f"template constant — {citation}: the {role.role} "
                                          "pipeline"),
        }
        if role.parent is None:
            parent = _cell("0", "synthetic",
                           "template constant — framework convention: the top pipeline's "
                           "PARENT_PIPELINE_ID is 0 (docs/acfc/METADATA_DB_SEMANTICS.md §2)")
        else:
            parent = _cell("", "needs_template",
                           f"assigned by the engineer: the PIPELINE_ID of row "
                           f"{position[role.parent]} ({role.parent}) — the parent by position")
        parent["badge_entry"]["convention"] = True
        cells["PARENT_PIPELINE_ID"] = parent
        cells["PIPELINE_FREQUENCY"] = _frequency(feed, faq, tpl)
        process = _process_name(faq)
        if process is not None:
            cells["APPLICATION_NAME"] = process
        context = {**_row_context(feed, faq, cells, role.role), **(extra or {})}
        _derive(tpl, tab, cells, context)
        rows.append(_with_constants(tpl, tab, cells, context, faq))
    return rows


def _lob_context(spec: ResolvedFeedSpec | None, config: Config) -> dict:
    """D1 post45: a feed that fans out per LOB (files with several LOBs) —
    the schedule's per-LOB description is offered in its NOTE."""
    if spec is None:
        return {}
    lobs = list(dict.fromkeys(f.lob for f in _feed_files(spec, config) if f.lob))
    return {"lob_fanout": "yes" if len(lobs) > 1 else "",
            "lob": "<LOB: " + ", ".join(lobs) + ">" if len(lobs) > 1 else ""}


def _pipeline_schedule(tab, feed, config, spec, faq, tpl) -> list[dict]:
    if not tpl.template_rows.get(tab) and tpl.pipeline_roles:
        return _pipeline_roles(tab, feed, faq, tpl, _lob_context(spec, config))
    rows = tpl.template_rows.get(tab) or [{}]
    out = []
    for template_row in rows:
        cells = {
            header: _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(citation=tpl.citation))
            for header, value in template_row.items() if not header.startswith("_")
        }
        cells["PIPELINE_FREQUENCY"] = _frequency(feed, faq, tpl)
        process = _process_name(faq)
        if process is not None:
            cells["APPLICATION_NAME"] = process
        context = {**_row_context(feed, faq, cells, template_row.get("_pipeline_role")),
                   **_lob_context(spec, config)}
        _derive(tpl, tab, cells, context)
        out.append(_with_constants(tpl, tab, cells, context, faq))
    return out


def _file_adls(tab, feed, config, spec, faq, tpl) -> list[dict]:
    cells = {
        "DOMAIN": _cell(feed.domain or "", "from_frd"),
        "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
    }
    landing = _landing(feed)
    if landing is not None:
        uri = bool(location_scheme(feed.landing_location))
        cells["TGT_ADLS_PATH"] = _path_cell(
            tpl, tab, "TGT_ADLS_PATH", landing, *_landing_badge(feed),
            lowered=landing.lower() if _lower_inputs(tpl, uri) else None)
    # A configured shape wins (e.g. {landing_rel}: the landing INSIDE its
    # container — Chunk A, pair 4); without one the FRD landing as before.
    cells.update(_paths(tpl, tab, feed, "", ""))
    return [_with_constants(tpl, tab, cells)]


def _adls_delta(tab, feed, config, spec, faq, tpl) -> list[dict]:
    """Rule 3: one row per FILE the feed receives (rule 2), every row into the
    DETAIL table (or the sole table); per-file cells OBJECT_ID / OBJECT_NAME /
    SRC_FILE_NAME / LOB / partition, the rest shared."""
    if spec is None:
        return []
    detail = _detail_group(_table_groups(spec))
    fields = detail.fields
    audit = _group_audit(detail, spec, tpl)
    stage = detail.stage
    reject = _reject_table(tpl, spec, stage.table)
    # One row per file pattern ALWAYS (first real-row scorecard): several
    # patterns are never joined with ';' into one cell.
    files = _feed_files(spec, config)
    if tpl.src_columns_style == "named" and _named_sources(fields):
        src_columns = ",".join(f"{f.source_column}:{f.source_column}" for f in fields)
    elif tpl.src_columns_style in ("positional", "named"):
        src_columns = ",".join(f"col{i}:{f.stage_column}" for i, f in enumerate(fields, start=1))
    else:
        src_columns = ",".join(f"{f.source_column}:{f.stage_column}" for f in fields)
    # A FILE source (delimited / fixed width): its fields are strings, whatever
    # the STTM's source band types them (first real-row scorecard, 2026-10-08).
    source_type = tpl.file_source_type
    if tpl.data_type_style == "base":
        src_types = ",".join(f"{source_type}:{_base_type(f.stage_datatype)}" for f in fields)
    else:
        src_types = ",".join(f"{source_type}:{f.stage_datatype}" for f in fields)
    coerced = [f for f in fields if (f.source_datatype or "").strip().lower()
               not in ("", "unstated", source_type.lower())]
    src_type_cell = _cell(src_types, "from_sttm",
                          f"file fields are strings: source side {source_type!r} for every "
                          "column (template file_source_type)")
    if coerced:
        src_type_cell["badge_entry"]["note"] = (
            f"src_type_coerced_string:{detail.stage.table} — {len(coerced)} source field(s) the "
            f"STTM types otherwise, written {source_type!r} (file fields are strings): "
            + ", ".join(f"{f.source_column} {f.source_datatype!r}"
                        + (f" ({f.provenance.sheet} row {f.provenance.row})"
                           if f.provenance else "") for f in coerced[:5])
            + (f" … +{len(coerced) - 5}" if len(coerced) > 5 else ""))
    key_columns = _primary_key(fields, "stage")
    rows = []
    for index, file in enumerate(files, start=1):
        pattern = _wildcarded(file.pattern, tpl)
        cells = {
            "OBJECT_ID": _sequence_cell(index, f"file ({pattern})"),
            "OBJECT_NAME": (_cell(_object_name(pattern, tpl.object_name_strip_tokens,
                                               tpl.object_name_bound_tokens),
                                  "from_frd",
                                  f"derived from the file pattern {pattern!r} (wildcards, "
                                  "trailing date / time tokens and extension removed)")
                            if tpl.object_name_from_pattern
                            else _cell(feed.feed_name, "from_frd")),
            "DOMAIN": _cell(feed.domain or "", "from_frd"),
            "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
            "SOURCE": _source_cell(feed),
            "FREQUENCY": _frequency(feed, faq, tpl),
            "LOB": _file_lob_cell(tpl, tab, file, spec),
            "SCHEMA_DRIFT_FLAG": _schema_drift_cell(tpl),
            "SRC_FILE_NAME": _src_file_name_cell(
                tpl, pattern, file.template,
                "from_frd" if feed.file_name_patterns else "from_sttm"),
            "SRC_COLUMNS": _cell(src_columns, "from_sttm"),
            "SRC_DATA_TYPE": src_type_cell,
            "TGT_DATABASE_NAME": _cell(stage.schema_name, "from_frd"),
            "TGT_TABLE_NAME": _cell(stage.table, "from_frd"),
            "TGT_COLUMN_NAMES": _cell(
                ",".join([f.stage_column for f in fields] + [c for c, _t in audit]), "from_sttm"),
            "TGT_DATA_TYPE": _cell(
                ",".join([f.stage_datatype for f in fields] + [t for _c, t in audit]), "from_sttm"),
            "TGT_LOAD_OPTION": _load_option_cell(spec.stage_load_strategy, "STG"),
            "TGT_RJT_TABLE_NAME": _cell(
                reject, "synthetic" if tpl.reject_table_suffix is not None else "from_sttm",
                _TEMPLATE_TOOLTIP.format(citation=tpl.citation)
                if tpl.reject_table_suffix is not None else "stage table + errors suffix"),
            **_recycle_cells(tpl, tab, feed, spec, config, stage.table),
        }
        if config.metadata.claim_type_id_default is not None:
            from codegen.metadata_sheet import _claim_type_cell

            cells["CLAIM_TYPE_ID"] = _claim_type_cell(config)
        extension = PurePosixPath(pattern).suffix.lstrip(".")
        if extension:
            cells["SRC_FORMAT"] = _cell(extension, "from_frd" if feed.file_name_patterns
                                        else "from_sttm", "file pattern extension")
        landing = _landing(feed)
        if landing is not None:
            uri = bool(location_scheme(feed.landing_location))
            cells["SRC_ADLS_PATH"] = _path_cell(
                tpl, tab, "SRC_ADLS_PATH", landing, "from_frd",
                "FRD Structural Metadata → ADLS Location",
                lowered=landing.lower() if _lower_inputs(tpl, uri) else None)
        if spec.delimiter:
            cells["SRC_FILE_DELIMITER"] = _cell(spec.delimiter, "from_frd")
        cells.update(_header_flag_cells(spec, faq, tpl))
        if spec.not_null_columns:
            cells["MANDATORY_FIELD_LIST"] = _cell(",".join(spec.not_null_columns), "from_sttm")
        if key_columns:
            # Unknown (no Primary Key cell) stays blank and open (Chunk A).
            cells["TGT_PRIMARY_KEY"] = _cell(",".join(key_columns), "from_sttm",
                                             "the detail table's Primary Key cells (Stage band)")
        if file.lob:
            cells["TGT_PARTITION_COLUMN"] = _cell(
                tpl.lob_partition_column, "synthetic",
                f"template constant — a per-LOB file partitions on {tpl.lob_partition_column} "
                "(docs/acfc/MULTI_TABLE_DESIGN.md rule 2)")
            cells["TGT_PARTITION_VALUE"] = _cell(file.lob, "from_frd",
                                                 f"this file's LOB — {file.provenance}")
        cells.update(_paths(tpl, tab, feed, stage.table, reject))
        rows.append(_with_constants(tpl, tab, cells))
    return rows


def _recycle_cells(tpl: MetadataTemplateConfig, tab: str, feed: FrdFeed,
                   spec: ResolvedFeedSpec, config: Config, stage_table: str) -> dict:
    """RECYCL_* (first real-row scorecard, 2026-10-08): derived when a document
    states the recycle (the STTM's Recycle Flag cell, the FRD's recycle rule):
    Y, the resolved recycle table, the template's RECYCL_ADLS_PATH shape, the
    stated window. Unstated: by the family convention — blank and open for
    the engineer to confirm, the convention-shaped table / path offered in the
    tooltip (never an asserted N), or the family's N / NA / NA."""
    from codegen.resolve.resolver import side_table_name

    shape = tpl.path_patterns.get(tab, {}).get("RECYCL_ADLS_PATH")
    table = (spec.recycle.recycle_table.table if spec.recycle is not None
             else side_table_name(stage_table, config.naming.recycle_table_suffix))
    landing = _landing(feed)
    path = None
    if shape and landing is not None and not location_scheme(feed.landing_location):
        landing_rel = _landing_rel(tpl, tab, landing)
        path = shape.format(landing=landing, landing_rel=landing_rel,
                            domain_path=_domain_path(landing_rel), stage_table=stage_table,
                            reject_table="", recycle_table=table).replace("//", "/")
    stated = spec.recycle is not None or bool(feed.recycle_rule)
    if stated:
        why = ("the STTM's Recycle Flag cell" if spec.recycle is not None
               else "the FRD's recycle rule")
        cells = {"RECYCL_ENBL_FLG": _cell("Y", "from_sttm" if spec.recycle else "from_frd",
                                          f"recycle stated — {why}")}
        if spec.recycle is not None:
            cells["RECYCL_TBL_NM"] = _cell(table, "from_sttm", "the resolved recycle table "
                                           "(stage table + recycle suffix)")
            cells["RECYCL_RETN_DAYS"] = _cell(str(spec.recycle.spec.recycle_window_days),
                                              "from_sttm", "the recycle window the STTM states")
        if path is not None:
            cells["RECYCL_ADLS_PATH"] = _path_cell(
                tpl, tab, "RECYCL_ADLS_PATH", path, "synthetic",
                _path_tooltip(tpl, tab, "RECYCL_ADLS_PATH", shape))
        return cells
    if tpl.family_conventions.recycle_unstated == "N":
        return {"RECYCL_ENBL_FLG": _cell("N", "from_frd", "no document states a recycle; the "
                                         "family writes N (family convention recycle_unstated: "
                                         f"N; {_family_citation(tpl)})")}
    offer = (f"no document states a recycle (FRD reprocessing / recycle rule, STTM Recycle "
             f"Flag) — confirm; if enabled, the convention-shaped table is {table!r}"
             + (f" and the path {path!r}" if path else ""))
    # Blank cells, never the template's NA constants: open, engineer to confirm.
    return {header: _cell("", "needs_template", offer)
            for header in ("RECYCL_ENBL_FLG", "RECYCL_TBL_NM", "RECYCL_ADLS_PATH")}


def _stg_std(tab, feed, config, spec, faq, tpl, profile=None) -> list[dict]:
    """Rule 4: one row per TABLE with a standard definition — source = its
    stage table, target = its standard table (catalog mapped, step 2)."""
    if spec is None or spec.standard_table is None:
        return []
    files = _feed_files(spec, config)
    lobs = [f.lob for f in files if f.lob]
    generalized = _generalized_pattern(files, tpl, config.extractor.lob_tokens)
    rows = []
    object_ids: list[tuple[_TableGroup, dict]] = []
    for group in _table_groups(spec):
        if group.standard is None:
            continue
        row = _stg_std_row(tab, feed, config, spec, faq, tpl, profile, group, lobs, generalized)
        if tpl.family_conventions.stgdelta_object_id == "from_file":
            cell = _stg_object_id_cell(tpl, group, files)
            if cell is not None:
                row["OBJECT_ID"] = cell
                object_ids.append((group, cell))
        rows.append(row)
    _note_shared_object_ids(object_ids)
    return rows


def _feeding_files(files: list[FeedFile]) -> list[FeedFile]:
    """The files whose rows land in a table of the feed: every file the feed
    receives, for EVERY table (rule 3: each file's ADLS row loads the DETAIL
    table; rule 5: a header / trailer table is split off the same files by the
    DQ rule) — no file feeds only some of the tables."""
    return list(files)


def _note_shared_object_ids(object_ids: list[tuple[_TableGroup, dict]]) -> None:
    """One file's ADLS OBJECT_ID written on SEVERAL STGDELTA rows (one file,
    several tables — e.g. a single-file segmented feed whose H / D / T segments
    are tables): the value stays (OBJECT_ID is per (group, file)), and every
    such cell carries one note, ``stgdelta_object_id_shared:<tables>``. If one
    GROUP_ID and PIPELINE_ID serve those rows, their (GROUP_ID, OBJECT_ID,
    PIPELINE_ID) repeats — the key METADATA_DB_SEMANTICS §5 / §7 states for the
    ADLS tables and only assumes for this one (its open question 7) — and a
    unique key there rejects the second INSERT, rolling the script back."""
    by_number: dict[str, list[tuple[_TableGroup, dict]]] = {}
    for group, cell in object_ids:
        if cell["value"]:
            by_number.setdefault(cell["value"], []).append((group, cell))
    for number, entries in by_number.items():
        if len(entries) < 2:
            continue
        tables = ",".join(group.stage.table for group, _shared in entries)
        note = (f"stgdelta_object_id_shared:{tables} — one file feeds {len(entries)} tables, so "
                f"each STGDELTA row takes its ADLS OBJECT_ID {number} (per (group, file)); "
                "under one GROUP_ID + PIPELINE_ID the key (GROUP_ID, OBJECT_ID, PIPELINE_ID) "
                "repeats and a unique key rejects the second INSERT (metadata_inserts.sql "
                "rolls back) — engineer: a group / pipeline per table, or confirm OBJECT_ID "
                "per table (Friday checklist 13)")
        for _group, cell in entries:
            cell["badge_entry"]["note"] = note


def _stg_object_id_cell(tpl: MetadataTemplateConfig, group: _TableGroup,
                        files: list[FeedFile]) -> dict | None:
    """STGDELTA OBJECT_ID by the family convention ``stgdelta_object_id:
    from_file`` (Chunk D, owner brief 2026-10-09): OBJECT_ID is per (group,
    file), so the row takes the OBJECT_ID of the ADLS_DELTA_INGESTION_DETAILS
    row of THE file that feeds its table — that row's position in the group
    (1..n, ``_adls_delta``). Several files feed it: no single file's id
    applies — open for the engineer, with a note. Both cells are convention
    cells (they keep their own tooltip in the always-blank column). No file
    known: None (the always-blank cell, as without the convention). One file
    feeding several tables: each row gets its id, noted by
    ``_note_shared_object_ids``."""
    feeding = _feeding_files(files)
    if not feeding:
        return None
    citation = _family_citation(tpl)
    if len(feeding) == 1:
        (file,) = feeding
        number = files.index(file) + 1
        pattern = _wildcarded(file.pattern, tpl)
        cell = _cell(str(number), "synthetic",
                     f"template constant — OBJECT_ID is per (group, file): the "
                     f"ADLS_DELTA_INGESTION_DETAILS row of the one file that feeds "
                     f"{group.stage.table} ({pattern}) is object {number} (family convention "
                     f"stgdelta_object_id: from_file; {citation})")
        cell["badge_entry"]["convention"] = True
        return cell
    patterns = [_wildcarded(f.pattern, tpl) for f in feeding]
    listed = ", ".join(patterns[:4]) + (f" … +{len(patterns) - 4}" if len(patterns) > 4 else "")
    cell = _cell("", "needs_template",
                 f"OBJECT_ID is per (group, file) and {len(feeding)} files feed "
                 f"{group.stage.table} ({listed}): no single file's ADLS OBJECT_ID applies — "
                 f"assigned by the engineer (family convention stgdelta_object_id: from_file; "
                 f"{citation})")
    cell["badge_entry"]["convention"] = True
    cell["badge_entry"]["note"] = (
        f"stgdelta_object_id_open:{group.stage.table} — {len(feeding)} files feed it "
        f"({listed}); OBJECT_ID is per (group, file), so the STGDELTA row takes no file's "
        "ADLS OBJECT_ID — left open for the engineer")
    return cell


def _stg_object_name(tpl: MetadataTemplateConfig, table: str, generalized: str) -> dict:
    """STGDELTA OBJECT_NAME by the feed family's convention."""
    convention = tpl.family_conventions
    citation = _family_citation(tpl)
    if convention.stgdelta_object_name == "literal":
        return _cell(convention.stgdelta_object_name_literal, "synthetic",
                     f"template constant — the family's own OBJECT_NAME form, transcribed "
                     f"(no derivation known; {citation})")
    if convention.stgdelta_object_name == "table_name":
        return _cell(table, "from_sttm", f"the table this row moves (family convention; "
                                         f"{citation})")
    return _cell(_object_name(generalized, tpl.object_name_strip_tokens,
                              tpl.object_name_bound_tokens), "from_frd",
                 f"the generalized file pattern {generalized!r} (wildcards and extension "
                 f"removed; family convention, {citation})")


def _stg_std_row(tab, feed, config, spec, faq, tpl, profile, group: _TableGroup,
                 lobs: list[str], generalized: str) -> dict:
    fields = [f for f in group.fields if f.standard_column]
    audit = _group_audit(group, spec, tpl)
    stage = group.stage
    standard = group.standard
    assert standard is not None
    reject = _reject_table(tpl, spec, standard.table)
    if tpl.data_type_style == "base":
        src_types = [f"{_base_type(f.stage_datatype)}:{_base_type(f.standard_datatype)}"
                     for f in fields] + [f"{t}:{t}" for _c, t in audit]
    else:
        src_types = [f"{f.stage_datatype}:{f.standard_datatype}" for f in fields] + [
            f"{t}:{t}" for _c, t in audit]
    cells = {
        "OBJECT_NAME": _stg_object_name(tpl, standard.table, generalized),
        "DOMAIN": _cell(feed.domain or "", "from_frd"),
        "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
        "SOURCE": _source_cell(feed),
        "FREQUENCY": _frequency(feed, faq, tpl),
        "LOB": (_feed_lob(tpl, tab, list(dict.fromkeys(lobs)),
                          "the LOB of the feed's per-LOB files")
                if lobs else
                _feed_lob(tpl, tab, list(spec.lobs),
                          "the feed's LOB (FRD / STTM header block) — no per-LOB file")),
        "SRC_SCHEMA_NAME": _cell(stage.schema_name, "from_frd"),
        "SRC_TABLE_NAME": _cell(stage.table, "from_frd"),
        "SRC_COLUMNS": _cell(
            ",".join([f"{f.stage_column}:{f.standard_column}" for f in fields]
                     + [f"{c}:{c}" for c, _t in audit]), "from_sttm"),
        "SRC_DATA_TYPE": _cell(",".join(src_types), "from_sttm"),
        "TGT_SCHEMA_NAME": _cell(standard.schema_name, "from_frd"),
        "TGT_TABLE_NAME": _cell(standard.table, "from_frd"),
        "TGT_COLUMN_NAMES": _cell(
            ",".join([f.standard_column for f in fields] + [c for c, _t in audit]), "from_sttm"),
        "TGT_DATA_TYPE": _cell(
            ",".join([f.standard_datatype or "" for f in fields] + [t for _c, t in audit]),
            "from_sttm"),
        "TGT_RJT_TABLE_NAME": _cell(
            reject, "synthetic" if tpl.reject_table_suffix is not None else "from_sttm",
            _TEMPLATE_TOOLTIP.format(citation=tpl.citation)
            if tpl.reject_table_suffix is not None else "stage table + errors suffix"),
    }
    for header, table, layer in (("SRC_CATALOG_NAME", stage, "stage"),
                                 ("TGT_CATALOG_NAME", standard, "standard")):
        catalog = _catalog_cell(config, profile, table, layer)
        if catalog is not None:
            cells[header] = catalog
    if spec.standard_load_strategy:
        cells["TGT_LOAD_OPTION"] = _load_option_cell(spec.standard_load_strategy, "STD")
    key_columns = _primary_key(fields, "standard")
    unknown = tpl.family_conventions.stgdelta_unknown_primary_key
    if key_columns:
        cells["TGT_PRIMARY_KEY"] = _cell(",".join(key_columns), "from_sttm",
                                         "the table's Primary Key cells (Standard band)")
    elif unknown:
        # No Primary Key cell: the family's convention value ('NA' for the
        # pair-1 family); "" leaves the cell blank and open.
        cells["TGT_PRIMARY_KEY"] = _cell(
            unknown, "synthetic", "template constant — no Primary Key cell in the table's "
            f"Standard band; family convention ({_family_citation(tpl)})")
    cells.update(_paths(tpl, tab, feed, standard.table, reject))
    return _with_constants(tpl, tab, cells)


def _segment_positions(segment: SegmentSpec) -> tuple[list[str], list[str], list[str]] | None:
    cols, lens, starts = [], [], []
    from codegen.resolve.widths import as_integer

    for f in segment.fields:
        # M9.2: LEN is the RESOLVED byte width — the STTM length verbatim while
        # it is an integer, else what the width chain resolved; never "10,2".
        if f.source_start is None or f.byte_width is None:
            return None
        cols.append(f.stage_column)
        lens.append(f.source_length.strip() if as_integer(f.source_length) is not None
                    else str(f.byte_width))
        starts.append(f.source_start.strip())
    return cols, lens, starts


def _fixed_width_handler(tab, feed, config, spec, faq, tpl) -> list[dict]:
    if spec is None or not spec.is_segmented or not (
            spec.delimiter == "" or any(
                token.lower() in (spec.file_format or "").lower()
                for token in config.extractor.vdd.fixed_width_tokens)):
        return []
    audit = ",".join(c for c, _t in _audit(spec, tpl))
    declared = getattr(faq, "record_type_discriminators", None) if faq is not None else None
    rows = []
    for segment in spec.segments:
        positions = _segment_positions(segment)
        if positions is None:
            continue
        cols, lens, starts = positions
        label = next((f.record_segment_label for f in segment.fields
                      if f.record_segment_label), segment.segment)
        stage = segment.stage_table
        reject = _reject_table(tpl, spec, stage.table)
        cells = {
            "SEGMENT": _cell(label, "from_sttm", "STTM Segment column, verbatim"),
            "COL": _cell(",".join(cols), "from_sttm"),
            "LEN": _cell(",".join(lens), "from_sttm", "STTM source band Length"),
            "start_ind": _cell(",".join(starts), "from_sttm", "STTM source band Start"),
            "TGT_TABLE": _cell(_qualified(stage), "from_frd",
                               ("qualified stage table" + catalog_mapping_note(stage))
                               if catalog_mapping_note(stage) else None),
            "TGT_AUDIT_CLMS": _cell(audit, "from_sttm", "STTM audit rows"),
        }
        process = _process_name(faq)
        if process is not None:
            cells["PROCESS_NAME"] = process
        if (declared is not None and declared.status == "confirmed"
                and tpl.segment_filter_pattern):
            value = getattr(declared, segment.segment.lower(), None)
            if value is not None:
                cells["SEGMENT_FILTER"] = _cell(
                    tpl.segment_filter_pattern.format(value=value), "from_faq",
                    "load-pattern FAQ record_type_discriminators (confirmed) in the "
                    f"template's filter shape ({tpl.citation})")
        cells.update(_paths(tpl, tab, feed, stage.table, reject))
        rows.append(_with_constants(tpl, tab, cells))
    return rows


def _notebook_details(tab, feed, config, spec, faq, tpl) -> list[dict]:
    from codegen.metadata_sheet import _refresh_type_cell

    rows = tpl.template_rows.get(tab) or [{}]
    out = []
    for template_row in rows:
        # Round 4: a row may cite its own reference cell (`_citation`).
        citation = template_row.get("_citation", tpl.citation)
        cells = {
            header: _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(citation=citation))
            for header, value in template_row.items() if not header.startswith("_")
        }
        layer = template_row.get("_layer", "stage")
        if spec is not None:
            strategy = (spec.standard_load_strategy if layer == "standard"
                        else spec.stage_load_strategy)
            if strategy:
                cells["TGT_REFRESH_TYPE"] = _refresh_type_cell(
                    strategy, "STD" if layer == "standard" else "STG", strategy)
        process = _process_name(faq)
        if process is not None:
            cells["PROCESS_NAME"] = process
        notebook = cells.get("DATABRICKS_NOTEBOOK_NAME")
        flow = _ROLE_FLOWS.get(template_row.get("_pipeline_role") or "", "")
        context = {
            **_row_context(feed, faq, cells, template_row.get("_pipeline_role")),
            "notebook_kind": _notebook_kind(flow, feed, spec, tpl, config),
            "layer": layer.capitalize(),
            "notebook": notebook["value"] if notebook is not None else "",
            "pipeline": _role_pipeline_name(feed, faq, tpl, template_row.get("_pipeline_role")),
        }
        _derive(tpl, tab, cells, context)
        out.append(_with_constants(tpl, tab, cells, context, faq))
    return out


# A pipeline role (pipeline_roles / a row's _pipeline_role) as the corpus
# patterns report names the flow (tools/iig_fill_rate.py, iig_keys.yaml flow).
_ROLE_FLOWS = {"file_to_stage": "file_to_stg", "stage_to_standard": "stg_to_std",
               "grand_master": "grand_master", "master": "master"}


def _notebook_kind(flow: str, feed: FrdFeed, spec: ResolvedFeedSpec | None,
                   tpl: MetadataTemplateConfig, config: Config) -> str:
    """The notebook a leg runs (D1 post45, patterns_post45 file_to_stg values):
    stg_to_std; else by the file format — fixed_width (a FixedWidthHandler),
    pipe_segmented (a pipe-delimited H / D / T feed: the PIPE_DELIMITED segment
    handler), delimited — with ``_tpl`` when the subdomain is a TPL one
    (``tpl_subdomains``: the TPL_FileInvokeDQDeltaTable variant)."""
    from codegen.resolve.resolver import _is_fixed_width

    if flow != "file_to_stg":
        return flow
    file_format = (spec.file_format if spec is not None else feed.file_format) or ""
    delimiter = spec.delimiter if spec is not None else feed.delimiter
    segmented = spec.is_segmented if spec is not None else bool(feed.record_segments)
    if _is_fixed_width(file_format, config):
        kind = "fixed_width"
    elif delimiter == "|" and segmented:
        kind = "pipe_segmented"
    else:
        kind = "delimited"
    sub = (feed.sub_domain or "").strip().lower()
    tpl_sub = any(re.search(rf"(?<![a-z0-9]){re.escape(t.lower())}(?![a-z0-9])", sub)
                  for t in tpl.tpl_subdomains if t.strip())
    return f"{kind}_tpl" if tpl_sub else kind


def _row_context(feed: FrdFeed, faq, cells: dict, role: str | None) -> dict:
    """The tokens / row keys of derived_cells and corpus_cells: {source},
    {feed}, the row's flow (its pipeline role) and PIPELINE_FREQUENCY; D1
    post45: {application} (the FAQ application_name, else the feed's SOURCE —
    the schedule's APPLICATION_NAME default), {freq} (the feed's FREQUENCY
    token, title case: Daily / Weekly / Monthly) and {domain}."""
    frequency = cells.get("PIPELINE_FREQUENCY")
    stated = getattr(faq, "application_name", None) if faq is not None else None
    application = (str(stated.value).strip() if stated is not None
                   and stated.source != "unknown" and str(stated.value).strip()
                   else _source_value(feed))
    freq = str(_frequency(feed, faq)["value"] or "").strip()
    return {"source": _source_value(feed), "feed": _feed_token(feed, faq)[0],
            "flow": _ROLE_FLOWS.get(role or "", role or ""),
            "frequency": str(frequency["value"] or "") if frequency is not None else "",
            "application": application, "freq": freq[:1].upper() + freq[1:].lower(),
            "domain": feed.domain or ""}


def _role_pipeline_name(feed: FrdFeed, faq, tpl: MetadataTemplateConfig,
                        role: str | None) -> str:
    """The schedule's PIPELINE_NAME of ``role`` (pipeline_roles, the same
    {feed} token) — a notebook row runs in its leg's pipeline."""
    match = next((r for r in tpl.pipeline_roles if r.role == role), None)
    if match is None:
        return ""
    token, _source = _feed_token(feed, faq)
    return match.name.format(feed=token)


def _date_rule(tpl: MetadataTemplateConfig, fields: list[SttmField]):
    regex = re.compile(tpl.date_format_rule_regex, re.IGNORECASE)
    columns, params = [], []
    for f in fields:
        match = regex.match(f.value_spec or "")
        if match is None:
            continue
        columns.append(f.stage_column)
        param = tpl.date_format_param_joiner.join(match.groups())
        if param not in params:
            params.append(param)
    return columns, params


def _by_type_order(fields: list[SttmField], type_order: list[str]) -> list[SttmField]:
    order = [t.lower() for t in type_order]

    def _rank(f: SttmField) -> int:
        base = _base_type(f.stage_datatype).lower()
        return order.index(base) if base in order else len(order)

    return sorted(fields, key=_rank)


def _dq_citation(tpl: MetadataTemplateConfig, kind: str) -> str:
    return tpl.dq_citations.get(kind) or tpl.citation


def _dq_head(tpl: MetadataTemplateConfig, kind: str) -> dict:
    """RULE_CLASS (+ RULE_TYPE when the kind has its own) and the kind's
    constant parameters (dq_params) — every one a cited template constant."""
    tooltip = _TEMPLATE_TOOLTIP.format(citation=_dq_citation(tpl, kind))
    cells = {"RULE_CLASS": _cell(tpl.dq_rule_classes.get(kind, kind), "synthetic", tooltip)}
    if kind in tpl.dq_rule_types:
        cells["RULE_TYPE"] = _cell(tpl.dq_rule_types[kind], "synthetic", tooltip)
    for header, value in tpl.dq_params.get(kind, {}).items():
        cells[header] = _cell(value, "synthetic", tooltip)
    return cells


def _split_groups(groups: list[_TableGroup], detail: _TableGroup) -> list[_TableGroup]:
    """The header / trailer tables other than the detail, header first."""
    split = [g for g in groups if g is not detail
             and any(s.segment in ("Header", "Trailer") for s in g.segments)]
    order = {"Header": 0, "Trailer": 1}
    split.sort(key=lambda g: min(order.get(s.segment, 2) for s in g.segments))
    return split


def _stage_catalog(config: Config, table) -> str:
    if table.catalog:
        return table.catalog
    from codegen.emit.framework import _config_default_catalog

    return _config_default_catalog(config, config.conventions.get(None), "stage") or ""


def _split_rule(tpl: MetadataTemplateConfig, config: Config, groups: list[_TableGroup],
                detail: _TableGroup, feed: FrdFeed | None = None) -> dict | None:
    """Rule 5: the LoadHeaderAndTrailerToSeparateTablesRule cells shared by
    every file — only when the header / trailer segments land in a table
    other than the detail. ``dq_split_style`` header_columns (pair 1):
    SOURCE_COLUMN = the header table's columns; TARGET_COLUMN =
    <catalog>,<schema>,<header table>,<trailer table>; INPUT_PARAM per file.
    header_and_trailer (the CAQH golden, D1 post44): SOURCE_COLUMN = header
    columns '|' trailer columns; TARGET_COLUMN = <catalog>,<schema>,<table>,
    <location> per table (dq_split_location)."""
    split = _split_groups(groups, detail)
    if not split:
        return None
    header = next((g for g in split if any(s.segment == "Header" for s in g.segments)), split[0])
    stage = header.stage
    catalog = _stage_catalog(config, stage)
    cells = _dq_head(tpl, "header_trailer_split")
    if tpl.dq_split_style == "header_and_trailer":
        landing = _landing(feed) if feed is not None else None
        container = tpl.constants.get("ADLS_DELTA_INGESTION_DETAILS", {}).get(
            "TGT_CONTAINER_NAME", "")
        parts: list[str] = []
        located = True
        for group in split:
            location = None
            account = (tpl.environment.entry.storage_account
                       if tpl.environment is not None else "")
            if tpl.dq_split_location and landing is not None and container and (
                    account or "{storage_account}" not in tpl.dq_split_location):
                rel = _landing_rel(tpl, "ADLS_DELTA_INGESTION_DETAILS", landing)
                location = tpl.dq_split_location.format(
                    container=container, domain_path=_domain_path(rel), table=group.stage.table,
                    storage_account=account)
            located = located and location is not None
            parts += [p for p in (_stage_catalog(config, group.stage), group.stage.schema_name)
                      if p] + [group.stage.table] + ([location] if location else [])
        cells["SOURCE_COLUMN"] = _cell(
            "|".join(",".join(f.stage_column for f in g.fields) for g in split), "from_sttm",
            "the header table's columns '|' the trailer table's (STTM Stage band; "
            f"{_dq_citation(tpl, 'header_trailer_split')})")
        target = _cell(",".join(parts), "from_sttm",
                       "<catalog>,<schema>,<table>,<location> per header / trailer table "
                       f"({_dq_citation(tpl, 'header_trailer_split')})"
                       + catalog_mapping_note(stage))
        if not located:
            target = _cell("", "needs_template", "no landing / container / location shape to "
                           "build the tables' locations from — open")
            needs_account = "{storage_account}" in (tpl.dq_split_location or "")
            if needs_account and not account:
                where = (f"environment {tpl.environment.name} ({tpl.environment.source}) states "
                         "no storage_account" if tpl.environment is not None else
                         "no environment is defined (environments:)")
                target["badge_entry"]["note"] = (
                    f"iig_env:DATA_QUALITY_RULES.TARGET_COLUMN — the tables' locations need the "
                    f"storage account: {where}; left open")
        elif tpl.environment is not None and "{storage_account}" in tpl.dq_split_location \
                and not is_placeholder(target["value"]):
            env = tpl.environment
            target["badge_entry"]["note"] = (
                f"iig_env:DATA_QUALITY_RULES.TARGET_COLUMN — the tables' locations in storage "
                f"account {env.entry.storage_account!r}, container {container!r} from "
                f"environment {env.name} ({env.source})")
        cells["TARGET_COLUMN"] = target
        return cells
    target = ",".join([p for p in (catalog, stage.schema_name) if p]
                      + [g.stage.table for g in split])
    cells["SOURCE_COLUMN"] = _cell(",".join(f.stage_column for f in header.fields), "from_sttm",
                                   f"the header table's columns ({stage.table}, STTM Stage band)")
    cells["TARGET_COLUMN"] = _cell(target, "from_sttm",
                                   "framework convention <catalog>,<schema>,<header table>,"
                                   "<trailer table> (docs/acfc/MULTI_TABLE_DESIGN.md rule 5)"
                                   + catalog_mapping_note(stage))
    return cells


def _audit_literals(spec: ResolvedFeedSpec, tpl: MetadataTemplateConfig) -> list[tuple[str, str]]:
    """(audit column, literal) for every audit row whose load rule names a
    literal default (dq_literal_regex: "Default to 'X'"), STTM order."""
    regex = re.compile(tpl.dq_literal_regex)
    found: dict[str, str] = {}
    audits = [*spec.audit_columns, *(a for s in spec.segments for a in s.audit_columns or [])]
    for audit in audits:
        match = regex.search(getattr(audit, "value_spec", None) or "")
        if match is not None:
            found.setdefault(audit.column, match.group(1).strip())
    return list(found.items())


def _columns_rule(tpl: MetadataTemplateConfig, kind: str, columns: list[str], why: str,
                  **extra: dict) -> dict:
    joined = ",".join(columns)
    return {**_dq_head(tpl, kind), "SOURCE_COLUMN": _cell(joined, "from_sttm", why),
            "TARGET_COLUMN": _cell(joined, "from_sttm", why), **extra}


def _stage_dq_rules(kind: str, tpl: MetadataTemplateConfig, config: Config, feed: FrdFeed,
                    spec: ResolvedFeedSpec, groups: list[_TableGroup],
                    detail: _TableGroup) -> list[dict]:
    """A stage-leg rule kind's rows, the same for every file (OBJECT_ID = the
    file's ADLS object)."""
    fields = detail.fields
    stage = detail.stage
    if kind == "header_trailer_split":
        split = _split_rule(tpl, config, groups, detail, feed)
        if split is None:
            return []
        per_file = {} if "INPUT_PARAM" in split else {"_per_file": "INPUT_PARAM"}
        return [{**split, **per_file}]
    if kind == "add_custom_columns":
        # D1 post44: a header / trailer feed's audit literal (the CAQH golden's
        # FILE_TYPE 'CAQH' row); none written for a flat feed.
        if not _split_groups(groups, detail):
            return []
        return [{**_dq_head(tpl, kind),
                 "SOURCE_COLUMN": _cell(literal, "from_sttm",
                                        f"the STTM's audit row {column}: a literal default"),
                 "TARGET_COLUMN": _cell(column, "from_sttm", "the audit column (STTM)")}
                for column, literal in _audit_literals(spec, tpl)]
    if kind in ("null_check", "dedup"):
        # D1 post45: the baseline PER FEED — once, on the first file's object
        # (NullCheckRule 186 rows / 114 workbooks, DeDuplicationRule 160 / 90: ~1.6
        # per workbook, not one per file); over the detail table's key columns.
        keyed = set(_primary_key(fields, "stage")) | set(spec.not_null_columns)
        columns = [f.stage_column for f in fields if f.stage_column in keyed]
        if not columns:
            rule = _dq_head(tpl, kind)
            rule["SOURCE_COLUMN"] = _cell("", "needs_template",
                                          "the STTM marks no Primary Key / not-null column on "
                                          "the detail table — open")
            return [{**rule, "_per_feed": True}]
        return [{**_columns_rule(tpl, kind, columns, "the detail table's Primary Key / "
                                                     "not-null columns (STTM Stage band)"),
                 "_per_feed": True}]
    if kind == "referential_check":
        recycle = spec.recycle
        if recycle is None:
            return []
        applies = recycle.spec.applies_to.strip().lower()
        field = next((f for f in fields if applies in ((f.source_column or "").strip().lower(),
                                                       f.stage_column.lower())), None)
        if field is None:
            return []
        return [{**_dq_head(tpl, kind),
                 "SOURCE_COLUMN": _cell(field.stage_column, "from_sttm",
                                        f"the STTM's lookup: {recycle.spec.validation!r} "
                                        f"(reference {recycle.reference_table})")}]
    if kind == "date_format":
        columns, params = _date_rule(tpl, fields)
        if not columns:
            return []
        joined = ",".join(columns)
        return [{**_dq_head(tpl, kind),
                 "SOURCE_COLUMN": _cell(joined, "from_sttm", "STTM Load Rule: date conversion"),
                 "INPUT_PARAM": _cell(";".join(params), "from_sttm",
                                      "STTM Load Rule text, formats in the template's shape"),
                 "TARGET_COLUMN": _cell(joined, "from_sttm")}]
    if kind == "data_type_cast":
        typed = [f for f in fields if _base_type(f.stage_datatype).lower() != "string"]
        if not typed:
            return []
        typed = _by_type_order(typed, tpl.cast_type_order)  # stable within a type
        return [_columns_rule(tpl, kind, [f.stage_column for f in typed],
                              "STTM stage columns typed other than String",
                              INPUT_PARAM=_cell(_qualified(stage), "from_frd",
                                                "qualified stage table"
                                                + catalog_mapping_note(stage)))]
    return []


_STD_KINDS = ("lr_trim", "std_date_conversion", "std_data_type_cast")


def _std_dq_rules(kind: str, tpl: MetadataTemplateConfig, group: _TableGroup) -> list[dict]:
    """A STDDelta rule kind's rows for one standard table (D1 post44: the SFMC
    reference rows' shapes — SOURCE_COLUMN = TARGET_COLUMN the columns)."""
    standard = group.standard
    fields = [f for f in group.fields if f.standard_column]
    if standard is None or not fields:
        return []
    if kind == "lr_trim":
        return [_columns_rule(tpl, kind, [f.standard_column for f in fields],
                              f"every column of the standard table {standard.table} (STTM "
                              "Standard band)")]
    if kind == "std_data_type_cast":
        typed = [f for f in fields if _base_type(f.standard_datatype).lower() != "string"]
        if not typed:
            return []
        order = [t.lower() for t in tpl.cast_type_order]
        typed = sorted(typed, key=lambda f: order.index(_base_type(f.standard_datatype).lower())
                       if _base_type(f.standard_datatype).lower() in order else len(order))
        return [_columns_rule(tpl, kind, [f.standard_column for f in typed],
                              "standard columns typed other than String (STTM Standard band)",
                              INPUT_PARAM=_cell(_qualified(standard), "from_frd",
                                                "qualified standard table"
                                                + catalog_mapping_note(standard)))]
    if kind == "std_date_conversion":
        regex = re.compile(tpl.date_format_rule_regex, re.IGNORECASE)
        rows = []
        for f in fields:
            if _base_type(f.standard_datatype).lower() != "date":
                continue
            match = regex.match(f.value_spec or "")
            param = (_cell(tpl.date_format_param_joiner.join(match.groups()), "from_sttm",
                           "STTM Load Rule text, formats in the template's shape")
                     if match is not None else
                     _cell("", "needs_template", "the STTM states no source / target date "
                                                 f"format for {f.standard_column} — open"))
            rows.append(_columns_rule(tpl, kind, [f.standard_column],
                                      "a Date-typed standard column (STTM Standard band)",
                                      INPUT_PARAM=param))
        return rows
    return []


def _dq_rules(tab, feed, config, spec, faq, tpl) -> list[dict]:  # noqa: C901
    """Rule 5 + the STTM-derived rules. Stage-leg kinds are keyed per FILE
    (decision 2026-10-07): for each ADLS object its rows in ``dq_rules``
    order, OBJECT_ID = the file's position, as on the ADLS row. STDDelta kinds
    (D1 post44: lr_trim, std_date_conversion, std_data_type_cast) per STANDARD
    table, OBJECT_ID = its STGDELTA row's. Rule classes no input derives are
    not generated — the review copy lists 'additional DQ rules — Engineer'
    per file (iig_review)."""
    if spec is None or not tpl.dq_rules:
        return []
    groups = _table_groups(spec)
    detail = _detail_group(groups)
    files = (_feed_files(spec, config) if tpl.rows_per_file_pattern else [None])
    rules = [rule for kind in tpl.dq_rules if kind not in _STD_KINDS
             for rule in _stage_dq_rules(kind, tpl, config, feed, spec, groups, detail)]
    rows = []
    for number, file in enumerate(files, start=1):
        pattern = _wildcarded(file.pattern, tpl) if file is not None else None
        kept = [rule for rule in rules if number == 1 or not rule.get("_per_feed")]
        for index, rule in enumerate(kept, start=1):
            cells = {k: v for k, v in rule.items() if not k.startswith("_")}
            if rule.get("_per_file") == "INPUT_PARAM" and pattern is not None:
                cells["INPUT_PARAM"] = _cell(pattern, "from_frd",
                                             "the object's SRC_FILE_NAME (ADLS row "
                                             f"OBJECT_ID {number})")
            cells["SEQUENCE_NO"] = _cell(index, "synthetic",
                                         _TEMPLATE_TOOLTIP.format(citation=tpl.citation))
            if pattern is not None:
                cells["OBJECT_ID"] = _sequence_cell(number, f"file ({pattern})")
            rows.append(_with_constants(tpl, tab, cells, {}, faq))
    std_kinds = [kind for kind in tpl.dq_rules if kind in _STD_KINDS]
    if std_kinds and spec.standard_table is not None:
        all_files = _feed_files(spec, config)
        for group in groups:
            std_rules = [rule for kind in std_kinds for rule in _std_dq_rules(kind, tpl, group)]
            object_id = (_stg_object_id_cell(tpl, group, all_files)
                         if tpl.family_conventions.stgdelta_object_id == "from_file" else None)
            for index, rule in enumerate(std_rules, start=1):
                cells = dict(rule)
                cells["SEQUENCE_NO"] = _cell(index, "synthetic",
                                             _TEMPLATE_TOOLTIP.format(citation=tpl.citation))
                if object_id is not None:
                    cells["OBJECT_ID"] = dict(object_id)
                rows.append(_with_constants(tpl, tab, cells))
    return rows


def _email_templates(tab, feed, config, spec, faq, tpl) -> list[dict]:
    recipients = ";".join(config.job.notification_emails)
    rows = tpl.template_rows.get(tab) or [{}]
    out = []
    for template_row in rows:
        cells = {
            header: _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(citation=tpl.citation))
            for header, value in template_row.items() if not header.startswith("_")
        }
        process = _process_name(faq)
        if process is not None:
            cells["TEMPLATE_NAME"] = process
            cells["PROCESS_NAME"] = process
        cells["EMAIL_TO"] = _cell(recipients, "from_standards",
                                  "EDO coding standard: success AND failure alerts to the "
                                  "prod-support DL (synthetic stand-in address)")
        context = {**_row_context(feed, faq, cells, None),
                   "outcome": template_row.get("_outcome", ""),
                   "sender": config.job.notification_sender,
                   "status": str(template_row.get("STATUS") or "")}
        _derive(tpl, tab, cells, context)
        # D1 post45: the subject / body's {template_name} is the row's TEMPLATE_NAME
        context["template_name"] = _cell_text(cells.get("TEMPLATE_NAME")).strip()
        out.append(_with_constants(tpl, tab, cells, context, faq))
    return out


_BUILDERS = {
    "DATA_FACTORY_PIPELINE_SCHEDULE": _pipeline_schedule,
    "FILE_ADLS_INGESTION_DETAILS": _file_adls,
    "ADLS_DELTA_INGESTION_DETAILS": _adls_delta,
    "STGDELTA_STDDELTA_INGESTION_DET": _stg_std,
    "ADLS_FIXED_WIDTH_HANDLER": _fixed_width_handler,
    "DATABRICKS_NOTEBOOK_DETAILS": _notebook_details,
    "DATA_QUALITY_RULES": _dq_rules,
    "EMAIL_TEMPLATE_CONFIG": _email_templates,
}


def template_tab_rows(tab: str, feed: FrdFeed, config: Config, spec: ResolvedFeedSpec | None,
                      faq, tpl: MetadataTemplateConfig, profile=None) -> list[dict]:
    """Cells for one tab of a non-default IIG template (rows without the
    header/always_blank assembly, which ``metadata_sheet._row`` does).
    ``profile`` = the run's conventions profile (its default_catalog is the
    catalog chain's last link)."""
    builder = _BUILDERS.get(tab)
    if builder is None:
        return []
    if tpl.environment is None:
        # 2026-10-14: the run's environment fills the environment_cells (callers
        # through metadata_sheet_payload get it applied already)
        from codegen.environments import apply_environment

        tpl = apply_environment(tpl, config)
    if builder is _stg_std:
        return builder(tab, feed, config, spec, faq, tpl, profile=profile)
    return builder(tab, feed, config, spec, faq, tpl)


def blank_flags(payload: dict) -> list[str]:
    """One ``iig_blank:<TAB>: <HEADER>, <HEADER>, …`` flag per sheet listing
    (in header order) every column left blank (needs template) in at least
    one row — the pinned blank-and-flag list, grouped so the gate output
    stays legible (M6)."""
    flags: list[str] = []
    for tab_name, tab in payload["tabs"].items():
        blank: list[str] = []
        for header in tab["headers"]:
            for row in tab["rows"]:
                entry = row["badges"].get(header)
                if (entry is not None and entry["badge"] == "needs_template"
                        and row["values"][header] in ("", None)):
                    blank.append(header)
                    break
        if blank:
            flags.append(f"iig_blank:{tab_name}: {', '.join(blank)}")
    return flags


def shape_flags(payload: dict) -> list[str]:
    """The notes the path derivation left on cells, once each: M10.2's
    ``iig_path_shape_on_uri:`` (a template shape that prefixes the landing,
    applied to a location URI) and the first ACFC run's ``path_normalised:``
    (an input path normalised — before / after). Empty for a clean
    folder-path landing."""
    return list(dict.fromkeys(
        note
        for tab in payload["tabs"].values()
        for row in tab["rows"]
        for entry in row["badges"].values() if entry is not None
        for note in (entry.get("note"), entry.get("path_note")) if note))


def blank_columns(flags: list[str]) -> dict[str, list[str]]:
    """Inverse of :func:`blank_flags` — sheet -> blank headers."""
    out: dict[str, list[str]] = {}
    for flag in flags:
        if not flag.startswith("iig_blank:"):
            continue
        tab, _sep, columns = flag[len("iig_blank:"):].partition(": ")
        out[tab] = [c for c in columns.split(", ") if c]
    return out


__all__ = ["template_tab_rows", "blank_flags", "blank_columns"]
