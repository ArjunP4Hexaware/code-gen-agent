# Round 2 IIG Validation — Routing Observed

Branch: `feature/multi-table`
Date: 2026-10-11

---

## 1. Per-Sheet, Per-Column Origin Tags and Agent Accuracy

Observed from pair_2 (the only pair with both golden and agent). The golden
is a prod export with 6 groups (180251–180256). The agent was generated from
a prior multitable/out/ session with mock Layer 2.

### ADLS_DELTA_INGESTION_DETAILS (golden: 3 rows, agent: 3 rows, paired: 0)

| Column | Origin | Agent Gets It | Example Failure |
| --- | --- | --- | --- |
| GROUP_ID | framework-assigned id | never (needs_assignment) | golden 180251, agent blank |
| OBJECT_ID | framework-assigned id | never (needs_assignment) | golden 1, agent 1 (same but different scope) |
| PIPELINE_ID | framework-assigned id | never (needs_assignment) | golden 180451, agent blank |
| OBJECT_NAME | FRD/STTM feed name | never (key mismatch) | golden vs agent use different feed identifiers |
| TGT_TABLE_NAME | STTM target band | never (key mismatch) | golden prod name vs agent generated name |
| SRC_FILE_NAME | STTM/FRD file pattern | sometimes | Depends on FRD contract extraction accuracy |
| SRC_ADLS_CONNECTION_ID | framework-assigned | never (needs_assignment) | golden 10, agent 0 |
| METADATA_CONNECTION_ID | framework-assigned | never (needs_assignment) | golden 10, agent 0 |
| TGT_CONNECTION_ID | framework-assigned | never (needs_assignment) | golden 11, agent 0 |
| SRC_CONTAINER_NAME | environment config | never | golden `<CONTAINER_RAW>`, agent blank |
| TGT_CONTAINER_NAME | environment config | never | golden `<CONTAINER_STG>`, agent blank |
| FILE_METADATA | golden-only column | never | column absent from agent |

### STGDELTA_STDDELTA_INGESTION_DET (golden: 3, agent: 3, paired: 0)

| Column | Origin | Agent Gets It | Example Failure |
| --- | --- | --- | --- |
| GROUP_ID | framework-assigned id | never | golden 180252, agent blank |
| PIPELINE_ID | framework-assigned id | never | golden 180452, agent blank |
| TGT_TABLE_NAME | STTM target band | never (key mismatch) | different naming conventions |
| TGT_SCHEMA_NAME | STTM/FRD schema | sometimes | depends on extraction |
| SRC_SCHEMA_NAME | STTM stage schema | sometimes | depends on extraction |

### DATA_FACTORY_PIPELINE_SCHEDULE (golden: 48, agent: 12, paired: 0)

| Column | Origin | Agent Gets It | Example Failure |
| --- | --- | --- | --- |
| PIPELINE_NAME | naming convention | never (key mismatch) | golden `PL_File_...` vs agent-generated names |
| PIPELINE_ID | framework-assigned | never | golden filled, agent blank |
| SCHEDULE_NAME | framework template | never | different schedule naming |
| DAY_OF_SCHEDULE | FRD frequency | sometimes | depends on frequency extraction |
| FREQUENCY | FRD frequency | sometimes | golden `DAILY`/`WEEKLY`, agent may match |

### DATABRICKS_NOTEBOOK_DETAILS (golden: 6, agent: 3, paired: 0)

| Column | Origin | Agent Gets It | Example Failure |
| --- | --- | --- | --- |
| PIPELINE_ID | framework-assigned | never | golden filled, agent blank |
| PIPELINE_NAME | naming convention | never (key mismatch) | `PL_File_STAGE_...` vs agent names |
| DATABRICKS_NOTEBOOK_NAME | naming convention | sometimes | depends on EDO naming adherence |
| DATABRICKS_WORKSPACE_URL | environment config | never | golden filled, agent blank |

### EMAIL_TEMPLATE_CONFIG (golden: 12, agent: 6, paired: 6 by scorecard)

