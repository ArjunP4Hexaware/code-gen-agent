-- metadata_inserts.sql — feed sd_community_demographic_risk
-- TARGET SYSTEM = SQL Server metadata DB (dbo config tables): the rows that DEFINE this feed's tables and pipelines — the client's "DDL" (docs/acfc/MULTI_TABLE_DESIGN.md rule 8). The framework creates the Unity Catalog Delta tables from them; `sd_community_demographic_risk_stage_table_creation.txt / sd_community_demographic_risk_standard_table_creation.txt` is the CREATE reference. It replaces the retired config_inserts_<env>.sql.
-- SOURCE = the same cells as the IIG workbook (config_rows.xlsx / the clean IIG copy), with the DB values below; nothing else is derived.
-- <<COLUMN#n>> = an OPEN cell (row n of that sheet): replace every one before running — the script does not parse until then. NULL = a cell decided blank.
-- RUN = one transaction: any guard or insert that fails rolls back everything.
-- FRD contract: FRD feed contract extracted from FRD_Medicare Expansion-MIDS - Socially Determined.docx sha256 1f720e92f5e30ce794d8572c8dc1b91f807d5db0151f427f4861624a4b34e4d2
-- STTM contract: STTM mapping contract extracted from STTM_Medicare Expansion-MIDS - Socially Determined.xlsx sha256 4f654e1701bb46e308379987fee80a912dd40f25bf21f56ebf55f33da4da559b
-- Load-pattern FAQ: sha256 defaults (no FAQ file) — 2 answered, 6 unknown
-- Engineering standards: EDO Data Engineering Naming + Coding Standards (received 2026-08-26)
-- WORKBOOK -> DATABASE — three rules (docs/acfc/METADATA_DB_SEMANTICS.md; config dml.*). The IIG workbook keeps what humans hand over; this script writes what the framework reads. Every other cell is the workbook's value as is.
--   RULE 1 — value map (dml.db_value_map): a workbook value the database spells differently
--     ACTIVE_FLAG: workbook 'Y' -> 'S' (the goldens print 'Y', §1 says the framework selects 'S' — UNCONFIRMED, Friday checklist 9)
--     ACTIVE_RULE_FLG: workbook 'Y' -> 'S' (the same assumption as ACTIVE_FLAG — UNCONFIRMED, Friday checklist 9)
--   RULE 2 — forced NULL (dml.db_null_columns): columns the framework fills itself / does not use today, NULL whatever the workbook holds (§2 'not populating … future purpose', §7): DAY_OF_SCHEDULE, UDF2, UDF3, UDF4, UDF5, ESTIMATED_START_TIME, COMPLETION_SLA, RUNTIME_SLA, CRITICAL_PROCESSING_PERIOD, CLAIM_TYPE_ID
--     DAY_OF_SCHEDULE: the pair-1 golden prints 0, §2 / §10 say NULL — UNCONFIRMED, Friday checklist 10
--   RULE 3 — audit defaults and open cells: CREATED_DATE blank -> GETDATE(); UPDATED_DATE blank -> GETDATE(); CREATED_BY / UPDATED_BY blank -> @RFC_NUMBER (§1); FILE_ADLS_INGESTION_DETAILS.SRC_CONNECTION_ID blank -> @SRC_CONNECTION_ID (§3); any other OPEN cell -> its <<COLUMN#n>> placeholder (fill before running); a cell decided blank -> NULL

