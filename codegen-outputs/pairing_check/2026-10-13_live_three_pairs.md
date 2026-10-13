# Live Pairing Check — 2026-10-13

codegen 0.5.8.post38 · profile: acfc_prx · IIG template: iig_v2 · provider=live (CODEGEN_PROVIDER) · overlays: config/overlays/acfc_env.yaml

## Environment

* Git: 490e089 on feature/multi-table
* Endpoint: databricks-claude-opus-5-5 (READY)
* Model used: Claude Opus 5.5
* Harness: --dry-run removed, CODEGEN_PROVIDER=live, branch default feature/multi-table
* App redeploy: FAILED (source_code_path snapshot could not locate out/ dir after cleanup)

## Summary

| Pair | Layout | Extract-STTM | Extract-VDD | Generate | Verdict | Feeds | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- |
| pair_02 | 0 | 0 | 0 | 0 | PASS_WITH_FLAGS (all 3 feeds) | 3 | 570 total |
| pair_11 | 0 | 1 | N/A | skipped | FAILED at extract-sttm | 0 (5 sheets, 1 FRD feed) | — |
| pair_12 | 0 | 0 | N/A | 1 | FAIL (derivations) | 1 | 46 |

---

## pair_02 — Medicare Expansion MIDS / Socially Determined

### Files in folder

| File | Role |
| --- | --- |
| FRD_Medicare Expansion-MIDS - Socially Determined (1).docx | FRD |
| STTM_Medicare Expansion_MIDS_Social Determined.xlsx | STTM (named) |
| STTM_Medicare Expansion-MIDS - Socially Determined_blank_version.xlsx | STTM (blank, unused) |
| VDD_Socially_Determined_MIDS.xlsx | VDD |

### Pairing decision

Rule: synonyms (no model call needed for either STTM or FRD layout).  
STTM: source=synonyms, provider_calls=0, roles_by_source: synonyms=47.  
FRD: source=synonyms, provider_calls=0, roles_by_source: synonyms=49.

### Layout

* Exit code: 0
* 3 unresolved items (structural labels only)
* 3 NOTE lines (file_name_patterns by elimination, file_format from extension + VDD confirmation)
* No QUESTION or WARNING lines
* FRD contract: 3 feeds (sd_community_demographic_risk, sd_community_risk, sd_individual_risk)

### Extract-STTM

* Exit code: 0
* 3 feeds: sd_community_demographic_risk (86 fields), sd_community_risk (267 fields), sd_individual_risk (46 fields)

### Extract-VDD

* Exit code: 0
* 3 file rows, 411 fields on Demographics / Economic Risk / Individual Risk
* 0 unresolved roles

### Generate

* Exit code: 0
* Model: Claude Opus 5.5 (databricks-claude-opus-5-5)
* Per-feed verdicts:
  * sd_community_demographic_risk — PASS_WITH_FLAGS, 349 flags
  * sd_community_risk — PASS_WITH_FLAGS, 170 flags
  * sd_individual_risk — PASS_WITH_FLAGS, 51 flags
* All checks passed: ruff, debug_patterns, secrets, test_per_module, metadata_inserts, sql_literals, derivations

### Feed IDs

1. sd_community_demographic_risk
2. sd_community_risk
3. sd_individual_risk

### IIG sheet-by-sheet row counts

**sd_community_demographic_risk_IIG.xlsx**

| Sheet | Rows |
| --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 5 |
| FILE_ADLS_INGESTION_DETAILS | 2 |
| ADLS_DELTA_INGESTION_DETAILS | 2 |
| STGDELTA_STDDELTA_INGESTION_DET | 2 |
| ADLS_FIXED_WIDTH_HANDLER | 1 |
| DATABRICKS_NOTEBOOK_DETAILS | 3 |
| DATA_QUALITY_RULES | 1 |
| EMAIL_TEMPLATE_CONFIG | 3 |

**sd_community_risk_IIG.xlsx**

