# RUN_v072_all_pairs — v0.7.2 Full Pair Evaluation

> **Version**: 0.7.2-acfc (commit 6b2d9ac on staging, ed95cd5 merge on acfc-local)
> **Deployment**: App `codegen-agent` deployment `01f1b659339c1fa0815e7792a699e662` (SNAPSHOT from acfc-local)
> **Generation options**: framework mode, acfc_prx conventions, iig_v2 template, VDD attached
> **Pairs evaluated**: 1–10 (workspace inputs role)
> **Scrub rule**: every file name, sheet name, vendor, feed, table, schema, catalog,
>   column and person that is a business term → `<TOKEN_n>`; structural words stay.

---

## Token Table

| Token | Category | Scope |
| --- | --- | --- |
| `<TOKEN_1>` | file | pair 1 STTM |
| `<TOKEN_2>` | file | pair 1 FRD |
| `<TOKEN_3>` | file | pair 1 VDD |
| `<TOKEN_4>` | file | pair 2 STTM |
| `<TOKEN_5>` | file | pair 2 FRD |
| `<TOKEN_6>` | file | pair 2 VDD |
| `<TOKEN_7>` | file | pair 3 STTM |
| `<TOKEN_8>` | file | pair 3 FRD |
| `<TOKEN_9>` | file | pair 3 VDD |
| `<TOKEN_10>` | file | pair 4 STTM |
| `<TOKEN_11>` | file | pair 4 FRD |
| `<TOKEN_12>` | file | pair 4 VDD |
| `<TOKEN_13>` | file | pair 5 STTM |
| `<TOKEN_14>` | file | pair 5 FRD |
| `<TOKEN_15>` | file | pair 5 VDD |
| `<TOKEN_16>` | file | pair 6 STTM |
| `<TOKEN_17>` | file | pair 6 FRD |
| `<TOKEN_18>` | file | pair 6 VDD |
| `<TOKEN_19>` | file | pair 7 STTM |
| `<TOKEN_20>` | file | pair 7 FRD |
| `<TOKEN_21>` | file | pair 7 VDD |
| `<TOKEN_22>` | file | pair 8 STTM |
| `<TOKEN_23>` | file | pair 8 FRD |
| `<TOKEN_24>` | file | pair 8 VDD |
| `<TOKEN_25>` | file | pair 9 STTM |
| `<TOKEN_26>` | file | pair 9 FRD |
| `<TOKEN_27>` | file | pair 9 VDD |
| `<TOKEN_28>` | file | pair 10 STTM |
| `<TOKEN_29>` | file | pair 10 FRD |
| `<TOKEN_30>` | file | pair 10 VDD |
| `<TOKEN_31>` | sheet | pair 1 mapping |
| `<TOKEN_32>` | sheet | pair 5 mapping |
| `<TOKEN_33>` | sheet | pair 7 mapping |
| `<TOKEN_34>` | sheet | pair 8 mapping |
| `<TOKEN_35>` | sheet | pair 10 outbound |
| `<TOKEN_36>` | sheet | pair 10 inbound OH |
| `<TOKEN_37>` | sheet | pair 10 inbound LA adult |
| `<TOKEN_38>` | sheet | pair 10 inbound LA child |
| `<TOKEN_39>` | sheet | pair 1 crosswalk |
| `<TOKEN_40>` | sheet | pair 1 version |
| `<TOKEN_41>` | sheet | VDD files tab |
| `<TOKEN_42>` | sheet | pair 1 VDD fields |
| `<TOKEN_43>` | vendor | pairs 1,3,4,6 |
| `<TOKEN_44>` | vendor | pair 2 |
| `<TOKEN_45>` | vendor | pair 5 |
| `<TOKEN_46>` | vendor | pair 5 |
| `<TOKEN_47>` | vendor | pairs 3,6 |
| `<TOKEN_48>` | vendor | pair 7 |
| `<TOKEN_49>` | vendor | pair 9 |
| `<TOKEN_50>` | vendor | pair 10 |
| `<TOKEN_51>` | vendor | reference |
| `<TOKEN_52>` | vendor | pair 7 org |
| `<TOKEN_53>` | vendor | pair 5 org |
| `<TOKEN_54>` | vendor | pair 10 org |
| `<TOKEN_55>` | project | pairs 1,3,4,6 |
| `<TOKEN_56>` | ticket | pairs 1,3,4,6 |
| `<TOKEN_57>` | project | pair 2 |
| `<TOKEN_58>` | project | pair 2 |
| `<TOKEN_59>` | ticket | pair 5 |
| `<TOKEN_60>` | ticket | pair 7 |
| `<TOKEN_61>` | project | pair 8 |
| `<TOKEN_62>` | ticket | pair 8 |
| `<TOKEN_63>` | project | pair 9 |
| `<TOKEN_64>` | project | pair 9 |
| `<TOKEN_65>` | ticket | pair 9 |
| `<TOKEN_66>` | ticket | pair 10 |
| `<TOKEN_67>` | ticket | pair 10 |
| `<TOKEN_68>` | table | pair 1 feed |
| `<TOKEN_69>` | schema | pair 1 standard |
| `<TOKEN_70>` | schema | pair 1 stage |
| `<TOKEN_71>` | schema | pair 1 stage |
| `<TOKEN_72>` | artefact | pair 1 DDL |

