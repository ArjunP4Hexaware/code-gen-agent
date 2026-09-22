# SHAPES_ROUND2 — Structural Deep-Dive for Pairs 2–10

> **Purpose**: Complements SHAPES_FOR_PORT with per-table FRD anatomy (pairs 8–10),
> STTM band/header detail (pair 7), STTM sizing (pair 3), segment banners (pair 5),
> audit rows (pair 6), format metadata (pair 4) and FILE_DETAILS (pair 2).
> Structure only — all file names, sheet names, vendor names, feed names,
> table names and column names that are business terms replaced with `<TOKEN_n>`.
> Structural words kept verbatim.

---

## Token Table

| Token | Category | Scope |
| --- | --- | --- |
| `<TOKEN_1>` | file | pair 8 FRD docx |
| `<TOKEN_2>` | file | pair 9 FRD docx |
| `<TOKEN_3>` | file | pair 10 FRD docx |
| `<TOKEN_4>` | file | pair 7 STTM xlsx |
| `<TOKEN_5>` | file | pair 3 STTM xlsx |
| `<TOKEN_6>` | file | pair 5 STTM xlsx |
| `<TOKEN_7>` | file | pair 6 STTM xlsx |
| `<TOKEN_8>` | file | pair 4 STTM xlsx |
| `<TOKEN_9>` | file | pair 4 FRD docx |
| `<TOKEN_10>` | file | pair 2 STTM xlsx |
| `<TOKEN_11>` | sheet | pair 7 mapping sheet |
| `<TOKEN_12>` | sheet | pair 5 mapping sheet |
| `<TOKEN_13>` | sheet | pair 6 mapping sheet |
| `<TOKEN_14>` | sheet | pair 4 crosswalk sheet |
| `<TOKEN_15>` | sheet | pair 4 rules sheet |
| `<TOKEN_16>` | sheet | pair 7 team notes sheet |
| `<TOKEN_17>` | sheet | pair 7 analysis detail sheet |
| `<TOKEN_18>` | sheet | pair 7 analysis compound sheet |
| `<TOKEN_19>` | vendor | pair 7 |
| `<TOKEN_20>` | vendor | pair 5 |
| `<TOKEN_21>` | vendor | pair 2 |
| `<TOKEN_22>` | vendor | pairs 4, 6 |
| `<TOKEN_23>` | project | pair 8 |
| `<TOKEN_24>` | project | pair 9 |
| `<TOKEN_25>` | project | pair 10 |
| `<TOKEN_26>` | project | pairs 3, 4, 6 |
| `<TOKEN_27>` | project | pair 2 |
| `<TOKEN_28>` | feed | pair 8 |
| `<TOKEN_29>` | feed | pair 9 source |
| `<TOKEN_30>` | feed | pair 7 |
| `<TOKEN_31>` | feed | pair 5 |
| `<TOKEN_32>` | feed | pair 10 outbound |
| `<TOKEN_33>` | feed | pair 10 inbound |
| `<TOKEN_34>` | schema | stg layer (pairs 7, 4) |
| `<TOKEN_35>` | schema | std layer (pair 7) |
| `<TOKEN_36>` | table | pair 7 target |
| `<TOKEN_37>` | schema | pair 5 stg |
| `<TOKEN_38>` | schema | pair 5 std |
| `<TOKEN_39>` | table | pair 5 target |
| `<TOKEN_40>` | schema | pair 6 stg region-1 |
| `<TOKEN_41>` | schema | pair 6 stg exchange |
| `<TOKEN_42>` | table | pair 6 source and target |
| `<TOKEN_43>` | table | pair 4 target |
| `<TOKEN_44>` | catalog | dlk catalog |
| `<TOKEN_45>` | catalog | std catalog |
| `<TOKEN_46>` | schema | pair 6 std |
| `<TOKEN_47>` | database | pair 6 source db |
| `<TOKEN_48>` | person | pair 8 author |
| `<TOKEN_49>` | person | pair 8/9 approver |
| `<TOKEN_50>` | person | pair 9 author |
| `<TOKEN_51>` | person | pairs 7, 10 author |
| `<TOKEN_52>` | person | pairs 9, 10 reviewer |
| `<TOKEN_53>` | person | pair 5 author |
| `<TOKEN_54>` | person | pair 6 author |
| `<TOKEN_55>` | column | pair 7 ID-list column |
| `<TOKEN_56>` | column | pair 4 first source field |
| `<TOKEN_57>` | feed | pair 2 demographics file |
| `<TOKEN_58>` | feed | pair 2 analytics file |
| `<TOKEN_59>` | feed | pair 2 individual-risk file |
| `<TOKEN_60>` | person | pair 9 signoff-1 |
| `<TOKEN_61>` | person | pair 9 signoff-2 |
| `<TOKEN_62>` | person | pair 10 signoff |
| `<TOKEN_63>` | file | pair 8 STTM reference |
| `<TOKEN_64>` | file | pair 9 STTM reference |
| `<TOKEN_65>` | server | pair 6 server names |
| `<TOKEN_66>` | feed | pair 4 file pattern |
| `<TOKEN_67>` | feed | pair 7 file pattern |
| `<TOKEN_68>` | feed | pair 5 file pattern |
| `<TOKEN_69>` | contact | pair 4 internal contacts |
| `<TOKEN_70>` | feed | pair 10 vendor spec sheet |

