# Multi-table feeds — one STTM, several tables; one feed, several files

Branch `feature/multi-table` (cut from `feature/iig-first` at be38f05).
Status: **Phase A (this document) and Phase B (fixture `fixtures/acfc_shapes/pair_4/`)
done; Phase C in progress — status per step in §6.** Every Phase C step keeps the
pair-1 acceptance (`tests/test_m4_acceptance.py`) byte-identical, the pair-4
golden consistent and `tests/test_m5_rfc_package.py` green.

## 1. The model (framework owners, 2026-10-07)

The IIG describes three movements:

| Movement | What it is | IIG sheet(s) |
| --- | --- | --- |
| SQL Server metadata → UC Delta | the metadata rows that DEFINE every table and pipeline; the UC Delta tables are created FROM those rows | every sheet (the INSERTs are the client's "DDL") |
| Source → Stage | one inbound file into the stage DETAIL table | `ADLS_DELTA_INGESTION_DETAILS` (+ `FILE_ADLS_INGESTION_DETAILS` for the O-drive → ADLS copy, + the `DATA_QUALITY_RULES` split rule) |
| Stage → Standard | one stage table into its standard table | `STGDELTA_STDDELTA_INGESTION_DET` |

Rules stated by the owners (2026-10-07; the row rules and the catalog rule were
amended the same evening and replace the earlier record-type phrasing):

1. **Tables = the distinct (catalog, schema, table) triples found in each STTM
   band.** A segment never implies a table by itself; the `TableName` cell
   decides. Pair 1's three segments (HDDR / DET / TRLR) map to one triple →
   one table; pair 4's three segments map to three triples → three tables.
2. **Files = the distinct `SRC_FILE_NAME` patterns the feed receives.** If the
   header block's file pattern contains a LOB-varying token and the block
   lists N LOBs, it expands to N files (one per LOB, partition = LOB);
   otherwise there is one file per listed pattern (LOB blank, partition `NA`).
   Pair 1: four patterns, no LOB → four files. Pair 4: one pattern
   parameterised by LOB, six LOBs → six files.
3. **`ADLS_DELTA_INGESTION_DETAILS` rows = files**, each targeting the DETAIL
   table (or the sole table).
4. **`STGDELTA_STDDELTA_INGESTION_DET` rows = tables**: source = the table's
   stage definition (delta, stage catalog / schema), target = its standard
   definition (standard catalog / schema, `Append`, the standard container).
5. **The header/trailer split is a `DATA_QUALITY_RULES` row** of `RULE_CLASS`
   `LoadHeaderAndTrailerToSeparateTablesRule` (`SOURCE_COLUMN` = the header
   columns, `INPUT_PARAM` = the row's `SRC_FILE_NAME`, `TARGET_COLUMN` =
   `catalog,schema,hdr_table,…`), emitted ONLY when the header / trailer
   segments land in a DIFFERENT table from the detail. Pair 1 gets none; pair
   4 gets one per ADLS object.
6. **Catalogs come from each table's own band.** The STTM main sheet carries
   two column bands per row — a Stage band (catalog like `PR_DLK`, schema
   `stg_*`) and a Standard band (catalog like `PR_STD`, schema without the
   `stg_` prefix) — each with its own Catalog / Schema / TableName /
   ColumnName / DataType / Mandatory / Primary Key. A table's stage_def and
   standard_def take catalog and schema from their own band, never from the
   other band and never from a profile default when the band states one.
   **Catalog precedence (decision 2026-10-07): STTM band → FRD label →
   `default_catalog`**; a band and an FRD label that disagree
   (case-insensitively) raise `catalog_conflict:<layer>` naming both, and the
   band is used. The
   standard_def comes from the Standard band; a `ForReference`-style STG→STD
   sheet (band labels `<client> - Source`, `STG - Dest 1`, blank, blank,
   `STD - Dest2`) is a secondary source.
7. **The STTM states LOGICAL catalogs; the environment maps them.**
   `conventions.catalog_map` in the environment overlay (d1: `PR_DLK` →
   `d1_dlk`, `PR_STD` → `d1_std`; prod: identity) is applied to every emitted
   catalog, and the cell tooltip cites the mapping. Keys match
   case-insensitively; a mapped catalog is emitted in lowercase. `default_catalog` is the
   fallback only for a band whose Catalog is blank. Every table-definition
   artefact (metadata inserts, the CREATE reference text) is labelled with its
   MAPPED three-part name, so stage and standard definitions are never
   ambiguous.
8. **"DDL" at this client means the metadata INSERT rows** that define a table
   in SQL Server; the UC Delta tables are created from those. The `CREATE
   TABLE` text stays as a reference artefact.

## 2. Where the code assumes one table per feed (or one file per pattern)

There is no `parse.py` in the repo; the STTM "parser" is
`src/codegen/extract/generic.py` (content-driven reader, the ACFC families) +
`src/codegen/extract/segmented.py` (the `MAPPING-` H/D/T dialect) + the layout
recognizer `src/codegen/layout/discover.py`. They are listed under "STTM
readers". What already works is listed too — the contract layer is further
along than the IIG layer.

### Already multi-table (keep)

- `contracts/resolved.py::SegmentSpec` carries `stage_table`, `standard_table`
  and `audit_columns` per segment; `resolve/resolver.py::_resolve_segments`
  builds one `SegmentSpec` per Header / Detail / Trailer with its own stage
  AND standard table (the CAQH segmented dialect, 2026-09-01).
- `extract/generic.py::_build_feed` sets `SttmField.stage_table` /
  `standard_table` from each ROW's table cell when the sheet is segmented
  (line ~633), so per-segment tables reach the contract.
- `metadata_sheet.py::_stg_std_row` (iig_v1 only) already writes one
  STG→STD leg per segment table.
- `metadata_template.py::_fixed_width_handler` already writes one row per
  segment with that segment's `TGT_TABLE`.

### Single-table / single-object assumptions

| File · function | Assumption | Consequence for pair 4 |
| --- | --- | --- |
| `metadata_template.py::_distinct_fields` | flattens EVERY segment's fields into ONE column list (dedup by stage column) | HDR / DTL / TRL columns merged into one list; shared names (`RECORD_TYPE`, `FILE_NAME`) collapse |
| `metadata_template.py::_adls_delta` | `stage = spec.detail_segment.stage_table` (right table) but `SRC_COLUMNS` / `TGT_COLUMN_NAMES` / `TGT_DATA_TYPE` from `_distinct_fields` (all segments); rows = `spec.file_name_patterns` (one per PATTERN, never × LOB); `LOB = ", ".join(feed.lobs)` on every row; `TGT_PARTITION_COLUMN` / `_VALUE` = the template constant `NA` | 1 row instead of 6; every LOB on the one row; header/trailer columns in the DTL column list; no partition |
| `metadata_template.py::_stg_std` | ONE row: `spec.detail_segment.stage_table` → `spec.standard_table`; standard columns = every segment's `f.standard_column` / `f.standard_datatype` merged | 1 row instead of 3; the three tables' standard columns merged into one list |
| `metadata_template.py::_dq_rules` | rule kinds `date_format` / `data_type_cast` only, computed over `_distinct_fields`; `INPUT_PARAM` = the qualified DETAIL stage table; objects = file patterns | no header/trailer split rule kind exists |
| `metadata_template.py::_pipeline_schedule`, `_notebook_details` | rows come only from overlay `template_rows` (the client's inventory); no structural rule | pair 4 without an inventory overlay gets ONE blank row, not the four movement rows |
| `metadata_template.py::_file_adls` | ONE row per feed | per-file copy rows impossible |
| `metadata_template.py::template_tab_rows` | dispatcher is per FEED; a builder sees `(feed, spec)` and nothing finer | no per-file / per-table iteration point |
| `emit/framework.py::_combined_ddl_text` | dedups the columns of ALL segments into ONE stage `CREATE` (`spec.detail_segment.stage_table`) and ONE standard `CREATE` (`spec.standard_table`); per-segment standard tables ignored | 2 CREATEs instead of 6, both wrong-shaped |
| `emit/framework.py::_description_map` | column name → description across segments, first wins | HDR / TRL `FILE_NAME` comments collide (cosmetic) |
| `emit/framework.py::emit_framework` | payload built for `specs=[spec]` and filtered per feed (fine); `frd_tables` banner from segments (fine) | — |
| `emit/dml.py::_VARIABLE_COLUMNS` / `_cell_sql` | EVERY row of EVERY sheet gets the same `@PIPELINE_ID`, `@GROUP_ID`, `@OBJECT_ID` | 6 ADLS rows share one `OBJECT_ID` → primary-key collision on (GROUP_ID, OBJECT_ID, PIPELINE_ID); 4 schedule rows share one `PIPELINE_ID`. **Latent today:** pair 1's golden has 4 ADLS objects and 4 pipelines, and the DML already collapses them |
| `iig_review.py` | none — it renders whatever rows the payload holds. Its `owner_for(sheet, column, reason)` has no class between "engineer" and "BSA": environment values and engineer-assigned ids are both `engineer` | owner colours cannot tell "fill from the environment overlay" from "engineer assigns" |
| STTM readers · `extract/generic.py::_band_constant` | the sheet's stage / standard catalog, schema and table = the DOMINANT cell of each band column; per-row catalog / schema were dropped | a row whose catalog or schema differs from the band's dominant value lost it — **fixed in step 1** (`SttmField.stage_catalog` / `stage_schema` / `standard_catalog` / `standard_schema`, written only when the row differs) |
| STTM readers · `extract/generic.py::_rule_columns` | not-null / mandatory / PHI = the DETAIL segment's fields only | HDR / TRL primary keys and mandatory flags are dropped |
| STTM readers · `extract/generic.py::_read_auxiliary` | every non-mapping sheet is an auxiliary sheet, read by signature and IGNORED by the contract | the `ForReference` STG→STD sheet is not read — acceptable now that it is a SECONDARY source (rule 6); a cross-check is future work |
| STTM readers · `extract/generic.py` (primary key) | the Primary Key column of any band was never read; `natural_key_columns` = the not-null columns | **fixed in step 1** (`SttmField.primary_key`, `standard_primary_key` / `standard_mandatory` when the Standard band differs) |
| STTM readers · `layout/discover.py::_segmented_family` | raised an uncaught `KeyError: 'source'` when a band row shared only SOME of the family's labels (`Stage Layer` under a plain `Source`) instead of falling through as its docstring says | pair 4 crashed discovery — **fixed in step 1** (falls through to content-driven discovery, which reads both bands) |
| STTM readers · header-block LOB | the meta row `LOB` is read as text and never split; LOBs come from the FRD only (`FrdFeed.lobs`) | the STTM's 6 codes reach nothing |
| `contracts/resolved.py::ResolvedFeedSpec` | `file_name_patterns: list[str]`, `lobs: list[str]` are FEED-level; no file ↔ LOB association | the files × LOB rows have no model to come from |

## 3. New data model

```
Feed                                   (one ResolvedFeedSpec — unchanged identity)
├── facts            domain, sub_domain, source, frequency, file_format, delimiter,
│                    landing (File Location), stage / standard load strategy
├── files[]          ONE per SRC_FILE_NAME pattern (rule 2)       codegen.resolve.files.FeedFile
│     pattern        the pattern as stated, the LOB token substituted
│     lob            the LOB of an expanded file; None = not a per-LOB file
│     partition      (LOB, <code>) for an expanded file, else NA
│     provenance     the cell(s) the file rests on
└── tables[]         ONE per distinct stage (catalog, schema, table) triple (rule 1)
      segments       the segments whose rows land in it ([] on a flat sheet)
      stage_def      TableDef — catalog / schema / table from the STAGE band,
                     columns (name, type, mandatory, primary key), audit columns
      standard_def   TableDef | None — from the STANDARD band of the same rows
                     (rows whose Standard band is blank are not carried)
                                                      codegen.contracts.tables.SttmTable
```

**Step 1 (done).** `SttmTable` / `TableDef` / `ColumnDef` are DERIVED from an
`SttmFeed` (`codegen.contracts.tables.feed_tables`), never stored, so every
existing STTM contract JSON is byte-identical. What the derivation needs and the
contract did not carry is on `SttmField`, each written only when it says
something (`exclude_defaults`): `primary_key`; `stage_catalog` /
`stage_schema` / `standard_catalog` / `standard_schema` when the row's band
cell differs from the band's dominant value; `standard_mandatory` /
`standard_primary_key` when the Standard band's cell differs from the Stage
band's. A table's audit columns are its segments' (`segmented.segment_audit`)
when the segmented extractor stated them, else the feed's. A stage triple whose
rows name two standard triples is an error naming both (one standard_def per
table). `detail_table(tables)` = the table holding the Detail segment, else
the sole table; `split_tables(tables)` = the header / trailer tables that are
NOT the detail table (rule 5's condition).

Files: `codegen.resolve.files.expand_files(patterns, lobs, tokens)` applies
rule 2 (`extractor.lob_tokens`, case-insensitive: `<LOB>`, `{LOB}`,
`[LOB]`); `header_block_files(sttm_feed, …)` reads the header block's
`File(s)` and `LOB` meta rows (`split_lobs`: `,` `;` `/` or newline). A
pattern carrying the token while no LOB is listed stays ONE file with the
token unexpanded and the flag `lob_token_without_lobs:<pattern>`.

**Step 2 (done).** `conventions.catalog_map` (logical → environment catalog;
empty = identity; case-insensitive keys, lowercase output). The resolver
picks each table's stated catalog band-first (`stated_catalog`: band → FRD
label, `catalog_conflict:<layer>` when both are stated and differ; a segment's
rows may state their own band catalog / schema), then maps every catalog it
puts on a
`ResolvedTable` and keeps the stated one on `ResolvedTable.catalog_logical`;
the IIG catalog cells and the qualified names (DDL, fixed-width `TGT_TABLE`,
DQ `INPUT_PARAM`) therefore carry the mapped name, and a catalog cell's
tooltip cites `catalog_map <logical> → <mapped>`. With a non-empty map, a
stated catalog that has no entry is written as stated and flagged
`catalog_unmapped:<layer> — <catalog>`. `default_catalog` stays the fallback
for a blank band (it is already an environment catalog and is not mapped).

**Step 3 (done).** `ResolvedFeedSpec.files` (the resolver applies rule 2 to the
resolved patterns; the LOBs are the STTM header block's when it lists any, else
the FRD's). The iig_v2 builders group the resolved segments by stage triple
(`metadata_template._table_groups`, the resolved-side twin of
`feed_tables`):

- `ADLS_DELTA_INGESTION_DETAILS` = one row per file into the detail (or sole)
  table: `OBJECT_ID` = the file's position (1..n, the framework convention of
  METADATA_DB_SEMANTICS §5 — a cited convention cell, the one way a builder may
  fill an `always_blank` column), `OBJECT_NAME` / `SRC_FILE_NAME` from the
  pattern with its date placeholder written as `*`
  (`file_pattern_wildcards`: `CCYYMMDD`, `YYYYMMDD`, … → `*`), `LOB` /
  `TGT_PARTITION_VALUE` = the file's LOB and `TGT_PARTITION_COLUMN` =
  `lob_partition_column` (`LOB`) for a per-LOB file; a file that is not
  per-LOB gets `LOB` blank (a *decided* blank — not an open review cell) and
  the template's `NA` partition. Columns / types / mandatory / key = the
  detail table's (its Stage-band Primary Key cells; none = the contract's
  natural key, as before).
- `STGDELTA_STDDELTA_INGESTION_DET` = one row per table with a standard
  definition: source = the stage table, target = the standard table (mapped
  catalog), `OBJECT_NAME` = the table name, `LOB` = the per-LOB files' codes
  joined (blank, decided, when there are none), `TGT_PRIMARY_KEY` = the
  Standard band's Primary Key cells, else `NA` (the pair-1 golden's value).
  `OBJECT_ID` stays blank (the brief sequences ADLS / DQ objects only).
