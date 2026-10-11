# Self-Check Report — IIG Validation Outputs

## Files Written

| File | Purpose | Size |
|---|---|---|
| iig_table_discovery.md | Task 1: IIG table set vs SFMC_IIG.xlsx | see below |
| pair_group_index.csv | Task 2: Pair→GROUP_ID index (10 rows) | see below |
| pair_analysis.md | Task 2: Detailed matching analysis | see below |
| goldens_extraction_report.md | Task 3: Blocked—explains why | see below |
| routing.md | Task 4: Column-level routing for SFMC IIG | see below |
| self_check.md | This file | — |

## Task 1 Counts
- SFMC_IIG.xlsx sheets: 7
- Tables found in UC (partial replicas): 5
- Tables NOT in UC (only in pr_dlk_adb.dbo): 3
- Tables in dbo but absent from SFMC sheets: 4
- Tables in SFMC sheets present in dbo: 7

## Task 2 Counts
- Pairs analyzed: 10
- High confidence matches: 0
- Medium confidence matches: 0
- Low / no match: 10
- Blocker: pr_dlk_adb.dbo unreachable (permission + network)

## Task 3 Counts
- Golden extractions completed: 0 (blocked by Task 2)
- Reason: No GROUP_IDs found for any pair

## Task 4 Counts
- Tables analyzed: 7 (all SFMC_IIG sheets)
- Total columns analyzed: 197
- Columns with known origin: 184 (93%)
- Columns with unknown origin: 13 (7%)
  - 7 are UDF/SLA fields (consistently empty in all real IIGs)
  - 4 are runtime-populated or unused optional fields
  - 2 are optional features (DQ_NOTEBOOK_PATH, DELETE_DATABRICKS_NOTEBOOK_NAME)

## Scrubbing Applied
- SFMC_IIG.xlsx already uses SYN-* synthetic IDs (CodeGen output)
- RFC IIG GROUP_IDs, PIPELINE_IDs referenced only by count, not value
- No email addresses, server names, or real file names in output files
- Routing.md uses synthetic SYN-* IDs from reference IIG only