---

## 1. Pairs 8, 9, 10 — FRD Table-by-Table Anatomy

### 1.1 Pair 8 FRD — `<TOKEN_1>` (14 tables)

**Family F2** (Solution Requirements, no dedicated metadata section tables).

| Idx | Rows×Cols | Preceding Context | Row 0 (headers / labels) | Row 1 (first data) | Classification |
| --- | --- | --- | --- | --- | --- |
| 0 | 4×4 | [VerNo] `<TOKEN_23>`; [VerNo] `<TOKEN_28>` Load into Data Lake; [Main Document Title] Revision History | `Date`, `Version`, `Author(s)`, `Description of Version/Changes` | `12/15/25`, `1.0`, `<TOKEN_48>`, `Initial` | **boilerplate: revision-history** |
| 1 | 7×5 | [Document Heading 3] Document Scope; [Normal] scope paragraph; [Document Heading 2] Intended Audience | `Name`, `Role`, `Title`, `Plan (LOB)`, `Department` | `<TOKEN_49>`, `Approver`, `Manager - IS`, `Enterprise`, `EDO Management` | **boilerplate: audience** |
| 2 | 17×2 | [Document Heading 2] Definitions and Acronyms | `Acronym`, `Definition` | `AC`, `AmeriHealth Caritas` | **boilerplate: glossary** |
| 3 | 3×2 | [Document Heading 1] Solution Description; [Document Heading 2] Systems Overview | `Name`, `Description` | `System Overview`, `<TOKEN_28> files processed via scheduling …` | **boilerplate: systems-overview** |
| 4 | 8×3 | [List Paragraph] config note; [Document Heading 1] Functional/Non-Functional Requirements; [Document Heading 2] List of Functional requirements | `Functional Requirement #`, `Functional Requirement Definition`, `Business Requirement #` | `1`, `Descriptive Metadata for the ingestion of <TOKEN_28> into DL2.0`, `` | **requirement-index** |
| 5 | 9×4 | *(immediately after table 4)* | `[merged]`, `Solution Requirement: 1` | `Name`, `Descriptive Metadata for the ingestion of <TOKEN_28> into DL2.0` | **F2-solution-req (Descriptive)** |
| 6 | 10×4 | *(contiguous)* | `[merged]`, `Solution Requirement: 2` | `Name`, `Structural Metadata for the ingestion of <TOKEN_28> into DL2.0` | **F2-solution-req (Structural)** |
| 7 | 10×4 | | `[merged]`, `Solution Requirement: 3` | `Name`, `Administrative Metadata for the ingestion of <TOKEN_28> into DL2.0` | **F2-solution-req (Administrative)** |
| 8 | 10×4 | | `[merged]`, `Solution Requirement: 4` | `Name`, `Technical Metadata for the ingestion of <TOKEN_28> into DL2.0` | **F2-solution-req (Technical)** |
| 9 | 10×4 | | `[merged]`, `Solution Requirement: 5` | `Name`, `Data Quality for the ingestion of <TOKEN_28> into DL2.0` | **F2-solution-req (Data Quality)** |
| 10 | 10×4 | | `[merged]`, `Solution Requirement: 6` | `Name`, `Vendor Metadata for the ingestion of <TOKEN_28> into DL2.0` | **F2-solution-req (Vendor)** |
| 11 | 10×4 | | `[merged]`, `Solution Requirement: 7` | `Name`, `Email Notification on Failure` | **F2-solution-req (Notification)** |
| 12 | 4×3 | [Document Heading 3] Software Quality Attributes; [Normal] Not Applicable; [Document Heading 1] Stakeholder Signoff | `Approver Name`, `Signature/Proof`, `Date` | `<TOKEN_49>`, ``, `` | **boilerplate: signoff** |
| 13 | 4×3 | [Document Heading 1] Appendix; [Document Heading 2] Reference Documents | `Document Name`, `Description`, `Network Path` | `<TOKEN_63>`, `Mapping Document`, `SharePoint URL` | **boilerplate: references** |

