# BACKEND_SPEC — the FastAPI process behind UI_SPEC v2

Tables and inline example payloads only. Every route, status code and error string here is
identical to `UI_SPEC.md` Part 3 (that document is the contract the frontend is built on;
this one is the build order for the process behind it). "Generator step" names what the S1–S6
package does, in prose; "SPEC ref" is the section that defines it. Tags: DEMO-DAY routes are
built first and must be green in the S7 curl block before any frontend exists.

Conventions: `<<x>>` variable span; `'<<x>>'` the value in single quotes (repr, SPEC 0);
paths are relative to the two Volumes (`<<inputs_volume>>` read-only, `<<outputs_volume>>`
read-write); every error body is `{"detail": "<<text>>"}`.

## 1. Route table

| Path | Method | Request | Response | Status codes | Error strings (verbatim) | Generator step (prose) | SPEC ref | Tag |
|---|---|---|---|---|---|---|---|---|
| `/api/feeds` | GET | — | `FeedsResponse` | 200 | none; start-up failure is reported inside the body as `failures: [{label: "startup", error: "pipeline unavailable — <<error>>"}]` | none — serves the in-memory run state | — | DEMO-DAY |
| `/api/feeds/{slug}` | GET | — | `FeedDetail` | 200, 404 | `no generated feed named '<<slug>>'` | none | — | DEMO-DAY |
| `/api/generate` | POST | `{"feed_slug": string\|null, "dry_run": bool, "skip_tests": bool}` | `FeedsResponse` | 200, 409, 404 | `config.contracts.pairs is empty — nothing to generate. Restore anonymized contract pairs in config/config.yaml, or load a replay set / past live run instead.` · `no resolved feed matches '<<slug>>'` | the mock run over `contracts.pairs`: extract each `.xlsx` pair member, resolve, per feed compile rules → mock Layer 2 → FAQ → DDL ×2 → IIG workbook → flags/verdict/report; failures scoped per pair / per feed | 1.1–1.8, 2–4, 5.1–5.5 (S1–S5) | DEMO-DAY |
| `/api/feeds/{slug}/file` | GET | `?path=<<relative>>` | `{"path": string, "content": string}` | 200, 404, 400 | `no generated feed named '<<slug>>'` · `path escapes feed directory: <<path>>` · `file not found: <<path>>` · `not a text file: <<path>> — use the download route` | none — reads the Volume copy | 5.5 (report), header table (files) | DEMO-DAY |
| `/api/feeds/{slug}/download` | GET | `?path=<<relative>>` | bytes, `Content-Disposition: attachment; filename="<<name>>"`; media type per §5 | 200, 404, 400 | as above (without the text-file case) | none | — | DEMO-DAY |
| `/api/feeds/{slug}/report` | GET | — | `{"markdown": string}` | 200, 404 | `no report for '<<slug>>'` | none — `reports/<<slug>>.md` | 5.5 | DEMO-DAY |
| `/api/feeds/{slug}/candidates/{index}/decision` | POST | `{"decision": "pending"\|"approved"\|"rejected", "note": string\|null}` | `{"feed_slug", "index", "review": {"decision", "note"}}` | 200, 404 | `no generated feed named '<<slug>>'` · `candidate index <<index>> out of range` | none — decisions store (§2.3); the candidates artifact is never modified | 5.2 (artifact) | LATER |
| `/api/decisions/reset` | POST | — | `FeedsResponse` | 200 | — | none — removes the current run key from the decisions store | — | LATER |
| `/api/demo/inspect` | POST | — | `InspectResponse` | 200, 400, 409 | `no STTM workbook chosen — choose one first` · `cannot inspect while a live run is in progress` · `extracting workbook — <<message>>` · `resolving contracts — <<message>>` | extract the chosen workbook against the effective FRD into a scratch contract; resolve; FAQ prefills per feed as if no file existed, merged with the file on the Volume | 1.1–1.8, 5.4 (messages) (S1) | DEMO-DAY |
| `/api/demo/faq/{slug}` | GET | — | `FaqForm` | 200, 404, 400 | `no inspected feed named '<<slug>>' — inspect the pair first` · `FAQ file <<path>> is not a YAML mapping` · the loader's unknown-key message | the FAQ loader + prefills | 1.8 (S1) | DEMO-DAY |
| `/api/demo/faq/{slug}` | PUT | `{"answers": {"<<question>>": {"value": string, "source": "engineer"\|"frd", "evidence": string\|null}}}` | `FaqSaveResult` | 200, 404, 409, 400 | as GET · `cannot change inputs while a live run is in progress` · `unknown FAQ key '<<key>>'` · `answer '<<question>>' has no value` · `answer '<<question>>' with source 'frd' needs evidence` | writes `faq/<<slug>>.faq.yaml` in the SPEC 1.8 file shape (empty answers → the file is removed) | 1.8 | DEMO-DAY |
| `/api/demo/live-available` | GET | — | `LiveAvailability` | 200 | — | provider selection only | 5.2 (provider selection) | DEMO-DAY |
| `/api/demo/run-live` | POST | `{"confirm": true}` | `DemoStatus` | 200, 400, 409 | `live run requires explicit confirm: true (billed API calls)` · `live run unavailable: <<reason>>` · `a live demo run is already in progress` | the full run on a background thread (§3), one run directory per run | 1.1–1.8, 2–4, 5.1–5.5 | DEMO-DAY |
| `/api/demo/status` | GET | — | `DemoStatus` (+ `output_modes_available`) | 200 | — | none | — | DEMO-DAY |
| `/api/demo/output-mode` | POST | `{"mode": "notebook"\|"framework"\|"both"\|null}` | `DemoStatus` | 200, 400, 409 | `unknown output mode '<<mode>>'` · `cannot change the output mode while a live run is in progress` | none — in-memory override | — | DEMO-DAY (`framework`) / LATER (`notebook`, `both`) |
| `/api/demo/workbooks` | GET | — | `{"workbooks": [{"name", "source", "selected"}]}` | 200 | — | none — lists `sttm/` and `uploads/` | — | DEMO-DAY |
| `/api/demo/workbook` | POST | `{"name": string}` | `{"workbooks": [...]}` | 200, 404, 409 | `no STTM workbook named '<<name>>' in <<inputs_volume>>/sttm/ or <<outputs_volume>>/uploads/` · `cannot change the STTM while a live run is in progress` | none | — | DEMO-DAY |
| `/api/demo/workbook` | DELETE | — | `{"workbooks": [...]}` | 200, 409 | as above | none | — | DEMO-DAY |
| `/api/demo/frd-choices` | GET | — | `FrdChoicesResponse` | 200 | — (`upstream_error` is inline) | none — lists `frd/` + `uploads/` contracts and `.docx` without a contract; pairing flags from the pairing map / ticket / stem heuristic | 1.4 (pairing) | DEMO-DAY (local) / LATER (upstream) |
| `/api/demo/frd` | POST | `{"kind": "upstream"\|"local", "id": string}` | `{"selected", "kind", "feeds": null}` (local) / `{"selected", "kind", "audited_at", "feeds": [...]}` (upstream) | 200, 400, 404, 409, 502, 503 | `invalid contract name '<<id>>'` · `no local contract named '<<id>>'` · `unknown kind '<<kind>>'` · `cannot change the FRD while a live run is in progress` · upstream transport text · `not built in this workspace — upstream contracts table` | none (local); upstream materialises a contract into `uploads/` | 1.6 | DEMO-DAY (local) / LATER (upstream) |
| `/api/demo/frd` | DELETE | — | `{"selected": null}` | 200, 409 | as above | none | — | DEMO-DAY |
| `/api/demo/upload` | POST | multipart `kind=sttm\|frd`, `file` | 201 `{"stored": "<<name>>", "kind", "selected": true}` | 201, 400, 409, 413 | `cannot change inputs while a live run is in progress` · `invalid file name '<<name>>'` · `'<<name>>' exceeds the 25 MiB upload cap` · `'<<name>>' is empty` · `an STTM upload must be a .xlsx workbook, got '<<name>>'` · `an FRD upload must be a .contract.json produced by the FRD→STTM agent, got '<<name>>'` · `not a valid FRD contract: <<first line, ≤200 chars>> — run the FRD→STTM agent to produce one` · `unknown upload kind '<<kind>>'` | FRD contract validation | 1.6 | DEMO-DAY |
| `/api/replay/sets` | GET | — | `{"sets": [ReplaySet]}` | 200 | — | none — lists `<<inputs_volume>>/replay/` | — | LATER |
| `/api/replay/load` | POST | `{"set": string}` | `FeedsResponse` | 200, 404, 500, 503 | `no replay set named '<<set>>' under fixtures/replay/` · `contract pair failed to resolve: <<message>>` · `not built in this workspace — replay loader` | deterministic re-run with recorded candidates injected (needs a candidate-override entry point; not in S1–S6) | 5.2 (artifact shape) | LATER |
| `/api/demo/live-runs` | GET | — | `{"runs": [PastLiveRun]}` | 200 | — | none — lists `runs/demo_*` | — | LATER |
| `/api/demo/load-live-run` | POST | `{"run": string}` | `FeedsResponse` | 200, 404, 400 | `no past live run named '<<run>>' under runs/` · `live run '<<run>>' failed before producing results — cannot load` · `contract pair failed to resolve: <<message>>` | against the run directory alone: read each feed's report (verdict line, `Flags:` block, `## Gate` table), `candidates/candidates.json`, `framework/` listing and `run_meta.json`; rebuild the run records without re-running the generator | 5.5 (report layout), 5.2 | LATER |
| `/api/demo/input-documents` | GET | — | `{"documents": [InputDocumentScan ×2]}` | 200 | — | none — scans `standards/` and `uploads/` | — | DEMO-DAY |
| `/api/demo/source-files` | GET | — | `SourceFilesResponse` | 200, 404, 503 | file-not-found text · `not built in this workspace — source files panel` | display only | 0.1 (`demo.source_files.*`) | LATER |
| `/api/demo/metadata-sheet` | GET | — | `MetadataSheetResponse` | 200, 404 | file-not-found text | reads each loaded feed's `config_rows.xlsx` (seven tabs + `_provenance`) | 4.0 (S3–S5) | DEMO-DAY |
| `/api/demo/metadata-sheet.xlsx` | GET | — | bytes (`.xlsx`), attachment `metadata_sheet_<<label or mock>>.xlsx` | 200, 404 | as above | same content as one workbook | 4.0 | DEMO-DAY |
| `/api/demo/input-requirements` | GET | — | `InputRequirementsResponse` | 200, 503 | `not built in this workspace — input requirements check` | display only | — | LATER |
| `/api/demo/governance-checks` | GET | — | `GovernanceChecksResponse` | 200, 503 | `not built in this workspace — governance checks` | display only | — | LATER |
| `/api/databricks/documents` | GET | — | `DatabricksDocumentsResponse` | 200, 502, 503 | the workspace's message · `not built in this workspace — raw document volumes` | none | — | LATER |
| `/api/databricks/fetch` | POST | `{"volume", "name"}` | `{"fetched", "dest"}` | 200, 400, 502, 503 | `unknown volume '<<volume>>'` · transport text | none | — | LATER |
| `/api/databricks/publish-target` | GET | — | `DatabricksPublishTarget` | 200 | — (`reason: "not built in this workspace — volume publish"` until built) | none | — | LATER |
| `/api/databricks/publish` | POST | `{"confirm": true, "feed_slug", "catalog", "schema_name", "volume", "force"?}` | `DatabricksPublishResult` | 200, 400, 404, 502, 503 | `publishing writes to a Unity Catalog volume and requires an explicit {"confirm": true}` · `pipeline unavailable` · `no generated feed named '<<slug>>'` · `nothing to publish for '<<slug>>' — generate the feed first` · the writable-prefix refusal · transport text | none — copies the feed's report + framework files (+ notebook when one exists) | — | LATER |
| `/api/sharepoint/config` | GET | — | `{"configured", "site", "library", "input_folder", "output_folder"}` | 200 | — | none | — | LATER |
| `/api/sharepoint/documents` | GET | — | `{"site", "library", "folder", "documents": [...]}` | 200, 502, 503 | UI_SPEC §3.8 | none | — | LATER |
| `/api/sharepoint/import` | POST | `{"item_id", "name"}` | 201 `{"path", "name", "stem", "kind", "source": "sharepoint", "size_bytes"}` | 201, 400, 413, 502, 503 | UI_SPEC §3.8 | none | — | LATER |
| `/api/sharepoint/locate` | POST | `{"name"}` | `{"status": "ready", ...}` / `{"status": "candidates", ...}` | 200, 400, 404, 502, 503 | UI_SPEC §3.8 | none | — | LATER |
| `/api/sharepoint/artifact/{item_id}` | GET | — | bytes | 200, 404, 502, 503 | UI_SPEC §3.8 | none | — | LATER |
| `/api/sharepoint/publish` | POST | `{"feed_slug", "path"?, "confirm": true}` | `{"published": true, "feed_slug", "artifacts": [...], "target"}` | 200, 400, 404, 413, 502, 503 | UI_SPEC §3.8 | none | — | LATER |
| `/` and every non-`/api` path | GET | — | the frontend (HTML shell fallback, `Cache-Control: no-store, must-revalidate` on HTML) | 200 | — | none | — | DEMO-DAY |

