# EDH_E2E_READER_RUN — the gold reader on the 11 real v2.1 files

> **Run** (2026-10-20, D1 container, `.venv-d1`, nothing installed): `codegen
> read-edh-e2e --input <scratch copy of the v2.1 volume folder> --table <i> --out
> <scratch>/m<i>.json`, once per manifest index, so that a crash in one table could not hide
> another. The config is the tracked one plus `acfc_env.yaml`. **No `edh_e2e` profile
> values were set**, so every profile-owned role is asked (§3).
> **Counts only**: tables are manifest indices `m<i>`; no table, column, region, cell or
> expression text appears here. The contracts and the printed lines (which quote free-text
> cells) stayed in the scratch directory.
> Reader: `src/codegen/layouts/edh_e2e.py`; contract: `src/codegen/contracts/gold.py`;
> dialect: `EDH_E2E_JSON_SCHEMA.md`.

## 1. Outcome

| Table | Rows | Blocks | Regions | Filled | Proposed | QUESTION | Flags | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m0 | 11 | 1 | 7 | 48 | 1 | 5 | 0 | 3 |
| m1 | 98 | 2 | 7 | 380 | 3 | 22 | 0 | 3 |
| m2 | 55 | 1 | 28 | 161 | 56 | 23 | 0 | 3 |
| m3 | 9 | 1 | 7 | 32 | 11 | 11 | 1 | 3 |
| m4 | 63 | 1 | 7 | 241 | 0 | 35 | 0 | 3 |
| m5 | 7 | 1 | 7 | 28 | 3 | 13 | 1 | 3 |
| m6 | 75 | 1 | 7 | 291 | 22 | 46 | 1 | 3 |
| m7 | 11 | 1 | 7 | 46 | 0 | 5 | 0 | 3 |
| m8 | 4 | 1 | 7 | 22 | 0 | 5 | 0 | 3 |
| m9 | 49 | 1 | 7 | 193 | 2 | 27 | 8 | 3 |
| m10 | 6 | 2 | 7 | 28 | 0 | 8 | 0 | 3 |
| **all** | 388 | 13 | 98 | **1,470** | **98** | **200** | 11 | — |

- **No table crashed.** All 11 exit 3 (NEEDS_ANSWERS: at least one QUESTION each), so
  `first_error_line` is `None` for every table.
- The printed lines match the contract: QUESTION lines = questions and INPUT_NEEDED lines =
  proposals, on every table.
- The 11 flags are 3 kinds: `edh_drag_fill` (7, m9) and `edh_region_column_not_identifier`
  (4 tables).

## 2. By role (filled / proposed / QUESTION)

| Role | m0 | m1 | m2 | m3 | m4 | m5 | m6 | m7 | m8 | m9 | m10 | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `target_catalog` | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 11/0/0 |
| `target_table` | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 11/0/0 |
| `target_schema` | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/11 |
| `load_mode` | 0/0/1 | 1/0/0 | 0/0/1 | 0/0/1 | 1/0/0 | 0/0/1 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 0/0/1 | 6/0/5 |
| `primary_key` | 4/0/0 | 6/0/0 | 1/0/0 | 3/0/0 | 4/0/0 | 3/0/1 | 2/0/0 | 0/0/1 | 3/0/0 | 1/0/0 | 2/0/0 | 29/0/2 |
| `scd2_mode` | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/11 |
| `sk_strategy` | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/11 |
| `source_table` | 10/0/0 | 80/0/0 | 52/0/0 | 8/0/0 | 62/0/1 | 6/0/0 | 70/0/0 | 10/0/0 | 4/0/0 | 45/0/0 | 6/0/0 | 353/0/1 |
| `source_catalog_schema` | 0/0/1 | 0/0/17 | 0/0/9 | 0/0/3 | 0/0/6 | 0/0/3 | 0/0/17 | 0/0/1 | 0/0/2 | 0/0/6 | 0/0/4 | 0/0/69 |
| `target_type` | 10/1/0 | 98/0/0 | 51/4/0 | 9/0/0 | 63/0/0 | 5/1/1 | 75/0/0 | 11/0/0 | 4/0/0 | 49/0/0 | 6/0/0 | 381/6/1 |
| `nullable` | 11/0/0 | 98/0/0 | 55/0/0 | 9/0/0 | 63/0/0 | 6/0/0 | 74/1/0 | 11/0/0 | 4/0/0 | 49/0/0 | 6/0/0 | 386/1/0 |
| `expression` | 11/0/0 | 95/1/2 | 0/52/3 | 1/7/1 | 44/0/18 | 6/0/1 | 60/0/15 | 11/0/0 | 4/0/0 | 34/0/15 | 6/0/0 | 272/60/55 |
| `join` | · | · | · | · | 2/0/2 | · | 0/18/0 | · | · | · | · | 2/18/2 |
| `filter` | · | 0/2/0 | 0/0/6 | 0/0/2 | 0/0/3 | · | 7/0/10 | · | · | 12/0/1 | · | 19/2/22 |
| `region_drift` | · | · | · | 0/4/0 | · | 0/2/0 | 0/3/0 | · | · | 0/2/0 | · | 0/11/0 |
| `document_note` | · | · | 0/0/1 | 0/0/1 | · | 0/0/1 | 0/0/1 | · | · | 0/0/2 | · | 0/0/6 |
| `rule` | · | · | · | · | 0/0/2 | 0/0/2 | · | · | · | · | · | 0/0/4 |

