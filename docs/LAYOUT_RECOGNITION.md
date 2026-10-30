# Layout recognition — a model decides structure, code copies values

Added 2026-09-18 (M2.5 of the ACFC generalization build). Modules:
`src/codegen/layout/` (`profile`, `frd_profile`, `fingerprint`, `discover`,
`validate`, `model`, `resolve`); readers in `src/codegen/extract/`
(`workbook`, `segmented`, `generic`, `frd_docx`).

## The principle, enforced by code

No string produced by a model is ever written into a contract, a DDL or an
IIG cell. The model emits a **layout profile** — where things are: sheet
kinds, header and band rows, band spans, `role → column` for a workbook;
`field → (table, row, label cell)` for a document. The deterministic
extractor then copies cell text through that profile and stamps every field
with its provenance (sheet/row/col, or table/row/col + the label seen) and
the source that placed the role (`synonyms | model | user | cache`).

The guarantee is structural, not a convention:

- the profile schema carries integers, sheet names that must exist, role
  names from a fixed enum and literal kinds — never a cell value;
- `resolve` merges out of a model answer ONLY the column numbers of roles
  the synonyms left unresolved, onto columns no other role claims; a role
  name outside the enum, a note, a label string in the answer is dropped;
- every merged claim is validated against the workbook before use;
- a canary test (`tests/test_layout_resolution.py`) places a marker in a
  mock answer's notes and role names and asserts it reaches no artefact.

## What the model sees

Only the **fingerprint material** (`layout/fingerprint.py`): sheet names,
merged ranges, row/column counts and the cells of each sheet's header
region — meta rows, the band row and the header row, bounded at the header
row by a cheap structural scan (a data row never enters). When the region
cannot be bounded (no row of 3+ cells within 25 rows: a two-column lookup,
valid-values or member list) it is capped at 25 rows and marked `capped`. The
fingerprint hashes that capped region, but the MODEL gets only the sheet's
summary line, `(capped, cells withheld)`, because those rows may be data
(`fingerprint.model_region`, post111). A role on such a sheet is placed by
synonyms or asked of the user, never by the model. For every bounded sheet the
cache key and the prompt material are the same rendering. Two tests place a
canary in a data row (a mapping sheet, and a capped lookup sheet) and check the
recorded provider request body.

For a document: table titles and the label texts of each table (the
section-prefix column and the label column), never a value cell.

**FRD placements by the model** (P1-3, 2026-10-30; red team LM-3): a model claim
is applied only when its label cell (or the inline label it claims) is one of
the field's spellings in `extractor.frd.labels` / `fixed_rows`, read the way the
synonyms read it (`frd_docx._paths_for`), in the section its table really is, and
on a row the synonyms did not bind to another field. Anything else is a PROPOSAL:
the field stays open (a question for a person, the model's row pre-selected with
`suggested_reason`), the rejection names coordinates only.

**Size caps** (P1-7, 2026-10-30; red team LM-5: a 296 KB STTM made a 12.2 MB
request). `layout.max_cell_chars` clips every header-region cell, FRD label
line and partial-profile string in the model's copy (`fingerprint.clip_text`,
`... [clipped, N chars]`); cells go only for the sheets that still have an
open role, at most `layout.max_sheets_sent` of them (the rest: summary line,
`(cells withheld)`); a request whose JSON is over `layout.max_prompt_chars` is
refused before the provider is called (rejection `layout.request_too_large`,
integers only) and so never retried - its roles stay questions. The caps live
under `layout:`, which the vocabulary hash does not read, and the fingerprint
still hashes the full region: no cache key moves.

## Resolution order (`layout/resolve.py`)

