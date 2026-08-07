# Workbook → STTM-Mapping-Contract Extractor — Reconnaissance

Read-only survey (2026-08-07) ahead of building the missing
workbook→STTM-mapping-contract extractor. Repos inspected: this repo
(`staging` @ `59f420f`) and `~/Desktop/frd-to-sttm-agent` (`staging` @
`3b6cfc2`, read-only). No files in either repo were modified; this document
is the sole output.

---

## 1. Consumer-side contract schema (what the extractor must emit)

### Where the contract is read/validated

| Concern | Location |
|---|---|
| Pydantic models (the schema) | `src/codegen/contracts/sttm.py` — `SttmContract`, `SttmFeed`, `SttmField`, `SourceFile`, `TableRef`, `LoadRules`, `RecycleSpec`, `AuditColumn` |
| Load + validate call site | `src/codegen/resolve/resolver.py:380` — `resolve_pair()`: `SttmContract.model_validate(json.loads(...))` |
| Pairing with FRD contract | `config/config.yaml` `contracts.pairs` (dir `fixtures/contracts`); CLI also accepts `--sttm-contract` (`src/codegen/cli.py:174`) |
| Cross-contract validation | `resolver.py` `resolve_feeds()` / `_resolve_one()` — every FRD⋈STTM disagreement raises `ContractMismatchError`, never reconciled |
| Fixture parse tests | `tests/test_contracts.py` (`test_both_sttm_fixtures_parse`, `test_synthetic_marker_is_carried`, `test_unknown_key_is_rejected`), `tests/test_resolver.py` |

All models are `frozen=True`, `extra="forbid"`, `populate_by_name=True`
(`_MODEL_CONFIG`, sttm.py:19). **`extra="forbid"` means the extractor cannot
emit any key not listed below.** Missing-is-`None`, never a default
(CLAUDE.md config doctrine) — the only defaulted keys are `value_spec`,
`record_segment`, `stage_table` (all `= None`) and `synthetic = False`.

### Field inventory

`SttmContract` (top level):

| Field | Type | Required | Notes |
|---|---|---|---|
| `contract_name` | str | yes | |
| `generated_from_workbook` | str | yes | provenance: source workbook filename |
| `sttm_version` | str | yes | MIDS fixture carries the workbook VERSION_HISTORY's latest version ("1.1") |
| `generated_date` | str | yes | |
| `notes` | list[str] | yes | free-text conventions (see §2) |
| `feeds` | list[SttmFeed], min 1 | yes | `feed_id` uniqueness enforced (`_check_unique_feed_ids`) |
| `synthetic` | bool | no (default False) | only the synthetic CAQH stand-in sets it; "the real generator never emits this key" (sttm.py:171–173) |

`SttmFeed`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `feed_id` | str | yes | join key: must equal `normalize_feed_name(FRD feed_name)` (resolver.py:50–52, lowercase, non-alnum runs → `_`) or be mapped via `config.feed_aliases` |
| `source_system` | str | yes | |
| `mapping_sheet` | str \| None | yes (nullable) | provenance: source sheet name |
| `source_file` | SourceFile | yes | `name_pattern`, `format`, `delimiter` (nullable), `frequency` (nullable) |
| `stage` | TableRef | yes | `schema` (alias → `schema_name`), `table`; for segmented feeds must be the **Detail** table (resolver.py:176–180) |
| `standard` | TableRef \| None | yes (nullable) | None ⇔ FRD standard target empty (cross-checked, resolver.py:311–336) |
| `load_rules` | LoadRules | yes | `not_null_columns`, `mandatory_columns`, `phi_columns` (all list[str] of **source** column names), `recycle: RecycleSpec \| None` |
| `audit_columns` | list[AuditColumn], min 1 | yes | `column` + `datatype` restricted to `Literal["String","Timestamp"]` |
| `field_count` | int | yes | must equal `len(fields)` (validator) |
| `fields` | list[SttmField], min 1 | yes | |

`SttmField` (one mapping row):

