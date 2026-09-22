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
  pairs inside the row-4 text are read with the same label synonyms.

Same discipline as the STTM path: :func:`discover_frd` builds an
:class:`~codegen.layout.frd_profile.FrdLayoutProfile` (positions + labels,
never values) from the label-synonym table in ``config/config.yaml``
``extractor.frd`` — populated only with the variants SHAPES_FOR_PORT §2
lists — and :func:`read_frd` copies cell text through it. Blank values stay
empty; a field with no source is null and listed as unresolved; every
sourced field records its table/row/col and the label seen. No python-docx.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from codegen.config import Config, FrdExtractorConfig
from codegen.contracts.frd import (
    AcdItem,
    FieldEvidence,
    FrdContract,
    FrdFeed,
    FrdLayoutSummary,
    GroundingSummary,
    ProjectInfo,
    Provenance,
    TargetSpec,
)
from codegen.layout.frd_profile import (
    FrdFieldSource,
    FrdLayoutProfile,
    FrdSectionRef,
    FrdUnresolved,
    frd_fingerprint,
)

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


def read_docx(path: Path) -> DocxContent:
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("word/document.xml"))
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise FrdDocxError(f"{path.name}: not a readable .docx ({exc})") from exc
    body = root.find(f"{_W}body")
    if body is None:
        raise FrdDocxError(f"{path.name}: document has no body")
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
    if not tables:
        raise FrdDocxError(f"{path.name}: document carries no tables")
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
    sr_prefix = normalize_label(config.solution_requirement_prefix)
    f1_tables = [(i, _section_key(t[0][0], sections)) for i, t in enumerate(tables)
                 if t and t[0] and _section_key(t[0][0], sections) is not None]
    # v0.7.2 (SHAPES_ROUND2 §1): the real F2 tables put "Solution Requirement:
    # N" in a cell MERGED across columns B-D, after a leading column — never
    # in column 0. Any cell of row 0 may carry it; sub-IDs ("2.1") and a
    # trailing title are allowed.
    sr_tables = [i for i, t in enumerate(tables)
                 if t and t[0] and _sr_title(t[0], sr_prefix) is not None]
    if f1_tables:
        return _discover_f1(tables, f1_tables, labels, digest, config)
    if sr_tables:
        profile = _discover_f2(tables, sr_tables, sections, labels, digest, config)
        if profile.sections:
            return profile
        # Requirement tables, none naming a metadata section: the
        # topic-organized family (M11 item 9).
        return _discover_f3(tables, sr_tables, labels, digest, config)
    return _discover_unrecognized(tables, digest)


def _table_class(rows: list[list[str]], classes: dict[str, list[str]],
                 labels: dict[str, str]) -> str:
    first = _first_cell(rows[0]) if rows and rows[0] else None
    if first is None:
        return "other"
    head = normalize_label(first[1])
    header_keys = {labels.get(normalize_label(c)) for c in rows[0] if c and c.strip()}
    if len(rows) >= 2 and "domain" in header_keys and header_keys <= {"domain", "sub_domain"}:
        return "domain"
    for kind, prefixes in classes.items():
        if any(head.startswith(normalize_label(p)) for p in prefixes):
            return kind
    return "other"


def _discover_f3(tables, sr_tables, labels, digest, config) -> FrdLayoutProfile:
    """M11 item 9 — F3, the topic-organized requirement document (SHAPES_
    ROUND2 §1.2 / §1.3): recognized and CLASSIFIED only. The one table read
    for a value is a Domain / SubDomain table (a header row over one value
    row); every other field is unresolved here and comes from the fallback
    chain, or from the layout model when live (through the validator)."""
    classes = {kind: list(prefixes) for kind, prefixes in config.table_classes.items()}
    kinds = [_table_class(rows, classes, labels) for rows in tables]
    for index in sr_tables:
        kinds[index] = "requirement"
    fields: dict[str, FrdFieldSource] = {}
    confidence: dict[str, float] = {}
    domain_table = next((i for i, kind in enumerate(kinds) if kind == "domain"), None)
    if domain_table is not None:
        header = tables[domain_table][0]
        for col, cell in enumerate(header):
            key = labels.get(normalize_label(cell)) if cell else None
            if key not in ("domain", "sub_domain"):
                continue
            path = f"feeds[0].{key}"
            fields[path] = FrdFieldSource(table=domain_table, row=1, col=col, value_col=col,
                                          label=cell, section=None, feed_index=0)
            confidence[path] = 1.0
    counts = {kind: kinds.count(kind) for kind in dict.fromkeys(kinds)}
    notes = [f"F3 (topic-organized requirements): {len(tables)} table(s) — "
             + ", ".join(f"{n} {kind}" for kind, n in counts.items())
             + (f"; domain table {domain_table}" if domain_table is not None else "")]
    profile = FrdLayoutProfile(fingerprint=digest, family="F3", source="synonyms",
                               fields=fields, confidence=confidence, sections=[], notes=notes)
    return _with_unresolved(profile, [], 1)


