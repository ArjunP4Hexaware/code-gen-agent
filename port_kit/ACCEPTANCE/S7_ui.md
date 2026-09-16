# S7 — The demo UI as a Databricks App (manual checklist)

**Goal:** the DEMO scope of `UI_SPEC.md` running as a Databricks App: choose a pair, answer the
FAQ, run, see the verdict and flags, preview and download the three files.

**Frozen prerequisites:** S1–S3 frozen (S4–S6 may still be in progress; checks 10 and 15 need
S3 only, the IIG tabs beyond tab 2 are shown as produced and not compared here).

**Read first:** `UI_SPEC.md` (all sections) and this file. Do not read `SPEC.md` for the UI;
the generator is frozen.

**Setup before the checks:** materialize the synthetic inputs of `INPUTS.md` and place them
on the inputs Volume: `frd/syn_widget_frd`, `frd/syn_widget_frd_renamed`, `frd/syn_segmented_frd`,
`frd/syn_sensor_frd`; `sttm/syn_widget_sttm.xlsx`, `sttm/syn_widget_sttm_v12.xlsx`,
`sttm/syn_segmented_sttm.xlsx`, `sttm/syn_sensor_sttm.xlsx`; `standards/` holds any two files
(their names are only counted). The configuration carries the SPEC 0.1 acceptance values and
the force-mock switch (UI_SPEC §6). Start from a fresh browser session. "Exact" below means
the on-screen text equals the quoted text character for character; `<<run_id>>` is whatever the
app minted.

The UI cannot be byte-diffed; every check states a click path and the exact expected result.
A check passes only when every expected line holds.

## 1. Cold start lands in `idle` with the folder listed

Click path: open the app URL.

Expected: the caption `Layer 1 deterministic · Layer 2 mock provider (review-only candidates) · verdict computed in code, never by judgment.`
under the title; section `1 · Choose the pair` open; the input-folder caption shows the
configured `/Volumes/…/` path; the FRD dropdown offers exactly `(select one)`, `syn_segmented_frd`,
`syn_sensor_frd`, `syn_widget_frd`, `syn_widget_frd_renamed` (sorted); the STTM dropdown offers
`(select one)` and the four workbooks (sorted); the Standards box is checked and disabled with
the caption `Client Data Engineering Naming + Coding Standards` and `documents: 2 present`;
`Inspect pair` is disabled with the tooltip `Choose both files first`; sections 2–4 are collapsed.

## 2. A workbook that pairs with no FRD feed fails loudly at inspection (Pair E)

Click path: FRD `syn_widget_frd_renamed`, STTM `syn_widget_sttm.xlsx`, `Inspect pair`.

Expected: a red card titled `RUN FAILED — nothing was written for the failed scope`; line 1
exact: `extracting workbook — sheet 'MAPPING-SYN_GADGET_EVENTS' (stage table 'syn_gadget_events') matches 0 FRD feeds ['Syn Widget Risk', 'Syn Gadget Events']; expected exactly one whose stage_target.tables contains it`;
line 2 exact: `The workbook could not be read as a mapping document; nothing was guessed. Fix the sheet the message names and inspect the pair again.`;
section 2 stays collapsed; the two dropdowns keep their picks.

## 3. Pair A inspects into two feeds

Click path: FRD `syn_widget_frd`, STTM `syn_widget_sttm.xlsx`, `Inspect pair`.

Expected: the red card is gone; the Pair inspection card reads `Extracted: syn_widget_sttm.contract.json — 2 feed(s)`
and two rows exact:

| feed_id | stage tables | standard | rules |
|---|---|---|---|
| syn_widget_risk | stg_syn.syn_widget_risk | syn.syn_widget_risk | 1 |
| syn_gadget_events | stg_syn.syn_gadget_events, stg_syn.syn_gadget_events_recycle | syn.syn_gadget_events | 5 |

Section `2 · Load-pattern FAQ` opens with two tabs `syn_widget_risk` and `syn_gadget_events`;
`Generate` in section 3 is enabled.

