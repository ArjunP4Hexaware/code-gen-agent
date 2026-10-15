# SELF_CHECK - scrubbed export (counts only)

- fixtures token universe: git ls-files fixtures/, 98 files, 2494 tokens
- local denylist: 27 terms
- raw harvest (inputs/reference_raw): absent or empty
- cells exported: 687 (mismatch 30, missing-in-agent 350, extra-in-agent 307)
- rows listed in row_keys.md: golden 26, agent 23
- per-column rows in sheets.md: 142
- placeholders: G 0 (0 uses), A 59 (2102 uses)
- scrub_check hits before replacement, per class: client_storage_prefix 19, local_denylist 155
- re-scan of mismatches.md, row_keys.md, sheets.md, SELF_CHECK.md with scrub_check: 0 hits
