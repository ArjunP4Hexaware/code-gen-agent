# RUN v0.5.2 — pair 1

Run of the codegen CLI on the **real** pair-1 documents
(`<PAIRS_DIR>/pair_1/`) at staging HEAD `e2cc3d2` (v0.5.2), merged into
`acfc-runs`.

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

Requirements marker: `# codegen-version-marker: 0.5.2` (confirmed).

## Pair (from answers.yaml)

```
PAIRING         answers.yaml maps <STTM_FILE> -> frd: <FRD_FILE>, vdd: <VDD_FILE>
ANSWERS         8 answer(s) applied (stage schema/table/column/target_type x2 + standard x4), source=user
GAPS            feeds[0].file_format = "Fixed Width" (FRD-sourced), feeds[0].frequency = "Daily" (VDD-sourced)
```

## Cell 2 — layout --refresh

```
REFRESH         caches bypassed; runtime entries overwritten (0 provider call(s))
NOTE            8 answers confirm synonyms (stage/standard schema/table/column/target_type)
NOTE            2 gaps match no open question (file_format, frequency already resolved)
ANSWERS         8 answer(s) applied from answers.yaml (source=user)
REPORT          <WORK>/unresolved_headers.md — 0 unresolved item(s), structural labels only
STTM            source=user cache_hit=False provider_calls=0 roles_by_source={'synonyms': 19, 'model': 0, 'user': 8, 'cache': 0}
FRD             source=synonyms cache_hit=False provider_calls=0 roles_by_source={'synonyms': 49, 'model': 0, 'user': 0, 'cache': 0}
PROVIDER        databricks_fmapi, 0 call(s)
FRD CONTRACT    <WORK>/frd.contract.json — feeds ['<FEED_ID>'] (1 value(s) taken from the other documents)
```

Cross-checks:

| Check | Result | Detail |
| --- | --- | --- |
| feed_name | unchecked | FRD Object Name multiline (3 labelled files); STTM uses its own stage table |
| stage_schema | unchecked | one side states none |
| stage_catalog | unchecked | one side states none |
| standard_schema | unchecked | one side states none |
| standard_catalog | unchecked | one side states none |
| file_format | agree | FRD 'Fixed width file' ↔ STTM 'Fixed-width' |
| delimiter | unchecked | one side states none |
| frequency | agree | FRD 'Daily' ↔ STTM 'Daily' |

**Provider call count: 0** — 19 STTM roles by synonyms + 8 by user; 49 FRD
roles by synonyms alone.

**file_pattern_from_frd**: the FRD's Object Name cell yields **3 file-name
patterns** (`<FILE_1>_YYYYMMDD_HHMMSS.txt`, `<FILE_2>_YYYYMMDD_HHMMSS.txt`,
`<FILE_3>_YYYYMMDD_HHMMSS.txt`). The STTM's meta/FILES supplies 1 pattern
matching the first. v0.5.1 real-pair note said "neither the FRD nor the
workbook names a file pattern" — v0.5.2's FRD reader now resolves labelled
files inside the multiline Object Name cell (M9.1b file-pattern chain fix).

## Cell 3 — extract

### extract-sttm

```
EXTRACTED       <WORK>/sttm.contract.json — 1 feed(s): <FEED_ID> (70 fields)
```

Key contract values:

| Field | Value |
| --- | --- |
| feed_id | <FEED_ID> |
| source_file.name_pattern | <FILE_1>_YYYYMMDD_HHMMSS.txt |
| source_file.format | Fixed width file |
| source_file.frequency | Daily |
| stage | <STG_CATALOG>.<STG_SCHEMA>.<FEED_ID> |
| standard | <STD_CATALOG>.<STD_SCHEMA>.<FEED_ID> |
| load_strategy (meta) | Append |
| segments (from fields) | Header, Detail, Trailer |
| field_count | 70 |
| audit_columns | LOB, SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME |

Extraction flags (6):

