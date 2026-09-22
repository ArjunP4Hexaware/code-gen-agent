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

## What v0.7.4-acfc adds (housekeeping)

- **ruff is pinned to one minor range, `>=0.16,<0.17`**, in both extras that
  install it (`[dev]`, `[ui]`); the App's `requirements.txt` installs
  `.[ui,databricks]` and so carries the pin. v0.7.3 pinned the rule SET the
  gate selects; this pins what those rules mean — a new ruff release can no
  longer add rules inside E / F / I / UP / B / SIM and flip the gate on
  unchanged code. Moving it is a deliberate change with a full suite and
  baseline run. (The generator emits no requirements file of its own.)
- **`scripts/scrub_check.py` is 0 over every tracked file.** The synthetic
  storage-URI examples in `gate/derivations.py` and
  `tests/test_m101_real_run_bugs.py` now use hosts under `example.invalid`
  (RFC 2606 — never a real ADLS / blob host) instead of `*.dfs.core.windows.net`
  / `*.blob.core.windows.net`, which the `real_adls_host` pattern flagged.

Version marker 0.7.4. CV / SFMC baselines byte-identical (193 files).

## What v0.7.3-acfc adds (M12 — four causes read out of the v0.7.2 all-pairs run)

- **Item 1 — a layout model's answer is judged on its PLACEMENT only.** In
  the v0.7.2 run every model answer (pairs 5, 7, 8, 9, 10) was thrown away by
  a `literal_error` on `source` and on every `role_sources` key: the answer
  was validated against `LayoutProfile`, whose provenance fields are a
  four-word Literal, and the prompt had shown the model a partial profile
  carrying them. The wire schema is now its own model
  (`codegen/layout/response.py`): sheets / bands / roles / meta rows, NO
  source, role_sources, confidence, fingerprint or strategy; extra keys are
  dropped, never a rejection; the resolver stamps `source="model"` and the
  per-role sources itself. The prompt's `partial_profile` and its new
  `response_schema` are generated from that model. Same fix on the FRD side
  (`field_sources`, `family` — the family is what discovery found). A
  placement that does not parse is still rejected, and every surviving claim
  still goes through the validator. Expect the next run's layout stage to
  reach the validator on those five pairs — whether their placements pass it
  is the next thing the run will show.
- **Item 2 — the gate's ruff no longer depends on where the tree lives.** It
  runs `--isolated` with the rule set pinned in `codegen/lint_rules.py` (the
  same definition the emitted `ruff.toml` renders from, byte-identical), and
  ignores EXE002 — a file mode is the storage's business, never a finding.
  Before, ruff DISCOVERED its config: the emitted `ruff.toml` / the
  checkout's `pyproject.toml` here, the config of the process's working
  directory when nothing sat above the tree, ruff's own defaults otherwise.
  The runner notebook's unused `noqa: SLF001` (RUF100 under the defaults) is
  gone. Note: in framework mode the gate lints the scratch pipeline tree, not
  the runner notebooks; the RUF100 / EXE002 lines in the run record came
  from a manual ruff over `framework/`. The gate's own findings list for
  that run was not captured — the gate details carry every finding (M9.1b),
  so the next run shows what, if anything, remains. (v0.7.4 pins ruff
  itself to `>=0.16,<0.17`.)
- **Item 3 — a parser that cannot start no longer holds a selection.**
  Whether the document parser child can start is asked ONCE per process at
  App start, in the background, within `inputs.parser_probe_seconds` (10 s).
  When it cannot (serverless compute; the App runtime of the v0.7.2 run),
  documents are parsed in-process: `docworker.read_document` in a worker
  thread with the same per-file timeout, the used-range loader and the cell
  cap; one read per lane at a time, a late read abandoned (`timed_out`) and
  holding its lane until it ends. A child that started once and then fails to
  start demotes the process to in-process. The status says so once:
  `parser_mode` = `{mode: probing | subprocess | inprocess, reason}`; the
  `start parser` step reads `in-process (parser_mode=inprocess)`. A workbook
  whose dimension claims a million rows classifies in-process in well under
  2 s.
- **Item 4 — a VDD tie is a question.** Pair 5 had three dictionaries at 1.0
  each, below `min_score`, and was left with no VDD and no question. A tie at
  a positive score is now a `pair.vdd` choice question (the margin rule can
  never separate equal candidates). One weak candidate alone is still not a
  question — a VDD is optional.

Version marker 0.7.3. CV / SFMC baselines byte-identical (193 files); the
pair-1 acceptance goldens unchanged. No frontend change (dist untouched).

## What v0.7.2-acfc adds (M11 addendum items 10, 8, 12, 13, 9 — from SHAPES_ROUND2)

