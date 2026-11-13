# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
`AGENTS.md`, the rules file - `CLAUDE.md` until 2026-11-03). What each version did: `CHANGELOG_ACFC.md`.

## Start here (session ended 2026-11-13 - dev compute STOPPED; staging = post192; feature = post192, pushed)

**First check:** `git fetch && git status -sb` = up to date with
`origin/feature/multi-table` (head = the hand-off docs commit on top of 9b23113, post192).
- **dev `codegen-agent`:** compute STOPPED, last deployment post189 (fdf7e9f). Starting it
  bills compute - Soham's call; then `/ship-dev` deploys post192.
- **staging `codegen-agent-staging`:** post192, `main` = 820047f (identical-tree merge),
  health + smoke green. The tester's paused run (11/12, needs_layout) was CANCELLED on
  Soham's word before the post191 deploy (folder `demo_20261112_131457` kept).
- **post191 + post192 fully checked:** both suites green (post192: 2600 / 2251), the
  framework 12-pair check outcomes unchanged; post192's REAL changes = pair_10's frequency
  now read from a "File Frequency:" line (flagged `frd_line_located:`) + the new line
  choices in the open questions' reports - no DDL / IIG / SQL / notebook changed. The
  post191 notebook-mode 12-pair check was NOT run (comment-only change, Soham's call).
- **Before a deploy, check staging's stored runs** (`GET /api/demo/runs`, `/api/demo/status`
  through `tools/check/app_api.py`, `APP_API_CHARS=100000000` for the full JSON) and analyse
  them - Soham asks for it (2026-11-13). A deploy kills a paused run: cancel it first
  (`POST /api/demo/cancel`) on his word.
- After a container reset: `~/bootstrap`, then the OAuth login (recipe below) - auto-memory
  does not survive a reset, so anything that must is written here.
- Session log: CLAUDE_HISTORY §[H25].

**Open, in order:**
1. **Tell the tester (via Soham):** staging has post190-192 - her 11/12 run was cancelled
   for the deploy; re-run that FRD: frequency now fills itself, each open question offers
   the document's own labelled lines, and FRD answers are APPLIED (they were dropped
   silently before post192). Watch that run's next stored status.
