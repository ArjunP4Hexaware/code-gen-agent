"""Join one FRD feed contract with one STTM mapping contract.

Produces one :class:`ResolvedFeedSpec` per feed. Every disagreement between
the two contracts is collected and raised as a single loud
:class:`ContractMismatchError` naming the feed, the field, and both values —
never silently reconciled.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from codegen.config import Config
from codegen.contracts.frd import FrdContract, FrdFeed
from codegen.contracts.resolved import (
    ResolvedFeedSpec,
    ResolvedRecycle,
    ResolvedTable,
    SegmentSpec,
)
from codegen.contracts.sttm import SttmContract, SttmFeed, SttmField
from codegen.run_errors import Coord, located

# Format -> implied delimiter when a contract leaves it null.
_FORMAT_DELIMITERS = {"csv": ",", "psv": "|"}

# Parses the STTM recycle validation text. Canonical form:
# "Match member_id against SBSB_ID in PR_STD.FACETS.CMC_SBSB_SUBSC where GRGR_CK = 31"
_REFERENCE_RE = re.compile(
    r"against\s+(?P<id_column>\w+)\s+in\s+(?P<table>[\w.]+)"
    r"(?:\s+where\s+(?P<filter>.+?))?\s*$",
    re.IGNORECASE,
)

# Client phrasing, carried VERBATIM from workbooks/FRDs (never rewritten), e.g.
# "Check with SUBS_ID from CoreMember in the PR_STD.COREMEMBER.CM_SUBS_MASTER
#  FOR GRP_CK = 47, if available process it else ..." — the table is the
# dotted name, with or without a prose alias ("from CoreMember in the ...")
# before it; the filter runs to the first comma/newline.
_CLIENT_REFERENCE_RE = re.compile(
    r"check\s+with\s+(?P<id_column>\w+)\s+from\s+"
    r"(?:[\w ]+?\s+in\s+(?:the\s+)?)?"
    r"(?P<table>\w+(?:\.\w+)+)"
    r"(?:\s+for\s+(?P<filter>[^,\n)]+))?",
    re.IGNORECASE,
)

_WINDOW_DAYS_RE = re.compile(r"(\d+)\s*days?", re.IGNORECASE)

# FRD-driven AS-IS switch evidence (the character class covers space, ASCII
# hyphen, and the non-breaking hyphen real FRD text uses).
_AS_IS_RE = re.compile(r"\bAS[\s\-‑]?IS\b", re.IGNORECASE)


class MismatchItem(str):
    """One mismatch line (the quoted text) tagged with its kind
    (``codegen.run_errors.MISMATCH_LABELS``) and the names it covers — used
    only to COUNT distinct names (three segments naming one table = 1 table);
    the names are never printed by the coordinates tier."""

    kind: str
    count: int
    names: tuple[str, ...]
    # post57: a value.unstated item names the FRD contract field it leaves
    # empty (``file_format``, ``stage_target.load_strategy``) and the places
    # searched (vocabulary labels, never a value) — its QUESTION line.
    field: str | None
    searched: tuple[str, ...]


def mismatch_item(kind: str, text: str, count: int = 1,
                  names: tuple | list = (), *, field: str | None = None,
                  searched: tuple | list = ()) -> MismatchItem:
    item = MismatchItem(text)
    item.kind = kind
    item.names = tuple(str(n) for n in names)
    item.count = len(set(item.names)) if item.names else max(int(count), 1)
    item.field = field
    item.searched = tuple(str(s) for s in searched)
    return item


UNSTATED = "value.unstated"


@dataclass(frozen=True)
class UnstatedValue:
    """One value no document states (post57): a QUESTION, never a FAIL.
    ``key`` = the answers-file key (``feeds[<i>].<field>``, under gaps:);
    ``searched`` = where the run looked (vocabulary labels only)."""

    key: str
    field: str
    searched: tuple[str, ...]
    feed_id: str
    position: int | None = None
    of: int | None = None

    @property
    def reason(self) -> str:
        where = f"feed {self.position} of {self.of}; " if self.position else ""
        return (f"value stated in no document ({where}contract field {self.field}); searched: "
                f"{', '.join(self.searched) or 'the FRD'} - answer the value under gaps: "
                "in answers.yaml and rerun generate --answers")


def _mismatch_counts(errors: list[str]) -> dict[str, int]:
    """kind -> distinct names (named items) + count (unnamed items)."""
    named: dict[str, set[str]] = {}
    counts: dict[str, int] = {}
    for error in errors:
        kind = getattr(error, "kind", "other")
        names = getattr(error, "names", ())
        if names:
            named.setdefault(kind, set()).update(names)
        else:
            counts[kind] = counts.get(kind, 0) + getattr(error, "count", 1)
    for kind, names in named.items():
        counts[kind] = counts.get(kind, 0) + len(names)
    return counts


class ContractMismatchError(ValueError):
    """The FRD and STTM contracts disagree; generation must not proceed.

    D1 post51 addendum 4: the first line carries the summary as COUNTS
    (``self.counts``, by kind) — the coordinates tier prints only those
    ("contract mismatch, feed 2 of 3: 1 table only in FRD, 2 value conflicts");
    the names stay on the bullet lines (the full tier)."""

    def __init__(self, feed: str, errors: list[str]) -> None:
        from codegen.run_errors import mismatch_summary

        self.feed = feed
        self.errors = errors
        self.counts: dict[str, int] = _mismatch_counts(errors)
        bullet_list = "\n  - ".join(errors)
        super().__init__(f"contract mismatch for feed '{feed}' ({mismatch_summary(self.counts)})"
                         f":\n  - {bullet_list}")


class ContractUnstatedError(ContractMismatchError):
    """post57 (D1 post55 pairs 03 / 04): every disagreement of a feed is a
    value NO document states — NEEDS_ANSWERS (exit 3, one QUESTION per value),
    not a contract mismatch. Raised by :func:`resolve_feeds` once every feed is
    resolved: ``specs`` = the feeds that DID resolve (generated as usual),
    ``questions`` = the :class:`UnstatedValue` items of the others. A feed with
    a genuine conflict (two documents, two values) still raises
    :class:`ContractMismatchError`."""

    def __init__(self, feed: str, errors: list[str], questions: list[UnstatedValue],
                 specs: list | None = None) -> None:
        super().__init__(feed, errors)
        self.questions = list(questions)
        self.specs = list(specs or [])


def _unstated_questions(errors: list[str], feed_id: str, feed_index: int,
                        position: int | None, of: int | None) -> list[UnstatedValue]:
    """One question per unstated FIELD (two checks of one field merge)."""
    merged: dict[str, list[str]] = {}
    for error in errors:
        field = getattr(error, "field", None) or "value"
        merged.setdefault(field, [])
        for place in getattr(error, "searched", ()):
            if place not in merged[field]:
                merged[field].append(place)
    return [UnstatedValue(f"feeds[{feed_index}].{field}", field, tuple(places), feed_id,
                          position, of) for field, places in merged.items()]


# post57: what an unstated value's answer sets on the FRD feed at generate time
# (the layout stage takes the same gaps: keys).
_UNSTATED_ANSWERS = {"file_format": "text", "delimiter": "text",
                     "stage_target.load_strategy": "strategy", "lobs": "list",
                     "file_name_patterns": "list", "file_patterns": "list",
                     # post74: the IIG landing cell's question sets the landing
                     "src_adls_path": "text"}
_UNSTATED_TARGET = {"file_patterns": "file_name_patterns", "src_adls_path": "landing_location"}


def _answered_unstated(frd_feed: FrdFeed, gaps: dict[str, str] | None, feed_index: int,
                       flags: list[str]) -> FrdFeed:
    """A ``gaps:`` answer for a value the FRD leaves empty (the QUESTION of
    :class:`UnstatedValue`) fills it, flagged ``frd_unstated:<field>
    source_used:user``; a value the FRD states is never overwritten."""
    from codegen.layout.resolve import _feed_get, _feed_set
    from codegen.resolve.gapfill import Statement, canonical_strategy, fill_flag

    feed_id = normalize_feed_name(frd_feed.feed_name)
    for field, kind in _UNSTATED_ANSWERS.items():
        answer = str((gaps or {}).get(f"feeds[{feed_index}].{field}")
                     or (gaps or {}).get(f"feeds.{feed_id}.{field}") or "").strip()
        target = _UNSTATED_TARGET.get(field, field)
        if not answer or _feed_get(frd_feed, target) not in (None, "", []):
            continue
        if kind == "list":
            value = [v.strip() for v in re.split(r"[,;\n]+", answer) if v.strip()]
        elif kind == "strategy":
            value = canonical_strategy(answer) or answer
        else:
            value = answer
        frd_feed = _feed_set(frd_feed, target, value)
        flags.append(fill_flag(target, Statement(answer, "user",
                                                 f"answers gaps: feeds[{feed_index}].{field}")))
    return frd_feed


def normalize_feed_name(name: str) -> str:
    """FRD display name -> join key: lowercase, runs of non-alphanumerics -> _."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def side_table_name(stage_table: str, suffix: str) -> str:
    """Derive a side-table name, following the stage table's case style."""
    if stage_table.isupper():
        return stage_table + suffix.upper()
    return stage_table + suffix.lower()


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_table_name(name: str) -> tuple[str, bool]:
    """(comparison form, was qualified) of a table name as a document writes
    it (M9.3): quotes / backticks / brackets dropped, case folded, and a
    ``catalog.schema.table`` / ``schema.table`` spelling reduced to its last
    part — Databricks identifiers are case-insensitive and one document may
    qualify a name the other writes bare."""
    parts = [p.strip().strip("`\"'[]").strip() for p in name.strip().split(".")]
    parts = [p for p in parts if p]
    return (parts[-1].lower() if parts else ""), len(parts) > 1


