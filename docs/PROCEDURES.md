# Procedures — pushing, deploying, the App, gotchas

Moved verbatim from `AGENTS.md` on 2026-11-10 (they load only when needed). The skills `/ship-dev`, `/ship-staging`, `/pair-check`, `/handoff` and `tools/check/` carry them out; the rules here still hold when doing it by hand.

## Working rules (procedures)

- **Pushing:** the App deploys from GitHub, so an unpushed commit never reaches it —
  after a deploy, `/api/health` must name the pushed version. The App deploys FROM
  `feature/multi-table`, but a push alone does NOT redeploy it (verified 2026-11-02: the
  App stayed on the old commit until `databricks apps deploy` ran) — never push or
  deploy right before a demo without asking; local commits are always safe. A push that adds or
  changes `.github/workflows/` needs the `workflow` scope on the `gh` login (`gh auth
  refresh -s workflow`, interactive — Soham runs it); never route around a refused push.
- **Deploying:** two Apps. `codegen-agent` (from `feature/multi-table`) is the dev App:
  Soham is its only user, so the agent deploys it after every green push (recipe in
  RESTART.md), then checks `/api/health` names the pushed version and runs the
  Playwright smoke (Generate + Results: 200, no console errors). `codegen-agent-staging`
  (from `main`) is what the data engineers test: never deploy it, run on it or change
  its grants without Soham's word. For ~30 s after a
  deploy `/api/health` may answer non-JSON and the Dashboard time out — retry before
  believing it. A Git deploy can time out downloading the repo (`get-repo-archive ...
  timed out`) or fail "failed to extract source code from Git": a Databricks-side
  hiccup, retry the deploy once. **A failed deploy takes the App DOWN (502)** - restore
  it at once by deploying the last good commit by sha (`git_source.commit`, the full sha
  from `git rev-parse` - never a typed one), then stop and ask (spiral log 2026-11-06).
  A RUN on the dev App is
  live (client documents go to the model) — allowed without a per-run ask (2026-11-02;
  report pair, outcome and counts only); the App quotes a new pair's first layout run as
  6-8 DBU (a deliberately high estimate; measured once at 4.84 DBU, RESTART.md). Check
  the App is idle before starting a run: Soham uses it too, one run at a time. The App's API
  wants an OAuth token (profile `codegen-oaut`, RESTART.md); the DEFAULT PAT can deploy
  but not call the API. A STOPPED App refuses a deploy ("not in RUNNING
  state"): starting it bills compute — ask Soham first.
- **The shared progress spreadsheet** (SharePoint, sheet `codegen_agent`): Graph is
  refused by ACFC's Conditional Access (managed devices only) — never route around it.
  Write an Office Script Soham pastes into Automate: rows found by column A, a missing
  row = nothing written, a `DRY_RUN` switch, bold in column C = updated today (clear the
  previous day's bold, the C1 header names the date). Keep it short; detail goes to the
  day's work.
- **Gotchas:**
  - the DEFAULT Databricks profile's PAT lives 15 minutes (the coding App rotates it
    every 10): a CLI call that waits longer fails "Invalid access token" - use the OAuth
    profile (RESTART.md) for slow calls;
  - bash heredocs mangle escapes and backticks — write patch scripts with the Write tool
    and run them as files; write commit messages to a file and `git commit -F`;
  - `fixtures/** -text` commits raw bytes — patch fixtures with `read_bytes` /
    `write_bytes`, keep each file's EOL, check `git diff --cached --stat` for churn;
  - the state root lives in TWO copies: the Apps' `CODEGEN_STATE_DIR` (Workspace
    `codegen/state/codegen-state/`, mirrored read-only on every generate request - no
    restart) and the volume `d1_dlk/codegen/state/` the harness recipe copies; a state
    edit goes to both (byte-check each, a dated `.bak_<date>` beside it - loaders read only
    `<name>.yaml`), and it reaches BOTH Apps at their next run - Soham's word first;
  - the Playwright smoke here needs `LD_LIBRARY_PATH=/tmp/pwlibs/usr/lib/x86_64-linux-gnu:
    /tmp/pwlibs/lib/x86_64-linux-gnu PLAYWRIGHT_BROWSERS_PATH=/tmp/pw` (dev_bootstrap's
    Chromium + libs); without them Chromium dies on a missing `.so`, not the App;
  - the container harness sets `CODEGEN_CONFIG_OVERLAYS` itself for its sub-steps (its
    state overlay): a config experiment on a harness run goes into a scratch copy of the
    state dir's `overlays/acfc_prx.yaml`, never the environment variable;
  - a new field on a layout model (`layout/profile.py`) changes a fresh build of the
    tracked layout profiles: regenerate them (`scripts/build_layout_profiles.py`) and
    check the diff is that field only (`test_tracked_layout_profiles_equal_a_fresh_build`);
  - the container harness applies the state volume's `answers/<pair>/answers.yaml`, so a
    question the App asks (it applies none) may never appear in a harness run — check an
    App-path fix through the App's API (a local server on a scratch copy, mock);
  - a worktree has no `ui/frontend/node_modules`: symlink the main tree's for vitest /
    tsc / `npm run build`, remove the link before committing;
  - after a container reset, `~/bootstrap` runs `scripts/dev_bootstrap.sh`, which rebuilds
    the venvs, Chromium, the git hooks (repo pre-push + the container's Workspace-sync
    post-commit, both) and the push login; it prints what needs a person (OAuth). The
    coding App's own setup lives in the Workspace folder `coding-agents-databricks-apps`
    (SNAPSHOT deploy): change it by importing files there (never `.git`), then `databricks
    apps deploy codingapp` - a restart, so only on Soham's word;
  - `isolation: "worktree"` agents branch from the default branch — reset each to the
    working branch first, cherry-pick back, delete the `worktree-agent-*` branch;
  - running the App locally inside this container: the container is itself a Databricks
    App and sets `DATABRICKS_APP_PORT=8000`, which the backend reads before
    `CODEGEN_UI_PORT` — override `DATABRICKS_APP_PORT` (and point the storage roles at
    /tmp) or the server fails to bind;
  - on Windows hosts, `;`-separated path lists get MSYS-converted (`export
    MSYS2_ENV_CONV_EXCL=CODEGEN_CONFIG_OVERLAYS`), and the symlink test
    `test_state_volume_mirror.py` fails (WinError 1314) — passes on Linux.
