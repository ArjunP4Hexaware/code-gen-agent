# RFC Package Shapes

Structural analysis of RFC deployment packages across three families.
Values are omitted; only naming patterns, sheet layouts, and structural
differences are documented.

---

## 1. INGESTION family

### Folder-tree naming pattern

```
RFC<number>_<FeedOrDomain>/
  <Feed> stage table creation.txt          # always present
  <Feed> standard table creation.txt       # always present
  <Feed>_IIG.xlsx                           # always present
  RFC<number>_<Feed>_Deployment_Playbook.xlsx  # always present
  FILE_LOG_INFORMATION.txt                  # sometimes present
  Operational_RunBook_<Feed>.docx           # sometimes present
  TDD_<description>.docx                    # sometimes present
```

Variations observed:

| File | INGESTION_A (fullest) | PRX\_###### | PRX\_###### |
|---|---|---|---|
| stage DDL .txt | Yes (separate) | Combined in ACCUM\_DDL.txt | Absent (no stage DDL) |
| standard DDL .txt | Yes (separate) | Combined in ACCUM\_DDL.txt | PROD\_PRVDR\_TABLES.txt |
| IIG .xlsx | 7 sheets, 28/55/40/13/19/15/27 col headers | 8 sheets (adds FILE\_ADLS + FIXED\_WIDTH, drops ALL\_FILES) | 3 sheets only (partial) |
| Playbook .xlsx | 7-sheet SFMC template | Single-sheet (Main) | Single-sheet (Main) |
| FILE\_LOG\_INFORMATION | Yes | Absent | Absent |
| Runbook .docx | Yes | Absent | Absent |
| TDD .docx | Yes | Absent | Absent |

### IIG .xlsx structure

**SFMC reference sheets** (7 sheets):

| Sheet | Header row | Header count | Purpose |
|---|---|---|---|
| DATA\_FACTORY\_PIPELINE\_SCHEDULE | 1 | 28 | Pipeline orchestration |
| ADLS\_DELTA\_INGESTION\_DETAILS | 1 | 55 | RAW→Stage config |
| STGDELTA\_STDDELTA\_INGESTION\_DET | 1 | 40 | Stage→Standard config |
| DATA\_QUALITY\_RULES | 1 | 13 | DQ rule definitions |
| DATABRICKS\_NOTEBOOK\_DETAILS | 1 | 19 | Notebook assignments |
| EMAIL\_TEMPLATE\_CONFIG | 1 | 15 | Alert email setup |
| ALL\_FILES\_STATIC\_INFORMATION | 1 | 27 | Source file inventory |

**Per-RFC IIG differences vs SFMC reference:**

| RFC | Sheets | Missing vs SFMC | Extra vs SFMC | Header-count deltas |
|---|---|---|---|---|
| INGESTION_A | 7 | (none) | (none) | All match (28/55/40/13/19/15/27) |
| PRX\_###### | 8 | ALL\_FILES\_STATIC\_INFORMATION | FILE\_ADLS\_INGESTION\_DETAILS (17 cols), ADLS\_FIXED\_WIDTH\_HANDLER (23 cols) | DATA\_FACTORY\_PIPELINE\_SCHEDULE: 16 vs 28; EMAIL: 16 vs 15 |
| PRX\_###### | 3 | ADLS\_DELTA, DATA\_QUALITY, EMAIL, ALL\_FILES | (none) | DATA\_FACTORY: 16 vs 28 |

### FILE\_LOG\_INFORMATION format

Present only in INGESTION_A. T-SQL DDL format:
```
CREATE TABLE [dbo].[FILE_LOG_INFORMATION](
  [ID] [int] IDENTITY(1,1) NOT NULL,
  [PIPELINE_ID] [int] NOT NULL,
  [GROUP_ID] [int] NOT NULL,
  [OBJECT_ID] [int] NOT NULL,
  [SRC_FILE_NAME] [varchar](MAX) NOT NULL,
  [SOURCE_COUNT] [int] NOT NULL,
  [TARGET_COUNT] [int] NOT NULL,
  [REJECT_COUNT] [int] NOT NULL,
  [RECYCLE_COUNT] [int] NOT NULL,
  [CREATED_BY] [varchar](<length>) NOT NULL,
  [CREATED_DATE] [datetime] NOT NULL,
  [UPDATED_BY] [varchar](<length>) NOT NULL,
  [UPDATED_DATE] [datetime] NOT NULL
)
```
Header line: `CREATE TABLE [dbo].[FILE_LOG_INFORMATION](`
Delimiter: comma-separated column definitions.
One row rewritten with type placeholders: `[<col_name>] [<sql_type>](<length_or_max>) <nullable>`.

