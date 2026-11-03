# GOLD_STTM_SHAPE — Structural Shape of the Provider-Domain Gold-Layer STTM + Models

> **Purpose**: the gold-layer counterpart of `SHAPES_FOR_PORT.md`, written for the next phase
> (CodeGen generates the gold load SQL from this mapping; the upstream agent writes the
> mapping). Structural description only: header labels as spelled, counts, shapes and
> coordinates. **No document values** — no table, column, catalog or schema names, no
> criteria text, no business definitions. Sheets are cited by 0-based workbook position
> (`sheets[<i>]`, the same convention as the printed answer keys); model entities by an
> anonymous label (`F1`, `F2`, `D01`…`D14`, §4).
>
> **Inputs read (2026-10-20, read-only, from the Workspace folder, never copied into the repo)**:
> one STTM workbook (20 sheets), one physical-model PDF, one logical-model PDF.
> Read with openpyxl 3.1.5 (`data_only=True`), pypdf 6.21.1, pdfplumber; the PDF images were
> inspected visually for counts only.

---

## 1. Workbook layout

20 sheets: 19 visible, 1 hidden (`sheets[5]`).

| Sheet | Role | Header row | Data rows | Notes |
| --- | --- | --- | --- | --- |
| `sheets[0]` | Instructions / change log | r5 (table B5:G5) | 17 (r6–r22) | Title lines B2, B3 (merged B:G). Version table headers: `Version No.`, `Integration/Project Name`, `Change Description`, `Date`, `Name`, `Status`. Notes block below: a label in B24 and 4 long free-text cells B25–B28 (merged B:G; 11 merges in all). Used range B2:G32. |
| `sheets[1]` | Table list | r1 | 16 + 1 blank row (r5) | Headers `TABLE NAME`, `BUSINESS DEFINITION`. Of the 16 entries, 14 equal a mapping sheet's name, 1 equals the reference sheet's name, 1 equals the `Target Table Name` of a sheet whose own sheet name differs (`sheets[14]`). Not listed: `sheets[5]` (hidden) and `sheets[6]`. |
| `sheets[2]`–`sheets[18]` | One sheet per target table (17 sheets) | r3 (field headers); r2 = band row; r1 = title | see §2 | Exceptions: `sheets[5]` has 3 target tables and repeats the header row at r4; `sheets[8]` has 2 target tables; `sheets[14]`'s target table name ≠ its sheet name. |
| `sheets[19]` | Reference / seed table (static rows, not a mapping) | r1 | 25 | Headers `SK`, `ENTITY_DOMAIN`, `ENTITY_TYPE`, `ENTITY_TYPE_CODE`, `ENTITY_TYPE_DESCP`, `Created Date`, `created by`, `updated Date ` (trailing space), `update by`. Fill: SK 23/25, the three entity columns 21/25, the description 11/25, the four audit columns 0/25. Listed in `sheets[1]`. |

### 1.1 Mapping-sheet header block (r1–r3)

- **r1** — one title cell in A1, identical text on all 17 mapping sheets (merged A1:E1 on
  `sheets[2]` only).
- **r2** — band labels. `Data Source` at A2 on 15 sheets; `Notes / Comments` on all 17.
  Variants: `sheets[7]` = `Data Source - STD Layer` (A2) + `Target-EDH Layer` (G2) +
  `Notes / Comments` (P2); `sheets[18]` = `Data Source` + `Relational Table Target` (I2) +
  `Notes / Comments` (N2). No other sheet labels the target band. `Notes / Comments` sits at
  L2 (13 sheets), M2 (`sheets[9]`), N2 (`sheets[8]`, `sheets[18]`), P2 (`sheets[7]`); the
  column under it has no r3 header and is empty on every sheet except where SCD2 lands in it.
- **r3** — field headers. The base layout (13 sheets):

  ```
  A Table / Segment | B Column | C Datatype | D Length | E Business Definition |
  F Data selection criteria | G Target Table Name | H Column Name | I Datatype |
  J Nullable | K Length | L (none) | M SCD2-family (or absent)
  ```

  `Datatype` and `Length` appear twice (source side C/D, target side I/K) with identical
  spelling — a reader must disambiguate by position / band, not by label.

### 1.2 Spelling and position variants across the 17 mapping sheets

