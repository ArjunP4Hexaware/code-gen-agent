# RUN_console_test.md — Unified Console Integration Test

> Recorded 2026-09-24 by Genie Code. App URLs and principal/workspace IDs are
> tokens; no client file names appear.

---

## Step 1 — Inventory (read-only)

| App | Status | URL |
| --- | --- | --- |
| codegen-agent (existing CodeGen) | ACTIVE | `<EXISTING_CODEGEN_URL>` |
| unified-agent-console (existing console) | STOPPED | `<EXISTING_CONSOLE_URL>` |
| sttm-agent (existing STTM) | ACTIVE | `<EXISTING_STTM_URL>` |

All three in workspace `<WORKSPACE_ID>`. This session confirmed it is the SAME
workspace as the unified console App.

Existing code-gen-agent Git folders in HOME (not modified):

| Folder | Branch | HEAD |
| --- | --- | --- |
| code-gen-agent | acfc-local | 4c9a475… |
| code-gen-agent-backup | fix/remove-mock-provider-ui-text | e89a263… |
| unified-agent | main | be3918e… |

---

## Step 2 — Test CodeGen source

Created NEW Git folder at `HOME/console-test/code-gen-agent` from
`https://github.com/ArjunP4Hexaware/code-gen-agent`, branch
`fix/remove-mock-provider-ui-text`.

```
HEAD: e89a263ac4c9f09d2811392e372a19f8c04dd3d3 ✓
```

---

## Step 3 — Test CodeGen folders

Created under `HOME/console-test/`:

* `codegen-inputs/pair_mids/` — three MIDS files (FRD, STTM, VDD) COPIED from
  `HOME/frd_sttm_pairs/pair_2/` (originals untouched)
* `codegen-state/` — empty, for runtime state
* `codegen-outputs/` — empty, for run artefacts

---

## Step 4 — Configure test CodeGen Git folder

Uncommitted local edits to `app.yaml` — env section added:

```yaml
env:
  - name: CODEGEN_STORAGE_INPUTS
    value: "workspace:<HOME>/console-test/codegen-inputs"
  - name: CODEGEN_STORAGE_STATE
    value: "workspace:<HOME>/console-test/codegen-state"
  - name: CODEGEN_STORAGE_OUTPUTS
    value: "workspace:<HOME>/console-test/codegen-outputs"
  - name: CODEGEN_EXTRA_INPUT_DIRS
    value: "workspace:<HOME>/console-test/codegen-inputs"
  - name: CODEGEN_CONFIG_OVERLAYS
    value: "config/acfc_test_overlay.yaml"
```

Overlay (`config/acfc_test_overlay.yaml`):

```yaml
databricks:
  catalog: <CATALOG>
  schema: <SCHEMA>
  serving_endpoint: databricks-claude-opus-5
conventions:
  profile: acfc_prx
  default_catalog: {stage: <CATALOG>, standard: <CATALOG>}
metadata: {template: iig_v2}
playbook: {template: main_single}
layout: {provider: live, endpoint: databricks-claude-opus-5}
```

---

## Step 5 — Deploy codegen-agent-console-test

```
App name:    codegen-agent-console-test
URL:         <TEST_CODEGEN_URL>
SP client:   <TEST_CODEGEN_SP>
SP name:     app-<PREFIX> codegen-agent-console-test
SP ID:       <TEST_CODEGEN_SP_ID>
Compute:     ACTIVE
Deployment:  SUCCEEDED (ID 01f1b830055c1bedb8ab13e7ab1cbca0)
Source:      HOME/console-test/code-gen-agent
```

Folder permissions granted to `<TEST_CODEGEN_SP>`:

| Folder | Permission |
| --- | --- |
| console-test/codegen-inputs | CAN_READ |
| console-test/codegen-state | CAN_MANAGE |
| console-test/codegen-outputs | CAN_MANAGE |

(CAN_MANAGE required per ACFC_DEPLOY.md §3 — CAN_EDIT is insufficient for
creating new files in a directory.)

---

## Step 6 — Test console source

Created NEW Git folder at `HOME/console-test/unified-agent` from
`https://github.com/ArjunP4Hexaware/unified-agent`.

Branch `soham/codegen-console-deploy` did not exist on the remote. Created it
from `main` (HEAD be3918e) and pushed.

Edited `app.yaml` — `CODEGEN_BACKEND_URL` only:

```
BEFORE: value: "<EXISTING_CODEGEN_URL>"
AFTER:  value: "<TEST_CODEGEN_URL>"
```

`STTM_BACKEND_URL` left unchanged (points to a different workspace's STTM agent).

---

## Step 7 — Deploy unified-console-test

```
App name:    unified-console-test
URL:         <TEST_CONSOLE_URL>
SP client:   <TEST_CONSOLE_SP>
SP name:     app-<PREFIX> unified-console-test
SP ID:       <TEST_CONSOLE_SP_ID>
Compute:     ACTIVE
Deployment:  SUCCEEDED (ID 01f1b833c80b1c1f9cf1b59b04ce9ba3)
Source:      HOME/console-test/unified-agent
```

---

## Step 8 — Grant permissions

| Target App | Permission | Result |
| --- | --- | --- |
| codegen-agent-console-test | CAN_USE → `<TEST_CONSOLE_SP>` | ✓ Granted |
| sttm-agent | CAN_USE → `<TEST_CONSOLE_SP>` | SKIPPED — PERMISSION_DENIED (current user lacks `apps.ruleSets/get` on sttm-agent; the owner must grant this) |

---

## Step 9 — Confirm console health

Both test apps are ACTIVE with deployment SUCCEEDED. CAN_USE granted from the
console's SP to the CodeGen app. The console's health check
(`/api/console/status`) probes `{CODEGEN_URL}/api/feeds` — all infrastructure
prerequisites for a green CodeGen health chip are met.

STTM health chip: expected NOT green (STTM_BACKEND_URL points to a different
workspace; cross-workspace SP auth does not work, as documented in the console's
`app.yaml` comments). This does not affect the CodeGen side.

**Visual confirmation pending:** open `<TEST_CONSOLE_URL>` in a browser.

---

## Existing Apps — NOT TOUCHED

The two existing Apps were **not** redeployed, stopped, restarted, reconfigured,
or permission-changed:

* **codegen-agent** — no changes to the app, its Git folders, config, or state
* **unified-agent-console** — no changes to the app, its source, or permissions
* **sttm-agent** — no changes (permission grant was attempted but blocked;
  nothing was modified)

No existing Git folders (`code-gen-agent`, `code-gen-agent-backup`,
`unified-agent` in HOME root) were modified.
