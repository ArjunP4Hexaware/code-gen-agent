# IIG scorecard — 2026-10-07 (IIG-first demo, `feature/iig-first`)

What the generated `ADLS_DELTA_INGESTION_DETAILS` row for the Socially
Determined community-demographic feed gets right, measured against the REAL
`demographics_package` row (`IIG test cells.xlsx`, read in place at the repo
root, gitignored, never copied). The generated side is the CV golden pair —
the anonymised copy of the same feed (`cv_` = `sd_`, `sdh` = `sdoh`, the
vendor name) — so name-only differences score **ALIAS**, not DIFF.
`CREATED_BY` / `UPDATED_BY` values are never printed.

## Scorecard

Committed state (`config/overlays/acfc_env.yaml` applied by default, the
shipped `iig_v2` path shapes, `src_columns_style: positional`):

```
filled 38/55, matched 31, alias 3, open 10 (BSA 5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 11
```

Demo configuration — the same plus the per-feed path shapes (P1d) and
`src_columns_style: named` (P1e), which go in an overlay (not committed):

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
DIFF  LOB                        real 'MIDS' | generated 'OHDS'
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
DIFF  TGT_DATA_TYPE              (case only) real 90 items ['String', 'String', 'String'] | generated 90 items ['String', 'String', 'String']; first difference at item 87: 'string' vs 'String'
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
filled 38/55, matched 32, alias 7, open 10 (BSA 5, Engineer 3, Engineer-confirm 0, CI/CD 2), diff 6
```

Five rows move between the two runs: `SRC_ADLS_PATH`, `SRC_ADLS_ARCHVL_PATH`,
`TGT_ADLS_PATH` and `TGT_RJT_ADLS_PATH` go from DIFF to ALIAS (the landing
loses its `/mftlanding` container prefix, the target paths drop `inbound/`
and use `Reject/`), and `SRC_COLUMNS` goes from DIFF to MATCH
(`zip_code:zip_code`).

## Where the 54 template cells came from (demo configuration)

| Source | Cells | Columns |
| --- | --- | --- |
| **ACFC overlay**: environment constants, badged synthetic, tooltip names `config/overlays/acfc_env.yaml` | 6 | SRC_ADLS_CONNECTION_ID, METADATA_CONNECTION_ID, TGT_CONNECTION_ID, SRC_CONTAINER_NAME, TGT_CONTAINER_NAME, SCHEMA_DRIFT_FLAG |
| **Overlay path shapes** applied to the FRD ADLS Location | 4 | SRC_ADLS_PATH, SRC_ADLS_ARCHVL_PATH, TGT_ADLS_PATH, TGT_RJT_ADLS_PATH |
| **FRD** | 13 | OBJECT_NAME, DOMAIN, SUBDOMAIN, SOURCE, FREQUENCY (token, P1c), LOB, SRC_FILE_NAME, SRC_FORMAT, SRC_FILE_DELIMITER, TGT_DATABASE_NAME, TGT_TABLE_NAME, TGT_LOAD_OPTION (Overwrite, P1b), RECYCL_ENBL_FLG |
| **STTM** | 6 | SRC_COLUMNS, SRC_DATA_TYPE, MANDATORY_FIELD_LIST, TGT_COLUMN_NAMES, TGT_DATA_TYPE, TGT_PRIMARY_KEY |
| **Template constants**: framework vocabulary, shipped | 9 | ACTIVE_FLAG, SRC_COMPRESSION, MULTILINE_FLAG, TGT_FORMAT, TGT_RJT_TABLE_NAME, TGT_PARTITION_COLUMN, TGT_PARTITION_VALUE, RECYCL_TBL_NM, RECYCL_ADLS_PATH |
| **Open**: blank, flagged, owner in the review copy | 16 | see below |

The 55th real column, `FILE_METADATA`, is not in the `iig_v2` template. Its
real value is NULL, so it scores MATCH. The path-shape cells' tooltip still
reads "synthetic path shape from the template". It does not yet say that an
overlay supplied the shape.

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
| LOB | `MIDS` vs `OHDS` | the fixture's LOB, possibly anonymised. It is not in the alias list |
| TGT_DATA_TYPE | case only, first at item 87: `string` vs `String` | the REAL row mixes `String` and `string`. The generated row is consistent |
| TGT_PRIMARY_KEY | `NULL` vs `zip_code` | the mapping contract's natural key, while the real row states none. Question for the framework team: is the PK used for a truncate-and-load feed? |

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

## The ACFC run

The overlay needs no env change. `load_config` applies
`config/overlays/acfc_env.yaml` whenever `CODEGEN_CONFIG_OVERLAYS` is unset,
and prints one stderr line, `config overlay (default): …`. To add the path
shapes and `named` for the demo, either add the block above to
`config/overlays/acfc_env.yaml` in the ACFC checkout, or keep it in a second
file and list both files, because an explicit value replaces the default:

```bash
export CODEGEN_CONFIG_OVERLAYS="config/overlays/acfc_env.yaml;<path>/sdoh_paths.yaml"
```

Notebook path: run `acfc_run.py` with widgets `conventions_profile = acfc_prx`
and `iig_template = iig_v2`. Its `generate` step already passes
`--output-mode framework --skip-tests`.

CLI path, run in the pair's working directory after `codegen layout …
--frd-contract-out frd.contract.json` and `codegen extract-sttm … --out
sttm.contract.json`:

```bash
python -m codegen.cli generate --frd-contract frd.contract.json \
    --sttm-contract sttm.contract.json --output-mode framework \
    --profile acfc_prx --iig-template iig_v2 --skip-tests [--dry-run]
```

Both IIG workbooks land in `<outputs>/<feed_slug>/framework/`:
`<feed_slug>_IIG.xlsx` (clean copy) and `<feed_slug>_IIG_REVIEW.xlsx` (review
copy). To score one against the real rows:

```bash
python scripts/iig_scorecard.py \
    --generated <outputs>/sd_community_demographic_risk/framework/sd_community_demographic_risk_IIG.xlsx \
    --real "IIG test cells.xlsx" --real-table sd_community_demographic_risk
```

On the real documents nothing needs aliasing. Pass `--alias x=x` to switch
the CV defaults off.
