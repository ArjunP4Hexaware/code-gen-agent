# SHAPES_FOR_PORT — Structural Shapes of 10 FRD / STTM / VDD Triplets

> **Purpose**: Structural description only — no data values, no business-term column
> names, no vendor names, no IDs.  Anonymised for external portability.
>
> **Naming key**: Vendor names → VENDOR_A … VENDOR_J; feeds → FEED_1 … FEED_10;
> source systems → SRC_SYS_A … SRC_SYS_E; project names → PROJECT_ALPHA … PROJECT_DELTA.

---

## 1. STTM Workbooks

### Layout Families

Five layout families were identified across the ten workbooks:

| Family | Description | Pairs |
| --- | --- | --- |
| **A – Inline-Meta + Banded Mapping** | Rows 1-12 hold file-level metadata as label:value pairs (File Name, Frequency, File Format, LOB, Load Strategy, etc.). A band-header row spans merged cells across column groups (Source Data / Data Rules / Stage Layer / Standard Layer). Field-level header row follows immediately below. | 1, 8 |
| **B – FILE_DETAILS + MAPPING Sheets** | Separate FILE_DETAILS sheet (tabular: Vendor, FileName, File Description, Location, Frequency). One MAPPING- sheet per source file, each with a two-row header: band row (Source File Layout / Stage Layer / Standard Layer) then field header row. | 2 |
| **C – Layout + STTM Dual Sheets** | A "Layout" sheet reproduces the vendor's original field spec (Field #, Field Name, Type, Length, Start, End, Comments, plus LOB-specific columns). A separate "STTM" sheet adds mapping columns (Data Definition, PII, Primary Key, Load Rules, Workspace, Catalog, Schema, TableName, ColumnName, DataType — repeated for Stage and Standard layers). | 3 |
| **D – Single STTM Mapping Sheet** | One primary mapping sheet with a merged band-header row (Source Data / Data Rules / Stage Layer / Standard Layer) at row 4, field-level headers at row 5. May include auxiliary sheets (LOB crosswalk, overpunch rules, server details). | 4, 6 |
| **E – Multi-Domain / Multi-Sheet** | Multiple mapping sheets — one per file or per table/segment. Header structure varies per sheet but follows pattern: band row then field headers. May include Summary, File Details, Table_Details, Version History, Analysis, and scratch sheets. | 5, 7, 9, 10 |

### Pair 1 — STTM (Family A)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | Version | 6 | 4 | 3 (`Date`, `Version`, `Author(s)`, `Description of Version/Changes`) | 1 (A2:D2) |
| 2 | LOB_CROSSWALK | 18 | 5 | 1 (5 generic LOB-mapping headers) | 2 |
| 3 | FEED_1_MAPPING | 103 | 62 | Band r14 merged across 4 groups; field headers r15 (27 cols) | 4 (row-14 band merges) |

**FEED_1_MAPPING meta rows (r1-r12):**
```
r1  File Names           = [value]
r2  File Name Example    = [value]
r3  Frequency            = [value]
r4  File Format (text, csv) = [value]
r5  File Delimiter       = [empty]
r6  Last Update Date     = [empty]
r7  Version              = [empty]
r8  LOB                  = [value]
r9  Target table Name Desc = [value]
r10 Feed Type            = [empty]
r11 Load Strategy        = [value]
r12 Notes                = [empty]
```

**FEED_1_MAPPING band row r14:** `Source Data` | `Data Rules and Primary Keys` | `Staging Layer Table` | `Standard Layer Table`

**FEED_1_MAPPING field headers r15 (27 cols):**
`S.No`, `Segment`, `Field Name`, `Required?`, `Format`, `Start`, `Length`, `End`, `Description`, `Data Definition`, `PII`, `Primary Key`, `Critical Data`, `Not NULL`, `Load Rules`, `Workspace`, `Target Catalog`, `Target Schema Name in DL`, `Target Table Name in DL`, `Target_Column_Name_in_DL`, `Target Data Type in DL` — repeated for Stage and Standard layers.