| Sheet | Rows |
| --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 5 |
| FILE_ADLS_INGESTION_DETAILS | 2 |
| ADLS_DELTA_INGESTION_DETAILS | 2 |
| STGDELTA_STDDELTA_INGESTION_DET | 2 |
| ADLS_FIXED_WIDTH_HANDLER | 1 |
| DATABRICKS_NOTEBOOK_DETAILS | 3 |
| DATA_QUALITY_RULES | 1 |
| EMAIL_TEMPLATE_CONFIG | 3 |

**sd_individual_risk_IIG.xlsx**

| Sheet | Rows |
| --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 5 |
| FILE_ADLS_INGESTION_DETAILS | 2 |
| ADLS_DELTA_INGESTION_DETAILS | 2 |
| STGDELTA_STDDELTA_INGESTION_DET | 2 |
| ADLS_FIXED_WIDTH_HANDLER | 1 |
| DATABRICKS_NOTEBOOK_DETAILS | 3 |
| DATA_QUALITY_RULES | 1 |
| EMAIL_TEMPLATE_CONFIG | 3 |

### IIG diff

No golden IIG found in pair_02 folder. Diff not run.

---

## pair_11 — Pyx Care Management MI DSNP

### Files in folder

| File | Role |
| --- | --- |
| Pyx_ Care Management Data MI DSNP_FRD.docx | FRD |
| STTM_Pyx_Care_Management_Data_MI_DSNP.xlsx | STTM |
| 25_Pyx_Health_IIG.xlsx | Golden IIG |

### Pairing decision

Rule: synonyms for FRD (0 provider calls); synonyms + 1 model call for STTM (model response rejected — schema validation failed).  
STTM: source=synonyms, provider_calls=1, roles_by_source: synonyms=150.  
FRD: source=synonyms, provider_calls=0, roles_by_source: synonyms=49.  
Note: STTM model response REJECTED (8 validation errors).

### Layout

* Exit code: 0 (81.0s)
* 10 unresolved items (structural labels only)
* 9 UNRESOLVED Table_Details roles (field_name, schema, table, column, target_type for stage+standard)
* 5 mapping sheets detected: Monthly Engmnt Billing, Monthly Outreach Report, Monthly Screening Repor, Weekly Activity Report, Weekly DNC Report
* FRD contract: 1 feed (unnamed — "feed 1 (unnamed)")
* CROSSCHECK: feed_name disagree (FRD unnamed vs STTM file details), stage_schema agree (stg_cm), standard_schema agree (cm), file_format disagree (Text files vs csv), frequency agree (Weekly Wednesday)

### Extract-STTM

* Exit code: 1 (0.9s)
* FAIL: all 5 mapping sheets paired with the single unnamed FRD feed
* Error: "each mapping sheet must be its own feed: write the FRD contract with `codegen layout --frd-contract-out`"
* Pipeline halted — no IIG generated

### Generate

* Skipped (extract-sttm failed)

### Feed IDs

Expected 5 distinct feeds (one per mapping sheet): Monthly Engmnt Billing, Monthly Outreach Report, Monthly Screening Report, Weekly Activity Report, Weekly DNC Report.  
Actual: 0 feeds extracted (blocked by single-FRD-feed → multiple-sheet mismatch).

### IIG diff

Golden IIG (25_Pyx_Health_IIG.xlsx) present but no generated IIG to diff against. Diff not run.

---

## pair_12 — Payment Integrity TPL CAQH

### Files in folder

| File | Role |
| --- | --- |
| Payment Integrity_CAQH_EDO_TPL process Improvement FRD_08032026SS.docx | FRD |
| STTM_STG_STD_PaymentIntegrity_TPL_CAQH_To_DL_Mapping_Document_1005034.xlsx | STTM |
| PAYMENT_INTEGRITY_CAQH_IIG.xlsx | Golden IIG |

### Pairing decision

