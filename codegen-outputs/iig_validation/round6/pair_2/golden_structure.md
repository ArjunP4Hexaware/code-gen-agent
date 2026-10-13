# Golden structure (counts only)

Note: real GROUP_IDs withheld (PIPELINE_IDs too): group#k / pipeline#k number the distinct ids in sorted order; table / object / file names are compared by normalized value and never printed.

Distinct GROUP_IDs: 6; distinct PIPELINE_IDs: 6

## Sheets

| sheet | rows | grouped by | groups |
| --- | ---: | --- | ---: |
| adls_delta_ingestion_details | 3 | GROUP_ID | 3 |
| all_files_static_information | 3 | not grouped (no GROUP_ID / PIPELINE_ID column) | 0 |
| data_factory_pipeline_schedule | 6 | PIPELINE_ID (sheet has no GROUP_ID) | 6 |
| data_quality_rules | 10 | GROUP_ID | 5 |
| databricks_notebook_details | 6 | GROUP_ID | 6 |
| stgdelta_stddelta_ingestion_det | 3 | GROUP_ID | 3 |

## group#1 (grouped by GROUP_ID)

- sheets with rows: adls_delta_ingestion_details, data_quality_rules, databricks_notebook_details
- PIPELINE_IDs on the same rows: pipeline#1
- pairs with: on TGT_TABLE_NAME: group#2; on OBJECT_NAME: group#2
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adls_delta_ingestion_details | 1 | 1 | 1 | - | 1 | group#2 | 1 | group#2 |
| data_quality_rules | 1 | - | - | - | - | - | - | - |
| databricks_notebook_details | 1 | - | - | - | - | - | - | - |

## group#2 (grouped by GROUP_ID)

- sheets with rows: data_quality_rules, databricks_notebook_details, stgdelta_stddelta_ingestion_det
- PIPELINE_IDs on the same rows: pipeline#2
- pairs with: on TGT_TABLE_NAME: group#1; on OBJECT_NAME: group#1
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): group#1

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_quality_rules | 2 | - | - | - | - | - | - | - |
| databricks_notebook_details | 1 | - | - | - | - | - | - | - |
| stgdelta_stddelta_ingestion_det | 1 | 1 | 1 | - | 1 | group#1 | 1 | group#1 |

## group#3 (grouped by GROUP_ID)

- sheets with rows: adls_delta_ingestion_details, databricks_notebook_details
- PIPELINE_IDs on the same rows: pipeline#3
- pairs with: on TGT_TABLE_NAME: group#4; on OBJECT_NAME: group#4
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adls_delta_ingestion_details | 1 | 1 | 1 | - | 1 | group#4 | 1 | group#4 |
| databricks_notebook_details | 1 | - | - | - | - | - | - | - |

## group#4 (grouped by GROUP_ID)

- sheets with rows: data_quality_rules, databricks_notebook_details, stgdelta_stddelta_ingestion_det
- PIPELINE_IDs on the same rows: pipeline#4
- pairs with: on TGT_TABLE_NAME: group#3; on OBJECT_NAME: group#3
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): group#3

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_quality_rules | 2 | - | - | - | - | - | - | - |
| databricks_notebook_details | 1 | - | - | - | - | - | - | - |
| stgdelta_stddelta_ingestion_det | 1 | 1 | 1 | - | 1 | group#3 | 1 | group#3 |

## group#5 (grouped by GROUP_ID)

- sheets with rows: adls_delta_ingestion_details, data_quality_rules, databricks_notebook_details
- PIPELINE_IDs on the same rows: pipeline#5
- pairs with: on TGT_TABLE_NAME: group#6; on OBJECT_NAME: group#6
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adls_delta_ingestion_details | 1 | 1 | 1 | - | 1 | group#6 | 1 | group#6 |
| data_quality_rules | 2 | - | - | - | - | - | - | - |
| databricks_notebook_details | 1 | - | - | - | - | - | - | - |

## group#6 (grouped by GROUP_ID)

- sheets with rows: data_quality_rules, databricks_notebook_details, stgdelta_stddelta_ingestion_det
- PIPELINE_IDs on the same rows: pipeline#6
- pairs with: on TGT_TABLE_NAME: group#5; on OBJECT_NAME: group#5
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): group#5

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_quality_rules | 3 | - | - | - | - | - | - | - |
| databricks_notebook_details | 1 | - | - | - | - | - | - | - |
| stgdelta_stddelta_ingestion_det | 1 | 1 | 1 | - | 1 | group#5 | 1 | group#5 |

## pipeline#1 (grouped by PIPELINE_ID)

- sheets with rows: data_factory_pipeline_schedule
- GROUP_IDs on the same rows: group#1
- pairs with: on TGT_TABLE_NAME: -; on OBJECT_NAME: -
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_factory_pipeline_schedule | 1 | - | - | - | - | - | - | - |

## pipeline#2 (grouped by PIPELINE_ID)

- sheets with rows: data_factory_pipeline_schedule
- GROUP_IDs on the same rows: group#2
- pairs with: on TGT_TABLE_NAME: -; on OBJECT_NAME: -
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_factory_pipeline_schedule | 1 | - | - | - | - | - | - | - |

## pipeline#3 (grouped by PIPELINE_ID)

- sheets with rows: data_factory_pipeline_schedule
- GROUP_IDs on the same rows: group#3
- pairs with: on TGT_TABLE_NAME: -; on OBJECT_NAME: -
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_factory_pipeline_schedule | 1 | - | - | - | - | - | - | - |

## pipeline#4 (grouped by PIPELINE_ID)

- sheets with rows: data_factory_pipeline_schedule
- GROUP_IDs on the same rows: group#4
- pairs with: on TGT_TABLE_NAME: -; on OBJECT_NAME: -
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_factory_pipeline_schedule | 1 | - | - | - | - | - | - | - |

## pipeline#5 (grouped by PIPELINE_ID)

- sheets with rows: data_factory_pipeline_schedule
- GROUP_IDs on the same rows: group#5
- pairs with: on TGT_TABLE_NAME: -; on OBJECT_NAME: -
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_factory_pipeline_schedule | 1 | - | - | - | - | - | - | - |

## pipeline#6 (grouped by PIPELINE_ID)

- sheets with rows: data_factory_pipeline_schedule
- GROUP_IDs on the same rows: group#6
- pairs with: on TGT_TABLE_NAME: -; on OBJECT_NAME: -
- reads tables written by (its SRC_TABLE_NAME = their TGT_TABLE_NAME): -

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME | rows sharing TGT_TABLE_NAME with another group | pairs with group#k on TGT_TABLE_NAME hash | rows sharing OBJECT_NAME with another group | pairs with group#k on OBJECT_NAME hash |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| data_factory_pipeline_schedule | 1 | - | - | - | - | - | - | - |

## Not grouped

| sheet | rows | distinct OBJECT_NAME | distinct TGT_TABLE_NAME | distinct FILE_NAME |
| --- | --- | --- | --- | --- |
| all_files_static_information | 3 | - | - | 3 |
