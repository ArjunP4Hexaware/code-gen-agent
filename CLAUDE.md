# CodeGen / Data Engineer Agent — working notes

## NEWEST — IIG validation (state as of 2026-10-14 night, `feature/multi-table`, post50)

Scoring the agent's IIG workbooks against prod "golden" IIG rows — pair_2 (SD) first, for Venu.
Deliverables: DDL / `metadata_inserts.sql` + the IIG workbook (runbook / playbook out of scope).

**RESTART HERE (2026-10-15, post51; `CHANGELOG_ACFC.md` has the five items).** Head = the
bump commit after b95f39c. Item 0 (the post50 LEAK_GATE_BLOCKED 9 → 3 hits) was closed
"unclassifiable from current reports" (the gate writes 4-field stubs); the gate fix is
Genie's — it should emit per-hit JSONL (`output_file, pattern_class, term_sha256,
occurrences`), classified at home with `tools/hit_lookup.py`.
- `codegen.run_errors.first_error_line` + `codegen.term_hash.term_sha256` are STABLE APIs
  the harness imports. Config fields renamed in Python only: `discovery.thresholds`
  (YAML `validate`), `dml.db_schema` (YAML `schema`).
- Environments are PROFILES (D1 / A2 / PR): `codegen-state/environments/<name>.yaml`
  over the overlay block; a required key (storage account, containers) unset =
  `QUESTION run.environment.<key>`, exit 3. The suite runs on its own synthetic D1
  profile (`tests/environment_profiles/d1.yaml`; fixture `no_environment_profiles`
  opts out). ACFC must place `codegen-state/environments/d1.yaml` or every run exits 3.
- The ACFC-side overlay `codegen-state/overlays/<profile>.yaml` (after acfc_env.yaml)
  holds notebook names / versions, status sets, per-feed SRC_FILE_NAME styles
  (`docs/acfc/OVERLAY_FIELDS.md`); both `codegen-state/` folders are gitignored.
- Pre-push: `tests/test_tracked_scrub.py` vs the hashed rows in `docs/acfc/LEAK_LEDGER.md`
  (68 known hits / 18 rows; `scripts/scrub_check.py --rebaseline`); local terms via
  `CODEGEN_SCRUB_DENYLIST`.
- Home SD scorecard (three SD rows, `IIG test cells.xlsx`): diff 1 / 1 / 3, per-cell
  verdicts identical to c3f2153 (not 0: SCHEMA_DRIFT_FLAG Y vs N is the known round-6
  conflict; individual-risk OBJECT_NAME / SRC_FILE_NAME).

**RESTART HERE (2026-10-14, after post50).** Pushed head `5ae6644` (0.5.8.post50), tree clean;
verified there: 1561 passed / 28 skipped, ruff clean, scrub clean on every line since 147af25.
The post50 report was given. **Waiting on D1 — nothing to code at home until Soham brings:**
1. **The D1 golden SRC_COLUMNS cells** (ADLS_DELTA + STGDELTA, pair_2 / pair_12). Home
   comparison (masked, given in the report): SD — current = the strict
   `source_column:target_column` reading (ADLS 86 pairs, STGDELTA 90). CAQH ADLS — current
   `Display:Display` (STTM display names), strict `Display:STAGE_COL`, golden
   `STAGE_COL:STAGE_COL` (neither matches; rule 4's variant matched 18/18). CAQH STGDELTA
   trailer — strict 9 pairs (own STTM audit rows) = golden; current 10 (adds LOB). If the
   cells confirm rule 4: `git cherry-pick 49d3e73 3b0082d` from local `wip/src-columns-rule4`
   (overlay `src_columns_style: source_target` + `audit_columns_from_sttm`), suite, bump.
2. The D1 dump for rule 2's PIPELINE_DESCRIPTION shapes (provisional; per-LOB fan-out cell
   left open by choice) and the D1 workspace-folder token (notebook path, home CAQH 40.0).
Home CAQH (mock, no LOB answers, vs p45 golden): 78.4 (baseline 77.2; 79.1 with rule 4).
Run-level inputs at home: environment, storage_account, application_name, email_to,
email_statuses; per feed 5 (4 pipeline names + active_start_date).

**post50 (2026-10-14) — four follow-ups** (marker **0.5.8.post50**): rule 4 (SRC_COLUMNS)
REVERTED pending the D1 golden cells (0132080; kept on local branch `wip/src-columns-rule4`);
2b01346 the handler two-notebook forms only for EDI 834 feeds (`edi_feed_patterns`: 834 / EDI
tokens in source / file patterns / name; else the single notebook, `_TPL` for TPL; NOTE names
the rule, `_notebook_rule`); 46272ce `gate.derivations.list_columns` (notebook NAME / PATH:
comma list OK when every segment passes); 12605b8 NullCheck / DeDup INPUT_PARAM = the stage
table FQN (`_target_fqn_cell`; owed items + FAQ companions dropped; open + NOTE only when the
catalog is unset — the environment's INPUT_NEEDED asks); bf1b6dc `email_status_input`
(run-level `INPUT_NEEDED run.email_statuses`, default all four; an answer trims the rows) +
iig_diff `status_columns` → `status-not-in-golden`. Home CAQH 78.4 (email 11.5 → 21.4).

**post49 (2026-10-14) — the client framework owner's rules 1–5**, one commit each
(8a2108d, 86bcc16, 8e4c65c, 49d3e73, 7d59a3f), marker **0.5.8.post49**; tests in
`tests/test_framework_owner_rules.py` + the touched files.
1. **PIPELINE_NAME is BSA-assigned.** ACFC `pipeline_roles` carry no name (`name: None`);
   owed cells `per_flow` on schedule + notebook: `INPUT_NEEDED
   feeds.<feed>.pipeline_name.<flow>` (FAQ companions `pipeline_name_<flow>`; answers_for maps
   `.`→`_`). iig_v2 email has no PIPELINE_NAME. iig_diff: `bsa_columns` → status
   `bsa-owned` (never missing / scored; `bsa_cells` cells + golden_filled).
2. **PIPELINE_DESCRIPTION long shapes** (corpus_cells values; short forms in `alternatives` +
   `alternative_shares`, NOTE only; `per_lob` + `per_lob_share`: a LOB-fan-out feed's ONE
   file_to_stg row is left OPEN with each LOB's description in the NOTE). Shapes provisional
   until the D1 dump of pair_2 / pair_12 cells — overlay-editable.
3. **FILE_ADLS empty for MFT** (`file_adls_rows: per_file`, `mft_landing_markers:
   [mftlanding]`; `metadata_template.mft_landing`): headers only + `iig_file_adls_mft` NOTE;
   non-MFT = one row per ADLS_DELTA row. iig_diff `mft:` block: ALL_FILES alias retargeted to
   ADLS_DELTA, FILE_ADLS presence `empty-by-rule`. pair_11's FRD landing is itself under
   mftlanding.
4. **SRC_COLUMNS** `src_columns_style: source_target` (source names when EVERY one is an
   identifier, else the stage columns throughout, verbatim) + `audit_columns_from_sttm` (a
   table's own STTM audit rows, in order). Home CAQH: ADLS SRC_COLUMNS 0 → 18/18, STGDELTA 3/3,
   ADLS TGT_COLUMN_NAMES 18/18; TOTAL 79.1 (no LOB answers). SD unchanged.
   **REVERTED on the branch (Soham: wait for the D1 golden cells)** — kept on the local
   branch `wip/src-columns-rule4` (49d3e73 + 3b0082d); re-apply with `git cherry-pick`
   once the D1 SRC_COLUMNS cells confirm the reading.
5. **Header check** — iig_diff `header_report` / `compare_headers` (score.json `headers`,
   console HEADERS first, `## Headers` first in sheets.md). Home CAQH: 2 golden-side issues
   (notebook DQ_NOTEBOOK_PATH / DELETE order = iig_v1's; email CRETAED_BY / CREATED_AT).
- Spiral: hook (a) on the rule-4 audit test — my oracle guessed the row layout; logged.

**post48 (2026-10-14) — the D1 exemption replaced by the provider.** A NAMED
environment with a key unset (blank / any `<<ENV:...>>`, D1's included) is FATAL
only under provider=live and no `--dry-run` (`environments._complete(live=)`; CLI
`cli._live_run`; App `_execute` checks it before the run folder exists) — the
message names every key, nothing written. Under mock: one `INPUT_NEEDED
run.environment.<key>` each (`unset_items` now covers named environments), cells
empty; a placeholder catalog is left unset (`catalog_unset_reason`,
`default_catalog_unset`), never written. At home every run now lists
`run.environment.storage_account` (D1's placeholder). `tests/test_d1_placeholders.py`
is the live-only check: conftest keeps the operator's `CODEGEN_PROVIDER` as
`CODEGEN_PROVIDER_REQUESTED`; started live it FAILS on any `<<D1:...>>` (10 at home).

**Restart here (2026-10-14, post47).** Three small items, marker **0.5.8.post47**:
- **Catalogs + connection ids per environment.** `EnvironmentConfig` gains
  `catalog_map`, `default_catalog`, `connection_ids` (acfc_env.yaml: D1 real, QA /
  PROD `<<QA:...>>`); `conventions.catalog_map` / the acfc_prx `default_catalog` /
  the ADLS connection-id constants are gone from the overlay. Readers:
  `codegen.environments.catalog_map` / `default_catalog` (resolver `map_catalog`,
  `emit.framework._config_default_catalog`); ADLS connection ids are
  `environment_cells` (`connection_ids.<name>`). Catalog cells get an `iig_env:`
  NOTE (`metadata_template._catalog_env_notes`). A NAMED environment (selected or
  default) with any key unset FAILS naming every key (`_complete`; superseded by
  post48 above: fatal only under provider=live). A CUSTOM one inherits nothing: missing keys stay unset,
  their cells empty (an unset catalog: `catalog_env_unset:<layer>` flag, DDL for
  that layer not written, never FAIL), one `INPUT_NEEDED run.environment.<key>`
  each, header `environment: SANDBOX (custom, N keys unset)`; `inputs.run:
  environment.<key>` fills one on a rerun.
- **INPUT_NEEDED scoping.** `owed_cells.<..>.scope: run` (APPLICATION_NAME,
  EMAIL_TO; NOTE prefix `iig_owed_run:`) + the environment = RUN-level: printed
  once before any feed (`owed_inputs.run_block_lines`), one block at the top of
  each feed report (`run_block`), `inputs.run` in answers_template.yaml. Feed-level
  keys are now `feeds.<feed_id>.<name>` (`inputs.feeds.<feed>`); the flat
  `feeds[<i>].` keys still read (`answers_template.flatten_inputs`). App banner
  groups by `scope`; `DemoRunner._run_level_inputs` (NOT `_run_inputs` — that is
  the documents tuple).
- **LOB question in the App dialog.** `resolver.lob_question_item(spec)` = a
  layout question of kind `files` (the unkeyed files, the FRD codes as
  candidates); the App appends it to the Answers-needed list, passes the gaps
  answers to the contract resolver (`resolve_pair(gaps=)` — it was never passed)
  and writes the applied ones to `<run>/answers.yaml` (`write_applied_answers`,
  every value quoted). Frontend: `LayoutQuestions` kind `files` (a `<select>` per
  file, posted `"<file>=<code>; ..."`), `pickFile`.

**Restart points post36–post46 moved verbatim to `docs/CLAUDE_HISTORY.md` §[H2].** Rules still in force:
- Owner rule (post45): a corpus value fills a cell only when `patterns.json` states it; anything else is a `<<D1:NAME>>` placeholder (`codegen.config.is_d1_placeholder`) — the cell stays OPEN with an `iig_d1_placeholder:` NOTE, never the placeholder text; `tests/test_d1_placeholders.py` is the live-only check (post48 above). → §[H2] post45
- `MetadataTemplateConfig.corpus_cells` (per tab / header; `by:` flow / status / frequency / notebook_kind, `shares`, `offer`, `alternatives`; NOTE `iig_corpus:`) never overwrites an FAQ / FRD / STTM-stated cell; `owed_cells` carry `default`, `when`, `header`, `scope: run`. → §[H2] post45, post46
- INPUT_NEEDED is NON-blocking (`codegen.owed_inputs`): exit 0, the cell written empty, the key under `inputs:` in `answers_template.yaml`, `generate --answers` fills it; NEEDS_ANSWERS = QUESTION / UNRESOLVED lines only; `scripts/run_round.py` records INPUT_NEEDED keys and keeps going. → §[H2] post45
- Environments: `environments:` in `acfc_env.yaml` with exactly one default; CLI `generate --environment NAME | --environment-file PATH`; neither = the default + `INPUT_NEEDED run.environment`; report header `environment: <name> (default|selected|custom)`. → §[H2] post46
- LOB lookup: FRD Region / LOB table → plan-id column → region (REG# token) → `conventions.lob_reference`; files still unkeyed = ONE blocking QUESTION `feeds[<i>].lob_by_file`, answer values QUOTED; gate `iig_single_value` (LOB, CLAIM_TYPE*, flags, TGT_PARTITION_VALUE) fails a list in a single-value cell. → §[H2] post46
- iig_diff (`tools/iig_diff.py` + `tools/iig_keys.yaml`): default `--pair-mode identity` (golden feed × flow from `docs/acfc/iig_goldens/01_pair_group_index.csv`); `--pair-mode key` is the old natural-key rule — never use it for a score. → §[H2] post40
- iig_diff statuses: `convention_columns` (generated names) never pair or score; FeedScope marks other feeds' rows `out-of-scope`; `sheet_aliases` map v1 ALL_FILES ↔ v2 FILE_ADLS; `group-level` agent master rows are not scored. → §[H2] post38, post40, post42, post44
- iig_diff outputs: `--dump-row SHEET[:N]` and the `RAW` / `FILE NAMES` / `RULES (D1 only)` blocks are D1-only console; `--export-scrubbed DIR` must re-scan to 0 hits; score.json / diff.xlsx / routing.csv carry prod text and are never committed; CREATED_BY / UPDATED_BY values are withheld. → §[H2] post43, post45
- Provider: ONE switch, `--provider` > `CODEGEN_PROVIDER` > `reasoning.mode` > mock, never inferred from the runtime; `--dry-run` under live prints `WARNING provider=live overridden by --dry-run → mock` first; conftest sets `CODEGEN_BLOCK_LIVE_MODEL` (live tests only with `CODEGEN_ALLOW_LIVE_TESTS=1`). → §[H2] post38
- Model JSON: `layout/model.py::parse_json_response` + one `RETRY_INSTRUCTION` retry for layout and Layer 2 (`reasoning/providers/ask.py::ask_candidate`, truncation retried at `reasoning.truncation_max_tokens`); failures logged `LAYER2 FAILED` / `RAW (D1 only)`. → §[H2] post43, post44
- Build identity: `codegen.build_info.build_identity()` on the CLI's first line, `codegen doctor` and `/api/health`; `generate` writes `CODEGEN_BUILD.json`; iig_diff refuses an agent workbook without one. → §[H2] "Build identity"
- D1 runs, home reviews: the prod goldens (`docs/acfc/iig_goldens/*.xlsx`) exist only on D1 — never force-add; Genie pushes scrubbed evidence to `acfc-results` / `acfc-pairing-check`, read here in place with `git show`, never checked out. → §[H2] "D1 runs, home reviews"
- Pushing: once per clone `git config core.hooksPath scripts/git-hooks`; pre-push refuses a code push with an unchanged version, a requirements marker ≠ pyproject, a tracked `_build.py`, or `ui/frontend/src` changed without `dist`; bump with `python scripts/bump_version.py`; docs-only pushes need no bump. → §[H2] "Pushing"
- Round gate: `python scripts/doc_fingerprint.py --compare docs/acfc/fingerprints/pair_2_sd_home.json <D1 fingerprint>` — a HARD line = STOP, WARN recorded; value hashes HMAC under the gitignored `codegen-state/fingerprint.key`. → §[H2] "Round gate"
- ACFC output is framework mode: `output.profile_mode: {acfc_prx: framework}` makes the App default to framework; a DDL column identifier must match `^[A-Za-z_][A-Za-z0-9_]*$` (`gate/ddl_names.py`). → §[H2] post36
- Document roles by name: `demo_sources.classify_document_name` (a role token anywhere, `iig` is never an input), `pairing_key` / `match_by_name`; a `pairing_overrides.yaml` (or `--pairs-file`) wins over everything. → §[H2] post37
- Blank Schema / TableName in an STTM band: schema from the FRD with a NOTE, else a QUESTION; table names are always a QUESTION, never derived. → §[H2] "Blank Schema / TableName"
- Home run recipe: `codegen layout --frd-contract-out … --answers …` (`--require-complete` exits 3 while an owed item is open; `--report-unresolved` lists them) → `extract-sttm` → `generate --feed <id> --output-mode framework --profile acfc_prx --iig-template iig_v2 --skip-tests --dry-run` with `PYTHONUTF8=1` and outputs in a scratch dir. → §[H3] item 2, §[H2] post43
- `tools/iig_diff.py --golden <xlsx> --agent <every feed's *_IIG.xlsx>` (scored as their union; `--scope feeds` default; `--golden-structure` describes the golden's shape). → §[H2] post38, "iig_diff"
- `tools/iig_fill_rate.py --corpus docs/acfc/iig_goldens <email csv> --agent <outputs> --patterns <dir> [--top N]` (D1 only; the scrubbed `patterns.md` comes home). → §[H2] post44, post45
- `scripts/iig_scorecard.py --generated <feed>_IIG.xlsx --real "IIG test cells.xlsx" --real-table <table> [--all-sheets]` is the older per-row scorecard (pair 1 / SD rows). → §[H3], §[H4]
- Tests by area (all current; the moved text describes each): provider / transport `test_provider_mode.py`, `test_transport.py`, `test_layer2_failures.py`, `test_layout_json_response.py`; iig_diff `test_iig_diff_identity.py`, `test_iig_diff_sheet_alias.py`, `test_iig_fill_rate.py`, `test_iig_scorecard.py`; IIG cells `test_iig_v2_derivations.py`, `test_iig_cheap_misses.py`, `test_derivations.py`, `test_pair4_full_golden.py`; answer lines `test_answer_labels.py`, `test_layout_gap_labels.py`, `test_cold_pairs.py`, `test_pyx_questions.py`, `test_multi_sheet_feed_ids.py`, `test_format_from_extension.py`, `test_audit_annotation.py`, `test_mapping_general_first.py`; pairing `test_pairing_name_key.py`; launch / deploy `test_app_imports_tree_src.py`, `test_cli_launch_tree_src.py`, `test_ruff_dependency.py`, `test_health_probe.py`, `test_deploy_without_out.py`, `test_run_round.py`. → §[H2], §[H3], §[H4]

## Working rules (older branch notes moved to `docs/CLAUDE_HISTORY.md` §[H3] 2026-10-09 / §[H4] 2026-10-07)

- Branches: `feature/multi-table` = this checkout (all current work); `feature/iig-first` = the old demo branch `codegen-watch` pulled (post13) — never merge into it without Soham's word; `backup/ddl-only` = DDL-only fallback; `acfc/harness-exit3` = docs only (`docs/acfc/HARNESS_EXIT_CODES.md`, local a6b8002 NOT pushed — edit in a scratch worktree). → §[H3], §[H4]
- Others push to this branch from ACFC: `git fetch` and rebase before work, never force-push. → §[H3]
- Stage files explicitly, never `git add -A`; gitignored local-only files (never stage): `docs/acfc/denylist_local.txt`, `PROJECT_HANDOFF.md`, `CODEGEN_INDEPENDENT_REVIEW.md`. → §[H3]
- The real client SD documents + `IIG test cells.xlsx` at the repo root: read in place, mock runs only, outputs to a scratchpad, report SCORES only — never copy names into the repo, commits or replies. → §[H3]
- Exit codes 0 ok / 1 failed / 3 NEEDS_ANSWERS; answer lines `f"{label:<15}{key} — {reason}"` (`cli.answer_line`, key verbatim); QUESTION / UNRESOLVED only for answers owed, everything informational is NOTE; the harness regex is copied in `tests/test_harness_answer_lines.py`; details in `docs/ACFC_DEPLOY.md` "CLI exit codes". → §[H3] "Today's rules"
- An STTM band's layer comes only from evidence; source by elimination only for the one leftover band left of both evidenced target bands (owner rule 5cbaf63); anything else stays `UNRESOLVED <sheet>/band[<n>]/layer`. → §[H3] Chunk A
- `framework/metadata_inserts.sql` is the client's "DDL": one INSERT per IIG row, an open cell = unquoted `<<COLUMN#n>>`; rules via `dml.db_value_map` / `dml.db_null_columns`; `config_inserts_<env>.sql` is retired. → §[H3] "What the branch does"
- `config/overlays/acfc_env.yaml` is committed and ALWAYS applied first by `load_config`; `CODEGEN_CONFIG_OVERLAYS` adds on top (later wins); `CODEGEN_SKIP_ENV_OVERLAY=1` opts out and `tests/conftest.py` sets it, so a test that wants the overlay passes `overlays=[…]` and a fixture overlay carries every value its golden needs. → §[H4], §[H3] gotchas
- `acfc_env.yaml` pins the SD / CAQH family for EVERY feed; a PRX-shaped feed needs a feed overlay on top (splitting it per source family is still open). → §[H3] item 5, §[H4]
- Src-first: `src/codegen/_srcpath.py` (`ensure_src_first`, `child_env`) — every child launch passes `env=child_env()`; `codegen-watch` (not in this repo) must put `PYTHONPATH=<repo>/src` first itself. → §[H4] ca6bab8
- ruff is a base dependency; a missing ruff module = flag `ruff_unavailable`, PASS_WITH_FLAGS, never FAIL. → §[H4] 2c3c6d4
- Real reference files are TRACKED on origin (`IIG test cells.xlsx`, `d1_d1k.stg_doh/`, `d1_std.sdoh/`, `sd_community_demographic_risk.lvdash.json`); untrack / purge is Soham's call after the demo — `git rm --cached` would delete them from the ACFC checkout; never print CREATED_BY / UPDATED_BY. → §[H4] "Open / scheduled"
- Storage health: `ui/backend/health.py` probes every root (`GET /api/health`: principal, roots); App env + grants in `docs/ACFC_APP_ENV.md`. → §[H4] 9da340a
- Gotcha: bash heredocs mangle escapes and backticks — write patch scripts with the Write tool and run them as files; write commit messages to a file and `git commit -F`. → §[H3], §[H4]
- Gotcha: `fixtures/** -text` commits raw bytes — patch fixtures with `read_bytes` / `write_bytes`, keep each file's EOL, check `git diff --cached --stat` for whole-file churn. → §[H3]
- Gotcha: the CLI loads the local `.env` (its DL leaks the client domain into EMAIL_TO) — `export CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example` before a shareable run. → §[H3]
- Gotcha: `isolation: "worktree"` agents branch from the default branch — reset each to the working branch first, cherry-pick back, delete the `worktree-agent-*` branch. → §[H3]
- Gotcha: `;`-separated path lists get MSYS-converted — `export MSYS2_ENV_CONV_EXCL=CODEGEN_CONFIG_OVERLAYS` (or `PYTHONPATH`); the spiral-detector hook keys on the exact command string, so re-run the quoted command before trusting a "failing" signal. → §[H4] "Session gotchas"
- The local `.venv` has no lxml: install it to a scratch `--target` dir on `PYTHONPATH` to reproduce lxml-only bugs (the 2026-10-07 unreadable-xlsx bug was one). → §[H4] be4c6e4

## History moved out (2026-10-14)

`docs/CLAUDE_HISTORY.md` holds, VERBATIM: (first pass) the legacy demo branch
`fix/remove-mock-provider-ui-text` (M15–M15e), M9 + v0.5.1–v0.5.8-acfc, M8 and M7;
(second pass, tagged) §[H2] restart points post36–post46, §[H3] the 2026-10-09 START HERE,
§[H4] the `feature/iig-first` notes (2026-10-07), §[H5] FRD pairing, §[H6] the Databricks
volumes seam, §[H7] demo panels, §[H8] fixtures & data rules. Each rule still in force has a
one-line copy above or below with its § pointer. From the first pass:
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
  `claude-opus-5-5`; endpoint `databricks-claude-opus-5-5`). The Claude 4.8/5 API families reject sampling
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

## FRD pairing + upstream contracts (condensed; full text `docs/CLAUDE_HISTORY.md` §[H5])

- The run takes an (STTM, FRD) pair; the FRD comes from the `.docx` itself (`codegen extract-frd`, `extract/frd_docx.py`) or the upstream contract table (`read_table_rows`, SELECT-only — its first read wakes the warehouse = DBU spend). → §[H5]
- Selection-time pairing is by content (`codegen.pairing`, M8.2), then by name role (post37 rules above); a manual pick is never marked automatic, no match / ambiguity pairs nothing. → §[H5]
- FRD gap fill (`resolve/gapfill.py`): each fill is a `frd_unstated:<field> source_used:<cell>` flag; format / delimiter from the STTM meta row → VDD FILES → the file extension; stage load strategy STTM per layer → FAQ `load_mode`; domain / subdomain FRD-only; the STTM stage band is authoritative for catalog / schema / tables; the dialog asks only when sources disagree or are ambiguous. → §[H5] "FRD gap handling"
- One metadata block listing many files (`layout/resolve.py::split_frd_feeds_by_sttm`): one FRD feed per STTM mapping sheet, flag `frd_feeds_split_from_sttm:`, files paired by mutual unique token. → §[H5] "one-block / many-files"
- Client-document rule: a LIVE run sends document content to the model API — live runs on client pairs only per the client-document process (Venu's email approval); mock runs need no approval. → §[H5]
- Live runs are self-contained: `frd.contract.json` + `run_meta.json` in the run folder; completeness keys on emitted artefacts, so zero Layer-2 candidates is complete. → §[H5]

## Databricks volumes seam (condensed; full text `docs/CLAUDE_HISTORY.md` §[H6])

- `src/codegen/databricks.py` is a read-only edge (list + download) plus the confirm-gated `publish_artifacts` (every write through `_guarded_full_name` / `WRITABLE_PREFIX`); OFF as shipped (blank catalog / schema / volumes — opt in with `DATABRICKS_*`); table / job writes are NOT BUILT; the only SQL it may send is `EXPLAIN`. → §[H6]
- Auth: the named profile, unless `DATABRICKS_HOST` is set (Apps runtime) — never leave a placeholder `DATABRICKS_HOST` in `.env`; client construction failures become `DatabricksTransportError` (502). → §[H6] 0.3.5 lessons
- App deploy from a staged tree: delete its `.gitignore` (sync honours it and skips `dist`), `databricks sync` WITHOUT `--full`, then check the remote `dist/index.html` hash; bump pyproject + the requirements marker whenever `src/` changes (the runtime caches the env); re-lock to mock with `CODEGEN_FORCE_MOCK_PROVIDER=1` in app.yaml. → §[H6] "Databricks App deployment"

## Demo panels (condensed; full text `docs/CLAUDE_HISTORY.md` §[H7])

- One run page, "Generate" (`/modes`): the "Choose documents…" modal, output toggles, selectors, Generate; the request-time check panels render only when `demo.input_documents` resolves and never alter generated output. → §[H7]
- Deprecated with no UI consumer (kept for API compatibility; nothing new may depend on them): `/api/replay/*`, `/api/demo/live-runs`, `/api/demo/input-documents`. → §[H7]

## Deliberately NOT ported

Three frd-to-sttm features are deliberately absent (`jobs_runner.py`, the
`_sharepoint.py` shim, the duplicate-input short-circuit) — rationale in
`.claude/skills/code-gen-agent/references/deep-dive.md` § "Deliberately
NOT ported"; read it before porting anything from that repo. Running jobs
belongs to the client's framework, never to the agent.

## Branching model

Work happens on feature branches (now `feature/multi-table`; the branch list is under
"Working rules"). `staging` and `main` are untouched since the feature branches were cut;
nothing merges anywhere without Soham's word. `main` is the deployment branch.

## Fixtures & data rules (condensed; full text `docs/CLAUDE_HISTORY.md` §[H8])

- No client documents are tracked on staging / the feature branches; every fixture re-include (`fixtures/faq/`, `fixtures/reference/`, `fixtures/acfc_shapes/`, `fixtures/layout_profiles/`, the synthetic segmented golden) is a deliberate per-path `.gitignore` decision, never a directory blanket. → §[H8]
- `scripts/scrub_check.py` over tracked files must stay at zero new hits (the pre-existing ones are named in the restart notes). → §[H8] M6
- MAIN tracks the client documents (b0560af, program go-ahead); at a staging → main merge, main keeps them and takes staging's `.gitignore`. → §[H8]
- `config.contracts.pairs` is empty: `generate-all` refuses; generate with explicit paths; fixture-driven tests SKIP with a reason when files are absent (`require_fixture_files`). → §[H8]
- The anonymized CV / golden set may be restored working-tree-only with `git show "044752e^:<path>" > <path>` — never `git checkout`. → §[H8]
- Offline: tests and dry-run pass with zero credentials and zero network; generated output is byte-stable (no timestamps; extract-sttm takes `--generated-date`). → §[H8]

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