| Field | Type | Required |
|---|---|---|
| `source_column` | str | yes |
| `description` | str \| None | yes (nullable) |
| `sample_value` | str \| None | yes (nullable) |
| `source_datatype` | str | yes |
| `nullable` | bool | yes |
| `phi` | bool | yes |
| `mandatory` | bool | yes |
| `stage_column` | str | yes |
| `stage_datatype` | str | yes |
| `standard_column` | str \| None | yes (nullable) |
| `standard_datatype` | str \| None | yes (nullable) |
| `value_spec` | str \| None | no (default None) |
| `record_segment` | `Literal["Header","Detail","Trailer"]` \| None | no (default None) |
| `stage_table` | str \| None | no (default None) |

`RecycleSpec`: `applies_to` (must be a `source_column` in `fields[]`),
`enabled: bool`, `validation: str`, `on_match: str`, `on_no_match: str`,
`recycle_window_days: int > 0`.

### Internal validators the extractor's output must satisfy

`SttmFeed._check_internal_consistency` (sttm.py:105–153):

- `field_count == len(fields)`;
- every column in `load_rules.{not_null,mandatory,phi}_columns` and
  `recycle.applies_to` must be a real `fields[].source_column`;
- `{f.source_column where f.phi}` must **exactly equal**
  `set(load_rules.phi_columns)`;
- segment annotations are all-or-nothing per feed, and `record_segment` ⟺
  `stage_table` per field (half-migrated contracts rejected).

### Resolver-side constraints (violations are loud `ContractMismatchError`s)

- `feed_id` sets must join 1:1 with FRD feeds (unmatched on either side
  fails, resolver.py:192–224).
- Flat feed: `stage.table` must be in FRD `stage_target.tables`. Segmented:
  each segment's fields must share one `stage_table`, all in the FRD list; a
  **Detail** segment is mandatory; STTM must not name segments the FRD
  doesn't declare (`_resolve_segments`).
- Delimiter: STTM vs FRD must agree when both stated; if neither, implied
  from format only for `csv`→`,` / `psv`→`|` (`_FORMAT_DELIMITERS`,
  resolver.py:27) — any other format with no stated delimiter errors.
- `recycle.validation` **must parse** against `_REFERENCE_RE`
  (resolver.py:31–35): `against <id_column> in <table> [where <filter>]` —
  see §4, this is a normalization the extractor must perform.
- Recycle window must agree with any `N days` found in FRD `recycle_rule`
  free text (`_WINDOW_DAYS_RE`).
- Standard target presence must agree with FRD in both directions.

### Where the H/D/T discriminator assumption lives

- `config/config.yaml` `segments:` block — `record_type_column:
  record_type`, `record_type_values: {Header: "H", Detail: "D", Trailer:
  "T"}`, `trailer_count_column: record_count`; commented "ASSUMPTION pending
  the source dictionary".
- Config model: `src/codegen/config.py:65–66`.
- Consumed at emit time: `src/codegen/emit/context.py:187–201` (per-segment
  `record_type_value`; raises if a segment has no configured value),
  `:230–232` (trailer count reconciliation), `:315` (`record_type_column`
  emitted only for segmented feeds).
- Documented as an assumption: `CLAUDE.md` "Known gaps" (…"H/D/T, in
  `config.segments`) is an assumption pending the source dictionary"…) and
  `docs/DESIGN.md` open questions. The synthetic CAQH fixture bakes the same
  assumption into its `record_type` first-field rows and its `notes[2]`.

**The discriminator is NOT part of the STTM contract schema** — the
contract only carries `record_segment` per field; the mapping of segment →
one-letter record-type value is config. The extractor therefore does not
need to emit it, but a real CAQH workbook may finally *confirm* it — worth
capturing into `notes` if seen.

---

## 2. Existing fixture contracts

### `fixtures/contracts/sttm_mapping_contracts.json` (MIDS — real, produced out-of-repo)

- `contract_name` "SD SDOH bronze-to-silver mapping contract",
  `generated_from_workbook` "STTM-Medicare Expansion-MIDS-Social
  Determine.xlsx", `sttm_version` "1.1", `generated_date` "2026-07-16". No
  `synthetic` key (defaults False).
- `notes[]` record the production conventions: stage lands ALL columns as
  String 1:1; casts only at standard (gold); every stage table adds the 4
  audit columns; "Source dtype casing normalized (e.g. 'string' →
  'String'); NULL Check normalized to boolean 'nullable'".
- 3 flat feeds (`source_system` "Socially Determined"): 

