# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
`AGENTS.md`, the rules file - `CLAUDE.md` until 2026-11-03). What each version did: `CHANGELOG_ACFC.md`.

## Start here (session ended 2026-11-10 - both Apps' code = post187; the DEV App's compute is STOPPED, staging running; everything pushed)

**Since the last version (docs / tools only, no bump):** the recipes are tracked in
`tools/check/` with the skills `/ship-dev`, `/ship-staging`, `/pair-check`, `/handoff`;
AGENTS.md split verbatim (root 240 lines; the pipeline's rules in `.claude/rules/pipeline.md`,
procedures in `docs/PROCEDURES.md`); this file trimmed (old blocks in CLAUDE_HISTORY).
`ship.sh`'s deploy path is not yet exercised end to end (dev was stopped, staging needs
Soham's word): watch its first `/ship-dev`. Starting the dev App bills compute - Soham.

**First check:** `git fetch && git status -sb` should say up to date with
`origin/feature/multi-table`. BOTH Apps on post187: dev from feature 718c4c3 (deployment
01f1dc902166...), staging from `main` 8fcdea6 (identical-tree merge, deployment
01f1dc9958511f...); health post187 + smoke (Generate + Results 200, 0 console errors)
green on both. Later docs-only commits on feature need no deploy. Session log:
CLAUDE_HISTORY §[H23].

**Open, in order:**
1. **post185's protocol lines** (Soham's call): the standard TBLPROPERTIES carry
   `delta.minReaderVersion 1` / `minWriterVersion 2` as he sent them, but a table with
   deletion vectors / column mapping / v2 checkpoints runs on 3 / 7 (Databricks upgrades
   it), so the DDL test case "includes delta.minReaderVersion = 1" will not match by eye;
   `predictiveOptimization` is no Delta property (stored as a label, enables nothing).
2. **Ask Lokesh (via Soham), from pair_2's TDD** (`rfc_samples/TDD_Implement_Medicare_
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
2b. **Also for Lokesh (drafted, acronyms spelled out, H23):** for plain vendor-file
   ingestion is the sub-product NSP? Is a CDC-via-HVR feed sub-product HVR (pair_06) or
   only the tool? Is a load "for HEDIS consumption" product DLK or HDS (pairs 05 / 07)?
   Any answer is a config change (the 3.2 / 3.3 `stated_as` phrases or a per-feed
   override), no code.
3. **TDD training** (Venu): only two TDDs exist in `rfc_samples` (pair_2's, pair_12's).
   They link "Generic Pipeline Design Documents" and "Parameterize ADF Workflows" on
   SharePoint (unreachable from here) - copies in the Workspace would be the useful ones.
   A TDD is training material only (AGENTS.md); more TDDs are needed before any convention
   is learned + proven on held-out pairs.
4. **Tell the tester (via Soham)**: staging has the "Do Not Map" fix (her Accumulators
   pair ran PASS_WITH_OPEN_INPUTS there), a VDD is optional (no question when none
   matches), the template TBLPROPERTIES, Naming-Standards codes read from the FRD
   (+ "How the names were built" in each report / LOG.md) and the Pipeline orchestrator
   dropdown (Advanced options). Message text drafted in the session (H23).
5. **A second standard table per stage table** (the 820 pair's `_sumry` tables): a model
   change in `metadata_template._table_groups` - Soham's call before any code.
6. **Rows 3 / 4 of the delegation workbook** (check an existing pipeline / IIG config, the
   tables in Unity Catalog): need read-only queries beyond the EXPLAIN-only rule - that
   rule changes first (his call).
7. NO_OF_CYCLE_PER_DAY "1" (corpus 98.2%) is wrong on pairs 11 / 12 - Soham's call.
8. **`codingapp` deploy** - the bootstrap patch is IMPORTED (CLAUDE_HISTORY, retired block "State (2026-11-04 — cost work, model pilot, App bootstrap patch)");
   `databricks apps deploy codingapp` restarts this container: on Soham's word, last in a
   session. After it: `gh auth login`, `~/bootstrap`, the checks in that block.
9. Step 3 for the STTM cell locator (`layout/cell_locate.py` reads only FRD cells); ask the
   BSA about pairs 05 / 11's STTM "DQ rules" sheet and pair_12's recycle days / stage load
   option; the Apps stop / start schedule, Venu's GPT-6.1 Sol answer, the 11-pair layout
   cost, Rama's answers (CLAUDE_HISTORY, the blocks retired 2026-11-10).

## State (2026-11-09 — post183 to post187)

- **post183** a "Do Not Map" STTM table / schema cell names no table
  (`layout.resolve._sttm_facts`; the staging Accumulators pair failed "FRD stage tables not
  mapped ... ['Do Not Map']"). Live dev run of that pair: PASS_WITH_OPEN_INPUTS, 1 feed
  PASS_WITH_FLAGS, 0 blocking, no model call; staging re-run (someone else's) the same.
- **post184** a VDD is optional: no pairing question when no dictionary shares content
  (`pairing.PairDecision.ambiguous`); AGENTS.md rule.
- **post185** the standard-table TBLPROPERTIES = the template Soham sent (21 properties,
  verbatim; zstd dropped). Open item 1 above.
- **post186** the Naming Standards product (3.2) / sub-product (3.3) codes READ from the
  FRD (`codegen.naming_codes`, transcribed tables in config; product = what the FRD
  ingests into, sub-product = a 3.3 entry named, else NSP + flag; none / several = open,
  asked); every PIPELINE_NAME sourced part by part in the feed report + run LOG.md
  ("How the names were built", `codegen.naming_provenance`, for Lokesh). 12 pairs: all DLK
  from an FRD line, pair_06 HVR (a held table-source IIG, so no written name changes).
- **post187** ADF (`PL_`, default) or Databricks Workflow (`WF_`) - App Advanced options
  "Pipeline orchestrator" / `generate --orchestrator`; `{pipeline_prefix}` in the ACFC
  patterns (`codegen.orchestrator`). No FRD / STTM / VDD states it (searched: 12 pairs +
  15 RFC packages, every prod IIG name PL_).
- Every one: both suites green, the 12-pair check (mock, framework) outcomes unchanged
  (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2 GATE_FAIL, 2 FAIL), dev deployed + smoked,
  staging merged identical-tree + deployed + smoked on Soham's word.

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
  recreate it after a reset: memory "Databricks OAuth login flow"; the DEFAULT PAT is
  refused by the API).
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
