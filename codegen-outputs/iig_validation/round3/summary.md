# Round 3 IIG Validation — Summary

Branch: `feature/multi-table`
Date: 2026-10-11

---

## 1. Tooling Changes

### build_goldens.py

| Change | Detail |
| --- | --- |
| Scoped PID filtering | PIPELINE_IDs collected from core ingestion sheets only (ADLS_DELTA, STGDELTA, DATABRICKS_NOTEBOOK) — schedule and fixed-width no longer seed the filter set |
| 834-family resolution | Bare `*` SRC_FILE_NAME resolved to the missing FD/FW/FM/FR prefix (pair_8: `*` → `FM*`) |
| all_files stem guard | Stems < 4 chars rejected (bare `*`, `*.*`, etc.) unless they match the 834 prefix set |
| Union header alignment | Column-name alignment on mismatch (instead of silent append) |
| Removed bare except | `except: pass` replaced with direct openpyxl call |
| Summary print | Now shows total rows, usable stems, email before/after counts |

### iig_diff.py

| Change | Detail |
| --- | --- |
| `--pair-mode` CLI | `{key, position, fuzzy}` — controls row-matching strategy |
| Key fallback | key mode auto-falls back to position when 0 rows pair and both sides ≤ 10 rows |
| `fuzzy_key()` | Strips PL_File_/PL_/NB_/WF_ prefixes, collapses underscores, casefolds |
| Template aliases | `FILE_ADLS_INGESTION_DETAILS` → `ALL_FILES_STATIC_INFORMATION` (template version mismatch) |
| score.json fields | `pair_mode` and `template_mismatch` added per sheet |

### test_iig_diff.py

7 new tests: position mode, key→position fallback, fuzzy pairing, `fuzzy_key()` unit,
template mismatch alias, `pair_mode` reporting, CLI argument. Total: **34/34 passed**.

### config.py

`"na": "NA"` added to `segment_names` — unblocks pair_5 STTM extraction (fixed-width with
NA segment marker no longer fails with "segment spelling 'NA' outside vocabulary").

---

## 2. Golden Rebuild

All 7 goldens rebuilt with the fixed `build_goldens.py`. Key improvements:

| Pair | Rows (before) | Rows (after) | Key change |
| --- | --- | --- | --- |
| sfmc | 28 | 20 | Schedule filtered 8→4 by scoped PIDs |
| pair_2 | 105 | 89 | Schedule 48→36, email 16→12 |
| pair_5 | 28 | 20 | Schedule 8→4 |
| pair_7 | 34 | 22 | Schedule 8→4 |
| pair_8 | 18124 (hand-patched to 924) | 884 | Automated: schedule 736→64, FWH 2808→416, all_files 368/14528, 834 `*`→`FM*` |
| pair_9 | 1263 | 205 | Schedule 222→4, email 860→20 (scoped PIDs) |
| pair_10 | 169 | 69 | Schedule 96→16, email 40→20 |

pair_8 is now fully automated (no hand-patch needed). The 884 vs 924 difference: scoped PIDs
(4093xxx) have no email template entries (the email CSV uses a different PID numbering space).

---

## 3. FRD / Pair Checks (Prerequisite C)

| Pair | Check | Result |
| --- | --- | --- |
| pair_9 | maternity / db_104 / 10945909xx | **Clean** — spec'd groups (2109458903, 2109458904) have only PeopleSoft (PS_*) tables |
| pair_10 | maternity / db_104 / 10945909xx | **Clean** — spec'd groups have only hra_bestfootforward; maternity/db_104 in non-spec'd groups |
| pair_5 | 5-cell sanity diff | **Pass** — self-diff 100.0 (322 scored cells), 5 perturbations = exactly 5 mismatches (98.4) |

No pairs excluded.

---

## 4. Provenance Table

| Pair | Runner | FMAPI vs Mock | Unresolved Prompts | Agent Output |
| --- | --- | --- | --- | --- |
| sfmc | — | — | No STTM input | No agent output |
| pair_2 | prior session (multitable/out/) | mock (dry-run) | none (3-feed IIG) | pair_2_iig_agent.xlsx |
| pair_5 | round 3 attempt | — | Layout needs column placement (duplicate "Stage Schema" headers at col I and M) | No agent output |
| pair_7 | round 3 attempt | — | Every feed needs layout answers (band/layer/role) | No agent output |
| pair_8 | — | — | Non-F1/F2 FRD format | No agent output |
| pair_9 | — | — | Non-F1/F2 FRD format | No agent output |
| pair_10 | — | — | Non-F1/F2 FRD format | No agent output |

### Extraction Attempt Details

