# Spiral log

## 2026-07 to 2026-08: "Repository not found" on git clone (3 occurrences)
- Actual cause: Git used a cached credential for the other GitHub account; `gh auth switch` doesn't change what Git sends.
- Pattern: A (wrong layer)
- Caught by skill: n/a (pre-skill)
- Earliest signal: repo visible in browser / `gh repo view` while clone failed.
- Approx. time lost: several hours across three incidents
- Permanent fix: per-account SSH host aliases (github-work / github-personal).

## 2026-09: ~20h rebuild in Genie Code patched by guesswork
- Actual cause: no tests or acceptance criteria; every fix was unverifiable.
- Pattern: B (no oracle)
- Caught by skill: n/a (pre-skill)
- Earliest signal: second fix that "looked right" but broke something else.
- Approx. time lost: ~20h
- Permanent fix: port kit with SPEC.md + ACCEPTANCE.md generated from the working codebase.

## 2026-08: overnight agent run produced claims the source FRD didn't support
- Actual cause: unsupervised extraction with no per-fact citation; plausible values filled gaps.
- Pattern: C (drift from source of truth)
- Caught by skill: n/a (pre-skill)
- Earliest signal: output asserted a conflict and a key the document never states.
- Permanent fix: citation-required extraction; uncitable facts marked UNVERIFIED.

## 2026-08: model adapter broke after endpoint upgrade
- Actual cause: endpoint began returning a list of reasoning + text blocks instead of a string.
- Pattern: A (wrong layer)
- Caught by skill: n/a (pre-skill)
- Earliest signal: failure appeared downstream of the adapter right after the endpoint changed.
- Permanent fix: shape assertion at the adapter boundary — commit "fix: fail loud on unrecognized FMAPI content shapes" (2026-10-05): `_chat_content_text` in `src/codegen/databricks.py` accepts only a str or a list of dict blocks with a str-valued text block and raises `DatabricksTransportError` (structure only, never content text) on anything else, incl. the former silent `''`; pinned by `tests/test_databricks.py::test_chat_content_text_accepts_the_observed_shapes`, `::test_chat_content_text_raises_on_unknown_shapes_without_leaking`, `::test_chat_content_shape_error_names_the_structure`, `::test_chat_raises_on_a_content_list_without_text`.

## 2026-09: multiple workarounds to move code past mail gateways
- Actual cause: an access policy question, not a technical one; Git folder cloning was approved once asked.
- Pattern: D (permission problem)
- Caught by skill: n/a (pre-skill)
- Earliest signal: second blocked transfer attempt.
- Permanent fix: ask the constraint owner for the sanctioned path after the first block.

## 2026-10: includeIf rules matched no repos after the SSH remote rewrite
- Actual cause: `**` after `:` isn't a path wildcard in Git's matcher, so `git@github-work:**` couldn't match owner/repo.
- Pattern: A (wrong layer)
- Caught by skill: n/a (pre-skill)
- Earliest signal: per-repo email check came back empty for every aliased repo.
- Approx. time lost: minutes (caught by verification step)
- Permanent fix: patterns changed to `git@github-work:*/**` / `git@github-personal:*/**`, plus throwaway-repo regression check.

## 2026-10-05: hook signal (b) during planned red-then-green test update
- Actual cause: not a spiral. One planned red run (15 expected failures), four planned test edits, then a green run (56/56).
- Pattern: none
- Caught by skill: n/a (not a spiral; the skill correctly concluded none applied)
- Hook signal: b, false positive
- Earliest signal: n/a
- Approx. time lost: none
- Proposed refinement (for a retro, not now): count edit-run cycles that end in an unchanged error signature, rather than raw edits while red.

## 2026-10-07: hook signal (b) — doc edited 4x while a ruff command "still failing"
- Actual cause: not a spiral. `ruff check scripts/iig_scorecard.py tests/test_iig_scorecard.py` failed once (B905 + E501 from a heredoc line-join), was fixed by one edit, and then passed under a LONGER command line (`… src tests scripts/iig_scorecard.py`). The hook keys on the exact command string, so it never saw that command go green; the four edits were to four different sections of an unrelated doc (docs/acfc/IIG_SCORECARD_2026-10-07.md).
- Pattern: none
- Caught by skill: false trigger (diagnostic: re-ran the exact command — exit 0, "All checks passed!")
- Hook signal: b, false positive
- Earliest signal: n/a
- Approx. time lost: ~2 minutes
- Proposed refinement (for a retro, not now): treat a later passing run whose command is a superset (same tool, more paths) as clearing an earlier failing one; and ignore edits to files the failing command does not cover.

