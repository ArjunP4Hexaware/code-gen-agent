# CodeGen / Data Engineer Agent — working notes

## NEWEST — IIG validation (state as of 2026-10-14 night, `feature/multi-table`, post45)

Scoring the agent's IIG workbooks against prod "golden" IIG rows — pair_2 (SD) first, for Venu.
Deliverables: DDL / `metadata_inserts.sql` + the IIG workbook (runbook / playbook out of scope).

**Restart here (2026-10-14 night, post45).** The post44 report's six items
(`acfc-pairing-check` `2026-10-14_post44.md` + `patterns_post44/`) are DONE, one commit each,
marker **0.5.8.post45**. Owner rule for items 1–3 / 5: ONLY values `patterns.json` states;
anything it does not carry is a `<<D1:NAME>>` placeholder (`codegen.config.is_d1_placeholder`):
the cell stays OPEN with an `iig_d1_placeholder:` NOTE, never the placeholder text, and
`tests/test_d1_placeholders.py` FAILS on D1 (`CODEGEN_D1_RUN=1`, a Databricks runtime, or
`docs/acfc/iig_goldens/*.xlsx` present) while one survives — it lists all 25. Commits
(oldest first): e3689b0 patterns tool (pushed first, for D1), 0ec4558 items 1–3 (one
mechanism + one overlay block), fb19087 item 5, f12477c item 4, 46e5da4 item 6, 0c2c704
INPUT_NEEDED surfaces, then the notes + bump — intermediate commits not suite-run one by
one. **Verified at the head:** 1525 passed / 29 skipped (Python 3.11; the bundle test
passes once dist is committed); ruff clean on `src/ tests/ ui/backend/ tools/iig_diff.py
tools/iig_fill_rate.py scripts/run_round.py`; tsc clean, vitest 31; scrub: pre-existing
hits only (CLAUDE.md, acfc_env.yaml, ACFC_DEPLOY.md, test_derivations.py, build_goldens.py).
**D1 next:**
1. Run the extended patterns tool (e3689b0): `python tools/iig_fill_rate.py --corpus
   docs/acfc/iig_goldens <round2>/email_template_config_by_pipeline.csv --agent <outputs>
   --patterns <dir>` — per-flow breakdown (notebook name / path / process name, schedule
   description), the email STATUS x SUBJECT x BODY table on file-ingestion pipelines,
   `--top N`, framework vocabulary unscrubbed (`tools/iig_vocabulary.yaml`).
2. From it, Soham writes a D1 overlay (CODEGEN_CONFIG_OVERLAYS) replacing every placeholder
   (corpus_cells values per flow / status, the two extra STATUS rows, SENDER_EMAIL, EMAIL_TO,
   EMAIL_NOTIFICATION_URL, APPLICATION_NAME, the DQ split location's storage account).
3. Rebuild the goldens with `tools/build_goldens.py` (now keeps the grand master / master
   parents) and re-run pair_2 / pair_12; `iig_diff --dump-row` for pair_12's ADLS convention.
- **post45 mechanics.** `MetadataTemplateConfig.corpus_cells` {tab: {header: {value | by
  flow|status|frequency + values ("*" fallback; no entry = decided blank), share, todo}}} —
  NOTE `iig_corpus:` with the corpus share; never over an input-stated cell (FAQ / FRD / STTM).
  Row keys from `metadata_template._row_context` (flow = the pipeline role as the report
  names it: file_to_stg / stg_to_std / grand_master / master). `owed_cells` (ACTIVE_START_DATE
  -> FAQ companion `active_start_date`) are NON-BLOCKING: `codegen.owed_inputs` — `generate`
  prints `INPUT_NEEDED   feeds[<i>].active_start_date — …` (never QUESTION), exit 0, the
  workbook written with the cell empty, the item under `inputs:` in `answers_template.yaml`
  (output root; header "N open question(s), M input(s) needed"); `generate --answers` reads
  `inputs:` (`AnswersFile.inputs`, `faq.with_faq_answers`) and fills the cell. The feed
  report's header: "**Answers owed** — questions: N, inputs needed: M" (only when either > 0,
  so feeds owing nothing keep their bytes); the App: `status.inputs_needed` ->
  `InputsNeededBanner` (non-blocking, never the Answers-needed pause; dist
  `index-DqG-rduu.js`). NEEDS_ANSWERS = QUESTION / UNRESOLVED lines only (docs/ACFC_DEPLOY.md;
  harness doc on `acfc/harness-exit3` local commit 625617f, NOT pushed — with a6b8002, on
  Soham's word); `run_round.py` records INPUT_NEEDED keys and keeps going.
  ACFC overlay: email 4 rows per feed (Success, Failed + 2 placeholders), + EMAIL_NOTIFICATION_URL
  column; schedule gets the corpus's 28 columns, LAYER_NAME STAGE / STANDARD by flow,
  DAY_OF_SCHEDULE '0' only for Weekly, PROCESS_NAME / SUBPROCESS_NAME / SLA / UDF decided
  blank; `pending_cells` and the home-golden SUBJECT / BODY / notebook names are gone.
- **post45 DQ (item 5).** `dq_rules` kinds add_custom_columns (an audit row's load rule
  "Default to 'X'" — `AuditColumn.value_spec`, carried by `extract/generic.py` and
  `extract/segmented.py`; header / trailer feeds only), null_check (PK + not-null), referential_check
  (the STTM recycle lookup's column), and per STANDARD table lr_trim / std_date_conversion
  (a Date column; INPUT_PARAM open unless the load rule states the formats) /
  std_data_type_cast; `dq_rule_types`, `dq_params` (CAQH + SFMC golden formats),
  `dq_split_style: header_and_trailer` (SOURCE_COLUMN header '|' trailer, TARGET_COLUMN
  catalog,schema,table,location per table). G72 / G73 = NullCheckRule (pair_2 golden) and
  AddCustomColumnsRule (CAQH golden). iig_diff: `object_tables.by_rule_type` resolves a DQ
  row's OBJECT_ID on its leg's sheet (STDDelta -> STGDELTA). Home CAQH (mock, vs the real golden in
  Downloads): DQ 0 -> 54 / 54 paired (90.2), TOTAL 45.9 -> 75.8; the split TARGET_COLUMN stays
  open until the storage account is set.
- **post45 items 4 / 6.** `build_goldens._with_ancestors` keeps every PARENT_PIPELINE_ID
  ancestor of the pair's pipelines; iig_keys flow rules classify masters by description
  substring or name token (PL_GMSTR_ / PL_Gmstr_ / PL_MSTR_) — "group-level rows: N (not
  scored)" stays until the goldens are rebuilt. `iig_diff --dump-row [SHEET[:N] ...]`: one
  paired row's golden / agent / status per column (D1 only, console, withheld columns hidden).
- CLAUDE.md was 158k chars: the M15 / M9 / M8 / M7 history moved verbatim to
  `docs/CLAUDE_HISTORY.md` (pointer section "History moved out").

**Previous restart point (2026-10-14 evening, post44).** cd56673 is pushed; the head is the docs-only notes commit
after it (check `git status -sb` for whether it is pushed), marker **0.5.8.post44**. The post43 report's six
items are DONE (the post44 bullet below). Verified at cd56673: **1509 passed / 27 skipped**
(Python 3.11); ruff clean on `src/ tests/ ui/backend/ tools/iig_diff.py
tools/iig_fill_rate.py` (`tools/build_goldens.py` keeps 8 pre-existing findings); scrub: the
3 pre-existing hits only (CLAUDE.md, acfc_env.yaml, config.yaml — `document_title_phrase`),
none on post44's lines. **Waiting on D1 (nothing to do at home until it lands on
`acfc-pairing-check`):**
1. `python tools/iig_fill_rate.py --corpus docs/acfc/iig_goldens <path>/email_template_config_by_pipeline.csv --agent <run outputs> --patterns <dir>`
   → bring home the scrubbed `patterns.md`. It decides the 3b fills (APPLICATION_NAME,
   notebook PROCESS_NAME, DAY_OF_SCHEDULE — blank + `iig_pending:` NOTE until then), whether
   the emitter keeps writing grand master / master rows (item 5), and the corpus DQ classes.
2. Re-run pair_2 and pair_12 on post44: the `LAYER2 FAILED` / `RAW (D1 only)` lines give
   the still-unknown cause of pair_12's 5/5 Layer-2 failures; ADLS / STGDELTA projected
   ~99 / ~100 on pair_2 (from D1's per-column counts — RECYCL_RETN_DAYS 7 vs 30 is the open
   remainder); the `RULES (D1 only)` block for DQ.
3. Confirm with Soham: the D1 standard container `z-use-d1-dlk-std-01` (assumed by analogy
   with the stage container); RECYCL_RETN_DAYS.
DQ next (only once the corpus classes are in, see `docs/acfc/DQ_DIAGNOSTIC_2026-10-14.md`):
CAQH split rule SOURCE_COLUMN = header + trailer columns and RULE_TYPE Predefined;
AddCustomColumnsRule / ReferentialCheckRule; SD's STDDelta casts / trims.

**Previous restart point (2026-10-13, App demo day).** Working tree clean at 042b9fa, `HEAD:src` tree
`54a50fefb007`, marker 0.5.8.post36. The App on D1 deploys from `feature/multi-table` in the D1
Git folder; `docs/acfc/APP_DEMO_CHECKLIST.md` is the demo script, pinned to that tree and
version >= post36 (step 5: the run header badge must read `Output: Framework artefacts`).
**post35 was never pushed** — D1's annotated-column DDL came from post34 (9fb09c6).
- **post34 (9fb09c6) file_format:** an FRD ingestion-type phrase ("File Data Ingestion",
  `extractor.frd.format_tokens`) is no format — the file pattern's extension decides
  (`resolve/gapfill.py` `is_format_text` / `format_delimiter`; `layout/resolve.py`
  `_FeedGapFiller._file_format`, VDD FILES rows matched per feed by file pattern —
  `_own_vdd_rows`); flag `format_from_extension` printed as a NOTE. SD with the VDD: the only
  QUESTIONs are `feeds[0..2].frequency`; without it, exit 0 with three file_format NOTEs.
  Tests `tests/test_format_from_extension.py`.
- **post36 (042b9fa) — the D1 App failure `TemplateGapError 'LOB(Hardcod to MIDS)'`.** Cause:
  the App ran NOTEBOOK mode (config `output.mode: notebook`, toggles untouched); every scored
  round used `--output-mode framework`, whose render skips that gap check and wrote the
  annotated name into the DDL as a column. Fixes: (1) `src/codegen/extract/audit_names.py`
  (`split_audit_annotation`, `clean_audit_column`) used by all three STTM readers (generic,
  legacy `MAPPING-`, segmented) — the contract carries `LOB`, flag
  `audit_column_annotated:<key> <cell>: … (value 'MIDS')`; the emitter is unchanged.
  (2) `output.profile_mode: {acfc_prx: framework}` + `OutputConfig.default_parts()` — the App
  (`ui/backend/demo.py::effective_output_parts`) defaults to framework for acfc_prx; the CLI
  default stays notebook. `ModesPage.tsx` shows an `Output: …` badge and warns "notebook not
  validated for acfc_prx" (dist `index-BdZrOxwQ.js`). (3) `src/codegen/gate/ddl_names.py` +
  `scripts/run_round.py` stage `## DDL sanity` after the CLI: a column identifier not
  `^[A-Za-z_][A-Za-z0-9_]*$` = exit 1, named. Tests `tests/test_audit_annotation.py`, a DDL-gate
  test in `tests/test_run_round.py`.
