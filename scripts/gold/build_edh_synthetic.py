# ruff: noqa: E501  (the fabricated cell texts are kept on one line each)
"""Write the synthetic EDH E2E gold-mapping fixture set (tests/fixtures/edh_gold_synthetic/).

    python scripts/gold/build_edh_synthetic.py [OUT_DIR]

Dialect v2.2 (extractor_version 2.2.0): every mapping row carries the same 15 keys, among them
``block_index`` and ``source_row``; every table file carries ``document_notes``. Every name is
SYN_-prefixed and every value fabricated; only the structure and cardinalities follow the real
set (docs/acfc/EDH_E2E_JSON_SCHEMA.md §5). Each file's ``$comment`` names the
real-set counts it stands in for. Deterministic: tests/test_gold_profiler.py rebuilds the set
and compares it byte for byte with the tracked files.
"""

import hashlib
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "edh_gold_synthetic"
STAMP = "2026-10-20T00:00:00.000000+00:00"
EXTRACTOR_VERSION = "2.2.0"

REGION_SHAPES = [  # (label, code count, space before paren) — the real set's seven shapes
    ("SYNR1", 9, True),
    ("SYNR2", 3, True),
    ("SYNR5", 2, False),
    ("SYNR6", 2, False),
    ("SYNR7", 1, False),
    ("SYNMC1", 10, False),
    ("SYNEX1", 5, False),
]


def region_key(label, n, space, variant=False):
    codes = [f"S{label[-1]}{k:03d}" for k in range(1, n + 1)]
    if variant and n == 3:
        codes[-1] = codes[-1][0] + codes[-1][2:]  # one code without its leading zero
    return f"{label} - LOB{' ' if space else ''}({', '.join(codes)})"


DTYPES = [
    "VARCHAR2(20 BYTE),",
    "DATE,",
    "NUMBER(10),",
    "VARCHAR2(10 BYTE)     NOT NULL,",
    "TIMESTAMP(6),",
    "NUMBER(10,2),",
    "VARCHAR2(5)",
    "DATE               NOT NULL,",
]


def regions(cols, *, differ_in=None, variant=False, sentinels=False):
    out = {}
    for r, (label, n, space) in enumerate(REGION_SHAPES):
        rows = []
        for k, c in enumerate(cols):
            if differ_in == r and k == len(cols) - 1:
                continue  # this region lacks the last column
            dt = DTYPES[k % len(DTYPES)]
            if sentinels and r == 6:
                dt = (
                    [None, "NOT AVAILABLE", "NOT SUPPLIED", "COLUMN NOT FOUND"][k % 4]
                    if k < 4
                    else dt
                )
            rows.append({"column_name": c, "data_type": dt})
        out[region_key(label, n, space, variant)] = rows
    return out


def row(
    src_tbl,
    src_fld,
    tgt_tbl,
    tgt_attr,
    *,
    edits="Direct mapping",
    sel=None,
    idx=None,
    fmt="VARCHAR2",
    length="20",
    definition="SYN definition of the attribute.",
    comments=None,
    block=0,
    source_row=1,
    target_format=None,
):
    """One v2.1 mapping row: the fixed 15-key set, a missing value is null."""
    return {
        "source_database": "SYNFCT",
        "source_table": src_tbl,
        "source_field": src_fld,
        "target_table": tgt_tbl,
        "target_attribute": tgt_attr,
        "data_definition": definition,
        "selection_criteria": sel,
        "mapping_edits": edits,
        "source_format": fmt,
        "field_length": length,
        "target_format": target_format,
        "indexes": idx,
        "comments": comments,
        "block_index": block,
        "source_row": source_row,
    }


