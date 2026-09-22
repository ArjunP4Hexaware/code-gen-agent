# v0.6.0 — Pair 1 end-to-end run

> Automated verification of the v0.6.0-acfc deployment against pair 1
> (OptumRx Accumulators). Executed 2026-09-22.

## 1  Git & deploy

| Step | Outcome |
| --- | --- |
| `git checkout staging && git pull` | cdda58f — M10: environment reconciliation |
| pyproject version | 0.6.0 |
| requirements marker | codegen-version-marker: 0.6.0 |
| `git checkout acfc-local` | created from acfc-hotfix-1 + stash, merged staging |
| config.yaml merge | ACFC values kept; staging new keys added (default\_schema, unmapped\_markers, object\_name\_labels, layer\_block, meta\_blank\_values) |
| `env.probe.enabled` | false |
| App stop / start / deploy | deployment `<DEPLOYMENT_ID>` — RUNNING |

Config diff vs staging — ACFC overlays only:

* `databricks.catalog: <CATALOG>`, `schema: <SCHEMA>`, volumes set
* `layout.provider: live`, `endpoint: <ENDPOINT>`
* `conventions.profile: acfc_prx`
* `conventions.default_catalog: {stage: <CATALOG>, standard: <CATALOG>}`
* `metadata.template: iig_v2`
* `playbook.template: main_single`
* `storage.inputs / state / outputs: workspace:/Workspace/Users/<USER>/...`

## 2  API smoke tests

| Test | Outcome |
| --- | --- |
| GET `/api/demo/generation-options` | `acfc_prx`, `iig_v2`, `main_single` — 200 OK |
| output\_parts | `["notebook"]` — `rfc` absent |
| GET `/api/demo/workbooks` | VDDs classified as `vdd` throughout |
| POST `/api/demo/workbook` (pair 1 STTM) | 202, job id=2, <1 s |
| Poll `/api/demo/status` | done — all 7 steps (locate → download → start parser → classify → pair FRD → pair VDD → record) |

Pairing:

* **STTM**: `STTM_Project Eagle_OptumRx_1005789_Accumulators File Ingestion from OptumRx.xlsx`
* **FRD**: `FRD_STG_STD_OptumRx-Project Eagle 1005789_Accumulators file Ingestion from OptumRx (1).docx` — `ticket` rule, score 4
* **VDD**: `VDD_OptumRx_Accumulators.xlsx` — `same_folder` rule

## 3  Generation (framework, acfc\_prx, iig\_v2, VDD attached)

### 3.1  Bug: `KeyError: 'REC_TYP_TRLR'`

The App (and the CLI) crash at `emit/context.py:445`:

```
detail_fields_by_stage[stage_column] for stage_column in spec.natural_key_columns
```

`natural_key_columns` includes `REC_TYP_TRLR` (a Trailer-segment column),
but the lookup dict is built from `spec.detail_segment.fields` only.
Segmented feeds whose natural key references a non-Detail segment column
trigger a `KeyError`.

**Workaround applied**: a runtime monkey-patch drops non-Detail natural key
columns from the lookup, then restores the full set in the emitted context.
No repo code was changed.

### 3.2  Verdict

**FAIL** — 80 flag(s); derivations=FAIL (whitespace in FRD ADLS path),
ruff=NOT RUN, tests=skipped.

### 3.3  Gate checks

| Check | Result | Notes |
| --- | --- | --- |
| ruff | NOT RUN | `No module named ruff` in serverless env |
| debug\_patterns | pass | |
| secrets | pass | |
| test\_per\_module | pass | |
| vdd\_positions | pass | fixed-width positions from VDD |
| dml\_parse\_q1 | pass | tsql dialect |
| dml\_parse\_a2 | pass | |
| dml\_parse\_prod | pass | |
| dml\_row\_counts | pass | PIPELINE\_SCHEDULE 1, FILE\_ADLS 1, ADLS\_DELTA 3, STGSTD 1, FIXED\_WIDTH 3, NOTEBOOK 1, EMAIL 2 |
| sql\_literals | pass | |
| derivations | **FAIL** | whitespace in ADLS paths from FRD (`/Path : <STORAGE>/<LANDING>/...`) |