def _table_in(table: str, stated: list[str], side: str, other: str,
              flags: list[str]) -> bool:
    """True when ``table`` is among ``stated`` by normalized name. A match
    that is not literal is reported: which spelling differed and which side
    was schema-qualified."""
    if table in stated:
        return True
    wanted, table_qualified = normalize_table_name(table)
    for candidate in stated:
        name, candidate_qualified = normalize_table_name(candidate)
        if name and name == wanted:
            qualified = [label for label, q in ((side, table_qualified),
                                                (other, candidate_qualified)) if q]
            flag = (f"table_name_normalized: {side} {table!r} ↔ {other} {candidate!r} — matched "
                    "ignoring case / quotes / qualification; "
                    + (f"{' and '.join(qualified)} schema-qualified" if qualified
                       else "neither side schema-qualified"))
            if flag not in flags:
                flags.append(flag)
            return True
    return False


def _resolve_widths(sttm_feed: SttmFeed, vdd, feed_index: int, flags: list[str]) -> SttmFeed:
    """Links 3-4 of the width chain (codegen.resolve.widths) for every
    positional field the STTM left without a byte width: the VDD's span for
    the same field (normalized name, and segment when both documents are
    segmented), then the person's answer. Flagged with the cells; a field no
    link resolves stays open — the fixed-width template stops on it, naming
    the question to answer."""
    from codegen.resolve.widths import as_integer, normalize_field_name, width_key

    vdd_fields = list(getattr(vdd, "fields", []) or [])
    by_segment = sttm_feed.is_segmented and any(f.segment for f in vdd_fields)
    index: dict[tuple, list] = {}
    for vf in vdd_fields:
        key = ((vf.segment_canonical or vf.segment) if by_segment else None,
               normalize_field_name(vf.name))
        index.setdefault(key, []).append(vf)

    def vdd_width(vf) -> tuple[int | None, str]:
        if vf.start is not None and vf.end is not None and vf.end >= vf.start:
            cells = " / ".join(vf.cells[a].a1 for a in ("start", "end") if a in vf.cells)
            return vf.end - vf.start + 1, f"VDD {cells or vf.sheet}: end {vf.end} - start " \
                                          f"{vf.start} + 1"
        if vf.length is not None and vf.length > 0:
            cell = vf.cells["length"].a1 if "length" in vf.cells else vf.sheet
            return vf.length, f"VDD {cell}: Length {vf.length} (the row states no end)"
        return None, ""

    fields = []
    for f in sttm_feed.fields:
        if f.byte_width is not None or as_integer(f.source_start) is None:
            fields.append(f)
            continue
        label = " ".join(f.source_column.split())
        key = (f.record_segment if by_segment else None, normalize_field_name(f.source_column))
        stated = {w: cite for w, cite in (vdd_width(vf) for vf in index.get(key, []))
                  if w is not None}
        if len(stated) == 1:
            (width, cite), = stated.items()
            flags.append(f"width_from_vdd:{label} — {cite} = {width} (matched by field name"
                         f"{' + segment ' + repr(f.record_segment) if by_segment else ''})")
            fields.append(f.model_copy(update={"source_width": width}))
        elif f.width_answer is not None:
            flags.append(f"width_from_user:{label} — no document states the width (STTM length "
                         f"{f.source_length!r}, no STTM end, "
                         f"{'VDD rows disagree' if stated else 'no VDD span'}); the person "
                         f"answered {width_key(feed_index, f.source_column)} = {f.width_answer}")
            fields.append(f.model_copy(update={"source_width": f.width_answer}))
        else:
            fields.append(f)
    return sttm_feed.model_copy(update={"fields": fields})


def _is_fixed_width(file_format: str | None, config: Config) -> bool:
    fmt = (file_format or "").lower()
    return any(token.lower() in fmt for token in config.extractor.vdd.fixed_width_tokens)


_DELIMITER_CHARS = "|,;^~\t:"


def delimiter_char(value: str | None, words: dict[str, str]) -> str | None:
    """The delimiter CHARACTER a stated value means: a single character as
    is, a word ("Pipe", "comma delimited", "TAB") through
    ``extractor.delimiter_words``, a character quoted inside a phrase
    ("Pipe (|)"); None when the value names none (prose such as "File Data
    Ingestion"). Every artefact writes the character, never the word."""
    if value is None or value == "":
        return None
    if len(value) == 1:
        return value
    text = value.strip()
    if len(text) == 1:
        return text
    if text.lower() in ("\\t", "\t"):
        return "\t"
    for word in re.findall(r"[a-z]+", text.lower()):
        if word in words:
            return words[word]
    quoted = [c for c in text if c in _DELIMITER_CHARS]
    return quoted[0] if len(set(quoted)) == 1 else None


def _resolve_delimiter(frd_feed: FrdFeed, sttm_feed: SttmFeed, errors: list[str],
                       config: Config | None = None, flags: list[str] | None = None) -> str:
    flags = flags if flags is not None else []
    words = config.extractor.delimiter_words if config is not None else {}
    explicit = []
    for label, stated in (("STTM", sttm_feed.source_file.delimiter),
                          ("FRD", frd_feed.delimiter)):
        if not stated:
            continue
        char = delimiter_char(stated, words)
        if char is None:
            flags.append(f"delimiter_unreadable:{label} — the {label} states {stated!r}, "
                         "which names no delimiter character; the file extension decides")
        else:
            explicit.append(char)
    if not explicit and config is not None and _is_fixed_width(frd_feed.file_format, config):
        # M3: a fixed-width file has no delimiter by definition (positions
        # come from the VDD / STTM); an empty delimiter is the honest value.
        return ""
    if explicit:
        if len(set(explicit)) > 1:
            errors.append(mismatch_item(
                "value.conflict",
                f"delimiter disagrees: STTM says {sttm_feed.source_file.delimiter!r}, "
                f"FRD says {frd_feed.delimiter!r}"
            ))
        return explicit[0]
    implied = _FORMAT_DELIMITERS.get((frd_feed.file_format or "").lower())
    if implied is None:
        # Last resort: the delimiter the file extension implies (csv / psv / tsv).
        from codegen.extract.extractor import _extension_delimiter

        for pattern in (*frd_feed.file_name_patterns, sttm_feed.source_file.name_pattern or ""):
            implied = _extension_delimiter(pattern)
            if implied is not None:
                flags.append(f"delimiter_from_extension:{pattern} -> {implied!r} — no document "
                             "states a delimiter; the file extension implies it (.csv ',', "
                             ".psv '|', .tsv tab; a .txt / .dat file needs the FRD)")
                break
    if implied is None:
        errors.append(mismatch_item(
            "value.unstated",
            f"format '{frd_feed.file_format}' has no implied delimiter, neither contract "
            "states one, and no file pattern carries a csv / psv / tsv extension",
            field="delimiter",
            searched=("FRD Delimiter", "FRD Object/data Format", "STTM Delimiter meta row",
                      "VDD FILES delimiter", "file pattern extension")))
        return ""
    return implied


