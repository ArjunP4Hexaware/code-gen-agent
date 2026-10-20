# EDH_E2E_READER_RUN — the gold reader on the 11 real v2.2 files

> **Run** `run_20261020T180637Z_fa5270e` (2026-10-20, D1 container, `.venv-d1`, nothing
> installed). The reader ran from the working tree on head `fa5270e` with the post78
> changes, which were committed after the run.
> - **Per-table runs:** `codegen read-edh-e2e --input <scratch copy of the v2.2 volume
>   folder> --table <i> --out <scratch>/m<i>.json`, once per manifest index, so that a crash
>   in one file could not hide another.
> - **Full run:** one more run over the whole manifest wrote the questions workbook (§5).
> - **Config:** the tracked one plus `acfc_env.yaml`. **No `edh_e2e` profile values were
>   set**, so every profile-owned role is asked (§3).
> - **Counts only:** files are manifest indices `m<i>` and feeds are `feeds[<i>]` indices.
>   No table, column, region, cell or expression text appears here. The contracts and
>   printed lines stayed in the scratch directory; the questions workbook (which quotes
>   cells) is in the state volume only.
> - **Code and docs:** reader `src/codegen/layouts/edh_e2e.py`; contract
>   `src/codegen/contracts/gold.py`; dialect `EDH_E2E_JSON_SCHEMA.md` (v2.2); profile
>   `ENVIRONMENT_ACFC.md` §h.

## 1. Outcome — one feed per target table

v2.2 has 390 rows in 11 files. m10's two blocks load two different tables, so the reader
emits **12 feeds**. The feed numbering is the same for a one-table run (`--table 10`)
and for the full run.

| Feed | File | Blocks | Rows | Regions | Filled | Proposed | QUESTION | Flags | Exit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | m0 | 0 | 11 | 7 | 48 | 10 | 6 | 0 | 3 |
| 1 | m1 | 0,1 | 98 | 7 | 462 | 3 | 22 | 0 | 3 |
| 2 | m2 | 0 | 55 | 28 | 211 | 56 | 23 | 0 | 3 |
| 3 | m3 | 0 | 9 | 7 | 38 | 11 | 11 | 1 | 3 |
| 4 | m4 | 0 | 63 | 7 | 291 | 0 | 35 | 0 | 3 |
| 5 | m5 | 0 | 7 | 7 | 32 | 3 | 13 | 1 | 3 |
| 6 | m6 | 0 | 75 | 7 | 358 | 22 | 46 | 1 | 3 |
| 7 | m7 | 0 | 11 | 7 | 54 | 0 | 5 | 0 | 3 |
| 8 | m8 | 0 | 4 | 7 | 26 | 0 | 5 | 0 | 3 |
| 9 | m9 | 0 | 49 | 7 | 237 | 2 | 27 | 8 | 3 |
| 10 | m10 | 0 | 4 | 7 | 18 | 0 | 9 | 0 | 3 |
| 11 | m10 | 1 | 4 | 7 | 18 | 0 | 8 | 0 | 3 |
| **all** | 11 files | 13 | 390 | — | **1,793** | **107** | **210** | 11 | — |

- **No file crashed.** All 11 per-table runs and the full run exit 3 (NEEDS_ANSWERS),
  so `first_error_line` is `None` everywhere.
- **The two counts agree:** the per-table QUESTION total (210) equals the full run's.
- **m10 → feeds 10 and 11:** one target, one block and 4 rows each. The file's
  `mixed_target` note is asked once, by feed 10, the feed of its lowest block.
- **m0's lengths are proposals** derived from `target_format` (9). Its 2 DATE columns
  have no length, so nothing is asked for them.
- **Against the v2.1 run** (388 rows): 1,470 filled / 98 proposed / 200 QUESTION. The new
  `length` role adds 321 filled and 9 proposed. The new feed and the 2 new note kinds add
  10 QUESTIONs.

## 2. By role (filled / proposed / QUESTION)

