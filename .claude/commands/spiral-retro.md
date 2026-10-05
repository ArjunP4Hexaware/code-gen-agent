---
description: Retro over the spiral log — propose spiral-breaker improvements, prove core changes with replay evals, stop for approval
---

# /spiral-retro

## When to run

Run a retro only when (a) 5 or more spiral-log entries have accumulated since the last
retro, or (b) any entry is logged with Caught by skill: no or false trigger (the
SKILL's misses and false triggers only; a hook false positive alone does not count),
or (c) the user asks, or (d) 3 or more hook false positives since the last retro
(entries whose `Hook signal:` line says false positive). One hook false positive is not
enough evidence to retune the hook's thresholds. Between retros, the skill only logs
spirals, appends known causes, and drafts replay scenarios.

## What a retro does

Improve the spiral-breaker skill from evidence. You may PROPOSE changes to it; the replay
set decides whether a core change is better, and the user approves every core change.
All content you write stays generic: no client names, feed names or document contents.

Paths: skill `.claude/skills/spiral-breaker/` (core = `SKILL.md`), known causes
`references/known-causes.md`, replay set `evals/scenarios.json`, baseline
`evals/baseline.json`, runner `scripts/run_replay.py`, log `docs/spiral-log.md`,
reports `docs/spiral-retro/<YYYY-MM-DD>.md`.

## 1. Read the evidence

Find the newest report in `docs/spiral-retro/`. Read the `docs/spiral-log.md` entries
dated after it (all entries if there is no report). Summarize:
- catches (`Caught by skill: yes`)
- misses (`Caught by skill: no (noticed afterward)`)
- false triggers (`Caught by skill: false trigger`)
- entries whose cause fit none of the four patterns

Then compare the spiral-detector hook's firings (`.local/spiral-hook-fires.jsonl`,
local only, written by `.claude/hooks/spiral_detector.py`) dated after the last
report against the same log entries:
- **precision**: firings that matched a logged spiral, out of all firings (a firing
  with no logged spiral is a false alarm, or a spiral nobody logged; say which);
- **recall**: logged spirals that a firing preceded, out of all logged spirals in the
  window (a spiral logged with no earlier firing is a hook miss).
Report both as k/n, broken down by signal (a / b / c). The hook's thresholds are
pre-registered at the top of the script; propose a threshold change only from these
counts, and treat it like a core change (stop for approval). The fires log holds no
command output; quote from it freely, but never paste command output into the report.

Then read the replay evidence: `evals/baseline.json` and any fresh replay of the current
skill. List every positive scenario with a trigger rate under 100% and every negative
scenario with a trigger rate above 0%. Before proposing anything for such a scenario,
diagnose it: replay it at least 10 times and use each run's `classification`
((a) skill never loaded, (b) loaded but no SPIRAL CHECK or the wrong pattern, (c) pass)
to decide whether the description, the skill body, or the scenario itself is at fault.

## 2. Draft proposals, each with the log evidence behind it

- **Known-causes cleanup**: merge duplicate entries, sharpen signatures, add dates to
  Seen lines. Only from log text; never invent details.
- **New replay scenarios** for every log entry that lacks one (match on `source`). Same
  format as the existing entries; the prompt starts with "Don't change any files in
  this session.", describes the symptom plus the two failed fixes generically, and uses
  the must_not of the existing scenarios of the same kind.
- **Core changes** (pattern wording, a new pattern, the trigger description) ONLY when
  backed by evidence: a miss, a false trigger, 2+ entries that fit no pattern, or a
  replay result (a positive scenario under 100% trigger rate, a negative above 0%). No
  evidence, no core proposal. Match the change to the diagnosis: mostly (a) → a minimal
  change to the description; mostly (b) → a minimal change to the body section that
  applies.
