# Leak ledger — values on origin that need the coordinated history purge

What is recorded here: the FILE, the commit that put the value on origin,
the commit that removed it from the working tree, and the CLASS of value.
Never the value itself. History is NOT rewritten by any session; the purge is
one planned, coordinated operation (every clone re-fetched afterwards).

Scanner: `python scripts/scrub_check.py <paths>` — `GENERIC_PATTERNS`, the
harvested raw denylist, and (2026-10-12) `structural_hits`: any e-mail address
outside the synthetic / example / `.invalid` / anthropic.com domains, and any
`/Workspace/Users/<user>` path whose user segment is not a placeholder.
2026-10-13: `copy_suffixed_document_name` (a downloaded copy's `(n).<ext>` suffix in a
name) and `document_title_phrase` (the SD document titles, held in the scanner
only as sha256 of their word pairs — `TITLE_PHRASE_SHA256`). Both phrases are
already in tracked config / docs / tests (`config/config.yaml` among them), so
these two classes guard push dirs and emitted artefacts, not the whole tree.

## Scrubbed in the tree, still in history (purge)

| File | Introduced | Scrubbed | Class | Count |
| --- | --- | --- | --- | --- |
| `codegen-outputs/iig_validation/round3/pair_2/score.json` (lines 2-4) | 535a0b3 (2026-10-12, D1) | 8ea75d8 | workspace_user_path + email_address (user segment of an ACFC workspace path) | 3 |
| `CLAUDE.md` (Databricks App deployment notes) | d7aa44c (2026-08-28) | the post31 commit (2026-10-13; `<deploy-contact>`) | email_address + workspace_user_path (the Hexaware build workspace's deploy user id) | 1 |
| `docs/acfc/fingerprints/pair_2_sd_home.json` | 95f87bb (2026-10-12; on origin through 382acb7 / 5411014) | the post31 commit (regenerated under the HMAC key) | unkeyed per-column value hashes of the home SD STTM — a plain sha256 of a short or low-cardinality column can be reversed by guessing | 56 (`column_hashes` over 5 sheets) |

## Present in the tree, NOT scrubbed — decision owed (Soham)

Found by the 2026-10-12 patterns / the harvested denylist over every tracked
file. Left in place on purpose: each was committed deliberately or is needed
as-is; listed so the purge decision covers them.

| File | Class | Count | Why it is there |
| --- | --- | --- | --- |
| `app.yaml` | email_address + workspace_user_path | 8 | the four ACFC storage roots (6f14a2d, committed on explicit instruction) — the App needs them; a purge would have to move them to App env |
| `.claude/skills/spiral-breaker/evals/baseline.json` | email_address | 3 | git author lines captured in an eval baseline |
| `docs/acfc/iig_goldens/01_pair_group_index.csv` | harvested_raw_value (6-digit prod GROUP_IDs) | 4 | pair → GROUP_ID index (0080c94, ACFC) |
| `tools/build_goldens.py` | harvested_raw_value (6-digit prod GROUP_IDs) | 2 | `PAIR_GROUPS` (860a798, D1) |
| `codegen-outputs/iig_validation/round2/routing_observed.md` | harvested_raw_value (6-digit prod GROUP_IDs) | 2 | round 2 notes (0b0e080, D1) |

## On `acfc-results` (D1's branch), not scrubbed there — purge

| File | Introduced | Class | Count |
| --- | --- | --- | --- |
| `codegen-outputs/iig_validation/round5/pair_2/RUN.md` | cf807a6 (2026-10-13, D1) | document_title_phrase + copy_suffixed_document_name (the pair's STTM / FRD file names) | 2 classes |
| `codegen-outputs/iig_validation/round5/pair_2/fingerprint_d1.json` | cf807a6 (2026-10-13, D1) | unkeyed per-column value hashes of the D1 STTM copies (no `key_id`) | 57 |

From round 6 on, `scripts/run_round.py` writes the push dir: inputs only as
`<STTM>` / `<FRD>`, the fingerprint structure-only, the keyed one kept in the
work dir.

## The harness leak gate

The ACFC harness (codegen-watch) is not in this repo, so its gate cannot be
edited here. Its owner adds the same two patterns — or runs
`scripts/scrub_check.py` over every result before the push — and allow-lists
its own keys (see `docs/acfc/HARNESS_EXIT_CODES.md` on `acfc/harness-exit3`).
