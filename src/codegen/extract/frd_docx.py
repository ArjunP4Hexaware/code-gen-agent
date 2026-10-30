"""FRD .docx → FrdContract, deterministic, stdlib zipfile + XML (M2).

Two document families (docs/acfc/SHAPES_FOR_PORT.md §2):

- **F1** — six metadata section tables (Descriptive, Structural,
  Administrative, Technical, Data Quality, Vendor), each row 0 = section
  title, rows 1–3 = Name / Description / Functional Requirement, rows 4+ =
  label:value pairs. A document may carry several complete sets (one per
  sub-domain); each set becomes one feed.
- **F2** — no metadata tables; Solution Requirement tables whose row-4
  label names the metadata section. The requirement's Functional
  Requirement text becomes a rule of that section, and ``Label: value``
  pairs inside the row-4 text are read with the same label synonyms. A
  Solution Requirement table is found by its row labels (``sr_signal``: the
  ``solution_requirement_labels`` fingerprint), its caption a second signal —
  D1 post51 pairs 08-10 carried none.

Same discipline as the STTM path: :func:`discover_frd` builds an
:class:`~codegen.layout.frd_profile.FrdLayoutProfile` (positions + labels,
never values) from the label-synonym table in ``config/config.yaml``
``extractor.frd`` — populated only with the variants SHAPES_FOR_PORT §2
lists — and :func:`read_frd` copies cell text through it. Blank values stay
empty; a field with no source is null and listed as unresolved; every
sourced field records its table/row/col and the label seen. No python-docx.
"""

from __future__ import annotations

import itertools
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from codegen.config import Config, FrdExtractorConfig
from codegen.contracts.frd import (
    BANNER_TEXT_REASON,
    UNSTATED_SOURCE,
    AcdItem,
    FieldEvidence,
    FrdContract,
    FrdFeed,
    FrdLayoutSummary,
    GroundingSummary,
    ProjectInfo,
    Provenance,
    TargetSpec,
    banner_text_problem,
)
from codegen.layout.frd_profile import (
    FrdFieldSource,
    FrdLayoutProfile,
    FrdSectionRef,
    FrdUnresolved,
    frd_fingerprint,
)
from codegen.run_errors import Coord, located

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_LOAD_STRATEGIES = ("Truncate and Load", "Append", "Upsert")
_ACD_TYPES = ("Assumption", "Constraint", "Dependency")
_PAIR_RE = re.compile(r"^\s*([^:]{1,60}?)\s*:\s*(.*)$")

# Which contract field each label key feeds (the synonyms for the label
# keys live in config). Scalars unless noted.
_SCALAR_FIELDS = {
    "object_name": "feed_name",
    "data_source": "source_system",
    "frequency": "frequency",
    "object_format": "file_format",
    "adls_location": "landing_location",
    "archive_schedule": "archive_retention",
    "source_data_dictionary": "sttm_reference",
    "pii_fields": "phi_pii_notes",
    "recycle_process": "recycle_rule",
    "primary_key": "key_statement",          # post70: a key signal
}
_FALLBACK_FIELDS = {          # used only when the primary label is blank/absent
    "name": "feed_name",
    "vendor_name": "source_system",
}
_LIST_FIELDS = {
    "lobs": "lobs",
    "target_table_name": "tables",
    "traced_requirements": "requirement_ids",
}
_RULE_LABELS = ("business_rules", "transformation_logic", "filter_criteria",
                "solution_acceptance_criteria", "functional_requirement")


class FrdDocxError(ValueError):
    """The document cannot be read as an F1/F2 FRD; message names the spot."""


class FrdUnreadableError(FrdDocxError):
    """No F1 / F2 table found (D1 post51 pairs 08-10). Carries the table count
    and each table's header-row fingerprint for the coordinates tier
    (``run_errors.error_tables``) — never a table's text."""

    def __init__(self, message: str, *, table_count: int, fingerprints: list[str]) -> None:
        super().__init__(message)
        self.table_count = table_count
        self.fingerprints = list(fingerprints)


# ------------------------------------------------------------- docx reading


