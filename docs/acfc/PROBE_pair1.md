# Probe Snapshot Record — pair 1

## Token Table

| Token | Category |
| --- | --- |
| <TOKEN_1> | catalog |
| <TOKEN_2> | catalog |
| <TOKEN_3> | catalog |
| <TOKEN_4> | schema |
| <TOKEN_5> | schema |
| <TOKEN_6> | table / feed |
| <TOKEN_7> | vendor |
| <TOKEN_8> | vendor |
| <TOKEN_9> | project |
| <TOKEN_9b> | project |
| <TOKEN_10> | identifier |
| <TOKEN_11> | business-term |
| <TOKEN_12> | business-term |
| <TOKEN_13> | email |
| <TOKEN_14> | person |
| <TOKEN_15> | organization |
| <TOKEN_16> | table-prefix |
| <TOKEN_17> | vendor-prefix |
| <TOKEN_19> | filename |
| <TOKEN_20> | filename |
| <TOKEN_21> | filename |
| <TOKEN_22> | sheet |
| <TOKEN_23> | sheet |

## Version

- **Version**: 0.8.1 (`pyproject.toml`)
- **Tag at HEAD**: none; `v0.8.1-acfc` points at `10aa9d9` (one behind HEAD `658c4e8`)
- **acfc-local merge commit**: `c8aae5f`

## Secret Scope Decision

22 secret scopes visible (<SCOPE_1> … <SCOPE_22>). Config `env.probe.metadata_db.secret_scope` is blank — metadata DB part **skipped**. All config-row objects recorded as `unreadable` (expected).

## Probe Headline

Feed `<TOKEN_6>` — **UNKNOWN**: 2 absent, 12 unreadable — the 12 unreadable object(s) decide between NOT STARTED and PARTIAL.

Identity: `<TOKEN_13>`, transports: `unity_catalog=spark`, `metadata_db=unavailable`.

## Probed Objects

| Object | State | What the generated DDL/DML did about it |
| --- | --- | --- |
| `<TOKEN_1>.<TOKEN_4>.<TOKEN_6>` (Stage) | absent | CREATE, as without a probe |
| `<TOKEN_2>.<TOKEN_5>.<TOKEN_6>` (Standard) | absent | CREATE, as without a probe |
| `DATA_FACTORY_PIPELINE_SCHEDULE[row 1]` | unreadable | INSERT, as without a probe (natural key PIPELINE_NAME blank) |
| `FILE_ADLS_INGESTION_DETAILS[row 1]` | unreadable | INSERT, as without a probe (natural key GROUP_ID blank) |
| `ADLS_DELTA_INGESTION_DETAILS[row 1]` | unreadable | INSERT, as without a probe (natural key GROUP_ID blank) |
| `ADLS_DELTA_INGESTION_DETAILS[row 2]` | unreadable | INSERT, as without a probe (natural key GROUP_ID blank) |
| `ADLS_DELTA_INGESTION_DETAILS[row 3]` | unreadable | INSERT, as without a probe (natural key GROUP_ID blank) |
| `STGDELTA_STDDELTA_INGESTION_DET[row 1]` | unreadable | INSERT, as without a probe (natural key GROUP_ID blank) |
| `ADLS_FIXED_WIDTH_HANDLER[row 1]` | unreadable | INSERT, as without a probe (natural key PROCESS_NAME blank) |
| `ADLS_FIXED_WIDTH_HANDLER[row 2]` | unreadable | INSERT, as without a probe (natural key PROCESS_NAME blank) |
| `ADLS_FIXED_WIDTH_HANDLER[row 3]` | unreadable | INSERT, as without a probe (natural key PROCESS_NAME blank) |
| `DATABRICKS_NOTEBOOK_DETAILS[row 1]` | unreadable | INSERT, as without a probe (natural key PIPELINE_NAME blank) |
| `EMAIL_TEMPLATE_CONFIG[row 1]` | unreadable | INSERT, as without a probe (natural key TEMPLATE_NAME blank) |
| `EMAIL_TEMPLATE_CONFIG[row 2]` | unreadable | INSERT, as without a probe (natural key TEMPLATE_NAME blank) |

## Generate Verdict

**Verdict: FAIL** — `ruff` check failed (28 findings).

### Failed Checks

| Check | Result | Findings |
| --- | --- | --- |
| ruff | **FAIL** | 28 findings: E501 Line too long (128 > 100) across `pipeline/` modules, `tests/`, `job/notebook_entrypoint.py`, `tools/make_fixtures.py` |

All other checks passed: `debug_patterns=ok`, `secrets=ok`, `test_per_module=ok`, `vdd_positions=ok`, `dml_parse_q1=ok`, `dml_parse_a2=ok`, `dml_parse_prod=ok`, `dml_row_counts=ok`, `sql_literals=ok`, `derivations=ok`.

### Environment Section (from report)

Deployment: **UNKNOWN** — 2 absent, 12 unreadable — the 12 unreadable object(s) decide between NOT STARTED and PARTIAL.

Snapshot used, taken 2026-09-22T13:53:27Z as `<TOKEN_13>` (probe age < 1 h). Observations replayed against current artefact expectations.

- 2 UC tables (`<TOKEN_1>.<TOKEN_4>.<TOKEN_6>`, `<TOKEN_2>.<TOKEN_5>.<TOKEN_6>`) → **absent** → CREATE emitted
- 12 config rows → **unreadable** (natural key columns blank at generation time; metadata DB transport unavailable) → INSERT emitted, as without a probe
