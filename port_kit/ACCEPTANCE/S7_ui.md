# S7 — The full UI as a Databricks App (manual checklist, v2)

**Goal:** the FULL user interface of `UI_SPEC.md` v2 running as a Databricks App over the
S1–S6 generator: every route, screen, modal, panel and control. DEMO-DAY checks are numbered
first and must all be green before the LATER checks are attempted; LATER checks are built and
verified afterwards at the same fidelity.

**Frozen prerequisites:** S1–S6 frozen (the last DEMO-DAY check compares downloads against
S1–S3 outputs; the boot summary against S6 case 1).

**Read first:** `UI_SPEC.md` (all parts), `BACKEND_SPEC.md`, then this file. Do not read
`SPEC.md` for the UI; the generator is frozen.

**Setup before the checks.** Materialize the synthetic inputs of `INPUTS.md` on the inputs
Volume: `frd/syn_widget_frd`, `frd/syn_widget_frd_renamed`, `frd/syn_segmented_frd`,
`frd/syn_sensor_frd`; `sttm/syn_widget_sttm.xlsx`, `sttm/syn_widget_sttm_v12.xlsx`,
`sttm/syn_segmented_sttm.xlsx`, `sttm/syn_sensor_sttm.xlsx`; `standards/` holds any two files
(their names are only counted). Place the three acceptance FAQ files on the outputs Volume:
`faq/syn_widget_risk.faq.yaml` (INPUTS.md, all eight answered), `faq/synthetic_segmented_feed.faq.yaml`
and `faq/syn_sensor_pings.faq.yaml` (the ACCEPTANCE S5 inputs); NO file for `syn_gadget_events`.
The configuration carries the SPEC 0.1 acceptance values, the force-mock switch,
`output.mode: framework`, `contracts.pairs` = Pairs A, B, C in that order (`syn_widget_frd` +
`syn_widget_sttm.xlsx`, `syn_segmented_frd` + `syn_segmented_sttm.xlsx`, `syn_sensor_frd` +
`syn_sensor_sttm.xlsx`) and `demo.frd` / `demo.workbook` = Pair A. Start from a fresh browser
session. "Exact" below means the on-screen text equals the quoted text character for character;
`<<run_id>>` is whatever the app minted; `<<family>>` masks the token between `per ` and
`-style spec` in the CONFIRM item text (SPEC 5.3).

The UI cannot be byte-diffed; every check states a click path (or the request) and the exact
expected result. A check passes only when every expected line holds.

---

## Block A — backend-only checks (curl, before any frontend exists)  [DEMO-DAY]

Run against the App URL (or the process on its port). `<<base>>` is the origin. A check names
the request, then the exact expectation.

### A1. Boot populates the mock run with the four synthetic feeds (S6 case 1)

Request: `GET <<base>>/api/feeds`.

Expected: status 200; `mode` = `mock`; `label` = `null`; `failures` = `[]`; `feeds` holds
exactly four entries whose `feed_slug` / `verdict` / number of `flags` are, in this order:
`syn_widget_risk` / `PASS_WITH_FLAGS` / 2; `syn_gadget_events` / `PASS_WITH_FLAGS` / 10;
`synthetic_segmented_feed` / `PASS_WITH_FLAGS` / 9; `syn_sensor_pings` / `PASS_WITH_FLAGS` / 11
(the S6 case 1 lines); each entry's `checks` has four members named `ruff`, `debug_patterns`,
`secrets`, `test_per_module`, all `passed: true`; each `framework.files` equals
`["<<slug>>_stage_table_creation.txt", "<<slug>>_standard_table_creation.txt", "config_rows.xlsx"]`;
`syn_gadget_events.rule_counts` = `{"mappable": 2, "orchestration_config": 1, "notification": 1, "unmapped": 1}`,
`rule_total` 5, `candidate_count` 1, `candidates_pending` 1; `synthetic_segmented_feed.candidate_count` = 4;
`syn_widget_risk.candidate_count` = 0.

### A2. Unknown feed, path escape, binary file, download, report

Requests and expectations, in order:

| Request | Status | Expected body / headers |
|---|---|---|
| `GET /api/feeds/nope` | 404 | `{"detail": "no generated feed named 'nope'"}` |
| `GET /api/feeds/syn_gadget_events/file?path=../../frd.contract.json` | 400 | `{"detail": "path escapes feed directory: ../../frd.contract.json"}` |
| `GET /api/feeds/syn_gadget_events/file?path=framework/missing.txt` | 404 | `{"detail": "file not found: framework/missing.txt"}` |
| `GET /api/feeds/syn_gadget_events/file?path=framework/config_rows.xlsx` | 400 | `{"detail": "not a text file: framework/config_rows.xlsx — use the download route"}` |
| `GET /api/feeds/syn_gadget_events/file?path=framework/syn_gadget_events_stage_table_creation.txt` | 200 | `content` starts with `-- FRD contract: syn_widget_frd sha256 ` and contains the line `-- Load-pattern FAQ: sha256 defaults (no FAQ file) — 2 answered, 6 unknown` |
| `GET /api/feeds/syn_gadget_events/download?path=framework/config_rows.xlsx` | 200 | header `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`; header `Content-Disposition: attachment; filename="config_rows.xlsx"`; the body opens as a workbook with sheets `DATA_FACTORY_PIPELINE_SCHEDULE, ADLS_DELTA_INGESTION_DETAILS, STGDELTA_STDDELTA_INGESTION_DET, DATA_QUALITY_RULES, DATABRICKS_NOTEBOOK_DETAILS, EMAIL_TEMPLATE_CONFIG, ALL_FILES_STATIC_INFORMATION, _provenance, _inputs` in that order |
| `GET /api/feeds/syn_gadget_events/download?path=framework/syn_gadget_events_stage_table_creation.txt` | 200 | `Content-Type: text/plain; charset=utf-8`; the body, after masking the two sha256 spans, equals the ACCEPTANCE S1 case 3 block byte for byte |
| `GET /api/feeds/syn_gadget_events/report` | 200 | `markdown` contains the line `**Verdict: PASS_WITH_FLAGS**` and the ten `- ` bullets of ACCEPTANCE S5 case 1's second feed in order |
| `GET /api/feeds/nope/report` | 404 | `{"detail": "no report for 'nope'"}` |