### Playbook comparison vs SFMC reference

**SFMC reference playbook** (7 sheets):

| Sheet | Header row | Cols | Key headers |
|---|---|---|---|
| Overview | 1–2 | 100 | Day/time grid |
| Cover Page | n/a | 6 | IS Methodology text |
| How to use this template | n/a | 1 | (instructions) |
| PrePost-Prod & Prod Execution | 2 | 67 | #, Task, Task Detail, RFC#s, Deployment Team, dates×6, times×4, Task Owner, Status, Task Dependency, Task Instructions, Comments |
| Rollback Execution | 2 | 19 | #, Task, Task Detail, RFC#s, team, dates×4, times×4, owner, status, dependency, instructions, communication, comments |
| Rollback Validation | 2 | 22 | #, Task, Task Detail, RFC#s, team, dates×4, times×4, owner, RFC, conditions, status, done-by, dependency, instructions |
| Contact List | 1 | 5 | Contact Name, Deployment Team, Cell Phone, Office, Escalation Point |

**Differences per INGESTION RFC playbook:**

| RFC | Matches SFMC template? | Differences |
|---|---|---|
| INGESTION_A | Yes — 7 sheets, same structure | Rows differ: PrePost-Prod=11, Rollback Exec=4, Rollback Val=4. Contact data populated. |
| PRX\_###### | No — 1 sheet (Main) | Single sheet with 10 rows, 126 cols. Headers: Task #, Task, Detail, (blank), RFC#s, Deployment Team, dates/times, Task Owner, Status. No Overview/Cover/Rollback/Contact sheets. |
| PRX\_###### | No — 1 sheet (Main) | Same single-sheet layout as PRX\_######. 9 rows, 126 cols. |

### Runbook .docx

Present only in INGESTION_A (`Operational_RunBook_<Feed>.docx`).
Section headings not extracted (binary .docx).

### TDD .docx

Present only in INGESTION_A (`TDD_<description>.docx`, 2.2 MB).
Section headings not extracted (binary .docx).

---

## 2. EXTRACTION family

### Folder-tree naming pattern

```
<RFC_number>_<Feed>_Extraction/
  <RFC>_<Feed>_PROD_PLAYBOOK.xlsx             # always
  Prod_Metadata.xlsx                           # always
  email_config_inserts.txt                      # always
  ALTER_AUDIT_PROD.ipynb                        # always
  Insert_scripts_config_table_prod.ipynb        # always
  RE_<email_subject>.msg                        # sometimes
  QA_and_A2_Deployment/                         # sometimes
    <RFC>_<Feed>_playbook.xlsx
    QA_Metadata.xlsx
    A2_Metdata.xlsx
    ALTER_AUDIT_QA.ipynb
    Insert_scripts_config_table_q1.txt
    Insert_scripts_config_table_a2.txt
    Alter_audit_DB_Steps.txt
    [dbo].[<stored_proc_name>]_updated.txt
```

