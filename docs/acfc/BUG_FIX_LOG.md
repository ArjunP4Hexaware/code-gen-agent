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

## 0.5.8.post214 — first tester: the MandatoryColumnCheckRule as a standard DQ rule (a feature)

- **Symptom:** no DATA_QUALITY_RULES row checked the STTM's required fields the way the
  client framework does (MandatoryColumnCheckRule with the FRD's error code); the agent
  wrote the list into ADLS MANDATORY_FIELD_LIST instead, which the tester keeps blank.
- **Reproduced:** her staging uploads (pairs A / B / C, /tmp only, mock, post213): no such
  row; each of her FRDs has an error table (inside a requirement cell) with one
  "mandatory field missing" row and a numeric code; none of the 12 pairs has one.
- **Root cause:** not a defect - the rule class was not in `dq_rule_classes`, and post171
  writes DQ rows only where a document states the rule. Soham (2026-11-19 / 20): a
  standard rule; blank the list when the row is written; no error table = the row with
  INPUT_PARAM open, non-blocking.
- **Change:** `extract/frd_docx.py :: mandatory_error_codes` (+ `read_frd`) with
  `extractor.frd.error_code_headers / error_description_headers /
  mandatory_error_descriptions` (config.yaml) -> `FrdFeed.mandatory_error_code / _source`
  -> `ResolvedFeedSpec.frd_mandatory_error_*` (`resolve/resolver.py`) ->
  `metadata_sheet._feed_from_spec` (the run path rebuilds the FRD feed from the spec -
  the first harness run left INPUT_PARAM open until this). `metadata_template.py ::
  _mandatory_columns / mandatory_rule_written / _mandatory_error_cell / _std_dq_rules`:
  the `std_mandatory_check` kind (ACFC overlay `dq_rules`, class, type STDDelta,
  citation), one row per standard table holding a required field; the ADLS
  MANDATORY_FIELD_LIST cell a `deliberate_blank` then; `dq_not_generated_flags` drops
  the NullCheckRule "required columns" suggestion then. `emit/notebook_v2.RULES`: the
  class runs as the null check. Why a new reader (READER_GENERALIZATION): the error
  table is a header-keyed table no existing reader covers; its headers and row words are
  config lists, no field-specific code path.
- **Reach:** 12-pair check (post213 da6783a vs post214 81ed4f0, mock, framework): outcomes
  unchanged (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2 GATE_FAIL, 2 FAIL), 295 / 295
  files. REAL in pairs 01 02 03 04 05 06 09 11 12: DATA_QUALITY_RULES 140 cells per IIG /
  review copy (the new rows), ADLS_DELTA MANDATORY_FIELD_LIST 17 cells blanked, 9 feeds
  with `iig_dq_open:` (INPUT_PARAM open - no 12-pair FRD states an error table) and a new
  `iig_blank:DATA_QUALITY_RULES` line (the sheet's usual blanks + INPUT_PARAM; those feeds
  had no DQ row before), 5 LOG lines of the NullCheckRule suggestion gone, the review
  summary / provenance sheets accordingly. The contracts' one changed line = the cached
  old side's run date (2026-11-19). Tester pairs: A and C get the row with the FRD's code
  (37 / 32 columns) and the list blank; B stays held at layout under mock (as before).
- **Side effects:** a feed with required fields but no error table is PASS_WITH_FLAGS
  with one more flag; no verdict / outcome moved.
- **Unchanged:** NullCheckRule / DeDuplicationRule (post171 / post193); the FRD's "No
  Rejection" row (no rule row, post193's reason on the list); an overlay without
  `std_mandatory_check` keeps the list (pinned); the notebook does not write the error
  code (the client framework's own).
- **Tests:** `tests/test_mandatory_rule_post214.py` (17);
  `test_tracker_incidents_post193.py` (the list test pins both cases);
  `test_iig_corpus_cells.py::test_dq_key_rules_only_where_a_document_states_them` (the
  row, no suggestion). `test_a_run_rebuilds_the_feed_from_the_spec_with_the_code` failed
  with only `metadata_sheet.py` reverted; the rest are new behaviour.
- **Verified:** both suites on the pushed tree; the 12-pair check above.
- **Revert:** drop `std_mandatory_check` from the ACFC overlay's `dq_rules` (the row and the
  blank list go; the reader stays inert), or revert the post214 commits.
- **Deployed:** not yet.

## 0.5.8.post213 — second tester: a standard type cell reading a note CRASHED the run

- **Symptom:** the live run on staging ended CRASHED (`TemplateGapError: no SQL type
  mapping for contract datatype`).
- **Reproduced:** her staging uploads (pair C, /tmp only), mock, post212: CRASHED with
  scratch answers; one standard band type cell reads a note.
- **Root cause:** `extract/generic.py` carried any standard type text into the contract;
  `emit/context.sql_type` (post158's guard) then raised - by design for the DDL, but no
  earlier step asked.
- **Change:** `generic._is_data_type` (the same `sql_type` mapping) + a blocking QUESTION
  `feeds[i].columns[j].standard_type` (the row left out until answered; a non-type answer
  keeps it open); `ui/backend/demo.pending_question` (plain title + the reason as hint).
  Why a pass: none - the post74 blank-stage-type question applied to the standard cell.
- **Reach:** 12-pair check (post212 vs post213, framework, mock): outcomes unchanged, no
  REAL change on any pair (after the "BIG INT" fix below); pair C: CRASHED ->
  NEEDS_ANSWERS (one question); answered "String" -> PASS_WITH_OPEN_INPUTS; answered
  "Derived too" -> still asked.
- **Side effects:** the first 12-pair run caught one: pair_09's 8 "BIG INT" cells (a real
  type spelled with a space) were asked - `_is_data_type` now also tries the spelling
  without spaces (no question; pair_09 as before). Known, not new: such a cell still
  stops the run at `sql_type` if a feed reaches the notebook render (pair_09 does not).
- **Unchanged:** post158's guard and tests; every cell `sql_type` reads; the stage type
  question (post74 / post95 wording).
- **Tests:** `tests/test_standard_type_question_post213.py` (5; 4 failed with HEAD's
  `generic.py` + `demo.py`).
- **Verified:** `.venv-d1` 2367 passed; `.venv` 2719 passed + 1 failed
  (`test_demo_ui.py::test_choosing_an_sttm_auto_pairs_its_frd` - passes alone 3/3 and as
  a file 33/33: a load flake, not in this change) - RE-RUN `.venv` before the push.
- **Revert:** drop the `standard_type` block in `generic._build_feed` (the crash returns).
- **Deployed:** dev not yet (STOPPED); staging not yet.

## 0.5.8.post212 — tracker #5: SRC_FILE_NAME not the FRD's file pattern

- **Symptom:** the FRD states `*_<A>_*_<B>*`; ADLS SRC_FILE_NAME was `<A>_<B>*` - it no
  longer matches the real file names (they start with a number).
- **Reproduced:** pair_13 (the Accumulators pair), mock, post211.
- **Root cause:** `metadata_template._src_file_name_cell` applied the family convention
  (`prefix_star`, learned from production IIGs) to every pattern, the FRD's own glob too.
- **Change:** an FRD-stated pattern holding a wildcard (`_STATED_GLOB_RE`) is written as
  stated, unless a feed override or the data engineer's style choice says otherwise.
- **Reach:** 12-pair check (post211 vs post212, framework, mock): outcomes unchanged; ADLS
  SRC_FILE_NAME on pair_04 (1 cell: the FRD's leading-wildcard glob) and pair_12 (18
  cells: the FRD's glob instead of the prefix_star form - pair_12's production IIG uses
  that form, so its golden score on this column drops by design); pair_13 = the FRD's
  pattern.
- **Side effects:** none found (10 DDL test pins updated for the new statements).
- **Verified:** `.venv` 2715 passed; `.venv-d1` 2363 passed; ruff clean; 12-pair check
  alone + pair_13.
- **Deployed:** dev not yet (STOPPED); staging 049c6e8 2026-11-19.
- **Unchanged:** derived patterns (a sample name with date tokens) keep the convention;
  STTM-sourced patterns keep it.
- **Tests:** `test_tracker_fixes_post212.py` #5 block (3; 1 failed reverted, 2 pin the rest).
- **Revert:** remove the `elif` branch in `_src_file_name_cell`.

## 0.5.8.post212 — tracker #7 / #20: archive paths were template shapes, not the FRD's

- **Symptom:** ADLS SRC_ADLS_ARCHVL_PATH `.../Archive/` (the FRD: `.../archive/`), the
  fixed-width handler's `/Archive/<container>/...` (#20).
- **Reproduced:** pair_13, mock, post211: the FRD's three "Archive Path:" lines (main /
  daily / monthly) unread.
