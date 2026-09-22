# RUN v0.6.2-acfc — All Pairs

**Date**: 2026-09-22 05:58 UTC
**Version**: v0.6.2-acfc (staging commit 435e4a5, acfc-local merge 52c3da7)
**Deployment**: codegen-agent app, deployment 01f1b643c1a41c2ead43bd50a1eca9ac
**Profile**: acfc_prx | **IIG template**: iig_v2 | **Output**: framework
**Layout provider**: live (databricks-claude-opus-5)

---

## Summary

| Pair | Select | Run | Verdict | Error |
| --- | --- | --- | --- | --- |
| 1 | 4.0s | 102s | **PASS_WITH_FLAGS** | — |
| 2 | 4.0s | 11s | FAIL | WorkbookParseError: FILE_DETAILS row 6 |
| 3 | 124s | — | FAIL | StepTimeout: parser process killed at 120s |
| 4 | 6.0s | 20s | FAIL | ContractMismatchError: format .xlsx no delimiter |
| 5 | 4.0s | 107s | FAIL | ExtractionError: segment spelling ['NA'] |
| 6 | 4.0s | 11s | FAIL | ExtractionError: audit column tinyint |
| 7 | 4.0s | 89s | FAIL | ExtractionError: stage band missing column/target_type |
| 8 | 4.0s | 33s | FAIL | FrdDocxError: no F1/F2 table |
| 9 | 4.0s | 6s | FAIL | FrdDocxError: no F1/F2 table |
| 10 | 4.0s | 66s | FAIL | FrdDocxError: no F1/F2 table |

**1 / 10 PASS. 9 / 10 FAIL.**

---

## Pair 1 — PASS_WITH_FLAGS (detail)

### Selection (4.0s)

* **STTM**: STTM_Project Eagle_OptumRx_1005789_Accumulators File Ingestion from OptumRx.xlsx
* **FRD**: FRD_STG_STD_OptumRx-Project Eagle 1005789_Accumulators file Ingestion from OptumRx (1).docx
  * Pairing rule: **ticket** (score 4, tables +3, ticket +1: 1005789)
* **VDD**: VDD_OptumRx_Accumulators.xlsx
  * Pairing rule: **same_folder** (only VDD in pair_1/)

### Generation (102s)

* **Feed**: orx_accum_optumrx_dly
* **Verdict**: PASS_WITH_FLAGS
* **Checks**: 11 (all passed; `ruff` not_run — no ruff in runtime)

| Check | Passed | Details |
| --- | --- | --- |
| ruff | true (not_run) | ruff not installed |
| debug_patterns | true | no debug statements |
| secrets | true | no hardcoded secrets |
| test_per_module | true | every pipeline module has a test file |
| vdd_positions | true | fixed-width positions present in VDD |
| dml_parse_q1 | true | config_inserts_q1.sql: every statement parses (tsql) |
| dml_parse_a2 | true | config_inserts_a2.sql: every statement parses (tsql) |
| dml_parse_prod | true | config_inserts_prod.sql: every statement parses (tsql) |
| dml_row_counts | true | DML rows per table equal the IIG |
| sql_literals | true | every COMMENT / LOCATION / TBLPROPERTIES literal single-line |
| derivations | true | every derived name and path single-line and within cap |

### Flags (92 total, grouped)

| Flag kind | Count |
| --- | --- |
| dml_unassigned | 10 |
| frd_unstated | 9 |
| frd_multiline | 8 |
| iig_blank | 7 |
| Layer-2 candidate pending engineer approval | 7 |
| field_unmapped | 6 |
| length_is_precision | 6 |
| width_from_sttm_span | 6 |
| sibling_type_mismatch | 6 |
| faq_unanswered | 6 |
| dml_not_described | 4 |
| vdd_missing_in_sttm | 6 |
| vdd_field_count | 1 |
| frd_layer_block | 1 |
| file_pattern_from_object_name | 1 |
| frd_feed_name_unstated | 1 |
| segments_from_sttm | 1 |
| ddl_file_name_from_slug | 1 |
| dml_unconfirmed | 1 |
| load_mode_not_enforced | 1 |
| rule classified flagged | 1 |
| generated tests were skipped | 1 |
| check_not_run | 1 |

### Artefacts (14 files)

