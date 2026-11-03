# ACFC App environment — one screen (2026-10-07)

A Git deploy must carry its own env: `app.yaml`'s `env:` block is the only
place the App learns where the documents are. If the document chooser is
empty, it now shows a **storage-roots table** (also `GET /api/health`): every
variable below, its value, and a live probe — `readable` / `empty` / `not
shared with the App` (naming the App's service principal) / `not set`.

## 1. The env block (`app.yaml`)

| Variable | Value | Grant the App's service principal needs |
| --- | --- | --- |
| `CODEGEN_EXTRA_INPUT_DIRS` | `workspace:/Workspace/<path to frd_sttm_pairs>` (`;`-separated for several) | **Can Read** — only listed and downloaded |
| `CODEGEN_STORAGE_INPUTS` | `workspace:/Workspace/<…>/codegen/inputs` | **Can Manage** |
| `CODEGEN_STORAGE_STATE` | `workspace:/Workspace/<…>/codegen/state` | **Can Manage** |
| `CODEGEN_STORAGE_OUTPUTS` | `workspace:/Workspace/<…>/codegen/outputs` | **Can Manage** |
| `CODEGEN_CONFIG_OVERLAYS` | `config/overlays/acfc_env.yaml` | — (a file in the deployed tree) |
| `CODEGEN_STATE_DIR` | `/Volumes/d1_dlk/codegen/state` (post72; a LOCAL folder in the deployed tree still works) | **USE CATALOG** on the catalog, **USE SCHEMA** on the schema, **READ VOLUME** on the volume |

`CODEGEN_STATE_DIR` (post56): the environment profiles (`environments/<name>.yaml`)
and the ACFC overlay (`overlays/<profile>.yaml`) are read from it. Without it the
App looks next to its own code, and a staged deploy has no `codegen-state` there
(it is gitignored, and `databricks sync` honours `.gitignore`). Copy the
checkout's `codegen-state/` into the staged tree before the sync and set the
variable to it. The App's startup log prints `codegen-state root: … ; environments
… ; overlays …`, with `[MISSING]` after any folder it cannot see, and the
environment picker names the folder ("profiles read from …") and each field's
source.

post72: a `/Volumes/...` value is a UC volume. The App has no `/Volumes` mount,
so `codegen.state_mirror` copies the folder read-only through the Files API
into `<tmp>/codegen-state-volume/current` at startup (before the config loads,
so the volume's `overlays/<profile>.yaml` applies) and again before every
generate request (`POST /api/generate`, `POST /api/demo/run-live`): an edit on
the volume shows without a redeploy, and a changed copy reloads the config. The
startup line reads `codegen-state root: /Volumes/… (CODEGEN_STATE_DIR; volume)
-> local copy … (N files, copied …)`; a failed refresh keeps the previous copy
and says so, and with no copy at all the line ends `[MISSING]`. The picker shows
each field's source as the volume path. Job compute that mounts `/Volumes`
reads the folder directly; the harness passes it as the `state_dir` job
parameter.

The folders must exist before the App starts — the agent never creates a
root. `workspace:` = the Workspace API (never the `/Workspace` mount).

## 2. The three Can Manage grants

On each of `codegen/inputs`, `codegen/state`, `codegen/outputs`: folder →
**Share** → add the App's service principal → **Can Manage**. Can Edit is
NOT enough: creating a new file in a folder (`selection.json`, a run's
artefacts, an upload) is a Manage operation (observed 2026-09-21: `Missing
required permissions [Manage] on node …`). The pairs folder needs **Can
Read** only.

## 3. Finding the App's service principal

- **App page**: Compute → Apps → the App — the App's details name the
  service principal it runs as (name and application id).
- **CLI**: `databricks apps get <app-name>` → `service_principal_name`,
  `service_principal_client_id`.
- **The App itself**: `GET /api/health` → `principal`, and the storage-roots
  table in an empty document chooser says "probed now, as <principal>".

**A fresh Git deploy may create a NEW App — and with it a NEW service
principal.** Grants made to the previous App's principal do not carry over:
after creating / re-creating the App, re-share the four folders with the new
principal, then open the document chooser (or `/api/health`) and confirm
every row reads `readable` (or `empty` for a new state / outputs folder).
