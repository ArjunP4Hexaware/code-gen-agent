# IIG scorecard — 2026-10-07 (IIG-first demo, `feature/iig-first`)

What the generated `ADLS_DELTA_INGESTION_DETAILS` row for the Socially
Determined community-demographic feed gets right, measured against the REAL
`demographics_package` row (`IIG test cells.xlsx`, read in place at the repo
root, gitignored, never copied). The generated side is the CV golden pair —
the anonymised copy of the same feed (`cv_` = `sd_`, `sdh` = `sdoh`, the
vendor name) — so name-only differences score **ALIAS**, not DIFF.
`CREATED_BY` / `UPDATED_BY` values are never printed.

## Scorecard

`config/overlays/acfc_env.yaml` as committed now carries the SDOH path shapes
and `src_columns_style: named` (follow-up, 2026-10-07):

```yaml
metadata:
  templates:
    iig_v2:
      src_columns_style: named
      path_patterns:
        ADLS_DELTA_INGESTION_DETAILS:
          SRC_ADLS_PATH: "{landing_rel}"
          SRC_ADLS_ARCHVL_PATH: "{landing_rel}Archive/"
          TGT_ADLS_PATH: "/{domain_path}Processed/{stage_table}"
          TGT_RJT_ADLS_PATH: "/{domain_path}Reject/{reject_table}"
```

> **This overlay applies to EVERY feed generated in ACFC.** A PRX-shaped feed
> (pair 1, the accumulators) gets these SDOH-shaped paths and the `named`
> SRC_COLUMNS style too, until the overlay is split per source family. The
> path cells say which shape they came from: tooltip and review-copy citation
> name `config/overlays/acfc_env.yaml` and quote the shape.

Score history for the CV pair against the real row:

| State | Line |
| --- | --- |
| first commit (shipped path shapes, positional) | `filled 38/55, matched 31, alias 3, open 10 (BSA 5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 11` |
| + path shapes and `named` in the overlay | `filled 38/55, matched 32, alias 7, open 10 (BSA 5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 6` |
| + scorecard: data types caseless, LOB as ALIAS on the fixture (now) | `filled 38/55, matched 33, alias 8, open 10 (BSA 5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 4` |

Current output (committed overlay, default-loaded, no env set):

```
ADLS_DELTA_INGESTION_DETAILS: real sd_community_demographic_risk vs generated cv_community_demographic_risk
OPEN  GROUP_ID                   owner: Engineer
OPEN  OBJECT_ID                  owner: Engineer
DIFF  OBJECT_NAME                real 'demographics_package' | generated 'demographic_extract_CCYY_MM'
MATCH DOMAIN
MATCH SUBDOMAIN
OPEN  PIPELINE_ID                owner: Engineer
DIFF  SOURCE                     real 'Socially Determined' | generated 'Civic Vantage (CV)'
MATCH FREQUENCY
ALIAS LOB                        (anonymised in the fixture) generated 'OHDS'
MATCH CLAIM_TYPE_ID              (both blank / NULL)
MATCH ACTIVE_FLAG
MATCH SRC_ADLS_CONNECTION_ID
MATCH METADATA_CONNECTION_ID
MATCH SRC_CONTAINER_NAME
ALIAS SRC_ADLS_PATH              generated '/inbound/sdh/public/civic_vantage/'
DIFF  SRC_FILE_NAME              real 'demographics_package*' | generated 'demographic_extract_CCYY_MM.csv'
MATCH SRC_FORMAT
MATCH SRC_COLUMNS
MATCH SRC_DATA_TYPE
MATCH SRC_FILE_DELIMITER
MATCH SRC_REC_LNGTH              (both blank / NULL)
MATCH SRC_COL_LNGTH              (both blank / NULL)
MATCH SRC_COL_STRT_END_INDX      (both blank / NULL)
ALIAS SRC_ADLS_ARCHVL_PATH       generated '/inbound/sdh/public/civic_vantage/Archive/'
MATCH SRC_COMPRESSION
OPEN  HEADER_FLAG                owner: BSA
MATCH MULTILINE_FLAG
MATCH SCHEMA_DRIFT_FLAG
OPEN  FILE_HEADER_FLAG           owner: BSA
OPEN  FILE_FOOTER_FLAG           owner: BSA
MATCH MANDATORY_FIELD_LIST
MATCH TGT_CONNECTION_ID
ALIAS TGT_DATABASE_NAME          generated 'stg_sdh'
ALIAS TGT_TABLE_NAME             generated 'cv_community_demographic_risk'
MATCH TGT_CONTAINER_NAME
ALIAS TGT_ADLS_PATH              generated '/sdh/public/civic_vantage/Processed/cv_community_demograp...'
MATCH TGT_COLUMN_NAMES
MATCH TGT_FORMAT
MATCH TGT_DATA_TYPE              (case-insensitive; real 90 items ['String', 'String', 'String'] | generated 90 items ['String', 'String', 'String']; first difference at item 87: 'string' vs 'String')
MATCH TGT_LOAD_OPTION
ALIAS TGT_RJT_TABLE_NAME         generated 'cv_community_demographic_risk_reject'
ALIAS TGT_RJT_ADLS_PATH          generated '/sdh/public/civic_vantage/Reject/cv_community_demographic...'
MATCH TGT_PARTITION_COLUMN
MATCH TGT_PARTITION_VALUE
DIFF  TGT_PRIMARY_KEY            real 1 items ['NULL'] | generated 1 items ['zip_code']
MATCH RECYCL_ENBL_FLG
MATCH RECYCL_TBL_NM
MATCH RECYCL_ADLS_PATH
MATCH RECYCL_RETN_DAYS           (both blank / NULL)
MATCH MAPPING_EXPRESSION         (both blank / NULL)
OPEN  CREATED_BY                 owner: BSA
OPEN  CREATED_DATE               owner: Set at load (CI/CD)
OPEN  UPDATED_BY                 owner: BSA
OPEN  UPDATED_DATE               owner: Set at load (CI/CD)
MATCH FILE_METADATA              (both blank / NULL)
filled 38/55, matched 33, alias 8, open 10 (BSA 5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 4
```

