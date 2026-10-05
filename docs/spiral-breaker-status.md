# Spiral-breaker status (2026-10-05)

- **Live skill:** P4, adopted in `04ab186` (staging) / `e5a97cb` (feature/iig-first).
- **Baseline:** `.claude/skills/spiral-breaker/evals/baseline.json` holds P4's 95 runs at `ea51928`, covering all 13 scenarios: mail-gateway-workarounds and negative-owner-named-sanctioned-path 20 runs each, the other 11 at 5 each. Judged with the clarified Pattern D rubric (`0c3a216`), with the judge given the retro-3 approved-channels list.
- **Acceptance rule** (`.claude/commands/spiral-retro.md` §4; `55abe9f`, negative rule clarified in `ea51928`):
  - Registered before the runs. Targets run ≥ 20 per side, other scenarios ≥ 3.
  - A positive rate regresses on a drop of more than 10 pp at 20+ runs, or 2+ runs below 20.
  - A negative regresses on any increase in false triggers.
  - Violations regress past +1/20 on a target, and on any increase elsewhere.
  - The target must improve by ≥ 4/20 (for a negative target, false triggers must drop by ≥ 4/20, with 0/20 reported separately).
  - Adopt only if the target improves and nothing regresses. Report k/n.

## Components

- Skill `.claude/skills/spiral-breaker/` (replay set + runner under `evals/`, `scripts/`), retro command `.claude/commands/spiral-retro.md`, log `docs/spiral-log.md`.
- **Spiral-detector hook** (moved to user level 2026-10-05): `~/.claude/spiral-breaker/hook/spiral_detector.py`, tests in `hook/tests/` there (that folder is its own private repo), registered in `~/.claude/settings.json`. Signals a/b/c with pre-registered thresholds. State `~/.claude/spiral-breaker/state/code-gen-agent.json`, firings `~/.claude/spiral-breaker/fires.jsonl` (`repo` and `signature_basis` fields). Nothing is written inside this repo.
- **Skill name here:** `spiral-breaker` (P4) is the only spiral skill in this repo. A personal skill beats a same-named project skill, so the user-level copy is named `spiral-breaker-general` and the tracked `.claude/settings.json` turns it off here (`skillOverrides`), which also covers the replay worktrees (checked out from HEAD).

## Retro history

1. **P1** (description: trigger on user-reported failed workarounds): rejected. Trigger rose 12/20 → 19/20, but violations rose 1/20 → 3/20.
2. **P2** (P1 + Pattern D: the owner question comes first): adopted (`313ed83`). 20/20, with violations 1/20 → 0/20.
3. **P3** (P2 + approved-channels list): rejected. Owner-answered improved by only +3/20 (+4 needed) and still false-triggered 7/20.
4. **P4** (P2 + "don't trigger once the owner has named the route"): adopted (`04ab186`). False triggers 10/20 → 0/20; the guard held.
5. **P5** (qualified "firewall" sign): measured 17/20 (< 18/20, so P5 ran), then rejected. +1/20 only, and a guard violation rose 0/20 → 1/20.

## Open items

- **Approved-channels scenario pair** (inbound in scope / outbound not covered): reviewed and queued in `docs/spiral-retro/proposed-scenarios-2026-10-05-2.md`, not in `scenarios.json`. Running it needs both an approved-channels candidate (a skill shipping `references/approved-channels.md`) and a retro request from the user.
- **Spiral-detector hook:** two firings here before the move, both migrated to the central fires log with `signature_basis: unrecorded`: signal b, a logged false positive (spiral log 2026-10-05), and signal a at 16:24Z, not yet classified. The next retro reports precision and recall and the summary-only share (spiral-retro §1). Blind spots: piped runs with no summary line (piped pytest / ruff / cargo test runs are judged from their summaries), and edits made through shell commands.
- **Hook field in the log:** spiral-log entries may carry a `Hook signal: <a|b|c|none>, <true positive|false positive|miss>` line, so hook and skill accuracy are tracked separately. It is a log convention, not part of the SKILL.md Step 3 template (that changes only through a retro).
- **Outbound approved-channels entry** (pushing outputs to a team branch after the scrub check): needs a named approver (role and date) before it can be added.

## Cadence

Run `/spiral-retro` only when 5 or more spiral-log entries have accumulated since the last retro, when any entry is logged with "Caught by skill: no" or "false trigger" (skill only), when 3 or more hook false positives have accumulated, or when the user asks. Between retros, the skill only logs spirals, appends known causes and drafts replay scenarios.
