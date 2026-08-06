# Workflow: contracts → generated pipeline → reviewed PR

How generated code travels from this agent to production. The generator
never merges anything itself; an engineer owns every PR.

## 1. Generate

```bash
# all configured contract pairs
.venv/Scripts/python -m codegen.cli generate-all --config config/config.yaml

# one pair / one feed
.venv/Scripts/python -m codegen.cli generate \
  --frd-contract "FRD_Medicare Expansion-MIDS - Socially Determined.contract.json" \
  --sttm-contract sttm_mapping_contracts.json \
  --feed sd_individual_risk
```

Per feed this produces:

| Path | What |
|---|---|
| `out/<feed_slug>/pipeline/` | PySpark modules (feed_spec, reader, drift, mapping, audit, rejects, writer, dq, orchestrator, + segments/reference/recycle where the contracts call for them) |
| `out/<feed_slug>/ddl/` | `CREATE TABLE IF NOT EXISTS … USING DELTA` scripts |
| `out/<feed_slug>/job/` | Databricks Workflows JSON + notebook entrypoint |
| `out/<feed_slug>/tests/` | pytest suite (real local Spark + Delta), one test file per pipeline module |
| `out/<feed_slug>/candidates/candidates.json` | Layer-2 (LLM) candidates for rules the deterministic compiler could not map — **review artifact, never wired into modules** |
| `reports/<feed_slug>.md` | generation report: contracts + sha256, rule table with grounding, candidates, gate checks, verdict |

Every generated file carries a provenance banner (contract names + sha256).
Renders are byte-stable: same contracts in, same bytes out.

## 2. Read the gate verdict

Printed per feed and written into the report:

- **PASS** — every rule compiled deterministically, ruff clean, generated
  tests pass, nothing pending.
- **PASS_WITH_FLAGS** — output is usable but something needs a human:
  Layer-2 candidates awaiting approval, rules flagged as contradicting the
  STTM, notification rules (config carries no recipients yet), or tests
  skipped. **Read the flags in the report before raising a PR.**
- **FAIL** — do not ship: contract mismatch, template gap, lint failure, or
  generated tests failing. Fix contracts (or the generator) and regenerate.

With the current fixtures all four feeds land on PASS_WITH_FLAGS — that is
correct, honest behavior (every feed has flagged/notification/unmapped
rules).

## 3. Engineer reviews and decides

- Confirm flagged rules against the source teams (e.g. a rule naming a
  column the feed's STTM does not carry — see `_provenance.ambiguities` in
  the FRD).
- Review `candidates/candidates.json`: each entry shows the provider,
  whether every citation passed the verbatim grounding check, rationale,
  and a sketch. Approving a candidate means implementing it yourself in a
  follow-up commit (v1 has no auto-merge mechanism — deliberately).
- Never hand-edit files under `out/` (the banner says so): fix the
  contracts or templates and regenerate, otherwise the next run silently
  reverts your edit.

## 4. Raise the PR

Copy the feed's `out/<feed_slug>/` tree into the target pipeline repo per
that repo's layout, plus the generation report in the PR description. The
PR then goes through the **Code Review Agent** (sibling repo), whose checks
the gate pre-flights: ruff, debug-statement scan, secrets scan, structural
test-per-module check, tests.

## 5. Regeneration

When a contract changes (e.g. the real CAQH STTM replaces the synthetic
stand-in): update `config.contracts.pairs`, rerun `generate-all`, diff
`out/` in the PR — the sha256 in every banner shows exactly which contract
version produced which code.
