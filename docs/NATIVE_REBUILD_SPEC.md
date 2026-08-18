# CodeGen / Data Engineer Agent — Native Rebuild Specification

> **Scope of this document.** A functional and architectural specification, written to be sufficient to rebuild the agent from scratch on **Databricks Genie Code** using **Lakeflow Declarative Pipelines (LDP)**, **Unity Catalog (UC)**, and **Databricks Model Serving / AI Gateway** — instead of the current Python-CLI + Jinja2 + Anthropic-SDK stack. It describes *what* each component does and *why*, in prose, tables, and pseudocode. It deliberately avoids pasting source, exact function bodies, or literal Pydantic classes; those live in the existing repo and should not be transcribed here.

---

## 1. Product Context

The agent is the **third link in a five-agent AI-in-Engineering program**: BRD → FRD → FRD → STTM → **CodeGen** → Code Review (SQL Optimization is standalone). Its inputs and output are content contracts with the neighboring agents:

- **Upstream** — consumes **two** approved, machine-readable artifacts per feed, both produced by the FRD → STTM agent (or, for the STTM half, extracted deterministically from a client workbook by this repo's own `extract-sttm` tool):
  - the **FRD feed contract** (`*.contract.json`) — feed-level facts: file-name patterns, format/delimiter, `record_segments` for segmented dialects, stage/standard targets and load strategies, free-text `validation_rules`, `recycle_rule`, PHI notes, SLAs;
  - the **STTM mapping contract** — column-level facts: `fields[]` with source/stage/standard names, dtypes, nullable/phi/mandatory flags, `audit_columns`, structured `load_rules` (including a recycle spec).
  Both are pydantic v2 models: `frozen=True`, `extra="forbid"` (unknown keys fail loudly, never silently drop), missing is `None` — never a default that could be mistaken for a real value.
- **Downstream** — the **Code Review Agent** reviews whatever this agent emits, once an engineer opens a PR containing the generated code. This agent's own gate pre-flights the Code Review Agent's checks (ruff, structural scans, test-per-module) so a PR is never opened on output that would fail review for a reason this agent could have caught itself.

Design philosophy carried over from the existing implementation — the same two-layer trust rule the Code Review Agent's five-layer architecture generalizes, collapsed to two:

> Everything derivable from the contract is compiled by deterministic code. The LLM touches only what determinism cannot — free-text rules a rule compiler cannot classify — and its output never lands in a generated module directly. It proposes; an engineer approves and implements.

The rebuild must preserve that division of labor. The LLM is never the arbiter of "is this code correct" — the deterministic gate (ruff, structural checks, the generated Spark test suite) is.

---

## 2. End-to-End Pipeline

Five stages, all triggered per invocation against one resolved feed (there is no continuously-running data-transformation loop in this agent — see §6.1 for why that matters to the target architecture):

```
   ┌──────────┐   ┌────────────┐   ┌───────────────┐   ┌──────────────┐   ┌─────────┐
   │ Resolve  │ → │  Classify  │ → │  Layer 1 Emit │ → │   Layer 2    │ → │  Gate + │
   │FRD ⋈ STTM│   │   rules    │   │ (Jinja2: DDL, │   │  Reasoning   │   │  Report │
   │          │   │(determinis-│   │  PySpark, job,│   │ (unmapped    │   │(verdict,│
   │          │   │    tic)    │   │ tests, notebook│  │ rules only,  │   │notebook)│
   │          │   │            │   │  assembly)    │   │ mock default)│   │         │
   └──────────┘   └────────────┘   └───────────────┘   └──────────────┘   └─────────┘
```

### 2.1 Stage 1 — Contract Resolution

**Purpose.** Join one FRD feed contract with one STTM mapping contract into a single flattened `ResolvedFeedSpec` — the only object every downstream template reads. Nothing downstream ever touches the raw contracts again.

**Conceptual input.** Two contract JSON files (paths, or a `config.contracts.pairs` entry).

**Conceptual output.** One `ResolvedFeedSpec` per feed named in the pair (a pair may resolve to more than one feed, e.g. a segmented feed with Header/Detail/Trailer stage tables).

**Behavior worth preserving — every mismatch is a loud, named error, never a silent skip:**

- **Join key**: the normalized feed name (lowercase, non-alphanumeric → `_`), so an FRD `"CAQH TPL Inbound Files"` matches an STTM `caqh_tpl_inbound_files`. An explicit `feed_aliases` map in config overrides normalization when names genuinely differ. A feed present in one contract but missing from the other is a resolution **FAIL**, not a skip.
- **Delimiter**: prefer the STTM's explicit delimiter; else infer from format (`csv`→`,`, `psv`→`|`); `txt` requires an explicit delimiter in at least one contract. Two explicit-but-different values is an error naming both.
- **Recycle window**: the FRD's free-text `recycle_rule` and the STTM's structured `recycle.recycle_window_days` must agree on the window when both state one (the FRD text is parsed only for the `N days` figure; the structured STTM spec is what executes).
- **Targets**: every stage/standard schema+table the STTM names must appear in the FRD's target lists (for segmented feeds: every `stage_table` a field names must be one of the FRD's stage tables).
- **Natural key**: derived as `load_rules.not_null_columns` — never hardcoded — combined with `SRC_FILE_NAME` as the MERGE/idempotency key.
- **`ContractMismatchError`** names the feed, the field, and both conflicting values. There is no partial-resolution mode; a mismatched feed does not get generated with a best-guess.

