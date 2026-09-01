# Segmented-mode design (CAQH layout family) — IMPLEMENTED, document-derived

**Status (2026-09-01, corrected):** the segmented dialect is implemented
(`src/codegen/extract/segmented.py`) and the 2026-08-31 build's two "open
source-team questions" are **RETRACTED — the documents answer both**:

1. *Record identification* is stated by the STTM itself: the Trailer's
   "Record Type" row comment reads **"Static text identifying the record
   as the trailer record. Contains the value \*\*\*\*\*\*"** — so trailer
   = record whose first field equals `******`, header = first record,
   detail = all others. Derived with that cell quoted as the citation;
   the FAQ `record_type_discriminators` remains strictly a
   `status: confirmed` OVERRIDE. One soft **CONFIRM** review item
   ("positional header/detail identification per CAQH spec — confirm
   with source team") rides the review flow; it is not an assumption gate.
2. *The "standard-layer contradiction" never existed.* The FRD scopes
   BOTH layers: Structural Metadata states **"Load Strategy STG:
   Truncate and Load"** and **"Load Strategy STD: Append"**, and the
   Technical Metadata Business Rule reads **"Data should be loaded AS IS
   into STG and STD."** The 2026-08-31 build inferred "stage-only" from
   the Target Schema block (which names only `pr_dlk`/`stg_mbr`) instead
   of reading Load Strategy. The STD catalog/schema/tables come from the
   STTM's second target column group (`PR_STD.MBR`), recorded with a
   cited provenance note.

Also settled by the documents: acceptance criterion 2 — "Header, Detail,
Trailer data should be mapped to respective HDR, DTL and TRL tables" —
segments are TABLES in both layers, not file envelope; acceptance
criterion 3 — "Data Type of the fields in Stage and standard should be
STRING except for audit date fields" — an FRD-driven AS-IS switch, not a
CAQH special case; and Technical Metadata Business/Primary/Unique Key =
**None** with truncate/append strategies — no MERGE key exists, so empty
STTM Mandatory/PK columns are FRD-consistent provenance, not an unknown.

**Lessons (also in CLAUDE.md):** assumptions and conflicts must cite the
exact source cells they rest on — a conflict that cannot quote its
evidence is a bug; and "stage-only" was inferred from a schema block
instead of read from Load Strategy — target-layer scope comes from Load
Strategy STG/STD, never from which schemas the Target Schema block
happens to name.

Out of scope (stated, not hidden): the generated reader/segments module
still splits records via `config.segments` — adapting the runtime filter
to the derived positional/marker identification is Option-A-only future
work, pending the source team's confirmation of the CONFIRM item.

Design input derived from a **local-only inspection of the real CAQH STTM
workbook** (project 1005034) performed 2026-08-07 under the program's
data rules — only the structural characterization below (sheet/header/
table identifiers, no data-row values) is recorded here. The flat-dialect
extractor (docs/EXTRACTOR_RECON.md) is unaffected and byte-identical.

## Why v1 rejected this family

The segmented workbook is not a `MAPPING-*`-prefixed variant of the flat
layout — it is a different layout family. The parser's content-based
detection recognizes the family signature (metadata block + band row
and/or per-row Segment column); v1 raised `SegmentedWorkbookError`
unconditionally, v2 routes it to the segmented parser gated on the FAQ
declarations. Everything below is the structural characterization the
implementation follows.

## Layout family characterization

One wide mapping sheet (observed: 136 rows × 31 used columns) plus an
advisory crosswalk sheet; **no** FILE_DETAILS or VERSION_HISTORY sheets.

1. **Key:value metadata block (rows 1–8, col A key / col B value)** —
   plays FILE_DETAILS' role: `File(s)` (multi-line list of name
   patterns), `File Generator`, `File Location`, `LOB`, `File frequency`,
   `Domain`, `Sub-Domain`, `File type`. Unlike the flat dialect the
   **delimiter is stated here** (`File type` reads like
   "txt (pipe delimited |)"), and fixed-width is a representable option.