def table(
    target,
    rows,
    *,
    comment,
    regional,
    refresh="Daily",
    load="This is a full SYN load",
    rules=None,
    summary=None,
    notes=None,
):
    doc = f"SYN_EDH_E2E_Mapping_{target}_V1.0"
    return {
        "$comment": comment,
        "document_name": doc,
        "source_file": f"SYN Mappings/{doc}.xlsx",
        "layer": "gold",
        "destination_catalog": "syn_edh",
        "target_table": target,
        "refresh_schedule": refresh,
        "load_type": load,
        "mapping_count": len(rows),
        "mappings": rows,
        "regional_table_structures": regional,
        "rules": rules,
        "summary": summary,
        "document_notes": notes,
        "extracted_at": STAMP,
    }


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# (a) regions whose column names match the target; the edit grammar's every class --------------
A = "SYN_MBR_DIM"
a_cols = [
    "SYN_MBR_ID",
    "SYN_GRP_ID",
    "SYN_ALT_ID",
    "SYN_STS_CD",
    "SYN_TYP_CD",
    "SYN_MID_INIT",
    "SYN_SFX",
    "SYN_ZIP_CD",
    "SYN_FULL_NM",
    "SYN_NOTE_TXT",
    "SYN_LOAD_TS",
    "SYN_DEL_DT",
    "SYN_AREA_CD",
    "SYN_AGE_NBR",
]
a_edits = [
    ("SYN_MBR_ID", "Direct mapping", "Primary key"),
    ("SYN_GRP_ID", "SYN_GRP_ID", "Primary Key"),
    ("SYN_GRP_ID", "SYN_ALT_ID", None),
    ("SYN_STS", "if SYN_STS <> 'X' THEN SYN_STS ELSE 'U'", None),
    ("SYN_TYP", "if SYN_TYP = 'A' THEN SYN_A ELSE if SYN_TYP = 'B' THEN 'B1' ELSE 'Z'", None),
    ("SYN_MID_INIT", "if SYN_MID_INIT IS an empty string THEN SynBlank() ELSE SYN_MID_INIT", None),
    ("SYN_SFX", "if ISNULL(SYN_SFX) THEN SynBlank() ELSE TRIM(SYN_SFX)[1,10]", None),
    ("SYN_ZIP", "SYN_ZIP[1,5]", None),
    ("SYN_NM", "TRIM(SYN_NM)[1,30]", None),
    ("SYN_TXT", "TRIM(CONVERT('SYN_A', 'SYN_B', s.SYN_TXT))[1,50]", None),
    ("SYN_TS", "current timestamp", None),
    ("SYN_DEL", "set to NULL", None),
    ("SYN_AREA", "only for SYN_REGION .", None),
    ("SYN_AGE", "SYN_AGE > 0", None),
]
a_rows = [
    row("SYN_MBR_SRC", s, A, c, edits=e, idx=i, source_row=8 + k)
    for k, ((s, e, i), c) in enumerate(zip(a_edits, a_cols, strict=True))
]
a_rows[0]["selection_criteria"] = "SYN_STS_CD = 'A'"
a_rows[1]["selection_criteria"] = "SYN_STS_CD = 'A'"
a_rows[10]["source_format"] = "DATE"
a_rows[10]["field_length"] = None
a_rows[11]["comments"] = "SYN comment."
a_rows[12]["source_field"] = None
a_rows[13]["source_format"] = None
# the second block: the same target fed from another source table (6 of the 14 attributes)
a_rows += [
    row("SYN_MBR_ALT_SRC", f"SYN_ALT_{k}", A, a_cols[k], block=1, source_row=30 + k,
        sel="Pull FROM SYN_MBR_ALT_SRC AND INNER JOIN with SYN_GRP_SRC table using SYN_GRP_ID column")
    for k in range(6)
]
a_rows[14]["indexes"] = "Primary key"
A_DOC = table(
    A,
    a_rows,
    regional=regions(a_cols),
    summary={
        "table_name": A,
        "version": "1",
        "document_name": "SYN_EDH_E2E_Mapping_SYN_MBR_DIM_V1.0",
        "resource_name": "SYNRES",
        "bsa": "SYNBSA",
        "completion_date": "2026-01-01 00:00:00",
    },
    comment=(
        "Stands in for: regional_table_structures whose column names match the target "
        "attributes (10 of 11 real v2.1 files); two mapping blocks for one target "
        "(2 of 11), block 1 feeding a subset of the attributes from another source; "
        "every non-Direct mapping_edits class and free text (21 free-text of 146 non-Direct real cells); summary present in 4 of "
        "11; PK marker spellings 2 of 4."
    ),
)

