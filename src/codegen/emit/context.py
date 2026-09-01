"""Build the fully-materialized render context for one feed.

Templates never compute anything: every list, name, and literal they emit is
precomputed here from the ResolvedFeedSpec + config, in deterministic order,
so rendering is byte-stable given identical inputs. A spec feature no
template covers raises :class:`TemplateGapError` (a gate FAIL), never a
silent skip.
"""

from __future__ import annotations

import re
from typing import Any

from codegen.config import Config, EngineeringStandardsConfig
from codegen.contracts.resolved import ResolvedFeedSpec, SegmentSpec
from codegen.faq import WRITER_BEHAVIOR, LoadPatternFaq, summarize

# Contract file-name patterns use date placeholders; longest tokens first so
# CCYYMMDD is consumed before CCYY / MM. "*" is a free wildcard.
_PLACEHOLDER_MAP = {
    # Combined date-time stamps first: tokens only substitute when bounded by
    # non-alphanumerics, so SFMC-style contiguous "YYYYMMDDHHMMSS" must be a
    # token of its own or it would be treated as a literal (found 2026-08-26
    # against the SFMC Email Campaign FRD's file-name pattern).
    "CCYYMMDDHHMMSS": r"\d{14}",
    "YYYYMMDDHHMMSS": r"\d{14}",
    "CCYYMMDD": r"\d{8}",
    "YYYYMMDD": r"\d{8}",
    "HHMMSS": r"\d{6}",
    "CCYY": r"\d{4}",
    "YYYY": r"\d{4}",
    "HHMM": r"\d{4}",
    "MM": r"\d{2}",
    "DD": r"\d{2}",
    "HH": r"\d{2}",
    "SS": r"\d{2}",
}
_TOKENS_LONGEST_FIRST = sorted(_PLACEHOLDER_MAP, key=len, reverse=True)

# Contract datatype -> Delta SQL type for the standard (typed) layer.
_SQL_TYPES = {
    "string": "STRING",
    "int": "INT",
    "integer": "INT",
    "bigint": "BIGINT",
    "timestamp": "TIMESTAMP",
    "date": "DATE",
    "double": "DOUBLE",
    "float": "FLOAT",
    "boolean": "BOOLEAN",
}
_DECIMAL_RE = re.compile(r"^decimal\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)$", re.IGNORECASE)

# Quartz cron for "Weekly <Day> <H> <AM|PM>" SLA phrases; anything else ships
# unscheduled with the SLA text carried in the job JSON for a human to set.
# Simple equality filter (e.g. "GRGR_CK = 31") — enough for the fixture
# contracts; anything richer is a template gap until a template covers it.
_EQUALITY_FILTER_RE = re.compile(r"^\s*(?P<column>\w+)\s*=\s*(?P<value>'[^']*'|\S+)\s*$")

_WEEKLY_RE = re.compile(
    r"^Weekly\s+(?P<day>Mon|Tues|Wednes|Thurs|Fri|Satur|Sun)day\s+(?P<hour>\d{1,2})\s*(?P<ampm>AM|PM)$",
    re.IGNORECASE,
)
_QUARTZ_DAYS = {
    "mon": "MON",
    "tues": "TUE",
    "wednes": "WED",
    "thurs": "THU",
    "fri": "FRI",
    "satur": "SAT",
    "sun": "SUN",
}
_HOURS_PER_HALF_DAY = 12
_SECONDS_PER_HOUR = 3600


class TemplateGapError(ValueError):
    """The spec asks for something no template covers; generation must FAIL."""


def pattern_to_regex(name_pattern: str) -> str:
    """Contract file-name pattern -> anchored regex string.

    Date tokens substitute only when bounded by non-alphanumerics or string
    edges (so a literal word containing "MM" is untouched); "*" becomes a
    wildcard; everything else is escaped.
    """
    out = ["^"]
    i, n = 0, len(name_pattern)
    while i < n:
        token = None
        for tok in _TOKENS_LONGEST_FIRST:
            end = i + len(tok)
            if name_pattern.startswith(tok, i):
                before_ok = i == 0 or not name_pattern[i - 1].isalnum()
                after_ok = end == n or not name_pattern[end].isalnum()
                if before_ok and after_ok:
                    token = tok
                    break
        if token is not None:
            out.append(_PLACEHOLDER_MAP[token])
            i += len(token)
        elif name_pattern[i] == "*":
            out.append(".*")
            i += 1
        else:
            out.append(re.escape(name_pattern[i]))
            i += 1
    out.append("$")
    return "".join(out)


