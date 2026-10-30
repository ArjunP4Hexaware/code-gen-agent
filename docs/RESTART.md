# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
CLAUDE.md). What each version did: `CHANGELOG_ACFC.md`.

## State (2026-10-30 — post157)

- **Branch** `feature/multi-table`: pushed, working tree clean. App `codegen-agent`
  deployed from post157 (2026-10-30), smoke green (Generate `/` + Results `/results`:
  200, no console errors). post155 / post156 went out first (deployed as post156). Both
  suites green on every version.
- **UI audit (2026-10-30, Playwright on the local App, mock, pair 4) -> post157:** loading
  states on Generate / Results, no sideways scroll at 390 px, 24 px targets, the logo out
  of the tab order, one `h1` on the Report tab. Not done (optional, not asked): lazy-load
  prism / marked (one 374 kB bundle), the published source map in `dist`. Scripts:
  `/tmp/t/ux/audit.js` (numbers only), `small.js`, `overflow.js`, `flash.js`.
- **This session's App work** (CHANGELOG_ACFC.md): post143 the guided look of the STTM
  agent's App (UX skill Part 1 "Design pillars"); post144 Generate is `/` (Results
  `/results`, `/modes` redirects) and the client's logo top-left, read from the state
  root `branding/logo.png` (uploaded to the App's workspace state folder; never in git);
  post145 the confirm dialog's new-pair layout cost in DBUs (`reasoning.dbu_rates`,
  `demo.new_pair_layout_estimate` until a run measures it — 6–8 DBU since post148, Venu's
  conservative approximation); post146 the run's
  progress bar; post147 the environment line inside Advanced; post148 the feed Overview
  in the Results layout, new-pair estimate 6–8 DBU; post149/150 client-facing text and
  generated files name no person; post151 "Generate Documents" again; post152 the run
  card under the Generate button; post153 the DDL test cases' column check (0-based);
  post154 the client's pipeline-level test cases (load strategy on a second file, a
  second file, several files, one email case per IIG status) + the test-record
  workbook `<ABBREV>_DDL_TestCases.xlsx` (Aruna's layout; combined: one sheet per feed).
- **DDL test on D1 (Soham, 2026-10-29; Venu asked whether the DDL is functional).**
  Schema `d1_dlk.soham_test` created (owner Soham's account, managed, comment says
  disposable; empty again after the test). Warehouse: Serverless Starter
  `063a5140dc0f34b1` (Soham's choice). Runner: `/tmp/t/ddlt_run.py <work dir> <warehouse>`
  — scratch copies of each combined `_DDL.txt` / `_DDL_TestCases.txt` retargeted to
  `d1_dlk.soham_test.<schema>__<table>` (information_schema filters follow, record-count
  parameters bound to 0), DDL run twice (the re-run proves it is safe to re-run), every
  test-case statement run, counts / test ids / error classes printed only, tables dropped.
  Results (mock harness on the 12 client pairs, code post152; client copies deleted):
  - DDL: pairs 01, 02, 04, 11, 12 — every statement OK on the first run AND the re-run
    (48 statements; tags set). pair_03 (GATE_FAIL, quarantined) — 2 statements do not
    parse, 2 depend on them: the DDL the gate already refused; its STTM needs a look.
    Pairs 05, 06, 09 (FAIL) and 07, 08, 10 (NEEDS_ANSWERS) wrote no DDL — same outcome
    on the old code (12-pair check).
  - Test cases: every FAIL was the column/type check (columns_match): Databricks numbers
    `information_schema.columns.ordinal_position` from 0, the agent counted from 1 —
    fixed in post153 (`ddl_test_ordinal_base: 0`); on D1 synthetic pair 4 then 30 PASS,
    6 NO DATA (empty tables), 0 FAIL. Tag checks pass. NO DATA = empty tables, expected.
  - Rerun on post153 output (same 12 pairs, same warehouse): pairs 01, 02, 04, 11, 12 —
    DDL OK twice, test cases 0 FAIL (11 / 33 / 11 / 44 / 33 PASS; NO DATA = empty
    tables); pair_03 unchanged. 12-pair check post152 vs post153: 12/12 same outcome,
    187 files both sides, 17 differ — all `_DDL_TestCases.txt`, only by the `+ 1`.
  - Not tested yet: loading a real file through the framework (the load cases are
    written steps); pair_03's DDL.
  - **Audit-log test case (item 4 of the post154 list): blocked on a name.** The
    framework's audit DB (SQL Server, Bastion) is said to be cloned in Unity Catalog under
    d1_dlk / d1_std, schema varying per pair. Searched 2026-10-29 (metadata only): no
    catalog like it, no table with the audit sheet's columns (PIPELINE_EXEC_ID,
    EXEC_STATUS, SRC_REC_COUNT, BATCH_CYCLE_NUMBER together); nearest
    `d1_dlk.monitoring_temp.data_factory_pipeline_exec_log*_dev` (5 of 14 columns, a temp
    dev table). information_schema shows only what the login may read - ask Soham for
    ONE known example (a pair's audit table full name); the pattern goes in the
    environment state file, never the repo.
- **Open (UI, optional):** the feed page's Overview kept its panels (restyled), not
  the issue-card layout of Results. The new-pair DBU figure stays an estimate until a
  live first run on an unmapped pair is recorded. Tours: `/tmp/t/ux/tour143.js`,
  `/tmp/t/ux/bar.js` (local App, `/tmp/t/ui/serve.sh`).
- Before post143, post142 was deployed (notebook stage types). Every version this
  session: both suites green, its tests fail with only the fix reverted; output-changing
  ones had the 12-pair check with every diff classified.
  Session log + what each version did: CLAUDE_HISTORY §[H15]; detail: CHANGELOG_ACFC.md.
- **Decided by Soham this session** (all in CLAUDE.md): stage column types as the STTM
  states; ONE combined `<ABBREV>_DDL.txt`; table COMMENT = Table Description + load
  strategy; the LOB question asked once, never blocking; ACFC's visual identity; then (post143) the guided look of the STTM agent's App, rounded.
- **pair_09 (one STTM sheet, 36 database tables) - parked with the RDMS sheet (Soham,
  2026-10-29, option B).** post155 holds a table source's IIG; post156 splits a one-sheet,
  N-table STTM per table when the FRD NAMES the tables. pair_09's FRD names none (tables
  from the STTM, the 36 file patterns from the VDD, the format from its answers), so it
  still FAILs. To finish: split when the FRD names no table (STTM authoritative), and in
  the gap fill give each table source its own object (exact identity with its source
  table / the STTM source table), never the VDD's whole list - do it with the RDMS sheet.
  Clue (2026-10-29): letting extract-sttm split it (its contract carries the 36 tables by
  then) reaches generate, which stops at a TemplateGapError (contract segment 1 field 1,
  "a value only the answers file can supply") - counted CRASHED; reverted, see post156.
- **Open, needs others:**
  - pair_03 is GATE_FAIL (`ddl_identifiers` 8 + `ddl_parses`): four column names in its
    STTM carry a stray space after an underscore (`WORD_WORD_ 9_WORD`; third sheet,
    rows 157-160, stage column Z and standard column AG = DDL columns 152-155 of both
    tables). The agent never renames; the BSA must remove the spaces. Proven on D1
    (2026-10-29): with only those spaces removed the DDL runs twice and its test cases
    pass (9 PASS, 0 FAIL).
  - pair_11's billing sheet is GATE_FAIL: its standard column 8 is stated with a space
    (`word _word`) — the STTM must be corrected (BSA); the agent never renames.
  - DDL test cases: Jinesh / Suganya on the framework's reject behaviour and header
    validation; then whether the load cases become runnable tests (option 2).
  - EXPLAIN check of the test-case SQL on D1: the DEFAULT PAT has no Can Use on warehouse
    `172877b5178f7bb7`. Needs a grant or another warehouse id from Soham.
  - The Rama session (child pipelines, then the ID assignment) — no date yet.
  - #4 multi-file FRD split / the multi-table decision; the recycle-days citation.
- **Open, codeable:** a fixed-width segment with its OWN stage table states no types in
  its IIG row (notebook lands it STRING + `notebook_segment_types_unstated`; none of the
  12 pairs has one); the medium/low audit list below (#31 first); the sheet's NYS rows
  (connection IDs, RDMS sheet, new vs existing process).
- **Known flakes** (pass alone, under `-n 4` + a parallel harness they can fail once):
  `test_m93_chooser.py` (`slow_and_failing_downloads…`;
  `index_writes_never_run_inside_a_selection_step`), `test_frd_default.py::
  test_a_paired_sttm_preselects_its_frd_labelled_paired`. Rerun alone before believing.

## Recipes this session relied on (`/tmp` is lost on a container reset)

- **12-pair check:** `/tmp/t/pair_check.sh <old-sha>` (variants `pair_check139b.sh` = one
  pair, `pair_check142.sh` = notebook mode) — copies the state (`environments overlays
  leakgate answers` from `dbfs:/Volumes/d1_dlk/codegen/state/`) and the pairs
  (`/Workspace/Users/<me>/frd_sttm_pairs`) into `/tmp/t/rp`, adds a worktree of
  `<old-sha>`, runs the harness `--pairs 1` once per tree (cache warm-up), then all 12 per
  tree, compares (`cmp2.py`, `cmp_kinds.py`), then the CLASSIFIERS — `tc_check.py`
  (test-case SELECTs), `ddl_comment_diff.py` (DDLs differ only in COMMENTs),
  `classify_rest.py` (every other file: banner sha only vs real), `classify_nb.py`
  (which notebook cells differ) — and only then removes the worktree and deletes the
  copies. Rebuild from this description if lost; never pass a placeholder sha.
- **Local App on scratch data:** `/tmp/t/ui/serve.sh` (port 8599, mock, storage roles and
  state in `/tmp/t/ui`, synthetic pair 4 as the input folder; `DATABRICKS_APP_PORT`
  overridden). A copy pointed at a worktree: `cd` + `PYTHONPATH=<worktree>/src:<worktree>`.
  Drive it by API (`/tmp/t/p12/drive.py` answers nothing each round and prints keys /
  kinds only) or Playwright (`/tmp/t/ui/tour.js` every screen, `dialogs.js`,
  `flags.js`, `cancel.js`). A client pair copied for it lives in `/tmp/t/<x>` and is
  deleted after.
- **Smoke test:** `/tmp/t/smoke/smoke.js <url> <png>` (Playwright from
  `ui/frontend/node_modules`; `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw`; LD_LIBRARY_PATH = all
  three lib dirs under /tmp/pwlibs (lib/x86_64-linux-gnu, usr/lib/x86_64-linux-gnu, its
  nss/) or Chromium exits 127; `CODEGEN_BEARER` = the OAuth token for the deployed App,
  never written).
- **Deploy / start:** `DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg databricks apps deploy
  codegen-agent -p codegen-oaut --json '{"mode":"SNAPSHOT","git_source":{"branch":
  "feature/multi-table"}}'`; a stopped App: `databricks apps start codegen-agent -p
  codegen-oaut` first (Soham's go — it bills compute).
- **The shared spreadsheet (current, since 2026-10-29):** SharePoint
  `amerihealth-agents-update-merged.xlsx`, sheet `codegen_agent`. Graph is refused
  (Conditional Access), so write an Office Script for Soham to run (rules in CLAUDE.md;
  last ones `/tmp/t/graph/update_ui_row_30oct.ts`, `update_ddl_rows.ts`). As of 30 Oct
  bold = the "App look and feel" row only; the D header still reads "from 29 Oct".
- **The old spreadsheet** (`/Workspace/Users/<me>/amerihealth-agents-update.xlsx`,
  sheets `codegen_agent` / `sttm_agent`, Soham's voice — "I", never "Soham"; status
  vocabulary Yes / NYS / WIP; plain wording on purpose): download it, edit IN PLACE with
  a small openpyxl script (`/tmp/xl_work/update_*.py`), check it is unchanged since the
  last upload, upload with `databricks workspace import … --overwrite`, download again
  and compare. `/tmp/t/xl/make_update.py` (rebuilds from scratch) is OBSOLETE — it would
  wipe later edits.

## Layer-2 review: OFF (2026-10-27, post123)

`config/overlays/acfc_env.yaml` → `reasoning: {layer2_app: skip, layer2_cli: skip}`.
To turn it back on: delete that block, bump, push, redeploy. Cost when it was on
(pair_11 live, measured): 4 calls, 5,757 in / 9,860 out tokens = 3.15 DBU. Without it,
a pair_11 run uses 0 model tokens (layout by synonyms; DDL / IIG / log are code); App
hosting is the cost (Medium, 0.5 DBU/h while running). A new pair whose layout the
rules cannot read pays one layout call per document once (STTM + FRD measured offline:
pair 8 ≈ 23k chars of requests, pair 10 ≈ 32k; est. 1.5–4.5 DBU per pair, output side
not measured), then the cache makes it free.

## Codeflow audit (2026-10-26) — where it stands

Detail of every finding: `/tmp/trace/high.json`, `/tmp/trace/rest.json` +
`rest_verdicts.json` (verdict per finding); history §[H13] / §[H14].
- **High list:** 13 real. Fixed: #1 #3 #8 #9 #11 #12/#15 (post108–113) and the seven
  re-rated #2 #5 #6 #7 #10 #13 #14 (post125–132). **Needs Soham:** #4 (multi-file FRD
  split renames standard tables to the stage names, pairs files by name guess, silently)
  — tied to the multi-table decision.
- **Medium/low list (47): every one now has a verdict.** Fixed so far: #1 #3 #8 #17 #19
  #20 #21 #30 #37 #43/#44, #9 (post133, pending push).
  - **Next, codeable, on paths ACFC runs (in this order):** #31 an Upsert non-detail
    (segmented H/T) table with no key signal gets a blank key (acfc_env; NA in the PRX
    family) with no QUESTION; #34 `config_inserts.xlsx` builds its own INSERTs with the
    retired logic, differing from `metadata_inserts.sql`; #10 an FRD user answer for a
    field already placed is dropped silently; #7 width answers keyed by sheet index but
    read by the paired FRD feed index; #24 `codegen pair` / acfc_run lack the App's
    same-folder FRD rescue (NONE, exit 0); #16(b) spec.lobs from the FRD while files
    expand from the STTM header's LOBs.
  - CLI-only (the layout stage already asks): #14 #15 #16(a).
  - low: #4 #18 #28 #32 #36 #39 #45 #46 #47; and from the first triage #33 #35 #36 #42,
    dead code (#5 #11 #26), 23 of 25 notebook v2 tests skip (#27).
  - **Needs Soham:** #29 ACTIVE_START_DATE = run date vs byte-stable; #12 an "as is" FRD
    rule turns every column STRING unflagged; #13 the rule classifier stops at its first
    match; **the recycle-days citation** (found fixing #2): in all three readers a
    defaulted window reaches `RECYCL_RETN_DAYS` badged "the recycle window the STTM
    states" — fixing it needs RecycleSpec to record whether the window was stated.
- The 11 audit areas never searched (config, edges, App runner / API, frontend, the
  cross-cutting lenses) — if resumed: one area at a time, inline or with a hard budget.

## Soham's notes (2026-10-28) - all three DONE: Cancel (post141), pair_12 LOB loop
(post138), DDL description COMMENTs (post139 column, post140 table).

## Next up — Nikshit's review (2026-10-23)

**DDL — run-safe: DEPLOYED (post105, 2026-10-26).** Verified on the App: a live pair_11
run (PASS_WITH_OPEN_INPUTS, 5 feeds PASS_WITH_FLAGS) gave a combined DDL of 10 CREATE
(all `IF NOT EXISTS`, CLUSTER BY AUTO, 4 / 13 TBLPROPERTIES, table COMMENT) each followed
by its SET TAGS, 20 statements all terminated, no conflicts, no `''`. The PK note's
separator is " — " since post106 (Soham), so no `;` sits inside a COMMENT the agent writes. Soham, 2026-10-26: the
agent's DDL GETS RUN. post104 (column COMMENTs, PK notes, load strategy, standard
TBLPROPERTIES, `\'` escapes) is deployed; post105 adds five `acfc_prx` knobs (on in
config.yaml, off in the pair-1 overlay — golden byte-identical): `CREATE TABLE IF NOT
EXISTS`, `;` after every statement, `CLUSTER BY AUTO` on both layers, the 4 stage
TBLPROPERTIES, `ALTER TABLE … SET TAGS ('DOMAIN', 'SUBDOMAIN')` from the FRD (blank =
none + `ddl_tags_blank`). Tests: `tests/test_ddl_runsafe.py`.
- **Scored 2026-10-26** vs prod D1 (`/Volumes/d1_dlk/stg_ddls/ddls/d1_*`, scratch copy
  deleted): stage 11/12, standard 10/11 (post104: 6/12, 6/11). The one DIFF per layer
  is column-comment coverage (pair 11's audit rows state no description). Prod's
  current set is itself `IF NOT EXISTS` + terminated, CLUSTER BY AUTO on stage, no
  LOCATION. `tools/ddl_shape.py` had scored 5 of 6 D1 stage files as standard (layer
  from `STTM_STG_STD` in the title) — fixed: the `<env>_<layer>_` prefix wins.
- **The three DDL questions (2026-10-23) - all ANSWERED by Soham:** (1) stage column
  types stay AS THE STTM STATES (2026-10-29: "the information is derived from the
  STTM") - today's behaviour, no change; (2) table COMMENT = description + load
  strategy (2026-10-28, post140); (3) ONE combined `<ABBREV>_DDL.txt` per feed
  (2026-10-29) - today's behaviour, no change; do not split per layer.
- **Follows from (1): DONE post142** - the notebook lands stage columns as the STTM types
  them. Left: a fixed-width segment with its OWN stage table states no types in its
  IIG row, so it still lands as STRING (flag `notebook_segment_types_unstated`); none of
  the 12 pairs has one. Not run on real Spark (no Java here).
- Prod has no PK and no load strategy; `q1` there vs our `A2` (ask Soham). The Pharmacy
  EDH RFC DDLs are warehouse dims (identity key, NOT NULL, `ADD CONSTRAINT PRIMARY
  KEY`, CDF) — a different pattern, not the target.
- `edo_sfmc` is run-safe too since post112 (IF NOT EXISTS) and writes only stated column
  COMMENTs since post131; ACFC runs `acfc_prx`.
- Keep the stage DDL (Nikshit thinks the framework doesn't need it; do not deprecate).
- The segmented extractor reads the Primary Key cell but never stores `primary_key`, so
  that dialect gets no PK notes. Left as is.

**DDL test cases — BUILT (post128, deployed):** a generic best-practice set, chosen at runtime per feed,
filled with the feed's own values (target table, real location):
- positive / negative: file present; at the right location; column mapping correct;
  every column populated; column shift (negative: shuffle the columns);
- does the framework map by column name or by position?
- Soham may ask Jinesh / Suganya which file needs which cases.
- **Where they go (Venu, via Soham, 2026-10-27):** a SEPARATE framework artefact, never
  inside the DDL — named like the DDL with `_TestCases` appended: per feed
  `<ABBREV>_DDL_TestCases.txt` next to `<ABBREV>_DDL.txt`, and in the combined set
  `<STTM>_DDL_TestCases.txt` next to `<STTM>_DDL.txt` (`run_artefacts`, the App
  listing). The DDL stays run-safe SQL only. **BUILT post128:** Nikshit's six + record
  count, key unique, structure checks (`conventions.profiles.acfc_prx.ddl_test_cases`);
  read-only SQL, gate `ddl_tests_read_only`. **post134:** every SELECT returns one row
  (test_id, result PASS / FAIL / NO DATA, found, expected); record count takes a per-case
  parameter `:expected_rows_tcNN`; columns_match compares with information_schema in the
  catalog's type spelling (`ddl_test_type_names` / `_defaults`); names lower-cased. Still
  manual: the load cases (no SQL) and SHOW TBLPROPERTIES. Not verified on a warehouse
  (no Java here; an EXPLAIN on D1 would check them — ask Soham, it wakes the warehouse).
  Option 2 (a runnable load-test notebook) waits on Jinesh / Suganya. Open: the framework's real reject behaviour
  ("fails or rejects" today) and whether it validates the header row — ask Jinesh /
  Suganya; a per-table grouping if 55 cases per 3-table feed reads too long.

**UX**
- DONE 2026-10-27 (post124, `95360b0`, deployed): the blue button reads
  "Generate Documents"; port kit / demo scripts / UX skill updated.
- On that click, a disclaimer with the approximate DBU / token cost of the run, computed
  from the actual documents (tokenizer over them → input / output tokens, priced against
  Opus 5.5), replacing the static estimate.

**IIG metadata**
- Connection IDs depend on the source; the ADLS connection ID comes from its associated
  table.
- Add RDMS_DELTA_INGESTION_DETAILS: MFT landing → ADLS, another SQL database → RDMS. The
  FRD's Functional Requirement cell says which; the agent reads it, states file vs table
  ingestion and recommends.
- New vs existing process, chosen when the FRD / STTM is selected:
  - new → names per the naming standard;
  - existing → the user gives the grand master pipeline name; the agent reads that
    pipeline's entries in the audit control DB + the FRD and adds only the new file
    ingestion. A new READ seam (the never-writes doctrine still holds).
- Child pipelines: Nikshit doubts every feed has its own children (pair_11: 12 rows per
  the standards doc vs 10 in the prod IIG). Find which groups run in parallel and which
  in sequence. **Hold this until after the session with Rama — planned for Mon 2026-10-26, not yet
  held (Soham, 2026-10-27); no new date yet.**
- Next level: how GROUP_ID / PIPELINE_ID and the other IDs get assigned (blank today by
  the never-invent-IDs rule).

## Open

**With Soham:**
- He reported the pair_11 combined DDL as "4 stage + 5 standard tables from 3 feeds";
  the App's pair_11 runs give 5 + 5, one pair per feed. Still to learn which file or run
  he counted (a pre-post97 download? the golden, which has 4 feeds?).
- The multi-table / contract-mismatch decision (blocks pairs 05 / 06 / 08 / 09, and
  pair_09's per-table load strategies from its STTM Summary sheet).
- Standards: the keep / drop table in `docs/acfc/STANDARDS_DEPRECATION_REVIEW.md` (alerts,
  timeout, default DQ on upsert, DBR 15.4 + Photon); then rewrite
  `docs/EDO_STANDARDS_ALIGNMENT.md`, `print` → logging in the v2 notebook templates, the
  `engineering_standards.status` line (byte-pinned outputs: one bump + snapshots).
- 106 `scripts/scrub_check.py` hits over tracked files on this branch (2026-10-23):
  mostly `docs/acfc/review/*.xlsx` and `IIG test cells.xlsx`, plus emails / ADLS hosts
  in a few tests and `app.yaml`. Keep or clean.
- Git hooks: solved 2026-10-23 — `scripts/dev_bootstrap.sh` points the clone at
  `.git/codegen-hooks/` (untracked wrappers): the repo's `pre-push` guard, then the
  container's global hook (its `post-commit` syncs the Workspace).

**Codeable here:**
- CI: `.github/workflows/tests.yml` (both venvs' suites in parallel, vitest + tsc, the
  pre-push version guard on the pushed range) — in the unpushed `5010c50`; starts on its
  first push (needs the `workflow` scope, State above). Actions minutes bill the GitHub
  repo owner. Reproduced in a clean clone: the container's counts.
- DONE 2026-10-27 (`8a60ece`): `tools/iig_diff.py` sorts the `--agent` files itself;
  `feed#n` labels follow the sorted order. A score taken unsorted before this may move.
- STGDELTA SRC_ADLS_PATH uses the standard table's name — wrong only when stage ≠
  standard names; no such pair found yet, so wait for one.
- RECYCL_ADLS_PATH on pair_11 (4 cells): the golden states a recycle no document does.
  Ask where prod got it.

**Needs others:**
- **The BSA:** pair_10's delimiters (4 feeds) and feeds 1–3 load strategy / LOBs;
  pair_08 `columns[87].target_type` is answered INT, probably STRING (INT in standard =
  STRING in stage, 39 of 39) — reported, not changed.
- **Nikshit / Venu:** child pipeline names — the EDO child pattern
  `PL_CHLD_<Product>_<Sub-Product>_<Source>_TO_<Target>_<Load Strategy>` has no feed slot,
  so every feed's children share a name (the `_LOG.md` lists them); the pair_11 golden
  uses an older pattern (`PL_File_PYX_CM_MIDS_<feed>_ADLS_To_Delta_Incr`). Tell Nikshit the
  document cannot give unique child names; do not deviate without his word. Also: which
  path convention is standard.
- **Nikshit:** re-confirm the D1 `storage_account` `z-use-d1-dlk-std-02` (given
  2026-10-21; hyphens are invalid in an Azure account name and it looks like a
  container; the earlier value is in `d1.yaml.bak_20261021_pre_storage_account`, volume
  only). If it changes: both state copies + the `storage_account` provenance text in
  acfc_env.yaml.
- **The ACFC framework team** — cells the pair-1 golden fills that no input determines:
  the semantics of `HEADER_FLAG` (`Y` in the golden for a fixed-width file whose first
  record is a header SEGMENT, while the FAQ's `has_header` means a column-header row);
  the stage leg's `TGT_LOAD_OPTION` / `TGT_REFRESH_TYPE` = `Overwrite` in the golden
  while the FRD's Load Strategy STG says `Append`; `LOB` blank in the golden while the
  FRD states `ALL`; the derivation of the STGDELTA row's `OBJECT_NAME`
  (`Accumulator_accumclient`) and `SOURCE` (the feed name, not the vendor). Until
  answered these cells follow the inputs and differ from the golden.
- **HEDIS owners (via Soham):** what prod deploys for one Stage → Consumption load + one
  deployed XREF and one claims example (`docs/acfc/HEDIS_CONSUMPTION_STTM_SHAPE.md` §6);
  nothing to build before that.
- **EMAIL_TO:** no value anywhere.
- **Raj:** the `USE CATALOG` grant (then app.yaml back to the volume; until then edit
  BOTH state copies: the volume and `/Workspace/Users/<me>/codegen/state/codegen-state`).
- **D1 / Genie:** the golden SRC_COLUMNS cells (rule 4 — re-apply with `git cherry-pick
  49d3e73 3b0082d` from local `wip/src-columns-rule4` if they confirm it), the
  PIPELINE_DESCRIPTION dump, the workspace-folder token.
- **Aruna:** `docs/acfc/OPEN_QUESTIONS.md` §4–6.
- **Deferred by Soham:** pair_10's FRD prose values (file format / load strategy / LOBs in
  paragraphs, not in feed order) — a layout-model task.

## Driving the App and the container

- **Deploy:** the App builds from GitHub, not a staged tree. Push, then
  `DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg databricks apps deploy codegen-agent -p
  codegen-oaut --json '{"mode":"SNAPSHOT","git_source":{"branch":"feature/multi-table"}}'`
  (prints the resolved commit). Soham also deploys this way.
- **Token:** `DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg databricks auth token -p
  codegen-oaut` gives an OAuth token the App's API accepts (a PAT does not). URL
  `https://codegen-agent-4812116803419068.8.azure.databricksapps.com`.
- **Live runs:** the App runs live (`CODEGEN_PROVIDER=live` in app.yaml), so a run sends
  client documents to the model — Soham approves each pair (08 / 10 / 03 / 11 approved
  2026-10-22).
- **Flow:** `POST /api/demo/workbook {name}` (202, poll status `selection_job`) →
  `/api/demo/run-live {confirm: true}` → while paused, `/api/demo/layout-answers
  {answers, proceed | cancel}` or `/api/demo/rerun-with-answers {answers: {gaps},
  confirm: true}`. One run at a time: cancel a paused one first. The combined set:
  `GET /api/combined/<name>`.
- **Container harness:** pairs in `/Workspace/Users/<me>/frd_sttm_pairs/pair_<n>`; for the
  App's own state copy `environments/`, `overlays/`, `leakgate/` and `answers/pair_<n>`
  from `dbfs:/Volumes/d1_dlk/codegen/state/` into a /tmp state dir (`databricks fs cp
  -r`), then `PYTHONUTF8=1 .venv-d1/bin/python scripts/container_harness.py --pairs-dir
  <dir> --state-dir <dir> --out <dir> --work <dir> --pairs 3,8,9,10 --dry-run
  --output-mode framework`. `--pairs` is comma-separated. It is mock: pairs 08 / 10 stop
  at the layout step (no cached layout profile; the live App resolves it). Never run the
  CLI from the repo root with outputs in `out/`.
- **SharePoint:** memory `sharepoint-via-uc-connection` (read_files + `d1_dlk_sharepoint`
  on the Serverless Starter Warehouse). The 9 HEDIS workbooks are in
  `/Volumes/d1_dlk/codegen/state/hedis/stage_to_consumption/`.

## After a container reset

Venvs, `/tmp`, the OAuth profile and possibly `~/.gitconfig` are gone. Run
`scripts/dev_bootstrap.sh` (idempotent; `--no-d1` / `--no-browser` / `--no-hooks`): it
does the venv, Chromium, hooks and push-login steps below and prints the rest. The
manual recipe stays here for when it fails.

- **Venvs** via uv (pip's isolated pyspark build failed 2026-10-23):
  - `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e
    ".[dev,ui,live,databricks]"`;
  - `.venv-d1` the same with `-e ".[dev,databricks]" -c constraints/acfc_d1.txt`.
- **OAuth:** the login's `localhost:8020` callback listens IN the container. Start
  `BROWSER=echo DATABRICKS_CONFIG_FILE=/tmp/cgs/oauth.cfg databricks auth login --host
  <the DEFAULT profile's host, `databricks auth profiles`> --profile codegen-oaut` in the
  background; Soham opens the printed URL and pastes back the `localhost:8020/?code=…`
  URL; `curl` that URL inside the container. A code only works for the login that
  issued it.
- **Git push:** `gh auth setup-git` (git then uses the `gh` login).
- **Browser checks:** Chromium in `/tmp/pw` + libs in `/tmp/pwlibs`, run with
  `LD_LIBRARY_PATH=/tmp/pwlibs/usr/lib/x86_64-linux-gnu:/tmp/pwlibs/lib/x86_64-linux-gnu
  PLAYWRIGHT_BROWSERS_PATH=/tmp/pw node <script>`. Stub `/api/feeds` or
  `/api/demo/status` with `page.route`. Rebuild:
  - `cd ui/frontend && npm ci`, then (no `npx` in the container)
    `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw node node_modules/playwright/cli.js install
    chromium-headless-shell`; a script `require`s that `node_modules/playwright` by path.
  - Libs: `apt-get download` + `dpkg -x … /tmp/pwlibs` of libglib2.0-0 libnspr4 libnss3
    libatk1.0-0 libatk-bridge2.0-0 libdbus-1-3 libxcomposite1 libxdamage1 libxfixes3
    libxrandr2 libgbm1 libxkbcommon0 libasound2 libatspi2.0-0 libwayland-server0 libdrm2
    libxi6 libxrender1 libxext6 libx11-6 libxcb1 libxau6 libxdmcp6 libbsd0 libmd0
    libxcb-randr0; `ldd …/chrome-headless-shell | grep "not found"` must print nothing.
  - Against the deployed App: `newContext({extraHTTPHeaders: {Authorization: "Bearer
    <OAuth token>"}})`.
- **The MLflow Stop hook** in `/app/python/source_code/.claude/settings.json` was removed
  2026-10-23 (tracing was disabled and mlflow not installed; its `uv run` wrote
  `uv.lock` into the repo and rebuilt `.venv`). A reprovision may restore it — delete
  `hooks.Stop` again.
