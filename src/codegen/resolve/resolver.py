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
from pathlib import Path

from codegen.config import Config
from codegen.contracts.frd import FrdContract, FrdFeed
from codegen.contracts.resolved import (
    ResolvedFeedSpec,
    ResolvedRecycle,
    ResolvedTable,
    SegmentSpec,
)
from codegen.contracts.sttm import SttmContract, SttmFeed

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


class ContractMismatchError(ValueError):
    """The FRD and STTM contracts disagree; generation must not proceed."""

    def __init__(self, feed: str, errors: list[str]) -> None:
        self.feed = feed
        self.errors = errors
        bullet_list = "\n  - ".join(errors)
        super().__init__(f"contract mismatch for feed '{feed}':\n  - {bullet_list}")


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


def _is_fixed_width(file_format: str | None, config: Config) -> bool:
    fmt = (file_format or "").lower()
    return any(token.lower() in fmt for token in config.extractor.vdd.fixed_width_tokens)


def _resolve_delimiter(frd_feed: FrdFeed, sttm_feed: SttmFeed, errors: list[str],
                       config: Config | None = None) -> str:
    explicit = [d for d in (sttm_feed.source_file.delimiter, frd_feed.delimiter) if d]
    if not explicit and config is not None and _is_fixed_width(frd_feed.file_format, config):
        # M3: a fixed-width file has no delimiter by definition (positions
        # come from the VDD / STTM); an empty delimiter is the honest value.
        return ""
    if explicit:
        if len(set(explicit)) > 1:
            errors.append(
                f"delimiter disagrees: STTM says {sttm_feed.source_file.delimiter!r}, "
                f"FRD says {frd_feed.delimiter!r}"
            )
        return explicit[0]
    implied = _FORMAT_DELIMITERS.get((frd_feed.file_format or "").lower())
    if implied is None:
        errors.append(
            f"format '{frd_feed.file_format}' has no implied delimiter and neither "
            "contract states one"
        )
        return ""
    return implied


def _parse_reference(validation_text: str, feed: str) -> tuple[str, str, str | None]:
    match = _REFERENCE_RE.search(validation_text) or _CLIENT_REFERENCE_RE.search(validation_text)
    if match is None:
        raise ContractMismatchError(
            feed,
            [
                "recycle validation text is not parseable as "
                "'against <id_column> in <table> [where <filter>]' or "
                "'Check with <id_column> from ... <table> [FOR <filter>]': "
                f"{validation_text!r}"
            ],
        )
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


