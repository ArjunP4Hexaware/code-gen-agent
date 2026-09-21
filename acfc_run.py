# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Install codegen package
# MAGIC %pip install -e /Workspace/Users/admz-sb65923@amerihealthcaritas.com/code-gen-agent[ui,databricks]

# COMMAND ----------

# DBTITLE 1,Restart Python (required after pip install)
dbutils.library.restartPython()  # noqa: F821 — notebook global

# COMMAND ----------

# DBTITLE 1,Pair 1 — layout (live provider, --report-unresolved)
import os, subprocess, sys
from pathlib import Path

# editable install .pth not always picked up after restartPython on serverless
sys.path.insert(0, "/Workspace/Users/admz-sb65923@amerihealthcaritas.com/code-gen-agent/src")

# ---- paths (API only — never mounted /Workspace or /Volumes) ----
HOME = "/Workspace/Users/admz-sb65923@amerihealthcaritas.com"
REPO = Path(f"{HOME}/code-gen-agent")
PAIRS = Path(f"{HOME}/frd_sttm_pairs")
RFC  = Path(f"{HOME}/rfc_samples")

# Layer 2 stays mock; layout goes live (config.yaml)
os.environ["CODEGEN_FORCE_MOCK_PROVIDER"] = "1"

# propagate notebook auth to subprocesses (codegen.cli runs via subprocess)
ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()  # noqa: F821
os.environ["DATABRICKS_HOST"]  = ctx.apiUrl().get()
os.environ["DATABRICKS_TOKEN"] = ctx.apiToken().get()
# same workspace: URIs as the App (config.yaml + env override)
os.environ["CODEGEN_STORAGE_INPUTS"]  = f"workspace:{PAIRS}"
os.environ["CODEGEN_STORAGE_STATE"]   = f"workspace:{HOME}/codegen-state"
os.environ["CODEGEN_STORAGE_OUTPUTS"] = f"workspace:{HOME}/codegen-outputs"


def run_cli(*args, label="cli"):
    """Run a codegen CLI command, print output, return CompletedProcess."""
    sep = "=" * 60
    print(f"\n{sep}\n  {label}\n{sep}")
    proc = subprocess.run(
        [sys.executable, "-m", "codegen.cli", *args],
        cwd=str(REPO), text=True, capture_output=True, check=False,
    )
    if proc.stdout.strip():
        print(proc.stdout)
    if proc.stderr.strip():
        print("STDERR:", proc.stderr)
    return proc


# ---- load config + storage ----
from codegen.config import load_config
from codegen.storage import (
    open_storage, open_backend, RoleStore, default_client_factory,
)

config = load_config(REPO / "config" / "config.yaml")
stores = open_storage(config, REPO)
cf = default_client_factory(config)

# ---- fetch pair_1 via workspace API ----
pair_uri = f"workspace:{PAIRS}/pair_1"
pair_be  = open_backend(pair_uri, base_dir=REPO, client_factory=cf)
pair_rs  = RoleStore("inputs", pair_be, stores.outputs.workdir.parent / "pair_in")
local_pair = pair_rs.fetch_tree("", depth=0)

# discover documents by FRD_ / STTM_ / VDD_ prefix
sttm = frd = vdd = None
for p in sorted(local_pair.iterdir()):
    if not p.is_file():
        continue
    up = p.name.upper()
    if up.startswith("STTM"):
        sttm = p
    elif up.startswith("FRD") and p.suffix.lower() == ".docx":
        frd = p
    elif up.startswith("VDD") and p.suffix.lower() == ".xlsx":
        vdd = p
assert sttm, f"no STTM_*.xlsx in {local_pair}"
assert frd,  f"no FRD_*.docx in {local_pair}"
print(f"STTM : {sttm.name}\nFRD  : {frd.name}\nVDD  : {vdd.name if vdd else '(none)'}")

# ---- pair by content (confirm) ----
from codegen.pairing import pair_by_content

frd_cands = {p.name: p for p in local_pair.iterdir()
             if p.is_file() and p.name.lower().endswith((".docx", ".contract.json"))}
