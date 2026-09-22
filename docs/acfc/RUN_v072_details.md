# RUN v0.7.2 — details (all pairs)

Supplementary detail for the v0.7.2 all-pairs run.  Captures ruff output
(pair 1), the selection step trace (pair 3), the `/api/demo/status`
payloads (pairs 2, 4–10), and layout rejection logs (pairs 5, 7, 8, 9,
10).  Scrub conventions match `RUN_v072_all_pairs.md`.

## Token table

| Token | Scope | Notes |
| --- | --- | --- |
| `<VENDOR_1>` | OptumRx | pair 1, 3, 4, 6 |
| `<VENDOR_2>` | Facets | pair 3, 6 |
| `<VENDOR_3>` | Socially Determined | pair 2 |
| `<VENDOR_4>` | WellPoint / Wellpoint | pair 5 |
| `<VENDOR_5>` | UHC | pair 7 |
| `<VENDOR_6>` | PeopleSoft | pair 9 |
| `<VENDOR_7>` | BestFootForward / BFF | pair 10 |
| `<VENDOR_8>` | PerformRx | pair 1 (LOB sheet) |
| `<PROJECT_1>` | Project Eagle | pair 1, 3, 4, 6 |
| `<PROJECT_2>` | Medicare Expansion | pair 2 |
| `<PROJECT_3>` | Reprocurement | pair 8 |
| `<ORG_1>` | ACDC | pair 5 |
| `<ORG_2>` | ACLA | pair 7 |
| `<ORG_3>` | PA CHC | pair 8 |
| `<ORG_4>` | ISFDA | pair 10 |
| `<PROGRAM_1>` | Medicaid | pair 5, 7 |
| `<PROGRAM_2>` | MIDS | pair 2 |
| `<TICKET_1>` | 1005789 | pair 1, 3, 4, 6 |
| `<TICKET_2>` | 1006111 | pair 5 |
| `<TICKET_3>` | 1005567 | pair 7 |
| `<TICKET_4>` | 1004429 | pair 8 |
| `<TICKET_5>` | 1004845 | pair 9 |
| `<TICKET_6>` | 1004808 | pair 10 |
| `<TICKET_7>` | E17231 | pair 10 |
| `<FEED_1>` | Accumulators | pair 1 |
| `<FEED_2>` | Member Eligibility | pair 3 |
| `<FEED_3>` | PDE Edit Code Report | pair 4 |
| `<FEED_4>` | Medical Claims | pair 5 |
| `<FEED_5>` | CAG Crosswalk | pair 6 |
| `<FEED_6>` | RxClaims / Rx Claims | pair 7 |
| `<FEED_7>` | 834 Unified Layout | pair 8 ("834" is structural) |
| `<FEED_8>` | HRA Data Ingestion | pair 10 |
| `<FEED_9>` | HCM Data Ingestion | pair 9 |
| `<FEED_10>` | HR Analytics | pair 9 |
| `<SLUG_1>` | orx_accum_optumrx_dly | pair 1 feed slug |
| `<SCHEMA_1>` | pharmcy | pair 1 standard schema |
| `<STG_SCHEMA_1>` | stg_pharmcy | pair 1 stage schema |
| `<SHEET_A>` | Accumulator - Optum Daily File | pair 1 mapping sheet |
| `<SHEET_B>` | Wellpoint MEDClaim_ACDC_Mapping | pair 5 mapping sheet |
| `<SHEET_C>` | EXT_OPTM_PLAN_CAG_XWLK | pair 6 mapping sheet |
| `<SHEET_D>` | Mapping - UHC Rx Claims | pair 7 mapping sheet |
| `<SHEET_E>` | LOB Crosswalk | pair 1 LOB sheet |
| `<AHC>` | AHC | client abbreviation |
| `<CLIENT>` | AmeriHealth Caritas | client name |

Structural labels kept verbatim: fixed width, csv, .dat, .psv, .txt, xlsx,
docx, mapping, stage, standard, source, FILE_DETAILS, VERSION_HISTORY,
MAPPING-, Sheet2, Unified Layout, HCM, STTM, Inbound, Outbound.

---

## 1. Pair 1 — ruff check

Source: `codegen-outputs/demo_20260922_081731` (latest live run).

### Generated files and line counts