| feed_id | fields | sheet | stage | standard | file | recycle |
|---|---|---|---|---|---|---|
| `sd_community_demographic_risk` | 86 | `MAPPING-SD_COMMUNITY_DEMOGRAPHI` | stg_sdoh.sd_community_demographic_risk | sdoh.same | `demographics_package_YYYY_MM.csv`, csv, `,`, twice yearly | None |
| `sd_community_risk` | 267 | `MAPPING-SD_COMMUNITY_RISK` | stg_sdoh.sd_community_risk | sdoh.same | `analytics_package_YYYY_MM.csv`, csv, `,`, twice yearly | None |
| `sd_individual_risk` | 46 | `MAPPING-SD_INDIV_RISK` | stg_cm.sd_individual_risk | cm.same | `sd_ind_risk_data_package_amer_MI_YYYYMMDD_HHMM.psv`, psv, `\|`, monthly | yes (member_id, 7 days) |

- Population: all core field keys 100% populated; `sample_value` null on a
  handful (4 of 267 / 1 of 46); `value_spec` present **only** on
  `sd_individual_risk` (46/46 — sourced from that sheet's extra "Comment"
  column, see §3); no `record_segment`/`stage_table` anywhere.
- `load_rules`: `not_null_columns` == `mandatory_columns` (single key
  column per feed); `phi_columns` only `["member_id"]` on individual risk.
- `audit_columns` identical on all feeds: LOB/String, SRC_FILE_NAME/String,
  REC_CREATION_TIME/Timestamp, REC_UPDATED_TIME/Timestamp.
- Recycle (individual risk): `validation` **"Match member_id against
  SBSB_ID in PR_STD.FACETS.CMC_SBSB_SUBSC where GRGR_CK = 31"** — the
  resolver-parseable phrasing, which is *not* the phrasing found in either
  the FRD (`recycle_rule`: "Recycle Flag enabled for 7 days (Check with
  SBSB_ID from PR_STD.FACETS.CMC_SBSB_SUBSC FOR GRGR_CK = 31, …)") or the
  workbook family (§3). Whoever produced this contract **rewrote** the
  free text into the canonical `Match X against Y in T where F` form.

### `fixtures/contracts/sttm_mapping_contracts_caqh.SYNTHETIC.json` (CAQH — synthetic)

- `synthetic: true`, `sttm_version` "0.0-synthetic";
  `generated_from_workbook` explicitly says "SYNTHETIC — no real workbook".
- 1 feed `caqh_tpl_inbound_files` (`source_system` "CAQH"), 17 fields, all
  carrying `record_segment` + `stage_table` (Header→`EXT_TPL_CAQH_HDR` 4
  fields, Detail→`EXT_TPL_CAQH_DTL` 10, Trailer→`EXT_TPL_CAQH_TRL` 3);
  `stage` = stg_mbr.EXT_TPL_CAQH_DTL (the Detail table, per resolver rule);
  `standard: null` (FRD standard target empty — stage-only feed);
  `mapping_sheet` "SYNTHETIC-CAQH_TPL".
- Dialect differences vs MIDS: `standard_column`/`standard_datatype` null
  on all 17 fields (0% populated); no `value_spec`; stage columns UPPERCASE
  (`member_id` → `MEMBER_ID`) where MIDS is 1:1 lowercase; first field of
  each segment is the assumed `record_type` discriminator; recycle window
  15 days with validation already in the canonical `Match … against … in …`
  phrasing (no `where` clause).
- Same 4 audit columns; `phi_columns` = not_null = mandatory-ish
  (`member_id`, `policy_number`).
- Both fixtures conform to the same `SttmContract` schema (proven by
  `test_both_sttm_fixtures_parse`); the differences above are exactly the
  documented "segmented dialect extension" (docs/DESIGN.md §1) plus
  population differences.

Feed-id derivation note: for MIDS, `feed_id` == stage table name == FRD
`feed_name` (already normalized). For CAQH, `feed_id`
(`caqh_tpl_inbound_files`) is `normalize_feed_name("CAQH TPL Inbound
Files")` — the FRD feed name, **not** the stage table. So "feed_id = stage
table" is a coincidence of MIDS; the invariant is "feed_id = normalized FRD
feed name".

---

## 3. Producer-side workbook shape (frd-to-sttm, read-only)

Two artifacts inspected with openpyxl (no writes):

