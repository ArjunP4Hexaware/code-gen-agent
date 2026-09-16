# ACCEPTANCE inputs — the synthetic pairs every case uses

Everything here is synthetic. `Pair` = one FRD contract + one STTM workbook (+ optional FAQ files). The workbooks are given sheet by sheet as CSV (the row order, header spellings, blank spacer columns and whitespace are part of the input); rebuild each sheet cell-for-cell. FRD contracts are given as field tables: `(null)` is an absent value, `(empty list)` an empty list, ` ; ` separates list items, and `[n]` numbers the validation rules. Feed identifiers are slug(feed_name).

Configuration: the acceptance values of SPEC 0.1 (in particular the landing-root template `syn-landing/inbound/{domain}/{sub_domain}/{source_system}`, the standards status `Client Data Engineering Naming + Coding Standards`, the notification list `syn.dl.prodsupport@synthetic.example`, the synthetic LOCATION prefix, the segmented member reference table `syn_member_ref`); mock Layer 2; tests skipped; contract generated_date `2026-01-01`.

## Pair A — flat workbook, two feeds (`syn_widget_frd` + `syn_widget_sttm.xlsx`)

FRD contract `syn_widget_frd` (contract-level fields):

| Contract field | Value |
|---|---|
| contract_name | syn_widget_frd |
| generated_from_frd | syn_widget_frd.docx |
| generated_date | 2026-01-01T00:00:00 |
| generator | synthetic-kit |
| status | PASS |
| project.project_id / project_name / business_context_summary | SYN-0001 / Synthetic Widget Ingestion / (null) |
| in_scope | (empty list) |
| out_of_scope | (empty list) |
| assumptions_constraints_dependencies | (empty list) |
| system_interfaces | (empty list) |
| open_items | (empty list) |

Feed 1 of 2:

| Feed field | Value |
|---|---|
| feed_name | Syn Widget Risk |
| source_system | SynVendor Analytics |
| file_name_patterns | widget_risk_CCYYMMDD.csv ; widget_risk_YYYYMMDD.csv |
| file_format | csv |
| delimiter | (null) |
| record_segments | (empty list) |
| frequency | Monthly Run; file received by the fifth business day |
| load_windows_sla | File received by the fifth business day of each month |
| lobs | Region 5 |
| domain | Member |
| sub_domain | Widgets |
| landing_location | syn-landing\inbound\member\widgets\synvendor |
| stage_target.catalog | (null) |
| stage_target.schema | stg_syn |
| stage_target.tables | syn_widget_risk |
| stage_target.load_strategy | Truncate and Load |
| standard_target.catalog | (null) |
| standard_target.schema | syn |
| standard_target.tables | syn_widget_risk |
| standard_target.load_strategy | Append |
| validation_rules | [1] If the WIDGET_ID column is NULL, reject the record and move it to the reject table. |
| recycle_rule | (null) |
| history_backfill | (null) |
| archive_retention | (null) |
| phi_pii_notes | (null) |
| sttm_reference | (null) |
| requirement_ids | (empty list) |

Feed 2 of 2:

