# IIG fill rate — DATABRICKS_NOTEBOOK_DETAILS, DATA_FACTORY_PIPELINE_SCHEDULE, EMAIL_TEMPLATE_CONFIG (2026-10-13)

Per column: the share of corpus rows that fill it against the agent's, before and after the
ACFC overlay's `derived_cells` (config/overlays/acfc_env.yaml; one `iig_derived` NOTE per column).
Columns the corpus fills in >= 90% of rows only. `assigned` = iig_keys.yaml needs_assignment or the
template's always_blank (ids, workspace URL / secret / cluster, audit stamps): never invented.

**Corpus (home):** the 199-IIG corpus is on D1 only. At home: the SFMC reference IIG, the pair-1
golden and the CAQH golden (three workbooks, percentages only here). **Agent:** the home CAQH pair,
mock, `--output-mode framework --profile acfc_prx --iig-template iig_v2`, before and after.

On D1, over the full corpus:

```
python tools/iig_fill_rate.py --corpus docs/acfc/iig_goldens --agent <run outputs> --json fill.json
```

## DATABRICKS_NOTEBOOK_DETAILS

Corpus 7 rows; agent 2 rows.

| column | corpus % | agent before % | agent after % | after | how |
| --- | --- | --- | --- | --- | --- |
| PIPELINE_ID | 100.0 | 0.0 | 0.0 | assigned |  |
| PIPELINE_NAME | 100.0 | 0.0 | 100.0 | ok | derived: the schedule's leg pipeline name |
| GROUP_ID | 100.0 | 0.0 | 0.0 | assigned |  |
| SEQ_NM | 100.0 | 100.0 | 100.0 | ok |  |
| PROCESS_NAME | 100.0 | 0.0 | 100.0 | ok | derived: `{layer} Load for {source}` |
| TGT_REFRESH_TYPE | 100.0 | 100.0 | 100.0 | ok |  |
| ACTIVE_FLAG | 100.0 | 100.0 | 100.0 | ok |  |
| DATABRICKS_WORKSPACE_URL | 100.0 | 0.0 | 0.0 | assigned |  |
| DATABRICKS_WORKSPACE_SECRET | 100.0 | 0.0 | 0.0 | assigned |  |
| DATABRICKS_CLUSTERID | 100.0 | 0.0 | 0.0 | assigned |  |
| DATABRICKS_NOTEBOOK_PATH | 100.0 | 0.0 | 100.0 | ok | derived: `/Workspace/iig/{notebook}` |
| DATABRICKS_NOTEBOOK_NAME | 100.0 | 100.0 | 100.0 | ok |  |
| CREATED_BY | 100.0 | 0.0 | 0.0 | assigned |  |
| CREATED_DATE | 100.0 | 0.0 | 0.0 | assigned |  |
| UPDATED_BY | 100.0 | 0.0 | 0.0 | assigned |  |
| UPDATED_DATE | 100.0 | 0.0 | 0.0 | assigned |  |
| CLUSTER_DETAILS_ID | 100.0 | 0.0 | 0.0 | assigned |  |

## DATA_FACTORY_PIPELINE_SCHEDULE

Corpus 12 rows; agent 4 rows.

| column | corpus % | agent before % | agent after % | after | how |
| --- | --- | --- | --- | --- | --- |
| PIPELINE_ID | 100.0 | 0.0 | 0.0 | assigned |  |
| PIPELINE_NAME | 100.0 | 100.0 | 100.0 | ok |  |
| PIPELINE_DESCRIPTION | 100.0 | 100.0 | 100.0 | ok |  |
| PIPELINE_FREQUENCY | 100.0 | 100.0 | 100.0 | ok |  |
| NO_OF_CYCLE_PER_DAY | 100.0 | 100.0 | 100.0 | ok |  |
| DAY_OF_SCHEDULE | 100.0 | 100.0 | 100.0 | ok |  |
| ACTIVE_FLAG | 100.0 | 100.0 | 100.0 | ok |  |
| ACTIVE_START_DATE | 100.0 | 0.0 | 0.0 | gap | open: a per-RFC go-live date, no document states it, no value dominates |
| ACTIVE_END_DATE | 100.0 | 100.0 | 100.0 | ok |  |
| APPLICATION_NAME | 100.0 | 0.0 | 100.0 | ok | derived: `{source}` |
| CREATED_BY | 100.0 | 0.0 | 0.0 | assigned |  |
| CREATED_DATE | 100.0 | 0.0 | 0.0 | assigned |  |
| UPDATED_BY | 100.0 | 0.0 | 0.0 | assigned |  |
| UPDATED_DATE | 100.0 | 0.0 | 0.0 | assigned |  |

## EMAIL_TEMPLATE_CONFIG

Corpus 6 rows; agent 2 rows.

| column | corpus % | agent before % | agent after % | after | how |
| --- | --- | --- | --- | --- | --- |
| TEMPLATE_NAME | 100.0 | 0.0 | 100.0 | ok | derived: `{source}` (the corpus writes `<source> <subprocess>`) |
| PROCESS_NAME | 100.0 | 0.0 | 100.0 | ok | derived: `{source}` (as TEMPLATE_NAME) |
| STATUS | 100.0 | 100.0 | 100.0 | ok |  |
| ACTIVE_FLAG | 100.0 | 100.0 | 100.0 | ok |  |
| SUBJECT | 100.0 | 0.0 | 100.0 | ok | derived: `{source} Load {outcome}` |
| BODY | 100.0 | 0.0 | 100.0 | ok | derived: `{source} Files Load Process {outcome}` |
| SENDER_NAME | 100.0 | 0.0 | 100.0 | ok | constant `dbo` (dominant) |
| SENDER_EMAIL | 100.0 | 0.0 | 100.0 | ok | `job.notification_sender` (env CODEGEN_NOTIFICATION_SENDER) |
| EMAIL_TO | 100.0 | 100.0 | 100.0 | ok |  |
| UPDATED_BY | 100.0 | 0.0 | 0.0 | assigned |  |

Below 90% in the home corpus, left as they were: DQ_NOTEBOOK_PATH (3 of 7 rows), BODY_QUERY (one
golden, a feed-specific query), EMAIL_CC (4 of 6), PARENT_PIPELINE_ID (assigned).

Against the CAQH golden (counts only): notebook PROCESS_NAME 2/2, APPLICATION_NAME 4/4, SUBJECT 2/2,
SENDER_NAME 2/2 equal; BODY 2/2 after whitespace normalization; NOTEBOOK_PATH 1/2; email
TEMPLATE_NAME / PROCESS_NAME 0/2 (the golden adds a subprocess word no document states);
notebook PIPELINE_NAME 0/2 (a convention column, never scored).