## 2026-10-07: hook signal (b) — iig_scorecard.py edited 4x while a wc -l command "still failing" (Chunk C worktree agent)
- Actual cause: not a spiral. The agent's worktree was created at `main` (4c35c61), where `scripts/iig_scorecard.py` does not exist, so the quoted `wc -l` failed; the agent then reset the worktree branch to 8b94b9e and the same command passed. The hook keys on the exact command string and never saw it go green.
- Pattern: none
- Caught by skill: false trigger (diagnostic: re-ran the exact command — exit 0)
- Hook signal: b, false positive
- Earliest signal: n/a
- Approx. time lost: ~2 minutes
- Proposed refinement (for a retro, not now): a worktree created at the default branch instead of the caller's HEAD makes every file of the caller's branch "missing" — the Agent worktree base, not the code, was wrong.

## 2026-10-08: hook signal (b) — derivations.py edited 4x while a `-k missing_schema` pytest "still failing"
- Actual cause: not a spiral. `pytest tests/test_m9_acfc_findings.py -k missing_schema` failed twice by design while a pinned test was re-stated for the new NEEDS_ANSWERS behaviour (first ACFC run defects, item 2b); it then passed under the broader `pytest tests/test_m9_acfc_findings.py` (24 passed). The four edits were to `src/codegen/gate/derivations.py` — new item-3 code (`normalise_path`) the failing test does not cover.
- Pattern: none
- Caught by skill: false trigger (diagnostic: re-ran the exact command — 1 passed)
- Hook signal: b, false positive
- Earliest signal: n/a
- Approx. time lost: ~1 minute
- Proposed refinement (for a retro, not now): same as 2026-10-07 — a superset run going green, and edits to files the failing command does not import, should clear the signal.

## 2026-10-09: hook signal (a) — a new end-to-end test failed 2x on the same test name (Chunk A, band detection)
- Actual cause: not a spiral. `pytest tests/test_band_detection.py` failed on `test_cli_chain_asks_per_band_then_completes_after_answers` each run, but at a LATER step each time, each failure a different, understood cause: (1) the synthetic STTM had no audit rows (extract-sttm refuses), (2) the test read `needs_answers` that `contract_to_json` omits when empty (`exclude_defaults=True` - diagnosed by reading the serializer before any change), (3) the synthetic FRD's stage schema disagreed with the sheet's, (4) `LOAD_TS` is an audit column no template knows, (5) no catalog stated with the ACFC overlay off. (1), (4), (5) are real cold-document findings carried to Chunk B; (2), (3) were test / fixture errors. The hook's error signature is the failing test name, so a test advancing through new failures reads as "the same error".
- Pattern: none (every attempt produced new information - the definition's opposite)
- Caught by skill: false trigger (diagnostic: read `SttmContract` serialization before changing the assertion; the exact command then passed, 35 passed)
- Hook signal: a, false positive
- Earliest signal: n/a
- Approx. time lost: ~3 minutes
- Proposed refinement (for a retro, not now): signal (a) could hash the first `E ` line / the failing assertion's line number rather than the test name, so a test that advances through different failures is not one signature.

## 2026-10-09: hook signal (b) — test_cold_drill_fixes.py edited 4x while a chooser + cold-drill pytest "still failing" (Chunk B)
- Actual cause: not a spiral. `pytest tests/test_m93_chooser.py tests/test_cold_drill_fixes.py tests/test_band_detection.py` failed once on a pinned chooser reason text after the classifier began treating pass-3 candidate mapping sheets as "unclassified - confirm"; ONE fix (the candidate verdict moved after the VDD check, keeping the pinned phrase) made it pass under a superset command (+ test_pairing_content.py, 122 passed). The four counted edits to test_cold_drill_fixes.py ADDED new focused tests (delimiter-in-format, F2 domain table, schema markers) and re-stated my own new classifier expectations - no edit was a retry on the failing test.
- Pattern: none
- Caught by skill: false trigger (diagnostic: re-ran the exact command — 117 passed, exit 0)
- Hook signal: b, false positive
- Earliest signal: n/a
- Approx. time lost: ~2 minutes
- Proposed refinement (for a retro, not now): as 2026-10-07 / 10-08 — a superset run going green should clear the signal; edits that only add new test functions are not fix attempts.