| Feed field | Value |
|---|---|
| feed_name | Syn Gadget Events |
| source_system | SynVendor Analytics |
| file_name_patterns | gadget_events_CCYYMMDD_HHMM.psv |
| file_format | psv |
| delimiter | \| |
| record_segments | (empty list) |
| frequency | Weekly Monday 8 PM |
| load_windows_sla | Weekly Monday 8 PM |
| lobs | Region 1 ; Region 2 |
| domain | Claims |
| sub_domain | Gadget Events |
| landing_location | (null) |
| stage_target.catalog | (null) |
| stage_target.schema | stg_syn |
| stage_target.tables | syn_gadget_events ; syn_gadget_events_recycle |
| stage_target.load_strategy | Truncate and Load |
| standard_target.catalog | (null) |
| standard_target.schema | syn |
| standard_target.tables | syn_gadget_events |
| standard_target.load_strategy | Upsert |
| validation_rules | [1] Process shall fail when file layout is not as per source dictionary. ; [2] Duplicate file name check shall be turned off for this feed. ; [3] Email notification should be sent to the Support team whenever there is an issue. ; [4] Column GADGET_NM is mapped to GADGET_NAME in the standard layer. ; [5] Records failing the reference check are moved to the recycle table. |
| recycle_rule | Recycle Flag (Enabled for 10 Days) Y (Check with GADGET_KEY from GadgetMaster in the SYN_STD.GADGETS.GDG_MASTER FOR GRP_CD = 9, If available, process it else load this to the Recycle Table with Recycle Flag Enabled for 10 days.) |
| history_backfill | (null) |
| archive_retention | (null) |
| phi_pii_notes | (null) |
| sttm_reference | (null) |
| requirement_ids | (empty list) |


Sheet `FILE_DETAILS` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
Vendor,FileName,File Description,Location,Frequency
SynVendor Analytics,widget_risk_YYYYMMDD.csv,,,Monthly
SynVendor Analytics,gadget_events_YYYYMMDD_HHMM.psv,,,Weekly
```

Sheet `VERSION_HISTORY` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
Date,Version,Author(s),Description of Version/Changes
2026-01-05,1.0,Synthetic Author,Initial draft
2026-01-20,1.1,Synthetic Author,Added gadget events
```

