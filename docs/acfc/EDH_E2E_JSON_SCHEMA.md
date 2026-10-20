# EDH_E2E_JSON_SCHEMA — the EDH E2E gold-mapping JSON dialect

> **Purpose**: let the home reader for the gold-layer EDH E2E mappings be built without a real
> value crossing the wire. The dialect is written as a JSON Schema (draft 2020-12), with
> per-field counts, three placeholder grammars with coverage counts, the validator's defect
> checks, and a comparison of the synthetic fixture set against the real set.
> Companion to `GOLD_STTM_SHAPE.md` (the Provider Lakehouse STTM workbook, a different
> document family).
>
> **Real set** (read 2026-10-20 on D1, never copied into the repo): the extractor's output
> volume folder, `_manifest.json` + 11 table files, 389 mapping rows, 1,963 regional items.
> Source system Facets, target the Enterprise Data Hub gold layer.
> **This document carries no source_table, target_table, column name, region label, criteria
> text or expression from that set** — only header/key names, counts, shapes and placeholder
> patterns. Real files are cited as `file[<n>]` (1-based, sorted file-name order, manifest
> excluded) and rows as `file[<n>].mappings[<k>]` (0-based).
> **Synthetic set**: `tests/fixtures/edh_gold_synthetic/` (§5) — every name `SYN_`-prefixed,
> every value fabricated.

---

## 1. JSON Schema

Two documents: the manifest and one table file. Constraints JSON Schema cannot state
(cross-field equality, uniqueness of a property across items) are listed under
`x-codegen-checks` and in §4. Fixture files carry a top-level `$comment` (0 of 11 real files);
the schema allows it.