Rule: synonyms (no model call needed for either STTM or FRD layout).  
STTM: source=synonyms, provider_calls=0, roles_by_source: synonyms=31.  
FRD: source=synonyms, provider_calls=0, roles_by_source: synonyms=49.

### Layout

* Exit code: 0 (3.5s)
* 0 unresolved items
* 1 sheet: caqh (31 roles, all source=synonyms)
* Feed: EXT_TPL_CAQH_DTL
* CROSSCHECK: feed_name agree (EXT_TPL_CAQH_DTL vs CAQH), frequency agree (Weekly Monday 8 PM vs Weekly)
* Model: Resolved from documents (no model call needed)

### Extract-STTM

* Exit code: 0 (0.9s)
* 1 feed: ext_tpl_caqh_dtl (115 fields)

### Generate

* Exit code: 1 (87.2s)
* Verdict: FAIL, 46 flags
* CHECK FAILED derivations: 22 cells with line break in SUBDOMAIN ("Domain: Member\\nSub Domain: Third Party Liability")
* Model: Claude Opus 5.5 (databricks-claude-opus-5-5) · 5 calls
* All other checks passed: ruff, debug_patterns, secrets, test_per_module, metadata_inserts, sql_literals

### Feed IDs

1. ext_tpl_caqh_dtl

### IIG sheet-by-sheet row counts

**ext_tpl_caqh_dtl_IIG.xlsx**

| Sheet | Rows |
| --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 5 |
| FILE_ADLS_INGESTION_DETAILS | 2 |
| ADLS_DELTA_INGESTION_DETAILS | 19 |
| STGDELTA_STDDELTA_INGESTION_DET | 4 |
| ADLS_FIXED_WIDTH_HANDLER | 1 |
| DATABRICKS_NOTEBOOK_DETAILS | 3 |
| DATA_QUALITY_RULES | 19 |
| EMAIL_TEMPLATE_CONFIG | 3 |

### IIG diff — pair_12 (CAQH)

Golden: PAYMENT_INTEGRITY_CAQH_IIG.xlsx (iig_v1 layout, 7-sheet).  
Agent: ext_tpl_caqh_dtl_IIG.xlsx (regenerated with `--iig-template iig_v1`).  
Agent build: 0.5.8.post38 · 490e089 on feature/multi-table.

**Comparable score: 0.0** over 2150 scoped cells (2 golden rows out of scope).

| Sheet | Score | Exact | Norm | Mismatch | Missing | Extra | Needs-assign |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 0.0 | 0 | 0 | 0 | 92 | 46 | 30 |
| ADLS_DELTA_INGESTION_DETAILS | 0.0 | 0 | 0 | 0 | 810 | 135 | 210 |
| STGDELTA_STDDELTA_INGESTION_DET | 0.0 | 0 | 0 | 0 | 90 | 90 | 60 |
| DATA_QUALITY_RULES | 0.0 | 0 | 0 | 0 | 378 | 14 | 336 |
| DATABRICKS_NOTEBOOK_DETAILS | 0.0 | 0 | 0 | 0 | 26 | 26 | 24 |
| EMAIL_TEMPLATE_CONFIG | 0.0 | 0 | 0 | 0 | 26 | 26 | 8 |
| ALL_FILES_STATIC_INFORMATION | 0.0 | 0 | 0 | 0 | 368 | 23 | 68 |
| **TOTAL** | **0.0** | 0 | 0 | 0 | 1790 | 360 | 736 |

**Warnings:**

* DATA_FACTORY_PIPELINE_SCHEDULE: agent duplicate key (PIPELINE_NAME) — paired in sheet order
* DATA_QUALITY_RULES: 2 agent rows with unresolved OBJECT_ID — not paired; 3 golden duplicate keys — paired in sheet order
* DATABRICKS_NOTEBOOK_DETAILS: agent duplicate key (DATABRICKS_NOTEBOOK_NAME) — paired in sheet order
* ALL_FILES_STATIC_INFORMATION: key column FILE_NAME not in both sheets — rows not paired; 2 golden rows out of scope

