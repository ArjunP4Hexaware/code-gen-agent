# Segmented-mode design (CAQH layout family) — IMPLEMENTED under declared assumptions

**Status change (2026-08-31):** the segmented dialect is implemented
(`src/codegen/extract/segmented.py`), governance-honest — the blockers
below did NOT get guessed; they became explicit, per-feed FAQ
declarations (`record_type_discriminators`, `natural_key_columns`) that
surface in the review layer for human approval, the provenance banner,
and the generation report (ASSUMED flags). With no declaration the v1
refusal fires unchanged, plus a remedy line naming the FAQ path.
Detail-segment rows are the payload (flat-shaped spec); Header/Trailer
rows are file envelope (report-only, never DDL); a workbook Standard
layer the FRD does not scope is parsed and HELD as an escalated-conflict
review card (the FRD governs target layers), never emitted, never
deleted. **The two source-team confirmations below remain OPEN asks** —
`status: confirmed` in the FAQ drops the review gate once they answer.

Design input derived from a **local-only inspection of the real CAQH STTM
workbook** (project 1005034) performed 2026-08-07 under the program's
data rules — only the structural characterization below (sheet/header/
table identifiers, no data-row values) is recorded here. The flat-dialect
extractor (docs/EXTRACTOR_RECON.md) is unaffected and byte-identical.

**Discovered on implementation (2026-08-31):** the real workbook's
`Mandatory Column` / `Primary Key` / `PII` cells carry NO signal at all
(all empty), so the "Mandatory + Primary Key driven" nullability rule
sketched below has nothing to drive it — a third unknown, handled the
same way: the natural key comes only from the FAQ's
`natural_key_columns` declaration (engineer decision, surfaced as an
ASSUMED review item), and the run refuses without it. Also out of scope
until the discriminators are confirmed: the generated reader does not
yet FILTER rows by the assumed discriminator values — the assumption is
surfaced, not silently executed; wiring the filter in is the natural
next step once `status: confirmed`.

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

## Open source-team asks (verbatim from the original blockers — now
## declared assumptions pending their answer, no longer hard blockers)

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
