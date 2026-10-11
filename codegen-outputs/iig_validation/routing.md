# Task 4 — Routing Notes: SFMC Email Campaign IIG (SFMC_IIG.xlsx Reference)

This routing analysis traces each column value in the SFMC_IIG.xlsx reference workbook 
to its origin: where the value comes from in the FRD, STTM, DDL, or is an assigned/constant value.

Pair context: FRD_STG_STD_SFMC_1005310 / SFMC Email Campaign Tracking
(SFMC_IIG.xlsx is the CodeGen-generated golden for this FRD)

---

## Table 1: DATA_FACTORY_PIPELINE_SCHEDULE (4 rows, 28 columns)

| Column | Origin | Source Field | Notes |
|---|---|---|---|
| PIPELINE_ID | assigned ID | — | System-assigned; SYN-PIPE-001 through SYN-PIPE-004 in reference |
| PIPELINE_NAME | constant / naming standard | EDO naming convention | Pattern: PL_File_<Source>_<Flow>_<Freq> or PL_GMSTR/MSTR_<Domain>_<Freq> |
| PARENT_PIPELINE_ID | assigned ID | — | FK to another PIPELINE_ID row; Grand-master→Master→Child hierarchy |
| PIPELINE_DESCRIPTION | FRD field | FRD.Pipeline_Description / free text | Derived from FRD structural metadata "Object Description" |
| PIPELINE_FREQUENCY | FRD field | FRD.Frequency | Maps from FRD "Daily/Weekly/Monthly" |
| NO_OF_CYCLE_PER_DAY | constant | — | Default "1" for daily |
| DAY_OF_SCHEDULE | constant | — | Default "0" |
| ACTIVE_FLAG | constant | — | Always "Y" for new IIG |
| ACTIVE_START_DATE | constant | — | Date of IIG deployment |
| ACTIVE_END_DATE | constant | — | Default "9999-12-31" |
| ESTIMATED_START_TIME | unknown | — | Not populated in SFMC reference |
| APPLICATION_NAME | FRD field | FRD.Application_Name | "SFMC Email Campaign" from FRD |
| CREATED_BY | assigned ID | — | RFC user identifier |
| CREATED_DATE | constant | — | Deployment timestamp |
| UPDATED_BY | assigned ID | — | Same as CREATED_BY |
| UPDATED_DATE | constant | — | Same as CREATED_DATE |
| PROCESS_NAME | FRD field | FRD.Process_Name | "EMCIPS SFMC" — from FRD structural metadata |
| SUBPROCESS_NAME | FRD field | FRD.Subprocess_Name | "SFMC" |
| LAYER_NAME | STTM cell | STTM mapping band layer | "STAGE" or "STANDARD" per pipeline |
| COMPLETION_SLA | unknown | — | Not populated |
| RUNTIME_SLA | unknown | — | Not populated |
| CRITICAL_PROCESSING_PERIOD | unknown | — | Not populated |
| UDF1–UDF5 | unknown | — | Not populated |
| IsFileCopyReqFlag | constant | — | "N" default for non-copy pipelines |

**Unknown count: 7** (ESTIMATED_START_TIME, COMPLETION_SLA, RUNTIME_SLA, CRITICAL_PROCESSING_PERIOD, UDF1–UDF5)

---

## Table 2: ADLS_DELTA_INGESTION_DETAILS (1 row, 55 columns)

