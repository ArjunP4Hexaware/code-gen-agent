# Metadata DB semantics — the SQL Server config tables behind ACFC's ingestion framework

Transcribed from the Hexaware-internal walkthrough of the framework's
metadata configuration tables by the framework maintainer (recorded
2026-09-11, 39 min; local copy `docs/acfc/SQL_Database_transcript.docx`,
untracked — the repo ignores `*.docx`). This document is the SPEC the DML
emitter (`src/codegen/emit/dml.py`, M7) is built from: every rule the
emitter applies cites a section here. Nothing below is inferred from the
IIG goldens; where the walkthrough and a golden disagree, the disagreement
is listed in §10 and the golden's value is kept for the pair-1 byte-identity
acceptance.

Scope of the walkthrough: **six tables** (§2–§7). The maintainer said the
database holds "close to 10 to 15" configuration tables plus stored
procedures and that the rest would be covered in a later session; every
table the walkthrough did not reach is marked **not yet described** (§8).
Column NAMES below are as spoken; the exact SQL identifiers are confirmed
only where the IIG goldens print the same header (marked ✔).

## 1. Conventions that hold across every table

| Convention | Statement (walkthrough) | Emitter rule |
| --- | --- | --- |
| Audit columns | "These 4 columns will be the default target columns, which will be available in all the configuration tables": CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE. "Created by will populate as a RFC number and even the updated [by] also will be same and the dates will be the get date of when we are trying to create or insert the metadata." The RFC number may also be "our ATMT number". | `CREATED_BY = @RFC_NUMBER`, `UPDATED_BY = @RFC_NUMBER`, `CREATED_DATE = GETDATE()`, `UPDATED_DATE = GETDATE()` on every INSERT. |
| ACTIVE_FLAG | "If active flag is set to yes, then only all entries associated to this process will [be] picked up. … deactivate, you just set some value other than S, then your process is not going to pick the entries which we have marked as not equal to S." The framework selects rows `WHERE ACTIVE_FLAG = 'S'`. | The DML writes the configured active value (`dml.active_flag`, default `'S'` from this statement). The IIG review workbooks keep the goldens' `Y` (§10). |
| Access | Connect to the jump VM, then SQL Server Management Studio with MFA; one database; tables + stored procedures. Credentials are personal (ADMZ) — never in a script. | The notebook reads the JDBC secret NAMES from config and the values from a Databricks secret scope; nothing in the repo holds a credential. |
| Uniqueness of framework IDs | Pipeline ID: "the unique generator and we have to make sure each process should have a unique ID." Group ID: "always we have to maintain a unique group ID … which is not being used by another process, and even in future process also they should not use the same group ID." Connection ID: "auto-generated". | `@PIPELINE_ID` / `@GROUP_ID` are engineer-assigned and pre-checked unused (preflight); connection IDs are identity values captured with `SCOPE_IDENTITY()` or reused. |
| Who assigns what | Engineer: pipeline ID, group ID, object ID (1..n within a group), pipeline name, process/sub-process names, layer. Identity: connection IDs. Platform / Azure team: host names, port numbers, service account, Key Vault secret key, connection string. Business / FRD: domain, subdomain, frequency, LOB. | Variables block comments name the assigner per §2–§7. |

## 2. DATA_FACTORY_PIPELINE_SCHEDULE ✔ (IIG tab of the same name)

Role: "the table where for any new process, our new addition is getting
into the system … Then only the process will start." One row per pipeline
(workflow or ADF pipeline), master and children.