def _discover_unrecognized(tables, digest) -> FrdLayoutProfile:
    """M11 item 7: the FRD family NEVER blocks a run. A document matching no
    known family yields a profile that maps no field — one feed, every
    required field unresolved — so ``read_frd`` returns an empty-but-valid
    contract flagged ``frd_family_unrecognized``, the fallback chain (STTM
    bands, meta rows, File Details, VDD FILES, config defaults) fills what it
    can, the layout model may map fields when live (through the validator),
    and whatever is left becomes a question. The note records what WAS
    there: the table count and the first row-0 headings."""
    headings = [" | ".join(c for c in t[0] if c)[:60] for t in tables if t and t[0]][:8]
    profile = FrdLayoutProfile(
        fingerprint=digest, family="unrecognized", source="synonyms", fields={},
        confidence={}, sections=[],
        notes=[f"no metadata section table (F1) and no Solution Requirement table (F2): "
               f"{len(tables)} table(s); first row-0 headings: {headings}"])
    return _with_unresolved(profile, [], 1)


def _sr_title(row: list[str], sr_prefix: str) -> str | None:
    """The row-0 cell that opens a Solution Requirement table, whichever
    column it sits in (the real F2 documents lead with a merged column)."""
    return next((cell for cell in row
                 if cell and normalize_label(cell).startswith(sr_prefix)), None)


def _first_cell(row: list[str]) -> tuple[int, str] | None:
    """(col, text) of a row's first non-empty cell — its LABEL cell, whatever
    column a leading merged column pushes it into."""
    return next(((col, cell) for col, cell in enumerate(row) if cell and cell.strip()), None)


def _section_row(rows: list[list[str]], sections: dict[str, str],
                 configured: int) -> tuple[int, int, str, str] | None:
    """(row, label col, label text, section) — the documented F2 shape: the
    LABEL cell of row ``configured`` (4) names the metadata section. Its
    column follows the table's leading merged column (SHAPES_ROUND2 §1.1).
    A table whose row-4 label names no section is not F2 (the topic-organized
    shape is F3)."""
    if configured >= len(rows):
        return None
    found = _first_cell(rows[configured])
    if found is None:
        return None
    col, text = found
    section = sections.get(normalize_label(text)) or _section_key(text, sections)
    return (configured, col, text, section) if section is not None else None


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


def _row_label(row: list[str], labels: dict[str, str], title: str,
               fixed: dict[str, str]) -> tuple[int, str, str | None] | None:
    """(label col, label text, label key) — the first cell whose text is a
    known label; the section-prefix column (repeating the title) is skipped."""
    for col, cell in enumerate(row):
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
        title = rows[0][0]
        refs.append(FrdSectionRef(table=table_index, section=section, title=title,
                                  feed_index=feed_index))
        for row_index, row in enumerate(rows[1:], start=1):
            found = _row_label(row, labels, title, fixed)
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
    sr_prefix = normalize_label(config.solution_requirement_prefix)
    for table_index in sr_tables:
        rows = tables[table_index]
        title = _sr_title(rows[0], sr_prefix) or rows[0][0]
        placed = _section_row(rows, sections, config.solution_requirement_section_row)
        if placed is None:
            notes.append(f"table {table_index} ({title}): the row-"
                         f"{config.solution_requirement_section_row} label names no metadata "
                         "section; skipped")
            continue
        section_row, section_col, section_label, section = placed
        if section_col:
            notes.append(f"table {table_index} ({title}): a leading merged column — the "
                         f"labels sit in column {section_col}")
        refs.append(FrdSectionRef(table=table_index, section=section, title=section_label,
                                  feed_index=feed_index))
        for row_index, row in enumerate(rows[1:], start=1):
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
        # Label: value pairs inside the section-label row's text, read with
        # the same synonyms. The text is the cell AFTER the label cell.
        text_col = section_col + 1
        text = rows[section_row][text_col] if len(rows[section_row]) > text_col else ""
        for inline_label, _value in _inline_pairs(text, config):
            key = labels.get(normalize_label(inline_label))
            if key is None:
                notes.append(f"table {table_index} row {section_row}: inline label "
                             f"{inline_label!r} maps to no contract field")
                continue
            source = FrdFieldSource(table=table_index, row=section_row, col=section_col,
                                    value_col=text_col, label=section_label, section=section,
                                    inline_label=inline_label, feed_index=feed_index)
            for path in _paths_for(key, feed_index, section, rule_counts):
                fields.setdefault(path, source)
                confidence[path] = 1.0
    profile = FrdLayoutProfile(fingerprint=digest, family="F2", source="synonyms",
                               fields=fields, confidence=confidence, sections=refs, notes=notes)
    return _with_unresolved(profile, [], 1 if refs else 0)


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