-- TABLE DEFINITIONS — every table this feed defines (one per distinct stage catalog.schema.table), by its MAPPED three-part name; reference only: the framework creates the Unity Catalog Delta tables from the rows below.
-- table 1 of 1 (segments: Detail)
--   stage    stg_sdoh.sd_community_demographic_risk — 86 column(s) + 4 audit
--     zip_code STRING
--     total_population STRING
--     gender_female_pop STRING
--     gender_male_pop STRING
--     gender_female_pct STRING
--     gender_male_pct STRING
--     race_white_pop STRING
--     race_black_pop STRING
--     race_asian_pop STRING
--     race_other_alone_pop STRING
--     race_two_or_more_pop STRING
--     race_white_pct STRING
--     race_black_pct STRING
--     race_asian_pct STRING
--     race_other_alone_pct STRING
--     race_two_or_more_pct STRING
--     ethnicity_hispanic_pop STRING
--     ethnicity_hispanic_white_pop STRING
--     ethnicity_hispanic_black_pop STRING
--     ethnicity_hispanic_other_pop STRING
--     ethnicity_hispanic_pct STRING
--     ethnicity_hispanic_white_pct STRING
--     ethnicity_hispanic_black_pct STRING
--     ethnicity_hispanic_other_pct STRING
--     age_female_0_17_pop STRING
--     age_female_18_24_pop STRING
--     age_female_25_34_pop STRING
--     age_female_35_44_pop STRING
--     age_female_45_54_pop STRING
--     age_female_55_64_pop STRING
--     age_female_65_74_pop STRING
--     age_female_75_84_pop STRING
--     age_female_85_over_pop STRING
--     age_male_0_17_pop STRING
--     age_male_18_24_pop STRING
--     age_male_25_34_pop STRING
--     age_male_35_44_pop STRING
--     age_male_45_54_pop STRING
--     age_male_55_64_pop STRING
--     age_male_65_74_pop STRING
--     age_male_75_84_pop STRING
--     age_male_85_over_pop STRING
--     age_female_0_17_pct STRING
--     age_female_18_24_pct STRING
--     age_female_25_34_pct STRING
--     age_female_35_44_pct STRING
--     age_female_45_54_pct STRING
--     age_female_55_64_pct STRING
--     age_female_65_74_pct STRING
--     age_female_75_84_pct STRING
--     age_female_85_over_pct STRING
--     age_male_0_17_pct STRING
--     age_male_18_24_pct STRING
--     age_male_25_34_pct STRING
--     age_male_35_44_pct STRING
--     age_male_45_54_pct STRING
--     age_male_55_64_pct STRING
--     age_male_65_74_pct STRING
--     age_male_75_84_pct STRING
--     age_male_85_over_pct STRING
--     language_english_hld STRING
--     language_spanish_hld STRING
--     language_other_european_hld STRING
--     language_asian_hld STRING
--     language_other_hld STRING
--     language_english_pct STRING
--     language_spanish_pct STRING
--     language_other_european_pct STRING
--     language_asian_pct STRING
--     language_other_pct STRING
--     veteran_pop STRING
--     veteran_female_pop STRING
--     veteran_male_pop STRING
--     veteran_pct STRING
--     veteran_female_pct STRING
--     veteran_male_pct STRING
--     education_no_hs_pop STRING
--     education_hs_ged_pop STRING
--     education_some_college_pop STRING
--     education_college_degree_pop STRING
--     education_adv_degree_pop STRING
--     education_no_hs_pct STRING
--     education_hs_ged_pct STRING
--     education_some_college_pct STRING
--     education_college_degree_pct STRING
--     education_adv_degree_pct STRING
--     LOB String
--     SRC_FILE_NAME String
--     REC_CREATION_TIME Timestamp
--     REC_UPDATED_TIME Timestamp
--   standard sdoh.sd_community_demographic_risk — 86 column(s) + 4 audit
--     zip_code String
--     total_population String
--     gender_female_pop String
--     gender_male_pop String
--     gender_female_pct Decimal(10,2)
--     gender_male_pct Decimal(10,2)
--     race_white_pop String
--     race_black_pop String
--     race_asian_pop String
--     race_other_alone_pop String
--     race_two_or_more_pop String
--     race_white_pct Decimal(10,2)
--     race_black_pct Decimal(10,2)
--     race_asian_pct Decimal(10,2)
--     race_other_alone_pct Decimal(10,2)
--     race_two_or_more_pct Decimal(10,2)
--     ethnicity_hispanic_pop String
--     ethnicity_hispanic_white_pop String
--     ethnicity_hispanic_black_pop String
--     ethnicity_hispanic_other_pop String
--     ethnicity_hispanic_pct Decimal(10,2)
--     ethnicity_hispanic_white_pct Decimal(10,2)
--     ethnicity_hispanic_black_pct String
--     ethnicity_hispanic_other_pct Decimal(10,2)
--     age_female_0_17_pop String
--     age_female_18_24_pop String
--     age_female_25_34_pop String
--     age_female_35_44_pop String
--     age_female_45_54_pop String
--     age_female_55_64_pop String
--     age_female_65_74_pop String
--     age_female_75_84_pop String
--     age_female_85_over_pop String
--     age_male_0_17_pop String
--     age_male_18_24_pop String
--     age_male_25_34_pop String
--     age_male_35_44_pop String
--     age_male_45_54_pop String
--     age_male_55_64_pop String
--     age_male_65_74_pop String
--     age_male_75_84_pop String
--     age_male_85_over_pop String
--     age_female_0_17_pct Decimal(10,2)
--     age_female_18_24_pct Decimal(10,2)
--     age_female_25_34_pct Decimal(10,2)
--     age_female_35_44_pct Decimal(10,2)
--     age_female_45_54_pct Decimal(10,2)
--     age_female_55_64_pct Decimal(10,2)
--     age_female_65_74_pct Decimal(10,2)
--     age_female_75_84_pct Decimal(10,2)
--     age_female_85_over_pct Decimal(10,2)
--     age_male_0_17_pct Decimal(10,2)
--     age_male_18_24_pct Decimal(10,2)
--     age_male_25_34_pct Decimal(10,2)
--     age_male_35_44_pct Decimal(10,2)
--     age_male_45_54_pct Decimal(10,2)
--     age_male_55_64_pct Decimal(10,2)
--     age_male_65_74_pct Decimal(10,2)
--     age_male_75_84_pct Decimal(10,2)
--     age_male_85_over_pct Decimal(10,2)
--     language_english_hld String
--     language_spanish_hld String
--     language_other_european_hld String
--     language_asian_hld String
--     language_other_hld String
--     language_english_pct Decimal(10,2)
--     language_spanish_pct Decimal(10,2)
--     language_other_european_pct Decimal(10,2)
--     language_asian_pct Decimal(10,2)
--     language_other_pct Decimal(10,2)
--     veteran_pop String
--     veteran_female_pop String
--     veteran_male_pop String
--     veteran_pct Decimal(10,2)
--     veteran_female_pct String
--     veteran_male_pct Decimal(10,2)
--     education_no_hs_pop String
--     education_hs_ged_pop String
--     education_some_college_pop String
--     education_college_degree_pop String
--     education_adv_degree_pop String
--     education_no_hs_pct Decimal(10,2)
--     education_hs_ged_pct Decimal(10,2)
--     education_some_college_pct Decimal(10,2)
--     education_college_degree_pct Decimal(10,2)
--     education_adv_degree_pct Decimal(10,2)
--     LOB String
--     SRC_FILE_NAME String
--     REC_CREATION_TIME Timestamp
--     REC_UPDATED_TIME Timestamp

SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
BEGIN TRANSACTION;

-- VARIABLES
DECLARE @RFC_NUMBER NVARCHAR(50) = <<RFC_NUMBER>>;  -- the RFC / ATMT ticket: CREATED_BY / UPDATED_BY of every row (§1)

