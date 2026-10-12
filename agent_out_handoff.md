# Round 2 IIG Validation — Handoff

Branch: `feature/multi-table`  
Date: 2026-10-12

---

## Done (committed)

- **27/27 tests** passing on `test_iig_diff.py` (commits 776f1cf + 0d2203a).
- **199 + 77 xlsx** unzipped from `d1_dlk.export` Volumes into `docs/acfc/iig_goldens/goldens/` and `iig_goldens_round2/goldens/`.
- **`tools/build_goldens.py`** — merges per-GROUP_ID xlsx into 7 pair-level goldens in `goldens/`. Drops exec_log, file_log, *_audit_log. Filters all_files_static_information by SRC_FILE_NAME. Adds EMAIL_TEMPLATE_CONFIG. 5-cell sanity test passes (exactly 5 mismatches).
- **`.gitignore`** — `goldens/`, `agent_out/`, docs subdirs.
- **FRD contracts extracted** (deterministic, in `/tmp/agent_work/<pair>/frd.contract.json`) for pair_1–7. pair_8/9/10 have non-F1/F2 FRDs the extractor can't parse.
- **pair_1 agent IIG** produced (dry-run, no golden).
- **pair_2 agent IIGs** copied from `code-gen-agent-multitable/out/` (3 feed IIGs: sd_community_demographic_risk, sd_community_risk, sd_individual_risk).

## Goldens built (in `goldens/`)

| Pair | Groups | Sheets | Rows |
|------|--------|--------|------|
| sfmc | 190141, 190142 | 7 | 144 |
| pair_2 | 180251–180256 | 7 | 461 |
| pair_5 | 2240732, 2240733 | 7 | 144 |
| pair_7 | 18603, 18604 | 7 | 146 |
| pair_8 | 4092933,34,36,37,39,40,42,43 | 8 | 18,124 |
| pair_9 | 2109458903, 2109458904 | 7 | 1,315 |
| pair_10 | 2109459103,04, 210944903,04 | 7 | 397 |

## Agent runs — what worked and what didn't

| Pair | FRD | STTM | Generate | Blocker |
|------|-----|------|----------|---------|
| pair_1 | ok | ok | ok (dry-run) | No golden — save only |
| pair_2 | ok | — | prior run | 3 feed IIGs from multitable/out/ |
| pair_3 | ok | ok | FAIL | Contract mismatch: no stage load strategy |
| pair_4 | ok | ok | FAIL | No delimiter for .xlsx format; table name mismatch |
| pair_5 | ok | FAIL | — | Segment spelling 'NA' outside vocabulary |
| pair_6 | ok | FAIL | — | Audit column DELETE_FLAG has datatype tinyint |
| pair_7 | ok | FAIL | — | Every feed needs layout answers (answers.yaml) |
| pair_8 | FAIL | — | — | FRD is not F1/F2 format |
| pair_9 | FAIL | — | — | FRD is not F1/F2 format |
| pair_10 | FAIL | — | — | FRD is not F1/F2 format |

**FMAPI note:** All calls to `databricks-claude-opus-5` failed from ephemeral serverless compute. pair_1's IIG was produced with mock Layer 2 (--dry-run). The endpoint works fine from `acfc_run.py` notebook / the App.

## What you run (to get ≥5 pairs)

Run the remaining pairs from `acfc_run.py` notebook or the App UI where "proceed with unresolved" works. The pairs most likely to succeed:

1. **pair_5** (Wellpoint) — segment 'NA' is a CLI extraction issue; the App handles it
2. **pair_7** (UHC RxClaims) — needs layout answers the App dialog provides
3. **pair_8** (834 Unified) — needs the App's F2/alternate FRD parser
4. **pair_9** (HCM PeopleSoft) — same
5. **pair_10** (BestFootForward) — same
6. **sfmc** — FRD/STTM not in `inputs/databricks/`; fetch from SharePoint

For each, save the agent IIG to:
```
agent_out/<pair>/<pair>_iig_agent.xlsx
```
For multi-feed pairs (pair_2 has 3 feeds), merge into one workbook or leave separate — the diff step handles both.

## What I run when agent outputs land

```bash
# 1. Diff
python tools/iig_diff.py --batch diff_input/ --out diff_output/

# 2. Scorecard
python scripts/iig_scorecard.py --all-sheets ...

# 3. routing_observed.md
# 4. Scrub → codegen-outputs/iig_validation/round2/
# 5. Commit + push
```

## Config reminder

- `reasoning.provider: databricks_fmapi` (config.yaml line 474)
- `databricks.serving_endpoint: databricks-claude-opus-5` (line 768)
- `conventions.profile: acfc_prx` (acfc_env.yaml)
- `metadata.template: iig_v2` (acfc_env.yaml)
- No `.env` needed from notebook/App — SDK auto-authenticates