Scoring rules worth knowing: `SRC_DATA_TYPE` / `TGT_DATA_TYPE` compare
case-insensitively (the real row itself mixes `String` and `string`; a
case-only difference is MATCH with a note), and `LOB` is ALIAS when the
generated row is the anonymised fixture (its table name differs from
`--real-table`) — on the real documents both are compared exactly.

## Where the 54 template cells came from (committed overlay)

| Source | Cells | Columns |
| --- | --- | --- |
| **ACFC overlay**: environment constants, badged synthetic, tooltip names `config/overlays/acfc_env.yaml` | 6 | SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, TGT_CONNECTION_ID, SRC_CONTAINER_NAME, TGT_CONTAINER_NAME, SCHEMA_DRIFT_FLAG |
| **Overlay path shapes** applied to the FRD ADLS Location (tooltip and review citation name the overlay and quote the shape) | 4 | SRC_ADLS_PATH, SRC_ADLS_ARCHVL_PATH, TGT_ADLS_PATH, TGT_RJT_ADLS_PATH |
| **FRD** | 13 | OBJECT_NAME, DOMAIN, SUBDOMAIN, SOURCE, FREQUENCY (token, P1c), LOB, SRC_FILE_NAME, SRC_FORMAT, SRC_FILE_DELIMITER, TGT_DATABASE_NAME, TGT_TABLE_NAME, TGT_LOAD_OPTION (Overwrite, P1b), RECYCL_ENBL_FLG |
| **STTM** | 6 | SRC_COLUMNS, SRC_DATA_TYPE, MANDATORY_FIELD_LIST, TGT_COLUMN_NAMES, TGT_DATA_TYPE, TGT_PRIMARY_KEY |
| **Template constants**: framework vocabulary, shipped | 9 | ACTIVE_FLAG, SRC_COMPRESSION, MULTILINE_FLAG, TGT_FORMAT, TGT_RJT_TABLE_NAME, TGT_PARTITION_COLUMN, TGT_PARTITION_VALUE, RECYCL_TBL_NM, RECYCL_ADLS_PATH |
| **Open**: blank, flagged, owner in the review copy | 16 | see below |

The 55th real column, `FILE_METADATA`, is not in the `iig_v2` template. Its
real value is NULL, so it scores MATCH.

### Open cells and why

