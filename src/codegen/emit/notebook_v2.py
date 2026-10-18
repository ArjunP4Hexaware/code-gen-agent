"""post69: notebook v2 — the standalone notebook rendered FROM the IIG rows.

Selected by the conventions profile (``notebook_version: v2``; acfc_prx), v1
(``codegen.emit.notebook``) stays as it was for every other profile. v2 reads
the rows the workbook emitter produced (``FrameworkArtefacts.payload``: the
same feed contract, environment profile, overlay and answers) and states
nothing the IIG does not: every constant in the notebook is an IIG cell, or the
run's environment profile (the storage account). Jinja only
(``templates/notebook_v2``); no model call.

Cells: title · config · read (+ provenance) · stage (+ provenance) · standard
(+ provenance) · DQ (+ provenance) · run · review-only Layer-2 candidates.
The DQ cell renders one call per DATA_QUALITY_RULES row through a rule
registry (``RULES``); a RULE_CLASS outside it is a markdown cell "rule not
implemented" and a gate flag, never code. A cell the notebook needs and the
IIG leaves open makes the config cell stop the run (``OPEN_CELLS``) and is a
gate flag; a value the environment leaves unset is already a blocking line
(``codegen.emit.notebook_env`` via ``codegen.generate_run``).

Written to ``<feed>/notebook/<slug>.ipynb`` and ``<slug>.py`` (Databricks
source) — the manifest's notebook_emit stage.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, StrictUndefined

from codegen.emit import notebook_files as nbf

NOTEBOOK_DIR = "notebook"
ADLS = "ADLS_DELTA_INGESTION_DETAILS"
FIXED = "ADLS_FIXED_WIDTH_HANDLER"
STD = "STGDELTA_STDDELTA_INGESTION_DET"
DQ = "DATA_QUALITY_RULES"
DRY_RUN_ROWS = 100
NA = {"", "NA", "N/A"}

# RULE_CLASS -> the registry entry (templates/notebook_v2/dq.py.j2 renders it).
# The corpus's classes (config/overlays/acfc_env.yaml dq_rule_classes, the base
# template's DateFormatRule); a class not here is "rule not implemented".
RULES = {
    "DateFormatRule": "date_format",
    "DataTypeCastRule": "data_type_cast",
    "LRTrimRule": "lr_trim",
    "DateConversionRule": "date_conversion",
    "NullCheckRule": "null_check",
    "DeDuplicationRule": "dedup",
    "AddCustomColumnsRule": "add_custom_columns",
    "LoadHeaderAndTrailerToSeparateTablesRule": "header_trailer_split",
}
# the profile's audit columns the stage cell knows how to fill
AUDIT_VALUES = {"LOB": "lob", "SRC_FILE_NAME": "file_name",
                "REC_CREATION_TIME": "timestamp", "REC_UPDATED_TIME": "timestamp"}
# IIG header -> the FRD contract field it is read from (provenance coordinates)
FRD_FIELDS = {
    "DOMAIN": "domain", "SUBDOMAIN": "sub_domain", "SOURCE": "source_system",
    "FREQUENCY": "frequency", "SRC_FILE_DELIMITER": "delimiter", "SRC_FORMAT": "file_format",
    "SRC_ADLS_PATH": "landing_location", "SRC_FILE_NAME": "file_name_patterns",
    "LOB": "lobs", "TGT_LOAD_OPTION": "stage_target.load_strategy",
}
STTM_COLUMN_HEADERS = ("SRC_COLUMNS", "SRC_DATA_TYPE", "TGT_COLUMN_NAMES", "TGT_DATA_TYPE",
                       "MANDATORY_FIELD_LIST", "TGT_PRIMARY_KEY", "COL", "LEN", "start_ind")


@dataclass
class NotebookV2:
    cells: list[nbf.Cell]
    ipynb: str
    source: str
    flags: list[str] = field(default_factory=list)
    checks: list = field(default_factory=list)


def notebook_version(config, conventions_profile: str | None) -> str:
    """The profile's notebook: ``v1`` | ``v2`` (post69)."""
    return config.conventions.get(conventions_profile).notebook_version


# ---------------------------------------------------------------- IIG values


