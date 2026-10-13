# Document fingerprints (scripts/doc_fingerprint.py)

`pair_2_sd_home.json` — the home checkout's SD STTM + FRD, keyed under `codegen-state/fingerprint.key` (key id `73fc1ff0`); the round gate compares D1's documents against it (`--compare`, HARD = stop, WARN = recorded).

- **Reference SD STTM = D1's copy (round 6, accepted 2026-10-13):** the home copy differs only in its anonymized stage / standard `ColumnName` columns (round 6 compare.txt: sheets 2–3 columns J, O; sheet 4 columns K, P) — every other column hash, sheet, extent and header is identical, and the FRD's text is identical (only its file sha256 differs).
