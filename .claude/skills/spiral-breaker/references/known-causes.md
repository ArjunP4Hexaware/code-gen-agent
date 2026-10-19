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
- Seen: 2026-10-07 (twice — the second in a worktree agent created at main); 2026-10-09
  (Chunk B: the counted edits ADDED new tests to a file the command covers; the
  failure was one pinned reason text, fixed once, green under a superset command);
  2026-10-11 (iig_diff: the check DID fail at signal time — one over-long line in
  feature code written that step; the counted edits were the feature, no retry;
  `ruff format` once, exact command exit 0); 2026-10-15 (the failing run was a
  `-W error::DeprecationWarning` probe under .venv-d1 tripping openpyxl 3.1.2's utcnow;
  the counted edits were CLAUDE.md restart notes; the command without the flag exit 0);
  2026-10-18 (post68: a pinned "notebook owes nothing" assertion fixed once inside a
  multi-file run; the counted edits added one test block per item to a new test file)
- Permanent fix: none yet — candidate hook refinement logged for /spiral-retro.

## Hook (a) false positive: one test name, a different failure each run
- Signature: spiral-detector signal (a) — the same pytest command "failed 2 times in a row with
  the same error signature" while each run failed at a later assertion of the same test.
- Usual cause: the signature keys on the failing test's name; a new end-to-end test advancing
  through fixture gaps (audit rows, matching schemas, known names) fails under one name each time.
- Check: compare the first `E ` lines / failing line numbers of the two runs. Different = new
  information each run, not a spiral; diagnose the current failure before changing anything.
- Pattern: none (not a spiral)
- Seen: 2026-10-09; 2026-10-14 (related, a TRUE signal: the two different failures were two
  guesses at a new test's expected row layout — observe the emitted value before asserting)
- Permanent fix: none yet — candidate hook refinement logged for /spiral-retro.

## A patch script that aborted before writing, so the "fix" changed nothing
- Signature: a check fails twice with byte-identical findings right after a scripted edit
  (python / sed in a bash heredoc) whose own output shows a traceback or "0 replacements".
- Usual cause: heredoc escaping on this Windows box mangles backslash escapes / backticks, the
  script's match guard fails, nothing is written.
- Check: grep the file for the text the patch was meant to remove BEFORE re-running the check.
- Pattern: A (wrong layer - the edit never landed)
- Seen: 2026-10-12; 2026-10-15 (post57: a heredoc regex patch; hook signal (a))
- Permanent fix: patch with the Edit tool, or a script file written with the Write tool.
## Hook (a)/(b) false positive: a brand-new test file in its planned red phase
- Signature: signal (b) counts edits to a module while a pytest command on a NEW (untracked)
  test file "still fails"; signal (a) then reports the same command failing twice "with the
  same error signature" — both runs a collection-time ImportError.
- Usual cause: tests written first against an API not yet implemented; each edit adds that API,
  so the missing import moves from one name / module to the next. The signature does not
  include the missing name.
- Check: compare the `cannot import name 'X' from 'M'` lines of the two runs, and whether the
  test file is untracked. A different X (or M) on a new file = planned progression, not a spiral.
- Pattern: none (not a spiral)
- Seen: 2026-10-13
- Permanent fix: none yet — candidate hook refinement logged for /spiral-retro (proposals.md).
## Windows host without symlink privilege (state_mirror tests)
- Signature: tests/test_state_volume_mirror.py fails with MirrorStatus error 'OSError, error code
  none' on a Windows checkout; passes in the Linux container / App.
- Usual cause: `Path.symlink_to` needs Developer Mode or admin on Windows (WinError 1314).
- Check: one `Path(tmp/'l').symlink_to('t', target_is_directory=True)` outside the suite.
- Pattern: A (wrong layer - the host OS)
- Seen: 2026-10-19
- Permanent fix: none yet (candidate: skip on Windows without the privilege).
