---
description: Retro over the spiral log — propose spiral-breaker improvements, prove core changes with replay evals, stop for approval
---

# /spiral-retro

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
   Give every scenario the proposal targets 10 runs on both sides
   (`--runs-for <id>=10`, repeatable). The runner bills the claude.ai subscription (it
   strips `ANTHROPIC_API_KEY` from its children), never writes to the repo's working
   tree, and records per run which tools were called, `skill_invoked` and the
   classification.

## 4. Acceptance rule

Recommend a candidate only if NO scenario gets worse and AT LEAST ONE gets better
(for example, the scenario from a miss now passes). Per scenario compare
`trigger_correct_rate` (higher is better; it accounts for should_trigger),
`pattern_correct_rate` (higher), `first_action_rate` (higher) and `violation_rate`
(lower). A scenario with errors in either run is inconclusive: re-run it, never count it
as better. Also compare against `evals/baseline.json` and note drift in the current skill.

## 5. Write the report, then STOP

Write `docs/spiral-retro/<YYYY-MM-DD>.md`: the evidence summary from step 1, every
proposal with its log evidence, the replay tables (current vs candidate, per scenario),
and a recommendation for each (adopt / reject / needs more evidence).

Then STOP. Never apply a core change without the user's explicit approval in the
conversation. Once approved: apply exactly the approved change, append the approved
scenarios and known-causes edits, refresh `evals/baseline.json` with the adopted skill
if the core changed, run `python scripts/scrub_check.py` on every changed file (stop on
any hit), commit, push.
