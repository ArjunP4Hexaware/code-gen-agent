# IIG diff per sheet - scrubbed export

Every value below is scrubbed: a scrub_check class (and a local-denylist term) is `<CLASS>`; a token found in the golden but not in the repo's committed fixtures is `G<n>`, any other token outside the fixtures is `A<n>` - one map for every file of this export, so the same token is the same placeholder everywhere. Tokens under 3 characters and numbers under 5 digits are kept. CREATED_BY / UPDATED_BY values are withheld.

Template sheet and column names are written as they are; every other name is scrubbed.

## Headers

HEADERS (agent vs template iig_v2 and vs the golden): 0 issue(s)
  DATA_FACTORY_PIPELINE_SCHEDULE vs golden: template-only (not scored) PROCESS_NAME, SUBPROCESS_NAME, LAYER_NAME, COMPLETION_SLA, RUNTIME_SLA, CRITICAL_PROCESSING_PERIOD, UDF1, UDF2, UDF3, UDF4, UDF5, IsFileCopyReqFlag
  ADLS_DELTA_INGESTION_DETAILS vs golden: template-only (not scored) FILE_METADATA
  EMAIL_TEMPLATE_CONFIG vs golden: template-only (not scored) EMAIL_NOTIFICATION_URL
  every sheet's headers match (names, spelling, order)

| sheet | paired (identity / order / position / key) | unpaired (golden / agent) | score | comparable | exact | normalized | mismatch | missing | extra | out of scope | convention | bsa-owned | template-only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | 4 / 0 / 0 / 0 | 0 / 0 | 42.5 | 42.5 | 8 | 9 | 12 | 11 | 0 | 0 | 0 | 4 | 48 |
| FILE_ADLS_INGESTION_DETAILS | 0 / 0 / 0 / 0 | 0 / 0 | - | - | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| ADLS_DELTA_INGESTION_DETAILS | 0 / 3 / 0 / 0 | 1 / 0 | 40.7 | 40.7 | 50 | 20 | 50 | 46 | 6 | 0 | 4 | 0 | 3 |
| STGDELTA_STDDELTA_INGESTION_DET | 0 / 1 / 0 / 0 | 0 / 0 | 34.5 | 34.5 | 9 | 1 | 19 | 0 | 0 | 0 | 1 | 0 | 0 |
| ADLS_FIXED_WIDTH_HANDLER | 0 / 3 / 0 / 0 | 0 / 0 | 33.3 | 33.3 | 15 | 3 | 18 | 18 | 0 | 0 | 0 | 0 | 0 |
| DATABRICKS_NOTEBOOK_DETAILS | 2 / 0 / 0 / 0 | 1 / 0 | 13.3 | 13.3 | 4 | 0 | 6 | 20 | 0 | 0 | 6 | 3 | 0 |
| DATA_QUALITY_RULES | 0 / 0 / 0 / 0 | 8 / 6 | 0.0 | 0.0 | 0 | 0 | 0 | 56 | 42 | 0 | 0 | 0 | 0 |
| EMAIL_TEMPLATE_CONFIG | 2 / 0 / 0 / 0 | 0 / 0 | 27.3 | 27.3 | 6 | 0 | 8 | 8 | 0 | 0 | 2 | 0 | 2 |

Missing = a golden cell the agent row does not fill (or a golden row no agent row pairs with); extra = an agent cell / row the golden does not have.

## DATA_FACTORY_PIPELINE_SCHEDULE

Identity components (distinct values golden / agent / shared): @feed 1/1/1

| column | exact | normalized | mismatch | missing | extra |
| --- | --- | --- | --- | --- | --- |
| PARENT_PIPELINE_ID | 0 | 0 | 1 | 3 | 0 |
| PIPELINE_DESCRIPTION | 0 | 0 | 4 | 0 | 0 |
| PIPELINE_FREQUENCY | 0 | 1 | 3 | 0 | 0 |
| NO_OF_CYCLE_PER_DAY | 4 | 0 | 0 | 0 | 0 |
| DAY_OF_SCHEDULE | 0 | 0 | 0 | 4 | 0 |
| ACTIVE_FLAG | 0 | 4 | 0 | 0 | 0 |
| ACTIVE_START_DATE | 0 | 0 | 0 | 4 | 0 |
| ACTIVE_END_DATE | 0 | 4 | 0 | 0 | 0 |
| ESTIMATED_START_TIME | 4 | 0 | 0 | 0 | 0 |
| APPLICATION_NAME | 0 | 0 | 4 | 0 | 0 |