vdd_cands = {p.name: p for p in local_pair.iterdir()
             if p.is_file() and p.suffix.lower() == ".xlsx" and p != sttm}
frd_res = pair_by_content("frd", sttm, frd_cands, config, REPO)
vdd_res = pair_by_content("vdd", sttm, vdd_cands, config, REPO)
print(f"\nContent pairing — FRD: {frd_res.chosen}, VDD: {vdd_res.chosen}")

# ---- layout: live provider, --report-unresolved ----
WORK = stores.outputs.local_path("demo/pair_1")
WORK.mkdir(parents=True, exist_ok=True)

answers_file = local_pair / "answers.yaml"
answers_args = ["--answers", str(answers_file)] if answers_file.exists() else []

layout_proc = run_cli(
    "layout",
    "--workbook", str(sttm), "--frd", str(frd),
    *(["--vdd", str(vdd)] if vdd else []),
    *answers_args,
    "--report-unresolved", str(WORK / "unresolved_headers.md"),
    "--profile-out", str(WORK / "sttm.layout.json"),
    "--require-complete",
    label="layout — pair 1 (live provider)",
)

# ---- summary: source per doc, provider calls, unresolved, cross-check ----
print("\n" + "=" * 60 + "\n  PAIR 1 — LAYOUT RESULT\n" + "=" * 60)
for line in layout_proc.stdout.splitlines():
    lo = line.lower()
    if any(kw in lo for kw in ("source:", "provider", "unresolved",
                                "cross-check", "cache", "synonym",
                                "model", "flag", "call")):
        print(f"  {line.strip()}")

if layout_proc.returncode != 0:
    uh = WORK / "unresolved_headers.md"
    if uh.exists():
        print("\n" + "=" * 60 + "\n  unresolved_headers.md (verbatim)\n" + "=" * 60)
        print(uh.read_text(encoding="utf-8"))
    print("\n*** STOP — layout incomplete: write answers.yaml "
          "(ACFC_DEPLOY.md par. 6), place in the pair folder, re-run. ***")
else:
    print("\nLayout complete — all roles resolved.")

# COMMAND ----------

# DBTITLE 1,(temp) Git commit on acfc-hotfix-1 (no push)
import subprocess, os
os.chdir(str(REPO))
for cmd in [
    ["git", "status", "--short"],
    ["git", "add", "config/config.yaml", "src/codegen/extract/generic.py",
     "src/codegen/layout/resolve.py", "acfc_run.py"],
    ["git", "commit", "-m",
     "fix(extract): forward-fill band constants + log layout rejections\n\n"
     "Diagnosis: finding (a) — STTM pair_1 states schema/table as constants\n"
     "in every data row (col T='stg_pharmcy', U='orx_accum_optumrx_dly'),\n"
     "but discovery synonyms only carried 'in lakehouse'; header reads 'in DL'.\n\n"
     "Fixes:\n"
     "- config.yaml: add 'target {schema,table,column,data type} name in dl'\n"
     "- generic.py: _band_constant (forward-fill) + decouple schema gate\n"
     "- resolve.py: _log_layout_rejection to <state>/layout_rejections/"],
]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(f"$ {' '.join(cmd[:3])}{'...' if len(cmd)>3 else ''}")
    if r.stdout.strip(): print(r.stdout.strip())
    if r.stderr.strip(): print("STDERR:", r.stderr.strip())
    print()

# COMMAND ----------

# DBTITLE 1,Pair 1 — generate (acfc_prx / iig_v2 / rfc)
# ---- extract contracts ----
frd_contract = WORK / "frd.contract.json"
if frd.suffix.lower() == ".docx":
    run_cli("extract-frd", "--docx", str(frd),
            "--out", str(frd_contract),
            label="extract-frd — pair 1")
else:
    frd_contract = frd

sttm_contract = WORK / "sttm.contract.json"
run_cli("extract-sttm",
        "--workbook", str(sttm),
        "--frd-contract", str(frd_contract),
        "--out", str(sttm_contract),
        "--layout", str(WORK / "sttm.layout.json"),
        *answers_args,
        label="extract-sttm — pair 1")