**On Genie Code / LDP.** A pure Python transformation step (no model calls, no I/O beyond reading the two contract JSON artifacts from a UC Volume). No streaming table or continuous trigger is appropriate — it runs once per invocation, on demand.

### 2.2 Stage 2 — Rule Classification

**Purpose.** Deterministically sort every FRD free-text `validation_rule` into one of six outcomes, so only genuinely unclassifiable text ever reaches the LLM.

**Classification vocabulary (six values — enforce as a closed set):**

| Class | Meaning | Disposition |
|---|---|---|
| `mappable` | Rule matches a known pattern (e.g. "If column X is NULL, reject…") | Compiled deterministically into the generated modules |
| `orchestration_config` | Rule describes a job-level toggle (e.g. "duplicate file name check shall be turned off…") | Becomes a knob in the generated job/config, documented in the report |
| `notification` | Rule describes an operational notification (e.g. "email notification post job completion") | Listed in the report; generated job JSON gets an `email_notifications` block |
| `out_of_scope` | Rule describes something outside this agent's remit (e.g. a QA-environment masking process) | Listed in the report, no code generated |
| `flagged` | Rule appears to contradict the paired STTM contract or another rule | Listed in the report for engineer confirmation against the source teams; no code generated |
| `unmapped` | None of the above — the compiler cannot classify it | Routed to Layer 2 (see §3) |

**Behavior worth preserving.** This is a pure pattern-classifier — no model call. It runs before Layer 1 emission and before Layer 2 reasoning, and it is the single gate deciding what reaches the LLM: **only `unmapped` outcomes are sent.** A rebuild must not let any other class reach the model "just to double-check" — that erodes the entire point of having a compiler.

**On Genie Code / LDP.** Another pure Python transformation step. No model calls; safe to run at full LDP-pipeline speed with no cost concern.

### 2.3 Stage 3 — Layer 1 Deterministic Emission (Jinja2)

**Purpose.** Compile everything the contract pins down into byte-stable, production-shaped output. This is the bulk of the agent's value and carries zero LLM risk.

**Conceptual output**, per feed, into `out/<feed_id>/`:

```
out/<feed_id>/
  ddl/            stage / standard / errors / recycle / processed-files DDL (Delta / Unity Catalog)
  pipeline/       reader, [segments], drift, mapping, audit, rejects,
                  [recycle, reference], writer (MERGE), masking, dq,
                  run_report, orchestrator
  job/            Databricks Workflows job JSON + a thin notebook entrypoint
  tests/          pytest suite FOR THE GENERATED CODE (local SparkSession + delta-spark)
  tools/          make_fixtures.py — synthetic data derived from the contract's sample_value fields
  README.md       what was generated, from which contracts, verdict summary
```

`[bracketed]` modules are emitted only when the resolved spec requires them (segments for segmented feeds; recycle/reference for feeds with a recycle rule).

**Behavior worth preserving — the semantics every template encodes:**

- Stage tables are all-String plus typed audit columns; standard tables are typed per `standard_datatype`.
- Schema drift: a missing column fails the file; an extra column is quarantined (the column dropped, the rest of the row still loads).
- Audit columns are pipeline-populated: `LOB` (a job parameter), `SRC_FILE_NAME`, `REC_CREATION_TIME` / `REC_UPDATED_TIME`, with an injectable `run_ts` so recycle aging and backfills are deterministic and testable.
- Not-null enforcement routes rejects to an errors table; PHI keys are masked in that side table too.
- Recycle: a reference lookup (a configurable Facets `SBSB_ID`/`GRGR_CK` stand-in), no-match rows land in a recycle table, retried each run, expired after the configured window (contract-derived — e.g. 7 days for MIDS, 15 for CAQH — **never a literal in generator logic**, only a `defaults.recycle_window_days` fallback in config for a feed with a recycle rule but no stated window).
- Idempotent `MERGE INTO` keyed on `SRC_FILE_NAME` + the derived natural key; `REC_CREATION_TIME` is preserved across re-ingest of the same file.
- PHI masked to last-4 at every log/report/error egress; raw values exist only inside the actual data tables.
- Segmented feeds (CAQH-style): pipe-delimited Header/Detail/Trailer splitting by a record-type discriminator; trailer count reconciled against detail row count in the generated DQ check.
- **Byte-stability.** Templates render with sorted, fully-resolved context; there is no clock read anywhere in the emit path. Every generated file carries a provenance banner (the source contract names + a content hash, never a timestamp). Identical contract inputs must produce identical output bytes, run after run, workspace after workspace.
- **Never hand-edit generated output.** The provenance banner says so; the discipline is that the next regeneration silently reverts a hand-edit, so the only durable fix is to the contract or the template.

