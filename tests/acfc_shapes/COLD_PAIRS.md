# COLD_PAIRS — six synthetic FRD + STTM pairs for a cold-document drill

Purpose: simulate a framework owner handing the agent a pair it has never seen.
These shapes were designed **blind to the reader code and the synonym tables**:
the only inputs were `docs/acfc/SHAPES_FOR_PORT.md`,
`docs/acfc/MULTI_TABLE_DESIGN.md` §1–2, `tests/acfc_shapes/bands.py`,
`tests/acfc_shapes/pair4_nb.py` and `docs/LAYOUT_RECOGNITION.md` ("Band location
by label group, layer by evidence"). Every name below is invented (Northwind
Benefits / Contoso Health / Fabrikam Care, prefixes `nb_` / `ch_` / `fc_`).
Catalogs, where stated at all, are the logical `PR_DLK` / `PR_STD`.

Conventions used in this spec:

- Cell addresses are Excel A1 style. "A1:D1 merged" = one merged range.
- A `|` in a row listing separates consecutive cells (A, B, C, …).
- `(blank)` = the cell exists and is empty. Rows not listed are empty.
- FRD "F1" table rows are written `Ref | Label | Value` (three columns: a row
  reference, the label, the value), as the documented F1 3-column pattern.
- FRD "F2" Solution Requirement tables are written `Label | Value` per row
  (4-column tables with the value merged across columns 2–4).
- "ASK" in the answer key = the two documents legitimately do not determine
  the value; the reader should ask (or, where noted, may apply a documented
  default WITH a cited flag). "STATED" = the reader must not ask.

## Coverage matrix

| Variation | cold_1 | cold_2 | cold_3 | cold_4 | cold_5 | cold_6 |
| --- | --- | --- | --- | --- | --- | --- |
| STTM family (closest) | A | D + banners | E | B | D (minimal) | C |
| Band order | **Standard, then Stage** | stage, standard | stage, standard | stage, standard | one band only | stage, standard, rules AFTER |
| Band title row | layer words | **"Target 1" / "Target 2"** (no layer) | "Raw Zone" / "Curated Zone" | layer words | **none** | **none** (a document title row only) |
| Target header wording | `Target … Name` (both bands identical) | `Schema / TableName / ColumnName / DataType` | **`Schema / Table / Column / Type`** | **`Target Schema / Target Tbl / Target Col / Target Type`** | `Target … in DL` | **`Landing … / Curated … Nm`** |
| Layer evidence in values | PR_DLK/PR_STD + `stg_` | none | `stg_` on stage only | `stg_` on stage only | none | PR_DLK/PR_STD (no `stg_`) |
| Sheets | 2 | 3 | **6** (3 mapping + File Details + Version History + reference) | 4 (FILE_DETAILS, VERSION_HISTORY, 2 × MAPPING-) | 1 | 4 (Version, Layout, STTM, crosswalk) |
| Segmented | no | **H / D / T banner rows** | no | no | no | no |
| Format | pipe delimited | **fixed width (Start/End/Length)** | CSV | CSV | CSV | tab delimited |
| Files → tables | 1 → 1 | 1 → 3 | 3 → 3 | **3 LOB files + 1 file → 2 tables** | 1 → 1 | 1 → 1 |
| Audit rows | the three standard | **LOAD_TS, BATCH_ID** + SRC_FILE_NAME | four standard incl. FILE_TYPE | incl. LOB, FILE_TYPE | **none** | all five standard |
| FRD family | F1 (complete) | **F2** | F1 (`Target Schema` variant, no catalog) | F1 (stanza Object Name) | **short free-form** | F2 + Heading 1 |
| FRD vs STTM disagree | **delimiter** | — | — | — | — | — |
| Expected questions | 1 | 3–4 | 1–2 | 2 | 8–9 | 2 |

---

## cold_1 — `ch_claims_daily` (Contoso Health)

**Purpose:** Family A inline-meta sheet whose Standard band sits LEFT of the
Stage band (titles, catalogs and the `stg_` prefix all agree, column order
contradicts them); a complete F1 FRD that disagrees with the STTM on exactly
one value, the delimiter.

### STTM `STTM_ch_claims_daily.xlsx`

**Sheet 1 `Version`**

- A1:D1 merged: `Contoso Health – Claims Daily STTM`
- Row 3 (header): A `Date` | B `Version` | C `Author(s)` | D `Description of Version/Changes`
- Row 4: `2026-09-01` | `1.0` | `Synthetic Analyst A` | `Initial draft`
- Row 5: `2026-09-15` | `1.1` | `Synthetic Analyst B` | `Added audit columns`

**Sheet 2 `CH_CLAIMS_DAILY`**

Meta rows (label in A, value in B):

| Row | A | B |
| --- | --- | --- |
| 1 | File Names | CH_CLAIMS_DAILY_YYYYMMDD.psv |
| 2 | File Name Example | CH_CLAIMS_DAILY_20260901.psv |
| 3 | Frequency | Daily |
| 4 | File Format (text, csv) | Delimited text |
| 5 | File Delimiter | `,` ← **disagrees with the FRD (pipe, `\|`)** |
| 6 | Last Update Date | 2026-09-15 |
| 7 | Version | 1.1 |
| 8 | LOB | ALL |
| 9 | Target table Name Desc | Daily professional and institutional claim headers |
| 10 | Feed Type | Inbound |
| 11 | Load Strategy | STG: Append; STD: Upsert |
| 12 | (blank) | (blank) |

Band title row 13 (merged ranges):

- A13:F13 `Source Data`
- G13:H13 `Data Rules and Primary Keys`
- I13:N13 `Standard Layer Table`  ← standard FIRST
- O13:T13 `Staging Layer Table`

Header row 14:

| Col | Header | Col | Header |
| --- | --- | --- | --- |
| A | S.No | K | Target Table Name |
| B | Field Name | L | Target Column Name |
| C | Required? | M | Target Data Type |
| D | Format | N | Load Rules |
| E | Length | O | Target Catalog |
| F | Description | P | Target Schema Name |
| G | Primary Key | Q | Target Table Name |
| H | Not NULL | R | Target Column Name |
| I | Target Catalog | S | Target Data Type |
| J | Target Schema Name | T | Load Rules |

(I–N and O–T carry identical header texts; only the titles, the catalog values
and the schema prefix tell the layers apart.)

Data rows 15–20 (A–H | standard band I–N | stage band O–T):