- **`demo_sttm.xlsx`** — the committed anonymized golden fixture (repo
  root; identical copy at `local_dev_fixtures/sttm_reference/demo_sttm.xlsx`,
  same bytes/size 46744). This is the anonymized stand-in for a *real
  client-authored* STTM workbook ("Civic Vantage" universe, `cv_*`).
- **`local_dev_fixtures/sttm_out_live_e2e_20260807b/rendered/demo_frd.sttm.xlsx`**
  — the tracked replay set's workbook, *rendered by* `04_sttm_render.py`
  (dialect `sheet_per_table`) from the live-E2E contract.

### 3a. Golden workbook `demo_sttm.xlsx`

Sheets: `FILE_DETAILS`, `VERSION_HISTORY`, `MAPPING-CV_COMMUNITY_DEMOGRAPHI`,
`MAPPING-CV_COMMUNITY_RISK`, `MAPPING-CV_INDIV_RISK`.

**Feed delineation: one `MAPPING-*` sheet per feed.** Sheet names hit
Excel's 31-char limit (`MAPPING-CV_COMMUNITY_DEMOGRAPHI` is truncated
"…DEMOGRAPHIC"); the MIDS fixture's `mapping_sheet` values show the same
truncation.

**`FILE_DETAILS`** (columns `Vendor | FileName | File Description |
Location | Frequency`): one row per feed, **same order as the mapping
sheets**, no explicit key linking row↔sheet. Description and Location are
empty in the golden fixture. Values: Vendor "Civic Vantage" (→
`source_system`), FileName e.g.
`cv_ind_risk_data_package_mrdn_OH_YYYYMMDD_HHMM.psv` (→
`source_file.name_pattern`; extension → `format`), Frequency "Yearly
Twice" / "Monthly" (→ `frequency`; NB the MIDS fixture says "twice yearly"
— reworded, not verbatim). **No delimiter column anywhere.**

**`VERSION_HISTORY`**: layout quirk — content is anchored at E6:H12, not
A1: merged title cell `E6:H6` "Revision History", header row 7 (`Date |
Version | Author(s) | Description of Version/Change`), data rows 8–9
(1.0 Initial Draft, 1.1 "Recycle check enabled"). Latest version "1.1"
matches the MIDS fixture's `sttm_version`.

**Mapping sheets** — common skeleton: row 1 is a merged three-band header
(`Source File Layout` | `Stage Layer` | `Standard Layer`; merge ranges
differ per sheet), row 2 is the real column header, data starts row 3, no
blank separator rows. A **blank spacer column** sits between the Stage and
Standard blocks (col L in 16-col sheets, col M in the 18-col sheet). Stage
and Standard blocks are always `Schema | TableName | ColumnName | DataType`.

**The source-side header block differs per sheet — three dialects in one
workbook:**

| Sheet | Cols | Source-block header (row 2, verbatim) |
|---|---|---|
| CV_COMMUNITY_DEMOGRAPHI | 16 | `Database column Name, NULL CHECK, Description, Sample Value, DataType, PHI Field␠, Mandatory Field` |
| CV_COMMUNITY_RISK | 16 | `Database Name, Description, Sample Value, DataType, ␠NULL Check, PHI Field␠, Mandatory Field` (NULL check in a different position; leading/trailing spaces) |
| CV_INDIV_RISK | 18 | `Client Data Table Column Name, Description, Comment, Example Values, Data Type, NULL Check, PHI/PII Field, Mandatory` + trailing col R `Recycle Flag ( Enabled for 7 Days)` |

