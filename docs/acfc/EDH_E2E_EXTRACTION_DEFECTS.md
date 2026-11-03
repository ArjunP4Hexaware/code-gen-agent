# EDH_E2E_EXTRACTION_DEFECTS — where each defect in the EDH E2E JSON comes from

> **Scope**: the 11 table files of the gold-layer EDH E2E extraction (schema and counts:
> `EDH_E2E_JSON_SCHEMA.md`). I checked each defect against its **source workbook**: the 11
> `source_file`s, all present in the manifest's `source_volume`, read on D1 into a scratch
> directory outside the repo. A defect is **(A) extractor** when the workbook is right and
> the JSON is not. It is **(B) source document** when the JSON copies the workbook faithfully.
> Counts and coordinates only, no cell values.
>
> **File references are manifest indices**: `m<i>` = `_manifest.json` `tables[<i>]`,
> 0-based. They are not the sorted-file `file[<n>]` numbers of `EDH_E2E_JSON_SCHEMA.md`.
> The map from `m<i>` to `file[<n>]` is: m0→10, m1→1, m2→2, m3→4, m4→5, m5→6, m6→3,
> m7→7, m8→8, m9→9, m10→11. Workbook coordinates are `sheets[<k>]!<A1>`, with sheets
> counted from 0.
>
> **"Rule"** names the JSON Schema rule (`EDH_E2E_JSON_SCHEMA.md` §1.2) the defect breaks.
> Where JSON Schema cannot express the check, it names the `x-codegen-checks` entry; where
> nothing breaks, it says so.

---

## v2.1 status (extractor_version 2.1.0, 2026-10-20)

Each item below was checked against the v2.1 output with the same profiler.