Global rule: when the configuration failed to load at start-up, `/api/feeds` answers as in
its row and every other `/api` route answers `503` `pipeline unavailable — <<error>>`.

Example — `GET /api/feeds` after boot on the synthetic Pair A (abridged to one feed):

```json
{
  "feeds": [
    {
      "feed_slug": "syn_gadget_events", "feed_id": "syn_gadget_events", "feed_name": "Syn Gadget Events",
      "source_system": "SynVendor Analytics", "lobs": ["Region 1", "Region 2"], "file_format": "psv",
      "frequency": "Weekly Monday 8 PM", "segmented": false, "sttm_is_synthetic": false,
      "verdict": "PASS_WITH_FLAGS",
      "flags": ["faq_unanswered:is_master_file", "faq_unanswered:dedup_within_file",
                "faq_unanswered:existing_record_policy", "faq_unanswered:target_tables_exist",
                "faq_unanswered:reject_threshold", "faq_unanswered:data_integrity_checks",
                "load_mode_not_enforced: declared truncate_and_load; generated writer uses MERGE-by-file (branching planned v2)",
                "rule classified notification: 'Email notification should be sent to the Support team whenever there is an issue.' — job JSON carries an email_notifications block; recipients come from config (job.notification_emails)",
                "Layer-2 candidate pending engineer approval: 'Column GADGET_NM is mapped to GADGET_NAME in the standard layer.'",
                "generated tests were skipped — PASS cannot be claimed"],
      "checks": [{"name": "ruff", "passed": true, "details": "ruff clean"},
                 {"name": "debug_patterns", "passed": true, "details": "no debug statements"},
                 {"name": "secrets", "passed": true, "details": "no hardcoded secrets"},
                 {"name": "test_per_module", "passed": true, "details": "every pipeline module has a test file"}],
      "rule_counts": {"mappable": 2, "orchestration_config": 1, "notification": 1, "unmapped": 1},
      "rule_total": 5, "candidate_count": 1, "candidates_pending": 1, "files_written": 3,
      "framework": {"files": ["syn_gadget_events_stage_table_creation.txt",
                              "syn_gadget_events_standard_table_creation.txt", "config_rows.xlsx"],
                    "row_counts": {"DATA_FACTORY_PIPELINE_SCHEDULE": 2, "ADLS_DELTA_INGESTION_DETAILS": 1,
                                   "STGDELTA_STDDELTA_INGESTION_DET": 1, "DATA_QUALITY_RULES": 3,
                                   "DATABRICKS_NOTEBOOK_DETAILS": 2, "EMAIL_TEMPLATE_CONFIG": 2,
                                   "ALL_FILES_STATIC_INFORMATION": 1},
                    "coverage": {"derived": 83, "synthetic": 34, "needs_template": 168, "total": 285},
                    "flagged_blank_columns": ["PIPELINE_ID", "PARENT_PIPELINE_ID", "GROUP_ID", "OBJECT_ID",
                                              "INVENTORY_ID", "SRC_ADLS_CONNECTION_ID", "METADATA_CONNECTION_ID",
                                              "TGT_CONNECTION_ID", "CLUSTER_DETAILS_ID", "DATABRICKS_WORKSPACE_URL",
                                              "DATABRICKS_WORKSPACE_SECRET", "DATABRICKS_CLUSTERID"]}
    }
  ],
  "failures": [],
  "mode": "mock",
  "label": null
}
```

