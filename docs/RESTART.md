# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
`AGENTS.md`, the rules file - `CLAUDE.md` until 2026-11-03). What each version did: `CHANGELOG_ACFC.md`.

## Start here (2026-11-09 - dev post184, staging post183)

**First check:** `git fetch && git status -sb` should say up to date with
`origin/feature/multi-table`.
- **post183** (a "Do Not Map" STTM table cell is no table) is on BOTH Apps: staging from
  `main` 99cdcd1 (identical-tree merge), health + smoke green. A live dev-App run of the
  staging pair that failed: PASS_WITH_OPEN_INPUTS (1 feed PASS_WITH_FLAGS, 0 blocking, 13
  open, no model call).
- **post184** (a VDD is optional: no question when nothing points to one; AGENTS.md rule)
  is on the DEV App only (bbc945c, deployment 01f1dc6b...; health + smoke green; the same
  pair now selects with no VDD question). Suites `.venv` 2546 / `.venv-d1` 2198.
  Staging waits for Soham's word.
Session log: CLAUDE_HISTORY §[H22].

**Open, in order:**
1. **Tell the tester (via Soham)** staging has post182: her 820 pair runs through (split
   into one feed per line of business, read by record type; its `_sumry` standard tables
   are flagged, not built); the HBL pair reaches the normal questions. Neither has been run
   LIVE yet - a dev-App run is allowed without a per-run ask (report pair / outcome /
   counts only); her files are in Soham's Workspace folder `aruna_test_files`.
2. **A second standard table per stage table** (the `_sumry` tables): a model change in
   `metadata_template._table_groups` (one stage table -> one standard table today) and the
   IIG's stage-to-standard rows; which records go to which table is not an IIG value any
   document states - Soham's call before any code.
3. **Rows 3 / 4 of the delegation workbook** (check an existing pipeline / IIG config,
   check the tables in Unity Catalog) are IN scope and not built: they need read-only
   queries beyond the EXPLAIN-only rule in AGENTS.md - that rule changes first (his call).
4. NO_OF_CYCLE_PER_DAY "1" (corpus 98.2%) is wrong on pairs 11 / 12 - Soham's call.
5. **`codingapp` deploy** - the bootstrap patch is IMPORTED (block "2026-11-04" below);
   `databricks apps deploy codingapp` restarts this container: on Soham's word, last in a
   session. After it: `gh auth login`, `~/bootstrap`, the checks in that block.
6. Step 3 for the STTM cell locator (`layout/cell_locate.py` reads only FRD cells); ask the
   BSA about pairs 05 / 11's STTM "DQ rules" sheet and pair_12's recycle days / stage load
   option; the Apps stop / start schedule, Venu's GPT-6.1 Sol answer, the 11-pair layout
   cost, Rama's answers (blocks below).

## State (2026-11-06 → 09 — post178 to post182)

- **post178** ADDITION.md retired (the run LOG.md carries HELD BACK / PROVENANCE).
  **post179** two staging failures: a TableName cell listing two tables (split by
  position, `extract/list_cells.py`), an FRD nested "Vendor | Target Table" cell, two sheets
  sharing one file, an audit column typed `integer`. **post180** "Record Type" = a segment
  column (H/D/T read by record type), the split on segmented sheets, a shared column keeps
  its standard mapping. **post181** one standard table per stage table on every sheet.
  **post182** nine fixes from an adversarial review of 178-181
  (`tests/test_adversarial_post182.py`). Details: CHANGELOG_ACFC.md.
- Every one: both suites green, its new tests fail with only it reverted, the 12-pair check
  (mock, framework) outcomes unchanged (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2
  GATE_FAIL, 2 FAIL). Real artefact changes on the 12 pairs: none, except post179's
  nested-cell fix (two pairs drop junk FRD tables and a bogus review item).
