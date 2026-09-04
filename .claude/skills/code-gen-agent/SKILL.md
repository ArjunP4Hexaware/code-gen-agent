---
name: code-gen-agent
description: Read this when (a) designing an agent — for any client, domain, or artifact type — that must generate code, transformations, or configuration from an already-approved structured specification (an approved mapping document, schema contract, API spec, control matrix, config manifest, etc.) rather than from free-form natural-language prompting, where correctness has to be provable, output must be byte-stable, and a shared verdict vocabulary needs to survive across a multi-agent pipeline; OR (b) working in or asking about the `code-gen-agent` repository itself — the CodeGen / Data Engineer Agent that emits Databricks PySpark + Delta ingestion pipelines from approved FRD + STTM contracts for the AmeriHealth Caritas program (questions about the two-layer trust architecture, `generate-all`, `extract-sttm`, PASS/PASS_WITH_FLAGS/FAIL verdicts, the Run modes demo UI, the live/replay fixtures under `fixtures/replay/`, the Databricks App `codegen-agent` and its live FMAPI Layer 2, or how the unified agent console proxies this backend). Covers the reusable pattern (Part B) as well as the concrete implementation (Part A).
---

# code-gen-agent — implementation + reusable pattern

Two parts. **Part A** is the concrete agent in this repo — fully
self-contained, including the complete Databricks Genie Code rebuild
specification. **Part B** abstracts the design so another team can lift
it into an unrelated project.

> **Import note.** Only this SKILL.md file travels into the AmeriHealth
> Databricks workspace — no other file in this repo (`README.md`,
> `CLAUDE.md`, `docs/`, `references/`) is reachable from inside Genie
> Code. Part A below is written to be sufficient on its own for that
> reason; every "read more" pointer in this file to another repo file is
> for local Claude Code / repo development only, never a build
> dependency.

---

## Part A — This agent, concretely

### Databricks Unit (DBU) budget — read before generating anything

Arjun and Soham share a **450-DBU/month** pool (recurring, not one-time)
across both engineers and the agents in this program. Genie Code's
own build/iterate loop and the resulting pipeline's runtime compute both
draw against it, so both need to be efficient — not just the finished
architecture. (The table below is the original five-agent split; the
program was cut to three agents on 2026-08-21 — BRD→FRD and SQL
Optimization left — so their rows are historical, and the two Databricks
Apps now running, `codegen-agent` and `unified-agent-console`, bill by
the hour while up: stop them when not demoing.)

| Agent | Monthly DBU guardrail | Real Databricks footprint |
|---|---|---|
| FRD → STTM | ~150 | 4 chained serverless notebooks + UC volumes — **cost center** |
| **CodeGen (this agent)** | **~120** | **Generated Spark tests need a JVM cluster — cost center** |
| SQL Optimization | ~130 | Warehouse EXPLAIN/DESCRIBE/telemetry queries — **cost center** |
| BRD → FRD | ~30 | Databricks App hosting only — light |
| Code Review | ~10 | Runs off Databricks entirely; audit-sink stub only — near-zero |
| *(10 DBU/month held as shared pod buffer)* | | |

This agent's only real Databricks-compute dependency is running the
**generated Spark test suite**, which needs a JVM — everything else
(Jinja2 rendering, `extract-sttm`, the demo UI) is local and touches no
workspace resource. These are planning guardrails, not automatic limits
— check the workspace usage/cost dashboard against this table monthly;
if a wave is trending over its guardrail before it's done, stop and
re-scope rather than keep spending.

**Minimizing Genie Code build cost (the biggest lever):**

The largest controllable cost is how many separate generation passes it
takes Genie Code to go from "empty folder + spec" to a working agent —
not the runtime footprint above. Attack it directly:

- **Give Genie Code the complete spec in one import, not incremental
  prompts.** Every open design question Genie Code has to explore or ask
  about is a billed pass; every question the spec already answers is one
  it doesn't spend a turn discovering.
- **This SKILL.md is fully self-contained — nothing else needs to be
  imported.** The complete target architecture, stage-by-stage design,
  design constraints, acceptance criteria, and Anthropic-adaptation notes
  are inlined below (§1–§8 of this Part A). There is no separate rebuild
  document to point Genie Code at; everything it needs is already in the
  one file it has.
- **Request full-scope generation per layer in one pass** (e.g.,
  "generate the Layer 1 Jinja2 templates and emitter now," then
  separately "generate the Layer 2 reasoning + grounding path"), not
  file-by-file back-and-forth.
- **Treat this file's two-layer architecture and verdict vocabulary as
  fixed scope.** Don't ask Genie Code to propose alternatives — that
  exploration is billed iteration the spec has already resolved.
- **Review generated code yourself, outside Genie Code**, rather than
  prompting it to re-explain or re-justify what it wrote.
- **Batch fixes** into one follow-up prompt instead of correcting issues
  one at a time across many small turns.
- **Cap generation passes per agent** (e.g., 5–8) and stop to reassess if
  you hit it — that's a signal the spec is underspecified, not a signal
  to keep prompting.

**General doctrine — applies everywhere in this repo:**

