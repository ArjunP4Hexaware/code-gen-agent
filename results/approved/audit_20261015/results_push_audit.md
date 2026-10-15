# Results Push Audit — 2026-10-15

## Step 1: Files removed from acfc-results

| Run | Real Hits | Reason |
| --- | --- | --- |
| run_20261005T161040Z_39653aa | NONE | no leak_hits.jsonl |
| run_20261007T133343Z_d8b2f29 | NONE | no leak_hits.jsonl |
| run_20261007T141416Z_d8b2f29 | NONE | no leak_hits.jsonl |
| run_20261007T154055Z_50a510e | NONE | no leak_hits.jsonl |
| run_20261007T160108Z_ca6bab8 | NONE | no leak_hits.jsonl |
| run_20261007T170530Z_ca6bab8 | NONE | no leak_hits.jsonl |
| run_20261007T173055Z_2c3c6d4 | NONE | no leak_hits.jsonl |
| run_20261007T183106Z_9da340a | NONE | no leak_hits.jsonl |
| run_20261008T130107Z_be38f05 | NONE | no leak_hits.jsonl |
| run_20261013T180056Z_490e089 | NONE | no leak_hits.jsonl |
| run_20261013T202059Z_24b97f6 | NONE | no leak_hits.jsonl |
| run_20261013T213101Z_c35da62 | NONE | no leak_hits.jsonl |
| run_20261014T130120Z_cd56673 | NONE | no leak_hits.jsonl |
| run_20261014T142054Z_e3689b0 | NONE | no leak_hits.jsonl |
| run_20261014T151053Z_cbfab42 | NONE | no leak_hits.jsonl |
| run_20261014T201058Z_7e45d96 | NONE | no leak_hits.jsonl |
| run_20261015T022412Z_5ae6644 | NONE | no leak_hits.jsonl |
| run_20261015T061147Z_97fe673 | 40 | real hits (pre-gate) |
| run_20261015T065841Z_97fe673 | 40 | real hits (pre-filter) |
| run_20261015T073632Z_97fe673 | 24 | real hits (no wordfreq) |
| run_20261015T074546Z_97fe673 | 13 | real hits (pre-all-words) |
| run_20261015T083528Z_97fe673 | 6 | real hits (bad answers) |
| run_20261015T130059Z_7620649 | 2 | real hits |
| run_20261015T082440Z_1e2f813 | 0 | wrong SHA (post53) |

Total removed: 66 files across 24 runs.

## Step 2: Gate-controlled push

Push now routes through `results/approved/<run>/` (CLEAN or self-redacted)
vs `results/held/<run>/` (gitignored, never leaves ACFC).
`git add` stages only `results/approved/` and `results/.gitignore`.
Refuses to push if any approved run lacks a sibling `leak_hits.jsonl` with
`real_hits == 0` after redaction.

## Step 3: Pre-push scrub

Before `git push`, the harness runs the static denylist and dictionary
filter over all staged text (`.md` and `.json` in the approved lane).
Any hit aborts the push.

## Step 4: Run labelling

Each run folder is named `run_<timestamp>_<sha>` where `<sha>` is the
7-char prefix from the codegen package version actually used (read from
`.run_sha.txt` at clone time), not from the Git folder's HEAD.
