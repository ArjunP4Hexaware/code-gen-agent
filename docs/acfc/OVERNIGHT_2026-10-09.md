# Overnight 2026-10-08 → 10-09 — robustness to unseen documents (`feature/multi-table`)

Unattended run for the Friday 2026-10-09 session, where a framework owner hands
the agent an FRD + STTM pair it has never seen. **Nothing was pushed.** Every
commit is local on `feature/multi-table` (head = the commit carrying this file),
version marker **0.5.8.post26**.

**Final verification (integrated tree):**
- **Python 3.11:** 1164 passed / 27 skipped. Every skip is the pre-existing "contract fixtures removed 2026-08-22".
- **Python 3.10:** 1163 passed / 28 skipped (the extra skip: `tests/test_ruff_dependency.py` needs `tomllib`, stdlib from 3.11)
- **Lint:** ruff clean (`src/ tests/ ui/backend/ scripts/iig_scorecard.py`).
- **Frontend:** tsc clean; vitest 29 passed; `ui/frontend/dist` identical to a fresh build (`index-CHt2wtuJ.js`).
- **Scrub:** 0 repo hits and 0 local-denylist hits on every added line since 1ecbacd (85 files), and 0 on the text inside the 12 new binary fixtures.
- **Real SD pair, mock run, scores only:** layout / extract-sttm / generate exit 0, 3 feeds PASS_WITH_FLAGS; scorecard demographic and community-risk matched 43, individual-risk 46, diff 0 on all three (identical to before tonight)

## What landed (oldest first)

| Commit | What |
| --- | --- |
| `14fd40c` | **Chunk A** — STTM bands located by their label group; layer only from evidence; `UNRESOLVED <sheet>/band[<n>]/layer` |
| `c3663a8` | Chunk A — the 9 findings of an independent review, each fixed and pinned by a test that fails on 14fd40c |
| `8b64eab` | Chunk A addendum — `MAPPING-` sheets read by the general reader first, proven equal to the legacy reader |
| `8005d04` `670dc63` `b78ead8` `de520e4` | **Chunk D** — `metadata_inserts.sql` table names; the STGDELTA stage → standard row; acfc_prx + iig_v2 defaults; docs + Friday 12 / 13 |
| `e1d3659` `38cb321` | **Chunk C** — the App's needs-answers path, the band question in the dialog, readable error cards |
| `5db03c2` `df582af` `2047a6c` | **Chunk B** — six cold pairs, the generator fixes they forced, the drill as a test |
| `3565459` | the `MAPPING-` equivalence test names the workbook the legacy reader refuses (cold_4) |
| `da15f82` … `1bb8302` (13) | the review findings of B, C and D, one commit each |
| *(this commit)* | this report, CLAUDE.md START HERE, marker post26 |

How it ran: I did Chunk A myself (blocking; it needed the whole discovery
path in one head), then ran B, C and D as parallel writer agents in their own
worktrees (cut at 14fd40c), each followed by a read-only reviewer. I
integrated them by cherry-pick; two conflicts were resolved by hand: B's
answer rounds superseded my band-first pre-pass, and both sides of
`discover.py` were kept. Three fixer agents then addressed the reviews.
Cost: 1 + 7 + 3 agents (~3.5M subagent tokens); every writer stayed within
the 3-agent repro-lane cap. After your mid-run budget rules, the fixers ran
the full suite once each, at the end.

## Chunk A — band detection by header labels

- **Location.** A target band is the run of `roles.target` headers that places at least three of catalog / schema / table / column / data type, with column or data type among them. It is found anywhere in the header row: any order, any offset, any count of bands, never a fixed column. Order inside a band is free. A repeated role splits a run at the column-order restart, so a source "Data Type" next to Schema stays in the source band.
- **Layer, from evidence only**, the first that names exactly one layer wins:
  1. an answer
  2. the band title row (`titles` words or a `band_tokens` token)
  3. a whole word of the band's own headers (`header_words`)
  4. the band's Catalog values (PR_DLK → stage, PR_STD → standard)
  5. the band's Schema values (`stg_` → stage)
  6. elimination, after your follow-up rule: stage and standard each claimed with their own evidence, exactly one band left over, and it sits LEFT of both target bands. It is the source, and layout (and extract-sttm `--answers`) prints a `NOTE <sheet>/band[<n>]/layer — … layer by elimination` line. A leftover to the right, or more than one, still asks. An independent check of the rule added three guards:
     - source must not already be claimed (by another band, a "Source…" title elsewhere, or a field-name column outside the bands);
     - a band whose own evidence lost a same-layer conflict is never "left over";
     - a layer by elimination is never trusted from the layout cache.

  Column order is never evidence. "in DL" / "DLK" are **OFF** as stage evidence (your call; one list in `extractor.discovery.layer_evidence.header_words`, flippable).