| Column | Origin | Agent Gets It | Example Failure |
| --- | --- | --- | --- |
| TEMPLATE_NAME | naming convention | sometimes | golden `MIDS SDOH`, agent blank |
| STATUS | template constant | always | `Success` / `Failed` match |
| ACTIVE_FLAG | template constant | always | `Y` |
| SUBJECT | template text | sometimes | differs in specifics |
| BODY | template text | sometimes | differs in details |
| PIPELINE_ID | framework-assigned | never | golden filled, agent blank |
| TEMPLATE_ID | framework-assigned | never | golden filled, agent blank |

### DATA_QUALITY_RULES (golden: 11, agent: 0, paired: 0)

Agent produced 0 DQ rules. Golden has 11 rules. The agent's DQ sheet is empty
because the prior run did not generate DQ rules (mock Layer 2).

### ALL_FILES_STATIC_INFORMATION (golden: 378, agent: 0)

The golden has this sheet; the agent produces `FILE_ADLS_INGESTION_DETAILS` instead.
These are structurally different tables — the agent's sheet is not a 1:1 match.

---

## 2. PIPELINE_ID == GROUP_ID + 200 Check

### Rule

In the IIG framework, PIPELINE_ID is conventionally derived as GROUP_ID + 200.
This was verified across all 7 goldens.

### Results

| Pair | Groups | PIPELINE_ID - GROUP_ID | Verdict |
| --- | --- | --- | --- |
| sfmc | 190141, 190142 | +200 | pass |
| pair_2 | 180251–180256 | +200 | pass |
| pair_5 | 2240732, 2240733 | +200 | pass |
| **pair_7** | **18603, 18604** | **+162,000** | **ANOMALY** |
| pair_8 | 4092933–4092943 | +200 | pass |
| pair_9 | 2109458903–2109458904 | +200 | pass |
| pair_10 | 2109459103–210944904 | +200 | pass |

### pair_7 Anomaly (±162,000)

GROUP_ID 18603 → PIPELINE_ID 180603 (delta = 162,000).
GROUP_ID 18604 → PIPELINE_ID 180604 (delta = 162,000).

This is not the standard +200 offset. The PIPELINE_ID appears to be constructed
by prepending `18` to the GROUP_ID (18 + 0603 = 180603), or alternatively the
GROUP_ID is 18603 and the PIPELINE_ID is 180603 with a multiplier-like offset.

This anomaly appears consistently across all 4 rows in the pair_7 golden
(adls_delta_ingestion_details, stgdelta_stddelta_ingestion_det, and both
databricks_notebook_details rows). It is NOT a data error — this is how
prod has these groups configured.

**Impact on agent**: An agent that hardcodes the +200 rule will produce wrong
PIPELINE_IDs for pair_7. The PIPELINE_ID derivation must use the actual mapping
from the IIG metadata database, not a formula.

---

## 3. RDBMS 3-Hop Section (Groups 3063/3064)

Groups 3063 and 3064 belong to **pair_6** (absent from prod golden — in the
`NO_GOLDEN` set). They demonstrate the RDBMS 3-hop ingestion pattern.

### Hop 1: RDBMS → ADLS (Group 3063)

- **Sheet**: `rdbms_adls_ingestion_details` (not `adls_delta_ingestion_details`)
- GROUP_ID = 3063, PIPELINE_ID = 3263 (delta = +200, standard)
- SOURCE_TYPE = RDBMS
- SRC_TABLE = `EXT_HICS_CASE_CUR_DAY` (schema `dbo`)
- SRC_CONNECTION_ID = 70
- TGT_ADLS_PATH = `/DIGITAL/UTILEXT/EXT_XCH_1/DBO`
- TGT_FILE_NAME = `EXT_HICS_CASE_CUR_DAY.csv`
- TGT_FORMAT = csv, TGT_LOAD_TYPE = Overwrite
- SRC_EXTRACT_TYPE = Full