| File | Size |
| --- | --- |
| ddl/pharmcy.orx_accum_optumrx_dly.standard.sql | 2,604 |
| ddl/stg_pharmcy.orx_accum_optumrx_dly.sql | 2,587 |
| ddl/stg_pharmcy.orx_accum_optumrx_dly_errors.sql | 782 |
| ddl/stg_pharmcy.orx_accum_optumrx_dly_processed_files.sql | 750 |
| framework/ORX_ACCUM_OPTUMRX_DLY_DDL.txt | 3,203 |
| framework/config_inserts_q1.sql | 41,277 |
| framework/Insert_scripts_config_table_q1.py | 4,670 |
| framework/config_inserts_a2.sql | 41,277 |
| framework/Insert_scripts_config_table_a2.py | 4,670 |
| framework/config_inserts_prod.sql | 41,281 |
| framework/Insert_scripts_config_table_prod.py | 4,676 |
| framework/config_rows.xlsx | 25,952 |
| framework/config_inserts.xlsx | 19,479 |
| framework/ADDITION.md | 3,443 |

### DDL diff vs RFC_110921_PRX/ACCUM_DDL.txt

Table names differ as expected (generated: `pr_dlk.stg_pharmcy.orx_accum_optumrx_dly` / `pr_std.pharmcy.orx_accum_optumrx_dly`,
golden: `pr_dlk_prx.stg_prx_accum.prx_accum_acfc` / `pr_std_prx.accum.prx_accum_acfc`).

Column lists differ entirely: generated has 68 columns from the OptumRx Accumulators STTM;
golden has 21 columns from the Abarca-style accumulator layout. This is expected —
different source vendor, different field set. Structural shape (stage + standard blocks,
SRC_FILE_NAME / REC_CREATION_TIME / REC_UPDATED_TIME trailer columns, USING DELTA / LOCATION / TBLPROPERTIES)
is the same in both.

