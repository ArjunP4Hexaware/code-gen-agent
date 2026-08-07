# Live-Path Recon — reasoning stage, call profile, UI, E2E, env

> Findings reflect `staging` @ `ba62f20` — the tree immediately before the
> pre-live hardening commit that addresses risks 1–7 below.

Read-only recon ahead of the first live Anthropic E2E. Nothing here changes
code; corrections to stale assumptions are noted inline.

## 1. What the reasoning/review stage consumes and produces

Flow (CLI `generate` / `generate-all` → `src/codegen/cli.py:_generate_feed`):

1. `resolve_pair` joins one FRD + one STTM contract into `ResolvedFeedSpec`s
   (one per feed).
2. `compile_rules` (Layer 1, deterministic) classifies every FRD free-text
   validation rule: `mappable` / `orchestration_config` / `notification` /
   `flagged` / `out_of_scope` / `unmapped`.
3. `run_reasoning` (`reasoning/engine.py`) loops over **only the `unmapped`
   outcomes**. Per rule it builds a `ContextPack`
   (`reasoning/context.py`): the rule text, all contract validation-rule
   excerpts + SLA + frequency strings, and the source/stage/audit column
   name lists. **Inputs are contract-derived text only — generated code is
   never sent to the model.**
4. The provider gets a fixed system prompt (demand: single JSON object
   matching `CandidateResponse`) plus one user message containing the pack
   as indented JSON (`anthropic_provider.py`).
5. Response schema (`reasoning/schema.py::CandidateResponse`, pydantic
   `frozen` + `extra="forbid"`): `classification` (4-value literal),
   `code_candidate: str | None`, `rationale` (non-empty), `citations`
   (non-empty list).
6. `grounding_failures` rejects any citation that is not an exact verbatim
   substring of the rule text or pack excerpts.
7. Output: `RuleCandidate` entries written to
   `out/<feed>/candidates/candidates.json` — a review artifact, never a
   generated module. Provider exceptions become `response=None` candidates
   with a failure note; generation of deterministic modules always proceeds.

Gate coupling (`gate/verdict.py`): candidates can never cause `FAIL`.
`FAIL` comes only from gate checks (ruff / structural / generated tests).
Every candidate contributes a flag — "pending engineer approval",
"NOT grounded", or "provider failed" — so any feed with ≥1 unmapped rule is
at best **PASS_WITH_FLAGS**, live or mock. A live provider changes flag
*content*, not verdict mechanics.

## 2. Call profile of a full live run

Measured in-memory from the actual fixtures (chars ÷ 4 ≈ tokens):

| Feed | Unmapped rules | User-prompt size |
|---|---|---|
| MIDS × 3 feeds (`sd_*`) | 0 | — (no calls at all) |
| `caqh_tpl_inbound_files` | 2 | ~2.1 KB each (~520–530 tok) |
| `cv_community_demographic_risk` | 1 | ~5.7 KB (~1.4k tok) |
| `cv_community_risk` | 1 | ~23.1 KB (~5.8k tok — big column lists) |
| `cv_individual_risk` | 1 | ~4.0 KB (~1.0k tok) |

- System prompt: 773 chars (~190 tok). `max_tokens=4096` output cap per
  call (raised to 8192 by the hardening commit).
- `generate-all` (configured pairs = MIDS + CAQH): **2 calls minimum**.
  CV pair via `generate`: **3 calls**. Everything: **5**.
- Retry loop: `config.reasoning.max_attempts = 2` → worst case **2× (10
  calls total)**; each retry re-sends the grown prompt (previous prompt +
  appended validation error) in a fresh single-message conversation.