vdd_contract_args = []
if vdd is not None:
    vdd_contract = WORK / "vdd.contract.json"
    run_cli("extract-vdd", "--vdd", str(vdd),
            "--out", str(vdd_contract),
            label="extract-vdd — pair 1")
    vdd_contract_args = ["--vdd", str(vdd_contract)]

# ---- generate in rfc mode ----
gen_proc = run_cli(
    "generate",
    "--frd-contract", str(frd_contract),
    "--sttm-contract", str(sttm_contract),
    *vdd_contract_args,
    "--profile", "acfc_prx",
    "--iig-template", "iig_v2",
    "--output-mode", "rfc",
    label="generate — pair 1 (acfc_prx / iig_v2 / rfc)",
)

# ---- verdict and grouped flags ----
print("\n" + "=" * 60 + "\n  PAIR 1 — GENERATION VERDICT\n" + "=" * 60)
for line in gen_proc.stdout.splitlines():
    lo = line.lower()
    if any(kw in lo for kw in ("verdict", "flag", "pass", "fail",
                                "warn", "check", "group")):
        print(f"  {line.strip()}")

# ---- push outputs ----
sent = stores.outputs.push_tree("")
print(f"\n{len(sent)} file(s) stored under {stores.outputs.uri()}" if sent
      else f"Outputs local: {stores.outputs.workdir}")

# COMMAND ----------

# DBTITLE 1,Pair 1 — DDL diff + IIG sheet-by-sheet comparison vs golden
import difflib
import openpyxl

# ---- locate generated files ----
gen_dirs = sorted(WORK.glob("RFC*"))
assert gen_dirs, f"no RFC*_* directory in {WORK}"
rfc_dir = gen_dirs[0]
print(f"Generated RFC dir: {rfc_dir.name}")

gen_ddl = gen_iig = None
for f in rfc_dir.iterdir():
    lo = f.name.lower()
    if lo.endswith("_ddl.txt") or lo.endswith("ddl.txt"):
        gen_ddl = f
    elif lo.endswith("_iig.xlsx") or lo.endswith("iig.xlsx"):
        gen_iig = f
# fallback: check framework/ subdir
if gen_ddl is None:
    fw = WORK / "framework"
    if fw.exists():
        for f in fw.iterdir():
            if "ddl" in f.name.lower() and f.suffix == ".txt":
                gen_ddl = f
                break
assert gen_ddl, f"no *DDL.txt found under {WORK}"
assert gen_iig, f"no *IIG.xlsx found under {WORK}"

# ---- golden files (PRX accumulators) ----
GOLDEN_DIR = RFC / "RFC_110921_PRX"
golden_ddl = GOLDEN_DIR / "ACCUM_DDL.txt"
golden_iig = GOLDEN_DIR / "RFC_110921_Accumulators.xlsx"
assert golden_ddl.exists(), f"missing: {golden_ddl}"
assert golden_iig.exists(), f"missing: {golden_iig}"

# ---- 1. unified diff: ACCUM_DDL.txt ----
print("=" * 60 + f"\n  UNIFIED DIFF: {gen_ddl.name}  vs  {golden_ddl.name}\n" + "=" * 60)
gen_lines  = gen_ddl.read_text(encoding="utf-8").splitlines(keepends=True)
gold_lines = golden_ddl.read_text(encoding="utf-8").splitlines(keepends=True)
diff = list(difflib.unified_diff(
    gold_lines, gen_lines,
    fromfile=f"golden/{golden_ddl.name}", tofile=f"generated/{gen_ddl.name}",
))
print("".join(diff) if diff else "  (byte-identical)")

# ---- 2. sheet-by-sheet IIG comparison ----
print("\n" + "=" * 60 + f"\n  IIG COMPARISON: {gen_iig.name}  vs  {golden_iig.name}\n" + "=" * 60)

wb_gen  = openpyxl.load_workbook(gen_iig, data_only=True)
wb_gold = openpyxl.load_workbook(golden_iig, data_only=True)

