---
paths:
  - "src/codegen/**"
  - "config/**"
  - "tests/**"
---

# The pipeline's rules (how a run works, config, outputs, seams, known gaps)

Loaded by Claude Code when it works on a file under `src/codegen/` (the `paths` above);
Codex and anyone else: the root `AGENTS.md` points here - read it before changing the
extractors, resolver, emitters, gate or config. The repo-wide rules (the ones that never
bend, working rules, tests) stay in the root `AGENTS.md`. Moved here verbatim from it on
2026-11-10.

## How a run works

- **Inputs:** an FRD `.docx` (or the upstream FRD→STTM contract table, read SELECT-only),
  an STTM `.xlsx`, optionally a VDD `.xlsx` (feeds only the IIG fixed-width rows and the
  `vdd_*` gate flags, never the standard layer). Selection-time pairing is automatic
  among local candidates (`codegen.pairing`: content, ticket number, name role; a
  `pairing_overrides.yaml` wins); a manual pick is never marked automatic; no match or
  ambiguity pairs nothing. **Only the FRD and STTM are mandatory** (Soham, 2026-11-09): a
  run never stops for a VDD - a dictionary is asked about only when it shares content
  with the pair (score > 0) or an override names a missing one (post184).
- **Layout recognition** (`src/codegen/layout/`, `docs/LAYOUT_RECOGNITION.md`): a model
  decides WHERE things are, code copies the values, a validator sits between. Order:
  cache → synonyms → model → validate → user. The model sees only fingerprint material
  (header regions, table labels — never a data row) and no model string reaches a
  contract, DDL or IIG cell. One exception (Soham, 2026-11-05, post176): a cell of the
  INGESTED FRD the reader refused, for a field no other document fills - the model sees
  that one cell's lines and answers a LINE NUMBER only; the code copies the line, the
  field's vocabulary validates it, `frd_model_located:` flags it (`layout/cell_locate.py`). A sheet with no header row (no 3+ cell row in 25: a
  lookup / valid-values sheet) is CAPPED: the fingerprint hashes it, the model gets its
  summary line only (`fingerprint.model_region`) — keep the cache key and the prompt
  separate there. A model claim that validates carries the DOCUMENT's wording (the label
  cell as written, the inline pair as the cell spells it; `labelled_rule` derived, never
  the model's flag), and a model FRD claim under a path it was not asked about is
  dropped. A layout `Rejection` holds coordinates and vocabulary only — never a cell's
  text, a model string or a model-invented sheet name (it reaches the state log, the
  REJECTED lines and the "structural labels only" report). Families A, C and E may legitimately leave roles unresolved
  under synonyms alone (`tests/acfc_shapes/layout_truth.py`) — do not widen the synonym
  tables to force them; a header seen in a client document is evidence, one invented to
  close a fixture gap is not.
- **Documented shapes:** `docs/acfc/SHAPES_FOR_PORT.md` — STTM families A–E, FRD families
  F1 / F2, VDD patterns V1–V3. The non-`MAPPING-` STTM reader is `extract/generic.py`.
