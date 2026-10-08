# Harness Exit Codes

> How `codegen-watch` / `pull_and_run` interpret the exit code returned by
> each `codegen` CLI stage.

## Exit code table

| Code | Meaning | Pair status | Harness behaviour |
| ---: | --- | --- | --- |
| 0 | Success | OK | Continue to next stage |
| 3 | Needs answers | NEEDS_ANSWERS | Record needed answer-key names; **do not stop** — continue to later stages for feeds that produced output |
| Any other non-zero | Failure | FAILED | Record first-error line, stop the pair (do not run later stages) |
| (timeout) | Cumulative timeout exceeded | TIMEOUT | Raise `TimeoutError`, stop the pair |

## Stages affected

Exit code 3 is recognised at **every** stage.  The harness never stops a
pair on exit 3 — it records the stage status as `NEEDS_ANSWERS` and
continues to later stages so that feeds with usable output still run.
Only exit 1 (or another non-zero, non-3 code) or a timeout stops a pair.

| Stage name | CLI command | When code 3 is expected |
| --- | --- | --- |
| `sttm_parse` | `codegen layout` | Workbook layout has unresolved roles that require `answers.yaml` entries |
| `frd_extract` | `codegen extract-sttm` | Nothing usable was written — the contract requires answers before any feed can be extracted |
| `vdd_crosscheck` | `codegen extract-vdd` | VDD layout has unresolved roles |
| `generate` | `codegen generate` | Generation cannot proceed without gap values or pairing decisions in `answers.yaml` |

### CLI rule for `extract-sttm`

`extract-sttm` exits 3 **only when nothing usable was written** (no
contract JSON, or an empty contract with zero feeds).  If the CLI writes
a partial contract (some feeds extracted, some blocked on answers) it
exits 0; the unresolved items appear as `QUESTION` / `UNRESOLVED` lines
in stdout but are not fatal.

## What gets recorded

When any stage returns exit code 3:

1. **Stage status** is set to `NEEDS_ANSWERS` (visible in the per-pair
   Stages table of the run report).  Later stages still run.
2. At the **end of the pair** (after all stages), the harness scans the
   accumulated stdout for `QUESTION` and `UNRESOLVED` lines:
   ```
   QUESTION       sttm stage.schema — reason; candidates [...]
   UNRESOLVED     stage.schema — reason
   ```
   The key is the text between the label and the em-dash separator.
   If any keys are found **or** any stage status is `NEEDS_ANSWERS`,
   the pair's final status is overridden to `NEEDS_ANSWERS` (unless
   the pair timed out).  A consequential exit-1 from a later stage
   (e.g. `generate` failing because `extract-sttm` wrote nothing) is
   also overridden — the root cause is the missing answers.
3. **Pair state file** is written to
   `codegen-state/<pair_id>/status.json` with:
   ```json
   {
     "status": "NEEDS_ANSWERS",
     "sha": "<commit>",
     "timestamp": "<ISO 8601>",
     "needed_answer_keys": ["stage.schema", "stage.table", ...]
   }
   ```
   The state file is written for every pair on every run (not just
   NEEDS_ANSWERS), keeping the on-disk status in sync with the latest
   result.

## Overall run status

The harness computes one overall status from all pair results.  Priority
(highest wins):

```
FAILED > TIMEOUT > NEEDS_ANSWERS > OK
```

A run where some pairs are NEEDS_ANSWERS and others are OK reports
`NEEDS_ANSWERS`.  A run where any pair is FAILED reports `FAILED`
regardless of other pairs' NEEDS_ANSWERS status.

## Providing the missing answers

Place an `answers.yaml` file in the pair's input directory
(`frd_sttm_pairs/pair_<N>/answers.yaml`).  The harness discovers it
automatically and passes `--answers` to every stage that accepts it.
On the next run the CLI should exit 0 for that pair, clearing the
NEEDS_ANSWERS state.

See the existing `pair_1/answers.yaml` for the schema (three top-level
keys: `answers`, `gaps`, `pairing`).
