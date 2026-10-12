# round 5 · pair_2 (SD) — D1 Git folder

## Step 1 — code

```
build 363c523 on feature/multi-table, committed 2026-10-12T16:03:01-04:00 (git)
```
SHA: `363c523` · version: `0.5.8.post29`

## Step 2 — fingerprint

**Hash check FAILED.** Expected <STTM> sha256 prefix `464ad181`, got `e1ed74dc`.
Expected <FRD> sha256 prefix `795091c7`, got `f27e2b6d`.
No `_blank_version.xlsx` found in the pair folder or anywhere in the workspace/volumes.

```
file#1 sha256=e1ed74dc2a2909a0c314d8f1039533479e2e5a363f8e4908ce0ba4a8852140d6 size=10711 kind=xlsx
  sheet[0] name#cf4939941de0 visible max_row=4 max_column=5 nonblank_rows=4 nonblank_cells=20 formulas=0 merged=0 header_row=1 header#b4eb40c2a79931b1 body#370e7fa39e149d70
    columns: A=3 B=3 C=3 D=3 E=3
  sheet[1] name#c64ff2203055 visible max_row=2 max_column=4 nonblank_rows=2 nonblank_cells=8 formulas=0 merged=0 header_row=1 header#4b33f239e45efcc5 body#034740207bbef271
    columns: A=1 B=1 C=1 D=1
  sheet[2] name#cc199f5fd4b8 visible max_row=15 max_column=16 nonblank_rows=15 nonblank_cells=224 formulas=0 merged=0 header_row=2 header#8cad0a5cfc24b93a body#eb7eae73199ef8c4
    columns: A=13 B=13 C=13 D=13 E=13 F=13 G=13 H=10 I=13 J=13 K=13 L=13 M=13 N=13 O=13 P=13
  sheet[3] name#cae3b1f83b5f visible max_row=17 max_column=16 nonblank_rows=17 nonblank_cells=256 formulas=0 merged=0 header_row=2 header#8cad0a5cfc24b93a body#ede05e8188aad931
    columns: A=15 B=15 C=15 D=15 E=15 F=15 G=15 H=12 I=15 J=15 K=15 L=15 M=15 N=15 O=15 P=15
  sheet[4] name#ca7596506ae7 visible max_row=15 max_column=16 nonblank_rows=15 nonblank_cells=224 formulas=0 merged=0 header_row=2 header#8cad0a5cfc24b93a body#2ca925215b8be344
    columns: A=13 B=13 C=13 D=13 E=13 F=13 G=13 H=10 I=13 J=13 K=13 L=13 M=13 N=13 O=13 P=13
file#2 sha256=f27e2b6d787b370ae79cf1855563402c4db2a1e96c4104a4977d361a81fad4c7 size=3857 kind=docx
  document_xml_sha256=41d99f09f4d459a6 paragraphs=582 nonempty_paragraphs=468 top_level_tables=22 tables=22 rows=196 cells=581 text_hash=34596370b1e5b688
```

file#1 = <STTM> (filled, synthetic fixture).
file#2 = <FRD> (synthetic fixture).
Searched fixture dir, `inputs/databricks/`, Volume `codegen_workbooks_in/`,
Volume `codegen_inputs/`. The synthetic fixture pair was the only pair_2
candidate; no file matching `*_blank_version.xlsx` exists.

**STOP** — hash gate (step 0). Steps 3–5 skipped.
