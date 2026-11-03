# EDO standards alignment

The client's engineering-standards documents landed 2026-08-26 — **EDO Data
Engineering Naming Standards** and **EDO Data Engineering Coding Standards**
(plus the SFMC Email Campaign FRD used as the first real feed to validate
against). This closes the three-input model's input #2, which had been a
STUB since the model was introduced. This page maps each applicable clause
to where the generator implements it, and names every deliberate deviation.

The documents themselves are client documents and are **not** in this repo
(see CLAUDE.md "Fixtures & data rules"); this page carries only the derived
rules, which also live as data in `config/config.yaml
engineering_standards:`.

## Naming standards (Databricks section)

| EDO clause | Implementation |
|---|---|
| WORKFLOW: `WF_<3 Char Product>_<3 Char Sub-Product>_<Sources>_<Domain>_<Subdomain>_<Region/LOB>_<Frequency>` | `config.yaml engineering_standards.job_name_pattern` + abbreviation tables; resolved in `codegen.emit.context.resolve_job_name`. Emitted as the generated job/task name in `job/workflow.json`. |
| NOTEBOOK: `NB_<Product>_<Sub-Product>_<Domain>_<Subdomain>_<Functionality>` | `notebook_name_pattern`; the generated job's `notebook_path` leaf is the `NB_` name (deploy the assembled `<feed_slug>.ipynb` under that workspace name). |
| Product / Sub-Product codes (tables 3.2/3.3) | `product_code: DLK` (Data Lake), `sub_product_code: NSP` (No Sub-Product). |
| Source, Domain/Subdomain, Region/LOB, Frequency abbreviation tables (3.1, 3.4, 3.5, 3.6) | Transcribed into `source_abbreviations` / `domain_abbreviations` / `lob_abbreviations` / `frequency_abbreviations`. Unmapped values fall back to their sanitized-uppercase form rather than failing generation. |
| Load-strategy / data-layer abbreviations (3.6/3.7: TRUNC/UPSRT, STG/STD) | Informational only here: the client's target table names (`stg_mbr.…`, `mbr.…`) already carry the layer; the generator never invents table names beyond configured side-table suffixes. |
| Python naming (functions/variables lower_snake, classes PascalCase, CONSTANTS upper) | Generated modules already comply; enforced by the gate's ruff pass (`pep8-naming` not needed — templates are fixed-form). |

**Deviations (deliberate):**

- **`{feed}` stands in for `<Sources>` in the workflow name.** The bare
  source abbreviation collides when one vendor ships several feeds into the
  same domain (the CV fixture universe does exactly this); the feed slug
  carries the vendor prefix *and* stays unique. The full EDO component
  order is otherwise preserved.
- **ADF-side conventions (PL_/LS_/DS_/TRG_, data-flow abbreviations) are
  out of scope**: this agent emits Databricks artifacts only. The ADF
  tables are retained in config comments for whoever wires the pipeline
  into ADF/Tidal.
- **A feed with no resolvable frequency ships as `ADH`** (it runs ad hoc —
  the honest reading of "unscheduled").

## Coding standards (Databricks section)

