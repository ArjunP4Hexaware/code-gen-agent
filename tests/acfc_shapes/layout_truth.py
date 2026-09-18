# ruff: noqa: E501  -- curated role tables kept on one line per sheet
"""The correct layout profiles of the M0 fixtures (M2.5 §5), curated by hand.

For every STTM fixture: the roles the synonym tables leave unresolved,
placed by reading the workbook (column numbers, 1-based). For every FRD
fixture: the synonym discovery already resolves every field, so the truth
is that profile. The builder (``scripts/build_layout_profiles.py``) merges
the curated roles onto the synonym profile, asserts nothing stays
unresolved, and materializes ``fixtures/layout_profiles/`` — the repo cache
AND the mock provider's answers. The adversarial set (``mock/``) is derived
from the pair-1 truth with one deliberate wrong claim each.
"""

from __future__ import annotations

# fixture -> {"<sheet>/<layer>/<role>": column}
STTM_CURATED: dict[str, dict[str, int]] = {
    "pair_1_family_a.xlsx": {
        "FEED_1_MAPPING/source/source_type": 5,          # "Format"
        "FEED_1_MAPPING/stage/schema": 18,               # "Target Schema Name in DL"
        "FEED_1_MAPPING/stage/table": 19,                # "Target Table Name in DL"
        "FEED_1_MAPPING/stage/column": 20,               # "Target_Column_Name_in_DL"
        "FEED_1_MAPPING/stage/target_type": 21,          # "Target Data Type in DL"
        "FEED_1_MAPPING/standard/schema": 24,
        "FEED_1_MAPPING/standard/table": 25,
        "FEED_1_MAPPING/standard/column": 26,
        "FEED_1_MAPPING/standard/target_type": 27,
    },
    "pair_8_family_a.xlsx": {
        "FEED_8_LAYOUT/source/field_name": 3,            # "Input File"
        "FEED_8_LAYOUT/source/description": 5,           # "Data Definition"
        "FEED_8_LAYOUT/source/critical": 8,              # "Critical Data"
        "FEED_8_LAYOUT/source/not_null": 9,              # "NOT NULL"
    },
    "pair_2_family_b.xlsx": {},
    "pair_3_family_c.xlsx": {
        "STTM/source/ordinal": 1,                        # "Field #"
    },
    "pair_4_family_d.xlsx": {},
    "pair_6_family_d.xlsx": {},
    "pair_5_family_e.xlsx": {},
    "pair_7_family_e.xlsx": {
        "MAPPING_FEED_7/source/required": 3,             # "Mandatory or Situational"
        "MAPPING_FEED_7/source/source_type": 6,          # "Format"
        "MAPPING_FEED_7/source/length": 7,               # "Size"
        "MAPPING_FEED_7/stage/column": 11,               # "Stage Table - Column Name"
        "MAPPING_FEED_7/stage/target_type": 12,          # "Stage Table - DataType"
        "MAPPING_FEED_7/standard/column": 15,            # "Standard Table - Column Name"
    },
    "pair_9_family_e.xlsx": {
        "MAPPING_FEED_9/source/critical": 12,            # "Critical Data elements"
        "MAPPING_FEED_9_TBL2/source/critical": 12,
    },
    "pair_10_family_e.xlsx": {
        "Outbound_REGION_A/source/field_name": 1,        # "Source Column Name"
        "Outbound_REGION_A/source/pii": 4,               # "PII (Y/N)"
        "Inbound_REGION_A/source/ordinal": 1,            # "Survey Item #"
        "Inbound_REGION_A/source/field_name": 2,         # "Data Field"
        "Inbound_REGION_A/source/pii": 3,                # "PII Y/N"
        "Inbound_REGION_B_Adult/source/ordinal": 1,
        "Inbound_REGION_B_Adult/source/field_name": 2,
        "Inbound_REGION_B_Adult/source/pii": 4,          # "PII Field"
        "Inbound_REGION_B_Child/source/ordinal": 1,
        "Inbound_REGION_B_Child/source/field_name": 2,
        "Inbound_REGION_B_Child/source/pii": 4,
    },
}

FRD_FIXTURES = ["f1_pair_1.docx", "f1_pair_2_variant.docx", "f2_pair_8.docx"]

# VDD fixtures (M3): all three carry the V1/V2/V3 headers verbatim, so the
# synonym tables resolve every role — pinned: no curated roles needed.
VDD_CURATED: dict[str, dict[str, int]] = {
    "pair_1_v1_segments.xlsx": {},
    "pair_2_v2_per_file.xlsx": {},
    "pair_9_v3_per_table.xlsx": {},
}

# Adversarial mock answers (M2.5 §5c), each derived from the pair-1 truth
# with ONE wrong claim; the validator must reject exactly that claim with
# the right reason and keep everything else.
ADVERSARIAL: dict[str, dict] = {
    "adversarial_wrong_header_row.json": {
        "mutation": "header_row",
        "reason_fragment": "header cell at column",
    },
    "adversarial_swapped_spans.json": {
        "mutation": "swap_spans",
        "reason_fragment": "carries no stage token",
    },
    "adversarial_role_at_data_column.json": {
        "mutation": "data_column",
        "reason_fragment": "header cell at column 30 is empty",
    },
    "adversarial_invented_sheet.json": {
        "mutation": "phantom_sheet",
        "reason_fragment": "sheet does not exist",
    },
    "adversarial_free_text_column.json": {
        "mutation": "free_text",
        "reason_fragment": "integer-like",
    },
    "adversarial_canary.json": {
        "mutation": "canary",
        "reason_fragment": "",
    },
}

# VDD adversarial answers (M3), derived from the pair-1 VDD truth.
VDD_ADVERSARIAL: dict[str, dict] = {
    "adversarial_vdd_canary.json": {"mutation": "canary", "reason_fragment": ""},
    "adversarial_vdd_free_text_column.json": {"mutation": "free_text",
                                              "reason_fragment": "integer-like"},
}

CANARY = "CANARY_7f3a9c_MODEL_STRING"
