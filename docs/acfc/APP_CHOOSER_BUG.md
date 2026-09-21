# APP_CHOOSER_BUG — App hangs on workbook selection via API

**Date:** 2026-09-21T19:00Z  
**App:** codegen-agent  
**URL:** `https://codegen-agent-<WORKSPACE_ID>.azure.databricksapps.com`  
**Deployment:** `01f1b5ed563619a0aea04f965d1d3383` (SNAPSHOT, SUCCEEDED)  
**Reporter:** `<SCRUBBED>`  
**App SP:** `<SP_CLIENT_ID>`  

## Summary

The app's STTM chooser endpoints respond normally for read operations
(`GET /api/demo/workbooks`, `GET /api/demo/frd-choices`), but `POST
/api/demo/workbook` — selecting pair 1's STTM — hangs the entire FastAPI
process. After the POST, **every** endpoint (including `/api/feeds`,
`/api/demo/status`) times out. The app never recovers without a restart.

## Reproduction

1. Token exchange (notebook → audience-scoped OAuth).
2. `GET /api/demo/workbooks` — 200 OK.
3. `GET /api/demo/frd-choices` — 200 OK.
4. `POST /api/demo/workbook` with `{"name": "STTM_Project Eagle_OptumRx_1005789_Accumulators File Ingestion from OptumRx.xlsx"}` — **ReadTimeout** after 180 s.
5. `GET /api/demo/status` — **ReadTimeout** after 120 s.
6. `GET /api/feeds` — **ReadTimeout** after 30 s.
7. App remains hung; platform reports `RUNNING` / `ACTIVE`.

## Hypothesis

`DemoRunner.select_workbook()` acquires `self._lock` and then performs
synchronous I/O (workbook parsing, FRD auto-pairing, layout profile
resolution) on the single uvicorn event-loop thread. If any step blocks
(e.g. workspace file read, upstream contract table query), the GIL +
lock hold prevents all other handlers from returning.

The `upstream_error` in `GET /api/demo/frd-choices` is telling:
> `table read failed: You do not have permission to use the SQL Warehouse.`

The SP may be attempting a SQL Warehouse query during workbook selection
that hangs indefinitely on an auth denial rather than raising.

---

## API responses

### 1. GET /api/demo/workbooks — 200 OK

```json
{
  "workbooks": [
    {
      "name": "demo_sttm_cv_golden.xlsx",
      "source": "fixtures/workbooks",
      "selected": false
    },
    {
      "name": "synthetic_segmented_golden.xlsx",
      "source": "fixtures/workbooks",
      "selected": false
    },
    {
      "name": "STTM_Project Eagle_OptumRx_1005789_Accumulators File Ingestion from OptumRx.xlsx",
      "source": "<PAIR_DIR>/pair_1",
      "selected": true
    },
    {
      "name": "VDD_OptumRx_Accumulators.xlsx",
      "source": "<PAIR_DIR>/pair_1",
      "selected": false
    },
    {
      "name": "STTM_ISFDA_1004808_E17231_BestFootForward_HRADataIngestion.xlsx",
      "source": "<PAIR_DIR>/pair_10",
      "selected": false
    },
    {
      "name": "VDD_BestFootForward_HRA.xlsx",
      "source": "<PAIR_DIR>/pair_10",
      "selected": false
    },
    {
      "name": "STTM_Medicare Expansion-MIDS - Socially Determined (1).xlsx",
      "source": "<PAIR_DIR>/pair_2",
      "selected": false
    },
    {
      "name": "VDD_Socially_Determined_MIDS.xlsx",
      "source": "<PAIR_DIR>/pair_2",
      "selected": false
    },
    {
      "name": "STTM_Project Eagle_OptumRx_1005789_Facets Member Eligibility_v1.2.xlsx",
      "source": "<PAIR_DIR>/pair_3",
      "selected": false
    },
    {
      "name": "VDD_Facets_Member_Eligibility.xlsx",
      "source": "<PAIR_DIR>/pair_3",
      "selected": false
    },
    {
      "name": "STTM_Project_Eagle_OptumRx_1005789_PDE Edit Code Report.xlsx",
      "source": "<PAIR_DIR>/pair_4",
      "selected": false
    },
    {
      "name": "VDD_OptumRx_PDE_Edit_Code_Report.xlsx",
      "source": "<PAIR_DIR>/pair_4",
      "selected": false
    },
    {
      "name": "STTM_STG_STD_ACDC_Wellpoint_Medicaid_MedicalClaims_Historical_Ingestion_1006111.xlsx",
      "source": "<PAIR_DIR>/pair_5",
      "selected": false
    },
    {
      "name": "VDD_Wellpoint_Medical_Claims.xlsx",
      "source": "<PAIR_DIR>/pair_5",
      "selected": false
    },
    {
      "name": "STTM_Project Eagle_OptumRx_1005789_Facets CAG Crosswalk Table.xlsx",
      "source": "<PAIR_DIR>/pair_6",
      "selected": false
    },
    {
      "name": "VDD_Facets_CAG_Crosswalk.xlsx",
      "source": "<PAIR_DIR>/pair_6",
      "selected": false
    },
    {
      "name": "STTM_STG_STD_ACLA_UHC_Medicaid_Member_Distribution_RxClaims_Historical_Ingestion_1005567.xlsx",
      "source": "<PAIR_DIR>/pair_7",
      "selected": false
    },
    {
      "name": "VDD_UHC_Medicaid_RxClaims.xlsx",
      "source": "<PAIR_DIR>/pair_7",
      "selected": false
    },
    {
      "name": "STTM_PA CHC Reprocurement_1004429_834_Unified Layout_FILE.xlsx",
      "source": "<PAIR_DIR>/pair_8",
      "selected": false
    },
    {
      "name": "VDD_834_Unified_Layout.xlsx",
      "source": "<PAIR_DIR>/pair_8",
      "selected": false
    },
    {
      "name": "STTM_HR_Analytics_HCM_To_DL_Mapping_Document_1004845_V1.0.xlsx",
      "source": "<PAIR_DIR>/pair_9",
      "selected": false
    },
    {
      "name": "VDD_HCM_PeopleSoft.xlsx",
      "source": "<PAIR_DIR>/pair_9",
      "selected": false
    }
  ]
}
```

