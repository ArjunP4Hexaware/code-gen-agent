# Multi-table Run — 2026-10-08

Branch `feature/multi-table` at **e02defa** (`0.5.8.post17`).  
Flags: `--output-mode framework --profile acfc_prx --iig-template iig_v2`.  
Layer 2: mock (CODEGEN_FORCE_MOCK_PROVIDER).  
Overlay: `config/overlays/acfc_env.yaml` (always-on).

---

## Pair 1 — PRX-family fixture

Fixture STTM (`pair_1_family_a.xlsx`), FRD (`f1_pair_1.docx`), VDD
(`pair_1_v1_segments.xlsx`), plus `pair_1/config_overlay.yaml`.

### Verdict

```
PASS_WITH_FLAGS vnd_p_accum_client — 42 flag(s); ruff=ok, debug_patterns=ok,
secrets=ok, test_per_module=ok, vdd_positions=ok, metadata_inserts=ok,
sql_literals=ok, derivations=ok
```

### Per-sheet row counts

| Sheet | Rows |
| --- | ---: |
| DATA_FACTORY_PIPELINE_SCHEDULE | 4 |
| FILE_ADLS_INGESTION_DETAILS | 1 |
| ADLS_DELTA_INGESTION_DETAILS | 4 |
| STGDELTA_STDDELTA_INGESTION_DET | 1 |
| ADLS_FIXED_WIDTH_HANDLER | 3 |
| DATABRICKS_NOTEBOOK_DETAILS | 3 |
| DATA_QUALITY_RULES | 8 |
| EMAIL_TEMPLATE_CONFIG | 2 |

### metadata_inserts.sql

Written: **yes** — **27 INSERTs**, 44 048 bytes.

### Scorecard — generated vs pair-1 golden (`--all-sheets`)

| Sheet | Score | Excl. open-by-design | Paired | Diff | Open | Alias |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DATA_FACTORY_PIPELINE_SCHEDULE | 51.6 | 82.5 | 4 | 3 | 28 | 0 |
| FILE_ADLS_INGESTION_DETAILS | 29.4 | 62.5 | 1 | 0 | 12 | 0 |
| ADLS_DELTA_INGESTION_DETAILS | 64.4 | 72.4 | 4 | 41 | 36 | 4 |
| STGDELTA_STDDELTA_INGESTION_DET | 67.5 | 81.8 | 1 | 1 | 12 | 0 |
| ADLS_FIXED_WIDTH_HANDLER | 60.9 | 77.8 | 3 | 0 | 27 | 0 |
| DATABRICKS_NOTEBOOK_DETAILS | 33.3 | 70.4 | 3 | 2 | 36 | 0 |
| DATA_QUALITY_RULES | 61.5 | 100.0 | 8 | 0 | 40 | 8 |
| EMAIL_TEMPLATE_CONFIG | 31.2 | 45.5 | 2 | 2 | 20 | 0 |
| **TOTAL (8 sheets)** | **56.6** | **77.0** | **26** | **49** | **211** | **12** |

All 26 real rows paired; 0 real-only, 0 generated-only. Every DIFF is a
pinned deviation (environment constant, overlay convention, or open cell).
DATA_QUALITY_RULES scores 100.0 excl. open-by-design. The main DIFF
families are:
* environment constants (`SRC_ADLS_CONNECTION_ID`, `TGT_CONTAINER_NAME`,
  `SCHEMA_DRIFT_FLAG`) — the golden carries synthetic values, the overlay
  carries the d1 environment's;
* SRC_COLUMNS style (`col<N>:…` in the golden vs `<name>:<name>` from
  `src_columns_style: named`);
* MANDATORY_FIELD_LIST (generated = not-null columns, golden = blank);
* HEADER_FLAG / TGT_LOAD_OPTION / TGT_REFRESH_TYPE (FRD-stated vs golden);
* EMAIL_TO (environment distribution list vs a personal address).

---

## SD MIDS — Socially Determined (3 feeds)

Real documents from the pair folder. The STTM required two pre-processing
fixes (annotation row in FILE_DETAILS removed; empty Schema / TableName
columns filled from the existing demo output's conventions) and a 7-gap
answers.yaml (file_format × 3, file_name_patterns × 3, frequency × 1).
No per-pair config overlay.

### Verdicts

| Feed | Verdict | Flags | Gate failures |
| --- | --- | ---: | --- |
| sd_community_demographic_risk | **FAIL** | 173 | ruff (4 findings) |
| sd_community_risk | **PASS_WITH_FLAGS** | 357 | — |
| sd_individual_risk | **FAIL** | 39 | derivations (path punctuation) |

The ruff failures in `sd_community_demographic_risk` and the path-segment
punctuation (`socially_determined.` with a trailing dot) in
`sd_individual_risk` are pre-existing input issues, not multi-table
regressions.

### Per-sheet row counts

| Sheet | demographic_risk | community_risk | individual_risk |
| --- | ---: | ---: | ---: |
| DATA_FACTORY_PIPELINE_SCHEDULE | 4 | 4 | 4 |
| FILE_ADLS_INGESTION_DETAILS | 1 | 1 | 1 |
| ADLS_DELTA_INGESTION_DETAILS | 1 | 1 | 1 |
| STGDELTA_STDDELTA_INGESTION_DET | 1 | 1 | 1 |
| ADLS_FIXED_WIDTH_HANDLER | 0 | 0 | 0 |
| DATABRICKS_NOTEBOOK_DETAILS | 1 | 1 | 1 |
| DATA_QUALITY_RULES | 0 | 0 | 0 |
| EMAIL_TEMPLATE_CONFIG | 2 | 2 | 2 |

Each feed produces one file and one table (CSV, no segments) — hence 1 row
in FILE_ADLS, ADLS, STGDELTA and NOTEBOOK, and 0 in FIXED_WIDTH and DQ
(DQ rules are not generated for CSV feeds without explicit DQ definitions).

### metadata_inserts.sql

| Feed | Written | INSERTs | Bytes |
| --- | --- | ---: | ---: |
| sd_community_demographic_risk | yes | 11 | 39 968 |
| sd_community_risk | yes | 11 | 112 556 |
| sd_individual_risk | yes | 11 | 32 238 |

### Scorecard — no golden IIG

The SD MIDS pair has no golden IIG workbook to score against. The real
file-to-stage row counts from the STTM mapping sheets are:

| Sheet (STTM) | Stage fields |
| --- | ---: |
| MAPPING- (demographics) | 86 |
| MAPPING-1 (community risk) | 267 |
| MAPPING-2 (individual risk) | 46 |

These counts match the `EXTRACTED` output of `extract-sttm`: 86, 267 and
46 fields respectively. A golden-grade scorecard requires a real completed
IIG from the deployment team.

---

## Notes

* **Real pair_1 documents** (from the workspace pair folder) hit a
  `KeyError: 'REC_TYP_TRLR'` at `context.py:445` — the trailer segment's
  record-type column appears in `natural_key_columns` but not in
  `detail_fields_by_stage`. The fixture pair (aliased / synthetic) does not
  trigger this because its column names and segment structure differ. This
  is a pre-existing edge case in the real-document extractor.
* **SD MIDS STTM quality issues** — the FILE_DETAILS sheet has an
  annotation row in position 6 (`Amber italic DataType = …`) that the
  extractor reads as a data row, and all three MAPPING sheets have blank
  Schema / TableName columns. Both issues required manual patching before
  the pipeline could run. The pair was previously recorded as
  `NEEDS_ANSWERS` in the watcher state.
