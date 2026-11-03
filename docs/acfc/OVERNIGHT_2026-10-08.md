# Overnight 2026-10-07 → 10-08 — `feature/multi-table`

Unattended run. **Nothing was pushed.** Every chunk ended with ruff clean, scrub
clean on every changed file and the full suite green; the final suite is
**906 passed / 27 skipped** (version marker **0.5.8.post16**). Design and
status: `docs/acfc/MULTI_TABLE_DESIGN.md`; owner questions: its **§7a Friday
checklist**.

## What landed (oldest first, all local on `feature/multi-table`)

| Commit | What |
| --- | --- |
| `2a67c91` | Catalog precedence STTM band → FRD label → `default_catalog`; band / FRD disagreement = `catalog_conflict:<layer>` naming both; `catalog_map` matches case-insensitively and emits lowercase |
| `0c85b39` | Step 3 — ADLS rows = files (one per file into the detail table), STGDELTA rows = tables (target from the standard definition, mapped catalog) |
| `0a6efd7` | Step 4 — DQ keyed per file; `LoadHeaderAndTrailerToSeparateTablesRule` row per file only when header / trailer are their own tables; one "additional DQ rules (not generated)" — Engineer review entry per file |
| `9685f97` | Step 5 — pipeline schedule = four structural rows named by the convention when no inventory overlay supplies them; marker post15 |
| `8b94b9e` | **Chunk A** — every cell of every IIG sheet pinned for pair 1 (+ DDL bytes) and pair 4; feed-family conventions; ADLS `TGT_PRIMARY_KEY` blank when unknown; FILE_ADLS path shapes; a test-isolation fix |
| `686aad9` | **Chunk C** (step 7) — `scripts/iig_scorecard.py --all-sheets` (cherry-picked from a worktree agent) |
| `4fa9e78`, `eb9ff00` | **Chunk B** (step 6) — `framework/metadata_inserts.sql`; the CREATE reference text one block per table (cherry-picked from a worktree agent) |
| *(this commit)* | **Chunk D** — design doc, ACFC run doc, scorecard how-to, Friday checklist, this report; marker post16 |

Chunks B and C ran as two parallel agents in their own git worktrees (B: ~360k
tokens / 27 min; C: ~264k tokens / 15 min — inside the ultracode caps); I did A
first (both depend on it) and D meanwhile, then cherry-picked their commits and
re-ran the integrated suite.

## Row counts per sheet

| Sheet | pair 1 (PRX family) | pair 4 (CAQH-style family) |
| --- | ---: | ---: |
| DATA_FACTORY_PIPELINE_SCHEDULE | 4 (inventory overlay) | 4 (convention rows) |
| FILE_ADLS_INGESTION_DETAILS | 1 | 1 |
| ADLS_DELTA_INGESTION_DETAILS | 4 (four patterns, no LOB) | 6 (one per LOB file) |
| STGDELTA_STDDELTA_INGESTION_DET | 1 (one table) | 3 (HDR / DTL / TRL) |
| ADLS_FIXED_WIDTH_HANDLER | 3 (fixed-width segments) | 0 (pipe-delimited) |
| DATABRICKS_NOTEBOOK_DETAILS | 3 (inventory overlay) | 1 (no inventory) |
| DATA_QUALITY_RULES | 8 (4 files × date + cast; no split row) | 6 (one split row per file) |
| EMAIL_TEMPLATE_CONFIG | 2 | 2 |
| `metadata_inserts.sql` INSERTs | 26 | 23 |
| CREATE blocks in `<FEED>_DDL.txt` | 2 (byte-identical to the golden) | 6 (3 stage + 3 standard) |

Both IIGs are pinned cell for cell: pair 1 against the client golden (every
cell equal / open-and-flagged / masked sequence / a pinned deviation), pair 4
against `fixtures/acfc_shapes/pair_4/golden/IIG_EXPECTED.yaml` (exact, all eight
sheets). Scorecard, generated pair 1 vs its golden: **TOTAL 57.9** (schedule
51.6, FILE_ADLS 29.4, ADLS 68.1, STGDELTA 67.5, fixed-width 60.9, notebooks 33.3,
DQ 61.5, email 31.2); every row paired; every DIFF one of the pinned deviations,
every ALIAS a masked OBJECT_ID, the rest open cells (engineer / environment /
audit values the inputs do not state). Both goldens score 100.0 against
themselves.

## What failed

Nothing is red. Not done / still open:

- ~~**`config_inserts_<env>.sql` still gives every row one `@OBJECT_ID` /
  `@PIPELINE_ID` / `@GROUP_ID`**~~ — **resolved in the morning cleanup**: the
  file is retired, its DB-side knowledge ported into `metadata_inserts.sql`
  (see "Morning cleanup" below).
- **Pair-1 cells that still differ from the golden** — all open framework
  questions, each pinned with its reason in
  `tests/test_m4_acceptance.py::FULL_DEVIATIONS`: per-pipeline / per-file
  FREQUENCY, per-file SOURCE, STGDELTA SOURCE, HEADER_FLAG on a fixed-width
  file, the first object's Overwrite and the notebooks' refresh type (FRD says
  Append), MANDATORY_FIELD_LIST (ours = the STTM's not-null columns, golden
  blank), EMAIL_TO (environment).
- Both worktree agents' worktrees were created at `main` (4c35c61), not at the
  branch head; each reset its own branch to `8b94b9e` before working (no effect
  on the result; logged as a spiral-hook false trigger in `docs/spiral-log.md`).
  The worktrees and their branches (`worktree-agent-*`) are still on disk —
  delete them when convenient.

## What I decided (the brief left these open)

1. **Your first Chunk A rules contradicted the pair-1 golden** (LOB `ALL`,
   STGDELTA `TGT_PRIMARY_KEY` blank, STGDELTA OBJECT_NAME = generalized pattern;
   the golden — aliased AND raw — has blank / `NA` / `Accumulator_accumclient`).
   Your correction made the golden the authority: the three cells are
   **`family_conventions`** (`metadata.templates.iig_v2`), pair 1's overlay pins
   the PRX family, pair 4's the CAQH-style family; no "decided difference"
   entries remain.
2. **Pair 1's STGDELTA OBJECT_NAME is a transcribed literal** in the pair-1
   overlay (`stgdelta_object_name: literal`), cited as such: no input derives
   `Accumulator_accumclient`, and inventing a formula to match it is the pattern
   CLAUDE.md forbids.
3. **Shipped default family** (what real ACFC runs get, the ACFC overlay sets
   none): the PRX family's `lob: blank` and `stgdelta_unknown_primary_key: "NA"`
   (the real golden backs them) with `stgdelta_object_name:
   generalized_file_pattern` (the PRX family's own form has no derivation).
4. **ADLS `TGT_PRIMARY_KEY` = the Stage band's Primary Key cells, else blank and
   open** — the old natural-key fallback (the not-null columns) is gone; the
   pair-1 golden is blank there.
5. **The pair-4 golden** gained the four sheets it lacked (FILE_ADLS 1 row,
   FIXED_WIDTH 0, NOTEBOOK 1, EMAIL 2 — hand-derived from the inputs and config
   before comparing), and its STGDELTA OBJECT_NAME / unknown primary key follow
   the CAQH-style family as your rules state them (`NWB_COB_RPT`, blank). Its
   environment overlay gained `FILE_ADLS_INGESTION_DETAILS.TGT_ADLS_PATH =
   {landing_rel}` and the generator now applies configured FILE_ADLS shapes
   (pair 1 has none — unchanged).
6. **Test isolation fix:** `cli.main()` re-reads the operator's `.env`
   mid-suite, so a session fixture built after a CLI test carried the real
   `CODEGEN_NOTIFICATION_EMAILS`; the full-cell `EMAIL_TO` check exposed it. The
   suite now strips the machine-local overrides after every test.
7. **Scorecard** (Chunk C): scores all **eight** iig_v2 sheets (the brief said
   seven); a golden's masked `SYN-OBJ-<n>` against a run's `<n>` is ALIAS;
   score = 100 × (matched + alias) / cells, unmatched rows count against it.
8. **metadata_inserts.sql** (Chunk B): in the DDL artefact group (the M7 labels
   test pins the DML group at six files); every blank that is not a decided
   blank becomes a placeholder (stricter than the brief's NULL-for-other-badges —
   no undecided value can run); line breaks kept as `+ NCHAR(10) +`; standard
   CREATE columns = the rows carrying a Standard band (pair 4: 7 / 19 / 5).

### Test expectations changed — each because the brief changed the behaviour

| Test | Change | Instruction |
| --- | --- | --- |
| `test_m4_acceptance::EXPECTED_BLANK` | ADLS OBJECT_ID / DQ OBJECT_ID filled; + ADLS TGT_PRIMARY_KEY blank | OBJECT_ID sequence (steps 3–4); "TGT_PRIMARY_KEY blank when unknown" (Chunk A) |
| `test_m4_acceptance::test_shipped_config_carries_no_client_pipeline_names` | four convention rows named from the FAQ abbreviation (`ACCUM`) | step 5 |
| `test_iig_review::INVENTORY` (pair 1, pair 11) | owner counts | OBJECT_ID convention, STGDELTA `NA`, ADLS PK open, step-5 rows, the family literal |
| `test_multi_table_step2` | three STGDELTA rows, not one | step 3 |
| `test_pair4_multi_table_fixture` | OBJECT_ID 1..n; convention pipeline names; eight goldened sheets; STGDELTA family values | steps 3–5, Chunk A |
| `test_iig_v2_derivations::test_named_style_is_overlay_selectable` | reads the detail table's fields | step 3 (ADLS columns = the detail table's) |