Sheet `MAPPING-SYN_WIDGET_RISK` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
Source File Layout,,,,,,,Stage Layer,,,,,Standard Layer,,,
Database column Name,NULL CHECK,Description,Sample Value,DataType,PHI Field ,Mandatory Field,Schema,TableName,ColumnName,DataType,,Schema,TableName,ColumnName,DataType
widget_id,Not NULL,Widget identifier,W-0001,String,No,Yes,stg_syn,syn_widget_risk,widget_id,String,,syn,syn_widget_risk,widget_id,String
widget_color,NULL ,Widget color name,Blue,String,No,No,stg_syn,syn_widget_risk,widget_color,String,,syn,syn_widget_risk,widget_color,String
risk_score,NULL,Widget risk score,2.5,String,No,No,stg_syn,syn_widget_risk,risk_score,String,,syn,syn_widget_risk,risk_score,"Decimal(10,2)"
measured_on,NULL,Measurement date,2026-01-15,Date,No,No,stg_syn,syn_widget_risk,measured_on,String,,syn,syn_widget_risk,measured_on,Date
owner_ref,NULL,Owner reference code,OWN-0007,String,Yes,No,stg_syn,syn_widget_risk,owner_ref,String,,syn,syn_widget_risk,owner_ref,String
NA,NULL,NA,NA,NA,No,No,stg_syn,syn_widget_risk,LOB,string,,syn,syn_widget_risk,LOB,string
NA,NULL,NA,NA,NA,No,No,stg_syn,syn_widget_risk,SRC_FILE_NAME,string,,syn,syn_widget_risk,SRC_FILE_NAME,string
NA,NULL,NA,NA,NA,No,No,stg_syn,syn_widget_risk,REC_CREATION_TIME,timestamp,,syn,syn_widget_risk,REC_CREATION_TIME,timestamp
NA,NULL,NA,NA,NA,No,No,stg_syn,syn_widget_risk,REC_UPDATED_TIME,timestamp,,syn,syn_widget_risk,REC_UPDATED_TIME,timestamp
```

Cells carrying deliberate leading/trailing whitespace (kept exactly; the parser normalizes them): F2: 'PHI Field ', B4: 'NULL '

Sheet `MAPPING-SYN_GADGET_EVENTS` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
Source File Layout,,,,,,,,Stage Layer,,,,,Standard Layer,,,,
Client Data Table Column Name,Description,Comment,Example Values,Data Type,NULL Check,PHI/PII Field,Mandatory,Schema,TableName,ColumnName,DataType,,Schema,TableName,ColumnName,DataType,Recycle Flag ( Enabled for 10 Days)
gadget_key,Gadget key,string,G-100,String,Not NULL,No,Yes,stg_syn,syn_gadget_events,gadget_key,String,,syn,syn_gadget_events,gadget_key,String,"Recycle Flag ( Enabled for 10 Days)
Y ( Check with GADGET_KEY from GadgetMaster in the SYN_STD.GADGETS.GDG_MASTER FOR GRP_CD = 9, if available process it else load this to the Recycle Table with Recycle Flag Enabled for 10 days.)"
event_ts,Event timestamp,"timestamp, UTC",2026-01-15 09:00:00,Timestamp,Not NULL,No,Yes,stg_syn,syn_gadget_events,event_ts,String,,syn,syn_gadget_events,event_ts,Timestamp,
gadget_owner,Gadget's owner name,string,Synthetic Owner,String,NULL,Yes,No,stg_syn,syn_gadget_events,gadget_owner,String,,syn,syn_gadget_events,gadget_owner,String,
gadget_nm,Gadget name,string,Sprocket,String,NULL,No,No,stg_syn,syn_gadget_events,gadget_nm,String,,syn,syn_gadget_events,gadget_name,String,
event_count,Events in window,integer or null,12,Int,NULL,No,No,stg_syn,syn_gadget_events,event_count,String,,syn,syn_gadget_events,event_count,Int,
amount,"Event amount
in local currency",decimal,10.50,"Decimal(12,2)",NULL,No,No,stg_syn,syn_gadget_events,amount,String,,syn,syn_gadget_events,amount,"Decimal(12,2)",
is_active,Active flag,boolean,true,Boolean,NULL,No,No,stg_syn,syn_gadget_events,is_active,String,,syn,syn_gadget_events,is_active,Boolean,
big_ref,Large reference number,bigint,9007199254740993,BigInt,NULL,No,No,stg_syn,syn_gadget_events,big_ref,String,,syn,syn_gadget_events,big_ref,BigInt,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,LOB,string,,syn,syn_gadget_events,LOB,string,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,SRC_FILE_NAME,string,,syn,syn_gadget_events,SRC_FILE_NAME,string,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,REC_CREATION_TIME,timestamp,,syn,syn_gadget_events,REC_CREATION_TIME,timestamp,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,REC_UPDATED_TIME,timestamp,,syn,syn_gadget_events,REC_UPDATED_TIME,timestamp,
```

FAQ file `syn_widget_risk.faq.yaml` (key: value block; each answer is a nested mapping):

```text
schema_version: 1
load_mode:
  value: truncate_and_load
  source: engineer
  evidence: 'FRD Structural Metadata: Load Strategy STG = "Truncate and Load"'
is_master_file:
  value: "no"
  source: engineer
dedup_within_file:
  value: none
  source: engineer
existing_record_policy:
  value: delete_and_insert
  source: engineer
load_frequency:
  value: monthly
  source: frd
  evidence: 'FRD frequency: "Monthly Run; file received by the fifth business day"'
target_tables_exist:
  value: "yes"
  source: engineer
reject_threshold:
  value: none
  source: engineer
data_integrity_checks:
  value: not_null_keys
  source: engineer
has_header:
  value: "yes"
  source: engineer
  evidence: "Vendor file specification: first row carries column names"
has_trailer:
  value: "no"
  source: engineer
```

FAQ file `syn_gadget_events.faq.yaml`: **absent** (every answer defaults with source `unknown`; contract prefills apply).

## Pair B — segmented workbook, one feed (`syn_segmented_frd` + `syn_segmented_sttm.xlsx`)

FRD contract `syn_segmented_frd` (contract-level fields):