| Column | Origin | Source Field | Notes |
|---|---|---|---|
| GROUP_ID | assigned ID | — | SYN-GRP-001; system-assigned per ingestion group |
| OBJECT_ID | assigned ID | — | SYN-OBJ-001; unique per source object |
| OBJECT_NAME | FRD field | FRD.Source_Object_Name | "SFMC_CampaignInteractions" |
| DOMAIN | FRD field | FRD.Domain | "Member" |
| SUBDOMAIN | FRD field | FRD.Subdomain | "Outreach" |
| PIPELINE_ID | assigned ID | — | FK to DATA_FACTORY_PIPELINE_SCHEDULE |
| SOURCE | FRD field | FRD.Source_System | "Salesforce Marketing Cloud" |
| FREQUENCY | FRD field | FRD.Frequency | "Daily" |
| LOB | FRD field | FRD.LOB | Not populated in SFMC |
| CLAIM_TYPE_ID | FRD field | FRD.Claim_Type | Not populated (N/A for non-claims) |
| ACTIVE_FLAG | constant | — | "Y" |
| SRC_ADLS_CONNECTION_ID | assigned ID | — | SYN-CONN-001; references ADLS_CONNECTION_DETAILS |
| METADATA_CONNECTION_ID | assigned ID | — | SYN-CONN-002; references audit DB connection |
| SRC_CONTAINER_NAME | FRD field | FRD.ADLS_Container | Container name from FRD structural metadata |
| SRC_ADLS_PATH | FRD field | FRD.Inbound_File_Folder_Path | "/inbound/member/outreach/salesforce_marketing_cloud/" |
| SRC_FILE_NAME | FRD field / VDD | VDD.FILES.File_Name_Pattern | "SFMC_CampaignInteractions*" |
| SRC_FORMAT | FRD field / VDD | VDD.FILES.Format | "csv" |
| SRC_COLUMNS | STTM cell | STTM.Stage_Mapping (source:target pairs) | Column mapping from STTM stage band |
| SRC_DATA_TYPE | STTM cell | STTM.Stage_Mapping (types) | Data type mapping from STTM stage band |
| SRC_FILE_DELIMITER | FRD field / VDD | VDD.FILES.Delimiter | "," |
| SRC_REC_LNGTH | VDD field | VDD.FILES.Record_Length | Not populated (CSV has no fixed length) |
| SRC_COL_LNGTH | VDD field | VDD.FIELDS.Length | Not populated for CSV |
| SRC_COL_STRT_END_INDX | VDD field | VDD.FIELDS.Start_End_Index | Not populated for CSV |
| SRC_ADLS_ARCHVL_PATH | FRD field | FRD.Archive_Path | Derived from SRC_ADLS_PATH + "/Archive/" |
| SRC_COMPRESSION | FRD field | FRD.Compression | "N" |
| HEADER_FLAG | VDD field | VDD.FILES.Has_Header | "Y" |
| MULTILINE_FLAG | constant | — | "N" default |
| SCHEMA_DRIFT_FLAG | constant | — | "N" default |
| FILE_HEADER_FLAG | VDD field | VDD.FILES.Has_Header | "Y" |
| FILE_FOOTER_FLAG | VDD field | VDD.FILES.Has_Footer | "N" |
| MANDATORY_FIELD_LIST | STTM cell | STTM.Mandatory_Columns | Comma-separated list from STTM |
| TGT_CONNECTION_ID | assigned ID | — | SYN-CONN-003 |
| TGT_DATABASE_NAME | STTM cell | STTM.Stage_Schema | "stg_mbr" from STTM stage band |
| TGT_TABLE_NAME | STTM cell | STTM.Stage_Table_Name | "sfmc_member_outreach_email_tracking" |
| TGT_CONTAINER_NAME | FRD field | FRD.Target_Container | Target ADLS container |
| TGT_ADLS_PATH | standard DDL | Naming convention | /Domain/Subdomain/Source/Processed/<table_name> |
| TGT_COLUMN_NAMES | STTM cell | STTM.Stage_Columns | All target columns from STTM + audit columns |
| TGT_FORMAT | constant | — | "delta" (always) |
| TGT_DATA_TYPE | STTM cell | STTM.Stage_Data_Types | Target data types from STTM |
| TGT_LOAD_OPTION | FRD field | FRD.Load_Strategy_STG | "Overwrite" (from FRD "Truncate and Load") |
| TGT_RJT_TABLE_NAME | standard DDL | Naming convention | <table_name>_reject |
| TGT_RJT_ADLS_PATH | standard DDL | Naming convention | .../Reject/<table_name> |
| TGT_PARTITION_COLUMN | FRD field | FRD.Partition_Column | "NA" (not partitioned) |
| TGT_PARTITION_VALUE | FRD field | FRD.Partition_Value | "NA" |
| TGT_PRIMARY_KEY | STTM cell | STTM.Primary_Key_Columns | Composite key from STTM |
| RECYCL_ENBL_FLG | FRD field | FRD.Recycle_Enabled | "Y" (Patient Medicaid recycle from FRD) |
| RECYCL_TBL_NM | standard DDL | Naming convention | <table_name>_recycle |
| RECYCL_ADLS_PATH | standard DDL | Naming convention | .../Recycle/<table_name> |
| RECYCL_RETN_DAYS | constant | — | "7" default |
| MAPPING_EXPRESSION | unknown | — | Not populated |
| CREATED_BY | assigned ID | — | RFC user identifier |
| CREATED_DATE | constant | — | Deployment timestamp |
| UPDATED_BY | assigned ID | — | Same as CREATED_BY |
| UPDATED_DATE | constant | — | Same as CREATED_DATE |
| FILE_METADATA | unknown | — | Not populated |

