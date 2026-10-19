# Follow-ups to run_20261019T181043Z_fe61bc4 (report only)

* runner: claude-code container, src-only (post73, fe61bc4); provider live, databricks-claude-opus-5, --environment D1, notebook + framework

## 1. pair_11 rerun with the answers from the volume

* Pair answers copied into the state volume as answers/<pair>/answers.yaml for pair_1, pair_2, pair_11 and pair_12; the container runner now prefers that file over the pair folder's.
* The first run had already passed pair_11's answers file (the pair folder holds one; it answers 1 gap). The old Git folder's codegen-state/answers holds a pair_2 file only.
* Rerun (pair_11 alone, answers source: volume): outcome NEEDS_ANSWERS, 15 QUESTION keys, unchanged.
* All 15 keys are notebook-mode paths, 3 per feed for its 5 feeds: feeds.feed_<n>.notebook.landing_path / .archive_path / .reject_path. Notebook output withholds the notebook while a blocking line is open (notebook present: no x 5); the framework artefacts are written (DDL / IIG / DML emit PASS). The answers file has no notebook paths.

## 2. Pairs 07-10: Friday NEEDS_ANSWERS vs today FAIL

Friday (post57 0ac6846) all four stopped at layout (NEEDS_ANSWERS). Today the live layout stage (sttm_parse) PASSES for all four; each stops later:

| Pair | Today: stages | first_error_line (coordinates tier) |
| --- | --- | --- |
| pair_07 | layout PASS; extract-sttm NEEDS_ANSWERS (2 keys); generate FAIL | generate — Contract not found: STTM <workdir>/pair_07/… [FileNotFoundError] |
| pair_08 | layout PASS; extract-sttm FAIL (1 key) | extract-sttm — STTM Required element missing (role target_type) at STTM sheet 1 row 96 col 17 [ExtractionError] |
| pair_09 | layout PASS; extract-sttm NEEDS_ANSWERS (3 keys); generate FAIL | generate — Contract not found: STTM <workdir>/pair_09/… [FileNotFoundError] |
| pair_10 | layout PASS; extract-sttm FAIL (3 keys) | extract-sttm — Contract fails validation at STTM sheet 2 [ExtractionError] |

Reading:
* Live layout is not where they fail: it resolves what the dry-run layout left open on Friday.
* pair_07 / pair_09: the real state is NEEDS_ANSWERS at extract-sttm. The FAIL is the harness's: it runs generate after an extract-sttm exit 3, and generate finds no STTM contract. The harness should stop a pair at an exit 3.
* pair_08 / pair_10: real extract-sttm failures, reached only now that layout resolves (a required target-type cell, a contract validation failure).