```diff
--- RFC_110921_PRX/ACCUM_DDL.txt
+++ generated/ORX_ACCUM_OPTUMRX_DLY_DDL.txt
@@ -1,29 +1,79 @@
 
 --stage table
 
-CREATE OR REPLACE TABLE pr_dlk_prx.stg_prx_accum.prx_accum_acfc
+CREATE OR REPLACE TABLE pr_dlk.stg_pharmcy.orx_accum_optumrx_dly
 (
-SEGMENT_IDENTIFIER String,
-FILE_TYPE String,
-DATA_CATEGORY String,
-PROCESS_DATE Date,
-PROCESS_TIME String,
-GROUP_ID String,
-FILLER_1 String,
-VERSION_RELEASE String,
-CARDHOLDER_ID String,
-PLAN_ID String,
-INDIVIDUAL_DEDUCTIBLE Decimal(17,2),
-FAMILY_DEDUCTIBLE Decimal(18,2),
-COPAY Decimal(19,2),
-COINSURANCE Decimal(20,2),
-INDIVIDUAL_LIMIT Decimal(21,2),
-FAMILY_LIMIT Decimal(22,2),
-PLAN_YEAR_START_DATE Date,
-PLAN_YEAR_END_DATE Date,
-FILLER_2 String,
-LINE_COUNT String,
-FILLER_3 String,
+REC_TYP_HDR String,
+FILE_CREATN_TS String,
+SNDR_NM String,
+RCVR_NM String,
+RESRV_HDR String,
+VRSN String,
+REC_TYP_DTL String,
+REC_TS String,
+REC_ORD String,
+REC_ID String,
+SNDR_TYP String,
+SNDR_ID String,
+SNDR_NOTE String,
+SNDR_CLM_NBR String,
+RSN_CD String,
+ADJMNT_DT String,
+AMT_TYP String,
+TOT_NBR_OF_ADJMNT String,
+ADJMNT_TYP_01 String,
+IN_OUT_OF_NTWK_IND_01 String,
+INDVDL_01 String,
+AMT_01 String,
+NEGATV_AMT_IND_01 String,
+ACCMLTN_CD_01 String,
+ADJMNT_TYP_02 String,
+IN_OUT_OF_NTWK_IND_02 String,
+INDVDL_02 String,
+AMT_02 String,
+NEGATV_AMT_IND_02 String,
+ACCMLTN_CD_02 String,
+ADJMNT_TYP_03 String,
+IN_OUT_OF_NTWK_IND_03 String,
+INDVDL_03 String,
+AMT_03 String,
+NEGATV_AMT_IND_03 String,
+ACCMLTN_CD_03 String,
+ADJMNT_TYP_04 String,
+IN_OUT_OF_NTWK_IND_04 String,
+INDVDL_04 String,
+AMT_04 String,
+NEGATV_AMT_IND_04 String,
+ACCMLTN_CD_04 String,
+ADJMNT_TYP_05 String,
+IN_OUT_OF_NTWK_IND_05 String,
+INDVDL_05 String,
+AMT_05 String,
+NEGATV_AMT_IND_05 String,
+ACCMLTN_CD_05 String,
+ADJMNT_TYP_06 String,
+IN_OUT_OF_NTWK_IND_06 String,
+INDVDL_06 String,
+AMT_06 String,
+NEGATV_AMT_IND_06 String,
+ACCMLTN_CD_06 String,
+CARR_ID String,
+ACCT_NBR String,
+GRP_ID String,
+MBR_ID String,
+MBR_FRST_NM String,
+MBR_MID_INIT String,
+MBR_LAS_NAME String,
+MBR_BIRTH_DT String,
+MBR_GNDR String,
+MBR_RELATN_CD String,
+SUBSCRIBER_ID String,
+RTRN_CD String,
+RESRV_DTL String,
+REC_TYP_TRLR String,
+REC_CNT String,
+RESRV_TRLR String,
+LOB STRING,
 SRC_FILE_NAME STRING,
 REC_CREATION_TIME TIMESTAMP,
 REC_UPDATED_TIME TIMESTAMP
@@ -33,29 +83,79 @@
 
 --standard table
 
-CREATE OR REPLACE TABLE pr_std_prx.accum.prx_accum_acfc
+CREATE OR REPLACE TABLE pr_std.pharmcy.orx_accum_optumrx_dly
 (
-SEGMENT_IDENTIFIER String,
-FILE_TYPE String,
-DATA_CATEGORY String,
-PROCESS_DATE Date,
-PROCESS_TIME String,
-GROUP_ID String,
-FILLER_1 String,
-VERSION_RELEASE String,
-CARDHOLDER_ID String,
-PLAN_ID String,
-INDIVIDUAL_DEDUCTIBLE Decimal(17,2),
-FAMILY_DEDUCTIBLE Decimal(18,2),
-COPAY Decimal(19,2),
-COINSURANCE Decimal(20,2),
-INDIVIDUAL_LIMIT Decimal(21,2),
-FAMILY_LIMIT Decimal(22,2),
-PLAN_YEAR_START_DATE Date,
-PLAN_YEAR_END_DATE Date,
-FILLER_2 String,
-LINE_COUNT String,
-FILLER_3 String,
+REC_TYP_HDR String,
+FILE_CREATN_TS String,
+SNDR_NM String,
+RCVR_NM String,
+RESRV_HDR String,
+VRSN String,
+REC_TYP_DTL String,
+REC_TS String,
+REC_ORD String,
+REC_ID String,
+SNDR_TYP String,
+SNDR_ID String,
+SNDR_NOTE String,
+SNDR_CLM_NBR String,
+RSN_CD String,
+ADJMNT_DT String,
+AMT_TYP String,
+TOT_NBR_OF_ADJMNT String,
+ADJMNT_TYP_01 String,
+IN_OUT_OF_NTWK_IND_01 String,
+INDVDL_01 String,
+AMT_01 String,
+NEGATV_AMT_IND_01 String,
+ACCMLTN_CD_01 String,
+ADJMNT_TYP_02 String,
+IN_OUT_OF_NTWK_IND_02 String,
+INDVDL_02 String,
+AMT_02 String,
+NEGATV_AMT_IND_02 String,
+ACCMLTN_CD_02 String,
+ADJMNT_TYP_03 String,
+IN_OUT_OF_NTWK_IND_03 String,
+INDVDL_03 String,
+AMT_03 String,
+NEGATV_AMT_IND_03 String,
+ACCMLTN_CD_03 String,
+ADJMNT_TYP_04 String,
+IN_OUT_OF_NTWK_IND_04 String,
+INDVDL_04 String,
+AMT_04 String,
+NEGATV_AMT_IND_04 String,
+ACCMLTN_CD_04 String,
+ADJMNT_TYP_05 String,
+IN_OUT_OF_NTWK_IND_05 String,
+INDVDL_05 String,
+AMT_05 String,
+NEGATV_AMT_IND_05 String,
+ACCMLTN_CD_05 String,
+ADJMNT_TYP_06 String,
+IN_OUT_OF_NTWK_IND_06 String,
+INDVDL_06 String,
+AMT_06 String,
+NEGATV_AMT_IND_06 String,
+ACCMLTN_CD_06 String,
+CARR_ID String,
+ACCT_NBR String,
+GRP_ID String,
+MBR_ID String,
+MBR_FRST_NM String,
+MBR_MID_INIT String,
+MBR_LAS_NAME String,
+MBR_BIRTH_DT String,
+MBR_GNDR String,
+MBR_RELATN_CD String,
+SUBSCRIBER_ID String,
+RTRN_CD String,
+RESRV_DTL String,
+REC_TYP_TRLR String,
+REC_CNT String,
+RESRV_TRLR String,
+LOB STRING,
 SRC_FILE_NAME STRING,
 REC_CREATION_TIME TIMESTAMP,
 REC_UPDATED_TIME TIMESTAMP
```

