# Generation report — cv_individual_risk

## Contracts

- FRD: `demo_frd feed-level mapping contract` — sha256 `c54a585bea6b4fddb7f6d10a03030b981c1303a3acc8e71306ee75cf75e528b3`
- STTM: `STTM mapping contract extracted from demo_sttm_cv_golden.xlsx` — sha256 `ca18bee62d92c8218b48a39d8543df60687c61fe6a6ff6072df3636dae7f6cb6`

## Files emitted

- `cv_individual_risk/ddl/stg_care.cv_individual_risk.sql`
- `cv_individual_risk/ddl/stg_care.cv_individual_risk_errors.sql`
- `cv_individual_risk/ddl/stg_care.cv_individual_risk_processed_files.sql`
- `cv_individual_risk/ddl/stg_care.cv_individual_risk_recycle.sql`
- `cv_individual_risk/ddl/care.cv_individual_risk.standard.sql`
- `cv_individual_risk/pipeline/__init__.py`
- `cv_individual_risk/pipeline/feed_spec.py`
- `cv_individual_risk/pipeline/masking.py`
- `cv_individual_risk/pipeline/reader.py`
- `cv_individual_risk/pipeline/drift.py`
- `cv_individual_risk/pipeline/mapping.py`
- `cv_individual_risk/pipeline/audit.py`
- `cv_individual_risk/pipeline/rejects.py`
- `cv_individual_risk/pipeline/reference.py`
- `cv_individual_risk/pipeline/recycle.py`
- `cv_individual_risk/pipeline/writer.py`
- `cv_individual_risk/pipeline/dq.py`
- `cv_individual_risk/pipeline/run_report.py`
- `cv_individual_risk/pipeline/orchestrator.py`
- `cv_individual_risk/job/workflow.json`
- `cv_individual_risk/job/notebook_entrypoint.py`
- `cv_individual_risk/tests/conftest.py`
- `cv_individual_risk/tests/test_feed_spec.py`
- `cv_individual_risk/tests/test_masking.py`
- `cv_individual_risk/tests/test_reader.py`
- `cv_individual_risk/tests/test_drift.py`
- `cv_individual_risk/tests/test_mapping.py`
- `cv_individual_risk/tests/test_audit.py`
- `cv_individual_risk/tests/test_rejects.py`
- `cv_individual_risk/tests/test_reference.py`
- `cv_individual_risk/tests/test_recycle.py`
- `cv_individual_risk/tests/test_writer.py`
- `cv_individual_risk/tests/test_dq.py`
- `cv_individual_risk/tests/test_run_report.py`
- `cv_individual_risk/tests/test_orchestrator.py`
- `cv_individual_risk/tools/make_fixtures.py`
- `cv_individual_risk/ruff.toml`
- `cv_individual_risk/README.md`
- `cv_individual_risk/cv_individual_risk.ipynb`

## Validation rules

| # | Classification | Feature | Rule | Grounding | Notes |
|---|---|---|---|---|---|
| 1 | unmapped |  | If the MEMBER_ID column is NULL, then we are rejecting the record and moving it to the reject table from the below file. | If the MEMBER_ID column is NULL, then we are rejecting the record and moving it to the reject table from the below file. | no deterministic template matches — sent to Layer 2 for a reviewed candidate |

## Layer-2 candidates (review required — never auto-merged)

### Candidate 1 (anthropic, grounded)

- Rule: If the MEMBER_ID column is NULL, then we are rejecting the record and moving it to the reject table from the below file.
- Proposed classification: mappable
- Rationale: The rule specifies a deterministic row-level null check on MEMBER_ID (available as source/stage column 'member_id') and routing failing rows to a reject table. This is a standard mappable validation expressible as a PySpark filter, splitting NULL records off to the reject table and retaining the rest.
- Citations:
  - > If the MEMBER_ID column is NULL, then we are rejecting the record and moving it to the reject table from the below file.

```python
valid_df = df.filter(F.col('member_id').isNotNull())
reject_df = df.filter(F.col('member_id').isNull())
reject_df.write.mode('append').saveAsTable('reject_table')
```

## Gate

| Check | Result | Details |
|---|---|---|
| ruff | pass | ruff clean |
| debug_patterns | pass | no debug statements |
| secrets | pass | no hardcoded secrets |
| test_per_module | pass | every pipeline module has a test file |

Flags:
- Layer-2 candidate pending engineer approval: 'If the MEMBER_ID column is NULL, then we are rejecting the record and moving it to the reject table from the below file.'
- generated tests were skipped — PASS cannot be claimed

**Verdict: PASS_WITH_FLAGS**