### A3. Status, availability and the output-mode guard

| Request | Status | Expected |
|---|---|---|
| `GET /api/demo/status` | 200 | `state` `idle`; `stages` `[]`; `mode` `mock`; `label` `null`; `sttm_chosen` `false`; `sttm_workbook` `syn_widget_sttm.xlsx`; `frd_chosen` `false`; `frd_name` `syn_widget_frd`; `frd_warning` `false`; `output_mode` `framework`; `output_modes_available` `["framework"]`; `estimates` `{"calls": 3, "cost_usd": 0.1, "seconds": 20}` |
| `GET /api/demo/live-available` | 200 | `{"available": true, "provider": "mock (locked)", "reason": ""}` |
| `POST /api/demo/output-mode` `{"mode": "bogus"}` | 400 | `{"detail": "unknown output mode 'bogus'"}` |
| `POST /api/demo/output-mode` `{"mode": "framework"}` | 200 | a status whose `output_mode` is `framework` |
| `POST /api/demo/run-live` `{}` | 400 | `{"detail": "live run requires explicit confirm: true (billed API calls)"}` |

### A4. Choosing inputs

| Request | Status | Expected |
|---|---|---|
| `GET /api/demo/workbooks` | 200 | `workbooks` = the four names, each `source` `sttm`, each `selected` `false`, sorted: `syn_segmented_sttm.xlsx`, `syn_sensor_sttm.xlsx`, `syn_widget_sttm.xlsx`, `syn_widget_sttm_v12.xlsx` |
| `POST /api/demo/workbook` `{"name": "nope.xlsx"}` | 404 | `{"detail": "no STTM workbook named 'nope.xlsx' in <<inputs_volume>>/sttm/ or <<outputs_volume>>/uploads/"}` with the two resolved Volume paths |
| `POST /api/demo/workbook` `{"name": "syn_sensor_sttm.xlsx"}` | 200 | the list with `syn_sensor_sttm.xlsx` `selected: true`; a following `GET /api/demo/status` shows `sttm_chosen` `true`, `frd_warning` `true` |
| `GET /api/demo/frd-choices` | 200 | `sttm` `syn_sensor_sttm.xlsx`; `current` `{"label": "syn_widget_frd", "chosen": false}`; `upstream` `[]`; `upstream_error` `not built in this workspace — upstream contracts table`; `local` = `["syn_segmented_frd", "syn_sensor_frd", "syn_widget_frd", "syn_widget_frd_renamed"]` (the FRD contracts carry no extension in INPUTS.md; when materialised with `.contract.json` the names carry it); `no_contract` `[]` |
| `POST /api/demo/frd` `{"kind": "local", "id": "../x"}` | 400 | `{"detail": "invalid contract name '../x'"}` |
| `POST /api/demo/frd` `{"kind": "local", "id": "nope"}` | 404 | `{"detail": "no local contract named 'nope'"}` |
| `POST /api/demo/frd` `{"kind": "other", "id": "x"}` | 400 | `{"detail": "unknown kind 'other'"}` |
| `POST /api/demo/frd` `{"kind": "upstream", "id": "x"}` | 503 | `{"detail": "not built in this workspace — upstream contracts table"}` |
| `POST /api/demo/frd` `{"kind": "local", "id": "syn_sensor_frd"}` | 200 | `{"selected": "syn_sensor_frd", "kind": "local", "feeds": null}`; status now `frd_chosen` `true`, `frd_warning` `false` |
| `DELETE /api/demo/frd` then `DELETE /api/demo/workbook` | 200, 200 | `{"selected": null}`; the workbook list with nothing selected; status back to A3's values |

### A5. Upload validation

| Request (multipart) | Status | Expected |
|---|---|---|
| `kind=sttm`, file `notes.txt` (any bytes) | 400 | `{"detail": "an STTM upload must be a .xlsx workbook, got 'notes.txt'"}` |
| `kind=frd`, file `empty.json` (zero bytes) | 400 | `{"detail": "'empty.json' is empty"}` |
| `kind=frd`, file `bad.json` (body `{}`) | 400 | `detail` starts with `not a valid FRD contract: ` and ends with ` — run the FRD→STTM agent to produce one` |
| `kind=other`, file `x.xlsx` | 400 | `{"detail": "unknown upload kind 'other'"}` |
| `kind=sttm`, file `syn_widget_sttm.xlsx` (the Pair A workbook bytes) | 201 | `{"stored": "syn_widget_sttm.xlsx", "kind": "sttm", "selected": true}`; `GET /api/demo/workbooks` now lists the name once (source `sttm` — the inputs copy wins the dedupe) and `selected: true`; the file exists at `<<outputs_volume>>/uploads/syn_widget_sttm.xlsx` |
| `kind=frd`, file `syn_widget_frd.json` (the Pair A FRD bytes) | 201 | `{"stored": "syn_widget_frd.contract.json", "kind": "frd", "selected": true}`; status `frd_name` `syn_widget_frd.contract.json`, `frd_chosen` `true` |

Clean up: `DELETE /api/demo/frd`, `DELETE /api/demo/workbook`, remove the two uploaded files.

### A6. Inspect: the two failing pairs stop loudly (Pair E, Pair D)

| Requests | Status | Expected |
|---|---|---|
| `POST /api/demo/inspect` with nothing chosen | 400 | `{"detail": "no STTM workbook chosen — choose one first"}` |
| choose `syn_widget_sttm.xlsx` + local FRD `syn_widget_frd_renamed`; `POST /api/demo/inspect` | 400 | `detail` exact: `extracting workbook — sheet 'MAPPING-SYN_GADGET_EVENTS' (stage table 'syn_gadget_events') matches 0 FRD feeds ['Syn Widget Risk', 'Syn Gadget Events']; expected exactly one whose stage_target.tables contains it` |
| choose `syn_widget_sttm_v12.xlsx` + local FRD `syn_widget_frd`; `POST /api/demo/inspect` | 400 | `detail` exact, two lines: `resolving contracts — contract mismatch for feed 'syn_gadget_events':` newline `  - recycle window disagrees: FRD text says 10 days, STTM spec says 12 days` |

