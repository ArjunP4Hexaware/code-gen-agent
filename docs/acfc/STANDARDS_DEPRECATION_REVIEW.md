# Standards deprecation review (2026-10-22)

Soham was told the 2023/2024 *Data Engineering Coding Standards* document is
deprecated. This page records what that means for the agent, so the decision can be
picked up later. The documents themselves are client documents and stay out of the repo.

## The documents

In `/Workspace/Users/<me>/standards_docs/`:

| File | Status | What it covers |
| --- | --- | --- |
| `EDO Data Engineering Naming Standards.docx` | current | `WF_` / `NB_` / `PL_` naming patterns, product / sub-product codes, the abbreviation tables |
| `EDO Data Engineering Coding Standards.pdf` | current | "Azure Cloud Data Engineering Coding Standards", **Databricks section** (v0.0, 4/8/2024) |
| `EDO - Data, Sql & Pyspark Coding Standards.pdf` | current | data standards (table / column / view naming, column order), SQL and PySpark practice (Feb 2023) |
| `deprecated/Data_Engineering_Coding_Standards.pdf` | **deprecated** | the same series, **Azure Data Factory section** (v0.0, 4/8/2024) |

The agent was configured in August from `EDO Data Engineering Coding Standards.docx`
(received 2026-08-26, no longer anywhere we can reach). It most likely combined the ADF and
Databricks sections. The agent never reads the folder at run time: the rules were
transcribed into `config/config.yaml` (`engineering_standards:`, `job:`) and the templates.
Removing a document changes nothing until the config / templates change.

## The rules, by source

### A. Backed by a current document (keep)

- All naming rules (Naming Standards).
- Python / Spark style: secrets in Key Vault, no lambdas, no `print` (use logging),
  `F.lit(None)` for empty columns, no UDFs, a select as the schema contract, explicit join
  types, no right joins, the 79-character line limit (the agent uses 100: a deviation), temp
  tables cleaned up / views for intermediates (Databricks section + Data/SQL/PySpark).

### B. Only in the deprecated ADF section (decision needed)

| # | Rule | Where the agent applies it |
| --- | --- | --- |
| 1 | Success **and** failure email alerts to the prod-support DL on every pipeline | `templates/job/workflow.json.j2` (unconditional), `job.notification_emails` |
| 2 | Timeout = execution hours + 1–2, never the 7-day (ADF activity) default | `job.timeout_hours` → `timeout_seconds` |
| 3 | DQ on upsert loads by default: NULL check on the PK, dedup on the key, NULL check on referential columns when recycle is on; rejects to a reject table + email | `rejects.py`, `dq.py`, `recycle.py` / `reference.py` (notebook mode) |
| — | DQ configured in `DATA_QUALITY_RULES`, email via `EMAIL_TEMPLATE_CONFIG` | IIG sheets — but those are filled because the prod goldens have them, not because of this document. Unaffected. |

Each was written for ADF pipelines and carried over to Databricks jobs. The FRD's own
validation rules still drive DQ per feed whatever is decided for rule 3.

### C. In no document (program decisions)

| # | Rule | Source |
| --- | --- | --- |
| 4 | Job clusters on DBR 15.4 LTS + Photon | unknown (the August `.docx`, or a call) |
| 5 | `CLUSTER BY AUTO` on new tables; MERGE instead of UPDATE | the 2026-08-26 framework calls (CLAUDE.md "Client framework doctrine") |

## Impact

- **Framework output (DDL + IIG, what ACFC deploys):** barely affected; its DQ / email rows
  follow the prod goldens.
- **Notebook output** (`job/workflow.json`, the PySpark modules): carries rules 1–4.

## Decisions (Soham) — OPEN

| Rule | Options | Decision |
| --- | --- | --- |
| 1. Alerts | both / failure only / none | |
| 2. Timeout | run hours + 1 / other | |
| 3. Default DQ on upsert | keep / only what the FRD states | |
| 4. DBR 15.4 + Photon | keep / change | |
| 5. CLUSTER BY AUTO, MERGE | keep (recommended) / change | |

## To do regardless of the decisions

1. Rewrite `docs/EDO_STANDARDS_ALIGNMENT.md` so every rule names its real source (current
   document, program decision, FRD); its "Coding standards (Databricks section)" table
   credits rules 1–3 to the wrong section.
2. Replace `print` with logging in the v2 notebook templates (`notebook_v2/run.py.j2`,
   `run_report.py.j2`, `framework/insert_scripts_notebook.py.j2`) — both current coding
   documents forbid `print`.
3. Update `engineering_standards.status` ("EDO Data Engineering Naming + Coding Standards
   (received 2026-08-26)"), stamped into every generated DDL and `ADDITION.md`. Byte-pinned
   outputs change: one version bump with the snapshots / fixtures refreshed. Also the
   reference-document list in `config/config.yaml` (`EDO Data Engineering Coding
   Standards.docx`), the UX skill, `DEMO_SCRIPT.md`, `port_kit/`.
4. The deprecated PDF names the real prod-support DL: it never enters the repo; it is set at
   deployment through `CODEGEN_NOTIFICATION_EMAILS`.
