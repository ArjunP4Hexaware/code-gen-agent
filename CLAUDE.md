# CodeGen / Data Engineer Agent — working notes

**This file holds rules and orientation only — keep it that way.** Session state goes
elsewhere:
- **Where the work is now** (state, next up, open items, container recipes):
  `docs/RESTART.md` — read it first, update it at the end of a session.
- **What each version did:** `CHANGELOG_ACFC.md`.
- **Older notes, verbatim:** `docs/CLAUDE_HISTORY.md` (§[H2]–§[H12]; §[H9] = everything
  this file carried before the 2026-10-23 clean-up, §[H10] = retired RESTART.md blocks).
  The pre-clean-up file itself: `git show fa79a28:CLAUDE.md`.

A new rule earns a line here only if it stays true across sessions; a dated "after postNN"
note goes in RESTART.md and then into the history, never here.

## Purpose & pipeline position

Generates Databricks ingestion artefacts (DDL, the IIG metadata workbook + its insert SQL,
optionally a PySpark + Delta notebook) from an FRD + STTM pair, optionally with a Vendor
Data Dictionary. It is the **second agent** of the three-agent AI-in-Engineering program at
AmeriHealth Caritas (ACFC): FRD→STTM → **CodeGen** → Code Review. BRD→FRD and SQL
Optimization were dropped (2026-08-21) — do not build them or depend on them.

**Where this runs:** Hexaware builds, ACFC rebuilds. This repo is the reference
implementation; the production agent is rebuilt inside ACFC from the contracts, config and
docs — anything not re-derivable from those does not survive the hand-off. ACFC runs it
as the Databricks App `codegen-agent` and through the container harness (`docs/RESTART.md`).

## Rules that never bend

- **Two-layer trust.** Layer 1 is deterministic Jinja2: everything derivable from the
  inputs, byte-stable, every file stamped with a provenance banner (input names +
  sha256). Layer 2 is the LLM: only free-text `validation_rules` the compiler classifies
  as `unmapped` reach a model; its output lands in a review artefact
  (`<feed>/candidates/candidates.json`), never in generated code, and every citation
  must appear verbatim in the input text. Candidates never affect the verdict.
- **A value not transcribed from an input is a bug, however plausible.** Every cell /
  column / DDL value comes from an input document, a cited config constant, or an answer
  the user gave; the rest stays blank AND flagged. Never synthesize a mapping to make a
  diff close (the 2026-09 Genie episode: the documents answered it).
- **Citation rule:** every conflict / assumption / confirm item and provenance note quotes
  the exact FRD field or STTM cell it rests on (models enforce non-empty citations; tests
  assert them). Layer scope comes from Load Strategy, never from which schemas a Target
  Schema block names.