**F2 pattern summary for pair 8:** 7 Solution Requirement tables (idx 5–11), each 9–10 rows × 4 cols. Row-0 col B–D merged with "Solution Requirement: N". Row-1 = `Name`; row-2 = `Business Requirement`; row-3 = `Functional Requirement`; row-4 = `[Metadata Section Label]` (Descriptive / Structural / Administrative / Technical / Data Quality / Vendor Metadata); row-5 = `Impact Details`; row-6 = `Solution Acceptance Criteria`; row-7 = `Priority`; row-8 = `Source/Reference`; row-9 = `Traced/Related Requirements` (when present).

---

### 1.2 Pair 9 FRD — `<TOKEN_2>` (30 tables)

**Family F2** (Solution Requirements), richer than pair 8 — 12 solution-req tables plus many non-functional requirement tables.

| Idx | Rows×Cols | Preceding Context | Row 0 | Row 1 | Classification |
| --- | --- | --- | --- | --- | --- |
| 0 | 4×4 | [VerNo] Waterfall Lite; [VerNo] `<TOKEN_24>`; [Main Document Title] Revision History | `Date`, `Version`, `Author(s)`, `Description of Version/Changes` | `12/23/2025`, `1.0`, `<TOKEN_50>`, `Initial Version.` | **boilerplate: revision-history** |
| 1 | 9×4 | [List Paragraph] scope text; [Document Heading 2] Intended Audience | `Name`, `Role`, `Title`, `Department` | `<TOKEN_52>`, `Reviewer`, `Director`, `Data Products` | **boilerplate: audience** |
| 2 | 13×2 | [Document Heading 2] Definitions and Acronyms | `Acronym`, `Definition` | `HR`, `Human Resources` | **boilerplate: glossary** |
| 3 | 9×4 | [Document Heading 2] As-Is Processes; [Body-New] narrative; [Document Heading 2] Assumptions, Constraints & Dependencies | `ID #`, `Name`, `Description`, `ACD Type` | `1`, `Data Accessibility`, `… accessible and can be connected to DL 2.0.`, `Assumptions` | **boilerplate: ACD** |
| 4 | 10×4 | [Heading 4] Functional Requirement 1 – `<TOKEN_29>` Integration | `[merged]`, `Solution Requirement: 1` | `Name`, `<TOKEN_29> Source system integration` | **F2-solution-req** |
| 5 | 10×4 | [Heading 4] Functional Requirement 2 – New Schemas | — | `Name`, `New Schemas creation in DL 2.0 Layers` | **F2-solution-req** |
| 6 | 10×4 | [Heading 4] Functional Requirement 3 – New Tables | — | `Name`, `New Tables creation in new HR Schema in DL 2.0` | **F2-solution-req** |
| 7 | 10×4 | [Heading 4] Functional Requirement 4 – Source Data | — | `Name`, `<TOKEN_29> data Extraction and ingestion into DL 2.0` | **F2-solution-req** |
| 8 | 10×4 | [Heading 4] Functional Requirement 5 – Target | — | `Name`, `HR Data Ingestion into Target - Data Lake 2.0` | **F2-solution-req** |
| 9 | 9×5 | [Heading 4] Functional Requirement 6 – Failure Notification | — | col-B/C merged: `CM Automation – File Ingestion – Process Failure Alert` | **F2-solution-req** |
| 10 | 10×4 | [Heading 4] Functional Requirement 7 – Administrative metadata | — | `Name`, `Administrative information for the HR data ingestion Process` | **F2-solution-req** |
| 11 | 10×4 | [Heading 4] Functional Requirement 8 – Technical metadata | — | `Name`, `Source to target metadata mapping (STTM)` | **F2-solution-req** |
| 12 | 10×4 | [Heading 4] Functional Requirement 9 – Data Quality | — | `Name`, `ETL Data Quality Rules` | **F2-solution-req** |
| 13 | 5×2 | [Document Heading 2] File Naming Conventions; [Document Heading 2] Business Rules | `Business Rule ID: 1` (merged) | `Name`, `NA` | **boilerplate: business-rule** |
| 14 | 3×3 | [Document Heading 2] Non-Functional Requirements; [Document Heading 2] Data Management | `Non-Functional Requirement ID:` (merged) | `Name`, `Data Management` | **NFR: Data Management** |
| 15 | 3×2 | [Document Heading 2] Data Migration | merged | `Name`, `Data Migration` | **NFR: Data Migration** |
| 16 | 3×3 | [Document Heading 2] Disaster Recovery Plan | merged | `Name`, `Disaster Recovery Plan` | **NFR** |
| 17 | 3×3 | [Document Heading 2] Legal/Regulatory | merged | `Name`, `Legal/ Regulatory Requirements` | **NFR** |
| 18 | 3×3 | [Document Heading 2] System Interference | merged | `Name`, `System Interference` | **NFR** |
| 19 | 3×4 | [Document Heading 2] Supportability | merged | `Name`, `Supportability Requirement` | **NFR** |
| 20 | 3×3 | [Document Heading 2] Performance Requirement | merged | `Name`, `Performance Requirement` | **NFR** |
| 21 | 3×3 | [Document Heading 2] Security Requirement | merged | `Name`, `Security Requirement` | **NFR** |
| 22 | 3×3 | [Document Heading 2] Software Quality Attributes | merged | `Name`, `Software Quality Attributes` | **NFR** |
| 23 | 3×2 | [Document Heading 2] Code Review | merged | `Name`, `Code Review` | **NFR** |
| 24 | 3×2 | [Document Heading 2] Service Level Agreement | merged | `Name`, `Service Level Agreement` | **NFR** |
| 25 | 3×2 | [Document Heading 2] Access | merged | `Name`, `Data Access` | **NFR** |
| 26 | 6×4 | [Heading 1] Technical Implementation | `Component`, `Description`, `Schema`, `Notes` | ``, ``, ``, `` | **boilerplate: tech-impl (empty)** |
| 27 | 5×4 | [Heading 1] Business Rules & Data Transformation | `Rule ID`, `Rule Description`, `Applicable Table/View`, `Transformation Logic` | *(empty)* | **boilerplate: biz-rules (empty)** |
| 28 | 6×5 | [Heading 1] Stakeholder Signoff | `Approver Name`, `Date`, `Signature/Proof`, `<TOKEN_60>` | ``, `<TOKEN_61>` | **boilerplate: signoff** |
| 29 | 5×4 | [Heading 1] Appendix; [Document Heading 3] Reference Documents | `Document Name`, `Description`, `Network Path`, `Attachment` | `<TOKEN_64>`, `Mapping Document`, `SharePoint URL`, `<TOKEN_64>` | **boilerplate: references** |