The `details` strings of the four checks are whatever the S1–S6 package records for its
trivially-passing checks (SPEC 5.4); the coverage numbers are the workbook's. The flags list
is line-exact with ACCEPTANCE S5 case 1's second feed.

Example — `POST /api/demo/inspect` on Pair A (abridged):

```json
{
  "sttm": "syn_widget_sttm.xlsx", "frd": "syn_widget_frd",
  "contract_file": "syn_widget_sttm.contract.json",
  "summary": "2 feed(s): syn_widget_risk (4 fields), syn_gadget_events (6 fields)",
  "feeds": [
    {"feed_id": "syn_widget_risk", "feed_slug": "syn_widget_risk",
     "stage_tables": ["stg_syn.syn_widget_risk"], "standard_table": "syn.syn_widget_risk", "rule_count": 1},
    {"feed_id": "syn_gadget_events", "feed_slug": "syn_gadget_events",
     "stage_tables": ["stg_syn.syn_gadget_events", "stg_syn.syn_gadget_events_recycle"],
     "standard_table": "syn.syn_gadget_events", "rule_count": 5}
  ],
  "faq": {
    "syn_gadget_events": {
      "feed_slug": "syn_gadget_events", "file_present": false,
      "questions": [
        {"name": "load_mode", "value": "truncate_and_load", "source": "contract",
         "evidence": "stage_target.load_strategy: \"Truncate and Load\"", "default": "unknown", "prefilled": true,
         "options": ["truncate_and_load", "append", "merge_on_keys"]},
        {"name": "is_master_file", "value": null, "source": "unknown", "evidence": null, "default": "unknown",
         "prefilled": false, "options": ["yes", "no"]},
        {"name": "load_frequency", "value": "weekly", "source": "contract", "evidence": "Weekly Monday 8 PM",
         "default": "unknown", "prefilled": true, "options": ["daily", "weekly", "monthly", "yearly", "adhoc"]}
      ],
      "companions": [{"name": "has_header", "value": null, "source": "unknown", "evidence": null,
                      "default": "", "prefilled": false, "options": ["yes", "no"]}],
      "counts": {"from_contract": 2, "answered_here": 0, "unanswered": 6}
    }
  }
}
```