| File | Lines |
| --- | ---: |
| `<SLUG_1>/ddl/<SCHEMA_1>.<SLUG_1>.standard.sql` | 86 |
| `<SLUG_1>/ddl/<STG_SCHEMA_1>.<SLUG_1>.sql` | 85 |
| `<SLUG_1>/ddl/<STG_SCHEMA_1>.<SLUG_1>_errors.sql` | 17 |
| `<SLUG_1>/ddl/<STG_SCHEMA_1>.<SLUG_1>_processed_files.sql` | 16 |
| `<SLUG_1>/framework/Insert_scripts_config_table_a2.py` | 125 |
| `<SLUG_1>/framework/Insert_scripts_config_table_prod.py` | 125 |
| `<SLUG_1>/framework/Insert_scripts_config_table_q1.py` | 125 |
| `<SLUG_1>/framework/config_inserts_a2.sql` | 80 |
| `<SLUG_1>/framework/config_inserts_prod.sql` | 80 |
| `<SLUG_1>/framework/config_inserts_q1.sql` | 80 |
| `<SLUG_1>/framework/<SLUG_1_UC>_DDL.txt` | 164 |
| `<SLUG_1>/framework/config_inserts.xlsx` | (binary) |
| `<SLUG_1>/framework/config_rows.xlsx` | (binary) |
| `<SLUG_1>/framework/ADDITION.md` | 37 |
| `<SLUG_1>/candidates/candidates.json` | 136 |
| `reports/<SLUG_1>.md` | 295 |

(`<SLUG_1_UC>` = upper-case of `<SLUG_1>`.)

### ruff check --select ALL (verbatim, paths shortened)

```
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:1:1: EXE002 The file is executable but no shebang is present
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:1:1: INP001 File `<SLUG_1>/framework/Insert_scripts_config_table_a2.py` is part of an implicit namespace package. Add an `__init__.py`.
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:1:1: D100 Missing docstring in public module
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:1:1: CPY001 Missing copyright notice at top of file
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:4:1: ERA001 Found commented-out code
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:7:89: E501 Line too long (90 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:22:16: S105 Possible hardcoded password assigned to: "SECRET_SCOPE"
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:58:15: PTH120 `os.path.dirname()` should be replaced by `Path.parent`
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:60:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:61:6: PTH123 `open()` should be replaced by `Path.open()`
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:61:11: PTH118 `os.path.join()` should be replaced by `Path` with `/` operator
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:70:19: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:70:30: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:74:19: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:74:30: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:74:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:77:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:81:15: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:81:26: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:89:89: E501 Line too long (90 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:94:1: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:94:89: E501 Line too long (91 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:112:17: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:119:5: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_a2.py:122:5: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:1:1: EXE002 The file is executable but no shebang is present
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:1:1: INP001 File `<SLUG_1>/framework/Insert_scripts_config_table_prod.py` is part of an implicit namespace package. Add an `__init__.py`.
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:1:1: D100 Missing docstring in public module
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:1:1: CPY001 Missing copyright notice at top of file
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:4:1: ERA001 Found commented-out code
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:7:89: E501 Line too long (90 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:22:16: S105 Possible hardcoded password assigned to: "SECRET_SCOPE"
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:58:15: PTH120 `os.path.dirname()` should be replaced by `Path.parent`
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:60:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:61:6: PTH123 `open()` should be replaced by `Path.open()`
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:61:11: PTH118 `os.path.join()` should be replaced by `Path` with `/` operator
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:70:19: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:70:30: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:74:19: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:74:30: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:74:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:77:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:81:15: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:81:26: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:89:89: E501 Line too long (90 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:94:1: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:94:89: E501 Line too long (91 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:112:17: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:119:5: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_prod.py:122:5: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:1:1: EXE002 The file is executable but no shebang is present
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:1:1: INP001 File `<SLUG_1>/framework/Insert_scripts_config_table_q1.py` is part of an implicit namespace package. Add an `__init__.py`.
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:1:1: D100 Missing docstring in public module
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:1:1: CPY001 Missing copyright notice at top of file
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:4:1: ERA001 Found commented-out code
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:7:89: E501 Line too long (90 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:22:16: S105 Possible hardcoded password assigned to: "SECRET_SCOPE"
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:58:15: PTH120 `os.path.dirname()` should be replaced by `Path.parent`
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:60:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:61:6: PTH123 `open()` should be replaced by `Path.open()`
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:61:11: PTH118 `os.path.join()` should be replaced by `Path` with `/` operator
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:70:19: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:70:30: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:74:19: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:74:30: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:74:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:77:89: E501 Line too long (89 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:81:15: TRY003 Avoid specifying long messages outside the exception class
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:81:26: EM102 Exception must not use an f-string literal, assign to variable first
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:89:89: E501 Line too long (90 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:94:1: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:94:89: E501 Line too long (91 > 88)
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:112:17: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:119:5: T201 `print` found
<SLUG_1>/framework/Insert_scripts_config_table_q1.py:122:5: T201 `print` found
Found 75 errors.
No fixes available (21 hidden fixes can be enabled with the `--unsafe-fixes` option).
```