def _parse_reference(validation_text: str, feed: str) -> tuple[str, str, str | None]:
    match = _REFERENCE_RE.search(validation_text) or _CLIENT_REFERENCE_RE.search(validation_text)
    if match is None:
        # quotes the STTM validation text: the reason only (no position here;
        # the caller's coordinates stand)
        raise located(ContractMismatchError(
            feed,
            [
                mismatch_item("rule.unparseable",
                "recycle validation text is not parseable as "
                "'against <id_column> in <table> [where <filter>]' or "
                "'Check with <id_column> from ... <table> [FOR <filter>]': "
                f"{validation_text!r}")
            ],
        ), None, "contract.mismatch")
    filter_text = match.group("filter")
    return (
        match.group("table"),
        match.group("id_column"),
        filter_text.strip() if filter_text else None,
    )


def _frd_window_days(frd_feed: FrdFeed) -> int | None:
    """The recycle window the FRD states in free text, if any."""
    if frd_feed.recycle_rule is None:
        return None
    match = _WINDOW_DAYS_RE.search(frd_feed.recycle_rule)
    return int(match.group(1)) if match else None


def _frd_cell(frd: FrdContract | None, feed_index: int, field: str) -> str:
    """The FRD cell a contract field was read from (its field provenance), as
    the layout stage cites it; the bare field name when none is recorded."""
    item = frd.field_provenance.get(f"feeds[{feed_index}].{field}") if frd is not None else None
    return (f"table {item.table} row {item.row} ({item.label!r})" if item is not None
            else f"FRD contract field {field!r}")


def _delimiter_from_format_text(frd_feed: FrdFeed, others: list, feed_index: int,
                                frd: FrdContract | None, config: Config
                                ) -> tuple[str | None, str | None, str | None]:
    """Chunk B review (B1): the layout stage's FRD-format-cell rule on the
    CLI path. The FRD states no delimiter cell, but its FORMAT cell names one
    in so many words ("Pipe delimited (|) text file"): that is the FRD's
    statement. Returns (character, fill flag, error): the character + a flag
    citing the FRD cell when the STTM / VDD agree or are silent; an error
    naming both cells and the remedy when they state another character -
    never the STTM value silently. (None, None, None) when the format cell
    names no delimiter."""
    from codegen.resolve.gapfill import Statement, delimiter_in_format, fill_flag

    words = config.extractor.delimiter_words
    char = delimiter_in_format(frd_feed.file_format, words)
    if char is None:
        return None, None, None
    cell = f"{_frd_cell(frd, feed_index, 'file_format')}: {frd_feed.file_format!r}"
    disagreeing = [o for o in others if delimiter_char(o.value, words) not in (None, char)]
    if disagreeing:
        key = f"feeds[{feed_index}].delimiter"
        return None, None, (
            f"delimiter disagrees: the FRD format cell {cell} names {char!r}, "
            + "; ".join(f"the {o.source} {o.cell} says {o.value!r}" for o in disagreeing)
            + f" — answer {key} under gaps: in answers.yaml and re-run `codegen layout "
            "--answers answers.yaml --frd-contract-out <frd contract>` (then extract-sttm and "
            "generate on that contract)")
    return char, fill_flag("delimiter", Statement(char, "FRD", cell)), None


def _fill_frd_gaps(frd_feed: FrdFeed, sttm_feed: SttmFeed, config: Config, vdd,
                   *, feed_index: int = 0, frd: FrdContract | None = None
                   ) -> tuple[FrdFeed, list[str], list[str]]:
    """The contract-level gap chain. Returns (patched feed, flags, errors)."""
    from codegen.faq import load_faq
    from codegen.resolve.gapfill import (
        Statement,
        distinct,
        fill_flag,
        format_statements,
        parse_load_strategy_text,
        strategy_from_faq,
    )

    flags: list[str] = []
    errors: list[str] = []
    meta = sttm_feed.meta_rows
    sheet = sttm_feed.mapping_sheet
    feed = frd_feed
    vdd_files = list(getattr(vdd, "files", []) or [])

    def others_for(meta_key: str, vdd_attr: str) -> list[Statement]:
        out: list[Statement] = []
        if meta.get(meta_key):
            out.append(Statement(meta[meta_key], "STTM", f"{sheet} meta row {meta_key!r}"))
        for f in vdd_files:
            value = getattr(f, vdd_attr, None)
            if value:
                out.append(Statement(value, "VDD", f"FILES row {f.row}"))
        return distinct(out, config.extractor.delimiter_words)

    if feed.file_format is None:
        others = distinct(format_statements(others_for("file_format", "format")))
        if len(others) == 1:
            feed = feed.model_copy(update={"file_format": others[0].value})
            flags.append(fill_flag("file_format", others[0]))
        elif len(others) > 1:
            errors.append(mismatch_item(
                "value.conflict",
                "the FRD states no file format and the other documents disagree: "
                + "; ".join(f"{s.source} {s.cell} says {s.value!r}" for s in others)
                + " — choose one in the layout dialog"))
    if feed.delimiter is None:
        others = others_for("delimiter", "delimiter")
        # The FRD's own format cell first (only the FRD's: a format the STTM
        # filled above is no FRD statement).
        char, flag, error = _delimiter_from_format_text(frd_feed, others, feed_index, frd,
                                                        config)
        if error is not None:
            errors.append(mismatch_item("value.conflict", error))
        elif char is not None:
            feed = feed.model_copy(update={"delimiter": char})
            flags.append(flag)
        elif len(others) == 1:
            feed = feed.model_copy(update={"delimiter": others[0].value})
            flags.append(fill_flag("delimiter", others[0]))
    if feed.frequency is None:
        sttm_frequency = sttm_feed.source_file.frequency or meta.get("frequency")
        if sttm_frequency:
            statement = Statement(sttm_frequency, "STTM",
                                  f"{sheet} File Details / meta row 'frequency'")
            feed = feed.model_copy(update={"frequency": statement.value})
            flags.append(fill_flag("frequency", statement))
    # M9.3: the STTM target band is authoritative for the schema; an FRD that
    # states none takes it from there, flagged per layer.
    for layer, ref in (("stage", sttm_feed.stage), ("standard", sttm_feed.standard)):
        target = getattr(feed, f"{layer}_target")
        if ref is None or target.schema_name is not None or not ref.schema_name:
            continue
        if layer == "standard" and not target.tables:
            continue
        statement = Statement(ref.schema_name, "STTM", f"{sheet} {layer} band (schema column)")
        feed = feed.model_copy(update={f"{layer}_target": target.model_copy(
            update={"schema_name": ref.schema_name})})
        flags.append(fill_flag(f"{layer}_target.schema", statement))
    # The catalog chain's second link (FRD label -> STTM band -> config
    # default): the resolver carries whichever document states one. A
    # segmented extraction already cites its standard catalog (provenance
    # note), so only the flat / generic path is flagged here.
    for layer, ref in (("stage", sttm_feed.stage), ("standard", sttm_feed.standard)):
        target = getattr(feed, f"{layer}_target")
        if ref is None or target.catalog is not None or not ref.catalog:
            continue
        if sttm_feed.segmented is not None or (layer == "standard" and not target.tables):
            continue
        statement = Statement(ref.catalog, "STTM", f"{sheet} {layer} band (catalog column)")
        feed = feed.model_copy(update={f"{layer}_target": target.model_copy(
            update={"catalog": ref.catalog})})
        flags.append(fill_flag(f"{layer}_target.catalog", statement))
    parsed = parse_load_strategy_text(meta.get("load_strategy"),
                                      config.extractor.frd.target_schema_markers)
    cell = f"{sheet} meta row 'load_strategy'"
    if feed.stage_target.load_strategy is None:
        if parsed.get("stage"):
            statement = Statement(parsed["stage"], "STTM", cell)
        else:
            statement = strategy_from_faq(load_faq(normalize_feed_name(feed.feed_name), config))
        if statement is not None:
            feed = feed.model_copy(update={"stage_target": feed.stage_target.model_copy(
                update={"load_strategy": statement.value})})
            flags.append(fill_flag("stage_target.load_strategy", statement))
        elif "any" in parsed:
            errors.append(mismatch_item(
                "value.unstated",
                f"the STTM states one load strategy ({parsed['any']!r}, {cell}) "
                "without a layer — say which layer it applies to in the layout "
                "dialog, or answer the FAQ load_mode", field="stage_target.load_strategy",
                searched=("FRD Load Strategy STG", "STTM Load Strategy meta row (no layer)",
                          "FAQ load_mode")))
    if feed.standard_target.load_strategy is None:
        if parsed.get("standard"):
            statement = Statement(parsed["standard"], "STTM", cell)
            feed = feed.model_copy(update={"standard_target": feed.standard_target.model_copy(
                update={"load_strategy": statement.value})})
            flags.append(fill_flag("standard_target.load_strategy", statement))
        elif feed.standard_target.tables:
            flags.append("frd_unstated:standard_target.load_strategy source_used:none — the "
                         "FRD and the STTM state no standard-layer strategy; left blank")
    return feed, flags, errors