### A7. Inspect Pair A and drive the FAQ

| Requests | Status | Expected |
|---|---|---|
| choose `syn_widget_sttm.xlsx` + local FRD `syn_widget_frd`; `POST /api/demo/inspect` | 200 | `contract_file` `syn_widget_sttm.contract.json`; `summary` starts with `2 feed(s): syn_widget_risk (`; `feeds` = two rows: `syn_widget_risk` / `["stg_syn.syn_widget_risk"]` / `syn.syn_widget_risk` / 1 and `syn_gadget_events` / `["stg_syn.syn_gadget_events", "stg_syn.syn_gadget_events_recycle"]` / `syn.syn_gadget_events` / 5; `faq.syn_gadget_events.file_present` `false`, its `counts` `{"from_contract": 2, "answered_here": 0, "unanswered": 6}`, its `load_mode` question `{"value": "truncate_and_load", "source": "contract", "evidence": "stage_target.load_strategy: \"Truncate and Load\"", "prefilled": true}`, its `load_frequency` question value `weekly`, evidence `Weekly Monday 8 PM`; `faq.syn_widget_risk.file_present` `true`, counts `{"from_contract": 0, "answered_here": 8, "unanswered": 0}` |
| `GET /api/demo/faq/nope` | 404 | `{"detail": "no inspected feed named 'nope' — inspect the pair first"}` |
| `PUT /api/demo/faq/syn_gadget_events` `{"answers": {"is_master_file": {"value": "no", "source": "engineer"}}}` | 200 | `saved` `true`; `file` `syn_gadget_events.faq.yaml`; `message` `Saved syn_gadget_events.faq.yaml`; `form.counts` `{"from_contract": 2, "answered_here": 1, "unanswered": 5}`; the file exists at `<<outputs_volume>>/faq/syn_gadget_events.faq.yaml` and reads `schema_version: 1` then a mapping `is_master_file` with `value: "no"` (quoted) and `source: engineer` |
| `PUT /api/demo/faq/syn_gadget_events` `{"answers": {"load_frequency": {"value": "weekly", "source": "frd"}}}` | 400 | `{"detail": "answer 'load_frequency' with source 'frd' needs evidence"}` |
| `PUT /api/demo/faq/syn_gadget_events` `{"answers": {"colour": {"value": "x", "source": "engineer"}}}` | 400 | `{"detail": "unknown FAQ key 'colour'"}` |
| `PUT /api/demo/faq/syn_gadget_events` `{"answers": {}}` | 200 | `saved` `false`; `file` `null`; `message` `No answers set — the generator will use defaults and flag every question`; the file no longer exists |

### A8. A live (mock-locked) run of Pair A, its stages and its directory

Requests: with Pair A still chosen, `POST /api/demo/run-live` `{"confirm": true}`; then
`GET /api/demo/status` every second until `state` is `done` or `failed`.

