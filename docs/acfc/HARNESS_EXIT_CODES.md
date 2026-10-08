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
| `sttm_parse` | `codegen layout --require-complete` | Workbook layout has unplaced columns (unresolved roles) or open questions that require `answers.yaml` entries — one `UNRESOLVED` / `QUESTION` line each. Layout is the first stage, so this exit 3 is the only way a pair with unplaced columns reads `NEEDS_ANSWERS` instead of `FAILED` |
| `frd_extract` | `codegen extract-sttm` | Nothing usable was written — the contract requires answers before any feed can be extracted |
| `vdd_crosscheck` | `codegen extract-vdd` | **Not today**: `extract-vdd` never exits 3 — VDD role gaps surface as gate flags on the feed (`vdd_*`), not as answers. Exit 3 here is planned, not implemented; treat its non-zero exits as `FAILED` |
| `generate` | `codegen generate` | Generation cannot proceed without gap values or pairing decisions in `answers.yaml` |

### CLI rule for `extract-sttm`

`extract-sttm` exits 3 **only when nothing usable was written** (no
contract JSON, or an empty contract with zero feeds).  If the CLI writes
a partial contract (some feeds extracted, some blocked on answers) it
exits 0; the unresolved items appear as `QUESTION` / `UNRESOLVED` lines
in stdout but are not fatal.

## Line format

The CLI emits structured lines with the label padded to 15 columns:

```
QUESTION       <key> — <reason>
UNRESOLVED     <key> — <reason>
```

The Python f-string producing these lines is:

```python
print(f"{'QUESTION':<15} {key} \u2014 {reason}")
print(f"{'UNRESOLVED':<15} {key} \u2014 {reason}")
```

The harness parses them with the following compiled regex
(`_NEEDED_KEY_RE` in `pull_and_run`):

```python
_NEEDED_KEY_RE = re.compile(
    r"^(?:QUESTION|UNRESOLVED)\s+(.+?)(?:\s+\u2014\s|$)"
)
```

Capture group 1 is the **key** (the text between the label and the
em-dash separator).  Lines without an em-dash (e.g. bare `UNRESOLVED`
items) match via the `$` alternative.

## What gets recorded

At the **end of every pair** (after all stages have run or the pair has
been stopped), the harness **always** scans the pair’s accumulated
stdout for `QUESTION` and `UNRESOLVED` lines using `_NEEDED_KEY_RE`,
regardless of exit codes.

1. **Stage status** is set to `NEEDS_ANSWERS` (visible in the per-pair
   Stages table of the run report) for any stage that returned exit
   code 3.  Later stages still run.
2. **Stdout scan** runs unconditionally.  If any keys are found **or**
   any stage status is `NEEDS_ANSWERS`, the pair’s final status is
   overridden to `NEEDS_ANSWERS` — even when every stage exited 0.
   Exit code 3 is a stage-level signal, not the only trigger.  When a
   pair is `FAILED` and keys are found, see “When an exit 1 is
   reclassified” below for the narrowed override.
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
   A pair that stays `FAILED` under the rule below records BOTH the error
   and the keys:
   ```json
   {
     "status": "FAILED",
     "sha": "<commit>",
     "timestamp": "<ISO 8601>",
     "failed_stage": "generate",
     "first_error": "FAIL            template gap: …",
     "needed_answer_keys": ["feeds[2].stage_target.tables", ...]
   }
   ```
   The state file is written for every pair on every run (not just
   NEEDS_ANSWERS), keeping the on-disk status in sync with the latest
   result.

## When an exit 1 is reclassified (2026-10-08)

A later stage's exit 1 in a pair that already has a `NEEDS_ANSWERS` stage
(or `QUESTION` / `UNRESOLVED` keys) is reclassified as `NEEDS_ANSWERS`
**only when its first-error line says the stage's INPUT is missing because of
those answers** — the consequence, not a new failure. The first-error line is
the first stdout line starting `FAIL` (else the first stderr line). It is
reclassified when it matches one of (case-insensitive):

| Class | First-error line contains | Typical cause |
| --- | --- | --- |
| no contract | `contract not found:` | `generate` (or `extract-sttm`, whose FRD contract the layout stage writes) reading a contract an earlier stage did not write because every feed needed answers |
| no feeds | `no resolved feed matches --feed` / `produced no feeds` | the feeds the stage was given were all held back for answers |
| missing answers | `under gaps:` (or ``under `gaps:` ``) / `NEEDS_ANSWERS` | the stage stops on a value only the answers file can supply (the line names the key) |

Where the line names a path (`contract not found: <path>`), the path must be
the output of an earlier stage of the SAME pair — a contract that was never
going to exist is not a consequence of the missing answers.

**Any other exit 1 stays `FAILED`**, even in a pair that needs answers (a
gate FAIL, a template gap, a parse error, a traceback — and a MALFORMED
answers file: `FAIL layout — answers file: …` / `FAIL pair — answers file: …`
is a failure, not a missing answer, which is why the class keys on
`under gaps:` and never on the words "answers file" alone): the pair status is
`FAILED`, the stage's `first_error` AND the pair's `needed_answer_keys` are
both recorded (state file above, and the run report's per-pair row), so the
engineer sees the real failure and the answers still owed. Priority below is
unchanged: `FAILED` wins over `NEEDS_ANSWERS`.

Where each class comes from in the `codegen` CLI (`code-gen-agent`,
`feature/multi-table`, `src/codegen/cli.py`):

- no contract — `FAIL            contract not found: <path> (also tried …)`
  (`_contract_path`: `generate` / `extract-sttm` given a contract file that
  does not exist).
- no feeds — `FAIL            no resolved feed matches --feed '<feed>'`
  (`_run_pairs`); the App's `live run produced no feeds — …`.
- missing answers — a line carrying `NEEDS_ANSWERS` or `under gaps:`. At exit
  1 the CLI rarely prints one first: the resolver's stops are MULTI-line —
  `FAIL … — contract mismatch for feed '<x>':` then one `  - <error>` line
  each — so their first-error line names no class and they stay `FAILED`
  (keys recorded) by design, even when a bullet names a `gaps:` key: the
  first-error line rule is deliberately conservative.

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