| Variant | Sheets | Detail |
| --- | --- | --- |
| SCD2 header `SCD2` | 2, 4, 6, 7, 8, 12, 13, 14, 15, 16 | column M (2, 4, 6, 8), L (12–16), O (7) |
| SCD2 header `SCD2)` | 9, 10 | column N (9), M (10) |
| SCD2 header `SCD2?` | 11 | column M |
| No SCD2 header | 3, 5, 17, 18 | — |
| SCD2 header present, column empty | 7, 8 | header only, 0 marks |
| `Catalog Name` + `Schema Name` (target side) | 7, 18 | G, H; each holds exactly 1 distinct value on its sheet |
| `Table Name` instead of `Target Table Name` | 18 | column I |
| `Logical Name` | 7 (N), 8 (L) | the only two sheets with it |
| Extra unlabeled empty column B (shifts every header one column right) | 9 | `Column` at C … `SCD2)` at N; 2 stray cells outside the headers (Q9, R10) |
| Header row repeated as the first data row | 5 (hidden) | r3 and r4 identical |
| Used range inflated to column XFD / row 2173 | 2 | real data ends at r184 / column M |

SCD2 cell vocabulary: only `Y` (87 marks over 10 sheets). Nullable vocabulary (target `J`):
`Nullable` 427, `Not null` 220, `Not Null` 35, `Null` 11, `nullable` 11, other 1 — five
spellings of two meanings.

---

## 2. Per target-table sheet

Data rows start at r4. "Target cols" = rows with a target `Column Name`. "3-part sources" =
distinct `catalog.schema.table` references in `Table / Segment`.

| Sheet | Data rows | Target cols | Targets | 3-part sources | `No mapping` rows | SK-generation cell | Merges below r3 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 181 | 78 | 1 | 25 | 14 | F4 | 153 |
| 3 | 13 | 13 | 1 | 1 | 10 | F4 | 0 |
| 4 | 278 | 194 | 1 | 19 | 14 | F4 | 94 |
| 5 (hidden) | 14 | 14 | 3 | 1 | 9 | — | 0 |
| 6 | 58 (1 blank) | 57 | 1 | 4 | 16 | E4 | 0 |
| 7 | 27 | 27 | 1 | 1 | 12 | F4 | 0 |
| 8 | 37 | 37 | 2 | 2 | 9 | E4 | 0 |
| 9 | 32 | 32 | 1 | 1 | 14 | G4 | 0 |
| 10 | 32 | 32 | 1 | 1 | 14 | F4 | 0 |
| 11 | 30 | 30 | 1 | 3 | 14 | F4 | 0 |
| 12 | 24 | 24 | 1 | 1 | 14 | F4 | 0 |
| 13 | 27 | 27 | 1 | 1 | 14 | E4 | 0 |
| 14 | 36 | 36 | 1 | 1 | 14 | F4 | 0 |
| 15 | 32 | 32 | 1 | 1 | 14 | E4 | 0 |
| 16 | 38 | 38 | 1 | 0 (24 unqualified) | 14 | F4 | 0 |
| 17 | 17 | 17 | 1 | 0 (11 unqualified) | 6 | — | 0 |
| 18 | 34 | 17 | 1 | 17 | 11 | F4 | 11 |

Fill rate per column (non-empty / data rows; columns at 0 omitted):

