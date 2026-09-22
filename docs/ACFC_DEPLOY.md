# Deploying CodeGen inside ACFC (v0.5.8-acfc)

How to stand the agent up in ACFC's own Databricks workspace, written around
what the workspace itself proved (recorded by Genie Code on 2026-09-18 in
`docs/acfc/ENVIRONMENT_ACFC.md` and `docs/acfc/RETROFIT_LOG.md` — scrubbed
copies: workspace identifiers are `<placeholders>`). Values in `<angle brackets>` are ACFC's and are set in the App's
environment or a config overlay, never in the tracked `config/config.yaml`.

## 1. What the workspace proved — and what follows from it

| Fact (ENVIRONMENT_ACFC / RETROFIT_LOG) | Consequence in v0.5.0 |
| --- | --- |
| The App container does **not** receive gitignored files (`inputs/`, `*.docx`, `*.xlsx`), so documents copied into the Git folder never reach the App (§c, log #6). | Inputs are read through a storage URI (`workspace:` / `volume:`), listed and downloaded by API. |
| `/Volumes` is **not** a usable filesystem: `Path.mkdir(parents=True)` on a `/Volumes/…` path from serverless raises `PermissionError: [Errno 13] … '/Volumes'` (log #5, #8); an App container has no such mount at all. | No code path treats `/Volumes` or `/Workspace` as a path. `volume:` goes through the Files API, `workspace:` through the Workspace API. `local:/Volumes/…`, and a `/Volumes` path in `layout.runtime_cache_dir`, are refused at config load with the remedy. |
| Directories may only be created **below** a root the caller can write; the root (and its ancestors) cannot be created (same error). | Every backend creates folders only below its root. A missing root is a named configuration error, never an attempted `mkdir`. **Create the root folders up front (§3).** |
| The App's service principal has **zero** Unity Catalog grants and the deploying user lacks `MANAGE` on the catalog, so cannot grant (§d, log #9). | The App runs entirely on **workspace folders shared with the service principal** — a folder permission the user can give, no catalog admin involved. UC volumes become an option once an admin runs §4. |
| Four of the ten pairs share one ticket number, so ticket pairing pairs nothing (log #7). | Pairing is by **content** (§7); the ten-entry `pairing_map` with real file names is not needed and stays out of tracked config. |
| The real pair-1 STTM leaves six roles unresolved under synonyms with the mock recognizer (log #2) — the stage / standard table, column and type columns. | Three ways forward, in order of preference: the **live recognizer** (§5), an **answers file** (§6), or the UI's layout dialog. `unresolved_headers.md` takes the header strings home without any data. |
| Serverless notebook: Python 3.12.3; Apps runtime: documented as Python 3.10+ (§a). | The package supports **Python 3.10 – 3.12**; the suite runs on 3.10, 3.11 and 3.12. |
| PyPI resolves; `pip install -e .[ui,databricks]` dry-runs clean (§b). | `requirements.txt` (`.[ui,databricks]`) is the App's install, unchanged. |
| `conventions.default_catalog` was rejected by the v0.4.2 loader (log #1). | It is a real key since M7.1 — see §2. |

## 2. Config: one overlay, nothing workspace-specific in the tracked file

Put ACFC's values in an overlay (`CODEGEN_CONFIG_OVERLAYS=<path.yaml>`) — a
YAML mapping deep-merged onto `config/config.yaml` before validation. The
loader refuses unknown keys, so a typo fails at start-up.

```yaml
# acfc.overlay.yaml — lives in the shared workspace folder, NOT in the repo
databricks:
  catalog: <catalog>                 # only for the volume fetch / publish panels
  schema: <schema>
  frd_volume: <raw FRD volume>
  sttm_volume: <raw STTM volume>
  output_volume: <publish volume>
  serving_endpoint: databricks-claude-opus-5
conventions:
  profile: acfc_prx
  default_catalog: {stage: <stage catalog>, standard: <standard catalog>}
metadata: {template: iig_v2}
playbook: {template: main_single}
layout: {provider: live, endpoint: databricks-claude-opus-5}
```

| Section | Key | Why |
| --- | --- | --- |
| `conventions.profile` | `acfc_prx` | one combined `<ABBREV>_DDL.txt`, typed stage columns, the DML deliverable, three-part names |
| `conventions.default_catalog` | `{stage, standard}` | the LAST link of the catalog chain (FRD label → STTM band → here, provenance `config_default`); without it `acfc_prx` FAILs `catalog_unstated:<layer>` for a pair that states no catalog |
| `metadata.template` / `playbook.template` | `iig_v2` / `main_single` | the PRX package layouts |
| `layout.provider` / `layout.endpoint` | `live` + the endpoint name | §5 |
| `storage.*`, `inputs.extra_dirs` | storage URIs | §3 — usually set as App env instead |

ACFC's pipeline / notebook inventory for the IIG
(`metadata.templates.iig_v2.template_rows`) and any explicit
`demo.pairing_map` entries also belong in the overlay. Per-feed answers the
documents do not state go in `fixtures/faq/<feed_slug>.faq.yaml`, each with
its citation; unanswered means blank-and-flag, never a guess. The real
prod-support DL is `CODEGEN_NOTIFICATION_EMAILS` in the App env.

## 3. Storage: workspace folders shared with the App's service principal

Three roles, one storage URI each:

| Role | What lives there | Config key | Env (wins) | Default |
| --- | --- | --- | --- | --- |
| inputs | the inboxes `uploads/`, `databricks/`, `sharepoint/` | `storage.inputs` | `CODEGEN_STORAGE_INPUTS` | `local:./inputs` |
| state | `decisions.json`, `layout_profiles/` (runtime profile cache) | `storage.state` | `CODEGEN_STORAGE_STATE` | `local:./ui/backend/state` |
| outputs | `demo_<timestamp>/…` run folders, CLI output | `storage.outputs` | `CODEGEN_STORAGE_OUTPUTS` | `output.dir` (local) |
| extra inputs (read-only) | folders of documents, scanned at depth 1 (`pair_1/ … pair_N/`) | `inputs.extra_dirs` | `CODEGEN_EXTRA_INPUT_DIRS` (`;`-separated) | none |

URI forms: `local:<dir>` · `workspace:/Workspace/Users/<user>/<folder>` ·
`volume:/Volumes/<catalog>/<schema>/<volume>/<folder>`. The generator still
reads and writes local files: a remote role has a local working copy (system
temp, or `CODEGEN_STORAGE_SCRATCH`) that is filled before a document is read
and pushed after a result is written. The App container's disk is wiped on
every restart; a remote state / outputs role is what survives it (past runs
are pulled back when listed).

**Set-up, once, by the user — no admin needed:**

1. Create the folders (Workspace → your user folder → Create → Folder):
   `codegen/pairs` (put `pair_1/ … pair_N/` inside, each with its STTM, FRD
   and VDD), `codegen/inputs`, `codegen/state`, `codegen/outputs`. **The
   agent never creates a root** — a missing one is reported by name.
2. Find the App's service principal: `databricks apps get codegen-agent`
   → `service_principal_name` / `service_principal_client_id`.
3. Share the folders with it (folder → **Share** → add the service
   principal): **Can Manage** on `codegen/state` and `codegen/outputs` (and on
   `codegen/inputs`, which the App's upload and fetch write to); **Can Read**
   on the `codegen/pairs` folder, which is only listed and downloaded.

   **Can Edit is not enough on a folder the App writes NEW files into**
   (observed 2026-09-21 in the ACFC workspace): with CAN_EDIT the first write
   of `selection.json` fails with `Missing required permissions [Manage] on
   node with ID …`. CAN_EDIT covers changing objects that already exist;
   CREATING one in a directory is a Manage operation. The state role writes
   `selection.json`, `document_index.json`, `decisions.json` and the layout
   cache; the outputs role writes a run's artefacts. CLI equivalent, once per
   folder:

   ```bash
   databricks workspace get-status /Users/<user>/codegen/state     # -> object_id
   databricks workspace update-permissions directories <object_id> --json \
     '{"access_control_list":[{"service_principal_name":"<app-sp-client-id>","permission_level":"CAN_MANAGE"}]}'
   databricks workspace get-status /Users/<user>/codegen/pairs     # -> object_id
   databricks workspace update-permissions directories <object_id> --json \
     '{"access_control_list":[{"service_principal_name":"<app-sp-client-id>","permission_level":"CAN_READ"}]}'
   ```

Workspace files are limited to 10 MB per import call — far above any artefact
the agent writes; a very large input workbook belongs in a volume.

## 4. Grants for the admin (when UC volumes and live model calls are wanted)

Nothing in §3 needs these. They enable `volume:` storage roles, the UI's
volume fetch / publish panels, and live model calls.

```sql
-- Unity Catalog (a principal with MANAGE on the catalog runs these)
GRANT USE CATALOG ON CATALOG <catalog> TO `<app-sp-client-id>`;
GRANT USE SCHEMA  ON SCHEMA  <catalog>.<schema> TO `<app-sp-client-id>`;
GRANT READ VOLUME ON VOLUME  <catalog>.<schema>.<raw FRD volume>  TO `<app-sp-client-id>`;
GRANT READ VOLUME ON VOLUME  <catalog>.<schema>.<raw STTM volume> TO `<app-sp-client-id>`;
GRANT READ VOLUME, WRITE VOLUME ON VOLUME <catalog>.<schema>.<state / outputs volume> TO `<app-sp-client-id>`;
GRANT READ VOLUME, WRITE VOLUME ON VOLUME <catalog>.<schema>.<publish volume>         TO `<app-sp-client-id>`;
```

`CAN_QUERY` on the serving endpoint (not SQL — an endpoint permission):

- **Declaratively (preferred):** App → Edit → **Resources** → add *Serving
  endpoint* `databricks-claude-opus-5`, permission **Can query**, key
  `llm-endpoint`. The platform grants the App's service principal the
  permission on deploy.
- **Or by CLI:**

  ```bash
  databricks serving-endpoints get databricks-claude-opus-5        # -> id
  databricks serving-endpoints update-permissions <endpoint-id> --json \
    '{"access_control_list":[{"service_principal_name":"<app-sp-client-id>","permission_level":"CAN_QUERY"}]}'
  ```

The upstream FRD-contracts table read (optional) additionally needs `SELECT`
on that table and `CAN_USE` on the SQL warehouse.

## 5. Model posture: two independent switches

| Switch | Values | Effect |
| --- | --- | --- |
| `CODEGEN_FORCE_MOCK_PROVIDER=1` (App env; **set in the shipped `app.yaml`**) | set / unset | Layer 2 (rule reasoning) is mock-locked. Remove it and redeploy once `CAN_QUERY` is in place. |
| `layout.provider` / `CODEGEN_LAYOUT_PROVIDER` | `auto` (default: live only when Layer 2 is live) · `mock` · `live` | `live`: the layout recognizer queries `layout.endpoint` / `CODEGEN_LAYOUT_ENDPOINT` (else `databricks.serving_endpoint`) **even while Layer 2 stays mock-locked**. Needs `CAN_QUERY` (§4). |
| `CODEGEN_FORCE_MOCK_LAYOUT=1` | set / unset | locks the recognizer to mock regardless of the above. |

The live recognizer sends the same request as the mock — the fingerprint
material only: header regions and table labels, never a data row — and its
answer passes the same validator before any role is merged; no model string
reaches a contract, DDL or IIG cell (`docs/LAYOUT_RECOGNITION.md`). A
completed profile is cached in the state role (`<state>/layout_profiles/`), so
a workbook is asked about once. Runtime profiles carry real sheet names and
are **never** written under `fixtures/` (refused in code and at config load).

## 6. When roles stay unresolved: the answers file

```bash
codegen layout --workbook STTM.xlsx --frd FRD.docx --vdd VDD.xlsx \
               --report-unresolved unresolved_headers.md --require-complete
```

`unresolved_headers.md` lists, per unresolved role, the sheet name as written,
the header-row texts and the candidate columns — **structural labels only, no
data rows** — so it can leave the workspace and the strings be added to the
synonym tables (`extractor.discovery` / `extractor.vdd` / `extractor.frd`, in
an overlay). Until then, place the roles by hand:

```yaml
# answers.yaml — (document, sheet, role) -> column header text, index or letter
answers:
  - document: sttm
    sheet: "FEED_1_MAPPING"            # as written in the workbook
    layer: stage                       # needed when the role is open in two bands
    role: table
    column: "Target Table Name in DL"  # header text (compared normalized)
  - {sheet: "FEED_1_MAPPING", layer: stage,    role: schema,      column: T}
  - {sheet: "FEED_1_MAPPING", layer: stage,    role: column,      column: 22}
  - {sheet: "FEED_1_MAPPING", layer: stage,    role: target_type, column: W}
  - {sheet: "FEED_1_MAPPING", layer: standard, role: table,       column: "Target Table Name in DL"}
  - {sheet: "FEED_1_MAPPING", layer: standard, role: column,      column: 29}
  - {sheet: "FEED_1_MAPPING", layer: standard, role: target_type, column: AD}
gaps:                                   # choice / layer questions, by question key
  "feeds[0].file_format": {value: "Fixed Width"}
pairing:                                # an undecided content pairing (§7)
  "STTM.xlsx": {frd: "FRD.docx", vdd: "VDD.xlsx"}
```

```bash
codegen layout       --workbook STTM.xlsx --frd FRD.docx --answers answers.yaml --require-complete
codegen extract-sttm --workbook STTM.xlsx --frd-contract frd.contract.json \
                     --answers answers.yaml --out sttm.contract.json
```

An answer may set ANY role, open or not (v0.5.1): it lands with `source=user`
through the same merge and validation as the dialog's answers, and where it
conflicts with a synonym / model / cached placement the answer wins (`NOTE …
overrides column N (synonyms) with column M`). An entry that names no sheet /
band of the document is reported, never applied elsewhere. The schema is a
REQUIRED role in both target bands, so a profile without it always asks. In
the UI the same questions appear in the layout dialog (state `needs_layout`):
choose, **Continue**; **Proceed with unresolved** reads the remaining roles as
empty and gate-flags them; **Re-resolve layout** starts over past the caches.

**A cached profile that is wrong** (the 2026-09-21 run was stuck on one that
lacked the schema): nothing needs deleting. A runtime entry made under other
synonym tables, or one that lacks a required role, is ignored and re-resolved
on its own; to force it, `codegen layout … --refresh` (the notebook's
`refresh_layout` widget, the UI's "Re-resolve layout" checkbox) bypasses every
cache and overwrites the entries. When a model answer is rejected the full
reasons are in `<state>/layout_profiles/rejections/<fingerprint>.json`.

## 7. Pairing by content

Choosing an STTM scores every FRD and VDD candidate on what the documents
say — FRD feed / object name in the STTM's header region, target tables and
schemas against the STTM's bands, file patterns against its file-details rows
(the one-block / many-files FRD lists file names as "tables"; both are
compared); VDD FILES-sheet patterns, format, delimiter and cadence against the
STTM's file and meta rows. The ticket number and the file-name stem are two
weak signals among several. A candidate is paired only when it reaches
`inputs.pairing.min_score` **and** leads the next by `margin`; otherwise the
top candidates — each with its score and the cells behind it — are asked in
the layout dialog when the run starts, or printed by `codegen pair --sttm X`
with the `pairing:` remedy for the answers file. An explicit
`demo.pairing_map` / `vdd_pairing_map` entry (overlay) still overrides. A
manual pick in the chooser always wins. When no document says anything in
common, the pre-0.5 name rules (unique shared ticket, else unique name stem)
still apply.

## 8. Deploy and redeploy

First deploy — **Compute → Apps → Create app → Custom** → name `codegen-agent`
→ source code path: the Git folder of `staging` → Resources: the serving
endpoint (§4) → Create. The shipped `app.yaml` sets the command and
`CODEGEN_FORCE_MOCK_PROVIDER=1`; add the workspace values as App env:

```yaml
env:
  - {name: CODEGEN_FORCE_MOCK_PROVIDER, value: "1"}          # remove once CAN_QUERY is in place
  - {name: CODEGEN_EXTRA_INPUT_DIRS, value: "workspace:/Workspace/Users/<user>/codegen/pairs"}
  - {name: CODEGEN_STORAGE_INPUTS,   value: "workspace:/Workspace/Users/<user>/codegen/inputs"}
  - {name: CODEGEN_STORAGE_STATE,    value: "workspace:/Workspace/Users/<user>/codegen/state"}
  - {name: CODEGEN_STORAGE_OUTPUTS,  value: "workspace:/Workspace/Users/<user>/codegen/outputs"}
  - {name: CODEGEN_CONFIG_OVERLAYS,  value: "<path to acfc.overlay.yaml inside the source tree>"}
  - {name: CODEGEN_LAYOUT_PROVIDER,  value: "live"}           # optional, §5
  - {name: CODEGEN_NOTIFICATION_EMAILS, value: "<prod-support DL>"}
```

Keep a workspace-specific `app.yaml` out of the shared branch (a user email in
a path is a workspace identifier).

Redeploy sequence, every time `src/` or `ui/` changes:

1. Pull `staging` in the Git folder.
2. Check `requirements.txt`'s `codegen-version-marker` differs from the
   deployed one (it moves with the `pyproject.toml` version — 0.5.8 now). The
   Apps runtime caches the installed environment keyed on that file; an
   unchanged marker serves stale code.
3. `databricks apps deploy codegen-agent --source-code-path /Workspace/<path-to-the-git-folder>`
   (or **Deploy** in the UI).
4. Open the App → Generate → **Choose documents…**: the pair folders list
   under their folder names (`pairs/pair_1`, …). An input root the App cannot
   list is reported by name with the API's message, and the rest still lists.
5. After a restart nothing local survives: selections reset; past runs reload
   from the outputs role.

`ui/frontend/dist` is tracked, so the Git folder carries the built bundle —
no Node toolchain is needed in the workspace (there is no `npm` on the
serverless image).

### The notebook fallback

`acfc_run.py` (repo root, Databricks notebook source) runs one pair from a
serverless notebook with the same storage URIs as widgets: it downloads the
pair folder by API, pairs by content, resolves the layout with the answers
file (writing `unresolved_headers.md` and stopping when roles stay open),
extracts, generates in `rfc` mode and pushes the outputs to the outputs role.
Since v0.5.1 the FRD contract is the one the LAYOUT step writes
(`--frd-contract-out`: the pair-resolved contract — a feed the FRD leaves
unnamed is named after the STTM stage band), the conventions profile / IIG /
playbook templates are widgets passed to `generate` (never an edit of
`config.yaml`; `generate` used to drop `--profile` / `--vdd` silently), and
`refresh_layout` re-resolves past the cached profiles.
Use it when the App is stopped or its service principal has no access yet —
the notebook runs as the user, whose own folders need no sharing.

## 9. What to compare against the pair-1 golden

Run pair 1 (`f1_pair_1.docx` + `pair_1_family_a.xlsx` + `pair_1_v1_segments.xlsx`)
under `acfc_prx` / `iig_v2` / `main_single` with the pair-1 overlay loaded,
then check (this is exactly `tests/test_m4_acceptance.py` and
`tests/test_m5_rfc_package.py`):

- `framework/ACCUM_DDL.txt` (and the copy in `RFC######_ACCUM/`) is
  byte-identical to `fixtures/acfc_shapes/pair_1/golden/ACCUM_DDL.txt` —
  including the `Decimal(17,2)`→`Decimal(22,2)` run, which the gate flags
  (`drag_fill_suspect`) and never alters.
- `config_rows.xlsx` / `ACCUM_IIG.xlsx`: eight sheets in the golden's order,
  identical headers, row counts 4/1/4/1/3/3/8/2; the pinned columns
  (`PINNED_COLUMNS` in the M4 test) equal the golden verbatim; every other
  cell blank and listed in the `iig_blank:<SHEET>: …` flags.
- Verdict `PASS_WITH_FLAGS` with `segments_from_sttm`, `file_pattern_from_sttm`,
  one `drag_fill_suspect`, eight `iig_blank` (one per sheet), the `playbook_blank`
  set, `rfc_number_unanswered` (until the FAQ answers it) and the six
  `faq_unanswered` questions. No `vdd_*` flag.
- The package: `RFC######_ACCUM/ACCUM_DDL.txt`, `ACCUM_IIG.xlsx`,
  `RFC######_ACCUM_Deployment_Playbook.xlsx`, `MANIFEST.md`.

Cells the golden fills that the fixture universe cannot determine (per-file
`SOURCE`/`FREQUENCY`, `TGT_REFRESH_TYPE` Overwrite on the stage legs, the
handler's `VERSION`/`SEGMNT_TYP`/`FILE_TYPE`/`EXTENSION`, the email wording)
are expected to differ or be blank — they are the open questions for the
framework team listed in `CLAUDE.md`.

## What v0.6.0-acfc adds (M10 — the environment probe, read-only)

Before this the artefacts assumed an empty target: every table a `CREATE OR
REPLACE`, every config row an `INSERT`. Now, when the probe is on, the run
asks the environment first — each stage / standard table of the deployment
DDL (`DESCRIBE TABLE` through a SQL warehouse) and each config row the DML
would insert (one keyed `SELECT` per row against the metadata DB) — and each
object reads **absent | identical | different | unreadable**, with the query
and the timestamp as evidence (`<state>/env_probe/<feed>.json`, the report's
"Environment" section, the feed page's Environment table, flags `env_absent`
/ `env_identical` / `env_different` / `env_unreadable`).

What the artefacts then do:

| State | DDL (`conventions.profiles.<p>.reconcile_ddl`, on for `acfc_prx`) | DML (`config_inserts_<env>.sql`, the probed environment only) |
| --- | --- | --- |
| absent | CREATE, as before | INSERT, as before (+ an assertion: still absent) |
| identical | a comment, no CREATE | a comment, no INSERT (+ an assertion: still identical) |
| different | `ALTER TABLE … ADD COLUMNS` for additive drift; a REVIEW block, no statement, for type / removal differences. Never DROP, never CREATE OR REPLACE over an existing table | a REVIEW block naming the key and both values of every differing column, a **commented-out** UPDATE candidate, and an assertion that fails while the row still differs. `dml.emit_updates: true` turns the candidate live — only once the framework team confirms an update path exists (question 19 in `docs/acfc/METADATA_DB_SEMANTICS.md` §11) |
| unreadable | as before | as before |

`unreadable` is a **flag, never a stop**. Row status columns
(`dml.status_columns`: `ACTIVE_FLAG` …) are shown in the report when they
differ and never touched, unless the load-pattern FAQ answers
`manage_row_status: yes`. A row whose natural key (`dml.natural_keys`) has no
value at generation time — an unassigned `@GROUP_ID`, a client-filled
`PROCESS_NAME` — or is shared by several rows of the feed reads `unreadable`
and says why; it is never guessed at. With the probe **off**, or when every
object is absent / unreadable, every artefact is byte for byte what it was
(pinned: CV, SFMC and pair 1).

**It is off, and it stays off until granted.** The tracked config ships
`env.probe.enabled: false` and every workspace value blank. Turn it on in
the App's env (an overlay works too):

```
CODEGEN_ENV_PROBE=1
CODEGEN_ENV_PROBE_WAREHOUSE_ID=<a SQL warehouse the App SP has CAN USE on>
CODEGEN_ENV_PROBE_ENVIRONMENT=q1            # which metadata DB this workspace's is
CODEGEN_ENV_PROBE_SECRET_SCOPE=<scope>      # + _JDBC_URL_SECRET / _USER_SECRET / _PASSWORD_SECRET
```

What each half needs:

- **Unity Catalog** — the App's service principal needs **CAN USE** on the
  warehouse (today it has none: every table reads `unreadable` with that
  reason) and USE CATALOG / USE SCHEMA / SELECT on the target tables. Each
  probe is one `DESCRIBE TABLE` per table; a `DESCRIBE` wakes an auto-stopped
  warehouse.
- **The metadata DB** — a **read-only** SQL Server login, its JDBC URL / user
  / password in a secret scope the SP can read (secret NAMES in config, values
  only in the workspace), and the `[envprobe]` extra (`pymssql`) in the App's
  `requirements.txt` — the App container has no JVM. Without the extra that
  half reads `unreadable` naming the extra.
- `databricks.warehouse_id` is **never** a fallback — it names another
  workspace's warehouse.

**Where it runs.** In the App: on the run's own thread, after the contracts
resolve, every query bounded by `env.probe.timeout_seconds` (a query that
hangs is given up, not waited for), never on a request path. In the notebook
fallback (`acfc_run.py`, widget `env_probe = run`): two passes — `generate
--env-expected-out` writes what the artefacts expect, the notebook probes
in-process through its own SparkSession (`DESCRIBE TABLE` on the notebook's
compute, the metadata DB over Spark JDBC with `dbutils.secrets`), then
`generate --env-probe-result` emits the adjusted artefacts.

**UNVERIFIED (2026-09-21):** neither transport has run against a real
workspace or a real SQL Server — the suite drives fakes (`tests/env_fakes.py`,
`tests/test_m10_env_probe.py`). Outside a Databricks runtime the probe
resolves nothing at all: no CLI profile is ever consulted, every object reads
`unreadable`. The suite runs under a socket guard (`tests/conftest.py`): an
outbound connection fails the test that made it.

## What v0.5.8-acfc adds (Generate works right after a restart)

Starting a run now supersedes the startup **restore** job instead of being
refused by it ("'the recorded selection' is still being selected"). On a slow
workspace that restore takes seconds per document, and it is not the person's
act. Found by the new end-to-end test below, not on site.

**A whole live run under remote roles is now tested**
(`tests/test_remote_run_e2e.py`): inputs / state on a fake workspace, outputs
on a fake volume, the real `_execute` — generate, list, push. Both v0.5.6 and
v0.5.7 were App-only failures that a green suite missed because every other
run test uses the default LOCAL roles; this one covers that shape.

## What v0.5.7-acfc adds (a run with a REMOTE outputs role finishes)

With `storage.outputs` on a workspace / volume root, a run's working copy is
the role's temp directory (`/tmp/codegen_storage/outputs_<id>/…`) — outside the
App's code directory. The UI listed every generated file as repo-relative, so
`Path.relative_to` raised `'…' is not in the subpath of '/app/python/
source_code'` for EVERY feed and the App reported **"live run produced no
feeds"** with nothing published — after the generation itself had succeeded.
`ui/backend/service.py::display_path` now keeps the absolute path when a run
lives outside the checkout (the UI only needs the `/<feed_slug>/` segment).
Regression test: `tests/test_remote_outputs_paths.py` generates a real feed
into a root outside the repo.

## What v0.5.6-acfc adds (a document stays chosen)

- **Pairing and recording are best-effort.** Only locating and reading the
  workbook can fail a selection. When the FRD / VDD pairing raises, or the
  state role cannot be written, the step is a **warning** on the job and the
  STTM STAYS SELECTED. v0.5.4 / v0.5.5 failed the whole selection there: in
  the ACFC workspace the App's SP had CAN_EDIT (not CAN_MANAGE) on the state
  folder, `selection.json` could not be created, and choosing an STTM
  therefore selected nothing at all — the picker looked stuck. Grant
  **Can Manage** (§3) to have the choice survive a container restart; without
  it the agent still runs, and says so on the job.
- The page now polls the status the whole time the chooser is open, says in
  plain text why Generate is disabled, and shows a failed selection with the
  chooser CLOSED too (it used to be inside the modal only). A startup
  `restore` job no longer disables the chooser.
- **The UI bundle must match the backend.** The old bundle crashes (blank
  page) against the 202-job response of v0.5.5+: if the App serves a stale
  `ui/frontend/dist`, re-sync it — `databricks sync` honours a `.gitignore`
  in the staged tree and silently skips `dist` (§"Deploying"). Check the
  served page names the freshly built asset hash.

## What v0.5.5-acfc adds (the chooser can no longer hang the App)

The site record (`docs/acfc/APP_CHOOSER_BUG.md` on the run-records branch):
choosing the pair-1 STTM ran into the client's 180 s read timeout, and after it
EVERY endpoint timed out until the App was restarted. v0.5.5 removes each way a
request could wait on I/O or a runaway parse:

- **Choosing the STTM is a background job.** `POST /api/demo/workbook` answers
  **202 with the job** at once. The job runs locate → download → start parser →
  classify → pair FRD → pair VDD → record, each step bounded by
  `inputs.select_timeout_seconds` (120; the parser start by
  `inputs.parser_start_timeout_seconds`, 60). `GET /api/demo/status` carries it
  as `selection_job` — state `running | done | failed`, every step with its
  state (`timed_out` for a late one), `error {code: not_found | timeout | failed
  | superseded, message}` and the pairing outcome. The chooser shows the steps
  as they happen and, on failure, "Not selected — …". Nothing is selected until
  every step has succeeded; a Clear supersedes a running job; Generate waits
  while one runs. The lock guards state mutation only — no I/O under it.
- **Documents are opened in a child process** (`codegen.layout.docworker`), one
  for the background index and one for selections. A file that is not read
  within its budget gets the process **killed** (a thread can only be
  abandoned; an abandoned parse of a sheet that declares a million rows kept
  the App's process busy). The child is restarted on the next request. Pairing
  never opens a document in the App's own process: a candidate that is
  unreadable or not read in time scores on its NAME (listed as "not read" in the
  pairing outcome).
- **Upstream FRD contracts are OFF** (`upstream.enabled: false`, new). The FRD
  list, a selection and a failed run's hint never touch the SQL Warehouse. The
  App's service principal has no warehouse permission inside ACFC anyway — it
  was the `upstream_error` on the FRD list. When enabled, the listing refreshes
  in the background with a hard timeout (`upstream.timeout_seconds`, 20) and the
  FRD list shows "loading" meanwhile; an upstream FRD choice is a job too (202).
- **Remote folder listings are bounded** (`inputs.listing_timeout_seconds`, 30):
  a root that does not answer is reported under `input_errors` and its last
  known listing served.
- **One record of what is selected.** `status.selection = {sttm, frd, vdd}`; the
  workbook list's `selected` (and the new `selected_as`) and the status' STTM /
  FRD / VDD fields are all derived from it — on site the list said "selected"
  while the chooser said otherwise.

No new permission. After the redeploy (marker 0.5.5): open the chooser, choose
pair 1's STTM — the steps appear under the list; if a step times out it says
which, and the App keeps answering.

## What v0.5.4-acfc adds (the document chooser on the workspace backend)

- **The lists return at once.** `GET /api/demo/workbooks` (and the FRD list)
  return listing METADATA only — name, folder, size, modified — and never
  download or open a document. What needs a document's content is computed once
  per file version by ONE background task (`ui/backend/docindex.py`) and kept in
  the state role as `document_index.json`: a workbook's **kind by content**
  (`sttm` — a band row with stage + standard labels / `MAPPING-` sheets; `vdd` —
  a FILES / field-sheet header; else `unclassified`) and every document's
  pairing facts. Until a verdict exists the row shows **classifying…**. A file
  that cannot be downloaded or opened, or exceeds
  `inputs.classify_timeout_seconds` (60), shows **unreadable** with the reason —
  still listed, never retried on its own (only when its size / modified changes,
  or with **Retry**). Dictionaries are listed under the VDD heading, everything
  else under STTM; an unclassified workbook is badged, never hidden. The App's
  service principal therefore needs **Can Manage** on the state folder (§3) — it
  already did, for `decisions.json` and the layout cache.
- **A selection succeeds or says why.** Choosing an STTM downloads it (bounded
  by `inputs.select_timeout_seconds`, 120), pairs it and records the choice in
  the state role (`selection.json` — restored after a container restart). If any
  step fails the response is **HTTP 424 with the reason**, the chooser shows
  "Not selected — …", the STTM stays unselected and **Generate is refused** —
  never a silent fall back to the config default. The VDD route now finds a
  dictionary in ANY input root (it used to look in the local directories only:
  a VDD in a workspace pair folder answered 404).
- **Pairing on select, same folder first.** With `…/frd_sttm_pairs/pair_N/`
  folders the FRD / VDD candidates of the STTM's OWN folder are scored first;
  the other input roots only when that folder holds none. A pair folder holding
  exactly one candidate that no content signal decides (the real pair-1 STTM
  states `TBD` for its files, so nothing points at its dictionary) pairs by rule
  `same_folder`; two or more undecided candidates are a question among THEM. The
  outcome comes back in the select response — `pairing.frd` / `pairing.vdd` =
  `{chosen, rule, reason, scope, folder, candidates, question}` — and stays on the
  status.

## What v0.5.3-acfc adds (the fixed-width width chain)

Record: `docs/acfc/M9_FINDINGS.md` §6. The real pair-1 sheet writes `10,2` in
the Length cell of six Detail amount fields — a precision, not a byte width —
and v0.5.2 stopped on it before the gate. A Length cell is a width only when it
is an INTEGER; otherwise the width comes from the chain, each link flagged with
its cells:

1. STTM `End` − `Start` + 1, when both are integers — `width_from_sttm_span`;
2. the VDD's `End Position` − `Start Position` + 1 for the same field (matched
   by normalized field name + segment; its `Length` when it states no end) —
   `width_from_vdd`. **Pass the VDD** (`layout --vdd`, `generate --vdd`; the
   notebook does);
3. the question **`feeds[0].fields[<field name>].width`** — a text box in the
   dialog, or in the answers file (the CLI prints the full keys; the
   `unresolved_headers.md` report withholds the field name):

   ```yaml
   gaps:
     "feeds[0].fields[Amount (01)].width": {value: 13}
   ```

   `codegen extract-sttm --answers answers.yaml` carries the answers —
   `width_from_user`.

The `10,2` is kept as the field's precision (`Decimal(10,2)`,
`length_is_precision:<field>`); **a width is never derived from a precision**.
The fixed-width reader, the `ADLS_FIXED_WIDTH_HANDLER` `LEN` cell and the VDD
cross-check all use the resolved width. A field no link resolves stops
`generate` with a message naming its question.

## What v0.5.2-acfc adds (the first real v0.5.1 run)

Record: `docs/acfc/M9_FINDINGS.md` §5.

- **File patterns are a chain, not a hard stop in `extract-sttm`:** FRD (incl.
  its Object Name block) → STTM meta rows `File Names` / `File Name Example` /
  the File Details sheet → the VDD `FILES` sheet's `File Name Pattern` column →
  the question **`feeds[0].file_patterns`** (layout dialog: a text box; answers
  file: `gaps: {"feeds[0].file_patterns": {value: "a_*.txt; b_*.txt"}}`). Each
  fill is flagged `file_pattern_from_<object_name|sttm|vdd|user>` with its
  cell. Only `generate` stops, when the chain ends unanswered — pass the VDD to
  `layout` (the notebook does) or to `generate --vdd`.
- **Object Name as a block:** the real cell is stanzas — a `<line of
  business>:` line, the file name pattern on the next line. Blocks (several
  lines, or a nested label | value table) are read per line / row: feed name
  from an `Object Name` / `Feed Name` / `Name` label, files from a `File
  Name`-type label or any file-like value under another label
  (`extractor.frd.object_name_labels`).
- **`layout --refresh` reports who really placed each role.** Its second pass
  (the answers file) used to re-read the entry the first pass had just written
  and print `source=cache cache_hit=True`; it now continues from the first pass
  — also no second model call.
- **Exit code = gate verdict** (`PASS` / `PASS_WITH_FLAGS` → 0, `FAIL` → 1;
  the console headline is the report's verdict). A failed check prints its
  first lines (`CHECK FAILED ruff — …`). A check that could not RUN — `ruff`
  missing or unusable in the environment — is `ruff=not-run` plus the flag
  `check_not_run:ruff` (PASS cannot be claimed), never a FAIL: only findings
  fail a feed. Layer-2 sketches are never linted (they live in
  `candidates/candidates.json`).

## What v0.5.1-acfc adds (M9 — the 2026-09-21 pair-1 findings)

Full record: `docs/acfc/M9_FINDINGS.md`. In one list: the "… in DL" header
family, `Format` and the `Details` segment spelling are synonyms; the schema
is a required role (always asked); answers may set any role; the runtime
profile cache is keyed by the synonym tables, never trusts or stores a profile
without a required role, and has `--refresh`; model-answer rejections are
logged in full; band constants (schema / table / catalog) are read with their
cell as provenance and an unstated schema falls back FRD → config
(`conventions.default_schema`) before the hard stop; `Do Not Map` rows are left
out and flagged `field_unmapped:<field>`; `TBD` meta values are blanks; an FRD
target cell written as an inline layer block (`Staging Layer:` / `Table: …`)
is parsed per layer; an Object Name cell that lists `<label>: <file>` lines
gives the file patterns and the feed is named after the STTM stage band
(`frd_feed_name_unstated`); the contract matcher compares normalized table
names; `codegen generate` honours `--vdd` / `--profile` / `--iig-template` /
`--playbook-template`.

## What v0.5.0-acfc adds (M7.1 + M8)

- **Global correctness gates (M7.1):** SQL-literal, path-literal and derived-
  name cap checks are gate CHECKS for every profile (FAIL); sibling-type
  consistency is a global FLAG. `conventions.default_catalog` is a top-level
  key (provenance `config_default`); the iig_v1 synthetic `TGT_ADLS_PATH`
  slugifies its domain segments (`metadata.synthetic_path_slug`). Only
  conventions stay profile knobs (`emit_dml`, `require_qualified_names`).
- **Storage backends (M8.1):** `codegen.storage` — `local` / `workspace` /
  `volume` behind one interface; roles `storage.inputs|state|outputs`.
- **Input discovery + content pairing (M8.2):** `inputs.extra_dirs`,
  `codegen.pairing`, `codegen pair`.
- **Layout in a real workspace (M8.3):** `layout.provider: live`, the answers
  file, `--report-unresolved`, the profile cache in the state role, Python
  3.10 – 3.12.
- Earlier (v0.4.2, M7): `docs/acfc/METADATA_DB_SEMANTICS.md`, the one-block /
  many-files F1 reader, the derivation gate, the SQL Server DML deliverable
  (`config_inserts_<env>.sql` + the runner notebook; create the `dml:` secret
  scope before the first run).

## Open questions to raise with the document authors

- **MIDS FRD, Structural Metadata → ADLS Location, row "Individual Risk"**:
  the path ends in a period (`…\care_management\sdoh\socially_determined.`).
  The path gate FAILs a segment that ends in punctuation, so the
  individual-risk feed cannot ship until the FRD is corrected (an FRD typo
  to raise with the author) — the agent does not silently strip it.
- **MIDS FRD, Target Schema**: names no catalog; set
  `conventions.default_catalog` (above) or have the FRD state it.