| Row | A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R | S | T |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 15 | 1 | claim_id | Y | String | 20 | Unique claim identifier | Y | Y | PR_STD | ch_claims | ch_claim_header | CLAIM_ID | String | Direct | PR_DLK | stg_ch_claims | ch_claim_header | CLAIM_ID | String | Direct |
| 16 | 2 | member_id | Y | String | 12 | Member identifier | N | Y | PR_STD | ch_claims | ch_claim_header | MEMBER_ID | String | Direct | PR_DLK | stg_ch_claims | ch_claim_header | MEMBER_ID | String | Direct |
| 17 | 3 | service_from_date | Y | Date (YYYYMMDD) | 8 | First date of service | N | Y | PR_STD | ch_claims | ch_claim_header | SERVICE_FROM_DATE | Date | Cast to DATE using yyyyMMdd | PR_DLK | stg_ch_claims | ch_claim_header | SERVICE_FROM_DATE | String | Direct |
| 18 | 4 | billed_amount | N | Decimal | 12 | Total billed amount | N | N | PR_STD | ch_claims | ch_claim_header | BILLED_AMOUNT | Decimal(12,2) | Cast to DECIMAL(12,2) | PR_DLK | stg_ch_claims | ch_claim_header | BILLED_AMOUNT | String | Direct |
| 19 | 5 | claim_status | Y | String | 2 | Adjudication status code | N | Y | PR_STD | ch_claims | ch_claim_header | CLAIM_STATUS | String | Direct | PR_DLK | stg_ch_claims | ch_claim_header | CLAIM_STATUS | String | Direct |
| 20 | 6 | provider_npi | N | String | 10 | Billing provider identifier | N | N | PR_STD | ch_claims | ch_claim_header | PROVIDER_NPI | String | Direct | PR_DLK | stg_ch_claims | ch_claim_header | PROVIDER_NPI | String | Direct |

Audit rows 21–23: A (blank), B `NA`, C–H (blank), standard band = `PR_STD |
ch_claims | ch_claim_header | <col> | <type> | Populated by framework`, stage
band = `PR_DLK | stg_ch_claims | ch_claim_header | <col> | <type> | Populated by framework`:

| Row | Audit column | Type (both bands) |
| --- | --- | --- |
| 21 | SRC_FILE_NAME | String |
| 22 | REC_CREATION_TIME | Timestamp |
| 23 | REC_UPDATED_TIME | Timestamp |

### FRD `FRD_ch_claims_daily.docx` — family F1

No heading styles. Body = a sequence of Word tables.

**Table 1 — Version History** (header `Version | Date | Author | Change`): `1.0 | 2026-08-28 | Synthetic BSA | Initial`.

**Table 2 — Descriptive Metadata**

| Ref | Label | Value |
| --- | --- | --- |
| DM | Descriptive Metadata | (blank) |
| DM-1 | Name | ch_claims_daily |
| DM-2 | Description | Daily claim headers from Contoso Health |
| DM-3 | Functional Requirement | The system shall ingest the Contoso Health daily claims file into the stage and standard layers. |
| DM-4 | Data Source | Contoso Health |
| DM-5 | Object Name | CH_CLAIMS_DAILY_YYYYMMDD.psv |
| DM-6 | Description | One file per business day with all claim headers adjudicated that day |
| DM-7 | Frequency | Daily |
| DM-8 | LOBs | ALL |
| DM-9 | Tags/Keywords | claims, daily |
| DM-10 | Inbound Ingestion | Y |
| DM-11 | Impact Details | (blank) |

**Table 3 — Structural Metadata**

| Ref | Label | Value |
| --- | --- | --- |
| SM | Structural Metadata | (blank) |
| SM-1 | Name | ch_claims_daily structure |
| SM-2 | Description | File and target structure |
| SM-3 | Functional Requirement | Land the file to stage, then publish to standard. |
| SM-4 | Object/data Format | Pipe delimited (`\|`) text file, extension .psv, first row is a column header |
| SM-5 | Target Catalog and Schema | Stage: PR_DLK.stg_ch_claims; Standard: PR_STD.ch_claims |
| SM-6 | Target Table Name | ch_claim_header |
| SM-7 | Domain and Subdomain | Claims / Professional and Institutional |
| SM-8 | Load Strategy STG | Append |
| SM-9 | Load Strategy STD | Upsert on claim_id |
| SM-10 | Archive Schedule | 7 years |
| SM-11 | Source Data Dictionary | Not provided |
| SM-12 | ADLS Location | inbound/contoso_health/claims_daily/ |
| SM-13 | Inbound File Folder Path | mftlanding/inbound/claims/contoso_health/ |

**Table 4 — Technical Metadata**: rows `Primary Key | claim_id`, `PII Fields | member_id`, `Business Key | claim_id`, `Foreign Key(s) | None`, `Transformation Logic | Dates cast from yyyyMMdd; amounts to DECIMAL(12,2)`.

**Table 5 — Data Quality** (positional rows):
1. `Uniqueness/Duplicate Record check/reject (HARD - In pipeline)` | `Reject duplicate claim_id within a file`
2. `Incomplete Record Rejection Process (HARD - In pipeline)` | `Reject records where claim_id or member_id is blank`
3. `Record Recycle Process (HARD - In pipeline)` | `Not applicable`

**Table 6 — Vendor Metadata**: `Vendor Name | Contoso Health`, `Vendor Abbreviation | CH`.

### Answer key — cold_1

| Item | Verdict | Value a careful human gives |
| --- | --- | --- |
| Delimiter | **ASK** (FRD SM-4 `\|` vs STTM B5 `,`; sources disagree) | `\|` — the FRD and the `.psv` extension agree; B5 is a template leftover |
| Band layers | STATED (titles I13 / O13, catalogs PR_STD / PR_DLK, `stg_` prefix on P) — must NOT ask; must NOT assign by column order (column order says the opposite) | I–N = standard, O–T = stage |
| File pattern, format, header row | STATED | CH_CLAIMS_DAILY_YYYYMMDD.psv; delimited; header row yes (SM-4) |
| Frequency, LOB | STATED (both agree) | Daily; ALL |
| Load strategies | STATED (STTM B11 + FRD SM-8/9 agree) | STG Append; STD Upsert on claim_id |
| Catalog / schema / table | STATED (both agree) | PR_DLK.stg_ch_claims.ch_claim_header; PR_STD.ch_claims.ch_claim_header |
| Domain / subdomain, landing path, ADLS location, PK | STATED | as in the FRD |
| Audit columns | STATED | SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME |

Expected: exactly one question (delimiter).

---

## cold_2 — `fc_elig_monthly` (Fabrikam Care)

**Purpose:** fixed-width, segmented H/D/T with banner rows, three stage tables of
which only the Detail table goes to standard; band titles `Target 1` / `Target 2`
name no layer and no value carries layer evidence; audit columns outside the
usual list; FRD family F2.

### STTM `STTM_fc_elig_monthly.xlsx`

**Sheet 1 `Revision Log`**: row 1 header `Rev | Date | Changed By | Notes`;
row 2 `A | 2026-08-11 | Synthetic Analyst D | First cut`; row 3 `B | 2026-09-03 |
Synthetic Analyst D | Trailer count added`.