- **Item 10 — layer-prefixed headers (pair 7).** A mapping sheet with NO band
  row whose headers carry the layer in their text ("Stage Table - Column
  Name", "Standard Data Type", "Stage Schema") now resolves: when the full
  header matches no role, the layer token is stripped, then a leading
  "Table", and the remainder resolves through the base role synonyms; a
  trailing-group header with a qualifier ("Recycle Flag ( Enabled for 7
  Days)") resolves by its synonym prefix. Only on a miss — every header that
  resolved before is untouched. Pair 7 resolves with ZERO questions and no
  model call (its tracked layout profile regenerated: key ORDER only — the
  synonyms land exactly on the columns the curated truth placed by hand).
- **Item 8 — F2 detection (pair 8).** "Solution Requirement" is found in ANY
  row-0 cell (the real tables merge it across B–D after a leading column),
  sub-IDs and trailing titles allowed; the row-4 LABEL cell names the
  section wherever the leading column pushes it. Both plausible Word
  structures of that leading column read exactly like the round-1 fixture.
- **Item 12 — a blank band label (pair 5).** A band row that names one target
  layer and leaves the other merged group's label BLANK takes that group's
  layer from the headers beneath it (a layer prefix, or two target-role
  headers after a stage group = standard) — both for detection and for the
  bands. A meta **NOTE** row is recorded but never a value source (its
  `"|"` is prose, not a delimiter).
- **Item 13 — pair 6.** A column whose VALUES are In Scope / Out of scope
  (`extractor.scope_in_values` / `scope_out_values`) filters the rows — one
  grouped flag `rows_out_of_scope:`. A Load Rules cell reading "Audit Column…"
  (`extractor.audit_load_rule_markers`) marks an audit row even when it names
  its column in ONE layer only (flag `audit_column_one_layer:`); headed
  columns BETWEEN two band groups (Load Rules, between source and stage) are
  the data-rules group. A type cell carrying a format —
  `timestamp(YYYY-MM-DD HH:MM:SS)` — is the type plus the format (flag
  `type_format:`; a precision like `decimal(10,2)` stays). A source band
  with server / catalog / schema / table roles marks the feed
  `source_kind=rdbms` (flag `source_kind_rdbms:`): the DDL is generated; the
  DML writes a REVIEW block for the file-source tables (`dml.file_source_
  tables`) and skips the file-connection lookup — the RDBMS connection /
  ingestion tables (§4, §6) are not described. And an audit column no rule
  populates (`DELETE_FLAG`, `REGION_NAME`) is no longer a hard stop: the
  generated pipeline writes it as a typed NULL, flagged
  `audit_column_unpopulated:`.
- **Item 9 — F3 (pairs 9 and 10).** Topic-organized requirement documents
  are recognized and classified (requirement / NFR / boilerplate / domain
  tables, `extractor.frd.table_classes`), flagged `frd_family_f3:`; a 2-column
  Domain / SubDomain table is read; everything else comes from the chain or
  a typed question; a live layout model may map fields through the
  validator (the mock declines, recorded as a rejection).

Version marker 0.7.2. CV / SFMC baselines byte-identical (193 files); the
pair-1 acceptance goldens unchanged.

## What v0.7.1-acfc adds (M11 addendum items 7 and 11 — from SHAPES_ROUND2)

The round-2 shape capture (`docs/acfc/SHAPES_ROUND2.md` on `origin/acfc-runs`,
tokenised) changed two conclusions of v0.7.0:

**Item 11 — the real used range (pair 3).** Pair 3 is NOT a 140k-cell
workbook: its STTM sheet holds about 336 rows but carries formatting down to
row 1,048,538, so openpyxl reports `max_row = 1,048,538`, and every
`iter_rows` scan in normal mode CREATES a cell per row — 34 columns x a
million rows. That, not the data, ran the parser past its budget. Every
document workbook is now opened through `codegen.layout.extent.load_document`,
which trims each sheet to its USED range (the last valued row before
`extractor.used_range_empty_rows` = 500 consecutive empty rows); openpyxl
derives `max_row` from the cells it holds, so all ~20 scans are bounded with
no change at the call sites. Measured on the pair-1 fixture with one formatted
cell at row 1,000,000: **151 s without the used range, 0.1 s with it**, and the
extracted contract is byte-identical to the clean fixture's. Rows WITH values
beyond such a gap are counted and reported, never dropped silently. A sheet
with only a few formatted empty rows keeps its exact `max_row` (it is layout
fingerprint input — no cached profile moves).

The v0.7.0 cell cap is now the BACKSTOP and measures the used range too:
v0.7.0 would have refused pair 3 on its declaration ("35,650,292 cells");
v0.7.1 streams the sheet read-only, counts the ~11k cells it holds, and reads
it. A workbook that really is over `inputs.max_workbook_cells` is still
`unreadable: <n> used cells, > cap <c>`.

**Item 7 — the FRD family never blocks (pairs 8/9/10).** A document with no
F1 metadata table and no Solution Requirement table no longer stops the run
(`FrdDocxError: no metadata section table (F1) and no Solution Requirement
table (F2) found`). It yields an empty-but-valid contract flagged
`frd_family_unrecognized` (with the table count and the first row-0
headings); the fallback chain fills what it can — the STTM bands name the
feed, its tables and schemas; the VDD states the format and file patterns;
config defaults follow — and what is left becomes a question. Because such
a document has no cell to point at, its questions are TYPED-value questions
(`feeds[i].source_system`, `.lobs`, `.domain`, … answered under `gaps:`; LOBs
split on `;`), and a question the chain already answered is not asked.
`codegen extract-frd` exits 0 on such a document. (Recognising the real
pair-8 F2 geometry and the pairs 9/10 "F3" shape is v0.7.2.)

Version marker 0.7.1. CV / SFMC baselines byte-identical (193 files).

## What v0.7.0-acfc adds (M11 — the six causes of the all-pairs run)

The first all-pairs run of v0.6.2 (2026-09-22) passed 1 of 10. Six of the
nine failures were the agent refusing to read a document it could have read,
or hiding what it skipped. Each is now a flag or a named check, never a
crash. (The three FRD documents that match neither the F1 nor the F2 family
are NOT in this release — they wait for the round-2 shape capture.)

| Was | Now |
| --- | --- |
| `WorkbookParseError: FILE_DETAILS row 6: Vendor and FileName must both be present` — a LEGEND row ("… DataType = … Confirm before use.") | A FILE_DETAILS row whose vendor cell is an annotation (`extractor.file_details_annotation.phrases`, or an italic cell) or that names no file is SKIPPED and logged — flag `file_details_row_skipped:<sheet> row N: <reason>`. A sheet of nothing but annotations still fails loudly. |
| `ExtractionError: segment spelling(s) ['NA'] are outside the Header/Detail/Trailer vocabulary` | `extractor.discovery.segment_synonyms` gained a **`none`** class (`NA`, `N/A`, `-`, `none`, …): a Segment column holding only these means ONE record type, and the sheet extracts unsegmented — flag `segments_none:<sheet>`. A spelling that is neither a segment nor a `none` value is still loud, and now names the `none` class in its message. The `none` spellings are never a banner row and never a segment sheet name. |
| `ExtractionError: audit column 'DELETE_FLAG' has datatype 'tinyint'; expected one of ['string','timestamp']` | The declared type is carried VERBATIM and flagged `audit_type_nonstandard:<column>`. Whether it is acceptable is a deployment question, decided per profile: `conventions.profiles.<p>.audit_types_restricted` (true for `edo_sfmc`, **false for `acfc_prx`**). Restricted, it is the gate check **`audit_types` = FAIL** naming the column — never a refusal to read the STTM. The Delta scalar types (`tinyint`, `smallint`, `binary`, …) now map in the DDL; an unknown type is still a loud `TemplateGapError`. |
| `ContractMismatchError: format '.xlsx' has no implied delimiter` | **An .xlsx / .xls source is a first-class format** (`extractor.spreadsheet_tokens`): no delimiter (`""`), no byte positions, a SHEET instead. The generated reader reads the sheet with pandas + openpyxl (no cluster library); `feed_spec.py` carries `SPREADSHEET = True` and `SHEET_NAME`; the fixture writer and the generated tests write a WORKBOOK. The sheet name comes from the FRD, then the STTM meta row (`Sheet Name` / `Tab Name` / `Worksheet`), else it is a layout question (`feeds[i].sheet_name`); unanswered, the reader takes the FIRST sheet and the gate says so (`sheet_name_unstated`). **The trap this closes:** `delimiter == ""` used to MEAN fixed width in the emitter and the IIG, so an xlsx feed would have rendered as positional — `codegen.formats` now keeps the three kinds apart, and `ADLS_FIXED_WIDTH_HANDLER` stays empty for a spreadsheet. A spreadsheet that also declares record segments is flagged `spreadsheet_segmented:`. |
| `StepTimeout: the document was not read within 120s — the parser process was killed` (a 140k-cell workbook) | The cheap question is asked FIRST, read-only, from each sheet's declared dimension (or, for a writer that declares none, estimated from the sheet XML's size in the zip — the message then says "about"): over `inputs.max_workbook_cells` (**250,000**) the document is `unreadable: <n> cells, > cap <c> (largest sheets: …)`. A verdict with a reason, in the chooser and in the CLI, instead of a killed child. 0 = no cap. |
| "Layout: 6 questions (proceeded unresolved)" — then an extraction error naming roles nobody had seen | A **Proceed with unresolved** no longer erases the questions. They stay on the status (`layout_skipped`, shown in the UI after the dialog closes), are staged in the run log, become gate flags `layout_question_skipped:<key>`, and get their own report section, **Layout questions left unanswered**. The CLI / notebook path was already correct (`--require-complete` refuses). |