| Column(s) | Owner | Why it stays open |
| --- | --- | --- |
| GROUP_ID, OBJECT_ID, PIPELINE_ID | Engineer | framework-assigned identifiers, never invented |
| HEADER_FLAG, FILE_HEADER_FLAG, FILE_FOOTER_FLAG | BSA | the FRD states no header row or trailer, and the CV FAQ leaves `has_header` / `has_trailer` unanswered. P1f derives Y/N only from a stated answer, so answering them in `fixtures/faq/<feed>.faq.yaml` fills all three |
| CREATED_BY, UPDATED_BY | BSA | the RFC number (FAQ `rfc_number`), which is unanswered |
| CREATED_DATE, UPDATED_DATE | CI/CD | set by GETDATE() at insert |
| CLAIM_TYPE_ID, SRC_REC_LNGTH, SRC_COL_LNGTH, SRC_COL_STRT_END_INDX, RECYCL_RETN_DAYS, MAPPING_EXPRESSION | — | blank here and NULL in the real row too, so they score MATCH |

### The remaining DIFFs

| Column | Real vs generated | Cause |
| --- | --- | --- |
| OBJECT_NAME, SRC_FILE_NAME | `demographics_package*` vs `demographic_extract_CCYY_MM.csv` | the fixture's file pattern is not the real one. The derivation (the pattern minus wildcards and extension) produces the real row's shape |
| SOURCE | `Socially Determined` vs `Civic Vantage (CV)` | the FRD's Data Source cell carries a bracketed abbreviation that the real row drops |
| TGT_PRIMARY_KEY | `NULL` vs `zip_code` | **a real question for the framework team, kept as DIFF on purpose**: the mapping contract states `zip_code` as the natural key, the real row states no primary key. Is TGT_PRIMARY_KEY read at all for a truncate-and-load (Overwrite) feed, and should it then be NULL? |

## Step results

| Step | Commit | Result |
| --- | --- | --- |
| .gitignore: reference xlsx + dashboard-JSON folders | be4c6e4 | done. NOTE: these files were committed on this branch earlier (705e332, 17d1300, e27ef7f) and are on origin. A gitignore line does not untrack them |
| P0 unreadable xlsx (`dcterms:modified` keeps xmlns:xsi) | be4c6e4 | pass. The round-trip tests fail on the old regex when lxml is installed |
| P0 ACFC overlay, applied by default in `load_config` | 44e74a9 | pass. CV: FAIL → PASS_WITH_FLAGS, DDL writes `d1_dlk.stg_sdh.*` / `d1_std.sdh.*` |
| P1a STGDELTA catalogs | 13e93bd | pass |
| P1b TGT_LOAD_OPTION vocabulary | f247020 | pass |
| P1c FREQUENCY token | f346e3b | pass |
| P1d `{landing_rel}` / `{domain_path}` | 494b38a | pass |
| P1e `src_columns_style: named` | 663f031 | pass |
| P1f header / footer flags | 0e14ce7 | pass |
| P2 `scripts/iig_scorecard.py` | 4b0c1ce | pass |
| Wrap: 0.5.8.post7, suite 797 passed / 27 skipped, ruff clean, scrub 0 | e743147 | pushed |
| Follow-up: path shapes + `named` in the overlay, overlay path citations, scorecard caseless types / fixture LOB, the ACFC run section; 0.5.8.post8 | see `git log` | pushed |

## ACFC run — the Socially Determined (MIDS) pair

