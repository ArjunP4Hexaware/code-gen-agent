# Parser self-extension — plan (2026-11-05)

Soham: "I cannot viably manage a solution every single time I need to extend the parser …
in prod there's going to be a lot of unfamiliarities." Goal: a new way of writing a value
costs **one human approval**, not a code change + deploy. The trust rules do not move: a
value is copied from a document (or answered), never synthesised; whatever proposes a rule
(code or model), a person approves it once, and from then on it is deterministic.

## What the parser knows

1. **Vocabulary** — which label means which field (`extractor.frd.labels`, the STTM role
   synonyms, `cell_line_labels`). Already data (config / state overlays).
2. **Cell grammars** — how a value is written inside a cell: one value, labelled lines
   (post168), a list, a nested table, per-file blocks, a pointer. Code (`extract/frd_docx.py`
   `classify_cell` + the readers).

Most "parser extensions" so far were vocabulary; the expensive ones were grammars.

## Steps

| # | Step | Removes | Rules change? | Size |
|---|------|---------|---------------|------|
| 1 | **General grammars.** The labelled-lines reader for EVERY single-value FRD field: a line whose label is any FRD label synonym fills that field when its own row is absent or blank (a stated row is never overwritten; a disagreement is flagged). | the post168 class of edits, for all fields | no | small (post172) |
| 2 | **Proposed vocabulary, approved in the App.** When a person answers a question with a value that appears verbatim in a cell the reader refused, the run records a proposal (label as written -> field, cell coordinates). The App lists proposals; Approve writes them to the state root's `overlays/<profile>.yaml` (runtime config, both Apps, next run, no deploy); Reject drops them. | most vocabulary edits | no (proposals are never applied until approved) | medium |
| 3 | **Model points, code copies.** For a refused cell no grammar reads, the layout model is asked which line / span states the field; code copies that span verbatim, the validator checks it is in the cell and fits the field's vocabulary (format tokens, delimiter words, …), the answer is cached per cell fingerprint (a template asks once). | most new grammars | **yes — Soham's decision**: today the model sees fingerprint material only (headers / labels, never a cell value); this shows it the refused FRD metadata cell (no data rows) | medium |
| 4 | **Unfamiliar-shapes report.** Every refusal (`frd_multiline`, `frd_pointer`, `label_prefixed`, UNRESOLVED roles, …) is already recorded per run; aggregate them across runs into one report (shape, field, count, last seen — coordinates and vocabulary only, never cell text) so the rare ones that still need code are fixed by frequency. | guesswork about what to build next | no | small |

Order: 1 -> 4 -> 2 -> 3 (3 only on Soham's word).

## Status

- Step 1: built in post172 (`tests/test_frd_labelled_lines.py`).
- Step 4: built in post173 (`codegen shapes-report`, `tests/test_shapes_report.py`).
- Step 2: built in post174 (`codegen.vocabulary`, the Generate page's card; approve on the
  dev App, shared by both Apps).
- Step 3: Soham, 2026-11-05: allowed for a refused cell of the ingested FRD / STTM (the only
  two inputs) - not built yet.
