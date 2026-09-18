# Scrub report — pair_1 golden (RFC######_PRX → Accumulators)

Source: `rfc_samples/RFC######_PRX/`
Matched pair: `frd_sttm_pairs/pair_1/` (Accumulators file Ingestion)

## ACCUM_DDL.txt
- (no replacements)

Following SFMC DDL precedent: table names (`pr_dlk_prx.stg_prx_accum.prx_accum_acfc`,
`pr_std_prx.accum.prx_accum_acfc`), column names, data types, and `USING delta`
are schema structure and kept verbatim. No LOCATION/abfss clause present,
no emails, no person names, no RFC numbers embedded in the DDL.

## RFC_ACCUMULATORS_IIG.xlsx
- cluster_or_pool_id: 6
- connection_id: 11
- container_name: 11
- email: 4
- group_id: 17
- numeric_id: 2
- object_id: 14
- pipeline_id: 20
- rfc_number: 52
- secret_name: 3
- workspace_url: 3

Sheets preserved (8): DATA_FACTORY_PIPELINE_SCHEDULE,
FILE_ADLS_INGESTION_DETAILS, ADLS_DELTA_INGESTION_DETAILS,
STGDELTA_STDDELTA_INGESTION_DET, ADLS_FIXED_WIDTH_HANDLER,
DATABRICKS_NOTEBOOK_DETAILS, DATA_QUALITY_RULES, EMAIL_TEMPLATE_CONFIG.

Sheet order, column order, row counts, and header texts kept verbatim.
Replaced values follow the SFMC reference synthetic-token pattern
(SYN-PIPE-nnn, SYN-GRP-nnn, syn-container-nnn, etc.).

### What was kept
- All header row texts (column names)
- Pipeline names, process names, object names
- Domain / Subdomain descriptors
- Source field values (vendor/system names)
- ADLS paths (structural routing, no server names)
- Column lists in SRC_COLUMNS, TGT_COLUMN_NAMES, SRC_DATA_TYPE, TGT_DATA_TYPE
- DQ rule types, rule classes, source/target column lists
- Notebook paths and notebook names
- Frequency, LOB, file format, file extension values
- Fixed-width segment definitions (COL, LEN, start_ind)

### What was replaced
- PIPELINE_ID, PARENT_PIPELINE_ID → SYN-PIPE-nnn
- GROUP_ID → SYN-GRP-nnn
- OBJECT_ID → SYN-OBJ-nnn
- SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, SRC_CONNECTION_ID → SYN-CONN-nnn
- SRC_CONTAINER_NAME, TGT_CONTAINER_NAME → syn-container-nnn
- DATABRICKS_CLUSTERID → SYN-CLUSTER-nnn
- DATABRICKS_WORKSPACE_SECRET → SYN-SECRET-nnn
- DATABRICKS_WORKSPACE_URL → https://syn-dbx-workspace-001.synthetic.example/
- CREATED_BY, UPDATED_BY containing RFC numbers → RFC######
- SENDER_EMAIL, EMAIL_TO, EMAIL_CC → syn.person.nnn@synthetic.example
- TEMPLATE_ID → SYN-TMPL-nnn

## FILE_LOG_INFORMATION
- Not present in this RFC package.