| Sheet | Table / Segment | Column | Src Datatype | Src Length | Business Definition | Data selection criteria | Target Table | Column Name | Tgt Datatype | Nullable | Tgt Length | SCD2 | Logical Name |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 181/181 | 167 | 63 | 16 | 78 | 30 | 78 | 78 | 78 | 78 | 0 | 16 | — |
| 3 | 13/13 | 3 | 3 | 0 | 13 | 3 | 13 | 13 | 13 | 13 | 0 | — | — |
| 4 | 278/278 | 253 | 171 | 34 | 193 | 129 | 194 | 194 | 194 | 194 | 0 | 8 | — |
| 5 | 14/14 | 2 | 6 | 2 | 10 | 1 | 14 | 14 | 14 | 14 | 1 | — | — |
| 6 | 57/58 | 44 | 43 | 2 | 57 | 8 | 57 | 57 | 57 | 57 | 0 | 9 | — |
| 7 | 27/27 | 22 | 17 | 0 | 27 | 7 | 27 | 27 | 27 | 27 | 0 | 0 | 11 |
| 8 | 37/37 | 29 | 28 | 0 | 37 | 12 | 37 | 37 | 37 | 37 | 0 | 0 | 9 |
| 9 | 32/32 | 18 | 18 | 5 | 32 | 4 | 32 | 32 | 32 | 32 | 0 | 4 | — |
| 10 | 32/32 | 18 | 18 | 3 | 32 | 3 | 32 | 32 | 32 | 32 | 0 | 10 | — |
| 11 | 30/30 | 16 | 11 | 2 | 30 | 6 | 30 | 30 | 30 | 30 | 0 | 3 | — |
| 12 | 24/24 | 10 | 9 | 1 | 24 | 3 | 24 | 24 | 24 | 24 | 0 | 3 | — |
| 13 | 27/27 | 13 | 4 | 1 | 27 | 2 | 27 | 27 | 27 | 27 | 0 | 5 | — |
| 14 | 36/36 | 22 | 12 | 2 | 36 | 3 | 36 | 36 | 36 | 36 | 0 | 8 | — |
| 15 | 32/32 | 18 | 16 | 3 | 32 | 2 | 32 | 32 | 32 | 32 | 0 | 8 | — |
| 16 | 38/38 | 24 | 23 | 19 | 38 | 5 | 38 | 38 | 38 | 38 | 0 | 14 | — |
| 17 | 17/17 | 11 | 11 | 0 | 17 | 0 | 17 | 17 | 17 | 17 | 0 | — | — |
| 18 | 34/34 | 23 | 5 | 0 | 17 | 5 | 17 | 17 | 17 | 17 | 0 | — | — |

`sheets[7]` and `sheets[18]` also fill `Catalog Name` / `Schema Name` on every target row
(27/27, 17/34).

### 2.1 How a target row and its sources are expressed

- **`Table / Segment` is never blank on a data row** (one blank row in `sheets[6]` is an
  empty row). There are no segment banner rows and no "only column A" rows.
- **Source references** (column A without the 213 `No mapping` markers, the 4 `derived`
  markers and the repeated header — 691 cells): 594 are three-part
  `catalog.schema.table` names (39 distinct tables, 2 distinct catalogs, 7 distinct
  catalog.schema pairs); 48 are a single unqualified token (24 on `sheets[16]`, 11 on
  `sheets[17]`, a few elsewhere — `sheets[17]`'s sources are other gold tables, its target
  being 12 of 17 SK columns); 49 are other text: 39 an `alias.table`-style two-part reference
  followed by words, 7 long multi-sentence lineage prose, 2 short phrases, 1 shaped as an
  `UPDATE … SET … = CURRENT_TIMESTAMP() WHERE …` statement (`sheets[4]`).
- **`No mapping` / `No Mapping`** (206 + 7 rows) in column A, column B blank: the target-only
  columns the load populates itself. 14 per sheet on the standard-shaped sheets — the same
  count as a model dimension's UDF (4) + SCD2 triple (3) + audit (4) + lineage (3) columns
  (§4); the SK row is not one of them (it carries a source and the SK-generation sentence).
- **Multi-source per target column = vertical merges of the target cells.** On `sheets[2]`
  and `sheets[4]` the target-side cells (E–M) of one target column are merged over 2–16 rows,
  and each row inside the span names one source table/column (`sheets[2]`: 181 rows for 78
  target columns, merge spans 2 → 16 rows; `sheets[4]`: 278 rows for 194 target columns,
  43 spans of 15 rows). `sheets[18]` carries one 18-row block merged across C–N. With openpyxl
  the merged-away cells read as empty — a reader must expand merges before reading.
- **Interleaving**: source tables are not grouped — `sheets[2]` has 32 distinct column-A
  values in 145 runs, `sheets[4]` 28 in 113. Each row names its own source.
- **Target table name** is repeated on every target row (never qualified: 705 cells, 0 dots);
  the target band carries no catalog/schema except on `sheets[7]` and `sheets[18]`.
- Target datatypes: `STRING` / `TIMESTAMP` / `BIGINT` / `INT` / `INTEGER` / `DATE` /
  `BOOLEAN`; one `BIGINT` (the SK) on 12 sheets, more where the target also carries
  other SKs (`sheets[4]`, 5, 8, 17, 18); `sheets[5]` carries the
  literal header word in a data cell (the repeated header). Source datatypes add `CHAR`,
  `VARCHAR`, `DATETIME`, `SMALLINT`, `MONEY`, `DECIMAL(p,s)` and the marker `NO MAPPING`
  (`sheets[6]`, `sheets[7]`) — source-system types, not Spark types.
