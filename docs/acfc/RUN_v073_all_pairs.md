# RUN_v073_all_pairs — v0.7.3 Full Pair Evaluation

> **Version**: 0.7.3-acfc (commit efb909f on staging, 9216e9b merge+fix on acfc-local)
> **Deployment**: App `codegen-agent` deployment `<TOKEN_76>` (SNAPSHOT from acfc-local)
> **Generation options**: framework mode, acfc_prx conventions, iig_v2 template, VDD attached
> **Pairs evaluated**: 1–10 (workspace inputs role)
> **Scrub rule**: every file name, sheet name, vendor, feed, table, schema, catalog,
>   column and person that is a business term → `<TOKEN_n>`; structural words stay.
>   Applies INSIDE quoted strings, flag bodies and rejection messages too (file-name patterns, LOB names, sheet names, feed wording).
>   Generic data-element names (Amount, Adj. Group, AMT_nn, *_DT columns) are structural and stay.

---

## Token Table

| Token | Category | Scope |
| --- | --- | --- |
| `<TOKEN_1>` | file | pair 1 STTM |
| `<TOKEN_2>` | file | pair 1 FRD |
| `<TOKEN_3>` | file | pair 1 VDD |
| `<TOKEN_4>` | file | pair 2 STTM |
| `<TOKEN_5>` | file | pair 2 FRD |
| `<TOKEN_6>` | file | pair 2 VDD |
| `<TOKEN_7>` | file | pair 3 STTM |
| `<TOKEN_8>` | file | pair 3 FRD |
| `<TOKEN_9>` | file | pair 3 VDD |
| `<TOKEN_10>` | file | pair 4 STTM |
| `<TOKEN_11>` | file | pair 4 FRD |
| `<TOKEN_12>` | file | pair 4 VDD |
| `<TOKEN_13>` | file | pair 5 STTM |
| `<TOKEN_14>` | file | pair 5 FRD |
| `<TOKEN_15>` | file | pair 5 VDD |
| `<TOKEN_16>` | file | pair 6 STTM |
| `<TOKEN_17>` | file | pair 6 FRD |
| `<TOKEN_18>` | file | pair 6 VDD |
| `<TOKEN_19>` | file | pair 7 STTM |
| `<TOKEN_20>` | file | pair 7 FRD |
| `<TOKEN_21>` | file | pair 7 VDD |
| `<TOKEN_22>` | file | pair 8 STTM |
| `<TOKEN_23>` | file | pair 8 FRD |
| `<TOKEN_24>` | file | pair 8 VDD |
| `<TOKEN_25>` | file | pair 9 STTM |
| `<TOKEN_26>` | file | pair 9 FRD |
| `<TOKEN_27>` | file | pair 9 VDD |
| `<TOKEN_28>` | file | pair 10 STTM |
| `<TOKEN_29>` | file | pair 10 FRD |
| `<TOKEN_30>` | file | pair 10 VDD |
| `<TOKEN_31>` | sheet | pair 5 mapping |
| `<TOKEN_32>` | sheet | pair 7 mapping |
| `<TOKEN_33>` | sheet | pair 1 VDD fields |
| `<TOKEN_34>` | sheet | pair 1 mapping |
| `<TOKEN_35>` | sheet | pair 1 VDD fields |
| `<TOKEN_36>` | vendor | pairs 1,3,4,6 |
| `<TOKEN_37>` | vendor | pair 2 |
| `<TOKEN_38>` | vendor | pair 5 |
| `<TOKEN_39>` | vendor | pair 5 |
| `<TOKEN_40>` | vendor | pair 7 |
| `<TOKEN_41>` | vendor | pair 10 |
| `<TOKEN_42>` | vendor | pairs 3,6 |
| `<TOKEN_43>` | vendor | pair 9 |
| `<TOKEN_44>` | project | pairs 1,3,4,6 |
| `<TOKEN_45>` | ticket | pairs 1,3,4,6 |
| `<TOKEN_46>` | project | pair 2 |
| `<TOKEN_47>` | project | pair 2 |
| `<TOKEN_48>` | ticket | pair 5 |
| `<TOKEN_49>` | ticket | pair 7 |
| `<TOKEN_50>` | project | pair 8 |
| `<TOKEN_51>` | ticket | pair 8 |
| `<TOKEN_52>` | project | pair 9 |
| `<TOKEN_53>` | project | pair 9 |
| `<TOKEN_54>` | ticket | pair 9 |
| `<TOKEN_55>` | ticket | pair 10 |
| `<TOKEN_56>` | ticket | pair 10 |
| `<TOKEN_57>` | project | pair 10 |
| `<TOKEN_58>` | project | pair 7 |
| `<TOKEN_59>` | project | pair 5 |
| `<TOKEN_60>` | catalog | pair 1 stage |
| `<TOKEN_61>` | catalog | pair 1 standard |
| `<TOKEN_62>` | schema | pair 1 standard |
| `<TOKEN_63>` | schema | pair 1 stage |
| `<TOKEN_64>` | feed | pair 1 |
| `<TOKEN_65>` | artefact | pair 1 DDL |
| `<TOKEN_66>` | sheet | pair 10 mapping |
| `<TOKEN_67>` | sheet | pair 10 mapping |
| `<TOKEN_68>` | sheet | pair 10 mapping |
| `<TOKEN_69>` | LOB | pair 1 |
| `<TOKEN_70>` | LOB | pair 1 |
| `<TOKEN_71>` | LOB | pair 1 |
| `<TOKEN_72>` | file pattern | pair 1 |
| `<TOKEN_73>` | file pattern | pair 1 |
| `<TOKEN_74>` | file pattern | pair 1 |
| `<TOKEN_75>` | feed wording | pair 1 |
| `<TOKEN_76>` | deployment id | App deployment |

