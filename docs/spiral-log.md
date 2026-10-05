# Spiral log

## 2026-07 to 2026-08: "Repository not found" on git clone (3 occurrences)
- Actual cause: Git used a cached credential for the other GitHub account; `gh auth switch` doesn't change what Git sends.
- Pattern: A (wrong layer)
- Earliest signal: repo visible in browser / `gh repo view` while clone failed.
- Approx. time lost: several hours across three incidents
- Permanent fix: per-account SSH host aliases (github-work / github-personal).

## 2026-09: ~20h rebuild in Genie Code patched by guesswork
- Actual cause: no tests or acceptance criteria; every fix was unverifiable.
- Pattern: B (no oracle)
- Earliest signal: second fix that "looked right" but broke something else.
- Approx. time lost: ~20h
- Permanent fix: port kit with SPEC.md + ACCEPTANCE.md generated from the working codebase.

## 2026-08: overnight agent run produced claims the source FRD didn't support
- Actual cause: unsupervised extraction with no per-fact citation; plausible values filled gaps.
- Pattern: C (drift from source of truth)
- Earliest signal: output asserted a conflict and a key the document never states.
- Permanent fix: citation-required extraction; uncitable facts marked UNVERIFIED.

## 2026-08: model adapter broke after endpoint upgrade
- Actual cause: endpoint began returning a list of reasoning + text blocks instead of a string.
- Pattern: A (wrong layer)
- Earliest signal: failure appeared downstream of the adapter right after the endpoint changed.
- Permanent fix: shape assertion at the adapter boundary.

## 2026-09: multiple workarounds to move code past mail gateways
- Actual cause: an access policy question, not a technical one; Git folder cloning was approved once asked.
- Pattern: D (permission problem)
- Earliest signal: second blocked transfer attempt.
- Permanent fix: ask the constraint owner for the sanctioned path after the first block.

## 2026-10: includeIf rules matched no repos after the SSH remote rewrite
- Actual cause: `**` after `:` isn't a path wildcard in Git's matcher, so `git@github-work:**` couldn't match owner/repo.
- Pattern: A (wrong layer)
- Earliest signal: per-repo email check came back empty for every aliased repo.
- Approx. time lost: minutes (caught by verification step)
- Permanent fix: patterns changed to `git@github-work:*/**` / `git@github-personal:*/**`, plus throwaway-repo regression check.