- `{landing_rel}` / `{domain_path}` strip the LANDING container
  (`ADLS_DELTA_INGESTION_DETAILS.SRC_CONTAINER_NAME`) first: a stage →
  standard sheet's own `SRC_CONTAINER_NAME` is the stage container.

Still to come (steps 4–7).

## 4. Row-count rules per sheet

`F` = files (rule 2), `T` = tables (rule 1), `R` = DQ rule kinds that fire per
object.

| Sheet | Rule | pair 1 (golden) | pair 4 (golden) |
| --- | --- | --- | --- |
| `DATA_FACTORY_PIPELINE_SCHEDULE` | 4: grand master, master, file→stage child, stage→standard child (fewer only when the engineer reuses an existing master — open Q4) | 4 | **4** |
| `FILE_ADLS_INGESTION_DETAILS` | one per file (F) — or one wildcard row per root (open Q5) | 1 | 6 *(not goldened)* |
| `ADLS_DELTA_INGESTION_DETAILS` | F; every row targets the detail (or sole) table | 4 (LOB blank, partition `NA`) | **6** (LOB = partition value) |
| `STGDELTA_STDDELTA_INGESTION_DET` | T (tables with a standard_def) | 1 | **3** |
| `DATA_QUALITY_RULES` | F × R; R includes the split rule only when header / trailer land in a table other than the detail | 4 × 2 = 8 (no split rule) | **6 × 1 = 6** |
| `ADLS_FIXED_WIDTH_HANDLER` | one per segment, fixed-width files only | 3 | 0 |
| `DATABRICKS_NOTEBOOK_DETAILS` | one per notebook the children invoke (inventory overlay) | 3 | *(not goldened)* |
| `EMAIL_TEMPLATE_CONFIG` | 2 (Success, Failed) | 2 | 2 *(not goldened)* |