## FILE_ADLS_INGESTION_DETAILS

No cells compared (sheet on one side only).

## ADLS_DELTA_INGESTION_DETAILS

Identity components (distinct values golden / agent / shared): @feed 1/1/1; @flow 1/1/1; TGT_TABLE_NAME 1/1/0; @file 4/3/0

| column | exact | normalized | mismatch | missing | extra |
| --- | --- | --- | --- | --- | --- |
| OBJECT_NAME | 0 | 0 | 3 | 1 | 0 |
| DOMAIN | 3 | 0 | 0 | 1 | 0 |
| SUBDOMAIN | 1 | 2 | 0 | 1 | 0 |
| SOURCE | 0 | 0 | 3 | 1 | 0 |
| FREQUENCY | 2 | 0 | 1 | 1 | 0 |
| LOB | 3 | 0 | 0 | 1 | 0 |
| CLAIM_TYPE_ID | 3 | 0 | 0 | 1 | 0 |
| ACTIVE_FLAG | 3 | 0 | 0 | 1 | 0 |
| SRC_CONTAINER_NAME | 0 | 0 | 3 | 1 | 0 |
| SRC_ADLS_PATH | 0 | 0 | 3 | 1 | 0 |
| SRC_FILE_NAME | 0 | 0 | 3 | 1 | 0 |
| SRC_FORMAT | 0 | 0 | 3 | 1 | 0 |
| SRC_COLUMNS | 0 | 0 | 3 | 1 | 0 |
| SRC_DATA_TYPE | 0 | 0 | 3 | 1 | 0 |
| SRC_FILE_DELIMITER | 0 | 0 | 0 | 4 | 0 |
| SRC_REC_LNGTH | 3 | 0 | 0 | 1 | 0 |
| SRC_COL_LNGTH | 3 | 0 | 0 | 1 | 0 |
| SRC_COL_STRT_END_INDX | 3 | 0 | 0 | 1 | 0 |
| SRC_ADLS_ARCHVL_PATH | 0 | 0 | 3 | 1 | 0 |
| SRC_COMPRESSION | 3 | 0 | 0 | 1 | 0 |
| HEADER_FLAG | 0 | 3 | 0 | 1 | 0 |
| MULTILINE_FLAG | 0 | 3 | 0 | 1 | 0 |
| SCHEMA_DRIFT_FLAG | 0 | 3 | 0 | 1 | 0 |
| FILE_HEADER_FLAG | 0 | 3 | 0 | 1 | 0 |
| FILE_FOOTER_FLAG | 0 | 3 | 0 | 1 | 0 |
| MANDATORY_FIELD_LIST | 0 | 0 | 0 | 1 | 3 |
| TGT_DATABASE_NAME | 0 | 0 | 3 | 1 | 0 |
| TGT_TABLE_NAME | 0 | 0 | 3 | 1 | 0 |
| TGT_CONTAINER_NAME | 0 | 0 | 3 | 1 | 0 |
| TGT_ADLS_PATH | 0 | 0 | 3 | 1 | 0 |
| TGT_COLUMN_NAMES | 0 | 0 | 3 | 1 | 0 |
| TGT_FORMAT | 3 | 0 | 0 | 1 | 0 |
| TGT_DATA_TYPE | 0 | 0 | 3 | 1 | 0 |
| TGT_LOAD_OPTION | 2 | 0 | 1 | 1 | 0 |
| TGT_RJT_ADLS_PATH | 0 | 0 | 3 | 1 | 0 |
| TGT_PARTITION_COLUMN | 3 | 0 | 0 | 1 | 0 |
| TGT_PARTITION_VALUE | 3 | 0 | 0 | 1 | 0 |
| TGT_PRIMARY_KEY | 0 | 0 | 0 | 1 | 3 |
| RECYCL_ENBL_FLG | 0 | 3 | 0 | 1 | 0 |
| RECYCL_TBL_NM | 3 | 0 | 0 | 1 | 0 |
| RECYCL_ADLS_PATH | 3 | 0 | 0 | 1 | 0 |
| RECYCL_RETN_DAYS | 3 | 0 | 0 | 1 | 0 |
| MAPPING_EXPRESSION | 3 | 0 | 0 | 1 | 0 |

