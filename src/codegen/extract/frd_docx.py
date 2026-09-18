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
    for child in body:
        if child.tag == f"{_W}tbl":
            rows = []
            for tr in child.findall(f"{_W}tr"):
                rows.append([_cell_text(tc) for tc in tr.findall(f"{_W}tc")])
            tables.append(rows)
        elif child.tag == f"{_W}p":
            text = "".join(t.text or "" for t in child.iter(f"{_W}t")).strip()
            if text:
                paragraphs.append((len(tables), text))
    if not tables:
        raise FrdDocxError(f"{path.name}: document carries no tables")
    return DocxContent(tables=tables, paragraphs=paragraphs)


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
    f1_tables = [(i, sections[normalize_label(t[0][0])]) for i, t in enumerate(tables)
                 if t and t[0] and normalize_label(t[0][0]) in sections]
    sr_tables = [i for i, t in enumerate(tables)
                 if t and t[0] and normalize_label(t[0][0]).startswith(sr_prefix)]
    if f1_tables:
        return _discover_f1(tables, f1_tables, labels, digest, config)
    if sr_tables:
        return _discover_f2(tables, sr_tables, sections, labels, digest, config)
    raise FrdDocxError(
        "no metadata section table (F1) and no Solution Requirement table (F2) found; "
        f"table titles seen: {[t[0][0][:40] for t in tables if t and t[0]][:12]}"
    )


def _row_label(row: list[str], labels: dict[str, str], title: str,
               fixed: dict[str, str]) -> tuple[int, str, str | None] | None:
    """(label col, label text, label key) — the first cell whose text is a
    known label; the section-prefix column (repeating the title) is skipped."""
    for col, cell in enumerate(row):
        if col == 0 and normalize_label(cell) == normalize_label(title) and len(row) > 1:
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
        title = rows[0][0]
        section_row = config.solution_requirement_section_row
        if section_row >= len(rows) or not rows[section_row]:
            notes.append(f"table {table_index} ({title}): no row {section_row}; skipped")
            continue
        section_label = rows[section_row][0]
        section = sections.get(normalize_label(section_label))
        if section is None:
            notes.append(f"table {table_index} ({title}): row-{section_row} label "
                         f"{section_label!r} names no metadata section; skipped")
            continue
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
        # Label: value pairs inside the row-4 text, read with the same synonyms.
        text = rows[section_row][1] if len(rows[section_row]) > 1 else ""
        for inline_label, _value in _inline_pairs(text, config):
            key = labels.get(normalize_label(inline_label))
            if key is None:
                notes.append(f"table {table_index} row {section_row}: inline label "
                             f"{inline_label!r} maps to no contract field")
                continue
            source = FrdFieldSource(table=table_index, row=section_row, col=0, value_col=1,
                                    label=section_label, section=section,
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

    def get(path: str) -> str:
        source = profile.fields.get(path)
        if source is None:
            return ""
        value = _value(content, source, frd_config)
        evidence[path] = FieldEvidence(
            table=source.table, row=source.row, col=source.col, label=source.label,
            section=source.section, inline_label=source.inline_label, source=profile.source)
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
        if confirming:
            evidence[path] = evidence.pop(confirming_key)
        return confirming

    def get_with_fallback(path: str) -> str:
        value = get(path)
        if not value and f"{path}#fallback" in profile.fields:
            value = get(f"{path}#fallback")
            if value:
                evidence[path] = evidence.pop(f"{path}#fallback")
        return value

    feeds: list[FrdFeed] = []
    for feed_index in range(max(profile.feed_count, 1)):
        prefix = f"feeds[{feed_index}]"
        feed_name = get_with_fallback(f"{prefix}.feed_name")
        source_system = get_with_fallback(f"{prefix}.source_system")
        domain_text = get(f"{prefix}.domain")
        domain_parts = _split(domain_text, frd_config.domain_separators)
        (stage_catalog, stage_schema), (std_catalog, std_schema) = _parse_target_schema(
            get(f"{prefix}.stage_target.schema"), frd_config)
        tables = _split(get(f"{prefix}.stage_target.tables"), frd_config.list_separators)
        get(f"{prefix}.standard_target.tables")   # same cell; records its evidence
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
            feed_name=feed_name or f"{document_name} feed {feed_index + 1} (unnamed)",
            source_system=source_system or "unstated",
            file_name_patterns=[],
            file_format=get(f"{prefix}.file_format") or None,
            delimiter=None,
            record_segments=[],
            frequency=get(f"{prefix}.frequency") or None,
            load_windows_sla=[],
            lobs=_split(get(f"{prefix}.lobs"), frd_config.list_separators),
            domain=domain_parts[0] if domain_parts else None,
            sub_domain=domain_parts[1] if len(domain_parts) > 1 else None,
            landing_location=_landing(prefix) or None,
            stage_target=TargetSpec(catalog=stage_catalog, schema=stage_schema, tables=tables,
                                    load_strategy=stage_strategy),
            standard_target=TargetSpec(catalog=std_catalog, schema=std_schema,
                                       tables=list(tables) if std_schema or std_catalog else [],
                                       load_strategy=std_strategy),
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
    )


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
    "contract_to_json",
    "discover_frd",
    "extract_frd_contract",
    "normalize_label",
    "read_docx",
    "read_frd",
]