---

## Summary

| Pair | FRD Family | Select (s) | FRD Rule | VDD Rule | Outcome | Verdict | Flags | Artefacts | Questions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F1 | — | ticket | ? | DONE | FAIL | 93 | 7 | — |
| 2 | F1 | 9.1 | name_stem | content | NEEDS_ANSWERS | — | — | — | 1 |
| 3 | F1 | 116.5 | ticket | same_folder | FAILED | — | — | — | — |
| 4 | F1 | 8.5 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 2 |
| 5 | F1 | 7.1 | ticket | None | NEEDS_ANSWERS | — | — | — | 6 |
| 6 | F1 | 8.6 | ticket | content | NEEDS_ANSWERS | — | — | — | 2 |
| 7 | F1 | 7.1 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 4 |
| 8 | F2 | 8.7 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 5 |
| 9 | F2 | 9.2 | ticket | content | NEEDS_ANSWERS | — | — | — | 5 |
| 10 | F3 | 7.6 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 16 |

**Outcome legend**: DONE = ran to verdict; NEEDS_ANSWERS = layout resolution produced questions
the operator must answer before generation; FAILED = generation failed (timeout or error).

---

## Per-Pair Detail

### Pair 1

* **STTM**: `<TOKEN_1>`
* **FRD**: `<TOKEN_2>`
* **VDD**: `<TOKEN_3>`
* **FRD family**: F1
* **Select time**: ? s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: ?

**Layout resolution**

| Document | Source | Provider Calls | Roles |
| --- | --- | --- | --- |
| STTM | synonyms | 0 | 27 |
| FRD | synonyms | 0 | 49 |
| VDD | synonyms | 0 | 21 |

* Gap fills: `feeds[0].frequency` ← "Daily" from VDD (``<TOKEN_33>`!E2`)
* Layout questions: 0

**Generation** (? s)

* **Feed**: `<TOKEN_64>`
* **Verdict**: FAIL
* **Candidate count**: 7
* **Flag count**: 93

**Findings (all 93 flags)**

