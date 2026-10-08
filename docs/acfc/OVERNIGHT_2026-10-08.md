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

- **`config_inserts_<env>.sql` still gives every row one `@OBJECT_ID` /
  `@PIPELINE_ID` / `@GROUP_ID`** — the latent primary-key collision (design §2).
  Chunk B's brief said to leave that file unchanged; the new
  `metadata_inserts.sql` uses per-row placeholders (`<<OBJECT_ID#3>>`) instead.
  Decide whether to retire the older file or fix it.
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
primary key, STGDELTA OBJECT_NAME).
