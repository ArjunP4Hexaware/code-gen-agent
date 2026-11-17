# One reader for every document shape — proposal (2026-11-17)

Soham, 2026-11-17: "start looking at the total set of bugfixes and try to think of a
generalized solution ... instead of patchworking with finetunes and special cases because
this isn't sustainable." No code yet; this is the design to decide on.

## 1. What the fix history says

80 version entries since post51 changed how an input document is read (catalogue of
CHANGELOG_ACFC.md, 2026-11-17; versions, shapes and counts only):

| Kind of change | Count | Example versions |
|---|---|---|
| New parser code for a cell / table shape (SHAPE-CODE) | 21 | 168, 172, 175, 189, 192, 196, 197 |
| Synonyms / label words (SYNONYM) | 14 | 55, 74, 94, 180, 192, 195 |
| A value taken from another document or derived (FALLBACK) | 14 | 57, 81, 84, 108, 130, 196 |
| When / how to ask (QUESTION) | 13 | 57, 80, 155, 170, 192 |
| Matching files / sheets / tables / feeds (PAIRING) | 9 | 59, 114, 156, 179, 182 |
| Document family detection (FAMILY) | 5 | 55, 62, 118, 161 |
| Layout model / line locator (MODEL) | 4 | 111, 129, 159, 176 |

Only 11 of the 80 were config-only. The same five underlying shapes keep coming back:

1. **A `label: value` line inside a prose cell** - 10 versions (57, 84, 168, 172, 174, 175,
   176, 189, 192, 196).
2. **A value no document states** (ask / blank / default / derive) - 11 versions.
3. **Matching by name or position** (file <-> sheet <-> table <-> feed <-> requirement) -
   8+ versions, and at least four separate pairing functions in `layout/resolve.py`.
4. **A canonical value spelled another way** (load strategy, decimal, audit types,
   delimiters) - 9 versions.
5. **A marker word meaning "nothing"** (N, NA, Do Not Map, `-`) - 5 versions.

The self-extension plan (`docs/PARSER_SELF_EXTENSION.md`, steps 1-4, built post172-176)
made VOCABULARY an approval instead of a deploy. It did not stop the code changes,
because the expensive gaps are not vocabulary: post192, post196 and post197 were all new
SHAPES (a value on one line of a long cell; a heading with sub-headings; a bracketed file
name; keys after a phrase) and new SCOPES (a value stated per requirement, not per
document).

## 2. Why the patches keep coming (root cause)

The FRD reader is organised by **document family and by field**: `_discover_f1`,
`_discover_f2`, then a growing chain of post-passes, each for one field in one shape -
`_place_line_fields` (post192), `requirement_landings` (post84), `_place_load_type_blocks`,
`requirement_file_names` (post196), `requirement_load_type_keys` (post197). Each pass
carries its own guards (single feed only, all must agree, skip nested cells) and its own
citation flag. Three consequences:

- **Families are not real.** Real FRDs mix them (the post196 document: two F1 section
  tables beside seven Solution Requirement tables). Choosing a family decides which tables
  are read at all.
- **Every new place a fact is written is new code**, even when the grammar is one already
  handled for another field (post196's Load Type block is the labelled-lines grammar
  nested one level).
- **Passes interact.** Each reads the same cells with different rules; a side effect shows
  up in another field (post193's decided blank, post196's serialised `null`).

## 3. The proposal: one document model, generic grammars, data-driven fields

Read EVERY document into one shape first, then decide fields from data:

```
Document -> Scopes -> Statements
  Scope      = where a fact may apply: the whole document, a section table, a requirement
               table, an STTM sheet, a per-file block. It carries its identity evidence
               (requirement Name, file names, table names it mentions).
  Statement  = (label path, value text, coordinates), e.g.
               ["Functional Requirement", "Load Type", "STG"] -> "Incremental:- Truncate & load"
               ["Functional Requirement", <file>]             -> "NAME_MMDDYYYY.csv"
               ["Frequency"]                                   -> "Monthly"
```