| Contract field | Value |
|---|---|
| contract_name | syn_segmented_frd |
| generated_from_frd | syn_segmented_frd.docx |
| generated_date | 2026-01-01T00:00:00 |
| generator | synthetic-kit |
| status | PASS |
| project.project_id / project_name / business_context_summary | SYN-0001 / Synthetic Segmented Ingestion / (null) |
| in_scope | (empty list) |
| out_of_scope | (empty list) |
| assumptions_constraints_dependencies | (empty list) |
| system_interfaces | (empty list) |
| open_items | (empty list) |

Feed 1 of 1:

| Feed field | Value |
|---|---|
| feed_name | Synthetic Segmented Feed |
| source_system | SyntheticVendor |
| file_name_patterns | CCYYMMDD_syn_segmented_*.txt |
| file_format | txt |
| delimiter | \| |
| record_segments | Header ; Detail ; Trailer |
| frequency | Weekly |
| load_windows_sla | (empty list) |
| lobs | ALL |
| domain | Synthetic |
| sub_domain | Segmented |
| landing_location | landing/inbound/synthetic/segmented |
| stage_target.catalog | SYN_DLK |
| stage_target.schema | STG_SYN |
| stage_target.tables | EXT_SYN_HDR ; EXT_SYN_DTL ; EXT_SYN_TRL ; EXT_SYN_DTL_RECYCLE |
| stage_target.load_strategy | Truncate and Load |
| standard_target.catalog | (null) |
| standard_target.schema | (null) |
| standard_target.tables | (empty list) |
| standard_target.load_strategy | Append |
| validation_rules | [1] Process shall fail when file layout is not as per source dictionary. ; [2] Files are pipe delimited and contain incremental changes. ; [3] Member ID validation should be performed against Facets for existence. ; [4] Process should load the files AS-IS after Member ID validation and should not perform any data transformation while loading. ; [5] Populate file type and source file name fields in the target tables. ; [6] Header, Detail and Trailer data should be mapped to respective HDR, DTL and TRL tables. |
| recycle_rule | Invalid records will be moved to Recycle table, retained for 15 days. |
| history_backfill | (null) |
| archive_retention | (null) |
| phi_pii_notes | (null) |
| sttm_reference | (null) |
| requirement_ids | (empty list) |


Sheet `syn_segmented` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
File(s),YYYYMMDD_syn_segmented_*.txt,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
File Generator,SyntheticVendor,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
File Location,landing/inbound/synthetic/segmented,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
LOB,ALL,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
File frequency,Weekly,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
Domain,SYNTHETIC,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
Sub-Domain,SEGMENTED,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
File type,txt (pipe delimited |),,,,,,,,,,,,,,,,,,,,,,,,,,,,,
Source Layout,,,,,,,,,,,Stage Layer ,,,,,,,,,,Standard Layer ,,,,,,,,,
#,Field Name,Data Type,Length,"Field Length
 (fixed width)","Start position 
