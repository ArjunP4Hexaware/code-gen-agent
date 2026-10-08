# SD scorecard — 2026-10-08

Run context:

* Branch head: `d84e2a6` (`feature/multi-table`, `0.5.8.post19`)
* Flags: `--output-mode framework --profile acfc_prx --iig-template iig_v2`
* Inputs reused from the earlier run: patched `out/pair_2_sd_run/pair_in/STTM_SD_MIDS_fixed.xlsx` and `out/pair_2_sd_run/pair_in/answers.yaml`
* Real comparison workbook: `IIG test cells.xlsx`

## Re-run verdict lines

| Feed | Verdict line |
| --- | --- |
| `sd_community_demographic_risk` | `FAIL — 172 flag(s); ruff=FAIL, debug_patterns=ok, secrets=ok, test_per_module=ok, generated_tests=FAIL, metadata_inserts=ok, sql_literals=ok, derivations=ok` |
| `sd_community_risk` | `FAIL — 356 flag(s); ruff=ok, debug_patterns=ok, secrets=ok, test_per_module=ok, generated_tests=FAIL, metadata_inserts=ok, sql_literals=ok, derivations=ok` |
| `sd_individual_risk` | `FAIL — 38 flag(s); ruff=ok, debug_patterns=ok, secrets=ok, test_per_module=ok, generated_tests=FAIL, metadata_inserts=ok, sql_literals=ok, derivations=FAIL` |

Notes:

* The post-`e02defa` behavior change is visible here: `sd_community_risk` is now **356** flags (was 357) and fails on `generated_tests`, not PASS_WITH_FLAGS.
* Every `generated_tests` failure is the same environment issue: `PySparkRuntimeError: [CANNOT_CONFIGURE_SPARK...]` in the generated pytest suite.

## ADLS_DELTA_INGESTION_DETAILS scorecards vs `IIG test cells.xlsx`

### `sd_community_demographic_risk`

Breakdown:

* matched: **40**
* open-by-design (`BSA` + `CI/CD`): **7**
* open-for-engineer (`Engineer` + `Engineer-confirm`): **2**
* diff: **6**

DIFF columns:

* `OBJECT_NAME` — real `demographics_package` | generated `demographics_package_MM.csv; demographics_package_MM`
* `SOURCE` — real `Socially Determined` | generated `Socially Determined – SD 33732`
* `SRC_FILE_NAME` — real `demographics_package*` | generated `demographics_package_*_MM.csv; demographics_package_*_MM.csv`
* `SRC_FILE_DELIMITER` — real `,` | generated `Comma`
* `TGT_COLUMN_NAMES` — real `90 items ['zip_code', 'total_population', 'gender_female_pop']` | generated `90 items ['zip_code', 'total_population', 'gender_female_pop']; first difference at item 87: 'LOB' vs 'SRC_FILE_NAME'`
* `TGT_DATA_TYPE` — real `90 items ['String', 'String', 'String']` | generated `90 items ['String', 'String', 'String']; first difference at item 87: 'string' vs 'String'`

### `sd_community_risk`

Breakdown:

* matched: **39**
* open-by-design (`BSA` + `CI/CD`): **7**
* open-for-engineer (`Engineer` + `Engineer-confirm`): **2**
* diff: **7**

DIFF columns:

* `OBJECT_NAME` — real `analytics_package` | generated `analytics_package_MM`
* `SOURCE` — real `Socially Determined` | generated `Socially Determined – SD 33732`
* `FREQUENCY` — real `Monthly` | generated `Yearly`
* `SRC_FILE_NAME` — real `analytics_package*` | generated `analytics_package_*_MM.csv`
* `SRC_FILE_DELIMITER` — real `,` | generated `Comma`
* `TGT_COLUMN_NAMES` — real `271 items ['zip_code', 'economic_risk_score', 'economic_risk_score_1_hex_count']` | generated `271 items ['zip_code', 'economic_risk_score', 'economic_risk_score_1_hex_count']; first difference at item 268: 'LOB' vs 'SRC_FILE_NAME'`
* `TGT_DATA_TYPE` — real `271 items ['String', 'String', 'String']` | generated `271 items ['String', 'String', 'String']; first difference at item 268: 'string' vs 'String'`

### `sd_individual_risk`

Breakdown:

* matched: **31**
* open-by-design (`BSA` + `CI/CD`): **8**
* open-for-engineer (`Engineer` + `Engineer-confirm`): **2**
* diff: **14**

DIFF columns:

