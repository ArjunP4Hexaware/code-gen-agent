# CHANGELOG — ACFC (`feature/multi-table`)

What each version marker changes for a run inside ACFC. Newest first. Values that
must not enter git (storage account, containers, notebook names, status sets) are
named by field only — see `docs/acfc/OVERLAY_FIELDS.md`.

## 0.5.8.post57 — 2026-10-15 (D1 post55 report: leak keys, unstated values, path whitespace, scorer)

From acfc-results `run_20261015T172048Z_3e09149` and the pair_01 scrubbed diff
(`run_20261015T193331Z_3e09149`). One commit each, synthetic fixtures only.

- **Answer keys name sheets by position.** All 10 post55 leak hits were sheet
  names inside `needed_answer_keys`. Every key on stdout is now
  `sheets[<i>]/<layer>/<role>` (0-based workbook position, like `feeds[<i>]`;
  the coordinates tier's `STTM sheet <i+1>`), band keys too:
  `sheets[<i>]/band[<n>]/layer`. The name stays ACFC-side: the answers
  template's `sheet_name:` reading aid and `unresolved_headers.md`. An answers
  file may give `sheet: "sheets[2]"` or the name; an unknown position is a NOTE,
  never applied elsewhere (`codegen.layout.sheet_refs`).
- **A value no document states is NEEDS_ANSWERS, not a FAIL** (pairs 03 / 04).
  A feed whose every mismatch is `value.unstated` exits 3 with one
  `QUESTION feeds[<i>].<field>` per value, citing the contract field and the
  places searched (vocabulary only); the other feeds of the pair still
  generate. `generate --answers` (gaps:) fills the value
  (`frd_unstated:<field> source_used:user`). Two documents stating different
  values stay a FAIL.
- **Stated paths** (pair_01's `derivations [path_whitespace 19]` all came from ONE
  FRD landing cell copied with its label, `Path : <account>/<container>/<folder>`):
  - *Label stripping.* An FRD cell `<Label> : <value>` whose label is a synonym of
    the field being read (conventions profile `field_label_synonyms`: landing
    path / folder / location, file name, frequency, delimiter) is read as
    `<value>`, flag `label_stripped` with the FRD table / row. A label that is
    not a synonym of that field is never stripped.
  - *The environment's address.* A landing that starts `<account>/<container>/`
    (the account matching the profile's `storage_account_pattern`) or an abfss
    URI takes account and container from the run's environment profile; the
    folder under the container stays the document's, byte for byte. A different
    document account / container raises `environment_mismatch` naming the field
    and "document states another environment" — never the document's value.
  - *Whitespace* (switch `path_whitespace: keep | fail`, default `keep`): a
    stated path keeps its whitespace byte for byte, and each path cell gets ONE
    flag `iig_path_whitespace:<SHEET>!<A1> (<COLUMN>) — double space | leading |
    trailing | tab` for the BSA to confirm; `fail` = the old check. On the
    pair_01 shape: the D1 address, one `label_stripped`, one
    `environment_mismatch`, zero whitespace flags.
- **iig_diff, four rules** (re-scored: pair_01 export 3.2 → 28.3, see
  `docs/acfc/iig_exports/pair_01_post55/RESCORE.md`):
  (a) an identity carrying a NAME (TGT_TABLE_NAME / TGT_TABLE / @file) that
  differs, both sides one feed and one flow: leftover rows pair by feed + flow +
  row order — the name is one mismatch cell; (b) agent-template columns the
  golden lacks are `template-only` (not scored, listed once under HEADERS);
  (c) `9999-12-31` == `9999-12-31 00:00:00`; (d) segment codes through the
  profile's new `segment_codes` (hddr / det / trlr == header / details /
  trailer). `tools/iig_rescore_export.py` re-scores a scrubbed export at home
  (the post56 scorer reproduces the export's 3.2 exactly on the rebuilt pair).
- **Extraction error lines say what kind of thing.** "STTM required element
  missing" / "STTM audit column invalid" now carry `(role <role>; type
  <keyword>)` — the header role in the template vocabulary and the type keyword
  in the framework type vocabulary, both allowlisted (`run_errors.ROLE_WORDS`,
  `TYPE_KEYWORDS`; anything else is dropped or `other`).
- **Not in this release:** pair_05 / pair_06's own fixes wait for Genie's answer
  on the segment-code vocabulary (rule (d) above).

## 0.5.8.post56 — 2026-10-15 (IIG cell counts per feed; one environment resolver)

- **IIG cell counts.** pair_11 (4 feeds) and pair_12 (1 feed) printed the same
  nine "unpopulated" numbers because the harness counted one workbook for both.
  Its metric (empty cells of each sheet's used range) matches the generator's
  own SD workbook exactly, so the counter was right but the file was wrong.
  Each feed now writes its own counts to `CODEGEN_STAGES.json`
  (`feeds[].iig_cells`; read them with `codegen.run_stages.iig_unpopulated(out_root)`),
  per sheet over the rows the generator wrote:
  - `open_for_bsa`: empty cells that the inputs panel asks about (an owed-cell
    or environment NOTE);
  - `empty_other`: every other empty cell;
  - `template_blanks`: the old number, kept for this release only.
  
  `open_inputs` lists the input keys behind the `open_for_bsa` cells. One
  input can leave several cells open (`run.email_to` on each status row), so
  cells ≠ inputs. The harness should read these per feed instead of scanning a
  workbook.
- **Environment resolution.** The App and the CLI share one resolver,
  `codegen.environments.resolve`. Precedence: explicit file >
  `<state root>/environments/<name>.yaml` > the overlay block > unset
  (INPUT_NEEDED, or a QUESTION for a required key). Every field records its
  source, and the picker shows it.
  
  The 10:07 mismatch came from where `codegen-state/` was looked up: next to
  the code. The App runs a staged copy with no `codegen-state/` (gitignored, so
  `databricks sync` skips it). New App setting **`CODEGEN_STATE_DIR`**: copy
  `codegen-state/` into the staged tree and point the variable at it
  (`docs/ACFC_APP_ENV.md`). The App logs `codegen-state root: …` at startup,
  with `[MISSING]` after any folder it cannot see.

## 0.5.8.post55 — 2026-10-15 (D1 post51 12-pair report: the extraction failures)

From acfc-results `run_20261015T074546Z_97fe673`. Each fix has a synthetic
reproduction of the pair's exact error line (`tests/post51_pairs.py`).
- **pair_05**: a Segment column of `NA` / `-` / blank no longer FAILs "outside
  the Header/Detail/Trailer vocabulary". New `extractor.discovery.
  unsegmented_markers` (`na`, `n/a`, `-`, `none`, `null`): a sheet whose Segment
  cells are only these (or blank) is unsegmented, with a contract note. The
  segmented path needs one real segment word, and a marker beside one still
  FAILs at its coordinates.
- **pair_06**: a flag / indicator audit column (`*_FLAG`, `*_IND`) may be
  `tinyint` / `int` / `smallint` / `boolean`; every other audit column stays
  `string` / `timestamp`. The sets are conventions-profile fields
  (`audit_datatypes`, `audit_flag_datatypes`, `audit_flag_suffixes`;
  `docs/acfc/OVERLAY_FIELDS.md`), so an overlay widens them. Framework DDL
  renders `DELETE_FLAG TINYINT`.
- **pairs 08–10**: F2 FRDs whose Solution Requirement tables carry no caption
  are now read. A table counts as one by its row labels (`extractor.frd.
  solution_requirement_labels` / `_required_labels` / `_min_labels`), with the
  caption as a second signal. `codegen layout` prints `NOTE frd/family — F2
  signal: <header-row fingerprint | caption> — table(s) [...]`. The section row
  is found when the caption row is missing, and labels may sit after a blank
  first column. An F2 feed whose tables name no section lists its required
  fields as unresolved, never an empty feed. "Cannot be read" now names the
  table COUNT and each table's header-row fingerprint (12 hex of `term_sha256`
  over row 0), never a title: `… at FRD: 12 tables, header-row fingerprints …`.
- **pairs 03 / 04**: the count-only mismatch summary (post52 / post53) is
  confirmed end to end: `contract mismatch, feed 1 of 1: 2 tables only in FRD`.
  It stays FAIL for now. The FRD carries no column list, so the set differences
  are tables / segments, and which kinds become NEEDS_ANSWERS waits for these
  two pairs' counts under post55.
- **pair_01**: the gate is unchanged. On a FAIL, the full report (ACFC-side)
  lists the flags grouped by type, and stdout prints `GATE_FLAGS <type> — n`.
  The pushed line carries counts only: `… (failed checks: derivations
  [path_whitespace 9]; flags by type: path_normalised 9, …)`. `GATE_FAIL.md`
  gains the findings-by-rule table and the D1 step to score the quarantined
  workbook (`tools/iig_diff.py … --export-scrubbed`).
- **pair_03 at 109 s**: no stage scales with the column count (a 330-column
  synthetic pair takes about 5 s under mock), and no model call runs per column.
  The MODEL USAGE line now carries the live calls' seconds (`· 2 call(s) in
  97.3s`), so the next D1 run shows which stage spent them.

## 0.5.8.post54 — 2026-10-15 (generate: CRASHED vs GATE_FAIL)

Two failure outcomes of the generate stage, exit code 1 for both
(`codegen.run_stages.OUTCOMES`; CODEGEN_STAGES.json `stages.generate.status`):
- **CRASHED** (an exception mid-write: a template gap, an uncaught error): the
  feed's partial emit files are deleted and the emit stages SKIPPED, as post52.
  An uncaught crash now writes the manifest before the error propagates.
- **GATE_FAIL** (files complete, the correctness gate said no): every file the
  feed wrote is KEPT, moved byte for byte to `<output>/<feed>/quarantine/` (same
  relative paths) beside a `GATE_FAIL.md`. That file lists the failed checks and
  the flag counts per type, with no names or values (those stay in the run's full
  report, ACFC-side). The emit stages report PASS, and the manifest says
  `generate: {status: GATE_FAIL, label: "complete, gate failed, review only",
  quarantine: [...]}`, with each feed's artefact paths under `quarantine/`.
  `tools/iig_diff.py` still scores the quarantined workbook: its build stamp is
  3 folders up, within the 5 it searches. Generating the feed again clears its
  old quarantine. Console: `GATE_FAIL      <feed> — complete, gate failed,
  review only: N file(s) moved to …`.
- **FAIL** (nothing written: a contract mismatch, no feed matching `--feed`):
  emit stages SKIPPED.
- The App's own generate path (`ui/backend/service.py`) does not quarantine yet;
  it can read the same outcome from `CODEGEN_STAGES.json` for CLI runs.

## 0.5.8.post53 — 2026-10-15 (addendum 4: derived values never reach the error line)

Feed slugs, work-dir paths and contract keys are generated, not harvested, so the
leak gate cannot see them. The coordinates tier (`first_error_line`) already
printed none (it is built from vocabulary + integers); post53 makes what it prints
for them useful:
- **Contract mismatch = counts on the first line**, e.g. `contract mismatch,
  feed 1 of 1: 2 tables only in FRD, 1 table only in STTM`. Every resolver
  mismatch item is tagged by kind (`resolver.mismatch_item`; labels in
  `run_errors.MISMATCH_LABELS`). Names count once, so three segments naming one
  table are 1 table. `ContractMismatchError.counts` rides the marker.
  The full message's first line carries the same summary.
- **A feed is `feed N of M`**: the mismatch coordinate now uses the original
  FRD feed object (the gap chain had replaced it, so it read `pair 1 of 1`).
- **A path is `<workdir>/pair_07/…`** (`run_errors.path_hint`: only a harness
  `pair_NN` folder survives), e.g. `contract not found: STTM <workdir>/pair_07/…`.
- Column names were already coordinates (the post52 raise-site audit).

## 0.5.8.post52 — 2026-10-15 (D1 post51 report: two defects + the pydantic addendum)

1. **Error lines: two tiers, coordinates only in the one a report carries.** The
   post51 report's 4 static-denylist hits were all document text inside
   `first_error_line`. `codegen.run_errors.first_error_line(returncode, stderr,
   stdout)` (same STABLE signature) now returns ONLY fixed vocabulary + integers:
   `FAIL            extract-sttm — STTM audit column invalid at STTM sheet 3 row 4
   col 11 [WorkbookParseError]`. New `first_error_line_full` (same signature) is the
   quoted line, for `codegen-outputs/` inside ACFC only. The CLI pairs every `FAIL`
   line with a `CODEGEN-ERROR {json}` marker on stderr (stage, reason code, `Coord`);
   118 raise sites in the STTM parser, FRD extractor, VDD reader, layout and generator
   attach their position via `run_errors.located(exc, Coord(...), reason)` (message
   text unchanged); an uncaught error gets a marker too. The harness phrases
   `contract not found:`, `no resolved feed matches --feed`, `produced no feeds`,
   `under gaps:` survive in the reason phrases. `scripts/run_round.py` prints the
   coordinates line (the quoted one stays in its work dir); `acfc_run.py` keeps both.
   **Harness side:** keep importing `first_error_line` for the report; write
   `first_error_line_full` only under `codegen-outputs/`.
2. **Emit stages SKIPPED, never PASS, after a failed Generate.** Pairs 03 / 04 / 07
   showed DDL / IIG / DML emit PASS with pair_02's exact unpopulated counts. A generate
   run where anything failed (contract mismatch, template gap, gate verdict FAIL, an
   uncaught error) prints `SKIPPED        <ddl_emit|iig_emit|dml_emit> — upstream
   stage generate failed`, deletes every emit artefact a failed feed wrote or rewrote
   (no partial workbook), keeps the exit code, and writes
   `<output root>/CODEGEN_STAGES.json` (`codegen.run_stages`, STABLE: stage statuses
   + the artefacts this run actually wrote, per feed). **Harness side:** read the
   emit-stage statuses and the workbook to count from `CODEGEN_STAGES.json`
   (`run_stages.read_stage_manifest(out_root)`), never from a glob of the output
   folder — it is shared across pairs, which is how pair_02's workbook was counted
   for pairs 03 / 04 / 07.
3. **The pydantic addendum (pair_07's error line was a warning).**
   a. `layout.model_confidence` is `LayoutConfig.placed_confidence` in Python (YAML key
      kept as alias) with `protected_namespaces=()` on the model; the App's
      `FeedRun.model_usage` (an API key, not renamed) gets `protected_namespaces=()`.
      `tests/test_d1_environment.py` fails on any unprotected `model_*` field at any
      pydantic version.
   b. A Python warning BLOCK is skipped whole: the head line, its continuation (blank
      lines inside the message included — pydantic's own message has one), through the
      indented source line; it ends early at a traceback / error / CLI-label / log line.
   c. Per stage, exit-code first: 0 (PASS) and 3 (NEEDS_ANSWERS) return `None` from
      both tiers — stderr is read only for a FAILed stage.
   The D1 pin set (pydantic 2.8.2, openpyxl 3.1.2, jinja2 3.1.6, pyyaml 6.0.1, ruff
   0.17.0, databricks-sdk 0.30.0) is `constraints/acfc_d1.txt` + §0 of
   `docs/acfc/ENVIRONMENT_ACFC.md`; the suite runs in the dev venv AND `.venv-d1`
   before a push. Under openpyxl 3.1.2 the byte-pinned `.xlsx` fixtures are compared
   cell by cell.

## 0.5.8.post51 — 2026-10-15 (D1 post50 follow-ups)

1. **Run errors: exit code first, warnings never the error** (904178e).
   `codegen.run_errors.first_error_line(returncode, stderr, stdout)` — a STABLE API
   for the harness report writer: exit 0 = no error whatever stderr holds; otherwise
   the first `Traceback` / `FAIL` / `ERROR` / `<Name>Error:` line, Python warning
   lines (and the source line under them) skipped. `scripts/run_round.py` and
   `acfc_run.py` use it. The noise is gone at its source: importing `codegen.config`
   printed two pydantic `UserWarning`s (fields named after BaseModel attributes);
   they are `thresholds` / `db_schema` in Python now, the YAML keys unchanged
   (`extractor.discovery.validate`, `dml.schema`). The CLI also ignores pydantic's
   own deprecation category. **Harness side:** import `first_error_line` instead of
   taking the first stderr line; the leak gate's stderr reading wants the same filter.
2. **Environment profiles D1 / A2 / PR** (a859b6e; QA / PROD renamed A2 / PR).
   Resolution: `--environment-file` > `--environment <name>` (else the default) =
   `codegen-state/environments/<name>.yaml` (outside the tracked tree) laid over the
   overlay block > INPUT_NEEDED. A REQUIRED value (`environment_schema.required`:
   storage account, containers) still unset is `QUESTION run.environment.<key>`,
   **exit 3** (was a non-blocking INPUT_NEEDED). The run banner / report header /
   RUN.md read `environment: D1 (complete, from codegen-state/environments/d1.yaml;
   selected)`. The DQ header / trailer location never formats a placeholder storage
   account. App: each profile's values prefilled and editable, required fields
   marked, "Other…" free text kept. **ACFC side:** put the storage account in
   `codegen-state/environments/d1.yaml` (`config/environments/example.yaml` shows
   the shape) — without it every D1 run now exits 3.
3. **Golden alignment, mechanism only** (5515376). The ACFC-side overlay
   `codegen-state/overlays/<profile>.yaml` (outside the tracked tree) is applied
   right after `acfc_env.yaml`; notebook names / paths / versions, the email status
   default + per-feed status sets, and per-feed SRC_FILE_NAME styles are set there
   (`docs/acfc/OVERLAY_FIELDS.md`; synthetic `config/overlays/example.yaml`). New:
   `notebook_path_prefix` (`/Workspace` in `acfc_env.yaml`), `email_status_default`,
   `feed_overrides.<feed_id>.{email_statuses, src_file_name}`, the `prefix_middle`
   wildcard style. The "dropped" stg_to_std notebook row was `iig_diff` giving both
   notebook rows no flow (the corpus `PROCESS_NAME` shapes matched no rule): two flow
   rules in `tools/iig_keys.yaml`. SRC_COLUMNS left naming and PIPELINE_DESCRIPTION
   row counts are open convention questions (`docs/acfc/OPEN_QUESTIONS.md`), untouched.
4. **Pre-push scrub gate at home** (f6d0412). `tests/test_tracked_scrub.py` scans
   every tracked file under `config/` + `docs/acfc/` and fails only on a (file, hash)
   pair not in the `docs/acfc/LEAK_LEDGER.md` baseline (18 rows = the 68 known hits,
   hashes only; regenerate with `scripts/scrub_check.py --rebaseline`).
   `codegen.term_hash.term_sha256` (strip, casefold, NFC, sha256) is the shared hash.
5. **`tools/hit_lookup.py`** (b95f39c): matches the gate's per-hit JSONL hash
   records against a local, gitignored candidates file — classification at home
   without a term entering git.
