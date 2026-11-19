# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
`AGENTS.md`, the rules file - `CLAUDE.md` until 2026-11-03). What each version did: `CHANGELOG_ACFC.md`.

## Start here (2026-11-19 night - staging = post212 (049c6e8); dev STOPPED on post194; feature = post212, pushed)

**Who uses the agent: a data engineer, not a BSA** (the CodeGen Data Engineer Agent;
AGENTS.md "Purpose") - write App text, review notes and manuals for that reader.

**First check:** `git fetch && git status -sb` = up to date with
`origin/feature/multi-table` (head = docs on top of post205).
- **staging `codegen-agent-staging` = post205** (`main` = e2b967b, identical-tree merge;
  health + smoke green).
- **dev `codegen-agent`:** STOPPED, last deployment post194 - starting it bills compute
  (Soham's call); then `/ship-dev` deploys post205.
- **This session: post200-post205**, every one with both suites green, CI green, the
  framework 12-pair outcomes unchanged (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS,
  2 GATE_FAIL, 2 FAIL), no artefact cell moved outside the fix's own reach, and its
  BUG_FIX_LOG entry (reach, revert); all on staging. What each did:
  CHANGELOG_ACFC; why: CLAUDE_HISTORY §[H28].
- **The tester (staging)** re-ran on post199 - working. Her Comments column (the standard
  band's last column) is read since post201; for her date-format note to become a
  DateConversionRule she writes "Convert <source> to <target>" and types the standard
  column Date (Soham chose this, no code; reply sent via Soham).
- **pair_13** (the Accumulators pair) is in `/Workspace/Users/<me>/frd_sttm_pairs/pair_13`,
  not in the 12-pair default (`--pairs 13`); the tester's pairs are NOT stored (her uploads:
  staging `codegen/inputs/codegen-agent-staging/uploads`) - see Open 1.
- **The codebase deck:** `/Workspace/Users/<me>/CodeGen_Agent_Codebase_Walkthrough.pptx`
  (slide 42 says post192 - update if reused).
- After a container reset: `~/bootstrap`, then the OAuth login (recipe below).

**Open, in order:**
-4. **Tracker triage 2026-11-19 - #5, #7, #18, #19, #20 FIXED in post212 (staging); the
   update Office Script given in the chat (/tmp only, client text); (export of sheet CodeGen, 22 incidents; reproduced on
   pair_13, mock):** NEW / re-opened: #5 SRC_FILE_NAME = family `prefix_star` turns the
   FRD's `*_X_*_Y*` into `X_Y*` (no longer matches the files; the App's
   src_file_name_style "pattern" is the workaround); #7 + #20 archive paths are the
   template shapes (capital "Archive", "/Archive{landing}" on FIXED_WIDTH) - this FRD
   states three "Archive Path:" lines (main / daily / monthly), unread (label unknown,
   three paths); #18 no reject table DDL (stage or standard); #19 table COMMENT = the
   load strategy (no FRD description field); #3 comment: stage + stage-reject
   TBLPROPERTIES not ACFC's (template needed). Ready to mark resolved on staging: #11,
   #13 (post193), #21 (post195-199 + 206-210), #22 (post201). Decisions: #9/#10, #12
   rest, #14, #16 (item 3 below).
