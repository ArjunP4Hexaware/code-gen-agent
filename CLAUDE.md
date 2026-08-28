# CodeGen / Data Engineer Agent — working notes

## Purpose & pipeline position

Generates production-shaped Databricks ingestion pipelines (PySpark + Delta
Lake) from approved machine-readable contracts — one FRD feed contract plus
one STTM mapping contract per feed. It is the **second agent** in the
three-agent AI-in-Engineering program at AmeriHealth Caritas: FRD→STTM
(produces the FRD feed contracts consumed here) → **CodeGen** → Code Review
(reviews what this repo emits).

**Scope cut 2026-08-21:** the program dropped from five agents to three —
BRD→FRD and SQL Optimization are no longer in scope. Do not build them or
add dependencies on them.

**Where this runs:** Hexaware builds, ACFC rebuilds. This repo is the
Hexaware-side reference implementation; the production agent gets rebuilt
inside ACFC's own environment with Claude Code, using this as the
blueprint. Nothing here deploys to ACFC directly — anything that cannot be
re-derived from the contracts, config, and docs does not survive the
hand-off. **Current program priority is FRD→STTM's live Databricks App
(due 2026-08-24), not this repo.**

Two-layer trust rule (never violate): **Layer 1** is deterministic Jinja2 —
everything derivable from the contracts, byte-stable, every file stamped
with a provenance banner carrying the contract names + sha256. **Layer 2**
is the LLM, mock by default — ONLY free-text `validation_rules` the
compiler classifies as `unmapped` reach a model; its output lands in a
review artifact (`out/<feed>/candidates/candidates.json`), never in
generated modules, and every citation must appear verbatim in the contract
text. Each feed ends in a computed gate verdict: PASS / PASS_WITH_FLAGS /
FAIL (semantics in `docs/WORKFLOW.md`).

## Repo layout

```
src/codegen/        sharepoint.py (Microsoft Graph transport, stdlib-only),
                    databricks.py (UC volumes transport, read-only, needs the
                    [databricks] extra; added 2026-08-27),
                    demo_sources.py / metadata_sheet.py / input_requirements.py /
                    governance_checks.py (request-time display+check modules,
                    all OUTSIDE the generation path; added 2026-08-27),
                    contracts/ (pydantic models, both dialects, frozen),
                    resolve/ (FRD⋈STTM join → ResolvedFeedSpec), extract/
                    (workbook→STTM extractor, see below), rules/ (rule
                    classifier), reasoning/ (Layer 2: providers, verbatim
                    grounding), emit/ (Jinja2 + notebook assembler), gate/
                    (preflight, tests, verdict), report/, templates/, cli.py, config.py
tests/              137 tests, offline, no Spark needed; 31 of them SKIP since
                    2026-08-22 because the fixtures they drive on were removed
                    (see "Fixtures & data rules"); the demo-UI and SharePoint-
                    route tests also skip when the [ui] extra (or httpx) isn't
                    installed. Run pytest for the live count rather than
                    trusting a number written down here.
config/config.yaml  every knob — contract pairs (EMPTY since 2026-08-22), extractor layout,
                    naming, masking, gate, job
fixtures/           GONE since 2026-08-22 — contracts/ (2 real-FRD contracts + MIDS STTM +
                    SYNTHETIC CAQH STTM + CV/golden FRD + expected extract), workbooks/
                    (anonymized golden STTM) and replay/ (live E2E set) were deleted and
                    git rm'd; .gitignore now blocks all three paths
docs/               DESIGN.md, WORKFLOW.md, EXTRACTOR_RECON.md, SEGMENTED_MODE_DESIGN.md,
                    LIVE_PATH_RECON.md, LIVE_RUN_RECORD.md, DEMO_RUNBOOK.md (client demo script),
                    EDO_STANDARDS_ALIGNMENT.md (clause-by-clause map of the EDO
                    naming/coding standards to the generator, incl. deviations), media/
ui/                 demo dashboard: FastAPI (8571) + Vite/React (5173); pip install -e ".[ui]", see ui/README.md
                    backend/sharepoint_routes.py: picker + confirm-gated publish
inputs/sharepoint/  gitignored landing dir for documents pulled from SharePoint
```

