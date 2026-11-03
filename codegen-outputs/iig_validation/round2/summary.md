# Round 2 IIG Validation — Summary

Branch: `feature/multi-table`
Date: 2026-10-11

---

## 1. Provenance Table

| Pair | Runner | FMAPI vs Mock | Unresolved Prompts | Skipped Reason |
| --- | --- | --- | --- | --- |
| sfmc | — | — | — | No STTM in `inputs/databricks/`; notebook asserts exactly 1 STTM |
| pair_2 | prior run (multitable/out/) | mock (dry-run) | none (3-feed IIG from prior session) | — |
| pair_5 | — | — | segment 'NA' outside vocabulary (STTM extraction) | CLI extraction error; App handles it |
| pair_7 | — | — | every feed needs layout answers (band/layer roles) | No pre-built answers.yaml; requires interactive dialog |
| pair_8 | — | — | — | FRD is non-F1/F2 format; no `.contract.json` available |
| pair_9 | — | — | — | FRD is non-F1/F2 format; no `.contract.json` available |
| pair_10 | — | — | — | FRD is non-F1/F2 format; no `.contract.json` available |

**Coverage**: Only pair_2 has both a golden and an agent file.
Pairs 1/3/4/6 have no prod golden (`NO_GOLDEN` in `build_goldens.py`).
Pairs 5/7/8/9/10 have goldens but no agent outputs.
SFMC has a golden but no STTM input, so the notebook cannot run.

---

## 2. acfc_run.py Probe (step 2)

### Q1: Non-interactive run capability

**Partial.** The notebook accepts an `answers` widget pointing to an answers.yaml file.
Layout questions (`QUESTION`/`UNRESOLVED` lines) are resolved via `gaps:` and `answers:` sections.

**No `--proceed-unresolved` flag.** The `--require-complete` flag is hardcoded in the layout step —
unresolved roles always exit 3 (NEEDS_ANSWERS). Without answers.yaml or with incomplete answers,
the notebook stops at layout.

**Two-pass pattern**: First run discovers QUESTION/UNRESOLVED lines. Second run with answers.yaml
completes. The CLI's `extract-sttm` supports partial extraction (exit 0 + held-back feeds) but
the notebook's `--require-complete` blocks that path.

### Q2: Alternate FRD parser for non-F1/F2 documents

**No.** `frd_docx.py` handles only F1/F2 families. Non-F1/F2 FRDs (pair_8, 9, 10) hard-fail.

**Bypass exists**: If a pre-extracted `.contract.json` is in the pair folder, the notebook
skips FRD extraction (`if frd.suffix.lower() != ".docx": frd_contract = frd`). No pre-extracted
contracts exist for pair_8/9/10 outside the ephemeral `/tmp/` session.

### Q3: FRD-only run (no STTM)

**No.** Cell 7 asserts `len(sttms) == 1`. The entire pipeline (pair -> layout -> extract-sttm ->
generate) requires the STTM.

### Per-pair blockers

| Pair | Blocker | Prompts Needed |
| --- | --- | --- |
| pair_5 | `segment spelling 'NA' outside vocabulary` | Extraction-level, not fixable via answers.yaml |
| pair_7 | `every feed needs layout answers` | Band/layer/role column placements for each mapping sheet |
| pair_8 | `non-F1/F2 FRD format` | N/A (parser limitation) |
| pair_9 | `non-F1/F2 FRD format` | N/A (parser limitation) |
| pair_10 | `non-F1/F2 FRD format` | N/A (parser limitation) |
| sfmc | `no STTM in inputs/databricks/` | STTM file required; FRD-only not supported |

---

## 3. Pair x Sheet: iig_diff + iig_scorecard (pair_2 only)

The golden uses lowercase sheet names (prod export); the agent uses uppercase (codegen framework).
iig_diff matches case-insensitively (via `sheet_id()`); iig_scorecard partially does.

### iig_diff.py scores

| Sheet | Golden Rows | Agent Rows | Paired | Score |
| --- | --- | --- | --- | --- |
| adls_delta_ingestion_details | 3 | 3 | 0 | 0.0 |
| all_files_static_information | 378 | 0 (agent-only as FILE_ADLS_INGESTION_DETAILS) | 0 | 0.0 |
| data_factory_pipeline_schedule | 48 | 12 | 0 | 0.0 |
| data_quality_rules | 11 | 0 | 0 | 0.0 |
| databricks_notebook_details | 6 | 3 | 0 | 0.0 |
| stgdelta_stddelta_ingestion_det | 3 | 3 | 0 | 0.0 |
| EMAIL_TEMPLATE_CONFIG | 12 | 6 | 0 | 0.0 |
| ADLS_FIXED_WIDTH_HANDLER | 0 (agent-only) | 0 | 0 | 100.0 |
| **TOTAL** | — | — | — | **0.0** |

### iig_scorecard.py scores

| Sheet | Paired | Real-only | Score | Excl. Open-by-Design |
| --- | --- | --- | --- | --- |
| EMAIL_TEMPLATE_CONFIG | 6 | 6 | 5.6 | 6.2 |
| adls_delta_ingestion_details | 0 | 3 | 0.0 | 0.0 |
| all_files_static_information | 0 | 378 | 0.0 | 0.0 |
| data_factory_pipeline_schedule | 0 | 48 | 0.0 | 0.0 |
| data_quality_rules | 0 | 11 | 0.0 | 0.0 |
| databricks_notebook_details | 0 | 6 | 0.0 | 0.0 |
| stgdelta_stddelta_ingestion_det | 0 | 3 | 0.0 | 0.0 |
| **TOTAL** | **6** | **455** | **0.1** | **0.1** |

### Disagreement analysis (> 10-point)

No > 10-point disagreements between the two scorers because both report 0.0 for all matched
sheets except EMAIL_TEMPLATE_CONFIG (5.6 in scorecard vs 0.0 in diff). The diff scored 0.0
because row keys (TEMPLATE_NAME + STATUS) didn't pair (golden has `MIDS SDOH | Success` while
agent has `<blank> | Success`). The scorecard paired by STATUS alone and achieved 5.6.

### Why scores are so low

The pair_2 agent output was generated in a prior session from a different code path
(`code-gen-agent-multitable/out/`) with mock (dry-run) Layer 2. The golden is a prod export
with real GROUP_IDs, PIPELINE_IDs, OBJECT_IDs, and connection strings. The agent's rows have
freshly assigned sequential IDs. Row pairing fails because the natural keys
(OBJECT_NAME + TGT_TABLE_NAME, PIPELINE_NAME, SRC_FILE_NAME) differ between prod and generated.

---

## 4. pair_8 Golden Fix

**Before**: 18,124 rows (8 sheets). `all_files_static_information` had 14,528 rows because the
monthly group's `SRC_FILE_NAME = *` matched every file. `adls_fixed_width_handler` had 2,808
rows from 71 unrelated PIPELINE_IDs.

**Fix applied**:
- `all_files_static_information`: Replaced bare `*` pattern with `FM*` (834 monthly convention:
  FD=Daily, FW=Weekly, FM=Monthly, FR=Quarterly). 14,528 -> 392 rows.
- `adls_fixed_width_handler`: Filtered to 8 pair_8 PIPELINE_IDs only. 2,808 -> 416 rows.
- `data_factory_pipeline_schedule`: Filtered to 8 pair_8 PIPELINE_IDs only. 736 -> 64 rows.
- `EMAIL_TEMPLATE_CONFIG`: Kept as-is (16 rows, uses different PIDs from the index CSV).

**After**: 924 rows. No sheet over 500.
