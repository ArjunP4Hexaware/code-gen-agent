# CodeGen / Data Engineer Agent — design

Generates production-shaped Databricks ingestion pipelines (PySpark + Delta)
from approved machine-readable contracts. Third agent in the five-agent
program (AI in Engineering at AmeriHealth Caritas); sits downstream of the
BRD→FRD / STTM agent (which produces the contracts this agent consumes) and
upstream of the Code Review Agent (which reviews what this agent emits).

Two sibling repos define the house style and are vendored read-only under
`reference/` (gitignored):

- `reference/source-to-stage` — a hand-written POC bronze→silver pipeline.
  **It is the target shape of the code this agent generates**: contract-first,
  no hardcoded column names or thresholds, audit/recycle/drift/idempotency
  semantics, PHI masked to last-4 at every egress, and a module→Databricks
  mapping table (its `AGENTS.md` §2) that this agent's output follows.
- `reference/code-review-agent` — the layered trust architecture
  (deterministic first, LLM last, grounding-checked, three-state gate) and
  the review this agent's output must pass.

---

## 1. Inputs: the frozen spec

Per feed, generation consumes **two** artifacts:

1. **FRD feed contract** (`*.contract.json`) — feed-level facts: file name
   patterns, format and delimiter, `record_segments` (the CAQH dialect is
   Header/Detail/Trailer), stage/standard targets and load strategies,
   free-text `validation_rules`, `recycle_rule`, PHI notes, SLAs.
2. **STTM mapping contract** (`sttm_mapping_contracts.json` shape) —
   column-level facts: `fields[]` with source/stage/standard names, dtypes,
   nullable/phi/mandatory flags, `audit_columns`, `load_rules` (including a
   structured recycle spec).

Two client dialects exist in `fixtures/contracts/`:

| Dialect | FRD contract | Feeds | Shape |
|---|---|---|---|
| MIDS (Socially Determined) | `FRD_Medicare Expansion-MIDS…contract.json` | 3 flat CSV/PSV feeds | one stage table per feed |
| CAQH (Payment Integrity TPL) | `FRD_STG_STD_PaymentIntegrity…contract.json` | 1 feed, 18 file patterns | pipe-delimited Header/Detail/Trailer → 3 stage tables + a recycle table |

A complete FRD+STTM pair exists for MIDS. No CAQH STTM mapping contract is
present, so the repo ships a **clearly-labeled SYNTHETIC one**
(`fixtures/contracts/sttm_mapping_contracts_caqh.SYNTHETIC.json`, marked
`"synthetic": true` in the payload) — a plausible subset of columns
consistent with the FRD contract's stage tables and segments — so the CAQH
dialect is exercised end to end. The real contract drops in later with no
code change.

### STTM dialect extension for segmented feeds