_EXAMPLE_SUBSTITUTIONS = {
    "CCYYMMDDHHMMSS": "20260115090000",
    "YYYYMMDDHHMMSS": "20260115090000",
    "CCYYMMDD": "20260115",
    "YYYYMMDD": "20260115",
    "HHMMSS": "090000",
    "CCYY": "2026",
    "YYYY": "2026",
    "HHMM": "0900",
    "MM": "01",
    "DD": "15",
    "HH": "09",
    "SS": "00",
}


def example_file_name(name_pattern: str, variant: int = 0) -> str:
    """A concrete file name matching the pattern, for tests and docs.

    ``variant`` shifts the day-of-month so callers can mint distinct valid
    names from one pattern (each end-to-end test ingests its own file).
    """
    day = 15 + variant
    substitutions = {
        **_EXAMPLE_SUBSTITUTIONS,
        "CCYYMMDDHHMMSS": f"202601{day:02d}090000",
        "YYYYMMDDHHMMSS": f"202601{day:02d}090000",
        "CCYYMMDD": f"202601{day:02d}",
        "YYYYMMDD": f"202601{day:02d}",
        "DD": f"{day:02d}",
        "MM": f"{1 + variant:02d}",
    }
    out = []
    i, n = 0, len(name_pattern)
    while i < n:
        token = None
        for tok in _TOKENS_LONGEST_FIRST:
            end = i + len(tok)
            if name_pattern.startswith(tok, i):
                before_ok = i == 0 or not name_pattern[i - 1].isalnum()
                after_ok = end == n or not name_pattern[end].isalnum()
                if before_ok and after_ok:
                    token = tok
                    break
        if token is not None:
            out.append(substitutions[token])
            i += len(token)
        elif name_pattern[i] == "*":
            out.append("X")
            i += 1
        else:
            out.append(name_pattern[i])
            i += 1
    return "".join(out)


def sql_type(contract_datatype: str) -> str:
    """Contract datatype string -> Delta SQL type, loud on unknowns."""
    normalized = contract_datatype.strip()
    decimal = _DECIMAL_RE.match(normalized)
    if decimal:
        return f"DECIMAL({decimal.group(1)},{decimal.group(2)})"
    mapped = _SQL_TYPES.get(normalized.lower())
    if mapped is None:
        raise TemplateGapError(f"no SQL type mapping for contract datatype {contract_datatype!r}")
    return mapped


def schedule_from_sla(frequency: str | None) -> dict[str, str] | None:
    """Compile an unambiguous frequency phrase to Quartz cron, else None."""
    if frequency is None:
        return None
    match = _WEEKLY_RE.match(frequency.strip())
    if match is None:
        return None
    hour = int(match.group("hour")) % _HOURS_PER_HALF_DAY
    if match.group("ampm").upper() == "PM":
        hour += _HOURS_PER_HALF_DAY
    day = _QUARTZ_DAYS[match.group("day").lower()]
    return {"quartz_cron_expression": f"0 0 {hour} ? * {day}", "timezone_id": "America/New_York"}


def _sanitize_name_part(value: str | None) -> str:
    """EDO name component: uppercase, runs of non-alphanumerics → ``_``."""
    if value is None:
        return ""
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()


def _abbreviate(value: str | None, abbreviations: dict[str, str]) -> str:
    """EDO abbreviation-table lookup (case-insensitive on the sanitized key);
    an unmapped value falls back to its sanitized uppercase form."""
    if value is None:
        return ""
    normalized = _sanitize_name_part(value)
    by_normalized = {_sanitize_name_part(k): v for k, v in abbreviations.items()}
    return by_normalized.get(normalized, normalized)


def _name_components(
    standards: EngineeringStandardsConfig,
    faq: LoadPatternFaq,
    slug: str,
    *,
    source: str | None,
    domain: str | None,
    sub_domain: str | None,
    lobs: tuple[str, ...] | list[str],
) -> dict[str, str]:
    """Every placeholder either naming pattern may interpolate."""
    if len(lobs) == 1:
        lob = _abbreviate(lobs[0], standards.lob_abbreviations)
    else:
        lob = standards.multi_lob_abbreviation if lobs else ""
    frequency = standards.frequency_abbreviations.get(
        faq.load_frequency.value, standards.unknown_frequency_abbreviation
    )
    return {
        "prefix": standards.job_prefix_by_frequency.get(faq.load_frequency.value, ""),
        "slug": slug,
        "feed": _sanitize_name_part(slug),
        "product": _sanitize_name_part(standards.product_code),
        "subproduct": _sanitize_name_part(standards.sub_product_code),
        "source": _abbreviate(source, standards.source_abbreviations),
        "domain": _abbreviate(domain, standards.domain_abbreviations),
        "subdomain": _abbreviate(sub_domain, standards.domain_abbreviations),
        "lob": lob,
        "frequency": frequency,
    }