So: header labels vary (three different names for "source column"; "Sample
Value" vs "Example Values"), column order varies, stray whitespace occurs,
and per-sheet extra columns exist (**Comment** → the fixture's
`value_spec`; **Recycle Flag** → the recycle spec). Header-driven,
fuzzy-normalized column resolution is mandatory; positional parsing will
break.

**Cell value conventions** (all with casing/whitespace variance):

- NULL check: `Not NULL␠` / `NULL␠` / `NULL` → `nullable` bool.
- PHI / Mandatory: `Yes`/`No`/`NO` → bool.
- Datatypes: `String`, `Int`, `Date`, `Decimal(10,2)`, lowercase `string`/
  `timestamp` on audit rows — MIDS notes say casing was normalized.
- Stage DataType is String for every real column (matches notes);
  standard DataType carries the real cast (`Decimal(10,2)`, `Int`, `Date`).

**Audit columns live IN the sheets as trailing rows**: the last 4 data
rows of every mapping sheet have source-side cells `NA` (or blank) and
stage/standard ColumnName = `LOB`, `SRC_FILE_NAME`, `REC_CREATION_TIME`,
`REC_UPDATED_TIME` with lowercase datatypes `string`/`timestamp`. This is
where the fixture's `audit_columns` (and the row-count delta:
90/271/50 sheet rows vs 86/267/46 fixture fields) come from. The extractor
must recognize `source_column == "NA"` trailing rows as audit rows — they
are **not** `fields[]` entries (and would fail schema/consistency checks if
emitted as such).

**Recycle**: the whole spec is free text inside the flagged row's col R
cell (`R3`, on `member_id`):

> `Recycle Flag ( Enabled for 7 Days)\nY ( Check with SUBS_ID from
> CoreMember in the PR_STD.COREMEMBER.CM_SUBS_MASTER FOR GRP_CK = 47, if
> available process it else load this to the Recycle Table with Recycle
> Flag Enabled for 7 days.)`

i.e. header text repeated + `Y (...)` free text. `applies_to` = the row
carrying the `Y`; window days appear in both header and body; the
reference check is phrased "Check with `<id_column>` from `<x>` in the
`<table>` FOR `<filter>`" — the **same phrasing family as the FRD's
`recycle_rule`**, and *not* the `Match … against … in … where …` form the
resolver's `_REFERENCE_RE` requires. Other rows' col R is empty.

### 3b. Rendered replay workbook (`04_sttm_render.py` output)

Same 5-sheet structure but a **canonicalized, information-lossy**
rendition — it is *not* a fully faithful stand-in for a client workbook:

- All three mapping sheets use one uniform 16-col header (the
  COMMUNITY_DEMOGRAPHI dialect, `PHI Field` without trailing space), **no
  merged cells** (row-1 band labels present but unmerged), data from row 3.
- Sheet named `MAPPING-CV_INDIVIDUAL_RISK` (golden: `…CV_INDIV_RISK`) —
  under the 31-char limit so no truncation.
- **Dropped**: the Comment column (`value_spec` source) and the entire
  Recycle Flag column.
- **Degraded audit rows**: last 4 rows have `NA` even in Stage/Standard
  *ColumnName* (golden names them LOB etc.), datatype String — audit
  identities are unrecoverable from the rendered workbook.
- Standard-layer DataType is String everywhere (golden carries
  `Decimal(10,2)`/`Int`/`Date`) — the gold-layer casts are lost.