Minimal variant (CHG######): single `<number>_PROD_metadata.xlsx` only.

### Metadata .xlsx (per environment)

Sheets (2): `dlk_gold_cnmsptn_extrctn`, `EMAIL_TEMPLATE_CONFIG`.

| Sheet | Header row | Cols | Key headers |
|---|---|---|---|
| dlk\_gold\_cnmsptn\_extrctn | 1 | 41 | ID, PIPELINE\_NAME, PROCESS\_NAME, EXTRACT\_NAME, SEQ\_NO, TGT\_REFRESH\_TYP, INITIAL\_LOAD\_VQUERY, DELTA\_LOAD\_VQUERY, ACTV\_FLAG, STAT, SRC\_TABLE\_NM, LOB\_CD, … |
| EMAIL\_TEMPLATE\_CONFIG | 1 | 16 | TEMPLATE\_ID, TEMPLATE\_NAME, PROCESS\_NAME, STATUS, ACTIVE\_FLAG, SUBJECT, BODY, SENDER\_NAME, SENDER\_EMAIL, EMAIL\_TO, EMAIL\_CC, CRETAED\_BY, … |

Per-environment differences: env name in catalog prefix (pr\_ vs q1\_ vs a2\_),
path prefixes, TEMPLATE\_ID values, email recipients. Query text (INITIAL/DELTA\_LOAD\_VQUERY)
may differ between QA (simplified test queries) and PROD (full production queries).
Row counts identical across environments (EXTRACTION_A: 9 data rows).

### Insert scripts

Target: `<catalog>_dlk.all_config.hedis_meas_submeas_extrct` config table.
Column list: PRCS\_CD, PRCS\_DESC, MEAS\_ROOT\_KEY, MEAS\_ROOT\_SUFFIX\_KEY,
MEAS, SUBMEAS, YEAR, BEGIN\_DT, END\_DT, ACTV\_FLG, CREATE\_USER\_ID,
CREATE\_SYS\_TS, UPDT\_USER\_ID, UPDT\_SYS\_TS, FILTER\_EXPRESSION.
One INSERT rewritten: `INSERT INTO <catalog>_dlk.all_config.<table> (<col_list>) VALUES (<literal>, <literal>, …)`.
Statement count: 32 per file (q1), 16 per notebook (prod, split across cells).

### ALTER\_AUDIT notebooks

| Cell | Purpose |
|---|---|
| 1 | Set environment variable (env="q1" or "pr") |
| 2 | Import datetime, pyspark functions, pyodbc |
| 3 | Build Key Vault connection (scope, username, password, JDBC URL) |
| 4 | SQL DDL: ALTER TABLE to add columns to config tables |
| 5 | Print query (debug) |
| 6–7 | CREATE OR ALTER stored procedure + execute via pyodbc |
| 8–10 | Utility: readTables, readAuditTable (QA only, extra cells) |

QA has 10 cells; PROD has 8 cells (no debug/utility cells).

### Stored-proc and DB-steps files

`[dbo].[create_reexecute_extraction_batch]_updated.txt`: T-SQL CREATE PROCEDURE
for batch re-execution. Parameters: @executionstate, @processname. Manages batch
status transitions and rollback of failed extractions.

`Alter_audit_DB_Steps.txt`: Same stored-proc body as above (identical content).
Present only in QA\_and\_A2\_Deployment/.

---

## 3. OTHER families

### 3a. EDH gold-layer loading (3 RFCs)

Pattern: DDL .txt + IIG(gold) .xlsx + deployment-plan .xlsx + INSERT/SR scripts.

```
RFC<number>_EDH_DOMAIN/  (or ######_FEED_B_EDH/)
  DDL_SCRIPT.txt                             # always
  RFC<number>_IIG.xlsx                        # always (gold-layer sheets)
  EDH_proddeployment_plan.xlsx               # always
  INSERT_SCRIPT.txt                           # always
  SR_Script.txt                               # sometimes
  DDL-PROD/DDL/<table_ddl>.txt               # variant (###### only)
  -1_RECORDS/-1_RECORDS/<insert>.txt         # variant (###### only)
```

IIG sheets for EDH (differ from SFMC reference):

| Sheet | Header row | Cols | Notes |
|---|---|---|---|
| DATA\_FACTORY\_PIPELINE\_SCHEDULE | 1 | 28 | Same as SFMC |
| STGDELTA\_GOLD\_INGESTION\_DETAILS | 1 | 32–35 | Replaces ADLS\_DELTA + STGDELTA\_STDDELTA; adds vquery, Additional\_query, SRC\_TABLES |
| DATABRICKS\_NOTEBOOK\_DETAILS | 1 | 19 | Same as SFMC |
| GOLD\_CONSUMPTION\_BATCH\_AUDIT\_LO | 1 | 9 | Extra: Layer\_Name, Batch\_Start/End\_Time, Status, Type, audit cols |
| EMAIL\_TEMPLATE\_CONFIG | 1 | 15 | Same as SFMC |

### 3b. Materialized-view replacement (2 RFCs)

```
RFC_<number>_MV_Phase_<N>/
  23_<seq>_<mv_table>_script.txt              # per-MV CREATE OR REPLACE
  23_<N>_VENDOR_E_MV_Phase_<N>_Playbook_RFC_<number>.xlsx  # SFMC-template playbook
  MVs_Pipelines_Notebook Details.xlsx         # MV→pipeline→notebook mapping
  Phase<N>_MV_bkps/
    NB_HVR_FACETS_<table>_mv.txt|.ipynb       # backup of original MV notebooks
  Phase<N>_MV_bkps_definitions/
    <table>_backup.sql                         # full MV SQL definitions
```

Phase 2: 9 MV scripts + 9 MV backups + 9 MV definitions + playbook + notebook-details.
Phase 3: empty (only Phase3\_MV\_bkps/ folder, no files).

### 3c. Unified-table DDL (1 RFC)

```
RFC<number>_FEED_EDI_Unified/
  feed_unified_daily.txt                    # one per frequency
  feed_unified_monthly.txt
  feed_unified_quarterly.txt
  feed_unified_weekly.txt
  FEED_EDI_SQL.txt                   # SQL script
  FEED_EDI_TABLE_BACKUP.txt          # backup CREATE TABLE stmts
  RFC<number>_FEED_EDI_Unified_Deployment_Playbook.xlsx  # SFMC-template playbook
```

### 3d. DQ/metadata update (2 RFCs)

```
RFC<number>_FEED_C_TML/                      (or RFC<number>_FEED_C_Inbound_Reporting/)
  feed_metadata_update.txt                                # ALTER TABLE + UPDATE metadata SQL
  PlayBook_RFC_<number>.xlsx                   # single-sheet playbook
  feed_metadata_update_prod.xlsx                           # DATA_QUALITY_RULES sheet only
  feed_metadata_update_qa.xlsx                             # 3 sheets: PIPELINE, NOTEBOOK, DQ
  PROD/
    Insert_script_for_New_DQ.txt
    PlayBook_RFC_<number>.xlsx
    FEED_C_metadata_update_script.txt
  QA/
    QA_DQ_Metadata_feed_c.xlsx                # DATA_QUALITY_RULES sheet only
    FEED_C_metadata_update_script.txt
```

### 3e. Playbook-only / script-only

- `RFC######_OTHER_FEED_D_Provider/`: playbook only (8-sheet SFMC template + Story sheet).
- `SR_EDH_DOMAIN_DimRevenue/`: single `script.txt` (UPDATE statement for IIG metadata).

---

## 4. Playbook shape comparison vs SFMC reference

All playbooks using the SFMC template share 7 sheets:
Overview, Cover Page, How to use this template,
PrePost-Prod & Prod Execution, Rollback Execution,
Rollback Validation, Contact List.

| RFC | Template match | Extra sheets | Row/col deltas |
|---|---|---|---|
| INGESTION_A | Full match | (none) | PrePost rows: 11 vs 14 |
| FEED_EDI | Full match | (none) | PrePost rows: 12 vs 14 |
| MV_PHASE_2 | Full match | (none) | PrePost rows: 14; Rollback Exec: 16 vs 4 |
| OTHER_FEED_D | Partial | +Story (1 sheet) | PrePost rows: 12; Rollback Exec: 20; Rollback Val: 25 |
| PRX\_###### | No match | Single-sheet (Main) | 10 rows, 126 cols |
| PRX\_###### | No match | Single-sheet (Main) | 9 rows, 126 cols |
| EXTRACTION_A (both) | No match | Single-sheet (RFC\_######\_EXTRACTION_A) | 5–6 rows, 19 cols |
| METADATA_UPD_A | No match | Single-sheet (######) | 9 rows, 17 cols |
| METADATA_UPD_B | No match | Single-sheet (RFC\_######) | 5 rows, 19 cols |
| EDH deployments (3) | No match | Single-sheet per RFC | Varies |

Single-sheet playbooks share a common header pattern:
Task #, Task, Detail, [Team], RFC#s, [SR], dates×4, times×4, but with
varying column counts (17–126 cols) and no Rollback/Contact/Overview sheets.
