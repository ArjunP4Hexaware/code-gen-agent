# pair_01 IIG diff, re-scored at home (post57)

The four other files here are the scrubbed export the D1 harness pushed for the
post55 run (acfc-results `run_20261015T193331Z_3e09149/pair_01_scrubbed`), copied
as they are (`scripts/scrub_check.py` on this folder: clean). No golden is
read here: `tools/iig_rescore_export.py` rebuilds a golden and an agent workbook
from the export (every listed cell with its scrubbed value, every unlisted cell
equal on both sides, every row at its row number, key columns from `row_keys.md`)
and scores the rebuilt pair.

    python tools/iig_rescore_export.py --export docs/acfc/iig_exports/pair_01_post55 \
        --out <scratch> --baseline-tool <post56 tools/iig_diff.py> \
        --baseline-keys <post56 tools/iig_keys.yaml>

(the baseline is `git archive 95c0be6 tools scripts config src` unpacked in a
scratch folder; the ACFC overlay is applied, as on D1).

## Old vs new

"before" = the post56 scorer on the rebuilt pair; it reproduces the export's own
numbers exactly (every sheet's score, and the totals: 23 exact + normalized, 30
mismatch, 350 missing, 307 extra = 3.2). "now" = post57.

| sheet | export | before | now | now: paired (by order) | now: exact+norm / mismatch / missing / extra / template-only |
| --- | --- | --- | --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 14.8 | 14.8 | 42.5 | 4 (0) | 17 / 12 / 11 / 0 / 48 |
| FILE_ADLS_INGESTION_DETAILS | - | empty by rule (MFT) | empty by rule (MFT) | 0 | - |
| ADLS_DELTA_INGESTION_DETAILS | 0.0 | 0.0 | 40.7 | 3 (3) | 70 / 50 / 46 / 6 / 3 |
| STGDELTA_STDDELTA_INGESTION_DET | 0.0 | 0.0 | 37.9 | 1 (1) | 11 / 18 / 0 / 0 / 0 |
| ADLS_FIXED_WIDTH_HANDLER | 0.0 | 0.0 | 33.3 | 3 (3) | 18 / 18 / 18 / 0 / 0 |
| DATABRICKS_NOTEBOOK_DETAILS | 13.3 | 13.3 | 13.3 | 2 (0) | 4 / 6 / 20 / 0 / 0 |
| DATA_QUALITY_RULES | 0.0 | 0.0 | 0.0 | 0 (0) | 0 / 0 / 56 / 42 / 0 |
| EMAIL_TEMPLATE_CONFIG | 25.0 | 25.0 | 27.3 | 2 (0) | 6 / 8 / 8 / 0 / 2 |
| **TOTAL** | **3.2** | **3.2** | **28.3** | 15 (7) | 126 / 112 / 159 / 48 / 53 |

## Each rule switched off alone (now = 28.3)

| without | score | exact+norm / mismatch / missing / extra / template-only |
| --- | --- | --- |
| (a) feed + flow + row order pairing | 4.1 | 27 / 26 / 350 / 254 / 53 |
| (b) template-only columns | 25.3 | 126 / 112 / 159 / 101 / 0 |
| (c) date = midnight datetime | 27.4 | 122 / 116 / 159 / 48 / 53 |
| (d) segment codes (hddr / det / trlr) | 27.6 | 123 / 115 / 159 / 48 / 53 |

(a) carries most of the change: the golden and the agent name the stage table
differently, so under identity pairing every ADLS_DELTA / STGDELTA / fixed-width
row was missing on one side and extra on the other (7 rows paired now, the name one
mismatch cell each; golden ADLS_DELTA row 5 stays missing: the golden has 4 file
rows, the agent 3). (b) moves the 48 schedule cells (PROCESS_NAME … IsFileCopyReqFlag),
3 FILE_METADATA and 2 EMAIL_NOTIFICATION_URL cells out of the score. (c) is the
schedule's ACTIVE_END_DATE (4 cells). (d) is the fixed-width SEGMENT (3 cells).

## What is left (for the next D1 round, not fixed here)

- DATA_QUALITY_RULES pairs nothing: the golden has 8 rules over two columns
  (DateFormat / DataTypeCast, 4 each), the agent 6 over other columns and classes.
- The agent's ADLS_DELTA SRC_ADLS_PATH starts `/Path : …`: a label of the FRD's
  landing cell read as part of the path (agent side, to look at with the FRD).
- APPLICATION_NAME / PROCESS_NAME: the golden prefixes the vendor package
  (`VND_P_…`), the agent does not.