- Cost order of magnitude: ≤10 calls × <6k in / ≤4k out — cents.
- Model: read from `config/config.yaml` (`reasoning.model`) →
  `AnthropicProvider.__init__`. **No hardcoded model name anywhere in
  src/tests/ui.** (At recon time the value was `claude-sonnet-5`, never
  validated live; the hardening commit sets the string proven by
  frd-to-sttm's live E2E.)

## 3. The `ui/` directory

- **Stack:** React + TypeScript + Vite frontend (`ui/frontend`, dev server
  :5173) and FastAPI backend (`ui/backend`, uvicorn :8571). Launched as
  **two processes** in two terminals; Vite proxies `/api` → :8571 and the
  backend's CORS allowlist is the Vite dev origin.
- **Real pipeline, mocked provider:** the backend runs the actual
  in-process pipeline (`GenerationStore` mirrors `cli._generate_feed` step
  for step) on startup and via `POST /api/generate` — but hardwired
  `dry_run=True, skip_tests=True`, so the provider is **always mock**.
- **Shows:** verdict dashboard, per-feed detail (rule classifications,
  Layer-2 candidate review with approve/reject persisted to gitignored
  `ui/backend/state/decisions.json`, assembled notebook viewer, generated
  file tree, markdown report), and a 6-step guided demo mode.
- **Databricks-Apps-shaped? No — local-dev-only.** No `StaticFiles` mount:
  the backend never serves the frontend build, so there is no single-port
  mode today. Getting there needs: `npm run build` + a static mount on the
  FastAPI app, dropping the dev-origin CORS, and a `dry_run` knob if live
  Layer 2 should be demoable.

## 4. E2E surface

One invocation runs contract-pair → rules → Layer 2 → emit → gate → report:

```bash
.venv/bin/python -m codegen.cli generate \
  --frd-contract FRD_demo_cv_golden.contract.json \
  --sttm-contract sttm_mapping_contracts_cv_golden.json \
  --skip-tests          # drop --dry-run for the live provider
```

- The CV pair is **not** in `config.contracts.pairs` (those are MIDS +
  CAQH, which `generate-all` covers), so the CV E2E uses `generate`
  explicitly.
- With mock it passes today: 58/58 tests green, and each CV feed has
  exactly 1 unmapped rule → expected `PASS_WITH_FLAGS`.
- Full workbook-to-verdict chain = `extract-sttm` (deterministic) piped
  into `generate` — two commands, no single wrapper.

## 5. Env plumbing

- The CLI ships its own tiny loader — `_load_dotenv` reads `./.env`
  (KEY=VALUE, never overrides existing env vars). No python-dotenv
  dependency.
- Caveat at recon time: only the **CLI** entry point called it;
  `ui/backend/main.py` did not load `.env` (fixed by the hardening
  commit — moot while the UI is mock-hardwired, relevant if it ever goes
  live).
- `.gitignore` already covers `.env` (first entry, "Secrets" block).
  `.env.example` documents `ANTHROPIC_API_KEY` + Databricks vars.

## 6. Live-vs-stub breakage risks in the reasoning stage

Ordered by likelihood of biting on the first real call. All except 8 (which
needs no fix) are addressed by the pre-live hardening commit.

1. **JSON-escaped citations → false "ungrounded".** The pack is shown to
   the model as *indented JSON*, so excerpts containing quotes/newlines
   appear escaped (`\"`, `\n`). A model that copies a citation from what
   it literally sees produces an escaped string that fails the
   exact-substring grounding check against the raw text. Stub never hits
   this (it cites clean strings). Cosmetic normalization (curly quotes,
   collapsed whitespace, `…`) fails the same way. Consequence is a flag,
   not a crash — but it would make live look worse than mock.
2. **`extra="forbid"` + required-key strictness.** Any extra key, or an
   omitted `code_candidate` (must be explicitly `null`), is a
   ValidationError → burns the single retry.
3. **Leading prose.** `_extract_json` tolerated a ```-fenced block but only
   when the response *starts* with the fence; "Here is the JSON:" preamble
   → parse failure → retry.
4. **Fence edge case:** a response starting with ``` but containing no
   newline raised `ValueError` from `str.index` (not ValidationError) —
   escaping the retry loop, recorded as a provider-failure candidate.
   Cosmetic, but noisy.
5. **Truncation:** a verbose `code_candidate` hitting `max_tokens=4096`
   yields invalid JSON → retry with the same cap (likely truncates again).
6. **Non-determinism:** no `temperature` set (SDK default 1.0).
   `candidates.json` is a gitignored artifact so byte-stability doctrine is
   not violated, but live runs would vary run-to-run.
7. **Packaging gap:** `anthropic` is lazy-imported and was **not in
   `pyproject.toml`** (not even an extra) — a live run on a fresh venv
   ImportErrors at provider construction.
8. Fine as-is: SDK/API errors (rate limit, timeout) escape `complete()` and
   are recorded as failure candidates — a live outage degrades to flags,
   never a crashed generation.