**Unknown count: 2** (MAPPING_EXPRESSION, FILE_METADATA)

---

## Table 3: STGDELTA_STDDELTA_INGESTION_DET (1 row, 40 columns)

| Column | Origin | Source Field | Notes |
|---|---|---|---|
| GROUP_ID | assigned ID | — | SYN-GRP-002 (different from STG group) |
| OBJECT_ID | assigned ID | — | SYN-OBJ-001 (same object, different flow) |
| OBJECT_NAME | FRD field | FRD.Source_Object_Name | Same as ADLS table |
| DOMAIN | FRD field | FRD.Domain | "Member" |
| SUBDOMAIN | FRD field | FRD.Subdomain | "Outreach" |
| PIPELINE_ID | assigned ID | — | FK to pipeline schedule (STD pipeline) |
| SOURCE | FRD field | FRD.Source_System | "Salesforce Marketing Cloud" |
| FREQUENCY | FRD field | FRD.Frequency | "Daily" |
| LOB | FRD field | FRD.LOB | Not populated |
| ACTIVE_FLAG | constant | — | "Y" |
| SRC_ADLS_CONNECTION_ID | assigned ID | — | Points to STG output |
| METADATA_CONNECTION_ID | assigned ID | — | SYN-CONN-002 |
| SRC_CONTAINER_NAME | stage DDL | ADLS table TGT_CONTAINER | STG target becomes STD source |
| SRC_ADLS_PATH | stage DDL | ADLS table TGT_ADLS_PATH | STG ADLS path |
| SRC_TABLE_NAME | stage DDL | ADLS table TGT_TABLE_NAME | "sfmc_member_outreach_email_tracking" |
| SRC_CATALOG_NAME | stage DDL | — | "pr_dlk" (stage catalog) |
| SRC_SCHEMA_NAME | stage DDL | ADLS table TGT_DATABASE_NAME | "stg_mbr" |
| SRC_FORMAT | constant | — | "delta" (STG output is always delta) |
| SRC_COLUMNS | STTM cell | STTM.Standard_Mapping | Column mapping from STTM standard band |
| SRC_DATA_TYPE | STTM cell | STTM.Standard_Data_Types | Type mapping from STTM standard band |
| SRC_ADLS_ARCHVL_PATH | standard DDL | Naming convention | .../Archive/ |
| TGT_CONNECTION_ID | assigned ID | — | SYN-CONN-003 |
| TGT_CATALOG_NAME | STTM cell | STTM.Standard_Catalog | "pr_std" |
| TGT_SCHEMA_NAME | STTM cell | STTM.Standard_Schema | "mbr" |
| TGT_TABLE_NAME | STTM cell | STTM.Standard_Table_Name | "sfmc_member_outreach_email_tracking" |
| TGT_CONTAINER_NAME | FRD field | FRD.Target_Container | Standard container |
| TGT_ADLS_PATH | standard DDL | Naming convention | /Domain/Subdomain/Source/Processed/ |
| TGT_COLUMN_NAMES | STTM cell | STTM.Standard_Columns | All columns from STTM standard band |
| TGT_FORMAT | constant | — | "delta" |
| TGT_DATA_TYPE | STTM cell | STTM.Standard_Data_Types | Target types |
| TGT_LOAD_OPTION | FRD field | FRD.Load_Strategy_STD | "Upsert" (from FRD) |
| TGT_RJT_TABLE_NAME | standard DDL | Naming convention | <table_name>_reject |
| TGT_RJT_ADLS_PATH | standard DDL | Naming convention | .../Reject/ |
| TGT_PARTITION_COLUMN | FRD field | FRD.Partition_Column | "NA" |
| TGT_PARTITION_VALUE | FRD field | FRD.Partition_Value | "NA" |
| TGT_PRIMARY_KEY | STTM cell | STTM.Primary_Key_Columns | Same composite key |
| CREATED_BY | assigned ID | — | RFC user |
| CREATED_DATE | constant | — | Deployment timestamp |
| UPDATED_BY | assigned ID | — | Same |
| UPDATED_DATE | constant | — | Same |

