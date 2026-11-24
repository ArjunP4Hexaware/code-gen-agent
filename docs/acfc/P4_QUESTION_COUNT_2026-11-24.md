# P4 — questions per pair, before / after the question UX work (2026-11-24)

P4 of the plan agreed 2026-11-19 (P1 = post210, P2 = post216, P3 = post218): the measure.
**Before** = post209 (83a336a, the last version before P1); **after** = post218 (deada62;
post219 / post220 change no question). Counts only - no client values.

## Method

- Pairs 1-17 (Workspace `frd_sttm_pairs`; 13-17 = staging uploads), copies in /tmp,
  deleted after. Mock provider (`--dry-run`), **no stored answers** (what a first-time
  user meets), each tree from its own worktree and its own copy of the state dir.
- **The dialog:** `codegen layout --json --no-cache` per pair -> `questions[]`; a
  question's choices = its `candidates` (the App adds no cells: `typed_frd_question`
  only adds the text box - present since post206, so on both sides - and the
  `(leave blank)` choice where the field allows it).
- **The run:** `scripts/container_harness.py` per tree -> each pair's "Needed answers"
  (the blocking keys the run stops on, generate-stage questions included), deduped.
- Not measured: the layout model's live proposal (mock makes none; P2 always offers it,
  so a live run can show one more choice per FRD question). The testers' pairs A / B / C
  (the ones that motivated P1-P3) were never stored, so they are not in the set.

## The dialog (layout questions)

| | post209 | post218 |
|---|---|---|
| questions, pairs 1-17 | 40 | 39 |
| of them FRD questions | 29 | 28 |
| choices offered, total | **649** | **64** |
| questions offering the SAME list as another question | 27 | 12 |
| FRD questions with no list (a typed answer) | 0 | 14 |

Only pairs 8, 9 and 10 move (every other pair: identical counts):
- pair_08: 4 FRD questions x 58 identical cells -> a typed answer each (no list).
- pair_09: 5 FRD questions x 67 identical cells -> a typed answer each.
- pair_10: 18 -> 17 questions (the post208 feed-name question gone, P1); 6 FRD role
  questions x 3 identical cells -> 5 typed answers; its 8 two-document `choice`
  questions (2 values each) and 4 STTM column questions unchanged.
- The 12 questions still sharing a list after: pair_10's 8 choice questions (the same
  two documents' values) and pair_17's STTM column questions (one sheet's header row) -
  both expected.

## The run (blocking keys, no answers)

| | post209 | post218 |
|---|---|---|
| blocking keys, pairs 1-17 | 23 | 57 |
| outcomes | identical (8 NEEDS_ANSWERS, 6 PASS_WITH_OPEN_INPUTS, 2 GATE_FAIL, 1 FAIL) | same |

Every pair the same except **pair_17: 7 -> 41**. The +34 are
`feeds[i].columns[j].standard_type` - post213's question for a standard type cell that is
no type (it CRASHED the run before; pair_17 joined the check only on 2026-11-23). All 34
cells hold the SAME text: a person answers one question 34 times.

## Findings

1. P1-P3 did what they were for: FRD questions no longer offer a document's every cell
   (649 -> 64 choices; the 58- and 67-cell lists are gone), with no question added.
2. **Done (post221):** post213's standard-type question is asked per cell; identical
   cell texts could be ONE question (one answer applied to every cell that reads it) -
   pair_17: 34 -> 1. **Built as post221** (Soham: "go ahead and group"): pair_17's
   open questions 38 -> 5, standard_type 34 -> 1; no other pair moved.