**Step A - generic cell grammars, no field knowledge.** About six, each applied to every
cell of every table: label | value rows; `label: value` lines; a heading line followed by
indented / sub-headed lines (nested to any depth - Load Type > STG > value); bracketed
tokens (`<file.csv>`); nested tables; lists. Today these exist, but each is wired to one
field.

**Step B - fields as vocabulary.** Each contract field declares, in config, the label PATHS
that state it and the TYPE of its value (strategy, file pattern, delimiter character,
cadence, column list, schema name). Matching is path match + the type's validator and
normaliser (one per type: the canonical strategy with leading words, delimiter words,
format tokens, marker words for "nothing"). A new shape that is an existing grammar becomes
a config line - approvable in the App like today's vocabulary (post174).

**Step C - one scope-to-feed binding.** Every statement keeps its scope; scopes bind to
feeds by identity evidence through ONE pairing function (file name, then table name, then
requirement name; unique or asked - never by elimination of 2+). post84's landings,
post196's file names and post197's keys are the same binding three times today.

**Step D - one conflict policy.** For each (feed, field), every statement from every
document (FRD, STTM, VDD, a derivation like the file extension) is collected with a
precedence from config. Agree -> the value + its citation; disagree -> a choice question
listing them; none -> the field's question / blank rule. Today this is the gap chain plus
per-field custom code.

**Step E - the unknown is visible.** Statements no field claims go to the existing
shapes report (post173); the model locator (post176) points at a STATEMENT id - code
copies it, as now.

**What does not move:** the two-layer trust, the citation rule, the validators, byte-stable
output, and the contracts. The new reader produces the same `FrdContract` / STTM contract,
so the resolver's downstream, the emitters and the gate are untouched.

## 4. Getting there without a big-bang rewrite

| Phase | What | Behaviour change | Exit test |
|---|---|---|---|
| 0 | **Shape corpus**: a synthetic replica (no client values) of every shape in §1's catalogue, each with its expected contract fields - the oracle | none | every replica passes on today's reader |
| 1 | **Statement extractor** (Steps A + scopes) + a dump tool; run on the 12 pairs, pair_13 and the shape corpus | none | every value today's reader extracts appears as a statement (coverage %, per field) |
| 2 | **Shadow resolver** (Steps B-D) builds a second contract beside the old one; the 12-pair check diffs them field by field | none (shadow only) | per field: equal, or the difference reviewed and accepted |
| 3 | **Cut over field by field**; delete each post-pass as its field moves | per field, reviewed | 12-pair check + the shape corpus green |

STTM headers can start sooner and alone: header roles are already data; the post195 class
(`FieldName` vs `field name`, `ColumnName`, `TableName`) disappears if labels also match
with spaces removed - one change in the normaliser, checked with the 12-pair check.

## 5. Cheap generic wins available now (each one change, each kills a class)

1. **Space-insensitive label matching** (STTM roles + FRD labels): compare the normalised
   label with and without spaces. Removes the post195 class; `columnname` / `tablename` in
   config today are hand-written copies of it.
2. **One value normaliser per field type** (strategy, delimiter, format, decimal, marker
   words) used by every reader - post196's `canonical_strategy` is the first.
3. **One pairing function** for file / sheet / table / requirement -> feed (Step C alone):
   the four variants in `layout/resolve.py` merge into one with the same rules.

## 6. Decisions for Soham

1. Go / no-go on the Phase 0-3 plan (Phase 0-1 change no output and are the oracle for
   the rest).
2. Whether the three cheap wins (§5) go first, each as its own version with the 12-pair
   check.
3. Until Phase 3, new tester shapes keep being fixed as today (a version each) - or held
   for the new reader when they are not blocking a tester.

Rough size (my estimate, not measured): Phase 0 and 1 are days, not weeks; Phase 2-3 is the
bulk and depends on how many fields differ in the shadow diff.