## 4. The FAQ shows the contract prefills and the defaults

Click path: tab `syn_widget_risk`.

Expected: row `load_mode` preselected `truncate_and_load`, source `contract` (read-only),
evidence `stage_target.load_strategy: "Truncate and Load"`, caption
`prefilled from the contract — change the value to override it`; row `load_frequency`
preselected `monthly`, source `contract`, evidence
`Monthly Run; file received by the fifth business day`; the other six rows read
`(unanswered)` with captions `default: unknown`, `default: none`, `default: unknown`,
`default: yes`, `default: none`, `default: none` in that order; the summary line exact:
`2 answered by the contract · 0 answered here · 6 unanswered → 6 flags`. Tab `syn_gadget_events`:
`load_mode` prefilled `truncate_and_load`, `load_frequency` prefilled `weekly` with evidence
`Weekly Monday 8 PM`, same summary line.

## 5. Answers are saved as the generator's FAQ file; an untouched feed gets no file

Click path: tab `syn_widget_risk`; set every row to the value, source and evidence
`INPUTS.md` lists for `syn_widget_risk.faq.yaml` (load_mode `truncate_and_load` / engineer /
`FRD Structural Metadata: Load Strategy STG = "Truncate and Load"`; is_master_file `no` /
engineer; dedup_within_file `none` / engineer; existing_record_policy `delete_and_insert` /
engineer; load_frequency `monthly` / frd / `FRD frequency: "Monthly Run; file received by the fifth business day"`;
target_tables_exist `yes` / engineer; reject_threshold `none` / engineer;
data_integrity_checks `not_null_keys` / engineer; has_header `yes` / engineer /
`Vendor file specification: first row carries column names`; has_trailer `no` / engineer);
click `Save answers`. Switch to tab `syn_gadget_events`; change nothing; click `Save answers`.

Expected: on the first tab the summary line reads `0 answered by the contract · 8 answered here · 0 unanswered → 0 flags`
and the line `Saved syn_widget_risk.faq.yaml`; on the second tab the line
`No answers set — the generator will use defaults and flag every question` and the summary
line unchanged from check 4.

## 6. Generate shows the stages in order and ends with flags

Click path: `Generate`.

Expected: the button reads `Generating…` and every control of sections 1–2 is disabled while it
runs; the stage list ends as exactly these lines, in this order, each marked `✓`:
`extracting workbook — syn_widget_sttm.xlsx → STTM mapping contract (FRD: syn_widget_frd)`,
`resolving contracts — syn_widget_frd ⋈ extracted contract`, `syn_widget_risk: compiling rules`,
`syn_widget_risk: Layer-2 reasoning`, `syn_widget_risk: emitting code`,
`syn_widget_risk: framework artefacts`, `syn_widget_risk: gate`, then the same five for
`syn_gadget_events`, then `publishing results — 2 feed(s), 0 failure(s)`; section
`4 · Results — <<run_id>>` opens; the run id starts with `run_` followed by 15 characters.

## 7. PASS_WITH_FLAGS case — the two-flag feed (Pair A, `syn_widget_risk`)

Click path: results tab `syn_widget_risk`.

Expected: an amber banner exact: `PASS_WITH_FLAGS syn_widget_risk — 2 flag(s); ruff=ok, debug_patterns=ok, secrets=ok, test_per_module=ok`;
the line `Run verdict: PASS_WITH_FLAGS (worst of the feeds)`; heading `Flags (2) — needs a human`;
exactly two rows in this order — name `load_mode_not_enforced`, trigger
`FAQ load_mode is declared (answered or prefilled)`, cited text
`declared truncate_and_load; generated writer uses MERGE-by-file (branching planned v2)`;
name `generated tests were skipped`, trigger `tests skipped in this run`, cited text `—`;
the gate line `ruff ok · debug_patterns ok · secrets ok · test_per_module ok`.

## 8. The untouched feed carries the six unanswered-question flags first

Click path: results tab `syn_gadget_events`.

