-- metadata_inserts.sql — feed sd_community_demographic_risk
-- TARGET SYSTEM = SQL Server metadata DB (dbo config tables): the rows that DEFINE this feed's tables and pipelines — the client's "DDL" (docs/acfc/MULTI_TABLE_DESIGN.md rule 8). The framework creates the Unity Catalog Delta tables from them; `SD_COMMUNITY_DEMOGRAPHIC_RISK_DDL.txt` is the CREATE reference. It replaces the retired config_inserts_<env>.sql.
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
--   stage    d1_dlk.stg_sdoh.sd_community_demographic_risk — 86 column(s) + 4 audit
--     zip_code String
--     total_population String
--     gender_female_pop String
--     gender_male_pop String
--     gender_female_pct String
--     gender_male_pct String
--     race_white_pop String
--     race_black_pop String
--     race_asian_pop String
--     race_other_alone_pop String
--     race_two_or_more_pop String
--     race_white_pct String
--     race_black_pct String
--     race_asian_pct String
--     race_other_alone_pct String
--     race_two_or_more_pct String
--     ethnicity_hispanic_pop String
--     ethnicity_hispanic_white_pop String
--     ethnicity_hispanic_black_pop String
--     ethnicity_hispanic_other_pop String
--     ethnicity_hispanic_pct String
--     ethnicity_hispanic_white_pct String
--     ethnicity_hispanic_black_pct String
--     ethnicity_hispanic_other_pct String
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
--     age_female_0_17_pct String
--     age_female_18_24_pct String
--     age_female_25_34_pct String
--     age_female_35_44_pct String
--     age_female_45_54_pct String
--     age_female_55_64_pct String
--     age_female_65_74_pct String
--     age_female_75_84_pct String
--     age_female_85_over_pct String
--     age_male_0_17_pct String
--     age_male_18_24_pct String
--     age_male_25_34_pct String
--     age_male_35_44_pct String
--     age_male_45_54_pct String
--     age_male_55_64_pct String
--     age_male_65_74_pct String
--     age_male_75_84_pct String
--     age_male_85_over_pct String
--     language_english_hld String
--     language_spanish_hld String
--     language_other_european_hld String
--     language_asian_hld String
--     language_other_hld String
--     language_english_pct String
--     language_spanish_pct String
--     language_other_european_pct String
--     language_asian_pct String
--     language_other_pct String
--     veteran_pop String
--     veteran_female_pop String
--     veteran_male_pop String
--     veteran_pct String
--     veteran_female_pct String
--     veteran_male_pct String
--     education_no_hs_pop String
--     education_hs_ged_pop String
--     education_some_college_pop String
--     education_college_degree_pop String
--     education_adv_degree_pop String
--     education_no_hs_pct String
--     education_hs_ged_pct String
--     education_some_college_pct String
--     education_college_degree_pct String
--     education_adv_degree_pct String
--     LOB STRING
--     SRC_FILE_NAME STRING
--     REC_CREATION_TIME TIMESTAMP
--     REC_UPDATED_TIME TIMESTAMP
--   standard d1_std.sdoh.sd_community_demographic_risk — 86 column(s) + 4 audit
--     zip_code String
--     total_population String
--     gender_female_pop String
--     gender_male_pop String
--     gender_female_pct DECIMAL(10,2)
--     gender_male_pct DECIMAL(10,2)
--     race_white_pop String
--     race_black_pop String
--     race_asian_pop String
--     race_other_alone_pop String
--     race_two_or_more_pop String
--     race_white_pct DECIMAL(10,2)
--     race_black_pct DECIMAL(10,2)
--     race_asian_pct DECIMAL(10,2)
--     race_other_alone_pct DECIMAL(10,2)
--     race_two_or_more_pct DECIMAL(10,2)
--     ethnicity_hispanic_pop String
--     ethnicity_hispanic_white_pop String
--     ethnicity_hispanic_black_pop String
--     ethnicity_hispanic_other_pop String
--     ethnicity_hispanic_pct DECIMAL(10,2)
--     ethnicity_hispanic_white_pct DECIMAL(10,2)
--     ethnicity_hispanic_black_pct String
--     ethnicity_hispanic_other_pct DECIMAL(10,2)
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
--     age_female_0_17_pct DECIMAL(10,2)
--     age_female_18_24_pct DECIMAL(10,2)
--     age_female_25_34_pct DECIMAL(10,2)
--     age_female_35_44_pct DECIMAL(10,2)
--     age_female_45_54_pct DECIMAL(10,2)
--     age_female_55_64_pct DECIMAL(10,2)
--     age_female_65_74_pct DECIMAL(10,2)
--     age_female_75_84_pct DECIMAL(10,2)
--     age_female_85_over_pct DECIMAL(10,2)
--     age_male_0_17_pct DECIMAL(10,2)
--     age_male_18_24_pct DECIMAL(10,2)
--     age_male_25_34_pct DECIMAL(10,2)
--     age_male_35_44_pct DECIMAL(10,2)
--     age_male_45_54_pct DECIMAL(10,2)
--     age_male_55_64_pct DECIMAL(10,2)
--     age_male_65_74_pct DECIMAL(10,2)
--     age_male_75_84_pct DECIMAL(10,2)
--     age_male_85_over_pct DECIMAL(10,2)
--     language_english_hld String
--     language_spanish_hld String
--     language_other_european_hld String
--     language_asian_hld String
--     language_other_hld String
--     language_english_pct DECIMAL(10,2)
--     language_spanish_pct DECIMAL(10,2)
--     language_other_european_pct DECIMAL(10,2)
--     language_asian_pct DECIMAL(10,2)
--     language_other_pct DECIMAL(10,2)
--     veteran_pop String
--     veteran_female_pop String
--     veteran_male_pop String
--     veteran_pct DECIMAL(10,2)
--     veteran_female_pct String
--     veteran_male_pct DECIMAL(10,2)
--     education_no_hs_pop String
--     education_hs_ged_pop String
--     education_some_college_pop String
--     education_college_degree_pop String
--     education_adv_degree_pop String
--     education_no_hs_pct DECIMAL(10,2)
--     education_hs_ged_pct DECIMAL(10,2)
--     education_some_college_pct DECIMAL(10,2)
--     education_college_degree_pct DECIMAL(10,2)
--     education_adv_degree_pct DECIMAL(10,2)
--     LOB STRING
--     SRC_FILE_NAME STRING
--     REC_CREATION_TIME TIMESTAMP
--     REC_UPDATED_TIME TIMESTAMP

SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRY
BEGIN TRANSACTION;

-- VARIABLES
DECLARE @RFC_NUMBER NVARCHAR(50) = <<RFC_NUMBER>>;  -- the RFC / ATMT ticket: CREATED_BY / UPDATED_BY of every row (§1)
DECLARE @SRC_HOST_NAME NVARCHAR(200) = <<SRC_HOST_NAME>>;  -- platform team: the file connection's host (§3)
DECLARE @SRC_ROOT_PATH NVARCHAR(400) = N'mftlanding\inbound\sdoh\public\socially_determined';  -- the FRD landing path
DECLARE @SRC_CONNECTION_ID INT = NULL;  -- set to reuse a known connection id (FAQ connection_ids); NULL = looked up by host + root path, inserted when absent

-- GUARDS — checked before the first INSERT; any failure aborts the whole script and rolls it back (docs/acfc/METADATA_DB_SEMANTICS.md §1, §2, §5)
IF @RFC_NUMBER IS NULL RAISERROR(N'RFC_NUMBER is not assigned (audit columns, §1)', 16, 1);
IF <<PIPELINE_ID#1>> IS NULL RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 1: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE [PIPELINE_ID] = <<PIPELINE_ID#1>>) RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 1: PIPELINE_ID is already used (unique per process, §2)', 16, 1);
IF <<PIPELINE_ID#2>> IS NULL RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 2: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE [PIPELINE_ID] = <<PIPELINE_ID#2>>) RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 2: PIPELINE_ID is already used (unique per process, §2)', 16, 1);
IF <<PIPELINE_ID#3>> IS NULL RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 3: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE [PIPELINE_ID] = <<PIPELINE_ID#3>>) RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 3: PIPELINE_ID is already used (unique per process, §2)', 16, 1);
IF <<PIPELINE_ID#4>> IS NULL RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 4: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] WHERE [PIPELINE_ID] = <<PIPELINE_ID#4>>) RAISERROR(N'DATA_FACTORY_PIPELINE_SCHEDULE row 4: PIPELINE_ID is already used (unique per process, §2)', 16, 1);
IF <<GROUP_ID#1>> IS NULL RAISERROR(N'FILE_ADLS_INGESTION_DETAILS row 1: GROUP_ID is not assigned', 16, 1);
IF <<OBJECT_ID#1>> IS NULL RAISERROR(N'FILE_ADLS_INGESTION_DETAILS row 1: OBJECT_ID is not assigned', 16, 1);
IF <<PIPELINE_ID#1>> IS NULL RAISERROR(N'FILE_ADLS_INGESTION_DETAILS row 1: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[FILE_ADLS_INGESTION_DETAILS] WHERE [GROUP_ID] = <<GROUP_ID#1>>) RAISERROR(N'FILE_ADLS_INGESTION_DETAILS row 1: GROUP_ID is already used (never reused, §5)', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[FILE_ADLS_INGESTION_DETAILS] WHERE [GROUP_ID] = <<GROUP_ID#1>> AND [OBJECT_ID] = <<OBJECT_ID#1>> AND [PIPELINE_ID] = <<PIPELINE_ID#1>>) RAISERROR(N'FILE_ADLS_INGESTION_DETAILS row 1: the key (GROUP_ID, OBJECT_ID, PIPELINE_ID) is already used (§5, §7)', 16, 1);
IF <<GROUP_ID#1>> IS NULL RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: GROUP_ID is not assigned', 16, 1);
IF <<PIPELINE_ID#1>> IS NULL RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[ADLS_DELTA_INGESTION_DETAILS] WHERE [GROUP_ID] = <<GROUP_ID#1>>) RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: GROUP_ID is already used (never reused, §5)', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[ADLS_DELTA_INGESTION_DETAILS] WHERE [GROUP_ID] = <<GROUP_ID#1>> AND [OBJECT_ID] = N'1' AND [PIPELINE_ID] = <<PIPELINE_ID#1>>) RAISERROR(N'ADLS_DELTA_INGESTION_DETAILS row 1: the key (GROUP_ID, OBJECT_ID, PIPELINE_ID) is already used (§5, §7)', 16, 1);
IF <<GROUP_ID#1>> IS NULL RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: GROUP_ID is not assigned', 16, 1);
IF <<OBJECT_ID#1>> IS NULL RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: OBJECT_ID is not assigned', 16, 1);
IF <<PIPELINE_ID#1>> IS NULL RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: PIPELINE_ID is not assigned', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[STGDELTA_STDDELTA_INGESTION_DET] WHERE [GROUP_ID] = <<GROUP_ID#1>>) RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: GROUP_ID is already used (never reused, §5)', 16, 1);
IF EXISTS (SELECT 1 FROM [dbo].[STGDELTA_STDDELTA_INGESTION_DET] WHERE [GROUP_ID] = <<GROUP_ID#1>> AND [OBJECT_ID] = <<OBJECT_ID#1>> AND [PIPELINE_ID] = <<PIPELINE_ID#1>>) RAISERROR(N'STGDELTA_STDDELTA_INGESTION_DET row 1: the key (GROUP_ID, OBJECT_ID, PIPELINE_ID) is already used (§5, §7)', 16, 1);
-- CONNECTION LOOKUP (§3; table / column identifiers as spoken in the walkthrough — confirm: dml_unconfirmed:connection_table): 0 rows = insert and take its identity, 1 = reuse, more = abort
DECLARE @CONNECTION_MATCHES INT = 0;
SELECT @CONNECTION_MATCHES = COUNT(*) FROM [dbo].[FILE_CONNECTION_DETAILS] WHERE [HOST_NAME] = @SRC_HOST_NAME AND [ROOT_PATH] = @SRC_ROOT_PATH;
IF @CONNECTION_MATCHES > 1 RAISERROR(N'more than one connection matches host + root path (expected 0 or 1)', 16, 1);
IF @SRC_CONNECTION_ID IS NULL AND @SRC_HOST_NAME IS NULL RAISERROR(N'SRC_HOST_NAME is not assigned and no SRC_CONNECTION_ID is given (§3)', 16, 1);
IF @SRC_CONNECTION_ID IS NULL
BEGIN
    SELECT @SRC_CONNECTION_ID = [CONNECTION_ID] FROM [dbo].[FILE_CONNECTION_DETAILS] WHERE [HOST_NAME] = @SRC_HOST_NAME AND [ROOT_PATH] = @SRC_ROOT_PATH;
    IF @SRC_CONNECTION_ID IS NULL
    BEGIN
        INSERT INTO [dbo].[FILE_CONNECTION_DETAILS] ([CONNECTION_DESCRIPTION], [HOST_NAME], [ROOT_PATH], [SOURCE_TYPE], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (CONCAT(N'File connection for ', @SRC_ROOT_PATH), @SRC_HOST_NAME, @SRC_ROOT_PATH, N'File', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());
        SET @SRC_CONNECTION_ID = SCOPE_IDENTITY();
    END
END

-- DATA_FACTORY_PIPELINE_SCHEDULE: 4 row(s)
INSERT INTO [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] ([PIPELINE_ID], [PIPELINE_NAME], [PARENT_PIPELINE_ID], [PIPELINE_DESCRIPTION], [PIPELINE_FREQUENCY], [NO_OF_CYCLE_PER_DAY], [DAY_OF_SCHEDULE], [ACTIVE_FLAG], [ACTIVE_START_DATE], [ACTIVE_END_DATE], [ESTIMATED_START_TIME], [APPLICATION_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<PIPELINE_ID#1>>, N'PL_GMSTR_SD_COMMUNITY_DEMOGRAPHIC_RISK', N'0', N'Grand master', N'Monthly', N'1', NULL, N'S', <<ACTIVE_START_DATE#1>>, N'9999-12-31', NULL, <<APPLICATION_NAME#1>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());
INSERT INTO [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] ([PIPELINE_ID], [PIPELINE_NAME], [PARENT_PIPELINE_ID], [PIPELINE_DESCRIPTION], [PIPELINE_FREQUENCY], [NO_OF_CYCLE_PER_DAY], [DAY_OF_SCHEDULE], [ACTIVE_FLAG], [ACTIVE_START_DATE], [ACTIVE_END_DATE], [ESTIMATED_START_TIME], [APPLICATION_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<PIPELINE_ID#2>>, N'PL_MSTR_SD_COMMUNITY_DEMOGRAPHIC_RISK', <<PARENT_PIPELINE_ID#2>>, N'Master', N'Monthly', N'1', NULL, N'S', <<ACTIVE_START_DATE#2>>, N'9999-12-31', NULL, <<APPLICATION_NAME#2>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());
INSERT INTO [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] ([PIPELINE_ID], [PIPELINE_NAME], [PARENT_PIPELINE_ID], [PIPELINE_DESCRIPTION], [PIPELINE_FREQUENCY], [NO_OF_CYCLE_PER_DAY], [DAY_OF_SCHEDULE], [ACTIVE_FLAG], [ACTIVE_START_DATE], [ACTIVE_END_DATE], [ESTIMATED_START_TIME], [APPLICATION_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<PIPELINE_ID#3>>, N'PL_File_SD_COMMUNITY_DEMOGRAPHIC_RISK_ADLS_To_Delta_Incr', <<PARENT_PIPELINE_ID#3>>, N'File to Stage', N'Monthly', N'1', NULL, N'S', <<ACTIVE_START_DATE#3>>, N'9999-12-31', NULL, <<APPLICATION_NAME#3>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());
INSERT INTO [dbo].[DATA_FACTORY_PIPELINE_SCHEDULE] ([PIPELINE_ID], [PIPELINE_NAME], [PARENT_PIPELINE_ID], [PIPELINE_DESCRIPTION], [PIPELINE_FREQUENCY], [NO_OF_CYCLE_PER_DAY], [DAY_OF_SCHEDULE], [ACTIVE_FLAG], [ACTIVE_START_DATE], [ACTIVE_END_DATE], [ESTIMATED_START_TIME], [APPLICATION_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<PIPELINE_ID#4>>, N'PL_File_SD_COMMUNITY_DEMOGRAPHIC_RISK_Delta_To_STD_Incr', <<PARENT_PIPELINE_ID#4>>, N'Stage to Standard', N'Monthly', N'1', NULL, N'S', <<ACTIVE_START_DATE#4>>, N'9999-12-31', NULL, <<APPLICATION_NAME#4>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());

-- FILE_ADLS_INGESTION_DETAILS: 1 row(s)
INSERT INTO [dbo].[FILE_ADLS_INGESTION_DETAILS] ([GROUP_ID], [OBJECT_ID], [DOMAIN], [SUBDOMAIN], [PIPELINE_ID], [SRC_CONNECTION_ID], [SRC_ROOT_DIR], [TGT_CONTAINER_NAME], [TGT_ADLS_PATH], [SOURCE_TYPE], [SRC_EXTRACT_START_TIME], [COPY_START_TIME_OFFSET_IN_MINUTES], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE], [TGT_STORAGE_ACCOUNT_NAME]) VALUES (<<GROUP_ID#1>>, <<OBJECT_ID#1>>, N'Social Determinants of Health', N'Public', <<PIPELINE_ID#1>>, @SRC_CONNECTION_ID, <<SRC_ROOT_DIR#1>>, <<TGT_CONTAINER_NAME#1>>, N'/mftlanding/inbound/sdoh/public/socially_determined/', N'File', <<SRC_EXTRACT_START_TIME#1>>, N'0', @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE(), <<TGT_STORAGE_ACCOUNT_NAME#1>>);

-- ADLS_DELTA_INGESTION_DETAILS: 1 row(s)
-- table d1_dlk.stg_sdoh.sd_community_demographic_risk <- file demographics_package*
INSERT INTO [dbo].[ADLS_DELTA_INGESTION_DETAILS] ([GROUP_ID], [OBJECT_ID], [OBJECT_NAME], [DOMAIN], [SUBDOMAIN], [PIPELINE_ID], [SOURCE], [FREQUENCY], [LOB], [CLAIM_TYPE_ID], [ACTIVE_FLAG], [SRC_ADLS_CONNECTION_ID], [METADATA_CONNECTION_ID], [SRC_CONTAINER_NAME], [SRC_ADLS_PATH], [SRC_FILE_NAME], [SRC_FORMAT], [SRC_COLUMNS], [SRC_DATA_TYPE], [SRC_FILE_DELIMITER], [SRC_REC_LNGTH], [SRC_COL_LNGTH], [SRC_COL_STRT_END_INDX], [SRC_ADLS_ARCHVL_PATH], [SRC_COMPRESSION], [HEADER_FLAG], [MULTILINE_FLAG], [SCHEMA_DRIFT_FLAG], [FILE_HEADER_FLAG], [FILE_FOOTER_FLAG], [MANDATORY_FIELD_LIST], [TGT_CONNECTION_ID], [TGT_DATABASE_NAME], [TGT_TABLE_NAME], [TGT_CONTAINER_NAME], [TGT_ADLS_PATH], [TGT_COLUMN_NAMES], [TGT_FORMAT], [TGT_DATA_TYPE], [TGT_LOAD_OPTION], [TGT_RJT_TABLE_NAME], [TGT_RJT_ADLS_PATH], [TGT_PARTITION_COLUMN], [TGT_PARTITION_VALUE], [TGT_PRIMARY_KEY], [RECYCL_ENBL_FLG], [RECYCL_TBL_NM], [RECYCL_ADLS_PATH], [RECYCL_RETN_DAYS], [MAPPING_EXPRESSION], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<GROUP_ID#1>>, N'1', N'demographics_package', N'Social Determinants of Health', N'Public', <<PIPELINE_ID#1>>, N'Socially Determined', N'Monthly', N'MIDS', NULL, N'S', N'7', N'4', N'mftlanding', N'/inbound/sdoh/public/socially_determined/', N'demographics_package*', N'csv', N'zip_code:zip_code,total_population:total_population,gender_female_pop:gender_female_pop,gender_male_pop:gender_male_pop,gender_female_pct:gender_female_pct,gender_male_pct:gender_male_pct,race_white_pop:race_white_pop,race_black_pop:race_black_pop,race_asian_pop:race_asian_pop,race_other_alone_pop:race_other_alone_pop,race_two_or_more_pop:race_two_or_more_pop,race_white_pct:race_white_pct,race_black_pct:race_black_pct,race_asian_pct:race_asian_pct,race_other_alone_pct:race_other_alone_pct,race_two_or_more_pct:race_two_or_more_pct,ethnicity_hispanic_pop:ethnicity_hispanic_pop,ethnicity_hispanic_white_pop:ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop:ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop:ethnicity_hispanic_other_pop,ethnicity_hispanic_pct:ethnicity_hispanic_pct,ethnicity_hispanic_white_pct:ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct:ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct:ethnicity_hispanic_other_pct,age_female_0_17_pop:age_female_0_17_pop,age_female_18_24_pop:age_female_18_24_pop,age_female_25_34_pop:age_female_25_34_pop,age_female_35_44_pop:age_female_35_44_pop,age_female_45_54_pop:age_female_45_54_pop,age_female_55_64_pop:age_female_55_64_pop,age_female_65_74_pop:age_female_65_74_pop,age_female_75_84_pop:age_female_75_84_pop,age_female_85_over_pop:age_female_85_over_pop,age_male_0_17_pop:age_male_0_17_pop,age_male_18_24_pop:age_male_18_24_pop,age_male_25_34_pop:age_male_25_34_pop,age_male_35_44_pop:age_male_35_44_pop,age_male_45_54_pop:age_male_45_54_pop,age_male_55_64_pop:age_male_55_64_pop,age_male_65_74_pop:age_male_65_74_pop,age_male_75_84_pop:age_male_75_84_pop,age_male_85_over_pop:age_male_85_over_pop,age_female_0_17_pct:age_female_0_17_pct,age_female_18_24_pct:age_female_18_24_pct,age_female_25_34_pct:age_female_25_34_pct,age_female_35_44_pct:age_female_35_44_pct,age_female_45_54_pct:age_female_45_54_pct,age_female_55_64_pct:age_female_55_64_pct,age_female_65_74_pct:age_female_65_74_pct,age_female_75_84_pct:age_female_75_84_pct,age_female_85_over_pct:age_female_85_over_pct,age_male_0_17_pct:age_male_0_17_pct,age_male_18_24_pct:age_male_18_24_pct,age_male_25_34_pct:age_male_25_34_pct,age_male_35_44_pct:age_male_35_44_pct,age_male_45_54_pct:age_male_45_54_pct,age_male_55_64_pct:age_male_55_64_pct,age_male_65_74_pct:age_male_65_74_pct,age_male_75_84_pct:age_male_75_84_pct,age_male_85_over_pct:age_male_85_over_pct,language_english_hld:language_english_hld,language_spanish_hld:language_spanish_hld,language_other_european_hld:language_other_european_hld,language_asian_hld:language_asian_hld,language_other_hld:language_other_hld,language_english_pct:language_english_pct,language_spanish_pct:language_spanish_pct,language_other_european_pct:language_other_european_pct,language_asian_pct:language_asian_pct,language_other_pct:language_other_pct,veteran_pop:veteran_pop,veteran_female_pop:veteran_female_pop,veteran_male_pop:veteran_male_pop,veteran_pct:veteran_pct,veteran_female_pct:veteran_female_pct,veteran_male_pct:veteran_male_pct,education_no_hs_pop:education_no_hs_pop,education_hs_ged_pop:education_hs_ged_pop,education_some_college_pop:education_some_college_pop,education_college_degree_pop:education_college_degree_pop,education_adv_degree_pop:education_adv_degree_pop,education_no_hs_pct:education_no_hs_pct,education_hs_ged_pct:education_hs_ged_pct,education_some_college_pct:education_some_college_pct,education_college_degree_pct:education_college_degree_pct,education_adv_degree_pct:education_adv_degree_pct', N'String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String', N',', <<SRC_REC_LNGTH#1>>, <<SRC_COL_LNGTH#1>>, <<SRC_COL_STRT_END_INDX#1>>, N'/inbound/sdoh/public/socially_determined/Archive/', N'N', <<HEADER_FLAG#1>>, N'N', N'Y', <<FILE_HEADER_FLAG#1>>, <<FILE_FOOTER_FLAG#1>>, N'zip_code', N'2', N'stg_sdoh', N'sd_community_demographic_risk', N'z-use-d1-dlk-stage-01', N'/sdoh/public/socially_determined/Processed/sd_community_demographic_risk', N'zip_code,total_population,gender_female_pop,gender_male_pop,gender_female_pct,gender_male_pct,race_white_pop,race_black_pop,race_asian_pop,race_other_alone_pop,race_two_or_more_pop,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pop,ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct,age_female_0_17_pop,age_female_18_24_pop,age_female_25_34_pop,age_female_35_44_pop,age_female_45_54_pop,age_female_55_64_pop,age_female_65_74_pop,age_female_75_84_pop,age_female_85_over_pop,age_male_0_17_pop,age_male_18_24_pop,age_male_25_34_pop,age_male_35_44_pop,age_male_45_54_pop,age_male_55_64_pop,age_male_65_74_pop,age_male_75_84_pop,age_male_85_over_pop,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_hld,language_spanish_hld,language_other_european_hld,language_asian_hld,language_other_hld,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pop,veteran_female_pop,veteran_male_pop,veteran_pct,veteran_female_pct,veteran_male_pct,education_no_hs_pop,education_hs_ged_pop,education_some_college_pop,education_college_degree_pop,education_adv_degree_pop,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct,LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME', N'delta', N'String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,Timestamp,Timestamp', N'Overwrite', N'sd_community_demographic_risk_reject', N'/sdoh/public/socially_determined/Reject/sd_community_demographic_risk_reject', N'NA', N'NA', <<TGT_PRIMARY_KEY#1>>, <<RECYCL_ENBL_FLG#1>>, <<RECYCL_TBL_NM#1>>, <<RECYCL_ADLS_PATH#1>>, <<RECYCL_RETN_DAYS#1>>, <<MAPPING_EXPRESSION#1>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());

-- STGDELTA_STDDELTA_INGESTION_DET: 1 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
-- table d1_dlk.stg_sdoh.sd_community_demographic_risk -> d1_std.sdoh.sd_community_demographic_risk
INSERT INTO [dbo].[STGDELTA_STDDELTA_INGESTION_DET] ([GROUP_ID], [OBJECT_ID], [OBJECT_NAME], [DOMAIN], [SUBDOMAIN], [PIPELINE_ID], [SOURCE], [FREQUENCY], [LOB], [ACTIVE_FLAG], [SRC_ADLS_CONNECTION_ID], [METADATA_CONNECTION_ID], [SRC_CONTAINER_NAME], [SRC_ADLS_PATH], [SRC_TABLE_NAME], [SRC_CATALOG_NAME], [SRC_SCHEMA_NAME], [SRC_FORMAT], [SRC_COLUMNS], [SRC_DATA_TYPE], [SRC_ADLS_ARCHVL_PATH], [TGT_CONNECTION_ID], [TGT_CATALOG_NAME], [TGT_SCHEMA_NAME], [TGT_TABLE_NAME], [TGT_CONTAINER_NAME], [TGT_ADLS_PATH], [TGT_COLUMN_NAMES], [TGT_FORMAT], [TGT_DATA_TYPE], [TGT_LOAD_OPTION], [TGT_RJT_TABLE_NAME], [TGT_RJT_ADLS_PATH], [TGT_PARTITION_COLUMN], [TGT_PARTITION_VALUE], [TGT_PRIMARY_KEY], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<GROUP_ID#1>>, <<OBJECT_ID#1>>, N'demographics_package', N'Social Determinants of Health', N'Public', <<PIPELINE_ID#1>>, N'Socially Determined', N'Monthly', N'MIDS', N'S', <<SRC_ADLS_CONNECTION_ID#1>>, <<METADATA_CONNECTION_ID#1>>, <<SRC_CONTAINER_NAME#1>>, N'/mftlanding/inbound/sdoh/public/socially_determined/Processed/', N'sd_community_demographic_risk', N'd1_dlk', N'stg_sdoh', N'delta', N'zip_code:zip_code,total_population:total_population,gender_female_pop:gender_female_pop,gender_male_pop:gender_male_pop,gender_female_pct:gender_female_pct,gender_male_pct:gender_male_pct,race_white_pop:race_white_pop,race_black_pop:race_black_pop,race_asian_pop:race_asian_pop,race_other_alone_pop:race_other_alone_pop,race_two_or_more_pop:race_two_or_more_pop,race_white_pct:race_white_pct,race_black_pct:race_black_pct,race_asian_pct:race_asian_pct,race_other_alone_pct:race_other_alone_pct,race_two_or_more_pct:race_two_or_more_pct,ethnicity_hispanic_pop:ethnicity_hispanic_pop,ethnicity_hispanic_white_pop:ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop:ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop:ethnicity_hispanic_other_pop,ethnicity_hispanic_pct:ethnicity_hispanic_pct,ethnicity_hispanic_white_pct:ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct:ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct:ethnicity_hispanic_other_pct,age_female_0_17_pop:age_female_0_17_pop,age_female_18_24_pop:age_female_18_24_pop,age_female_25_34_pop:age_female_25_34_pop,age_female_35_44_pop:age_female_35_44_pop,age_female_45_54_pop:age_female_45_54_pop,age_female_55_64_pop:age_female_55_64_pop,age_female_65_74_pop:age_female_65_74_pop,age_female_75_84_pop:age_female_75_84_pop,age_female_85_over_pop:age_female_85_over_pop,age_male_0_17_pop:age_male_0_17_pop,age_male_18_24_pop:age_male_18_24_pop,age_male_25_34_pop:age_male_25_34_pop,age_male_35_44_pop:age_male_35_44_pop,age_male_45_54_pop:age_male_45_54_pop,age_male_55_64_pop:age_male_55_64_pop,age_male_65_74_pop:age_male_65_74_pop,age_male_75_84_pop:age_male_75_84_pop,age_male_85_over_pop:age_male_85_over_pop,age_female_0_17_pct:age_female_0_17_pct,age_female_18_24_pct:age_female_18_24_pct,age_female_25_34_pct:age_female_25_34_pct,age_female_35_44_pct:age_female_35_44_pct,age_female_45_54_pct:age_female_45_54_pct,age_female_55_64_pct:age_female_55_64_pct,age_female_65_74_pct:age_female_65_74_pct,age_female_75_84_pct:age_female_75_84_pct,age_female_85_over_pct:age_female_85_over_pct,age_male_0_17_pct:age_male_0_17_pct,age_male_18_24_pct:age_male_18_24_pct,age_male_25_34_pct:age_male_25_34_pct,age_male_35_44_pct:age_male_35_44_pct,age_male_45_54_pct:age_male_45_54_pct,age_male_55_64_pct:age_male_55_64_pct,age_male_65_74_pct:age_male_65_74_pct,age_male_75_84_pct:age_male_75_84_pct,age_male_85_over_pct:age_male_85_over_pct,language_english_hld:language_english_hld,language_spanish_hld:language_spanish_hld,language_other_european_hld:language_other_european_hld,language_asian_hld:language_asian_hld,language_other_hld:language_other_hld,language_english_pct:language_english_pct,language_spanish_pct:language_spanish_pct,language_other_european_pct:language_other_european_pct,language_asian_pct:language_asian_pct,language_other_pct:language_other_pct,veteran_pop:veteran_pop,veteran_female_pop:veteran_female_pop,veteran_male_pop:veteran_male_pop,veteran_pct:veteran_pct,veteran_female_pct:veteran_female_pct,veteran_male_pct:veteran_male_pct,education_no_hs_pop:education_no_hs_pop,education_hs_ged_pop:education_hs_ged_pop,education_some_college_pop:education_some_college_pop,education_college_degree_pop:education_college_degree_pop,education_adv_degree_pop:education_adv_degree_pop,education_no_hs_pct:education_no_hs_pct,education_hs_ged_pct:education_hs_ged_pct,education_some_college_pct:education_some_college_pct,education_college_degree_pct:education_college_degree_pct,education_adv_degree_pct:education_adv_degree_pct,LOB:LOB,SRC_FILE_NAME:SRC_FILE_NAME,REC_CREATION_TIME:REC_CREATION_TIME,REC_UPDATED_TIME:REC_UPDATED_TIME', N'String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:String,String:Decimal,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:String,String:String,String:String,String:Decimal,String:String,String:Decimal,String:String,String:String,String:String,String:String,String:String,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:Decimal,String:String,String:String,Timestamp:Timestamp,Timestamp:Timestamp', N'/Archive/mftlanding/inbound/sdoh/public/socially_determined/', <<TGT_CONNECTION_ID#1>>, N'd1_std', N'sdoh', N'sd_community_demographic_risk', <<TGT_CONTAINER_NAME#1>>, N'/mftlanding/inbound/sdoh/public/socially_determined/Processed/sd_community_demographic_risk', N'zip_code,total_population,gender_female_pop,gender_male_pop,gender_female_pct,gender_male_pct,race_white_pop,race_black_pop,race_asian_pop,race_other_alone_pop,race_two_or_more_pop,race_white_pct,race_black_pct,race_asian_pct,race_other_alone_pct,race_two_or_more_pct,ethnicity_hispanic_pop,ethnicity_hispanic_white_pop,ethnicity_hispanic_black_pop,ethnicity_hispanic_other_pop,ethnicity_hispanic_pct,ethnicity_hispanic_white_pct,ethnicity_hispanic_black_pct,ethnicity_hispanic_other_pct,age_female_0_17_pop,age_female_18_24_pop,age_female_25_34_pop,age_female_35_44_pop,age_female_45_54_pop,age_female_55_64_pop,age_female_65_74_pop,age_female_75_84_pop,age_female_85_over_pop,age_male_0_17_pop,age_male_18_24_pop,age_male_25_34_pop,age_male_35_44_pop,age_male_45_54_pop,age_male_55_64_pop,age_male_65_74_pop,age_male_75_84_pop,age_male_85_over_pop,age_female_0_17_pct,age_female_18_24_pct,age_female_25_34_pct,age_female_35_44_pct,age_female_45_54_pct,age_female_55_64_pct,age_female_65_74_pct,age_female_75_84_pct,age_female_85_over_pct,age_male_0_17_pct,age_male_18_24_pct,age_male_25_34_pct,age_male_35_44_pct,age_male_45_54_pct,age_male_55_64_pct,age_male_65_74_pct,age_male_75_84_pct,age_male_85_over_pct,language_english_hld,language_spanish_hld,language_other_european_hld,language_asian_hld,language_other_hld,language_english_pct,language_spanish_pct,language_other_european_pct,language_asian_pct,language_other_pct,veteran_pop,veteran_female_pop,veteran_male_pop,veteran_pct,veteran_female_pct,veteran_male_pct,education_no_hs_pop,education_hs_ged_pop,education_some_college_pop,education_college_degree_pop,education_adv_degree_pop,education_no_hs_pct,education_hs_ged_pct,education_some_college_pct,education_college_degree_pct,education_adv_degree_pct,LOB,SRC_FILE_NAME,REC_CREATION_TIME,REC_UPDATED_TIME', N'delta', N'String,String,String,String,Decimal(10,2),Decimal(10,2),String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),String,String,String,String,Decimal(10,2),Decimal(10,2),String,Decimal(10,2),String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),String,String,String,Decimal(10,2),String,Decimal(10,2),String,String,String,String,String,Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),Decimal(10,2),String,String,Timestamp,Timestamp', N'Append', N'sd_community_demographic_risk_reject', N'/mftlanding/inbound/sdoh/public/socially_determined/Processed/sd_community_demographic_risk_reject', N'NA', N'NA', <<TGT_PRIMARY_KEY#1>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());

-- ADLS_FIXED_WIDTH_HANDLER: 0 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only

-- DATA_QUALITY_RULES: 0 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only

-- DATABRICKS_NOTEBOOK_DETAILS: 1 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
INSERT INTO [dbo].[DATABRICKS_NOTEBOOK_DETAILS] ([PIPELINE_ID], [PIPELINE_NAME], [GROUP_ID], [SEQ_NM], [PROCESS_NAME], [TGT_REFRESH_TYPE], [ACTIVE_FLAG], [DATABRICKS_WORKSPACE_URL], [DATABRICKS_WORKSPACE_SECRET], [DATABRICKS_CLUSTERID], [DATABRICKS_NOTEBOOK_PATH], [DATABRICKS_NOTEBOOK_NAME], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE], [CLUSTER_DETAILS_ID], [DELETE_DATABRICKS_NOTEBOOK_NAME], [DQ_NOTEBOOK_PATH]) VALUES (<<PIPELINE_ID#1>>, <<PIPELINE_NAME#1>>, <<GROUP_ID#1>>, N'1', <<PROCESS_NAME#1>>, N'Overwrite', N'S', <<DATABRICKS_WORKSPACE_URL#1>>, <<DATABRICKS_WORKSPACE_SECRET#1>>, <<DATABRICKS_CLUSTERID#1>>, <<DATABRICKS_NOTEBOOK_PATH#1>>, <<DATABRICKS_NOTEBOOK_NAME#1>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE(), <<CLUSTER_DETAILS_ID#1>>, <<DELETE_DATABRICKS_NOTEBOOK_NAME#1>>, <<DQ_NOTEBOOK_PATH#1>>);

-- EMAIL_TEMPLATE_CONFIG: 2 row(s) — table not yet described in the framework walkthrough (docs/acfc/METADATA_DB_SEMANTICS.md §8); §1 conventions only
INSERT INTO [dbo].[EMAIL_TEMPLATE_CONFIG] ([TEMPLATE_ID], [TEMPLATE_NAME], [PROCESS_NAME], [STATUS], [ACTIVE_FLAG], [SUBJECT], [BODY], [BODY_QUERY], [SENDER_NAME], [SENDER_EMAIL], [EMAIL_TO], [EMAIL_CC], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<TEMPLATE_ID#1>>, <<TEMPLATE_NAME#1>>, <<PROCESS_NAME#1>>, N'Success', N'S', <<SUBJECT#1>>, <<BODY#1>>, <<BODY_QUERY#1>>, <<SENDER_NAME#1>>, <<SENDER_EMAIL#1>>, N'syn.dl.prodsupport@synthetic.example', <<EMAIL_CC#1>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());
INSERT INTO [dbo].[EMAIL_TEMPLATE_CONFIG] ([TEMPLATE_ID], [TEMPLATE_NAME], [PROCESS_NAME], [STATUS], [ACTIVE_FLAG], [SUBJECT], [BODY], [BODY_QUERY], [SENDER_NAME], [SENDER_EMAIL], [EMAIL_TO], [EMAIL_CC], [CREATED_BY], [CREATED_DATE], [UPDATED_BY], [UPDATED_DATE]) VALUES (<<TEMPLATE_ID#2>>, <<TEMPLATE_NAME#2>>, <<PROCESS_NAME#2>>, N'Failed', N'S', <<SUBJECT#2>>, <<BODY#2>>, <<BODY_QUERY#2>>, <<SENDER_NAME#2>>, <<SENDER_EMAIL#2>>, N'syn.dl.prodsupport@synthetic.example', <<EMAIL_CC#2>>, @RFC_NUMBER, GETDATE(), @RFC_NUMBER, GETDATE());

COMMIT TRANSACTION;
END TRY
BEGIN CATCH
IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
THROW;
END CATCH;