(The field counts in `summary` are whatever the extractor reports for the INPUTS.md sheets;
the eight questions always appear in SPEC 1.8 order — the example shows three.)

Example — `POST /api/demo/run-live` answer, and `GET /api/demo/status` a few seconds later:

```json
{"state": "running", "stages": [], "error": null, "last_run_label": null,
 "mode": "mock", "label": null, "estimates": {"calls": 3, "cost_usd": 0.1, "seconds": 20},
 "sttm_workbook": "syn_widget_sttm.xlsx", "sttm_chosen": true,
 "output_mode": "framework", "output_modes_available": ["framework"],
 "frd_name": "syn_widget_frd", "frd_chosen": true, "frd_warning": false, "error_hint": null}
```

```json
{"state": "running",
 "stages": [{"stage": "extracting workbook", "detail": "syn_widget_sttm.xlsx → STTM mapping contract (FRD: syn_widget_frd)", "at": 1768574400.12},
            {"stage": "resolving contracts", "detail": "syn_widget_frd ⋈ extracted contract", "at": 1768574400.48},
            {"stage": "syn_widget_risk: compiling rules", "detail": "", "at": 1768574400.51},
            {"stage": "syn_widget_risk: Layer-2 reasoning", "detail": "", "at": 1768574400.52},
            {"stage": "syn_widget_risk: emitting code", "detail": "", "at": 1768574400.53},
            {"stage": "syn_widget_risk: framework artefacts", "detail": "", "at": 1768574400.90},
            {"stage": "syn_widget_risk: gate", "detail": "", "at": 1768574401.40},
            {"stage": "syn_gadget_events: compiling rules", "detail": "", "at": 1768574401.62}],
 "error": null, "last_run_label": null, "mode": "mock", "label": null,
 "estimates": {"calls": 3, "cost_usd": 0.1, "seconds": 20},
 "sttm_workbook": "syn_widget_sttm.xlsx", "sttm_chosen": true, "output_mode": "framework",
 "output_modes_available": ["framework"], "frd_name": "syn_widget_frd", "frd_chosen": true,
 "frd_warning": false, "error_hint": null}
```

