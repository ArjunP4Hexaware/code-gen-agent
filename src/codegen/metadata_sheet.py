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
    "Layout is a stand-in; the client's metadata template defines the real "
    "tabs and columns. Values carry over."
)
NO_RUN_STATE = "choose an STTM and generate"

BADGE_LABELS = {
    "from_sttm": "from STTM",
    "from_sttm_unmapped": "from STTM (unmapped)",
    "from_frd": "from FRD",
    "synthetic": "SYNTHETIC",
    "needs_template": "NEEDS CLIENT TEMPLATE",
}

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


def _file_layout_row(feed: FrdFeed, config: Config,
                     spec: ResolvedFeedSpec | None) -> dict[str, dict]:
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
        # segments DO state whether a Trailer record exists.
        "has_header": _cell(
            "", "needs_template",
            "no column-header-row indicator exists in the FRD contract",
        ),
        "has_trailer": _cell(
            "yes" if "Trailer" in feed.record_segments else "no", "from_frd"
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
        cells["frequency"] = _cell("", "needs_template", "not stated in the FRD")
    return cells


def _load_config_rows(feed: FrdFeed, config: Config,
                      spec: ResolvedFeedSpec | None) -> list[dict[str, dict]]:
    strategy = config.demo.source_files.load_strategy
    rows: list[dict[str, dict]] = []
    for layer, target, strategy_value in (
        ("stage", feed.stage_target, strategy.stage),
        ("standard", feed.standard_target, strategy.standard),
    ):
        if not target.tables:
            continue  # stage-only feeds declare no standard target
        if layer == "standard" and spec is not None:
            dedup = _cell(
                ", ".join(spec.natural_key_columns), "from_sttm",
                "the mapping contract's natural key columns",
            )
        elif layer == "standard":
            dedup = _cell("", "needs_template",
                          "key columns come from the mapping contract — no run yet")
        else:
            dedup = _cell("", "needs_template",
                          "load-pattern FAQ: dedup_within_file is unanswered")
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


# -- payload ------------------------------------------------------------------- #


def metadata_sheet_payload(
    config: Config,
    base_dir: Path,
    specs: list[ResolvedFeedSpec] | None = None,
    unmapped_by_slug: dict[str, set[str]] | None = None,
    run_label: str | None = None,
) -> dict:
    """The whole preview. ``specs`` (a run's resolved feeds) populate the
    STTM-derived cells; without them the ``columns`` tab is empty with an
    explicit state and STTM-derived cells fall back to needs_template."""
    frd_path = base_dir / config.contracts.dir / config.demo.frd
    if not frd_path.is_file():
        raise FileNotFoundError(f"demo FRD contract not found: {frd_path}")
    contract = FrdContract.model_validate(json.loads(frd_path.read_text(encoding="utf-8")))

    sheet = config.demo.metadata_sheet
    always_blank = set(sheet.always_blank)
    spec_by_id = {s.feed_id: s for s in (specs or [])}
    unmapped_by_slug = unmapped_by_slug or {}

    tabs: dict[str, dict] = {}
    for name, tab in sheet.tabs.items():
        rows: list[dict] = []
        if name == "file_layout":
            for feed in contract.feeds:
                spec = spec_by_id.get(normalize_feed_name(feed.feed_name))
                rows.append(_row(tab.headers, always_blank,
                                 _file_layout_row(feed, config, spec),
                                 feed_slug=normalize_feed_name(feed.feed_name)))
        elif name == "load_config":
            for feed in contract.feeds:
                spec = spec_by_id.get(normalize_feed_name(feed.feed_name))
                for cells in _load_config_rows(feed, config, spec):
                    rows.append(_row(tab.headers, always_blank, cells,
                                     feed_slug=normalize_feed_name(feed.feed_name)))
        elif name == "columns":
            for spec in specs or []:
                unmapped = unmapped_by_slug.get(spec.feed_slug, set())
                for cells, slug in _columns_rows(spec, unmapped):
                    rows.append(_row(tab.headers, always_blank, cells, feed_slug=slug))
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
                if badge in ("from_sttm", "from_sttm_unmapped", "from_frd"):
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
    "synthetic": "FFE699",           # amber
    "needs_template": "D9D9D9",      # grey
}


def build_workbook(payload: dict) -> Workbook:
    """One worksheet per tab + a ``_provenance`` sheet, cells filled by badge."""
    workbook = Workbook()
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


def workbook_bytes(payload: dict) -> bytes:
    """In-memory .xlsx — nothing is written to disk on the serving path."""
    buffer = io.BytesIO()
    build_workbook(payload).save(buffer)
    return buffer.getvalue()


def workbook_filename(payload: dict) -> str:
    return f"metadata_sheet_preview_{payload.get('run_label') or 'pre-run'}.xlsx"
