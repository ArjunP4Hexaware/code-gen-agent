# Run Report

* Status: FAILED
* Branch: feature/iig-first
* SHA: ca6bab8df7fbc7a8a4d8b631448fedbb8cb08976
* <redacted-3>stamp: 20261007T170530Z
* Env override: CODEGEN_SKIP_ENV_OVERLAY=1

## Environment

* Python: 3.12.3
* codegen-data-engineer-agent: 0.5.8.post11
* openpyxl: 3.1.5
* pydantic: 2.13.3
* jinja2: 3.1.6
* pyyaml: 6.0.3
* ruff: not installed
* databricks-sdk: 0.122.0
* Endpoint: databricks-claude-opus-5 (Endpoint<redacted-2>Ready.READY)

## Summary

| Pair | Status | Run<redacted-3> (s) | Layout Family | FRD Type | Verdict |
| --- | --- | --- | --- | --- | --- |
| pair_01 | FAILED | 9.9 | user | - | - |
| pair_02 | FAILED | 3.7 | - | - | - |
| pair_03 | FAILED | 205.6 | synonyms | - | - |
| pair_04 | FAILED | 5.2 | synonyms | - | - |
| pair_05 | FAILED | 2.9 | - | - | - |
| pair_06 | FAILED | 3.2 | - | - | - |
| pair_07 | FAILED | 5.3 | - | - | - |
| pair_08 | FAILED | 3.1 | - | - | - |
| pair_09 | FAILED | 4.0 | - | - | - |
| pair_10 | FAILED | 2.9 | - | - | - |

## pair_01

* Status: FAILED
* Run<redacted-3>: 9.9s
* Layout family: user

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | PASS |
| FRD extract | PASS |
| VDD cross-check | PASS |
| Generate | FAIL |
| DDL emit | FAIL |
| IIG workbook emit | FAIL |
| DML emit | FAIL |

### <redacted-1>s

* Mapped columns: 70

## pair_02

* Status: FAILED
* Run<redacted-3>: 3.7s

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | PASS |
| FRD extract | FAIL |

## pair_03

* Status: FAILED
* Run<redacted-3>: 205.6s
* Layout family: synonyms

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | PASS |
| FRD extract | PASS |
| VDD cross-check | PASS |
| Generate | FAIL |
| DDL emit | FAIL |
| IIG workbook emit | FAIL |
| DML emit | FAIL |

### <redacted-1>s

* Mapped columns: 331

## pair_04

* Status: FAILED
* Run<redacted-3>: 5.2s
* Layout family: synonyms

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | PASS |
| FRD extract | PASS |
| VDD cross-check | PASS |
| Generate | FAIL |
| DDL emit | FAIL |
| IIG workbook emit | FAIL |
| DML emit | FAIL |

### <redacted-1>s

* Mapped columns: 135

## pair_05

* Status: FAILED
* Run<redacted-3>: 2.9s

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | PASS |
| FRD extract | FAIL |

## pair_06

* Status: FAILED
* Run<redacted-3>: 3.2s

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | PASS |
| FRD extract | FAIL |

## pair_07

* Status: FAILED
* Run<redacted-3>: 5.3s

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | PASS |
| FRD extract | FAIL |

## pair_08

* Status: FAILED
* Run<redacted-3>: 3.1s

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | FAIL |

## pair_09

* Status: FAILED
* Run<redacted-3>: 4.0s

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | FAIL |

## pair_10

* Status: FAILED
* Run<redacted-3>: 2.9s

### Stages

| Stage | Status |
| --- | --- |
| <redacted-4> parse | FAIL |

## Per-Pair Stage Table

| Pair | Stage | Pass/Fail | First Error Line |
| --- | --- | --- | --- |
| pair_01 | <redacted-1> parse | PASS |  |
| pair_01 | FRD extract | PASS |  |
| pair_01 | VDD cross-check | PASS |  |
| pair_01 | Generate | FAIL | stage generate returned non-zero |
| pair_01 | DDL emit | FAIL | stage generate returned non-zero |
| pair_01 | IIG workbook emit | FAIL | stage generate returned non-zero |
| pair_01 | DML emit | FAIL | stage generate returned non-zero |
| pair_02 | <redacted-1> parse | PASS |  |
| pair_02 | FRD extract | FAIL | stage frd_extract returned non-zero |
| pair_03 | <redacted-1> parse | PASS |  |
| pair_03 | FRD extract | PASS |  |
| pair_03 | VDD cross-check | PASS |  |
| pair_03 | Generate | FAIL | stage generate returned non-zero |
| pair_03 | DDL emit | FAIL | stage generate returned non-zero |
| pair_03 | IIG workbook emit | FAIL | stage generate returned non-zero |
| pair_03 | DML emit | FAIL | stage generate returned non-zero |
| pair_04 | <redacted-1> parse | PASS |  |
| pair_04 | FRD extract | PASS |  |
| pair_04 | VDD cross-check | PASS |  |
| pair_04 | Generate | FAIL | stage generate returned non-zero |
| pair_04 | DDL emit | FAIL | stage generate returned non-zero |
| pair_04 | IIG workbook emit | FAIL | stage generate returned non-zero |
| pair_04 | DML emit | FAIL | stage generate returned non-zero |
| pair_05 | <redacted-1> parse | PASS |  |
| pair_05 | FRD extract | FAIL | stage frd_extract returned non-zero |
| pair_06 | <redacted-1> parse | PASS |  |
| pair_06 | FRD extract | FAIL | stage frd_extract returned non-zero |
| pair_07 | <redacted-1> parse | PASS |  |
| pair_07 | FRD extract | FAIL | stage frd_extract returned non-zero |
| pair_08 | <redacted-1> parse | FAIL | stage <redacted-1>_parse returned non-zero |
| pair_09 | <redacted-1> parse | FAIL | stage <redacted-1>_parse returned non-zero |
| pair_10 | <redacted-1> parse | FAIL | stage <redacted-1>_parse returned non-zero |

## Self-Check (Leak Gate)

* Terms checked: 3824
* MD hits redacted: 4
* Stage-table hits redacted: 1
* Total hit_count: 5
* Mode: inline-redact (not blocked)
* Env override: CODEGEN_SKIP_ENV_OVERLAY=1
