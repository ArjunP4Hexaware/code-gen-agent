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
# 2026-10-13: THE provider switch (codegen.reasoning.mode) for the layout recognizer
# AND Layer 2. This notebook runs inside ACFC, so it says LIVE explicitly — the
# default everywhere else is mock, and nothing infers live from the workspace.
dbutils.widgets.dropdown("provider", "live", ["live", "mock"], "Model provider")  # noqa: F821
dbutils.widgets.dropdown("refresh_layout", "no", ["no", "yes"],  # noqa: F821
                         "Re-resolve layout (ignore + overwrite cached profiles)")
# Output conventions are run arguments, never an edit of config/config.yaml
# (blank = whatever the config / overlay selects).
dbutils.widgets.text("conventions_profile", "acfc_prx", "Conventions profile")  # noqa: F821
dbutils.widgets.text("iig_template", "iig_v2", "IIG template")  # noqa: F821
dbutils.widgets.text("playbook_template", "main_single", "Playbook template")  # noqa: F821

PAIR_URI = dbutils.widgets.get("pair_folder")  # noqa: F821
os.environ["CODEGEN_STORAGE_OUTPUTS"] = dbutils.widgets.get("outputs")  # noqa: F821
os.environ["CODEGEN_STORAGE_STATE"] = dbutils.widgets.get("state")  # noqa: F821
os.environ["CODEGEN_PROVIDER"] = dbutils.widgets.get("provider")  # noqa: F821
# One switch decides; no leftover lock from a past run.
for _lock in ("CODEGEN_LAYOUT_PROVIDER", "CODEGEN_FORCE_MOCK_PROVIDER",
              "CODEGEN_FORCE_MOCK_LAYOUT"):
    os.environ.pop(_lock, None)
ANSWERS_NAME = dbutils.widgets.get("answers").strip()  # noqa: F821
REFRESH_LAYOUT = dbutils.widgets.get("refresh_layout") == "yes"  # noqa: F821
CONVENTIONS = [arg for flag, widget in (("--profile", "conventions_profile"),
                                        ("--iig-template", "iig_template"),
                                        ("--playbook-template", "playbook_template"))
               if dbutils.widgets.get(widget).strip()  # noqa: F821
               for arg in (flag, dbutils.widgets.get(widget).strip())]  # noqa: F821

# COMMAND ----------

# DBTITLE 1,Launcher: always the checkout's own codegen, never a stale install
def repo_root_from(start: Path) -> Path:
    """The checkout holding this launcher: the first of ``start`` and its
    parents with a pyproject.toml."""
    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise RuntimeError(f"no pyproject.toml at or above {start}")


def launcher_file() -> Path:
    """This notebook's own location — ``__file__`` when run as a file, else
    the notebook path from the Databricks context. Never the cwd."""
    try:
        return Path(__file__).resolve()
    except NameError:
        context = dbutils.notebook.entry_point.getDbutils().notebook().getContext()  # noqa: F821
        return Path("/Workspace" + context.notebookPath().get())