### 1.1 Manifest (`_manifest.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "codegen:edh_e2e/manifest",
  "type": "object",
  "additionalProperties": false,
  "required": ["extracted_at", "source_volume", "file_count", "tables"],
  "properties": {
    "$comment": {"type": "string"},
    "extracted_at": {"type": "string", "format": "date-time"},
    "source_volume": {"type": "string", "pattern": "^/Volumes/[^/]+/[^/]+/[^/]+"},
    "file_count": {"type": "integer", "minimum": 1},
    "tables": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["target_table", "mapping_count", "refresh_schedule", "json_file"],
        "properties": {
          "target_table": {"type": "string"},
          "mapping_count": {"type": "integer", "minimum": 1},
          "refresh_schedule": {"type": ["string", "null"]},
          "json_file": {"type": "string", "pattern": "^[a-z0-9_]+\\.json$"}
        }
      }
    }
  },
  "x-codegen-checks": [
    "file_count == len(tables)",
    "every tables[].json_file exists beside the manifest",
    "tables[].json_file == slug(tables[].target_table) + '.json' (lower-case, non-alphanumerics -> '_')",
    "tables[].target_table / mapping_count / refresh_schedule equal the table file's top-level values"
  ]
}
```

### 1.2 Table file (`<slug>.json`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "codegen:edh_e2e/table",
  "type": "object",
  "additionalProperties": false,
  "required": ["document_name", "source_file", "layer", "destination_catalog", "target_table",
               "refresh_schedule", "load_type", "mapping_count", "mappings",
               "regional_table_structures", "rules", "summary", "extracted_at"],
  "properties": {
    "$comment": {"type": "string"},
    "document_name": {"type": "string", "minLength": 1},
    "source_file": {"type": "string", "pattern": "\\.xlsx?$"},
    "layer": {"const": "gold"},
    "destination_catalog": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
    "target_table": {"$ref": "#/$defs/identifier"},
    "refresh_schedule": {
      "anyOf": [{"type": "null"},
                {"enum": ["Daily", "Weekly", "Monthly"]},
                {"type": "string", "pattern": "^(Daily|Weekly|Monthly) \\(.+\\)$"}]
    },
    "load_type": {
      "anyOf": [{"type": "null"},
                {"type": "string", "pattern": "^This is a full \\S+ load\\.?$"}]
    },
    "mapping_count": {"type": "integer", "minimum": 1},
    "mappings": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/mapping"}},
    "regional_table_structures": {
      "type": "object",
      "propertyNames": {"pattern": "^[A-Z]+[0-9]+ - LOB ?\\(.+\\)$"},
      "additionalProperties": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/region_item"}}
    },
    "rules": {"type": ["array", "null"], "items": {"type": "string", "minLength": 1}},
    "summary": {
      "anyOf": [{"type": "null"},
                {"type": "object", "additionalProperties": false,
                 "required": ["table_name", "version", "document_name", "resource_name", "bsa", "completion_date"],
                 "properties": {
                   "table_name": {"type": "string"},
                   "version": {"type": "string", "pattern": "^[0-9]+$"},
                   "document_name": {"type": "string"},
                   "resource_name": {"type": "string"},
                   "bsa": {"type": "string"},
                   "completion_date": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$"}}}]
    },
    "extracted_at": {"type": "string", "format": "date-time"}
  },
  "$defs": {
    "identifier": {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9_]*$"},
    "nullable_text": {"type": ["string", "null"]},
    "mapping": {
      "type": "object",
      "additionalProperties": false,
      "required": ["source_database", "source_table", "source_field", "target_table",
                   "target_attribute", "data_definition", "selection_criteria",
                   "source_format", "indexes"],
      "properties": {
        "source_database": {"$ref": "#/$defs/nullable_text"},
        "source_table": {"$ref": "#/$defs/nullable_text"},
        "source_field": {"$ref": "#/$defs/nullable_text"},
        "target_table": {"$ref": "#/$defs/identifier"},
        "target_attribute": {"$ref": "#/$defs/identifier"},
        "data_definition": {"$ref": "#/$defs/nullable_text"},
        "selection_criteria": {"$ref": "#/$defs/nullable_text"},
        "mapping_edits": {"$ref": "#/$defs/nullable_text"},
        "source_format": {"$ref": "#/$defs/nullable_text"},
        "field_length": {"$ref": "#/$defs/nullable_text"},
        "target_format": {"$ref": "#/$defs/nullable_text"},
        "indexes": {"$ref": "#/$defs/nullable_text"},
        "comments": {"$ref": "#/$defs/nullable_text"}
      }
    },
    "region_item": {
      "type": "object",
      "additionalProperties": false,
      "required": ["column_name", "data_type"],
      "properties": {
        "column_name": {"type": "string", "minLength": 1},
        "data_type": {"$ref": "#/$defs/nullable_text"}
      }
    }
  },
  "x-codegen-checks": [
    "mapping_count == len(mappings)",
    "every mappings[].target_table == target_table (one target per file)",
    "mappings[].target_attribute unique within the file",
    "every regional region's column_name set == the set of mappings[].target_attribute (else a region-drift flag, not a failure)",
    "region keys identical across the manifest's files (same label, same code list)",
    "source_format VARCHAR<n> with n > 2 is a drag-fill suspect (flag, value kept)",
    "a region column_name that is not an identifier is a flag (the region is kept)",
    "indexes in {Primary key, Primary Key, PRIMARY KEY, PK} = a primary-key member; any other text = QUESTION"
  ]
}
```

Validated with `jsonschema` 4.26 (`Draft202012Validator`, format checker on). Real set: both
manifest and 8 of 11 table files valid. The 3 invalid files fail only on the identifier rule
for `target_table` / `target_attribute`, i.e. defects 1, 3 and 8 (§4). Synthetic set: the
manifest and (a), (b), (c) valid; (d) invalid on the same rules.

---

## 2. Fields, with counts over the real set

"Key" = files whose JSON carries the key; "non-null" = files (top level) or rows (mappings,
of 389) where the value is non-null and non-empty.

### 2.1 Top level (11 files)

| Field | Type | Required | Key | Non-null | Values / shape (counts) |
| --- | --- | --- | --- | --- | --- |
| `document_name` | string | yes | 11/11 | 11 | 9 end in a `<n>.0` version suffix, 2 do not; `source_file` never ends with it |
| `source_file` | string | yes | 11/11 | 11 | extension `.xlsx` 10, `.xls` 1 |
| `layer` | const | yes | 11/11 | 11 | `gold` 11 |
| `destination_catalog` | string | yes | 11/11 | 11 | 1 distinct value (the EDH catalog of the run environment) |
| `target_table` | string | yes | 11/11 | 11 | identifier 9, prose sentence 2 (defect 1) |
| `refresh_schedule` | string \| null | yes | 11/11 | 8 | `Daily` 5, `Weekly` 1, `Monthly` 1, `Weekly (<words>)` 1, null 3 |
| `load_type` | string \| null | yes | 11/11 | 6 | `This is a full table load` 5, the same + `.` 1, null 5 |
| `mapping_count` | integer | yes | 11/11 | 11 | 4 – 98 (sorted: 4, 7, 7, 9, 11, 11, 49, 55, 63, 75, 98); always `== len(mappings)` |
| `mappings` | array | yes | 11/11 | 11 | 389 rows |
| `regional_table_structures` | object | yes | 11/11 | 10 | 7 regions in each of the 10; `{}` in 1 |
| `rules` | array \| null | yes | 11/11 | 2 | 2 sentences in each of the 2 |
| `summary` | object \| null | yes | 11/11 | 4 | 6 keys: `table_name`, `version` (one digit), `document_name`, `resource_name`, `bsa`, `completion_date` (`YYYY-MM-DD HH:MM:SS`) |
| `extracted_at` | string | yes | 11/11 | 11 | ISO-8601 with microseconds and UTC offset |