**F2 pattern summary for pair 9:** 9 Solution Requirement tables (idx 4–12), each preceded by a `[Heading 4]` with the requirement title. 12 Non-Functional Requirement tables (idx 14–25), each 3 rows × 2–4 cols with identical structure: row-0 merged NFR ID, row-1 Name, row-2 Description. Two empty template tables (idx 26–27).

---

### 1.3 Pair 10 FRD — `<TOKEN_3>` (25 tables)

**Family F2**, similar to pair 9 but with domain/subdomain table (idx 1) unique among F2 FRDs.

| Idx | Rows×Cols | Preceding Context | Row 0 | Row 1 | Classification |
| --- | --- | --- | --- | --- | --- |
| 0 | 4×4 | [VerNo] Waterfall Lite; [VerNo] `<TOKEN_25>`; [Main Document Title] Revision History | `Date`, `Version`, `Author(s)`, `Description of Version/Changes` | `09/12/2025`, `V1.0`, `<TOKEN_51>`, `Initial Version …` | **boilerplate: revision-history** |
| 1 | 2×2 | [Document Heading 1] Introduction; [Document Heading 2] Purpose; [List Paragraph] scope | `Domain`, `SubDomain` | `Care Management`, `Assessments` | **metadata: domain (unique to F2)** |
| 2 | 8×4 | [Document Heading 2] Intended Audience | `Name`, `Role`, `Title`, `Department` | `<TOKEN_52>`, `Reviewer`, `Director IS`, `CDO Management` | **boilerplate: audience** |
| 3 | 17×2 | [Document Heading 2] Definitions and Acronyms | `Acronym`, `Definition` | `ACFC`, `AmeriHealth Caritas Family of Companies` | **boilerplate: glossary** |
| 4 | 11×4 | [Document Heading 2] Assumptions, Constraints & Dependencies | `ID #`, `Name`, `Description`, `ACD Type` | `1`, `Data Accessibility`, `…accessible…`, `Assumptions` | **boilerplate: ACD** |
| 5 | 11×4 | [Document Heading 2] Solution Requirements; …Outbound Files Data Ingestion Requirements | `[merged]`, `Solution Requirement: 2.1` | `Name`, `Automated Data Ingestion for Outbound <TOKEN_25> Data …` | **F2-solution-req (Outbound)** |
| 6 | 11×4 | [Document Heading 2] Inbound Files Data Ingestion Requirements | `[merged]`, `Solution Requirement: 2.2 – Inbound File Data Ingestion` | `Name`, `Automated Data Ingestion for Inbound <TOKEN_25> Data …` | **F2-solution-req (Inbound region A)** |
| 7 | 11×4 | [Document Heading 2] Outbound – Amendments | `[merged]`, `Solution Requirement: 2.3 - Outbound File Amendments` | `Name`, `Amend the Target schema for the Outbound table in DL.` | **F2-solution-req (Amendments)** |
| 8 | 11×4 | [Document Heading 2] Inbound File Data Ingestion (region B) | `[merged]`, `Solution Requirement: 2.4 – Inbound File Data Ingestion` | `Name`, `Automated Data Ingestion for Inbound <TOKEN_25> Data …` | **F2-solution-req (Inbound region B)** |
| 9 | 5×2 | [Document Heading 2] Business Rules | `Business Rule ID: 1` (merged) | `Name`, `N/A` | **boilerplate: business-rule** |
| 10–22 | 3×2 to 3×4 | [Document Heading 2] Data Management / Data Migration / Email Notification / Disaster Recovery / Legal / System Interference / Supportability / Performance / Security / Software Quality / Code Review / SLA / Access | `Non-Functional Requirement ID: N` (merged) | `Name`, `[NFR title]` | **NFR (13 tables)** |
| 23 | 7×5 | [Document Heading 1] Stakeholder Signoff | `Approver Name`, `Date`, `Signature/Proof`, `<TOKEN_52>` | ``, `<TOKEN_62>` | **boilerplate: signoff** |
| 24 | 4×4 | [Document Heading 1] Appendix; [Document Heading 2] Reference Documents | `Document Name`, `Description`, `Network Path`, `Attachment` | `<TOKEN_70>`, `<TOKEN_25> Mapping`, `<TOKEN_70>`, `` | **boilerplate: references** |