2. **Band-label row (row 9, merged)** — `Source Layout` (not the flat
   family's `Source File Layout`) | `Stage Layer` | `Standard Layer`.
   Band position is NOT row 1; discovery must scan for it.
3. **Header row (row 10)** — source block (11 cols): `#`, `Field Name`,
   `Data Type`, `Length`, `Field Length / (fixed width)`,
   `Start position / (fixed width)`, `End Position / (fixed width)`,
   `Segment (Ex:Header,Trailer,Detail)`, `PII`, `Comments`,
   `Business Rule`. Stage and Standard blocks (10 cols each, identical
   vocabulary): `Catalog`, `Schema`, `TableName`, `ColumnName`,
   `DataType`, `Mandatory Column`, `Primary Key`, `Field Description`,
   `Table Description`, `Transformations/Data Quality`. Deltas vs flat:
   no NULL-check column (Mandatory lives on the target blocks), `PII` not
   `PHI Field`, a `Catalog` level (three-part table refs), `Primary Key`,
   fixed-width position columns, free-text `Business Rule`.
4. **Per-row `Segment` column** — segment membership per field, values
   spelled out (`Header` 8 fields / `Detail` 101 / `Trailer` 6 observed).
   The `#` numbering **restarts per segment**. Each segment maps to its
   own stage AND standard table pair (`EXT_TPL_CAQH_{HDR,DTL,TRL}` in
   `PR_DLK.STG_MBR` / `PR_STD.MBR`).
5. **Per-segment audit rows** — at the end of each segment block, with
   **empty source-side cells** (not the flat family's `NA`) and empty
   Segment cell. Identities vary per table: Header/Trailer get
   SRC_FILE_NAME + REC_CREATION_TIME + REC_UPDATED_TIME; Detail gets five
   (adds LOB and FILE_TYPE). Cells may carry stray trailing whitespace.
6. **Advisory crosswalk sheet** (`ForReference`-style) — source name →
   stage name → standard name for a related field universe, with a lone
   boolean flag on its record-type row. It does NOT 1:1 index the mapping
   sheet (different field set and different stage names); treat as
   advisory only, pending the source dictionary.

## IR / contract extension sketch

- **Detection & entry:** discover mapping sheets by content, not name —
  scan for a row whose normalized cells include ≥2 band labels (with the
  `Source Layout` variant); header row = band row + 1; the key:value
  block above supplies feed-level facts (format AND delimiter, location,
  frequency, LOB).
- **`MappingRow` additions:** `segment: str | None` (header matched by
  normalized prefix "segment"), `stage_catalog`/`standard_catalog`,
  `primary_key: bool`, `business_rule: str | None`, and fixed-width
  fields (`length`, `start_position`, `end_position`) when the file type
  says fixed-width.
- **`SheetIR` becomes multi-segment:** per-segment (stage, standard)
  table pairs and per-segment audit lists. Audit recognition: empty
  source cell + empty Segment cell within a segment block; trim
  whitespace on identities.
- **Emission:** maps onto the existing contract dialect (`record_segment`
  + `stage_table` per field) — the contract schema needs no change for
  segmentation itself. `Catalog`, `Primary Key`, and fixed-width facts
  have **no contract fields today**: decide whether to extend the dialect
  or drop them with a note before building.
- Mandatory/nullability semantics differ (no NULL-check column; Mandatory
  on target blocks): the flat mapping `null_check`→`nullable` cannot be
  reused as-is; needs its own rule (likely `Mandatory Column` +
  `Primary Key` driven).

## Original blockers (historical — RETRACTED 2026-09-01, see the status
## block above: the documents answer both; one soft CONFIRM item remains)

1. **H/D/T discriminator requires the client source dictionary.** The
   workbook confirms segment MEMBERSHIP per field but cannot confirm the
   discriminator: only the Trailer segment carries an explicit
   record-type field (`TPL_REC_TYPE`), Header/Detail carry none, and the
   literal `H`/`D`/`T` values appear nowhere in the workbook. The
   `config.segments` assumption (record-type as first column of every
   row, values H/D/T) therefore remains unverified — do not build the
   discriminator on workbook evidence alone.
2. **Standard-target contradiction — escalated to the Lead for a human
   decision.** The real workbook's Standard Layer is fully populated
   (per-segment `PR_STD` tables, transformations "Load as is"), while the
   committed CAQH FRD contract's standard target is empty and the
   synthetic STTM contract says `standard: null` (stage-only). One of
   them is wrong; emission must not proceed until the source team /
   Lead resolves which.
