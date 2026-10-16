# CHANGELOG — ACFC (`feature/multi-table`)

What each version marker changes for a run inside ACFC. Newest first. Values that
must not enter git (storage account, containers, notebook names, status sets) are
named by field only — see `docs/acfc/OVERLAY_FIELDS.md`.

## 0.5.8.post66 — 2026-10-16 (artefacts panel review summary; generated files unchanged except the report's wording)

1. **Artefacts panel, per feed:** the bold sheet-count line is one review summary,
   e.g. "8 sheets · 17 rows · 9 open inputs (1 blocking) · empty by rule:
   FILE_ADLS (MFT), FIXED_WIDTH (delimited)". The derived ratio left the panel.
   - "empty by rule" lists only empty sheets, each with its reason:
     `FrameworkArtefacts.empty_by_rule` (FILE_ADLS = MFT from the rule-3 note; the
     fixed-width handler = delimited for a delimited file); short names in
     `metadata_template.EMPTY_BY_RULE_LABELS`.
   - Open inputs = the feed's open lines + the run-level ones
     (`GenerateRun.review_open`), attached by the App after the run. At home the
     one blocking line is `run.environment.storage_account` (D1's placeholder).
2. **Generation report:** the "badge coverage" row became the labelled line
   "cells derived from documents: <d> of <t>; the rest are profile defaults,
   framework-assigned blanks, or open inputs", under the per-sheet "IIG rows".

## 0.5.8.post65 — 2026-10-16 (Dashboard: two deprecated sections removed; App only)

One commit per item. Nothing else on the Dashboard moved; generated files are unchanged.

1. **Metadata-sheet preview removed** (tabs, table, coverage line, Download .xlsx,
   footnote): `MetadataSheetPanel`, its types / CSS, and the routes
   `GET /api/demo/metadata-sheet` and `/api/demo/metadata-sheet.xlsx`.
   `codegen.metadata_sheet` stays (the generator and `codegen demo-metadata-sheet`
   use it).
2. **"Publish to Unity Catalog volume" removed** (controls and the volume /
   credentials text): `DatabricksPublishPanel`, its types, and the routes
   `GET /api/databricks/publish-target` and `POST /api/databricks/publish`.
   Publishing stays on the CLI (`codegen databricks-publish`); the documents /
   fetch routes are unchanged.

## 0.5.8.post64 — 2026-10-16 (App wording; text only)

1. **Output toggle tooltip (App).** "Framework artefacts" now reads "DDL +
   BSA-annotated IIG for the existing ingestion framework" (was "DDL scripts +
   config rows + inserts …").

## 0.5.8.post63 — 2026-10-16 (approval wording; text only, the same files are written)

One commit per item.

1. **Metadata-sheet preview footnote (App).** It no longer describes the config
   rows and the insert SQL as the approval path. It now says the BSA-annotated
   IIG is the approval artefact and the CI/CD pipeline applies the DDL after
   approval: the artefacts panel's sentence (one constant, `artefacts.ts`
   `APPROVAL_NOTE`).
2. **Generation report.** "Framework output (Option B)" is now "Framework
   artefacts", with the same sentence. Its file table lists the files the App
   presents (`framework.presented_files`: the DDL, the IIG, its review copy,
   ADDITION.md); the DML / `metadata_inserts.sql` line is gone. Row counts read
   "IIG rows: <sheet>".

## 0.5.8.post62 — 2026-10-16 (App cleanup for the demo; no generator behaviour change)

One commit per item.

1. **Generate panel.** The "Source files this run will read" section was removed,
   along with its convention-check table (fed by the same request), the
   "In the Databricks workspace" disclosure, their state, the `api.sourceFiles()`
   request and the `GET /api/demo/source-files` route. Nothing else on the panel
   moved. The payload builder `codegen.demo_sources.source_files_payload` (used by
   `codegen demo-source-files`) is kept.
2. **Framework artefacts panel.** Each feed now shows exactly four files:
   `<FEED>_DDL.txt`, `<feed>_IIG.xlsx`, `<feed>_IIG_REVIEW.xlsx` and
   `ADDITION.md` (`ui/frontend/src/artefacts.ts`). `metadata_inserts.sql`,
   `config_rows.xlsx` and `config_inserts.xlsx` are still generated; the App no
   longer lists them.
   - Heading: "Framework artefacts".
   - Subtitle: the BSA-annotated IIG is the approval artefact; the CI/CD
     pipeline applies the DDL after approval.