## STGDELTA_STDDELTA_INGESTION_DET

Identity components (distinct values golden / agent / shared): @feed 1/1/1; @flow 1/1/1; TGT_TABLE_NAME 1/1/0; @file 1/1/0

| column | exact | normalized | mismatch | missing | extra |
| --- | --- | --- | --- | --- | --- |
| OBJECT_NAME | 0 | 0 | 1 | 0 | 0 |
| DOMAIN | 1 | 0 | 0 | 0 | 0 |
| SUBDOMAIN | 0 | 1 | 0 | 0 | 0 |
| SOURCE | 0 | 0 | 1 | 0 | 0 |
| FREQUENCY | 1 | 0 | 0 | 0 | 0 |
| LOB | 1 | 0 | 0 | 0 | 0 |
| ACTIVE_FLAG | 1 | 0 | 0 | 0 | 0 |
| SRC_CONTAINER_NAME | 0 | 0 | 1 | 0 | 0 |
| SRC_ADLS_PATH | 0 | 0 | 1 | 0 | 0 |
| SRC_TABLE_NAME | 0 | 0 | 1 | 0 | 0 |
| SRC_CATALOG_NAME | 0 | 0 | 1 | 0 | 0 |
| SRC_SCHEMA_NAME | 0 | 0 | 1 | 0 | 0 |
| SRC_FORMAT | 1 | 0 | 0 | 0 | 0 |
| SRC_COLUMNS | 0 | 0 | 1 | 0 | 0 |
| SRC_DATA_TYPE | 0 | 0 | 1 | 0 | 0 |
| SRC_ADLS_ARCHVL_PATH | 0 | 0 | 1 | 0 | 0 |
| TGT_CATALOG_NAME | 0 | 0 | 1 | 0 | 0 |
| TGT_SCHEMA_NAME | 0 | 0 | 1 | 0 | 0 |
| TGT_TABLE_NAME | 0 | 0 | 1 | 0 | 0 |
| TGT_CONTAINER_NAME | 0 | 0 | 1 | 0 | 0 |
| TGT_ADLS_PATH | 0 | 0 | 1 | 0 | 0 |
| TGT_COLUMN_NAMES | 0 | 0 | 1 | 0 | 0 |
| TGT_FORMAT | 1 | 0 | 0 | 0 | 0 |
| TGT_DATA_TYPE | 0 | 0 | 1 | 0 | 0 |
| TGT_LOAD_OPTION | 1 | 0 | 0 | 0 | 0 |
| TGT_RJT_ADLS_PATH | 0 | 0 | 1 | 0 | 0 |
| TGT_PARTITION_COLUMN | 1 | 0 | 0 | 0 | 0 |
| TGT_PARTITION_VALUE | 1 | 0 | 0 | 0 | 0 |
| TGT_PRIMARY_KEY | 0 | 0 | 1 | 0 | 0 |

## ADLS_FIXED_WIDTH_HANDLER

Identity components (distinct values golden / agent / shared): @feed 1/1/1; TGT_TABLE 1/1/0; SEGMENT 3/3/3; COL 3/3/0

| column | exact | normalized | mismatch | missing | extra |
| --- | --- | --- | --- | --- | --- |
| PROCESS_NAME | 0 | 0 | 0 | 3 | 0 |
| VERSION | 0 | 0 | 0 | 3 | 0 |
| SEGMNT_TYP | 0 | 0 | 0 | 3 | 0 |
| ACTIVE_FLAG | 3 | 0 | 0 | 0 | 0 |
| SEGMENT | 0 | 3 | 0 | 0 | 0 |
| SEGMENT_FILTER | 0 | 0 | 0 | 3 | 0 |
| COL | 0 | 0 | 3 | 0 | 0 |
| LEN | 0 | 0 | 3 | 0 | 0 |
| start_ind | 0 | 0 | 3 | 0 | 0 |
| TGT_TABLE | 0 | 0 | 3 | 0 | 0 |
| FILE_TYPE | 0 | 0 | 0 | 3 | 0 |
| EXTENSION | 0 | 0 | 0 | 3 | 0 |
| TGT_AUDIT_CLMS | 0 | 0 | 3 | 0 | 0 |
| SRC_ADLS_ARCHVL_PATH | 0 | 0 | 3 | 0 | 0 |
| IS_MANDATORY | 3 | 0 | 0 | 0 | 0 |
| COLUMN_VALIDATIONS | 3 | 0 | 0 | 0 | 0 |
| FILE_REJECTION | 3 | 0 | 0 | 0 | 0 |
| RJCT_RSN_COLUMN_NM | 3 | 0 | 0 | 0 | 0 |