### Pair 2 — STTM (Family B)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | FILE_DETAILS | 6 | 5 | 1 (`Vendor`, `FileName`, `File Description`, `Location`, `Frequency`) | 0 |
| 2 | VERSION_HISTORY | 2 | 4 | 1 (`Version`, `Date`, `Author`, `Change Description`) | 0 |
| 3 | MAPPING- | 92 | 18 | Band r1 (3 cols); field headers r2 (16 cols) | 0 |
| 4 | MAPPING-1 | 273 | 18 | Band r1 (3 cols); field headers r2 (16 cols) | 0 |
| 5 | MAPPING-2 | 52 | 18 | Band r1 (3 cols); field headers r2 (16 cols) | 0 |

**MAPPING band row r1:** `Source File Layout` | `Stage Layer` | `Standard Layer`

**MAPPING field headers r2 (16 cols):**
`Database column Name`, `NULL CHECK`, `Description`, `Sample Value`, `DataType`, `PHI Field`, `Mandatory Field`, `Comment`, `Schema`, `TableName`, `ColumnName`, `DataType`, `Schema`, `TableName`, `ColumnName`, `DataType`

Note: Schema/TableName/ColumnName/DataType appear twice — once for Stage, once for Standard.

### Pair 3 — STTM (Family C)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | Version Control | 9 | 4 | 1 (`Version`, `Date`, `Description`, `Updated By`) | 0 |
| 2 | Layout | 336 | 15 | Meta r1 (FileName=[value]); field headers r4 (13 cols) | 0 |
| 3 | STTM | 1048538 | 34 | Meta r1-r2; band r4 merged 4 groups; field headers r5 (31 cols) | 4 |
| 4 | FileNames | 24 | 3 | 1 (`LOB`, `Carrier`, `Inbound File Name`) | 0 |

**Layout field headers r4 (13 cols):**
`Field #`, `Field Name`, `Req'd?`, `Type`, `Length`, `Start`, `End`, `Comments`, then 5 LOB-applicability columns

**STTM band row r4:** `Source - [SRC_SYS_A] File` | `Destination` | `Target Table - Staging Layer` | `Target Table - Standard Layer`

**STTM field headers r5 (31 cols):**
`Field #`, `Field Name`, `Type`, `Length`, `Start Position`, `End Position`, `Comments`, 5 LOB columns, `Data Definition`, `PII`, `Primary Key`, `Critical Data`, `Required/Situational/Optional`, `DQ Rules`, `Load Rules`, `Workspace`, `Catalog`, `Schema`, `TableName`, `ColumnName`, `DataType` — repeated for Stage and Standard.

**Note:** Row count 1,048,538 on STTM sheet is an openpyxl artefact — actual populated rows ≈ 336 (matching Layout sheet).

### Pair 4 — STTM (Family D)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | STTM | 148 | 28 | Meta r1 (File Name); band r4 (4 groups merged); field headers r5 (25 cols) | 4 |
| 2 | LOB_CROSSWALK | 8 | 3 | 1 (3 cols: plan-code mapping) | 0 |
| 3 | OVERPUNCH_RULES | 21 | 3 | Band r1-r2; field headers r3 (3 cols) | 2 |

**STTM band row r4:** `Source Data` | `Data Rules` | `Target Table - Staging Layer` | `Target Table - Standard Layer`

**STTM field headers r5 (25 cols):**
`Sl. No.`, `Field Name`, `Type`, `Start`, `End`, `Len`, `Description`, `Data Definition`, `PII`, `Primary Key`, `Critical Data`, `Not NULL`, `LOAD Rule`, `Workspace`, `Target Catalog`, `Target Schema Name in Lakehouse`, `Target Table Name in Lakehouse`, `Target Column Name in Lakehouse`, `Target Data Type in Lakehouse` — repeated for Stage and Standard.