**F2 pattern summary for pair 10:** 4 Solution Requirement tables (idx 5–8), numbered with sub-IDs (2.1, 2.2, 2.3, 2.4) distinguishing outbound vs. inbound and by region. 13 NFR tables (idx 10–22). Unique: table 1 is a 2×2 Domain/SubDomain table not seen in other F2 FRDs. Table 12 (Email Notification) is an expanded NFR (9 rows vs. the usual 3).

---

## 2. Pair 7 STTM — Band Row and Header Row Detail

**File:** `<TOKEN_4>` — 10 sheets, Family E.

### 2.1 Mapping sheet `<TOKEN_11>` — 476 rows × 19 cols

**Band row:** *none* — no merged band row exists. Layer grouping is implicit in the header-row prefixes.

**Header row = Row 1** (column letter → text):

```
A: Field ID
B: Field Name
C: Mandatory or Situational
D: Column Description
E: <TOKEN_19> Data Fields - Comments
F: Format
G: Size
H: PHI\PII Field
I: Stage Schema
J: Stage Table Name
K: Stage Table - Column Name
L: Stage Table - DataType
M: Standard Schema
N: Standard Table Name
O: Standard Table - Column Name
P: Standard Data Type
Q: Mandatory Fields (Include in DQ Check)
R: Recycle Flag ( Enabled for 7 Days)
S: Comments
```