Manifest: `extracted_at` (same format), `source_volume` (a 3-segment `/Volumes/...` path),
`file_count` = 11 = `len(tables)`, `tables[]` = `{target_table, mapping_count,
refresh_schedule, json_file}`; every `json_file` exists and equals the slug of its
`target_table` — so a prose `target_table` becomes a prose file name (one 98-character name).

### 2.2 `mappings[]` (389 rows)

| Field | Type | Required | Key (files) | Non-null (rows) | Values / shape (counts) |
| --- | --- | --- | --- | --- | --- |
| `source_database` | string \| null | yes | 11/11 | 366 | one word 357, `<word><digit><word>` 7, `NA` 1, two words 1; never `catalog.schema` |
| `source_table` | string \| null | yes | 11/11 | 354 | bare names: 0 of 354 contain a `.` |
| `source_field` | string \| null | yes | 11/11 | 381 | |
| `target_table` | string | yes | 11/11 | 389 | one identifier per file on 9 files; 2 files carry 2–3 distinct values (defect 3). In one of them, 46 of 55 rows carry a trailing `.`; in the other, one value has a space |
| `target_attribute` | string | yes | 11/11 | 389 | unique per file on 9 files; 2 files repeat them (defect 2); 1 value with a space (1 file) |
| `data_definition` | string \| null | yes | 11/11 | 270 | free text |
| `selection_criteria` | string \| null | yes | 11/11 | 120 | §3.1 / §3.2 grammars (46 distinct texts) |
| `mapping_edits` | string \| null | no | 10/11 | 322 | §3.3 grammar: 175 `Direct …`, 147 other (119 distinct) |
| `source_format` | string \| null | yes | 11/11 | 386 | `VARCHAR2` 246, `DATE` 56, `VARCHAR` 39, other word 15, `CHAR(<n>)` 9, `TIMESTAMP` 7, `VARCHAR<n>` n = 3…7 7 (drag-fill), `DECIMAL` 4, `<word> as is` 1, `DATE,` 1, two words 1 |
| `field_length` | string \| null | no | 10/11 | 322 | `<n>` 271, `<n>.<n>` 46, `<n>,<n>` 4, two words 1 |
| `target_format` | string \| null | no | 1/11 | 11 | `VARCHAR2(<n>)` 9, `DATE` 2 — the one file with this key has no `field_length` |
| `indexes` | string \| null | yes | 11/11 | 31 | PK marker: `Primary key` 19, `Primary Key` 3, `PRIMARY KEY` 3, `PK` 4; other two-word text 2 |
| `comments` | string \| null | no | 10/11 | 10 | free text |

### 2.3 `regional_table_structures`

- Keys are **region labels with the region's code list embedded in the key** — data stored
  as a dict key. Shape `<LABEL><n> - LOB[ ](<code>, …)`, 7 shapes, the same 7 in every file
  that has regions:

  | Shape | Codes in the list | Space before `(` |
  | --- | --- | --- |
  | R1 | 9 | yes |
  | R2 | 3 | yes |
  | R3 | 2 | no |
  | R4 | 2 | no |
  | R5 | 1 | no |
  | R6 | 10 | no |
  | R7 | 5 | no |

  8 distinct keys across the 10 files: one file spells R2's list differently (one code
  without the leading zero the other 9 files carry). Match regions on the label part, never
  on the whole key.
- Values: `[{column_name, data_type}]`; 1,963 items. Rows per region = `mapping_count` on 7
  of 10 files; in 9 of 10 files the column names match the target attributes (> 80 %); in
  5 of 10 the 7 regions are not identical. 10 column names (4 files) contain spaces, so
  they are not identifiers.