---

## Summary

| Pair | FRD Family | Select (s) | FRD Rule | VDD Rule | Outcome | Verdict | Flags | Artefacts | Questions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | F1 | 6.0 | ticket | same_folder | DONE | FAIL | 93 | 14 | 0 |
| 2 | F1 | 4.0 | name_stem | content | NEEDS_ANSWERS | — | — | — | 1 |
| 3 | F1 | 120.0 | none | none | SELECT_TIMEOUT | — | — | — | — |
| 4 | F1 | 6.0 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 2 |
| 5 | F1 | 4.0 | ticket | none | NEEDS_ANSWERS | — | — | — | 5 |
| 6 | F1 | 4.0 | ticket | content | NEEDS_ANSWERS | — | — | — | 2 |
| 7 | F1 | 4.0 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 4 |
| 8 | F2 | 6.0 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 6 |
| 9 | F2 | 6.0 | ticket | content | NEEDS_ANSWERS | — | — | — | 5 |
| 10 | F3 | 4.0 | ticket | same_folder | NEEDS_ANSWERS | — | — | — | 20 |

**Outcome legend**: DONE = ran to verdict; NEEDS_ANSWERS = layout resolution produced questions
the operator must answer before generation; SELECT_TIMEOUT = STTM selection did not complete
within 120 s (no FRD/VDD paired).

---

## Per-Pair Detail

### Pair 1