### 2. GET /api/demo/frd-choices — 200 OK

```json
{
  "sttm": "STTM_Project Eagle_OptumRx_1005789_Accumulators File Ingestion from OptumRx.xlsx",
  "current": {
    "label": "FRD_STG_STD_OptumRx-Project Eagle 1005789_Accumulators file Ingestion from OptumRx (1).docx",
    "chosen": true
  },
  "upstream": [],
  "upstream_error": "table read failed: You do not have permission to use the SQL Warehouse. Please contact your administrator. Config: host=https://adb-<WORKSPACE_ID>.azuredata",
  "local": [
    "FRD_Medicare Expansion-MIDS - Socially Determined (1).docx",
    "FRD_STD_ISFDA_1004808_E17231_BestFootForward_HRADataIngestion (1).docx",
    "FRD_STG_STD_ACLA_UHC_Medicaid_Member_Distribution_RxClaims_Historical_Ingestion_1005567.docx",
    "FRD_STG_STD_HR_Analytics_HCM_Data_Ingestion_1004845_V1.1 (1).docx",
    "FRD_STG_STD_OptumRx-Project Eagle 1005789_Accumulators file Ingestion from OptumRx (1).docx",
    "FRD_STG_STD_OptumRx-Project Eagle 1005789_Facets Member Eligibility (1).docx",
    "FRD_STG_STD_OptumRx-Project Eagle 1005789_Ingestion of CAG Crosswalk & Provider relationship tables from Facets (1).docx",
    "FRD_STG_STD_OptumRx-Project Eagle 1005789_PDE Edit Code Report File (1).docx",
    "FRD_STG_STD_PA CHC Reprocurement_1004429_834_Unified Layout_FILE (1).docx",
    "FRD_WellPoint_Medical_Claims_Historical_Ingestion_1006111.docx",
    "FRD_demo_cv_golden.contract.json"
  ],
  "no_contract": []
}
```

### 3. POST /api/demo/workbook — ReadTimeout (180 s)

**Request body:**
```json
{"name": "STTM_Project Eagle_OptumRx_1005789_Accumulators File Ingestion from OptumRx.xlsx"}
```

**Response:** No HTTP response received. `requests.exceptions.ReadTimeout` after 180 s.

### 4. GET /api/demo/status — ReadTimeout (120 s)

Issued after the POST timeout. No response — app is hung.

### 5. GET /api/feeds — ReadTimeout (30 s)

Issued after status timeout. No response — confirms full hang.

---

## Log excerpt

**Logs could not be retrieved programmatically.**

* `databricks apps logs codegen-agent` — CLI unavailable from serverless
  notebook compute (runtime auth only, no PAT).
* `/logz` endpoint — returns HTML shell with WebSocket-driven live stream;
  the WebSocket connection requires a browser or `websocket-client` (blocked
  by compute egress policy).
* All app-served endpoints (including hypothetical log routes) are unreachable
  because the FastAPI process is hung.
* Platform still reports `app_status.state: RUNNING`,
  `compute_status.state: ACTIVE`.

**Recommendation:** Retrieve logs from the Databricks Apps UI Logs tab after
`apps stop codegen-agent && apps start codegen-agent` (the stop/start will
flush buffered stdout). Alternatively, run `databricks apps logs codegen-agent`
from a Web Terminal with OAuth auth.

---

## Environment

| Field | Value |
| --- | --- |
| App status (platform) | RUNNING / ACTIVE |
| Active deployment | `01f1b5ed563619a0aea04f965d1d3383` |
| Deployment status | SUCCEEDED |
| Source code path | `<WORKSPACE_PATH>/code-gen-agent` |
| SP scopes | `files`, `iam.access-control:read`, `iam.current-user:read`, `sql` |
| CODEGEN_FORCE_MOCK_PROVIDER | `1` (Layer 2 locked) |
| Upstream contract access | **denied** — SQL Warehouse permission missing for SP |
| Auth method | OAuth token exchange (notebook → audience-scoped) |

---

## Suggested fix

1. **Timeout guard on `select_workbook`:** the handler should run the
   workbook parse / auto-pair / layout probe on a bounded thread with a
   30 s timeout, returning 504 on expiry instead of holding the lock
   indefinitely.
2. **Async lock or per-request lock:** a `threading.Lock` held across I/O
   blocks every other handler in the single-worker uvicorn. Consider an
   `asyncio.Lock` or moving heavy work to `run_in_executor` with a timeout.
3. **Upstream contract query guard:** the `list_contracts` SQL Warehouse
   call inside `select_workbook`'s FRD auto-pairing should have its own
   timeout and should degrade gracefully (skip pairing) instead of hanging.