3. **ADDITION.md** (template text only; the same files are written). It now has
   three sections:
   - the file table: the DDL, the IIG, the IIG review copy and ADDITION.md itself;
   - "Review flow": IIG → BSA review → the CI/CD pipeline applies the DDL;
   - "Framework-assigned IDs left blank", one per line.

   Nothing mentions inserts or config rows any more: the "By target system" and
   "Switches" blocks are gone.
4. **FRD picker default: none chosen.**
   - The demo contract is never preselected.
   - If the STTM has a match in the pair index, that FRD is preselected and
     labelled "paired" (status `frd_paired`, frd-choices `current.paired`).
   - A chosen STTM with no chosen or paired FRD disables Generate, with the reason
     shown. The run refuses with "no FRD chosen for <STTM>", unless the FRD
     pairing is still landing or will be asked.
   - Only when no STTM is chosen does a run fall back to the configured demo
     pair.
   - The `frd_warning` flag is gone.
   - Test: `test_frd_default.py`.
5. **The STTM picker lists only STTMs.** The existing content classifier
   (`classify_workbook`) gains the kinds `iig` and `iig_review`. A workbook with
   at least two IIG template sheets is an IIG; with the `REVIEW_SUMMARY` sheet as
   well, it is the review copy.
   - Only the App's document worker passes the template sheet names; the CLI's
     pair folders classify as before.
   - The chooser leaves both kinds out of the STTM and VDD lists, as well as any
     workbook with an `iig` token in its name (the existing name rule).
   - Index verdicts are stamped `classifier: 2`. An older verdict of
     "unclassified" is read again once, so IIGs cached before this change also
     drop out.
   - Test: a folder with 2 STTMs and 2 IIGs lists 2 (`test_m93_chooser.py`).

## 0.5.8.post61 — 2026-10-16 (two kinds of default: profile_default / agent_proposal)

- **profile_default** — the value comes from the conventions profile or the ACFC
  overlay. It is written when the run gives no answer: source `profile` in
  `CODEGEN_STAGES.json`, no gate flag and no open INPUT_NEEDED line (so it does
  not count toward PASS_WITH_OPEN_INPUTS). It is still listed as changeable: a
  `NOTE` line on the console, an `applied:` entry in `answers_template.yaml`
  (`choice: naming_standard` + `standard:` changes it) and the App's panel.
  - The email status set: back to the overlay's `email_status_default` (else every
    template row) when unanswered. With the overlay saying [Success, Failed] and
    no answer, the workbook gets two rows.
  - EMAIL_TO: the overlay's literal default (open while it is a `<<D1:…>>`
    placeholder, as before).
  - The notebook NAME per leg (`notebook_name.file_to_stg` / `.stg_to_std`, the
    `corpus_cells` value for the feed's notebook kind) and the ADLS SRC_FILE_NAME
    style (`src_file_name_style`: pattern | prefix_star | prefix_middle). These
    were already applied from the profile; they are now also listed and
    changeable. A changed notebook name leaves DATABRICKS_NOTEBOOK_PATH as the
    profile's (said in the cell's tooltip).
- **agent_proposal** — the value is rendered or derived by the agent: the
  PIPELINE_NAME template, APPLICATION_NAME from SOURCE, ACTIVE_START_DATE (no
  default). Unchanged from post59: shown, never written until chosen.
- An owed cell's kind is its new `default_kind`; unset, a default with a `{token}` is
  an agent proposal, a literal one a profile default. The committed overlay sets
  EMAIL_TO `profile_default`, APPLICATION_NAME `agent_proposal`; the email status
  rule is `profile_default`.
- Manifest: `feeds[].inputs.<key>.kind`. The App's `inputs_needed` items carry
  `kind` / `applied`; the panel counts only open inputs and lists applied
  profile defaults as "profile default applied … — changeable". The console's
  `ANSWERS FILE` line and the template header no longer count them (nor the
  shared pipeline_name entry) as needed.
- Tests: `tests/test_default_kinds.py` (the two-row status set, the agent
  proposals in the same run, EMAIL_TO, notebook names / style, changing each,
  the kind rule) and an `InputsNeededBanner.test.tsx` case. Updated:
  `test_overlay_fields.py`, `test_framework_owner_rules.py`,
  `test_iig_corpus_cells.py`, `test_environments.py`,
  `test_open_inputs_outcome.py` (the run-level open inputs are now 3, not 4).