-3. **Done 2026-11-19 (post206-211, all on staging):** typed / blank FRD answers (206),
   Landing Location + "Domain -" (207), feed name never from a non-descriptive section +
   Archive Location compared (208), the STTM File Details tab (209), FRD questions offer
   only plausible cells + no feed-name question (210, P1 of the question-UX plan), the
   data engineer (not the BSA) everywhere (211). Next: "Derived"-type cells asked as a
   question (post158's guard keeps the stop); P2 / P3 of the question UX; tester pairs
   A / B / C stored as pair_14-16; MandatoryColumnCheckRule (waits on the tester's 4
   answers). The user manual: Workspace `code-gen-agent-documentation.docx` (builder
   was /tmp/t/doc/build_cg_manual.py - gone after a reset; the doc is the source now).
-2. **A second tester's run (staging post208, 2026-11-19; pair C = the same program's third
   vendor, copied to /tmp/t/ik/pairs/pair_93; her run is PAUSED on staging - do not touch):**
   she found the question block impenetrable, and the File format question listed ~16-20
   choices that are FRD labels (Name, IS Owner, "Container Name", "History" lines ...) -
   the SAME 16 for all 6 questions (feed name, format, LOBs, domain, both strategies);
   none states any of them. Root causes: (a) an FRD role question offers EVERY labelled
   cell / line of the document, never filtered by what the field's value looks like;
   (b) the person is asked WHERE a value is (a location question - the layout's job),
   not WHAT it is; (c) keys / table-row coordinates up front, plain words folded.
   REGRESSION from post208: with no Descriptive section `feeds[0].feed_name` is now asked
   (16 cells, no text box) though it blocks nothing (the stage band names the feed) - on
   pairs A and C. On post209 pair C still asks 5 (feed name, LOBs, domain, 2 strategies).
   Game plan given to Soham (chat 2026-11-19): P1 stop the feed-name question + a value
   validator on FRD candidates (none valid -> a plain value question); P2 FRD questions
   become VALUE questions (values, deduped, cited; coordinates folded); P3 the dialog
   rewritten in plain words per feed (what each answer sets in the IIG); P4 the question
   count per pair as the measure. Waiting on his pick.
-1. **The tester's 2026-11-19 report (staging post205; 5 items, IN PROGRESS this session).**
   Her pairs are called pair A / pair B here (no client names). Reproduce on HER uploads
   (mock, /tmp) before any fix; then a BUG_FIX_LOG entry for each fix.
   - (1) Pair A (FRD + STTM): every feed held back at the first step. Layout asks
     `feeds[0].file_format`, `feeds[0].lobs` and domain / subdomain; the FRD states none
     of them; the only choices are wrong FRD table cells (Functional Requirement, Name,
     Impact Details, IS Owner) + "None of these". **"Proceed with unresolved" does NOT
     release the feed** - bug (or a dead-end message) to find.
   - (2) Pair A's STTM has a separate "File Details" sheet: label column A, value
     column B - File Type `.txt`, File Delimitor (sic) `Pipe`, File Delivery Method,
     Proposed Frequency, Proposed Time, History, File Naming convention, SFTP. Her
     question: does the agent read that sheet or only the FRD? (A
     READER_GENERALIZATION question first - a generic label/value sheet reader.)
   - (3) Pair B: `SRC_ADLS_PATH` / `SRC_ADLS_ARCHVL_PATH` blank. Its FRD states them as
     "Landing Location:" (under per-environment "Prod:" / "QA:" blocks, each with a
     "Container Name:" line) and "Archive Location: (Raw Layer - ADLS Gen 2 container)"
     with the path on the NEXT line. = old item 4(d) (`requirement_landing_labels` =
     only "Raw ADLS Location" / "ADLS Location"; `landing_line_labels`) - it now matters.
   - (4) After she typed the standard column's data type as Date (our advice for the
     DateConversionRule), `TGT_DATA_TYPE` AND `SRC_DATA_TYPE` in sheet
     STGDELTA_STDDELTA_INGESTION_DET changed too - check which STTM column feeds each
     (a source type should come from the source band, not the standard one).
   - (5) Her suggestion: build a `MandatoryColumnCheckRule` DATA_QUALITY_RULES row from
     the STTM's source "Required/Optional" column. Transcribed from an input, so the rules
     allow it - a feature, Soham's call.
   - **Diagnosis 2026-11-19 (mock, her uploads copied to /tmp/t/ik as pair_91 = A,
     pair_92 = B; staging state + layout cache in /tmp/t/ik/state; harness: both
     NEEDS_ANSWERS at layout):**
     (1) ROOT CAUSE = UI dead end: a layout ROLE question (place an FRD field) offers only
     FRD cells + "None of these" - no text box, no "(leave blank)" (`LayoutQuestions.tsx`
     QuestionItem: text input / leave_blank only for `kind: text`). "None of these" leaves
     the role unplaced, the run holds the feed, and NeedsAnswersPanel re-asks the SAME
     role question -> a loop she cannot leave. Also the DQ rules item (sheet STTM,
     `value_unstated`) - not yet traced.
     What the documents do state: pair A's FRD HAS "Domain -<x>" / "Subdomain-<x>" lines
     (hyphen, no colon - unread); file format + delimiter are on the STTM "File Details"
     sheet (unread - the agent never reads that sheet); LOBs: no document states them
     (only as a key column name) -> must be typed or left blank.
     (2) NOT read today. (3) both pairs: "Landing Location:" / "Archive Location: (...)"
     with the path on the NEXT line, under Prod: / QA: blocks (same path in both here).
     (4) BY DESIGN: STGDELTA `SRC_DATA_TYPE` = stage:standard pairs, `TGT_DATA_TYPE` =
     the standard types (`metadata_template._stg_std_row`), so a standard type change
     moves both; the source band's type is not in that row.
     (5) no `MandatoryColumnCheckRule` in our class list (`dq_rule_classes`); the nearest
     homes are ADLS `MANDATORY_FIELD_LIST` and `NullCheckRule` - ask her which the
     framework expects.
   - **DONE 2026-11-19:** post206 = F1 (1A), staging 741a62f; post207 = F4-landing +
     F3 (pushed, NOT on staging yet - Soham's word). Her pair A then GATE_FAILs on
     `ddl_identifiers` (4 STTM column names; the STTM's to fix) - tell her.
   - **Soham's pick (2026-11-19): my picks, in order - F1 (1A) = post206, then F4-landing (config label) + F3 (Domain "-" lines,
     narrow), then F2 (generic label | value STTM sheet reader; the STTM File Details sheet
     is ALREADY searched for file names - extend that), archive = option C (template kept,
     a stated archive path that disagrees is flagged), item 5 waits on the tester's
     answer. NEW: pair A's feed is NAMED "Data Quality rules" (a wrong FRD cell read as
     the feed name) - trace it. Pre-existing UI: at 390 px the Settings card's
     connection-ID table scrolls sideways.
   - **Item 5, the tester's answer (2026-11-19):** the class is `MandatoryColumnCheckRule`
     (framework notebook `/Workspace/subcon_version/DataQuality_StandardEnhancement`, read
     in place): `SOURCE_COLUMN` = comma list, `INPUT_PARAM` = an ERROR CODE, rejects
     null / blank / "NULL". She asks for it as a STANDARD rule on every ingestion (the
     framework checks mandatory fields on all). Today: the STTM Required column IS read
     (pair A: 37 / 60 mandatory -> `not_null_columns`) -> ADLS `MANDATORY_FIELD_LIST`;
     NullCheckRule only when a DQ sheet / the FRD states it, else an
     `iig_dq_not_generated:` suggestion (post171). Open before building: the error-code
     value, RULE_TYPE + TARGET_COLUMN, overlap with MANDATORY_FIELD_LIST / NullCheckRule,
     the FRD "No Rejection" case. Soham's call (it is a client standard = a cited
     constant, a change to post171's stated-only rule for this one class).
   - **Proposed fixes:** F1 role questions get "type a value" +
     "leave blank" (blankable fields), answered under `gaps:`; F2 a generic label/value
     sheet reader for the STTM (File Details) using the FRD label synonyms, filling only
     where the FRD is blank (`frd_unstated:` flag); F3 "Domain -x" lines; F4 next-line
     values for Landing / Archive Location (env block choice when Prod / QA differ).
   - **Code facts behind the options (checked 2026-11-19):** the backend ALREADY applies a
     typed `gaps:` answer for an FRD role key of file_format / delimiter / frequency /
     domain / sub_domain / lobs / landing_location (`layout.resolve._ANSWERABLE_FRD_FIELDS`)
     -> F1 is UI-only (not run end to end yet). `frd_docx._labelled_path` already reads a
     path on the NEXT line -> "Landing Location" can be a config line
     (`landing_line_labels`, today only "Raw Path"); "Archive Location: (Raw Layer ...)"
     is not (text after the colon, no path). No archive reader exists:
     `SRC_ADLS_ARCHVL_PATH` is a TEMPLATE of the landing (`path_patterns`:
     ADLS `{landing}Archive/`, STGDELTA `/Archive{landing}`) - a stated archive path can
     disagree with it. Pros / cons of each option were given in chat; the pick is Soham's.
