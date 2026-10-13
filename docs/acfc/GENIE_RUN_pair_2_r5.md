# Genie Code — pair_2 (SD) round 5 (D1 Git folder)
In order; stop where told. NEVER modify `src/codegen/**`, never hand-edit or split a contract,
never add an answer beyond step 3's one. Results go to `/tmp/r5/push/` (RUN.md is one of them).
0. **Fingerprint key.** `codegen-state/fingerprint.key` exists in this Git folder and is not empty
   (gitignored; Soham places it — never print, copy or commit it), else STOP.
1. **Code.** `git fetch origin` · `git checkout feature/multi-table` · `git pull --ff-only origin
   feature/multi-table`. Record `python -m codegen.cli doctor`'s `build …` line and `git rev-parse
   --short HEAD`; STOP unless the build line names that SHA `(git)`; version >= 0.5.8.post31.
2. **Fingerprint + content gate** (hashes + counts only). `<STTM>` = the FILLED workbook, never
   `*_blank_version*`. Keyed (stays in /tmp, never pushed): `python scripts/doc_fingerprint.py
   <STTM> <FRD> --json > /tmp/r5/fp_keyed.json`. Structure-only (pushed): the same + `--structure-only`
   `> /tmp/r5/push/fingerprint_d1.json`; its text form (`--structure-only`, no `--json`) into RUN.md.
   **Gate:** `python scripts/doc_fingerprint.py --compare docs/acfc/fingerprints/pair_2_sd_home.json
   /tmp/r5/fp_keyed.json > /tmp/r5/push/compare.txt`, also into RUN.md. Exit 2 (`REFUSED`, another
   key) → STOP. Exit 1 = a `HARD` line (sheet names, counts, extents, merged ranges, header
   row + hash, per-column fill; the docx `text_hash` and counts) → STOP. `WARN` lines (whole-file sha256 / size, document.xml,
   `body_hash`, per-column value hashes, with all of the above equal) are recorded and the run
   continues — the home copy is anonymised, so its cell values are expected to differ.
   Finding to record, do not investigate: `*_blank_version*` has other mapping-sheet names, a
   uniform 18-column header and no merged ranges; all five of its sheet-name hashes equal the
   repo's synthetic `fixtures/acfc_shapes/sttm/pair_2_family_b.xlsx`. It is NOT pipeline-
   generated (owner); it is not the run's `<STTM>`.
3. **Run the CLI clean.** `/tmp/r5/answers.yaml` = ONE entry, `gaps:` →
   `"feeds[1].file_name_patterns": {value: <the FILE_DETAILS file feeds 0 and 2 do not take>}`.
   env: `PYTHONUTF8=1 CODEGEN_FORCE_MOCK_LAYOUT=1 CODEGEN_FORCE_MOCK_PROVIDER=1
   CODEGEN_NOTIFICATION_EMAILS=syn.dl.prodsupport@synthetic.example
   CODEGEN_STORAGE_STATE=local:/tmp/r5/state CODEGEN_STORAGE_OUTPUTS=local:/tmp/r5/out`
   - `python -m codegen.cli layout --workbook <STTM> --frd <FRD> --require-complete
     --frd-contract-out /tmp/r5/frd.json --answers /tmp/r5/answers.yaml` — exit 3 → record
     every QUESTION / UNRESOLVED key (text up to ` — `) in RUN.md, go to step 4, skip step 5.
   - `python -m codegen.cli extract-sttm --workbook <STTM> --frd-contract /tmp/r5/frd.json
     --out /tmp/r5/sttm.json --answers /tmp/r5/answers.yaml`
   - `python -m codegen.cli generate --frd-contract /tmp/r5/frd.json --sttm-contract
     /tmp/r5/sttm.json --output-mode framework --profile acfc_prx --iig-template iig_v2
     --skip-tests --dry-run` — RUN.md: each command (`<STTM>` / `<FRD>`), exit, first line, verdicts.
4. **Golden, rebuilt on this SHA.** `python tools/build_goldens.py --out /tmp/r5/goldens`; `<G>` =
   `/tmp/r5/goldens/pair_2_iig_golden.xlsx`. Its pair_2 `dedup … -> …` lines into RUN.md (GROUP_IDs
   180251–180256 may stay); `python tools/iig_diff.py --golden <G> --golden-structure --out /tmp/r5/push`.
5. **Diff + scrubbed evidence.** `python tools/iig_diff.py --golden <G> --agent <the 3 *_IIG.xlsx,
   not *_REVIEW> --out /tmp/r5/diff --export-scrubbed /tmp/r5/push`; never `--pair-mode`.
   score.json's `totals` + per-sheet `rows` / `counts` / `score` → `/tmp/r5/push/score_totals.json`.
   In RUN.md, right under the dedup lines, one line per sheet from score.json `rows`:
   `<sheet>: agent <agent> rows · golden <golden> rows (deduped) · paired <paired>` — a row-count gap.
6. **Scrub, commit, push.** `python scripts/scrub_check.py /tmp/r5/push` must print `clean` (else
   STOP; report class counts only). `git checkout -B acfc-results origin/acfc-results`; copy
   `/tmp/r5/push/*` to `codegen-outputs/iig_validation/round5/pair_2/`; `git add` those files by
   name; `git commit -m "round5 pair_2"`; `git push origin acfc-results`; `git checkout
   feature/multi-table`. Commit compare.txt (which columns differ) and the structure-only
   fingerprint_d1.json — never /tmp/r5/fp_keyed.json or any fingerprint with `column_hashes` /
   `body_hash`, the key, diff.xlsx, score.json, routing.csv, a golden, an xlsx, the answers file
   or anything under /tmp/r5/out.
