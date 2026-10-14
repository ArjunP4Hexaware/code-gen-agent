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
| PIPELINE_NAME | 100.0 | G1_G2 stage to std load | 3.2 | Pl_File_G3_{table}_Regular_ADLS_To_Delta_Incr | 9.8 | 208 | yes |
| GROUP_ID | 100.0 | withheld (assigned / withheld column) | | | | | |
| SEQ_NM | 100.0 | 1 | 64.6 | 1 | 64.6 | 62 |  |
| PROCESS_NAME | 100.0 | G1  Raw to stage load | 19.6 | G1  Raw to stage load | 19.6 | 107 |  |
| TGT_REFRESH_TYPE | 100.0 | Overwrite | 62.4 | Overwrite | 62.4 | 6 |  |
| ACTIVE_FLAG | 100.0 | Y | 98.9 | Y | 98.9 | 2 |  |
| DATABRICKS_WORKSPACE_URL | 100.0 | withheld (assigned / withheld column) | | | | | |
| DATABRICKS_WORKSPACE_SECRET | 100.0 | withheld (assigned / withheld column) | | | | | |
| DATABRICKS_CLUSTERID | 97.4 | withheld (assigned / withheld column) | | | | | |
| DATABRICKS_NOTEBOOK_PATH | 100.0 | /iig/DeltaInvokeDQStandardDeltaTable_V4 | 26.5 | /iig/DeltaInvokeDQStandardDeltaTable_V4 | 26.5 | 19 |  |
| DATABRICKS_NOTEBOOK_NAME | 100.0 | DeltaInvokeDQStandardDeltaTable_V4 | 29.6 | DeltaInvokeDQStandardDeltaTable_V4 | 29.6 | 15 |  |
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
| PIPELINE_NAME | 100.0 | PL_File_STAGE_G7_G8_extract | 0.5 | Pl_File_G3_{table}_Regular_ADLS_To_Delta_Incr | 8.2 | 376 | yes |
| PARENT_PIPELINE_ID | 92.1 | withheld (assigned / withheld column) | | | | | |
| PIPELINE_DESCRIPTION | 100.0 | G1 Stage Load | 18.9 | G1 Stage Load | 18.9 | 395 |  |
| PIPELINE_FREQUENCY | 100.0 | Daily | 68.5 | Daily | 68.5 | 7 |  |
| NO_OF_CYCLE_PER_DAY | 100.0 | 1 | 98.2 | 1 | 98.2 | 2 |  |
| DAY_OF_SCHEDULE | 3.5 | 0 | 54.8 | 0 | 54.8 | 3 |  |
| ACTIVE_FLAG | 100.0 | Y | 97.5 | Y | 97.5 | 2 |  |
| ACTIVE_START_DATE | 100.0 | 2025-12-20 00:00:00 | 19.4 | 2025-12-20 00:00:00 | 19.4 | 44 |  |
| ACTIVE_END_DATE | 100.0 | 9999-12-31 00:00:00 | 50.0 | 9999-12-31 00:00:00 | 50.0 | 2 |  |
| ESTIMATED_START_TIME | 0.0 |  | - |  | - | 0 |  |
| APPLICATION_NAME | 100.0 | G1 | 38.8 | G1 | 38.8 | 27 |  |
| CREATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| CREATED_DATE | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_DATE | 100.0 | withheld (assigned / withheld column) | | | | | |
| PROCESS_NAME | 60.9 | G3 834 G12 | 59.0 | G3 834 G12 | 56.0 | 33 |  |
| SUBPROCESS_NAME | 53.8 | G2 | 7.6 | G2 | 7.3 | 51 |  |
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
| PIPELINE_NAME | 100.0 | PL_Gmstr_G16_Historical_Load | 7.3 | PL_Gmstr_G16_Historical_Load | 7.3 | 1367 |  |
| TEMPLATE_ID | 100.0 | withheld (assigned / withheld column) | | | | | |
| TEMPLATE_NAME | 19.8 | G21 G22 | 26.1 | G21 G22 | 26.1 | 50 |  |
| PROCESS_NAME | 19.8 | G21 G22 | 26.1 | G21 G22 | 26.1 | 54 |  |
| STATUS | 19.8 | Success | 23.1 | Success | 23.1 | 16 |  |
| ACTIVE_FLAG | 19.8 | Y | 100.0 | Y | 100.0 | 1 |  |
| SUBJECT | 19.8 | G23 G24 G26 Daily File Not Received - | 3.4 | G23 G24 G26 Daily File Not Received - | 3.4 | 162 |  |
| BODY | 19.8 | The G27 files have not been received for the CM Automation. G28 review and take the necessary G29. | 21.7 | The G27 files have not been received for the CM Automation. G28 review and take the necessary G29. | 21.7 | 156 |  |
| SENDER_NAME | 19.8 | dbo | 97.8 | dbo | 97.8 | 2 |  |
| SENDER_EMAIL | 19.8 | G30@<LOCAL_DENYLIST>.G31 | 97.7 | G30@<LOCAL_DENYLIST>.G31 | 97.7 | 5 |  |
| EMAIL_TO | 19.8 | G33@<LOCAL_DENYLIST>.G31 | 47.6 | G33@<LOCAL_DENYLIST>.G31 | 47.6 | 24 |  |
| EMAIL_CC | 18.8 | G35@<LOCAL_DENYLIST>.G31,G36@<LOCAL_DENYLIST>.G31,G37@<LOCAL_DENYLIST>.G31,G38@<LOCAL_DENYLIST>.G31,G39@<LOCAL_DENYLIST>.G31,G40@<LOCAL_DENYLIST>.G31,G41@<LOCAL_DENYLIST>.G31,G42@<LOCAL_DENYLIST>.G31,G43@<LOCAL_DENYLIST>.G31 | 26.7 | G35@<LOCAL_DENYLIST>.G31,G36@<LOCAL_DENYLIST>.G31,G37@<LOCAL_DENYLIST>.G31,G38@<LOCAL_DENYLIST>.G31,G39@<LOCAL_DENYLIST>.G31,G40@<LOCAL_DENYLIST>.G31,G41@<LOCAL_DENYLIST>.G31,G42@<LOCAL_DENYLIST>.G31,G43@<LOCAL_DENYLIST>.G31 | 26.7 | 27 |  |
| CRETAED_BY | 19.8 | withheld (assigned / withheld column) | | | | | |
| CREATED_AT | 19.8 | 2025-12-18 12:30:00 | 25.3 | 2025-12-18 12:30:00 | 25.3 | 36 |  |
| UPDATED_BY | 100.0 | withheld (assigned / withheld column) | | | | | |
| UPDATED_AT | 100.0 | 2026-07-02 15:34:17 | 24.1 | 2026-07-02 15:34:17 | 24.1 | 39 |  |
| EMAIL_NOTIFICATION_URL | 100.0 | https://<REAL_WEBHOOK_HOST>:443/api/LOG_EMAIL_WITH_G49/G50/When_an_G51_request_is_received/G52?api-version=2022-05-01&sp=%G53%G54_an_G51_request_is_received%G55&sv=1.0&G56=G57-G58 | 95.4 | https://<REAL_WEBHOOK_HOST>:443/api/LOG_EMAIL_WITH_G49/G50/When_an_G51_request_is_received/G52?api-version=2022-05-01&sp=%G53%G54_an_G51_request_is_received%G55&sv=1.0&G56=G57-G58 | 95.4 | 3 |  |