- **The delegation workbook** (Workspace `STTM_to_Artefacts_Agent_Delegation (1).xlsx`,
  overwritten in place on Soham's word): rows 12 / 13 out of scope, row 7 RFC dropped,
  ADDITION.md folded into LOG.md, rows 3 / 4 in scope; projected 29 h saved of 69 (42%).
- **Deploys failed for about an hour on 2026-11-06** (Databricks build layer, transient;
  spiral log + known cause): each failure took the dev App DOWN (502) - restore by
  deploying the last good commit by sha.
- /doctor (2026-11-06): 43 unused `~/.claude/skills` + debug-everything off, deepwiki MCP
  off for this project, defaultMode auto - all in HOME, gone on the next restart.

## State (2026-11-06 — post177 on BOTH Apps)

- **State overlay: three own-pair overrides REMOVED** (Soham's word; both copies - the
  Workspace `codegen/state/codegen-state/overlays/acfc_prx.yaml` the Apps read and the
  volume the harness reads; backup `acfc_prx.yaml.bak_20261105_pre_override_removal` beside
  each). Gone: `path_family_by_source` (pair_11), `feed_overrides` (pair_12 src_file_name,
  pair_2 email_statuses). Harness after: pair_12 84.9%, pair_11 36.6%, outcomes unchanged.
  Still open for Soham: NO_OF_CYCLE_PER_DAY "1" fails on pairs 11 / 12.
- **post177** (CHANGELOG; Soham: "it should only extract information from the FRD and
  STTM ... the IIG is for training off of ... don't cheat"): the masters' frequency is
  `run` = the feeds' one stated frequency, else blank + flagged - post102's Daily came
  from the pair_11 prod IIG. AGENTS.md now says a prod IIG is never a value source.
  Deployment 01f1d96994e91a3f81a5becd5f8caed0 (56f10cc); health post177; smoke Generate +
  Results 0 console errors. Suites `.venv` 2507, `.venv-d1` 2160. 12-pair check: outcomes
  12/12, only master rows + their INSERT lines change.
- **Line-A analysis of pair_12** (wrong IIG cells whose prod value appears in the FRD /
  STTM, 63 cells): 0 parser misses. 2 = the Daily constant (fixed); 18 recycle days and 4
  load options = the agent follows the FRD, prod does not; 24 = naming conventions
  (OBJECT_NAME, process name); 6 = environment (scored D1 vs prod PR); 9 = coincidental
  text matches.
- **Held-out audit** (values learned from prod IIGs, scored on pairs they were NOT learned
  from; the 199-IIG corpus is not reachable from this container): header / footer /
  schema-drift flags, `/Workspace` notebook prefix, ACTIVE_END_DATE hold; default path
  family holds on pair_12's ADLS sheet but not its STGDELTA sheet; data_type_style mixed;
  NO_OF_CYCLE_PER_DAY fails on 2 of 3.
- **Delegation workbook** (Workspace `STTM_to_Artefacts_Agent_Delegation (1).xlsx`, a
  sheet Soham shares): main sheet columns I-K (built today / what the agent does / hours
  today: 69 h -> 49 h per feed, IIG 4-8 h) + sheet "Measured 2026-11-05" (12-pair mock
  run, honest IIG scores 84.9% / 36.6%); the original is saved beside it
  (`... - before 2026-11-05.xlsx`). Hours are estimates until an engineer times a feed.
- **Recipes in `/tmp/deleg_scripts/`** (lost on a container reset - rebuild from this):
  `pair_check.sh <old-sha>` = the 12-pair check (state from the volume + the pairs into
  `/tmp/t/rp`, a worktree of the old sha, harness `--pairs 1` warm-up then all 12 per tree,
  `classify.py` = per pair identical / banner-only / REAL with xlsx sheet.column counts,
  then removes the worktree and the copies); `heldout.sh` = pairs 2 / 11 / 12 through
  the harness + `tools/iig_diff.py` per golden file, per-column status counts
  (`heldout_cols.py`); `score_run.sh` (+ `STRIP=1` = the state overlay's overrides
  stripped in the scratch copy) = per-pair totals; `parser_ceiling.py` / `line_a.py` =
  is a wrong cell's prod value stated in the FRD / STTM (a text match - short values
  match by accident, read the field's own cell before believing it).
- **Merged + deployed staging** (Soham's word, 2026-11-06): `main` 5527eff (tree = feature
  f3f9e30, fast-forward), `codegen-agent-staging` deployment
  01f1d9711f041d8b84eed96acaf56ead, health post177, smoke green. Feature has docs-only
  commits after f3f9e30 - `main` catches up at the next merge.

## State (2026-11-05 night — post176 on BOTH Apps)

- **Both Apps on post176** (Soham's word): dev from feature 5e75cdc (deployment
  01f1d940960a1a60ba7235e66297e5d8), staging from `main` = 001500c (identical tree;
  deployment 01f1d940a1fd1408bfb0709f8fb6e522). Health + smoke green on both; suites
  `.venv` 2501, `.venv-d1` 2154; 12-pair check post174 vs post176: outcomes 12/12, every
  artefact identical.
- **Parser self-extension complete (steps 1-4)** - `docs/PARSER_SELF_EXTENSION.md`:
  post175 = option B (a cell's known lines read, unknown ones skipped + flagged
  `frd_cell_line_ignored:`); post176 = step 3 (`layout/cell_locate.py`: for a refused FRD
  cell no other document fills, the model names the LINE; code copies + validates; cached;
  `frd_model_located:` in the review copy; AGENTS.md records the exception). The STTM's
  refused cells could use the same locator - not wired.
- **Next:** the `codingapp` deploy (restarts this container - last in a session).

## State (2026-11-05 late — post174 on BOTH Apps)

- **Staging on post174 too** (`main` 7e0a608, identical tree; deployment
  01f1d93523c0196180a448cabe7e7940; health + smoke green; `/api/vocabulary` there:
  can_decide false = read-only, as designed). A docs push failed twice with GitHub's
  "fatal error in commit_refs_rules" (status page green) and went through on a later try.

- **Dev App on post174** (fcafbf5; deployment 01f1d9327a761c3fb1638fb51b6acb9a; health +
  smoke green, `/api/vocabulary` answers from the shared state root, can_decide true).
  Staging on post173 (`main` b1615d4, Soham's word; health + smoke green). Suites `.venv`
  2487, `.venv-d1` 2140.
- **Parser self-extension:** steps 1, 2 (post174, learned labels: proposed by a run's
  answers, approved on the dev App, shared via `<state root>/vocabulary/`), 4 built. Step 3
  allowed by Soham for a refused cell of the ingested FRD / STTM only - not built.
  Open choice for Soham: read a cell's KNOWN lines and ignore unknown ones (today every line
  must be known, post168's rule).

## State (2026-11-05 late — post173 on the dev App)

- **Dev App on post173** (b1b61bd; deployment 01f1d928f9f917e6a165549728866686; health +
  smoke green). Staging stays on post171 (`main` 5bce029) until Soham's word.
  Suites `.venv` 2473, `.venv-d1` 2131.
- **Parser self-extension** (Soham: "I cannot viably manage a solution every single time I
  need to extend the parser") - plan `docs/PARSER_SELF_EXTENSION.md`: step 1 (post172,
  labelled lines for every single-value FRD field) and step 4 (post173, `codegen
  shapes-report --runs <dir | workspace:...>`) built; on the dev App's outputs the report
  lists 4 FRD shapes of today's run (label-prefixed Data Source, nested-table Object Name,
  per-file-block landing, pointer Frequency). **Next: step 2** (proposed vocabulary,
  approved in the App). **Step 3 waits on Soham** (the model seeing a refused FRD cell).

## State (2026-11-05 — post171 LIVE on both Apps)

- **Both Apps on post171** (Soham's word): dev from feature 2cf5096 (deployment
  01f1d8c2e8ee1fcfb17af461e673a07e), staging from `main` = 5bce029 (identical tree;
  deployment 01f1d8c2f5271d58b5dd216fb9b5c6ed). Health post171 + smoke green on both;
  suites `.venv` 2464, `.venv-d1` 2122.
- **post171 = DQ option 1 BUILT** (CHANGELOG): a DQ row only where a document states the
  rule (`dq_stated_only`, ACFC overlay); the rest = `iig_dq_not_generated:` suggestions in
  the review copy's summary. Real pairs: pair_03 = one FRD-stated DeDuplicationRule on its
  4 STTM key columns; pair_11 16 -> 4 rows; pairs 05 / 11's STTM DQ rules sheet names 0 / 1
  of the feed's fields (looks copied from another feed's template - worth asking the BSA).
  The 12-pair check ran before the review-summary wiring (that adds summary rows only).
- **Next:** the `codingapp` deploy (restarts this container - last in a session), then the
  older items below.

## State (2026-11-05 — post170 LIVE on both Apps)

- **Both Apps on post170** (Soham's word): dev `codegen-agent` from feature 4d1465d
  (deployment 01f1d8b7f2161f93868ff10900a790f0); staging `codegen-agent-staging` from
  `main` = 502a3b6, a merge commit whose tree is feature's (deployment
  01f1d8b806a716719ed9286e5b3d1f5b; the post169 merge before it: f1bc603). Health post170
  on both, smoke green on both; staging now uses `codegen/state|outputs/codegen-agent-staging`
  (post167 live there). Both suites green on the pushed tree (`.venv` 2449, `.venv-d1` 2107).
- **post170 - "Leave blank and continue"** for the file format / delimiter / frequency
  (CHANGELOG). Soham: "a blank answer is still better than no answer". 12-pair check: outcomes
  12/12, artefacts identical.
- **The message to the data engineer** (staging changes post167-170) was drafted for Soham.
- **Next:** (1) DQ option 1 (decisions below, in the 2026-11-04 evening block); (2) the
  `codingapp` deploy (restarts this container - last in a session).

## State (2026-11-04 evening — post167-169 deployed to the dev App)

- **Live, dev App `codegen-agent`:** post169 (54ee423; deployment
  01f1d8a1a6ed1313b9ac8021979609a1). Health = post169 (every root readable, the original
  folders: it is the primary App), live smoke Generate + Results 200, 0 console errors.
  Both suites green on the pushed tree (`.venv` 2442, `.venv-d1` 2101), vitest 271.
  - **post167 - each App its own state + outputs** (`CODEGEN_STORAGE_PER_APP=state,outputs`,
    `CODEGEN_STORAGE_PRIMARY_APP=codegen-agent` in app.yaml): seen 2026-11-04 - a data
    engineer's document pick on staging replaced the dev App's `selection.json` and her run
    card showed the dev App's run id. A non-primary App uses `codegen/state/<app>/` +
    `codegen/outputs/<app>/` (made by the App, inherits Can Manage on `codegen`).
    **Takes effect on staging only once `main` carries it** (Soham's word: merge + deploy
    staging); until then staging still writes the dev App's folders. Staging then starts
    with an empty layout cache / run list (its cache entries are keyed per tree anyway).
  - **post168 - an FRD cell of `<label>: <value>` lines** ("File Format: .txt" + "Delimiter:
    Pipe Delimited" in Object/data Format) is read line by line - the staging run asked
    for a file format its FRD states. 12-pair check: outcomes 12/12, artefacts identical.
  - **post169 - the typed question card:** a plain question + example, where the agent
    looked (FRD row + coordinates), what a blank answer does, technical reason folded.
    Open: Soham offered the data engineer a way to "click through" a blank value - that
    is a rule change (blank = held back today); not built, his call.
- **Open - DQ "option 1"** (Soham, 2026-11-04: DATA_QUALITY_RULES only from rules the
  documents state; derived rows to the review copy). Survey of the 12 pairs (counts only):
  the FRD's DQ section is one template (Uniqueness / duplicate check, Incomplete record
  rejection, Record recycle, then BSL/EDH rows); only pair_03 states a duplicate check, no
  pair states incomplete-record rejection (pair_11's says NA, yet post166 writes NullCheck +
  DeDup on every feed); STTM: pairs 05 / 11 have a "DQ rules" sheet ("allow nulls" /
  "don't allow nulls" per field), pair_07 a "mandatory fields include in DQ check" Y/N
  column, pair_03 an empty "DQ rules (hard reject / soft check)" column. None of these is
  read today (layout roles `dq_rules` / `dq_mandatory` exist, no extractor uses them).
  Soham, 2026-11-05: "if we're arguing about things in the prod IIG that's automatically
  wrong" - pair_11's DeDuplication / DataTypeCast / DateConversion rows (11 of 15) are stated
  by neither document: they go. **NullCheck: the STTM wins** over an FRD "NA" (the STTM's
  "DQ rules" sheet / "mandatory fields include in DQ check" column name the fields). pair_03's
  dedup columns: the STTM Primary Key (Soham). BUILT in post171.
- **Next:** (1) Soham: merge feature -> main + deploy staging (brings post167-169 to the
  data engineers); (2) the DQ questions above; (3) the `codingapp` deploy (below; restarts
  this container - last thing in a session).

## State (2026-11-04 — cost work, model pilot, App bootstrap patch)

**If a session ended on the `codingapp` deploy:** the bootstrap
patch was imported into `coding-agents-databricks-apps` and `databricks apps deploy
codingapp` was started (it restarts this container). Verify: (1) `gh auth login`, then
`~/bootstrap` exists and runs; (2) `~/.claude/settings.json` has the 5.5 model defaults,
`skillOverrides` (23 off) and no mlflow Stop hook; (3) the 14 Databricks skills are plain
files (`/tmp/bootstrap-aitools.log` ok); (4) `databricks apps get codingapp` shows the new
deployment SUCCEEDED. If the App came back without the patch: the pre-patch originals are
the patch base (`codingapp-patch-2026-11-04/codingapp.patch`, reverse-apply).

post165 (DQ rows only where the STTM states them) and post166 (placeholder pipeline IDs, workbook only) pushed; post166 DEPLOYED to the dev App `codegen-agent` 2026-11-04 (started on Soham's word; deployment 01f1d87be2191ec5ad49305a107e1c79, commit 492032e; health = post166, live smoke Generate + Results 200, 0 console errors). The staging App still runs post164 (main). Earlier pushes 9f387ee, adc2adb, f1b0757. Session log: CLAUDE_HISTORY
§[H19]; the harnesses: `tools/model_eval/` (README).
- **Spend, October 2026** (EDO Spend Monitor screenshots; Soham's user can NOT read
  `system.billing` / `system.serving`): model serving $2,108.53 (opus-5-5 on D1 $2,075.28 ≈
  all Claude Code - an App layout read is ~$0.34), Apps compute $480 (`codegen-agent`
  $300.97, `codingapp` = this container $139.09, two console tests $39.56), Genie $468.35
  (Genie Code before the switch to Claude Code; ends). **Target: Claude Code tokens + Apps
  ≤ $1,500 / month** (the old Genie Code Tier-5 budget).
- **Apps bill every RUNNING hour:** Medium = 0.5 DBU/h = 12 DBU/day ≈ $9.66/day at the
  observed ≈ $0.81/DBU (≈ $290 / month each). Running at the end of 2026-11-04:
  `codegen-agent` (restarted for the post166 deploy), `codingapp`, `codegen-agent-staging`
  (≈ $870 / month 24/7). Proposed, not done (Soham
  decides each stop / start): stop them outside working hours, or a scheduled stop/start
  job. The duplicate `code-gen-agent-staging` is stopped.
- **Model choice, measured** (replay pilot, 4 past fixes, blind review): Opus 5.5 medium
  solo 4/4 mergeable ($1.21 per mergeable fix); Haiku 5.5 xhigh solo 1/4 (patched the CLI
  instead of the shared GenerateRun; symptom fixes); Opus lead + Haiku worker 2/4 (lead
  delegated before the root cause; accepted a worker's semantic choice backed by its own
  green tests). Haiku hits its 5x long-context tier by ~request 7 (the ~68k session
  baseline). Rule in AGENTS.md.
- **AGENTS.md split test** (6 adversarial probes x 2 arms x 2 runs, $17.59): no rule
  violation in either arm; NOT adopted (saving ~$15-30 / month in real sessions vs the
  compaction risk). Don't re-run it without a new reason.
- **The coding App (`codingapp`) - patch IMPORTED 2026-11-04, deploy pending** (Soham's
  word to ship it; the Workspace source was checked byte-identical to the patch base first,
  the five imported files exported back byte-identical). Its source is
  the Workspace folder `coding-agents-databricks-apps` (SNAPSHOT deploy; the local copy is
  `/app/python/source_code`, byte-identical before the patch; HOME is wiped on restart, so
  the copy that survives is the Workspace folder `codingapp-patch-2026-11-04/files/` +
  `codingapp.patch`). The five files:
  `setup_bootstrap.sh` + `bootstrap_repos.txt` (new last setup step: the 14 Databricks
  skills as plain files instead of the plugin, writes `~/bootstrap`), `setup_claude.py`
  (`skillOverrides` for 23 unused template skills), `setup_mlflow.py` (no Stop hook while
  tracing is off; removes old copies), `app.py` (registers the step; the interactive-PAT
  path wrote Opus 4.7 / Sonnet 4.6 / Haiku 4.5 defaults - now 5.5). Shipped by importing
  those five files into `coding-agents-databricks-apps` (never `.git`), then `databricks apps
  deploy codingapp` - a deploy RESTARTS the container (session ends, HOME and /tmp wiped).
- **HOME is rebuilt on every `codingapp` restart** (all of `~/.claude`, the gh login, the
  clone, auto-memory): anything worth keeping goes in this repo, committed AND pushed.
- **GPT-6.1 Sol for the coding assistant (proposal to Venu):** same per-token price as
  Sonnet 5.5 on Databricks, about a fifth of Opus's tokens per task on VulcanBench -> about
  $0.33-0.87 per solved task vs $2.84 (Opus medium); Sonnet 5.5 is no saving ($2.75 at best,
  20 / 23). NOT enabled in D1 (only gpt-oss endpoints); `codingapp`'s `CODEX_MODEL` names a
  missing endpoint. Briefing page: Workspace `codingapp-patch-2026-11-04/coding-task-cost.html`.
  If enabled: run the replay (`tools/model_eval/replay`) on Sol via Codex first (< $5). The
  CodeGen agent itself stays Anthropic-only.
- **DEFAULT profile token lives 15 min** (the coding App rotates it every 10): long CLI waits on it
  fail "Invalid access token" - use the OAuth profile for anything slow.
- **Open from post165 / post166:** the FRD's Data Quality section and the STTM's "DQ
  rules" / "mandatory in DQ check" columns never reach DATA_QUALITY_RULES (Layer 2 only,
  off) - proposed: list them in the review copy as "stated, not generated". Decided (Soham,
  2026-11-04): the grand master's PARENT_PIPELINE_ID is NULL, as post166 writes it (not the
  0 of the framework owner's walkthrough, METADATA_DB_SEMANTICS §2).
- **Next (this block):** (1) the Apps schedule decision; (2) Venu's answer on Sol; (3) the items of the 2026-11-03 block below (measure the 11 pairs, Rama's
  answers, live runs).