- **Serverless first.** Use serverless notebooks/jobs/SQL warehouses
  wherever the workspace offers them — they bill only for execution
  seconds and scale to zero between Genie Code turns. If a classic
  cluster is unavoidable, use the smallest single-node instance type and
  set auto-termination to 10–15 minutes; never leave the default.
- **Local/mock/replay first.** Iterate against this repo's existing
  offline paths (local dev, mock providers, replay fixtures, `--dry-run`)
  for as long as possible. Reserve real Databricks compute for a small
  number of deliberate validation checkpoints, not every change.
- **Capture every successful live run once.** This repo's record/replay
  seam exists exactly so a working path never needs to be re-run, and
  re-spent, to prove it still works.
- **No scheduled/cron jobs during the build phase.** Trigger runs
  manually, only when there's something new to validate.

**Specific to this agent:**

- Default every `generate-all` invocation Genie Code runs while
  iterating to `--dry-run --skip-tests` — this is already the documented
  quickstart path and makes zero network/compute calls.
- Drop `--skip-tests` only for a deliberate, occasional validation pass,
  on the **smallest single-node** compute the workspace offers, with a
  short (10–15 min) auto-termination — never a standing cluster.
- Layer 2 (the LLM path) is **mock on every dry run** and the tracked
  config's live transport is `reasoning.provider: databricks_fmapi`
  (Claude served by the workspace endpoint `databricks-claude-opus-5`),
  which resolves from workspace auth **without any env secret** — so a
  test or a demo that touches a live path must pin the provider (or set
  `CODEGEN_FORCE_MOCK_PROVIDER=1`), otherwise it spends. The first live
  E2E on the Databricks App happened 2026-09-04 (`demo_20260904_150435`,
  CV golden pair) — capture any further live run as a replay fixture
  immediately so it never needs re-spending.
- The demo UI already always runs `--dry-run --skip-tests` by design —
  don't change that to make a demo "feel more real"; it's already the
  cheap path.

---

### 1. Product Context

The agent is the **second link in the three-agent AI-in-Engineering program** (scope cut 2026-08-21 from five): FRD → STTM → **CodeGen** → Code Review. Its inputs and output are content contracts with the neighboring agents:

- **Upstream** — consumes **two** approved, machine-readable artifacts per feed, both produced by the FRD → STTM agent (or, for the STTM half, extracted deterministically from a client workbook by this repo's own `extract-sttm` tool):
  - the **FRD feed contract** (`*.contract.json`) — feed-level facts: file-name patterns, format/delimiter, `record_segments` for segmented dialects, stage/standard targets and load strategies, free-text `validation_rules`, `recycle_rule`, PHI notes, SLAs;
  - the **STTM mapping contract** — column-level facts: `fields[]` with source/stage/standard names, dtypes, nullable/phi/mandatory flags, `audit_columns`, structured `load_rules` (including a recycle spec).
  Both are pydantic v2 models: `frozen=True`, `extra="forbid"` (unknown keys fail loudly, never silently drop), missing is `None` — never a default that could be mistaken for a real value.
- **Downstream** — the **Code Review Agent** reviews whatever this agent emits, once an engineer opens a PR containing the generated code. This agent's own gate pre-flights the Code Review Agent's checks (ruff, structural scans, test-per-module) so a PR is never opened on output that would fail review for a reason this agent could have caught itself.

Design philosophy carried over from the existing implementation — the same two-layer trust rule the Code Review Agent's five-layer architecture generalizes, collapsed to two:

> Everything derivable from the contract is compiled by deterministic code. The LLM touches only what determinism cannot — free-text rules a rule compiler cannot classify — and its output never lands in a generated module directly. It proposes; an engineer approves and implements.

The rebuild must preserve that division of labor. The LLM is never the arbiter of "is this code correct" — the deterministic gate (ruff, structural checks, the generated Spark test suite) is.

---

### 2. End-to-End Pipeline

Five stages, all triggered per invocation against one resolved feed (there is no continuously-running data-transformation loop in this agent — see §6.1 for why that matters to the target architecture):

```
   ┌──────────┐   ┌────────────┐   ┌───────────────┐   ┌──────────────┐   ┌─────────┐
   │ Resolve  │ → │  Classify  │ → │  Layer 1 Emit │ → │   Layer 2    │ → │  Gate + │
   │FRD ⋈ STTM│   │   rules    │   │ (Jinja2: DDL, │   │  Reasoning   │   │  Report │
   │          │   │(determinis-│   │  PySpark, job,│   │ (unmapped    │   │(verdict,│
   │          │   │    tic)    │   │  tests, notebook│  │ rules only,  │   │notebook)│
   │          │   │            │   │  assembly)    │   │ mock default)│   │         │
   └──────────┘   └────────────┘   └───────────────┘   └──────────────┘   └─────────┘
```

#### 2.1 Stage 1 — Contract Resolution

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

#### 2.2 Stage 2 — Rule Classification

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

#### 2.3 Stage 3 — Layer 1 Deterministic Emission (Jinja2)

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
  candidates/     candidates.json — the Layer 2 review artifact (see §2.4, §3.6)
  ruff.toml       lint config matching the generator's own rules (see §7.7)
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

#### 2.4 Stage 4 — Layer 2 Reasoning

**Purpose.** Propose a classification, a code sketch, and grounded rationale for each `unmapped` rule — never write code directly. See §3 for the full design contract; this subsection is the pipeline-position summary only.

**Conceptual output.** `out/<feed_id>/candidates/candidates.json` — a **review artifact**, never merged automatically. Every citation in it must be verbatim-groundable against the rule text or the contract excerpts the model was shown.

**On Genie Code / LDP.** The one step in this pipeline that calls a model. See §6.1 and §6.3 for why this argues for an on-demand Genie Code notebook/job step rather than a continuously-triggered LDP table.

#### 2.5 Stage 5 — Gate, Report, and Notebook Assembly

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

#### 2.6 `extract-sttm` — a separate deterministic tool

**Purpose.** When only a client-authored Excel workbook exists (no STTM mapping contract yet), deterministically convert it into one, paired with the FRD contract whose `feed_id` (via `normalize_feed_name`) and format/delimiter/standard-target facts anchor the extraction.

**Conceptual input.** A workbook plus its paired FRD contract.

**Conceptual output.** An STTM mapping contract JSON, byte-reproducible given an injected `--generated-date` (no clock reads).

**Behavior worth preserving — the hard scope boundary.**

- **Flat dialect only.** The extractor recognizes one layout family: a `FILE_DETAILS` + `VERSION_HISTORY` + per-feed `MAPPING-<TABLE>` sheet structure, with a band-label row (`Source File Layout` / `Stage Layer` / `Standard Layer`), fuzzy header-synonym matching (three header dialects already observed in one golden workbook), and trailing `NA` rows recognized as audit columns.
- **A segmented (Header/Detail/Trailer) workbook is a hard error (`SegmentedWorkbookError`), by design, not a bug.** The parser detects the family by content (a key:value metadata block, a `Source Layout` band variant, and/or a per-row `Segment` column), not by filename, and refuses rather than guessing. This is why the CAQH feed ships with a clearly-labeled **synthetic** STTM contract (`"synthetic": true` in the payload) instead of an extracted real one.
- **Segmented-dialect v2 is a scoped, not-yet-built backlog item** (`docs/SEGMENTED_MODE_DESIGN.md` — local repo only, not part of the Databricks import), with two named blockers that must be resolved by a human before it can be built, not inferred from the workbook alone:
  1. The Header/Detail/Trailer record-type discriminator (assumed to be the row's first column, values `H`/`D`/`T`) is **unverified** — the real CAQH workbook confirms segment *membership* per field but never states the literal discriminator values anywhere in the sheet.
  2. The real CAQH workbook's Standard Layer is **fully populated** (per-segment target tables, "Load as is" transformations), while the committed FRD contract's standard target is empty and the synthetic STTM says stage-only. This is a genuine contradiction between two supposedly-authoritative sources and has been escalated for a human decision — a rebuild must not silently pick one.

**On Genie Code / LDP.** A separate, on-demand utility step (CLI-equivalent notebook or job), not part of the main generation pipeline's trigger path. It has no model call and no compute-shape implications beyond ordinary Python execution.

---

### 3. Layer 2 Reasoning — Design Contract

Because this is the one place a model touches the pipeline, and the one real DBU cost driver for this agent's build (see the DBU budget section above), it gets its own design contract.

#### 3.1 What reaches the model

**Only rule-compiler-classified `unmapped` outcomes** — never a `mappable`, `flagged`, `notification`, `orchestration_config`, or `out_of_scope` rule, and never generated code. Per unmapped rule, the model receives a **context pack**: the rule text, all of that feed's contract validation-rule excerpts plus SLA/frequency strings, and the source/stage/audit column name lists (as *context*, explicitly not as citable material — see §3.3).

#### 3.2 Request shape

**One prompt in, one JSON object out — no streaming, no tool use, no multi-turn conversation beyond the retry loop below.** The system prompt states the exact four required output keys (`classification`, `code_candidate`, `rationale`, `citations`) and forbids omitting any of them (a non-code classification still requires the JSON literal `null` for `code_candidate`, never an omitted key). The user message is the context pack rendered as indented JSON.

**This repo's retry policy differs from a "no repair loop" design — state this plainly, do not assume it matches the FRD→STTM agent's pattern.** A schema-invalid response is retried, with the validation error appended to a *grown* prompt, up to `config.reasoning.max_attempts` total attempts (currently 2) — not treated as an immediate hard failure. Exhausting attempts raises a `ProviderError`, which the pipeline catches and records as a **provider-failure candidate** (a flag, never a crashed generation). This is a deliberate, verified design choice for this agent; do not "fix" it into parity with the other agent's no-retry policy without a decision to do so.

#### 3.3 Grounding — the citable-set boundary (a live-validated lesson)

Every citation the model returns must be an **exact verbatim substring** of the rule text or a contract-excerpt entry in the pack — nothing else is citable. This was tightened after the first live run: the model cited a bare column name copied from the pack's `available_source_columns` list, which the system prompt at the time did not clearly exclude. **The system prompt must state the citable set explicitly** ("rule_text and contract_excerpts entries ONLY — column lists are context, not citable material") — this is not optional prose polish, it is what separates a real grounding failure from a false one. A candidate with any non-groundable citation is marked ungrounded in the report; it is never silently dropped, and it never promotes to a clean gate state.

#### 3.4 Mock-by-default gating

`MockProvider` is the default for every test and every `--dry-run` invocation — deterministic, offline, zero cost. A live provider activates **only** when dry-run is off and the configured transport resolves: `anthropic` needs `ANTHROPIC_API_KEY`; `databricks_fmapi` (the tracked config since 2026-08-28 — the same Claude model served by the workspace endpoint, a transport, not a vendor change) needs resolvable workspace auth and **no env secret at all**, which is why live-touching tests pin the provider and why `CODEGEN_FORCE_MOCK_PROVIDER=1` exists as a hard lock (it was set on the App for 0.3.2–0.3.3 and removed 2026-09-01). A rebuild must preserve this gate exactly: unresolvable credentials must never silently degrade a live-intended run to mock (it is recorded as a provider failure), and resolvable credentials during a dry run must never silently promote a mock-intended run to live. `GET /api/demo/live-available` reports `{available, provider, reason}` — the `reason` is the provider-specific remedy, never a hardwired "no ANTHROPIC_API_KEY".

#### 3.5 No sampling parameters (a real, billed lesson)

The model family behind this agent's `reasoning.model` config value (`claude-opus-5` since 2026-08-28; `claude-opus-4-8` before) **rejects `temperature`/`top_p`/`top_k` with an HTTP 400** — discovered on the very first live attempt, when every one of three calls was rejected before processing (the 400s were not billed, but the run produced zero live signal that day). **Do not add a sampling-parameter knob to the request or to config.** Live output is therefore inherently non-deterministic run-to-run; `candidates.json` is a snapshot for engineer review, never a byte-stable expectation, and no test may assert its exact content against a live provider.

**Extended-thinking content (2026-09-01 lesson, FMAPI path):** the serving endpoint returns `message.content` as a **list of typed blocks** (reasoning + text), not a string. `codegen.databricks.chat` normalises it (text blocks joined, non-text ignored); "simplifying" that back to `content or ""` produced provider-failure candidates in a real run. Keep the normalisation.

#### 3.6 Output artifact is a review artifact, never generated code

`candidates.json` (plus a per-run markdown rationale) is read by an engineer, who implements an approved candidate **by hand, in a follow-up commit**. There is deliberately no auto-merge mechanism in v1 — the mechanism that would promote an approved candidate into a generated module (regenerate with an approvals file? patch?) is an explicit, not-yet-made v2 decision, held open until an engineer has actually used the review artifact format. A rebuild must not "complete" this for convenience; that erases the audit line the two-layer design exists to protect.

---

### 4. Verdict & Review Model

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

### 5. Design Constraints a Rebuild Must Respect (Hard-Won Lessons)

#### 5.1 The rule compiler is the whole point — do not let more reach the model

Only `unmapped` rules should ever be sent to Layer 2. If a rebuild finds itself routing `flagged` or `mappable` rules to the model "for a second opinion," that is a regression against the entire two-layer design — it reintroduces exactly the non-determinism and audit-trail loss the deterministic-first architecture exists to prevent.

#### 5.2 Byte-stability has no exceptions in Layer 1

No timestamps, no clock reads, no non-deterministic ordering anywhere in the emit path. Provenance banners carry a content hash of the *inputs*, never a generation timestamp. `extract-sttm` accepts an injected `--generated-date` for the same reason — the rebuild must offer an equivalent injection point rather than defaulting to "now."

#### 5.3 Segmented dialects are a hard boundary, not a best-effort parse

`extract-sttm` refusing a segmented workbook outright (rather than guessing at a layout it wasn't built for) is the correct behavior, proven out by two live blockers discovered on real inspection of the actual CAQH workbook (§2.6): an unverifiable record-type discriminator, and a genuine contradiction between the workbook's populated Standard Layer and the committed contracts' stage-only assumption. **A rebuild must not resolve either blocker by inference** — both require a human decision from the source team, and the existing repo has already escalated them rather than guessing. Preserve the hard-error behavior until both are resolved.

#### 5.4 No sampling parameters, ever, on this model family

See §3.5. This was discovered the expensive way (a fully-failed first live attempt). Do not reintroduce a `temperature`/`top_p`/`top_k` knob without first confirming the target Databricks Model Serving endpoint's actual constraint — it may or may not carry the same restriction as the direct Anthropic path.

#### 5.5 The citable-set boundary must be explicit in the prompt, not implied

See §3.3. "Ground every claim in the provided context" is not specific enough — a model reasonably treats an entire context pack as citable unless told otherwise. State the citable set (`rule_text` + `contract_excerpts` only) explicitly, and treat column-name lists as context-only. This is a proven, live-validated fix, not a theoretical concern.

#### 5.6 Never regenerate over a hand-edit silently

The provenance banner's warning is a real behavioral contract: any manual edit to a file under `out/` is silently reverted on the next `generate` invocation. A rebuild must preserve this — the fix path is always "edit the contract or the template, then regenerate," never "patch the output directly."

#### 5.7 The client's downstream pipeline stack is genuinely unknown

Output targets plain PySpark + Databricks Workflows, structured module-for-module specifically so a Lakeflow Declarative Pipelines port is mechanical later (drift checks map to Auto Loader expectations, DQ checks map to LDP expectations, the orchestrator maps to a Workflow DAG). **This existing "structured for a later DLT port" design intent is directly relevant to §6** — the rebuild target for *this agent's own runtime* is Genie Code/LDP, but the *code this agent emits* should keep being structured the same portable way, since the emitted pipeline is a separate deployable artifact aimed at whatever the client's actual production stack turns out to be.

---

### 6. Target Architecture on Databricks Genie Code

#### 6.1 Runtime shape — an important divergence from the FRD→STTM agent's target

**This agent is fundamentally on-demand, not continuous.** Unlike the FRD→STTM agent (which processes an arbitrary, ongoing stream of incoming FRDs through a fixed four-stage pipeline, and is well modeled as an always-available Lakeflow Declarative Pipeline), CodeGen is invoked **once per approved contract pair**, produces a bounded set of output files, and then is done until the next contract changes. A rebuild should resist modeling this as a continuously-triggered LDP streaming table for its own sake — the natural shape is:

- A **Genie Code notebook or job**, parameterized by the contract-pair identity, triggered **on demand** (a new/changed contract landing in a UC Volume, or a manual/API trigger from whatever workflow tool wraps the "engineer requests generation" step) — not a permanently-running pipeline.
- Internally, the five stages (§2.1–2.5) can still be Lakeflow Declarative Pipeline **steps** within that one triggered run, which gets the benefits of LDP's lineage/observability without paying for a permanently-materialized streaming table that has nothing to stream most of the time.
- **The generated PySpark pipeline this agent emits is a wholly separate artifact**, meant to be deployed as **its own** Databricks Job / LDP pipeline in the target ingestion project — it is not part of this agent's own runtime and must not be confused with it in the target architecture diagram.

#### 6.2 Table & volume topology

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

#### 6.3 Databricks Model Serving for Layer 2

Layer 2 (§3) is the only step needing model access. On the target platform this becomes a Databricks Model Serving (Foundation Model API or external-model endpoint via AI Gateway) call in place of the direct Anthropic SDK client — see §8 for the specific rework items. Because this step runs **at most a handful of times per feed** (one call per `unmapped` rule; the live-run record shows full-pipeline runs completing in 1–5 calls), it should be invoked from **inside** the same on-demand Genie Code run as everything else, not as a separately-triggered serving job.

#### 6.4 Config surface (parameterize the pipeline; do not hardcode)

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

### 7. Acceptance Criteria — What "Done" Looks Like

The current test suite (run `pytest -q` for the live count — all offline, no Spark needed to *render*; a JVM is needed only to *execute* the generated tests; fixture-driven tests skip unless the anonymized CV/golden fixtures are restored from git history) is the strongest available specification of correct behavior. A rebuild is not done until an equivalent suite is green. Grouped by theme:

#### 7.1 Contract resolution

- Matching feed names (via normalization and via `feed_aliases`) resolve; a feed present on only one side is a named `ContractMismatchError`, not a skip.
- Delimiter inference and conflict detection for `csv`/`psv`/`txt`.
- Recycle-window agreement/disagreement between FRD free text and STTM structured spec.
- Segmented-feed target validation: every STTM `stage_table` must be one of the FRD's declared stage tables.
- Natural key derivation from `load_rules.not_null_columns`, never hardcoded.

#### 7.2 Rule classification

- Each of the six classification outcomes (§2.2) fires on its representative fixture example.
- Exactly the `unmapped` outcomes reach Layer 2 — a test should assert that no other class ever appears in a reasoning call.

#### 7.3 Layer 1 byte-stability

- Identical contract inputs produce byte-identical output across repeated runs (no timestamps, no incidental ordering differences).
- Provenance banner carries the correct contract names and content hash.
- Schema-drift behavior: missing column fails the file; extra column is quarantined, the rest of the row still loads.
- Audit-column population and MERGE idempotency: re-ingesting the same file produces no duplicates and preserves `REC_CREATION_TIME`.
- Segmented-feed splitting and trailer-count reconciliation.
- Notebook assembly: `TemplateGapError` on any cross-module namespace collision; assembled notebook and canonical module files never diverge.

#### 7.4 Layer 2 grounding and gating

- A citation that is an exact substring of `rule_text` or a `contract_excerpts` entry passes; a citation from the column-name lists fails (§3.3's live-validated fix, pinned as a regression test).
- Schema-invalid model output retries up to `max_attempts`, then raises `ProviderError`, which the pipeline turns into a failure-flagged candidate — generation of deterministic modules still completes.
- No sampling parameters are ever sent in the provider request (§3.5) — a stub test should assert this directly against the request payload.
- Mock provider is the default with no credential present or with `--dry-run`; a live provider requires an explicit, present credential.

#### 7.5 Gate verdict computation

- Clean feed (no unmapped rules, ruff clean, tests pass) → `PASS`.
- Any flagged/notification/out_of_scope rule, or any pending/ungrounded candidate, or skipped tests → `PASS_WITH_FLAGS`, **never** `FAIL`.
- Ruff failure, structural-check failure, contract mismatch, or a failing generated test → `FAIL`.
- A Layer-2 provider failure alone never produces `FAIL`.

#### 7.6 `extract-sttm`

- The committed golden CV/demo pair reproduces its expected output byte-for-byte (given an injected `--generated-date`).
- A segmented workbook (matching the family signature — key:value metadata block, `Source Layout` band variant, or a per-row `Segment` column) raises `SegmentedWorkbookError` and never silently falls through to the flat parser.
- Fuzzy header-synonym resolution across at least the header dialects already observed in real client workbooks.
- Feed-pairing via `normalize_feed_name` against the paired FRD contract, with a named error on an unpaired feed.

#### 7.7 Generated code quality (the gate's own claim)

- Generated code passes the same `ruff` rules the generator source is held to.
- No debug-statement patterns (`breakpoint()`, `pdb.set_trace(`, debug `print(...)`) in generated output.
- One test file exists per generated pipeline module.
- Generated tests, when run against a local Spark + delta-spark environment, pass for every fixture feed.

---

### 8. Anthropic / Claude-Specific Adaptation Notes

Everything in this section is a rework item for the port to Databricks Model Serving / AI Gateway. Nothing else in the pipeline is provider-specific.

1. **Model client.** The current plain `anthropic.Anthropic().messages.create(...)` call (non-streaming — this repo does **not** stream, unlike the FRD→STTM agent's extraction path, because output per call is small: a few hundred tokens) must be replaced by a **Databricks Model Serving** invocation — the Foundation Model API for a Claude-family endpoint, an external-model endpoint via AI Gateway, or the `databricks-sdk` serving client. The request shape (one system prompt + one user message containing the context pack as JSON) is preserved; only the transport changes.

2. **Model identifier.** `config.reasoning.model` (currently `claude-opus-4-8`, an **Anthropic-side model id**) becomes a **Serving endpoint name** (or Foundation Model id) on the Databricks target. This is already read purely from config — no hardcoded model name anywhere in `src`/`tests`/`ui` — so the port touches only the config value and its documentation, not code.

3. **Auth / secret scope.** Today the client reads `ANTHROPIC_API_KEY` from the environment (loaded by the CLI's own tiny `.env` reader, which never overrides an already-set environment variable). On a Foundation Model endpoint, **workspace identity handles auth** and the secret entirely drops out. If routing through AI Gateway to an external Anthropic key, a Databricks secret scope is retained, but its consumer becomes the Gateway, not this agent's code.

4. **SDK error taxonomy.** Today the code lets Anthropic SDK exceptions escape `complete()` and records them as failure candidates (§2.4, §4) — deliberately, this never crashes generation. Replace the caught exception types with the equivalent Model Serving client error classes (or HTTP-status branching for a direct REST call), preserving the same semantic: any provider failure degrades to a flagged candidate, never a crash.

5. **Retry policy.** The current retry loop (validation-error-appended-to-prompt, up to `max_attempts=2`, §3.2) is application-level, not SDK-level, and must be re-implemented identically at the new transport layer — this is a genuine design choice of this repo, not incidental Anthropic-SDK behavior, so it survives the port unchanged in spirit. Do not add a separate transient-error retry inside the new client on top of this without ensuring the two retry loops can't compound unexpectedly (e.g. a 5xx retried by the client library AND by the application loop).

6. **Streaming.** Not used today (see #1) and not expected to be needed on the target endpoint given the small output size per call — verify against the new endpoint's actual timeout behavior for a ~8k-max-token response before assuming non-streaming stays safe.

7. **Structured outputs — genuinely untested here, unlike the FRD→STTM agent.** This repo has **never attempted provider-native structured output** (e.g. `messages.parse(output_format=...)`); it goes straight to "describe the schema in the system prompt, validate client-side with pydantic `extra=\"forbid\"`." Whether the `CandidateResponse` schema (four keys, one nested list, one nullable string) would hit the same "grammar too large" wall the FRD→STTM agent's much larger schema hit on Anthropic's `messages.parse` is an **open question** — this schema is far smaller and simpler, so it may well succeed where the other agent's did not. **Re-probe server-side structured output on the target endpoint before assuming schema-in-prompt is required here too**; if it works, it's a legitimate simplification for this agent specifically, unlike the FRD→STTM agent where the fallback is settled. If it fails, keep the current schema-in-prompt pattern — it already works and is already validated live.

8. **No sampling parameters.** See §3.5, §5.4. This is model-family behavior discovered on the Anthropic direct path (`claude-opus-4-8` returns 400 on `temperature`/`top_p`/`top_k`). **Re-verify independently on whatever Databricks Model Serving endpoint is actually used** — a Foundation Model endpoint fronting a different model family may accept sampling parameters, or may impose a different restriction entirely. Do not assume the constraint transfers; do not assume it doesn't.

9. **Provider gate values.** `config.reasoning` currently has no explicit provider-name enum beyond "mock unless a key is present and dry-run is off" (simpler than the FRD→STTM agent's explicit `mock`/`anthropic` string gate). If the port introduces an explicit provider tag (`mock` / `databricks`), preserve the same fail-loud discipline the sibling agents use: an unrecognized value should raise, never silently degrade.

10. **Packaging.** `anthropic` is lazy-imported (only inside `AnthropicProvider.__init__`) so the deterministic path never needs it installed; it lives behind a `live` extra in `pyproject.toml`. The equivalent Databricks Model Serving client package (`databricks-sdk` or the relevant Foundation Model client) should follow the same lazy-import-behind-an-extra discipline, so the deterministic Layer-1-only path keeps working with zero optional dependencies installed.

11. **Documentation references.** `docs/LIVE_RUN_RECORD.md` and `docs/LIVE_PATH_RECON.md` (local repo only, not part of the Databricks import) cite Anthropic-specific behaviors (the temperature-400 discovery, exact token/cost measurements, SDK-specific error handling). Retain them as historical context in the git repo — the numbers are real and valuable — but the runbook that ships with the rebuild must reflect the Databricks-native cost/observability surface (Model Serving usage tables, endpoint metrics), not the Anthropic dashboard.

---

### Demo UI + replay fixtures

`ui/` is a FastAPI (8571) + Vite/React (5173) dashboard for the client demo.
Three run modes:

- **Mock** — what start-up generation and "Generate all feeds" run; zero
  network. With `contracts.pairs` empty (the tracked config) generate-all
  answers **409 "config.contracts.pairs is empty — nothing to generate"**
  — expected, not a fault.
- **Live** — the full pipeline for real: choose an STTM workbook (from
  fixtures, `inputs/sharepoint`, `inputs/databricks` after a volume fetch,
  or a from-device upload via `POST /api/demo/upload`), pair an FRD
  contract (upstream table rows, local contracts, or an uploaded
  contract JSON; a real pairing is auto-suggested, a look-alike never
  auto-picked), pick the output mode, confirm the cost (~3 calls, ≈ $0.10,
  ~20 s), run. Layer 2 goes through `databricks_fmapi` on the App and by
  default locally; output isolated to `out/demo_<timestamp>/` with
  `run_meta.json` + the FRD copied in, so a past run reloads self-contained.
- **Replay** — loads a recorded run from `fixtures/replay/<run_id>/`
  byte-for-byte; zero API calls; no key or network needed

Replay layout (each fixture is a full recorded live run):

```
fixtures/replay/<run_id>/
  README.md
  call_log.json                         # per-call model/tokens/latency/stop reason
  <feed_slug>/candidates.json           # Layer-2 review artifact
  <feed_slug>/report.md                 # generation report with verdict
```

**Fixtures differ per branch (reconciled 2026-09-01):** on **staging**
`fixtures/contracts/`, the CV golden workbook and `fixtures/replay/` are
untracked (the 2026-08-22 "no client documents in the repository" rule;
only `fixtures/faq/`, the scrubbed `fixtures/reference/` and the
synthetic segmented golden are tracked), so a fresh staging clone has NO
replay set and Replay (and Live) fail loudly with file-not-found. On
**main** commit `b0560af` (2026-08-28, program go-ahead) tracks the
client documents, the CV-golden fixtures and `live_e2e_20260807` — main
keeps them at every merge; staging still holds none. On staging the
anonymized CV/golden demo set — `live_e2e_20260807/` (three CV feeds,
all PASS_WITH_FLAGS), the demo contract pair, and the golden workbook —
is restored from git history at `044752e^` as untracked files. Restore
with `git show`, never `git checkout` (checkout would stage the paths
and re-track them):

```bash
git show "044752e^:fixtures/contracts/FRD_demo_cv_golden.contract.json" \
  > fixtures/contracts/FRD_demo_cv_golden.contract.json   # etc. for the
  # sttm_mapping_contracts_cv_golden.json, demo_sttm_cv_golden.xlsx and
  # every file under fixtures/replay/live_e2e_20260807/
```

Do NOT restore the other historical fixtures (MIDS/CAQH contracts) on
staging — those are client-derived and must stay out of that branch's
working tree.

### Databricks App deployment (`codegen-agent`, 0.3.5 as of 2026-09-04)

The demo UI runs as the workspace app **`codegen-agent`** in Soham's
workspace (`adb-7405617821962942.2`, CLI profile `DEFAULT`):
https://codegen-agent-7405617821962942.2.azure.databricksapps.com

- **Manifest** `app.yaml`: `command: ["python", "-m", "ui.backend.main"]`;
  the app declares the serving endpoint **resource** `llm-endpoint`
  (`databricks-claude-opus-5`, CAN_QUERY), which grants Layer 2 its
  permission declaratively. `requirements.txt` (`.[ui,databricks]`) is the
  Apps pip install; the runtime **caches the installed env keyed on that
  file**, so bump the pyproject version AND the `codegen-version-marker`
  comment whenever `src/` changes, or the App serves stale code.
- **Deploy from a staged tree** (repo files + the gitignored
  `ui/frontend/dist` and fixtures — never `inputs/`), with the repo's
  `.gitignore` **deleted from the staged tree** (`databricks sync` honours
  it and would silently skip `dist`, the contracts, the golden workbook
  and the replay set): `databricks sync <staged> /Workspace/Users/
  <you>/codegen-agent-app` (**without** `--full` — the remote also carries
  `inputs/standards/`, which no longer exists locally) then
  `databricks apps deploy codegen-agent --source-code-path <that path>`.
  Check the remote `dist/index.html` names the fresh bundle hash.
- **State is ephemeral**: every deploy restarts the container, wiping
  `inputs/databricks/`, `inputs/uploads/`, runner state, the output-mode
  selection (back to `notebook`) and past live runs under `out/`.
- **Mock lock removed 2026-09-01 (0.3.4)**; the App runs live Layer 2 via
  FMAPI. UI gates remain: explicit STTM choice, cost confirmation, mock on
  dry-run. Re-lock with `CODEGEN_FORCE_MOCK_PROVIDER=1` in `app.yaml`.
- **0.3.5 lessons (2026-09-04):** `WorkspaceClient` construction raises
  when auth cannot resolve — wrapped in `DatabricksTransportError` so
  routes answer 502 with the SDK's message, never a bare 500; the UI hides
  the volumes section only on **503 (unconfigured)** and shows a 502 with
  Retry; `/api/demo/live-available` carries `reason`; from-device upload
  buttons live in the STTM chooser.
- **Unified agent console** (repo `unified-agent-console`, app
  `unified-agent-console` in the same workspace) reverse-proxies this
  backend under `/api/codegen/*` using its own service principal, which
  holds **CAN_USE** on this app (SP `3a9fb6f7-…`, granted 2026-09-01).
  Every route here is therefore a contract with two front ends; the
  console mirrors `ui/backend/main.py`'s types in `frontend/src/api/
  codegen.ts` and surfaces every `detail` verbatim — keep status codes
  meaningful (409 one-at-a-time / nothing-to-generate, 503 unconfigured,
  502 refused).

### Key docs — local repo / Claude Code development only

These files live in this git repo for local development and future Claude
Code sessions; **none of them are reachable once only this SKILL.md is
imported into the AmeriHealth Databricks workspace.** Everything Genie
Code needs for the actual build is inlined in §1–§8 above.

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
- [`docs/NATIVE_REBUILD_SPEC.md`](../../../docs/NATIVE_REBUILD_SPEC.md) —
  the standalone source this SKILL.md's §1–§8 were merged from; kept in
  the repo as a local reference, but its content now lives above so there
  is no need to open it separately
- [`app.yaml`](../../../app.yaml) — Databricks Apps manifest (see gap #1
  below)

Deeper design references — split out to keep the git repo tidy (local
only):

- [`references/deep-dive.md`](references/deep-dive.md) — file-level tour
  of `src/codegen/` and the config-doctrine rules
- [`references/reusable-checklist.md`](references/reusable-checklist.md) —
  Part B expanded as a build checklist for a new project

### Known open items (do not present as done)

1. **Provider failures render as candidate cards** — a live provider
   error (e.g. the extended-thinking content regression of 2026-08-31)
   becomes a "provider failed" candidate rather than its own flag class;
   the post-demo TODO in `docs/DESIGN.md` §8 is to give it one.
2. **Segmented (Header/Detail/Trailer) STTM workbooks:** the extractor's
   segmented dialect is IMPLEMENTED (corrected 2026-09-01 against the FRD
   read verbatim — segments as tables in both layers, identification
   derived from the STTM, two cited soft CONFIRM items remain); §2.6 and
   §5.3 above describe the earlier hard-error posture and the blockers
   that were since answered by the documents. The MIDS STTM contract
   still predates the extractor.
3. **Layer-2 approval-to-merge is v2** — see §3.6 and §4 above; decisions
   do not gate, merging stays a manual engineer step.
4. **No live-credential `.env` is committed** (there never was one; an
   earlier claim was stale).
5. **`extract-sttm` has never been run on FRD→STTM's own output** — the
   upstream agent (rebuilt 2026-08-27) emits no contract JSON and its
   workbook carries no `Comment`/`Recycle Flag` columns; closing that
   round trip is an open integration task.

### How to run

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"                 # add ",ui,databricks" for the demo UI + FMAPI/volumes; ",live" for the Anthropic SDK
.venv/bin/python -m pytest -q   # offline; fixture-driven tests skip unless the
                                # anonymized CV/golden fixtures are restored (see
                                # "Demo UI + replay fixtures" above); run pytest
                                # for the live count, don't trust a written one
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
- **Anthropic Claude / `claude-opus-5` via Databricks FMAPI** *(incidental — swap freely)* — the model and its transport. Any tool-capable
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