## The App

- Deployed from GitHub (`databricks apps deploy codegen-agent … git_source`; recipe in
  RESTART.md); every deploy restarts the container and wipes its local run state. The
  manifest `app.yaml` sets `CODEGEN_PROVIDER=live`, the storage roles and
  `CODEGEN_STATE_DIR`; re-lock to the mock with `CODEGEN_FORCE_MOCK_PROVIDER=1`.
- **Whose identity the App uses:** always its OWN service principal (`WorkspaceClient()`
  inside the Apps runtime); there is no on-behalf-of user auth. So the person using the
  App needs no access to the folders, and anyone with Can Use on an App can choose and run
  every document its folders hold - grant Can Use accordingly. Each App has its own
  principal (`databricks apps get <app>` -> `service_principal_name`); grants never carry
  over. A principal needs **Can Manage** on the `codegen` folder (inputs / state /
  outputs / the state dir inherit it; Can Edit fails on file creation) and **Can Read**
  on `frd_sttm_pairs`. A folder the principal cannot see reads `empty` in `/api/health`,
  not an error. Both Apps read the same `app.yaml`; since post167 every App but
  `CODEGEN_STORAGE_PRIMARY_APP` (`codegen-agent`) keeps state + outputs in its own
  subfolder (`codegen/state/<app>/`, `codegen/outputs/<app>/`, made by the App) -
  inputs, the pairs and `CODEGEN_STATE_DIR` stay shared. Before post167 (still on an App
  whose tree lacks it) they shared runs, selection and "Clear past runs".
- The App's UI rules (guided page, look and themes, provider wording, Choose
  documents, Cancel run) live in `ui/AGENTS.md`, loaded when working under `ui/`.
- **Model cost** (`reasoning.dbu_rates`, source: databricks.com/product/pricing/
  proprietary-foundation-model-serving): Claude Opus 5.5 = 57.143 input / 285.714 output
  DBU per 1M tokens (+10% with regional processing); $ = the contract's $/DBU x rate
  (the page's example: $0.07). A cached pair makes no model call; output dominates.
- **Learned labels** (post174, `codegen.vocabulary`): an answer a refused FRD cell
  already states proposes its line label; proposals + approvals live in the SHARED state
  root (`vocabulary/`), approved on the dev App only (Soham), applied by `load_config` on
  both Apps from the next run - never before approval, never a cell value stored.
- Layer-2 approve / reject decisions are recorded (`ui/backend/state/decisions.json`)
  but never merged into generated code and never gate.