#### iig_v2 comparison (agent generated with `--iig-template iig_v2`)

**Comparable score: 0.2** over 2888 scoped cells (2 golden rows out of scope).  
Agent IIG has an extra sheet (ADLS_FIXED_WIDTH_HANDLER) not in the golden.

| Sheet | Score | Exact | Norm | Mismatch | Missing | Extra | Needs-assign |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 0.0 | 0 | 0 | 0 | 92 | 44 | 40 |
| ADLS_DELTA_INGESTION_DETAILS | 0.0 | 0 | 0 | 0 | 810 | 792 | 360 |
| STGDELTA_STDDELTA_INGESTION_DET | 0.0 | 0 | 0 | 0 | 90 | 90 | 60 |
| DATA_QUALITY_RULES | 0.0 | 0 | 0 | 0 | 378 | 126 | 432 |
| DATABRICKS_NOTEBOOK_DETAILS | **15.4** | **6** | 0 | 0 | 20 | 13 | 18 |
| EMAIL_TEMPLATE_CONFIG | 0.0 | 0 | 0 | 0 | 26 | 24 | 12 |
| ALL_FILES_STATIC_INFORMATION | 0.0 | 0 | 0 | 0 | 368 | 9 | 72 |
| ADLS_FIXED_WIDTH_HANDLER | (not in golden) | — | — | — | — | — | — |
| **TOTAL** | **0.2** | 6 | 0 | 0 | 1784 | 1098 | 994 |

#### Template comparison

| Metric | iig_v1 | iig_v2 |
| --- | --- | --- |
| Comparable score | 0.0 | 0.2 |
| Scoped cells | 2150 | 2888 |
| Exact matches | 0 | 6 |
| Needs-assignment | 736 | 994 |
| Best sheet | — | DATABRICKS_NOTEBOOK_DETAILS (15.4) |

iig_v2 is marginally better: DATABRICKS_NOTEBOOK_DETAILS paired 6 cells by key (the notebook naming convention matched). Every other sheet still scores 0.0 — keys diverge across the board.

**Interpretation:** Both templates are dominated by key-pairing failures (`needs_assignment`), meaning rows exist on both sides but the natural keys (PIPELINE_NAME, OBJECT_ID, NOTEBOOK_NAME, FILE_NAME) diverge between golden and agent. The hint continues to flag the golden as iig_v1, but the v2 template paradoxically scores better because its extra ADLS_DELTA rows happen to line up the DATABRICKS_NOTEBOOK_DETAILS keys.

---

## Step 6 — App _plan_pair (Pyx)

Blocked: the app deployment to post38 failed (source_code_path could not snapshot the workspace folder after out/ cleanup). The running app is on post37 (1a5d7ad). Direct API call returned 401 (OAuth required). _plan_pair comparison not performed.

---

## Leak Gate

* Terms checked: 1126 (all STTM/VDD cell values >20 chars from pair_2, pair_11, pair_12)
* Hits: 1 — feed name "sd_community_demographic_risk" (a table name that appears in both the report and STTM cells; technical identifier, not document content)
* No emails, no numeric IDs, no duplicate-key values, no document prose found
* Verdict: CLEAN (false positive — feed/table names are pipeline output metadata)

---

## Observations

1. **pair_02** runs cleanly end-to-end on post38 with provider=live. All 3 feeds produce IIGs. Flag count 570 is non-zero but all checks pass.
2. **pair_11** hits a structural wall: the FRD has a single unnamed feed but the STTM has 5 distinct mapping sheets. The layout phase now correctly identifies 5 sheets and names them, but the FRD contract is written with only 1 unnamed feed, causing extract-sttm to reject the 5-to-1 mismatch.
3. **pair_12** gets through layout and extraction cleanly but generate fails on the SUBDOMAIN derivation: the FRD's "Domain: Member\nSub Domain: Third Party Liability" string contains a literal line break that propagates into IIG cells.
