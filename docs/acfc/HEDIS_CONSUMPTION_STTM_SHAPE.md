# HEDIS_CONSUMPTION_STTM_SHAPE — Structural Shape of the HEDIS Stage → Consumption STTMs

> **Purpose**: decide whether CodeGen can read the HEDIS 2.0 Stage → Consumption mapping
> workbooks, and with what. Structural description only, in the style of
> `GOLD_STTM_SHAPE.md`: header labels as spelled, counts, shapes, coordinates. **No document
> values** — no table, column, catalog or schema names, no logic text. Workbooks are cited by
> an anonymous label (`W1`…`W9`), sheets by 0-based position (`sheets[<i>]`).
>
> **Inputs read (2026-10-22, read-only)**: the 9 Stage → Consumption `.xlsx` files of the EDO
> SharePoint HEDIS folder, pulled through the UC connection `d1_dlk_sharepoint`
> (`read_files(..., format => 'binaryFile')` on the Serverless Starter Warehouse) into session
> scratch, never into the repo. openpyxl 3.1.2 (`data_only=True`). The 2 Raw → Stage
> workbooks, the FRDs and the FRD addenda were not read.

---

## 1. The workbooks

| Label | Kind (from the file name) | Sheets | Mapping sheets | Target-column rows | Source tables | Target tables |
| --- | --- | --- | --- | --- | --- | --- |
| W1 | observation feed, custom | 1 | 1 | 180 | 1 | 1 |
| W2 | observation feed, homegrown custom | 1 | 1 | 27 | 3 | 1 |
| W3 | pharmacy, historical | 1 | 1 | 27 | 1 | 1 |
| W4 | medical, institutional custom | 2 | 1 (+ `Addendum`) | 111 | 9 | 3 |
| W5 | medical, professional custom | 2 | 1 (+ `Addendum`) | 111 | 8 | 2 |
| W6 | medical, historical | 3 | 1 (+ version history, + a scratch sheet) | 96 | 1 | 1 |
| W7 | pharmacy, custom | 1 | 1 | 27 | 4 | 1 |
| W8 | all XREF tables | 14 | 13 (+ `CONTENTS`) | 251 | 1 per sheet | 1 per sheet |
| W9 | member demographics | 1 | 1 | 71 | 26 | 1 (+ 1 alternate) |

901 target-column rows in all. Row = one consumption column; a row's "data" is the source
column(s) and the logic that fills it.

## 2. Families

Five header shapes. All share the same core: a source table, a source column, one or two
logic columns, a consumption table, a consumption column, a data type.

### H1 — flat column list (W3, W6, W7)

Header in r1 (W3, W6) or r2 (W7), no band row. W3:
`Stage Table` | `Stage column Name` | `Stage Logic` | `CONSUMPTION TABLE NAME` |
`CONSUMPTION COLUMN NAME` | `Data Type (max length)` | `Supported Products` | `Description` |
`Valid Values`. W6 spells them `Stage Table Name ` / `Stage Column Name ` (trailing spaces) /
`Stage Table Logic` / `Consumption Field Name `. W7 has TWO logic columns:
`Existing derivation Logic` | `New Derivation Logic`.

### H2 — banded Standard|Stage / Consumption (W1, W2)

r1 = band labels (`Standard` + `Consumption`, or `Stage` + `Consumption`), r2 = headers:
`Standard Table Name` (W2: `Stage Table Name`) | `Standard Column Name` |
`Prospective Transformation Logic` | `Consumption Table Name` | `Column Name` | `Description` |
`Data Type (Max length)`. W2 has an empty spacer column between the logic and the
consumption band. W1 carries 32 merges (vertical blocks).

### H3 — mapping + procedural Addendum (W4, W5)

`Mapping` sheet: r1 = a confidentiality banner + band labels `Current Logic` / `New Logic`; r2 =
ONE long prose cell (merged A:B) stating a row-pivot rule for the detail records; r3 =
headers `STAGE TABLE NAME` | `STAGE COLUMN NAME` | `Existing Stage Table Logic` |
`New derivation Logic` | `Consumption Table Name` | `Field Name ` | `Data Type (max length)` |
`Supported Products` | `Description` | `Valid Values`. 16 vertical merges in A–D (blocks of
10–12 rows share one source / logic cell).

`Addendum` sheet: 114 numbered steps, header r2: `Step` | `SP (SQL Step Reference)` |
`Object/Title` | `Changes part of Oct 2022 Release` | `Description` | `Implemented Logic …` |
`Tables Headers(…)` | `HEDIS 2_0 table headers(…)` | `Intermediate Table` | `HEDIS 2.0 source`.
The `Implemented Logic` cell is labelled text (`Source Table :` / `Reference :` /
`Join Table :` / `Join Condition :` / `Filter:`), filled on 108 steps; the two header
columns hold SELECT statements (107 / 106 steps); every step names an intermediate table;
`HEDIS 2.0 source` is empty. This is a stored-procedure chain written out step by step.

### H4 — one sheet per table + a contents sheet (W8)

`CONTENTS`: `File name` (a file pattern) | `Consumption Table name` |
`LOAD CRITERIA (STAGE_TO_CONSUMPTION)` (every row "truncate and load"). Then one sheet per
consumption table, header `STAGE TABLE NAME ` | `STAGE COLUMN NAME` | `STAGE LOGIC` | (spacer) |
`CONSUMPTION TABLE NAME ` | `CONSUMPTION COLUMN NAME ` | `DATA TYPE (MAX Length)`. Drift:
header in r2 on 12 sheets, r3 on 1; the block starts in column A on 10 sheets, B on 3 (one with a
`PROCESS 1` label in A1); 5 sheets carry a free-text note to the right of the header.
Audit rows at the bottom: no source, logic "hardcoded" or "ETL generated".

