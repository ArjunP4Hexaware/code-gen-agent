# Generation report — cv_community_demographic_risk

## Contracts

- FRD: `demo_frd feed-level mapping contract` — sha256 `c54a585bea6b4fddb7f6d10a03030b981c1303a3acc8e71306ee75cf75e528b3`
- STTM: `STTM mapping contract extracted from demo_sttm_cv_golden.xlsx` — sha256 `ca18bee62d92c8218b48a39d8543df60687c61fe6a6ff6072df3636dae7f6cb6`

## Files emitted

- `cv_community_demographic_risk/ddl/stg_sdh.cv_community_demographic_risk.sql`
- `cv_community_demographic_risk/ddl/stg_sdh.cv_community_demographic_risk_errors.sql`
- `cv_community_demographic_risk/ddl/stg_sdh.cv_community_demographic_risk_processed_files.sql`
- `cv_community_demographic_risk/ddl/sdh.cv_community_demographic_risk.standard.sql`
- `cv_community_demographic_risk/pipeline/__init__.py`
- `cv_community_demographic_risk/pipeline/feed_spec.py`
- `cv_community_demographic_risk/pipeline/masking.py`
- `cv_community_demographic_risk/pipeline/reader.py`
- `cv_community_demographic_risk/pipeline/drift.py`
- `cv_community_demographic_risk/pipeline/mapping.py`
- `cv_community_demographic_risk/pipeline/audit.py`
- `cv_community_demographic_risk/pipeline/rejects.py`
- `cv_community_demographic_risk/pipeline/writer.py`
- `cv_community_demographic_risk/pipeline/dq.py`
- `cv_community_demographic_risk/pipeline/run_report.py`
- `cv_community_demographic_risk/pipeline/orchestrator.py`
- `cv_community_demographic_risk/job/workflow.json`
- `cv_community_demographic_risk/job/notebook_entrypoint.py`
- `cv_community_demographic_risk/tests/conftest.py`
- `cv_community_demographic_risk/tests/test_feed_spec.py`
- `cv_community_demographic_risk/tests/test_masking.py`
- `cv_community_demographic_risk/tests/test_reader.py`
- `cv_community_demographic_risk/tests/test_drift.py`
- `cv_community_demographic_risk/tests/test_mapping.py`
- `cv_community_demographic_risk/tests/test_audit.py`
- `cv_community_demographic_risk/tests/test_rejects.py`
- `cv_community_demographic_risk/tests/test_writer.py`
- `cv_community_demographic_risk/tests/test_dq.py`
- `cv_community_demographic_risk/tests/test_run_report.py`
- `cv_community_demographic_risk/tests/test_orchestrator.py`
- `cv_community_demographic_risk/tools/make_fixtures.py`
- `cv_community_demographic_risk/ruff.toml`
- `cv_community_demographic_risk/README.md`
- `cv_community_demographic_risk/cv_community_demographic_risk.ipynb`

## Validation rules

| # | Classification | Feature | Rule | Grounding | Notes |
|---|---|---|---|---|---|
| 1 | unmapped |  | If the ZIP_CODE column is NULL, then we are rejecting the record and moving it to the reject table from the below files. | If the ZIP_CODE column is NULL, then we are rejecting the record and moving it to the reject table from the below files. | no deterministic template matches — sent to Layer 2 for a reviewed candidate |

## Layer-2 candidates (review required — never auto-merged)

### Candidate 1 (anthropic, grounded)

- Rule: If the ZIP_CODE column is NULL, then we are rejecting the record and moving it to the reject table from the below files.
- Proposed classification: mappable
- Rationale: The rule specifies a row-level null check on a single available column: when ZIP_CODE is NULL the record is rejected and routed to a reject table. This is a deterministic filter expressible in PySpark against the zip_code column present in both source and stage columns.
- Citations:
  - > If the ZIP_CODE column is NULL, then we are rejecting the record and moving it to the reject table from the below files.

```python
df = df.withColumn("is_rejected", F.col("zip_code").isNull())
reject_df = df.filter(F.col("is_rejected"))
valid_df = df.filter(~F.col("is_rejected"))
```

## Gate

| Check | Result | Details |
|---|---|---|
| ruff | pass | ruff clean |
| debug_patterns | pass | no debug statements |
| secrets | pass | no hardcoded secrets |
| test_per_module | pass | every pipeline module has a test file |

Flags:
- Layer-2 candidate pending engineer approval: 'If the ZIP_CODE column is NULL, then we are rejecting the record and moving it to the reject table from the below files.'
- generated tests were skipped — PASS cannot be claimed

**Verdict: PASS_WITH_FLAGS**
