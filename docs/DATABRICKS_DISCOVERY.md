# Databricks discovery — B0 (2026-08-27, read-only)

Scope: list/describe/get ONLY. No statement execution of any kind (not even
`EXPLAIN`), no job runs, no writes. All calls via Databricks CLI v1.14.0
with `--profile DEFAULT` — the machine's single configured profile, which
is also the `[__settings__]`-declared default.

Redaction note: the workspace hostname and principal identity are written
as `<HEXAWARE_WORKSPACE_HOST>` / `<PRINCIPAL>` below — the two real values
live in the CLI profile (`~/.databrickscfg`, `DEFAULT`), not in this repo.

## Workspace & principal

- Host: `<HEXAWARE_WORKSPACE_HOST>` (Azure)
- Principal: `<PRINCIPAL>` — **workspace admin** (direct member of
  `admins`); entitlements: workspace-access, databricks-sql-access,
  workspace-consume, allow-cluster-create
- Auth: `databricks-cli` OAuth, token in OS keyring (not a PAT). Note for
  B1: the shipped `databricks-sdk` module authenticates via env/profile
  the same way; `DATABRICKS_TOKEN` in `.env.example` remains empty here.

## SQL warehouse

Exactly one:

| name | id | type | serverless | photon | auto-stop | state |
|---|---|---|---|---|---|---|
| Serverless Starter Warehouse | `172877b5178f7bb7` | PRO | yes | yes | 10 min | STOPPED |

→ `databricks.warehouse_id: "172877b5178f7bb7"` for B1 config. It was
STOPPED at discovery time; any future `EXPLAIN` (B2, cost-confirmed)
wakes it — that wake is DBU spend from the shared ~120/month pool.

## Serving endpoints — Claude models (all READY, task `llm/v1/chat`)

`databricks-claude-opus-5`, `databricks-claude-opus-4-8`,
`databricks-claude-opus-4-7`, `databricks-claude-opus-4-6`,
`databricks-claude-opus-4-5`, `databricks-claude-opus-4-1`,
`databricks-claude-sonnet-5`, `databricks-claude-sonnet-4-6`,
`databricks-claude-sonnet-4-5`, `databricks-claude-sonnet-4`,
`databricks-claude-haiku-4-5`.

`databricks-claude-opus-4-8` exists and is READY — it matches
`config.reasoning.model: claude-opus-4-8` exactly, so the B1
`databricks_fmapi` provider can serve the same model the Anthropic
provider uses today (Anthropic stays the sole model vendor; FMAPI is a
transport). Non-Claude endpoints (gpt-oss, llama, qwen, gemma, embedding
models) exist but are out of scope by program policy.

## Catalogs / schemas (readable by this principal)

`system`, `samples` (system) plus managed: `ai_prac`, `migration`,
`amaze_omnicore`, `hexapsa`, `iph_dbx_catalog`, `hexa_dbx_insurance`,
`soham_workspace`, `ai_ready_data`, `omnissa_agents_demo`,
`data_science`, `lakebridge_oraexport`.

Program-relevant:

- **`soham_workspace.sttm_agent`** — the FRD→STTM agent's state: tables
  `frd_contracts`, `frd_documents`; volumes `frd_raw`, `sttm_out`,
  `sttm_reference`.
- `soham_workspace.default` — volume `brd_to_frd` (descoped agent's
  leftover).