| Column | Meaning (walkthrough) | Assigned by | Emitter |
| --- | --- | --- | --- |
| PIPELINE_ID ✔ | "the unique generator … each process should have a unique ID" | engineer | `@PIPELINE_ID`; preflight asserts unused |
| PIPELINE_NAME ✔ | "the same pipeline name what we are going to be creating … in Azure workflow or … ADF pipeline common standards" | engineer (EDO naming standard) | IIG cell |
| PARENT_PIPELINE_ID ✔ | "for master pipeline, parent pipeline will be there by default to the zero … the child pipeline … I assign my pipeline ID as a parent pipeline ID for my child pipeline" | engineer | `@PARENT_PIPELINE_ID` (0 = master) |
| PIPELINE_DESCRIPTION ✔ | "whatever it is specific to your project or pipeline or workflow" | engineer / FRD | IIG cell |
| PIPELINE_FREQUENCY ✔ | schedule support word (daily / weekly / monthly) | FRD | IIG cell |
| NO_OF_CYCLE_PER_DAY ✔ | "if your workflow is scheduled to run multiple times, then the count will be two or three" | engineer | IIG cell |
| DAY_OF_SCHEDULE ✔ | "as of now, this column, we are not populating, but going forward … if something is monthly or weekly, that information we are going to populate" | — (unused today) | NULL; golden prints `0` (§10) |
| ACTIVE_FLAG ✔ | §1 | — | `dml.active_flag` |
| ACTIVE_START_DATE / ACTIVE_END_DATE ✔ | "by default for our process … we are setting up these two fields as a default. But … as of now, we are not using" | — (defaults) | IIG cell (default `9999-12-31` end) |
| ESTIMATED_START_TIME ✔ | "as of now … not using" | — | NULL |
| APPLICATION_NAME ✔ | "for whatever the project we are working … what will be the application name" | engineer | IIG cell |
| CREATED_BY … UPDATED_DATE ✔ | §1 | — | §1 |
| PROCESS_NAME, SUBPROCESS_NAME (iig_v1 ✔) | "the process name specific to our project we are going to define. And for my process, my work will be the sub-process name" | engineer | IIG cell |
| LAYER_NAME (iig_v1 ✔) | "we have multiple layers like stage layer, gold layer, and standard layer … specify what will be the appropriate layer" | engineer | IIG cell |
| COMPLETION_SLA, RUNTIME_SLA, CRITICAL_PROCESSING_PERIOD (iig_v1 ✔) | "these three columns also, as of now, we are not using … added for future purpose" | — | NULL |
| UDF1 (iig_v1 ✔) | "the column where we're going to check the dependencies … either my source required tables for this particular process has been completed or not" | engineer | NULL unless a FAQ answer names the dependency (none exists today) |
| UDF2 … UDF5 (iig_v1 ✔) | "we are not using anything. This field is also created for future purpose" | — | NULL, always |
| IsFileCopyReqFlag (iig_v1 ✔) | "if there is a file ingestion, so we are going to set this flag to yes or no based on the file requirement. If there is no file ingestion … we'll set it to no" | engineer | `Y` for a file feed (every feed this agent generates is a file ingestion); cited constant |

## 3. File connection details (name as spoken: "file connection" table; not an IIG tab)

Role: "If any file based ingestion is going to happen into our data lake,
we have to enable the connection here because all our framework is
metadata driven … if it is [an] existing file [path], you no need to enable
the connection. You can make use of the existing connection ID itself."

| Column (as spoken) | Meaning | Assigned by |
| --- | --- | --- |
| connection ID | "the unique identifier. It will be auto-generated." | identity |
| connection description | "from which source or which system you are going to be configured … generic information specific to your file system" | engineer |
| host name | "you can get it from the platform team or business team" | platform team |
| port number | "we can get it from platform or Azure team" | platform team |
| username | "service accounts. It is not specific to our [personal ids] … mostly in production, they'll use one service account only for all the path or host accessing" | platform team |
| secret key | "this password will be sitting under key vault. … the platform team … will give this secret key to us. And this secret key will be configured here." | platform team (Key Vault) |
| source type | "is it connection is best for file-based or for API? Mostly we have only two types … Hadoop is already decommissioned" | engineer (`File` / `API`) |
| CREATED_BY … UPDATED_DATE | §1 | — |

Reuse rule: look the connection up by host (and root path) before inserting;
"if there is no connection ID for your new file ingestion, if it is coming
from new path, then you have to make sure you should have an entry in this
table". The exact table and column identifiers were not printed in the
session; the emitter takes them from `dml.connection_table` and flags the
block `dml_unconfirmed:connection_table` until the framework team confirms
the spelling.

## 4. RDBMS connection details (not an IIG tab)