Example — a failed run (Pair D, the disagreeing recycle window):

```json
{"state": "failed",
 "stages": [{"stage": "extracting workbook", "detail": "syn_widget_sttm_v12.xlsx → STTM mapping contract (FRD: syn_widget_frd)", "at": 1768574500.01},
            {"stage": "resolving contracts", "detail": "syn_widget_frd ⋈ extracted contract", "at": 1768574500.40}],
 "error": "ContractMismatchError: contract mismatch for feed 'syn_gadget_events':\n  - recycle window disagrees: FRD text says 10 days, STTM spec says 12 days",
 "last_run_label": null, "mode": "mock", "label": null, "estimates": {"calls": 3, "cost_usd": 0.1, "seconds": 20},
 "sttm_workbook": "syn_widget_sttm_v12.xlsx", "sttm_chosen": true, "output_mode": "framework",
 "output_modes_available": ["framework"], "frd_name": "syn_widget_frd", "frd_chosen": true,
 "frd_warning": false, "error_hint": null}
```

The exception type name is whatever the S1 resolver raises for a mismatch; the message after
the colon is SPEC 5.4's mismatch text verbatim.

## 2. State model

### 2.1 The loaded run (one at a time)

| Field | Type | Meaning |
|---|---|---|
| `mode` | `mock` \| `live` \| `replay` | which pipeline produced the served state; boot and `/api/generate` set `mock` |
| `label` | string \| null | `null` for mock; `<<run_id>>` for live; the set name for replay |
| `out_root` | Volume path | `runs/mock/` for mock; `runs/<<run_id>>/` for live; `runs/replay_<<set>>/` for replay |
| `reports_root` | Volume path | `<<out_root>>/reports/` |
| `runs` | map feed_slug → run record | one record per generated feed |
| `failures` | list of `{label, error}` | pairs that failed to resolve (`label` = `<<frd file>> + <<sttm file>>`) and feeds that hit a template gap (`label` = feed_id, `error` = `template gap: <<message>>`) |
| `has_run` | bool | false until boot or the first generate completes |