- `FILE_DETAILS` richer in places (Location populated, verbose Frequency
  "Monthly Run; File will be received yearly twice…", Vendor "Civic
  Vantage (CV)", multiple `;`-joined name patterns incl. CCYY variants) but
  differently worded.
- `VERSION_HISTORY` is a different layout entirely: A1-anchored, header
  `Version | Date | Author | Change Description`, single auto-generated row
  ("frd-sttm-agent phase5 v0.1", "Auto-generated from demo_frd.docx").

**Neither workbook contains any segmented (H/D/T) sheet** — the CAQH
layout (per-segment sections? a Record Type column? separate sheets per
segment?) is entirely unobserved in committed fixtures.

---

## 4. Gap analysis: workbook → contract

### (a) Directly derivable from the golden-workbook shape

| Contract field | Workbook source |
|---|---|
| `feeds[]` partition | one `MAPPING-*` sheet per feed |
| `mapping_sheet` | sheet name (verbatim, incl. 31-char truncation) |
| `stage` / `standard` TableRef | Stage/Standard blocks' Schema+TableName (constant down the sheet) |
| `fields[].source_column` | source-block "column name" column (label varies per sheet) |
| `description` | Description |
| `sample_value` | Sample Value / Example Values (null when blank) |
| `source_datatype` | source DataType (casing normalized per MIDS notes) |
| `nullable` | NULL check cell (`Not NULL*` → False, else True; trim whitespace) |
| `phi` | PHI Field / PHI-PII Field (`Yes`→True; case-insensitive) |
| `mandatory` | Mandatory Field / Mandatory |
| `stage_column`, `stage_datatype` | Stage ColumnName/DataType |
| `standard_column`, `standard_datatype` | Standard ColumnName/DataType |
| `value_spec` | Comment column, when the sheet has one |
| `audit_columns` | trailing `NA`-source rows' stage ColumnName/DataType (casing normalized to `String`/`Timestamp` — Literal enforced) |
| `field_count` | count of non-audit data rows |
| `load_rules.not_null_columns` | rows with `Not NULL` |
| `load_rules.mandatory_columns` | rows with Mandatory = Yes |
| `load_rules.phi_columns` | rows with PHI = Yes (must exactly match per-field flags — same cells, so consistent by construction) |
| `source_file.name_pattern` | FILE_DETAILS FileName |
| `source_system` | FILE_DETAILS Vendor |
| `sttm_version` | VERSION_HISTORY latest Version row |
| `generated_from_workbook` | input filename |
| `recycle.applies_to`, `recycle_window_days` | flagged row + "N Days" in Recycle Flag text |

### (b) Requiring inference, normalization, or defaults

| Field | Inference |
|---|---|
| `source_file.format` | file-name extension (`csv`/`psv`; CAQH is `.txt`) |
| `source_file.delimiter` | **not in the workbook**; inferable for csv/psv (mirror `_FORMAT_DELIMITERS`), but `.txt` (CAQH) has no implied delimiter — must come from FRD (`frd_feed.delimiter`) or be emitted null and rely on the FRD side stating it |
| `source_file.frequency` | FILE_DETAILS Frequency, but fixture shows rewording ("Yearly Twice" → "twice yearly") — decide verbatim vs normalized |
| FILE_DETAILS row ↔ sheet pairing | positional (same order) or fuzzy name match — no key exists |
| header/column resolution | per-sheet fuzzy header mapping over 3+ observed label dialects, whitespace-tolerant |
| `feed_id` | invariant is *normalized FRD feed name*; equals stage table name for MIDS only. Deriving from stage table + `feed_aliases` works for MIDS but CAQH proves it wrong in general → likely needs the FRD contract as a second input (or emit stage-table-derived ids and lean on `config.feed_aliases`) |
| `recycle.validation` | must be **rewritten** from the workbook's "Check with X from … in the T FOR F" phrasing into the resolver-parseable `Match <applies_to> against <X> in <T> where <F>` (the MIDS contract's author did exactly this by hand); `enabled` from the `Y`; `on_match`/`on_no_match` are boilerplate sentences in the fixtures — templated from the free text |
| `contract_name`, `notes`, `generated_date` | authored/templated (fixture notes are hand-written convention statements; extractor could emit factual notes) |
| datatype casing | normalize `string`→`String`, `timestamp`→`Timestamp` (audit Literal requires it) |

### (c) NOT derivable from the workbook alone