- **Root cause:** no reader for "Archive Path" (post208 read only requirement "Archive
  Location" lines) and option C (template kept) - reversed by Soham: "FRD path wins, use
  the main one".
- **Change:** `extractor.frd.archive_line_labels`, `frd_docx._archive` (first path,
  `frd_archive_main:` flag), `_labelled_paths`; `resolve/stated.environment_address` (the
  archive's account / container like the landing's); `metadata_template._paths` +
  `_stated_archive_tail` + `stated_archive_tabs` (config).
- **Reach:** 12-pair check: SRC_ADLS_ARCHVL_PATH on pair_01 (3 ADLS + 3 FIXED_WIDTH
  cells: the FRD's stated archive); pair_13 = `.../archive/` on both sheets (the tester's
  expected value); FRD contracts gain `archive_location` where stated.
- **Side effects:** none found (10 DDL test pins updated for the new statements).
- **Verified:** `.venv` 2715 passed; `.venv-d1` 2363 passed; ruff clean; 12-pair check
  alone + pair_13.
- **Deployed:** dev not yet (STOPPED); staging 049c6e8 2026-11-19.
- **Unchanged:** STGDELTA's archive (the stage-to-standard step's, not the raw file's)
  keeps its shape + the post208 note; an archive outside the landing's folder keeps the
  shape + the note.
- **Tests:** #7 / #20 block (5).
- **Revert:** `archive_line_labels: []` and `stated_archive_tabs: []`.

## 0.5.8.post212 — tracker #18: no standard reject table in the DDL

- **Symptom:** the STGDELTA row names TGT_RJT_TABLE_NAME `<stage table>_reject` under the
  standard catalog / schema; the DDL creates no such table.
- **Reproduced:** pair_13, mock, post211 (2 CREATEs: stage, standard).
- **Root cause:** never built.
- **Change:** `ConventionsProfileConfig.standard_reject_table` (`StandardRejectTableConfig`;
  on in `acfc_prx`, null in the pair-1 overlay); `emit/framework._standard_reject_blocks`;
  the `ddl_parses` allow-list (`_defined_table_names` + the reject names - computed, the
  post158 guard stays closed); `run_artefacts` merge banners. Columns: every standard
  column (audit included) as String + REJECT_REASON / SRC_TABLE_NAME / RUNID (the tester's
  instruction, cited).
- **Reach:** 12-pair check: every ACFC DDL (and the combined sets, the DDL test cases)
  gains one reject table per standard table; outcomes unchanged; pair_13 = the table the
  tester named.
- **Side effects:** none found (10 DDL test pins updated for the new statements).
- **Verified:** `.venv` 2715 passed; `.venv-d1` 2363 passed; ruff clean; 12-pair check
  alone + pair_13.
- **Deployed:** dev not yet (STOPPED); staging 049c6e8 2026-11-19.
- **Unchanged:** no stage reject table (not asked); the IIG.
- **Tests:** #18 block (3); `test_ddl_runsafe` / `test_ddl_parse_gate` /
  `test_ddl_comments` / `test_table_comment` pins updated (statement counts).
- **Revert:** `standard_reject_table: null` in the ACFC profile.

## 0.5.8.post212 — tracker #19: the table COMMENT was the load strategy

- **Symptom:** every table's COMMENT read "Load strategy: ..." - no business description.
- **Reproduced:** pair_13, mock, post211 (the STTM states no Table Description).
- **Root cause:** `emit/framework._table_comment` had only the STTM's Table Description;
  the FRD's Description row was placed (`description#descriptive`) but never carried.
- **Change:** `FrdFeed.description`, `ResolvedFeedSpec.frd_description`, the resolver;
  `_table_comment` uses it when the STTM states none.
- **Reach:** 12-pair check: the table COMMENTs of the F1 pairs open with the FRD's
  Description; FRD contracts gain `description`; pair_13 = its Descriptive Description.
- **Side effects:** none found (10 DDL test pins updated for the new statements).
- **Verified:** `.venv` 2715 passed; `.venv-d1` 2363 passed; ruff clean; 12-pair check
  alone + pair_13.
- **Deployed:** dev not yet (STOPPED); staging 049c6e8 2026-11-19.
- **Unchanged:** the STTM's Table Description wins; post140's "description + load
  strategy" join; F2 FRDs (no Descriptive section) still the load strategy alone.
- **Tests:** #19 block (3).
- **Revert:** drop the `or getattr(spec, "frd_description", None)` in `_table_comment`.

## 0.5.8.post211 — Soham 2026-11-19: the App and its files named the BSA as the agent's user

- **Symptom:** the App's output option ("DDL + BSA-annotated IIG"), the review copy's
  Owner column (BSA / Engineer), its notes ("left blank: the BSA chose ..."), the DQ
  suggestions ("if the BSA confirms one"), the report and LOG.md ("BSA review ... the BSA
  certifies") named the BSA; the agent's user is the data engineer.
- **Reproduced:** n/a (wording).
- **Root cause:** the M3-era wording (2026-10) assumed the BSA reviews the IIG.
- **Change:** text only, ~40 strings across src / ui / config (`the BSA` -> `the data
  engineer`); `config :: iig_review.owner_labels` + `review_flag_owner` (and the model's
  defaults in `config.py`). Keys (`bsa` / `engineer` / `engineer_confirms`), colours and
  every cell's group unchanged.
- **Reach:** 12-pair check (framework, mock, post210 vs post211): outcomes unchanged,
  295 / 295 files; changed: the review copies only (REVIEW_SUMMARY owner values, the cells'
  "Owner:" comments on every sheet), the combined LOG.md (6) and the reports (13) -
  wording; no clean IIG, DDL or test-case file moved.
- **Side effects:** none; the first full suite run caught a 10th label pin
  (`test_multi_table_step4`), updated.
- **Unchanged:** cell values, groups, counts; the 2026-10-14 framework-owner rule's
  comments (history).
- **Tests:** 10 updated (path whitespace flag, pipeline-name choice, review inventory x2,
  file tie-break, scorecard, framework report, 2 vitest); no new behaviour to pin.
- **Verified:** `.venv` 2701 passed; `.venv-d1` 2349 passed (on the pushed tree); vitest
  286; tsc + ruff clean; 12-pair check alone.
- **Revert:** the owner labels are config (`iig_review.owner_labels`); `git revert` the
  wording.
- **Deployed:** dev not yet (STOPPED); staging 602b360 2026-11-19.

## 0.5.8.post210 — second tester 2026-11-19: unreadable FRD questions; a feed-name dead end

- **Symptom:** the layout dialog asked 6 questions, each listing the same 16 FRD cells
  (labels such as Name / IS Owner / requirement lines) - none stating any of them; the
  feed name asked with no way to answer it; after "proceed" the live run CRASHED
  (`TemplateGapError: no SQL type mapping`), its feed named after the Data Quality section.
- **Reproduced:** her staging uploads (pair C, /tmp only), mock, post209: 5 questions x
  16 candidates; with answers the run CRASHED on one standard-band type cell that is no
  type. The live naming: staging's status (`data_quality_rules`), the model path.
- **Root cause:** (a) `layout/resolve.py :: _frd_questions` gave every unresolved FRD field
  the whole candidate list (every unused labelled row + every labelled line), never
  checked against the field; (b) post208 made an unplaced feed name an FRD question with
  no text box (`answerable_frd_field` is false for it); (c) `_model_label_reason` accepts
  a "Name" row in any section for the feed name (post208 covered the synonyms only);
  (d) the CRASH: `emit/context.py :: sql_type` stops on a standard-band type cell that is
  no type ("Derived") - post158's deliberate guard (pentest CS-1), NOT changed here (a
  first version wrote it as stated; `test_ddl_types_gate` failed - withdrawn). Next: ask
  for that cell's type, like a blank stage type.
- **Change:** `_frd_questions` (skip `feeds[i].feed_name`), `_plausible_candidates`,
  `_value_reads_as`, `_candidate_value` (new); `_model_label_reason` (the section rule);
  `metadata_template.frequency_token` (public, the frequency's reader);
  `layout/answers.py` (a typed feed-name answer still refused with its reason);
  `LayoutQuestions.tsx :: typedOnly`. No reader pass, no new vocabulary: the field readers that exist.
- **Reach:** 12-pair check (framework, mock, post209 vs post210): outcomes unchanged,
  295 / 295 files, no artefact moved; 3 reports (pairs 08 / 09 / 10) lose candidate lines
  of their open questions (removals only). Questions on the tester pairs (mock): pair C 5 x 16
  -> 4 (LOBs 0, domain 0, the strategies 4 each); pair A 4 (LOBs 0, strategies 2 each);
  pair B 2 questions with no cell list.
- **Side effects:** the first suite run caught 5: the feed-name answer's refusal note
  (restored), post158's type guard (the context change withdrawn), and post192's
  frequency lines (a frequency reader added; its dialog test now pins the filter).
- **Unchanged:** STTM / VDD column questions; FRD fields a person may not type (every
  cell, as before); the never-guess rule (no value is filled); a model proposal stays a
  pre-selection.
- **Tests:** `tests/test_frd_questions_post210.py` (7; 4 failed with HEAD's resolve.py
  before the model-claim case was added), `LayoutQuestions.test.tsx` post210 block (1 of 2
  failed with HEAD's component - the other pins the unchanged case); Playwright on a local
  mock App (her question shapes: 3 radios, no console error).
- **Verified:** `.venv` 2701 passed; `.venv-d1` 2349 passed (second run, after the 5
  fixes); vitest 286; tsc + ruff clean; 12-pair check alone.
- **Revert:** `git revert` the version; `_plausible_candidates` returning `candidates`
  restores the old lists.
- **Deployed:** dev not yet (STOPPED); staging 13d098e 2026-11-19.

## 0.5.8.post209 — tester report 2026-11-19 (2): the STTM's File Details tab unread

- **Symptom:** file format and delimiter asked though her STTM's "File Details" tab
  states them ("File Type", "File Delimitor" rows).
- **Reproduced:** her staging uploads, mock, post208, /tmp only: the tab's layout kind
  `ignore`; both values asked.
- **Root cause:** `layout/resolve.py :: _sttm_facts` read meta facts from mapping sheets'
  meta rows and tabular `file_details` sheets only; a label | value sheet is neither.
- **Change:** `layout/resolve.py :: _detail_sheet_meta` (new); `config ::
  extractor.discovery.meta_synonyms.delimiter` + "file delimitor". Why a pass
  (READER_GENERALIZATION): the meta-row grammar applied on its own sheet - the same
  labels, no new vocabulary beyond one spelling seen in a client STTM.
- **Reach:** 12-pair check (framework, mock, post208 vs post209): outcomes unchanged,
  295 / 295 files, no REAL change on any pair (build stamps only). On her pair A: file
  format + delimiter filled from the tab (cited), no longer asked.
- **Side effects:** none found.
- **Unchanged:** a mapping sheet's meta rows (they win); tabular file_details sheets; the
  other labels of such a tab (delivery method, naming convention) - not read.
- **Tests:** `tests/test_detail_sheet_meta_post209.py` (6; 3 failed with HEAD's
  `resolve.py` + config).
- **Verified:** `.venv` 2694 passed; `.venv-d1` 2342 passed; ruff clean; 12-pair check
  alone.
- **Revert:** `git revert` the version (or `_detail_sheet_meta` returning at once).
- **Deployed:** dev not yet (STOPPED); staging c2a3019 2026-11-19.

## 0.5.8.post208 — tester report 2026-11-19: the feed named after a Data Quality section; the stated archive path unread

- **Symptom:** her first pair's only feed was named "Data Quality rules" (the run's
  held-back list, the IIG / DDL names); the FRD's "Archive Location" was never read.
- **Reproduced:** her staging uploads, mock, post207, /tmp only: the FRD profile's
  `feeds[0].feed_name#fallback` = the Data Quality section table's Name row.
- **Root cause:** `frd_docx._discover_f1` took the FIRST F1 section's "Name" row as the
  feed name's fallback - in an FRD without a Descriptive Metadata table that was the
  Data Quality section's own title. The archive: no reader existed
  (`SRC_ADLS_ARCHVL_PATH` is the `path_patterns` template of the landing).
- **Change:** `config :: extractor.frd.feed_name_sections` (new, [descriptive]) checked in
  `_discover_f1` (a note instead of the fallback); `config :: requirement_archive_labels`
  (new); `frd_docx._labelled_path` (a bracketed note after the label = no value;
  `spaced_ok` for a compared path), `requirement_landings(labels, spaced_ok)`,
  `_requirement_path_blocks` (the post84 landing blocks, for the landing and the
  archive); `contracts.frd.FrdFeed.archive_location`,
  `contracts.resolved.ResolvedFeedSpec.archive_location` (new, default None - absent
  from the JSON), `resolver` + `metadata_sheet._feed_from_spec` carry it,
  `layout.resolve.resolve_structured_fields` binds it per feed like the landing;
  `metadata_template._note_stated_archive` (the review note). Why passes: the feed-name
  one is a config gate on an existing rule; the archive reuses the landing reader.
- **Reach:** 12-pair check (framework, mock, post207 vs post208): outcomes unchanged,
  295 / 295 files, no REAL change on any pair (build stamps only) - no pair has a Name
  row outside a descriptive section as its feed's name, nor an Archive Location line.
  On her pair A: the feed named after the STTM stage band; the stated archive agrees
  with both sheets' shapes (no note).
- **Side effects:** a test stub feed without the new attribute (getattr default).
- **Unchanged:** the archive cell's value (always the template shape - option C); a
  Descriptive section's Name row; the vendor-name fallback for the source system.
- **Tests:** `tests/test_feed_name_archive_post208.py` (10; with HEAD's `frd_docx.py` +
  config.yaml 4 failed, with the note a no-op 1 failed).
- **Verified:** `.venv` 2688 passed; `.venv-d1` 2336 passed; ruff clean; 12-pair check
  alone.
- **Revert:** `feed_name_sections` listing every section restores the old fallback;
  `requirement_archive_labels: []` stops the archive reading; or `git revert`.
- **Deployed:** dev not yet (STOPPED); staging 237caa3 2026-11-19.

## 0.5.8.post207 — tester report 2026-11-19 (3, 1): "Landing Location" unread; "Domain -" cell unread

- **Symptom:** ADLS / STGDELTA `SRC_ADLS_PATH` and `SRC_ADLS_ARCHVL_PATH` blank on both
  her pairs; the domain asked though the FRD states it.
- **Reproduced:** her staging uploads, mock, post206, /tmp only: both pairs' FRD
  contracts had no landing (5 feeds), pair A no domain / sub domain.
- **Root cause:** (a) `extractor.frd.requirement_landing_labels` knew only "Raw ADLS
  Location" / "ADLS Location"; (b) `frd_docx._labelled_path` returned a cell's FIRST
  labelled path - with a label per environment block, a QA path that differs would be
  ignored silently; (c) `frd_docx._DOMAIN_LABEL_RE` took only ':' / '=' after the label,
  and the domain was read only from a row of its own (her cell sits in a row with no
  label cell, column 0).
- **Change:** `config/config.yaml :: extractor.frd.requirement_landing_labels` +
  "Landing Location"; `frd_docx._labelled_path` (every labelled path of the cell; one
  path, spaces ignored -> the first as written; several -> None);
  `frd_docx._DOMAIN_LABEL_RE` (+ '-', en dash); `frd_docx._place_domain_cell` (new,
  called from `discover_frd`). Why a pass (READER_GENERALIZATION): the domain is read by
  its own two-label grammar, not as a post192 `<label>: <value>` line field, so post192's
  "the ONE cell in any table" rule is applied with that grammar - no new grammar.
- **Reach:** 12-pair check (framework, mock, post206 vs post207): outcomes unchanged
  (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2 GATE_FAIL, 2 FAIL), 295 / 295 files, no
  artefact moved - only the report's version / environment-path line (13, sha-only kind)
  and the build stamps. On her pairs (mock, /tmp): landing read for 5 / 5 feeds (2 once
  their file question is answered), pair A's domain + sub domain as written.
- **Side effects:** none found.
- **Unchanged:** a stated "Archive Location" is not read (the archive path is still the
  `path_patterns` template - option C, a flag when they differ, is next); a multi-feed
  FRD's domain; a domain row of its own wins over any other cell.
- **Tests:** `tests/test_landing_domain_post207.py` (11; 8 failed with HEAD's
  `frd_docx.py` + config, the "different paths" one with HEAD's `frd_docx.py` alone).
- **Verified:** `.venv` 2678 passed; `.venv-d1` 2326 passed; ruff clean; 12-pair check
  alone.
- **Revert:** drop "Landing Location" from the config list; `git revert` the version for
  the reader changes.
- **Deployed:** dev not yet (STOPPED); staging bb5ce4a 2026-11-19.

## 0.5.8.post206 — tester report 2026-11-19 (1): an FRD field no cell states could not be answered in the App

- **Symptom:** every feed held back at the first step; the questions for the file
  format and the LOBs offered only FRD table cells that do not state them + "None of
  these"; "Proceed with unresolved" held the feed and asked the same questions again.
- **Reproduced:** the tester's uploads (staging), mock, post205, /tmp only: layout
  questions for file format / LOBs / domain / load strategies (FRD role questions);
  with an answers file typing the LOBs and leaving the file format blank, both questions
  were gone - the backend applied them, only the App had no way to give them.
- **Root cause:** `ui/frontend :: LayoutQuestions.tsx :: QuestionItem` renders a text box
  (and post170's blank choice) only for `kind: text`; an FRD role question
  (`kind: role`) got radios over its candidate cells + "None of these". The backend
  (`layout.answers`, Chunk B) applies a `gaps:` value for an answerable FRD field, but
  nothing marked which fields those are for the page.
- **Change:** `ui/backend/demo.py :: typed_frd_question` (new; used where the layout
  dialog's questions, the owed questions after "proceed" and the held-back feeds'
  questions are built) adds `typed`, `example`, `leave_blank` to an FRD role question
  of an answerable field; `LayoutQuestions.tsx :: TypedFrdValue` + `hasPick` /
  `pickCandidate` (a typed value counts as an answer; it and a cell pick exclude each
  other). Why no reader pass: none - a UI gap, not a document shape (the shapes behind
  this run - the STTM File Details sheet, "Domain -" lines - are separate items).
- **Reach:** no generated file can move: the run's inputs are the same answers the
  backend already took; `src/` unchanged; the CLI unchanged. No 12-pair check (UI and
  App status only); the App status gains three keys on those questions.
- **Side effects:** none found. Seen in the browser check, not caused by this: at
  390 px the Settings card's connection-ID table scrolls sideways (438 px).
- **Unchanged:** the feed's name (an answer cannot rename a feed - no text box); STTM /
  VDD column questions; LOBs and domain cannot be left blank (`answers.blankable_fields`
  is still file format / delimiter / frequency).
- **Tests:** `tests/test_typed_frd_answer_post206.py` (3; 2 failed with the helper
  returning the question unchanged); `LayoutQuestions.test.tsx` "post206" block (5; 4
  failed with HEAD's LayoutQuestions.tsx); Playwright on a local mock App (stubbed
  status: typed + blank choices, "Re-run with 2 answers", no console error).
- **Verified:** `.venv` 2667 passed; `.venv-d1` 2315 passed (the App tests skip there:
  no fastapi); vitest 284 passed; tsc + ruff clean; staging not yet.
- **Revert:** `typed_frd_question` returning its question unchanged hides the controls;
  or `git revert` the version.
- **Deployed:** dev not yet (STOPPED); staging 741a62f 2026-11-19.

## 0.5.8.post205 — generic: one "states nothing" word list (three placeholder lists had drifted)

- **Symptom (class):** the same placeholder read as blank in one place and as a value in
  another: "Null" blank in a Segment cell, a VALUE in an FRD cell or an STTM meta row;
  "Not applicable" a value everywhere but the DQ section.
- **Reproduced:** the new test (an FRD cell "Not applicable" / "Null", an STTM meta value
  "Null" / "Not applicable") - read as values before.
- **Root cause:** three hand-kept config lists (`extractor.frd.blank_values`,
  `discovery.meta_blank_values`, `discovery.unsegmented_markers`), each grown by its own
  fix (M9.0, D1 post51 ...).
- **Change:** `config/config.yaml :: extractor.blank_words` (new);
  `config.py :: ExtractorConfig._merge_blank_words` (a before-validator: base words
  appended to each list unless present). Readers unchanged. Why no new reader pass: one
  config list, the READER_GENERALIZATION shape-5 normaliser.
- **Reach:** 12-pair check (framework, mock, post204 vs post205): outcomes unchanged,
  295 / 295 files, nothing moved but the version / environment-path report line - no
  pair writes "Null" / "Not applicable" (or "TBD" in a Segment cell) where it is read.
- **Side effects:** none found.
- **Unchanged:** `dq_no_check_words` (starts-with matching), `unmapped_markers` (drop a
  field), `no_values` (yes / no); each reader's own comparison (a delimiter character
  is still a value - `is_blank_placeholder`).
- **Tests:** `tests/test_blank_words_post205.py` (10; 5 failed before the change).
- **Verified:** `.venv` 2664 passed; `.venv-d1` 2315 passed; ruff clean; 12-pair check
  alone.
- **Revert:** delete `extractor.blank_words` (the validator then does nothing), or `git revert`.
- **Deployed:** dev not yet (STOPPED); staging e2b967b 2026-11-18.

## 0.5.8.post204 — generic: one delimiter reader and one format / extension table (the same delimiter read differently by reader)

- **Symptom (class):** a delimiter read differently by which reader met it: '|' vs
  'Pipe (|)' counted as a disagreement between documents (a needless question); "Comma or
  pipe" read as a comma (silent pick); "Fixed width, 120 bytes" read as a comma; a "TSV"
  format implied tab on the gap-fill path, nothing on the resolver's.
- **Reproduced:** every reader over 20 spellings side by side (the table in the session;
  the new test's cases): old `same_value('|', 'Pipe (|)')` False, old
  `delimiter_char('Comma or pipe')` ','.
- **Root cause:** two readers with different rules (`resolve/resolver.py ::
  delimiter_char`, `resolve/gapfill.py :: _delimiter_of`) and three code tables
  (`resolver._FORMAT_DELIMITERS`, `gapfill._FORMAT_NAME_DELIMITERS`,
  `extractor._EXTENSION_DELIMITERS`) with different entries.
- **Change:** `resolve/gapfill.py :: delimiter_reading` (new, the one reader;
  `delimiter_char` / `_delimiter_of` delegate); `config.py :: ExtractorConfig.
  format_delimiters` + `config/config.yaml :: extractor.format_delimiters` (new, the one
  table); `format_delimiter(text, words, formats)`, `extractor._extension_delimiter(name,
  formats)`, `extractor._resolve_delimiter(feed, name, formats)` take it; callers in
  `resolve/resolver._resolve_delimiter`, `extract/generic.py`, `extract/segmented.py`,
  `layout/resolve.py` (format gap fill) pass `config.extractor.format_delimiters`; the
  three code tables removed.
- **Reach:** 12-pair check (framework, mock, post203 vs post204): outcomes unchanged,
  295 / 295 files, NOTHING moved but the build stamp - no pair's delimiter, format or
  agreement check reads differently (none states a two-delimiter or sentence-comma value,
  a "TSV" format, or a '|' vs 'Pipe (|)' pair).
- **Side effects:** none found.
- **Unchanged:** `delimiter_in_format` (format cells: "<word> delimited" phrases only);
  `segmented._metadata_delimiter`'s "delimit" guard; `delimiter_words`; every artefact
  writes the character, never the word; `same_value` for non-delimiter values.
- **Tests:** `tests/test_delimiter_reading_post204.py` (23 readings, 4 agreement pairs,
  a disagreement, the config table, the no-code-table guard; the old readers give ','
  for the two pick cases and False for 3 of the 4 agreements);
  `tests/test_frd_multi_object.py`, `tests/test_format_from_extension.py` pass the table.
- **Verified:** `.venv` 2654 passed; `.venv-d1` 2305 passed; ruff clean; 12-pair check
  alone.
- **Revert:** `git revert` (code + config move together).
- **Deployed:** dev not yet (STOPPED); staging b933626 2026-11-18.

## 0.5.8.post203 — RESTART item 2(b): the live layout model's invalid `source` value failed its answer

- **Symptom:** a live STTM layout answer reported "model response failed schema
  validation" (4 of 4 sheets kept by the salvage); the cause was the answer's top-level
  `source` value, which the code overwrites anyway.
- **Reproduced:** synthetic: the pair-1 profile (STTM) and a stub FRD answer, each with a
  bogus `source` / `role_sources` / `field_sources` - STTM: 3 schema errors + the salvage
  line; FRD: the whole answer discarded (no salvage on that path).
- **Root cause:** `layout/resolve.py :: salvage_layout_answer` and the FRD model step
  validate the model's JSON as a whole profile, including fields only the code sets
  (`source` - a 4-value Literal - and the per-role / per-field source maps).
- **Change:** `layout/resolve.py :: _code_owned` (new) - `source` set to "model",
  `role_sources` / `field_sources` dropped, before both validations. Why no prompt change:
  the code owns these fields; a prompt asking the model not to write them would still
  fail on the next slip.
- **Reach:** 12-pair check (framework, mock, post202 vs post203): outcomes unchanged,
  295 / 295 files, nothing moved but the version / environment-path report line (a mock
  run makes no model call - the change acts only on a live layout answer).
- **Side effects:** none found.
- **Unchanged:** every claim's validation (schema, workbook, the FRD label / section /
  bound-row rules); the `confidence` field (still validated - an existing test pins its
  schema error); the salvage path for real errors; the prompt.
- **Tests:** `tests/test_layout_code_owned_fields.py ::
  test_an_sttm_answers_own_source_value_is_no_schema_error`,
  `test_an_frd_answers_own_source_value_does_not_discard_it` (both failed with the change
  stashed).
- **Verified:** `.venv` 2623 passed; `.venv-d1` 2274 passed (committed tree); ruff
  clean; 12-pair check alone.
- **Revert:** make `_code_owned` return `answer` unchanged, or `git revert`.
- **Deployed:** dev not yet (STOPPED); staging b933626 2026-11-18.

## 0.5.8.post202 — RESTART item 2(a): two FRD line choices read the same in the unresolved-headers report

- **Symptom:** `unresolved_headers.md` listed an FRD field's line choices as
  `<col>: <row label>` only - two labelled lines of one cell were indistinguishable there
  (the App dialog showed them apart).
- **Reproduced:** a synthetic question with two line candidates of one cell (the new test).
- **Root cause:** `layout/answers.py :: unresolved_report` formats a candidate from `col` /
  `table` and `header` / `label` only; the line candidate's `inline_label` (post192,
  `layout/resolve._frd_line_candidates`) was never shown.
- **Change:** `layout/answers.py :: unresolved_report` appends ` · <inline_label>` when a
  candidate carries one. `line` (label + VALUE) stays out - this file is structural only.
- **Reach:** 12-pair check (framework, mock, post201 vs post202): outcomes unchanged,
  295 / 295 files, no artefact / contract / layout moved. Only `unresolved_headers.md` of
  the 3 NEEDS_ANSWERS pairs (08, 09, 10) changed: their FRD line choices gain
  ` · <line label>` (3-4 lines each). Every other report diff = the version /
  environment-path line.
- **Side effects:** none found.
- **Unchanged:** every other candidate shape (STTM columns, FRD cells); the dialog; the
  answers keys; no artefact.
- **Tests:** `tests/test_unresolved_report_inline_label.py ::
  test_two_line_choices_of_one_cell_differ_by_their_line_label` (failed with the change
  stashed; asserts no value text appears).
- **Verified:** `.venv` 2621 passed; `.venv-d1` 2272 passed (with the de-flaked
  `test_m93_chooser` timing tests under full load); ruff clean; 12-pair check alone.
- **Revert:** drop the ` · inline_label` term in `unresolved_report`, or `git revert`.
- **Deployed:** dev not yet (STOPPED); staging c67ba0e 2026-11-18.

## 0.5.8.post201 — tester's STTM: the Comments column (standard band) was read by nothing

- **Symptom:** the tester's run (staging, post199/200) wrote no STDDelta / review-copy
  trace of her STTM Comments notes (4 date-format, 4 SPLIT_PART among 11 filled cells,
  4 mapping sheets); she asked whether the agent reads Comments. (Her empty
  DATA_QUALITY_RULES sheet is by design - post171 - and stays empty: none is a null /
  duplicate check.)
- **Reproduced:** her STTM (mock, /tmp, deleted after): discovery placed no `comments`
  role on any sheet; the STTM contract carried `value_spec` on 0 fields.
- **Root cause:** the Comments header is the standard band's last column;
  `layout/discover.py` resolves a target band's headers through
  `extractor.discovery.roles.target`, which had no `comments` role, so the column was
  dropped. Also `extract/generic.py` read `value_spec` from `source.comments` only - a
  trailing Comments column (`rules.comments`) was placed and never read.
- **Change:** `config/config.yaml :: extractor.discovery.roles.target.comments` (new);
  `extract/generic.py :: _comments` (new; `build_generic_contract`'s `value_spec`
  fallback); `layout/discover.py :: mapping_differences` skips a target band's
  `comments` role; `label_groups` ignores Comments as span evidence (`_SPAN_NEUTRAL_ROLES`,
  the side effect below). Why no new reader pass (READER_GENERALIZATION): one config role +
  one shared fallback for every band, not a field-specific pass.
- **Reach:** 12-pair check (framework, mock, post200 vs post201, after the side-effect
  fix below): outcomes unchanged (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2 GATE_FAIL,
  2 FAIL), 295 / 295 files, no DDL / IIG / test-case cell and no contract moved. ONE real
  change: pair_10's STTM layout places the standard band's Comments column on its 4
  mapping sheets (4 "no role, ignored" header notes gone); pair_10 stops at
  NEEDS_ANSWERS before a contract, so nothing downstream. Every other report diff = the
  version / environment-path line.
- **Side effects:** found by the first 12-pair run and FIXED in this version: on a sheet
  with no band title row (pair_07), `layout/discover.py :: label_groups` sizes a target
  band by its run of target-role headers - Comments, now a target role, stretched the
  standard band over the trailing Recycle Flag / DQ-mandatory / Comments columns (the
  DQ-mandatory column then read by nothing; the open standard-column question gained a
  candidate). Fix: `_SPAN_NEUTRAL_ROLES` (Comments) - placed inside a band, never span
  evidence. Re-run: pair_07 byte-identical to post200. Test:
  `test_a_trailing_comments_column_never_widens_a_label_group_band` (failed before the
  fix: band (5, 11) instead of (5, 8)).
- **Unchanged:** DATA_QUALITY_RULES (document-stated checks only); the description
  fallback (`source.comments` only - a Comments cell is never a COMMENT/description);
  a row whose load rule / transformation / business rule states rule text keeps it
  (Comments is the fallback only); the legacy MAPPING- reader's profile.
- **Tests:** `tests/test_target_band_comments_post201.py ::
  test_the_standard_band_places_its_comments_column`,
  `test_a_target_band_comments_cell_is_the_rows_rule_text` (both failed with the config
  line reverted), `test_every_bands_comments_join_once_in_band_order` (failed, with the
  contract test, with `_COMMENT_KEYS` = `source.comments` only).
- **Verified:** `.venv` 2618 passed; `.venv-d1` 2269 passed (final tree); ruff clean;
  12-pair check alone (twice: the side effect, then clean).
- **Revert:** delete `roles.target.comments` (the standard / stage Comments is unread
  again; `_SPAN_NEUTRAL_ROLES` is then inert) and set `_COMMENT_KEYS =
  ("source.comments",)`, or `git revert`.
- **Deployed:** dev not yet (STOPPED); staging 12a8f46 2026-11-18.

## 0.5.8.post200 — generic: FRD labels match synonyms with spaces ignored (the post195 class, FRD side)

- **Symptom (class):** an FRD label written without its space ("LoadType:") matched no
  synonym, so its field stayed open and was asked (post198 closed the same class for
  STTM / VDD headers only).
- **Reproduced:** post196's synthetic requirement FRD with its Load Type line written
  "LoadType:" - both load strategies unresolved on post199.
- **Root cause:** `extract/frd_docx.py` compared `normalize_label(cell)` with
  `normalize_label(synonym)`; `normalize_label` keeps word boundaries as spaces.
- **Change:** `extract/frd_docx.py :: label_key`, `LabelTable`, `LabelSet` (new);
  `_lookup` and `_markers` return a `LabelTable`; the label sets in `_stated_pattern`,
  `requirement_landings`, `_place_line_fields`, `_place_load_type_blocks`,
  `requirement_file_names`, `requirement_load_type_keys`, `_value` (block layer),
  `_nested_rows`, `parse_object_name_block`, `nested_table_names`, `parse_layer_blocks`,
  `split_labelled_lines` use them; `_names_label` (sr_signal) accepts the space-free
  equality; `layout/resolve.py :: _frd_questions` uses `_lookup`. No config change. Why
  no new reader pass: this is the generic grammar change READER_GENERALIZATION asks for.
- **Reach:** 12-pair check (framework, mock, post199 vs post200): outcomes unchanged
  (5 PASS_WITH_OPEN_INPUTS, 3 NEEDS_ANSWERS, 2 GATE_FAIL, 2 FAIL), 295 / 295 files, no
  DDL / IIG / test-case cell moved. ONE real change: pair_08's FRD titles its Data
  Quality section with a space after the "/" of the configured spelling - post199
  skipped that Solution Requirement table ("no row names a metadata section"), post200
  reads it: the FRD contract gains one `validation_rules` entry (6 -> 7; section
  `data_quality`) and its report the matching provenance lines. Every other report diff
  = the version / environment-path line (old side ran from a worktree).
- **Side effects:** the pair_08 rule above is the intended class (a label read that was
  missed); it reaches Layer 2 only (OFF for ACFC) and no artefact.
- **Unchanged:** `normalize_label` (values, blank words, label agreement, prefix tests);
  the section-title prefix rule; the layer-heading word split; key phrases; an exact
  match always wins; a space-free collision between two keys matches neither.
- **Tests:** `tests/test_label_key_post200.py :: test_label_key_drops_spaces_only`,
  `test_label_table_exact_first_then_space_free_and_never_a_pick`,
  `test_label_set_matches_space_free_and_keeps_it_through_union`,
  `test_a_one_word_frd_label_is_read_without_its_own_synonym` (all 4 failed with
  `label_key` returning `normalize_label`), `test_no_two_keys_share_a_label_key_in_the_
  shipped_config` (the guard).
- **Verified:** `.venv` 2614 passed; `.venv-d1` 2265 passed; ruff clean; 12-pair check
  alone.
- **Revert:** make `label_key` return `normalize_label(text)` (one line - the containers
  then match exactly as before), or `git revert`.
- **Deployed:** dev not yet (STOPPED); staging 3e9168f 2026-11-18.

## 0.5.8.post199 — generic: one load-strategy alias table (the same word read differently by document)

- **Symptom (class):** a load-strategy word read differently by which document stated
  it ("Merge" = Upsert in an STTM meta row, null + ambiguity in an FRD); "Incremental"
  (a load TYPE) read as Append on the STTM / answers side.
- **Reproduced:** the two readers side by side on the same words (the new test's table).
- **Root cause:** two readers - `resolve/gapfill.py :: canonical_strategy` with a code
  table `_STRATEGY_ALIASES`, `extract/frd_docx.py :: canonical_strategy` with the config
  table only - and different normalisation (punctuation-free vs label form).
- **Change:** `resolve/gapfill.py :: strategy_reading` (new, the one reader);
  `canonical_strategy(text, synonyms)` and `parse_load_strategy_text(text, markers,
  synonyms)` take the table (callers: `resolver._answered_unstated`, the resolver's STTM
  meta step, `layout/resolve._FeedGapFiller.run` step c); `_STRATEGY_ALIASES` removed;
  `frd_docx.canonical_strategy` delegates; `config/config.yaml ::
  extractor.frd.load_strategy_synonyms` holds every alias, "Incremental" dropped.
- **Reach:** 12-pair check (framework, mock, post198 vs post199): outcomes unchanged,
  295 / 295 files, no artefact cell moved, all 28 FRD / STTM contracts byte-identical -
  no pair's load strategy reads differently (none writes "Incremental" in an STTM or
  "Merge" / "Full Load" in an FRD). Only diff: the build stamp.
- **Side effects:** none found.
- **Unchanged:** the three canonical strategies; the leading-word rule stays opt-in (Load
  Type block lines only); the post197 key phrase reading; an answer that names no
  strategy is still refused loudly (post115).
- **Tests:** `tests/test_strategy_aliases_post199.py` (the alias table set back to its
  single entry -> 7 failed; "Incremental" put back -> the drop test failed);
  `tests/test_frd_gapfill.py :: test_load_strategy_text_parsing` passes the table.
- **Verified:** `.venv-d1` 2260 passed; `.venv` 2609 passed; ruff clean; 12-pair check
  alone.
- **Revert:** `git revert` (code + config move together); to restore only "Incremental"
  add `"Incremental": "Append"` to the table.
- **Deployed:** dev not yet (STOPPED); staging 7f57610 2026-11-17 (post198 + post199).

## 0.5.8.post198 — generic: STTM / VDD headers match synonyms with spaces ignored (the post195 class)

- **Symptom (class):** a header written without its space ("FieldName") matched no role
  synonym, so every mapping sheet asked the role (post195 fixed one spelling by hand).
- **Reproduced:** post195's case with the hand-written `fieldname` synonym removed
  (synthetic workbook, the tester's header shape).
- **Root cause:** `layout/discover.py` compared `normalize(header)` with
  `normalize(synonym)`; `normalize` keeps word boundaries as spaces, so one-word and
  spaced spellings differ.
- **Change:** `layout/discover.py :: header_key` (new); the role-table builds and header
  lookups in `_resolve_flat_roles`, the target-role runs, `_target_role`, the target
  spans, `_resolve_band_roles`, `_mapping_source_vocabulary` use it. No config change.
- **Reach:** 12-pair check (framework, mock, post197 vs post198): outcomes unchanged,
  295 / 295 files, no artefact cell moved, and all 12 STTM layout profiles
  byte-identical - no header of the 12 pairs resolves differently. Only diffs: build
  stamp, report version / environment-path lines.
- **Side effects:** none found.
- **Unchanged:** `normalize` (all value / name comparisons); meta labels, segment words,
  sheet-name segments; FRD labels; ambiguity handling (two roles = refused).
- **Tests:** `tests/test_header_key_post198.py :: test_header_key_drops_spaces_only`,
  `test_a_one_word_header_resolves_without_its_own_synonym` (both failed with
  `header_key` returning `normalize`), `test_no_two_roles_share_a_header_key_in_the_
  shipped_config` (the guard).
- **Verified:** `.venv-d1` 2248 passed; `.venv` 2596 passed + the known load-sensitive
  `test_m93_chooser` timing test (3/3 alone); ruff clean; 12-pair check alone.
- **Revert:** make `header_key` return `normalize(value)` (one line), or `git revert`.
- **Deployed:** dev not yet (STOPPED); staging 7f57610 2026-11-17 (post198 + post199).

## 0.5.8.post197 — tester's pair: TGT_PRIMARY_KEY asked although each requirement states its keys

- **Symptom:** after post196 (files + LOBs answered), generate asked
  `feeds.<feed>.primary_key` for all 4 tables; the FRD's Load Type lines name each
  table's merge columns.
- **Reproduced:** the tester's staging pair, mock, post196, staging's layout cache.
- **Root cause (two):** (1) `extract/frd_docx.py` read the strategy of a Load Type line
  and dropped the rest ("using keys ..."), so `FrdFeed.key_statement` stayed empty;
  (2) `primary_key.py :: _match` counted only the mapped data fields as the table's
  columns - two of the three key names are the STTM's audit rows (columns the DDL
  creates), so even a stated key matched nothing.
- **Change:**
  - `extract/frd_docx.py`: new `requirement_load_type_keys`; `read_frd`'s
    `_requirement_keys` (own row first; single-feed FRD: one set -> the statement, sets
    that differ -> `structured[...key_statement]` per-file blocks by file name).
  - `layout/resolve.py :: resolve_structured_fields`: a `key_statement` block row ->
    the matched feed's `key_statement` (`frd_nested:` flag).
  - `primary_key.py`: `TableKey.audit` + `audit_names`; `_match` accepts an audit column
    name (written as the table writes it). `metadata_template._key_cell` passes the
    detail table's audit columns.
  - `config.py` + `config/config.yaml`: `extractor.frd.load_type_key_phrases`.
- **Reach:** 12-pair check (framework, mock, post196 vs post197): outcomes unchanged,
  295 / 295 files, no DDL / IIG / workbook cell moved (no pair's TGT_PRIMARY_KEY changed
  by the audit-column match; no pair takes the Load Type key reader). Only diffs: the
  build stamp and the reports' version / environment-path lines. The tester's pair
  (mock, files + LOBs answered): NEEDS_ANSWERS -> PASS_WITH_OPEN_INPUTS.
- **Side effects:** none found (12-pair check, both suites).
- **Unchanged:** every key name must still be a column of the table (no partial key);
  the key is a PROPOSAL written by the profile default / the BSA's choice as before
  (post70 / post81); a non-detail table gets no audit match (the FRD key is the detail
  table's); a feed whose file is still asked gets no key until the file is chosen.
- **Tests:** `tests/test_frd_requirement_keys_post197.py ::
  test_one_key_set_for_every_requirement_is_the_feeds`,
  `test_differing_key_sets_go_to_each_feed_by_its_file`,
  `test_a_key_may_name_the_tables_audit_columns`. Revert proof: key phrases emptied ->
  the two reader tests failed; `resolve.py` from post196 -> the per-feed test failed;
  only the `_match` audit branch removed -> the audit test failed (assertions, not
  import / signature errors).
- **Verified:** `.venv-d1` 2245 passed; `.venv` 2593 passed + the known load-sensitive
  `test_m93_chooser` timing test (3/3 alone); ruff + scrub clean; 12-pair check alone.
- **Revert:** empty `load_type_key_phrases` (reader off); remove the `key_statement`
  branch in `resolve_structured_fields`; remove the audit branch in `_match`.
- **Deployed:** dev not yet (STOPPED); staging 71299d6 2026-11-17.

## 0.5.8.post196 — tester's paused run: requirement tables of a mixed FRD never read

- **Symptom:** after post195, the run still asked the stage / standard load strategy and
  the file format (and LOBs / domain) although the FRD's Solution Requirements state the
  strategies and the file names.
- **Reproduced:** the tester's staging pair, mock, post195, staging's layout cache:
  layout asked load strategy + format + LOBs (+ domain live); extraction asked the format
  of each of the 4 feeds.
- **Root cause:** `extract/frd_docx.py :: _discover_family` takes F1 as soon as one F1
  section table exists (here Data Quality + Vendor Metadata), so the Solution Requirement
  tables are never read; and no reader knew their shape - values as lines of the
  Functional Requirement cell (a "Load Type:" block with STG / STD sub-lines, the file
  name in angle brackets on the first line). `_discover_f2` would not read it either (it
  wants a metadata-section row). With no file pattern, `layout/resolve.py ::
  _FeedGapFiller.run` had nothing to take a format from.
- **Change:**
  - `extract/frd_docx.py`: new `load_type_block`, `canonical_strategy`,
    `_place_load_type_blocks` (chained after `_place_line_fields` in `discover_frd`),
    `requirement_file_names`; `_value` reads a `block_layer` source; `_strategy` uses
    `canonical_strategy`; `read_frd` takes the requirement file names (single-feed, no
    pattern) and reads a block strategy with the leading-word rule + a citation flag.
  - `layout/frd_profile.py :: FrdFieldSource.block_layer` (new, default None).
  - `config.py` + `config/config.yaml`: `extractor.frd.load_type_block_labels`,
    `requirement_file_name_labels` (empty default = off).
  - `layout/resolve.py :: _FeedGapFiller.run` step b: no statement -> the extension.
- **Reach:** 12-pair check (framework, mock, post195 vs post196): outcomes unchanged
  (5 PASS_WITH_OPEN_INPUTS, 2 GATE_FAIL, 2 FAIL, 3 NEEDS_ANSWERS), 295 / 295 files, no
  DDL / IIG / workbook cell moved; no pair takes a new reader (no `frd_load_type_block` /
  `frd_requirement_file_names` / extension-only format flag). Only diffs: the build
  stamp and each report's version / environment-path lines. The tester's pair (mock):
  layout questions 7 -> 4 (LOBs, domain, the file of 2 tables); load strategy and
  format no longer asked; generate then asks the primary key per feed.
- **Side effects:** the new `block_layer` field first serialised as `null` in every FRD
  profile (the tracked-fixture test caught it: `frd_f1_pair_1.layout.json drifted`);
  fixed in the same version - `FrdFieldSource` writes `block_layer` only when set, so
  every profile without a Load Type block is byte-identical to post195.
- **Unchanged:** F1 / F2 family choice itself (the section tables still decide the
  family); LOBs / domain (not stated - still asked); two files whose names match no
  table stay a choice question (never paired by elimination of 2+); the upsert keys of
  a Load Type line (differ per requirement; not read - post197 candidate); a strategy
  cell outside a Load Type block keeps the exact-match rule (no leading-word reading).
- **Tests:** `tests/test_frd_requirement_blocks_post196.py` (5);
  `tests/test_format_from_extension.py :: test_no_format_anywhere_the_extension_decides`,
  `test_no_format_and_two_extensions_is_asked`, `test_no_format_and_a_txt_name_stays_the_
  ordinary_question`; `tests/test_layout_resolution.py ::
  test_tracked_layout_profiles_equal_a_fresh_build` guards the serialisation. Revert proof: with the two config labels emptied, the two reading
  tests failed on assertions; with `resolve.py` from post195, the two extension tests
  failed.
- **Verified:** `.venv-d1` 2242 passed; `.venv` 2590 passed + the known load-sensitive
  `test_m93_chooser::test_index_writes_never_run_inside_a_selection_step` (both suites in
  parallel; 3/3 alone); ruff clean; scrub check clean; 12-pair check run alone.
- **Revert:** empty `load_type_block_labels` / `requirement_file_name_labels` in
  config.yaml (the readers switch off); revert the step-b block in `resolve.py` for the
  format fallback; or `git revert` the post196 commit.
- **Deployed:** dev not yet (STOPPED); staging 08786dc 2026-11-17 (post196).

## 0.5.8.post195 — tester's paused run: source field name UNRESOLVED on a multi-sheet STTM

- **Symptom:** a staging run paused on 5 `UNRESOLVED sheets[<i>]/source/field_name` lines,
  one per mapping sheet; the run could not go on without a person placing the column.
- **Reproduced:** the tester's staging uploads, mock, post194, staging's own layout cache:
  two STTM versions 5 UNRESOLVED each, a third version 4 (all `source/field_name`).
- **Root cause:** the source band's field-name header is written as one word; `discover`
  normalizes it to `fieldname`, and `extractor.discovery.roles.source.field_name` had
  only the spaced spelling (and `columnname`, the same pattern for another header).
- **Change:** `config/config.yaml` :: `extractor.discovery.roles.source.field_name` +
  `"fieldname"`. No code change.
- **Reach:** 12-pair check (framework, mock, post194 vs post195): outcomes unchanged
  (5 PASS_WITH_OPEN_INPUTS, 2 GATE_FAIL, 2 FAIL, 3 NEEDS_ANSWERS), 295 / 295 files, no
  DDL / IIG / workbook cell moved - no pair writes the one-word header. The only diffs:
  the build stamp and each report's "Produced by" line (version + checkout path).
- **Side effects:** none expected - a header must normalize to exactly `fieldname`.
- **Unchanged:** a source header written only `Field` (another upload) stays a question:
  too generic to be a synonym on one sighting. The DQ-sheet `dq_sheet_field_headers`
  overlay key already read `FieldName` and is untouched.
- **Tests:** `tests/test_sttm_fieldname_header.py ::
  test_field_name_header_resolves_with_or_without_the_space` - the `FieldName` case failed
  with only the synonym removed (run before the config edit).
- **Verified:** `.venv-d1` 2234 passed; `.venv` 2582 passed + 1 known load-sensitive
  timing test (`test_m93_chooser::test_index_writes_never_run_inside_a_selection_step`,
  ran beside the 12-pair check; passed 3/3 alone - H25); ruff clean; the tester's three
  STTM versions 0 UNRESOLVED (mock). The first 12-pair run's old side timed out pair_03
  under the same load (901 s) - re-run alone, equal.
- **Revert:** remove `"fieldname"` from that synonym list (and the test).
- **Deployed:** dev not yet (STOPPED); staging 08786dc 2026-11-17 (post196).

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
- **Deployed:** dev 294f4b3 2026-11-16; staging c53102b 2026-11-17 (with post194).

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
- **Deployed:** dev 294f4b3 2026-11-16; staging c53102b 2026-11-17 (with post194).

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
- **Deployed:** dev 294f4b3 2026-11-16; staging c53102b 2026-11-17 (with post194).

## Not fixed in post193 (decisions open) — for the record

- **#9 / #10** fixed-width `SRC_FORMAT = CSV` + `SRC_FILE_DELIMITER = '|'`: framework
  conventions only the tester states; waiting on confirmation for every fixed-width feed.
  (Reproduced: the fixed-width handler rows ARE generated; SRC_FORMAT is blank, not TXT.)
- **#14** DataTypeCastRule: reverses post171 ("no cast rule"); the pair-1 golden has one.
- **#16** no grand master for a Workflow run: changes the post166 flow.
- **#17** `WF_` names: no code - already the "Databricks Workflow (WF_)" run option
  (post187).