0. **Venu's "run the DDL tests from the App" (Soham + Venu):** options sent - (1) an
   "Open in Databricks" button, no rule change; (2) the App runs them - needs the
   EXPLAIN-only rule widened to read-only test statements, an identity (user
   on-behalf-of vs the App's SP), a warehouse (DBU spend), D1 only or more. Waiting on
   Venu's pick. Same rule blocks item 11.
1. **The health review (2026-11-18, Soham's calls):** (a) store each tester pair that
   triggered a fix as `pair_14+` in the Workspace pairs folder and add it to the check
   (the 12-pair check never exercised post196-199's shapes); (b) the READER_GENERALIZATION
   decision (item 2); (c) the private cross-module imports (66; `layout/resolve` reads
   `frd_docx` internals) -> a public module; (d) `emit/rfc.py` + the `dml:` config
   section - removal needs his word (AGENTS / pipeline.md keep them); (e) merging
   `discover.header_key` and `frd_docx.label_key` CHANGES what FRD labels match
   (punctuation) - a pair-checked version, not a tidy-up.
2. **DECIDE (Soham): `docs/acfc/READER_GENERALIZATION.md`** - phases 0-3 (0-1 change no
   output). §5 cheap wins DONE: post198 (STTM headers), post199 (load strategy), post200
   (FRD labels), post204 (delimiters), post205 (one "states nothing" list,
   `extractor.blank_words`). NEXT value normalisers (mine, no decision needed): file
   format, decimal.
   Pairing is Phase 2 (6 matchers differ on purpose).
3. **Tracker decisions (Soham), incidents 9-17** (tracker export: Soham runs the Office
   Script `tools/tracker/export_incident_tracker.ts` (tracked since 2026-11-19) and pastes
   `_JSON_EXPORT` column A; an update script is written per change, DRY_RUN first):
   #12 rest (STGDELTA `TGT_DATA_TYPE` precision - the tester: drop; the pair-1 golden
   keeps it); #14 (a DataTypeCastRule - reverses post171); #16 (no grand master for a
   Workflow run - changes post166); #9 / #10 (fixed-width -> `SRC_FORMAT = CSV`,
   delimiter `|` - confirm for EVERY fixed-width feed, then a cited constant); #11 / #13
   set Resolved.