def map_catalog(catalog: str | None, layer: str, config: Config,
                flags: list[str]) -> tuple[str | None, str | None]:
    """Multi-table rule 7: (emitted catalog, logical catalog). The documents
    state LOGICAL catalogs (PR_DLK); ``conventions.catalog_map`` — an
    environment value — maps them (case-insensitive key match) and the mapped
    name is emitted in lowercase. An empty map is identity (logical None).
    With a map, a stated catalog that has no entry is written as stated and
    flagged ``catalog_unmapped:<layer>`` (once per catalog).

    2026-10-14 (post47): the map is the run's environment's
    (``codegen.environments.catalog_map``); a CUSTOM environment that states
    none leaves a stated catalog UNSET (None, its logical name kept) —
    never the logical name written, never another environment's map."""
    from codegen import environments as envs

    # post47b: also a named environment's placeholder (provider=mock)
    reason = envs.catalog_unset_reason(config, catalog)
    if reason is not None:
        flag = (f"catalog_unset:{layer} — {catalog!r}: {reason}; the catalog is left unset "
                f"(INPUT_NEEDED run.environment.catalog_map.{catalog})")
        if flag not in flags:
            flags.append(flag)
        return None, catalog
    catalog_map = envs.catalog_map(config)
    if catalog is None or not catalog_map:
        return catalog, None
    mapped = catalog_map.get(catalog)
    if mapped is None:
        mapped = next((v for k, v in catalog_map.items() if k.lower() == catalog.lower()), None)
    if mapped is None:
        flag = (f"catalog_unmapped:{layer} — {catalog!r} has no conventions.catalog_map entry "
                f"(keys: {sorted(catalog_map)}); written as stated")
        if flag not in flags:
            flags.append(flag)
        return catalog, None
    return mapped.lower(), catalog


def stated_catalog(layer: str, band: str | None, frd: str | None,
                   flags: list[str]) -> str | None:
    """Multi-table rule 6 precedence: the STTM band's catalog, else the FRD
    label's (``default_catalog`` is the emitters' last link). Both stated and
    different (case-insensitively) = ``catalog_conflict:<layer>`` naming both;
    the band wins."""
    if band and frd and band.lower() != frd.lower():
        flag = (f"catalog_conflict:{layer} — STTM band {band!r} vs FRD label {frd!r}; the band "
                "is used (docs/acfc/MULTI_TABLE_DESIGN.md rule 6)")
        if flag not in flags:
            flags.append(flag)
    return band or frd


def _sttm_segment_names(sttm_feed: SttmFeed) -> list[str]:
    """Header / Detail / Trailer as the STTM's fields declare them, in order."""
    return [s for s in ("Header", "Detail", "Trailer")
            if any(f.record_segment == s for f in sttm_feed.fields)]


