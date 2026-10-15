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

## 2026-10-15 — scrub backlog: the SD document-title phrases (visible, not tonight's work)

64 of the 68 known hits under `config/` + `docs/acfc/` are the `document_title_phrase`
class (a deny-listed SD document title phrase). Files and counts only:

| File | Hits |
| --- | --- |
| `config/config.yaml` | 1 |
| `config/overlays/acfc_env.yaml` | 1 |
| `docs/acfc/IIG_SCORECARD_2026-10-07.md` | 1 |
| `docs/acfc/METADATA_DB_SEMANTICS.md` | 1 |
| `docs/acfc/metadata_inserts.sql` | 1 |
| `docs/acfc/review/ADDITION %287%29.md` | 1 |
| `docs/acfc/review/config_inserts %287%29.xlsx` | 16 |
| `docs/acfc/review/config_rows %2810%29.xlsx` | 18 |
| `docs/acfc/review/metadata_inserts %281%29.sql` | 1 |
| `docs/acfc/review/sd_community_demographic_risk_IIG.xlsx` | 11 |
| `docs/acfc/review/sd_community_demographic_risk_IIG_REVIEW.xlsx` | 11 |
| `docs/acfc/sd_community_demographic_risk_standard_table_creation %287%29.txt` | 1 |

The other 4: `harvested_raw_value` in `docs/acfc/iig_goldens/01_pair_group_index.csv`
(already in the table above). Scrubbing these is a backlog item; until then they are
baselined below. Paths in this section are written with `(` / `)` as `%28` / `%29`: a
copy-suffixed document name is itself a scrub pattern, and the ledger adds no hit.

## Known-hit baseline (2026-10-15)

`tests/test_tracked_scrub.py` scans every TRACKED file under `config/` and
`docs/acfc/` with `scripts/scrub_check.py` (generic patterns, the harvested raw
denylist when `inputs/reference_raw/` is present, the local term file
`CODEGEN_SCRUB_DENYLIST` names) and fails only on a hit whose (file, sha256) pair
is not in the rows below. One row per distinct (file, class, term), tab-separated,
the last column its occurrences (hits: one per xlsx cell / text file); the hash is
`codegen.term_hash.term_sha256` (strip, casefold, Unicode NFC, sha256 of the UTF-8,
hex) — never the term. The rows are generated, never hand-edited: regenerate them
deliberately with `python scripts/scrub_check.py --rebaseline`; the test never
writes. This file itself is not scanned (it holds only hashes).

<!-- known-hit baseline: begin -->
```
config/config.yaml	document_title_phrase	aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f	1
config/overlays/acfc_env.yaml	document_title_phrase	754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c	1
docs/acfc/IIG_SCORECARD_2026-10-07.md	document_title_phrase	754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c	1
docs/acfc/METADATA_DB_SEMANTICS.md	document_title_phrase	754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c	1
docs/acfc/iig_goldens/01_pair_group_index.csv	harvested_raw_value	1a2f059d2b983cf6149403857bd7e70d05e2d4e24fdc9e6bc298458779e53a93	1
docs/acfc/iig_goldens/01_pair_group_index.csv	harvested_raw_value	74e6a6aa3db53c4a94f99138b1b7416546452f6a6c061251c97bb0114b62f6d6	1
docs/acfc/iig_goldens/01_pair_group_index.csv	harvested_raw_value	763c6b4d710a6120c44064018b9bdbfbd4e0db1937f9651cac2bc9e4d54a0ae1	1
docs/acfc/iig_goldens/01_pair_group_index.csv	harvested_raw_value	9c831775ac11b8d67ae05d68bb272ef493dde8ce7f5cad3293549e693ac85bd3	1
docs/acfc/metadata_inserts.sql	document_title_phrase	aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f	1
docs/acfc/review/ADDITION %287%29.md	document_title_phrase	aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f	1
docs/acfc/review/config_inserts %287%29.xlsx	document_title_phrase	754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c	14
docs/acfc/review/config_inserts %287%29.xlsx	document_title_phrase	aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f	2
docs/acfc/review/config_rows %2810%29.xlsx	document_title_phrase	754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c	16
docs/acfc/review/config_rows %2810%29.xlsx	document_title_phrase	aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f	2
docs/acfc/review/metadata_inserts %281%29.sql	document_title_phrase	aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f	1
docs/acfc/review/sd_community_demographic_risk_IIG.xlsx	document_title_phrase	754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c	11
docs/acfc/review/sd_community_demographic_risk_IIG_REVIEW.xlsx	document_title_phrase	754350e1cd2f1b5159f33de64a1e85a597cbfb81f6d9783a59011c66273a537c	11
docs/acfc/sd_community_demographic_risk_standard_table_creation %287%29.txt	document_title_phrase	aa5ba889e06d6ba11931bc8aefd6ce5582456803046c1de93a7e01ebfeb6845f	1
```
<!-- known-hit baseline: end -->