## STTM workbook extractor (codegen extract-sttm)

Deterministic, no LLM, pairing-aware: inputs are (workbook, FRD contract); `feed_id`
is `normalize_feed_name(FRD feed_name)` — the resolver's join invariant, NOT the
stage table name — and format/delimiter/standard-target presence come from the FRD side. Recycle validation text stays VERBATIM
(the resolver also accepts the client "Check with ... FOR ..." phrasing).
FLAT only — segmented (H/D/T) raises `SegmentedWorkbookError`; a prefix-less
workbook matching the family signature gets the docs/SEGMENTED_MODE_DESIGN.md
diagnostic. Header resolution is fuzzy + config-driven (`extractor:` knob);
trailing `NA` rows → `audit_columns`, never `fields[]`; `Comment` →
`value_spec`; file-name pairing canonicalizes date placeholders (CCYY→YYYY,
case-insensitive) and stays fail-loud. The CV/golden pair is byte-tested against
its committed expected output and can NEVER match the MIDS fixture
(different universe — docs/EXTRACTOR_RECON.md §4d).

## Setup / run / test

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"   # deps from pyproject
# Live Layer-2 runs additionally need the Anthropic SDK: -e ".[dev,live]"
.venv/bin/python -m pytest -q          # 80 passed, no Spark, no network