Pair 4's DQ count rests on two readings: one split row per ADLS object
(DQ rows key on GROUP_ID / OBJECT_ID / SEQUENCE_NO and the pair-1 golden
repeats its rules per object; `INPUT_PARAM` = that object's file name), and
no date / cast rule (pair 4's main sheet has no Load Rules column and its
stage columns are all `String`). Both are open Q2 / Q3.

## 5. Owner map

Classes: **per-file** (differs per inbound file), **per-table** (differs per
HDR / DTL / TRL), **per-feed** (one value for the feed, from the FRD / STTM
header block), **environment** (differs per workspace — the environment
overlay), **convention** (framework vocabulary, template shapes, audit
conventions — the same for every feed), **engineer-assigned** (ids, names and
technical choices no document states). A class names who or what determines the
value: an engineer-assigned id still VARIES per file (ADLS / DQ `OBJECT_ID`) or per
table (STGDELTA `OBJECT_ID`), and a convention path shape still embeds the table
name. Catalog and schema cells are **per-table**: each table's own band states them (rule
6); the catalog value is that LOGICAL catalog mapped by the environment's `catalog_map`
(rule 7), so the cell has an input (the band) and an environment mapping. The machine-readable copy for the four
goldened sheets is `fixtures/acfc_shapes/pair_4/golden/IIG_EXPECTED.yaml`
(`columns:`); a test keeps the lines below and that file in agreement.
Mapping to today's `iig_review` owners: environment → `engineer` (should be
its own owner — Phase C), engineer-assigned → `engineer`, convention →
`engineer_confirms`, CREATED_BY / UPDATED_BY → `bsa` (the RFC number),
CREATED_DATE / UPDATED_DATE → `set_at_load`.