@dataclass(frozen=True)
class DocxContent:
    tables: list[list[list[str]]]       # table -> row -> cell texts
    paragraphs: list[tuple[int, str]]   # (index of the next table, text) for body paragraphs
    # M7: tables nested INSIDE a cell, keyed (table, row, col) -> rows of cell
    # texts. The flat ``tables`` text of such a cell is the nested cells
    # joined by newlines (unchanged, so fingerprints stay stable).
    nested: dict[tuple[int, int, int], list[list[str]]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.nested is None:
            object.__setattr__(self, "nested", {})


def _cell_text(tc) -> str:
    """Runs join with no separator (Word splits words across runs); a
    ``<w:br/>`` is a newline; paragraphs within the cell join with newlines."""
    paragraphs = []
    for p in tc.iter(f"{_W}p"):
        parts = []
        for node in p.iter():
            if node.tag == f"{_W}t":
                parts.append(node.text or "")
            elif node.tag == f"{_W}br":
                parts.append("\n")
        paragraphs.append("".join(parts))
    return "\n".join(paragraphs).strip()


# A DOCTYPE / ENTITY declaration anywhere in the part (Word writes neither).
_DTD_RE = re.compile(rb"<!\s*(?:DOCTYPE|ENTITY)", re.IGNORECASE)


def read_docx(path: Path, prose_ok: bool = False) -> DocxContent:
    """``prose_ok`` (Chunk B): a document whose body is paragraphs only - the
    short free-form FRD - is returned with no tables (``discover_frd`` reads
    it as a ``prose`` FRD that places no field) instead of being refused."""
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except (OSError, zipfile.BadZipFile, KeyError) as exc:
        raise located(FrdDocxError(f"{path.name}: not a readable .docx ({exc})"),
                      Coord("FRD"), "frd.docx") from exc
    if _DTD_RE.search(xml):
        # post159 (pentest P2-10): Word never writes a DTD; one in an uploaded
        # FRD is an entity-expansion / external-entity attempt - refused unparsed.
        raise located(FrdDocxError(f"{path.name}: document.xml declares a DTD or an "
                                   "entity - refused"), Coord("FRD"), "frd.docx")
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise located(FrdDocxError(f"{path.name}: not a readable .docx ({exc})"),
                      Coord("FRD"), "frd.docx") from exc
    body = root.find(f"{_W}body")
    if body is None:
        raise located(FrdDocxError(f"{path.name}: document has no body"),
                      Coord("FRD"), "frd.docx")
    tables: list[list[list[str]]] = []
    paragraphs: list[tuple[int, str]] = []
    nested: dict[tuple[int, int, int], list[list[str]]] = {}
    for child in body:
        if child.tag == f"{_W}tbl":
            rows = []
            for row_index, tr in enumerate(child.findall(f"{_W}tr")):
                cells = tr.findall(f"{_W}tc")
                rows.append([_cell_text(tc) for tc in cells])
                for col_index, tc in enumerate(cells):
                    inner = tc.findall(f"{_W}tbl")
                    if inner:
                        nested[(len(tables), row_index, col_index)] = [
                            [_cell_text(itc) for itc in itr.findall(f"{_W}tc")]
                            for tbl in inner for itr in tbl.findall(f"{_W}tr")]
            tables.append(rows)
        elif child.tag == f"{_W}p":
            text = "".join(t.text or "" for t in child.iter(f"{_W}t")).strip()
            if text:
                paragraphs.append((len(tables), text))
    if not tables and not (prose_ok and paragraphs):
        raise located(FrdDocxError(f"{path.name}: document carries no tables"),
                      Coord("FRD"), "frd.unreadable")
    return DocxContent(tables=tables, paragraphs=paragraphs, nested=nested)


# ---------------------------------------------------------------- discovery


def normalize_label(text: str) -> str:
    """Case-insensitive, whitespace/newline-collapsed, trailing-colon-free."""
    collapsed = re.sub(r"\s+", " ", text).strip().lower()
    return collapsed.rstrip(":").strip()


def _lookup(table: dict[str, list[str]]) -> dict[str, str]:
    return {normalize_label(spelling): key for key, spellings in table.items()
            for spelling in spellings}


def discover_frd(content: DocxContent, config: FrdExtractorConfig) -> FrdLayoutProfile:
    tables = content.tables
    digest = frd_fingerprint(tables)
    sections = _lookup(config.section_titles)
    labels = _lookup(config.labels)
    signals = {i: s for i in range(len(tables))
               if (s := sr_signal(i, tables[i], content, config)) is not None}
    # A table with the Solution Requirement row labels is never an F1 section
    # table (a requirement NAMED "Data quality" fits the F1 reference-column
    # variant's shape).
    f1_tables = [(i, section_title(t, sections)[1]) for i, t in enumerate(tables)
                 if section_title(t, sections) is not None
                 and not (signals.get(i) or "").startswith("header-row")]
    sr_tables = sorted(signals)
    if not tables:
        # Chunk B (cold drill): a free-form FRD (paragraphs only). Prose has
        # no label to read a value by: no field is placed, every required
        # one is an unresolved field - filled from the STTM / VDD by the
        # layout stage's gap chain, else a QUESTION the person answers.
        profile = FrdLayoutProfile(fingerprint=digest, family="prose", source="synonyms",
                                   notes=[f"no table in the document ({len(content.paragraphs)} "
                                          "paragraph(s)): a prose FRD; no field is read from "
                                          "it"])
        return _with_unresolved(profile, [], 1, reason=_PROSE_REASON)
    if f1_tables:
        return _discover_f1(tables, f1_tables, labels, digest, config)
    if sr_tables:
        profile = _discover_f2(tables, sr_tables, sections, labels, digest, config)
        by_signal: dict[str, list[int]] = {}
        for i in sr_tables:
            by_signal.setdefault(signals[i], []).append(i)
        notes = [f"{F2_SIGNAL_NOTE} {signal} \u2014 table(s) {indexes}"
                 for signal, indexes in sorted(by_signal.items())]
        return profile.model_copy(update={"notes": notes + list(profile.notes)})
    # D1 post51: never the tables' text (titles were document content) - the
    # count and each table's header-row fingerprint (header_fingerprint).
    prints = [header_fingerprint(t) for t in tables]
    raise located(FrdUnreadableError(
        "no metadata section table (F1) and no Solution Requirement table (F2) found among "
        f"{len(tables)} table(s); header-row fingerprints: {prints[:16]}"
        + (f" (+{len(prints) - 16} more)" if len(prints) > 16 else ""),
        table_count=len(tables), fingerprints=prints[:16]), Coord("FRD"), "frd.unreadable")


F2_SIGNAL_NOTE = "F2 signal:"
_LABEL_CELL_MAX = 60
_LABEL_BOUNDARY = (" ", ":", "/", "(", "-")


def header_fingerprint(rows: list[list[str]]) -> str:
    """12 hex of ``term_sha256`` over a table's row 0 (normalized cells joined
    by ``|``) - names a table shape in an error line without its text. At
    home: ``term_sha256("version|date|author|description")[:12]``."""
    from codegen.term_hash import term_sha256

    row = rows[0] if rows else []
    return term_sha256("|".join(normalize_label(c) for c in row))[:12]


def _names_label(cell: str, label: str) -> bool:
    return cell == label or (cell.startswith(label)
                             and cell[len(label):len(label) + 1] in _LABEL_BOUNDARY)


def sr_signal(index: int, rows: list[list[str]], content: DocxContent,
              config: FrdExtractorConfig) -> str | None:
    """Why table ``index`` is a Solution Requirement table, or None:
    ``header-row fingerprint (k labels)`` (the row labels of SHAPES_FOR_PORT
    section F2, required ones present), ``+ caption`` when its caption also says
    so; ``caption`` alone for a captioned table the fingerprint misses (the
    short requirement tables of the documented shape)."""
    cells = {normalize_label(c) for row in rows for c in row
             if c.strip() and len(c) <= _LABEL_CELL_MAX}
    wanted = [normalize_label(label) for label in config.solution_requirement_labels]
    found = [label for label in wanted if any(_names_label(c, label) for c in cells)]
    required = [normalize_label(label) for label in config.solution_requirement_required_labels]
    fingerprint = (all(label in found for label in required)
                   and len(found) >= config.solution_requirement_min_labels)
    prefix = normalize_label(config.solution_requirement_prefix)
    before = [text for at, text in content.paragraphs if at == index]
    caption = (any(normalize_label(c).startswith(prefix) for c in (rows[0] if rows else []))
               or bool(before and normalize_label(before[-1]).startswith(prefix)))
    if fingerprint:
        return f"header-row fingerprint ({len(found)} labels)" + (" + caption" if caption
                                                                  else "")
    return "caption" if caption else None


_PATH_RE = re.compile(r"^[^\s:]+(?:/[^\s]+)+/?$")


def _labelled_path(text: str, labels: set[str]) -> str | None:
    """The path a cell states under one of ``labels``: ``<label> : <path>`` on
    one line, or the label line followed by the path line; None otherwise."""
    lines = [line.strip() for line in text.split("\n")]
    for at, line in enumerate(lines):
        pair = _PAIR_RE.match(line)
        if pair is None or normalize_label(pair.group(1)) not in labels:
            continue
        value = pair.group(2).strip() or next((n for n in lines[at + 1:] if n), "")
        if _PATH_RE.match(value):
            return value
    return None


_IDENT_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+\b")


def requirement_landings(content: DocxContent, config: FrdExtractorConfig
                         ) -> list[tuple[str, str, int, int]]:
    """post84 (pair_11): ``(key, path, table, row)`` per Solution Requirement
    table whose Name row names the requirement and ONE row states one landing
    under :attr:`FrdExtractorConfig.requirement_landing_labels` (a table stating
    two different paths is skipped — never a pick). ``key`` = the Name plus the
    ``word_word`` identifiers only THIS requirement's text names (a descriptive
    Name — "Full member roster …" — still names its file / table there)."""
    labels = {normalize_label(label) for label in config.requirement_landing_labels}
    out = []
    for index, rows in enumerate(content.tables):
        if sr_signal(index, rows, content, config) is None:
            continue
        name = next((row[1].strip() for row in rows
                     if len(row) > 1 and normalize_label(row[0]) == "name" and row[1].strip()),
                    "")
        found = {(path, row_index) for row_index, row in enumerate(rows) for cell in row[1:]
                 if (path := _labelled_path(cell, labels))}
        if name and len({path for path, _r in found}) == 1:
            path, row_index = min(found, key=lambda f: f[1])
            idents = {m.lower() for row in rows for cell in row[1:]
                      for m in _IDENT_RE.findall(cell) if "/" not in m}
            out.append((name, path, index, row_index, idents))
    common = {ident for a, b in itertools.combinations(out, 2) for ident in a[4] & b[4]}
    return [(" ".join([name, *sorted(idents - common)]), path, index, row_index)
            for name, path, index, row_index, idents in out]


def _first_cell(row: list[str]) -> tuple[int, str] | None:
    return next(((col, cell) for col, cell in enumerate(row) if cell.strip()), None)


def _section_row(rows: list[list[str]], sections: dict[str, str],
                 config: FrdExtractorConfig) -> tuple[int, int] | None:
    """(row, label col) of the row naming the metadata section: the configured
    row when its first filled cell names one, else the first row that does
    (an untitled table may carry no caption row, so the label moves up)."""
    order = [config.solution_requirement_section_row] + list(range(len(rows)))
    for index in order:
        if index >= len(rows):
            continue
        first = _first_cell(rows[index])
        if first is not None and normalize_label(first[1]) in sections:
            return index, first[0]
    return None


def _section_key(title: str, sections: dict[str, str]) -> str | None:
    """The metadata section a table title names. Real FRDs suffix the title
    with a requirement ID ("Structural Metadata: MDST231070"): a synonym
    followed by ':' / ' ' / '-' / '(' still names the section."""
    key = normalize_label(title)
    if key in sections:
        return sections[key]
    for synonym, section in sections.items():
        if key.startswith(synonym) and key[len(synonym):len(synonym) + 1] in (":", " ", "-", "("):
            return section
    return None


def section_title(rows: list[list[str]], sections: dict[str, str]
                  ) -> tuple[str, str, str | None] | None:
    """(title text, section key, reference token) of an F1 section table, or
    None. The title is row 0's first cell — or, in the reference-column
    variant (``Ref | Label | Value``: ``DM | Descriptive Metadata`` over
    ``DM-1 | Name | …``), the cell after a short reference token, which every
    label row's first cell then repeats as its prefix (Chunk B cold drill)."""
    if not rows or not rows[0]:
        return None
    first = rows[0][0]
    key = _section_key(first, sections)
    if key is not None:
        return first, key, None
    token = first.strip()
    if (len(rows[0]) > 1 and token and len(token) <= _REF_TOKEN_MAX and " " not in token
            and _section_key(rows[0][1], sections) is not None):
        return rows[0][1], _section_key(rows[0][1], sections), token
    return None


_REF_TOKEN_MAX = 8


def is_prefix_cell(cell: str, title: str, ref: str | None) -> bool:
    """True for a label row's first cell that only repeats the section: the
    title itself (with or without its requirement-ID suffix) or the table's
    reference token (``DM`` -> ``DM-1``)."""
    value = normalize_label(cell)
    if not value:
        return False
    if value == normalize_label(title) or normalize_label(title).startswith(value):
        return True
    return ref is not None and value.startswith(normalize_label(ref))


def _row_label(row: list[str], labels: dict[str, str], title: str,
               fixed: dict[str, str], ref: str | None = None
               ) -> tuple[int, str, str | None] | None:
    """(label col, label text, label key) — the first cell whose text is a
    known label; the section-prefix column (repeating the title, or the
    table's reference token) is skipped."""
    for col, cell in enumerate(row):
        if col == 0 and len(row) > 1 and ref is not None and is_prefix_cell(cell, title, ref):
            continue
        # The prefix column repeats the section title — with or without the
        # requirement-ID suffix the title itself may carry.
        if col == 0 and len(row) > 1 and normalize_label(cell) and (
                normalize_label(cell) == normalize_label(title)
                or normalize_label(title).startswith(normalize_label(cell))):
            continue
        key = labels.get(normalize_label(cell)) or fixed.get(normalize_label(cell))
        if key is not None:
            return col, cell, key
        if cell.strip():
            return col, cell, None
    return None


def _discover_f1(tables, f1_tables, labels, digest, config) -> FrdLayoutProfile:
    fixed = _lookup(config.fixed_rows)
    fields: dict[str, FrdFieldSource] = {}
    confidence: dict[str, float] = {}
    unresolved: list[FrdUnresolved] = []
    refs: list[FrdSectionRef] = []
    notes: list[str] = []
    feed_index = -1
    seen: set[str] = set()
    rule_counts: dict[int, int] = {}
    for table_index, section in f1_tables:
        if section in seen or feed_index < 0:
            feed_index += 1
            seen = set()
        seen.add(section)
        rows = tables[table_index]
        title, _key, ref = section_title(rows, _lookup(config.section_titles))
        refs.append(FrdSectionRef(table=table_index, section=section, title=title,
                                  feed_index=feed_index))
        for row_index, row in enumerate(rows[1:], start=1):
            found = _row_label(row, labels, title, fixed, ref)
            if found is None:
                continue
            col, label, key = found
            value_col = col + 1 if col + 1 < len(row) else None
            source = FrdFieldSource(table=table_index, row=row_index, col=col,
                                    value_col=value_col, label=label, section=section,
                                    feed_index=feed_index)
            if section == "data_quality" and key not in ("name", "description",
                                                         "functional_requirement"):
                # Positional DQ rule rows: every row is a rule (recycle also
                # feeds recycle_rule).
                n = rule_counts.get(feed_index, 0)
                source = source.model_copy(update={"labelled_rule": True})
                fields[f"feeds[{feed_index}].validation_rules[{n}]"] = source
                rule_counts[feed_index] = n + 1
                if key == "recycle_process":
                    fields[f"feeds[{feed_index}].recycle_rule"] = source
                continue
            paths = [] if key is None else _paths_for(key, feed_index, section, rule_counts)
            if not paths:
                notes.append(f"table {table_index} ({title}) row {row_index}: label "
                             f"{label!r} maps to no contract field")
                continue
            for path in paths:
                fields.setdefault(path, source)
                confidence[path] = 1.0
    profile = FrdLayoutProfile(fingerprint=digest, family="F1", source="synonyms",
                               fields=fields, confidence=confidence, sections=refs, notes=notes)
    return _with_unresolved(profile, unresolved, feed_index + 1)


def _paths_for(key: str, feed_index: int, section: str | None,
               rule_counts: dict[int, int]) -> list[str]:
    prefix = f"feeds[{feed_index}]"
    if key in _SCALAR_FIELDS:
        return [f"{prefix}.{_SCALAR_FIELDS[key]}"]
    if key in _FALLBACK_FIELDS:
        return [f"{prefix}.{_FALLBACK_FIELDS[key]}#fallback"]
    if key in _LIST_FIELDS:
        target = _LIST_FIELDS[key]
        if target == "tables":
            return [f"{prefix}.stage_target.tables", f"{prefix}.standard_target.tables"]
        return [f"{prefix}.{target}"]
    if key == "target_schema":
        return [f"{prefix}.stage_target.schema", f"{prefix}.standard_target.schema"]
    if key == "domain_subdomain":
        return [f"{prefix}.domain", f"{prefix}.sub_domain"]
    if key == "domain":
        return [f"{prefix}.domain"]
    if key == "sub_domain":
        return [f"{prefix}.sub_domain"]
    if key == "load_strategy_stg":
        return [f"{prefix}.stage_target.load_strategy"]
    if key == "load_strategy_std":
        return [f"{prefix}.standard_target.load_strategy"]
    if key == "inbound_folder":
        # The inbound folder path denotes the landing location too: a
        # CONFIRMING source on the same slot (ADLS Location stays primary),
        # and the value when ADLS Location is blank.
        return [f"{prefix}.landing_location#confirming"]
    if key in _RULE_LABELS:
        # Only sections whose rule rows are business/functional rules feed
        # validation_rules; a section's Functional Requirement row does when
        # it is the descriptive or technical section (the others repeat it).
        if key == "functional_requirement" and section not in ("descriptive", None):
            return []
        n = rule_counts.get(feed_index, 0)
        rule_counts[feed_index] = n + 1
        return [f"{prefix}.validation_rules[{n}]"]
    if key == "description":
        return [f"{prefix}.description#{section}"]
    return []


def _discover_f2(tables, sr_tables, sections, labels, digest, config) -> FrdLayoutProfile:
    fixed = _lookup(config.fixed_rows)
    fields: dict[str, FrdFieldSource] = {}
    confidence: dict[str, float] = {}
    refs: list[FrdSectionRef] = []
    notes: list[str] = []
    rule_counts: dict[int, int] = {}
    feed_index = 0
    for table_index in sr_tables:
        rows = tables[table_index]
        title = rows[0][0] if rows and rows[0] else ""
        located_row = _section_row(rows, sections, config)
        if located_row is None:
            notes.append(f"table {table_index}: no row names a metadata section; skipped")
            continue
        section_row, label_col = located_row
        section_label = rows[section_row][label_col]
        section = sections[normalize_label(section_label)]
        refs.append(FrdSectionRef(table=table_index, section=section, title=section_label,
                                  feed_index=feed_index))
        # Row 0 is read too: an untitled table's first row is a label row (a
        # caption row names no label, so it is passed over).
        for row_index, row in enumerate(rows):
            if row_index == section_row:
                continue
            found = _row_label(row, labels, title, fixed)
            if found is None or found[2] is None:
                continue
            col, label, key = found
            value_col = col + 1 if col + 1 < len(row) else None
            source = FrdFieldSource(table=table_index, row=row_index, col=col,
                                    value_col=value_col, label=label, section=section,
                                    feed_index=feed_index)
            if key == "functional_requirement":
                n = rule_counts.get(feed_index, 0)
                fields[f"feeds[{feed_index}].validation_rules[{n}]"] = source
                rule_counts[feed_index] = n + 1
                if section == "recycle":
                    fields[f"feeds[{feed_index}].recycle_rule"] = source
                continue
            if key in _RULE_LABELS:
                # Per-requirement acceptance criteria / business rules rows
                # are requirement boilerplate in F2; only the Functional
                # Requirement row is the section's rule.
                continue
            for path in _paths_for(key, feed_index, section, rule_counts):
                fields.setdefault(path, source)
                confidence[path] = 1.0
        # Label: value pairs inside the section row's text, same synonyms.
        value_col = label_col + 1
        text = rows[section_row][value_col] if len(rows[section_row]) > value_col else ""
        for inline_label, _value in _inline_pairs(text, config):
            key = labels.get(normalize_label(inline_label))
            if key is None:
                notes.append(f"table {table_index} row {section_row}: inline label "
                             f"{inline_label!r} maps to no contract field")
                continue
            source = FrdFieldSource(table=table_index, row=section_row, col=label_col,
                                    value_col=value_col, label=section_label, section=section,
                                    inline_label=inline_label, feed_index=feed_index)
            for path in _paths_for(key, feed_index, section, rule_counts):
                fields.setdefault(path, source)
                confidence[path] = 1.0
    # Chunk B (cold drill): the F2 documents state Domain / Sub Domain in a
    # separate two-column label | value table (SHAPES_FOR_PORT section 4,
    # pair 10) - read through the same label synonyms, never as a value of
    # any other field.
    sr = set(sr_tables)
    for table_index, rows in enumerate(tables):
        if table_index in sr or not rows or any(len(r) != 2 for r in rows):
            continue
        keys = [labels.get(normalize_label(r[0])) for r in rows]
        if not all(k in ("domain", "sub_domain") for k in keys):
            continue
        for row_index, (row, key) in enumerate(zip(rows, keys, strict=True)):
            path = f"feeds[0].{key}"
            if path in fields:
                continue
            fields[path] = FrdFieldSource(table=table_index, row=row_index, col=0, value_col=1,
                                          label=row[0], section=None, feed_index=0)
            confidence[path] = 1.0
    profile = FrdLayoutProfile(fingerprint=digest, family="F2", source="synonyms",
                               fields=fields, confidence=confidence, sections=refs, notes=notes)
    # One feed even when no requirement names a section (pair 10's shape: the
    # metadata sits in free text) - its required fields are then unresolved
    # (gap chain / QUESTION), never a silently empty feed.
    return _with_unresolved(profile, [], 1)


def _inline_pairs(text: str, config: FrdExtractorConfig) -> list[tuple[str, str]]:
    pairs = []
    for part in re.split("|".join(re.escape(s) for s in config.inline_pair_separators), text):
        match = _PAIR_RE.match(part)
        if match:
            pairs.append((match.group(1).strip(), match.group(2).strip()))
    return pairs


_REQUIRED_PATHS = ("feed_name", "source_system", "file_format", "frequency", "lobs", "domain",
                   "stage_target.schema", "stage_target.tables", "stage_target.load_strategy",
                   "standard_target.load_strategy")


_PROSE_REASON = ("the FRD is prose (no table): no label places this field; another "
                 "document fills it or the person answers it")


def _with_unresolved(profile: FrdLayoutProfile, unresolved: list[FrdUnresolved],
                     feed_count: int,
                     reason: str = "no label in the document maps to this field"
                     ) -> FrdLayoutProfile:
    out = list(unresolved)
    for feed_index in range(feed_count):
        for path in _REQUIRED_PATHS:
            key = f"feeds[{feed_index}].{path}"
            if key not in profile.fields and f"{key}#fallback" not in profile.fields:
                out.append(FrdUnresolved(field=key, feed_index=feed_index, reason=reason))
    return profile.model_copy(update={"unresolved": out})


# ------------------------------------------------------------------ reading


def _value(content: DocxContent, source: FrdFieldSource, config: FrdExtractorConfig) -> str:
    rows = content.tables[source.table]
    if source.value_col is None or source.value_col >= len(rows[source.row]):
        return ""
    text = rows[source.row][source.value_col].strip()
    if source.inline_label is not None:
        text = next((value for label, value in _inline_pairs(text, config)
                     if normalize_label(label) == normalize_label(source.inline_label)), "")
    # A placeholder ("None", "N/A" …) is a stated blank, not a value.
    if normalize_label(text) in {normalize_label(b) for b in config.blank_values}:
        return ""
    return text


# ---------------------------------------------------- M7: refused cell shapes

_HEADING_LINE_RE = re.compile(r"^\s*([^=:\n]{2,80}?):\s*$")
_LABEL_VALUE_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9 /_()-]{0,40}?)\s*[=:]\s*(.+?)\s*$")
_PREFIXED_RE = re.compile(r"^\s*([^=\n]{1,40}?)\s*=\s*(.+)$", re.S)
_FILE_LIKE_RE = re.compile(r"(\.[a-z0-9]{2,4}$|[*?]|yyyy|ccyy|mmdd)", re.IGNORECASE)


