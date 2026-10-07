# Backup branch `backup/ddl-only` (2026-10-07, for the 2:30 PM demo)

## What it is

A fallback for the IIG-first demo in case `feature/iig-first` misbehaves inside
ACFC. It is `origin/fix/remove-mock-provider-ui-text` at **e89a263** (M15e,
2026-09-23 — the last state verified in ACFC before the IIG-first work), plus
exactly three changes:

1. `pyproject.toml` version and the `requirements.txt`
   `codegen-version-marker` → **`0.5.8.post5+ddl1`**. `0.5.8.post5-ddl1` is not
   valid PEP 440; `+ddl1` is a local version label, and pip builds it
   (`Would install codegen-data-engineer-agent-0.5.8.post5+ddl1`). A changed
   marker makes the Apps runtime rebuild its venv, so no stale wheel serves
   old code.
2. `config/overlays/acfc_env.yaml`, containing only the ACFC catalogs:
   ```yaml
   conventions:
     profiles:
       acfc_prx:
         default_catalog: {stage: d1_dlk, standard: d1_std}
   ```
   This branch has **no auto-load**: the overlay applies only when
   `CODEGEN_CONFIG_OVERLAYS` names it.
3. This document.

None of the IIG-first work is here (no IIG review / clean workbooks, no
iig_v2 derivation fixes, no scorecard, no src-first shim, no `codegen
doctor`). What it delivers is the **deployment DDL**: one combined
`<FEED>_DDL.txt` per feed with three-part names, plus the framework
artefacts this branch already wrote (`config_rows.xlsx`,
`config_inserts.xlsx`, and under `acfc_prx` the SQL Server DML
`config_inserts_<env>.sql`).

## Where it comes from

| Ref | Commit | |
| --- | --- | --- |
| tag `v0.5.8-acfc` | 3a5b85d (2026-09-21) | ancestor of the branch (`git merge-base --is-ancestor` → yes) |
| `origin/fix/remove-mock-provider-ui-text` | e89a263 (2026-09-23) | 29 commits after the tag; the branch point |

## Verified locally (2026-10-07)

- Full suite in a worktree of this branch: see the commit message for the
  count (2026-09-23 record: 730 passed / 27 skipped). The gitignored fixtures
  (SFMC contracts, the raw pair-1 IIG golden) were copied in from the main
  checkout; nothing gitignored is committed.
- CV golden pair, `--dry-run --skip-tests --output-mode framework --profile
  acfc_prx` with `CODEGEN_CONFIG_OVERLAYS=config/overlays/acfc_env.yaml`:
  all three feeds **PASS_WITH_FLAGS**; DDL `CREATE OR REPLACE TABLE
  d1_dlk.stg_sdh.cv_community_demographic_risk` /
  `d1_std.sdh.cv_community_demographic_risk` (and the same shape for the other
  two feeds). Without the overlay the same run is **FAIL**
  (`catalog_unstated`) and writes no DDL.

## Run it in ACFC

**App env** (in `app.yaml` env or the App's environment settings):

```
CODEGEN_CONFIG_OVERLAYS=config/overlays/acfc_env.yaml
```

Deploy from the Git folder checked out at `backup/ddl-only`; the bumped
marker rebuilds the venv. In the App choose the documents, set the
conventions profile to `acfc_prx`, output **Framework**, Generate.

**Notebook** (`acfc_run.py` on this branch): set
`os.environ["CODEGEN_CONFIG_OVERLAYS"] = "config/overlays/acfc_env.yaml"` before
the "Bring the pair down" cell (or in the cluster env); widget
`conventions_profile = acfc_prx`. Its `generate` already passes
`--output-mode framework --skip-tests`.

**CLI**, from the repo root of the checkout (`$PAIR` holds the pair's FRD
`.docx` and STTM `.xlsx`):

```bash
export CODEGEN_CONFIG_OVERLAYS=config/overlays/acfc_env.yaml
python -m codegen.cli layout --workbook "$PAIR/<STTM>.xlsx" --frd "$PAIR/<FRD>.docx" \
    --frd-contract-out work/frd.contract.json --profile-out work/sttm.layout.json \
    --report-unresolved work/unresolved_headers.md --require-complete
python -m codegen.cli extract-sttm --workbook "$PAIR/<STTM>.xlsx" \
    --frd-contract work/frd.contract.json --layout work/sttm.layout.json \
    --out work/sttm.contract.json
python -m codegen.cli generate --frd-contract work/frd.contract.json \
    --sttm-contract work/sttm.contract.json --output-mode framework \
    --profile acfc_prx --skip-tests [--dry-run]
```

The DDL lands at `out/<feed_slug>/framework/<FEED>_DDL.txt` (with
`CODEGEN_STORAGE_OUTPUTS` set, in that role).

## Caveats

- No src-first shim on this branch: if the Apps venv does NOT rebuild, a stale
  wheel can still shadow the tree. The bumped marker is what forces the
  rebuild — check the App log shows the new install.
- Fresh Windows checkouts with `core.autocrlf=true` convert
  `docs/acfc/rfc_capture/.../goldens/pair_1/ACCUM_DDL.txt` to CRLF (no
  `-text` rule outside `fixtures/**`), which fails
  `test_every_registered_fixture_is_tracked_and_byte_stable` locally only.
  Not an issue on Linux / ACFC.