### DATA_FACTORY_PIPELINE_SCHEDULE

- **per-file:** —
- **per-table:** —
- **per-feed:** PIPELINE_FREQUENCY
- **environment:** —
- **convention:** PIPELINE_DESCRIPTION, NO_OF_CYCLE_PER_DAY, DAY_OF_SCHEDULE, ACTIVE_FLAG, ACTIVE_END_DATE, ESTIMATED_START_TIME, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** PIPELINE_ID, PIPELINE_NAME, PARENT_PIPELINE_ID, ACTIVE_START_DATE, APPLICATION_NAME, CREATED_BY, UPDATED_BY

### ADLS_DELTA_INGESTION_DETAILS

- **per-file:** OBJECT_ID, OBJECT_NAME, LOB, SRC_FILE_NAME, TGT_PARTITION_VALUE
- **per-table:** SRC_COLUMNS, SRC_DATA_TYPE, MANDATORY_FIELD_LIST, TGT_DATABASE_NAME, TGT_TABLE_NAME, TGT_COLUMN_NAMES, TGT_DATA_TYPE, TGT_RJT_TABLE_NAME, TGT_PRIMARY_KEY
- **per-feed:** DOMAIN, SUBDOMAIN, SOURCE, FREQUENCY, SRC_ADLS_PATH, SRC_FORMAT, SRC_FILE_DELIMITER, HEADER_FLAG, FILE_HEADER_FLAG, FILE_FOOTER_FLAG, TGT_LOAD_OPTION, TGT_PARTITION_COLUMN, RECYCL_ENBL_FLG
- **environment:** SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, SRC_CONTAINER_NAME, TGT_CONNECTION_ID, TGT_CONTAINER_NAME
- **convention:** CLAIM_TYPE_ID, ACTIVE_FLAG, SRC_REC_LNGTH, SRC_COL_LNGTH, SRC_COL_STRT_END_INDX, SRC_ADLS_ARCHVL_PATH, SRC_COMPRESSION, MULTILINE_FLAG, SCHEMA_DRIFT_FLAG, TGT_ADLS_PATH, TGT_FORMAT, TGT_RJT_ADLS_PATH, RECYCL_TBL_NM, RECYCL_ADLS_PATH, RECYCL_RETN_DAYS, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** GROUP_ID, PIPELINE_ID, MAPPING_EXPRESSION, CREATED_BY, UPDATED_BY