def _with_unresolved(profile: FrdLayoutProfile, unresolved: list[FrdUnresolved],
                     feed_count: int) -> FrdLayoutProfile:
    out = list(unresolved)
    for feed_index in range(feed_count):
        for path in _REQUIRED_PATHS:
            key = f"feeds[{feed_index}].{path}"
            if key not in profile.fields and f"{key}#fallback" not in profile.fields:
                out.append(FrdUnresolved(field=key, feed_index=feed_index,
                                         reason="no label in the document maps to this field"))
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


# ------------------------------------------ M10.1: label-prefixed path values

_PATH_LABEL_FIELDS = {"landing_location"}


def strip_value_label(text: str, prefixes: list[str]) -> tuple[str, str | None]:
    """``"/Path : abfss://…"`` -> ``("abfss://…", "Path")``: a path cell that
    starts with a configured label token (a leading slash before it allowed),
    optional spaces and ':' loses the label. (remainder, label) — the label
    is None when nothing was stripped. Case-insensitive; the longest label
    wins ("ADLS Path" before "Path")."""
    if not text or not prefixes:
        return text, None
    for label in sorted(prefixes, key=len, reverse=True):
        match = re.match(r"^\s*/?\s*(" + re.escape(label) + r")\s*:\s*(.*)$", text,
                         flags=re.IGNORECASE | re.S)
        if match and match.group(2).strip():
            return match.group(2).strip(), match.group(1).strip()
    return text, None


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


def _split(text: str, separators: list[str]) -> list[str]:
    if not text:
        return []
    parts = re.split("|".join(re.escape(s) for s in separators), text)
    return [p.strip() for p in parts if p.strip()]


def _parse_target_schema(text: str, config: FrdExtractorConfig) -> tuple[
        tuple[str | None, str | None], tuple[str | None, str | None]]:
    """"STG: a.b; STD: c.d" → ((a, b), (c, d)); "x / y" → stage x, standard y;
    a single value → stage only. Each part splits on its last '.' into
    catalog.schema; a part without '.' is a schema."""
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
        parts = _split(text, config.target_schema_separators)
        stage = parts[0] if parts else None
        standard = parts[1] if len(parts) > 1 else None
    return _part(stage), _part(standard)