# Generate everything from the fixture contracts (mock Layer 2, no network)
.venv/bin/python -m codegen.cli generate-all --config config/config.yaml --dry-run --skip-tests
```

Expected with current fixtures: **all 4 feeds PASS_WITH_FLAGS** (every feed
has flagged/notification/unmapped rules — correct behavior, not a failure).
Output lands in `out/<feed_slug>/` (module tree, DDL, tests,
job JSON, one assembled runnable `.ipynb`) with a markdown report per feed
in `reports/` — both gitignored. Running the *generated* Spark tests (drop
`--skip-tests`) needs a JVM: `JAVA_HOME` → Java 17, `PYSPARK_PYTHON` → the
venv interpreter. `ruff check src/ tests/` must stay clean; generated code
must be ruff-clean against the same rules (`out/<feed>/ruff.toml` emitted).

## Config doctrine

- Every knob lives in `config/config.yaml` — contract pairs, extractor
  layout, naming, masking, segment discriminators, gate, job cluster. No
  numeric literals in generator logic; the loader is loud on typo'd keys.
- No secrets in the repo, ever. Credentials only via environment / `.env`
  (gitignored; `.env.example` documents the names).
- Program policy: **Anthropic is the sole model vendor** across the
  AmeriHealth agents program. Mock always wins on dry-run; live selection
  is transport-dependent (2026-08-28): the tracked config's
  `reasoning.provider` is **`databricks_fmapi`** (Claude via the workspace
  serving endpoint `databricks.serving_endpoint` — a transport, not a
  vendor change; resolves from YAML + workspace auth, no Anthropic key),
  with `anthropic` (key-gated on `ANTHROPIC_API_KEY`) still available.
  CAUTION: because FMAPI resolves without any env secret, tests that touch
  live paths must pin the provider — `tests/test_demo_ui.py`'s `client`
  fixture does this; a 2026-08-28 pytest run fired real FMAPI calls before
  that guard existed. First live FMAPI E2E: 2026-08-28 (CV golden pair,
  candidates verified). Live LLM use is confined to Layer 2
  (reasoning/review); code generation itself is deterministic Jinja2 by
  design. Model name lives in config (`reasoning.model`, currently
  `claude-opus-5`). The Claude 4.8/5 API families reject sampling
  parameters (`temperature`/`top_p`/`top_k` return a 400), so no
  temperature knob exists and live Layer-2 output is inherently
  non-deterministic — do not re-add one.
- Pydantic v2 models are `frozen=True` + `extra="forbid"`; missing is
  `None`, never a default. PHI masked to last-4 at every egress.
- **Client framework doctrine (Aug 26 framework calls, encoded 2026-08-27):**
  job parameters carry IDs the wrapper resolves from metadata, NEVER inline
  SQL (~250 KB parameter cap); all new tables managed with
  `CLUSTER BY AUTO` and CDF on (NOT workspace defaults — must be explicit
  DDL, per B0 observation); the agent never creates target tables and never
  runs jobs; Anthropic is the sole model vendor — Databricks FMAPI serving
  a Claude model (`reasoning.provider: databricks_fmapi`,
  `databricks.serving_endpoint`) is a transport, not a vendor change. The
  only SQL shape the seam may send is `EXPLAIN` (`codegen.databricks
  .explain` enforces the prefix), and an EXPLAIN wakes the auto-stopped
  warehouse = DBU spend from the shared ~120/month pool.
- **Engineering standards are REAL as of 2026-08-26** (three-input model
  input #2 is no longer a stub): the EDO Data Engineering Naming + Coding
  Standards live as data in `config.yaml engineering_standards:` (WF_/NB_
  naming patterns + abbreviation tables) and `job:` (prod-support alert DL
  on success AND failure, `timeout_hours`, Photon, DBR 15.4). The
  `standards_stub` gate flag is gone for the tracked config; the MODEL
  defaults keep the stub so a config without the section still degrades
  honestly. Clause-by-clause map + deviations:
  `docs/EDO_STANDARDS_ALIGNMENT.md`. The DDL templates emit
  `CLUSTER BY AUTO` (Liquid Clustering) and `LoadStrategy` accepts
  `"Upsert"` (the SFMC FRD's standard-layer strategy).

## SharePoint / Microsoft Graph (added 2026-08-23)

Ported from frd-to-sttm-agent-v2's integration. The document library is the
program's system of record: STTM workbooks and FRD contracts in, generated
artifacts out. `src/codegen/sharepoint.py` is the whole transport.

**It is a seam at the edges, deliberately outside resolve/emit/gate.** The
generator's inputs and outputs are files on disk; SharePoint attaches before
(`codegen sharepoint-fetch`) and after (`codegen sharepoint-publish`).
Keeping the network at the edge is what lets Layer 1 stay deterministic,
offline and credential-free. **Do not "simplify" this by calling Graph from
inside `extract-sttm` or the resolver.**

- **Standard library only** (`urllib.request`). Graph is plain REST; no SDK,
  no new runtime dependency. (`httpx` was added to the `dev` extra — it is
  test-only: `fastapi.testclient` is httpx-backed and the [ui] extra did not
  pull it, so the demo-UI tests could not actually run.)
- **App-only client credentials.** Secret from `SHAREPOINT_CLIENT_SECRET`
  (env or the gitignored `.env`), same resolution as `ANTHROPIC_API_KEY`.
  Excluded from `SharePointConfig.__repr__` so it cannot reach a traceback.
  Required Graph APPLICATION permission with admin consent: `Sites.Selected`
  on the target site, preferred over tenant-wide `Files.ReadWrite.All`.
- **Config split follows this repo's doctrine, not the source repo's.**
  frd-to-sttm reads every knob from notebook widgets/env. Here the non-secret
  knobs (host, site_path, library, input/output folder) live in
  `config/config.yaml` under `sharepoint:`, and identity + secret are
  env-only so a tenant is never committed. `param_from_config` layers them:
  env var > YAML > default. The section is OPTIONAL — a config without it
  still loads and every other command is unaffected.
- **Fail-loud, both directions.** Missing config raises naming both remedies.
  A short download raises rather than leaving a truncated .xlsx for openpyxl
  to report as a layout problem. A missing library lists what the site has.
  Fetching nothing and publishing nothing are both errors, not no-ops.
- **Publish is separate from generate on purpose.** Generation re-runs every
  time a rule or contract changes, and a re-generate is not a re-publish —
  the human gate sits between them. Running `sharepoint-publish` IS that
  gate, which is why the CLI takes no `--confirm` (mirroring the source
  repo's standalone publish notebook); the HTTP endpoint, which a stray POST
  could reach, DOES require `{"confirm": true}`.
- **Write scope is one folder.** `sharepoint.output_folder` is the only path
  this repo ever writes to. Keep the app registration's write grant scoped
  to it.
- **Publish names are qualified.** `<feed_slug>.md` / `<feed_slug>.ipynb`
  publish under their own name; anything else (`bronze.py`, `ddl.sql`) is
  prefixed `<feed_slug>__`, because those names repeat across feeds and a
  flat library folder has no other way to stop the second feed overwriting
  the first.
- **UI routes** (`ui/backend/sharepoint_routes.py`): a picked document is
  downloaded into `inputs/sharepoint/` — the same place `sharepoint-fetch
  --dest` writes — so it starts through the existing generate path. There is
  deliberately no second "generate from SharePoint" execution path. Status
  codes say whose problem it is: 503 not configured, 502 Graph refused, 400
  bad request, 404 no such feed/artifact, 413 over a cap. The panel renders
  nothing when unconfigured.

## Output modes (Option A / Option B, added 2026-08-27)

`output.mode: notebook | framework | both` (CLI `--output-mode`, UI
selector). **Option A** ("notebook", the default) is today's output byte
for byte — a fresh standalone pipeline, the ~10% case; guarded by
`tests/snapshots/notebook_mode.json` (sha256 per emitted file for the CV
pair — regenerate deliberately, never casually). **Option B**
("framework") is the primary ACFC path per the Aug 25/26 calls: an
*addition* to the existing metadata-driven ingestion framework (~90% of
runs) — `out/<slug>/framework/` holds `ddl_scripts.xlsx`,
`config_rows.xlsx` (THE approval artefact; built by `codegen.
metadata_sheet`, the single source of truth for the row layout — a
stand-in until the client's template arrives, values carry over),
`config_inserts.sql` (sqlserver|lakebase dialect via `framework:` config;
plain INSERTs, idempotency belongs to the framework's load path) and
`ADDITION.md`. **The master notebook is ACFC's own existing notebook
(clarified 2026-08-27): the DDL scripts and insert SQL are ADD-ONS to it —
the agent never generates, edits, or ships that notebook.** Framework mode still renders the FULL pipeline into a
scratch tree so gate checks and verdicts are identical across modes; it
persists only ddl/ + framework/. **Never-invent-IDs:** `always_blank`
columns render as `framework.id_placeholder` and are flagged — assigned
by the client's framework or manually by client instruction, never by the
agent. Workbook serialization is pinned byte-stable
(`stable_workbook_bytes`). The FAQ gained `has_header`/`has_trailer`
companions (NOT questions — banner/flag counts untouched) feeding the
"from FAQ" badge.

## FRD pairing + upstream contracts (added 2026-08-28)

The run takes an **(STTM, FRD) pair**. FRD contracts come from the
upstream FRD→STTM agent's Delta table
(`soham_workspace.sttm_agent.frd_contracts`, read via the allowlisted
SELECT-only `read_table_rows`; first read wakes the warehouse = DBU
spend) — there is deliberately **no docx→contract extractor** here: a
document with no contract row is a loud "run the FRD→STTM agent first".
Pairing precedence: explicit `demo.pairing_map` (canonical stems; ships
MIDS) → shared ticket number (CAQH `1005034`) → the ≥3-token stem
heuristic **as a UI suggestion only**, never auto-paired. Defaults are
unchanged (golden STTM + golden FRD, snapshot byte-identical), a
mismatched pick shows a warning chip, and feed-match failures name the
FRD used and offer the paired candidate — the human clicks, nothing
auto-retries. **Client-document rule:** the MIDS/CAQH artefacts are real
client documents, and a LIVE run sends their content to the model API —
live runs on client STTM/FRD pairs are permitted only per the program's
client-document process (Venu's email approval); the demo CV golden
remains the default rehearsal pair, and mock runs need no approval.
**Live runs are self-contained (View-results fix, 2026-08-28):** every
live run copies its FRD into `out/demo_<ts>/frd.contract.json` and writes
`run_meta.json` (frd_label / sttm_workbook / output_mode); the past-run
loader reloads with the run's OWN pair and recorded output mode (older
dirs fall back to the demo golden + inferred mode). Run completeness keys
on emitted artefacts (README / ddl / framework / candidates.json) — a
feed with ZERO Layer-2 candidates (all rules compiled deterministically,
e.g. MIDS) is complete and replays with an empty candidate list.

## Databricks volumes seam (added 2026-08-27)

`src/codegen/databricks.py` — the UC-volumes twin of the SharePoint seam,
READ-ONLY (list + download), same edge doctrine: fetch documents to local
disk (`codegen databricks-fetch` → `inputs/databricks/`, also the UI's
per-file Fetch in the STTM chooser), then generation proceeds from disk.
The client's raw documents live in `soham_workspace.codegen_agent.frd_raw`
/ `.sttm_raw` (uploaded 2026-08-27, un-anonymized, on explicit user
instruction — Databricks volumes are allowed to hold client documents;
this REPO still is not). Non-secret knobs in `config/config.yaml`
`databricks:` (profile/catalog/schema/volumes; env `DATABRICKS_*` >
YAML); auth resolves from the named profile (CLI OAuth keyring) — except
when `DATABRICKS_HOST` is set in the env (a Databricks Apps runtime),
where `_client()` lets the SDK's unified auth resolve the injected
credentials instead of a profile. `databricks-sdk` via the optional
`[databricks]` extra, keyless import. CAUTION: never leave a placeholder
`DATABRICKS_HOST` uncommented in `.env` — the SDK prefers env over
profile and will try to reach it. The FMAPI provider (`chat()` here +
`reasoning/providers/databricks_provider.py`) got its explicit go and is
LIVE as of 2026-08-28. Everything else write-shaped (tables, jobs, UC
grounding gate checks — "B1") stays NOT BUILT pending explicit go; the
governance check "never writes back" introspects this module and flips if
a write-shaped function ever appears (an FMAPI query is a read).

**Databricks App deployment (2026-08-28):** the demo UI runs as the
workspace app `codegen-agent`
(https://codegen-agent-7405617821962942.2.azure.databricksapps.com),
source synced to `/Workspace/Users/2000198474@hexaware.com/
codegen-agent-app` via `databricks sync --full` with `--include` for the
gitignored `ui/frontend/dist`, `fixtures/` (anonymized CV golden only)
and `inputs/standards/`; `requirements.txt` (`.[ui,databricks]`) is the
Apps pip install; `app.yaml` carries no secret — Layer 2 rides FMAPI on
the app's service principal, which holds CAN_QUERY on the serving
endpoint via the app's `llm-endpoint` resource. Redeploy = re-sync + 
`databricks apps deploy codegen-agent --source-code-path <that path>`.

## Demo panels + reference-document checks (added 2026-08-27, display/check only)

The Run-modes card grew config-driven panels — documents card
(`demo.input_documents`, env `CODEGEN_INPUT_DOCS_DIR` override),
source-files table + convention check (real FRD docx read live),
synthetic `databricks fs ls` block (`demo.databricks_paths` placeholders,
Option A), metadata-sheet preview for ACFC's metadata-driven framework
(`demo.metadata_sheet`, provenance-badged cells + xlsx download), and the
reference-document checks: the input-requirements deck's eleven rows
evaluated against the demo contract AND the real FRD document, plus the
two architecture decks' stated controls evaluated against the loaded run.
All of it reads documents at request time, caches nothing, commits
nothing, and NONE of it alters generated output — the generation path is
untouched and byte-stable (verified against tags `pre-demo-2026-08-27` /
`post-mgr-demo`). CLI twins: `demo-source-files`, `demo-metadata-sheet`.

### Deliberately NOT ported

Three frd-to-sttm features are deliberately absent (`jobs_runner.py`, the
`_sharepoint.py` shim, the duplicate-input short-circuit) — rationale in
`.claude/skills/code-gen-agent/references/deep-dive.md` § "Deliberately
NOT ported"; read it before porting anything from that repo. Running jobs
belongs to the client's framework, never to the agent.

## Branching model

All development on `staging`; `main` is the deployment branch — `staging`
merges to `main` only after testing.

## Fixtures & data rules

**No FRD/STTM material is in this repo — as of 2026-08-22.** On Arjun's
instruction that no client documents (raw or derived) live in any repo,
`fixtures/contracts/` (two of which were contracts derived from *real*
client FRDs, plus the MIDS STTM, the synthetic CAQH STTM and the CV/golden
pair), `fixtures/workbooks/`, `fixtures/replay/`, and the gitignored `out/`
and `reports/` (generated pipelines embedding CAQH/MIDS field names) were
deleted from the working tree and `git rm`'d. They remain in git history
until a purge is decided. What changed to keep the repo coherent:
`config.contracts.pairs` is `[]` (the model no longer requires ≥1 pair);
`codegen generate-all` and the demo UI's startup generate refuse loudly on an
empty list; `codegen generate --frd-contract X --sttm-contract Y` still works
with explicit paths; the `demo:` config section keeps its (anonymized-universe)
file names but the files are absent, so Live/Replay fail with file-not-found
until anonymized copies are restored; every fixture-driven test skips with an
explicit reason rather than failing (`tests/conftest.py` `require_fixture_files`
/ `_pair_paths`). Restoring anonymized fixtures at the configured paths
re-enables the full 80-test suite unchanged. The anonymized CV/golden set
(demo FRD + STTM contracts, golden workbook, and the `live_e2e_20260807`
replay set) survives at `044752e^` and may be restored **working-tree-only**
with `git show "044752e^:<path>" > <path>` — never `git checkout`, which
would stage and re-track the paths (done locally 2026-08-25; the MIDS/CAQH
client-derived contracts must NOT be restored).

Offline fixtures only — tests and dry-run generation must pass with zero
credentials and zero network. No real client data, ever; any new fixture
material must be anonymized first AND tracked by a deliberate decision (the
`.gitignore` re-include for workbooks was removed for that reason).
Generated output is byte-stable by design — no timestamps or randomness in
generated files; keep it that way (extract-sttm: inject `--generated-date`).

## Known gaps / cautions

- **There is no live-credential `.env` in this repo** (an earlier claim in
  this file that one existed was stale).
- **`extract-sttm` has never been run on FRD→STTM's own output.** It is
  validated against *client* workbooks (the CV/golden pair is byte-tested),
  not against what `04_sttm_render` emits upstream. Checked 2026-08-21: the
  upstream `sheet_per_table` dialect does match this extractor's sheet
  names, band labels and header synonyms — but it emits no `Comment` column
  (→ `value_spec` empty) and no `Recycle Flag` column (→ the verbatim
  validation text, i.e. this repo's entire Layer-2 input, is dropped
  *silently*), and its `single_sheet` CAQH dialect is incompatible outright
  (no `MAPPING-` prefix, `Source Layout` vs `Source File Layout`, different
  header dialect). Closing that round trip is a real integration task; do
  not assume the pipeline joins up.
- **The CAQH STTM contract is synthetic** — `extract-sttm` is flat-only, so
  CAQH (segmented) still cannot be extracted; the MIDS STTM contract
  predates the extractor (out-of-repo; no committed workbook reproduces it).
  The record-type discriminator (first field, H/D/T, `config.segments`) is
  an assumption pending the source dictionary; CAQH's standard target is
  empty in the FRD (stage-only, load AS-IS) — confirm with the source team.
- `FrdContract._provenance.ambiguities` accepts plain strings (older
  contracts) AND the structured `GatedAmbiguity` objects current
  frd-to-sttm output emits; absent context keys there are not drift.
- Layer-2 candidate **approval merge is deliberately v2**: the UI records
  approve/reject decisions (`ui/backend/state/decisions.json`, gitignored),
  but merging into generated code stays manual; decisions don't gate.
- `ui/backend/service.py::GenerationStore._generate_feed` mirrors
  `cli._generate_feed` step for step — keep them in sync if CLI
  orchestration changes. UI runs are always dry-run + skip-tests.
- Generated job JSON cluster shape/schedule is a config guess; only "Weekly
  Monday 8 PM" compiles to cron, MIDS ships unscheduled. The client's
  pipeline stack is unknown — output targets plain PySpark + Workflows,
  structured for a mechanical DLT port.
