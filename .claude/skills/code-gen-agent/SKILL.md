---
name: code-gen-agent
description: Read this when (a) designing an agent — for any client, domain, or artifact type — that must generate code, transformations, or configuration from an already-approved structured specification (an approved mapping document, schema contract, API spec, control matrix, config manifest, etc.) rather than from free-form natural-language prompting, where correctness has to be provable, output must be byte-stable, and a shared verdict vocabulary needs to survive across a multi-agent pipeline; OR (b) working in or asking about the `code-gen-agent` repository itself — the CodeGen / Data Engineer Agent that emits Databricks PySpark + Delta ingestion pipelines from approved FRD + STTM contracts for the AmeriHealth Caritas program (questions about the two-layer trust architecture, `generate-all`, `extract-sttm`, PASS/PASS_WITH_FLAGS/FAIL verdicts, the Run modes demo UI, or the live/replay fixtures under `fixtures/replay/`). Covers the reusable pattern (Part B) as well as the concrete implementation (Part A).
---

# code-gen-agent — implementation + reusable pattern

Two parts. **Part A** is the concrete agent in this repo. **Part B** abstracts
the design so another team can lift it into an unrelated project.

---

## Part A — This agent, concretely

### Position in the program

Third of five agents in the AmeriHealth Caritas AI-in-Engineering program:

```
BRD→FRD  →  FRD→STTM  →  CodeGen (this repo)  →  Code Review  →  SQL Optimization
```

Upstream agents emit the machine-readable contracts this one consumes.
The Code Review agent reviews what this agent generates. SQL Optimization
is standalone.

### Input

**Approved, machine-readable contracts** — one FRD feed contract plus one
STTM mapping contract per feed, both pydantic v2 frozen models (`extra="forbid"`).
The upstream FRD→STTM agent produces them. When only a client-authored Excel
workbook exists, `extract-sttm` (deterministic, no LLM, no network) converts
it into the STTM mapping contract; it requires the paired FRD as its second
input because the resolver's join invariant (`feed_id = normalize_feed_name(FRD feed_name)`)
and format/delimiter/standard-target facts live on the FRD side.

### Output (per feed, into `out/<feed_slug>/`)

- PySpark pipeline modules (schema, reader, drift, masking, audit, recycle, load)
- Delta DDL
- Generated pytest suite (offline; no Spark needed to render, JVM needed to run)
- Databricks job JSON
- **One assembled runnable notebook** — `<feed_slug>.ipynb` — deterministically
  stitched from the rendered modules; each cell self-registers as
  `pipeline.<module>` so the notebook runs unmodified. The module files stay
  canonical.
- A generation report in `reports/<feed_slug>.md`
- A Layer-2 review artifact `out/<feed>/candidates/candidates.json` (never
  merged into generated code — that is a manual step by design)
- A `ruff.toml` so generated code passes the same lint rules as the generator

Every emitted file carries a provenance banner: contract names + sha256.
Output is byte-stable (no timestamps, no randomness — `extract-sttm` accepts
`--generated-date` for the same reason).

### The two-layer trust architecture

1. **Layer 1 — deterministic (Jinja2, no LLM).** Everything derivable from
   the contracts. Byte-stable.
2. **Layer 2 — LLM, mock by default.** Only free-text `validation_rules`
   the deterministic rule compiler tags `unmapped` reach a model.
   `build_provider` picks the mock unless `ANTHROPIC_API_KEY` is set AND
   dry-run is off — zero network otherwise. Anthropic is the sole model
   vendor across the program (`reasoning.model` in config). Every model
   citation must appear verbatim in the contract text or the candidate is
   flagged ungrounded. `claude-opus-4-8` rejects sampling parameters, so
   there is no temperature knob and live output is inherently non-deterministic
   across runs — do not re-add one.

### Verdict vocabulary (per feed, computed by the gate)

- **PASS** — all preflight checks green, all rules classified, no flagged
  candidates
- **PASS_WITH_FLAGS** — code is clean but something needs a human
  (unmapped rules with pending candidates, generated tests skipped, etc.).
  The honest middle state; not a failure.
- **FAIL** — preflight failed, ruff dirty, contract mismatch, or grounding
  rejected

Current fixture state: all four feeds land at **PASS_WITH_FLAGS**
(intentional; each feed has flagged/notification/unmapped rules).

### Demo UI + replay fixtures

`ui/` is a FastAPI (8571) + Vite/React (5173) dashboard for the client demo.
Two run modes:

- **Live** — real Anthropic call, ~3 billed calls, ≈ $0.10, ~20s;
  confirmation dialog required; output isolated to `out/demo_<timestamp>/`
- **Replay** — loads a tracked fixture from `fixtures/replay/<run_id>/`
  byte-for-byte; zero API calls; works offline on a fresh clone

Replay layout (each fixture is a full committed live run):

```
fixtures/replay/<run_id>/
  README.md
  call_log.json                         # per-call model/tokens/latency/stop reason
  <feed_slug>/candidates.json           # Layer-2 review artifact
  <feed_slug>/report.md                 # generation report with verdict
```

Ships today: `live_e2e_20260807/` with three CV feeds, all PASS_WITH_FLAGS.

### Key docs — read these before making non-trivial changes

- [`README.md`](../../../README.md) — quick start, two-layer architecture,
  `extract-sttm` usage, repo layout table
- [`CLAUDE.md`](../../../CLAUDE.md) — working conventions: config doctrine,
  branching (staging→main), fixture rules, known gaps, extractor invariants
- [`docs/DEMO_RUNBOOK.md`](../../../docs/DEMO_RUNBOOK.md) — client demo
  choreography, contingency, safety rails, and the 2026-08-07 rehearsal
  findings
- [`docs/DESIGN.md`](../../../docs/DESIGN.md) and
  [`docs/WORKFLOW.md`](../../../docs/WORKFLOW.md) — design rationale and
  the gate verdict semantics
- [`app.yaml`](../../../app.yaml) — Databricks Apps manifest (see gap #1
  below)

Deeper design references — split out to keep this file short:

- [`references/deep-dive.md`](references/deep-dive.md) — file-level tour
  of `src/codegen/` and the config-doctrine rules
- [`references/reusable-checklist.md`](references/reusable-checklist.md) —
  Part B expanded as a build checklist for a new project

### Known open items (do not present as done)

1. **First live E2E on an actual Databricks Apps deployment is still
   pending.** The Anthropic provider path is unit-tested with a stubbed
   SDK but has not been validated against a real workspace. The UI polls
   short intervals rather than streaming to minimize the untested-proxy
   surface — see `app.yaml`.
2. **Segmented (Header/Detail/Trailer) STTM workbooks are out of extractor
   scope.** `extract-sttm` is flat-only and raises `SegmentedWorkbookError`
   otherwise. The CAQH feed ships with a **synthetic** stand-in STTM
   contract until the source dictionary lands and the standard-target
   decision is made.
3. **Layer-2 approval-to-merge is v2.** The UI records approve/reject
   decisions to `ui/backend/state/decisions.json`, but merging into
   generated code stays a manual engineer step; decisions do not gate.
4. **No live-credential `.env` is committed** (there never was one; an
   earlier claim was stale).

### How to run

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"                 # add ",live,ui" for demo UI + Anthropic SDK
.venv/bin/python -m pytest -q                      # 80 tests, offline
.venv/bin/python -m codegen.cli generate-all \
    --config config/config.yaml --dry-run --skip-tests