### H5 — member, two targets (W9)

Header r1: `STAGE TABLE NAME` | `STAGE TABLE TARGET COLUMN NAME` | `Logic` |
`Logic for impacted Lob in prospective` | `Consumption Table Name` |
`Consumption Table Name for impacted Lob in prospective` | `Consumption ` |
`Data Type (max length)` | `Supported Products` | `Description` | `Valid Values`. Two logic
columns AND two target-table columns (a per-LOB alternate target). Used range runs to FN
(stray cells far right). 22 of 71 rows name several source tables / columns in one cell
(newline-separated).

## 3. How the logic is written

Each logic cell classified by a keyword pass (approximate; for the shape, not for a reader):

| | direct ("Direct Map", "Direct move", "Move as is") | hardcoded / null / ETL-generated | lookup / join / SQL | "Refer FRD / step N" | other prose | blank |
| --- | --- | --- | --- | --- | --- | --- |
| W1 | 9 | 153 | 4 | 0 | 14 | 0 |
| W2 | 9 | 9 | 3 | 5 | 1 | 0 |
| W3 | 8 | 2 | 5 | 0 | 7 | 5 |
| W4 (new logic) | 5 | 36 | 12 | 0 | 11 | 47 |
| W5 (new logic) | 6 | 41 | 11 | 0 | 13 | 40 |
| W6 | 9 | 15 | 1 | 47 | 22 | 2 |
| W7 (new logic) | 7 | 5 | 6 | 0 | 8 | 1 |
| W8 (13 sheets) | 195 | 36 | 0 | 0 | 0 | 20 |
| W9 (`Logic`) | 5 | 19 | 16 | 17 | 12 | 2 |

Notes:
- The blanks of W4 / W5 sit under the vertical merges: openpyxl gives the value to the
  top-left cell only, so a reader must fill a merged block down before reading it.
- W8's blanks are audit rows with no logic (sheets whose audit rows carry only a type).
- "Refer FRD / step N" points into the FRD or an FRD addendum (the member crosswalk /
  exclusion procedure addenda are "Stage to Consumption" workbooks of their own): for W6 and W9
  the FRD side is an input, not optional.
- Two logic columns (W4, W5, W7, W9): the second ("New" / "prospective") differs from the
  first on some rows; which one to build is a question for the owner.

## 4. Other shape facts

- **Data types are SQL Server vocabulary** on the claims / member workbooks (`varchar(n)`,
  `nvarchar(n)`, `bit`, `datetime`, `integer`, `decimal (p,s)` with a space), and Spark
  vocabulary (`string`, `timestamp`) on 5 of W8's sheets. Audit rows set a user column to a
  hardcoded schema-owner literal. Both point at a SQL Server consumption target for part of
  the set — the target platform is a question (§6).
- **Source-table cells**: three-part names on some workbooks, bare names on others, trailing
  spaces, and (W4, W5, W7, W9) several tables in one cell.
- **Source-column cells**: `<column> as <alias>` on W4 / W5 / W7; several columns per cell
  (newline-separated) on W4 / W5 / W9; empty when the value is derived.
- **Extra per-column metadata** none of the ingestion contracts carry: `Supported Products`,
  `Description`, `Valid Values` (allowed codes, or a date format).

## 5. Fit with what CodeGen has

- Not the ingestion path (FRD + Raw→Stage STTM → DDL + IIG): no landing file, no bands per
  layer, no IIG rows.
- `codegen.contracts.gold.GoldContract` (post77) holds most of a row: source table,
  expression, join, filter, target type / length, load mode, primary key, with the
  filled / proposed / QUESTION rule. Missing: a second logic version, a per-LOB alternate
  target, several source columns per row, supported products / valid values / description,
  and anything procedural (W4 / W5's step chain with intermediate tables).
- `codegen.layouts.edh_e2e` is a different family; HEDIS needs its own reader (one module, five
  header shapes above, found by the same label synonyms + content-driven header search the
  STTM extractor uses).

Rough feasibility by family:

| Family | Rows | What a deterministic reader + emitter can produce |
| --- | --- | --- |
| H4 (W8) | 251 | Nearly all of it: target DDL + a truncate-and-load SELECT per table; audit columns by rule. |
| H2 (W1, W2) | 207 | Most of it: direct / null / audit columns written; lookups and prose = one QUESTION each, cell quoted. |
| H1 (W3, W6, W7) | 150 | DDL + direct / hardcoded columns; the many "Refer FRD" and prose rows = QUESTIONs unless the FRD steps are read too. |
| H5 (W9) | 71 | As H1, plus the multi-table source joins (a QUESTION per row naming the tables). |
| H3 (W4, W5) | 222 + 228 steps | The `Mapping` sheet as H1; the `Addendum` is existing SQL to TRANSLATE (T-SQL → Spark SQL), a separate task from mapping-to-code. |

## 6. Open questions (for the HEDIS / EDO owners)

1. **What does prod deploy for one Stage → Consumption load?** A notebook, a SQL script, a
   stored procedure, a framework metadata row, a DLT pipeline? One deployed example per family
   (best: an XREF table and one claims table) is the golden to score against.
2. **Target platform**: Databricks (`HEDIS_DATA` as a UC schema) or SQL Server for the claims /
   member tables? The type vocabulary says SQL Server for part of the set.
3. **Existing vs New logic columns**: build "New" always, or per LOB?
4. **The FRD side**: for "Refer FRD step N" rows, is the FRD (or its addendum) the authority, and
   is it maintained alongside the STTM?
5. **The W4 / W5 Addendum**: is the step chain the spec to re-implement, or the current
   implementation to migrate as is?
