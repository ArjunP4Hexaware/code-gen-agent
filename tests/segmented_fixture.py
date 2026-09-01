"""Synthetic segmented-workbook golden fixture — CAQH-SHAPED, zero client values.

Builds the layout family the segmented extractor parses (metadata block,
band row, per-row Segment column, per-segment audit rows with empty source
cells, fully populated Standard layer) from purely synthetic vocabulary, so
tests exercise every structural feature without a byte of client material
(the scrub denylist scan runs over it in the suite).

Importable by tests (build in tmp) and runnable to materialize the tracked
golden:  python tests/segmented_fixture.py [out.xlsx]
"""

from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook

FEED_NAME = "Synthetic Segmented Feed"
FEED_SLUG = "synthetic_segmented_feed"
FILE_PATTERN = "YYYYMMDD_syn_segmented_*.txt"

_HEADER_ROW = [
    "#", "Field Name", "Data Type", "Length", "Field Length\n (fixed width)",
    "Start position \n(fixed width)", "End Position\n(fixed width)",
    "Segment\n(Ex:Header,Trailer,Detail)", "PII", "Comments ", "Business Rule",
    # stage block
    "Catalog", "Schema ", "TableName ", "ColumnName ", "DataType",
    "Mandatory \nColumn", "Primary Key", "Field Description",
    "Table Description", "Transformations/Data Quality",
    # standard block
    "Catalog", "Schema ", "TableName ", "ColumnName ", "DataType",
    "Mandatory \nColumn", "Primary Key", "Field Description",
    "Table Description", "Transformations/Data Quality",
]

_BAND_ROW = ["Source Layout"] + [None] * 10 + ["Stage Layer "] + [None] * 9 + [
    "Standard Layer "]


def _data_row(ordinal, field, dtype, segment, pii, comment, rule,
              stage_table, stage_col, mandatory=None, primary_key=None):
    """One mapping row; stage + standard blocks mirror each other."""
    return [
        ordinal, field, dtype, "10", None, None, None, segment, pii, comment,
        rule,
        "SYN_DLK", "STG_SYN ", stage_table, stage_col, "String ",
        mandatory, primary_key, comment, f"Stage table {stage_table}", None,
        "SYN_STD", "SYN ", stage_table, stage_col, "String ",
        None, None, comment, f"Standard table {stage_table}", "Load as is",
    ]


def _audit_row(stage_table, column, dtype):
    return [
        None, None, None, None, None, None, None, None, None, None, None,
        "SYN_DLK", "STG_SYN ", stage_table, column, dtype,
        None, None, None, None, None,
        "SYN_STD", "SYN ", stage_table, column, dtype,
        None, None, None, None, None,
    ]


def build_workbook(*, mandatory_detail_field: bool = False) -> Workbook:
    """The synthetic segmented workbook. ``mandatory_detail_field=True``
    marks one Detail row Mandatory (workbook-signal natural key); the default
    leaves Mandatory/Primary Key empty, mirroring the real workbook's gap."""
    workbook = Workbook()
    ws = workbook.active
    ws.title = "syn_segmented"
    metadata = [
        ("File(s)", FILE_PATTERN),
        ("File Generator", "SyntheticVendor"),
        ("File Location", "landing/inbound/synthetic/segmented"),
        ("LOB", "ALL"),
        ("File frequency", "Weekly"),
        ("Domain", "SYNTHETIC"),
        ("Sub-Domain", "SEGMENTED"),
        ("File type", "txt (pipe delimited |)"),
    ]
    for key, value in metadata:
        ws.append([key, value])
    ws.append(_BAND_ROW)
    ws.append(_HEADER_ROW)

    rows = [
        # Header segment (file envelope)
        _data_row(1, "Format Version", "varchar", "Header", None,
                  "Envelope format version", "Load as is",
                  "EXT_SYN_HDR", "SYN_FMT_VER"),
        _data_row(2, "Extract Date", "varchar", "Header", None,
                  "Date the file was produced", "Must equal file-name date",
                  "EXT_SYN_HDR", "SYN_EXTRACT_DT"),
        # Header audit rows
        _audit_row("EXT_SYN_HDR", "SRC_FILE_NAME", "String "),
        _audit_row("EXT_SYN_HDR", "REC_CREATION_TIME", "timestamp"),
        _audit_row("EXT_SYN_HDR", "REC_UPDATED_TIME", "timestamp"),
        # Detail segment (payload)
        _data_row(1, "Member ID", "varchar", "Detail", "No",
                  "Synthetic member identifier", "Load as is",
                  "EXT_SYN_DTL", "SYN_MEMBER_ID",
                  mandatory="Yes" if mandatory_detail_field else None),
        _data_row(2, "Widget Owner", "varchar", "Detail", "Yes",
                  "Synthetic owner name", "Load as is",
                  "EXT_SYN_DTL", "SYN_WIDGET_OWNER"),
        _data_row(3, "Widget Color", "varchar", "Detail", "No",
                  "Synthetic color", "Load as is",
                  "EXT_SYN_DTL", "SYN_WIDGET_COLOR"),
        # Detail audit rows
        _audit_row("EXT_SYN_DTL", "LOB", "String "),
        _audit_row("EXT_SYN_DTL", "FILE_TYPE", "String "),
        _audit_row("EXT_SYN_DTL", "SRC_FILE_NAME", "String "),
        _audit_row("EXT_SYN_DTL", "REC_CREATION_TIME", "timestamp"),
        _audit_row("EXT_SYN_DTL", "REC_UPDATED_TIME", "timestamp"),
        # Trailer segment — row 1 states the static record-type marker the
        # way the real workbook does (identification derives from this cell).
        _data_row(1, "Record Type", "varchar", "Trailer", None,
                  "Static text identifying the record as the trailer record.\n"
                  "Contains the value ******",
                  "Load as is",
                  "EXT_SYN_TRL", "SYN_REC_TYPE"),
        _data_row(2, "Record Count", "Numeric", "Trailer", None,
                  "Number of Detail records in the file",
                  "Must equal the Detail row count",
                  "EXT_SYN_TRL", "SYN_REC_CNT"),
        # Trailer audit rows
        _audit_row("EXT_SYN_TRL", "SRC_FILE_NAME", "String "),
        _audit_row("EXT_SYN_TRL", "REC_CREATION_TIME", "timestamp"),
        _audit_row("EXT_SYN_TRL", "REC_UPDATED_TIME", "timestamp"),
    ]
    for row in rows:
        ws.append(row)
    return workbook


