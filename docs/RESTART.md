# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
`AGENTS.md`, the rules file - `CLAUDE.md` until 2026-11-03). What each version did: `CHANGELOG_ACFC.md`.

## Start here (2026-11-24 - staging = post221 (main a3ad97f); feature = post221 + docs; dev STOPPED on post194)

**Who uses the agent: a data engineer, not a BSA** (the CodeGen Data Engineer Agent;
AGENTS.md "Purpose") - write App text, review notes and manuals for that reader.

**First check:** after a reset: `~/bootstrap` (clones `feature/multi-table`), then the
OAuth login (recipe below; a login code expires in minutes - paste the `localhost:8020`
URL back at once). A restored checkout comes back on `main` (the staging copy of this
file): read RESTART AFTER the bootstrap. `git fetch` - `origin/feature/multi-table` =
post220 + docs (no wip branches).
- **staging `codegen-agent-staging` = post221** (`main` = a3ad97f, 2026-11-24; before: post220 13cd550, post218 05f9139; post217 = 3fb28aa first, one change per deploy; identical-tree merges,
  2026-11-23; health + smoke green; the proxy's `x-forwarded-email` reaches the App).
  **dev `codegen-agent`:** STOPPED on post194 (starting it bills compute - Soham's call).
- **The last session (2026-11-24): post220 (the audit columns' standard COMMENTs) built
  on Soham's yes and shipped to staging with post219; P4 measured (no code change)** -
  what it did: CHANGELOG_ACFC, `docs/acfc/P4_QUESTION_COUNT_2026-11-24.md`;
  why / decisions: CLAUDE_HISTORY §[H32] (the session before: §[H31]). Every shipped version: both suites green on the pushed tree, the
  pair check alone where output can move. SINCE 2026-11-23 it runs pairs 1-17 by default
  (1-12 + the tester pairs 13-17, Workspace `frd_sttm_pairs`): outcomes 7
  PASS_WITH_OPEN_INPUTS, 6 NEEDS_ANSWERS, 2 GATE_FAIL, 2 FAIL (1-12 as always 5 / 3 / 2 / 2;
  13 + 15 PASS_WITH_OPEN_INPUTS, 14 / 16 / 17 NEEDS_ANSWERS - no answers stored).
- **Testers' documents** (staging uploads, `/Workspace/Users/<me>/codegen/inputs/
  codegen-agent-staging/uploads`, 14 STTMs on 2026-11-23): pair A / B = the first
  tester's (two vendors of one program), pair C = the second tester's; the first tester's
  template (FieldDescription in the source band) = 6 of the 14. No /tmp copies left
  (deleted 2026-11-23); re-export when needed (mock only, /tmp, delete after). pair_13
  (the Accumulators pair) = Workspace `frd_sttm_pairs/pair_13` (`--pairs 13`).
- **Tracker:** `tools/tracker/` (export script tracked; per-change update scripts quote
  client text - chat + /tmp only). Office Scripts compile stricter than tsc
  (`tools/tracker/README.md`, `check_office_script.py`).
- **Docs out:** the user manual = Workspace `code-gen-agent-documentation.docx`; the WSR
  deck `AI_in_Engineering_ WSR_Nov 20.pptx`; model comparisons = `docs/MODEL_COMPARISON.md`.
  The note to Nikshit / Raj on feedback triage and the 11/23 report: sent 2026-11-23.
  Text Soham pastes goes in a code block, short, one line per item, no blank lines.
- **post222 + post223 ON STAGING 2026-11-25 (main 00ac166, health + smoke green):** post222 = one
  data-type rule (`sql_type` reads "BIG INT"; `_is_data_type` asks it - pair_09's 8 cells;
  no artefact moved); post223 = a stated delimiter that the format / a file extension
  contradicts gets `delimiter_implied_differs:` (pair_02's `.psv` + "Comma"; one report
  line, nothing else). Both suites green on each (2807 / 2440; 2814 / 2447), pair check
  1-17 alone each. The decimal normaliser was NOT built: measured, no pair states a
  non-Spark decimal in the stage / standard layers (source types go only to the VDD check).
  The fixed-width readers (4 copies, two token lists) agree on every pair; their
  no-delimiter difference is tracker #9 / #10's question - left for that decision.
- **2026-11-25 (no code change; CLAUDE_HISTORY §[H33]):** the Nov 27 WSR deck's CodeGen
  boxes (slides 4 / 6) updated; the tracker update script given (8 rows: #11 #13 #18 #19
  #20 Resolved, #3 re-opened - stage / stage-reject TBLPROPERTIES, #5 #7 update lines;
  Soham ran it 2026-11-25); a time-savings deck from the delegation sheet = Workspace
  `CodeGen_Agent_Time_Savings.pptx` (69 / 49 / 40 h per feed; regenerate when the testers'
  measured hours arrive - the builder was /tmp only). The efficiency sheet =
  Workspace `STTM_to_Artefacts_Agent_Delegation (1).xlsx` (still says "BSA review copy" /
  `metadata_inserts.sql`). Bug scan of post212-221: both suites green, no live bug; kept
  in mind: the reject table's suffix is set twice (`standard_reject_table.suffix` vs
  iig_v2 `reject_table_suffix`; iig_v1 = `_errors`) - fold into the #18 re-decision;
  the stated archive path's environment rewrite raises no mismatch flag (0 of 17 pairs).

**Open, in order:**
-8. **post220 (a standard COMMENT for each audit column; the tester's request, Soham's
   yes 2026-11-24) - ON STAGING (13cd550, health + smoke green; post219 with it):** acfc_prx `audit_column_comments` (LOB
   'Line of Business'; SRC_FILE_NAME / REC_* = the SFMC production DDL's wording).
   Both suites green (2782 / 2415); pair check 1-17 vs post219: same outcomes, DDL
   COMMENTs on 9 pairs (BUG_FIX_LOG post220). If the tester wants other wording: edit
   the config texts only. Her pair's remaining blank column (post217: 5 per table, 4
   audit): her own run was not stored; pair_16 (her template) has none left. Her
   re-run on staging is the check - Soham sent her the message 2026-11-24; waiting on
   her reply (wording / any column still blank).
-7. **post217 (FieldDescription -> DDL column COMMENT) ON STAGING (3fb28aa) and post218 (P3:
   one card per feed, plain words, "Fills in the IIG") ON STAGING (05f9139), 2026-11-23;
   health + smoke green each.** The first tester was told to re-run her file (message
   drafted for Soham 2026-11-23). Her audit-column COMMENT question = a REQUEST: only on a
   yes. The P3 screenshots: Workspace `codegen/p3_screenshots/` (synthetic; one card per
   image - a full-page shot is unreadable in the Workspace preview).
   **P4 DONE 2026-11-24** (`docs/acfc/P4_QUESTION_COUNT_2026-11-24.md`, pairs 1-17, mock,
   no answers): dialog 40 -> 39 questions, 649 -> 64 choices (pairs 8 / 9 / 10 move);
   run's blocking keys 23 -> 57, all of it pair_17's 34 post213 standard-type questions
   on cells with ONE identical text -> **post221 groups them (Soham's word): pair_17
   34 -> 1, open 38 -> 5; both suites green (2787 / 2420); pair check: only pair_17
   moved. ON STAGING (a3ad97f, health + smoke green).** The numbers go in the next report.
   The testers' note on post221 (+ post220's audit comments) drafted for Soham
   2026-11-24 - their re-runs are the check; feedback sorted before any code.
-6. **post219 (the review's dead `fieldname` synonym) - ON STAGING with post220 (13cd550):** both suites
   green (2777 / 2410); pair check 1-17 vs post218: same outcomes, no artefact change (17
   report .md lines = the "Produced by" code path). Shipped 2026-11-24 with post220
   (no behaviour change). pairs 14-17 = the 4 staging uploads (of 14) the agent's own
   content pairing pairs with one FRD (READMEs: shas + rule; NOT necessarily pairs A / B / C,
   which were never recorded); 9 more uploads match several FRDs - pair them only on
   Soham's / the testers' word.
-5. **The review of the week's fixes (2026-11-23; an independent agent on BUG_FIX_LOG,
   claims verified):** most fixed real problems; Soham's calls: (a) post214's
   MandatoryColumnCheckRule as a default (432 lines, 9 of 12 pairs moved, its error-code
   reader reaches none; revert = drop `std_mandatory_check` from the overlay's `dq_rules`)
   and (b) 212 #18's standard reject table in every ACFC DDL (one tracker line is its only
   source; revert = `standard_reject_table: null`) - both his own decisions, to decide
   again. Mine, no decision: post195's dead `fieldname` synonym - DONE (post219); the other
   one-word duplicates (`columnname`, `tablename`, `datatype`, `schemaname`) stay - code
   looks some up by that spelling; fold the two archive label lists (`requirement_archive_labels`,
   `archive_line_labels`) and post196 / post197's passes into READER_GENERALIZATION Phase 1.
   The review's own flaw (Soham caught it): "0 of 12 pairs moved" was read as "unneeded" -
   the rubric fixed in AGENTS.md ("Tester feedback is sorted BEFORE any code").
-4. **post215 (Feedback on the App) ON STAGING:** no submissions yet (2026-11-23: no
   `app_feedback/` folder); no admins - the staging state root needs `feedback_admins.txt`
   (one address per line; Soham to give the addresses).
-3. **The first tester (MandatoryColumnCheckRule, post214, on staging):** open: her
   spelling 'STDdelta' vs our 'STDDelta'; the NullCheckRule overlap she did not answer.
0. **Venu's "run the DDL tests from the App" (Soham + Venu):** options sent - (1) an
   "Open in Databricks" button, no rule change; (2) the App runs them - needs the
   EXPLAIN-only rule widened to read-only test statements, an identity (user
   on-behalf-of vs the App's SP), a warehouse (DBU spend), D1 only or more. Waiting on
   Venu's pick. Same rule blocks item 11.
1. **The health review (2026-11-18, Soham's calls):** (a) DONE 2026-11-23 - pairs 13-17 in
   the check by default (item -6; the 9 ambiguous uploads wait on a pairing word); (b) the READER_GENERALIZATION
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
3. **Tracker decisions (Soham)** (export: `tools/tracker/export_incident_tracker.ts`; the
   2026-11-19 update script set #5 #7 #11 #13 #18-#22 Resolved, #3 Open - confirm Soham
   ran it): #12 rest (STGDELTA `TGT_DATA_TYPE` precision - the tester: drop; the pair-1
   golden keeps it); #14 (a DataTypeCastRule - reverses post171); #16 (no grand master for
   a Workflow run - changes post166); #9 / #10 (fixed-width -> `SRC_FORMAT = CSV`,
   delimiter `|` - the tester's own solution says so; a cited constant once Soham agrees);
   #3 (stage + stage-reject TBLPROPERTIES - needs ACFC's stage template, Lokesh); #2
   external tables (item 7).
4. **Small, mine:** (c) a source header written only `Field` stays a question (a synonym
   only with more evidence); (e) store pairs A / B / C (+ pair_13) as Workspace
   `frd_sttm_pairs/pair_14-17` with READMEs and add them to the check (item 1a).
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
15. **Model comparisons** (other vendors vs Opus 5.5): `docs/MODEL_COMPARISON.md` -
    Gemini 4 Neon (2026-11-20) and the GPT-6.2 Astra summary (2026-11-19); verdict both
    times: stay on Opus (the vendor rule). Add every new one there.

## Recipes (tracked since 2026-11-10 - `tools/check/`, `/tmp` holds only copies)

- **Question count (P4, 2026-11-24; scripts were /tmp only):** per tree a detached
  worktree + its own copy of the state dir (`environments overlays leakgate`, NO
  `answers`); per pair `codegen.cli layout --config <tree>/config/config.yaml
  --workbook ... --frd ... [--vdd ...] --dry-run --no-cache --json` from cwd /tmp with
  `PYTHONPATH=<tree>/src` (the CLI's default `config/...` is relative - it fails from
  /tmp), `discover()` from the tree's `container_harness.py` for the files, the JSON
  `questions[]` (choices = `candidates`; stdout carries a trailing text line - use
  `raw_decode`); then the harness on a copy of the pairs WITHOUT their `answers.yaml`
  for the blocking keys (the run report's "Needed answers", deduped).
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