Version marker 0.7.0. CV / SFMC baselines byte-identical (193 files); the
pair-1 acceptance goldens are unchanged.

**Still open:** pairs 8, 9 and 10 fail with `FrdDocxError: no metadata section
table (F1) and no Solution Requirement table (F2) found`. That needs the
round-2 shape capture (`SHAPES_ROUND2.md`) before the detector is extended —
guessing at a third family from an error message is exactly what this repo
does not do. It lands as v0.7.1.

## What v0.6.2-acfc adds (M10.2 — location URIs)

A landing value with a storage scheme — `abfss://`, `abfs://`, `wasbs://`,
`wasb://`, `dbfs:/`, `s3://`, `s3a://`, `adl://`, `gs://` — is a **location
URI**, not a folder path. v0.6.1 pushed it through the folder rules
(`/abfss:/…`, "segment 'abfss:' ends in punctuation"). Now:

- **Validated as a URI** (`gate/derivations.py::uri_violations`): scheme,
  an authority (except `dbfs:/`), no whitespace or line break, the length
  cap, and every path segment by the existing folder rules. The derivations
  check names the rule in each finding ("(location URI rule)") and, when it
  passes, how many cells the URI rule covered. `https://` is not a storage
  location and still fails the folder rules.
- **Carried through as written.** The IIG's from-FRD cell holds the URI
  verbatim, badged **`location_uri`** (light blue like from-FRD; the
  provenance sheet says "from FRD (location URI)"); a template path shape
  appends its segments INSIDE the URI's path (`{landing}Archive/` →
  `abfss://…/dom/sub/Archive/`). A shape that PREFIXES the landing
  (`/Archive{landing}`) cannot prefix a URI: its segments follow the URI and
  the cell is flagged `iig_path_shape_on_uri:<TAB>.<HEADER>`. The FRD
  contract records `value_kind: location_uri` on the field's evidence (absent
  for a folder path — existing contracts unchanged). The iig_v1 layout's
  container / path cells read the URI's authority (the container before `@`)
  and its path.