print(f"Generated sheets : {wb_gen.sheetnames}")
print(f"Golden sheets    : {wb_gold.sheetnames}")
if wb_gen.sheetnames != wb_gold.sheetnames:
    print("  *** SHEET ORDER / NAMES DIFFER ***")

for sn in wb_gold.sheetnames:
    print(f"\n--- {sn} ---")
    if sn not in wb_gen.sheetnames:
        print("  MISSING in generated workbook")
        continue
    ws_g = wb_gen[sn]
    ws_o = wb_gold[sn]
    g_hdrs = [c.value for c in ws_g[1]]
    o_hdrs = [c.value for c in ws_o[1]]
    if g_hdrs == o_hdrs:
        print(f"  Headers: match ({len(o_hdrs)} cols)")
    else:
        print(f"  Headers DIFFER:\n    golden    : {o_hdrs}\n    generated : {g_hdrs}")
    gr, or_ = ws_g.max_row, ws_o.max_row
    print(f"  Rows: generated={gr}, golden={or_}" + (" ok" if gr == or_ else " *** DIFFER ***"))
    diffs = []
    for r in range(2, max(gr, or_) + 1):
        for c in range(1, max(ws_g.max_column, ws_o.max_column) + 1):
            gv = ws_g.cell(r, c).value
            ov = ws_o.cell(r, c).value
            if str(gv or "") != str(ov or ""):
                hdr = o_hdrs[c - 1] if c <= len(o_hdrs) else f"col{c}"
                diffs.append((r, hdr, ov, gv))
    if diffs:
        print(f"  Differing cells ({len(diffs)}):")
        for row, col, gold_v, gen_v in diffs:
            print(f"    row {row}, {col}: golden={gold_v!r}  generated={gen_v!r}")
    else:
        print("  All data cells match")

wb_gen.close()
wb_gold.close()

# COMMAND ----------

# DBTITLE 1,Pairs 2-10 — batch run + summary table
import traceback