**Sheet 2 `FC_ELIG_LAYOUT`**

Meta rows:

| Row | A | B |
| --- | --- | --- |
| 1 | Inbound File | FC_ELIG_MTH_CCYYMM.dat |
| 2 | Record Length | 120 |
| 3 | File Layout | Fixed width; Header, Detail and Trailer records |
| 4 | LOB | MCD, CHIP |
| 5 | (blank) | (blank) |

Band title row 6 (merged):

- A6:H6 `Vendor Layout`
- I6:N6 `Target 1`
- O6:T6 `Target 2`

Header row 7: A `Seq` | B `Record Type` | C `Field Name` | D `Start` | E `End` |
F `Length` | G `Type` | H `Notes` | I `Schema` | J `TableName` | K `ColumnName` |
L `DataType` | M `Nullable` | N `Key` | O `Schema` | P `TableName` |
Q `ColumnName` | R `DataType` | S `Nullable` | T `Key`.

Body (segment banner rows are a single text in A, merged A:T; the Target 2
cells are BLANK for Header and Trailer rows — only Detail reaches standard):

| Row | A | B | C | D | E | F | G | H | I | J | K | L | M | N | O | P | Q | R | S | T |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 8 | **Header Record** (A8:T8 merged) | | | | | | | | | | | | | | | | | | | |
| 9 | 1 | H | rec_type | 1 | 1 | 1 | X | Always 'H' | fc_elig_land | fc_elig_hdr | REC_TYPE | String | N | N | | | | | | |
| 10 | 2 | H | file_create_date | 2 | 9 | 8 | 9(8) | CCYYMMDD | fc_elig_land | fc_elig_hdr | FILE_CREATE_DATE | String | N | N | | | | | | |
| 11 | 3 | H | sender_id | 10 | 19 | 10 | X(10) | Sender code | fc_elig_land | fc_elig_hdr | SENDER_ID | String | N | N | | | | | | |
| 12 | **Detail Record** (A12:T12 merged) | | | | | | | | | | | | | | | | | | | |
| 13 | 4 | D | rec_type | 1 | 1 | 1 | X | Always 'D' | fc_elig_land | fc_elig_dtl | REC_TYPE | String | N | N | fc_elig | fc_elig_dtl | REC_TYPE | String | N | N |
| 14 | 5 | D | member_id | 2 | 13 | 12 | X(12) | Member identifier | fc_elig_land | fc_elig_dtl | MEMBER_ID | String | N | Y | fc_elig | fc_elig_dtl | MEMBER_ID | String | N | Y |
| 15 | 6 | D | last_name | 14 | 48 | 35 | X(35) | | fc_elig_land | fc_elig_dtl | LAST_NAME | String | Y | N | fc_elig | fc_elig_dtl | LAST_NAME | String | Y | N |
| 16 | 7 | D | first_name | 49 | 73 | 25 | X(25) | | fc_elig_land | fc_elig_dtl | FIRST_NAME | String | Y | N | fc_elig | fc_elig_dtl | FIRST_NAME | String | Y | N |
| 17 | 8 | D | birth_date | 74 | 81 | 8 | 9(8) | CCYYMMDD | fc_elig_land | fc_elig_dtl | BIRTH_DATE | String | N | N | fc_elig | fc_elig_dtl | BIRTH_DATE | Date | N | N |
| 18 | 9 | D | elig_start | 82 | 89 | 8 | 9(8) | CCYYMMDD | fc_elig_land | fc_elig_dtl | ELIG_START | String | N | Y | fc_elig | fc_elig_dtl | ELIG_START | Date | N | Y |
| 19 | 10 | D | elig_end | 90 | 97 | 8 | 9(8) | CCYYMMDD; 99991231 = open | fc_elig_land | fc_elig_dtl | ELIG_END | String | Y | N | fc_elig | fc_elig_dtl | ELIG_END | Date | Y | N |
| 20 | 11 | D | plan_code | 98 | 103 | 6 | X(6) | | fc_elig_land | fc_elig_dtl | PLAN_CODE | String | N | N | fc_elig | fc_elig_dtl | PLAN_CODE | String | N | N |
| 21 | **Trailer Record** (A21:T21 merged) | | | | | | | | | | | | | | | | | | | |
| 22 | 12 | T | rec_type | 1 | 1 | 1 | X | Always 'T' | fc_elig_land | fc_elig_trl | REC_TYPE | String | N | N | | | | | | |
| 23 | 13 | T | record_count | 2 | 10 | 9 | 9(9) | Count of D records | fc_elig_land | fc_elig_trl | RECORD_COUNT | String | N | N | | | | | | |
| 24 | 14 | T | filler | 11 | 120 | 110 | X(110) | Filler – not loaded | (blank) | (blank) | (blank) | (blank) | | | | | | | | |

Audit rows 25–33 (A blank, C `NA`, D–H blank; B = the record type the row
belongs to; Target 1 always filled; Target 2 filled for the D rows only):

| Row | B | Target 1 (I–L) | Target 2 (O–R) |
| --- | --- | --- | --- |
| 25 | H | fc_elig_land / fc_elig_hdr / SRC_FILE_NAME / String | (blank) |
| 26 | H | fc_elig_land / fc_elig_hdr / LOAD_TS / Timestamp | (blank) |
| 27 | H | fc_elig_land / fc_elig_hdr / BATCH_ID / String | (blank) |
| 28 | D | fc_elig_land / fc_elig_dtl / SRC_FILE_NAME / String | fc_elig / fc_elig_dtl / SRC_FILE_NAME / String |
| 29 | D | fc_elig_land / fc_elig_dtl / LOAD_TS / Timestamp | fc_elig / fc_elig_dtl / LOAD_TS / Timestamp |
| 30 | D | fc_elig_land / fc_elig_dtl / BATCH_ID / String | fc_elig / fc_elig_dtl / BATCH_ID / String |
| 31 | T | fc_elig_land / fc_elig_trl / SRC_FILE_NAME / String | (blank) |
| 32 | T | fc_elig_land / fc_elig_trl / LOAD_TS / Timestamp | (blank) |
| 33 | T | fc_elig_land / fc_elig_trl / BATCH_ID / String | (blank) |

(M/N on audit rows: `N` / `N`.)

**Sheet 3 `Record Type Codes`**: row 1 `Code | Meaning`; rows 2–4 `H | Header`,
`D | Detail`, `T | Trailer`.

### FRD `FRD_fc_elig_monthly.docx` — family F2

Heading 1: `Fabrikam Care Monthly Eligibility – Functional Requirements`.

Paragraph: `This document describes the monthly eligibility feed from Fabrikam Care.`