## DATABRICKS_NOTEBOOK_DETAILS

Identity components (distinct values golden / agent / shared): @feed 1/1/1

| column | exact | normalized | mismatch | missing | extra |
| --- | --- | --- | --- | --- | --- |
| SEQ_NM | 2 | 0 | 0 | 1 | 0 |
| PROCESS_NAME | 0 | 0 | 2 | 1 | 0 |
| TGT_REFRESH_TYPE | 0 | 0 | 2 | 1 | 0 |
| ACTIVE_FLAG | 2 | 0 | 0 | 1 | 0 |
| DATABRICKS_WORKSPACE_URL | 0 | 0 | 0 | 3 | 0 |
| DATABRICKS_WORKSPACE_SECRET | 0 | 0 | 0 | 3 | 0 |
| DATABRICKS_CLUSTERID | 0 | 0 | 0 | 3 | 0 |
| DATABRICKS_NOTEBOOK_PATH | 0 | 0 | 2 | 1 | 0 |
| CLUSTER_DETAILS_ID | 0 | 0 | 0 | 3 | 0 |
| DQ_NOTEBOOK_PATH | 0 | 0 | 0 | 3 | 0 |

## DATA_QUALITY_RULES

Identity components (distinct values golden / agent / shared): @feed 1/1/1; @table 1/1/0; SOURCE_COLUMN 2/5/0; RULE_CLASS 2/5/1

Rows per RULE_TYPE x RULE_CLASS (values scrubbed):

| side | RULE_TYPE | RULE_CLASS | rows |
| --- | --- | --- | --- |
| golden | Custom | DateFormatRule | 4 |
| golden | Custom | DataTypeCastRule | 4 |
| agent | STDDelta | DateConversionRule | 2 |
| agent | Predefined | A46 | 1 |
| agent | Predefined | A47 | 1 |
| agent | STDDelta | LRTrimRule | 1 |
| agent | STDDelta | DataTypeCastRule | 1 |

| column | exact | normalized | mismatch | missing | extra |
| --- | --- | --- | --- | --- | --- |
| SEQUENCE_NO | 0 | 0 | 0 | 8 | 6 |
| RULE_TYPE | 0 | 0 | 0 | 8 | 6 |
| RULE_CLASS | 0 | 0 | 0 | 8 | 6 |
| ACTIVE_RULE_FLG | 0 | 0 | 0 | 8 | 6 |
| SOURCE_COLUMN | 0 | 0 | 0 | 8 | 6 |
| INPUT_PARAM | 0 | 0 | 0 | 8 | 6 |
| TARGET_COLUMN | 0 | 0 | 0 | 8 | 6 |

## EMAIL_TEMPLATE_CONFIG

Identity components (distinct values golden / agent / shared): @feed 1/1/1; STATUS 2/4/2

| column | exact | normalized | mismatch | missing | extra |
| --- | --- | --- | --- | --- | --- |
| TEMPLATE_ID | 0 | 0 | 0 | 2 | 0 |
| PROCESS_NAME | 0 | 0 | 2 | 0 | 0 |
| STATUS | 2 | 0 | 0 | 0 | 0 |
| ACTIVE_FLAG | 2 | 0 | 0 | 0 | 0 |
| SUBJECT | 0 | 0 | 2 | 0 | 0 |
| BODY | 0 | 0 | 2 | 0 | 0 |
| BODY_QUERY | 0 | 0 | 0 | 2 | 0 |
| SENDER_NAME | 0 | 0 | 2 | 0 | 0 |
| SENDER_EMAIL | 0 | 0 | 0 | 2 | 0 |
| EMAIL_TO | 0 | 0 | 0 | 2 | 0 |
| EMAIL_CC | 2 | 0 | 0 | 0 | 0 |