1b. **A mixed-family FRD reader (not built, Soham's call):** the tester's FRD has F1
   section tables (Data Quality, Vendor Metadata) AND F2 Solution Requirement tables;
   `discover_frd` takes F1 as soon as one F1 table exists, so the requirement tables are
   never read as F2 - 6 questions stay open on it (format in a nested table, LOBs / domain
   in prose, Load Type with two values on following lines).
1c. **Small, mine:** the unresolved-questions report names a line choice by its row label
   only (`answers.unresolved_report`) - add the `inline_label` (a structural label) so the
   choices differ there; the live layout model's STTM answer had an invalid `source`
   value (refused by the schema, 4 of 4 sheets kept) - tighten the prompt / schema text.
2. **The Standard Abbreviation List v28 - ASKED (Lokesh, via Soham, 2026-11-13; message
   drafted in the session, not known if sent):** it is cited as
   `Standard_Abbreviation_List_modified_v28.csv` in the Data Lakehouse Data Layers
   Standards V1.1 "Reference Documents" (a COLUMN abbreviation list - it may not shorten
   notebook name parts; asked); the Naming Standards' "Abbreviations" section points at an
   attachment missing from our copy. Same ask: Data Domains - SOR SOT.xlsx, the Data
   Modelling Guidelines, an IIG Framework sample (the Code Review PRD's G-1). Files land
   in the Workspace `standards_docs` folder. Waiting on it: NM-001 (names 41-83 vs 30
   chars), NM-004, Code Review's NM-006.
3. **DL-006 (Soham's call):** the notebook reads source files by `abfss://` address; the
   standard prefers a Unity Catalog volume. No document names one - ask ACFC whether raw
   files land in a volume and its name per environment (then one environment-profile key).
4. **Incident 2 (Lokesh):** external tables - his property set + `LOCATION` format, and
   which FRD / STTM field marks a table external (message drafted in the session, H24).
5. **PY-006 on feeds with many DATA_QUALITY_RULES rows** (pair_12: `apply_stage_rules` 261
   lines): a data-driven rule dispatch would fix it - not built, Soham's call.
6. **DECIDED (Lokesh via Soham, 2026-11-10): the standard TBLPROPERTIES stay exactly as
   post185 has them** ("suggested by Databricks") - incl. `delta.minReaderVersion 1` /
   `minWriterVersion 2` and `predictiveOptimization`; tracker incident 3 closed by that.
   Do not change them or re-raise the 3 / 7 and label points. Still open from the same
   ask: incident 2 (external-table properties + how a document marks a table external).
7. **Ask Lokesh (via Soham), from pair_2's TDD** (`rfc_samples/TDD_Implement_Medicare_
   Growth_Expansion_2025_1003866.docx`). **(a) DECIDED (Soham, 2026-11-10): the Naming
   Standards win** - grand master names keep the product / sub-product codes (post186 as
   is). **(c) DECIDED (Lokesh via Soham, 2026-11-10): pair_12 is a Databricks Workflow -
   its names are `WF_`; its prod IIG's `PL_` names are wrong** (choose "Databricks
   Workflow (WF_)" in Advanced options for pair_12; a WF_ run scores as a PIPELINE_NAME
   mismatch against that golden - the golden is wrong, never "fix" it back; the RFC's TDD
   is where the orchestrator is stated). (b) explained to Soham, still open. Background:
   (a) prod grand master names are
   `PL_GMSTR_<source>_<subject>_<LOB>_<freq>` WITHOUT product / sub-product codes (pair_11's
   prod IIG too) - the Naming Standards pattern post186 follows has them; which wins?
   (b) most modules REUSE an existing grand master - should a new feed point at one (its
   name from the BSA) instead of the agent always writing a new GMSTR + MSTR? (c) pair_12's
   TDD says "Databricks Workflow Job" yet its prod IIG names are PL_.
7b. **Also for Lokesh (drafted, acronyms spelled out, H23):** for plain vendor-file
   ingestion is the sub-product NSP? Is a CDC-via-HVR feed sub-product HVR (pair_06) or
   only the tool? Is a load "for HEDIS consumption" product DLK or HDS (pairs 05 / 07)?
   Any answer is a config change (the 3.2 / 3.3 `stated_as` phrases or a per-feed
   override), no code.
8. **TDD training** (Venu): only two TDDs exist in `rfc_samples` (pair_2's, pair_12's).
   They link "Generic Pipeline Design Documents" and "Parameterize ADF Workflows" on
   SharePoint (unreachable from here) - copies in the Workspace would be the useful ones.
   A TDD is training material only (AGENTS.md); more TDDs are needed before any convention
   is learned + proven on held-out pairs.
10. **A second standard table per stage table** (the 820 pair's `_sumry` tables): a model
   change in `metadata_template._table_groups` - Soham's call before any code.
11. **Rows 3 / 4 of the delegation workbook** (check an existing pipeline / IIG config, the
   tables in Unity Catalog): need read-only queries beyond the EXPLAIN-only rule - that
   rule changes first (his call).
12. NO_OF_CYCLE_PER_DAY "1" (corpus 98.2%) is wrong on pairs 11 / 12 - Soham's call.
13. **`codingapp` deploy** - the bootstrap patch is IMPORTED (CLAUDE_HISTORY, retired block "State (2026-11-04 — cost work, model pilot, App bootstrap patch)");
   `databricks apps deploy codingapp` restarts this container: on Soham's word, last in a
   session. After it: `gh auth login`, `~/bootstrap`, the checks in that block.
14. Step 3 for the STTM cell locator (`layout/cell_locate.py` reads only FRD cells); ask the
   BSA about pairs 05 / 11's STTM "DQ rules" sheet and pair_12's recycle days / stage load
   option; the Apps stop / start schedule, Venu's GPT-6.1 Sol answer, the 11-pair layout
   cost, Rama's answers (CLAUDE_HISTORY, the blocks retired 2026-11-10).

## State (2026-11-13 — post191, post192)

- **post191** the last PY-003: the 74-char comment in `templates/notebook_v2/run.py.j2`
  wrapped; the recycle / shared-segment template test checks line width too.
- **post192** a staging FRD (no metadata rows; prose cells with `<label>: <value>` lines):
  (1) the App's FRD answers were dropped silently (`source` key forbidden by
  `FrdFieldSource`) and read blank (no value cell) - `_merge_frd` fixed; (2) "File
  Frequency" a frequency label; (3) `frd_docx._place_line_fields`: a single-value field
  with no row placed at its ONE labelled line (single-feed docs; disagreeing lines place
  nothing; `frd_line_located:` in the review copy); (4) `resolve._frd_line_candidates`:
  every labelled line a dialog choice (`inline_label`, `value_col`, `line` - the line text
  is UI-only, never in a report). Tests: `tests/test_frd_line_fields_post192.py` + the
  LayoutQuestions vitest.
- Slide 4 of the 11/13 WSR deck (Soham's Workspace) - CodeGen card rewritten in the deck's
  bullet style; the original is only in `/tmp/wsr/` (gone after a reset).
- Every version: both suites green, the framework 12-pair check outcomes unchanged
  (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2 GATE_FAIL, 2 FAIL).

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