- **Extraction rules:** `feed_id` = `normalize_feed_name(FRD feed_name)` (the resolver's
  join invariant, not the stage table). An STTM band's layer comes only from evidence
  (source by elimination only for the one leftover band; else `UNRESOLVED
  <sheet>/band[<n>]/layer`). Blank Schema → from the FRD with a NOTE, else a QUESTION;
  table names are always a QUESTION. Trailing `NA` rows → `audit_columns`. A Length cell
  is a byte width only when it is an INTEGER. An empty schema never reaches a contract.
  One non-segmented STTM sheet whose tables are EXACTLY the FRD's (post156): a feed per
  table (`layout.resolve._split_per_table`, `extract.generic._split_by_table`), every
  pairing from the documents (standard table from its rows, file pattern by file
  identity) or blank + flagged - never token overlap. When the FRD names no table
  (pair_09) it is not split (parked with the RDMS sheet; RESTART.md).
  **A TableName cell that LISTS tables** (post179, `extract/list_cells.py`): one
  mapping for parallel feeds is split by POSITION (feed i = the i-th name of every
  list cell + the i-th line of File Names) only when File Names states as many files;
  else no split; a segmented sheet splits too (post180). **One standard table per
  stage table** (post181, every sheet, `generic._one_standard_table_per_stage`): the
  DDL / IIG model (`metadata_template._table_groups`) builds one, so a row naming
  another keeps stage, standard blank + flagged - never silently dropped. An FRD
  target-table cell holding a nested table is read by its table column, never its
  header words.
  **The STTM is authoritative for a feed's table set** (post160, Soham 2026-11-02): FRD
  stage tables no STTM field maps are set aside, never silently (flag
  `frd_tables_set_aside:stage` + NOTE + one non-blocking INPUT_NEEDED) - only when that
  is the feed's one disagreement and the FRD's tables were not copied from the STTM
  band; everything else stays a contract mismatch (`contracts.sttm_authoritative_tables`).
  Segmented (H/D/T) files: segments are tables in both layers, identification derived
  from the STTM (`extract/segmented.py`, `docs/SEGMENTED_MODE_DESIGN.md`). A stated
  delimiter (any document) is read by `resolver.delimiter_char` (quoted character, else
  `extractor.delimiter_words`) — never "the character after a word". Recycle Flag
  cells: a `no_values` word is an unflagged row, every other non-empty cell must be a
  `Y ( <validation> )` flag; differing rules stop the extraction, never a silent pick.
