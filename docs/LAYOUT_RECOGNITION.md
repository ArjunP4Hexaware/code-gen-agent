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
row by a cheap structural scan (a data row never enters; when the region
cannot be bounded it is capped at 25 rows and marked `capped`). The same
rendering is hashed into the fingerprint, so the cache key and the prompt
material are one and the same. A test places a canary in a data row and
checks the recorded provider request body.

For a document: table titles and the label texts of each table (the
section-prefix column and the label column), never a value cell.

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
   The CLI prints them
   (`codegen layout --require-complete` exits non-zero); the UI pauses the
   run in `needs_layout` and shows one dialog grouped by document; answers
   merge with `source: user`, confidence 1.0, and the completed profile is
   saved to the runtime cache.
6. A profile with unresolved roles still extracts: those values read empty
   and the gate flags `layout_unresolved:…`.

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
  frd:{…}}, proceed, cancel, refresh}` resumes the run (`refresh` =
  re-resolve past the caches, the earlier answers dropped); `POST
  /api/demo/layout-refresh {enabled}` arms the same for the NEXT run (one
  shot; `layout_refresh` on the status; 409 while a run is in progress).
- Report: per document the source per role, validator rejections with
  reasons, provider call count; per pair the cross-checks that fired.