- `data_type` is a raw Oracle DDL fragment, padding and trailing comma included:
  `VARCHAR2(<n> BYTE),` 1,329, `DATE,` 244, `VARCHAR2(<n> BYTE) NOT NULL,` 99,
  `VARCHAR2 (<n> BYTE)` 77, `DATE` 49, `NUMBER(<n>),` 42, `VARCHAR2(<n> BYTE)` 36,
  `DATE NOT NULL,` 35, `VARCHAR2(<n>)` 21, `NUMBER(<n>) NOT NULL,` 7, `NUMBER(<n>,<n>),` 7,
  `TIMESTAMP(<n>),` 7 (whitespace collapsed for counting); sentinels `NOT AVAILABLE` 5,
  `NOT SUPPLIED` 3, `COLUMN NOT FOUND` 1, `NULL` 1, null 1. A reader strips the comma,
  collapses whitespace, splits `NOT NULL` off as nullability, and maps the sentinels to an
  open input.

---

## 3. Grammars (placeholder patterns, coverage over the real cells)

The patterns are case-insensitive regular expressions over the cell text; `<…>` is a
placeholder, `[…]` optional. A cell no pattern covers is **free text** and becomes a QUESTION
in the contract. Counts: cells (distinct texts in brackets).

### 3.1 `selection_criteria` — join hints

62 cells (17 distinct texts) contain a join; **4 patterns cover 62 / 62 (100 %)**.

| Pattern | Cells (distinct) | Join type | ON columns | Tables named | Example (placeholders) |
| --- | --- | --- | --- | --- | --- |
| J1 using-column | 47 (11) | INNER | one shared column name (`using <col>`); 7 add a second (`& <col2>`) | base + joined (2 cells name two joined tables) | `<verb> FROM <src_table> AND INNER JOIN with <join_table> [table] using <key_col> column [& <col2>] [WHERE <filter>]` |
| J1 filter-first | 13 (4) | INNER | one shared column name | base + joined | `<verb> FROM <src_table> WHERE <filter> AND INNER JOIN with <join_table> [table] using <key_col> column [& <filter>]` |
| J2 column without `using` | 1 (1) | INNER | one column name, no `using` | base + joined | `<verb> FROM <src_table> AND INNER JOIN with <join_table> WHERE <filter> <key_col> column & <filter>` |
| J3 alias equalities | 1 (1) | INNER **and** OUTER (legacy `*=`) | `<a>.<col> = <b>.<col>` pairs | none — aliases only | `INNER <word> BETWEEN <a>.<col> = <b>.<col> AND <a>.<col2> = <b>.<col2> OUTER JOIN BETWEEN <a>.<col3> *= <c>.<col3>` |
| J4 table only | 0 | — | — | — | `<verb> FROM <src_table> AND INNER JOIN with <join_table>` |

- Join type stated: **62 / 62** (61 INNER only; 1 INNER + OUTER, whose outer side is the
  legacy `*=` operator).
- ON columns: 60 give one column name that the reader must assume is spelled the same on both
  sides; 1 names a column without `using`; 1 gives explicit alias equalities. No cell gives a
  two-sided ON clause with table names.
- Table names: 61 name the joined table (bare, unqualified — the UC mapping is a separate
  input); 1 names none.
- Free text: 0 cells.

### 3.2 `selection_criteria` — filters

120 cells (46 distinct): 3 are a join with no filter part, so the filter grammar runs on
**117 cells**. The join clause and a leading `<verb> FROM <src_table> [WHERE]` preamble are
removed first; a cell is covered when nothing but connectives (`AND`, `OR`, `&`, `WHERE`,
`column`, `table`, `the`) remains.

| Pattern | Cells (multi-label) | Example (placeholders) |
| --- | --- | --- |
| F1 equality | 73 | `<col> = '<v>'`, `<col> <> <n>`, `<col words> = <token>` |
| F2 IN list | 17 | `<col> IN ('<v1>', '<v2>', …, '<v7>')` |
| F3 date window, relative | 7 | `<fn>(<date_col>) >= sysdate - <n> AND <fn>(<date_col>) <= sysdate` |
| F4 date window, as-of range | 2 | `(<eff>/<term> >= <asof> AND <eff>/<term> <= <asof>) AND (<eff2>/<term2> >= <asof> AND <eff2>/<term2> <= <asof>)` |
| F5 date window, between | 1 | `<eff_col> < <fn>() < <term_col>` |