**On Genie Code / LDP.** A deterministic transformation step producing files into a UC Volume (or, if the target platform prefers it, Delta rows holding the rendered text plus metadata — see §6.2). No model calls. This step can run on every invocation without cost concern; it is not the DBU-sensitive part of the pipeline.

### 2.4 Stage 4 — Layer 2 Reasoning

**Purpose.** Propose a classification, a code sketch, and grounded rationale for each `unmapped` rule — never write code directly. See §3 for the full design contract; this subsection is the pipeline-position summary only.

**Conceptual output.** `out/<feed_id>/candidates/candidates.json` — a **review artifact**, never merged automatically. Every citation in it must be verbatim-groundable against the rule text or the contract excerpts the model was shown.

**On Genie Code / LDP.** The one step in this pipeline that calls a model. See §6.1 and §6.3 for why this argues for an on-demand Genie Code notebook/job step rather than a continuously-triggered LDP table.

### 2.5 Stage 5 — Gate, Report, and Notebook Assembly

**Purpose.** Compute the three-state verdict, write the per-run generation report, and assemble the single runnable notebook.

**Conceptual pipeline** (all pure code, no model calls):

```
Layer 1 output + Layer 2 candidates
    │
    ├── preflight()      # ruff over out/<feed_id>/, same rules the generator
    │                     # source itself must pass
    │
    ├── structural_checks()  # debug-statement scan (breakpoint(), pdb.set_trace(),
    │                         # print("DEBUG...) — patterns from config.gate.debug_patterns),
    │                         # secrets scan, test-file-per-module check
    │
    ├── run_generated_tests()  # optional (config.gate.run_generated_tests); needs a
    │                           # JVM + local Spark + delta-spark to actually execute —
    │                           # generation itself never needs Spark
    │
    ├── compute_verdict()   # see §4 — candidates can NEVER cause FAIL
    │
    ├── render_report()     # reports/<feed_id>.md — contracts + sha256, rule table
    │                       # with grounding results, candidates, gate checks, verdict
    │
    └── assemble_notebook() # <feed_slug>.ipynb: provenance intro → sys.modules
                            # bootstrap → DDL → each pipeline module verbatim
                            # (self-registering as pipeline.<module>) → job
                            # entrypoint. AST-level namespace checks raise a
                            # TemplateGapError on any cross-module name collision.
```

**Behavior worth preserving.** The assembled notebook is a convenience artifact, not the canonical source — the module files under `pipeline/` remain canonical and tested. Both representations must always agree; the notebook assembler is deterministic code, not a second copy of business logic.

**On Genie Code / LDP.** Pure code. The `run_generated_tests` step is the one place in this whole pipeline that needs a JVM — see §6.1 for the compute-shape implication.

### 2.6 `extract-sttm` — a separate deterministic tool

**Purpose.** When only a client-authored Excel workbook exists (no STTM mapping contract yet), deterministically convert it into one, paired with the FRD contract whose `feed_id` (via `normalize_feed_name`) and format/delimiter/standard-target facts anchor the extraction.

**Conceptual input.** A workbook plus its paired FRD contract.

**Conceptual output.** An STTM mapping contract JSON, byte-reproducible given an injected `--generated-date` (no clock reads).

**Behavior worth preserving — the hard scope boundary.**