def srcpath_module(repo_root: Path):
    """This checkout's ``src/codegen/_srcpath.py``, loaded BY FILE PATH — never
    via ``import codegen``, which a stale install could answer."""
    import importlib.util

    path = repo_root / "src" / "codegen" / "_srcpath.py"
    spec = importlib.util.spec_from_file_location("codegen_srcpath_bootstrap", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def codegen_env(repo_root: Path, base: dict | None = None) -> dict:
    """``base`` (default: this process's env) with ``<repo_root>/src``
    prepended to PYTHONPATH, existing entries kept (``_srcpath.child_env``)."""
    return srcpath_module(repo_root).child_env(base=base)


def launch_codegen(repo_root: Path, *args: str,
                   env: dict | None = None) -> subprocess.CompletedProcess:
    """``python -m codegen.cli <args>`` on the checkout's src/ (its first
    output line names the codegen that ran)."""
    return subprocess.run([sys.executable, "-m", "codegen.cli", *args], cwd=repo_root,
                          env=codegen_env(repo_root, env), text=True, capture_output=True,
                          check=False)


REPO = repo_root_from(launcher_file().parent)
# The in-process imports below resolve the same code as the subprocesses.
srcpath_module(REPO).ensure_src_first()
print("repo:", REPO)

# COMMAND ----------

# DBTITLE 1,Bring the pair down to local scratch (Workspace / Files API)
from codegen.build_info import source_line  # noqa: E402
from codegen.config import load_config  # noqa: E402
from codegen.storage import (  # noqa: E402
    RoleStore,
    default_client_factory,
    open_backend,
    open_storage,
)

# load_config applies config/overlays/acfc_env.yaml, then CODEGEN_CONFIG_OVERLAYS
# on top (and prints the list); the `codegen` subprocesses below inherit both.
config = load_config(REPO / "config" / "config.yaml")
print(source_line())
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
from codegen.cli import EXIT_FAILED, EXIT_NEEDS_ANSWERS, EXIT_OK  # noqa: E402
from codegen.run_errors import (  # noqa: E402
    first_error_line,
    first_error_line_full,
    model_usage,
    usage_summary,
)

STEPS: dict[str, int] = {}             # step -> codegen exit code (the summary below)
# D1 post51: two tiers — coordinates only (safe to copy into a report) / quoted
ERRORS: dict[str, str] = {}            # step -> its first error line, coordinates only
ERRORS_FULL: dict[str, str] = {}       # step -> the quoted line (stays in this workspace)
NEEDS_ANSWERS: list[str] = []          # the CLI's QUESTION / UNRESOLVED lines (answer keys)
USAGE: dict[str, str] = {}             # post74: step -> its MODEL USAGE (calls, seconds)


def run(label: str, *args: str) -> int:
    print(f"\n=== {label}")
    done = launch_codegen(REPO, *args)
    print(done.stdout + (("\nSTDERR:\n" + done.stderr) if done.stderr.strip() else ""))
    STEPS[label] = done.returncode
    usage = model_usage(done.stderr, done.stdout)
    if usage:
        USAGE[label] = usage_summary(usage)
    # D1 post50: the exit code decides (0 PASS / 3 NEEDS_ANSWERS: no error line);
    # a warning on stderr is never the error
    error = first_error_line(done.returncode, done.stderr, done.stdout)
    if error is not None:
        ERRORS[label] = error
        ERRORS_FULL[label] = first_error_line_full(done.returncode, done.stderr, done.stdout)
    NEEDS_ANSWERS.extend(line for line in done.stdout.splitlines()
                         if line.startswith(("QUESTION", "UNRESOLVED")) and line not in NEEDS_ANSWERS)
    return done.returncode


from codegen.demo_sources import classify_document_name  # noqa: E402

# The role is a token ANYWHERE in the name ("<title>_STTM.xlsx" too).
from codegen.pairing import OVERRIDE_FILE_NAMES as _OVERRIDES  # noqa: E402
from codegen.pairing import load_pair_overrides as _load_overrides  # noqa: E402

sttms = [n for n in documents
         if n.lower().endswith(".xlsx") and classify_document_name(n).role == "sttm"]
if len(sttms) > 1:
    # More than one STTM: a pairs override file that lists exactly one of them
    # pins it; otherwise stop and NAME them — the chosen one is never silent.
    _files = [local_pair / n for n in documents if n.lower() in _OVERRIDES]
    _pinned = ([n for n in sttms if _load_overrides(_files[0]).lookup(n, "frd")
                or _load_overrides(_files[0]).lookup(n, "vdd")] if _files else [])
    print(f"NOTE           pair.sttm — the folder holds {len(sttms)} STTM workbooks: "
          f"{sttms}; " + (f"the override file pins {_pinned[0]}" if len(_pinned) == 1
                          else "no override file pins one"))
    sttms = _pinned if len(_pinned) == 1 else sttms
assert len(sttms) == 1, (f"expected one STTM workbook in the pair folder, found {sttms} — "
                         f"list the one to run in {_OVERRIDES[0]} (sttm / frd / vdd)")
sttm = local_pair / sttms[0]
answers = ["--answers", str(local_pair / ANSWERS_NAME)] if ANSWERS_NAME else []

# 1. Which FRD / VDD belong to this STTM — by what the documents say.
run("pair", "pair", "--sttm", str(sttm), *answers)
from codegen.pairing import (  # noqa: E402
    OVERRIDE_FILE_NAMES,
    PairOverrides,
    classify_folder,
    load_pair_overrides,
    pair_by_content,
)

# The same roles `codegen pair` printed above: an FRD by its frd token, a VDD
# by its vdd token or positive dictionary evidence — never an IIG golden or an
# unclassified workbook; a pairing_overrides.yaml in the folder wins.
roles = classify_folder([p for p in sorted(local_pair.iterdir())
                         if p.is_file() and p != sttm], config)
frds = {r.name: r.path for r in roles if r.role == "frd"}
vdds = {r.name: r.path for r in roles if r.role == "vdd"}
override_files = [local_pair / n for n in documents if n.lower() in OVERRIDE_FILE_NAMES]
overrides = load_pair_overrides(override_files[0]) if override_files else PairOverrides()
for kind, found in (("frd", frds), ("vdd", vdds)):
    wanted = overrides.lookup(sttm.name, kind)
    if wanted and (local_pair / wanted).is_file():
        found.setdefault(wanted, local_pair / wanted)
frd_name = pair_by_content("frd", sttm, frds, config, REPO, overrides=overrides).chosen
vdd_name = pair_by_content("vdd", sttm, vdds, config, REPO, overrides=overrides).chosen
assert frd_name, "no FRD paired — add `pairing:` to the answers file (see the output above)"
frd = frds[frd_name]
vdd = vdds.get(vdd_name) if vdd_name else None

work = stores.outputs.local_path(f"notebook_{sttm.stem}")
work.mkdir(parents=True, exist_ok=True)

# 2. Layout: cache -> synonyms -> (live recognizer) -> answers file. Whatever
#    stays open is written to unresolved_headers.md — structural labels only.
#    The FRD contract is written HERE, as the pair resolved it (M9): a feed the
#    FRD leaves unnamed is named after the STTM stage band and the gaps are
#    filled from the STTM / VDD — a separate extract-frd knows none of that.
#    REFRESH_LAYOUT re-resolves past every cached profile and overwrites it.
frd_contract = work / "frd.contract.json"
layout_rc = run("layout", "layout", "--workbook", str(sttm), "--frd", str(frd),
                *(["--vdd", str(vdd)] if vdd else []), *answers,
                *(["--refresh"] if REFRESH_LAYOUT else []),
                "--report-unresolved", str(work / "unresolved_headers.md"),
                "--profile-out", str(work / "sttm.layout.json"),
                *(["--frd-contract-out", str(frd_contract)]
                  if frd.suffix.lower() == ".docx" else []), "--require-complete")

# COMMAND ----------

# DBTITLE 1,Extract + generate (stops here when the layout is incomplete)
if layout_rc != 0:
    print((work / "unresolved_headers.md").read_text(encoding="utf-8"))
    if layout_rc == EXIT_NEEDS_ANSWERS:          # unplaced columns: answers owed, not a failure
        raise SystemExit("layout NEEDS ANSWERS: place the roles above (UNRESOLVED / QUESTION "
                         "lines) in an answers.yaml (docs/ACFC_DEPLOY.md §6), put it in the "
                         "pair folder and re-run")
    raise SystemExit("layout FAILED (exit %d) — see its output above" % layout_rc)

if frd.suffix.lower() != ".docx":
    frd_contract = frd
run("extract-sttm", "extract-sttm", "--workbook", str(sttm), "--frd-contract",
    str(frd_contract), "--out", str(work / "sttm.contract.json"),
    "--layout", str(work / "sttm.layout.json"))
if not (work / "sttm.contract.json").is_file():
    # Exit 3 with no contract: EVERY feed needs an answer — nothing to generate.
    raise SystemExit("extract-sttm wrote no contract — see the QUESTION / UNRESOLVED / FAIL lines "
                     "above; answer the keys in answers.yaml (docs/ACFC_DEPLOY.md §6)")
vdd_args: list[str] = []
if vdd is not None:
    run("extract-vdd", "extract-vdd", "--vdd", str(vdd), "--out", str(work / "vdd.contract.json"))
    vdd_args = ["--vdd", str(work / "vdd.contract.json")]
run("generate", "generate", "--frd-contract", str(frd_contract), "--sttm-contract",
    str(work / "sttm.contract.json"), *vdd_args, *CONVENTIONS, "--output-mode", "framework",
    "--skip-tests",
    *(["--dry-run"] if os.environ["CODEGEN_PROVIDER"] == "mock" else []))

# COMMAND ----------

# DBTITLE 1,Store the outputs (no-op when the outputs role is local)
sent = stores.outputs.push_tree("")
print(f"{len(sent)} file(s) stored under {stores.outputs.uri()}" if sent
      else f"outputs are local: {stores.outputs.workdir}")

# COMMAND ----------

# DBTITLE 1,Summary — 0 ok, 1 failed, 3 needs answers (codegen --help)
from codegen.run_stages import open_counts, pair_outcome, read_stage_manifest  # noqa: E402

MEANING = {EXIT_OK: "ok", EXIT_FAILED: "FAILED", EXIT_NEEDS_ANSWERS: "needs answers"}
for step, code in STEPS.items():
    print(f"{step:<14} {MEANING.get(code, f'exit {code}')}"
          + (f" — first error: {ERRORS[step]}" if ERRORS.get(step) else ""))
    if ERRORS_FULL.get(step):
        print(f"{'':<14}   quoted (this workspace only): {ERRORS_FULL[step]}")
    if USAGE.get(step):
        print(f"{'':<14}   model usage: {USAGE[step]}")
# post58: the pair's outcome — the worst step; generate's from CODEGEN_STAGES.json
# (PASS_WITH_OPEN_INPUTS: every feed written, lines still open)
OUTCOME = pair_outcome(STEPS, stores.outputs.workdir)
_manifest = read_stage_manifest(stores.outputs.workdir) or {}
_open = (open_counts(_manifest.get("questions") or [])
         if "generate" in STEPS and _manifest.get("exit") == STEPS["generate"] else None)
print(f"\n{'outcome':<14} {OUTCOME}" + (
    f" — {_open['blocking']} blocking question(s), {_open['non_blocking']} input(s) open"
    if _open else ""))
if NEEDS_ANSWERS:
    print("\nNEEDS ANSWERS — the outputs above were written for every feed that could "
          "proceed; answer these keys under `gaps:` in the pair folder's answers.yaml and "
          "re-run:")
    for line in NEEDS_ANSWERS:
        print("  " + line)
