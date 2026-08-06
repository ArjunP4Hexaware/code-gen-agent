# CodeGen / Data Engineer Agent — working notes

## Purpose & pipeline position

Generates production-shaped Databricks ingestion pipelines (PySpark + Delta
Lake) from approved machine-readable contracts — one FRD feed contract plus
one STTM mapping contract per feed. It is the **third agent** in the
five-agent AI-in-Engineering program at AmeriHealth Caritas: BRD→FRD →
FRD→STTM → **CodeGen** → Code Review (SQL Optimization is standalone).
Upstream, the FRD→STTM agent produces the FRD feed contracts this repo
consumes; downstream, the Code Review Agent reviews what this repo emits.
Two-layer trust rule (never violate): **Layer 1** is deterministic Jinja2 —
everything derivable from the contracts, byte-stable, every file stamped
with a provenance banner carrying the contract names + sha256. **Layer 2**
is the LLM, mock by default — ONLY free-text `validation_rules` the
deterministic compiler classifies as `unmapped` reach a model, and its
output lands in a review artifact (`out/<feed>/candidates/candidates.json`),
never in generated modules; every citation must appear verbatim in the
contract text. Each feed ends in a computed gate verdict:
PASS / PASS_WITH_FLAGS / FAIL (semantics in `docs/WORKFLOW.md`).

## Repo layout

```
src/codegen/        contracts/ (pydantic models, both dialects, frozen),
                    resolve/ (FRD⋈STTM join → ResolvedFeedSpec), rules/
                    (deterministic rule classifier), reasoning/ (Layer 2:
                    providers, verbatim grounding), emit/ (Jinja2 emitter +
                    single-notebook assembler), gate/ (preflight, test runner,
                    verdict), report/, templates/, cli.py, config.py
tests/              36 generator tests, offline, no Spark needed
config/config.yaml  every knob — contract pairs, naming, masking, gate, job
fixtures/contracts/ 2 real FRD contracts + MIDS STTM contract + SYNTHETIC CAQH STTM
docs/               DESIGN.md (rationale), WORKFLOW.md (contracts → PR flow), media/
ui/                 demo dashboard: FastAPI backend (8571) + Vite/React frontend
                    (5173); install via pip install -e ".[ui]" — see ui/README.md
```

## Setup / run / test

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"      # deps + pytest/ruff/pyspark, from pyproject

.venv/bin/python -m pytest -q          # 36 passed, no Spark, no network

# Generate everything from the fixture contracts (mock Layer 2, no network)
.venv/bin/python -m codegen.cli generate-all \
    --config config/config.yaml --dry-run --skip-tests
```

Expected with current fixtures: **all 4 feeds PASS_WITH_FLAGS** — every feed
has flagged/notification/unmapped rules; that is correct, honest behavior,
not a failure. Output lands in `out/<feed_slug>/` (module tree, DDL, tests,
job JSON, one assembled runnable `.ipynb`) with a markdown report per feed
in `reports/` — both gitignored. Running the *generated* Spark test suites
(drop `--skip-tests`) additionally needs a JVM: `JAVA_HOME` → Java 17, and
`PYSPARK_PYTHON` pointed at the venv interpreter. `ruff check src/ tests/`
must stay clean, and generated code must be ruff-clean against the same
rules (an `out/<feed>/ruff.toml` is emitted alongside).

## Config doctrine

- Every knob lives in `config/config.yaml` — contract pairs, naming
  suffixes, masking policy, segment discriminators, gate switches, job
  cluster shape. No numeric literals in generator logic; the loader is loud
  on typo'd top-level keys.
- No secrets in the repo, ever. Credentials only via environment / `.env`
  (gitignored; `.env.example` documents the names).
- The LLM provider is **mock by default**; `AnthropicProvider` activates
  only when `ANTHROPIC_API_KEY` is set, and `--dry-run` forces mock — no
  key ⇒ zero network. Model name lives in config (`reasoning.model`).
- Pydantic v2 models are `frozen=True` + `extra="forbid"`; missing is
  `None`, never a default. PHI is masked to last-4 at every
  log/report/error egress.

## Branching model

All development happens on `staging`. `main` is the deployment branch;
`staging` merges to `main` only after testing.

## Fixtures & data rules

Offline fixtures only — tests and dry-run generation must pass with zero
credentials and zero network. No real client data beyond the approved
contract fixtures enters this repo; any new fixture material must be
anonymized first. Generated output is byte-stable by design — no timestamps
or randomness in generated files; keep it that way.

## Known gaps / cautions

- **There is no live-credential `.env` in this repo.** (An earlier version
  of this file claimed one existed in the repo root — that claim was stale.)
- **The CAQH STTM contract is synthetic** — a clearly-labeled stand-in
  until the real workbook extract lands; swap the file in
  `config.contracts.pairs` and regenerate. The MIDS STTM mapping contract
  was produced out-of-repo (no committed workbook→contract extractor exists
  in the program yet). The CAQH record-type discriminator (first field,
  H/D/T, in `config.segments`) is an assumption pending the source
  dictionary, and CAQH's standard target is empty in the FRD (stage-only,
  load AS-IS) — confirm with the source team.
- Layer-2 candidate **approval merge is deliberately v2**: the UI records
  approve/reject decisions (`ui/backend/state/decisions.json`, gitignored)
  but merging an approved candidate into generated code stays manual, and
  decisions do not affect the gate verdict.
- `ui/backend/service.py::GenerationStore._generate_feed` mirrors
  `cli._generate_feed` step for step — keep them in sync if CLI
  orchestration changes. UI runs are always dry-run + skip-tests; the full
  Spark gate stays a CLI concern.
- Generated job JSON cluster shape/schedule is a config guess; only
  "Weekly Monday 8 PM" compiles to cron, MIDS ships unscheduled.
- The client's existing pipeline stack is unknown — output targets plain
  PySpark + Workflows, structured for a mechanical DLT port.
