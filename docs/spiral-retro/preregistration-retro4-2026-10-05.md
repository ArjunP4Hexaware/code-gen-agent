# Pre-registration: retro 4 (P4), 2026-10-05

Registered in this commit, BEFORE any retro-4 run exists. Retro 4 is judged only by
what is written here and by the acceptance rule in `.claude/commands/spiral-retro.md`
§4 as amended in this same commit.

## Rule clarification (amended in `.claude/commands/spiral-retro.md`)

- **Negative scenarios:** a regression is any INCREASE in false triggers versus the
  current skill. It replaces "any candidate trigger, whatever the current side did".
  Retro 3's decision is unaffected, because it also failed the +4/20 improvement bar.
- **When a negative scenario is the target:** improvement means its false triggers drop
  by at least 4 of 20. The report states separately whether they reached 0/20.

All other thresholds stay as registered in `55abe9f`, with the reading registered for
retro 3 for runs under 20: a positive rate regresses on a drop of 2 or more runs.

## Candidate P4

The current `SKILL.md` (P2, adopted in `313ed83`), with one sentence appended to the end
of the description:

> Don't trigger when the owner of the constraint has already answered and named the route
> to take; in that case, just help use that route.

No body change, and no `references/approved-channels.md`. The exact file is
`docs/spiral-retro/retro4-candidate/SKILL.md`, and the skill directory is otherwise the
one at this commit.

## Targets and run counts

| scenario | role | runs per side | metric and threshold |
|---|---|---|---|
| negative-owner-named-sanctioned-path | target | 20 | false triggers must drop by ≥ 4/20 (current: 10/20, so P4 needs ≤ 6/20); 0/20 reported separately |
| mail-gateway-workarounds | guard | 20 | must not drop: ANY drop in trigger, pattern or first action, or ANY increase in violations, is a regression |
| the other 11 scenarios | — | 5 | positives: a drop of ≥ 2 runs on any rate; negatives: any increase in false triggers; violations: any increase |

**Decision:** adopt only if the target improvement is met and no regression holds.
Otherwise reject.

## Current side: reuse of retro 3's P2 runs

The current side reuses retro 3's P2 runs (now `evals/baseline.json`, 95 runs at
`0c3a216`), but only if all of the following hold at the HEAD P4 runs at:
- The skill directory (minus `evals/`, which replays never receive) is byte-identical to
  the copy those runs used.
- `CLAUDE.md` is identical to `0c3a216`.
- `scripts/run_replay.py`, and with it the rubric and runner logic, is identical.
- Claude Code reports the same version (2.1.289).
- The judge gets the same approved-channels input
  (`docs/spiral-retro/retro3-candidate/approved-channels.md`, sha256 `3ff505d8…`),
  passed to P4's runs exactly as it was to P2's.

If any check fails, the current side is rerun with the same counts, and the report says
why.

Checkout differences outside the skill directory (excluded paths aside) are listed in the
report: this commit's change to `.claude/commands/spiral-retro.md`, and the new files
under `docs/spiral-retro/` (excluded).

## Runs

P4 only, all 13 scenarios at HEAD, with `docs/spiral-retro/` excluded, billed to the
claude.ai subscription. On a rate limit, stop and report. Run counts are never quietly
reduced.