`·` = the role does not occur in that table.

**How the cells are counted:**
- **Per row:** `primary_key`, `source_table`, `target_type`, `nullable` and `expression`.
- **Per distinct cell text and block:** `join` and `filter`. One cell can yield two joins
  (a second joined table) or several filters.
- **Per distinct `(database, table)` in a block:** `source_catalog_schema`.

## 3. What the 200 questions are

| Kind | Questions | Closed by |
| --- | --- | --- |
| Profile-owned values, asked because the profile is empty: `target_schema` 11, `scd2_mode` 11, `sk_strategy` 11, `source_catalog_schema` 69 | 102 | `edh_e2e.target_schema`, `scd2_mode`, `sk_strategy`, `source_catalog_map`. The 69 source questions name few distinct source databases (v2.0: 1–3 per file), so a handful of map entries closes them all |
| `expression`, unmapped zero-argument function | 17 | `edh_e2e.function_map` (2 function names) |
| `expression`, outside the translated grammar (an `if` without `ELSE` 9; text after a complete expression 10; a character outside the grammar 7; an `if` missing its `THEN` 2; an untranslated function 1; a stray `.` 1; `CONVERT` with character-set arguments 1) | 31 | a person: the cell is quoted in the question |
| `expression`, no `mapping_edits` and no source field / table | 7 | a person |
| `filter`, free text or an equality whose left side is several words | 22 | a person: the cell is quoted |
| `join`, alias-only tables (J3) | 2 | a person |
| `load_mode` null | 5 | a person or the profile |
| `document_note` (`space_in_name` 4, `drag_fill` 1, `region_label_nonstandard` 1) | 6 | a person |
| `rule` (free-text rules) | 4 | a person |
| `primary_key`: a non-PK `indexes` cell (1), a table with no PK marker (1) | 2 | a person |
| `target_type`: all regions give a sentinel | 1 | a person |
| `source_table`: a direct move without a source table | 1 | a person |

## 4. What is proposed (98)

| Proposal | Count |
| --- | --- |
| `expression`: no `mapping_edits` cell (m2 has none), so a direct move of `source_field` is proposed | 60 |
| `join`: one column named, assumed to have the same name on both sides (J1 / J2) | 18 |
| `region_drift`: a column present in some regions only | 11 |
| `target_type`: regions disagree, or a region states a sentinel (the most common type is proposed) | 6 |
| `filter`: the F4 slash notation, read as a validity window | 2 |
| `nullable`: NOT NULL in some regions only | 1 |

## 5. Not exercised by the real set

- The reader translates `CAST(<x> AS <type>)` and F3 / F5 functions it does not know (kept
  as proposals). The tests drive these paths; the real set does not reach them.
- The empty-regions case occurs only in synthetic fixture (b).
