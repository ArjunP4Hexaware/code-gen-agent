# Deploying CodeGen inside ACFC (v0.4.1-acfc)

How to stand the agent up in ACFC's own Databricks workspace from a Git
folder clone of `staging`, run the ten documented pairs, and check the
pair-1 output against the golden. Every value below that is ACFC's (catalog,
schema, endpoint, volume names) is a placeholder the deploying engineer
confirms; nothing here invents one. Items marked **(confirm)** were written
without access to the ACFC workspace.

## 1. Clone `staging` as a Git folder

Workspace → **Repos** (Git folders) → **Add Git folder** → this repository's
URL, branch `staging`. The tree is self-contained for a deploy: the built
frontend bundle (`ui/frontend/dist/`), the synthetic fixture universe
(`fixtures/acfc_shapes/`, `fixtures/layout_profiles/`), the scrubbed SFMC
reference artefacts (`fixtures/reference/`) and the CV golden pair are all
tracked. **Not** on `staging` (by the no-client-documents rule): the MIDS /
CAQH client documents and the SFMC client-derived contract pair. They are on
`main` if ACFC wants them; nothing in this document needs them.

## 2. Config edits before the first run

All knobs live in `config/config.yaml`; the loader refuses unknown keys, so a
typo fails at start-up. Edit these:

| Section | Key | Set to | Why |
| --- | --- | --- | --- |
| `databricks` | `catalog` / `schema` | `d1_dlk` / `codegen` **(confirm the catalog and schema exist)** | where the raw FRD/STTM volumes live; `codegen.databricks` refuses writes outside this prefix |
| `databricks` | `frd_volume` / `sttm_volume` | ACFC's volume names for raw FRD `.docx` and STTM `.xlsx` **(confirm)** | the UI's Fetch buttons list these volumes |
| `databricks` | `landing_volume` / `output_volume` | the writable landing volume and the artefact publish target **(confirm)** | `codegen databricks-publish` / the UI publish panel write only here |
| `databricks` | `serving_endpoint` | the workspace serving endpoint that fronts a Claude model **(confirm the name)** | Layer 2 (reasoning) and the layout recognizer both call it through FMAPI; `reasoning.model` names the same model |
| `databricks` | `warehouse_id` / `wrapper_notebook_path` | ACFC's values, or leave empty | `EXPLAIN` is the only SQL the seam sends; empty = feature off |
| `demo` | `databricks_paths` | `{catalog: d1_dlk, schema: codegen, volume: <landing volume>}` | the synthetic `databricks fs ls` block on the Generate card |
| `conventions` | `profile` | `acfc_prx` | one combined `<ABBREV>_DDL.txt`, typed stage columns, the pair-1 shape |
| `metadata` | `template` | `iig_v2` | the eight-sheet IIG layout of the PRX packages |
| `playbook` | `template` | `main_single` | the single-sheet `Main` playbook of the PRX packages |
| `output` | `mode` | `rfc` (or leave `notebook` and pick per run in the UI) | framework artefacts + the assembled `RFC<number>_<Feed>/` package |
| `layout` | `provider` | `auto` (live via the serving endpoint) or `mock` | `mock` never calls a model: a workbook no synonym resolves pauses for a human instead |

Optional overlay: `CODEGEN_CONFIG_OVERLAYS=<path.yaml>` (or `load_config(...,
overlays=[...])`) deep-merges a YAML mapping onto the config before
validation. ACFC's own pipeline / notebook inventory for the IIG
(`metadata.templates.iig_v2.template_rows`) belongs in such an overlay,
never in the tracked config; `fixtures/acfc_shapes/pair_1/config_overlay.yaml`
is the shape.

Per-feed answers the documents do not state go in
`fixtures/faq/<feed_slug>.faq.yaml` (each with its citation): `process_name`,
`feed_abbreviation`, `rfc_number`, the record-type discriminators. Unanswered
means blank-and-flag, never a guess.

### First deploy: mock the model