- The target `Length` column is empty everywhere but one cell (`sheets[5]`).

**Sheets that break the pattern**: 2 and 4 (merged multi-source spans; most criteria cells),
5 (hidden, 3 targets, repeated header, not in the table list), 6 (not in the table list),
7 and 18 (catalog/schema columns, own band labels; 18 says `Table Name`), 8 (2 targets),
9 (shifted by a blank column B), 14 (sheet name ≠ target name), 16 and 17 (no qualified
sources), 17 and 18 (no SCD2 column).

---

## 3. "Data selection criteria" (column F; G on `sheets[9]`)

223 non-empty cells, 79 distinct texts (repeats come from one text per row of a merged
span), on 16 of 17 sheets (`sheets[17]` has none). Length: 6 → 2,594 characters, median 141.
Per sheet: 2: 30, 3: 3, 4: 129, 5: 1, 6: 8, 7: 7, 8: 12, 9: 4, 10: 3, 11: 6, 12: 3, 13: 2,
14: 3, 15: 2, 16: 5, 18: 5.

Most cells mix shapes (cells by number of classes: 0 → 28, 1 → 145, 2 → 28, 3 → 9,
4 → 11, 5 → 2), so the counts are given two ways: every class a cell shows (multi-label),
and one primary class (precedence join > window > equality > derivation > free text).

| Class | Multi-label cells | Primary cells | Primary distinct | Sheets (cells) | Generic example (placeholders only) |
| --- | --- | --- | --- | --- | --- |
| Join hint | 144 | 144 | 27 | 2 (20), 4 (116), 7, 8 (3), 11 (2), 16, 18 | `join <alias>.<table_a> to <alias>.<table_b> ON (<a>.<key> = <b>.<key> AND <a>.<key2> = <b>.<key2>)` |
| — of which join type stated | 2 | — | 2 | `sheets[7]!F12`, `sheets[18]!F7` | `FROM <schema>.<table_a> LEFT JOIN <schema>.<table_b> ON <a>.<key> = <b>.<key>` |
| Date / validity window, latest record | 14 (+18 ROW_NUMBER rankings) | 1 | 1 | 2 (13), 4 (1); rankings `sheets[2]` only | `ROW_NUMBER() OVER (PARTITION BY <key cols> ORDER BY <date col> DESC) = 1`; `CASE WHEN <end date> > CURRENT_DATE() THEN '<v1>' ELSE '<v2>' END` |
| Equality filter | 48 | 25 | 13 | 15 sheets; most on 2 (16), 4 (9) | `where <col> = '<value>' and <col2> = '<value2>'` |
| Derivation / expression | 58 | 25 | 23 | 15 sheets | `CONCAT(<col1>, <col2>, COALESCE(<col3>, '<default>'))`; `SK <name> generated based on <col> and <col>` |
| Free text | 28 | 28 | 15 | 16 sheets | `only <qualifier> for the <qualifier> source`; `for <column group> NULL` |

Also: 4 cells hold a full `SELECT … FROM …` (`sheets[2]!F63`, `sheets[4]` ×2, `sheets[7]!F12`).
Row 4 of 15 sheets carries the SK-generation sentence (§2 table) — in column F on 10 sheets,
column E (`Business Definition`) on 4, G on `sheets[9]`.

---

## 4. Physical model

**No text layer.** One page (1964 × 3704 pt), produced by PDFlib 9.0.3: pypdf
`extract_text()` returns 0 characters, pdfplumber finds 0 words / 0 chars / 0 rects / 0 lines
and **1 embedded raster image** (1820 × 3560 px RGB). Nothing is extractable with
pdfplumber / pypdf; every count below was read by eye from the image and is a structural
count, not a transcription. A DDL export (§7 Q1) replaces this section.

16 entity boxes: 2 facts (`F1`, `F2`), 14 dimensions (`D01`–`D14`), of which 2 (`D07`, `D08`)
are collapsed to their key row. Labels follow the diagram: left column top → bottom
(`D01`–`D05`), centre (`D06`, `F1`, `D07`, `D08`, `D09`, `F2`), right (`D10`–`D14`).

Annotations the image carries: a key icon on the PK row (above a rule), per-column datatype,
`NULL` / `NOT NULL` on every column, `(FK)`, `(AKn.n)` alternate-key members, and colour
(key/AK columns orange, attributes green, audit blue).