- **Flat dialect only.** The extractor recognizes one layout family: a `FILE_DETAILS` + `VERSION_HISTORY` + per-feed `MAPPING-<TABLE>` sheet structure, with a band-label row (`Source File Layout` / `Stage Layer` / `Standard Layer`), fuzzy header-synonym matching (three header dialects already observed in one golden workbook), and trailing `NA` rows recognized as audit columns.
- **A segmented (Header/Detail/Trailer) workbook is a hard error (`SegmentedWorkbookError`), by design, not a bug.** The parser detects the family by content (a key:value metadata block, a `Source Layout` band variant, and/or a per-row `Segment` column), not by filename, and refuses rather than guessing. This is why the CAQH feed ships with a clearly-labeled **synthetic** STTM contract (`"synthetic": true` in the payload) instead of an extracted real one.
- **Segmented-dialect v2 is a scoped, not-yet-built backlog item** (`docs/SEGMENTED_MODE_DESIGN.md`), with two named blockers that must be resolved by a human before it can be built, not inferred from the workbook alone:
  1. The Header/Detail/Trailer record-type discriminator (assumed to be the row's first column, values `H`/`D`/`T`) is **unverified** — the real CAQH workbook confirms segment *membership* per field but never states the literal discriminator values anywhere in the sheet.
  2. The real CAQH workbook's Standard Layer is **fully populated** (per-segment target tables, "Load as is" transformations), while the committed FRD contract's standard target is empty and the synthetic STTM says stage-only. This is a genuine contradiction between two supposedly-authoritative sources and has been escalated for a human decision — a rebuild must not silently pick one.

**On Genie Code / LDP.** A separate, on-demand utility step (CLI-equivalent notebook or job), not part of the main generation pipeline's trigger path. It has no model call and no compute-shape implications beyond ordinary Python execution.

---

## 3. Layer 2 Reasoning — Design Contract

Because this is the one place a model touches the pipeline, and the one real DBU cost driver for this agent's build (see the SKILL.md's DBU budget section), it gets its own design contract.

### 3.1 What reaches the model

**Only rule-compiler-classified `unmapped` outcomes** — never a `mappable`, `flagged`, `notification`, `orchestration_config`, or `out_of_scope` rule, and never generated code. Per unmapped rule, the model receives a **context pack**: the rule text, all of that feed's contract validation-rule excerpts plus SLA/frequency strings, and the source/stage/audit column name lists (as *context*, explicitly not as citable material — see §3.3).

### 3.2 Request shape

**One prompt in, one JSON object out — no streaming, no tool use, no multi-turn conversation beyond the retry loop below.** The system prompt states the exact four required output keys (`classification`, `code_candidate`, `rationale`, `citations`) and forbids omitting any of them (a non-code classification still requires the JSON literal `null` for `code_candidate`, never an omitted key). The user message is the context pack rendered as indented JSON.

**This repo's retry policy differs from a "no repair loop" design — state this plainly, do not assume it matches the FRD→STTM agent's pattern.** A schema-invalid response is retried, with the validation error appended to a *grown* prompt, up to `config.reasoning.max_attempts` total attempts (currently 2) — not treated as an immediate hard failure. Exhausting attempts raises a `ProviderError`, which the pipeline catches and records as a **provider-failure candidate** (a flag, never a crashed generation). This is a deliberate, verified design choice for this agent; do not "fix" it into parity with the other agent's no-retry policy without a decision to do so.

### 3.3 Grounding — the citable-set boundary (a live-validated lesson)

Every citation the model returns must be an **exact verbatim substring** of the rule text or a contract-excerpt entry in the pack — nothing else is citable. This was tightened after the first live run: the model cited a bare column name copied from the pack's `available_source_columns` list, which the system prompt at the time did not clearly exclude. **The system prompt must state the citable set explicitly** ("rule_text and contract_excerpts entries ONLY — column lists are context, not citable material") — this is not optional prose polish, it is what separates a real grounding failure from a false one. A candidate with any non-groundable citation is marked ungrounded in the report; it is never silently dropped, and it never promotes to a clean gate state.

### 3.4 Mock-by-default gating

`MockProvider` is the default for every test and every `--dry-run` invocation — deterministic, offline, zero cost. `AnthropicProvider` (or its Databricks-native successor) activates **only** when a live credential is present and dry-run is off. No key ⇒ no network call, no spend. A rebuild must preserve this gate exactly: the absence of a credential must never silently degrade a live-intended run to mock, and the presence of a credential during a dry run must never silently promote a mock-intended run to live.

### 3.5 No sampling parameters (a real, billed lesson)

The model family behind this agent's `reasoning.model` config value (`claude-opus-4-8` at time of writing; Opus 4.7+ generally) **rejects `temperature`/`top_p`/`top_k` with an HTTP 400** — discovered on the very first live attempt, when every one of three calls was rejected before processing (the 400s were not billed, but the run produced zero live signal that day). **Do not add a sampling-parameter knob to the request or to config.** Live output is therefore inherently non-deterministic run-to-run; `candidates.json` is a snapshot for engineer review, never a byte-stable expectation, and no test may assert its exact content against a live provider.

### 3.6 Output artifact is a review artifact, never generated code

`candidates.json` (plus a per-run markdown rationale) is read by an engineer, who implements an approved candidate **by hand, in a follow-up commit**. There is deliberately no auto-merge mechanism in v1 — the mechanism that would promote an approved candidate into a generated module (regenerate with an approvals file? patch?) is an explicit, not-yet-made v2 decision, held open until an engineer has actually used the review artifact format. A rebuild must not "complete" this for convenience; that erases the audit line the two-layer design exists to protect.