A 2×2 table (pair-10 style): `Domain | Eligibility` / `Sub Domain | Enrollment Spans`.

**Solution Requirement table 1**

| Label | Value |
| --- | --- |
| Solution Requirement: 1 | (blank) |
| Name | Receive monthly eligibility file |
| Business Requirement | Member services needs current eligibility spans. |
| Functional Requirement: | The system shall ingest the fixed-width file FC_ELIG_MTH_CCYYMM.dat, delivered monthly by the 5th business day, from mftlanding/inbound/eligibility/fabrikam_care/. |
| Structural Metadata | Record length 120. Header (H), Detail (D) and Trailer (T) records are identified by the value in position 1. |
| Impact Details | (blank) |
| Solution Acceptance Criteria | Trailer record_count equals the number of D records in the file. |
| Priority | High |
| Source/Reference | Vendor layout v3 |
| Traced/Related Requirements | SYN-REQ-2201 |
| IS Owner | Synthetic IS Owner |

**Solution Requirement table 2**

| Label | Value |
| --- | --- |
| Solution Requirement: 2 | (blank) |
| Name | Load to landing layer |
| Business Requirement | Keep every monthly file as received. |
| Functional Requirement: | Each record type shall be loaded to its own landing table in schema fc_elig_land, appending each month's file. |
| Technical Metadata | Primary key of the detail record: member_id + elig_start. |
| Impact Details | (blank) |
| Solution Acceptance Criteria | Three landing tables populated per file. |
| Priority | High |
| Source/Reference | (blank) |
| Traced/Related Requirements | SYN-REQ-2202 |
| IS Owner | Synthetic IS Owner |

**Solution Requirement table 3**

| Label | Value |
| --- | --- |
| Solution Requirement: 3 | (blank) |
| Name | Publish to standard layer |
| Business Requirement | Analysts query one curated eligibility table. |
| Functional Requirement: | Detail records shall be published to fc_elig.fc_elig_dtl. Header and trailer records are not published. |
| Data Quality | Reject detail records with a blank member_id. |
| Impact Details | (blank) |
| Solution Acceptance Criteria | Standard table holds only D records. |
| Priority | Medium |
| Source/Reference | (blank) |
| Traced/Related Requirements | SYN-REQ-2203 |
| IS Owner | Synthetic IS Owner |

No catalog is named anywhere. No standard load strategy is named.

### Answer key — cold_2

| Item | Verdict | Value a careful human gives |
| --- | --- | --- |
| Layer of band I–N | **ASK** (`<sheet>/band[n]/layer`): title `Target 1`, plain headers, schema `fc_elig_land` without `stg_`, no catalog. A reader MAY instead resolve it by a CITED cross-document match (FRD SR2 names `fc_elig_land` as the landing schema); assigning it by column order is a FAIL | stage |
| Layer of band O–T | **ASK**, same reasoning (FRD SR3 names `fc_elig.fc_elig_dtl` as standard) | standard |
| Catalogs | **ASK** (or the environment default WITH a flag) — neither document states one | PR_DLK (stage), PR_STD (standard) |
| Standard load strategy | **ASK** — "published" states none | Upsert on member_id + elig_start |
| Stage load strategy | STATED in prose ("appending each month's file", SR2). A human does not ask; a reader that asks is over-asking, not wrong | Append |
| Format / widths | STATED: fixed width, record length 120, every Start/End/Length integer — must NOT ask a width | as in rows 9–24 |
| Segments / record identification | STATED: H/D/T by position 1 (FRD SR1 + B column + banner rows) | H / D / T |
| Tables | STATED: three stage tables (fc_elig_hdr / _dtl / _trl); ONE standard table (fc_elig_dtl) — header/trailer never get a standard table | — |
| Filler (row 24) | STATED as not loaded — must not become a column | — |
| Audit columns | STATED: SRC_FILE_NAME, **LOAD_TS, BATCH_ID** — must be carried as named, not renamed to REC_CREATION_TIME, not supplemented silently | — |
| File pattern, frequency, landing path, LOB, PK, domain | STATED | FC_ELIG_MTH_CCYYMM.dat; Monthly; mftlanding/inbound/eligibility/fabrikam_care/; MCD, CHIP (one file, no LOB token → one file); member_id + elig_start; Eligibility / Enrollment Spans |

Expected: 3–4 questions (two band layers unless resolved by cited
cross-reference; catalogs; standard load strategy).

---

## cold_3 — `nb_provider_roster` (Northwind Benefits)

**Purpose:** Family E multi-sheet workbook: three mapping sheets (one table
each, one file each), plus File Details, Version History and a reference
code sheet; band titles `Raw Zone` / `Curated Zone`; target headers
`Schema / Table / Column / Type` (not `TableName` / `ColumnName` / `DataType`).

### STTM `STTM_nb_provider_roster.xlsx`

**Sheet 1 `Version History`**: A1:D1 merged `Version History`; row 2
`Version | Date | Author | Change Description`; row 3 `0.1 | 2026-08-20 |
Synthetic Analyst C | Draft`; row 4 `1.0 | 2026-09-02 | Synthetic Analyst C |
Baseline after review`.

**Sheet 2 `File Details`**: row 1 header `Vendor | FileName | File Description |
Location | Frequency | File Extension`; rows:

| Row | Vendor | FileName | File Description | Location | Frequency | File Extension |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | Northwind Benefits | NB_PROV_DEMOG_YYYYMMDD.csv | Provider demographics | /mftlanding/inbound/provider/northwind/ | Weekly | .csv |
| 3 | Northwind Benefits | NB_PROV_LOC_YYYYMMDD.csv | Provider service locations | /mftlanding/inbound/provider/northwind/ | Weekly | .csv |
| 4 | Northwind Benefits | NB_PROV_SPEC_YYYYMMDD.csv | Provider specialties | /mftlanding/inbound/provider/northwind/ | Weekly | .csv |

**Sheets 3–5 `PROV_DEMOG`, `PROV_LOC`, `PROV_SPEC`** — identical layout, no
meta rows.

Band title row 1 (merged): A1:E1 `Source Extract`; F1:I1 `Raw Zone`;
J1:M1 `Curated Zone`; N1 `Rules` (single cell).

Header row 2: A `Col #` | B `Source Field` | C `Source Type` | D `Max Len` |
E `Sample` | F `Schema` | G `Table` | H `Column` | I `Type` | J `Schema` |
K `Table` | L `Column` | M `Type` | N `Mandatory (Y/N)`.

Raw-zone schema `stg_nb_prov`, curated-zone schema `nb_prov`; raw types all
`String`. Data rows from row 3 (A–E | F–I | J–M | N):

`PROV_DEMOG` (table `nb_provider_demographic` in both zones):