- **post38 — the D1 pairing-check report's four fixes** (`origin/acfc-pairing-check`
  `codegen-outputs/pairing_check/2026-10-13_pyx_caqh.md`, read in place):
  (1) **family E, a file per sheet** — `split_frd_feeds_by_sttm` now splits when the sheets
  SHARE the FRD's one table; sheets whose feed names would collide are named per sheet
  (`sheet_feed_label`: own `File Name` row, extension + date tokens dropped, else the sheet
  name; flag `feed_names_per_sheet`), the sheet's own file is its pattern; the generic
  extractor's `_match_feed` tries the sheet's own file row, then a feed named after the sheet,
  and two sheets on one FRD feed are a NAMED error (never pydantic's "duplicate feed_id").
  Unique names stay as they were. Fixture `tests/acfc_shapes/family_e_multi.py`, tests
  `tests/test_multi_sheet_feed_ids.py`. (2) **ONE provider switch** `codegen.reasoning.mode`:
  `--provider` > `CODEGEN_PROVIDER` > `reasoning.mode` > mock; never inferred from
  DATABRICKS_HOST / the App markers / an endpoint (`resolve_transport` no longer overrides by
  runtime); live that cannot run = ONE startup line (CLI `FAIL provider —`, App
  `startup_error`); `provider=<mode> (<source>)` on the CLI first line, doctor, /api/health and
  every mock reason. ACFC sets live in `app.yaml` + `acfc_run.py` + `scripts/run_round.py`
  (`--provider`, default live; no `--dry-run`, every `CODEGEN_FORCE_MOCK_*` cleared; RUN.md's
  Build section names it); the recipes `docs/acfc/GENIE_RUN_pair_2*.md` show
  `CODEGEN_PROVIDER=live` without `--dry-run`; the harness jobs (in D1) are Soham's.
  `--dry-run` under live = `WARNING provider=live overridden by --dry-run → mock` as the FIRST
  line of the run AND of the report (+ mock reason, flag `provider_overridden:`). Test guard: conftest sets
  `CODEGEN_BLOCK_LIVE_MODEL`; `guard_live_call` (a BaseException) at every real connection
  unless `CODEGEN_ALLOW_LIVE_TESTS=1`. Serving model **Claude Opus 5.5**
  (`claude-opus-5-5` / `databricks-claude-opus-5-5` — confirm the endpoint exists in D1).
  Tests `tests/test_provider_mode.py`, `tests/test_transport.py` rewritten.
  (3) **iig_diff like with like** — `FeedScope` (`--scope feeds` default): an unpaired golden
  row naming another feed of the group and none of the agent's = `out-of-scope`, not missing;
  a one-sided sheet = `sheet not in <side>`, score None; iig_v1 / iig_v2 detected + a note (post41: inform only);
  overall `score` unchanged in meaning, `comparable_score` over scoped shared-sheet cells;
  duplicate-key warnings name the values. (4) `codegen pair` lists EVERY file (the STTM,
  lock files) and NOTEs `pair.sttm` when a folder holds 2+ STTMs with no override pinning one
  (App: outcome `notes`; `acfc_run.py`: the override pins one, else it stops naming them);
  a `name_fuzzy` NOTE in the content branch carries the stem words.
- **post40 — iig_diff pairs rows by IDENTITY, not by generated names** (`acfc-pairing-check`
  `2026-10-13_pair2_diff.md`: SD pair_2 0.0, zero rows paired — goldens `PL_File_<DOMAIN>_<PKG>_<FLOW>_Incr`,
  agent iig_v1 `WF_DLK_NSP_…` / `NB_…`; ALL_FILES_STATIC_INFORMATION stripped by hand to dodge
  a 600 s timeout). Default `--pair-mode identity`: golden rows get feed + flow from
  `docs/acfc/iig_goldens/01_pair_group_index.csv` (GROUP_ID / PIPELINE_ID → flow_type +
  matched_table, matched to the agent workbook whose name / TGT_TABLE_NAME it is; a feed the
  agent did not write = out of scope); agent rows: workbook = feed, flow from the sheet or
  LAYER_NAME / PIPELINE_DESCRIPTION / PROCESS_NAME (`iig_keys.yaml flow`). Per-sheet `identity`
  in `tools/iig_keys.yaml` (schedule / notebook = feed × flow; ADLS / STGDELTA + TGT_TABLE_NAME;
  DQ = feed × @table × SOURCE_COLUMN × RULE_CLASS; email + STATUS; ALL_FILES = FILE_NAME), values
  normalized (case, separators, a table's schema prefix); a component one side never states is
  dropped + warned; an incomplete identity = unpaired + said. No identity → position only when
  counts are equal, else unpaired + said. `convention_columns` (PIPELINE_NAME, notebook names,
  TEMPLATE_NAME, TGT_RJT_TABLE_NAME) never pair, never score: status `convention`, counted with
  how many differ. Every sheet reports paired by identity / position / unpaired. `--pair-mode
  key` = the old natural-key rule. Speed: diff.xlsx called `ws.max_row` per cell (64 of 72 s at
  3,000 rows) and FeedScope compared every row with every stem (`StemIndex` now) — the
  D1-sized CLI runs in ~8 s. `tools/iig_identity_check.py` (counts only) self-pairs goldens by
  identity — run it over the 199-IIG corpus on D1 (only the SFMC / pair_1 / CAQH goldens are
  at home: every row identified). Note: post38's `WF_` / `NB_` names came from
  `--iig-template iig_v1`, not the live model. Tests `tests/test_iig_diff_identity.py`.
  **post41:** the iig_v1 / iig_v2 `HINT` is now an inform-only `NOTE` (score.json
  `templates.note`) and never recommends a template switch: iig_v1 also changes the naming
  convention (`WF_` / `NB_` vs `PL_File_`). ACFC default stays iig_v2 —
  `docs/acfc/IIG_TEMPLATE_DEFAULT.md`.
  **post42 — cross-template sheet:** `iig_keys.yaml sheet_aliases` (replaces the hard-coded
  round-3 `TEMPLATE_ALIASES`): a v1 golden `ALL_FILES_STATIC_INFORMATION` (one row per FILE)
  vs the v2 agent `FILE_ADLS_INGESTION_DETAILS` (one row per FEED, no file column) is ONE
  sheet `ALL_FILES_STATIC_INFORMATION → FILE_ADLS_INGESTION_DETAILS`; a golden file row pairs
  with the FILE_ADLS row of the agent feed whose ADLS_DELTA `SRC_FILE_NAME` is that file
  (`file_identity` + `file_name_tokens`: case, separators, extension, CCYY_MM = YYYY_MM = `*`;
  many golden files → one feed row), scoped by FeedScope; only the shared headers are compared
  (`columns`: OBJECT_ID, domain, subdomain, CREATED_DATE, UPDATED_DATE — only domain /
  subdomain scored), the rest `not_comparable` per side (score.json + console). Applies only
  when neither side has the other's sheet. Tests `tests/test_iig_diff_sheet_alias.py`.
- **post43 — the identity-diff report's four items** (`acfc-pairing-check`
  `2026-10-13_identity_diff.md`; one commit each + the Opus 5.5 labels):
  (1) **live layout JSON** — `layout/model.py` `parse_json_response` (fences, a preamble,
  the outermost balanced object, never a nested one) + `ask_for_json` (one retry with
  `RETRY_INSTRUCTION` "Respond with JSON only, no fences"); every rejected response logged,
  first 500 chars, D1-only: stderr `RAW (D1 only)` + `<runtime cache>/rejections/<fp>.raw.json`.
  Tests `tests/test_layout_json_response.py`. (2) **Pyx questions** (synthetic
  `family_e_multi.build_sttm_reports` / `build_frd_reports` reproduce D1's 22 → 0):
  a metadata sheet (`extractor.discovery.metadata_sheet_names`, or no role resolving while
  other sheets map) is kind `table_details`, never a feed; FRD "Text files"
  (`extractor.frd.generic_text_formats`) + a csv / psv / tsv / txt extension → the extension,
  `format_from_extension` NOTE; files per sheet: one candidate per FILE (`file_identity`),
  then `best_file_matches` (sheet title + File Name row + label vs the files, Jaccard, words
  shared by all sheets / files dropped) → unique best = NOTE "best name match", a tie =
  QUESTION naming the tied files; `answers_template.yaml` beside `--out` whenever answers
  are owed (layout `--require-complete` starts it, extract-sttm adds; empty entries are
  skipped by `load_answers`). Tests `tests/test_pyx_questions.py`. (3) **iig_diff** —
  scrubbed `sheets.md` (per-sheet table with missing / extra + per-column breakdown,
  template headers verbatim), score.json `column_counts` + `file_samples`, console
  `FILE NAMES (D1 only - unscrubbed)`; pair_12's 0 rows = a CAQH inventory name with a date
  FIRST and a wildcard INSIDE vs the agent's prefix-star SRC_FILE_NAME: `file_identity` now
  drops date / wildcard tokens wherever they sit. (4) **corpus fill rate** —
  `tools/iig_fill_rate.py` (GAP = corpus >= 90 %, agent not; assigned = needs_assignment +
  always_blank); ACFC overlay `derived_cells` (shapes over {source} {layer} {outcome}
  {notebook} {pipeline} {sender}; one `iig_derived` NOTE per column) fills notebook
  PIPELINE_NAME / PROCESS_NAME / NOTEBOOK_PATH, schedule APPLICATION_NAME, email
  TEMPLATE_NAME / PROCESS_NAME / SUBJECT / BODY / SENDER_NAME (dbo) / SENDER_EMAIL
  (`job.notification_sender`, env `CODEGEN_NOTIFICATION_SENDER`). The 199-IIG corpus is
  D1-only: measured over the 3 home goldens (SFMC, pair_1, CAQH) — 11 gaps → 1
  (ACTIVE_START_DATE, a go-live date). `docs/acfc/IIG_FILL_RATE_2026-10-13.md`; tests
  `tests/test_iig_fill_rate.py`. Run the tool on D1 over `docs/acfc/iig_goldens`.
- **post44 — the post43 report's six items** (`acfc-pairing-check`
  `2026-10-14_post43.md`; one commit each): (1) **Layer 2** — both live providers ask
  through `reasoning/providers/ask.py::ask_candidate` (post43 `parse_json_response`, one
  `RETRY_INSTRUCTION` retry, a response that `TRUNCATED` = "ends inside the JSON object"
  retried with `reasoning.truncation_max_tokens` 32000); every failed attempt an
  `AttemptFailure` on `provider.failures`, logged by `reasoning/raw_log.py`
  (`LAYER2 FAILED` reason, `RAW (D1 only)` 500 chars, the max_tokens NOTE;
  `<state>/rejections/layer2_<feed>.raw.json`); `StageUsage.recovered` / `all_failed` -> a
  `> **WARNING**` report header + console line. Tests `tests/test_layer2_failures.py`.
  (2) **iig_diff identity `@file`** (`iig_keys.yaml file_columns`) splits ONLY rows the
  other components leave equal (CAQH: 18 ADLS rows, one table); `file_name_tokens` drops a
  trailing run of 2+ one-character segments (CAQH `_P_I_1_T`) — home CAQH ADLS and
  ALL_FILES -> FILE_ADLS 18 / 18 paired. (3a) `iig_fill_rate.py --patterns DIR`: scrubbed
  `patterns.md` / `.json` (dominant value + slot pattern {table} {schema} {domain} … per
  column, DAY_OF_SCHEDULE per PIPELINE_FREQUENCY, master rows per GROUP_ID, DQ rule
  classes), re-scanned with scrub_check. (3c) sheets match case / separator-blind, a header
  row may sit under a title, `.csv` table exports (suffix allowed); the 199 per-pair
  workbooks carry NO email sheet — build_goldens reads `email_template_config_by_pipeline.csv`.
  (3b) `pending_cells` (blank + `iig_pending:` NOTE, never over an FAQ value): schedule
  APPLICATION_NAME / DAY_OF_SCHEDULE, notebook PROCESS_NAME; ACTIVE_END_DATE
  `9999-12-31 00:00:00` (the corpus's datetime). (4) ACFC overlay: FILE_HEADER_FLAG by
  format (`file_header_flag_by_format`: delimited Y / fixed-width N), ADLS FILE_METADATA
  (the prod 55th column; `deliberate_blanks` -> NULL in the SQL), STGDELTA containers
  stage in / std out (constants, the offer retired), `data_type_style: full`
  (`String:Decimal(10,2)`). Tests `tests/test_iig_cheap_misses.py`. (5) iig_diff status
  `group-level` (`group_level_flows`: grand_master / master agent rows the golden lacks) —
  "group-level rows: N (not scored)". (6) DQ diagnostic only: `component_overlap` per
  identity sheet, `RULES (D1 only)` block / `rule_samples`; `docs/acfc/DQ_DIAGNOSTIC_2026-10-14.md`.
- **post39 — the live D1 check's four fixes** (`origin/acfc-pairing-check`
  `codegen-outputs/pairing_check/2026-10-13_live_three_pairs.md`; one commit each):
  (1) **pair_12 CAQH** — `frd_docx.split_domain_labels`: a cell with a `Domain:` AND a
  `Sub Domain:` label (any case / separator) → DOMAIN + SUBDOMAIN, flag
  `frd_domain_labels_split:`; every IIG payload cell made single-line at the emitter
  boundary (`gate/derivations.normalise_iig_line_breaks`, flag
  `iig_line_break_normalised:<SHEET>!<A1>`); gate check `iig_single_line` over the WRITTEN
  config_rows / `_IIG.xlsx` fails with `<file> <SHEET>!<A1> (<header>)`. Real CAQH (mock):
  22 × Member / Third Party Liability, PASS_WITH_FLAGS. (2) **pair_11 Pyx** — the harness
  handed extract-sttm a ONE-feed FRD contract (extract-frd's); extract-sttm now splits it
  per mapping sheet by the layout rule (`layout/resolve.split_single_frd_feed`,
  `split_frd_feeds_by_sttm(force=True)`; the layout stage forces it too for content
  strategy), records `SttmContract.frd_split` (absent when unused), and generate joins it
  (`resolver.apply_frd_split`); NOTE `frd.split`. Live layout answers are SALVAGED
  (`salvage_layout_answer`): one REJECTED line per schema error, null role = not found,
  valid sheets / bands kept and workbook-validated; `--report-unresolved` lists them. The
  real Pyx shape is still unseen here — the synthetic family-E fixture stands in.
  (3) **iig_diff** — `key_samples` (first 5 golden vs agent keys, console + score.json, D1
  only) and a SEPARATE `positional` score (key-unpaired rows paired by position when the
  counts match, else best cell overlap); key-paired score + scrubbed export unchanged.
  (4) **App deploy** — nothing needs `out/` (`tests/test_deploy_without_out.py`); deploy
  from Git or keep harness outputs under `/tmp` (`docs/acfc/APP_DEPLOY_NO_OUT.md`).
- **post37 — pairing by NAME ROLE + token key (the Pyx pair_11 failure).** The App's
  `local_frd_candidates` and `codegen pair` took a `.docx` as an FRD only when its name
  STARTED with "frd" (`Pyx_ … DSNP_FRD.docx` was never a candidate), the name rule was the
  first three tokens, and the same-folder rescue attached an IIG golden as the VDD. Now:
  `demo_sources.classify_document_name` (a role token ANYWHERE; `iig` always = IIG, never an
  input; two roles → the prefix decides + NOTE), `pairing_key` / `match_by_name` (exact key →
  `name_key`; else a unique whole-word-stem Jaccard ≥ `inputs.pairing.name_fuzzy_threshold`
  0.8 → `name_fuzzy` + NOTE naming the stem-matched words; below → QUESTION, `codegen pair`
  exit 3). A VDD candidate needs a `vdd` token or the index's positive dictionary verdict
  ("VDD by content: <file>" NOTE → outcome `notes`, run flag `pairing_note:`); the same-folder
  rescue applies to a confirmed dictionary only. Pairs override file
  (`pairing_overrides.yaml|yml|json` in an input folder, `--pairs-file`,
  `inputs.pairing.overrides_file` / `CODEGEN_PAIRING_OVERRIDES`) wins over everything
  (`rule: override`); `InputCatalog.every_document` (no name dedupe). The pairing outcome
  carries `folder_roles` (every file of the STTM's folder, role + rule) and `considered`
  (every document of the kind, its name score, why it is not a candidate); dist
  `index-DGsprVYN.js`. Tests `tests/test_pairing_name_key.py` (incl. pair_11 end to end on
  local folders AND the fake workspace backend). Storage path audit: nothing strips / splits /
  quotes a segment; the SDK quotes Files API URLs, the Workspace API takes `path` as a
  parameter (`clean_rel` strips only the ends of the whole rel — not this shape).
- **Verified at 042b9fa:** 1360 passed / 28 skipped; ruff, tsc clean; vitest 29. SD invariant
  (home, mock) 47 / 47 / 45 matched, diff 1 / 1 / 3 — unchanged by post36. App (nothing POSTed
  → framework) vs CLI: `framework/` + `ddl/` byte-identical, mock AND live
  (databricks-claude-opus-5, profile DEFAULT; only `candidates.json` differs live); the IIGs
  equal post33's; 16 DDL files / 1,735 column identifiers / 0 with "(". A double-POST of the
  same workbook answers 200 `joined`.
- **The home SD documents:** the home STTM (60,905 B) has anonymized ColumnName columns; D1's
  (61,141 B) is the reference. The SD VDD is only in the user's Downloads folder; its FILES!C2:C4
  say "Delimited text" (D1's reportedly `csv`). Session scratch scripts (`drive_app.py` App HTTP
  driver, `cli_ref.py`, `sd_run.py`) died with the session — rebuild from the checklist.
- **The round-8 brief (was ON HOLD for the demo):** DONE in post44 — Decimal(10,2) precision,
  the STGDELTA containers (constants stage in / std out, not a QUESTION). Still open: drop Q8;
  RECYCL Q3; ALL_FILES layout; EMAIL_TEMPLATE_CONFIG (the corpus email CSV — D1 item 1 above).
- Commits post30 → post33 (oldest first): a7f98fc `run_round.py` (post31/32), 28d3abb iig_diff
  environment tokens, df0e1a7 STGDELTA paths, b9a10c8 SD-family flags, e90562d `_MI` OBJECT_NAME,
  0891329 EMAIL_TEMPLATE_CONFIG export, fff4f57 post33 + `GENIE_RUN_pair_2_r7.md`, 1cd5574 the
  demo checklist.

- **D1 runs, home reviews.** The prod goldens exist only on D1 (`*.xlsx` + the 860a798 ignore
  lines keep them off origin; unscrubbed prod rows — never force-add them). Genie runs
  `docs/acfc/GENIE_RUN_pair_2_r5.md` in the D1 Git folder and pushes scrubbed evidence to
  `acfc-results` (`codegen-outputs/iig_validation/round<N>/pair_2/`); this checkout reads it
  in place (`git show`), never checks it out.
- **D1's SD STTM is the reference (accepted after round 6):** the home copy differs only in its anonymized stage / standard `ColumnName` columns (compare.txt: J, O / K, P) — column-dependent fixes (SRC_DATA_TYPE precision, DQ column lists) are unit-tested here, verified on D1 only.
- **Build identity (99f262b):** `codegen.build_info.build_identity()` — git → the deploy stamp
  `src/codegen/_build.py` (`scripts/stamp_build.py`, never committed) → `CODEGEN_BUILD_SHA` →
  the src tree id — names commit / branch / commit time on the CLI's first line, `codegen
  doctor`'s `build …` line and `GET /api/health`. `codegen generate` writes
  `<output root>/CODEGEN_BUILD.json`; iig_diff refuses an agent workbook without one within 5
  folders above it (`unscored: agent workbook has no build identity`).
- **Pushing:** once per clone `git config core.hooksPath scripts/git-hooks`. `pre-push`
  refuses a code push to `feature/multi-table` / `feature/iig-first` with an unchanged
  version, a requirements marker ≠ pyproject, a tracked `_build.py`, or `ui/frontend/src`
  changed without `dist` (1f7316f, b06ce1f). Bump: `python scripts/bump_version.py`. Docs-only
  pushes need no bump.
- **409 fix (53468c2):** `POST /api/demo/workbook` for the workbook already being selected =
  200 + that job (`joined: true`); another workbook is still 409; a job older than every step
  budget is replaced; a job always ends.
- **`tools/iig_diff.py` + `tools/iig_keys.yaml`:** rows paired by natural key only (4ba59b9;
  `--pair-mode` still parses — never use it for a score). Cell statuses exact / normalized /
  mismatch / missing-in-agent / extra-in-agent / needs_assignment. The agreed ignore set =
  `needs_assignment` in iig_keys.yaml (INVENTORY / OBJECT / PIPELINE / GROUP_ID, the connection
  ids, the audit stamps; every other `*_ID` IS scored), printed in each report header;
  CREATED_BY / UPDATED_BY values withheld. `--agent` takes every feed's `*_IIG.xlsx` (not
  `*_REVIEW`), scored as their union (5e3df10). `--export-scrubbed DIR` → mismatches.md /
  row_keys.md / SELF_CHECK.md with G<n> / A<n> tokens, a re-scan must find 0;
  `--golden-structure` describes the golden's shape (d8cb519). score.json / diff.xlsx /
  routing.csv carry prod text — never committed.
- **`tools/build_goldens.py` (28fd6d2):** each sheet de-duplicated across the GROUP_ID exports
  on the non-ignored columns; `_source_group_ids` lists the contributing exports (never
  scored, shown in row_keys.md); one `dedup before -> after` line per sheet. Pre-existing,
  not ours: 8 ruff findings + 2 scrub hits (SFMC GROUP_IDs).
- **Blank Schema / TableName in an STTM band (581d235):** the feeds are split on the mapping
  sheets (`layout/resolve.py::_blank_sheet_targets`); the schema comes from the FRD when it
  states one, with a NOTE (`sttm_target_from_frd`), else it is a QUESTION; table names are
  always a QUESTION — never derived. A blank-cell copy of the real SD STTM owes 14 QUESTIONs
  (6 schema, 6 table, 2 file): its FRD's Target Schema is a per-file-group list.
- **Round gate (post30):** `python scripts/doc_fingerprint.py --compare
  docs/acfc/fingerprints/pair_2_sd_home.json <D1 fingerprint>` — exit 1 on a HARD line (sheet
  names, counts, extents, merged ranges, header row + hash, per-column fill, the docx
  `text_hash` + counts) = STOP; WARN (whole-file sha256 / size, document.xml, `body_hash`,
  per-column value hashes) is recorded, the run continues. Value hashes are HMAC under the
  gitignored `codegen-state/fingerprint.key` (post31; same key both sides, else REFUSED).
- **Round 4 (not a clean run):** TOTAL 4.6; ADLS 33.5 / STGDELTA 31.7 with 2 of 3 rows paired.
  The golden was 6× duplicated on the unfiltered pair-wide sheets (now de-duplicated), and the
  run used a hand-split contract and the blank-cell STTM.
- **Round 5 ran on the blank STTM** (Genie chose the input). **Round 6 = `scripts/run_round.py`**
  (post32; `docs/acfc/GENIE_RUN_pair_2_r6.md`): the inputs come from the gitignored
  `codegen-state/round_inputs/pair_2.yaml`, no answers file, gate → CLI → golden → diff → RUN.md
  → scrub (exit 2 gate; 3 layout asks / scrub hit; 1 a stage). Then: only name / description columns differ →
  anonymization; Schema / TableName / file-pattern columns differ → the home SD invariant
  (mock 43 / 43 / 46, diff 0) was measured on another copy. DQ rules: not implemented.

## START HERE — branch `feature/multi-table` (state as of 2026-10-09, early morning — after the overnight robustness run)

**Where things stand.** Four live branches, all pushed, nothing merged
anywhere (staging / main untouched):

| Branch | Head | Version | What it is |
| --- | --- | --- | --- |
| `feature/multi-table` (this checkout) | **this notes commit** (on 5cbaf63) — **PUSHED 2026-10-09 on Soham's word** (29 commits since 1ecbacd) | 0.5.8.post26 | cut from `feature/iig-first` at be38f05: the multi-table IIG model + `metadata_inserts.sql`, the first-ACFC-run fixes, the real-row scorecard rules, the exit-code / answer-line contract, then the **2026-10-09 overnight robustness run** (below). **Not yet re-run in ACFC** |
| `acfc/harness-exit3` | **9cba013** on origin; local **a6b8002** (the `band[n]` key form, NOT pushed — Soham pushes it with the Genie-side regex change) | docs only | `docs/acfc/HARNESS_EXIT_CODES.md` — the ACFC harness's (codegen-watch / pull_and_run, NOT in this repo) exit-code + answer-line contract. **Genie implements the harness from this doc**; ACFC-side commits land here too (517919c was theirs) — `git fetch` and fast-forward before editing (edit in a scratch worktree, never switch this checkout) |
| `feature/iig-first` | **be38f05** | 0.5.8.post13 | the stable demo branch `codegen-watch` pulls — **do NOT merge `feature/multi-table` into it until after the Friday 2026-10-09 session, and only on Soham's word**. Its notes (next section) still apply |
| `backup/ddl-only` | **4acec93** | 0.5.8.post5+ddl2 | DDL-only demo fallback (next section) |

**Overnight 2026-10-08 → 10-09 (read `docs/acfc/OVERNIGHT_2026-10-09.md` first).**
Robustness to unseen documents, four chunks + an addendum, all local:
- **Chunk A** — STTM target bands located by their LABEL GROUP anywhere in the
  header row; a band's layer ONLY from evidence (answer > band title > header
  word > Catalog values PR_DLK/PR_STD > Schema prefix stg_ > elimination;
  "in DL"/"DLK" OFF — `extractor.discovery.layer_evidence`); a band nothing
  names = `UNRESOLVED <sheet>/band[<n>]/layer` (answers: `{sheet, layer:
  band[n], role: layer, value: source|stage|standard}`), its feed held back;
  value-derived layers re-derived on every cache hit; classifier = STTM only
  with target-layer evidence ("unclassified — confirm" otherwise). Pass 1 (the
  old band-row reading) wins when it agrees, pass 2 only when pass 1 finds no
  mapping sheet — every pinned profile byte-identical. `MAPPING-` sheets read
  by the GENERAL reader first, proven equal to the legacy reader on every
  fixture (`tests/test_mapping_general_first.py`); legacy text only at
  `parse_workbook`. `docs/LAYOUT_RECOGNITION.md` "Band location by label group".
- **Chunk B** — six cold pairs (`fixtures/acfc_shapes/cold/`, designed blind to
  the reader) + the generator fixes they forced (pass-3 candidate sheets,
  prose FRDs, held-back instead of FAIL, answer ROUNDS in layout /
  extract-sttm, FRD format-cell delimiter, `feeds[i].audit_columns`, …);
  `tests/test_cold_pairs.py` pins every owed line and that answers complete.
- **Chunk C** — the App: run state `needs_answers` with an inline answer list
  + `POST /api/demo/rerun-with-answers`; band questions answerable in the
  dialog; every error a readable card (JSON: type, `where`, health line).
- **Chunk D** — `metadata_inserts.sql` table names via `dml.table_names` (STGDELTA →
  `stg_delta_stddelta_ingestion_details` confirmed from Soham's brief; the
  rest `-- unconfirmed` + Friday 12); STGDELTA row paths container-relative,
  OBJECT_ID per (group, file) with notes, SRC_CONTAINER_NAME left OPEN (offered
  candidate only); `acfc_env.yaml` makes acfc_prx + iig_v2 the defaults and the
  CLI's first line / `codegen doctor` name the active profile + template.
- Every chunk independently reviewed; every verified finding fixed (one commit
  each). Decisions left for Soham: the report's "Decisions for you" (1–5).
- **Elimination (owner rule, 5cbaf63):** source by elimination ONLY for the one
  band left over, with no evidence, LEFT of both evidenced target bands, while
  source is unclaimed — a layout `NOTE <sheet>/band[n]/layer … layer by
  elimination`; any other leftover stays `UNRESOLVED`; never trusted from cache.

Working tree clean after the overnight report commit. Before tonight: the last four commits
before it are Soham's own from the ACFC side (2026-10-08 17:16–18:12 UTC):
6f14a2d `app.yaml` ACFC env block (the four storage paths are SET on this
branch now — `CODEGEN_EXTRA_INPUT_DIRS` / `_STORAGE_INPUTS` / `_STATE` /
`_OUTPUTS` under a workspace user folder; `CODEGEN_CONFIG_OVERLAYS` dropped,
`acfc_env.yaml` loads anyway), adac4ec / bb5fa55 / 51103de review
deliverables of a real SD feed force-added under `docs/acfc/review/` (DDL,
metadata_inserts, config_rows / config_inserts, IIG + IIG_REVIEW; scrub-clean
at 51103de; client-derived — read in place, never quote names). Others can
push here: `git fetch` before work and rebase, never force. Gitignored here
(local only, never stage): `docs/acfc/denylist_local.txt`, `PROJECT_HANDOFF.md`,
`CODEGEN_INDEPENDENT_REVIEW.md`. Stage files explicitly — never `git add -A`.
The real client SD documents + `IIG test cells.xlsx` sit at the repo root
(gitignored / tracked-before-policy): read in place, mock runs only, outputs to
a scratchpad, report SCORES only — never copy names into the repo, commits or
replies.

**FIRST, pick up here (pending, in priority order):**
1. **Friday 2026-10-09 working session with the framework owners** — brief
   `docs/acfc/FRIDAY_2026-10-09.md`; checklist `docs/acfc/MULTI_TABLE_DESIGN.md`
   §7a: 1–5 open questions, 6–8a which family convention is current for new
   feeds, 9–10 sheet vs walkthrough (ACTIVE_FLAG Y/S, DAY_OF_SCHEDULE 0/NULL —
   cited BY NUMBER in `metadata_inserts.sql` and its tests; never renumber),
   **11 (confirm, not ask): "FREQUENCY = run cadence, delivery cadence noted —
   correct?"** Most answers land as CONFIG (`catalog_map`,
   `constants.STGDELTA_STDDELTA_INGESTION_DET`, `family_conventions.*`,
   `dml.db_value_map`, `dml.db_null_columns`). Record each answer in §7a.
   NEW tonight: items **12** (the unconfirmed metadata-DB table names) and **13**
   (STGDELTA source path form, the offered stage container, OBJECT_ID per
   file vs per table), plus the report's "Decisions for you".
2. **Re-run the real documents in ACFC on 0.5.8.post26** (the harness pairs;
   push first — on Soham's word).
   Expectation from a local MOCK run of the real SD pair: all three SD rows
   diff 0 (demographic / community-risk matched 43, individual-risk 46); the
   3 RECYCL cells of the two recycle-less feeds are OPEN (Engineer-confirm) by
   design ("never an asserted N"). Re-run recipe (scratchpad scripts are gone
   with the session — rebuild): layout --frd-contract-out --answers (the one
   open question: `gaps: feeds[1].file_name_patterns` = the community-risk
   file) → extract-sttm → generate `--output-mode framework --profile acfc_prx
   --iig-template iig_v2 --skip-tests --dry-run`, env PYTHONUTF8=1,
   CODEGEN_FORCE_MOCK_LAYOUT/PROVIDER=1, CODEGEN_STORAGE_OUTPUTS/STATE to a
   scratch dir; then `scripts/iig_scorecard.py --generated <feed>_IIG.xlsx
   --real "IIG test cells.xlsx" --real-table <table>` per feed.
3. **Harness side (Genie, from the doc on `acfc/harness-exit3`)**: exit 3 never
   stops a pair; stdout scanned for QUESTION / UNRESOLVED at the end of every
   pair; a later stage's exit 1 reclassified as NEEDS_ANSWERS ONLY for a
   missing-input first-error line (`contract not found:`, `no resolved feed
   matches --feed` / `produced no feeds`, `under gaps:` / `NEEDS_ANSWERS`),
   else FAILED with first_error + needed keys. Ask the harness owner also to
   allow-list its own keys in the leak gate (older runs on
   `origin/acfc-results` were `LEAK_GATE_BLOCKED` false positives — read in
   place, never check out, never quote names).
4. **Open choices left for Soham:** `extract-vdd` exit 3 (doc says planned, not
   implemented — VDD gaps are flags); optional-column ambiguity can only arise
   once client headers are added to the synonym tables (the shipped vocabulary
   has no shared synonym).
5. **The `feature/iig-first` pending items still apply** (next section): the
   four ACFC `app.yaml` paths — DONE on this branch (6f14a2d), still pending on
   `feature/iig-first` / `backup/ddl-only` (never guess them) — the after-demo untrack /
   purge of the real reference files, splitting `acfc_env.yaml` per source
   family — `acfc_env.yaml` now pins the SD / CAQH family for EVERY feed
   (SCHEMA_DRIFT_FLAG Y, `src_file_name: prefix_star`, the four SD audit
   columns, recycle open, the RECYCL path shape), so a PRX-shaped real feed
   needs a feed overlay on top.

**Verified at 1bb8302 (overnight, marker 0.5.8.post26):** 1164 passed / 27 skipped
(Python 3.11) and 1163 / 28 (Python 3.10); ruff clean (`src/ tests/ ui/backend/
scripts/iig_scorecard.py`); tsc clean, vitest 29 passed, `ui/frontend/dist`
identical to a fresh build (`index-CHt2wtuJ.js`); scrub 0 on every line added
since 1ecbacd (+ the binary fixtures' text); the real SD pair (mock) unchanged
— matched 43 / 43 / 46, diff 0. (Before tonight, at 0e7358e: 1004 / 27, marker post25.) `tests/snapshots/notebook_mode.json` re-based in 0c2ba13 (37
hashes: `ruff format` rewrites every emitted .py before the ruff gate).

**What the branch does** (design + status: `docs/acfc/MULTI_TABLE_DESIGN.md`;
the night's and the cleanup's record: `docs/acfc/OVERNIGHT_2026-10-08.md`):
- **Row rules.** Tables = the distinct (catalog, schema, table) triples of each
  STTM band; files = the distinct patterns, a `<LOB>` pattern expanded per
  listed LOB. ADLS rows = files (into the detail table), STGDELTA rows =
  tables, `DATA_QUALITY_RULES` keyed per file (+ the header / trailer split row
  only when they are their own tables), schedule = four structural rows when no
  inventory overlay supplies them, OBJECT_ID = 1..n within the group.
- **Catalogs.** STTM band → FRD label → `default_catalog`, a disagreement =
  `catalog_conflict:<layer>`; `conventions.catalog_map` maps logical catalogs
  (case-insensitive keys, lowercase output; `acfc_env.yaml`: PR_DLK → d1_dlk,
  PR_STD → d1_std).
- **Feed families** (`metadata.templates.iig_v2.family_conventions`): `lob`,
  `stgdelta_unknown_primary_key`, `stgdelta_object_name` (+ `_literal`),
  `schema_drift_flag` (ADLS; was an overlay constant until 0e7dbc3). Shipped
  default = the PRX family (blank / `NA` / generalized pattern / `N`); pair 1's
  overlay pins PRX (+ the literal `Accumulator_accumclient`); pair 4's overlay
  and `acfc_env.yaml` pin the SD / CAQH-style family (codes / blank /
  generalized pattern / `Y`). Neither golden is edited to fit the other.
- **`framework/metadata_inserts.sql` = the client's "DDL"**, written on EVERY
  framework run: one INSERT per IIG row, an open cell = an unquoted
  `<<COLUMN#n>>` placeholder (the script does not parse until filled). The
  header states the three workbook → database rules: (1) value map
  `dml.db_value_map` (ACTIVE_FLAG / ACTIVE_RULE_FLG Y → S), (2) forced NULL
  `dml.db_null_columns` (DAY_OF_SCHEDULE, UDF2–5, the SLA columns,
  CLAIM_TYPE_ID), (3) audit defaults (`GETDATE()`, `@RFC_NUMBER`) +
  placeholders. Guards before the first INSERT (RFC assigned, every
  placeholder id not NULL, PIPELINE_ID / GROUP_ID / key unused), the file
  connection reuse-or-insert (a NULL host with no id aborts), all inside
  `SET XACT_ABORT ON` + TRY / TRANSACTION / CATCH ROLLBACK THROW. Gate check
  `metadata_inserts`. `emit_dml` / `dml.enabled` gate ONLY the runner notebooks
  `Insert_scripts_config_table_<env>.py`. **`config_inserts_<env>.sql` is
  RETIRED** (e02defa, after its DB-side rules were ported; every remaining
  old-vs-new difference is in the overnight report); `config_rows.xlsx` stays
  the approval artefact. The CREATE reference text is one block per table.
- **Scorecard** `scripts/iig_scorecard.py --all-sheets`: rows paired by key,
  a score per sheet + TOTAL, each line ending `| matched / open-by-design /
  open-for-engineer / diff; score excl. open-by-design` (pair 1: 57.9 raw,
  83.8 excl.); `--real` also reads a golden in the `IIG_EXPECTED.yaml` shape.
  Both-blank cells count as MATCH.
- **Fixtures.** Pair 4 = `fixtures/acfc_shapes/pair_4/` (synthetic "Northwind
  Benefits", feed `nb_cob_report`, three tables, six LOB files), hand-written
  golden `golden/IIG_EXPECTED.yaml` (`tests/test_pair4_full_golden.py`); its
  walk-through scores TOTAL 100.0 under the shipped overlay. Pair 1: every IIG
  cell pinned (`tests/test_m4_acceptance.py` FULL_OPEN / FULL_SEQUENCE /
  FULL_DEVIATIONS — the 9 deviation columns are the 21 scorecard diffs).

**Commits (oldest first):** e76496a, 79ed3d7 Phase A / B · e64539b step 1 ·
12a401a step 2 (`catalog_map`) · 2a67c91 catalog precedence · 0c85b39 step 3 ·
0a6efd7 step 4 · 9685f97 step 5 (post15) · 8b94b9e chunk A · 686aad9 step 7
(scorecard) · 4fa9e78, eb9ff00 step 6 (`metadata_inserts.sql`) · 54ecaad chunk D
(post16) · e02defa cleanup (post17) · ff3c420 Friday brief (post18) · 10806a6,
68fea24, 73f69fa pair-4 SCHEMA_DRIFT_FLAG Y · 0e7dbc3 `schema_drift_flag`
convention (post19) · d84e2a6 item 8a · **2026-10-08:** a376ccf first ACFC
run's four defects (post20) · 0c2ba13 real-row scorecard's nine rules (post21)
· cd18ec1 answer lines + exit-3 branches + FREQUENCY = run cadence (post22) ·
2bece72 `layout --require-complete` exits 3 (post23) · 84edab9 the harness's
own `_NEEDED_KEY_RE`, keys verbatim (post24) · 5192895 QUESTION / UNRESOLVED
reserved for answers owed, NOTE informational (post25) · 0e7358e layout-gaps
test (2 optional + 1 required unplaced).

**Today's rules in one place** (details: `docs/ACFC_DEPLOY.md` "What
feature/multi-table adds" + "CLI exit codes"):
- *First ACFC run (post20):* the Detail key resolved by (segment, field name),
  `key_column_not_in_table`; FILE_DETAILS annotation rows skipped
  (`file_details_annotation_skipped`); blank Schema / TableName → File Details
  target / FRD / layer convention (`sttm_target_missing`), else the feed is
  held back NEEDS_ANSWERS with its `gaps:` key (`SttmContract.needs_answers`);
  paths normalised (`path_normalised`); ruff safe fixes (`ruff_fixed`).
- *Real-row scorecard (post21/22):* delimiter is a character
  (`delimiter_from_extension`); OBJECT_NAME drops trailing date tokens;
  SRC_FILE_NAME / audit columns / RECYCL by family convention
  (`src_file_name`, `audit_columns`, `audit_type_case`, `recycle_unstated`);
  SOURCE = vendor display name; SRC_DATA_TYPE `String:<target>`
  (`src_type_coerced_string`); FREQUENCY = run cadence
  (`frequency_delivery_differs`); `spark_unavailable`; `ruff format` before the
  gate (`ruff_formatted`); one `vdd_scope_mismatch`.
- *Exit codes:* 0 ok, 1 failed, 3 NEEDS_ANSWERS — `layout --require-complete`
  with an owed item open; `extract-sttm` only when NO feed is usable (else 0,
  contract written, QUESTION lines still printed); `generate` only when a feed
  asked for (`--feed`) is held back. acfc_run.py summarises codes + lines.
- *Answer lines:* `f"{label:<15}{key} — {reason}"` (`cli.answer_line`, key
  verbatim). QUESTION (a `gaps:` / `pairing:` value) and UNRESOLVED (a
  REQUIRED column, `<sheet>/<layer>/<role>`) ONLY for answers owed
  (`cli._owed_key`); everything informational is `NOTE`. The harness's
  `_NEEDED_KEY_RE` (copied verbatim in `tests/test_harness_answer_lines.py`)
  matches QUESTION / UNRESOLVED only. Clean pairs 1 / 4 print none
  (`tests/test_answer_labels.py`); `tests/test_layout_gap_labels.py` pins
  2 NOTE + 1 UNRESOLVED → exit 3, answered → 2 NOTE, exit 0, zero keys.

**Gotchas learned on this branch:**
- **Bash heredocs on this box mangle escapes and backticks** (an escaped tab /
  newline became a real one, a backtick body aborted bash): write patch scripts
  with the Write tool and run them as files; check `git diff --stat` after.
  **Commit messages too:** a backtick inside `git commit -m "…"` runs as a
  command (5192895's message lost a phrase) — write the message to a file and
  use `git commit -F`.
- **`fixtures/** -text` commits fixture bytes raw.** Python `write_text` /
  text-mode `open` writes CRLF on Windows and Git Bash `sed -i` can turn CRLF
  into LF — either churns a whole fixture file (10806a6 → fixed in 73f69fa).
  Patch with `read_bytes` / `write_bytes`, keeping each file's own EOL; check
  `git diff --cached --stat` before committing; read index EOLs with
  `git ls-files --eol` (`git show rev:path` applies the checkout conversion).
- **The CLI loads the operator's local `.env`** (only names not already set),
  and its notification DL carries the client email domain into EMAIL_TO →
  scrub hits in CLI output. For a shareable run, `export
  CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example` first.
- **The suite runs with `CODEGEN_SKIP_ENV_OVERLAY=1`**, so a fixture overlay
  must carry every environment / family value its golden relies on (the pair-4
  overlay mirrors `acfc_env.yaml`'s shape); a CLI run applies `acfc_env.yaml`
  first, then `CODEGEN_CONFIG_OVERLAYS`.
- **`isolation: "worktree"` agents branch from the default branch**, not HEAD
  — reset each to the working branch before it starts; cherry-pick its commits
  back and delete its `worktree-agent-*` branch afterwards.

## Parent branch `feature/iig-first` (state as of 2026-10-07, end of day — the demo branch)

**Where things stand.** Two live branches, both pushed, nothing merged
anywhere (staging / main untouched):

| Branch | Head | Version | What it is |
| --- | --- | --- | --- |
| `feature/iig-first` | **9da340a** (be38f05 = this docs block) | 0.5.8.post13 | cut from `fix/remove-mock-provider-ui-text` at e89a263 (M15e — that branch's notes below still apply); IIG-first M1–M3 (6291cb5 … 3f44dc8) made every `acfc_prx` framework run write `<feed>_IIG.xlsx` (clean) + `<feed>_IIG_REVIEW.xlsx` (review); then the 2026-10-07 work below. `codegen-watch` inside ACFC pulls it |
| `backup/ddl-only` | **4acec93** | 0.5.8.post5+ddl2 | DDL-only fallback for the demo: `origin/fix/remove-mock-provider-ui-text` (e89a263, descended from tag `v0.5.8-acfc` 3a5b85d) + version bump + `config/overlays/acfc_env.yaml` with ONLY the `acfc_prx` default_catalog (NO auto-load there — `CODEGEN_CONFIG_OVERLAYS`) + the health probe below. `docs/acfc/BACKUP_DDL_ONLY.md`. Suite 740 passed / 28 skipped |

Working tree clean at 9da340a (only the untracked `docs/acfc/denylist_local.txt`).
A worktree of `backup/ddl-only` lived in the 2026-10-07 session scratchpad
(gone with it): recreate with `git worktree prune` then `git worktree add
<dir> backup/ddl-only`; copy in the gitignored fixtures (SFMC contracts, the
raw pair-1 IIG golden under `docs/acfc/rfc_capture/…/goldens/pair_1/`) and run
with the main `.venv` + `PYTHONPATH="src;."` (export
`MSYS2_ENV_CONV_EXCL=PYTHONPATH`). A fresh Windows checkout CRLF-converts
`docs/acfc/rfc_capture/…/goldens/pair_1/ACCUM_DDL.txt` (no `-text` rule outside
`fixtures/**`) and fails one fixture test locally — re-check it out with
`git -c core.autocrlf=false checkout -- <file>`.

**FIRST, pick up here (pending, in priority order):**
1. **The four ACFC workspace paths for `app.yaml` (both branches).** The
   Git-deployed App finds no documents because the committed `app.yaml` had no
   env block. Both branches now carry `env:` with
   `CODEGEN_CONFIG_OVERLAYS=config/overlays/acfc_env.yaml` and the four
   `CODEGEN_EXTRA_INPUT_DIRS` / `CODEGEN_STORAGE_INPUTS` / `_STATE` / `_OUTPUTS`
   entries **commented out as PENDING** — Soham's brief carried placeholders,
   not values; never guess them. When he sends them: uncomment on BOTH
   branches (comment says ACFC paths committed on explicit instruction), bump
   the marker, suite, push. Grants + how to find the App's principal:
   `docs/ACFC_APP_ENV.md` (a fresh Git deploy may mean a new App = a new
   service principal → re-share the folders).
2. **ACFC harness results are `LEAK_GATE_BLOCKED`.** `origin/acfc-results`
   (read in place with `git show`, never check out, never quote names): every
   10-pair run of this branch on 2026-10-07 (d8b2f29 ×2, 50a510e, ca6bab8)
   is a 4-field stub — `status: LEAK_GATE_BLOCKED, hit_count: 4`, no pairs,
   no env, no log — so it says nothing about pass/fail. The only detailed
   result (2026-10-05, 39653aa, 1 pair) was leak-gate CLEAN (0/197),
   installed 0.5.8.post6 = the tree, generate/ddl/iig/dml FAIL, error null.
   **Hypothesis (unverified):** the 4 hits are the overlay's four
   environment names (two catalogs, two containers) now in the DDL / IIG.
   Test: re-run the harness on this branch with `CODEGEN_SKIP_ENV_OVERLAY=1`;
   0 hits → it is a leak-gate allow-list decision; else ask the harness owner
   for the per-pair stages with only the hit terms redacted.
   **Update 2026-10-09:** that run happened (784e110) — pair-level results and
   the redactions inside the harness's own keys are summarised in the
   `feature/multi-table` START HERE above, item 2.
3. After the demo (scheduled, Soham's call): untrack / purge the real
   reference files (see "Open / scheduled" below); split `acfc_env.yaml` per
   source family.

**Verified at 9da340a:** 818 passed / 27 skipped (Python 3.11, full suite);
ruff (`src/ tests/ ui/backend/`), tsc clean; vitest 15 passed; scrub 0 over
every changed file; `ui/frontend/dist` rebuilt (`index-CS2UgojU.js` + map).
The IIG / metadata / framework files also pass with lxml installed (the local
`.venv` has NO lxml — install it to a scratch `--target` dir and put it on
`PYTHONPATH` to reproduce lxml-only bugs). Version marker **0.5.8.post13**
(pyproject + requirements.txt — bump BOTH on every push that changes `src/`
or `ui/`).

**What 2026-10-07 changed (oldest first):**
- be4c6e4 — `stable_workbook_bytes` replaced the whole `<dcterms:modified>`
  element and dropped the `xmlns:xsi` openpyxl declares ON it under lxml →
  every IIG xlsx unreadable in ACFC. Only the timestamp text is replaced now;
  round-trip tests (`test_every_iig_workbook_round_trips_through_openpyxl`).
- 44e74a9 / d0afec7 (+ the overlay-order commit after 58ed330) —
  **`config/overlays/acfc_env.yaml` is COMMITTED and ALWAYS applied first by
  `load_config`** (`codegen.config.overlay_paths`); `CODEGEN_CONFIG_OVERLAYS`
  ADDS overlays on top (later wins, a duplicate applies once); opt out only
  with `CODEGEN_SKIP_ENV_OVERLAY=1`. stderr `config overlays (in order): …`;
  the App's startup line and `GET /api/health` (`config_overlays`) list them.
  **`tests/conftest.py` sets `CODEGEN_SKIP_ENV_OVERLAY=1` at import** so the
  suite stays on the shipped config — a test that wants the overlay passes
  `overlays=[…]` or unsets it. Content: `acfc_prx.default_catalog {stage: d1_dlk,
  standard: d1_std}`; six ADLS_DELTA constants (connection ids 7/4/2,
  `mftlanding`, `z-use-d1-dlk-stage-01`, SCHEMA_DRIFT_FLAG Y) with
  `constant_citations`; `always_blank` minus the five connection/container
  columns (lists REPLACE on merge); `src_columns_style: named`; four SDOH
  path shapes with `path_citations`. **It applies to EVERY ACFC feed** —
  PRX-shaped feeds (pair 1) get SDOH paths until it is split per source
  family. Documented in `docs/ACFC_DEPLOY.md` §2.
- 13e93bd … 0e14ce7 — iig_v2 derivations in `src/codegen/metadata_template.py`
  (tests: `tests/test_iig_v2_derivations.py`): (a) STGDELTA SRC_/TGT_CATALOG_NAME
  follow the DDL chain (the run's profile is threaded through
  `metadata_sheet_payload(conventions_profile=)` → `template_tab_rows(profile=)`);
  (b) TGT_LOAD_OPTION via `_REFRESH_TYPE_BY_STRATEGY` (Truncate and Load →
  Overwrite); (c) FREQUENCY token (leading word, else the only token, else
  open); (d) `{landing_rel}` / `{domain_path}` placeholders (shipped shapes
  unchanged, test-pinned); (e) `src_columns_style: named`; (f) HEADER/FILE_
  HEADER/FILE_FOOTER flags only from FAQ `has_header`/`has_trailer`, and ONLY
  for delimited files — fixed-width keeps the old reading because the pair-1
  golden's flags contradict segment semantics.
- 4b0c1ce / 984ab92 — `scripts/iig_scorecard.py` (+ `tests/test_iig_scorecard.py`):
  MATCH / ALIAS / OPEN / DIFF per real column; never prints CREATED_BY /
  UPDATED_BY; data types caseless; LOB ALIAS only when the generated row is
  the anonymised fixture.
- `docs/acfc/IIG_SCORECARD_2026-10-07.md` — scorecard output, cell provenance,
  open cells + owners, remaining DIFFs, and the exact ACFC run commands for
  the Socially Determined (MIDS) pair.

- 50a510e and the commit after it — **stale-install immunity**: the App
  (`ui/backend/__init__.py` loads `src/codegen/_srcpath.py` by path:
  `ensure_src_first()`; every child launch — docindex parser, gate ruff /
  pytest, acfc_run.py — passes `env=_srcpath.child_env()`,
  startup line `codegen source: …`, `GET /api/health`), the CLI (first line
  `codegen <v> from <file> · overlays: …`, `codegen doctor`), `acfc_run.py`
  (`launch_codegen` with `PYTHONPATH=<repo>/src`, root from its own location),
  `run_meta.json` `codegen`, the report's `- Produced by:` line (stripped
  from the notebook-mode snapshot hash — it names the checkout). Tests:
  `tests/test_app_imports_tree_src.py`, `tests/test_cli_launch_tree_src.py`
  (decoy `codegen` ahead on PYTHONPATH). docs/ACFC_DEPLOY.md "Which codegen runs".
- ca6bab8 — one src-first rule, `src/codegen/_srcpath.py` (stdlib, loadable
  BY FILE PATH before any `import codegen`): `ensure_src_first()`,
  `child_env(extra=None, base=None)`, `load_by_path()`. Launch sites that pass
  `env=child_env()`: `ui/backend/docindex.py` `ParserProcess._start` (also
  calls `ensure_src_first()` first), `gate/preflight.py` (ruff),
  `gate/tests_runner.py` (pytest), `acfc_run.py` `launch_codegen`
  (`srcpath_module`). `codegen-watch` is NOT in this repo — it must put
  `PYTHONPATH=<repo>/src` first itself.
- 2c3c6d4 — **ruff is a BASE dependency** (every install: `.`, `.[ui]`,
  `.[databricks]`); a missing ruff module is the gate flag
  `ruff_unavailable — <reason>` (GateCheck.flag), PASS_WITH_FLAGS, never FAIL;
  any other reason ruff did not run keeps `check_not_run:ruff`
  (`tests/test_ruff_dependency.py`).
- 9da340a (cherry-pick of backup 4acec93) — **self-diagnosing storage roots**:
  `ui/backend/health.py` probes every root the App reads
  (`CODEGEN_EXTRA_INPUT_DIRS` entries + `CODEGEN_STORAGE_INPUTS/_STATE/_OUTPUTS`):
  readable / empty / not_shared (names the App's principal + the grant: Can
  Read pairs, Can Manage roles) / unset / invalid / error / timeout; read-only
  (`exists` then `list` — a remote `list` answers `[]` for a root it cannot
  see). `GET /api/health` here = version, codegen_source, codegen_file,
  config_overlays, startup_error, **principal, roots**. The document chooser's
  empty state shows the table (`components/StorageRoots.tsx`). Tests:
  `tests/test_health_probe.py`. Docs: `docs/ACFC_APP_ENV.md`.

**Current scorecard** (CV golden pair, committed overlay, vs the real
`demographics_package` row): `filled 38/55, matched 33, alias 8, open 10 (BSA
5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 4`. Remaining DIFFs:
OBJECT_NAME / SRC_FILE_NAME (fixture file pattern), SOURCE ("(CV)" suffix),
TGT_PRIMARY_KEY (`NULL` real vs `zip_code` — kept as DIFF: a framework-team
question). Re-run: generate the CV pair (`fixtures/contracts/FRD_demo_cv_golden
.contract.json` + `sttm_mapping_contracts_cv_golden.json`, `--feed
cv_community_demographic_risk --dry-run --skip-tests --output-mode framework
--profile acfc_prx --iig-template iig_v2`, outputs via
`CODEGEN_STORAGE_OUTPUTS=local:<scratch>`), then `python scripts/iig_scorecard.py
--generated <…>_IIG.xlsx --real "IIG test cells.xlsx" --real-table
sd_community_demographic_risk`.

**Open / scheduled — do not act without Soham:**
- **Real client reference files are TRACKED and on origin**: `IIG test
  cells.xlsx` (705e332 — real CREATED_BY user ids), `d1_d1k.stg_doh/`,
  `d1_std.sdoh/` (note the real folder names) and
  `sd_community_demographic_risk.lvdash.json` (17d1300, e27ef7f), committed
  from ACFC before this session. `.gitignore` now lists them, which does NOT
  untrack them. Untracking / history purge is **scheduled for after the
  demo** — `git rm --cached` would delete them from the ACFC checkout on its
  next pull. Read them in place; never print CREATED_BY / UPDATED_BY.
- Split `acfc_env.yaml` per source family (SDOH vs PRX path shapes).
- The CV FAQ leaves `has_header` / `has_trailer` unanswered → the three flag
  cells stay open (BSA).

**Demo-day facts worth keeping:** `0.5.8.post5-ddl1` is not PEP 440 — a
local label `+ddl1` is (pip builds it). `.claude/skills/spiral-breaker/…/
run_replay.py` launches `claude`, not codegen (no child_env there).

**Session gotchas (this Windows box):** bash heredocs containing backticks
break — write patch scripts with the Write tool and run them as files;
Write-tool files may be CRLF, so `str.replace` patches can miss (use Edit);
an env var holding a `;`-separated path list with a drive letter gets
MSYS-converted — `export MSYS2_ENV_CONV_EXCL=CODEGEN_CONFIG_OVERLAYS`. The
spiral-detector hook keys on the exact command string: a check that later
passed under a broader command still reads "failing" (logged as a false
trigger in `docs/spiral-log.md`, 2026-10-07) — re-run the quoted command first.

## History moved out (2026-10-14)

The notes for the legacy demo branch `fix/remove-mock-provider-ui-text` (M15–M15e,
selection latency, pairing jobs), M9 + v0.5.1–v0.5.8-acfc (the first real ACFC runs,
the width chain, the chooser / hang / remote-role fixes), M8 (storage roles, input
discovery, pairing by content, live layout) and M7 (metadata-DB DML, the many-files
FRD shape, the derivation gate) live VERBATIM in `docs/CLAUDE_HISTORY.md`. Rules
from them still in force:
- Nothing may assume a run lives under REPO_ROOT (`relative_to` on a role-store path
  needs a fallback); Can Manage (not Can Edit) on the state / outputs / inputs folders.
- `tests/test_remote_run_e2e.py` is the only run test on remote roles — extend it when
  touching the run path; a pairing / record step is best-effort (never discards a choice).
- A Length cell is a byte width only when it is an INTEGER; never derive a width from a
  precision. An empty schema never reaches a contract (STTM band -> FRD -> default -> stop).
- `ui_stores.get_stores` caches per config object; test fixtures assign `store.config`
  plainly; `_Workspace.release()` drains every runner thread.
- A rebuilt `ui/frontend/dist` must ship with any `ui/frontend/src` change (pre-push).

## Purpose & pipeline position

Generates production-shaped Databricks ingestion pipelines (PySpark + Delta
Lake) from approved machine-readable contracts — one FRD feed contract plus
one STTM mapping contract per feed. It is the **second agent** in the
three-agent AI-in-Engineering program at AmeriHealth Caritas: FRD→STTM
(produces the FRD feed contracts consumed here) → **CodeGen** → Code Review
(reviews what this repo emits).

**Scope cut 2026-08-21:** the program dropped from five agents to three —
BRD→FRD and SQL Optimization are no longer in scope. Do not build them or
add dependencies on them.

**Where this runs:** Hexaware builds, ACFC rebuilds. This repo is the
Hexaware-side reference implementation; the production agent gets rebuilt
inside ACFC's own environment with Claude Code, using this as the
blueprint. Nothing here deploys to ACFC directly — anything that cannot be
re-derived from the contracts, config, and docs does not survive the
hand-off. **Current program priority is FRD→STTM's live Databricks App
(due 2026-08-24), not this repo.**

Two-layer trust rule (never violate): **Layer 1** is deterministic Jinja2 —
everything derivable from the contracts, byte-stable, every file stamped
with a provenance banner carrying the contract names + sha256. **Layer 2**
is the LLM, mock by default — ONLY free-text `validation_rules` the
compiler classifies as `unmapped` reach a model; its output lands in a
review artifact (`out/<feed>/candidates/candidates.json`), never in
generated modules, and every citation must appear verbatim in the contract
text. Each feed ends in a computed gate verdict: PASS / PASS_WITH_FLAGS /
FAIL (semantics in `docs/WORKFLOW.md`).

## Repo layout

```
src/codegen/        sharepoint.py (Microsoft Graph transport, stdlib-only),
                    databricks.py (UC volumes transport, read-only, needs the
                    [databricks] extra; added 2026-08-27),
                    demo_sources.py / metadata_sheet.py / input_requirements.py /
                    governance_checks.py (request-time display+check modules,
                    all OUTSIDE the generation path; added 2026-08-27),
                    contracts/ (pydantic models, both dialects + vdd.py, frozen),
                    layout/ (M2.5 layout recognizer: profile, fingerprint,
                    discover, validate, model, resolve, frd_profile),
                    resolve/ (FRD⋈STTM join → ResolvedFeedSpec), extract/
                    (workbook→STTM incl. generic.py content-driven reader,
                    frd_docx.py, vdd.py), rules/ (rule classifier),
                    reasoning/ (Layer 2: providers, verbatim grounding),
                    emit/ (Jinja2 + notebook assembler; framework.py Option B,
                    rfc.py the RFC package, dml.py the SQL Server DML — M7),
                    gate/ (preflight, tests, verdict, vdd_check, drag_fill,
                    derivations — M7), metadata_template.py (IIG template
                    versions), report/, templates/, cli.py, config.py,
                    storage/ (M8.1: local | workspace | volume backends, role
                    stores, input catalog — an EDGE, never imported by the
                    generation path), pairing.py (M8.2: pairing by content),
                    layout/answers.py (M8.3: answers file + unresolved report)
tests/              offline, no Spark needed; some SKIP when the fixtures they
                    drive on are absent (see "Fixtures & data rules"); the
                    demo-UI and SharePoint-route tests also skip when the [ui]
                    extra (or httpx) isn't installed. Run pytest for the live
                    count rather than
                    trusting a number written down here.
config/config.yaml  every knob — contract pairs (EMPTY since 2026-08-22), extractor layout
                    (+ discovery / frd / vdd synonym tables), naming, masking, gate, job,
                    layout, conventions, metadata, rfc, playbook. Overlays:
                    load_config(path, overlays=[…]) / CODEGEN_CONFIG_OVERLAYS deep-merge
                    a YAML mapping first — client-shaped vocabulary lives THERE
                    (fixtures/acfc_shapes/pair_1/config_overlay.yaml), never in the tracked file
fixtures/           tracked on staging (state as of 2026-09-18, M6): faq/ (per-feed
                    load-pattern FAQs), reference/ (SCRUBBED SFMC client reference
                    artefacts incl. the deployment playbook + SCRUB_REPORT),
                    acfc_shapes/ (the SYNTHETIC fixture universe for ACFC's shapes,
                    generated by scripts/build_acfc_shapes.py; the aliased pair-1
                    golden; the pair-1 config overlay), layout_profiles/ (cached
                    layout profiles + the mock/adversarial answers, generated by
                    scripts/build_layout_profiles.py), the CV golden contracts +
                    workbook + replay set (anonymized universe) and
                    workbooks/synthetic_segmented_golden.xlsx — all via deliberate
                    per-file .gitignore re-includes. NOT on staging: the MIDS/CAQH
                    client documents and the SFMC client-derived contract pair
                    (untracked 2026-09-18; on MAIN they are tracked since b0560af)
docs/               DESIGN.md, WORKFLOW.md, EXTRACTOR_RECON.md, SEGMENTED_MODE_DESIGN.md,
                    LIVE_PATH_RECON.md, LIVE_RUN_RECORD.md, DEMO_RUNBOOK.md (client demo script),
                    EDO_STANDARDS_ALIGNMENT.md (clause-by-clause map of the EDO
                    naming/coding standards to the generator, incl. deviations),
                    LAYOUT_RECOGNITION.md (the recognizer), ACFC_DEPLOY.md (stand-up
                    inside ACFC), acfc/SHAPES_FOR_PORT.md + acfc/rfc_capture/…/
                    RFC_PACKAGE_SHAPES.md (the documented client shapes) + the pair-1
                    goldens, acfc/METADATA_DB_SEMANTICS.md (the SQL Server metadata-DB
                    walkthrough as a spec — M7; its raw .docx stays untracked), media/
ui/                 demo dashboard: FastAPI (8571) + Vite/React (5173); pip install -e ".[ui]", see ui/README.md
                    backend/sharepoint_routes.py: picker + confirm-gated publish.
                    ui/frontend/dist IS TRACKED (M6): rebuild (`npm run build`) and
                    commit it whenever ui/frontend/src changes — the App serves it
inputs/sharepoint/  gitignored landing dir for documents pulled from SharePoint
acfc_run.py         Databricks notebook source: the one-pair fallback run (storage URIs as
                    widgets, answers file) for a workspace where the App is not usable
```

## STTM workbook extractor (codegen extract-sttm)

Deterministic, no LLM, pairing-aware: inputs are (workbook, FRD contract); `feed_id`
is `normalize_feed_name(FRD feed_name)` — the resolver's join invariant, NOT the
stage table name — and format/delimiter/standard-target presence come from the FRD side. Recycle validation text stays VERBATIM
(the resolver also accepts the client "Check with ... FOR ..." phrasing).
**Segmented (H/D/T) dialect IMPLEMENTED, corrected 2026-09-01 against the
FRD read verbatim** (`extract/segmented.py`; docs/SEGMENTED_MODE_DESIGN.md):
segments are TABLES in BOTH layers (FRD acceptance criterion 2 — fields
carry `record_segment`/`stage_table`/`standard_table`; per-segment
standard DDL), layer scope comes from **Load Strategy STG/STD, never from
which schemas the Target Schema block names** (STD catalog/schema/tables
from the STTM's second target group with a cited provenance note), record
identification is **DERIVED from the STTM** (trailer static marker quoted
verbatim as the citation; header positional; FAQ
`record_type_discriminators` is strictly a confirmed-status override),
STRING-except-audit in both layers rides an FRD-driven AS-IS switch
(`spec.load_as_is`), and a keys-None FRD (truncate/append, no MERGE)
makes empty `natural_key_columns` legitimate. The review layer gets ONE
soft cited CONFIRM item (`RuleCandidate.kind == "confirm"`), riding the
existing candidates/decision flow. **Citation rule (2026-09-01 lesson):
every conflict/assumption/confirm item and provenance note the agent
raises MUST quote the exact FRD field or STTM cell it rests on — an item
that cannot cite its evidence is a bug (models enforce non-empty
citations; tests assert them). And never infer target-layer scope from a
schema block: "stage-only" was wrongly inferred that way once — read Load
Strategy.** Header resolution is fuzzy + config-driven (`extractor:` knob);
trailing `NA` rows → `audit_columns`, never `fields[]`; `Comment` →
`value_spec`; file-name pairing canonicalizes date placeholders (CCYY→YYYY,
case-insensitive) and stays fail-loud. The CV/golden pair is byte-tested against
its committed expected output and can NEVER match the MIDS fixture
(different universe — docs/EXTRACTOR_RECON.md §4d).

## Setup / run / test

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"   # deps from pyproject
# Python 3.10 – 3.12 are supported (the Databricks Apps floor is 3.10): before shipping,
# run the suite on 3.10 and 3.12 too — uv venv --python 3.10 <dir> && uv pip install -e ".[dev,ui,databricks]"
# Live Layer-2 runs additionally need the Anthropic SDK: -e ".[dev,live]"
.venv/bin/python -m pytest -q          # no Spark, no network

# Generate everything from the fixture contracts (mock Layer 2, no network)
.venv/bin/python -m codegen.cli generate-all --config config/config.yaml --dry-run --skip-tests
```

`contracts.pairs` is empty (see "Fixtures & data rules"), so `generate-all`
refuses loudly; generate via explicit paths (`codegen generate
--frd-contract X --sttm-contract Y`) or the demo UI's golden pair. A feed
with flagged/notification/unmapped rules verdicts PASS_WITH_FLAGS — correct
behavior, not a failure. Output lands in `out/<feed_slug>/` (module tree, DDL, tests,
job JSON, one assembled runnable `.ipynb`) with a markdown report per feed
in `reports/` — both gitignored. Running the *generated* Spark tests (drop
`--skip-tests`) needs a JVM: `JAVA_HOME` → Java 17, `PYSPARK_PYTHON` → the
venv interpreter. `ruff check src/ tests/` must stay clean; generated code
must be ruff-clean against the same rules (`out/<feed>/ruff.toml` emitted).

## Config doctrine

- Every knob lives in `config/config.yaml` — contract pairs, extractor
  layout, naming, masking, segment discriminators, gate, job cluster. No
  numeric literals in generator logic; the loader is loud on typo'd keys.
- No secrets in the repo, ever. Credentials only via environment / `.env`
  (gitignored; `.env.example` documents the names).
- Program policy: **Anthropic is the sole model vendor** across the
  AmeriHealth agents program. Mock always wins on dry-run; live selection
  is transport-dependent (2026-08-28): the tracked config's
  `reasoning.provider` is **`databricks_fmapi`** (Claude via the workspace
  serving endpoint `databricks.serving_endpoint` — a transport, not a
  vendor change; resolves from YAML + workspace auth, no Anthropic key),
  with `anthropic` (key-gated on `ANTHROPIC_API_KEY`) still available.
  CAUTION: because FMAPI resolves without any env secret, tests that touch
  live paths must pin the provider — `tests/test_demo_ui.py`'s `client`
  fixture does this; a 2026-08-28 pytest run fired real FMAPI calls before
  that guard existed. First live FMAPI E2E: 2026-08-28 (CV golden pair,
  candidates verified). Live LLM use is confined to Layer 2
  (reasoning/review); code generation itself is deterministic Jinja2 by
  design. Model name lives in config (`reasoning.model`, currently
  `claude-opus-5`). The Claude 4.8/5 API families reject sampling
  parameters (`temperature`/`top_p`/`top_k` return a 400), so no
  temperature knob exists and live Layer-2 output is inherently
  non-deterministic — do not re-add one. CAUTION (2026-09-01): the
  endpoint serves extended-thinking Claude, whose `message.content` comes
  back as a LIST of typed blocks (reasoning + text), not a string —
  `codegen.databricks.chat` normalizes via `_chat_content_text` (text
  blocks joined, non-text ignored). Do not "simplify" that back to
  `content or ""`; that exact regression produced the provider-failure
  candidates in run demo_20260831_212539 (fixed in e91ec11; post-demo
  TODO in docs/DESIGN.md §8: provider failures should be their own flag
  class, not candidate cards).
- Pydantic v2 models are `frozen=True` + `extra="forbid"`; missing is
  `None`, never a default. PHI masked to last-4 at every egress.
- **Client framework doctrine (Aug 26 framework calls, encoded 2026-08-27):**
  job parameters carry IDs the wrapper resolves from metadata, NEVER inline
  SQL (~250 KB parameter cap); all new tables managed with
  `CLUSTER BY AUTO` and CDF on (NOT workspace defaults — must be explicit
  DDL, per B0 observation); the agent never creates target tables and never
  runs jobs; Anthropic is the sole model vendor — Databricks FMAPI serving
  a Claude model (`reasoning.provider: databricks_fmapi`,
  `databricks.serving_endpoint`) is a transport, not a vendor change. The
  only SQL shape the seam may send is `EXPLAIN` (`codegen.databricks
  .explain` enforces the prefix), and an EXPLAIN wakes the auto-stopped
  warehouse = DBU spend from the shared ~120/month pool.
- **Engineering standards are REAL as of 2026-08-26** (three-input model
  input #2 is no longer a stub): the EDO Data Engineering Naming + Coding
  Standards live as data in `config.yaml engineering_standards:` (WF_/NB_
  naming patterns + abbreviation tables) and `job:` (prod-support alert DL
  on success AND failure, `timeout_hours`, Photon, DBR 15.4). The
  `standards_stub` gate flag is gone for the tracked config; the MODEL
  defaults keep the stub so a config without the section still degrades
  honestly. Clause-by-clause map + deviations:
  `docs/EDO_STANDARDS_ALIGNMENT.md`. The DDL templates emit
  `CLUSTER BY AUTO` (Liquid Clustering) and `LoadStrategy` accepts
  `"Upsert"` (the SFMC FRD's standard-layer strategy).

## SharePoint / Microsoft Graph (added 2026-08-23)

Ported from frd-to-sttm-agent-v2's integration. The document library is the
program's system of record: STTM workbooks and FRD contracts in, generated
artifacts out. `src/codegen/sharepoint.py` is the whole transport.

**It is a seam at the edges, deliberately outside resolve/emit/gate.** The
generator's inputs and outputs are files on disk; SharePoint attaches before
(`codegen sharepoint-fetch`) and after (`codegen sharepoint-publish`).
Keeping the network at the edge is what lets Layer 1 stay deterministic,
offline and credential-free. **Do not "simplify" this by calling Graph from
inside `extract-sttm` or the resolver.**

Mechanics (stdlib-only transport, app-only credentials via
`SHAREPOINT_CLIENT_SECRET`, config split, fail-loud rules, the
publish-is-the-human-gate design, one-folder write scope, qualified publish
names, UI route status codes):
`.claude/skills/code-gen-agent/references/sharepoint-seam.md` — read it
before touching `sharepoint.py`, the publish flow, or the UI routes. No
secrets in the repo; the `sharepoint:` config section is optional and
non-secret.

## Output modes (Option A / Option B, added 2026-08-27)

The outputs are EXACTLY Notebook and Framework artefacts
(`src/codegen/output_modes.py` is the one vocabulary): `output.mode:
notebook | framework | [notebook, framework]`, CLI `--output-mode`
(repeatable, choices notebook / framework), UI two toggles rendered from
`GET /api/demo/output-options`. The RFC package / All options were removed
(2026-09-22); a config, saved selection or past run that still says `both`,
`rfc` or `all` maps to notebook + framework with a one-time notice
(`output_notices` on the status), never an error. `codegen/emit/rfc.py` is
kept but no output option reaches it (its tests drive it directly).
**Option A** ("notebook", the default) is today's output byte
for byte — a fresh standalone pipeline, the ~10% case; guarded by
`tests/snapshots/notebook_mode.json` (sha256 per emitted file for the CV
pair — regenerate deliberately, never casually). **Option B**
("framework") is the primary ACFC path per the Aug 25/26 calls: an
*addition* to the existing metadata-driven ingestion framework (~90% of
runs) — `out/<slug>/framework/` holds (formats swapped 2026-08-31 per
Venu's standup direction + the real client reference artefacts, scrubbed
into `fixtures/reference/` by `scripts/scrub_reference.py`; the raw
exports live only in gitignored `inputs/reference_raw/`, and
`scripts/scrub_check.py` is the denylist scanner tests run over every
emitted artefact): `<slug>_stage_table_creation.txt` +
`<slug>_standard_table_creation.txt` (deployment-team DDL conformant to
the reference goldens — CREATE OR REPLACE, per-column COMMENTs, stage
LOCATION labeled-SYNTHETIC, standard CLUSTER BY AUTO + full TBLPROPERTIES,
trailing SET TAGS), `config_rows.xlsx` (THE approval artefact; built by
`codegen.metadata_sheet`, the single source of truth for the row layout —
now the REAL 7-tab client IIG layout from the scrubbed reference
workbook) and `config_inserts.xlsx` (one sheet per populated tab, value
rows + generated INSERT column, sqlserver|lakebase dialect via
`framework:` config; statements over Excel's cell limit chunk into
`_PART<n>` columns; plain INSERTs, idempotency belongs to the framework's
load path) and `ADDITION.md`. **The master notebook is ACFC's own existing notebook
(clarified 2026-08-27): the DDL scripts and insert SQL are ADD-ONS to it —
the agent never generates, edits, or ships that notebook.** Framework mode still renders the FULL pipeline into a
scratch tree so gate checks and verdicts are identical across modes; it
persists only ddl/ + framework/. **Never-invent-IDs:** `always_blank`
columns render as `framework.id_placeholder` and are flagged — assigned
by the client's framework or manually by client instruction, never by the
agent. Workbook serialization is pinned byte-stable
(`stable_workbook_bytes`). The FAQ gained `has_header`/`has_trailer`
companions (NOT questions — banner/flag counts untouched) feeding the
"from FAQ" badge.

## Layout recognition (added 2026-09-18, M2.5)

A model decides WHERE things are, code copies the values: every extractor
reads through a layout profile (`src/codegen/layout/`), resolved cache →
synonyms → model → validate → user; the model sees only the fingerprint
material (header regions / table labels, never a data row), only the
unresolved remainder is merged out of its answer, every merged claim is
validated against the document, and no model string can reach a contract,
DDL or IIG cell. Full description, resolution order, validator checks,
caches (`fixtures/layout_profiles/`, runtime under `ui/backend/state/`)
and surfaces: `docs/LAYOUT_RECOGNITION.md`. The Vendor Data Dictionary
(M3) is the pair's third input through the same machinery
(`codegen extract-vdd`, `generate --vdd`, `contracts/vdd.py`); it never
feeds the standard layer — only the IIG fixed-width rows and the
STTM-vs-VDD gate flags (`gate/vdd_check.py`).

## Standalone doctrine + ACFC's documented shapes (M0–M6, 2026-09-18)

**Standalone doctrine (policy commit 25b4b72):** the agent runs from the
documents themselves — an FRD `.docx`, an STTM `.xlsx`, optionally a Vendor
Data Dictionary `.xlsx` — with no dependency on the upstream FRD→STTM
agent's contract table (still supported as an FRD source). Every extractor
is deterministic and reads through a layout profile (next section).

**The shapes** are documented, not guessed: `docs/acfc/SHAPES_FOR_PORT.md`
transcribes ACFC's five STTM families (A inline-meta + banded mapping, B
FILE_DETAILS + `MAPPING-` sheets, C Layout + STTM dual sheets, D single
mapping sheet, E multi-domain / multi-sheet), two FRD families (F1 six
metadata section tables with `label: value` rows; F2 Solution-Requirement
tables with the section label in row 4 and inline `Label: value` pairs)
and three VDD patterns (V1 full position, V2 length only per file, V3
database table per sheet); `docs/acfc/rfc_capture/rfc_capture/
RFC_PACKAGE_SHAPES.md` documents the RFC deployment packages (INGESTION_A
vs the PRX packages). `fixtures/acfc_shapes/` is the SYNTHETIC universe
built from those documents (`tests/acfc_shapes/` + `scripts/build_acfc_
shapes.py`, byte-asserted; alias map in `ALIASES.md`); pair 1 is the one
pair whose structure (columns, types, fixed-width positions, audit rows)
is the scrubbed + aliased client golden. **Families A, C and E may
legitimately leave roles unresolved under synonyms alone — that is pinned
as expected in `tests/acfc_shapes/layout_truth.py`; do not widen the
synonym tables to force them.** (M9 exception: pair 1's `… in DL` headers and
`Format` became synonyms because the REAL sheet was captured with them — a
header seen in a client document is evidence; a header invented to close a
fixture gap is not. Pairs 7, 8 and 10 still need the model.) The client STTM reader for non-`MAPPING-`
workbooks is `extract/generic.py` (content-driven: band row with stage +
standard tokens, header beneath, meta rows, auxiliary sheets by signature,
segments from a Segment column or banner rows).

**Layout recognizer principle:** a model decides WHERE things are, code
copies the values, and a validator sits between them — the model sees only
the fingerprint material (header regions, table labels; never a data row),
only the unresolved remainder is merged out of its answer, every merged
claim is re-validated against the document, and no model string can reach
a contract, DDL or IIG cell. Order: cache → synonyms → model → validate →
user (the UI's `needs_layout` dialog, radios over candidate columns / FRD
cells). Full description: `docs/LAYOUT_RECOGNITION.md`.

## Conventions profiles, IIG / playbook templates, the `rfc` package (M4–M5)

- `conventions.profile` selects how the deployment DDL is laid out.
  `edo_sfmc` (default) = today's two `.txt` files exactly; `acfc_prx` = ONE
  combined `<ABBREV>_DDL.txt` with `--stage table` / `--standard table`
  banners, stage columns TYPED as the STTM stage band states them, audit
  types in the profile's casing, standard = the stage column list, and
  every whitespace quirk of the pair-1 golden as a knob (the golden is
  compared byte for byte). **To add a profile:** a new key under
  `conventions.profiles` (all knobs on `ConventionsProfileConfig`), a
  golden under `fixtures/acfc_shapes/<pair>/golden/`, and a byte-identity
  test like `tests/test_m4_acceptance.py`. A new layout kind (beyond
  two_files / combined) is a new Jinja template under
  `templates/framework/` + a branch in `emit/framework.py`.
- `metadata.template` selects the IIG workbook version. `iig_v1` =
  `demo.metadata_sheet` (the 7-tab SFMC reference, byte for byte); `iig_v2`
  = the PRX 8-sheet layout, headers transcribed from the aliased golden in
  its order, rows built by `metadata_template.py` from derivation knobs
  (positional `SRC_COLUMNS`, base-type pairs, one object per file pattern,
  fixed-width handler rows from the STTM positions + FAQ discriminators,
  DateFormat / DataTypeCast DQ rules from the STTM load rules, per-sheet
  path shapes, framework-vocabulary constants WITH a citation). Every cell
  is transcribed from an input or a cited constant; the rest is blank AND
  flagged (`iig_blank:<SHEET>: <columns>`, one flag per sheet). **To add a
  template:** a key under `metadata.templates` with `tabs` transcribed from
  the client's workbook, `always_blank`, the knobs, a `citation`; client
  inventory rows go in a config OVERLAY, not the tracked yaml; pin
  headers + blank list in a test.
- `playbook.template` (rfc mode): `sfmc_7sheet` reads the scrubbed
  reference workbook for its structure and blanks every value it carried
  (`playbook_blank:<sheet>.<header>` flags); `main_single` is the PRX
  one-sheet `Main`. Task rows come only from `playbook.tasks` (per profile,
  `default` fallback), phrased over the package's own artefacts. **To add
  one:** a key under `playbook.templates` (`kind`, sheet/header knobs) and
  a `tasks.<profile>` list; nothing else may fill a playbook cell.
- **`rfc` output mode** writes `out/<slug>/RFC{rfc_number}_{feed}/`: the
  profile's DDL, `<FEED>_IIG.xlsx` (template sheets only — provenance stays
  in `framework/config_rows.xlsx`), the playbook, `FILE_LOG_INFORMATION.txt`
  (documented T-SQL shape, `rfc.file_log_information`), `MANIFEST.md`
  (every file, its source artefact, the flags that apply; Runbook / TDD
  named out of scope). RFC number = FAQ companion `rfc_number`, feed token
  = FAQ `feed_abbreviation`, else the documented `######` placeholder /
  the sanitized slug, each flagged. FAQ companions (not questions):
  `process_name`, `feed_abbreviation`, `rfc_number`.
- Gate additions: `drag_fill_suspect` (≥3 adjacent `Decimal(p,s)` columns
  stepping p by one — flagged, never altered; the client golden carries
  exactly such a run), `segments_from_sttm` / `file_pattern_from_sttm`
  (a docx FRD names neither; the STTM supplies them, flagged), `vdd_*`
  cross-check flags, `iig_blank`, `playbook_blank`, `rfc_*`.
- **Known inconsistency (accepted, Option A shelved):** under `acfc_prx`
  the deployment DDL types the stage columns as the STTM states them
  (`Decimal(17,2)`, `Date`), while the generated PySpark pipeline still
  lands every stage column as STRING (the notebook-mode contract). The two
  disagree by design until the Option A pipeline is revisited; the
  framework path (Option B / rfc) is what ACFC deploys.
- **Open questions for the framework team** (cells the pair-1 golden fills
  that no input document determines): the semantics of `HEADER_FLAG`
  (`Y` in the golden for a fixed-width file whose first record is a header
  SEGMENT, while the FAQ's `has_header` means a column-header row); the
  stage leg's `TGT_LOAD_OPTION` / `TGT_REFRESH_TYPE` = `Overwrite` in the
  golden while the FRD's Load Strategy STG says `Append`; `LOB` blank in
  the golden while the FRD states `ALL`; the derivation of the STGDELTA
  row's `OBJECT_NAME` (`Accumulator_accumclient`) and `SOURCE` (the feed
  name, not the vendor). Until answered these cells follow the inputs and
  differ from the golden.
- **The Genie episode (2026-09, three lines):** a Genie-assisted diagnosis
  claimed the pair-1 mismatch was a "field spec" problem — it was wrong; the
  documents answered it, and the fix was to read the STTM's stage band as
  written. Never synthesize a mapping to make a diff close: a value not
  transcribed from an input is a bug, however plausible. When a
  plan-completion agent runs unattended, give it a rules file (this file +
  the milestone brief) and explicit stop conditions (byte-identical
  baselines, zero scrub hits, one commit per milestone, stop for
  go-ahead) — the rules, not the agent's judgement, decide when it is done.

## FRD pairing + upstream contracts (added 2026-08-28)

The run takes an **(STTM, FRD) pair**. FRD contracts come from the
upstream FRD→STTM agent's Delta table
(`soham_workspace.sttm_agent.frd_contracts`, read via the allowlisted
SELECT-only `read_table_rows`; first read wakes the warehouse = DBU
spend) **or, since 2026-09-18 (standalone doctrine), from the FRD .docx
itself**: `codegen extract-frd` / `codegen.extract.frd_docx` reads the
F1/F2 document families deterministically (stdlib docx, label synonyms in
`extractor.frd`, per-field provenance), the UI chooser and upload accept
a `.docx` alongside a `.contract.json`, and the runner extracts a docx
selection into the run's own `frd.contract.json`. The earlier "no
docx→contract extractor here" rule is retired.
Pairing precedence: explicit `demo.pairing_map` (canonical stems; ships
MIDS) → shared ticket number (CAQH `1005034`) → the ≥3-token content-stem
match (role tokens `frd`/`sttm` and a `.contract` suffix ignored; unique
both ways). **M8.2 (v0.5.0): at selection time this chain is superseded by
pairing by CONTENT (`codegen.pairing`, see the M8 section) — the name rules
below decide only when no document shares any content.** **Since 2026-09-18 pairing is automatic at selection time**:
choosing an STTM selects its associated FRD among the LOCAL candidates
(contracts dir + the three inboxes; no network) and the status carries
`frd_auto_paired {frd, rule}`; the same happens for the Vendor Data
Dictionary among the listed workbooks (`demo.vdd_pairing_map` → ticket →
name stem; `vdd_auto_paired`); the chooser still lets the person override,
a manual pick is never marked automatic, and clearing the STTM clears an
automatic pair. No match or ambiguity pairs nothing. Defaults are
unchanged (golden STTM + golden FRD, snapshot byte-identical), a
mismatched pick shows a warning chip, and feed-match failures name the
FRD used and offer the paired candidate — nothing auto-retries.

**FRD gap handling (2026-09-18, `resolve/gapfill.py`):** when a docx FRD is
silent, the fallback chain fills — each fill a `frd_unstated:<field>
source_used:<document cell>` flag — file format and delimiter from the
STTM meta row then the VDD FILES sheet; the stage load strategy from the
STTM "Load Strategy" meta row when it states one per layer (`STG: …; STD:
…`) then the FAQ `load_mode`; the standard strategy from the STTM per
layer only (else blank + flag). Domain / subdomain stay FRD-only; the
STTM stage band is authoritative for catalog / schema / tables (never
asked; the FRD's statement is a cross-check). The layout dialog does NOT
ask when exactly one other document states the value ("Taken from other
documents" lists the fills), DOES ask when sources disagree (a `choice`
question showing each value + cell; the answer lands with source=user) or
when the only source is ambiguous (one layer-less "Load Strategy" → the
`layer` question: stage / standard / both). The contract resolver applies
the same chain on the CLI path. Remaining hard stops: file format and
stage load strategy when every source is silent (the reader / writer
cannot proceed without them); an ambiguous single strategy on the CLI
path names the dialog / FAQ as the remedy.
**The one-block / many-files FRD shape (MIDS, 2026-09-18,
`layout/resolve.py::split_frd_feeds_by_sttm`):** section titles may carry
a requirement-ID suffix ("Structural Metadata: MDST231070" —
`frd_docx._section_key` prefix-matches); the "Object Name" cell can be a
flattened nested table (a name with newlines / >80 chars is "garbled");
and one metadata block's "Target Table Name" may list FILE names for
several feeds, none an STTM stage table. The layout stage then derives
ONE FRD feed per STTM mapping sheet (feed name + stage/standard tables +
stage schema from the sheet's bands, everything else shared; flag
`frd_feeds_split_from_sttm:`), pairs each feed's file by a MUTUAL unique
token match (tokens every table shares, e.g. `risk`, carry no
information and are dropped; a leftover single file is only the
dialog's `suggested`), and asks a `choice` question otherwise. A
single-sheet STTM keeps the FRD feed name unless garbled and takes the
file-like entries as its patterns. `format: File Data Ingestion` states
no delimiter, so the extractor / resolver fall back to the file
EXTENSION (`.csv` → `,`, `.psv` → `|`, `.tsv` → tab; else the existing
hard stop). `feed_spec.py.j2` renders the free-text constants
(FEED_NAME / SOURCE_SYSTEM / FILE_FORMAT) through the `pyconst` filter:
identical to `tojson` when short, a parenthesized implicit
concatenation when the line would exceed the emitted ruff line length
(a long "Data Source" cell made every MIDS feed FAIL its own ruff
check). MIDS in mock mode now runs end to end: 3 feeds
PASS_WITH_FLAGS, one dialog question (the file for `sd_community_risk`,
whose name matches no file). **Client-document rule:** the MIDS/CAQH artefacts are real
client documents, and a LIVE run sends their content to the model API —
live runs on client STTM/FRD pairs are permitted only per the program's
client-document process (Venu's email approval); the demo CV golden
remains the default rehearsal pair, and mock runs need no approval.
**Live runs are self-contained (View-results fix, 2026-08-28):** every
live run copies its FRD into `out/demo_<ts>/frd.contract.json` and writes
`run_meta.json` (frd_label / sttm_workbook / output_mode); the past-run
loader reloads with the run's OWN pair and recorded output mode (older
dirs fall back to the demo golden + inferred mode). Run completeness keys
on emitted artefacts (README / ddl / framework / candidates.json) — a
feed with ZERO Layer-2 candidates (all rules compiled deterministically,
e.g. MIDS) is complete and replays with an empty candidate list.

## Databricks volumes seam (added 2026-08-27)

**OFF as shipped (2026-09-22):** `databricks.catalog / schema / frd_volume /
sttm_volume` are BLANK in the tracked config — they named the Hexaware build
workspace's own volumes, and inside ACFC the App listed / fetched FRDs and
STTMs from them. Blank = no Databricks section in the chooser, nothing
listed or fetched (and the publish panel unavailable). A desktop that has
the volumes opts in via `DATABRICKS_CATALOG / _SCHEMA / _FRD_VOLUME /
_STTM_VOLUME`. `config_for(require=...)`: the serving endpoint, the layout
recognizer and the upstream table reader pass `require=()`, so blank volumes
never drop live Layer 2 to mock.

`src/codegen/databricks.py` — the UC-volumes twin of the SharePoint seam,
READ-ONLY (list + download), same edge doctrine: fetch documents to local
disk (`codegen databricks-fetch` → `inputs/databricks/`, also the UI's
per-file Fetch in the STTM chooser), then generation proceeds from disk.
The client's raw documents live in `soham_workspace.codegen_agent.frd_raw`
/ `.sttm_raw` (uploaded 2026-08-27, un-anonymized, on explicit user
instruction — Databricks volumes are allowed to hold client documents;
this REPO still is not). Non-secret knobs in `config/config.yaml`
`databricks:` (profile/catalog/schema/volumes; env `DATABRICKS_*` >
YAML); auth resolves from the named profile (CLI OAuth keyring) — except
when `DATABRICKS_HOST` is set in the env (a Databricks Apps runtime),
where `_client()` lets the SDK's unified auth resolve the injected
credentials instead of a profile. `databricks-sdk` via the optional
`[databricks]` extra, keyless import. CAUTION: never leave a placeholder
`DATABRICKS_HOST` uncommented in `.env` — the SDK prefers env over
profile and will try to reach it. The FMAPI provider (`chat()` here +
`reasoning/providers/databricks_provider.py`) got its explicit go and is
LIVE as of 2026-08-28. **Artifact publish got its explicit go
2026-08-28 too**: `publish_artifacts` (+ generalized `ensure_volume`) is
the human-gated outbound half — the UC twin of `sharepoint-publish` —
targeting `databricks.output_volume` (default `generated`), per-feed
directories, confirm-gated over HTTP (`POST /api/databricks/publish`),
no `--confirm` on the CLI (`codegen databricks-publish`) because running
it IS the gate. The UI's publish panel (Dashboard) lets the user pick
any catalog.schema.volume, but every write resolves through
`_guarded_full_name` — `WRITABLE_PREFIX` refusal is enforced in code,
and the governance "never writes back" check sanctions exactly
{ensure_volume, upload_file, publish_artifacts}. Everything else
write-shaped (tables, jobs) stays NOT BUILT pending explicit go; the
check flips if any other write-shaped function appears (an FMAPI query
is a read).

**Databricks App deployment (2026-08-28; mock-locked 0.3.2–0.3.3, live
FMAPI since 0.3.4, currently 0.3.5):** the demo UI runs as the workspace app `codegen-agent`
(https://codegen-agent-7405617821962942.2.azure.databricksapps.com).
Deploy from a STAGED TREE (repo files + the gitignored
`ui/frontend/dist` and fixtures — never `inputs/`): `databricks sync
--full <staged tree> /Workspace/Users/<deploy-contact>/
codegen-agent-app` then `databricks apps deploy codegen-agent
--source-code-path <that path>`. `requirements.txt` (`.[ui,databricks]`)
is the Apps pip install; the runtime CACHES the installed env keyed on
it, so bump the pyproject version AND the `codegen-version-marker`
comment in requirements.txt whenever `src/` changes or the App serves
stale code. **The mock lock was REMOVED 2026-09-01 (Soham's direction,
0.3.4)**: the App runs live Layer 2 via FMAPI
(`databricks-claude-opus-5`). The original reason for the lock — the
SP's CAN_QUERY being unverifiable by CLI — is superseded by the app's
declared serving-endpoint RESOURCE (`llm-endpoint`, CAN_QUERY), which
grants the permission declaratively. The UI's own gates remain (explicit
STTM choice, cost confirmation, mock on dry-run); re-lock by setting
`CODEGEN_FORCE_MOCK_PROVIDER=1` in app.yaml and redeploying. App
container restarts wipe
`inputs/databricks/` + `inputs/uploads/` fetches, runner state and the
output-mode selection (back to `notebook`) — re-fetch and re-select after
a restart. **First live run from inside the App: 2026-09-04**
(`demo_20260904_150435`, CV golden pair, 3 feeds PASS_WITH_FLAGS, 3/3
grounded via `databricks_fmapi`); volume fetch, upstream CAQH pairing,
decision writes and past-run reload verified the same day. **0.3.5 App
debugging lessons (2026-09-04):** (1) `WorkspaceClient` CONSTRUCTION
raises when auth cannot resolve (expired CLI refresh token locally; an
SP whose credentials don't resolve on the App) — `codegen.databricks
._client` now wraps it in `DatabricksTransportError`, so the routes
answer 502 with the SDK's message instead of a bare 500; (2) the UI no
longer hides a 502 on the volumes listing as "unconfigured" (only 503
hides the section) — the chooser shows the message + Retry; (3)
`/api/demo/live-available` carries the provider-specific `reason` and
the UI shows it (the old hardwired "no ANTHROPIC_API_KEY" text was wrong
on the FMAPI App); (4) the from-device upload endpoint (0.3.4's
`POST /api/demo/upload`) finally has UI buttons in the STTM chooser.
The deployed tree ALSO carries `inputs/standards/` (the six reference
documents the documents card lists as present: the SFMC FRD, the three
decks, the two EDO standards) — that directory no longer exists in the
local checkout, so redeploy with `databricks sync` WITHOUT `--full`
(never deletes remote files); `--full` would wipe it. **`databricks
sync` honours a `.gitignore` in the source dir** — a staged tree that
still carries the repo's `.gitignore` silently skips `ui/frontend/dist`,
`fixtures/contracts`, the golden workbook and the replay set (the
2026-09-04 first deploy shipped the OLD bundle that way): delete
`.gitignore` from the staged tree before syncing, then check the remote
`dist/index.html` names the freshly built hash. Every deploy restarts
the container, so past live runs under `out/` vanish with it.

## Demo panels + reference-document checks (added 2026-08-27, display/check only; UI trimmed 2026-09-18)

**UI state after the ACFC trim (2026-09-18):** the frontend has ONE page
for runs — "Generate" (`/modes`): a single "Choose documents…" modal
(STTM / FRD / VDD sections, a Clear per input), the output mode + the
conventions / IIG / playbook selectors, the Generate button and run
progress, then the two request-time check tables — which render ONLY when
`demo.input_documents` resolves to existing files (their endpoints carry
`configured: false` otherwise). Removed from the UI: the reference-
documents card + attach modal, the "Demo FRD" gap block, the Replay card,
the Past-live-runs list, the Demo-mode page, the metadata-sheet preview on
the Generate page (the Dashboard keeps it). **Deprecated, no UI consumer:**
`/api/replay/*`, `/api/demo/live-runs`, `/api/demo/input-documents`
(`/api/demo/load-live-run` survives for the post-run View-results button);
they stay for API compatibility and their tests, nothing new may depend on
them. The Layer-2 transport a run uses is decided once in
`codegen.reasoning.transport` (mock lock → Databricks runtime forces the
Foundation Model endpoint → configured provider → mock degrade) and the
card badge / confirm dialog word themselves from `/api/demo/live-available`.

The Run-modes card (now "Generate") grew config-driven panels — documents card
(`demo.input_documents`, env `CODEGEN_INPUT_DOCS_DIR` override),
source-files table + convention check (real FRD docx read live),
synthetic `databricks fs ls` block (`demo.databricks_paths` placeholders,
Option A), metadata-sheet preview for ACFC's metadata-driven framework
(`demo.metadata_sheet`, provenance-badged cells + xlsx download), and the
reference-document checks: the input-requirements deck's eleven rows
evaluated against the demo contract AND the real FRD document, plus the
two architecture decks' stated controls evaluated against the loaded run.
All of it reads documents at request time, caches nothing, commits
nothing, and NONE of it alters generated output — the generation path is
untouched and byte-stable (verified against tags `pre-demo-2026-08-27` /
`post-mgr-demo`). CLI twins: `demo-source-files`, `demo-metadata-sheet`.

### Deliberately NOT ported

Three frd-to-sttm features are deliberately absent (`jobs_runner.py`, the
`_sharepoint.py` shim, the duplicate-input short-circuit) — rationale in
`.claude/skills/code-gen-agent/references/deep-dive.md` § "Deliberately
NOT ported"; read it before porting anything from that repo. Running jobs
belongs to the client's framework, never to the agent.

## Branching model

All development on `staging`; `main` is the deployment branch — `staging`
merges to `main` only after testing.

## Fixtures & data rules

**No FRD/STTM material is in this repo — as of 2026-08-22.** On Arjun's
instruction that no client documents (raw or derived) live in any repo,
`fixtures/contracts/` (two of which were contracts derived from *real*
client FRDs, plus the MIDS STTM, the synthetic CAQH STTM and the CV/golden
pair), `fixtures/workbooks/`, `fixtures/replay/`, and the gitignored `out/`
and `reports/` (generated pipelines embedding CAQH/MIDS field names) were
deleted from the working tree and `git rm`'d. They remain in git history
until a purge is decided. What changed to keep the repo coherent:
`config.contracts.pairs` is `[]` (the model no longer requires ≥1 pair);
`codegen generate-all` and the demo UI's startup generate refuse loudly on an
empty list; `codegen generate --frd-contract X --sttm-contract Y` still works
with explicit paths; the `demo:` config section keeps its (anonymized-universe)
file names but the files are absent, so Live/Replay fail with file-not-found
until anonymized copies are restored; every fixture-driven test skips with an
explicit reason rather than failing (`tests/conftest.py` `require_fixture_files`
/ `_pair_paths`). Restoring anonymized fixtures at the configured paths
re-enables the full test suite unchanged. The anonymized CV/golden set
(demo FRD + STTM contracts, golden workbook, and the `live_e2e_20260807`
replay set) survives at `044752e^` and may be restored **working-tree-only**
with `git show "044752e^:<path>" > <path>` — never `git checkout`, which
would stage and re-track the paths (done locally 2026-08-25; the MIDS/CAQH
client-derived contracts must NOT be restored **on staging**).

**The 2026-08-22 removal was partially reversed — differently per branch.**
On **staging**, three fixture families are tracked again by deliberate
`.gitignore` re-includes: `fixtures/faq/` (per-feed load-pattern FAQs),
`fixtures/reference/` (the SCRUBBED SFMC client reference artefacts +
`SCRUB_REPORT.md`; raw exports live only in gitignored
`inputs/reference_raw/`, `scripts/scrub_check.py` is the denylist
scanner) and `fixtures/workbooks/synthetic_segmented_golden.xlsx`; the
client documents themselves stay untracked (root-anchored `.gitignore`
guards block stray `*FRD*`/`*STTM*`/`*CAQH*`/`*MIDS*`/`*SFMC*`/`*RFC*`
files at the repo root). On **main**, commit `b0560af` (2026-08-28,
"Track FRD/STTM documents and contracts in the repo") reverses the
removal outright on a program go-ahead (reported by Soham, 2026-08-28,
reconfirmed in-session 2026-08-31 — the commit message is the only
in-repo record): main tracks the MIDS/CAQH client FRD/STTM documents,
the CV-golden demo fixtures, the sfmc contracts and the
`live_e2e_20260807` replay set. The branches therefore DISAGREE about
client documents. **Reconciled at the 2026-09-01 staging→main merge
(Soham):** main KEEPS its b0560af-tracked client documents and fixtures
(the program go-ahead stands) while taking staging's `.gitignore`
(gitignore patterns never untrack already-tracked files, so the tracked
documents survive under staging's guards — they only block NEW strays);
staging itself continues to hold no client documents. Apply the same
resolution at future merges unless the program policy changes.

**2026-09-18 (M6):** b0560af's merge had left the four root-level MIDS/CAQH
client documents and the SFMC client-derived contract pair tracked on
staging; `git rm` / `git rm --cached` removed them (the SFMC FRD contract
carried the client prod-support DL — the one scrub hit no other fix could
clear). MAIN still tracks all six by the program go-ahead; apply the same
removal there if policy requires. `scripts/scrub_check.py` over every
tracked file is now zero hits and must stay so.

Offline fixtures only — tests and dry-run generation must pass with zero
credentials and zero network. No real client data, ever (on staging); any
new fixture material must be anonymized/scrubbed first AND tracked by a
deliberate decision — every current re-include (faq/, reference/, the
synthetic segmented golden) was added that way, one path at a time, never
a directory blanket.
Generated output is byte-stable by design — no timestamps or randomness in
generated files; keep it that way (extract-sttm: inject `--generated-date`).

## Known gaps / cautions

- **There is no live-credential `.env` in this repo** (an earlier claim in
  this file that one existed was stale).
- **`extract-sttm` has never been run on FRD→STTM's own output.** It is
  validated against *client* workbooks (the CV/golden pair is byte-tested),
  not against what `04_sttm_render` emits upstream. Checked 2026-08-21: the
  upstream `sheet_per_table` dialect does match this extractor's sheet
  names, band labels and header synonyms — but it emits no `Comment` column
  (→ `value_spec` empty) and no `Recycle Flag` column (→ the verbatim
  validation text, i.e. this repo's entire Layer-2 input, is dropped
  *silently*), and its `single_sheet` CAQH dialect is incompatible outright
  (no `MAPPING-` prefix, `Source Layout` vs `Source File Layout`, different
  header dialect). Closing that round trip is a real integration task; do
  not assume the pipeline joins up.
- **CAQH extracts for real (corrected 2026-09-01)** — segments as tables
  in both layers, identification derived from the STTM, recycle from the
  FRD's DQ requirement; the historical synthetic CAQH STTM contract is
  obsolete and the 2026-08-31 "two open source-team questions" are
  RETRACTED (the documents answer both — docs/SEGMENTED_MODE_DESIGN.md
  quotes them). TWO soft CONFIRM items remain, both cited: positional
  identification (STTM trailer marker) and per-segment audit-column
  scope (HDR/TRL follow the STTM's fewer audit rows, not the FRD's
  feed-wide wording). The generated segments module renders the DERIVED
  identification (trailer-marker + positional header) when
  `segmented_extraction` is present; `config.segments` discriminators
  are the legacy branch. The CAQH FAQ
  (`fixtures/faq/caqh_tpl_inbound_files.faq.yaml`) carries seven
  FRD-cited answers as of 2026-09-01 (load_frequency, has_header/
  has_trailer, dedup_within_file, existing_record_policy,
  data_integrity_checks, reject_threshold); is_master_file and
  target_tables_exist stay honestly unanswered → CAQH verdicts
  PASS_WITH_FLAGS with 10 flags. The MIDS STTM contract still predates
  the extractor.
- `FrdContract._provenance.ambiguities` accepts plain strings (older
  contracts) AND the structured `GatedAmbiguity` objects current
  frd-to-sttm output emits; absent context keys there are not drift.
- Layer-2 candidate **approval merge is deliberately v2**: the UI records
  approve/reject decisions (`ui/backend/state/decisions.json`, gitignored),
  but merging into generated code stays manual; decisions don't gate.
- `ui/backend/service.py::GenerationStore._generate_feed` mirrors
  `cli._generate_feed` step for step — keep them in sync if CLI
  orchestration changes. UI runs are always dry-run + skip-tests.
- Generated job JSON cluster shape/schedule is a config guess; only "Weekly
  Monday 8 PM" compiles to cron, MIDS ships unscheduled. The client's
  pipeline stack is unknown — output targets plain PySpark + Workflows,
  structured for a mechanical DLT port.

## Debugging
After two failed fix attempts on the same problem, follow the spiral-breaker skill
(.claude/skills/spiral-breaker/SKILL.md) before trying anything else. When extracting
facts from FRD/STTM documents, apply its Pattern C citation rules. Log resolved
spirals in docs/spiral-log.md.
If I say a past problem was a spiral that wasn't caught, log it with the
spiral-breaker Step 3 template, Caught by skill: no, including the known-causes
entry and replay scenario.
If the spiral-detector hook reports a signal, treat it as coming from me: stop
fix attempts and follow the spiral-breaker skill before the next change.