---

## 4. Verdict & Review Model

**Three-state vocabulary, computed entirely in code, never by the model:**

| Status | Triggered by |
|---|---|
| `PASS` | Every validation rule compiled deterministically or was explicitly engineer-approved; generated tests pass; ruff is clean over generated output; nothing pending. |
| `PASS_WITH_FLAGS` | Layer-2 candidates awaiting approval, rules classified `notification` / `out_of_scope` / `flagged` (surfaced, never silently dropped), or generated tests skipped. The honest middle state — usable output, something needs a human. |
| `FAIL` | Contract resolution mismatch, a template gap (a spec feature no template covers), ruff failure, or generated tests failing. |

**The load-bearing rule: Layer-2 candidates can never cause `FAIL`.** `FAIL` comes only from the deterministic gate checks (ruff / structural / generated tests). A live provider outage, an ungrounded citation, or an unresolved candidate all degrade the verdict to `PASS_WITH_FLAGS` at worst — they never block generation of the deterministic modules, which always proceeds regardless of what Layer 2 does. This is what lets the agent be useful even when the model is unavailable or wrong.

**Current committed fixture behavior**: all configured feeds land on `PASS_WITH_FLAGS` — correct, honest behavior, since every feed in the fixture set carries at least one flagged, notification, or unmapped rule. A rebuild should not treat an all-`PASS_WITH_FLAGS` result as a smell; it is the expected shape for these specific real fixtures.

**Review-artifact + decision store (UI, not gating).** A demo dashboard persists engineer approve/reject decisions on Layer-2 candidates. **These decisions do not gate anything** — merging an approved candidate into generated code is a manual step, described in §3.6. The decision store exists for review bookkeeping, not for pipeline control flow.

---

## 5. Design Constraints a Rebuild Must Respect (Hard-Won Lessons)

### 5.1 The rule compiler is the whole point — do not let more reach the model

Only `unmapped` rules should ever be sent to Layer 2. If a rebuild finds itself routing `flagged` or `mappable` rules to the model "for a second opinion," that is a regression against the entire two-layer design — it reintroduces exactly the non-determinism and audit-trail loss the deterministic-first architecture exists to prevent.

### 5.2 Byte-stability has no exceptions in Layer 1

No timestamps, no clock reads, no non-deterministic ordering anywhere in the emit path. Provenance banners carry a content hash of the *inputs*, never a generation timestamp. `extract-sttm` accepts an injected `--generated-date` for the same reason — the rebuild must offer an equivalent injection point rather than defaulting to "now."

### 5.3 Segmented dialects are a hard boundary, not a best-effort parse

