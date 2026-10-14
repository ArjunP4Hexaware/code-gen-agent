# Identity-Mode Diff Report — 2026-10-13

Build `9244765` on `feature/multi-table` (0.5.8.post42).
`CODEGEN_PROVIDER=live`; default IIG template (`iig_v2`); profile `acfc_prx`.

---

## 1 — Generation Runs

### pair\_2 — <FRD> + <STTM>

| Stage | Exit | Notes |
| --- | --- | --- |
| layout | 0 | Resolved from documents (no model call). 3 feeds. |
| extract-sttm | 0 | 3 feeds extracted (86 / 267 / 46 fields). |
| generate | 0 | 3 feeds PASS\_WITH\_FLAGS. |

| Feed | Verdict | Flags | Questions |
| --- | --- | --- | --- |
| sd\_community\_demographic\_risk | PASS\_WITH\_FLAGS | 42 | 0 |
| sd\_community\_risk | PASS\_WITH\_FLAGS | 44 | 0 |
| sd\_individual\_risk | PASS\_WITH\_FLAGS | 49 | 0 |

Feed IDs: `sd_community_demographic_risk`, `sd_community_risk`, `sd_individual_risk` (3 distinct).
Model: Claude Opus 5.5 — 1 call per feed (1 failed per feed; retries succeeded).
No WARNING or layout validation-error lines.

### pair\_11 — <FRD> + <STTM>

| Stage | Exit | Notes |
| --- | --- | --- |
| layout | 0 (w/o `--require-complete`) / 3 (with) | Model call needed; 2 calls. REJECTED: model returned no JSON profile after 2 attempts. |
| extract-sttm | 3 | NOT EXTRACTED — every feed needs an answer. |
| generate | — | Not run (blocked by extract). |

Feed IDs from FRD contract: `pyxhealth_dnc_report`, `pyxhealth_outreach_report`,
`pyxhealth_engagement_billing_report`, `pyxhealth_screening_report`,
`pyxhealth_weekly_activity_report` (5 distinct real feeds) + `Table_Details`
(metadata sheet, 9 UNRESOLVED roles — not a real feed).

**22 open questions:**

* 5 × `feeds[N].file_name_patterns` — no unique file-to-feed match; candidates offered
* 6 × `feeds[N].file_format` — FRD says "Text files", STTM says "csv"; disagree
* 9 × `Table_Details` UNRESOLVED roles (field\_name, schema, table, column, target\_type × stage + standard)
* 1 × `feeds[5].stage_target.tables` — every stage TableName cell blank
* 1 × `feeds[5].file_name_patterns` — no match

WARNING lines:

* `REJECTED  sttm : model: no JSON profile after 2 attempt(s); last error: Expecting value: line 1 column 1 (char 0)`
* 9 × `UNRESOLVED  Table_Details/<band>/<role>`

### pair\_12 — <FRD> + <STTM>

| Stage | Exit | Notes |
| --- | --- | --- |
| layout | 0 | Resolved from documents (no model call). 1 feed. |
| extract-sttm | 0 | 1 feed extracted (115 fields). |
| generate | 0 | 1 feed PASS\_WITH\_FLAGS. |

| Feed | Verdict | Flags | Questions |
| --- | --- | --- | --- |
| ext\_tpl\_caqh\_dtl | PASS\_WITH\_FLAGS | 46 | 0 |

Feed IDs: `ext_tpl_caqh_dtl` (1 distinct).
Model: Claude Opus 5.5 — 5 calls.
No WARNING or layout validation-error lines.

---

## 2 — Identity Diffs

### pair\_2 vs <IIG> (6 golden GROUP\_IDs → combined golden)

**Default scope (`feeds`) — 1.3 s:**