def _resolve_segments(
    frd_feed: FrdFeed,
    sttm_feed: SttmFeed,
    catalog: str | None,
    errors: list[str],
    segment_names: list[str] | None = None,
    flags: list[str] | None = None,
    catalog_logical: str | None = None,
    config: Config | None = None,
) -> list[SegmentSpec]:
    flags = flags if flags is not None else []
    # M4: a docx-extracted FRD names no segments (the F1/F2 label families
    # have no slot for them); the STTM's Segment column is then the source,
    # recorded as a provenance flag by the caller.
    segment_names = segment_names if segment_names is not None else list(frd_feed.record_segments)
    stage_schema = sttm_feed.stage.schema_name
    frd_schema = frd_feed.stage_target.schema_name
    # Segmented-extraction contracts carry the workbook's identifiers
    # verbatim; Databricks identifiers are case-insensitive, so pure case
    # drift is not a mismatch on that path.
    schemas_equal = frd_schema == stage_schema or (
        sttm_feed.segmented is not None
        and frd_schema is not None
        and frd_schema.lower() == stage_schema.lower()
    )
    if frd_schema is not None and not schemas_equal:
        # Chunk B (cold drill): the STTM stage band is authoritative for the
        # schema (CLAUDE.md doctrine); the FRD's statement is a cross-check -
        # flagged with both values, never a contract mismatch.
        flags.append(f"frd_crosscheck:stage_target.schema — STTM stage band {stage_schema!r} "
                     f"(authoritative, used) vs FRD {frd_schema!r}")

    if not frd_feed.is_segmented and not (sttm_feed.is_segmented and segment_names):
        if sttm_feed.is_segmented:
            errors.append(mismatch_item(
                "segment.sttm_only",
                "STTM fields carry record_segment but the FRD declares no segments",
                names=sorted({f.record_segment for f in sttm_feed.fields if f.record_segment})))
        if not _table_in(sttm_feed.stage.table, frd_feed.stage_target.tables, "STTM", "FRD",
                         flags):
            errors.append(mismatch_item(
                "table.sttm_only",
                f"STTM stage table '{sttm_feed.stage.table}' is not among FRD stage "
                f"tables {frd_feed.stage_target.tables}", names=[sttm_feed.stage.table]
            ))
        table = ResolvedTable(
            catalog=catalog, schema_name=stage_schema, table=sttm_feed.stage.table, role="stage",
            catalog_logical=catalog_logical,
        )
        return [SegmentSpec(segment="Detail", stage_table=table, fields=sttm_feed.fields)]

    if not sttm_feed.is_segmented:
        errors.append(mismatch_item(
            "segment.frd_only",
            f"FRD declares segments {frd_feed.record_segments} but no STTM field "
            "carries record_segment/stage_table", names=frd_feed.record_segments or []
        ))
        return []

    segments: list[SegmentSpec] = []
    seen_segments: list[str] = []
    for segment_name in segment_names:
        seg_fields = [f for f in sttm_feed.fields if f.record_segment == segment_name]
        if not seg_fields:
            errors.append(mismatch_item(
                "segment.frd_only",
                f"FRD segment '{segment_name}' has no fields in the STTM contract",
                names=[segment_name]))
            continue
        seg_tables = {f.stage_table for f in seg_fields}
        if len(seg_tables) > 1:
            errors.append(mismatch_item(
                "table.conflict",
                f"segment '{segment_name}' maps to multiple stage tables: {sorted(seg_tables)}"
            ))
        seg_table = seg_fields[0].stage_table
        assert seg_table is not None  # guaranteed by SttmFeed validation
        # Rule 6: a table takes catalog / schema from its OWN band — a row
        # that states a catalog / schema other than the band's carries it.
        seg_catalog, seg_catalog_logical = catalog, catalog_logical
        row_catalog = next((f.stage_catalog for f in seg_fields if f.stage_catalog), None)
        if row_catalog is not None and config is not None:
            seg_catalog, seg_catalog_logical = map_catalog(row_catalog, "stage", config, flags)
        seg_schema = next((f.stage_schema for f in seg_fields if f.stage_schema), stage_schema)
        if not _table_in(seg_table, frd_feed.stage_target.tables, "STTM", "FRD", flags):
            errors.append(mismatch_item(
                "table.sttm_only",
                f"segment '{segment_name}' stage table '{seg_table}' is not among FRD "
                f"stage tables {frd_feed.stage_target.tables}", names=[seg_table]
            ))
        # Per-segment STANDARD table (segmented dialect: H/D/T map to their
        # own tables in BOTH layers). Catalog/schema come from the STTM's
        # standard target group when the FRD's Target Schema block names
        # stage targets only.
        standard_table = None
        seg_standard_tables = {f.standard_table for f in seg_fields} - {None}
        if len(seg_standard_tables) > 1:
            errors.append(mismatch_item(
                "table.conflict",
                f"segment '{segment_name}' maps to multiple standard tables: "
                f"{sorted(t for t in seg_standard_tables if t)}"
            ))
        elif seg_standard_tables and sttm_feed.standard is not None:
            stated = stated_catalog(
                "standard",
                next((f.standard_catalog for f in seg_fields if f.standard_catalog),
                     sttm_feed.standard.catalog),
                frd_feed.standard_target.catalog, flags)
            standard_catalog, standard_logical = (
                map_catalog(stated, "standard", config, flags) if config is not None
                else (stated, None))
            standard_table = ResolvedTable(
                catalog=standard_catalog,
                schema_name=next((f.standard_schema for f in seg_fields if f.standard_schema),
                                 sttm_feed.standard.schema_name),
                table=next(iter(seg_standard_tables)),
                role="standard",
                catalog_logical=standard_logical,
            )
        segment_audit = (
            sttm_feed.segmented.segment_audit.get(segment_name)
            if sttm_feed.segmented is not None else None
        )
        segments.append(
            SegmentSpec(
                segment=segment_name,
                stage_table=ResolvedTable(
                    catalog=seg_catalog, schema_name=seg_schema, table=seg_table, role="stage",
                    catalog_logical=seg_catalog_logical,
                ),
                fields=seg_fields,
                standard_table=standard_table,
                audit_columns=segment_audit,
            )
        )
        seen_segments.append(segment_name)

    sttm_segments = {f.record_segment for f in sttm_feed.fields if f.record_segment}
    extra = sttm_segments - set(segment_names)
    if extra:
        errors.append(mismatch_item(
            "segment.sttm_only",
            f"STTM fields name segments the FRD does not declare: {sorted(extra)}",
            names=sorted(extra)))

    if segments and not any(s.segment == "Detail" for s in segments):
        errors.append(mismatch_item(
            "segment.missing", "no Detail segment resolved; the data-carrying segment is required"))
    if segments:
        detail = next((s for s in segments if s.segment == "Detail"), None)
        if detail is not None and sttm_feed.stage.table != detail.stage_table.table:
            errors.append(mismatch_item(
                "table.conflict",
                f"STTM stage.table '{sttm_feed.stage.table}' should be the Detail segment "
                f"table '{detail.stage_table.table}'"
            ))
    return segments


def _key_marked(f: SttmField) -> bool:
    return not f.nullable or f.primary_key


def _pk_marked(f: SttmField) -> bool:
    return f.primary_key


def _detail_key_columns(segments: list[SegmentSpec], source_columns: list[str],
                        flags: list[str], marked=_key_marked) -> list[str]:
    """The Detail table's natural key, resolved by (segment, field name).

    A key names SOURCE fields, and a fixed-width file repeats some of them in
    every record (``REC_TYPE`` in the header, the detail and the trailer, each
    mapped to its own target column). The lookup therefore stays inside the
    Detail segment — the rows the Detail table's MERGE sees — and never
    crosses into another segment: a name marked only in the header / trailer
    is THAT table's key (it keeps its Primary Key on its own field, which the
    per-table IIG reads), not the Detail table's. A listed name that no
    segment carries after resolution is dropped with ``key_column_not_in_table``."""
    detail = next((s for s in segments if s.segment == "Detail"), None)
    if detail is None:
        return []
    keys: list[str] = []
    for name in dict.fromkeys(source_columns):
        own = [f for f in detail.fields if f.source_column == name]
        elsewhere = [(s, f) for s in segments if s is not detail
                     for f in s.fields if f.source_column == name]
        if own and (any(marked(f) for f in own)
                    or not any(marked(f) for _s, f in elsewhere)):
            hit = next((f for f in own if marked(f)), own[0])
            keys.append(hit.stage_column)
            continue
        if elsewhere:
            continue                 # the key of its own segment's table
        flags.append(
            f"key_column_not_in_table:{name} — the STTM lists {name!r} as a key / not-null "
            f"column (load_rules.not_null_columns), but after per-segment resolution no field "
            f"of the Detail table {detail.stage_table.table!r} (or of any other resolved "
            "segment) carries it; dropped from the natural key")
    return list(dict.fromkeys(keys))


def _phi_stage_columns(segments: list[SegmentSpec], source_columns: list[str]) -> list[str]:
    """Every PHI-flagged field's OWN stage column, resolved by (segment, field
    name): a name the header, detail and trailer all carry maps to each
    segment's column that is flagged PHI — never to whichever came last."""
    columns: list[str] = []
    for name in source_columns:
        columns += [f.stage_column for s in segments for f in s.fields
                    if f.source_column == name and f.phi]
    return list(dict.fromkeys(columns))


def apply_frd_split(frd: FrdContract, sttm: SttmContract) -> FrdContract:
    """2026-10-13 (D1 pair_11): the STTM contract records the FRD feeds
    ``extract-sttm`` derived from a ONE-feed FRD contract (one per mapping
    sheet). Given that same one-feed contract, the join uses those feeds —
    with their flags — so extract and generate agree. Any other FRD contract
    (already split by the layout stage, or several feeds) is used as given."""
    split = sttm.frd_split
    if (split is None or len(frd.feeds) != 1
            or normalize_feed_name(frd.feeds[0].feed_name)
            != normalize_feed_name(split.source_feed_name)):
        return frd
    return frd.model_copy(update={
        "feeds": list(split.feeds),
        "extraction_flags": list(dict.fromkeys([*frd.extraction_flags, *split.flags]))})