### 3.4  Grouped flags (80 total)

| Flag group | Count | Summary |
| --- | --- | --- |
| Layer-2 candidate pending | 7 | mock provider stubs; requires engineer review |
| dml\_unassigned | 10 | engineer-assigned IDs (RFC#, connection IDs, etc.) |
| iig\_blank | 7 | IIG template columns left blank for the client |
| field\_unmapped | 6 | `Do Not Map` fields (Adj. Group 01–06) |
| length\_is\_precision | 6 | Decimal(10,2) kept as precision, not byte width |
| width\_from\_sttm\_span | 6 | byte width derived from STTM start/end columns |
| sibling\_type\_mismatch | 6 | AMT\_01–06 Decimal vs string siblings |
| vdd\_missing\_in\_sttm | 6 | VDD Adj. Group fields not in STTM |
| frd\_unstated | 4 | schema/catalog from STTM (FRD unstated) |
| dml\_not\_described | 4 | IIG tabs from §1 conventions only |
| faq\_unanswered | 7 | load-pattern FAQ defaults |
| ddl\_file\_name\_from\_slug | 1 | no feed\_abbreviation in FAQ |
| dml\_unconfirmed | 1 | connection table identifiers |
| frd\_layer\_block | 1 | inline layer block in FRD table |
| file\_pattern\_from\_object\_name | 1 | 3 file patterns from Object Name block |
| frd\_feed\_name\_unstated | 1 | placeholder feed name |
| segments\_from\_sttm | 1 | H/D/T segments from STTM |
| load\_mode\_not\_enforced | 1 | append declared, MERGE-by-file generated |
| rule classified flagged | 1 | recycle rule unconfirmed |
| vdd\_field\_count | 1 | 70 STTM vs 76 VDD fields |
| check\_not\_run | 1 | ruff |
| tests skipped | 1 | |

### 3.5  Environment section

`env.probe.enabled: false` — the probe was never run.
**Unreadable throughout** (as expected): no Unity Catalog or metadata-DB
queries were issued; every object reads `unreadable`. The run proceeds
exactly as without the probe.

### 3.6  Artefact list

| Path | Bytes |
| --- | --- |
| `framework/ADDITION.md` | 3,692 |
| `framework/<FEED>_DDL.txt` | 3,203 |
| `framework/Insert_scripts_config_table_q1.py` | 4,670 |
| `framework/Insert_scripts_config_table_a2.py` | 4,676 |
| `framework/Insert_scripts_config_table_prod.py` | 4,670 |
| `framework/config_inserts.xlsx` | 19,522 |
| `framework/config_inserts_q1.sql` | 41,581 |
| `framework/config_inserts_a2.sql` | 41,585 |
| `framework/config_inserts_prod.sql` | 41,581 |
| `framework/config_rows.xlsx` | 26,005 |
| `ddl/pharmcy.orx_accum_optumrx_dly.standard.sql` | 2,687 |
| `ddl/stg_pharmcy.orx_accum_optumrx_dly.sql` | 2,670 |
| `ddl/stg_pharmcy.orx_accum_optumrx_dly_errors.sql` | 865 |
| `ddl/stg_pharmcy.orx_accum_optumrx_dly_processed_files.sql` | 833 |
| `candidates/candidates.json` | 7,890 |
| `reports/<FEED>.md` | 34,834 |
| **Total** | **240,964** |

## 4  Known issues (v0.6.0)

1. **`KeyError: 'REC_TYP_TRLR'`** — `emit/context.py:445` assumes
   natural\_key\_columns are all Detail-segment columns. Segmented feeds
   with Trailer/Header key columns crash. Needs a fix in `build_context`
   to use all segments when resolving the natural key source columns.

2. **Derivations FAIL** — the FRD's ADLS Location cell contains
   `/Path : <STORAGE>/...` with whitespace around the colon.
   The derivations check flags every path that embeds it.