def split_list(text: str | None) -> list[str]:
    """A comma list, commas inside parentheses kept (``Decimal(17,2)``)."""
    if not text or str(text).strip() in NA:
        return []
    items, depth, current = [], 0, ""
    for char in str(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            items.append(current.strip())
            current = ""
        else:
            current += char
    items.append(current.strip())
    return [i for i in items if i]


def _pairs(text: str | None) -> list[tuple[str, str]]:
    out = []
    for item in split_list(text):
        left, sep, right = item.partition(":")
        out.append((left.strip(), right.strip()) if sep else (item.strip(), item.strip()))
    return out


def _value(row: dict, header: str) -> str:
    value = row["values"].get(header)
    return "" if value is None else str(value).strip()


def _flag(value: str) -> bool:
    return value.strip().upper() in ("Y", "YES", "TRUE")


def _rows(payload: dict, tab: str) -> list[tuple[int, dict]]:
    """(workbook row number, row) — the header is row 1."""
    rows = ((payload.get("tabs") or {}).get(tab) or {}).get("rows") or []
    return [(i + 2, row) for i, row in enumerate(rows)]


@dataclass
class _Open:
    cells: list[str] = field(default_factory=list)

    def need(self, row: dict, number: int, tab: str, header: str) -> str:
        value = _value(row, header)
        if not value:
            self.cells.append(f"{tab}.{header} (row {number})")
        return value


def _date_formats(param: str, joiner: str) -> tuple[str, str] | None:
    source, sep, target = param.partition(joiner)
    return (source.strip(), target.strip()) if sep and source.strip() else None


# ---------------------------------------------------------------- the context


def _sources(payload: dict, opened: _Open) -> list[dict]:
    sources = []
    for index, (number, row) in enumerate(_rows(payload, ADLS)):
        delimiter = _value(row, "SRC_FILE_DELIMITER")
        partition = _value(row, "TGT_PARTITION_COLUMN")
        sources.append({
            "index": index, "row": number,
            "object_name": _value(row, "OBJECT_NAME"),
            "lob": _value(row, "LOB"),
            "file_pattern": opened.need(row, number, ADLS, "SRC_FILE_NAME"),
            "file_format": _value(row, "SRC_FORMAT"),
            "delimiter": delimiter,
            "header": _flag(_value(row, "HEADER_FLAG")),
            "footer": _flag(_value(row, "FILE_FOOTER_FLAG")),
            "compression": "" if _value(row, "SRC_COMPRESSION").upper() in ("N", *NA)
            else _value(row, "SRC_COMPRESSION"),
            "multiline": _flag(_value(row, "MULTILINE_FLAG")),
            "landing_container": opened.need(row, number, ADLS, "SRC_CONTAINER_NAME"),
            "landing_path": opened.need(row, number, ADLS, "SRC_ADLS_PATH"),
            "archive_path": _value(row, "SRC_ADLS_ARCHVL_PATH"),
            "reject_container": _value(row, "TGT_CONTAINER_NAME"),
            "reject_path": _value(row, "TGT_RJT_ADLS_PATH"),
            "src_columns": _pairs(opened.need(row, number, ADLS, "SRC_COLUMNS")),
            "src_types": _pairs(_value(row, "SRC_DATA_TYPE")),
            "mandatory": split_list(_value(row, "MANDATORY_FIELD_LIST")),
            "schema": opened.need(row, number, ADLS, "TGT_DATABASE_NAME"),
            "table": opened.need(row, number, ADLS, "TGT_TABLE_NAME"),
            "target_columns": split_list(_value(row, "TGT_COLUMN_NAMES")),
            "target_types": split_list(_value(row, "TGT_DATA_TYPE")),
            "load_option": opened.need(row, number, ADLS, "TGT_LOAD_OPTION"),
            "partition_column": "" if partition in NA else partition,
            "partition_value": _value(row, "TGT_PARTITION_VALUE"),
            "primary_key": split_list(_value(row, "TGT_PRIMARY_KEY")),
        })
        if sources[-1]["mandatory"]:
            opened.need(row, number, ADLS, "TGT_RJT_ADLS_PATH")
            opened.need(row, number, ADLS, "TGT_CONTAINER_NAME")
    return sources


def _detail_label(spec) -> str | None:
    """The Detail segment's spelling as the workbook writes it (the handler
    rows' SEGMENT), from the resolved spec."""
    for segment in spec.segments:
        if segment.segment == "Detail":
            return next((f.record_segment_label for f in segment.fields
                         if f.record_segment_label), None)
    return None


def _segments(payload: dict, opened: _Open, detail_table: str,
              detail_label: str | None) -> list[dict]:
    rows = _rows(payload, FIXED)
    segments = []
    for number, row in rows:
        names = split_list(_value(row, "COL"))
        lengths = split_list(_value(row, "LEN"))
        starts = split_list(_value(row, "start_ind"))
        if not (names and len(names) == len(lengths) == len(starts)):
            opened.cells.append(f"{FIXED}.COL/LEN/start_ind (row {number})")
        target = _value(row, "TGT_TABLE")
        segments.append({
            "row": number, "segment": _value(row, "SEGMENT"),
            "filter": (opened.need(row, number, FIXED, "SEGMENT_FILTER") if len(rows) > 1
                       else _value(row, "SEGMENT_FILTER")),
            "columns": [(n, int(s), int(ln)) for n, s, ln in zip(names, starts, lengths,
                                                                strict=False)
                        if s.isdigit() and ln.isdigit()],
            "table": target,
            "audit": split_list(_value(row, "TGT_AUDIT_CLMS")),
            # the segment's records load with the detail's (one shared stage table)
            "shared": target.split(".")[-1].lower() == detail_table.lower(),
            "detail": False,
        })
    detail = next((s for s in segments if detail_label and s["segment"] == detail_label),
                  next((s for s in segments if s["shared"]), segments[0] if segments else None))
    if detail is not None:
        detail["detail"] = True
    return segments


def _standards(payload: dict, opened: _Open) -> list[dict]:
    out = []
    for number, row in _rows(payload, STD):
        partition = _value(row, "TGT_PARTITION_COLUMN")
        out.append({
            "index": len(out), "row": number,
            "src_catalog": opened.need(row, number, STD, "SRC_CATALOG_NAME"),
            "src_schema": opened.need(row, number, STD, "SRC_SCHEMA_NAME"),
            "src_table": opened.need(row, number, STD, "SRC_TABLE_NAME"),
            "catalog": opened.need(row, number, STD, "TGT_CATALOG_NAME"),
            "schema": opened.need(row, number, STD, "TGT_SCHEMA_NAME"),
            "table": opened.need(row, number, STD, "TGT_TABLE_NAME"),
            "mapping": _pairs(_value(row, "SRC_COLUMNS")),
            "target_columns": split_list(_value(row, "TGT_COLUMN_NAMES")),
            "target_types": split_list(_value(row, "TGT_DATA_TYPE")),
            "load_option": opened.need(row, number, STD, "TGT_LOAD_OPTION"),
            "partition_column": "" if partition in NA else partition,
            "partition_value": _value(row, "TGT_PARTITION_VALUE"),
            "primary_key": split_list(_value(row, "TGT_PRIMARY_KEY")),
            "mapping_expression": _value(row, "MAPPING_EXPRESSION"),
            "reject_container": _value(row, "TGT_CONTAINER_NAME"),
            "reject_path": _value(row, "TGT_RJT_ADLS_PATH"),
        })
    return out


def _fqn(*parts: str) -> str:
    return ".".join(p for p in parts if p).lower()


def _dq(payload: dict, sources: list[dict], standards: list[dict],
        joiner: str) -> tuple[list[dict], list[dict], list[dict]]:
    """(stage-leg calls, standard-leg calls, not implemented): one per row.
    A rule's leg: its INPUT_PARAM names a standard table / the RULE_TYPE says
    STDDelta -> standard; else stage. Per-file copies of a stage rule (one per
    ADLS row, in row order) go to their file; a single row to every file."""
    std_fqns = {_fqn(s["catalog"], s["schema"], s["table"]): s["index"] for s in standards}
    std_fqns.update({_fqn(s["schema"], s["table"]): s["index"] for s in standards})
    stage, standard, missing = [], [], []
    seen: dict[tuple, int] = {}
    rows = _rows(payload, DQ)
    counts: dict[tuple, int] = {}
    for _number, row in rows:
        key = tuple(_value(row, h) for h in ("RULE_CLASS", "SOURCE_COLUMN", "INPUT_PARAM",
                                             "TARGET_COLUMN"))
        counts[key] = counts.get(key, 0) + 1
    for number, row in rows:
        rule_class = _value(row, "RULE_CLASS")
        columns = split_list(_value(row, "SOURCE_COLUMN"))
        param = _value(row, "INPUT_PARAM")
        target = _value(row, "TARGET_COLUMN")
        call = {"row": number, "rule_class": rule_class, "columns": columns, "param": param,
                "target": target, "sequence": _value(row, "SEQUENCE_NO"),
                "rule_type": _value(row, "RULE_TYPE")}
        kind = RULES.get(rule_class)
        if kind is None:
            missing.append({**call, "why": "RULE_CLASS not in the notebook's rule registry"})
            continue
        if kind in ("date_format", "date_conversion"):
            formats = [_date_formats(p, joiner) for p in param.split(";")] if param else []
            if not formats or any(f is None for f in formats):
                missing.append({**call, "why": "INPUT_PARAM states no source / target "
                                               "date format"})
                continue
            call["formats"] = formats if len(formats) == len(columns) else formats[:1] * len(
                columns)
        std_index = std_fqns.get(param.lower()) if param else None
        if std_index is None and (call["rule_type"].lower() == "stddelta"
                                  or kind in ("lr_trim", "date_conversion")):
            std_index = next((s["index"] for s in standards
                              if set(columns) <= set(s["target_columns"])), None)
            if std_index is None and len(standards) == 1:
                std_index = 0
        call["kind"] = kind
        if std_index is not None:
            types = dict(zip(standards[std_index]["target_columns"],
                             standards[std_index]["target_types"], strict=False))
            call["types"] = [types.get(c, "") for c in columns]
            standard.append({**call, "standard": std_index})
            continue
        key = (rule_class, _value(row, "SOURCE_COLUMN"), param, target)
        occurrence = seen.get(key, 0)
        seen[key] = occurrence + 1
        per_file = counts[key] == len(sources) and len(sources) > 1
        call["source"] = occurrence if per_file else None
        if kind == "data_type_cast":
            first = sources[occurrence if per_file else 0] if sources else None
            types = dict(zip(first["target_columns"], first["target_types"],
                             strict=False)) if first else {}
            call["types"] = [types.get(c, "") for c in columns]
        stage.append(call)
    return stage, standard, missing


def _sheet_index(spec, config, sttm_path: Path | None = None) -> dict[str, int]:
    """STTM sheet name -> its 0-based position (coordinates only; {} when the
    workbook the contract was extracted from is not readable here)."""
    from codegen.layout.sheet_refs import workbook_sheet_names

    path = sttm_path or Path(config.contracts.dir) / spec.sttm_contract_name
    try:
        workbook = json.loads(path.read_text(encoding="utf-8")).get("generated_from_workbook")
    except (OSError, ValueError):
        workbook = None
    return {name: i for i, name in enumerate(workbook_sheet_names(workbook))} if workbook else {}


def _sttm_coordinates(spec, config, sttm_path: Path | None = None) -> str:
    rows = [f.provenance for seg in spec.segments for f in seg.fields
            if getattr(f, "provenance", None) is not None]
    if not rows:
        return "STTM: no field coordinates recorded"
    index = _sheet_index(spec, config, sttm_path)
    by_sheet: dict[str, list[int]] = {}
    for p in rows:
        ref = f"sheets[{index[p.sheet]}]" if p.sheet in index else "sheets[?]"
        by_sheet.setdefault(ref, []).append(p.row)
    return "; ".join(f"STTM {ref} rows {min(r)}-{max(r)}" for ref, r in sorted(by_sheet.items()))


def _frd_coordinates(frd_path: Path | None, feed_index) -> dict[str, str]:
    if frd_path is None or feed_index is None:
        return {}
    try:
        evidence = json.loads(Path(frd_path).read_text(encoding="utf-8")).get(
            "field_provenance") or {}
    except (OSError, ValueError):
        return {}
    out = {}
    for header, name in FRD_FIELDS.items():
        found = evidence.get(f"feeds[{feed_index}].{name}")
        if isinstance(found, dict) and "table" in found:
            out[header] = (f"FRD tables[{found['table']}] row {found.get('row')} "
                           f"col {found.get('col')}")
    return out


def _provenance(tab: str, rows: list[tuple[int, dict]], headers: list[str], sttm: str,
                frd: dict[str, str], env_name: str | None) -> list[dict]:
    lines = []
    for number, row in rows:
        cells = []
        for header in headers:
            if header not in row["values"]:
                continue
            badge = (row["badges"].get(header) or {}).get("badge", "")
            tooltip = (row["badges"].get(header) or {}).get("tooltip") or ""
            if badge == "from_frd":
                where = frd.get(header, "FRD: no field coordinates recorded")
            elif header in STTM_COLUMN_HEADERS and badge.startswith("from_sttm"):
                where = sttm
            elif badge == "from_faq":
                where = "load-pattern FAQ"
            elif env_name and f"environment {env_name} (" in tooltip:
                where = f"environment profile {env_name}"
            elif badge in ("synthetic", "from_standards"):
                where = "template / profile constant"
            elif not _value(row, header):
                where = "open in the IIG"
            else:
                where = badge or "—"
            cells.append({"header": header, "badge": badge or "—", "where": where})
        lines.append({"tab": tab, "row": number, "cells": cells})
    return lines


def build_context(spec, config, payload: dict, *, candidates, frd_path: Path | None,
                  iig_template: str | None, feed_index=None,
                  sttm_path: Path | None = None) -> tuple[dict, list[str]]:
    """The template context and the gate flags."""
    from codegen import environments as envs
    from codegen.build_info import codegen_version

    tpl = config.metadata.templates.get(iig_template or config.metadata.template)
    opened = _Open()
    sources = _sources(payload, opened)
    standards = _standards(payload, opened)
    detail_table = sources[0]["table"] if sources else ""
    segments = _segments(payload, opened, detail_table, _detail_label(spec))
    stage_catalog = standards[0]["src_catalog"] if standards else ""
    if not stage_catalog:
        stage_catalog = envs.default_catalog(config, "stage") or ""
    joiner = tpl.date_format_param_joiner if tpl is not None else "--"
    stage_calls, std_calls, missing = _dq(payload, sources, standards, joiner)
    profile_audit = list(tpl.family_conventions.audit_columns) if tpl is not None else []
    stage_columns = sources[0]["target_columns"] if sources else []
    audit = [c for c in profile_audit if c in stage_columns]
    unknown_audit = [c for c in audit if c not in AUDIT_VALUES]
    try:
        env = envs.run_environment(config)
    except Exception:       # noqa: BLE001 — an incomplete named one fails the run elsewhere
        env = None
    account = (env.entry.storage_account if env is not None else "") or ""
    first = _rows(payload, ADLS)[0][1] if _rows(payload, ADLS) else {"values": {}}
    sttm = _sttm_coordinates(spec, config, sttm_path)
    frd = _frd_coordinates(frd_path, feed_index)
    env_name = env.name if env is not None else None
    adls_rows, std_rows = _rows(payload, ADLS), _rows(payload, STD)
    provenance = {
        "read": _provenance(ADLS, adls_rows, [
            "SRC_FILE_NAME", "SRC_FORMAT", "SRC_FILE_DELIMITER", "HEADER_FLAG",
            "FILE_FOOTER_FLAG", "SRC_COMPRESSION", "MULTILINE_FLAG", "SRC_CONTAINER_NAME",
            "SRC_ADLS_PATH", "SRC_COLUMNS", "SRC_DATA_TYPE", "MANDATORY_FIELD_LIST",
            "TGT_RJT_ADLS_PATH"], sttm, frd, env_name)
        + _provenance(FIXED, _rows(payload, FIXED), [
            "SEGMENT", "SEGMENT_FILTER", "COL", "LEN", "start_ind", "TGT_TABLE",
            "RJCT_RSN_COLUMN_NM"], sttm, frd, env_name),
        "stage": _provenance(ADLS, adls_rows, [
            "TGT_DATABASE_NAME", "TGT_TABLE_NAME", "TGT_COLUMN_NAMES", "TGT_DATA_TYPE",
            "TGT_LOAD_OPTION", "TGT_PARTITION_COLUMN", "TGT_PARTITION_VALUE",
            "TGT_PRIMARY_KEY", "LOB"], sttm, frd, env_name),
        "standard": _provenance(STD, std_rows, [
            "SRC_CATALOG_NAME", "SRC_SCHEMA_NAME", "SRC_TABLE_NAME", "SRC_COLUMNS",
            "TGT_CATALOG_NAME", "TGT_SCHEMA_NAME", "TGT_TABLE_NAME", "TGT_COLUMN_NAMES",
            "TGT_DATA_TYPE", "TGT_LOAD_OPTION", "TGT_PRIMARY_KEY", "MAPPING_EXPRESSION"],
            sttm, frd, env_name),
        "dq": _provenance(DQ, _rows(payload, DQ), [
            "SEQUENCE_NO", "RULE_TYPE", "RULE_CLASS", "SOURCE_COLUMN", "INPUT_PARAM",
            "TARGET_COLUMN"], sttm, frd, env_name),
    }
    flags = [f"notebook_rule_not_implemented:{m['rule_class'] or 'blank'} — DATA_QUALITY_RULES "
             f"row {m['row']}: {m['why']}" for m in missing]
    flags += [f"notebook_iig_cell_open:{cell} — the notebook stops at its config cell until "
              "the IIG states it" for cell in opened.cells]
    flags += [f"notebook_audit_column_unfilled:{c} — the profile's audit column has no "
              "known value rule in the notebook" for c in unknown_audit]
    flags += [f"notebook_mapping_expression_not_implemented:{STD} row {s['row']}"
              for s in standards if s["mapping_expression"]]
    review = [c for c in candidates if getattr(c, "kind", "layer2") == "layer2"
              and c.response is not None]
    context = {
        "feed": {"id": spec.feed_id, "slug": spec.feed_slug, "name": spec.feed_name},
        "meta": {k.lower(): _value(first, k) for k in ("DOMAIN", "SUBDOMAIN", "SOURCE",
                                                       "FREQUENCY")},
        "version": codegen_version(), "iig_template": iig_template or config.metadata.template,
        "env_name": env_name, "storage_account": account,
        "stage_catalog": stage_catalog, "sources": sources, "standards": standards,
        "segments": segments, "fixed_width": bool(segments),
        "reject_reason_column": next((_value(r, "RJCT_RSN_COLUMN_NM") for _n, r
                                      in _rows(payload, FIXED)
                                      if _value(r, "RJCT_RSN_COLUMN_NM")), ""),
        "audit": [{"name": c, "rule": AUDIT_VALUES.get(c)} for c in audit],
        "audit_rules": {c: AUDIT_VALUES[c] for c in profile_audit if c in AUDIT_VALUES},
        "file_column": next((c for c in audit if AUDIT_VALUES.get(c) == "file_name"), ""),
        "stage_calls": stage_calls, "std_calls": std_calls, "missing_rules": missing,
        "open_cells": opened.cells, "provenance": provenance,
        "candidates": [{"rule_text": c.rule_text, "classification":
                        c.response.classification, "code": c.response.code_candidate or "",
                        "rationale": c.response.rationale} for c in review],
        "dry_run_rows": DRY_RUN_ROWS,
        "needs_merge": any(s["load_option"].lower() in ("upsert", "merge")
                           for s in [*sources, *standards]),
        "needs_reduce": any(s["mandatory"] for s in sources) or any(
            c["kind"] == "null_check" for c in [*stage_calls, *std_calls]),
    }
    return context, flags


# ---------------------------------------------------------------- rendering


def _py(value: Any) -> str:
    """A Python literal (strings double-quoted, the JSON spelling)."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return "None"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        inner = ", ".join(_py(v) for v in value)
        return f"({inner},)" if isinstance(value, tuple) and len(value) == 1 else (
            f"({inner})" if isinstance(value, tuple) else f"[{inner}]")
    if isinstance(value, dict):
        return "{" + ", ".join(f"{_py(k)}: {_py(v)}" for k, v in value.items()) + "}"
    raise TypeError(f"no literal for {type(value).__name__}")


def _block(value: list | dict, indent: int = 4) -> str:
    """A list / dict literal, one item per line (stays under the line length)."""
    pad = " " * indent
    close = " " * (indent - 4)
    if isinstance(value, dict):
        body = "".join(f"{pad}{_py(k)}: {_nested(v, indent)},\n" for k, v in value.items())
        return "{\n" + body + close + "}" if value else "{}"
    body = "".join(f"{pad}{_nested(v, indent)},\n" for v in value)
    return "[\n" + body + close + "]" if value else "[]"


def _nested(value: Any, indent: int) -> str:
    if isinstance(value, (list, dict)) and len(_py(value)) > 60:
        return _block(value, indent + 4)
    return _py(value)


def _environment() -> Environment:
    env = Environment(loader=PackageLoader("codegen", "templates/notebook_v2"),
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                      keep_trailing_newline=True)
    env.filters["py"] = _py
    env.filters["block"] = _block
    env.filters["arg"] = lambda value, base: (_py(value) if len(_py(value)) <= 50
                                              else _block(value, base + 4))
    env.filters["mdcell"] = lambda v: str(v).replace("|", "\\|").replace("\n", " ")
    return env


def _render(env: Environment, name: str, context: dict) -> str:
    return env.get_template(name).render(**context)


def render_cells(context: dict) -> list[nbf.Cell]:
    env = _environment()
    cells = [nbf.md("title", _render(env, "title.md.j2", context)),
             nbf.code("config", _render(env, "config.py.j2", context)),
             nbf.code("read", _render(env, "read.py.j2", context)),
             nbf.md("read-provenance", _render(env, "provenance.md.j2",
                                               {"stage": "Read", **context,
                                                "lines": context["provenance"]["read"]})),
             nbf.code("stage", _render(env, "stage.py.j2", context)),
             nbf.md("stage-provenance", _render(env, "provenance.md.j2",
                                                {"stage": "Stage", **context,
                                                 "lines": context["provenance"]["stage"]})),
             nbf.code("standard", _render(env, "standard.py.j2", context)),
             nbf.md("standard-provenance", _render(env, "provenance.md.j2",
                                                   {"stage": "Standard", **context,
                                                    "lines":
                                                        context["provenance"]["standard"]})),
             nbf.code("dq", _render(env, "dq.py.j2", context))]
    cells += [nbf.md(f"dq-not-implemented-{m['row']}",
                     _render(env, "rule_missing.md.j2", {"m": m}))
              for m in context["missing_rules"]]
    cells += [nbf.md("dq-provenance", _render(env, "provenance.md.j2",
                                              {"stage": "Data quality", **context,
                                               "lines": context["provenance"]["dq"]})),
              nbf.code("run", _render(env, "run.py.j2", context))]
    if context["candidates"]:
        cells.append(nbf.md("review-candidates", _render(env, "candidates.md.j2", context)))
    return cells


def build(spec, config, payload: dict, *, candidates, frd_path: Path | None,
          iig_template: str | None, feed_index=None,
          sttm_path: Path | None = None) -> NotebookV2:
    context, flags = build_context(spec, config, payload, candidates=candidates,
                                   frd_path=frd_path, iig_template=iig_template,
                                   feed_index=feed_index, sttm_path=sttm_path)
    cells = render_cells(context)
    ipynb = nbf.ipynb_text(cells)
    source = nbf.databricks_source(cells)
    checks = [nbf.check_nbformat(ipynb), nbf.check_cells_compile(cells),
              nbf.check_ruff(source),
              nbf.check_scrub([ipynb, source], list(config.job.notification_emails))]
    return NotebookV2(cells=cells, ipynb=ipynb, source=source, flags=flags, checks=checks)


def write(notebook: NotebookV2, feed_dir: Path, slug: str) -> list[Path]:
    folder = feed_dir / NOTEBOOK_DIR
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / f"{slug}.ipynb", folder / f"{slug}.py"]
    paths[0].write_text(notebook.ipynb, encoding="utf-8", newline="\n")
    paths[1].write_text(notebook.source, encoding="utf-8", newline="\n")
    return paths


__all__ = ["NOTEBOOK_DIR", "RULES", "NotebookV2", "build", "build_context", "notebook_version",
           "render_cells", "split_list", "write"]