(fixed width)","End Position
(fixed width)","Segment
(Ex:Header,Trailer,Detail)",PII,Comments ,Business Rule,Catalog,Schema ,TableName ,ColumnName ,DataType,"Mandatory 
Column",Primary Key,Field Description,Table Description,Transformations/Data Quality,Catalog,Schema ,TableName ,ColumnName ,DataType,"Mandatory 
Column",Primary Key,Field Description,Table Description,Transformations/Data Quality
1,Format Version,varchar,10,,,,Header,,Envelope format version,Load as is,SYN_DLK,STG_SYN ,EXT_SYN_HDR,SYN_FMT_VER,String ,,,Envelope format version,Stage table EXT_SYN_HDR,,SYN_STD,SYN ,EXT_SYN_HDR,SYN_FMT_VER,String ,,,Envelope format version,Standard table EXT_SYN_HDR,Load as is
2,Extract Date,varchar,10,,,,Header,,Date the file was produced,Must equal file-name date,SYN_DLK,STG_SYN ,EXT_SYN_HDR,SYN_EXTRACT_DT,String ,,,Date the file was produced,Stage table EXT_SYN_HDR,,SYN_STD,SYN ,EXT_SYN_HDR,SYN_EXTRACT_DT,String ,,,Date the file was produced,Standard table EXT_SYN_HDR,Load as is
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_HDR,SRC_FILE_NAME,String ,,,,,,SYN_STD,SYN ,EXT_SYN_HDR,SRC_FILE_NAME,String ,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_HDR,REC_CREATION_TIME,timestamp,,,,,,SYN_STD,SYN ,EXT_SYN_HDR,REC_CREATION_TIME,timestamp,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_HDR,REC_UPDATED_TIME,timestamp,,,,,,SYN_STD,SYN ,EXT_SYN_HDR,REC_UPDATED_TIME,timestamp,,,,,
1,Member ID,varchar,10,,,,Detail,No,Synthetic member identifier,Load as is,SYN_DLK,STG_SYN ,EXT_SYN_DTL,SYN_MEMBER_ID,String ,,,Synthetic member identifier,Stage table EXT_SYN_DTL,,SYN_STD,SYN ,EXT_SYN_DTL,SYN_MEMBER_ID,String ,,,Synthetic member identifier,Standard table EXT_SYN_DTL,Load as is
2,Widget Owner,varchar,10,,,,Detail,Yes,Synthetic owner name,Load as is,SYN_DLK,STG_SYN ,EXT_SYN_DTL,SYN_WIDGET_OWNER,String ,,,Synthetic owner name,Stage table EXT_SYN_DTL,,SYN_STD,SYN ,EXT_SYN_DTL,SYN_WIDGET_OWNER,String ,,,Synthetic owner name,Standard table EXT_SYN_DTL,Load as is
3,Widget Color,varchar,10,,,,Detail,No,Synthetic color,Load as is,SYN_DLK,STG_SYN ,EXT_SYN_DTL,SYN_WIDGET_COLOR,String ,,,Synthetic color,Stage table EXT_SYN_DTL,,SYN_STD,SYN ,EXT_SYN_DTL,SYN_WIDGET_COLOR,String ,,,Synthetic color,Standard table EXT_SYN_DTL,Load as is
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_DTL,LOB,String ,,,,,,SYN_STD,SYN ,EXT_SYN_DTL,LOB,String ,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_DTL,FILE_TYPE,String ,,,,,,SYN_STD,SYN ,EXT_SYN_DTL,FILE_TYPE,String ,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_DTL,SRC_FILE_NAME,String ,,,,,,SYN_STD,SYN ,EXT_SYN_DTL,SRC_FILE_NAME,String ,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_DTL,REC_CREATION_TIME,timestamp,,,,,,SYN_STD,SYN ,EXT_SYN_DTL,REC_CREATION_TIME,timestamp,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_DTL,REC_UPDATED_TIME,timestamp,,,,,,SYN_STD,SYN ,EXT_SYN_DTL,REC_UPDATED_TIME,timestamp,,,,,
1,Record Type,varchar,10,,,,Trailer,,"Static text identifying the record as the trailer record.
Contains the value ******",Load as is,SYN_DLK,STG_SYN ,EXT_SYN_TRL,SYN_REC_TYPE,String ,,,"Static text identifying the record as the trailer record.
Contains the value ******",Stage table EXT_SYN_TRL,,SYN_STD,SYN ,EXT_SYN_TRL,SYN_REC_TYPE,String ,,,"Static text identifying the record as the trailer record.
Contains the value ******",Standard table EXT_SYN_TRL,Load as is
2,Record Count,Numeric,10,,,,Trailer,,Number of Detail records in the file,Must equal the Detail row count,SYN_DLK,STG_SYN ,EXT_SYN_TRL,SYN_REC_CNT,String ,,,Number of Detail records in the file,Stage table EXT_SYN_TRL,,SYN_STD,SYN ,EXT_SYN_TRL,SYN_REC_CNT,String ,,,Number of Detail records in the file,Standard table EXT_SYN_TRL,Load as is
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_TRL,SRC_FILE_NAME,String ,,,,,,SYN_STD,SYN ,EXT_SYN_TRL,SRC_FILE_NAME,String ,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_TRL,REC_CREATION_TIME,timestamp,,,,,,SYN_STD,SYN ,EXT_SYN_TRL,REC_CREATION_TIME,timestamp,,,,,
,,,,,,,,,,,SYN_DLK,STG_SYN ,EXT_SYN_TRL,REC_UPDATED_TIME,timestamp,,,,,,SYN_STD,SYN ,EXT_SYN_TRL,REC_UPDATED_TIME,timestamp,,,,,
```

Cells carrying deliberate leading/trailing whitespace (kept exactly; the parser normalizes them): L9: 'Stage Layer ', V9: 'Standard Layer ', J10: 'Comments ', M10: 'Schema ', N10: 'TableName ', O10: 'ColumnName ', W10: 'Schema ', X10: 'TableName ', Y10: 'ColumnName ', M11: 'STG_SYN ', P11: 'String ', W11: 'SYN ', Z11: 'String ', M12: 'STG_SYN ', P12: 'String ', W12: 'SYN ', Z12: 'String ', M13: 'STG_SYN ', P13: 'String ', W13: 'SYN ', Z13: 'String ', M14: 'STG_SYN ', W14: 'SYN ', M15: 'STG_SYN ', W15: 'SYN ', M16: 'STG_SYN ', P16: 'String ', W16: 'SYN ', Z16: 'String ', M17: 'STG_SYN ', P17: 'String ', W17: 'SYN ', Z17: 'String ', M18: 'STG_SYN ', P18: 'String ', W18: 'SYN ', Z18: 'String ', M19: 'STG_SYN ', P19: 'String ', W19: 'SYN ', Z19: 'String ', M20: 'STG_SYN ', P20: 'String ', W20: 'SYN ', Z20: 'String ', M21: 'STG_SYN ', P21: 'String ', W21: 'SYN ', Z21: 'String ', M22: 'STG_SYN ', W22: 'SYN ', M23: 'STG_SYN ', W23: 'SYN ', M24: 'STG_SYN ', P24: 'String ', W24: 'SYN ', Z24: 'String ', M25: 'STG_SYN ', P25: 'String ', W25: 'SYN ', Z25: 'String ', M26: 'STG_SYN ', P26: 'String ', W26: 'SYN ', Z26: 'String ', M27: 'STG_SYN ', W27: 'SYN ', M28: 'STG_SYN ', W28: 'SYN '

FAQ file `synthetic_segmented_feed.faq.yaml` (key: value block; each answer is a nested mapping):

```text
schema_version: 1
load_frequency:
  value: weekly
  source: frd
  evidence: 'FRD frequency: "Weekly"'