- The label strip of v0.6.1 composes with it: `/Path : abfss://…` → the URI.

Fixture variants: `frd.build_f1_pair1(landing="/Path : abfss://…")` and the
folder-path one; both pass the derivations check; a URI whose segment ends in
punctuation still FAILs under the URI rule. Version marker 0.6.2; CV / SFMC
baselines byte-identical (193 files).

## What v0.6.1-acfc adds (M10.1 — the two v0.6.0 real-run bugs)

From the first ACFC run of v0.6.0 (pair 1, 2026-09-22):

1. **`KeyError` on a trailer stage column in the natural key.** The sheet
   names its record-type field the same in every segment; the resolver's
   source-name → stage-column map let the LAST segment win, so the detail
   MERGE was keyed on the trailer's stage column, and the emitter (which
   resolved the key against the Detail segment only) crashed. Now: a shared
   source name maps to the **Detail** segment's stage column
   (`resolve/resolver.py::_stage_columns`); `build_context` resolves the key
   against **every** segment (`natural_key_segments` in the context); a key
   column that exists in no segment is the gate check
   **`natural_key_columns` = FAIL** naming it and the segments searched —
   never a crash. The check is added only when it fails, so no baseline
   report moves. Variant fixture: `sttm.build_pair1(trailer_key=True)`;
   `tests/test_m101_real_run_bugs.py` drives it through the CLI and through
   the App runner (`DemoRunner._execute`, chooser and all).
2. **`/Path : <storage>/<landing>/…` in the FRD's ADLS Location cell.** The
   derivations check FAILed every path that embedded the label. The FRD
   reader now strips a leading label token (`extractor.frd.value_label_
   prefixes`: Path, ADLS Path, Location, ADLS Location, Landing Path; a
   leading slash before the label, spaces around the colon, any case) and
   records it as `stripped_label` in the field's evidence; the remainder
   goes through the existing path validation unchanged — so a URI where a
   folder path is expected still FAILs, as it should. Variant fixture:
   `frd.build_f1_pair1(landing="/Path : …")`.
3. **`ruff=NOT RUN` in the notebook fallback.** `acfc_run.py`'s install
   cell is now `.[ui,databricks]` — `[ui]` carries ruff. `check_not_run`
   stays the fallback.

Version marker 0.6.1. CV / SFMC baselines byte-identical (193 files).

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
