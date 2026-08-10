# code-gen-agent — deep dive

A worked-example tour of `src/codegen/` and the config doctrine, referenced
from `SKILL.md`.

## Package layout

| Path | Role |
|---|---|
| `src/codegen/contracts/` | Pydantic v2 frozen models for both contract dialects (`extra="forbid"`); missing fields are `None`, never a default. |
| `src/codegen/resolve/` | FRD ⋈ STTM join producing `ResolvedFeedSpec`; disagreements raise `ContractMismatchError`. The join invariant is `feed_id = normalize_feed_name(FRD.feed_name)`. |
| `src/codegen/rules/` | Deterministic classifier for free-text `validation_rules` — anything unclassified becomes `unmapped` and is what (and *only* what) Layer 2 sees. |
| `src/codegen/reasoning/` | Layer 2: context packs, provider abstraction, verbatim grounding check. `providers/anthropic_provider.py` is the live path (unit-tested with a stubbed SDK, not yet billed E2E). `build_provider` selects the deterministic mock unless `ANTHROPIC_API_KEY` is set AND `--dry-run` is off. |
| `src/codegen/extract/` | Workbook → STTM-mapping-contract extractor. Flat dialect only; segmented workbook = `SegmentedWorkbookError`. Header resolution is fuzzy + config-driven (`extractor:` block). |
| `src/codegen/emit/` | Render context + Jinja2 emitter + `notebook.py` (single-notebook assembler that stitches rendered modules into one runnable `.ipynb`). |
| `src/codegen/templates/` | Full Jinja inventory: pipeline modules, DDL, job JSON, generated tests, fixture data. |
| `src/codegen/gate/` | Preflight (ruff, debug-pattern scan, secrets scan, test-per-module), the generated-test runner, and verdict computation (`PASS` / `PASS_WITH_FLAGS` / `FAIL`). |
| `src/codegen/report/` | Per-feed generation report writer (`reports/<feed_slug>.md`). |
| `src/codegen/cli.py` | Entry point: `generate`, `generate-all`, `extract-sttm`. |
| `src/codegen/config.py` | Loud loader over `config/config.yaml`. |

## Config doctrine

- Every knob lives in `config/config.yaml` — contract pairs, extractor
  layout, naming, masking, segment discriminators, gate thresholds, job
  cluster shape.
- The loader raises on typo'd keys; do not silently ignore unknowns.
- No numeric literals in generator logic. If you find yourself typing
  `if x > 3:` in `emit/` or `gate/`, that `3` belongs in config.
- No secrets in the repo. Credentials only via `.env` (gitignored;
  `.env.example` documents the names).
- `reasoning.model` in config names the Anthropic model. Do not re-add a
  temperature knob — `claude-opus-4-8` rejects sampling parameters (400
  from the API).

## Byte-stability rules

- No `datetime.now()`, no `uuid`, no `random` in the emit path. Ever.
- `extract-sttm` accepts `--generated-date` for the same reason.
- Tests byte-compare the CV/golden extractor output against
  `fixtures/contracts/sttm_mapping_contracts_cv_golden.json`.
- Provenance banners include contract names + sha256, not build times.

## UI ↔ CLI parity

`ui/backend/service.py::GenerationStore._generate_feed` mirrors
`cli._generate_feed` step for step. Any change to CLI orchestration must
land in both. UI runs are always dry-run + skip-tests; only the Run modes
"Live" button reaches the real Anthropic API, and only after a confirmation
dialog. UI-created live output is isolated to `out/demo_<timestamp>/` so it
cannot touch the tracked replay fixtures or the default output tree.

## Fixtures

- `fixtures/contracts/` — real MIDS + CAQH FRD contracts, **synthetic**
  CAQH STTM stand-in (segmented is not extractor-supported yet), CV/golden
  FRD + expected extractor output.
- `fixtures/workbooks/` — anonymized golden STTM workbook (extractor
  input; `*.xlsx` is otherwise gitignored).
- `fixtures/replay/<run_id>/` — full committed real-model runs the demo
  UI's Replay mode loads byte-for-byte.

## Test posture

80 tests total, all offline, no Spark needed. 15 demo-UI tests skip
cleanly if `[ui]` extra is not installed. `ruff check src/ tests/` must
stay clean; generated code is held to the same rules
(`out/<feed>/ruff.toml` is emitted).

## Branching

`staging` for all development; `main` is deploy-only. `staging` merges
into `main` only after testing.
