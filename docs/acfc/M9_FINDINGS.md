# M9 — the pair-1 findings of 2026-09-21, and what was done with the hotfix

Scrubbed record (structure only; no client table, schema, file, LOB or sheet
name, no workspace path). Sources: the two captures a Genie Code session left on
the remote branch `acfc-hotfix-1` — `docs/acfc/HANDOVER_GENIE.md` (diagnosis,
error sequence, hotfix diffs) and `docs/acfc/PAIR1_HEADERS.md` (rows 14–15 of
the pair-1 mapping sheet cell by cell, the FRD's Descriptive Metadata table
label by label). **That branch is NOT merged** and must not be: its
`config/config.yaml` carries workspace-specific values (a user's workspace
folder paths, workspace catalogs, the live layout provider switched on) and its
two documents quote real client identifiers. M9 (v0.5.1-acfc) re-derives the
fixes on `staging` from what the captures establish.

## 1. What the captures establish about the real pair 1

**STTM mapping sheet** (the fixture `fixtures/acfc_shapes/sttm/pair_1_family_a.xlsx`
now has this geometry; values stay the aliased golden's):

| Where | What |
| --- | --- |
| r1–r10, A:B | Ten meta rows: `File Names`, `File Name Example`, `Frequency`, `File Format (text, csv)`, `File Delimiter`, `Last Update Date`, `Version`, `LOB`, `Target table Name Desc`, `Feed Type`. Names / example / frequency read `TBD`; the format reads `.dat`; delimiter, date, version, feed type are empty. No `Load Strategy` / `Notes` row (the shapes document lists r11–r12; the real sheet has none). |
| r14 | Four merged band labels: `Source Data` A14:I14, `Data Rules and Primary Keys` K14:P14, `Staging Layer Table` R14:W14, `Standard Layer Table` Y14:AD14. |
| r15 | 27 header texts over 30 columns — A–I source (`S.No` … `Description`), K–P rules (`Data Definition` … `Load Rules`), R–W and Y–AD the layer headers `Workspace`, `Target Catalog`, `Target Schema Name in DL`, `Target Table Name in DL`, `Target_Column_Name_in_DL`, `Target Data Type in DL`. **J, Q and X are empty** in both rows. |
| data rows | Schema and table are constants repeated on EVERY data row of both bands (not in a meta row, not in a merged cell). The detail block is introduced by a banner reading `Details` (plural). One row's stage column reads `Do Not Map` with no data type; its field-name cell carries a line break. |

**FRD** (fixture `fixtures/acfc_shapes/frd/f1_pair_1.docx`):

| Cell | What |
| --- | --- |
| Structural · `Target Table Name` | An inline layer block — `Staging Layer:` / `Table: <name>` / `Standard Layer:` / `Table: <name>`. The reader used to split it on newlines into four "table names". |
| Structural · `Target Catalog and Schema` | States no schema and no catalog. |
| Descriptive · `Object Name` | The label IS `Object Name`; the cell lists the inbound FILES, one `<line of business>: <file name pattern>` line each. It names no feed — the reader refused it as multi-line, skipped the `Name` fallback and the feed came out "unnamed". |
| Descriptive · `Name` | A sentence about the requirement ("Descriptive Metadata for the ingestion of …"), not a feed name. |
| Descriptive · `Tags/Keywords` | `Domain: …` / `Subdomain: …` lines. |
| Descriptive · `Frequency` | A compound schedule sentence (a time per line of business). **Not modelled in the fixture** — open item 3 below. |

**Why the run could not be repaired on site.** (1) The sheet's `… in DL` headers
were outside the synonym tables; (2) a model answer failed schema validation
and the report kept only "10 validation errors" — the reasons were lost;
(3) the profile that did get cached had NO schema role, and the schema was not
a required role, so nothing asked; (4) every re-run hit that cached profile —
no way to bypass it, and deleting the file was blocked; (5) an answers-file
entry for the schema was refused ("matches no open question").

## 2. What M9 changed

| Finding | Change | Test |
| --- | --- | --- |
| `… in DL` headers, `Details`, `Format` | Synonyms (`extractor.discovery.roles.target`, `segment_synonyms.Detail`, `roles.source.source_type`). `Format` is not in the brief's list: without it the real sheet's source types read `unstated` and nothing asks (the role is optional), so "answers file not needed" could not hold. | `test_m9_acfc_findings.py`, `test_layout_discovery.py` |
| Schema missing, nothing asked | `schema` is a REQUIRED role in both target bands (catalog optional); a missing required role is always in the question list, whoever produced the profile (`_list_missing_required`). | `test_a_missing_required_role_is_always_a_question` |
| Answer refused | An answer may set ANY role; it overrides a synonym / model / cache placement, the displaced role gives the column up, all `source=user`. | `test_an_answer_may_set_a_role_no_question_asks_for_and_it_wins` |
| Stale cache | Runtime entries keyed by the vocabulary hash; a profile lacking a required role is never trusted and never written; `codegen layout --refresh`, the UI's "Re-resolve layout" (checkbox before a run, button in the dialog), the notebook's `refresh_layout` widget bypass and overwrite (tombstone when incomplete). | `test_a_stale_cached_profile_lacking_schema_is_ignored_and_re_resolved`, `test_cache_key_includes_the_vocabulary`, `test_refresh_bypasses_and_overwrites_the_runtime_entry`, `test_demo_ui.py` |
| Rejection reasons lost | `<runtime cache>/rejections/<fingerprint>.json` — every schema error (type, location, message) and validator rejection; invented keys masked, no input value kept. | `test_rejection_log_is_written_in_full_and_carries_no_model_string` |
| Band constants | `_band_constant`: the first non-empty cell when the column holds ONE value (every row, or a merged anchor), the dominant value when it holds several (one table per segment) — with the cell as provenance in the contract notes. | `test_band_constant_reads_a_merged_anchor_and_keeps_the_dominant_of_many` |
| Empty schema | NOT tolerated. Chain: STTM band → FRD → `conventions.default_schema[layer]` (flag `sttm_unstated:<layer>.schema source_used:…`), then the hard stop. | `test_missing_schema_is_a_hard_stop_after_the_fallback_chain` |
| `Do Not Map` | `extractor.unmapped_markers`; the field is left out of both layers, flag `field_unmapped:<field>` citing the cell (`SttmFeed.extraction_flags` → the gate). | `test_real_shape_fixture_extracts_…`, `test_unmapped_markers_are_config` |
| `TBD` meta values | `extractor.discovery.meta_blank_values`: read as blank, so the chain looks further. A format cell that is only an extension (`.dat`) never "disagrees" with a stated format. | `test_banner_rows_and_placeholders_…`, `test_frd_gapfill.py` |
| Inline layer block | `parse_layer_blocks` (`extractor.frd.layer_block_*`): per layer into table / schema / catalog; flag `frd_layer_block`; no line is ever a table name. | `test_frd_docx.py` |
| Unnamed feed | Flag `frd_feed_name_unstated` (never a silent default). A `<label>: <file>` Object Name cell = the file patterns (`file_pattern_from_object_name`). The layout stage names the feed after the STTM stage band (`frd_unstated:feeds[0].feed_name source_used:STTM stage band`); `codegen layout --frd-contract-out` writes that contract for the CLI path. | `test_frd_docx.py`, `test_cli_chain_…` |
| Literal table match | `normalize_table_name`: case, quotes / backticks / brackets, qualified vs bare; a non-literal match is a flag naming the qualified side. FRD schema / catalog unstated → filled from the STTM bands, `frd_unstated:<layer>_target.schema` / `.catalog`. | `test_contract_matcher_reports_which_side_was_qualified` |
| Found on the way | `codegen generate` parsed `--vdd` / `--profile` / `--iig-template` / `--playbook-template` and dropped them (the on-site run had to edit `config.yaml` to get `acfc_prx`, and its VDD never reached the gate). Forwarded now. | `test_cli_chain_…` |

Acceptance (M9.4, `tests/test_m4_acceptance.py`): the real-shape pair, no answers
file, zero model calls → `acfc_prx` / `iig_v2` → DDL byte-identical to the aliased
golden, IIG sheets / headers / row counts / pinned cells as in M4, verdict
PASS_WITH_FLAGS with the flag list pinned by kind and count.

## 3. The hotfix branch, commit by commit

| Commit · file | Verdict | What happened to it |
| --- | --- | --- |
| `3ee696b` · `extract/generic.py` — `_band_constant` replaces `_dominant` | **Reworked** | Kept the idea (first non-empty cell, merged anchors); it now returns the cell as provenance and keeps the dominant value for a column that is not a constant — the blanket swap changed the stage table of every multi-table sheet (pair 8). |
| `3ee696b` · `extract/generic.py` — schema gate decoupled, `TableRef(schema=stage_schema or "")` | **Dropped** | An empty schema must never reach a contract. Replaced by the STTM → FRD → config chain and the hard stop. |
| `3ee696b` · `layout/resolve.py` — `_log_layout_rejection` | **Reworked** | It opened the storage backend from inside the resolver (the storage seam is an EDGE the callers own), only when `CODEGEN_STORAGE_STATE` was set, swallowed every exception, covered schema errors only and echoed error locations verbatim (model-made keys). Now: written into the runtime cache directory the caller already owns (the existing push carries it), validator rejections too, invented keys masked. |
| `3ee696b` · `config/config.yaml` — the four `… in dl` synonyms | **Kept** | As written. |
| `3ee696b` · `config/config.yaml` — storage URIs, catalogs / volumes, `layout.provider: live` + endpoint, `conventions.profile: acfc_prx`, `default_catalog`, `metadata.template: iig_v2`, `playbook.template: main_single`, the two pairing maps emptied | **Dropped** | Workspace setup: it belongs in an overlay / env (`docs/ACFC_DEPLOY.md` §2), never in the tracked file. The conventions are notebook widgets passed to `generate` now. |
| `3ee696b` · `acfc_run.py` — restructured into per-pair cells, batch run for pairs 2–10, golden diff cell | **Dropped** | Session scaffolding around the unfixed bugs (and uncommitted edits on top). The tracked notebook gained three things instead: the FRD contract from the layout step, conventions widgets, `refresh_layout`. |
| `d889c51` · `config/config.yaml` — `details` | **Kept** | As written. |
| `d889c51` · `extract/generic.py` — `_DNM` skip set, a note | **Reworked** | The markers are config (`extractor.unmapped_markers`), and the skip is a gate FLAG citing the cell — a note alone is invisible to the reviewer. |
| `bbb491d`, `8377954` · the two documents | **Not brought over** | They quote client identifiers; this file is their scrubbed record. |

## 5. v0.5.2 — what the first real run of v0.5.1 showed

Sources: `docs/acfc/PAIR1_REAL_RUN.md` and `docs/acfc/RUN_v051_pair1.md` on the
remote branch `acfc-runs` (placeholders throughout; not merged — run records).

| Finding | Change |
| --- | --- |
| The real Object Name cell is STANZAS — a `<line of business>:` line, then the file name pattern on the NEXT line (three of them). v0.5.1 only read `<label>: <file>` on one line, so the FRD yielded no pattern. | `parse_object_name_block`: a multi-line block or a nested label \| value table is read per line / row — feed name from a feed-name label's value, files from a `File Name`-type label or any file-like value under another label; a flattened table (no labels) keeps the M7 refusal. The fixture cell is the stanza shape now. Two further shapes (labelled lines, a two-row table) are supported and tested as UNVERIFIED. |
| The mapping sheet HAS rows 11–12 (`Load Strategy` = `Append`, `Notes` empty); the first capture stopped at r10. No File Details sheet. | Fixture corrected (r1–r12). The layer-less `Append` raises no question while the FRD states both strategies. |
| `extract-sttm` hard-failed: "neither the FRD nor the workbook names a file pattern" — the VDD FILES sheet held one (a `*`-prefixed glob), but `extract-sttm` never reads the VDD. | The chain FRD → STTM → VDD FILES → `feeds[0].file_patterns` question; `SourceFile.name_pattern` may be null at extract time; the hard stop remains only in `generate`. |
| `layout --refresh --answers` printed `source=cache cache_hit=True` for STTM and FRD. | The answers pass continues from the refresh pass (`prior=`). |
| `generate` exited 1 with `ruff=FAIL`; the run note read it as "ruff on the mock sketches". | Sketches are never linted (pinned by a test). The exit code already followed the verdict — the verdict WAS `FAIL`, on the ruff check. What ruff failed on is not recorded; the check now tells findings from "ruff did not run" (a flag, `check_not_run:ruff`, not a FAIL) and the console prints the failed check's first lines, so the next run says which it was. |

Not changed, worth knowing: with `File Names` = `TBD` the STTM offers the VDD
pairing no content signal (`codegen pair` asks for the VDD) — the FRD's Object
Name files could serve as that signal.

## 6. v0.5.3 — the fixed-width width chain

Source: `docs/acfc/RUN_v052_pair1.md` on `acfc-runs`. With v0.5.2 the real pair
got through layout (0 provider calls), extract-sttm (70 fields, six
`field_unmapped`) and extract-vdd, then `generate` stopped BEFORE the gate:
"fixed-width feed: field … has no start/length (start='220', length='10,2')" —
six Detail amount fields, starts 220 / 246 / 272 / 298 / 324 / 350, whose Length
cell reads `10,2`.

| Rule | Where |
| --- | --- |
| A Length cell is a byte width only when it is an integer. `10,2` / `10.2` / `Decimal(10,2)` is a PRECISION: kept (`SttmField.source_precision`, flag `length_is_precision:<field>` citing the cell), never turned into a width — 10 digits with 2 decimals may occupy 10 to 13 bytes. | `codegen/resolve/widths.py` |
| Chain: STTM integer length → STTM end − start + 1 (`width_from_sttm_span`) → VDD end − start + 1, matched by normalized field name + segment (`width_from_vdd`) → the question `feeds[i].fields[<name>].width` (`width_from_user`). | extractor (links 1–2), contract resolver (3–4), layout stage (asks) |
| One resolved value, three consumers: the fixed-width template's positions, the `ADLS_FIXED_WIDTH_HANDLER` `LEN` cell (verbatim while the length is an integer), the VDD cross-check (STTM width vs VDD width). | `emit/context.py`, `metadata_template.py`, `gate/vdd_check.py` |
| Unresolved = `generate` stops, naming the question; `extract-sttm` never stops on it. `Do Not Map` rows are never asked about. | |

Fixture: the six fields are a test VARIANT of the pair-1 documents
(`sttm.build_pair1(amounts=True)` / `vdd.build_vdd_pair1(amounts=True)`), not
part of the tracked acceptance pair — the golden DDL has no such columns, and
the acceptance stays byte-identical. **UNVERIFIED:** the VDD span of these
fields (13 bytes in the variant) — capture the real dictionary's rows.

## 7. v0.5.5 — the App hang (APP_CHOOSER_BUG)

Source: `docs/acfc/APP_CHOOSER_BUG.md` on `acfc-runs` (a pre-0.5.4 build; it
quotes real file names, so it is NOT copied here). Recorded: both list
endpoints answered; the FRD list carried an upstream warehouse-permission
error; `POST /api/demo/workbook` for the pair-1 STTM hit the client's 180 s
timeout; afterwards every endpoint timed out (`/api/demo/status`, `/api/feeds`)
until a restart, with the App still reported RUNNING and no logs obtainable.

What the code shows: the request did not hold the runner lock across I/O, and
it did not call the warehouse. It did, on that build, auto-pair the VDD by
downloading and parsing EVERY other workbook of the input folders in the App's
own process — client sheets that declare ~1,048,000-row dimensions among them.
v0.5.4 moved that to a background thread, which can only be abandoned, not
stopped. The fix covers the doc's hypotheses and the finding alike:

| Rule | Where |
| --- | --- |
| The STTM selection is a JOB: 202 at once; locate / download / start parser / classify / pair FRD / pair VDD / record each bounded; the outcome on `status.selection_job`; nothing selected until all succeeded. | `ui/backend/demo.py` (`start_selection`, `_run_selection`, `_step`) |
| Documents are parsed in a killable child process; late = killed and restarted. | `codegen/layout/docworker.py`, `ui/backend/docindex.py` (`ParserProcess`) |
| Pairing never opens a document in-process: indexed facts, else the parser within the step's budget, else the name alone. | `DemoRunner._plan_pair`, `pairing.empty_facts` |
| Upstream (warehouse) lookups off by default; on = background refresh with a hard timeout, never awaited by a request. | `upstream:` config, `DemoRunner.upstream_snapshot` |
| Remote listings bounded; the last known listing served. | `storage/catalog.py` |
| One selection record for the list and the status. | `DemoRunner.selection()` |

Regression tests: `tests/test_m93_app_hang.py` — a download and an upstream
call that never return (POST answers in < 1 s, `/api/feeds` answers, the status
shows the timed-out step), a parser that never answers (killed), upstream off
by default and never called, one selection record, a Clear superseding a job.

## 4. Open items

1. **The two documents on the remote branch are not scrubbed** (client table /
   schema / file names, LOB codes, a ticket number), and that branch's
   `config.yaml` holds a user's workspace paths. Decide whether the branch stays.
2. The first real run of v0.5.1 inside ACFC: pull `staging`, redeploy (marker
   0.5.1), pair 1 with no answers file. Expected: layout `source=synonyms`, zero
   provider calls, no questions; the flag list of §2.
3. The real `Frequency` cell is a compound sentence; the reader will refuse it
   (multi-line) and the chain goes STTM (`TBD` → blank) → VDD cadence. If the
   VDD lists several cadences that is a `choice` question — answer it under
   `gaps:`.
4. The derived feed id is the stage TABLE name, so the load-pattern FAQ file is
   `<stage table>.faq.yaml` (the fixture's was renamed accordingly).
5. The real `Format` column's values are unknown (type words? COBOL pictures?
   date masks?). As a synonym it is read verbatim into `source_datatype`; the
   VDD cross-check will say so if it disagrees.