Expected: the POST answers 200 with `state` `running` and `stages` `[]`; a second
`POST /api/demo/run-live` `{"confirm": true}` fired at once answers 409
`{"detail": "a live demo run is already in progress"}` (if the run already finished, repeat
the pair once more and fire the two POSTs back to back); the final status has `state` `done`,
`error` `null`, `last_run_label` = `demo_` + 15 characters, and `stages[].stage` exactly, in
order: `extracting workbook`, `resolving contracts`, `syn_widget_risk: compiling rules`,
`syn_widget_risk: Layer-2 reasoning`, `syn_widget_risk: emitting code`, `syn_widget_risk:
framework artefacts`, `syn_widget_risk: gate`, `syn_gadget_events: compiling rules`,
`syn_gadget_events: Layer-2 reasoning`, `syn_gadget_events: emitting code`,
`syn_gadget_events: framework artefacts`, `syn_gadget_events: gate`, `publishing results`;
the first stage's `detail` is `syn_widget_sttm.xlsx → STTM mapping contract (FRD:
syn_widget_frd)`, the second's `syn_widget_frd ⋈ extracted contract`, the last's `2 feed(s),
0 failure(s)`; `GET /api/feeds` now answers `mode` `live`, `label` = that run id, two feeds
(`syn_widget_risk` 2 flags, `syn_gadget_events` 10 flags).

Then list `<<outputs_volume>>/runs/<<run_id>>/`. Expected entries: `frd.contract.json`
(byte-identical to `<<inputs_volume>>/frd/syn_widget_frd`), `run_meta.json` reading
`{"frd_label": "syn_widget_frd", "sttm_workbook": "syn_widget_sttm.xlsx", "output_mode": "framework"}`,
`extracted_sttm.contract.json`, `faq/syn_widget_risk.faq.yaml` (and no
`faq/syn_gadget_events.faq.yaml`), `syn_widget_risk/framework/` and
`syn_gadget_events/framework/` each with the three files, `syn_gadget_events/candidates/candidates.json`
(one entry, `provider` `mock`, `grounded` `true`), no `syn_widget_risk/candidates/`,
`reports/syn_widget_risk.md`, `reports/syn_gadget_events.md`.

### A9. A failed run leaves a directory without results

Requests: choose `syn_widget_sttm_v12.xlsx` + `syn_widget_frd`; `POST /api/demo/run-live`
`{"confirm": true}`; poll until terminal.

Expected: `state` `failed`; `stages` = the first two only; `error` exact, two lines:
`ContractMismatchError: contract mismatch for feed 'syn_gadget_events':` newline
`  - recycle window disagrees: FRD text says 10 days, STTM spec says 12 days` (the type name
before the colon is whatever the S1 resolver raises — record it if it differs, the message
must not); `error_hint` `null`; `GET /api/feeds` still shows the A8 run (nothing adopted);
the new run directory holds `frd.contract.json`, `run_meta.json`, `extracted_sttm.contract.json`
and nothing else.

### A10. Routes that are not built yet say so, and the loaded run's decisions are scoped

| Request | Status | Expected |
|---|---|---|
| `GET /api/demo/source-files` | 503 | `{"detail": "not built in this workspace — source files panel"}` |
| `GET /api/demo/input-requirements` | 503 | `{"detail": "not built in this workspace — input requirements check"}` |
| `GET /api/demo/governance-checks` | 503 | `{"detail": "not built in this workspace — governance checks"}` |
| `GET /api/databricks/documents` | 503 | `{"detail": "not built in this workspace — raw document volumes"}` |
| `GET /api/databricks/publish-target` | 200 | `available` `false`; `reason` `not built in this workspace — volume publish` |
| `GET /api/replay/sets` | 200 | `{"sets": []}` |
| `GET /api/demo/input-documents` | 200 | `documents[0]` has `kind` `reference_documents`, `present` listing the two files placed in `standards/` by name, `missing` = the rest of the configured expected list; `documents[1]` = `{"kind": "frd", "matches": [], "stand_in": "syn_widget_frd"}` |
| `GET /api/demo/metadata-sheet` | 200 | `run_label` = the A8 run id; `tabs` keys in order `DATA_FACTORY_PIPELINE_SCHEDULE`, `ADLS_DELTA_INGESTION_DETAILS`, `STGDELTA_STDDELTA_INGESTION_DET`, `DATA_QUALITY_RULES`, `DATABRICKS_NOTEBOOK_DETAILS`, `EMAIL_TEMPLATE_CONFIG`, `ALL_FILES_STATIC_INFORMATION`; `ALL_FILES_STATIC_INFORMATION.rows` has two rows (one per feed); the `syn_gadget_events` row's `values.FILE_NAME` `gadget_events_CCYYMMDD_HHMM.psv`, `values.INVENTORY_ID` `""`, `badges.INVENTORY_ID.badge` `needs_template`, `badges.FILE_NAME.badge` `from_frd` |

---

## Block B — DEMO-DAY screen checks (browser)

### 1. Cold start lands on a populated dashboard in MOCK

Click path: open the app URL (after a fresh boot; the A-block selections do not matter).

Expected: sidebar brand `CodeGen · Data Engineer Agent`, sub-line `Contracts → Databricks
pipelines`, badge exact `MOCK`; nav rows `Dashboard`, `Run modes` (hint `live · replay`),
`Demo mode` (hint `guided tour`); under `FEEDS` four rows `syn_widget_risk`,
`syn_gadget_events`, `synthetic_segmented_feed`, `syn_sensor_pings`, each with an amber
verdict dot; footer `Layer 1 deterministic (Jinja2) · Layer 2 review-only candidates.` /
`Gate verdict computed in code, never by judgment.`; no mode banner; `h1` `Generation gate`;
tiles: `FEEDS` `4` / `from configured contract pairs`; `PASS` `0` / `4 with flags · 0 failed`;
`RULES COMPILED` `8/15` / `deterministic (Layer 1 + orchestration)`; `PENDING REVIEW` `6` /
`Layer-2 candidates awaiting an engineer`; four feed cards, each chip `PASS WITH FLAGS`.

### 2. The feed card is the run's numbers

Click path: none (dashboard).

Expected on the `syn_gadget_events` card: meta line `SynVendor Analytics | Region 1, Region 2 |
PSV`; the rule strip has four segments; counts row `mappable 2`, `orchestration 1`,
`notification 1`, `unmapped → L2 1` in that order; foot `3/5 rules compiled
deterministically` and `3 files · 1 pending review`. On the `synthetic_segmented_feed` card:
meta ends ` · segmented`; foot `4/6 rules compiled deterministically` and `3 files · 4 pending
review`.

### 3. The framework panel lists the three files and the blank IDs

Click path: scroll to `Framework artefacts (Option B)`.

Expected: hint `config rows are the approval artefact; DDL + inserts are add-ons to
<<client>>'s master notebook, applied only after approval` with the configured client short
name; the `syn_gadget_events` block reads `DATA_FACTORY_PIPELINE_SCHEDULE 2 ·
ADLS_DELTA_INGESTION_DETAILS 1 · STGDELTA_STDDELTA_INGESTION_DET 1 · DATA_QUALITY_RULES 3 ·
DATABRICKS_NOTEBOOK_DETAILS 2 · EMAIL_TEMPLATE_CONFIG 2 · ALL_FILES_STATIC_INFORMATION 1 ·
83/285 derived`; three buttons `syn_gadget_events_stage_table_creation.txt`,
`syn_gadget_events_standard_table_creation.txt`, `config_rows.xlsx`; the line begins
`Framework-assigned IDs left blank: PIPELINE_ID, PARENT_PIPELINE_ID, GROUP_ID, OBJECT_ID,
INVENTORY_ID, SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, TGT_CONNECTION_ID,
CLUSTER_DETAILS_ID, DATABRICKS_WORKSPACE_URL, DATABRICKS_WORKSPACE_SECRET, DATABRICKS_CLUSTERID`
and ends `— the agent never invents them.`

### 4. The metadata sheet preview: tabs in workbook order, one dot per cell, blanks blank

Click path: scroll to `For <<client>>'s framework: metadata sheet preview`; click tab
`ALL_FILES_STATIC_INFORMATION`.