def _truncate(text: str, limit: int) -> str:
    text = text.replace("\r", "")
    return text if len(text) <= limit else text[:limit] + "…"


def _pointer_target(text: str, phrases: list[str]) -> str | None:
    """The clause a pointer sentence names ("the File Details tab of the
    mapping document"), or None when no phrase matches."""
    lowered = text.lower()
    for phrase in phrases:
        at = lowered.find(phrase.lower())
        if at < 0:
            continue
        clause = re.sub(r"\s+", " ", text[at + len(phrase):]).strip(" .:;,")
        clause = re.split(r"\battached\b|\.\s", clause, maxsplit=1)[0].strip(" .:;,")
        return clause or phrase
    return None


def _nested_rows(rows: list[list[str]], header_words: list[str]) -> tuple[list[str], list]:
    """(headers, StructuredRow list) — the first row is a header when one of
    its cells is a header word and none is file-like."""
    from codegen.contracts.frd import StructuredRow

    words = {normalize_label(w) for w in header_words}
    headers: list[str] = []
    body = rows
    if rows and any(normalize_label(c) in words for c in rows[0]) and not any(
            _FILE_LIKE_RE.search(c) for c in rows[0]):
        headers = [c.strip() for c in rows[0]]
        body = rows[1:]
    names: list[str] = []
    for i in range(max((len(r) for r in rows), default=0)):
        name = headers[i] if i < len(headers) and headers[i] else f"col{i + 1}"
        while name in names:                      # duplicate headers ("FileName" twice)
            name = f"{name}_{names.count(name) + 1}"
        names.append(name)
    out = []
    for row in body:
        cells = [c.strip() for c in row]
        if not any(cells):
            continue
        keyed = {names[i]: c for i, c in enumerate(cells)}
        # The row's key is its file name when a cell looks like one (the
        # Object Name table keys on the vendor otherwise), else column 1.
        key = next((c for c in cells if _FILE_LIKE_RE.search(c)), cells[0])
        out.append(StructuredRow(key=key, values=keyed))
    return headers, out