def resolve_feeds(
    frd: FrdContract,
    sttm: SttmContract,
    config: Config,
    *,
    frd_sha256: str,
    sttm_sha256: str,
    vdd=None,
    gaps: dict[str, str] | None = None,
) -> list[ResolvedFeedSpec]:
    """Join every FRD feed to its STTM feed. Unmatched feeds on either side
    fail — except a feed the extractor held back as NEEDS_ANSWERS
    (``sttm.needs_answers``): it is reported by the caller
    (:func:`pending_answers`), never resolved and never an error. A feed whose
    only problem is a value no document states (post57) does not stop the
    others: once every feed is joined, :class:`ContractUnstatedError` carries
    the resolved specs and the questions."""
    frd = apply_frd_split(frd, sttm)
    sttm_by_id = {f.feed_id: f for f in sttm.feeds}
    held_back = {p.feed_name for p in sttm.needs_answers}
    matched_sttm_ids: set[str] = set()
    specs: list[ResolvedFeedSpec] = []
    unmatched_frd: list[str] = []
    unstated: list[ContractUnstatedError] = []

    for frd_feed in frd.feeds:
        feed_id = config.feed_aliases.get(frd_feed.feed_name) or normalize_feed_name(
            frd_feed.feed_name
        )
        sttm_feed = sttm_by_id.get(feed_id)
        if sttm_feed is None and frd_feed.feed_name in held_back:
            continue
        if sttm_feed is None:
            unmatched_frd.append(f"{frd_feed.feed_name!r} (looked for STTM feed_id '{feed_id}')")
            continue
        matched_sttm_ids.add(feed_id)
        try:
            specs.append(_resolve_one(frd, frd_feed, sttm, sttm_feed, config, frd_sha256,
                                      sttm_sha256, vdd=vdd, gaps=gaps))
        except ContractUnstatedError as held:
            unstated.append(held)

    errors = [mismatch_item("feed.frd_only", f"FRD feed has no STTM mapping: {name}")
              for name in unmatched_frd]
    errors += [
        mismatch_item("feed.sttm_only", f"STTM feed '{feed_id}' has no FRD feed")
        for feed_id in sorted(set(sttm_by_id) - matched_sttm_ids)
    ]
    if errors:
        # names feeds on both sides: the reason only (the whole pair; the
        # caller's coordinates stand)
        raise located(ContractMismatchError(frd.contract_name, errors), None,
                      "contract.mismatch")
    if unstated:
        raise ContractUnstatedError(
            ", ".join(u.feed for u in unstated), [e for u in unstated for e in u.errors],
            [q for u in unstated for q in u.questions], specs)
    return specs