### Pair 5 — STTM (Family E)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | Version History | 9 | 5 | Band r3; field headers r4 (4 cols) | 1 |
| 2 | File Details | 15 | 7 | 1 (`Vendor`, `FileName`, `Actual File Name`, `File Description`, `Location`, `Frequency`, `File Extension`) | 0 |
| 3 | Table_Details | 2 | 4 | 1 (`S.No`, `SchemaName`, `Table_Name`, `Table_Description`) | 0 |
| 4 | FEED_5_MAPPING | 170 | 33 | Meta r1-r9; band r10 (3 groups merged); field headers r11 (33 cols) | 5 |
| 5 | Sheet2 (unmapped fields list) | 88 | 3 | 1 (3 cols — field expansion notes) | 0 |
| 6 | Sheet3 (field names only) | 88 | 1 | No header — single-column list | 0 |
| 7 | Sheet1 (DQ rules) | 132 | 3 | 1 (`FieldName`, `DQ Rules`, `DataType`) | 0 |

**FEED_5_MAPPING meta rows (r1-r9):**
```
r1  File(s)          = [value]
r2  File Generator   = [empty]
r3  File Location    = [value]
r4  LOB              = [value]
r5  File frequency   = [value]
r6  Domain           = [value]
r7  Sub-Domain       = [value]
r8  NOTE             = [text note about delimiters]
r9  File type        = [value]
```

**FEED_5_MAPPING band row r10:** `Source Layout` | `Stage Layer` | `Standard Layer`

**FEED_5_MAPPING field headers r11 (33 cols):**
`Field Id`, `Column No.`, `Field Name`, `Data Type`, `Length`, `Field Length`, `Start position`, `End Position`, `Segment`, `PII/PHI`, `Comments`, `Catalog`, `Schema`, `TableName`, `ColumnName`, `DataType`, `Mandatory`, `Primary Key`, `Constraints`, `Field Description`, `Table Description`, `Transformations/Data Quality` — repeated for Stage and Standard.

### Pair 6 — STTM (Family D)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | Version Control | 4 | 4 | 2 (`Version`, `Date`, `Author(s)`, `Description of Version/Changes`) | 0 |
| 2 | Server details | 22 | 3 | 1 (`Server`, `Database`, `Environment`) | 6 (environment-group merges) |
| 3 | FEED_6_MAPPING | 212 | 24 | Band r2 (3 groups merged); field headers r3 (22 cols) | 3 |

**FEED_6_MAPPING band row r2:** `Source table` | `Stage Layer` | `STD layer`

**FEED_6_MAPPING field headers r3 (22 cols):**
`Inscope for Implementation`, `SERVER NAME`, `TABLE_CATALOG`, `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME`, `Primary Key`, `DATA_TYPE`, `NULL/NOT NULL`, `Load Rules`, `Workspace`, `Catalog`, `Schema`, `TableName`, `ColumnName`, `DataType` — repeated for Stage and Standard.

Note: Source here is a **database table** (not a file), so headers include TABLE_CATALOG / TABLE_SCHEMA / TABLE_NAME.

### Pair 7 — STTM (Family E)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | Version History | 7 | 8 | Band r5; field headers r6 (4 cols) | 1 |
| 2 | File Details | 6 | 5 | 1 (`Vendor`, `FileName`, `File Description`, `Location`, `Frequency (Historical Drops)`) | 0 |
| 3 | MAPPING_FEED_7 | 476 | 19 | Field headers r1 (19 cols — no band row) | 0 |
| 4 | Sheet2 (ID list) | 1615 | 1 | No header — single-column ID list | 0 |
| 5 | Queries | 2 | 1 | No header — question text | 0 |
| 6 | Analysis_Notes | 7 | 2 | Meta rows only | 0 |
| 7 | Analysis Sheet - Detail | 562 | 3 | 1 (`FIELD_NAME`, `TEXTVALUE`, `FIELD_NO`) | 0 |
| 8 | Analysis Sheet - Compound | 236 | 10 | 1 (10 cols: `Field`, `Field Name`, `Mandatory or Situational`, `Source`, `Format`, `Size`, `Start`, `End`, `Record Analysis` x2) | 0 |
| 9 | Sample Records | 3 | 1 | No header — raw record samples | 0 |
| 10 | Sheet1 (legacy crosswalk) | 587 | 17 | 1 (17 cols: Source mapping vs legacy columns) | 0 |