1. frd_unstated:feeds[0].feed_name source_used:STTM stage band '`<TOKEN_34>`': '`<TOKEN_64>`' (the FRD's Object Name cell is a labelled_files value, not a name)
2. frd_multiline:feeds[0].domain (line breaks) — FRD table 6 row 7 ('Domain and Subdomain'); unstated, resolved from the other documents
3. frd_multiline:feeds[0].stage_target.schema (line breaks) — FRD table 6 row 5 ('Target Catalog and Schema'); unstated, resolved from the other documents
4. frd_multiline:feeds[0].frequency (line breaks) — FRD table 5 row 7 ('Frequency'); unstated, resolved from the other documents
5. frd_multiline:feeds[0].landing_location (line breaks) — FRD table 6 row 13 ('ADLS Location'); unstated, resolved from the other documents
6. frd_unstated:feeds[0].frequency source_used:VDD `<TOKEN_33>`!E2: 'Daily'
7. frd_unstated:feeds[0].stage_target.schema source_used:STTM stage band (authoritative; never asked)
8. frd_layer_block:feeds[0].stage_target.tables — inline layer block in table 6 row 6 ('Target Table Name'): stage table='`<TOKEN_64>`'; standard table='`<TOKEN_64>`'; read per layer, never as a table name
9. file_pattern_from_object_name:feeds[0] — the FRD table 5 row 5 ('Object Name') cell is a block listing 3 file(s) under ['`<TOKEN_69>`', '`<TOKEN_70>`', '`<TOKEN_71>`']; taken as the file name patterns ['`<TOKEN_72>`', '`<TOKEN_73>`', '`<TOKEN_74>`']
10. frd_feed_name_unstated:feeds[0] — the table 5 row 5 ('Object Name') cell is a labelled_files value, not a name; placeholder '`<TOKEN_2>` feed 1 (unnamed)' until the layout stage names the feed after the STTM stage band
11. frd_unstated:feeds[0].feed_name source_used:STTM stage band '`<TOKEN_34>`': '`<TOKEN_64>`' (the FRD's Object Name cell is a labelled_files value, not a name)
12. frd_multiline:feeds[0].domain (line breaks) — FRD table 6 row 7 ('Domain and Subdomain'); unstated, resolved from the other documents
13. frd_multiline:feeds[0].stage_target.schema (line breaks) — FRD table 6 row 5 ('Target Catalog and Schema'); unstated, resolved from the other documents
14. frd_multiline:feeds[0].frequency (line breaks) — FRD table 5 row 7 ('Frequency'); unstated, resolved from the other documents
15. frd_multiline:feeds[0].landing_location (line breaks) — FRD table 6 row 13 ('ADLS Location'); unstated, resolved from the other documents
16. frd_unstated:feeds[0].frequency source_used:VDD `<TOKEN_33>`!E2: 'Daily'
17. type_format:ADJMNT_DT — the STTM declares 'Date(YYYY-MM-DD)' (sheet '`<TOKEN_34>`' row 31): type 'Date', format 'YYYY-MM-DD'
18. field_unmapped:Adj. Group (01) — STTM `<TOKEN_34>`!V34 reads 'Do Not Map'; the field is in neither the stage nor the standard table
19. length_is_precision:Amount (01) — STTM `<TOKEN_34>`!G38 reads '10,2': a precision, kept as the source type precision Decimal(10,2); it is not a byte width and none is derived from it
20. width_from_sttm_span:Amount (01) — STTM `<TOKEN_34>`!F38 / `<TOKEN_34>`!H38: end 231 - start 220 + 1 = 12
21. field_unmapped:Adj. Group (02) — STTM `<TOKEN_34>`!V41 reads 'Do Not Map'; the field is in neither the stage nor the standard table
22. length_is_precision:Amount (02) — STTM `<TOKEN_34>`!G45 reads '10,2': a precision, kept as the source type precision Decimal(10,2); it is not a byte width and none is derived from it
23. width_from_sttm_span:Amount (02) — STTM `<TOKEN_34>`!F45 / `<TOKEN_34>`!H45: end 257 - start 246 + 1 = 12
24. field_unmapped:Adj. Group (03) — STTM `<TOKEN_34>`!V48 reads 'Do Not Map'; the field is in neither the stage nor the standard table
25. length_is_precision:Amount (03) — STTM `<TOKEN_34>`!G52 reads '10,2': a precision, kept as the source type precision Decimal(10,2); it is not a byte width and none is derived from it
26. width_from_sttm_span:Amount (03) — STTM `<TOKEN_34>`!F52 / `<TOKEN_34>`!H52: end 283 - start 272 + 1 = 12
27. field_unmapped:Adj. Group (04) — STTM `<TOKEN_34>`!V55 reads 'Do Not Map'; the field is in neither the stage nor the standard table
28. length_is_precision:Amount (04) — STTM `<TOKEN_34>`!G59 reads '10,2': a precision, kept as the source type precision Decimal(10,2); it is not a byte width and none is derived from it
29. width_from_sttm_span:Amount (04) — STTM `<TOKEN_34>`!F59 / `<TOKEN_34>`!H59: end 309 - start 298 + 1 = 12
30. field_unmapped:Adj. Group (05) — STTM `<TOKEN_34>`!V62 reads 'Do Not Map'; the field is in neither the stage nor the standard table
31. length_is_precision:Amount (05) — STTM `<TOKEN_34>`!G66 reads '10,2': a precision, kept as the source type precision Decimal(10,2); it is not a byte width and none is derived from it
32. width_from_sttm_span:Amount (05) — STTM `<TOKEN_34>`!F66 / `<TOKEN_34>`!H66: end 335 - start 324 + 1 = 12
33. field_unmapped:Adj. Group (06) — STTM `<TOKEN_34>`!V69 reads 'Do Not Map'; the field is in neither the stage nor the standard table
34. length_is_precision:Amount (06) — STTM `<TOKEN_34>`!G73 reads '10,2': a precision, kept as the source type precision Decimal(10,2); it is not a byte width and none is derived from it
35. width_from_sttm_span:Amount (06) — STTM `<TOKEN_34>`!F73 / `<TOKEN_34>`!H73: end 361 - start 350 + 1 = 12
36. type_format:MBR_BIRTH_DT — the STTM declares 'Date(YYYY-MM-DD)' (sheet '`<TOKEN_34>`' row 83): type 'Date', format 'YYYY-MM-DD'
37. frd_unstated:stage_target.schema source_used:STTM `<TOKEN_34>` stage band (schema column): '`<TOKEN_63>`'
38. frd_unstated:standard_target.schema source_used:STTM `<TOKEN_34>` standard band (schema column): '`<TOKEN_62>`'
39. frd_unstated:stage_target.catalog source_used:STTM `<TOKEN_34>` stage band (catalog column): '`<TOKEN_60>`'
40. frd_unstated:standard_target.catalog source_used:STTM `<TOKEN_34>` standard band (catalog column): '`<TOKEN_61>`'
41. segments_from_sttm: the FRD names no record segments; the STTM's Segment column declares ['Header', 'Detail', 'Trailer'] (sheet '`<TOKEN_34>`')
42. sibling_type_mismatch:_01 — `<TOKEN_64>`: 6 columns end in _01, 5 typed string, minority: AMT_01 Decimal(10,2) (`<TOKEN_34>` row 38); transcribed as stated, confirm with the STTM author
43. sibling_type_mismatch:_02 — `<TOKEN_64>`: 6 columns end in _02, 5 typed string, minority: AMT_02 Decimal(10,2) (`<TOKEN_34>` row 45); transcribed as stated, confirm with the STTM author
44. sibling_type_mismatch:_03 — `<TOKEN_64>`: 6 columns end in _03, 5 typed string, minority: AMT_03 Decimal(10,2) (`<TOKEN_34>` row 52); transcribed as stated, confirm with the STTM author
45. sibling_type_mismatch:_04 — `<TOKEN_64>`: 6 columns end in _04, 5 typed string, minority: AMT_04 Decimal(10,2) (`<TOKEN_34>` row 59); transcribed as stated, confirm with the STTM author
46. sibling_type_mismatch:_05 — `<TOKEN_64>`: 6 columns end in _05, 5 typed string, minority: AMT_05 Decimal(10,2) (`<TOKEN_34>` row 66); transcribed as stated, confirm with the STTM author
47. sibling_type_mismatch:_06 — `<TOKEN_64>`: 6 columns end in _06, 5 typed string, minority: AMT_06 Decimal(10,2) (`<TOKEN_34>` row 73); transcribed as stated, confirm with the STTM author
48. vdd_missing_in_sttm — VDD `<TOKEN_35>`!B20 (field 'Adj. Group (01)') has no source field in the STTM
49. vdd_missing_in_sttm — VDD `<TOKEN_35>`!B27 (field 'Adj. Group (02)') has no source field in the STTM
50. vdd_missing_in_sttm — VDD `<TOKEN_35>`!B34 (field 'Adj. Group (03)') has no source field in the STTM
51. vdd_missing_in_sttm — VDD `<TOKEN_35>`!B41 (field 'Adj. Group (04)') has no source field in the STTM
52. vdd_missing_in_sttm — VDD `<TOKEN_35>`!B48 (field 'Adj. Group (05)') has no source field in the STTM
53. vdd_missing_in_sttm — VDD `<TOKEN_35>`!B55 (field 'Adj. Group (06)') has no source field in the STTM
54. vdd_field_count — STTM 70 source field(s) vs VDD 76 field(s) on sheet(s) ['`<TOKEN_35>`']
55. iig_blank:DATA_FACTORY_PIPELINE_SCHEDULE: PIPELINE_ID, PIPELINE_NAME, PARENT_PIPELINE_ID, PIPELINE_DESCRIPTION, ACTIVE_START_DATE, ESTIMATED_START_TIME, APPLICATION_NAME, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
56. iig_blank:FILE_ADLS_INGESTION_DETAILS: GROUP_ID, OBJECT_ID, PIPELINE_ID, SRC_CONNECTION_ID, SRC_ROOT_DIR, TGT_CONTAINER_NAME, SRC_EXTRACT_START_TIME, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE, TGT_STORAGE_ACCOUNT_NAME
57. iig_blank:ADLS_DELTA_INGESTION_DETAILS: GROUP_ID, OBJECT_ID, PIPELINE_ID, CLAIM_TYPE_ID, SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, SRC_CONTAINER_NAME, SRC_FILE_DELIMITER, SRC_REC_LNGTH, SRC_COL_LNGTH, SRC_COL_STRT_END_INDX, HEADER_FLAG, FILE_HEADER_FLAG, FILE_FOOTER_FLAG, TGT_CONNECTION_ID, TGT_CONTAINER_NAME, RECYCL_RETN_DAYS, MAPPING_EXPRESSION, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
58. iig_blank:STGDELTA_STDDELTA_INGESTION_DET: GROUP_ID, OBJECT_ID, PIPELINE_ID, SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, SRC_CONTAINER_NAME, TGT_CONNECTION_ID, TGT_CONTAINER_NAME, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
59. iig_blank:ADLS_FIXED_WIDTH_HANDLER: PROCESS_NAME, VERSION, SEGMNT_TYP, SEGMENT_FILTER, PIPELINE_ID, FILE_TYPE, EXTENSION, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE, FILE_REJECTION, RJCT_RSN_COLUMN_NM
60. iig_blank:DATABRICKS_NOTEBOOK_DETAILS: PIPELINE_ID, PIPELINE_NAME, GROUP_ID, PROCESS_NAME, DATABRICKS_WORKSPACE_URL, DATABRICKS_WORKSPACE_SECRET, DATABRICKS_CLUSTERID, DATABRICKS_NOTEBOOK_PATH, DATABRICKS_NOTEBOOK_NAME, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE, CLUSTER_DETAILS_ID, DELETE_DATABRICKS_NOTEBOOK_NAME, DQ_NOTEBOOK_PATH
61. iig_blank:EMAIL_TEMPLATE_CONFIG: TEMPLATE_ID, TEMPLATE_NAME, PROCESS_NAME, SUBJECT, BODY, BODY_QUERY, SENDER_NAME, SENDER_EMAIL, EMAIL_CC, CREATED_BY, CREATED_DATE, UPDATED_BY, UPDATED_DATE
62. ddl_file_name_from_slug: no feed_abbreviation in the load-pattern FAQ; the combined DDL is named '`<TOKEN_65>`' from the feed slug
63. dml_unconfirmed:connection_table — table / column identifiers FILE_CONNECTION_DETAILS(CONNECTION_ID, HOST_NAME, ROOT_PATH) are as spoken in the walkthrough, not printed; confirm before running (docs/acfc/METADATA_DB_SEMANTICS.md §3)
64. dml_not_described:STGDELTA_STDDELTA_INGESTION_DET — written from the IIG cells under the §1 conventions only (docs/acfc/METADATA_DB_SEMANTICS.md §8)
65. dml_not_described:ADLS_FIXED_WIDTH_HANDLER — written from the IIG cells under the §1 conventions only (docs/acfc/METADATA_DB_SEMANTICS.md §8)
66. dml_not_described:DATABRICKS_NOTEBOOK_DETAILS — written from the IIG cells under the §1 conventions only (docs/acfc/METADATA_DB_SEMANTICS.md §8)
67. dml_not_described:EMAIL_TEMPLATE_CONFIG — written from the IIG cells under the §1 conventions only (docs/acfc/METADATA_DB_SEMANTICS.md §8)
68. dml_unassigned:@RFC_NUMBER — engineer (the RFC / ATMT ticket); CREATED_BY and UPDATED_BY on every row (§1) (docs/acfc/METADATA_DB_SEMANTICS.md); answer FAQ 'rfc_number' or set it in the notebook
69. dml_unassigned:@PIPELINE_ID — engineer; unique across DATA_FACTORY_PIPELINE_SCHEDULE, one per process (§2) (docs/acfc/METADATA_DB_SEMANTICS.md); answer FAQ 'pipeline_id' or set it in the notebook
70. dml_unassigned:@PARENT_PIPELINE_ID — engineer; 0 for a master pipeline, else the master's PIPELINE_ID (§2) (docs/acfc/METADATA_DB_SEMANTICS.md); answer FAQ 'parent_pipeline_id' or set it in the notebook
71. dml_unassigned:@GROUP_ID — engineer; unique across the ingestion tables and never reused by another process (§5) (docs/acfc/METADATA_DB_SEMANTICS.md); answer FAQ 'group_id' or set it in the notebook
72. dml_unassigned:@OBJECT_ID — engineer; 1..n within the group, one per input file (§5) (docs/acfc/METADATA_DB_SEMANTICS.md); answer FAQ 'object_id' or set it in the notebook
73. dml_unassigned:@SRC_CONNECTION_ID — identity value of the connection table; reused by host / root path or inserted (preflight); docs/acfc/METADATA_DB_SEMANTICS.md §3
74. dml_unassigned:@SRC_ADLS_CONNECTION_ID — identity value of the connection table; reused by host / root path or inserted (preflight); docs/acfc/METADATA_DB_SEMANTICS.md §3
75. dml_unassigned:@METADATA_CONNECTION_ID — identity value of the connection table; reused by host / root path or inserted (preflight); docs/acfc/METADATA_DB_SEMANTICS.md §3
76. dml_unassigned:@TGT_CONNECTION_ID — identity value of the connection table; reused by host / root path or inserted (preflight); docs/acfc/METADATA_DB_SEMANTICS.md §3
77. dml_unassigned:@SRC_HOST_NAME — platform / Azure team; the file connection's host (docs/acfc/METADATA_DB_SEMANTICS.md §3)
78. faq_unanswered:is_master_file
79. faq_unanswered:dedup_within_file
80. faq_unanswered:existing_record_policy
81. faq_unanswered:target_tables_exist
82. faq_unanswered:reject_threshold
83. faq_unanswered:data_integrity_checks
84. load_mode_not_enforced: declared append; generated writer uses MERGE-by-file (branching planned v2)
85. rule classified flagged: 'Record Recycle Process (HARD - In pipeline): No Recycle Process' — FRD states a recycle rule but the STTM has no structured recycle spec for this feed — unconfirmed attribution; no recycle module generated
86. Layer-2 candidate pending engineer approval: 'Capture Descriptive Metadata'
87. Layer-2 candidate pending engineer approval: 'The `<TOKEN_75>` Inbound Files with the above descriptive meta data will be ingested into Lake House.'
88. Layer-2 candidate pending engineer approval: 'The `<TOKEN_75>` Inbound Files with the Structural Metadata mentioned above will be ingested into Lake House'
89. Layer-2 candidate pending engineer approval: 'Administrative Metadata will be captured for the ingestion of `<TOKEN_75>` Inbound files from `<TOKEN_36>` into Lake House'
90. Layer-2 candidate pending engineer approval: '`<TOKEN_75>` Inbound Files data will be ingested as per the mapping document'
91. Layer-2 candidate pending engineer approval: 'Solution Acceptance Criteria: `<TOKEN_75>` Inbound Files data will be ingested as per the DQ rules mentioned above'
92. Layer-2 candidate pending engineer approval: 'IS Owner: `<TOKEN_36>`'
93. generated tests were skipped — PASS cannot be claimed

**Top flag kinds**

| Flag Kind | Count |
| --- | --- |
| dml_unassigned | 10 |
| frd_unstated | 9 |
| frd_multiline | 8 |
| iig_blank | 7 |
| Layer-2 candidate pending engineer approval | 7 |
| field_unmapped | 6 |
| length_is_precision | 6 |
| width_from_sttm_span | 6 |
| sibling_type_mismatch | 6 |
| vdd_missing_in_sttm | 6 |
| faq_unanswered | 6 |
| dml_not_described | 4 |
| type_format | 2 |
| frd_layer_block | 1 |
| file_pattern_from_object_name | 1 |

### Pair 2

* **STTM**: `<TOKEN_4>`
* **FRD**: `<TOKEN_5>`
* **VDD**: `<TOKEN_6>`
* **FRD family**: F1
* **Select time**: 9.1 s
* **Parser mode**: subprocess
* **FRD pairing**: name_stem
* **VDD pairing**: content
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 15.1 s (halted on layout questions)
* **Provider calls**: 0

**Questions** (verbatim)

1. [choice] **File format** — `feeds[0].file_format` — candidates: File Data Ingestion, CSV

### Pair 3

* **STTM**: `<TOKEN_7>`
* **FRD**: `<TOKEN_8>`
* **VDD**: `<TOKEN_9>`
* **FRD family**: F1
* **Select time**: 116.5 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: FAILED
* **Run time**: 266.5 s
* **Error**: None

### Pair 4

* **STTM**: `<TOKEN_10>`
* **FRD**: `<TOKEN_11>`
* **VDD**: `<TOKEN_12>`
* **FRD family**: F1
* **Select time**: 8.5 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 14.7 s (halted on layout questions)
* **Provider calls**: 0

**Questions** (verbatim)

1. [text] **Sheet name** — `feeds[0].sheet_name`
2. [choice] **File format** — `feeds[0].file_format` — candidates: .xlsx, Fixed-width

### Pair 5

* **STTM**: `<TOKEN_13>`
* **FRD**: `<TOKEN_14>`
* **VDD**: `<TOKEN_15>`
* **FRD family**: F1
* **Select time**: 7.1 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: None
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 34.1 s (halted on layout questions)
* **Provider calls**: 1

**Questions** (verbatim)

1. [role] **Field name** — ``<TOKEN_31>`/source/field_name` — candidates: ?
2. [role] **Schema** — ``<TOKEN_31>`/stage/schema` — candidates: ?
3. [role] **Table** — ``<TOKEN_31>`/stage/table` — candidates: ?
4. [role] **Column name** — ``<TOKEN_31>`/stage/column` — candidates: ?
5. [role] **Target data type** — ``<TOKEN_31>`/stage/target_type` — candidates: ?
6. [choice] **File format** — `feeds[0].file_format` — candidates: .txt files, Delimited

### Pair 6

* **STTM**: `<TOKEN_16>`
* **FRD**: `<TOKEN_17>`
* **VDD**: `<TOKEN_18>`
* **FRD family**: F1
* **Select time**: 8.6 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: content
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 14.5 s (halted on layout questions)
* **Provider calls**: 0

**Questions** (verbatim)

1. [choice] **File format** — `feeds[0].file_format` — candidates: SQL Server Table to  Databricks Table, Database Table
2. [choice] **File format** — `feeds[1].file_format` — candidates: SQL Server Table to  Databricks Table, Database Table

### Pair 7

* **STTM**: `<TOKEN_19>`
* **FRD**: `<TOKEN_20>`
* **VDD**: `<TOKEN_21>`
* **FRD family**: F1
* **Select time**: 7.1 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 28.4 s (halted on layout questions)
* **Provider calls**: 1
* **STTM rejections**: ["sttm <TOKEN_32>/standard/schema: column 13 lies outside the standard band 14-16"]

**Questions** (verbatim)

1. [role] **Schema** — ``<TOKEN_32>`/standard/schema`
2. [text] **Sheet name** — `feeds[0].sheet_name`
3. [choice] **File format** — `feeds[0].file_format` — candidates: Xlsx files, Fixed-width
4. [choice] **Load frequency** — `feeds[0].frequency` — candidates: 1) 03/20/2026 
2) 03/31/2026 
3) 04/02/2026 
4)  04/08/2026 
5) 04/15/2026, Historical (one-time)