- **A cell of `<label>: <value>` lines** (post168/172/175, `frd_docx.split_labelled_lines`):
  each line whose label is a known synonym of a single-value field (file format,
  frequency, source system, delimiter) fills that field where its own row is absent or
  blank (a stated row is never overwritten - `frd_cell_line_conflict:`); a line no field
  knows is skipped and named (`frd_cell_line_ignored:`, Soham's option B); a cell with an
  unlabelled (prose) line is refused whole. New spellings: config or the App's learned
  labels, never a code edit. The parser self-extension plan: `docs/PARSER_SELF_EXTENSION.md`.
- **Agreement between documents** goes through `gapfill.same_value(a, b, words)`: a
  punctuation-only value normalizes to '' — compare delimiters as characters (pass
  `extractor.delimiter_words`), never by `normalize` substring tests.
- **Gap fill** (`resolve/gapfill.py`): each fill is a `frd_unstated:<field>
  source_used:<cell>` flag; the STTM stage band is authoritative for catalog / schema /
  tables; the dialog asks only when sources disagree or are ambiguous.
- **Answers:** QUESTION / UNRESOLVED lines are blocking, INPUT_NEEDED is not, NOTE is
  informational. Answer lines are `f"{label:<15}{key} — {reason}"` (`cli.answer_line`,
  key verbatim; printed sheet keys are `sheets[<i>]/<layer>/<role>`); `generate
  --answers` / the App's dialog fill them. **Proposed is not applied:** a proposal is
  written only when chosen (`profile_default` values are the exception — written
  unasked, changeable). **A blank answer** (post170, Soham: "a blank answer is still
  better than no answer"): the reserved `answers.leave_blank` token on an
  `answers.blankable_fields` value (file format / delimiter / frequency) lets the run
  through - those cells blank + flagged, one non-blocking INPUT_NEEDED, the DDL unchanged;
  an empty answer is still no answer; the token never reaches an artefact.
- **Verdicts and outcomes.** Each feed's gate verdict is PASS / PASS_WITH_FLAGS / FAIL
  (`docs/WORKFLOW.md`); a flagged feed is PASS_WITH_FLAGS by design, not a failure. The
  run outcome (`codegen.run_stages.OUTCOMES`; exit codes in `docs/ACFC_DEPLOY.md`):
  PASS / PASS_WITH_OPEN_INPUTS (workbook written, every open line non-blocking) = exit 0;
  NEEDS_ANSWERS (any blocking line open) = exit 3; GATE_FAIL (files complete, moved to
  `<feed>/quarantine/` + `GATE_FAIL.md`), CRASHED (partial files deleted), FAIL (nothing
  written) = exit 1.
- **Error lines are two tiers** (`codegen.run_errors`, STABLE — the harness imports it):
  `first_error_line` = coordinates only (vocabulary + integers), `first_error_line_full`
  = quoted, written only under the outputs role. A new raise that quotes document text
  goes through `run_errors.located(exc, Coord(...), "<REASONS code>")`.
- **Layer 2** is its own stage after the outcome (`codegen.layer2_stage`, one request per
  feed): `--layer2 now | defer | skip`; config `reasoning.layer2_cli: now`,
  `reasoning.layer2_app: defer` (pending = `<feed>/candidates/layer2_pending.json`, asked
  by `codegen layer2` or `POST /api/demo/layer2`). For ACFC it is OFF: the
  `reasoning:` block at the top of `config/overlays/acfc_env.yaml` sets both to `skip`
  (Soham, 2026-10-27) — delete that block to turn it back on. Tests that exercise a
  Layer-2 mode with the ACFC overlay loaded pin the mode on their config.
- **One generate entry point:** `cli.generate_feed_result` + `codegen.generate_run
  .GenerateRun`, driven by the CLI and the App alike (the App's
  `GenerationStore._generate_feed` wraps it); manifests are byte-identical for the same
  pair (`CODEGEN_STAGES.json`).

## Config doctrine

- **Every knob lives in config;** no numeric literals in generator logic; the loader is
  loud on typo'd keys. Pydantic v2 models are `frozen=True` + `extra="forbid"`; missing
  is `None`, never a default. PHI masked to last-4 at every egress. A placeholder a
  reader stores for "no document states it" (the .docx reader's `unstated` source,
  `contracts.frd.UNSTATED_SOURCE`) is read through its helper (`stated_source`) — it
  never reaches an artefact as a value; the cell is blank + flagged.
- **Overlays:** `config/overlays/acfc_env.yaml` is committed and ALWAYS applied first by
  `load_config`; `CODEGEN_CONFIG_OVERLAYS` adds on top (later wins); client-shaped
  vocabulary lives in overlays, never in the tracked config.yaml. It pins the SD / CAQH
  family for every feed — a PRX-shaped feed needs a feed overlay on top.
- **State root** (`CODEGEN_STATE_DIR`, `config.state_root()`): `environments/<name>.yaml`
  (D1 / A2 / PR profiles; exactly one default; a required key unset under mock =
  `INPUT_NEEDED run.environment.<key>`, under live = fatal before anything is written),
  `overlays/<profile>.yaml` (notebook names, status sets, per-feed overrides —
  `docs/acfc/OVERLAY_FIELDS.md`), `answers/`, `leakgate/`. Not in git. On the App,
  `codegen.state_mirror` copies a workspace / volume state root read-only.
- **The provider switch** (`codegen/reasoning/mode.py`) — ONE switch, mock | live, never
  inferred from a configured endpoint or the Databricks runtime. First that answers
  wins: `--provider` > `CODEGEN_PROVIDER` > `reasoning.mode` (shipped: `mock`) > mock. It
  governs both model users (layout + Layer 2). `--dry-run` and
  `CODEGEN_FORCE_MOCK_PROVIDER` / `CODEGEN_FORCE_MOCK_LAYOUT` force the mock (under live
  that prints a WARNING first); live with its endpoint / key unset fails at startup,
  never a quiet degrade. `reasoning.provider` (`databricks_fmapi`, endpoint
  `databricks.serving_endpoint`) picks the live transport; `anthropic` (key-gated) also
  exists. Model name: `reasoning.model`.
- **FMAPI responses** from extended-thinking Claude come back as a LIST of typed blocks —
  `codegen.databricks.chat` normalizes via `_chat_content_text`. Do not "simplify" that
  to `content or ""`. Model JSON goes through `layout/model.py::parse_json_response` with
  one retry.
- **Engineering standards** live as data in `engineering_standards:` (EDO naming
  patterns + abbreviation tables) and `job:`; clause-by-clause map + deviations in
  `docs/EDO_STANDARDS_ALIGNMENT.md` (being revisited — RESTART.md). **A naming
  standard's abbreviation table is a LOOKUP, never a constant** (Soham, 2026-11-09,
  post186): the product / sub-product codes are read from the FRD through tables 3.2 /
  3.3 (`codegen.naming_codes`; none / several = open, a name that needs the code is
  asked - except 3.3's own "No Sub-Product" code, written WITH a flag). Every
  PIPELINE_NAME is sourced part by part in the feed report and the run's LOG.md ("How
  the names were built", `codegen.naming_provenance`) - keep that when names change.
  The prefix is the run's orchestrator (post187, Lokesh via Soham): ADF = `PL_` (the
  default), a Databricks Workflow = `WF_`, the rest of the name unchanged - a RUN choice
  (App Advanced options / `generate --orchestrator`), since no FRD / STTM states it.
  The RFC's TDD states it; a prod IIG's prefix is NOT evidence (Lokesh, 2026-11-10:
  pair_12 is a Workflow, its prod IIG's PL_ names are wrong - never score a WF_ run
  "back" to PL_).

## Output modes and artefacts

- `output.mode: notebook | framework | [notebook, framework]` (`codegen/output_modes.py`
  is the one vocabulary; CLI `--output-mode`, repeatable). The retired spellings `both` /
  `rfc` / `all` map to notebook + framework with a one-time notice, never an error.
  `output.profile_mode: {acfc_prx: framework}`; the App offers only `output.app_options:
  [framework]` and shows `output.app_files`.
- **Framework mode is what ACFC deploys:** an ADDITION to the client's existing
  metadata-driven framework. A feed whose FRD states a database-table source
  (`framework.table_source_formats`) is table ingestion, not built yet (the RDMS sheet):
  it writes its DDL + test cases and HOLDS the IIG (no IIG / review / config rows /
  inserts; a flag, a HELD BACK line, one non-blocking NOTE) - never file-ingestion rows
  for a table (post155). Per feed: the deployment DDL (per conventions profile),
  the IIG workbook + its BSA review copy, `framework/metadata_inserts.sql` (one INSERT
  per IIG row; an open cell = unquoted `<<COLUMN#n>>`), `config_rows.xlsx`, and
  (acfc_prx) the DDL test cases `<ABBREV>_DDL_TestCases.txt` — a
  SEPARATE file, never inside the DDL (Venu): read-only SQL the engineer runs after the
  DDL, gate `ddl_tests_read_only`; the same cases as `<ABBREV>_DDL_TestCases.xlsx` in the
  client's test-record layout (post154; the tester fills the result columns). Per run and
  STTM, `<out>/combined/<STTM>_{IIG.xlsx, IIG_REVIEW.xlsx, DDL.txt, DDL_TestCases.txt,
  DDL_TestCases.xlsx (one sheet per feed), LOG.md}` (`codegen.run_artefacts`; the STTM token is dropped from the name;
  run-level rows written once, children never merged). The LOG.md replaced the per-feed
  `ADDITION.md` (post178): it carries each feed's HELD BACK / PROVENANCE notes; a
  `--feed` run writes no combined set, so its feed's report is the record. Framework
  mode still renders the full pipeline in a scratch tree so gate verdicts match across
  modes. The master
  notebook is ACFC's own — the agent never generates, edits or ships it.
- **Notebook mode** (Option A, ~10% case): a standalone PySpark pipeline; `acfc_prx` uses
  notebook v2 (`emit/notebook_v2.py` + `templates/notebook_v2/`, rendered from the IIG
  rows). It never calls `partitionBy` — the DDL clusters every table (`CLUSTER BY AUTO`)
  and Delta clustering is incompatible with partitioning; `TGT_PARTITION_COLUMN` /
  `_VALUE` only scope an Overwrite (`replaceWhere`). Under `acfc_prx` stage columns are
  typed as the STTM states them (Soham, 2026-10-29) and the DDL is the reference: the
  notebook casts each stage column to the ADLS row's TGT_DATA_TYPE before the write, and
  a non-blank value the type cannot read stops the load — never a silent NULL.
- **Conventions profiles** (`conventions.profile`; default `edo_sfmc`): `edo_sfmc` = two
  `.txt` DDL files with per-column COMMENTs, CLUSTER BY AUTO + TBLPROPERTIES;
  `acfc_prx` = ONE combined `<ABBREV>_DDL.txt` (Soham, 2026-10-29: never split per
  layer), stage columns typed as the STTM states (Soham, 2026-10-29),
  every whitespace quirk of the pair-1 golden a knob, compared byte for byte; its column
  / table COMMENT, primary-key note and standard TBLPROPERTIES are knobs too (on in
  config.yaml, off in the pair-1 overlay so that golden stays exact). To add a
  profile: a key under `conventions.profiles`, a golden under
  `fixtures/acfc_shapes/<pair>/golden/`, a byte-identity test like
  `tests/test_m4_acceptance.py`. A DDL column identifier must match
  `^[A-Za-z_][A-Za-z0-9_]*$` (gate check `ddl_identifiers`, `gate/ddl_names.py`).
- **The DDL is RUN by the engineer** (Soham, 2026-10-26), not a reference only: every
  statement must be safe to re-run against deployed tables (`CREATE TABLE IF NOT EXISTS`,
  never `CREATE OR REPLACE` there) and terminated — `create_statement` (default `CREATE
  TABLE IF NOT EXISTS`) feeds BOTH layouts; only the pair-1 fixture overlay pins OR
  REPLACE for its golden. Two gate checks enforce it: `ddl_parses` (sqlglot, dialect
  `gate.ddl_parse_dialect`; a parse error, an unrecognised statement or a CREATE OR
  REPLACE fails; sqlglot is a base dependency, absent = `sqlglot_unavailable`, never
  FAIL; the pair-1 overlay sets the dialect null — its golden is unterminated) and
  `ddl_identifiers` (on the table definitions; a name as stated that is no identifier
  fails, naming layer / table / position — the agent never rewrites it, the STTM is
  fixed). ACFC's prod DDL template is the
  target; `tools/ddl_shape.py` scores the agent's DDL structure against it (counts and
  property names only — prod files read into a scratch dir, never the repo).