Expected: the tab strip reads, in order, `DATA_FACTORY_PIPELINE_SCHEDULE`,
`ADLS_DELTA_INGESTION_DETAILS`, `STGDELTA_STDDELTA_INGESTION_DET`, `DATA_QUALITY_RULES`,
`DATABRICKS_NOTEBOOK_DETAILS`, `EMAIL_TEMPLATE_CONFIG`, `ALL_FILES_STATIC_INFORMATION`, each
with a row count; the active table's header row is verbatim (`INVENTORY_ID`, `OBJECT_ID`,
`FILE_NAME`, `DESCRIPTION`, `LOB`, … `CREATED_DATE`, `UPDATED_DATE`); the `syn_gadget_events`
row shows `FILE_NAME` `gadget_events_CCYYMMDD_HHMM.psv`, `DESCRIPTION` `Syn Gadget Events`,
`LOB` `Region 1, Region 2`, and `INVENTORY_ID` / `OBJECT_ID` empty (not `NULL`); hovering the
`INVENTORY_ID` cell's dot shows `NEEDS CLIENT TEMPLATE`, the `FILE_NAME` dot shows `from FRD`;
every cell has exactly one dot; the footer starts `<<d>> of <<t>> values derived from
documents`; a `Download .xlsx` button; the disclaimer starts `Display only — the reviewed sheet
is the approval artifact.`

### 5. Feed detail: Overview panels and the HITL row

Click path: sidebar `syn_gadget_events`.

Expected: mono `h1` `syn_gadget_events`; chip `PASS WITH FLAGS`; sub-line `SynVendor
Analytics · Region 1, Region 2 · PSV`; tabs exact `Overview`, `Rules 5`, `Layer-2 review 1`,
`Generated code 3`, `Report` — and NO `Notebook` tab; panel `Gate checks` (hint `verdict
computed in code — never by judgment`) with four green rows `ruff` / `ruff clean`,
`debug_patterns` / `no debug statements`, `secrets` / `no hardcoded secrets`,
`test_per_module` / `every pipeline module has a test file`; panel `Flags — needs a human`
(hint `10 open`) whose rows are the ten flag texts of A2 in order, the ninth row carrying the
tag `PENDING ENGINEER APPROVAL` on an amber background; panel `Source contracts` with `FRD`
`syn_widget_frd` + a `sha256 ` line, `STTM` `STTM mapping contract extracted from
syn_widget_sttm.xlsx` + a `sha256 ` line, `File patterns` `gadget_events_CCYYMMDD_HHMM.psv`,
`Delimiter` `"|"`, `Lines of business` `Region 1, Region 2`, `Frequency` `Weekly Monday 8
PM`; panel `Target tables` with `Stage` `stg_syn.syn_gadget_events`, `Standard`
`syn.syn_gadget_events`, `Errors` `stg_syn.syn_gadget_events_errors`, `Recycle`
`stg_syn.syn_gadget_events_recycle`, `Processed files` `stg_syn.syn_gadget_events_processed_files`;
panel `Load semantics` present.

### 6. Rules tab

Click path: tab `Rules`.

Expected: panel title `Validation rules — verbatim from the FRD`; five rows numbered 1–5; row 3
badge `notification`, rule `Email notification should be sent to the Support team whenever
there is an issue.`, feature `—`; row 4 badge `unmapped → L2`, rule `Column GADGET_NM is
mapped to GADGET_NAME in the standard layer.`, grounding in curly quotes equal to the rule
text; row 5 badge `mappable`, feature `recycle`.

### 7. Layer-2 review tab: the candidate card (display)

Click path: tab `Layer-2 review`.

Expected: the intro paragraph starting `These rules could not be compiled deterministically`;
one card: title `Rule: “Column GADGET_NM is mapped to GADGET_NAME in the standard layer.”`;
pills `provider: mock`, `✓ grounded`, badge `mappable`; rationale exact `Mock provider:
deterministic stand-in generated without model access, grounded on the rule text alone.
Requires engineer review.`; a code box whose first line is `# LAYER-2 CANDIDATE (mock
provider) — feed syn_gadget_events`; one citation `“Column GADGET_NM is mapped to GADGET_NAME
in the standard layer.”`; buttons `✓ Approve`, `✗ Reject`; status `Awaiting engineer
decision`. (Clicking is LATER check L3.)

### 8. Generated code tab: the framework group, binary as download

Click path: tab `Generated code`.

Expected: the tree has one group header `FRAMEWORK` with three entries
`syn_gadget_events_stage_table_creation.txt`, `syn_gadget_events_standard_table_creation.txt`,
`config_rows.xlsx`; the first `.txt` is open with the path bar
`framework/syn_gadget_events_stage_table_creation.txt` and a mono body whose first line is
`-- FRD contract: syn_widget_frd sha256 ` + 64 hex characters and which contains the lines
`--stg_syn.syn_gadget_events` and `--stg_syn.syn_gadget_events_recycle`, scrolling
horizontally without wrapping; hovering `config_rows.xlsx` shows `binary — download` and
clicking it downloads the workbook.

### 9. Report tab

Click path: tab `Report`.

Expected: a rendered document whose first heading is `Generation report — syn_gadget_events`,
with headings `Contracts`, `Inputs (three-input model)`, `Files emitted`, `Validation rules`,
`Layer-2 candidates (review required — never auto-merged)`, `Gate`, then a `Flags:` list of
ten items and the bold line `Verdict: PASS_WITH_FLAGS`, then `Framework output (Option B)`.

### 10. Run modes: Card B opens on "none chosen" with the mock lock

Click path: sidebar `Run modes`.

Expected: `h1` `Run modes`; subtitle `Pick how the results you're about to walk through get
produced. Both modes end on the same dashboard — and the same human review queue.`; Card A
head `Replay a recorded run` badge `REPLAY`, body `No replay sets tracked under
fixtures/replay/.`; Card B head `Generate a Pipeline` badge exact `MOCK — provider locked`;
`STTM workbook: none chosen`; `Clear` disabled with tooltip `Nothing chosen yet`; `FRD
contract: syn_widget_frd (demo golden — default)`; `Reset` disabled with tooltip `Already on
the demo golden default`; NO `Source files this run will read` section; the metadata sheet
preview present; `Step 1.5` hint present with `Inspect pair` disabled (tooltip `Choose an STTM
workbook first`); `Output` toggles with `Framework artefacts` active and `Notebook` / `Both`
disabled (tooltip `Option A emitter not built in this workspace (SPEC L16)`); `Input
documents` card `Some reference documents are missing` with two `✓` rows and the rest `☐`;
NO `Input requirements check` and NO `Reference-architecture checks` sections; `Known input
gaps` call-out with `Provide…`; the button `Generate from this STTM…` disabled with tooltip
`Choose an STTM workbook first`; `Past live runs` reading either `No past live runs on this
machine yet.` or the A8/A9 runs (the A9 run carries `failed — not loadable`).