| Entity | PK | AK members (group AK1) | FK marks | NOT NULL stated | SCD2 triple (rec. eff. start / end / is-current) |
| --- | --- | --- | --- | --- | --- |
| F1 | 1 SK, INT | 7 (= its 7 FKs) | 7 | yes | no |
| F2 | 1 SK, INT | 0 | 6 | yes | no |
| D01 | 1 SK, INT | 3 | 0 | yes | yes |
| D02 | 1 SK, INT | 3 | 0 | yes | yes |
| D03 | 1 SK, INT | 4 | 0 | yes | yes |
| D04 | 1 SK, INT | 4 | 0 | yes | yes |
| D05 | 1 SK, INT | 0 | 0 | yes | no |
| D06 | 1 SK, INT | 2 | 0 | yes | yes |
| D07 (collapsed) | 1 SK, INT | — | — | key row only | — |
| D08 (collapsed) | 1 SK, INT | — | — | key row only | — |
| D09 | 1 SK, INT | 4 | 0 | yes | yes |
| D10 | 1 SK, INT | 4 (2 of them its FKs) | 2 | yes | yes |
| D11 | 1 SK, INT | 0 | 0 | yes | no |
| D12 | 1 SK, INT | 5 | 0 | yes | yes |
| D13 | 1 SK, INT | 2 | 0 | yes | yes |
| D14 | 1 SK, INT | 0 labelled (3 columns key-coloured, NOT NULL) | 0 | yes | no |

Every AK group on a dimension includes a region-role column as its last member (all 9
dimensions with an AK). The SK is a single INT column on every entity; the STTM types it
`BIGINT` (§2).

**FK relationships recoverable (15 FK marks)** — FK column name = the referenced
dimension's PK name in every legible case:

| From | To | Via column role | Count |
| --- | --- | --- | --- |
| F1 | D01, D02, D03, D04, D06, D09, D12 | dimension SK (each also an F1 AK1 member → the grain) | 7 |
| F2 | D05, D06, D13, D14 | dimension SK | 4 |
| F2 | D07 (role-played twice) | two date-role SKs (`…_DT_SK` suffix; endpoint inferred from the suffix) | 2 |
| D10 | D06, D11 | dimension SK (both also D10 AK members) | 2 |

D08 has no FK column pointing at it (F2 carries a plain string attribute of the same role).
Relationship lines are dashed (non-identifying); cardinality marks and line endpoints are not
legible at this resolution. Two audit columns carry a type that differs from the same column
on every other entity (one in F2, one in D14).

---

## 5. Logical model

Same format (one page, PDFlib 9.0.3, **no text layer**, 1 raster image 1820 × 3560 px) and
the **same 16 boxes in the same positions** as the physical model. What it adds:

- **Business names** for every entity and column (Title Case words, abbreviations expanded),
  in place of the physical abbreviated names.
- **Logical datatypes**: `INTEGER` for keys, a uniform `CHAR(18)` for every string (a
  modelling-tool default, not a width), `TIMESTAMP`, `DATE`, `DECIMAL(p,s)`, one `TEXT`.
- The same PK / `(FK)` / `(AKn.n)` / `NULL`-`NOT NULL` marks.
- **No descriptions or definitions** — the business definitions exist only in the STTM
  (`Business Definition` E: every target row on 14 sheets; `sheets[4]` 193/194, `sheets[5]`
  10/14, `sheets[18]` 17 of 17 target rows)
  and in `sheets[1]` column B.

Logical → physical mapping: positional (same box, same row order) plus abbreviation; at least
one column of F2 sits at a different row in the two models. The STTM's `Logical Name`
column carries the logical name on 2 sheets only (`sheets[7]` N: 11/27, `sheets[8]` L: 9/37);
no other sheet links a target column to the logical model.

---

## 6. Nikshit's five asks

