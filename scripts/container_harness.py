"""The container runner (post75): the D1 harness's 12-pair run, from this
repo's ``src/`` (no pip install of the project, never a third-party install),
gated by :mod:`codegen.leakgate`.

    python scripts/container_harness.py --pairs-dir DIR --state-dir DIR --out DIR
        [--pairs 1,2,...] [--environment D1] [--endpoint databricks-claude-opus-5]
        [--output-mode notebook --output-mode framework] [--dry-run]
        [--timeout-min 15] [--label run_<ts>_<sha>] [--work DIR]

Per pair (``<pairs-dir>/pair_<n>``): layout -> extract-sttm -> extract-vdd (when
a VDD is present) -> generate, every stage the codegen CLI. A stage exiting 3
ENDS the pair: the stages after it are SKIPPED and the outcome is
NEEDS_ANSWERS; any other non-zero exit ends it as FAIL. Answers: the state
dir's ``answers/<pair>/answers.yaml`` (the volume) wins over the pair folder's
``answers.yaml``. Each pair writes into its own ``<work>/<pair>/out``.

The report (``<label>.md`` / ``.json``), the pairing report (outcome + QUESTION
keys per pair, feed ids masked to ``feed_<n>``, notebook presence per feed) and
every stage's ``CODEGEN-USAGE`` line are gated by the leak gate (harvested from
the pair folders, the static denylist from ``<state-dir>/leakgate/``); the lane
is ``approved`` only at zero real hits — a ``held`` run is written redacted and
stays local. Exit 0 approved, 4 held, 2 a dependency missing.
"""
from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
NEEDS_ANSWERS = 3
STAGES = ("sttm_parse", "frd_extract", "vdd_crosscheck", "generate")
RUNNER = "claude-code container, src-only"
KEY_LINE = re.compile(r"^(?:QUESTION|UNRESOLVED)\s+(.+?)(?:\s+—\s|$)")
FEED_KEY = re.compile(r"(feeds\.)([^.\s]+)(\.)")