### 11. The chooser lists the Volume folders and keeps itself open

Click path: `Choose STTM…`.

Expected: title `Choose an STTM workbook`; the upload row with `Upload STTM (.xlsx)…` and
`Upload FRD contract (.json)…` and the note `Uploads land in <<outputs_volume>>/uploads/ on
the outputs Volume.`; four workbook rows in sorted order, each with the chip `sttm`; NO
`Databricks volumes unavailable.` call-out and NO `STTM workbooks in` section; `FRD for this
run — currently syn_widget_frd (demo golden — default).` followed by `FRD→STTM agent table
unavailable: not built in this workspace — upstream contracts table`; four rows chipped
`local contract`; footer `Cancel`. Click `syn_widget_sttm.xlsx`: the modal STAYS open, the row's
chip now reads `sttm · selected`, the footer reads `Done`. Click `syn_widget_frd` under `FRD
for this run`, then `Done`.

Expected after closing: `STTM workbook: syn_widget_sttm.xlsx`; `FRD contract: syn_widget_frd`
without the default hint; no warning pill; `Inspect pair` and `Generate from this STTM…`
enabled.

### 12. A pair that does not match warns, never blocks

Click path: `Choose FRD…`, pick `syn_sensor_frd`, `Done`.

Expected: the amber pill `These names do not look like a pair — the FRD feeds must name the
workbook's stage tables (SPEC 1.4). Inspect anyway; a mismatch fails loudly.`; both buttons
stay enabled. Click `Inspect pair`: a red banner whose first line starts `extracting workbook
— ` and the second line exact `The workbook could not be read as a mapping document; nothing
was guessed. Fix the sheet the message names and inspect the pair again.` Then `Choose
FRD…`, pick `syn_widget_frd`, `Done`: the pill disappears.

### 13. Pair D disagrees at inspection

Click path: `Choose STTM…`, pick `syn_widget_sttm_v12.xlsx`, `Done`; `Inspect pair`.

Expected: red banner line 1 exact, on two lines: `resolving contracts — contract mismatch for
feed 'syn_gadget_events':` / `  - recycle window disagrees: FRD text says 10 days, STTM spec
says 12 days`; line 2 exact `The FRD and the STTM disagree; nothing here is guessed. Fix the
document that is wrong and inspect the pair again.`; no feed tabs; `Generate from this
STTM…` still enabled (the run would fail the same way — check 18 covers it).

### 14. Pair A inspects into two feeds and the FAQ shows prefills and defaults

Click path: `Choose STTM…`, pick `syn_widget_sttm.xlsx`, `Done`; `Inspect pair`; tab
`syn_gadget_events`.

Expected: `Extracted: syn_widget_sttm.contract.json — 2 feed(s)`; two rows exact:

| feed_id | stage tables | standard | rules |
|---|---|---|---|
| syn_widget_risk | stg_syn.syn_widget_risk | syn.syn_widget_risk | 1 |
| syn_gadget_events | stg_syn.syn_gadget_events, stg_syn.syn_gadget_events_recycle | syn.syn_gadget_events | 5 |

On tab `syn_gadget_events`: row `load_mode` preselected `truncate_and_load`, source `contract`
(read-only), evidence `stage_target.load_strategy: "Truncate and Load"`, caption `prefilled
from the contract — change the value to override it`; row `load_frequency` preselected
`weekly`, source `contract`, evidence `Weekly Monday 8 PM`; the other six rows `(unanswered)`
with captions `default: unknown`, `default: none`, `default: unknown`, `default: yes`,
`default: none`, `default: none` in that order; `Companions (not questions, never flagged):`
with `has_header` (caption `companion — sets HEADER_FLAG`) and `has_trailer`; summary exact `2
answered by the contract · 0 answered here · 6 unanswered → 6 flags`. Tab `syn_widget_risk`
(its file exists): every row answered, summary `0 answered by the contract · 8 answered here ·
0 unanswered → 0 flags`.

### 15. Answers are saved as the generator's FAQ file; an untouched feed gets no file

Click path: tab `syn_gadget_events`; set `is_master_file` `no` / `engineer`; `Save answers`;
then set it back to `(unanswered)`; `Save answers`.

Expected: after the first save the line `Saved syn_gadget_events.faq.yaml` and the summary `2
answered by the contract · 1 answered here · 5 unanswered → 5 flags`; after the second save
the line `No answers set — the generator will use defaults and flag every question` and the
summary back to check 14's; `<<outputs_volume>>/faq/` holds no `syn_gadget_events.faq.yaml`.

### 16. The cost modal under the mock lock, then the run and its stages

Click path: `Generate from this STTM…`.

Expected: title `Generate a pipeline from this STTM?`; `Input: syn_widget_sttm.xlsx`; the
sentence `This deployment is **locked to the mock provider** — the run makes **zero model
calls** (deterministic mock candidates).`; `Output is isolated to its own run directory; the
tracked replay fixtures and default output are never touched.`; the paragraph starting
`Client documents in play:` (the FRD is explicitly chosen); buttons `Confirm — run live` /
`Cancel`. Click `Confirm — run live`.

Expected: the button reads `Live run in progress…`; every control of Step 1 and Step 1.5 is
disabled; the hint `Running — stages appear as they start:`; the stage list grows, the last
entry marked `⋯`, earlier ones `✓`; at the end every entry is `✓`, the list is exactly the
thirteen A8 stage names in order with the first two details and `publishing results — 2
feed(s), 0 failure(s)`; the hint `Last live run completed.`; the button `View results →`.

