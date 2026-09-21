# RUN v0.5.1 — pair 1

Run of `acfc_run.py` cells 1–4 on the fixture pair-1 documents
(fixtures/acfc_shapes/) at staging HEAD `7810e27` (v0.5.1).

## Config diff vs staging

11 edits to `config/config.yaml` (uncommitted — stays local):

```diff
-  catalog: <PREV_CATALOG>
-  schema: <PREV_SCHEMA>
+  catalog: <TARGET_CATALOG>
+  schema: <TARGET_SCHEMA>

-  provider: auto
-  endpoint: null
+  provider: live
+  endpoint: <SERVING_ENDPOINT>

-  profile: <PREV_PROFILE>
+  profile: acfc_prx

-  default_catalog: {}
+  default_catalog: {stage: <STG_CATALOG>, standard: <STD_CATALOG>}

-  template: iig_v1
+  template: iig_v2

-  inputs: "local:./inputs"
-  state: "local:./ui/backend/state"
-  outputs: null
+  inputs: "workspace:<WORKSPACE_PATH>/frd_sttm_pairs"
+  state: "workspace:<WORKSPACE_PATH>/codegen-state"
+  outputs: "workspace:<WORKSPACE_PATH>/codegen-outputs"

-  extra_dirs: []
+  extra_dirs: ["workspace:<WORKSPACE_PATH>/frd_sttm_pairs"]
```

Environment: `CODEGEN_FORCE_MOCK_PROVIDER=1`,
`CODEGEN_CONFIG_OVERLAYS=fixtures/acfc_shapes/pair_1/config_overlay.yaml`,
`CODEGEN_STORAGE_STATE=local:<TEMPDIR>/state`,
`CODEGEN_STORAGE_OUTPUTS=local:<TEMPDIR>/outputs`.

Requirements marker: `# codegen-version-marker: 0.5.1` (confirmed).

## Cell 1 — pair

```
NONE            frd — no candidate shares any content
QUESTION        vdd — no candidate shares any content
REMEDY          answers file: pairing: {"<STTM_FILE>": {vdd: <candidate>}}
```

The fixture documents share no ticket number or name stem across sibling
fixtures; pairing relies on the explicit answers file or the `--vdd` flag.

## Cell 2 — layout --refresh

```
REFRESH         caches bypassed; runtime entries overwritten (0 provider call(s))
REPORT          <WORK>/unresolved_headers.md — 0 unresolved item(s), structural labels only
STTM            source=synonyms cache_hit=False provider_calls=0 roles_by_source={'synonyms': 27, 'model': 0, 'user': 0, 'cache': 0}
FRD             source=synonyms cache_hit=False provider_calls=0 roles_by_source={'synonyms': 38, 'model': 0, 'user': 0, 'cache': 0}
PROVIDER        databricks_fmapi, 0 call(s)
FRD CONTRACT    <WORK>/frd.contract.json — feeds ['<FEED_ID>'] (0 value(s) taken from the other documents)
```

Cross-checks: file_format=agree, frequency=agree, feed_name/schema/catalog=unchecked
(one side states none — the FRD leaves them as structured values).

**Provider call count: 0** — all 27 STTM + 38 FRD roles resolved by synonyms alone.

## Cell 3 — extract

```
EXTRACTED       <WORK>/sttm.contract.json — 1 feed(s): <FEED_ID> (23 fields)
EXTRACTED       <WORK>/vdd.contract.json — 4 file row(s), 23 field(s) on ['<VDD_SHEET>'], 23 position row(s); layout source synonyms, 0 unresolved role(s)
```

VDD extracted with source=synonyms, 0 unresolved roles. 4 file patterns extracted.

## Cell 4 — generate

```
FAIL            <FEED_ID> — 62 flag(s); ruff=FAIL, debug_patterns=ok, secrets=ok,
                test_per_module=ok, vdd_positions=ok, dml_parse_q1=ok, dml_parse_a2=ok,
                dml_parse_prod=ok, dml_row_counts=ok, sql_literals=ok, derivations=ok
```

### Verdict: PASS_WITH_FLAGS

The CLI exit code is 1 (ruff=FAIL on generated sketches), but the gate
report verdict is **PASS_WITH_FLAGS**.

### Flags (grouped)

