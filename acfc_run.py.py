# Databricks notebook source
# DBTITLE 1,Install codegen package
# MAGIC %pip install -e /Workspace/Users/admz-sb65923@amerihealthcaritas.com/code-gen-agent[ui,databricks]
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Pair 1: layout + generate RFC package
import os, subprocess, shutil, pathlib

ROOT = pathlib.Path("/Workspace/Users/admz-sb65923@amerihealthcaritas.com/code-gen-agent")
PAIRS_DIR = pathlib.Path("/Workspace/Users/admz-sb65923@amerihealthcaritas.com/frd_sttm_pairs")
# Write locally; publish to volumes from the app UI later.

os.environ["CODEGEN_FORCE_MOCK_PROVIDER"] = "1"
os.chdir(ROOT)

# ── Pair 1 document paths ───────────────────────────────────────────
p1 = PAIRS_DIR / "pair_1"
frd_docx  = p1 / "FRD_STG_STD_OptumRx-Project Eagle 1005789_Accumulators file Ingestion from OptumRx (1).docx"
sttm_xlsx = p1 / "STTM_Project Eagle_OptumRx_1005789_Accumulators File Ingestion from OptumRx.xlsx"
vdd_xlsx  = p1 / "VDD_OptumRx_Accumulators.xlsx"

out_dir = ROOT / "out" / "pair_1"
out_dir.mkdir(parents=True, exist_ok=True)

def run(cmd, label):
    print(f"\n{'='*72}\n  {label}\n{'='*72}")
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if r.stdout:
        print(r.stdout)
    if r.stderr:
        print("STDERR:", r.stderr)
    print(f"exit code: {r.returncode}")
    return r

# ── 1. Layout recognition ───────────────────────────────────────────
run([
    "codegen", "layout",
    "--workbook", str(sttm_xlsx),
    "--frd", str(frd_docx),
    "--vdd", str(vdd_xlsx),
    "--dry-run",
], "codegen layout (pair mode, mock provider)")

# ── 2. Extract FRD contract ─────────────────────────────────────────
run([
    "codegen", "extract-frd",
    "--docx", str(frd_docx),
    "--out", str(out_dir / "frd.contract.json"),
], "codegen extract-frd")

# ── 3. Extract STTM contract ────────────────────────────────────────
run([
    "codegen", "extract-sttm",
    "--workbook", str(sttm_xlsx),
    "--frd-contract", str(out_dir / "frd.contract.json"),
    "--out", str(out_dir / "sttm.contract.json"),
    "--generated-date", "2026-01-01",
], "codegen extract-sttm")

# ── 4. Extract VDD contract ─────────────────────────────────────────
run([
    "codegen", "extract-vdd",
    "--vdd", str(vdd_xlsx),
    "--out", str(out_dir / "vdd.contract.json"),
], "codegen extract-vdd")

# ── 5. Generate RFC package ─────────────────────────────────────────
result = run([
    "codegen", "generate",
    "--frd-contract", str(out_dir / "frd.contract.json"),
    "--sttm-contract", str(out_dir / "sttm.contract.json"),
    "--vdd", str(out_dir / "vdd.contract.json"),
    "--output-mode", "rfc",
    "--profile", "acfc_prx",
    "--iig-template", "iig_v2",
    "--playbook-template", "main_single",
    "--skip-tests",
], "codegen generate --output-mode rfc (pair 1)")

# ── 6. List generated output ─────────────────────────────────────────
gen_out = ROOT / "out"
feed_dirs = [d for d in gen_out.iterdir()
             if d.is_dir() and d.name not in ("pair_1", "reports")]
print(f"\nGenerated feed directories: {[d.name for d in feed_dirs]}")
for fd in feed_dirs:
    for f in sorted(fd.rglob("*")):
        if f.is_file():
            print(f"  {f.relative_to(gen_out)}")
print(f"\nPair 1 output under: {gen_out}")

# COMMAND ----------

# DBTITLE 1,Pair 1: DDL diff and IIG comparison vs golden
import difflib, openpyxl, pathlib

ROOT = pathlib.Path("/Workspace/Users/admz-sb65923@amerihealthcaritas.com/code-gen-agent")
GOLDEN_DIR = pathlib.Path("/Workspace/Users/admz-sb65923@amerihealthcaritas.com/rfc_samples/RFC_110921_PRX")

# ── Locate the generated ACCUM_DDL.txt ──────────────────────────────
gen_out = ROOT / "out"
ddl_candidates = list(gen_out.rglob("ACCUM_DDL.txt"))
if not ddl_candidates:
    # Also check framework/ subdirectories
    ddl_candidates = list(gen_out.rglob("*DDL.txt"))
print(f"DDL candidates found: {[str(p) for p in ddl_candidates]}")

golden_ddl = GOLDEN_DIR / "ACCUM_DDL.txt"
assert golden_ddl.exists(), f"Golden DDL not found: {golden_ddl}"