def _per_file_blocks(text: str, labels: dict[str, str]) -> list:
    """Blocks introduced by a heading line ("<File> file Ingestion from
    <Src>:") holding "Label = value" / "Label: value" lines; labels are read
    with the synonym table (unknown labels keep their own spelling)."""
    from codegen.contracts.frd import StructuredRow

    blocks: list = []
    current: StructuredRow | None = None
    for line in text.split("\n"):
        if not line.strip():
            continue
        heading = _HEADING_LINE_RE.match(line)
        if heading:
            current = StructuredRow(key=heading.group(1).strip(), values={})
            blocks.append(current)
            continue
        pair = _LABEL_VALUE_RE.match(line)
        if pair and current is not None:
            key = labels.get(normalize_label(pair.group(1))) or pair.group(1).strip()
            current = current.model_copy(update={"values": {**current.values,
                                                            key: pair.group(2).strip()}})
            blocks[-1] = current
    return [b for b in blocks if b.values]


def _block_pairs(value: str) -> list[tuple[str | None, str]]:
    """(label, value) pairs of a multi-line block. Two spellings, freely
    mixed: ``Label: value`` on one line, and the STANZA the real pair-1 cell
    uses — a ``Label:`` line, then its value(s) on the following line(s). A
    line under no label is a (None, value) pair."""
    pairs: list[tuple[str | None, str]] = []
    pending: str | None = None
    for line in value.split("\n"):
        text = line.strip()
        if not text:
            continue
        label, sep, rest = text.partition(":")
        if sep and label.strip() and not rest.strip():
            pending = label.strip()                    # "Label:" — the value follows
            continue
        if sep and label.strip() and rest.strip() and not _FILE_LIKE_RE.search(label):
            pairs.append((label.strip(), rest.strip()))
            pending = None
            continue
        pairs.append((pending, text))
    return pairs


def _table_pairs(nested: list[list[str]], names: set[str]) -> list[tuple[str | None, str]] | None:
    """(label, value) pairs of a nested label | value table: two columns, the
    first holding labels (no header row), or a header row whose columns are
    labels (each body cell a pair under its header). None for anything else
    — a several-column table with one row per FILE keeps the M7 reading."""
    rows = [[c.strip() for c in row] for row in nested if any(c.strip() for c in row)]
    if not rows:
        return None
    header = [normalize_label(c.rstrip(":")) for c in rows[0]]
    if len(rows) == 2 and all(h in names for h in header if h) and any(header):
        # A header row of labels over ONE body row.
        return [(rows[0][i].rstrip(":").strip(), cell) for i, cell in enumerate(rows[1]) if cell]
    if all(len([c for c in row if c]) <= 2 and len(row) >= 2 for row in rows) and any(
            normalize_label(row[0].rstrip(":")) in names for row in rows):
        return [(row[0].rstrip(":").strip() or None, row[1]) for row in rows if row[1]]
    return None


def parse_object_name_block(value: str, nested: list[list[str]] | None,
                            config: FrdExtractorConfig):
    """``(feed name | None, StructuredRows of files)`` for an Object Name cell
    that is a BLOCK — a nested label | value table or several lines — else
    None. The feed name is the value under a ``feed_name`` label; a file is
    the value under a ``file_name`` label, or any file-like value under
    another label (the real cell labels each file with its line of
    business). Nothing else in the block becomes a value."""
    from codegen.contracts.frd import StructuredRow

    labels = config.object_name_labels
    feed_labels = {normalize_label(s) for s in labels.get("feed_name", [])}
    file_labels = {normalize_label(s) for s in labels.get("file_name", [])}
    if nested:
        pairs = _table_pairs(nested, feed_labels | file_labels)
    elif "\n" in value:
        pairs = _block_pairs(value)
    else:
        pairs = None
    if not pairs:
        return None
    feed_name: str | None = None
    files: list = []
    for label, text in pairs:
        key = normalize_label(label) if label else ""
        single = "\n" not in text and len(text) <= _FEED_NAME_MAX
        if key in feed_labels and single and not _FILE_LIKE_RE.search(text):
            feed_name = feed_name or text
        elif label and (key in file_labels or _FILE_LIKE_RE.search(text)) and " " not in text:
            # Only a LABELLED value: a flattened table ("Vendor / FileName /
            # VENDOR_A / x.csv", one cell per line) has no label to read by and
            # keeps the M7 refusal.
            files.append(StructuredRow(key=text, values={"label": label}))
    if feed_name is None and not files:
        return None
    return feed_name, files