### Pair 8

* **STTM**: `<TOKEN_22>`
* **FRD**: `<TOKEN_23>`
* **VDD**: `<TOKEN_24>`
* **FRD family**: F2
* **Select time**: 8.7 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 45.5 s (halted on layout questions)
* **Provider calls**: 2

**Questions** (verbatim)

1. [role] **Source system / vendor** — `feeds[0].source_system` — candidates: Business 
Requirement, Descriptive Metadata, Impact Details, Solution 
Acceptance 
Criteria, Priority (+48 more)
2. [role] **Lines of business** — `feeds[0].lobs` — candidates: Business 
Requirement, Descriptive Metadata, Impact Details, Solution 
Acceptance 
Criteria, Priority (+48 more)
3. [role] **Domain and subdomain** — `feeds[0].domain` — candidates: Business 
Requirement, Descriptive Metadata, Impact Details, Solution 
Acceptance 
Criteria, Priority (+48 more)
4. [role] **Stage load strategy** — `feeds[0].stage_target.load_strategy` — candidates: Business 
Requirement, Descriptive Metadata, Impact Details, Solution 
Acceptance 
Criteria, Priority (+48 more)
5. [role] **Standard load strategy** — `feeds[0].standard_target.load_strategy` — candidates: Business 
Requirement, Descriptive Metadata, Impact Details, Solution 
Acceptance 
Criteria, Priority (+48 more)