if ddl_candidates:
    gen_ddl = ddl_candidates[0]
    gen_lines = gen_ddl.read_text(encoding="utf-8").splitlines(keepends=True)
    golden_lines = golden_ddl.read_text(encoding="utf-8").splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        golden_lines, gen_lines,
        fromfile="golden/ACCUM_DDL.txt",
        tofile="generated/ACCUM_DDL.txt",
        lineterm="",
    ))
    print("\n" + "="*72)
    print("  UNIFIED DIFF: ACCUM_DDL.txt (golden vs generated)")
    print("="*72)
    if diff:
        for line in diff:
            print(line)
    else:
        print("IDENTICAL — no differences.")
else:
    print("WARNING: No generated DDL .txt found under out/")

# ── IIG sheet-by-sheet comparison ───────────────────────────────────
print("\n" + "="*72)
print("  IIG SHEET-BY-SHEET COMPARISON")
print("="*72)

golden_iig = GOLDEN_DIR / "RFC_110921_Accumulators.xlsx"
assert golden_iig.exists(), f"Golden IIG not found: {golden_iig}"

# Find generated IIG
iig_candidates = list(gen_out.rglob("*IIG*.xlsx"))
if not iig_candidates:
    iig_candidates = list(gen_out.rglob("*_IIG.xlsx"))
print(f"IIG candidates found: {[str(p) for p in iig_candidates]}")

if iig_candidates:
    gen_iig = iig_candidates[0]
    wb_golden = openpyxl.load_workbook(str(golden_iig), read_only=True, data_only=True)
    wb_gen = openpyxl.load_workbook(str(gen_iig), read_only=True, data_only=True)

    print(f"\nGolden sheets: {wb_golden.sheetnames}")
    print(f"Generated sheets: {wb_gen.sheetnames}")

    all_sheets = list(dict.fromkeys(wb_golden.sheetnames + wb_gen.sheetnames))
    for sheet_name in all_sheets:
        print(f"\n--- Sheet: {sheet_name} ---")
        if sheet_name not in wb_golden.sheetnames:
            print("  EXTRA in generated (not in golden)")
            continue
        if sheet_name not in wb_gen.sheetnames:
            print("  MISSING from generated (in golden)")
            continue

        ws_g = wb_golden[sheet_name]
        ws_n = wb_gen[sheet_name]

        # Read all rows
        g_rows = list(ws_g.iter_rows(values_only=True))
        n_rows = list(ws_n.iter_rows(values_only=True))

        # Headers
        g_hdr = [str(c) if c is not None else "" for c in g_rows[0]] if g_rows else []
        n_hdr = [str(c) if c is not None else "" for c in n_rows[0]] if n_rows else []
        hdr_match = g_hdr == n_hdr
        print(f"  Headers match: {hdr_match}")
        if not hdr_match:
            print(f"    Golden:    {g_hdr}")
            print(f"    Generated: {n_hdr}")

        print(f"  Row counts — golden: {len(g_rows)}, generated: {len(n_rows)}")

        # Cell-by-cell diff (data rows)
        diffs = []
        max_rows = max(len(g_rows), len(n_rows))
        max_cols = max(len(g_hdr), len(n_hdr))
        for r in range(1, max_rows):  # skip header
            g_row = g_rows[r] if r < len(g_rows) else tuple([None] * max_cols)
            n_row = n_rows[r] if r < len(n_rows) else tuple([None] * max_cols)
            for c in range(max_cols):
                gv = g_row[c] if c < len(g_row) else None
                nv = n_row[c] if c < len(n_row) else None
                gs = str(gv) if gv is not None else ""
                ns = str(nv) if nv is not None else ""
                if gs != ns:
                    col_name = g_hdr[c] if c < len(g_hdr) else f"col_{c}"
                    diffs.append((r + 1, col_name, gs, ns))

        if diffs:
            print(f"  Differing cells: {len(diffs)}")
            for row, col, gv, nv in diffs[:50]:
                print(f"    Row {row}, {col}: golden={gv!r} | generated={nv!r}")
            if len(diffs) > 50:
                print(f"    ... +{len(diffs)-50} more")
        else:
            print("  All cells identical.")

    wb_golden.close()
    wb_gen.close()
else:
    print("WARNING: No generated IIG .xlsx found under out/")

# COMMAND ----------

# DBTITLE 1,Pairs 2-10: batch layout + generate
import os, subprocess, shutil, pathlib, traceback

ROOT = pathlib.Path("/Workspace/Users/admz-sb65923@amerihealthcaritas.com/code-gen-agent")
PAIRS_DIR = pathlib.Path("/Workspace/Users/admz-sb65923@amerihealthcaritas.com/frd_sttm_pairs")
os.environ["CODEGEN_FORCE_MOCK_PROVIDER"] = "1"
os.chdir(ROOT)

def find_doc(pair_dir, prefix):
    """Find a file starting with prefix (case-insensitive) in pair_dir."""
    for f in pair_dir.iterdir():
        if f.name.upper().startswith(prefix.upper()):
            return f
    return None

def run_quiet(cmd, cwd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd))

results = []