- `hexa_dbx_insurance.amerihealth_dataforge` — tables `delivery_configs`,
  `extract_configs`, `extract_runs`, `sftp_connections`; volume
  `outbound`. (Metadata-driven extract config shape — closest analogue in
  this workspace to the client's metadata-driven Workflows doctrine.)
- `ai_ready_data.claims_stage1` — full medallion set (`bronze_*`,
  `silver_*`, `gold_*` per entity, plus `dq_*` materialized views,
  `*_metrics` metric views): the best stage/standard-like tables for the
  B2 grounding checks to be exercised against.

## Stage/standard-like tables — verbatim

### `soham_workspace.sttm_agent.frd_contracts` (MANAGED, DELTA)

```
doc_id            string
status            string
n_feeds           int
n_ambiguities     int
n_strict_failed   int
contract          string
audited_at        timestamp
```

### `ai_ready_data.claims_stage1.bronze_medical_claim` (MANAGED, DELTA — stage-like)

```
claim_id             string
patient_id           string
encounter_id         string
practitioner_id      string
service_date         date
claim_status         string
billed_amount        double
allowed_amount       double
paid_amount          double
diagnosis_code       string
procedure_code       string
place_of_service     string
created_at           date
_rescued_data        string
_bronze_loaded_at    timestamp
_bronze_source_file  string
_bronze_entity       string
```

### `ai_ready_data.claims_stage1.silver_medical_claim` (MANAGED, DELTA — standard-like)

```
claim_id               string
patient_id             string
encounter_id           string
practitioner_id        string
service_date           date
claim_status           string
billed_amount          double
allowed_amount         double
paid_amount            double
diagnosis_code         string
procedure_code         string
place_of_service       string
created_at             date
_rescued_data          string
_silver_processed_at   timestamp
diagnosis_description  string
diagnosis_category     string
pos_description        string
care_setting           string
service_year           int
service_month          int
cost_band              string
is_high_cost           boolean
payment_variance       double
```

## Observable managed-table defaults

From `tables get` properties on the three tables above (no settings API
touched):

- Format DELTA, managed; `delta.enableDeletionVectors = true`;
  `delta.parquet.compression.codec = zstd`; reader v3 / writer v7;
  collation `UTF8_BINARY`; predictive-analyze auto statistics
  (`spark.sql.statistics.auxiliaryInfo source=PREDICTIVE_ANALYZE`).
- Newer tables additionally get row tracking
  (`delta.enableRowTracking = true`).
- **NOT present by default: `delta.enableChangeDataFeed`, and no
  clustering columns / CLUSTER BY AUTO markers.** The client doctrine
  (all new tables managed, `CLUSTER BY AUTO`, CDF on) is therefore an
  explicit-DDL obligation, not something the workspace grants for free —
  the planned B2 PASS_WITH_FLAGS check ("managed/CLUSTER BY AUTO/CDF
  unset on an existing target") will have real findings.

## Wrapper-notebook / job candidates

- **Jobs: none.** `jobs list` returns empty. **Pipelines: none.**
- Parameterized notebooks (the FRD→STTM agent's, under
  `/Users/<PRINCIPAL>/` — the only workspace code present;
  `/Shared` and `/Repos` are empty):
  - `01_frd_ingest` — widgets: `catalog`, `schema`, `table`,
    `raw_volume`, `preview_volume`
  - `02_contract_build` — widgets: `catalog`, `schema`, `docs_table`,
    `contracts_table`, `out_volume`, `agent_endpoint`,
    `extraction_source` (dropdown)
  - `03_sttm_render` — widgets: `catalog`, `schema`, `contracts_table`,
    `runs_table`, `out_volume`, `reference_volume`
- These already follow the client's parameter doctrine: every widget is a
  UC coordinate, table name, or endpoint name — IDs the notebook resolves
  against metadata; never inline SQL, nowhere near the ~250 KB parameter
  cap. The closest stand-in for the client's common wrapper notebook is
  this trio's shape; an actual wrapper job would have to be **created**,
  which is out of scope for this session (no `create_job`).

## Lakebase

CLI surface exists (`databricks database …`, Public Preview);
`list-database-instances` returns **zero instances**. Lakebase is
available but unused in this workspace.

## Calls used (all read-only, all `--profile DEFAULT`)

```
databricks --version
databricks auth describe
databricks current-user me -o json
databricks catalogs list -o json
databricks warehouses list -o json
databricks serving-endpoints list -o json
databricks schemas list <catalog> -o json          # × 11 managed catalogs
databricks jobs list [-o json]
databricks pipelines list-pipelines -o json
databricks tables list soham_workspace sttm_agent -o json
databricks tables list hexa_dbx_insurance amerihealth_dataforge -o json
databricks tables list ai_ready_data claims_stage1 -o json
databricks tables list ai_ready_data metadata -o json
databricks volumes list <catalog> <schema> -o json  # × 8 likely schemas
databricks tables get soham_workspace.sttm_agent.frd_contracts -o json
databricks tables get ai_ready_data.claims_stage1.bronze_medical_claim -o json
databricks tables get ai_ready_data.claims_stage1.silver_medical_claim -o json
databricks database list-database-instances -o json   # + --help (probe only)
databricks workspace list / | /Users | /Users/<me> | /Shared | /Repos
databricks workspace export /Users/<me>/{01_frd_ingest,02_contract_build,03_sttm_render} --file <scratchpad>
```

(Notebook exports went to the session scratchpad outside the repo and are
disposable; nothing was cached into the repo.)

## Proposal: `demo.databricks_paths` (decision needed before the client demo)

**No landing-style volume exists in this workspace.** Nothing named or
shaped like `mftlanding`/inbound-MFT was found; the only real volumes are
the FRD→STTM agent's (`frd_raw`, `sttm_out`, `sttm_reference`),
`brd_to_frd`, `outbound` (dataforge), and two unrelated demo volumes.

Two honest options — my recommendation is **Option A**:

**Option A (recommended): keep the placeholders, sharpen the SYNTHETIC
header.** `hexaware_demo/landing/mft` stays in config, and the shell
block's header line becomes:

> "SYNTHETIC — rendered from the FRD's landing location and file
> patterns; not a live listing. No landing volume exists in the Hexaware
> workspace yet — creating one (e.g.
> `soham_workspace.codegen_agent.mftlanding`) is the Databricks seam's
> first write task, after which this becomes a real `fs ls`."

Rationale: every real volume in the workspace belongs to another agent's
pipeline; pointing the demo path at one would render a path that implies
feed files land where FRD documents actually do. A placeholder that says
it's a placeholder beats a real name that lies about its contents.

**Option B: real volume root, synthetic listing.**
`demo.databricks_paths: {catalog: soham_workspace, schema: sttm_agent,
volume: frd_raw}` → renders
`dbfs:/Volumes/soham_workspace/sttm_agent/frd_raw/mftlanding/inbound/…`.
The volume genuinely exists (an `fs ls` of its root would succeed), but
it is the FRD-document inbox, not an MFT landing zone — the SYNTHETIC
label must then carry that extra caveat. Only worth it if tomorrow's
audience will ask "is that a real volume?" and a yes matters more than
the mixed semantics.

Creating a proper landing volume is a **write** and stays out of scope
until an explicit go (B1+, and it needs the DBU/permissions conversation
with the ingestion owner).

**Decision 2026-08-27: Option A.** `demo.databricks_paths` keeps
`hexaware_demo/landing/mft`; the shell block's SYNTHETIC header gets the
sharpened text; `frd_raw` is not used.

## B1/B2 inputs

The facts the seam build consumes, in one place:

- **Warehouse:** `172877b5178f7bb7` ("Serverless Starter Warehouse",
  serverless PRO, Photon). Auto-stop 10 min and **STOPPED at discovery**
  — any `EXPLAIN` (B2, cost-confirmed) wakes it, and that wake is DBU
  spend from the shared ~120/month pool.
- **Serving endpoint:** `databricks-claude-opus-4-8` (READY,
  `llm/v1/chat`) — matches `config.reasoning.model: claude-opus-4-8`
  exactly; the `databricks_fmapi` provider serves the same model the
  Anthropic provider uses today.
- **UC grounding stand-ins:** the two verbatim medallion tables above —
  `ai_ready_data.claims_stage1.bronze_medical_claim` (stage-like) and
  `ai_ready_data.claims_stage1.silver_medical_claim` (standard-like) —
  are the targets the B2 checks (`table_exists`, `describe_table`,
  column/dtype comparison) get exercised against.
- **Observed defaults:** managed Delta tables come with deletion vectors,
  zstd, predictive stats — but **no `delta.enableChangeDataFeed` and no
  CLUSTER BY AUTO**. B2's "doctrine unset on existing target"
  PASS_WITH_FLAGS check is therefore *expected to fire* on existing
  tables; that is signal, not noise.
- **Absent, so stubbed:** zero jobs, zero pipelines, zero Lakebase
  instances. The wrapper-job path (`get_job`) and any IG-load/Lakebase
  path stay stubbed in B1 until real targets exist; nothing in this
  workspace can be pointed at today without creating it first.