| # | Source Field | Source Type | Max Len | Sample | Raw Column | Curated Column | Curated Type | Mandatory |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | provider_id | varchar | 15 | NBP000000101 | PROVIDER_ID | PROVIDER_ID | String | Y |
| 2 | provider_npi | varchar | 10 | 1000000001 | PROVIDER_NPI | PROVIDER_NPI | String | N |
| 3 | last_name | varchar | 50 | Sample | LAST_NAME | LAST_NAME | String | Y |
| 4 | first_name | varchar | 35 | Pat | FIRST_NAME | FIRST_NAME | String | N |
| 5 | gender | char | 1 | U | GENDER | GENDER | String | N |
| 6 | effective_date | date | 10 | 2026-01-01 | EFFECTIVE_DATE | EFFECTIVE_DATE | Date | Y |

`PROV_LOC` (table `nb_provider_location`):

| # | Source Field | Source Type | Max Len | Sample | Raw Column | Curated Column | Curated Type | Mandatory |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | provider_id | varchar | 15 | NBP000000101 | PROVIDER_ID | PROVIDER_ID | String | Y |
| 2 | location_id | varchar | 10 | L0001 | LOCATION_ID | LOCATION_ID | String | Y |
| 3 | address_line_1 | varchar | 60 | 1 Example Way | ADDRESS_LINE_1 | ADDRESS_LINE_1 | String | Y |
| 4 | city | varchar | 40 | Sampleton | CITY | CITY | String | Y |
| 5 | state_code | char | 2 | ZZ | STATE_CODE | STATE_CODE | String | Y |
| 6 | zip_code | varchar | 10 | 00000 | ZIP_CODE | ZIP_CODE | String | N |

`PROV_SPEC` (table `nb_provider_specialty`):

| # | Source Field | Source Type | Max Len | Sample | Raw Column | Curated Column | Curated Type | Mandatory |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | provider_id | varchar | 15 | NBP000000101 | PROVIDER_ID | PROVIDER_ID | String | Y |
| 2 | specialty_code | varchar | 4 | SP01 | SPECIALTY_CODE | SPECIALTY_CODE | String | Y |
| 3 | primary_flag | char | 1 | Y | PRIMARY_FLAG | PRIMARY_FLAG | String | N |
| 4 | effective_date | date | 10 | 2026-01-01 | EFFECTIVE_DATE | EFFECTIVE_DATE | Date | Y |

Each mapping sheet ends with four audit rows: A blank, B `NA`, C–E blank,
raw `stg_nb_prov | <table> | <col> | <type>`, curated `nb_prov | <table> |
<col> | <type>`, N `N`: `SRC_FILE_NAME String`, `REC_CREATION_TIME Timestamp`,
`REC_UPDATED_TIME Timestamp`, `FILE_TYPE String`.

**Sheet 6 `Specialty Codes`**: row 1 `Code | Description`; rows `SP01 | Family
Medicine`, `SP02 | Pediatrics`, `SP03 | Cardiology`, `SP04 | Behavioral Health`.

### FRD `FRD_nb_provider_roster.docx` — family F1

**Descriptive Metadata**

| Ref | Label | Value |
| --- | --- | --- |
| DM | Descriptive Metadata | (blank) |
| DM-1 | Name | nb_provider_roster |
| DM-2 | Description | Weekly provider roster from Northwind Benefits |
| DM-3 | Functional Requirement | Ingest the three roster files into stage and standard. |
| DM-4 | Data Source | Northwind Benefits |
| DM-5 | Object Name | NB_PROV_DEMOG_YYYYMMDD.csv<br>NB_PROV_LOC_YYYYMMDD.csv<br>NB_PROV_SPEC_YYYYMMDD.csv (three lines in one cell) |
| DM-6 | Frequency | Weekly |
| DM-7 | LOBs | ALL |

**Structural Metadata** (the `Target Schema` variant label — no catalog)

| Ref | Label | Value |
| --- | --- | --- |
| SM | Structural Metadata | (blank) |
| SM-1 | Name | Provider roster structure |
| SM-2 | Description | (blank) |
| SM-3 | Functional Requirement | (blank) |
| SM-4 | Object/data Format | CSV, comma delimited, first row is a header |
| SM-5 | Target Schema | stg_nb_prov (stage), nb_prov (standard) |
| SM-6 | Target Table Name | nb_provider_demographic, nb_provider_location, nb_provider_specialty |
| SM-7 | Domain and Subdomain | Provider / Roster |
| SM-8 | Load Strategy STG | Truncate and Load |
| SM-9 | Load Strategy STD | Upsert |
| SM-10 | ADLS Location | (blank) |
| SM-11 | Inbound File Folder Path | /mftlanding/inbound/provider/northwind/ |

**Technical Metadata**: `Primary Key | provider_id (demographic); provider_id +
location_id (location); provider_id + specialty_code (specialty)`; `PII Fields |
provider_npi, last_name, first_name`.

**Data Quality**: (1) `Reject duplicate primary keys within a file`; (2)
`Reject rows missing a mandatory field`; (3) `Record Recycle Process | Not
applicable`.

**Vendor Metadata**: `Vendor Name | Northwind Benefits`, `Vendor Abbreviation | NB`.

### Answer key — cold_3

| Item | Verdict | Value a careful human gives |
| --- | --- | --- |
| Catalogs | **ASK** (or environment default WITH a flag) — no catalog column, FRD label is `Target Schema` only | PR_DLK / PR_STD |
| ADLS Location | Blank in the FRD (SM-10). A human ASKS only if the deliverable needs it; if a path convention exists, apply it with a flag | inbound/northwind/provider_roster/ (BSA supplied) |
| Band layers | STATED for a human: `Raw Zone` + `stg_` schema = stage; `Curated Zone` = standard; FRD SM-5 matches both schemas. A reader that asks band[2] is over-asking (acceptable, record it); assigning by column order is a FAIL | F–I stage, J–M standard |
| Mapping vs auxiliary sheets | STATED: three mapping sheets; Version History, File Details, Specialty Codes are not feeds | — |
| Files → tables | STATED by name (DEMOG / LOC / SPEC tokens in file, sheet and table) | 3 files, 3 tables, one each |
| Frequency, format, header row, landing path, load strategies, PKs, domain, LOB | STATED (File Details + FRD agree) | Weekly; CSV `,`; header yes; /mftlanding/inbound/provider/northwind/; STG Truncate and Load / STD Upsert; per-table keys as in Technical Metadata; Provider / Roster; ALL |
| Audit columns | STATED | SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME, FILE_TYPE |

Expected: 1 question (catalogs), 2 if the ADLS location is required.

---

## cold_4 — `ch_rx_claims` (Contoso Health)

