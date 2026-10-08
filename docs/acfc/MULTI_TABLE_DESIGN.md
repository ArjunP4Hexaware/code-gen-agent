# Multi-table feeds — one STTM, several tables; one feed, several files

Branch `feature/multi-table` (cut from `feature/iig-first` at be38f05).
Status: **Phase A (this document) and Phase B (fixture `fixtures/acfc_shapes/pair_4/`)
done; Phase C steps 1–7 done (§6); open items on the Friday checklist (§7a).** Every Phase C step keeps the
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
| `emit/dml.py::_VARIABLE_COLUMNS` / `_cell_sql` | EVERY row of EVERY sheet gets the same `@PIPELINE_ID`, `@GROUP_ID`, `@OBJECT_ID` | 6 ADLS rows share one `OBJECT_ID` → primary-key collision on (GROUP_ID, OBJECT_ID, PIPELINE_ID); 4 schedule rows share one `PIPELINE_ID`. **Latent today:** pair 1's golden has 4 ADLS objects and 4 pipelines, and the DML already collapses them. **Resolved 2026-10-08:** `config_inserts_<env>.sql` is retired; `metadata_inserts.sql` writes one `<<COLUMN#n>>` placeholder per row (step 6) |
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

**Step 4 (done).** `DATA_QUALITY_RULES` is keyed per FILE (decision (a),
2026-10-07): for each ADLS object, in `dq_rules` order —
`header_trailer_split` (rule 5's condition: the header / trailer segments land
in a table other than the detail; `SOURCE_COLUMN` = the header table's
columns, `INPUT_PARAM` = the object's `SRC_FILE_NAME`, `TARGET_COLUMN` =
`<mapped catalog>,<schema>,<header table>,<trailer table>`), then the
date-format / data-type-cast rows the STTM states (unchanged; pair 1's eight).
`SEQUENCE_NO` restarts per object; `OBJECT_ID` = the file's ADLS `OBJECT_ID`.
No other rule class is generated: the review copy's summary lists one
**"additional DQ rules (not generated)" — Engineer** entry per file
(`iig_review.dq_review_entries`, Cells = 0 — there is no cell to fill), so the
sheet is visibly incomplete, never silently so.

**Step 5 (done).** Without a client inventory (`template_rows` for the sheet),
`DATA_FACTORY_PIPELINE_SCHEDULE` is the four structural rows of
`iig_v2.pipeline_roles`: grand master → master → file-to-stage,
stage-to-standard. `PIPELINE_NAME` from the naming convention —
`PL_GMSTR_{feed}`, `PL_MSTR_{feed}`, `PL_File_{feed}_ADLS_To_Delta_Incr`,
`PL_File_{feed}_Delta_To_STD_Incr`, `{feed}` = the FAQ `feed_abbreviation`,
else the feed slug in capitals; `PIPELINE_FREQUENCY` from the feed;
`PARENT_PIPELINE_ID` by position — `0` on the top row (METADATA_DB_SEMANTICS
§2), blank elsewhere with the tooltip naming the parent row; ids, dates and
audit left to the engineer. A configured inventory (pair 1's overlay) wins.

**Chunk A (2026-10-08) — every cell pinned, the golden is the authority.**
`tests/test_m4_acceptance.py::test_pair1_every_iig_cell_and_the_ddl_are_pinned`
compares EVERY cell of all eight pair-1 sheets with the golden (plus the DDL byte
for byte): each cell is *equal*, *open* (the golden carries an engineer /
environment / audit value no input states — ours blank AND flagged), a masked
*sequence* (`SYN-OBJ-<n>` = our `<n>`), or a *deviation* pinned with its reason
(open framework questions only: per-file SOURCE / FREQUENCY, HEADER_FLAG on a
fixed-width file, the first object's Overwrite, STGDELTA SOURCE, the notebooks'
refresh type, MANDATORY_FIELD_LIST, EMAIL_TO). A difference outside the tables,
or an entry no cell needs, fails. `tests/test_pair4_full_golden.py` is the
mirror for pair 4: a real framework run, every cell of all eight sheets equal to
`IIG_EXPECTED.yaml` (now goldened for all eight sheets).

Generator rules settled in Chunk A:

- **`TGT_PRIMARY_KEY`** = the band's Primary Key cells; none = blank and open
  (no natural-key fallback — the pair-1 golden is blank there). On STGDELTA the
  unknown value is a family convention (below).
- **Feed families** (correction 2026-10-08; `SCHEMA_DRIFT_FLAG` joined
  2026-10-09): two families' goldens fill four cells differently, neither an
  error. `metadata.templates.iig_v2.
  family_conventions` carries them; each fixture's overlay pins its own:

  | setting | pair-1 (PRX) family | CAQH-style family (pair 4) |
  | --- | --- | --- |
  | `lob` (ADLS, STGDELTA) | `blank` (decided, not an open cell) | `codes` — a per-LOB file's code, else the feed's LOB codes (FRD / STTM header) |
  | `stgdelta_unknown_primary_key` | `"NA"` | `""` (blank, open) |
  | `stgdelta_object_name` | `literal` — `Accumulator_accumclient`, transcribed from the golden (no input derives it) | `generalized_file_pattern` — the feed's patterns with LOB token and dates as `*`, generalized position by position, wildcards and extension removed (`NWB_COB_RPT`) |
  | `schema_drift_flag` (ADLS) | `N` (the golden, every row) | `Y` — the SD file-to-stage row and the CAQH IIG (`fixtures/acfc_shapes/README.md`); was an overlay constant until 2026-10-09 |

  The shipped default (`config/config.yaml`) is the pair-1 family's `lob` /
  primary key and the generalized file pattern (`table_name` is also
  available). **The ACFC overlay (`config/overlays/acfc_env.yaml`) pins the
  CAQH-style family explicitly (2026-10-08)** — the convention observed in the
  newest real sheet; a feed of the pair-1 family selects its own in a feed
  overlay. Which convention is current for NEW feeds is on the Friday checklist.
- `FILE_ADLS_INGESTION_DETAILS` applies configured path shapes (pair 4:
  `TGT_ADLS_PATH` = `{landing_rel}`, the landing inside its container).
- Test isolation: `cli.main()` re-reads the operator's `.env` mid-suite; the
  suite now strips the machine-local overrides after every test
  (`tests/conftest.py`), which the full-cell `EMAIL_TO` check exposed.

**Steps 6–7 (done)** — §6: `metadata_inserts.sql` + one CREATE block per table;
`scripts/iig_scorecard.py --all-sheets`.

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
- **convention:** PIPELINE_NAME, PIPELINE_DESCRIPTION, NO_OF_CYCLE_PER_DAY, DAY_OF_SCHEDULE, ACTIVE_FLAG, ACTIVE_END_DATE, ESTIMATED_START_TIME, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** PIPELINE_ID, PARENT_PIPELINE_ID, ACTIVE_START_DATE, APPLICATION_NAME, CREATED_BY, UPDATED_BY

### ADLS_DELTA_INGESTION_DETAILS

- **per-file:** OBJECT_ID, OBJECT_NAME, LOB, SRC_FILE_NAME, TGT_PARTITION_VALUE
- **per-table:** SRC_COLUMNS, SRC_DATA_TYPE, MANDATORY_FIELD_LIST, TGT_DATABASE_NAME, TGT_TABLE_NAME, TGT_COLUMN_NAMES, TGT_DATA_TYPE, TGT_RJT_TABLE_NAME, TGT_PRIMARY_KEY
- **per-feed:** DOMAIN, SUBDOMAIN, SOURCE, FREQUENCY, SRC_ADLS_PATH, SRC_FORMAT, SRC_FILE_DELIMITER, HEADER_FLAG, FILE_HEADER_FLAG, FILE_FOOTER_FLAG, TGT_LOAD_OPTION, TGT_PARTITION_COLUMN, RECYCL_ENBL_FLG
- **environment:** SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, SRC_CONTAINER_NAME, TGT_CONNECTION_ID, TGT_CONTAINER_NAME
- **convention:** CLAIM_TYPE_ID, ACTIVE_FLAG, SRC_REC_LNGTH, SRC_COL_LNGTH, SRC_COL_STRT_END_INDX, SRC_ADLS_ARCHVL_PATH, SRC_COMPRESSION, MULTILINE_FLAG, SCHEMA_DRIFT_FLAG, TGT_ADLS_PATH, TGT_FORMAT, TGT_RJT_ADLS_PATH, RECYCL_TBL_NM, RECYCL_ADLS_PATH, RECYCL_RETN_DAYS, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** GROUP_ID, PIPELINE_ID, MAPPING_EXPRESSION, CREATED_BY, UPDATED_BY

### STGDELTA_STDDELTA_INGESTION_DET

- **per-file:** —
- **per-table:** SRC_TABLE_NAME, SRC_CATALOG_NAME, SRC_SCHEMA_NAME, SRC_COLUMNS, SRC_DATA_TYPE, TGT_CATALOG_NAME, TGT_SCHEMA_NAME, TGT_TABLE_NAME, TGT_COLUMN_NAMES, TGT_DATA_TYPE, TGT_RJT_TABLE_NAME, TGT_PRIMARY_KEY
- **per-feed:** OBJECT_NAME, DOMAIN, SUBDOMAIN, SOURCE, FREQUENCY, LOB, TGT_LOAD_OPTION
- **environment:** SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, SRC_CONTAINER_NAME, TGT_CONNECTION_ID, TGT_CONTAINER_NAME
- **convention:** ACTIVE_FLAG, SRC_ADLS_PATH, SRC_FORMAT, SRC_ADLS_ARCHVL_PATH, TGT_ADLS_PATH, TGT_FORMAT, TGT_RJT_ADLS_PATH, TGT_PARTITION_COLUMN, TGT_PARTITION_VALUE, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** GROUP_ID, OBJECT_ID, PIPELINE_ID, CREATED_BY, UPDATED_BY

### DATA_QUALITY_RULES

- **per-file:** OBJECT_ID, INPUT_PARAM
- **per-table:** SOURCE_COLUMN, TARGET_COLUMN
- **per-feed:** —
- **environment:** —
- **convention:** SEQUENCE_NO, RULE_TYPE, RULE_CLASS, ACTIVE_RULE_FLG, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** GROUP_ID, CREATED_BY, UPDATED_BY

### FILE_ADLS_INGESTION_DETAILS

- **per-file:** —
- **per-table:** —
- **per-feed:** DOMAIN, SUBDOMAIN
- **environment:** SRC_CONNECTION_ID, TGT_CONTAINER_NAME, TGT_STORAGE_ACCOUNT_NAME
- **convention:** TGT_ADLS_PATH, SOURCE_TYPE, COPY_START_TIME_OFFSET_IN_MINUTES, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** GROUP_ID, OBJECT_ID, PIPELINE_ID, SRC_ROOT_DIR, SRC_EXTRACT_START_TIME, CREATED_BY, UPDATED_BY

### ADLS_FIXED_WIDTH_HANDLER

- **per-file:** —
- **per-table:** SEGMENT, SEGMENT_FILTER, COL, LEN, start_ind, TGT_TABLE, TGT_AUDIT_CLMS
- **per-feed:** —
- **environment:** —
- **convention:** ACTIVE_FLAG, CREATED_DATE, UPDATED_DATE, SRC_ADLS_ARCHVL_PATH, IS_MANDATORY, COLUMN_VALIDATIONS
- **engineer-assigned:** PROCESS_NAME, VERSION, SEGMNT_TYP, PIPELINE_ID, FILE_TYPE, EXTENSION, CREATED_BY, UPDATED_BY, FILE_REJECTION, RJCT_RSN_COLUMN_NM

### DATABRICKS_NOTEBOOK_DETAILS

- **per-file:** —
- **per-table:** —
- **per-feed:** TGT_REFRESH_TYPE
- **environment:** DATABRICKS_WORKSPACE_URL, DATABRICKS_WORKSPACE_SECRET, DATABRICKS_CLUSTERID, CLUSTER_DETAILS_ID
- **convention:** SEQ_NM, ACTIVE_FLAG, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** PIPELINE_ID, PIPELINE_NAME, GROUP_ID, PROCESS_NAME, DATABRICKS_NOTEBOOK_PATH, DATABRICKS_NOTEBOOK_NAME, CREATED_BY, UPDATED_BY, DELETE_DATABRICKS_NOTEBOOK_NAME, DQ_NOTEBOOK_PATH

### EMAIL_TEMPLATE_CONFIG

- **per-file:** —
- **per-table:** —
- **per-feed:** —
- **environment:** SENDER_NAME, SENDER_EMAIL, EMAIL_TO, EMAIL_CC
- **convention:** STATUS, ACTIVE_FLAG, CREATED_DATE, UPDATED_DATE
- **engineer-assigned:** TEMPLATE_ID, TEMPLATE_NAME, PROCESS_NAME, SUBJECT, BODY, BODY_QUERY, CREATED_BY, UPDATED_BY

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
4. **`DATA_QUALITY_RULES` header/trailer row — DONE** (pair 4: 6 rows = the golden;
   pair 1: no split row, its 8 derived rows; `tests/test_multi_table_step4.py`).
5. **`DATA_FACTORY_PIPELINE_SCHEDULE`: four rows — DONE** (pair 4: 4 = the golden;
   pair 1 keeps its inventory overlay's four; `tests/test_multi_table_step5.py`).
6. **`metadata_inserts.sql` — DONE.** `codegen.emit.metadata_inserts` renders
   the client's "DDL" (rule 8) from the same payload as the IIG: one block per
   sheet in `dml.table_order` (`-- <SHEET>: <n> row(s)`), one INSERT per row,
   header order. A value is an `N'…'` literal (line breaks as `+ NCHAR(10) +`,
   lossless); an OPEN blank (what the review copy calls open) is an unquoted
   `<<COLUMN#n>>` placeholder, so the script does not parse until every one is
   filled; a decided blank (`deliberate_blank`) is `NULL`. A `TABLE
   DEFINITIONS` index names every table's stage and standard definition by its
   mapped three-part name with its columns; ADLS rows are labelled `-- table
   <stage> <- file <pattern>`, STGDELTA rows `-- table <src> -> <tgt>`.
   **Written on every framework run (2026-10-08)**, independent of the DML
   switches (`emit_dml` + `dml.enabled` now gate only the runner notebooks
   `Insert_scripts_config_table_<env>.py`, which execute this file and refuse
   while a placeholder is left); DDL artefact group; gate check
   `metadata_inserts` (statement count = IIG rows; parses as T-SQL with the
   placeholders read as NULL). **It replaces `config_inserts_<env>.sql`**
   (retired 2026-10-08 after its DB-side knowledge was ported):
   - **Workbook → database: three rules** (amended 2026-10-09; stated as
     `RULE 1`–`RULE 3` in the script header, each with its
     `METADATA_DB_SEMANTICS.md` section). The IIG workbook keeps what humans
     hand over; the SQL writes what the framework reads; every other cell is
     the workbook's value as is.
     1. **Value map** (`dml.db_value_map`): `ACTIVE_FLAG` and
        `ACTIVE_RULE_FLG` workbook `'Y'` → `'S'` (§1; the goldens print
        `'Y'`, §10 — UNCONFIRMED, Friday checklist item 9).
     2. **Forced NULL** (`dml.db_null_columns`) — columns the framework fills
        itself / does not use today, NULL whatever the workbook holds:
        `DAY_OF_SCHEDULE`, `UDF2`–`UDF5`, `ESTIMATED_START_TIME`, the SLA
        columns (`COMPLETION_SLA`, `RUNTIME_SLA`,
        `CRITICAL_PROCESSING_PERIOD`) and `CLAIM_TYPE_ID` (§2 "not populating
        … future purpose", §7). `DAY_OF_SCHEDULE`: the pair-1 golden prints
        `0`, §2 / §10 say NULL — UNCONFIRMED, Friday checklist item 10.
     3. **Audit defaults and open cells**: blank `CREATED_DATE` /
        `UPDATED_DATE` → `GETDATE()` (`dml.db_blank_expressions`); blank
        `CREATED_BY` / `UPDATED_BY` → `@RFC_NUMBER` (FAQ `rfc_number`, else
        the `<<RFC_NUMBER>>` placeholder + `dml_unassigned:@RFC_NUMBER`);
        `FILE_ADLS_INGESTION_DETAILS.SRC_CONNECTION_ID` → `@SRC_CONNECTION_ID`
        (§3); any other OPEN cell → its `<<COLUMN#n>>` placeholder; a cell
        decided blank → `NULL`.
   - **Guards**, before the first INSERT: `@RFC_NUMBER` assigned; per schedule
     row its `PIPELINE_ID` unused; per `FILE_ADLS` / `ADLS_DELTA` / `STGDELTA`
     row its `GROUP_ID` unused in that table and the (GROUP_ID, OBJECT_ID,
     PIPELINE_ID) key unused (§2, §5).
   - **Connection lookup** (§3): `FILE_ADLS_INGESTION_DETAILS.SRC_CONNECTION_ID`
     = `@SRC_CONNECTION_ID` — reused by host + root path (more than one match
     aborts), else inserted and taken from `SCOPE_IDENTITY()`; a NULL
     `@SRC_HOST_NAME` with no id given aborts. Identifiers as spoken in the
     walkthrough (`dml_unconfirmed:connection_table`).
   - **Abort, never half-insert:** `SET XACT_ABORT ON` + `BEGIN TRY` /
     `BEGIN TRANSACTION` … `COMMIT` / `BEGIN CATCH` → `ROLLBACK` + `THROW`.
   The old-vs-new comparison on pair 1 (every remaining difference) is in
   `docs/acfc/OVERNIGHT_2026-10-08.md` "Morning cleanup". The CREATE reference text is one block per
   table and layer from `emit.framework.table_definitions` (the same
   derivation): stage blocks, then standard blocks; standard columns = the rows
   carrying a Standard band, named by it (a table with none keeps the stage
   list). Pair 1 byte-identical; pair 4 six CREATEs as in `TABLE_DEFINITIONS`
   (`tests/test_metadata_inserts.py`, incl. a round trip against the clean IIG).
   The one-`@OBJECT_ID` / `@PIPELINE_ID` / `@GROUP_ID` collision of the
   retired `config_inserts_<env>.sql` (§2) is gone with it: one placeholder per
   row.
7. **`scripts/iig_scorecard.py --all-sheets` — DONE.** Scores every sheet of the
   real workbook (iig_v2: all eight), pairing rows by key: schedule and notebook
   details by PIPELINE_NAME, ADLS by SRC_FILE_NAME, STGDELTA by table, DQ by
   (file — via the SAME workbook's ADLS OBJECT_ID — and RULE_CLASS) in
   SEQUENCE_NO order, fixed-width by SEGMENT, email by STATUS, FILE_ADLS by
   position. Real-only / generated-only rows are reported (key only) and count as
   unmatched cells; a golden's masked `SYN-OBJ-<n>` against a run's `<n>` is
   ALIAS. Score per sheet and in TOTAL = 100 × (matched + alias) / cells. Both
   goldens score 100.0 against themselves; the generated pair 1 scores TOTAL
   57.9 with every row paired — every DIFF is a pinned Chunk A deviation, every
   ALIAS a masked OBJECT_ID, and the rest is open cells (engineer / environment /
   audit values) (`tests/test_iig_scorecard_all.py`).

## 7. Open questions (for the framework owners)

1. `TARGET_COLUMN` of the split rule was given as `catalog,schema,hdr_table,…`
   — is the continuation `trl_table` (the golden assumes
   `catalog,schema,hdr_table,trl_table`)? Are the trailer's columns named
   anywhere (`SOURCE_COLUMN` lists the header columns only)?
2. ~~One split-rule row per ADLS object, or one per group?~~ **Decided
   2026-10-07: one per file** (pair 4 = 6).
3. Does a delimited feed whose stage is all-`String` get a `DataTypeCastRule`
   on the stage → standard leg (where the types change), and on which sheet?
4. Are the grand master and master new rows per feed, or existing pipelines a
   feed's children attach to? (Step 5 writes all four; an inventory overlay
   replaces them.)
5. `FILE_ADLS_INGESTION_DETAILS`: one row per file, or one wildcard row per
   root folder?
6. `HEADER_FLAG` / `FILE_HEADER_FLAG` / `FILE_FOOTER_FLAG` when header and
   trailer are split by the DQ rule: `N` (pair-1 analogy — a rule does the
   split) or `Y` (the walkthrough: "if your file is having a header")? Left
   open in the golden.
7. ~~`STGDELTA_STDDELTA_INGESTION_DET.LOB`~~ — a **family convention** since
   2026-10-08 (pair-1 family blank, CAQH-style family the codes); which is
   current for new feeds: Friday checklist.
8. ~~`STGDELTA_STDDELTA_INGESTION_DET.OBJECT_NAME`~~ — a **family convention**
   (pair-1 family: its own transcribed form; CAQH-style: the generalized file
   pattern); Friday checklist.
9. The real `ForReference` sheet's geometry below the band row (the fixture
   assumes one sub-header row: Field Name | Table / Column / Data Type |
   Schema / Table / Column / Data Type).

## 7a. Friday checklist — framework owners, 2026-10-09

To confirm before the next real run. Each item names what the code does today
and where the answer lands (config, not code, wherever possible).

**The five questions**

1. **Catalog names in the real STTMs.** Do the real Stage / Standard bands
   state exactly `PR_DLK` / `PR_STD` (the keys of the d1 `catalog_map` in
   `config/overlays/acfc_env.yaml`), or longer names (the pair-1 alias reads
   `pr_dlk_<x>`)? Today a stated catalog the map lacks is written as stated and
   flagged `catalog_unmapped:<layer>`. Answer → the `catalog_map` keys.
2. **The standard container for d1.** `STGDELTA_STDDELTA_INGESTION_DET`
   `TGT_CONTAINER_NAME` (and its `SRC_CONTAINER_NAME`, the stage container) for
   d1. The ACFC overlay carries the ADLS_DELTA connection / container constants
   only, so these cells are open on real runs. Answer → `acfc_env.yaml`
   `constants.STGDELTA_STDDELTA_INGESTION_DET`.
3. **The STGDELTA `OBJECT_NAME` convention.** The pair-1 family's golden prints
   `Accumulator_accumclient` (no input derives it — transcribed in the pair-1
   overlay); the CAQH-style family uses the generalized file pattern
   (`NWB_COB_RPT`). What is the rule? Answer →
   `family_conventions.stgdelta_object_name` (+ a derivation if there is one).
4. **`TGT_PRIMARY_KEY` semantics.** ADLS: the Stage band's Primary Key cells,
   else blank and open. STGDELTA: the Standard band's, else `'NA'` (pair-1
   family) or blank (CAQH-style). Is `'NA'` meaningful to the framework, and is
   `MANDATORY_FIELD_LIST` (today: the STTM's not-null detail columns; the pair-1
   golden leaves it blank; the walkthrough calls it "basically a primary key")
   the key list or the mandatory list?
5. **Which DQ rule classes are standard.** Generated today:
   `LoadHeaderAndTrailerToSeparateTablesRule` (one per file, only when header /
   trailer are their own tables), `DateFormatRule` and `DataTypeCastRule`
   (from the STTM's load rules / typed stage columns). The review copy lists
   "additional DQ rules (not generated)" — Engineer, one entry per file. Which
   other classes should every feed carry, and from which input?

**Confirm which convention is current for NEW feeds** (both are pinned today —
pair 1's overlay the PRX family, pair 4's the CAQH-style family; the shipped
default is the PRX family's LOB / key / SCHEMA_DRIFT_FLAG and the generalized
OBJECT_NAME; the ACFC overlay `acfc_env.yaml` sets the CAQH-style family, seen
in the newest real sheet):

6. `LOB` — blank (PRX family) or the LOB codes (CAQH-style)?
7. STGDELTA `TGT_PRIMARY_KEY` with no Primary Key cell — `'NA'` (PRX) or blank
   (CAQH-style)?
8. STGDELTA `OBJECT_NAME` — the family's own form (PRX) or the generalized
   file pattern (CAQH-style)?
8a. ADLS `SCHEMA_DRIFT_FLAG` — `N` (PRX: the pair-1 golden) or `Y` (SD /
    CAQH-style: the SD file-to-stage row and the CAQH IIG)? Answer →
    `family_conventions.schema_drift_flag`. (Numbered 8a so items 9 and 10
    keep the numbers `metadata_inserts.sql` cites.)

**Where the client's sheet and the framework walkthrough disagree, which one
does the database actually honour?** That is the real question; the two
columns below are its instances (same evidence pattern: the goldens say one
thing, `METADATA_DB_SEMANTICS.md` §10 the other). Today the workbook keeps the
sheet's value and `metadata_inserts.sql` writes the walkthrough's (rules 1 and
2 of the three workbook → database rules, step 6).

9. **`ACTIVE_FLAG` `Y` vs `S`.** The IIG workbooks (and both goldens) carry
   `'Y'`; the walkthrough (§1, §10) says the framework selects active rows
   with `ACTIVE_FLAG = 'S'`. Today: workbook `'Y'`, SQL `'S'` through
   `dml.db_value_map` (`ACTIVE_FLAG` and `DATA_QUALITY_RULES.ACTIVE_RULE_FLG`,
   the same assumption). Answer → the `dml.db_value_map` entry (drop it if the
   database honours `'Y'`).
10. **`DAY_OF_SCHEDULE` `0` vs NULL.** The pair-1 golden prints `0` on every
    schedule row; the walkthrough (§2 "as of now, this column, we are not
    populating", §10) says NULL. Today: workbook `0`, SQL NULL through
    `dml.db_null_columns`. Answer → that list (remove `DAY_OF_SCHEDULE` if the
    database expects `0`).

**Confirm, don't ask** (a decision already applied; say "correct" or correct it):

11. **FREQUENCY = run cadence, delivery cadence noted — correct?** Since
    0.5.8.post22 the ADLS / STGDELTA `FREQUENCY` and the schedule's
    `PIPELINE_FREQUENCY` are the PIPELINE RUN cadence: the FRD's run / schedule
    / refresh statement ("Frequency of data refresh – Monthly Run"), else the
    `DATA_FACTORY_PIPELINE_SCHEDULE` inventory's frequency; the file-delivery
    cadence (the FRD Frequency field / its File Details fill) goes in the cell's
    tooltip, and when the two differ the cell is flagged
    `frequency_delivery_differs` with both. Evidence: the SD real rows are
    `Monthly` while their files arrive twice a year; the CAQH ingestion
    FREQUENCY equals its pipeline schedule frequency. With no run statement the
    delivery cadence is written, as before. If wrong → `_frequency` in
    `src/codegen/metadata_template.py` (one switch of the source order).

**If time allows** (§7): the split rule's `TARGET_COLUMN` continuation (Q1),
whether grand master / master are new rows per feed (Q4), one
`FILE_ADLS_INGESTION_DETAILS` row per file or per root (Q5), and the header /
trailer flags when a DQ rule does the split (Q6).

## 8. Fixture numbering note

`fixtures/acfc_shapes/pair_4/` (this work, vendor "Northwind Benefits", feed
`nb_cob_report`) is NOT the documented pair 4 of `docs/acfc/SHAPES_FOR_PORT.md`
(`sttm/pair_4_family_d.xlsx`, STTM family D). The directory name follows the
brief; the README table says which is which.
