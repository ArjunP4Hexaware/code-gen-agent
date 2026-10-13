# pair_2 (SD) — round 5 — D1 Git folder

## Step 1 — Code
```
build 5411014 on feature/multi-table, committed 2026-10-13T00:03:49-04:00 (git)
git rev-parse --short HEAD → 5411014
codegen 0.5.8.post30
```

## Step 2 — Fingerprint
```
file#1 sha256=16dc274ec1cc0aac06f0bd11d5c14778271b749d8a8f0872005dfd8f3e2d5302 size=38003 kind=xlsx
  sheet[0] name#cf4939941de0 visible max_row=6 max_column=5 nonblank_rows=5 nonblank_cells=18 formulas=0 merged=0 header_row=1 header#b4eb40c2a79931b1 body#3dd9d300cbb449da
    columns: A=4 B=3 C=3 D=0 E=3
  sheet[1] name#c64ff2203055 visible max_row=2 max_column=4 nonblank_rows=2 nonblank_cells=8 formulas=0 merged=0 header_row=1 header#4b33f239e45efcc5 body#fa472488e246175d
    columns: A=1 B=1 C=1 D=1
  sheet[2] name#cc199f5fd4b8 visible max_row=92 max_column=18 nonblank_rows=92 nonblank_cells=985 formulas=0 merged=0 header_row=2 header#f27e6ee42023843a body#2e3d33456a2adec0
    columns: A=90 B=86 C=86 D=86 E=86 F=86 G=86 H=0 J=0 K=0 L=90 M=90 O=0 P=0 Q=90 R=90
  sheet[3] name#cae3b1f83b5f visible max_row=273 max_column=18 nonblank_rows=273 nonblank_cells=2972 formulas=0 merged=0 header_row=2 header#f27e6ee42023843a body#0b51a0315dd83d01
    columns: A=271 B=267 C=267 D=263 E=267 F=267 G=267 H=0 J=0 K=0 L=271 M=271 O=0 P=0 Q=271 R=271
  sheet[4] name#ca7596506ae7 visible max_row=52 max_column=18 nonblank_rows=52 nonblank_cells=590 formulas=0 merged=0 header_row=2 header#f27e6ee42023843a body#72a898e7a610af73
    columns: A=50 B=46 C=46 D=45 E=46 F=46 G=46 H=46 J=0 K=0 L=50 M=50 O=0 P=0 Q=50 R=50
file#2 sha256=9311156530a39ad61321b6ddb8ff054fb133fb4d270886cac8ed0dd43eb280b2 size=321367 kind=docx
  document_xml_sha256=481416665c19751f paragraphs=966 nonempty_paragraphs=693 top_level_tables=40 tables=44 rows=273 cells=677 text_hash=311c437cd18ebdd0
```

## Step 3 — CLI layout (exit 3 — NEEDS_ANSWERS)

**Command:** `python -m codegen.cli layout --workbook <STTM> --frd <FRD> --require-complete --frd-contract-out /tmp/r5/frd.json --answers /tmp/r5/answers.yaml`
- `<STTM>` = `inputs/databricks/STTM_Medicare Expansion-MIDS - Socially Determined (1).xlsx`
- `<FRD>` = `inputs/databricks/FRD_Medicare Expansion-MIDS - Socially Determined (1).docx`
- **Exit:** 3
- **First line:** `ANSWERS         1 answer(s) applied from /tmp/r5/answers.yaml (source=user)`
- **Verdict:** `NEEDS_ANSWERS   layout — 14 answer(s) owed (--require-complete); nothing is wrong with the documents`

**QUESTION keys (14):**
1. `feeds[0].file_name_patterns`
2. `feeds[0].stage_target.schema`
3. `feeds[0].stage_target.tables`
4. `feeds[0].standard_target.schema`
5. `feeds[0].standard_target.tables`
6. `feeds[1].stage_target.schema`
7. `feeds[1].stage_target.tables`
8. `feeds[1].standard_target.schema`
9. `feeds[1].standard_target.tables`
10. `feeds[2].file_name_patterns`
11. `feeds[2].stage_target.schema`
12. `feeds[2].stage_target.tables`
13. `feeds[2].standard_target.schema`
14. `feeds[2].standard_target.tables`

extract-sttm and generate skipped (exit 3 → step 4, skip step 5).

## Step 4 — Golden (rebuilt on 5411014)

```
pair_2/EMAIL_TEMPLATE_CONFIG: dedup 12 -> 12; rows by number of contributing exports {1: 12}
pair_2/adls_delta_ingestion_details: dedup 3 -> 3; rows by number of contributing exports {1: 3}; GROUP_ID on the rows: ['180251', '180253', '180255']
pair_2/all_files_static_information: dedup 18 -> 3; rows by number of contributing exports {6: 3}
pair_2/data_factory_pipeline_schedule: dedup 36 -> 6; rows by number of contributing exports {6: 6}
pair_2/data_quality_rules: dedup 11 -> 10; rows by number of contributing exports {1: 9, 2: 1}; GROUP_ID on the rows: ['180251', '180252', '180254', '180255', '180256']
pair_2/databricks_notebook_details: dedup 6 -> 6; rows by number of contributing exports {1: 6}; GROUP_ID on the rows: ['180251', '180252', '180253', '180254', '180255', '180256']
pair_2/stgdelta_stddelta_ingestion_det: dedup 3 -> 3; rows by number of contributing exports {1: 3}; GROUP_ID on the rows: ['180252', '180254', '180256']
```

GROUP_IDs 180251–180256 stay.

## Step 5 — SKIPPED (layout exit 3)
