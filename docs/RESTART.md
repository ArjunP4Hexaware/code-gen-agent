# Restart here — current state

Where the work is now. Update this file at the end of a session; when a block stops
being current, move it to `docs/CLAUDE_HISTORY.md` (rules still in force go to
CLAUDE.md). What each version did: `CHANGELOG_ACFC.md`.

## State (2026-10-27, post126 pushed, post124 deployed)

- **Branch** `feature/multi-table` at `8808a55` (post126) + docs, pushed. post125 = audit
  #5 (an unstated source stays blank + flagged), post126 = audit #7 (VDD / STTM delimiter
  disagreement is a conflict; a gaps: answer wins over the STTM). Suites on post126:
  `.venv` 2176, `.venv-d1` 1869 passed. **App still on post124 — post126 needs
  a deploy.**
- **App** `codegen-agent` deployed from `cad3698` (Soham, 2026-10-27), `/api/health` =
  `0.5.8.post124`, serving the dist with the new button label. The redeploy wiped the
  App's run state; the last LIVE pair_11 run (post123; 0 model calls, 0 tokens) had
  outcome GATE_FAIL — 4 feeds
  PASS_WITH_FLAGS, ONE feed FAIL on the new `ddl_identifiers` check: an STTM
  Standard-band column name with a stray space ("Word _Word", column 8 of that feed's
  standard table). The agent copies names as stated, so that invalid column was in the
  DDL since the feed was first generated (also in the post105 DDL shown to Nikshit);
  `ddl_parses` (post107) caught it, post122 names it. Fix belongs in the STTM (BSA).
  The combined DDL on the dashboard = the 4 good feeds: 8 CREATE IF NOT EXISTS, 8 SET
  TAGS, no OR REPLACE.
- **Today's versions (2026-10-26, one bump per fix, each with a test that fails without
  it; details in CHANGELOG_ACFC.md):** post104–105 DDL comments + run-safe DDL;
  post106 PK-note separator " — "; post107 notebook v2 never `partitionBy` + gate
  `ddl_parses`; then codeflow-audit fixes — post108 Standard-band-only key gets its
  input (#11), post109 segmented File Type delimiter (#3), post110 generic recycle rule
  behind an N cell (#1), post111 the layout model gets no cells of a header-less sheet
  (#9, privacy), post112 edo_sfmc run-safe + the gate fails CREATE OR REPLACE (#12/#15),
  post113 delimiter agreement compared as characters (#8 + medium #8), post114 pairing
  name match on word boundaries, post115 an answered load strategy must name one,
  post116 a quoted column index in the answers file, post117 the recycle-column
  question can be answered, post118 .docx FRD Load Strategy STD makes the feed
  two-layer (doctrine), post119 edo_sfmc tags escaped, post120 the unstated-recycle N
  badged a convention, post121 acfc_run.py honours `pairing:`, post122 gate
  `ddl_identifiers`.
- **Real-pair regression checks** (mock container harness, all 12 pairs, old vs new code,
  client copies in /tmp deleted after): run for post110, post113, post114, post118,
  post126 (vs post124: 12/12 same outcome, 170/170 artefacts identical — no real pair
  has either shape) —
  same outcomes; byte-identical DDL / IIG except post118 (3 pairs' FRD contracts gain the
  standard tables their Load Strategy STD implies; artefacts unchanged).
- **Newly seen flake:** `tests/test_m93_chooser.py::test_slow_and_failing_downloads_never_
  block_the_list_and_are_listed_unreadable` — a healthy STTM gets a 0.4 s classify
  timeout; under `-n 4` load it once took longer (passes alone, 3/3; the full rerun was
  green). Widen its timeout margin if it recurs.
- **Second flake (2026-10-27):** `tests/test_frd_default.py::test_a_paired_sttm_
  preselects_its_frd_labelled_paired` — `frd_name` None once under `-n 4` (it is in the
  `repo_shared_state` group, so likely state left by an earlier module there); passes
  alone 3/3, the full rerun was green. If it recurs, find which module leaves the
  selection behind.
- **Harness lesson (2026-10-27):** never run the old and new harness IN PARALLEL on one
  state dir — they share the layout cache, so one side reads a layout by `synonyms`, the
  other from `cache`: the contracts' provenance and every banner sha then differ (9
  false diffs on pair_01). Run them one after the other, or re-run one side warm.
- **Lesson (this session):** a push was once chained after a suite with 1 failure (the
  flake above; the tree was green on rerun) — read the result, then push, never chained.

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

- Phase 1 (deterministic, /tmp/trace — lost on a container reset): static graph,
  coverage with per-test contexts (91 functions never run; 153 CLI-only / 112 App-only
  src functions), vulture, config-knob audit (6 knobs never read, 55 defaults absent
  from the YAML), 62 skipped tests (33+ for fixtures removed 2026-08-22).
- Phase 2: a multi-agent workflow was STOPPED at 7 of 18 finders (1.7M tokens — no
  budget set; do not rerun it without one). Its 62 findings were verified BY HAND: 15
  high (13 real, 1 minor, 1 duplicate) and 29 of 47 medium/low triaged. Fixed: high
  #11 #3 #1 #9 #12/#15 #8; medium #8 #20 #21 #17 #3 #1 #37 #30 #19 #43/#44.
- **The "high" list's other seven** (numbering of `/tmp/trace/high.json`; #15 = #12's
  duplicate): the 2026-10-26 triage confirmed them but re-rated #2 #5 #7 #10 #13 #14
  medium and #6 low (partly confirmed). Re-checked on post124 (2026-10-27, the old
  probes + reading): all seven were still present. FIXED 2026-10-27: #5 (post125),
  #7 (post126). Still open, all codeable: #2 #6 #10 #13 #14.
  - #2 `extract/segmented.py:703` recycle window `or 15` (config default 7, no document
    states 15) -> `RECYCL_RETN_DAYS`;
  - (fixed, post125) #5 `frd_docx.py:1241` sentinel `unstated` -> IIG SOURCE cell badged from_frd
    (`metadata_template._source_cell`; probe: `{'value': 'unstated'}`);
  - #6 `layout/resolve.py:954` checks only the normalized label: the model's spelling
    reaches provenance and rule text (probe: `'FREQUENCY ::'` for `Frequency`);
  - (fixed, post126) #7 `resolve/resolver.py:528` STTM `|` vs VDD `,` -> `|`, no flag, no conflict;
  - #10 `primary_key.py:180` a corpus key never checked against the table's columns
    (probe: `NOT_A_COLUMN_X` in every key cell, rc 0; D1 only — goldens there);
  - #13 `emit/framework.py:689` edo_sfmc invents a title-cased COMMENT and uses
    `f.description` (Comments text) not `ddl_description` (ACFC runs acfc_prx);
  - #14 `generate_run.write_combined` never clears `<out>/combined/`: a CLI / harness
    rerun into the same dir that GATE_FAILs keeps the old combined IIG / DDL (App runs
    get a fresh folder).
