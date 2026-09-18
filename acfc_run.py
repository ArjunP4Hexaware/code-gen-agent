# Databricks notebook source
# MAGIC %md
# MAGIC # CodeGen — notebook run (the fallback when the App is not available)
# MAGIC
# MAGIC Runs ONE pair end to end from a serverless notebook: pair by content → layout
# MAGIC (answers file) → extract → generate → store the outputs. Documents and outputs
# MAGIC are reached through **storage URIs** (`workspace:` / `volume:`), i.e. the
# MAGIC Workspace API and the Files API — never `/Volumes` or `/Workspace` as a mounted
# MAGIC path (`docs/ACFC_DEPLOY.md` §3, `docs/acfc/RETROFIT_LOG.md` §5 and §8).
# MAGIC
# MAGIC Attach to serverless (or any cluster with Python 3.10+) and run the cells in
# MAGIC order. Nothing here carries a client file name: every location is a widget.

# COMMAND ----------

# MAGIC %pip install -q -e ".[databricks]"

# COMMAND ----------

dbutils.library.restartPython()  # noqa: F821 — notebook global

# COMMAND ----------

import os
import subprocess
import sys
from pathlib import Path

dbutils.widgets.text("pair_folder", "workspace:/Workspace/Users/<you>/codegen/pairs/pair_1",  # noqa: F821
                     "Pair folder (storage URI)")
dbutils.widgets.text("outputs", "workspace:/Workspace/Users/<you>/codegen/outputs",  # noqa: F821
                     "Outputs root (storage URI, must exist)")
dbutils.widgets.text("state", "workspace:/Workspace/Users/<you>/codegen/state",  # noqa: F821
                     "State root (storage URI, must exist)")
dbutils.widgets.text("answers", "", "answers.yaml inside the pair folder (optional)")  # noqa: F821
dbutils.widgets.dropdown("layout_provider", "mock", ["mock", "live"], "Layout recognizer")  # noqa: F821
dbutils.widgets.dropdown("layer2", "mock", ["mock", "live"], "Layer 2 (reasoning)")  # noqa: F821

PAIR_URI = dbutils.widgets.get("pair_folder")  # noqa: F821
os.environ["CODEGEN_STORAGE_OUTPUTS"] = dbutils.widgets.get("outputs")  # noqa: F821
os.environ["CODEGEN_STORAGE_STATE"] = dbutils.widgets.get("state")  # noqa: F821
os.environ["CODEGEN_LAYOUT_PROVIDER"] = dbutils.widgets.get("layout_provider")  # noqa: F821
if dbutils.widgets.get("layer2") == "mock":  # noqa: F821
    os.environ["CODEGEN_FORCE_MOCK_PROVIDER"] = "1"
else:
    os.environ.pop("CODEGEN_FORCE_MOCK_PROVIDER", None)
ANSWERS_NAME = dbutils.widgets.get("answers").strip()  # noqa: F821

# COMMAND ----------

# DBTITLE 1,Bring the pair down to local scratch (Workspace / Files API)
from codegen.config import load_config
from codegen.storage import RoleStore, default_client_factory, open_backend, open_storage

REPO = Path.cwd()
config = load_config(REPO / "config" / "config.yaml",
                     overlays=[p for p in os.environ.get("CODEGEN_CONFIG_OVERLAYS", "").split(";")
                               if p] or None)
stores = open_storage(config, REPO)
pair_backend = open_backend(PAIR_URI, base_dir=REPO,
                            client_factory=default_client_factory(config))
pair = RoleStore("inputs", pair_backend, stores.outputs.workdir.parent / "pair_in")
local_pair = pair.fetch_tree("", depth=0)
documents = sorted(p.name for p in local_pair.iterdir() if p.is_file())
print("pair folder:", PAIR_URI)
for name in documents:
    print("  ", name)

# COMMAND ----------

# DBTITLE 1,Pair by content, resolve the layout, extract, generate
def run(label: str, *args: str) -> int:
    print(f"\n=== {label}")
    done = subprocess.run([sys.executable, "-m", "codegen.cli", *args], cwd=REPO, text=True,
                          capture_output=True, check=False)
    print(done.stdout + (("\nSTDERR:\n" + done.stderr) if done.stderr.strip() else ""))
    return done.returncode


sttms = [n for n in documents if n.lower().endswith(".xlsx") and n.lower().startswith("sttm")]
assert len(sttms) == 1, f"expected one STTM_*.xlsx in the pair folder, found {sttms}"
sttm = local_pair / sttms[0]
answers = ["--answers", str(local_pair / ANSWERS_NAME)] if ANSWERS_NAME else []

# 1. Which FRD / VDD belong to this STTM — by what the documents say.
run("pair", "pair", "--sttm", str(sttm), *answers)
from codegen.pairing import pair_by_content  # noqa: E402

frds = {p.name: p for p in local_pair.iterdir()
        if p.name.lower().endswith((".docx", ".contract.json"))}
vdds = {p.name: p for p in local_pair.iterdir()
        if p.suffix.lower() == ".xlsx" and p != sttm}
frd_name = pair_by_content("frd", sttm, frds, config, REPO).chosen
vdd_name = pair_by_content("vdd", sttm, vdds, config, REPO).chosen
assert frd_name, "no FRD paired — add `pairing:` to the answers file (see the output above)"
frd = frds[frd_name]
vdd = vdds.get(vdd_name) if vdd_name else None

work = stores.outputs.local_path(f"notebook_{sttm.stem}")
work.mkdir(parents=True, exist_ok=True)

# 2. Layout: cache -> synonyms -> (live recognizer) -> answers file. Whatever
#    stays open is written to unresolved_headers.md — structural labels only.
layout_rc = run("layout", "layout", "--workbook", str(sttm), "--frd", str(frd),
                *(["--vdd", str(vdd)] if vdd else []), *answers,
                "--report-unresolved", str(work / "unresolved_headers.md"),
                "--profile-out", str(work / "sttm.layout.json"), "--require-complete")

# COMMAND ----------

# DBTITLE 1,Extract + generate (stops here when the layout is incomplete)
if layout_rc != 0:
    print((work / "unresolved_headers.md").read_text(encoding="utf-8"))
    raise SystemExit("layout incomplete: place the roles above in an answers.yaml "
                     "(docs/ACFC_DEPLOY.md §6), put it in the pair folder and re-run")

frd_contract = work / "frd.contract.json"
if frd.suffix.lower() == ".docx":
    run("extract-frd", "extract-frd", "--docx", str(frd), "--out", str(frd_contract))
else:
    frd_contract = frd
run("extract-sttm", "extract-sttm", "--workbook", str(sttm), "--frd-contract",
    str(frd_contract), "--out", str(work / "sttm.contract.json"),
    "--layout", str(work / "sttm.layout.json"))
vdd_args: list[str] = []
if vdd is not None:
    run("extract-vdd", "extract-vdd", "--vdd", str(vdd), "--out", str(work / "vdd.contract.json"))
    vdd_args = ["--vdd", str(work / "vdd.contract.json")]
run("generate", "generate", "--frd-contract", str(frd_contract), "--sttm-contract",
    str(work / "sttm.contract.json"), *vdd_args, "--output-mode", "rfc", "--skip-tests",
    *(["--dry-run"] if os.environ.get("CODEGEN_FORCE_MOCK_PROVIDER") else []))

# COMMAND ----------

# DBTITLE 1,Store the outputs (no-op when the outputs role is local)
sent = stores.outputs.push_tree("")
print(f"{len(sent)} file(s) stored under {stores.outputs.uri()}" if sent
      else f"outputs are local: {stores.outputs.workdir}")