# (b) no regions, no mapping_edits key; free-text selection criteria ---------------------------
B = "SYN_PLAN_REF"
b_rows = [
    row(
        "SYN_PLAN_SRC",
        f"SYN_P{k}",
        B,
        f"SYN_PLAN_ATTR_{k}",
        edits=None,
        definition=None,
        source_row=5 + k,
        idx=("PRIMARY KEY" if k == 1 else None),
    )
    for k in range(1, 9)
]
b_rows[2]["selection_criteria"] = "for the latest record of SYN_PLAN"
b_rows[3]["selection_criteria"] = "for the latest record of a SYN plan group"
b_rows[4]["selection_criteria"] = "column NOT SYN_RETIRED"
b_rows[5]["source_database"] = None
b_rows[5]["source_table"] = None
B_DOC = table(
    B,
    b_rows,
    regional={},
    load=None,
    refresh="Weekly",
    comment=(
        "Stands in for: mapping_edits null on every row and regional_table_structures {} "
        "(0 of 11 real v2.1 files - kept so the reader has the empty case); load_type null "
        "(5 of 11); data_definition null; free-text selection_criteria; rows without a "
        "source table; document_notes null (6 of 11)."
    ),
)

# (c) selection_criteria: typed join, nameless join, equality, date window -------------------
C = "SYN_ELIG_FACT"
c_sel = [
    "Pull FROM SYN_MBR_SRC AND INNER JOIN with SYN_ELIG_SRC table using SYN_MBR_ID column WHERE SYN_STS_CD = 'A'",
    "Pull FROM SYN_MBR_SRC AND INNER JOIN with SYN_ELIG_SRC & SYN_GRP_SRC tables using SYN_GRP_ID column & SYN_LOB_CD = 'SYN1'",
    "Pull FROM SYN_MBR_SRC AND INNER JOIN with SYN_ELIG_SRC WHERE SYN_PLAN_CD IN ('P1', 'P2', 'P3') using SYN_MBR_ID & SYN_GRP_ID",
    "Pull FROM SYN_PROV_SRC WHERE SYN_TYP_CD = 'X' AND INNER JOIN with SYN_ADDR_SRC table using SYN_PROV_ID column",
    "Pull FROM SYN_PROV_SRC AND INNER JOIN with SYN_ADDR_SRC using SYN_PROV_ID column",
    "Pull FROM SYN_MBR_SRC AND INNER JOIN with SYN_ELIG_SRC WHERE SYN_PLAN_CD IN ('P1', 'P2') SYN_MBR_ID column & SYN_LOB_CD = 'SYN1'",
    "INNER join BETWEEN a.SYN_MBR_ID = b.SYN_MBR_ID AND a.SYN_GRP_ID = b.SYN_GRP_ID OUTER JOIN BETWEEN a.SYN_PLAN_ID *= c.SYN_PLAN_ID",
    "SYN_STS_CD = 'A'",
    "Pull FROM SYN_ELIG_SRC WHERE TRUNC(SYN_EFF_DT) >= sysdate - 30 AND TRUNC(SYN_EFF_DT) <= sysdate",
    "(SYN_EFF/SYN_TERM >= SYN_ASOF AND SYN_EFF/SYN_TERM <= SYN_ASOF) AND (SYN_EFF2/SYN_TERM2 >= SYN_ASOF AND SYN_EFF2/SYN_TERM2 <= SYN_ASOF)",
    "SYN_EFF_DT < GETDATE() < SYN_TERM_DT",
    "NOT SYN_DELETED IN the source",
    "only SYN_ACTIVE in SYN_REGION 1",
    "if SYN_FLAG = 1 - a.SYN_COL IS NOT blank",
]
c_cols = [f"SYN_ELIG_ATTR_{k}" for k in range(1, len(c_sel) + 1)]
c_rows = [
    row(
        "SYN_ELIG_SRC",
        f"SYN_E{k}",
        C,
        col,
        sel=s,
        length="VARCHAR2(20)",  # a type in field_length, as the one real file carries it
        idx=("PK" if k == 1 else None),
        source_row=3 + k,
    )
    for k, (s, col) in enumerate(zip(c_sel, c_cols, strict=True), start=1)
]
c_rows[0]["mapping_edits"] = "if SYN_A IS NULL THEN SYN_B[1,4] ELSE SYN_C : '-' : SYN_D[1,4]"
c_rows[1]["mapping_edits"] = "set NULL"
c_regions = regions(c_cols, differ_in=3, sentinels=True)
list(c_regions.values())[5][2]["column_name"] = "SYN ELIG ATTR"  # a region column name with a space
for extra in ("SYNREG - LOB(S0001, S0002)", "SYNREGX - LOB (S0003)"):  # non-standard labels
    c_regions[extra] = [{"column_name": col, "data_type": "VARCHAR2(20 BYTE),"} for col in c_cols]