1. **Cache** — `layout.cache_dirs` (repo, `fixtures/layout_profiles/`) then
   the runtime cache (`layout.runtime_cache_dir`), keyed by fingerprint; for
   a pair, the pair fingerprint (`sha256(sttm_fp:frd_fp)`) first. Hit →
   `source: cache`, zero model calls. **M9.1:** a RUNTIME entry is also keyed
   by the **vocabulary hash** (`vocabulary_hash`: the whole `extractor:`
   section — synonym tables, band tokens, thresholds — plus the role
   vocabulary and the required roles); an entry written under other tables,
   or before M9 (no key), is stale and ignored. A cached profile that lacks a
   REQUIRED role is never trusted, from either cache — it is re-resolved and
   the report says why — and such a profile is never written. **Refresh**
   (`codegen layout --refresh`, the UI's "Re-resolve layout") bypasses every
   cache and OVERWRITES the runtime entries: a complete result replaces them
   (even a synonyms-only one), an incomplete one tombstones them
   (`"invalidated": true` — the storage roles have no delete).
2. **Synonyms** — the deterministic discovery (`discover.py`, three
   strategies: `mapping_prefix`, `segmented_family`, `content`;
   `frd_docx.discover_frd` for documents). Every required role resolved →
   done, `source: synonyms`, zero model calls.
3. **Model** — one call per new document with the unresolved remainder,
   through the same provider seam as Layer 2 (`layout/model.py`: mock by
   default, Databricks FMAPI serving the configured Claude model, or the
   Anthropic API; no sampling parameters). Mock answers come from
   `fixtures/layout_profiles/mock/` then the cache directories, by
   fingerprint.
4. **Validate** (`layout/validate.py`, thresholds in
   `extractor.discovery.validate`) — header row exists and every claimed
   role column has a non-empty header cell; band spans carry their layer
   token and do not overlap; stage/standard bands resolve at least table +
   column (the REQUIRED roles are schema, table, column and data type in both
   target bands since M9.1 — the catalog stays optional, its chain ends in a
   config default); one role per column; content plausibility under the header
   (length/start/end ≥ 80 % integer-like, source/target types ≥ 80 %
   type-token-like, yes/no roles ≥ 80 % Y/N-like or blank, field name
   ≥ 90 % non-empty); meta-row labels match the claimed key's synonyms and
   the value sits to the right; auxiliary kinds carry their header
   signature. A failed check drops that claim to unresolved with a reason
   that reaches the report and the gate. The report line of a model answer
   that fails the SCHEMA keeps one line ("10 validation errors …"); the full
   list — type, location, message per error, plus every validator rejection
   — is written to `<runtime cache>/rejections/<fingerprint>.json` (M9.1).
   A location key outside the profile schema / role vocabulary is written
   `<key>` and no input value is kept: nothing the model invented is stored.
5. **User** — what remains comes back as questions (document, sheet, layer,
   role, the header row rendered, candidate columns); a missing REQUIRED role
   is always among them, whoever produced the profile. An answer may set ANY
   role, open or not (M9.1): it replaces a synonym / model / cache placement
   of that role, a role that held the answered column gives it up (a
   required one is asked again), and every displacement is a profile note.
   The CLI resolves twice when an answers file is given — once to learn the
   questions, once with the answers; the second pass CONTINUES from the first
   (`prior=`): no cache read, no second model call, true role sources (a
   `--refresh` used to come back `source=cache`). The CLI prints them
   (`codegen layout --require-complete` exits non-zero); the UI pauses the
   run in `needs_layout` and shows one dialog grouped by document; answers
   merge with `source: user`, confidence 1.0, and the completed profile is
   saved to the runtime cache.
6. A profile with unresolved roles still extracts: those values read empty
   and the gate flags `layout_unresolved:…`.

## Band location by label group, layer by evidence (Chunk A, 2026-10-09)

A target band is located by its **label group** — a run of `roles.target`
headers placing at least `layer_evidence.group_min_location_roles` (3) of
catalog / schema / table / column / data type — wherever it sits in the
header row: any order, any offset, any count of bands, never a fixed column
(`discover.label_groups`); column or data type must be among them (a Table
Details sheet's Catalog | Schema | Table Name is not a band). Order INSIDE a
band is free ("TableName | ColumnName | Schema | DataType" is one band). A run
closes after `group_max_gap` other cells; a REPEATED role splits it at the
location-rank drop between the two occurrences that restarts lowest ("Data
Type | Schema | TableName | ColumnName | DataType …": the source's type stays
with the source), else just before the repeat; a rules band's Primary Key
beside the stage band is never the stage band's first role.

A band's **layer** comes only from evidence, first that names exactly one
layer wins (`extractor.discovery.layer_evidence`):

| Evidence (`BandProfile.layer_evidence`) | Read from |
| --- | --- |
| `answer` | `<sheet>/band[<n>]/layer` answered source / stage / standard |
| `title` | the band title row over the group's location columns (`titles` words, or a `band_tokens` token) |
| `header` | a whole word of the band's own header texts (`header_words`; "in DL" / "DLK" are OFF — pair 1 writes "… in DL" in both bands) |
| `catalog_value` | the band's Catalog values (`catalog_words`: PR_DLK → stage, PR_STD → standard) |
| `schema_value` | the band's Schema values (`schema_prefixes`: stg_ → stage) |
| `elimination` | stage AND standard each claimed by a band with its OWN (non-elimination) evidence, EXACTLY ONE band left over, and that band LEFT of both target bands (the source precedes the targets in every real layout): it is the source, said in a layout `NOTE <sheet>/band[<n>]/layer — … source - layer by elimination …` line. A leftover right of a target band, or more than one, stays the band question (owner rule, 2026-10-09). Also never when source is already claimed (another band, a "Source" title elsewhere, a field-name column outside the bands), never for a band whose own evidence lost a same-layer conflict, and never trusted from a cache |

**Column order is never evidence.** A band nothing names, or two bands naming
the same target layer (unless one was answered), is the question
`UNRESOLVED <sheet>/band[<n>]/layer — <what was seen>; answer under answers:
with source | stage | standard` (`n` = the band's position among the sheet's
label groups), and the sheet's feed is held back (`extract-sttm`: NEEDS_ANSWERS,
the same line) until it is answered — in answers.yaml:

```yaml
answers:
  - sheet: "Mapping"
    layer: band[2]
    role: layer
    value: stage          # source | stage | standard
```

(the App: `{"sttm": {"Mapping/band[2]/layer": "stage"}}`). A band answered
`source` is the source band (its Schema / TableName / ColumnName / DataType
read as the source's schema / table / field name / type). A model never
places a layer: band questions are not in its request.

**What did not change.** Pass 1 is the reading of every workbook before
2026-10-09 (a band row naming stage AND standard, or layer prefixes in the
header texts). When its bands agree with the label groups and their evidence,
the profile is exactly the one read before — every pinned profile in
`fixtures/layout_profiles/` and `tests/test_layout_discovery.py` is
byte-identical, and such bands carry no `layer_evidence` (absent from the
JSON). The groups rebuild the bands only when the band row contradicts them
(a title merged over part of a band). Pass 2 — header-row groups with no such
band row (one band only, another title wording, no title row) — runs only
when pass 1 finds no mapping sheet in the workbook: a reference sheet beside
real mapping sheets ("STG - Dest 1 | STD - Dest2", pair 4) is never read as a
feed; the diagnostics name it. A pass-2 header row needs two or more label
groups, or one plus a field-name header outside it (an auxiliary sheet with one
table-shaped group is not a mapping sheet); the row above it is its title row
only when sparse, short, not a meta label ("Notes | …") and a cell names a
layer or sits over a group. **`MAPPING-` sheets are read by the general reader first** (addendum,
2026-10-09; `discover._mapping_general_first`): band row / label groups,
layers by evidence, the band question, and family B's own source vocabulary
on those sheets (`extractor.header_synonyms` — "Mandatory" is `mandatory`
there, `required` on the content families); the per-row Recycle Flag column by
its header PREFIX everywhere. The legacy reader is the fallback when the
general reader finds nothing, and the reference it is proven equal to: on
every `MAPPING-` workbook of the fixture set (pairs 2 and 11, the CV golden,
the tests' minimal and SD-shaped sheets — and the real SD workbook) both place
the same roles in the same columns (`mapping_differences` is empty), so
`discover` returns the legacy profile byte for byte and every contract stays
byte-identical. Where they disagree, or the legacy reader refuses (another
title wording, titles in row 2, an unknown header), the general reader's
bands are used, each difference a diagnostic; the legacy extractor still
reads the rows when every column it requires is placed (data from the
profile's header row + 1), else the generic extractor does (strategy
`content`, which also holds a sheet with an open band back). The flat
`parse_workbook` API is the legacy reader only (its errors stand), and the
segmented dialect on a `MAPPING-` sheet keeps its explicit
`SegmentedWorkbookError`.

**Caches.** A layer read from catalog / schema VALUES is never trusted from a
cache — the fingerprint hashes headers, not values: on every cache hit (the
document entry AND the pair entry) `stale_value_evidence` re-runs the value
chain (Catalog values, then Schema values) on the workbook in hand, and a
cached layer or evidence kind the values no longer support is re-resolved (the
report says why). **P1-2 (2026-10-30, red team LM-2):** nor is a placement the
model or a person made: on every hit (document entry, pair entry, VDD, FRD) the
synonyms are re-run on the document in hand, every cached role they do not place
the same way is re-validated (`validate_profile` / `_validate_frd`, header +
plausibility, the checks a fresh claim meets), and one rejection makes the entry
stale (`cached profile: N placement(s) ... do not validate`, coordinates only).
An entry records each role's REAL provenance (`model` / `synonyms` / `user`,
never `cache`; `DocumentResolution.placed_by` / `placed()`), and a model-placed
role stays `model` through a hit, so the extractor can flag it. Knob
`layout.cache_model_placements` (default true = cached as before): false keeps a
profile with an unanswered model placement out of the cache (the next run asks
the model again). A band-layer question is never put to the advice model.
**answers.yaml** applies its band layers FIRST (`band_layer_answers`), so a
column entry for a band that exists only once its layer is answered
(`{sheet, layer: standard, role: table, column: …}`) finds that band.
Adding `layer_evidence` to `extractor:` changed the vocabulary hash: every
runtime cache entry written before re-resolves once.

**Classification.** A workbook is an STTM only when a band carries evidence of
a TARGET layer; target-shaped columns nothing names (a dictionary or an IIG
sheet looks the same) classify as `unclassified` with a reason starting
`confirm:` — never silently an STTM; a person can still pick it as the STTM
and answer the band questions.

Tests: `tests/test_band_detection.py` (shapes: `tests/acfc_shapes/bands.py`).

## Candidate mapping sheets (Chunk B, 2026-10-09, the cold drill)

Pass 3 — only when passes 1 and 2 find NO mapping sheet in the workbook (so
no pinned profile moves): a sheet whose header row carries at least
`layer_evidence.candidate_min_header_cells` (8) text cells over data is a
CANDIDATE mapping sheet when its bands are marked by structure —

- a band title row of two or more spans over the header row (each span a
  band: a `source` / `rules` title is that band, any other span a target
  band — "Raw Zone", "Curated Zone"), else
- runs of at least `candidate_min_run` (3) adjacent headers sharing their
  first word ("Landing Catalog | Landing Schema | …", "Curated … Nm"): each
  run one band; the shared word is the band's QUALIFIER — it names the band,
  the rest of a header names the role ("Landing Schema" -> `schema`).

A target band's layer comes from evidence only, as in Chunk A (an answer, a
title word, a qualifier / header word, Catalog values, Schema values); a band
nothing names is `UNRESOLVED <sheet>/band[<n>]/layer` (n = the candidate target
bands left to right). Columns left of the first target band are the source
band, the rest rules. Every REQUIRED role no synonym places is listed
unresolved — the layout model places it, or the person (`answers:`); a
candidate is never refused as "no mapping sheets found". The sheet's first
note starts `no mapping sheet by band row or label group`
(`discover.CANDIDATE_SHEET_NOTE`): the classifier never calls a workbook an
STTM on candidates alone (an IIG or dictionary sheet — `SRC_… / TGT_…` — has
the same shape): `unclassified`, reason starting `confirm:`.

A document no reader can open at all (an FRD with neither F1 nor F2 tables, an
STTM with no candidate) is a `FAIL` line naming the document and the remedy —
never a traceback. An FRD of paragraphs only (no table) reads as the `prose`
family: no field is placed, every required one is the gap chain's or a
`QUESTION`. F1 section tables may carry a reference column (`DM |
Descriptive Metadata` over `DM-1 | Name | …`).

Tests: `tests/test_cold_pairs.py` (the six cold pairs, the chain before and
after `answers.yaml`), `tests/test_cold_drill_fixes.py`.

## Pair-level resolution and cross-checks

`resolve_pair` resolves the STTM and the FRD (a `.docx` through its own
profile; a `.contract.json` as loaded facts) together; unresolved roles of
both documents form one question list. Before returning it runs
cross-document checks that adjust confidence and raise flags, never values:

- the FRD feed / object name should appear in the STTM meta rows or
  file-details cells (normalized, stem match);
- the FRD target catalog/schema should match the dominant value of the
  STTM stage / standard schema and catalog columns;
- the FRD file format / delimiter / frequency should agree with the STTM
  meta rows and, when a VDD is given, its `FILES` sheet.

Agreement adds `layout.crosscheck_bonus` to the involved confidences
(capped at 1.0); disagreement is a gate flag `layout_crosscheck:<name>`
citing both cells. A completed pair is cached under its pair fingerprint.

**Model-placed identifiers** (P1-1, 2026-10-30; red team LM-1: header text
steered the model into swapping the stage catalog and schema). (1) A catalog /
schema column the MODEL placed is judged by its values through the catalog-value
chain (`layer_evidence.catalog_words`, `discover.value_layers`): a catalog's
values read as catalogs, a schema's do not (`validate._identifier_values`, counts
only). (2) The cross-check `<layer>_identifier_swap` flags an STTM catalog equal
to the FRD's schema (or the reverse). (3) A catalog / schema the model placed that
a cross-check contradicts is NOT applied: it goes back to the person as a
question (`_reopen_model_identifiers`); a synonym or a person's placement keeps
the flag only. (4) Every identifier column the model placed (catalog, schema,
table, column, target_type) is a feed flag `layout_model_placed:<sheet>/<layer>/
<role>` (`extract.extractor.model_placed_flags`, also after a cache hit), and the
flags named by `iig_review.review_flag_prefixes` (that one, `frd_crosscheck:`,
`layout_crosscheck:`) are one summary row each in the review copy (per feed and
combined) and a "Check before approving" section in the combined LOG.md.