- **Scenario rewording** only when the diagnosis shows the scenario itself is ambiguous
  or unfair. Flag it separately from core changes: a test changed until it passes is
  the one change that can fake an improvement. Explain exactly why the old wording was
  unfair, and never make it pass by putting the expected answer (pattern name, the
  skill's own phrases, the expected first action) into the prompt.

Known-causes and scenario additions are not core changes; they need no replay but do
need the user's review in the report.

## 3. Replay every proposed core change

For each core proposal:
1. Copy `.claude/skills/spiral-breaker/` to a temp directory OUTSIDE the repo and apply
   the change there. Never edit the real `SKILL.md` at this stage.
2. Run the runner from the repo root on BOTH skills, full scenario set (including the
   scenarios proposed in step 2, written to a temp copy of the scenarios file):
   ```
   python .claude/skills/spiral-breaker/scripts/run_replay.py --skill-dir .claude/skills/spiral-breaker --scenarios <scenarios> --runs 3 --out <tmp>/current.json
   python .claude/skills/spiral-breaker/scripts/run_replay.py --skill-dir <tmp>/candidate --scenarios <scenarios> --runs 3 --out <tmp>/candidate.json
   ```
   Give every scenario the proposal targets 20 runs on both sides
   (`--runs-for <id>=20`, repeatable; see the acceptance rule). The runner bills the claude.ai subscription (it
   strips `ANTHROPIC_API_KEY` from its children), never writes to the repo's working
   tree, and records per run which tools were called, `skill_invoked` and the
   classification.

## 4. Acceptance rule (noise-aware, pre-registered 2026-10-05)

This rule is fixed BEFORE a candidate's replay data exists. Never adjust it after
seeing results; a rule change is its own commit, made before the runs it will judge.

Before running, name the candidate's **target scenario(s)** and its **target metric**,
from the diagnosis: (a) not loaded → `trigger_correct_rate`; (b) loaded but no check or
wrong pattern → `pattern_correct_rate` or `first_action_rate`, whichever the (b) runs
failed.

Run sizes: every target scenario at least **20 runs per side**; every other scenario at
least 3 runs per side. All counts below are runs, out of the runs actually made (k/n).

**Regressions.** A candidate is rejected if ANY of these holds:
- *Positive scenario, any of trigger / pattern / first-action rate:* the drop is more than
  10 percentage points at 20+ runs (more than 2 of 20), or 2 or more runs at 3 runs per
  side.
- *Negative scenario:* any INCREASE in false triggers versus the current skill (clarified
  2026-10-05 before retro 4; until then any candidate trigger counted, whatever the
  current side did). Its first-action rate follows the positive thresholds above.
- *Violations (`violated_must_not`):* on a target scenario, an increase of more than 1 of
  20 (more than 5 percentage points); on any other scenario, any increase.

**Improvement.** The target metric on the target scenario must improve by at least 4 of
20 runs (20 percentage points). When the target is a negative scenario, improvement
means its false triggers drop by at least 4 of 20; the report also states separately
whether they reached 0/20.

**Decision.** Adopt only if no regression holds AND the improvement threshold is met;
otherwise reject. There is no "needs more evidence" outcome once the pre-registered run
sizes are reached. A scenario with errors in either side is inconclusive: re-run it up to
the required count before deciding, and never count an errored run as better.

Report every metric as raw counts **k/n** per side (rates alone are not enough), plus
the hash of the commit that registered this rule. Also compare against
`evals/baseline.json` and note drift in the current skill.

## 5. Write the report, then STOP

Write `docs/spiral-retro/<YYYY-MM-DD>.md`: the evidence summary from step 1 (including
the hook's precision and recall), every
proposal with its log evidence, the replay tables (current vs candidate, per scenario),
and a recommendation for each (adopt / reject / needs more evidence).

Then STOP. Never apply a core change without the user's explicit approval in the
conversation. Once approved: apply exactly the approved change, append the approved
scenarios and known-causes edits, refresh `evals/baseline.json` with the adopted skill
if the core changed, run `python scripts/scrub_check.py` on every changed file (stop on
any hit), commit, push.