**Unknown count: 0**

---

## Table 4: DATA_QUALITY_RULES (6 rows, 13 columns)

| Column | Origin | Source Field | Notes |
|---|---|---|---|
| GROUP_ID | assigned ID | — | Links to ADLS (SYN-GRP-001) or STGDELTA (SYN-GRP-002) |
| OBJECT_ID | assigned ID | — | SYN-OBJ-001 |
| SEQUENCE_NO | assigned ID | — | Sequential within group |
| RULE_TYPE | FRD field / constant | FRD.DQ_Requirements | "Predefined" (STG) or "STDDelta" (STD) |
| RULE_CLASS | FRD field | FRD.DQ_Requirements | CheckRule, ReferentialCheckRule, LRTrimRule, DateConversionRule, DateFormatRule, DataTypeCastRule |
| ACTIVE_RULE_FLG | constant | — | "Y" |
| SOURCE_COLUMN | STTM cell | STTM.Mandatory_Columns / DQ columns | Column names from STTM |
| INPUT_PARAM | STTM cell / FRD field | Various | Rule-specific: date formats, reference views, target table |
| TARGET_COLUMN | STTM cell | STTM.Target_Column | Same as or mapped from SOURCE_COLUMN |
| CREATED_BY | assigned ID | — | RFC user |
| CREATED_DATE | constant | — | Deployment timestamp |
| UPDATED_BY | assigned ID | — | Same |
| UPDATED_DATE | constant | — | Same |

**Unknown count: 0**

---

## Table 5: DATABRICKS_NOTEBOOK_DETAILS (2 rows, 19 columns)

| Column | Origin | Source Field | Notes |
|---|---|---|---|
| PIPELINE_ID | assigned ID | — | FK to pipeline schedule |
| PIPELINE_NAME | constant / naming standard | — | Same as pipeline schedule |
| GROUP_ID | assigned ID | — | Links to ADLS or STGDELTA group |
| SEQ_NM | constant | — | "1" (single notebook per group) |
| PROCESS_NAME | FRD field | FRD.Process_Description | "Stage Load for SFMC" / "Standard Load for SFMC" |
| TGT_REFRESH_TYPE | FRD field | FRD.Load_Strategy | "Overwrite" (STG) / "Append" (STD uses Upsert→mapped to Append?) |
| ACTIVE_FLAG | constant | — | "Y" |
| DATABRICKS_WORKSPACE_URL | constant | — | Workspace URL (environment-specific) |
| DATABRICKS_WORKSPACE_SECRET | assigned ID | — | Key Vault secret name |
| DATABRICKS_CLUSTERID | assigned ID | — | Cluster ID |
| DATABRICKS_NOTEBOOK_PATH | constant | — | Standard IIG notebook path |
| DATABRICKS_NOTEBOOK_NAME | constant | — | FileInvokeDQDeltaTable_V0.1 (STG) or DeltaInvokeDQStandardDeltaTable_V2 (STD) |
| CREATED_BY | assigned ID | — | RFC user |
| CREATED_DATE | constant | — | Deployment timestamp |
| UPDATED_BY | assigned ID | — | Same |
| UPDATED_DATE | constant | — | Same |
| CLUSTER_DETAILS_ID | assigned ID | — | SYN-CONN-004 |
| DQ_NOTEBOOK_PATH | unknown | — | Not populated |
| DELETE_DATABRICKS_NOTEBOOK_NAME | unknown | — | Not populated |

**Unknown count: 2** (DQ_NOTEBOOK_PATH, DELETE_DATABRICKS_NOTEBOOK_NAME)

---

## Table 6: EMAIL_TEMPLATE_CONFIG (2 rows, 15 columns)

| Column | Origin | Source Field | Notes |
|---|---|---|---|
| TEMPLATE_NAME | FRD field | FRD.Process_Name | "EMCIPS SFMC" |
| PROCESS_NAME | FRD field | FRD.Process_Name | Same |
| STATUS | constant | — | "Success" or "Failed" (one row each) |
| ACTIVE_FLAG | constant | — | "Y" |
| SUBJECT | FRD field + constant | — | Template: "<Process> Load Completed/Failed" |
| BODY | FRD field + constant | — | Template: "<Process> Files Load Process Completed/Failed" |
| SENDER_NAME | constant | — | "dbo" |
| SENDER_EMAIL | assigned ID | — | Sender email address |
| EMAIL_TO | assigned ID | — | Recipient email address |
| EMAIL_CC | assigned ID | — | CC email addresses |
| CRETAED_BY | assigned ID | — | RFC user (note: typo in column name) |
| CREATED_AT | constant | — | Deployment timestamp |
| UPDATED_BY | assigned ID | — | Same |
| UPDATED_AT | constant | — | Same |
| EMAIL_NOTIFICATION_URL | assigned ID | — | Webhook URL |

