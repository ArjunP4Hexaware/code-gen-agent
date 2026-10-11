# Task 2 — Pair → GROUP_ID Index Analysis

## Blocker: pr_dlk_adb.dbo Unreachable

The IIG control tables (ADLS_DELTA_INGESTION_DETAILS, STGDELTA_STDDELTA_INGESTION_DETAILS, etc.) reside exclusively in `pr_dlk_adb.dbo` (Azure SQL Server audit/control DB). This database is:
- NOT a Unity Catalog native catalog
- Accessible via federated catalog `d1_edmcore_sqlserver` but user lacks USE CATALOG permission
- JDBC connection fails from serverless compute networking

Without access to these tables, GROUP_ID lookup by ADLS path, filename pattern, or target table name is blocked.

## Matching Attempts

Four routes were attempted for each pair:
1. **rfc**: Match against IIG workbooks in rfc_samples/
2. **path**: Match FRD ADLS inbound paths against file_adls_ingestion_details (only 1 unrelated row in UC)
3. **filename**: Match file patterns against all_files_static_information (2,450 rows, partial matches)
4. **table**: Match STTM standard table names against adls_delta_ingestion_details (NOT IN UC)

### Pair 1: OptumRx Accumulators (Project Eagle 1005789)

- **STTM target tables**: orx_accum_optumrx_dly
- **STTM schemas**: stg_pharmcy / pr_std
- **RFC IIG match**: RFC_110921_PRX has Accumulators IIG but targets prx_accum_acfc (ACFC accumulators), not orx_accum_optumrx_dly (OptumRx daily). Different data flow.
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: RFC_110921 is ACFC accumulators, not OptumRx accumulators. No IIG workbook found for orx_accum_optumrx_dly. pr_dlk_adb.dbo unreachable.

### Pair 2: Medicare Expansion-MIDS Socially Determined

- **STTM target tables**: sd_economic_principal_driver, sd_food_*, sd_housing_*, sd_ind_*, sd_household_*, sd_opportunity_index (16 tables)
- **STTM schemas**: (not extracted from STTM)
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: No RFC IIG workbook matches Socially Determined MIDS. No matching file patterns in all_files_static_information. pr_dlk_adb.dbo unreachable.

### Pair 3: OptumRx Facets Member Eligibility (1005789)

- **STTM target tables**: orx_mbr_elig (inferred from stg_pharmcy schema)
- **STTM schemas**: stg_pharmcy / pr_std
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: orx_mbr_elig exists in d1_dlk.stg_pharmcy but no IIG workbook found. pr_dlk_adb.dbo unreachable.

### Pair 4: OptumRx PDE Edit Code Report (1005789)

- **STTM target tables**: orx_pde_edit_cd
- **STTM schemas**: stg_pharmcy / pr_std
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: orx_pde_edit_cd exists in d1_dlk.stg_pharmcy but no IIG workbook found. pr_dlk_adb.dbo unreachable.

### Pair 5: Wellpoint Medicaid Medical Claims Historical (1006111)

- **STTM target tables**: claim_medical_state_hist
- **STTM schemas**: stg_clm / clm
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: claim_medical_state_hist exists in d1_dlk.stg_clm but no IIG workbook found. pr_dlk_adb.dbo unreachable.

### Pair 6: OptumRx CAG Crosswalk (1005789)

- **STTM target tables**: EXT_OPTM_PLAN_CAG_XWLK, EXT_REG_*, EXT_XCH_*, EXT_MDC_*
- **STTM schemas**: stg_util_reg1
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: RDBMS ingestion (Facets tables). No IIG workbook found. pr_dlk_adb.dbo unreachable.

### Pair 7: UHC Medicaid RxClaims Historical (1005567)

- **STTM target tables**: claim_pharmacy_state_hist, NCPDP_MAGELLAN_STAG_DTL/STG_CMP
- **STTM schemas**: stg_pharmcy / pharmcy
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: claim_pharmacy_state_hist exists in d1_dlk.stg_pharmcy but no IIG workbook found. pr_dlk_adb.dbo unreachable.

### Pair 8: PA CHC Reprocurement 834 Unified Layout (1004429)

- **STTM target tables**: (unified layout - table names not extracted)
- **STTM schemas**: stg_edi834prop
- **RFC IIG match**: RFC111251_EDI834PROP_Unified_DT exists but contains scripts, not IIG workbook
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: RFC111251 has related scripts but no IIG workbook with GROUP_IDs. pr_dlk_adb.dbo unreachable.

### Pair 9: HR Analytics HCM PeopleSoft (1004845)

- **STTM target tables**: (HCM tables in stg_hcm)
- **STTM schemas**: stg_hcm / pr_std_hrr
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: UMPeopleSoftData found in all_files_static_information (OBJ_ID=2) but no GROUP_ID route. pr_dlk_adb.dbo unreachable.

### Pair 10: BestFootForward HRA Data (1004808)

- **STTM target tables**: (BFF tables in stg_care_mgmt)
- **STTM schemas**: stg_care_mgmt
- **RFC IIG match**: None
- **GROUP_ID**: NOT FOUND
- **Confidence**: low
- **Note**: db_104_hra_data_enterprise found in all_files_static_information (OBJ_ID=1) but no GROUP_ID route. pr_dlk_adb.dbo unreachable.

## RFC IIG Workbooks in rfc_samples/ (for reference)

| RFC | IIG File | GROUP_IDs | Target Tables |
|---|---|---|---|
| RFC_110921_PRX | RFC_110921_Accumulators.xlsx | 21100001, 21100002, 21100206 | prx_accum_acfc |
| RFC_111895_PRX | IIG_ENTRIES.xlsx | 22089903–22089909 | provider_medicaid_* (7 states) |
| RFC111412 | PAYMENT_INTEGRITY_CAQH_IIG.xlsx | 180276, 180281 | EXT_TPL_CAQH_DTL/HDR/TRL |
| RFC111807 | RFC111807_IIG.xlsx | 2109459812 | EDH claims dim tables (Gold) |
| RFC112190 | RFC112190_IIG.xlsx | 2109459812 | EDH claims dim tables (Gold) |
| RFC112916 | RFC112916_IIG_PROD.xlsx | 2109560208 | EDH pharmacy dimensions (Gold) |

None of these correspond to any of the 10 FRD/STTM pairs.