def _resolve_one(
    frd: FrdContract,
    frd_feed: FrdFeed,
    sttm: SttmContract,
    sttm_feed: SttmFeed,
    config: Config,
    frd_sha256: str,
    sttm_sha256: str,
    vdd=None,
    gaps: dict[str, str] | None = None,
) -> ResolvedFeedSpec:
    errors: list[str] = []
    feed_id = sttm_feed.feed_id
    original_frd_feed = frd_feed

    # FRD gap chain (resolve/gapfill.py): a docx-extracted FRD that states no
    # file format / load strategy takes them from the STTM meta rows, the VDD
    # FILES sheet or the FAQ — each fill a provenance flag. The layout stage
    # applies the same chain earlier (with the dialog for disagreements);
    # here it covers the CLI path and anything the dialog left blank.
    feed_index = next((i for i, f in enumerate(frd.feeds) if f is original_frd_feed), 0)
    # post57 (D1 post55 pair_01): an FRD cell's own label taken off its value,
    # and the landing's account / container from the run's environment
    from codegen.resolve.stated import stated_values

    frd_feed, stated_flags = stated_values(frd_feed, feed_index, frd, config)
    answered_flags: list[str] = []
    frd_feed = _answered_unstated(frd_feed, gaps, feed_index, answered_flags)
    frd_feed, gap_flags, gap_errors = _fill_frd_gaps(frd_feed, sttm_feed, config, vdd,
                                                     feed_index=feed_index, frd=frd)
    gap_flags = [*answered_flags, *gap_flags]
    errors.extend(e if isinstance(e, MismatchItem) else mismatch_item("value.conflict", e)
                  for e in gap_errors)
    catalog_flags: list[str] = []
    catalog, catalog_logical = map_catalog(
        stated_catalog("stage", sttm_feed.stage.catalog, frd_feed.stage_target.catalog,
                       catalog_flags),
        "stage", config, catalog_flags)
    width_flags: list[str] = []
    sttm_feed = _resolve_widths(sttm_feed, vdd, feed_index, width_flags)

    delimiter_flags: list[str] = []
    delimiter = _resolve_delimiter(frd_feed, sttm_feed, errors, config, delimiter_flags)
    provenance_flags: list[str] = []
    segment_names: list[str] | None = None
    if not frd_feed.is_segmented and sttm_feed.is_segmented:
        segment_names = _sttm_segment_names(sttm_feed)
        provenance_flags.append(
            f"segments_from_sttm: the FRD names no record segments; the STTM's Segment "
            f"column declares {segment_names} (sheet {sttm_feed.mapping_sheet!r})")
    segments = _resolve_segments(frd_feed, sttm_feed, catalog, errors, segment_names,
                                 provenance_flags, catalog_logical=catalog_logical,
                                 config=config)
    # docx-extracted FRD contracts (M2) leave unsourced values null; each
    # is a loud stop here, never a default — except the file pattern, which
    # the STTM's meta rows / FILE_DETAILS supply when the FRD names none
    # (M4), flagged as such.
    # The file-pattern chain (M9.1b): FRD -> STTM meta rows / File Details ->
    # VDD FILES sheet -> (the layout stage's `file_patterns` question, whose
    # answer arrives as FRD patterns) -> the hard stop, here, at generate time.
    file_name_patterns = list(frd_feed.file_name_patterns)
    if not file_name_patterns:
        sttm_patterns = [p.strip() for p in re.split(
            r"[;\n,]+", sttm_feed.source_file.name_pattern or "") if p.strip()]
        meta_names = sttm_feed.meta_rows.get("file_names")
        if meta_names:
            sttm_patterns = [p.strip() for p in re.split(r"[;\n,]+", meta_names) if p.strip()]
        if sttm_patterns:
            file_name_patterns = sttm_patterns
            provenance_flags.append(
                f"file_pattern_from_sttm: the FRD names no file pattern; the STTM states "
                f"{sttm_patterns} (meta row 'File Names' / FILE_DETAILS)")
        else:
            vdd_patterns = [(f.pattern.strip(), f.row) for f in (getattr(vdd, "files", []) or [])
                            if f.pattern and f.pattern.strip()]
            if vdd_patterns:
                file_name_patterns = list(dict.fromkeys(p for p, _row in vdd_patterns))
                provenance_flags.append(
                    f"file_pattern_from_vdd: the FRD and the STTM name no file pattern; the VDD "
                    f"FILES sheet states {file_name_patterns} (File Name Pattern, row(s) "
                    f"{sorted({row for _p, row in vdd_patterns})})")
            else:
                errors.append(mismatch_item(
                    "value.unstated",
                    "no source names a file pattern: the FRD states none, the STTM meta rows "
                    "'File Names' / 'File Name Example' and its File Details sheet are blank, "
                    "and no VDD FILES sheet was given (or its File Name Pattern column is "
                    "empty) — answer `feeds[0].file_patterns` in the layout dialog or under "
                    "`gaps:` in the answers file, or pass the VDD (`generate --vdd`)",
                    field="file_name_patterns",
                    searched=("FRD File Name Pattern", "STTM File Names meta row",
                              "STTM File Name Example meta row", "STTM File Details sheet",
                              "VDD FILES File Name Pattern")))
    # Hard stops that remain: fields every source is silent on and the
    # generator cannot proceed without (a reader needs the format; a writer
    # needs the stage strategy). Domain / standard strategy are blank-and-flag.
    if frd_feed.file_format is None:
        errors.append(mismatch_item(
            "value.unstated",
            "no source states the file format: FRD 'Object/data Format', the STTM "
            "'File Format' meta row and the VDD FILES sheet are all blank",
            field="file_format",
            searched=("FRD Object/data Format", "STTM File Format meta row",
                      "VDD FILES format", "file pattern extension")))
    if frd_feed.stage_target.load_strategy is None:
        errors.append(mismatch_item(
            "value.unstated",
            "no source states the stage load strategy: FRD 'Load Strategy STG' blank, "
            "the STTM 'Load Strategy' meta row states none per layer, and the FAQ "
            "load_mode is unanswered — answer it in the layout dialog or the FAQ",
            field="stage_target.load_strategy",
            searched=("FRD Load Strategy STG", "STTM Load Strategy meta row",
                      "FAQ load_mode")))

    if not frd_feed.lobs:
        errors.append(mismatch_item(
            "value.unstated", "FRD feed declares no LOBs; the LOB audit column needs at least one",
            field="lobs", searched=("FRD LOB", "FRD Region / LOB table")))

    # --- side tables, derived from the Detail stage table ------------------
    detail_table_name = next(
        (s.stage_table.table for s in segments if s.segment == "Detail"),
        sttm_feed.stage.table,
    )
    stage_schema = sttm_feed.stage.schema_name

    def side_table(suffix: str, role: str) -> ResolvedTable:
        return ResolvedTable(
            catalog=catalog,
            schema_name=stage_schema,
            table=side_table_name(detail_table_name, suffix),
            role=role,  # type: ignore[arg-type]
            catalog_logical=catalog_logical,
        )

    errors_table = side_table(config.naming.errors_table_suffix, "errors")
    processed_files_table = side_table(
        config.naming.processed_files_table_suffix, "processed_files"
    )

    # --- recycle -----------------------------------------------------------
    resolved_recycle: ResolvedRecycle | None = None
    recycle_spec = sttm_feed.load_rules.recycle
    if recycle_spec is not None and recycle_spec.enabled:
        frd_days = _frd_window_days(frd_feed)
        if frd_days is not None and frd_days != recycle_spec.recycle_window_days:
            errors.append(mismatch_item(
                "value.conflict",
                f"recycle window disagrees: FRD text says {frd_days} days, "
                f"STTM spec says {recycle_spec.recycle_window_days} days"
            ))
        reference_table, reference_id_column, reference_filter = _parse_reference(
            recycle_spec.validation, feed_id
        )
        # Prefer a recycle table the FRD names explicitly; else derive one.
        derived = side_table_name(detail_table_name, config.naming.recycle_table_suffix)
        frd_named = [
            t
            for t in frd_feed.stage_target.tables
            if t.lower() == derived.lower() and t not in {s.stage_table.table for s in segments}
        ]
        recycle_table = ResolvedTable(
            catalog=catalog,
            schema_name=stage_schema,
            table=frd_named[0] if frd_named else derived,
            role="recycle",
            catalog_logical=catalog_logical,
        )
        resolved_recycle = ResolvedRecycle(
            spec=recycle_spec,
            frd_rule_text=frd_feed.recycle_rule,
            recycle_table=recycle_table,
            reference_table=reference_table,
            reference_id_column=reference_id_column,
            reference_filter=reference_filter,
        )

    # Every FRD stage table must be accounted for (segment tables + recycle).
    accounted = {s.stage_table.table for s in segments}
    if resolved_recycle is not None:
        accounted.add(resolved_recycle.recycle_table.table)
    # (the same normalized comparison, the other way round — already reported)
    unaccounted = [t for t in frd_feed.stage_target.tables
                   if not _table_in(t, sorted(accounted), "FRD", "STTM", [])]
    if unaccounted:
        errors.append(mismatch_item(
            "table.frd_only",
            f"FRD stage tables not mapped by any STTM field or recycle rule: {unaccounted}",
            names=unaccounted
        ))

    # --- standard target ---------------------------------------------------
    standard_table: ResolvedTable | None = None
    standard_strategy = None
    if sttm_feed.standard is not None:
        if not frd_feed.standard_target.tables:
            if sttm_feed.segmented is None:
                errors.append(mismatch_item(
                    "table.sttm_only",
                    f"STTM names standard table '{sttm_feed.standard.table}' but the FRD "
                    "standard target is empty", names=[sttm_feed.standard.table]
                ))
            # Segmented extraction: the standard layer is scoped by the FRD's
            # Load Strategy STD; its catalog/schema/tables come from the
            # STTM's standard target group (the FRD's Target Schema block
            # names stage targets only) — recorded as a cited provenance note
            # on the extraction, never inferred silently.
        elif not _table_in(sttm_feed.standard.table, frd_feed.standard_target.tables, "STTM",
                           "FRD", provenance_flags):
            errors.append(mismatch_item(
                "table.sttm_only",
                f"STTM standard table '{sttm_feed.standard.table}' is not among FRD "
                f"standard tables {frd_feed.standard_target.tables}",
                names=[sttm_feed.standard.table]
            ))
        standard_catalog, standard_logical = map_catalog(
            stated_catalog("standard", sttm_feed.standard.catalog,
                           frd_feed.standard_target.catalog, catalog_flags),
            "standard", config, catalog_flags)
        standard_table = ResolvedTable(
            catalog=standard_catalog,
            schema_name=sttm_feed.standard.schema_name,
            table=sttm_feed.standard.table,
            role="standard",
            catalog_logical=standard_logical,
        )
        standard_strategy = frd_feed.standard_target.load_strategy
    elif frd_feed.standard_target.tables:
        errors.append(mismatch_item(
            "table.frd_only",
            f"FRD names standard tables {frd_feed.standard_target.tables} but the STTM "
            "has no standard mapping", names=frd_feed.standard_target.tables
        ))

    if errors:
        # the ORIGINAL feed object: the gap chain above may have replaced frd_feed
        position = next((i for i, f in enumerate(frd.feeds, 1) if f is original_frd_feed),
                        None)
        if all(getattr(e, "kind", None) == UNSTATED for e in errors):
            # post57: nothing disagrees — values no document states are
            # questions (NEEDS_ANSWERS), collected by resolve_feeds
            raise ContractUnstatedError(feed_id, errors, _unstated_questions(
                errors, feed_id, feed_index, position, len(frd.feeds)))
        raise located(ContractMismatchError(feed_id, errors),
                      Coord("feed", n=position, of=len(frd.feeds)) if position else None,
                      "contract.mismatch")

    # Multi-table rule 2: the files the feed receives — the resolved patterns,
    # expanded per LOB when one carries a LOB token. The LOBs are the STTM
    # header block's when it lists any, else the FRD's.
    from codegen.resolve.files import expand_files, split_lobs

    header_lobs = split_lobs(sttm_feed.meta_rows.get("lob"),
                             config.extractor.discovery.meta_blank_values)
    files, file_flags = expand_files(
        file_name_patterns, header_lobs or list(frd_feed.lobs), config.extractor.lob_tokens,
        provenance=("FRD / STTM file pattern; LOBs from the STTM header block 'LOB'"
                    if header_lobs else "FRD / STTM file pattern; LOBs from the FRD"))
    lob_key, lob_unkeyed = _key_files_by_lob_table(frd_feed, feed_index, files, file_flags,
                                                   config, gaps)
    if lob_key is not None:
        files = file_flags.pop()

    key_flags: list[str] = []
    # post70: two lists, never one — the not-null columns (rejects, MANDATORY)
    # and the natural key, which only an explicit key signal states (the STTM's
    # Primary Key cells: load_rules.natural_key). A required column is not a key.
    not_null = _detail_key_columns(segments, sttm_feed.load_rules.not_null_columns,
                                   key_flags)
    natural_key = _detail_key_columns(segments, sttm_feed.load_rules.natural_key, [],
                                      marked=_pk_marked)
    phi = _phi_stage_columns(segments, sttm_feed.load_rules.phi_columns)

    return ResolvedFeedSpec(
        feed_id=feed_id,
        feed_slug=normalize_feed_name(feed_id),
        feed_name=frd_feed.feed_name,
        source_system=frd_feed.source_system,
        lobs=frd_feed.lobs,
        domain=frd_feed.domain,
        sub_domain=frd_feed.sub_domain,
        file_name_patterns=file_name_patterns,
        file_format=frd_feed.file_format,
        delimiter=delimiter,
        landing_location=frd_feed.landing_location,
        segments=segments,
        stage_load_strategy=frd_feed.stage_target.load_strategy,
        standard_table=standard_table,
        standard_load_strategy=standard_strategy,
        errors_table=errors_table,
        processed_files_table=processed_files_table,
        natural_key_columns=natural_key,
        not_null_columns=not_null,
        frd_key_statement=frd_feed.key_statement,
        phi_columns=phi,
        audit_columns=sttm_feed.audit_columns,
        recycle=resolved_recycle,
        validation_rules=frd_feed.validation_rules,
        load_windows_sla=frd_feed.load_windows_sla,
        frequency=frd_feed.frequency,
        frd_contract_name=frd.contract_name,
        frd_contract_sha256=frd_sha256,
        sttm_contract_name=sttm.contract_name,
        sttm_contract_sha256=sttm_sha256,
        sttm_is_synthetic=sttm.synthetic,
        segmented_extraction=sttm_feed.segmented,
        # FRD-driven AS-IS switch: business columns STRING in BOTH layers when
        # the FRD's rules state an AS-IS load (acceptance criterion 3 shape).
        load_as_is=any(_AS_IS_RE.search(r) for r in frd_feed.validation_rules),
        source_table=sttm_feed.source_table,
        provenance_flags=list(dict.fromkeys([
            *_frd_extraction_flags(frd, original_frd_feed), *sttm_feed.extraction_flags,
            *stated_flags, *width_flags, *gap_flags, *catalog_flags, *provenance_flags,
            *file_flags,
            *key_flags, *delimiter_flags])),
        files=files,
        frequency_mentions=list(frd_feed.frequency_mentions),
        lob_unkeyed=lob_unkeyed,
        lob_question_key=lob_key if lob_unkeyed else None,
    )