Set `CODEGEN_FORCE_MOCK_PROVIDER=1` in `app.yaml`'s `env` for the first
deploy. Every run then uses the mock Layer-2 provider and the mock layout
provider (answers from `fixtures/layout_profiles/`), so the App can be
exercised end to end with zero model calls and no serving-endpoint
permission. Remove the variable and redeploy once the endpoint permission
(`CAN_QUERY` for the App's service principal) is confirmed.

### Notification DL

The tracked config carries a synthetic prod-support address. The real DL is
a client value: set `CODEGEN_NOTIFICATION_EMAILS=<dl>` in `app.yaml`'s `env`
(or `.env` locally); never commit it.

## 3. Running the ten pairs

The documented shapes (`docs/acfc/SHAPES_FOR_PORT.md`: STTM families A–E,
FRD families F1/F2, VDD patterns V1–V3) are exercised by the synthetic pairs
under `fixtures/acfc_shapes/`. FRD documents exist for pairs 1, 2 and 8; VDDs
for pairs 1, 2 and 9; every pair has an STTM.

### Through the UI (the intended path)

1. Generate page → **Choose documents…**. In the modal: pick the STTM `.xlsx`
   (fixture, fetched from a volume, or uploaded from the device); pick the FRD
   (an upstream contract row, a local `.contract.json`, or the FRD **`.docx`**
   itself, extracted deterministically when the run starts); optionally pick
   the **VDD** `.xlsx` in its own section (cross-checked against the STTM,
   never a source of values). Each input has a Clear button on the card.
2. Output: pick `RFC package` (or the mode you want) and confirm the three
   selectors show `acfc_prx` / `iig_v2` / `main_single` (or the config
   defaults you set). The card's badge and the "Model transport" line name
   the Layer-2 transport the run will use — inside a Databricks runtime that
   is always the Foundation Model serving endpoint.
3. **Generate from this STTM…** → confirm the cost dialog.

### Through the CLI (batch, or CI)

```bash
codegen extract-frd  --docx fixtures/acfc_shapes/frd/f1_pair_1.docx --out out/pair1/frd.contract.json
codegen extract-sttm --workbook fixtures/acfc_shapes/sttm/pair_1_family_a.xlsx \
                     --frd-contract out/pair1/frd.contract.json --out out/pair1/sttm.contract.json \
                     --generated-date 2026-01-01
codegen extract-vdd  --vdd fixtures/acfc_shapes/vdd/pair_1_v1_segments.xlsx --out out/pair1/vdd.contract.json
codegen generate --frd-contract out/pair1/frd.contract.json --sttm-contract out/pair1/sttm.contract.json \
                 --vdd out/pair1/vdd.contract.json --output-mode rfc \
                 --profile acfc_prx --iig-template iig_v2 --playbook-template main_single --dry-run --skip-tests
```

`--dry-run` forces the mock providers (no model calls). Drop it for live
Layer 2. `codegen layout --workbook X --frd Y --vdd Z --dry-run --json`
shows what the recognizer resolved before any extraction. `contracts.pairs`
in the config lists (FRD contract, STTM contract) pairs for `codegen
generate-all`; it ships empty.

## 4. Where outputs land

- UI runs: `out/demo_<timestamp>/<feed_slug>/` plus `run_meta.json`,
  `frd.contract.json`, `extracted_sttm.contract.json` and, with a VDD,
  `vdd.contract.json`. Reports under `out/demo_<timestamp>/reports/`.
- CLI runs: `out/<feed_slug>/` and `reports/<feed_slug>.md`.
- Per feed: `ddl/` (the generator's own `.sql`), `framework/` (the profile's
  deployment DDL `.txt`, `config_rows.xlsx` = the approval artefact with its
  `_provenance` sheet, `config_inserts.xlsx`, `ADDITION.md`), and in `rfc`
  mode `RFC<number>_<FEED>/` with the DDL, `<FEED>_IIG.xlsx`, the playbook,
  `FILE_LOG_INFORMATION.txt` when enabled, and `MANIFEST.md` listing every
  file, its source and the flags that apply. `candidates/candidates.json`
  holds the Layer-2 review items.
- The App container's disk is wiped on every restart; publish what you want
  to keep to the output volume (`codegen databricks-publish` or the UI's
  publish panel, both confirm-gated).

## 5. Databricks Apps deploy

Click path: **Compute → Apps → Create app → Custom** → name (`codegen-agent`)
→ **Source code path**: the Git folder from §1 **(confirm that a Git folder
path is accepted as the source; the Hexaware deploys used a synced workspace
path)** → **Resources**: add the serving endpoint as `llm-endpoint` with
`CAN_QUERY` → Create. Later deploys: open the app → **Deploy** with the same
path. The CLI equivalent:

```bash
databricks apps deploy codegen-agent --source-code-path /Workspace/<path-to-the-git-folder>
```

`requirements.txt` is the runtime's pip install (`.[ui,databricks]`,
includes ruff). The runtime caches the environment keyed on that file:
bump the `codegen-version-marker` comment (and the pyproject version)
whenever `src/` changes, or the App serves stale code. The App's service
principal needs `READ VOLUME` on the raw volumes and `WRITE VOLUME` on the
landing / output volumes **(confirm the grant names in ACFC's UC setup)**.
`app.yaml` already sets the command; the platform injects the port and the
`DATABRICKS_HOST` credentials, which `codegen.databricks` prefers over any
CLI profile.

## 6. The layout dialog, first time a new workbook is seen

The recognizer reads a workbook through a layout profile: cache → synonyms →
model → validator → human. On a workbook whose fingerprint (its header
region only, never a data row) is not cached and whose roles the synonyms
cannot all place, the run **pauses** in state `needs_layout`. The Generate
card shows one question per unresolved role, grouped by document (STTM /
FRD / VDD), each a radio over the candidate columns (STTM/VDD) or candidate
table cells (FRD), with the header row printed for orientation. Choose,
then **Continue**; **Proceed with unresolved** reads the remaining roles as
empty and gate-flags them; **Cancel run** stops. The completed profile is
cached under `ui/backend/state/layout_profiles/` (also wiped on restart), so
the same workbook never asks twice. With `layout.provider: mock` or the
mock lock, the model step is skipped and the dialog is the only fallback.
Expect questions on families A, C and E: their band rows do not name every
role, and the synonym tables are deliberately not widened to force them.

## 7. What to compare against the pair-1 golden

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
