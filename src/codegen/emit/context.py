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

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec, SegmentSpec

# Contract file-name patterns use date placeholders; longest tokens first so
# CCYYMMDD is consumed before CCYY / MM. "*" is a free wildcard.
_PLACEHOLDER_MAP = {
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


def _segment_context(
    segment: SegmentSpec, spec: ResolvedFeedSpec, config: Config
) -> dict[str, Any]:
    record_type_value = None
    if spec.is_segmented:
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
        "source_columns": [f.source_column for f in segment.fields],
        "stage_columns": [f.stage_column for f in segment.fields],
        "not_null_stage_columns": not_null_stage,
        "column_samples": [
            (f.source_column, f.sample_value if f.sample_value is not None else "x")
            for f in segment.fields
        ],
    }


def build_context(
    spec: ResolvedFeedSpec,
    config: Config,
    *,
    allow_duplicate_file_name: bool,
    duplicate_rule_text: str | None,
    notification_rule_texts: list[str],
) -> dict[str, Any]:
    """Everything the templates interpolate, and nothing they compute."""
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

    standard = None
    if spec.standard_table is not None:
        detail_fields = spec.detail_segment.fields
        standard_columns = [
            (f.standard_column, sql_type(f.standard_datatype))
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
        },
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
        "record_type_column": config.segments.record_type_column if spec.is_segmented else None,
        "segments": segments,
        "detail": detail,
        "audit_columns": [(a.column, sql_type(a.datatype)) for a in spec.audit_columns],
        "natural_key": spec.natural_key_columns,
        "phi_columns": spec.phi_columns,
        "errors_table": spec.errors_table.table,
        "processed_files_table": spec.processed_files_table.table,
        "recycle": recycle,
        "standard": standard,
        "stage_load_strategy": spec.stage_load_strategy,
        "trailer_count_stage_column": trailer_count_stage_column,
        "trailer_count_source_column": trailer_count_source_column,
        "detail_natural_key_source_columns": detail_natural_key_source_columns,
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
        },
    }