Expected: banner exact `PASS_WITH_FLAGS syn_gadget_events — 10 flag(s); ruff=ok, debug_patterns=ok, secrets=ok, test_per_module=ok`;
heading `Flags (10) — needs a human`; rows 1–6 have name `faq_unanswered` and cited text
beginning `is_master_file`, `dedup_within_file`, `existing_record_policy`,
`target_tables_exist`, `reject_threshold`, `data_integrity_checks` in that order; row 7 is
`load_mode_not_enforced`; the last row is `generated tests were skipped`.

## 9. Stage DDL preview is the whole file, monospace, with the no-FAQ banner line

Click path: results tab `syn_gadget_events`, expander `Stage DDL — syn_gadget_events_stage_table_creation.txt`.

Expected: a monospace block whose first three lines are
`-- FRD contract: syn_widget_frd sha256 <<64 hex>>`,
`-- STTM contract: STTM mapping contract extracted from syn_widget_sttm.xlsx sha256 <<64 hex>>`,
`-- Load-pattern FAQ: sha256 defaults (no FAQ file) — 2 answered, 6 unknown`; the block
contains the lines `--stg_syn.syn_gadget_events` and `--stg_syn.syn_gadget_events_recycle` and
scrolls horizontally without wrapping; a `Download` button sits beside the file name.

## 10. IIG preview: tabs in workbook order, cells verbatim, blanks blank

Click path: same feed, expander `IIG config rows — config_rows.xlsx`.

Expected: the tab strip reads, in order, `DATA_FACTORY_PIPELINE_SCHEDULE 2`,
`ADLS_DELTA_INGESTION_DETAILS 1`, `STGDELTA_STDDELTA_INGESTION_DET 1`, `DATA_QUALITY_RULES 3`,
`DATABRICKS_NOTEBOOK_DETAILS 2`, `EMAIL_TEMPLATE_CONFIG 2`, `ALL_FILES_STATIC_INFORMATION 1`, then a nested
`service sheets` expander holding `_provenance` and `_inputs`; on tab
`ALL_FILES_STATIC_INFORMATION` the single row shows `FILE_NAME` = `gadget_events_CCYYMMDD_HHMM.psv`,
`DESCRIPTION` = `Syn Gadget Events`, `LOB` = `Region 1, Region 2`, and `INVENTORY_ID`,
`OBJECT_ID` empty (not `NULL`); the line under the strip begins
`Framework-assigned IDs left blank: PIPELINE_ID, PARENT_PIPELINE_ID, GROUP_ID, OBJECT_ID, INVENTORY_ID, SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, TGT_CONNECTION_ID, CLUSTER_DETAILS_ID, DATABRICKS_WORKSPACE_URL, DATABRICKS_WORKSPACE_SECRET, DATABRICKS_CLUSTERID`
and ends `— the agent never invents them.`

## 11. FAIL case — a pair that disagrees stops before any verdict (Pair D)

Click path: section 1: FRD `syn_widget_frd`, STTM `syn_widget_sttm_v12.xlsx` (the results of
check 6 disappear as the state returns to `idle`), `Inspect pair`.

Expected: the red card `RUN FAILED — nothing was written for the failed scope`; line 1 exact,
on three lines:
`resolving contracts — contract mismatch for feed 'syn_gadget_events':`
`  - recycle window disagrees: FRD text says 10 days, STTM spec says 12 days`;
line 2 exact: `The FRD and the STTM disagree; nothing here is guessed. Fix the document that is wrong and inspect the pair again.`;
`Generate` stays disabled; no results section. (SPEC 5.4 reports this family as `FAIL`; a
`FAIL` verdict banner on a completed feed needs a failed gate check, which no synthetic input
can produce — this card is the FAIL case.)

## 12. Segmented pair: CONFIRM items appear as flags with their citations (Pair B)

Click path: FRD `syn_segmented_frd`, STTM `syn_segmented_sttm.xlsx`, `Inspect pair`; on the
FAQ tab `synthetic_segmented_feed` set is_master_file `no` / engineer and has_header `yes` /
engineer, `Save answers`; `Generate`; results tab `synthetic_segmented_feed`.