**MAPPING_FEED_7 field headers r1 (19 cols):**
`Field ID`, `Field Name`, `Mandatory or Situational`, `Column Description`, `Comments`, `Format`, `Size`, `PHI/PII Field`, `Stage Schema`, `Stage Table Name`, `Stage Table - Column Name`, `Stage Table - DataType`, `Standard Schema`, `Standard Table Name`, `Standard Table - Column Name`, `Standard Data Type`, `Mandatory Fields (Include in DQ Check)`, `Recycle Flag`, `Comments`

### Pair 8 — STTM (Family A)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | FEED_8_LAYOUT | 446 | 27 | Meta r1-r6; band r7 (3 groups); field headers r8 (21 cols) | 145 |

**Single-sheet workbook.** Very high merge count (145) due to multi-segment layout (HR/DR/TR/FT record types spanning many rows with merged segment labels).

**FEED_8_LAYOUT meta rows (r1-r6):**
```
r1  File Names             = [value]
r2  Last Update Date       = [value]
r3  Version                = [value]
r4  LOB                    = [value]
r5  Target table Name Desc = [value]
r6  Feed Type              = [value]
```

**FEED_8_LAYOUT band row r7:** `Header Record` (label) | `Staging Layer` | `Standard Layer`

**FEED_8_LAYOUT field headers r8 (21 cols):**
`count`, `Sr. No`, `Input File`, `Output Flat File layout`, `Data Definition`, `PII`, `Primary Key`, `Critical Data`, `NOT NULL`, `Workspace`, `Catalog`, `Schema`, `TableName`, `ColumnName`, `DataType` — repeated for Stage and Standard.

### Pair 9 — STTM (Family E)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | Summary | 37 | 8 | 1 (`S.No`, `Source`, `Source Type`, `Name`, `Table Description`, `Total Count`, `Load strategy(Stage)`, `Load strategy(std)`) | 0 |
| 2 | MAPPING_FEED_9 | 1400 | 26 | Band r1 (3 groups merged); field headers r2 (24 cols) | 3 |
| 3 | Sheet2 (column template) | 13 | 2 | Meta rows — column-name : sample-value | 0 |
| 4 | Log | 7 | 3 | 2 (`Version`, `Date`, `Description`) | 0 |
| 5 | Sheet1 (column list) | 12 | 2 | Single-col label list | 0 |

**MAPPING_FEED_9 band row r1:** `Source Tables` | `Target - DL Staging Layer` | `Target - DL Standard Layer`

**MAPPING_FEED_9 field headers r2 (24 cols):**
`DataBase`, `Schema`, `TableName`, `ColumnName`, `Key (Y/N)`, `Required`, `Length`, `Data Type`, `Column Description`, `Column Long Description`, `PII`, `Critical Data elements`, `Workspace`, `Catalog`, `Schema`, `TableName`, `ColumnName`, `Data Type` — repeated for Stage and Standard.

Note: Source is a **database** (not a file) — headers include DataBase / Schema / TableName for source.

### Pair 10 — STTM (Family E)

| Sheet | Anonymised Name | Rows | Cols | Header Row | Merged |
| --- | --- | --- | --- | --- | --- |
| 1 | Version | 4 | 4 | 2 (`Date`, `Version`, `Author(s)`, `Description of Version/Changes`) | 0 |
| 2 | Outbound_REGION_A | 16388 | 19 | Meta r2; band r4 (3 groups merged); field headers r5 (17 cols) | 4 |
| 3 | Inbound_REGION_A | 124 | 20 | Meta r2; band r4; field headers r5 (20 cols) | 4 |
| 4 | Inbound_REGION_B_Adult | 209 | 18 | Meta r2; band r4; field headers r5 (18 cols) | 2 |
| 5 | Inbound_REGION_B_Child | 212 | 18 | Meta r2; band r4; field headers r5 (18 cols) | 2 |
| 6 | Mapping (vendor spec) | 117 | 5 | 1 (`Field`, `Value/Question`, `Result Values for File Spec`, `Type`, `Required?`) | 0 |