| Sheet | Paired (identity / position) | Unpaired (golden / agent) | Score | Exact | Normalized | Mismatch | OOS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EMAIL\_TEMPLATE\_CONFIG | 6 / 0 | 0 / 0 | 7.4 | 12 | 0 | 6 | 0 |
| adls\_delta\_ingestion\_details | 3 / 0 | 0 / 0 | 94.7 | 104 | 21 | 1 | 0 |
| ALL\_FILES → FILE\_ADLS | 3 / 0 | 0 / 0 | **100.0** | 6 | 0 | 0 | 0 |
| data\_factory\_pipeline\_schedule | 6 / 0 | 0 / 0 | 15.6 | 18 | 12 | 12 | 0 |
| data\_quality\_rules | 0 / 0 | 0 / 0 | 0.0 | 0 | 0 | 0 | 0 |
| databricks\_notebook\_details | 6 / 0 | 0 / 0 | 40.0 | 24 | 0 | 0 | 0 |
| stgdelta\_stddelta\_ingestion\_det | 3 / 0 | 0 / 0 | 89.7 | 69 | 9 | 3 | 0 |
| ADLS\_FIXED\_WIDTH\_HANDLER | 0 / 0 | 0 / 0 | — | 0 | 0 | 0 | 0 |
| **Total** | | | **38.8** | **233** | **42** | **22** | **0** |

**Scope `all` — 1.3 s:**

Identical to default scope. The combined golden carries only rows belonging to the
3 feeds the agent generated; `--scope all` adds zero out-of-scope rows.

**Difference between scopes:** 0 rows. The agent did not drop any files —
the golden's ALL\_FILES sheet has 3 rows (one per feed) and all 3 are
covered. The `ALL_FILES_STATIC_INFORMATION → FILE_ADLS_INGESTION_DETAILS`
mapped row scored **100.0** (3 golden, 3 agent, 3 paired by identity,
exact=6, normalized=0, mismatch=0).

### pair\_11 vs <IIG>

**Cannot diff.** Generation was blocked at `extract-sttm` (exit 3, 22 open questions).
No agent IIG workbook was produced.

### pair\_12 vs <IIG> — 1.6 s

| Sheet | Paired (identity / position) | Unpaired (golden / agent) | Score | Exact | Normalized | Mismatch | OOS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DATA\_FACTORY\_PIPELINE\_SCHEDULE | 2 / 0 | 0 / 0 | 9.3 | 6 | 4 | 4 | 0 |
| ADLS\_DELTA\_INGESTION\_DETAILS | 18 / 0 | 0 / 0 | 74.5 | 428 | 162 | 166 | 0 |
| STGDELTA\_STDDELTA\_INGESTION\_DET | 3 / 0 | 0 / 0 | 58.6 | 42 | 9 | 24 | 0 |
| DATA\_QUALITY\_RULES | 0 / 0 | 0 / 0 | 0.0 | 0 | 0 | 0 | 0 |
| DATABRICKS\_NOTEBOOK\_DETAILS | 2 / 0 | 0 / 0 | 40.0 | 8 | 0 | 0 | 0 |
| EMAIL\_TEMPLATE\_CONFIG | 2 / 0 | 0 / 0 | 14.3 | 4 | 0 | 2 | 0 |
| ALL\_FILES → FILE\_ADLS | 0 / 0 | 0 / 0 | 0.0 | 0 | 0 | 0 | 0 |
| ADLS\_FIXED\_WIDTH\_HANDLER | 0 / 0 | 0 / 0 | — | 0 | 0 | 0 | 0 |
| **Total** | | | **42.1** | **488** | **175** | **196** | **0** |

---

## 3 — Summary

| Pair | Feeds | Generate | Comparable Score | Identity Pairs | Scope Difference |
| --- | --- | --- | --- | --- | --- |
| pair\_2 | 3 | PASS\_WITH\_FLAGS ×3 | 38.8 % | 27 / 0 position | 0 rows (scopes identical) |
| pair\_11 | 5 (+1 metadata) | blocked (22 Qs) | — | — | — |
| pair\_12 | 1 | PASS\_WITH\_FLAGS ×1 | 42.1 % | 27 / 0 position | N/A (single scope run) |
