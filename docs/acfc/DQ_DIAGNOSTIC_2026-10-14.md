# DATA_QUALITY_RULES — diagnostic (2026-10-14, D1 post43 item 6)

Diagnostic only: no emitter change. Scrubbed — rule classes are framework
vocabulary; no feed, table, file or column name appears here.

## What the agent writes, and from what

`src/codegen/metadata_template.py::_dq_rules` (template `iig_v2`,
`dq_rules: [header_trailer_split, date_format, data_type_cast]`) writes, per
file:

| rule | written when | RULE_TYPE |
| --- | --- | --- |
| LoadHeaderAndTrailerToSeparateTablesRule | the header / trailer segments land in tables other than the detail | `Custom` (template constant) |
| DateFormatRule | an STTM load rule states a date conversion | `Custom` |
| DataTypeCastRule | a STAGE column is typed other than String | `Custom` |

Every other class is "additional DQ rules — Engineer" in the review copy.

## SD (pair_2): golden 10 rows, agent 0

- Golden (acfc-results round7 pair_2, scrubbed): RULE_TYPE STDDelta 7,
  Predefined 2, Custom 1. RULE_CLASS DataTypeCastRule 3, LRTrimRule 3,
  DateConversionRule 1, ReferentialCheckRule 1, and one class the scrubber
  masked (2 rows).
- The agent writes none. The SD files are flat CSVs (no header / trailer
  table), no STTM load rule states a date conversion, and the stage is all
  String (AS-IS). So neither rule fires.
- The golden's casts and trims are STDDelta rules: the stage → standard leg
  casting String to the standard types, which the agent's stage-typed
  DataTypeCastRule never looks at.

## CAQH (pair_12): golden 54 rows, agent 18, 0 paired

The home CAQH golden vs the home mock run (`tools/iig_diff.py` RULES block):

| side | RULE_TYPE / RULE_CLASS | rows |
| --- | --- | --- |
| golden | Predefined / LoadHeaderAndTrailerToSeparateTablesRule | 18 |
| golden | Predefined / AddCustomColumnsRule | 18 |
| golden | Custom / ReferentialCheckRule | 18 |
| agent | Custom / LoadHeaderAndTrailerToSeparateTablesRule | 18 |

Identity components (distinct values golden / agent / shared): `@feed` 1/1/1,
`@table` 1/1/1, SOURCE_COLUMN 3/1/0, RULE_CLASS 3/1/1.

- **Why 0 pairs:** SOURCE_COLUMN. The golden's header/trailer row lists the
  header columns AND the trailer columns. The agent's lists the header
  table's only (`_split_rule`: "SOURCE_COLUMN = the header table's
  columns").
- **RULE_TYPE:** the golden writes `Predefined` for the split rule; the
  agent writes `Custom`.
- **Missing classes:** the agent writes no AddCustomColumnsRule and no
  ReferentialCheckRule (one each per file in the golden).

## The corpus's rule classes

Run on D1, then bring home the scrubbed `patterns.md`. Its
"DATA_QUALITY_RULES rule classes" table gives rows and workbooks per
RULE_TYPE × RULE_CLASS:

    python tools/iig_fill_rate.py --corpus docs/acfc/iig_goldens --agent <run outputs> \
        --patterns codegen-outputs/iig_patterns

Per pair, `tools/iig_diff.py` now prints `RULES (D1 only - unscrubbed)`: the
classes per side, the component overlap and every row's identity. The scrubbed
`sheets.md` carries the class table and the overlap counts.