### 17. View results lands on the LIVE dashboard with the run label

Click path: `View results →`.

Expected: the dashboard; sidebar badge `LIVE · <<run_id>>`; a red-tinted banner `LIVE —
generated now; each candidate card names its provider · <<run_id>>`; tiles `FEEDS` `2`,
`PASS` `0` / `2 with flags · 0 failed`, `RULES COMPILED` `3/6`, `PENDING REVIEW` `1`; cards
`syn_widget_risk` and `syn_gadget_events`; the framework panel and metadata preview now show
these two feeds; the metadata preview's `run_label` is the run id (the download names the
workbook `metadata_sheet_<<run_id>>.xlsx`).

### 18. A failing run is said, not hidden

Click path: `Run modes`; `Choose STTM…`, pick `syn_widget_sttm_v12.xlsx`, `Done`; `Generate
from this STTM…`; `Confirm — run live`.

Expected: hint `Last live run FAILED — nothing was published.`; a red banner with the
two-line mismatch text of A9 verbatim; the stage list shows `extracting workbook` and
`resolving contracts`, both `✓`; no `View results →`; the sidebar badge still reads `LIVE ·
<<check-17 run id>>`; `Past live runs` lists the failed run with `failed — not loadable` and
`no results produced`, its `Load` disabled.

### 19. Segmented pair: CONFIRM items ride the same review flow

Click path: `Choose STTM…`, pick `syn_segmented_sttm.xlsx`; under `FRD for this run` pick
`syn_segmented_frd`; `Done`; `Inspect pair`; `Generate from this STTM…`; `Confirm — run
live`; `View results →`; sidebar `synthetic_segmented_feed`; tab `Layer-2 review`.

Expected: the inspection table lists one feed with three stage tables; the run's `publishing
results — 1 feed(s), 0 failure(s)`; on the review tab four cards: the first two lead with the
amber pill `CONFIRM — document-derived, cited`, their titles begin `CONFIRM — positional
header/detail identification per <<family>>-style spec:` and `CONFIRM — audit columns per
segment follow the STTM:`, their pills read `source: `, each shows one citation — the first
names the STTM row and contains `******`, the second begins `FRD rule:`; their approve buttons
read `✓ Confirm` and their status `Soft confirmation — the run proceeds; a source-team answer
closes it`; cards three and four are Layer-2 cards for `Populate file type and source file
name fields in the target tables.` and `Header, Detail and Trailer data should be mapped to
respective HDR, DTL and TRL tables.`; the Overview's flags panel reads `9 open`; the Generated
code `.txt` preview shows four `CREATE OR REPLACE TABLE` statements in the stage file and
three in the standard file.

### 20. Stage-only pair: classified-flagged rules and the empty standard file

Click path: `Run modes`; chooser: `syn_sensor_sttm.xlsx` + `syn_sensor_frd`; `Done`;
`Inspect pair` (leave the FAQ untouched); generate; `View results →`; sidebar
`syn_sensor_pings`.

Expected: the inspection standard column reads `none — stage-only`; Overview: `Target
tables` → `Standard` italic `none — stage-only feed (load AS-IS)`, `Recycle` italic `no
recycle rule`; flags `11 open` including the rows `rule classified flagged: 'Files are
pipe-delimited.' — MISMATCH: resolved delimiter is ','` and `rule classified flagged:
'Invalid records will be moved to the Recycle table.' — FRD states a recycle rule but the
STTM has no structured recycle spec for this feed — unconfirmed attribution; no recycle module
generated` and the HITL row `Layer-2 candidate pending engineer approval: 'If the SENSOR_ID
column is NULL, then we are rejecting the record and moving it to the reject table.'`; Rules
tab rows 1–2 badge `flagged`, row 3 `unmapped → L2`; Generated code:
`syn_sensor_pings_standard_table_creation.txt` is the six-line banner followed by the single
line `-- No standard-layer table for this feed (stage-only load).`

### 21. Regenerate-all from LIVE asks first, and lands back in MOCK

Click path: `Dashboard`; `Generate all feeds`.

Expected: modal `Replace the current LIVE results?` with body `This replaces the current live
results (<<run_id>>) with a fresh **mock** run. You can reload them afterwards from the Run
modes page.`; `Cancel` closes it with nothing changed; `Continue — run mock` runs and the
dashboard returns to check 1's state (badge `MOCK`, four feeds, no banner).

### 22. Final — the downloaded files match the frozen S1–S3 outputs

Click path: `Run modes`; chooser: `syn_widget_sttm.xlsx` + `syn_widget_frd`; `Done`; `Inspect
pair`; on tab `syn_widget_risk` confirm the eight answers are those of INPUTS.md (the file
placed in setup) and leave `syn_gadget_events` untouched; generate; `View results →`; in the
framework panel click the three buttons of `syn_gadget_events`, then the stage file button of
`syn_widget_risk`; also click `Download .xlsx` under the metadata preview.

Expected: `syn_gadget_events_stage_table_creation.txt`, after masking the two sha256 spans,
equals the S1 case 3 block byte for byte; `syn_gadget_events_standard_table_creation.txt`,
masked the same way, equals the S2 case 1 block; `config_rows.xlsx` tabs
`ALL_FILES_STATIC_INFORMATION` and `ADLS_DELTA_INGESTION_DETAILS` are cell-exact (value and
badge) against the S3 case 3 dump and the remaining five tabs against the S4 case 3 dump when
S4 is frozen; `syn_widget_risk_stage_table_creation.txt`, masked, equals the S1 case 1 block;
the three `syn_gadget_events` downloads are byte-identical to the files under
`<<outputs_volume>>/runs/<<run_id>>/syn_gadget_events/framework/`; the metadata workbook's
`ALL_FILES_STATIC_INFORMATION` sheet holds the two feeds' rows with the same values as the
per-feed workbooks.

---

## Block C — LATER checks (after every DEMO-DAY check is green)

### L1. Reset decisions clears only the loaded run

Click path: dashboard `Reset decisions`.

