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

## 3. PIPELINE_NAME — blank (Aruna) vs default + naming standard (Venu) (2026-10-16)

| Golden sheet | Column | Header |
| --- | --- | --- |
| `DATA_FACTORY_PIPELINE_SCHEDULE` | B | `PIPELINE_NAME` |
| `DATABRICKS_NOTEBOOK_DETAILS` | — | `PIPELINE_NAME` (the leg's pipeline) |

- Aruna's rule: PIPELINE_NAME is BSA-assigned, so the agent leaves it blank
  (framework owner's rule 1, post49).
- Venu's ask: the agent proposes a default name, and the BSA may apply the
  team's naming standard instead.
- **Resolved (post59): the BSA chooses, with the default shown.** Every
  `pipeline_name.<flow>` input (grand_master / master / file_to_stg /
  stg_to_std, per feed) is a three-way choice: `use_default` (the conventions
  profile's per-flow template, rendered from the feed's {domain} {subdomain}
  {source} {frequency} {layer} {load_mode}), `naming_standard` (the BSA's own
  template in the same syntax), or `leave_blank`.
- Aruna's rule still holds for every unattended run (CLI, harness, App with no
  confirmation). The proposal is shown and NOT applied: the cell stays blank,
  and a non-blocking INPUT_NEEDED line names the proposal and its template. A
  cell is filled only on an explicit choice (the answers file's `choice:` /
  `standard:`, or the App's Confirm); a filled default or standard carries the
  "taken from other documents" gate flag (`frd_unstated:…`).
- A proposal that collides with a PIPELINE_NAME of the loaded goldens / corpus
  (`pipeline_name_corpus`) is never offered; the line asks instead.
- The repo ships SYNTHETIC templates only (`SYN_PL_…`, labelled "no naming
  standard loaded — placeholder"). The real templates go in the ACFC-side
  `codegen-state/overlays/acfc_prx.yaml`, per flow
  (`docs/acfc/OVERLAY_FIELDS.md`).
- The same control applies to APPLICATION_NAME, EMAIL_TO and the email status
  set wherever a default exists (ACTIVE_START_DATE has none).
- **post61: two kinds of default.** Aruna's rule covers what the AGENT renders or
  derives (`agent_proposal`: the PIPELINE_NAME template, APPLICATION_NAME from
  SOURCE, ACTIVE_START_DATE) — shown, never applied without confirmation. A value
  the conventions profile or the ACFC overlay sets (`profile_default`: the email
  status set, EMAIL_TO, the notebook names, the SRC_FILE_NAME wildcard style) is
  written when unanswered — source `profile`, no gate flag, no open input — and
  still listed (a NOTE line, the answers template, the App's panel) so the BSA
  can change it. An owed cell's kind is its `default_kind` (unset: a default with
  a `{token}` is an agent proposal, a literal one a profile default).
- Still open: the team's naming standard itself (the attach-a-document path
  is deferred).