for i in range(2, 11):
    pair_dir = PAIRS_DIR / f"pair_{i}"
    frd_docx = find_doc(pair_dir, "FRD")
    sttm_xlsx = find_doc(pair_dir, "STTM")
    vdd_xlsx = find_doc(pair_dir, "VDD")

    row = {
        "pair": f"pair_{i}",
        "layout_sources": "",
        "unresolved_roles": "",
        "verdict": "FAIL",
        "top_flags": "",
        "package_path": "",
        "error": "",
    }

    if not sttm_xlsx:
        row["error"] = "No STTM found"
        results.append(row)
        continue

    out_dir = ROOT / "out" / f"pair_{i}"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Layout
        layout_cmd = [
            "codegen", "layout",
            "--workbook", str(sttm_xlsx),
            *([ "--frd", str(frd_docx)] if frd_docx else []),
            *([ "--vdd", str(vdd_xlsx)] if vdd_xlsx else []),
            "--dry-run",
        ]
        lr = run_quiet(layout_cmd, ROOT)
        # Parse layout output for sources and unresolved
        sources = []
        unresolved = []
        for line in (lr.stdout or "").splitlines():
            if "source=" in line:
                sources.append(line.strip())
            if "UNRESOLVED" in line:
                unresolved.append(line.strip().replace("UNRESOLVED", "").strip())
        row["layout_sources"] = "; ".join(sources)[:120]
        row["unresolved_roles"] = "; ".join(unresolved)[:120] if unresolved else "none"

        # Extract FRD
        if frd_docx:
            r = run_quiet([
                "codegen", "extract-frd",
                "--docx", str(frd_docx),
                "--out", str(out_dir / "frd.contract.json"),
            ], ROOT)
            if r.returncode != 0:
                row["error"] = f"extract-frd failed: {(r.stdout or r.stderr or '')[:120]}"
                row["verdict"] = "FAIL"
                results.append(row)
                print(f"pair_{i}: FAIL at extract-frd")
                continue

        # Extract STTM
        frd_contract = out_dir / "frd.contract.json"
        r = run_quiet([
            "codegen", "extract-sttm",
            "--workbook", str(sttm_xlsx),
            "--frd-contract", str(frd_contract),
            "--out", str(out_dir / "sttm.contract.json"),
            "--generated-date", "2026-01-01",
        ], ROOT)
        if r.returncode != 0:
            row["error"] = f"extract-sttm failed: {(r.stdout or r.stderr or '')[:120]}"
            row["verdict"] = "FAIL"
            results.append(row)
            print(f"pair_{i}: FAIL at extract-sttm")
            continue

        # Extract VDD
        if vdd_xlsx:
            r = run_quiet([
                "codegen", "extract-vdd",
                "--vdd", str(vdd_xlsx),
                "--out", str(out_dir / "vdd.contract.json"),
            ], ROOT)
            if r.returncode != 0:
                row["error"] = f"extract-vdd failed: {(r.stdout or r.stderr or '')[:120]}"
                row["verdict"] = "FAIL"
                results.append(row)
                print(f"pair_{i}: FAIL at extract-vdd")
                continue

        # Generate
        gen_cmd = [
            "codegen", "generate",
            "--frd-contract", str(out_dir / "frd.contract.json"),
            "--sttm-contract", str(out_dir / "sttm.contract.json"),
            *([ "--vdd", str(out_dir / "vdd.contract.json")] if vdd_xlsx else []),
            "--output-mode", "rfc",
            "--profile", "acfc_prx",
            "--iig-template", "iig_v2",
            "--playbook-template", "main_single",
            "--skip-tests",
        ]
        gr = run_quiet(gen_cmd, ROOT)
        gen_output = gr.stdout or ""

        # Parse verdict and flags from generate output
        verdict_line = [l for l in gen_output.splitlines() if any(
            v in l for v in ("PASS", "FAIL", "PASS_WITH_FLAGS"))]
        if verdict_line:
            row["verdict"] = verdict_line[-1].strip()[:80]
        elif gr.returncode != 0:
            row["verdict"] = "FAIL"
            row["error"] = f"generate exit {gr.returncode}: {gen_output[:120]}"
        else:
            row["verdict"] = "UNKNOWN"

        # Extract flags
        flag_lines = [l.strip() for l in gen_output.splitlines() if "flag" in l.lower()]
        row["top_flags"] = "; ".join(flag_lines[:3])[:120]

        row["package_path"] = str(out_dir)

    except Exception as e:
        row["verdict"] = "FAIL"
        row["error"] = f"{type(e).__name__}: {e}"
        traceback.print_exc()

    results.append(row)
    status = row['verdict'][:20]
    print(f"pair_{i}: {status}")

# ── Summary table ────────────────────────────────────────────────────
print("\n" + "="*120)
print("  PAIRS 2–10 RESULTS")
print("="*120)
print(f"{'Pair':<10} {'Verdict':<25} {'Unresolved':<25} {'Top Flags':<40} {'Error':<30}")
print("-" * 120)
for r in results:
    print(f"{r['pair']:<10} {r['verdict'][:24]:<25} {r['unresolved_roles'][:24]:<25} "
          f"{r['top_flags'][:39]:<40} {r['error'][:29]:<30}")