**Merged ranges on mapping sheet:** 0

### 2.2 The 6 Layout Questions (verbatim from profile) with Candidate Columns

The layout recognizer resolves these six structural questions for the mapping sheet:

**Q1. Where is the band row?**
→ *null* (no band row). Note: `"no band row; layer prefixes in header row 1"`.

**Q2. Where is the header row?**
→ Row 1. Columns A–S populated.

**Q3. Which columns form the source band?**
→ Cols 1–8 (A–H). Roles: `ordinal`=A, `field_name`=B, `required`=C, `description`=D, `comments`=E, `source_type`=F, `length`=G, `pii`=H.

**Q4. Which columns form the stage band?**
→ Cols 9–12 (I–L). Roles: `schema`=I, `table`=J, `column`=K, `target_type`=L.

**Q5. Which columns form the standard band?**
→ Cols 13–16 (M–P). Roles: `schema`=M, `table`=N, `column`=O, `target_type`=P.

**Q6. Which columns form the rules band?**
→ Cols 17–19 (Q–S). Roles: `dq_mandatory`=Q, `recycle_flag`=R, `comments`=S.

### 2.3 Auxiliary Sheets

| Sheet | Rows×Cols | Kind | Header Row | Notes |
| --- | --- | --- | --- | --- |
| Version History | 7×8 | version | r6 (`Date`, `Version`, `Author(s)`, `Description …`) | Band r5 merged E5:H5 (Revision History) |
| File Details | 6×5 | file_details | r1 (`Vendor`, `FileName`, `File Description`, `Location`, `Frequency (Historical Drops)`) | Vendor=`<TOKEN_19>`, file pattern=`<TOKEN_67>` |
| Sheet2 | 1615×1 | ignore | *(none)* | Single column: `<TOKEN_55>` values |
| Queries | 2×1 | ignore | *(none)* | Two question strings |
| `<TOKEN_16>` | 7×2 | ignore | *(none)* | Summary notes and field names |
| `<TOKEN_17>` | 562×3 | ignore | r1 (`FIELD_NAME`, `TEXTVALUE`, `FIELD_NO`) | Sample detail-record field analysis |
| `<TOKEN_18>` | 236×10 | ignore | r1 (10 cols: `Field`, `Field Name`, `Mandatory or Situational`, `Source`, `Format`, `Size`, `Start`, `End`, record-analysis × 2) | Compound-record analysis |
| Sample Records | 3×1 | ignore | *(none)* | Raw fixed-width sample lines (Detail, Compound-D, Compound-E) |
| Sheet1 | 587×17 | ignore | r1 (17 cols: `Source`, `Column Map Against …`, `Mandatory or Situational`, `Source`, `Format`, `Size`, `Start`, `End`, `What to expect?`, `Schema`, `Table Name`, `Column`, `… Comments`, `… Clarifications?`) | Legacy crosswalk |