**Purpose:** Family B (FILE_DETAILS + one `MAPPING-` sheet per table),
multi-file: one pattern parameterised by LOB (3 LOBs → 3 files) into one
table, plus a second single file into a second table; target headers
`Target Schema / Target Tbl / Target Col / Target Type` under plain layer titles.

### STTM `STTM_ch_rx_claims.xlsx`

**Sheet 1 `FILE_DETAILS`**: row 1 `Vendor | FileName | File Description |
Location | Frequency`; rows:

| Row | Vendor | FileName | File Description | Location | Frequency |
| --- | --- | --- | --- | --- | --- |
| 2 | Contoso Health | CH_RX_CLM_<LOB>_YYYYMMDD.csv | Paid pharmacy claims, one file per LOB (MCD, MCR, DSNP) | /mftlanding/inbound/pharmacy/contoso_health/ | Daily |
| 3 | Contoso Health | CH_RX_REV_YYYYMMDD.csv | Pharmacy claim reversals, all LOBs in one file | /mftlanding/inbound/pharmacy/contoso_health/ | Weekly |

**Sheet 2 `VERSION_HISTORY`**: row 1 `Version | Date | Author | Change Description`;
row 2 `1.0 | 2026-09-10 | Synthetic Analyst E | Initial`.

**Sheet 3 `MAPPING-RX_CLAIM`** and **Sheet 4 `MAPPING-RX_REVERSAL`** — same layout:

Band row 1 (merged): A1:G1 `Source File Layout`; H1:K1 `Stage Layer`; L1:O1 `Standard Layer`.

Header row 2: A `Source Column` | B `Null Check` | C `Description` |
D `Sample Value` | E `Source Type` | F `PHI` | G `Comment` | H `Target Schema` |
I `Target Tbl` | J `Target Col` | K `Target Type` | L `Target Schema` |
M `Target Tbl` | N `Target Col` | O `Target Type`.

`MAPPING-RX_CLAIM` rows 3–8 (stage `stg_ch_rx` / `ch_rx_claim`, standard `ch_rx` / `ch_rx_claim`):

| Row | Source Column | Null Check | Description | Sample | Source Type | PHI | Comment | Stage Col / Type | Standard Col / Type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | rx_claim_id | NOT NULL | Pharmacy claim identifier | RX0000000001 | varchar(20) | N | | RX_CLAIM_ID / String | RX_CLAIM_ID / String |
| 4 | member_id | NOT NULL | Member identifier | M00000000001 | varchar(12) | Y | | MEMBER_ID / String | MEMBER_ID / String |
| 5 | fill_date | NOT NULL | Date dispensed | 2026-09-01 | date | N | | FILL_DATE / String | FILL_DATE / Date |
| 6 | ndc_code | NOT NULL | Product code | 00000000000 | varchar(11) | N | | NDC_CODE / String | NDC_CODE / String |
| 7 | quantity_dispensed | NULL | Units dispensed | 30 | decimal(10,3) | N | | QUANTITY_DISPENSED / String | QUANTITY_DISPENSED / Decimal(10,3) |
| 8 | paid_amount | NULL | Plan paid amount | 12.50 | decimal(12,2) | N | | PAID_AMOUNT / String | PAID_AMOUNT / Decimal(12,2) |

Audit rows 9–12 (A `NA`, B–G blank): `SRC_FILE_NAME String`, `REC_CREATION_TIME
Timestamp`, `LOB String` (Comment G: `From the <LOB> token of the file name`),
`FILE_TYPE String` — in both bands.

`MAPPING-RX_REVERSAL` rows 3–6 (stage `stg_ch_rx` / `ch_rx_reversal`, standard `ch_rx` / `ch_rx_reversal`):

| Row | Source Column | Null Check | Description | Sample | Source Type | PHI | Comment | Stage Col / Type | Standard Col / Type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | rx_claim_id | NOT NULL | Reversed claim identifier | RX0000000001 | varchar(20) | N | | RX_CLAIM_ID / String | RX_CLAIM_ID / String |
| 4 | reversal_date | NOT NULL | Date reversed | 2026-09-05 | date | N | | REVERSAL_DATE / String | REVERSAL_DATE / Date |
| 5 | reversal_reason_code | NULL | Reason code | R1 | varchar(4) | N | | REVERSAL_REASON_CODE / String | REVERSAL_REASON_CODE / String |
| 6 | reversed_amount | NULL | Amount reversed | 12.50 | decimal(12,2) | N | | REVERSED_AMOUNT / String | REVERSED_AMOUNT / Decimal(12,2) |

Audit rows 7–9: `SRC_FILE_NAME String`, `REC_CREATION_TIME Timestamp`,
`FILE_TYPE String` (no LOB — the reversal file carries all LOBs).

### FRD `FRD_ch_rx_claims.docx` — family F1

**Descriptive Metadata**

| Ref | Label | Value |
| --- | --- | --- |
| DM | Descriptive Metadata | (blank) |
| DM-1 | Name | ch_rx_claims |
| DM-2 | Description | Pharmacy claims and reversals from the Contoso Health PBM |
| DM-3 | Functional Requirement | Ingest claim files per LOB and the weekly reversal file. |
| DM-4 | Data Source | Contoso Health PBM |
| DM-5 | Object Name | Stanzas in one cell: `Pharmacy claims:` / `CH_RX_CLM_<LOB>_YYYYMMDD.csv` / `Reversals:` / `CH_RX_REV_YYYYMMDD.csv` (four lines) |
| DM-6 | Frequency | Claims daily; reversals weekly |
| DM-7 | LOBs | MCD, MCR, DSNP |

**Structural Metadata**

| Ref | Label | Value |
| --- | --- | --- |
| SM | Structural Metadata | (blank) |
| SM-4 | Object/data Format | CSV |
| SM-5 | Target Catalog and Schema | PR_DLK.stg_ch_rx; PR_STD.ch_rx |
| SM-6 | Target Table Name | ch_rx_claim, ch_rx_reversal |
| SM-7 | Domain and Subdomain | Pharmacy / Claims |
| SM-8 | Load Strategy STG | Append |
| SM-9 | Load Strategy STD | Upsert |
| SM-10 | ADLS Location | inbound/contoso_health/pharmacy/ |
| SM-11 | Inbound File Folder Path | /mftlanding/inbound/pharmacy/contoso_health/ |

(SM-1..SM-3: `Name | Pharmacy structure`, `Description | (blank)`,
`Functional Requirement | (blank)`.)

**Technical Metadata**: `Primary Key | rx_claim_id`; `PII Fields | member_id`.

**Data Quality**: (1) `Reject duplicate rx_claim_id within a claim file`; (2)
`Reject records missing member_id`; (3) `Record Recycle Process | Not applicable`.

**Vendor Metadata**: `Vendor Name | Contoso Health PBM`, `Vendor Abbreviation | CHRX`.