### IIG diff vs RFC_110921_PRX/RFC_110921_Accumulators.xlsx

| Sheet | Gen rows | Golden rows | Gen cols | Golden cols | Headers match | Differing cells |
| --- | --- | --- | --- | --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 2 | 5 | 16 | 16 | yes | 11 |
| FILE_ADLS_INGESTION_DETAILS | 2 | 2 | 17 | 17 | yes | 15 |
| ADLS_DELTA_INGESTION_DETAILS | 4 | 5 | 54 | 54 | yes | 110 |
| STGDELTA_STDDELTA_INGESTION_DET | 2 | 2 | 40 | 40 | yes | 33 |
| ADLS_FIXED_WIDTH_HANDLER | 4 | 4 | 23 | 23 | yes | 54 |
| DATABRICKS_NOTEBOOK_DETAILS | 2 | 4 | 19 | 19 | yes | 16 |
| DATA_QUALITY_RULES | 1 | 9 | 13 | 13 | yes | 0 |
| EMAIL_TEMPLATE_CONFIG | 3 | 3 | 16 | 16 | yes | 26 |
| _provenance | gen only | — | — | — | — | — |
| _inputs | gen only | — | — | — | — | — |

**Key differences**: All headers match across all 8 common sheets. Row count mismatches
on 4 sheets (PIPELINE_SCHEDULE, ADLS_DELTA, NOTEBOOK_DETAILS, DATA_QUALITY_RULES) reflect
the golden's multi-segment/multi-row entries vs the generated single-feed output.
Cell-level differences are predominantly: (a) table/schema/catalog names (expected), (b)
column lists (different vendor), (c) template-filled cells (PIPELINE_ID, CREATED_BY,
RFC number, timestamps) that the generator leaves blank (flagged iig_blank).

---

## Pairs 2–10 — Individual Results

### Pair 2 — FAIL

* **STTM**: STTM_Medicare Expansion-MIDS - Socially Determined (1).xlsx
* **FRD**: FRD_Medicare Expansion-MIDS - Socially Determined (1).docx (rule: name_stem)
* **VDD**: VDD_Socially_Determined_MIDS.xlsx
* **Select**: 4.0s | **Layout**: 1 question (proceeded unresolved)
* **Error**: `WorkbookParseError: FILE_DETAILS row 6: Vendor and FileName must both be present (got vendor='Amber italic DataType = the vendor gave neither a data type nor an example value for this column, so the ACFC default applies. Confirm before use.', file_name=None)`
* **Cause**: STTM FILE_DETAILS sheet has a descriptive note in the Vendor column but no corresponding FileName value.

### Pair 3 — FAIL

* **STTM**: STTM_Project Eagle_OptumRx_1005789_Facets Member Eligibility_v1.2.xlsx
* **FRD**: N/A (selection failed)
* **VDD**: N/A
* **Select**: 124s (timeout)
* **Error**: `StepTimeout: the document was not read within 120s — the parser process was killed`
* **Cause**: The workbook was previously classified as `unreadable`; the parser timed out at 120s.

### Pair 4 — FAIL

* **STTM**: STTM_Project_Eagle_OptumRx_1005789_PDE Edit Code Report.xlsx
* **FRD**: FRD_STG_STD_OptumRx-Project Eagle 1005789_PDE Edit Code Report File (1).docx (rule: ticket)
* **VDD**: VDD_OptumRx_PDE_Edit_Code_Report.xlsx
* **Select**: 6.0s | **Layout**: 1 question (proceeded unresolved)
* **Error**: `ContractMismatchError: contract mismatch for feed 'orx_pde_edit_cd': format '.xlsx' has no implied delimiter, neither contract states one, and no file pattern carries a csv / psv / tsv extension`
* **Cause**: The FRD/STTM pair describes .xlsx-format inbound files; the resolver requires a delimiter for non-xlsx targets.

### Pair 5 — FAIL