`extract-sttm` refusing a segmented workbook outright (rather than guessing at a layout it wasn't built for) is the correct behavior, proven out by two live blockers discovered on real inspection of the actual CAQH workbook (§2.6): an unverifiable record-type discriminator, and a genuine contradiction between the workbook's populated Standard Layer and the committed contracts' stage-only assumption. **A rebuild must not resolve either blocker by inference** — both require a human decision from the source team, and the existing repo has already escalated them rather than guessing. Preserve the hard-error behavior until both are resolved.

### 5.4 No sampling parameters, ever, on this model family

See §3.5. This was discovered the expensive way (a fully-failed first live attempt). Do not reintroduce a `temperature`/`top_p`/`top_k` knob without first confirming the target Databricks Model Serving endpoint's actual constraint — it may or may not carry the same restriction as the direct Anthropic path.

### 5.5 The citable-set boundary must be explicit in the prompt, not implied

See §3.3. "Ground every claim in the provided context" is not specific enough — a model reasonably treats an entire context pack as citable unless told otherwise. State the citable set (`rule_text` + `contract_excerpts` only) explicitly, and treat column-name lists as context-only. This is a proven, live-validated fix, not a theoretical concern.

### 5.6 Never regenerate over a hand-edit silently

The provenance banner's warning is a real behavioral contract: any manual edit to a file under `out/` is silently reverted on the next `generate` invocation. A rebuild must preserve this — the fix path is always "edit the contract or the template, then regenerate," never "patch the output directly."

### 5.7 The client's downstream pipeline stack is genuinely unknown

Output targets plain PySpark + Databricks Workflows, structured module-for-module specifically so a Lakeflow Declarative Pipelines port is mechanical later (drift checks map to Auto Loader expectations, DQ checks map to LDP expectations, the orchestrator maps to a Workflow DAG). **This existing "structured for a later DLT port" design intent is directly relevant to §6** — the rebuild target for *this agent's own runtime* is Genie Code/LDP, but the *code this agent emits* should keep being structured the same portable way, since the emitted pipeline is a separate deployable artifact aimed at whatever the client's actual production stack turns out to be.

---

## 6. Target Architecture on Databricks Genie Code

### 6.1 Runtime shape — an important divergence from the FRD→STTM agent's target

**This agent is fundamentally on-demand, not continuous.** Unlike the FRD→STTM agent (which processes an arbitrary, ongoing stream of incoming FRDs through a fixed four-stage pipeline, and is well modeled as an always-available Lakeflow Declarative Pipeline), CodeGen is invoked **once per approved contract pair**, produces a bounded set of output files, and then is done until the next contract changes. A rebuild should resist modeling this as a continuously-triggered LDP streaming table for its own sake — the natural shape is:

- A **Genie Code notebook or job**, parameterized by the contract-pair identity, triggered **on demand** (a new/changed contract landing in a UC Volume, or a manual/API trigger from whatever workflow tool wraps the "engineer requests generation" step) — not a permanently-running pipeline.
- Internally, the five stages (§2.1–2.5) can still be Lakeflow Declarative Pipeline **steps** within that one triggered run, which gets the benefits of LDP's lineage/observability without paying for a permanently-materialized streaming table that has nothing to stream most of the time.
- **The generated PySpark pipeline this agent emits is a wholly separate artifact**, meant to be deployed as **its own** Databricks Job / LDP pipeline in the target ingestion project — it is not part of this agent's own runtime and must not be confused with it in the target architecture diagram.

### 6.2 Table & volume topology

```
Unity Catalog
├── <catalog>.<schema>.codegen_runs         (Delta, one row per generation invocation:
│                                            contract names + sha256, verdict, feed_id,
│                                            n_candidates, n_flagged, generated_at)
└── (no other durable Delta tables — this agent's state is files, not rows, by design;
     see the caution below)

UC Volumes
├── /Volumes/<catalog>/<schema>/codegen_contracts_in   (approved FRD + STTM contract JSON,
│                                                        written by the upstream agent)
├── /Volumes/<catalog>/<schema>/codegen_workbooks_in   (client STTM workbooks, extract-sttm input)
└── /Volumes/<catalog>/<schema>/codegen_out
        ├── <feed_id>/ddl/ ...
        ├── <feed_id>/pipeline/ ...
        ├── <feed_id>/job/ ...
        ├── <feed_id>/tests/ ...
        ├── <feed_id>/candidates/candidates.json
        ├── <feed_id>/<feed_id>.ipynb
        └── reports/<feed_id>.md
```

**Caution — do not over-fit a Delta-table shape onto this agent just for consistency with FRD→STTM.** That agent's per-stage Delta rows exist because it processes many documents over time and needs a durable per-document record. CodeGen's natural persistence unit is the **generated file tree per feed**, which already carries its own provenance (contract names + sha256) in every file's banner — a single lightweight `codegen_runs` audit table is enough; do not invent additional Delta tables to mirror the other agent's shape.

### 6.3 Databricks Model Serving for Layer 2

Layer 2 (§3) is the only step needing model access. On the target platform this becomes a Databricks Model Serving (Foundation Model API or external-model endpoint via AI Gateway) call in place of the direct Anthropic SDK client — see §8 for the specific rework items. Because this step runs **at most a handful of times per feed** (one call per `unmapped` rule; the live-run record shows full-pipeline runs completing in 1–5 calls), it should be invoked from **inside** the same on-demand Genie Code run as everything else, not as a separately-triggered serving job.

### 6.4 Config surface (parameterize the pipeline; do not hardcode)

| Setting | Purpose |
|---|---|
| `contracts.dir`, `contracts.pairs` | Where approved contract JSON lives and which pairs to generate |
| `feed_aliases` | FRD-feed-name → STTM-feed-id overrides when normalization isn't enough |
| `output.dir`, `output.reports_dir` | Output roots |
| `naming.*` (`errors_table_suffix`, `recycle_table_suffix`, `processed_files_table_suffix`) | Side-table naming derived from the stage table name |
| `defaults.recycle_window_days` | Fallback only — used when a feed has a recycle rule but no window stated anywhere |
| `masking.policy`, `masking.visible_chars`, `masking.mask_char` | PHI masking policy at every egress |
| `segments.record_type_column`, `segments.record_type_values`, `segments.trailer_count_column` | Segmented-feed discriminator assumption — flagged unverified, see §2.6 and §5.3 |
| `extractor.*` | `extract-sttm`'s sheet names, band labels, header synonyms, audit-row markers — all fuzzy-matching knobs |
| `reasoning.model`, `reasoning.max_tokens`, `reasoning.max_attempts` | Layer 2 model identity and retry policy — **no temperature/top_p/top_k knob, ever** (§3.5, §5.4) |
| `demo.*` | Cost-confirmation copy for a live demo run (estimated calls/cost/seconds) — kept in a separate file from the primary `extra="forbid"` config for the same reason the other four agents split demo config out |
| `gate.run_generated_tests`, `gate.ruff`, `gate.structural_checks`, `gate.debug_patterns`, `gate.pytest_tail_lines` | What the gate checks and how strictly |
| `job.notification_emails`, `job.spark_version`, `job.node_type_id`, `job.num_workers` | Generated Databricks Workflows job shape — a config guess pending the client's actual cluster policy |

Genie Code / job parameters should map cleanly to these names, the same discipline the FRD→STTM agent's rebuild spec follows.

---

## 7. Acceptance Criteria — What "Done" Looks Like

The current test suite (80 test functions across 11 files, all offline, no Spark needed to *render* — a JVM is needed only to *execute* the generated tests) is the strongest available specification of correct behavior. A rebuild is not done until an equivalent suite is green. Grouped by theme:

### 7.1 Contract resolution

- Matching feed names (via normalization and via `feed_aliases`) resolve; a feed present on only one side is a named `ContractMismatchError`, not a skip.
- Delimiter inference and conflict detection for `csv`/`psv`/`txt`.
- Recycle-window agreement/disagreement between FRD free text and STTM structured spec.
- Segmented-feed target validation: every STTM `stage_table` must be one of the FRD's declared stage tables.
- Natural key derivation from `load_rules.not_null_columns`, never hardcoded.

### 7.2 Rule classification

- Each of the six classification outcomes (§2.2) fires on its representative fixture example.
- Exactly the `unmapped` outcomes reach Layer 2 — a test should assert that no other class ever appears in a reasoning call.

### 7.3 Layer 1 byte-stability

- Identical contract inputs produce byte-identical output across repeated runs (no timestamps, no incidental ordering differences).
- Provenance banner carries the correct contract names and content hash.
- Schema-drift behavior: missing column fails the file; extra column is quarantined, the rest of the row still loads.
- Audit-column population and MERGE idempotency: re-ingesting the same file produces no duplicates and preserves `REC_CREATION_TIME`.
- Segmented-feed splitting and trailer-count reconciliation.
- Notebook assembly: `TemplateGapError` on any cross-module namespace collision; assembled notebook and canonical module files never diverge.

### 7.4 Layer 2 grounding and gating

- A citation that is an exact substring of `rule_text` or a `contract_excerpts` entry passes; a citation from the column-name lists fails (§3.3's live-validated fix, pinned as a regression test).
- Schema-invalid model output retries up to `max_attempts`, then raises `ProviderError`, which the pipeline turns into a failure-flagged candidate — generation of deterministic modules still completes.
- No sampling parameters are ever sent in the provider request (§3.5) — a stub test should assert this directly against the request payload.
- Mock provider is the default with no credential present or with `--dry-run`; a live provider requires an explicit, present credential.

### 7.5 Gate verdict computation

- Clean feed (no unmapped rules, ruff clean, tests pass) → `PASS`.
- Any flagged/notification/out_of_scope rule, or any pending/ungrounded candidate, or skipped tests → `PASS_WITH_FLAGS`, **never** `FAIL`.
- Ruff failure, structural-check failure, contract mismatch, or a failing generated test → `FAIL`.
- A Layer-2 provider failure alone never produces `FAIL`.

### 7.6 `extract-sttm`

- The committed golden CV/demo pair reproduces its expected output byte-for-byte (given an injected `--generated-date`).
- A segmented workbook (matching the family signature — key:value metadata block, `Source Layout` band variant, or a per-row `Segment` column) raises `SegmentedWorkbookError` and never silently falls through to the flat parser.
- Fuzzy header-synonym resolution across at least the header dialects already observed in real client workbooks.
- Feed-pairing via `normalize_feed_name` against the paired FRD contract, with a named error on an unpaired feed.

### 7.7 Generated code quality (the gate's own claim)

- Generated code passes the same `ruff` rules the generator source is held to.
- No debug-statement patterns (`breakpoint()`, `pdb.set_trace(`, debug `print(...)`) in generated output.
- One test file exists per generated pipeline module.
- Generated tests, when run against a local Spark + delta-spark environment, pass for every fixture feed.

---

## 8. Anthropic / Claude-Specific Adaptation Notes

Everything in this section is a rework item for the port to Databricks Model Serving / AI Gateway. Nothing else in the pipeline is provider-specific.

1. **Model client.** The current plain `anthropic.Anthropic().messages.create(...)` call (non-streaming — this repo does **not** stream, unlike the FRD→STTM agent's extraction path, because output per call is small: a few hundred tokens) must be replaced by a **Databricks Model Serving** invocation — the Foundation Model API for a Claude-family endpoint, an external-model endpoint via AI Gateway, or the `databricks-sdk` serving client. The request shape (one system prompt + one user message containing the context pack as JSON) is preserved; only the transport changes.

2. **Model identifier.** `config.reasoning.model` (currently `claude-opus-4-8`, an **Anthropic-side model id**) becomes a **Serving endpoint name** (or Foundation Model id) on the Databricks target. This is already read purely from config — `grep` confirms no hardcoded model name anywhere in `src`/`tests`/`ui` — so the port touches only the config value and its documentation, not code.

3. **Auth / secret scope.** Today the client reads `ANTHROPIC_API_KEY` from the environment (loaded by the CLI's own tiny `.env` reader, which never overrides an already-set environment variable). On a Foundation Model endpoint, **workspace identity handles auth** and the secret entirely drops out. If routing through AI Gateway to an external Anthropic key, a Databricks secret scope is retained, but its consumer becomes the Gateway, not this agent's code.

4. **SDK error taxonomy.** Today the code lets Anthropic SDK exceptions escape `complete()` and records them as failure candidates (§2.4, §4) — deliberately, this never crashes generation. Replace the caught exception types with the equivalent Model Serving client error classes (or HTTP-status branching for a direct REST call), preserving the same semantic: any provider failure degrades to a flagged candidate, never a crash.

5. **Retry policy.** The current retry loop (validation-error-appended-to-prompt, up to `max_attempts=2`, §3.2) is application-level, not SDK-level, and must be re-implemented identically at the new transport layer — this is a genuine design choice of this repo, not incidental Anthropic-SDK behavior, so it survives the port unchanged in spirit. Do not add a separate transient-error retry inside the new client on top of this without ensuring the two retry loops can't compound unexpectedly (e.g. a 5xx retried by the client library AND by the application loop).

6. **Streaming.** Not used today (see #1) and not expected to be needed on the target endpoint given the small output size per call — verify against the new endpoint's actual timeout behavior for a ~8k-max-token response before assuming non-streaming stays safe.

7. **Structured outputs — genuinely untested here, unlike the FRD→STTM agent.** This repo has **never attempted provider-native structured output** (e.g. `messages.parse(output_format=...)`); it goes straight to "describe the schema in the system prompt, validate client-side with pydantic `extra=\"forbid\"`." Whether the `CandidateResponse` schema (four keys, one nested list, one nullable string) would hit the same "grammar too large" wall the FRD→STTM agent's much larger schema hit on Anthropic's `messages.parse` is an **open question** — this schema is far smaller and simpler, so it may well succeed where the other agent's did not. **Re-probe server-side structured output on the target endpoint before assuming schema-in-prompt is required here too**; if it works, it's a legitimate simplification for this agent specifically, unlike the FRD→STTM agent where the fallback is settled. If it fails, keep the current schema-in-prompt pattern — it already works and is already validated live.

8. **No sampling parameters.** See §3.5, §5.4. This is model-family behavior discovered on the Anthropic direct path (`claude-opus-4-8` returns 400 on `temperature`/`top_p`/`top_k`). **Re-verify independently on whatever Databricks Model Serving endpoint is actually used** — a Foundation Model endpoint fronting a different model family may accept sampling parameters, or may impose a different restriction entirely. Do not assume the constraint transfers; do not assume it doesn't.

9. **Provider gate values.** `config.reasoning` currently has no explicit provider-name enum beyond "mock unless a key is present and dry-run is off" (simpler than the FRD→STTM agent's explicit `mock`/`anthropic` string gate). If the port introduces an explicit provider tag (`mock` / `databricks`), preserve the same fail-loud discipline the sibling agents use: an unrecognized value should raise, never silently degrade.

10. **Packaging.** `anthropic` is lazy-imported (only inside `AnthropicProvider.__init__`) so the deterministic path never needs it installed; it lives behind a `live` extra in `pyproject.toml`. The equivalent Databricks Model Serving client package (`databricks-sdk` or the relevant Foundation Model client) should follow the same lazy-import-behind-an-extra discipline, so the deterministic Layer-1-only path keeps working with zero optional dependencies installed.

11. **Documentation references.** `docs/LIVE_RUN_RECORD.md` and `docs/LIVE_PATH_RECON.md` cite Anthropic-specific behaviors (the temperature-400 discovery, exact token/cost measurements, SDK-specific error handling). Retain them as historical context — the numbers are real and valuable — but the runbook that ships with the rebuild must reflect the Databricks-native cost/observability surface (Model Serving usage tables, endpoint metrics), not the Anthropic dashboard.

---

*End of specification.*