### Answer key — cold_4

| Item | Verdict | Value a careful human gives |
| --- | --- | --- |
| Standard upsert key of `ch_rx_reversal` | **ASK** — the FRD's single Primary Key = `rx_claim_id` is feed-level; a claim can be reversed more than once, and the STTM marks no key column | rx_claim_id + reversal_date |
| Header row in the CSV files | **ASK** — "CSV" alone does not say | yes, one header row |
| Files | STATED: `<LOB>` × 3 listed LOBs = 3 claim files + 1 reversal file = 4 files; must NOT ask the LOB list | CH_RX_CLM_MCD_…, CH_RX_CLM_MCR_…, CH_RX_CLM_DSNP_…, CH_RX_REV_… |
| Files → tables | STATED (sheet names, Object Name stanzas, File Details descriptions) | 3 claim files → ch_rx_claim; reversal → ch_rx_reversal |
| Band layers | STATED (titles `Stage Layer` / `Standard Layer`, `stg_` prefix, FRD SM-5) | H–K stage, L–O standard |
| Frequency per file | STATED (File Details + DM-6 agree) | claims Daily, reversals Weekly |
| Catalogs / schemas / tables, load strategies, landing path, ADLS location, domain, claim PK | STATED | as in the FRD |
| Delimiter | STATED by format CSV | `,` |
| Audit columns | STATED; LOB only on the claim table | as listed |

Expected: 2 questions.

---

## cold_5 — `fc_provdir` (Fabrikam Care)

**Purpose:** the thinnest plausible pair — a SHORT free-form FRD (three
paragraphs: a landing file path and a target table name, nothing else) and a
one-sheet STTM with NO band title row, ONE target band whose headers say
`… in DL` (deliberately not layer evidence), no catalog, no audit rows.

### STTM `STTM_fc_provdir.xlsx`

**Sheet 1 `Provider Directory`** (the only sheet)

| Row | A | B |
| --- | --- | --- |
| 1 | File Name | fc_provdir_YYYYMMDD.csv |
| 2 | File Format | CSV |
| 3 | (blank) | (blank) |

No band title row. Header row 4: A `No.` | B `Field Name` | C `Data Type` |
D `Length` | E `Description` | F `PII` | G `Target Schema Name in DL` |
H `Target Table Name in DL` | I `Target Column Name in DL` | J `Target Data Type in DL`.

Rows 5–10 (G = `fc_provdir`, H = `fc_provider_directory` on every row):

| Row | A | B | C | D | E | F | I | J |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 1 | provider_id | String | 15 | Directory provider identifier | No | PROVIDER_ID | String |
| 6 | 2 | provider_name | String | 80 | Display name | No | PROVIDER_NAME | String |
| 7 | 3 | specialty_desc | String | 60 | Specialty description | No | SPECIALTY_DESC | String |
| 8 | 4 | phone_number | String | 15 | Office phone | No | PHONE_NUMBER | String |
| 9 | 5 | accepting_new_patients | String | 1 | Y/N | No | ACCEPTING_NEW_PATIENTS | String |
| 10 | 6 | last_verified_date | Date | 10 | YYYY-MM-DD | No | LAST_VERIFIED_DATE | Date |

No audit rows. No `NA` rows. Nothing below row 10.

### FRD `FRD_fc_provdir.docx` — short free-form

No tables, no section labels. Title paragraph (Title style):
`Fabrikam Care – Provider Directory Feed`. Then exactly three Normal paragraphs:

1. `Fabrikam Care sends a provider directory extract so that member services can look up in-network providers.`
2. `The file lands at /mftlanding/inbound/provider/fabrikam_care/fc_provdir_YYYYMMDD.csv.`
3. `The data is to be loaded into the table fc_provider_directory.`

### Answer key — cold_5

| Item | Verdict | Value a careful human gives |
| --- | --- | --- |
| Layer of the single band (G–J) | **ASK** — no title row; "in DL" is NOT layer evidence; schema `fc_provdir` has no `stg_`; no catalog | stage |
| Standard layer in scope? | **ASK** — one band, one table named; nothing says whether a standard copy exists | not in scope for this drop (stage only) |
| Frequency | **ASK** — stated nowhere | Weekly |
| Stage load strategy | **ASK** | Truncate and Load (a directory snapshot) |
| Header row | **ASK** | yes |
| Primary key | **ASK** — no key column, no FRD statement | provider_id |
| Domain / subdomain | **ASK** | Provider / Directory |
| Catalog | **ASK** (or environment default WITH a flag) | PR_DLK |
| Audit columns | **ASK / confirm** — the STTM lists none; the framework set must not be added silently | SRC_FILE_NAME, REC_CREATION_TIME, REC_UPDATED_TIME |
| Delimiter | Inferable from `.csv` + `File Format CSV`; a human does not ask (a confirming question is acceptable) | `,` |
| File pattern, landing path | STATED (FRD paragraph 2 + STTM B1 agree) | fc_provdir_YYYYMMDD.csv; /mftlanding/inbound/provider/fabrikam_care/ |
| Table, schema | STATED (FRD paragraph 3 + STTM H; schema STTM-only) | fc_provdir.fc_provider_directory |
| Source / vendor | STATED (paragraph 1) | Fabrikam Care |
| Field list and types | STATED | rows 5–10 |

Expected: 8–9 questions. A reader that produces a pipeline here without asking
has invented values.

---

## cold_6 — `ch_member_enroll` (Contoso Health)

**Purpose:** Family C dual sheets (vendor `Layout` + mapping `STTM`) where the
mapping sheet has a document TITLE row (one merged cell, not a band row) and no
band title row; layer told only by `Landing …` / `Curated …` header wording and
the catalog values PR_DLK / PR_STD (schemas carry no `stg_`); rules columns
come AFTER both target bands; tab delimited; F2 FRD with Heading 1 sections.

### STTM `STTM_ch_member_enroll.xlsx`

**Sheet 1 `Version Control`**: row 1 `Version | Date | Description | Updated By`;
row 2 `1.0 | 2026-09-12 | Initial mapping | Synthetic Analyst F`;
row 3 `1.1 | 2026-09-26 | Added lob_code | Synthetic Analyst F`.

**Sheet 2 `Layout`** (vendor spec): A1 `FileName` | B1 `CH_MBR_ENROLL_YYYYMMDD.tsv`;
header row 3: A `Field #` | B `Field Name` | C `Req'd?` | D `Type` | E `Max Length` | F `Comments`;
rows 4–10: `1 | member_id | Y | AN | 12 |`, `2 | subscriber_id | Y | AN | 12 |`,
`3 | relationship_code | Y | AN | 2 | 18 = self`, `4 | coverage_start | Y | DT | 8 | CCYYMMDD`,
`5 | coverage_end | N | DT | 8 | CCYYMMDD`, `6 | plan_id | Y | AN | 8 |`,
`7 | lob_code | Y | AN | 2 | see LOB Crosswalk`.