Per-feed run record:

| Field | Source |
|---|---|
| `spec` | the resolved feed specification (SPEC 1.7): feed_id, feed_slug, feed_name, source_system, lobs, file_format, delimiter, frequency, file_name_patterns, landing_location, segments (stage tables), standard table, errors / processed-files / recycle tables, natural key, not-null, PHI, load windows, contract names + sha256, `sttm_is_synthetic`, `is_segmented` |
| `outcomes` | the classified rules (5.1) in contract order |
| `candidates` | the Layer 2 artifact entries (5.2), CONFIRM items first |
| `gate` | `{verdict, flags[], checks[{name, passed, details}]}` (5.3, 5.4) |
| `written_files` | Volume-relative posix paths of every file the feed wrote (the three files) |
| `framework` | `{files[], row_counts{}, coverage{}, flagged_blank_columns[]}` from the workbook (4.0) — `null` in notebook mode |

Adopting a run swaps all seven fields atomically under one lock.

### 2.2 The runner (state machine)

| State | Meaning | Allowed transitions |
|---|---|---|
| `idle` | no run since boot | → `running` on `POST /api/demo/run-live` |
| `running` | the background thread is executing; `stages` append-only | → `done` when the thread finishes with ≥1 feed; → `failed` on any exception |
| `done` | the last run completed; `last_run_label` = its `<<run_id>>`; the run is adopted as the loaded run (mode `live`) | → `running` on the next run (stages reset, error cleared) |
| `failed` | `error` = `<<ExceptionType>>: <<message>>`; nothing adopted; `error_hint` may be set | → `running` on the next run |

409 rules: while `running`, every mutating input route (workbook select/clear, FRD
select/clear, upload, output mode, inspect, FAQ save) answers 409 with its own exact string
(§1); a second `run-live` answers 409 `a live demo run is already in progress`. Reads
(`status`, `feeds`, files, downloads) are never blocked. The runner's selections live in
memory only: `selected_workbook` (null = the configured default), `selected_frd` +
`selected_frd_label` (null = the configured default FRD), `output_mode` (null = the
configured default), `last_run_label`, `error_hint`.

### 2.3 Decisions store (v2)

File: `<<outputs_volume>>/state/decisions.json`. Key: `run_key` = the loaded `label`, or
`mock` when it is null.

```json
{
  "version": 2,
  "runs": {
    "mock": {
      "syn_gadget_events": {"0": {"decision": "approved", "note": null}}
    },
    "demo_20260116_143000": {
      "syn_gadget_events": {"0": {"decision": "rejected", "note": "duplicate of the STTM rename"}}
    }
  }
}
```

A file whose `version` is not 2, or whose top level is not a mapping, is discarded as a
whole (treated as empty). Reset removes the current `run_key` entry only. Every write
replaces the whole file (2-space indent, trailing newline) under the store's lock.

### 2.4 Run directory layout