**Outbound field headers r5 (17 cols):**
`Source Column Name`, `Nullable ?`, `Description`, `PII (Y/N)`, `Workspace`, `Catalog`, `Stage Schema`, `Stage Table Name`, `Stage_Column_Name`, `Datatype`, `Workspace`, `Catalog`, `Standard Schema`, `Standard Table Name`, `Standard Column_Name`, `Datatype`, `Comments`

**Inbound_REGION_A field headers r5 (20 cols):**
`Survey Item #`, `Data Field`, `PII Y/N`, `Type`, `Mandatory?`, `Value/Question`, `Description`, `Workspace`, `Catalog`, `Stage Schema`, `Stage Table Name`, `Stage Column Name`, `Stage DataType`, `Workspace`, `Catalog`, `Standard Schema`, `Standard Table Name`, `Standard Column Name`, `Standard Data Type`, `Comments`

**Inbound_REGION_B (Adult/Child) field headers r5 (18 cols):**
`Survey Item #`, `Data Field`, `Description`, `PII Field`, `Mandatory?`, `Workspace`, `Catalog`, `Stage Schema`, `Stage Table Name`, `Stage Column Name`, `Stage DataType`, `Workspace`, `Catalog`, `Standard Schema`, `Standard Table Name`, `Standard Column Name`, `Standard Data Type`, `Comments`

Note: Row count 16,388 on Outbound sheet is an openpyxl artefact — actual populated rows are much smaller.

---

## 2. FRD Documents

### Document Families

Two FRD structural families:

| Family | Description | Pairs |
| --- | --- | --- |
| **F1 – Six Metadata Sections** | Uses python-docx Heading styles: none. Document body is a sequence of Word tables. Six metadata section tables (Descriptive, Structural, Administrative, Technical, Data Quality, Vendor) each follow the same 3-column pattern: row 0 = section title, row 1 = Name, row 2 = Description, row 3 = Functional Requirement, rows 4+ = label:value pairs. Additional tables for version history, LOB crosswalk, ACD items, stakeholders, solution requirements, approvers, glossary, references. | 1, 2, 3, 4, 5, 6, 7 |
| **F2 – Solution Requirements (no metadata sections)** | Uses Heading 1 and/or Heading 4 styles. No dedicated Descriptive/Structural/Administrative/Technical/Data Quality/Vendor metadata tables. Instead, each functional requirement is a separate "Solution Requirement" table (10 rows x 4 cols) with: Name, Business Requirement, Functional Requirement, [metadata section label], Impact Details, Solution Acceptance Criteria, Priority, Source/Reference, Traced Requirements, IS Owner. Metadata labels appear as row-4 cell values (Descriptive Metadata, Structural Metadata, etc.) rather than as table titles. | 8, 9, 10 |

### FRD Structural Metadata Labels (Family F1)

The six metadata section tables use these label texts in column 1 (after the section-name prefix).
✓ = value present; ∅ = label present but value blank/missing.

#### Descriptive Metadata labels
```
Data Source                    ✓ in all 7
Object Name                   ✓ in 1,3,4,6; ∅ in 2,5,7
Description                   ✓ in 1,3,4,6; ∅ in 2,5,7
Frequency                     ✓ in all 7
LOBs                          ✓ in all 7
Tags/Keywords                 ✓ in 1,3,4,6; ∅ in 2,5,7
Government Program            ✓ in all 7
Inbound Ingestion             ✓ in all 7
SFG template (Y/N)            ✓ in all 7
SR# for SFG Template          ✓ in all 7
Data Catalog Entry            ✓ in all 7
Impact Details                ∅ in all 7
Solution Acceptance Criteria   ✓ in 1,3,4,6; ∅ in 2,5,7
Traced/Related Requirements   ✓ in 1,3; ∅ in 2,4,5,6,7
IS Owner                      ✓ in 1,4,6; ∅ in 2,3,5,7
```