| Item | Why / where it must come from |
|---|---|
| H/D/T record-type discriminator (column + `H`/`D`/`T` values) | not a contract field at all — lives in `config.segments`; the assumption is "pending the source dictionary". Source: the client's **source dictionary** / source team; a real CAQH workbook *may* reveal it (first Detail-sheet column) but per CLAUDE.md it's unconfirmed either way |
| `record_segment` / `stage_table` per field (segmented dialect) | **no segmented workbook exists in any repo** — the real CAQH workbook layout is unknown; the extractor's segmented path cannot even be designed from committed fixtures, only from the synthetic contract's *output* shape |
| `feed_id` join key (general case) | FRD feed name (see (b)) — an FRD contract input or aliases config |
| Delimiter for non-csv/psv formats | FRD contract / source team |
| Recycle reference-table semantics | the workbook states the check only as free text; correctness of the canonicalized `validation` string depends on the FRD/source-dictionary agreement (resolver cross-checks window days against FRD text) |
| Standard-layer presence for stage-only feeds | FRD `standard_target` (CAQH's empty standard is an FRD-side fact; a workbook Standard block might be absent — unobserved) |

### (d) Feed-universe mismatch: fixtures cannot directly test the extractor

The two workbook fixtures (frd-to-sttm repo) and the two contract fixtures
(this repo) come from **different anonymization universes**:

| | Workbooks (frd-to-sttm) | MIDS contract fixture (here) |
|---|---|---|
| Vendor/system | Civic Vantage (CV) | Socially Determined (SD) |
| Tables/columns | `cv_*`, `stg_sdh`/`sdh`, `stg_care`/`care` | `sd_*`, `stg_sdoh`/`sdoh`, `stg_cm`/`cm` |
| File names | `demographic_extract_YYYY_MM.csv`, `cv_ind_risk_…_mrdn_OH_…` | `demographics_package_YYYY_MM.csv`, `sd_ind_risk_…_amer_MI_…` |
| Recycle reference | `SUBS_ID` / `PR_STD.COREMEMBER.CM_SUBS_MASTER` / `GRP_CK = 47` | `SBSB_ID` / `PR_STD.FACETS.CMC_SBSB_SUBSC` / `GRGR_CK = 31` |

Structurally they are the *same feeds* (86/267/46 fields; same flags,
same audit rows, same single-PHI-column pattern), so the MIDS fixture is an
excellent **structural** oracle but a byte-level diff target for nothing.
Implications:

- Running the extractor on `demo_sttm.xlsx` can never reproduce
  `sttm_mapping_contracts.json`; equality-based golden tests need a **new
  committed expected-output fixture in the CV universe** (plus the FRD
  side: frd-to-sttm's `demo_frd`-derived contract uses `cv_*` feed names,
  so a CV-universe pair would also resolve end-to-end through codegen).
- Alternatively, test structurally: extract from `demo_sttm.xlsx`, assert
  field counts/flags/shape match the MIDS fixture modulo renames — weaker
  but no new fixture needed.
- The CAQH/segmented path has **no workbook fixture at all**; tests would
  need a synthetic segmented workbook authored to whatever layout the real
  CAQH STTM turns out to have (currently unknowable).
- The rendered replay workbook is a *third* shape (lossy: no Comment/
  Recycle columns, degraded audit rows, String-only standard datatypes) —
  supporting it as an input means accepting contracts without value_spec,
  recycle, audit identities, or gold casts; probably a non-goal, or an
  explicit degraded mode.

---

## 5. Open design questions for the extractor

1. **Where does it get the FRD-side facts?** `feed_id` (general case),
   delimiter for `.txt`, standard-target presence, and recycle
   cross-checks all live in the FRD contract. Should the extractor take
   `(workbook, frd_contract)` as inputs — making it a *pairing-aware*
   extractor that can emit resolver-ready ids — or workbook-only, leaning
   on `config.feed_aliases` and emitting nullable/absent values for the
   rest?
2. **Recycle canonicalization**: rewrite the workbook's "Check with X from
   … FOR F" free text into `Match <col> against <X> in <T> where <F>`
   inside the extractor (deterministic regex over an observed-in-two-repos
   phrasing family), or extend `resolver._REFERENCE_RE` to accept the
   native phrasing and keep the contract verbatim? (Verbatim favors
   grounding/auditability — the program's Layer-1 doctrine; rewriting
   matches what the existing MIDS fixture did.)
3. **Header-dialect strategy**: the one golden workbook already shows 3
   source-block layouts. Config-driven header synonym map (in
   `config.yaml`, per config doctrine) vs. hardcoded fuzzy matcher vs.
   per-client layout profiles? And what is the failure mode for an
   unrecognized column — loud error (repo doctrine) or note-and-skip?
4. **Segmented workbooks**: block on obtaining the real CAQH STTM workbook
   (its layout is unknowable today), or ship flat-only v1 with the
   segmented dialect explicitly out of scope and the synthetic contract
   remaining the CAQH stand-in?
5. **Test oracle**: commit a new CV-universe expected contract (strong,
   byte-diffable, enables an end-to-end fixture pair with frd-to-sttm's
   demo) vs. structural assertions against the SD-universe MIDS fixture?
6. **Audit-row recognition rule**: `source_column in {"NA", ""}` +
   membership in the known audit-name set, or trailing-position-based? The
   golden workbook varies (`NA` vs blank vs `No` across its own sheets);
   the rendered workbook degrades them entirely.
7. **Where does the extractor live in this repo's layout** (`src/codegen/`
   new `extract/` package + CLI subcommand?) and does its output land in
   `fixtures/contracts/` as a committed artifact or in gitignored `out/`
   with explicit promotion (matching the program's "promote a new baseline
   explicitly" doctrine)?
