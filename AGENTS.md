# CodeGen / Data Engineer Agent — working notes

**This file holds rules and orientation only — keep it that way.** It is the rules file
for every coding agent on this repo (Claude Code, Codex, ...): it was `CLAUDE.md` until
2026-11-03, renamed so Codex reads it; older notes that say "CLAUDE.md" mean this file.
Session state goes elsewhere:
- **Where the work is now** (state, next up, open items, container recipes):
  `docs/RESTART.md` — read it first, update it at the end of a session.
- **What each version did:** `CHANGELOG_ACFC.md`.
- **Older notes, verbatim:** `docs/CLAUDE_HISTORY.md` (§[H2]–§[H12]; §[H9] = everything
  this file carried before the 2026-10-23 clean-up, §[H10] = retired RESTART.md blocks).
  The pre-clean-up file itself: `git show fa79a28:CLAUDE.md`.

**Who you work with:** Soham (GitHub `SohamBHexaware`) leads the project, decides,
deploys and is the dev App's only user. Talk to him directly ("you"), keep answers short
and plain, and give ELI5 versions of things he relays to PMs. Text he will send on to
others (Venu, Nikshit, the BSA ...) is written in his voice.

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
  diff close (the 2026-09 Genie episode: the documents answered it). **A production
  IIG is training and scoring material, never a value source** (Soham, 2026-11-05: users
  bring an FRD + STTM, not a prod IIG): a convention may be LEARNED from the corpus and
  proven on pairs it was not learned from; a constant copied from one pair's prod IIG is
  this bug (post177 removed post102's Daily masters). **A TDD (the RFC's technical design
  document) is the same: training material, never a value source** - the agent's inputs
  are the FRD, the STTM and a VDD (2026-11-09: only two TDDs exist in `rfc_samples`).
- **Citation rule:** every conflict / assumption / confirm item and provenance note quotes
  the exact FRD field or STTM cell it rests on (models enforce non-empty citations; tests
  assert them). Layer scope comes from Load Strategy, never from which schemas a Target
  Schema block names.
