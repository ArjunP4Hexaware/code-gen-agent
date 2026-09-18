# ENVIRONMENT_ACFC.md — ACFC workspace environment facts

Recorded 2026-09-18 by Genie Code from the ACFC Databricks workspace.
Every fact comes from a command run in that workspace; output is trimmed
to what matters. Where a command could not run, the section says so.

---

## a. Runtimes

### (i) Genie Code serverless shell

```
$ python --version  # via sys.version
Python 3.12.3 (main, Jun 19 2026, 12:46:00) [GCC 13.3.0]
sys.executable: /local_disk0/.ephemeral_nfs/envs/pythonEnv-<uuid>/bin/python

$ pip --version
pip 25.0.1 (python 3.12)

$ node --version
v22.9.0

$ npm --version
npm: not on PATH (shutil.which returns None)
```

### (ii) Notebook cluster

The Genie Code shell IS serverless notebook compute (DBR Serverless,
Python 3.12.3). There is no separate interactive cluster attached.

### (iii) Databricks App runtime

App compute is currently STOPPED (`compute_status.state: STOPPED`).
The App's Python version was not directly observable; the platform
documents Apps as Python 3.10+ on Debian. No startup logs were
available because the App has not been deployed with the current
config changes.

---

## b. Package access

### PyPI resolution

```
$ pip download sqlglot --no-deps -d /tmp/pypi_test
Saved /tmp/pypi_test/sqlglot-30.18.0-py3-none-any.whl
exit: 0
```

PyPI resolves. No internal index; `pip config list`:

```
:env:.no-input='1'
global.constraint='<ephemeral>/pipConstraints.txt'
```

### Dry-run install of the project

```
$ pip install --dry-run -e ROOT[ui,databricks]
Would install: codegen-data-engineer-agent-0.4.1 et_xmlfile-2.0.0
               openpyxl-3.1.5 python-multipart-0.0.32 ruff-0.16.8
exit: 0
```

All dependencies resolve from public PyPI. fastapi, uvicorn,
databricks-sdk already satisfied in the base image.

### App deployment pip step

Not available — App is STOPPED and has not been redeployed with the
current changes.

---

## c. Filesystem

### Workspace writability from notebook

```python
Path(ROOT / "_write_test_deleteme.txt").write_text("test")  # OK
Path(ROOT / "_write_test_deleteme.txt").unlink()             # OK
```

`/Workspace/Users/<user>/...` is writable from serverless notebook.

### Volume existence + writability (current user)

```
codegen_inputs            exists=True  writable=True
codegen_workbooks_in      exists=True  writable=True
codegen_outputs           exists=True  writable=True
codegen_out               exists=True  writable=True
codegen_contracts_in      exists=True  writable=True
mftlanding                exists=True  writable=True
```

All six volumes under `d1_dlk.codegen` exist and are writable by the
current user. **However**, `pathlib.Path.mkdir(parents=True)` on a
`/Volumes/...` path from serverless compute raises
`PermissionError: [Errno 13] Permission denied: '/Volumes'` — the
underlying FUSE mount does not support creating the mount-point
directory itself. Individual files can be written once the volume
path exists.

### App writability

Not observable (App STOPPED). Expected: the App's SP has no UC grants
(see §d), so volume writes will fail until grants are issued.

### Git-folder binary integrity

```
ui/frontend/dist/index.html:                   sha256=9c6f0faa7a106e55... (768 bytes)
fixtures/acfc_shapes/sttm/pair_1_family_a.xlsx: sha256=c8c45093e397b732... (10,481 bytes)
fixtures/reference/EDO_Data_Engineering_Naming_Standards.xlsx: NOT FOUND
```

