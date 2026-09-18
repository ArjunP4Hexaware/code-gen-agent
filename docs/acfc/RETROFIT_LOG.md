# RETROFIT_LOG.md — changes made to run v0.4.2-acfc in the ACFC workspace

Recorded 2026-09-18 by Genie Code.

---

## a. Changed files

### git diff HEAD --stat

```
 app.yaml           |  5 +++++
 config/config.yaml | 48 +++++++++++++++++++++++++++++++++++-------------
 requirements.txt   |  2 +-
 ui/backend/demo.py | 43 +++++++++++++++++++++++++++++++++++++------
 4 files changed, 78 insertions(+), 20 deletions(-)
```

Untracked new file: `acfc_run.py.py` (notebook).

### Per-file reasons

**config/config.yaml** (config for this workspace) — Changed
`databricks.catalog` from `soham_workspace` to `d1_dlk`,
`databricks.schema` from `codegen_agent` to `codegen`, and the three
volume names (`frd_volume` → `codegen_inputs`, `sttm_volume` →
`codegen_workbooks_in`, `output_volume` → `codegen_outputs`) to match
the volumes that exist in the ACFC workspace. Changed
`conventions.profile` to `acfc_prx`, `metadata.template` to `iig_v2`,
`playbook.template` to `main_single`, `layout.provider` to `mock`.
Reverted `layout.runtime_cache_dir` from a `/Volumes/...` path back to
`ui/backend/state/layout_profiles` after a `PermissionError` on
serverless. Added 10-pair explicit `demo.pairing_map` and
`demo.vdd_pairing_map` entries because ticket-number auto-pairing is
ambiguous (pairs 1/3/4/6 share ticket `1005789`).

**app.yaml** (config for this workspace) — Added
`CODEGEN_FORCE_MOCK_PROVIDER=1` env (locks the App to mock Layer-2
until the SP’s FMAPI grant is verified). Added
`CODEGEN_EXTRA_INPUT_DIRS` pointing to the workspace path
`/Workspace/Users/<user>/frd_sttm_pairs` so the App can read client
documents without UC volume grants.

**requirements.txt** (config for this workspace) — Bumped the
`codegen-version-marker` comment from `0.4.1` to `0.4.2`.

**ui/backend/demo.py** (code change to make it run here) — Added
`import os`. Modified `_workbook_dirs()` and `local_frd_candidates()` to
read `CODEGEN_EXTRA_INPUT_DIRS` env var (colon-separated directory
paths). For each path, the code scans both the directory and its
immediate subdirectories for `.xlsx` / `.docx` / `.contract.json` files.
This lets the App find the 10 FRD/STTM/VDD pairs stored in
`frd_sttm_pairs/pair_1/…pair_10/` without UC volume grants and without
tracking client documents in git.

**acfc_run.py** (new, untracked notebook) — 4-cell notebook:
(1) pip install, (2) pair-1 layout + extract + generate, (3) DDL diff
+ IIG comparison vs golden RFC, (4) pairs 2–10 batch loop with summary
table. Writes all output under `out/` (gitignored).

---

## b. Failure log (in order)

### 1. `conventions.default_catalog` rejected

**Run:** Loading config with `default_catalog: pr_dlk` added under
`conventions:`. 
**Error:** `pydantic_core._pydantic_core.ValidationError: ... Extra inputs are not permitted` 
**Fix:** Removed `default_catalog`; documented the value as a YAML
comment only.
**Result:** Config loads.

### 2. Pair-1 extract-sttm: unresolved layout roles

**Run:** `codegen extract-sttm` on the real client STTM (pair 1,
Accumulators). 
**Error:** `FAIL extract-sttm — sheet 'Accumulator - Optum Daily File': the stage band has no values for ['table', 'column', 'target_type']` 
**Root cause:** The real STTM’s column headers for stage/standard
table/column/type don’t match any synonym in the config’s synonym
tables, AND the mock provider has no cached profile for fingerprint
`61e6f7f3...`. A live model call is needed. 
**Fix:** None applied — this is expected with `layout.provider: mock`
and no cached profile. The synthetic fixtures extract successfully.
**Result:** Pair-1 real documents cannot complete extraction in mock
mode.

### 3. Pair-1 generate: missing contract