No golden value was changed to make a check pass; the pair-1 golden is untouched.

## Friday (2026-10-09)

`docs/acfc/MULTI_TABLE_DESIGN.md` §7a: the five questions (catalog names in the
real STTMs, the d1 standard container, the STGDELTA OBJECT_NAME convention,
`TGT_PRIMARY_KEY` semantics, which DQ rule classes are standard) and the three
"confirm which convention is current for new feeds" items (LOB, STGDELTA unknown
primary key, STGDELTA OBJECT_NAME), and — added in the morning cleanup — item 9,
**`ACTIVE_FLAG` `Y` vs `S`** (unconfirmed); item 10, **`DAY_OF_SCHEDULE` `0` vs
NULL**, was added 2026-10-09 under the same question (which one does the
database honour?). Session brief: `docs/acfc/FRIDAY_2026-10-09.md`.

## Morning cleanup (2026-10-08, before the push) — marker 0.5.8.post17

Pushed as one commit on `feature/multi-table`; **not merged into
`feature/iig-first`** (codegen-watch pulls that one; it stays the stable demo
branch until after Friday). Verified: full suite **912 passed / 27 skipped**
(Python 3.11); ruff clean (`src/ tests/ ui/backend/ scripts/iig_scorecard.py`);
scrub 0 on every changed file.

1. **`metadata_inserts.sql` is written on every framework run**, independent of
   `emit_dml` / `dml.enabled`; those switches now gate only the runner notebooks
   `Insert_scripts_config_table_<env>.py` (which run `metadata_inserts.sql` and
   refuse while a `<<…>>` placeholder is left). ADDITION.md's switch line and the
   report's DML line say "`metadata_inserts.sql` is written regardless".
   **Pair 4 regenerated through the CLI with shipped settings**
   (`extract-sttm` + `generate --output-mode framework --profile acfc_prx
   --iig-template iig_v2`, overlays `acfc_env.yaml` → the pair-4 overlay, DML
   switches off): `framework/metadata_inserts.sql` present, 23 INSERTs (= the IIG
   rows), no runner notebook, gate `metadata_inserts=ok`, `PASS_WITH_FLAGS`.
   Test: `test_metadata_inserts::test_pair4_with_shipped_settings_writes_metadata_inserts`
   (+ `test_dml_emit::test_shipped_settings_write_metadata_inserts_and_no_notebook`
   for pair 1 through `cli._generate_feed`).
2. **`config_inserts_<env>.sql` retired — after porting its DB-side knowledge**
   (amended brief). `emit/dml.py` now writes only the notebooks; `config_rows.xlsx`
   stays the approval artefact; ADDITION.md says `metadata_inserts.sql` replaces
   the old file and why (one placeholder per row ends the shared `@OBJECT_ID` /
   `@PIPELINE_ID`). Ported into `metadata_inserts.sql`:
   - **DB values**, config `dml.db_value_map` (`ACTIVE_FLAG` and
     `ACTIVE_RULE_FLG`: workbook `Y` → `S`), `dml.db_blank_expressions`
     (`CREATED_DATE` / `UPDATED_DATE` → `GETDATE()`), `dml.db_null_columns`
     (`DAY_OF_SCHEDULE`, `UDF2`–`UDF5`, the SLA columns, `CLAIM_TYPE_ID`), blank
     `CREATED_BY` / `UPDATED_BY` → `@RFC_NUMBER`; a `DB VALUES` header block names
     every mapping and cites `METADATA_DB_SEMANTICS.md` (§1, §2, §7, §10). The
     workbook keeps `Y`. Friday checklist item 9 (unconfirmed).
   - **Guards before the first INSERT**: `@RFC_NUMBER` assigned; every
     placeholder id not NULL (the old `IS NULL` checks, per row); per schedule row
     `PIPELINE_ID` unused; per FILE_ADLS / ADLS_DELTA / STGDELTA row `GROUP_ID`
     unused in its table and the (GROUP_ID, OBJECT_ID, PIPELINE_ID) key unused.
   - **Connection reuse** (§3): look up the file connection by host + root path
     (more than one match aborts), else insert it and take `SCOPE_IDENTITY()`;
     a NULL host with no id given aborts.
   - **Abort, never half-insert**: `SET XACT_ABORT ON` + `BEGIN TRY` /
     `BEGIN TRANSACTION` … `COMMIT` / `CATCH` → `ROLLBACK` + `THROW`.
   Tests: `tests/test_dml_emit.py` (rewritten: DB values, variables + guards +
   connection lookup, abort structure, FAQ-filled variables, value map is
   config, notebook refuses placeholders) and `tests/test_metadata_inserts.py`.