| EDO clause | Implementation |
|---|---|
| NULL check on PK columns when target load is upsert | `rejects.py` (not-null over `load_rules.not_null_columns` → errors table) + post-load `dq.py` `not_null:` checks. |
| Dedup rule on key columns when target load is upsert | `dq.py` `duplicate_key` check over (SRC_FILE_NAME, natural key); the writer's MERGE is keyed the same way. |
| NULL check on referential columns when recycle enabled | `recycle.py`/`reference.py`: no-match and null-reference rows land in the recycle table, retried for the window. |
| Rejects captured in a reject table + email alert to Production Support | Errors side table per feed; `email_notifications` now **always** emitted (see next row). |
| Every pipeline must have success AND failure alerts to the prod-support DL (a client value — the tracked config carries the synthetic stand-in `syn.dl.prodsupport@synthetic.example`; the real DL rides `CODEGEN_NOTIFICATION_EMAILS` at deployment) | `config.yaml job.notification_emails`; `workflow.json.j2` emits `on_success` + `on_failure` unconditionally (previously only when a contract rule asked). |
| Never leave the default (7-day) timeout; use execution hours + 1 | `job.timeout_hours` (7 = the SFMC FRD's 6-hour file SLA + 1) → `timeout_seconds` on the job and task. |
| Job clusters: DBR ≥ 15.4 LTS with Photon | `job.spark_version: 15.4.x-scala2.12`, `job.runtime_engine: PHOTON` in the generated cluster spec. |
| Liquid Clustering for new tables (`CLUSTER BY AUTO`) | All five DDL templates now emit `CLUSTER BY AUTO` (DDL remains REFERENCE-only under `create_tables: false`). |
| Use MERGE instead of UPDATE | The writer has always been MERGE-based (`MERGE INTO` on SRC_FILE_NAME + natural key). |
| Avoid lambda expressions | `rejects.py.j2` refactored to `operator.or_` / `DataFrame.unionByName`. |
| Avoid print, use logging | Pipeline modules use no prints; the thin notebook entrypoint prints the final run report (display, not logging) and `make_fixtures.py` is an offline dev tool — both accepted. |
| `F.lit(None)` for empty columns, explicit join type, no right joins, no UDFs, select-based schema contract, `is`/`is not` for singletons | Audited 2026-08-26: generated modules already comply (no UDFs, no joins beyond the recycle reference lookup which is an explicit `left_anti`-style check, casts in select). |
| Line length ≤ 79 (PEP 8) | **Deviation**: generated code and generator stay at ruff `line-length = 100`, matching the generator repo's own settings and the Code Review Agent's convention. Flagged for a program-level decision rather than churning every template. |
| IIG Framework, `DATA_QUALITY_RULES` / `EMAIL_TEMPLATE_CONFIG` tables, Logic App email path, Tidal scheduling, ADF Git rules | **Out of this agent's remit**: those are shared-platform integration points. The generated job JSON carries the notification recipients and SLA text so the integration step has everything it needs. |
| Vacuum on Delta tables / temp-table cleanup in `tempdb` | Maintenance-operations concern of the deployed pipeline, not per-run ingest logic; noted here so the TDD picks it up. |

## Data Lakehouse Data Layers Standards (reviewed 2026-10-30)

A third client standard, **Data Lakehouse Data Layers Standards**: the file
is named V1.1, but its revision history runs to **1.3 (Feb 2026, after the
ERB review)**, so read it as v1.3. It is a layer-architecture document (Raw /
STG / STD / EDH / BSL: object type, load type, catalog and schema naming,
user access). Most of it governs the client's platform and framework. The
rows below are the clauses that touch what this agent generates. The document
is not in the repo; client-specific tables (storage accounts, the domain ->
schema list, catalog inventory) stay out of it too. If a check needs them,
they go in an overlay or the state root.

| Standard clause | Status here |
|---|---|
| STG and STD objects are Delta **managed** tables | Aligned: `acfc_prx` writes no LOCATION. |
| Databricks best practices: liquid clustering | Aligned: every DDL table `CLUSTER BY AUTO`. |
| Table and column metadata descriptions | Aligned: column / table COMMENTs from the STTM description (+ load strategy on the table COMMENT). |
| Table **and column** tags | **Partial**: table `DOMAIN` / `SUBDOMAIN` tags from the FRD (`ALTER TABLE … SET TAGS`, flag `ddl_tags_blank` when either is unstated); no column tags. Which column tags the standard means is not stated: open question. |
| ETL standard audit columns | Aligned: the STTM's trailing `NA` rows -> `audit_columns`. |
| Success / failure notifications with record counts | Aligned for the generated job (`on_success` + `on_failure`); record counts and the IIG email rows are the framework's. |
| STG attributes all **string** for file sources ("to avoid any data rejections"); RDBMS sources keep proper types | **Conflict**: under `acfc_prx` stage columns are typed as the STTM states them (`typed_stage: true`, decided 2026-10-29), and notebook mode stops the load on a value the type cannot read. The STTMs state the types, so either the STTMs or this clause gives: to be settled with the architecture team. No change until then. |
| STG load default Overwrite (Truncate & Load); any deviation approved by Data Architecture | **Not checked**: the agent transcribes the FRD's Load Strategy STG as stated. Proposed: a non-blocking `load_strategy_deviation:stage` flag citing the FRD cell (never a changed value). |
| STD load default Upsert (a full refresh still upserts only the impacted rows); Append needs architecture approval | **Not checked**, same as above: proposed `load_strategy_deviation:standard`. |
| STG schema for flat files = `STG_` + domain abbreviation; STD schema = the domain abbreviation (a 15-domain table) | **Not checked**: schemas come from the STTM stage / standard bands (authoritative, never derived; correct). At least one prod golden uses a schema outside the standard's abbreviation. Proposed: a check-only flag driven by an overlay domain -> schema table. The standard's schema abbreviations are a **different set** from the job-name `domain_abbreviations` above (Naming Standards table 3.4): keep them apart. |
| Catalogs `<env>_DLK` (STG) and `<env>_STD` (STD), plus separate PerformRx catalogs | Aligned for the two main catalogs (`catalog_map`, per environment). A PRX catalog an STTM names has no D1 mapping yet and is flagged `catalog_unmapped:<layer>`; its environment names go in the state root's environment file, never guessed. |
| STD default cleansing: trim strings, dates `YYYY-MM-DD`, timestamps ISO 8601 | **Open**: notebook v2 trims only where an IIG row states `LRTrimRule`; whether the framework applies these defaults or the IIG must state them is unknown. Ask before generating anything. |
| STD schema drift not recommended (STG may enable it) | Nothing to emit: the agent writes no schema-evolution options. |
| Reject tables with error description + standard layout; STG recycle / reject process | The framework's (IIG rows); notebook mode writes rejects to its reject path. |
| Inbound landing folder `mftlanding/inbound/<Domain>/<Sub-Domain>/<vendor>` | Aligned: `demo.source_files.landing_root_template` (display-only; the FRD's ADLS location wins). |
| No temp / transient data in STG; temp schema naming | Not applicable: the agent creates no tables. |
| RDBMS source in STD: Delta table vs view by query volume / core-source status | Not built: table ingestion (the RDMS sheet) is held. Applies when it is built. |
| Raw layer storage accounts and archival, Kafka / HVR routing, EDH, BSL, user access | Out of this agent's remit. |

**Proposed follow-ups** (none built yet):
1. Gate flags `load_strategy_deviation:<layer>` (STG not Truncate and Load, STD not Upsert), non-blocking, each citing the FRD Load Strategy cell.
2. A check-only schema-naming flag from an overlay domain -> schema table (values never in the tracked config).
3. Questions for the architecture team: stage string typing vs `typed_stage`; who applies the STD default cleansing; which column tags.

## What the SFMC FRD validation surfaced (2026-08-26)

Running the generator against a contract pair authored from
`FRD_STG_STD_SFMC_Email_Campaign_Tracking_Details_Ingestion_1005310`
(local, untracked — see CLAUDE.md fixture rules) found and fixed four real
gaps:

1. **`LoadStrategy` had no `"Upsert"`** — the SFMC standard layer is
   Upsert; the literal only allowed Truncate and Load / Append.
2. **Contiguous `YYYYMMDDHHMMSS` file stamps never tokenized**
   (`SFMC_CampaignInteractions_YYYYMMDDHHMMSS.csv` was matched literally);
   combined date-time tokens added to the placeholder map.
3. **`make_fixtures.py` broke its own ruff gate on wide natural keys**
   (SFMC's 8-column upsert key produced a 141-char line); the key list now
   renders one column per line.
4. **Two documented FRD phrasings fell through to Layer 2**: the
   incomplete-record-rejection rule (deterministically implemented by
   `rejects.py`) and the "Email notification should be sent…" rule (a
   `notification`). Both classifier patterns extended; the SFMC feed now
   compiles with **zero** unmapped rules.

Also fixed while validating: `run_demo.sh` now finds the venv python on
Windows (`Scripts/`) as well as POSIX (`bin/`).