def missing_dependencies(repo: Path = REPO) -> list[str]:
    """Every distribution of constraints/acfc_d1.txt and of the project's base +
    [databricks] dependencies that this interpreter lacks (nothing installed)."""
    names: list[str] = []
    for line in (repo / "constraints" / "acfc_d1.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            names.append(re.split(r"[<>=!~\[; ]", line, maxsplit=1)[0])
    for spec in _pyproject_list(repo, "dependencies") + _pyproject_list(repo, "databricks"):
        names.append(re.split(r"[<>=!~\[; ]", spec.strip(), maxsplit=1)[0])
    missing = []
    for name in dict.fromkeys(names):
        try:
            md.version(name)
        except md.PackageNotFoundError:
            missing.append(name)
    return missing


def _pyproject_list(repo: Path, name: str) -> list[str]:
    """The quoted entries of ``<name> = [ ... ]`` in pyproject.toml (no tomllib on 3.10)."""
    text = (repo / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(rf"^{re.escape(name)}\s*=\s*\[(.*?)^\]", text, re.S | re.M)
    if block is None:
        return []
    return [m.group(1) for line in block.group(1).splitlines()
            if (m := re.match(r'\s*"([^"]+)"', line.split("#", 1)[0]))]


def discover(pair_dir: Path, state_dir: Path) -> dict[str, Path | None]:
    """sttm / frd / vdd / answers of a pair folder (the D1 harness's rules)."""
    files = sorted(f for f in pair_dir.iterdir() if f.is_file() and not f.name.startswith("~$"))

    def golden(f: Path) -> bool:
        low = f.name.lower()
        return "iig" in low or low.startswith(("payment_integrity", "25_pyx"))

    books = [f for f in files if f.suffix.lower() == ".xlsx" and not golden(f)]
    sttms = [f for f in books if f.name.lower().startswith("sttm")]
    sttm = next((f for f in sttms if "blank" not in f.name.lower()), sttms[0] if sttms else None)
    frd = next((f for f in files if f.suffix.lower() == ".docx"), None)
    vdd = next((f for f in books if f != sttm and f.name.lower().startswith("vdd")), None)
    state = state_dir / "answers" / pair_dir.name / "answers.yaml"
    local = pair_dir / "answers.yaml"
    answers = state if state.is_file() else (local if local.is_file() else None)
    return {"sttm": sttm, "frd": frd, "vdd": vdd, "answers": answers,
            "answers_source": "state" if state.is_file() else "pair folder" if answers else "none"}


@dataclass
class Stage:
    name: str
    status: str = "SKIPPED"
    exit: int | None = None
    first_error_line: str | None = None
    usage: str | None = None
    keys: list[str] = field(default_factory=list)


@dataclass
class PairRun:
    pair: str
    stages: dict[str, Stage]
    outcome: str = "FAIL"
    runtime_sec: float = 0.0
    answers_source: str = "none"
    notebook_present: list[bool] | None = None
    error: str | None = None

    def answer_keys(self) -> list[str]:
        return [k for s in self.stages.values() for k in s.keys]


def mask_feed_ids(keys: list[str]) -> list[str]:
    ids: dict[str, str] = {}

    def sub(m: re.Match) -> str:
        return m.group(1) + ids.setdefault(m.group(2), f"feed_{len(ids) + 1}") + m.group(3)

    return [FEED_KEY.sub(sub, k) for k in keys]


class Runner:
    def __init__(self, args: argparse.Namespace, env: dict[str, str]):
        self.args, self.env = args, env

    def _cli(self, stage: Stage, cli_args: list[str], deadline: float) -> int:
        from codegen.run_errors import first_error_line, model_usage, usage_summary

        timeout = max(1.0, deadline - time.time())
        try:
            done = subprocess.run([sys.executable, "-m", "codegen.cli", *cli_args], cwd=REPO,
                                  env=self.env, capture_output=True, text=True, timeout=timeout)
            rc, out, err = done.returncode, done.stdout, done.stderr
        except subprocess.TimeoutExpired as exc:
            rc, out, err = -1, _text(exc.stdout), _text(exc.stderr)
        stage.exit = rc
        stage.status = ("TIMEOUT" if rc == -1 else "PASS" if rc == 0
                        else "NEEDS_ANSWERS" if rc == NEEDS_ANSWERS else "FAIL")
        stage.first_error_line = first_error_line(rc, err, out) if rc not in (0, -1) else None
        entries = model_usage(err, out)
        stage.usage = usage_summary(entries) if entries else None
        stage.keys = [m.group(1).strip() for line in out.splitlines()
                      if (m := KEY_LINE.match(line.strip()))]
        return rc

    def run_pair(self, n: int) -> PairRun:
        from codegen.run_stages import pair_outcome, read_stage_manifest

        name = f"pair_{n:02d}"
        run = PairRun(name, {s: Stage(s) for s in STAGES})
        pair_dir = self.args.pairs_dir / f"pair_{n}"
        if not pair_dir.is_dir():
            run.error = "pair folder not found"
            return run
        docs = discover(pair_dir, self.args.state_dir)
        run.answers_source = str(docs["answers_source"])
        if docs["sttm"] is None:
            run.error = "no STTM workbook found"
            return run
        work = self.args.work / name
        out = work / "out"
        work.mkdir(parents=True, exist_ok=True)
        overlay = work / "output_overlay.yaml"
        overlay.write_text(f"output:\n  dir: {out.as_posix()}\n  reports_dir: "
                           f"{(work / 'reports').as_posix()}\n", encoding="utf-8")
        self.env["CODEGEN_CONFIG_OVERLAYS"] = str(overlay)
        answers = ["--answers", str(docs["answers"])] if docs["answers"] else []
        dry = ["--dry-run"] if self.args.dry_run else []
        frd = docs["frd"]
        frd_contract = work / "frd.contract.json"
        plan: list[tuple[str, list[str]]] = [
            ("sttm_parse", ["layout", "--workbook", str(docs["sttm"]),
                            *(["--frd", str(frd)] if frd else []),
                            *(["--vdd", str(docs["vdd"])] if docs["vdd"] else []),
                            "--profile-out", str(work / "sttm.layout.json"),
                            "--report-unresolved", str(work / "unresolved.md"),
                            *(["--frd-contract-out", str(frd_contract)] if frd else []),
                            *dry, *answers]),
            ("frd_extract", ["extract-sttm", "--workbook", str(docs["sttm"]),
                             "--frd-contract", str(frd_contract),
                             "--out", str(work / "sttm.contract.json"),
                             "--layout", str(work / "sttm.layout.json"), *answers]),
        ]
        if docs["vdd"]:
            plan.append(("vdd_crosscheck", ["extract-vdd", "--vdd", str(docs["vdd"]),
                                            "--out", str(work / "vdd.contract.json")]))
        plan.append(("generate", [
            "generate", "--frd-contract", str(frd_contract),
            "--sttm-contract", str(work / "sttm.contract.json"),
            *(["--vdd", str(work / "vdd.contract.json")] if docs["vdd"] else []),
            *[a for mode in self.args.output_mode for a in ("--output-mode", mode)],
            "--skip-tests", "--profile", "acfc_prx", "--iig-template", "iig_v2",
            *(["--environment", self.args.environment] if self.args.environment else []),
            *dry, *answers]))
        start = time.time()
        deadline = start + self.args.timeout_min * 60
        steps: dict[str, int] = {}
        for stage_name, cli_args in plan:
            rc = self._cli(run.stages[stage_name], cli_args, deadline)
            steps[cli_args[0]] = rc
            if rc != 0:
                break                      # exit 3 or a failure ends the pair
        run.runtime_sec = round(time.time() - start, 1)
        if "generate" in steps and out.is_dir():
            run.outcome = pair_outcome(steps, out)
            manifest = read_stage_manifest(out) or {}
            run.notebook_present = [bool((f.get("artefacts") or {}).get("notebook_emit"))
                                    for f in manifest.get("feeds", [])]
        else:
            run.outcome = pair_outcome(steps)
        if any(s.status == "TIMEOUT" for s in run.stages.values()):
            run.outcome = "FAIL"
        for stage in run.stages.values():
            stage.keys = mask_feed_ids(stage.keys)
        return run


def _text(value) -> str:
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else (value or "")


def report_md(label: str, sha: str, runs: list[PairRun], meta: dict) -> str:
    lines = ["# Run Report", "", f"* Label: {label}", f"* SHA: {sha}", f"* Runner: {RUNNER}",
             *[f"* {k}: {v}" for k, v in meta.items()], "", "## Summary", "",
             "| Pair | Outcome | Runtime (s) | Answers |", "| --- | --- | --- | --- |"]
    lines += [f"| {r.pair} | {r.outcome} | {r.runtime_sec} | {r.answers_source} |" for r in runs]
    for r in runs:
        lines += ["", f"## {r.pair}", "", f"* Outcome: {r.outcome}", f"* Runtime: {r.runtime_sec}s"]
        if r.error:
            lines.append(f"* Error: {r.error}")
        lines += ["", "### Stages", "", "| Stage | Status | Exit | first_error_line |",
                  "| --- | --- | --- | --- |"]
        lines += [f"| {s.name} | {s.status} | {'' if s.exit is None else s.exit} | "
                  f"{s.first_error_line or ''} |" for s in r.stages.values()]
        lines += ["", "### Model usage", ""]
        lines += [f"* {s.name}: {s.usage}" for s in r.stages.values() if s.usage] or ["* none"]
        if r.answer_keys():
            lines += ["", "### Needed answers", ""] + [f"* `{k}`" for k in r.answer_keys()]
    return "\n".join(lines) + "\n"


def report_json(label: str, sha: str, runs: list[PairRun], meta: dict) -> str:
    def stage(s: Stage) -> dict:
        return {"status": s.status, "exit": s.exit, "first_error_line": s.first_error_line,
                "usage": s.usage, "keys": s.keys}

    return json.dumps({"label": label, "sha": sha, "runner": RUNNER, **meta, "pairs": [
        {"pair": r.pair, "outcome": r.outcome, "runtime_sec": r.runtime_sec,
         "answers_source": r.answers_source, "notebook_present": r.notebook_present,
         "error": r.error, "stages": {s.name: stage(s) for s in r.stages.values()}}
        for r in runs]}, indent=2) + "\n"


def pairing_md(label: str, runs: list[PairRun], notebook_pairs: tuple[str, ...]) -> str:
    lines = ["# Pairing report (redacted)", "", f"* {label}", f"* runner: {RUNNER}", "",
             "| Pair | Outcome | QUESTION keys |", "| --- | --- | --- |"]
    for r in runs:
        keys = sorted(set(r.answer_keys()))
        lines.append(f"| {r.pair} | {r.outcome} | {'; '.join(keys) if keys else '-'} |")
    lines += ["", "## Notebook present per feed", ""]
    for r in runs:
        if r.pair in notebook_pairs:
            flags = r.notebook_present
            text = ("no manifest" if flags is None else ", ".join(
                f"feed_{i + 1}: {'yes' if f else 'no'}" for i, f in enumerate(flags)) or "no feeds")
            lines.append(f"* {r.pair}: {text}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pairs-dir", type=Path, required=True)
    ap.add_argument("--state-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--work", type=Path)
    ap.add_argument("--pairs", default="")
    ap.add_argument("--environment", default="D1")
    ap.add_argument("--endpoint", default="databricks-claude-opus-5")
    ap.add_argument("--output-mode", action="append", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout-min", type=float, default=15)
    ap.add_argument("--label")
    ap.add_argument("--notebook-pairs", default="pair_02,pair_11,pair_12")
    args = ap.parse_args(argv)
    args.output_mode = args.output_mode or ["notebook", "framework"]

    missing = missing_dependencies()
    if missing:
        print(f"missing dependencies (nothing installed): {', '.join(missing)}")
        return 2
    sys.path.insert(0, str(SRC))
    from codegen import leakgate

    sha = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                         text=True, check=False).stdout.strip() or "unknown"
    label = args.label or f"run_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{sha[:7]}"
    args.work = args.work or args.out.parent / f"{label}.work"
    env = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONUTF8": "1",
           "CODEGEN_PROVIDER": "mock" if args.dry_run else "live",
           "CODEGEN_STATE_DIR": str(args.state_dir),
           "DATABRICKS_SERVING_ENDPOINT": args.endpoint}
    for var in ("CODEGEN_ENVIRONMENTS_DIR", "CODEGEN_STATE_OVERLAYS_DIR",
                "CODEGEN_SKIP_ENV_OVERLAY", "CODEGEN_FORCE_MOCK_PROVIDER"):
        env.pop(var, None)
    numbers = [int(x) for x in args.pairs.split(",") if x.strip()] or sorted(
        int(p.name.split("_")[1]) for p in args.pairs_dir.iterdir()
        if p.is_dir() and re.fullmatch(r"pair_\d+", p.name))
    runner = Runner(args, env)
    runs = []
    for n in numbers:
        print(f"pair_{n:02d} ...", flush=True)
        run = runner.run_pair(n)
        print(f"  -> {run.outcome} in {run.runtime_sec}s (answers: {run.answers_source})",
              flush=True)
        runs.append(run)

    meta = {"provider": env["CODEGEN_PROVIDER"], "endpoint": args.endpoint,
            "environment": args.environment, "output_modes": ", ".join(args.output_mode),
            "python": sys.version.split()[0]}
    files = {f"{label}.md": report_md(label, sha, runs, meta),
             f"{label}.json": report_json(label, sha, runs, meta),
             f"{label}.pairing.md": pairing_md(label, runs,
                                               tuple(args.notebook_pairs.split(",")))}
    os.environ["CODEGEN_STATE_DIR"] = str(args.state_dir)
    # the static denylist: <state dir>/leakgate/denylist_local.txt (or CODEGEN_LEAKGATE_DENYLIST)
    deny = leakgate.build_denylist([args.pairs_dir / f"pair_{n}" for n in numbers])
    gate = leakgate.scan(files, deny)
    out = args.out / label
    out.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (out / name).write_text(text if gate.clean else leakgate.redact(text, deny),
                                encoding="utf-8")
    leakgate.write_hits(gate, out / f"{label}.leak_hits.jsonl")
    if gate.hits:
        vocab = leakgate.template_vocabulary()
        with open(out / f"{label}.leak_hits_classified.jsonl", "w", encoding="utf-8") as fh:
            for hit in gate.hits:
                fh.write(json.dumps({**hit.__dict__, "category": leakgate.classify(
                    hit, deny, vocab)}, separators=(",", ":")) + "\n")
    lane = leakgate.lane(gate)
    stub = {"status": "CLEAN" if gate.clean else "LEAK_GATE_BLOCKED", "label": label,
            "sha": sha, "runner": RUNNER, "lane": lane, **gate.summary(),
            "outcomes": {r.pair: r.outcome for r in runs}}
    (out / f"{label}.stub.json").write_text(json.dumps(stub, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {label}: gate {stub['status']} ({gate.real_hits} real hit(s), dictionary "
          f"{gate.dictionary}), lane {lane}")
    return 0 if lane == "approved" else 4


if __name__ == "__main__":
    raise SystemExit(main())