_FEED_NAME_MAX = 80


def parse_layer_blocks(value: str, config: FrdExtractorConfig) -> dict[str, dict[str, str]] | None:
    """``{"stage": {"table": …, "schema": …}, "standard": {…}}`` for a cell
    holding inline layer blocks (module docstring of the config knob); None
    when the cell has no layer heading. Lines that are neither a heading nor
    a known "Label: value" are ignored — never taken as a table name."""
    words = {normalize_label(w) for w in config.layer_block_heading_words}
    if not value or not words:
        return None
    markers = {normalize_label(m): layer for layer, spellings in
               config.target_schema_markers.items() for m in spellings}
    labels = {normalize_label(s): slot for slot, spellings in config.layer_block_labels.items()
              for s in spellings}
    blocks: dict[str, dict[str, str]] = {}
    current: str | None = None
    for line in value.split("\n"):
        text = line.strip()
        if not text:
            continue
        heading = normalize_label(text.rstrip(":")).split(" ")
        if len(heading) == 2 and heading[0] in markers and heading[1] in words:
            current = markers[heading[0]]
            blocks.setdefault(current, {})
            continue
        pair = _PAIR_RE.match(text)
        if pair and current is not None:
            slot = labels.get(normalize_label(pair.group(1)))
            if slot is not None and pair.group(2).strip():
                blocks[current].setdefault(slot, pair.group(2).strip())
    return blocks or None


def classify_cell(content: DocxContent, source: FrdFieldSource, field: str, value: str,
                  config: FrdExtractorConfig, labels: dict[str, str],
                  own_keys: set[str]):
    """The StructuredValue a single-line field's cell amounts to, or None
    when the cell is an ordinary scalar. Order: nested table → pointer →
    label-prefixed → per-file blocks → remaining line break."""
    from codegen.contracts.frd import StructuredValue

    if field not in config.single_line_fields:
        return None
    base = {"table": source.table, "row": source.row, "col": source.value_col or source.col,
            "label": source.label,
            "text": _truncate(value, config.structured_text_max_chars)}
    nested = content.nested.get((source.table, source.row, source.value_col or source.col))
    if field == "feed_name" and (nested or value):
        # M9.1b: a BLOCK Object Name cell is read per line / row.
        block = parse_object_name_block(value, nested, config)
        if block is not None:
            feed_name, files = block
            return StructuredValue(kind="labelled_files", rows=files, feed_name=feed_name,
                                   **base)
    if nested:
        headers, rows = _nested_rows(nested, config.nested_table_header_words)
        return StructuredValue(kind="nested_table", headers=headers, rows=rows, **base)
    if not value:
        return None
    if field.endswith("_target.schema") and parse_layer_blocks(value, config):
        return None          # an inline layer block: parsed per layer by read_frd
    target = _pointer_target(value, config.pointer_phrases)
    if target is not None:
        return StructuredValue(kind="pointer", target=target, **base)
    prefixed = _PREFIXED_RE.match(value)
    if prefixed and labels.get(normalize_label(prefixed.group(1))) not in own_keys:
        return StructuredValue(kind="label_prefixed", prefix_label=prefixed.group(1).strip(),
                               **base)
    blocks = _per_file_blocks(value, labels)
    if blocks:
        return StructuredValue(kind="per_file_blocks", rows=blocks, **base)
    if "\n" in value:
        return StructuredValue(kind="multiline", **base)
    return None


# 2026-10-13 (pair_12, CAQH): one cell states BOTH labels, on two lines —
# "Domain: Member\nSub Domain: Third Party Liability". "Sub Domain" is tried
# first at each position, and a bare "domain" never matches inside "subdomain".
_DOMAIN_LABEL_RE = re.compile(r"(?i)(?<![a-z])(sub[\s_-]*domain|domain)\s*[:=]")


def split_domain_labels(text: str | None) -> tuple[str | None, str | None] | None:
    """``(domain, sub domain)`` when the cell carries a ``Domain:`` AND a
    ``Sub Domain:`` label (any case; ``Sub-Domain`` / ``Subdomain`` /
    ``Sub_Domain``; ``:`` or ``=``; any separator between them, either order);
    None for any other cell — a plain value reads as before."""
    if not text:
        return None
    marks = list(_DOMAIN_LABEL_RE.finditer(text))
    kinds = ["domain" if m.group(1).lower() == "domain" else "sub_domain" for m in marks]
    if sorted(kinds) != ["domain", "sub_domain"]:
        return None
    values: dict[str, str | None] = {}
    for index, (mark, kind) in enumerate(zip(marks, kinds, strict=True)):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        values[kind] = text[mark.end():end].strip(" \t\r\n;,|/") or None
    return values["domain"], values["sub_domain"]


def _lobs_and_table(content: DocxContent, profile: FrdLayoutProfile, prefix: str, text: str,
                    frd_config, flags: list[str], cell_of) -> tuple[list[str], list[dict]]:
    """The feed's LOBs. 2026-10-14 (D1 pair_12): a LOB cell holding a Region /
    LOB table (a nested table, or flattened one cell per line under its header
    row) is read as rows — ``lobs`` = its LOB column's distinct codes, the rows
    kept for the resolver to key each file to ONE LOB. Else the cell's list."""
    from codegen.resolve.files import lob_column, lob_table_from_lines, lob_table_from_rows

    source = profile.fields.get(f"{prefix}.lobs")
    nested = (content.nested.get((source.table, source.row, source.col))
              if source is not None else None)
    table = lob_table_from_rows(nested, frd_config.lob_table_lob_headers) if nested else []
    if not table:
        table = lob_table_from_lines(_split(text, ["\n"]), frd_config.lob_table_lob_headers,
                                     [*frd_config.lob_table_plan_headers,
                                      *frd_config.lob_table_region_headers])
    column = lob_column(table, frd_config.lob_table_lob_headers)
    if column is None:
        return _split(text, frd_config.list_separators), []
    lobs = list(dict.fromkeys(row[column] for row in table if row.get(column)))
    flags.append(f"frd_lob_table:{prefix}.lobs — the {cell_of(f'{prefix}.lobs')} cell is a "
                 f"table ({', '.join(table[0])}; {len(table)} row(s)): the LOBs are its "
                 f"{column} column ({len(lobs)} distinct); each file takes ONE row's LOB, "
                 "keyed by the file name at resolve time — the table is never a cell value")
    return lobs, table


def _split(text: str, separators: list[str]) -> list[str]:
    if not text:
        return []
    parts = re.split("|".join(re.escape(s) for s in separators), text)
    return [p.strip() for p in parts if p.strip()]


def _parse_target_schema(text: str, config: FrdExtractorConfig) -> tuple[
        tuple[str | None, str | None], tuple[str | None, str | None]]:
    """"STG: a.b; STD: c.d" → ((a, b), (c, d)); "a.b (stage), c.d (standard)"
    the same (Chunk B: the layer marker in parentheses AFTER the value);
    "x / y" → stage x, standard y; a single value → stage only. Each part
    splits on its last '.' into catalog.schema; a part without '.' is a
    schema."""
    def _part(value: str | None) -> tuple[str | None, str | None]:
        if not value:
            return None, None
        value = value.strip().rstrip(";,")
        if "." in value:
            catalog, _, schema = value.rpartition(".")
            return catalog.strip() or None, schema.strip() or None
        return None, value
    stage = standard = None
    for marker in config.target_schema_markers.get("stage", []):
        match = re.search(rf"(?i)\b{re.escape(marker)}\s*:\s*([^\s;,]+)", text)
        if match:
            stage = match.group(1)
            break
    for marker in config.target_schema_markers.get("standard", []):
        match = re.search(rf"(?i)\b{re.escape(marker)}\s*:\s*([^\s;,]+)", text)
        if match:
            standard = match.group(1)
            break
    if stage is None and standard is None:
        for layer in ("stage", "standard"):
            for marker in config.target_schema_markers.get(layer, []):
                match = re.search(rf"(?i)([^\s;,()]+)\s*\(\s*{re.escape(marker)}\s*\)", text)
                if match:
                    if layer == "stage":
                        stage = match.group(1)
                    else:
                        standard = match.group(1)
                    break
    if stage is None and standard is None:
        parts = _split(text, config.target_schema_separators)
        stage = parts[0] if parts else None
        standard = parts[1] if len(parts) > 1 else None
    return _part(stage), _part(standard)


_CADENCE_RE = re.compile(r"\b(daily|weekly|monthly|quarterly|yearly|annual(?:ly)?)\b",
                         re.IGNORECASE)
_MENTION_LIMIT = 12
_MENTION_CHARS = 120