* **STTM**: `<TOKEN_1>`
* **FRD**: `<TOKEN_2>`
* **VDD**: `<TOKEN_3>`
* **FRD family**: F1 (49 fields, synonyms)
* **Select time**: 6.0 s
* **FRD pairing**: ticket (score 4, next 0; tables +3, ticket +1: both names carry <TOKEN_56>)
* **VDD pairing**: same_folder (the only VDD in the STTM's folder)

**Layout resolution**

| Document | Source | Provider Calls | Roles |
| --- | --- | --- | --- |
| STTM | synonyms | 0 | 27 |
| FRD | synonyms | 0 | 49 |
| VDD | synonyms | 0 | 21 |

* Gap fills: `feeds[0].frequency` ← "Daily" from VDD (`<TOKEN_41>!E2`)
* Layout questions: 0

**Generation** (110 s)

* **Feed**: `<TOKEN_68>`
* **Verdict**: FAIL
* **Artefact count**: 14 written files + 10 framework artefacts
* **Candidates**: 7 (all pending)
* **Outcomes**: 10 compiled rules

**Failed / not-run checks**

| Check | Status | First Line |
| --- | --- | --- |
| ruff | FAIL | (lint errors in generated code) |

**Top flag kinds**

| Flag Kind | Count |
| --- | --- |
| dml_unassigned | 10 |
| frd_unstated | 9 |
| frd_multiline | 8 |
| iig_blank | 7 |
| Layer-2 candidate pending | 7 |
| field_unmapped | 6 |
| length_is_precision | 6 |
| width_from_sttm_span | 6 |
| sibling_type_mismatch | 6 |
| vdd_missing_in_sttm | 6 |

### Pair 2

* **STTM**: `<TOKEN_4>`
* **FRD**: `<TOKEN_5>`
* **VDD**: `<TOKEN_6>`
* **FRD family**: F1
* **Select time**: 4.0 s
* **FRD pairing**: name_stem
* **VDD pairing**: content
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 5 s (halted on layout questions)

**Questions** (verbatim)

1. [choice] **File format** — `feeds[0].file_format`

### Pair 3

* **STTM**: `<TOKEN_7>`
* **FRD**: `<TOKEN_8>`
* **VDD**: `<TOKEN_9>`
* **FRD family**: F1
* **Select time**: 120.0 s
* **FRD pairing**: none
* **VDD pairing**: none
* **Outcome**: SELECT_TIMEOUT
* **Run time**: — (selection timed out at 120 s; the document parser did not return within budget)

*No questions — selection itself timed out before layout resolution.*

### Pair 4

* **STTM**: `<TOKEN_10>`
* **FRD**: `<TOKEN_11>`
* **VDD**: `<TOKEN_12>`
* **FRD family**: F1
* **Select time**: 6.0 s
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 5 s (halted on layout questions)

**Questions** (verbatim)

1. [text] **Sheet name** — `feeds[0].sheet_name`
1. [choice] **File format** — `feeds[0].file_format`

### Pair 5

* **STTM**: `<TOKEN_13>`
* **FRD**: `<TOKEN_14>`
* **VDD**: `<TOKEN_15>`
* **FRD family**: F1
* **Select time**: 4.0 s
* **FRD pairing**: ticket
* **VDD pairing**: None
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 55 s (layout resolution ran model call before halting on role questions)

**Questions** (verbatim)

1. [role] **Field name** — `<TOKEN_32>/source/field_name`
1. [role] **Schema** — `<TOKEN_32>/stage/schema`
1. [role] **Table** — `<TOKEN_32>/stage/table`
1. [role] **Column name** — `<TOKEN_32>/stage/column`
1. [role] **Target data type** — `<TOKEN_32>/stage/target_type`

### Pair 6

* **STTM**: `<TOKEN_16>`
* **FRD**: `<TOKEN_17>`
* **VDD**: `<TOKEN_18>`
* **FRD family**: F1
* **Select time**: 4.0 s
* **FRD pairing**: ticket
* **VDD pairing**: content
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 5 s (halted on layout questions)

**Questions** (verbatim)

1. [choice] **File format** — `feeds[0].file_format`
1. [choice] **File format** — `feeds[1].file_format`

### Pair 7

* **STTM**: `<TOKEN_19>`
* **FRD**: `<TOKEN_20>`
* **VDD**: `<TOKEN_21>`
* **FRD family**: F1
* **Select time**: 4.0 s
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 45 s (layout resolution ran before halting on questions)

**Questions** (verbatim)

1. [role] **Schema** — `<TOKEN_33>/standard/schema`
1. [text] **Sheet name** — `feeds[0].sheet_name`
1. [choice] **File format** — `feeds[0].file_format`
1. [choice] **Load frequency** — `feeds[0].frequency`

### Pair 8

* **STTM**: `<TOKEN_22>`
* **FRD**: `<TOKEN_23>`
* **VDD**: `<TOKEN_24>`
* **FRD family**: F2
* **Select time**: 6.0 s
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 70 s (layout resolution ran before halting on role questions)

**Questions** (verbatim)

1. [role] **Field name** — `<TOKEN_34>/source/field_name`
1. [role] **Source system / vendor** — `feeds[0].source_system`
1. [role] **Lines of business** — `feeds[0].lobs`
1. [role] **Domain and subdomain** — `feeds[0].domain`
1. [role] **Stage load strategy** — `feeds[0].stage_target.load_strategy`
1. [role] **Standard load strategy** — `feeds[0].standard_target.load_strategy`

### Pair 9

* **STTM**: `<TOKEN_25>`
* **FRD**: `<TOKEN_26>`
* **VDD**: `<TOKEN_27>`
* **FRD family**: F2
* **Select time**: 6.0 s
* **FRD pairing**: ticket
* **VDD pairing**: content
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 35 s (layout resolution ran before halting on role questions)

**Questions** (verbatim)

1. [role] **Source system / vendor** — `feeds[0].source_system`
1. [role] **Lines of business** — `feeds[0].lobs`
1. [role] **Domain and subdomain** — `feeds[0].domain`
1. [role] **Stage load strategy** — `feeds[0].stage_target.load_strategy`
1. [role] **Standard load strategy** — `feeds[0].standard_target.load_strategy`

### Pair 10

* **STTM**: `<TOKEN_28>`
* **FRD**: `<TOKEN_29>`
* **VDD**: `<TOKEN_30>`
* **FRD family**: F3
* **Select time**: 4.0 s
* **FRD pairing**: ticket
* **VDD pairing**: same_folder
* **Outcome**: NEEDS_ANSWERS
* **Run time**: 80 s (layout resolution ran before halting on 20 questions across 4 feeds)

**Questions** (verbatim)

1. [role] **Field name** — `<TOKEN_35>/source/field_name`
1. [role] **Field name** — `<TOKEN_36>/source/field_name`
1. [role] **Field name** — `<TOKEN_37>/source/field_name`
1. [role] **Field name** — `<TOKEN_38>/source/field_name`
1. [text] **Source system / vendor** — `feeds[0].source_system`
1. [text] **Lines of business** — `feeds[0].lobs`
1. [text] **Stage load strategy** — `feeds[0].stage_target.load_strategy`
1. [text] **Standard load strategy** — `feeds[0].standard_target.load_strategy`
1. [choice] **File format** — `feeds[0].file_format`
1. [choice] **Delimiter** — `feeds[0].delimiter`
1. [choice] **Load frequency** — `feeds[0].frequency`
1. [choice] **File format** — `feeds[1].file_format`
1. [choice] **Delimiter** — `feeds[1].delimiter`
1. [choice] **Load frequency** — `feeds[1].frequency`
1. [choice] **File format** — `feeds[2].file_format`
1. [choice] **Delimiter** — `feeds[2].delimiter`
1. [choice] **Load frequency** — `feeds[2].frequency`
1. [choice] **File format** — `feeds[3].file_format`
1. [choice] **Delimiter** — `feeds[3].delimiter`
1. [choice] **Load frequency** — `feeds[3].frequency`