- `field_unmapped:Adj. Group (01)` — reads 'Do Not Map'
- `field_unmapped:Adj. Group (02)` — reads 'Do Not Map'
- `field_unmapped:Adj. Group (03)` — reads 'Do Not Map'
- `field_unmapped:Adj. Group (04)` — reads 'Do Not Map'
- `field_unmapped:Adj. Group (05)` — reads 'Do Not Map'
- `field_unmapped:Adj. Group (06)` — reads 'Do Not Map'

### extract-vdd

```
EXTRACTED       <WORK>/vdd.contract.json — 1 file row(s), 76 field(s) on ['<VDD_SHEET>'], 70 position row(s); layout source synonyms, 0 unresolved role(s)
```

VDD extracted with source=synonyms, 0 unresolved roles. 1 file pattern
extracted.

## Cell 4 — generate

```
FAIL            <FEED_ID> — template gap: fixed-width feed: field 'Amount\n(01)'
                in segment 'Detail' has no start/length in the STTM source band
                (start='220', length='10,2')
```

### Verdict: FAIL (pre-gate)

The generator fails **before** the gate: the six Amount fields in the Detail
segment carry `length='10,2'` (a Decimal precision,scale notation) which the
fixed-width template cannot parse as a byte width. All six affected fields:

| Field | Segment | Start | Length (raw) |
| --- | --- | --- | --- |
| Amount\n(01) | Detail | 220 | 10,2 |
| Amount\n(02) | Detail | 246 | 10,2 |
| Amount\n(03) | Detail | 272 | 10,2 |
| Amount\n(04) | Detail | 298 | 10,2 |
| Amount\n(05) | Detail | 324 | 10,2 |
| Amount\n(06) | Detail | 350 | 10,2 |

No output was produced — no DDL, IIG, framework inserts, or report. The gate
(ruff, debug_patterns, secrets, etc.) was never reached.

### Checks (not run)

Because the generator fails at the template gap before rendering any code:

- ruff: not run
- debug_patterns: not run
- secrets: not run
- test_per_module: not run
- vdd_positions: not run
- dml_parse_q1 / dml_parse_a2 / dml_parse_prod: not run
- dml_row_counts: not run
- sql_literals: not run
- derivations: not run

### Flags: none (gate not reached)

## DDL diff

Not applicable — the generator produced no DDL. No comparison to
`<RFC_DIR>/ACCUM_DDL.txt` is possible.

## IIG comparison

Not applicable — the generator produced no IIG workbook. No comparison to
the golden IIG is possible.

## Comparison to v0.5.1

| Aspect | v0.5.1 (fixtures) | v0.5.2 (real pair) |
| --- | --- | --- |
| layout | 27 STTM synonyms, 38 FRD synonyms | 19 STTM synonyms + 8 user, 49 FRD synonyms |
| provider calls | 0 | 0 |
| extract-sttm fields | 23 | 70 |
| file pattern | from STTM (4 patterns via meta/FILES) | from FRD (3 patterns via Object Name) + STTM (1 match) |
| file_pattern flag | file_pattern_from_sttm | file_pattern_from_frd (M9.1b chain fix) |
| extract-vdd | 4 file rows, 23 fields, 23 positions | 1 file row, 76 fields, 70 positions |
| generate | PASS_WITH_FLAGS (62 flags, ruff=FAIL) | FAIL (template gap: Decimal length '10,2') |
| DDL | IDENTICAL to fixture golden | not produced |
| IIG | 8 sheets, headers match, 2 row-count gaps | not produced |

## Root cause

The real STTM's source band encodes the six `Amount` fields' length as
`10,2` — meaning Decimal(10,2) (precision,scale). The fixture's synthetic
fields use plain integer widths. The fixed-width template's `start/length`
validator rejects the comma-bearing value because it cannot derive a byte
width from it. This is a **shape gap** (family B, fixed-width + Decimal
precision) not covered by the M9.1b patch.

## v0.5.3 action

Parse `length` as `precision,scale` → byte width = precision + sign +
decimal point (i.e., 10,2 → 13 bytes) or flag and ask. The template should
either consume the parsed width or flag it for human confirmation.
