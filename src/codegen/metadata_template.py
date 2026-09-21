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
from pathlib import PurePosixPath

from codegen.config import Config, MetadataTemplateConfig
from codegen.contracts.frd import FrdFeed
from codegen.contracts.resolved import ResolvedFeedSpec, SegmentSpec
from codegen.contracts.sttm import SttmField

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
    return _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(citation=tpl.citation))


def _with_constants(tpl: MetadataTemplateConfig, tab: str, cells: dict) -> dict:
    for header in tpl.constants.get(tab, {}):
        if header not in cells:
            cells[header] = _const(tpl, tab, header)
    return cells


def _base_type(dtype: str | None) -> str:
    return re.sub(r"\(.*\)", "", dtype or "").strip()


def _distinct_fields(spec: ResolvedFeedSpec) -> list[SttmField]:
    """Fields across segments, one per stage column, STTM order (the
    segments-in-one-table shape lists each shared column once)."""
    seen: set[str] = set()
    out: list[SttmField] = []
    for segment in spec.segments:
        for f in segment.fields:
            if f.stage_column not in seen:
                seen.add(f.stage_column)
                out.append(f)
    return out


def _audit(spec: ResolvedFeedSpec, tpl: MetadataTemplateConfig) -> list[tuple[str, str]]:
    return [(a.column, tpl.audit_type_casing.get(a.datatype, a.datatype))
            for a in spec.audit_columns]


def _qualified(table) -> str:
    parts = [table.catalog, table.schema_name, table.table]
    return ".".join(p for p in parts if p)


def _landing(feed: FrdFeed) -> str | None:
    if not feed.landing_location:
        return None
    value = feed.landing_location.replace("\\", "/")
    return "/" + value.strip("/") + "/"


def _paths(tpl: MetadataTemplateConfig, tab: str, feed: FrdFeed,
           stage_table: str, reject_table: str) -> dict[str, dict]:
    landing = _landing(feed)
    if landing is None:
        return {}
    cells = {}
    for header, pattern in tpl.path_patterns.get(tab, {}).items():
        value = pattern.format(landing=landing, stage_table=stage_table,
                               reject_table=reject_table)
        cells[header] = _cell(value.replace("//", "/"), "synthetic",
                              _PATH_TOOLTIP.format(citation=tpl.citation))
    return cells


def _object_name(pattern: str) -> str:
    stem = PurePosixPath(pattern).stem if "." in pattern else pattern
    return re.sub(r"_\*|\*_|\*", "", stem)


def _faq_cell(faq, name: str, label: str) -> dict | None:
    from codegen.metadata_sheet import _faq_cell as base

    return base(getattr(faq, name, None), label) if faq is not None else None


def _process_name(faq) -> dict | None:
    return _faq_cell(faq, "process_name", "framework process name (load-pattern FAQ)")


def _frequency(feed: FrdFeed, faq) -> dict:
    from codegen.metadata_sheet import _frequency_cell

    return _frequency_cell(feed, faq)


def _reject_table(tpl: MetadataTemplateConfig, spec: ResolvedFeedSpec, stage_table: str) -> str:
    if tpl.reject_table_suffix is not None:
        return f"{stage_table}{tpl.reject_table_suffix}"
    return spec.errors_table.table


# -- tabs ---------------------------------------------------------------------- #


def _pipeline_schedule(tab, feed, config, spec, faq, tpl) -> list[dict]:
    rows = tpl.template_rows.get(tab) or [{}]
    out = []
    for template_row in rows:
        cells = {
            header: _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(citation=tpl.citation))
            for header, value in template_row.items() if not header.startswith("_")
        }
        cells["PIPELINE_FREQUENCY"] = _frequency(feed, faq)
        process = _process_name(faq)
        if process is not None:
            cells["APPLICATION_NAME"] = process
        out.append(_with_constants(tpl, tab, cells))
    return out


def _file_adls(tab, feed, config, spec, faq, tpl) -> list[dict]:
    cells = {
        "DOMAIN": _cell(feed.domain or "", "from_frd"),
        "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
    }
    landing = _landing(feed)
    if landing is not None:
        cells["TGT_ADLS_PATH"] = _cell(landing, "from_frd",
                                       "FRD Structural Metadata → ADLS Location")
    return [_with_constants(tpl, tab, cells)]