- **The question.** A band nothing names, or two bands naming one layer, gets one line per band:
  `UNRESOLVED <sheet>/band[<n>]/layer — band[<n>] (columns H–K): Schema | TableName | ColumnName | DataType — <what was seen>; answer under answers: with source | stage | standard`.
  `extract-sttm` holds that sheet's feed back with the same line, and the App shows it in the dialog. Answer it in answers.yaml with `{sheet, layer: band[2], role: layer, value: stage}`.
- **Missing TableName** stays `UNRESOLVED <sheet>/<layer>/table`, never a blank.
- **Nothing read before moves.** 23 workbooks were dumped before tonight and again on the final tree (all fixtures plus the real ones at the root, read in place). Every STTM profile is byte-identical, apart from a diagnostic note on pair 4 naming its ForReference sheet as "not read as a mapping sheet".
  - The three IIG workbooks (the pair-1 golden IIG, the SFMC IIG and the real one at the root) used to stop with "no mapping sheets found". Chunk B's candidate-sheet pass now reads them as candidates, by design. They still classify as `unclassified` ("confirm: …"), never as an STTM.
  - Pass 1, the band-row reading, wins when the label groups agree with it.
  - The groups rebuild spans only when the title row contradicts them (titles merged over part of a band).
  - Pass 2 (header-row groups) runs only when pass 1 finds no mapping sheet in the workbook.
- **Cache.** Value-derived layers are never trusted from the layout cache. On every hit, for the document entry and the pair entry, the value chain is re-run (Catalog values first, then Schema) and must give the same layer and the same evidence kind.
- **Classifier.** A workbook is an STTM only when a band has target-layer evidence. Otherwise it is "unclassified — confirm: …", and a person can still pick it and answer the band questions.
- **Fixtures** (`tests/acfc_shapes/bands.py`, built in code):
  - families A–E
  - the SD shape (stage Schema/TableName at I/J, standard at N/O, no Catalog), including titles merged over I–J / N–O only
  - three look-alike bands without titles (three UNRESOLVED) and with titles (clean)
  - one band with no evidence (one UNRESOLVED)
  - one band with a `stg_` schema (stage, no question)
  - header words, catalog values, two bands claiming stage, any order and offset, missing TableName
  - the CLI chain before and after answers.yaml

  Tests: `tests/test_band_detection.py` (45).
- **Independent review (9 findings, all fixed in `c3663a8`):**
  1. the source Data Type was glued onto the stage band
  2. a database-shaped source band was held back
  3. order inside a band mattered
  4. band questions were sent to the advice model
  5. answers.yaml could not place a column on a band that exists only once answered
  6. a meta row was taken as the title row
  7. a Table Details sheet was read as a mapping sheet
  8. the segmented `MAPPING-` refusal was lost
  9. the cache re-check tried only one value kind

### Addendum — the `MAPPING-` reader is not a separate world (`8b64eab`)

- **Order.** For any workbook with `MAPPING-` sheets, the general reader runs first. That brings evidence, the band question, and family B's own source vocabulary (`extractor.header_synonyms`) on those sheets. Its bands are used.
  - The legacy reader is the fallback when the general reader finds nothing.
  - The legacy error text survives only at the pinned `parse_workbook` entry point.