C_DOC = table(
    C,
    c_rows,
    regional=c_regions,
    refresh=None,
    rules=[
        "SYN rule: the SYN_ELIG_SRC & SYN_GRP_SRC feed the table.",
        "SYN rule: SYN_PLAN_SRC loads the table.",
    ],
    notes=[
        {"kind": "space_in_name", "where": "sheet 2, column B", "detail": "1 cell"},
        {"kind": "region_label_nonstandard", "where": "sheet 2, row 1", "detail": "2 labels (no region number)"},
    ],
    comment=(
        "Stands in for: join grammar J1 (47 + 13 filter-first), J2 (1), J3 "
        "alias-qualified equalities with INNER + OUTER `*=` (1); two joined tables "
        "(2), a second join column (7); filters F1 equality (73), F2 IN list (17), "
        "F3 / F4 / F5 date windows (7 / 2 / 1), free text; field_length holding a type, "
        "not a length (11 rows of 1 real file; target_format null on all 388 real rows); regions that differ (6 of 11); region data_type "
        "sentinels (10 real items); non-standard region labels (26 real keys); rules "
        "present (2 of 11); refresh_schedule null (3 of 11); a region column name with "
        "spaces (10 real items); document_notes kinds space_in_name and "
        "region_label_nonstandard."
    ),
)

# (d) defects 1–3: prose target_table, duplicated rows, mixed targets ----------------------------
D_PROSE = "SYN memo: SYN_VIEW pulls SYN_SCHEMA SYN_CODE_SRC entries per SYN grouping"
d_attrs = ["SYN_CD", "SYN_CD_DESC", "SYN_EFF_DT", "SYN_TERM_DT", "SYN LOB"]
d_rows = []
for rep in range(2):  # both copies in block 0: the (block_index, target_attribute) check fails
    for k, att in enumerate(d_attrs):
        tgt = (
            "SYN_CODE_DIM"
            if k < 3
            else ("SYN_CODE_VIEW" if k == 3 else "SYN code view (all lines)")
        )
        d_rows.append(
            row("SYN_CODE_SRC", f"SYN_C{k}", tgt, att, idx=("Primary key" if k == 0 else None),
                source_row=3 + 8 * rep + k)
        )