```

Generated Spark tests need `JAVA_HOME` (Java 17) + `PYSPARK_PYTHON` set to
the venv interpreter. Confirm you are on `staging` before edits — `main`
is deploy-only.

---

## Part B — The reusable pattern

Lift this section when building a different agent that must generate
code, transformations, or configuration from an *approved* structured
artifact. The AmeriHealth specifics fall away; the shape survives.

### When this pattern applies

You are building an agent when **all** of these hold:

- The upstream artifact is **approved** — signed off by a human, versioned,
  and machine-readable (JSON/YAML/protobuf/OpenAPI/CSV/xlsx-with-schema).
  Not a free-form user prompt.
- The output is **executable** (code, SQL, IaC, config) — correctness is
  provable by lint/type/test, not by "reads well."
- The output feeds a **downstream reviewer or agent** — so the emitter's
  contract with that reviewer is stable.
- Regenerating the same input must produce the same bytes; ambiguity or
  free-text corners must be surfaced, not silently guessed.

If any of these are missing (input is free-form, output is prose, no
downstream contract), reach for a different pattern.

### The essentials

Skip any of them and the pattern breaks.

1. **Approved structured input is the source of truth. [essential]** The agent's job
   is not to interpret intent — it is to compile a signed-off artifact
   into runnable code. If the artifact is wrong, the agent should faithfully
   emit the wrong code and let the reviewer catch it, not "improve" it.
2. **Two layers, LLM in a bounded corner. [essential]** Layer 1 is a deterministic
   compiler over everything the spec pins down. Layer 2 is only where the
   spec has genuine free text the compiler cannot classify. Every fact the
   spec *could* express in structure must live in Layer 1.
3. **Layer 2 output is a review artifact, not generated code. [essential]** A file the
   engineer reads and merges by hand. The agent proposes; a human confirms.
   Even an approval does not self-merge. This preserves the audit line.
4. **Verbatim grounding on every model claim. [essential]** If Layer 2 cites the spec,
   the citation must be found literally in the source. No paraphrasing,
   no invented references. Failed grounding rejects the candidate.
5. **Byte-stable output. [essential]** No timestamps, no randomness, no clock reads in
   the emitter. Inject any needed dates. Same input, same bytes — every
   time. This is what makes diffs reviewable and CI trustworthy.
6. **Provenance banner in every emitted file. [essential]** Input artifact names +
   content hashes. A reader of the output alone can reconstruct which
   version of the spec produced it.
7. **A shared verdict vocabulary across the pipeline. [essential]** A fixed enum —
   e.g. `PASS / PASS_WITH_FLAGS / FAIL` — that every agent in the chain
   understands the same way. **Include the honest-middle state** ("clean
   but something needs a human"). Without it, teams collapse everything
   to green/red and lose the case that matters most: correct code with a
   pending human decision.
8. **Config-driven, no magic numbers in generator logic. [essential]** Every knob
   (naming, layout, cluster shape, gate rules) lives in one config file
   that is loud on typos. Templates read from it; generator code does not
   inline literals.
9. **Mock-by-default LLM path. [essential]** No key → deterministic mock, no network.
   Tests and dev loops run offline. The live path is a single opt-in
   (`API_KEY` present + `--dry-run` off).
10. **A gate step that computes the verdict. [essential]** Lint the generated code
    with the same rules as the generator itself, scan for debug/secret
    patterns, require a test per module, and — if a JVM/runtime is
    available — actually run the generated tests. The verdict comes from
    the gate's outputs, not from a human decision at the end.
11. **Replay fixtures for demos and CI. [essential]** Commit at least one full run of
    real-model output as a tracked fixture, and build the UI/CLI to load
    it byte-for-byte. Live demos need a proven fallback that works with
    no key and no network.

### What is incidental

- **PySpark + Delta + Databricks** *(incidental — swap freely)* — target platform. Replace with
  Snowflake, dbt, Airflow, Terraform, OpenAPI-to-Kotlin, whatever fits.
- **FRD + STTM** *(incidental — swap freely)* — the specific artifact names. Your equivalents might be
  "API spec + auth policy" or "schema contract + retention rules."
- **Jinja2** *(incidental — swap freely)* — the templating engine. Any deterministic template system
  works; the essential property is *no logic beyond what the spec pins
  down*.
- **Anthropic Claude / `claude-opus-4-8`** *(incidental — swap freely)* — the model. Any tool-capable
  LLM works for Layer 2, provided you can enforce grounding externally.
  (Program policy pinned this vendor; the pattern does not.)
- **Pydantic v2 frozen models** *(incidental — swap freely)* — the schema enforcer. Any strict schema
  library that fails loud on unknown fields is fine.
- **Three verdict states** *(incidental — swap freely)* — the shape is essential; the exact labels are
  not. Some domains benefit from four or five (e.g. adding a
  `NEEDS_UPSTREAM` for spec-side problems).
- **`ruff`** *(incidental — swap freely)* — the linter. Whatever language you emit, use its most
  authoritative linter/type-checker and hold the *generated* code to the
  same standard as the generator source.

### Anti-patterns this design rules out

- Letting Layer 2 write directly into generated modules "just this once"
  for a stubborn case — the audit line disappears immediately.
- Silent defaults for missing spec fields. Missing must be `None`, and
  the emitter must fail loudly or classify the row as unmapped.
- A single boolean pass/fail gate. You will collapse the honest middle
  state and either ship flagged output as green or block clean output as
  red.
- A "temperature knob" or any run-to-run variation source in Layer 1.
  Reviews depend on stable diffs.
- Free-form prompt input alongside the structured spec ("also apply this
  hint"). Every ad-hoc input erodes reproducibility. If it matters, add
  it to the spec schema.

### Where to look next

- [`references/reusable-checklist.md`](references/reusable-checklist.md) —
  the Part B essentials expanded as a build-order checklist with the
  concrete file/module shapes this repo settled on.
- [`references/deep-dive.md`](references/deep-dive.md) — the `src/codegen/`
  tour, useful as a worked example when scaffolding an equivalent
  package.
