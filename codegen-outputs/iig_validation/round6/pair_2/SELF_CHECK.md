# SELF_CHECK - scrubbed export (counts only)

- fixtures token universe: git ls-files fixtures/, 98 files, 2494 tokens
- local denylist: 27 terms
- raw harvest (inputs/reference_raw): absent or empty
- cells exported: 733 (mismatch 16, missing-in-agent 412, extra-in-agent 305)
- rows listed in row_keys.md: golden 31, agent 33
- placeholders: G 16 (831 uses), A 0 (0 uses)
- scrub_check hits before replacement, per class: client_storage_prefix 15, databricks_workspace_host 6, email_address 12, local_denylist 9
- re-scan of mismatches.md, row_keys.md, SELF_CHECK.md with scrub_check: 0 hits