| Item | v2.1 | Evidence (counts) |
| --- | --- | --- |
| A1 prose `target_table` | fixed | 0 of 11 files; every `json_file` is slugged from an identifier |
| A2 two blocks flattened | fixed | `block_index` on 388 of 388 rows; m1 and m10 carry blocks 0 and 1; 0 duplicate `(block_index, target_attribute)` |
| A3 `.xls` regions not extracted | **fixed** | m2 now has regions. It has **28** keys, not 7 (the `region_label_nonstandard` note); 26 of its 28 labels are outside the 7 standard shapes, and each region holds the 55 target columns |
| A4 key sets differ by file | fixed | 15 keys on every row of every file |
| A5 `target_format` vs `field_length` | **not fixed, moved** | `target_format` is null on all 388 rows; m0's 11 type values (`VARCHAR2(<n>)` 9, `DATE` 2) now sit in `field_length` |
| B3 mixed targets | **changed by the extractor** | m10: v2.0 had two blocks with different target tables plus a third target; v2.1 has one target. The second block's rows are retargeted to the file's target, and the row with a space in its target and attribute is dropped (7 → 6 rows; 389 → 388 in all). The workbook names a different target table for that block (`sheets[0]!D12:D14`). v2.1 has erased a document fact here. Ask whether the block really loads the same table |
| B4 trailing `.` | changed by the extractor | m2: 0 of 55 targets carry the dot now, though the workbook still does (46 cells) |
| B5 space in a target attribute | gone with the dropped m10 row | 0 rows |
| B1, B2, B6, B7 | unchanged (copied verbatim) | drag-fill 7 rows (+ a `drag_fill` note); spaces 10 items (+ 4 `space_in_name` notes); comma 3,282 / padding 98 items; sentinels 10 |
| B8 region key variant | unchanged | 36 distinct keys (29 in one file only, 28 of them m2's) |
| B9 non-PK `indexes` | 1 row (was 2) | the other row was the dropped m10 row |

## (A) Caused by the extractor

| # | Defect | Files | Count | Evidence in the workbook | Rule broken |
| --- | --- | --- | --- | --- | --- |
| A1 | Prose captured as the top-level `target_table` | m1, m10 | 2 files | m1: the value equals the file's `document_name`; it is no cell and no sheet name; the mapping rows and `summary.table_name` carry the real identifier. m10: the value is the title cell `sheets[0]!A1`, a 93-character sentence (other workbooks carry the table name in their title cell). In both, the manifest's `json_file` is slugged from it. | `/properties/target_table` → `$defs/identifier` (pattern); `x-codegen-checks`: json_file = slug(target_table) |
| A2 | Two mapping blocks flattened with no block marker (reads as duplicated rows) | m1, m10 | m1: 49 attributes × 2 = 98 rows; m10: 3 attributes × 2 | m1: the mapping sheet holds two blocks of the same 49 target attributes, starting at rows 8 and 58 of `sheets[1]` (first attribute at F8 and F58). They are **not copies**: across the 49 row pairs, 34 differ in `source_table`, 37 in `data_definition` and 22 in `mapping_edits`; 8 are identical. m10: two blocks on `sheets[0]` (rows 3–6 and 11–14). The JSON keeps neither block's identity. | `x-codegen-checks`: target_attribute unique within the file (JSON Schema cannot state it) |
| A3 | **FIXED in v2.1** — regional structures not extracted from the `.xls` workbook | m2 | 1 file | `sheets[1]` has 28 region-label-shaped cells and 1,232 Oracle-type cells; the JSON's `regional_table_structures` is `{}` (the only file without regions). | none — `{}` is valid; proposed check: a workbook with a region sheet yields regions |
| A4 | Key sets differ by file: keys named after each workbook's headers instead of one fixed set with nulls | m2 (no `mapping_edits`), m3 (no `comments`), m0 (no `field_length`, adds `target_format`) | 3 files | Each workbook lacks that column header (m2, m3) or names it differently (m0). | none — the schema leaves `mapping_edits`, `field_length`, `comments`, `target_format` out of `required` to admit it |
| A5 | `target_format` in place of `field_length`: the field holds a type, not a length | m0 | 11 rows | The column under that header carries `VARCHAR2(<n>)` 9 and `DATE` 2; the other 10 files carry lengths. | none — both keys optional; a reader must take the length from the type |

### Moved from (A) to (B) by the workbook check

The request listed two items under (A) that the workbooks themselves carry:

- **The stray trailing `.` on target names** (m2, 46 of 55 rows). The workbook has the
  same 46 cells with the dot (from `sheets[0]!E7` down); its other 9 rows and the title
  cell lack it. → B4.
- **Trailing commas and padding in regional `data_type`.** All 1,962 non-null `data_type`
  values equal a workbook cell exactly, commas and padding included (none is a multi-line
  DDL cell split by the extractor). → B6.

The extractor's only part in both is copying without normalising, which the reader handles
(strip the comma, collapse whitespace, split off `NOT NULL`).

---

## (B) Present in the source document

| # | Defect | Files | Count | Evidence in the workbook | Rule broken |
| --- | --- | --- | --- | --- | --- |
| B1 | Excel drag-fill of `source_format` (`VARCHAR2` dragged to `VARCHAR3` … `VARCHAR7`) | m9 | 7 rows | 7 cells in column J of `sheets[1]`, rows 44–56 | none (`nullable_text`); `x-codegen-checks`: drag-fill suspect, flagged, value kept |
| B2 | Spaces in regional column names | m3 (3), m5 (1), m6 (1), m9 (5) | 10 items in 4 files | each equals a workbook cell (e.g. m3 `sheets[1]!K6`, m9 `sheets[2]!C32`) | `$defs/region_item/column_name` was `identifier`, loosened to string; `x-codegen-checks`: non-identifier column_name = flag |
| B3 | Mixed targets in one file | m10 (3 values), m2 (2 values) | 2 files | m10: two blocks name different target tables (`sheets[0]!D4:D6`, `D12:D14`), plus a third value with a space (`D3`, `D11`). m2: the trailing-dot variant (B4) beside the clean name (9 rows + the title cell `A1`). | `$defs/mapping/properties/target_table` → identifier (pattern) for the space / dot values; `x-codegen-checks`: one mappings[].target_table per file, equal to the top level |
| B4 | Stray trailing `.` on the target table name | m2 | 46 rows | 46 workbook cells carry it | `$defs/mapping/properties/target_table` → identifier (pattern) |
| B5 | Space in a target attribute name | m10 | 1 attribute (2 rows) | `sheets[0]!E3`, `E11` | `$defs/mapping/properties/target_attribute` → identifier (pattern) |
| B6 | Regional `data_type` as raw Oracle DDL fragments: trailing comma, inner padding | comma: m0, m1, m3, m4, m5, m6, m9; padding: m1, m3, m4, m5, m6 | 1,770 items with a comma, 98 with padding | every value equals a workbook cell | none (`nullable_text`); reader normalises |
| B7 | Regional `data_type` sentinels (`NOT AVAILABLE`, `NOT SUPPLIED`, `COLUMN NOT FOUND`, `NULL`) or empty | m3 (3), m5 (1), m6 (1, an empty cell), m9 (5) | 10 items | each equals a workbook cell | none; `x-codegen-checks` (§4 row 7): sentinel = open input |
| B8 | One region key spelled differently (a code without its leading zero) | m10 | 1 file | all 7 keys of m10 are workbook cells | `x-codegen-checks`: region keys identical across files |
| B9 | `indexes` text that is not a PK spelling | m5 (1), m10 (1) | 2 rows | each equals a workbook cell | `x-codegen-checks`: other text = QUESTION |

Not a defect, recorded for the reader: the 7 regions differ from each other in 5 files (m0,
m3, m5, m6, m9). The regional tables genuinely differ, so a reader keys the mapping on the
target attributes and compares regions per column.

---

## What goes back to whom

- **Extractor owner (A1–A5):**
  - take `target_table` from the mapping rows / summary, never from the document name or a
    title cell;
  - carry a block index on every mapping row;
  - read the `.xls` workbook's region sheet;
  - emit one fixed key set with nulls, and name the type-vs-length column for what it holds.
- **Mapping authors (B1, B3–B5, B9):**
  - fix the drag-filled types (m9), the trailing dot (m2) and the spaces in names (m10);
  - confirm that m10's blocks really load different target tables.
- **The reader (B2, B6–B8):**
  - normalise `data_type`;
  - flag region column names with spaces;
  - treat sentinels as open inputs;
  - match regions on the label, not the whole key.