**Summary**: 75 errors, 25 per file (identical pattern across 3 environment
variants).  By rule:

| Code | Count | Message |
| --- | ---: | --- |
| E501 | 18 | Line too long |
| T201 | 12 | `print` found |
| TRY003 | 9 | Long messages outside exception class |
| EM102 | 9 | f-string literal in exception |
| EXE002 | 3 | Executable without shebang |
| INP001 | 3 | Implicit namespace package |
| D100 | 3 | Missing module docstring |
| CPY001 | 3 | Missing copyright notice |
| ERA001 | 3 | Commented-out code |
| S105 | 3 | Possible hardcoded password (SECRET_SCOPE) |
| PTH120 | 3 | `os.path.dirname` → `Path.parent` |
| PTH123 | 3 | `open()` → `Path.open()` |
| PTH118 | 3 | `os.path.join` → `Path` `/` operator |

Default rules (without `--select ALL`): 6 errors (3× EXE002, 3× RUF100
unused noqa).

---

## 2. Pair 3 — selection step trace

STTM: `STTM_<PROJECT_1>_<VENDOR_1>_<TICKET_1>_<VENDOR_2> <FEED_2>_v1.2.xlsx`

Re-run of `/api/demo/select` from notebook environment (serverless
compute, not the App runtime).  The document parser subprocess does not
start on serverless — the `start parser` step warns and `classify` falls
back to `unreadable`.  On the App runtime the same pair is known to hang
at `classify` until the selection timeout expires.

### Step trace

| Elapsed | Step | State | Detail |
| ---: | --- | --- | --- |
| 0.50s | locate | running | |
| 1.50s | locate | done | |
| 1.50s | download | running | |
| 2.00s | download | done | |
| 2.00s | start parser | running | |
| 2.50s | start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| 2.50s | classify | running | |
| 3.00s | classify | warning | unreadable: the document parser process did not start (not ready within 60s) |
| 3.00s | pair FRD | running | |
| 4.50s | pair FRD | done | |
| 4.50s | pair VDD | done | |
| 4.50s | record | running | |
| 5.00s | record | done | |

**Total**: 5.0s.  **Step running at expiry** (App runtime): `classify`
(the STTM xlsx parser did not start, so classify cannot open the
workbook; on serverless it falls through immediately as `unreadable`;
on the App it blocks on the parser subprocess until the
`select_timeout_seconds` budget).

Final selection:

```
sttm: STTM_<PROJECT_1>_<VENDOR_1>_<TICKET_1>_<VENDOR_2> <FEED_2>_v1.2.xlsx
frd:  FRD_STG_STD_<VENDOR_1>-<PROJECT_1> <TICKET_1>_<VENDOR_2> <FEED_2> (1).docx
vdd:  VDD_<VENDOR_2>_<FEED_2>.xlsx
```

FRD paired by `ticket` (scope: same_folder).  VDD paired by
`same_folder`.  0 layout questions.

---

## 3. Pairs 2, 4–10 — /api/demo/status payloads

All pairs selected via `start_selection` in a single session.  Every pair
resolved with **0 layout questions**.  The `start parser` step warned on
every pair (serverless — document parser subprocess unavailable); classify
fell back to content discovery or `unreadable`.  Layout questions appear
only during generation runs when the recognizer cannot resolve all header
roles; at selection time no layout questions are surfaced.

### Pair 2