def _collapse_name(name: str) -> str:
    """Empty components leave doubled separators behind; collapse them."""
    return re.sub(r"__+", "_", name).strip("_")


def resolve_job_name(
    standards: EngineeringStandardsConfig,
    faq: LoadPatternFaq,
    slug: str,
    *,
    source: str | None = None,
    domain: str | None = None,
    sub_domain: str | None = None,
    lobs: tuple[str, ...] | list[str] = (),
) -> str:
    """Job/workflow name from the standards pattern (EDO naming standard:
    ``WF_<product>_<subproduct>_<sources>_<domain>_<subdomain>_<lob>_<freq>``).
    With the stub default pattern and an unknown frequency this degrades to
    the legacy ``ingest_<slug>``."""
    components = _name_components(
        standards, faq, slug, source=source, domain=domain, sub_domain=sub_domain, lobs=lobs
    )
    return _collapse_name(standards.job_name_pattern.format(**components))


def resolve_notebook_name(
    standards: EngineeringStandardsConfig,
    faq: LoadPatternFaq,
    slug: str,
    *,
    source: str | None = None,
    domain: str | None = None,
    sub_domain: str | None = None,
    lobs: tuple[str, ...] | list[str] = (),
) -> str | None:
    """EDO workspace notebook name (``NB_...``); None when unconfigured."""
    if not standards.notebook_name_pattern:
        return None
    components = _name_components(
        standards, faq, slug, source=source, domain=domain, sub_domain=sub_domain, lobs=lobs
    )
    return _collapse_name(standards.notebook_name_pattern.format(**components))


def _segment_context(
    segment: SegmentSpec, spec: ResolvedFeedSpec, config: Config
) -> dict[str, Any]:
    record_type_value = None
    if spec.is_segmented and spec.segmented_extraction is None:
        # Legacy segmented contracts: split by configured record-type values.
        # Segmented-extraction feeds derive identification from the STTM and
        # need no configured discriminators.
        record_type_value = config.segments.record_type_values.get(segment.segment)
        if record_type_value is None:
            raise TemplateGapError(
                f"no record_type value configured for segment '{segment.segment}'"
            )
    not_null_stage = [
        f.stage_column for f in segment.fields if f.stage_column in set(spec.not_null_columns)
    ]
    return {
        "name": segment.segment,
        "is_detail": segment.segment == "Detail",
        "stage_table": segment.stage_table.table,
        "record_type_value": record_type_value,
        # Per-segment audit columns exactly as the STTM lists them; None ->
        # the feed-wide set (flat feeds render byte-identically).
        "audit_columns": (
            [(a.column, sql_type(a.datatype)) for a in segment.audit_columns]
            if segment.audit_columns is not None
            else [(a.column, sql_type(a.datatype)) for a in spec.audit_columns]
        ),
        "source_columns": [f.source_column for f in segment.fields],
        "stage_columns": [f.stage_column for f in segment.fields],
        "not_null_stage_columns": not_null_stage,
        "column_samples": _column_samples(segment, spec),
    }


def _column_samples(segment: SegmentSpec,
                    spec: ResolvedFeedSpec) -> list[tuple[str, str]]:
    samples = [
        (f.source_column, f.sample_value if f.sample_value is not None else "x")
        for f in segment.fields
    ]
    # Derived record identification: the trailer's first field carries the
    # STTM-stated static marker, so generated test fixtures classify the way
    # real files do. Other samples are untouched (flat feeds unaffected).
    if (spec.segmented_extraction is not None
            and segment.segment == "Trailer" and samples):
        column, _ = samples[0]
        samples[0] = (column,
                      spec.segmented_extraction.identification.trailer_marker)
    return samples