3. **`config/overlays/acfc_env.yaml`** pins `family_conventions` to the CAQH-style
   (pair-4) family — `lob: codes`, `stgdelta_unknown_primary_key: ""`,
   `stgdelta_object_name: generalized_file_pattern` — commented as the convention
   observed in the newest real sheet and on the Friday checklist; a pair-1 family
   feed selects its own in a feed overlay.
4. **Scorecard breakdown.** Every score line now ends `| matched M /
   open-by-design B / open-for-engineer E / diff D; score excl. open-by-design X`.
   Generated pair 1 vs its golden: `score 57.9 … | matched 347 / open-by-design
   185 / open-for-engineer 46 / diff 21; score excl. open-by-design 83.8`.
   How-to updated (`IIG_SCORECARD_2026-10-07.md`, "Reading the score").
5. **Worktrees / branches deleted:** `worktree-agent-aa12743afd2705dd7` and
   `worktree-agent-aba6dee66207d7353` (worktrees clean; every commit already on
   this branch as its cherry-pick — `git cherry` showed all equivalent; never on
   origin), plus the scratch `.local/old_tree` worktree used for the diff below.

### Old `config_inserts_q1.sql` vs new `metadata_inserts.sql` on pair 1 — every remaining difference

Both generated from the same pair-1 run (old: the tree at `54ecaad` with the DML
switches on; new: this commit), INSERT cells compared column by column (script:
`.local/overnight/diff_old_new.py`, gitignored). Row counts per table are equal
(26 IIG rows + the connection insert). **No ported value differs**: ACTIVE_FLAG /
ACTIVE_RULE_FLG `'S'`, audit dates `GETDATE()`, audit users `@RFC_NUMBER`, the
NULL columns and `SRC_CONNECTION_ID` are identical. What still differs (201 cells
across 71 table.column pairs, by kind):