| Role | f0 | f1 | f2 | f3 | f4 | f5 | f6 | f7 | f8 | f9 | f10 | f11 | all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `target_catalog` | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 12/0/0 |
| `target_table` | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 12/0/0 |
| `target_schema` | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/12 |
| `load_mode` | 0/0/1 | 1/0/0 | 0/0/1 | 0/0/1 | 1/0/0 | 0/0/1 | 1/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 0/0/1 | 0/0/1 | 6/0/6 |
| `primary_key` | 4/0/0 | 6/0/0 | 1/0/0 | 3/0/0 | 4/0/0 | 3/0/1 | 2/0/0 | 0/0/1 | 3/0/0 | 1/0/0 | 1/0/0 | 1/0/0 | 29/0/2 |
| `scd2_mode` | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/12 |
| `sk_strategy` | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/1 | 0/0/12 |
| `source_table` | 10/0/0 | 80/0/0 | 52/0/0 | 8/0/0 | 62/0/1 | 6/0/0 | 70/0/0 | 10/0/0 | 4/0/0 | 45/0/0 | 3/0/0 | 3/0/0 | 353/0/1 |
| `source_catalog_schema` | 0/0/1 | 0/0/17 | 0/0/9 | 0/0/3 | 0/0/6 | 0/0/3 | 0/0/17 | 0/0/1 | 0/0/2 | 0/0/6 | 0/0/2 | 0/0/2 | 0/0/69 |
| `target_type` | 10/1/0 | 98/0/0 | 51/4/0 | 9/0/0 | 63/0/0 | 5/1/1 | 75/0/0 | 11/0/0 | 4/0/0 | 49/0/0 | 3/0/1 | 3/0/1 | 381/6/3 |
| `nullable` | 11/0/0 | 98/0/0 | 55/0/0 | 9/0/0 | 63/0/0 | 6/0/0 | 74/1/0 | 11/0/0 | 4/0/0 | 49/0/0 | 3/0/0 | 3/0/0 | 386/1/0 |
| `length` | 0/9/0 | 82/0/0 | 50/0/0 | 6/0/0 | 50/0/0 | 4/0/0 | 67/0/0 | 8/0/0 | 4/0/0 | 44/0/0 | 3/0/0 | 3/0/0 | 321/9/0 |
| `expression` | 11/0/0 | 95/1/2 | 0/52/3 | 1/7/1 | 44/0/18 | 6/0/1 | 60/0/15 | 11/0/0 | 4/0/0 | 34/0/15 | 3/0/1 | 3/0/1 | 272/60/57 |
| `join` | · | · | · | · | 2/0/2 | · | 0/18/0 | · | · | · | · | · | 2/18/2 |
| `filter` | · | 0/2/0 | 0/0/6 | 0/0/2 | 0/0/3 | · | 7/0/10 | · | · | 12/0/1 | · | · | 19/2/22 |
| `region_drift` | · | · | · | 0/4/0 | · | 0/2/0 | 0/3/0 | · | · | 0/2/0 | · | · | 0/11/0 |
| `document_note` | 0/0/1 | · | 0/0/1 | 0/0/1 | · | 0/0/1 | 0/0/1 | · | · | 0/0/2 | 0/0/1 | · | 0/0/8 |
| `rule` | · | · | · | · | 0/0/2 | 0/0/2 | · | · | · | · | · | · | 0/0/4 |

`·` = the role does not occur in that feed.

**How the cells are counted:**
- **Per row:** `primary_key`, `source_table`, `target_type`, `nullable`, `length`,
  `expression`.
- **Per distinct cell text and block:** `join` and `filter`.
- **Per distinct `(database, table)` in a block:** `source_catalog_schema`.
- **One per note / rule:** a file's notes and rules are asked once, not once per feed.

## 3. What the 210 questions are

