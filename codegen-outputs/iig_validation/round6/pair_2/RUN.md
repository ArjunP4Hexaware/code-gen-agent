# round 6 · pair_2 — scripts/run_round.py

- <STTM>: `/Workspace/Users/<me>/…/<STTM>`
- <FRD>: `/Workspace/Users/<me>/…/<FRD>`
- answers: none given (the layout resolves everything itself, or the round stops)
- **exit 0** — ok

## Fingerprint (structure only; file#1 = <STTM>, file#2 = <FRD>)

```
file#1 sha256=16e06c698d73093812fc033ccab8877be77570563188566d13b27336ca927ed8 size=61141 kind=xlsx
  sheet[0] name#cf4939941de0 visible max_row=4 max_column=5 nonblank_rows=4 nonblank_cells=14 formulas=0 merged=0 header_row=1 header#b4eb40c2a79931b1 body#-
    columns: A=3 B=3 C=0 D=0 E=3
  sheet[1] name#c64ff2203055 visible max_row=12 max_column=8 nonblank_rows=4 nonblank_cells=13 formulas=0 merged=1 header_row=7 header#44d7334ac66f9a41 body#-
    columns: E=2 F=2 G=2 H=2
  sheet[2] name#01292dd6fa7b visible max_row=92 max_column=16 nonblank_rows=92 nonblank_cells=1368 formulas=0 merged=3 header_row=2 header#a7c7e50d9108357b body#-
    columns: A=90 B=90 C=90 D=90 E=90 F=90 G=90 H=90 I=90 J=90 K=90 M=90 N=90 O=90 P=90
  sheet[3] name#ef35f6a78545 visible max_row=273 max_column=16 nonblank_rows=273 nonblank_cells=4079 formulas=0 merged=3 header_row=2 header#1cadd93b4c2f66e9 body#-
    columns: A=271 B=271 C=267 D=271 E=271 F=271 G=271 H=271 I=271 J=271 K=271 M=271 N=271 O=271 P=271
  sheet[4] name#a60e2e099a94 visible max_row=52 max_column=18 nonblank_rows=52 nonblank_cells=816 formulas=0 merged=3 header_row=2 header#52901527b4eeabb6 body#-
    columns: A=50 B=50 C=50 D=49 E=50 F=46 G=50 H=50 I=50 J=50 K=50 L=50 N=50 O=50 P=50 Q=50 R=1
file#2 sha256=9311156530a39ad61321b6ddb8ff054fb133fb4d270886cac8ed0dd43eb280b2 size=321367 kind=docx
  document_xml_sha256=481416665c19751f paragraphs=966 nonempty_paragraphs=693 top_level_tables=40 tables=44 rows=273 cells=677 text_hash=311c437cd18ebdd0
```

## Document gate (--compare reference vs this run's documents)

reference: `docs/acfc/fingerprints/pair_2_sd_home.json` · key id `73fc1ff0`

```
WARN file#1 vs file#1: sha256 differs; size 60905 vs 61141
WARN file#1 vs file#1 sheet[2] name#01292dd6fa7b: body_hash differs; column hashes differ: J, O
WARN file#1 vs file#1 sheet[3] name#ef35f6a78545: body_hash differs; column hashes differ: J, O
WARN file#1 vs file#1 sheet[4] name#a60e2e099a94: body_hash differs; column hashes differ: K, P
WARN file#2 vs file#2: sha256 differs
```

pass (WARN lines are recorded, not a stop)

## Build

`build a7f98fc on feature/multi-table, committed 2026-10-13T01:15:03-04:00 (git)`
HEAD `a7f98fc`

## CLI (harness env: mock layout + provider, synthetic e-mail, local storage under <work>)

- `codegen layout --workbook <STTM> --frd <FRD> --require-complete --frd-contract-out <work>/frd.json` → exit 0
  first line: `codegen 0.5.8.post32 from <repo>/src/codegen/__init__.py · profile: acfc_prx · IIG template: iig_v2 · overlays: config/overlays/acfc_env.yaml`
  NOTE `feeds[1].file_name_patterns`
- `codegen extract-sttm --workbook <STTM> --frd-contract <work>/frd.json --out <work>/sttm.json` → exit 0
  first line: `codegen 0.5.8.post32 from <repo>/src/codegen/__init__.py · profile: acfc_prx · IIG template: iig_v2 · overlays: config/overlays/acfc_env.yaml`
- `codegen generate --frd-contract <work>/frd.json --sttm-contract <work>/sttm.json --output-mode framework --profile acfc_prx --iig-template iig_v2 --skip-tests --dry-run` → exit 0
  first line: `codegen 0.5.8.post32 from <repo>/src/codegen/__init__.py · profile: acfc_prx (--profile) · IIG template: iig_v2 (--iig-template) · overlays: config/overlays/acfc_env.yaml`
  verdicts: PASS_WITH_FLAGS ×3

## Golden (rebuilt on this SHA)

GROUP_ID exports found 6 of 6
pair_2/adls_delta_ingestion_details: dedup 3 -> 3; rows by number of contributing exports {1: 3}; GROUP_ID on the rows: ['180251', '180253', '180255']
pair_2/all_files_static_information: dedup 18 -> 3; rows by number of contributing exports {6: 3}
pair_2/data_factory_pipeline_schedule: dedup 36 -> 6; rows by number of contributing exports {6: 6}
pair_2/data_quality_rules: dedup 11 -> 10; rows by number of contributing exports {1: 9, 2: 1}; GROUP_ID on the rows: ['180251', '180252', '180254', '180255', '180256']
pair_2/databricks_notebook_details: dedup 6 -> 6; rows by number of contributing exports {1: 6}; GROUP_ID on the rows: ['180251', '180252', '180253', '180254', '180255', '180256']
pair_2/stgdelta_stddelta_ingestion_det: dedup 3 -> 3; rows by number of contributing exports {1: 3}; GROUP_ID on the rows: ['180252', '180254', '180256']

## Rows per sheet (agent vs de-duplicated golden)

adls_delta_ingestion_details: agent 3 rows · golden 3 rows (deduped) · paired 2
all_files_static_information: agent 3 rows · golden 3 rows (deduped) · paired 0
data_factory_pipeline_schedule: agent 12 rows · golden 6 rows (deduped) · paired 0
data_quality_rules: agent 0 rows · golden 10 rows (deduped) · paired 0
databricks_notebook_details: agent 6 rows · golden 6 rows (deduped) · paired 6
stgdelta_stddelta_ingestion_det: agent 3 rows · golden 3 rows (deduped) · paired 2
ADLS_FIXED_WIDTH_HANDLER: agent 0 rows · golden 0 rows (deduped) · paired 0
EMAIL_TEMPLATE_CONFIG: agent 6 rows · golden 0 rows (deduped) · paired 0

## Score (key-paired, agreed ignore set)

TOTAL 17.2 over 885 scored cells; agent IIG workbooks: 3