## 0.5.8.post60 — 2026-10-16 (the App writes CODEGEN_STAGES.json; one generate entry point)

- **One feed pipeline.** `codegen.cli.generate_feed_result` is the feed
  pipeline of both the CLI and the App. `ui.backend.service.GenerationStore.
  _generate_feed` wraps it in a FeedRun instead of mirroring the CLI step by
  step. The App now gets the CLI's `iig_cells` and check order.
- **One run bookkeeper.** `codegen.generate_run.GenerateRun` is driven by both
  `codegen generate` (`cli._run_pairs`) and the App's live run
  (`DemoRunner._generate_specs`). It records:
  - the run-level lines (`run_level_lines`), held-back feeds and values no
    document states;
  - the BSA's choices and each feed's owed inputs / LOB question;
  - CRASHED (partial files removed) / GATE_FAIL (files quarantined +
    GATE_FAIL.md) / written;
  - the outcome and `<out root>/CODEGEN_STAGES.json`.

  The manifest (questions with `blocking`, `written`, `open`, `inputs`,
  `iig_cells`, the outcome) is identical from both.
- **App run states read the manifest.** The run's `outcome` (also on
  `GET /api/demo/status`) and each feed's `written` decide the state; nothing
  is inferred from which feeds returned. A run with no written feed is
  needs_answers when the outcome is NEEDS_ANSWERS, else failed. A GATE_FAIL
  feed is now quarantined in the App too, and its listed files point under
  `quarantine/`.
- Test: `tests/test_generate_entry_point.py`. It runs the App and the CLI on
  the same synthetic pair and checks the manifests are byte-identical (the
  manifest carries no timestamp), unanswered and with a confirmed choice, plus
  a GATE_FAIL quarantined by the App.

## 0.5.8.post59 — 2026-10-16 (PIPELINE_NAME three-way choice; file-name tie-break)

- **A defaulted input is a three-way choice** (`codegen.input_choices`): every
  `pipeline_name.<flow>` (grand_master / master / file_to_stg / stg_to_std, per
  feed) and APPLICATION_NAME, EMAIL_TO and the email status set where a default
  exists (ACTIVE_START_DATE has none).
  - `use_default`: the proposal. For PIPELINE_NAME this is the conventions
    profile's per-flow `pipeline_name_templates` over {domain} {subdomain}
    {source} {frequency} {layer} {load_mode}, shown with its template.
  - `naming_standard`: the BSA's template in the same syntax. One template for
    the feed renders all four names.
  - `leave_blank`.
