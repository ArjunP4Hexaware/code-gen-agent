# Live Run Record — first billed Layer-2 validation (2026-08-07)

Record of the runs that took the reasoning stage from "unit-tested against a
stubbed SDK" to "validated with real billed Anthropic calls." All runs use
the CV/golden contract pair (`FRD_demo_cv_golden.contract.json` +
`sttm_mapping_contracts_cv_golden.json`, 3 resolved feeds, 1 unmapped rule
each) via `codegen generate --skip-tests`, model `claude-opus-4-8`
(config `reasoning.model`), `max_tokens: 8192`.

## Attempt 1 — zero billed calls (temperature 400)

Every call was rejected: `400 invalid_request_error — 'temperature' is
deprecated for this model`. The pre-live hardening had added a
`reasoning.temperature: 0` knob; this model family rejects sampling
parameters (`temperature`/`top_p`/`top_k`) outright. The 400s were rejected
before processing and **not billed**.

What this attempt validated anyway: the failure path. All three provider
errors degraded to `response: null` candidates with failure notes and
gate flags — `PASS_WITH_FLAGS`, exit 0, no crashed generation, exactly the
designed behavior for a live outage.

**Fix:** temperature knob removed end to end (provider call, `ReasoningConfig`,
`config.yaml`, stub test now asserts `temperature` is never sent). Live
Layer-2 output is therefore inherently non-deterministic; `candidates.json`
is a snapshot, never a byte-stable expectation.

## Live E2E #1 — functional pass, one ungrounded citation

3 calls, 3/3 schema-valid on the first attempt (0 retries), `end_turn` on
all, 14.5s wall. 14,978 input + 667 output tokens ≈ **$0.092**
($5/$25 per MTok).

All three feeds `PASS_WITH_FLAGS`; all candidates classified `mappable`
with a correct minimal two-line PySpark null-check/reject sketch and a
substantive rationale.

Grounding: 2 of 3 feeds grounded — via **exact** substring match; the
citation normalization added pre-live was never needed (the model copies
text cleanly rather than transcribing JSON escapes). One feed
(`cv_community_demographic_risk`) was ungrounded: the model added a second
citation consisting of a bare column name copied from the pack's
`available_source_columns` list. Diagnosis: prompt-scope ambiguity, not a
transcription bug — the system prompt said "copied from the provided
contract text," and the model reasonably treated the whole pack as contract
text, while the grounding check's citable set is rule text +
contract excerpts only.

**Fix:** system prompt now states the citable set explicitly — rule_text and
contract_excerpts entries ONLY; column lists are context, not citable
material. A stub test pins the constraint.

## Live E2E #2 — fully clean (the tracked replay run)

3 calls, 0 retries, `end_turn` on all, 15.8s wall. 15,200 input + 735
output tokens ≈ **$0.094**.

| Call | Feed | Input tok | Output tok | Latency | Stop reason |
| --- | --- | --- | --- | --- | --- |
| 1 | cv_community_demographic_risk | 3,003 | 243 | 4.3s | end_turn |
| 2 | cv_community_risk | 10,039 | 234 | 6.8s | end_turn |
| 3 | cv_individual_risk | 2,158 | 258 | 4.2s | end_turn |

All three feeds `PASS_WITH_FLAGS` (candidate-pending + tests-skipped flags
only); all candidates `mappable` with code sketches; **every citation
grounded on every feed** — each cites its rule text verbatim, none cite
column names. Artifacts preserved in `fixtures/replay/live_e2e_20260807/`.

Total spend across both billed runs: **≈ $0.19**.

## Calibration note — token estimates

The recon's chars÷4 heuristic under-estimates real input tokens by ~1.7×
for this workload (e.g. the 23.1 KB `cv_community_risk` prompt ≈ 5.8k
estimated vs 10k actual): the pack is rendered as indented JSON and the
snake_case column lists tokenize heavily. Scale chars÷4 estimates by ~1.7
(or use the token-counting endpoint) when projecting live costs.
