# App deploy: `out/` is never part of it (2026-10-13)

## What failed

The D1 live pairing check (`acfc-pairing-check`,
`codegen-outputs/pairing_check/2026-10-13_changes.md` §6) redeployed the App with
`databricks apps deploy … --source-code-path <the D1 Git folder>`. The deployment
failed: the snapshot could not find `out/`, which the harness had deleted between pair
runs. The App stayed on post37.

## Why

- A `--source-code-path` deploy snapshots the Workspace folder **as it is at that
  moment**. `.gitignore` excludes nothing at that step; the Databricks docs tie the
  exclusions to the `databricks sync` upload, not to `apps deploy`.
- `out/` was in the Git folder only because the harness ran codegen there, and the
  CLI's default output dir is `out/` inside the checkout. Something created it after the
  pull, and the cleanup deleted it while the snapshot was reading the folder.
- Nothing the App needs lives in `out/`:
  - `app.yaml` names no path under it.
  - The frontend it serves is the committed `ui/frontend/dist`.
  - Its outputs go to the outputs role (`CODEGEN_STORAGE_OUTPUTS` in `app.yaml`, a
    workspace folder).
  - `out/` is gitignored and never tracked.

## Decision: the deploy is independent of `out/`

The App needs no `out/`, so nothing has to keep one around. Pinned by
`tests/test_deploy_without_out.py`:
- `app.yaml` names nothing under `out/` and sends outputs to the role.
- Every asset `dist/index.html` loads is tracked.
- `out/` is never tracked.
- The App answers `/api/health` and `/` with no `out/` folder present.

Do not "fix" a failed deploy by creating an empty `out/`.

## How to deploy (D1)

1. **Preferred: deploy from Git.** Use `git_source` with branch `feature/multi-table`.
   Only the repository's contents are deployed: no `out/`, no `codegen-state/`, no
   harness leftovers. `dist` is committed, so no build step is needed.
2. **If the source stays the Git folder** (`--source-code-path`):
   - The harness writes its runs **outside** that folder, as the
     `docs/acfc/GENIE_RUN_*` recipes already do:
     `CODEGEN_STORAGE_OUTPUTS=local:/tmp/<run>/out`, `CODEGEN_STORAGE_STATE=local:/tmp/<run>/state`.
   - Its cleanup deletes only what it created under `/tmp`.
   - Never deploy while a pair run is in progress in that folder.

The harness jobs (`codegen-runner/pull_and_run`, `watch`) live in D1 and are
maintained there.
