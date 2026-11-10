---
name: handoff
description: End-of-session (or before /clear) hand-off - update docs/RESTART.md, the session log in docs/CLAUDE_HISTORY.md and AGENTS.md (durable rules only), delete client copies, commit + push docs. Run when Soham says he is closing / clearing, or asks to update the markdowns.
disable-model-invocation: true
---

# /handoff

Once per session, not after every deploy (RESTART.md commits per deploy were 57% of the
week's commits).

1. **docs/RESTART.md** stays short: "Start here" (what each App runs: version, sha,
   deployment; anything running; the first check), "Open, in order" (each item: what,
   whose call), then the recipes. Move every State block older than this session into
   CLAUDE_HISTORY as "Retired RESTART.md block (<date>)". Target: under 300 lines.
2. **docs/CLAUDE_HISTORY.md**: append `## §[H<n+1>] Session <dates>: <topics>` - bugs and
   their causes, Soham's decisions (dated, his words where short), process slips and
   what prevents them next time. Then the retired RESTART block.
3. **AGENTS.md**: only rules that stay true across sessions (a dated "after postNN"
   note goes to RESTART / the history, never here). Keep it near 200 lines: a procedure
   belongs in a skill, a module-only rule in `.claude/rules/`.
4. `tools/check/pair_check.sh cleanup`; delete any other client copies in /tmp.
5. `python scripts/scrub_check.py` and `pytest -q tests/test_tracked_scrub.py` (zero NEW
   hits), commit the three files (`git commit -F`), fetch, push. Docs-only: no bump, no
   deploy.
