# Round 3 IIG Validation — Routing Observed

Branch: `feature/multi-table`
Date: 2026-10-11
Delta from round 2: tooling improvements, position fallback pairing, template-mismatch detection.

> **SUPERSEDED (2026-10-12, home review).** Every pair_2 score below comes from
> a STALE agent workbook (a prior session's `multitable/out/`, before the
> post21 real-row rules) paired by the now-removed POSITION fallback, so a
> golden row could be compared with a different feed's agent row. Do not quote
> these numbers. `tools/iig_diff.py` now pairs by natural key only and refuses a
> workbook without a build identity; round 4 (`round4/pair_2/`) replaces them.
> Three statements below were also wrong and are corrected in place (marked
> "corrected 2026-10-12").

---

## 1. Per-Sheet, Per-Column Origin Tags (pair_2, round 3 diff)

All from the round 3 diff: pair_2 mock agent vs rebuilt golden (key mode with position
fallback). Sheets that gained paired rows are marked Δ.

### Δ ADLS_DELTA_INGESTION_DETAILS (golden: 3, agent: 3, paired: 3 via position fallback)

Round 2 paired 0 rows. Round 3 pairs by position (both sides ≤ 10 rows, key mismatch).

| Column | Origin | Status (round 3) | Note |
| --- | --- | --- | --- |
| OBJECT_NAME | FRD/STTM feed name | mismatch | Different feed identifiers |
| TGT_TABLE_NAME | STTM target band | mismatch | Prod vs generated naming |
| SRC_FILE_NAME | STTM/FRD file pattern | normalized/exact | Matches after case normalization |
| SRC_FORMAT | STTM file details | exact | csv/psv match |
| SRC_ADLS_CONNECTION_ID | acfc_env overlay | exact | Overlay value 7 matches |
| METADATA_CONNECTION_ID | acfc_env overlay | exact | Overlay value 4 matches |
| TGT_CONNECTION_ID | acfc_env overlay | exact | Overlay value 2 matches |
| SRC_CONTAINER_NAME | acfc_env overlay | exact | mftlanding matches |
| TGT_CONTAINER_NAME | acfc_env overlay | **mismatch** | corrected 2026-10-12: `pair_2/routing.csv:58` records `mismatch=3`, not exact |
| SRC_ADLS_PATH | path pattern | mismatch | Different path structure |
| TGT_ADLS_PATH | path pattern | normalized | Case/slash differences |
| GROUP_ID | needs_assignment | — | Not scored |
| PIPELINE_ID | needs_assignment | — | Not scored |
| OBJECT_ID | needs_assignment | — | Not scored |

**Score: 65.2** — environment constants (overlay) are exact; path patterns and feed names diverge.

### Δ STGDELTA_STDDELTA_INGESTION_DET (golden: 3, agent: 3, paired: 3 via position fallback)

| Column | Origin | Status | Note |
| --- | --- | --- | --- |
| OBJECT_NAME | STTM band | mismatch | |
| TGT_TABLE_NAME | STTM band | mismatch | |
| SRC_SCHEMA_NAME | STTM | exact/normalized | |
| TGT_SCHEMA_NAME | STTM | exact/normalized | |
| SRC_FORMAT | convention | exact | "delta" |

**Score: 52.2** — schema names match; table names differ (naming convention gap).

### Δ DATABRICKS_NOTEBOOK_DETAILS (golden: 6, agent: 3, paired: 3 via position fallback)

**Score: 19.4** — golden has 6 rows (2 per feed: ADLS + STD notebook), agent has 3 (one per feed).
3 paired; 3 missing-in-agent. The naming convention (EDO NB_ pattern) partially matches.

### ALL_FILES_STATIC_INFORMATION (golden: 18, agent: 3, paired: 3 by position)

Template mismatch detected: agent produces `FILE_ADLS_INGESTION_DETAILS`, golden has
`ALL_FILES_STATIC_INFORMATION`. Automatically mapped by `TEMPLATE_ALIASES` in iig_diff.

**Score: 1.4** — golden has 18 rows (post-filter), agent has 3; 15 rows missing-in-agent.
Key column (FILE_NAME) absent from agent sheet → falls back to position.

### DATA_FACTORY_PIPELINE_SCHEDULE (golden: 36, agent: 12, paired: 0)

**Score: 0.0** — PIPELINE_NAME key does not match (PL_File_ prefix convention vs agent names).
Round 3 did NOT fall back because golden has 36 rows > 10 threshold.

### EMAIL_TEMPLATE_CONFIG (golden: 12, agent: 6, paired: 0)

**Score: 0.0** — TEMPLATE_NAME + STATUS key; golden has "MIDS SDOH" as template name,
agent has blank TEMPLATE_NAME. Duplicate keys flagged.

### DATA_QUALITY_RULES (golden: 11, agent: 0)

**Score: 0.0** — mock run produces no DQ rules.

---

## 2. Anomalies Carried Forward from Round 2

### PIPELINE_ID = GROUP_ID + 200 (±162,000 for pair_7)

Unchanged. pair_7 GROUP_ID 18603 → PIPELINE_ID 180603 (delta = +162,000).
All other pairs follow the +200 convention. Agent must use actual mapping, not formula.

### RDBMS 3-Hop (pair_6, groups 3063/3064)

Unchanged. RDBMS-sourced pipelines use `rdbms_adls_ingestion_details` (not `adls_delta`).
Agent must detect SOURCE_TYPE=RDBMS and emit the correct sheet.

### Template Mismatch (ALL_FILES vs FILE_ADLS)

**Now auto-detected by iig_diff.** The `TEMPLATE_ALIASES` dict maps
`FILE_ADLS_INGESTION_DETAILS` → `ALL_FILES_STATIC_INFORMATION`. The `template_mismatch`
fact is reported in `score.json` per sheet. No manual intervention needed.

---

## 3. Score-Improvement Ranking

What would move the overall score most, ordered by cell-count impact:

| Rank | Action | Cells affected | Expected delta |
| --- | --- | --- | --- |
| 1 | ~~Live FMAPI run~~ — **wrong, corrected 2026-10-12** | — | The model never fills an IIG cell: Layer 2 sees only the `unmapped` validation rules and writes `candidates.json`; every IIG cell is Layer 1 (contracts + conventions profile + template constants), so a mock and a live run produce the same IIG. The real lever: re-run pair_2 on the current head (this workbook predates the post21 rules) and classify what still differs (class A / C / D) |
| 2 | **Pipeline-name alignment** (EDO NB_/PL_ naming) | 200+ | Schedule + notebook sheets move from 0.0 to key-paired |
| 3 | **Row-count alignment** (per-group rows) | 300+ | Schedule 36 vs 12, email 12 vs 6, all_files 18 vs 3 |
| 4 | **DQ rules generation** | 100+ | golden has 11 rows, agent has 0 |
| 5 | **Template-name fill** (TEMPLATE_NAME blank) | 12 | EMAIL_TEMPLATE_CONFIG key pairing |

---

## 4. Coverage (unchanged from round 2)

| Pair | Status |
| --- | --- |
| pair_1, 3, 4, 6 | No prod golden (NO_GOLDEN) |
| sfmc | No STTM input |
| pair_8, 9, 10 | Non-F1/F2 FRD format |
| pair_5 | NA segment fix done; layout needs interactive column placement (duplicate headers) |
| pair_7 | All feeds need layout answers (two-pass workflow) |
| pair_2 | **Scored** (mock): 7.9 overall (up from 0.0 in round 2) |