* **STTM**: STTM_STG_STD_ACDC_Wellpoint_Medicaid_MedicalClaims_Historical_Ingestion_1006111.xlsx
* **FRD**: FRD_WellPoint_Medical_Claims_Historical_Ingestion_1006111.docx (rule: ticket)
* **VDD**: N/A (no VDD matched)
* **Select**: 4.0s | **Layout**: 5 questions (proceeded unresolved)
* **Error**: `ExtractionError: sheet 'Wellpoint MEDClaim_ACDC_Mapping': segment spelling(s) ['NA'] are outside the Header/Detail/Trailer vocabulary`
* **Cause**: The STTM uses 'NA' as a segment label, which is not in the extractor's recognized vocabulary.

### Pair 6 — FAIL

* **STTM**: STTM_Project Eagle_OptumRx_1005789_Facets CAG Crosswalk Table.xlsx
* **FRD**: FRD_STG_STD_OptumRx-Project Eagle 1005789_Ingestion of CAG Crosswalk & Provider relationship tables from Facets (1).docx (rule: ticket)
* **VDD**: VDD_Facets_CAG_Crosswalk.xlsx
* **Select**: 4.0s | **Layout**: 2 questions (proceeded unresolved)
* **Error**: `ExtractionError: sheet 'EXT_OPTM_PLAN_CAG_XWLK' row 28: audit column 'DELETE_FLAG' has datatype 'tinyint'; expected one of ['string', 'timestamp']`
* **Cause**: The STTM declares a `tinyint` audit column, but the extractor's schema only allows string/timestamp for audit columns.

### Pair 7 — FAIL

* **STTM**: STTM_STG_STD_ACLA_UHC_Medicaid_Member_Distribution_RxClaims_Historical_Ingestion_1005567.xlsx
* **FRD**: FRD_STG_STD_ACLA_UHC_Medicaid_Member_Distribution_RxClaims_Historical_Ingestion_1005567.docx (rule: ticket)
* **VDD**: VDD_UHC_Medicaid_RxClaims.xlsx
* **Select**: 4.0s | **Layout**: 6 questions (proceeded unresolved)
* **Error**: `ExtractionError: sheet 'Mapping - UHC Rx Claims': the stage band has no values for ['column', 'target_type'] (roles unresolved or empty)`
* **Cause**: The STTM's layout could not resolve stage column names and types; the stage band was empty after layout resolution.

### Pair 8 — FAIL

* **STTM**: STTM_PA CHC Reprocurement_1004429_834_Unified Layout_FILE.xlsx
* **FRD**: FRD_STG_STD_PA CHC Reprocurement_1004429_834_Unified Layout_FILE (1).docx (rule: ticket)
* **VDD**: VDD_834_Unified_Layout.xlsx
* **Select**: 4.0s
* **Error**: `FrdDocxError: no metadata section table (F1) and no Solution Requirement table (F2) found`
* **Cause**: The FRD document does not follow the F1/F2 format the extractor expects.

### Pair 9 — FAIL

* **STTM**: STTM_HR_Analytics_HCM_To_DL_Mapping_Document_1004845_V1.0.xlsx
* **FRD**: FRD_STG_STD_HR_Analytics_HCM_Data_Ingestion_1004845_V1.1 (1).docx (rule: ticket)
* **VDD**: VDD_HCM_PeopleSoft.xlsx
* **Select**: 4.0s
* **Error**: `FrdDocxError: no metadata section table (F1) and no Solution Requirement table (F2) found`
* **Cause**: Same as pair 8 — FRD document layout not recognized.

### Pair 10 — FAIL

* **STTM**: STTM_ISFDA_1004808_E17231_BestFootForward_HRADataIngestion.xlsx
* **FRD**: FRD_STD_ISFDA_1004808_E17231_BestFootForward_HRADataIngestion (1).docx (rule: ticket)
* **VDD**: VDD_BestFootForward_HRA.xlsx
* **Select**: 4.0s
* **Error**: `FrdDocxError: no metadata section table (F1) and no Solution Requirement table (F2) found`
* **Cause**: Same as pairs 8/9 — FRD document layout not recognized.

---

## Failure Classification

| Category | Pairs | Count |
| --- | --- | --- |
| FrdDocxError: no F1/F2 table | 8, 9, 10 | 3 |
| ExtractionError: STTM schema/vocab | 5, 6, 7 | 3 |
| WorkbookParseError: FILE_DETAILS | 2 | 1 |
| ContractMismatchError: format/delimiter | 4 | 1 |
| StepTimeout: parser killed | 3 | 1 |
| **PASS_WITH_FLAGS** | **1** | **1** |
