"""Metadata-sheet preview for ACFC's metadata-driven framework — DISPLAY ONLY.

ACFC's position (Nikshit, 2026-08-25) is that the agent's real output for
their framework is a reviewable metadata Excel — approved by a human, then
inserted through their existing metadata path — not per-feed notebooks.
This module renders that preview: the same facts the generator already
resolves, laid out as the sheet a reviewer would approve. Nothing here is
consumed by generation; ``resolve → rules → reasoning → emit → gate`` is
untouched and the live run stays byte-identical.

Every cell carries exactly one provenance badge, in this priority:

- ``from_sttm`` (light green)  — read from the mapping contract
- ``from_frd`` (light blue)    — read from the FRD feed contract
- ``synthetic`` (amber)        — Part A stand-in values, same tooltip
                                 convention as the source-files panel
- ``needs_template`` (grey)    — unknowable until the client's metadata
                                 template / IG sheet arrives, or assigned
                                 by the client's framework by design

The tab names and column headers are OUR guess at the client's template
(``demo.metadata_sheet`` in config); the payload's ``layout_note`` says so.
The agent refuses to guess: anything the documents don't state is left
blank and flagged, never filled in.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from codegen.config import Config
from codegen.contracts.frd import FrdContract, FrdFeed
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.demo_sources import feed_source_files
from codegen.resolve.resolver import normalize_feed_name

LAYOUT_NOTE = (
    "Layout is the client IIG template (anonymized reference — "
    "fixtures/reference/SFMC_IIG.xlsx). Values carry over."
)
NO_RUN_STATE = "choose an STTM and generate"

BADGE_LABELS = {
    "from_sttm": "from STTM",
    "from_sttm_unmapped": "from STTM (unmapped)",
    "from_frd": "from FRD",
    # The load-pattern FAQ is an INPUT (three-input model), not a guess:
    # an engineer-answered value fills cells the FRD cannot.
    "from_faq": "from FAQ",
    # Engineering standards (three-input model, input #2) — e.g. the EDO
    # WF_/NB_ naming patterns and the prod-support alert DL.
    "from_standards": "from standards",
    "synthetic": "SYNTHETIC",
    "needs_template": "NEEDS CLIENT TEMPLATE",
}

# Badges that count as "derived" in coverage (everything traceable to an
# input document/answer, as opposed to synthetic stand-ins or blanks).
DERIVED_BADGES = ("from_sttm", "from_sttm_unmapped", "from_frd", "from_faq",
                  "from_standards")

_ALWAYS_BLANK_TOOLTIP = (
    "assigned by the ACFC framework / manual by client instruction — "
    "the agent leaves it blank and flags it."
)
_LOAD_STRATEGY_TOOLTIP = (
    "the real FRD states this under Structural Metadata → Load Strategy; "
    "this build carries a config stand-in."
)
_LANDING_TOOLTIP = (
    "The real FRD states this under Structural Metadata → ADLS Location; "
    "this build carries an anonymized stand-in."
)


def _cell(value, badge: str, tooltip: str | None = None) -> dict:
    entry: dict = {"badge": badge}
    if tooltip:
        entry["tooltip"] = tooltip
    return {"value": "" if value is None else value, "badge_entry": entry}


def _row(headers: list[str], always_blank: set[str], cells: dict[str, dict],
         **extra) -> dict:
    """Assemble one row: every configured header gets a value + one badge."""
    values: dict = {}
    badges: dict = {}
    for header in headers:
        if header in always_blank:
            cell = _cell("", "needs_template", _ALWAYS_BLANK_TOOLTIP)
        else:
            cell = cells.get(header) or _cell("", "needs_template", None)
        values[header] = cell["value"]
        badges[header] = cell["badge_entry"]
    return {"values": values, "badges": badges, **extra}


# -- per-tab row builders ------------------------------------------------------ #


def _faq_cell(answer, tooltip_prefix: str):
    """A from-FAQ cell when the engineer (or a prefill) answered; else None."""
    if answer is None or answer.source == "unknown":
        return None
    tooltip = f"{tooltip_prefix} (source: {answer.source}"
    if answer.evidence:
        tooltip += f'; evidence: "{answer.evidence}"'
    return _cell(answer.value, "from_faq", tooltip + ")")


def _file_layout_row(feed: FrdFeed, config: Config,
                     spec: ResolvedFeedSpec | None, faq=None) -> dict[str, dict]:
    source = feed_source_files(feed, config)  # Part A's synthesis rules, reused
    landing = source["landing_root"]
    cells = {
        "feed_name": _cell(feed.feed_name, "from_frd"),
        "source_system": _cell(feed.source_system, "from_frd"),
        "landing_path": _cell(
            landing["value"],
            "synthetic" if landing["synthetic"] else "from_frd",
            _LANDING_TOOLTIP if landing["synthetic"] else None,
        ),
        "file_pattern": _cell("; ".join(feed.file_name_patterns), "from_frd"),
        "file_format": _cell(feed.file_format, "from_frd"),
        # The FRD template has no column-header-row indicator; record
        # segments DO state whether a Trailer record exists. The load-pattern
        # FAQ (an input, not a guess) fills what the FRD lacks.
        "has_header": _faq_cell(getattr(faq, "has_header", None),
                                "load-pattern FAQ answer")
        or _cell(
            "", "needs_template",
            "no column-header-row indicator exists in the FRD contract",
        ),
        "has_trailer": (
            _cell("yes", "from_frd")
            if "Trailer" in feed.record_segments
            else _faq_cell(getattr(faq, "has_trailer", None),
                           "load-pattern FAQ answer")
            or _cell("no", "from_frd")
        ),
    }
    if feed.delimiter:
        cells["delimiter"] = _cell(feed.delimiter, "from_frd")
    elif spec is not None:
        # Not stated in the FRD; the resolver reconciled it from the STTM.
        cells["delimiter"] = _cell(spec.delimiter, "from_sttm")
    else:
        cells["delimiter"] = _cell(
            "", "needs_template",
            "not stated in the FRD; reconciled from the STTM at generation time",
        )
    if feed.frequency:
        cells["frequency"] = _cell(feed.frequency, "from_frd")
    else:
        cells["frequency"] = (
            _faq_cell(getattr(faq, "load_frequency", None),
                      "load-pattern FAQ answer")
            or _cell("", "needs_template", "not stated in the FRD")
        )
    return cells


def _load_config_rows(feed: FrdFeed, config: Config,
                      spec: ResolvedFeedSpec | None,
                      faq=None) -> list[dict[str, dict]]:
    strategy = config.demo.source_files.load_strategy
    rows: list[dict[str, dict]] = []
    for layer, target, strategy_value in (
        ("stage", feed.stage_target, strategy.stage),
        ("standard", feed.standard_target, strategy.standard),
    ):
        if not target.tables:
            continue  # stage-only feeds declare no standard target
        faq_keys = ", ".join(getattr(faq, "dedup_keys", []) or [])
        if layer == "standard" and spec is not None:
            dedup = _cell(
                ", ".join(spec.natural_key_columns), "from_sttm",
                "the mapping contract's natural key columns",
            )
        elif layer == "standard" and faq_keys:
            dedup = _cell(faq_keys, "from_faq", "load-pattern FAQ dedup_keys")
        elif layer == "standard":
            dedup = _cell("", "needs_template",
                          "key columns come from the mapping contract — no run yet")
        else:
            dedup = (
                _faq_cell(getattr(faq, "dedup_within_file", None),
                          "load-pattern FAQ answer")
                or _cell("", "needs_template",
                         "load-pattern FAQ: dedup_within_file is unanswered")
            )
        rows.append({
            "layer": _cell(layer, "from_frd"),
            "target_schema": _cell(target.schema_name, "from_frd"),
            "target_table": _cell(", ".join(target.tables), "from_frd"),
            "load_strategy": _cell(strategy_value, "synthetic", _LOAD_STRATEGY_TOOLTIP),
            "dedup_keys": dedup,
        })
    return rows


def _columns_rows(spec: ResolvedFeedSpec,
                  unmapped_rule_texts: set[str]) -> list[tuple[dict[str, dict], str]]:
    """(cells, feed_slug) per mapped column, workbook ordinal preserved."""
    rows: list[tuple[dict[str, dict], str]] = []
    ordinal = 0
    for segment in spec.segments:
        for field in segment.fields:
            ordinal += 1
            if field.value_spec and field.value_spec in unmapped_rule_texts:
                # Routed to Layer 2: badge says so; the model's candidate
                # text is NEVER used to fill the cell.
                transformation = _cell(field.value_spec, "from_sttm_unmapped",
                                       "routed to Layer-2 review; shown verbatim "
                                       "from the STTM, never from the model")
            else:
                transformation = _cell(field.value_spec or "", "from_sttm")
            rows.append((
                {
                    "ordinal": _cell(ordinal, "from_sttm"),
                    "column_name": _cell(field.stage_column, "from_sttm"),
                    "data_type": _cell(field.stage_datatype, "from_sttm"),
                    "nullable": _cell("yes" if field.nullable else "no", "from_sttm"),
                    "source_column": _cell(field.source_column, "from_sttm"),
                    "transformation": transformation,
                },
                spec.feed_slug,
            ))
    return rows


# -- IIG-layout row builders --------------------------------------------------- #
# The real client layout (demo.metadata_sheet sourced from the anonymized
# fixtures/reference/SFMC_IIG.xlsx). Existing derivations map onto the real
# columns; anything the inputs don't state stays blank + needs_template, and
# framework-assigned IDs stay always_blank — honest coverage by design.

_SYNTHETIC_PATH_TOOLTIP = (
    "synthetic path shape (from the anonymized reference workbook); the real "
    "container/path are assigned at deployment"
)
_FRAMEWORK_VOCAB_TOOLTIP = (
    "framework vocabulary from the anonymized reference workbook — confirm "
    "with the framework team"
)


def _frequency_cell(feed: FrdFeed, faq):
    if feed.frequency:
        return _cell(feed.frequency, "from_frd")
    return (_faq_cell(getattr(faq, "load_frequency", None),
                      "load-pattern FAQ answer")
            or _cell("", "needs_template", "not stated in the FRD"))


def _standards_name_cell(config: Config, feed: FrdFeed, slug: str, faq,
                         kind: str):
    """WF_/NB_ name from the engineering-standards patterns (input #2)."""
    if faq is None:
        return None
    from codegen.emit.context import resolve_job_name, resolve_notebook_name

    builder = resolve_job_name if kind == "job" else resolve_notebook_name
    name = builder(config.engineering_standards, faq, slug,
                   source=feed.source_system, domain=feed.domain,
                   sub_domain=feed.sub_domain, lobs=feed.lobs)
    if not name:
        return None
    return _cell(name, "from_standards",
                 "EDO naming standard pattern applied to FRD facts")


def _landing_cells(feed: FrdFeed, config: Config) -> tuple[dict, dict]:
    """(SRC_CONTAINER_NAME, SRC_ADLS_PATH) from the FRD landing convention."""
    landing = feed_source_files(feed, config)["landing_root"]
    value = str(landing["value"]).replace("\\", "/").strip("/")
    container, _, rest = value.partition("/")
    badge = "synthetic" if landing["synthetic"] else "from_frd"
    tooltip = _LANDING_TOOLTIP if landing["synthetic"] else None
    return (_cell(container, badge, tooltip),
            _cell("/" + rest if rest else "/", badge, tooltip))


def _stage_names(feed: FrdFeed, spec: ResolvedFeedSpec | None):
    """(schema, table) of the stage target — resolved spec preferred."""
    if spec is not None:
        table = spec.detail_segment.stage_table
        return table.schema_name, table.table
    target = feed.stage_target
    return target.schema_name, ", ".join(target.tables or [])


def _adls_delta_row(feed: FrdFeed, config: Config, spec, faq,
                    unmapped: set[str]) -> dict[str, dict]:
    container, src_path = _landing_cells(feed, config)
    stage_schema, stage_table = _stage_names(feed, spec)
    cells = {
        "OBJECT_NAME": _cell(feed.feed_name, "from_frd"),
        "DOMAIN": _cell(feed.domain or "", "from_frd"),
        "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
        "SOURCE": _cell(feed.source_system, "from_frd"),
        "FREQUENCY": _frequency_cell(feed, faq),
        "LOB": _cell(", ".join(feed.lobs), "from_frd"),
        "SRC_CONTAINER_NAME": container,
        "SRC_ADLS_PATH": src_path,
        "SRC_FILE_NAME": _cell("; ".join(feed.file_name_patterns), "from_frd"),
        "SRC_FORMAT": _cell(feed.file_format, "from_frd"),
        "TGT_DATABASE_NAME": _cell(stage_schema, "from_frd"),
        "TGT_TABLE_NAME": _cell(stage_table, "from_frd"),
        "TGT_FORMAT": _cell("delta", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
        "TGT_LOAD_OPTION": _cell(
            config.demo.source_files.load_strategy.stage, "synthetic",
            _LOAD_STRATEGY_TOOLTIP),
        "HEADER_FLAG": (_faq_cell(getattr(faq, "has_header", None),
                                  "load-pattern FAQ answer")
                        or _cell("", "needs_template",
                                 "no header indicator in the FRD contract")),
    }
    if feed.delimiter:
        cells["SRC_FILE_DELIMITER"] = _cell(feed.delimiter, "from_frd")
    elif spec is not None:
        cells["SRC_FILE_DELIMITER"] = _cell(spec.delimiter, "from_sttm")
    if spec is not None:
        fields = [f for seg in spec.segments for f in seg.fields]
        cells["SRC_COLUMNS"] = _cell(
            ",".join(f"{f.source_column}:{f.stage_column}" for f in fields),
            "from_sttm")
        cells["SRC_DATA_TYPE"] = _cell(
            ",".join(f"{f.source_datatype}:{f.stage_datatype}" for f in fields),
            "from_sttm")
        cells["TGT_COLUMN_NAMES"] = _cell(
            ",".join(f.stage_column for f in fields), "from_sttm")
        cells["TGT_DATA_TYPE"] = _cell(
            ",".join(f.stage_datatype for f in fields), "from_sttm")
        cells["MANDATORY_FIELD_LIST"] = _cell(
            ",".join(spec.not_null_columns), "from_sttm")
        cells["TGT_PRIMARY_KEY"] = _cell(
            ",".join(spec.natural_key_columns), "from_sttm",
            "the mapping contract's natural key columns")
        cells["TGT_RJT_TABLE_NAME"] = _cell(
            spec.errors_table.table, "from_sttm",
            "stage table + configured errors suffix")
        cells["RECYCL_ENBL_FLG"] = _cell(
            "Y" if spec.recycle else "N", "from_frd")
        if spec.recycle:
            cells["RECYCL_TBL_NM"] = _cell(
                spec.recycle.recycle_table.table, "from_frd")
            cells["RECYCL_RETN_DAYS"] = _cell(
                spec.recycle.spec.recycle_window_days, "from_sttm")
        tgt_path = f"/{feed.domain or ''}/{feed.sub_domain or ''}/Processed/{stage_table}"
        cells["TGT_ADLS_PATH"] = _cell(tgt_path.replace("//", "/"),
                                       "synthetic", _SYNTHETIC_PATH_TOOLTIP)
    return cells


def _stg_std_row(feed: FrdFeed, config: Config, spec, faq,
                 unmapped: set[str]) -> list[dict[str, dict]]:
    if spec is None or spec.standard_table is None:
        return []
    stage_schema, stage_table = _stage_names(feed, spec)
    standard = spec.standard_table
    fields = [f for seg in spec.segments for f in seg.fields
              if f.standard_column]
    cells = {
        "OBJECT_NAME": _cell(feed.feed_name, "from_frd"),
        "DOMAIN": _cell(feed.domain or "", "from_frd"),
        "SUBDOMAIN": _cell(feed.sub_domain or "", "from_frd"),
        "SOURCE": _cell(feed.source_system, "from_frd"),
        "FREQUENCY": _frequency_cell(feed, faq),
        "LOB": _cell(", ".join(feed.lobs), "from_frd"),
        "SRC_CATALOG_NAME": _cell(
            spec.detail_segment.stage_table.catalog or "", "from_frd"),
        "SRC_SCHEMA_NAME": _cell(stage_schema, "from_frd"),
        "SRC_TABLE_NAME": _cell(stage_table, "from_frd"),
        "SRC_FORMAT": _cell("delta", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
        "SRC_COLUMNS": _cell(
            ",".join(f"{f.stage_column}:{f.standard_column}" for f in fields),
            "from_sttm"),
        "SRC_DATA_TYPE": _cell(
            ",".join(f"{f.stage_datatype}:{f.standard_datatype}" for f in fields),
            "from_sttm"),
        "TGT_CATALOG_NAME": _cell(standard.catalog or "", "from_frd"),
        "TGT_SCHEMA_NAME": _cell(standard.schema_name, "from_frd"),
        "TGT_TABLE_NAME": _cell(standard.table, "from_frd"),
        "TGT_FORMAT": _cell("delta", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
        "TGT_COLUMN_NAMES": _cell(
            ",".join(f.standard_column for f in fields), "from_sttm"),
        "TGT_DATA_TYPE": _cell(
            ",".join(f.standard_datatype or "" for f in fields), "from_sttm"),
        "TGT_LOAD_OPTION": _cell(
            spec.standard_load_strategy or
            config.demo.source_files.load_strategy.standard,
            "from_frd" if spec.standard_load_strategy else "synthetic",
            None if spec.standard_load_strategy else _LOAD_STRATEGY_TOOLTIP),
        "TGT_PRIMARY_KEY": _cell(
            ",".join(spec.natural_key_columns), "from_sttm",
            "the mapping contract's natural key columns"),
    }
    return [cells]


def _pipeline_schedule_rows(feed: FrdFeed, config: Config, spec, faq,
                            unmapped: set[str]) -> list[dict[str, dict]]:
    slug = normalize_feed_name(feed.feed_name)
    name_cell = _standards_name_cell(config, feed, slug, faq, "job")
    rows = []
    layers = ["STAGE"]
    if (spec is not None and spec.standard_table is not None) or (
            spec is None and feed.standard_target.tables):
        layers.append("STANDARD")
    for layer in layers:
        cells = {
            "PIPELINE_DESCRIPTION": _cell(
                f"{feed.feed_name} ingestion ({layer.lower()})", "from_frd"),
            "PIPELINE_FREQUENCY": _frequency_cell(feed, faq),
            "APPLICATION_NAME": _cell(feed.source_system, "from_frd"),
            "PROCESS_NAME": _cell(feed.feed_name, "from_frd"),
            "LAYER_NAME": _cell(layer, "from_frd"),
            "ACTIVE_FLAG": _cell("Y", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "ACTIVE_END_DATE": _cell("9999-12-31", "synthetic",
                                     _FRAMEWORK_VOCAB_TOOLTIP),
        }
        if name_cell:
            cells["PIPELINE_NAME"] = name_cell
        rows.append(cells)
    return rows


def _dq_rules_rows(feed: FrdFeed, config: Config, spec, faq,
                   unmapped: set[str]) -> list[dict[str, dict]]:
    if spec is None:
        return []
    rows = []
    if spec.not_null_columns:
        joined = ",".join(spec.not_null_columns)
        rows.append({
            "SEQUENCE_NO": _cell(1, "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "RULE_TYPE": _cell("Predefined", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "RULE_CLASS": _cell("CheckRule", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "ACTIVE_RULE_FLG": _cell("Y", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "SOURCE_COLUMN": _cell(joined, "from_sttm",
                                   "the mapping contract's not-null columns"),
            "TARGET_COLUMN": _cell(joined, "from_sttm",
                                   "the mapping contract's not-null columns"),
        })
    if spec.standard_table is not None:
        fields = [f.standard_column for seg in spec.segments
                  for f in seg.fields if f.standard_column]
        joined = ",".join(fields)
        rows.append({
            "SEQUENCE_NO": _cell(len(rows) + 1, "synthetic",
                                 _FRAMEWORK_VOCAB_TOOLTIP),
            "RULE_TYPE": _cell("STDDelta", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "RULE_CLASS": _cell("LRTrimRule", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "ACTIVE_RULE_FLG": _cell("Y", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "SOURCE_COLUMN": _cell(joined, "from_sttm",
                                   "the mapping contract's standard columns"),
            "TARGET_COLUMN": _cell(joined, "from_sttm",
                                   "the mapping contract's standard columns"),
        })
    return rows


def _notebook_details_rows(feed: FrdFeed, config: Config, spec, faq,
                           unmapped: set[str]) -> list[dict[str, dict]]:
    slug = normalize_feed_name(feed.feed_name)
    job_cell = _standards_name_cell(config, feed, slug, faq, "job")
    notebook_cell = _standards_name_cell(config, feed, slug, faq, "notebook")
    strategy = config.demo.source_files.load_strategy
    rows = []
    layers = [("STAGE", strategy.stage)]
    if (spec is not None and spec.standard_table is not None) or (
            spec is None and feed.standard_target.tables):
        refresh = (spec.standard_load_strategy if spec else None) or strategy.standard
        layers.append(("STANDARD", refresh))
    for index, (layer, refresh) in enumerate(layers, start=1):
        cells = {
            "SEQ_NM": _cell(index, "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "PROCESS_NAME": _cell(
                f"{layer.capitalize()} Load for {feed.feed_name}", "from_frd"),
            "TGT_REFRESH_TYPE": _cell(refresh, "synthetic",
                                      _LOAD_STRATEGY_TOOLTIP),
            "ACTIVE_FLAG": _cell("Y", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
        }
        if job_cell:
            cells["PIPELINE_NAME"] = job_cell
        if notebook_cell:
            cells["DATABRICKS_NOTEBOOK_NAME"] = notebook_cell
        rows.append(cells)
    return rows


def _email_template_rows(feed: FrdFeed, config: Config, spec, faq,
                         unmapped: set[str]) -> list[dict[str, dict]]:
    recipients = ";".join(config.job.notification_emails)
    rows = []
    for status in ("Success", "Failed"):
        rows.append({
            "TEMPLATE_NAME": _cell(feed.feed_name, "from_frd"),
            "PROCESS_NAME": _cell(feed.feed_name, "from_frd"),
            "STATUS": _cell(status, "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "ACTIVE_FLAG": _cell("Y", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
            "SUBJECT": _cell(f"{feed.feed_name} Load {status}", "synthetic",
                             _FRAMEWORK_VOCAB_TOOLTIP),
            "EMAIL_TO": _cell(
                recipients, "from_standards",
                "EDO coding standard: success AND failure alerts to the "
                "prod-support DL (synthetic stand-in address)"),
        })
    return rows


def _static_information_rows(feed: FrdFeed, config: Config, spec, faq,
                             unmapped: set[str]) -> list[dict[str, dict]]:
    return [{
        "FILE_NAME": _cell("; ".join(feed.file_name_patterns), "from_frd"),
        "DESCRIPTION": _cell(feed.feed_name, "from_frd"),
        "LOB": _cell(", ".join(feed.lobs), "from_frd"),
        "FILE_TYPE": _cell(feed.file_format, "from_frd"),
        "SUPPLIER": _cell(feed.source_system, "from_frd"),
        "vendor_name": _cell(feed.source_system, "from_frd"),
        "FREQUENCY": _frequency_cell(feed, faq),
        "ACTIVE_TERM_STATUS": _cell("Y", "synthetic", _FRAMEWORK_VOCAB_TOOLTIP),
        "PROCESS_NAME": _cell(feed.feed_name, "from_frd"),
        "domain": _cell(feed.domain or "", "from_frd"),
        "subdomain": _cell(feed.sub_domain or "", "from_frd"),
    }]


def _adls_delta_rows(feed, config, spec, faq, unmapped):
    return [_adls_delta_row(feed, config, spec, faq, unmapped)]


# tab name (verbatim from the client IIG workbook) -> row builder
_IIG_TAB_BUILDERS = {
    "DATA_FACTORY_PIPELINE_SCHEDULE": _pipeline_schedule_rows,
    "ADLS_DELTA_INGESTION_DETAILS": _adls_delta_rows,
    "STGDELTA_STDDELTA_INGESTION_DET": _stg_std_row,
    "DATA_QUALITY_RULES": _dq_rules_rows,
    "DATABRICKS_NOTEBOOK_DETAILS": _notebook_details_rows,
    "EMAIL_TEMPLATE_CONFIG": _email_template_rows,
    "ALL_FILES_STATIC_INFORMATION": _static_information_rows,
}


# -- payload ------------------------------------------------------------------- #


def metadata_sheet_payload(
    config: Config,
    base_dir: Path,
    specs: list[ResolvedFeedSpec] | None = None,
    unmapped_by_slug: dict[str, set[str]] | None = None,
    run_label: str | None = None,
    faq_by_slug: dict | None = None,
    frd_path: Path | None = None,
) -> dict:
    """The whole preview. ``specs`` (a run's resolved feeds) populate the
    STTM-derived cells; without them the ``columns`` tab is empty with an
    explicit state and STTM-derived cells fall back to needs_template."""
    if frd_path is None:
        frd_path = base_dir / config.contracts.dir / config.demo.frd
    if not frd_path.is_file():
        raise FileNotFoundError(f"demo FRD contract not found: {frd_path}")
    contract = FrdContract.model_validate(json.loads(frd_path.read_text(encoding="utf-8")))

    sheet = config.demo.metadata_sheet
    always_blank = set(sheet.always_blank)
    spec_by_id = {s.feed_id: s for s in (specs or [])}
    unmapped_by_slug = unmapped_by_slug or {}
    faq_by_slug = faq_by_slug or {}

    tabs: dict[str, dict] = {}
    for name, tab in sheet.tabs.items():
        rows: list[dict] = []
        if name == "file_layout":
            for feed in contract.feeds:
                slug = normalize_feed_name(feed.feed_name)
                spec = spec_by_id.get(slug)
                rows.append(_row(tab.headers, always_blank,
                                 _file_layout_row(feed, config, spec,
                                                  faq=faq_by_slug.get(slug)),
                                 feed_slug=slug))
        elif name == "load_config":
            for feed in contract.feeds:
                slug = normalize_feed_name(feed.feed_name)
                spec = spec_by_id.get(slug)
                for cells in _load_config_rows(feed, config, spec,
                                               faq=faq_by_slug.get(slug)):
                    rows.append(_row(tab.headers, always_blank, cells,
                                     feed_slug=slug))
        elif name == "columns":
            for spec in specs or []:
                unmapped = unmapped_by_slug.get(spec.feed_slug, set())
                for cells, slug in _columns_rows(spec, unmapped):
                    rows.append(_row(tab.headers, always_blank, cells, feed_slug=slug))
        elif name in _IIG_TAB_BUILDERS:
            builder = _IIG_TAB_BUILDERS[name]
            for feed in contract.feeds:
                slug = normalize_feed_name(feed.feed_name)
                spec = spec_by_id.get(slug)
                unmapped = unmapped_by_slug.get(slug, set())
                for cells in builder(feed, config, spec,
                                     faq_by_slug.get(slug), unmapped):
                    rows.append(_row(tab.headers, always_blank, cells,
                                     feed_slug=slug))
        entry: dict = {"headers": list(tab.headers), "rows": rows}
        if name == "columns" and not specs:
            entry["state"] = NO_RUN_STATE
        tabs[name] = entry

    derived = synthetic = needs_template = total = 0
    for tab in tabs.values():
        for row in tab["rows"]:
            for entry in row["badges"].values():
                total += 1
                badge = entry["badge"]
                if badge in DERIVED_BADGES:
                    derived += 1
                elif badge == "synthetic":
                    synthetic += 1
                else:
                    needs_template += 1

    return {
        "layout_note": LAYOUT_NOTE,
        "run_label": run_label,
        "tabs": tabs,
        "coverage": {
            "derived": derived,
            "synthetic": synthetic,
            "needs_template": needs_template,
            "total": total,
        },
    }


# -- xlsx export --------------------------------------------------------------- #

_BADGE_FILLS = {
    "from_sttm": "C6EFCE",           # light green
    "from_sttm_unmapped": "C6EFCE",  # light green (same family)
    "from_frd": "DDEBF7",            # light blue
    "from_faq": "E4DFEC",            # light purple — engineer-answered input
    "from_standards": "CCECE6",      # light teal — EDO standards input
    "synthetic": "FFE699",           # amber
    "needs_template": "D9D9D9",      # grey
}


def _pin_workbook_properties(workbook: Workbook) -> None:
    """Byte-stable output doctrine: no wall-clock timestamps in artefacts."""
    from datetime import datetime

    fixed = datetime(2026, 1, 1)
    workbook.properties.created = fixed
    workbook.properties.modified = fixed


def build_workbook(payload: dict) -> Workbook:
    """One worksheet per tab + a ``_provenance`` sheet, cells filled by badge."""
    workbook = Workbook()
    _pin_workbook_properties(workbook)
    workbook.remove(workbook.active)
    provenance_rows: list[tuple] = []

    for tab_name, tab in payload["tabs"].items():
        sheet = workbook.create_sheet(title=tab_name)
        headers = tab["headers"]
        sheet.append(headers)
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for row_index, row in enumerate(tab["rows"], start=2):
            sheet.append([row["values"][h] for h in headers])
            for col_index, header in enumerate(headers, start=1):
                entry = row["badges"][header]
                badge = entry["badge"]
                sheet.cell(row=row_index, column=col_index).fill = PatternFill(
                    start_color=_BADGE_FILLS[badge],
                    end_color=_BADGE_FILLS[badge],
                    fill_type="solid",
                )
                provenance_rows.append((
                    tab_name, row_index, header,
                    BADGE_LABELS[badge], entry.get("tooltip", ""),
                ))

    provenance = workbook.create_sheet(title="_provenance")
    provenance.append(["tab", "row", "header", "badge", "tooltip"])
    for cell in provenance[1]:
        cell.font = Font(bold=True)
    for entry in provenance_rows:
        provenance.append(list(entry))
    return workbook


def stable_workbook_bytes(workbook: Workbook) -> bytes:
    """Byte-stable .xlsx serialization (repo doctrine: no wall-clock in
    artefacts). openpyxl stamps ``modified`` and the zip member headers with
    now() at save time; this rewrites both to a fixed instant so the same
    workbook always serializes to the same bytes."""
    import re
    import zipfile

    buffer = io.BytesIO()
    workbook.save(buffer)
    source = zipfile.ZipFile(io.BytesIO(buffer.getvalue()))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as destination:
        for info in source.infolist():
            data = source.read(info.filename)
            if info.filename == "docProps/core.xml":
                data = re.sub(
                    rb"<dcterms:modified[^>]*>[^<]*</dcterms:modified>",
                    b'<dcterms:modified xsi:type="dcterms:W3CDTF">'
                    b"2026-01-01T00:00:00Z</dcterms:modified>",
                    data,
                )
            pinned = zipfile.ZipInfo(info.filename, date_time=(2026, 1, 1, 0, 0, 0))
            pinned.compress_type = zipfile.ZIP_DEFLATED
            pinned.external_attr = info.external_attr
            destination.writestr(pinned, data)
    return out.getvalue()


def workbook_bytes(payload: dict) -> bytes:
    """In-memory .xlsx — nothing is written to disk on the serving path."""
    return stable_workbook_bytes(build_workbook(payload))


def workbook_filename(payload: dict) -> str:
    return f"metadata_sheet_preview_{payload.get('run_label') or 'pre-run'}.xlsx"