def frd_contract_dict() -> dict:
    """The paired synthetic FRD contract: segmented, both layers scoped by
    Load Strategy (STG truncate / STD append) with the Target Schema block
    naming stage targets only — the STD schema comes from the STTM, like the
    real CAQH pair. No keys anywhere (no MERGE)."""
    return {
        "contract_name": "synthetic segmented FRD",
        "generated_from_frd": "synthetic.docx",
        "generated_date": "2026-01-01T00:00:00",
        "generator": "test",
        "status": "PASS",
        "project": {"project_id": None, "project_name": "syn",
                    "business_context_summary": None},
        "in_scope": [],
        "out_of_scope": [],
        "assumptions_constraints_dependencies": [],
        "feeds": [{
            "feed_name": FEED_NAME,
            "source_system": "SyntheticVendor",
            "file_name_patterns": [FILE_PATTERN.replace("YYYY", "CCYY")],
            "file_format": "txt",
            "delimiter": "|",
            "record_segments": ["Header", "Detail", "Trailer"],
            "frequency": "Weekly",
            "load_windows_sla": [],
            "lobs": ["ALL"],
            "domain": "Synthetic",
            "sub_domain": "Segmented",
            "landing_location": "landing/inbound/synthetic/segmented",
            "stage_target": {
                "catalog": "SYN_DLK", "schema": "STG_SYN",
                "tables": ["EXT_SYN_HDR", "EXT_SYN_DTL", "EXT_SYN_TRL",
                           "EXT_SYN_DTL_RECYCLE"],
                "load_strategy": "Truncate and Load",
            },
            "standard_target": {
                "catalog": None, "schema": None, "tables": [],
                "load_strategy": "Append",
            },
            "validation_rules": [
                "Process shall fail when file layout is not as per source dictionary.",
                "Files are pipe delimited and contain incremental changes.",
                "Member ID validation should be performed against Facets for existence.",
                "Process should load the files AS-IS after Member ID validation "
                "and should not perform any data transformation while loading.",
                "Synthetic free-text rule the compiler cannot classify.",
            ],
            "recycle_rule": "Invalid records will be moved to Recycle table, "
                            "retained for 15 days.",
            "history_backfill": None,
            "archive_retention": None,
            "phi_pii_notes": None,
            "sttm_reference": None,
            "requirement_ids": [],
        }],
        "system_interfaces": [],
        "open_items": [],
    }


# FAQ override declarations for the override tests: identification is
# document-derived by default; an override requires status "confirmed".
FAQ_OVERRIDE_CONFIRMED = """\
record_type_discriminators:
  header: "H"
  detail: "D"
  trailer: "T"
  status: confirmed
"""

FAQ_OVERRIDE_ASSUMED = FAQ_OVERRIDE_CONFIRMED.replace(
    "confirmed", "assumed_pending_source_team")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "fixtures/workbooks/synthetic_segmented_golden.xlsx")
    out.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, "src")
    from codegen.metadata_sheet import stable_workbook_bytes

    out.write_bytes(stable_workbook_bytes(build_workbook()))
    print(f"wrote {out}")
