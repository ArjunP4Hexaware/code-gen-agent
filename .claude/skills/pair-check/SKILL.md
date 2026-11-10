---
name: pair-check
description: The 12-pair real-pair check for a change that can move generated output - the container harness, mock, framework mode, old tree vs new, outcomes + artefact differences by kind and count only. Use after committing such a change and before pushing it.
---

# /pair-check

1. Commit first: the NEW side is HEAD (the script refuses uncommitted `src/` `config/`
   `scripts/`). Never edit `src/` while it runs (use a worktree).
2. Run in the background: `tools/check/pair_check.sh run [<old-sha>]` (old defaults to
   HEAD~1; give the last DEPLOYED version's sha when several commits are unchecked).
   A side whose code tree ran before is reused from `$PAIR_CHECK_DIR/cache` - the old
   side of the next version is usually free. A notebook change: add
   `--output-mode notebook` to the harness line (edit a copy, never the env).
3. Read the result: outcomes must be unchanged unless the change means them to move;
   every REAL difference must be explained (sha-only = a changed contract's banner).
   Report kinds and counts only - never a cell value, client name or file name from a
   pair.
4. At the end of the SESSION (not after each version): `tools/check/pair_check.sh
   cleanup` - it deletes the client copies, the cache and the worktree.