* `OBJECT_NAME` — real `sd_ind_risk_data_package_amer` | generated `sd_ind_risk_data_package_amer_MI_HHMM`
* `SOURCE` — real `Socially Determined` | generated `Socially Determined – SD 33732`
* `SRC_ADLS_PATH` — real `/inbound/care_management/sdoh/socially_determined/` | generated `/inbound/care_management/sdoh/socially_determined./`
* `SRC_FILE_NAME` — real `sd_ind_risk_data_package_amer*` | generated `sd_ind_risk_data_package_amer_MI_*_HHMM.psv`
* `SRC_DATA_TYPE` — real `46 items ['String:String', 'String:String', 'String:String']` | generated `46 items ['String:String', 'Int:String', 'String:String']`
* `SRC_FILE_DELIMITER` — real `|` | generated `Comma`
* `SRC_ADLS_ARCHVL_PATH` — real `/inbound/care_management/sdoh/socially_determined/Archive/` | generated `/inbound/care_management/sdoh/socially_determined./Archive/`
* `TGT_ADLS_PATH` — real `/care_management/sdoh/socially_determined/Processed/sd_individual_risk` | generated `/care_management/sdoh/socially_determined./Processed/sd_individual_risk`
* `TGT_COLUMN_NAMES` — real `50 items ['member_id', 'sd_ind_financial_strain', 'sd_economic_principal_driver']` | generated `50 items ['member_id', 'sd_ind_financial_strain', 'sd_economic_principal_driver']; first difference at item 47: 'LOB' vs 'SRC_FILE_NAME'`
* `TGT_DATA_TYPE` — real `50 items ['String', 'String', 'String']` | generated `50 items ['String', 'String', 'String']; first difference at item 47: 'string' vs 'String'`
* `TGT_RJT_ADLS_PATH` — real `/care_management/sdoh/socially_determined/Reject/sd_individual_risk_reject` | generated `/care_management/sdoh/socially_determined./Reject/sd_individual_risk_reject`
* `RECYCL_ENBL_FLG` — real `Y` | generated `N`
* `RECYCL_TBL_NM` — real `sd_individual_risk_recycle` | generated `NA`
* `RECYCL_ADLS_PATH` — real `/care_management/sdoh/socially_determined/Recycle/sd_individual_risk_recycle` | generated `NA`

## Ruff findings — `sd_community_demographic_risk`

Source: `reports/sd_community_demographic_risk.md`.

| File | Line | Rule | Message |
| --- | ---: | --- | --- |
| `pipeline/feed_spec.py` | 40 | `E501` | Line too long (114 > 100) |
| `tests/test_orchestrator.py` | 34 | `E501` | Line too long (102 > 100) |
| `tests/test_orchestrator.py` | 46 | `E501` | Line too long (102 > 100) |
| `tests/test_orchestrator.py` | 69 | `E501` | Line too long (102 > 100) |

## `sd_community_risk` flags grouped by type

Source: `reports/sd_community_risk.md`.

Total flags: **356**.

| Flag type | Count |
| --- | ---: |
| `vdd_missing_in_vdd` | 267 |
| `vdd_missing_in_sttm` | 47 |
| `frd_unstated` | 6 |
| `iig_blank` | 6 |
| `faq_unanswered` | 6 |
| `sibling_type_mismatch` | 5 |
| `dml_not_described` | 3 |
| `frd_nested` | 2 |
| `catalog_from_config` | 2 |
| `dml_unassigned` | 2 |
| `frd_feeds_split_from_sttm` | 1 |
| `frd_nested_table` | 1 |
| `frd_label_prefixed` | 1 |
| `frd_multiline` | 1 |
| `frd_pointer` | 1 |
| `vdd_field_count` | 1 |
| `ddl_file_name_from_slug` | 1 |
| `dml_unconfirmed` | 1 |
| `load_mode_not_enforced` | 1 |
| `Layer-2 candidate pending engineer approval` | 1 |

Largest driver: `vdd_missing_in_vdd` (**267**) because the supplied VDD only covers the `Individual Risk` sheet while `sd_community_risk` has 267 STTM fields.

## Trailing-dot cell — `sd_individual_risk`

The root trailing-dot path literal is present in:

* `FILE_ADLS_INGESTION_DETAILS!I2` = `/mftlanding/inbound/care_management/sdoh/socially_determined./`

It then propagates into these generated cells:

* `ADLS_DELTA_INGESTION_DETAILS!O2`
* `ADLS_DELTA_INGESTION_DETAILS!X2`
* `ADLS_DELTA_INGESTION_DETAILS!AJ2`
* `ADLS_DELTA_INGESTION_DETAILS!AP2`
* `STGDELTA_STDDELTA_INGESTION_DET!N2`
* `STGDELTA_STDDELTA_INGESTION_DET!U2`
* `STGDELTA_STDDELTA_INGESTION_DET!AA2`
* `STGDELTA_STDDELTA_INGESTION_DET!AG2`

## Short takeaways

* `d84e2a6` did **not** fix the SD MIDS run end to end; all three feeds still fail the full gate because generated pytest needs a configurable Spark runtime.
* The scorecards are still useful because the framework outputs were written for all three feeds.
* The two material data-quality deltas remain:
  * `sd_community_risk` still emits `FREQUENCY = Yearly` while the real row says `Monthly`.
  * `sd_individual_risk` still carries the `socially_determined.` path segment and still misses recycle settings vs the real row.
