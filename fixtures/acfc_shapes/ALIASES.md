# Alias map — pair-1 golden ↔ fixtures

The pair-1 golden (`docs/acfc/rfc_capture/rfc_capture/goldens/pair_1/`, scrubbed
upstream) keeps two client-identifying tokens in its table names and process
names. The fixtures under this directory and the tracked COPY of the golden
(`pair_1/golden/`) both carry the aliased vocabulary, applied by
`tests/acfc_shapes/pair1.py::alias` as ordered, case-preserving literal
replacements:

| Raw token | Alias | Where it appears |
| --- | --- | --- |
| `prx` / `Prx` / `PRX` | `vnd_p` / `Vnd_P` / `VND_P` | catalog/schema/table names (`pr_dlk_prx.stg_prx_accum.prx_accum_acfc`), `PRX_ACCUMULATOR`, notebook paths, sender name |
| `acfc` / `Acfc` / `ACFC` | `client` / `Client` / `CLIENT` | table name suffix, `I_ACCUM_*_TO_ACFC_*.csv` file patterns, object names |
| `Abarca` | `VENDOR_A` | IIG `SOURCE` column (vendor name → VENDOR_x per SHAPES_FOR_PORT's naming key) |
| `Facets` | `SRC_SYS_A` | IIG `SOURCE` column (source system → SRC_SYS_x per the naming key) |
| every value in column `TGT_STORAGE_ACCOUNT_NAME` | `syn-storage-001` | IIG `FILE_ADLS_INGESTION_DETAILS` — the golden carries a real storage-account name the upstream scrub missed (`scripts/scrub_check.py` flags it, so it is not spelled here either); the raw golden therefore stays untracked |

Aliased results: stage `pr_dlk_vnd_p.stg_vnd_p_accum.vnd_p_accum_client`,
standard `pr_std_vnd_p.accum.vnd_p_accum_client`, process `VND_P_ACCUMULATOR`,
vendor abbreviation `VND_P`.

Column names, data types (`String`, `Date`, `Decimal(17,2)`…`Decimal(22,2)`,
audit `STRING`/`TIMESTAMP`), segment membership, fixed-width starts/lengths and
the golden's segment vocabulary (`HDDR`/`DET`/`TRLR`) are structure and are kept
verbatim. The VDD fixture uses the segment vocabulary SHAPES_FOR_PORT §3 records
for the pair-1 dictionary (`HDR`/`DTL`/`TRL`).
