# Bug-fix log — what exactly was done for each bug

One entry per fixed bug (a tracker incident, a tester report, a defect found in a check).
`CHANGELOG_ACFC.md` says what a VERSION did; this file says what a FIX touched, so a
regression can be traced to the fix that caused it. Newest first. Written before the
version is pushed; the "Deployed" line is updated when it reaches staging.

**No client values here** (`AGENTS.md`, client documents): no file, sheet, table, column
or vendor names from a client document, and no tracker text — name cells by IIG template
sheet / column, documents by role (the FRD, the STTM), pairs by `pair_<n>`, incidents by
number.

## The template

```
## <version> — tracker #<n>: <one line>
- Symptom:      what the user saw (template vocabulary only)
- Reproduced:   on whose documents, mock / live, which version, what came out
- Root cause:   file :: function — why the code did that
- Change:       file :: function / config key — exactly what now happens
- Reach:        12-pair check: which pairs, sheets, columns, cell counts moved; outcomes
- Side effects: anything else that moved, and whether it was fixed in the same version
- Unchanged:    what the fix deliberately does NOT do (and why)
- Tests:        test file :: test names; failed with ONLY the fix reverted (yes / how)
- Verified:     suites (both venvs), 12-pair check, dev live run, staging
- Revert:       how to undo just this fix
- Deployed:     dev <sha> <date>; staging <sha> <date> | not yet
```

---

## 0.5.8.post193 — side effect of #11: the review copy asked for a decided blank

- **Symptom:** after the #11 fix, pair_01's `<feed>_IIG_REVIEW.xlsx` summary gained one
  row - `ADLS_DELTA_INGESTION_DETAILS.MANDATORY_FIELD_LIST`, owner BSA, "no document
  states it" - although the FRD states it (no rejection). The row shifted every row below
  it, so a position compare counted 858 changed cells.
- **Found by:** the 12-pair check (classified per row before the client copies were
  deleted: 1 new row per summary, 0 removed).
- **Root cause:** `iig_review._reason` treats every blank cell as `unstated` unless its
  badge entry carries `deliberate_blank`; the #11 cell did not.
- **Change:** `metadata_template` (the ADLS row builder) sets
  `badge_entry.deliberate_blank = True` on the empty list - the marker LOB's convention
  blanks already use; the review copy no longer lists it and `metadata_inserts.sql`
  writes `NULL` for it (`emit/metadata_inserts.py`: a decided blank is NULL).
