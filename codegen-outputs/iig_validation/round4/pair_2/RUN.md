# Round 4 — pair_2 (SD), D1 Git folder

## Step 1: Code

```
git fetch origin                              # exit 0
git checkout feature/multi-table              # exit 0
git pull --ff-only origin feature/multi-table  # exit 0 (stash/pop for modified csv)
git rev-parse --short HEAD                    # 31609e9
```

build line: `build 31609e9 on feature/multi-table, committed 2026-10-12T13:45:57-04:00 (git)`
version: `0.5.8.post28` (>= 0.5.8.post28 ✓)

## Step 3: Run the CLI (harness)

env: `PYTHONUTF8=1 CODEGEN_FORCE_MOCK_LAYOUT=1 CODEGEN_FORCE_MOCK_PROVIDER=1
CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example
CODEGEN_STORAGE_STATE=local:/tmp/r4/state CODEGEN_STORAGE_OUTPUTS=local:/tmp/r4/out`

| # | command | exit | first line |
|---|---------|------|------------|
| 1 | `python -m codegen.cli layout --workbook <STTM> --frd <FRD> --require-complete --frd-contract-out /tmp/r4/frd.json --answers /tmp/r4/answers.yaml` | 0 | `codegen 0.5.8.post28 … profile: acfc_prx · IIG template: iig_v2 · overlays: config/overlays/acfc_env.yaml` |
| 2 | `python -m codegen.cli extract-sttm --workbook <STTM> --frd-contract /tmp/r4/frd_gen.json --out /tmp/r4/sttm_gen.json --answers /tmp/r4/answers.yaml` | 0 | `codegen 0.5.8.post28 …` |
| 3 | `python -m codegen.cli generate --frd-contract /tmp/r4/frd_gen.json --sttm-contract /tmp/r4/sttm_gen.json --output-mode framework --profile acfc_prx --iig-template iig_v2 --skip-tests --dry-run` | 0 | `codegen 0.5.8.post28 … profile: acfc_prx (--profile) · IIG template: iig_v2 (--iig-template) …` |

Results: 3 IIG xlsx, CODEGEN_BUILD.json present.
feeds 0,1 PASS_WITH_FLAGS; feed 2 FAIL (ruff E501 line-length only, derivations ok).

### Answer keys consumed by layout (14 keys; home needed 0)

**Finding:** at home on the same SHA this pair needed zero answers. In D1 all
three STTM mapping sheets have blank Schema and TableName cells, so the layout
and extract-sttm needed 14 gap answers to produce the same contract. The FRD
contract was also manually split into 3 feeds to match the 3-feed STTM (the
layout's `split_frd_feeds_by_sttm` requires at least one non-blank STTM table
cell to trigger).

Keys:

1. `feeds[1].file_name_patterns`
2. `feeds[0].frequency`
3. `feeds[0].stage_target.schema`
4. `feeds[0].standard_target.schema`
5. `feeds[0].standard_target.tables`
6. `feeds[0].stage_target.tables`
7. `feeds[1].stage_target.schema`
8. `feeds[1].standard_target.schema`
9. `feeds[1].standard_target.tables`
10. `feeds[1].stage_target.tables`
11. `feeds[2].stage_target.schema`
12. `feeds[2].standard_target.schema`
13. `feeds[2].standard_target.tables`
14. `feeds[2].stage_target.tables`

## Step 4: Diff (key-paired)

```
python tools/build_goldens.py --out /tmp/r4/goldens_dir   # exit 0
python tools/iig_diff.py --golden <pair_2 golden> --agent <3 IIG xlsx> --out /tmp/r4/diff  # exit 0
```

Header: `AGENT BUILD: codegen 0.5.8.post28 · build 31609e9 on feature/multi-table, committed 2026-10-12T13:45:57-04:00 (git)`
IGNORED: `INVENTORY_ID, OBJECT_ID, PIPELINE_ID, GROUP_ID, CONNECTION_ID, *_CONNECTION_ID, CREATED_BY, UPDATED_BY, CREATED_DATE, UPDATED_DATE, CRETAED_BY, CRETAED_DATE`
No "unscored".
TOTAL score: 4.6

## Step 4 (this file): Scrub, commit, push

Files committed: `RUN.md`, `score_totals.json`.
Real IDs replaced with SYN-*. No diff.xlsx, score.json, routing.csv, golden,
agent xlsx, or filled answers.yaml committed.