def read_frd(content: DocxContent, profile: FrdLayoutProfile, config: Config, *,
             document_name: str, generated_date: str, contract_name: str | None = None
             ) -> FrdContract:
    frd_config = config.extractor.frd
    evidence: dict[str, FieldEvidence] = {}
    ambiguities: list[str] = []
    structured: dict = {}
    labels = _lookup(frd_config.labels)

    def get(path: str) -> str:
        source = profile.fields.get(path)
        if source is None:
            return ""
        value = _value(content, source, frd_config)
        clean = path.split("#", 1)[0]
        field = clean.split(".", 1)[1] if "." in clean else clean
        stripped_label = None
        value_kind = None
        if field in _PATH_LABEL_FIELDS:
            value, stripped_label = strip_value_label(value, frd_config.value_label_prefixes)
            from codegen.gate.derivations import location_scheme

            value_kind = "location_uri" if location_scheme(value) else None
        evidence[path] = FieldEvidence(
            table=source.table, row=source.row, col=source.col, label=source.label,
            section=source.section, inline_label=source.inline_label, source=profile.source,
            stripped_label=stripped_label, value_kind=value_kind)
        own = {k for k, v in {**_SCALAR_FIELDS, **_FALLBACK_FIELDS}.items() if v == field}
        if field == "domain":
            own |= {"domain_subdomain", "domain"}
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

    flags: list[str] = []
    feeds: list[FrdFeed] = []
    for feed_index in range(max(profile.feed_count, 1)):
        prefix = f"feeds[{feed_index}]"
        feed_name = get_with_fallback(f"{prefix}.feed_name")
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
        rules = []
        n = 0
        while f"{prefix}.validation_rules[{n}]" in profile.fields:
            source = profile.fields[f"{prefix}.validation_rules[{n}]"]
            value = get(f"{prefix}.validation_rules[{n}]")
            if value:
                rules.append(f"{source.label}: {value}" if source.labelled_rule else value)
            n += 1
        stage_strategy = _strategy(get(f"{prefix}.stage_target.load_strategy"),
                                   f"{prefix}.stage_target.load_strategy", ambiguities)
        std_strategy = _strategy(get(f"{prefix}.standard_target.load_strategy"),
                                 f"{prefix}.standard_target.load_strategy", ambiguities)
        feeds.append(FrdFeed(
            feed_name=feed_name or unnamed_feed_name(document_name, feed_index),
            source_system=source_system or "unstated",
            file_name_patterns=file_name_patterns,
            file_format=get(f"{prefix}.file_format") or None,
            delimiter=None,
            record_segments=[],
            frequency=get(f"{prefix}.frequency") or None,
            load_windows_sla=[],
            lobs=_split(get(f"{prefix}.lobs"), frd_config.list_separators),
            domain=domain_parts[0] if domain_parts else None,
            # A sub-domain stated in a cell of its own (the F3 Domain / SubDomain
            # table, M11 item 9) wins over the split of a combined domain cell.
            sub_domain=(get(f"{prefix}.sub_domain") if _own_cell(profile, prefix, "sub_domain")
                        else None) or (domain_parts[1] if len(domain_parts) > 1 else None),
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
            sttm_reference=get(f"{prefix}.sttm_reference") or None,
            requirement_ids=_split(get(f"{prefix}.requirement_ids"), frd_config.list_separators),
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
    if profile.family == "F3":
        flags.append(f"frd_family_f3: {profile.notes[0] if profile.notes else ''} — "
                     "recognized and classified only; the fields come from the fallback chain "
                     "(STTM, VDD, config), the layout model when live, or a layout question")
    if profile.family == "unrecognized":
        # Structure, never content: the count and the headings are row-0
        # labels, the same material the fingerprint reads.
        flags.append(f"frd_family_unrecognized: {profile.notes[0] if profile.notes else ''} "
                     "— the document matched neither the F1 nor the F2 family; every field "
                     "comes from the fallback chain (STTM, VDD, config) or a layout question")

    project_name = next((text for index, text in content.paragraphs if index == 0),
                        Path(document_name).stem)
    acd = _acd_items(content, frd_config)
    status = "PASS_WITH_FLAGS" if ambiguities else "PASS"
    sourced = len([k for k in evidence if "#" not in k])
    return FrdContract(
        contract_name=contract_name or f"FRD feed contract extracted from {document_name}",
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
        structured=structured,
        extraction_flags=flags,
    )


def _own_cell(profile: FrdLayoutProfile, prefix: str, field: str) -> bool:
    """True when ``field`` is read from a cell OTHER than the domain's — a
    combined "Domain and Subdomain" cell maps both paths to one cell, and is
    split instead (M11 item 9)."""
    mine = profile.fields.get(f"{prefix}.{field}")
    domain = profile.fields.get(f"{prefix}.domain")
    if mine is None:
        return False
    if domain is None:
        return True
    return (mine.table, mine.row, mine.col, mine.inline_label) != (
        domain.table, domain.row, domain.col, domain.inline_label)


_UNNAMED_SUFFIX = "(unnamed)"


def unnamed_feed_name(document_name: str, feed_index: int) -> str:
    return f"{document_name} feed {feed_index + 1} {_UNNAMED_SUFFIX}"


def is_unnamed_feed(feed_name: str) -> bool:
    """True for the placeholder ``read_frd`` gives a feed no cell names."""
    return feed_name.endswith(_UNNAMED_SUFFIX)


def _strategy(value: str, path: str, ambiguities: list[str]):
    if not value:
        return None
    for literal in _LOAD_STRATEGIES:
        if normalize_label(value) == normalize_label(literal):
            return literal
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
    content = read_docx(path)
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