- **Open — needs Soham:** high #4 (multi-file FRD split renames standard tables to the
  stage names and pairs files by name guess, silently; both the classic and the .docx
  copy) — tied to the multi-table decision; medium #29 ACTIVE_START_DATE = run date
  (post81, intended) vs the byte-stable rule; #12 any "as is" FRD rule turns every
  column STRING in both layers, unflagged; #13 the rule classifier stops at its first
  match.
- **Open — codeable later:** #36 notebook v2 drops fixed-width columns whose start /
  length is not a digit, unflagged; #35 notebook v2 several ADLS rows into one stage
  table overwrite each other (needs Spark to prove); #33 `<<COLUMN#n>>` placeholders
  repeat across sheets; #27 / blind spots: 23 of 25 notebook v2 tests skip (fixtures
  removed); dead code `_reject_segmented_family`, `_frd_required`, `band_layer_answers`
  (#5 #11 #26); #42 `ddl_parses` checks framework `.txt` only; #7 width questions
  keyed by sheet index; 18 medium/low still unverified. The CLI/App flag differences
  (#40 #41) are partly by design.
- The 11 audit areas never searched (config, edges, App runner / API, frontend, the
  cross-cutting lenses) — if resumed: one area at a time, inline or with a hard budget.

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
- **Three questions for Soham, unanswered** (two asked 2026-10-23): (1) stage column
  types: all STRING (recommended — the notebook lands stage as STRING too) or as the
  STTM states (today); (2) table COMMENT: description + load strategy (recommended),
  description only (prod), or load strategy only (today); (3) one file per layer (prod)
  or the combined `<ABBREV>_DDL.txt` (today; the combined set, App listing and
  `run_artefacts` read `_DDL.txt`, so a split touches all three) — keep the combined
  file behind a knob the pair-1 overlay pins either way.
- Prod has no PK and no load strategy; `q1` there vs our `A2` (ask Soham). The Pharmacy
  EDH RFC DDLs are warehouse dims (identity key, NOT NULL, `ADD CONSTRAINT PRIMARY
  KEY`, CDF) — a different pattern, not the target.
- `edo_sfmc` still writes `CREATE OR REPLACE` (its SFMC reference goldens do); ACFC runs
  `acfc_prx` (the overlay pins it), so left as is.
- Keep the stage DDL (Nikshit thinks the framework doesn't need it; do not deprecate).
- The segmented extractor reads the Primary Key cell but never stores `primary_key`, so
  that dialect gets no PK notes. Left as is.

**DDL test cases** (later): a generic best-practice set, chosen at runtime per feed,
filled with the feed's own values (target table, real location):
- positive / negative: file present; at the right location; column mapping correct;
  every column populated; column shift (negative: shuffle the columns);
- does the framework map by column name or by position?
- Soham may ask Jinesh / Suganya which file needs which cases.

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