**Sheet 3 `STTM`**

- A1:Q1 merged: `Contoso Health Member Enrollment – Source to Target Mapping` (a document title, NOT a band title)
- A2 `Delimiter` | B2 `Tab`
- Row 3 blank
- Header row 4 (no band title row above it):

| Col | Header | Col | Header |
| --- | --- | --- | --- |
| A | Field # | J | Curated Catalog |
| B | Field Name | K | Curated Schema Nm |
| C | Type | L | Curated Table Nm |
| D | Data Definition | M | Curated Column Nm |
| E | Landing Catalog | N | Curated Data Type |
| F | Landing Schema | O | PII |
| G | Landing Table | P | Primary Key |
| H | Landing Col | Q | Load Rules |
| I | Landing Data Type | | |

Rows 5–11 (E = `PR_DLK`, F = `ch_mbr_land`, G = `ch_member_enrollment`;
J = `PR_STD`, K = `ch_mbr`, L = `ch_member_enrollment` on every row):

| Row | A | B | C | D | H | I | M | N | O | P | Q |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 1 | member_id | AN | Member identifier | MEMBER_ID | String | MEMBER_ID | String | Y | Y | Direct |
| 6 | 2 | subscriber_id | AN | Subscriber identifier | SUBSCRIBER_ID | String | SUBSCRIBER_ID | String | Y | N | Direct |
| 7 | 3 | relationship_code | AN | Relationship to subscriber | RELATIONSHIP_CODE | String | RELATIONSHIP_CODE | String | N | N | Direct |
| 8 | 4 | coverage_start | DT | Span start | COVERAGE_START | String | COVERAGE_START | Date | N | Y | Cast to DATE using yyyyMMdd |
| 9 | 5 | coverage_end | DT | Span end | COVERAGE_END | String | COVERAGE_END | Date | N | N | Cast to DATE using yyyyMMdd |
| 10 | 6 | plan_id | AN | Benefit plan | PLAN_ID | String | PLAN_ID | String | N | N | Direct |
| 11 | 7 | lob_code | AN | Line of business code | LOB_CODE | String | LOB_CODE | String | N | N | Direct |

Audit rows 12–16 (A blank, B `NA`, C–D blank, both bands filled with the same
catalog / schema / table as above, O–P `N`, Q `Populated by framework`):
`SRC_FILE_NAME String`, `REC_CREATION_TIME Timestamp`, `REC_UPDATED_TIME
Timestamp`, `LOB String`, `FILE_TYPE String`.

**Sheet 4 `LOB Crosswalk`**: row 1 `Code | LOB`; rows `01 | MCD`, `02 | CHIP`, `03 | MCR`.

### FRD `FRD_ch_member_enroll.docx` — family F2 with Heading 1

- Heading 1 `1 Overview` → paragraph: `Contoso Health sends a daily member enrollment file. This document states the requirements for landing and curating it.`
- A 2×2 table: `Domain | Membership` / `Sub Domain | Enrollment`.
- Heading 1 `2 Solution Requirements`, then three SR tables:

**Solution Requirement: 1**

| Label | Value |
| --- | --- |
| Solution Requirement: 1 | (blank) |
| Name | Ingest member enrollment file |
| Business Requirement | Enrollment spans must be available the next morning. |
| Functional Requirement: | Ingest the tab-delimited daily file CH_MBR_ENROLL_YYYYMMDD.tsv from mftlanding/inbound/membership/contoso_health/ into the landing table ch_mbr_land.ch_member_enrollment. |
| Structural Metadata | Load Strategy STG: Append |
| Impact Details | (blank) |
| Solution Acceptance Criteria | Every delivered file is landed once. |
| Priority | High |
| Source/Reference | Vendor layout v2 |
| Traced/Related Requirements | SYN-REQ-6101 |
| IS Owner | Synthetic IS Owner |

**Solution Requirement: 2**

| Label | Value |
| --- | --- |
| Solution Requirement: 2 | (blank) |
| Name | Curate member enrollment |
| Business Requirement | One current row per enrollment span. |
| Functional Requirement: | Publish enrollment spans to ch_mbr.ch_member_enrollment. |
| Technical Metadata | Primary Key: member_id, coverage_start |
| Impact Details | (blank) |
| Solution Acceptance Criteria | No duplicate member_id + coverage_start in standard. |
| Priority | High |
| Source/Reference | (blank) |
| Traced/Related Requirements | SYN-REQ-6102 |
| IS Owner | Synthetic IS Owner |

**Solution Requirement: 3**

| Label | Value |
| --- | --- |
| Solution Requirement: 3 | (blank) |
| Name | Enrollment data quality |
| Business Requirement | Bad spans must not reach analysts. |
| Functional Requirement: | Reject records whose coverage_end is earlier than coverage_start. |
| Data Quality | Reject; no recycle. |
| Impact Details | (blank) |
| Solution Acceptance Criteria | Rejected rows are logged with the reason. |
| Priority | Medium |
| Source/Reference | (blank) |
| Traced/Related Requirements | SYN-REQ-6103 |
| IS Owner | Synthetic IS Owner |

No standard load strategy is stated. No catalog is stated in the FRD.

### Answer key — cold_6

| Item | Verdict | Value a careful human gives |
| --- | --- | --- |
| Standard load strategy | **ASK** — SR2 says "publish" and names a key, but no strategy | Upsert on member_id + coverage_start |
| Header row | **ASK** — neither document says | yes |
| Band layers | STATED: Catalog values PR_DLK (E) → stage, PR_STD (J) → standard; header words Landing / Curated and FRD SR1 / SR2 agree. Row 1 is a document title, not a band title — must not be read as one band spanning A–Q | E–I stage, J–N standard |
| Rules columns O–Q | STATED as rules (PII, Primary Key, Load Rules) after both bands — must not be read as part of the standard band | — |
| Delimiter | STATED (STTM B2 `Tab`, FRD SR1, `.tsv`) | tab |
| Catalogs / schemas / table | STATED in the STTM; FRD names schema.table, consistent | PR_DLK.ch_mbr_land.ch_member_enrollment; PR_STD.ch_mbr.ch_member_enrollment |
| Stage load strategy, frequency, landing path, domain, PK, DQ, recycle | STATED | Append; Daily; mftlanding/inbound/membership/contoso_health/; Membership / Enrollment; member_id + coverage_start; reject, no recycle |
| LOB | STATED: one file with no LOB token; LOB per record from lob_code via the crosswalk; partition `NA` | MCD / CHIP / MCR as values, one file |
| Audit columns | STATED | all five |

Expected: 2 questions.