### The file of each feed when one FRD block splits (2026-10-12)

When one FRD block describes several STTM mapping sheets,
`split_frd_feeds_by_sttm` gives each derived feed its file. The candidates are
the files the documents list (FRD "Target Table Name" entries, FILE_DETAILS
rows, the meta "File Names" row, and the FRD's own patterns). In order:

1. **an answer** (`gaps: feeds[i].file_name_patterns`) wins;
2. **a unique name match** — the table and the file are each other's only
   token match (tokens every table shares, e.g. `risk`, carry nothing);
3. **by elimination** — exactly ONE table and ONE file are left after the
   name matches: that file is the table's value, flagged
   `frd_unstated:feeds[i].file_name_patterns … (by elimination: …)` and printed
   by `layout` as a `NOTE` line, never a `QUESTION` (owner decision: fewer
   questions; the elimination has to be strictly unique);
4. otherwise **a question** — `QUESTION feeds[i].file_name_patterns` with the
   candidate list (`layout --require-complete` exits 3). The feed owns NO
   pattern meanwhile: never the block's shared list (the 1faa83d regression,
   where an unpaired feed inherited every file and extract failed on "N
   FILE_DETAILS rows match"), and the general STTM reader holds it back as
   NEEDS_ANSWERS rather than take the first file listed.

## The Vendor Data Dictionary (M3)

The VDD goes through the same machinery: `discover_vdd` finds the `FILES`
sheet by header signature and the field sheets by the FILES sheet's
`Field Sheet` column or by signature, with roles from `extractor.vdd`
(populated only from the V1/V2/V3 headers of SHAPES_FOR_PORT §3), segments
from a `Segment` column, and one-sheet-per-table dictionaries narrowed to
the STTM's table names. `resolve_pair(vdd_path=…)` resolves it as the third
document (same cache → synonyms → model → validate → user order, same
dialog group), and `codegen extract-vdd` reads it into a `VddContract`
(`src/codegen/contracts/vdd.py`) with a cell reference on every value.
The VDD is never a source for the standard layer: its values enter an
output only as the fixed-width position rows (IIG v2, M4) and as the
STTM-vs-VDD gate flags (`src/codegen/gate/vdd_check.py`: one flag per
mismatch citing both cells — `vdd_mismatch:type` through the
type-equivalence classes in config, `vdd_mismatch:length`,
`vdd_mismatch:position`, `vdd_missing_in_sttm`, `vdd_missing_in_vdd`,
`vdd_segment_mismatch`, plus one `vdd_field_count` summary). The verdict
stays PASS_WITH_FLAGS except when the FRD states a fixed-width format and
the VDD supplies no positions — a failed gate check naming the remedy.

## Caches and fixtures

`fixtures/layout_profiles/<doc>.layout.json` — the correct profile of every
M0 fixture (curated in `tests/acfc_shapes/layout_truth.py`, materialized by
`scripts/build_layout_profiles.py`; the suite asserts the tracked files
equal a fresh build). They double as the mock provider's answers and as the
few-shot examples. `fixtures/layout_profiles/mock/adversarial_*.json` —
one wrong claim each (wrong header row, swapped spans, a role on a data
column, an invented sheet, a role on a free-text column) plus the canary
answer. The runtime cache lives under `ui/backend/state/` (gitignored).

## Surfaces

- CLI: `codegen layout --workbook X [--frd Y] [--vdd Z] [--dry-run]
  [--no-cache] [--refresh] [--json] [--profile-out P]
  [--frd-contract-out C] [--answers A] [--require-complete]` —
  `--frd-contract-out` writes the FRD contract AS THE PAIR RESOLVED IT (a
  feed the FRD leaves unnamed is named after the STTM stage band, gaps
  filled, every such decision in its `extraction_flags`);
  `codegen extract-sttm --layout <profile.json> [--require-complete]`;
  `codegen extract-frd --profile <out.json>`.
- UI: `GET /api/demo/status` carries `layout_questions` and
  `layout_report` while `state == "needs_layout"`; `POST
  /api/demo/layout-answers {answers:{sttm:{"<sheet>/<layer>/<role>": col},
  frd:{…}, gaps:{"feeds[0].file_patterns": {value}}}, proceed, cancel,
  refresh}` resumes the run (question kinds: `role`, `choice`, `layer`, and
  since v0.5.2 `text` — a value no document states, typed; `refresh` =
  re-resolve past the caches, the earlier answers dropped); `POST
  /api/demo/layout-refresh {enabled}` arms the same for the NEXT run (one
  shot; `layout_refresh` on the status; 409 while a run is in progress).
- Report: per document the source per role, validator rejections with
  reasons, provider call count; per pair the cross-checks that fired.
