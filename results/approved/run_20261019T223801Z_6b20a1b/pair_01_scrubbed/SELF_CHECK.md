# SELF_CHECK - scrubbed export (counts only)

the leak gate (codegen.leakgate): dictionary repo-tokens, 3572 terms (harvested + static), 1231 harvested terms dropped

- repo-token dictionary (the leak gate's): repo-tokens: src ui docs, text files only, 292 files, 9038 tokens
- static denylist: 62 terms
- harvested gate terms: 2 checked, 8 dropped (dictionary words / under 5 characters)
- raw harvest (inputs/reference_raw): absent or empty
- cells exported: 317 (mismatch 108, missing-in-agent 164, extra-in-agent 45)
- rows listed in row_keys.md: golden 26, agent 21
- per-column rows in sheets.md: 128
- placeholders: G 2 (3 uses), A 47 (1284 uses)
- scrub_check hits before replacement, per class: local_denylist 363
- re-scan of mismatches.md, row_keys.md, sheets.md, SELF_CHECK.md with scrub_check + the gate's terms: FAILED - gate_column_value 1 (classes only; mismatches.md, row_keys.md, sheets.md deleted)