Per cell (one class each):

| Class | Cells (distinct) |
| --- | --- |
| equality (F1 / F2 only) | 72 (26) |
| date window (F3 / F4 / F5, possibly with F1 / F2) | 10 (3) |
| **free text** | **35 (14)** |

**Coverage: 82 / 117 = 70.1 %.** The 35 free-text cells, by shape:
- 7 are a conditional, `if <col> = <n> - <a>.<col> IS NOT <word>`.
- 12 read `for the <words> of [a] <words>`.
- 5 read `only <word> IN <word> <n>` or a variant of it.
- 4 read `NOT <word> IN the <word>`.
- 2 read `column NOT <word>`.
- 2 read `<word> NOT <word> to <word>`.
- 2 are a single word or phrase.
- 1 mixes an `AS` alias with `IN (<n>, …)` lists.

### 3.3 `mapping_edits` — expressions

322 non-null cells: 175 are `Direct …` (a straight move). The grammar runs on the other
**147 cells (119 distinct)**; first match wins, in this order.

| Pattern (user class) | Cells (distinct) | Example (placeholders) |
| --- | --- | --- |
| literal: `set [to\|as] NULL` | 16 (5) | `set to NULL` |
| literal / system value: `current timestamp` | 4 (2) | `current timestamp` |
| CAST: `CONVERT(` / `CAST(` | 1 (1) | `TRIM(CONVERT('<a>', '<b>', <t>.<col>))[<n>,<n>]` |
| other — substring slice | 31 (30) | `<col>[<n>,<n>]`, `TRIM(<col>)[<n>,<n>]`, `(<col>)[<n>,<n>]` |
| COALESCE (null / empty substitution) | 27 (27) | `if ISNULL(<col>) THEN <fn>() ELSE <col>`; `if <col> IS [NOT] [an] empty string [OR NULL] THEN <alt> ELSE <col>` |
| CASE (`if … THEN … [ELSE if …] ELSE …`) | 25 (24) | `if <col> <> '<v>' THEN <col> ELSE '<v>'`; `if <col> = '<v1>' THEN <a> ELSE if <col> = '<v2>' THEN '<b>' ELSE '<c>'` |
| other — column reference, = `source_field` | 18 (18) | `<source_field>` |
| other — column reference, another column | 3 (3) | `<other_col>` |
| concat | 0 as a top-level form | `:` concatenation appears inside 3 cells (CASE / COALESCE / free text), e.g. `… ELSE <col> : '<sep>' : <col2>[<n>,<n>]` |

**Coverage: 125 / 147 = 85.0 %.** The 22 free-text cells (9 distinct), by shape:
- 6 read `NOT <col> for <words> IN <col>, <col> & <col>`.
- 4 read `only for <word> .`.
- 4 are a bare predicate, `<col> > <n>`.
- 4 are a single non-column word.
- 1 is an `if` with no `THEN`.
- 1 has a slice before an `if`.
- 1 is a `SUBSTRING(…)` inside prose.
- 1 is a phrase.

The expression dialect is Facets / Informix-shaped, not SQL: `if … THEN … ELSE`, `ISNULL()`,
`col[<start>,<end>]` slices, zero-argument functions (2 name lengths, 27 uses), `:` concatenation.
The reader translates it; it does not pass it through.

---

## 4. Validator checks (defects in the real set)

