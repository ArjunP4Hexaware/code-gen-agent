# SharePoint / Microsoft Graph seam — mechanics

Moved from CLAUDE.md (2026-08-28) so only the summary + prohibitions stay
resident; this is the full doctrine for `src/codegen/sharepoint.py`,
`codegen sharepoint-fetch` / `sharepoint-publish`, and
`ui/backend/sharepoint_routes.py`.

- **Standard library only** (`urllib.request`). Graph is plain REST; no SDK,
  no new runtime dependency. (`httpx` was added to the `dev` extra — it is
  test-only: `fastapi.testclient` is httpx-backed and the [ui] extra did not
  pull it, so the demo-UI tests could not actually run.)
- **App-only client credentials.** Secret from `SHAREPOINT_CLIENT_SECRET`
  (env or the gitignored `.env`), same resolution as `ANTHROPIC_API_KEY`.
  Excluded from `SharePointConfig.__repr__` so it cannot reach a traceback.
  Required Graph APPLICATION permission with admin consent: `Sites.Selected`
  on the target site, preferred over tenant-wide `Files.ReadWrite.All`.
- **Config split follows this repo's doctrine, not the source repo's.**
  frd-to-sttm reads every knob from notebook widgets/env. Here the non-secret
  knobs (host, site_path, library, input/output folder) live in
  `config/config.yaml` under `sharepoint:`, and identity + secret are
  env-only so a tenant is never committed. `param_from_config` layers them:
  env var > YAML > default. The section is OPTIONAL — a config without it
  still loads and every other command is unaffected.
- **Fail-loud, both directions.** Missing config raises naming both remedies.
  A short download raises rather than leaving a truncated .xlsx for openpyxl
  to report as a layout problem. A missing library lists what the site has.
  Fetching nothing and publishing nothing are both errors, not no-ops.
- **Publish is separate from generate on purpose.** Generation re-runs every
  time a rule or contract changes, and a re-generate is not a re-publish —
  the human gate sits between them. Running `sharepoint-publish` IS that
  gate, which is why the CLI takes no `--confirm` (mirroring the source
  repo's standalone publish notebook); the HTTP endpoint, which a stray POST
  could reach, DOES require `{"confirm": true}`.
- **Write scope is one folder.** `sharepoint.output_folder` is the only path
  this repo ever writes to. Keep the app registration's write grant scoped
  to it.
- **Publish names are qualified.** `<feed_slug>.md` / `<feed_slug>.ipynb`
  publish under their own name; anything else (`bronze.py`, `ddl.sql`) is
  prefixed `<feed_slug>__`, because those names repeat across feeds and a
  flat library folder has no other way to stop the second feed overwriting
  the first.
- **UI routes** (`ui/backend/sharepoint_routes.py`): a picked document is
  downloaded into `inputs/sharepoint/` — the same place `sharepoint-fetch
  --dest` writes — so it starts through the existing generate path. There is
  deliberately no second "generate from SharePoint" execution path. Status
  codes say whose problem it is: 503 not configured, 502 Graph refused, 400
  bad request, 404 no such feed/artifact, 413 over a cap. The panel renders
  nothing when unconfigured.