existing_record_policy:
  value: delete_and_insert
  source: frd
  evidence: 'FRD Structural Metadata: Load Strategy STG "Truncate and Load"; Load Strategy STD "Append"'
reject_threshold:
  value: none
  source: frd
  evidence: 'FRD: "Process shall fail when file layout is not as per source dictionary."'
data_integrity_checks:
  value: custom
  source: frd
  evidence: 'FRD: "Member ID validation should be performed against Facets for existence."'
has_header:
  value: "yes"
  source: frd
  evidence: "FRD record_segments declare a Header"
has_trailer:
  value: "yes"
  source: frd
  evidence: "FRD record_segments declare a Trailer"
```

## Pair C — flat workbook, stage-only feed (`syn_sensor_frd` + `syn_sensor_sttm.xlsx`)

FRD contract `syn_sensor_frd` (contract-level fields):

| Contract field | Value |
|---|---|
| contract_name | syn_sensor_frd |
| generated_from_frd | syn_sensor_frd.docx |
| generated_date | 2026-01-01T00:00:00 |
| generator | synthetic-kit |
| status | PASS |
| project.project_id / project_name / business_context_summary | SYN-0001 / Synthetic Sensor Ingestion / (null) |
| in_scope | (empty list) |
| out_of_scope | (empty list) |
| assumptions_constraints_dependencies | (empty list) |
| system_interfaces | (empty list) |
| open_items | (empty list) |

Feed 1 of 1:

| Feed field | Value |
|---|---|
| feed_name | Syn Sensor Pings |
| source_system | SynVendor Analytics |
| file_name_patterns | sensor_pings_CCYYMMDD.csv |
| file_format | csv |
| delimiter | (null) |
| record_segments | (empty list) |
| frequency | Twice a day, ad hoc reruns allowed |
| load_windows_sla | (empty list) |
| lobs | North |
| domain | (null) |
| sub_domain | (null) |
| landing_location | syn-landing\inbound\sensors\pings\synvendor |
| stage_target.catalog | syn_dlk |
| stage_target.schema | stg_syn |
| stage_target.tables | syn_sensor_pings |
| stage_target.load_strategy | Append |
| standard_target.catalog | (null) |
| standard_target.schema | (null) |
| standard_target.tables | (empty list) |
| standard_target.load_strategy | Append |
| validation_rules | [1] Files are pipe-delimited. ; [2] Invalid records will be moved to the Recycle table. ; [3] If the SENSOR_ID column is NULL, then we are rejecting the record and moving it to the reject table. |
| recycle_rule | (null) |
| history_backfill | (null) |
| archive_retention | (null) |
| phi_pii_notes | (null) |
| sttm_reference | (null) |
| requirement_ids | (empty list) |


Sheet `FILE_DETAILS` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
Vendor,FileName,File Description,Location,Frequency
SynVendor Analytics,sensor_pings_YYYYMMDD.csv,,,Twice daily
```

