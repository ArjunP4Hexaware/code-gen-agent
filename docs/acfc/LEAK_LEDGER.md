# Leak ledger — values on origin that need the coordinated history purge

What is recorded here: the FILE, the commit that put the value on origin,
the commit that removed it from the working tree, and the CLASS of value.
Never the value itself. History is NOT rewritten by any session; the purge is
one planned, coordinated operation (every clone re-fetched afterwards).

Scanner: `python scripts/scrub_check.py <paths>` — `GENERIC_PATTERNS`, the
harvested raw denylist, and (2026-10-12) `structural_hits`: any e-mail address
outside the synthetic / example / `.invalid` / anthropic.com domains, and any
`/Workspace/Users/<user>` path whose user segment is not a placeholder.

## Scrubbed in the tree, still in history (purge)

| File | Introduced | Scrubbed | Class | Count |
| --- | --- | --- | --- | --- |
| `codegen-outputs/iig_validation/round3/pair_2/score.json` (lines 2-4) | 535a0b3 (2026-10-12, D1) | 8ea75d8 | workspace_user_path + email_address (user segment of an ACFC workspace path) | 3 |

## Present in the tree, NOT scrubbed — decision owed (Soham)

Found by the 2026-10-12 patterns / the harvested denylist over every tracked
file. Left in place on purpose: each was committed deliberately or is needed
as-is; listed so the purge decision covers them.

| File | Class | Count | Why it is there |
| --- | --- | --- | --- |
| `app.yaml` | email_address + workspace_user_path | 8 | the four ACFC storage roots (6f14a2d, committed on explicit instruction) — the App needs them; a purge would have to move them to App env |
| `CLAUDE.md` | email_address + workspace_user_path | 3 | the Hexaware build workspace's deploy path / user id (deploy notes) |
| `.claude/skills/spiral-breaker/evals/baseline.json` | email_address | 3 | git author lines captured in an eval baseline |
| `docs/acfc/iig_goldens/01_pair_group_index.csv` | harvested_raw_value (6-digit prod GROUP_IDs) | 4 | pair → GROUP_ID index (0080c94, ACFC) |
| `tools/build_goldens.py` | harvested_raw_value (6-digit prod GROUP_IDs) | 2 | `PAIR_GROUPS` (860a798, D1) |
| `codegen-outputs/iig_validation/round2/routing_observed.md` | harvested_raw_value (6-digit prod GROUP_IDs) | 2 | round 2 notes (0b0e080, D1) |

## The harness leak gate

The ACFC harness (codegen-watch) is not in this repo, so its gate cannot be
edited here. Its owner adds the same two patterns — or runs
`scripts/scrub_check.py` over every result before the push — and allow-lists
its own keys (see `docs/acfc/HARNESS_EXIT_CODES.md` on `acfc/harness-exit3`).