Expected: modal `Reset review decisions?`, body `Clears every approve/reject recorded for the
currently loaded run (mock state). Candidates return to **pending engineer approval**.
Decisions made under other runs are untouched.` (the parenthesis carries the run id under
LIVE); `Reset — clean slate` → `Resetting…` → the `PENDING REVIEW` tile returns to the full
count; `<<outputs_volume>>/state/decisions.json` no longer has the current run key while other
keys remain.

### L2. Feed detail Regenerate

Click path: `syn_gadget_events` → `Regenerate`.

Expected: `Generating…` then the page reloads with the same verdict; the sidebar badge is
`MOCK`; from LIVE the regenerate replaces the loaded run with the mock run for every
configured pair (the reference behaviour).

### L3. Candidate decisions and the toggle semantics

Click path: `syn_gadget_events` → `Layer-2 review` → `✓ Approve`.

Expected: the button gets a tinted fill; status `Marked approved — merge into generated code
remains a manual (v2) step`; the dashboard's `PENDING REVIEW` tile drops by one; click
`✓ Approve` again → status `Awaiting engineer decision` and the tile goes back up; `✗ Reject`
→ `Marked rejected — …`; on a CONFIRM card `✓ Confirm` → `Marked approved — recorded in the
decision store`; the decisions file holds `{"version": 2, "runs": {"mock": {"syn_gadget_events":
{"0": {"decision": "rejected", "note": null}}}}}` after the last click.

### L4. Demo mode: six steps, arrow keys, dots, the human decision last

Click path: sidebar `Demo mode`; press → five times; press ← once; click the sixth dot.

Expected: kicker `GUIDED DEMO`; titles in order `What this is`, `Contracts go in`, `Layer 1 —
deterministic`, `The safety gate`, `What comes out`, `Layer 2 — the human decision`; counter
`1 / 6` … `6 / 6`; `← Back` disabled on step 1; `Finish → dashboard` on step 6; step 1's fact
`Right now: 4 feeds generated, 8/15 contract rules compiled deterministically. …`; step 2's
running example `synthetic_segmented_feed` (the first feed with candidates) with the segmented
clause; step 5 shows the empty state `No notebook for synthetic_segmented_feed — this run
produced framework artefacts only (Option B). The notebook appears when a run uses output mode
Notebook or Both.` and the Option B fact line; step 6 lists four quote blocks with approve /
reject and the closing fact `4 of 4 candidates still pending for synthetic_segmented_feed —
the full queue lives on the Layer-2 review tab`.

### L5. Past live runs reload their own pair

Click path: `Run modes` → `Past live runs` → `Load` on the check-19 run.

Expected: `Loading…`, then the dashboard in `LIVE · <<that run id>>` with one feed
`synthetic_segmented_feed`, 9 flags, four candidates; the feed's `Source contracts` FRD is
`syn_segmented_frd`.

### L6. Replay sets

Setup: place a set under `<<inputs_volume>>/replay/replay_set_20260101/synthetic_segmented_feed/candidates.json`
(the check-19 run's file) and the loader built.

Click path: `Run modes` → Card A → `Load`.

Expected: the row reads `replay_set_20260101` / `recorded 2026-01-01 · 1 feeds`; after `Load`
the dashboard shows badge `REPLAY · replay_set_20260101` and the blue banner `REPLAY —
recorded live run · replay_set_20260101`; the candidate cards carry the recorded provider name.

### L7. Output-mode Notebook and the Option A surfaces

Setup: an Option A emitter present (`output_modes_available` lists `notebook`).

Click path: `Run modes` → `Output` → `Notebook`; run Pair A; open `syn_gadget_events`.

Expected: the tab strip gains `Notebook`; the Notebook tab's panel title `syn_gadget_events.ipynb`
with hint `the whole pipeline as one runnable Databricks notebook — the module files stay
canonical`; Generated code groups `PIPELINE`, `DDL`, … with the first `pipeline/` file open;
demo step 5 renders the notebook in the 46vh box.

### L8. Source files, requirements and governance sections appear when their routes are built

Expected on `Run modes` once the three display routes answer 200: `Source files this run will
read` table with one row per feed of the effective FRD, `SYNTHETIC` pills with the two
tooltips of UI_SPEC §4.2, the `In the Databricks workspace` block with a `$ databricks fs ls
dbfs:/Volumes/…` command line; `Input requirements check` with eleven rows and the four pill
kinds; `Reference-architecture checks` with the three pill kinds flipping from `awaiting a
run` after a run.

### L9. Chooser volumes sections, 502 versus 503

Expected once the raw-document volumes seam exists: a 503 hides sections 4–6; a 502 shows
`**Databricks volumes unavailable.** <<message>>` with `Retry`; `Fetch` / `Re-fetch` /
`Fetched ✓` states as UI_SPEC §2.4.4; the companion FRD is fetched with a paired STTM.

### L10. Publish panel

Expected once the publish route is built: defaults pre-filled; the policy line `Target:
/Volumes/<<c>>/<<s>>/<<v>>/<<feed>>/ · policy: writes only under <<prefix>>*, enforced in
code.`; editing the catalog outside the prefix turns the line amber with `is outside the
writable policy`; `Publish…` → modal `Publish to the workspace?` → `Confirm — publish` →
`Published 4 artifact(s) to <<volume>>: …`; a target outside the prefix answers 400 into the
panel's red banner.

### L11. Every backend detail string reaches the screen unchanged

Click path: any failing action in checks 12, 13, 18 and L10.

Expected: the text on screen equals the `detail` the route returned, character for character.

## If you can't hit this

Compare what is on screen with the quoted text word for word; the first differing word names
the UI_SPEC control or the §4.2 string to re-read. If the difference is inside a generator
message, a file preview or a download, the UI is not at fault: the frozen S1–S6 slice is —
stop and report it rather than editing a frozen file or masking the difference in the UI.
Never paraphrase a generator message, never hide a flag, never preselect a pair, never drop
a screen because its data source is absent — build its empty state.