VERSION_HISTORY of this workbook is anchored at C3 (title `Revision History` in C3, header `Date | Version | Author(s) | Description` in C4:F4, one data row in C5:F5):

Sheet `VERSION_HISTORY` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
,,,,,
,,,,,
,,Revision History,,,
,,Date,Version,Author(s),Description
,,2026-02-01,1.0,Synthetic Author,Initial draft
```

Sheet `MAPPING-SYN_SENSOR_PINGS` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
Source File Layout,,,,,,,Stage Layer,,,
Database Name,Description,Sample Value,DataType, NULL Check,PHI Field ,Mandatory Field,Schema,TableName,ColumnName,DataType
sensor_id,Sensor identifier,S-01,String,NOT NULL,NO,Yes,stg_syn,syn_sensor_pings,sensor_id,String
ping_ts,Ping timestamp,2026-02-01 00:00:00,Timestamp,NULL,NO,NO,stg_syn,syn_sensor_pings,ping_ts,String
reading,Sensor reading,0.75,"Decimal(6,3)",NULL,NO,NO,stg_syn,syn_sensor_pings,reading,String
NA,NA,NA,NA,NULL,No,No,stg_syn,syn_sensor_pings,LOB,string
NA,NA,NA,NA,NULL,No,No,stg_syn,syn_sensor_pings,SRC_FILE_NAME,string
NA,NA,NA,NA,NULL,No,No,stg_syn,syn_sensor_pings,REC_CREATION_TIME,timestamp
NA,NA,NA,NA,NULL,No,No,stg_syn,syn_sensor_pings,REC_UPDATED_TIME,timestamp
```

Cells carrying deliberate leading/trailing whitespace (kept exactly; the parser normalizes them): E2: ' NULL Check', F2: 'PHI Field '

FAQ file `syn_sensor_pings.faq.yaml` (key: value block; each answer is a nested mapping):

```text
schema_version: 1
is_master_file:
  value: "no"
  source: engineer
has_header:
  value: "yes"
  source: engineer
```