-- GUARDS — checked before the first INSERT; any failure aborts the whole script and rolls it back (docs/acfc/METADATA_DB_SEMANTICS.md §1, §2, §5)
IF @RFC_NUMBER IS NULL RAISERROR(N'RFC_NUMBER is not assigned (audit columns, §1)', 16, 1);
IF <<PIPELINE_ID#1>> IS NULL RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 1: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE [PIPELINE_ID] = <<PIPELINE_ID#1>>) RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 1: PIPELINE_ID is already used (unique per process, §2)', 16, 1);
IF <<PIPELINE_ID#2>> IS NULL RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 2: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE [PIPELINE_ID] = <<PIPELINE_ID#2>>) RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 2: PIPELINE_ID is already used (unique per process, §2)', 16, 1);
IF <<GROUP_ID#1>> IS NULL RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: GROUP_ID is not assigned', 16, 1);
IF <<OBJECT_ID#1>> IS NULL RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: OBJECT_ID is not assigned', 16, 1);
IF <<PIPELINE_ID#1>> IS NULL RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[ADLS_DELTA_INGESTION_DETAILS] WHERE [GROUP_ID] = <<GROUP_ID#1>>) RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: GROUP_ID is already used (never reused, §5)', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[ADLS_DELTA_INGESTION_DETAILS] WHERE [GROUP_ID] = <<GROUP_ID#1>> AND [OBJECT_ID] = <<OBJECT_ID#1>> AND [PIPELINE_ID] = <<PIPELINE_ID#1>>) RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: the key (GROUP_ID, OBJECT_ID, PIPELINE_ID) is already used (§5, §7)', 16, 1);
IF <<GROUP_ID#1>> IS NULL RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: GROUP_ID is not assigned', 16, 1);
IF <<OBJECT_ID#1>> IS NULL RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: OBJECT_ID is not assigned', 16, 1);
IF <<PIPELINE_ID#1>> IS NULL RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[STGDELTA_STDDELTA_INGESTION_DET] WHERE [GROUP_ID] = <<GROUP_ID#1>>) RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: GROUP_ID is already used (never reused, §5)', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[STGDELTA_STDDELTA_INGESTION_DET] WHERE [GROUP_ID] = <<GROUP_ID#1>> AND [OBJECT_ID] = <<OBJECT_ID#1>> AND [PIPELINE_ID] = <<PIPELINE_ID#1>>) RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: the key (GROUP_ID, OBJECT_ID, PIPELINE_ID) is already used (§5, §7)', 16, 1);

