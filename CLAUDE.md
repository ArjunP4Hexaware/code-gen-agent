# CodeGen / Data Engineer Agent — working notes

## Purpose & pipeline position

Generates production-shaped Databricks ingestion pipelines (PySpark + Delta
Lake) from approved machine-readable contracts — one FRD feed contract plus
one STTM mapping contract per feed. It is the **third agent** in the
five-agent AI-in-Engineering program at AmeriHealth Caritas: BRD→FRD →
FRD→STTM (produces the FRD feed contracts consumed here) → **CodeGen** →
Code Review (reviews what this repo emits; SQL Optimization is standalone).
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
src/codegen/        contracts/ (pydantic models, both dialects, frozen),
                    resolve/ (FRD⋈STTM join → ResolvedFeedSpec), extract/
                    (workbook→STTM extractor, see below), rules/ (rule
                    classifier), reasoning/ (Layer 2: providers, verbatim
                    grounding), emit/ (Jinja2 + notebook assembler), gate/
                    (preflight, tests, verdict), report/, templates/, cli.py, config.py
tests/              58 generator tests, offline, no Spark needed
config/config.yaml  every knob — contract pairs, extractor layout, naming, masking, gate, job
fixtures/contracts/ 2 real FRD + MIDS STTM + SYNTHETIC CAQH STTM + CV/golden FRD + expected extract
fixtures/workbooks/ anonymized golden STTM workbook (extractor input; re-included past *.xlsx ignore)
docs/               DESIGN.md, WORKFLOW.md, EXTRACTOR_RECON.md, SEGMENTED_MODE_DESIGN.md, media/
ui/                 demo dashboard: FastAPI (8571) + Vite/React (5173); pip install -e ".[ui]", see ui/README.md
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
.venv/bin/python -m pytest -q          # 58 passed, no Spark, no network

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
  AmeriHealth agents program. The LLM provider is **mock by default**:
  `build_provider` selects the deterministic mock unless
  `ANTHROPIC_API_KEY` is set and dry-run is off — zero network otherwise.
  The live path (`reasoning/providers/anthropic_provider.py`) is
  implemented and unit-tested (stubbed SDK) but has not yet been validated
  with a real billed call — first live E2E is upcoming. Live LLM use is
  confined to Layer 2 (reasoning/review); code generation itself is
  deterministic Jinja2 by design. Model name lives in config
  (`reasoning.model`).
- Pydantic v2 models are `frozen=True` + `extra="forbid"`; missing is
  `None`, never a default. PHI masked to last-4 at every egress.

## Branching model

All development on `staging`; `main` is the deployment branch — `staging`
merges to `main` only after testing.

## Fixtures & data rules

Offline fixtures only — tests and dry-run generation must pass with zero
credentials and zero network. No real client data beyond the approved
contract/workbook fixtures; new fixture material must be anonymized first.
Generated output is byte-stable by design — no timestamps or randomness in
generated files; keep it that way (extract-sttm: inject `--generated-date`).

## Known gaps / cautions

- **There is no live-credential `.env` in this repo** (an earlier claim in
  this file that one existed was stale).
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
