# round 5 · pair_2 (SD) — D1 Git folder

## Step 1 — code

```
build 363c523 on feature/multi-table, committed 2026-10-12T16:03:01-04:00 (git)
```
SHA: `363c523` · version: `0.5.8.post29`

## Step 2 — fingerprint

<STTM> sha256 `16e06c69` (expected `464ad181`); <FRD> sha256 `93111565` (expected `795091c7`).
**Gate override (approved):** <FRD> passes on text_hash. <STTM>: every count, extent,
header and column-fill matches the home copy; only mapping-sheet body_hash differs
(expected — home copy was anonymized). Continuing with file#2 as <STTM>.

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
file#2 sha256=16e06c698d73093812fc033ccab8877be77570563188566d13b27336ca927ed8 size=61141 kind=xlsx
  sheet[0] name#cf4939941de0 visible max_row=4 max_column=5 nonblank_rows=4 nonblank_cells=14 formulas=0 merged=0 header_row=1 header#b4eb40c2a79931b1 body#1ef724b1faa83758
    columns: A=3 B=3 C=0 D=0 E=3
  sheet[1] name#c64ff2203055 visible max_row=12 max_column=8 nonblank_rows=4 nonblank_cells=13 formulas=0 merged=1 header_row=7 header#44d7334ac66f9a41 body#5b58d0d8d589e163
    columns: E=2 F=2 G=2 H=2
  sheet[2] name#01292dd6fa7b visible max_row=92 max_column=16 nonblank_rows=92 nonblank_cells=1368 formulas=0 merged=3 header_row=2 header#a7c7e50d9108357b body#1db22486e7ff6775
    columns: A=90 B=90 C=90 D=90 E=90 F=90 G=90 H=90 I=90 J=90 K=90 M=90 N=90 O=90 P=90
  sheet[3] name#ef35f6a78545 visible max_row=273 max_column=16 nonblank_rows=273 nonblank_cells=4079 formulas=0 merged=3 header_row=2 header#1cadd93b4c2f66e9 body#a9fbfe6d0814c72e
    columns: A=271 B=271 C=267 D=271 E=271 F=271 G=271 H=271 I=271 J=271 K=271 M=271 N=271 O=271 P=271
  sheet[4] name#a60e2e099a94 visible max_row=52 max_column=18 nonblank_rows=52 nonblank_cells=816 formulas=0 merged=3 header_row=2 header#52901527b4eeabb6 body#f4ddaecb02334bcc
    columns: A=50 B=50 C=50 D=49 E=50 F=46 G=50 H=50 I=50 J=50 K=50 L=50 N=50 O=50 P=50 Q=50 R=1
file#3 sha256=9311156530a39ad61321b6ddb8ff054fb133fb4d270886cac8ed0dd43eb280b2 size=321367 kind=docx
  document_xml_sha256=481416665c19751f paragraphs=966 nonempty_paragraphs=693 top_level_tables=40 tables=44 rows=273 cells=677 text_hash=311c437cd18ebdd0
```

file#1 = <STTM_BLANK> · file#2 = <STTM> (filled) · file#3 = <FRD>

## Step 3 — CLI clean

layout (<STTM>, <FRD>) · exit 0 · `codegen 0.5.8.post29 ... · profile: acfc_prx · IIG template: iig_v2 · overlays: config/overlays/acfc_env.yaml`
extract-sttm (<STTM>) · exit 0 · `EXTRACTED ... 3 feed(s): sd_community_demographic_risk (86 fields), sd_community_risk (267 fields), sd_individual_risk (46 fields)`
generate · exit 0 · `codegen 0.5.8.post29 ... · profile: acfc_prx (--profile) · IIG template: iig_v2 (--iig-template)`
Verdicts: 3 × PASS_WITH_FLAGS (sd_community_demographic_risk 41 flags, sd_community_risk 43 flags, sd_individual_risk 48 flags)

## Step 4 — golden (363c523)

pair_2 dedup (GROUP_IDs 180251–180256):
```
EMAIL_TEMPLATE_CONFIG: dedup 12 -> 12
adls_delta_ingestion_details: dedup 3 -> 3
all_files_static_information: dedup 18 -> 3
data_factory_pipeline_schedule: dedup 36 -> 6
data_quality_rules: dedup 11 -> 10
databricks_notebook_details: dedup 6 -> 6
stgdelta_stddelta_ingestion_det: dedup 3 -> 3
```
pair_2: 7 sheets, 43 total rows → pair_2_iig_golden.xlsx

## Step 5 — diff + scrubbed evidence

EMAIL_TEMPLATE_CONFIG: agent 6 rows · golden 12 rows (deduped) · paired 0 — score 0.0
adls_delta_ingestion_details: agent 3 rows · golden 3 rows (deduped) · paired 2 — score 40.2
all_files_static_information: agent 3 rows · golden 3 rows (deduped) · paired 0 — score 0.0
data_factory_pipeline_schedule: agent 12 rows · golden 6 rows (deduped) · paired 0 — score 0.0
data_quality_rules: agent 0 rows · golden 10 rows (deduped) · paired 0 — score 0.0
databricks_notebook_details: agent 6 rows · golden 6 rows (deduped) · paired 6 — score 46.2
stgdelta_stddelta_ingestion_det: agent 3 rows · golden 3 rows (deduped) · paired 2 — score 36.7
ADLS_FIXED_WIDTH_HANDLER: agent 0 rows · golden 0 rows (deduped) · paired 0 — score 100.0

**TOTAL: score 14.3** · exact 146 · normalized 6 · mismatch 16 · missing-in-agent 592 · extra-in-agent 305