-- DATA_FACTORY_PIPELINE_SCHEDULE: 2 row(s)
INSERT INTO [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] ([PIPELINE_ID], [PIPELINE_NAME], [PARENT_PIPELINE_ID], [PIPELINE_DESCRIPTION], [PIPELINE_FREQUENCY], [NO_OF_CYCLE_PER_DAY], [DAY_OF_SCHEDULE], [ACTIVE_FLAG], [ACTIVE_START_DATE], [ACTIVE_END_DATE], [ESTIMATED_START_TIME], [APPLICATION_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE], [PROCESS_NAME], [SUBPROCESS_NAME], [LAYER_NAME], [COMPLETION_SLA], [RUNTIME_SLA], [CRITICAL_PROCESSING_PERIOD], [UDF1], [UDF2], [UDF3], [UDF4], [UDF5], [IsFileCopyReqFlag]) VALUES (<<PIPELINE_ID#1>>, N'WF_DLK_NSP_SD_COMMUNITY_DEMOGRAPHIC_RISK_SOCIAL_DETERMINANTS_OF_HEALTH_PUBLIC_MIDS_YRL', <<PARENT_PIPELINE_ID#1>>, N'sd_community_demographic_risk ingestion (stage)', N'Yearly Twice', <<NO_OF_CYCLE_PER_DAY#1>>, NULL, N'S', <<ACTIVE_START_DATE#1>>, N'9999-12-31', NULL, N'Socially Determined – SD 33732', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE(), N'sd_community_demographic_risk', <<SUBPROCESS_NAME#1>>, N'STAGE', NULL, NULL, NULL, <<UDF1#1>>, NULL, NULL, NULL, NULL, <<IsFileCopyReqFlag#1>>);
INSERT INTO [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] ([PIPELINE_ID], [PIPELINE_NAME], [PARENT_PIPELINE_ID], [PIPELINE_DESCRIPTION], [PIPELINE_FREQUENCY], [NO_OF_CYCLE_PER_DAY], [DAY_OF_SCHEDULE], [ACTIVE_FLAG], [ACTIVE_START_DATE], [ACTIVE_END_DATE], [ESTIMATED_START_TIME], [APPLICATION_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE], [PROCESS_NAME], [SUBPROCESS_NAME], [LAYER_NAME], [COMPLETION_SLA], [RUNTIME_SLA], [CRITICAL_PROCESSING_PERIOD], [UDF1], [UDF2], [UDF3], [UDF4], [UDF5], [IsFileCopyReqFlag]) VALUES (<<PIPELINE_ID#2>>, N'WF_DLK_NSP_SD_COMMUNITY_DEMOGRAPHIC_RISK_SOCIAL_DETERMINANTS_OF_HEALTH_PUBLIC_MIDS_YRL', <<PARENT_PIPELINE_ID#2>>, N'sd_community_demographic_risk ingestion (standard)', N'Yearly Twice', <<NO_OF_CYCLE_PER_DAY#2>>, NULL, N'S', <<ACTIVE_START_DATE#2>>, N'9999-12-31', NULL, N'Socially Determined – SD 33732', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE(), N'sd_community_demographic_risk', <<SUBPROCESS_NAME#2>>, N'STANDARD', NULL, NULL, NULL, <<UDF1#2>>, NULL, NULL, NULL, NULL, <<IsFileCopyReqFlag#2>>);

-- ADLS_DELTA_INGESTION_DETAILS: 1 row(s)
-- table stg_sdoh.sd_community_demographic_risk <- file demographics_package_YYYY_MM.csv
INSERT INTO [dbo].[ADLS_DELTA_INGESTION_DETAILS] ([GROUP_ID], [OBJECT_ID], [OBJECT_NAME], [DOMAIN], [SUBDOMAIN], [PIPELINE_ID], [SOURCE], [FREQUENCY], [LOB], [CLAIM_TYPE_ID], [ACTIVE_FLAG], [SRC_ADLS_CONNECTION_ID], [METADATA_CONNECTION_ID], [SRC_CONTAINER_NAME], [SRC_ADLS_PATH], [SRC_FILE_NAME], [SRC_FORMAT], [SRC_COLUMNS], [SRC_DATA_TYPE], [SRC_FILE_DELIMITER], [SRC_REC_LNGTH], [SRC_COL_LNGTH], [SRC_COL_STRT_END_INDX], [SRC_ADLS_ARCHVL_PATH], [SRC_COMPRESSION], [HEADER_FLAG], [MULTILINE_FLAG], [SCHEMA_DRIFT_FLAG], [FILE_HEADER_FLAG], [FILE_FOOTER_FLAG], [MANDATORY_FIELD_LIST], [TGT_CONNECTION_ID], [TGT_DATABASE_NAME], [TGT_TABLE_NAME], [TGT_CONTAINER_NAME], [TGT_ADLS_PATH], [TGT_COLUMN_NAMES], [TGT_FORMAT], [TGT_DATA_TYPE], [TGT_LOAD_OPTION], [TGT_RJT_TABLE_NAME], [TGT_RJT_ADLS_PATH], [TGT_PARTITION_COLUMN], [TGT_PARTITION_VALUE], [TGT_PRIMARY_KEY], [RECYCL_ENBL_FLG], [RECYCL_TBL_NM], [RECYCL_ADLS_PATH], [RECYCL_RETN_DAYS], [MAPPING_EXPRESSION], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE], [FILE_METADATA]) VALUES (<<GROUP_ID#1>>, <<OBJECT_ID#1>>, N'sd_community_demographic_risk', N'Social Determinants of Health', N'Public', <<PIPELINE_ID#1>>, N'Socially Determined – SD 33732', N'Yearly Twice', N'MIDS', NULL, <<ACTIVE_FLAG#1>>, <<SRC_ADLS_CONNECTION_ID#1>>, <<METADATA_CONNECTION_ID#1>>, N'mftlanding', N'/inbound/sdoh/public/socially_determined', N'demographics_package_YYYY_MM.csv', N'File Data Ingestion', N'zip_code:zip_code,total_population:total_population,gender_female_pop:gender_female_pop,gender_male_pop:gender_male_pop,gender_female_pct:gender_female_pct,gender_male_pct:gender_male_pct,race_white_pop:race_white_pop,race_black_pop:race_black_pop,race_asian_pop:race_asian_pop,race_other_alone_pop:race_other_alone_pop,race_two_or_more_pop:race_two_or_more_pop,race_white_pct:race_white_pct,race_black_pct:race_black_pct,race_asian_pct:race_asian_pct,race_other_alone_pct:race_other_alone_pct,race_two_or_more_pct:race_two_or_more_pct,ethnicity_hispanic_pop:ethnicity_hispanic_pop,ethnicity_hispanic_white_pop:ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop:ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop:ethnicity_hispanic_other_pop,ethnicity_hispanic_pct:ethnicity_hispanic_pct,ethnicity_hispanic_white_pct:ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct:ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct:ethnicity_hispanic_other_pct,age_female_0_17_pop:age_female_0_17_pop,age_female_18_24_pop:age_female_18_24_pop,age_female_25_34_pop:age_female_25_34_pop,age_female_35_44_pop:age_female_35_44_pop,age_female_45_54_pop:age_female_45_54_pop,age_female_55_64_pop:age_female_55_64_pop,age_female_65_74_pop:age_female_65_74_pop,age_female_75_84_pop:age_female_75_84_pop,age_female_85_over_pop:age_female_85_over_pop,age_male_0_17_pop:age_male_0_17_pop,age_male_18_24_pop:age_male_18_24_pop,age_male_25_34_pop:age_male_25_34_pop,age_male_35_44_pop:age_male_35_44_pop,age_male_45_54_pop:age_male_45_54_pop,age_male_55_64_pop:age_male_55_64_pop,age_male_65_74_pop:age_male_65_74_pop,age_male_75_84_pop:age_male_75_84_pop,age_male_85_over_pop:age_male_85_over_pop,age_female_0_17_pct:age_female_0_17_pct,age_female_18_24_pct:age_female_18_24_pct,age_female_25_34_pct:age_female_25_34_pct,age_female_35_44_pct:age_female_35_44_pct,age_female_45_54_pct:age_female_45_54_pct,age_female_55_64_pct:age_female_55_64_pct,age_female_65_74_pct:age_female_65_74_pct,age_female_75_84_pct:age_female_75_84_pct,age_female_85_over_pct:age_female_85_over_pct,age_male_0_17_pct:age_male_0_17_pct,age_male_18_24_pct:age_male_18_24_pct,age_male_25_34_pct:age_male_25_34_pct,age_male_35_44_pct:age_male_35_44_pct,age_male_45_54_pct:age_male_45_54_pct,age_male_55_64_pct:age_male_55_64_pct,age_male_65_74_pct:age_male_65_74_pct,age_male_75_84_pct:age_male_75_84_pct,age_male_85_over_pct:age_male_85_over_pct,language_english_hld:language_english_hld,language_spanish_hld:language_spanish_hld,language_other_european_hld:language_other_european_hld,language_asian_hld:language_asian_hld,language_other_hld:language_other_hld,language_english_pct:language_english_pct,language_spanish_pct:language_spanish_pct,language_other_european_pct:language_other_european_pct,language_asian_pct:language_asian_pct,language_other_pct:language_other_pct,veteran_pop:veteran_pop,veteran_female_pop:veteran_female_pop,veteran_male_pop:veteran_male_pop,veteran_pct:veteran_pct,veteran_female_pct:veteran_female_pct,veteran_male_pct:veteran_male_pct,education_no_hs_pop:education_no_hs_pop,education_hs_ged_pop:education_hs_ged_pop,education_some_college_pop:education_some_college_pop,education_college_degree_pop:education_college_degree_pop,education_adv_degree_pop:education_adv_degree_pop,education_no_hs_pct:education_no_hs_pct,education_hs_ged_pct:education_hs_ged_pct,education_some_college_pct:education_some_college_pct,education_college_degree_pct:education_college_degree_pct,education_adv_degree_pct:education_adv_degree_pct', N'String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String', N',', <<SRC_REC_LNGTH#1>>, <<SRC_COL_LNGTH#1>>, <<SRC_COL_STRT_END_INDX#1>>, <<SRC_ADLS_ARCHVL_PATH#1>>, <<SRC_COMPRESSION#1>>, <<HEADER_FLAG#1>>, <<MULTILINE_FLAG#1>>, <<SCHEMA_DRIFT_FLAG#1>>, <<FILE_HEADER_FLAG#1>>, <<FILE_FOOTER_FLAG#1>>, N'zip_code', <<TGT_CONNECTION_ID#1>>, N'stg_sdoh', N'sd_community_demographic_risk', <<TGT_CONTAINER_NAME#1>>, N'/SOCIAL_DETERMINANTS_OF_HEALTH/PUBLIC/Processed/sd_community_demographic_risk', N'zip_code,total_population,gender_female_pop,gender_male_pop,gender_female_pct,gender_male_pct,race_white_pop,race_black_pop,race_asian_pop,race_other_alone_pop,race_two_or_more_pop,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pop,ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct,age_female_0_17_pop,age_female_18_24_pop,age_female_25_34_pop,age_female_35_44_pop,age_female_45_54_pop,age_female_55_64_pop,age_female_65_74_pop,age_female_75_84_pop,age_female_85_over_pop,age_male_0_17_pop,age_male_18_24_pop,age_male_25_34_pop,age_male_35_44_pop,age_male_45_54_pop,age_male_55_64_pop,age_male_65_74_pop,age_male_75_84_pop,age_male_85_over_pop,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_hld,language_spanish_hld,language_other_european_hld,language_asian_hld,language_other_hld,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pop,veteran_female_pop,veteran_male_pop,veteran_pct,veteran_female_pct,veteran_male_pct,education_no_hs_pop,education_hs_ged_pop,education_some_college_pop,education_college_degree_pop,education_adv_degree_pop,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct', N'delta', N'String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String', N'Truncate and Load', N'sd_community_demographic_risk_errors', <<TGT_RJT_ADLS_PATH#1>>, <<TGT_PARTITION_COLUMN#1>>, <<TGT_PARTITION_VALUE#1>>, N'zip_code', N'N', <<RECYCL_TBL_NM#1>>, <<RECYCL_ADLS_PATH#1>>, <<RECYCL_RETN_DAYS#1>>, <<MAPPING_EXPRESSION#1>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE(), <<FILE_METADATA#1>>);

-- STGDELTA_STDDELTA_INGESTION_DET: 1 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
-- table ?.stg_sdoh.sd_community_demographic_risk -> ?.sdoh.sd_community_demographic_risk
INSERT INTO [dbo].[STGDELTA_STDDELTA_INGESTION_DET] ([GROUP_ID], [OBJECT_ID], [OBJECT_NAME], [DOMAIN], [SUBDOMAIN], [PIPELINE_ID], [SOURCE], [FREQUENCY], [LOB], [ACTIVE_FLAG], [SRC_ADLS_CONNECTION_ID], [METADATA_CONNECTION_ID], [SRC_CONTAINER_NAME], [SRC_ADLS_PATH], [SRC_TABLE_NAME], [SRC_CATALOG_NAME], [SRC_SCHEMA_NAME], [SRC_FORMAT], [SRC_COLUMNS], [SRC_DATA_TYPE], [SRC_ADLS_ARCHVL_PATH], [TGT_CONNECTION_ID], [TGT_CATALOG_NAME], [TGT_SCHEMA_NAME], [TGT_TABLE_NAME], [TGT_CONTAINER_NAME], [TGT_ADLS_PATH], [TGT_COLUMN_NAMES], [TGT_FORMAT], [TGT_DATA_TYPE], [TGT_LOAD_OPTION], [TGT_RJT_TABLE_NAME], [TGT_RJT_ADLS_PATH], [TGT_PARTITION_COLUMN], [TGT_PARTITION_VALUE], [TGT_PRIMARY_KEY], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<GROUP_ID#1>>, <<OBJECT_ID#1>>, N'sd_community_demographic_risk', N'Social Determinants of Health', N'Public', <<PIPELINE_ID#1>>, N'Socially Determined – SD 33732', N'Yearly Twice', N'MIDS', <<ACTIVE_FLAG#1>>, <<SRC_ADLS_CONNECTION_ID#1>>, <<METADATA_CONNECTION_ID#1>>, <<SRC_CONTAINER_NAME#1>>, <<SRC_ADLS_PATH#1>>, N'sd_community_demographic_risk', <<SRC_CATALOG_NAME#1>>, N'stg_sdoh', N'delta', N'zip_code:zip_code,total_population:total_population,gender_female_pop:gender_female_pop,gender_male_pop:gender_male_pop,gender_female_pct:gender_female_pct,gender_male_pct:gender_male_pct,race_white_pop:race_white_pop,race_black_pop:race_black_pop,race_asian_pop:race_asian_pop,race_other_alone_pop:race_other_alone_pop,race_two_or_more_pop:race_two_or_more_pop,race_white_pct:race_white_pct,race_black_pct:race_black_pct,race_asian_pct:race_asian_pct,race_other_alone_pct:race_other_alone_pct,race_two_or_more_pct:race_two_or_more_pct,ethnicity_hispanic_pop:ethnicity_hispanic_pop,ethnicity_hispanic_white_pop:ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop:ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop:ethnicity_hispanic_other_pop,ethnicity_hispanic_pct:ethnicity_hispanic_pct,ethnicity_hispanic_white_pct:ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct:ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct:ethnicity_hispanic_other_pct,age_female_0_17_pop:age_female_0_17_pop,age_female_18_24_pop:age_female_18_24_pop,age_female_25_34_pop:age_female_25_34_pop,age_female_35_44_pop:age_female_35_44_pop,age_female_45_54_pop:age_female_45_54_pop,age_female_55_64_pop:age_female_55_64_pop,age_female_65_74_pop:age_female_65_74_pop,age_female_75_84_pop:age_female_75_84_pop,age_female_85_over_pop:age_female_85_over_pop,age_male_0_17_pop:age_male_0_17_pop,age_male_18_24_pop:age_male_18_24_pop,age_male_25_34_pop:age_male_25_34_pop,age_male_35_44_pop:age_male_35_44_pop,age_male_45_54_pop:age_male_45_54_pop,age_male_55_64_pop:age_male_55_64_pop,age_male_65_74_pop:age_male_65_74_pop,age_male_75_84_pop:age_male_75_84_pop,age_male_85_over_pop:age_male_85_over_pop,age_female_0_17_pct:age_female_0_17_pct,age_female_18_24_pct:age_female_18_24_pct,age_female_25_34_pct:age_female_25_34_pct,age_female_35_44_pct:age_female_35_44_pct,age_female_45_54_pct:age_female_45_54_pct,age_female_55_64_pct:age_female_55_64_pct,age_female_65_74_pct:age_female_65_74_pct,age_female_75_84_pct:age_female_75_84_pct,age_female_85_over_pct:age_female_85_over_pct,age_male_0_17_pct:age_male_0_17_pct,age_male_18_24_pct:age_male_18_24_pct,age_male_25_34_pct:age_male_25_34_pct,age_male_35_44_pct:age_male_35_44_pct,age_male_45_54_pct:age_male_45_54_pct,age_male_55_64_pct:age_male_55_64_pct,age_male_65_74_pct:age_male_65_74_pct,age_male_75_84_pct:age_male_75_84_pct,age_male_85_over_pct:age_male_85_over_pct,language_english_hld:language_english_hld,language_spanish_hld:language_spanish_hld,language_other_european_hld:language_other_european_hld,language_asian_hld:language_asian_hld,language_other_hld:language_other_hld,language_english_pct:language_english_pct,language_spanish_pct:language_spanish_pct,language_other_european_pct:language_other_european_pct,language_asian_pct:language_asian_pct,language_other_pct:language_other_pct,veteran_pop:veteran_pop,veteran_female_pop:veteran_female_pop,veteran_male_pop:veteran_male_pop,veteran_pct:veteran_pct,veteran_female_pct:veteran_female_pct,veteran_male_pct:veteran_male_pct,education_no_hs_pop:education_no_hs_pop,education_hs_ged_pop:education_hs_ged_pop,education_some_college_pop:education_some_college_pop,education_college_degree_pop:education_college_degree_pop,education_adv_degree_pop:education_adv_degree_pop,education_no_hs_pct:education_no_hs_pct,education_hs_ged_pct:education_hs_ged_pct,education_some_college_pct:education_some_college_pct,education_college_degree_pct:education_college_degree_pct,education_adv_degree_pct:education_adv_degree_pct', N'String:String,String:String,String:String,String:String,String:Decimal(10,2),String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:String,String:String,String:String,String:String,String:Decimal(10,2),String:Decimal(10,2),String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:String,String:String,String:String,String:Decimal(10,2),String:String,String:Decimal(10,2),String:String,String:String,String:String,String:String,String:String,String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2),String:Decimal(10,2)', <<SRC_ADLS_ARCHVL_PATH#1>>, <<TGT_CONNECTION_ID#1>>, <<TGT_CATALOG_NAME#1>>, N'sdoh', N'sd_community_demographic_risk', <<TGT_CONTAINER_NAME#1>>, <<TGT_ADLS_PATH#1>>, N'zip_code,total_population,gender_female_pop,gender_male_pop,gender_female_pct,gender_male_pct,race_white_pop,race_black_pop,race_asian_pop,race_other_alone_pop,race_two_or_more_pop,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pop,ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct,age_female_0_17_pop,age_female_18_24_pop,age_female_25_34_pop,age_female_35_44_pop,age_female_45_54_pop,age_female_55_64_pop,age_female_65_74_pop,age_female_75_84_pop,age_female_85_over_pop,age_male_0_17_pop,age_male_18_24_pop,age_male_25_34_pop,age_male_35_44_pop,age_male_45_54_pop,age_male_55_64_pop,age_male_65_74_pop,age_male_75_84_pop,age_male_85_over_pop,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_hld,language_spanish_hld,language_other_european_hld,language_asian_hld,language_other_hld,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pop,veteran_female_pop,veteran_male_pop,veteran_pct,veteran_female_pct,veteran_male_pct,education_no_hs_pop,education_hs_ged_pop,education_some_college_pop,education_college_degree_pop,education_adv_degree_pop,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct', N'delta', N'String,String,String,String,Decimal(10,2),Decimal(10,2),String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),String,String,String,String,Decimal(10,2),Decimal(10,2),String,Decimal(10,2),String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),String,String,String,Decimal(10,2),String,Decimal(10,2),String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2)', N'Append', <<TGT_RJT_TABLE_NAME#1>>, <<TGT_RJT_ADLS_PATH#1>>, <<TGT_PARTITION_COLUMN#1>>, <<TGT_PARTITION_VALUE#1>>, N'zip_code', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());

-- DATA_QUALITY_RULES: 2 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
INSERT INTO [dbo].[DATA_QUALITY_RULES] ([GROUP_ID], [OBJECT_ID], [SEQUENCE_NO], [RULE_TYPE], [RULE_CLASS], [ACTIVE_RULE_FLG], [SOURCE_COLUMN], [INPUT_PARAM], [TARGET_COLUMN], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<GROUP_ID#1>>, <<OBJECT_ID#1>>, N'1', N'Predefined', N'CheckRule', N'S', N'zip_code', <<INPUT_PARAM#1>>, N'zip_code', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());
INSERT INTO [dbo].[DATA_QUALITY_RULES] ([GROUP_ID], [OBJECT_ID], [SEQUENCE_NO], [RULE_TYPE], [RULE_CLASS], [ACTIVE_RULE_FLG], [SOURCE_COLUMN], [INPUT_PARAM], [TARGET_COLUMN], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<GROUP_ID#2>>, <<OBJECT_ID#2>>, N'2', N'STDDelta', N'LRTrimRule', N'S', N'zip_code,total_population,gender_female_pop,gender_male_pop,gender_female_pct,gender_male_pct,race_white_pop,race_black_pop,race_asian_pop,race_other_alone_pop,race_two_or_more_pop,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pop,ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct,age_female_0_17_pop,age_female_18_24_pop,age_female_25_34_pop,age_female_35_44_pop,age_female_45_54_pop,age_female_55_64_pop,age_female_65_74_pop,age_female_75_84_pop,age_female_85_over_pop,age_male_0_17_pop,age_male_18_24_pop,age_male_25_34_pop,age_male_35_44_pop,age_male_45_54_pop,age_male_55_64_pop,age_male_65_74_pop,age_male_75_84_pop,age_male_85_over_pop,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_hld,language_spanish_hld,language_other_european_hld,language_asian_hld,language_other_hld,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pop,veteran_female_pop,veteran_male_pop,veteran_pct,veteran_female_pct,veteran_male_pct,education_no_hs_pop,education_hs_ged_pop,education_some_college_pop,education_college_degree_pop,education_adv_degree_pop,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct', <<INPUT_PARAM#2>>, N'zip_code,total_population,gender_female_pop,gender_male_pop,gender_female_pct,gender_male_pct,race_white_pop,race_black_pop,race_asian_pop,race_other_alone_pop,race_two_or_more_pop,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pop,ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct,age_female_0_17_pop,age_female_18_24_pop,age_female_25_34_pop,age_female_35_44_pop,age_female_45_54_pop,age_female_55_64_pop,age_female_65_74_pop,age_female_75_84_pop,age_female_85_over_pop,age_male_0_17_pop,age_male_18_24_pop,age_male_25_34_pop,age_male_35_44_pop,age_male_45_54_pop,age_male_55_64_pop,age_male_65_74_pop,age_male_75_84_pop,age_male_85_over_pop,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_hld,language_spanish_hld,language_other_european_hld,language_asian_hld,language_other_hld,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pop,veteran_female_pop,veteran_male_pop,veteran_pct,veteran_female_pct,veteran_male_pct,education_no_hs_pop,education_hs_ged_pop,education_some_college_pop,education_college_degree_pop,education_adv_degree_pop,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());

-- DATABRICKS_NOTEBOOK_DETAILS: 2 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
INSERT INTO [dbo].[DATABRICKS_NOTEBOOK_DETAILS] ([PIPELINE_ID], [PIPELINE_NAME], [GROUP_ID], [SEQ_NM], [PROCESS_NAME], [TGT_REFRESH_TYPE], [ACTIVE_FLAG], [DATABRICKS_WORKSPACE_URL], [DATABRICKS_WORKSPACE_SECRET], [DATABRICKS_CLUSTERID], [DATABRICKS_NOTEBOOK_PATH], [DATABRICKS_NOTEBOOK_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE], [CLUSTER_DETAILS_ID], [DQ_NOTEBOOK_PATH], [DELETE_DATABRICKS_NOTEBOOK_NAME]) VALUES (<<PIPELINE_ID#1>>, N'WF_DLK_NSP_SD_COMMUNITY_DEMOGRAPHIC_RISK_SOCIAL_DETERMINANTS_OF_HEALTH_PUBLIC_MIDS_YRL', <<GROUP_ID#1>>, N'1', N'Stage Load for sd_community_demographic_risk', N'Overwrite', N'S', <<DATABRICKS_WORKSPACE_URL#1>>, <<DATABRICKS_WORKSPACE_SECRET#1>>, <<DATABRICKS_CLUSTERID#1>>, <<DATABRICKS_NOTEBOOK_PATH#1>>, N'NB_DLK_NSP_SOCIAL_DETERMINANTS_OF_HEALTH_PUBLIC_INGEST', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE(), <<CLUSTER_DETAILS_ID#1>>, <<DQ_NOTEBOOK_PATH#1>>, <<DELETE_DATABRICKS_NOTEBOOK_NAME#1>>);
INSERT INTO [dbo].[DATABRICKS_NOTEBOOK_DETAILS] ([PIPELINE_ID], [PIPELINE_NAME], [GROUP_ID], [SEQ_NM], [PROCESS_NAME], [TGT_REFRESH_TYPE], [ACTIVE_FLAG], [DATABRICKS_WORKSPACE_URL], [DATABRICKS_WORKSPACE_SECRET], [DATABRICKS_CLUSTERID], [DATABRICKS_NOTEBOOK_PATH], [DATABRICKS_NOTEBOOK_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE], [CLUSTER_DETAILS_ID], [DQ_NOTEBOOK_PATH], [DELETE_DATABRICKS_NOTEBOOK_NAME]) VALUES (<<PIPELINE_ID#2>>, N'WF_DLK_NSP_SD_COMMUNITY_DEMOGRAPHIC_RISK_SOCIAL_DETERMINANTS_OF_HEALTH_PUBLIC_MIDS_YRL', <<GROUP_ID#2>>, N'2', N'Standard Load for sd_community_demographic_risk', N'Append', N'S', <<DATABRICKS_WORKSPACE_URL#2>>, <<DATABRICKS_WORKSPACE_SECRET#2>>, <<DATABRICKS_CLUSTERID#2>>, <<DATABRICKS_NOTEBOOK_PATH#2>>, N'NB_DLK_NSP_SOCIAL_DETERMINANTS_OF_HEALTH_PUBLIC_INGEST', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE(), <<CLUSTER_DETAILS_ID#2>>, <<DQ_NOTEBOOK_PATH#2>>, <<DELETE_DATABRICKS_NOTEBOOK_NAME#2>>);

-- EMAIL_TEMPLATE_CONFIG: 2 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
INSERT INTO [dbo].[EMAIL_TEMPLATE_CONFIG] ([TEMPLATE_NAME], [PROCESS_NAME], [STATUS], [ACTIVE_FLAG], [SUBJECT], [BODY], [SENDER_NAME], [SENDER_EMAIL], [EMAIL_TO], [EMAIL_CC], [CRETAED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [EMAIL_NOTIFICATION_URL]) VALUES (N'sd_community_demographic_risk', N'sd_community_demographic_risk', N'Success', N'S', N'sd_community_demographic_risk Load Success', <<BODY#1>>, <<SENDER_NAME#1>>, <<SENDER_EMAIL#1>>, N'syn.dl.prodsupport@synthetic.example', <<EMAIL_CC#1>>, @RFC_NUMBER, <<CREATED_AT#1>>, @RFC_NUMBER, <<UPDATED_AT#1>>, <<EMAIL_NOTIFICATION_URL#1>>);
INSERT INTO [dbo].[EMAIL_TEMPLATE_CONFIG] ([TEMPLATE_NAME], [PROCESS_NAME], [STATUS], [ACTIVE_FLAG], [SUBJECT], [BODY], [SENDER_NAME], [SENDER_EMAIL], [EMAIL_TO], [EMAIL_CC], [CRETAED_BY], [CREATED_AT], [UPDATED_BY], [UPDATED_AT], [EMAIL_NOTIFICATION_URL]) VALUES (N'sd_community_demographic_risk', N'sd_community_demographic_risk', N'Failed', N'S', N'sd_community_demographic_risk Load Failed', <<BODY#2>>, <<SENDER_NAME#2>>, <<SENDER_EMAIL#2>>, N'syn.dl.prodsupport@synthetic.example', <<EMAIL_CC#2>>, @RFC_NUMBER, <<CREATED_AT#2>>, @RFC_NUMBER, <<UPDATED_AT#2>>, <<EMAIL_NOTIFICATION_URL#2>>);

-- ALL_FILES_STATIC_INFORMATION: 1 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
INSERT INTO [dbo].[ALL_FILES_STATIC_INFORMATION] ([INVENTORY_ID], [OBJECT_ID], [FILE_NAME], [DESCRIPTION], [LOB], [GOVT_PROGRAM_NM], [FILE_TYPE], [SUPPLIER], [SUPPLIER_CONTACT_PH], [SUPPLIER_EMAIL], [GENERATOR], [GENERATOR_CONTACT_PH], [GENERATOR_EMAIL], [FREQUENCY], [ACTIVE_TERM_STATUS], [INTERNAL_CONTACT_NM], [INTERNAL_CONTACT_EMAIL], [LAST_SUCCESS_PROCESSED_DATE], [NEXT_EXPECTED_RECEIVE_DT], [FILE_RECEIVE_PER_FREQUENCY], [PROCESS_NAME], [FILE_TR_MODE], [domain], [subdomain], [vendor_name], [CREATED_DATE], [UPDATED_DATE]) VALUES (<<INVENTORY_ID#1>>, <<OBJECT_ID#1>>, N'demographics_package_YYYY_MM.csv', N'sd_community_demographic_risk', N'MIDS', <<GOVT_PROGRAM_NM#1>>, N'File Data Ingestion', N'Socially Determined – SD 33732', <<SUPPLIER_CONTACT_PH#1>>, <<SUPPLIER_EMAIL#1>>, <<GENERATOR#1>>, <<GENERATOR_CONTACT_PH#1>>, <<GENERATOR_EMAIL#1>>, N'Yearly Twice', N'Y', <<INTERNAL_CONTACT_NM#1>>, <<INTERNAL_CONTACT_EMAIL#1>>, <<LAST_SUCCESS_PROCESSED_DATE#1>>, <<NEXT_EXPECTED_RECEIVE_DT#1>>, <<FILE_RECEIVE_PER_FREQUENCY#1>>, N'sd_community_demographic_risk', <<FILE_TR_MODE#1>>, N'Social Determinants of Health', N'Public', N'Socially Determined – SD 33732', GETDATE(), GETDATE());

COMMIT TRANSACTION;
END TRY
BEGIN CATCH
IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
THROW;
END CATCH;
