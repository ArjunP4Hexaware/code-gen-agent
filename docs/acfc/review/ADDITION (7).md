# Framework addition — sd_community_demographic_risk

- FRD contract: FRD feed contract extracted from FRD_Medicare Expansion-MIDS - Socially Determined.docx sha256 1f720e92f5e30ce794d8572c8dc1b91f807d5db0151f427f4861624a4b34e4d2
- STTM contract: STTM mapping contract extracted from STTM_Medicare Expansion-MIDS - Socially Determined.xlsx sha256 4f654e1701bb46e308379987fee80a912dd40f25bf21f56ebf55f33da4da559b
- Load-pattern FAQ: sha256 defaults (no FAQ file) — 2 answered, 6 unknown
- Engineering standards: EDO Data Engineering Naming + Coding Standards (received 2026-08-26)
- Layout: client IIG template (anonymized reference — fixtures/reference/SFMC_IIG.xlsx); values carry over

Option B output: an **addition to the existing ingestion framework** (the
~90% case), not a standalone pipeline. The DDL scripts and the insert SQL
are **add-ons to ACFC's master notebook** — the notebook the client
already has and runs; the agent never generates or edits that notebook,
it only produces the add-ons.

| File | What it is |
| --- | --- |
| `SD_COMMUNITY_DEMOGRAPHIC_RISK_DDL.txt` | Deployment-team DDL, conformant to the client's reference format (the `.sql` sources sit in `../ddl/`). **Run in the data lake by the deployment team** — the agent never creates target tables. |
| `metadata_inserts.sql` | The client's "DDL": one INSERT per IIG row, sheet by sheet, from the same cells as the IIG — the metadata rows that define the tables in the SQL Server metadata DB (the framework creates the Unity Catalog tables from them; the CREATE text above is the reference). A `TABLE DEFINITIONS` index names every table by its mapped three-part name. Every open cell is a `<<COLUMN#n>>` placeholder: the script does not run until each is replaced. `config_inserts_<env>.sql` is retired (2026-10-08): this file replaces it — one placeholder per row fixes the colliding `@OBJECT_ID` / `@PIPELINE_ID` the per-environment script gave every row. |
| `config_rows.xlsx` | The config rows for the framework DB — **this is the approval artefact**. Every cell carries a provenance badge; the `_provenance` sheet lists them all. |
| `config_inserts.xlsx` | One sheet per populated IIG tab; value rows on the client layout plus the generated INSERT statement (sqlserver dialect) as the final column. **Run only after approval**, through the client's existing ADF metadata path. Plain INSERTs — idempotency belongs to the framework's load path. |
| `sd_community_demographic_risk_IIG_REVIEW.xlsx` | The BSA's review copy of the IIG: sheet `REVIEW_SUMMARY` first (one row per sheet / column / reason / owner group), then the template sheets with every open cell highlighted by owner and commented with its reason, citation and owner. |
| `sd_community_demographic_risk_IIG.xlsx` | The clean copy of the IIG: the template's sheets and columns, values only — the file the BSA certifies and CI/CD loads. |
| `ADDITION.md` | This manifest. |

Columns awaiting framework-assigned IDs (rendered as `NULL`,
never invented): `CLUSTER_DETAILS_ID`, `CREATED_DATE`, `DATABRICKS_CLUSTERID`, `DATABRICKS_WORKSPACE_SECRET`, `DATABRICKS_WORKSPACE_URL`, `GROUP_ID`, `OBJECT_ID`, `PARENT_PIPELINE_ID`, `PIPELINE_ID`, `SRC_CONNECTION_ID`, `TEMPLATE_ID`, `TGT_STORAGE_ACCOUNT_NAME`, `UPDATED_DATE`.

## Switches

- `conventions.profiles.acfc_prx.emit_iig_review`: on — the two IIG workbooks above are written.
- `conventions.profiles.acfc_prx.emit_dml` (with `dml.enabled`): off — no runner notebook (disabled): conventions profile 'acfc_prx' has emit_dml: false; `metadata_inserts.sql` is written regardless.

Layout note: the tab names and column headers are the client IIG template
(anonymized reference — `fixtures/reference/SFMC_IIG.xlsx`).

On approval: the config rows land in the ingestion framework database, and
the DDL + insert SQL are added on to ACFC's master notebook with the
framework-assigned IDs. The agent never inserts unapproved rows.
