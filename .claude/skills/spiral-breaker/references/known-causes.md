# Known causes

Concrete signatures seen before. A match is a HYPOTHESIS to verify with the pattern's
diagnostic action, never a conclusion to act on directly.

Entry format:

```
## <short name>
- Signature: <error text / symptom / context that identifies it>
- Usual cause:
- Check: <the command or observation that confirms or rules it out>
- Pattern: <A/B/C/D>
- Seen: <dates>
- Permanent fix: <if any>
```

## Git "Repository not found" under the wrong account
- Signature: `git clone` fails with "Repository not found" while the repo is visible in
  the browser and in `gh repo view`.
- Usual cause: Git sends a cached credential for the other GitHub account; `gh auth
  switch` doesn't change what Git sends.
- Check: confirm the repo is visible via the browser / `gh repo view` while the clone
  fails, then look at which account's credential Git itself sends for that host, not
  which account `gh` is logged into.
- Pattern: A
- Seen: 2026-07 to 2026-08 (3 occurrences)
- Permanent fix: per-account SSH host aliases (github-work / github-personal).

## Rebuild patched by guesswork, no tests
- Signature: during a rebuild or port, a fix "looks right" but breaks something else;
  there are no tests or acceptance criteria to check a fix against.
- Usual cause: no oracle; every fix is unverifiable.
- Check: can you say in one sentence how you will know it is fixed? If not, there is no
  failing test or acceptance check yet.
- Pattern: B
- Seen: 2026-09
- Permanent fix: port kit with SPEC.md + ACCEPTANCE.md generated from the working
  codebase.

## Extraction claims the source document doesn't support
- Signature: an unsupervised extraction run asserts facts (a conflict, a key) that the
  source document never states.
- Usual cause: extraction with no per-fact citation; plausible values filled the gaps.
- Check: cite every extracted claim against the document (section or table plus the
  short source text); anything that cannot be cited is UNVERIFIED.
- Pattern: C
- Seen: 2026-08
- Permanent fix: citation-required extraction; uncitable facts marked UNVERIFIED.

## Model endpoint content-shape change breaks the adapter
- Signature: right after a model endpoint upgrade or change, a failure appears downstream
  of the model adapter.
- Usual cause: the endpoint began returning a list of reasoning + text blocks instead of
  a string.
- Check: print the raw response content at the adapter boundary, with its type at each
  level, before changing code downstream.
- Pattern: A
- Seen: 2026-08
- Permanent fix: shape assertion at the adapter boundary (fail loud on unrecognized
  content shapes, pinned by tests).

## Workarounds to move code past a mail gateway
- Signature: a second blocked attempt to transfer code past a mail gateway or similar
  policy control.
- Usual cause: an access-policy question, not a technical one.
- Check: is there a sanctioned path? Ask the constraint owner; in the logged case Git
  folder cloning was approved once asked.
- Pattern: D
- Seen: 2026-09
- Permanent fix: ask the constraint owner for the sanctioned path after the first block.

## includeIf rules match nothing after an SSH remote rewrite
- Signature: after rewriting remotes to SSH host aliases, the per-repo identity
  (e.g. `user.email`) check comes back empty in every aliased repo.
- Usual cause: `**` after `:` isn't a path wildcard in Git's matcher, so
  `git@<alias>:**` can't match owner/repo.
- Check: run the per-repo email check in a throwaway repo whose remote uses the alias.
- Pattern: A
- Seen: 2026-10
- Permanent fix: patterns `git@github-work:*/**` / `git@github-personal:*/**`, plus a
  throwaway-repo regression check.

## Hook (b) false positive: the failing command later passed under a different command line
- Signature: spiral-detector signal (b) names a lint / test command as "still failing"
  while the edits it counts are to files that command does not cover.
- Usual cause: the hook matches the exact command string; the same check went green
  under a broader invocation (more paths), which the hook does not link to the old one.
- Check: re-run the exact command the signal quotes. Exit 0 = false trigger.
- Pattern: none (not a spiral)
- Seen: 2026-10-07 (twice — the second in a worktree agent created at main)
- Permanent fix: none yet — candidate hook refinement logged for /spiral-retro.