results = []
for pair_num in range(2, 11):
    pair_name = f"pair_{pair_num}"
    print(f"\n{'#' * 60}\n  {pair_name}\n{'#' * 60}")
    row = dict(pair=pair_name, layout_sources="", provider_calls=0,
               unresolved_roles="", pairing_frd="", pairing_vdd="",
               verdict="FAIL", top_flags="", package_path="")
    try:
        # fetch
        p_uri = f"workspace:{PAIRS}/{pair_name}"
        p_be = open_backend(p_uri, base_dir=REPO, client_factory=cf)
        p_rs = RoleStore("inputs", p_be,
                         stores.outputs.workdir.parent / f"pair_in_{pair_num}")
        lp = p_rs.fetch_tree("", depth=0)

        # discover by prefix
        p_sttm = p_frd = p_vdd = None
        for f in sorted(lp.iterdir()):
            if not f.is_file():
                continue
            up = f.name.upper()
            if up.startswith("STTM"):        p_sttm = f
            elif up.startswith("FRD") and f.suffix.lower() == ".docx": p_frd = f
            elif up.startswith("VDD") and f.suffix.lower() == ".xlsx": p_vdd = f
        if not p_sttm:
            row["top_flags"] = "no STTM found"; results.append(row); continue

        # content pairing
        fc = {p.name: p for p in lp.iterdir()
              if p.is_file() and p.name.lower().endswith((".docx", ".contract.json"))}
        vc = {p.name: p for p in lp.iterdir()
              if p.is_file() and p.suffix.lower() == ".xlsx" and p != p_sttm}
        fr = pair_by_content("frd", p_sttm, fc, config, REPO)
        vr = pair_by_content("vdd", p_sttm, vc, config, REPO)
        row["pairing_frd"] = fr.chosen or "(none)"
        row["pairing_vdd"] = vr.chosen or "(none)"
        if p_frd is None and fr.chosen:
            p_frd = fc[fr.chosen]
        if not p_frd:
            row["top_flags"] = "no FRD paired"; results.append(row); continue

        pw = stores.outputs.local_path(f"demo/{pair_name}")
        pw.mkdir(parents=True, exist_ok=True)
        ans = lp / "answers.yaml"
        aa = ["--answers", str(ans)] if ans.exists() else []

        # layout
        lay = run_cli(
            "layout", "--workbook", str(p_sttm), "--frd", str(p_frd),
            *(["--vdd", str(p_vdd)] if p_vdd else []), *aa,
            "--report-unresolved", str(pw / "unresolved_headers.md"),
            "--profile-out", str(pw / "sttm.layout.json"),
            "--require-complete",
            label=f"layout — {pair_name}",
        )
        sources = []
        for ln in lay.stdout.splitlines():
            lo = ln.lower()
            if "source:" in lo: sources.append(ln.strip())
            if "provider" in lo and "call" in lo:
                try: row["provider_calls"] = int("".join(c for c in ln if c.isdigit()) or "0")
                except ValueError: pass
            if "unresolved" in lo: row["unresolved_roles"] = ln.strip()[:60]
        row["layout_sources"] = "; ".join(sources[:3]) or "(see output)"

        if lay.returncode != 0:
            row["top_flags"] = "layout_incomplete"; results.append(row); continue

        # extract
        fc_path = pw / "frd.contract.json"
        if p_frd.suffix.lower() == ".docx":
            run_cli("extract-frd", "--docx", str(p_frd), "--out", str(fc_path),
                    label=f"extract-frd — {pair_name}")
        else:
            fc_path = p_frd
        run_cli("extract-sttm", "--workbook", str(p_sttm),
                "--frd-contract", str(fc_path),
                "--out", str(pw / "sttm.contract.json"),
                "--layout", str(pw / "sttm.layout.json"), *aa,
                label=f"extract-sttm — {pair_name}")
        vc_a = []
        if p_vdd:
            run_cli("extract-vdd", "--vdd", str(p_vdd),
                    "--out", str(pw / "vdd.contract.json"),
                    label=f"extract-vdd — {pair_name}")
            vc_a = ["--vdd", str(pw / "vdd.contract.json")]

        # generate
        gp = run_cli(
            "generate",
            "--frd-contract", str(fc_path),
            "--sttm-contract", str(pw / "sttm.contract.json"),
            *vc_a, *aa,
            "--profile", "acfc_prx", "--iig-template", "iig_v2",
            "--output-mode", "rfc", "--output-dir", str(pw),
            label=f"generate — {pair_name}",
        )
        for ln in gp.stdout.splitlines():
            lo = ln.lower()
            if "verdict" in lo:
                row["verdict"] = ln.strip().split(":")[-1].strip() if ":" in ln else ln.strip()
            if "flag" in lo and not row["top_flags"]:
                row["top_flags"] = ln.strip()[:60]
        rfc_dirs = sorted(pw.glob("RFC*"))
        row["package_path"] = str(rfc_dirs[0].relative_to(stores.outputs.workdir)) if rfc_dirs else "(none)"

    except Exception as exc:
        row["top_flags"] = f"{type(exc).__name__}: {str(exc)[:50]}"
        traceback.print_exc()
    results.append(row)

# ---- summary table ----
print("\n" + "=" * 60 + "\n  PAIRS 2-10 SUMMARY\n" + "=" * 60)
hdr = (f"{'pair':<8}|{'layout sources':<32}|{'calls':>5}|{'unresolved':<22}"
       f"|{'FRD':<22}|{'VDD':<22}|{'verdict':<22}|{'top flags':<32}|{'path'}")
print(hdr)
print("-" * len(hdr))
for r in results:
    print(f"{r['pair']:<8}|"
          f"{r['layout_sources'][:31]:<32}|"
          f"{r['provider_calls']:>5}|"
          f"{r['unresolved_roles'][:21]:<22}|"
          f"{r['pairing_frd'][:21]:<22}|"
          f"{r['pairing_vdd'][:21]:<22}|"
          f"{r['verdict'][:21]:<22}|"
          f"{r['top_flags'][:31]:<32}|"
          f"{r['package_path']}")