- **The standard-table TBLPROPERTIES are ACFC's template verbatim** (post185; Lokesh,
  2026-11-10: "keep the properties as is, this was suggested by Databricks") - the
  reader / writer 1 / 2 and `predictiveOptimization` lines included; never "correct"
  them.
- **DDL string literals** escape a quote with a backslash (`\'`); `''` is no escape in
  Databricks SQL (DBR 18+ reads `'a''b'` as two chained literals). The `sql_literals`
  gate fails a doubled quote. A COMMENT is the STTM's description, never a Comments
  cell (rule text) and never an audit marker (`NA`).
- **IIG templates** (`metadata.template`): `iig_v1` = the 7-tab SFMC reference; `iig_v2`
  = the PRX 8-sheet layout, rows from `metadata_template.py`. Every cell is transcribed
  from an input, a cited constant or an answer; the rest is blank and flagged
  (`iig_blank:<SHEET>: <columns>`). A corpus value fills a cell only when `patterns.json`
  states it; anything else is a `<<D1:NAME>>` placeholder kept OPEN, never written. To
  add a template: a key under `metadata.templates` with `tabs` transcribed from the
  client's workbook, `always_blank`, the knobs, a `citation`; client inventory rows go in
  an overlay; pin headers + blank list in a test. **DATA_QUALITY_RULES only where a
  document states the rule** (post171, Soham: "if we're arguing about things in the prod
  IIG that's automatically wrong"; `dq_stated_only` in the ACFC overlay): DeDup only on an
  FRD-stated duplicate check (STTM Primary Key columns), NullCheck on the fields the STTM
  names for a DQ check (the STTM wins over an FRD "NA"), no cast rule; whatever is only
  derivable is an `iig_dq_not_generated:` suggestion in the review copy, never a row.
- **Scoring vs prod goldens:** `tools/iig_diff.py --golden <xlsx> --agent <every feed's
  *_IIG.xlsx>` with the default `--pair-mode identity` (`--pair-mode key` never for a
  score); `score.json` / `diff.xlsx` / `routing.csv` carry prod text and are never
  committed; `--export-scrubbed DIR` must re-scan to 0 hits. Build identity:
  `codegen.build_info` (`CODEGEN_BUILD.json`; iig_diff refuses a workbook without one).
- **Gate flags worth knowing:** `drag_fill_suspect` (≥3 adjacent `Decimal(p,s)` stepping
  p by one — flagged, never altered), `segments_from_sttm` / `file_pattern_from_sttm`,
  `vdd_*`, `iig_blank`, `iig_single_value` (a list in a single-value cell fails),
  `decimal_no_precision`, `source_names_repeated`. ruff missing = `ruff_unavailable`,
  never FAIL.

## Edge seams (network stays at the edges)

The generator's inputs and outputs are files on disk; seams attach before and after.
Keeping the network out of resolve / emit / gate is what keeps Layer 1 deterministic and
offline — **do not call Graph or Databricks from inside the extractors or the resolver.**
- **SharePoint** (`sharepoint.py`, stdlib-only): `codegen sharepoint-fetch` /
  `sharepoint-publish` (publish is the human gate). Read
  `.claude/skills/code-gen-agent/references/sharepoint-seam.md` before touching it.
- **Databricks** (`databricks.py`, the `[databricks]` extra): read-only list + download,
  plus the confirm-gated `publish_artifacts` (every write through `_guarded_full_name` /
  `WRITABLE_PREFIX`); table / job writes are NOT BUILT. Auth: the named profile unless
  `DATABRICKS_HOST` is set (the Apps runtime) — never leave a placeholder
  `DATABRICKS_HOST` in `.env`. Client-construction failures become
  `DatabricksTransportError` (502).
- **Storage roles** (`storage/`, `CODEGEN_STORAGE_*`): local | workspace | volume; Can
  Manage (not Can Edit) on the state / outputs / inputs folders. Health: `GET
  /api/health` (`ui/backend/health.py`; principal, roots, version).
- Deliberately NOT ported from frd-to-sttm: `jobs_runner.py`, the `_sharepoint.py` shim,
  the duplicate-input short-circuit (`.claude/skills/code-gen-agent/references/
  deep-dive.md`). Running jobs belongs to the client's framework.

## Known gaps

- `extract-sttm` has never been run on FRD→STTM's own output: its `sheet_per_table`
  dialect emits no `Comment` / `Recycle Flag` columns (Layer 2's input would be dropped
  silently) and its `single_sheet` dialect is incompatible. Closing that round trip is a
  real integration task.
- `FrdContract._provenance.ambiguities` accepts plain strings AND structured
  `GatedAmbiguity` objects.
- Notebook v2's own tests mostly SKIP (their SFMC fixtures were removed 2026-08-22): a
  notebook change needs its own test on a synthetic pair (pair 4 renders one), and no
  generated Spark code is executed here (no Java).
- Generated job JSON cluster shape / schedule is a config guess; output targets plain
  PySpark + Workflows, structured for a mechanical DLT port.