| # | Old | New | Cells (columns) | Why |
| --- | --- | --- | ---: | --- |
| 1 | `@PIPELINE_ID`, `@PARENT_PIPELINE_ID`, `@GROUP_ID` — one script variable for every row | `<<PIPELINE_ID#n>>`, `<<PARENT_PIPELINE_ID#n>>`, `<<GROUP_ID#n>>` — one placeholder per row | 37 (12) | the brief: one placeholder per row fixes the collision (design §2) |
| 2 | `@OBJECT_ID` on every row | ADLS_DELTA / DQ: the IIG's sequential literal (`N'1'` … `N'n'`); FILE_ADLS / STGDELTA: `<<OBJECT_ID#n>>` | 14 (4) | OBJECT_ID = 1..n within the group (steps 3–4); the old variable collided across ADLS rows |
| 3 | `@SRC_ADLS_CONNECTION_ID`, `@METADATA_CONNECTION_ID`, `@TGT_CONNECTION_ID` (script variables; FAQ `connection_ids` could fill them) | per-row placeholders (the ACFC overlay's ADLS_DELTA constants fill them on real runs) | 15 (6) | only `SRC_CONNECTION_ID` has a lookup (§3); the other three are IIG cells like any other. **FAQ `connection_ids` now feeds only `SRC_CONNECTION_ID`** |
| 4 | `NULL` for an open blank cell | `<<COLUMN#n>>` | 107 (38) | step-6 rule: an open cell must be decided (a value or NULL) before the script parses; a decided blank stays NULL |
| 5 | `CONCAT(@PATH_PREFIX, N'…')` on path columns | `N'…'` (the same literal inside) | 28 (11) | `dml.env_path_prefix` was empty in every environment; environment paths are IIG cells (overlay `path_patterns`) |

Structural differences (not cell values):

- **One file, not three.** `config_inserts_q1/a2/prod.sql` differed only in the
  variables block (`@ENV`, `@PATH_PREFIX`); `metadata_inserts.sql` has no
  environment variable — fill its placeholders per environment. The runner
  notebooks stay one per environment (`dml.environments`).
- **Variables block.** Old: 13 `DECLARE`s, each flagged `dml_unassigned` when the
  FAQ left it open (pair 1: 10 flags). New: `@RFC_NUMBER`, `@SRC_HOST_NAME`,
  `@SRC_ROOT_PATH`, `@SRC_CONNECTION_ID` only (pair 1: 2 flags — `@RFC_NUMBER`,
  `@SRC_HOST_NAME`; the per-row ids are flagged by the IIG's `iig_blank` flags
  and the review copy). FAQ answers for `pipeline_id`, `parent_pipeline_id`,
  `group_id` and `object_id` are no longer read (one value cannot fill several
  rows).
- **Guards really abort.** The old preflight `RAISERROR`s (severity 16) ran
  outside any `TRY` and without `XACT_ABORT`, so the batch carried on into the
  INSERTs and only the notebook's JDBC rollback undid them. The new guards
  `THROW` inside the TRY, so nothing runs after a failed guard, whether or not
  the caller rolls back. New: the per-row key guard (GROUP_ID, OBJECT_ID,
  PIPELINE_ID) and a guard on every row's GROUP_ID, not just one.
- **The connection lookup no longer skips a NULL host.** Old: no host → no
  lookup, `SRC_CONNECTION_ID` left NULL. New: no host and no id given → abort.
- **No `SELECT … @@ROWCOUNT` lines.** Old: one after each table block — it
  reported only the LAST INSERT's count (1), not the table's. The gate check
  `metadata_inserts` asserts the counts at generation time instead (one INSERT
  per IIG row); the notebook still prints any result set a script returns.
- **Multi-line cells.** Old: `NULL` + flag `dml_multiline`. New: lossless
  `+ NCHAR(10) +` concatenation. (No pair-1 cell is multi-line; same output
  there.)
- **New in the header:** the `DB VALUES` block, the `TABLE DEFINITIONS` index
  (each table's stage / standard definition by its mapped three-part name), the
  per-row `-- table … <- file …` labels, and empty sheets kept as a header line.
- **Gate checks.** `dml_parse_<env>` and `dml_row_counts` are gone with the old
  file; `metadata_inserts` (statement count = IIG rows, parses as T-SQL with the
  placeholders read as NULL) covers both.

### Test expectations changed in the cleanup — each follows from items 1–2

| Test | Change |
| --- | --- |
| `test_dml_emit` (rewritten, 12 tests) | the retired script is not written; the notebooks run `metadata_inserts.sql`; DB values / guards / connection / abort / FAQ variables |
| `test_metadata_inserts` | the cell rule with DB values; written with the switches off; the round trip applies the value map |
| `test_framework_output::test_framework_mode_tree_and_verdicts` | + `metadata_inserts.sql` in the CV framework tree |
| `test_iig_review::test_addition_lists_both_workbooks_and_both_switches` | switch text "off — no runner notebook (disabled) …; `metadata_inserts.sql` is written regardless" |
| `test_m102_location_uri` (2) | read `metadata_inserts.sql` instead of `config_inserts_<env>.sql` |
| `test_m4_acceptance::PAIR1_GATE_FLAG_KINDS` | `dml_unassigned` 10 → 2 |
| `test_m4_acceptance::test_pair1_default_profile_writes_two_files_and_no_combined_ddl` | + `metadata_inserts.sql` |
| `test_m5_rfc_package` (3) | the package carries `metadata_inserts.sql` instead of `config_inserts_*.sql` (SFMC: + `metadata_inserts.sql`) |
| `test_m7_labels_semantics` (3) | `metadata_inserts.sql` in the DDL group; DML group = 3 notebooks; README / manifest name the new file; its manifest row carries the `dml_*` flags |
| `test_m9_acfc_findings::test_cli_chain…` | console check `metadata_inserts=ok` instead of `dml_row_counts=ok` |

No golden was changed.
