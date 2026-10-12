# CodeGen Agent Run — Round 2 IIG Validation Handoff

Generated: 2026-10-12
Branch: `feature/multi-table` @ `0d2203a`

---

## What's done

| # | Task | Status |
|---|------|--------|
| 1 | Git pull, verify 776f1cf + 0d2203a | ✅ 27/27 tests passing |
| 2 | 199 xlsx unzipped from UC Volumes into `docs/acfc/iig_goldens/goldens/` | ✅ |
| 3 | `tools/build_goldens.py` — 7 pair-level goldens in `goldens/` | ✅ |
| 4 | 5-cell sanity test on pair_5 → iig_diff reports exactly 5 | ✅ |
| 5 | `.gitignore` updated for `goldens/`, `agent_out/` | ✅ |

### Golden build summary

| Pair | Groups | Sheets | Rows | all_files kept / dropped | email_cfg |
|------|--------|--------|------|--------------------------|-----------|
| sfmc | 190141, 190142 | 7 | 144 | 122 / 876 | 4 |
| pair_2 | 180251–180256 | 7 | 461 | 378 / 2,616 | 12 |
| pair_5 | 2240732, 2240733 | 7 | 144 | 122 / 876 | 4 |
| pair_7 | 18603, 18604 | 7 | 146 | 122 / 876 | 8 |
| pair_8 | 4092933,34,36,37,39,40,42,43 | 8 | 18,124 | 14,528 / 0 | 16 |
| pair_9 | 2109458903, 2109458904 | 7 | 1,315 | 120 / 3,062 | 792 |
| pair_10 | 2109459103,04, 210944903,04 | 7 | 397 | 248 / 2,428 | 20 |

---

## What you run

### Credentials — already wired

`config.yaml` has `reasoning.provider: databricks_fmapi` and
`databricks.serving_endpoint: databricks-claude-opus-5`. On serverless the
SDK auto-authenticates. **No `.env` needed.**

### Pipeline per pair

```bash
# 1. Extract contracts (deterministic, no LLM)
codegen extract-frd  <FRD.docx>  > out/<pair>/frd.contract.json
codegen extract-sttm --frd out/<pair>/frd.contract.json <STTM.xlsx> > out/<pair>/sttm.contract.json

# 2. Generate (uses databricks-claude-opus-5 for Layer 2)
codegen generate \
  --frd out/<pair>/frd.contract.json \
  --sttm out/<pair>/sttm.contract.json \
  [--vdd out/<pair>/vdd.contract.json] \
  --output-mode framework \
  --profile acfc_prx \
  --iig-template iig_v2

# 3. Copy the generated IIG to agent_out/
mkdir -p agent_out/<pair>
cp out/<feed_slug>/framework/<feed>_IIG.xlsx agent_out/<pair>/<pair>_iig_agent.xlsx
```

### Pair → document mapping

| Pair | FRD (in `inputs/databricks/`) | STTM | VDD | Notes |
|------|-------------------------------|------|-----|-------|
| pair_2 | `FRD_Medicare Expansion-MIDS - Socially Determined (1).docx` | `STTM_Medicare Expansion-MIDS - Socially Determined (1).xlsx` | `VDD_Socially_Determined_MIDS.xlsx` | 3 feeds → merge into one IIG |
| pair_8 | `FRD_STG_STD_PA CHC…834_Unified_Layout_FILE (1).docx` | `STTM_PA CHC…834_Unified_Layout_FILE.xlsx` | `VDD_834_Unified_Layout.xlsx` | 8 segments × daily + monthly |
| sfmc | Not in `inputs/databricks/` — FRD_STG_STD_SFMC_1005310.docx | Need STTM | — | **You supply the docs** |
| pair_5 | ? (matched_table: `claim_medical_state_hist`) | ? | ? | **You supply** |
| pair_7 | ? (matched_table: `claim_pharmacy_state_hist`) | ? | ? | **You supply** |
| pair_9 | ? (2 groups, 91 pipeline_ids) | ? | ? | FRD cross-check: if it names maternity / db_104 / 10945909xx, stop |
| pair_10 | ? (4 groups, 16 pipeline_ids) | ? | ? | Same FRD cross-check |

**pair_2 already has outputs** in `code-gen-agent-multitable/out/`:
`sd_community_demographic_risk_IIG.xlsx`, `sd_community_risk_IIG.xlsx`,
`sd_individual_risk_IIG.xlsx` — copy or re-run.

### 4 pairs WITHOUT golden (save output only, no diff)

| Pair | Notes |
|------|-------|
| pair_1 | OptumRx Accumulators — contracts exist in `out/pair_1/` |
| pair_3 | OptumRx Facets Member Eligibility — NOT_FOUND |
| pair_4 | OptumRx PDE Edit Code — NOT_FOUND |
| pair_6 | Ignore all addendum rows (matched Facets region paths, not target) |

### Output layout

```
agent_out/
  <pair>/
    <pair>_iig_agent.xlsx     ← for the 7 with goldens
    error.txt                 ← if a run failed
```

For multi-feed pairs (pair_2 = 3 feeds, pair_8 = 16 feeds), the agent
produces one IIG per feed. Merge them into one workbook (one sheet per
table, union rows across feeds — same logic as `build_goldens.py`). Or
leave them separate and I'll merge before diffing.

---

## What happens after your runs land

I run (all scripted, waiting for `agent_out/` to be populated):

1. **iig_diff.py --batch** → `summary.md` + per-pair `score.json` + `diff.xlsx`
2. **iig_scorecard.py --all-sheets** → side-by-side with iig_diff scores
3. **routing_observed.md** — origin tags, agent accuracy per sheet/column,
   PIPELINE_ID == GROUP_ID + 200 check, pair_7 162k anomaly, RDBMS 3-hop
   shape (groups 3063/3064 as reference), pairs 1/3/4/6 absent
4. **Scrub** → `codegen-outputs/iig_validation/round2/`, commit, push

---

## Key files on disk

| File | Purpose |
|------|---------|
| `goldens/<pair>_iig_golden.xlsx` | Merged pair-level golden (the "expected") |
| `goldens/build_report.json` | Detailed merge report |
| `tools/build_goldens.py` | Golden merge script |
| `tools/iig_diff.py` | Cell-level IIG differ (776f1cf) |
| `tools/iig_keys.yaml` | Natural keys for row pairing |
| `scripts/iig_scorecard.py` | Sheet-level scorecard |
| `docs/acfc/iig_goldens/01_pair_group_index.csv` | GROUP_ID → pair mapping |
| `docs/acfc/iig_goldens_round2/01_pair_group_index_addendum.csv` | Round-2 additions |
| `docs/acfc/iig_goldens/00_table_set.csv` | IIG table catalog |
| `config/overlays/acfc_env.yaml` | ACFC environment constants |

## FRD cross-check (pair_9, pair_10)

Open each pair's FRD. List every table it describes. Compare against the
golden's sheet names.  **If the FRD names any of: maternity tables, db_104,
or the 10945909xx-generation groups — note them and stop for that pair.**
The golden was built only from the listed GROUP_IDs; an excluded table in
the FRD means the golden is intentionally incomplete.