Expected: the Pair inspection card lists one feed with three stage tables; the banner reads
`PASS_WITH_FLAGS synthetic_segmented_feed — 9 flag(s); …`; the flags table has two rows named
`confirm item pending` whose cited text begins `CONFIRM — positional header/detail identification per`
and `CONFIRM — audit columns per segment follow the STTM:` respectively, each followed by a
quoted citation line — the first citation names the STTM row and contains `******`, the second
begins `FRD rule:`; two rows named `Layer-2 candidate pending` whose
cited text quotes `Populate file type and source file name fields in the target tables.` and
`Header, Detail and Trailer data should be mapped to respective HDR, DTL and TRL tables.`; the
Stage DDL expander shows four `CREATE OR REPLACE TABLE` statements and the Standard DDL expander three; the candidates expander
lists four entries, two marked `CONFIRM`.

## 13. Stage-only pair: classified-flagged rules and the empty standard file (Pair C)

Click path: FRD `syn_sensor_frd`, STTM `syn_sensor_sttm.xlsx`, `Inspect pair`; leave the FAQ
untouched; `Generate`; results tab `syn_sensor_pings`.

Expected: banner `PASS_WITH_FLAGS syn_sensor_pings — 11 flag(s); …`; two rows named
`rule classified flagged` with cited text exact
`'Files are pipe-delimited.' — MISMATCH: resolved delimiter is ','` and
`'Invalid records will be moved to the Recycle table.' — FRD states a recycle rule but the STTM has no structured recycle spec for this feed — unconfirmed attribution; no recycle module generated`;
one row named `Layer-2 candidate pending` quoting
`If the SENSOR_ID column is NULL, then we are rejecting the record and moving it to the reject table.`;
the Standard DDL expander caption reads `stage-only feed — no standard tables` and its block
ends with the single line `-- No standard-layer table for this feed (stage-only load).`; the Pair inspection card shows `none — stage-only` in the standard column.

## 14. A rerun mints a new run id and leaves the previous run untouched

Click path: with Pair C still selected, `Generate` again; then list
`<<outputs_volume>>/runs/` in the workspace.

Expected: the results heading shows a different `<<run_id>>` (later timestamp); the runs folder
holds every run of checks 6, 12, 13 and 14, each with `inputs/`, `out/<<feed_slug>>/framework/`,
`reports/`, `run_meta.json`; the run of check 13 still holds its three files with unchanged
sizes.

## 15. Final — the downloaded files match the frozen S1–S3 outputs

Click path: FRD `syn_widget_frd`, STTM `syn_widget_sttm.xlsx`, `Inspect pair`; FAQ exactly as
in check 5; `Generate`; results tab `syn_gadget_events`; click `Download` in each of the three
expanders, then `Download all (zip)`.

Expected: `syn_gadget_events_stage_table_creation.txt`, after masking the two sha256 spans,
equals the S1 case 3 block byte for byte; `syn_gadget_events_standard_table_creation.txt`,
masked the same way, equals the S2 case 1 block; `config_rows.xlsx` tabs
`ALL_FILES_STATIC_INFORMATION` and `DATA_FACTORY_PIPELINE_SCHEDULE` are cell-exact (value and
badge) against the S3 case 3 dump; the zip contains the same three files at
`out/syn_gadget_events/framework/` with identical bytes to the three single downloads, plus
`reports/syn_gadget_events.md`. Repeat the stage comparison for `syn_widget_risk` against the
S1 case 1 block.

## If you can't hit this

Compare what is on screen with the quoted text word for word; the first differing word names
the UI_SPEC control or the §7 message to re-read. If the difference is inside a generator
message, a file preview or a download, the UI is not at fault: the frozen S1–S3 slice is —
stop and report it rather than editing a frozen file or masking the difference in the UI. Never
paraphrase a generator message, never hide a flag, never preselect a pair.
