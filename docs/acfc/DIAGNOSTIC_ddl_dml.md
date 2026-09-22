# DIAGNOSTIC — DDL / DML artefacts (pair-2 MIDS-shape)

Date: 2026-09-22
Fixture: `fixtures/acfc_shapes/sttm/pair_2_family_b.xlsx` + `frd/f1_pair_2_variant.docx`
Profile: `acfc_prx`, IIG template: `iig_v2`, output mode: `framework`
Contrast: `edo_sfmc` profile against CV pair (SFMC reference goldens)

> **Pair-2 caveat.** The pair-2 STTM+FRD fixture does not fully resolve today
> (the multi-file FRD contract names no file patterns, so
> `extract_contract` raises `ExtractionError: feed 'FEED_2 Claims': the
> FRD contract names NO file for it`). Every finding below is traced from
> the **code paths** (`src/codegen/emit/framework.py`,
> `src/codegen/emit/dml.py`, `config/config.yaml`) and confirmed against
> the **pair-1 golden output** (`fixtures/acfc_shapes/pair_1/golden/
> ACCUM_DDL.txt`) and the **SFMC reference files**
> (`fixtures/reference/SFMC_*_table_creation.txt`), which do run end to end.


---

## 1. Stage and standard DDL are in one file

### What the code does today

`src/codegen/emit/framework.py:L629`: when `profile.ddl_layout == "combined"`,
the emitter calls `_combined_tables` → `_render_combined`, which renders
`templates/framework/combined_ddl.txt.j2` — a single `.txt` file containing
both `--stage table` and `--standard table` blocks (e.g. `ACCUM_DDL.txt`).

When `ddl_layout == "two_files"` (the default, L641-683), it renders
`templates/framework/table_creation.txt.j2` once per layer into
`<slug>_stage_table_creation.txt` and `<slug>_standard_table_creation.txt`.

### Profile keys that cause it

| Key | `acfc_prx` | `edo_sfmc` |
| --- | --- | --- |
| `conventions.profiles.<name>.ddl_layout` | `combined` | `two_files` (default) |

`config/config.yaml:L869`:
```
profiles:
  edo_sfmc:
    ddl_layout: two_files
  acfc_prx:
    ddl_layout: combined
```

`src/codegen/config.py:L968`:
```
ddl_layout: Literal["two_files", "combined"] = "two_files"
```

### Origin

