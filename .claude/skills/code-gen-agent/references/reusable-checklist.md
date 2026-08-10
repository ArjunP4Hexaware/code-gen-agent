# Reusable checklist — building an approved-spec → code agent

The Part B essentials from `SKILL.md`, expanded into a build-order
checklist. Use this when scaffolding an equivalent agent for a different
client, domain, or artifact type. The order matters — later steps assume
earlier ones are stable.

## 0. Confirm the pattern fits

Skip this pattern unless **all** hold:

- Input is an **approved, machine-readable** artifact (JSON/YAML/proto/
  OpenAPI/CSV/xlsx-with-schema), not a free-form prompt.
- Output is **executable** (code, SQL, IaC, config) — correctness is
  provable by lint/type/test.
- There is a **downstream consumer** (reviewer, deployer, another agent)
  whose contract with your output must be stable.
- Same input must yield identical bytes on regeneration.

If any of those fail, use a different pattern.

## 1. Schema the input contracts first

- Strict schema library that **fails loud on unknown fields** (pydantic
  v2 `extra="forbid"`, JSON Schema `additionalProperties: false`, protobuf
  proto3 with `unknown_fields=strict`, etc.).
- Frozen / immutable models — the agent must not mutate its input.
- Missing = `None` / `null`, never a silent default. If the spec doesn't
  say it, the agent must know the spec didn't say it.
- Commit at least one real + one synthetic fixture per contract dialect
  under `fixtures/contracts/`.

## 2. Write the resolver / join before any emitter

- If your agent takes more than one artifact, define the join invariant
  (this repo: `feed_id = normalize_feed_name(FRD.feed_name)`) and put it
  behind one function.
- Disagreements between artifacts must raise a typed error
  (`ContractMismatchError`), not warn-and-continue.
- The resolver's output is a single flat `ResolvedSpec` object that the
  emitter and gate both consume.

## 3. Build the deterministic classifier

- Anything the spec expresses in structured fields is Layer 1.
- Anything free-text that the classifier recognizes (regexes, keyword
  tables, small state machines) is Layer 1.
- What the classifier cannot classify is tagged `unmapped` and becomes
  the **only** input Layer 2 will ever see.
- Test the classifier extensively — every ambiguity here is one Layer 2
  will have to reason about later.

## 4. Deterministic emitter (Layer 1)

- Templating engine with no logic beyond spec-pinned facts (Jinja2, Go
  templates, Handlebars — anything without arbitrary computation in the
  template).
- **No timestamps, no `random`, no clock reads.** Inject any date the
  output needs. Same input, same bytes.
- Emit a **provenance banner** in every file: input artifact names +
  content hashes.
- Emit a linter/type-checker config alongside so generated code is held
  to the same standard as the generator source (`ruff.toml`, `.eslintrc`,
  `pyrightconfig.json`, etc.).
- Byte-compare emitter output against a committed golden fixture in CI.

## 5. Layer-2 reasoning (LLM in a bounded corner)

- **Mock provider is the default**; live provider requires both `API_KEY`
  present AND `--dry-run` off. Tests and dev loops run offline.
- Layer 2 output lands in a **review artifact** file
  (`candidates.json` or similar), not in generated modules.
- **Verbatim grounding check**: every citation the model produces must be
  found literally in the source text; failed grounding rejects the
  candidate. Do not accept paraphrases.
- No temperature / sampling knob unless you are willing to defend the
  variance to your reviewer.
- Provider abstraction (`build_provider`) so the mock and live paths
  share one interface.

## 6. Gate + verdict

- Fixed verdict enum with **at least three states**: `PASS`,
  `PASS_WITH_FLAGS`, `FAIL`. The middle state is essential — it is where
  clean-but-needs-human lives.
- Preflight checks on the *generated* code: lint, debug-pattern scan,
  secret scan, test-per-module presence.
- If a runtime is reachable in CI, actually run the generated tests.
- The gate computes the verdict from its own outputs; no human decision
  at the end.
- Publish the same verdict vocabulary to every agent downstream so they
  interpret it identically.

## 7. Config doctrine

- One config file. Loud on typos.
- No numeric literals in generator logic — if you see `if x > 3:` in the
  emitter, `3` belongs in config.
- Secrets only via `.env` / secret manager; `.env.example` documents the
  names.

## 8. Report + review surface

- Per-input generation report (markdown): verdict, gate checks, flagged
  items, links to Layer-2 candidates.
- Demo UI or CLI that can load a full past run byte-for-byte. Which
  brings us to:

## 9. Replay fixtures

- Commit at least one full run of *real* model output as a tracked
  fixture (`fixtures/replay/<run_id>/`).
- Include a `call_log.json` per fixture (model, tokens, latency, stop
  reason) so cost/latency claims have a receipt.
- The UI/CLI Replay path loads these with zero API calls, zero network.
  This is your contingency when a live demo can't reach the model.

## 10. Isolate live output; never let it clobber fixtures

- Live runs write to a timestamped directory (`out/demo_<timestamp>/` in
  this repo). Never to the default output tree, never to the replay
  fixtures.
- Confirm-before-cost dialog on any billed action.
- A crashed live run releases whatever single-run guard you introduce
  and marks its directory failed; do not let it load as if successful.

## 11. Human-in-the-loop finale

- The engineer approves Layer-2 candidates in the UI; approval **does
  not self-merge** into generated code. Merging is a manual step.
- Approval state is scoped to the run, not global — approvals from one
  run must not appear against another.
- Say this out loud in the demo: the agent proposes, the engineer
  confirms, and even an approval doesn't self-merge. This is the audit
  line the whole design exists to preserve.

## Anti-patterns to reject

- Layer 2 writing directly into generated modules "just this once."
- Silent defaults for missing spec fields.
- Single boolean pass/fail gate.
- Free-form prompt input alongside the structured spec.
- Any run-to-run variation source in Layer 1.
- Re-adding a temperature knob to reduce or increase variance without
  changing the review contract.