4. **Small, mine:** (c) a source header written only `Field` stays a question (a synonym
   only with more evidence); (d) "Landing Location:" lines unread
   (`requirement_landing_labels`) - no effect on any run today.
5. **The Standard Abbreviation List v28 - ASKED (Lokesh, via Soham, 2026-11-13)** + Data
   Domains SOR SOT.xlsx, the Data Modelling Guidelines, an IIG Framework sample (land in
   the Workspace `standards_docs` folder). Waiting on it: NM-001, NM-004, NM-006.
6. **DL-006 (Soham's call):** raw files by `abfss://` vs a Unity Catalog volume - ask ACFC.
7. **Incident 2 (Lokesh):** external tables - property set, `LOCATION` format, which field
   marks a table external.
8. **PY-006 on feeds with many DATA_QUALITY_RULES rows** (pair_12) - Soham's call.
9. **DECIDED, do not re-raise:** the standard TBLPROPERTIES stay as post185 has them; the
   Naming Standards win for grand master names; pair_12 is a Workflow (WF_). Still open:
   reuse an existing grand master? + the NSP / HVR / DLK-vs-HDS questions (H23 draft).
10. **TDD training** (Venu): two TDDs in `rfc_samples`; training material only.
11. **A second standard table per stage table** (the 820 pair); **rows 3 / 4 of the
    delegation workbook** (need the EXPLAIN-only rule changed); NO_OF_CYCLE_PER_DAY "1"
    on pairs 11 / 12 - Soham's calls.
12. **`codingapp` deploy** (bootstrap patch imported) - on Soham's word, last in a session.
13. The STTM cell locator step 3; BSA questions (pairs 05 / 11 DQ sheet, pair_12 recycle);
    the Apps stop / start schedule (CLAUDE_HISTORY, blocks retired 2026-11-10).
14. **AGENTS.md is 270 lines** (target ~200, /handoff): move procedures to skills /
    `.claude/rules/` in a quiet session.

## Recipes (tracked since 2026-11-10 - `tools/check/`, `/tmp` holds only copies)

- **12-pair check:** `tools/check/pair_check.sh run [<old-sha>]` (skill `/pair-check`):
  copies the pairs + the state volume's `environments overlays leakgate answers` into
  `$PAIR_CHECK_DIR` (default `/tmp/t/pairs`), a worktree of the old sha, warms + runs the
  harness per side, then `outcomes.py` + `classify.py` (sha-only vs REAL, masked line
  shapes, workbook cells by kind). A side whose code tree ran before is CACHED (the next
  version's old side is free). `cleanup` at the end of the session.
- **Deploy + prove:** `tools/check/ship.sh dev` / `staging --approved` (skills
  `/ship-dev`, `/ship-staging`): idle check, staging's identical-tree merge, deploy with
  one retry, restore the last good commit on failure, health = pyproject's version,
  smoke. Refuses a STOPPED App (starting bills compute - Soham's call).
- **The App's API:** `python -I tools/check/app_api.py <app> GET /api/demo/status`
  (OAuth profile `codegen-oaut` in `CODEGEN_OAUTH_CFG`, default `/tmp/cgs/oauth.cfg` -
  recreate it after a reset: "OAuth" under "After a container reset" below; the DEFAULT
  PAT is refused by the API).
- **Smoke / local App:** `tools/check/smoke.cjs <url> <png>` (`CODEGEN_BEARER`,
  `PLAYWRIGHT_BROWSERS_PATH=/tmp/pw`, LD_LIBRARY_PATH = the /tmp/pwlibs lib dirs);
  `tools/check/serve_local.sh [port]` (mock, scratch storage in `/tmp/t/ui`, synthetic
  pair 4; stop it by the PID in `server.pid`, never `pkill -f` a pattern in your own
  command line).
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

## Driving the App and the container

- **Deploy:** the App builds from GitHub (`feature/multi-table`), not a staged tree; a
  push alone does not redeploy (verified 2026-11-02). Push, then
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

HOME (`/app/python/source_code`) is rebuilt on every restart of the coding App: the clone,
venvs, `/tmp`, the gh login, `~/.claude` (settings, memory) and the OAuth profile are gone.
With the App bootstrap patch deployed (State 2026-11-04), the routine is:
1. `gh auth login` (the wrapper answers the prompts), then `~/bootstrap` - it re-clones
   this repo on `feature/multi-table` (`bootstrap_repos.txt` in the App source), runs
   `gh auth setup-git` and `scripts/dev_bootstrap.sh` (venvs, Chromium + libs, git hooks,
   the work branch from a clean main, push login). The Databricks skills and the skill
   trim are already done by the App's own setup.
2. The Databricks OAuth login (below) when the App's API or SQL is needed.
Without the patch: clone, then `scripts/dev_bootstrap.sh` (idempotent; `--no-d1` /
`--no-browser` / `--no-hooks`), `databricks aitools install`, delete the MLflow Stop hook.
The manual recipe stays here for when it fails.

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
  `LD_LIBRARY_PATH=/tmp/pwlibs/usr/lib/x86_64-linux-gnu:/tmp/pwlibs/lib/x86_64-linux-gnu:/tmp/pwlibs/usr/lib/x86_64-linux-gnu/nss
  PLAYWRIGHT_BROWSERS_PATH=/tmp/pw node <script>` (without the `nss/` dir Chromium exits
  127). Smoke: a script that `require`s `ui/frontend/node_modules/playwright` by path,
  opens the page, waits for the `h1`, screenshots, prints the title + console errors. Stub `/api/feeds` or
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
  `hooks.Stop` again. Cause found 2026-11-04: the App's `setup_mlflow.py` re-adds it on
  every start even with tracing off - fixed by the App patch (State 2026-11-04).
- **SQL on the system tables:** Soham's user has no USE SCHEMA on `system.billing` /
  `system.serving`; spend comes from the EDO Spend Monitor (another workspace - not
  reachable from here, read screenshots). Warehouse `D1-HRR-RO-SQ-S-01` fails to start
  (WORKSPACE_CONFIGURATION_ERROR / PERMISSION_DENIED, an admin issue); the Serverless
  Starter Warehouse starts (ask first, it bills).