## DAY_OF_SCHEDULE by PIPELINE_FREQUENCY (DATA_FACTORY_PIPELINE_SCHEDULE)

| frequency | rows | DAY filled | filled % | dominant DAY | share % |
|---|---|---|---|---|---|
| Daily | 24410 | 0 | 0.0 |  | - |
| Monthly | 8200 | 32 | 0.4 | 5 | 0.2 |
| Weekly | 1592 | 474 | 29.8 | 0 | 14.9 |
| WEEKLY | 1178 | 632 | 53.7 | 0 | 26.8 |
| G71 | 158 | 0 | 0.0 |  | - |
| MONTHLY | 96 | 96 | 100.0 | 0 | 100.0 |
| DAILY | 24 | 24 | 100.0 | 0 | 100.0 |

## DATA_QUALITY_RULES rule classes (RULE_TYPE x RULE_CLASS)

- workbooks with the sheet: 150 of 1255

| RULE_TYPE | RULE_CLASS | rows | workbooks |
|---|---|---|---|
| Predefined | G72 | 186 | 114 |
| STDDelta | LRTrimRule | 180 | 104 |
| Predefined | G73 | 160 | 90 |
| Custom | ReferentialCheckRule | 52 | 16 |
| Predefined | G74 | 38 | 4 |
| Predefined | LoadHeaderAndTrailerToSeparateTablesRule | 36 | 2 |
| STDDelta | DateConversionRule | 34 | 26 |
| STDDelta | DataTypeCastRule | 32 | 28 |
| STDDelta | DateFormatRule | 16 | 10 |
| Predefined | G75 | 10 | 8 |
| Custom | DateFormatRule | 10 | 10 |
| STGDelta | G76 | 8 | 4 |
| STDDelta | G77 | 8 | 6 |
| STDDelta | G78 | 8 | 8 |
| STGDelta | ReferentialCheckRule | 6 | 2 |
| STDDelta | G72 | 6 | 2 |
| STDDelta | G79 | 4 | 4 |
| Custom | G77 | 4 | 4 |
| Custom | DataTypeCastRule | 4 | 4 |
| Predefined | G80 | 2 | 2 |
| STDDelta | G77_NEW | 2 | 2 |

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