- **Proposed is not applied** (Aruna's rule holds for every unattended run:
  CLI, harness, an App run with no confirmation).
  - An unanswered run writes the cell BLANK. Its non-blocking INPUT_NEEDED line
    shows the proposal and its template.
  - A cell is filled only on an explicit choice: the answers file's `choice:` /
    `standard:`, or Confirm in the App. A chosen default / standard raises the
    "taken from other documents" flag (`frd_unstated:<TAB>.<HEADER>[<flow>]
    source_used:…`).
  - Behaviour change: an unanswered APPLICATION_NAME is now blank (it was
    written with the feed's SOURCE), and an unanswered email status set writes
    every template row (`email_status_default` is a proposal).
  - `CODEGEN_STAGES.json` records each input's `source` per feed entry
    (`inputs`): default | standard | blank | answer, with `chosen`, `proposed`
    and `template`.
- **Templates.** The repo ships SYNTHETIC placeholders (`SYN_PL_…`, labelled
  "no naming standard loaded — placeholder" in the CLI line and the App). The
  real templates come from `codegen-state/overlays/acfc_prx.yaml`, overriding
  per flow (`docs/acfc/OVERLAY_FIELDS.md`).
- **Collisions.** A proposal that collides with a PIPELINE_NAME of the loaded
  goldens / corpus (`pipeline_name_corpus`; the committed overlay lists
  `docs/acfc/iig_goldens`) is never offered — the line asks instead, without
  printing the colliding name.
- **App.** The inputs panel shows radios (resting on use_default), the
  proposal beside its template, one naming-standard box per feed with a live
  preview of all four names, and Confirm (`POST /api/demo/input-choices`). Only
  confirmed choices reach the next Generate.
- **File-name recognizer.** A tie between files is broken by source priority
  (`file_tie_source_priority`: the FRD's landed pattern over an STTM
  FILE_DETAILS label …), then by shape (`file_tie_shape`: a vendor prefix + an
  extension). The BSA's answer is cached in the STTM layout profile
  (`file_choices`), so the next run of the same workbook takes it.
- `docs/acfc/OPEN_QUESTIONS.md` §3: Aruna's "blank" vs Venu's "default +
  standard", resolved as BSA-chooses-with-default-shown. Attach-a-document
  path deferred.
- Tests: `test_pipeline_name_choice.py`, `test_file_tie_break.py`,
  `InputsNeededBanner.test.tsx`.

## 0.5.8.post58 — 2026-10-15 (outcome PASS_WITH_OPEN_INPUTS; blocking per question)

- **New generate outcome `PASS_WITH_OPEN_INPUTS`** (exit 0): the workbook was
  written and every open line is non-blocking (`INPUT_NEEDED` only). The console
  prints an `OUTCOME` line with the counts (for NEEDS_ANSWERS too).
  `run_stages.OUTCOMES`, most severe first: CRASHED, FAIL, GATE_FAIL,
  NEEDS_ANSWERS, PASS_WITH_OPEN_INPUTS, PASS.
- **`CODEGEN_STAGES.json` lists every open line.** `questions: [{line, key,
  scope, blocking}]`:
  - `QUESTION` / `UNRESOLVED` are `blocking: true`. In the App these are
    "Answers needed" and the "required (blocking)" environment values.
  - `INPUT_NEEDED` is `blocking: false` (the App's "not blocking").

  Each generated feed's entry gains `written: true|false` and `open: {blocking,
  non_blocking}`.
- **NEEDS_ANSWERS (exit 3) = at least one blocking line open, whether or not a
  workbook was written.** A workbook with an empty storage account is not
  deployable, so the harness number never calls it a pass. Exit 3 as before for
  the unset required environment value (mock and live) and pair_12's
  `lob_by_file`; their workbooks are marked `written: true` so the App can still
  show them. One change: without `--feed`, a held-back feed's QUESTION used to
  leave the run at exit 0 (printed for information); it is now exit 3 too, with
  the ready feeds' workbooks written.
- **`run_stages.pair_outcome(steps, out_root)`** (STABLE; the post56 report
  noted it was missing). It returns a pair's outcome as the worst of its steps'
  exit codes. Generate's status comes from the manifest when the manifest's
  `exit` matches that step. `acfc_run.py`'s summary prints it as `outcome`.
  Test: `tests/test_open_inputs_outcome.py`.

## 0.5.8.post57 — 2026-10-15 (D1 post55 report: leak keys, unstated values, path whitespace, scorer)

From acfc-results `run_20261015T172048Z_3e09149` and the pair_01 scrubbed diff
(`run_20261015T193331Z_3e09149`). One commit each, synthetic fixtures only.

- **Answer keys name sheets by position.** All 10 post55 leak hits were sheet
  names inside `needed_answer_keys`. Every key on stdout is now
  `sheets[<i>]/<layer>/<role>` (0-based workbook position, like `feeds[<i>]`;
  the coordinates tier's `STTM sheet <i+1>`), band keys too:
  `sheets[<i>]/band[<n>]/layer`. The name stays ACFC-side: the answers
  template's `sheet_name:` reading aid and `unresolved_headers.md`. An answers
  file may give `sheet: "sheets[2]"` or the name; an unknown position is a NOTE,
  never applied elsewhere (`codegen.layout.sheet_refs`).
- **A value no document states is NEEDS_ANSWERS, not a FAIL** (pairs 03 / 04).
  A feed whose every mismatch is `value.unstated` exits 3 with one
  `QUESTION feeds[<i>].<field>` per value, citing the contract field and the
  places searched (vocabulary only); the other feeds of the pair still
  generate. `generate --answers` (gaps:) fills the value
  (`frd_unstated:<field> source_used:user`). Two documents stating different
  values stay a FAIL.
- **Stated paths** (pair_01's `derivations [path_whitespace 19]` all came from ONE
  FRD landing cell copied with its label, `Path : <account>/<container>/<folder>`):
  - *Label stripping.* An FRD cell `<Label> : <value>` whose label is a synonym of
    the field being read (conventions profile `field_label_synonyms`: landing
    path / folder / location, file name, frequency, delimiter) is read as
    `<value>`, flag `label_stripped` with the FRD table / row. A label that is
    not a synonym of that field is never stripped.
  - *The environment's address.* A landing that starts `<account>/<container>/`
    (the account matching the profile's `storage_account_pattern`) or an abfss
    URI takes account and container from the run's environment profile; the
    folder under the container stays the document's, byte for byte. A different
    document account / container raises `environment_mismatch` naming the field
    and "document states another environment" — never the document's value.
  - *Whitespace* (switch `path_whitespace: keep | fail`, default `keep`): a
    stated path keeps its whitespace byte for byte, and each path cell gets ONE
    flag `iig_path_whitespace:<SHEET>!<A1> (<COLUMN>) — double space | leading |
    trailing | tab` for the BSA to confirm; `fail` = the old check. On the
    pair_01 shape: the D1 address, one `label_stripped`, one
    `environment_mismatch`, zero whitespace flags.
- **iig_diff, four rules** (re-scored: pair_01 export 3.2 → 28.3, see
  `docs/acfc/iig_exports/pair_01_post55/RESCORE.md`):
  (a) an identity carrying a NAME (TGT_TABLE_NAME / TGT_TABLE / @file) that
  differs, both sides one feed and one flow: leftover rows pair by feed + flow +
  row order — the name is one mismatch cell; (b) agent-template columns the
  golden lacks are `template-only` (not scored, listed once under HEADERS);
  (c) `9999-12-31` == `9999-12-31 00:00:00`; (d) segment codes through the
  profile's new `segment_codes` (hddr / det / trlr == header / details /
  trailer). `tools/iig_rescore_export.py` re-scores a scrubbed export at home
  (the post56 scorer reproduces the export's 3.2 exactly on the rebuilt pair).
- **Extraction error lines say what kind of thing.** "STTM required element
  missing" / "STTM audit column invalid" now carry `(role <role>; type
  <keyword>)` — the header role in the template vocabulary and the type keyword
  in the framework type vocabulary, both allowlisted (`run_errors.ROLE_WORDS`,
  `TYPE_KEYWORDS`; anything else is dropped or `other`).
- **Not in this release:** pair_05 / pair_06's own fixes wait for Genie's answer
  on the segment-code vocabulary (rule (d) above).

## 0.5.8.post56 — 2026-10-15 (IIG cell counts per feed; one environment resolver)

- **IIG cell counts.** pair_11 (4 feeds) and pair_12 (1 feed) printed the same
  nine "unpopulated" numbers because the harness counted one workbook for both.
  Its metric (empty cells of each sheet's used range) matches the generator's
  own SD workbook exactly, so the counter was right but the file was wrong.
  Each feed now writes its own counts to `CODEGEN_STAGES.json`
  (`feeds[].iig_cells`; read them with `codegen.run_stages.iig_unpopulated(out_root)`),
  per sheet over the rows the generator wrote:
  - `open_for_bsa`: empty cells that the inputs panel asks about (an owed-cell
    or environment NOTE);
  - `empty_other`: every other empty cell;
  - `template_blanks`: the old number, kept for this release only.
  
  `open_inputs` lists the input keys behind the `open_for_bsa` cells. One
  input can leave several cells open (`run.email_to` on each status row), so
  cells ≠ inputs. The harness should read these per feed instead of scanning a
  workbook.
- **Environment resolution.** The App and the CLI share one resolver,
  `codegen.environments.resolve`. Precedence: explicit file >
  `<state root>/environments/<name>.yaml` > the overlay block > unset
  (INPUT_NEEDED, or a QUESTION for a required key). Every field records its
  source, and the picker shows it.
  
  The 10:07 mismatch came from where `codegen-state/` was looked up: next to
  the code. The App runs a staged copy with no `codegen-state/` (gitignored, so
  `databricks sync` skips it). New App setting **`CODEGEN_STATE_DIR`**: copy
  `codegen-state/` into the staged tree and point the variable at it
  (`docs/ACFC_APP_ENV.md`). The App logs `codegen-state root: …` at startup,
  with `[MISSING]` after any folder it cannot see.

## 0.5.8.post55 — 2026-10-15 (D1 post51 12-pair report: the extraction failures)

From acfc-results `run_20261015T074546Z_97fe673`. Each fix has a synthetic
reproduction of the pair's exact error line (`tests/post51_pairs.py`).
- **pair_05**: a Segment column of `NA` / `-` / blank no longer FAILs "outside
  the Header/Detail/Trailer vocabulary". New `extractor.discovery.
  unsegmented_markers` (`na`, `n/a`, `-`, `none`, `null`): a sheet whose Segment
  cells are only these (or blank) is unsegmented, with a contract note. The
  segmented path needs one real segment word, and a marker beside one still
  FAILs at its coordinates.
- **pair_06**: a flag / indicator audit column (`*_FLAG`, `*_IND`) may be
  `tinyint` / `int` / `smallint` / `boolean`; every other audit column stays
  `string` / `timestamp`. The sets are conventions-profile fields
  (`audit_datatypes`, `audit_flag_datatypes`, `audit_flag_suffixes`;
  `docs/acfc/OVERLAY_FIELDS.md`), so an overlay widens them. Framework DDL
  renders `DELETE_FLAG TINYINT`.
- **pairs 08–10**: F2 FRDs whose Solution Requirement tables carry no caption
  are now read. A table counts as one by its row labels (`extractor.frd.
  solution_requirement_labels` / `_required_labels` / `_min_labels`), with the
  caption as a second signal. `codegen layout` prints `NOTE frd/family — F2
  signal: <header-row fingerprint | caption> — table(s) [...]`. The section row
  is found when the caption row is missing, and labels may sit after a blank
  first column. An F2 feed whose tables name no section lists its required
  fields as unresolved, never an empty feed. "Cannot be read" now names the
  table COUNT and each table's header-row fingerprint (12 hex of `term_sha256`
  over row 0), never a title: `… at FRD: 12 tables, header-row fingerprints …`.
- **pairs 03 / 04**: the count-only mismatch summary (post52 / post53) is
  confirmed end to end: `contract mismatch, feed 1 of 1: 2 tables only in FRD`.
  It stays FAIL for now. The FRD carries no column list, so the set differences
  are tables / segments, and which kinds become NEEDS_ANSWERS waits for these
  two pairs' counts under post55.
- **pair_01**: the gate is unchanged. On a FAIL, the full report (ACFC-side)
  lists the flags grouped by type, and stdout prints `GATE_FLAGS <type> — n`.
  The pushed line carries counts only: `… (failed checks: derivations
  [path_whitespace 9]; flags by type: path_normalised 9, …)`. `GATE_FAIL.md`
  gains the findings-by-rule table and the D1 step to score the quarantined
  workbook (`tools/iig_diff.py … --export-scrubbed`).
- **pair_03 at 109 s**: no stage scales with the column count (a 330-column
  synthetic pair takes about 5 s under mock), and no model call runs per column.
  The MODEL USAGE line now carries the live calls' seconds (`· 2 call(s) in
  97.3s`), so the next D1 run shows which stage spent them.

## 0.5.8.post54 — 2026-10-15 (generate: CRASHED vs GATE_FAIL)

Two failure outcomes of the generate stage, exit code 1 for both
(`codegen.run_stages.OUTCOMES`; CODEGEN_STAGES.json `stages.generate.status`):
- **CRASHED** (an exception mid-write: a template gap, an uncaught error): the
  feed's partial emit files are deleted and the emit stages SKIPPED, as post52.
  An uncaught crash now writes the manifest before the error propagates.
- **GATE_FAIL** (files complete, the correctness gate said no): every file the
  feed wrote is KEPT, moved byte for byte to `<output>/<feed>/quarantine/` (same
  relative paths) beside a `GATE_FAIL.md`. That file lists the failed checks and
  the flag counts per type, with no names or values (those stay in the run's full
  report, ACFC-side). The emit stages report PASS, and the manifest says
  `generate: {status: GATE_FAIL, label: "complete, gate failed, review only",
  quarantine: [...]}`, with each feed's artefact paths under `quarantine/`.
  `tools/iig_diff.py` still scores the quarantined workbook: its build stamp is
  3 folders up, within the 5 it searches. Generating the feed again clears its
  old quarantine. Console: `GATE_FAIL      <feed> — complete, gate failed,
  review only: N file(s) moved to …`.
- **FAIL** (nothing written: a contract mismatch, no feed matching `--feed`):
  emit stages SKIPPED.
- The App's own generate path (`ui/backend/service.py`) does not quarantine yet;
  it can read the same outcome from `CODEGEN_STAGES.json` for CLI runs.

## 0.5.8.post53 — 2026-10-15 (addendum 4: derived values never reach the error line)

Feed slugs, work-dir paths and contract keys are generated, not harvested, so the
leak gate cannot see them. The coordinates tier (`first_error_line`) already
printed none (it is built from vocabulary + integers); post53 makes what it prints
for them useful:
- **Contract mismatch = counts on the first line**, e.g. `contract mismatch,
  feed 1 of 1: 2 tables only in FRD, 1 table only in STTM`. Every resolver
  mismatch item is tagged by kind (`resolver.mismatch_item`; labels in
  `run_errors.MISMATCH_LABELS`). Names count once, so three segments naming one
  table are 1 table. `ContractMismatchError.counts` rides the marker.
  The full message's first line carries the same summary.
- **A feed is `feed N of M`**: the mismatch coordinate now uses the original
  FRD feed object (the gap chain had replaced it, so it read `pair 1 of 1`).
- **A path is `<workdir>/pair_07/…`** (`run_errors.path_hint`: only a harness
  `pair_NN` folder survives), e.g. `contract not found: STTM <workdir>/pair_07/…`.
- Column names were already coordinates (the post52 raise-site audit).

## 0.5.8.post52 — 2026-10-15 (D1 post51 report: two defects + the pydantic addendum)

1. **Error lines: two tiers, coordinates only in the one a report carries.** The
   post51 report's 4 static-denylist hits were all document text inside
   `first_error_line`. `codegen.run_errors.first_error_line(returncode, stderr,
   stdout)` (same STABLE signature) now returns ONLY fixed vocabulary + integers:
   `FAIL            extract-sttm — STTM audit column invalid at STTM sheet 3 row 4
   col 11 [WorkbookParseError]`. New `first_error_line_full` (same signature) is the
   quoted line, for `codegen-outputs/` inside ACFC only. The CLI pairs every `FAIL`
   line with a `CODEGEN-ERROR {json}` marker on stderr (stage, reason code, `Coord`);
   118 raise sites in the STTM parser, FRD extractor, VDD reader, layout and generator
   attach their position via `run_errors.located(exc, Coord(...), reason)` (message
   text unchanged); an uncaught error gets a marker too. The harness phrases
   `contract not found:`, `no resolved feed matches --feed`, `produced no feeds`,
   `under gaps:` survive in the reason phrases. `scripts/run_round.py` prints the
   coordinates line (the quoted one stays in its work dir); `acfc_run.py` keeps both.
   **Harness side:** keep importing `first_error_line` for the report; write
   `first_error_line_full` only under `codegen-outputs/`.
2. **Emit stages SKIPPED, never PASS, after a failed Generate.** Pairs 03 / 04 / 07
   showed DDL / IIG / DML emit PASS with pair_02's exact unpopulated counts. A generate
   run where anything failed (contract mismatch, template gap, gate verdict FAIL, an
   uncaught error) prints `SKIPPED        <ddl_emit|iig_emit|dml_emit> — upstream
   stage generate failed`, deletes every emit artefact a failed feed wrote or rewrote
   (no partial workbook), keeps the exit code, and writes
   `<output root>/CODEGEN_STAGES.json` (`codegen.run_stages`, STABLE: stage statuses
   + the artefacts this run actually wrote, per feed). **Harness side:** read the
   emit-stage statuses and the workbook to count from `CODEGEN_STAGES.json`
   (`run_stages.read_stage_manifest(out_root)`), never from a glob of the output
   folder — it is shared across pairs, which is how pair_02's workbook was counted
   for pairs 03 / 04 / 07.
3. **The pydantic addendum (pair_07's error line was a warning).**
   a. `layout.model_confidence` is `LayoutConfig.placed_confidence` in Python (YAML key
      kept as alias) with `protected_namespaces=()` on the model; the App's
      `FeedRun.model_usage` (an API key, not renamed) gets `protected_namespaces=()`.
      `tests/test_d1_environment.py` fails on any unprotected `model_*` field at any
      pydantic version.
   b. A Python warning BLOCK is skipped whole: the head line, its continuation (blank
      lines inside the message included — pydantic's own message has one), through the
      indented source line; it ends early at a traceback / error / CLI-label / log line.
   c. Per stage, exit-code first: 0 (PASS) and 3 (NEEDS_ANSWERS) return `None` from
      both tiers — stderr is read only for a FAILed stage.
   The D1 pin set (pydantic 2.8.2, openpyxl 3.1.2, jinja2 3.1.6, pyyaml 6.0.1, ruff
   0.17.0, databricks-sdk 0.30.0) is `constraints/acfc_d1.txt` + §0 of
   `docs/acfc/ENVIRONMENT_ACFC.md`; the suite runs in the dev venv AND `.venv-d1`
   before a push. Under openpyxl 3.1.2 the byte-pinned `.xlsx` fixtures are compared
   cell by cell.

## 0.5.8.post51 — 2026-10-15 (D1 post50 follow-ups)

1. **Run errors: exit code first, warnings never the error** (904178e).
   `codegen.run_errors.first_error_line(returncode, stderr, stdout)` — a STABLE API
   for the harness report writer: exit 0 = no error whatever stderr holds; otherwise
   the first `Traceback` / `FAIL` / `ERROR` / `<Name>Error:` line, Python warning
   lines (and the source line under them) skipped. `scripts/run_round.py` and
   `acfc_run.py` use it. The noise is gone at its source: importing `codegen.config`
   printed two pydantic `UserWarning`s (fields named after BaseModel attributes);
   they are `thresholds` / `db_schema` in Python now, the YAML keys unchanged
   (`extractor.discovery.validate`, `dml.schema`). The CLI also ignores pydantic's
   own deprecation category. **Harness side:** import `first_error_line` instead of
   taking the first stderr line; the leak gate's stderr reading wants the same filter.
2. **Environment profiles D1 / A2 / PR** (a859b6e; QA / PROD renamed A2 / PR).
   Resolution: `--environment-file` > `--environment <name>` (else the default) =
   `codegen-state/environments/<name>.yaml` (outside the tracked tree) laid over the
   overlay block > INPUT_NEEDED. A REQUIRED value (`environment_schema.required`:
   storage account, containers) still unset is `QUESTION run.environment.<key>`,
   **exit 3** (was a non-blocking INPUT_NEEDED). The run banner / report header /
   RUN.md read `environment: D1 (complete, from codegen-state/environments/d1.yaml;
   selected)`. The DQ header / trailer location never formats a placeholder storage
   account. App: each profile's values prefilled and editable, required fields
   marked, "Other…" free text kept. **ACFC side:** put the storage account in
   `codegen-state/environments/d1.yaml` (`config/environments/example.yaml` shows
   the shape) — without it every D1 run now exits 3.
3. **Golden alignment, mechanism only** (5515376). The ACFC-side overlay
   `codegen-state/overlays/<profile>.yaml` (outside the tracked tree) is applied
   right after `acfc_env.yaml`; notebook names / paths / versions, the email status
   default + per-feed status sets, and per-feed SRC_FILE_NAME styles are set there
   (`docs/acfc/OVERLAY_FIELDS.md`; synthetic `config/overlays/example.yaml`). New:
   `notebook_path_prefix` (`/Workspace` in `acfc_env.yaml`), `email_status_default`,
   `feed_overrides.<feed_id>.{email_statuses, src_file_name}`, the `prefix_middle`
   wildcard style. The "dropped" stg_to_std notebook row was `iig_diff` giving both
   notebook rows no flow (the corpus `PROCESS_NAME` shapes matched no rule): two flow
   rules in `tools/iig_keys.yaml`. SRC_COLUMNS left naming and PIPELINE_DESCRIPTION
   row counts are open convention questions (`docs/acfc/OPEN_QUESTIONS.md`), untouched.
4. **Pre-push scrub gate at home** (f6d0412). `tests/test_tracked_scrub.py` scans
   every tracked file under `config/` + `docs/acfc/` and fails only on a (file, hash)
   pair not in the `docs/acfc/LEAK_LEDGER.md` baseline (18 rows = the 68 known hits,
   hashes only; regenerate with `scripts/scrub_check.py --rebaseline`).
   `codegen.term_hash.term_sha256` (strip, casefold, NFC, sha256) is the shared hash.
5. **`tools/hit_lookup.py`** (b95f39c): matches the gate's per-hit JSONL hash
   records against a local, gitignored candidates file — classification at home
   without a term entering git.