| Group | Count | Items |
| --- | --- | --- |
| segments_from_sttm | 1 | FRD names no segments; STTM declares Header/Detail/Trailer |
| file_pattern_from_sttm | 1 | FRD names no file pattern; STTM states 4 patterns from meta/FILES |
| drag_fill_suspect:stage | 1 | Decimal(17,2)→(22,2) increments by one per adjacent column; confirm with STTM author |
| iig_blank | 8 | One flag per IIG tab listing framework-assigned / blank columns |
| rfc_number_unanswered | 1 | Placeholder `######` used |
| playbook_blank | 11 | Deployment Team, dates/times, Task Owner, Status |
| faq_unanswered | 6 | is_master_file, dedup_within_file, existing_record_policy, target_tables_exist, reject_threshold, data_integrity_checks |
| load_mode_not_enforced | 1 | Declared append; generated uses MERGE-by-file (branching v2) |
| rule_classified_flagged | 1 | Recycle process: FRD states rule but STTM has no structured spec |
| Layer-2 candidate pending | 6 | Mock sketches for 6 unmapped rules |
| generated_tests_skipped | 1 | `--skip-tests` passed |

## DDL diff

Generated `ACCUM_DDL.txt` vs fixture golden
(`fixtures/acfc_shapes/pair_1/golden/ACCUM_DDL.txt`): **IDENTICAL — 0 differences**.

Generated `ACCUM_DDL.txt` vs `<RFC_DIR>/ACCUM_DDL.txt` (the RFC sample):

```diff
--- <RFC_DIR>/ACCUM_DDL.txt
+++ generated/ACCUM_DDL.txt
@@ -1,7 +1,7 @@

 --stage table

-CREATE OR REPLACE TABLE <RFC_STG_CATALOG>.<RFC_STG_SCHEMA>.<RFC_TABLE>
+CREATE OR REPLACE TABLE <GEN_STG_CATALOG>.<GEN_STG_SCHEMA>.<GEN_TABLE>
 (
 SEGMENT_IDENTIFIER String,
 FILE_TYPE String,
@@ -33,7 +33,7 @@

 --standard table

-CREATE OR REPLACE TABLE <RFC_STD_CATALOG>.<RFC_STD_SCHEMA>.<RFC_TABLE>
+CREATE OR REPLACE TABLE <GEN_STD_CATALOG>.<GEN_STD_SCHEMA>.<GEN_TABLE>
 (
 SEGMENT_IDENTIFIER String,
 FILE_TYPE String,
```

The only differences are the aliased catalog/schema/table names: the RFC
sample carries the pre-alias names, while the generated output uses the
fixture alias map. Column lists, types, audit columns, `USING delta`,
banners, and whitespace are identical.

## IIG comparison

Generated `ACCUM_IIG.xlsx` vs golden `RFC_ACCUMULATORS_IIG.xlsx`:

| Sheet | Gen rows | Golden rows | Headers | Notes |
| --- | --- | --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 2 | 5 | MATCH | overlay template_rows gap (4 vs 1 data row) |
| FILE_ADLS_INGESTION_DETAILS | 2 | 2 | MATCH | |
| ADLS_DELTA_INGESTION_DETAILS | 5 | 5 | MATCH | |
| STGDELTA_STDDELTA_INGESTION_DET | 2 | 2 | MATCH | |
| ADLS_FIXED_WIDTH_HANDLER | 4 | 4 | MATCH | |
| DATABRICKS_NOTEBOOK_DETAILS | 2 | 4 | MATCH | overlay template_rows gap (3 vs 1 data row) |
| DATA_QUALITY_RULES | 9 | 9 | MATCH | |
| EMAIL_TEMPLATE_CONFIG | 3 | 3 | MATCH | |

All 8 sheets present, all headers match. Two sheets
(DATA_FACTORY_PIPELINE_SCHEDULE and DATABRICKS_NOTEBOOK_DETAILS) have fewer
data rows than the golden — the config overlay's `template_rows` multiply
the pipeline/notebook inventory but the overlay's row expansion is partial
vs the golden's full inventory.

## Question raised

No `gaps:` blocking question was raised. The 6 unanswered FAQ items
(`is_master_file`, `dedup_within_file`, `existing_record_policy`,
`target_tables_exist`, `reject_threshold`, `data_integrity_checks`) are
flagged in the verdict, not surfaced as interactive questions.

## Note on real-document pair

The real-document pair at `<PAIRS_DIR>/pair_1/` was also tested; the
layout resolves (source=cache, 0 provider calls, 0 unresolved) but
`extract-sttm` fails because neither the FRD nor the workbook names a
file pattern (the FRD Object Name cell is structured/multiline and the
STTM meta rows read TBD → blank). The fixture pair (which embeds synthetic
file patterns) is the one that completes the full chain.
