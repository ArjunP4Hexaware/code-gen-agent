# Live E2E replay set — 2026-08-07

Artifacts of the first fully clean **live** Layer-2 run (real Anthropic API,
`claude-opus-4-8`) over the CV/golden contract pair. Intended for a future
demo Replay mode: everything needed to reconstruct the results view without
a key or network. Full narrative: `docs/LIVE_RUN_RECORD.md`.

Produced by (from the repo root, `.env` holding a real key):

```bash
.venv/bin/python -m codegen.cli generate --config config/config.yaml --skip-tests \
  --frd-contract FRD_demo_cv_golden.contract.json \
  --sttm-contract sttm_mapping_contracts_cv_golden.json
```

Layout — one directory per resolved feed, discoverable by globbing
`fixtures/replay/*/<feed_slug>/`:

| File | Contents |
| --- | --- |
| `call_log.json` | Per-API-call model, prompt size, input/output tokens, latency, stop reason |
| `<feed_slug>/candidates.json` | The Layer-2 review artifact (provider `anthropic`, all grounded) |
| `<feed_slug>/report.md` | The generation report incl. gate verdict (all PASS_WITH_FLAGS) |

All three candidates classified their rule `mappable` with a PySpark sketch
and a single verbatim rule-text citation; every citation passed grounding.
Verdicts are PASS_WITH_FLAGS by design (candidates pending engineer
approval + generated tests skipped), not failures.

Unlike generated output, live model output is non-reproducible run to run
(sampling params are rejected by this model family) — these files are a
snapshot, not a byte-stable expectation. Do not regenerate over them.
