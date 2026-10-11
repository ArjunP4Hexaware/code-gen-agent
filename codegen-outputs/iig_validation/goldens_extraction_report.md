# Task 3 — Golden Extraction Report

## Status: BLOCKED

No high or medium confidence GROUP_ID matches were found for any of the 10 pairs.
Golden extraction requires:
1. A known GROUP_ID for each pair
2. Access to pr_dlk_adb.dbo to query IIG control tables

### Root Cause
The IIG control tables (ADLS_DELTA_INGESTION_DETAILS, STGDELTA_STDDELTA_INGESTION_DETAILS, 
DATA_FACTORY_PIPELINE_SCHEDULE, DATABRICKS_NOTEBOOK_DETAILS, DATA_QUALITY_RULES) reside 
exclusively in the Azure SQL Server `pr_dlk_adb.dbo`, which is not queryable from this 
compute context due to:
- `d1_edmcore_sqlserver` federated catalog: INSUFFICIENT_PERMISSIONS (USE CATALOG denied)
- Direct JDBC: network connectivity failure from serverless compute

### What Would Be Needed
To unblock, any ONE of:
1. Grant USE CATALOG on `d1_edmcore_sqlserver` to this user/SP
2. Run from a cluster with network access to the SQL Server endpoint
3. Provide GROUP_IDs manually (e.g., from a DBA query or existing deployment playbook)
4. Replicate the 5 core IIG tables to a UC schema (e.g., d1_dlk.iig_metadata)

### Available Data (not GROUP_ID-keyed)
Target data tables DO exist in UC for most pairs:
- pair_1: d1_dlk.stg_pharmcy.orx_accum_optumrx_dly
- pair_4: d1_dlk.stg_pharmcy.orx_pde_edit_cd
- pair_5: d1_dlk.stg_clm.claim_medical_state_hist
- pair_7: d1_dlk.stg_pharmcy.claim_pharmacy_state_hist
- pair_3: d1_dlk.stg_pharmcy.orx_mbr_elig (inferred)

But without GROUP_IDs, we cannot extract the IIG metadata rows that CONFIGURE these tables.