| Ask | STTM | Model | Verdict |
| --- | --- | --- | --- |
| Joins (which tables, on what keys) | Stated partly, as text: 144 criteria cells with a join hint (27 distinct), 136 of them on `sheets[2]` / `sheets[4]` (e.g. `sheets[2]!F63`, `sheets[2]!F122:F126`, `sheets[4]!F47`); 49 prose / two-part source cells in column A (e.g. `sheets[6]!A5:A15`, `sheets[8]!A5:A14`); multi-source columns as merged spans (§2.1). 10 of 17 sheets have no join text at all. | Gold-to-gold only: 15 FK marks (§4). Source-to-gold joins: nowhere. | **STTM (partial, free text)** for source joins; **model** for gold FKs |
| Join type | Stated in 2 cells (`sheets[7]!F12`, `sheets[18]!F7`, both LEFT). | Not stated (dashed non-identifying lines; FKs NOT NULL on F1 / F2 / D10). | **Nowhere** for 142 of 144 join cells |
| UC source naming | Stated: 594 three-part `catalog.schema.table` cells in column A (15 sheets; 39 tables, 2 catalogs, 7 schemas); unqualified on `sheets[16]` A (24) and `sheets[17]` A (11). Target: catalog/schema only on `sheets[7]` G:H and `sheets[18]` G:H; `Target Table Name` never qualified. | Not stated (entity names only). | **STTM** for sources; **nowhere** for the target catalog/schema on 15 of 17 sheets |
| Filters | Stated as text: 48 equality-filter cells, 14 date/validity-window cells, 18 ROW_NUMBER rankings (`sheets[2]!F122` …), 4 full SELECTs (§3). | Not stated. | **STTM (free text)** |
| PK / SK | No key column in any STTM header; SK generation stated in one row-4 sentence on 15 sheets (§2 table: E4 / F4 / G4); SK typed BIGINT; `Nullable` J; `SCD2` = `Y` on 10 sheets. Natural / alternate key: nowhere in the STTM (1 cell mentions a key, `sheets[2]!F4`). | PK = one INT SK on all 16 entities; AK groups on 10 (§4); D14's key is colour-only; D07 / D08 collapsed. | **Model** for PK/AK (raster only); **STTM** for SK generation (text); SK type conflicts (INT vs BIGINT) |

---

## 7. Open questions for Nikshit

1. Can you export the physical model as DDL (or the modelling tool's column report as CSV), since both PDFs are images with no text layer?
2. What SCD2 / SK convention do the existing EDH gold loads use — SK generation (identity, sequence, hash, max+1), the effective-end value for a current row, and the is-current values?
3. Is the SK `INT` (model) or `BIGINT` (STTM)?
4. Are the model's `AK1` groups the business keys the MERGE should match on, and what is `D14`'s key (3 key-coloured columns, no AK label)?
5. For a join hint with no stated type (142 of 144 cells), is the default LEFT or INNER?
6. Which catalog and schema do the 15 target sheets without `Catalog Name` / `Schema Name` load into?
7. Is the hidden `sheets[5]` (3 targets, not in the table list) in scope?
8. Is `sheets[6]`, which is not in the table list, in scope?
9. Does `sheets[14]`'s sheet name or its `Target Table Name` name the table?
10. Is `sheets[19]` a seed table that CodeGen should load as static rows, or is it reference only?
11. On `sheets[2]` / `sheets[4]`, does a merged target span mean COALESCE over the listed sources in row order, a UNION, or one row per source?
12. Do the unqualified sources on `sheets[16]` / `sheets[17]` live in a known catalog.schema, or are they gold tables built earlier in the same run?
13. Do `SCD2`, `SCD2)` and `SCD2?` mean the same thing, and does a blank cell mean type-1 overwrite?
14. Is the `SCD2` column on `sheets[7]` / `sheets[8]` empty on purpose, i.e. no SCD2 columns there?
15. Are the 14 `No mapping` rows per sheet always the load-populated columns (SCD2 triple, UDFs, audit, lineage), and which of them must CodeGen populate?
16. What table do the 2 date-role SKs in `F2` reference, and which load populates `D07` / `D08` (collapsed in both models)?
17. Will the upstream agent keep the column-F criteria as free text, or can it write structured fields (join keys, join type, filter predicate)?

---

## 8. The second input dialect: EDH E2E JSON

The gold-layer EDH E2E mappings arrive as JSON from an extractor, not as this workbook.
They come from a different document family: Facets → Enterprise Data Hub, 11 tables, 389
mapping rows. Against §6's five asks they state more:
- the join type, in every join hint (62 of 62);
- the primary key, through an `indexes` marker on 29 rows.

They state less in two places:
- UC source naming: `source_database` + a bare `source_table`, never qualified;
- SK / SCD2: nothing.

The dialect, with field counts, the three placeholder grammars and their coverage, is in
`EDH_E2E_JSON_SCHEMA.md`. The defects, split by origin (extractor vs source workbook), are
in `EDH_E2E_EXTRACTION_DEFECTS.md`. The fabricated fixtures are in
`tests/fixtures/edh_gold_synthetic/`.