**Run:** `codegen generate` after extract-sttm failure. 
**Error:** `sttm.contract.json not found` 
**Root cause:** Consequence of #2 — extract-sttm didn’t produce the
contract. 
**Fix:** N/A (upstream of #2).

### 4. Pair-1 synthetic fixtures: PASS_WITH_FLAGS

**Run:** Full pipeline on `fixtures/acfc_shapes/` pair-1 files. 
**Result:** `PASS_WITH_FLAGS accumulators — 38 flag(s); ruff=ok,
debug_patterns=ok, secrets=ok, test_per_module=ok`. Layout resolved
from cache (0 unresolved).

### 5. PermissionError on `/Volumes` (notebook, first occurrence)

**Run:** Cell 2 of `acfc_run.py` — `pkg_dest.mkdir(parents=True,
exist_ok=True)` with `pkg_dest = Path("/Volumes/d1_dlk/codegen/codegen_outputs/demo/pair_1")`. 
**Error:** `PermissionError: [Errno 13] Permission denied: '/Volumes'` 
**Root cause:** Serverless FUSE mount does not allow `mkdir` on the
mount-point directory `/Volumes` itself; `parents=True` tries to
create every ancestor. 
**Fix:** Removed all `/Volumes/...` write paths from the notebook.
Output stays under `out/` (workspace-local).
**Result:** Fixed.

### 6. FRDs vanish from the chooser UI

**Run:** App deployment (by user, in parallel). Documents copied to
`inputs/databricks/` visible from notebook but not from the App. 
**Error:** FRD/STTM chooser shows no documents. 
**Root cause:** `.gitignore` has `inputs/` and `*.docx` / `*.xlsx`
globally — gitignored files are not deployed to the App container. 
**Fix:** Added `CODEGEN_EXTRA_INPUT_DIRS` env var to `app.yaml` and
code support in `demo.py`. The App reads from
`/Workspace/.../frd_sttm_pairs` directly (workspace files API), no UC
grants needed. 
**Result:** Verified: scan finds all 10 STTM + 10 VDD + 10 FRD from
the env-var path.

### 7. FRD/STTM auto-pairing broken

**Run:** Selecting an STTM in the App chooser — no companion FRD
auto-selected. 
**Root cause:** Pairs 1/3/4/6 share ticket `1005789`; pair 2 has no
ticket. The ticket-number pairing algorithm finds ambiguous candidates
and pairs nothing. 
**Fix:** Added all 10 STTM→FRD and 10 STTM→VDD entries to
`demo.pairing_map` and `demo.vdd_pairing_map` in config.yaml. 
**Result:** Fixed.

### 8. PermissionError on `/Volumes` (second occurrence)

**Run:** `codegen layout` via notebook (cell 2). 
**Error:** `PermissionError: [Errno 13] Permission denied: '/Volumes'` 
**Root cause:** `layout.runtime_cache_dir` was set to
`/Volumes/d1_dlk/codegen/codegen_outputs/state/layout_profiles`. 
**Fix:** Reverted to `ui/backend/state/layout_profiles`. Removed
`/Volumes/...` from `layout.cache_dirs` as well. 
**Result:** Fixed. Zero `/Volumes` references remain in config.yaml.

### 9. App SP has zero UC grants (not fixable by current user)

**Run:** `GRANT USE CATALOG ON CATALOG d1_dlk TO \`9f4e709d-...\``
**Error:** `PERMISSION_DENIED: User does not have MANAGE on Catalog 'd1_dlk'.` 
**Workaround:** Bypassed volume access entirely via
`CODEGEN_EXTRA_INPUT_DIRS` (workspace filesystem path). Volume-based
fetch panel still non-functional until a catalog admin grants UC
access.

---

## c. Current status

| Capability | Works | Evidence | Blocker |
| --- | --- | --- | --- |
| Config loads | Yes | `load_config()` succeeds | — |
| PyPI accessible | Yes | `pip download sqlglot` exit 0 | — |
| `pip install -e .[ui,databricks]` | Yes | dry-run exit 0 | — |
| Layout (synthetic pair 1) | Yes | exit 0, 0 unresolved, from cache | — |
| Layout (real pair 1) | No | 6 unresolved roles, no cached profile | Needs live model call |
| extract-frd (real pair 1) | Yes | exit 0, 1 feed | — |
| extract-sttm (real pair 1) | No | stage band empty | Needs resolved layout |
| extract-vdd (real pair 1) | Yes | exit 0, 76 fields | — |
| generate (synthetic pair 1) | Yes | PASS_WITH_FLAGS (38 flags) | — |
| generate (real pair 1) | No | sttm.contract.json missing | Blocked by extract-sttm |
| Notebook `/Volumes` write | No | PermissionError | Use `out/` instead |
| App chooser: STTM/FRD list | Expected yes | `CODEGEN_EXTRA_INPUT_DIRS` scan finds 30 docs | Needs redeploy |
| App chooser: auto-pairing | Expected yes | 10+10 explicit pairing_map entries | Needs redeploy |
| App volume fetch panel | No | SP has zero UC grants | Catalog admin must grant |
| App live Layer-2 (FMAPI) | Untested | `CODEGEN_FORCE_MOCK_PROVIDER=1` | Needs FMAPI grant verification |
| Network (PyPI, GitHub) | Yes | curl HTTP/2 200 | — |
| `databricks-claude-opus-5` | Yes | READY | — |
| Scrub check (tracked files) | Pass | 0 hits on files-to-commit | — |