### Hop 2: ADLS → Stage Delta (Group 3064)

- **Sheet**: `adls_delta_ingestion_details`
- GROUP_ID = 3064, PIPELINE_ID = 3264 (delta = +200, standard)
- Picks up `EXT_HICS_CASE_CUR_DAY.csv` from ADLS
- Loads into stage delta table

### Hop 3: Stage → Standard (implied)

The stgdelta_stddelta_ingestion_det step would be in a companion group
(likely 3064's STD counterpart or another group in the pair_6 set).

### Sheets per hop

| Hop | Group | Distinct Sheet | Other Sheets |
| --- | --- | --- | --- |
| RDBMS→ADLS | 3063 | rdbms_adls_ingestion_details | all_files_static_information, data_factory_pipeline_schedule |
| ADLS→Stage | 3064 | adls_delta_ingestion_details | all_files_static_information, data_factory_pipeline_schedule, databricks_notebook_details |

### Agent implications

The RDBMS hop uses a **different IIG sheet** (`rdbms_adls_ingestion_details`)
with different columns (SRC_SCHEMA, SRC_TABLE, SOURCE_TYPE=RDBMS) than the
standard file-to-stage path. The codegen agent must detect RDBMS-sourced
pipelines and emit this sheet instead of (or in addition to)
`adls_delta_ingestion_details`.

Group 3063 has no `databricks_notebook_details` — the RDBMS-to-ADLS hop
is an ADF pipeline without a Databricks notebook.

---

## 4. Coverage Section

### Pairs absent from prod (no golden)

| Pair | Reason |
| --- | --- |
| pair_1 | NOT_FOUND in the index (no prod golden) |
| pair_3 | NOT_FOUND in the index (no prod golden) |
| pair_4 | NOT_FOUND in the index (no prod golden) |
| pair_6 | NOT_FOUND in the index (no prod golden) |

These 4 pairs have agent_out/ directories but only pair_1 has an agent xlsx.
Pair_6 has RDBMS groups (3063/3064) that demonstrate a 3-hop pattern the agent
does not yet handle.

### SFMC STTM missing

The SFMC FRD (`FRD_STG_STD_SFMC_Email_Campaign_Tracking_Details_Ingestion_1005310.docx`)
is present in `inputs/databricks/` but its STTM is not. The notebook requires an STTM
(`assert len(sttms) == 1`). No SFMC agent run is possible until the STTM is added.

### Prompts the CLI cannot skip

| Pair | Prompt Type | Details |
| --- | --- | --- |
| pair_5 | Vocabulary error | Segment spelling 'NA' outside vocabulary; extraction-level, not layout-level |
| pair_7 | Layout answers | Every feed needs band/layer/role column placements; no `--proceed-unresolved` flag |
| pair_8 | FRD parser | Non-F1/F2 document; no `.contract.json` bypass available |
| pair_9 | FRD parser | Non-F1/F2 document; no `.contract.json` bypass available |
| pair_10 | FRD parser | Non-F1/F2 document; no `.contract.json` bypass available |
| sfmc | Missing STTM | Notebook asserts exactly 1 STTM_*.xlsx; FRD-only not supported |

The App's alternate FRD parser (for non-F1/F2) and its "proceed with unresolved"
dialog handle pair_8/9/10 and pair_7 respectively. These capabilities are not
exposed via the CLI or the notebook.

### Round 2 scoring gap

Only pair_2 has both golden + agent. The iig_diff score is 0.0 and the scorecard
is 0.1 because:
1. The agent output was from a mock (dry-run) session with different naming
2. Framework-assigned IDs (GROUP_ID, PIPELINE_ID, OBJECT_ID, connection IDs)
   are blank or sequential in agent output vs real prod values in golden
3. Row pairing keys (OBJECT_NAME, TGT_TABLE_NAME, PIPELINE_NAME) don't match

To get meaningful scores, agent runs need real FMAPI calls (not mock) and the
App's interactive features for pairs 5/7/8/9/10.
