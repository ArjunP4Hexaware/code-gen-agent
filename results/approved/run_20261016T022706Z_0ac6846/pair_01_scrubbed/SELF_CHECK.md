# SELF_CHECK - scrubbed export (counts only)

- fixtures token universe: git ls-files fixtures/, 98 files, 2494 tokens
- local denylist: 27 terms
- raw harvest (inputs/reference_raw): absent or empty
- cells exported: 320 (mismatch 113, missing-in-agent 159, extra-in-agent 48)
- rows listed in row_keys.md: golden 26, agent 23
- per-column rows in sheets.md: 128
- placeholders: G 0 (0 uses), A 59 (1476 uses)
- scrub_check hits before replacement, per class: local_denylist 147
- re-scan of mismatches.md, row_keys.md, sheets.md, SELF_CHECK.md with scrub_check: 0 hits