### Pair 9

* **STTM**: `<TOKEN_25>`
* **FRD**: `<TOKEN_26>`
* **VDD**: `<TOKEN_27>`
* **FRD family**: F2
* **Select time**: 9.2 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: content
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 30.6 s (halted on layout questions)
* **Provider calls**: 1

**Questions** (verbatim)

1. [role] **Source system / vendor** — `feeds[0].source_system` — candidates: Business 
Requirement, Reject /Recycle Process, Impact Details, Solution 
Acceptance 
Criteria, Priority (+57 more)
2. [role] **Lines of business** — `feeds[0].lobs` — candidates: Business 
Requirement, Reject /Recycle Process, Impact Details, Solution 
Acceptance 
Criteria, Priority (+57 more)
3. [role] **Domain and subdomain** — `feeds[0].domain` — candidates: Business 
Requirement, Reject /Recycle Process, Impact Details, Solution 
Acceptance 
Criteria, Priority (+57 more)
4. [role] **Stage load strategy** — `feeds[0].stage_target.load_strategy` — candidates: Business 
Requirement, Reject /Recycle Process, Impact Details, Solution 
Acceptance 
Criteria, Priority (+57 more)
5. [role] **Standard load strategy** — `feeds[0].standard_target.load_strategy` — candidates: Business 
Requirement, Reject /Recycle Process, Impact Details, Solution 
Acceptance 
Criteria, Priority (+57 more)

