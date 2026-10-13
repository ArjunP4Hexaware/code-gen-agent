# App demo checklist — SD pair (pair_2), src = fff4f57

Home proof (2026-10-13, mock env, same build, home documents): App path == CLI path — every
`framework/` + `ddl/` file of the 3 feeds (the `*_IIG.xlsx` included) byte-identical to round 7's
CLI chain; selection 1.0 s, FRD auto-paired (`pairing_map`), a second POST of it = 200 `joined`.

1. **Redeploy.** D1 Git folder: `git pull --ff-only origin feature/multi-table` →
   `python scripts/stamp_build.py` (the App gets no `.git`; the stamp `src/codegen/_build.py` is
   untracked, never committed) → `databricks apps deploy <app> --source-code-path <Git folder>`
   (or Deploy in the UI). `app.yaml` runs `python -m ui.backend.main`, its env names the four
   storage roots; `ui/frontend/dist` is current (`index-BWkpBi1E.js` = a fresh build).
2. **Health line.** `GET /api/health/facts` → `health_line`: `0.5.8.post33`, `build <sha> on
   feature/multi-table … (stamp)`, overlays `config/overlays/acfc_env.yaml`, startup error none.
   No stamp → `build unknown … src tree 93a0395502fc` = fff4f57's `src/` (`git rev-parse
   fff4f57:src`). Any other tree = stale code: STOP.
3. **Live.** `GET /api/demo/live-available` → `available: true`, `databricks_fmapi` (the App's
   principal needs CAN_QUERY on the serving endpoint).
4. **Choose.** Generate → Choose documents… → the SD STTM of **61,141 B** (never the blank-cell
   copy); every step done, FRD chip auto-paired, no VDD. **Selection sticks** (running / 409):
   `DELETE /api/demo/workbook` (the chooser's Clear), choose again.
5. **Generate.** Framework on (profile `acfc_prx`, IIG `iig_v2` = defaults) → Generate → confirm.
6. **Dashboard.** 3 feeds PASS_WITH_FLAGS, 1 pending Layer-2 candidate each in the review queue;
   model usage: layout "Resolved from the documents (no model call needed)", Layer 2 the
   endpoint · N call(s); each feed's `framework/` has `_IIG.xlsx`, `_IIG_REVIEW.xlsx`,
   `metadata_inserts.sql`.
7. **D1 proof (App == round-7 CLI).** `python scripts/doc_fingerprint.py --json <outputs
   root>/demo_<ts>/*/framework/*_IIG.xlsx > /tmp/app.json`; the same over
   `/tmp/r7/push.work/out/*/framework/*_IIG.xlsx > /tmp/cli.json` (gone → re-run
   `GENIE_RUN_pair_2_r7.md` step 3); `--compare /tmp/cli.json /tmp/app.json` → no HARD line.