### STGDELTA_STDDELTA_INGESTION_DET

- **per-file:** —
- **per-table:** OBJECT_NAME, SRC_TABLE_NAME, SRC_CATALOG_NAME, SRC_SCHEMA_NAME, SRC_COLUMNS, SRC_DATA_TYPE, TGT_CATALOG_NAME, TGT_SCHEMA_NAME, TGT_TABLE_NAME, TGT_COLUMN_NAMES, TGT_DATA_TYPE, TGT_RJT_TABLE_NAME, TGT_PRIMARY_KEY
- **per-feed:** DOMAIN, SUBDOMAIN, SOURCE, FREQUENCY, LOB, TGT_LOAD_OPTION
- **environment:** SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, SRC_CONTAINER_NAME, TGT_CONNECTION_ID, TGT_CONTAINER_NAME
- **convention:** ACTIVE_FLAG, SRC_ADLS_PATH, SRC_FORMAT, SRC_ADLS_ARCHVL_PATH, TGT_ADLS_PATH, TGT_FORMAT, TGT_RJT_ADLS_PATH, TGT_PARTITION_COLUMN, TGT_PARTITION_VALUE, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** GROUP_ID, OBJECT_ID, PIPELINE_ID, CREATED_BY, UPDATED_BY

### DATA_QUALITY_RULES