- **Never invent IDs.** PIPELINE_ID, PARENT_PIPELINE_ID, GROUP_ID and the other
  framework-assigned IDs (`always_blank` columns; the run's `_LOG.md` lists them) are
  assigned by the client's framework or by client instruction — the agent leaves them
  blank. The one exception (Soham, 2026-11-04, post166): under
  `placeholder_pipeline_ids` the IIG WORKBOOK shows placeholder PIPELINE_IDs that only
  show the flow (grand master 0 with a blank parent - NULL, Soham's decision, not 0 - master 1, children on, parent =
  their master), flagged `iig_placeholder_id`; `metadata_inserts.sql` never carries
  them (open `<<PIPELINE_ID#n>>`). Connection IDs come from the environment profile, never guessed. A `SYN_`
  template is never written.
- **The agent never creates tables, never runs jobs, never writes back** beyond the
  confirm-gated artefact publish. The only SQL the Databricks seam may send is `EXPLAIN`
  (`codegen.databricks.explain` enforces the prefix; it wakes the warehouse = DBU spend).
  Job parameters carry IDs the wrapper resolves, never inline SQL.
- **Client documents.** A live run sends document content to the model API. Runs on
  the deployed App are allowed without a per-run ask (Soham, 2026-11-02) - report the
  pair, outcome and counts only; a live CLI / harness run on client pairs outside the App
  still follows the client-document process; mock runs need none. Real client documents (and `IIG test cells.xlsx`) are read in place,
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

- **Branches:** `feature/multi-table` = all current work. `main` = the STABLE branch the
  data engineers' test App `codegen-agent-staging` deploys from (since 2026-11-03, when
  its tree was made identical to post164): it moves ONLY on Soham's word, and then as one
  merge commit on top of `main` whose tree is feature's (`git commit-tree
  <feature>^{tree} -p origin/main -p <feature>`, pushed as a fast-forward) - never a
  force-push, never a casual merge. `feature/iig-first` = the old demo branch
  `codegen-watch` pulled — never merge into it without Soham's word. `backup/ddl-only` =
  DDL-only fallback. `staging` is untouched since the feature branches were cut; nothing
  merges anywhere without Soham's word.
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
- **Other workspaces are out of reach from this container:** it runs as an App in workspace
  `4812116803419068`, and another workspace refuses its calls even with a valid login
  ("Cert validation failed ... trusted workload checks did not pass", seen 2026-11-03) -
  a security policy: never route around it; ask Soham to look in that workspace's UI or
  run the CLI from his own machine.
- **Pushing / deploying / the App's identity and grants / gotchas:** `docs/PROCEDURES.md`
  (moved verbatim 2026-11-10). Deploy with `/ship-dev` and, on Soham's word only,
  `/ship-staging` (`tools/check/ship.sh`); the 12-pair check is `/pair-check`
  (`tools/check/pair_check.sh`); the session hand-off is `/handoff`.
- **Two gotchas that bite everywhere:** bash heredocs mangle escapes and backticks (write
  patch scripts with the Write tool, commit messages to a file + `git commit -F`);
  `fixtures/** -text` commits raw bytes (patch fixtures with `read_bytes` /
  `write_bytes`).
- **CI** (`.github/workflows/tests.yml`): both venvs' suites, vitest + tsc and the
  version guard on every push; offline, no secrets. It never replaces the local
  full-suite run before a push.
- **`ui/frontend/dist` is tracked:** any `ui/frontend/src` change ships with a rebuilt
  `dist` (`npm run build`) — the App serves it.
- **Tests:** run the affected files while working; run the full suite in BOTH venvs once
  on the locally committed tree and READ the result before `git push` — never chain the
  push. In parallel: `pytest -n 4 --dist loadgroup` (`.venv` ≈ 12 min, `.venv-d1` ≈ 10, 2026-11-09;
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
  differing file before the copies are deleted — run the classifier INSIDE the check
  script, before its cleanup (kinds and counts only; a changed contract moves every
  banner sha256, so separate "sha only" from real changes). A notebook change runs the
  check in notebook mode (`--output-mode notebook`).
- **Working while a suite runs:** never edit `src/` or `tests/` under a running suite.
  Develop the next fix in a worktree (`git worktree add -b wip/<x> /tmp/t/<x> HEAD`, run
  with `PYTHONPATH=/tmp/t/<x>/src` and `-p no:cacheprovider`), then cherry-pick it onto
  the branch once the running checks are read, and delete the worktree and branch.
- **Model choice (measured 2026-11-03, `tools/model_eval/`):** Opus 5.5 medium, no
  workers, for code changes here (replay: 4/4 mergeable vs Haiku 5.5 xhigh 1/4 and Opus +
  Haiku workers 2/4). Haiku only for read-only work (search, log / test-output triage)
  that returns file:line pointers the lead then reads. Delegate edits only for large
  mechanical changes, with the lead's root cause, failing tests and placement written
  first - and check the diff against that, never the worker's own tests. Set model and
  effort at a session's start (a switch re-sends the whole context uncached). Sonnet 5.5 is
  no saving on long agentic work (more tokens, fewer solves; VulcanBench). Compare models by
  cost per ACCEPTED task, never per token.
- **Spend:** Claude Code tokens + Apps compute ≤ $1,500 / month (Soham). An App bills every
  RUNNING hour (Medium 0.5 DBU/h ≈ $290 / month); stopping or starting one is Soham's call.
- **HOME is wiped on every restart of the coding App** (`~/.claude`, auto-memory, the
  clone, the gh login, /tmp): what must survive goes into this repo, committed and pushed.
  After a restart: `gh auth login` (Soham), then `~/bootstrap` (written by the App's
  `setup_bootstrap.sh`: git login via gh, clones this repo on `feature/multi-table`, runs
  `scripts/dev_bootstrap.sh`).
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
- **Client-facing text names no person** (Soham, 2026-10-29): the App, generated files
  and the shared spreadsheet never say whose estimate / ask a thing was ("a conservative
  estimate", not "<name>'s"); the spreadsheet is in Soham's voice ("I", never "Soham").
- **The hand-off to the Code Review agent** (the third agent; Soham, 2026-11-10: not
  built into CodeGen, but no known issue at the hand-off that can be fixed here): a
  notebook-template change is re-checked with Code Review's exact rules (`review.py
  --no_llm`, its engine read from its owner's Workspace into /tmp, never vendored or
  committed; recipe in RESTART.md). A finding that needs a value no document states
  stays a known item, never a made-up value.
- **The incident tracker** (SharePoint `AI_Agent_Incident_tracker.xlsx`, sheet
  `CodeGen`) is read as JSON exported by an Office Script Soham runs (Graph is refused);
  it is client text - never committed; a bug it names is reproduced on the tester's
  documents (mock, /tmp) before it is fixed.
- **Never run the CLI from the repo root with outputs in `out/`;** use the harness or a
  scratch output dir. Shareable runs: `export
  CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example` first (the CLI loads
  the local `.env`, whose DL would leak the client domain into EMAIL_TO).

## Repo layout

`ls` / `codegen --help` show the tree. Not derivable from it:
- `emit/rfc.py` is unreachable, kept with its tests.
- `fixtures/` is synthetic / scrubbed only, each path re-included deliberately in
  `.gitignore`; `acfc_shapes/` pair 1 = the aliased client golden.
- prod IIG goldens exist only on D1 (never in `docs/acfc/iig_goldens/`); `acfc_run.py`
  = the one-pair fallback run where the App is not usable.

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

## The pipeline's rules (how a run works, config, outputs, seams, known gaps)

Moved verbatim to `.claude/rules/pipeline.md` (2026-11-10): Claude Code loads it when it
works on `src/codegen/`, `config/` or `tests/` files; every other agent (Codex ...): READ
IT before changing the extractors, resolver, emitters, gate or config.

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