def build_context(
    spec: ResolvedFeedSpec,
    config: Config,
    *,
    allow_duplicate_file_name: bool,
    duplicate_rule_text: str | None,
    notification_rule_texts: list[str],
    faq: LoadPatternFaq | None = None,
) -> dict[str, Any]:
    """Everything the templates interpolate, and nothing they compute."""
    # No file read here — callers load the FAQ (codegen.faq.faq_for_spec) so
    # rendering stays a pure function of its arguments. None → all defaults.
    faq = faq if faq is not None else LoadPatternFaq()
    segments = [_segment_context(s, spec, config) for s in spec.segments]
    detail = next(s for s in segments if s["is_detail"])

    trailer_count_stage_column = None
    trailer_count_source_column = None
    if spec.is_segmented:
        trailer = next((s for s in spec.segments if s.segment == "Trailer"), None)
        if trailer is not None:
            source_names = {f.source_column: f.stage_column for f in trailer.fields}
            trailer_count_stage_column = source_names.get(config.segments.trailer_count_column)
            if trailer_count_stage_column is not None:
                trailer_count_source_column = config.segments.trailer_count_column

    detail_fields_by_stage = {f.stage_column: f.source_column for f in spec.detail_segment.fields}
    detail_natural_key_source_columns = [
        detail_fields_by_stage[stage_column] for stage_column in spec.natural_key_columns
    ]

    def _standard_type(datatype: str) -> str:
        # FRD-driven AS-IS switch: business columns are STRING in BOTH layers
        # (audit columns keep their own types; they are appended separately).
        return "STRING" if spec.load_as_is else sql_type(datatype)

    standard = None
    standard_tables: list[dict] = []
    if spec.standard_table is not None:
        detail_fields = spec.detail_segment.fields
        standard_columns = [
            (f.standard_column, _standard_type(f.standard_datatype))
            for f in detail_fields
            if f.standard_column is not None and f.standard_datatype is not None
        ]
        standard = {
            "catalog": spec.standard_table.catalog,
            "schema": spec.standard_table.schema_name,
            "table": spec.standard_table.table,
            "columns": standard_columns,
            "load_strategy": spec.standard_load_strategy,
        }
        # Per-segment standard tables (segmented dialect: H/D/T map to their
        # own tables in BOTH layers). Flat feeds carry no per-segment
        # standard_table, so this stays the single entry and emission is
        # byte-identical.
        per_segment = [s for s in spec.segments if s.standard_table is not None]
        if per_segment:
            for seg_spec in per_segment:
                standard_tables.append({
                    "catalog": seg_spec.standard_table.catalog,
                    "schema": seg_spec.standard_table.schema_name,
                    "table": seg_spec.standard_table.table,
                    "columns": [
                        (f.standard_column, _standard_type(f.standard_datatype))
                        for f in seg_spec.fields
                        if f.standard_column is not None
                        and f.standard_datatype is not None
                    ],
                    "load_strategy": spec.standard_load_strategy,
                    "audit_columns": (
                        [(a.column, sql_type(a.datatype))
                         for a in seg_spec.audit_columns]
                        if seg_spec.audit_columns is not None
                        else [(a.column, sql_type(a.datatype))
                              for a in spec.audit_columns]
                    ),
                })
        else:
            standard_tables = [standard]

    recycle = None
    if spec.recycle is not None:
        recycle_key = spec.recycle.spec.applies_to
        key_stage = {f.source_column: f.stage_column for f in spec.detail_segment.fields}.get(
            recycle_key
        )
        if key_stage is None:
            raise TemplateGapError(
                f"recycle applies_to '{recycle_key}' has no stage column in the Detail segment"
            )
        filter_column = None
        filter_value = None
        if spec.recycle.reference_filter is not None:
            match = _EQUALITY_FILTER_RE.match(spec.recycle.reference_filter)
            if match is None:
                raise TemplateGapError(
                    "reference filter is not a simple equality, no template covers "
                    f"it: {spec.recycle.reference_filter!r}"
                )
            filter_column = match.group("column")
            filter_value = match.group("value").strip("'")
        recycle = {
            "table": spec.recycle.recycle_table.table,
            "window_days": spec.recycle.spec.recycle_window_days,
            "key_stage_column": key_stage,
            "reference_table": spec.recycle.reference_table,
            "reference_id_column": spec.recycle.reference_id_column,
            "reference_filter": spec.recycle.reference_filter,
            "reference_filter_column": filter_column,
            "reference_filter_value": filter_value,
            "on_no_match": spec.recycle.spec.on_no_match,
        }

    return {
        "feed": {
            "id": spec.feed_id,
            "slug": spec.feed_slug,
            "name": spec.feed_name,
            "source_system": spec.source_system,
        },
        "provenance": {
            "frd_name": spec.frd_contract_name,
            "frd_sha": spec.frd_contract_sha256,
            "sttm_name": spec.sttm_contract_name,
            "sttm_sha": spec.sttm_contract_sha256,
            "synthetic": spec.sttm_is_synthetic,
            # Three-input model summary for the banner: what each input
            # contributed and what is still stubbed/unknown.
            "inputs": {
                "standards_status": config.engineering_standards.status,
                "writer_behavior": WRITER_BEHAVIOR,
                **summarize(faq),
            },
            # Document-derived record identification (segmented extraction
            # only); None on flat feeds so their banners stay byte-identical.
            "segmented": (
                {
                    "trailer_marker": spec.segmented_extraction.identification.trailer_marker,
                    "header_rule": spec.segmented_extraction.identification.header_rule,
                    "method": spec.segmented_extraction.identification.method,
                }
                if spec.segmented_extraction is not None
                else None
            ),
        },
        "standards": {
            "status": config.engineering_standards.status,
            "create_tables": config.engineering_standards.create_tables,
        },
        "job_name": resolve_job_name(
            config.engineering_standards,
            faq,
            spec.feed_slug,
            source=spec.source_system,
            domain=spec.domain,
            sub_domain=spec.sub_domain,
            lobs=spec.lobs,
        ),
        # EDO workspace notebook name; the legacy leaf when unconfigured.
        "workspace_notebook_name": resolve_notebook_name(
            config.engineering_standards,
            faq,
            spec.feed_slug,
            source=spec.source_system,
            domain=spec.domain,
            sub_domain=spec.sub_domain,
            lobs=spec.lobs,
        )
        or "notebook_entrypoint",
        "lobs": spec.lobs,
        "file_name_patterns": spec.file_name_patterns,
        "file_regexes": [pattern_to_regex(p) for p in spec.file_name_patterns],
        "example_file_name": example_file_name(spec.file_name_patterns[0]),
        "e2e_file_names": [
            example_file_name(spec.file_name_patterns[0], variant) for variant in range(5)
        ],
        "file_format": spec.file_format,
        "delimiter": spec.delimiter,
        "landing_location": spec.landing_location,
        "default_catalog": next((s.stage_table.catalog for s in spec.segments), None),
        "stage_schema": spec.segments[0].stage_table.schema_name,
        "is_segmented": spec.is_segmented,
        # Derived record identification (segmented extraction); None on flat
        # feeds and on legacy config-discriminator contracts.
        "segment_identification": (
            {
                "method": spec.segmented_extraction.identification.method,
                "trailer_marker": spec.segmented_extraction.identification.trailer_marker,
                "citation": spec.segmented_extraction.identification.citation,
            }
            if spec.segmented_extraction is not None and spec.is_segmented
            else None
        ),
        "record_type_column": config.segments.record_type_column if spec.is_segmented else None,
        "segments": segments,
        "detail": detail,
        "audit_columns": [(a.column, sql_type(a.datatype)) for a in spec.audit_columns],
        # True only when the contract declares a FILE_TYPE audit column
        # (segmented-extraction feeds); flat feeds render byte-identically.
        "has_file_type_audit": any(a.column == "FILE_TYPE" for a in spec.audit_columns),
        "natural_key": spec.natural_key_columns,
        "phi_columns": spec.phi_columns,
        "errors_table": spec.errors_table.table,
        "processed_files_table": spec.processed_files_table.table,
        "recycle": recycle,
        "standard": standard,
        "standard_tables": standard_tables,
        "stage_load_strategy": spec.stage_load_strategy,
        "trailer_count_stage_column": trailer_count_stage_column,
        "trailer_count_source_column": trailer_count_source_column,
        "detail_natural_key_source_columns": detail_natural_key_source_columns,
        # Key column the generated tests probe with: the first natural-key
        # source when keys exist (flat feeds — byte-identical), else the
        # recycle key (a no-keys feed can still exercise the reference path),
        # else None (the null-key tests are omitted).
        "test_key_source_column": (
            detail_natural_key_source_columns[0]
            if detail_natural_key_source_columns
            else (spec.recycle.spec.applies_to if spec.recycle is not None else None)
        ),
        "has_null_key_test": bool(detail_natural_key_source_columns),
        "masking": {
            "visible_chars": config.masking.visible_chars,
            "mask_char": config.masking.mask_char,
        },
        "allow_duplicate_file_name": allow_duplicate_file_name,
        "duplicate_rule_text": duplicate_rule_text,
        "notifications": {
            "emails": config.job.notification_emails,
            "rule_texts": notification_rule_texts,
        },
        "schedule": schedule_from_sla(spec.frequency),
        "sla_texts": spec.load_windows_sla,
        "job": {
            "spark_version": config.job.spark_version,
            "node_type_id": config.job.node_type_id,
            "num_workers": config.job.num_workers,
            # EDO coding standard: never ship the platform default timeout.
            "timeout_seconds": config.job.timeout_hours * _SECONDS_PER_HOUR,
            "runtime_engine": config.job.runtime_engine,
        },
    }