**pair_2**: `pair` (exit 0) → `layout` (exit 3, 1 gap: `feeds[0].file_format`) → answered
"delimited" → `layout` (exit 0) → `extract-sttm` (exit 1: FRD contract has empty
`file_name_patterns`; FILE_DETAILS cell `demographics_package_CCYY_MM.csv; demographics_package_YYYY_MM.csv`
contains semicolon-separated patterns the matcher doesn't split). **Blocker**: the FRD parser
does not extract individual file names for multi-file feeds.

**pair_5**: `pair` (exit 1, VDD not auto-paired → answered via pairing section) → `layout`
(exit 3: `feeds[0].file_format` answered "Fixed-width"; `band[1]/layer` answered "stage";
then `stage/column` unresolved because columns I and M both say "Stage Schema" and the
candidate matcher picks column O "Standard Table - Column Name" instead of K). **Blocker**:
duplicate column headers require domain-expert confirmation of which K/I/M is stage vs standard.

**pair_7**: `pair` succeeded in round 2 but `layout` exited with NEEDS_ANSWERS for every feed.
The two-pass workflow needs the QUESTION/UNRESOLVED lines captured and an answers.yaml
written with band/layer/role/column placements for each mapping sheet.

---

## 5. Pair × Sheet: iig_diff (pair_2 only)

Agent: prior mock run. Golden: round 3 rebuilt. Pairing: key mode with position fallback.

| Sheet | Golden | Agent | Paired | Mode | Score |
| --- | --- | --- | --- | --- | --- |
| adls_delta_ingestion_details | 3 | 3 | 3 | position (fallback) | 65.2 |
| all_files_static_information | 18 | 3 | 3 | position | 1.4 |
| data_factory_pipeline_schedule | 36 | 12 | 0 | key | 0.0 |
| data_quality_rules | 11 | 0 | 0 | key | 0.0 |
| databricks_notebook_details | 6 | 3 | 3 | position (fallback) | 19.4 |
| stgdelta_stddelta_ingestion_det | 3 | 3 | 3 | position (fallback) | 52.2 |
| EMAIL_TEMPLATE_CONFIG | 12 | 6 | 0 | key | 0.0 |
| ADLS_FIXED_WIDTH_HANDLER | 0 | 0 | 0 | key | 100.0 |
| **TOTAL** | | | | | **7.9** |

Cell breakdown: 148 exact, 5 normalized, 71 mismatch, 1497 missing-in-agent, 207 extra-in-agent
(1928 scored cells).

### Round 2 → Round 3 comparison (pair_2)

| Metric | Round 2 | Round 3 | Delta |
| --- | --- | --- | --- |
| Overall score | 0.0 | 7.9 | +7.9 |
| Paired rows (ADLS) | 0 | 3 | +3 (position fallback) |
| Paired rows (STGDELTA) | 0 | 3 | +3 (position fallback) |
| Template mismatch | undetected | detected + auto-mapped | all_files ↔ FILE_ADLS |
| ADLS score | 0.0 | 65.2 | key fallback enabled pairing |
| STGDELTA score | 0.0 | 52.2 | key fallback enabled pairing |

The score increase is entirely from the **position fallback** — round 2 paired 0 rows
because the natural keys (OBJECT_NAME + TGT_TABLE_NAME, PIPELINE_NAME) differ between
prod golden and mock agent. Round 3's fallback pairs by ordinal when both sides have ≤ 10 rows,
unlocking cell-level comparison.

The template mismatch detection correctly maps the agent's `FILE_ADLS_INGESTION_DETAILS`
to the golden's `ALL_FILES_STATIC_INFORMATION`, avoiding a false golden-only + agent-only split.

### What would move the score most

1. **Row-count alignment** (schedule: 36 vs 12, email: 12 vs 6) — the mock run generates
   per-feed rows, the golden has per-group-per-feed rows. A live FMAPI run should produce
   group-aware row counts.
2. **data_quality_rules**: golden has 11 rows, agent has 0. The mock doesn't generate DQ rules.
3. **PIPELINE_NAME alignment**: key-mode pairing would succeed if the agent produced the
   same pipeline names as prod.

---

## 6. Commits

| Commit | Files | Message |
| --- | --- | --- |
| 1 | config.py | `fix(extract): accept 'NA' segment spelling` |
| 2 | .gitignore, build_goldens.py, iig_diff.py, test_iig_diff.py | `feat(iig-validation): round 3 tooling overhaul` |

---

## 7. Next Steps

1. **pair_2 live run**: Fix FRD `file_name_patterns` bridging for semicolon-separated
   FILE_DETAILS cells, then re-run with FMAPI (reasoning.provider=databricks_fmapi).
2. **pair_5 answers.yaml**: Domain expert to confirm column I vs M for Stage Schema,
   column K for Stage Column Name. Then run extract-sttm + generate.
3. **pair_7 two-pass**: Run layout without `--require-complete`, capture QUESTION/UNRESOLVED
   lines, write answers.yaml, re-run.
4. **pair_8/9/10**: Requires non-F1/F2 FRD parser or pre-extracted `.contract.json` files.
5. **sfmc**: Requires an SFMC STTM in the pair folder.