# SPEC — Option B rebuild specification for the CodeGen agent

This document specifies, to the byte, how three Option B deliverables are produced from an
approved (STTM workbook, FRD contract) pair plus a per-feed load-pattern FAQ and the client
engineering standards:

| Deliverable | File | Pass criterion (see ACCEPTANCE/) |
|---|---|---|
| Stage-layer deployment DDL | `<feed_slug>_stage_table_creation.txt` | byte-exact after masking the two sha256 spans in the banner |
| Standard-layer deployment DDL | `<feed_slug>_standard_table_creation.txt` | byte-exact after masking the two sha256 spans in the banner |
| Framework config rows workbook | `config_rows.xlsx` (7 IIG tabs + `_provenance` + `_inputs`) | cell-exact per tab (value and badge) |
| Per-feed flags + verdict | the `Flags:` block and `**Verdict: …**` line of the run report | line-exact |

Also produced by the reference implementation but **out of scope for this kit** (exists,
shelved): the Jinja-rendered PySpark notebook and module tree (Option A), the `.sql` DDL
source files under `ddl/`, `config_inserts.xlsx`, `ADDITION.md`, the demo UI, the SharePoint
transport and the Databricks volumes/publish transport.

## 0. Conventions used in this document

| Convention | Meaning |
|---|---|
| `<<name>>` | a variable span in a filled example; the surrounding bytes are literal |
| **normalize(x)** | lowercase x, collapse every run of whitespace (including newlines) to one space, strip leading/trailing whitespace |
| **sanitize(x)** | uppercase x, replace every run of non-alphanumeric characters with `_`, strip leading/trailing `_` (alphanumeric = ASCII letters and digits only; any other character, accented letters included, is a separator) |
| **slug(x)** | lowercase x, replace every run of non-alphanumeric characters with `_`, strip leading/trailing `_` (same ASCII-only rule) |
| **feed_id** | the mapping-contract feed id: `feed_aliases[FRD feed_name]` when the FRD feed_name is an exact (case-sensitive) key of the alias map and the value is non-empty, else slug(FRD feed_name); an alias value is used verbatim, never slugged |
| **feed_slug** | slug(feed_id); identical to feed_id unless an alias value contains characters outside lowercase letters, digits and `_`; the slug names the output files (`<feed_slug>_stage_table_creation.txt`), the FAQ file and the report |
| **repr(x)** | Python-style quoting of a text, used wherever this document says "repr": wrap in single quotes; if the text contains `'` and no `"`, wrap in double quotes instead; if it contains both, wrap in single quotes and write `\'` for each `'`; write `\\` for a backslash, `\n` for a newline, `\t` for a tab. A list is rendered as `['a', 'b']` (items repr'd, joined by `, `, in square brackets); an empty list as `[]` |
| **cell text** | every workbook cell is converted to text and stripped of leading/trailing whitespace before any use: numbers as Python prints them (`10`, `1.0`), booleans as `True`/`False`, dates as `YYYY-MM-DD HH:MM:SS`; formula cells contribute their cached value; an empty or whitespace-only cell is "empty" |
| **canonical file name(x)** | strip x, lowercase, replace every `ccyy` with `yyyy` |
| (null) | the value is absent; missing is never a default that looks like a real value |
| decision table | rows are evaluated top to bottom; the first matching row wins unless the table says otherwise |
| "error" | generation of that pair/feed stops with the quoted message; nothing is written for it (see 5.4) |

Processing order for one pair (every step is deterministic except 5.2):

1. Load and validate the FRD contract (1.6) — before the workbook is opened — then parse the STTM workbook into a mapping contract (1.2 or 1.3), pairing sheets/segments with the FRD feeds (1.4).
2. Validate the mapping contract (1.5) and resolve the two into one feed specification per feed (1.7).
3. Classify every FRD validation rule (5.1); send only `unmapped` rules to Layer 2 (5.2).
4. Load the FAQ and apply contract prefills (1.8).
5. Render the DDL sources and re-style them into the two deployment `.txt` files (2, 3).
6. Build the IIG rows and the workbook (4).
7. Compute flags and the verdict; write the report (5.3, 5.4, 5.5).

### 0.1 Configuration knobs the outputs depend on

Every knob below is read from one configuration file (any format the rebuild chooses). The
"acceptance value" column is the value every ACCEPTANCE case was generated with; the last
column says what to use in production.

| Knob | Acceptance value | Production guidance |
| --- | --- | --- |
| `feed_aliases` | empty map | FRD feed_name → STTM feed_id overrides when slug() is not enough (exact, case-sensitive key match; value used verbatim; empty value falls back to slug()) |
| `defaults.recycle_window_days` must be > 0; `engineering_standards.source_abbreviations`, `engineering_standards.type_mapping`, `load_pattern_faq.schema_version` | present in the reference configuration | read by no Option B code path (the source abbreviation feeds an unused name component); carry them or not, nothing changes |
| `naming.errors_table_suffix` | `_errors` | keep |
| `naming.recycle_table_suffix` | `_recycle` | keep |
| `naming.processed_files_table_suffix` | `_processed_files` | keep |
| `defaults.recycle_window_days` | 7 | used only when a recycle cell states no window |
| `extractor.*` (flat dialect vocabulary) | as listed in 1.2 | extend synonym lists for new client header spellings |
| `extractor.segmented.*` (segmented vocabulary) | as listed in 1.3; `member_reference_table` = `syn_member_ref` | `member_reference_table` = the reference table the client FRD's DQ requirement names (transcribe, never invent) |
| `load_pattern_faq.per_feed_dir` | a directory holding `<feed_slug>.faq.yaml` files | one FAQ file per feed |
| `engineering_standards.status` | `Client Data Engineering Naming + Coding Standards` | any text not starting with `STUB` once the standards are real |
| `engineering_standards.job_name_pattern` | `WF_{product}_{subproduct}_{feed}_{domain}_{subdomain}_{lob}_{frequency}` | from client naming standards doc, Databricks WORKFLOW clause |
| `engineering_standards.notebook_name_pattern` | `NB_{product}_{subproduct}_{domain}_{subdomain}_INGEST` | from client naming standards doc, NOTEBOOK clause |
| `engineering_standards.product_code` / `sub_product_code` | `DLK` / `NSP` | from client naming standards doc, product tables |
| `engineering_standards.domain_abbreviations`, `lob_abbreviations`, `frequency_abbreviations` | tables in 1.9 | transcribe from the client naming standards doc abbreviation tables |
| `engineering_standards.unknown_frequency_abbreviation` | `ADH` | keep |
| `engineering_standards.multi_lob_abbreviation` | `ALL` | keep |
| `engineering_standards.create_tables` | false | keep false (DDL is engineer-run) |
| `job.notification_emails` | `syn.dl.prodsupport@synthetic.example` (one entry) | the client production-support distribution list, from the client coding standards doc (alerts on success AND failure) |
| `framework.synthetic_location_prefix` | `abfss://syn-container-stage@synstorage.dfs.synthetic.example` | a labelled synthetic prefix; the real container is assigned by the platform team |
| `framework.deployment_ddl_include_side_tables` | false | keep false |
| `framework.id_placeholder` | `NULL` | used only by the shelved insert workbook |
| `demo.source_files.landing_root_template` | `syn-landing/inbound/{domain}/{sub_domain}/{source_system}` | the client landing convention as stated under the FRD's Structural Metadata → ADLS Location, written as a template with those three placeholders |
| `demo.source_files.load_strategy.stage` / `.standard` | `Truncate and Load` / `Upsert` | stand-ins shown with the SYNTHETIC badge (4.2 TGT_LOAD_OPTION) |
| `demo.metadata_sheet.tabs` | the seven tabs and headers in 4.0 | transcribe verbatim from the client IIG workbook (tab names, header spellings, order) |
| `demo.metadata_sheet.always_blank` | the 12 headers in 4.0 | framework-assigned identifiers; never invented |
| `segments.*` (runtime record-type values) | `record_type`, H/D/T, `record_count` | only the notebook path reads these; a segmented feed without a segmented extraction block and without a configured value for one of its segments is a template gap (5.4) |
| `reasoning.max_attempts` | 2 | Layer 2 retry budget |

## 1. Inputs contract

### 1.1 STTM workbook — dialect detection

| # | Condition (checked in this order) | Dialect / outcome |
| --- | --- | --- |
| 1 | at least one sheet name starts with `MAPPING-` (case-sensitive) | flat dialect (1.2); every such sheet is one feed |
| 2 | no `MAPPING-` sheet, and within the first 30 rows of any sheet there is a row whose normalized cells contain at least two of {`source file layout`, `source layout`, `stage layer`, `standard layer`} AND (some earlier row has both column A and column B non-empty, OR the next row has a cell whose normalized text starts with `segment`) | segmented dialect (1.3) |
| 3 | neither | error `<file>: no mapping sheets found (prefix 'MAPPING-'); sheets present: [...]` |
| 4 | flat dialect, but one mapping sheet's rows name more than one stage (schema, table), or a source-block header normalizes to `segment` / `record segment` | the flat parse is abandoned and the WHOLE workbook is handed to the segmented parser (1.3). Because a `MAPPING-` workbook has no metadata block, that parser then fails: `<file>: no sheet matches the segmented layout family (band row + metadata block / Segment header)` when no sheet's row 2 carries a header starting with `segment`, or `<sheet>: metadata block is missing key(s) [...]` when one does. Only if the workbook ALSO contains a genuine segmented sheet is that sheet extracted — and the `MAPPING-` sheets are then silently ignored. The flat parser itself never guesses a multi-table layout |

A flat single-sheet workbook (no `MAPPING-` prefix, no metadata block, no Segment column) is
therefore NOT handled: row 3 fires. The "column A and column B non-empty" test of row 2 treats
a whitespace-only cell as non-empty. Contrasting examples:

| Workbook | Outcome |
|---|---|
| sheets `FILE_DETAILS`, `VERSION_HISTORY`, `MAPPING-SYN_WIDGET_RISK` | flat, one feed |
| one sheet `syn_segmented` whose row 9 reads `Source Layout` / `Stage Layer` / `Standard Layer` under a key:value block | segmented |
| one sheet `notes` with `hello`, `world` in row 1 | error "no mapping sheets found" |

### 1.2 Flat dialect (one `MAPPING-<TABLE>` sheet per feed)

Sheet layout: row 1 carries the band labels, row 2 the real headers, data starts at row 3.
Rows whose cells are all empty are skipped. A blank spacer column may sit between bands.

| Element | Rule |
| --- | --- |
| band row (row 1) | normalized cells must contain `source file layout` and `stage layer` exactly once each; `standard layer` is optional; a label appearing twice is an error; the column positions must satisfy source < stage < standard; the last band runs to the last used column |
| source band headers (row 2) | every non-empty header must normalize to one synonym in the table below; unknown header → error `unrecognized source-block header`; the same logical column twice → error; required logical columns: source_column, description, sample_value, source_datatype, null_check, phi, mandatory; optional: value_spec |
| stage / standard band headers (row 2) | every non-empty header must normalize to one of `schema`, `tablename`, `columnname`, `datatype`; all four required per band; the same header twice in one band → error `<sheet>: <band>-block header '<h>' appears twice`; a header starting with `recycle flag` inside a band is ignored |
| recycle column | any row-2 header (any band) whose normalized text starts with `recycle flag`; at most one |
| columns left of the source band | ignored entirely (only the recycle-column scan covers them) |
| order of checks (for diagnostics) | VERSION_HISTORY is parsed first, then FILE_DETAILS, then each mapping sheet; within a sheet: band labels (duplicate check per label, then missing, then order), recycle column, source headers, stage headers, standard headers, then row by row: source column → stage Schema → stage TableName → standard Schema/TableName/ColumnName/DataType → NULL check → source DataType → PHI → Mandatory → stage ColumnName → stage DataType; after the rows: no rows → stage-table count → standard-table count; every sheet is parsed and paired before the "FRD feed without a sheet" check (1.4 row 2) runs; a sheet with only one row crashes with an unhandled error rather than a parse error |

Source-block header synonyms (compare after normalize):

| Logical column | Accepted header spellings |
| --- | --- |
| source_column | `database column name`, `database name`, `client data table column name` |
| description | `description` |
| sample_value | `sample value`, `example values` |
| source_datatype | `datatype`, `data type` |
| null_check | `null check` |
| phi | `phi field`, `phi/pii field` |
| mandatory | `mandatory field`, `mandatory` |
| value_spec (optional) | `comment` |

Cell conventions per data row (row 3 onward):

| Cell | Rule | Example → result |
| --- | --- | --- |
| every cell | the "cell text" convention of Section 0 applies (text, stripped); `String ` therefore reads `String` |  |
| source column cell normalizes to `na` | the row is an AUDIT row: take stage ColumnName (required, must not itself be `na`) and stage DataType, which must normalize to `string` → `String` or `timestamp` → `Timestamp`; anything else is an error; audit rows never become fields | `NA` … `LOB` / `string` → audit column LOB String |
| source column (field row) | required text (empty → error) | `widget_id` |
| NULL check | normalized value starts with `not null` → nullable false; any other non-empty value → nullable true; empty → error | `Not NULL` → not nullable; `NULL ` → nullable; `NOT NULL` → not nullable |
| PHI | normalized `yes` → true, `no` → false, else error | `NO` → false |
| Mandatory | same as PHI | `Yes` → true |
| source DataType | required text (stripped, otherwise verbatim) | `Decimal(12,2)` |
| Description, Sample Value | optional text (empty → null) |  |
| Comment | value_spec (only when the sheet has a `comment` header); not used by any Option B output |  |
| stage Schema / TableName / ColumnName / DataType | required text; every field row of a sheet must name the same (schema, table) pair | `stg_syn` / `syn_widget_risk` |
| standard Schema / TableName / ColumnName / DataType | required when a standard band exists; one (schema, table) pair per sheet | `syn` / `syn_widget_risk` / `risk_score` / `Decimal(10,2)` |
| Recycle Flag cell | see the recycle rule below |  |

Recycle Flag cell rule (at most one flagged row per sheet):

| Condition | Result |
| --- | --- |
| no row has a non-empty recycle cell | no recycle spec |
| more than one row has a non-empty recycle cell | error `N rows carry recycle text` |
| the cell has no marker: an uppercase `Y` at a word boundary (not preceded by a letter, digit or `_`), then any whitespace including newlines, then `(` | error `recycle cell has no 'Y (...)' flag marker` |
| otherwise | applies_to = that row's source column; validation = the text after the marker, stripped of outer whitespace, THEN one trailing `)` removed if present, THEN trailing whitespace stripped again (must be non-empty); window = the first `<digits>` followed by optional whitespace and `day` anywhere in the cell (case-insensitive; `10days` counts, `10-day` does not; no word boundary is required after `day`), else the configured default (7); a stated window of 0 also falls to the default | see example |
| resulting recycle spec | enabled = true; validation as above; on_match = `Process record into stage table`; on_no_match = `Load record to Recycle Table with recycle flag enabled for <window> days; retry on subsequent runs` (both texts are configuration values with `{window_days}` filled) |  |

Example cell (the header line is repeated inside the cell, then the flag):

```
Recycle Flag ( Enabled for 10 Days)
Y ( Check with GADGET_KEY from GadgetMaster in the SYN_STD.GADGETS.GDG_MASTER FOR GRP_CD = 9, if available process it else load this to the Recycle Table with Recycle Flag Enabled for 10 days.)
```

→ applies_to `gadget_key`, window 10, validation `Check with GADGET_KEY from GadgetMaster in the SYN_STD.GADGETS.GDG_MASTER FOR GRP_CD = 9, if available process it else load this to the Recycle Table with Recycle Flag Enabled for 10 days.`

Metadata sheets:

| Sheet | Rule |
| --- | --- |
| `FILE_DETAILS` | required; row 1 must carry exactly one header from each list: vendor {`vendor`}, file name {`filename`, `file name`}, frequency {`frequency`} (normalized); rows with vendor and file name both empty are skipped; a row with only one of them empty is an error; no rows → error |
| `VERSION_HISTORY` | required; the header is the first row anywhere that has one cell normalizing exactly to `version` and another normalizing exactly to `date` (whole-cell equality, not substring); the version is the LAST non-empty cell in the Version column below it; none → error |

Three-row excerpts, one per observed header sub-dialect (the reference implementation handles
all three in one workbook). Cells are shown as CSV; `,` separates columns and an empty field
is an empty cell.

Sub-dialect A (`Database column Name` + `NULL CHECK` second):

```csv
Source File Layout,,,,,,,Stage Layer,,,,,Standard Layer,,,
Database column Name,NULL CHECK,Description,Sample Value,DataType,PHI Field ,Mandatory Field,Schema,TableName,ColumnName,DataType,,Schema,TableName,ColumnName,DataType
widget_id,Not NULL,Widget identifier,W-0001,String,No,Yes,stg_syn,syn_widget_risk,widget_id,String,,syn,syn_widget_risk,widget_id,String
risk_score,NULL,Widget risk score,2.5,String,No,No,stg_syn,syn_widget_risk,risk_score,String,,syn,syn_widget_risk,risk_score,"Decimal(10,2)"
NA,NULL,NA,NA,NA,No,No,stg_syn,syn_widget_risk,LOB,string,,syn,syn_widget_risk,LOB,string
```

Sub-dialect B (`Database Name`, NULL check fifth with a leading space, no standard band):

```csv
Source File Layout,,,,,,,Stage Layer,,,
Database Name,Description,Sample Value,DataType, NULL Check,PHI Field ,Mandatory Field,Schema,TableName,ColumnName,DataType
sensor_id,Sensor identifier,S-01,String,NOT NULL,NO,Yes,stg_syn,syn_sensor_pings,sensor_id,String
reading,Sensor reading,0.75,"Decimal(6,3)",NULL,NO,NO,stg_syn,syn_sensor_pings,reading,String
NA,NA,NA,NA,NULL,No,No,stg_syn,syn_sensor_pings,REC_CREATION_TIME,timestamp
```

Sub-dialect C (`Client Data Table Column Name`, `Comment`, `Example Values`, `Data Type`,
`PHI/PII Field`, `Mandatory`, plus a trailing Recycle Flag column beyond the standard band):

```csv
Source File Layout,,,,,,,,Stage Layer,,,,,Standard Layer,,,,
Client Data Table Column Name,Description,Comment,Example Values,Data Type,NULL Check,PHI/PII Field,Mandatory,Schema,TableName,ColumnName,DataType,,Schema,TableName,ColumnName,DataType,Recycle Flag ( Enabled for 10 Days)
gadget_key,Gadget key,string,G-100,String,Not NULL,No,Yes,stg_syn,syn_gadget_events,gadget_key,String,,syn,syn_gadget_events,gadget_key,String,"Recycle Flag ( Enabled for 10 Days)
Y ( Check with GADGET_KEY from GadgetMaster in the SYN_STD.GADGETS.GDG_MASTER FOR GRP_CD = 9, if available process it else load this to the Recycle Table with Recycle Flag Enabled for 10 days.)"
gadget_nm,Gadget name,string,Sprocket,String,NULL,No,No,stg_syn,syn_gadget_events,gadget_nm,String,,syn,syn_gadget_events,gadget_name,String,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,SRC_FILE_NAME,string,,syn,syn_gadget_events,SRC_FILE_NAME,string,
```

Output of the flat parse, per sheet: the stage (schema, table); the standard (schema, table)
or none; the field rows in sheet order; the audit rows in sheet order; the recycle text.

### 1.3 Segmented dialect (one wide sheet, Header/Detail/Trailer)

| Element | Rule |
| --- | --- |
| mapping sheet | per sheet, scan ALL rows (no 30-row cap here) for the FIRST row containing ≥ 2 band labels; the sheet qualifies only if THAT row has a key:value block above it or a `segment…` header below it (a later band row is never considered); exactly one sheet must qualify: none → `<file>: no sheet matches the segmented layout family (band row + metadata block / Segment header)`, more than one → `<file>: N sheets match the segmented layout family ([names]); expected exactly one mapping sheet` |
| band row | that row; source band starts at `source file layout` or `source layout`, stage band at `stage layer`, standard band (optional) at `standard layer`; a label appearing twice keeps the LAST occurrence; no left-to-right order check (a misplaced standard label surfaces as a missing-column error); missing source or stage → error `<sheet>: band row <n> lacks source/stage band labels` |
| metadata block | every row ABOVE the band row whose column A normalizes to one of the keys below AND whose column B is non-empty contributes column B; a key whose column B is empty is simply absent; the same key twice (both non-empty) → error; required keys: `File(s)`, `File Generator`, `File type` — missing → error `<sheet>: metadata block is missing key(s) [<labels, sorted>]` |
| header row | band row + 1 |
| source headers | for each non-empty header (left to right within the source band), the logical column is the FIRST synonym entry (in the order listed below) whose normalized text equals the header OR whose text before ` (` is a prefix of the header (so `Length` also prefix-matches `Length of record`; `Segment (Ex:…)` matches any header starting with `segment`); a header matching no entry → error `<sheet>: unrecognized source-block header '<h>' (column <c>); known: {...}`; a logical column already taken is left as is (the later header is dropped silently); required after resolution: field_name, datatype, segment → else error `source block is missing required column(s) [...]` |
| stage / standard headers | each non-empty header must normalize to one of the ten table headers below (else error); the first occurrence of a header wins, duplicates are dropped silently; required per band: schema, tablename, columnname, datatype |
| data rows | below the header row; all-empty rows skipped; no data rows at all → error `<sheet>: no data rows below the header row` |

Metadata keys (column A, normalized) → fact:

| Key | Fact | Used for |
| --- | --- | --- |
| `File(s)` | file name pattern list (split on newline, `,`, `;`) | FRD pairing; `name_pattern` = the FIRST entry (cell order) whose canonical form matches an FRD pattern, stripped of outer whitespace but otherwise verbatim |
| `File Generator` | source_system of the mapping contract | (not an Option B output; the FRD's source_system is what the rows show) |
| `File Location` | not consumed |  |
| `LOB` | not consumed |  |
| `File frequency` | mapping contract `frequency` | not an Option B output |
| `Domain`, `Sub-Domain` | not consumed |  |
| `File type` | delimiter fallback: the first non-space character after the first occurrence of the lowercase word `delimited` (case-sensitive; zero or more whitespace characters in between), unless that character is `)` | delimiter (below) |

Delimiter precedence (segmented feeds): the FRD delimiter when non-empty; else the File-type
character above; else `,` for format `csv` / `\|` for `psv` (format lowercased); else error
`feed '<name>': no delimiter in the FRD, the metadata block ('<file type text>'), or implied by
format '<format>'`.

Source-block header synonyms (normalize, then equality or prefix-before-` (`):

| Logical | Spellings | Required |
|---|---|---|
| ordinal | `#` | no |
| field_name | `Field Name` | yes |
| datatype | `Data Type` | yes |
| length | `Length` | no |
| fixed_width_length | `Field Length (fixed width)` | no |
| fixed_width_start | `Start position (fixed width)` | no |
| fixed_width_end | `End Position (fixed width)` | no |
| segment | `Segment (Ex:Header,Trailer,Detail)`, `Segment` | yes |
| pii | `PII` | no |
| comments | `Comments` | no |
| business_rule | `Business Rule` | no |

Stage and standard block headers (same vocabulary in both bands): `Catalog`, `Schema`,
`TableName`, `ColumnName`, `DataType`, `Mandatory Column`, `Primary Key`, `Field Description`,
`Table Description`, `Transformations/Data Quality`. Cell text is stripped, so a header such
as `Schema ` (trailing space) or `Mandatory \nColumn` (newline) resolves.

Data-row classification (decision table, per row):

| # | Condition | Outcome |
| --- | --- | --- |
| 1 | Segment cell non-empty but not one of `Header`, `Detail`, `Trailer` (normalized) | error `unrecognized Segment value` |
| 2 | Segment empty and Field Name non-empty | error `field '<name>' carries no Segment value` |
| 3 | Segment non-empty | a FIELD of that segment; the segment becomes the "current segment"; segments are recorded in first-seen order |
| 4 | Segment empty and Field Name empty, and (no current segment yet OR the stage ColumnName cell is empty) | error `<sheet> row <n>: row carries neither a Segment value nor an audit-column identity` |
| 5 | Segment empty and Field Name empty, current segment set, stage ColumnName present | an AUDIT row of the current segment; stage DataType must normalize to `string` or `timestamp` else error `audit column '<c>' has datatype '<d>'; expected one of ['String', 'Timestamp']` |
| 6 | after grouping: no Detail field rows | error `<sheet>: no Detail-segment rows found` (raised right after grouping, before identification is derived… see the identification table: pairing, the FAQ status check and identification actually run BEFORE grouping) |
| 7 | after fields, notes and recycle are built: no Detail audit rows | error `feed '<name>': no Detail-segment audit rows found (rows with empty source cells inside the Detail block)` |

Order of the segmented steps: locate the sheet → band starts → metadata block → header blocks →
data-row classification → FRD pairing (1.4) → FAQ override status check → record
identification → grouping by segment (rows 6 above) → standard-layer decision → fields → notes
→ recycle → Detail audit check (row 7) → targets → file pattern → delimiter → contract.

Field derivation per data row:

| Contract field | Rule |
| --- | --- |
| source_column | Field Name |
| description | Comments (or null) |
| sample_value | always null |
| source_datatype | Data Type, or the literal `unstated` when empty |
| mandatory (field attribute) | stage `Mandatory Column` ∈ {yes, y, true} (normalized) — Primary Key alone does not set it |
| nullable | NOT (Mandatory Column yes OR Primary Key yes) |
| phi | source `PII` ∈ {yes, y, true} |
| stage_column, stage_datatype, stage_table | stage ColumnName, DataType, TableName (each required) |
| standard_column, standard_datatype, standard_table | the standard block cells, only when the standard layer is emitted (below); else null |
| value_spec | stage `Transformations/Data Quality` and source `Business Rule`, the non-empty ones joined with `; ` (null when both empty) |
| record_segment | the canonical segment name |

Field ORDER in the contract: grouped by segment in first-seen segment order, and within a
segment in sheet order (a sheet that interleaves segments is regrouped). Every list below
follows the same grouped order.

Feed-level derivations:

| Item | Rule |
| --- | --- |
| standard layer emitted | a standard band exists AND at least one field row has a non-empty standard TableName |
| standard target | schema = first non-empty standard Schema over the grouped field rows (empty string when none — no error); catalog = first non-empty standard Catalog (or none); table = the Detail segment's first-row standard TableName (empty string when blank — no error) |
| stage target | schema, catalog (optional), table from the Detail segment's first row (schema and table required) |
| not_null_columns = mandatory_columns | source names of fields with Mandatory Column yes OR Primary Key yes, grouped order; NOT de-duplicated (a field name mandatory in two segments appears twice) |
| phi_columns | source names with PII yes, grouped order, not de-duplicated |
| audit_columns (feed-wide) | the Detail segment's audit rows |
| per-segment audit | every segment's own audit rows (used by the DDL and by the audit-scope CONFIRM item) |
| record identification | see the next table |
| version | the literal `unversioned (segmented workbook carries no VERSION_HISTORY sheet)` |

Record identification (decision table):

| # | Condition | Outcome |
| --- | --- | --- |
| 1 | the feed's FAQ declares `record_type_discriminators` with status other than `confirmed` | error `record_type_discriminators in the FAQ is an OVERRIDE and requires status 'confirmed'` |
| 2 | the FAQ declares it with status `confirmed` | method `declared_override`; trailer marker = declared trailer value; header rule `records whose first field equals repr(header value)`; detail rule `records whose first field equals repr(detail value)`; citation `FAQ record_type_discriminators override (status: confirmed): header=repr(h) detail=repr(d) trailer=repr(t)`; Trailer field rows are NOT required on this path |
| 3 | no override and no Trailer field rows | error `<sheet>: no Trailer-segment rows found` |
| 4 | otherwise, the FIRST Trailer field row's Comments contains `contains the value <token>` (case-insensitive; token = the next run of non-whitespace characters) | method `derived_from_sttm`; trailer marker = token; header rule `first record of the file`; detail rule `every record that is neither the first record nor a record whose first field equals repr(token)`; citation `STTM repr(sheet) row <n>, repr(Field Name) Comments: repr(comment)` — so a two-line comment shows `\n` inside the quotes and a comment containing `'` is double-quoted |
| 5 | otherwise | error `<sheet> row <n>: the Trailer record-type comment does not state a static marker value (comment: repr(comment)); record identification cannot be derived — declare a confirmed record_type_discriminators override in the feed's FAQ instead` |

Every citation and rule string in this section is built with repr (Section 0): quoted values
follow the repr quoting rules, newlines render as `\n`, backslashes are doubled.

Provenance notes (each note carries the verbatim citation it rests on; they surface in the run
report and in the shelved manifest, not in the seven tabs):

| Note (fixed text) | When | Citation |
| --- | --- | --- |
| `STD target schema sourced from STTM; FRD Structural Metadata names stage targets only. The standard layer is scoped by its Load Strategy, never inferred absent from the Target Schema block.` | standard layer emitted AND the FRD standard table list is empty | `FRD Load Strategy STD: repr(strategy); STTM standard target group: <catalog>.<schema>` (empty parts omitted from the dotted name) |
| `No MERGE key required or derived: the FRD's Technical Metadata states Business Key / Primary Key / Unique Key(s) = None and the load strategies are truncate (STG) / append (STD). The STTM's empty Mandatory/Primary Key columns are consistent with the FRD.` | always | `FRD Load Strategy STG: repr(strategy); Load Strategy STD: repr(strategy)` |
| `AS-IS load: business columns are STRING in BOTH layers, audit date/timestamp fields excepted (FRD-driven switch, not a feed special case).` | any FRD validation rule contains `AS` + `IS` as a whole word joined by nothing, one ASCII hyphen, one non-breaking hyphen or exactly one whitespace character (any case) | `FRD validation rule: repr(first such rule)` |
| recycle notes | see the recycle table below |  |

Segmented recycle derivation (decision table):

| # | Condition | Outcome |
| --- | --- | --- |
| 1 | FRD `recycle_rule` is null or empty | no recycle |
| 2 | no FRD validation rule matches `validation` … `against facets` or `member id` … `facets` on ONE line (case-insensitive; `…` = any text not crossing a newline; `memberid` without the space also matches) | no recycle; note `FRD states a recycle rule but no member-validation rule; no recycle module is generated.` citing `FRD recycle_rule: repr(text)` |
| 3 | no field's Field Name normalizes to the configured member field (`member id`), searching the grouped field rows | no recycle; note `FRD states member validation but no field named 'Member ID' exists in the STTM; no recycle module is generated.` citing `FRD validation rule: repr(first matching rule)` |
| 4 | otherwise | recycle spec: applies_to = the member field's source name; reference = `<stage Catalog>.<stage Schema>.<member_reference_table>` (empty parts omitted); window = first `<digits>` + optional whitespace + `day` in recycle_rule, else 15 (a stated 0 also gives 15); validation = `Check with <stage ColumnName> from <reference>, per FRD rule repr(rule)`; on_match `Process record into stage table`; on_no_match `Load record to Recycle Table with recycle flag enabled for <N> days; retry on subsequent runs`; note `Recycle: 'Member ID' existence checked against <reference> in the stage layer; invalid records recycle for <N> days.` citing `FRD validation rule: repr(rule); FRD recycle_rule: repr(text)` |

Three-row excerpt (rows 9–13 of the sheet; the eight metadata rows precede the band row):

```csv
Source Layout,,,,,,,,,,,Stage Layer ,,,,,,,,,,Standard Layer ,,,,,,,,,
#,Field Name,Data Type,Length,"Field Length
 (fixed width)","Start position
(fixed width)","End Position
(fixed width)","Segment
(Ex:Header,Trailer,Detail)",PII,Comments ,Business Rule,Catalog,Schema ,TableName ,ColumnName ,DataType,"Mandatory
Column",Primary Key,Field Description,Table Description,Transformations/Data Quality,Catalog,Schema ,TableName ,ColumnName ,DataType,"Mandatory
Column",Primary Key,Field Description,Table Description,Transformations/Data Quality
1,Format Version,varchar,10,,,,Header,,Envelope format version,Load as is,SYN_DLK,STG_SYN ,EXT_SYN_HDR,SYN_FMT_VER,String ,,,Envelope format version,Stage table EXT_SYN_HDR,,SYN_STD,SYN ,EXT_SYN_HDR,SYN_FMT_VER,String ,,,Envelope format version,Standard table EXT_SYN_HDR,Load as is
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_HDR,SRC_FILE_NAME,String ,,,,,,SYN_STD,SYN ,EXT_SYN_HDR,SRC_FILE_NAME,String ,,,,,
1,Record Type,varchar,10,,,,Trailer,,"Static text identifying the record as the trailer record.
Contains the value ******",Load as is,SYN_DLK,STG_SYN ,EXT_SYN_TRL,SYN_REC_TYPE,String ,,,"Static text identifying the record as the trailer record.
Contains the value ******",Stage table EXT_SYN_TRL,,SYN_STD,SYN ,EXT_SYN_TRL,SYN_REC_TYPE,String ,,,"Static text identifying the record as the trailer record.
Contains the value ******",Standard table EXT_SYN_TRL,Load as is
```

(Trailing spaces in `Stage Layer `, `Standard Layer `, `Comments `, `Schema `, `TableName `,
`ColumnName `, `STG_SYN `, `SYN `, `String ` are deliberate: they are stripped/normalized away.)

### 1.4 Pairing a workbook with the FRD contract

| # | Dialect | Rule | Error text when violated |
| --- | --- | --- | --- |
| 0 | both | the FRD contract is loaded and validated before the workbook is opened; an invalid FRD fails with the contract validator's own message (5.4) | — |
| 1 | flat | each mapping sheet's stage table must appear in exactly one FRD feed's `stage_target.tables` | `sheet '<name>' (stage table '<t>') matches <n> FRD feeds <list>; expected exactly one whose stage_target.tables contains it` — `<list>` = the matching feed names, or ALL FRD feed names when none match, as a repr list |
| 2 | flat | every FRD feed must have a sheet | `FRD feed(s) [...] have no mapping sheet in <workbook> (sheet stage tables: [...])` |
| 3 | flat | an FRD feed that declares record_segments cannot pair with a flat sheet | `FRD declares record segments [...] — segmented feeds are not supported by this extractor` |
| 4 | flat | exactly one FILE_DETAILS row whose canonical file name equals a canonical FRD pattern | `<n> FILE_DETAILS rows match its file_name_patterns […] (compared after date-placeholder canonicalization: CCYY->YYYY, case-insensitive)` |
| 5 | flat | FRD has standard tables ⟺ the sheet has a standard band; the sheet's standard table must be in the FRD list | `standard-target presence disagrees` / `sheet standard table … is not among FRD standard tables` |
| 6 | flat | at least one audit row | `sheet '<name>' has no audit rows` |
| 7 | segmented | exactly one FRD feed shares a canonical pattern with the metadata File(s) entries; the segmented path performs NO other FRD cross-check (it does not require the FRD to declare record_segments, and does not compare standard-target presence — those disagreements surface only at resolution, 1.7) | `<file>: <n> FRD feeds match the metadata File(s) patterns [...] (FRD feeds: [...])` |
| 7a | flat | a feed-level validation failure of the assembled contract (1.5) is reported as `feed '<name>': extracted feed fails contract validation:` followed by the validator's message; a contract-level failure (two sheets naming the same stage table → duplicate feed ids) is the validator's raw message; a flat feed whose delimiter cannot be resolved reads `feed '<name>': extracted feed fails contract validation:` + newline + `feed '<name>': format '<f>' has no implied delimiter and the FRD contract states none` | — |
| 8 | both | feed_id = `feed_aliases[FRD feed_name]` when the feed_name is an exact key with a non-empty value (used verbatim), else slug(FRD feed_name); feed_slug = slug(feed_id) | — |
| 9 | both | contract_name = `STTM mapping contract extracted from <workbook file name>` unless overridden; generated_from_workbook = the file name; generated_date = the injected date (acceptance: `2026-01-01`) | — |

Examples: FRD feed_name `Syn Widget Risk` → feed_id `syn_widget_risk`; FRD pattern
`widget_risk_CCYYMMDD.csv` pairs with FILE_DETAILS `widget_risk_YYYYMMDD.csv` (both canonicalize
to `widget_risk_yyyymmdd.csv`), and the emitted `name_pattern` is the workbook's spelling
`widget_risk_YYYYMMDD.csv`; FRD pattern `CCYYMMDD_syn_segmented_*.txt` pairs with File(s)
`YYYYMMDD_syn_segmented_*.txt`.

### 1.5 The mapping contract (intermediate representation)

The parse produces one mapping contract per workbook (the reference implementation writes it as a
file; a rebuild may keep it in memory). Every field below is consumed downstream unless marked
"not used by Option B".

| Level | Field | Value rule | Used by |
| --- | --- | --- | --- |
| contract | contract_name | 1.4 row 9 | banners (2, 3), `_inputs` sheet |
| contract | sttm_version | flat: VERSION_HISTORY; segmented: the fixed "unversioned" literal | not used by Option B |
| contract | generated_from_workbook, generated_date, notes (three fixed sentences, different per dialect) | file name; injected date or today; fixed text | generated_date is not used by Option B; the others only identify the file |
| feed | mapping_sheet, field_count | sheet title; number of fields | not used by Option B |
| feed | feed_id | 1.4 row 8 | join key, `feed_slug` |
| feed | source_system | flat: FILE_DETAILS Vendor; segmented: File Generator | not used by Option B (rows use the FRD's) |
| feed | source_file.name_pattern / format / delimiter / frequency | flat: FILE_DETAILS FileName / FRD format / FRD delimiter else csv `,` psv `\|` with the format compared after lowercasing (else error) / FILE_DETAILS Frequency; segmented: matching File(s) entry / FRD format / 1.3 delimiter fallback / File frequency | only the delimiter feeds resolution (1.7); format, name_pattern and frequency are never read again |
| feed | stage.schema / table / catalog | the sheet's stage pair; segmented adds the catalog | schema and table are targets; the STTM stage catalog is NEVER read by resolution (stage catalogs come from the FRD, 1.7 row 5) |
| feed | standard | the sheet's standard pair or null | targets |
| feed | load_rules.not_null_columns | flat: source columns with nullable false; segmented: mandatory fields | natural key, MANDATORY_FIELD_LIST, DQ CheckRule |
| feed | load_rules.mandatory_columns | flat: Mandatory yes; segmented: same as not_null | not used by Option B |
| feed | load_rules.phi_columns | PHI/PII yes | not used by Option B |
| feed | load_rules.recycle | 1.2 recycle rule / 1.3 recycle table | recycle DDL, DQ row, ADLS cells |
| feed | audit_columns | flat: the audit rows; segmented: the Detail audit rows | DDL audit columns |
| feed | fields[] | 1.2 field rows in sheet order / 1.3 field rows grouped by segment | everything column-level |
| feed | segmented (block) | segmented only: segments_found, row_counts, identification, provenance_notes, segment_audit | per-segment DDL, CONFIRM items |

Contract-level validation that must hold (an invalid contract is a pair-level error): field_count
equals the number of fields; every column named in load_rules and recycle.applies_to is a
field's source_column; the set of fields with phi true equals phi_columns; segment annotations
(record_segment, stage_table) are all-or-nothing across a feed and always set together; audit
datatypes are only `String` or `Timestamp`; feed_ids are unique; at least one audit column and
one field.

### 1.6 FRD feed contract

The FRD contract is the upstream agent's machine-readable output (one document → one contract,
one or more feeds). Unknown keys are rejected; nullable fields must be present as null. Fields
consumed by Option B are marked ✔; every other field must still be present and valid.

| Field | Type | FRD document section (as the upstream agent names it) | Option B use |
| --- | --- | --- | --- |
| contract_name | text | — | banner line 1; the file that holds the FRD is looked up under this name (see 6) |
| generated_from_frd, generated_date (ISO timestamp), generator, status (`PASS` / `PASS_WITH_FLAGS` / `FAIL`) | text | — | validated only |
| project.project_id (nullable), project.project_name, project.business_context_summary (nullable) | text | title block | validated only |
| in_scope, out_of_scope, system_interfaces, open_items | lists of text | scope sections | validated only |
| assumptions_constraints_dependencies[] | {name, description, acd_type ∈ Assumption/Constraint/Dependency} | ACD table | validated only |
| `_provenance` | optional block; when present it must carry all three keys: `enrichments` (list of text), `ambiguities` (list; each entry is either plain text or a block with required `id` (text), `kind` ∈ {attribution, disagreement, advisory_grounding}, `text`, `has_candidates` (boolean) and optional `candidates` (list of text) and `context` (block whose keys feed_names, feed_indices, rule, field, agent_value, content_value, path, feed_index are all optional)), `grounding` (block with required `strict_checked` (integer), `strict_failed` (list of text), `advisory_checked` (integer), `advisory_flagged` (list of text)) | — | validated only; a malformed block rejects the contract |
| feeds[].feed_name ✔ | text | feed heading | join key via slug(); OBJECT_NAME, PROCESS_NAME, DESCRIPTION, TEMPLATE_NAME, SUBJECT, PIPELINE_DESCRIPTION, table COMMENT |
| feeds[].source_system ✔ | text | Source System | SOURCE, SUPPLIER, vendor_name, APPLICATION_NAME, table COMMENT, landing synthesis |
| feeds[].file_name_patterns ✔ | list ≥ 1 | File Name / Pattern | pairing; SRC_FILE_NAME, FILE_NAME (`; `-joined) |
| feeds[].file_format ✔ | text (`csv`, `psv`, `txt`, …) | File Format | SRC_FORMAT, FILE_TYPE; implied delimiter for csv/psv |
| feeds[].delimiter ✔ | text or null | File Format / Delimiter | resolution 1.7; SRC_FILE_DELIMITER badge |
| feeds[].record_segments ✔ | list ⊆ {Header, Detail, Trailer} (empty for flat feeds) | Functional Requirement (record types) | dialect (must match the workbook) |
| feeds[].frequency ✔ | text or null | Load Frequency / SLA | FREQUENCY, PIPELINE_FREQUENCY, FAQ prefill, Layer 2 excerpt |
| feeds[].load_windows_sla ✔ | list of text | Load window / SLA | Layer 2 excerpts only |
| feeds[].lobs ✔ | list of text (must be non-empty) | LOB | LOB cells (`, `-joined), WF name component |
| feeds[].domain ✔, sub_domain ✔ | text or null | Domain / Sub-domain | DOMAIN/SUBDOMAIN cells, SET TAGS, WF/NB names, TGT_ADLS_PATH, landing synthesis |
| feeds[].landing_location ✔ | text or null | Structural Metadata → ADLS Location | stage LOCATION, SRC_CONTAINER_NAME, SRC_ADLS_PATH |
| feeds[].stage_target ✔ {catalog (nullable), schema (nullable), tables, load_strategy} | block | Structural Metadata → Target Schema (stage) + Load Strategy STG | pairing, stage catalog, table accounting, TGT_REFRESH_TYPE, FAQ load_mode prefill |
| feeds[].standard_target ✔ {same shape; tables may be empty} | block | Structural Metadata → Target Schema (standard) + Load Strategy STD | standard presence, catalog, TGT_LOAD_OPTION (standard), TGT_REFRESH_TYPE |
| feeds[].validation_rules ✔ | list of text | Data Quality / Functional Requirements | rule classification (5.1), AS-IS switch, MAPPING_EXPRESSION, Layer 2 |
| feeds[].recycle_rule ✔ | text or null | Data Quality (recycle) | window agreement (1.7), segmented recycle (1.3) |
| feeds[].history_backfill, archive_retention, phi_pii_notes, sttm_reference | text or null | — | validated only |
| feeds[].requirement_ids | list of text | — | validated only |

Load strategy values allowed: `Truncate and Load`, `Append`, `Upsert`.

Validation details that matter for accept/reject: the key spellings `schema_name` (for `schema`)
and `provenance` (for `_provenance`) are also accepted; `generated_date` accepts any ISO-8601
timestamp (offset or `Z` forms) and also a numeric epoch; `record_segments` is not checked for
duplicates (a duplicated segment name yields duplicated segment tables downstream); an FRD that
declares exactly one segment resolves to a one-segment feed that the DDL/IIG builders treat as
NOT segmented (segment count 1) — its single segment must be `Detail`; an empty `lobs` list is
accepted by the contract and rejected only at resolution (1.7 row 6).

Synthetic excerpt (one feed; `; ` separates list items, `(null)` is an absent value):

| Feed field | Value |
|---|---|
| feed_name | Syn Gadget Events |
| source_system | SynVendor Analytics |
| file_name_patterns | gadget_events_CCYYMMDD_HHMM.psv |
| file_format | psv |
| delimiter | \| |
| record_segments | (empty list) |
| frequency | Weekly Monday 8 PM |
| load_windows_sla | Weekly Monday 8 PM |
| lobs | Region 1 ; Region 2 |
| domain | Claims |
| sub_domain | Gadget Events |
| landing_location | (null) |
| stage_target.catalog | (null) |
| stage_target.schema | stg_syn |
| stage_target.tables | syn_gadget_events ; syn_gadget_events_recycle |
| stage_target.load_strategy | Truncate and Load |
| standard_target.catalog | (null) |
| standard_target.schema | syn |
| standard_target.tables | syn_gadget_events |
| standard_target.load_strategy | Upsert |
| validation_rules | [1] Process shall fail when file layout is not as per source dictionary. ; [2] Duplicate file name check shall be turned off for this feed. ; [3] Email notification should be sent to the Support team whenever there is an issue. ; [4] Column GADGET_NM is mapped to GADGET_NAME in the standard layer. ; [5] Records failing the reference check are moved to the recycle table. |
| recycle_rule | Recycle Flag (Enabled for 10 Days) Y (Check with GADGET_KEY from GadgetMaster in the SYN_STD.GADGETS.GDG_MASTER FOR GRP_CD = 9, If available, process it else load this to the Recycle Table with Recycle Flag Enabled for 10 days.) |
| history_backfill, archive_retention, phi_pii_notes, sttm_reference | (null) |
| requirement_ids | (empty list) |

### 1.7 Resolution — joining one FRD feed with one mapping-contract feed

Every disagreement is a loud error naming the feed, the field and both values; there is no
partial resolution: one failing feed fails the whole pair (5.4).

| # | Rule | Error text (exact) when violated |
| --- | --- | --- |
| 1 | every FRD feed's feed_id (aliases, else slug(feed_name)) must exist in the mapping contract and vice versa. Evaluation order: FRD feeds are walked in FRD order and each matched feed is resolved immediately (rows 2–14), so a disagreement in an earlier matched feed is raised before any pairing error is reported; pairing errors are raised together after the loop, FRD-unmatched first (FRD order) then STTM-unmatched (sorted by id), and their error is labelled with the FRD contract_name, i.e. the console reads `contract mismatch for feed '<FRD contract_name>':` | `FRD feed has no STTM mapping: '<name>' (looked for STTM feed_id '<id>')` / `STTM feed '<id>' has no FRD feed` |
| 2 | delimiter: take the explicit values in order (mapping contract first, then FRD); two explicit values that differ → error; none → csv `,`, psv `\|` after lowercasing the FRD file_format (`CSV`, `Psv` also imply); any other format with no explicit value → error. Only the FRD file_format is consulted; the mapping contract's format, name_pattern and frequency are never compared | `delimiter disagrees: STTM says '<a>', FRD says '<b>'` / `format '<f>' has no implied delimiter and neither contract states one` |
| 3 | FRD stage schema, when stated, must equal the mapping contract's stage schema (case-insensitive only for segmented extractions) | `stage schema disagrees: STTM '<a>', FRD '<b>'` |
| 4 | flat feed (FRD declares no segments): the mapping fields must carry no record_segment; the stage table must be in the FRD stage tables; the whole feed becomes one segment named `Detail` | `STTM fields carry record_segment but the FRD declares no segments` / `STTM stage table '<t>' is not among FRD stage tables [...]` |
| 5 | segmented feed (FRD declares segments): the mapping contract must carry segment annotations; the segments are built in FRD `record_segments` order (a duplicated name yields a duplicated segment); every FRD segment needs fields; each segment's fields name one stage table that is in the FRD list; every stage table's catalog is the FRD stage_target catalog (the mapping contract's stage catalog is never used); per-segment standard table: the distinct non-null `standard_table` values of the segment's fields — more than one → error; exactly one AND the feed-level standard block is present → a standard table with catalog = the mapping contract's standard catalog else the FRD standard catalog, schema = the mapping contract's standard schema (fields carrying a standard_table while the feed-level standard block is null are ignored silently); per-segment audit columns = the contract's `segment_audit` list for that segment when present, else none (the feed-wide list applies); the mapping contract must not name segments the FRD does not declare; a Detail segment must exist; the contract's stage.table must be the Detail table | `FRD declares segments [...] but no STTM field carries record_segment/stage_table` / `FRD segment '<s>' has no fields in the STTM contract` / `segment '<s>' maps to multiple stage tables: [...]` / `segment '<s>' stage table '<t>' is not among FRD stage tables [...]` / `segment '<s>' maps to multiple standard tables: [...]` / `STTM fields name segments the FRD does not declare: [...]` / `no Detail segment resolved; the data-carrying segment is required` / `STTM stage.table '<t>' should be the Detail segment table '<d>'` (lists render as `['a', 'b']`) |
| 6 | the FRD feed must list at least one LOB | `FRD feed declares no LOBs; the LOB audit column needs at least one` |
| 7 | side tables derive from the Detail stage table: errors = table + `_errors`, processed files = table + `_processed_files`, recycle = table + `_recycle`; the suffix is uppercased when the table name is entirely uppercase (at least one letter, no lowercase letter) and lowercased otherwise (the configured suffix's own case is never used as-is) | — |
| 8 | recycle (only when the mapping contract's recycle spec exists and is enabled): if the FRD recycle_rule states a window — the first `<digits>` followed by optional whitespace and `day`/`days` (so `10-day` is not a window statement) — it must equal the contract window | `recycle window disagrees: FRD text says <a> days, STTM spec says <b> days` |
| 9 | recycle validation text must parse (case-insensitive), trying form A first, then form B. Form A: `against <id_column> in <table>` where `<id_column>` is one word, `<table>` is a run of word characters and dots (a sentence-ending period is captured into the table name), optionally followed by ` where <filter>` in which the filter is everything up to the END of the text; nothing but whitespace may follow the table or the filter (any other trailing text makes form A fail). Form B: `check with <id_column> from ` + optional `<words> in [the] ` + `<table>` (word characters with at least one dot) + optional ` for <filter>` where the filter stops at the first comma, newline or `)`. The filter is stripped of outer whitespace. This error is raised on its own: disagreements already collected for the feed are not reported alongside it | `recycle validation text is not parseable as 'against <id_column> in <table> [where <filter>]' or 'Check with <id_column> from ... <table> [FOR <filter>]': '<text>'` |
| 10 | recycle table name = the FRD stage table that equals the derived name case-insensitively and is not a segment table, else the derived name | — |
| 11 | every FRD stage table must be a segment table or the recycle table | `FRD stage tables not mapped by any STTM field or recycle rule: [...]` |
| 12 | standard: contract standard present + FRD standard tables empty → error (except segmented extractions, where the STTM supplies the standard target); contract standard table not in the FRD list → error; FRD standard tables present + contract standard null → error; the feed-level standard table's catalog = FRD standard catalog, else the contract's (note the reverse precedence for per-segment tables, row 5); its schema = the contract's standard schema (the FRD standard schema is never compared); standard load strategy = FRD's | `STTM names standard table '<t>' but the FRD standard target is empty` / `STTM standard table '<t>' is not among FRD standard tables [...]` / `FRD names standard tables [...] but the STTM has no standard mapping` |
| 13 | natural key columns = not-null columns = the STAGE column names of load_rules.not_null_columns, in contract order (may be empty); phi columns likewise. The source→stage mapping is one entry per source column name across ALL segments, so when the same source column name appears in several segments the LAST field's stage column is used | — |
| 14 | load_as_is = any FRD validation rule contains `AS` + `IS` as a whole word joined by nothing, by one ASCII hyphen, by one non-breaking hyphen, or by exactly one whitespace character (any case); en/em dashes do not count | — |
| 15 | the sha256 of each contract file's bytes is recorded for the banners | — |

Worked examples:

| Inputs | Result |
|---|---|
| FRD delimiter null, format `csv`, contract delimiter `,` | `,` |
| FRD delimiter `\|`, contract delimiter `\|` | `\|` |
| FRD recycle_rule says `Enabled for 10 Days`, contract window 12 | error `recycle window disagrees: FRD text says 10 days, STTM spec says 12 days` |
| FRD stage tables `syn_gadget_events`, `syn_gadget_events_recycle`; contract stage table `syn_gadget_events`; recycle enabled | recycle table `syn_gadget_events_recycle` (the FRD's spelling); nothing unaccounted |
| stage table `EXT_SYN_DTL` (all uppercase) | errors table `EXT_SYN_DTL_ERRORS`, recycle `EXT_SYN_DTL_RECYCLE` |
| stage table `syn_widget_risk` | errors table `syn_widget_risk_errors` |

### 1.8 Load-pattern FAQ

One file per feed, `<feed_slug>.faq.yaml`, in the configured directory; a missing file (or a
directory of that name) is not an error (every answer defaults with source `unknown`); an
existing file whose top level is not a mapping (empty file, list, scalar) is an error
`FAQ file <path> is not a YAML mapping`. Each answer is a mapping with `value` (required text)
and optional `source` and `evidence`; `source` ∈ `engineer`, `frd`, `contract`, `unknown` and
DEFAULTS to `unknown`, so an answer written without a source counts as unanswered (flagged) and
is overwritten by a contract prefill — always write the source. Unknown keys anywhere are an
error. Values are free text but must be TEXT: in YAML, `yes`, `no`, `true`, `false` and bare
numbers parse as booleans/numbers and reject the whole file — quote them (`"yes"`, `"no"`,
`"100"`). The allowed vocabulary below is the convention, not enforced.

| Question (fixed order) | Allowed values (convention) | Default value / source | Contract prefill (only while source is unknown) | Flag when still unanswered |
| --- | --- | --- | --- | --- |
| load_mode | truncate_and_load, append, merge_on_keys | unknown / unknown | from FRD stage load strategy: `Truncate and Load` → truncate_and_load, `Append` → append, `Upsert` → no prefill; source `contract`, evidence `stage_target.load_strategy: "<value>"` | `faq_unanswered:load_mode` |
| is_master_file | yes, no, unknown | unknown / unknown | none | `faq_unanswered:is_master_file` |
| dedup_within_file | none, row_level, by_keys | none / unknown | none | `faq_unanswered:dedup_within_file` |
| existing_record_policy | plain_append, skip_if_exists, delete_and_insert, unknown | unknown / unknown | none | `faq_unanswered:existing_record_policy` |
| load_frequency | daily, weekly, monthly, yearly, adhoc | unknown / unknown | from the FRD frequency text: leading word (after optional whitespace, followed by a word boundary) `daily`/`weekly`/`monthly`/`yearly`/`annual`/`annually`/`ad hoc`/`ad-hoc`/`ad_hoc`/`adhoc` (case-insensitive; exactly one separator between `ad` and `hoc`) → canonical (annual(ly) → yearly, ad-hoc variants → adhoc); source `contract`, evidence = the whole frequency text; no leading word → no prefill | `faq_unanswered:load_frequency` |
| target_tables_exist | yes, no | yes / unknown | none | `faq_unanswered:target_tables_exist` |
| reject_threshold | number, none | none / unknown | none | `faq_unanswered:reject_threshold` |
| data_integrity_checks | none, not_null_keys, custom | none / unknown | none | `faq_unanswered:data_integrity_checks` |

Companions (not questions: never flagged, never counted):

| Companion | Shape | Effect on Option B |
| --- | --- | --- |
| has_header | answer (value yes/no) | HEADER_FLAG cell when answered (4.2) |
| has_trailer | answer | none on the seven tabs |
| dedup_keys | list | none on the seven tabs |
| dataset_ids {source, target} | text or null | none on the seven tabs (banner counts only) |
| record_type_discriminators {header, detail, trailer, status ∈ assumed_pending_source_team / confirmed} | block | segmented identification override (1.3) |
| natural_key_columns | list | none |

Derived counts used in banners: answered = questions whose source ≠ unknown; from_contract =
answered with source `contract` or `frd`; unknown = 8 − answered.

Example FAQ file (the acceptance feed `syn_widget_risk`; note that the file's frequency answer
carries source `frd` with its own evidence — the prefill alone would have produced the same
value `monthly` but with source `contract` and the verbatim FRD frequency text as evidence):

```yaml-like
schema_version: 1
load_mode:            value: truncate_and_load   source: engineer   evidence: 'FRD Structural Metadata: Load Strategy STG = "Truncate and Load"'
is_master_file:       value: "no"                source: engineer
dedup_within_file:    value: none                source: engineer
existing_record_policy: value: delete_and_insert source: engineer
load_frequency:       value: monthly             source: frd        evidence: 'FRD frequency: "Monthly Run; file received by the fifth business day"'
target_tables_exist:  value: "yes"               source: engineer
reject_threshold:     value: none                source: engineer
data_integrity_checks: value: not_null_keys      source: engineer
has_header:           value: "yes"               source: engineer   evidence: "Vendor file specification: first row carries column names"
has_trailer:          value: "no"                source: engineer
```

(Each answer is a nested mapping with the keys value / source / evidence; the one-line rendering
above is only a compact view.) Contrast: feed `syn_gadget_events` has no FAQ file → load_mode
prefilled `truncate_and_load` (contract), load_frequency prefilled `weekly` (contract, evidence
`Weekly Monday 8 PM`), the other six questions unanswered → six `faq_unanswered:` flags; the
banner reads `2 answered, 6 unknown`.

### 1.9 Engineering standards and naming

Name components (every component is computed even when unused by a pattern):

| Component | Rule | Example |
| --- | --- | --- |
| product, subproduct | sanitize(config product code), sanitize(sub-product code) | `DLK`, `NSP` |
| feed | sanitize(feed_slug) | `syn_widget_risk` → `SYN_WIDGET_RISK` |
| domain, subdomain | abbreviation lookup of the FRD domain / sub_domain in the domain table: the value is sanitized and compared with the sanitized table keys; hit → the table VALUE verbatim (not sanitized); no hit → sanitize(value); null → empty | `Member` → `MBR`; `Widgets` → `WIDGETS`; `Gadget Events` → `GADGET_EVENTS`; null → empty |
| lob | exactly one LOB → lookup in the LOB table (same matching), else sanitize; several LOBs → the multi-LOB code `ALL`; none → empty | `Region 5` → `REG_5`; `Region 1` + `Region 2` → `ALL`; `North` → `NORTH`; `ALL` → `ALL` |
| frequency | EXACT, case-sensitive lookup of the raw FAQ load_frequency value (after prefill) in the frequency table — no sanitize; no hit (including `unknown` or `Monthly` with a capital) → `ADH` | monthly → `MTH`; weekly → `WKL`; unknown → `ADH`; `Monthly` → `ADH` |
| source | abbreviation of source_system via the source table (same matching as domain) — computed but unused by both patterns |  |
| prefix | EXACT lookup of the raw load_frequency value in the job-prefix table (empty when absent) — unused by both patterns |  |
| slug | the raw feed_slug (lowercase) — available to patterns, unused by the two production patterns |  |

Assembly: fill the pattern (a pattern naming a placeholder outside this list crashes the run),
then replace every run of two or more `_` with one `_` and strip leading/trailing `_`. The
notebook name is absent when its pattern is empty. Two table keys that sanitize to the same
text collide (the later one wins).

| Pattern | Filled example |
| --- | --- |
| `WF_{product}_{subproduct}_{feed}_{domain}_{subdomain}_{lob}_{frequency}` | `WF_DLK_NSP_SYN_WIDGET_RISK_MBR_WIDGETS_REG_5_MTH`; with null domain/subdomain: `WF_DLK_NSP_SYN_SENSOR_PINGS_NORTH_ADH` |
| `NB_{product}_{subproduct}_{domain}_{subdomain}_INGEST` | `NB_DLK_NSP_MBR_WIDGETS_INGEST`; with null domain/subdomain: `NB_DLK_NSP_INGEST` |

Abbreviation tables (transcribed from the client Data Engineering Naming Standards document,
tables 3.2–3.6; re-verify against the local document before use). Domain and LOB keys are
matched after sanitize, so `VITAL SIGN` and `vital-sign` both hit; the frequency table is
matched exactly on the raw FAQ value:

| Domain / sub-domain value | Code |
|---|---|
| CLAIMS | CLM |
| CLINICAL | CLIN |
| PROVIDER | PRV |
| NETWORK | NWK |
| VISION | VISN |
| PHARMACY | RX |
| DENTAL | DNTL |
| MEMBER | MBR |
| ENROLLMENT | ENRL |
| ELIGIBLITY (sic) and ELIGIBILITY | ELIG |
| COVERAGE | CVRG |
| LABORATORY | LAB |
| MEDICATION | MED |
| IMMUNIZATION | IMNZ |
| VITAL SIGN | VTL |
| GENERIC | GNR |

| LOB / region value | Code |
|---|---|
| All | ALL |
| All Region | REG_ALL |
| EXCHANGE | REG_EXCH |
| MMP | REG_MMP |
| REGION 1 | REG_1 |
| REGION 2 | REG_2 |
| REGION 5 | REG_5 |
| REGION 6 | REG_6 |

| FAQ load_frequency value | Code |
|---|---|
| hourly | HRL |
| daily | DLY |
| weekly | WKL |
| fortnightly | FRT |
| monthly | MTH |
| quarterly | QTR |
| yearly | YRL |
| adhoc | ADH |
| onetime | ONT |
| history | HST |
| (anything else, incl. unknown) | ADH |

Product code `DLK`, sub-product code `NSP` (client naming standards, product / sub-product
tables). Job prefixes by frequency (daily `D_`, weekly `W_`, monthly `M_`, yearly `Y_`, adhoc
`A_`) exist in the configuration but are not used by either pattern.

Other standards-derived rules used by Option B:

| Rule | Where it lands |
| --- | --- |
| success AND failure alerts go to the production-support distribution list (config `job.notification_emails`) | EMAIL_TO in both EMAIL_TEMPLATE_CONFIG rows, badge "from standards" |
| new tables use Liquid Clustering | `CLUSTER BY AUTO` on every standard-layer table (3) |
| standards status text | banner line `Engineering standards: <status>`; a status starting with `STUB` raises the `standards_stub:` flag |

Catalog / schema conventions: the generator never invents a catalog, schema or table name. Stage
schema and table names come from the STTM stage block and the stage catalog ALWAYS from the FRD
stage target (null → two-part names; the STTM stage catalog is ignored); standard schema and
table names come from the STTM standard block; the feed-level standard catalog is the FRD
standard catalog else the STTM's, while a per-segment standard catalog is the STTM's else the
FRD's (1.7 rows 5 and 12); side-table names come from the naming suffixes (1.7 row 7). A table
name is rendered exactly as spelled in the inputs (no case folding).
## 2. Stage DDL — `<feed_slug>_stage_table_creation.txt`

### 2.1 Filled example (feed `syn_widget_risk`, ACCEPTANCE S1 case 1) with the variable spans marked

```
-- FRD contract: <<frd_contract_name>> sha256 <<sha256>>
-- STTM contract: <<sttm_contract_name>> sha256 <<sha256>>
-- Load-pattern FAQ: sha256 <<faq_sha16 | defaults (no FAQ file)>> — <<answered>> answered, <<unknown>> unknown
-- Engineering standards: <<standards_status>>
-- DDL is engineer-run; the agent never creates target tables (create_tables: false).
-- side-tables omitted from deployment DDL — not in FRD Target Table Name (FRD lists: <<frd_tables>>); omitted: <<omitted_tables>> (CodeGen conventions, kept in ddl/)

--<<qualified_table>>

CREATE OR REPLACE TABLE <<qualified_table>> (
  <<stage_column_1>> STRING COMMENT '<<comment_1>>',
  <<stage_column_2>> STRING COMMENT '<<comment_2>>',
  <<...>>
  <<audit_column_n>> TIMESTAMP COMMENT '<<comment_n>>')
USING delta
COMMENT '<<purpose>> for feed <<feed_name>> (source: <<source_system>>)'
-- SYNTHETIC location — derived from the FRD landing convention; the real
-- container/storage account are assigned by the client platform, never by the agent.
LOCATION '<<synthetic_location_prefix>>/<<landing>>/<<table>>'
TBLPROPERTIES (
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2');

ALTER TABLE <<qualified_table>> SET TAGS ('DOMAIN' = '<<domain>>', 'SUBDOMAIN' = '<<sub_domain>>');
```

The same feed, fully filled (this is the S1 case 1 expected output after sha masking):

```
-- FRD contract: syn_widget_frd sha256 <<sha256>>
-- STTM contract: STTM mapping contract extracted from syn_widget_sttm.xlsx sha256 <<sha256>>
-- Load-pattern FAQ: sha256 <<sha256>> — 8 answered, 0 unknown
-- Engineering standards: Client Data Engineering Naming + Coding Standards
-- DDL is engineer-run; the agent never creates target tables (create_tables: false).
-- side-tables omitted from deployment DDL — not in FRD Target Table Name (FRD lists: syn_widget_risk); omitted: syn_widget_risk_errors, syn_widget_risk_processed_files (CodeGen conventions, kept in ddl/)

--stg_syn.syn_widget_risk

CREATE OR REPLACE TABLE stg_syn.syn_widget_risk (
  widget_id STRING COMMENT 'Widget identifier',
  widget_color STRING COMMENT 'Widget color name',
  risk_score STRING COMMENT 'Widget risk score',
  measured_on STRING COMMENT 'Measurement date',
  owner_ref STRING COMMENT 'Owner reference code',
  LOB STRING COMMENT 'Lob',
  SRC_FILE_NAME STRING COMMENT 'Src File Name',
  REC_CREATION_TIME TIMESTAMP COMMENT 'Rec Creation Time',
  REC_UPDATED_TIME TIMESTAMP COMMENT 'Rec Updated Time')
USING delta
COMMENT 'Stage target table for feed Syn Widget Risk (source: SynVendor Analytics)'
-- SYNTHETIC location — derived from the FRD landing convention; the real
-- container/storage account are assigned by the client platform, never by the agent.
LOCATION 'abfss://syn-container-stage@synstorage.dfs.synthetic.example/syn-landing/inbound/member/widgets/synvendor/syn_widget_risk'
TBLPROPERTIES (
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.minReaderVersion' = '1',
  'delta.minWriterVersion' = '2');

ALTER TABLE stg_syn.syn_widget_risk SET TAGS ('DOMAIN' = 'Member', 'SUBDOMAIN' = 'Widgets');
```

### 2.2 Banner (six lines, identical in both .txt files)

| Line | Content |
| --- | --- |
| 1 | `-- FRD contract: <contract_name> sha256 <sha256 of the FRD contract file bytes, 64 hex>` |
| 2 | `-- STTM contract: <contract_name> sha256 <sha256 of the mapping contract file bytes, 64 hex>` |
| 3 | `-- Load-pattern FAQ: sha256 <first 16 hex of sha256(FAQ file bytes)> — <answered> answered, <unknown> unknown`; when no FAQ file exists the sha span is the literal `defaults (no FAQ file)` |
| 4 | `-- Engineering standards: <engineering_standards.status>` |
| 5 | `-- DDL is engineer-run; the agent never creates target tables (create_tables: false).` (fixed) |
| 6 | `-- side-tables omitted from deployment DDL — not in FRD Target Table Name (FRD lists: <segment stage tables in the FRD record_segments list order (flat feed: the one table)[, recycle table last]>); omitted: <omitted tables sorted, comma-joined> (CodeGen conventions, kept in ddl/)` — always present under the acceptance configuration, because the errors and processed-files tables are always rendered as sources and always omitted (with `deployment_ddl_include_side_tables` true the line is absent, the banner has five lines, and the two side tables render as sections ranked 1 and 2 with purposes `Errors side-table` / `Processed-files ledger` and their own LOCATION) |

The dash in lines 3 and 6 is the em dash `—` (U+2014). The sha256 values are the only spans
that differ between implementations (different serializations of the same inputs); the
acceptance pass criterion masks them: every run of 16 or 64 lowercase hexadecimal characters
that immediately follows `sha256 ` is compared as `<<sha256>>`.

### 2.3 Which tables appear, and in which order

| # | Rule |
| --- | --- |
| 1 | one section per stage table: flat feed → the one stage table; segmented feed → one per segment (two segments naming the same stage table collapse into one section carrying the LAST segment's columns) |
| 2 | plus the recycle table when the feed has a recycle spec that is present AND enabled (purpose "recycle store") |
| 3 | the errors table and the processed-files table are omitted (config `deployment_ddl_include_side_tables` false) and named in banner line 6 |
| 4 | order = purpose rank (stage target table 0, errors 1, processed-files 2, recycle store 3), then the DDL source file name `<stage_schema>.<table>.sql` in byte order |
| 5 | purpose is decided by the table-name suffix (case-insensitive) using the LITERAL suffixes `_errors` → errors side-table, `_processed_files` → processed-files ledger, `_recycle` → recycle store, else stage target table (the configured naming suffixes name the tables but are not consulted here; a non-default suffix would misclassify) |
| 6 | qualified stage table name = `<FRD stage_target catalog>.` (only when non-null) + `<STTM stage schema>.<table>`; the STTM stage catalog is never used |

Contrasting examples: a segmented feed with tables `EXT_SYN_HDR`, `EXT_SYN_DTL`, `EXT_SYN_TRL`
and recycle `EXT_SYN_DTL_RECYCLE` renders `EXT_SYN_DTL`, `EXT_SYN_HDR`, `EXT_SYN_TRL` (byte order
of `STG_SYN.EXT_SYN_DTL.sql` < `…HDR…` < `…TRL…`), then `EXT_SYN_DTL_RECYCLE`. A flat feed with a
recycle spec renders `syn_gadget_events` then `syn_gadget_events_recycle`.

### 2.4 Columns of a stage table

| # | Rule |
| --- | --- |
| 1 | the segment's fields in STTM order, one column per field: `<stage_column> STRING` — the STTM stage DataType is NOT consulted; every business column is STRING |
| 2 | then the audit columns: the segment's own audit list when the contract carries one (segmented feeds; an empty list counts as "carries one" and yields no audit columns), else the feed-wide audit columns; `String` → `STRING`, `Timestamp` → `TIMESTAMP` |
| 3 | the FEED-WIDE audit column names must be among LOB, FILE_TYPE, SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME; any other name is a template gap: the feed FAILs with `no template populates audit column(s) ['<name>', …]; known: ['FILE_TYPE', 'LOB', 'REC_CREATION_TIME', 'REC_UPDATED_TIME', 'SRC_FILE_NAME']`; per-segment audit lists are NOT checked (an unknown name there renders as a column) |
| 4 | the recycle table = the Detail segment's stage columns (STRING), then the FEED-WIDE audit columns, then `FIRST_SEEN_TIME TIMESTAMP` and `RECYCLE_STATUS STRING` |
| 5 | every column line is `  <name> <TYPE> COMMENT '<comment>'` followed by `,` except the last, which is followed by `)` |

### 2.5 Comments

| Element | Rule | Examples |
| --- | --- | --- |
| column COMMENT | a name → description map is built over every field of every segment in FRD segment order, recording the field's NON-EMPTY description under its stage column name and (when present) its standard column name, first occurrence winning; a column whose name is in the map gets that description with whitespace runs (including newlines and other Unicode whitespace) collapsed to one space, outer whitespace removed and `'` doubled; ANY column whose name is not in the map — audit columns, recycle bookkeeping columns, and business columns whose STTM description is empty — gets the fallback: the column name with `_` replaced by a space, then title-cased (each maximal run of letters gets an uppercase first letter and lowercase rest; digits and punctuation end a run: `REC_2ND_TIME` → `Rec 2Nd Time`); a description that is whitespace-only would produce a column line with no COMMENT clause at all (unreachable from a workbook, whose blank cells are empty) | `Gadget's owner name` → `'Gadget''s owner name'`; `Event amount⏎in local currency` → `'Event amount in local currency'`; `SRC_FILE_NAME` → `'Src File Name'`; `LOB` → `'Lob'`; `FIRST_SEEN_TIME` → `'First Seen Time'` |
| table COMMENT | `<Purpose with its first letter uppercased> for feed <feed_name> (source: <source_system>)`, same escaping | `Stage target table for feed Syn Widget Risk (source: SynVendor Analytics)`; `Recycle store for feed Syn Gadget Events (source: SynVendor Analytics)` |

### 2.6 LOCATION, tags, properties

| Element | Rule |
| --- | --- |
| LOCATION (stage layer only) | `<synthetic_location_prefix without trailing />/<landing>/<table>` where landing = the FRD landing_location with every `\` turned into `/` and leading/trailing `/` removed; when landing_location is null or empty, landing = the feed slug; table = the last dotted part of the qualified name. Two fixed comment lines precede it. |
| SET TAGS | `ALTER TABLE <qualified> SET TAGS ('DOMAIN' = '<domain>', 'SUBDOMAIN' = '<sub_domain>');` only when BOTH FRD domain and sub_domain are non-empty; values verbatim (no escaping) |
| TBLPROPERTIES (stage) | the four properties exactly as in 2.1 |
| USING delta | fixed, lowercase `delta` |

Contrasting examples: landing_location `syn-landing\inbound\member\widgets\synvendor` →
`…/syn-landing/inbound/member/widgets/synvendor/syn_widget_risk`; landing_location null for
feed `syn_gadget_events` → `…/syn_gadget_events/syn_gadget_events`; domain `Member` +
sub_domain `Widgets` → tags line present; domain null → no `ALTER TABLE` line at all.

### 2.7 Exact line structure of the file

| Position | Bytes |
| --- | --- |
| start | the six banner lines, each `-- ` + text + newline |
| per table | empty line; `--<qualified>`; empty line; `CREATE OR REPLACE TABLE <qualified> (`; the column lines; `USING delta`; `COMMENT '…'`; the two LOCATION comment lines; `LOCATION '…'`; `TBLPROPERTIES (`; four property lines (the last ends `);`); empty line; then `ALTER TABLE … SET TAGS (…);` when tags exist |
| end | the file ends right after the last table's `ALTER TABLE …;` line (newline-terminated); without tags it ends with the empty line after `);` |
| no tables (standard file of a stage-only feed) | the six banner lines, then ONE EMPTY LINE, then `-- No standard-layer table for this feed (stage-only load).` (newline-terminated), then EOF |
| line endings | LF; UTF-8; no trailing spaces |

## 3. Standard DDL — `<feed_slug>_standard_table_creation.txt`

### 3.1 Filled example (feed `syn_gadget_events`, ACCEPTANCE S2 case 1)

```
-- FRD contract: syn_widget_frd sha256 <<sha256>>
-- STTM contract: STTM mapping contract extracted from syn_widget_sttm.xlsx sha256 <<sha256>>
-- Load-pattern FAQ: sha256 defaults (no FAQ file) — 2 answered, 6 unknown
-- Engineering standards: Client Data Engineering Naming + Coding Standards
-- DDL is engineer-run; the agent never creates target tables (create_tables: false).
-- side-tables omitted from deployment DDL — not in FRD Target Table Name (FRD lists: syn_gadget_events, syn_gadget_events_recycle); omitted: syn_gadget_events_errors, syn_gadget_events_processed_files (CodeGen conventions, kept in ddl/)

--syn.syn_gadget_events

CREATE OR REPLACE TABLE syn.syn_gadget_events (
  gadget_key STRING COMMENT 'Gadget key',
  event_ts TIMESTAMP COMMENT 'Event timestamp',
  gadget_owner STRING COMMENT 'Gadget''s owner name',
  gadget_name STRING COMMENT 'Gadget name',
  event_count INT COMMENT 'Events in window',
  amount DECIMAL(12,2) COMMENT 'Event amount in local currency',
  is_active BOOLEAN COMMENT 'Active flag',
  big_ref BIGINT COMMENT 'Large reference number',
  LOB STRING COMMENT 'Lob',
  SRC_FILE_NAME STRING COMMENT 'Src File Name',
  REC_CREATION_TIME TIMESTAMP COMMENT 'Rec Creation Time',
  REC_UPDATED_TIME TIMESTAMP COMMENT 'Rec Updated Time')
USING delta
COMMENT 'Standard target table for feed Syn Gadget Events (source: SynVendor Analytics)'
CLUSTER BY AUTO
TBLPROPERTIES (
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.checkpoint.writeStatsAsJson' = 'false',
  'delta.checkpoint.writeStatsAsStruct' = 'true',
  'delta.checkpointPolicy' = 'v2',
  'delta.enableDeletionVectors' = 'true',
  'delta.enableRowTracking' = 'true',
  'delta.feature.appendOnly' = 'supported',
  'delta.feature.deletionVectors' = 'supported',
  'delta.feature.invariants' = 'supported',
  'delta.feature.rowTracking' = 'supported',
  'delta.feature.v2Checkpoint' = 'supported',
  'delta.parquet.compression.codec' = 'zstd');

ALTER TABLE syn.syn_gadget_events SET TAGS ('DOMAIN' = 'Claims', 'SUBDOMAIN' = 'Gadget Events');
```

Spans: the banner (2.2, identical to the stage file), `--<<qualified_standard_table>>`, the
column lines, the table COMMENT (`Standard target table for feed <<feed_name>> (source:
<<source_system>>)`), the tags line. Differences from the stage layout: no LOCATION and no
LOCATION comment lines; `CLUSTER BY AUTO` right after the COMMENT line; the thirteen-property
TBLPROPERTIES block.

### 3.2 Which tables, which columns

| # | Rule |
| --- | --- |
| 1 | flat feed: one standard table (the STTM standard block's schema.table, prefixed with the FRD standard catalog, else the STTM standard catalog, when one exists); no standard table → the file carries the banner, an empty line, and one line `-- No standard-layer table for this feed (stage-only load).` (2.7) |
| 2 | segmented feed: one standard table per segment that has a standard table (catalog = the STTM standard catalog, else the FRD standard catalog — the reverse of the flat rule), in byte order of `<std_schema>.<table>.standard.sql`; two segments naming the same standard table collapse into one section with the last segment's columns; a segmented contract whose fields carry NO per-segment standard table but whose feed-level standard block exists renders ONE section from the Detail segment's fields with the feed-wide audit columns |
| 3 | columns = the fields (Detail segment for flat feeds; that segment's fields for segmented ones) that have BOTH a standard column name and a standard datatype, in STTM order, named by the standard column name; a field whose standard column differs from its stage column is renamed here (`gadget_nm` → `gadget_name`) |
| 4 | column type = the type mapping below applied to the STTM standard DataType, EXCEPT when the feed is AS-IS (1.7 row 14): then every business column is `STRING` and the datatype text is not even validated |
| 5 | then the audit columns exactly as in the stage table (segment list when present, else feed-wide) |
| 6 | no recycle / errors / processed-files sections ever appear in the standard file |

### 3.3 Type mapping (STTM standard DataType → Delta type)

Applied to the STTM text after stripping outer whitespace; the lookup is case-insensitive.

| STTM standard DataType (any case) | Delta type |
| --- | --- |
| `string` | `STRING` |
| `int`, `integer` | `INT` |
| `bigint` | `BIGINT` |
| `timestamp` | `TIMESTAMP` |
| `date` | `DATE` |
| `double` | `DOUBLE` |
| `float` | `FLOAT` |
| `boolean` | `BOOLEAN` |
| `decimal(p,s)` — spaces allowed around the digits and inside the parentheses, e.g. `Decimal (10, 2)` | `DECIMAL(p,s)` with the spaces removed |
| anything else (`varchar`, `numeric`, `number`, `datetime`, `decimal` without precision, an empty string, …) | template gap → the feed FAILs with `no SQL type mapping for contract datatype repr(text as given, unstripped)` (unless the feed is AS-IS, in which case the value is never inspected) |

Audit column types use the same mapping on the contract's `String` / `Timestamp` literals.
When a feed has several template gaps only the first is reported, in this evaluation order: a
segmented feed without an extraction block whose segment has no configured record-type value;
the Detail segment's standard datatypes (evaluated even on segmented feeds); each segment's
standard datatypes in FRD segment order; the recycle key not being a Detail stage column; the
recycle filter not being a simple `<column> = <value>` equality; then, at emit time, the
feed-wide audit column names (2.4 row 3).

Examples: `Decimal(10,2)` → `DECIMAL(10,2)`; `BigInt` → `BIGINT`; `Date` → `DATE`; `varchar` on
a non-AS-IS feed → FAIL; `varchar` on an AS-IS feed → `STRING`.

### 3.4 Everything else

Banner, comments, column line syntax, tags rule, line endings and the blank-line structure are
identical to Section 2 (2.2, 2.5, 2.6, 2.7), with `CLUSTER BY AUTO` in place of the LOCATION
block and the thirteen-property TBLPROPERTIES block in place of the four-property one.
## 4. IIG workbook — `config_rows.xlsx`

### 4.0 Workbook structure, badges, blanks

| Element | Rule |
| --- | --- |
| sheets, in order | `DATA_FACTORY_PIPELINE_SCHEDULE`, `ADLS_DELTA_INGESTION_DETAILS`, `STGDELTA_STDDELTA_INGESTION_DET`, `DATA_QUALITY_RULES`, `DATABRICKS_NOTEBOOK_DETAILS`, `EMAIL_TEMPLATE_CONFIG`, `ALL_FILES_STATIC_INFORMATION`, `_provenance`, `_inputs` |
| header row | row 1 of each tab = the tab's headers verbatim (spelling and order transcribed from the client IIG workbook, including `CRETAED_BY` and the lowercase `domain`, `subdomain`, `vendor_name`, `IsFileCopyReqFlag`), bold |
| data rows | one row per built row (multiplicity per tab below), from row 2; a tab with no rows keeps its header row only |
| empty cell convention | a cell with no value is written as the empty string (never the text `NULL`, never a missing column); readers see it as an empty cell — compare empties as equal whether they read back as `""` or as no value |
| cell types | SEQUENCE_NO, SEQ_NM and RECYCL_RETN_DAYS are numeric cells (integers); every other filled cell is text (`ACTIVE_END_DATE` is the text `9999-12-31`, not a date; HEADER_FLAG is the FAQ answer text verbatim) |
| badge | every data cell carries exactly one badge, recorded in `_provenance` and painted as the cell fill (solid fill, colour stored as `00` + the hex below); header cells and the two service sheets carry no fill; the `_provenance` header row is bold, the `_inputs` header row is not |
| byte stability (informative) | the reference implementation pins the workbook's created/modified properties to 2026-01-01 and every zip member's timestamp to 2026-01-01 00:00 so identical inputs give identical bytes; the acceptance criterion is cell-exact, so a rebuild need not match bytes |
| `always_blank` headers | `PIPELINE_ID`, `PARENT_PIPELINE_ID`, `GROUP_ID`, `OBJECT_ID`, `INVENTORY_ID`, `SRC_ADLS_CONNECTION_ID`, `METADATA_CONNECTION_ID`, `TGT_CONNECTION_ID`, `CLUSTER_DETAILS_ID`, `DATABRICKS_WORKSPACE_URL`, `DATABRICKS_WORKSPACE_SECRET`, `DATABRICKS_CLUSTERID` → always empty, badge NEEDS CLIENT TEMPLATE, tooltip present (MANUAL: assigned by the client framework or by client instruction, never by the agent) |
| any other header a tab builder does not fill | empty, badge NEEDS CLIENT TEMPLATE, no tooltip |

Badge labels and fills:

| Badge (internal) | Label written in `_provenance` | Fill (hex) | Counts as "derived" |
| --- | --- | --- | --- |
| from_sttm | `from STTM` | C6EFCE | yes |
| from_sttm_unmapped | `from STTM (unmapped)` | C6EFCE | yes (not used by the seven tabs) |
| from_frd | `from FRD` | DDEBF7 | yes |
| from_faq | `from FAQ` | E4DFEC | yes |
| from_standards | `from standards` | CCECE6 | yes |
| synthetic | `SYNTHETIC` | FFE699 | no |
| needs_template | `NEEDS CLIENT TEMPLATE` | D9D9D9 | no |

`_provenance` sheet: header `tab | row | header | badge | tooltip`; one row per data cell, in
sheet order, row order (Excel row number, first data row = 2), header order; `badge` = the label
above; `tooltip` = the tooltip text or empty. `_inputs` sheet: header `input | value` then five
rows: `FRD contract` (`<name> sha256 <64 hex>`), `STTM contract` (same shape), `Load-pattern
FAQ` (`sha256 <16 hex | defaults (no FAQ file)> — <n> answered, <m> unknown`), `Engineering
standards` (the status text), `Layout` (`client IIG template (anonymized reference —
<<local reference workbook path>>); values carry over`).

Tooltip texts (the tooltip column is informative: the acceptance criterion checks presence, not
text):

| Tooltip key | Text |
| --- | --- |
| always-blank | `assigned by the client framework / manual by client instruction — the agent leaves it blank and flags it.` (the reference implementation names the client organisation in place of "the client") |
| load-strategy stand-in | `the real FRD states this under Structural Metadata → Load Strategy; this build carries a config stand-in.` |
| landing stand-in | `The real FRD states this under Structural Metadata → ADLS Location; this build carries an anonymized stand-in.` |
| synthetic path | `synthetic path shape (from the anonymized reference workbook); the real container/path are assigned at deployment` |
| framework vocabulary | `framework vocabulary from the anonymized reference workbook — confirm with the framework team` |
| FAQ answer | `load-pattern FAQ answer (source: <source>)` or `load-pattern FAQ answer (source: <source>; evidence: "<evidence>")` |
| standards name | `client naming standard pattern applied to FRD facts` (the reference implementation names the client's data office in place of "client") |
| header indicator | `no header indicator in the FRD contract` |
| frequency unknown | `not stated in the FRD` (on the blank FREQUENCY / PIPELINE_FREQUENCY cell when the FRD frequency is null and the FAQ load_frequency is unanswered — a blank cell WITH a tooltip) |
| natural key | `the mapping contract's natural key columns` |
| reject table | `stage table + configured errors suffix` |
| mapping expression | `FRD business rule(s), verbatim` |
| DQ referential source | `FRD DQ: existence check driving the recycle table` |
| DQ referential input | `reference table from the FRD DQ Functional Requirement` |
| DQ not-null | `the mapping contract's not-null columns` |
| DQ trim | `the mapping contract's standard columns` |
| refresh type | `FRD Structural Metadata → Load Strategy (<STG or STD>): '<strategy>' → framework refresh type '<refresh>' (reference IIG vocabulary)` |
| email | `client coding standard: success AND failure alerts to the prod-support DL (synthetic stand-in address)` (the reference implementation names the client's data office) |

Which feed facts feed the rows: for every feed of the FRD contract a row set is built from that
feed's FRD facts plus the resolved feed found by matching slug(FRD feed_name) against the
resolved feed_id; the rows kept are those whose slug equals the run's feed_slug (the run's own
FRD; see Section 6 for the reference implementation's lookup quirk). Rows for other feeds in
the same FRD contract are built and discarded. Consequence: a feed whose feed_id comes from a
`feed_aliases` entry never matches (its resolved feed_id ≠ slug(feed_name)), so its STTM-derived
cells fall to NEEDS CLIENT TEMPLATE and, after filtering, EVERY tab is header-only — do not use
aliases for feeds that need the IIG workbook (Section 6).

Names from the standards (PIPELINE_NAME, DATABRICKS_NOTEBOOK_NAME) are filled only when the
corresponding pattern is non-empty; with an empty pattern the cell is blank, NEEDS CLIENT
TEMPLATE, no tooltip.

In the tables below, "source" names the input; "MANUAL" means never filled by the agent.
Example values are from the acceptance feeds (`syn_widget_risk` unless stated).

### 4.1 DATA_FACTORY_PIPELINE_SCHEDULE (tab 1)

Rows: one per layer — `STAGE` always; `STANDARD` when the feed resolves a standard table.


| Column | Source | Derivation | Example | Badge / when blank |
|---|---|---|---|---|
| PIPELINE_ID | MANUAL | always blank | | NEEDS CLIENT TEMPLATE + tooltip |
| PIPELINE_NAME | standards rule 1.9 | the WF name | `WF_DLK_NSP_SYN_WIDGET_RISK_MBR_WIDGETS_REG_5_MTH` | from standards + tooltip |
| PARENT_PIPELINE_ID | MANUAL | always blank | | NEEDS CLIENT TEMPLATE + tooltip |
| PIPELINE_DESCRIPTION | FRD feed_name | `<feed_name> ingestion (stage)` / `… (standard)` | `Syn Widget Risk ingestion (stage)` | from FRD |
| PIPELINE_FREQUENCY | FRD frequency, else FAQ load_frequency | the FRD frequency text verbatim; when null, the FAQ load_frequency value when answered (from FAQ + tooltip); else blank with the tooltip `not stated in the FRD` (see Section 6 on the never-firing parsed form) | `Monthly Run; file received by the fifth business day` | from FRD; NEEDS CLIENT TEMPLATE + tooltip when neither |
| NO_OF_CYCLE_PER_DAY | — | blank | | NEEDS CLIENT TEMPLATE |
| DAY_OF_SCHEDULE | — | blank in the reference implementation (Section 6) | | NEEDS CLIENT TEMPLATE |
| ACTIVE_FLAG | reference-file constant | `Y` | `Y` | SYNTHETIC + tooltip |
| ACTIVE_START_DATE | — | blank | | NEEDS CLIENT TEMPLATE |
| ACTIVE_END_DATE | reference-file constant | `9999-12-31` | `9999-12-31` | SYNTHETIC + tooltip |
| ESTIMATED_START_TIME | — | blank | | NEEDS CLIENT TEMPLATE |
| APPLICATION_NAME | FRD source_system | verbatim | `SynVendor Analytics` | from FRD |
| CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE | — | blank | | NEEDS CLIENT TEMPLATE |
| PROCESS_NAME | FRD feed_name | verbatim | `Syn Widget Risk` | from FRD |
| SUBPROCESS_NAME | — | blank | | NEEDS CLIENT TEMPLATE |
| LAYER_NAME | layer | `STAGE` / `STANDARD` | `STAGE` | from FRD |
| COMPLETION_SLA, RUNTIME_SLA, CRITICAL_PROCESSING_PERIOD, UDF1..UDF5, IsFileCopyReqFlag | — | blank | | NEEDS CLIENT TEMPLATE |

### 4.2 ADLS_DELTA_INGESTION_DETAILS (tab 2)

Rows: one per stage table — flat feed: one row; segmented feed: one row per segment in the
FRD contract's `record_segments` list order (whatever order it states; the acceptance feed lists
Header, Detail, Trailer). Some cells are filled only on the Detail row (marked "Detail only").


| Column | Source | Derivation | Example | Badge / when blank |
|---|---|---|---|---|
| GROUP_ID, OBJECT_ID, PIPELINE_ID, SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, TGT_CONNECTION_ID | MANUAL | always blank | | NEEDS CLIENT TEMPLATE + tooltip |
| OBJECT_NAME | FRD feed_name | verbatim | `Syn Widget Risk` | from FRD |
| DOMAIN, SUBDOMAIN | FRD domain, sub_domain | verbatim; null → empty string (still badged from FRD) | `Member`, `Widgets` | from FRD |
| SOURCE | FRD source_system | verbatim | `SynVendor Analytics` | from FRD |
| FREQUENCY | FRD frequency, else FAQ load_frequency | verbatim FRD text; else the FAQ answer when answered (from FAQ + tooltip); else blank with tooltip `not stated in the FRD` | `Monthly Run; file received by the fifth business day` | from FRD / from FAQ / NEEDS CLIENT TEMPLATE + tooltip |
| LOB | FRD lobs | joined with `, ` | `Region 1, Region 2` | from FRD |
| CLAIM_TYPE_ID, ACTIVE_FLAG | — | blank (note: ACTIVE_FLAG is blank on this tab) | | NEEDS CLIENT TEMPLATE |
| SRC_CONTAINER_NAME | FRD landing_location, else synthesis (knob `demo.source_files.landing_root_template`, 0.1) | landing = landing_location with `\`→`/`, outer `/` stripped, or the synthesized `<template>` with {domain}/{sub_domain} = slug(FRD value) or `unknown_domain` / `unknown_subdomain`, {source_system} = slug(source_system); container = the text before the first `/` | `syn-landing` (both cases) | from FRD; SYNTHETIC + tooltip when synthesized |
| SRC_ADLS_PATH | same | `/` + the text after the first `/` (or `/` when there is none) | `/inbound/member/widgets/synvendor`; synthesized: `/inbound/claims/gadget_events/synvendor_analytics` | from FRD; SYNTHETIC + tooltip when synthesized |
| SRC_FILE_NAME | FRD file_name_patterns | joined with `; ` | `widget_risk_CCYYMMDD.csv; widget_risk_YYYYMMDD.csv` | from FRD |
| SRC_FORMAT | FRD file_format | verbatim | `csv` | from FRD |
| SRC_COLUMNS | STTM fields of this stage table | `<source_column>:<stage_column>` joined with `,` | `widget_id:widget_id,widget_color:widget_color,…` | from STTM |
| SRC_DATA_TYPE | same | `<source_datatype>:<stage_datatype>` joined with `,` | `String:String,String:String,String:String,Date:String,String:String` | from STTM |
| SRC_FILE_DELIMITER | FRD delimiter, else the resolved delimiter | verbatim | `,` (resolved from csv → from STTM); `\|` (stated in the FRD → from FRD) | from FRD when the FRD states it; from STTM when resolved |
| SRC_REC_LNGTH, SRC_COL_LNGTH, SRC_COL_STRT_END_INDX, SRC_ADLS_ARCHVL_PATH, SRC_COMPRESSION | — | blank | | NEEDS CLIENT TEMPLATE |
| HEADER_FLAG | FAQ has_header | the answer value when answered | `yes` | from FAQ + tooltip; NEEDS CLIENT TEMPLATE + tooltip `no header indicator in the FRD contract` when unanswered |
| MULTILINE_FLAG, SCHEMA_DRIFT_FLAG, FILE_HEADER_FLAG, FILE_FOOTER_FLAG | — | blank (has_trailer is never used here) | | NEEDS CLIENT TEMPLATE |
| MANDATORY_FIELD_LIST | resolved not-null STAGE columns (feed-wide, every row) | joined with `,`; empty string when the feed has none (still badged from STTM) | `gadget_key,event_ts` | from STTM |
| TGT_DATABASE_NAME | stage schema of this table | verbatim | `stg_syn` | from FRD |
| TGT_TABLE_NAME | stage table | verbatim | `syn_widget_risk`; segmented: `EXT_SYN_HDR` on the Header row | from FRD |
| TGT_CONTAINER_NAME | — | blank | | NEEDS CLIENT TEMPLATE |
| TGT_ADLS_PATH | FRD domain/sub_domain + this row's stage table | `/<domain>/<sub_domain>/Processed/<stage_table>` with ONE left-to-right replacement pass of `//` → `/` (one null part collapses cleanly; both null leaves `//Processed/…`, see Section 6) | `/Member/Widgets/Processed/syn_widget_risk`; `/Claims/Gadget Events/Processed/syn_gadget_events`; `//Processed/syn_sensor_pings` | SYNTHETIC + tooltip |
| TGT_COLUMN_NAMES | STTM stage columns of this table | joined with `,` | `widget_id,widget_color,risk_score,measured_on,owner_ref` | from STTM |
| TGT_FORMAT | reference-file constant | `delta` | `delta` | SYNTHETIC + tooltip |
| TGT_DATA_TYPE | STTM stage datatypes | joined with `,` | `String,String,String,String,String` | from STTM |
| TGT_LOAD_OPTION | config stand-in `demo.source_files.load_strategy.stage` | the stand-in text (NOT the FRD strategy; see 4.5 for the FRD-sourced one) | `Truncate and Load` | SYNTHETIC + tooltip |
| TGT_RJT_TABLE_NAME | resolved errors table (Detail only) | the errors side-table name | `syn_widget_risk_errors`; `EXT_SYN_DTL_ERRORS` | from STTM + tooltip |
| TGT_RJT_ADLS_PATH, TGT_PARTITION_COLUMN, TGT_PARTITION_VALUE | — | blank | | NEEDS CLIENT TEMPLATE |
| TGT_PRIMARY_KEY | resolved natural keys (every row) | joined with `,`; cell absent (blank) when the feed has no natural key | `widget_id`; `gadget_key,event_ts` | from STTM + tooltip; NEEDS CLIENT TEMPLATE when no keys |
| RECYCL_ENBL_FLG | recycle presence (Detail only) | `Y` when the feed has a recycle spec, else `N` | `N`; `Y` | from FRD |
| RECYCL_TBL_NM | recycle table (Detail only, recycle feeds only) | verbatim | `syn_gadget_events_recycle` | from FRD; blank otherwise |
| RECYCL_ADLS_PATH | — | blank | | NEEDS CLIENT TEMPLATE |
| RECYCL_RETN_DAYS | recycle window (Detail only, recycle feeds only) | the integer | `10`; `15` | from STTM; blank otherwise |
| MAPPING_EXPRESSION | FRD validation rules (Detail only) | the rules whose lowercase text contains `mapped to`, joined with `; `; blank when none | `Column GADGET_NM is mapped to GADGET_NAME in the standard layer.` | from FRD + tooltip; NEEDS CLIENT TEMPLATE when none |
| CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE, FILE_METADATA | — | blank | | NEEDS CLIENT TEMPLATE |

### 4.3 STGDELTA_STDDELTA_INGESTION_DET (tab 3)

Rows: none when the feed has no standard table; otherwise one per segment that has its own
standard table (segmented feeds, in `record_segments` order), or exactly one leg (flat feeds,
and also a segmented contract whose fields carry no per-segment standard table: that single leg
uses the Detail stage table, the feed-level standard table and every segment's fields that have
a standard column). Fields are limited to those with a standard column name; a field with a
standard column but no standard datatype renders `None` inside SRC_DATA_TYPE and an empty
element inside TGT_DATA_TYPE (contract-only situation).

| Column | Source | Derivation | Example | Badge / when blank |
|---|---|---|---|---|
| GROUP_ID, OBJECT_ID, PIPELINE_ID, SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, TGT_CONNECTION_ID | MANUAL | always blank | | NEEDS CLIENT TEMPLATE + tooltip |
| OBJECT_NAME, DOMAIN, SUBDOMAIN, SOURCE, FREQUENCY, LOB | as in 4.2 | same rules | | same |
| ACTIVE_FLAG, SRC_CONTAINER_NAME, SRC_ADLS_PATH, SRC_ADLS_ARCHVL_PATH | — | blank | | NEEDS CLIENT TEMPLATE |
| SRC_TABLE_NAME | stage table of the leg | verbatim | `syn_widget_risk`; `EXT_SYN_HDR` | from FRD |
| SRC_CATALOG_NAME | stage catalog | verbatim; empty string when none (still from FRD) | `` ; `SYN_DLK` | from FRD |
| SRC_SCHEMA_NAME | stage schema | verbatim | `stg_syn` | from FRD |
| SRC_FORMAT | reference-file constant | `delta` | `delta` | SYNTHETIC + tooltip |
| SRC_COLUMNS | STTM fields with a standard column | `<stage_column>:<standard_column>` joined with `,` | `…,gadget_nm:gadget_name,…` | from STTM |
| SRC_DATA_TYPE | same | `<stage_datatype>:<standard_datatype>` joined with `,` | `String:String,String:String,String:Decimal(10,2),String:Date,String:String` | from STTM |
| TGT_CATALOG_NAME | standard catalog | verbatim; empty when none | `` ; `SYN_STD` | from FRD |
| TGT_SCHEMA_NAME | standard schema | verbatim | `syn` | from FRD |
| TGT_TABLE_NAME | standard table | verbatim | `syn_widget_risk` | from FRD |
| TGT_CONTAINER_NAME, TGT_ADLS_PATH | — | blank | | NEEDS CLIENT TEMPLATE |
| TGT_COLUMN_NAMES | standard columns | joined with `,` | `gadget_key,event_ts,gadget_owner,gadget_name,…` | from STTM |
| TGT_FORMAT | reference-file constant | `delta` | `delta` | SYNTHETIC + tooltip |
| TGT_DATA_TYPE | STTM standard datatypes (verbatim STTM text, NOT the Delta mapping) | joined with `,` | `String,String,Decimal(10,2),Date,String` | from STTM |
| TGT_LOAD_OPTION | FRD standard load strategy | verbatim | `Append`; `Upsert` | from FRD (SYNTHETIC with the config stand-in only when the feed has no standard strategy, which cannot happen on this tab) |
| TGT_RJT_TABLE_NAME, TGT_RJT_ADLS_PATH, TGT_PARTITION_COLUMN, TGT_PARTITION_VALUE | — | blank | | NEEDS CLIENT TEMPLATE |
| TGT_PRIMARY_KEY | natural keys | joined with `,`; blank when none | `widget_id` | from STTM + tooltip; NEEDS CLIENT TEMPLATE when none |
| CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE | — | blank | | NEEDS CLIENT TEMPLATE |

### 4.4 DATA_QUALITY_RULES (tab 4)

Rows (in this order, only those that apply): (a) a referential-check row when the feed has a
recycle spec; (b) a not-null check row when the feed has not-null columns; (c) a trim row when
the feed has a standard table. SEQUENCE_NO is the 1-based position among the rows that exist.


| Column | Row (a) referential | Row (b) not-null | Row (c) trim | Badge |
|---|---|---|---|---|
| GROUP_ID, OBJECT_ID | blank (MANUAL) | blank | blank | NEEDS CLIENT TEMPLATE + tooltip |
| SEQUENCE_NO | running number | running number | running number | SYNTHETIC + tooltip |
| RULE_TYPE | `Custom` | `Predefined` | `STDDelta` | SYNTHETIC + tooltip |
| RULE_CLASS | `ReferentialCheckRule` | `CheckRule` | `LRTrimRule` | SYNTHETIC + tooltip |
| ACTIVE_RULE_FLG | `Y` | `Y` | `Y` | SYNTHETIC + tooltip |
| SOURCE_COLUMN | the STAGE column of the recycle `applies_to` source column, looked up across all segments' fields (the last segment wins when a source name repeats) (from FRD + tooltip) | the not-null stage columns joined with `,` (from STTM + tooltip) | every standard column across all segments, `record_segments` order, joined with `,` (from STTM + tooltip) | see cells |
| INPUT_PARAM | the recycle reference table (from FRD + tooltip) | blank, NEEDS CLIENT TEMPLATE, no tooltip | blank, NEEDS CLIENT TEMPLATE, no tooltip | see cells |
| TARGET_COLUMN | the recycle reference id column (from FRD, no tooltip) | same as SOURCE_COLUMN | same as SOURCE_COLUMN | see cells |
| CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE | blank | blank | blank | NEEDS CLIENT TEMPLATE |

Examples: feed `syn_gadget_events` → rows 1 (Custom/ReferentialCheckRule, SOURCE_COLUMN
`gadget_key`, INPUT_PARAM `SYN_STD.GADGETS.GDG_MASTER`, TARGET_COLUMN `GADGET_KEY`), 2
(Predefined/CheckRule, `gadget_key,event_ts`), 3 (STDDelta/LRTrimRule, all eight standard
columns). Feed `syn_sensor_pings` (stage-only, no recycle) → one row (Predefined/CheckRule,
`sensor_id`). The segmented feed (no natural key) → rows 1 (referential, `SYN_MEMBER_ID`,
`SYN_DLK.STG_SYN.syn_member_ref`, `SYN_MEMBER_ID`) and 2 (trim over the seven standard columns
of all three segments).

### 4.5 DATABRICKS_NOTEBOOK_DETAILS (tab 5)

Rows: one per layer (STAGE; STANDARD when a standard table exists).

| Column | Source | Derivation | Example | Badge |
|---|---|---|---|---|
| PIPELINE_ID, GROUP_ID, DATABRICKS_WORKSPACE_URL, DATABRICKS_WORKSPACE_SECRET, DATABRICKS_CLUSTERID, CLUSTER_DETAILS_ID | MANUAL | always blank | | NEEDS CLIENT TEMPLATE + tooltip |
| PIPELINE_NAME | standards rule 1.9 | the WF name | `WF_DLK_NSP_SYN_GADGET_EVENTS_CLM_GADGET_EVENTS_ALL_WKL` | from standards + tooltip |
| SEQ_NM | position | `1` for STAGE, `2` for STANDARD (integers) | `1` | SYNTHETIC + tooltip |
| PROCESS_NAME | FRD feed_name | `Stage Load for <feed_name>` / `Standard Load for <feed_name>` | `Stage Load for Syn Widget Risk` | from FRD |
| TGT_REFRESH_TYPE | FRD load strategy of the layer | `Truncate and Load` → `Overwrite`; `Append` → `Append`; `Upsert` → `Upsert` | `Overwrite`; `Upsert` | from FRD + tooltip |
| ACTIVE_FLAG | reference-file constant | `Y` | `Y` | SYNTHETIC + tooltip |
| DATABRICKS_NOTEBOOK_PATH | — | blank | | NEEDS CLIENT TEMPLATE |
| DATABRICKS_NOTEBOOK_NAME | standards rule 1.9 | the NB name | `NB_DLK_NSP_MBR_WIDGETS_INGEST` | from standards + tooltip |
| CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE, DQ_NOTEBOOK_PATH, DELETE_DATABRICKS_NOTEBOOK_NAME | — | blank | | NEEDS CLIENT TEMPLATE |

### 4.6 EMAIL_TEMPLATE_CONFIG (tab 6)

Rows: exactly two, `Success` then `Failed`.

| Column | Source | Derivation | Example | Badge |
|---|---|---|---|---|
| TEMPLATE_NAME, PROCESS_NAME | FRD feed_name | verbatim | `Syn Widget Risk` | from FRD |
| STATUS | fixed | `Success` / `Failed` | | SYNTHETIC + tooltip |
| ACTIVE_FLAG | fixed | `Y` | | SYNTHETIC + tooltip |
| SUBJECT | FRD feed_name | `<feed_name> Load Success` / `<feed_name> Load Failed` | `Syn Widget Risk Load Failed` | SYNTHETIC + tooltip |
| BODY, SENDER_NAME, SENDER_EMAIL, EMAIL_CC, CRETAED_BY, CREATED_AT, UPDATED_BY, UPDATED_AT, EMAIL_NOTIFICATION_URL | — | blank | | NEEDS CLIENT TEMPLATE |
| EMAIL_TO | config `job.notification_emails` | entries joined with `;` | `syn.dl.prodsupport@synthetic.example` | from standards + tooltip |

### 4.7 ALL_FILES_STATIC_INFORMATION (tab 7)

Rows: exactly one.

| Column | Source | Derivation | Example | Badge |
|---|---|---|---|---|
| INVENTORY_ID, OBJECT_ID | MANUAL | always blank | | NEEDS CLIENT TEMPLATE + tooltip |
| FILE_NAME | FRD file_name_patterns | joined with `; ` | `widget_risk_CCYYMMDD.csv; widget_risk_YYYYMMDD.csv` | from FRD |
| DESCRIPTION, PROCESS_NAME | FRD feed_name | verbatim | `Syn Widget Risk` | from FRD |
| LOB | FRD lobs | joined with `, ` | `Region 5` | from FRD |
| GOVT_PROGRAM_NM | — | blank | | NEEDS CLIENT TEMPLATE |
| FILE_TYPE | FRD file_format | verbatim | `csv` | from FRD |
| SUPPLIER, vendor_name | FRD source_system | verbatim | `SynVendor Analytics` | from FRD |
| SUPPLIER_CONTACT_PH, SUPPLIER_EMAIL, GENERATOR, GENERATOR_CONTACT_PH, GENERATOR_EMAIL | — | blank | | NEEDS CLIENT TEMPLATE |
| FREQUENCY | FRD frequency, else FAQ | as in 4.2 | `Weekly` | from FRD / from FAQ |
| ACTIVE_TERM_STATUS | fixed | `Y` | `Y` | SYNTHETIC + tooltip |
| INTERNAL_CONTACT_NM, INTERNAL_CONTACT_EMAIL, LAST_SUCCESS_PROCESSED_DATE, NEXT_EXPECTED_RECEIVE_DT, FILE_RECEIVE_PER_FREQUENCY, FILE_TR_MODE | — | blank | | NEEDS CLIENT TEMPLATE |
| domain, subdomain | FRD domain, sub_domain | verbatim; null → empty (from FRD) | `Member`, `Widgets` | from FRD |
| CREATED_DATE, UPDATED_DATE | — | blank | | NEEDS CLIENT TEMPLATE |

### 4.8 One value, many names

| Value | Lands in |
|---|---|
| FRD feed_name | OBJECT_NAME (tabs 2, 3); PROCESS_NAME (tabs 1, 6, 7); DESCRIPTION (7); TEMPLATE_NAME (6); inside PIPELINE_DESCRIPTION (1), SUBJECT (6), PROCESS_NAME (5); table COMMENT (Sections 2, 3) |
| FRD source_system | SOURCE (2, 3); APPLICATION_NAME (1); SUPPLIER and vendor_name (7); table COMMENT; landing synthesis |
| FRD frequency | FREQUENCY (2, 3, 7); PIPELINE_FREQUENCY (1); FAQ load_frequency prefill → frequency code in the WF name |
| FRD lobs | LOB (2, 3, 7); LOB code in the WF name |
| FRD domain / sub_domain | DOMAIN / SUBDOMAIN (2, 3); domain / subdomain (7); TGT_ADLS_PATH (2); SET TAGS (Sections 2, 3); WF and NB names; landing synthesis |
| FRD file_name_patterns | SRC_FILE_NAME (2); FILE_NAME (7) |
| FRD file_format | SRC_FORMAT (2); FILE_TYPE (7) |
| stage table | TGT_TABLE_NAME and TGT_ADLS_PATH (2, per row); the Detail table also TGT_RJT_TABLE_NAME and RECYCL_TBL_NM (2) via the side-table suffixes; SRC_TABLE_NAME (3); `--<qualified>` sections (Section 2) |
| resolved not-null stage columns | MANDATORY_FIELD_LIST (2); TGT_PRIMARY_KEY (2, 3); DQ CheckRule SOURCE/TARGET_COLUMN (4) |
| WF name | PIPELINE_NAME (1, 5) |
| FRD load strategies | TGT_REFRESH_TYPE (5); TGT_LOAD_OPTION (3, standard only); FAQ load_mode prefill → `load_mode_not_enforced` flag; (TGT_LOAD_OPTION on tab 2 is the config stand-in, not the FRD) |
| recycle spec | RECYCL_ENBL_FLG / RECYCL_TBL_NM / RECYCL_RETN_DAYS (2); DQ referential row (4); recycle table section (Section 2) |
## 5. Gate and flags

### 5.1 Rule classification (deterministic; first matching row wins)

Every FRD validation rule is classified once, in contract order. Patterns are matched
case-insensitively anywhere in the rule text unless the row says otherwise. Six classes exist:
`mappable`, `orchestration_config`, `notification`, `out_of_scope`, `flagged`, `unmapped`.
Only `unmapped` rules reach Layer 2; `flagged`, `notification` and `out_of_scope` raise flags;
`mappable` and `orchestration_config` raise nothing.

| # | Pattern (in words) | Extra condition | Class | Note text used in the flag / report |
| --- | --- | --- | --- | --- |
| 1 | `If the <word> column is NULL` followed by an optional comma, one space and `reject` — `<word>` is one run of letters, digits and underscores; `reject` may be the start of a longer word (`rejected`, `rejecting`, `rejection` also match) but nothing may sit between `NULL,` and it | `<word>` equals (case-insensitively) a source or stage column name of the feed AND equals (case-insensitively) one of the resolved not-null STAGE column names | mappable (feature null_reject) | `compiled: rejects.py enforces not-null on '<word>' into the errors table` |
| 1a | same pattern | `<word>` is neither a source nor a stage column name | flagged | `rule names column '<word>' which does not exist in this feed's STTM mapping — unconfirmed attribution (see FRD _provenance ambiguities); no code generated for it` |
| 1b | same pattern | the name exists but is not a not-null stage column (a mandatory field named by a source name that differs from its stage name lands here) | flagged | `rule wants '<word>' rejected on NULL but the STTM does not mark it not-null — contracts disagree; resolve before compiling` |
| 2 | `incomplete record rejection`, or `mandatory column`/`mandatory columns` (followed by a word boundary) then within 80 characters — newlines allowed — a word starting with `reject` | feed has not-null columns | mappable (null_reject) | `compiled: rejects.py enforces not-null on the <n> STTM mandatory column(s) into the errors table` |
| 2a | same | no not-null columns | flagged | `rule wants incomplete records rejected but the STTM lists no not-null/mandatory columns — contracts disagree; resolve before compiling` |
| 3 | `fail when file layout is not as per source dictionary` | — | mappable (drift_fail) | `compiled: drift.py fails the file on layout drift` |
| 4 | `Duplicate file name check` … `turned off` (both on the same line) | — | orchestration_config (allow_duplicate_file_name) | `compiled: feed_spec.ALLOW_DUPLICATE_FILE_NAME = True` |
| 5 | `notification will be sent` / `notification should be sent` / `notification shall be sent` / `email notification` | — | notification | `job JSON carries an email_notifications block; recipients come from config (job.notification_emails)` |
| 6 | `populate <fields> field` or `… fields` `in the target tables` | every listed field (split on `,` and ` and `, lowercased, trimmed) maps via {`source file name`→SRC_FILE_NAME, `file name`→SRC_FILE_NAME, `load timestamp`→REC_CREATION_TIME, `lob id`→LOB, `lob`→LOB} to a column present in the feed's audit columns | mappable (audit_columns) | `compiled: audit.py populates the named audit columns` |
| 6a | same | some field does not map | unmapped | `audit-populate rule names field(s) <repr list of the unresolved names, e.g. ['file type']> that map to no known audit column — sent to Layer 2 for a reviewed candidate` |
| 7 | `validation should be performed against Facets` (the reference platform keyword as spelled in the client FRD) | feed has a recycle spec | mappable (reference_validation) | `compiled: reference.py + recycle.py validate against Facets` |
| 7a | same | no recycle spec | flagged | `rule wants Facets validation but the STTM has no recycle/reference spec for this feed` |
| 8 | `AS-IS` (hyphen or non-breaking hyphen) or `should not perform any data transformation` | — | mappable (identity_mapping) | `compiled: mapping.py is rename-only select, no transformation` |
| 9 | `recycle` | feed has a recycle spec | mappable (recycle) | `compiled: recycle.py, <n>-day window against <reference table>` |
| 9a | `recycle` | no recycle spec | flagged | `FRD states a recycle rule but the STTM has no structured recycle spec for this feed — unconfirmed attribution; no recycle module generated` |
| 10 | `pipe` + exactly one whitespace character or hyphen + `delimited` | resolved delimiter is `\|` | orchestration_config (feature delimiter) | `confirmed: resolved delimiter is '\|'` |
| 10a | same | any other delimiter | flagged (feature delimiter is still recorded) | `MISMATCH: resolved delimiter is repr(delimiter)` |
| 11 | anything else | — | unmapped | `no deterministic template matches — sent to Layer 2 for a reviewed candidate` |

No row produces `out_of_scope`; only a Layer 2 candidate can propose it. Each outcome also
records a "grounding" span for the report: the matched text for rows 1–10 (row 6a: the matched
`populate … tables` span) and the whole rule text for row 11.

Contrasting examples (the difference is the phrasing after `NULL`):

| Rule text | Class |
|---|---|
| `If the WIDGET_ID column is NULL, reject the record and move it to the reject table.` | mappable — `reject` directly follows `NULL,` |
| `If the SENSOR_ID column is NULL, then we are rejecting the record and moving it to the reject table.` | unmapped — the words `then we are` sit between `NULL,` and `rejecting`; the rule goes to Layer 2 (`…is NULL, rejecting the record…` would have matched row 1) |
| `Files are pipe delimited and contain incremental changes.` on a `\|` feed | orchestration_config |
| `Files are pipe-delimited.` on a `,` feed | flagged, note `MISMATCH: resolved delimiter is ','` |
| `Invalid records will be moved to the Recycle table.` on a feed without a recycle spec | flagged |
| `Records failing the reference check are moved to the recycle table.` on a feed with a recycle spec | mappable |
| `Populate file type and source file name fields in the target tables.` | unmapped (`file type` has no audit synonym) |
| `Header, Detail and Trailer data should be mapped to respective HDR, DTL and TRL tables.` | unmapped (also lands in MAPPING_EXPRESSION because it contains `mapped to`) |

### 5.2 Layer 2 (the only LLM-assisted step)

| Aspect | Specification |
| --- | --- |
| what goes in | one call per `unmapped` rule, in contract order; the context pack = feed_id, the rule text, the contract excerpts (every FRD validation rule, then every SLA text, then the frequency text when present) and three column-name lists (source, stage, audit); the user message is the literal line `Context pack (the only citable text):` followed by the pack rendered as an indented (2-space) JSON object with those six keys in that order |
| prompt intent (system message) | ask for a REVIEW CANDIDATE (never deployed directly): exactly one JSON object with exactly four keys — `classification` (one of mappable, orchestration_config, notification, out_of_scope), `code_candidate` (a short PySpark sketch, or the literal null for non-code classes; the key is never omitted), `rationale`, `citations` (a non-empty list of EXACT verbatim substrings of the rule text or the contract excerpts; the column lists are context and never citable); no preamble, no fences; ground every claim in the pack only; no sampling parameters are sent |
| reply extraction | the reply text is stripped; if it starts with `{` and ends with `}` it is used whole; otherwise the first `{…}` block with balanced braces (string-aware) is used; otherwise the stripped text — only then is the schema applied, so fenced or prefixed replies are tolerated |
| required output shape | the four keys above; `rationale` non-empty; `citations` ≥ 1 entry; unknown keys rejected |
| retry | only a schema-invalid reply is retried: the text `Your previous response failed schema validation:` + newline + the validation error + newline + `Respond again with ONLY the corrected JSON object.` is appended (after a blank line) to the accumulating user message, up to the configured attempt budget (2 attempts in total); exhausting it raises the provider failure `no schema-valid response after <n> attempt(s); last error: <last validation error>`; any transport/API exception propagates on the first attempt without using the budget |
| grounding gate | BOTH the citation and every citable text (rule text + excerpts) are canonicalized — in this order: `\\` → `\`, `\"` → `"`, `\n`/`\t`/`\r` → space, curly double quotes → `"`, curly single quotes → `'`, en/em dashes → `-`, `…` → `...`, then whitespace runs collapsed to one space — and the citation must then occur inside one of the citable texts; a citation that canonicalizes to empty always fails; each failure is noted as `citation is not verbatim contract text: repr(citation)` and any failure marks the candidate NOT grounded (it is still recorded) |
| failure gate | a provider exception becomes a candidate with no response and the note `provider '<provider name>' failed: <exception text>`; generation never aborts because of Layer 2 |
| provider selection | dry run → mock; environment variable `CODEGEN_FORCE_MOCK_PROVIDER` set (any non-empty value) → mock; configured provider `databricks_fmapi` → the workspace transport when its configuration resolves (a resolvable configuration without a serving endpoint aborts the run instead of degrading), else mock; otherwise `ANTHROPIC_API_KEY` present → the direct transport, else mock |
| default (mock) provider | classification `mappable`; code_candidate = five lines: `# LAYER-2 CANDIDATE (mock provider) — feed <feed_id>`, `# Rule: <rule text>`, `# Sketch: implement this rule using only columns the STTM defines`, `# (see available_stage_columns / audit_columns in the context pack).`, `# An engineer must replace this sketch before any code lands.` (each newline-terminated); rationale `Mock provider: deterministic stand-in generated without model access, grounded on the rule text alone. Requires engineer review.`; citations = [the rule text] (always grounded); provider name `mock` |
| review artifact | `candidates/candidates.json` is written whenever the candidate list is non-empty — CONFIRM items count, so every segmented feed gets one even with zero Layer 2 candidates; it is a JSON array (2-space indent, trailing newline) of objects with `feed_id`, `rule_text`, `provider`, `response` (null, or the four keys), `grounded`, `failure_notes`; CONFIRM items additionally carry `kind` = `confirm`, `detail`, `citation`; never merged into any output; the seven tabs and the two .txt files never contain model text |
| deterministic review items | segmented feeds add CONFIRM items (5.3) built from the extraction, with citations, placed BEFORE the Layer 2 candidates |

### 5.3 Flags (exact texts, in this order)

| # | Flag text | Trigger |
| --- | --- | --- |
| 1 | `faq_unanswered:<question>` (one per question, question order) | the FAQ answer's source is `unknown` after prefills |
| 2 | `load_mode_not_enforced: declared <load_mode value>; generated writer uses MERGE-by-file (branching planned v2)` | the FAQ load_mode value is anything but `unknown` — i.e. the FAQ answered it, or the prefill filled it (stage strategy `Truncate and Load` or `Append`; an `Upsert` stage strategy with no FAQ answer stays unknown and raises no flag) |
| 3 | `standards_stub: <status>` | the standards status starts with `STUB` |
| 4 | `rule classified <class>: repr(rule text) — <note>` (`— <note>` only when a note exists) | one per rule classified flagged, notification or out_of_scope, in contract order |
| 5 | `confirm item pending (document-derived, cited): <item text>` | one per CONFIRM item, in item order (segmented feeds only) |
| 6 | `Layer-2 provider failed for rule repr(rule): <failure notes joined by "; ">` | a candidate with no response |
| 7 | `Layer-2 candidate NOT grounded for rule repr(rule): <failure notes joined by "; ">` | a candidate whose citations failed grounding |
| 8 | `Layer-2 candidate pending engineer approval: repr(rule)` | a grounded candidate |
| 9 | `generated tests were skipped — PASS cannot be claimed` | the generated-test step was skipped: the run asked to skip tests, or the gate's run-tests knob is off (the acceptance runs and any Option B rebuild skip them; a dry run by itself does NOT skip them) |

Candidate flags (5–8) follow candidate order: CONFIRM items first (identification, then audit
scope), then Layer 2 candidates in rule order. Rule texts are rendered with repr (Section 0):
single quotes unless the rule contains `'`, in which case double quotes. The CONFIRM item texts
(one always, the second only when a segment's audit list differs) are:

| Item | Text | Citation (recorded in the candidate, not in the flag) |
| --- | --- | --- |
| identification (always, on every segmented feed) | `CONFIRM — positional header/detail identification per <<family>>-style spec: trailer marker repr(marker); header = <header rule>; detail = <detail rule>. Confirm with the source team.` — `<<family>>` is a fixed literal naming the segmented feed family; the reference implementation emits the acronym of the client feed that introduced the dialect, which this kit does not carry; the rebuild emits the literal `segmented` there, and every acceptance comparison masks the token between `per ` and `-style spec` as `<<family>>`. Its `detail` text: `Record identification is DERIVED from the documents (<method>), not assumed: the STTM states the trailer's static record-type value, and header/detail follow positionally. This is a soft confirmation, not an assumption gate — the run proceeds; a source-team confirmation closes it.` | the identification citation (1.3) |
| audit scope (only when at least one segment's audit list differs from the feed-wide list — compared as ordered lists, so the same columns in another order count as different) | ONE item: `CONFIRM — audit columns per segment follow the STTM: ` + `<Segment> gets <n>` for each differing segment in name order joined by `; ` + ` vs the feed-wide set (<m>) on Detail. FRD wording could imply feed-wide audit columns on HDR/TRL; the STTM lists fewer — followed STTM, confirm with source team.` Its `detail` text: `The STTM is the column-level authority (FRD: 'Metadata of the tables is provided in the STTM'); each segment table gets exactly its STTM-listed audit rows.` | `FRD rule: repr(the first rule whose lowercase text contains both "populate" and "file type") ('target tables' plural); ` (only when such a rule exists) + `STTM <Segment> audit rows: <cols joined by ", ">` for each differing segment joined by `; ` |

Standing rule for every assumption, conflict or confirm item the agent raises: it must quote
the exact FRD field or STTM cell it rests on (the citation is a required, non-empty field of
the item); an item that cannot cite its evidence is a defect, not an output.

Example flag blocks (from the acceptance feeds):

```
Flags:
- load_mode_not_enforced: declared truncate_and_load; generated writer uses MERGE-by-file (branching planned v2)
- generated tests were skipped — PASS cannot be claimed
**Verdict: PASS_WITH_FLAGS**
```

```
Flags:
- faq_unanswered:is_master_file
- faq_unanswered:dedup_within_file
- faq_unanswered:target_tables_exist
- load_mode_not_enforced: declared truncate_and_load; generated writer uses MERGE-by-file (branching planned v2)
- confirm item pending (document-derived, cited): CONFIRM — positional header/detail identification per <<family>>-style spec: trailer marker '******'; header = first record of the file; detail = every record that is neither the first record nor a record whose first field equals '******'. Confirm with the source team.
- confirm item pending (document-derived, cited): CONFIRM — audit columns per segment follow the STTM: Header gets 3; Trailer gets 3 vs the feed-wide set (5) on Detail. FRD wording could imply feed-wide audit columns on HDR/TRL; the STTM lists fewer — followed STTM, confirm with source team.
- Layer-2 candidate pending engineer approval: 'Populate file type and source file name fields in the target tables.'
- Layer-2 candidate pending engineer approval: 'Header, Detail and Trailer data should be mapped to respective HDR, DTL and TRL tables.'
- generated tests were skipped — PASS cannot be claimed
**Verdict: PASS_WITH_FLAGS**
```

### 5.4 Verdict semantics, failure scoping, exit code

| Verdict | Condition |
| --- | --- |
| `FAIL` | any gate check failed. The gate checks are a lint run (`ruff`), a debug-statement scan (`debug_patterns`), a secret-pattern scan over the generated Python, SQL, JSON, TOML and Markdown files (`secrets`) and a test-file-per-module check (`test_per_module`), all over the generated Python tree, each enabled by configuration (lint by one knob, the other three by another; with both off the console says `no checks run`); when tests are not skipped a fifth check `generated_tests` runs the generated test suite and can fail. An Option B rebuild has no such Python: the four checks trivially pass and are reported as `ruff=ok, debug_patterns=ok, secrets=ok, test_per_module=ok`; a failed check is reported as `<name>=FAIL` |
| `PASS_WITH_FLAGS` | no failed check and at least one flag (with tests skipped flag 9 always exists, so PASS is unreachable) |
| `PASS` | no failed check and no flag |

Errors that stop generation before any verdict (nothing is written for the scope they cover):

| Error source | Scope | Console line | Exit code |
| --- | --- | --- | --- |
| workbook parse or pairing error (Sections 1.1–1.4), or an FRD/workbook file that cannot be found | the whole workbook | `FAIL            extract-sttm — <message>` (success prints `EXTRACTED       <out path> — <n> feed(s): <feed_id> (<k> fields), …`, exit 0) | 1 |
| a contract path given to the generate step that is neither a file nor a file under the contracts directory | the run | `FAIL            contract not found: <value> (also tried <contracts dir>/<value>)` | 1 |
| contract validation error or resolution mismatch (1.5–1.7) | the whole PAIR (every feed of it) | `FAIL            <frd file name> + <sttm file name> — <message>`; a resolution mismatch reads `contract mismatch for feed '<feed>':` followed by one line per disagreement starting with two spaces and `- `; a contract validation error carries the validator's own multi-line layout (`<n> validation errors for <Model>` then location/message lines); a malformed JSON file gives a one-line decode message | 1 |
| template gap (2.4 row 3, 3.3 last row and the gap order stated there, an unparseable recycle filter, a recycle key outside the Detail segment, a segmented feed without identification and without a configured record-type value, and — because the full pipeline is rendered in a scratch tree — the notebook-assembly gaps: a name defined in two generated modules, a module importing another before its cell, a DDL containing a triple quote) | that FEED only; other feeds of the pair continue; in framework mode the feed's `ddl/` sources are already on disk when a later step fails | `FAIL            <feed_id> — template gap: <message>` | 1 |
| `--feed <id>` names no resolved feed | the run (printed after all pairs; also printed when the pair itself failed) | `FAIL            no resolved feed matches --feed repr(id)` | 1 |
| a batch run with an empty pair list | the run | `FAIL            config.contracts.pairs is empty -- nothing to generate. Restore anonymized contract pairs in config/config.yaml or run \`codegen generate --frd-contract X --sttm-contract Y\`.` | 1 |
| anything else (a pair file listed in the batch that does not exist, a FAQ file whose top level is not a mapping or has unknown keys, the demo FRD fallback file missing in framework mode, a live transport configured without its endpoint) | the WHOLE RUN aborts with a traceback and no `FAIL` line; later feeds and pairs are not processed | (traceback) | 1 |

Console line per generated feed: the verdict left-justified in a 15-character field, a space,
the feed_id, ` — `, `<n> flag(s); ` and the check list (`<name>=ok` or `<name>=FAIL` per check,
joined by `, `; `no checks run` when there are none). The process exit code is 0 only when
nothing failed. The generate step accepts a contract path directly or as a name under the
contracts directory.

```
PASS_WITH_FLAGS syn_widget_risk — 2 flag(s); ruff=ok, debug_patterns=ok, secrets=ok, test_per_module=ok
FAIL            syn_widget_frd + syn_widget_sttm_v12.contract.json — contract mismatch for feed 'syn_gadget_events':
  - recycle window disagrees: FRD text says 10 days, STTM spec says 12 days
```

### 5.5 Report file

`reports/<feed_slug>.md` (UTF-8, LF) is written for every generated feed with, in order: the
title `# Generation report — <feed_id>`; `## Contracts` (the two names with their sha256, the
STTM line suffixed ` **(SYNTHETIC stand-in)**` when the contract is marked synthetic); `## Inputs
(three-input model)` with five bullets (standards status; FAQ `<n> answered (<k> from contract),
<m> unknown`; dataset ids `not yet integrated (planned)`; declared load mode and source; write
behaviour `MERGE-by-file (load-mode branching: v2)`); `## Files emitted`; `## Validation rules`
as a table (index, class, feature, rule, grounding span, note — `|` escaped as `\|`); the
segmented-extraction section (segmented feeds only); `## Layer-2 candidates (review required —
never auto-merged)` with `None — every rule compiled deterministically.` or one
`### Candidate n (<provider>, grounded|**NOT GROUNDED**)` / `### Review item n (CONFIRM —
document-derived, cited)` block per candidate; `## Gate` with a table whose result cells read
`pass` or `**FAIL**`; then — only when at least one flag exists — the `Flags:` line and one
`- <flag>` bullet per flag; a blank line; the `**Verdict: …**` line; and, in framework mode, the
framework-output summary appended afterwards. Only the `Flags:` block and the verdict line are
acceptance-tested.

## 6. Known limitations of the reference implementation

These are behaviours a rebuild must know about. Where the acceptance evidence embeds the
behaviour, the rebuild must reproduce it to pass; the "Intended" column says what the
behaviour was meant to be, for a later, deliberate change.

| # | Limitation | Effect on outputs | Intended behaviour |
| --- | --- | --- | --- |
| L1 | the two regular expressions that parse a leading frequency word and a weekday out of the FRD frequency text contain literal backspace characters where word boundaries were meant, so they never match | PIPELINE_FREQUENCY always carries the verbatim FRD text (or the FAQ value); DAY_OF_SCHEDULE is never populated; the unit test pins this output | PIPELINE_FREQUENCY = the leading word uppercased (`WEEKLY`), DAY_OF_SCHEDULE = the weekday (`Monday`), both with a citation tooltip |
| L2 | the IIG builder loads the FRD contract from `<contracts.dir>/<contract_name>` (the JSON `contract_name` field used as a file name, not the file the run was invoked with); when no such file exists it falls back to a configured demo FRD: if that demo FRD holds a feed with the same slug, that (possibly stale) feed supplies every feed-level cell; otherwise the feed is rebuilt from the resolved spec, losing FRD-only facts and always badging SRC_FILE_DELIMITER "from FRD"; when the demo FRD is also absent the run crashes with an unhandled file-not-found error | acceptance evidence was generated with the run's own FRD found by name; a rebuild should simply use the run's FRD | use the run's FRD contract, always |
| L3 | the null-reject pattern requires a word starting with `reject` right after `NULL,` (the comma is optional); the phrasing observed in real FRDs (`…is NULL, then we are rejecting the record…`) has intervening words and is not matched, so it goes to Layer 2 | such rules produce a Layer 2 candidate flag instead of compiling | tolerate intervening words such as `then we are` |
| L4 | an environment variable overrides the notification list at load time, and a local environment file is read at start-up without overriding already-set variables | an operator's local value can silently replace the configured distribution list in EMAIL_TO | keep, but never let a client value into a tracked or shipped file |
| L5 | the reference-platform keyword (the client's core administration platform name as spelled in its FRDs) is hard-coded in two patterns (5.1 row 7; 1.3 recycle table row 2) | rules naming another reference system never compile to a reference validation | make the keyword a configuration knob |
| L6 | TGT_ADLS_PATH collapses `//` with a single left-to-right pass | a null domain and null sub_domain yields `//Processed/<table>` | collapse repeatedly or skip empty parts |
| L7 | the stage LOCATION uses the feed slug when landing_location is null, while the ADLS tab synthesizes a landing path from the template for the same feed | the two artefacts disagree for feeds without a stated landing location | one synthesis rule for both |
| L8 | `generated tests were skipped` is flagged whenever the generated Spark tests are not run (skip flag or gate knob), so `PASS` is unreachable without a Spark environment | every feed is at least PASS_WITH_FLAGS | none needed; keep the honest state |
| L9 | MANDATORY_FIELD_LIST is badged "from STTM" even when empty; DOMAIN/SUBDOMAIN/SRC_CATALOG_NAME/TGT_CATALOG_NAME are badged "from FRD" even when empty | empty cells with a derived badge | badge NEEDS CLIENT TEMPLATE when empty |
| L10 | FILE_HEADER_FLAG and FILE_FOOTER_FLAG are never populated although a `has_trailer` FAQ companion exists; only HEADER_FLAG uses `has_header` | two columns stay blank | map has_header/has_trailer to FILE_HEADER_FLAG/FILE_FOOTER_FLAG |
| L11 | in the segmented parser the first header matching a logical column wins and later duplicates are ignored silently; in the flat parser a duplicate is an error | inconsistent strictness | make both loud |
| L12 | the STTM stage DataType is never used for DDL (stage columns are always STRING); it only surfaces in SRC_DATA_TYPE / TGT_DATA_TYPE cells | by design | — |
| L13 | `out_of_scope` cannot be produced deterministically | only Layer 2 can propose it | — |
| L14 | the console check list names four Python-oriented checks that have no subject in an Option B rebuild | keep the vocabulary for byte-exact summaries | — |
| L15 | 27 of the reference suite's tests skip on the development branch because the anonymized contract fixtures are absent there; they are not evidence of missing behaviour | none | — |
| L16 | Option A (notebook + module tree), the `.sql` sources, `config_inserts.xlsx`, `ADDITION.md`, the demo UI, the SharePoint transport and the volumes/publish transport exist and are shelved for this kit | none | — |
| L17 | a `feed_aliases` entry makes the IIG row lookup miss (rows are matched by slug(FRD feed_name) while the resolved feed carries the alias as its id), so every tab of `config_rows.xlsx` comes out header-only for an aliased feed | aliased feeds get an empty workbook | match rows by the resolved feed id |
| L18 | errors outside the handled set (a listed pair file missing, an invalid FAQ file, the demo FRD fallback missing, a live transport without its endpoint) abort the whole batch with a traceback instead of a `FAIL` line | later pairs are not processed | catch and report per pair |
| L19 | a flat mapping sheet with only one row crashes the parser instead of producing a parse error | none in practice | report `no mapping rows found` |
| L20 | the audit-column template gap is checked only against the feed-wide (Detail) list; an unknown audit column name on a Header/Trailer segment renders silently | possible unpopulated column in a segment DDL | check every segment's list |