Every file the UI reads is named. `<<outputs_volume>>/runs/<<run_id>>/`:

| Path (relative to the run directory) | Written by | Read by |
|---|---|---|
| `frd.contract.json` | run start — a byte copy of the FRD used (content-identical, so provenance hashes are unchanged) | past-run loader; `FeedDetail.contracts` |
| `run_meta.json` | run start — `{"frd_label": "<<label>>", "sttm_workbook": "<<name>>", "output_mode": "framework"}` (2-space indent, trailing newline) | past-run loader; run history |
| `extracted_sttm.contract.json` | stage `extracting workbook` | stage `resolving contracts`; past-run loader |
| `faq/<<feed_slug>>.faq.yaml` | run start — copies of the answer store's files for the pair's feeds (only feeds with a file) | the generator (SPEC 1.8) |
| `<<feed_slug>>/framework/<<feed_slug>>_stage_table_creation.txt` | stage `framework artefacts` | Generated code tab, downloads, the framework panel |
| `<<feed_slug>>/framework/<<feed_slug>>_standard_table_creation.txt` | same | same |
| `<<feed_slug>>/framework/config_rows.xlsx` | same | downloads, the metadata-sheet preview (tabs + `_provenance` badges) |
| `<<feed_slug>>/candidates/candidates.json` | stage `Layer-2 reasoning` (only when the candidate list is non-empty; CONFIRM items count) | `FeedDetail.candidates`, the review tab |
| `reports/<<feed_slug>>.md` | stage `gate` (SPEC 5.5) | Report tab; past-run loader (verdict, flags, gate table) |

`runs/mock/` has the same layout minus `frd.contract.json`, `run_meta.json` and `faq/`, plus
`extracted/<<workbook stem>>.contract.json` per configured `.xlsx` pair member; it is rewritten
by every mock generate. Nothing under a `demo_*` directory is ever overwritten or deleted by
the App; two runs of the same pair yield two directories whose three files are byte-identical
except the FAQ sha span when the answers differ (SPEC 2.2).

Where the generator runs: on the container's local disk under a scratch directory; when a
feed's gate completes, its files are copied to the Volume run directory, and the run record's
`written_files` name the Volume paths. Reads served to the UI always come from the Volume
copy, so what the user downloads is what is on the Volume. The scratch directory is deleted
when the run ends.

## 3. Stage names (exact order) and detail texts

| # | Stage name | Detail text | When appended |
|---|---|---|---|
| 1 | `extracting workbook` | `<<workbook file name>> → STTM mapping contract (FRD: <<frd label>>)` | before the extractor runs (SPEC 1.1–1.4) |
| 2 | `resolving contracts` | `<<frd label>> ⋈ extracted contract` | before resolution (1.5–1.7) |
| 3 | `<<feed_slug>>: compiling rules` | `` (empty) | per feed, before classification (5.1) |
| 4 | `<<feed_slug>>: Layer-2 reasoning` — suffix ` (live)` when the provider is not mock | `` | per feed, before Layer 2 (5.2); omitted when recorded candidates are injected (replay) |
| 5 | `<<feed_slug>>: emitting code` | `` | per feed, before the FAQ is read and the DDL sources rendered (1.8, 2, 3) |
| 6 | `<<feed_slug>>: framework artefacts` | `` | per feed, framework and both modes only, before the IIG workbook (4) |
| 7 | `<<feed_slug>>: gate` | `` | per feed, before flags/verdict/report (5.3–5.5) |
| 8 | `publishing results` | `<<n>> feed(s), <<m>> failure(s)` | once, before the results are adopted as the loaded run |

A feed that raises after stage 3 leaves its stages listed and becomes a `failures` entry; the
next feed continues; stage 8 still fires when at least one feed completed. A run whose
extract or resolve raises stops after stage 1 or 2 with `state: failed`. The S1–S6 package
exposes no progress hook of its own; the backend's per-feed wrapper appends stages 3–7 around
the calls it makes, in the order above — a rebuild that cannot separate steps 5 and 6 appends
both before the combined call.

## 4. Start-up