def frequency_mentions(content: DocxContent) -> list[str]:
    """Every sentence of the document that names a cadence, with where it
    sits ("'Frequency of data refresh – Monthly Run' (FRD paragraph 229)"):
    body paragraphs first, then table cells; distinct texts, bounded. The
    FREQUENCY normaliser compares their tokens with the delivery statement."""
    found: list[str] = []
    seen: set[str] = set()
    sources = [(f"FRD paragraph {i}", text) for i, (_t, text) in enumerate(content.paragraphs)]
    sources += [(f"FRD table {t} row {r}", cell) for t, table in enumerate(content.tables)
                for r, row in enumerate(table) for cell in row]
    for where, text in sources:
        for sentence in re.split(r"(?<=[.;])\s+|\n+", text or ""):
            sentence = " ".join(sentence.split())
            key = sentence.lower()
            if not sentence or key in seen or not _CADENCE_RE.search(sentence):
                continue
            seen.add(key)
            shown = (sentence if len(sentence) <= _MENTION_CHARS
                     else sentence[:_MENTION_CHARS] + "…")
            found.append(f"{shown!r} ({where})")
            if len(found) >= _MENTION_LIMIT:
                return found
    return found


def read_frd(content: DocxContent, profile: FrdLayoutProfile, config: Config, *,
             document_name: str, generated_date: str, contract_name: str | None = None
             ) -> FrdContract:
    frd_config = config.extractor.frd
    evidence: dict[str, FieldEvidence] = {}
    ambiguities: list[str] = []
    structured: dict = {}
    labels = _lookup(frd_config.labels)
    mentions = frequency_mentions(content)

    def get(path: str) -> str:
        source = profile.fields.get(path)
        if source is None:
            return ""
        value = _value(content, source, frd_config)
        evidence[path] = FieldEvidence(
            table=source.table, row=source.row, col=source.col, label=source.label,
            section=source.section, inline_label=source.inline_label, source=profile.source)
        clean = path.split("#", 1)[0]
        field = clean.split(".", 1)[1] if "." in clean else clean
        own = {k for k, v in {**_SCALAR_FIELDS, **_FALLBACK_FIELDS}.items() if v == field}
        if field == "domain":
            own |= {"domain_subdomain", "domain"}
        if field in ("domain", "sub_domain") and split_domain_labels(value):
            return value            # two labelled lines: split where the feed is built
        refused = classify_cell(content, source, field, value, frd_config, labels, own)
        if refused is not None:
            structured[clean] = refused
            detail = {"pointer": f" → {refused.target}",
                      "label_prefixed": f" (label {refused.prefix_label!r} is not the field)",
                      "nested_table": f" ({len(refused.rows)} nested row(s))",
                      "per_file_blocks": f" ({len(refused.rows)} block(s))",
                      "labelled_files": f" ({len(refused.rows)} '<label>: <file>' line(s))",
                      "multiline": ""}[refused.kind]
            ambiguities.append(f"frd_{refused.kind}:{clean}{detail} — table {source.table} "
                               f"row {source.row}; unstated, resolved from the other documents")
            return ""
        if not value:
            ambiguities.append(f"{path}: label {source.label!r} present, value blank "
                               f"(table {source.table} row {source.row})")
        return value

    def _landing(prefix: str) -> str:
        path = f"{prefix}.landing_location"
        primary = get(path)
        confirming_key = f"{path}#confirming"
        if confirming_key not in profile.fields:
            return primary
        confirming = get(confirming_key)
        if primary:
            evidence[f"{path} (confirming)"] = evidence.pop(confirming_key)
            return primary
        if confirming and not re.search(r"[\\/]", confirming):
            # "Inbound" alone is a direction word, not a folder path.
            ambiguities.append(f"{path}: the folder-path label holds {confirming!r}, which "
                               "names no path; ignored")
            return ""
        if confirming:
            evidence[path] = evidence.pop(confirming_key)
        return confirming

    def get_with_fallback(path: str) -> str:
        value = get(path)
        if not value and path in structured and path.endswith(".feed_name"):
            # A nested Object Name table names SEVERAL files: the section's
            # own "Name" row is a section title, not this feed's name — the
            # layout stage names the derived feeds after the STTM stage band.
            return ""
        if not value and f"{path}#fallback" in profile.fields:
            value = get(f"{path}#fallback")
            if value:
                evidence[path] = evidence.pop(f"{path}#fallback")
        return value

    def cell_of(path: str) -> str:
        source = profile.fields.get(path)
        return (f"table {source.table} row {source.row} ({source.label!r})" if source
                else "no label cell")

    def _domain_fields(prefix: str, domain_text: str, domain_parts: list[str]) -> dict:
        labelled, path = split_domain_labels(domain_text), f"{prefix}.domain"
        sub_text = ""
        if labelled is None and len(domain_parts) <= 1:
            sub_text = get(f"{prefix}.sub_domain")
            labelled, path = split_domain_labels(sub_text), f"{prefix}.sub_domain"
        if labelled is None:
            return {"domain": domain_parts[0] if domain_parts else None,
                    "sub_domain": domain_parts[1] if len(domain_parts) > 1 else sub_text or None}
        flags.append(f"frd_domain_labels_split:{prefix} — the {cell_of(path)} cell states "
                     f"'Domain:' and 'Sub Domain:' on one cell: domain {labelled[0]!r}, "
                     f"sub domain {labelled[1]!r}")
        return {"domain": labelled[0], "sub_domain": labelled[1]}

    flags: list[str] = []
    feeds: list[FrdFeed] = []
    for feed_index in range(max(profile.feed_count, 1)):
        prefix = f"feeds[{feed_index}]"
        feed_name = get_with_fallback(f"{prefix}.feed_name")
        if (profile.family == "F2" and feed_name and f"{prefix}.feed_name" not in profile.fields
                and not _plain_name(feed_name)):
            # Chunk B (cold drill): an F2 "Name" row names the Solution
            # Requirement ("Receive monthly eligibility file"), not the feed:
            # a sentence there leaves the feed unnamed (the layout stage names
            # it after the STTM stage band), flagged below.
            evidence.pop(f"{prefix}.feed_name", None)
            feed_name = ""
        source_system = get_with_fallback(f"{prefix}.source_system")
        domain_text = get(f"{prefix}.domain")
        domain_parts = _split(domain_text, frd_config.domain_separators)
        schema_text = get(f"{prefix}.stage_target.schema")
        tables_text = get(f"{prefix}.stage_target.tables")
        get(f"{prefix}.standard_target.tables")   # same cell; records its evidence
        # M9.3: inline layer blocks ("Staging Layer:" / "Table: …") in either
        # target cell are parsed per layer; no line of one is a table name.
        blocks: dict[str, dict[str, str]] = {}
        for path, cell_text in ((f"{prefix}.stage_target.schema", schema_text),
                                (f"{prefix}.stage_target.tables", tables_text)):
            parsed = parse_layer_blocks(cell_text, frd_config)
            if not parsed:
                continue
            for layer, slots in parsed.items():
                for slot, slot_value in slots.items():
                    blocks.setdefault(layer, {}).setdefault(slot, slot_value)
            stated = "; ".join(f"{layer} {slot}={v!r}" for layer, slots in parsed.items()
                               for slot, v in slots.items())
            flags.append(f"frd_layer_block:{path} — inline layer block in {cell_of(path)}: "
                         f"{stated or 'no labelled value'}; read per layer, never as a table "
                         "name")
        if parse_layer_blocks(schema_text, frd_config):
            schema_text = ""
        (stage_catalog, stage_schema), (std_catalog, std_schema) = _parse_target_schema(
            schema_text, frd_config)
        if parse_layer_blocks(tables_text, frd_config):
            tables = [blocks["stage"]["table"]] if blocks.get("stage", {}).get("table") else []
            standard_tables = ([blocks["standard"]["table"]]
                               if blocks.get("standard", {}).get("table") else [])
        else:
            tables = _split(tables_text, frd_config.list_separators)
            standard_tables = list(tables) if std_schema or std_catalog else []
        stage_schema = stage_schema or blocks.get("stage", {}).get("schema")
        stage_catalog = stage_catalog or blocks.get("stage", {}).get("catalog")
        std_schema = std_schema or blocks.get("standard", {}).get("schema")
        std_catalog = std_catalog or blocks.get("standard", {}).get("catalog")
        # M9.3: an Object Name cell that lists "<label>: <file>" lines names
        # the feed's FILES, not the feed.
        listed = structured.get(f"{prefix}.feed_name")
        file_name_patterns: list[str] = []
        if listed is not None and listed.kind == "labelled_files":
            file_name_patterns = [row.key for row in listed.rows]
            if file_name_patterns:
                flags.append(f"file_pattern_from_object_name:{prefix} — the FRD "
                             f"{cell_of(f'{prefix}.feed_name')} cell is a block listing "
                             f"{len(listed.rows)} file(s) under "
                             f"{[row.values.get('label') for row in listed.rows]}; taken as "
                             f"the file name patterns {file_name_patterns}")
            if listed.feed_name and not feed_name:
                # The block's own "Object Name: …" / "Name | …" value — a
                # parsed label value, never the raw block text.
                feed_name = listed.feed_name
                flags.append(f"frd_object_name_block:{prefix} — feed name {feed_name!r} read "
                             f"from a labelled line / row of the "
                             f"{cell_of(f'{prefix}.feed_name')} block")
        elif feed_name and _names_one_file(feed_name):
            # Chunk B (cold drill): a one-line Object Name that IS a file name
            # pattern ("CH_CLAIMS_DAILY_YYYYMMDD.psv") names the feed's FILE,
            # not the feed: taken as its pattern; the feed is named by the
            # section's Name row when that is a plain name, else left unnamed
            # (the layout stage names it after the STTM stage band).
            file_name_patterns = [feed_name]
            object_cell = cell_of(f"{prefix}.feed_name")
            name_row = (get(f"{prefix}.feed_name#fallback")
                        if f"{prefix}.feed_name#fallback" in profile.fields else "")
            flags.append(f"file_pattern_from_object_name:{prefix} — the FRD {object_cell} cell "
                         f"{feed_name!r} is a file name pattern; taken as the file name "
                         "pattern, not the feed name")
            feed_name = name_row if _plain_name(name_row) else ""
            if feed_name:
                evidence[f"{prefix}.feed_name"] = evidence.pop(f"{prefix}.feed_name#fallback")
                flags.append(f"frd_feed_name_from_name_row:{prefix} — feed name {feed_name!r} "
                             f"from the {cell_of(f'{prefix}.feed_name#fallback')} cell")
        # Multi-file FRD: a refused nested table (or multiline / per-file
        # blocks) in the Object Name cell may hold file-like patterns that
        # belong in file_name_patterns.  Split on ';' and newlines; treat
        # CCYY_MM and YYYY_MM as the same pattern.
        if not file_name_patterns and listed is not None:
            file_name_patterns = _extract_patterns_from_structured(listed)
            if file_name_patterns:
                flags.append(
                    f"file_pattern_from_{listed.kind}:{prefix} — the "
                    f"{cell_of(f'{prefix}.feed_name')} cell contains "
                    f"{len(file_name_patterns)} file pattern(s): "
                    f"{file_name_patterns}")
        rules = []
        n = 0
        while f"{prefix}.validation_rules[{n}]" in profile.fields:
            source = profile.fields[f"{prefix}.validation_rules[{n}]"]
            value = get(f"{prefix}.validation_rules[{n}]")
            if value:
                rules.append(f"{source.label}: {value}" if source.labelled_rule else value)
            n += 1
        stage_strategy = _strategy(get(f"{prefix}.stage_target.load_strategy"),
                                   f"{prefix}.stage_target.load_strategy", ambiguities,
                                   frd_config.load_strategy_synonyms)
        std_strategy = _strategy(get(f"{prefix}.standard_target.load_strategy"),
                                 f"{prefix}.standard_target.load_strategy", ambiguities,
                                 frd_config.load_strategy_synonyms)
        if std_strategy is not None and tables and not standard_tables:
            # post118 (codeflow audit #1): layer scope comes from Load Strategy
            # (CLAUDE.md) — an STD load strategy makes the feed two-layer even when
            # the Target Schema block names no standard schema (it used to be
            # read as stage-only)
            standard_tables = list(tables)
            flags.append(f"frd_standard_from_load_strategy:{prefix} — the FRD "
                         f"{cell_of(f'{prefix}.standard_target.load_strategy')} states the "
                         f"standard load strategy {std_strategy!r} while the Target Schema "
                         "block names no standard schema; the standard layer carries the "
                         "stage table names")
        lobs, lob_table = _lobs_and_table(content, profile, prefix, get(f"{prefix}.lobs"),
                                          frd_config, flags, cell_of)
        named = feed_name or unnamed_feed_name(document_name, feed_index)
        system = source_system or UNSTATED_SOURCE
        for field, value in (("feed_name", named), ("source_system", system)):
            path = f"{prefix}.{field}"
            _require_one_line(path, value, evidence.get(path) or profile.fields.get(path))
        feeds.append(FrdFeed(
            feed_name=named,
            source_system=system,
            file_name_patterns=file_name_patterns,
            file_format=get(f"{prefix}.file_format") or None,
            delimiter=None,
            record_segments=[],
            frequency=get(f"{prefix}.frequency") or None,
            load_windows_sla=[],
            lobs=lobs,
            lob_table=lob_table,
            **_domain_fields(prefix, domain_text, domain_parts),
            landing_location=_landing(prefix) or None,
            stage_target=TargetSpec(catalog=stage_catalog, schema=stage_schema, tables=tables,
                                    load_strategy=stage_strategy),
            standard_target=TargetSpec(catalog=std_catalog, schema=std_schema,
                                       tables=standard_tables, load_strategy=std_strategy),
            validation_rules=rules,
            recycle_rule=get(f"{prefix}.recycle_rule") or None,
            history_backfill=None,
            archive_retention=get(f"{prefix}.archive_retention") or None,
            phi_pii_notes=get(f"{prefix}.phi_pii_notes") or None,
            key_statement=get(f"{prefix}.key_statement") or None,
            sttm_reference=get(f"{prefix}.sttm_reference") or None,
            requirement_ids=_split(get(f"{prefix}.requirement_ids"), frd_config.list_separators),
            frequency_mentions=mentions,
        ))
        if not feed_name:
            ambiguities.append(f"{prefix}.feed_name: unsourced (no Object Name / Name label)")
            # Never a silent default (M9.3): the placeholder name is flagged,
            # with the cell that failed to name the feed.
            why = (f"the {cell_of(f'{prefix}.feed_name')} cell is a {listed.kind} value, not a "
                   "name" if listed is not None else
                   f"no Object Name value ({cell_of(f'{prefix}.feed_name')}) and no usable "
                   "Name row")
            flags.append(f"frd_feed_name_unstated:{prefix} — {why}; placeholder "
                         f"{unnamed_feed_name(document_name, feed_index)!r} until the layout "
                         "stage names the feed after the STTM stage band")
        if not source_system:
            ambiguities.append(f"{prefix}.source_system: unsourced (no Data Source / Vendor "
                               "Name label)")
    for item in profile.unresolved:
        ambiguities.append(f"{item.field}: {item.reason}")

    project_name = next((text for index, text in content.paragraphs if index == 0),
                        Path(document_name).stem)
    acd = _acd_items(content, frd_config)
    status = "PASS_WITH_FLAGS" if ambiguities else "PASS"
    sourced = len([k for k in evidence if "#" not in k])
    contract_name = contract_name or f"FRD feed contract extracted from {document_name}"
    _require_one_line("contract_name", contract_name, None)
    return FrdContract(
        contract_name=contract_name,
        generated_from_frd=document_name,
        generated_date=datetime.fromisoformat(generated_date),
        generator=f"codegen extract-frd (docx family {profile.family}, layout "
                  f"source {profile.source})",
        status=status,
        project=ProjectInfo(project_id=None, project_name=project_name,
                            business_context_summary=None),
        in_scope=[],
        out_of_scope=[],
        assumptions_constraints_dependencies=acd,
        feeds=feeds,
        system_interfaces=[],
        open_items=[],
        provenance=Provenance(
            enrichments=[],
            ambiguities=ambiguities,
            grounding=GroundingSummary(strict_checked=sourced, strict_failed=[],
                                       advisory_checked=len(profile.unresolved),
                                       advisory_flagged=[u.field for u in profile.unresolved]),
        ),
        field_provenance={k: v for k, v in evidence.items()
                          if "#" not in k or k.endswith("(confirming)")},
        layout=FrdLayoutSummary(family=profile.family, source=profile.source,
                                fingerprint=profile.fingerprint,
                                unresolved=[f"{u.field}: {u.reason}" for u in profile.unresolved]),
        structured=_requirement_landing_blocks(content, frd_config, structured, feeds,
                                               ambiguities),
        extraction_flags=flags,
    )


