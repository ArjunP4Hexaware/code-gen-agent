# SELF_CHECK - scrubbed export (counts only)

- fixtures token universe: git ls-files fixtures/, 98 files, 2496 tokens
- local denylist: 27 terms
- raw harvest (inputs/reference_raw): absent or empty
- cells exported: 913 (mismatch 16, missing-in-agent 592, extra-in-agent 305)
- rows listed in row_keys.md: golden 43, agent 33
- placeholders: G 31 (1499 uses), A 0 (0 uses)
- scrub_check hits before replacement, per class: client_email_domain 48, client_storage_prefix 27, databricks_workspace_host 6, email_address 60, local_denylist 57, real_webhook_host 12
- re-scan of mismatches.md, row_keys.md, SELF_CHECK.md with scrub_check: 0 hits