| Step | What runs | Effect |
|---|---|---|
| 1 | load the configuration file; resolve `<<inputs_volume>>` and `<<outputs_volume>>` from the App-injected environment values | failure → the store is absent: `/api/feeds` reports `failures: [{label: "startup", error: "pipeline unavailable — <<ExceptionType>>: <<message>>"}]`, every other route 503; the process still serves the frontend |
| 2 | ensure `<<outputs_volume>>/uploads/`, `faq/`, `state/`, `runs/` exist | creates them when missing |
| 3 | discover the configured pairs: `contracts.pairs` entries `{frd, sttm}` where `frd` is a file name under `<<inputs_volume>>/frd/` and `sttm` a file name under `<<inputs_volume>>/sttm/` (an `.xlsx` is extracted at generate time; a `.contract.json` is used directly) | an entry whose file is missing becomes a `failures` row `{label: "<<frd>> + <<sttm>>", error: "<<file-not-found text>>"}`; the boot continues |
| 4 | run the mock generate over the pairs (the same path as `POST /api/generate`), FAQ answers from `<<outputs_volume>>/faq/`, output mode from configuration (`framework`) | the loaded run = mode `mock`, label `null`; `runs/mock/` rewritten |
| 5 | the runner starts `idle` with null selections | — |

What `/api/feeds` returns before the first run completes: boot generation runs BEFORE the
server starts accepting requests (the lifespan hook), so the first request already sees the
boot result. If boot generation raised, the App still starts: `{feeds: [], failures: [],
mode: "mock", label: null}` and the console line `Startup generation failed — UI starts
empty; POST /api/generate retries: <<error>>`. With zero configured pairs the boot generate
raises the 409 text and the same empty response is served.

## 5. Downloads and containment

| Rule | Detail |
|---|---|
| containment | `path` is joined to `<<out_root>>/<<feed_slug>>/`, resolved, and must remain inside that directory; otherwise 400 `path escapes feed directory: <<path>>` — never a read outside the feed |
| missing | a resolved path that is not a file → 404 `file not found: <<path>>` |
| text route | reads UTF-8; a decode failure → 400 `not a text file: <<path>> — use the download route` |
| download media types | `.xlsx` → `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`; everything else → `text/plain; charset=utf-8`; header `Content-Disposition: attachment; filename="<<basename>>"` |
| metadata-sheet workbook | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, attachment `metadata_sheet_<<label or mock>>.xlsx`, built in memory |
| report | `{markdown}` JSON, never a file download |
| upload cap | 25 MiB (`ui.upload_cap_mib`), checked after reading the body: 413 |
| upload names | the basename only; `~$` prefix or `..` → 400; written to `<<outputs_volume>>/uploads/<<name>>.part` then renamed |

## 6. Databricks App configuration (prose)

- **Command.** The Python interpreter launched in module mode on the backend package's main
  module — one process, no shell wrapper, no separate web server.
- **Port.** The process reads `DATABRICKS_APP_PORT` at start-up (the platform injects it),
  falls back to `CODEGEN_UI_PORT`, then `8571`, and binds all interfaces.
- **Resources.** Two Unity Catalog volume resources: the inputs Volume with the read
  permission and the outputs Volume with the read-and-write permission; the App reads their
  resolved paths from environment values the configuration maps from those resources (the
  `valueFrom` mechanism) — never a hard-coded path. Optionally a serving-endpoint resource
  (CAN_QUERY) for live Layer 2; when it is declared the configured provider resolves to it.
- **Service-principal permissions.** Read on the inputs Volume, read-and-write on the outputs
  Volume (both granted declaratively by the resources), and CAN_QUERY on the serving endpoint
  when one is declared. No SQL warehouse, no secret, no table access is needed for the
  DEMO-DAY set.
- **Force-mock switch.** The environment value `CODEGEN_FORCE_MOCK_PROVIDER=1` in the App
  configuration is the rebuild's default: Layer 2 makes zero model calls, the live-availability
  route reports provider `mock (locked)`, the generate card's badge reads `MOCK — provider
  locked`. Remove the value and declare the serving-endpoint resource to go live.
- **Notification list.** The environment value that overrides `job.notification_emails` is
  pinned to the synthetic address of SPEC 0.1 in any deployment whose artefacts may be shared.
- **Reverse-proxy note.** The run POST returns immediately with the status; the frontend
  polls `/api/demo/status` every 1 000 ms. No request is held open longer than a generator
  call for one route (inspect: extract + resolve, seconds). Long-request and streaming
  behaviour through the Apps reverse proxy is deliberately never relied on.
- **Container restarts.** Wipe in-memory selections and the loaded-run pointer; boot
  regenerates the mock run. Everything on the outputs Volume survives.