def _adls_delta(tab, feed, config, spec, faq, tpl) -> list[dict]:
    if spec is None:
        return []
    fields = _distinct_fields(spec)
    audit = _audit(spec, tpl)
    stage = spec.detail_segment.stage_table
    reject = _reject_table(tpl, spec, stage.table)
    patterns = (list(spec.file_name_patterns) if tpl.rows_per_file_pattern
                else ["; ".join(spec.file_name_patterns)])
    if tpl.src_columns_style == "positional":
        src_columns = ",".join(f"col{i}:{f.stage_column}" for i, f in enumerate(fields, start=1))
    else:
        src_columns = ",".join(f"{f.source_column}:{f.stage_column}" for f in fields)
    if tpl.data_type_style == "base":
        src_types = ",".join(f"{f.source_datatype}:{_base_type(f.stage_datatype)}" for f in fields)
    else:
        src_types = ",".join(f"{f.source_datatype}:{f.stage_datatype}" for f in fields)
    rows = []
    for pattern in patterns:
        cells = {
            "OBJECT_NAME": (_cell(_object_name(pattern), "from_frd",
                                  f"derived from the file pattern {pattern!r} (wildcards and "
                                  "extension removed)")
                            if tpl.object_name_from_pattern
                            else _cell(feed.feed_name, "from_frd")),
            "DOMAIN": _cell(feed.domain or "", "from_frd"),
            "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
            "SOURCE": _cell(feed.source_system, "from_frd"),
            "FREQUENCY": _frequency(feed, faq),
            "LOB": _cell(", ".join(feed.lobs), "from_frd"),
            "SRC_FILE_NAME": _cell(pattern, "from_frd" if feed.file_name_patterns else "from_sttm"),
            "SRC_COLUMNS": _cell(src_columns, "from_sttm"),
            "SRC_DATA_TYPE": _cell(src_types, "from_sttm"),
            "TGT_DATABASE_NAME": _cell(stage.schema_name, "from_frd"),
            "TGT_TABLE_NAME": _cell(stage.table, "from_frd"),
            "TGT_COLUMN_NAMES": _cell(
                ",".join([f.stage_column for f in fields] + [c for c, _t in audit]), "from_sttm"),
            "TGT_DATA_TYPE": _cell(
                ",".join([f.stage_datatype for f in fields] + [t for _c, t in audit]), "from_sttm"),
            "TGT_LOAD_OPTION": _cell(spec.stage_load_strategy, "from_frd",
                                     "FRD Structural Metadata → Load Strategy STG"),
            "TGT_RJT_TABLE_NAME": _cell(
                reject, "synthetic" if tpl.reject_table_suffix is not None else "from_sttm",
                _TEMPLATE_TOOLTIP.format(citation=tpl.citation)
                if tpl.reject_table_suffix is not None else "stage table + errors suffix"),
            "RECYCL_ENBL_FLG": _cell("Y" if spec.recycle else "N", "from_frd"),
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
            cells["SRC_ADLS_PATH"] = _cell(landing, "from_frd",
                                           "FRD Structural Metadata → ADLS Location")
        if spec.delimiter:
            cells["SRC_FILE_DELIMITER"] = _cell(spec.delimiter, "from_frd")
        header_flag = _faq_cell(faq, "has_header", "load-pattern FAQ answer")
        if header_flag is not None:
            cells["HEADER_FLAG"] = header_flag
        if spec.not_null_columns:
            cells["MANDATORY_FIELD_LIST"] = _cell(",".join(spec.not_null_columns), "from_sttm")
        if spec.natural_key_columns:
            cells["TGT_PRIMARY_KEY"] = _cell(",".join(spec.natural_key_columns), "from_sttm",
                                             "the mapping contract's natural key columns")
        cells.update(_paths(tpl, tab, feed, stage.table, reject))
        rows.append(_with_constants(tpl, tab, cells))
    return rows


def _stg_std(tab, feed, config, spec, faq, tpl) -> list[dict]:
    if spec is None or spec.standard_table is None:
        return []
    fields = [f for f in _distinct_fields(spec) if f.standard_column]
    audit = _audit(spec, tpl)
    stage = spec.detail_segment.stage_table
    standard = spec.standard_table
    reject = _reject_table(tpl, spec, standard.table)
    if tpl.data_type_style == "base":
        src_types = [f"{_base_type(f.stage_datatype)}:{_base_type(f.standard_datatype)}"
                     for f in fields] + [f"{t}:{t}" for _c, t in audit]
    else:
        src_types = [f"{f.stage_datatype}:{f.standard_datatype}" for f in fields] + [
            f"{t}:{t}" for _c, t in audit]
    cells = {
        "OBJECT_NAME": _cell(feed.feed_name, "from_frd"),
        "DOMAIN": _cell(feed.domain or "", "from_frd"),
        "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
        "SOURCE": _cell(feed.source_system, "from_frd"),
        "FREQUENCY": _frequency(feed, faq),
        "LOB": _cell(", ".join(feed.lobs), "from_frd"),
        "SRC_CATALOG_NAME": _cell(stage.catalog or "", "from_frd"),
        "SRC_SCHEMA_NAME": _cell(stage.schema_name, "from_frd"),
        "SRC_TABLE_NAME": _cell(stage.table, "from_frd"),
        "SRC_COLUMNS": _cell(
            ",".join([f"{f.stage_column}:{f.standard_column}" for f in fields]
                     + [f"{c}:{c}" for c, _t in audit]), "from_sttm"),
        "SRC_DATA_TYPE": _cell(",".join(src_types), "from_sttm"),
        "TGT_CATALOG_NAME": _cell(standard.catalog or "", "from_frd"),
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
    if spec.standard_load_strategy:
        cells["TGT_LOAD_OPTION"] = _cell(spec.standard_load_strategy, "from_frd",
                                         "FRD Structural Metadata → Load Strategy STD")
    if spec.natural_key_columns:
        cells["TGT_PRIMARY_KEY"] = _cell(",".join(spec.natural_key_columns), "from_sttm",
                                         "the mapping contract's natural key columns")
    cells.update(_paths(tpl, tab, feed, standard.table, reject))
    return [_with_constants(tpl, tab, cells)]


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
            "TGT_TABLE": _cell(_qualified(stage), "from_frd"),
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
        cells = {
            header: _cell(value, "synthetic", _TEMPLATE_TOOLTIP.format(citation=tpl.citation))
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
        out.append(_with_constants(tpl, tab, cells))
    return out


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


def _dq_rules(tab, feed, config, spec, faq, tpl) -> list[dict]:
    if spec is None or not tpl.dq_rules:
        return []
    fields = _distinct_fields(spec)
    stage = spec.detail_segment.stage_table
    objects = (list(spec.file_name_patterns) if tpl.rows_per_file_pattern else [None])
    rules: list[dict] = []
    for kind in tpl.dq_rules:
        if kind == "date_format":
            columns, params = _date_rule(tpl, fields)
            if not columns:
                continue
            joined = ",".join(columns)
            rules.append({
                "RULE_CLASS": _cell(tpl.dq_rule_classes.get(kind, kind), "synthetic",
                                    _TEMPLATE_TOOLTIP.format(citation=tpl.citation)),
                "SOURCE_COLUMN": _cell(joined, "from_sttm", "STTM Load Rule: date conversion"),
                "INPUT_PARAM": _cell(";".join(params), "from_sttm",
                                     "STTM Load Rule text, formats in the template's shape"),
                "TARGET_COLUMN": _cell(joined, "from_sttm"),
            })
        elif kind == "data_type_cast":
            typed = [f for f in fields if _base_type(f.stage_datatype).lower() != "string"]
            if not typed:
                continue
            typed = _by_type_order(typed, tpl.cast_type_order)  # stable within a type
            joined = ",".join(f.stage_column for f in typed)
            rules.append({
                "RULE_CLASS": _cell(tpl.dq_rule_classes.get(kind, kind), "synthetic",
                                    _TEMPLATE_TOOLTIP.format(citation=tpl.citation)),
                "SOURCE_COLUMN": _cell(joined, "from_sttm", "STTM stage columns typed "
                                       "other than String"),
                "INPUT_PARAM": _cell(_qualified(stage), "from_frd", "qualified stage table"),
                "TARGET_COLUMN": _cell(joined, "from_sttm"),
            })
    rows = []
    for _object in objects:
        for index, rule in enumerate(rules, start=1):
            cells = dict(rule)
            cells["SEQUENCE_NO"] = _cell(index, "synthetic",
                                         _TEMPLATE_TOOLTIP.format(citation=tpl.citation))
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
        out.append(_with_constants(tpl, tab, cells))
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
                      faq, tpl: MetadataTemplateConfig) -> list[dict]:
    """Cells for one tab of a non-default IIG template (rows without the
    header/always_blank assembly, which ``metadata_sheet._row`` does)."""
    builder = _BUILDERS.get(tab)
    if builder is None:
        return []
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
