# CodeGen / Data Engineer Agent

Generates production-shaped Databricks ingestion pipelines (PySpark +
Delta Lake) from approved machine-readable contracts — one FRD feed
contract plus one STTM mapping contract per feed. Third agent of five in
the AI-in-Engineering program at AmeriHealth Caritas: downstream of the
BRD→FRD/STTM agent (which produces the contracts), upstream of the Code
Review Agent (which reviews what this agent emits).

Design rationale: [`docs/DESIGN.md`](docs/DESIGN.md). Operating workflow:
[`docs/WORKFLOW.md`](docs/WORKFLOW.md). Demo UI + guided tour:
[`ui/README.md`](ui/README.md) —
[walkthrough GIF](docs/media/demo_mode_walkthrough.gif).

## The two-layer trust architecture

1. **Layer 1 — deterministic (Jinja2, no LLM).** Everything derivable from
   the contracts is compiled by code: schemas, DDL, readers, drift checks,
   masking, audit columns, recycle/reference logic, tests, job JSON.
   Byte-stable output; every file carries a provenance banner with the
   contract names and sha256.
2. **Layer 2 — LLM, mock by default.** Only free-text `validation_rules`
   the deterministic rule compiler classifies as `unmapped` reach a model.
   Its output lands in a **review artifact**
   (`out/<feed>/candidates/candidates.json`) — never in generated modules —
   and every citation must appear verbatim in the contract text or the
   candidate is marked ungrounded. Without `ANTHROPIC_API_KEY` (or with
   `--dry-run`) a deterministic mock runs and nothing touches the network.

Every generation ends in a computed three-state gate verdict per feed:
**PASS / PASS_WITH_FLAGS / FAIL** (see `docs/WORKFLOW.md` for semantics).

## Quick start

```bash
python -m venv .venv
.venv/Scripts/pip install -e .            # or: pip install -e ".[dev]" equivalents in pyproject
cp .env.example .env                      # optional; only needed for real creds

# generate everything from the fixture contracts (mock Layer 2, no network)
.venv/Scripts/python -m codegen.cli generate-all --config config/config.yaml --dry-run
```

Outputs land in `out/<feed_slug>/` with a markdown report per feed in
`reports/` (both gitignored). Alongside the module tree, each feed ships as
**one runnable Databricks notebook** — `out/<feed_slug>/<feed_slug>.ipynb`,
assembled deterministically from the rendered modules (DDL → pipeline modules
in dependency order → job entrypoint; each cell self-registers as
`pipeline.<module>` so the code runs unmodified). The module files remain the
canonical, tested source.

Running the generated Spark tests locally needs a JVM: set `JAVA_HOME`
(Java 17), on Windows also `HADOOP_HOME` (winutils), and `PYSPARK_PYTHON`
to the venv interpreter. Skip them with `--skip-tests` or
`gate.run_generated_tests: false` in config.

## Repository layout

| Path | What |
|---|---|
| `src/codegen/contracts/` | pydantic models for both contract dialects (frozen, `extra="forbid"`) |
| `src/codegen/resolve/` | FRD⋈STTM join → `ResolvedFeedSpec`; disagreements raise `ContractMismatchError` |
| `src/codegen/rules/` | deterministic classifier for free-text validation rules |
| `src/codegen/reasoning/` | Layer 2: context packs, providers (mock/Anthropic), verbatim grounding check |
| `src/codegen/emit/` | render context + Jinja2 emitter + single-notebook assembler (`notebook.py`) |
| `src/codegen/templates/` | the full template inventory (pipeline, DDL, job, tests, fixtures) |
| `src/codegen/gate/` | preflight (ruff, debug/secrets scan, test-per-module), generated-test runner, verdict |
| `src/codegen/report/` | per-feed generation report |
| `config/config.yaml` | every knob; no numeric literals live in generator logic |
| `fixtures/contracts/` | real MIDS + CAQH FRD contracts; **synthetic** CAQH STTM stand-in |
| `tests/` | generator's own test suite (no Spark needed) |

## Development

```bash
.venv/Scripts/ruff check src/ tests/
.venv/Scripts/python -m pytest tests/ -q
```

Conventions: Python 3.11; pydantic v2 frozen models; missing is `None`,
never a default; credentials only via `.env` (gitignored); PHI masked to
last-4 at every log/report/error egress; generated code must be ruff-clean
against the same rules as the generator (`out/<feed>/ruff.toml` is
emitted alongside).
