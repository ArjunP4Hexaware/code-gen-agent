# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
`AGENTS.md`, the rules file - `CLAUDE.md` until 2026-11-03). What each version did: `CHANGELOG_ACFC.md`.

## Start here (2026-11-18, later - staging = post201; dev STOPPED on post194; feature = post201, pushed)

**First check:** `git fetch && git status -sb` = up to date with
`origin/feature/multi-table` (head = docs on top of 579ee2b, post200).
- **post201 (staging 12a8f46, 2026-11-18; health + smoke green):** a Comments column in any STTM band is rule text
  (`roles.target.comments`, `generic._comments`; Comments never span evidence -
  `_SPAN_NEUTRAL_ROLES`, the pair_07 side effect caught + fixed). Suites `.venv` 2618 /
  `.venv-d1` 2269; 12-pair: outcomes + artefacts unchanged. From the tester's question
  (her Comments column = the standard band's last column, read by nothing).
  Her date-format note as a DateConversionRule: Soham chose option 1 (no code) - she
  writes "Convert <source> to <target>" in the Comments cell and types the standard
  column Date; proven by `tests/test_dq_stated_only.py ::
  test_a_comments_date_rule_writes_a_date_conversion_row_only_with_both_formats`
  (a one-format note writes no row, by design).
- **post200 (staging 3e9168f, 2026-11-18; health + smoke green):** FRD labels match their synonyms with spaces ignored
  (`frd_docx.label_key` / `LabelTable` / `LabelSet`). Both suites green (`.venv` 2614 /
  `.venv-d1` 2265), 12-pair outcomes unchanged, no artefact cell moved; pair_08's Data
  Quality section is now read (+1 validation rule, Layer 2 only). CI: one load-timing
  failure in `test_m93_chooser::test_a_run_never_waits_for_the_vdd...` (passed 3/3 alone,
  green on re-run) - a second timing-sensitive test in that module.
- **staging `codegen-agent-staging` = post201** (`main` = 12a8f46, identical-tree merge;
  health + smoke green).
- **dev `codegen-agent`:** STOPPED, last deployment post194 - starting it bills compute
  (Soham's call); then `/ship-dev` deploys post201.
- **Every version this session fully checked:** both suites green (`.venv` 2609 /
  `.venv-d1` 2260 on post199), CI green, framework 12-pair outcomes unchanged
  (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2 GATE_FAIL, 2 FAIL), no artefact cell moved.
  Per-fix reach + revert in `docs/acfc/BUG_FIX_LOG.md`.
- **The tester (staging) has not re-run yet:** her bugged run was cancelled; post195-197
  are its fixes. When she runs, read `GET /api/demo/status` / her run folder: she should
  be asked only LOBs, domain and the file of 2 tables.
- After a container reset: `~/bootstrap`, then the OAuth login (recipe below).
- Session log: CLAUDE_HISTORY §[H27].

**Open, in order:**
0. **DECIDE (Soham): `docs/acfc/READER_GENERALIZATION.md`** - the one-reader plan
   (phases 0-3; 0-1 change no output). The cheap wins (§5): post198 DONE (STTM / VDD
   headers, spaces ignored), post199 DONE (one strategy alias table, "Incremental"
   dropped), post200 DONE (FRD labels, spaces ignored - the synonym containers only,
   `normalize_label` unchanged). **NEXT: the delimiter readers** (5+ functions, 4 files)
   as the next value normaliser. Pairing is NOT a cheap win (6 matchers differ on purpose) - Phase 2.
1. **Tracker decisions (Soham), from incidents 9-17** (tracker export: Office Script in
   H26):
   - **#12 rest:** should STGDELTA `TGT_DATA_TYPE` drop the precision too? (the tester:
     yes; the pair-1 prod golden keeps `Decimal(17,2)`). post193 changed SRC only.
   - **#14:** a DataTypeCastRule for non-String standard columns - reverses post171 ("no
     cast rule"); the pair-1 golden has one.
   - **#16:** no grand master row for a Databricks Workflow run (master + children only) -
     changes the post166 flow; close to item 8(b).
   - **#9 / #10:** fixed-width feeds -> `SRC_FORMAT = CSV`, `SRC_FILE_DELIMITER = '|'`
     (the converter's output) - confirm it holds for EVERY fixed-width feed, then a cited
     config constant. The ADLS_FIXED_WIDTH_HANDLER rows ARE generated already; SRC_FORMAT
     is blank (not TXT, as the incident says).
   - **#11 / #13:** set Resolved (fixed post193, on staging since 2026-11-17).
2. **Small, mine:** (a) the unresolved-questions report names a line choice by its row
   label only (`answers.unresolved_report`) - add the `inline_label`; (b) the live layout
   model's STTM answer had an invalid `source` value - tighten the prompt / schema text;
   (c) a source header written only `Field` (a tester upload) stays a question - a
   synonym only with more evidence; (d) her FRD's "Landing Location:" lines are not
   read (`requirement_landing_labels` has only the ADLS spellings) - not asked today.
3. ~~README / DESIGN "third agent of five"~~ - DONE 2026-11-18 (second of three).
4. **The Standard Abbreviation List v28 - ASKED (Lokesh, via Soham, 2026-11-13):** in the
   Data Lakehouse Data Layers Standards V1.1 "Reference Documents"; same ask: Data
   Domains - SOR SOT.xlsx, the Data Modelling Guidelines, an IIG Framework sample. Files
   land in the Workspace `standards_docs` folder. Waiting on it: NM-001, NM-004, NM-006.
5. **DL-006 (Soham's call):** raw files by `abfss://` vs a Unity Catalog volume - ask ACFC.
6. **Incident 2 (Lokesh):** external tables - property set, `LOCATION` format, which FRD /
   STTM field marks a table external.
7. **PY-006 on feeds with many DATA_QUALITY_RULES rows** (pair_12) - not built, Soham's call.
8. **DECIDED, do not re-raise:** the standard TBLPROPERTIES stay as post185 has them; the
   Naming Standards win for grand master names; pair_12 is a Workflow (WF_), its prod
   IIG's PL_ names are wrong. Still open: (b) reuse an existing grand master? + the
   NSP / HVR / DLK-vs-HDS questions (H23 draft).
9. **TDD training** (Venu): only two TDDs in `rfc_samples`; training material only.
10. **A second standard table per stage table** (the 820 pair) - Soham's call.
11. **Rows 3 / 4 of the delegation workbook** - need the EXPLAIN-only rule changed first.
12. NO_OF_CYCLE_PER_DAY "1" wrong on pairs 11 / 12 - Soham's call.
13. **`codingapp` deploy** (bootstrap patch imported) - on Soham's word, last in a session.
14. The STTM cell locator step 3; BSA questions (pairs 05 / 11 DQ sheet, pair_12 recycle);
   the Apps stop / start schedule (CLAUDE_HISTORY, blocks retired 2026-11-10).

## State (2026-11-17 — post195 to post199)

- **post195** STTM source header `FieldName` -> the field name (config synonym).
- **post196** FRD Solution Requirements read beside F1 section tables: "Load Type" blocks
  (`load_type_block_labels`), `<file name.ext>` lines (`requirement_file_name_labels`),
  format from the extension when nothing states one. `FrdFieldSource.block_layer` (written
  only when set).
- **post197** a Load Type line's keys ("using keys ...", `load_type_key_phrases`) -> each
  feed's key statement by its requirement's file; `primary_key._match` accepts the
  table's audit columns.
- **post198** `layout/discover.header_key`: STTM / VDD header -> role lookups ignore
  spaces; a test guards that no two roles share a key.
- **post199** one load-strategy alias table (`extractor.frd.load_strategy_synonyms`) for
  every document and answer (`resolve/gapfill.strategy_reading`); "Incremental" dropped.
- **pair_13** (the Accumulators pair) in `/Workspace/Users/<me>/frd_sttm_pairs/pair_13`;
  not in the 12-pair default (`--pairs 13`). The tester's newer pair is NOT stored there
  (her uploads are on staging: `codegen/inputs/codegen-agent-staging/uploads`).
- **The codebase deck** (manager walkthrough): `/Workspace/Users/<me>/CodeGen_Agent_
  Codebase_Walkthrough.pptx`; slide 42 says post192 (update if reused).

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
