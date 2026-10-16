# Row keys - scrubbed export

Every value below is scrubbed: a scrub_check class (and a local-denylist term) is `<CLASS>`; a token found in the golden but not in the repo's committed fixtures is `G<n>`, any other token outside the fixtures is `A<n>` - one map for every file of this export, so the same token is the same placeholder everywhere. Tokens under 3 characters and numbers under 5 digits are kept. CREATED_BY / UPDATED_BY values are withheld.

## DATA_FACTORY_PIPELINE_SCHEDULE

- presence: compared; pair mode: identity; paired by identity 4
- key columns used for pairing: @feed
- rows: golden 4, agent 4, paired 4

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | feed#0 | paired | 2 |
| 3 | feed#0 | paired | 3 |
| 4 | feed#0 | paired | 4 |
| 5 | feed#0 | paired | 5 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 2 | feed#0 | paired | 2 |
| 3 | feed#0 | paired | 3 |
| 4 | feed#0 | paired | 4 |
| 5 | feed#0 | paired | 5 |

## FILE_ADLS_INGESTION_DETAILS

- presence: empty-by-rule; pair mode: key; paired by none
- key columns used for pairing: 
- rows: golden 1, agent 0, paired 0

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | inbound\pharmacy\<LOCAL_DENYLIST>  \| /Pharmacy/<LOCAL_DENYLIST>/ | unpaired | - |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |

## ADLS_DELTA_INGESTION_DETAILS

- presence: compared; pair mode: identity; paired by order 3
- key columns used for pairing: @feed, @flow, TGT_TABLE_NAME, @file
- rows: golden 4, agent 3, paired 3

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | feed#0 \| file_to_stg \| A1 \| A2 | paired | 2 |
| 3 | feed#0 \| file_to_stg \| A1 \| A33 | paired | 3 |
| 4 | feed#0 \| file_to_stg \| A1 \| A35 | paired | 4 |
| 5 | feed#0 \| file_to_stg \| A1 \| A37 | unpaired | - |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 2 | feed#0 \| file_to_stg \| A44 \| A52 | paired | 2 |
| 3 | feed#0 \| file_to_stg \| A44 \| A53 | paired | 3 |
| 4 | feed#0 \| file_to_stg \| A44 \| A54 | paired | 4 |

## STGDELTA_STDDELTA_INGESTION_DET

- presence: compared; pair mode: identity; paired by order 1
- key columns used for pairing: @feed, @flow, TGT_TABLE_NAME, @file
- rows: golden 1, agent 1, paired 1

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | feed#0 \| stg_to_std \| A1 \| A38 | paired | 2 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 2 | feed#0 \| stg_to_std \| A44 \| A4 | paired | 2 |

## ADLS_FIXED_WIDTH_HANDLER

- presence: compared; pair mode: identity; paired by order 3
- key columns used for pairing: @feed, TGT_TABLE, SEGMENT, COL
- rows: golden 3, agent 3, paired 3

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | feed#0 \| A1 \| header \| A39 | paired | 2 |
| 3 | feed#0 \| A1 \| details \| A40 | paired | 3 |
| 4 | feed#0 \| A1 \| trailer \| A41 | paired | 4 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 2 | feed#0 \| A44 \| header \| A55 | paired | 2 |
| 3 | feed#0 \| A44 \| details \| A56 | paired | 3 |
| 4 | feed#0 \| A44 \| trailer \| A57 | paired | 4 |

## DATABRICKS_NOTEBOOK_DETAILS

- presence: compared; pair mode: identity; paired by identity 2
- key columns used for pairing: @feed
- rows: golden 3, agent 2, paired 2

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | feed#0 | paired | 2 |
| 3 | feed#0 | paired | 3 |
| 4 | feed#0 | unpaired | - |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 2 | feed#0 | paired | 2 |
| 3 | feed#0 | paired | 3 |

## DATA_QUALITY_RULES

- presence: compared; pair mode: identity; paired by none
- key columns used for pairing: @feed, @table, SOURCE_COLUMN, RULE_CLASS
- rows: golden 8, agent 6, paired 0

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | feed#0 \| A1 \| A42 \| dateformatrule | unpaired | - |
| 3 | feed#0 \| A1 \| A43 \| datatypecastrule | unpaired | - |
| 4 | feed#0 \| A1 \| A42 \| dateformatrule | unpaired | - |
| 5 | feed#0 \| A1 \| A43 \| datatypecastrule | unpaired | - |
| 6 | feed#0 \| A1 \| A42 \| dateformatrule | unpaired | - |
| 7 | feed#0 \| A1 \| A43 \| datatypecastrule | unpaired | - |
| 8 | feed#0 \| A1 \| A42 \| dateformatrule | unpaired | - |
| 9 | feed#0 \| A1 \| A43 \| datatypecastrule | unpaired | - |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 2 | feed#0 \| A44 \| A45 \| A46 | unpaired | - |
| 3 | feed#0 \| A44 \| A45 \| A47 | unpaired | - |
| 4 | feed#0 \| <none> \| A48 \| lrtrimrule | unpaired | - |
| 5 | feed#0 \| <none> \| A49 \| dateconversionrule | unpaired | - |
| 6 | feed#0 \| <none> \| A50 \| dateconversionrule | unpaired | - |
| 7 | feed#0 \| <none> \| A51 \| datatypecastrule | unpaired | - |

## EMAIL_TEMPLATE_CONFIG

- presence: compared; pair mode: identity; paired by identity 2
- key columns used for pairing: @feed, STATUS
- rows: golden 2, agent 4, paired 2

### Golden rows

| golden row | key | status | agent row |
| --- | --- | --- | --- |
| 2 | feed#0 \| success | paired | 4 |
| 3 | feed#0 \| failed | paired | 5 |

### Agent rows

| agent row | key | status | golden row |
| --- | --- | --- | --- |
| 2 | feed#0 \| A58 | unpaired | - |
| 3 | feed#0 \| A59 | unpaired | - |
| 4 | feed#0 \| success | paired | 2 |
| 5 | feed#0 \| failed | paired | 3 |