The tracked synthetic fixtures are intact. The reference spreadsheet
was removed (matches `origin/staging` where it was git-rm'd).

---

## d. Unity Catalog

### Catalogs (29 total)

```sql
SHOW CATALOGS;
-- d1_bus, d1_dlk, d1_dlk_emcp, d1_dlk_hrr, d1_dlk_prx, d1_ds_optum,
-- d1_edh, d1_edh_hrr, d1_edmcore_sqlserver, d1_mdm_publish, d1_pdt,
-- d1_pdt_hrr, d1_rdm_publish, d1_std, d1_std_hrr, d1_std_prx,
-- frisco_analytics_lakefusion_databricks_native_mdm, hive_metastore,
-- main, q1_dlk, ... +9 more  (Total: 29)
```

### Schemas in d1_dlk (418 total; codegen at row 19)

```sql
SHOW SCHEMAS IN d1_dlk;
-- ... codegen ...  (418 schemas total)
```

### Volumes in d1_dlk.codegen

```sql
SHOW VOLUMES IN d1_dlk.codegen;
```

| volume_name          | volume_type |
| -------------------- | ----------- |
| codegen_contracts_in | MANAGED     |
| codegen_inputs       | MANAGED     |
| codegen_out          | MANAGED     |
| codegen_outputs      | MANAGED     |
| codegen_workbooks_in | MANAGED     |
| mftlanding           | MANAGED     |

### Grants for App SP `9f4e709d-e5f2-4c4d-9fff-d3fb7485a54a`

```sql
SHOW GRANTS ON CATALOG d1_dlk;   -- filtered for SP: NONE
SHOW GRANTS ON SCHEMA d1_dlk.codegen;  -- filtered for SP: NONE
```

The App's service principal (`app-5aprci codegen-agent`, SP client ID
`9f4e709d-...`) has **zero Unity Catalog grants** on `d1_dlk` or
`d1_dlk.codegen`. It cannot read or write any volumes. The current
user lacks `MANAGE` on `d1_dlk` so cannot issue grants.

Required grants (a catalog admin must run these):

```sql
GRANT USE CATALOG ON CATALOG d1_dlk TO `9f4e709d-e5f2-4c4d-9fff-d3fb7485a54a`;
GRANT USE SCHEMA ON SCHEMA d1_dlk.codegen TO `9f4e709d-e5f2-4c4d-9fff-d3fb7485a54a`;
GRANT READ VOLUME ON VOLUME d1_dlk.codegen.codegen_inputs TO `9f4e709d-...`;
GRANT READ VOLUME ON VOLUME d1_dlk.codegen.codegen_workbooks_in TO `9f4e709d-...`;
GRANT READ VOLUME, WRITE VOLUME ON VOLUME d1_dlk.codegen.mftlanding TO `9f4e709d-...`;
GRANT READ VOLUME, WRITE VOLUME ON VOLUME d1_dlk.codegen.codegen_outputs TO `9f4e709d-...`;
```

---

## e. Endpoints and secrets

### Serving endpoints (22 total)

```
databricks-claude-opus-4-7    READY
databricks-claude-opus-4-8    READY
databricks-claude-opus-5      READY    ← configured endpoint
databricks-claude-sonnet-5    READY
databricks-claude-sonnet-4-6  READY
databricks-claude-haiku-4-5   READY
databricks-gpt-oss-120b       READY
databricks-gpt-oss-20b        READY
... +14 more
```

`databricks-claude-opus-5` is the configured FMAPI endpoint (Claude
foundation model). All listed endpoints are READY.

### Secret scopes (22 total)

```
agent-edo-sttm-helper, Az_KeyVault_AH_820, Az_KeyVault_Secret_Scope,
Az_Prx_KeyVault_Secret_Scope, Azure_secret_Testing{,2,3},
databricks-package-management, jdbc-sample, jdbc-test, ... +12 more
```

### JDBC reachability

Not tested — no metadata DB connection is configured in the current
`config.yaml`. The `METADATA_DB_SEMANTICS.md` doc was removed in the
upstream diff.

---

## f. App runtime

### app.yaml (as on disk)

```yaml
command: ["python", "-m", "ui.backend.main"]
env:
  - name: CODEGEN_FORCE_MOCK_PROVIDER
    value: "1"
  - name: CODEGEN_EXTRA_INPUT_DIRS
    value: "/Workspace/Users/<user>/frd_sttm_pairs"
```

### App metadata (databricks apps get codegen-agent)

```json
{
  "name": "codegen-agent",
  "app_status.state": "UNAVAILABLE",
  "compute_status.state": "STOPPED",
  "compute_size": "MEDIUM",
  "create_time": "2026-09-11T03:06:53Z",
  "default_source_code_path": "/Workspace/Users/<user>/code-gen-agent",
  "url": "https://codegen-agent-<wid>.8.azure.databricksapps.com",
  "service_principal_client_id": "9f4e709d-e5f2-4c4d-9fff-d3fb7485a54a",
  "service_principal_name": "app-5aprci codegen-agent",
  "effective_user_api_scopes": ["files", "iam.access-control:read",
                                "iam.current-user:read", "sql"]
}
```

### Startup log

Not available — App is STOPPED and has not been redeployed.

---

## g. Network

```
$ curl -sI --connect-timeout 5 https://pypi.org/
HTTP/2 200

$ curl -sI --connect-timeout 5 https://files.pythonhosted.org/
HTTP/2 404          # expected (no path)

$ curl -sI --connect-timeout 5 https://github.com/
HTTP/2 200
```

All three external hosts are reachable from serverless notebook
compute. No egress firewall blocks observed for PyPI or GitHub.