#### Structural Metadata labels
```
Object/data Format                     ✓ in all 7
Target Catalog and Schema        [variant: "Target Schema" in 2,3,4,5,7]
Target Table Name                      ✓ in 1,2,3,4,6; ∅ in 5,7
Domain and Subdomain                   ✓ in all 7
Load Strategy STG                      ✓ in all 7
Load Strategy STD                [variant: "Load Strategy STD (View)" in 1]
Load Strategy Consumption (EDH, BSL)   ✓ in 1,3,4,6; ∅ in 2,5,7
Archive Schedule                       ✓ in 1,3,4,6; ∅ in 2,5,7
Source Data Dictionary                  ✓ in all 7
ADLS Location                          ✓ in 1,3,4,5,6,7; ∅ in 2
Inbound File Folder Path         [variant: "Inbound/outbound File Folder Path" in 2]
```

#### Administrative Metadata labels
```
Business Owner                 ✓ in all 7
Technical Owner                ✓ in all 7
Business Steward (SMEs)        ✓ in 1,3,4,5,6; ∅ in 2,7
Technical Steward (SMEs)       ✓ in 1,3,4,6; ∅ in 2,5,7
Contact Information (Internal) ✓ in 1,3,4,6; ∅ in 2,5,7
Contact Information (External) ✓ in 1,3,4,6; ∅ in 2,5,7
Data Custodian                 ✓ in 1,3,4,5,6,7; ∅ in 2
Access Rights/Permissions      ✓ in all 7
Access Exclusions              ✓ in all 7
Record Retention Schedule      ✓ in all 7
```

#### Technical Metadata labels
```
Business Rules                 ✓ in all 7
Filter Criteria                ✓ in 1,3,4,6; ∅ in 2,5,7
Data Definitions               ✓ in all 7
Critical Data Elements         ✓ in 1,3,4,6; ∅ in 2,5,7
PII Fields                     ✓ in all 7
Transformation Logic           ✓ in all 7
Business Key                   ✓ in all 7
Primary Key                    ✓ in all 7
Foreign Key(s)                 ✓ in all 7
Unique Key(s)                  ✓ in all 7
Service Level Agreement        ✓ in 1,3,4,6; ∅ in 2,5,7
```

#### Data Quality labels (row labels are not named — they are positional DQ rule rows)
```
Uniqueness/Duplicate Record check/reject (HARD - In pipeline)
Incomplete Record Rejection Process (HARD - In pipeline)
Record Recycle Process (HARD - In pipeline)
+ up to 8 additional DQ rule rows (count varies per FRD)
```

#### Vendor Metadata labels
```
Vendor Name                    ✓ in all 7
Vendor Abbreviation            ✓ in all 7
Vendor Relationship Manager    ✓ in all 7 (appears twice in 2,5,7)
Service Grouping               ✓ in 1,3,4,6; ∅ in 2,5,7
Data Type                      ✓ in 1,3,4,6; ∅ in 2,5,7
Vendor Type Agreement          ✓ in 1,3,4,6; ∅ in 2,5,7
Delegated Entity               ✓ in 1,3,4,6; ∅ in 2,5,7
```

### FRD Label Variants Across Documents

| Canonical Label | Variants Seen |
| --- | --- |
| Target Catalog and Schema | `Target Catalog and Schema` (pair 1,6), `Target Schema` (pairs 2,3,4,5,7) |
| Load Strategy STD | `Load Strategy STD (View)` (pair 1), `Load Strategy STD` (pairs 2-7) |
| Inbound File Folder Path | `Inbound File Folder Path` (pairs 1,3,4,5,6,7), `Inbound/outbound File Folder Path` (pair 2) |
| Functional Requirement | `Functional Requirement` (most), `Functional Requirement:` (with colon, pairs 8,9) |
| Business Requirement | `Business Requirement` (most), `Business \nRequirement` (with newline, pairs 8,9,10) |

### FRD Family F2 (Pairs 8, 9, 10) — Solution Requirement Tables

These FRDs embed metadata labels inside Solution Requirement tables rather than
standalone metadata-section tables. Each SR table has 10-11 rows x 4 cols:

```
Row 0: Solution Requirement: N
Row 1: Name = [requirement name]
Row 2: Business Requirement = [text]
Row 3: Functional Requirement = [text]
Row 4: [Metadata Section Label] = [empty or text]   ← key structural signal
Row 5: Impact Details
Row 6: Solution Acceptance Criteria
Row 7: Priority / Source/Reference
Row 8: Traced/Related Requirements
Row 9: IS Owner
```

Metadata section labels found in Row 4 across F2 FRDs:
* `Descriptive Metadata` (pair 9)
* `Structural Metadata` (pairs 8, 9)
* `Administrative Metadata` (pairs 8, 9)
* `Technical Metadata` (pairs 8, 9)
* `Data Quality` / `Data Quality Considerations/Options` (pairs 8, 9, 10)
* `Vendor Metadata` (pair 8)
* `Reject /Recycle Process` (pair 9)
* `Email` (pair 8)

Pair 10 has 4 Solution Requirement tables (2.1, 2.2, 2.3, 2.4) — none carry
traditional metadata section labels in Row 4. Metadata is embedded in free text.

**Additional FRD table counts:**

| Pair | Total Tables | Heading Styles |
| --- | --- | --- |
| 1 | 16 | None |
| 2 | 40 | None |
| 3 | 17 | None |
| 4 | 17 | None |
| 5 | 40 | None |
| 6 | 16 | None |
| 7 | 40 | None |
| 8 | 14 | None |
| 9 | 30 | Heading 1 (8), Heading 4 (9) |
| 10 | 25 | None |

Pairs 2, 5, 7 have 40 tables each — these FRDs have two complete sets of
metadata sections (one per sub-domain or feed) plus duplicated NFR placeholder tables.

---

## 3. VDD (Vendor Data Dictionary) Workbooks

All 10 VDDs are `.xlsx` files. All follow the same two-tier structure:
a `FILES` sheet (file-level metadata) plus one or more field sheets.

### FILES Sheet (universal across all 10)

Header row 1 (10 cols):
`File Name Pattern`, `File Title`, `Format`, `Delimiter`, `Delivery Cadence`,
`Content Description`, `Field Sheet`, `Multi Record Type`, `Record Type Field`, `Header Row`

Row count in FILES sheet ranges from 2 (single file) to 37 (multi-table source).

### Field Sheets — Header Variants

Three header patterns observed:

| Pattern | Header Columns | Position Style | Pairs |
| --- | --- | --- | --- |
| **V1 — Full Position (11 cols)** | `Position`, `Field Name`, `Data Type`, `Start Position`, `End Position`, `Length`, `Required`, `PHI/PII`, `Key`, `Segment`, `Description` | Start + End + Length | 1, 3, 4, 7, 8 |
| **V2 — Length Only (9 cols)** | `Position`, `Field Name`, `Data Type`, `Length`, `Required`, `PHI/PII`, `Key`, `Description`, `Example Value` | Length only | 2, 5, 10 |
| **V3 — DB Table (8 cols)** | `Position`, `Field Name`, `Data Type`, `Length`, `Required`, `PHI/PII`, `Key`, `Description` | Length only | 6, 9 |

### VDD Per-Pair Detail

| Pair | File Type | Field Sheets | Multi-File? | Total Field Rows | Position Style | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | .xlsx | 1 (FEED_1 Fields) | Y (HDR/DTL/TRL via Segment col) | 77 | Start+End+Length | Single sheet, segments identified by `Segment` column |
| 2 | .xlsx | 3 (one per source file) | Y (3 files) | 91+272+51=414 | Length only | One field sheet per CSV file |
| 3 | .xlsx | 1 (Eligibility Fields) | N | 296 | Start+End+Length | Fixed-width file |
| 4 | .xlsx | 1 (FEED_4 Fields) | N | 136 | Start+End+Length | Fixed-width file |
| 5 | .xlsx | 1 (Claims Fields) | N | 155 | Length only | Pipe-delimited file |
| 6 | .xlsx | 1 (DB table fields) | N | 169 | Length only | Source is a database table |
| 7 | .xlsx | 1 (Rx Claims Fields) | Y (D/CD/CE segments) | 460 | Start+End+Length | NCPDP-style with compound records |
| 8 | .xlsx | 1 (Layout Fields) | Y (HR/DR/TR/FT segments) | 387 | Start+End+Length | Multi-segment fixed-width |
| 9 | .xlsx | 36 (one per DB table) | Y (36 tables) | ≈ 1,100 total | Length only | Each table is a separate sheet |
| 10 | .xlsx | 4 (Outbound+3 Inbound) | Y (4 files, 2 regions) | 38+98+185+212=533 | Length only | Two regions, Adult/Child split |