- **Equivalence, proven** (`tests/test_mapping_general_first.py`). Covered: every `MAPPING-` workbook in the fixture set (pairs 2 and 11, the CV golden, the tests' minimal sheet, the SD-shaped sheet), plus the real SD workbook read in place. Both readers place the same roles in the same columns, and `discover()` returns the legacy profile byte for byte, so contracts are byte-identical. cold_4 is the one `MAPPING-` workbook the legacy reader refuses outright; it is named in the test.
- **The differences the comparison found** (reported, not papered over):
  - **"Mandatory" / "Mandatory Field" was `required` in the general reader, `mandatory` in family B.** The general reader didn't know family B's table. It now uses it on `MAPPING-` sheets; pair 10's "Mandatory?" keeps `required` on the content path, as pinned.
  - **"Recycle Flag ( Enabled for 7 Days)" was unplaced.** The general reader matched it exactly; the rule is the prefix, which now applies everywhere.
  - **Spans and labels** differ in representation only: the legacy stage band takes in the blank separator column, its last band runs to the sheet's last column, and its labels are the canonical config text. The legacy form is kept wherever the two readings agree.
- **Hand-written variants** (`bands.sd_mapping`): other title wording, titles in row 2 / headers in row 3, one unknown header. The legacy reader refuses each; the general reader reads them and the contract carries the base sheet's fields.
  - The legacy extractor still reads the rows when every column it needs is placed. Data now starts at the profile's header row + 1, not a fixed row 3.
  - An unknown header in a column the legacy extractor requires routes the sheet to the generic extractor.
  - An untitled `MAPPING-` sheet asks `band[1]` / `band[2]` and completes after answers.

## Chunk B — the cold-pair drill

Six pairs designed by an agent that never saw the reader code (`tests/acfc_shapes/COLD_PAIRS.md`), built byte-stably (`tests/acfc_shapes/cold_pairs.py`, `fixtures/acfc_shapes/cold/cold_1..6/`). Each was run through layout → extract-frd → extract-sttm → generate `--profile acfc_prx --iig-template iig_v2`, with the ACFC overlay on and mock layout / Layer 2.

| pair | shape | owed lines before answers | exits before (layout / extract-sttm) | after answers.yaml |
| --- | --- | --- | --- | --- |
| cold_1 ch_claims_daily | family A, standard band left of stage, F1 with a Ref column | 9: 8 UNRESOLVED target roles + QUESTION `feeds[0].delimiter` (FRD pipe vs STTM comma) | 3 / 3 | 0 / 0 / generate 0, PASS_WITH_FLAGS |
| cold_2 fc_elig_monthly | fixed-width H/D/T banners, "Target 1/2" titles, unknown audit columns, F2 | 5: band[1], band[2], file_format, stage load strategy, file_patterns | 3 / 3 | 0 / 0 / 0 |
| cold_3 nb_provider_roster | family E, Raw/Curated Zone titles, F1 without catalog | 15 over 3 sheets | 3 / 3 | 0 / 0 / 0 (3 feeds) |
| cold_4 ch_rx_claims | family B, `<LOB>` × 3 + reversal into 2 tables | 14 (round 2: which file feeds a table) | 3 / 3 | 0 / 0 / 0 (2 feeds) |
| cold_5 fc_provdir | one untitled "in DL" band, no audit rows, prose FRD | 3 (round 2: `feeds[0].audit_columns`) | 3 / 3 | 0 / 0 / 0 |
| cold_6 ch_member_enroll | family C, document title row, Landing/Curated qualifiers, tab, F2 | 8 | 3 / 3 | 0 / 0 / 0 |

`tests/test_cold_pairs.py` pins, per pair and stage, the exact (label, key) of every QUESTION / UNRESOLVED line before answers (`expected_questions.yaml`). It also proves `answers.yaml` settles every key and that the chain then completes.

**Generator fixes** (`df582af`; one focused test each in `tests/test_cold_drill_fixes.py`):
- **Tracebacks:** layout no longer prints a traceback on an unreadable FRD / STTM; it is a FAIL line naming the document and the remedy.
- **FRD reading:**
  - F1 section tables with a Ref column are read.
  - An Object Name that is a file pattern is now the pattern, not the feed name.
  - An F2 requirement sentence is never a feed name.
  - A prose FRD (no table) reads as family "prose", and every required field is asked.
- **Candidate mapping sheets ("pass 3"),** read by band title spans or shared header qualifiers. Pass 3 runs only when passes 1–2 find nothing, and the classifier never calls a candidate an STTM.
- **Held back, not failed:** a sheet whose extraction stops while a required role is unplaced is held back with UNRESOLVED; it is no longer a whole-run FAIL.
- **Feeds split per sheet:** one FRD feed naming two sheets' tables is split into one feed per sheet, and the split keeps every stage table of a band.
- **Delimiter:**
  - An STTM "File Delimiter: ," is a value, not the "-" placeholder.
  - The FRD format cell ("Pipe delimited (|)") disagreeing with the STTM is a choice QUESTION.
- **FRD fields** are answerable under `gaps:` and honoured.
- **Answer rounds:** answers.yaml is re-applied over rounds (`cli.ANSWER_ROUNDS`), so a band answer, then its columns, then "which file feeds the table" all settle from one file.
- **LOBs** are taken from the STTM meta row.
- **The five Chunk A findings:**
  1. no audit rows → QUESTION `feeds[i].audit_columns`
  2. unknown audit columns are carried in framework mode (flagged); notebook mode stops with a remedy
  3. catalog unstated → answerable under `gaps:`
  4. an FRD/STTM schema disagreement → the STTM wins, flagged `frd_crosscheck`
  5. a standard-only sheet → a legitimate stop naming the band answer

**Review fixes:**
- **B1 (`ac3eaf0`):** the same delimiter rule now applies on the pure-CLI resolver path. A disagreement there is a contract-mismatch FAIL naming both cells and the remedy; it no longer silently takes the STTM's character.
- **B2 (`9e5d94e`):** a `feeds[i].feed_name` answer is refused with a note saying why. The feed name is the join key the extractor pairs sheets by. NOTE lines no longer tell you to answer a field the contract already carries.
- **B4 (`1bb8302`):** focused tests for the compound-frequency rule, plus a citation fix.

## Chunk C — the App path for needs-answers

**What changed:**
- **Held-back runs.**
  - A run whose every feed is held back now ends in the new state `needs_answers`, not "live run produced no feeds".
  - `status.needs_answers` lists each item with its key, label (QUESTION / UNRESOLVED), answers section, answer kind (band layer / column / FRD cell / gap), feed, sheet, reason and the question itself.
  - A partially held-back run ends `done` with the same list, including owed questions skipped with "Proceed with unresolved" (`b0e77b0`).
- **Re-run route.** `POST /api/demo/rerun-with-answers` takes the answers and re-runs. It refuses (400) when the documents changed since that run, and the panel says so before you click (`ec4320c`).
- **Dialog.** The band question renders as radios: source / stage / standard / none.
- **Readable errors.** Every unhandled exception returns JSON with the type, message, `where` (innermost frame `file:line in func`), cause and the health line, secrets masked. A crashed run carries the same in `status.error_detail`. The frontend shows an error card, never a white screen; the two calls that swallowed errors now show it too (`39780c7`).

**Review fixes:**
- **C1 (`a87d793`):** a re-run's answers now belong to that run only. Before, after a cancelled re-run, the next ordinary Generate could apply them to other documents.
- **B3 (`4f28d64`):** an inline `feeds[i].audit_columns` answer now reaches extraction.

**What you see** (driven in Edge with Playwright on the synthetic three-look-alike pair):
1. Generate pauses with "Which layer is band[n] of sheet …?" × 3.
2. Choosing "Proceed with unresolved" shows the yellow "Every feed is held back — 3 answers needed" panel. It survives a page reload.
3. Answering and clicking "Re-run with 3 answers…" leads to "Last live run completed."

Tests: `tests/test_app_needs_answers.py`; the remote-roles e2e test was extended with the held-back path; frontend `LayoutQuestions.test.tsx`, `ErrorCard.test.tsx` and a page-level test.

## Chunk D — the two known bugs, and the defaults

**`metadata_inserts.sql` table names** (`dml.table_names`, config):

| Sheet | INSERT INTO | Status |
| --- | --- | --- |
| DATA_FACTORY_PIPELINE_SCHEDULE | `[dbo].[DATA_FACTORY_PIPELINE_SCHEDULE]` | confirmed (walkthrough §2) |
| FILE_ADLS_INGESTION_DETAILS | `[dbo].[FILE_ADLS_INGESTION_DETAILS]` | confirmed (§5) |
| ADLS_DELTA_INGESTION_DETAILS | `[dbo].[ADLS_DELTA_INGESTION_DETAILS]` | confirmed (§7) |
| STGDELTA_STDDELTA_INGESTION_DET | `[dbo].[stg_delta_stddelta_ingestion_details]` | confirmed — **your brief** (the first ACFC run's known bug), see Decisions |
| ADLS_FIXED_WIDTH_HANDLER, DATA_QUALITY_RULES, DATABRICKS_NOTEBOOK_DETAILS, EMAIL_TEMPLATE_CONFIG (+ iig_v1's ALL_FILES_STATIC_INFORMATION) | the sheet name | `-- unconfirmed` line on the block + Friday item 12 |

- Excel truncates tab names at 31 characters, so a tab name is never assumed to be a table name.
- The walkthrough's other three tables are not IIG sheets (the file connection table stays `dml.connection_table`, flagged).
- The unconfirmed comment says where the name came from: the IIG sheet name or `framework.tables` (`91063b6`).

**STGDELTA stage → standard row**, under the ACFC overlay / family convention (pinned pair-1 / pair-4 cells unchanged):
- **Paths:** `SRC_ADLS_PATH` = the stage Processed folder without the container (`/{domain_path}Processed/`). `TGT_ADLS_PATH` and `TGT_RJT_ADLS_PATH` use the standard-container shape (`…/Processed/<table>`, `…/Reject/<table>_reject`).
- **OBJECT_ID per (group, file):** the row takes the OBJECT_ID of the file that feeds the table.
  - Several files into one table → open, with a NOTE.
  - One file into several tables → the shared value is kept, with the NOTE `stgdelta_object_id_shared:<tables>` and a Friday line (`453cc15`).
  - Pair 4 keeps its 1..n within group.
- **Constants:** "IIG test cells.xlsx" has no STGDELTA row (only 4 ADLS rows). So the standard container, the three connection ids and SRC_CONTAINER_NAME stay **open**.
  - The stage container is offered as a candidate in the cell's tooltip and in Friday item 13 (`da15f82`). It is not filled: no document states it.
- **Real SD rows:** STGDELTA blank cells went from 13 to 11 of 40 per row. The ADLS scorecard is unchanged.

**Defaults:**
- `config/overlays/acfc_env.yaml` sets `conventions.profile: acfc_prx` and `metadata.template: iig_v2`, for the App and every CLI run under the overlay (the suite skips the overlay; `tests/test_acfc_defaults.py` checks it applied).
- The CLI's first line and `codegen doctor` name the active profile and template, e.g. `codegen 0.5.8.post26 from … · profile: acfc_prx · IIG template: iig_v2 · overlays: config\overlays\acfc_env.yaml`.

## Decisions for you

1. **STGDELTA table name.** D's reviewer read "only the walkthrough's six are confirmed" as excluding STGDELTA. I kept `stg_delta_stddelta_ingestion_details` confirmed, because your brief stated that mapping as the known bug. If you meant it unconfirmed, delete its line in `dml.table_names` (config) and it falls back to the sheet name with the `-- unconfirmed` comment.
2. **STGDELTA `SRC_ADLS_PATH` is the folder form** (no table name), matching both goldens; Friday item 13 asks. `SRC_ADLS_ARCHVL_PATH` still carries the landing container (not in the brief).
3. **Candidate synonyms (not added).** The doctrine forbids widening synonyms to fit a fixture. These header wordings were seen in the cold pairs and are left as answers: "Target Schema Name", "Target Table Name", "Target Column Name", "Target Data Type" without " in DL", "Target Tbl / Target Col / Target Type", "Source Column", "Source Field". With live layout the model places them; with mock layout a person does.
4. **An STTM-vs-FRD stage TABLE disagreement is still a FAIL.** Making the STTM win, as it already does for the schema, would move the pinned assertion in `tests/test_m9_acfc_findings.py::test_contract_matcher_reports_which_side_was_qualified`. Not done.
5. **The multi-file OBJECT_ID note is scoped to the ACFC overlay.** Applying it to every feed would move three pinned expectations:
   - `PAIR1_GATE_FLAG_KINDS`: +1 `stgdelta_object_id_open`
   - `INVENTORY['pair11']`: Engineer 153 → 150, Engineer (confirm) 156 → 159
   - pair 4's flag count: +3

   Not done.

## Rules kept, and where a test moved

- **No golden, `fixtures/layout_profiles/` or `tests/snapshots/notebook_mode.json` edit.** The pair-1 / pair-4 goldens and pinned EXPECTED tables are untouched.
- **One pre-existing test helper changed:** `tests/test_metadata_inserts.py::parse_script` asserted "INSERT target == sheet name", which is the bug item D2 fixes. It now maps through `dml.table_names`. Flagged by D's reviewer; I accept it as the expectation that pinned the defect, not an edit to make a check pass.
- **Tests added tonight were corrected where a later finding showed they pinned a defect:** `test_stgdelta_stage_to_standard` (the inferred container, the silent shared OBJECT_ID) and my equivalence test (cold_4).
- **No synthetic fixture carries a client name or value**; the real documents were read in place only, and every report above gives scores and counts only.
- **The harness doc's `band[n]` key form** is a LOCAL commit on `acfc/harness-exit3` (`a6b8002`, made in a scratch worktree, not pushed), for you to push with the Genie-side regex change.
- **Spiral checks.** The spiral-detector fired three times tonight, and each was a false trigger.
  - Chunk A, signal (a): a new end-to-end test advanced through five different failures under one test name.
  - Chunk B's writer, signal (b): a command later passed under a broader one.
  - C's fixer: a deliberate repro test failing while one fix was built in parts.

  The first two are logged in `docs/spiral-log.md`. The Chunk A one also has a known-causes entry and a replay scenario. C's fixer noted its trigger in its report without logging it.

## Left open

- **Round-2 questions:** an answer can open the next question (a band's columns, which file feeds a table, `audit_columns`). One answers.yaml settles the whole chain, but the harness only sees round-2 keys on the next run.
- **The App re-asks skipped optional questions:** a re-run asks again, in the dialog, the optional questions skipped with "Proceed", so completing a held-back feed takes one more Proceed click.
- **A wrong frequency cross-check on multi-file pairs:** `layout_crosscheck:frequency` compares every feed with the first File Details row. Fixing it to compare each feed with its own row may move pinned flag lists for multi-file fixtures, so it needs your go.
- **The ACFC overlay pins the SD family everywhere:** it applies the SD audit-column convention to every feed (cold_4's STGDELTA SRC_COLUMNS follows SD, not its own STTM). This is the existing pending item: split `acfc_env.yaml` per source family.
- **One-band sheets beside mapping sheets:** a one-band or other-wording sheet sitting next to sheets the band row finds is not read (pass 2 runs only when pass 1 finds nothing). That's the price of not turning pair 4's ForReference sheet into a feed; a diagnostic names such a sheet.
- **Inherited from earlier sessions:**
  - re-running the real documents in ACFC on this build;
  - the harness side (Genie);
  - `extract-vdd` exit 3;
  - the after-demo untrack of the real reference files.

## How to verify

```bash
export PYTHONUTF8=1 CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example
python -m pytest -q -rf -p no:cacheprovider                     # 1164 passed / 27 skipped
python -m pytest -q tests/test_band_detection.py tests/test_mapping_general_first.py \
  tests/test_cold_pairs.py tests/test_cold_drill_fixes.py tests/test_app_needs_answers.py \
  tests/test_stgdelta_stage_to_standard.py tests/test_acfc_defaults.py
python -m codegen.cli doctor                                    # profile + template in line 1
cd ui/frontend && npx tsc -b && npx vitest run                  # 29 passed
```

A cold pair by hand (overlay on, mock):

```bash
codegen layout --workbook fixtures/acfc_shapes/cold/cold_5/STTM_fc_provdir.xlsx \
  --frd fixtures/acfc_shapes/cold/cold_5/FRD_fc_provdir.docx --dry-run --no-cache --require-complete
```

This exits 3 with `UNRESOLVED <sheet>/band[1]/layer`. Add `--answers fixtures/acfc_shapes/cold/cold_5/answers.yaml` and it exits 0.