---

## 3. Pair 3 STTM — File Size and Sheet Dimensions

**File:** `<TOKEN_5>`

| Metric | Value |
| --- | --- |
| File size | 9,616,661 bytes (9,391 KB) |
| Sheet count | 4 |

| Sheet | max_row | max_column | Merged Ranges | Total Cells (max_row × max_column) | >100k Cells |
| --- | --- | --- | --- | --- | --- |
| Version Control | 9 | 4 | 0 | 36 | No |
| Layout | 336 | 15 | 0 | 5,040 | No |
| STTM | 1,048,538 | 34 | 4 | 35,650,292 | **Yes** |
| FileNames | 24 | 3 | 0 | 72 | No |

**Note:** The STTM sheet's `max_row=1,048,538` is an openpyxl artefact (Excel internal limit minus header). Actual populated rows ≈ 336 (matching Layout). The 4 merged ranges on the STTM sheet are band-header merges.

---

## 4. Supplementary Shapes — Pairs 5, 6, 4, 2

### 4.1 Pair 5 STTM — Segment Banner Texts

**File:** `<TOKEN_6>`, sheet `<TOKEN_12>` (170r × 33c, 5 merged ranges).

Meta rows r1–r9 serve as segment banners preceding the mapping data:

```
r1  File(s)         = <TOKEN_68>
r2  File Generator  = [empty]
r3  File Location   = [path value]
r4  LOB             = [value]
r5  File frequency  = [value]
r6  Domain          = [value]
r7  Sub-Domain      = [value]
r8  NOTE            = "Fields Id to be separated by "|" delimiter and field values to be in double (") quotes."
r9  File type       = [value]
```

**Band row r10** (3 merged groups):
- A10:K10 → `Source Layout`
- L10:V10 → `Stage Layer`
- W10:AG10 → *(blank — Standard Layer implied)*

Additional merged range: `L59:AG59` (mid-sheet gap), `A63:AG63` (section break).

**Sheet2** (88r × 3c) and **Sheet3** (88r × 1c) hold unmapped-field expansion notes — rows like:
`Revenue Code 2 ( These fields will be not available in the source layout file, please map to the empty or null value…)`
Pattern repeats for Revenue Code/HCPCS/Units/Charges × positions 2–23.

**Sheet1** (132r × 3c) = DQ rules sheet: `FieldName`, `DQ Rules`, `DataType` — field names are business terms for an outreach/member feed (e.g., `<TOKEN_31> field names`).

### 4.2 Pair 6 STTM — Audit Rows' Type Cells

**File:** `<TOKEN_7>`, sheet `<TOKEN_13>` (212r × 24c, 3 merged ranges).

**Band row = r2** (3 merged groups):
- B2:I2 → `Source table`
- L2:Q2 → `Stage Layer`
- S2:X2 → `STD layer`

**Header row = r3** (22 cols): `Inscope for Implementation`, `SERVER NAME`, `TABLE_CATALOG`, `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME`, `Primary Key`, `DATA_TYPE`, `NULL/NOT NULL`, `Load Rules`, [gap at K], `Workspace`, `Catalog`, `Schema`, `TableName`, `ColumnName`, `DataType`, [gap at R], `Workspace`, `Catalog`, `Schema`, `TableName`, `ColumnName`, `DataType`.

**Column A values** (the scope/audit marker column): three distinct values:
- `Inscope for <TOKEN_22> Implementation` (header row 3 label)
- `In Scope` (data rows 4–212)
- `Out of scope` (some rows)