- **per-file:** INPUT_PARAM
- **per-table:** SOURCE_COLUMN, TARGET_COLUMN
- **per-feed:** —
- **environment:** —
- **convention:** SEQUENCE_NO, RULE_TYPE, RULE_CLASS, ACTIVE_RULE_FLG, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** GROUP_ID, OBJECT_ID, CREATED_BY, UPDATED_BY

### Sheets not goldened for pair 4 (classes for Phase C)

- `FILE_ADLS_INGESTION_DETAILS` — per-file: OBJECT_ID, SRC_ROOT_DIR (when
  per file); per-feed: DOMAIN, SUBDOMAIN, TGT_ADLS_PATH; environment:
  SRC_CONNECTION_ID, TGT_CONTAINER_NAME, TGT_STORAGE_ACCOUNT_NAME; convention:
  SOURCE_TYPE, COPY_START_TIME_OFFSET_IN_MINUTES, audit dates;
  engineer-assigned: GROUP_ID, PIPELINE_ID, SRC_EXTRACT_START_TIME, audit by.
- `DATABRICKS_NOTEBOOK_DETAILS` — environment: DATABRICKS_WORKSPACE_URL,
  DATABRICKS_WORKSPACE_SECRET, DATABRICKS_CLUSTERID, CLUSTER_DETAILS_ID;
  per-feed: TGT_REFRESH_TYPE (by `_layer`); engineer-assigned: PIPELINE_ID,
  PIPELINE_NAME, GROUP_ID, PROCESS_NAME, DATABRICKS_NOTEBOOK_PATH / NAME,
  DQ_NOTEBOOK_PATH; convention: SEQ_NM, ACTIVE_FLAG.
- `EMAIL_TEMPLATE_CONFIG` — convention: STATUS, ACTIVE_FLAG; per-feed:
  TEMPLATE_NAME, PROCESS_NAME, SUBJECT, BODY; environment: SENDER_EMAIL,
  EMAIL_TO, EMAIL_CC; engineer-assigned: TEMPLATE_ID.
- `ADLS_FIXED_WIDTH_HANDLER` — per-table: SEGMENT, COL, LEN, start_ind,
  TGT_TABLE; convention: the rest (fixed-width files only).