Role: sources "which we are getting data from Oracle … on-prem SQL Server
… Sybase"; "all those RDBMS related server details will be stored here".
Same definition as §3 with: database name, host name, port ("in Dev it is
not there, but in production, the port number will be there"), a system ID
column "we are not using", the connection string ("generated from the
platform team"), host type, and the §1 audit columns. Not used by a file
ingestion; described here for completeness. **Not emitted** by this agent
(the agent only generates file ingestions).

## 5. FILE_ADLS_INGESTION_DETAILS ✔ (iig_v2 tab; file → ADLS copy, "O drive to ADLS")

Role: "once we receive the file from business user or vendor, it will be
sitting in [the] respective O drive or even business folders. So that
folder configuration we are going to be configured here."

| Column | Meaning | Assigned by / value |
| --- | --- | --- |
| GROUP_ID ✔ | "the ID which is getting generated here. We have to pick the unique one" (§1 uniqueness) | engineer, `@GROUP_ID` |
| OBJECT_ID ✔ | "for any given project, there is a scope to run multiple process … For member will assign one and for provider will assign object ID is 2 and claims will assign object ID is 3" — one per input file within the group | engineer, 1..n |
| PIPELINE_ID ✔ | the §2 pipeline | `@PIPELINE_ID` |
| DOMAIN / SUBDOMAIN ✔ | the object's domain (§7 wording) | FRD |
| SRC_CONNECTION_ID ✔ | "we created the connection … this connection ID will have, we are going to populate here" | §3 (variable) |
| SRC_ROOT_DIR ✔ | "your root folder"; single entry with a wildcard copies every file, several entries with a file identification copy per file: "if you are specifically mentioning the file name … whichever the file name starting with … those files only it will capture" | FRD / STTM file pattern |
| TGT_CONTAINER_NAME, TGT_ADLS_PATH ✔ | "the ADLS container details, and ADLS … file path" | platform (container) / FRD landing (path) |
| SOURCE_TYPE ✔ | "by default … file because it's a file-based ingestion" | `File` |
| SRC_EXTRACT_START_TIME ✔ | "based on this extract start time date it will identify what are the latest file which has been received by today itself" (vendors that never delete from the O drive) | engineer |
| COPY_START_TIME_OFFSET_IN_MINUTES ✔ | "in case if you missed a file to be picked yesterday … slightly alter this offset value to pick the yesterday's date information also" | engineer, default 0 |
| TGT_STORAGE_ACCOUNT_NAME ✔ | "sometimes we are doing a copy from within ADLS to ADLS itself … populate the ADLS storage account name and storage container name" | platform |
| delete flag (as spoken; no IIG header) | "if it is true means, then only we are deleting once our copy activity is completed … If flag is set to false, means it will not going to be deleted" | engineer; not in the IIG — not emitted |
| CREATED_BY … UPDATED_DATE ✔ | §1 | §1 |

Primary key (spoken): "for these two tables and even for ADLS to stage
ingestion table also, group ID, object ID, pipeline ID is the combination
of primary key."

## 6. RDBMS → ADLS ingestion (not an IIG tab)

Same key (GROUP_ID, OBJECT_ID, PIPELINE_ID); object ID = "whatever the
object we are going to create in data lake"; domain name; ACTIVE_FLAG;
SRC connection (§4); schema + table name; an optional comma-separated
column list ("if you populate those 5 or 10 columns … our process will pick
only those"); SRC extract type full vs incremental / delta with an
appended `WHERE modify_date > <last run>` maintained by the pipeline; the
silver-layer ADLS container, path, file name and format; target load option
(upsert vs override for a reused file name); source type; offset; audit
columns; storage account name; the incremental query. **Not emitted** (no
RDBMS source in scope).

## 7. ADLS_DELTA_INGESTION_DETAILS ✔ (ADLS → stage / standard-layer Delta table)

Role: "the table where data will be picked from ADLS and it will load to
the [stage] layer tables." Key: GROUP_ID, OBJECT_ID, PIPELINE_ID (§5).

| Column | Meaning | Assigned by / source |
| --- | --- | --- |
| OBJECT_NAME ✔ | "we are creating based on the table which we are creating" — "reference only … whatever you need to maintain based on your project need" | engineer (short token) |
| DOMAIN / SUBDOMAIN ✔ | "we can get this information from FRD, we have to populate the same information" | FRD |
| SOURCE ✔ | "from which source you are going to get" | FRD Data Source / Vendor |
| FREQUENCY ✔ | "is it historical or weekly or whatever the frequency, even this information we can get it from FRD or business users" | FRD (or STTM File Details when the FRD points there) |
| LOB ✔ | "LOB also will get it from FRD. So each process will have a LOB details" | FRD |
| CLAIM_TYPE_ID ✔ | "most of the records it will populated with null only or even NA" | `dml.claim_type_id_default` (NULL) |
| ACTIVE_FLAG ✔ | §1 | `dml.active_flag` |
| SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID ✔ | "same thing, we have to populate from where you need [to read] the ADLS file … metadata connection ID is also same" | connection variables |
| SRC_CONTAINER_NAME, SRC_ADLS_PATH, SRC_FILE_NAME ✔ | "container details … the source path … the source file name also you have to populate same as what you have been created in previous step" | platform / FRD landing / file pattern |
| SRC_FORMAT ✔ | file format | FRD / extension |
| SRC_COLUMNS, SRC_DATA_TYPE ✔ | "if you want to pick column names with limited number … it will pick the same column format … in a sequence. And for each column, we are going to set what will be the data type" | STTM |
| SRC_FILE_DELIMITER ✔ | "sometimes it will be the tab, sometimes it will be the pipe delimiter, sometimes … comma separator, sometimes … fixed width" | FRD / STTM / extension |
| SRC_REC_LNGTH, SRC_COL_LNGTH, SRC_COL_STRT_END_INDX ✔ | "these three columns will be used for fixed width … from which position to which position … not for all the records" | STTM positions; NULL for delimited files |
| SRC_ADLS_ARCHVL_PATH ✔ | "once you load a data into your target table, we have to maintain the same file in archive folder … that is the path" | FRD landing + template shape |
| SRC_COMPRESSION ✔ | "If there is a zip files, we are doing a compression. If it is not, we are not doing anything" | `N` unless the file pattern is `.zip` |
| HEADER_FLAG ✔ | "either your input file is having header" | FAQ `has_header` |
| MULTILINE_FLAG ✔ | "possibility of splitting the same record into multiple lines" | `N` unless stated |
| SCHEMA_DRIFT_FLAG ✔ | "if you are getting any new column from your source … the same column will be automatically … populated in data lake stage table … with a string value. If you set to no … it won't populate anything" | `N` unless stated |
| FILE_HEADER_FLAG, FILE_FOOTER_FLAG ✔ | "either if your file is having a [header / footer record]" | STTM segments (Header / Trailer) |
| MANDATORY_FIELD_LIST ✔ | "basically it's a primary key … either any of the file is having primary key or not" | STTM not-null / key columns |
| TGT_CONNECTION_ID ✔ | the target (Delta) connection | connection variable |
| TGT_DATABASE_NAME, TGT_TABLE_NAME ✔ | "the schema name of your data lake stage tables, and your stage table name" | FRD / STTM stage band |
| TGT_CONTAINER_NAME, TGT_ADLS_PATH ✔ | "it's a Delta Lake table, so we have to give the path … where the files is going to be sitting under the target table path" | platform / template shape |
| TGT_COLUMN_NAMES, TGT_DATA_TYPE ✔ | "source and target column mapping … in first position in source column list, if it is ABCD … you have to map it to the XYZ … place it in same position" | STTM |
| TGT_LOAD_OPTION ✔ | "is it delta or is it upsert or is it upsert delete or is it full load?" | FRD Load Strategy |
| TGT_RJT_TABLE_NAME, TGT_RJT_ADLS_PATH ✔ | "based on the DQ rules, the process will reject your incoming records. Those records will be sitting in our reject table and reject path" | stage table + suffix |
| TGT_PARTITION_COLUMN, TGT_PARTITION_VALUE ✔ | "if you want to do any kind of partition, column partition or value partition" (example: LOB, value 01) | `NA` when none |
| TGT_PRIMARY_KEY ✔ | "target table primary keys we have to populate here" | STTM natural key |
| RECYCL_ENBL_FLG, RECYCL_TBL_NM, RECYCL_RETN_DAYS (+ RECYCL_ADLS_PATH) ✔ | "there is one more table called recycle … they will send that particular transaction record … into the recycle table and they will do the recycle for next 30 days" | FRD recycle rule |
| MAPPING_EXPRESSION ✔ | "in some of the input files we'll get … special characters … To handle those special characters we'll use this mapping expression … replaced" | FRD business rule (verbatim) |
| CREATED_BY … UPDATED_DATE ✔ | §1 | §1 |

## 8. Not yet described

The walkthrough stopped after §7 ("I think we have covered … 6 tables, and
rest of tables will cover in another call"). These IIG tabs are therefore
**not yet described** — the emitter writes their rows from the IIG cells
with the §1 conventions only, and marks each such INSERT block
`-- table not yet described in the framework walkthrough`:

- `STGDELTA_STDDELTA_INGESTION_DET` (stage → standard) — key assumed
  (GROUP_ID, OBJECT_ID, PIPELINE_ID) by analogy with §5/§7; unconfirmed.
- `DATA_QUALITY_RULES` — referenced in §7 ("based on the DQ rules") but its
  columns were not walked through.
- `DATABRICKS_NOTEBOOK_DETAILS`
- `EMAIL_TEMPLATE_CONFIG`
- `ALL_FILES_STATIC_INFORMATION` (iig_v1) / `ADLS_FIXED_WIDTH_HANDLER`
  (iig_v2)
- `FILE_LOG_INFORMATION` (RFC_PACKAGE_SHAPES §1) and the stored procedures.

## 9. Dependency order for a deployment script

From the walkthrough's own narrative ("once this connection has been set
up, afterwards we have a file ingestion"; the pipeline row must exist
"then only the process will start"): connections (§3) → pipeline schedule
(§2) → file → ADLS ingestion (§5) → ADLS → Delta ingestion (§7) → stage →
standard (§8, not yet described) → DQ rules → notebook details → email
templates.

## 10. Open questions — walkthrough vs. the goldens

Recorded, not resolved; the pair-1 golden's value is kept in the IIG review
workbooks so the byte-identity acceptance holds, and the DML follows the
walkthrough where the brief says so (ACTIVE_FLAG).

| Cell | Walkthrough | Golden (pair-1 IIG) / reference | Kept |
| --- | --- | --- | --- |
| ACTIVE_FLAG | active rows are `S`; anything else is inactive | `Y` in every sheet of the pair-1 golden and the SFMC reference | IIG: `Y` (golden); DML: `dml.active_flag` = `S` with a comment citing both |
| DAY_OF_SCHEDULE | not populated today | `0` on every pair-1 schedule row | IIG: `0` (golden); DML: NULL, comment |
| CREATED_BY / UPDATED_BY | the RFC number | `RFC######` (masked) | `@RFC_NUMBER` from the FAQ `rfc_number`; unanswered → `NULL -- ASSIGN` |
| CLAIM_TYPE_ID | "null only or even NA" | blank | NULL |
| PARENT_PIPELINE_ID | `0` for a master pipeline | a pipeline id on every golden row (the golden rows are children of an existing master) | `@PARENT_PIPELINE_ID` — engineer supplies; `NULL -- ASSIGN` |
| DATA_FACTORY_PIPELINE_SCHEDULE.DAY_OF_SCHEDULE for weekly feeds (iig_v1) | not populated today | the SFMC-reference-shaped sheet prints the FRD's weekday | IIG unchanged (baseline); DML NULL |
| Connection table / column identifiers | spoken only | not in any golden | `dml.connection_table` config, flagged `dml_unconfirmed` |

### Findings the strict derivation gate raised on the repo's own baselines (recorded, not fixed)

The gate (`gate/derivations.py`) is ON under the `acfc_prx` profile and OFF
under the reference `edo_sfmc` profile because the CV / SFMC baselines are
byte-compared and carry these findings:

| Where | Finding | Status |
| --- | --- | --- |
| CV STTM standard band | `sibling_type_mismatch`: e.g. 2 of 42 `_pct` columns typed String among Decimal, 7 of 17 `_index`, 3 of 7 `_score`, `_10k`, `_income` (cv_community_risk / cv_community_demographic_risk) | transcribed as stated; confirm with the STTM author |
| iig_v1 `ADLS_DELTA_INGESTION_DETAILS.TGT_ADLS_PATH` (synthetic shape) | built from the FRD domain words, so it carries spaces (`/Social Determinants of Health/Public/Processed/…`) — the path rule FAILs it | the synthetic path shape is a stand-in ("real container/path assigned at deployment"); replace the shape or abbreviate the domain before turning the strict gate on for `edo_sfmc` |
| MIDS FRD `ADLS Location` nested table, row "Individual Risk" | the path ends in a period (`…socially_determined.`) — a segment ending in punctuation FAILs the path rule under `acfc_prx` | an FRD typo; fix the document or accept the FAIL as the signal it is |
| MIDS FRD `Target Schema` | names no catalog anywhere (FRD, STTM bands, config default) | `catalog_unstated:stage` / `standard` FAIL under `acfc_prx` until a catalog is stated (`conventions.profiles.acfc_prx.default_catalog` in an overlay, or the FRD) |

## 11. Questions for the framework team

Yes / no questions, ready to send as-is. Each names the section it settles.

**Connection table (§3) — identifiers were spoken, never printed**

1. Is the file connection table named `FILE_CONNECTION_DETAILS`? If not, what is its exact name?
2. Is its identity column named `CONNECTION_ID`?
3. Are the description, host, root-path and source-type columns named `CONNECTION_DESCRIPTION`, `HOST_NAME`, `ROOT_PATH` and `SOURCE_TYPE`? If not, what are they?
4. Is a connection uniquely identified by host name + root path (so a lookup returning more than one row is an error)?
5. Does the connection row carry the port number and the Key Vault secret key as columns of their own, and are they mandatory on insert?
6. Are the four audit columns (`CREATED_BY`, `CREATED_DATE`, `UPDATED_BY`, `UPDATED_DATE`) present on the connection table too?

**Tables not yet described (§8)**

7. `STGDELTA_STDDELTA_INGESTION_DET`: is the key (`GROUP_ID`, `OBJECT_ID`, `PIPELINE_ID`), as for the ADLS → Delta table?
8. `DATA_QUALITY_RULES`: is `SEQUENCE_NO` assigned by the engineer, and is (`GROUP_ID`, `OBJECT_ID`, `SEQUENCE_NO`) the key?
9. `DATABRICKS_NOTEBOOK_DETAILS`: are `DATABRICKS_WORKSPACE_URL`, `DATABRICKS_WORKSPACE_SECRET`, `DATABRICKS_CLUSTERID` and `CLUSTER_DETAILS_ID` assigned by the platform team (never by the engineer)?
10. `EMAIL_TEMPLATE_CONFIG`: is `TEMPLATE_ID` an identity column?
11. `ALL_FILES_STATIC_INFORMATION` (SFMC reference layout) and `ADLS_FIXED_WIDTH_HANDLER` (PRX layout): are both live tables in the current framework, or has one replaced the other?
12. `FILE_LOG_INFORMATION`: is it written by the framework only (never by a deployment script)?
13. Are the stored procedures part of a deployment, or framework-internal only?

**Contradictions with the IIG goldens (§10)**

14. `ACTIVE_FLAG`: is the active value `S` (the framework selects `WHERE ACTIVE_FLAG = 'S'`), given every row of the reference IIG workbooks reads `Y`?
15. `DAY_OF_SCHEDULE`: should a new row leave it NULL today (the reference rows carry `0`)?
16. `PARENT_PIPELINE_ID`: is `0` the correct value for a new master pipeline, and must a child row carry its master's `PIPELINE_ID`?
17. `CLAIM_TYPE_ID`: should a file-ingestion row carry NULL (or the literal `NA`)?

**Also (§1, §2)**

18. Is the `CREATED_BY` / `UPDATED_BY` value the bare ticket number (`RFC######`, the digits only after `RFC`) or does it carry a prefix?
19. Is `IsFileCopyReqFlag` `Y` for every file ingestion the framework copies from the O drive, and `N` only for non-file processes?