The MIDS STTM shape maps one feed → one stage table. CAQH needs
per-segment mapping, so `fields[]` entries may carry two optional keys:
`record_segment` (`Header` | `Detail` | `Trailer`) and `stage_table` (which
of the feed's stage tables the field lands in). Absent on flat feeds;
mandatory (validated loudly) on any feed whose FRD contract declares
`record_segments`. This is the only extension to the frozen STTM shape, and
it is backward compatible: the real MIDS contract parses unchanged.

---

## 2. Contract models and the resolver

`src/codegen/contracts/` defines pydantic v2 models for both artifacts,
house style throughout: `frozen=True`, `extra="forbid"` (unknown keys fail
loudly, never dropped), missing is `None` — never a default that could be
mistaken for a real value.

- `frd.py` — `FrdContract` → `FrdFeed` → `TargetSpec` etc. Mirrors the
  FRD-generator output byte for byte, including `_provenance` (aliased) and
  the three-state `status`.
- `sttm.py` — `SttmContract` → `SttmFeed` → `SttmField`, `LoadRules`,
  `RecycleSpec`, `AuditColumn`. In-model validation: `field_count ==
  len(fields)`, `not_null/mandatory/phi_columns` must name real fields,
  `recycle.applies_to` must be a real field, segment fields present when
  the dialect requires them.
- `resolved.py` — `ResolvedFeedSpec`: the single flattened object every
  template consumes. Nothing downstream ever touches the raw contracts.

`src/codegen/resolve/` joins one FRD feed with one STTM feed into a
`ResolvedFeedSpec`. **Every mismatch is a loud error** (a
`ContractMismatchError` naming the feed, the field, and both values):

- **Join key**: normalized feed name (lowercase, non-alphanumeric → `_`), so
  FRD `"CAQH TPL Inbound Files"` matches STTM `caqh_tpl_inbound_files`. An
  explicit `feed_aliases` map in `config.yaml` overrides normalization when
  the names genuinely differ. A feed present in one contract but missing
  from the other is a resolution FAIL, not a skip.
- **Delimiter**: prefer the STTM's explicit delimiter; else infer from
  format (`csv`→`,`, `psv`→`|`); `txt` requires an explicit delimiter in at
  least one contract. Two explicit-but-different values → error.
- **Recycle**: FRD `recycle_rule` free text and STTM structured
  `recycle.recycle_window_days` must agree on the window when both state
  one (the FRD text is parsed only for the `N days` figure; everything
  else executes from the structured STTM spec).
- **Targets**: stage/standard schema+table in the STTM must appear in the
  FRD's target lists (CAQH: every `stage_table` named by a field must be
  one of the FRD's stage tables).
- **Natural key**: derived as `load_rules.not_null_columns` (never
  hardcoded), used with `SRC_FILE_NAME` as the MERGE/idempotency key —
  same rule as source-to-stage.

---

## 3. Two-layer generation — the trust rule

Same principle as the Code Review Agent's five layers, collapsed to two:
**everything derivable from the contract is deterministic; the LLM touches
only what determinism cannot, and its output never lands in generated
modules directly.**

### Layer 1 — deterministic (Jinja2, no LLM)

Byte-stable: identical inputs produce identical bytes (templates are
rendered with sorted, fully-resolved context; no timestamps in code —
provenance banners carry the contract name + content hash, not a clock).
Emits, per feed, into `out/<feed_id>/`:

```
out/<feed_id>/
  ddl/            stage/standard/errors/recycle/processed-files DDL (Delta / Unity Catalog)
  pipeline/       reader, [segments], drift, mapping, audit, rejects,
                  [recycle, reference], writer (MERGE), masking, dq,
                  run_report, orchestrator   — mirrors source-to-stage/pipeline/
  job/            Databricks Workflows job JSON + thin notebook entrypoint
  tests/          pytest suite FOR THE GENERATED CODE (local SparkSession + delta-spark)
  tools/          make_fixtures.py — synthetic data from the contract's sample_value
  README.md       what was generated, from which contracts, verdict summary
```

`[bracketed]` modules are emitted only when the spec requires them
(segments for segmented feeds, recycle/reference for recycle feeds).

Semantics generated in (all from source-to-stage, mapped to Databricks per
its AGENTS.md §2 table):

- Stage tables all-String + typed audit columns; standard tables typed.
- Schema drift: missing column → fail the file; extra column → quarantine
  the column, load the rest.
- Audit columns pipeline-populated: `LOB` (job parameter), `SRC_FILE_NAME`,
  `REC_CREATION_TIME` / `REC_UPDATED_TIME`; injectable `run_ts` so recycle
  aging and backfills are deterministic and testable.
- Not-null enforcement → rejects to an errors table, PHI keys masked.
- Recycle: reference lookup (Facets `SBSB_ID`/`GRGR_CK` stand-in,
  configurable), no-match → recycle table, retried each run, expired after
  the configured window (7 days MIDS, 15 days CAQH — from the contract,
  never a literal in logic).
- Idempotent `MERGE INTO` keyed on `SRC_FILE_NAME` + natural key;
  `REC_CREATION_TIME` preserved across re-ingest.
- PHI masked to last-4 at every log/report/error egress; raw values only
  inside the data tables.
- CAQH: pipe-delimited Header/Detail/Trailer splitting; trailer count
  reconciled against detail rows in DQ.

### Layer 2 — LLM (Claude behind a provider abstraction, mock default)

Input: only the free-text `validation_rules` the deterministic **rule
compiler** (`src/codegen/rules/`) cannot map to a known template. The
compiler first classifies each rule by pattern:

| Class | Example (from fixtures) | Disposition |
|---|---|---|
| `mappable` | "If the ZIP_CODE column is NULL, reject…" | compiled deterministically into the generated modules |
| `orchestration-config` | "Duplicate file name check shall be turned off…" | becomes a knob in the generated job/config, documented |
| `notification` | "Email notification will be sent post job completion." | listed in the report; job JSON gets `email_notifications` |
| `out-of-scope` | "Files should be masked prior to Dev & QA testing." | listed in the report, no code |

Only rules the compiler cannot classify go to the LLM, which returns, per
rule: a classification, a code candidate, a rationale, and **the exact
contract text it grounds on**. A grounding check (same pattern as the Code
Review Agent's `reasoning/grounding.py` and STTM's grounding audit) rejects
any candidate citing text not present verbatim in the contract. Surviving
candidates land in a **review artifact** — `out/<feed_id>/candidates/`
(JSON candidates + markdown rationale) — awaiting engineer approval. LLM
output NEVER lands in generated modules directly.

Providers: `MockProvider` (default — deterministic, offline, used by every
test and `--dry-run`) and `AnthropicProvider` (activates only when
`ANTHROPIC_API_KEY` is set). No key ⇒ no network call, no spend.

---

## 4. Gate — PASS / PASS_WITH_FLAGS / FAIL

House semantics, computed in code, printed per run and written to a
per-run markdown generation report in `reports/`:

- **PASS** — every validation rule compiled deterministically or explicitly
  approved; generated tests pass; ruff clean over generated code.
- **PASS_WITH_FLAGS** — LLM candidates pending approval, or rules classified
  `notification` / `out-of-scope` (surfaced, not silently dropped).
- **FAIL** — contract validation errors, resolver mismatches, template
  gaps (a spec feature no template covers), or generated tests failing.

Ambiguity degrades the verdict; it never silently promotes to PASS.

## 5. Acceptance loop with the Code Review Agent

Generated output must pass `reference/code-review-agent`'s review. The gate
pre-flights this locally before declaring PASS:

- `ruff` over `out/<feed_id>/` (same linter that agent's ruff adapter runs);
- a replica of its structural checks: no debug statements, no secrets in
  output, a test file per generated source module.

Intended flow (documented in `docs/WORKFLOW.md` once built): `codegen
generate` → engineer inspects `out/<feed_id>/` + candidates → opens PR →
Code Review Agent reviews → merge.

## 6. Configuration, CLI, engineering rules

- Python 3.11+, pydantic v2, jinja2; pyspark + delta-spark **dev/test
  only** (generated-code tests run locally; generation itself never needs
  Spark); ruff, pytest; pip + venv; Windows 11 host.
- `config/config.yaml` holds every knob: recycle window default, output
  dir, model name, masking policy (last-4), linter toggles, feed aliases.
  **No numeric literals in logic** — the Code Review Agent's convention.
  Credentials only via `.env` (see `.env.example`).
- CLI:
  `codegen generate --feed <id> --frd-contract <path> --sttm-contract <path> [--dry-run]`
  and `codegen generate-all` (all feeds resolvable from the fixture
  contracts). `--dry-run` = mock provider + fixtures only, zero network.

Repo layout:

```
src/codegen/
  contracts/    pydantic models: frd.py, sttm.py, resolved.py
  resolve/      FRD⋈STTM join → ResolvedFeedSpec, mismatch errors
  templates/    Jinja2 templates (inventory below)
  emit/         render context building, file writing, byte-stable ordering
  rules/        deterministic rule compiler + classifier
  reasoning/    Layer 2: context pack, schema, grounding, providers/
  gate/         verdict computation + code-review pre-flight
  report/       per-run markdown generation report
fixtures/       contracts + (later) golden outputs
out/            generated pipelines (gitignored)
tests/          tests for the GENERATOR (contracts, resolve, rules, gate, e2e dry-run)
docs/           DESIGN.md (this file), WORKFLOW.md
```

---

## 7. Template inventory (Layer 1)

All under `src/codegen/templates/`. One template = one responsibility.

**Shared**

| Template | Responsibility |
|---|---|
| `_macros.sql.j2` | SQL macros: qualified table names, column-list and dtype rendering, identifier quoting |
| `_macros.py.j2` | Python macros: generated-file provenance banner (contract name + content hash), shared docstring header |

**DDL** (→ `out/<feed_id>/ddl/`)

| Template | Responsibility |
|---|---|
| `ddl/stage_table.sql.j2` | Stage Delta table: all source columns String + typed audit columns, Unity Catalog syntax |
| `ddl/standard_table.sql.j2` | Standard-layer typed Delta table (dtypes from `standard_datatype`) |
| `ddl/errors_table.sql.j2` | Not-null reject/errors side table (masked-key payload columns) |
| `ddl/recycle_table.sql.j2` | Recycle side table with recycle flag, first-seen timestamp, expiry metadata — recycle feeds only |
| `ddl/processed_files_table.sql.j2` | Ops table recording ingested files for idempotency and run audit |

**PySpark modules** (→ `out/<feed_id>/pipeline/`)

| Template | Responsibility |
|---|---|
| `pyspark/reader.py.j2` | File→DataFrame: name-pattern match, delimiter, all-String schema, header handling |
| `pyspark/segments.py.j2` | Header/Detail/Trailer splitting for segmented feeds (record-type dispatch to per-segment DataFrames) — CAQH only |
| `pyspark/drift.py.j2` | Schema-drift check: missing column → fail, extra column → quarantine |
| `pyspark/mapping.py.j2` | Source→stage 1:1 column mapping from the contract |
| `pyspark/audit.py.j2` | Audit column population (LOB, SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME) with injectable `run_ts` |
| `pyspark/rejects.py.j2` | Not-null enforcement: rejects → errors table, PHI keys masked |
| `pyspark/recycle.py.j2` | Recycle match / no-match / retry / expiry against the reference lookup, configurable window — recycle feeds only |
| `pyspark/reference.py.j2` | Member reference lookup (Facets `SBSB_ID` / `GRGR_CK` stand-in), configurable id/group columns — recycle feeds only |
| `pyspark/writer.py.j2` | Idempotent `MERGE INTO` keyed on SRC_FILE_NAME + natural key; `REC_CREATION_TIME` preserved |
| `pyspark/masking.py.j2` | PHI last-4 masking helpers used by every log/report/error egress |
| `pyspark/dq.py.j2` | Row reconciliation, not-null verification, duplicate-key check (+ trailer-count reconciliation on segmented feeds) |
| `pyspark/run_report.py.j2` | Per-run markdown ingest report, PHI masked |
| `pyspark/orchestrator.py.j2` | Land → load → dq → report sequence for one file; structured result objects |

**Job** (→ `out/<feed_id>/job/`)

| Template | Responsibility |
|---|---|
| `job/workflow.json.j2` | Databricks Workflows job JSON per feed (tasks, parameters, schedule from SLA text, notification settings from classified rules) |
| `job/notebook_entrypoint.py.j2` | Thin notebook: widgets (lob, run_ts, file path) → orchestrator call, nothing else |

**Generated tests** (→ `out/<feed_id>/tests/`)

| Template | Responsibility |
|---|---|
| `tests/conftest.py.j2` | Local SparkSession + delta-spark + tmp-dir warehouse fixtures |
| `tests/test_drift.py.j2` | Missing column → fail; extra column → quarantine, rows still load |
| `tests/test_null_rejection.py.j2` | Null natural-key row → errors table; PHI key arrives masked |
| `tests/test_recycle.py.j2` | Recycle match / no-match / retry / window expiry — recycle feeds only |
| `tests/test_audit_idempotency.py.j2` | Re-ingest same file: no duplicates, `REC_CREATION_TIME` preserved, `REC_UPDATED_TIME` advanced |
| `tests/test_segments.py.j2` | Header/Detail/Trailer split correctness + trailer count reconciliation — segmented feeds only |

**Fixtures & docs** (→ `out/<feed_id>/tools/`, `out/<feed_id>/`)

| Template | Responsibility |
|---|---|
| `fixtures/make_fixtures.py.j2` | Synthetic happy-path + edge-case files from the contract's `sample_value` data (null key, drift, unknown member, embedded delimiter) |
| `readme.md.j2` | Per-feed README: what was generated, from which contracts (names + hashes), module map, verdict summary |

**Assembled artifact** (not a template — built in code by
`emit/notebook.py` from the rendered sources above)

| Artifact | Responsibility |
|---|---|
| `<feed_slug>.ipynb` | The whole pipeline as one runnable Databricks notebook: provenance intro → `sys.modules` bootstrap → DDL → each pipeline module verbatim (self-registering as `pipeline.<module>`) → job entrypoint. Deterministic and byte-stable; AST-level namespace checks raise `TemplateGapError` on any cross-module name collision. The module files remain the canonical, tested source. |

---

## 8. Open questions

- **The client's existing pipeline stack is unknown.** Output targets plain
  PySpark + Databricks Workflows, structured module-for-module so a DLT
  port is mechanical per the portability table in
  `reference/source-to-stage/AGENTS.md` §2 (drift → Auto Loader
  expectations, dq → DLT expectations, orchestrator → Workflow DAG).
- **The real CAQH STTM mapping contract is pending.** The synthetic one is
  a labeled stand-in; column lists and segment assignments are plausible,
  not authoritative. Swap the file in and re-run `generate` when it lands.
- **CAQH standard target is empty in the FRD** (`tables: []`) — the feed is
  stage-only ("load AS-IS", exposed to the on-prem TPL application). v1
  generates no standard DDL for CAQH; confirm with the source team.
- **Where approved LLM candidates get merged** — v1 stops at the review
  artifact; the mechanism that promotes an approved candidate into the
  generated module (regenerate with an approvals file? patch?) is a v2
  decision, deliberately unbuilt until the review artifact format has been
  seen by an engineer.
- **Schedule fidelity in job JSON** — FRD SLA text ("Weekly Monday 8 PM",
  "between 11-15th of every month") is compiled to cron where the phrase is
  unambiguous; otherwise the job ships unscheduled with the SLA text in a
  comment field and a PASS_WITH_FLAGS note.
