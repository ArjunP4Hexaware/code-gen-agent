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

## 4. PHI masking — v1 masked from the FAQ, the framework path has no equivalent (2026-10-18, for Aruna)

- v1 notebook (the standalone module tree): a `masking` module masks the PHI
  columns (the STTM's PII / PHI flags, the FAQ's answers) to the last
  `masking.visible_chars` characters before anything is written.
- v2 notebook (post69, acfc_prx) renders only what the IIG states, and no IIG
  sheet has a PHI / masking cell. So v2 has no masking cell. The framework's
  generic notebooks have none we know of either.
- Question for Aruna: does the framework mask PHI anywhere, for example a
  DATA_QUALITY_RULES class, a view or a column tag? If it does, which IIG cell
  states it? Until that is answered, v2 writes the columns as they arrive, the
  same as the framework path.

## 5. The not-null list used as a key — v1 and iig_v1 only (2026-10-18)

- The STTM contract now carries two lists: `load_rules.not_null_columns` (the
  required columns) and `load_rules.natural_key` (the Primary Key / Key cells).
  The not-null list is never a key.
- iig_v2 (acfc_prx) proposes TGT_PRIMARY_KEY only from an explicit key signal
  (`codegen.primary_key`). A merge load with no signal gets a blocking QUESTION.
- Left as they were: the v1 notebook still merges and dedups on the not-null
  list (its MERGE keys, rejects and generated tests), and iig_v1 (the SFMC 7-tab,
  byte for byte) writes the not-null list as TGT_PRIMARY_KEY and the dedup keys.
  Both are now named `not_null_columns` in the code. Moving them to the
  explicit key changes their outputs and is a separate decision.
- Also unchanged: iig_v2's DeDuplicationRule / NullCheckRule SOURCE_COLUMN is
  still the detail table's Primary Key cells plus the not-null columns.

## 6. SCHEMA_DRIFT_FLAG — Y by default on a new delimited feed? (2026-10-18, for Aruna)

| Golden sheet | Header |
| --- | --- |
| `ADLS_DELTA_INGESTION_DETAILS` | `SCHEMA_DRIFT_FLAG` |

- **Now (post70):** the ACFC overlay writes `Y` (`family_conventions.schema_drift_flag`),
  as the SD golden does. A feed whose golden says `N` sets
  `feed_overrides.<feed_id>.schema_drift_flag: N` in the ACFC-side overlay. With `Y`,
  the v2 notebook adds a drift check before the stage: a missing column stops the
  run, extra columns are counted.
- **The sources disagree:**
  - `Y`: the SD test-cells sheet and the reported CAQH IIG.
  - `N`: the SD PROD rows read in round 6 (2026-10-13), the SFMC reference IIG and
    the pair-1 golden.
- **Questions for Aruna:**
  1. Does the framework expect `SCHEMA_DRIFT_FLAG = Y` on a new delimited feed by
     default?
  2. What does `Y` change in the generic notebook? Does a missing column fail the
     file? Is an extra column dropped, loaded or quarantined? Is the schema evolved?

## 7. EDH E2E gold loads — values no mapping document states (2026-10-20, for the EDH team)

Not IIG conventions: these concern the gold-layer EDH E2E mappings (Facets → Enterprise
Data Hub, 11 documents, 12 target tables). The reader asks each of them once per table
today. One answer per question closes them all, through the `edh_e2e:` profile
(`ENVIRONMENT_ACFC.md` §h). No document values are recorded here.

### 7.1 The target schema

The documents name the destination catalog and each target table, never a schema.
- **Question:** which UC schema do the 12 EDH gold tables load into? Is it one schema for
  all, or does it vary by table (and if so, by what rule)?

### 7.2 Facets databases → UC catalog.schema

Every source is named by its Facets database and a bare table name. None is a UC
three-part name.
- **Question:** for each Facets database the mappings name, which UC `catalog.schema`
  holds its tables in the environment the gold loads read from? Does that differ between
  D1 and the higher environments?

### 7.3 SCD2 and surrogate keys — the convention the existing EDH loads use

No document states whether history is kept, or how surrogate keys are made. The
documents carry effective-date columns, but no SCD2 marker and no SK.
- **Questions:**
  1. Do the existing EDH gold loads keep type-2 history?
  2. If yes, what are the effective-start / effective-end / current-flag columns, and what
     value closes a current row?
  3. How are surrogate keys generated (identity column, hash of the business key,
     sequence, max + 1)?
  4. Which columns form the business key that the MERGE matches on? The documents mark
     primary-key columns on 29 rows; is that the key?

### 7.4 The two zero-argument Facets functions

17 expressions call one of two zero-argument functions. Their meaning is not in the
documents.
- **Question:** what does each function return (for example an empty string, a blank of
  a given width, the current date), so that it can be written as Spark SQL?