## 6. Phase C — the order, and what each step must show

Each step: tests, ruff, scrub, commit; pair-1 acceptance byte-identical, the
pair-4 golden consistent, `test_m5_rfc_package` green.

1. **STTM parser — DONE.** Both bands → `SttmTable {stage_def, standard_def}`
   grouped by distinct triple; `Feed.files` from the header block per rule 2.
   Unit tests on the pair-1 and pair-4 shapes, a single-pattern-no-LOB case
   and a two-LOB case (`tests/test_multi_table_step1.py`).
2. **`catalog_map` — DONE.** Config + overlays (`config/overlays/acfc_env.yaml`
   d1 map; the pair-1 overlay maps identity so its golden stays byte-identical;
   the pair-4 overlay maps `PR_DLK` / `PR_STD` to `d1_dlk` / `d1_std` and
   carries a DIFFERENT `default_catalog` so the golden proves the fallback is
   not used). Wired into the resolver's `ResolvedTable` catalogs, hence
   `qualified_names`, the DDL and every IIG catalog cell
   (`tests/test_multi_table_step2.py`).
3. **ADLS rows = files; STGDELTA rows = tables — DONE** (pair 4: 6 and 3,
   cell for cell as the golden; pair 1: 4 and 1;
   `tests/test_multi_table_step3.py`).
4. **`DATA_QUALITY_RULES` header/trailer row** under rule 5's condition.
5. **`DATA_FACTORY_PIPELINE_SCHEDULE`: four rows** (grand master, master,
   file→stage, stage→standard), ids left to the engineer, names from the
   naming convention.
6. **`metadata_inserts.sql`** — INSERT statements per sheet from the same cells
   as the IIG; the CREATE TABLE text stays as a reference artefact, now one
   block per table labelled with its mapped three-part name. `emit/dml.py`
   already writes `config_inserts_<env>.sql` from the payload; this step must
   first replace the ONE `@OBJECT_ID` / `@PIPELINE_ID` / `@GROUP_ID` per
   script with one variable per row role — the latent collision in §2.
7. **`scripts/iig_scorecard.py` over all sheets**, matching STGDELTA rows by
   table and ADLS rows by file pattern.

## 7. Open questions (for the framework owners)

1. `TARGET_COLUMN` of the split rule was given as `catalog,schema,hdr_table,…`
   — is the continuation `trl_table` (the golden assumes
   `catalog,schema,hdr_table,trl_table`)? Are the trailer's columns named
   anywhere (`SOURCE_COLUMN` lists the header columns only)?
2. One split-rule row per ADLS object (6 for pair 4), or one per group?
3. Does a delimited feed whose stage is all-`String` get a `DataTypeCastRule`
   on the stage → standard leg (where the types change), and on which sheet?
4. Are the grand master and master new rows per feed, or existing pipelines a
   feed's children attach to?
5. `FILE_ADLS_INGESTION_DETAILS`: one row per file, or one wildcard row per
   root folder?
6. `HEADER_FLAG` / `FILE_HEADER_FLAG` / `FILE_FOOTER_FLAG` when header and
   trailer are split by the DQ rule: `N` (pair-1 analogy — a rule does the
   split) or `Y` (the walkthrough: "if your file is having a header")? Left
   open in the golden.
7. `STGDELTA_STDDELTA_INGESTION_DET.LOB` for a table that holds every LOB:
   the comma-joined codes (golden), blank (pair-1 golden) or `ALL`?
8. `STGDELTA_STDDELTA_INGESTION_DET.OBJECT_NAME`: the table name (golden,
   "based on the table which we are creating", METADATA_DB_SEMANTICS §7) or a
   free engineer token (pair 1's `Accumulator_accumclient`)?
9. The real `ForReference` sheet's geometry below the band row (the fixture
   assumes one sub-header row: Field Name | Table / Column / Data Type |
   Schema / Table / Column / Data Type).

## 8. Fixture numbering note

`fixtures/acfc_shapes/pair_4/` (this work, vendor "Northwind Benefits", feed
`nb_cob_report`) is NOT the documented pair 4 of `docs/acfc/SHAPES_FOR_PORT.md`
(`sttm/pair_4_family_d.xlsx`, STTM family D). The directory name follows the
brief; the README table says which is which.