**Unknown count: 0**

---

## Table 7: ALL_FILES_STATIC_INFORMATION (16 rows, 27 columns)

| Column | Origin | Source Field | Notes |
|---|---|---|---|
| INVENTORY_ID | assigned ID | — | Sequential per file |
| OBJECT_ID | assigned ID | — | Links to ADLS/STGDELTA OBJECT_ID |
| FILE_NAME | FRD field / VDD | VDD.FILES.File_Name_Pattern | Source file name pattern |
| DESCRIPTION | FRD field | FRD.File_Description | Free text |
| LOB | FRD field | FRD.LOB | Line of business |
| GOVT_PROGRAM_NM | FRD field | FRD.Government_Program | Program name |
| FILE_TYPE | FRD field / VDD | VDD.FILES.Format | "csv", "txt", etc. |
| SUPPLIER | FRD field | FRD.Source_System | Data supplier |
| SUPPLIER_CONTACT_PH | FRD field | FRD.Supplier_Contact | Contact phone |
| SUPPLIER_EMAIL | FRD field | FRD.Supplier_Email | Contact email |
| GENERATOR | FRD field | FRD.Generator | Data generator system |
| GENERATOR_CONTACT_PH | FRD field | FRD.Generator_Contact | Generator contact |
| GENERATOR_EMAIL | FRD field | FRD.Generator_Email | Generator email |
| FREQUENCY | FRD field | FRD.Frequency | "Daily" |
| ACTIVE_TERM_STATUS | constant | — | Active/Terminated |
| INTERNAL_CONTACT_NM | FRD field | FRD.Internal_Contact | Internal point of contact |
| INTERNAL_CONTACT_EMAIL | FRD field | FRD.Internal_Email | Internal email |
| LAST_SUCCESS_PROCESSED_DATE | unknown | — | Runtime value, not in IIG |
| NEXT_EXPECTED_RECEIVE_DT | unknown | — | Runtime value |
| FILE_RECEIVE_PER_FREQUENCY | FRD field | FRD.Files_Per_Frequency | How many files per cycle |
| PROCESS_NAME | FRD field | FRD.Process_Name | "EMCIPS SFMC" |
| FILE_TR_MODE | FRD field | FRD.Transfer_Mode | SFTP, API, etc. |
| domain | FRD field | FRD.Domain | "Member" |
| subdomain | FRD field | FRD.Subdomain | "Outreach" |
| vendor_name | FRD field | FRD.Vendor_Name | Vendor |
| CREATED_DATE | constant | — | Deployment timestamp |
| UPDATED_DATE | constant | — | Same |

**Unknown count: 2** (LAST_SUCCESS_PROCESSED_DATE, NEXT_EXPECTED_RECEIVE_DT — runtime values, not IIG-authored)

---

## Summary: Unknown Counts per Table

| Table | Total Columns | Unknown | % Known |
|---|---|---|---|
| DATA_FACTORY_PIPELINE_SCHEDULE | 28 | 7 | 75% |
| ADLS_DELTA_INGESTION_DETAILS | 55 | 2 | 96% |
| STGDELTA_STDDELTA_INGESTION_DET | 40 | 0 | 100% |
| DATA_QUALITY_RULES | 13 | 0 | 100% |
| DATABRICKS_NOTEBOOK_DETAILS | 19 | 2 | 89% |
| EMAIL_TEMPLATE_CONFIG | 15 | 0 | 100% |
| ALL_FILES_STATIC_INFORMATION | 27 | 2 | 93% |
| **TOTAL** | **197** | **13** | **93%** |

The 7 "unknowns" in DATA_FACTORY_PIPELINE_SCHEDULE are UDF/SLA fields that are consistently 
empty across all real IIG workbooks examined. The 4 remaining unknowns are runtime-populated 
or unused optional fields.
