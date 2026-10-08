# Harness Exit Codes

> How `codegen-watch` / `pull_and_run` interpret the exit code returned by
> each `codegen` CLI stage.

## Exit code table

| Code | Meaning | Pair status | Harness behaviour |
| ---: | --- | --- | --- |
| 0 | Success | OK | Continue to next stage |
| 3 | Needs answers | NEEDS_ANSWERS | Record needed answer-key names, persist pair state, stop the pair (do not run later stages) |
| Any other non-zero | Failure | FAILED | Record first-error line, stop the pair |
| (timeout) | Cumulative timeout exceeded | TIMEOUT | Raise `TimeoutError`, stop the pair |

## Stages affected

Exit code 3 is recognised on two stages only:

| Stage name | CLI command | When code 3 is expected |
| --- | --- | --- |
| `frd_extract` | `codegen extract-sttm` | Workbook layout has unresolved roles that require an `answers.yaml` entry |
| `generate` | `codegen generate` | Generation cannot proceed without gap values or pairing decisions listed in `answers.yaml` |

All other stages (`sttm_parse`, `vdd_crosscheck`) treat every non-zero exit
code as FAILED, unchanged from the original behaviour.

## What gets recorded

When a stage returns exit code 3:

1. **Stage status** is set to `NEEDS_ANSWERS` (visible in the per-pair
   Stages table of the run report).
2. **Pair result** gains a `needed_answer_keys` list, extracted from
   `QUESTION` and `UNRESOLVED` lines in the CLI's stdout:
   ```
   QUESTION       sttm stage.schema \u2014 reason; candidates [...]
   UNRESOLVED     stage.schema \u2014 reason
   ```
   The key is the text between the label and the em-dash separator.
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