LOB_ANSWER_FIELD = "lob_by_file"


def _key_files_by_lob_table(frd_feed: FrdFeed, feed_index: int, files: list, flags: list,
                            config: Config, gaps: dict[str, str] | None
                            ) -> tuple[str | None, list[str]]:
    """2026-10-14 (D1 pair_12): the FRD's Region / LOB table (``lob_table``,
    or a contract whose ``lobs`` list is that table flattened) keys each file
    to ONE LOB — plan-id column, then region column, then the client
    ``conventions.lob_reference`` (codegen.resolve.files). Appends the keyed
    file list as the LAST item of ``flags`` (the caller pops it) plus one flag
    per outcome. Returns (answers key, unmatched files); (None, []) when the
    FRD carries no LOB table."""
    from codegen.resolve.files import (
        LOB_SOURCES,
        key_files_by_lob_table,
        lob_column,
        lob_table_from_lines,
        parse_lob_answer,
    )

    frd_cfg = config.extractor.frd
    table = list(frd_feed.lob_table) or lob_table_from_lines(
        list(frd_feed.lobs), frd_cfg.lob_table_lob_headers,
        [*frd_cfg.lob_table_plan_headers, *frd_cfg.lob_table_region_headers])
    column = lob_column(table, frd_cfg.lob_table_lob_headers)
    if column is None:
        return None, []
    key = f"feeds[{feed_index}].{LOB_ANSWER_FIELD}"
    keyed, unmatched = key_files_by_lob_table(
        files, table, column, plan_headers=frd_cfg.lob_table_plan_headers,
        region_headers=frd_cfg.lob_table_region_headers,
        reference=config.conventions.lob_reference,
        answers=parse_lob_answer((gaps or {}).get(key)))
    by_source: dict[str, int] = {}
    for file in keyed:
        if file.lob_source:
            by_source[file.lob_source] = by_source.get(file.lob_source, 0) + 1
    flags.append(f"lob_from_table:{key} — {len(keyed) - len(unmatched)} of {len(keyed)} "
                 f"file(s) keyed to ONE LOB ("
                 + (", ".join(f"{n} by {LOB_SOURCES[s]}" for s, n in by_source.items())
                    or "none keyed")
                 + f"); the FRD LOB table: {', '.join(table[0])}, {len(table)} row(s)")
    if unmatched:
        codes = list(dict.fromkeys(row[column] for row in table if row.get(column)))
        flags.append(f"lob_unkeyed:{key} — {lob_question(len(unmatched), codes)}: "
                     f"{'; '.join(unmatched)} — their LOB cells stay OPEN (the table is never "
                     "written into a cell)")
    flags.append(keyed)
    return key, unmatched


def lob_question(count: int, codes: list[str]) -> str:
    """The ONE question a feed's unkeyed files ask."""
    return f"file-to-LOB mapping for {count} files; FRD lists LOB codes {', '.join(codes)}"


def lob_question_item(spec) -> dict | None:
    """2026-10-14 (post47): the feed's LOB question in the layout-question
    shape the App's Answers-needed dialog renders — kind ``files``: ONE block,
    every unkeyed file a key, the FRD's LOB codes its dropdown. Answered as a
    gaps value ``<file>=<code>; ...`` (what an answers file's ``files:``
    block reads as). None when every file is keyed."""
    if not spec.lob_unkeyed or spec.lob_question_key is None:
        return None
    key = spec.lob_question_key
    return {"document": "frd", "key": key, "sheet": None, "layer": None, "role": key,
            "kind": "files", "reason": lob_question(len(spec.lob_unkeyed), list(spec.lobs)),
            "header": [], "candidates": [{"value": code} for code in spec.lobs],
            "files": list(spec.lob_unkeyed),
            "title": f"The LOB of each file of {spec.feed_id}",
            "hint": ("No document keys these files to ONE LOB (no plan-id column, no region "
                     "token, no lob_reference entry). Pick each file's LOB from the FRD's "
                     "codes; a file left unanswered keeps its LOB cells open."),
            "suggested": None}


def _frd_extraction_flags(frd: FrdContract, frd_feed: FrdFeed) -> list[str]:
    """The docx reader's flags for THIS feed (they name ``feeds[i]``) plus the
    document-level ones."""
    index = next((i for i, f in enumerate(frd.feeds) if f is frd_feed), None)
    return [f for f in frd.extraction_flags
            if "feeds[" not in f or (index is not None and f"feeds[{index}]" in f)]


def pending_answers(sttm_path: Path) -> list:
    """The feeds an STTM contract holds back as NEEDS_ANSWERS
    (:class:`~codegen.contracts.sttm.PendingAnswer`), in contract order."""
    sttm = SttmContract.model_validate(json.loads(Path(sttm_path).read_text(encoding="utf-8")))
    return list(sttm.needs_answers)


def resolve_pair(frd_path: Path, sttm_path: Path, config: Config,
                 vdd_path: Path | None = None,
                 gaps: dict[str, str] | None = None) -> list[ResolvedFeedSpec]:
    """Load, validate, and join one FRD/STTM contract file pair; a VDD
    contract (M3) attaches to every spec as the third input."""
    frd = FrdContract.model_validate(json.loads(frd_path.read_text(encoding="utf-8")))
    sttm = SttmContract.model_validate(json.loads(sttm_path.read_text(encoding="utf-8")))
    vdd = None
    if vdd_path is not None:
        from codegen.contracts.vdd import VddContract

        vdd = VddContract.model_validate(json.loads(Path(vdd_path).read_text(encoding="utf-8")))
    specs = resolve_feeds(
        frd,
        sttm,
        config,
        frd_sha256=sha256_of_file(frd_path),
        sttm_sha256=sha256_of_file(sttm_path),
        vdd=vdd,
        gaps=gaps,
    )
    if vdd is not None:
        specs = [spec.model_copy(update={"vdd": vdd}) for spec in specs]
    return specs