**Audit rows** (rows 208–212) — identified by column J = `Audit Column`:

| Row | Col A | Col J (Load Rules) | Col P (Stage ColumnName) | Col W (Std ColumnName) |
| --- | --- | --- | --- | --- |
| 208 | In Scope | Audit Column | DELETE_FLAG | *(empty)* |
| 209 | In Scope | Audit Column | *(empty)* | SRC_FILE_NAME |
| 210 | In Scope | Audit Column | REC_CREATION_TIME | REC_CREATION_TIME |
| 211 | In Scope | Audit Column | REC_UPDATED_TIME | REC_UPDATED_TIME |
| 212 | In Scope | Audit Column + Hard code note | REGION_NAME | REGION_NAME |

Audit rows have no source-table columns (B–I empty) — they are target-only injected columns. The type cells for audit columns: `tinyint` (DELETE_FLAG), `string` (SRC_FILE_NAME, REGION_NAME), `timestamp(YYYY-MM-DD HH:MM:SS)` (REC_CREATION_TIME, REC_UPDATED_TIME).

**Server details sheet** (22r × 3c): `Server`, `Database`, `Environment` — lists `<TOKEN_65>` names across PROD/QA/DEV environments for regions REG_1, REG_2, REG_5, REG_6, REG_7, XCH_1, MDC_1.

### 4.3 Pair 4 — FRD File Format Cell and STTM Meta Format Row

**FRD:** `<TOKEN_9>`, Table 6 (Structural Metadata), Row 4:
- Column 0: `Structural Metadata`
- Column 1: `Object/data Format`
- Column 2: `.xlsx`

**STTM:** `<TOKEN_8>`, sheet `STTM` (148r × 28c).

Meta row r1: `File Name` = `<TOKEN_66>`

Band row r4 (from SHAPES_FOR_PORT): `Source Data` | `Data Rules` | `Target Table - Staging Layer` | `Target Table - Standard Layer`

Header row r5 (25 cols): `Sl. No.`, `Field Name`, `Type`, `Start`, `End`, `Len`, `Description`, [gap], `Data Definition`, `PII`, `Primary Key`, `Critical Data`, `Not NULL`, `LOAD Rule`, [gap], `Workspace`, `Target Catalog`, `Target Schema Name in Lakehouse`, `Target Table Name in Lakehouse` — repeated for stage and standard.

Row 6 (first data): `1`, `<TOKEN_56>`, `A/N`, `1`, `25`, `25`, field description, [gap], field definition, [gap], [gap], [gap], [gap], `Straight move`, [gap], workspace, `<TOKEN_44>`, `<TOKEN_34>`, `<TOKEN_43>`.

### 4.4 Pair 2 STTM — FILE_DETAILS Rows 1–8

**File:** `<TOKEN_10>`, sheet `FILE_DETAILS` (6r × 5c, 0 merged ranges).

| Row | A (Vendor) | B (FileName) | C (File Description) | D (Location) | E (Frequency) |
| --- | --- | --- | --- | --- | --- |
| 1 *(header)* | Vendor | FileName | File Description | Location | Frequency |
| 2 | `<TOKEN_21>` | `<TOKEN_57>` | Data Quality Rules Provided in the Mapping document. | *(empty)* | Monthly |
| 3 | `<TOKEN_21>` | `<TOKEN_58>` | Data Quality Rules … Community Risk file … | *(empty)* | Yearly twice (January/February, August/September) |
| 4 | `<TOKEN_21>` | `<TOKEN_59>` | Data Quality Rules … Individual Risk file … | *(empty)* | Monthly |
| 5 | *(empty row)* | | | | |
| 6 **[annotation]** | `Amber italic DataType = the vendor gave neither a data type nor an example value for this column, so the ACFC default applied.` | | | | |

**Annotation row (r6):** spans column A only; describes a colour-coding convention applied to DataType cells in the MAPPING sheets. This is not a data row — it is a formatting note that the extractor must skip.