| Kind | Questions | Closed by |
| --- | --- | --- |
| Profile-owned, asked because the profile is empty: `target_schema` 12, `scd2_mode` 12, `sk_strategy` 12, `source_catalog_schema` 69 | 105 | `edh_e2e.target_schema` / `scd2_mode` / `sk_strategy` / `source_catalog_map` (`ENVIRONMENT_ACFC.md` §h; `OPEN_QUESTIONS.md` §7.1–7.3) |
| `expression`, an unmapped zero-argument function | 17 | `edh_e2e.function_map` (`OPEN_QUESTIONS.md` §7.4) |
| `expression`, outside the translated grammar (text after a complete expression 12; an `if` without `ELSE` 9; a character outside the grammar 7; an `if` missing `THEN` 2; an untranslated function 1; a stray `.` 1; `CONVERT` with character-set arguments 1) | 33 | a person: the workbook quotes the cell |
| `expression`, no `mapping_edits` and no source field / table | 7 | a person |
| `filter`, free text or a multi-word left side | 22 | a person |
| `document_note`: `space_in_name` 4, `drag_fill` 1, `region_label_nonstandard` 1, `type_in_length_column` 1, `mixed_target` 1 | 8 | a person |
| `load_mode` null | 6 | a person |
| `rule` (free-text rules) | 4 | a person |
| `target_type`: no region lists the column, or every region states a sentinel | 3 | a person |
| `join`, alias-only tables (J3) | 2 | a person |
| `primary_key`: a non-PK `indexes` cell, a feed with no PK marker | 2 | a person |
| `source_table`: a direct move without a source table | 1 | a person |

## 4. What is proposed (107)

| Proposal | Count |
| --- | --- |
| `expression`: no `mapping_edits` cell (m2 has none), so a direct move of `source_field` is proposed | 60 |
| `join`: one column named, assumed to have the same name on both sides (J1 / J2) | 18 |
| `region_drift`: a column present in some regions only | 11 |
| `length`: derived from the type in `target_format` (m0) | 9 |
| `target_type`: the regions state two types (the most common is proposed) | 6 |
| `filter`: F4 slash notation (1), F5 with a function that is not mapped (1) | 2 |
| `nullable`: NOT NULL in some regions only | 1 |

## 5. The questions workbook

| | |
| --- | --- |
| Path | `/Volumes/d1_dlk/codegen/state/edh_e2e/questions_run_20261020T180637Z_fa5270e.xlsx` |
| Rows | **210**: one per open QUESTION, in 12 sheets (`feed_0` … `feed_11`) |
| Columns | `question_key`, `role`, `block_index`, `source_row`, `cell_text`, `question`, `answer` (empty) |
| Size | 22,767 bytes |

The workbook quotes document cells, so it lives in the state volume only. The CLI refuses
a path inside the repository, and the container has no `/Volumes` mount, so the file went
up through the Files API. A filled copy comes back with `codegen read-edh-e2e … --answers
<path>.xlsx`. An answers.yaml (`gaps: {<key>: {value: …}}`, the ingestion path's loader)
works the same way. Each answered key is recorded under `answered`, counted as filled, and
applied where it sets a value: schema, load mode, SCD2 / SK, source catalog.schema, type,
expression, key, length.

## 6. `test_m93_chooser` — re-included, and why it had failed

It runs again in the full suite, with nothing deselected: `tests/test_m93_chooser.py` 48
of 48, three times in a row on the D1 container.

- **Not on `main`:** `main` has neither the test nor `ui/backend/docindex.py`, so it
  cannot fail there.
- **When it started failing:** the test was added in 44cd970 (M9.3, 2026-09-21) and
  passes there. A bisect puts the first failure at **c0358f6** ("M9.3 addendum: the
  chooser can no longer hang the App", same day). Every later commit fails on this host.
- **Cause 1, a product bug:** `DocumentIndex._bounded` fixed the file's deadline before
  starting the parser process, so a parser restart was charged to the file. That
  contradicts the line's own comment, "its own budget, not this file's". After a timed-out
  file stops the parser, the restart takes longer than the 0.4 s budget on this
  container, so every healthy file got the 0.05 s floor and was listed `unreadable`.
  **Fixed:** the parse budget is now the timeout minus the download time.
- **Cause 2, a test artefact:** the first workspace download imports the SDK's workspace
  module (`storage.remote._format_kwarg`), which takes 1.1 s cold here. Since c0358f6
  made the startup restore a background job, that import lands on the first listing,
  inside the 1.0 s "the list does not wait" budget. **Fixed in the test:** it warms that
  import at module load, so the timing assertion measures only what it is about.
- **Still open, product side:** a real App could also pay that one-time import on its
  first listing. It is a one-off cost, not a wait on a download.