d_rows[4]["indexes"] = "Not NULL"
d_rows[3]["indexes"] = "Unique Index"
d_rows[2]["mapping_edits"] = None
for k, n in ((5, 3), (6, 4), (7, 5)):
    d_rows[k]["source_format"] = f"VARCHAR{n}"  # the drag-filled type cells
D_DOC = table(
    D_PROSE,
    d_rows,
    regional=regions(d_attrs[:4], variant=True),
    load=None,
    refresh=None,
    notes=[{"kind": "drag_fill", "where": "sheet 1, column I [6, 7, 8]", "detail": "3 cells"}],
    comment=(
        "Stands in for the v2.0 defects 1-3 the validator must still fail on (0 of 11 real "
        "v2.1 files carry them): a prose top-level target_table from which json_file is "
        "slugged; a target_attribute twice in one block; 3 distinct mappings[].target_table, "
        "one not an identifier; a target_attribute with a space. Also the variant region key "
        "spelling, non-PK indexes cells (1 real rows), drag-filled source_format "
        "VARCHAR<n> with n > 2 (7 real rows) with its drag_fill document note."
    ),
)


# (e) v2.2: one file, two blocks loading two different tables (mixed_target) ----------------
E_A, E_B = "SYN_SPLIT_A_DIM", "SYN_SPLIT_B_DIM"
e_cols = ["SYN_SPLIT_ID", "SYN_SPLIT_NM", "SYN_SPLIT_DT"]
e_types = ["VARCHAR2(12)", "VARCHAR2(40)", "DATE"]
e_rows = [
    row(f"SYN_SPLIT_{'A' if blk == 0 else 'B'}_SRC", f"SYN_S{k}", tgt, col, block=blk,
        source_row=4 + 8 * blk + k, length=None, target_format=t,
        idx=("Primary key" if k == 0 else None))
    for blk, tgt in ((0, E_A), (1, E_B))
    for k, (col, t) in enumerate(zip(e_cols, e_types, strict=True))
]
E_DOC = table(
    E_A,
    e_rows,
    regional=regions(e_cols),
    notes=[
        {"kind": "mixed_target", "where": "sheet 1, rows 3-14", "detail": "2 target tables",
         "blocks": [{"block_index": 0, "target_table": E_A},
                    {"block_index": 1, "target_table": E_B}]},
        {"kind": "type_in_length_column", "where": "file 1", "detail": "6 rows"},
    ],
    comment=(
        "Stands in for v2.2: a file whose two blocks load two different tables (1 of 11 real "
        "files, 4 rows per block) with its mixed_target note; target_format filled and "
        "field_length null (1 of 11 real files, 11 rows) with its type_in_length_column note. "
        "Read as two feeds."
    ),
)


def build(out=DEFAULT_OUT):
    """Write the manifest + five table files into ``out``; returns the file names."""
    os.makedirs(out, exist_ok=True)
    docs = [A_DOC, B_DOC, C_DOC, D_DOC, E_DOC]
    manifest = {
        "$comment": "Synthetic manifest: same keys as the real v2.1 _manifest.json (11 tables there, 4 here).",
        "extracted_at": STAMP,
        "extractor_version": EXTRACTOR_VERSION,
        "source_volume": "/Volumes/syn_cat/syn_schema/syn_inputs",
        "source_hashes": {
            d["source_file"].split("/")[-1]: hashlib.sha256(d["source_file"].encode()).hexdigest()
            for d in docs
        },
        "file_count": len(docs),
        "tables": [],
    }
    for d in docs:
        name = slug(d["target_table"]) + ".json"
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(d, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        manifest["tables"].append(
            {
                "target_table": d["target_table"],
                "mapping_count": d["mapping_count"],
                "refresh_schedule": d["refresh_schedule"],
                "json_file": name,
                "document_notes_count": len(d["document_notes"] or []),
            }
        )
    with open(os.path.join(out, "_manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return sorted(os.listdir(out))


if __name__ == "__main__":
    for name in build(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT):
        print(name)