def _fill_frd_gaps(frd_feed: FrdFeed, sttm_feed: SttmFeed, config: Config, vdd
                   ) -> tuple[FrdFeed, list[str], list[str]]:
    """The contract-level gap chain. Returns (patched feed, flags, errors)."""
    from codegen.faq import load_faq
    from codegen.resolve.gapfill import (
        Statement,
        distinct,
        fill_flag,
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
        return distinct(out)

    if feed.file_format is None:
        others = others_for("file_format", "format")
        if len(others) == 1:
            feed = feed.model_copy(update={"file_format": others[0].value})
            flags.append(fill_flag("file_format", others[0]))
        elif len(others) > 1:
            errors.append("the FRD states no file format and the other documents disagree: "
                          + "; ".join(f"{s.source} {s.cell} says {s.value!r}" for s in others)
                          + " — choose one in the layout dialog")
    if feed.delimiter is None:
        others = others_for("delimiter", "delimiter")
        if len(others) == 1:
            feed = feed.model_copy(update={"delimiter": others[0].value})
            flags.append(fill_flag("delimiter", others[0]))
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
            errors.append(f"the STTM states one load strategy ({parsed['any']!r}, {cell}) "
                          "without a layer — say which layer it applies to in the layout "
                          "dialog, or answer the FAQ load_mode")
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
) -> list[SegmentSpec]:
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
        errors.append(f"stage schema disagrees: STTM '{stage_schema}', FRD '{frd_schema}'")

    if not frd_feed.is_segmented and not (sttm_feed.is_segmented and segment_names):
        if sttm_feed.is_segmented:
            errors.append("STTM fields carry record_segment but the FRD declares no segments")
        if sttm_feed.stage.table not in frd_feed.stage_target.tables:
            errors.append(
                f"STTM stage table '{sttm_feed.stage.table}' is not among FRD stage "
                f"tables {frd_feed.stage_target.tables}"
            )
        table = ResolvedTable(
            catalog=catalog, schema_name=stage_schema, table=sttm_feed.stage.table, role="stage"
        )
        return [SegmentSpec(segment="Detail", stage_table=table, fields=sttm_feed.fields)]

    if not sttm_feed.is_segmented:
        errors.append(
            f"FRD declares segments {frd_feed.record_segments} but no STTM field "
            "carries record_segment/stage_table"
        )
        return []

    segments: list[SegmentSpec] = []
    seen_segments: list[str] = []
    for segment_name in segment_names:
        seg_fields = [f for f in sttm_feed.fields if f.record_segment == segment_name]
        if not seg_fields:
            errors.append(f"FRD segment '{segment_name}' has no fields in the STTM contract")
            continue
        seg_tables = {f.stage_table for f in seg_fields}
        if len(seg_tables) > 1:
            errors.append(
                f"segment '{segment_name}' maps to multiple stage tables: {sorted(seg_tables)}"
            )
        seg_table = seg_fields[0].stage_table
        assert seg_table is not None  # guaranteed by SttmFeed validation
        if seg_table not in frd_feed.stage_target.tables:
            errors.append(
                f"segment '{segment_name}' stage table '{seg_table}' is not among FRD "
                f"stage tables {frd_feed.stage_target.tables}"
            )
        # Per-segment STANDARD table (segmented dialect: H/D/T map to their
        # own tables in BOTH layers). Catalog/schema come from the STTM's
        # standard target group when the FRD's Target Schema block names
        # stage targets only.
        standard_table = None
        seg_standard_tables = {f.standard_table for f in seg_fields} - {None}
        if len(seg_standard_tables) > 1:
            errors.append(
                f"segment '{segment_name}' maps to multiple standard tables: "
                f"{sorted(t for t in seg_standard_tables if t)}"
            )
        elif seg_standard_tables and sttm_feed.standard is not None:
            standard_table = ResolvedTable(
                catalog=(sttm_feed.standard.catalog
                         or frd_feed.standard_target.catalog),
                schema_name=sttm_feed.standard.schema_name,
                table=next(iter(seg_standard_tables)),
                role="standard",
            )
        segment_audit = (
            sttm_feed.segmented.segment_audit.get(segment_name)
            if sttm_feed.segmented is not None else None
        )
        segments.append(
            SegmentSpec(
                segment=segment_name,
                stage_table=ResolvedTable(
                    catalog=catalog, schema_name=stage_schema, table=seg_table, role="stage"
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
        errors.append(f"STTM fields name segments the FRD does not declare: {sorted(extra)}")

    if segments and not any(s.segment == "Detail" for s in segments):
        errors.append("no Detail segment resolved; the data-carrying segment is required")
    if segments:
        detail = next((s for s in segments if s.segment == "Detail"), None)
        if detail is not None and sttm_feed.stage.table != detail.stage_table.table:
            errors.append(
                f"STTM stage.table '{sttm_feed.stage.table}' should be the Detail segment "
                f"table '{detail.stage_table.table}'"
            )
    return segments


def _stage_columns(sttm_feed: SttmFeed, source_columns: list[str], feed: str) -> list[str]:
    by_source = {f.source_column: f.stage_column for f in sttm_feed.fields}
    missing = [c for c in source_columns if c not in by_source]
    if missing:
        raise ContractMismatchError(feed, [f"columns not present in STTM fields: {missing}"])
    return [by_source[c] for c in source_columns]


def resolve_feeds(
    frd: FrdContract,
    sttm: SttmContract,
    config: Config,
    *,
    frd_sha256: str,
    sttm_sha256: str,
    vdd=None,
) -> list[ResolvedFeedSpec]:
    """Join every FRD feed to its STTM feed. Unmatched feeds on either side fail."""
    sttm_by_id = {f.feed_id: f for f in sttm.feeds}
    matched_sttm_ids: set[str] = set()
    specs: list[ResolvedFeedSpec] = []
    unmatched_frd: list[str] = []

    for frd_feed in frd.feeds:
        feed_id = config.feed_aliases.get(frd_feed.feed_name) or normalize_feed_name(
            frd_feed.feed_name
        )
        sttm_feed = sttm_by_id.get(feed_id)
        if sttm_feed is None:
            unmatched_frd.append(f"{frd_feed.feed_name!r} (looked for STTM feed_id '{feed_id}')")
            continue
        matched_sttm_ids.add(feed_id)
        specs.append(_resolve_one(frd, frd_feed, sttm, sttm_feed, config, frd_sha256, sttm_sha256,
                                  vdd=vdd))

    errors = [f"FRD feed has no STTM mapping: {name}" for name in unmatched_frd]
    errors += [
        f"STTM feed '{feed_id}' has no FRD feed"
        for feed_id in sorted(set(sttm_by_id) - matched_sttm_ids)
    ]
    if errors:
        raise ContractMismatchError(frd.contract_name, errors)
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
) -> ResolvedFeedSpec:
    errors: list[str] = []
    feed_id = sttm_feed.feed_id
    catalog = frd_feed.stage_target.catalog

    # FRD gap chain (resolve/gapfill.py): a docx-extracted FRD that states no
    # file format / load strategy takes them from the STTM meta rows, the VDD
    # FILES sheet or the FAQ — each fill a provenance flag. The layout stage
    # applies the same chain earlier (with the dialog for disagreements);
    # here it covers the CLI path and anything the dialog left blank.
    frd_feed, gap_flags, gap_errors = _fill_frd_gaps(frd_feed, sttm_feed, config, vdd)
    errors.extend(gap_errors)

    delimiter = _resolve_delimiter(frd_feed, sttm_feed, errors, config)
    provenance_flags: list[str] = []
    segment_names: list[str] | None = None
    if not frd_feed.is_segmented and sttm_feed.is_segmented:
        segment_names = _sttm_segment_names(sttm_feed)
        provenance_flags.append(
            f"segments_from_sttm: the FRD names no record segments; the STTM's Segment "
            f"column declares {segment_names} (sheet {sttm_feed.mapping_sheet!r})")
    segments = _resolve_segments(frd_feed, sttm_feed, catalog, errors, segment_names)
    # docx-extracted FRD contracts (M2) leave unsourced values null; each
    # is a loud stop here, never a default — except the file pattern, which
    # the STTM's meta rows / FILE_DETAILS supply when the FRD names none
    # (M4), flagged as such.
    file_name_patterns = list(frd_feed.file_name_patterns)
    if not file_name_patterns:
        sttm_patterns = [p.strip() for p in re.split(r"[;\n,]+", sttm_feed.source_file.name_pattern)
                         if p.strip()]
        meta_names = sttm_feed.meta_rows.get("file_names")
        if meta_names:
            sttm_patterns = [p.strip() for p in re.split(r"[;\n,]+", meta_names) if p.strip()]
        if sttm_patterns:
            file_name_patterns = sttm_patterns
            provenance_flags.append(
                f"file_pattern_from_sttm: the FRD names no file pattern; the STTM states "
                f"{sttm_patterns} (meta row 'File Names' / FILE_DETAILS)")
        else:
            errors.append("FRD names no file pattern (docx-extracted contract with no file "
                          "pattern label) and the STTM states none either")
    # Hard stops that remain: fields every source is silent on and the
    # generator cannot proceed without (a reader needs the format; a writer
    # needs the stage strategy). Domain / standard strategy are blank-and-flag.
    if frd_feed.file_format is None:
        errors.append("no source states the file format: FRD 'Object/data Format', the STTM "
                      "'File Format' meta row and the VDD FILES sheet are all blank")
    if frd_feed.stage_target.load_strategy is None:
        errors.append("no source states the stage load strategy: FRD 'Load Strategy STG' blank, "
                      "the STTM 'Load Strategy' meta row states none per layer, and the FAQ "
                      "load_mode is unanswered — answer it in the layout dialog or the FAQ")

    if not frd_feed.lobs:
        errors.append("FRD feed declares no LOBs; the LOB audit column needs at least one")

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
            errors.append(
                f"recycle window disagrees: FRD text says {frd_days} days, "
                f"STTM spec says {recycle_spec.recycle_window_days} days"
            )
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
    unaccounted = [t for t in frd_feed.stage_target.tables if t not in accounted]
    if unaccounted:
        errors.append(
            f"FRD stage tables not mapped by any STTM field or recycle rule: {unaccounted}"
        )

    # --- standard target ---------------------------------------------------
    standard_table: ResolvedTable | None = None
    standard_strategy = None
    if sttm_feed.standard is not None:
        if not frd_feed.standard_target.tables:
            if sttm_feed.segmented is None:
                errors.append(
                    f"STTM names standard table '{sttm_feed.standard.table}' but the FRD "
                    "standard target is empty"
                )
            # Segmented extraction: the standard layer is scoped by the FRD's
            # Load Strategy STD; its catalog/schema/tables come from the
            # STTM's standard target group (the FRD's Target Schema block
            # names stage targets only) — recorded as a cited provenance note
            # on the extraction, never inferred silently.
        elif sttm_feed.standard.table not in frd_feed.standard_target.tables:
            errors.append(
                f"STTM standard table '{sttm_feed.standard.table}' is not among FRD "
                f"standard tables {frd_feed.standard_target.tables}"
            )
        standard_table = ResolvedTable(
            catalog=(frd_feed.standard_target.catalog
                     or sttm_feed.standard.catalog),
            schema_name=sttm_feed.standard.schema_name,
            table=sttm_feed.standard.table,
            role="standard",
        )
        standard_strategy = frd_feed.standard_target.load_strategy
    elif frd_feed.standard_target.tables:
        errors.append(
            f"FRD names standard tables {frd_feed.standard_target.tables} but the STTM "
            "has no standard mapping"
        )

    if errors:
        raise ContractMismatchError(feed_id, errors)

    natural_key = _stage_columns(sttm_feed, sttm_feed.load_rules.not_null_columns, feed_id)
    not_null = natural_key
    phi = _stage_columns(sttm_feed, sttm_feed.load_rules.phi_columns, feed_id)

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
        provenance_flags=[*gap_flags, *provenance_flags],
    )


def resolve_pair(frd_path: Path, sttm_path: Path, config: Config,
                 vdd_path: Path | None = None) -> list[ResolvedFeedSpec]:
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
    )
    if vdd is not None:
        specs = [spec.model_copy(update={"vdd": vdd}) for spec in specs]
    return specs
