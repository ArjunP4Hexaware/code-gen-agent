# IIG corpus patterns - scrubbed (placeholders only)

Slot placeholders: {feed} {table} {schema} {catalog} {domain} {subdomain} {file} {source} - the row's own workbook's values (ADLS / STGDELTA / FILE_ADLS / fixed-width sheets). G<n>: a token outside the fixture vocabulary.

- corpus workbooks: 1255
- DATABRICKS_NOTEBOOK_DETAILS: in 378 workbook(s), 378 row(s)
- DATA_FACTORY_PIPELINE_SCHEDULE: in 398 workbook(s), 35658 row(s)
- EMAIL_TEMPLATE_CONFIG: in 1 workbook(s), 13468 row(s)

## Sheet sets (workbooks with each set)

- 199 x [all_files_static_information]
- 199 x [data_factory_pipeline_schedule]
- 189 x [databricks_notebook_details]
- 129 x [adls_delta_ingestion_details]
- 79 x [adls_fixed_width_handler]
- 75 x [data_quality_rules]
- 71 x [data_A1_details]
- 65 x [adls_delta_ingestion_details, adls_fixed_width_handler, all_files_static_information, data_A1_details, data_factory_pipeline_schedule, databricks_notebook_details]
- 65 x [stgdelta_stddelta_ingestion_details]
- 50 x [all_files_static_information, data_factory_pipeline_schedule, data_quality_rules, databricks_notebook_details, stgdelta_stddelta_ingestion_det]
- 37 x [adls_delta_ingestion_details, all_files_static_information, data_factory_pipeline_schedule, databricks_notebook_details]
- 29 x [data_factory_pipeline_exec_log]
- 13 x [file_log_information]
- 9 x [all_files_static_information, data_factory_pipeline_exec_log, data_factory_pipeline_schedule, data_quality_rules, databricks_notebook_details, stgdelta_stddelta_ingestion_det]
- 5 x [adls_delta_ingestion_details, all_files_static_information, data_factory_pipeline_exec_log, data_factory_pipeline_schedule, data_quality_rules, databricks_notebook_details, file_log_information]
- 5 x [all_files_static_information, data_factory_pipeline_exec_log, data_factory_pipeline_schedule, file_adls_ingestion_details]
- 5 x [adls_delta_ingestion_details, all_files_static_information, data_A1_details, data_factory_pipeline_exec_log, data_factory_pipeline_schedule]
- 5 x [file_adls_ingestion_details]
- 4 x [adls_delta_ingestion_details, all_files_static_information, data_factory_pipeline_exec_log, data_factory_pipeline_schedule, data_quality_rules, databricks_notebook_details]
- 4 x [adls_fixed_width_handler, all_files_static_information, data_factory_pipeline_schedule, data_quality_rules, databricks_notebook_details, stgdelta_stddelta_ingestion_det]
- 3 x [adls_delta_ingestion_details, adls_fixed_width_handler, all_files_static_information, data_factory_pipeline_schedule, databricks_notebook_details]
- 3 x [adls_delta_ingestion_details, adls_fixed_width_handler, all_files_static_information, data_factory_pipeline_schedule, databricks_notebook_details, file_log_information]
- 3 x [adls_delta_ingestion_details, all_files_static_information, data_factory_pipeline_schedule, databricks_notebook_details, file_log_information]
- 2 x [adls_delta_ingestion_details, adls_fixed_width_handler, all_files_static_information, data_factory_pipeline_schedule, data_quality_rules, databricks_notebook_details, file_log_information]
- 2 x [adls_fixed_width_handler, all_files_static_information, data_factory_pipeline_schedule, databricks_notebook_details, stgdelta_stddelta_ingestion_det]
- 1 x [adls_delta_ingestion_details, all_files_static_information, data_factory_pipeline_exec_log, data_factory_pipeline_schedule, databricks_notebook_details]
- 1 x [adls_delta_ingestion_details, all_files_static_information, data_A1_details, data_factory_pipeline_schedule, data_quality_rules, databricks_notebook_details]
- 1 x [00_table_set]
- 1 x [01_pair_group_index]
- 1 x [email_template_config_by_pipeline]

## DATABRICKS_NOTEBOOK_DETAILS (378 corpus rows)

| column | filled % | dominant value | share % | dominant pattern | share % | patterns | per-feed |
|---|---|---|---|---|---|---|---|
| PIPELINE_ID | 100.0 | withheld (assigned / withheld column) | | | | | |
| PIPELINE_NAME | 100.0 | G1_G2 stage to std load | 3.2 | Pl_File_G16_{table}_Regular_ADLS_To_Delta_Incr | 19.6 | 168 | yes |
| GROUP_ID | 100.0 | withheld (assigned / withheld column) | | | | | |
| SEQ_NM | 100.0 | 1 | 64.6 | 1 | 64.6 | 62 |  |
| PROCESS_NAME | 100.0 | G1  Raw to stage load | 19.6 | G1  Raw to stage load | 19.6 | 101 |  |
| TGT_REFRESH_TYPE | 100.0 | Overwrite | 62.4 | Overwrite | 62.4 | 6 |  |
| ACTIVE_FLAG | 100.0 | Y | 98.9 | Y | 98.9 | 2 |  |
| DATABRICKS_WORKSPACE_URL | 100.0 | withheld (assigned / withheld column) | | | | | |
| DATABRICKS_WORKSPACE_SECRET | 100.0 | withheld (assigned / withheld column) | | | | | |
| DATABRICKS_CLUSTERID | 97.4 | withheld (assigned / withheld column) | | | | | |
| DATABRICKS_NOTEBOOK_PATH | 100.0 | /iig/DeltaInvokeDQStandardDeltaTable_V4 | 26.5 | /iig/DeltaInvokeDQStandardDeltaTable_V4 | 26.5 | 16 |  |
| DATABRICKS_NOTEBOOK_NAME | 100.0 | DeltaInvokeDQStandardDeltaTable_V4 | 29.6 | DeltaInvokeDQStandardDeltaTable_V4 | 29.6 | 12 |  |
| CREATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| CREATED_DATE | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_DATE | 100.0 | withheld (assigned / withheld column) | | | | | |
| CLUSTER_DETAILS_ID | 62.4 | withheld (assigned / withheld column) | | | | | |
| DELETE_DATABRICKS_NOTEBOOK_NAME | 0.0 |  | - |  | - | 0 |  |
| DQ_NOTEBOOK_PATH | 0.0 |  | - |  | - | 0 |  |

## DATA_FACTORY_PIPELINE_SCHEDULE (35658 corpus rows)

| column | filled % | dominant value | share % | dominant pattern | share % | patterns | per-feed |
|---|---|---|---|---|---|---|---|
| PIPELINE_ID | 100.0 | withheld (assigned / withheld column) | | | | | |
| PIPELINE_NAME | 100.0 | PL_File_STAGE_G60_G61_extract | 0.5 | Pl_File_G16_{table}_Regular_ADLS_To_Delta_Incr | 17.2 | 303 | yes |
| PARENT_PIPELINE_ID | 92.1 | withheld (assigned / withheld column) | | | | | |
| PIPELINE_DESCRIPTION | 100.0 | G1 Stage Load | 18.9 | G1 Stage Load | 18.9 | 387 |  |
| PIPELINE_FREQUENCY | 100.0 | Daily | 68.5 | Daily | 68.5 | 7 |  |
| NO_OF_CYCLE_PER_DAY | 100.0 | 1 | 98.2 | 1 | 98.2 | 2 |  |
| DAY_OF_SCHEDULE | 3.5 | 0 | 54.8 | 0 | 54.8 | 3 |  |
| ACTIVE_FLAG | 100.0 | Y | 97.5 | Y | 97.5 | 2 |  |
| ACTIVE_START_DATE | 100.0 | 2025-12-20 00:00:00 | 19.4 | 2025-12-20 00:00:00 | 19.4 | 44 |  |
| ACTIVE_END_DATE | 100.0 | 9999-12-31 00:00:00 | 50.0 | 9999-12-31 00:00:00 | 50.0 | 2 |  |
| ESTIMATED_START_TIME | 0.0 |  | - |  | - | 0 |  |
| APPLICATION_NAME | 100.0 | G1 | 38.8 | G1 | 38.8 | 25 |  |
| CREATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| CREATED_DATE | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_DATE | 100.0 | withheld (assigned / withheld column) | | | | | |
| PROCESS_NAME | 60.9 | G16 834 G22 | 59.0 | G16 834 G22 | 56.0 | 31 |  |
| SUBPROCESS_NAME | 53.8 | G2 | 7.6 | G72 LAYOUT | 6.6 | 50 |  |
| LAYER_NAME | 38.4 | STAGE | 88.7 | STAGE | 88.7 | 6 |  |
| COMPLETION_SLA | 0.0 |  | - |  | - | 0 |  |
| RUNTIME_SLA | 0.0 | 6 | 100.0 | 6 | 100.0 | 1 |  |
| CRITICAL_PROCESSING_PERIOD | 0.0 |  | - |  | - | 0 |  |
| UDF1 | 0.0 |  | - |  | - | 0 |  |
| UDF2 | 0.0 |  | - |  | - | 0 |  |
| UDF3 | 0.0 |  | - |  | - | 0 |  |
| UDF4 | 0.0 |  | - |  | - | 0 |  |
| UDF5 | 0.0 |  | - |  | - | 0 |  |
| IsFileCopyReqFlag | 4.4 | N | 88.5 | N | 88.5 | 2 |  |

## EMAIL_TEMPLATE_CONFIG (13468 corpus rows)

| column | filled % | dominant value | share % | dominant pattern | share % | patterns | per-feed |
|---|---|---|---|---|---|---|---|
| PIPELINE_ID | 100.0 | withheld (assigned / withheld column) | | | | | |
| PIPELINE_NAME | 100.0 | PL_Gmstr_G97_Historical_Load | 7.3 | PL_Gmstr_G97_Historical_Load | 7.3 | 1365 |  |
| TEMPLATE_ID | 100.0 | withheld (assigned / withheld column) | | | | | |
| TEMPLATE_NAME | 19.8 | G544 G545 | 26.1 | G544 G545 | 26.1 | 52 |  |
| PROCESS_NAME | 19.8 | G544 G545 | 26.1 | G544 G545 | 26.1 | 56 |  |
| STATUS | 19.8 | Success | 23.1 | Success | 23.1 | 16 |  |
| ACTIVE_FLAG | 19.8 | Y | 100.0 | Y | 100.0 | 1 |  |
| SUBJECT | 19.8 | G135 G499 G555 Daily File Not Received - | 3.4 | G135 G499 G555 Daily File Not Received - | 3.4 | 170 |  |
| BODY | 19.8 | The G564 files have not been received for the CM Automation. G565 review and take the necessary G566. | 21.7 | The G564 files have not been received for the CM Automation. G565 review and take the necessary G566. | 21.7 | 164 |  |
| SENDER_NAME | 19.8 | dbo | 97.8 | dbo | 97.8 | 2 |  |
| SENDER_EMAIL | 19.8 | G571@<LOCAL_DENYLIST>.G572 | 97.7 | G571@<LOCAL_DENYLIST>.G572 | 97.7 | 5 |  |
| EMAIL_TO | 19.8 | G576@<LOCAL_DENYLIST>.G572 | 47.6 | G576@<LOCAL_DENYLIST>.G572 | 47.6 | 24 |  |
| EMAIL_CC | 18.8 | G605@<LOCAL_DENYLIST>.G572,G606@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G610@<LOCAL_DENYLIST>.G572,G611@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572 | 26.7 | G605@<LOCAL_DENYLIST>.G572,G606@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G610@<LOCAL_DENYLIST>.G572,G611@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572 | 26.7 | 27 |  |
| CRETAED_BY | 19.8 | withheld (assigned / withheld column) | | | | | |
| CREATED_AT | 19.8 | 2025-12-18 12:30:00 | 25.3 | 2025-12-18 12:30:00 | 25.3 | 36 |  |
| UPDATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_AT | 100.0 | 2026-07-02 15:34:17 | 24.1 | 2026-07-02 15:34:17 | 24.1 | 39 |  |
| EMAIL_NOTIFICATION_URL | 100.0 | https://<REAL_WEBHOOK_HOST>:443/api/LOG_EMAIL_WITH_G635/G636/When_an_G637_request_is_received/G638?api-version=2022-05-01&sp=%G639%G640_an_G637_request_is_received%G641&sv=1.0&G642=G643-G644 | 95.4 | https://<REAL_WEBHOOK_HOST>:443/api/LOG_EMAIL_WITH_G635/G636/When_an_G637_request_is_received/G638?api-version=2022-05-01&sp=%G639%G640_an_G637_request_is_received%G641&sv=1.0&G642=G643-G644 | 95.4 | 3 |  |

## DAY_OF_SCHEDULE by PIPELINE_FREQUENCY (DATA_FACTORY_PIPELINE_SCHEDULE)

| frequency | rows | DAY filled | filled % | dominant DAY | share % |
|---|---|---|---|---|---|
| Daily | 24410 | 0 | 0.0 |  | - |
| Monthly | 8200 | 32 | 0.4 | 5 | 0.2 |
| Weekly | 1592 | 474 | 29.8 | 0 | 14.9 |
| WEEKLY | 1178 | 632 | 53.7 | 0 | 26.8 |
| G21 | 158 | 0 | 0.0 |  | - |
| MONTHLY | 96 | 96 | 100.0 | 0 | 100.0 |
| DAILY | 24 | 24 | 100.0 | 0 | 100.0 |

## DATA_QUALITY_RULES rule classes (RULE_TYPE x RULE_CLASS)

- workbooks with the sheet: 150 of 1255

| RULE_TYPE | RULE_CLASS | rows | workbooks |
|---|---|---|---|
| Predefined | NullCheckRule | 186 | 114 |
| STDDelta | LRTrimRule | 180 | 104 |
| Predefined | DeDuplicationRule | 160 | 90 |
| Custom | ReferentialCheckRule | 52 | 16 |
| Predefined | AddCustomColumnsRule | 38 | 4 |
| Predefined | LoadHeaderAndTrailerToSeparateTablesRule | 36 | 2 |
| STDDelta | DateConversionRule | 34 | 26 |
| STDDelta | DataTypeCastRule | 32 | 28 |
| STDDelta | DateFormatRule | 16 | 10 |
| Predefined | DeDuplicationRankRule | 10 | 8 |
| Custom | DateFormatRule | 10 | 10 |
| STGDelta | AddColumnsRule | 8 | 4 |
| STDDelta | DataTypeConversionRule | 8 | 6 |
| STDDelta | removeExistingFileDupes | 8 | 8 |
| STGDelta | ReferentialCheckRule | 6 | 2 |
| STDDelta | NullCheckRule | 6 | 2 |
| STDDelta | DecimalTypeRule | 4 | 4 |
| Custom | DataTypeConversionRule | 4 | 4 |
| Custom | DataTypeCastRule | 4 | 4 |
| Predefined | ReplaceCharacterRule | 2 | 2 |
| STDDelta | DataTypeConversionRule_NEW | 2 | 2 |

## Framework vocabulary (passed through unscrubbed)

- columns: {'DATABRICKS_NOTEBOOK_DETAILS': ['DATABRICKS_NOTEBOOK_NAME', 'DELETE_DATABRICKS_NOTEBOOK_NAME'], 'DATA_QUALITY_RULES': ['RULE_TYPE', 'RULE_CLASS'], 'EMAIL_TEMPLATE_CONFIG': ['STATUS'], 'DATA_FACTORY_PIPELINE_SCHEDULE': ['LAYER_NAME']}
- tokens: 63 from the columns, 19 listed (framework_values); refused: 4 slot-value word(s), 0 person-column word(s)
- kept: addcolumnsrule, addcustomcolumnsrule, adp, datagaps, datatypeconversionrule, decimaltyperule, deduplicationrankrule, deduplicationrule, duplicatefilereceived, filesnotreceived, filesnotreceivedacdc, filesnotreceivedacde, filesnotreceivedacla, filesnotreceivedacnh, filesnotreceivedacoh, filesnotreceivedacpa, filesnotreceivedbccmi, filesnotreceivedenterprise, filesnotreceivedshsc, fixedwidthhandler, nostandardentriespresentiniigtables, nullcheckrule, rdbmsinvokedeltatable, removeexistingfiledupes, replacecharacterrule, v4, wf

## DATABRICKS_NOTEBOOK_DETAILS per flow

- rows by flow: {'file_to_stg': 248, 'stg_to_std': 130}
- flow from: {'group index': 378}

### DATABRICKS_NOTEBOOK_PATH - file_to_stg (248 of 248 filled)

- values:
  - 29.8% (74) `/iig/RDBMSInvokeDeltaTable_V0.1`
  - 27.4% (68) `/Workspace/G73/G16_G17_FixedWidthHandler,/Workspace/G73/FileInvokeDQDeltaTable`
  - 13.7% (34) `/Workspace/G73/G17_PIPE_DELIMITED_SEGMENT_HNDLR,/Workspace/G73/FileInvokeDQDeltaTable`
  - 12.9% (32) `/Workspace/G73/G16_G17_FixedWidthHandler,/Workspace/G73/TPL_FileInvokeDQDeltaTable`
  - 4.8% (12) `/Workspace/iig/FileInvokeDQDeltaTable_V0.1`
  - 4.0% (10) `/Workspace/iig/FileInvokeDQDeltaTable_V0.2`
  - 2.4% (6) `/iig/FileInvokeDQDeltaTable_V0.1`
  - 1.6% (4) `/Workspace/iig/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 1.6% (4) `/Workspace/iig/G75/NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.8% (2) `/Workspace/Shared/G76_PROD_G77_SCRIPTS/G76_CODE/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 0.8% (2) `/iig/FileInvokeDQDeltaTable_ADP`
- patterns:
  - 29.8% (74) `/iig/RDBMSInvokeDeltaTable_V0.1`
  - 27.4% (68) `/Workspace/G73/{domain}_FixedWidthHandler,/Workspace/G73/FileInvokeDQDeltaTable`
  - 13.7% (34) `/Workspace/G73/{source}_PIPE_DELIMITED_SEGMENT_HNDLR,/Workspace/G73/FileInvokeDQDeltaTable`
  - 12.9% (32) `/Workspace/G73/{domain}_FixedWidthHandler,/Workspace/G73/TPL_FileInvokeDQDeltaTable`
  - 4.8% (12) `/Workspace/iig/FileInvokeDQDeltaTable_V0.1`
  - 4.0% (10) `/Workspace/iig/FileInvokeDQDeltaTable_V0.2`
  - 2.4% (6) `/iig/FileInvokeDQDeltaTable_V0.1`
  - 1.6% (4) `/Workspace/iig/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 1.6% (4) `/Workspace/iig/G75/NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.8% (2) `/Workspace/Shared/G76_PROD_G77_SCRIPTS/G76_CODE/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 0.8% (2) `/iig/FileInvokeDQDeltaTable_ADP`

### DATABRICKS_NOTEBOOK_PATH - stg_to_std (130 of 130 filled)

- values:
  - 76.9% (100) `/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 9.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V2`
  - 9.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 3.1% (4) `/iig/G74/DeltaInvokeDQStandardDeltaTable`
  - 1.5% (2) `/iig/G74/DeltaInvokeDQStandardDeltaTable_V2`
- patterns:
  - 76.9% (100) `/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 9.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V2`
  - 9.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 3.1% (4) `/iig/G74/DeltaInvokeDQStandardDeltaTable`
  - 1.5% (2) `/iig/G74/DeltaInvokeDQStandardDeltaTable_V2`

### DATABRICKS_NOTEBOOK_NAME - file_to_stg (248 of 248 filled)

- values:
  - 30.6% (76) `G16_G17_FixedWidthHandler,FileInvokeDQDeltaTable`
  - 29.8% (74) `RDBMSInvokeDeltaTable_V0.1`
  - 13.7% (34) `G17_PIPE_DELIMITED_SEGMENT_HNDLR,FileInvokeDQDeltaTable`
  - 9.7% (24) `G16_G17_FixedWidthHandler,TPL_FileInvokeDQDeltaTable`
  - 7.3% (18) `FileInvokeDQDeltaTable_V0.1`
  - 4.0% (10) `FileInvokeDQDeltaTable_V0.2`
  - 2.4% (6) `FileInvokeDQDeltaTable_DATAGAPS`
  - 1.6% (4) `NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.8% (2) `FileInvokeDQDeltaTable_ADP`
- patterns:
  - 30.6% (76) `{domain}_FixedWidthHandler,FileInvokeDQDeltaTable`
  - 29.8% (74) `RDBMSInvokeDeltaTable_V0.1`
  - 13.7% (34) `{source}_PIPE_DELIMITED_SEGMENT_HNDLR,FileInvokeDQDeltaTable`
  - 9.7% (24) `{domain}_FixedWidthHandler,TPL_FileInvokeDQDeltaTable`
  - 7.3% (18) `FileInvokeDQDeltaTable_V0.1`
  - 4.0% (10) `FileInvokeDQDeltaTable_V0.2`
  - 2.4% (6) `FileInvokeDQDeltaTable_DATAGAPS`
  - 1.6% (4) `NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.8% (2) `FileInvokeDQDeltaTable_ADP`

### DATABRICKS_NOTEBOOK_NAME - stg_to_std (130 of 130 filled)

- values:
  - 86.2% (112) `DeltaInvokeDQStandardDeltaTable_V4`
  - 10.8% (14) `DeltaInvokeDQStandardDeltaTable_V2`
  - 3.1% (4) `DeltaInvokeDQStandardDeltaTable`
- patterns:
  - 86.2% (112) `DeltaInvokeDQStandardDeltaTable_V4`
  - 10.8% (14) `DeltaInvokeDQStandardDeltaTable_V2`
  - 3.1% (4) `DeltaInvokeDQStandardDeltaTable`

### PROCESS_NAME - file_to_stg (248 of 248 filled)

- values:
  - 29.8% (74) `G1  Raw to stage load`
  - 2.4% (6) `G22_834 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `Stage Load for SFMC`
  - 1.6% (4) `G22_834 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `PL_FILE_G3_G4_G5_ADLS_To_Delta_Incr`
  - 0.8% (2) `PL_File_STAGE_G7`
  - 0.8% (2) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.8% (2) `Stage Load for G8 Demographics Package`
  - 0.8% (2) `Stage Load for G8 Analytics Package`
  - 0.8% (2) `Stage Load for G8 SD Individual Risk Package`
  - 0.8% (2) `Stage Load for G71`
  - 0.8% (2) `Stage Load for G15 RX Claims History`
  - 0.8% (2) `G22_834 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `Stage Load for CAQH`
  - 0.8% (2) `Weekly Stage Load for MI`
  - 0.8% (2) `G22_834 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G16 834 G22 G72 Daily Stage Load`
  - 0.8% (2) `G16 834 G22 G72 Weekly Stage Load`
  - 0.8% (2) `G16 834 G22 G72  Monthly Stage Load`
  - 0.8% (2) `G16 834 G22 G72 G21 Stage Load`
  - 0.8% (2) `Stage Load for G60`
  - 0.8% (2) `Stage Load for G60 G62`
  - 0.8% (2) `Stage Load for G60 G63`
  - 0.8% (2) `Stage Load for G60 G64_Leave`
- patterns:
  - 29.8% (74) `G1  Raw to stage load`
  - 2.4% (6) `G22_834 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 2.4% (6) `G22_834 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `Stage Load for SFMC`
  - 1.6% (4) `G22_834 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (4) `G22_834 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.2% (3) `Stage Load for G8 {feed}`
  - 1.2% (3) `Stage Load for {source}`
  - 0.8% (2) `PL_FILE_G3_G4_G5_ADLS_To_Delta_Incr`
  - 0.8% (2) `PL_File_STAGE_G7`
  - 0.8% (2) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.8% (2) `Stage Load for G15 RX {domain} History`
  - 0.8% (2) `G22_834 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `Weekly Stage Load for MI`
  - 0.8% (2) `G22_834 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (2) `G22_834 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (1) `Stage Load for G8 {table} Package`
  - 0.4% (1) `{source} 834 G22 G72 Daily Stage Load`
  - 0.4% (1) `{source} 834 G22 G72 Weekly Stage Load`
  - 0.4% (1) `{source} 834 G22 G72  Monthly Stage Load`
  - 0.4% (1) `{source} 834 G22 G72 G21 Stage Load`
  - 0.4% (1) `Stage Load for {subdomain}`
  - 0.4% (1) `Stage Load for {subdomain} G62`
  - 0.4% (1) `Stage Load for {subdomain} G63`
  - 0.4% (1) `Stage Load for {subdomain} G64_Leave`
  - 0.4% (1) `Stage Load for G8 Analytics Package`
  - 0.4% (1) `Stage Load for G8 SD Individual Risk Package`
  - 0.4% (1) `Stage Load for CAQH`
  - 0.4% (1) `G16 834 G22 G72 Daily Stage Load`
  - 0.4% (1) `G16 834 G22 G72 Weekly Stage Load`
  - 0.4% (1) `G16 834 G22 G72  Monthly Stage Load`
  - 0.4% (1) `G16 834 G22 G72 G21 Stage Load`
  - 0.4% (1) `Stage Load for G60`
  - 0.4% (1) `Stage Load for G60 G62`
  - 0.4% (1) `Stage Load for G60 G63`
  - 0.4% (1) `Stage Load for G60 G64_Leave`

### PROCESS_NAME - stg_to_std (130 of 130 filled)

- values:
  - 56.9% (74) `G1  stage to std load`
  - 9.2% (12) `G1_G2  stage to std load`
  - 1.5% (2) `PL_FILE_G3_G4_G5_Delta_To_G6_Incr`
  - 1.5% (2) `PL_File_STANDARD_G7`
  - 1.5% (2) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 1.5% (2) `Standard Load for G8 Demographics Package`
  - 1.5% (2) `Standard Load for G8 Analytics Package`
  - 1.5% (2) `Standard Load for G8 Individual Risk Package`
  - 1.5% (2) `Standard Load for G71`
  - 1.5% (2) `Standard Load for G15 RX Claims History`
  - 1.5% (2) `Standard Load for CAQH`
  - 1.5% (2) `Weekly Standard Load for MI`
  - 1.5% (2) `G16 834 G22 G72 Daily Standard Load`
  - 1.5% (2) `G16 834 G22 G72 Weekly Standard Load`
  - 1.5% (2) `G16 834 G22 G72 Monthly Standard Load`
  - 1.5% (2) `G16 834 G22 G72 G21 Standard Load`
  - 1.5% (2) `G1_G65  stage to std load`
  - 1.5% (2) `G1_G66  stage to std load`
  - 1.5% (2) `G1_G67  stage to std load`
  - 1.5% (2) `G1_G68  stage to std load`
  - 1.5% (2) `G1_G69  stage to std load`
  - 1.5% (2) `G1_G69  Case Stage to Standard load`
  - 1.5% (2) `G1_G69 G70  Stage to Standard load`
  - 1.5% (2) `Standard Load for SFMC`
- patterns:
  - 56.9% (74) `G1  stage to std load`
  - 13.1% (17) `G1_{source}  stage to std load`
  - 2.3% (3) `Standard Load for {source}`
  - 1.5% (2) `PL_FILE_G3_G4_G5_Delta_To_G6_Incr`
  - 1.5% (2) `PL_File_STANDARD_G7`
  - 1.5% (2) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 1.5% (2) `Standard Load for {schema} {feed}`
  - 1.5% (2) `Standard Load for G8 Individual Risk Package`
  - 1.5% (2) `Standard Load for G15 RX {domain} History`
  - 1.5% (2) `Weekly Standard Load for MI`
  - 1.5% (2) `Standard Load for SFMC`
  - 0.8% (1) `{source} 834 G22 G72 Daily Standard Load`
  - 0.8% (1) `{source} 834 G22 G72 Weekly Standard Load`
  - 0.8% (1) `{source} 834 G22 G72 Monthly Standard Load`
  - 0.8% (1) `{source} 834 G22 G72 G21 Standard Load`
  - 0.8% (1) `G1_{source}  Case Stage to Standard load`
  - 0.8% (1) `G1_{source} G70  Stage to Standard load`
  - 0.8% (1) `Standard Load for G8 {feed}`
  - 0.8% (1) `Standard Load for G8 Analytics Package`
  - 0.8% (1) `Standard Load for CAQH`
  - 0.8% (1) `G16 834 G22 G72 Daily Standard Load`
  - 0.8% (1) `G16 834 G22 G72 Weekly Standard Load`
  - 0.8% (1) `G16 834 G22 G72 Monthly Standard Load`
  - 0.8% (1) `G16 834 G22 G72 G21 Standard Load`
  - 0.8% (1) `G1_G65  stage to std load`
  - 0.8% (1) `G1_G66  stage to std load`
  - 0.8% (1) `G1_G67  stage to std load`
  - 0.8% (1) `G1_G68  stage to std load`
  - 0.8% (1) `G1_G69  stage to std load`
  - 0.8% (1) `G1_G69  Case Stage to Standard load`
  - 0.8% (1) `G1_G69 G70  Stage to Standard load`

## DATA_FACTORY_PIPELINE_SCHEDULE per flow

- rows by flow: {'file_to_stg': 20212, 'grand_master': 2922, 'master': 1850, 'sftp_to_adls': 160, 'stg_to_std': 10514}
- flow from: {'group index': 29656, 'master row': 3680, 'schedule row': 2322}

### PIPELINE_DESCRIPTION - file_to_stg (20212 of 20212 filled)

- values:
  - 33.3% (6734) `G1 Stage Load`
  - 2.3% (474) `G16_G17 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (316) `G16_G17 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (182) `G60 G61_extract File Pipeline Regular Load to Stage`
  - 0.9% (182) `G60 G62_G63 G99_G62 File Pipeline Regular Load to Stage`
  - 0.9% (182) `G60 G62_G63 G99_G63 File Pipeline Regular Load to Stage`
  - 0.9% (182) `G60 G100_G64_Leave File Pipeline Regular Load to Stage`
  - 0.9% (182) `G1 G66 RAW to Stage Regular load`
  - 0.9% (182) `G1 G67 RAW to Stage Regular load`
  - 0.9% (182) `G1 G68 RAW to Stage Regular load`
  - 0.9% (182) `G1 G69 RAW to Stage Regular load`
  - 0.9% (182) `G1 G65 RAW to Stage Regular load`
  - 0.8% (158) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.8% (158) `G16_G17 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `CAQH TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.8% (158) `MI TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.8% (158) `G16_G17 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16_G17 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (158) `G16 834 G22 G72 Daily File Pipeline Regular Load to Stage`
  - 0.8% (158) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Stage`
  - 0.8% (158) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Stage`
  - 0.8% (158) `G16 834 G22 G72 G21 File Pipeline Regular Load to Stage`
  - 0.2% (32) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to Stage`
  - 0.2% (32) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to Stage`
  - 0.2% (32) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to Stage`
  - 0.2% (32) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to Stage`
  - 0.2% (32) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to Stage`
  - 0.2% (32) `G3_G4_G5 File Pipeline Regular Load to Stage`
  - 0.2% (32) `G7 File Pipeline Regular Load to Stage`
  - 0.2% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Stage`
  - 0.1% (12) `G8 Demographics Package Pipeline Regular Load to Stage`
  - 0.1% (12) `G8 Analytics Package Pipeline Regular Load to Stage`
  - 0.1% (12) `G8 Ind Risk Package Pipeline Regular Load to Stage`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Stage`
  - 0.0% (4) `Common Claims Medical History Regular Load to Stage`
  - 0.0% (4) `G14 LA History Stage Pipeline Historical Load`
- patterns:
  - 33.3% (6734) `G1 Stage Load`
  - 2.1% (432) `{domain} 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.4% (288) `{domain} G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (181) `G1 G66 RAW to Stage Regular load`
  - 0.9% (181) `G1 G67 RAW to Stage Regular load`
  - 0.9% (181) `G1 G68 RAW to Stage Regular load`
  - 0.9% (181) `G1 G65 RAW to Stage Regular load`
  - 0.9% (179) `G1 G69 RAW to Stage Regular load`
  - 0.9% (178) `G60 G61_extract File Pipeline Regular Load to Stage`
  - 0.9% (178) `G60 G62_G63 G99_G62 File Pipeline Regular Load to Stage`
  - 0.9% (178) `G60 G62_G63 G99_G63 File Pipeline Regular Load to Stage`
  - 0.9% (178) `G60 G100_G64_Leave File Pipeline Regular Load to Stage`
  - 0.8% (156) `MI TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.8% (154) `CAQH TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.7% (150) `G16 834 G22 G72 Daily File Pipeline Regular Load to Stage`
  - 0.7% (150) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Stage`
  - 0.7% (150) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Stage`
  - 0.7% (150) `G16 834 G22 G72 G21 File Pipeline Regular Load to Stage`
  - 0.7% (144) `{domain} 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.7% (144) `{domain} G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.7% (144) `{domain} 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.2% (32) `G3_G4_G5 File Pipeline Regular Load to Stage`
  - 0.2% (32) `G7 File Pipeline Regular Load to Stage`
  - 0.2% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Stage`
  - 0.1% (24) `{source}_G17 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G91_G92 File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G93_G94_G92 File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G95_pct_mo_de File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_data_G92 File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G96_G92 File Pipeline Regular Load to Stage`
  - 0.1% (16) `{source}_G17 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (16) `{source}_G17 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (12) `G16_G17 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `G8 Ind Risk Package Pipeline Regular Load to Stage`
  - 0.0% (9) `G8 Analytics Package Pipeline Regular Load to Stage`
  - 0.0% (8) `G8 {feed} Pipeline Regular Load to Stage`
  - 0.0% (8) `G16_G17 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source} 834 G22 G72 Daily File Pipeline Regular Load to Stage`
  - 0.0% (8) `{source} 834 G22 G72 Weekly File Pipeline Regular Load to Stage`
  - 0.0% (8) `{source} 834 G22 G72 Monthly File Pipeline Regular Load to Stage`
  - 0.0% (8) `{source} 834 G22 G72 G21 File Pipeline Regular Load to Stage`
  - 0.0% (7) `G1 {source} RAW to Stage Regular load`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Stage`
  - 0.0% (6) `G16_{source} 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (5) `DIGITAL G102 {subdomain} File Pipeline Regular Load to Stage`
  - 0.0% (5) `DIGITAL G102 {table} File Pipeline Regular Load to Stage`
  - 0.0% (4) `Common {domain} {subdomain} History Regular Load to Stage`
  - 0.0% (4) `{source} LA History Stage Pipeline Historical Load`
  - 0.0% (4) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `{subdomain} G100_G64_Leave File Pipeline Regular Load to Stage`
  - 0.0% (3) `G8 Demographics Package Pipeline Regular Load to Stage`
  - 0.0% (3) `{subdomain} G62_G63 G99_G62 File Pipeline Regular Load to Stage`
  - 0.0% (3) `{subdomain} G62_G63 G99_G63 File Pipeline Regular Load to Stage`
  - 0.0% (3) `{subdomain} G61_extract File Pipeline Regular Load to Stage`
  - 0.0% (2) `{schema} {feed} Pipeline Regular Load to Stage`
  - 0.0% (2) `{schema} Ind Risk Package Pipeline Regular Load to Stage`
  - 0.0% (2) `{source} TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.0% (2) `CAQH {subdomain} WORKFLOW FILE STAGE DATA INGESTION`
  - 0.0% (2) `MI {subdomain} WORKFLOW FILE STAGE DATA INGESTION`
  - 0.0% (2) `G16_{source} 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `{subdomain} G62_G63 {table} File Pipeline Regular Load to Stage`
  - 0.0% (1) `{schema} Analytics Package Pipeline Regular Load to Stage`
  - 0.0% (1) `{schema} Demographics Package Pipeline Regular Load to Stage`
  - 0.0% (1) `{subdomain} {table}_extract File Pipeline Regular Load to Stage`

### PIPELINE_DESCRIPTION - grand_master (2922 of 2922 filled)

- values:
  - 6.2% (182) `G60 Regular Load Grand Master Pipeline`
  - 6.2% (182) `G60 G62_G63 Regular Load Grand Master Pipeline`
  - 6.2% (182) `G60 G100_G64_Leave Regular Load Grand Master Pipeline`
  - 6.2% (182) `GMSTR_G1_G66_ONPREM_STG_INGESTION`
  - 6.2% (182) `GMSTR_G1_G67_ONPREM_STG_INGESTION`
  - 6.2% (182) `GMSTR_G1_G68_ONPREM_STG_INGESTION`
  - 6.2% (182) `GMSTR_G1_G69_ONPREM_STG_INGESTION`
  - 6.2% (182) `GMSTR_G1_G2_ONPREM_STG_INGESTION`
  - 6.2% (182) `G1 Grand Master Pipeline`
  - 6.2% (182) `GMSTR_G1_G65_ONPREM_STG_INGESTION`
  - 5.4% (158) `G16_G17 G101 Pipeline for Incremental load`
  - 5.4% (158) `CAQH TPL Grand Master Pipeline`
  - 5.4% (158) `G16 834 G22 G72 Daily Grand Master Pipeline`
  - 5.4% (158) `G16 834 G22 G72 Weekly Grand Master Pipeline`
  - 5.4% (158) `G16 834 G22 G72 Monthly Grand Master Pipeline`
  - 5.4% (158) `G16 834 G22 G72 G21 Grand Master Pipeline`
  - 1.1% (32) `DIGITAL G102 Regular Load Grand Master Pipeline`
  - 1.1% (32) `G3_G4_G5 Regular Load Grand Master Pipeline`
  - 1.1% (32) `G7 Regular Load Grand Master Pipeline`
  - 1.1% (32) `G3_G4_G5_Inbound Regular Load Grand Master Pipeline`
  - 0.4% (12) `G103 G8 Grand Master Pipeline`
  - 0.2% (6) `EMCIPS SFMC Email Campaign Tracking Details Grand Master Pipeline`
  - 0.1% (4) `Common Claims Medical History Grand Master Pipeline`
  - 0.1% (4) `G14 LA History Grand Master Pipeline`
- patterns:
  - 6.2% (182) `G1 Grand Master Pipeline`
  - 6.2% (181) `GMSTR_G1_G66_ONPREM_STG_INGESTION`
  - 6.2% (181) `GMSTR_G1_G67_ONPREM_STG_INGESTION`
  - 6.2% (181) `GMSTR_G1_G68_ONPREM_STG_INGESTION`
  - 6.2% (181) `GMSTR_G1_G65_ONPREM_STG_INGESTION`
  - 6.1% (179) `GMSTR_G1_G69_ONPREM_STG_INGESTION`
  - 6.1% (178) `G60 Regular Load Grand Master Pipeline`
  - 6.1% (178) `G60 G62_G63 Regular Load Grand Master Pipeline`
  - 6.1% (178) `G60 G100_G64_Leave Regular Load Grand Master Pipeline`
  - 5.3% (154) `CAQH TPL Grand Master Pipeline`
  - 5.1% (150) `G16 834 G22 G72 Daily Grand Master Pipeline`
  - 5.1% (150) `G16 834 G22 G72 Weekly Grand Master Pipeline`
  - 5.1% (150) `G16 834 G22 G72 Monthly Grand Master Pipeline`
  - 5.1% (150) `G16 834 G22 G72 G21 Grand Master Pipeline`
  - 4.9% (144) `{domain} G101 Pipeline for Incremental load`
  - 3.6% (104) `GMSTR_G1_{source}_ONPREM_STG_INGESTION`
  - 2.9% (85) `GMSTR_G1_G2_ONPREM_STG_INGESTION`
  - 1.1% (32) `DIGITAL G102 Regular Load Grand Master Pipeline`
  - 1.1% (32) `G3_G4_G5 Regular Load Grand Master Pipeline`
  - 1.1% (32) `G7 Regular Load Grand Master Pipeline`
  - 1.1% (32) `G3_G4_G5_Inbound Regular Load Grand Master Pipeline`
  - 0.3% (10) `G103 G8 Grand Master Pipeline`
  - 0.3% (8) `{source}_G17 G101 Pipeline for Incremental load`
  - 0.3% (8) `{source} 834 G22 G72 Daily Grand Master Pipeline`
  - 0.3% (8) `{source} 834 G22 G72 Weekly Grand Master Pipeline`
  - 0.3% (8) `{source} 834 G22 G72 Monthly Grand Master Pipeline`
  - 0.3% (8) `{source} 834 G22 G72 G21 Grand Master Pipeline`
  - 0.2% (6) `EMCIPS SFMC Email Campaign Tracking Details Grand Master Pipeline`
  - 0.1% (4) `Common {domain} {subdomain} History Grand Master Pipeline`
  - 0.1% (4) `{source} LA History Grand Master Pipeline`
  - 0.1% (4) `G16_G17 G101 Pipeline for Incremental load`
  - 0.1% (4) `{subdomain} Regular Load Grand Master Pipeline`
  - 0.1% (4) `{subdomain} G62_G63 Regular Load Grand Master Pipeline`
  - 0.1% (4) `{subdomain} G100_G64_Leave Regular Load Grand Master Pipeline`
  - 0.1% (2) `G103 {schema} Grand Master Pipeline`
  - 0.1% (2) `{source} TPL Grand Master Pipeline`
  - 0.1% (2) `CAQH {subdomain} Grand Master Pipeline`
  - 0.1% (2) `G16_{source} G101 Pipeline for Incremental load`

### PIPELINE_DESCRIPTION - master (1850 of 1850 filled)

- values:
  - 9.8% (182) `G60 Master Pipeline for RAW to Stage Regular load`
  - 9.8% (182) `G60 G62_G63 Master Pipeline for RAW to Stage Regular load`
  - 9.8% (182) `G60 G100_G64_Leave Master Pipeline for RAW to Stage Regular load`
  - 9.8% (182) `G1_G2 Master Pipeline for RAW to Stage Regular load`
  - 9.8% (182) `G1 Master Pipeline`
  - 8.5% (158) `G16_G17 Master Pipeline for RAW to Stage Incremental load`
  - 8.5% (158) `G16 834 G22 G72 Daily Master Pipeline RAW to Standard Regular load`
  - 8.5% (158) `G16 834 G22 G72 Weekly Master Pipeline RAW to Standard Regular load`
  - 8.5% (158) `G16 834 G22 G72 Monthly Master Pipeline RAW to Standard Regular load`
  - 8.5% (158) `G16 834 G22 G72 G21 Master Pipeline RAW to Standard Regular load`
  - 1.7% (32) `DIGITAL G102 Master Pipeline for RAW to Stage Regular load`
  - 1.7% (32) `G3_G4_G5 Master Pipeline for RAW to Stage Regular load`
  - 1.7% (32) `G7 Master Pipeline for RAW to Stage Regular load`
  - 1.7% (32) `G3_G4_G5_Inbound Master Pipeline for RAW to Stage Regular load`
  - 0.6% (12) `G103 G8 Master Pipeline RAW to Standard Regular load`
  - 0.3% (6) `EMCIPS SFMC Email Campaign Tracking Details Master Pipeline RAW to Standard Regular load`
  - 0.2% (4) `G14 LA History Master Pipeline Historical Load`
- patterns:
  - 9.8% (182) `G1 Master Pipeline`
  - 9.6% (178) `G60 Master Pipeline for RAW to Stage Regular load`
  - 9.6% (178) `G60 G62_G63 Master Pipeline for RAW to Stage Regular load`
  - 9.6% (178) `G60 G100_G64_Leave Master Pipeline for RAW to Stage Regular load`
  - 8.1% (150) `G16 834 G22 G72 Daily Master Pipeline RAW to Standard Regular load`
  - 8.1% (150) `G16 834 G22 G72 Weekly Master Pipeline RAW to Standard Regular load`
  - 8.1% (150) `G16 834 G22 G72 Monthly Master Pipeline RAW to Standard Regular load`
  - 8.1% (150) `G16 834 G22 G72 G21 Master Pipeline RAW to Standard Regular load`
  - 7.8% (144) `{domain} Master Pipeline for RAW to Stage Incremental load`
  - 5.2% (97) `G1_{source} Master Pipeline for RAW to Stage Regular load`
  - 4.6% (85) `G1_G2 Master Pipeline for RAW to Stage Regular load`
  - 1.7% (32) `DIGITAL G102 Master Pipeline for RAW to Stage Regular load`
  - 1.7% (32) `G3_G4_G5 Master Pipeline for RAW to Stage Regular load`
  - 1.7% (32) `G7 Master Pipeline for RAW to Stage Regular load`
  - 1.7% (32) `G3_G4_G5_Inbound Master Pipeline for RAW to Stage Regular load`
  - 0.5% (10) `G103 G8 Master Pipeline RAW to Standard Regular load`
  - 0.4% (8) `{source}_G17 Master Pipeline for RAW to Stage Incremental load`
  - 0.4% (8) `{source} 834 G22 G72 Daily Master Pipeline RAW to Standard Regular load`
  - 0.4% (8) `{source} 834 G22 G72 Weekly Master Pipeline RAW to Standard Regular load`
  - 0.4% (8) `{source} 834 G22 G72 Monthly Master Pipeline RAW to Standard Regular load`
  - 0.4% (8) `{source} 834 G22 G72 G21 Master Pipeline RAW to Standard Regular load`
  - 0.3% (6) `EMCIPS SFMC Email Campaign Tracking Details Master Pipeline RAW to Standard Regular load`
  - 0.2% (4) `{source} LA History Master Pipeline Historical Load`
  - 0.2% (4) `G16_G17 Master Pipeline for RAW to Stage Incremental load`
  - 0.2% (4) `{subdomain} Master Pipeline for RAW to Stage Regular load`
  - 0.2% (4) `{subdomain} G62_G63 Master Pipeline for RAW to Stage Regular load`
  - 0.2% (4) `{subdomain} G100_G64_Leave Master Pipeline for RAW to Stage Regular load`
  - 0.1% (2) `G103 {schema} Master Pipeline RAW to Standard Regular load`
  - 0.1% (2) `G16_{source} Master Pipeline for RAW to Stage Incremental load`

### PIPELINE_DESCRIPTION - sftp_to_adls (160 of 160 filled)

- values:
  - 20.0% (32) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to RAW`
  - 20.0% (32) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to RAW`
  - 20.0% (32) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to RAW`
  - 20.0% (32) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to RAW`
  - 20.0% (32) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to RAW`
- patterns:
  - 12.5% (20) `DIGITAL G102 db_104_{domain}_G91_G92 File Pipeline Regular Load to RAW`
  - 12.5% (20) `DIGITAL G102 db_104_{domain}_G93_G94_G92 File Pipeline Regular Load to RAW`
  - 12.5% (20) `DIGITAL G102 db_104_{domain}_G95_pct_mo_de File Pipeline Regular Load to RAW`
  - 12.5% (20) `DIGITAL G102 db_104_{domain}_data_G92 File Pipeline Regular Load to RAW`
  - 12.5% (20) `DIGITAL G102 db_104_{domain}_G96_G92 File Pipeline Regular Load to RAW`
  - 6.2% (10) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to RAW`
  - 6.2% (10) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to RAW`
  - 6.2% (10) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to RAW`
  - 6.2% (10) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to RAW`
  - 6.2% (10) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to RAW`
  - 3.1% (5) `DIGITAL G102 {subdomain} File Pipeline Regular Load to RAW`
  - 3.1% (5) `DIGITAL G102 {table} File Pipeline Regular Load to RAW`

### PIPELINE_DESCRIPTION - stg_to_std (10514 of 10514 filled)

- values:
  - 64.0% (6734) `G1 Standard Load`
  - 1.7% (182) `G1_G2 G78 Regular STANDARD Load`
  - 1.7% (182) `G1_G2 G79 Regular STANDARD Load`
  - 1.7% (182) `G1_G2 G80 Regular STANDARD Load`
  - 1.7% (182) `G1 G66 Regular STANDARD Load`
  - 1.7% (182) `G1 G67 Regular STANDARD Load`
  - 1.7% (182) `G1 G68 Regular STANDARD Load`
  - 1.7% (182) `G1 G69 Regular STANDARD Load`
  - 1.7% (182) `G1 G69 Case Regular STANDARD Load`
  - 1.7% (182) `G1 G69 G70 Regular STANDARD Load`
  - 1.7% (182) `G1_G2 G81 Regular STANDARD Load`
  - 1.7% (182) `G1_G2 G82 Regular STANDARD Load`
  - 1.7% (182) `G1_G2 G83 Regular STANDARD Load`
  - 1.7% (182) `G1 G65 Regular STANDARD Load`
  - 1.5% (158) `CAQH TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 1.5% (158) `MI TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 1.5% (158) `G16 834 G22 G72 Daily File Pipeline Regular Load to Standard`
  - 1.5% (158) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Standard`
  - 1.5% (158) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Standard`
  - 1.5% (158) `G16 834 G22 G72 G21 File Pipeline Regular Load to Standard`
  - 1.5% (158) `CAQH TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 1.5% (158) `MI TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.3% (32) `G3_G4_G5 File Pipeline Regular Load to Standard`
  - 0.3% (32) `G7 File Pipeline Regular Load to Standard`
  - 0.3% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Standard`
  - 0.1% (12) `G8 Demographics Package Pipeline Regular Load to Standard`
  - 0.1% (12) `G8 Analytics Package Pipeline Regular Load to Standard`
  - 0.1% (12) `G8 Ind Risk Package Pipeline Regular Load to Standard`
  - 0.1% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Standard`
  - 0.0% (4) `Common Claims Medical History Regular Load to Standard`
  - 0.0% (4) `Common Claims Medical History RAW to Standard Regular load`
  - 0.0% (4) `G14 LA History Standard Pipeline Historical Load`
- patterns:
  - 64.0% (6734) `G1 Standard Load`
  - 1.7% (181) `G1 G66 Regular STANDARD Load`
  - 1.7% (181) `G1 G67 Regular STANDARD Load`
  - 1.7% (181) `G1 G68 Regular STANDARD Load`
  - 1.7% (181) `G1 G65 Regular STANDARD Load`
  - 1.7% (179) `G1 G69 Regular STANDARD Load`
  - 1.7% (179) `G1 G69 Case Regular STANDARD Load`
  - 1.7% (179) `G1 G69 G70 Regular STANDARD Load`
  - 1.5% (156) `MI TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 1.5% (156) `MI TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 1.5% (154) `CAQH TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 1.5% (154) `CAQH TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 1.4% (150) `G16 834 G22 G72 Daily File Pipeline Regular Load to Standard`
  - 1.4% (150) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Standard`
  - 1.4% (150) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Standard`
  - 1.4% (150) `G16 834 G22 G72 G21 File Pipeline Regular Load to Standard`
  - 0.9% (97) `G1_{source} G78 Regular STANDARD Load`
  - 0.9% (97) `G1_{source} G79 Regular STANDARD Load`
  - 0.9% (97) `G1_{source} G80 Regular STANDARD Load`
  - 0.9% (97) `G1_{source} G81 Regular STANDARD Load`
  - 0.9% (97) `G1_{source} G82 Regular STANDARD Load`
  - 0.9% (97) `G1_{source} G83 Regular STANDARD Load`
  - 0.8% (85) `G1_G2 G78 Regular STANDARD Load`
  - 0.8% (85) `G1_G2 G79 Regular STANDARD Load`
  - 0.8% (85) `G1_G2 G80 Regular STANDARD Load`
  - 0.8% (85) `G1_G2 G81 Regular STANDARD Load`
  - 0.8% (85) `G1_G2 G82 Regular STANDARD Load`
  - 0.8% (85) `G1_G2 G83 Regular STANDARD Load`
  - 0.3% (32) `G3_G4_G5 File Pipeline Regular Load to Standard`
  - 0.3% (32) `G7 File Pipeline Regular Load to Standard`
  - 0.3% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Standard`
  - 0.1% (10) `G8 Ind Risk Package Pipeline Regular Load to Standard`
  - 0.1% (9) `G8 Analytics Package Pipeline Regular Load to Standard`
  - 0.1% (8) `G8 {feed} Pipeline Regular Load to Standard`
  - 0.1% (8) `{source} 834 G22 G72 Daily File Pipeline Regular Load to Standard`
  - 0.1% (8) `{source} 834 G22 G72 Weekly File Pipeline Regular Load to Standard`
  - 0.1% (8) `{source} 834 G22 G72 Monthly File Pipeline Regular Load to Standard`
  - 0.1% (8) `{source} 834 G22 G72 G21 File Pipeline Regular Load to Standard`
  - 0.1% (7) `G1 {source} Regular STANDARD Load`
  - 0.1% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Standard`
  - 0.0% (4) `Common {domain} {subdomain} History Regular Load to Standard`
  - 0.0% (4) `Common {domain} {subdomain} History RAW to Standard Regular load`
  - 0.0% (4) `{source} LA History Standard Pipeline Historical Load`
  - 0.0% (3) `G8 Demographics Package Pipeline Regular Load to Standard`
  - 0.0% (3) `G1 {source} Case Regular STANDARD Load`
  - 0.0% (3) `G1 {source} G70 Regular STANDARD Load`
  - 0.0% (2) `{schema} {feed} Pipeline Regular Load to Standard`
  - 0.0% (2) `{schema} Ind Risk Package Pipeline Regular Load to Standard`
  - 0.0% (2) `{source} TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.0% (2) `{source} TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.0% (2) `CAQH {subdomain} WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.0% (2) `MI {subdomain} WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.0% (2) `CAQH {subdomain} WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.0% (2) `MI {subdomain} WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.0% (1) `{schema} Analytics Package Pipeline Regular Load to Standard`
  - 0.0% (1) `{schema} Demographics Package Pipeline Regular Load to Standard`

## EMAIL_TEMPLATE_CONFIG on file-ingestion pipelines

- rows: 13468; on file-ingestion pipelines: 3844
- rows by flow: {'unclassified': 10430, 'grand_master': 1292, 'master': 784, 'stg_to_std': 526, 'file_to_stg': 436}
- flow from: {'none': 7548, 'pipeline name': 2882, 'rule': 1988, 'group index': 936, 'schedule row': 114}
- statuses per file-ingestion pipeline -> pipelines: {'1': 256, '2': 56, '4': 293}

| STATUS | rows | file-ingestion rows | file-ingestion pipelines |
|---|---|---|---|
| <blank> | 10800 | 2560 | 256 |
| Success | 615 | 349 | 349 |
| Failed | 615 | 349 | 349 |
| FilesNotReceived | 444 | 293 | 293 |
| New Files to Process | 392 | 293 | 293 |
| FilesNotReceivedACPA | 58 | 0 | 0 |
| FilesNotReceivedACLA | 58 | 0 | 0 |
| FilesNotReceivedACDC | 58 | 0 | 0 |
| FilesNotReceivedSHSC | 58 | 0 | 0 |
| FilesNotReceivedBCCMI | 58 | 0 | 0 |
| FilesNotReceivedACOH | 58 | 0 | 0 |
| FilesNotReceivedACDE | 58 | 0 | 0 |
| FilesNotReceivedACNH | 58 | 0 | 0 |
| FilesNotReceivedEnterprise | 58 | 0 | 0 |
| NoStandardEntriesPresentinIIGTables | 37 | 0 | 0 |
| DuplicateFileReceived | 37 | 0 | 0 |
| Files Not Received | 6 | 0 | 0 |

| STATUS | SUBJECT pattern | BODY pattern | rows | share % |
|---|---|---|---|---|
| <blank> |  |  | 2560 | 66.6 |
| FilesNotReceived | G135 G499 G555 Daily File Not Received - | G135 G499 G555 Daily File Not Received | 90 | 2.3 |
| New Files to Process | G135 G499 G555 Daily File Received - | Received The G564 Files for G135 G499 G555 Daily | 90 | 2.3 |
| Success | G135 G499 G555 Daily Load Completed - | G135 G499 G555 Daily Data Load Successful | 90 | 2.3 |
| Failed | G135 G499 G555 Daily Load  Failed - | G135 G499 G555 Daily Data Load Failed | 90 | 2.3 |
| FilesNotReceived | G135 G499 G555 History File Not Received - | G135 G499 G555 History File Not Received | 75 | 2.0 |
| New Files to Process | G135 G499 G555 History File Received - | Received The G564 Files for G135 G499 G555 History | 75 | 2.0 |
| Success | G135 G499 G555 History Load Completed - | G135 G499 G555 History Data Load Successful | 75 | 2.0 |
| Failed | G135 G499 G555 History Load  Failed - | G135 G499 G555 History Data Load Failed | 75 | 2.0 |
| FilesNotReceived | WC_G8 File Not Received | WC_G8 File Not Received | 27 | 0.7 |
| New Files to Process | WC_G8 File Received | Received The G564 Files for WC_G8 | 27 | 0.7 |
| Success | WC_G8   Load Completed | WC_G8 Data Load Successful | 27 | 0.7 |
| Failed | WC_G8   Load  Failed | WC_G8 Data Load Failed | 27 | 0.7 |
| FilesNotReceived | WC_G560_G528 File Not Received | WC_G560_G528  File Not Received | 18 | 0.5 |
| New Files to Process | WC_G560_G528 File Received | Received The G564 Files for WC_G560_G528 | 18 | 0.5 |
| Success | WC_G560_G528   Load Completed | WC_G560_G528 Data Load Successful | 18 | 0.5 |
| Failed | WC_G560_G528  Load  Failed | WC_G560_G528 Data Load Failed | 18 | 0.5 |
| Success | G16 820 Load Completed | G16 820 Files Load Process Completed | 12 | 0.3 |
| Failed | G16 820 Load Failed | G16 820 Files Load Process Failed | 12 | 0.3 |
| FilesNotReceived | G1 – G2 File Not Received | G1 G2 File Not Received | 12 | 0.3 |
| New Files to Process | G1 – G2 File Received | Received The G564 Files for G1 G2 | 12 | 0.3 |
| Success | G1 – G2 Data load to DL Completed | G1 G2 Load Completed | 12 | 0.3 |
| Failed | G1 – G2 Data load to DL Failed | G1 G2 Load Failed | 12 | 0.3 |
| FilesNotReceived | WC_G527 File Not Received | WC_G527  File Not Received | 12 | 0.3 |
| New Files to Process | WC_G527 File Received | Received The G564 Files for WC_G527 | 12 | 0.3 |
| Success | WC_G527   Load Completed | WC_G527 Data Load Successful | 12 | 0.3 |
| Failed | WC_G527  Load  Failed | WC_G527 Data Load Failed | 12 | 0.3 |
| FilesNotReceived | WC_Response File Not Received | WC_Response  File Not Received | 12 | 0.3 |
| New Files to Process | WC_Response File Received | Received The G564 Files for WC_Response | 12 | 0.3 |
| Success | WC_Response Load Completed | WC_Response Data Load Successful | 12 | 0.3 |
| Failed | WC_Response Load  Failed | WC_Response Data Load Failed | 12 | 0.3 |
| Success | G536 Health Load Completed | G536 Health Files Load Process Completed | 10 | 0.3 |
| Failed | G536 Health Load Failed | G536 Health Files Load Process Failed | 10 | 0.3 |
| Success | G103 G8 Load Completed | G103 G8 Files Load Process Completed | 6 | 0.2 |
| Failed | G103 G8 Load Failed | G103 G8 Files Load Process Failed | 6 | 0.2 |
| FilesNotReceived | G1 – {source} File Not Received | G1 {source} File Not Received | 6 | 0.2 |
| New Files to Process | G1 – {source} File Received | Received The G564 Files for G1 {source} | 6 | 0.2 |
| Success | G1 – {source} Data load to DL Completed | G1 {source} Load Completed | 6 | 0.2 |
| Failed | G1 – {source} Data load to DL Failed | G1 {source} Load Failed | 6 | 0.2 |
| FilesNotReceived | G135 G242 G136 Hist File Not Received | G135 G242 G136 Hist File Not Received | 6 | 0.2 |
| New Files to Process | G135 G242 G136 Hist File Received | Received The G564 G136 Historical Files for G135 G242 | 6 | 0.2 |
| Success | G135 G242 G136 Hist Load Completed | G135 G242 G136 Historical Data Load Successful | 6 | 0.2 |
| Failed | G135 G242 G136 Hist Load Failed | G135 G242 G136 Historical Data Load Failed | 6 | 0.2 |
| Success | {domain} Raw To Stage Master Pipeline Status | {domain} Data Load Successful | 4 | 0.1 |
| Failed | {domain} Raw To Stage Master Pipeline Status | {domain} Data Load Failed | 4 | 0.1 |
| Success | G1 – G69 Data load to DL Completed | G1 G69 Load Completed | 4 | 0.1 |
| Failed | G1 – G69 Data load to DL Failed | G1 G69 Load Failed | 4 | 0.1 |
| FilesNotReceived | G1 – G69 File Not Received | G1 G69 File Not Received | 4 | 0.1 |
| New Files to Process | G1 – G69 File Received | Received The G564 Files for G1 G69 | 4 | 0.1 |
| Success | G297 7200 Load Completed | G297 7200 Files Load Process Completed | 4 | 0.1 |
| Failed | G297 7200 Load Failed | G297 7200 Files Load Process Failed | 4 | 0.1 |
| Success | MI STATE TPL Load Completed | MI STATE TPL Files Load Process Completed | 3 | 0.1 |
| Failed | MI STATE TPL Load Failed | MI STATE TPL Files Load Process Failed | 3 | 0.1 |
| FilesNotReceived | G135 G242 G513 File Not Received | G135 G242 G513 File Not Received | 3 | 0.1 |
| New Files to Process | G135 G242 G513 File Received | Received The G564 G513 Files for G135 G242 | 3 | 0.1 |
| Success | G135 G242 G513 Load Completed | G135 G242 G513 Data Load Successful | 3 | 0.1 |
| Failed | G135 G242 G513 Load Failed | G135 G242 G513 Data Load Failed | 3 | 0.1 |
| FilesNotReceived | G135 G242 G514 File Not Received | G135 G242 G514 File Not Received | 3 | 0.1 |
| New Files to Process | G135 G242 G514 File Received | Received The G564 G514 Files for G135 G242 | 3 | 0.1 |
| Success | G135 G242 G514 Load Completed | G135 G242 G514 Data Load Successful | 3 | 0.1 |
| Failed | G135 G242 G514 Load Failed | G135 G242 G514 Data Load Failed | 3 | 0.1 |
| FilesNotReceived | G135 G242 G516 File Not Received | G135 G242 G516 File Not Received | 3 | 0.1 |
| New Files to Process | G135 G242 G516 File Received | Received The G564 G516 Files for G135 G242 | 3 | 0.1 |
| Success | G135 G242 G516 Load Completed | G135 G242 G516 Data Load Successful | 3 | 0.1 |
| Failed | G135 G242 G516 Load Failed | G135 G242 G516 Data Load Failed | 3 | 0.1 |
| FilesNotReceived | G135 G242 G517 File Not Received | G135 G242 G517 File Not Received | 3 | 0.1 |
| New Files to Process | G135 G242 G517 File Received | Received The G564 G517 Files for G135 G242 | 3 | 0.1 |
| Success | G135 G242 G517 Load Completed | G135 G242 G517 Data Load Successful | 3 | 0.1 |
| Failed | G135 G242 G517 Load Failed | G135 G242 G517 Data Load Failed | 3 | 0.1 |
| FilesNotReceived | G135 G242 G525 File Not Received | G135 G242 G525 File Not Received | 3 | 0.1 |
| New Files to Process | G135 G242 G525 File Received | Received The G564 G525 Files for G135 G242 | 3 | 0.1 |
| Success | G135 G242 G525 Load Completed | G135 G242 G525 Data Load Successful | 3 | 0.1 |
| Failed | G135 G242 G525 Load Failed | G135 G242 G525 Data Load Failed | 3 | 0.1 |
| FilesNotReceived | G135 G242 G499 File Not Received | G135 G242 G499 File Not Received | 3 | 0.1 |
| New Files to Process | G135 G242 G499 File Received | Received The G564 G499 Files for G135 G242 | 3 | 0.1 |
| Success | G135 G242 G499 Load Completed | G135 G242 G499 Data Load Successful | 3 | 0.1 |
| Failed | G135 G242 G499 Load Failed | G135 G242 G499 Data Load Failed | 3 | 0.1 |
| Failed | Risk G461 Medicare ONPREM to STANDARD process Failed | Risk G461 Medicare ONPREM to STANDARD process Failed | 3 | 0.1 |
| Success | Risk G461 Medicare ONPREM to STANDARD process Completed | Risk G461 Medicare ONPREM to STANDARD process Completed | 3 | 0.1 |
| Success | Common {domain} {subdomain} History Load Completed | Common {domain} {subdomain} History Files Load Process Completed | 3 | 0.1 |
| Failed | Common {domain} {subdomain} History Load Failed | Common {domain} {subdomain} History Files Load Process Failed | 3 | 0.1 |
| Success | CAQH Load Completed | CAQH Files Load Process Completed | 3 | 0.1 |
| Failed | CAQH Load Failed | CAQH  Files Load Process Failed | 3 | 0.1 |
| Success | G1 – G66 Data load to DL Completed | G1 G66 Load Completed | 2 | 0.1 |
| Failed | G1 – G66 Data load to DL Failed | G1 G66 Load Failed | 2 | 0.1 |
| FilesNotReceived | G1 – G66 File Not Received | G1 G66 File Not Received | 2 | 0.1 |
| New Files to Process | G1 – G66 File Received | Received The G564 Files for G1 G66 | 2 | 0.1 |
| Success | G1 – G65 Data load to DL Completed | G1 G65 Load Completed | 2 | 0.1 |
| Failed | G1 – G65 Data load to DL Failed | G1 G65 Load Failed | 2 | 0.1 |
| FilesNotReceived | G1 – G65 File Not Received | G1 G65 File Not Received | 2 | 0.1 |
| New Files to Process | G1 – G65 File Received | Received The G564 Files for G1 G65 | 2 | 0.1 |
| New Files to Process | G1 – G67 File Received | Received The G564 Files for G1 G67 | 2 | 0.1 |
| Success | G1 – G67 Data load to DL Completed | G1 G67 Load Completed | 2 | 0.1 |
| Failed | G1 – G67 Data load to DL Failed | G1 G67 Load Failed | 2 | 0.1 |
| FilesNotReceived | G1 – G67 File Not Received | G1 G67 File Not Received | 2 | 0.1 |
| Success | G1 – G68 Data load to DL Completed | G1 G68 Load Completed | 2 | 0.1 |
| Failed | G1 – G68 Data load to DL Failed | G1 G68 Load Failed | 2 | 0.1 |
| FilesNotReceived | G1 – G68 File Not Received | G1 G68 File Not Received | 2 | 0.1 |
| New Files to Process | G1 – G68 File Received | Received The G564 Files for G1 G68 | 2 | 0.1 |
| Success | Member Enrollment 7200 G539 Load Completed | Member Enrollment 7200 G539 Files Load Process Completed | 2 | 0.1 |
| Failed | Member Enrollment 7200 G539 Load Failed | Member Enrollment 7200 G539 Files Load Process Failed | 2 | 0.1 |
| Success | Member Enrollment 7200 FACETS Load Completed | Member Enrollment 7200 FACETS Files Load Process Completed | 2 | 0.1 |
| Failed | Member Enrollment 7200 FACETS Load Failed | Member Enrollment 7200 FACETS Files Load Process Failed | 2 | 0.1 |
| Success | Member Enrollment 7200 G540 Load Completed | Member Enrollment 7200 G540 Files Load Process Completed | 2 | 0.1 |
| Failed | Member Enrollment 7200 G540 Load Failed | Member Enrollment 7200 G540 Files Load Process Failed | 2 | 0.1 |
| Failed | {source} LA history Load Failed | {source} LA history Files Load Process Failed | 2 | 0.1 |
| FilesNotReceived | G518 File Not Received | G518 File Not Received | 2 | 0.1 |
| New Files to Process | G518 File Received | Received The G564 Files from G518 | 2 | 0.1 |
| Success | G518 Load Completed | G518 Load Process Completed | 2 | 0.1 |
| Failed | G518 Load Failed | G518 Load Process Failed | 2 | 0.1 |
| FilesNotReceived | {source} LA history Files Not Received | {source} LA history Files Not Received | 2 | 0.1 |
| New Files to Process | {source} LA history Files Received | Received the G564 files for {source} LA history | 2 | 0.1 |
| Success | {source} LA history Load Completed | {source} LA history Files Load Process Completed | 2 | 0.1 |
| Success | SFMC Email Campaign Tracking Details Load Completed | SFMC Email Campaign Tracking Details Files Load Process Completed | 2 | 0.1 |
| Failed | SFMC Email Campaign Tracking Details Load Failed | SFMC Email Campaign Tracking Details Files Load Process Failed | 2 | 0.1 |
| Failed | G14 LA history Load Failed | G14 LA history Files Load Process Failed | 1 | 0.0 |
| FilesNotReceived | G14 LA history Files Not Received | G14 LA history Files Not Received | 1 | 0.0 |
| New Files to Process | G14 LA history Files Received | Received the G564 files for G14 LA history | 1 | 0.0 |
| Success | G14 LA history Load Completed | G14 LA history Files Load Process Completed | 1 | 0.0 |

## Value and pattern lists (all)

### DATABRICKS_NOTEBOOK_DETAILS.PIPELINE_NAME

- values:
  - 3.2% (12) `G1_G2 stage to std load`
  - 1.1% (4) `PL_File_SFMC_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_FILE_G3_G4_G5_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_FILE_G3_G4_G5_Delta_To_G6_Incr`
  - 0.5% (2) `PL_File_STAGE_G7`
  - 0.5% (2) `PL_File_STANDARD_G7`
  - 0.5% (2) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.5% (2) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.5% (2) `PL_File_G8_G9_G10_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_G8_G9_G10_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_G8_G11_G10_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_G8_G11_G10_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_G8_SD_IND_RISK_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_G8_SD_IND_RISK_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_STAGE_CLM_G12_ADLS_To_Delta_G13`
  - 0.5% (2) `PL_File_STD_CLM_G12_Delta_To_STD_G13`
  - 0.5% (2) `PL_File_G14_G15_HIST_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_G14_G15_HIST_Delta_To_STD_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0100_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0500_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0530_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0540_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0100_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0500_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0530_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0540_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_2600_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_2600_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_6400_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_6400_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_G18_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_G18_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_G19_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_G19_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_2100_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_2100_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_5400_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0550_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0550_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_2400_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_2400_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0900_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_0900_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_1200_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_1200_Weekly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_1200_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_7100_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_7100_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_7200_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_7200_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_7700_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_7700_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_G20_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_G20_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G16_G17_2100_G21_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0100_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0100_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0500_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0500_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0530_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0530_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0540_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0540_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0550_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0550_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_5400_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_1200_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_1200_Weekly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_6400_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_6400_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0100_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0500_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0530_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0540_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0550_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_2600_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_2600_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_7200_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_7700_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_7700_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_CAQH_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_CAQH_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_MI_Weekly_G24_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_MI_Weekly_G24_Delta_To_STD_Incr`
  - 0.5% (2) `Pl_File_G22_834_G25_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_G25_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_G25_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_5420_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_5420_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_STAGE_G16_G17_G26_Daily_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_STD_G16_G17_G26_Daily_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_STAGE_G16_G17_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_STD_G16_G17_G26_Weekly_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_STAGE_G16_G17_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_STD_G16_G17_G26_Monthly_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_STAGE_G16_G17_G26_G21_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_STD_G16_G17_G26_G21_Delta_To_STD_Incr`
  - 0.5% (2) `G1  G27_VW Raw to stage load`
  - 0.5% (2) `G1 G27_VW stage to std load`
  - 0.5% (2) `G1  KM_JC_G28 Raw to stage load`
  - 0.5% (2) `G1 KM_JC_G28 stage to std load`
  - 0.5% (2) `G1 KM_G29_REQ_DATA Raw to stage load`
  - 0.5% (2) `G1 KM_G29_REQ_DATA stage to std load`
  - 0.5% (2) `G1 KM_G29_REQ_G30 Raw to stage load`
  - 0.5% (2) `G1 KM_G29_REQ_G30 stage to std load`
  - 0.5% (2) `G1 LOCATION_TBL Raw to stage load`
  - 0.5% (2) `G1 LOCATION_TBL stage to std load`
  - 0.5% (2) `G1 NAMES Raw to stage load`
  - 0.5% (2) `G1 NAMES stage to std load`
  - 0.5% (2) `G1 PER_G31_G32 Raw to stage load`
  - 0.5% (2) `G1 PER_G31_G32 stage to std load`
  - 0.5% (2) `G1 G33_DATA Raw to stage load`
  - 0.5% (2) `G1 G33_DATA stage to std load`
  - 0.5% (2) `G1 POSITION_DATA Raw to stage load`
  - 0.5% (2) `G1 POSITION_DATA stage to std load`
  - 0.5% (2) `G1 VALID_G34_TBL Raw to stage load`
  - 0.5% (2) `G1 VALID_G34_TBL stage to std load`
  - 0.5% (2) `G1 G35_CD_TBL Raw to stage load`
  - 0.5% (2) `G1 G35_CD_TBL stage to std load`
  - 0.5% (2) `G1 G36_REASON_TBL Raw to stage load`
  - 0.5% (2) `G1 G36_REASON_TBL stage to std load`
  - 0.5% (2) `G1 G37_TBL Raw to stage load`
  - 0.5% (2) `G1 G37_TBL stage to std load`
  - 0.5% (2) `G1 G38_G39 Raw to stage load`
  - 0.5% (2) `G1 G38_G39 stage to std load`
  - 0.5% (2) `G1 EMAIL_G40 Raw to stage load`
  - 0.5% (2) `G1 EMAIL_G40 stage to std load`
  - 0.5% (2) `G1 G41 Raw to stage load`
  - 0.5% (2) `G1 G41 stage to std load`
  - 0.5% (2) `G1 JOB Raw to stage load`
  - 0.5% (2) `G1 JOB stage to std load`
  - 0.5% (2) `G1 G42_TBL Raw to stage load`
  - 0.5% (2) `G1 G42_TBL stage to std load`
  - 0.5% (2) `G1 G43_TBL Raw to stage load`
  - 0.5% (2) `G1 G43_TBL stage to std load`
  - 0.5% (2) `G1 KM_G44_REVIEW Raw to stage load`
  - 0.5% (2) `G1 KM_G44_REVIEW stage to std load`
  - 0.5% (2) `G1 AUDIT_JOB Raw to stage load`
  - 0.5% (2) `G1 AUDIT_JOB stage to std load`
  - 0.5% (2) `G1 PERSON Raw to stage load`
  - 0.5% (2) `G1 PERSON stage to std load`
  - 0.5% (2) `G1 G45_DATA_G46 Raw to stage load`
  - 0.5% (2) `G1 G45_DATA_G46 stage to std load`
  - 0.5% (2) `G1 G40 Raw to stage load`
  - 0.5% (2) `G1 G40 stage to std load`
  - 0.5% (2) `G1 PER_G31_G47 Raw to stage load`
  - 0.5% (2) `G1 PER_G31_G47 stage to std load`
  - 0.5% (2) `G1 KM_G29_REQ_HIST Raw to stage load`
  - 0.5% (2) `G1 KM_G29_REQ_HIST stage to std load`
  - 0.5% (2) `G1 G48_REVIEW Raw to stage load`
  - 0.5% (2) `G1 G48_REVIEW stage to std load`
  - 0.5% (2) `G1 G49 Raw to stage load`
  - 0.5% (2) `G1 G49 stage to std load`
  - 0.5% (2) `G1 G50 Raw to stage load`
  - 0.5% (2) `G1 G50 stage to std load`
  - 0.5% (2) `G1 G33_PHONE Raw to stage load`
  - 0.5% (2) `G1 G33_PHONE stage to std load`
  - 0.5% (2) `G1 KM_G51_G52 Raw to stage load`
  - 0.5% (2) `G1 KM_G51_G52 stage to std load`
  - 0.5% (2) `G1 KM_SF_G53_HIST Raw to stage load`
  - 0.5% (2) `G1 KM_SF_G53_HIST stage to std load`
  - 0.5% (2) `G1 KM_SF_G54_HIST Raw to stage load`
  - 0.5% (2) `G1 KM_SF_G54_HIST stage to std load`
  - 0.5% (2) `G1 KM_SF_G55_HIST Raw to stage load`
  - 0.5% (2) `G1 KM_SF_G55_HIST stage to std load`
  - 0.5% (2) `G1 KM_SF_G56_HIST Raw to stage load`
  - 0.5% (2) `G1 KM_SF_G56_HIST stage to std load`
  - 0.5% (2) `G1 PS_G57_G58_G59 Raw to stage load`
  - 0.5% (2) `G1 PS_G57_G58_G59 stage to std load`
  - 0.5% (2) `PL_File_STAGE_G60_G61_extract`
  - 0.5% (2) `PL_File_STAGE_G60_G62`
  - 0.5% (2) `PL_File_STAGE_G60_G63`
  - 0.5% (2) `PL_File_STAGE_G60_G64_Leave`
  - 0.5% (2) `G1  Raw to stage load`
  - 0.5% (2) `G1 stage to std load`
  - 0.5% (2) `G1_G65 stage to std load`
  - 0.5% (2) `G1_G66 stage to std load`
  - 0.5% (2) `G1_G67 stage to std load`
  - 0.5% (2) `G1_G68 stage to std load`
  - 0.5% (2) `G1_G69 stage to std load`
  - 0.5% (2) `PL_MSTR_G1_G69_Case_Delta_To_STD_Incr`
  - 0.5% (2) `PL_MSTR_G1_G69_G70_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_SFMC_Delta_To_STD_Incr`
- patterns:
  - 19.6% (74) `Pl_File_G16_{table}_Regular_ADLS_To_Delta_Incr`
  - 9.5% (36) `{feed} Raw to stage load`
  - 4.5% (17) `G1_{source} stage to std load`
  - 1.1% (4) `PL_File_SFMC_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_FILE_G3_G4_G5_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_FILE_G3_G4_G5_Delta_To_G6_Incr`
  - 0.5% (2) `PL_File_STAGE_G7`
  - 0.5% (2) `PL_File_STANDARD_G7`
  - 0.5% (2) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.5% (2) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.5% (2) `PL_File_G8_G9_G10_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_G8_G11_G10_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_G8_SD_IND_RISK_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_G8_SD_IND_RISK_Delta_To_STD_Incr`
  - 0.5% (2) `PL_File_STAGE_CLM_G12_ADLS_To_Delta_G13`
  - 0.5% (2) `PL_File_{source}_G15_HIST_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_{source}_G15_HIST_Delta_To_STD_Incr`
  - 0.5% (2) `Pl_File_G22_834_0100_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0100_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0500_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0500_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0530_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0530_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0540_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0540_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0550_Daily_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0550_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_5400_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_1200_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_1200_Weekly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_6400_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_6400_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0100_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0500_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0530_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0540_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_0550_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_2600_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_2600_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_7200_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_7700_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_7700_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_MI_Weekly_G24_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_File_MI_Weekly_G24_Delta_To_STD_Incr`
  - 0.5% (2) `Pl_File_G22_834_G25_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_G25_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_G25_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_5420_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `Pl_File_G22_834_5420_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.5% (2) `G1 {table} stage to std load`
  - 0.5% (2) `G1 KM_JC_G28 stage to std load`
  - 0.5% (2) `G1 KM_G29_REQ_DATA stage to std load`
  - 0.5% (2) `G1 KM_G29_REQ_G30 stage to std load`
  - 0.5% (2) `G1 LOCATION_TBL stage to std load`
  - 0.5% (2) `G1 NAMES stage to std load`
  - 0.5% (2) `G1 PER_G31_G32 stage to std load`
  - 0.5% (2) `G1 G33_DATA stage to std load`
  - 0.5% (2) `G1 POSITION_DATA stage to std load`
  - 0.5% (2) `G1 VALID_G34_TBL stage to std load`
  - 0.5% (2) `G1 G35_CD_TBL stage to std load`
  - 0.5% (2) `G1 G36_REASON_TBL stage to std load`
  - 0.5% (2) `G1 G37_TBL stage to std load`
  - 0.5% (2) `G1 G38_G39 stage to std load`
  - 0.5% (2) `G1 EMAIL_G40 stage to std load`
  - 0.5% (2) `G1 G41 stage to std load`
  - 0.5% (2) `G1 JOB stage to std load`
  - 0.5% (2) `G1 G42_TBL stage to std load`
  - 0.5% (2) `G1 G43_TBL stage to std load`
  - 0.5% (2) `G1 KM_G44_REVIEW stage to std load`
  - 0.5% (2) `G1 AUDIT_JOB stage to std load`
  - 0.5% (2) `G1 PERSON stage to std load`
  - 0.5% (2) `G1 G45_DATA_G46 stage to std load`
  - 0.5% (2) `G1 G40 stage to std load`
  - 0.5% (2) `G1 PER_G31_G47 stage to std load`
  - 0.5% (2) `G1 KM_G29_REQ_HIST stage to std load`
  - 0.5% (2) `G1 G48_REVIEW stage to std load`
  - 0.5% (2) `G1 G49 stage to std load`
  - 0.5% (2) `G1 G50 stage to std load`
  - 0.5% (2) `G1 G33_PHONE stage to std load`
  - 0.5% (2) `G1 KM_G51_G52 stage to std load`
  - 0.5% (2) `G1 KM_SF_G53_HIST stage to std load`
  - 0.5% (2) `G1 KM_SF_G54_HIST stage to std load`
  - 0.5% (2) `G1 KM_SF_G55_HIST stage to std load`
  - 0.5% (2) `G1 KM_SF_G56_HIST stage to std load`
  - 0.5% (2) `G1  Raw to stage load`
  - 0.5% (2) `G1 stage to std load`
  - 0.5% (2) `PL_File_SFMC_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_{schema}_G9_G10_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_{schema}_G11_G10_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STD_{schema}_G12_Delta_To_STD_G13`
  - 0.3% (1) `PL_File_{source}_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_{source}_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{source}_G17_G26_Daily_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{source}_G17_G26_Daily_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{source}_G17_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{source}_G17_G26_Weekly_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{source}_G17_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{source}_G17_G26_Monthly_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{source}_G17_G26_G21_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{source}_G17_G26_G21_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{subdomain}_{table}_extract`
  - 0.3% (1) `PL_File_STAGE_{subdomain}_G62`
  - 0.3% (1) `PL_File_STAGE_{subdomain}_G63`
  - 0.3% (1) `PL_File_STAGE_{subdomain}_G64_Leave`
  - 0.3% (1) `PL_MSTR_G1_{source}_Case_Delta_To_STD_Incr`
  - 0.3% (1) `PL_MSTR_G1_{source}_G70_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_G8_G9_G10_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_G8_G11_G10_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STD_CLM_G12_Delta_To_STD_G13`
  - 0.3% (1) `PL_File_CAQH_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_CAQH_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{domain}_G26_Daily_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{domain}_G26_Daily_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{domain}_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{domain}_G26_Weekly_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{domain}_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{domain}_G26_Monthly_Delta_To_STD_Incr`
  - 0.3% (1) `PL_File_STAGE_{domain}_G26_G21_ADLS_To_Delta_Incr`
  - 0.3% (1) `PL_File_STD_{domain}_G26_G21_Delta_To_STD_Incr`
  - 0.3% (1) `G1  G27_VW Raw to stage load`
  - 0.3% (1) `G1 G27_VW stage to std load`
  - 0.3% (1) `G1  KM_JC_G28 Raw to stage load`
  - 0.3% (1) `G1 KM_G29_REQ_DATA Raw to stage load`
  - 0.3% (1) `G1 KM_G29_REQ_G30 Raw to stage load`
  - 0.3% (1) `G1 LOCATION_TBL Raw to stage load`
  - 0.3% (1) `G1 NAMES Raw to stage load`
  - 0.3% (1) `G1 PER_G31_G32 Raw to stage load`
  - 0.3% (1) `G1 G33_DATA Raw to stage load`
  - 0.3% (1) `G1 POSITION_DATA Raw to stage load`
  - 0.3% (1) `G1 VALID_G34_TBL Raw to stage load`
  - 0.3% (1) `G1 G35_CD_TBL Raw to stage load`
  - 0.3% (1) `G1 G36_REASON_TBL Raw to stage load`
  - 0.3% (1) `G1 G37_TBL Raw to stage load`
  - 0.3% (1) `G1 G38_G39 Raw to stage load`
  - 0.3% (1) `G1 EMAIL_G40 Raw to stage load`
  - 0.3% (1) `G1 G41 Raw to stage load`
  - 0.3% (1) `G1 JOB Raw to stage load`
  - 0.3% (1) `G1 G42_TBL Raw to stage load`
  - 0.3% (1) `G1 G43_TBL Raw to stage load`
  - 0.3% (1) `G1 KM_G44_REVIEW Raw to stage load`
  - 0.3% (1) `G1 AUDIT_JOB Raw to stage load`
  - 0.3% (1) `G1 PERSON Raw to stage load`
  - 0.3% (1) `G1 G45_DATA_G46 Raw to stage load`
  - 0.3% (1) `G1 G40 Raw to stage load`
  - 0.3% (1) `G1 PER_G31_G47 Raw to stage load`
  - 0.3% (1) `G1 KM_G29_REQ_HIST Raw to stage load`
  - 0.3% (1) `G1 G48_REVIEW Raw to stage load`
  - 0.3% (1) `G1 G49 Raw to stage load`
  - 0.3% (1) `G1 G50 Raw to stage load`
  - 0.3% (1) `G1 G33_PHONE Raw to stage load`
  - 0.3% (1) `G1 KM_G51_G52 Raw to stage load`
  - 0.3% (1) `G1 KM_SF_G53_HIST Raw to stage load`
  - 0.3% (1) `G1 KM_SF_G54_HIST Raw to stage load`
  - 0.3% (1) `G1 KM_SF_G55_HIST Raw to stage load`
  - 0.3% (1) `G1 KM_SF_G56_HIST Raw to stage load`
  - 0.3% (1) `G1 PS_G57_G58_G59 Raw to stage load`
  - 0.3% (1) `G1 PS_G57_G58_G59 stage to std load`
  - 0.3% (1) `PL_File_STAGE_G60_G61_extract`
  - 0.3% (1) `PL_File_STAGE_G60_G62`
  - 0.3% (1) `PL_File_STAGE_G60_G63`
  - 0.3% (1) `PL_File_STAGE_G60_G64_Leave`
  - 0.3% (1) `G1_G65 stage to std load`
  - 0.3% (1) `G1_G66 stage to std load`
  - 0.3% (1) `G1_G67 stage to std load`
  - 0.3% (1) `G1_G68 stage to std load`
  - 0.3% (1) `G1_G69 stage to std load`
  - 0.3% (1) `PL_MSTR_G1_G69_Case_Delta_To_STD_Incr`
  - 0.3% (1) `PL_MSTR_G1_G69_G70_Delta_To_STD_Incr`

### DATABRICKS_NOTEBOOK_DETAILS.SEQ_NM

- values:
  - 64.6% (244) `1`
  - 2.1% (8) `2`
  - 1.1% (4) `3`
  - 1.1% (4) `38`
  - 1.1% (4) `39`
  - 0.5% (2) `4`
  - 0.5% (2) `5`
  - 0.5% (2) `6`
  - 0.5% (2) `7`
  - 0.5% (2) `8`
  - 0.5% (2) `9`
  - 0.5% (2) `10`
  - 0.5% (2) `11`
  - 0.5% (2) `12`
  - 0.5% (2) `13`
  - 0.5% (2) `14`
  - 0.5% (2) `15`
  - 0.5% (2) `16`
  - 0.5% (2) `17`
  - 0.5% (2) `18`
  - 0.5% (2) `19`
  - 0.5% (2) `20`
  - 0.5% (2) `21`
  - 0.5% (2) `22`
  - 0.5% (2) `23`
  - 0.5% (2) `24`
  - 0.5% (2) `25`
  - 0.5% (2) `26`
  - 0.5% (2) `27`
  - 0.5% (2) `28`
  - 0.5% (2) `29`
  - 0.5% (2) `30`
  - 0.5% (2) `31`
  - 0.5% (2) `32`
  - 0.5% (2) `33`
  - 0.5% (2) `34`
  - 0.5% (2) `35`
  - 0.5% (2) `36`
  - 0.5% (2) `37`
  - 0.5% (2) `40`
  - 0.5% (2) `41`
  - 0.5% (2) `42`
  - 0.5% (2) `43`
  - 0.5% (2) `44`
  - 0.5% (2) `45`
  - 0.5% (2) `46`
  - 0.5% (2) `47`
  - 0.5% (2) `48`
  - 0.5% (2) `49`
  - 0.5% (2) `50`
  - 0.5% (2) `51`
  - 0.5% (2) `52`
  - 0.5% (2) `53`
  - 0.5% (2) `54`
  - 0.5% (2) `55`
  - 0.5% (2) `56`
  - 0.5% (2) `57`
  - 0.5% (2) `58`
  - 0.5% (2) `59`
  - 0.5% (2) `60`
  - 0.5% (2) `61`
  - 0.5% (2) `62`
- patterns:
  - 64.6% (244) `1`
  - 2.1% (8) `2`
  - 1.1% (4) `3`
  - 1.1% (4) `38`
  - 1.1% (4) `39`
  - 0.5% (2) `4`
  - 0.5% (2) `5`
  - 0.5% (2) `6`
  - 0.5% (2) `7`
  - 0.5% (2) `8`
  - 0.5% (2) `9`
  - 0.5% (2) `10`
  - 0.5% (2) `11`
  - 0.5% (2) `12`
  - 0.5% (2) `13`
  - 0.5% (2) `14`
  - 0.5% (2) `15`
  - 0.5% (2) `16`
  - 0.5% (2) `17`
  - 0.5% (2) `18`
  - 0.5% (2) `19`
  - 0.5% (2) `20`
  - 0.5% (2) `21`
  - 0.5% (2) `22`
  - 0.5% (2) `23`
  - 0.5% (2) `24`
  - 0.5% (2) `25`
  - 0.5% (2) `26`
  - 0.5% (2) `27`
  - 0.5% (2) `28`
  - 0.5% (2) `29`
  - 0.5% (2) `30`
  - 0.5% (2) `31`
  - 0.5% (2) `32`
  - 0.5% (2) `33`
  - 0.5% (2) `34`
  - 0.5% (2) `35`
  - 0.5% (2) `36`
  - 0.5% (2) `37`
  - 0.5% (2) `40`
  - 0.5% (2) `41`
  - 0.5% (2) `42`
  - 0.5% (2) `43`
  - 0.5% (2) `44`
  - 0.5% (2) `45`
  - 0.5% (2) `46`
  - 0.5% (2) `47`
  - 0.5% (2) `48`
  - 0.5% (2) `49`
  - 0.5% (2) `50`
  - 0.5% (2) `51`
  - 0.5% (2) `52`
  - 0.5% (2) `53`
  - 0.5% (2) `54`
  - 0.5% (2) `55`
  - 0.5% (2) `56`
  - 0.5% (2) `57`
  - 0.5% (2) `58`
  - 0.5% (2) `59`
  - 0.5% (2) `60`
  - 0.5% (2) `61`
  - 0.5% (2) `62`

### DATABRICKS_NOTEBOOK_DETAILS.PROCESS_NAME

- values:
  - 19.6% (74) `G1  Raw to stage load`
  - 19.6% (74) `G1  stage to std load`
  - 3.2% (12) `G1_G2  stage to std load`
  - 1.6% (6) `G22_834 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `Stage Load for SFMC`
  - 1.1% (4) `G22_834 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `PL_FILE_G3_G4_G5_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_FILE_G3_G4_G5_Delta_To_G6_Incr`
  - 0.5% (2) `PL_File_STAGE_G7`
  - 0.5% (2) `PL_File_STANDARD_G7`
  - 0.5% (2) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.5% (2) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.5% (2) `Stage Load for G8 Demographics Package`
  - 0.5% (2) `Standard Load for G8 Demographics Package`
  - 0.5% (2) `Stage Load for G8 Analytics Package`
  - 0.5% (2) `Standard Load for G8 Analytics Package`
  - 0.5% (2) `Stage Load for G8 SD Individual Risk Package`
  - 0.5% (2) `Standard Load for G8 Individual Risk Package`
  - 0.5% (2) `Stage Load for G71`
  - 0.5% (2) `Standard Load for G71`
  - 0.5% (2) `Stage Load for G15 RX Claims History`
  - 0.5% (2) `Standard Load for G15 RX Claims History`
  - 0.5% (2) `G22_834 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `Stage Load for CAQH`
  - 0.5% (2) `Standard Load for CAQH`
  - 0.5% (2) `Weekly Stage Load for MI`
  - 0.5% (2) `Weekly Standard Load for MI`
  - 0.5% (2) `G22_834 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G16 834 G22 G72 Daily Stage Load`
  - 0.5% (2) `G16 834 G22 G72 Daily Standard Load`
  - 0.5% (2) `G16 834 G22 G72 Weekly Stage Load`
  - 0.5% (2) `G16 834 G22 G72 Weekly Standard Load`
  - 0.5% (2) `G16 834 G22 G72  Monthly Stage Load`
  - 0.5% (2) `G16 834 G22 G72 Monthly Standard Load`
  - 0.5% (2) `G16 834 G22 G72 G21 Stage Load`
  - 0.5% (2) `G16 834 G22 G72 G21 Standard Load`
  - 0.5% (2) `Stage Load for G60`
  - 0.5% (2) `Stage Load for G60 G62`
  - 0.5% (2) `Stage Load for G60 G63`
  - 0.5% (2) `Stage Load for G60 G64_Leave`
  - 0.5% (2) `G1_G65  stage to std load`
  - 0.5% (2) `G1_G66  stage to std load`
  - 0.5% (2) `G1_G67  stage to std load`
  - 0.5% (2) `G1_G68  stage to std load`
  - 0.5% (2) `G1_G69  stage to std load`
  - 0.5% (2) `G1_G69  Case Stage to Standard load`
  - 0.5% (2) `G1_G69 G70  Stage to Standard load`
  - 0.5% (2) `Standard Load for SFMC`
- patterns:
  - 19.6% (74) `G1  Raw to stage load`
  - 19.6% (74) `G1  stage to std load`
  - 4.5% (17) `G1_{source}  stage to std load`
  - 1.6% (6) `G22_834 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.6% (6) `G22_834 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `Stage Load for SFMC`
  - 1.1% (4) `G22_834 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 1.1% (4) `G22_834 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (3) `Stage Load for G8 {feed}`
  - 0.8% (3) `Stage Load for {source}`
  - 0.8% (3) `Standard Load for {source}`
  - 0.5% (2) `PL_FILE_G3_G4_G5_ADLS_To_Delta_Incr`
  - 0.5% (2) `PL_FILE_G3_G4_G5_Delta_To_G6_Incr`
  - 0.5% (2) `PL_File_STAGE_G7`
  - 0.5% (2) `PL_File_STANDARD_G7`
  - 0.5% (2) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.5% (2) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.5% (2) `Standard Load for {schema} {feed}`
  - 0.5% (2) `Standard Load for G8 Individual Risk Package`
  - 0.5% (2) `Stage Load for G15 RX {domain} History`
  - 0.5% (2) `Standard Load for G15 RX {domain} History`
  - 0.5% (2) `G22_834 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `Weekly Stage Load for MI`
  - 0.5% (2) `Weekly Standard Load for MI`
  - 0.5% (2) `G22_834 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `G22_834 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.5% (2) `Standard Load for SFMC`
  - 0.3% (1) `Stage Load for G8 {table} Package`
  - 0.3% (1) `{source} 834 G22 G72 Daily Stage Load`
  - 0.3% (1) `{source} 834 G22 G72 Daily Standard Load`
  - 0.3% (1) `{source} 834 G22 G72 Weekly Stage Load`
  - 0.3% (1) `{source} 834 G22 G72 Weekly Standard Load`
  - 0.3% (1) `{source} 834 G22 G72  Monthly Stage Load`
  - 0.3% (1) `{source} 834 G22 G72 Monthly Standard Load`
  - 0.3% (1) `{source} 834 G22 G72 G21 Stage Load`
  - 0.3% (1) `{source} 834 G22 G72 G21 Standard Load`
  - 0.3% (1) `Stage Load for {subdomain}`
  - 0.3% (1) `Stage Load for {subdomain} G62`
  - 0.3% (1) `Stage Load for {subdomain} G63`
  - 0.3% (1) `Stage Load for {subdomain} G64_Leave`
  - 0.3% (1) `G1_{source}  Case Stage to Standard load`
  - 0.3% (1) `G1_{source} G70  Stage to Standard load`
  - 0.3% (1) `Standard Load for G8 {feed}`
  - 0.3% (1) `Stage Load for G8 Analytics Package`
  - 0.3% (1) `Standard Load for G8 Analytics Package`
  - 0.3% (1) `Stage Load for G8 SD Individual Risk Package`
  - 0.3% (1) `Stage Load for CAQH`
  - 0.3% (1) `Standard Load for CAQH`
  - 0.3% (1) `G16 834 G22 G72 Daily Stage Load`
  - 0.3% (1) `G16 834 G22 G72 Daily Standard Load`
  - 0.3% (1) `G16 834 G22 G72 Weekly Stage Load`
  - 0.3% (1) `G16 834 G22 G72 Weekly Standard Load`
  - 0.3% (1) `G16 834 G22 G72  Monthly Stage Load`
  - 0.3% (1) `G16 834 G22 G72 Monthly Standard Load`
  - 0.3% (1) `G16 834 G22 G72 G21 Stage Load`
  - 0.3% (1) `G16 834 G22 G72 G21 Standard Load`
  - 0.3% (1) `Stage Load for G60`
  - 0.3% (1) `Stage Load for G60 G62`
  - 0.3% (1) `Stage Load for G60 G63`
  - 0.3% (1) `Stage Load for G60 G64_Leave`
  - 0.3% (1) `G1_G65  stage to std load`
  - 0.3% (1) `G1_G66  stage to std load`
  - 0.3% (1) `G1_G67  stage to std load`
  - 0.3% (1) `G1_G68  stage to std load`
  - 0.3% (1) `G1_G69  stage to std load`
  - 0.3% (1) `G1_G69  Case Stage to Standard load`
  - 0.3% (1) `G1_G69 G70  Stage to Standard load`

### DATABRICKS_NOTEBOOK_DETAILS.TGT_REFRESH_TYPE

- values:
  - 62.4% (236) `Overwrite`
  - 19.0% (72) `upsert_delete`
  - 12.7% (48) `Append`
  - 4.2% (16) `Upsert`
  - 1.1% (4) `UPSERT`
  - 0.5% (2) `Upsert_delete`
- patterns:
  - 62.4% (236) `Overwrite`
  - 19.0% (72) `upsert_delete`
  - 12.7% (48) `Append`
  - 4.2% (16) `Upsert`
  - 1.1% (4) `UPSERT`
  - 0.5% (2) `Upsert_delete`

### DATABRICKS_NOTEBOOK_DETAILS.ACTIVE_FLAG

- values:
  - 98.9% (374) `Y`
  - 1.1% (4) `N`
- patterns:
  - 98.9% (374) `Y`
  - 1.1% (4) `N`

### DATABRICKS_NOTEBOOK_DETAILS.DATABRICKS_NOTEBOOK_PATH

- values:
  - 26.5% (100) `/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 19.6% (74) `/iig/RDBMSInvokeDeltaTable_V0.1`
  - 18.0% (68) `/Workspace/G73/G16_G17_FixedWidthHandler,/Workspace/G73/FileInvokeDQDeltaTable`
  - 9.0% (34) `/Workspace/G73/G17_PIPE_DELIMITED_SEGMENT_HNDLR,/Workspace/G73/FileInvokeDQDeltaTable`
  - 8.5% (32) `/Workspace/G73/G16_G17_FixedWidthHandler,/Workspace/G73/TPL_FileInvokeDQDeltaTable`
  - 3.2% (12) `/Workspace/iig/FileInvokeDQDeltaTable_V0.1`
  - 3.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V2`
  - 3.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 2.6% (10) `/Workspace/iig/FileInvokeDQDeltaTable_V0.2`
  - 1.6% (6) `/iig/FileInvokeDQDeltaTable_V0.1`
  - 1.1% (4) `/Workspace/iig/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 1.1% (4) `/iig/G74/DeltaInvokeDQStandardDeltaTable`
  - 1.1% (4) `/Workspace/iig/G75/NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.5% (2) `/Workspace/Shared/G76_PROD_G77_SCRIPTS/G76_CODE/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 0.5% (2) `/iig/G74/DeltaInvokeDQStandardDeltaTable_V2`
  - 0.5% (2) `/iig/FileInvokeDQDeltaTable_ADP`
- patterns:
  - 26.5% (100) `/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 19.6% (74) `/iig/RDBMSInvokeDeltaTable_V0.1`
  - 18.0% (68) `/Workspace/G73/{domain}_FixedWidthHandler,/Workspace/G73/FileInvokeDQDeltaTable`
  - 9.0% (34) `/Workspace/G73/{source}_PIPE_DELIMITED_SEGMENT_HNDLR,/Workspace/G73/FileInvokeDQDeltaTable`
  - 8.5% (32) `/Workspace/G73/{domain}_FixedWidthHandler,/Workspace/G73/TPL_FileInvokeDQDeltaTable`
  - 3.2% (12) `/Workspace/iig/FileInvokeDQDeltaTable_V0.1`
  - 3.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V2`
  - 3.2% (12) `/Workspace/iig/DeltaInvokeDQStandardDeltaTable_V4`
  - 2.6% (10) `/Workspace/iig/FileInvokeDQDeltaTable_V0.2`
  - 1.6% (6) `/iig/FileInvokeDQDeltaTable_V0.1`
  - 1.1% (4) `/Workspace/iig/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 1.1% (4) `/iig/G74/DeltaInvokeDQStandardDeltaTable`
  - 1.1% (4) `/Workspace/iig/G75/NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.5% (2) `/Workspace/Shared/G76_PROD_G77_SCRIPTS/G76_CODE/G74/FileInvokeDQDeltaTable_DATAGAPS`
  - 0.5% (2) `/iig/G74/DeltaInvokeDQStandardDeltaTable_V2`
  - 0.5% (2) `/iig/FileInvokeDQDeltaTable_ADP`

### DATABRICKS_NOTEBOOK_DETAILS.DATABRICKS_NOTEBOOK_NAME

- values:
  - 29.6% (112) `DeltaInvokeDQStandardDeltaTable_V4`
  - 20.1% (76) `G16_G17_FixedWidthHandler,FileInvokeDQDeltaTable`
  - 19.6% (74) `RDBMSInvokeDeltaTable_V0.1`
  - 9.0% (34) `G17_PIPE_DELIMITED_SEGMENT_HNDLR,FileInvokeDQDeltaTable`
  - 6.3% (24) `G16_G17_FixedWidthHandler,TPL_FileInvokeDQDeltaTable`
  - 4.8% (18) `FileInvokeDQDeltaTable_V0.1`
  - 3.7% (14) `DeltaInvokeDQStandardDeltaTable_V2`
  - 2.6% (10) `FileInvokeDQDeltaTable_V0.2`
  - 1.6% (6) `FileInvokeDQDeltaTable_DATAGAPS`
  - 1.1% (4) `DeltaInvokeDQStandardDeltaTable`
  - 1.1% (4) `NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.5% (2) `FileInvokeDQDeltaTable_ADP`
- patterns:
  - 29.6% (112) `DeltaInvokeDQStandardDeltaTable_V4`
  - 20.1% (76) `{domain}_FixedWidthHandler,FileInvokeDQDeltaTable`
  - 19.6% (74) `RDBMSInvokeDeltaTable_V0.1`
  - 9.0% (34) `{source}_PIPE_DELIMITED_SEGMENT_HNDLR,FileInvokeDQDeltaTable`
  - 6.3% (24) `{domain}_FixedWidthHandler,TPL_FileInvokeDQDeltaTable`
  - 4.8% (18) `FileInvokeDQDeltaTable_V0.1`
  - 3.7% (14) `DeltaInvokeDQStandardDeltaTable_V2`
  - 2.6% (10) `FileInvokeDQDeltaTable_V0.2`
  - 1.6% (6) `FileInvokeDQDeltaTable_DATAGAPS`
  - 1.1% (4) `DeltaInvokeDQStandardDeltaTable`
  - 1.1% (4) `NB_FileInvokeDQDeltaTable_WF_V1`
  - 0.5% (2) `FileInvokeDQDeltaTable_ADP`

### DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_NAME

- values:
  - 0.5% (182) `PL_File_STAGE_G60_G61_extract`
  - 0.5% (182) `PL_File_STAGE_G60_G62`
  - 0.5% (182) `PL_File_STAGE_G60_G63`
  - 0.5% (182) `PL_File_STAGE_G60_G64_Leave`
  - 0.5% (182) `PL_File_STD_G1_G2_G78`
  - 0.5% (182) `PL_File_STD_G1_G2_G79`
  - 0.5% (182) `PL_File_STD_G1_G2_G80`
  - 0.5% (182) `PL_MSTR_G1_G66_Delta_To_STD_Incr`
  - 0.5% (182) `PL_MSTR_G1_G67_Delta_To_STD_Incr`
  - 0.5% (182) `PL_MSTR_G1_G68_Delta_To_STD_Incr`
  - 0.5% (182) `PL_MSTR_G1_G69_Delta_To_STD_Incr`
  - 0.5% (182) `PL_MSTR_G1_G69_Case_Delta_To_STD_Incr`
  - 0.5% (182) `PL_MSTR_G1_G69_G70_Delta_To_STD_Incr`
  - 0.5% (182) `PL_File_STD_G1_G2_G81`
  - 0.5% (182) `PL_FILE_STD_G1_G2_G82`
  - 0.5% (182) `PL_File_STD_G1_G2_G83`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G27_VW`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G27_VW`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PS_KM_JC_G28`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PS_KM_JC_G28`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_DATA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_DATA`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_G30`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_G30`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_LOCATION_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_LOCATION_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_NAMES`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_NAMES`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G32`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PER_G31_G32`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G33_DATA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G33_DATA`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_POSITION_DATA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_POSITION_DATA`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_VALID_G34_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_VALID_G34_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G35_CD_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G35_CD_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G36_REASON_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G36_REASON_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G37_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G37_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G38_G39`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G38_G39`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_EMAIL_G40`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_EMAIL_G40`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G41`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G41`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_JOB`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_JOB`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G42_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G42_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G43_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G43_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G44_REVIEW`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G44_REVIEW`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_AUDIT_JOB`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_AUDIT_JOB`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PERSON`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PERSON`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G45_DATA_G46`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G45_DATA_G46`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G40`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G40`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G47`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PER_G31_G47`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G48_REVIEW`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G48_REVIEW`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G49`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G49`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G50`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G50`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G33_PHONE`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G33_PHONE`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G51_G52`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G51_G52`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G53_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G53_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G54_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G54_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G55_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G55_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G56_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G56_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PS_G57_G58_G59`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PS_G57_G58_G59`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6`
  - 0.5% (182) `PL_MSTR_G1_G65_Delta_To_STD_Incr`
  - 0.5% (182) `PL_Mstr_G60_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.5% (182) `PL_Mstr_G60_G62_G63_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.5% (182) `PL_Mstr_G60_G64_Leave_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.5% (182) `PL_MSTR_G1_G66_RAW_STG_INGESTION`
  - 0.5% (182) `PL_MSTR_G1_G67_RAW_STG_INGESTION`
  - 0.5% (182) `PL_MSTR_G1_G68_RAW_STG_INGESTION`
  - 0.5% (182) `PL_MSTR_G1_G69_RAW_STG_INGESTION`
  - 0.5% (182) `PL_MSTR_G1_G2_RAW_STG_INGESTION`
  - 0.5% (182) `PL_MSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.5% (182) `PL_MSTR_G1_G65_RAW_STG_INGESTION`
  - 0.5% (182) `Pl_Gmstr_G60_Regular_File_Load`
  - 0.5% (182) `Pl_Gmstr_G60_G62_G63_Regular_File_Load`
  - 0.5% (182) `Pl_Gmstr_G60_G64_Leave_Regular_File_Load`
  - 0.5% (182) `PL_GMSTR_G1_G66_FILE_RAW_TO_STG_STD_DLY`
  - 0.5% (182) `PL_GMSTR_G1_G67_FILE_RAW_TO_STG_STD_G85`
  - 0.5% (182) `PL_GMSTR_G1_G68_DLY_STG_INGESTION`
  - 0.5% (182) `PL_GMSTR_G1_G69_DLY_STG_INGESTION`
  - 0.5% (182) `PL_GMSTR_G1_G2_DLY_STG_INGESTION`
  - 0.5% (182) `PL_GMSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.5% (182) `PL_GMSTR_G1_G65_FILE_RAW_TO_STG_STD_MTH`
  - 0.4% (158) `Pl_File_G16_G17_0100_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0500_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0530_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0540_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0100_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0500_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0530_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0540_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2600_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2600_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_6400_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_6400_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G18_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G18_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G19_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G19_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2100_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2100_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_5400_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0550_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0550_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2400_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2400_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0900_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0900_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_1200_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_1200_Weekly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_1200_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7100_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7100_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7200_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7200_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7700_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7700_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G20_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G20_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2100_G21_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0100_Daily_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0100_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0500_Daily_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0500_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0530_Daily_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0530_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0540_Daily_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0540_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0550_Daily_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0550_Monthly_G23_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_5400_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_1200_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_1200_Weekly_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_6400_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_6400_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0100_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0500_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0530_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0540_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_0550_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2600_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_2600_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7200_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7700_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_7700_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `WF_CHLD_FILE_STG_CAQH`
  - 0.4% (158) `WF_CHLD_FILE_STD_CAQH`
  - 0.4% (158) `WF_CHLD_FILE_STG_MI_TPL`
  - 0.4% (158) `WF_CHLD_FILE_STD_MI_TPL`
  - 0.4% (158) `Pl_File_G16_G17_G25_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G25_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_G25_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_5420_Daily_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `Pl_File_G16_G17_5420_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.4% (158) `PL_File_STAGE_G16_G17_G26_Daily_ADLS_To_Delta_Incr`
  - 0.4% (158) `PL_File_STD_G16_G17_G26_Daily_Delta_To_STD_Incr`
  - 0.4% (158) `PL_File_STAGE_G16_G17_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.4% (158) `PL_File_STD_G16_G17_G26_Weekly_Delta_To_STD_Incr`
  - 0.4% (158) `PL_File_STAGE_G16_G17_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.4% (158) `PL_File_STD_G16_G17_G26_Monthly_Delta_To_STD_Incr`
  - 0.4% (158) `PL_File_STAGE_G16_G17_G26_G21_ADLS_To_Delta_Incr`
  - 0.4% (158) `PL_File_STD_G16_G17_G26_G21_Delta_To_STD_Incr`
  - 0.4% (158) `PL_Mstr_G16_G17_G86_Incremental_Load_Pipeline`
  - 0.4% (158) `WF_MSTR_FILE_RAW_STD_CAQH_ALL_DLY`
  - 0.4% (158) `WF_MSTR_FILE_RAW_STD_MI_TPL_ALL_DLY`
  - 0.4% (158) `PL_Mstr_G16_G17_G26_Daily_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (158) `PL_Mstr_G16_G17_G26_Weekly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (158) `PL_Mstr_G16_G17_G26_Monthly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (158) `PL_Mstr_G16_G17_G26_G21_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (158) `PL_Gmstr_G16_G17_Incremental_Load_Pipeline`
  - 0.4% (158) `PL_GMSTR_MBR_TPL_ALL_G85`
  - 0.4% (158) `PL_GMSTR_G16_G17_G26_ALL_DLY`
  - 0.4% (158) `PL_GMSTR_G16_G17_G26_ALL_G85`
  - 0.4% (158) `PL_GMSTR_G16_G17_G26_ALL_G87`
  - 0.4% (158) `PL_GMSTR_G16_G17_G26_ALL_G88`
  - 0.1% (32) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G91_G92`
  - 0.1% (32) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G93_G94_G92`
  - 0.1% (32) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G95_pct_mo_de`
  - 0.1% (32) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_data_G92`
  - 0.1% (32) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G96_G92`
  - 0.1% (32) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G91_G92`
  - 0.1% (32) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G93_G94_G92`
  - 0.1% (32) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G95_pct_mo_de`
  - 0.1% (32) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_data_G92`
  - 0.1% (32) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G96_G92`
  - 0.1% (32) `PL_File_STAGE_G3_G4_G5`
  - 0.1% (32) `PL_File_STANDARD_G3_G4_G5`
  - 0.1% (32) `PL_File_STAGE_G7`
  - 0.1% (32) `PL_File_STANDARD_G7`
  - 0.1% (32) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.1% (32) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.1% (32) `PL_Mstr_G97_G89_Raw_Stage_Regular_Load_Pipeline`
  - 0.1% (32) `PL_Mstr_G3_G4_G5_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (32) `PL_Mstr_G7_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (32) `PL_Mstr_G3_G4_G5_Inbound_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (32) `Pl_Gmstr_G89_Regular_Load`
  - 0.1% (32) `Pl_Gmstr_G3_G4_G5_Regular_File_Load`
  - 0.1% (32) `Pl_Gmstr_G7_Regular_File_Load`
  - 0.1% (32) `Pl_Gmstr_G3_G4_G5_Inbound_Regular_File_Load`
  - 0.0% (12) `PL_File_G8_G9_G10_ADLS_To_Delta_Incr`
  - 0.0% (12) `PL_File_G8_G9_G10_Delta_To_STD_Incr`
  - 0.0% (12) `PL_File_G8_G11_G10_ADLS_To_Delta_Incr`
  - 0.0% (12) `PL_File_G8_G11_G10_Delta_To_STD_Incr`
  - 0.0% (12) `PL_File_G8_SD_IND_RISK_ADLS_To_Delta_Incr`
  - 0.0% (12) `PL_File_G8_SD_IND_RISK_Delta_To_STD_Incr`
  - 0.0% (12) `PL_MSTR_G8_ALL_MTH`
  - 0.0% (12) `PL_GMSTR_G8_ALL_MTH`
  - 0.0% (6) `PL_File_SFMC_ADLS_To_Delta_Incr`
  - 0.0% (6) `PL_File_SFMC_Delta_To_STD_Incr`
  - 0.0% (6) `PL_MSTR_MBR_OUTREACH_ALL_DLY`
  - 0.0% (6) `PL_GMSTR_MBR_OUTREACH_ALL_DLY`
  - 0.0% (4) `PL_File_CLM_G12_G13_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_CLM_G12_G13_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_CLM_G12_G13_RAW_TO_STD`
  - 0.0% (4) `PL_GMSTR_CLM_G12_G13_ALL_G98`
  - 0.0% (4) `PL_File_STAGE_G14_G15_ADLS_To_Delta_G13`
  - 0.0% (4) `PL_File_STD_G14_G15_Delta_To_STD_G13`
  - 0.0% (4) `PL_MSTR_G14_G15_HIST_DLY`
  - 0.0% (4) `PL_GMSTR_G14_G15_HIST_DLY`
- patterns:
  - 17.2% (6150) `Pl_File_G16_{table}_Regular_ADLS_To_Delta_Incr`
  - 6.6% (2368) `Pl_File_G16_{table}_TPL_ADLS_To_Delta_Incr`
  - 4.2% (1500) `Pl_File_G16_{table}_G23_ADLS_To_Delta_Incr`
  - 0.9% (328) `Pl_File_{source}_{table}_Regular_ADLS_To_Delta_Incr`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_DATA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_DATA`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_G30`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_G30`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_LOCATION_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_LOCATION_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_NAMES`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_NAMES`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G32`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PER_G31_G32`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G33_DATA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G33_DATA`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_POSITION_DATA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_POSITION_DATA`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_VALID_G34_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_VALID_G34_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G35_CD_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G35_CD_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G36_REASON_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G36_REASON_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G37_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G37_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G38_G39`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G38_G39`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_EMAIL_G40`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_EMAIL_G40`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G41`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G41`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_JOB`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_JOB`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G42_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G42_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G43_TBL`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G43_TBL`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G44_REVIEW`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G44_REVIEW`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_AUDIT_JOB`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_AUDIT_JOB`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PERSON`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PERSON`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G45_DATA_G46`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G45_DATA_G46`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G40`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G40`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G47`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_PER_G31_G47`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G48_REVIEW`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G48_REVIEW`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G49`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G49`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G50`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G50`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_G33_PHONE`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_G33_PHONE`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_G51_G52`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_G51_G52`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G53_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G53_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G54_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G54_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G55_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G55_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G56_HIST`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6_KM_SF_G56_HIST`
  - 0.5% (182) `PL_G84_G1_ADLS_TO_DELTA`
  - 0.5% (182) `PL_G84_G1_DELTA_TO_G6`
  - 0.5% (182) `PL_MSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.5% (182) `PL_GMSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.5% (181) `PL_MSTR_G1_G66_Delta_To_STD_Incr`
  - 0.5% (181) `PL_MSTR_G1_G67_Delta_To_STD_Incr`
  - 0.5% (181) `PL_MSTR_G1_G68_Delta_To_STD_Incr`
  - 0.5% (181) `PL_MSTR_G1_G65_Delta_To_STD_Incr`
  - 0.5% (181) `PL_MSTR_G1_G66_RAW_STG_INGESTION`
  - 0.5% (181) `PL_MSTR_G1_G67_RAW_STG_INGESTION`
  - 0.5% (181) `PL_MSTR_G1_G68_RAW_STG_INGESTION`
  - 0.5% (181) `PL_MSTR_G1_G65_RAW_STG_INGESTION`
  - 0.5% (181) `PL_GMSTR_G1_G66_FILE_RAW_TO_STG_STD_DLY`
  - 0.5% (181) `PL_GMSTR_G1_G67_FILE_RAW_TO_STG_STD_G85`
  - 0.5% (181) `PL_GMSTR_G1_G68_DLY_STG_INGESTION`
  - 0.5% (181) `PL_GMSTR_G1_G65_FILE_RAW_TO_STG_STD_MTH`
  - 0.5% (179) `PL_MSTR_G1_G69_Delta_To_STD_Incr`
  - 0.5% (179) `PL_MSTR_G1_G69_Case_Delta_To_STD_Incr`
  - 0.5% (179) `PL_MSTR_G1_G69_G70_Delta_To_STD_Incr`
  - 0.5% (179) `PL_MSTR_G1_G69_RAW_STG_INGESTION`
  - 0.5% (179) `PL_GMSTR_G1_G69_DLY_STG_INGESTION`
  - 0.5% (178) `PL_File_STAGE_G60_G61_extract`
  - 0.5% (178) `PL_File_STAGE_G60_G62`
  - 0.5% (178) `PL_File_STAGE_G60_G63`
  - 0.5% (178) `PL_File_STAGE_G60_G64_Leave`
  - 0.5% (178) `PL_G84_G1_ADLS_TO_DELTA_G27_VW`
  - 0.5% (178) `PL_G84_G1_DELTA_TO_G6_G27_VW`
  - 0.5% (178) `PL_G84_G1_ADLS_TO_DELTA_PS_KM_JC_G28`
  - 0.5% (178) `PL_G84_G1_DELTA_TO_G6_PS_KM_JC_G28`
  - 0.5% (178) `PL_G84_G1_ADLS_TO_DELTA_PS_G57_G58_G59`
  - 0.5% (178) `PL_G84_G1_DELTA_TO_G6_PS_G57_G58_G59`
  - 0.5% (178) `PL_Mstr_G60_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.5% (178) `PL_Mstr_G60_G62_G63_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.5% (178) `PL_Mstr_G60_G64_Leave_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.5% (178) `Pl_Gmstr_G60_Regular_File_Load`
  - 0.5% (178) `Pl_Gmstr_G60_G62_G63_Regular_File_Load`
  - 0.5% (178) `Pl_Gmstr_G60_G64_Leave_Regular_File_Load`
  - 0.4% (156) `WF_CHLD_FILE_STG_CAQH`
  - 0.4% (156) `WF_CHLD_FILE_STD_CAQH`
  - 0.4% (156) `WF_CHLD_FILE_STG_MI_TPL`
  - 0.4% (156) `WF_CHLD_FILE_STD_MI_TPL`
  - 0.4% (156) `WF_MSTR_FILE_RAW_STD_CAQH_ALL_DLY`
  - 0.4% (156) `WF_MSTR_FILE_RAW_STD_MI_TPL_ALL_DLY`
  - 0.4% (156) `PL_GMSTR_MBR_TPL_ALL_G85`
  - 0.4% (144) `PL_File_STAGE_{domain}_G26_Daily_ADLS_To_Delta_Incr`
  - 0.4% (144) `PL_File_STD_{domain}_G26_Daily_Delta_To_STD_Incr`
  - 0.4% (144) `PL_File_STAGE_{domain}_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.4% (144) `PL_File_STD_{domain}_G26_Weekly_Delta_To_STD_Incr`
  - 0.4% (144) `PL_File_STAGE_{domain}_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.4% (144) `PL_File_STD_{domain}_G26_Monthly_Delta_To_STD_Incr`
  - 0.4% (144) `PL_File_STAGE_{domain}_G26_G21_ADLS_To_Delta_Incr`
  - 0.4% (144) `PL_File_STD_{domain}_G26_G21_Delta_To_STD_Incr`
  - 0.4% (144) `PL_Mstr_{domain}_G86_Incremental_Load_Pipeline`
  - 0.4% (144) `PL_Mstr_{domain}_G26_Daily_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (144) `PL_Mstr_{domain}_G26_Weekly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (144) `PL_Mstr_{domain}_G26_Monthly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (144) `PL_Mstr_{domain}_G26_G21_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.4% (144) `PL_Gmstr_{domain}_Incremental_Load_Pipeline`
  - 0.4% (144) `PL_GMSTR_{domain}_G26_ALL_DLY`
  - 0.4% (144) `PL_GMSTR_{domain}_G26_ALL_G85`
  - 0.4% (144) `PL_GMSTR_{domain}_G26_ALL_G87`
  - 0.4% (144) `PL_GMSTR_{domain}_G26_ALL_G88`
  - 0.4% (128) `Pl_File_{source}_{table}_TPL_ADLS_To_Delta_Incr`
  - 0.3% (104) `PL_MSTR_G1_{source}_RAW_STG_INGESTION`
  - 0.3% (101) `PL_GMSTR_G1_{source}_DLY_STG_INGESTION`
  - 0.3% (97) `PL_File_STD_G1_{source}_G78`
  - 0.3% (97) `PL_File_STD_G1_{source}_G79`
  - 0.3% (97) `PL_File_STD_G1_{source}_G80`
  - 0.3% (97) `PL_File_STD_G1_{source}_G81`
  - 0.3% (97) `PL_FILE_STD_G1_{source}_G82`
  - 0.3% (97) `PL_File_STD_G1_{source}_G83`
  - 0.2% (85) `PL_File_STD_G1_G2_G78`
  - 0.2% (85) `PL_File_STD_G1_G2_G79`
  - 0.2% (85) `PL_File_STD_G1_G2_G80`
  - 0.2% (85) `PL_File_STD_G1_G2_G81`
  - 0.2% (85) `PL_FILE_STD_G1_G2_G82`
  - 0.2% (85) `PL_File_STD_G1_G2_G83`
  - 0.2% (85) `PL_MSTR_G1_G2_RAW_STG_INGESTION`
  - 0.2% (85) `PL_GMSTR_G1_G2_DLY_STG_INGESTION`
  - 0.2% (80) `Pl_File_{source}_{table}_G23_ADLS_To_Delta_Incr`
  - 0.1% (32) `PL_File_STAGE_G3_G4_G5`
  - 0.1% (32) `PL_File_STANDARD_G3_G4_G5`
  - 0.1% (32) `PL_File_STAGE_G7`
  - 0.1% (32) `PL_File_STANDARD_G7`
  - 0.1% (32) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.1% (32) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.1% (32) `PL_Mstr_G97_G89_Raw_Stage_Regular_Load_Pipeline`
  - 0.1% (32) `PL_Mstr_G3_G4_G5_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (32) `PL_Mstr_G7_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (32) `PL_Mstr_G3_G4_G5_Inbound_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (32) `Pl_Gmstr_G89_Regular_Load`
  - 0.1% (32) `Pl_Gmstr_G3_G4_G5_Regular_File_Load`
  - 0.1% (32) `Pl_Gmstr_G7_Regular_File_Load`
  - 0.1% (32) `Pl_Gmstr_G3_G4_G5_Inbound_Regular_File_Load`
  - 0.1% (32) `Pl_File_G16_{table}_{subdomain}_ADLS_To_Delta_Incr`
  - 0.1% (20) `Pl_File_Based_Regular_Load_RAW_G89_db_104_{domain}_G91_G92`
  - 0.1% (20) `Pl_File_Based_Regular_Load_RAW_G89_db_104_{domain}_G93_G94_G92`
  - 0.1% (20) `Pl_File_Based_Regular_Load_RAW_G89_db_104_{domain}_G95_pct_mo_de`
  - 0.1% (20) `Pl_File_Based_Regular_Load_RAW_G89_db_104_{domain}_data_G92`
  - 0.1% (20) `Pl_File_Based_Regular_Load_RAW_G89_db_104_{domain}_G96_G92`
  - 0.1% (20) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_{domain}_G91_G92`
  - 0.1% (20) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_{domain}_G93_G94_G92`
  - 0.1% (20) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_{domain}_G95_pct_mo_de`
  - 0.1% (20) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_{domain}_data_G92`
  - 0.1% (20) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_{domain}_G96_G92`
  - 0.0% (12) `PL_G84_G1_ADLS_TO_DELTA_{table}`
  - 0.0% (12) `PL_G84_G1_DELTA_TO_G6_{table}`
  - 0.0% (10) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G91_G92`
  - 0.0% (10) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G93_G94_G92`
  - 0.0% (10) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G95_pct_mo_de`
  - 0.0% (10) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_data_G92`
  - 0.0% (10) `Pl_File_Based_Regular_Load_RAW_G89_db_104_G90_G96_G92`
  - 0.0% (10) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G91_G92`
  - 0.0% (10) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G93_G94_G92`
  - 0.0% (10) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G95_pct_mo_de`
  - 0.0% (10) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_data_G92`
  - 0.0% (10) `Pl_File_Based_Regular_Load_STAGE_G89_db_104_G90_G96_G92`
  - 0.0% (10) `PL_File_G8_G9_G10_ADLS_To_Delta_Incr`
  - 0.0% (10) `PL_File_G8_G9_G10_Delta_To_STD_Incr`
  - 0.0% (10) `PL_File_G8_G11_G10_ADLS_To_Delta_Incr`
  - 0.0% (10) `PL_File_G8_G11_G10_Delta_To_STD_Incr`
  - 0.0% (10) `PL_File_G8_SD_IND_RISK_ADLS_To_Delta_Incr`
  - 0.0% (10) `PL_File_G8_SD_IND_RISK_Delta_To_STD_Incr`
  - 0.0% (10) `PL_MSTR_G8_ALL_MTH`
  - 0.0% (10) `PL_GMSTR_G8_ALL_MTH`
  - 0.0% (8) `PL_File_STAGE_{source}_G17_G26_Daily_ADLS_To_Delta_Incr`
  - 0.0% (8) `PL_File_STD_{source}_G17_G26_Daily_Delta_To_STD_Incr`
  - 0.0% (8) `PL_File_STAGE_{source}_G17_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.0% (8) `PL_File_STD_{source}_G17_G26_Weekly_Delta_To_STD_Incr`
  - 0.0% (8) `PL_File_STAGE_{source}_G17_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.0% (8) `PL_File_STD_{source}_G17_G26_Monthly_Delta_To_STD_Incr`
  - 0.0% (8) `PL_File_STAGE_{source}_G17_G26_G21_ADLS_To_Delta_Incr`
  - 0.0% (8) `PL_File_STD_{source}_G17_G26_G21_Delta_To_STD_Incr`
  - 0.0% (8) `PL_Mstr_{source}_G17_G86_Incremental_Load_Pipeline`
  - 0.0% (8) `PL_Mstr_{source}_G17_G26_Daily_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (8) `PL_Mstr_{source}_G17_G26_Weekly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (8) `PL_Mstr_{source}_G17_G26_Monthly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (8) `PL_Mstr_{source}_G17_G26_G21_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (8) `PL_Gmstr_{source}_G17_Incremental_Load_Pipeline`
  - 0.0% (8) `PL_GMSTR_{source}_G17_G26_ALL_DLY`
  - 0.0% (8) `PL_GMSTR_{source}_G17_G26_ALL_G85`
  - 0.0% (8) `PL_GMSTR_{source}_G17_G26_ALL_G87`
  - 0.0% (8) `PL_GMSTR_{source}_G17_G26_ALL_G88`
  - 0.0% (7) `PL_MSTR_G1_{source}_Delta_To_STD_Incr`
  - 0.0% (6) `PL_File_SFMC_ADLS_To_Delta_Incr`
  - 0.0% (6) `PL_File_SFMC_Delta_To_STD_Incr`
  - 0.0% (5) `PL_MSTR_MBR_{subdomain}_ALL_DLY`
  - 0.0% (5) `PL_GMSTR_MBR_{subdomain}_ALL_DLY`
  - 0.0% (5) `Pl_File_Based_Regular_Load_RAW_G89_{subdomain}`
  - 0.0% (5) `Pl_File_Based_Regular_Load_STAGE_G89_{subdomain}`
  - 0.0% (5) `Pl_File_Based_Regular_Load_RAW_G89_{table}`
  - 0.0% (5) `Pl_File_Based_Regular_Load_STAGE_G89_{table}`
  - 0.0% (4) `PL_File_STAGE_{source}_G15_ADLS_To_Delta_G13`
  - 0.0% (4) `PL_File_STD_{source}_G15_Delta_To_STD_G13`
  - 0.0% (4) `PL_MSTR_{source}_G15_HIST_DLY`
  - 0.0% (4) `PL_GMSTR_{source}_G15_HIST_DLY`
  - 0.0% (4) `PL_File_STAGE_G16_G17_G26_Daily_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G16_G17_G26_Daily_Delta_To_STD_Incr`
  - 0.0% (4) `PL_File_STAGE_G16_G17_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G16_G17_G26_Weekly_Delta_To_STD_Incr`
  - 0.0% (4) `PL_File_STAGE_G16_G17_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G16_G17_G26_Monthly_Delta_To_STD_Incr`
  - 0.0% (4) `PL_File_STAGE_G16_G17_G26_G21_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G16_G17_G26_G21_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G16_G17_G86_Incremental_Load_Pipeline`
  - 0.0% (4) `PL_Mstr_G16_G17_G26_Daily_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (4) `PL_Mstr_G16_G17_G26_Weekly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (4) `PL_Mstr_G16_G17_G26_Monthly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (4) `PL_Mstr_G16_G17_G26_G21_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (4) `PL_Gmstr_G16_G17_Incremental_Load_Pipeline`
  - 0.0% (4) `PL_GMSTR_G16_G17_G26_ALL_DLY`
  - 0.0% (4) `PL_GMSTR_G16_G17_G26_ALL_G85`
  - 0.0% (4) `PL_GMSTR_G16_G17_G26_ALL_G87`
  - 0.0% (4) `PL_GMSTR_G16_G17_G26_ALL_G88`
  - 0.0% (4) `PL_File_STAGE_{subdomain}_G62`
  - 0.0% (4) `PL_File_STAGE_{subdomain}_G63`
  - 0.0% (4) `PL_File_STAGE_{subdomain}_G64_Leave`
  - 0.0% (4) `PL_Mstr_{subdomain}_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_Mstr_{subdomain}_G62_G63_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_Mstr_{subdomain}_G64_Leave_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `Pl_Gmstr_{subdomain}_Regular_File_Load`
  - 0.0% (4) `Pl_Gmstr_{subdomain}_G62_G63_Regular_File_Load`
  - 0.0% (4) `Pl_Gmstr_{subdomain}_G64_Leave_Regular_File_Load`
  - 0.0% (3) `PL_File_CLM_G12_G13_ADLS_To_Delta_Incr`
  - 0.0% (3) `PL_File_CLM_G12_G13_Delta_To_STD_Incr`
  - 0.0% (3) `PL_MSTR_CLM_G12_G13_RAW_TO_STD`
  - 0.0% (3) `PL_GMSTR_CLM_G12_G13_ALL_G98`
  - 0.0% (3) `PL_File_STAGE_{subdomain}_G61_extract`
  - 0.0% (3) `PL_MSTR_G1_{source}_Case_Delta_To_STD_Incr`
  - 0.0% (3) `PL_MSTR_G1_{source}_G70_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_{schema}_G9_G10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_{schema}_G9_G10_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_{schema}_G11_G10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_{schema}_G11_G10_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_{schema}_SD_IND_RISK_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_{schema}_SD_IND_RISK_Delta_To_STD_Incr`
  - 0.0% (2) `PL_MSTR_{schema}_ALL_MTH`
  - 0.0% (2) `PL_GMSTR_{schema}_ALL_MTH`
  - 0.0% (2) `WF_CHLD_FILE_STG_{source}`
  - 0.0% (2) `WF_CHLD_FILE_STD_{source}`
  - 0.0% (2) `WF_MSTR_FILE_RAW_STD_{source}_ALL_DLY`
  - 0.0% (2) `WF_CHLD_FILE_STG_MI_{subdomain}`
  - 0.0% (2) `WF_CHLD_FILE_STD_MI_{subdomain}`
  - 0.0% (2) `WF_MSTR_FILE_RAW_STD_MI_{subdomain}_ALL_DLY`
  - 0.0% (2) `PL_GMSTR_MBR_{subdomain}_ALL_G85`
  - 0.0% (2) `PL_File_STAGE_G16_{source}_G26_Daily_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STD_G16_{source}_G26_Daily_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_STAGE_G16_{source}_G26_Weekly_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STD_G16_{source}_G26_Weekly_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_STAGE_G16_{source}_G26_Monthly_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STD_G16_{source}_G26_Monthly_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_STAGE_G16_{source}_G26_G21_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STD_G16_{source}_G26_G21_Delta_To_STD_Incr`
  - 0.0% (2) `PL_Mstr_G16_{source}_G86_Incremental_Load_Pipeline`
  - 0.0% (2) `PL_Mstr_G16_{source}_G26_Daily_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (2) `PL_Mstr_G16_{source}_G26_Weekly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (2) `PL_Mstr_G16_{source}_G26_Monthly_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (2) `PL_Mstr_G16_{source}_G26_G21_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (2) `PL_Gmstr_G16_{source}_Incremental_Load_Pipeline`
  - 0.0% (2) `PL_GMSTR_G16_{source}_G26_ALL_DLY`
  - 0.0% (2) `PL_GMSTR_G16_{source}_G26_ALL_G85`
  - 0.0% (2) `PL_GMSTR_G16_{source}_G26_ALL_G87`
  - 0.0% (2) `PL_GMSTR_G16_{source}_G26_ALL_G88`
  - 0.0% (1) `PL_File_{schema}_G12_G13_ADLS_To_Delta_Incr`
  - 0.0% (1) `PL_File_{schema}_G12_G13_Delta_To_STD_Incr`
  - 0.0% (1) `PL_MSTR_{schema}_G12_G13_RAW_TO_STD`
  - 0.0% (1) `PL_GMSTR_{schema}_G12_G13_ALL_G98`
  - 0.0% (1) `PL_File_STAGE_{subdomain}_{table}_extract`
  - 0.0% (1) `PL_GMSTR_G1_{source}_FILE_RAW_TO_STG_STD_MTH`
  - 0.0% (1) `PL_GMSTR_G1_{source}_FILE_RAW_TO_STG_STD_DLY`
  - 0.0% (1) `PL_GMSTR_G1_{source}_FILE_RAW_TO_STG_STD_G85`
  - 0.0% (1) `PL_MSTR_{schema}_{subdomain}_ALL_DLY`
  - 0.0% (1) `PL_GMSTR_{schema}_{subdomain}_ALL_DLY`

### DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_DESCRIPTION

- values:
  - 18.9% (6734) `G1 Stage Load`
  - 18.9% (6734) `G1 Standard Load`
  - 1.3% (474) `G16_G17 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.9% (316) `G16_G17 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (182) `G60 G61_extract File Pipeline Regular Load to Stage`
  - 0.5% (182) `G60 G62_G63 G99_G62 File Pipeline Regular Load to Stage`
  - 0.5% (182) `G60 G62_G63 G99_G63 File Pipeline Regular Load to Stage`
  - 0.5% (182) `G60 G100_G64_Leave File Pipeline Regular Load to Stage`
  - 0.5% (182) `G1_G2 G78 Regular STANDARD Load`
  - 0.5% (182) `G1_G2 G79 Regular STANDARD Load`
  - 0.5% (182) `G1_G2 G80 Regular STANDARD Load`
  - 0.5% (182) `G1 G66 Regular STANDARD Load`
  - 0.5% (182) `G1 G67 Regular STANDARD Load`
  - 0.5% (182) `G1 G68 Regular STANDARD Load`
  - 0.5% (182) `G1 G69 Regular STANDARD Load`
  - 0.5% (182) `G1 G69 Case Regular STANDARD Load`
  - 0.5% (182) `G1 G69 G70 Regular STANDARD Load`
  - 0.5% (182) `G1_G2 G81 Regular STANDARD Load`
  - 0.5% (182) `G1_G2 G82 Regular STANDARD Load`
  - 0.5% (182) `G1_G2 G83 Regular STANDARD Load`
  - 0.5% (182) `G1 G65 Regular STANDARD Load`
  - 0.5% (182) `G60 Master Pipeline for RAW to Stage Regular load`
  - 0.5% (182) `G60 G62_G63 Master Pipeline for RAW to Stage Regular load`
  - 0.5% (182) `G60 G100_G64_Leave Master Pipeline for RAW to Stage Regular load`
  - 0.5% (182) `G1 G66 RAW to Stage Regular load`
  - 0.5% (182) `G1 G67 RAW to Stage Regular load`
  - 0.5% (182) `G1 G68 RAW to Stage Regular load`
  - 0.5% (182) `G1 G69 RAW to Stage Regular load`
  - 0.5% (182) `G1_G2 Master Pipeline for RAW to Stage Regular load`
  - 0.5% (182) `G1 Master Pipeline`
  - 0.5% (182) `G1 G65 RAW to Stage Regular load`
  - 0.5% (182) `G60 Regular Load Grand Master Pipeline`
  - 0.5% (182) `G60 G62_G63 Regular Load Grand Master Pipeline`
  - 0.5% (182) `G60 G100_G64_Leave Regular Load Grand Master Pipeline`
  - 0.5% (182) `GMSTR_G1_G66_ONPREM_STG_INGESTION`
  - 0.5% (182) `GMSTR_G1_G67_ONPREM_STG_INGESTION`
  - 0.5% (182) `GMSTR_G1_G68_ONPREM_STG_INGESTION`
  - 0.5% (182) `GMSTR_G1_G69_ONPREM_STG_INGESTION`
  - 0.5% (182) `GMSTR_G1_G2_ONPREM_STG_INGESTION`
  - 0.5% (182) `G1 Grand Master Pipeline`
  - 0.5% (182) `GMSTR_G1_G65_ONPREM_STG_INGESTION`
  - 0.4% (158) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (158) `G16_G17 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `CAQH TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.4% (158) `CAQH TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.4% (158) `MI TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.4% (158) `MI TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.4% (158) `G16_G17 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16_G17 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (158) `G16 834 G22 G72 Daily File Pipeline Regular Load to Stage`
  - 0.4% (158) `G16 834 G22 G72 Daily File Pipeline Regular Load to Standard`
  - 0.4% (158) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Stage`
  - 0.4% (158) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Standard`
  - 0.4% (158) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Stage`
  - 0.4% (158) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Standard`
  - 0.4% (158) `G16 834 G22 G72 G21 File Pipeline Regular Load to Stage`
  - 0.4% (158) `G16 834 G22 G72 G21 File Pipeline Regular Load to Standard`
  - 0.4% (158) `G16_G17 Master Pipeline for RAW to Stage Incremental load`
  - 0.4% (158) `CAQH TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.4% (158) `MI TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.4% (158) `G16 834 G22 G72 Daily Master Pipeline RAW to Standard Regular load`
  - 0.4% (158) `G16 834 G22 G72 Weekly Master Pipeline RAW to Standard Regular load`
  - 0.4% (158) `G16 834 G22 G72 Monthly Master Pipeline RAW to Standard Regular load`
  - 0.4% (158) `G16 834 G22 G72 G21 Master Pipeline RAW to Standard Regular load`
  - 0.4% (158) `G16_G17 G101 Pipeline for Incremental load`
  - 0.4% (158) `CAQH TPL Grand Master Pipeline`
  - 0.4% (158) `G16 834 G22 G72 Daily Grand Master Pipeline`
  - 0.4% (158) `G16 834 G22 G72 Weekly Grand Master Pipeline`
  - 0.4% (158) `G16 834 G22 G72 Monthly Grand Master Pipeline`
  - 0.4% (158) `G16 834 G22 G72 G21 Grand Master Pipeline`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to RAW`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to RAW`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to RAW`
  - 0.1% (32) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to RAW`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to RAW`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to Stage`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to Stage`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to Stage`
  - 0.1% (32) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to Stage`
  - 0.1% (32) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to Stage`
  - 0.1% (32) `G3_G4_G5 File Pipeline Regular Load to Stage`
  - 0.1% (32) `G3_G4_G5 File Pipeline Regular Load to Standard`
  - 0.1% (32) `G7 File Pipeline Regular Load to Stage`
  - 0.1% (32) `G7 File Pipeline Regular Load to Standard`
  - 0.1% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Stage`
  - 0.1% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Standard`
  - 0.1% (32) `DIGITAL G102 Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `G3_G4_G5 Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `G7 Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `G3_G4_G5_Inbound Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `DIGITAL G102 Regular Load Grand Master Pipeline`
  - 0.1% (32) `G3_G4_G5 Regular Load Grand Master Pipeline`
  - 0.1% (32) `G7 Regular Load Grand Master Pipeline`
  - 0.1% (32) `G3_G4_G5_Inbound Regular Load Grand Master Pipeline`
  - 0.0% (12) `G8 Demographics Package Pipeline Regular Load to Stage`
  - 0.0% (12) `G8 Demographics Package Pipeline Regular Load to Standard`
  - 0.0% (12) `G8 Analytics Package Pipeline Regular Load to Stage`
  - 0.0% (12) `G8 Analytics Package Pipeline Regular Load to Standard`
  - 0.0% (12) `G8 Ind Risk Package Pipeline Regular Load to Stage`
  - 0.0% (12) `G8 Ind Risk Package Pipeline Regular Load to Standard`
  - 0.0% (12) `G103 G8 Master Pipeline RAW to Standard Regular load`
  - 0.0% (12) `G103 G8 Grand Master Pipeline`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Stage`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Standard`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Master Pipeline RAW to Standard Regular load`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Grand Master Pipeline`
  - 0.0% (4) `Common Claims Medical History Regular Load to Stage`
  - 0.0% (4) `Common Claims Medical History Regular Load to Standard`
  - 0.0% (4) `Common Claims Medical History RAW to Standard Regular load`
  - 0.0% (4) `Common Claims Medical History Grand Master Pipeline`
  - 0.0% (4) `G14 LA History Stage Pipeline Historical Load`
  - 0.0% (4) `G14 LA History Standard Pipeline Historical Load`
  - 0.0% (4) `G14 LA History Master Pipeline Historical Load`
  - 0.0% (4) `G14 LA History Grand Master Pipeline`
- patterns:
  - 18.9% (6734) `G1 Stage Load`
  - 18.9% (6734) `G1 Standard Load`
  - 1.2% (432) `{domain} 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.8% (288) `{domain} G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.5% (182) `G1 Master Pipeline`
  - 0.5% (182) `G1 Grand Master Pipeline`
  - 0.5% (181) `G1 G66 Regular STANDARD Load`
  - 0.5% (181) `G1 G67 Regular STANDARD Load`
  - 0.5% (181) `G1 G68 Regular STANDARD Load`
  - 0.5% (181) `G1 G65 Regular STANDARD Load`
  - 0.5% (181) `G1 G66 RAW to Stage Regular load`
  - 0.5% (181) `G1 G67 RAW to Stage Regular load`
  - 0.5% (181) `G1 G68 RAW to Stage Regular load`
  - 0.5% (181) `G1 G65 RAW to Stage Regular load`
  - 0.5% (181) `GMSTR_G1_G66_ONPREM_STG_INGESTION`
  - 0.5% (181) `GMSTR_G1_G67_ONPREM_STG_INGESTION`
  - 0.5% (181) `GMSTR_G1_G68_ONPREM_STG_INGESTION`
  - 0.5% (181) `GMSTR_G1_G65_ONPREM_STG_INGESTION`
  - 0.5% (179) `G1 G69 Regular STANDARD Load`
  - 0.5% (179) `G1 G69 Case Regular STANDARD Load`
  - 0.5% (179) `G1 G69 G70 Regular STANDARD Load`
  - 0.5% (179) `G1 G69 RAW to Stage Regular load`
  - 0.5% (179) `GMSTR_G1_G69_ONPREM_STG_INGESTION`
  - 0.5% (178) `G60 G61_extract File Pipeline Regular Load to Stage`
  - 0.5% (178) `G60 G62_G63 G99_G62 File Pipeline Regular Load to Stage`
  - 0.5% (178) `G60 G62_G63 G99_G63 File Pipeline Regular Load to Stage`
  - 0.5% (178) `G60 G100_G64_Leave File Pipeline Regular Load to Stage`
  - 0.5% (178) `G60 Master Pipeline for RAW to Stage Regular load`
  - 0.5% (178) `G60 G62_G63 Master Pipeline for RAW to Stage Regular load`
  - 0.5% (178) `G60 G100_G64_Leave Master Pipeline for RAW to Stage Regular load`
  - 0.5% (178) `G60 Regular Load Grand Master Pipeline`
  - 0.5% (178) `G60 G62_G63 Regular Load Grand Master Pipeline`
  - 0.5% (178) `G60 G100_G64_Leave Regular Load Grand Master Pipeline`
  - 0.4% (156) `MI TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.4% (156) `MI TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.4% (156) `MI TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.4% (154) `CAQH TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.4% (154) `CAQH TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.4% (154) `CAQH TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.4% (154) `CAQH TPL Grand Master Pipeline`
  - 0.4% (150) `G16 834 G22 G72 Daily File Pipeline Regular Load to Stage`
  - 0.4% (150) `G16 834 G22 G72 Daily File Pipeline Regular Load to Standard`
  - 0.4% (150) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Stage`
  - 0.4% (150) `G16 834 G22 G72 Weekly File Pipeline Regular Load to Standard`
  - 0.4% (150) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Stage`
  - 0.4% (150) `G16 834 G22 G72 Monthly File Pipeline Regular Load to Standard`
  - 0.4% (150) `G16 834 G22 G72 G21 File Pipeline Regular Load to Stage`
  - 0.4% (150) `G16 834 G22 G72 G21 File Pipeline Regular Load to Standard`
  - 0.4% (150) `G16 834 G22 G72 Daily Master Pipeline RAW to Standard Regular load`
  - 0.4% (150) `G16 834 G22 G72 Weekly Master Pipeline RAW to Standard Regular load`
  - 0.4% (150) `G16 834 G22 G72 Monthly Master Pipeline RAW to Standard Regular load`
  - 0.4% (150) `G16 834 G22 G72 G21 Master Pipeline RAW to Standard Regular load`
  - 0.4% (150) `G16 834 G22 G72 Daily Grand Master Pipeline`
  - 0.4% (150) `G16 834 G22 G72 Weekly Grand Master Pipeline`
  - 0.4% (150) `G16 834 G22 G72 Monthly Grand Master Pipeline`
  - 0.4% (150) `G16 834 G22 G72 G21 Grand Master Pipeline`
  - 0.4% (144) `{domain} 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.4% (144) `{domain} G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.4% (144) `{domain} Master Pipeline for RAW to Stage Incremental load`
  - 0.4% (144) `{domain} G101 Pipeline for Incremental load`
  - 0.3% (104) `GMSTR_G1_{source}_ONPREM_STG_INGESTION`
  - 0.3% (97) `G1_{source} G78 Regular STANDARD Load`
  - 0.3% (97) `G1_{source} G79 Regular STANDARD Load`
  - 0.3% (97) `G1_{source} G80 Regular STANDARD Load`
  - 0.3% (97) `G1_{source} G81 Regular STANDARD Load`
  - 0.3% (97) `G1_{source} G82 Regular STANDARD Load`
  - 0.3% (97) `G1_{source} G83 Regular STANDARD Load`
  - 0.3% (97) `G1_{source} Master Pipeline for RAW to Stage Regular load`
  - 0.2% (85) `G1_G2 G78 Regular STANDARD Load`
  - 0.2% (85) `G1_G2 G79 Regular STANDARD Load`
  - 0.2% (85) `G1_G2 G80 Regular STANDARD Load`
  - 0.2% (85) `G1_G2 G81 Regular STANDARD Load`
  - 0.2% (85) `G1_G2 G82 Regular STANDARD Load`
  - 0.2% (85) `G1_G2 G83 Regular STANDARD Load`
  - 0.2% (85) `G1_G2 Master Pipeline for RAW to Stage Regular load`
  - 0.2% (85) `GMSTR_G1_G2_ONPREM_STG_INGESTION`
  - 0.1% (32) `G3_G4_G5 File Pipeline Regular Load to Stage`
  - 0.1% (32) `G3_G4_G5 File Pipeline Regular Load to Standard`
  - 0.1% (32) `G7 File Pipeline Regular Load to Stage`
  - 0.1% (32) `G7 File Pipeline Regular Load to Standard`
  - 0.1% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Stage`
  - 0.1% (32) `G3_G4_G5_Inbound File Pipeline Regular Load to Standard`
  - 0.1% (32) `DIGITAL G102 Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `G3_G4_G5 Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `G7 Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `G3_G4_G5_Inbound Master Pipeline for RAW to Stage Regular load`
  - 0.1% (32) `DIGITAL G102 Regular Load Grand Master Pipeline`
  - 0.1% (32) `G3_G4_G5 Regular Load Grand Master Pipeline`
  - 0.1% (32) `G7 Regular Load Grand Master Pipeline`
  - 0.1% (32) `G3_G4_G5_Inbound Regular Load Grand Master Pipeline`
  - 0.1% (24) `{source}_G17 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G91_G92 File Pipeline Regular Load to RAW`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G93_G94_G92 File Pipeline Regular Load to RAW`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G95_pct_mo_de File Pipeline Regular Load to RAW`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_data_G92 File Pipeline Regular Load to RAW`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G96_G92 File Pipeline Regular Load to RAW`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G91_G92 File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G93_G94_G92 File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G95_pct_mo_de File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_data_G92 File Pipeline Regular Load to Stage`
  - 0.1% (20) `DIGITAL G102 db_104_{domain}_G96_G92 File Pipeline Regular Load to Stage`
  - 0.0% (16) `{source}_G17 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (16) `{source}_G17 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (12) `G16_G17 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to RAW`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to RAW`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to RAW`
  - 0.0% (10) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to RAW`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to RAW`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G91_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G93_G94_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G95_pct_mo_de File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_data_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `DIGITAL G102 db_104_G90_G96_G92 File Pipeline Regular Load to Stage`
  - 0.0% (10) `G8 Ind Risk Package Pipeline Regular Load to Stage`
  - 0.0% (10) `G8 Ind Risk Package Pipeline Regular Load to Standard`
  - 0.0% (10) `G103 G8 Master Pipeline RAW to Standard Regular load`
  - 0.0% (10) `G103 G8 Grand Master Pipeline`
  - 0.0% (9) `G8 Analytics Package Pipeline Regular Load to Stage`
  - 0.0% (9) `G8 Analytics Package Pipeline Regular Load to Standard`
  - 0.0% (8) `G8 {feed} Pipeline Regular Load to Stage`
  - 0.0% (8) `G8 {feed} Pipeline Regular Load to Standard`
  - 0.0% (8) `G16_G17 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `G16_G17 G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (8) `{source}_G17 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source}_G17 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (8) `{source} 834 G22 G72 Daily File Pipeline Regular Load to Stage`
  - 0.0% (8) `{source} 834 G22 G72 Daily File Pipeline Regular Load to Standard`
  - 0.0% (8) `{source} 834 G22 G72 Weekly File Pipeline Regular Load to Stage`
  - 0.0% (8) `{source} 834 G22 G72 Weekly File Pipeline Regular Load to Standard`
  - 0.0% (8) `{source} 834 G22 G72 Monthly File Pipeline Regular Load to Stage`
  - 0.0% (8) `{source} 834 G22 G72 Monthly File Pipeline Regular Load to Standard`
  - 0.0% (8) `{source} 834 G22 G72 G21 File Pipeline Regular Load to Stage`
  - 0.0% (8) `{source} 834 G22 G72 G21 File Pipeline Regular Load to Standard`
  - 0.0% (8) `{source}_G17 Master Pipeline for RAW to Stage Incremental load`
  - 0.0% (8) `{source} 834 G22 G72 Daily Master Pipeline RAW to Standard Regular load`
  - 0.0% (8) `{source} 834 G22 G72 Weekly Master Pipeline RAW to Standard Regular load`
  - 0.0% (8) `{source} 834 G22 G72 Monthly Master Pipeline RAW to Standard Regular load`
  - 0.0% (8) `{source} 834 G22 G72 G21 Master Pipeline RAW to Standard Regular load`
  - 0.0% (8) `{source}_G17 G101 Pipeline for Incremental load`
  - 0.0% (8) `{source} 834 G22 G72 Daily Grand Master Pipeline`
  - 0.0% (8) `{source} 834 G22 G72 Weekly Grand Master Pipeline`
  - 0.0% (8) `{source} 834 G22 G72 Monthly Grand Master Pipeline`
  - 0.0% (8) `{source} 834 G22 G72 G21 Grand Master Pipeline`
  - 0.0% (7) `G1 {source} Regular STANDARD Load`
  - 0.0% (7) `G1 {source} RAW to Stage Regular load`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Stage`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Pipeline Regular Load to Standard`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Master Pipeline RAW to Standard Regular load`
  - 0.0% (6) `EMCIPS SFMC Email Campaign Tracking Details Grand Master Pipeline`
  - 0.0% (6) `G16_{source} 0550 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (5) `DIGITAL G102 {subdomain} File Pipeline Regular Load to RAW`
  - 0.0% (5) `DIGITAL G102 {subdomain} File Pipeline Regular Load to Stage`
  - 0.0% (5) `DIGITAL G102 {table} File Pipeline Regular Load to RAW`
  - 0.0% (5) `DIGITAL G102 {table} File Pipeline Regular Load to Stage`
  - 0.0% (4) `Common {domain} {subdomain} History Regular Load to Stage`
  - 0.0% (4) `Common {domain} {subdomain} History Regular Load to Standard`
  - 0.0% (4) `Common {domain} {subdomain} History RAW to Standard Regular load`
  - 0.0% (4) `Common {domain} {subdomain} History Grand Master Pipeline`
  - 0.0% (4) `{source} LA History Stage Pipeline Historical Load`
  - 0.0% (4) `{source} LA History Standard Pipeline Historical Load`
  - 0.0% (4) `{source} LA History Master Pipeline Historical Load`
  - 0.0% (4) `{source} LA History Grand Master Pipeline`
  - 0.0% (4) `G16_G17 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (4) `G16_G17 G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_G17 Master Pipeline for RAW to Stage Incremental load`
  - 0.0% (4) `G16_G17 G101 Pipeline for Incremental load`
  - 0.0% (4) `G16_{source} 2600 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 2600 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 6400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 6400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 5400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0550 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 1200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 1200 LOB Weekly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 7200 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 7700 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 7700 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0500 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0530 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} 0540 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `G16_{source} G25 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (4) `{subdomain} G100_G64_Leave File Pipeline Regular Load to Stage`
  - 0.0% (4) `{subdomain} Master Pipeline for RAW to Stage Regular load`
  - 0.0% (4) `{subdomain} G62_G63 Master Pipeline for RAW to Stage Regular load`
  - 0.0% (4) `{subdomain} G100_G64_Leave Master Pipeline for RAW to Stage Regular load`
  - 0.0% (4) `{subdomain} Regular Load Grand Master Pipeline`
  - 0.0% (4) `{subdomain} G62_G63 Regular Load Grand Master Pipeline`
  - 0.0% (4) `{subdomain} G100_G64_Leave Regular Load Grand Master Pipeline`
  - 0.0% (3) `G8 Demographics Package Pipeline Regular Load to Stage`
  - 0.0% (3) `G8 Demographics Package Pipeline Regular Load to Standard`
  - 0.0% (3) `{subdomain} G62_G63 G99_G62 File Pipeline Regular Load to Stage`
  - 0.0% (3) `{subdomain} G62_G63 G99_G63 File Pipeline Regular Load to Stage`
  - 0.0% (3) `{subdomain} G61_extract File Pipeline Regular Load to Stage`
  - 0.0% (3) `G1 {source} Case Regular STANDARD Load`
  - 0.0% (3) `G1 {source} G70 Regular STANDARD Load`
  - 0.0% (2) `{schema} {feed} Pipeline Regular Load to Stage`
  - 0.0% (2) `{schema} {feed} Pipeline Regular Load to Standard`
  - 0.0% (2) `{schema} Ind Risk Package Pipeline Regular Load to Stage`
  - 0.0% (2) `{schema} Ind Risk Package Pipeline Regular Load to Standard`
  - 0.0% (2) `G103 {schema} Master Pipeline RAW to Standard Regular load`
  - 0.0% (2) `G103 {schema} Grand Master Pipeline`
  - 0.0% (2) `{source} TPL WORKFLOW FILE STAGE DATA INGESTION`
  - 0.0% (2) `{source} TPL WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.0% (2) `{source} TPL WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.0% (2) `{source} TPL Grand Master Pipeline`
  - 0.0% (2) `CAQH {subdomain} WORKFLOW FILE STAGE DATA INGESTION`
  - 0.0% (2) `CAQH {subdomain} WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.0% (2) `MI {subdomain} WORKFLOW FILE STAGE DATA INGESTION`
  - 0.0% (2) `MI {subdomain} WORKFLOW FILE STANDARD DATA INGESTION`
  - 0.0% (2) `CAQH {subdomain} WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.0% (2) `MI {subdomain} WORKFLOW FILE RAW TO STANDARD DATA INGESTION`
  - 0.0% (2) `CAQH {subdomain} Grand Master Pipeline`
  - 0.0% (2) `G16_{source} 0100 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0500 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0530 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0540 LOB Daily File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0100 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0500 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0530 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} 0540 LOB Monthly File Pipeline Incremental Load to Stage`
  - 0.0% (2) `G16_{source} G18 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G18 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G19 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G19 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2400 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2400 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0900 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0900 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 1200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 7100 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 7100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 7200 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G20 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G20 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 2100 LOB G21 File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0100 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0500 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0530 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 0540 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} G25 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 5420 LOB Daily File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} 5420 LOB Monthly File Pipeline Incremental Load to STAGE`
  - 0.0% (2) `G16_{source} Master Pipeline for RAW to Stage Incremental load`
  - 0.0% (2) `G16_{source} G101 Pipeline for Incremental load`
  - 0.0% (2) `{subdomain} G62_G63 {table} File Pipeline Regular Load to Stage`
  - 0.0% (1) `{schema} Analytics Package Pipeline Regular Load to Stage`
  - 0.0% (1) `{schema} Analytics Package Pipeline Regular Load to Standard`
  - 0.0% (1) `{schema} Demographics Package Pipeline Regular Load to Stage`
  - 0.0% (1) `{schema} Demographics Package Pipeline Regular Load to Standard`
  - 0.0% (1) `{subdomain} {table}_extract File Pipeline Regular Load to Stage`

### DATA_FACTORY_PIPELINE_SCHEDULE.PIPELINE_FREQUENCY

- values:
  - 68.5% (24410) `Daily`
  - 23.0% (8200) `Monthly`
  - 4.5% (1592) `Weekly`
  - 3.3% (1178) `WEEKLY`
  - 0.4% (158) `G21`
  - 0.3% (96) `MONTHLY`
  - 0.1% (24) `DAILY`
- patterns:
  - 68.5% (24410) `Daily`
  - 23.0% (8200) `Monthly`
  - 4.5% (1592) `Weekly`
  - 3.3% (1178) `WEEKLY`
  - 0.4% (158) `G21`
  - 0.3% (96) `MONTHLY`
  - 0.1% (24) `DAILY`

### DATA_FACTORY_PIPELINE_SCHEDULE.NO_OF_CYCLE_PER_DAY

- values:
  - 98.2% (35026) `1`
  - 1.8% (632) `3`
- patterns:
  - 98.2% (35026) `1`
  - 1.8% (632) `3`

### DATA_FACTORY_PIPELINE_SCHEDULE.DAY_OF_SCHEDULE

- values:
  - 54.8% (689) `0`
  - 44.0% (553) `0.0`
  - 1.3% (16) `5`
- patterns:
  - 54.8% (689) `0`
  - 44.0% (553) `0.0`
  - 1.3% (16) `5`

### DATA_FACTORY_PIPELINE_SCHEDULE.ACTIVE_FLAG

- values:
  - 97.5% (34772) `Y`
  - 2.5% (886) `N`
- patterns:
  - 97.5% (34772) `Y`
  - 2.5% (886) `N`

### DATA_FACTORY_PIPELINE_SCHEDULE.ACTIVE_START_DATE

- values:
  - 19.4% (6916) `2025-12-20 00:00:00`
  - 19.4% (6916) `2025-12-20`
  - 8.6% (3081) `2024-10-24 00:00:00`
  - 8.6% (3081) `2024-10-24`
  - 4.9% (1738) `2024-11-14 00:00:00`
  - 4.9% (1738) `2024-11-14`
  - 4.6% (1638) `2024-09-05 00:00:00`
  - 4.6% (1638) `2024-09-05`
  - 3.5% (1264) `2026-02-19 00:00:00`
  - 3.5% (1264) `2026-02-19`
  - 1.3% (455) `1900-01-03 00:00:00`
  - 1.3% (455) `1900-01-03`
  - 1.0% (364) `2025-06-18 00:00:00`
  - 1.0% (364) `2025-06-18`
  - 0.9% (316) `2026-08-06 00:00:00`
  - 0.9% (316) `2026-08-06`
  - 0.8% (273) `2024-09-26 00:00:00`
  - 0.8% (273) `2025-06-30 00:00:00`
  - 0.8% (273) `2024-09-26`
  - 0.8% (273) `2025-06-30`
  - 0.7% (249) `2026-08-20 00:00:00`
  - 0.7% (249) `2026-08-20`
  - 0.7% (246) `2026-04-16 00:00:00`
  - 0.7% (246) `2026-04-16`
  - 0.7% (237) `2024-12-03 00:00:00`
  - 0.7% (237) `2025-05-03 00:00:00`
  - 0.7% (237) `2024-12-03`
  - 0.7% (237) `2025-05-03`
  - 0.5% (176) `2023-05-18 00:00:00`
  - 0.5% (176) `2023-05-18`
  - 0.4% (158) `2026-03-05 00:00:00`
  - 0.4% (158) `2026-03-05`
  - 0.2% (64) `2025-10-16 00:00:00`
  - 0.2% (64) `2025-11-26 00:00:00`
  - 0.2% (64) `2025-10-16`
  - 0.2% (64) `2025-11-26`
  - 0.1% (48) `2026-06-25 00:00:00`
  - 0.1% (48) `2026-06-25`
  - 0.0% (16) `2023-04-06 00:00:00`
  - 0.0% (16) `2023-04-06`
  - 0.0% (8) `2026-09-17 00:00:00`
  - 0.0% (8) `2026-04-19 00:00:00`
  - 0.0% (8) `2026-09-17`
  - 0.0% (8) `2026-04-19`
- patterns:
  - 19.4% (6916) `2025-12-20 00:00:00`
  - 19.4% (6916) `2025-12-20`
  - 8.6% (3081) `2024-10-24 00:00:00`
  - 8.6% (3081) `2024-10-24`
  - 4.9% (1738) `2024-11-14 00:00:00`
  - 4.9% (1738) `2024-11-14`
  - 4.6% (1638) `2024-09-05 00:00:00`
  - 4.6% (1638) `2024-09-05`
  - 3.5% (1264) `2026-02-19 00:00:00`
  - 3.5% (1264) `2026-02-19`
  - 1.3% (455) `1900-01-03 00:00:00`
  - 1.3% (455) `1900-01-03`
  - 1.0% (364) `2025-06-18 00:00:00`
  - 1.0% (364) `2025-06-18`
  - 0.9% (316) `2026-08-06 00:00:00`
  - 0.9% (316) `2026-08-06`
  - 0.8% (273) `2024-09-26 00:00:00`
  - 0.8% (273) `2025-06-30 00:00:00`
  - 0.8% (273) `2024-09-26`
  - 0.8% (273) `2025-06-30`
  - 0.7% (249) `2026-08-20 00:00:00`
  - 0.7% (249) `2026-08-20`
  - 0.7% (246) `2026-04-16 00:00:00`
  - 0.7% (246) `2026-04-16`
  - 0.7% (237) `2024-12-03 00:00:00`
  - 0.7% (237) `2025-05-03 00:00:00`
  - 0.7% (237) `2024-12-03`
  - 0.7% (237) `2025-05-03`
  - 0.5% (176) `2023-05-18 00:00:00`
  - 0.5% (176) `2023-05-18`
  - 0.4% (158) `2026-03-05 00:00:00`
  - 0.4% (158) `2026-03-05`
  - 0.2% (64) `2025-10-16 00:00:00`
  - 0.2% (64) `2025-11-26 00:00:00`
  - 0.2% (64) `2025-10-16`
  - 0.2% (64) `2025-11-26`
  - 0.1% (48) `2026-06-25 00:00:00`
  - 0.1% (48) `2026-06-25`
  - 0.0% (16) `2023-04-06 00:00:00`
  - 0.0% (16) `2023-04-06`
  - 0.0% (8) `2026-09-17 00:00:00`
  - 0.0% (8) `2026-04-19 00:00:00`
  - 0.0% (8) `2026-09-17`
  - 0.0% (8) `2026-04-19`

### DATA_FACTORY_PIPELINE_SCHEDULE.ACTIVE_END_DATE

- values:
  - 50.0% (17829) `9999-12-31 00:00:00`
  - 50.0% (17829) `9999-12-31`
- patterns:
  - 50.0% (17829) `9999-12-31 00:00:00`
  - 50.0% (17829) `9999-12-31`

### DATA_FACTORY_PIPELINE_SCHEDULE.APPLICATION_NAME

- values:
  - 38.8% (13832) `G1`
  - 30.6% (10902) `G104.0`
  - 7.1% (2528) `G16 834 G22 G72`
  - 5.1% (1820) `G60`
  - 4.1% (1456) `G1_G2`
  - 2.6% (910) `G1_G69`
  - 1.8% (632) `CAQH`
  - 1.5% (546) `G1_G66`
  - 1.5% (546) `G1_G67`
  - 1.5% (546) `G1_G68`
  - 1.5% (546) `G1_G65`
  - 1.3% (474) `MI TPL`
  - 1.1% (384) `Files`
  - 1.0% (352) `DataLake 2.0`
  - 0.3% (96) `G8 G103`
  - 0.1% (32) `Digital_G92`
  - 0.1% (24) `SFMC Email Campaign`
  - 0.0% (16) `Common Claims Medical`
  - 0.0% (16) `G14 LA history`
- patterns:
  - 38.8% (13832) `G1`
  - 30.6% (10902) `G104.0`
  - 6.7% (2400) `G16 834 G22 G72`
  - 5.0% (1780) `G60`
  - 2.5% (895) `G1_G69`
  - 2.3% (803) `G1_{source}`
  - 1.9% (680) `G1_G2`
  - 1.7% (624) `CAQH`
  - 1.5% (543) `G1_G66`
  - 1.5% (543) `G1_G67`
  - 1.5% (543) `G1_G68`
  - 1.5% (543) `G1_G65`
  - 1.3% (468) `MI TPL`
  - 1.1% (384) `Files`
  - 1.0% (352) `DataLake 2.0`
  - 0.4% (128) `{source} 834 G22 G72`
  - 0.2% (80) `G8 G103`
  - 0.1% (40) `{subdomain}`
  - 0.1% (32) `Digital_G92`
  - 0.1% (24) `SFMC Email Campaign`
  - 0.0% (16) `{schema} G103`
  - 0.0% (16) `Common {domain} {subdomain}`
  - 0.0% (16) `{source} LA history`
  - 0.0% (8) `{source}`
  - 0.0% (6) `MI {subdomain}`

### DATA_FACTORY_PIPELINE_SCHEDULE.PROCESS_NAME

- values:
  - 59.0% (12798) `G16 834 G22`
  - 8.4% (1820) `ADP`
  - 6.7% (1456) `G1_G2`
  - 4.2% (910) `G1_G69`
  - 2.9% (632) `G16_G17`
  - 2.9% (632) `CAQH TPL`
  - 2.5% (546) `G1_G66`
  - 2.5% (546) `G1_G67`
  - 2.5% (546) `G1_G68`
  - 2.5% (546) `G1_G65`
  - 2.2% (474) `MI STATE TPL`
  - 0.9% (192) `DIGITAL`
  - 0.7% (160) `G105`
  - 0.6% (128) `FILES`
  - 0.4% (96) `G103 G8`
  - 0.3% (64) `G106 Scripts`
  - 0.1% (32) `G90`
  - 0.1% (32) `Care Management`
  - 0.1% (32) `Digital G92`
  - 0.1% (24) `EMCIPS SFMC`
  - 0.1% (16) `Common Claims Medical`
  - 0.1% (16) `G14 LA history`
- patterns:
  - 56.0% (12150) `G16 834 G22`
  - 8.4% (1820) `ADP`
  - 4.1% (895) `G1_G69`
  - 3.7% (803) `G1_{source}`
  - 3.1% (680) `G1_G2`
  - 3.0% (648) `{domain}`
  - 3.0% (648) `{source} 834 G22`
  - 2.8% (616) `CAQH TPL`
  - 2.5% (543) `G1_G66`
  - 2.5% (543) `G1_G67`
  - 2.5% (543) `G1_G68`
  - 2.5% (543) `G1_G65`
  - 2.2% (468) `MI STATE TPL`
  - 0.9% (192) `DIGITAL`
  - 0.6% (128) `FILES`
  - 0.5% (110) `G105`
  - 0.4% (80) `G103 G8`
  - 0.3% (64) `G106 Scripts`
  - 0.1% (32) `Digital G92`
  - 0.1% (32) `{source}_G17`
  - 0.1% (30) `Care Management`
  - 0.1% (24) `EMCIPS SFMC`
  - 0.1% (16) `G103 {schema}`
  - 0.1% (16) `Common {domain} {subdomain}`
  - 0.1% (16) `{source} LA history`
  - 0.1% (16) `G16_G17`
  - 0.1% (12) `G90`
  - 0.0% (8) `{source} TPL`
  - 0.0% (8) `CAQH {subdomain}`
  - 0.0% (8) `G16_{source}`
  - 0.0% (6) `MI STATE {subdomain}`

### DATA_FACTORY_PIPELINE_SCHEDULE.SUBPROCESS_NAME

- values:
  - 7.6% (1456) `G2`
  - 6.6% (1264) `G72 LAYOUT`
  - 4.7% (910) `G69`
  - 4.1% (790) `0100`
  - 4.1% (790) `0500`
  - 4.1% (790) `0530`
  - 4.1% (790) `0540`
  - 4.1% (790) `0550`
  - 3.8% (728) `G62`
  - 3.3% (632) `2600`
  - 3.3% (632) `6400`
  - 3.3% (632) `1200`
  - 3.3% (632) `CAQH load`
  - 2.8% (546) `G107/G108`
  - 2.8% (546) `G107_Leave`
  - 2.8% (546) `G66`
  - 2.8% (546) `G67`
  - 2.8% (546) `G68`
  - 2.8% (546) `G65`
  - 2.5% (474) `2100`
  - 2.5% (474) `MI TPL`
  - 2.5% (474) `G25`
  - 1.6% (316) `G18`
  - 1.6% (316) `G19`
  - 1.6% (316) `5400`
  - 1.6% (316) `2400`
  - 1.6% (316) `0900`
  - 1.6% (316) `7100`
  - 1.6% (316) `7200`
  - 1.6% (316) `7700`
  - 1.6% (316) `G20`
  - 0.8% (160) `DB_104`
  - 0.8% (160) `G90`
  - 0.5% (96) `G3_G4_G5`
  - 0.5% (96) `G103 G8 Risk`
  - 0.2% (32) `Pharmacy CHIP`
  - 0.2% (32) `Regular Load to Stage`
  - 0.2% (32) `Regular Load to Standard`
  - 0.2% (32) `G102`
  - 0.2% (32) `RAW to Stage Regular`
  - 0.2% (32) `G109`
  - 0.2% (32) `Regular Load Grand Master`
  - 0.1% (24) `SFMC`
  - 0.1% (16) `NA`
  - 0.1% (16) `RX Claims`
- patterns:
  - 6.6% (1264) `G72 LAYOUT`
  - 4.7% (895) `G69`
  - 4.2% (803) `{source}`
  - 4.1% (790) `0100`
  - 4.1% (790) `0500`
  - 4.1% (790) `0530`
  - 4.1% (790) `0540`
  - 4.1% (790) `0550`
  - 3.8% (728) `G62`
  - 3.5% (680) `G2`
  - 3.3% (632) `2600`
  - 3.3% (632) `6400`
  - 3.3% (632) `1200`
  - 3.3% (624) `CAQH load`
  - 2.8% (546) `G107/G108`
  - 2.8% (546) `G107_Leave`
  - 2.8% (543) `G66`
  - 2.8% (543) `G67`
  - 2.8% (543) `G68`
  - 2.8% (543) `G65`
  - 2.5% (474) `2100`
  - 2.5% (474) `G25`
  - 2.4% (468) `MI TPL`
  - 1.6% (316) `G18`
  - 1.6% (316) `G19`
  - 1.6% (316) `5400`
  - 1.6% (316) `2400`
  - 1.6% (316) `0900`
  - 1.6% (316) `7100`
  - 1.6% (316) `7200`
  - 1.6% (316) `7700`
  - 1.6% (316) `G20`
  - 0.8% (160) `DB_104`
  - 0.5% (100) `{domain}`
  - 0.5% (96) `G3_G4_G5`
  - 0.4% (80) `G103 G8 Risk`
  - 0.3% (60) `G90`
  - 0.2% (32) `Pharmacy CHIP`
  - 0.2% (32) `Regular Load to Stage`
  - 0.2% (32) `Regular Load to Standard`
  - 0.2% (32) `G102`
  - 0.2% (32) `RAW to Stage Regular`
  - 0.2% (32) `G109`
  - 0.2% (32) `Regular Load Grand Master`
  - 0.1% (24) `SFMC`
  - 0.1% (16) `G103 {schema} Risk`
  - 0.1% (16) `NA`
  - 0.1% (16) `RX {domain}`
  - 0.0% (8) `{source} load`
  - 0.0% (6) `MI {subdomain}`

### DATA_FACTORY_PIPELINE_SCHEDULE.LAYER_NAME

- values:
  - 88.7% (12158) `STAGE`
  - 7.3% (998) `STANDARD`
  - 2.3% (316) `STAGE AND STANDARD`
  - 1.2% (160) `RAW`
  - 0.5% (64) `Standard`
  - 0.1% (8) `NA`
- patterns:
  - 88.7% (12158) `STAGE`
  - 7.3% (998) `STANDARD`
  - 2.3% (316) `STAGE AND STANDARD`
  - 1.2% (160) `RAW`
  - 0.5% (64) `Standard`
  - 0.1% (8) `NA`

### DATA_FACTORY_PIPELINE_SCHEDULE.RUNTIME_SLA

- values:
  - 100.0% (16) `6`
- patterns:
  - 100.0% (16) `6`

### DATA_FACTORY_PIPELINE_SCHEDULE.IsFileCopyReqFlag

- values:
  - 88.5% (1398) `N`
  - 11.5% (182) `Y`
- patterns:
  - 88.5% (1398) `N`
  - 11.5% (182) `Y`

### EMAIL_TEMPLATE_CONFIG.PIPELINE_NAME

- values:
  - 7.3% (980) `PL_Gmstr_G97_Historical_Load`
  - 4.7% (630) `PL_CHLD_G110_G111_STD_TO_G112_G113`
  - 3.6% (480) `PL_CHLD_G110_G111_FL_G112`
  - 1.0% (140) `PL_CHLD_G110_G111_G114_G112`
  - 0.6% (80) `PL_CHLD_G110_G111_RAW_TO_STD_G113`
  - 0.6% (80) `WF_G115_G116_SF_STD`
  - 0.5% (66) `PL_CHLD_DATA_G117_G118`
  - 0.4% (60) `PL_CHLD_G110_G111_G112_TO_G119_G113`
  - 0.4% (50) `PL_File_RAW_G120_G121_G122_To_ADLS_Incr`
  - 0.4% (50) `PL_File_STAGE_G120_G121_G122_ADLS_To_Delta_Incr`
  - 0.4% (50) `PL_File_STD_G120_G121_G122_Delta_To_STD_Incr`
  - 0.3% (40) `PL_CHLD_G110_G111_G123_TO_RAW_INSERT`
  - 0.3% (40) `PL_CHLD_G110_G111_G119_TO_G124_G125`
  - 0.3% (40) `PL_CHLD_G110_G111_G126_TO_G124_G125`
  - 0.2% (30) `PL_CHLD_G110_G111_G127_PROCESS_G113`
  - 0.1% (20) `PL_MSTR_G128_G129_G124_RPT_DLY`
  - 0.1% (20) `Pl_CHLD_G130_PROCESSING_NC_G131_G132`
  - 0.1% (20) `Pl_CHLD_G130_PROCESSING_Sub_LOB_G132`
  - 0.1% (20) `PL_CHLD_G133_G134_FILE_RAW_TO_G123_DLY`
  - 0.1% (14) `PL_File_RAW_G135_G136_To_ADLS_Incr`
  - 0.1% (14) `PL_File_STAGE_G135_G136_ADLS_To_Delta_Incr`
  - 0.1% (14) `PL_File_STD_G135_G136_Delta_To_STD_Incr`
  - 0.1% (14) `PL_File_RAW_G135_G136_Hist_To_ADLS_Incr`
  - 0.1% (14) `PL_File_STAGE_G135_G136_Hist_ADLS_To_Delta_Incr`
  - 0.1% (14) `PL_File_STD_G135_G136_Hist_Delta_To_STD_Incr`
  - 0.1% (14) `WF_CHLD_G137_STD_G102_G126_CLM`
  - 0.1% (12) `PL_GMSTR_G133_G138_FILE_DLY`
  - 0.1% (12) `PL_MSTR_G133_G138_FILE_DLY`
  - 0.1% (12) `Pl_Mstr_Digital_G139_Raw_Stage_Ingestion`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3011_G140_POP_Update`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_2950_G141_G142_Outreach`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_2699_G143_MEMBER_GROUP`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G144_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G15 - G145 - G146 IDENTIFIED`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G147_G148_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G149_G148_REPORT_G150`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_Current_mbr_list_G151`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_INTERNAL_FILE_100_Unique`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_INTERNAL_FILE_500_Unique`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_1315_Lead_G152`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_33_G153_CM`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G154_G155_Profiles`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G154_G156_Profiles`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_5623`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157_G158`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G159_G148_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G160_Outreach_Roster`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G161_outreach Report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3292_2243_Daily_G158_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157 G162 Lead Extract`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G163_G148_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3242_OH_BH_ER_0_20`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3232_G164_House_G165`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G149_G166_MEMBER_LIST_NEW`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_KF_G166_MEMBER_LIST_NEW`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G139_G167`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157_G168_MEMBER_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_Weekly_Auth_G169_G157`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_ip_daily_census_report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G170_G171_G172_G173`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G174`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G175`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G176`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G177`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157_G170_G178_RISK_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G179_G144_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G180_G181`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_ip_claims_G182`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G163_G183_Current_G184`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3081_OH_Membership_Report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G185_G186_G187_MEMBERS`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G188_Identified_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G189_pop`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G190`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G191_DOC_G192_in_3_G193`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_834_G194_records_received_since`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G195_G196_Report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G197_<LOCAL_DENYLIST> - G198`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G197_<LOCAL_DENYLIST> - Exit`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G199`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G200_42_G201_Daily`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G202_G203_1_2_3_G204_RISK_LIST`
  - 0.1% (12) `PL_MSTR_G138_G205_DLY`
  - 0.1% (12) `PL_CHLD_G138_G205_TO_RAW_LOAD`
  - 0.1% (12) `DATA_G117_DEPENDENCY_G132`
  - 0.1% (12) `WF_CHLD_G137_STD_G102_G126_MBR`
  - 0.1% (12) `WF_CHLD_G137_STD_G102_G126_G206`
  - 0.1% (10) `Pl_File_G207_G208_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_G207_G209_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_CLM_G210_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_CLM_RX_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_G207_G211_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_02`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_03`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_04`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_05`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_06`
  - 0.1% (10) `Pl_G212_To_Adls_Full_02`
  - 0.1% (10) `Pl_Mstr_G212_G213_Full-Incr_Hist_01`
  - 0.1% (10) `G214_G215_master`
  - 0.1% (10) `Pl_File_G216_File_To_Adls_01`
  - 0.1% (10) `Pl_File_G16_834_1250_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_1300_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_2900_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_3700_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_6100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0500_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0530_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0540_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0900_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_1200_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2400_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2600_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_5400_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6400_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7200_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_1250_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_1300_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_2900_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_3700_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_6100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0500_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0530_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0540_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0900_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_1200_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2400_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2600_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_5400_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6400_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7200_Stage_To_G217_Incr`
  - 0.1% (10) `PI_Mstr_CA_CURRENT_G218_Raw_Stg`
  - 0.1% (10) `Pl_G219_case_G220_G84_to_adls`
  - 0.1% (10) `Pl_G219_case_G220_to_adls`
  - 0.1% (10) `File_Raw_To_Stage_UM_G221_Load`
  - 0.1% (10) `Pl_G128_G222_Refresh_G223`
  - 0.1% (10) `PL_Gmstr_G97_Historical_Load_G224`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_notes_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G229_acfc_member_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G230_claim_summary_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G232_G15_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_elig_G15_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G233_G15_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_campaign_dtl_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_G235_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G236_G157_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G237_G238_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G239_G147_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_er_G240_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G241_G242_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G243_G244_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_master_G245_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_notes_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G229_acfc_member_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G230_claim_summary_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G232_G15_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_elig_G15_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G233_G15_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_Campaign_Dtl_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_G235_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G236_G157_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G237_G238_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G239_G147_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_er_G240_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G241_G242_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G243_G244_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_master_G245_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G230_claim_summary_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_campaign_dtl_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_G235_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G237_G238_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G239_G147_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_er_G240_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G230_claim_summary_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_Campaign_Dtl_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_G235_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G237_G238_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G239_G147_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_er_G240_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_enroll_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_medical_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_pharmacy_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_rx_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G247_data_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_ip_data_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_G249_G132_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_exec_G132_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_exec_plan_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_members_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_G250_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_G251_category_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G252_G253_G254_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G255_G256_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G257_details_G258_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G259_G260_MAPPING_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G252_rx_G261_G262_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_one_time_17_tables_load_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_db_94_G246_G12_G248_3_tables_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_G252_db_G263_G252_procedure_G264_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_G252_rx_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_social_det_G265_mbr_all_lob_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_master_G245_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_master_G245_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G266_list_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_RR_568_REL_G267_DATA_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G268_DATE_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_RR_568_REL_G267_DATA_G268_DATE_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G269_group_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G270_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_social_det_G265_mbr_all_lob_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_facets_pcp_transfer_all_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G266_DIAG_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G271_PROCEDURE_CODE_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_CLIENT_MAPPING_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G259_G253_MAPPING_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G272_DIAGNOSIS_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_IP_MULTIPLE_LINES_G258_To_ADLS_Incr`
  - 0.1% (10) `PL_Mstr_G225_Load_G217_social_det_G265_mbr_all_lob`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_FACETS_G274_G275_G276`
  - 0.1% (10) `PL_GMSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G115_PIPELINE`
  - 0.1% (10) `PL_MSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G115_PIPELINE`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G278`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G279_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G34_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_DATES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G280`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G281`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G282`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_SYSTEM_G132_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_SYSTEM_PROMPT_TYPES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_TEXT_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G283_DEFINITIONS`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G283_G284`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G285_G286`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G285_G287`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_WF_JOB_G280`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G288_ITEM_STATUSES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G288_ITEMS`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_V_G289`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G290`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_SYSTEM_G287`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G290`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_FOLDER_TYPES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G280`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_DOCUMENT_TYPES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_DOCUMENT_STATUS_DEFINITIONS`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_FACETS_G274_G275_G276`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_01`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_02`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_05`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_06`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_07`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_01`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_02`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_05`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_06`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_07`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G294_EXT_G295_G296_G297_H`
  - 0.1% (10) `PL_GMSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G298_PIPELINE`
  - 0.1% (10) `PL_MSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G298_PIPELINE`
  - 0.1% (10) `Pl_G84_G277_G298_G84_To_ADLS_G277_G298_EXT_PROV_PROCESS_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Stage_G277_G298_EXT_PROV_PROCESS_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Delta_G113_G277_G298_EXT_PROV_PROCESS_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_G84_To_ADLS_G277_G298_EXT_PROV_SUMMARY_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Stage_G277_G298_EXT_PROV_SUMMARY_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Delta_G113_G277_G298_EXT_PROV_SUMMARY_HIST`
  - 0.1% (10) `Pl_Files_To_Adls`
  - 0.1% (10) `PL_G84_G299_MEMBER_G300_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G300_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G300_Delta_To_G6_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G301_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G301_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G301_Delta_To_G6_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G302_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G302_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G302_Delta_To_G6_Incr`
  - 0.1% (10) `Pl_GMstr_G303_Historical_Load`
  - 0.1% (10) `Pl_GMstr_G304_Historical_Load`
  - 0.1% (10) `Pl_GMstr_G305_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G306_Raw_Stage_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G307_Raw_Stage_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G308_Raw_Stage_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G306_G217_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G307_G217_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G308_G217_Historical_Load`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_metrics`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_target`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G309`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G310`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G311_code_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G312_config_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G311_code`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G313_plan_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G314_codes_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G314_codes`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G315_type_G316`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G317`
  - 0.1% (10) `Pl_Load_RAW_G304_home_office`
  - 0.1% (10) `Pl_Load_RAW_G304_group_cd_G313_map`
  - 0.1% (10) `Pl_Load_RAW_G304_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_RAW_G304_db_108_G318_G319`
  - 0.1% (10) `Pl_Load_RAW_G304_db_108_G318_service_codes`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G320_fl_mi`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G320_pa`
  - 0.1% (10) `Pl_Load_RAW_G304_db_108_G318_budget_amount`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G321`
  - 0.1% (10) `Pl_Load_RAW_G322_G270`
  - 0.1% (10) `Pl_Load_RAW_G322_G323`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_G324_type_code`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_G325_code`
  - 0.1% (10) `Pl_Load_RAW_G322_G120_ip`
  - 0.1% (10) `Pl_Load_RAW_G322_G271_procedure_code`
  - 0.1% (10) `Pl_Load_RAW_G322_claim_G326_status`
  - 0.1% (10) `Pl_Load_RAW_G322_client_mapping`
  - 0.1% (10) `Pl_Load_RAW_G322_G229_19_ip_G327_G328`
  - 0.1% (10) `Pl_Load_RAW_G322_G329_mapping`
  - 0.1% (10) `Pl_Load_RAW_G322_G330`
  - 0.1% (10) `Pl_Load_RAW_G322_G249_details`
  - 0.1% (10) `Pl_Load_RAW_G322_er_high_G331`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_diagnosis_code`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_language_code`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_place_of_G332_code`
  - 0.1% (10) `Pl_Load_RAW_G322_G120_op`
  - 0.1% (10) `Pl_Load_RAW_G322_G266_diag`
  - 0.1% (10) `Pl_Load_RAW_G322_G333`
  - 0.1% (10) `Pl_Load_RAW_G322_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_G334_G335_grp_code`
  - 0.1% (10) `Pl_Load_RAW_G322_G336`
  - 0.1% (10) `Pl_Load_RAW_G322_G337`
  - 0.1% (10) `Pl_Load_RAW_G322_mbr_segment`
  - 0.1% (10) `Pl_Load_STAGE_G322_G271_procedure_code`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_metrics`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_target`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G309`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G310`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G311_code_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G312_config_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G311_code`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G313_plan_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G314_codes_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G314_codes`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G315_type_G316`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G317`
  - 0.1% (10) `Pl_Load_G217_G304_home_office`
  - 0.1% (10) `Pl_Load_G217_G304_group_cd_G313_map`
  - 0.1% (10) `Pl_Load_G217_G304_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_G217_G304_db_108_G318_G319`
  - 0.1% (10) `Pl_Load_G217_G304_db_108_G318_service_codes`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G320_fl_mi`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G320_pa`
  - 0.1% (10) `Pl_Load_G217_G304_db_108_G318_budget_amount`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G321`
  - 0.1% (10) `Pl_Load_G217_G322_G270`
  - 0.1% (10) `Pl_Load_G217_G322_G323`
  - 0.1% (10) `Pl_Load_G217_G322_facets_G324_type_code`
  - 0.1% (10) `Pl_Load_G217_G322_facets_G325_code`
  - 0.1% (10) `Pl_Load_G217_G322_G120_ip`
  - 0.1% (10) `Pl_Load_G217_G322_G271_procedure_code`
  - 0.1% (10) `Pl_Load_G217_G322_claim_G326_status`
  - 0.1% (10) `Pl_Load_G217_G322_client_mapping`
  - 0.1% (10) `Pl_Load_G217_G322_G229_19_ip_G327_G328`
  - 0.1% (10) `Pl_Load_G217_G322_G329_mapping`
  - 0.1% (10) `Pl_Load_G217_G322_G330`
  - 0.1% (10) `Pl_Load_G217_G322_G249_details`
  - 0.1% (10) `Pl_Load_G217_G322_er_high_G331`
  - 0.1% (10) `Pl_Load_G217_G322_facets_diagnosis_code`
  - 0.1% (10) `Pl_Load_G217_G322_facets_language_code`
  - 0.1% (10) `Pl_Load_G217_G322_facets_place_of_G332_code`
  - 0.1% (10) `Pl_Load_G217_G322_G120_op`
  - 0.1% (10) `Pl_Load_G217_G322_G266_diag`
  - 0.1% (10) `Pl_Load_G217_G322_G333`
  - 0.1% (10) `Pl_Load_G217_G322_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_G217_G322_facets_G334_G335_grp_code`
  - 0.1% (10) `Pl_Load_G217_G322_G336`
  - 0.1% (10) `Pl_Load_G217_G322_G337`
  - 0.1% (10) `Pl_Load_G217_G322_mbr_segment`
  - 0.1% (10) `Pl_Load_RAW_G303_G338_G339`
  - 0.1% (10) `Pl_Load_RAW_G303_G340`
  - 0.1% (10) `Pl_Load_RAW_G304_G274_G341_G342`
  - 0.1% (10) `Pl_Load_RAW_G322_G255_G256`
  - 0.1% (10) `Pl_Load_G217_G303_G338_G339`
  - 0.1% (10) `Pl_Load_G217_G303_G340`
  - 0.1% (10) `Pl_Load_G217_G304_G274_G341_G342`
  - 0.1% (10) `Pl_Load_G217_G322_G255_G256`
  - 0.1% (10) `Pl_Load_RAW_G322_G272_group`
  - 0.1% (10) `Pl_Load_G217_G322_G272_group`
  - 0.1% (10) `Pl_Load_RAW_G322_G259_G253_mapping`
  - 0.1% (10) `Pl_Load_G217_G322_G259_G253_mapping`
  - 0.1% (10) `Pl_Load_RAW_G322_G272_diagnosis`
  - 0.1% (10) `Pl_Load_G217_G322_G272_diagnosis`
  - 0.1% (10) `Pl_Load_RAW_G322_ip_multiple_lines_G258`
  - 0.1% (10) `Pl_Load_G217_G322_ip_multiple_lines_G258`
  - 0.1% (10) `Pl_Load_RAW_G343_G157_members`
  - 0.1% (10) `Pl_Load_RAW_G343_G212_G157_data_G344`
  - 0.1% (10) `Pl_Load_RAW_G343_G345_temp`
  - 0.1% (10) `Pl_Load_RAW_G343_G346_load_log`
  - 0.1% (10) `Pl_Load_RAW_G343_G347_production`
  - 0.1% (10) `Pl_Load_RAW_G343_G347_production_G348`
  - 0.1% (10) `Pl_Load_RAW_G343_G349_production`
  - 0.1% (10) `Pl_Load_RAW_G343_ref_npi_data`
  - 0.1% (10) `Pl_Load_G217_G343_G157_members`
  - 0.1% (10) `Pl_Load_G217_G343_G212_G157_data_G344`
  - 0.1% (10) `Pl_Load_G217_G343_G345_temp`
  - 0.1% (10) `Pl_Load_G217_G343_G346_load_log`
  - 0.1% (10) `Pl_Load_G217_G343_G347_production`
  - 0.1% (10) `Pl_Load_G217_G343_G347_production_G348`
  - 0.1% (10) `Pl_Load_G217_G343_G349_production`
  - 0.1% (10) `Pl_Load_G217_G343_ref_npi_data`
  - 0.1% (10) `PL_MSTR_G128_G129_G124_RPT_MTH`
  - 0.1% (10) `Pl_G350_Load_G351_Derived_db_86_G245_G352`
  - 0.1% (10) `Pl_G350_Load_G351_G268_G353`
  - 0.1% (10) `PL_Mstr_G343_Raw_Stage_Incremental_Load_Pipeline`
  - 0.1% (10) `Pl_File_Based_Regular_Load_RAW_G89_output_claims_ip_all`
  - 0.1% (10) `Pl_Load_G217_G224_G354_G355_and_rr_G356`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_RR_2868_G357_DC_G358`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_G359`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_G360_for_G361_G362`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_SH_G180_Care_G363_New`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_G364_G365`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_834_G194_records received_on`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G366_G148_REPORT`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_DAILY_G367_Report_G148_G368`
  - 0.1% (10) `Pl_Load_RAW_G304_auth_360`
  - 0.1% (10) `Pl_Load_RAW_G304_auth_G369`
  - 0.1% (10) `Pl_Load_RAW_G304_claim_360`
  - 0.1% (10) `Pl_Load_RAW_G304_claims_G369`
  - 0.1% (10) `Pl_Load_RAW_G304_G243_G369`
  - 0.1% (10) `Pl_Load_G217_G304_auth_360`
  - 0.1% (10) `Pl_Load_G217_G304_auth_G369`
  - 0.1% (10) `Pl_Load_G217_G304_claim_360`
  - 0.1% (10) `Pl_Load_G217_G304_claims_G369`
  - 0.1% (10) `Pl_Load_G217_G304_G243_G369`
  - 0.1% (10) `PL_Load_Raw_G343_CLAIM_SERVICE_CATEGORY_OP`
  - 0.1% (10) `PL_Load_Raw_G343_G370`
  - 0.1% (10) `PL_Load_Raw_G343_IP_CATEGORY`
  - 0.1% (10) `PL_Load_Raw_G343_IP_G371_G372_BY_G373`
  - 0.1% (10) `PL_Load_Raw_G343_G374`
  - 0.1% (10) `PL_Load_Raw_G343_G374_G375_ADDED`
  - 0.1% (10) `PL_Load_Raw_G343_OP_CATEGORY`
  - 0.1% (10) `PL_Load_Raw_G343_PROC_CODE_G376_CT`
  - 0.1% (10) `PL_Load_Raw_G343_G377_CATEGORY`
  - 0.1% (10) `PL_Load_Raw_G343_REV`
  - 0.1% (10) `PL_Load_Raw_G343_PROC_RATE_G378_G379`
  - 0.1% (10) `PL_Load_Raw_G343_DIAG_G380_X_G271`
  - 0.1% (10) `PL_Load_Raw_G343_G324_TYPES_CODE_TABLE`
  - 0.1% (10) `PL_Load_Raw_G343_G381_G373_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G381_DX_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G381_G266_G384_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G381_G385_G386_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G387_G377_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G388_CODE_G383`
  - 0.1% (10) `PL_Load_Raw_G343_SERVICE_TYPE_CODE`
  - 0.1% (10) `PL_Load_Raw_G343_G382_G389_CD`
  - 0.1% (10) `PL_Load_G217_G343_CLAIM_SERVICE_CATEGORY_OP`
  - 0.1% (10) `PL_Load_G217_G343_G370`
  - 0.1% (10) `PL_Load_G217_G343_IP_CATEGORY`
  - 0.1% (10) `PL_Load_G217_G343_IP_G371_G372_BY_G373`
  - 0.1% (10) `PL_Load_G217_G343_G374`
  - 0.1% (10) `PL_Load_G217_G343_G374_G375_ADDED`
  - 0.1% (10) `PL_Load_G217_G343_OP_CATEGORY`
  - 0.1% (10) `PL_Load_G217_G343_PROC_CODE_G376_CT`
  - 0.1% (10) `PL_Load_G217_G343_G377_CATEGORY`
  - 0.1% (10) `PL_Load_G217_G343_REV`
  - 0.1% (10) `PL_Load_G217_G343_DIAG_G380_X_G271`
  - 0.1% (10) `PL_Load_G217_G343_G324_TYPES_CODE_TABLE`
  - 0.1% (10) `PL_Load_G217_G343_G381_G373_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G381_DX_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G381_G266_G384_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G381_G385_G386_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G387_G377_G383`
  - 0.1% (10) `PL_Load_G217_G343_G388_CODE_G383`
  - 0.1% (10) `PL_Load_G217_G343_SERVICE_TYPE_CODE`
  - 0.1% (10) `PL_Load_G217_G343_G382_G389_CD`
  - 0.1% (10) `PL_CHLD_G133_DE_G123_TO_RAW`
  - 0.1% (10) `PL_MSTR_FILE_RAW_TO_G123_DLY`
  - 0.1% (10) `PL_CHLD_G133_DE_RAW_TO_G123`
  - 0.1% (10) `PL_CHLD_G390_RR_2705_Provider_count_ADLS_To_Onprem`
  - 0.1% (10) `PL_CHLD_G390_RR_2470_G391_Member_G392_ADLS_To_Onprem`
  - 0.1% (10) `PL_CHLD_G390_RR_1641_Provider_Request_ADLS_To_Onprem`
  - 0.1% (10) `PL_CHLD_G390_RR_1728_G393_ADLS_To_Onprem`
  - 0.1% (10) `G394 Load to RAW G395`
  - 0.1% (10) `G394 Load to RAW G395_tracking_G396_G397_detail`
  - 0.1% (10) `G394 Load to RAW G395_tracking_G396_G212_data_v4`
  - 0.1% (10) `G394 Load to RAW G398_code_first_G399`
  - 0.1% (10) `G394 Load to RAW G400_G398`
  - 0.1% (10) `G394 Load to RAW provider_info`
  - 0.1% (10) `G394 Load to RAW transportation`
  - 0.1% (10) `G394 Load to RAW G401_G402`
  - 0.1% (10) `G394 Load to RAW dc_claims`
  - 0.1% (10) `G394 Load to RAW dc_members`
  - 0.1% (10) `G394 Load to RAW client_G403`
  - 0.1% (10) `G394 Load to RAW diagnosis_G404`
  - 0.1% (10) `G394 Load to RAW dc_G245`
  - 0.1% (10) `G394 Load to RAW G395_tracking_G396_G405`
  - 0.1% (10) `G394 Load to Raw G406 File Incremental load`
  - 0.1% (10) `G394 Load to G217 G406 File Incremental load`
  - 0.1% (10) `G394 Load to Raw G401_result File Incremental load`
  - 0.1% (10) `G394 Load to G217 G401_result File Incremental load`
  - 0.1% (10) `G394 G407 to RAW G408`
  - 0.1% (10) `G394 G407 to RAW G401_result`
  - 0.1% (10) `Pl_File_G16_G17_1200_Monthly_Regular_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_elig_G15_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G231_G233_G15_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G234_campaign_dtl_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G234_G235_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G237_G238_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G239_G147_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_master_G245_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G410_G411_membership_Regular_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G410_G411_membership_Regular_Delta_To_G217_Incr`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_NH_DLY`
  - 0.1% (10) `PL_CHLD_G110_G111_NH_G119`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_NC_DLY`
  - 0.1% (10) `PL_CHLD_G110_G111_NC_G119`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_G114_DLY`
  - 0.1% (10) `PL_CHLD_G110_G111_G114_G119`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_FL_DLY`
  - 0.1% (10) `PL_MSTR_G110_G111_DATA_G412_G110_FACETS_DLY`
  - 0.1% (10) `PL_GMSTR_G133_G138_G84_DLY`
  - 0.1% (10) `Pl_MSTR_G133_G138_G84_DLY`
  - 0.1% (10) `PL_CHLD_G84_RAW_G413_CM_G414_DATA_OUTPUT`
  - 0.1% (10) `PL_CHLD_G84_STD_G413_CM_G414_DATA_OUTPUT`
  - 0.1% (10) `PL_CHLD_G84_RAW_G415_G416_G417_EXT`
  - 0.1% (10) `PL_CHLD_G84_STD_G415_G416_G417_EXT`
  - 0.1% (10) `PL_CHLD_G84_RAW_G415_G416_G418_LOAD`
  - 0.1% (10) `PL_CHLD_G84_STD_G415_G416_G418_LOAD`
  - 0.1% (10) `PL_CHLD_G84_RAW_G413_RISK_G419_DATA_OUTPUT`
  - 0.1% (10) `PL_CHLD_G84_STD_G413_RISK_G419_DATA_OUTPUT`
  - 0.1% (10) `PL_GMSTR_CLM_G420_ALL_DLY`
  - 0.1% (10) `PL_Mstr_CLM_G420_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.1% (10) `PL_File_RAW_CLM_G420_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_CLM_G420_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STD_CLM_G420_Delta_To_STD_Incr`
  - 0.1% (10) `G421_NC_G131_G132`
  - 0.1% (10) `G421_Sub_LOB_G132`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_RAW_Sub_LOB_G132_G422`
  - 0.1% (10) `G212_SOURCE_RECORD_COUNT_G423`
  - 0.1% (10) `G212_SOURCE_RECORD_COUNT_G423_V2`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S3`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S4`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S5`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S6`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S7`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S8`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S9`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S3`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S4`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S5`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S6`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S7`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S8`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S9`
  - 0.1% (10) `PL_STG_STD_G60_Time_G424`
  - 0.1% (10) `PL_File_RAW_Load_G425_G426`
  - 0.1% (10) `Pl_CHLD_REPORTING_Update`
  - 0.1% (10) `Pl_CHLD_G427_CLAIMS_G428`
  - 0.1% (10) `Pl_CHLD_Check_G429`
  - 0.1% (10) `Pl_G430_To_Adls_Incr_01`
  - 0.1% (10) `Pl_G430_To_Adls_Full_01`
  - 0.1% (10) `Pl_G430_To_Adls_Incr_07`
  - 0.1% (10) `Pl_G430_To_Adls_Full_03`
  - 0.1% (10) `PL_GMSTR_G84_DIGITAL_RAW_STandard_INGESTION_G431_PIPELINE`
  - 0.1% (10) `PL_MSTR_G84_DIGITAL_RAW_STAGE_INGESTION_ G431_PIPELINE`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_G432`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_Line`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_Line_G432`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_Line_Modifier`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G92`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G92_G433`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G434_G433`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Pattern`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G433_processing_history`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_Line`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_Line_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_Line_Modifier`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G92`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G92_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G434_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Pattern`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G433_processing_history`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_Line`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_Line_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_Line_Modifier`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G92`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G92_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G434_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Pattern`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G433_processing_history`
  - 0.1% (10) `Pl_Gmstr_G435_G436_Plan_Regular_File_Load`
  - 0.1% (10) `PL_Mstr_G435_G436_Raw_Standard_File_Load_Pipeline`
  - 0.1% (10) `PL_File_RAW_G435_G436_G437_RISK_G438`
  - 0.1% (10) `PL_File_STAGE_G435_G436_G437_RISK_G438`
  - 0.1% (10) `PL_File_STANDARD_G435_G436_G437_RISK_G438`
  - 0.1% (10) `PL_File_RAW_G435_G436_RPT_G437`
  - 0.1% (10) `PL_File_STAGE_G435_G436_RPT_G437`
  - 0.1% (10) `PL_File_STANDARD_G435_G436_RPT_G437`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STAGE_NC_G131_G132`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STAGE_Sub_LOB_G132`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STAGE_Sub_LOB_G132_G422`
  - 0.1% (10) `PL_MSTR_CLM_G444_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G123_TO_G445_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_CLM_G446_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_CLM_G420_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_FACETS_MEMBERS_G447_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_RPT_G448_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G219_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STD_Sub_LOB_G132_G422`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_G449_Sub_LOB_G132_G422`
  - 0.1% (10) `Pl_CHLD_G130_PROCESSING_G427_CLAIM_G450_G428`
  - 0.1% (10) `PL_GMSTR_G451_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G451_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_G84_G451_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_GMSTR_G452_P2_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G452_P2_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_G84_G452_P2_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G452_P2_GROUP_1_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G452_P2_GROUP_1_Delta_To_G6_Incr`
  - 0.1% (10) `PL_MSTR_G445_CLM_G12_MTH_STD`
  - 0.1% (10) `PL_MSTR_G453_ONPREM_STG_G454`
  - 0.1% (10) `PL_FILE_G453_ONPREM_RAW_G454`
  - 0.1% (10) `PL_FILE_G453_RAW_STG_G454`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G457_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G457_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G457_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G103_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G103_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G103_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G458_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G458_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G458_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G459_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G459_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G459_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_2600_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_2600_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_2600_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_1200_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_1200_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_1200_Delta_To_STD_Incr`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G27_VW`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G27_VW`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G27_VW`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PS_KM_JC_G28`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PS_KM_JC_G28`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PS_KM_JC_G28`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G29_REQ_DATA`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_DATA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_DATA`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G29_REQ_G30`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_G30`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_G30`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_LOCATION_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_LOCATION_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_LOCATION_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_NAMES`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_NAMES`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_NAMES`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PER_G31_G32`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G32`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PER_G31_G32`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G33_DATA`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G33_DATA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G33_DATA`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_POSITION_DATA`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_POSITION_DATA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_POSITION_DATA`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_VALID_G34_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_VALID_G34_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_VALID_G34_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G35_CD_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G35_CD_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G35_CD_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G36_REASON_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G36_REASON_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G36_REASON_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G37_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G37_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G37_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G38_G39`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G38_G39`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G38_G39`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_EMAIL_G40`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_EMAIL_G40`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_EMAIL_G40`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G41`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G41`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G41`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_JOB`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_JOB`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_JOB`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G42_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G42_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G42_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G43_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G43_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G43_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G44_REVIEW`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G44_REVIEW`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G44_REVIEW`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_AUDIT_JOB`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_AUDIT_JOB`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_AUDIT_JOB`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PERSON`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PERSON`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PERSON`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G45_DATA_G46`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G45_DATA_G46`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G45_DATA_G46`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G40`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G40`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G40`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PER_G31_G47`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G47`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PER_G31_G47`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G29_REQ_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G48_REVIEW`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G48_REVIEW`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G48_REVIEW`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G49`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G49`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G49`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G50`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G50`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G50`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G33_PHONE`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G33_PHONE`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G33_PHONE`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G51_G52`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G51_G52`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G51_G52`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G53_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G53_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G53_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G54_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G54_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G54_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G55_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G55_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G55_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G56_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G56_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G56_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PS_G57_G58_G59`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PS_G57_G58_G59`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PS_G57_G58_G59`
  - 0.1% (10) `PL_G76_MEMBER_MERGE_STG`
  - 0.1% (10) `PL_GMSTR_Risk_G461_G462_G463_STG_INGESTION`
  - 0.1% (10) `PL_Mstr_Risk_G461_G462_RAW_STG_INGESTION`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_2_To_ADLS_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_3_To_ADLS_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_4_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_1_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_2_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_3_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_4_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_1_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_2_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_3_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_4_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_5_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_5_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_5_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_6_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_6_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_6_Delta_To_STD_Incr`
  - 0.1% (10) `PL_GMSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.1% (10) `PL_MSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6`
  - 0.1% (10) `PL_GMSTR_DLK_G1_EDH_STD_G464_ALL_DLY`
  - 0.1% (10) `PL_MSTR_DLK_G1_EDH_STD_G464_ALL_DLY`
  - 0.1% (10) `PL_G465_DLK_G1_EDH_STD_G464_ALL_DLY`
  - 0.1% (10) `PL_MSTR_G133_G466_G454`
  - 0.1% (10) `PL_CHLD_G133_G466_G454`
  - 0.1% (10) `Pl_Gmstr_G467_Regular_File_Load`
  - 0.1% (10) `PL_Mstr_G467_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_1_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_1_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_2_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_2_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_2_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_3_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_3_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_3_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_4_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_4_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_4_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_5_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_5_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_5_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_Gmstr_G3_G4_G5_Inbound_Regular_File_Load`
  - 0.1% (10) `PL_Mstr_G3_G4_G5_Inbound_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (10) `PL_File_RAW_G3_G4_G5_Inbound`
  - 0.1% (10) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.1% (10) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.1% (10) `PL_GMSTR_DLK_G1_EDH_BSL_ALL_MTH`
  - 0.1% (10) `PL_MSTR_DLK_G1_G1_BSL_ALL_G468`
  - 0.1% (10) `PL_G465_DLK_G1_G1_BSL_ALL_G468`
  - 0.1% (10) `PL_MSTR_G133_G134_DLY`
  - 0.1% (10) `PL_MSTR_G133_G134_FILE_EXT_TO_RAW_DLY`
  - 0.1% (10) `PL_MSTR_G133_G469_MBR_G134_DLY`
  - 0.1% (10) `PL_GMSTR_G470_G454`
  - 0.1% (10) `PL_MSTR_G470_G454_RAW_TO_STD`
  - 0.1% (10) `PL_File_RAW_G470_To_ADLS_G454`
  - 0.1% (10) `PL_File_STAGE_G470_ADLS_To_Delta_G454`
  - 0.1% (10) `PL_File_STD_G470_Delta_To_STD_G454`
  - 0.1% (10) `PL_G410_G273_Member_Stage_File_Based_Regular_Load`
  - 0.1% (10) `PL_GMSTR_G120_G463_STG_INGESTION`
  - 0.1% (10) `PL_MSTR_G120_FILE_RAW_STD_Load`
  - 0.1% (10) `PL_GMSTR_DLK_G471_STD_CLM_ALL_DLY`
  - 0.1% (10) `PL_MSTR_DLK_G471_STD_CLM_ALL_DLY`
  - 0.1% (10) `PL_G465_DLK_G471_STD_CLM_ALL_DLY`
  - 0.1% (8) `PL_MSTR_G472_G473_ADLS_To_Delta_Incr`
  - 0.1% (8) `WF_CHLD_G137_STD_G102_G126_G222`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G300`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G300_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G474_G475_DIR_OBJ_MAP`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G474_G475_DIR_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G474_OBJ_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G476`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G477_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G478`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G478_G479_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_G481`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_FORM_G482`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_G483_G484_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_HIST`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_IN_G485_STG`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_G486_MAP`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G487_G488`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G487_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_CO_G489_G490`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G481_G488_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G481_G491_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_DOC`
  - 0.0% (6) `PL_CHLD_G84_STAGE_DOC_G492_G493_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_DOC_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G494_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G495_DTL`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G495_G496`
  - 0.0% (6) `PL_CHLD_G84_STAGE_FORM_G497_GRP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_FORM_G482_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G498_SRC_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_LANG_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_LOB_G477_MAP`
  - 0.0% (6) `PL_CHLD_G84_STAGE_LOB_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486_ROLE`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486_ROLE_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486_TYP_REF`
  - 0.0% (4) `PL_GMSTR_G135_G400_Auth_G499_DLY`
  - 0.0% (4) `PL_Mstr_G135_G499_Raw_Stg_Std_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0100`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0100`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0100`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0500`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0500`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0500`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0530`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0530`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0530`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0540`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0540`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0540`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_2400`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_2400`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_2400`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_7100`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_7100`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_7100`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_7200`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_7200`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_7200`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_0192`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_0192`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_0192`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_1200`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_1200`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_1200`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_2600`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_2600`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_2600`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_6400`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_6400`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_6400`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_7700`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_7700`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_7700`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_8213`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_8213`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_8213`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G502`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G502`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G502`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G503`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G503`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G503`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G504`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G504`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G504`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G505`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G505`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G505`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G506`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G506`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G506`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G507`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G507`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G507`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G508`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G508`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G508`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_5400`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_5400`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_5400`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_0900`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_0900`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_0900`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_2100`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_2100`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_2100`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_G509`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_G509`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_G509`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G103`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G103`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G103`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G510`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G510`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G510`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G457`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G457`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G457`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0550`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0550`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0550`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_G25`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_G25`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_G25`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_5420`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_5420`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_5420`
  - 0.0% (4) `PL_GMSTR_G135_G400_Auth_G499_Hist`
  - 0.0% (4) `PL_Mstr_G135_G499_Raw_Stg_Std_Hist_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_G135_0100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0500_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0500_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0500_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0530_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0530_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0530_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0540_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0540_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0540_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_2400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_2400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_2400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_7100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_7100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_7100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_7200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_7200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_7200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0192_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0192_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0192_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_1200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_1200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_1200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_2600_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_2600_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_2600_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_6400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_6400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_6400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_7700_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_7700_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_7700_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_8213_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_8213_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_8213_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G502_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G502_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G502_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G503_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G503_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G503_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G504_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G504_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G504_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G505_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G505_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G505_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G506_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G506_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G506_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G507_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G507_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G507_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G508_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G508_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G508_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_5400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_5400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_5400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0900_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0900_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0900_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_2100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_2100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_2100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0550_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0550_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0550_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G25_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G25_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G25_G499_G511_G242_Hist`
  - 0.0% (4) `WF_Mstr_G512_STG_STD_INGESTION`
  - 0.0% (4) `WF_CHLD_FILE_STG_G512`
  - 0.0% (4) `WF_CHLD_FILE_STD_G512`
  - 0.0% (4) `PL_GMSTR_G1_G66_FILE_RAW_TO_STG_STD_DLY`
  - 0.0% (4) `PL_MSTR_G1_G66_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G66_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G66_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G66_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_RAW_STG_INGESTION`
  - 0.0% (4) `PL_GMSTR_G1_G65_FILE_RAW_TO_STG_STD_MTH`
  - 0.0% (4) `PL_GMSTR_G1_G67_FILE_RAW_TO_STG_STD_G85`
  - 0.0% (4) `PL_MSTR_G1_G67_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G67_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G67_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G67_Delta_To_STD_Incr`
  - 0.0% (4) `PL_GMSTR_G1_G68_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G68_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G68_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G68_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G68_Delta_To_STD_Incr`
  - 0.0% (4) `PL_File_RAW_G1_G2_G78`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G78`
  - 0.0% (4) `PL_File_STD_G1_G2_G78`
  - 0.0% (4) `PL_File_RAW_G1_G2_G79`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G79`
  - 0.0% (4) `PL_File_STD_G1_G2_G79`
  - 0.0% (4) `PL_File_RAW_G1_G2_G80`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G80`
  - 0.0% (4) `PL_File_STD_G1_G2_G80`
  - 0.0% (4) `PL_GMSTR_G1_G2_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G2_RAW_STG_INGESTION`
  - 0.0% (4) `PL_File_RAW_G1_G2_G81`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G81`
  - 0.0% (4) `PL_File_STD_G1_G2_G81`
  - 0.0% (4) `PL_File_RAW_G1_G2_G82`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G82`
  - 0.0% (4) `PL_FILE_STD_G1_G2_G82`
  - 0.0% (4) `PL_File_RAW_G1_G2_G83`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G83`
  - 0.0% (4) `PL_File_STD_G1_G2_G83`
  - 0.0% (4) `PL_MSTR_G1_G69_RAW_STG_INGESTION`
  - 0.0% (4) `PL_GMSTR_G1_G69_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G69_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Case_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Case_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Case_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_G70_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_G70_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_G70_Delta_To_STD_Incr`
  - 0.0% (4) `PL_GMSTR_G135_G242_MONTHLY_FILE_INGESTION`
  - 0.0% (4) `PL_Mstr_G135_G242_G136_RAW_STD_INGESTION`
  - 0.0% (4) `PL_GMSTR_G135_G242_G136_HIST_FILE_INGESTION`
  - 0.0% (4) `PL_Mstr_G135_G242_G136_HIST_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G513_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G513_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G513_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G513_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G514_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G514_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G514_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G514_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G515_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G515_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G515_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G516_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G517_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G517_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G517_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G517_RAW_STD_INGESTION`
  - 0.0% (4) `PL_GMSTR_G14_G15_HIST_DLY`
  - 0.0% (4) `PL_MSTR_G14_G15_HIST_DLY`
  - 0.0% (4) `PL_File_RAW_G14_G15_To_ADLS_G13`
  - 0.0% (4) `PL_File_STAGE_G14_G15_ADLS_To_Delta_G13`
  - 0.0% (4) `PL_File_STD_G14_G15_Delta_To_STD_G13`
  - 0.0% (4) `Pl_Gmstr_G518_Regular_File_Load`
  - 0.0% (4) `PL_Mstr_G518_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_G518_G202_G519_G203_1_3_G204 Risk_List_extract`
  - 0.0% (4) `PL_File_RAW_G518_G520_G521_J_01_CM_Interaction_G522_Rpt_G523_extract`
  - 0.0% (4) `PL_GMSTR_G472_G473_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G472_G473_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G472_G473_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_G524_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_G524_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_G524_Delta_To_STD_Incr`
  - 0.0% (4) `PL_File_RAW_G135_G525_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G525_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G525_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G525_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G499_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G499_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G499_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G499_RAW_STD_INGESTION`
  - 0.0% (4) `PL_GMSTR_WC_CD_FILE_G454`
  - 0.0% (4) `PL_Mstr_WC_CD_G90_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7700_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_7700_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7700_G527_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_1200_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_1200_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_1200_G527_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7100_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_7100_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7100_G527_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_2100_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_2100_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_2100_G527_G90`
  - 0.0% (4) `PL_GMSTR_WC_INB_G528_FILE_G463`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_2400_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_2400_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_2100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_2100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7200_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7200_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7700_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7700_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G149_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G149_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G149_DSNP_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G149_DSNP_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G103_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G103_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_1200_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_1200_WC_INB_G528`
  - 0.0% (4) `PL_GMSTR_G90_FILE_WC_Response_DLY`
  - 0.0% (4) `PL_Mstr_WC_G529_G90_Raw_Stage_Regular_File_Load_Pipeline_DLY`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G530_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G530_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G530_Response_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G531_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G531_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G531_Response_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G532_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G532_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G532_Response_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G533_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G533_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G533_Response_G90`
  - 0.0% (4) `PL_GMSTR_WC_G8_FILE_G463`
  - 0.0% (4) `PL_Mstr_WC_G8_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_WC_G8_2100`
  - 0.0% (4) `PL_File_STAGE_WC_G8_2100`
  - 0.0% (4) `PL_File_STD_WC_G8_2100`
  - 0.0% (4) `PL_File_RAW_WC_G8_2400`
  - 0.0% (4) `PL_File_STAGE_WC_G8_2400`
  - 0.0% (4) `PL_File_STD_WC_G8_2400`
  - 0.0% (4) `PL_File_RAW_WC_G8_7100`
  - 0.0% (4) `PL_File_STAGE_WC_G8_7100`
  - 0.0% (4) `PL_File_STD_WC_G8_7100`
  - 0.0% (4) `PL_File_RAW_WC_G8_7200`
  - 0.0% (4) `PL_File_STAGE_WC_G8_7200`
  - 0.0% (4) `PL_File_STD_WC_G8_7200`
  - 0.0% (4) `PL_File_RAW_WC_G8_7700`
  - 0.0% (4) `PL_File_STAGE_WC_G8_7700`
  - 0.0% (4) `PL_File_STD_WC_G8_7700`
  - 0.0% (4) `PL_File_RAW_WC_G8_G149`
  - 0.0% (4) `PL_File_STAGE_WC_G8_G149`
  - 0.0% (4) `PL_File_STD_WC_G8_G149`
  - 0.0% (4) `PL_File_RAW_WC_G8_G149_DSNP`
  - 0.0% (4) `PL_File_STAGE_WC_G8_G149_DSNP`
  - 0.0% (4) `PL_File_STD_WC_G8_G149_DSNP`
  - 0.0% (4) `PL_File_RAW_WC_G8_G103`
  - 0.0% (4) `PL_File_STAGE_WC_G8_G103`
  - 0.0% (4) `PL_File_STD_WC_G8_G103`
  - 0.0% (4) `PL_File_RAW_WC_G8_1200`
  - 0.0% (4) `PL_File_STAGE_WC_G8_1200`
  - 0.0% (4) `PL_File_STD_WC_G8_1200`
  - 0.0% (4) `PL_Mstr_WC_G528_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `WF_Mstr_G534_STG_STD_INGESTION`
  - 0.0% (4) `WF_CHLD_FILE_STG_G534`
  - 0.0% (4) `WF_CHLD_FILE_STD_G534`
  - 0.0% (2) `PL_File_G8_G9_G10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G8_G9_G10_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G8_G11_G10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G8_G11_G10_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G8_SD_IND_RISK_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G8_SD_IND_RISK_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_G8_ALL_MTH`
  - 0.0% (2) `PL_MSTR_G8_ALL_MTH`
  - 0.0% (2) `PL_G535_FILE_RAW_STAGE_INGESTION`
  - 0.0% (2) `PL_GMSTR_G536_CM_G103_DLY`
  - 0.0% (2) `PL_MSTR_G536_CM_G103_DLY`
  - 0.0% (2) `PL_File_G536_CM_G103_DNC_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Outreach_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Billing_RPT_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_G537_DTL_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Reports_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_DNC_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Outreach_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Billing_RPT_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_G537_DTL_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Reports_Delta_To_STD_Incr`
  - 0.0% (2) `Pl_File_G16_G17_1200_Monthly_Regular_ADLS_To_Delta_Incr`
  - 0.0% (2) `Pl_File_G16_G17_7200_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.0% (2) `Pl_File_G16_G17_7700_Daily_TPL_ADLS_To_Delta_Incr`
  - 0.0% (2) `Pl_File_G16_G17_7700_Monthly_TPL_ADLS_To_Delta_Incr`
  - 0.0% (2) `WF_MSTR_FILE_RAW_STD_MI_TPL_ALL_DLY`
  - 0.0% (2) `WF_CHLD_FILE_STG_MI_TPL`
  - 0.0% (2) `WF_CHLD_FILE_STD_MI_TPL`
  - 0.0% (2) `PL_MSTR_G133_MBR_G145_G538`
  - 0.0% (2) `PL_MSTR_G133_MBR_G145_G538_FILE_EXT_TO_RAW`
  - 0.0% (2) `PL_CHLD_G133_MBR_G145_G538_RAW_TO_G123`
  - 0.0% (2) `PL_GMSTR_G16_820_ALL_DLY`
  - 0.0% (2) `PL_Mstr_G16_820_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (2) `PL_File_G16_820_G103_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G509_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G508_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G506_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G503_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G505_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G103_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G509_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G508_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G506_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G503_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G505_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_G539_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_G539_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_G134_7200_G539_G85`
  - 0.0% (2) `PL_MSTR_MBR_G134_7200_G539_G85`
  - 0.0% (2) `PL_File_MBR_G134_7200_FACETS_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_FACETS_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_G134_7200_FACETS_G85`
  - 0.0% (2) `PL_MSTR_MBR_G134_7200_FACETS_G85`
  - 0.0% (2) `PL_File_MBR_G134_7200_G540_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_G540_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_G134_7200_G540_G85`
  - 0.0% (2) `PL_MSTR_MBR_G134_7200_G540_G85`
  - 0.0% (2) `pl_G541_G542_stg_load`
  - 0.0% (2) `PL_File_G297_7200_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G297_7200_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G297_7200_24_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G297_7200_24_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_G297_7200_DLY`
  - 0.0% (2) `PL_MSTR_G297_7200_DLY`
  - 0.0% (2) `PL_UM_G460_G452_SRC_TO_RAW`
  - 0.0% (2) `PI_Mstr_G460_G452_Source_to_Stage`
  - 0.0% (2) `PL_GMSTR_G452_G84_RAW_To_STG_TO_STD_DLY`
  - 0.0% (2) `PL_MSTR_G452_G84_RAW_To_STG_TO_STD_DLY`
  - 0.0% (2) `PL_G84_G452_GROUP_1_To_ADLS_Incr`
  - 0.0% (2) `PL_G84_G452_GROUP_1_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_G452_GROUP_1_Delta_To_G6_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_1_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_2_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_3_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_4_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_5_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_6_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_7_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_8_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_9_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_GROUP_2_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STAGE_Risk_G461_Medicaid_GROUP_1_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STAGE_Risk_G461_Medicaid_GROUP_2_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STAGE_Risk_G461_Medicaid_GROUP_3_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_SFMC_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_SFMC_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_OUTREACH_ALL_DLY`
  - 0.0% (2) `PL_MSTR_MBR_OUTREACH_ALL_DLY`
  - 0.0% (2) `PL_GMSTR_CLM_G12_G13_ALL_G98`
  - 0.0% (2) `PL_MSTR_CLM_G12_G13_RAW_TO_STD`
  - 0.0% (2) `PL_File_CLM_G12_G13_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_CLM_G12_G13_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_TPL_ALL_G85`
  - 0.0% (2) `WF_MSTR_FILE_RAW_STD_CAQH_ALL_DLY`
  - 0.0% (2) `WF_CHLD_FILE_STG_CAQH`
  - 0.0% (2) `WF_CHLD_FILE_STD_CAQH`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_MBR`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_CLM`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_G206`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_G222`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_RX`
  - 0.0% (2) `WF_CHLD_G137_STD_G102_G126_RX`
- patterns:
  - 7.3% (980) `PL_Gmstr_G97_Historical_Load`
  - 4.7% (630) `PL_CHLD_G110_G111_STD_TO_G112_G113`
  - 3.6% (480) `PL_CHLD_G110_G111_FL_G112`
  - 1.0% (140) `PL_CHLD_G110_G111_G114_G112`
  - 0.6% (80) `PL_CHLD_G110_G111_RAW_TO_STD_G113`
  - 0.6% (80) `WF_G115_G116_SF_STD`
  - 0.5% (66) `PL_CHLD_DATA_G117_G118`
  - 0.4% (60) `PL_CHLD_G110_G111_G112_TO_G119_G113`
  - 0.4% (50) `PL_File_RAW_G120_G121_G122_To_ADLS_Incr`
  - 0.4% (50) `PL_File_STAGE_G120_G121_G122_ADLS_To_Delta_Incr`
  - 0.4% (50) `PL_File_STD_G120_G121_G122_Delta_To_STD_Incr`
  - 0.3% (40) `PL_CHLD_G110_G111_G123_TO_RAW_INSERT`
  - 0.3% (40) `PL_CHLD_G110_G111_G119_TO_G124_G125`
  - 0.3% (40) `PL_CHLD_G110_G111_G126_TO_G124_G125`
  - 0.2% (30) `PL_CHLD_G110_G111_G127_PROCESS_G113`
  - 0.1% (20) `PL_MSTR_G128_G129_G124_RPT_DLY`
  - 0.1% (20) `Pl_CHLD_G130_PROCESSING_NC_G131_G132`
  - 0.1% (20) `Pl_CHLD_G130_PROCESSING_Sub_LOB_G132`
  - 0.1% (20) `PL_CHLD_G133_G134_FILE_RAW_TO_G123_DLY`
  - 0.1% (14) `PL_File_RAW_G135_G136_To_ADLS_Incr`
  - 0.1% (14) `PL_File_STAGE_G135_G136_ADLS_To_Delta_Incr`
  - 0.1% (14) `PL_File_STD_G135_G136_Delta_To_STD_Incr`
  - 0.1% (14) `PL_File_RAW_G135_G136_Hist_To_ADLS_Incr`
  - 0.1% (14) `PL_File_STAGE_G135_G136_Hist_ADLS_To_Delta_Incr`
  - 0.1% (14) `PL_File_STD_G135_G136_Hist_Delta_To_STD_Incr`
  - 0.1% (14) `WF_CHLD_G137_STD_G102_G126_CLM`
  - 0.1% (12) `PL_GMSTR_G133_G138_FILE_DLY`
  - 0.1% (12) `PL_MSTR_G133_G138_FILE_DLY`
  - 0.1% (12) `Pl_Mstr_Digital_G139_Raw_Stage_Ingestion`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3011_G140_POP_Update`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_2950_G141_G142_Outreach`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_2699_G143_MEMBER_GROUP`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G144_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G15 - G145 - G146 IDENTIFIED`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G147_G148_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G149_G148_REPORT_G150`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_Current_mbr_list_G151`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_INTERNAL_FILE_100_Unique`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_INTERNAL_FILE_500_Unique`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_1315_Lead_G152`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_33_G153_CM`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G154_G155_Profiles`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G154_G156_Profiles`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_5623`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157_G158`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G159_G148_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G160_Outreach_Roster`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G161_outreach Report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3292_2243_Daily_G158_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157 G162 Lead Extract`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G163_G148_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3242_OH_BH_ER_0_20`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3232_G164_House_G165`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G149_G166_MEMBER_LIST_NEW`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_KF_G166_MEMBER_LIST_NEW`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G139_G167`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157_G168_MEMBER_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_Weekly_Auth_G169_G157`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_ip_daily_census_report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G170_G171_G172_G173`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G174`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G175`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G176`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G177`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G157_G170_G178_RISK_REPORT`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G179_G144_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G180_G181`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_ip_claims_G182`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G163_G183_Current_G184`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_RR_3081_OH_Membership_Report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G185_G186_G187_MEMBERS`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G188_Identified_Members`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G189_pop`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G190`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G191_DOC_G192_in_3_G193`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_834_G194_records_received_since`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G195_G196_Report`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G197_<LOCAL_DENYLIST> - G198`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G197_<LOCAL_DENYLIST> - Exit`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G199`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G200_42_G201_Daily`
  - 0.1% (12) `PL_CHLD_G133_G138_FL_G123_RAW_G202_G203_1_2_3_G204_RISK_LIST`
  - 0.1% (12) `PL_MSTR_G138_G205_DLY`
  - 0.1% (12) `PL_CHLD_G138_G205_TO_RAW_LOAD`
  - 0.1% (12) `DATA_G117_DEPENDENCY_G132`
  - 0.1% (12) `WF_CHLD_G137_STD_G102_G126_MBR`
  - 0.1% (12) `WF_CHLD_G137_STD_G102_G126_G206`
  - 0.1% (10) `Pl_File_G207_G208_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_G207_G209_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_CLM_G210_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_CLM_RX_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_File_G207_G211_To_ADLS_Incr_01`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_02`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_03`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_04`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_05`
  - 0.1% (10) `Pl_G212_To_Adls_Incr_06`
  - 0.1% (10) `Pl_G212_To_Adls_Full_02`
  - 0.1% (10) `Pl_Mstr_G212_G213_Full-Incr_Hist_01`
  - 0.1% (10) `G214_G215_master`
  - 0.1% (10) `Pl_File_G216_File_To_Adls_01`
  - 0.1% (10) `Pl_File_G16_834_1250_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_1300_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_2900_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_3700_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_6100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0500_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0530_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0540_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0900_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_1200_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2400_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2600_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_5400_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6400_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7100_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7200_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G16_834_1250_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_1300_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_2900_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_3700_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_834_6100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0500_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0530_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0540_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_0900_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_1200_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2400_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_2600_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_5400_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_6400_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7100_Stage_To_G217_Incr`
  - 0.1% (10) `Pl_File_G16_835_OB_7200_Stage_To_G217_Incr`
  - 0.1% (10) `PI_Mstr_CA_CURRENT_G218_Raw_Stg`
  - 0.1% (10) `Pl_G219_case_G220_G84_to_adls`
  - 0.1% (10) `Pl_G219_case_G220_to_adls`
  - 0.1% (10) `File_Raw_To_Stage_UM_G221_Load`
  - 0.1% (10) `Pl_G128_G222_Refresh_G223`
  - 0.1% (10) `PL_Gmstr_G97_Historical_Load_G224`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_notes_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G229_acfc_member_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G230_claim_summary_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G232_G15_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_elig_G15_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G233_G15_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_campaign_dtl_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_G235_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G236_G157_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G237_G238_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G239_G147_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_er_G240_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G241_G242_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G243_G244_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_master_G245_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G226_open_G227_G228_notes_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G229_acfc_member_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G230_claim_summary_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G232_G15_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_elig_G15_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_G233_G15_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_Campaign_Dtl_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G234_G235_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G236_G157_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G237_G238_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G239_G147_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_er_G240_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G241_G242_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G243_G244_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_master_G245_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G230_claim_summary_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_campaign_dtl_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_G235_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G237_G238_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G239_G147_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_er_G240_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G230_claim_summary_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_Campaign_Dtl_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G234_G235_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G237_G238_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G239_G147_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_er_G240_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_enroll_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_medical_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_pharmacy_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_data_rx_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G247_data_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_ip_data_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_G249_G132_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_exec_G132_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_exec_plan_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_members_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_G250_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G246_G12_G248_G251_category_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G252_G253_G254_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G255_G256_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G257_details_G258_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G259_G260_MAPPING_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G252_rx_G261_G262_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_one_time_17_tables_load_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_db_94_G246_G12_G248_3_tables_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_G252_db_G263_G252_procedure_G264_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_G252_rx_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_Derived_G225_social_det_G265_mbr_all_lob_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_G84_G225_History_master_G245_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_master_G245_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G266_list_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_RR_568_REL_G267_DATA_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G268_DATE_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_RR_568_REL_G267_DATA_G268_DATE_Delta_To_G217_Incr`
  - 0.1% (10) `Pl_File_G225_G269_group_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G270_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_social_det_G265_mbr_all_lob_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_facets_pcp_transfer_all_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G266_DIAG_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G271_PROCEDURE_CODE_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_CLIENT_MAPPING_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G259_G253_MAPPING_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_G272_DIAGNOSIS_To_ADLS_Incr`
  - 0.1% (10) `Pl_G84_G225_History_IP_MULTIPLE_LINES_G258_To_ADLS_Incr`
  - 0.1% (10) `PL_Mstr_G225_Load_G217_social_det_G265_mbr_all_lob`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_FACETS_G274_G275_G276`
  - 0.1% (10) `PL_GMSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G115_PIPELINE`
  - 0.1% (10) `PL_MSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G115_PIPELINE`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G278`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G279_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G34_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_DATES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G280`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G281`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G282`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_SYSTEM_G132_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_SYSTEM_PROMPT_TYPES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_TEXT_VALUES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G283_DEFINITIONS`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G283_G284`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G285_G286`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G285_G287`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_WF_JOB_G280`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G288_ITEM_STATUSES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G288_ITEMS`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_V_G289`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_G290`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_SF_SYSTEM_G287`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G290`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_FOLDER_TYPES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_G280`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_DOCUMENT_TYPES`
  - 0.1% (10) `Pl_G84_G115_G84_To_ADLS_G277_G115_DOCUMENT_STATUS_DEFINITIONS`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_FACETS_G274_G275_G276`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_01`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_02`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_05`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_06`
  - 0.1% (10) `PL_CHLD_G273_RAW_G84_G291_EXT_G292_STATUS_G293_07`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_01`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_02`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_05`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_06`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G291_EXT_G292_STATUS_G293_07`
  - 0.1% (10) `PL_CHLD_G273_STD_G84_G294_EXT_G295_G296_G297_H`
  - 0.1% (10) `PL_GMSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G298_PIPELINE`
  - 0.1% (10) `PL_MSTR_G84_DIGITAL_RAW_STAGE_INGESTION_G277_G298_PIPELINE`
  - 0.1% (10) `Pl_G84_G277_G298_G84_To_ADLS_G277_G298_EXT_PROV_PROCESS_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Stage_G277_G298_EXT_PROV_PROCESS_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Delta_G113_G277_G298_EXT_PROV_PROCESS_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_G84_To_ADLS_G277_G298_EXT_PROV_SUMMARY_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Stage_G277_G298_EXT_PROV_SUMMARY_HIST`
  - 0.1% (10) `Pl_G84_G277_G298_ADLS_To_Delta_G113_G277_G298_EXT_PROV_SUMMARY_HIST`
  - 0.1% (10) `Pl_Files_To_Adls`
  - 0.1% (10) `PL_G84_G299_MEMBER_G300_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G300_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G300_Delta_To_G6_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G301_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G301_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G301_Delta_To_G6_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G302_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G302_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G299_MEMBER_G302_Delta_To_G6_Incr`
  - 0.1% (10) `Pl_GMstr_G303_Historical_Load`
  - 0.1% (10) `Pl_GMstr_G304_Historical_Load`
  - 0.1% (10) `Pl_GMstr_G305_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G306_Raw_Stage_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G307_Raw_Stage_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G308_Raw_Stage_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G306_G217_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G307_G217_Historical_Load`
  - 0.1% (10) `Pl_Mstr_G308_G217_Historical_Load`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_metrics`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_target`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G309`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G310`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G311_code_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G312_config_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G311_code`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G313_plan_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_89_G277_G314_codes_input`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G314_codes`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G315_type_G316`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G317`
  - 0.1% (10) `Pl_Load_RAW_G304_home_office`
  - 0.1% (10) `Pl_Load_RAW_G304_group_cd_G313_map`
  - 0.1% (10) `Pl_Load_RAW_G304_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_RAW_G304_db_108_G318_G319`
  - 0.1% (10) `Pl_Load_RAW_G304_db_108_G318_service_codes`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G320_fl_mi`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G320_pa`
  - 0.1% (10) `Pl_Load_RAW_G304_db_108_G318_budget_amount`
  - 0.1% (10) `Pl_Load_RAW_G304_db_mw_G321`
  - 0.1% (10) `Pl_Load_RAW_G322_G270`
  - 0.1% (10) `Pl_Load_RAW_G322_G323`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_G324_type_code`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_G325_code`
  - 0.1% (10) `Pl_Load_RAW_G322_G120_ip`
  - 0.1% (10) `Pl_Load_RAW_G322_G271_procedure_code`
  - 0.1% (10) `Pl_Load_RAW_G322_claim_G326_status`
  - 0.1% (10) `Pl_Load_RAW_G322_client_mapping`
  - 0.1% (10) `Pl_Load_RAW_G322_G229_19_ip_G327_G328`
  - 0.1% (10) `Pl_Load_RAW_G322_G329_mapping`
  - 0.1% (10) `Pl_Load_RAW_G322_G330`
  - 0.1% (10) `Pl_Load_RAW_G322_G249_details`
  - 0.1% (10) `Pl_Load_RAW_G322_er_high_G331`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_diagnosis_code`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_language_code`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_place_of_G332_code`
  - 0.1% (10) `Pl_Load_RAW_G322_G120_op`
  - 0.1% (10) `Pl_Load_RAW_G322_G266_diag`
  - 0.1% (10) `Pl_Load_RAW_G322_G333`
  - 0.1% (10) `Pl_Load_RAW_G322_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_RAW_G322_facets_G334_G335_grp_code`
  - 0.1% (10) `Pl_Load_RAW_G322_G336`
  - 0.1% (10) `Pl_Load_RAW_G322_G337`
  - 0.1% (10) `Pl_Load_RAW_G322_mbr_segment`
  - 0.1% (10) `Pl_Load_STAGE_G322_G271_procedure_code`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_metrics`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_target`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G309`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G310`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G311_code_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G312_config_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G311_code`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G313_plan_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_89_G277_G314_codes_input`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G314_codes`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G315_type_G316`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G317`
  - 0.1% (10) `Pl_Load_G217_G304_home_office`
  - 0.1% (10) `Pl_Load_G217_G304_group_cd_G313_map`
  - 0.1% (10) `Pl_Load_G217_G304_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_G217_G304_db_108_G318_G319`
  - 0.1% (10) `Pl_Load_G217_G304_db_108_G318_service_codes`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G320_fl_mi`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G320_pa`
  - 0.1% (10) `Pl_Load_G217_G304_db_108_G318_budget_amount`
  - 0.1% (10) `Pl_Load_G217_G304_db_mw_G321`
  - 0.1% (10) `Pl_Load_G217_G322_G270`
  - 0.1% (10) `Pl_Load_G217_G322_G323`
  - 0.1% (10) `Pl_Load_G217_G322_facets_G324_type_code`
  - 0.1% (10) `Pl_Load_G217_G322_facets_G325_code`
  - 0.1% (10) `Pl_Load_G217_G322_G120_ip`
  - 0.1% (10) `Pl_Load_G217_G322_G271_procedure_code`
  - 0.1% (10) `Pl_Load_G217_G322_claim_G326_status`
  - 0.1% (10) `Pl_Load_G217_G322_client_mapping`
  - 0.1% (10) `Pl_Load_G217_G322_G229_19_ip_G327_G328`
  - 0.1% (10) `Pl_Load_G217_G322_G329_mapping`
  - 0.1% (10) `Pl_Load_G217_G322_G330`
  - 0.1% (10) `Pl_Load_G217_G322_G249_details`
  - 0.1% (10) `Pl_Load_G217_G322_er_high_G331`
  - 0.1% (10) `Pl_Load_G217_G322_facets_diagnosis_code`
  - 0.1% (10) `Pl_Load_G217_G322_facets_language_code`
  - 0.1% (10) `Pl_Load_G217_G322_facets_place_of_G332_code`
  - 0.1% (10) `Pl_Load_G217_G322_G120_op`
  - 0.1% (10) `Pl_Load_G217_G322_G266_diag`
  - 0.1% (10) `Pl_Load_G217_G322_G333`
  - 0.1% (10) `Pl_Load_G217_G322_client_cd_G313_map`
  - 0.1% (10) `Pl_Load_G217_G322_facets_G334_G335_grp_code`
  - 0.1% (10) `Pl_Load_G217_G322_G336`
  - 0.1% (10) `Pl_Load_G217_G322_G337`
  - 0.1% (10) `Pl_Load_G217_G322_mbr_segment`
  - 0.1% (10) `Pl_Load_RAW_G303_G338_G339`
  - 0.1% (10) `Pl_Load_RAW_G303_G340`
  - 0.1% (10) `Pl_Load_RAW_G304_G274_G341_G342`
  - 0.1% (10) `Pl_Load_RAW_G322_G255_G256`
  - 0.1% (10) `Pl_Load_G217_G303_G338_G339`
  - 0.1% (10) `Pl_Load_G217_G303_G340`
  - 0.1% (10) `Pl_Load_G217_G304_G274_G341_G342`
  - 0.1% (10) `Pl_Load_G217_G322_G255_G256`
  - 0.1% (10) `Pl_Load_RAW_G322_G272_group`
  - 0.1% (10) `Pl_Load_G217_G322_G272_group`
  - 0.1% (10) `Pl_Load_RAW_G322_G259_G253_mapping`
  - 0.1% (10) `Pl_Load_G217_G322_G259_G253_mapping`
  - 0.1% (10) `Pl_Load_RAW_G322_G272_diagnosis`
  - 0.1% (10) `Pl_Load_G217_G322_G272_diagnosis`
  - 0.1% (10) `Pl_Load_RAW_G322_ip_multiple_lines_G258`
  - 0.1% (10) `Pl_Load_G217_G322_ip_multiple_lines_G258`
  - 0.1% (10) `Pl_Load_RAW_G343_G157_members`
  - 0.1% (10) `Pl_Load_RAW_G343_G212_G157_data_G344`
  - 0.1% (10) `Pl_Load_RAW_G343_G345_temp`
  - 0.1% (10) `Pl_Load_RAW_G343_G346_load_log`
  - 0.1% (10) `Pl_Load_RAW_G343_G347_production`
  - 0.1% (10) `Pl_Load_RAW_G343_G347_production_G348`
  - 0.1% (10) `Pl_Load_RAW_G343_G349_production`
  - 0.1% (10) `Pl_Load_RAW_G343_ref_npi_data`
  - 0.1% (10) `Pl_Load_G217_G343_G157_members`
  - 0.1% (10) `Pl_Load_G217_G343_G212_G157_data_G344`
  - 0.1% (10) `Pl_Load_G217_G343_G345_temp`
  - 0.1% (10) `Pl_Load_G217_G343_G346_load_log`
  - 0.1% (10) `Pl_Load_G217_G343_G347_production`
  - 0.1% (10) `Pl_Load_G217_G343_G347_production_G348`
  - 0.1% (10) `Pl_Load_G217_G343_G349_production`
  - 0.1% (10) `Pl_Load_G217_G343_ref_npi_data`
  - 0.1% (10) `PL_MSTR_G128_G129_G124_RPT_MTH`
  - 0.1% (10) `Pl_G350_Load_G351_Derived_db_86_G245_G352`
  - 0.1% (10) `Pl_G350_Load_G351_G268_G353`
  - 0.1% (10) `PL_Mstr_G343_Raw_Stage_Incremental_Load_Pipeline`
  - 0.1% (10) `Pl_File_Based_Regular_Load_RAW_G89_output_claims_ip_all`
  - 0.1% (10) `Pl_Load_G217_G224_G354_G355_and_rr_G356`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_RR_2868_G357_DC_G358`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_G359`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_G360_for_G361_G362`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_SH_G180_Care_G363_New`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_G364_G365`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_834_G194_records received_on`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_CM_G366_G148_REPORT`
  - 0.1% (10) `PL_CHLD_G133_G138_FL_G123_RAW_DAILY_G367_Report_G148_G368`
  - 0.1% (10) `Pl_Load_RAW_G304_auth_360`
  - 0.1% (10) `Pl_Load_RAW_G304_auth_G369`
  - 0.1% (10) `Pl_Load_RAW_G304_claim_360`
  - 0.1% (10) `Pl_Load_RAW_G304_claims_G369`
  - 0.1% (10) `Pl_Load_RAW_G304_G243_G369`
  - 0.1% (10) `Pl_Load_G217_G304_auth_360`
  - 0.1% (10) `Pl_Load_G217_G304_auth_G369`
  - 0.1% (10) `Pl_Load_G217_G304_claim_360`
  - 0.1% (10) `Pl_Load_G217_G304_claims_G369`
  - 0.1% (10) `Pl_Load_G217_G304_G243_G369`
  - 0.1% (10) `PL_Load_Raw_G343_CLAIM_SERVICE_CATEGORY_OP`
  - 0.1% (10) `PL_Load_Raw_G343_G370`
  - 0.1% (10) `PL_Load_Raw_G343_IP_CATEGORY`
  - 0.1% (10) `PL_Load_Raw_G343_IP_G371_G372_BY_G373`
  - 0.1% (10) `PL_Load_Raw_G343_G374`
  - 0.1% (10) `PL_Load_Raw_G343_G374_G375_ADDED`
  - 0.1% (10) `PL_Load_Raw_G343_OP_CATEGORY`
  - 0.1% (10) `PL_Load_Raw_G343_PROC_CODE_G376_CT`
  - 0.1% (10) `PL_Load_Raw_G343_G377_CATEGORY`
  - 0.1% (10) `PL_Load_Raw_G343_REV`
  - 0.1% (10) `PL_Load_Raw_G343_PROC_RATE_G378_G379`
  - 0.1% (10) `PL_Load_Raw_G343_DIAG_G380_X_G271`
  - 0.1% (10) `PL_Load_Raw_G343_G324_TYPES_CODE_TABLE`
  - 0.1% (10) `PL_Load_Raw_G343_G381_G373_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G381_DX_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G381_G266_G384_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G381_G385_G386_G382_CD_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G387_G377_G383`
  - 0.1% (10) `PL_Load_Raw_G343_G388_CODE_G383`
  - 0.1% (10) `PL_Load_Raw_G343_SERVICE_TYPE_CODE`
  - 0.1% (10) `PL_Load_Raw_G343_G382_G389_CD`
  - 0.1% (10) `PL_Load_G217_G343_CLAIM_SERVICE_CATEGORY_OP`
  - 0.1% (10) `PL_Load_G217_G343_G370`
  - 0.1% (10) `PL_Load_G217_G343_IP_CATEGORY`
  - 0.1% (10) `PL_Load_G217_G343_IP_G371_G372_BY_G373`
  - 0.1% (10) `PL_Load_G217_G343_G374`
  - 0.1% (10) `PL_Load_G217_G343_G374_G375_ADDED`
  - 0.1% (10) `PL_Load_G217_G343_OP_CATEGORY`
  - 0.1% (10) `PL_Load_G217_G343_PROC_CODE_G376_CT`
  - 0.1% (10) `PL_Load_G217_G343_G377_CATEGORY`
  - 0.1% (10) `PL_Load_G217_G343_REV`
  - 0.1% (10) `PL_Load_G217_G343_DIAG_G380_X_G271`
  - 0.1% (10) `PL_Load_G217_G343_G324_TYPES_CODE_TABLE`
  - 0.1% (10) `PL_Load_G217_G343_G381_G373_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G381_DX_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G381_G266_G384_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G381_G385_G386_G382_CD_G383`
  - 0.1% (10) `PL_Load_G217_G343_G387_G377_G383`
  - 0.1% (10) `PL_Load_G217_G343_G388_CODE_G383`
  - 0.1% (10) `PL_Load_G217_G343_SERVICE_TYPE_CODE`
  - 0.1% (10) `PL_Load_G217_G343_G382_G389_CD`
  - 0.1% (10) `PL_CHLD_G133_DE_G123_TO_RAW`
  - 0.1% (10) `PL_MSTR_FILE_RAW_TO_G123_DLY`
  - 0.1% (10) `PL_CHLD_G133_DE_RAW_TO_G123`
  - 0.1% (10) `PL_CHLD_G390_RR_2705_Provider_count_ADLS_To_Onprem`
  - 0.1% (10) `PL_CHLD_G390_RR_2470_G391_Member_G392_ADLS_To_Onprem`
  - 0.1% (10) `PL_CHLD_G390_RR_1641_Provider_Request_ADLS_To_Onprem`
  - 0.1% (10) `PL_CHLD_G390_RR_1728_G393_ADLS_To_Onprem`
  - 0.1% (10) `G394 Load to RAW G395`
  - 0.1% (10) `G394 Load to RAW G395_tracking_G396_G397_detail`
  - 0.1% (10) `G394 Load to RAW G395_tracking_G396_G212_data_v4`
  - 0.1% (10) `G394 Load to RAW G398_code_first_G399`
  - 0.1% (10) `G394 Load to RAW G400_G398`
  - 0.1% (10) `G394 Load to RAW provider_info`
  - 0.1% (10) `G394 Load to RAW transportation`
  - 0.1% (10) `G394 Load to RAW G401_G402`
  - 0.1% (10) `G394 Load to RAW dc_claims`
  - 0.1% (10) `G394 Load to RAW dc_members`
  - 0.1% (10) `G394 Load to RAW client_G403`
  - 0.1% (10) `G394 Load to RAW diagnosis_G404`
  - 0.1% (10) `G394 Load to RAW dc_G245`
  - 0.1% (10) `G394 Load to RAW G395_tracking_G396_G405`
  - 0.1% (10) `G394 Load to Raw G406 File Incremental load`
  - 0.1% (10) `G394 Load to G217 G406 File Incremental load`
  - 0.1% (10) `G394 Load to Raw G401_result File Incremental load`
  - 0.1% (10) `G394 Load to G217 G401_result File Incremental load`
  - 0.1% (10) `G394 G407 to RAW G408`
  - 0.1% (10) `G394 G407 to RAW G401_result`
  - 0.1% (10) `Pl_File_G16_G17_1200_Monthly_Regular_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G225_G225_G231_elig_G15_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G231_G233_G15_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G234_campaign_dtl_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G234_G235_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G237_G238_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_G225_G239_G147_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G225_master_G245_To_ADLS_Incr_G409_0`
  - 0.1% (10) `Pl_File_G410_G411_membership_Regular_To_ADLS_Incr`
  - 0.1% (10) `Pl_File_G410_G411_membership_Regular_Delta_To_G217_Incr`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_NH_DLY`
  - 0.1% (10) `PL_CHLD_G110_G111_NH_G119`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_NC_DLY`
  - 0.1% (10) `PL_CHLD_G110_G111_NC_G119`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_G114_DLY`
  - 0.1% (10) `PL_CHLD_G110_G111_G114_G119`
  - 0.1% (10) `PL_MSTR_G110_G111_FILE_G110_FL_DLY`
  - 0.1% (10) `PL_MSTR_G110_G111_DATA_G412_G110_FACETS_DLY`
  - 0.1% (10) `PL_GMSTR_G133_G138_G84_DLY`
  - 0.1% (10) `Pl_MSTR_G133_G138_G84_DLY`
  - 0.1% (10) `PL_CHLD_G84_RAW_G413_CM_G414_DATA_OUTPUT`
  - 0.1% (10) `PL_CHLD_G84_STD_G413_CM_G414_DATA_OUTPUT`
  - 0.1% (10) `PL_CHLD_G84_RAW_G415_G416_G417_EXT`
  - 0.1% (10) `PL_CHLD_G84_STD_G415_G416_G417_EXT`
  - 0.1% (10) `PL_CHLD_G84_RAW_G415_G416_G418_LOAD`
  - 0.1% (10) `PL_CHLD_G84_STD_G415_G416_G418_LOAD`
  - 0.1% (10) `PL_CHLD_G84_RAW_G413_RISK_G419_DATA_OUTPUT`
  - 0.1% (10) `PL_CHLD_G84_STD_G413_RISK_G419_DATA_OUTPUT`
  - 0.1% (10) `PL_GMSTR_CLM_G420_ALL_DLY`
  - 0.1% (10) `PL_Mstr_CLM_G420_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.1% (10) `PL_File_RAW_CLM_G420_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_CLM_G420_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STD_CLM_G420_Delta_To_STD_Incr`
  - 0.1% (10) `G421_NC_G131_G132`
  - 0.1% (10) `G421_Sub_LOB_G132`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_RAW_Sub_LOB_G132_G422`
  - 0.1% (10) `G212_SOURCE_RECORD_COUNT_G423`
  - 0.1% (10) `G212_SOURCE_RECORD_COUNT_G423_V2`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S3`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S4`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S5`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S6`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S7`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S8`
  - 0.1% (10) `PL_G84_ONPREM_G343_To_ADLS_Incr_S9`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S3`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S4`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S5`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S6`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S7`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S8`
  - 0.1% (10) `PL_G84_ONPREM_G343_Delta_To_G6_Incr_S9`
  - 0.1% (10) `PL_STG_STD_G60_Time_G424`
  - 0.1% (10) `PL_File_RAW_Load_G425_G426`
  - 0.1% (10) `Pl_CHLD_REPORTING_Update`
  - 0.1% (10) `Pl_CHLD_G427_CLAIMS_G428`
  - 0.1% (10) `Pl_CHLD_Check_G429`
  - 0.1% (10) `Pl_G430_To_Adls_Incr_01`
  - 0.1% (10) `Pl_G430_To_Adls_Full_01`
  - 0.1% (10) `Pl_G430_To_Adls_Incr_07`
  - 0.1% (10) `Pl_G430_To_Adls_Full_03`
  - 0.1% (10) `PL_GMSTR_G84_DIGITAL_RAW_STandard_INGESTION_G431_PIPELINE`
  - 0.1% (10) `PL_MSTR_G84_DIGITAL_RAW_STAGE_INGESTION_ G431_PIPELINE`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_G432`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_Line`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_Line_G432`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Claim_Line_Modifier`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G92`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G92_G433`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G434_G433`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_Pattern`
  - 0.1% (10) `Pl_G84_G431_G84_To_ADLS_G431_G433_processing_history`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_Line`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_Line_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Claim_Line_Modifier`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G92`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G92_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G434_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_Pattern`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Stage_G431_G433_processing_history`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_Line`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_Line_G432`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Claim_Line_Modifier`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G92`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G92_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G434_G433`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_Pattern`
  - 0.1% (10) `Pl_G84_G431_ADLS_To_Delta_G113_G431_G433_processing_history`
  - 0.1% (10) `Pl_Gmstr_G435_G436_Plan_Regular_File_Load`
  - 0.1% (10) `PL_Mstr_G435_G436_Raw_Standard_File_Load_Pipeline`
  - 0.1% (10) `PL_File_RAW_G435_G436_G437_RISK_G438`
  - 0.1% (10) `PL_File_STAGE_G435_G436_G437_RISK_G438`
  - 0.1% (10) `PL_File_STANDARD_G435_G436_G437_RISK_G438`
  - 0.1% (10) `PL_File_RAW_G435_G436_RPT_G437`
  - 0.1% (10) `PL_File_STAGE_G435_G436_RPT_G437`
  - 0.1% (10) `PL_File_STANDARD_G435_G436_RPT_G437`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G439_To_ADLS_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G442_To_ADLS_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G443_To_ADLS_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G439_DELTA_DELTA_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G442_DELTA_DELTA_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_G440_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_G440_G441_S2`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_G440_G441_S3`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_CUSTOM_LOAD_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_HISTORY_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_RESPONSE_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_CACHE_S1`
  - 0.1% (10) `PL_G84_G74_G443_DELTA_DELTA_Incr_REPORT_CACHE_S2`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STAGE_NC_G131_G132`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STAGE_Sub_LOB_G132`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STAGE_Sub_LOB_G132_G422`
  - 0.1% (10) `PL_MSTR_CLM_G444_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G123_TO_G445_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_CLM_G446_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_CLM_G420_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_FACETS_MEMBERS_G447_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_RPT_G448_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G219_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_STD_Sub_LOB_G132_G422`
  - 0.1% (10) `PL_CHLD_G130_PROCESSING_G449_Sub_LOB_G132_G422`
  - 0.1% (10) `Pl_CHLD_G130_PROCESSING_G427_CLAIM_G450_G428`
  - 0.1% (10) `PL_GMSTR_G451_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G451_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_G84_G451_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_GMSTR_G452_P2_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_MSTR_G452_P2_G84_RAW_To_STG_TO_STD_DLY`
  - 0.1% (10) `PL_G84_G452_P2_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_G84_G452_P2_GROUP_1_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_G84_G452_P2_GROUP_1_Delta_To_G6_Incr`
  - 0.1% (10) `PL_MSTR_G445_CLM_G12_MTH_STD`
  - 0.1% (10) `PL_MSTR_G453_ONPREM_STG_G454`
  - 0.1% (10) `PL_FILE_G453_ONPREM_RAW_G454`
  - 0.1% (10) `PL_FILE_G453_RAW_STG_G454`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G457_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G457_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G457_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G103_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G103_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G103_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G458_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G458_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G458_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_G459_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_G459_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_G459_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_2600_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_2600_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_2600_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G135_G455_G456_1200_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G135_G455_G456_1200_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G135_G455_G456_1200_Delta_To_STD_Incr`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G27_VW`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G27_VW`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G27_VW`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PS_KM_JC_G28`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PS_KM_JC_G28`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PS_KM_JC_G28`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G29_REQ_DATA`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_DATA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_DATA`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G29_REQ_G30`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_G30`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_G30`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_LOCATION_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_LOCATION_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_LOCATION_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_NAMES`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_NAMES`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_NAMES`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PER_G31_G32`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G32`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PER_G31_G32`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G33_DATA`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G33_DATA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G33_DATA`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_POSITION_DATA`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_POSITION_DATA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_POSITION_DATA`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_VALID_G34_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_VALID_G34_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_VALID_G34_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G35_CD_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G35_CD_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G35_CD_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G36_REASON_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G36_REASON_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G36_REASON_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G37_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G37_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G37_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G38_G39`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G38_G39`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G38_G39`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_EMAIL_G40`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_EMAIL_G40`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_EMAIL_G40`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G41`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G41`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G41`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_JOB`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_JOB`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_JOB`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G42_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G42_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G42_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G43_TBL`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G43_TBL`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G43_TBL`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G44_REVIEW`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G44_REVIEW`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G44_REVIEW`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_AUDIT_JOB`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_AUDIT_JOB`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_AUDIT_JOB`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PERSON`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PERSON`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PERSON`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G45_DATA_G46`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G45_DATA_G46`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G45_DATA_G46`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G40`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G40`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G40`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PER_G31_G47`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PER_G31_G47`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PER_G31_G47`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G29_REQ_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G29_REQ_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G29_REQ_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G48_REVIEW`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G48_REVIEW`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G48_REVIEW`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G49`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G49`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G49`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G50`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G50`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G50`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_G33_PHONE`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_G33_PHONE`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_G33_PHONE`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_G51_G52`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_G51_G52`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_G51_G52`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G53_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G53_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G53_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G54_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G54_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G54_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G55_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G55_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G55_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_KM_SF_G56_HIST`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_KM_SF_G56_HIST`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_KM_SF_G56_HIST`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS_PS_G57_G58_G59`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA_PS_G57_G58_G59`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6_PS_G57_G58_G59`
  - 0.1% (10) `PL_G76_MEMBER_MERGE_STG`
  - 0.1% (10) `PL_GMSTR_Risk_G461_G462_G463_STG_INGESTION`
  - 0.1% (10) `PL_Mstr_Risk_G461_G462_RAW_STG_INGESTION`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_2_To_ADLS_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_3_To_ADLS_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_4_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_1_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_2_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_3_ADLS_To_Delta_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_4_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_1_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_2_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_3_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_4_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_5_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_5_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_5_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_Risk_G461_G462_GROUP_6_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_Risk_G461_G462_GROUP_6_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_Risk_G461_G462_GROUP_6_Delta_To_STD_Incr`
  - 0.1% (10) `PL_GMSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.1% (10) `PL_MSTR_G1_G84_RAW_TO_STG_STD_DLY`
  - 0.1% (10) `PL_G84_G1_G460_To_ADLS`
  - 0.1% (10) `PL_G84_G1_ADLS_TO_DELTA`
  - 0.1% (10) `PL_G84_G1_DELTA_TO_G6`
  - 0.1% (10) `PL_GMSTR_DLK_G1_EDH_STD_G464_ALL_DLY`
  - 0.1% (10) `PL_MSTR_DLK_G1_EDH_STD_G464_ALL_DLY`
  - 0.1% (10) `PL_G465_DLK_G1_EDH_STD_G464_ALL_DLY`
  - 0.1% (10) `PL_MSTR_G133_G466_G454`
  - 0.1% (10) `PL_CHLD_G133_G466_G454`
  - 0.1% (10) `Pl_Gmstr_G467_Regular_File_Load`
  - 0.1% (10) `PL_Mstr_G467_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_1_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_1_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_1_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_2_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_2_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_2_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_3_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_3_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_3_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_4_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_4_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_4_Delta_To_STD_Incr`
  - 0.1% (10) `PL_File_RAW_G467_GROUP_5_To_ADLS_Incr`
  - 0.1% (10) `PL_File_STAGE_G467_GROUP_5_ADLS_To_Delta_Incr`
  - 0.1% (10) `Pl_File_STD_G467_GROUP_5_Delta_To_STD_Incr`
  - 0.1% (10) `Pl_Gmstr_G3_G4_G5_Inbound_Regular_File_Load`
  - 0.1% (10) `PL_Mstr_G3_G4_G5_Inbound_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.1% (10) `PL_File_RAW_G3_G4_G5_Inbound`
  - 0.1% (10) `PL_File_STAGE_G3_G4_G5_Inbound`
  - 0.1% (10) `PL_File_STANDARD_G3_G4_G5_Inbound`
  - 0.1% (10) `PL_GMSTR_DLK_G1_EDH_BSL_ALL_MTH`
  - 0.1% (10) `PL_MSTR_DLK_G1_G1_BSL_ALL_G468`
  - 0.1% (10) `PL_G465_DLK_G1_G1_BSL_ALL_G468`
  - 0.1% (10) `PL_MSTR_G133_G134_DLY`
  - 0.1% (10) `PL_MSTR_G133_G134_FILE_EXT_TO_RAW_DLY`
  - 0.1% (10) `PL_MSTR_G133_G469_MBR_G134_DLY`
  - 0.1% (10) `PL_GMSTR_G470_G454`
  - 0.1% (10) `PL_MSTR_G470_G454_RAW_TO_STD`
  - 0.1% (10) `PL_File_RAW_G470_To_ADLS_G454`
  - 0.1% (10) `PL_File_STAGE_G470_ADLS_To_Delta_G454`
  - 0.1% (10) `PL_File_STD_G470_Delta_To_STD_G454`
  - 0.1% (10) `PL_G410_G273_Member_Stage_File_Based_Regular_Load`
  - 0.1% (10) `PL_GMSTR_G120_G463_STG_INGESTION`
  - 0.1% (10) `PL_MSTR_G120_FILE_RAW_STD_Load`
  - 0.1% (10) `PL_GMSTR_DLK_G471_STD_CLM_ALL_DLY`
  - 0.1% (10) `PL_MSTR_DLK_G471_STD_CLM_ALL_DLY`
  - 0.1% (10) `PL_G465_DLK_G471_STD_CLM_ALL_DLY`
  - 0.1% (8) `PL_MSTR_G472_G473_ADLS_To_Delta_Incr`
  - 0.1% (8) `WF_CHLD_G137_STD_G102_G126_G222`
  - 0.0% (6) `Pl_File_G16_{table}_TPL_ADLS_To_Delta_Incr`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G300`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G300_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G474_G475_DIR_OBJ_MAP`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G474_G475_DIR_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G474_OBJ_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G476`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G477_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G478`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G478_G479_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_G481`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_FORM_G482`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_G483_G484_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_HIST`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_IN_G485_STG`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G480_G486_MAP`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G487_G488`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G487_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_CO_G489_G490`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G481_G488_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G481_G491_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_DOC`
  - 0.0% (6) `PL_CHLD_G84_STAGE_DOC_G492_G493_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_DOC_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G494_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G495_DTL`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G495_G496`
  - 0.0% (6) `PL_CHLD_G84_STAGE_FORM_G497_GRP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_FORM_G482_TYP_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G498_SRC_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_LANG_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_LOB_G477_MAP`
  - 0.0% (6) `PL_CHLD_G84_STAGE_LOB_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486_ROLE`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486_ROLE_REF`
  - 0.0% (6) `PL_CHLD_G84_STAGE_G486_TYP_REF`
  - 0.0% (4) `PL_GMSTR_G135_G400_Auth_G499_DLY`
  - 0.0% (4) `PL_Mstr_G135_G499_Raw_Stg_Std_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0100`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0100`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0100`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0500`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0500`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0500`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0530`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0530`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0530`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0540`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0540`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0540`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_2400`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_2400`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_2400`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_7100`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_7100`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_7100`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_7200`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_7200`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_7200`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_0192`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_0192`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_0192`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_1200`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_1200`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_1200`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_2600`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_2600`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_2600`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_6400`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_6400`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_6400`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_7700`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_7700`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_7700`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_8213`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_8213`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_8213`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G502`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G502`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G502`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G503`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G503`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G503`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G504`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G504`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G504`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G505`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G505`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G505`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G506`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G506`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G506`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G507`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G507`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G507`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G508`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G508`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G508`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_5400`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_5400`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_5400`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_0900`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_0900`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_0900`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_2100`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_2100`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_2100`
  - 0.0% (4) `PL_File_RAW_G135_G499_KY_G500_AUTH_G509`
  - 0.0% (4) `PL_File_STAGE_G135_G499_KY_G500_AUTH_G509`
  - 0.0% (4) `PL_File_STD_G135_G499_KY_G500_AUTH_G509`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G103`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G103`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G103`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G510`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G510`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G510`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_G457`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_G457`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_G457`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_0550`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_0550`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_0550`
  - 0.0% (4) `PL_File_RAW_G135_G499_PA_G500_AUTH_G25`
  - 0.0% (4) `PL_File_STAGE_G135_G499_PA_G500_AUTH_G25`
  - 0.0% (4) `PL_File_STD_G135_G499_PA_G500_AUTH_G25`
  - 0.0% (4) `PL_File_RAW_G135_G499_G501_G500_AUTH_5420`
  - 0.0% (4) `PL_File_STAGE_G135_G499_G501_G500_AUTH_5420`
  - 0.0% (4) `PL_File_STD_G135_G499_G501_G500_AUTH_5420`
  - 0.0% (4) `PL_GMSTR_G135_G400_Auth_G499_Hist`
  - 0.0% (4) `PL_Mstr_G135_G499_Raw_Stg_Std_Hist_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_G135_0100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0500_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0500_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0500_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0530_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0530_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0530_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0540_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0540_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0540_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_2400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_2400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_2400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_7100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_7100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_7100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_7200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_7200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_7200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0192_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0192_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0192_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_1200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_1200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_1200_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_2600_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_2600_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_2600_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_6400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_6400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_6400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_7700_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_7700_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_7700_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_8213_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_8213_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_8213_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G502_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G502_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G502_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G503_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G503_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G503_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G504_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G504_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G504_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G505_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G505_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G505_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G506_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G506_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G506_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G507_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G507_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G507_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G508_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G508_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G508_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_5400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_5400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_5400_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0900_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0900_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0900_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_2100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_2100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_2100_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_0550_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_0550_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_0550_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_RAW_G135_G25_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STAGE_G135_G25_G499_G511_G242_Hist`
  - 0.0% (4) `PL_File_STD_G135_G25_G499_G511_G242_Hist`
  - 0.0% (4) `WF_Mstr_G512_STG_STD_INGESTION`
  - 0.0% (4) `WF_CHLD_FILE_STG_G512`
  - 0.0% (4) `WF_CHLD_FILE_STD_G512`
  - 0.0% (4) `PL_GMSTR_G1_G66_FILE_RAW_TO_STG_STD_DLY`
  - 0.0% (4) `PL_MSTR_G1_G66_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G66_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G66_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G66_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G65_RAW_STG_INGESTION`
  - 0.0% (4) `PL_GMSTR_G1_G65_FILE_RAW_TO_STG_STD_MTH`
  - 0.0% (4) `PL_GMSTR_G1_G67_FILE_RAW_TO_STG_STD_G85`
  - 0.0% (4) `PL_MSTR_G1_G67_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G67_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G67_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G67_Delta_To_STD_Incr`
  - 0.0% (4) `PL_GMSTR_G1_G68_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G68_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G68_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G68_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G68_Delta_To_STD_Incr`
  - 0.0% (4) `PL_File_RAW_G1_G2_G78`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G78`
  - 0.0% (4) `PL_File_STD_G1_{source}_G78`
  - 0.0% (4) `PL_File_RAW_G1_G2_G79`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G79`
  - 0.0% (4) `PL_File_STD_G1_{source}_G79`
  - 0.0% (4) `PL_File_RAW_G1_G2_G80`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G80`
  - 0.0% (4) `PL_File_STD_G1_{source}_G80`
  - 0.0% (4) `PL_GMSTR_G1_{source}_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_{source}_RAW_STG_INGESTION`
  - 0.0% (4) `PL_File_RAW_G1_G2_G81`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G81`
  - 0.0% (4) `PL_File_STD_G1_{source}_G81`
  - 0.0% (4) `PL_File_RAW_G1_G2_G82`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G82`
  - 0.0% (4) `PL_FILE_STD_G1_{source}_G82`
  - 0.0% (4) `PL_File_RAW_G1_G2_G83`
  - 0.0% (4) `PL_File_STAGE_G1_G2_G83`
  - 0.0% (4) `PL_File_STD_G1_{source}_G83`
  - 0.0% (4) `PL_MSTR_G1_G69_RAW_STG_INGESTION`
  - 0.0% (4) `PL_GMSTR_G1_G69_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G1_G69_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Case_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Case_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_Case_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_G70_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_G70_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G1_G69_G70_Delta_To_STD_Incr`
  - 0.0% (4) `PL_GMSTR_G135_G242_MONTHLY_FILE_INGESTION`
  - 0.0% (4) `PL_Mstr_G135_G242_G136_RAW_STD_INGESTION`
  - 0.0% (4) `PL_GMSTR_G135_G242_G136_HIST_FILE_INGESTION`
  - 0.0% (4) `PL_Mstr_G135_G242_G136_HIST_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G513_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G513_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G513_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G513_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G514_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G514_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G514_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G514_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G515_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G515_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G515_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G516_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G517_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G517_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G517_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G517_RAW_STD_INGESTION`
  - 0.0% (4) `PL_GMSTR_{source}_G15_HIST_DLY`
  - 0.0% (4) `PL_MSTR_{source}_G15_HIST_DLY`
  - 0.0% (4) `PL_File_RAW_G14_G15_To_ADLS_G13`
  - 0.0% (4) `PL_File_STAGE_{source}_G15_ADLS_To_Delta_G13`
  - 0.0% (4) `PL_File_STD_{source}_G15_Delta_To_STD_G13`
  - 0.0% (4) `Pl_Gmstr_G518_Regular_File_Load`
  - 0.0% (4) `PL_Mstr_G518_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_G518_G202_G519_G203_1_3_G204 Risk_List_extract`
  - 0.0% (4) `PL_File_RAW_G518_G520_G521_J_01_CM_Interaction_G522_Rpt_G523_extract`
  - 0.0% (4) `PL_GMSTR_G472_G473_DLY_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G472_G473_RAW_STG_INGESTION`
  - 0.0% (4) `PL_MSTR_G472_G473_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_Delta_To_STD_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_G524_To_ADLS_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_G524_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_MSTR_G472_G473_G524_Delta_To_STD_Incr`
  - 0.0% (4) `PL_File_RAW_G135_G525_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G525_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G525_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G525_RAW_STD_INGESTION`
  - 0.0% (4) `PL_File_RAW_G135_G499_To_ADLS_Incr`
  - 0.0% (4) `PL_File_STAGE_G135_G499_ADLS_To_Delta_Incr`
  - 0.0% (4) `PL_File_STD_G135_G499_Delta_To_STD_Incr`
  - 0.0% (4) `PL_Mstr_G135_G242_G499_RAW_STD_INGESTION`
  - 0.0% (4) `PL_GMSTR_WC_CD_FILE_G454`
  - 0.0% (4) `PL_Mstr_WC_CD_G90_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7700_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_7700_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7700_G527_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_1200_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_1200_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_1200_G527_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7100_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_7100_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7100_G527_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_2100_G527_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_2100_G527_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_2100_G527_G90`
  - 0.0% (4) `PL_GMSTR_WC_INB_G528_FILE_G463`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_2400_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_2400_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_2100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_2100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7100_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7200_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7200_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_7700_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_7700_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G149_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G149_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G149_DSNP_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G149_DSNP_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G103_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G103_WC_INB_G528`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_1200_WC_INB_G528`
  - 0.0% (4) `PL_FILE_STD_G526_WC_1200_WC_INB_G528`
  - 0.0% (4) `PL_GMSTR_G90_FILE_WC_Response_DLY`
  - 0.0% (4) `PL_Mstr_WC_G529_G90_Raw_Stage_Regular_File_Load_Pipeline_DLY`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G530_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G530_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G530_Response_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G531_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G531_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G531_Response_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G532_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G532_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G532_Response_G90`
  - 0.0% (4) `PL_FILE_RAW_G526_WC_G533_Response_G90`
  - 0.0% (4) `PL_FILE_STAGE_G526_WC_G533_Response_G90`
  - 0.0% (4) `PL_FILE_STD_G526_WC_G533_Response_G90`
  - 0.0% (4) `PL_GMSTR_WC_G8_FILE_G463`
  - 0.0% (4) `PL_Mstr_WC_G8_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `PL_File_RAW_WC_G8_2100`
  - 0.0% (4) `PL_File_STAGE_WC_G8_2100`
  - 0.0% (4) `PL_File_STD_WC_G8_2100`
  - 0.0% (4) `PL_File_RAW_WC_G8_2400`
  - 0.0% (4) `PL_File_STAGE_WC_G8_2400`
  - 0.0% (4) `PL_File_STD_WC_G8_2400`
  - 0.0% (4) `PL_File_RAW_WC_G8_7100`
  - 0.0% (4) `PL_File_STAGE_WC_G8_7100`
  - 0.0% (4) `PL_File_STD_WC_G8_7100`
  - 0.0% (4) `PL_File_RAW_WC_G8_7200`
  - 0.0% (4) `PL_File_STAGE_WC_G8_7200`
  - 0.0% (4) `PL_File_STD_WC_G8_7200`
  - 0.0% (4) `PL_File_RAW_WC_G8_7700`
  - 0.0% (4) `PL_File_STAGE_WC_G8_7700`
  - 0.0% (4) `PL_File_STD_WC_G8_7700`
  - 0.0% (4) `PL_File_RAW_WC_G8_G149`
  - 0.0% (4) `PL_File_STAGE_WC_G8_G149`
  - 0.0% (4) `PL_File_STD_WC_G8_G149`
  - 0.0% (4) `PL_File_RAW_WC_G8_G149_DSNP`
  - 0.0% (4) `PL_File_STAGE_WC_G8_G149_DSNP`
  - 0.0% (4) `PL_File_STD_WC_G8_G149_DSNP`
  - 0.0% (4) `PL_File_RAW_WC_G8_G103`
  - 0.0% (4) `PL_File_STAGE_WC_G8_G103`
  - 0.0% (4) `PL_File_STD_WC_G8_G103`
  - 0.0% (4) `PL_File_RAW_WC_G8_1200`
  - 0.0% (4) `PL_File_STAGE_WC_G8_1200`
  - 0.0% (4) `PL_File_STD_WC_G8_1200`
  - 0.0% (4) `PL_Mstr_WC_G528_Raw_Stage_Regular_File_Load_Pipeline`
  - 0.0% (4) `WF_Mstr_G534_STG_STD_INGESTION`
  - 0.0% (4) `WF_CHLD_FILE_STG_G534`
  - 0.0% (4) `WF_CHLD_FILE_STD_G534`
  - 0.0% (2) `PL_File_G8_G9_G10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G8_G9_G10_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G8_G11_G10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G8_G11_G10_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G8_SD_IND_RISK_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G8_SD_IND_RISK_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_G8_ALL_MTH`
  - 0.0% (2) `PL_MSTR_G8_ALL_MTH`
  - 0.0% (2) `PL_G535_FILE_RAW_STAGE_INGESTION`
  - 0.0% (2) `PL_GMSTR_G536_CM_G103_DLY`
  - 0.0% (2) `PL_MSTR_G536_CM_G103_DLY`
  - 0.0% (2) `PL_File_G536_CM_G103_DNC_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Outreach_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Billing_RPT_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_G537_DTL_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Reports_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_DNC_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Outreach_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Billing_RPT_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_G537_DTL_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G536_CM_G103_Reports_Delta_To_STD_Incr`
  - 0.0% (2) `Pl_File_G16_{table}_Regular_ADLS_To_Delta_Incr`
  - 0.0% (2) `WF_MSTR_FILE_RAW_STD_MI_TPL_ALL_DLY`
  - 0.0% (2) `WF_CHLD_FILE_STG_MI_TPL`
  - 0.0% (2) `WF_CHLD_FILE_STD_MI_TPL`
  - 0.0% (2) `PL_MSTR_G133_MBR_G145_G538`
  - 0.0% (2) `PL_MSTR_G133_MBR_G145_G538_FILE_EXT_TO_RAW`
  - 0.0% (2) `PL_CHLD_G133_MBR_G145_G538_RAW_TO_G123`
  - 0.0% (2) `PL_GMSTR_G16_820_ALL_DLY`
  - 0.0% (2) `PL_Mstr_G16_820_Raw_Std_Ingestion_Pipeline_Incr`
  - 0.0% (2) `PL_File_G16_820_G103_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G509_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G508_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G506_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G503_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G505_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G16_820_G103_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G509_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G508_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G506_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G503_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G16_820_G505_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_G539_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_G539_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_G134_7200_G539_G85`
  - 0.0% (2) `PL_MSTR_MBR_G134_7200_G539_G85`
  - 0.0% (2) `PL_File_MBR_G134_7200_FACETS_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_FACETS_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_G134_7200_FACETS_G85`
  - 0.0% (2) `PL_MSTR_MBR_G134_7200_FACETS_G85`
  - 0.0% (2) `PL_File_MBR_G134_7200_G540_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_MBR_G134_7200_G540_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_G134_7200_G540_G85`
  - 0.0% (2) `PL_MSTR_MBR_G134_7200_G540_G85`
  - 0.0% (2) `pl_G541_G542_stg_load`
  - 0.0% (2) `PL_File_G297_7200_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G297_7200_Delta_To_STD_Incr`
  - 0.0% (2) `PL_File_G297_7200_24_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_G297_7200_24_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_G297_7200_DLY`
  - 0.0% (2) `PL_MSTR_G297_7200_DLY`
  - 0.0% (2) `PL_UM_G460_G452_SRC_TO_RAW`
  - 0.0% (2) `PI_Mstr_G460_G452_Source_to_Stage`
  - 0.0% (2) `PL_GMSTR_G452_G84_RAW_To_STG_TO_STD_DLY`
  - 0.0% (2) `PL_MSTR_G452_G84_RAW_To_STG_TO_STD_DLY`
  - 0.0% (2) `PL_G84_G452_GROUP_1_To_ADLS_Incr`
  - 0.0% (2) `PL_G84_G452_GROUP_1_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_G452_GROUP_1_Delta_To_G6_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_1_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_2_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_3_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_4_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_5_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_6_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_7_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_8_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_9_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_G117_GROUP_10_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_G84_Risk_G461_GROUP_2_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STAGE_Risk_G461_Medicaid_GROUP_1_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STAGE_Risk_G461_Medicaid_GROUP_2_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_STAGE_Risk_G461_Medicaid_GROUP_3_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_SFMC_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_SFMC_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_{subdomain}_ALL_DLY`
  - 0.0% (2) `PL_MSTR_MBR_{subdomain}_ALL_DLY`
  - 0.0% (2) `PL_GMSTR_CLM_G12_G13_ALL_G98`
  - 0.0% (2) `PL_MSTR_CLM_G12_G13_RAW_TO_STD`
  - 0.0% (2) `PL_File_CLM_G12_G13_ADLS_To_Delta_Incr`
  - 0.0% (2) `PL_File_CLM_G12_G13_Delta_To_STD_Incr`
  - 0.0% (2) `PL_GMSTR_MBR_TPL_ALL_G85`
  - 0.0% (2) `WF_MSTR_FILE_RAW_STD_CAQH_ALL_DLY`
  - 0.0% (2) `WF_CHLD_FILE_STG_CAQH`
  - 0.0% (2) `WF_CHLD_FILE_STD_CAQH`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_MBR`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_CLM`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_G206`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_G222`
  - 0.0% (2) `WF_G137_MSTR_STD_G543_RX`
  - 0.0% (2) `WF_CHLD_G137_STD_G102_G126_RX`

### EMAIL_TEMPLATE_CONFIG.TEMPLATE_NAME

- values:
  - 26.1% (696) `G544 G545`
  - 13.8% (368) `G135_G499`
  - 11.5% (308) `G135_G499_Hist`
  - 8.3% (222) `G546 Management`
  - 4.5% (120) `G526_G8`
  - 3.0% (80) `G1_G2`
  - 2.8% (76) `G526_INB_G528`
  - 2.2% (58) `G137 STD TO EDH Load`
  - 2.1% (56) `G526_G527`
  - 2.1% (56) `G526_Response`
  - 1.6% (44) `G1_G69`
  - 1.5% (40) `G135_G242_G136`
  - 1.3% (36) `HEALTH_AT_HOME`
  - 1.2% (32) `G462_G118`
  - 1.0% (28) `G16 820`
  - 1.0% (28) `Risk_G461`
  - 0.9% (24) `G536 Health`
  - 0.7% (20) `G1_G66`
  - 0.7% (20) `G1_G65`
  - 0.7% (20) `G1_G67`
  - 0.7% (20) `G1_G68`
  - 0.7% (20) `G14 LA history`
  - 0.7% (18) `G242_G118`
  - 0.6% (16) `G103 G8`
  - 0.6% (16) `G513`
  - 0.6% (16) `G514`
  - 0.6% (16) `G516`
  - 0.6% (16) `G517`
  - 0.6% (16) `G518`
  - 0.6% (16) `G525`
  - 0.6% (16) `G499`
  - 0.5% (14) `G452`
  - 0.4% (12) `G512`
  - 0.4% (12) `PA G547 7200 G297`
  - 0.4% (12) `G534`
  - 0.4% (10) `G548_G118`
  - 0.3% (8) `G549_G118`
  - 0.3% (8) `G16_G17`
  - 0.3% (8) `PA G547 7200 G539`
  - 0.3% (8) `PA G547 7200 FACETS`
  - 0.3% (8) `PA G547 7200 G540`
  - 0.3% (8) `EMCIPS SFMC`
  - 0.3% (8) `Common Claims Medical`
  - 0.3% (8) `CAQH TPL`
  - 0.2% (6) `MI STATE TPL`
  - 0.2% (6) `G145_G550_Campaign_Automation`
  - 0.2% (6) `G551_G118`
  - 0.1% (4) `G552_G118`
  - 0.1% (2) `G553_G118`
  - 0.1% (2) `G554`
- patterns:
  - 26.1% (696) `G544 G545`
  - 13.8% (368) `G135_G499`
  - 11.5% (308) `G135_G499_Hist`
  - 8.3% (222) `G546 Management`
  - 4.5% (120) `G526_G8`
  - 2.8% (76) `G526_INB_G528`
  - 2.2% (58) `G137 STD TO EDH Load`
  - 2.1% (56) `G526_G527`
  - 2.1% (56) `G526_Response`
  - 1.8% (48) `G1_G2`
  - 1.6% (44) `G1_G69`
  - 1.5% (40) `G135_G242_G136`
  - 1.3% (36) `HEALTH_AT_HOME`
  - 1.2% (32) `G462_G118`
  - 1.2% (32) `G1_{source}`
  - 1.0% (28) `G16 820`
  - 1.0% (28) `Risk_G461`
  - 0.9% (24) `G536 Health`
  - 0.7% (20) `G1_G66`
  - 0.7% (20) `G1_G65`
  - 0.7% (20) `G1_G67`
  - 0.7% (20) `G1_G68`
  - 0.7% (18) `G242_G118`
  - 0.6% (16) `G103 G8`
  - 0.6% (16) `G513`
  - 0.6% (16) `G514`
  - 0.6% (16) `G516`
  - 0.6% (16) `G517`
  - 0.6% (16) `{source} LA history`
  - 0.6% (16) `G518`
  - 0.6% (16) `G525`
  - 0.6% (16) `G499`
  - 0.5% (14) `G452`
  - 0.4% (12) `G512`
  - 0.4% (12) `PA G547 7200 G297`
  - 0.4% (12) `G534`
  - 0.4% (10) `G548_G118`
  - 0.3% (8) `G549_G118`
  - 0.3% (8) `{domain}`
  - 0.3% (8) `PA G547 7200 G539`
  - 0.3% (8) `PA G547 7200 FACETS`
  - 0.3% (8) `PA G547 7200 G540`
  - 0.3% (8) `EMCIPS SFMC`
  - 0.3% (8) `Common {domain} {subdomain}`
  - 0.3% (8) `CAQH TPL`
  - 0.2% (6) `MI STATE TPL`
  - 0.2% (6) `G145_G550_Campaign_Automation`
  - 0.2% (6) `G551_G118`
  - 0.1% (4) `G14 LA history`
  - 0.1% (4) `G552_G118`
  - 0.1% (2) `G553_G118`
  - 0.1% (2) `G554`

### EMAIL_TEMPLATE_CONFIG.PROCESS_NAME

- values:
  - 26.1% (696) `G544 G545`
  - 13.8% (368) `G135_G499`
  - 11.5% (308) `G135_G499_Hist`
  - 8.3% (222) `G546 Management`
  - 4.5% (120) `G526_G8`
  - 3.0% (80) `G1_G2`
  - 2.8% (76) `G526_INB_G528`
  - 2.1% (56) `G526_G527`
  - 2.1% (56) `G526_Response`
  - 1.6% (44) `G1_G69`
  - 1.5% (40) `G135_G242_G136`
  - 1.3% (36) `HEALTH_AT_HOME`
  - 1.2% (32) `G462_G118`
  - 1.0% (28) `G16 820`
  - 1.0% (28) `Risk_G461`
  - 0.9% (24) `G536 Health`
  - 0.7% (20) `G1_G66`
  - 0.7% (20) `G1_G65`
  - 0.7% (20) `G1_G67`
  - 0.7% (20) `G1_G68`
  - 0.7% (20) `G14 LA history`
  - 0.7% (18) `G242_G118`
  - 0.6% (16) `G103 G8`
  - 0.6% (16) `G513`
  - 0.6% (16) `G514`
  - 0.6% (16) `G516`
  - 0.6% (16) `G517`
  - 0.6% (16) `G518`
  - 0.6% (16) `G525`
  - 0.6% (16) `G499`
  - 0.6% (16) `G137_CLAIMS`
  - 0.5% (14) `G452`
  - 0.5% (14) `G137_MEMBER`
  - 0.5% (14) `G137_PROVIDER`
  - 0.4% (12) `G512`
  - 0.4% (12) `G297 7200`
  - 0.4% (12) `G534`
  - 0.4% (10) `G548_G118`
  - 0.4% (10) `G137_G222`
  - 0.3% (8) `G549_G118`
  - 0.3% (8) `G16_G17`
  - 0.3% (8) `Member Enrollment 7200 G539`
  - 0.3% (8) `Member Enrollment 7200 FACETS`
  - 0.3% (8) `Member Enrollment 7200 G540`
  - 0.3% (8) `EMCIPS SFMC`
  - 0.3% (8) `Common Claims Medical`
  - 0.3% (8) `CAQH TPL`
  - 0.2% (6) `MI STATE TPL`
  - 0.2% (6) `G145_G550_Campaign_Automation`
  - 0.2% (6) `G551_G118`
  - 0.1% (4) `G137_PHARMACY`
  - 0.1% (4) `G552_G118`
  - 0.1% (2) `G553`
  - 0.1% (2) `G554`
- patterns:
  - 26.1% (696) `G544 G545`
  - 13.8% (368) `G135_G499`
  - 11.5% (308) `G135_G499_Hist`
  - 8.3% (222) `G546 Management`
  - 4.5% (120) `G526_G8`
  - 2.8% (76) `G526_INB_G528`
  - 2.1% (56) `G526_G527`
  - 2.1% (56) `G526_Response`
  - 1.8% (48) `G1_G2`
  - 1.6% (44) `G1_G69`
  - 1.5% (40) `G135_G242_G136`
  - 1.3% (36) `HEALTH_AT_HOME`
  - 1.2% (32) `G462_G118`
  - 1.2% (32) `G1_{source}`
  - 1.0% (28) `G16 820`
  - 1.0% (28) `Risk_G461`
  - 0.9% (24) `G536 Health`
  - 0.7% (20) `G1_G66`
  - 0.7% (20) `G1_G65`
  - 0.7% (20) `G1_G67`
  - 0.7% (20) `G1_G68`
  - 0.7% (18) `G242_G118`
  - 0.6% (16) `G103 G8`
  - 0.6% (16) `G513`
  - 0.6% (16) `G514`
  - 0.6% (16) `G516`
  - 0.6% (16) `G517`
  - 0.6% (16) `{source} LA history`
  - 0.6% (16) `G518`
  - 0.6% (16) `G525`
  - 0.6% (16) `G499`
  - 0.6% (16) `G137_CLAIMS`
  - 0.5% (14) `G452`
  - 0.5% (14) `G137_MEMBER`
  - 0.5% (14) `G137_PROVIDER`
  - 0.4% (12) `G512`
  - 0.4% (12) `G297 7200`
  - 0.4% (12) `G534`
  - 0.4% (10) `G548_G118`
  - 0.4% (10) `G137_G222`
  - 0.3% (8) `G549_G118`
  - 0.3% (8) `{domain}`
  - 0.3% (8) `Member Enrollment 7200 G539`
  - 0.3% (8) `Member Enrollment 7200 FACETS`
  - 0.3% (8) `Member Enrollment 7200 G540`
  - 0.3% (8) `EMCIPS SFMC`
  - 0.3% (8) `Common {domain} {subdomain}`
  - 0.3% (8) `CAQH TPL`
  - 0.2% (6) `MI STATE TPL`
  - 0.2% (6) `G145_G550_Campaign_Automation`
  - 0.2% (6) `G551_G118`
  - 0.1% (4) `G14 LA history`
  - 0.1% (4) `G137_PHARMACY`
  - 0.1% (4) `G552_G118`
  - 0.1% (2) `G553`
  - 0.1% (2) `G554`

### EMAIL_TEMPLATE_CONFIG.STATUS

- values:
  - 23.1% (615) `Success`
  - 23.1% (615) `Failed`
  - 16.6% (444) `FilesNotReceived`
  - 14.7% (392) `New Files to Process`
  - 2.2% (58) `FilesNotReceivedACPA`
  - 2.2% (58) `FilesNotReceivedACLA`
  - 2.2% (58) `FilesNotReceivedACDC`
  - 2.2% (58) `FilesNotReceivedSHSC`
  - 2.2% (58) `FilesNotReceivedBCCMI`
  - 2.2% (58) `FilesNotReceivedACOH`
  - 2.2% (58) `FilesNotReceivedACDE`
  - 2.2% (58) `FilesNotReceivedACNH`
  - 2.2% (58) `FilesNotReceivedEnterprise`
  - 1.4% (37) `NoStandardEntriesPresentinIIGTables`
  - 1.4% (37) `DuplicateFileReceived`
  - 0.2% (6) `Files Not Received`
- patterns:
  - 23.1% (615) `Success`
  - 23.1% (615) `Failed`
  - 16.6% (444) `FilesNotReceived`
  - 14.7% (392) `New Files to Process`
  - 2.2% (58) `FilesNotReceivedACPA`
  - 2.2% (58) `FilesNotReceivedACLA`
  - 2.2% (58) `FilesNotReceivedACDC`
  - 2.2% (58) `FilesNotReceivedSHSC`
  - 2.2% (58) `FilesNotReceivedBCCMI`
  - 2.2% (58) `FilesNotReceivedACOH`
  - 2.2% (58) `FilesNotReceivedACDE`
  - 2.2% (58) `FilesNotReceivedACNH`
  - 2.2% (58) `FilesNotReceivedEnterprise`
  - 1.4% (37) `NoStandardEntriesPresentinIIGTables`
  - 1.4% (37) `DuplicateFileReceived`
  - 0.2% (6) `Files Not Received`

### EMAIL_TEMPLATE_CONFIG.ACTIVE_FLAG

- values:
  - 100.0% (2668) `Y`
- patterns:
  - 100.0% (2668) `Y`

### EMAIL_TEMPLATE_CONFIG.SUBJECT

- values:
  - 3.4% (92) `G135 G499 G555 Daily File Not Received -`
  - 3.4% (92) `G135 G499 G555 Daily File Received -`
  - 3.4% (92) `G135 G499 G555 Daily Load Completed -`
  - 3.4% (92) `G135 G499 G555 Daily Load  Failed -`
  - 2.9% (77) `G135 G499 G555 History File Not Received -`
  - 2.9% (77) `G135 G499 G555 History File Received -`
  - 2.9% (77) `G135 G499 G555 History Load Completed -`
  - 2.9% (77) `G135 G499 G555 History Load  Failed -`
  - 2.2% (58) `G149 CM Automation - File Not received`
  - 2.2% (58) `G15 CM Automation - File Not received`
  - 2.2% (58) `G556 CM Automation - File Not received`
  - 2.2% (58) `G139 CM Automation - File Not received`
  - 2.2% (58) `G557 CM Automation - File Not received`
  - 2.2% (58) `G163 CM Automation - File Not received`
  - 2.2% (58) `G179 CM Automation - File Not received`
  - 2.2% (58) `G558 CM Automation - File Not received`
  - 2.2% (58) `G92 CM Automation - File Not received`
  - 2.2% (58) `G544 G545 Load Completed`
  - 2.2% (58) `G544 G545 Load Failed`
  - 2.2% (58) `CM Automation File Not Received`
  - 1.4% (37) `No G559 For Standard`
  - 1.4% (37) `G546 Management File Not Received`
  - 1.4% (37) `G546 Management File Received`
  - 1.4% (37) `G546 Management Load Completed`
  - 1.4% (37) `G546 Management Load Failed`
  - 1.4% (37) `G546 Management Duplicate File Received`
  - 1.2% (32) `G462_G118_STATUS`
  - 1.1% (30) `WC_G8 File Not Received`
  - 1.1% (30) `WC_G8 File Received`
  - 1.1% (30) `WC_G8   Load Completed`
  - 1.1% (30) `WC_G8   Load  Failed`
  - 0.7% (20) `G1 – G2 File Not Received`
  - 0.7% (20) `G1 – G2 File Received`
  - 0.7% (20) `G1 – G2 Data load to DL Completed`
  - 0.7% (20) `G1 – G2 Data load to DL Failed`
  - 0.7% (19) `WC_G560_G528 File Not Received`
  - 0.7% (19) `WC_G560_G528 File Received`
  - 0.7% (19) `WC_G560_G528   Load Completed`
  - 0.7% (19) `WC_G560_G528  Load  Failed`
  - 0.7% (18) `G242_G118_STATUS`
  - 0.5% (14) `G16 820 Load Completed`
  - 0.5% (14) `G16 820 Load Failed`
  - 0.5% (14) `WC_G527 File Not Received`
  - 0.5% (14) `WC_G527 File Received`
  - 0.5% (14) `WC_G527   Load Completed`
  - 0.5% (14) `WC_G527  Load  Failed`
  - 0.5% (14) `WC_Response File Not Received`
  - 0.5% (14) `WC_Response File Received`
  - 0.5% (14) `WC_Response Load Completed`
  - 0.5% (14) `WC_Response Load  Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Completed`
  - 0.4% (12) `G536 Health Load Completed`
  - 0.4% (12) `G536 Health Load Failed`
  - 0.4% (11) `G1 – G69 Data load to DL Completed`
  - 0.4% (11) `G1 – G69 Data load to DL Failed`
  - 0.4% (11) `G1 – G69 File Not Received`
  - 0.4% (11) `G1 – G69 File Received`
  - 0.4% (10) `G135 G242 G136 Hist File Not Received`
  - 0.4% (10) `G135 G242 G136 Hist File Received`
  - 0.4% (10) `G135 G242 G136 Hist Load Completed`
  - 0.4% (10) `G135 G242 G136 Hist Load Failed`
  - 0.4% (10) `G548_G118_STATUS`
  - 0.3% (9) `G548 File Not Received`
  - 0.3% (9) `G548 File Received`
  - 0.3% (9) `G548   Load Completed`
  - 0.3% (9) `G548   Load  Failed`
  - 0.3% (8) `G549_G118_STATUS`
  - 0.3% (8) `G103 G8 Load Completed`
  - 0.3% (8) `G103 G8 Load Failed`
  - 0.3% (8) `G16_G17 Raw To Stage Master Pipeline Status`
  - 0.3% (8) `G137 CLM G126 LOAD COMPLETED`
  - 0.3% (8) `G137 CLM G126 LOAD FAILED`
  - 0.3% (7) `G452 ONPREM to STANDARD process Failed`
  - 0.3% (7) `G452 ONPREM to STANDARD process Completed`
  - 0.3% (7) `G137 MBR G126 LOAD COMPLETED`
  - 0.3% (7) `G137 MBR G126 LOAD FAILED`
  - 0.3% (7) `G137 G206 G126 LOAD COMPLETED`
  - 0.3% (7) `G137 G206 G126 LOAD FAILED`
  - 0.2% (6) `G297 7200 Load Completed`
  - 0.2% (6) `G297 7200 Load Failed`
  - 0.2% (6) `G551_G118_STATUS`
  - 0.2% (5) `G1 – G66 Data load to DL Completed`
  - 0.2% (5) `G1 – G66 Data load to DL Failed`
  - 0.2% (5) `G1 – G66 File Not Received`
  - 0.2% (5) `G1 – G66 File Received`
  - 0.2% (5) `G1 – G65 Data load to DL Completed`
  - 0.2% (5) `G1 – G65 Data load to DL Failed`
  - 0.2% (5) `G1 – G65 File Not Received`
  - 0.2% (5) `G1 – G65 File Received`
  - 0.2% (5) `G1 – G67 File Received`
  - 0.2% (5) `G1 – G67 Data load to DL Completed`
  - 0.2% (5) `G1 – G67 Data load to DL Failed`
  - 0.2% (5) `G1 – G67 File Not Received`
  - 0.2% (5) `G1 – G68 Data load to DL Completed`
  - 0.2% (5) `G1 – G68 Data load to DL Failed`
  - 0.2% (5) `G1 – G68 File Not Received`
  - 0.2% (5) `G1 – G68 File Received`
  - 0.2% (5) `G14 LA history Load Failed`
  - 0.2% (5) `G14 LA history Files Not Received`
  - 0.2% (5) `G14 LA history Files Received`
  - 0.2% (5) `G14 LA history Load Completed`
  - 0.2% (5) `G137 G222 G126 LOAD COMPLETED`
  - 0.2% (5) `G137 G222 G126 LOAD FAILED`
  - 0.1% (4) `G135 G242 G513 File Not Received`
  - 0.1% (4) `G135 G242 G513 File Received`
  - 0.1% (4) `G135 G242 G513 Load Completed`
  - 0.1% (4) `G135 G242 G513 Load Failed`
  - 0.1% (4) `G135 G242 G514 File Not Received`
  - 0.1% (4) `G135 G242 G514 File Received`
  - 0.1% (4) `G135 G242 G514 Load Completed`
  - 0.1% (4) `G135 G242 G514 Load Failed`
  - 0.1% (4) `G135 G242 G516 File Not Received`
  - 0.1% (4) `G135 G242 G516 File Received`
  - 0.1% (4) `G135 G242 G516 Load Completed`
  - 0.1% (4) `G135 G242 G516 Load Failed`
  - 0.1% (4) `G135 G242 G517 File Not Received`
  - 0.1% (4) `Member Enrollment 7200 G539 Load Completed`
  - 0.1% (4) `Member Enrollment 7200 G539 Load Failed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Load Completed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Load Failed`
  - 0.1% (4) `Member Enrollment 7200 G540 Load Completed`
  - 0.1% (4) `Member Enrollment 7200 G540 Load Failed`
  - 0.1% (4) `G518 File Not Received`
  - 0.1% (4) `G518 File Received`
  - 0.1% (4) `G518 Load Completed`
  - 0.1% (4) `G518 Load Failed`
  - 0.1% (4) `G135 G242 G517 File Received`
  - 0.1% (4) `G135 G242 G517 Load Completed`
  - 0.1% (4) `G135 G242 G517 Load Failed`
  - 0.1% (4) `G135 G242 G525 File Not Received`
  - 0.1% (4) `G135 G242 G525 File Received`
  - 0.1% (4) `G135 G242 G525 Load Completed`
  - 0.1% (4) `G135 G242 G525 Load Failed`
  - 0.1% (4) `G135 G242 G499 File Not Received`
  - 0.1% (4) `G135 G242 G499 File Received`
  - 0.1% (4) `G135 G242 G499 Load Completed`
  - 0.1% (4) `G135 G242 G499 Load Failed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Load Completed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Load Failed`
  - 0.1% (4) `Common Claims Medical History Load Completed`
  - 0.1% (4) `Common Claims Medical History Load Failed`
  - 0.1% (4) `CAQH Load Completed`
  - 0.1% (4) `CAQH Load Failed`
  - 0.1% (4) `G552_G118_STATUS`
  - 0.1% (3) `MI STATE TPL Load Completed`
  - 0.1% (3) `MI STATE TPL Load Failed`
  - 0.1% (3) `G512 File Not Received`
  - 0.1% (3) `G512 File Received`
  - 0.1% (3) `G512 Load Completed`
  - 0.1% (3) `G512 Load Failed`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Completed`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Failed`
  - 0.1% (3) `Transportation Claims G534 File Not Received`
  - 0.1% (3) `Transportation Claims G534 File Received`
  - 0.1% (3) `Transportation Claims G534 Load Completed`
  - 0.1% (3) `Transportation Claims G534 Load Failed`
  - 0.1% (2) `G553_G118_STATUS`
  - 0.1% (2) `G137 RX G126 LOAD COMPLETED`
  - 0.1% (2) `G137 RX G126 LOAD FAILED`
  - 0.0% (1) `G554_OUTPUT_G561 Pipeline G562 G563`
  - 0.0% (1) `G554_OUTPUT_G561 Pipeline G562 Failed`
- patterns:
  - 3.4% (92) `G135 G499 G555 Daily File Not Received -`
  - 3.4% (92) `G135 G499 G555 Daily File Received -`
  - 3.4% (92) `G135 G499 G555 Daily Load Completed -`
  - 3.4% (92) `G135 G499 G555 Daily Load  Failed -`
  - 2.9% (77) `G135 G499 G555 History File Not Received -`
  - 2.9% (77) `G135 G499 G555 History File Received -`
  - 2.9% (77) `G135 G499 G555 History Load Completed -`
  - 2.9% (77) `G135 G499 G555 History Load  Failed -`
  - 2.2% (58) `G149 CM Automation - File Not received`
  - 2.2% (58) `G15 CM Automation - File Not received`
  - 2.2% (58) `G556 CM Automation - File Not received`
  - 2.2% (58) `G139 CM Automation - File Not received`
  - 2.2% (58) `G557 CM Automation - File Not received`
  - 2.2% (58) `G163 CM Automation - File Not received`
  - 2.2% (58) `G179 CM Automation - File Not received`
  - 2.2% (58) `G558 CM Automation - File Not received`
  - 2.2% (58) `G92 CM Automation - File Not received`
  - 2.2% (58) `G544 G545 Load Completed`
  - 2.2% (58) `G544 G545 Load Failed`
  - 2.2% (58) `CM Automation File Not Received`
  - 1.4% (37) `No G559 For Standard`
  - 1.4% (37) `G546 Management File Not Received`
  - 1.4% (37) `G546 Management File Received`
  - 1.4% (37) `G546 Management Load Completed`
  - 1.4% (37) `G546 Management Load Failed`
  - 1.4% (37) `G546 Management Duplicate File Received`
  - 1.2% (32) `G462_G118_STATUS`
  - 1.1% (30) `WC_G8 File Not Received`
  - 1.1% (30) `WC_G8 File Received`
  - 1.1% (30) `WC_G8   Load Completed`
  - 1.1% (30) `WC_G8   Load  Failed`
  - 0.7% (19) `WC_G560_G528 File Not Received`
  - 0.7% (19) `WC_G560_G528 File Received`
  - 0.7% (19) `WC_G560_G528   Load Completed`
  - 0.7% (19) `WC_G560_G528  Load  Failed`
  - 0.7% (18) `G242_G118_STATUS`
  - 0.5% (14) `G16 820 Load Completed`
  - 0.5% (14) `G16 820 Load Failed`
  - 0.5% (14) `WC_G527 File Not Received`
  - 0.5% (14) `WC_G527 File Received`
  - 0.5% (14) `WC_G527   Load Completed`
  - 0.5% (14) `WC_G527  Load  Failed`
  - 0.5% (14) `WC_Response File Not Received`
  - 0.5% (14) `WC_Response File Received`
  - 0.5% (14) `WC_Response Load Completed`
  - 0.5% (14) `WC_Response Load  Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Completed`
  - 0.4% (12) `G536 Health Load Completed`
  - 0.4% (12) `G536 Health Load Failed`
  - 0.4% (12) `G1 – G2 File Not Received`
  - 0.4% (12) `G1 – G2 File Received`
  - 0.4% (12) `G1 – G2 Data load to DL Completed`
  - 0.4% (12) `G1 – G2 Data load to DL Failed`
  - 0.4% (11) `G1 – G69 Data load to DL Completed`
  - 0.4% (11) `G1 – G69 Data load to DL Failed`
  - 0.4% (11) `G1 – G69 File Not Received`
  - 0.4% (11) `G1 – G69 File Received`
  - 0.4% (10) `G135 G242 G136 Hist File Not Received`
  - 0.4% (10) `G135 G242 G136 Hist File Received`
  - 0.4% (10) `G135 G242 G136 Hist Load Completed`
  - 0.4% (10) `G135 G242 G136 Hist Load Failed`
  - 0.4% (10) `G548_G118_STATUS`
  - 0.3% (9) `G548 File Not Received`
  - 0.3% (9) `G548 File Received`
  - 0.3% (9) `G548   Load Completed`
  - 0.3% (9) `G548   Load  Failed`
  - 0.3% (8) `G549_G118_STATUS`
  - 0.3% (8) `G103 G8 Load Completed`
  - 0.3% (8) `G103 G8 Load Failed`
  - 0.3% (8) `{domain} Raw To Stage Master Pipeline Status`
  - 0.3% (8) `G1 – {source} File Not Received`
  - 0.3% (8) `G1 – {source} File Received`
  - 0.3% (8) `G1 – {source} Data load to DL Completed`
  - 0.3% (8) `G1 – {source} Data load to DL Failed`
  - 0.3% (8) `G137 CLM G126 LOAD COMPLETED`
  - 0.3% (8) `G137 CLM G126 LOAD FAILED`
  - 0.3% (7) `G452 ONPREM to STANDARD process Failed`
  - 0.3% (7) `G452 ONPREM to STANDARD process Completed`
  - 0.3% (7) `G137 MBR G126 LOAD COMPLETED`
  - 0.3% (7) `G137 MBR G126 LOAD FAILED`
  - 0.3% (7) `G137 G206 G126 LOAD COMPLETED`
  - 0.3% (7) `G137 G206 G126 LOAD FAILED`
  - 0.2% (6) `G297 7200 Load Completed`
  - 0.2% (6) `G297 7200 Load Failed`
  - 0.2% (6) `G551_G118_STATUS`
  - 0.2% (5) `G1 – G66 Data load to DL Completed`
  - 0.2% (5) `G1 – G66 Data load to DL Failed`
  - 0.2% (5) `G1 – G66 File Not Received`
  - 0.2% (5) `G1 – G66 File Received`
  - 0.2% (5) `G1 – G65 Data load to DL Completed`
  - 0.2% (5) `G1 – G65 Data load to DL Failed`
  - 0.2% (5) `G1 – G65 File Not Received`
  - 0.2% (5) `G1 – G65 File Received`
  - 0.2% (5) `G1 – G67 File Received`
  - 0.2% (5) `G1 – G67 Data load to DL Completed`
  - 0.2% (5) `G1 – G67 Data load to DL Failed`
  - 0.2% (5) `G1 – G67 File Not Received`
  - 0.2% (5) `G1 – G68 Data load to DL Completed`
  - 0.2% (5) `G1 – G68 Data load to DL Failed`
  - 0.2% (5) `G1 – G68 File Not Received`
  - 0.2% (5) `G1 – G68 File Received`
  - 0.2% (5) `G137 G222 G126 LOAD COMPLETED`
  - 0.2% (5) `G137 G222 G126 LOAD FAILED`
  - 0.1% (4) `G135 G242 G513 File Not Received`
  - 0.1% (4) `G135 G242 G513 File Received`
  - 0.1% (4) `G135 G242 G513 Load Completed`
  - 0.1% (4) `G135 G242 G513 Load Failed`
  - 0.1% (4) `G135 G242 G514 File Not Received`
  - 0.1% (4) `G135 G242 G514 File Received`
  - 0.1% (4) `G135 G242 G514 Load Completed`
  - 0.1% (4) `G135 G242 G514 Load Failed`
  - 0.1% (4) `G135 G242 G516 File Not Received`
  - 0.1% (4) `G135 G242 G516 File Received`
  - 0.1% (4) `G135 G242 G516 Load Completed`
  - 0.1% (4) `G135 G242 G516 Load Failed`
  - 0.1% (4) `G135 G242 G517 File Not Received`
  - 0.1% (4) `Member Enrollment 7200 G539 Load Completed`
  - 0.1% (4) `Member Enrollment 7200 G539 Load Failed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Load Completed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Load Failed`
  - 0.1% (4) `Member Enrollment 7200 G540 Load Completed`
  - 0.1% (4) `Member Enrollment 7200 G540 Load Failed`
  - 0.1% (4) `{source} LA history Load Failed`
  - 0.1% (4) `G518 File Not Received`
  - 0.1% (4) `G518 File Received`
  - 0.1% (4) `G518 Load Completed`
  - 0.1% (4) `G518 Load Failed`
  - 0.1% (4) `G135 G242 G517 File Received`
  - 0.1% (4) `G135 G242 G517 Load Completed`
  - 0.1% (4) `G135 G242 G517 Load Failed`
  - 0.1% (4) `G135 G242 G525 File Not Received`
  - 0.1% (4) `G135 G242 G525 File Received`
  - 0.1% (4) `G135 G242 G525 Load Completed`
  - 0.1% (4) `G135 G242 G525 Load Failed`
  - 0.1% (4) `G135 G242 G499 File Not Received`
  - 0.1% (4) `G135 G242 G499 File Received`
  - 0.1% (4) `G135 G242 G499 Load Completed`
  - 0.1% (4) `G135 G242 G499 Load Failed`
  - 0.1% (4) `{source} LA history Files Not Received`
  - 0.1% (4) `{source} LA history Files Received`
  - 0.1% (4) `{source} LA history Load Completed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Load Completed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Load Failed`
  - 0.1% (4) `Common {domain} {subdomain} History Load Completed`
  - 0.1% (4) `Common {domain} {subdomain} History Load Failed`
  - 0.1% (4) `CAQH Load Completed`
  - 0.1% (4) `CAQH Load Failed`
  - 0.1% (4) `G552_G118_STATUS`
  - 0.1% (3) `MI STATE TPL Load Completed`
  - 0.1% (3) `MI STATE TPL Load Failed`
  - 0.1% (3) `G512 File Not Received`
  - 0.1% (3) `G512 File Received`
  - 0.1% (3) `G512 Load Completed`
  - 0.1% (3) `G512 Load Failed`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Completed`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Failed`
  - 0.1% (3) `Transportation Claims G534 File Not Received`
  - 0.1% (3) `Transportation Claims G534 File Received`
  - 0.1% (3) `Transportation Claims G534 Load Completed`
  - 0.1% (3) `Transportation Claims G534 Load Failed`
  - 0.1% (2) `G553_G118_STATUS`
  - 0.1% (2) `G137 RX G126 LOAD COMPLETED`
  - 0.1% (2) `G137 RX G126 LOAD FAILED`
  - 0.0% (1) `G14 LA history Load Failed`
  - 0.0% (1) `G554_OUTPUT_G561 Pipeline G562 G563`
  - 0.0% (1) `G554_OUTPUT_G561 Pipeline G562 Failed`
  - 0.0% (1) `G14 LA history Files Not Received`
  - 0.0% (1) `G14 LA history Files Received`
  - 0.0% (1) `G14 LA history Load Completed`

### EMAIL_TEMPLATE_CONFIG.BODY

- values:
  - 21.7% (580) `The G564 files have not been received for the CM Automation. G565 review and take the necessary G566.`
  - 3.4% (92) `G135 G499 G555 Daily File Not Received`
  - 3.4% (92) `Received The G564 Files for G135 G499 G555 Daily`
  - 3.4% (92) `G135 G499 G555 Daily Data Load Successful`
  - 3.4% (92) `G135 G499 G555 Daily Data Load Failed`
  - 2.9% (77) `G135 G499 G555 History File Not Received`
  - 2.9% (77) `Received The G564 Files for G135 G499 G555 History`
  - 2.9% (77) `G135 G499 G555 History Data Load Successful`
  - 2.9% (77) `G135 G499 G555 History Data Load Failed`
  - 2.2% (58) `G544 G545 Load Process Completed`
  - 2.2% (58) `G544 G545 Load Process Failed`
  - 1.4% (37) `G546 Management No G559 For Standard`
  - 1.4% (37) `G546 Management File Not Received`
  - 1.4% (37) `Received The G564 Files from G546 Management`
  - 1.4% (37) `G546 Management Load Process Completed`
  - 1.4% (37) `G546 Management Load Process Failed`
  - 1.4% (37) `G546 Management Duplicate File Received`
  - 1.2% (32) `G462 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 1.1% (30) `WC_G8 File Not Received`
  - 1.1% (30) `Received The G564 Files for WC_G8`
  - 1.1% (30) `WC_G8 Data Load Successful`
  - 1.1% (30) `WC_G8 Data Load Failed`
  - 0.7% (20) `G1 G2 File Not Received`
  - 0.7% (20) `Received The G564 Files for G1 G2`
  - 0.7% (20) `G1 G2 Load Completed`
  - 0.7% (20) `G1 G2 Load Failed`
  - 0.7% (19) `WC_G560_G528  File Not Received`
  - 0.7% (19) `Received The G564 Files for WC_G560_G528`
  - 0.7% (19) `WC_G560_G528 Data Load Successful`
  - 0.7% (19) `WC_G560_G528 Data Load Failed`
  - 0.5% (14) `G16 820 Files Load Process Completed`
  - 0.5% (14) `G16 820 Files Load Process Failed`
  - 0.5% (14) `WC_G527  File Not Received`
  - 0.5% (14) `Received The G564 Files for WC_G527`
  - 0.5% (14) `WC_G527 Data Load Successful`
  - 0.5% (14) `WC_G527 Data Load Failed`
  - 0.5% (14) `WC_Response  File Not Received`
  - 0.5% (14) `Received The G564 Files for WC_Response`
  - 0.5% (14) `WC_Response Data Load Successful`
  - 0.5% (14) `WC_Response Data Load Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Completed`
  - 0.4% (12) `G536 Health Files Load Process Completed`
  - 0.4% (12) `G536 Health Files Load Process Failed`
  - 0.4% (11) `G1 G69 Load Completed`
  - 0.4% (11) `G1 G69 Load Failed`
  - 0.4% (11) `G1 G69 File Not Received`
  - 0.4% (11) `Received The G564 Files for G1 G69`
  - 0.4% (10) `G135 G242 G136 Hist File Not Received`
  - 0.4% (10) `Received The G564 G136 Historical Files for G135 G242`
  - 0.4% (10) `G135 G242 G136 Historical Data Load Successful`
  - 0.4% (10) `G135 G242 G136 Historical Data Load Failed`
  - 0.4% (10) `G548 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 0.3% (9) `G242 G118 process is complete.Please see the G568 for individual files below`
  - 0.3% (9) `G242 G118 process is Failed.Please see the G568 for individual files below`
  - 0.3% (9) `G548 File Not Received`
  - 0.3% (9) `Received The G564 Files for G548`
  - 0.3% (9) `G548 Data Load Successful`
  - 0.3% (9) `G548 Data Load Failed`
  - 0.3% (8) `G549 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 0.3% (8) `G103 G8 Files Load Process Completed`
  - 0.3% (8) `G103 G8 Files Load Process Failed`
  - 0.3% (8) `G137 CLAIMS LOAD COMPLETED`
  - 0.3% (8) `G137 CLAIMS LOAD FAILED`
  - 0.3% (7) `G452 ONPREM to STANDARD process Failed`
  - 0.3% (7) `G452 ONPREM to STANDARD process Completed`
  - 0.3% (7) `G137 MEMBER LOAD COMPLETED`
  - 0.3% (7) `G137 MEMBER LOAD FAILED`
  - 0.3% (7) `G137 PROVIDER LOAD COMPLETED`
  - 0.3% (7) `G137 PROVIDER LOAD FAILED`
  - 0.2% (6) `G297 7200 Files Load Process Completed`
  - 0.2% (6) `G297 7200 Files Load Process Failed`
  - 0.2% (5) `G1 G66 Load Completed`
  - 0.2% (5) `G1 G66 Load Failed`
  - 0.2% (5) `G1 G66 File Not Received`
  - 0.2% (5) `Received The G564 Files for G1 G66`
  - 0.2% (5) `G1 G65 Load Completed`
  - 0.2% (5) `G1 G65 Load Failed`
  - 0.2% (5) `G1 G65 File Not Received`
  - 0.2% (5) `Received The G564 Files for G1 G65`
  - 0.2% (5) `Received The G564 Files for G1 G67`
  - 0.2% (5) `G1 G67 Load Completed`
  - 0.2% (5) `G1 G67 Load Failed`
  - 0.2% (5) `G1 G67 File Not Received`
  - 0.2% (5) `G1 G68 Load Completed`
  - 0.2% (5) `G1 G68 Load Failed`
  - 0.2% (5) `G1 G68 File Not Received`
  - 0.2% (5) `Received The G564 Files for G1 G68`
  - 0.2% (5) `G14 LA history Files Load Process Failed`
  - 0.2% (5) `G14 LA history Files Not Received`
  - 0.2% (5) `Received the G564 files for G14 LA history`
  - 0.2% (5) `G14 LA history Files Load Process Completed`
  - 0.2% (5) `G137 G222 LOAD COMPLETED`
  - 0.2% (5) `G137 G222 LOAD FAILED`
  - 0.1% (4) `G16_G17 Data Load Successful`
  - 0.1% (4) `G16_G17 Data Load Failed`
  - 0.1% (4) `G135 G242 G513 File Not Received`
  - 0.1% (4) `Received The G564 G513 Files for G135 G242`
  - 0.1% (4) `G135 G242 G513 Data Load Successful`
  - 0.1% (4) `G135 G242 G513 Data Load Failed`
  - 0.1% (4) `G135 G242 G514 File Not Received`
  - 0.1% (4) `Received The G564 G514 Files for G135 G242`
  - 0.1% (4) `G135 G242 G514 Data Load Successful`
  - 0.1% (4) `G135 G242 G514 Data Load Failed`
  - 0.1% (4) `G135 G242 G516 File Not Received`
  - 0.1% (4) `Received The G564 G516 Files for G135 G242`
  - 0.1% (4) `G135 G242 G516 Data Load Successful`
  - 0.1% (4) `G135 G242 G516 Data Load Failed`
  - 0.1% (4) `G135 G242 G517 File Not Received`
  - 0.1% (4) `Member Enrollment 7200 G539 Files Load Process Completed`
  - 0.1% (4) `Member Enrollment 7200 G539 Files Load Process Failed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Files Load Process Completed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Files Load Process Failed`
  - 0.1% (4) `Member Enrollment 7200 G540 Files Load Process Completed`
  - 0.1% (4) `Member Enrollment 7200 G540 Files Load Process Failed`
  - 0.1% (4) `G518 File Not Received`
  - 0.1% (4) `Received The G564 Files from G518`
  - 0.1% (4) `G518 Load Process Completed`
  - 0.1% (4) `G518 Load Process Failed`
  - 0.1% (4) `Received The G564 G517 Files for G135 G242`
  - 0.1% (4) `G135 G242 G517 Data Load Successful`
  - 0.1% (4) `G135 G242 G517 Data Load Failed`
  - 0.1% (4) `G135 G242 G525 File Not Received`
  - 0.1% (4) `Received The G564 G525 Files for G135 G242`
  - 0.1% (4) `G135 G242 G525 Data Load Successful`
  - 0.1% (4) `G135 G242 G525 Data Load Failed`
  - 0.1% (4) `G135 G242 G499 File Not Received`
  - 0.1% (4) `Received The G564 G499 Files for G135 G242`
  - 0.1% (4) `G135 G242 G499 Data Load Successful`
  - 0.1% (4) `G135 G242 G499 Data Load Failed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Files Load Process Completed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Files Load Process Failed`
  - 0.1% (4) `Common Claims Medical History Files Load Process Completed`
  - 0.1% (4) `Common Claims Medical History Files Load Process Failed`
  - 0.1% (4) `CAQH Files Load Process Completed`
  - 0.1% (4) `CAQH  Files Load Process Failed`
  - 0.1% (4) `G552_G118 process is complete.Please see the G568 for individual files below`
  - 0.1% (3) `MI STATE TPL Files Load Process Completed`
  - 0.1% (3) `MI STATE TPL Files Load Process Failed`
  - 0.1% (3) `G512 File Not Received`
  - 0.1% (3) `Received The G564 G512 Files`
  - 0.1% (3) `G512 Data Load Successful`
  - 0.1% (3) `G512 Data Load Failed`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Completed. Please find the G569 as below:`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Failed. Please find the G569 as below:`
  - 0.1% (3) `G551 G118 process is failed.  Please Check the G570.`
  - 0.1% (3) `G551 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 0.1% (3) `Transportation Claims G534 File Not Received`
  - 0.1% (3) `Received The G564 Transportation Claims G534 Files`
  - 0.1% (3) `Transportation Claims G534 Data Load Successful`
  - 0.1% (3) `Transportation Claims G534 Data Load Failed`
  - 0.1% (2) `G553 G118 process is complete. Files with Success status are G567 to the G564 path location. Please see the status for individual files below.`
  - 0.1% (2) `G137 PHARMACY LOAD COMPLETED`
  - 0.1% (2) `G137 PHARMACY LOAD FAILED`
  - 0.0% (1) `G554 -Success`
  - 0.0% (1) `G554 -Failed`
- patterns:
  - 21.7% (580) `The G564 files have not been received for the CM Automation. G565 review and take the necessary G566.`
  - 3.4% (92) `G135 G499 G555 Daily File Not Received`
  - 3.4% (92) `Received The G564 Files for G135 G499 G555 Daily`
  - 3.4% (92) `G135 G499 G555 Daily Data Load Successful`
  - 3.4% (92) `G135 G499 G555 Daily Data Load Failed`
  - 2.9% (77) `G135 G499 G555 History File Not Received`
  - 2.9% (77) `Received The G564 Files for G135 G499 G555 History`
  - 2.9% (77) `G135 G499 G555 History Data Load Successful`
  - 2.9% (77) `G135 G499 G555 History Data Load Failed`
  - 2.2% (58) `G544 G545 Load Process Completed`
  - 2.2% (58) `G544 G545 Load Process Failed`
  - 1.4% (37) `G546 Management No G559 For Standard`
  - 1.4% (37) `G546 Management File Not Received`
  - 1.4% (37) `Received The G564 Files from G546 Management`
  - 1.4% (37) `G546 Management Load Process Completed`
  - 1.4% (37) `G546 Management Load Process Failed`
  - 1.4% (37) `G546 Management Duplicate File Received`
  - 1.2% (32) `G462 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 1.1% (30) `WC_G8 File Not Received`
  - 1.1% (30) `Received The G564 Files for WC_G8`
  - 1.1% (30) `WC_G8 Data Load Successful`
  - 1.1% (30) `WC_G8 Data Load Failed`
  - 0.7% (19) `WC_G560_G528  File Not Received`
  - 0.7% (19) `Received The G564 Files for WC_G560_G528`
  - 0.7% (19) `WC_G560_G528 Data Load Successful`
  - 0.7% (19) `WC_G560_G528 Data Load Failed`
  - 0.5% (14) `G16 820 Files Load Process Completed`
  - 0.5% (14) `G16 820 Files Load Process Failed`
  - 0.5% (14) `WC_G527  File Not Received`
  - 0.5% (14) `Received The G564 Files for WC_G527`
  - 0.5% (14) `WC_G527 Data Load Successful`
  - 0.5% (14) `WC_G527 Data Load Failed`
  - 0.5% (14) `WC_Response  File Not Received`
  - 0.5% (14) `Received The G564 Files for WC_Response`
  - 0.5% (14) `WC_Response Data Load Successful`
  - 0.5% (14) `WC_Response Data Load Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Failed`
  - 0.5% (14) `Risk G461 Medicare ONPREM to STANDARD process Completed`
  - 0.4% (12) `G536 Health Files Load Process Completed`
  - 0.4% (12) `G536 Health Files Load Process Failed`
  - 0.4% (12) `G1 G2 File Not Received`
  - 0.4% (12) `Received The G564 Files for G1 G2`
  - 0.4% (12) `G1 G2 Load Completed`
  - 0.4% (12) `G1 G2 Load Failed`
  - 0.4% (11) `G1 G69 Load Completed`
  - 0.4% (11) `G1 G69 Load Failed`
  - 0.4% (11) `G1 G69 File Not Received`
  - 0.4% (11) `Received The G564 Files for G1 G69`
  - 0.4% (10) `G135 G242 G136 Hist File Not Received`
  - 0.4% (10) `Received The G564 G136 Historical Files for G135 G242`
  - 0.4% (10) `G135 G242 G136 Historical Data Load Successful`
  - 0.4% (10) `G135 G242 G136 Historical Data Load Failed`
  - 0.4% (10) `G548 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 0.3% (9) `G242 G118 process is complete.Please see the G568 for individual files below`
  - 0.3% (9) `G242 G118 process is Failed.Please see the G568 for individual files below`
  - 0.3% (9) `G548 File Not Received`
  - 0.3% (9) `Received The G564 Files for G548`
  - 0.3% (9) `G548 Data Load Successful`
  - 0.3% (9) `G548 Data Load Failed`
  - 0.3% (8) `G549 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 0.3% (8) `G103 G8 Files Load Process Completed`
  - 0.3% (8) `G103 G8 Files Load Process Failed`
  - 0.3% (8) `G1 {source} File Not Received`
  - 0.3% (8) `Received The G564 Files for G1 {source}`
  - 0.3% (8) `G1 {source} Load Completed`
  - 0.3% (8) `G1 {source} Load Failed`
  - 0.3% (8) `G137 CLAIMS LOAD COMPLETED`
  - 0.3% (8) `G137 CLAIMS LOAD FAILED`
  - 0.3% (7) `G452 ONPREM to STANDARD process Failed`
  - 0.3% (7) `G452 ONPREM to STANDARD process Completed`
  - 0.3% (7) `G137 MEMBER LOAD COMPLETED`
  - 0.3% (7) `G137 MEMBER LOAD FAILED`
  - 0.3% (7) `G137 PROVIDER LOAD COMPLETED`
  - 0.3% (7) `G137 PROVIDER LOAD FAILED`
  - 0.2% (6) `G297 7200 Files Load Process Completed`
  - 0.2% (6) `G297 7200 Files Load Process Failed`
  - 0.2% (5) `G1 G66 Load Completed`
  - 0.2% (5) `G1 G66 Load Failed`
  - 0.2% (5) `G1 G66 File Not Received`
  - 0.2% (5) `Received The G564 Files for G1 G66`
  - 0.2% (5) `G1 G65 Load Completed`
  - 0.2% (5) `G1 G65 Load Failed`
  - 0.2% (5) `G1 G65 File Not Received`
  - 0.2% (5) `Received The G564 Files for G1 G65`
  - 0.2% (5) `Received The G564 Files for G1 G67`
  - 0.2% (5) `G1 G67 Load Completed`
  - 0.2% (5) `G1 G67 Load Failed`
  - 0.2% (5) `G1 G67 File Not Received`
  - 0.2% (5) `G1 G68 Load Completed`
  - 0.2% (5) `G1 G68 Load Failed`
  - 0.2% (5) `G1 G68 File Not Received`
  - 0.2% (5) `Received The G564 Files for G1 G68`
  - 0.2% (5) `G137 G222 LOAD COMPLETED`
  - 0.2% (5) `G137 G222 LOAD FAILED`
  - 0.1% (4) `{domain} Data Load Successful`
  - 0.1% (4) `{domain} Data Load Failed`
  - 0.1% (4) `G135 G242 G513 File Not Received`
  - 0.1% (4) `Received The G564 G513 Files for G135 G242`
  - 0.1% (4) `G135 G242 G513 Data Load Successful`
  - 0.1% (4) `G135 G242 G513 Data Load Failed`
  - 0.1% (4) `G135 G242 G514 File Not Received`
  - 0.1% (4) `Received The G564 G514 Files for G135 G242`
  - 0.1% (4) `G135 G242 G514 Data Load Successful`
  - 0.1% (4) `G135 G242 G514 Data Load Failed`
  - 0.1% (4) `G135 G242 G516 File Not Received`
  - 0.1% (4) `Received The G564 G516 Files for G135 G242`
  - 0.1% (4) `G135 G242 G516 Data Load Successful`
  - 0.1% (4) `G135 G242 G516 Data Load Failed`
  - 0.1% (4) `G135 G242 G517 File Not Received`
  - 0.1% (4) `Member Enrollment 7200 G539 Files Load Process Completed`
  - 0.1% (4) `Member Enrollment 7200 G539 Files Load Process Failed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Files Load Process Completed`
  - 0.1% (4) `Member Enrollment 7200 FACETS Files Load Process Failed`
  - 0.1% (4) `Member Enrollment 7200 G540 Files Load Process Completed`
  - 0.1% (4) `Member Enrollment 7200 G540 Files Load Process Failed`
  - 0.1% (4) `{source} LA history Files Load Process Failed`
  - 0.1% (4) `G518 File Not Received`
  - 0.1% (4) `Received The G564 Files from G518`
  - 0.1% (4) `G518 Load Process Completed`
  - 0.1% (4) `G518 Load Process Failed`
  - 0.1% (4) `Received The G564 G517 Files for G135 G242`
  - 0.1% (4) `G135 G242 G517 Data Load Successful`
  - 0.1% (4) `G135 G242 G517 Data Load Failed`
  - 0.1% (4) `G135 G242 G525 File Not Received`
  - 0.1% (4) `Received The G564 G525 Files for G135 G242`
  - 0.1% (4) `G135 G242 G525 Data Load Successful`
  - 0.1% (4) `G135 G242 G525 Data Load Failed`
  - 0.1% (4) `G135 G242 G499 File Not Received`
  - 0.1% (4) `Received The G564 G499 Files for G135 G242`
  - 0.1% (4) `G135 G242 G499 Data Load Successful`
  - 0.1% (4) `G135 G242 G499 Data Load Failed`
  - 0.1% (4) `{source} LA history Files Not Received`
  - 0.1% (4) `Received the G564 files for {source} LA history`
  - 0.1% (4) `{source} LA history Files Load Process Completed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Files Load Process Completed`
  - 0.1% (4) `SFMC Email Campaign Tracking Details Files Load Process Failed`
  - 0.1% (4) `Common {domain} {subdomain} History Files Load Process Completed`
  - 0.1% (4) `Common {domain} {subdomain} History Files Load Process Failed`
  - 0.1% (4) `CAQH Files Load Process Completed`
  - 0.1% (4) `CAQH  Files Load Process Failed`
  - 0.1% (4) `G552_G118 process is complete.Please see the G568 for individual files below`
  - 0.1% (3) `MI STATE TPL Files Load Process Completed`
  - 0.1% (3) `MI STATE TPL Files Load Process Failed`
  - 0.1% (3) `G512 File Not Received`
  - 0.1% (3) `Received The G564 G512 Files`
  - 0.1% (3) `G512 Data Load Successful`
  - 0.1% (3) `G512 Data Load Failed`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Completed. Please find the G569 as below:`
  - 0.1% (3) `G145 G550 Campaign Automation Data G118 Failed. Please find the G569 as below:`
  - 0.1% (3) `G551 G118 process is failed.  Please Check the G570.`
  - 0.1% (3) `G551 G118 process is complete.Files with Success status are G567 to the G564 path 'location'.Please see the G568 for individual files below`
  - 0.1% (3) `Transportation Claims G534 File Not Received`
  - 0.1% (3) `Received The G564 Transportation Claims G534 Files`
  - 0.1% (3) `Transportation Claims G534 Data Load Successful`
  - 0.1% (3) `Transportation Claims G534 Data Load Failed`
  - 0.1% (2) `G553 G118 process is complete. Files with Success status are G567 to the G564 path location. Please see the status for individual files below.`
  - 0.1% (2) `G137 PHARMACY LOAD COMPLETED`
  - 0.1% (2) `G137 PHARMACY LOAD FAILED`
  - 0.0% (1) `G14 LA history Files Load Process Failed`
  - 0.0% (1) `G554 -Success`
  - 0.0% (1) `G554 -Failed`
  - 0.0% (1) `G14 LA history Files Not Received`
  - 0.0% (1) `Received the G564 files for G14 LA history`
  - 0.0% (1) `G14 LA history Files Load Process Completed`

### EMAIL_TEMPLATE_CONFIG.SENDER_NAME

- values:
  - 97.8% (2610) `dbo`
  - 2.2% (58) `DBO`
- patterns:
  - 97.8% (2610) `dbo`
  - 2.2% (58) `DBO`

### EMAIL_TEMPLATE_CONFIG.SENDER_EMAIL

- values:
  - 97.7% (2606) `G571@<LOCAL_DENYLIST>.G572`
  - 1.6% (44) `DL-ACFC: G573 Data Lake Production Support`
  - 0.3% (8) `G571@<LOCAL_DENYLIST>.G572`
  - 0.2% (6) `G574@<LOCAL_DENYLIST>.G572`
  - 0.1% (4) `G575@<LOCAL_DENYLIST>.G572`
- patterns:
  - 97.7% (2606) `G571@<LOCAL_DENYLIST>.G572`
  - 1.6% (44) `DL-ACFC: G573 Data Lake Production Support`
  - 0.3% (8) `G571@<LOCAL_DENYLIST>.G572`
  - 0.2% (6) `G574@<LOCAL_DENYLIST>.G572`
  - 0.1% (4) `G575@<LOCAL_DENYLIST>.G572`

### EMAIL_TEMPLATE_CONFIG.EMAIL_TO

- values:
  - 47.6% (1270) `G576@<LOCAL_DENYLIST>.G572`
  - 17.4% (464) `G576@<LOCAL_DENYLIST>.G572,dl_acfc_G577@<LOCAL_DENYLIST>.G572,<EMAIL>`
  - 8.3% (222) `G571@<LOCAL_DENYLIST>.G572`
  - 5.1% (136) `dl_G578@<LOCAL_DENYLIST>.G572,G576@<LOCAL_DENYLIST>.G572`
  - 4.3% (116) `G579@<LOCAL_DENYLIST>.G572,G580@<LOCAL_DENYLIST>.G572`
  - 3.0% (80) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;G583@<LOCAL_DENYLIST>.G572;G584@<LOCAL_DENYLIST>.G572`
  - 2.2% (58) `G585@<LOCAL_DENYLIST>.G572,G586@<LOCAL_DENYLIST>.G572,G587@<LOCAL_DENYLIST>.G572,G588@<LOCAL_DENYLIST>.G572,G589@<LOCAL_DENYLIST>.G572`
  - 1.6% (44) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;`
  - 1.3% (36) `G576@<LOCAL_DENYLIST>.G572,G590@<LOCAL_DENYLIST>.G572`
  - 1.2% (32) `G591@<LOCAL_DENYLIST>.G572,G576@<LOCAL_DENYLIST>.G572`
  - 1.0% (28) `G576@<LOCAL_DENYLIST>.G572,G592@<LOCAL_DENYLIST>.G572,G593@<LOCAL_DENYLIST>.G572`
  - 0.9% (24) `G594@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572; DL-G582-Systems@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;G595@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;G596@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572;  DL-G582-Systems@<LOCAL_DENYLIST>.G572;  G597, G598 <G596@<LOCAL_DENYLIST>.G572>`
  - 0.7% (18) `G599@<LOCAL_DENYLIST>.G572,G576@<LOCAL_DENYLIST>.G572`
  - 0.6% (16) `G600@<LOCAL_DENYLIST>.G572`
  - 0.5% (14) `G576@<LOCAL_DENYLIST>.G572,dl_G578@<LOCAL_DENYLIST>.G572`
  - 0.3% (8) `G576@<LOCAL_DENYLIST>.G572`
  - 0.3% (8) `G571@<LOCAL_DENYLIST>.G572`
  - 0.2% (6) `<EMAIL>`
  - 0.2% (6) `G601@<LOCAL_DENYLIST>.G572;G576@<LOCAL_DENYLIST>.G572`
  - 0.1% (2) `G576@<LOCAL_DENYLIST>.G572;G602@<LOCAL_DENYLIST>.G572;G603@<LOCAL_DENYLIST>.G572;G604@<LOCAL_DENYLIST>.G572`
- patterns:
  - 47.6% (1270) `G576@<LOCAL_DENYLIST>.G572`
  - 17.4% (464) `G576@<LOCAL_DENYLIST>.G572,dl_acfc_G577@<LOCAL_DENYLIST>.G572,<EMAIL>`
  - 8.3% (222) `G571@<LOCAL_DENYLIST>.G572`
  - 5.1% (136) `dl_G578@<LOCAL_DENYLIST>.G572,G576@<LOCAL_DENYLIST>.G572`
  - 4.3% (116) `G579@<LOCAL_DENYLIST>.G572,G580@<LOCAL_DENYLIST>.G572`
  - 3.0% (80) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;G583@<LOCAL_DENYLIST>.G572;G584@<LOCAL_DENYLIST>.G572`
  - 2.2% (58) `G585@<LOCAL_DENYLIST>.G572,G586@<LOCAL_DENYLIST>.G572,G587@<LOCAL_DENYLIST>.G572,G588@<LOCAL_DENYLIST>.G572,G589@<LOCAL_DENYLIST>.G572`
  - 1.6% (44) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;`
  - 1.3% (36) `G576@<LOCAL_DENYLIST>.G572,G590@<LOCAL_DENYLIST>.G572`
  - 1.2% (32) `G591@<LOCAL_DENYLIST>.G572,G576@<LOCAL_DENYLIST>.G572`
  - 1.0% (28) `G576@<LOCAL_DENYLIST>.G572,G592@<LOCAL_DENYLIST>.G572,G593@<LOCAL_DENYLIST>.G572`
  - 0.9% (24) `G594@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572; DL-G582-Systems@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;G595@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572;DL-G582-Systems@<LOCAL_DENYLIST>.G572;G596@<LOCAL_DENYLIST>.G572`
  - 0.7% (20) `G581@<LOCAL_DENYLIST>.G572;  DL-G582-Systems@<LOCAL_DENYLIST>.G572;  G597, G598 <G596@<LOCAL_DENYLIST>.G572>`
  - 0.7% (18) `G599@<LOCAL_DENYLIST>.G572,G576@<LOCAL_DENYLIST>.G572`
  - 0.6% (16) `G600@<LOCAL_DENYLIST>.G572`
  - 0.5% (14) `G576@<LOCAL_DENYLIST>.G572,dl_G578@<LOCAL_DENYLIST>.G572`
  - 0.3% (8) `G576@<LOCAL_DENYLIST>.G572`
  - 0.3% (8) `G571@<LOCAL_DENYLIST>.G572`
  - 0.2% (6) `<EMAIL>`
  - 0.2% (6) `G601@<LOCAL_DENYLIST>.G572;G576@<LOCAL_DENYLIST>.G572`
  - 0.1% (2) `G576@<LOCAL_DENYLIST>.G572;G602@<LOCAL_DENYLIST>.G572;G603@<LOCAL_DENYLIST>.G572;G604@<LOCAL_DENYLIST>.G572`

### EMAIL_TEMPLATE_CONFIG.EMAIL_CC

- values:
  - 26.7% (676) `G605@<LOCAL_DENYLIST>.G572,G606@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G610@<LOCAL_DENYLIST>.G572,G611@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572`
  - 18.3% (464) `G613-G614@<LOCAL_DENYLIST>.G615.G572,G616@<LOCAL_DENYLIST>.G572,G579@<LOCAL_DENYLIST>.G572`
  - 12.1% (308) `G605@<LOCAL_DENYLIST>.G572,G606@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572`
  - 8.8% (222) `G571@<LOCAL_DENYLIST>.G572`
  - 7.3% (184) `G617@<LOCAL_DENYLIST>.G572;G618@<LOCAL_DENYLIST>.G572; G619@<LOCAL_DENYLIST>.G572;G620@<LOCAL_DENYLIST>.G572;G606@<LOCAL_DENYLIST>.G572;G607@<LOCAL_DENYLIST>.G572;G621@<LOCAL_DENYLIST>.G572;G622@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572,G580@<LOCAL_DENYLIST>.G572`
  - 5.4% (136) `G594@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572`
  - 4.6% (116) `G623@<LOCAL_DENYLIST>.G572`
  - 2.3% (58) `G624@<LOCAL_DENYLIST>.G572,G625@<LOCAL_DENYLIST>.G572`
  - 2.0% (50) `G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572`
  - 1.5% (38) `G626@<LOCAL_DENYLIST>.G572,G627@<LOCAL_DENYLIST>.G572`
  - 1.4% (36) `G626@<LOCAL_DENYLIST>.G572,G627@<LOCAL_DENYLIST>.G572,G628@<LOCAL_DENYLIST>.G572`
  - 1.4% (36) `G601@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572,G594@<LOCAL_DENYLIST>.G572`
  - 1.1% (28) `G628@<LOCAL_DENYLIST>.G572;G626@<LOCAL_DENYLIST>.G572`
  - 1.1% (28) `dl_G578@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G629@<LOCAL_DENYLIST>.G572`
  - 0.9% (24) `G626@<LOCAL_DENYLIST>.G572,G630@<LOCAL_DENYLIST>.G572`
  - 0.9% (22) `G627@<LOCAL_DENYLIST>.G572;G626@<LOCAL_DENYLIST>.G572`
  - 0.8% (20) `G576@<LOCAL_DENYLIST>.G572`
  - 0.8% (20) `G617@<LOCAL_DENYLIST>.G572;G618@<LOCAL_DENYLIST>.G572; G619@<LOCAL_DENYLIST>.G572;G620@<LOCAL_DENYLIST>.G572;G606@<LOCAL_DENYLIST>.G572;G607@<LOCAL_DENYLIST>.G572;G621@<LOCAL_DENYLIST>.G572;G622@<LOCAL_DENYLIST>.G572;`
  - 0.8% (20) `G626@<LOCAL_DENYLIST>.G572;G630@<LOCAL_DENYLIST>.G572;G628@<LOCAL_DENYLIST>.G572`
  - 0.5% (12) `G594@<LOCAL_DENYLIST>.G572`
  - 0.5% (12) `G594@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572`
  - 0.3% (8) `G631@<LOCAL_DENYLIST>.G572`
  - 0.2% (6) `G611@<LOCAL_DENYLIST>.G572`
  - 0.2% (4) `G626@<LOCAL_DENYLIST>.G572,G627@<LOCAL_DENYLIST>.G572,G632@<LOCAL_DENYLIST>.G572`
  - 0.2% (4) `<EMAIL>;G589@<LOCAL_DENYLIST>.G572`
  - 0.1% (2) `G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572,G633@<LOCAL_DENYLIST>.G572`
  - 0.1% (2) `G634@<LOCAL_DENYLIST>.G572`
- patterns:
  - 26.7% (676) `G605@<LOCAL_DENYLIST>.G572,G606@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G610@<LOCAL_DENYLIST>.G572,G611@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572`
  - 18.3% (464) `G613-G614@<LOCAL_DENYLIST>.G615.G572,G616@<LOCAL_DENYLIST>.G572,G579@<LOCAL_DENYLIST>.G572`
  - 12.1% (308) `G605@<LOCAL_DENYLIST>.G572,G606@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572`
  - 8.8% (222) `G571@<LOCAL_DENYLIST>.G572`
  - 7.3% (184) `G617@<LOCAL_DENYLIST>.G572;G618@<LOCAL_DENYLIST>.G572; G619@<LOCAL_DENYLIST>.G572;G620@<LOCAL_DENYLIST>.G572;G606@<LOCAL_DENYLIST>.G572;G607@<LOCAL_DENYLIST>.G572;G621@<LOCAL_DENYLIST>.G572;G622@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572,G580@<LOCAL_DENYLIST>.G572`
  - 5.4% (136) `G594@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572`
  - 4.6% (116) `G623@<LOCAL_DENYLIST>.G572`
  - 2.3% (58) `G624@<LOCAL_DENYLIST>.G572,G625@<LOCAL_DENYLIST>.G572`
  - 2.0% (50) `G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572`
  - 1.5% (38) `G626@<LOCAL_DENYLIST>.G572,G627@<LOCAL_DENYLIST>.G572`
  - 1.4% (36) `G626@<LOCAL_DENYLIST>.G572,G627@<LOCAL_DENYLIST>.G572,G628@<LOCAL_DENYLIST>.G572`
  - 1.4% (36) `G601@<LOCAL_DENYLIST>.G572,G607@<LOCAL_DENYLIST>.G572,G612@<LOCAL_DENYLIST>.G572,G594@<LOCAL_DENYLIST>.G572`
  - 1.1% (28) `G628@<LOCAL_DENYLIST>.G572;G626@<LOCAL_DENYLIST>.G572`
  - 1.1% (28) `dl_G578@<LOCAL_DENYLIST>.G572,G608@<LOCAL_DENYLIST>.G572,G629@<LOCAL_DENYLIST>.G572`
  - 0.9% (24) `G626@<LOCAL_DENYLIST>.G572,G630@<LOCAL_DENYLIST>.G572`
  - 0.9% (22) `G627@<LOCAL_DENYLIST>.G572;G626@<LOCAL_DENYLIST>.G572`
  - 0.8% (20) `G576@<LOCAL_DENYLIST>.G572`
  - 0.8% (20) `G617@<LOCAL_DENYLIST>.G572;G618@<LOCAL_DENYLIST>.G572; G619@<LOCAL_DENYLIST>.G572;G620@<LOCAL_DENYLIST>.G572;G606@<LOCAL_DENYLIST>.G572;G607@<LOCAL_DENYLIST>.G572;G621@<LOCAL_DENYLIST>.G572;G622@<LOCAL_DENYLIST>.G572;`
  - 0.8% (20) `G626@<LOCAL_DENYLIST>.G572;G630@<LOCAL_DENYLIST>.G572;G628@<LOCAL_DENYLIST>.G572`
  - 0.5% (12) `G594@<LOCAL_DENYLIST>.G572`
  - 0.5% (12) `G594@<LOCAL_DENYLIST>.G572,G601@<LOCAL_DENYLIST>.G572`
  - 0.3% (8) `G631@<LOCAL_DENYLIST>.G572`
  - 0.2% (6) `G611@<LOCAL_DENYLIST>.G572`
  - 0.2% (4) `G626@<LOCAL_DENYLIST>.G572,G627@<LOCAL_DENYLIST>.G572,G632@<LOCAL_DENYLIST>.G572`
  - 0.2% (4) `<EMAIL>;G589@<LOCAL_DENYLIST>.G572`
  - 0.1% (2) `G601@<LOCAL_DENYLIST>.G572,G609@<LOCAL_DENYLIST>.G572,G605@<LOCAL_DENYLIST>.G572,G633@<LOCAL_DENYLIST>.G572`
  - 0.1% (2) `G634@<LOCAL_DENYLIST>.G572`

### EMAIL_TEMPLATE_CONFIG.CREATED_AT

- values:
  - 25.3% (676) `2025-12-18 12:30:00`
  - 19.6% (522) `2025-10-23 09:47:20`
  - 11.5% (308) `2025-07-31 11:12:13`
  - 8.5% (226) `2026-09-17 00:00:00`
  - 5.7% (152) `2026-02-26 00:00:00`
  - 3.6% (96) `2026-04-09 10:00:00`
  - 2.2% (58) `2024-07-05 13:48:25`
  - 2.2% (58) `2024-07-03 07:28:26`
  - 2.2% (58) `2024-10-24 14:38:14`
  - 2.0% (54) `2026-09-10 17:00:00`
  - 1.5% (40) `2026-02-12 00:00:00`
  - 1.5% (40) `2026-02-19 17:36:40`
  - 1.5% (40) `2026-03-12 09:49:52`
  - 1.3% (36) `2026-04-23 00:00:00`
  - 1.3% (36) `2025-08-26 10:00:00`
  - 1.3% (34) `2026-06-25 00:00:00`
  - 1.2% (32) `2025-11-13 19:43:38`
  - 1.0% (28) `2025-10-01 00:00:00`
  - 0.9% (24) `2026-08-06 00:00:00`
  - 0.7% (20) `2026-04-28 00:00:00`
  - 0.7% (18) `2025-07-08 21:13:31`
  - 0.7% (18) `2026-09-24 00:00:00`
  - 0.6% (16) `2024-09-12 12:59:38`
  - 0.5% (14) `2026-08-20 00:00:00`
  - 0.5% (14) `2025-07-31 12:44:18`
  - 0.4% (12) `2026-09-03 00:00:00`
  - 0.3% (8) `2024-10-24 12:25:55`
  - 0.3% (8) `2026-08-13 00:00:00`
  - 0.2% (6) `2026-04-09 00:00:00`
  - 0.1% (4) `2026-09-17 00:00:01`
  - 0.1% (4) `2026-09-17 17:00:00`
  - 0.1% (4) `2026-09-11 00:00:00`
  - 0.0% (1) `2024-01-30 20:53:47`
  - 0.0% (1) `2024-01-30 20:58:28`
  - 0.0% (1) `2026-04-20 13:59:44`
  - 0.0% (1) `2026-04-20 14:00:45`
- patterns:
  - 25.3% (676) `2025-12-18 12:30:00`
  - 19.6% (522) `2025-10-23 09:47:20`
  - 11.5% (308) `2025-07-31 11:12:13`
  - 8.5% (226) `2026-09-17 00:00:00`
  - 5.7% (152) `2026-02-26 00:00:00`
  - 3.6% (96) `2026-04-09 10:00:00`
  - 2.2% (58) `2024-07-05 13:48:25`
  - 2.2% (58) `2024-07-03 07:28:26`
  - 2.2% (58) `2024-10-24 14:38:14`
  - 2.0% (54) `2026-09-10 17:00:00`
  - 1.5% (40) `2026-02-12 00:00:00`
  - 1.5% (40) `2026-02-19 17:36:40`
  - 1.5% (40) `2026-03-12 09:49:52`
  - 1.3% (36) `2026-04-23 00:00:00`
  - 1.3% (36) `2025-08-26 10:00:00`
  - 1.3% (34) `2026-06-25 00:00:00`
  - 1.2% (32) `2025-11-13 19:43:38`
  - 1.0% (28) `2025-10-01 00:00:00`
  - 0.9% (24) `2026-08-06 00:00:00`
  - 0.7% (20) `2026-04-28 00:00:00`
  - 0.7% (18) `2025-07-08 21:13:31`
  - 0.7% (18) `2026-09-24 00:00:00`
  - 0.6% (16) `2024-09-12 12:59:38`
  - 0.5% (14) `2026-08-20 00:00:00`
  - 0.5% (14) `2025-07-31 12:44:18`
  - 0.4% (12) `2026-09-03 00:00:00`
  - 0.3% (8) `2024-10-24 12:25:55`
  - 0.3% (8) `2026-08-13 00:00:00`
  - 0.2% (6) `2026-04-09 00:00:00`
  - 0.1% (4) `2026-09-17 00:00:01`
  - 0.1% (4) `2026-09-17 17:00:00`
  - 0.1% (4) `2026-09-11 00:00:00`
  - 0.0% (1) `2024-01-30 20:53:47`
  - 0.0% (1) `2024-01-30 20:58:28`
  - 0.0% (1) `2026-04-20 13:59:44`
  - 0.0% (1) `2026-04-20 14:00:45`

### EMAIL_TEMPLATE_CONFIG.UPDATED_AT

- values:
  - 24.1% (3240) `2026-07-02 15:34:17`
  - 24.1% (3240) `2026-07-02 15:34:42`
  - 16.0% (2160) `2026-07-02 15:33:29`
  - 16.0% (2160) `2026-07-02 15:34:51`
  - 3.4% (464) `2026-01-06 20:51:28`
  - 2.7% (368) `2026-07-02 14:27:33`
  - 2.3% (308) `2026-07-02 15:33:17`
  - 2.3% (308) `2026-07-02 15:28:21`
  - 1.6% (222) `2026-09-17 00:00:00`
  - 0.9% (124) `2026-07-02 15:20:38`
  - 0.9% (116) `2025-10-24 19:20:50`
  - 0.9% (116) `2026-07-02 15:33:23`
  - 0.7% (98) `2026-07-02 15:20:17`
  - 0.6% (86) `2026-10-01 20:11:44`
  - 0.5% (63) `2026-07-02 15:21:02`
  - 0.4% (54) `2026-09-10 17:00:00`
  - 0.3% (40) `2026-07-02 15:26:26`
  - 0.3% (36) `2026-07-02 15:25:25`
  - 0.2% (24) `2026-07-02 15:33:15`
  - 0.2% (24) `2026-08-06 00:00:00`
  - 0.2% (21) `2026-07-02 15:26:53`
  - 0.1% (20) `2026-07-02 13:14:10`
  - 0.1% (18) `2026-09-24 00:00:00`
  - 0.1% (16) `2026-07-02 15:34:41`
  - 0.1% (16) `2026-07-02 15:34:32`
  - 0.1% (15) `2026-07-02 15:34:48`
  - 0.1% (14) `2026-07-02 13:15:04`
  - 0.1% (14) `2026-07-02 15:28:44`
  - 0.1% (14) `2026-07-02 15:29:52`
  - 0.1% (12) `2026-09-30 15:43:02`
  - 0.1% (10) `2026-07-02 15:18:57`
  - 0.1% (10) `2026-07-02 15:25:05`
  - 0.1% (8) `2026-09-10 13:12:38`
  - 0.1% (8) `2026-08-13 00:00:00`
  - 0.0% (6) `2026-08-20 00:00:00`
  - 0.0% (5) `2026-07-02 14:23:50`
  - 0.0% (4) `2026-09-17 17:00:00`
  - 0.0% (4) `2026-09-11 00:00:00`
  - 0.0% (2) `2026-07-02 15:17:48`
- patterns:
  - 24.1% (3240) `2026-07-02 15:34:17`
  - 24.1% (3240) `2026-07-02 15:34:42`
  - 16.0% (2160) `2026-07-02 15:33:29`
  - 16.0% (2160) `2026-07-02 15:34:51`
  - 3.4% (464) `2026-01-06 20:51:28`
  - 2.7% (368) `2026-07-02 14:27:33`
  - 2.3% (308) `2026-07-02 15:33:17`
  - 2.3% (308) `2026-07-02 15:28:21`
  - 1.6% (222) `2026-09-17 00:00:00`
  - 0.9% (124) `2026-07-02 15:20:38`
  - 0.9% (116) `2025-10-24 19:20:50`
  - 0.9% (116) `2026-07-02 15:33:23`
  - 0.7% (98) `2026-07-02 15:20:17`
  - 0.6% (86) `2026-10-01 20:11:44`
  - 0.5% (63) `2026-07-02 15:21:02`
  - 0.4% (54) `2026-09-10 17:00:00`
  - 0.3% (40) `2026-07-02 15:26:26`
  - 0.3% (36) `2026-07-02 15:25:25`
  - 0.2% (24) `2026-07-02 15:33:15`
  - 0.2% (24) `2026-08-06 00:00:00`
  - 0.2% (21) `2026-07-02 15:26:53`
  - 0.1% (20) `2026-07-02 13:14:10`
  - 0.1% (18) `2026-09-24 00:00:00`
  - 0.1% (16) `2026-07-02 15:34:41`
  - 0.1% (16) `2026-07-02 15:34:32`
  - 0.1% (15) `2026-07-02 15:34:48`
  - 0.1% (14) `2026-07-02 13:15:04`
  - 0.1% (14) `2026-07-02 15:28:44`
  - 0.1% (14) `2026-07-02 15:29:52`
  - 0.1% (12) `2026-09-30 15:43:02`
  - 0.1% (10) `2026-07-02 15:18:57`
  - 0.1% (10) `2026-07-02 15:25:05`
  - 0.1% (8) `2026-09-10 13:12:38`
  - 0.1% (8) `2026-08-13 00:00:00`
  - 0.0% (6) `2026-08-20 00:00:00`
  - 0.0% (5) `2026-07-02 14:23:50`
  - 0.0% (4) `2026-09-17 17:00:00`
  - 0.0% (4) `2026-09-11 00:00:00`
  - 0.0% (2) `2026-07-02 15:17:48`

### EMAIL_TEMPLATE_CONFIG.EMAIL_NOTIFICATION_URL

- values:
  - 95.4% (12852) `https://<REAL_WEBHOOK_HOST>:443/api/LOG_EMAIL_WITH_G635/G636/When_an_G637_request_is_received/G638?api-version=2022-05-01&sp=%G639%G640_an_G637_request_is_received%G641&sv=1.0&G642=G643-G644`
  - 4.3% (580) `https://prod-10.G645.logic.G573.G572/G646/G647/G636/G648/paths/G638?api-version=2016-10-01&sp=%G639%G649%G641&sv=1.0&G642=G650_G651-G652`
  - 0.3% (36) `https://prod-58.G645.logic.G573.G572:443/G646/G653/G636/G648/paths/G638?api-version=2016-10-01&sp=%G639%G649%G641&sv=1.0&G642=G654_G655_G656`
- patterns:
  - 95.4% (12852) `https://<REAL_WEBHOOK_HOST>:443/api/LOG_EMAIL_WITH_G635/G636/When_an_G637_request_is_received/G638?api-version=2022-05-01&sp=%G639%G640_an_G637_request_is_received%G641&sv=1.0&G642=G643-G644`
  - 4.3% (580) `https://prod-10.G645.logic.G573.G572/G646/G647/G636/G648/paths/G638?api-version=2016-10-01&sp=%G639%G649%G641&sv=1.0&G642=G650_G651-G652`
  - 0.3% (36) `https://prod-58.G645.logic.G573.G572:443/G646/G653/G636/G648/paths/G638?api-version=2016-10-01&sp=%G639%G649%G641&sv=1.0&G642=G654_G655_G656`

## Grand master / master schedule rows

- rows by kind (description / name, else a PARENT_PIPELINE_ID): {'master': 1850, 'grand_master': 1830, 'parent': 1161}
- GROUP_IDs under one master row -> master rows: {'0': 4445, '1': 396}
- master rows over one GROUP_ID -> GROUP_IDs: {'1': 2, '2': 197}

| workbook | schedule rows | GROUP_IDs | grand master | master | parent only |
|---|---|---|---|---|---|
| 1 | 4 | 1 | 1 | 1 | 0 |
| 2 | 24 | 1 | 4 | 4 | 0 |
| 3 | 24 | 1 | 4 | 4 | 0 |
| 4 | 24 | 1 | 4 | 4 | 0 |
| 5 | 24 | 1 | 4 | 4 | 0 |
| 6 | 24 | 1 | 4 | 4 | 0 |
| 7 | 24 | 1 | 4 | 4 | 0 |
| 8 | 24 | 1 | 4 | 4 | 0 |
| 9 | 24 | 1 | 4 | 4 | 0 |
| 10 | 24 | 1 | 4 | 4 | 0 |
| 11 | 24 | 1 | 4 | 4 | 0 |
| 12 | 24 | 1 | 4 | 4 | 0 |
| 13 | 24 | 1 | 4 | 4 | 0 |
| 14 | 24 | 1 | 4 | 4 | 0 |
| 15 | 24 | 1 | 4 | 4 | 0 |
| 16 | 24 | 1 | 4 | 4 | 0 |
| 17 | 24 | 1 | 4 | 4 | 0 |
| 18 | 8 | 1 | 1 | 1 | 0 |
| 19 | 8 | 1 | 1 | 1 | 0 |
| 20 | 8 | 1 | 1 | 1 | 0 |
| 21 | 8 | 1 | 1 | 1 | 0 |
| 22 | 8 | 1 | 1 | 1 | 0 |
| 23 | 8 | 1 | 1 | 1 | 0 |
| 24 | 4 | 1 | 1 | 0 | 1 |
| 25 | 4 | 1 | 1 | 0 | 1 |
| 26 | 4 | 1 | 1 | 1 | 0 |
| 27 | 4 | 1 | 1 | 1 | 0 |
| 28 | 92 | 1 | 6 | 5 | 2 |
| 29 | 92 | 1 | 6 | 5 | 2 |
| 30 | 92 | 1 | 6 | 5 | 2 |
| 31 | 92 | 1 | 6 | 5 | 2 |
| 32 | 92 | 1 | 6 | 5 | 2 |
| 33 | 92 | 1 | 6 | 5 | 2 |
| 34 | 92 | 1 | 6 | 5 | 2 |
| 35 | 92 | 1 | 6 | 5 | 2 |
| 36 | 92 | 1 | 6 | 5 | 2 |
| 37 | 92 | 1 | 6 | 5 | 2 |
| 38 | 92 | 1 | 6 | 5 | 2 |
| 39 | 92 | 1 | 6 | 5 | 2 |
| 40 | 92 | 1 | 6 | 5 | 2 |
| 41 | 92 | 1 | 6 | 5 | 2 |
| 42 | 92 | 1 | 6 | 5 | 2 |
| 43 | 92 | 1 | 6 | 5 | 2 |
| 44 | 92 | 1 | 6 | 5 | 2 |
| 45 | 92 | 1 | 6 | 5 | 2 |
| 46 | 92 | 1 | 6 | 5 | 2 |
| 47 | 92 | 1 | 6 | 5 | 2 |
| 48 | 92 | 1 | 6 | 5 | 2 |
| 49 | 92 | 1 | 6 | 5 | 2 |
| 50 | 92 | 1 | 6 | 5 | 2 |
| 51 | 92 | 1 | 6 | 5 | 2 |
| 52 | 92 | 1 | 6 | 5 | 2 |
| 53 | 92 | 1 | 6 | 5 | 2 |
| 54 | 92 | 1 | 6 | 5 | 2 |
| 55 | 92 | 1 | 6 | 5 | 2 |
| 56 | 92 | 1 | 6 | 5 | 2 |
| 57 | 92 | 1 | 6 | 5 | 2 |
| 58 | 92 | 1 | 6 | 5 | 2 |
| 59 | 92 | 1 | 6 | 5 | 2 |
| 60 | 92 | 1 | 6 | 5 | 2 |
| 61 | 92 | 1 | 6 | 5 | 2 |
| 62 | 92 | 1 | 6 | 5 | 2 |
| 63 | 92 | 1 | 6 | 5 | 2 |
| 64 | 92 | 1 | 6 | 5 | 2 |
| 65 | 92 | 1 | 6 | 5 | 2 |
| 66 | 92 | 1 | 6 | 5 | 2 |
| 67 | 92 | 1 | 6 | 5 | 2 |
| 68 | 92 | 1 | 6 | 5 | 2 |
| 69 | 92 | 1 | 6 | 5 | 2 |
| 70 | 92 | 1 | 6 | 5 | 2 |
| 71 | 92 | 1 | 6 | 5 | 2 |
| 72 | 92 | 1 | 6 | 5 | 2 |
| 73 | 92 | 1 | 6 | 5 | 2 |
| 74 | 92 | 1 | 6 | 5 | 2 |
| 75 | 92 | 1 | 6 | 5 | 2 |
| 76 | 92 | 1 | 6 | 5 | 2 |
| 77 | 92 | 1 | 6 | 5 | 2 |
| 78 | 92 | 1 | 6 | 5 | 2 |
| 79 | 92 | 1 | 6 | 5 | 2 |
| 80 | 92 | 1 | 6 | 5 | 2 |
| 81 | 92 | 1 | 6 | 5 | 2 |
| 82 | 92 | 1 | 6 | 5 | 2 |
| 83 | 92 | 1 | 6 | 5 | 2 |
| 84 | 92 | 1 | 6 | 5 | 2 |
| 85 | 92 | 1 | 6 | 5 | 2 |
| 86 | 92 | 1 | 6 | 5 | 2 |
| 87 | 92 | 1 | 6 | 5 | 2 |
| 88 | 92 | 1 | 6 | 5 | 2 |
| 89 | 92 | 1 | 6 | 5 | 2 |
| 90 | 92 | 1 | 6 | 5 | 2 |
| 91 | 92 | 1 | 6 | 5 | 2 |
| 92 | 92 | 1 | 6 | 5 | 2 |
| 93 | 92 | 1 | 6 | 5 | 2 |
| 94 | 92 | 1 | 6 | 5 | 2 |
| 95 | 92 | 1 | 6 | 5 | 2 |
| 96 | 92 | 1 | 6 | 5 | 2 |
| 97 | 92 | 1 | 6 | 5 | 2 |
| 98 | 92 | 1 | 6 | 5 | 2 |
| 99 | 92 | 1 | 6 | 5 | 2 |
| 100 | 92 | 1 | 6 | 5 | 2 |
| 101 | 92 | 1 | 6 | 5 | 2 |
| 102 | 92 | 1 | 6 | 5 | 2 |
| 103 | 92 | 1 | 6 | 5 | 2 |
| 104 | 92 | 1 | 6 | 5 | 2 |
| 105 | 92 | 1 | 6 | 5 | 2 |
| 106 | 92 | 1 | 6 | 5 | 2 |
| 107 | 111 | 1 | 4 | 5 | 11 |
| 108 | 111 | 1 | 4 | 5 | 11 |
| 109 | 111 | 1 | 4 | 5 | 11 |
| 110 | 111 | 1 | 4 | 5 | 11 |
| 111 | 111 | 1 | 4 | 5 | 11 |
| 112 | 111 | 1 | 4 | 5 | 11 |
| 113 | 111 | 1 | 4 | 5 | 11 |
| 114 | 111 | 1 | 4 | 5 | 11 |
| 115 | 111 | 1 | 4 | 5 | 11 |
| 116 | 111 | 1 | 4 | 5 | 11 |
| 117 | 111 | 1 | 4 | 5 | 11 |
| 118 | 111 | 1 | 4 | 5 | 11 |
| 119 | 111 | 1 | 4 | 5 | 11 |
| 120 | 111 | 1 | 4 | 5 | 11 |
| 121 | 111 | 1 | 4 | 5 | 11 |
| 122 | 111 | 1 | 4 | 5 | 11 |
| 123 | 111 | 1 | 4 | 5 | 11 |
| 124 | 111 | 1 | 4 | 5 | 11 |
| 125 | 111 | 1 | 4 | 5 | 11 |
| 126 | 111 | 1 | 4 | 5 | 11 |
| 127 | 111 | 1 | 4 | 5 | 11 |
| 128 | 111 | 1 | 4 | 5 | 11 |
| 129 | 111 | 1 | 4 | 5 | 11 |
| 130 | 111 | 1 | 4 | 5 | 11 |
| 131 | 111 | 1 | 4 | 5 | 11 |
| 132 | 111 | 1 | 4 | 5 | 11 |
| 133 | 111 | 1 | 4 | 5 | 11 |
| 134 | 111 | 1 | 4 | 5 | 11 |
| 135 | 111 | 1 | 4 | 5 | 11 |
| 136 | 111 | 1 | 4 | 5 | 11 |
| 137 | 111 | 1 | 4 | 5 | 11 |
| 138 | 111 | 1 | 4 | 5 | 11 |
| 139 | 111 | 1 | 4 | 5 | 11 |
| 140 | 111 | 1 | 4 | 5 | 11 |
| 141 | 111 | 1 | 4 | 5 | 11 |
| 142 | 111 | 1 | 4 | 5 | 11 |
| 143 | 111 | 1 | 4 | 5 | 11 |
| 144 | 111 | 1 | 4 | 5 | 11 |
| 145 | 111 | 1 | 4 | 5 | 11 |
| 146 | 111 | 1 | 4 | 5 | 11 |
| 147 | 111 | 1 | 4 | 5 | 11 |
| 148 | 111 | 1 | 4 | 5 | 11 |
| 149 | 111 | 1 | 4 | 5 | 11 |
| 150 | 111 | 1 | 4 | 5 | 11 |
| 151 | 111 | 1 | 4 | 5 | 11 |
| 152 | 111 | 1 | 4 | 5 | 11 |
| 153 | 111 | 1 | 4 | 5 | 11 |
| 154 | 111 | 1 | 4 | 5 | 11 |
| 155 | 111 | 1 | 4 | 5 | 11 |
| 156 | 111 | 1 | 4 | 5 | 11 |
| 157 | 111 | 1 | 4 | 5 | 11 |
| 158 | 111 | 1 | 4 | 5 | 11 |
| 159 | 111 | 1 | 4 | 5 | 11 |
| 160 | 111 | 1 | 4 | 5 | 11 |
| 161 | 111 | 1 | 4 | 5 | 11 |
| 162 | 111 | 1 | 4 | 5 | 11 |
| 163 | 111 | 1 | 4 | 5 | 11 |
| 164 | 111 | 1 | 4 | 5 | 11 |
| 165 | 111 | 1 | 4 | 5 | 11 |
| 166 | 111 | 1 | 4 | 5 | 11 |
| 167 | 111 | 1 | 4 | 5 | 11 |
| 168 | 111 | 1 | 4 | 5 | 11 |
| 169 | 111 | 1 | 4 | 5 | 11 |
| 170 | 111 | 1 | 4 | 5 | 11 |
| 171 | 111 | 1 | 4 | 5 | 11 |
| 172 | 111 | 1 | 4 | 5 | 11 |
| 173 | 111 | 1 | 4 | 5 | 11 |
| 174 | 111 | 1 | 4 | 5 | 11 |
| 175 | 111 | 1 | 4 | 5 | 11 |
| 176 | 111 | 1 | 4 | 5 | 11 |
| 177 | 111 | 1 | 4 | 5 | 11 |
| 178 | 111 | 1 | 4 | 5 | 11 |
| 179 | 111 | 1 | 4 | 5 | 11 |
| 180 | 111 | 1 | 4 | 5 | 11 |
| 181 | 111 | 1 | 4 | 5 | 11 |
| 182 | 111 | 1 | 4 | 5 | 11 |
| 183 | 111 | 1 | 4 | 5 | 11 |
| 184 | 111 | 1 | 4 | 5 | 11 |
| 185 | 111 | 1 | 4 | 5 | 11 |
| 186 | 111 | 1 | 4 | 5 | 11 |
| 187 | 111 | 1 | 4 | 5 | 11 |
| 188 | 111 | 1 | 4 | 5 | 11 |
| 189 | 111 | 1 | 4 | 5 | 11 |
| 190 | 111 | 1 | 4 | 5 | 11 |
| 191 | 111 | 1 | 4 | 5 | 11 |
| 192 | 111 | 1 | 4 | 5 | 11 |
| 193 | 111 | 1 | 4 | 5 | 11 |
| 194 | 111 | 1 | 4 | 5 | 11 |
| 195 | 111 | 1 | 4 | 5 | 11 |
| 196 | 111 | 1 | 4 | 5 | 11 |
| 197 | 111 | 1 | 4 | 5 | 11 |
| 198 | 4 | 1 | 1 | 1 | 0 |
| 199 | 4 | 1 | 1 | 1 | 0 |
| 200 | 4 | 0 | 1 | 1 | 0 |
| 201 | 24 | 0 | 4 | 4 | 0 |
| 202 | 24 | 0 | 4 | 4 | 0 |
| 203 | 24 | 0 | 4 | 4 | 0 |
| 204 | 24 | 0 | 4 | 4 | 0 |
| 205 | 24 | 0 | 4 | 4 | 0 |
| 206 | 24 | 0 | 4 | 4 | 0 |
| 207 | 24 | 0 | 4 | 4 | 0 |
| 208 | 24 | 0 | 4 | 4 | 0 |
| 209 | 24 | 0 | 4 | 4 | 0 |
| 210 | 24 | 0 | 4 | 4 | 0 |
| 211 | 24 | 0 | 4 | 4 | 0 |
| 212 | 24 | 0 | 4 | 4 | 0 |
| 213 | 24 | 0 | 4 | 4 | 0 |
| 214 | 24 | 0 | 4 | 4 | 0 |
| 215 | 24 | 0 | 4 | 4 | 0 |
| 216 | 24 | 0 | 4 | 4 | 0 |
| 217 | 8 | 0 | 1 | 1 | 0 |
| 218 | 8 | 0 | 1 | 1 | 0 |
| 219 | 8 | 0 | 1 | 1 | 0 |
| 220 | 8 | 0 | 1 | 1 | 0 |
| 221 | 8 | 0 | 1 | 1 | 0 |
| 222 | 8 | 0 | 1 | 1 | 0 |
| 223 | 4 | 0 | 1 | 0 | 0 |
| 224 | 4 | 0 | 1 | 0 | 0 |
| 225 | 4 | 0 | 1 | 1 | 0 |
| 226 | 4 | 0 | 1 | 1 | 0 |
| 227 | 92 | 0 | 6 | 5 | 0 |
| 228 | 92 | 0 | 6 | 5 | 0 |
| 229 | 92 | 0 | 6 | 5 | 0 |
| 230 | 92 | 0 | 6 | 5 | 0 |
| 231 | 92 | 0 | 6 | 5 | 0 |
| 232 | 92 | 0 | 6 | 5 | 0 |
| 233 | 92 | 0 | 6 | 5 | 0 |
| 234 | 92 | 0 | 6 | 5 | 0 |
| 235 | 92 | 0 | 6 | 5 | 0 |
| 236 | 92 | 0 | 6 | 5 | 0 |
| 237 | 92 | 0 | 6 | 5 | 0 |
| 238 | 92 | 0 | 6 | 5 | 0 |
| 239 | 92 | 0 | 6 | 5 | 0 |
| 240 | 92 | 0 | 6 | 5 | 0 |
| 241 | 92 | 0 | 6 | 5 | 0 |
| 242 | 92 | 0 | 6 | 5 | 0 |
| 243 | 92 | 0 | 6 | 5 | 0 |
| 244 | 92 | 0 | 6 | 5 | 0 |
| 245 | 92 | 0 | 6 | 5 | 0 |
| 246 | 92 | 0 | 6 | 5 | 0 |
| 247 | 92 | 0 | 6 | 5 | 0 |
| 248 | 92 | 0 | 6 | 5 | 0 |
| 249 | 92 | 0 | 6 | 5 | 0 |
| 250 | 92 | 0 | 6 | 5 | 0 |
| 251 | 92 | 0 | 6 | 5 | 0 |
| 252 | 92 | 0 | 6 | 5 | 0 |
| 253 | 92 | 0 | 6 | 5 | 0 |
| 254 | 92 | 0 | 6 | 5 | 0 |
| 255 | 92 | 0 | 6 | 5 | 0 |
| 256 | 92 | 0 | 6 | 5 | 0 |
| 257 | 92 | 0 | 6 | 5 | 0 |
| 258 | 92 | 0 | 6 | 5 | 0 |
| 259 | 92 | 0 | 6 | 5 | 0 |
| 260 | 92 | 0 | 6 | 5 | 0 |
| 261 | 92 | 0 | 6 | 5 | 0 |
| 262 | 92 | 0 | 6 | 5 | 0 |
| 263 | 92 | 0 | 6 | 5 | 0 |
| 264 | 92 | 0 | 6 | 5 | 0 |
| 265 | 92 | 0 | 6 | 5 | 0 |
| 266 | 92 | 0 | 6 | 5 | 0 |
| 267 | 92 | 0 | 6 | 5 | 0 |
| 268 | 92 | 0 | 6 | 5 | 0 |
| 269 | 92 | 0 | 6 | 5 | 0 |
| 270 | 92 | 0 | 6 | 5 | 0 |
| 271 | 92 | 0 | 6 | 5 | 0 |
| 272 | 92 | 0 | 6 | 5 | 0 |
| 273 | 92 | 0 | 6 | 5 | 0 |
| 274 | 92 | 0 | 6 | 5 | 0 |
| 275 | 92 | 0 | 6 | 5 | 0 |
| 276 | 92 | 0 | 6 | 5 | 0 |
| 277 | 92 | 0 | 6 | 5 | 0 |
| 278 | 92 | 0 | 6 | 5 | 0 |
| 279 | 92 | 0 | 6 | 5 | 0 |
| 280 | 92 | 0 | 6 | 5 | 0 |
| 281 | 92 | 0 | 6 | 5 | 0 |
| 282 | 92 | 0 | 6 | 5 | 0 |
| 283 | 92 | 0 | 6 | 5 | 0 |
| 284 | 92 | 0 | 6 | 5 | 0 |
| 285 | 92 | 0 | 6 | 5 | 0 |
| 286 | 92 | 0 | 6 | 5 | 0 |
| 287 | 92 | 0 | 6 | 5 | 0 |
| 288 | 92 | 0 | 6 | 5 | 0 |
| 289 | 92 | 0 | 6 | 5 | 0 |
| 290 | 92 | 0 | 6 | 5 | 0 |
| 291 | 92 | 0 | 6 | 5 | 0 |
| 292 | 92 | 0 | 6 | 5 | 0 |
| 293 | 92 | 0 | 6 | 5 | 0 |
| 294 | 92 | 0 | 6 | 5 | 0 |
| 295 | 92 | 0 | 6 | 5 | 0 |
| 296 | 92 | 0 | 6 | 5 | 0 |
| 297 | 92 | 0 | 6 | 5 | 0 |
| 298 | 92 | 0 | 6 | 5 | 0 |
| 299 | 92 | 0 | 6 | 5 | 0 |
| 300 | 92 | 0 | 6 | 5 | 0 |
| 301 | 92 | 0 | 6 | 5 | 0 |
| 302 | 92 | 0 | 6 | 5 | 0 |
| 303 | 92 | 0 | 6 | 5 | 0 |
| 304 | 92 | 0 | 6 | 5 | 0 |
| 305 | 92 | 0 | 6 | 5 | 0 |
| 306 | 111 | 0 | 4 | 5 | 0 |
| 307 | 111 | 0 | 4 | 5 | 0 |
| 308 | 111 | 0 | 4 | 5 | 0 |
| 309 | 111 | 0 | 4 | 5 | 0 |
| 310 | 111 | 0 | 4 | 5 | 0 |
| 311 | 111 | 0 | 4 | 5 | 0 |
| 312 | 111 | 0 | 4 | 5 | 0 |
| 313 | 111 | 0 | 4 | 5 | 0 |
| 314 | 111 | 0 | 4 | 5 | 0 |
| 315 | 111 | 0 | 4 | 5 | 0 |
| 316 | 111 | 0 | 4 | 5 | 0 |
| 317 | 111 | 0 | 4 | 5 | 0 |
| 318 | 111 | 0 | 4 | 5 | 0 |
| 319 | 111 | 0 | 4 | 5 | 0 |
| 320 | 111 | 0 | 4 | 5 | 0 |
| 321 | 111 | 0 | 4 | 5 | 0 |
| 322 | 111 | 0 | 4 | 5 | 0 |
| 323 | 111 | 0 | 4 | 5 | 0 |
| 324 | 111 | 0 | 4 | 5 | 0 |
| 325 | 111 | 0 | 4 | 5 | 0 |
| 326 | 111 | 0 | 4 | 5 | 0 |
| 327 | 111 | 0 | 4 | 5 | 0 |
| 328 | 111 | 0 | 4 | 5 | 0 |
| 329 | 111 | 0 | 4 | 5 | 0 |
| 330 | 111 | 0 | 4 | 5 | 0 |
| 331 | 111 | 0 | 4 | 5 | 0 |
| 332 | 111 | 0 | 4 | 5 | 0 |
| 333 | 111 | 0 | 4 | 5 | 0 |
| 334 | 111 | 0 | 4 | 5 | 0 |
| 335 | 111 | 0 | 4 | 5 | 0 |
| 336 | 111 | 0 | 4 | 5 | 0 |
| 337 | 111 | 0 | 4 | 5 | 0 |
| 338 | 111 | 0 | 4 | 5 | 0 |
| 339 | 111 | 0 | 4 | 5 | 0 |
| 340 | 111 | 0 | 4 | 5 | 0 |
| 341 | 111 | 0 | 4 | 5 | 0 |
| 342 | 111 | 0 | 4 | 5 | 0 |
| 343 | 111 | 0 | 4 | 5 | 0 |
| 344 | 111 | 0 | 4 | 5 | 0 |
| 345 | 111 | 0 | 4 | 5 | 0 |
| 346 | 111 | 0 | 4 | 5 | 0 |
| 347 | 111 | 0 | 4 | 5 | 0 |
| 348 | 111 | 0 | 4 | 5 | 0 |
| 349 | 111 | 0 | 4 | 5 | 0 |
| 350 | 111 | 0 | 4 | 5 | 0 |
| 351 | 111 | 0 | 4 | 5 | 0 |
| 352 | 111 | 0 | 4 | 5 | 0 |
| 353 | 111 | 0 | 4 | 5 | 0 |
| 354 | 111 | 0 | 4 | 5 | 0 |
| 355 | 111 | 0 | 4 | 5 | 0 |
| 356 | 111 | 0 | 4 | 5 | 0 |
| 357 | 111 | 0 | 4 | 5 | 0 |
| 358 | 111 | 0 | 4 | 5 | 0 |
| 359 | 111 | 0 | 4 | 5 | 0 |
| 360 | 111 | 0 | 4 | 5 | 0 |
| 361 | 111 | 0 | 4 | 5 | 0 |
| 362 | 111 | 0 | 4 | 5 | 0 |
| 363 | 111 | 0 | 4 | 5 | 0 |
| 364 | 111 | 0 | 4 | 5 | 0 |
| 365 | 111 | 0 | 4 | 5 | 0 |
| 366 | 111 | 0 | 4 | 5 | 0 |
| 367 | 111 | 0 | 4 | 5 | 0 |
| 368 | 111 | 0 | 4 | 5 | 0 |
| 369 | 111 | 0 | 4 | 5 | 0 |
| 370 | 111 | 0 | 4 | 5 | 0 |
| 371 | 111 | 0 | 4 | 5 | 0 |
| 372 | 111 | 0 | 4 | 5 | 0 |
| 373 | 111 | 0 | 4 | 5 | 0 |
| 374 | 111 | 0 | 4 | 5 | 0 |
| 375 | 111 | 0 | 4 | 5 | 0 |
| 376 | 111 | 0 | 4 | 5 | 0 |
| 377 | 111 | 0 | 4 | 5 | 0 |
| 378 | 111 | 0 | 4 | 5 | 0 |
| 379 | 111 | 0 | 4 | 5 | 0 |
| 380 | 111 | 0 | 4 | 5 | 0 |
| 381 | 111 | 0 | 4 | 5 | 0 |
| 382 | 111 | 0 | 4 | 5 | 0 |
| 383 | 111 | 0 | 4 | 5 | 0 |
| 384 | 111 | 0 | 4 | 5 | 0 |
| 385 | 111 | 0 | 4 | 5 | 0 |
| 386 | 111 | 0 | 4 | 5 | 0 |
| 387 | 111 | 0 | 4 | 5 | 0 |
| 388 | 111 | 0 | 4 | 5 | 0 |
| 389 | 111 | 0 | 4 | 5 | 0 |
| 390 | 111 | 0 | 4 | 5 | 0 |
| 391 | 111 | 0 | 4 | 5 | 0 |
| 392 | 111 | 0 | 4 | 5 | 0 |
| 393 | 111 | 0 | 4 | 5 | 0 |
| 394 | 111 | 0 | 4 | 5 | 0 |
| 395 | 111 | 0 | 4 | 5 | 0 |
| 396 | 111 | 0 | 4 | 5 | 0 |
| 397 | 4 | 0 | 1 | 1 | 0 |
| 398 | 4 | 0 | 1 | 1 | 0 |