## Pair D — Pair A's FRD with a workbook whose recycle window disagrees (`syn_widget_frd` + `syn_widget_sttm_v12.xlsx`)

The workbook is Pair A's workbook with exactly two edits on sheet `MAPPING-SYN_GADGET_EVENTS`: the row-2 header `Recycle Flag ( Enabled for 10 Days)` becomes `Recycle Flag ( Enabled for 12 Days)`, and the recycle cell on the `gadget_key` row reads `12 Days` / `12 days` in place of `10 Days` / `10 days`. The FRD still says 10 days.

Sheet `MAPPING-SYN_GADGET_EVENTS` (CSV; an empty field is an empty cell; a quoted field may span lines):

```csv
Source File Layout,,,,,,,,Stage Layer,,,,,Standard Layer,,,,
Client Data Table Column Name,Description,Comment,Example Values,Data Type,NULL Check,PHI/PII Field,Mandatory,Schema,TableName,ColumnName,DataType,,Schema,TableName,ColumnName,DataType,Recycle Flag ( Enabled for 12 Days)
gadget_key,Gadget key,string,G-100,String,Not NULL,No,Yes,stg_syn,syn_gadget_events,gadget_key,String,,syn,syn_gadget_events,gadget_key,String,"Recycle Flag ( Enabled for 12 Days)
Y ( Check with GADGET_KEY from GadgetMaster in the SYN_STD.GADGETS.GDG_MASTER FOR GRP_CD = 9, if available process it else load this to the Recycle Table with Recycle Flag Enabled for 12 days.)"
event_ts,Event timestamp,"timestamp, UTC",2026-01-15 09:00:00,Timestamp,Not NULL,No,Yes,stg_syn,syn_gadget_events,event_ts,String,,syn,syn_gadget_events,event_ts,Timestamp,
gadget_owner,Gadget's owner name,string,Synthetic Owner,String,NULL,Yes,No,stg_syn,syn_gadget_events,gadget_owner,String,,syn,syn_gadget_events,gadget_owner,String,
gadget_nm,Gadget name,string,Sprocket,String,NULL,No,No,stg_syn,syn_gadget_events,gadget_nm,String,,syn,syn_gadget_events,gadget_name,String,
event_count,Events in window,integer or null,12,Int,NULL,No,No,stg_syn,syn_gadget_events,event_count,String,,syn,syn_gadget_events,event_count,Int,
amount,"Event amount
in local currency",decimal,10.50,"Decimal(12,2)",NULL,No,No,stg_syn,syn_gadget_events,amount,String,,syn,syn_gadget_events,amount,"Decimal(12,2)",
is_active,Active flag,boolean,true,Boolean,NULL,No,No,stg_syn,syn_gadget_events,is_active,String,,syn,syn_gadget_events,is_active,Boolean,
big_ref,Large reference number,bigint,9007199254740993,BigInt,NULL,No,No,stg_syn,syn_gadget_events,big_ref,String,,syn,syn_gadget_events,big_ref,BigInt,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,LOB,string,,syn,syn_gadget_events,LOB,string,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,SRC_FILE_NAME,string,,syn,syn_gadget_events,SRC_FILE_NAME,string,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,REC_CREATION_TIME,timestamp,,syn,syn_gadget_events,REC_CREATION_TIME,timestamp,
NA,NA,,NA,NA,NULL,No,No,stg_syn,syn_gadget_events,REC_UPDATED_TIME,timestamp,,syn,syn_gadget_events,REC_UPDATED_TIME,timestamp,
```

## Pair E — Pair A's workbook with an FRD whose second feed names a different stage table (`syn_widget_frd_renamed` + `syn_widget_sttm.xlsx`)

The FRD is Pair A's FRD with `contract_name` = `syn_widget_frd_renamed` and feed 2's `stage_target.tables` = `syn_gadget_event_log ; syn_gadget_events_recycle` (everything else unchanged).