| # | Check | Real files failing | Synthetic file built to fail |
| --- | --- | --- | --- |
| 1 | top-level `target_table` is an identifier (and the manifest's `json_file` is not slugged from prose) | 2 of 11 | (d) |
| 2 | `target_attribute` unique per file | 2 of 11 (one file holds all 49 attributes twice, one repeats 3) | (d) |
| 3 | one `mappings[].target_table` per file, equal to the top-level value, an identifier | 2 of 11 (2–3 distinct values, some prose) | (d) |
| 4 | region keys identical across files | 1 of 10 (one code spelled without its leading zero) | (d) |
| 5 | `source_format` not drag-filled (`VARCHAR<n>`, n > 2) | 7 rows | (d) |
| 6 | `indexes` is a PK spelling or empty | 2 rows of other text | (d) |
| 7 | region `data_type` not a sentinel | 10 items | (c) |
| 8 | `target_attribute` is an identifier | 1 of 11 (one value with a space) | (d) |
| 9 | region `column_name` is an identifier (flag only) | 10 items in 4 of 10 files | (c) |

Where each defect comes from (the extractor or the source workbook), checked cell by cell
against the 11 source workbooks: `EDH_E2E_EXTRACTION_DEFECTS.md`.

---

## 5. Synthetic vs real

`tests/fixtures/edh_gold_synthetic/`: `_manifest.json` + 4 files. (a) `syn_mbr_dim.json` is
the table with regions whose column names match the target. (b) `syn_plan_ref.json` has no
regions and no `mapping_edits` key. (c) `syn_elig_fact.json` mixes the selection-criteria
shapes. (d) `syn_memo_…json` carries defects 1–6 and 8. Each file's `$comment` names the real-set
counts it stands in for. The same profiler ran on both sets:

| Shape | Real (11 files, 389 rows) | Synthetic (4 files, 46 rows) |
| --- | --- | --- |
| top-level keys present (all 13) | 11 / 11 each | 4 / 4 each |
| `refresh_schedule` non-null | 8 | 2 |
| `load_type` non-null | 6 | 2 |
| `regional_table_structures` non-empty | 10 (7 regions each) | 3 (7 regions each) |
| `rules` non-null | 2 | 1 |
| `summary` non-null | 4 | 1 |
| distinct region keys | 8 | 8 |
| files whose region columns match targets | 9 | 3 |
| files whose regions differ | 5 | 1 |
| region `data_type` sentinel / null | 10 | 4 |
| row key `mapping_edits` (files) | 10 | 3 |
| row key `field_length` (files) | 10 | 3 |
| row key `comments` (files) | 10 | 3 |
| row key `target_format` (files) | 1 | 1 |
| rows: `source_table` non-null | 354 / 389 | 45 / 46 |
| rows: `source_field` non-null | 381 | 45 |
| rows: `source_format` non-null | 386 | 45 |
| rows: `data_definition` non-null | 270 | 38 |
| rows: `indexes` non-null | 31 | 8 |
| rows: `comments` non-null | 10 | 1 |
| defect 1 / 2 / 3 files | 2 / 2 / 2 | 1 / 1 / 1 |
| drag-filled `VARCHAR<n>` rows | 7 | 3 |
| files with a non-identifier `target_attribute` | 1 | 1 |
| region `column_name` with spaces (items) | 10 | 1 |
| J1 / J1 filter-first / J2 / J3 / J4 | 47 / 13 / 1 / 1 / 0 | 4 / 1 / 1 / 1 / 0 |
| J1 two joined tables / second join column | 2 / 7 | 1 / 1 |
| join cells free text | 0 | 0 |
| filter cells (after join-only) | 117 | 17 |
| F1 / F2 / F3 / F4 / F5 (multi-label) | 73 / 17 / 7 / 2 / 1 | 8 / 2 / 1 / 1 / 1 |
| filter per cell: equality / window / free text | 72 / 10 / 35 | 8 / 3 / 6 |
| join-only cells | 3 | 2 |
| `mapping_edits` Direct / other | 175 / 147 | 22 / 15 |
| literal NULL / system value / CAST | 16 / 4 / 1 | 2 / 1 / 1 |
| slice / COALESCE / CASE | 31 / 27 / 25 | 2 / 3 / 2 |
| column ref (= source) / (other) | 18 / 3 | 1 / 1 |
| `:` concat inside a cell | 3 | 1 |
| edit free text | 22 | 2 |

Every shape counted in the real set has at least one synthetic instance. J4 (table only) is 0
in both. The fixture adds no shape the real set lacks, except the `$comment` key.

---

## 6. How the counts were produced

On D1, read-only. Copies of the volume folder sat in a scratch directory outside the repo.
`scripts/gold/profile_edh.py DIR` prints keys, counts and example coordinates only; the
grammars above are its regular expressions. No real cell text was written to the repo or
printed in a report. Pointed at `tests/fixtures/edh_gold_synthetic/`, the same profiler
produced the right-hand column of §5. `scripts/gold/build_edh_synthetic.py` rebuilds the
fixtures. `tests/test_gold_profiler.py` asserts two things: the profiler's output shares
no token longer than 3 characters with the inputs' table names or region keys, and the
rebuilt fixtures match the tracked bytes.