Commit `0381f22` ("M4: conventions profiles + IIG template versions +
drag-fill gate; pair-1 acceptance"), 2026-09-18.

Evidence used at the time (commit message):
> `acfc_prx` is the pair-1 combined ACCUM\_DDL.txt shape … typed stage columns
> from the STTM stage band, audit types in profile casing, standard = stage
> list, `'--stage table'/'--standard table'` banners, every whitespace knob
> data.

The pair-1 golden `fixtures/acfc_shapes/pair_1/golden/ACCUM_DDL.txt` is a
single combined file; the byte-identical acceptance test
(`test_m4_acceptance.py::test_pair1_combined_ddl_is_byte_identical_to_the_golden`)
enforces it.

### `edo_sfmc` contrast

```
fixtures/reference/SFMC_stage_table_creation.txt   (stage, separate file)
fixtures/reference/SFMC_standard_table_creation.txt (standard, separate file)
```

Each file carries per-column COMMENTs, a table COMMENT, LOCATION (stage) /
CLUSTER BY AUTO (standard), TBLPROPERTIES, and trailing SET TAGS — none of
which the combined layout emits.

### Convention or bug

**Convention.** The combined layout faithfully reproduces the client golden.
A feed that needs two-file output uses `edo_sfmc` or a new profile. Not a
correctness issue.

### Proposed fix

None required for the combined layout. To support BOTH shapes from a single
profile (e.g. the combined file for deployment review AND two typed files for
the data lake), add a `ddl_layout: both` option that emits the combined `.txt`
plus the two-file `.txt` side by side.

### Tests / goldens that would change

`test_m4_acceptance.py::test_pair1_combined_ddl_is_byte_identical_to_the_golden`
— only if the combined file's content changes; a `both` option adds files,
does not alter the combined one.


---

## 2. Standard-layer DDL types are all STRING

### What the code does today

`src/codegen/emit/framework.py:L193-214`:

```python
stage_columns.append((f.stage_column, f.stage_datatype if profile.typed_stage
                      else "STRING"))
if f.standard_column is not None:
    standard_columns.append((f.standard_column, f.standard_datatype or ""))
...
columns = stage_columns if profile.standard_from_stage else standard_columns
```

When `standard_from_stage: true` (L975 of config.py, the `acfc_prx` default),
the standard table receives **stage_columns** — the stage types — instead of
**standard_columns** which carry the STTM standard band's `standard_datatype`.

### Type trace for three pair-2 STTM columns

| STTM column | STTM cell (standard band C16) | Contract field `standard_datatype` | Template variable used | DDL line |
| --- | --- | --- | --- | --- |
| `CLAIM_DATE` | `Date` (MAPPING- R3 C16) | `"Date"` | **ignored** (stage_columns used); `stage_datatype = "String"` (C12) | `CLAIM_DATE String` |
| `DOB` | `Date` (MAPPING-1 R4 C16) | `"Date"` | **ignored**; `stage_datatype = "String"` | `DOB String` |
| `CLAIM_ID` | `String` (MAPPING- R3 C16) | `"String"` | stage_datatype `"String"` (same) | `CLAIM_ID String` |

(Pair-2 has no Decimal columns in either band; pair-1 has Decimal(17,2)–(22,2)
in **both** bands, so stage = standard there and the bug is invisible.)

### Every code path where a standard type can be replaced by the stage type

1. **`framework.py:L214`** — `standard_from_stage: true` selects `stage_columns`
   for the standard CREATE. This is the direct cause.
2. **`framework.py:L205`** — `f.standard_datatype or ""` falls back to empty
   string when None; the fallback doesn't force STRING but an empty type in DDL
   is wrong. In practice, when `standard_from_stage: true` this line is dead.
3. **`config.py:L975`** — the profile knob itself. Only `acfc_prx` sets it.
4. **No other code path** (the `context.py` notebook-mode emitter at L490 uses
   `f.standard_datatype` directly, never the profile knob).

### Does the pair-1 golden depend on this behaviour?

**Yes.** Pair-1's STTM has **identical** types in both stage and standard bands
(String, Date, Decimal(p,2) at the same precisions). The golden
`ACCUM_DDL.txt` shows standard = stage, byte identical. The acceptance test
(`test_pair1_combined_ddl_is_byte_identical_to_the_golden`) passes because
`standard_from_stage: true` copies stage types which happen to equal the
standard types.

### What a real standard-type golden would require

A fixture where stage types differ from standard types (pair-2 qualifies:
stage `String` vs standard `Date` for CLAIM_DATE / DOB / EFFECTIVE_DATE /
TERM_DATE). The golden would show `Date` in the standard block.

The SFMC reference already demonstrates this:
```
Stage:    MEMBER_DOB STRING   (SFMC_stage_table_creation.txt)
Standard: MEMBER_DOB DATE     (SFMC_standard_table_creation.txt)
```

### Convention or bug

**Correctness bug.** The `standard_from_stage: true` flag was introduced to
match the pair-1 golden where it happens to be safe. For any feed where the
STTM declares different types in the standard band (pair-2, SFMC, and most
real feeds), the standard DDL loses those types.

### Proposed fix

In `_combined_tables`, build `standard_columns` from `f.standard_datatype`
(the STTM standard band) regardless of `standard_from_stage`. The knob should
control **which columns appear** (the stage list, including fillers), not
**their types**. Concretely:

```python
# L214: replace
columns = stage_columns if profile.standard_from_stage else standard_columns
# with something like:
if profile.standard_from_stage:
    # Use the stage column LIST but map each to its standard TYPE
    std_type_map = dict(standard_columns)
    columns = [(name, std_type_map.get(name, dtype)) for name, dtype in stage_columns]
else:
    columns = standard_columns
```

The pair-1 golden stays byte-identical (both bands have the same types).
A new pair-2 golden with typed standard columns is required.

### Tests / goldens that would change

* `test_m4_acceptance.py::test_pair1_combined_ddl_is_byte_identical_to_the_golden` —
  **unchanged** (pair-1 types are the same in both bands).
* A **new** golden for pair-2 (or any heterogeneous-type fixture) would be
  added to pin the correct behaviour.
* `test_dml_emit.py` — unchanged (DML rows carry IIG types, not DDL types).


---

## 3. DML files named q1 / a2 / prod

### Config key and origin

`config/config.yaml`, section `dml:`:
```yaml
environments: [q1, a2, prod]
file_name_pattern: "config_inserts_{env}.sql"
notebook_file_name_pattern: "Insert_scripts_config_table_{env}.py"
```

`src/codegen/config.py:L1221`:
```python
environments: list[str] = Field(default_factory=lambda: ["q1", "a2", "prod"])
```

Introduced in commit `a07bece` ("M7 step 3: DML deliverable for the SQL
Server metadata DB (emit/dml.py)"), 2026-09-18. Commit message:
> `config_inserts_<env>.sql` per environment (q1 / a2 / prod) + `Insert_scripts_config_table_<env>.py`

Source evidence: the walkthrough transcript in `docs/acfc/METADATA_DB_SEMANTICS.md`
mentions "q1", "a2", "prod" as the client's environment names — they are
ACFC-specific platform vocabulary (QA-1, Acceptance-2, Production), not a
framework convention.

### What differs between the three scripts

The **variables block** (first ~20 lines) differs; the **body** (INSERT
statements) is byte-identical across environments. Confirmed by
`test_dml_emit.py::test_environments_differ_only_in_the_variables_block`:

```python
assert _body(q1) == _body(prod)
assert "DECLARE @ENV NVARCHAR(16) = N'q1';" in q1 and "N'prod';" in prod
```

Per-environment differences in the variables block:

| Variable | q1 | a2 | prod |
| --- | --- | --- | --- |
| `@ENV` | `N'q1'` | `N'a2'` | `N'prod'` |
| `@PATH_PREFIX` | `N''` | `N''` | `N''` |

All other variables (`@RFC_NUMBER`, `@PIPELINE_ID`, `@GROUP_ID`, `@OBJECT_ID`,
connection roles) are identical across environments (all default to `NULL --
ASSIGN`). The path prefix is currently empty for all three (`env_path_prefix:
{q1: "", a2: "", prod: ""}`).

The runner notebooks (`Insert_scripts_config_table_{env}.py`) differ only in
the `SQL_NAME` constant (pointing to their `.sql` file) and the `ENVIRONMENT`
header comment.

### Does any catalog/schema in the DML or the runner notebook depend on the environment?

**No.** The DML operates against the SQL Server metadata database (T-SQL
dialect, `dbo` schema). The catalog/schema for the Databricks tables is in the
DDL, not the DML. The DML's path columns use `CONCAT(@PATH_PREFIX, …)` but the
prefix is empty for all three environments today.

### Does "d1" appear anywhere?

`d1_` appears only in `config/config.yaml`:
* `databricks.catalog: d1_dlk` (line 752)
* `conventions.default_catalog: {stage: d1_dlk, standard: d1_std}` (line 842)

These are the **DDL catalog defaults** (the convention fallback chain: FRD → STTM
→ `default_catalog`). They are NOT the DML's concern. The environment name
does NOT drive the `d1_` prefix — `d1_` is hardcoded in the config's
`default_catalog`, independent of any DML environment.

### What it would take for the environment to be "d1" by default and drive the catalog prefix

1. Add `d1` to `dml.environments` (or replace `q1`).
2. Add a new config key mapping environment → catalog prefix
   (e.g. `env_catalog_prefix: {d1: d1_, q1: q1_, a2: a2_, prod: ""}`).
3. Wire `_qualify()` in `framework.py` to read the environment's prefix
   instead of the static `default_catalog`.
4. Update the STTM extractor / resolver to accept environment-qualified
   catalogs.

This is a design change, not a bug fix. The current design treats the DDL
catalog as a document-level property (from the FRD/STTM) and the DML
environment as a deployment-level property (where the inserts run).

### Convention or bug

**Convention.** The environment names are ACFC-specific and correctly placed in
config rather than code. The empty `PATH_PREFIX` and the environment-blind DDL
catalog are documented limitations.

### Proposed fix

1. No code change needed for the environment names themselves.
2. If the DDL catalog must vary by environment, add an `env_catalog_map`
   config key and wire it into `_qualify()`. This is a feature, not a fix.
3. For `d1` as the development environment: add `d1` to `dml.environments`
   and add `env_path_prefix: {d1: ""}` in a config overlay.

### Tests / goldens that would change

Adding `d1` to environments would add `config_inserts_d1.sql` +
`Insert_scripts_config_table_d1.py`; existing files are unchanged. The
`test_dml_emit.py` suite checks all configured environments dynamically.


---

## 4. ADDITION.md coverage

### Current text

```
# Framework addition — accumulators

- FRD contract: … sha256 …
- STTM contract: … sha256 …
- Load-pattern FAQ: sha256 … — 2 answered, 6 unknown
- Engineering standards: EDO Data Engineering Naming + Coding Standards …
- Layout: client IIG template (anonymized reference — fixtures/reference/SFMC_IIG.xlsx) …

Option B output: an **addition to the existing ingestion framework** …

| File | What it is |
| --- | --- |
| `ACCUM_DDL.txt` | Deployment-team DDL … |
| `config_rows.xlsx` | The config rows for the framework DB … |
| `config_inserts.xlsx` | One sheet per populated IIG tab … |
| `ADDITION.md` | This manifest. |

Columns awaiting framework-assigned IDs …
```

### Full artefact inventory (from pair-1 output)

```
accumulators/
  framework/               ← the ADDITION.md scope
    ACCUM_DDL.txt
    ADDITION.md
    config_inserts.xlsx
    config_rows.xlsx
    [config_inserts_q1.sql]         ← emitted by dml.py when emit_dml=true
    [config_inserts_a2.sql]
    [config_inserts_prod.sql]
    [Insert_scripts_config_table_q1.py]
    [Insert_scripts_config_table_a2.py]
    [Insert_scripts_config_table_prod.py]
  RFC######_ACCUM/         ← rfc mode package
    ACCUM_DDL.txt
    ACCUM_IIG.xlsx
    MANIFEST.md
    RFC######_ACCUM_Deployment_Playbook.xlsx
  candidates/
    candidates.json
  ddl/                     ← side-table DDL
    accum.vnd_p_accum_client.standard.sql
    stg_vnd_p_accum.vnd_p_accum_client.sql
    stg_vnd_p_accum.vnd_p_accum_client_errors.sql
    stg_vnd_p_accum.vnd_p_accum_client_processed_files.sql
```

(Items in `[brackets]` are emitted when `acfc_prx.emit_dml: true` and `dml.enabled: true`; the pair-1 output shown was generated before DML was wired or with dry_run.)

### Artefacts ADDITION.md does not explain or explains wrongly

| Artefact | Status in ADDITION.md |
| --- | --- |
| `config_inserts_q1.sql` / `_a2.sql` / `_prod.sql` | **Missing.** Not listed. The DML deliverable is not mentioned. |
| `Insert_scripts_config_table_q1.py` / `_a2.py` / `_prod.py` | **Missing.** The runner notebooks are not mentioned. |
| `ddl/*.sql` (4 files under `ddl/`) | **Missing.** Side-table DDL (errors, processed_files) and per-layer SQL sources not mentioned. |
| `candidates/candidates.json` | **Missing.** The rule-classification candidates file is not mentioned. |
| `RFC######_ACCUM/` package | **Not in scope** (has its own `MANIFEST.md`). Correct omission. |
| Environment names (q1 / a2 / prod) | **Missing.** The per-environment concept is not described. |
| Environment probe / REVIEW blocks | **Missing.** When `reconcile_ddl: true` and the probe finds an existing table, the DDL contains ALTER / REVIEW blocks; not documented. |
| Target-system grouping | **Missing.** `artefact_groups()` in framework.py groups files by target system (DDL → Databricks, DML → SQL Server, xlsx → Review, md → Notes); this structure is not reflected in ADDITION.md. |
| `config_inserts.xlsx` | **Explained wrongly.** Says "the generated INSERT statement … as the final column" — but it also says "Run only after approval, through the client's existing ADF metadata path. Plain INSERTs." This is correct for the xlsx but doesn't mention the `.sql` files that ARE the actual insert scripts. |

### Convention or bug

**Bug (documentation completeness).** The template in `framework.py` (`_ADDITION_TEMPLATE`) was written before DML emission (M4) and was not updated when DML was added (M7 step 3). The DML files, side-table DDL, candidates, environment grouping, and REVIEW blocks were added in M7–M10 but the template was not extended.

### Proposed fix

Extend `_ADDITION_TEMPLATE` in `framework.py` to:
1. Dynamically list all files in `framework/` (not a hardcoded table).
2. Group them by target system using `artefact_groups()`.
3. Explain the per-environment DML concept.
4. Mention the `ddl/` side-tables and `candidates/`.
5. Document the REVIEW-block concept when `reconcile_ddl` is active.

### Tests / goldens that would change

No golden depends on ADDITION.md content (it is not byte-compared). The change
is documentation only; existing tests pass.


---

## 5. Other contradictions: "stage may be STRING, standard is typed" and "every value is transcribed or flagged"

### Gate findings

The existing gate (`gate/preflight.py`, `gate/derivations.py`, `gate/drag_fill.py`)
checks for:
- Debug patterns, ruff, secrets, test coverage
- IIG derivation correctness (names, paths, SQL literals, three-part names)
- Drag-fill suspect (Decimal precision runs)
- Audit type restrictions (per profile)

**It does NOT check:**
- Whether the standard DDL types match the STTM standard band types (the
  `standard_from_stage` bypass is invisible to the gate).
- Whether a non-STRING type in the standard band was replaced by STRING.

### Grep for placeholder / synthetic values in pair-1 DDL/DML

```
out/accumulators/RFC######_ACCUM/MANIFEST.md:
  "RFC number: RFC###### (placeholder — unanswered)"
```

No `synthetic`, `syn-`, `example`, or `TBD` tokens found in the DDL or
framework output (the STTM cells are all transcribed). The `RFC######`
placeholder is correctly flagged as "unanswered" in the manifest.

The config carries `synthetic_location_prefix: "abfss://syn-container-stage@synstorage.dfs.synthetic.example"`
and the SFMC reference files use `syn-container-001@synstorage001.dfs.synthetic.example`,
but these appear only in the `edo_sfmc` two-file DDL (LOCATION clause), not in
the `acfc_prx` combined DDL (which has no LOCATION clause).

### Specific rule violations found

1. **Standard types = stage types** (Issue #2 above). The `acfc_prx` combined
   DDL violates "standard is typed" for any feed where the bands differ.

2. **No gate check for the type rule.** Adding a gate check that compares each
   standard DDL column type against the STTM contract's `standard_datatype`
   would catch this at generation time.


---

## Proposed milestone plan

| # | Item | Type | Effort | Depends on |
| --- | --- | --- | --- | --- |
| F1 | Fix `standard_from_stage` to use standard-band types for the standard DDL column types while keeping the stage column LIST | Bug fix | S | — |
| F2 | Add pair-2 golden (or a heterogeneous-type fixture) that pins standard ≠ stage types | Test | S | F1 |
| F3 | Add a gate check: standard DDL types must match STTM standard band `standard_datatype` | Gate | S | F1 |
| F4 | Extend `_ADDITION_TEMPLATE` to list all artefacts, grouped by target system, with environment and REVIEW documentation | Doc fix | M | — |
| F5 | Fix pair-2 extraction (FRD → STTM multi-file file-pattern matching) so the fixture runs end to end | Feature | M | — |
| F6 | (Optional) Add `d1` as a dev environment; wire `env_catalog_map` for per-environment catalog prefixes | Feature | L | — |
| F7 | (Optional) `ddl_layout: both` — emit combined + two-file side by side | Feature | M | — |