- **Never invent IDs.** PIPELINE_ID, PARENT_PIPELINE_ID, GROUP_ID and the other
  framework-assigned IDs (`always_blank` columns; the run's `_LOG.md` lists them) are
  assigned by the client's framework or by client instruction — the agent leaves them
  blank. Connection IDs come from the environment profile, never guessed. A `SYN_`
  template is never written.
- **The agent never creates tables, never runs jobs, never writes back** beyond the
  confirm-gated artefact publish. The only SQL the Databricks seam may send is `EXPLAIN`
  (`codegen.databricks.explain` enforces the prefix; it wakes the warehouse = DBU spend).
  Job parameters carry IDs the wrapper resolves, never inline SQL.
- **Client documents.** A live run sends document content to the model API: live runs on
  client pairs only with Soham's approval per pair (the client-document process); mock
  runs need none. Real client documents (and `IIG test cells.xlsx`) are read in place,
  outputs go to a scratch dir, and only SCORES are reported — never copy client names or
  values into the repo, commits or replies. `scripts/scrub_check.py` must report zero NEW
  hits over tracked files (`docs/acfc/LEAK_LEDGER.md` holds the known ones;
  `tests/test_tracked_scrub.py`). Client terms never in the repo — the leak gate
  (`codegen.leakgate`) reads its denylist from the state volume.
- **Anthropic is the sole model vendor.** Claude via the Databricks Foundation Model API
  is a transport, not a vendor change. The Claude 4.8 / 5 families reject sampling
  parameters (`temperature` / `top_p` / `top_k` → 400): no temperature knob, and live
  output is inherently non-deterministic.
- **No secrets in the repo, ever.** Credentials only via environment / `.env`
  (gitignored; `.env.example` names them). Offline by default: tests and dry runs pass
  with zero credentials and zero network.
- **Byte-stable output:** no timestamps or randomness in generated files (`extract-sttm`
  takes `--generated-date`; workbooks via `stable_workbook_bytes`). Snapshots
  (`tests/snapshots/notebook_mode.json`, the pair-1 golden) are regenerated deliberately,
  never casually.

## Working rules

- **Branches:** `feature/multi-table` = all current work. `feature/iig-first` = the old
  demo branch `codegen-watch` pulled — never merge into it without Soham's word.
  `backup/ddl-only` = DDL-only fallback. `staging` / `main` are untouched since the
  feature branches were cut; nothing merges anywhere without Soham's word.
- **Others push to this branch from ACFC:** `git fetch` and rebase before work, never
  force-push.
- **Stage files explicitly, never `git add -A`.** Gitignored local-only files (never
  stage): `docs/acfc/denylist_local.txt`, `PROJECT_HANDOFF.md`,
  `CODEGEN_INDEPENDENT_REVIEW.md`.
- **Versions:** bump with `python scripts/bump_version.py` (pyproject + the
  `codegen-version-marker` in requirements.txt move together) whenever `src/` changes —
  the App caches its env on requirements.txt and `/api/health` must never name two trees
  with one version. The next version is the last `CHANGELOG_ACFC.md` entry + 1, never
  from a prompt. Docs-only pushes need no bump. The pre-push guard is
  `scripts/git-hooks/pre-push`; `scripts/dev_bootstrap.sh` installs it next to this
  container's global hooks (CI runs it too).
- **Pushing:** the App deploys from GitHub, so an unpushed commit never reaches it —
  after a deploy, `/api/health` must name the pushed version. A push that adds or
  changes `.github/workflows/` needs the `workflow` scope on the `gh` login (`gh auth
  refresh -s workflow`, interactive — Soham runs it); never route around a refused push.
- **Deploying:** Soham is the App's only user, so Claude deploys after every green push
  (recipe in RESTART.md), then checks `/api/health` names the pushed version and runs the
  Playwright smoke (Dashboard + Generate: 200, no console errors). A RUN on the deployed
  App is live (client documents go to the model) — never start one without asking.
- **CI** (`.github/workflows/tests.yml`): both venvs' suites, vitest + tsc and the
  version guard on every push; offline, no secrets. It never replaces the local
  full-suite run before a push.
- **`ui/frontend/dist` is tracked:** any `ui/frontend/src` change ships with a rebuilt
  `dist` (`npm run build`) — the App serves it.
- **Tests:** run the affected files while working; run the full suite in BOTH venvs once
  on the locally committed tree and READ the result before `git push` — never chain the
  push. In parallel: `pytest -n 4 --dist loadgroup` (`.venv` ≈ 7.5 min vs ≈ 12 serial;
  `tests/conftest.py` groups by module and keeps the App-state modules on one worker —
  a new test writing a checkout path outside those markers needs one). `--dist load`
  breaks that grouping; plain `pytest` stays serial. `ruff check src/
  tests/` stays clean; generated code must be ruff-clean too. Frontend: `cd ui/frontend
  && npx vitest run` (or `node node_modules/vitest/vitest.mjs run` where `npx` is
  missing).
- **Proving a fix:** its test must fail with ONLY the fix reverted (`git show HEAD:<file>`
  over the fixed file, run, restore) — a failure from a missing import proves nothing.
  A fix that can change generated output also gets the real-pair check: the container
  harness, mock, on every pair, old code vs new, comparing outcomes and the artefacts'
  hashes; client copies go to /tmp and are deleted after; report counts only. The
  layout cache lives in the state dir and is keyed per code TREE: warm EACH side (one
  pair-1 run per tree) before the comparison, and compare the contracts' layout
  `source` before hashes — a cold side differs on every banner sha. Classify any
  differing file before the copies are deleted.
- **Working while a suite runs:** never edit `src/` or `tests/` under a running suite.
  Develop the next fix in a worktree (`git worktree add -b wip/<x> /tmp/t/<x> HEAD`, run
  with `PYTHONPATH=/tmp/t/<x>/src` and `-p no:cacheprovider`), then cherry-pick it onto
  the branch once the running checks are read, and delete the worktree and branch.
- **Multi-agent workflows / fan-outs:** never without a hard token budget and effort
  caps — an uncapped audit burned 1.7M tokens on 7 of 18 finders (2026-10-26).
  Deterministic tools first (coverage with test contexts, static graph), agents only on
  the hotspots they rank, every finding verified before it is believed.
- **`.venv-d1`** mirrors ACFC's D1 environment: Python 3.12, `-e ".[dev,databricks]"`, no
  `ui` extra, pinned by `constraints/acfc_d1.txt` (pydantic 2.8.2 / openpyxl 3.1.2 /
  ruff 0.17.0 …; `docs/acfc/ENVIRONMENT_ACFC.md` §0). `model_*` pydantic fields need
  `protected_namespaces=()`; byte-pinned xlsx fixtures compare cell by cell when openpyxl
  ≠ 3.1.5; fastapi-only tests `importorskip`. openpyxl 3.1.2 keeps a
  `load_workbook(path)` file open — read workbooks on the generate path from bytes.
- **The test suite blocks every live model call** (`tests/conftest.py` sets
  `CODEGEN_BLOCK_LIVE_MODEL`; `CODEGEN_ALLOW_LIVE_TESTS=1` opts in) and runs WITHOUT the
  ACFC overlay (`CODEGEN_SKIP_ENV_OVERLAY=1`) on its own synthetic D1 profile
  (`tests/environment_profiles/d1.yaml`). A test that wants the overlay passes
  `overlays=[…]`.
- **`tests/test_remote_run_e2e.py`** is the only run test on remote storage roles —
  extend it when touching the run path. Nothing may assume a run lives under REPO_ROOT.
- **Never run the CLI from the repo root with outputs in `out/`;** use the harness or a
  scratch output dir. Shareable runs: `export
  CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example` first (the CLI loads
  the local `.env`, whose DL would leak the client domain into EMAIL_TO).
- **Gotchas:**
  - bash heredocs mangle escapes and backticks — write patch scripts with the Write tool
    and run them as files; write commit messages to a file and `git commit -F`;
  - `fixtures/** -text` commits raw bytes — patch fixtures with `read_bytes` /
    `write_bytes`, keep each file's EOL, check `git diff --cached --stat` for churn;
  - after a container reset, `scripts/dev_bootstrap.sh` rebuilds the venvs, Chromium,
    the git hooks (repo pre-push + the container's Workspace-sync post-commit, both) and
    the push login; it prints what needs a person (OAuth);
  - `isolation: "worktree"` agents branch from the default branch — reset each to the
    working branch first, cherry-pick back, delete the `worktree-agent-*` branch;
  - running the App locally inside this container: the container is itself a Databricks
    App and sets `DATABRICKS_APP_PORT=8000`, which the backend reads before
    `CODEGEN_UI_PORT` — override `DATABRICKS_APP_PORT` (and point the storage roles at
    /tmp) or the server fails to bind;
  - on Windows hosts, `;`-separated path lists get MSYS-converted (`export
    MSYS2_ENV_CONV_EXCL=CODEGEN_CONFIG_OVERLAYS`), and the symlink test
    `test_state_volume_mirror.py` fails (WinError 1314) — passes on Linux.

## Repo layout

```
src/codegen/   cli.py (all commands; `codegen --help`), config.py (models + load_config),
               contracts/ (pydantic: FRD, STTM, VDD, gold), extract/ (STTM workbooks incl.
               generic.py, frd_docx.py, vdd.py, segmented.py), layout/ (the layout
               recognizer + answers), resolve/ (FRD ⋈ STTM → ResolvedFeedSpec, gap fill),
               rules/ (rule classifier), reasoning/ (Layer 2 + the provider switch),
               emit/ (Jinja2: framework.py, metadata_inserts.py, dml.py, notebook_v2.py,
               rfc.py — unreachable, kept with its tests), gate/ (checks + verdict),
               metadata_template.py (IIG templates), run_artefacts.py (the per-run
               combined set), generate_run.py / run_stages.py / run_errors.py (outcomes,
               manifest, error lines), environments.py, input_choices.py, owed_inputs.py,
               leakgate.py, state_mirror.py, storage/ (local | workspace | volume — an
               EDGE), sharepoint.py + databricks.py (edge seams), templates/
ui/            the App: FastAPI backend (ui/backend, port 8571) + React frontend
               (ui/frontend, dist tracked); ui/README.md
config/        config.yaml (every knob) + overlays/acfc_env.yaml (ACFC values, always
               applied first)
fixtures/      synthetic / scrubbed only, each path re-included deliberately in .gitignore:
               faq/, reference/ (scrubbed SFMC artefacts), acfc_shapes/ (the synthetic
               ACFC universe; pair 1 = the aliased client golden), layout_profiles/,
               workbooks/synthetic_segmented_golden.xlsx
tests/         offline, no Spark; fixture-driven tests SKIP with a reason when files are
               absent (conftest `require_fixture_files`)
tools/ scripts/  iig_diff.py, iig_fill_rate.py, notebook_parity.py, ddl_shape.py;
               container_harness.py, scrub_check.py, bump_version.py,
               build_acfc_shapes.py, dev_bootstrap.sh, git-hooks/
docs/          RESTART.md, DESIGN.md, WORKFLOW.md (verdict semantics), LAYOUT_RECOGNITION.md,
               SEGMENTED_MODE_DESIGN.md, EDO_STANDARDS_ALIGNMENT.md, ACFC_DEPLOY.md
               (incl. CLI exit codes), ACFC_APP_ENV.md, acfc/ (SHAPES_FOR_PORT.md,
               ENVIRONMENT_ACFC.md, OPEN_QUESTIONS.md, OVERLAY_FIELDS.md, LEAK_LEDGER.md,
               METADATA_DB_SEMANTICS.md, iig_goldens/ — prod goldens exist only on D1)
acfc_run.py    Databricks notebook source: the one-pair fallback run where the App is
               not usable
app.yaml       the App manifest (env: CODEGEN_PROVIDER, storage roles, CODEGEN_STATE_DIR)
```

## Setup / run / test

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -e ".[dev,ui,live,databricks]"
uv venv --python 3.12 .venv-d1 && uv pip install --python .venv-d1/bin/python -e ".[dev,databricks]" -c constraints/acfc_d1.txt
.venv/bin/python -m pytest -q             # no Spark, no network
.venv/bin/ruff check src/ tests/

# One pair, framework artefacts, mock (outputs in a scratch dir):
PYTHONUTF8=1 .venv/bin/python -m codegen.cli layout --frd-contract-out … --answers …
PYTHONUTF8=1 .venv/bin/python -m codegen.cli generate --feed <id> --output-mode framework \
    --profile acfc_prx --iig-template iig_v2 --skip-tests --dry-run …
```

Python ≥ 3.10 is supported (`requires-python`); the venvs above use 3.12. `contracts.pairs`
is `[]`, so `generate-all` refuses loudly — generate with explicit inputs or the harness.
Running the *generated* Spark tests (no `--skip-tests`) needs Java 17 (`JAVA_HOME`) and
`PYSPARK_PYTHON` → the venv interpreter.

## How a run works

- **Inputs:** an FRD `.docx` (or the upstream FRD→STTM contract table, read SELECT-only),
  an STTM `.xlsx`, optionally a VDD `.xlsx` (feeds only the IIG fixed-width rows and the
  `vdd_*` gate flags, never the standard layer). Selection-time pairing is automatic
  among local candidates (`codegen.pairing`: content, ticket number, name role; a
  `pairing_overrides.yaml` wins); a manual pick is never marked automatic; no match or
  ambiguity pairs nothing.
- **Layout recognition** (`src/codegen/layout/`, `docs/LAYOUT_RECOGNITION.md`): a model
  decides WHERE things are, code copies the values, a validator sits between. Order:
  cache → synonyms → model → validate → user. The model sees only fingerprint material
  (header regions, table labels — never a data row) and no model string reaches a
  contract, DDL or IIG cell. A sheet with no header row (no 3+ cell row in 25: a
  lookup / valid-values sheet) is CAPPED: the fingerprint hashes it, the model gets its
  summary line only (`fingerprint.model_region`) — keep the cache key and the prompt
  separate there. A model claim that validates carries the DOCUMENT's wording (the label
  cell as written, the inline pair as the cell spells it; `labelled_rule` derived, never
  the model's flag), and a model FRD claim under a path it was not asked about is
  dropped. A layout `Rejection` holds coordinates and vocabulary only — never a cell's
  text, a model string or a model-invented sheet name (it reaches the state log, the
  REJECTED lines and the "structural labels only" report). Families A, C and E may legitimately leave roles unresolved
  under synonyms alone (`tests/acfc_shapes/layout_truth.py`) — do not widen the synonym
  tables to force them; a header seen in a client document is evidence, one invented to
  close a fixture gap is not.
- **Documented shapes:** `docs/acfc/SHAPES_FOR_PORT.md` — STTM families A–E, FRD families
  F1 / F2, VDD patterns V1–V3. The non-`MAPPING-` STTM reader is `extract/generic.py`.
- **Extraction rules:** `feed_id` = `normalize_feed_name(FRD feed_name)` (the resolver's
  join invariant, not the stage table). An STTM band's layer comes only from evidence
  (source by elimination only for the one leftover band; else `UNRESOLVED
  <sheet>/band[<n>]/layer`). Blank Schema → from the FRD with a NOTE, else a QUESTION;
  table names are always a QUESTION. Trailing `NA` rows → `audit_columns`. A Length cell
  is a byte width only when it is an INTEGER. An empty schema never reaches a contract.
  Segmented (H/D/T) files: segments are tables in both layers, identification derived
  from the STTM (`extract/segmented.py`, `docs/SEGMENTED_MODE_DESIGN.md`). A stated
  delimiter (any document) is read by `resolver.delimiter_char` (quoted character, else
  `extractor.delimiter_words`) — never "the character after a word". Recycle Flag
  cells: a `no_values` word is an unflagged row, every other non-empty cell must be a
  `Y ( <validation> )` flag; differing rules stop the extraction, never a silent pick.
- **Agreement between documents** goes through `gapfill.same_value(a, b, words)`: a
  punctuation-only value normalizes to '' — compare delimiters as characters (pass
  `extractor.delimiter_words`), never by `normalize` substring tests.
- **Gap fill** (`resolve/gapfill.py`): each fill is a `frd_unstated:<field>
  source_used:<cell>` flag; the STTM stage band is authoritative for catalog / schema /
  tables; the dialog asks only when sources disagree or are ambiguous.
- **Answers:** QUESTION / UNRESOLVED lines are blocking, INPUT_NEEDED is not, NOTE is
  informational. Answer lines are `f"{label:<15}{key} — {reason}"` (`cli.answer_line`,
  key verbatim; printed sheet keys are `sheets[<i>]/<layer>/<role>`); `generate
  --answers` / the App's dialog fill them. **Proposed is not applied:** a proposal is
  written only when chosen (`profile_default` values are the exception — written
  unasked, changeable).
- **Verdicts and outcomes.** Each feed's gate verdict is PASS / PASS_WITH_FLAGS / FAIL
  (`docs/WORKFLOW.md`); a flagged feed is PASS_WITH_FLAGS by design, not a failure. The
  run outcome (`codegen.run_stages.OUTCOMES`; exit codes in `docs/ACFC_DEPLOY.md`):
  PASS / PASS_WITH_OPEN_INPUTS (workbook written, every open line non-blocking) = exit 0;
  NEEDS_ANSWERS (any blocking line open) = exit 3; GATE_FAIL (files complete, moved to
  `<feed>/quarantine/` + `GATE_FAIL.md`), CRASHED (partial files deleted), FAIL (nothing
  written) = exit 1.
- **Error lines are two tiers** (`codegen.run_errors`, STABLE — the harness imports it):
  `first_error_line` = coordinates only (vocabulary + integers), `first_error_line_full`
  = quoted, written only under the outputs role. A new raise that quotes document text
  goes through `run_errors.located(exc, Coord(...), "<REASONS code>")`.
- **Layer 2** is its own stage after the outcome (`codegen.layer2_stage`, one request per
  feed): `--layer2 now | defer | skip`; config `reasoning.layer2_cli: now`,
  `reasoning.layer2_app: defer` (pending = `<feed>/candidates/layer2_pending.json`, asked
  by `codegen layer2` or `POST /api/demo/layer2`). For ACFC it is OFF: the
  `reasoning:` block at the top of `config/overlays/acfc_env.yaml` sets both to `skip`
  (Soham, 2026-10-27) — delete that block to turn it back on. Tests that exercise a
  Layer-2 mode with the ACFC overlay loaded pin the mode on their config.
- **One generate entry point:** `cli.generate_feed_result` + `codegen.generate_run
  .GenerateRun`, driven by the CLI and the App alike (the App's
  `GenerationStore._generate_feed` wraps it); manifests are byte-identical for the same
  pair (`CODEGEN_STAGES.json`).

## Config doctrine

- **Every knob lives in config;** no numeric literals in generator logic; the loader is
  loud on typo'd keys. Pydantic v2 models are `frozen=True` + `extra="forbid"`; missing
  is `None`, never a default. PHI masked to last-4 at every egress. A placeholder a
  reader stores for "no document states it" (the .docx reader's `unstated` source,
  `contracts.frd.UNSTATED_SOURCE`) is read through its helper (`stated_source`) — it
  never reaches an artefact as a value; the cell is blank + flagged.
- **Overlays:** `config/overlays/acfc_env.yaml` is committed and ALWAYS applied first by
  `load_config`; `CODEGEN_CONFIG_OVERLAYS` adds on top (later wins); client-shaped
  vocabulary lives in overlays, never in the tracked config.yaml. It pins the SD / CAQH
  family for every feed — a PRX-shaped feed needs a feed overlay on top.
- **State root** (`CODEGEN_STATE_DIR`, `config.state_root()`): `environments/<name>.yaml`
  (D1 / A2 / PR profiles; exactly one default; a required key unset under mock =
  `INPUT_NEEDED run.environment.<key>`, under live = fatal before anything is written),
  `overlays/<profile>.yaml` (notebook names, status sets, per-feed overrides —
  `docs/acfc/OVERLAY_FIELDS.md`), `answers/`, `leakgate/`. Not in git. On the App,
  `codegen.state_mirror` copies a workspace / volume state root read-only.
- **The provider switch** (`codegen/reasoning/mode.py`) — ONE switch, mock | live, never
  inferred from a configured endpoint or the Databricks runtime. First that answers
  wins: `--provider` > `CODEGEN_PROVIDER` > `reasoning.mode` (shipped: `mock`) > mock. It
  governs both model users (layout + Layer 2). `--dry-run` and
  `CODEGEN_FORCE_MOCK_PROVIDER` / `CODEGEN_FORCE_MOCK_LAYOUT` force the mock (under live
  that prints a WARNING first); live with its endpoint / key unset fails at startup,
  never a quiet degrade. `reasoning.provider` (`databricks_fmapi`, endpoint
  `databricks.serving_endpoint`) picks the live transport; `anthropic` (key-gated) also
  exists. Model name: `reasoning.model`.
- **FMAPI responses** from extended-thinking Claude come back as a LIST of typed blocks —
  `codegen.databricks.chat` normalizes via `_chat_content_text`. Do not "simplify" that
  to `content or ""`. Model JSON goes through `layout/model.py::parse_json_response` with
  one retry.
- **Engineering standards** live as data in `engineering_standards:` (EDO naming
  patterns + abbreviation tables) and `job:`; clause-by-clause map + deviations in
  `docs/EDO_STANDARDS_ALIGNMENT.md` (being revisited — RESTART.md).

## Output modes and artefacts

- `output.mode: notebook | framework | [notebook, framework]` (`codegen/output_modes.py`
  is the one vocabulary; CLI `--output-mode`, repeatable). The retired spellings `both` /
  `rfc` / `all` map to notebook + framework with a one-time notice, never an error.
  `output.profile_mode: {acfc_prx: framework}`; the App offers only `output.app_options:
  [framework]` and shows `output.app_files`.
- **Framework mode is what ACFC deploys:** an ADDITION to the client's existing
  metadata-driven framework. Per feed: the deployment DDL (per conventions profile),
  the IIG workbook + its BSA review copy, `framework/metadata_inserts.sql` (one INSERT
  per IIG row; an open cell = unquoted `<<COLUMN#n>>`), `config_rows.xlsx`,
  `ADDITION.md`, and (acfc_prx) the DDL test cases `<ABBREV>_DDL_TestCases.txt` — a
  SEPARATE file, never inside the DDL (Venu): read-only SQL the engineer runs after the
  DDL, gate `ddl_tests_read_only`. Per run and STTM, `<out>/combined/<STTM>_{IIG.xlsx,
  IIG_REVIEW.xlsx, DDL.txt, DDL_TestCases.txt, LOG.md}` (`codegen.run_artefacts`; the STTM token is dropped from the name;
  run-level rows written once, children never merged). Framework mode still renders the
  full pipeline in a scratch tree so gate verdicts match across modes. The master
  notebook is ACFC's own — the agent never generates, edits or ships it.
- **Notebook mode** (Option A, ~10% case): a standalone PySpark pipeline; `acfc_prx` uses
  notebook v2 (`emit/notebook_v2.py` + `templates/notebook_v2/`, rendered from the IIG
  rows). It never calls `partitionBy` — the DDL clusters every table (`CLUSTER BY AUTO`)
  and Delta clustering is incompatible with partitioning; `TGT_PARTITION_COLUMN` /
  `_VALUE` only scope an Overwrite (`replaceWhere`). Open conflict (RESTART.md): under
  `acfc_prx` the DDL types stage columns as the STTM states them while the notebook lands
  every stage column as STRING — now that the DDL is run first, that append fails.
- **Conventions profiles** (`conventions.profile`; default `edo_sfmc`): `edo_sfmc` = two
  `.txt` DDL files with per-column COMMENTs, CLUSTER BY AUTO + TBLPROPERTIES;
  `acfc_prx` = ONE combined `<ABBREV>_DDL.txt`, stage columns typed as the STTM states,
  every whitespace quirk of the pair-1 golden a knob, compared byte for byte; its column
  / table COMMENT, primary-key note and standard TBLPROPERTIES are knobs too (on in
  config.yaml, off in the pair-1 overlay so that golden stays exact). To add a
  profile: a key under `conventions.profiles`, a golden under
  `fixtures/acfc_shapes/<pair>/golden/`, a byte-identity test like
  `tests/test_m4_acceptance.py`. A DDL column identifier must match
  `^[A-Za-z_][A-Za-z0-9_]*$` (gate check `ddl_identifiers`, `gate/ddl_names.py`).
- **The DDL is RUN by the engineer** (Soham, 2026-10-26), not a reference only: every
  statement must be safe to re-run against deployed tables (`CREATE TABLE IF NOT EXISTS`,
  never `CREATE OR REPLACE` there) and terminated — `create_statement` (default `CREATE
  TABLE IF NOT EXISTS`) feeds BOTH layouts; only the pair-1 fixture overlay pins OR
  REPLACE for its golden. Two gate checks enforce it: `ddl_parses` (sqlglot, dialect
  `gate.ddl_parse_dialect`; a parse error, an unrecognised statement or a CREATE OR
  REPLACE fails; sqlglot is a base dependency, absent = `sqlglot_unavailable`, never
  FAIL; the pair-1 overlay sets the dialect null — its golden is unterminated) and
  `ddl_identifiers` (on the table definitions; a name as stated that is no identifier
  fails, naming layer / table / position — the agent never rewrites it, the STTM is
  fixed). ACFC's prod DDL template is the
  target; `tools/ddl_shape.py` scores the agent's DDL structure against it (counts and
  property names only — prod files read into a scratch dir, never the repo).
- **DDL string literals** escape a quote with a backslash (`\'`); `''` is no escape in
  Databricks SQL (DBR 18+ reads `'a''b'` as two chained literals). The `sql_literals`
  gate fails a doubled quote. A COMMENT is the STTM's description, never a Comments
  cell (rule text) and never an audit marker (`NA`).
- **IIG templates** (`metadata.template`): `iig_v1` = the 7-tab SFMC reference; `iig_v2`
  = the PRX 8-sheet layout, rows from `metadata_template.py`. Every cell is transcribed
  from an input, a cited constant or an answer; the rest is blank and flagged
  (`iig_blank:<SHEET>: <columns>`). A corpus value fills a cell only when `patterns.json`
  states it; anything else is a `<<D1:NAME>>` placeholder kept OPEN, never written. To
  add a template: a key under `metadata.templates` with `tabs` transcribed from the
  client's workbook, `always_blank`, the knobs, a `citation`; client inventory rows go in
  an overlay; pin headers + blank list in a test.
- **Scoring vs prod goldens:** `tools/iig_diff.py --golden <xlsx> --agent <every feed's
  *_IIG.xlsx>` with the default `--pair-mode identity` (`--pair-mode key` never for a
  score); `score.json` / `diff.xlsx` / `routing.csv` carry prod text and are never
  committed; `--export-scrubbed DIR` must re-scan to 0 hits. Build identity:
  `codegen.build_info` (`CODEGEN_BUILD.json`; iig_diff refuses a workbook without one).
- **Gate flags worth knowing:** `drag_fill_suspect` (≥3 adjacent `Decimal(p,s)` stepping
  p by one — flagged, never altered), `segments_from_sttm` / `file_pattern_from_sttm`,
  `vdd_*`, `iig_blank`, `iig_single_value` (a list in a single-value cell fails),
  `decimal_no_precision`, `source_names_repeated`. ruff missing = `ruff_unavailable`,
  never FAIL.

## Edge seams (network stays at the edges)

The generator's inputs and outputs are files on disk; seams attach before and after.
Keeping the network out of resolve / emit / gate is what keeps Layer 1 deterministic and
offline — **do not call Graph or Databricks from inside the extractors or the resolver.**
- **SharePoint** (`sharepoint.py`, stdlib-only): `codegen sharepoint-fetch` /
  `sharepoint-publish` (publish is the human gate). Read
  `.claude/skills/code-gen-agent/references/sharepoint-seam.md` before touching it.
- **Databricks** (`databricks.py`, the `[databricks]` extra): read-only list + download,
  plus the confirm-gated `publish_artifacts` (every write through `_guarded_full_name` /
  `WRITABLE_PREFIX`); table / job writes are NOT BUILT. Auth: the named profile unless
  `DATABRICKS_HOST` is set (the Apps runtime) — never leave a placeholder
  `DATABRICKS_HOST` in `.env`. Client-construction failures become
  `DatabricksTransportError` (502).
- **Storage roles** (`storage/`, `CODEGEN_STORAGE_*`): local | workspace | volume; Can
  Manage (not Can Edit) on the state / outputs / inputs folders. Health: `GET
  /api/health` (`ui/backend/health.py`; principal, roots, version).
- Deliberately NOT ported from frd-to-sttm: `jobs_runner.py`, the `_sharepoint.py` shim,
  the duplicate-input short-circuit (`.claude/skills/code-gen-agent/references/
  deep-dive.md`). Running jobs belongs to the client's framework.

## The App

- Deployed from GitHub (`databricks apps deploy codegen-agent … git_source`; recipe in
  RESTART.md); every deploy restarts the container and wipes its local run state. The
  manifest `app.yaml` sets `CODEGEN_PROVIDER=live`, the storage roles and
  `CODEGEN_STATE_DIR`; re-lock to the mock with `CODEGEN_FORCE_MOCK_PROVIDER=1`.
- One run page, "Generate" (`/modes`): "Choose documents…" (STTM / FRD / VDD), output
  toggles, selectors, Generate, the dialog that asks blocking questions BEFORE
  generating, then "View results" (the Dashboard). The App's API wants an OAuth token,
  not a PAT.
- Deprecated, no UI consumer (kept for API compatibility; nothing new may depend on
  them): `/api/replay/*`, `/api/demo/live-runs`, `/api/demo/input-documents`.
- Layer-2 approve / reject decisions are recorded (`ui/backend/state/decisions.json`)
  but never merged into generated code and never gate.

## Known gaps

- `extract-sttm` has never been run on FRD→STTM's own output: its `sheet_per_table`
  dialect emits no `Comment` / `Recycle Flag` columns (Layer 2's input would be dropped
  silently) and its `single_sheet` dialect is incompatible. Closing that round trip is a
  real integration task.
- `FrdContract._provenance.ambiguities` accepts plain strings AND structured
  `GatedAmbiguity` objects.
- Generated job JSON cluster shape / schedule is a config guess; output targets plain
  PySpark + Workflows, structured for a mechanical DLT port.

## Debugging

After two failed fix attempts on the same problem, follow the spiral-breaker skill
(.claude/skills/spiral-breaker/SKILL.md) before trying anything else. When extracting
facts from FRD/STTM documents, apply its Pattern C citation rules. Log resolved
spirals in docs/spiral-log.md.
If I say a past problem was a spiral that wasn't caught, log it with the
spiral-breaker Step 3 template, Caught by skill: no, including the known-causes
entry and replay scenario.
If the spiral-detector hook reports a signal, treat it as coming from me: stop
fix attempts and follow the spiral-breaker skill before the next change.
