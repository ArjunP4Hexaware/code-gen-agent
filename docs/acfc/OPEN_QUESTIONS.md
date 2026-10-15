# Open convention questions (IIG vs the prod goldens)

Each item is a place where the agent's IIG workbook and a prod golden disagree
and the documents do not decide it — a CONVENTION to be confirmed by the
framework convention owners, not a bug. Cells are named by golden sheet +
column letter only; no cell value is recorded here (the goldens live on D1).

Column letters follow the `iig_v2` header order (transcribed from the golden,
`metadata.templates.iig_v2.tabs`). The prod table may carry extra columns (the
ADLS sheet's 55th, `FILE_METADATA`, is appended) — confirm the letter on D1
with `tools/iig_diff.py --golden-structure`.

## 1. SRC_COLUMNS — the left-hand name of each `left:right` pair (2026-10-15)

| Golden sheet | Column | Header |
| --- | --- | --- |
| `ADLS_DELTA_INGESTION_DETAILS` | R | `SRC_COLUMNS` |
| `ADLS_DELTA_INGESTION_DETAILS` | AK | `TGT_COLUMN_NAMES` (the right-hand names, for reference) |
| `STGDELTA_STDDELTA_INGESTION_DET` | S | `SRC_COLUMNS` |

- Seen in: the post50 pairing check (`acfc-pairing-check`,
  `codegen-outputs/pairing_check/2026-10-15_post50.md`), pair_11 and pair_12.
- Agent: the left name is the STTM source band's field name (display name).
- Golden: the left name is the stage column name, for both pairs.
- pair_2 agrees only because its source and stage names are identical; the
  pair counts match on all three pairs (no row or column is missing).
- Not changed: the strict `source:target` reading (framework owner rule 4) is
  parked on the local branch `wip/src-columns-rule4` until the D1 golden cells
  confirm which side is meant.

## 2. PIPELINE_DESCRIPTION — rows per workbook (2026-10-15)

| Golden sheet | Column | Header |
| --- | --- | --- |
| `DATA_FACTORY_PIPELINE_SCHEDULE` | D | `PIPELINE_DESCRIPTION` |
| `DATA_FACTORY_PIPELINE_SCHEDULE` | B | `PIPELINE_NAME` (the row key; BSA-assigned, rule 1) |

- Agent: one workbook per FEED, one schedule row per flow (grand master,
  master, file_to_stg, stg_to_std; 3–4 rows).
- Golden: one workbook per PAIR, rows shared across the pair's feeds
  (pair_2: 8 rows for 3 feeds; pair_11: 10 rows for 4 feeds; pair_12: 4 rows
  for 1 feed against the agent's 3).
- The question: are the grand-master / master rows written once per pair (one
  workbook for every feed of an FRD), and does a single-feed pair still carry a
  separate file_to_stg row? Until answered, row counts differ by design; the
  per-feed description text itself is rule 2's (provisional until the D1 dump).