def _requirement_landing_blocks(content: DocxContent, config: FrdExtractorConfig,
                                structured: dict, feeds: list, ambiguities: list) -> dict:
    """post84 (pair_11): ONE feed whose landing is unstated (its ADLS Location
    cell lists several paths, or none) gets the Solution Requirements' own
    landing lines as per-file blocks — the layout stage then gives every
    derived feed the block whose requirement Name names it
    (``layout.resolve.resolve_structured_fields``); nothing is picked here."""
    key = "feeds[0].landing_location"
    current = structured.get(key)
    if len(feeds) != 1 or feeds[0].landing_location or (
            current is not None and current.kind != "multiline"):
        return structured
    found = requirement_landings(content, config)
    if not found:
        return structured
    from codegen.contracts.frd import StructuredRow, StructuredValue

    _name, _path, table, row = found[0]
    ambiguities.append(f"frd_requirement_landing:{key} — {len(found)} Solution Requirement(s) "
                       "state their own landing; given per derived feed by requirement name")
    return {**structured, key: StructuredValue(
        kind="per_file_blocks", table=table, row=row, col=1,
        label=config.requirement_landing_labels[0],
        rows=[StructuredRow(key=name, values={"path": path}) for name, path, _t, _r in found])}


def _names_one_file(value: str) -> bool:
    """A single token that reads as a file name pattern (an extension, a
    wildcard or a date placeholder), never a sentence."""
    text = value.strip()
    return bool(text) and not any(c.isspace() for c in text) and bool(_FILE_LIKE_RE.search(text))