No env change: `load_config` ALWAYS applies `config/overlays/acfc_env.yaml`
first; `CODEGEN_CONFIG_OVERLAYS` adds overlays on top (later wins);
`CODEGEN_SKIP_ENV_OVERLAY=1` opts out (stderr: `config overlays (in order): …`;
the App's startup line and `GET /api/health` list them too).
Run from the repo root of the ACFC checkout; `$PAIR` is the folder holding the
pair's FRD `.docx` and STTM `.xlsx` (names as they sit in that folder).

```bash
PAIR="<pair folder>"; FRD="$PAIR/<MIDS Socially Determined FRD>.docx"
STTM="$PAIR/<MIDS Socially Determined STTM>.xlsx"; mkdir -p work

# 1. layout (writes the pair-resolved FRD contract; stops when roles stay open)
python -m codegen.cli layout --workbook "$STTM" --frd "$FRD" \
    --frd-contract-out work/frd.contract.json --profile-out work/sttm.layout.json \
    --report-unresolved work/unresolved_headers.md --require-complete \
    [--answers "$PAIR/answers.yaml"]

# 2. extract the STTM mapping contract
python -m codegen.cli extract-sttm --workbook "$STTM" \
    --frd-contract work/frd.contract.json --layout work/sttm.layout.json \
    --out work/sttm.contract.json

# 3. generate — all three feeds of the pair (add --feed <feed_id> for one)
python -m codegen.cli generate --frd-contract work/frd.contract.json \
    --sttm-contract work/sttm.contract.json --output-mode framework \
    --profile acfc_prx --iig-template iig_v2 --skip-tests [--dry-run]

# 4. score the community-demographic feed against the real row
python scripts/iig_scorecard.py \
    --generated out/<feed>/framework/<feed>_IIG.xlsx \
    --real "IIG test cells.xlsx" --sheet ADLS_DELTA_INGESTION_DETAILS \
    --real-table sd_community_demographic_risk --generated-table <generated name>

# 5. score EVERY sheet (rows paired by key) against a golden or a real full IIG
#    workbook (multi-table step 7, 2026-10-08)
python scripts/iig_scorecard.py --all-sheets     --generated out/<feed>/framework/<feed>_IIG.xlsx --real "<real IIG>.xlsx"     [--summary-only | --matches] [--alias generated=real ...]
```

In `--all-sheets` mode the review copy next to `--generated` supplies the owners
of open cells; rows pair by key (schedule / notebooks by PIPELINE_NAME, ADLS by
SRC_FILE_NAME, STGDELTA by table, DQ by file + RULE_CLASS, fixed-width by
SEGMENT, email by STATUS); the last line is `TOTAL (8 sheets): score S; paired P,
real-only R, generated-only G; cells …` with score = 100 × (matched + alias) /
cells.

**Reading the score (2026-10-08).** The raw score is NOT a defect rate: most
non-matching cells are open on purpose. Every score line (each sheet and TOTAL)
ends with a breakdown:

```
… | matched M / open-by-design B / open-for-engineer E / diff D; score excl. open-by-design X
```

- **matched** = MATCH + ALIAS.
- **open-by-design** = OPEN cells no input document can state: engineer-assigned
  ids (PIPELINE_ID, GROUP_ID, OBJECT_ID …), environment connections / containers
  / workspace handles, and the audit stamps (dates set at load, CREATED_BY /
  UPDATED_BY = the RFC number). Read from the review copy's reason
  (`framework-assigned …`, `audit date …`, `audit by …`); a cell with no review
  entry falls back to the column list `BY_DESIGN_COLUMNS` in the script.
- **open-for-engineer** = every other OPEN cell — a value someone has to supply
  (engineer, BSA, or an FAQ answer).
- **diff** = generated ≠ real — the only class that can be a defect (on the
  goldens, each one is a pinned, reasoned deviation).
- **score excl. open-by-design** X = 100 × matched / (cells − open-by-design).

Generated pair 1 against its golden today: `score 57.9 … | matched 347 /
open-by-design 185 / open-for-engineer 46 / diff 21; score excl. open-by-design
83.8` — of the 42 % that is not matched, 185 cells are ids / environment /
audit values no document carries, 46 are cells to supply, 21 are the pinned
deviations.

`<feed>` is the feed slug `generate` prints on its verdict line (`PASS_WITH_FLAGS
<feed> — …`); `<generated name>` is that feed's `TGT_TABLE_NAME` — on the real
documents the STTM stage table, `sd_community_demographic_risk`. Both IIG
workbooks land in `out/<feed>/framework/` (`<feed>_IIG.xlsx`, the clean copy;
`<feed>_IIG_REVIEW.xlsx`, the review copy). With `CODEGEN_STORAGE_OUTPUTS` set,
`out/` is that role's working copy. The real workbook has one sheet, so
`--sheet` selects the generated sheet and the real side falls back to its first
sheet. On the real documents nothing is aliased: the table names agree, so the
LOB rule is off; pass `--alias x=x` to switch the CV name aliases off too.

Notebook alternative: `acfc_run.py` with widgets `conventions_profile =
acfc_prx`, `iig_template = iig_v2` runs steps 1–3 (its `generate` passes
`--output-mode framework --skip-tests`).
