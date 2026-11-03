# IIG mismatches - scrubbed export

Every value below is scrubbed: a scrub_check class (and a local-denylist term) is `<CLASS>`; a token found in the golden but not in the repo's committed fixtures is `G<n>`, any other token outside the fixtures is `A<n>` - one map for every file of this export, so the same token is the same placeholder everywhere. Tokens under 3 characters and numbers under 5 digits are kept. CREATED_BY / UPDATED_BY values are withheld.

Cells: 687 (mismatch 30, missing-in-agent 350, extra-in-agent 307). Exact / normalized / needs_assignment cells are not listed.

| sheet | column | status | golden | agent | row key |
| --- | --- | --- | --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | PARENT_PIPELINE_ID | mismatch | SYN-PIPE-002 | 0 | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PIPELINE_DESCRIPTION | mismatch | PARENT_PIPELINE | Pharmacy Daily Grand Master Pipeline | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PIPELINE_FREQUENCY | mismatch | Monthly | Daily | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | DAY_OF_SCHEDULE | missing-in-agent | 0 |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_START_DATE | missing-in-agent | 2026-05-21 |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_END_DATE | mismatch | 9999-12-31 | 9999-12-31 00:00:00 | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | APPLICATION_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST> | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | SUBPROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | LAYER_NAME | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | COMPLETION_SLA | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | RUNTIME_SLA | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | CRITICAL_PROCESSING_PERIOD | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF1 | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF2 | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF3 | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF4 | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF5 | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | IsFileCopyReqFlag | extra-in-agent |  |  | feed#0 (golden row 2, agent row 2) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PARENT_PIPELINE_ID | missing-in-agent | SYN-PIPE-001 |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PIPELINE_DESCRIPTION | mismatch | On Prem to Raw | Pharmacy Master Pipeline for RAW to Stage Regular load | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PIPELINE_FREQUENCY | mismatch | Monthly | Daily | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | DAY_OF_SCHEDULE | missing-in-agent | 0 |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_START_DATE | missing-in-agent | 2026-05-21 |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_END_DATE | mismatch | 9999-12-31 | 9999-12-31 00:00:00 | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | APPLICATION_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST> | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | SUBPROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | LAYER_NAME | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | COMPLETION_SLA | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | RUNTIME_SLA | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | CRITICAL_PROCESSING_PERIOD | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF1 | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF2 | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF3 | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF4 | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF5 | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | IsFileCopyReqFlag | extra-in-agent |  |  | feed#0 (golden row 3, agent row 3) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PARENT_PIPELINE_ID | missing-in-agent | SYN-PIPE-001 |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PIPELINE_DESCRIPTION | mismatch | Raw to Stage | Pharmacy Daily File Pipeline Incremental Load to STAGE | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | DAY_OF_SCHEDULE | missing-in-agent | 0 |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_START_DATE | missing-in-agent | 2026-05-21 |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_END_DATE | mismatch | 9999-12-31 | 9999-12-31 00:00:00 | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | APPLICATION_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST> | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | SUBPROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | LAYER_NAME | extra-in-agent |  | STAGE | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | COMPLETION_SLA | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | RUNTIME_SLA | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | CRITICAL_PROCESSING_PERIOD | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF1 | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF2 | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF3 | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF4 | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF5 | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | IsFileCopyReqFlag | extra-in-agent |  |  | feed#0 (golden row 4, agent row 4) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PARENT_PIPELINE_ID | missing-in-agent | SYN-PIPE-001 |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PIPELINE_DESCRIPTION | mismatch | Stage to Std | <LOCAL_DENYLIST> Pharmacy Regular STANDARD Load | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PIPELINE_FREQUENCY | mismatch | Monthly | Daily | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | DAY_OF_SCHEDULE | missing-in-agent | 0 |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_START_DATE | missing-in-agent | 2026-05-21 |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | ACTIVE_END_DATE | mismatch | 9999-12-31 | 9999-12-31 00:00:00 | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | APPLICATION_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST> | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | PROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | SUBPROCESS_NAME | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | LAYER_NAME | extra-in-agent |  | STANDARD | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | COMPLETION_SLA | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | RUNTIME_SLA | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | CRITICAL_PROCESSING_PERIOD | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF1 | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF2 | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF3 | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF4 | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | UDF5 | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| DATA_FACTORY_PIPELINE_SCHEDULE | IsFileCopyReqFlag | extra-in-agent |  |  | feed#0 (golden row 5, agent row 5) |
| ADLS_DELTA_INGESTION_DETAILS | OBJECT_NAME | missing-in-agent | I_ACCUM_TO_CLIENT |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | DOMAIN | missing-in-agent | Pharmacy |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SUBDOMAIN | missing-in-agent | <LOCAL_DENYLIST>  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SOURCE | missing-in-agent | VENDOR_A |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FREQUENCY | missing-in-agent | Daily |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | LOB | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | CLAIM_TYPE_ID | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_CONTAINER_NAME | missing-in-agent | syn-container-001 |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_NAME | missing-in-agent | I_ACCUM_*_TO_CLIENT_*.csv |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FORMAT | missing-in-agent | csv |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COLUMNS | missing-in-agent | col1:SEGMENT_IDENTIFIER,col2:FILE_TYPE,col3:DATA_CATEGORY,col4:PROCESS_DATE,col5:PROCESS_TIME,col6:GROUP_ID,col7:FILLER_1,col8:VERSION_RELEASE,col9:CARDHOLDER_ID,col10:PLAN_ID,col11:INDIVIDUAL_DEDUCTIBLE,col12:FAMILY_DEDUCTIBLE,col13:COPAY,col14:COINSURANCE,col15:INDIVIDUAL_LIMIT,col16:FAMILY_LIMIT,col17:PLAN_YEAR_START_DATE,col18:PLAN_YEAR_END_DATE,col19:FILLER_2,col20:LINE_COUNT,col21:FILLER_3 |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_DATA_TYPE | missing-in-agent | String:String,String:String,String:String,String:Date,String:String,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Date,String:Date,String:String,String:String,String:String |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_DELIMITER | missing-in-agent | \| |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_REC_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_STRT_END_INDX | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Archive/ |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COMPRESSION | missing-in-agent | N |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | HEADER_FLAG | missing-in-agent | Y     |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MULTILINE_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SCHEMA_DRIFT_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_HEADER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_FOOTER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MANDATORY_FIELD_LIST | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATABASE_NAME | missing-in-agent | stg_vnd_p_accum |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_TABLE_NAME | missing-in-agent | vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_CONTAINER_NAME | missing-in-agent | syn-container-002 |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_COLUMN_NAMES | missing-in-agent | SEGMENT_IDENTIFIER,FILE_TYPE,DATA_CATEGORY,PROCESS_DATE,PROCESS_TIME,GROUP_ID,FILLER_1,VERSION_RELEASE,CARDHOLDER_ID,PLAN_ID,INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE,FILLER_2,LINE_COUNT,FILLER_3,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_FORMAT | missing-in-agent | delta |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATA_TYPE | missing-in-agent | String,String,String,Date,String,String,String,String,String,String,Decimal(17,2),Decimal(18,2),Decimal(19,2),Decimal(20,2),Decimal(21,2),Decimal(22,2),Date,Date,String,String,String,String,TIMESTAMP,TIMESTAMP |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_LOAD_OPTION | missing-in-agent | Overwrite |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_RJT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client_reject |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_COLUMN | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_VALUE | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PRIMARY_KEY | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ENBL_FLG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_TBL_NM | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ADLS_PATH | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_RETN_DAYS | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MAPPING_EXPRESSION | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A2 (golden row 2, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | OBJECT_NAME | missing-in-agent | I_ACCUM_FROM_CLIENT |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | DOMAIN | missing-in-agent | Pharmacy |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SUBDOMAIN | missing-in-agent | <LOCAL_DENYLIST>  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SOURCE | missing-in-agent | SRC_SYS_A |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FREQUENCY | missing-in-agent | Daily |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | LOB | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | CLAIM_TYPE_ID | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_CONTAINER_NAME | missing-in-agent | syn-container-001 |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_NAME | missing-in-agent | I_ACCUM_*_FROM_CLIENT_*.csv |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FORMAT | missing-in-agent | csv |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COLUMNS | missing-in-agent | col1:SEGMENT_IDENTIFIER,col2:FILE_TYPE,col3:DATA_CATEGORY,col4:PROCESS_DATE,col5:PROCESS_TIME,col6:GROUP_ID,col7:FILLER_1,col8:VERSION_RELEASE,col9:CARDHOLDER_ID,col10:PLAN_ID,col11:INDIVIDUAL_DEDUCTIBLE,col12:FAMILY_DEDUCTIBLE,col13:COPAY,col14:COINSURANCE,col15:INDIVIDUAL_LIMIT,col16:FAMILY_LIMIT,col17:PLAN_YEAR_START_DATE,col18:PLAN_YEAR_END_DATE,col19:FILLER_2,col20:LINE_COUNT,col21:FILLER_3 |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_DATA_TYPE | missing-in-agent | String:String,String:String,String:String,String:Date,String:String,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Date,String:Date,String:String,String:String,String:String |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_DELIMITER | missing-in-agent | \| |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_REC_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_STRT_END_INDX | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Archive/ |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COMPRESSION | missing-in-agent | N |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | HEADER_FLAG | missing-in-agent | Y     |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MULTILINE_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SCHEMA_DRIFT_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_HEADER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_FOOTER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MANDATORY_FIELD_LIST | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATABASE_NAME | missing-in-agent | stg_vnd_p_accum |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_TABLE_NAME | missing-in-agent | vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_CONTAINER_NAME | missing-in-agent | syn-container-002 |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_COLUMN_NAMES | missing-in-agent | SEGMENT_IDENTIFIER,FILE_TYPE,DATA_CATEGORY,PROCESS_DATE,PROCESS_TIME,GROUP_ID,FILLER_1,VERSION_RELEASE,CARDHOLDER_ID,PLAN_ID,INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE,FILLER_2,LINE_COUNT,FILLER_3,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_FORMAT | missing-in-agent | delta |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATA_TYPE | missing-in-agent | String,String,String,Date,String,String,String,String,String,String,Decimal(17,2),Decimal(18,2),Decimal(19,2),Decimal(20,2),Decimal(21,2),Decimal(22,2),Date,Date,String,String,String,String,TIMESTAMP,TIMESTAMP |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_LOAD_OPTION | missing-in-agent | Append |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_RJT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client_reject |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_COLUMN | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_VALUE | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PRIMARY_KEY | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ENBL_FLG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_TBL_NM | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ADLS_PATH | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_RETN_DAYS | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MAPPING_EXPRESSION | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A3 (golden row 3, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | OBJECT_NAME | missing-in-agent | F_ACCUM_TO_CLIENT |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | DOMAIN | missing-in-agent | Pharmacy |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SUBDOMAIN | missing-in-agent | <LOCAL_DENYLIST> |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SOURCE | missing-in-agent | VENDOR_A |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FREQUENCY | missing-in-agent | Monthly |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | LOB | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | CLAIM_TYPE_ID | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_CONTAINER_NAME | missing-in-agent | syn-container-001 |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_NAME | missing-in-agent | F_ACCUM_*_TO_CLIENT_*.csv |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FORMAT | missing-in-agent | csv |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COLUMNS | missing-in-agent | col1:SEGMENT_IDENTIFIER,col2:FILE_TYPE,col3:DATA_CATEGORY,col4:PROCESS_DATE,col5:PROCESS_TIME,col6:GROUP_ID,col7:FILLER_1,col8:VERSION_RELEASE,col9:CARDHOLDER_ID,col10:PLAN_ID,col11:INDIVIDUAL_DEDUCTIBLE,col12:FAMILY_DEDUCTIBLE,col13:COPAY,col14:COINSURANCE,col15:INDIVIDUAL_LIMIT,col16:FAMILY_LIMIT,col17:PLAN_YEAR_START_DATE,col18:PLAN_YEAR_END_DATE,col19:FILLER_2,col20:LINE_COUNT,col21:FILLER_3 |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_DATA_TYPE | missing-in-agent | String:String,String:String,String:String,String:Date,String:String,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Date,String:Date,String:String,String:String,String:String |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_DELIMITER | missing-in-agent | \| |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_REC_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_STRT_END_INDX | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Archive/ |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COMPRESSION | missing-in-agent | N |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | HEADER_FLAG | missing-in-agent | Y     |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MULTILINE_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SCHEMA_DRIFT_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_HEADER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_FOOTER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MANDATORY_FIELD_LIST | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATABASE_NAME | missing-in-agent | stg_vnd_p_accum |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_TABLE_NAME | missing-in-agent | vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_CONTAINER_NAME | missing-in-agent | syn-container-002 |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_COLUMN_NAMES | missing-in-agent | SEGMENT_IDENTIFIER,FILE_TYPE,DATA_CATEGORY,PROCESS_DATE,PROCESS_TIME,GROUP_ID,FILLER_1,VERSION_RELEASE,CARDHOLDER_ID,PLAN_ID,INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE,FILLER_2,LINE_COUNT,FILLER_3,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_FORMAT | missing-in-agent | delta |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATA_TYPE | missing-in-agent | String,String,String,Date,String,String,String,String,String,String,Decimal(17,2),Decimal(18,2),Decimal(19,2),Decimal(20,2),Decimal(21,2),Decimal(22,2),Date,Date,String,String,String,String,TIMESTAMP,TIMESTAMP |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_LOAD_OPTION | missing-in-agent | Append |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_RJT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client_reject |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_COLUMN | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_VALUE | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PRIMARY_KEY | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ENBL_FLG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_TBL_NM | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ADLS_PATH | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_RETN_DAYS | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MAPPING_EXPRESSION | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A4 (golden row 4, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | OBJECT_NAME | missing-in-agent | F_ACCUM_FROM_CLIENT |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | DOMAIN | missing-in-agent | Pharmacy |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SUBDOMAIN | missing-in-agent | <LOCAL_DENYLIST> |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SOURCE | missing-in-agent | SRC_SYS_A |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FREQUENCY | missing-in-agent | Monthly |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | LOB | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | CLAIM_TYPE_ID | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_CONTAINER_NAME | missing-in-agent | syn-container-001 |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_NAME | missing-in-agent | F_ACCUM_*_FROM_CLIENT_*.csv |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FORMAT | missing-in-agent | csv |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COLUMNS | missing-in-agent | col1:SEGMENT_IDENTIFIER,col2:FILE_TYPE,col3:DATA_CATEGORY,col4:PROCESS_DATE,col5:PROCESS_TIME,col6:GROUP_ID,col7:FILLER_1,col8:VERSION_RELEASE,col9:CARDHOLDER_ID,col10:PLAN_ID,col11:INDIVIDUAL_DEDUCTIBLE,col12:FAMILY_DEDUCTIBLE,col13:COPAY,col14:COINSURANCE,col15:INDIVIDUAL_LIMIT,col16:FAMILY_LIMIT,col17:PLAN_YEAR_START_DATE,col18:PLAN_YEAR_END_DATE,col19:FILLER_2,col20:LINE_COUNT,col21:FILLER_3 |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_DATA_TYPE | missing-in-agent | String:String,String:String,String:String,String:Date,String:String,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Date,String:Date,String:String,String:String,String:String |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_DELIMITER | missing-in-agent | \| |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_REC_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_LNGTH | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_STRT_END_INDX | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Archive/ |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COMPRESSION | missing-in-agent | N |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | HEADER_FLAG | missing-in-agent | Y     |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MULTILINE_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | SCHEMA_DRIFT_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_HEADER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_FOOTER_FLAG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MANDATORY_FIELD_LIST | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATABASE_NAME | missing-in-agent | stg_vnd_p_accum |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_TABLE_NAME | missing-in-agent | vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_CONTAINER_NAME | missing-in-agent | syn-container-002 |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_COLUMN_NAMES | missing-in-agent | SEGMENT_IDENTIFIER,FILE_TYPE,DATA_CATEGORY,PROCESS_DATE,PROCESS_TIME,GROUP_ID,FILLER_1,VERSION_RELEASE,CARDHOLDER_ID,PLAN_ID,INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE,FILLER_2,LINE_COUNT,FILLER_3,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_FORMAT | missing-in-agent | delta |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATA_TYPE | missing-in-agent | String,String,String,Date,String,String,String,String,String,String,Decimal(17,2),Decimal(18,2),Decimal(19,2),Decimal(20,2),Decimal(21,2),Decimal(22,2),Date,Date,String,String,String,String,TIMESTAMP,TIMESTAMP |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_LOAD_OPTION | missing-in-agent | Append |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_RJT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client_reject |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_COLUMN | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_VALUE | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PRIMARY_KEY | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ENBL_FLG | missing-in-agent | N     |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_TBL_NM | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ADLS_PATH | missing-in-agent | NA |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_RETN_DAYS | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | MAPPING_EXPRESSION | missing-in-agent |  |  | feed#0 \| file_to_stg \| A1 \| A5 (golden row 5, agent row -) |
| ADLS_DELTA_INGESTION_DETAILS | OBJECT_NAME | extra-in-agent |  | A8_A9 | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | DOMAIN | extra-in-agent |  | Pharmacy | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SUBDOMAIN | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SOURCE | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | FREQUENCY | extra-in-agent |  | Daily | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | LOB | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | CLAIM_TYPE_ID | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | ACTIVE_FLAG | extra-in-agent |  | Y | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_CONTAINER_NAME | extra-in-agent |  | mftlanding | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/ | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_NAME | extra-in-agent |  | A8_A9* | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FORMAT | extra-in-agent |  | txt | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COLUMNS | extra-in-agent |  | Record Type:Record Type,File Creation Timestamp:File Creation Timestamp,Sender Name:Sender Name,Receiver Name:Receiver Name,Reserved:Reserved,Version:Version,Record Type:Record Type,Record Timestamp:Record Timestamp,Record Order:Record Order,Record ID:Record ID,Sender Type:Sender Type,Sender ID:Sender ID,Sender Note:Sender Note,Sender Claim Number:Sender Claim Number,Reason Code:Reason Code,A11 Date:A11 Date,Amount Type:Amount Type,Total number of A12:Total number of A12,A11 Type (01):A11 Type (01),IN/OUT of Network Indicator (01):IN/OUT of Network Indicator (01),Individual (01):Individual (01),Amount (01):Amount (01),A13 Amount Indicator (01):A13 Amount Indicator (01),A14 Code (01):A14 Code (01),A11 Type (02):A11 Type (02),IN/OUT of Network Indicator (02):IN/OUT of Network Indicator (02),Individual (02):Individual (02),Amount (02):Amount (02),A13 Amount Indicator (02):A13 Amount Indicator (02),A14 Code (02):A14 Code (02),A11 Type (03):A11 Type (03),IN/OUT of Network Indicator (03):IN/OUT of Network Indicator (03),Individual (03):Individual (03),Amount (03):Amount (03),A13 Amount Indicator (03):A13 Amount Indicator (03),A14 Code (03):A14 Code (03),A11 Type (04):A11 Type (04),IN/OUT of Network Indicator (04):IN/OUT of Network Indicator (04),Individual (04):Individual (04),Amount (04):Amount (04),A13 Amount Indicator (04):A13 Amount Indicator (04),A14 Code (04):A14 Code (04),A11 Type (05):A11 Type (05),IN/OUT of Network Indicator (05):IN/OUT of Network Indicator (05),Individual (05):Individual (05),Amount (05):Amount (05),A13 Amount Indicator (05):A13 Amount Indicator (05),A14 Code (05):A14 Code (05),A11 Type (06):A11 Type (06),IN/OUT of Network Indicator (06):IN/OUT of Network Indicator (06),Individual (06):Individual (06),Amount (06):Amount (06),A13 Amount Indicator (06):A13 Amount Indicator (06),A14 Code (6):A14 Code (6),Carrier ID:Carrier ID,Account Number:Account Number,Group ID:Group ID,Member ID:Member ID,Member First Name:Member First Name,Member A15 Initial:Member A15 Initial,Member Last Name:Member Last Name,Member Date of Birth:Member Date of Birth,Member Gender:Member Gender,Member Relationship Code:Member Relationship Code,Subscriber ID:Subscriber ID,A16 Code:A16 Code,Reserved:Reserved,Record Type:Record Type,Record Count:Record Count,Reserved:Reserved | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_DATA_TYPE | extra-in-agent |  | String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_DELIMITER | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_REC_LNGTH | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_LNGTH | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_STRT_END_INDX | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_ARCHVL_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Archive/ | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COMPRESSION | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | HEADER_FLAG | extra-in-agent |  | Y | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | MULTILINE_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | SCHEMA_DRIFT_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_HEADER_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_FOOTER_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | MANDATORY_FIELD_LIST | extra-in-agent |  | A17,REC_TYP_DTL,A18_TYP,A18_ID,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,A29_CD | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATABASE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_TABLE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_CONTAINER_NAME | extra-in-agent |  | z-use-d1-dlk-stage-01 | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Processed/<LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_COLUMN_NAMES | extra-in-agent |  | REC_TYP_HDR,FILE_A30_TS,A18_NM,A31_NM,A32_HDR,A17,REC_TYP_DTL,REC_TS,REC_A33,REC_ID,A18_TYP,A18_ID,A18_NOTE,A18_CLM_A21,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A34_AMT_IND_01,A35_CD_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A34_AMT_IND_02,A35_CD_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A34_AMT_IND_03,A35_CD_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A34_AMT_IND_04,A35_CD_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A34_AMT_IND_05,A35_CD_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A34_AMT_IND_06,A35_CD_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A36_INIT,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,MBR_A37_CD,SUBSCRIBER_ID,A29_CD,A32_DTL,REC_TYP_TRLR,REC_CNT,A32_TRLR,LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_FORMAT | extra-in-agent |  | delta | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATA_TYPE | extra-in-agent |  | String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,Timestamp,Timestamp | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_LOAD_OPTION | extra-in-agent |  | Append | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_RJT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Reject/<LOCAL_DENYLIST>_reject | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_COLUMN | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_VALUE | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PRIMARY_KEY | extra-in-agent |  | A24_ID,A25_A21,GRP_ID,MBR_ID | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ENBL_FLG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_TBL_NM | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ADLS_PATH | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_RETN_DAYS | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | MAPPING_EXPRESSION | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_METADATA | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A7 (golden row -, agent row 2) |
| ADLS_DELTA_INGESTION_DETAILS | OBJECT_NAME | extra-in-agent |  | A39_A9 | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | DOMAIN | extra-in-agent |  | Pharmacy | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SUBDOMAIN | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SOURCE | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | FREQUENCY | extra-in-agent |  | Daily | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | LOB | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | CLAIM_TYPE_ID | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | ACTIVE_FLAG | extra-in-agent |  | Y | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_CONTAINER_NAME | extra-in-agent |  | mftlanding | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/ | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_NAME | extra-in-agent |  | A39_A9* | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FORMAT | extra-in-agent |  | txt | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COLUMNS | extra-in-agent |  | Record Type:Record Type,File Creation Timestamp:File Creation Timestamp,Sender Name:Sender Name,Receiver Name:Receiver Name,Reserved:Reserved,Version:Version,Record Type:Record Type,Record Timestamp:Record Timestamp,Record Order:Record Order,Record ID:Record ID,Sender Type:Sender Type,Sender ID:Sender ID,Sender Note:Sender Note,Sender Claim Number:Sender Claim Number,Reason Code:Reason Code,A11 Date:A11 Date,Amount Type:Amount Type,Total number of A12:Total number of A12,A11 Type (01):A11 Type (01),IN/OUT of Network Indicator (01):IN/OUT of Network Indicator (01),Individual (01):Individual (01),Amount (01):Amount (01),A13 Amount Indicator (01):A13 Amount Indicator (01),A14 Code (01):A14 Code (01),A11 Type (02):A11 Type (02),IN/OUT of Network Indicator (02):IN/OUT of Network Indicator (02),Individual (02):Individual (02),Amount (02):Amount (02),A13 Amount Indicator (02):A13 Amount Indicator (02),A14 Code (02):A14 Code (02),A11 Type (03):A11 Type (03),IN/OUT of Network Indicator (03):IN/OUT of Network Indicator (03),Individual (03):Individual (03),Amount (03):Amount (03),A13 Amount Indicator (03):A13 Amount Indicator (03),A14 Code (03):A14 Code (03),A11 Type (04):A11 Type (04),IN/OUT of Network Indicator (04):IN/OUT of Network Indicator (04),Individual (04):Individual (04),Amount (04):Amount (04),A13 Amount Indicator (04):A13 Amount Indicator (04),A14 Code (04):A14 Code (04),A11 Type (05):A11 Type (05),IN/OUT of Network Indicator (05):IN/OUT of Network Indicator (05),Individual (05):Individual (05),Amount (05):Amount (05),A13 Amount Indicator (05):A13 Amount Indicator (05),A14 Code (05):A14 Code (05),A11 Type (06):A11 Type (06),IN/OUT of Network Indicator (06):IN/OUT of Network Indicator (06),Individual (06):Individual (06),Amount (06):Amount (06),A13 Amount Indicator (06):A13 Amount Indicator (06),A14 Code (6):A14 Code (6),Carrier ID:Carrier ID,Account Number:Account Number,Group ID:Group ID,Member ID:Member ID,Member First Name:Member First Name,Member A15 Initial:Member A15 Initial,Member Last Name:Member Last Name,Member Date of Birth:Member Date of Birth,Member Gender:Member Gender,Member Relationship Code:Member Relationship Code,Subscriber ID:Subscriber ID,A16 Code:A16 Code,Reserved:Reserved,Record Type:Record Type,Record Count:Record Count,Reserved:Reserved | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_DATA_TYPE | extra-in-agent |  | String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_DELIMITER | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_REC_LNGTH | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_LNGTH | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_STRT_END_INDX | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_ARCHVL_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Archive/ | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COMPRESSION | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | HEADER_FLAG | extra-in-agent |  | Y | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | MULTILINE_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | SCHEMA_DRIFT_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_HEADER_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_FOOTER_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | MANDATORY_FIELD_LIST | extra-in-agent |  | A17,REC_TYP_DTL,A18_TYP,A18_ID,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,A29_CD | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATABASE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_TABLE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_CONTAINER_NAME | extra-in-agent |  | z-use-d1-dlk-stage-01 | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Processed/<LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_COLUMN_NAMES | extra-in-agent |  | REC_TYP_HDR,FILE_A30_TS,A18_NM,A31_NM,A32_HDR,A17,REC_TYP_DTL,REC_TS,REC_A33,REC_ID,A18_TYP,A18_ID,A18_NOTE,A18_CLM_A21,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A34_AMT_IND_01,A35_CD_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A34_AMT_IND_02,A35_CD_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A34_AMT_IND_03,A35_CD_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A34_AMT_IND_04,A35_CD_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A34_AMT_IND_05,A35_CD_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A34_AMT_IND_06,A35_CD_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A36_INIT,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,MBR_A37_CD,SUBSCRIBER_ID,A29_CD,A32_DTL,REC_TYP_TRLR,REC_CNT,A32_TRLR,LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_FORMAT | extra-in-agent |  | delta | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATA_TYPE | extra-in-agent |  | String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,Timestamp,Timestamp | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_LOAD_OPTION | extra-in-agent |  | Append | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_RJT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Reject/<LOCAL_DENYLIST>_reject | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_COLUMN | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_VALUE | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PRIMARY_KEY | extra-in-agent |  | A24_ID,A25_A21,GRP_ID,MBR_ID | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ENBL_FLG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_TBL_NM | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ADLS_PATH | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_RETN_DAYS | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | MAPPING_EXPRESSION | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_METADATA | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A38 (golden row -, agent row 3) |
| ADLS_DELTA_INGESTION_DETAILS | OBJECT_NAME | extra-in-agent |  | A41_A9 | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | DOMAIN | extra-in-agent |  | Pharmacy | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SUBDOMAIN | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SOURCE | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | FREQUENCY | extra-in-agent |  | Daily | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | LOB | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | CLAIM_TYPE_ID | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | ACTIVE_FLAG | extra-in-agent |  | Y | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_CONTAINER_NAME | extra-in-agent |  | mftlanding | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/ | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_NAME | extra-in-agent |  | A41_A9* | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FORMAT | extra-in-agent |  | txt | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COLUMNS | extra-in-agent |  | Record Type:Record Type,File Creation Timestamp:File Creation Timestamp,Sender Name:Sender Name,Receiver Name:Receiver Name,Reserved:Reserved,Version:Version,Record Type:Record Type,Record Timestamp:Record Timestamp,Record Order:Record Order,Record ID:Record ID,Sender Type:Sender Type,Sender ID:Sender ID,Sender Note:Sender Note,Sender Claim Number:Sender Claim Number,Reason Code:Reason Code,A11 Date:A11 Date,Amount Type:Amount Type,Total number of A12:Total number of A12,A11 Type (01):A11 Type (01),IN/OUT of Network Indicator (01):IN/OUT of Network Indicator (01),Individual (01):Individual (01),Amount (01):Amount (01),A13 Amount Indicator (01):A13 Amount Indicator (01),A14 Code (01):A14 Code (01),A11 Type (02):A11 Type (02),IN/OUT of Network Indicator (02):IN/OUT of Network Indicator (02),Individual (02):Individual (02),Amount (02):Amount (02),A13 Amount Indicator (02):A13 Amount Indicator (02),A14 Code (02):A14 Code (02),A11 Type (03):A11 Type (03),IN/OUT of Network Indicator (03):IN/OUT of Network Indicator (03),Individual (03):Individual (03),Amount (03):Amount (03),A13 Amount Indicator (03):A13 Amount Indicator (03),A14 Code (03):A14 Code (03),A11 Type (04):A11 Type (04),IN/OUT of Network Indicator (04):IN/OUT of Network Indicator (04),Individual (04):Individual (04),Amount (04):Amount (04),A13 Amount Indicator (04):A13 Amount Indicator (04),A14 Code (04):A14 Code (04),A11 Type (05):A11 Type (05),IN/OUT of Network Indicator (05):IN/OUT of Network Indicator (05),Individual (05):Individual (05),Amount (05):Amount (05),A13 Amount Indicator (05):A13 Amount Indicator (05),A14 Code (05):A14 Code (05),A11 Type (06):A11 Type (06),IN/OUT of Network Indicator (06):IN/OUT of Network Indicator (06),Individual (06):Individual (06),Amount (06):Amount (06),A13 Amount Indicator (06):A13 Amount Indicator (06),A14 Code (6):A14 Code (6),Carrier ID:Carrier ID,Account Number:Account Number,Group ID:Group ID,Member ID:Member ID,Member First Name:Member First Name,Member A15 Initial:Member A15 Initial,Member Last Name:Member Last Name,Member Date of Birth:Member Date of Birth,Member Gender:Member Gender,Member Relationship Code:Member Relationship Code,Subscriber ID:Subscriber ID,A16 Code:A16 Code,Reserved:Reserved,Record Type:Record Type,Record Count:Record Count,Reserved:Reserved | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_DATA_TYPE | extra-in-agent |  | String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_FILE_DELIMITER | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_REC_LNGTH | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_LNGTH | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COL_STRT_END_INDX | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_ADLS_ARCHVL_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Archive/ | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SRC_COMPRESSION | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | HEADER_FLAG | extra-in-agent |  | Y | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | MULTILINE_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | SCHEMA_DRIFT_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_HEADER_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_FOOTER_FLAG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | MANDATORY_FIELD_LIST | extra-in-agent |  | A17,REC_TYP_DTL,A18_TYP,A18_ID,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,A29_CD | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATABASE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_TABLE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_CONTAINER_NAME | extra-in-agent |  | z-use-d1-dlk-stage-01 | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Processed/<LOCAL_DENYLIST> | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_COLUMN_NAMES | extra-in-agent |  | REC_TYP_HDR,FILE_A30_TS,A18_NM,A31_NM,A32_HDR,A17,REC_TYP_DTL,REC_TS,REC_A33,REC_ID,A18_TYP,A18_ID,A18_NOTE,A18_CLM_A21,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A34_AMT_IND_01,A35_CD_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A34_AMT_IND_02,A35_CD_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A34_AMT_IND_03,A35_CD_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A34_AMT_IND_04,A35_CD_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A34_AMT_IND_05,A35_CD_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A34_AMT_IND_06,A35_CD_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A36_INIT,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,MBR_A37_CD,SUBSCRIBER_ID,A29_CD,A32_DTL,REC_TYP_TRLR,REC_CNT,A32_TRLR,LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_FORMAT | extra-in-agent |  | delta | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_DATA_TYPE | extra-in-agent |  | String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,Timestamp,Timestamp | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_LOAD_OPTION | extra-in-agent |  | Append | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_RJT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Reject/<LOCAL_DENYLIST>_reject | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_COLUMN | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PARTITION_VALUE | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | TGT_PRIMARY_KEY | extra-in-agent |  | A24_ID,A25_A21,GRP_ID,MBR_ID | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ENBL_FLG | extra-in-agent |  | N | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_TBL_NM | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_ADLS_PATH | extra-in-agent |  | NA | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | RECYCL_RETN_DAYS | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | MAPPING_EXPRESSION | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| ADLS_DELTA_INGESTION_DETAILS | FILE_METADATA | extra-in-agent |  |  | feed#0 \| file_to_stg \| A6 \| A40 (golden row -, agent row 4) |
| STGDELTA_STDDELTA_INGESTION_DET | OBJECT_NAME | missing-in-agent | <LOCAL_DENYLIST>_accumclient |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | DOMAIN | missing-in-agent | Pharmacy |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SUBDOMAIN | missing-in-agent | <LOCAL_DENYLIST>  |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SOURCE | missing-in-agent | <LOCAL_DENYLIST>  |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | FREQUENCY | missing-in-agent | Daily |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | LOB | missing-in-agent |  |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_CONTAINER_NAME | missing-in-agent | syn-container-002 |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/ |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_TABLE_NAME | missing-in-agent | vnd_p_accum_client |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_CATALOG_NAME | missing-in-agent | <LOCAL_DENYLIST>_vnd_p |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_SCHEMA_NAME | missing-in-agent | stg_vnd_p_accum |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_FORMAT | missing-in-agent | delta |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_COLUMNS | missing-in-agent | SEGMENT_IDENTIFIER:SEGMENT_IDENTIFIER,FILE_TYPE:FILE_TYPE,DATA_CATEGORY:DATA_CATEGORY,PROCESS_DATE:PROCESS_DATE,PROCESS_TIME:PROCESS_TIME,GROUP_ID:GROUP_ID,FILLER_1:FILLER_1,VERSION_RELEASE:VERSION_RELEASE,CARDHOLDER_ID:CARDHOLDER_ID,PLAN_ID:PLAN_ID,INDIVIDUAL_DEDUCTIBLE:INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE:FAMILY_DEDUCTIBLE,COPAY:COPAY,COINSURANCE:COINSURANCE,INDIVIDUAL_LIMIT:INDIVIDUAL_LIMIT,FAMILY_LIMIT:FAMILY_LIMIT,PLAN_YEAR_START_DATE:PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE:PLAN_YEAR_END_DATE,FILLER_2:FILLER_2,LINE_COUNT:LINE_COUNT,FILLER_3:FILLER_3,SRC_FILE_NAME:SRC_FILE_NAME,REC_CREATION_TIME:REC_CREATION_TIME,REC_UPDATED_TIME:REC_UPDATED_TIME |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_DATA_TYPE | missing-in-agent | String:String,String:String,String:String,Date:Date,String:String,String:String,String:String,String:String,String:String,String:String,Decimal:Decimal,Decimal:Decimal,Decimal:Decimal,Decimal:Decimal,Decimal:Decimal,Decimal:Decimal,Date:Date,Date:Date,String:String,String:String,String:String,String:String,TIMESTAMP:TIMESTAMP,TIMESTAMP:TIMESTAMP |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Archive/Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_CATALOG_NAME | missing-in-agent | <LOCAL_DENYLIST>_vnd_p |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_SCHEMA_NAME | missing-in-agent | accum |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_TABLE_NAME | missing-in-agent | vnd_p_accum_client |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_CONTAINER_NAME | missing-in-agent | syn-container-002 |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_COLUMN_NAMES | missing-in-agent | SEGMENT_IDENTIFIER,FILE_TYPE,DATA_CATEGORY,PROCESS_DATE,PROCESS_TIME,GROUP_ID,FILLER_1,VERSION_RELEASE,CARDHOLDER_ID,PLAN_ID,INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE,FILLER_2,LINE_COUNT,FILLER_3,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_FORMAT | missing-in-agent | delta |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_DATA_TYPE | missing-in-agent | String,String,String,Date,String,String,String,String,String,String,Decimal(17,2),Decimal(18,2),Decimal(19,2),Decimal(20,2),Decimal(21,2),Decimal(22,2),Date,Date,String,String,String,String,TIMESTAMP,TIMESTAMP |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_LOAD_OPTION | missing-in-agent | Append |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_RJT_ADLS_PATH | missing-in-agent | /Pharmacy/<LOCAL_DENYLIST>/Processed/vnd_p_accum_client_reject |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_PARTITION_COLUMN | missing-in-agent | NA |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_PARTITION_VALUE | missing-in-agent | NA |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_PRIMARY_KEY | missing-in-agent | NA |  | feed#0 \| stg_to_std \| A1 \| A42 (golden row 2, agent row -) |
| STGDELTA_STDDELTA_INGESTION_DET | OBJECT_NAME | extra-in-agent |  | A9 | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | DOMAIN | extra-in-agent |  | Pharmacy | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SUBDOMAIN | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SOURCE | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | FREQUENCY | extra-in-agent |  | Daily | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | LOB | extra-in-agent |  |  | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | ACTIVE_FLAG | extra-in-agent |  | Y | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_CONTAINER_NAME | extra-in-agent |  | z-use-d1-dlk-stage-01 | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Processed/<LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_TABLE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_CATALOG_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_SCHEMA_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_FORMAT | extra-in-agent |  | delta | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_COLUMNS | extra-in-agent |  | REC_TYP_HDR:REC_TYP_HDR,FILE_A30_TS:FILE_A30_TS,A18_NM:A18_NM,A31_NM:A31_NM,A32_HDR:A32_HDR,A17:A17,REC_TYP_DTL:REC_TYP_DTL,REC_TS:REC_TS,REC_A33:REC_A33,REC_ID:REC_ID,A18_TYP:A18_TYP,A18_ID:A18_ID,A18_NOTE:A18_NOTE,A18_CLM_A21:A18_CLM_A21,RSN_CD:RSN_CD,A19_DT:A19_DT,AMT_TYP:AMT_TYP,A20_A21_OF_A19:A20_A21_OF_A19,A19_TYP_01:A19_TYP_01,IN_OUT_OF_A22_IND_01:IN_OUT_OF_A22_IND_01,A23_01:A23_01,AMT_01:AMT_01,A34_AMT_IND_01:A34_AMT_IND_01,A35_CD_01:A35_CD_01,A19_TYP_02:A19_TYP_02,IN_OUT_OF_A22_IND_02:IN_OUT_OF_A22_IND_02,A23_02:A23_02,AMT_02:AMT_02,A34_AMT_IND_02:A34_AMT_IND_02,A35_CD_02:A35_CD_02,A19_TYP_03:A19_TYP_03,IN_OUT_OF_A22_IND_03:IN_OUT_OF_A22_IND_03,A23_03:A23_03,AMT_03:AMT_03,A34_AMT_IND_03:A34_AMT_IND_03,A35_CD_03:A35_CD_03,A19_TYP_04:A19_TYP_04,IN_OUT_OF_A22_IND_04:IN_OUT_OF_A22_IND_04,A23_04:A23_04,AMT_04:AMT_04,A34_AMT_IND_04:A34_AMT_IND_04,A35_CD_04:A35_CD_04,A19_TYP_05:A19_TYP_05,IN_OUT_OF_A22_IND_05:IN_OUT_OF_A22_IND_05,A23_05:A23_05,AMT_05:AMT_05,A34_AMT_IND_05:A34_AMT_IND_05,A35_CD_05:A35_CD_05,A19_TYP_06:A19_TYP_06,IN_OUT_OF_A22_IND_06:IN_OUT_OF_A22_IND_06,A23_06:A23_06,AMT_06:AMT_06,A34_AMT_IND_06:A34_AMT_IND_06,A35_CD_06:A35_CD_06,A24_ID:A24_ID,A25_A21:A25_A21,GRP_ID:GRP_ID,MBR_ID:MBR_ID,MBR_A26_NM:MBR_A26_NM,MBR_A36_INIT:MBR_A36_INIT,MBR_A27_NAME:MBR_A27_NAME,MBR_BIRTH_DT:MBR_BIRTH_DT,MBR_A28:MBR_A28,MBR_A37_CD:MBR_A37_CD,SUBSCRIBER_ID:SUBSCRIBER_ID,A29_CD:A29_CD,A32_DTL:A32_DTL,REC_TYP_TRLR:REC_TYP_TRLR,REC_CNT:REC_CNT,A32_TRLR:A32_TRLR,LOB:LOB,SRC_FILE_NAME:SRC_FILE_NAME,REC_CREATION_TIME:REC_CREATION_TIME,REC_UPDATED_TIME:REC_UPDATED_TIME | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_DATA_TYPE | extra-in-agent |  | String:String,String:Timestamp,String:String,String:String,String:String,String:String,String:String,String:Timestamp,String:Integer,String:String,String:String,String:String,String:String,String:String,String:String,String:Date(YYYY-MM-DD),String:String,String:Integer,String:String,String:String,String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:Date(YYYY-MM-DD),String:String,String:String,String:String,String:String,String:String,String:String,String:Integer,String:String,String:String,String:String,Timestamp:Timestamp,Timestamp:Timestamp | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | SRC_ADLS_ARCHVL_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Archive/ | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_CATALOG_NAME | extra-in-agent |  | d1_std | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_SCHEMA_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_TABLE_NAME | extra-in-agent |  | <LOCAL_DENYLIST> | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_CONTAINER_NAME | extra-in-agent |  | z-use-d1-dlk-std-01 | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Processed/ | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_COLUMN_NAMES | extra-in-agent |  | REC_TYP_HDR,FILE_A30_TS,A18_NM,A31_NM,A32_HDR,A17,REC_TYP_DTL,REC_TS,REC_A33,REC_ID,A18_TYP,A18_ID,A18_NOTE,A18_CLM_A21,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A34_AMT_IND_01,A35_CD_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A34_AMT_IND_02,A35_CD_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A34_AMT_IND_03,A35_CD_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A34_AMT_IND_04,A35_CD_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A34_AMT_IND_05,A35_CD_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A34_AMT_IND_06,A35_CD_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A36_INIT,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,MBR_A37_CD,SUBSCRIBER_ID,A29_CD,A32_DTL,REC_TYP_TRLR,REC_CNT,A32_TRLR,LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_FORMAT | extra-in-agent |  | delta | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_DATA_TYPE | extra-in-agent |  | String,Timestamp,String,String,String,String,String,Timestamp,Integer,String,String,String,String,String,String,Date(YYYY-MM-DD),String,Integer,String,String,String,Decimal(10,2),String,String,String,String,String,Decimal(10,2),String,String,String,String,String,Decimal(10,2),String,String,String,String,String,Decimal(10,2),String,String,String,String,String,Decimal(10,2),String,String,String,String,String,Decimal(10,2),String,String,String,String,String,String,String,String,String,Date(YYYY-MM-DD),String,String,String,String,String,String,Integer,String,String,String,Timestamp,Timestamp | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_LOAD_OPTION | extra-in-agent |  | Append | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_RJT_ADLS_PATH | extra-in-agent |  | /Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/Reject/<LOCAL_DENYLIST>_reject | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_PARTITION_COLUMN | extra-in-agent |  | NA | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_PARTITION_VALUE | extra-in-agent |  | NA | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| STGDELTA_STDDELTA_INGESTION_DET | TGT_PRIMARY_KEY | extra-in-agent |  | A24_ID,A25_A21,GRP_ID,MBR_ID | feed#0 \| stg_to_std \| A6 \| A9 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | PROCESS_NAME | missing-in-agent | VND_P_<LOCAL_DENYLIST> |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | VERSION | missing-in-agent | <LOCAL_DENYLIST> |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMNT_TYP | missing-in-agent | SS |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT | missing-in-agent | HDDR |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT_FILTER | missing-in-agent | value like '00%' |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | COL | missing-in-agent | SEGMENT_IDENTIFIER,FILE_TYPE,DATA_CATEGORY,PROCESS_DATE,PROCESS_TIME,GROUP_ID,FILLER_1,VERSION_RELEASE |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | LEN | missing-in-agent | 2,1,1,8,6,10,20,2 |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | start_ind | missing-in-agent | 1,3,4,5,13,19,29,49 |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_TABLE | missing-in-agent | <LOCAL_DENYLIST>_vnd_p.stg_vnd_p_accum.vnd_p_accum_client |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_TYPE | missing-in-agent | .* |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | EXTENSION | missing-in-agent | TXT |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_AUDIT_CLMS | missing-in-agent | SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Archive/Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | IS_MANDATORY | missing-in-agent | N |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | COLUMN_VALIDATIONS | missing-in-agent | NA |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_REJECTION | missing-in-agent |  |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | RJCT_RSN_COLUMN_NM | missing-in-agent |  |  | feed#0 \| A1 \| hddr \| A43 (golden row 2, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | PROCESS_NAME | missing-in-agent | VND_P_<LOCAL_DENYLIST> |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | VERSION | missing-in-agent | <LOCAL_DENYLIST> |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMNT_TYP | missing-in-agent | SS |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT | missing-in-agent | DET |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT_FILTER | missing-in-agent | value like '10%' |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | COL | missing-in-agent | SEGMENT_IDENTIFIER,CARDHOLDER_ID,PLAN_ID,INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE,FILLER_2 |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | LEN | missing-in-agent | 2,15,16,17,18,19,20,21,22,23,24,25 |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | start_ind | missing-in-agent | 1,3,18,34,51,69,88,108,129,151,174,198 |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_TABLE | missing-in-agent | <LOCAL_DENYLIST>_vnd_p.stg_vnd_p_accum.vnd_p_accum_client |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_TYPE | missing-in-agent | .* |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | EXTENSION | missing-in-agent | TXT |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_AUDIT_CLMS | missing-in-agent | SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Archive/Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | IS_MANDATORY | missing-in-agent | N |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | COLUMN_VALIDATIONS | missing-in-agent | NA |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_REJECTION | missing-in-agent |  |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | RJCT_RSN_COLUMN_NM | missing-in-agent |  |  | feed#0 \| A1 \| det \| A44 (golden row 3, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | PROCESS_NAME | missing-in-agent | VND_P_<LOCAL_DENYLIST> |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | VERSION | missing-in-agent | <LOCAL_DENYLIST> |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMNT_TYP | missing-in-agent | SS |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT | missing-in-agent | TRLR |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT_FILTER | missing-in-agent | value like '99%' |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | COL | missing-in-agent | SEGMENT_IDENTIFIER,LINE_COUNT,FILLER_3 |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | LEN | missing-in-agent | 2,10,20 |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | start_ind | missing-in-agent | 1,3,13 |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_TABLE | missing-in-agent | <LOCAL_DENYLIST>_vnd_p.stg_vnd_p_accum.vnd_p_accum_client |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_TYPE | missing-in-agent | .* |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | EXTENSION | missing-in-agent | TXT |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_AUDIT_CLMS | missing-in-agent | SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | SRC_ADLS_ARCHVL_PATH | missing-in-agent | /Archive/Pharmacy/<LOCAL_DENYLIST>/ |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | IS_MANDATORY | missing-in-agent | N |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | COLUMN_VALIDATIONS | missing-in-agent | NA |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_REJECTION | missing-in-agent |  |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | RJCT_RSN_COLUMN_NM | missing-in-agent |  |  | feed#0 \| A1 \| trlr \| A45 (golden row 4, agent row -) |
| ADLS_FIXED_WIDTH_HANDLER | PROCESS_NAME | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | VERSION | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMNT_TYP | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | ACTIVE_FLAG | extra-in-agent |  | Y | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT | extra-in-agent |  | Header | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT_FILTER | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | COL | extra-in-agent |  | REC_TYP_HDR,FILE_A30_TS,A18_NM,A31_NM,A32_HDR | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | LEN | extra-in-agent |  | 1,19,10,10,621 | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | start_ind | extra-in-agent |  | 1,2,21,31,41 | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_TABLE | extra-in-agent |  | <LOCAL_DENYLIST>.<LOCAL_DENYLIST>.<LOCAL_DENYLIST> | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_TYPE | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | EXTENSION | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_AUDIT_CLMS | extra-in-agent |  | LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | SRC_ADLS_ARCHVL_PATH | extra-in-agent |  | /Archive/Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/ | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | IS_MANDATORY | extra-in-agent |  | N | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | COLUMN_VALIDATIONS | extra-in-agent |  | NA | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_REJECTION | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | RJCT_RSN_COLUMN_NM | extra-in-agent |  |  | feed#0 \| A6 \| header \| A46 (golden row -, agent row 2) |
| ADLS_FIXED_WIDTH_HANDLER | PROCESS_NAME | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | VERSION | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMNT_TYP | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | ACTIVE_FLAG | extra-in-agent |  | Y | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT | extra-in-agent |  | Details | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT_FILTER | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | COL | extra-in-agent |  | A17,REC_TYP_DTL,REC_TS,REC_A33,REC_ID,A18_TYP,A18_ID,A18_NOTE,A18_CLM_A21,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A34_AMT_IND_01,A35_CD_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A34_AMT_IND_02,A35_CD_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A34_AMT_IND_03,A35_CD_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A34_AMT_IND_04,A35_CD_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A34_AMT_IND_05,A35_CD_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A34_AMT_IND_06,A35_CD_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A36_INIT,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,MBR_A37_CD,SUBSCRIBER_ID,A29_CD,A32_DTL | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | LEN | extra-in-agent |  | 2,1,26,5,50,1,10,50,50,10,8,1,2,1,1,1,12,1,10,1,1,1,12,1,10,1,1,1,12,1,10,1,1,1,12,1,10,1,1,1,12,1,10,1,1,1,12,1,10,9,15,15,18,15,1,25,8,1,1,18,3,160 | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | start_ind | extra-in-agent |  | 1,3,4,30,35,85,86,96,146,196,206,214,215,217,218,219,220,232,233,243,244,245,246,258,259,269,270,271,272,284,285,295,296,297,298,310,311,321,322,323,324,336,337,347,348,349,350,362,363,373,382,397,412,430,445,446,471,479,480,481,499,502 | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_TABLE | extra-in-agent |  | <LOCAL_DENYLIST>.<LOCAL_DENYLIST>.<LOCAL_DENYLIST> | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_TYPE | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | EXTENSION | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_AUDIT_CLMS | extra-in-agent |  | LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | SRC_ADLS_ARCHVL_PATH | extra-in-agent |  | /Archive/Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/ | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | IS_MANDATORY | extra-in-agent |  | N | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | COLUMN_VALIDATIONS | extra-in-agent |  | NA | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_REJECTION | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | RJCT_RSN_COLUMN_NM | extra-in-agent |  |  | feed#0 \| A6 \| details \| A47 (golden row -, agent row 3) |
| ADLS_FIXED_WIDTH_HANDLER | PROCESS_NAME | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | VERSION | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMNT_TYP | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | ACTIVE_FLAG | extra-in-agent |  | Y | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT | extra-in-agent |  | Trailer | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | SEGMENT_FILTER | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | COL | extra-in-agent |  | REC_TYP_TRLR,REC_CNT,A32_TRLR | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | LEN | extra-in-agent |  | 1,7,653 | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | start_ind | extra-in-agent |  | 1,2,9 | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_TABLE | extra-in-agent |  | <LOCAL_DENYLIST>.<LOCAL_DENYLIST>.<LOCAL_DENYLIST> | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_TYPE | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | EXTENSION | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | TGT_AUDIT_CLMS | extra-in-agent |  | LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | SRC_ADLS_ARCHVL_PATH | extra-in-agent |  | /Archive/Path : <CLIENT_STORAGE_PREFIX>/mftlanding/inbound/pharmacy/<LOCAL_DENYLIST>/<LOCAL_DENYLIST>/<File.A10>/ | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | IS_MANDATORY | extra-in-agent |  | N | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | COLUMN_VALIDATIONS | extra-in-agent |  | NA | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | FILE_REJECTION | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| ADLS_FIXED_WIDTH_HANDLER | RJCT_RSN_COLUMN_NM | extra-in-agent |  |  | feed#0 \| A6 \| trailer \| A48 (golden row -, agent row 4) |
| DATABRICKS_NOTEBOOK_DETAILS | PROCESS_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST>  Raw to stage load | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | TGT_REFRESH_TYPE | mismatch | Overwrite | Append | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_WORKSPACE_URL | missing-in-agent | https://syn-dbx-workspace-001.synthetic.example/ |  | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_WORKSPACE_SECRET | missing-in-agent | SYN-SECRET-001 |  | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_CLUSTERID | missing-in-agent | SYN-CLUSTER-001 |  | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_NOTEBOOK_PATH | mismatch | /Workspace/VND_P/REPORTS/Daily_Ingested_Status_Report_V2 | /Workspace/iig/FileInvokeDQDeltaTable_V0.1 | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | CLUSTER_DETAILS_ID | missing-in-agent | SYN-CLUSTER-002 |  | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | DQ_NOTEBOOK_PATH | missing-in-agent | /Workspace/VND_P/VND_P_IIG/NB_VND_P_FXD_WDTH_SEG_HNDLR_V2 |  | feed#0 (golden row 2, agent row 2) |
| DATABRICKS_NOTEBOOK_DETAILS | PROCESS_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST>  stage to std load | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | TGT_REFRESH_TYPE | mismatch | Overwrite | Append | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_WORKSPACE_URL | missing-in-agent | https://syn-dbx-workspace-001.synthetic.example/ |  | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_WORKSPACE_SECRET | missing-in-agent | SYN-SECRET-001 |  | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_CLUSTERID | missing-in-agent | SYN-CLUSTER-001 |  | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_NOTEBOOK_PATH | mismatch | /Workspace/VND_P/VND_P_IIG/FileInvokeDQDeltaTable_V1 | /Workspace/iig/DeltaInvokeDQStandardDeltaTable_V4 | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | CLUSTER_DETAILS_ID | missing-in-agent | SYN-CLUSTER-002 |  | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | DQ_NOTEBOOK_PATH | missing-in-agent | /Workspace/VND_P/VND_P_IIG/NB_VND_P_FXD_WDTH_SEG_HNDLR |  | feed#0 (golden row 3, agent row 3) |
| DATABRICKS_NOTEBOOK_DETAILS | SEQ_NM | missing-in-agent | 1 |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | PROCESS_NAME | missing-in-agent | VND_P_<LOCAL_DENYLIST> |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | TGT_REFRESH_TYPE | missing-in-agent | Append |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | ACTIVE_FLAG | missing-in-agent | Y |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_WORKSPACE_URL | missing-in-agent | https://syn-dbx-workspace-001.synthetic.example/ |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_WORKSPACE_SECRET | missing-in-agent | SYN-SECRET-001 |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_CLUSTERID | missing-in-agent | SYN-CLUSTER-001 |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | DATABRICKS_NOTEBOOK_PATH | missing-in-agent | /Workspace/VND_P/VND_P_IIG/DeltaInvokeDQStandardDeltaTable_V2 |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | CLUSTER_DETAILS_ID | missing-in-agent | SYN-CLUSTER-002 |  | feed#0 (golden row 4, agent row -) |
| DATABRICKS_NOTEBOOK_DETAILS | DQ_NOTEBOOK_PATH | missing-in-agent | NA |  | feed#0 (golden row 4, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 1 |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 2, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 2, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DateFormatRule |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 2, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 2, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 2, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | yyyyMMdd--yyyy-MM-dd |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 2, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 2, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 2 |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 3, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 3, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DataTypeCastRule |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 3, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 3, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 3, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | <LOCAL_DENYLIST>_vnd_p.stg_vnd_p_accum.vnd_p_accum_client |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 3, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 3, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 1 |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 4, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 4, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DateFormatRule |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 4, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 4, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 4, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | yyyyMMdd--yyyy-MM-dd |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 4, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 4, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 2 |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 5, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 5, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DataTypeCastRule |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 5, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 5, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 5, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | <LOCAL_DENYLIST>_vnd_p.stg_vnd_p_accum.vnd_p_accum_client |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 5, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 5, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 1 |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 6, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 6, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DateFormatRule |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 6, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 6, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 6, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | yyyyMMdd--yyyy-MM-dd |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 6, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 6, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 2 |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 7, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 7, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DataTypeCastRule |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 7, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 7, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 7, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | <LOCAL_DENYLIST>_vnd_p.stg_vnd_p_accum.vnd_p_accum_client |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 7, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 7, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 1 |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 8, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 8, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DateFormatRule |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 8, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 8, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 8, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | yyyyMMdd--yyyy-MM-dd |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 8, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A49 \| dateformatrule (golden row 8, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | missing-in-agent | 2 |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 9, agent row -) |
| DATA_QUALITY_RULES | RULE_TYPE | missing-in-agent | Custom |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 9, agent row -) |
| DATA_QUALITY_RULES | RULE_CLASS | missing-in-agent | DataTypeCastRule |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 9, agent row -) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | missing-in-agent | Y |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 9, agent row -) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 9, agent row -) |
| DATA_QUALITY_RULES | INPUT_PARAM | missing-in-agent | <LOCAL_DENYLIST>_vnd_p.stg_vnd_p_accum.vnd_p_accum_client |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 9, agent row -) |
| DATA_QUALITY_RULES | TARGET_COLUMN | missing-in-agent | INDIVIDUAL_DEDUCTIBLE,FAMILY_DEDUCTIBLE,COPAY,COINSURANCE,INDIVIDUAL_LIMIT,FAMILY_LIMIT,PROCESS_DATE,PLAN_YEAR_START_DATE,PLAN_YEAR_END_DATE |  | feed#0 \| A1 \| A50 \| datatypecastrule (golden row 9, agent row -) |
| DATA_QUALITY_RULES | SEQUENCE_NO | extra-in-agent |  | 1 | feed#0 \| A6 \| A51 \| A52 (golden row -, agent row 2) |
| DATA_QUALITY_RULES | RULE_TYPE | extra-in-agent |  | Predefined | feed#0 \| A6 \| A51 \| A52 (golden row -, agent row 2) |
| DATA_QUALITY_RULES | RULE_CLASS | extra-in-agent |  | A52 | feed#0 \| A6 \| A51 \| A52 (golden row -, agent row 2) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | extra-in-agent |  | Y | feed#0 \| A6 \| A51 \| A52 (golden row -, agent row 2) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | extra-in-agent |  | A17,REC_TYP_DTL,A18_TYP,A18_ID,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,A29_CD | feed#0 \| A6 \| A51 \| A52 (golden row -, agent row 2) |
| DATA_QUALITY_RULES | INPUT_PARAM | extra-in-agent |  | <LOCAL_DENYLIST>.<LOCAL_DENYLIST>.<LOCAL_DENYLIST> | feed#0 \| A6 \| A51 \| A52 (golden row -, agent row 2) |
| DATA_QUALITY_RULES | TARGET_COLUMN | extra-in-agent |  | A17,REC_TYP_DTL,A18_TYP,A18_ID,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,A29_CD | feed#0 \| A6 \| A51 \| A52 (golden row -, agent row 2) |
| DATA_QUALITY_RULES | SEQUENCE_NO | extra-in-agent |  | 2 | feed#0 \| A6 \| A51 \| A53 (golden row -, agent row 3) |
| DATA_QUALITY_RULES | RULE_TYPE | extra-in-agent |  | Predefined | feed#0 \| A6 \| A51 \| A53 (golden row -, agent row 3) |
| DATA_QUALITY_RULES | RULE_CLASS | extra-in-agent |  | A53 | feed#0 \| A6 \| A51 \| A53 (golden row -, agent row 3) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | extra-in-agent |  | Y | feed#0 \| A6 \| A51 \| A53 (golden row -, agent row 3) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | extra-in-agent |  | A17,REC_TYP_DTL,A18_TYP,A18_ID,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,A29_CD | feed#0 \| A6 \| A51 \| A53 (golden row -, agent row 3) |
| DATA_QUALITY_RULES | INPUT_PARAM | extra-in-agent |  | <LOCAL_DENYLIST>.<LOCAL_DENYLIST>.<LOCAL_DENYLIST> | feed#0 \| A6 \| A51 \| A53 (golden row -, agent row 3) |
| DATA_QUALITY_RULES | TARGET_COLUMN | extra-in-agent |  | A17,REC_TYP_DTL,A18_TYP,A18_ID,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,A29_CD | feed#0 \| A6 \| A51 \| A53 (golden row -, agent row 3) |
| DATA_QUALITY_RULES | SEQUENCE_NO | extra-in-agent |  | 1 | feed#0 \| <none> \| A54 \| lrtrimrule (golden row -, agent row 4) |
| DATA_QUALITY_RULES | RULE_TYPE | extra-in-agent |  | STDDelta | feed#0 \| <none> \| A54 \| lrtrimrule (golden row -, agent row 4) |
| DATA_QUALITY_RULES | RULE_CLASS | extra-in-agent |  | LRTrimRule | feed#0 \| <none> \| A54 \| lrtrimrule (golden row -, agent row 4) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | extra-in-agent |  | Y | feed#0 \| <none> \| A54 \| lrtrimrule (golden row -, agent row 4) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | extra-in-agent |  | REC_TYP_HDR,FILE_A30_TS,A18_NM,A31_NM,A32_HDR,A17,REC_TYP_DTL,REC_TS,REC_A33,REC_ID,A18_TYP,A18_ID,A18_NOTE,A18_CLM_A21,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A34_AMT_IND_01,A35_CD_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A34_AMT_IND_02,A35_CD_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A34_AMT_IND_03,A35_CD_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A34_AMT_IND_04,A35_CD_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A34_AMT_IND_05,A35_CD_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A34_AMT_IND_06,A35_CD_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A36_INIT,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,MBR_A37_CD,SUBSCRIBER_ID,A29_CD,A32_DTL,REC_TYP_TRLR,REC_CNT,A32_TRLR | feed#0 \| <none> \| A54 \| lrtrimrule (golden row -, agent row 4) |
| DATA_QUALITY_RULES | INPUT_PARAM | extra-in-agent |  |  | feed#0 \| <none> \| A54 \| lrtrimrule (golden row -, agent row 4) |
| DATA_QUALITY_RULES | TARGET_COLUMN | extra-in-agent |  | REC_TYP_HDR,FILE_A30_TS,A18_NM,A31_NM,A32_HDR,A17,REC_TYP_DTL,REC_TS,REC_A33,REC_ID,A18_TYP,A18_ID,A18_NOTE,A18_CLM_A21,RSN_CD,A19_DT,AMT_TYP,A20_A21_OF_A19,A19_TYP_01,IN_OUT_OF_A22_IND_01,A23_01,AMT_01,A34_AMT_IND_01,A35_CD_01,A19_TYP_02,IN_OUT_OF_A22_IND_02,A23_02,AMT_02,A34_AMT_IND_02,A35_CD_02,A19_TYP_03,IN_OUT_OF_A22_IND_03,A23_03,AMT_03,A34_AMT_IND_03,A35_CD_03,A19_TYP_04,IN_OUT_OF_A22_IND_04,A23_04,AMT_04,A34_AMT_IND_04,A35_CD_04,A19_TYP_05,IN_OUT_OF_A22_IND_05,A23_05,AMT_05,A34_AMT_IND_05,A35_CD_05,A19_TYP_06,IN_OUT_OF_A22_IND_06,A23_06,AMT_06,A34_AMT_IND_06,A35_CD_06,A24_ID,A25_A21,GRP_ID,MBR_ID,MBR_A26_NM,MBR_A36_INIT,MBR_A27_NAME,MBR_BIRTH_DT,MBR_A28,MBR_A37_CD,SUBSCRIBER_ID,A29_CD,A32_DTL,REC_TYP_TRLR,REC_CNT,A32_TRLR | feed#0 \| <none> \| A54 \| lrtrimrule (golden row -, agent row 4) |
| DATA_QUALITY_RULES | SEQUENCE_NO | extra-in-agent |  | 2 | feed#0 \| <none> \| A55 \| dateconversionrule (golden row -, agent row 5) |
| DATA_QUALITY_RULES | RULE_TYPE | extra-in-agent |  | STDDelta | feed#0 \| <none> \| A55 \| dateconversionrule (golden row -, agent row 5) |
| DATA_QUALITY_RULES | RULE_CLASS | extra-in-agent |  | DateConversionRule | feed#0 \| <none> \| A55 \| dateconversionrule (golden row -, agent row 5) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | extra-in-agent |  | Y | feed#0 \| <none> \| A55 \| dateconversionrule (golden row -, agent row 5) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | extra-in-agent |  | A19_DT | feed#0 \| <none> \| A55 \| dateconversionrule (golden row -, agent row 5) |
| DATA_QUALITY_RULES | INPUT_PARAM | extra-in-agent |  |  | feed#0 \| <none> \| A55 \| dateconversionrule (golden row -, agent row 5) |
| DATA_QUALITY_RULES | TARGET_COLUMN | extra-in-agent |  | A19_DT | feed#0 \| <none> \| A55 \| dateconversionrule (golden row -, agent row 5) |
| DATA_QUALITY_RULES | SEQUENCE_NO | extra-in-agent |  | 3 | feed#0 \| <none> \| A56 \| dateconversionrule (golden row -, agent row 6) |
| DATA_QUALITY_RULES | RULE_TYPE | extra-in-agent |  | STDDelta | feed#0 \| <none> \| A56 \| dateconversionrule (golden row -, agent row 6) |
| DATA_QUALITY_RULES | RULE_CLASS | extra-in-agent |  | DateConversionRule | feed#0 \| <none> \| A56 \| dateconversionrule (golden row -, agent row 6) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | extra-in-agent |  | Y | feed#0 \| <none> \| A56 \| dateconversionrule (golden row -, agent row 6) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | extra-in-agent |  | MBR_BIRTH_DT | feed#0 \| <none> \| A56 \| dateconversionrule (golden row -, agent row 6) |
| DATA_QUALITY_RULES | INPUT_PARAM | extra-in-agent |  |  | feed#0 \| <none> \| A56 \| dateconversionrule (golden row -, agent row 6) |
| DATA_QUALITY_RULES | TARGET_COLUMN | extra-in-agent |  | MBR_BIRTH_DT | feed#0 \| <none> \| A56 \| dateconversionrule (golden row -, agent row 6) |
| DATA_QUALITY_RULES | SEQUENCE_NO | extra-in-agent |  | 4 | feed#0 \| <none> \| A57 \| datatypecastrule (golden row -, agent row 7) |
| DATA_QUALITY_RULES | RULE_TYPE | extra-in-agent |  | STDDelta | feed#0 \| <none> \| A57 \| datatypecastrule (golden row -, agent row 7) |
| DATA_QUALITY_RULES | RULE_CLASS | extra-in-agent |  | DataTypeCastRule | feed#0 \| <none> \| A57 \| datatypecastrule (golden row -, agent row 7) |
| DATA_QUALITY_RULES | ACTIVE_RULE_FLG | extra-in-agent |  | Y | feed#0 \| <none> \| A57 \| datatypecastrule (golden row -, agent row 7) |
| DATA_QUALITY_RULES | SOURCE_COLUMN | extra-in-agent |  | AMT_01,AMT_02,AMT_03,AMT_04,AMT_05,AMT_06,A19_DT,MBR_BIRTH_DT,FILE_A30_TS,REC_TS,REC_A33,A20_A21_OF_A19,REC_CNT | feed#0 \| <none> \| A57 \| datatypecastrule (golden row -, agent row 7) |
| DATA_QUALITY_RULES | INPUT_PARAM | extra-in-agent |  | d1_std.<LOCAL_DENYLIST>.<LOCAL_DENYLIST> | feed#0 \| <none> \| A57 \| datatypecastrule (golden row -, agent row 7) |
| DATA_QUALITY_RULES | TARGET_COLUMN | extra-in-agent |  | AMT_01,AMT_02,AMT_03,AMT_04,AMT_05,AMT_06,A19_DT,MBR_BIRTH_DT,FILE_A30_TS,REC_TS,REC_A33,A20_A21_OF_A19,REC_CNT | feed#0 \| <none> \| A57 \| datatypecastrule (golden row -, agent row 7) |
| EMAIL_TEMPLATE_CONFIG | TEMPLATE_ID | missing-in-agent | SYN-TMPL-001 |  | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | PROCESS_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST> | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | SUBJECT | mismatch | <Vendor>- Pharmacy <LOCAL_DENYLIST> File Load Status: | <LOCAL_DENYLIST> Daily Load Completed - | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | BODY | mismatch | VND_P_Pharmacy <LOCAL_DENYLIST> load completed. Please find the details for individuals files below : | <LOCAL_DENYLIST> Daily Data Load Successful | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | BODY_QUERY | missing-in-agent | SELECT FILE_NAME,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN 'NA' ELSE SRC_REC_COUNT END AS SRC_REC_COUNT,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN 'NA' ELSE TGT_REC_COUNT END AS TGT_REC_COUNT,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN 'NA' ELSE REJECTED_REC_COUNT END AS REJECTED_REC_COUNT,<br>     EXEC_STATUS, ERROR_MESSAGE, BATCH_DATE,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN nvl(LAST_SUCCESS_PROCESSED_DATE,'NA') ELSE 'NA' END AS LAST_FILE_PROCESSED_DATE<br>     FROM FILE_MONITORING.DIALY_INGESTED_FILE_STATUS<br>     WHERE APPLICATION_NAME='VND_P_REBATES' AND BATCH_DATE=current_date()<br>     AND ((FILE_RECEIVE_PER_FREQUENCY IS NULL OR (FILE_RECEIVE_PER_FREQUENCY='FALSE' AND EXEC_STATUS = 'NO NEW FILES TO PROCESS'))<br>     OR (EXEC_STATUS != 'NO NEW FILES TO PROCESS')) |  | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | SENDER_NAME | mismatch | vnd_p | dbo | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | SENDER_EMAIL | missing-in-agent | syn.person.001@synthetic.example |  | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | EMAIL_TO | missing-in-agent | syn.person.002@synthetic.example |  | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | EMAIL_NOTIFICATION_URL | extra-in-agent |  |  | feed#0 \| success (golden row 2, agent row 4) |
| EMAIL_TEMPLATE_CONFIG | TEMPLATE_ID | missing-in-agent | SYN-TMPL-002 |  | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | PROCESS_NAME | mismatch | VND_P_<LOCAL_DENYLIST> | <LOCAL_DENYLIST> | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | SUBJECT | mismatch | Pipeline Failed to process the Pharmacy <LOCAL_DENYLIST> Files | <LOCAL_DENYLIST> Daily Load  Failed - | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | BODY | mismatch | <Vendor>- Pharmacy <LOCAL_DENYLIST> File Load Status: | <LOCAL_DENYLIST> Daily Data Load Failed | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | BODY_QUERY | missing-in-agent | SELECT FILE_NAME,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN 'NA' ELSE SRC_REC_COUNT END AS SRC_REC_COUNT,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN 'NA' ELSE TGT_REC_COUNT END AS TGT_REC_COUNT,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN 'NA' ELSE REJECTED_REC_COUNT END AS REJECTED_REC_COUNT,<br>     EXEC_STATUS, ERROR_MESSAGE, BATCH_DATE,<br>     CASE WHEN EXEC_STATUS = 'NO NEW FILES TO PROCESS' THEN nvl(LAST_SUCCESS_PROCESSED_DATE,'NA') ELSE 'NA' END AS LAST_FILE_PROCESSED_DATE<br>     FROM FILE_MONITORING.DIALY_INGESTED_FILE_STATUS<br>     WHERE APPLICATION_NAME='VND_P_REBATES' AND BATCH_DATE=current_date()<br>     AND ((FILE_RECEIVE_PER_FREQUENCY IS NULL OR (FILE_RECEIVE_PER_FREQUENCY='FALSE' AND EXEC_STATUS = 'NO NEW FILES TO PROCESS'))<br>     OR (EXEC_STATUS != 'NO NEW FILES TO PROCESS')) |  | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | SENDER_NAME | mismatch | vnd_p | dbo | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | SENDER_EMAIL | missing-in-agent | syn.person.001@synthetic.example |  | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | EMAIL_TO | missing-in-agent | syn.person.003@synthetic.example |  | feed#0 \| failed (golden row 3, agent row 5) |
| EMAIL_TEMPLATE_CONFIG | EMAIL_NOTIFICATION_URL | extra-in-agent |  |  | feed#0 \| failed (golden row 3, agent row 5) |