```
STTM: STTM_<PROJECT_2>-<PROGRAM_2> - <VENDOR_3> (1).xlsx
FRD:  FRD_<PROJECT_2>-<PROGRAM_2> - <VENDOR_3> (1).docx
VDD:  VDD_<VENDOR_3>_<PROGRAM_2>.xlsx
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['MAPPING-', 'MAPPING-1', 'MAPPING-2'] (mapping_prefix discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=name_stem, scope=same_folder, score=4.0 (file_patterns +3,
name_stem +1).  VDD: rule=content, scope=same_folder, score=4.0
(file_patterns +3, meta_frequency +1).  Layout questions: 0.

### Pair 4

```
STTM: STTM_<PROJECT_1>_<VENDOR_1>_<TICKET_1>_<FEED_3>.xlsx
FRD:  FRD_STG_STD_<VENDOR_1>-<PROJECT_1> <TICKET_1>_<FEED_3> File (1).docx
VDD:  VDD_<VENDOR_1>_<FEED_3>.xlsx
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['STTM'] (content discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=ticket, scope=same_folder, score=1.0.  VDD: rule=same_folder,
score=0.  Layout questions: 0.

### Pair 5

```
STTM: STTM_STG_STD_<ORG_1>_<VENDOR_4>_<PROGRAM_1>_<FEED_4>_Historical_Ingestion_<TICKET_2>.xlsx
FRD:  FRD_<VENDOR_4>_<FEED_4>_Historical_Ingestion_<TICKET_2>.docx
VDD:  (none — no VDD paired)
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['<SHEET_B>', 'Sheet2'] (content discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=ticket, scope=same_folder, score=4.0 (ticket +3, file_patterns
+1).  VDD: rule=None (no candidate scored above threshold; 3 tied at
1.0).  Layout questions: 0.

### Pair 6

```
STTM: STTM_<PROJECT_1>_<VENDOR_1>_<TICKET_1>_<VENDOR_2> <FEED_5> Table.xlsx
FRD:  FRD_STG_STD_<VENDOR_1>-<PROJECT_1> <TICKET_1>_Ingestion of <FEED_5> & Provider relationship tables from <VENDOR_2> (1).docx
VDD:  VDD_<VENDOR_2>_<FEED_5>.xlsx
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['<SHEET_C>'] (content discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=ticket, scope=same_folder, score=4.0 (ticket +1, file_patterns
+3).  VDD: rule=content, scope=same_folder, score=3.0.  Layout
questions: 0.

### Pair 7

```
STTM: STTM_STG_STD_<ORG_2>_<VENDOR_5>_<PROGRAM_1>_Member_Distribution_<FEED_6>_Historical_Ingestion_<TICKET_3>.xlsx
FRD:  FRD_STG_STD_<ORG_2>_<VENDOR_5>_<PROGRAM_1>_Member_Distribution_<FEED_6>_Historical_Ingestion_<TICKET_3>.docx
VDD:  VDD_<VENDOR_5>_<PROGRAM_1>_<FEED_6>.xlsx
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['<SHEET_D>'] (content discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=ticket, scope=same_folder, score=5.0 (ticket +1, name_stem +4).
VDD: rule=same_folder, score=0.  Layout questions: 0.

### Pair 8

```
STTM: STTM_<ORG_3> <PROJECT_3>_<TICKET_4>_<FEED_7>_FILE.xlsx
FRD:  FRD_STG_STD_<ORG_3> <PROJECT_3>_<TICKET_4>_<FEED_7>_FILE (1).docx
VDD:  VDD_<FEED_7>.xlsx
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['Unified Layout'] (content discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=ticket, scope=same_folder, score=1.0.  VDD: rule=same_folder,
score=0.  Layout questions: 0.

### Pair 9

```
STTM: STTM_<FEED_10>_<FEED_9>_To_DL_Mapping_Document_<TICKET_5>_V1.0.xlsx
FRD:  FRD_STG_STD_<FEED_10>_<FEED_9>_Data_Ingestion_<TICKET_5>_V1.1 (1).docx
VDD:  VDD_<FEED_9>_<VENDOR_6>.xlsx
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['HCM'] (content discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=ticket, scope=same_folder, score=1.0.  VDD: rule=content,
scope=same_folder, score=3.0.  Layout questions: 0.

### Pair 10

```
STTM: STTM_<ORG_4>_<TICKET_6>_<TICKET_7>_<VENDOR_7>_<FEED_8>.xlsx
FRD:  FRD_STD_<ORG_4>_<TICKET_6>_<TICKET_7>_<VENDOR_7>_<FEED_8> (1).docx
VDD:  VDD_<VENDOR_7>_HRA.xlsx
```

| Step | State | Detail |
| --- | --- | --- |
| locate | done | |
| download | done | |
| start parser | warning | RuntimeError: the document parser process did not start (not ready within 60s) |
| classify | done | sttm: mapping sheet(s) ['Outbound_<VENDOR_7>_OH', 'Inbound_<VENDOR_7>_OH', 'Inbound_<VENDOR_7>_LA_Adult', 'Inbound_<VENDOR_7>_LA_Child'] (content discovery) |
| pair FRD | done | |
| pair VDD | done | |
| record | done | |

FRD: rule=ticket, scope=same_folder, score=1.0.  VDD: rule=same_folder,
score=0.  Layout questions: 0.

---

## 4. Pairs 5, 7, 8, 9, 10 — layout rejection logs

Path: `codegen-state/layout_profiles/rejections/`.  Four JSON files on
disk.  All rejections share the same root cause: the model returned a
`source` value outside the allowed literal set (`'synonyms' | 'model' |
'user' | 'cache'`), causing pydantic `LayoutProfile` validation to fail.
The same error propagates into `role_sources.<key>` for every role the
model resolved.

The rejection files are keyed by content fingerprint (a SHA-256 of the
model response), not by pair name.  All share vocabulary hash
`917455a5…5f6817`.

### Rejection 1 — `3b55d5ba…9eae.json`

```json
{
  "fingerprint": "3b55d5ba52fd1fecbfbb4eb4a8e347f5c8c88cb086314abcb1e71b2fa87c9eae",
  "document": "sttm",
  "vocabulary": "917455a55c1417eecdcc3dcf2db9b6a55a1d11b3f272e0c30eff7bb4925f6817",
  "rejections": [
    "sttm : model response failed schema validation: 2 validation errors for LayoutProfile"
  ],
  "schema_errors": [
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["source"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]}
  ]
}
```

### Rejection 2 — `f62af164…c244.json`

```json
{
  "fingerprint": "f62af164e2a9ce985a2a604f9eec995d5d4b713d1a1233df6e6855644c2bc244",
  "document": "sttm",
  "vocabulary": "917455a55c1417eecdcc3dcf2db9b6a55a1d11b3f272e0c30eff7bb4925f6817",
  "rejections": [
    "sttm : model response failed schema validation: 5 validation errors for LayoutProfile"
  ],
  "schema_errors": [
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["source"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]}
  ]
}
```

### Rejection 3 — `f8cba9b3…1dcd.json`

```json
{
  "fingerprint": "f8cba9b3e84f3fa6da16d94725c6bac24303e254bd7d1570a78fac248dbd1dcd",
  "document": "sttm",
  "vocabulary": "917455a55c1417eecdcc3dcf2db9b6a55a1d11b3f272e0c30eff7bb4925f6817",
  "rejections": [
    "sttm : model response failed schema validation: 9 validation errors for LayoutProfile"
  ],
  "schema_errors": [
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["source"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]}
  ]
}
```

### Rejection 4 — `d3c7b70f…ba9c1.json`

```json
{
  "fingerprint": "d3c7b70f2a4c6d1f1b6f2eeee4f6e615e3dc2e2af25cc64e03b19a252d9ba9c1",
  "document": "sttm",
  "vocabulary": "917455a55c1417eecdcc3dcf2db9b6a55a1d11b3f272e0c30eff7bb4925f6817",
  "rejections": [
    "sttm : model response failed schema validation: 16 validation errors for LayoutProfile"
  ],
  "schema_errors": [
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["source"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]},
    {"type": "literal_error", "msg": "Input should be 'synonyms', 'model', 'user' or 'cache'", "loc": ["role_sources", "<key>"]}
  ]
}
```

### Summary

| File (prefix) | Validation errors | role_sources errors |
| --- | ---: | ---: |
| 3b55d5ba | 2 | 1 |
| f62af164 | 5 | 4 |
| f8cba9b3 | 9 | 8 |
| d3c7b70f | 16 | 15 |

All four are `document: "sttm"`, all share the same vocabulary
fingerprint.  The model returned a `source` value not in the allowed
enum; the error count correlates with how many roles it resolved (1, 4,
8, 15 respectively).  These came from prior layout recognition attempts
for pairs 5, 7, 8, 9, 10 and are retained in the runtime cache as
negative entries (the recognizer falls back to synonyms / user answers
when a model response is rejected).
