# fixtures/acfc_shapes — synthetic fixture universe for ACFC's real shapes

Every file here is SYNTHETIC and GENERATED: `python scripts/build_acfc_shapes.py`
rebuilds the whole set byte for byte from `tests/acfc_shapes/` (the suite
asserts the tracked bytes equal a fresh build, and runs the scrub denylist
scanner over the directory). The structures are transcribed from
`docs/acfc/SHAPES_FOR_PORT.md` (STTM families A–E, FRD families F1/F2, VDD
patterns V1–V3) and `docs/acfc/rfc_capture/rfc_capture/RFC_PACKAGE_SHAPES.md`;
the values are invented, except pair 1, whose columns/types/segment layout are
the (scrubbed, aliased) pair-1 golden — see `ALIASES.md`.

Tracked by deliberate per-file `.gitignore` re-includes (the repo ignores
`*.xlsx` / `*.docx` by default); adding a fixture means adding its path there
too, one line per file.

| Fixture | Family / pattern | Source pair | Structure reproduced |
| --- | --- | --- | --- |
| `sttm/pair_1_family_a.xlsx` | STTM A — inline meta + banded mapping | 1 | Version (header r3, A2:D2 merged), LOB_CROSSWALK, FEED_1_MAPPING: meta r1–r12 (labels verbatim; r5/r6/r7/r10/r12 blank), band r14 `Source Data | Data Rules and Primary Keys | Staging Layer Table | Standard Layer Table` (4 merges), headers r15 (27 cols), Segment column HDDR/DET/TRLR, 3 trailing `NA` audit rows |
| `sttm/pair_8_family_a.xlsx` | STTM A — inline meta + banded mapping | 8 | single FEED_8_LAYOUT: meta r1–r6 (all populated), band r7 `Header Record | Staging Layer | Standard Layer`, headers r8 (21 cols), HR/DR/TR/FT blocks introduced by merged segment-label rows with `count` merged down each block |
| `sttm/pair_2_family_b.xlsx` | STTM B — FILE_DETAILS + MAPPING- sheets | 2 | FILE_DETAILS (5 cols), VERSION_HISTORY (4), `MAPPING-`, `MAPPING-1`, `MAPPING-2`: band r1 (3 labels, no merges), headers r2 (16 cols, Schema/TableName/ColumnName/DataType twice), trailing `NA` audit rows |
| `sttm/pair_3_family_c.xlsx` | STTM C — Layout + STTM dual sheets | 3 | Version Control, Layout (meta r1 FileName; headers r4 = 13 cols incl. 5 LOB cols), STTM (meta r1–r2; band r4 `Source - [SRC_SYS_A] File | Destination | Target Table - Staging Layer | Target Table - Standard Layer`, 4 merges; headers r5 = 31 cols), FileNames |
| `sttm/pair_4_family_d.xlsx` | STTM D — single mapping sheet | 4 | STTM (meta r1 File Name only; band r4 `Source Data | Data Rules | Target Table - Staging Layer | Target Table - Standard Layer`; headers r5 = 25 cols, `... in Lakehouse`; 3 trailing `NA` audit rows), LOB_CROSSWALK (3), OVERPUNCH_RULES (band r1–r2, headers r3, 2 merges) |
| `sttm/pair_6_family_d.xlsx` | STTM D — single mapping sheet | 6 | Version Control (header r2), Server details (6 environment-group merges), FEED_6_MAPPING (band r2 `Source table | Stage Layer | STD layer`, 3 merges; headers r3 = 22 cols; database-table source; 3 trailing `NA` audit rows) |
| `sttm/pair_5_family_e.xlsx` | STTM E — multi-domain / multi-sheet | 5 | Version History (band r3, headers r4), File Details (7 cols), Table_Details, FEED_5_MAPPING (meta r1–r9 incl. blank File Generator + NOTE; band r10 `Source Layout | Stage Layer | Standard Layer`; headers r11 = 33 cols; Segment column Header/Detail/Trailer; per-segment audit rows), Sheet2, Sheet3 (no header), Sheet1 (DQ rules) |
| `sttm/pair_7_family_e.xlsx` | STTM E — multi-domain / multi-sheet | 7 | Version History (band r5, headers r6), File Details (`Frequency (Historical Drops)`), MAPPING_FEED_7 (headers r1 = 19 cols, NO band row; Stage/Standard prefixes in the header texts; `Recycle Flag`), Sheet2 ID list, Queries, Analysis_Notes, Analysis Sheet - Detail, Analysis Sheet - Compound, Sample Records, Sheet1 crosswalk |
| `sttm/pair_9_family_e.xlsx` | STTM E — multi-domain / multi-sheet | 9 | Summary (8 cols), MAPPING_FEED_9 + MAPPING_FEED_9_TBL2 (band r1 `Source Tables | Target - DL Staging Layer | Target - DL Standard Layer`, 3 merges; headers r2 = 24 cols; database source), Sheet2, Log (header r2), Sheet1. **Deviation:** the documented pair 9 has ONE 1,400-row mapping sheet; the fixture splits two tables onto two mapping sheets to exercise the family's one-sheet-per-table shape |
| `sttm/pair_10_family_e.xlsx` | STTM E — multi-domain / multi-sheet | 10 | Version (header r2), Outbound_REGION_A (17 cols), Inbound_REGION_A (20), Inbound_REGION_B_Adult (18), Inbound_REGION_B_Child (18) — each meta r2, band r4 (3 merges), headers r5, trailing `Comments` — plus `Mapping` (vendor spec). **Note:** the document does not record pair 10's band texts; the fixture uses `Source Data | Stage Layer | Standard Layer` |
| `frd/f1_pair_1.docx` | FRD F1 — six metadata sections | 1 | 14 Word tables, no heading styles; Descriptive/Structural/Administrative/Technical/Data Quality/Vendor tables (row 0 title, rows 1–3 Name/Description/Functional Requirement, rows 4+ label:value); pair-1 label variants `Target Catalog and Schema`, `Load Strategy STD (View)`, `Inbound File Folder Path`; blanks per §4 pair 1; describes the pair-1 golden columns |
| `frd/f1_pair_2_variant.docx` | FRD F1 — six metadata sections | 2 | two complete metadata sets + duplicated NFR placeholder tables (the 40-table shape); label variants `Target Schema`, `Load Strategy STD`, `Inbound/outbound File Folder Path`; Functional Requirement blank everywhere; blanks per §4 pair 2 |
| `frd/f2_pair_8.docx` | FRD F2 — Solution Requirement tables | 8, 9, 10 | Heading 1 / Heading 4 paragraphs; no metadata tables; eight 10×4 Solution Requirement tables with the metadata section label in row 4 (`Descriptive Metadata` … `Reject /Recycle Process`, `Email`); `Business \nRequirement` (embedded newline) and `Functional Requirement:` (trailing colon) |
| `vdd/pair_1_v1_segments.xlsx` | VDD V1 — full position (11 cols) | 1 | FILES (10 cols, 4 patterns, Multi Record Type Y, Record Type Field SEGMENT_IDENTIFIER, Delimiter blank); `FEED_1 Fields` with Segment HDR/DTL/TRL; starts/lengths from the golden fixed-width handler |
| `vdd/pair_2_v2_per_file.xlsx` | VDD V2 — length only (9 cols) | 2 | FILES (3 csv files); one field sheet per file; Length blank throughout; Example Value populated |
| `vdd/pair_9_v3_per_table.xlsx` | VDD V3 — DB table (8 cols) | 9 | FILES (Delimiter / Multi Record Type / Record Type Field / Header Row blank); one field sheet per table (3 tables) |
| `pair_1/golden/ACCUM_DDL.txt` | pair-1 golden, aliased | 1 | the scrubbed golden DDL with `ALIASES.md` applied — the M4 byte-identity target |
| `pair_1/golden/RFC_ACCUMULATORS_IIG.xlsx` | pair-1 golden, aliased | 1 | the scrubbed golden IIG (8 sheets) with `ALIASES.md` applied, re-serialized byte-stably; sheet order, headers, row counts untouched |

Not built (out of the documented shapes' scope for this build): STTM pairs'
1,000,000-row openpyxl artefacts (rows are 10–30 here), the runbook and TDD
`.docx` of the RFC package.