### Pair 10

* **STTM**: `<TOKEN_28>`
* **FRD**: `<TOKEN_29>`
* **VDD**: `<TOKEN_30>`
* **FRD family**: F3
* **Select time**: 7.6 s
* **Parser mode**: subprocess
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 44.4 s (halted on layout questions)
* **Provider calls**: 2
* **STTM rejections**: ["sttm <TOKEN_66>/source/ordinal: only 23% of the values under the header are integer-like (threshold 80%)", "sttm <TOKEN_67>/source/ordinal: only 9% of the values under the header are integer-like (threshold 80%)", "sttm <TOKEN_68>/source/ordinal: only 10% of the values under the header are integer-like (threshold 80%)"]

**Questions** (verbatim)

1. [text] **Source system / vendor** — `feeds[0].source_system`
2. [text] **Lines of business** — `feeds[0].lobs`
3. [text] **Stage load strategy** — `feeds[0].stage_target.load_strategy`
4. [text] **Standard load strategy** — `feeds[0].standard_target.load_strategy`
5. [choice] **File format** — `feeds[0].file_format` — candidates: CSV, Delimited
6. [choice] **Delimiter** — `feeds[0].delimiter` — candidates: Comma, Pipe (|)
7. [choice] **Load frequency** — `feeds[0].frequency` — candidates: Periodic, Weekly
8. [choice] **File format** — `feeds[1].file_format` — candidates: CSV, Delimited
9. [choice] **Delimiter** — `feeds[1].delimiter` — candidates: Comma, Pipe (|)
10. [choice] **Load frequency** — `feeds[1].frequency` — candidates: Periodic, Weekly
11. [choice] **File format** — `feeds[2].file_format` — candidates: CSV, Delimited
12. [choice] **Delimiter** — `feeds[2].delimiter` — candidates: Comma, Pipe (|)
13. [choice] **Load frequency** — `feeds[2].frequency` — candidates: Periodic, Weekly
14. [choice] **File format** — `feeds[3].file_format` — candidates: CSV, Delimited
15. [choice] **Delimiter** — `feeds[3].delimiter` — candidates: Comma, Pipe (|)
16. [choice] **Load frequency** — `feeds[3].frequency` — candidates: Periodic, Weekly