def _extract_patterns_from_structured(sv) -> list[str]:
    """File-like patterns from a StructuredValue the reader refused as a scalar.

    Only ``nested_table`` and ``per_file_blocks`` are handled — their rows are
    structured data keyed on the file-like cell (the SD FRD's ``Vendor |
    INB/OUB | FileName`` table).  ``multiline`` text is NOT split: its flat
    dump may contain a single incidental file name among non-file content,
    and extracting it would steal a pattern from the real source (e.g.  the
    FRD's labelled-files block or the layout stage's per-file derivation).

    A pattern is a token ``_FILE_LIKE_RE`` matches (an extension, a wildcard,
    or a date placeholder like YYYY / CCYY).  At least two file-like rows must
    be present — a single file was already handled by the ``_names_one_file``
    branch."""
    if sv.kind not in ("nested_table", "per_file_blocks"):
        return []
    patterns = [row.key for row in sv.rows if _FILE_LIKE_RE.search(row.key)]
    return patterns if len(patterns) >= 2 else []


def _canonical_pattern(name: str) -> str:
    """Normalise date placeholders so CCYY_MM and YYYY_MM compare equal."""
    return re.sub(r"(?i)ccyy", "yyyy", name.strip().lower())


def _name_similarity(a: str, b: str) -> float:
    """Token-overlap similarity (Jaccard on underscore-split stems)."""
    tokens_a = set(re.split(r"[_\-.]+", _canonical_pattern(re.sub(r"\.[a-z0-9]{2,4}$", "", a))))
    tokens_b = set(re.split(r"[_\-.]+", _canonical_pattern(re.sub(r"\.[a-z0-9]{2,4}$", "", b))))
    tokens_a.discard("")
    tokens_b.discard("")
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))


def _split_multi_file_feeds(
    feeds: list[FrdFeed],
    flags: list[str],
    ambiguities: list[str],
    document_name: str,
) -> list[FrdFeed]:
    """When a single feed lists >1 file family AND >1 target table, split into
    one feed per target table and propose the file→table pairing by name
    similarity as a QUESTION the person confirms."""
    if len(feeds) != 1:
        return feeds
    feed = feeds[0]
    tables = feed.stage_target.tables
    patterns = feed.file_name_patterns
    if len(tables) <= 1 or len(patterns) <= 1:
        return feeds

    # Greedy best-match assignment: for each table pick the most-similar
    # unassigned pattern; any leftover patterns go to the last feed.
    remaining = list(patterns)
    assignments: list[tuple[str, str | None]] = []
    for table in tables:
        if not remaining:
            assignments.append((table, None))
            continue
        best = max(remaining, key=lambda p: _name_similarity(p, table))
        assignments.append((table, best))
        remaining.remove(best)

    split: list[FrdFeed] = []
    for idx, (table, pattern) in enumerate(assignments):
        extra_patterns = remaining if idx == len(assignments) - 1 else []
        pats = ([pattern] if pattern else []) + extra_patterns
        split.append(feed.model_copy(update={
            "feed_name": unnamed_feed_name(document_name, idx),
            "file_name_patterns": pats,
            "stage_target": feed.stage_target.model_copy(update={"tables": [table]}),
            "standard_target": feed.standard_target.model_copy(
                update={"tables": [table] if feed.standard_target.tables else []}),
        }))
        sim = _name_similarity(pattern, table) if pattern else 0.0
        flags.append(
            f"QUESTION multi_file_split:feeds[{idx}] — proposed pairing: "
            f"file {pattern!r} → table {table!r} (similarity {sim:.2f}); "
            "confirm or override in the answers file")

    ambiguities.append(
        f"multi_file_frd:feeds[0] → split 1 feed into {len(split)} feeds "
        f"(one per target table); file→table pairings are PROPOSED by name "
        "similarity — confirm each")
    return split


def _require_one_line(path: str, value: str,
                      source: FieldEvidence | FrdFieldSource | None) -> None:
    """post159 (P1-4, CS-2): a value that reaches the generated banners must be
    one printable line (``contracts.frd.banner_text_problem``). A cell holding
    a line break / control character the block readers did not take apart is
    a located error naming the cell by position (0-based in the message like
    every reader line, 1-based in the coordinates) - never stripped, never
    guessed. ``source`` None = the value is no cell (the document's name, the
    --contract-name argument)."""
    position = banner_text_problem(value)
    if position is None:
        return
    where = (f"table {source.table} row {source.row}" if source is not None
             else "the document name / --contract-name")
    coord = (Coord("FRD", table=source.table + 1, row=source.row + 1) if source is not None
             else Coord("FRD"))
    raise located(FrdDocxError(
        f"{path}: {where} holds a line break or control character at character "
        f"{position}; the value reaches the generated files' banners and must be one "
        "printable line - fix the cell"), coord, BANNER_TEXT_REASON)


def _plain_name(value: str) -> bool:
    """A Name-row value usable as a feed name: one token, not a file name."""
    text = (value or "").strip()
    return (bool(text) and len(text) <= _FEED_NAME_MAX and not any(c.isspace() for c in text)
            and not _FILE_LIKE_RE.search(text))


_UNNAMED_SUFFIX = "(unnamed)"


def unnamed_feed_name(document_name: str, feed_index: int) -> str:
    return f"{document_name} feed {feed_index + 1} {_UNNAMED_SUFFIX}"


def is_unnamed_feed(feed_name: str) -> bool:
    """True for the placeholder ``read_frd`` gives a feed no cell names."""
    return feed_name.endswith(_UNNAMED_SUFFIX)


_TRAILING_PARENTHETICAL = re.compile(r"\s*\([^()]*\)\s*$")


def _strategy(value: str, path: str, ambiguities: list[str],
              synonyms: dict[str, str] | None = None):
    """The cell's load strategy: one of the canonical three or a configured
    synonym (post94), the cell as written or without a trailing parenthetical
    explanation ('Truncate & Load (Delete existing records ...)')."""
    if not value:
        return None
    spelled = {normalize_label(k): v for k, v in (synonyms or {}).items()}
    stripped = _TRAILING_PARENTHETICAL.sub("", value).strip()
    for text in dict.fromkeys([value, stripped]):
        label = normalize_label(text)
        for literal in _LOAD_STRATEGIES:
            if label == normalize_label(literal):
                return literal
        if label in spelled:
            return spelled[label]
    ambiguities.append(f"{path}: load strategy {value!r} is not one of {list(_LOAD_STRATEGIES)}; "
                       "left null")
    return None


def _acd_items(content: DocxContent, config: FrdExtractorConfig) -> list[AcdItem]:
    wanted = [normalize_label(h) for h in config.acd_headers]
    for rows in content.tables:
        if not rows or [normalize_label(c) for c in rows[0]][: len(wanted)] != wanted:
            continue
        items = []
        for row in rows[1:]:
            if len(row) < 3 or row[0].strip() not in _ACD_TYPES:
                continue
            items.append(AcdItem(name=row[1].strip(), description=row[2].strip(),
                                 acd_type=row[0].strip()))  # type: ignore[arg-type]
        return items
    return []


# --------------------------------------------------------------- entry points


def extract_frd_contract(path: Path, config: Config, *, contract_name: str | None = None,
                         generated_date: str | None = None
                         ) -> tuple[FrdContract, FrdLayoutProfile]:
    content = read_docx(path, prose_ok=True)
    profile = discover_frd(content, config.extractor.frd)
    contract = read_frd(content, profile, config, document_name=path.name,
                        generated_date=generated_date or datetime.now().date().isoformat(),
                        contract_name=contract_name)
    return contract, profile


def contract_to_json(contract: FrdContract) -> str:
    import json

    payload = contract.model_dump(mode="json", by_alias=True, exclude_defaults=True)
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


__all__ = [
    "DocxContent",
    "FrdDocxError",
    "classify_cell",
    "contract_to_json",
    "discover_frd",
    "extract_frd_contract",
    "is_unnamed_feed",
    "normalize_label",
    "parse_layer_blocks",
    "parse_object_name_block",
    "read_docx",
    "read_frd",
]
