# Model / harness evaluations (2026-11-03 → 04)

Offline-graded, live-model experiments on this repo's own work. Each one spends Databricks
model DBUs (Opus 5.5 / Haiku 5.5 through the FMAPI endpoint Claude Code uses), so run them
only on Soham's word, with the caps below. Results and diffs are written under `/tmp/t/...`
(never committed); the conclusions are in `docs/CLAUDE_HISTORY.md` §[H19].

The scripts were written in `/tmp/t/` and copied here unchanged, so their paths still point
there. To rerun: `mkdir -p /tmp/t && cp -r tools/model_eval/replay /tmp/t/eval &&
cp -r tools/model_eval/agents_md_split /tmp/t/agtest`, then follow each section.

## `usage.py` — what a Claude Code session costs

`python3 -I tools/model_eval/usage.py` reads the local transcripts
(`~/.claude/projects/**/*.jsonl`, wiped on a container restart) and prints tokens, DBU by
price line (input / output / cache read / 5-min and 1-h cache writes), the cache-hit rate
and the gaps between requests. Rates: databricks.com proprietary FM serving page
(2026-11-03). Counts only, no content.

## `replay/` — Opus vs Haiku vs Opus-lead + Haiku-worker on past fixes

`tasks.py`: four past fixes (6c05d20, cba0759, 782bebf, 4a06ade) with symptom-only briefs
(synthetic fixtures). `oracle_check.sh`: each hidden test fails on `<commit>^` and passes on
`<commit>`. `run.py`: one worktree per (task, arm) at `<commit>^`, `claude -p` headless,
git hooks off, a DBU watchdog per run (Opus / hybrid $7, Haiku $3). `grade.py`: hidden
test, the run's own tests must fail without its fix, full suite vs the unfixed baseline,
ruff, hygiene (`--no-suite` for the fast part). Then a blind review: anonymised diffs +
the reference fix per task to one Opus reviewer.

Result (1 run each): mergeable fixes Opus medium solo 4/4 ($1.21 per mergeable fix),
Haiku xhigh solo 1/4 ($2.77), hybrid 2/4 ($2.59). Pilot cost $12.78 + ~$2 review.

## `agents_md_split/` — does moving AGENTS.md's reference sections out cost reliability?

`make_split.py <tree>`: keeps the rules, moves six reference sections into
`.claude/skills/codegen-reference/SKILL.md`. `probes.py`: six requests that tempt a
violation of a rule living in a moved section (config knob vs literal, coordinates-only
errors, CREATE OR REPLACE, a COMMENT from a Comments cell, the one generate entry point,
`''` vs `\'`). `run.py`: 6 probes × {full, split} × 2 runs, Opus medium, $2 per run, $30
total cap.

Result: no rule violation in either arm (12 / 12 each), the skill was loaded 12 / 12,
split 15% cheaper on these short runs ($8.09 vs $9.50). Not adopted: in multi-hour
sessions that touch `src/` the skill is loaded anyway (saving ~$15-30 / month), and a
loaded skill can be summarised away by compaction while AGENTS.md is re-sent on every
request — the risk this test could not reach.