- **Reach:** re-run 12-pair check: the review-summary row gone; no other change.
- **Tests:** `tests/test_tracker_incidents_post193.py ::
  test_the_review_copy_does_not_ask_for_the_decided_blank` (+ the `deliberate_blank`
  assert in the #11 test) - both failed with only the marker line removed.
- **Lesson:** a cell left empty ON PURPOSE must say so (`deliberate_blank`), or every
  consumer that reads "empty" as "missing" (review copy, inserts, notebook OPEN_CELLS)
  turns the fix into a new open question.

## 0.5.8.post193 — tracker #11: MANDATORY_FIELD_LIST filled although the FRD says "No Rejection"

- **Symptom:** ADLS `MANDATORY_FIELD_LIST` listed every required column. The stage load
  rejects a row with any listed field null, so header / trailer rows and valid records
  with an optional blank would go to the reject table, against the FRD.
- **Reproduced:** the tester's staging pair (newest STTM + FRD), mock, post192: the list
  held all required columns.
- **Root cause:** `metadata_template` (ADLS row builder) always wrote
  `spec.not_null_columns` (the STTM's required columns). The FRD's incomplete-record row
  was read only to decide the NullCheckRule (`_stated_key_rules`), never this cell.
- **Change:** new `metadata_template.frd_states_no_rejection` (the FRD DQ row for
  `null_check` whose value STARTS with a `dq_no_rejection_words` phrase); when it fires,
  the cell is empty, badge `from_frd`, the tooltip quoting the FRD row, `deliberate_blank`
  (see the side effect above). Refactor: `frd_dq_check` now uses `_frd_dq_row` +
  `_starts_with_any` (same behaviour). Config: `MetadataTemplateConfig.
  dq_no_rejection_words` (`config.py`), set to `["No Rejection"]` in
  `config/overlays/acfc_env.yaml`.
- **Reach:** pair_01 only (3 cells: its 3 ADLS rows); outcomes unchanged; knock-ons on
  pair_01: `CODEGEN_STAGES.json` empty-cell counts +3, `iig_single_line` scanned 6 fewer
  text cells (still pass), the same cells in `config_rows.xlsx` / `metadata_inserts.sql`.
- **Unchanged:** a blank or "NA" incomplete-record row states nothing - the STTM list
  stays (a person must not read "NA" as "load as-is"); the NullCheckRule logic (post171).
- **Tests:** `test_tracker_incidents_post193.py :: test_the_incomplete_record_row_says_
  no_rejection_or_not`, `test_no_rejection_leaves_the_mandatory_list_empty_with_the_frds_
  reason`, `test_otherwise_the_mandatory_list_is_the_sttms_required_columns` (guard).
  Failed with only `metadata_template.py` reverted: yes (assertions, not imports).
- **Verified:** both suites green (2616 / 2267); 12-pair check as above; dev live run of
  the tester's pair: the cell empty in every row.
- **Revert:** delete `dq_no_rejection_words` from the ACFC overlay (the helper then never
  fires) - or revert the ADLS-builder branch.
- **Deployed:** dev 294f4b3 2026-11-16; staging not yet (a tester run was paused there).

## 0.5.8.post193 — tracker #13: DeDuplicationRule on the key although the FRD says "true duplicates"

- **Symptom:** the DeDuplicationRule listed the STTM's 4 Primary Key columns; one member
  has many valid records, so valid records were rejected as duplicates.
- **Reproduced:** the tester's pair, mock, post192: SOURCE_COLUMN = the key.
- **Root cause:** `metadata_template._stated_key_rules` (dedup) used `_primary_key`
  whenever the FRD stated ANY duplicate check (post171) - what kind of duplicate the FRD
  meant was not read.
- **Change:** new `metadata_template.frd_states_true_duplicates` (the stated value names
  a `dq_true_duplicate_words` phrase, on word boundaries); when it fires the rule lists
  every data column of the detail table (`fields` - audit columns are not fields), the
  tooltip quoting the FRD's first line. Config: `MetadataTemplateConfig.
  dq_true_duplicate_words`, `["True Duplicate"]` in the ACFC overlay.
- **Reach:** pair_03 only (SOURCE_COLUMN + TARGET_COLUMN of its one DeDup row); outcomes
  unchanged.
- **Unchanged:** a plain duplicate check keeps the STTM key; no key + a stated check still
  writes an open, flagged cell; INPUT_PARAM (the target FQN) as before.
- **Tests:** `test_true_duplicates_are_read_on_word_boundaries`,
  `test_a_true_duplicate_check_lists_every_data_column`,
  `test_a_plain_duplicate_check_still_keys_on_the_sttm_primary_key` (guard). Failed with
  only `metadata_template.py` reverted: yes.
- **Verified:** suites, 12-pair check, dev live run: 70 data columns (74 minus 4 audit).
- **Revert:** delete `dq_true_duplicate_words` from the ACFC overlay.
- **Deployed:** dev 294f4b3 2026-11-16; staging not yet.

## 0.5.8.post193 — tracker #12: SRC_DATA_TYPE with precision split wrongly by the standard load

- **Symptom:** STGDELTA `SRC_DATA_TYPE` held `String:Decimal(12,2)`; the standard load
  splits the list on commas, so the list had more pieces than columns and every type after
  a decimal was misaligned.
- **Reproduced:** the tester's pair, mock, post192: 80 comma pieces for 74 columns.
- **Root cause:** config, not code: the ACFC overlay set `data_type_style: full`
  (post43, from one SD prod row); `metadata_template._stg_std_row` writes full types then.
- **Change:** `config/overlays/acfc_env.yaml` `data_type_style: base` (`String:Decimal`,
  the pair-1 golden's form - the shipped `config.yaml` value). No code change.
- **Reach:** pair_01 + pair_02 (4 SRC_DATA_TYPE cells); outcomes unchanged.
- **Unchanged:** `TGT_DATA_TYPE` keeps the precision (the pair-1 golden keeps
  `Decimal(17,2)` there) - the tester asks to drop it too: OPEN, asked; the DDL keeps the
  STTM's type (gate `decimal_precision` unchanged); no DataTypeCastRule (#14, post171).
- **Tests:** `test_the_acfc_overlay_writes_base_source_types`,
  `test_src_data_type_has_one_comma_piece_per_column`; updated
  `test_iig_cheap_misses.py :: test_stgdelta_containers_and_base_source_data_types` (was
  `..._full_data_types`, which pinned post43). All failed with only the overlay value set
  back to `full`: yes.
- **Verified:** suites, 12-pair check, dev live run: 74 pieces for 74 columns.
- **Revert:** `data_type_style: full` in the ACFC overlay (and the test rename back).
- **Deployed:** dev 294f4b3 2026-11-16; staging not yet.

## Not fixed in post193 (decisions open) — for the record

- **#9 / #10** fixed-width `SRC_FORMAT = CSV` + `SRC_FILE_DELIMITER = '|'`: framework
  conventions only the tester states; waiting on confirmation for every fixed-width feed.
  (Reproduced: the fixed-width handler rows ARE generated; SRC_FORMAT is blank, not TXT.)
- **#14** DataTypeCastRule: reverses post171 ("no cast rule"); the pair-1 golden has one.
- **#16** no grand master for a Workflow run: changes the post166 flow.
- **#17** `WF_` names: no code - already the "Databricks Workflow (WF_)" run option
  (post187).