---

## 4. Fields Left Empty Per Pair (and Why)

### FRD Empty Fields

| Pair | Labels Present but Value Blank | Labels Absent |
| --- | --- | --- |
| 1 | Impact Details (all 6 sections), Description (Admin, DQ, Vendor), Traced/Related Requirements (Structural, Admin) | None — all canonical labels present |
| 2 | Object Name, Description (Descriptive), Tags/Keywords, Load Strategy Consumption, Archive Schedule, ADLS Location, many Admin sub-fields, most DQ rows, Service Grouping, Data Type, Vendor Type Agreement, Delegated Entity | Functional Requirement (all sections blank) |
| 3 | Description (Admin), Impact Details (all 6) | IS Owner (Descriptive, Structural, Admin, Tech) |
| 4 | Functional Requirement (5/6 sections) | None — all labels present |
| 5 | Object Name, Description (Descriptive), Tags/Keywords, Target Table Name, Inbound File Folder Path, Load Strategy Consumption, Archive Schedule, most Admin sub-fields, SLA, most DQ rows, all Vendor sub-fields past Abbreviation | Functional Requirement (all blank) |
| 6 | Description (Admin), Impact Details (all 6) | IS Owner on some sections |
| 7 | Same pattern as pair 5 (template-B FRD) | Functional Requirement (all blank) |
| 8 | No metadata section tables — SR tables have sparse Row 4 content | All six metadata section tables absent (F2 family) |
| 9 | No metadata section tables — SR tables reference metadata as labels only | All six metadata section tables absent (F2 family) |
| 10 | No metadata section tables — SR tables contain requirement text only | All six metadata section tables absent (F2 family); Domain/SubDomain in a separate 2x2 table |

### STTM Empty Fields

| Pair | Structural Gaps |
| --- | --- |
| 1 | File Delimiter (r5), Last Update Date (r6), Version (r7), Feed Type (r10), Notes (r12) — all meta labels present but values blank |
| 2 | No meta rows in mapping sheets (values embedded directly in FILE_DETAILS) |
| 3 | Meta rows in STTM sheet only: r1 (File Name = ref to another sheet), r2 (Version = value) |
| 4 | Only r1 (File Name) meta row present |
| 5 | r2 (File Generator) blank |
| 6 | No meta rows in mapping sheet (source is database table) |
| 7 | No meta rows in mapping sheet |
| 8 | All 6 meta rows populated |
| 9 | No meta rows — source is database; Summary sheet serves as file-details equivalent |
| 10 | Only r2 (Target Table Description) meta row per sheet |

### VDD Empty Fields

| Pair | Gaps |
| --- | --- |
| 1 | Delimiter blank (fixed-width); PHI/PII and Key columns mostly blank |
| 2 | Length column blank throughout; Start/End Position absent; Example Value present |
| 3 | Required, PHI/PII, Key, Segment columns mostly blank |
| 4 | Required, PHI/PII, Key, Segment columns mostly blank |
| 5 | Start/End Position absent; Example Value column present but mostly empty |
| 6 | Delimiter, Multi Record Type, Record Type Field, Header Row blank (DB table source); Required column blank; Key values use NULL/NOT NULL |
| 7 | Start Position and End Position columns present but blank (NCPDP uses Field ID not position); Length populated |
| 8 | Start/End/Length columns present but blank (layout derives positions from segment rules) |
| 9 | Delimiter, Multi Record Type, Record Type Field, Header Row blank (DB table source); all 36 field sheets have Length populated |
| 10 | Length column blank; Data Type partially blank on outbound sheet; some field sheets have values bleeding into wrong columns |

---