## State (2026-11-03 evening — post164 DEPLOYED, main = staging App)

- **Live, dev App `codegen-agent`:** post164 (a88cd79; deployment
  01f1d7b294821f52ae8831217d2b349d). Health = post164, live smoke green (Generate +
  Results 200, 0 console errors). post164 = **Cancel run** beside a run's questions
  (`POST /api/demo/cancel`; a cancel ends idle, not FAILED) + **Clear past runs** drops
  a stopped run's blocking questions (it skipped needs_answers before). CHANGELOG_ACFC.md.
  Both suites green on the commit (`.venv` 2406, `.venv-d1` 2068), vitest 270.
- **Staging App `codegen-agent-staging`** (for the data engineers; AGENTS.md: never
  deploy / run / re-grant without Soham's word): deployed from `main` = 7e70ef0, a
  merge commit whose tree is IDENTICAL to post164 (main's 2 old commits kept; none of
  the client documents main had removed is on feature). Deployment
  01f1d7bc09ae173bbd71a37f544c0018 SUCCEEDED (the first attempt timed out downloading
  the repo; a retry worked). Principal `app-5aprci codegen-agent-staging`, application
  id 31fdee91-d999-4b8f-9071-f7c3dfd2819b. **Its health read every folder `empty` =
  not shared yet:** Soham is granting Can Manage on `codegen` + Can Read on
  `frd_sttm_pairs`; re-check `/api/health` (every root `readable`) and Choose documents
  after. A duplicate App `code-gen-agent-staging` (hyphenated) was created by a double
  submit - Soham is deleting it (keep `codegen-agent-staging`).
- **Open, the two Apps share storage:** both read the same `app.yaml`, so they share the
  outputs / state / inputs roles (runs, `selection.json`, the layout cache, the live-run
  record; Clear past runs on one deletes the other's runs). Proposed, not built: the App
  picks its state + outputs by `DATABRICKS_APP_NAME` (inputs + pairs stay shared), the
  staging principal gets Can Manage on its own new folders. Ask Soham before building.
- **pair_10 first-layout measurement (live, dev App, 2026-11-03):** the STTM layout was
  cached, so the run was re-resolved past the cache (`refresh`) to read STTM + FRD with
  the model: **4 calls, 30,088 in / 10,932 out tokens, 84 s = 4.84 DBU** (1.72 in + 3.12
  out; 5.33 with the regional uplift; about $0.34 at $0.07/DBU). Slight overcount: it
  includes the FRD call of the first (cached-STTM) resolve. Output = about 65% of the
  cost. The run stopped NEEDS_ANSWERS (15 open lines, the known BSA gaps; no answers
  given). The App's record still shows the 6-8 estimate (`measured_runs: 0`): it records
  only a FINISHED run, and that one was paused. The reply to Venu (6-8 = deliberately
  high; 4.84 measured; 3.15 was a different, now-off Layer-2 run) was drafted for Soham.
- **Next:**
  1. **Measure the other 11 pairs** (asked by Soham; NOT run - the App was busy with his
     own pair_11 run). Recipe: build the pairs map (`databricks workspace list` of each
     `frd_sttm_pairs/pair_<n>` -> JSON {pair_n: {sttm, frd, vdd}}; /tmp only, it holds
     document names); BACK UP the layout cache first (`databricks workspace export-dir
     <state>/layout_profiles <dir>`: a refresh overwrites every pair's cached layout and
     tombstones a document it cannot fully place, which would re-ask Soham's earlier
     answers), then `MEASURE_PAIRS_MAP=... python scripts/measure_layout_cost.py pair_1
     ... pair_12` (arms the one-shot refresh BEFORE each run = a clean first read, no
     double count; proceeds past questions with no answers; Cancel run after each; ~5
     DBU per pair, ~60 DBU total), then import the backup back (`databricks workspace
     import-dir --overwrite`). Report calls / tokens / DBU per pair, counts only. The
     2026-11-03 backup (26 files) was in /tmp and is gone - nothing was overwritten
     except pair_10's (by the refresh above).
  2. **Record Rama's answers** to `docs/acfc/RAMA_QUESTIONS_2026-11-03.md` (15 questions:
     child pipelines, ID assignment, N-object vs per-table pipelines; settles pair_11's
     child count, the ID rule and pairs 08 / 09). The shareable HTML page was built in
     `out/share/` (gitignored, lost on reset) - publishing it needed a claude.ai login.
     Prod facts found for it: PIPELINE_ID = GROUP_ID + 200 on 297 of 299 prod rows
     (pair_07 the exception), the stage -> standard group = GROUP_ID + 1 (pair_02),
     pair_11's 12 vs 10 schedule rows = 5 feeds vs 4 (not children per feed), pair_09
     carries BOTH shapes (one group of 36 objects and 36 one-object groups).
  3. Carried over from the block below: live runs pair_05 / 07 / 08 / 10, the end user's
     fixes (pair_07, pair_03 / pair_11 STTM spaces), Anju's golden load.
- **Other workspaces:** this container cannot call another workspace (trusted-workload
  check, AGENTS.md). Soham asked what `app-spend-monitor` (workspace 2465312035833126)
  reads: not answerable from here - its App page (Resources / Environment / source) or
  the CLI from his own machine. Likely the billing system tables, unconfirmed. A CLI
  profile `spend-ws` was saved in /tmp/cgs/oauth.cfg (gone on reset).
- **The rules file is now `AGENTS.md`** (renamed from CLAUDE.md for Codex, 2026-11-03).

## State (2026-11-03 — post163 deployed)

- **Live:** post163 (ae5aec7) - post160 STTM-authoritative tables, post161 HEDIS H4
  reader, post162 dark mode, post163 the Results feeds fold. Health + live smoke green.
  Session log: CLAUDE_HISTORY §[H17]. Tags post160..post163, `rollback/post159-deployed`.
- **Next (agreed with Soham, not started):**
  1. A one-page question sheet for the **Rama session (2026-11-03)**: child pipelines
     (parallel / sequential, children per feed: pair_11 12 vs prod 10), how GROUP_ID /
     PIPELINE_ID / OBJECT_ID are assigned, and what decides one pipeline with N objects
     (pair_09: 36) vs one pipeline per table (pair_02) - his answer settles pairs 08/09.
  2. **Live App runs** (allowed now): pair_05 (confirm the set-aside live), 07 (does the
     live layout place `sheets[2]/standard/column`, candidate column 15?), 08 and 10 (the
     real blocker past the layout step). Report outcome + keys only.
  3. **The end user's fixes** (no analyst is connected): pair_07 one answer; pair_03
     and pair_11 stray spaces in STTM column names (rows in "Open, needs others" below).
- **Open:** Soham reported once that a pair in Choose documents would not click; not
  reproduced live (rows enabled, a click selected pair_11). Likely the post-restart
  "restore" selection job, which disables every row and only dims it in dark mode -
  if it recurs: a clear disabled style + a "Restoring the last selection..." line.
- **Waiting:** Anju - one deployed HEDIS Stage -> Consumption load (DDL + the load) as
  the golden before any gold emitter.
- Pre-existing: 390 px sideways scroll on long names (Generate table, feed cards, h1).

## State (2026-11-02 — post162 deployed)

- **Pushed + deployed 2026-11-02:** efc1e79..61f2c74 (post160 + post161 + post162). The
  push did NOT redeploy; `databricks apps deploy codegen-agent --json '{"mode":"SNAPSHOT",
  "git_source":{"branch":"feature/multi-table"}}'` (DEFAULT profile works for deploy)
  did - deployment 01f1d70c3d531c5a9aedb65556c4f6ce, commit 61f2c74. `/api/health` =
  post162 (build sha "unknown" on a snapshot deploy), roots readable, no startup error;
  live Playwright smoke (`/tmp/t/dark/live_smoke.cjs`, CODEGEN_BEARER env only): Generate
  + Results 200, dark default, toggle works, 0 console errors. OAuth for the App's API:
  profile `codegen-oaut` in /tmp/cgs/oauth.cfg (the DEFAULT profile is a PAT, refused).
  Rollback: `git revert 61f2c74 6022f92 4049588`, push, then deploy (never force-push).

## State (2026-11-02 — post162)

- **post162 = dark mode, the default** (+ header toggle; CHANGELOG_ACFC.md). Light is
  pixel-identical below the header. Local tags post160 / post161 / post162; none pushed
  (a push is a deploy). Open, pre-existing: sideways scroll at 390 px on long names
  (Generate's table, Results' feed cards, a feed page's h1).
- Open UI ask (Soham, 2026-11-02, to discuss): the feeds collapsed in a dropdown,
  auto-collapsed on "View results", the framework artefacts immediately visible - which
  feed list (sidebar vs Results cards) was not settled.
- UI checks rebuilt in /tmp/t/dark: tour.cjs (pages x themes x widths), overflow.cjs,
  lightcmp.cjs (light pixel hash), drive.py (one mock run on a synthetic fixture via
  the API); local App on /tmp/t/ui scratch storage.

## State (2026-11-02 — post161)

- **post161 = the HEDIS H4 reader** (`codegen read-hedis`, gold contract dialect
  `hedis_h4`; CHANGELOG_ACFC.md). Additive: 12-pair check post160 vs post161 12/12 same,
  0 real differences; both suites green. Local tag `post161`. Not pushed (a push is a
  deploy). Next gold steps: H1 / H2 / H5 readers (H3's Addendum is SQL to translate),
  then one deployed consumption load per family as the golden (asked of the HEDIS
  owners) before any emitter.
- Sheet `codegen_agent` updated 2 Nov by Office Script (row 20 + two new rows); the dump
  script reads the sheet as JSON (read-only).

## State (2026-11-02 — post160)

- **post160 = the STTM is authoritative for a feed's table set** (CHANGELOG_ACFC.md).
  pair_05 FAIL -> PASS_WITH_OPEN_INPUTS; the other 11 pairs unchanged (12-pair check,
  0 real differences). Both suites green. Committed locally only - **a push to
  `feature/multi-table` IS a deploy** (the App deploys straight from that branch), so it
  was held for Soham's demo. After the push: `/api/health` must say post160, then the
  Playwright smoke.
- **Rollback points (local tags, not pushed):** `rollback/post159-deployed` = efc1e79
  (what the App ran on 2026-11-02); `post160` = the post160 commit. Undo after a push:
  `git revert <post160 sha>` + push (never force-push - others push here).
- **Pairs now** (mock): PASS_WITH_OPEN_INPUTS 01 02 04 05 12; GATE_FAIL 03, 11 (STTM
  spaces, BSA); NEEDS_ANSWERS 07 (one key `sheets[2]/standard/column`, candidate column
  15), 08 (layout `sheets[0]/source/field_name` in mock), 10 (BSA); FAIL 06 (feed-level
  mismatch + table source -> RDMS), 09 (parked: the per-table split crashes on answers
  keyed for the unsplit feed).
- **HEDIS folder** (`/Workspace/Users/<me>/HEDIS`, 53 docs, read 2026-11-02, structure
  only): 26 of 27 FRDs are a different template ("ETL Functional Requirement
  Definition" - extract / consumption / gold, e.g. "MDM to Gold Layer"), refused by the
  ingestion FRD reader (correct); the 2 Raw->Stage STTMs lay out with one open role
  (stage schema). Gold-layer learning: steps in the session notes - profile the gold
  FRDs, extend `contracts/gold.py` for the HEDIS consumption STTMs, get one deployed
  gold load per family as ground truth before any emitter.
- 12-pair check rebuilt: `/tmp/t/pc/pair_check.sh <old-sha>` + `compare.py` (path-aware
  classifier: same / meta / path / banner / real; deletes the client copies itself).
- **Container note:** `.venv` / `.venv-d1` rebuilt on 3.12 via `scripts/dev_bootstrap.sh`;
  Playwright Chromium in `/tmp/pw` + libs in `/tmp/pwlibs` (smoke `/tmp/pwtest/smoke.cjs`).

## State (2026-10-31 — post159)

- **Branch** `feature/multi-table`: pushed at post159 (620b5ee). App `codegen-agent`
  deployed from it, `/api/health` = post159, smoke green (Generate + Results: 200, no
  console errors), CSP / nosniff / no-referrer / X-Frame-Options live. post158
  (2b1e0c8) was deployed first. Both suites green on each; 12-pair mock check
  (framework + notebook) = outcomes and artefacts unchanged, only the known noise.
- **Prompt-injection / hostile-document hardening (2026-10-30/31):** red-team
  workflow (5 surfaces, mock, synthetic; plan `/tmp/t/pi/HARDENING_PLAN.md`, lost on a
  container reset - the CHANGELOG entries post158/post159 carry what was done) + a
  live injection eval on synthetic pair 4 (30 FMAPI calls; the model obeyed no
  planted instruction; harnesses `/tmp/t/pi/live/`). Done: every P0 and P1 item,
  P2-2, P2-9, P2-10, the content-filter fallback, the layout claim routing.
  **Open (P2):** P2-1 untrusted-data clause in the layout / Layer-2 system prompts
  (needs a live re-run of the eval to measure - billed, ask); P2-3 control / bidi
  characters blanked + flagged; P2-4 hidden rows / sheets flagged; P2-5 raw model
  log opt-in; P2-6 leak-gate NFKC / separators; P2-7 validate_tsql literals; P2-8
  feed-name length cap; P2-11 validate_advice hygiene; the advice request is not
  size-capped yet. **Decisions for Soham:** `layout.cache_model_placements`
  (true = today's caching, re-checked on every hit); should a disputed model
  placement block a bare CLI generate; ruff missing in notebook mode stays a flag
  (CLAUDE.md rule) now that `python_compiles` exists.
- **Arjun's STTM-agent output** (Workspace `sttm_agent_staging/SDOH_column_derivation`,
  4 bands incl. BSL, a `Transformations/Data Quality` column per band, a "derived as"
  standard column): three changes prototyped and adversarially tested on branches
  `wip/mod-a` (standard-band transformation text + `derived_column` flags), `wip/mod-b`
  (the "IF <col> is null or blank, THEN REJECT" wording), `wip/mod-c` (a BSL band known
  and excluded), combined `wip/mod-abc` (both suites green, 12-pair unchanged); worktrees
  `/tmp/t/wt_a|b|c|abc`. NOT built: each needs Soham's call (mod A: a derived row with no
  source field - DDL column or flag only, plus the pre-existing silent drop / CAQH crash
  / audit mis-filing of such rows; mod B: whether the rule feeds the dedup key, and
  whether the framework's NullCheck rejects blanks; mod C: source + BSL-only sheet =
  FAIL instead of NEEDS_ANSWERS, one-time layout-cache miss at deploy). Suggested order:
  C, then A with the derived-row fixes, then B.
- **Data Lakehouse Data Layers Standards** (read as v1.3): mapped in
  `docs/EDO_STANDARDS_ALIGNMENT.md` (pushed). Proposed, not built: flags
  `load_strategy_deviation:<layer>` and a schema-naming check from an overlay table;
  stage all-string vs `typed_stage` and the STD default cleansing go to the
  architecture team.
- **Shared spreadsheet:** the update script is in the Workspace,
  `/Workspace/Users/<me>/sheet_scripts/codegen_sheet_update_30oct.ts` (the App's
  terminal copies only the visible part of a long paste - put scripts there).
- **OAuth for deploys** expired once this session: the `BROWSER=echo` login recipe
  (After a container reset -> OAuth) worked; the URL also went to a Workspace file.

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
  - **2026-10-30: tables KEPT for Venu.** Pairs 01, 02, 04, 11, 12 regenerated (mock
    harness, code 79c9756 = post157), DDL run twice + every test case, tables left in
    place: 24 managed tables in `d1_dlk.soham_test` (`<schema>__<table>`, empty - no file
    loaded). DDL 48/48 OK on both runs; tests 120 PASS + 36 PASS needing a loaded file,
    26 NO DATA, 0 FAIL. pair_11 is GATE_FAIL on one of its five feeds (one column name
    no identifier - `ddl_identifiers`; same on post153, inputs unchanged since 10-12/10-19);
    its combined DDL covers the four clean feeds. Runner `/tmp/t/ddlt_keep.py` (=
    ddlt_run.py without the drop). Not shown after all: all 24 dropped the same day
    (Soham), `d1_dlk.soham_test` empty again.
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

- **12-pair check** (rebuilt 2026-11-06, `/tmp/t/p182/`): `pair_check.sh prepare | run |
  compare | cleanup` with the old sha in `base_sha` (look it up with `git rev-parse`, never
  type one) - copies `environments overlays leakgate` from `dbfs:/Volumes/d1_dlk/codegen/
  state/` and the pairs (`/Workspace/Users/<me>/frd_sttm_pairs`) into `/tmp/t/rp182`, adds
  a worktree of the old sha, runs the harness `--pairs 1` (warm-up) then 1-12 per tree.
  Compare the `--work` trees (`work_old` / `work_new` - the artefacts live there; `--out`
  holds only the run summary). Then: `outcomes.py` (per-pair outcome, old vs new),
  `classify_sha.py` (sha only vs REAL: normalizes the scratch paths, timestamps, the
  version, and 12-64-char hex - banners print a 16-char sha prefix; xlsx compared cell by
  cell), `classify.py` (REAL changes as shapes only: JSON key paths, md / sql line shapes
  with words masked - parse JSON raw, never after normalizing). Only then `cleanup`
  (deletes the copies + the worktree). Rebuild from this description if lost.
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
