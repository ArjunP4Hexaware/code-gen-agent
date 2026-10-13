"""One IIG validation round, start to finish, with no input choice left to the
operator (2026-10-13 — round 5 ran on the wrong STTM because the prompt let the
runner pick the workbook).

    python scripts/run_round.py --round 6 --inputs codegen-state/round_inputs/pair_2.yaml \\
        --golden-dir docs/acfc/iig_goldens --out /tmp/r6/push

``--inputs`` is a gitignored YAML (``sttm: <path>``, ``frd: <path>``) placed by the
owner next to the fingerprint key, so no document name ever reaches git;
``--sttm`` / ``--frd`` give the paths directly instead (home use). In order, each
step stopping the run on failure:

1. keyed fingerprint of both inputs (scripts/doc_fingerprint.py; the key must be
   present) → ``--compare`` against ``--reference``; a HARD line or a REFUSED
   compare → exit 2;
2. ``codegen layout`` / ``extract-sttm`` / ``generate`` under the harness env (mock
   layout + provider, the synthetic notification address, local storage under
   ``--work``), with NO answers unless ``--answers`` is given: the layout must
   resolve every file by itself (elimination included) — anything it still asks
   (a QUESTION / UNRESOLVED line, exit 3 of layout or extract-sttm) → exit 3, RUN.md
   lists the keys; any other stage failure → exit 1;
3. tools/build_goldens.py for ``--pair`` (the de-duplicated golden); a GROUP_ID
   export missing → exit 1 (never scored against a short golden);
4. tools/iig_diff.py key-paired, ``--golden-structure`` + ``--export-scrubbed``;
5. RUN.md (every section the round-5 prompt asked for) + score_totals.json;
6. scripts/scrub_check.py over the push dir: a hit → exit 3 (RUN.md is then
   reduced to the exit and the hit classes).

Answer-line keys (QUESTION / UNRESOLVED / NOTE) are recorded as keys only; a
sheet-scoped key's sheet part is shown as ``sheet#<first 12 hex of sha256>`` (the
fingerprint's ``name#``), never the sheet name.

The push dir holds only what may be committed: RUN.md, compare.txt, the
STRUCTURE-ONLY fingerprint, golden_structure.*, the scrubbed exports,
score_totals.json. Everything else (the keyed fingerprint, contracts, the agent
workbooks, the golden, score.json, diff.xlsx) stays in ``--work`` (default:
``<out>.work``), never pushed. RUN.md names the inputs only as ``<STTM>`` /
``<FRD>`` (``/Workspace/Users/<me>/…/<STTM>``): never a user segment, never a file name.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "acfc" / "fingerprints" / "pair_2_sd_home.json"
SYNTHETIC_EMAIL = "syn.dl.prodsupport@synthetic.example"
EXIT_MEANING = {0: "ok", 1: "a stage failed", 2: "document gate failed (HARD line / REFUSED / "
                "no key)", 3: "stop: the layout asks for answers, or the scrub check is not clean"}
ANSWER_LABELS = ("QUESTION", "UNRESOLVED", "NOTE")
LABEL_WIDTH = 15                       # codegen.cli.ANSWER_LABEL_WIDTH
CLI_TITLE = ("CLI (harness env: mock layout + provider, synthetic e-mail, local storage "
             "under <work>)")
VERDICTS = ("PASS", "PASS_WITH_FLAGS", "FAIL")
_WORKSPACE_USER = re.compile("/Workspace/" + r"Users/[^/\s'\"<>]+")   # split: not a hit
_HOME_DIR = re.compile(r"(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\s'\"]+")


def _load(name: str, path: Path):
    """The module at ``path``, loaded once (later calls return the same object)."""
    known = sys.modules.get(name)
    if known is not None and getattr(known, "__file__", None) and \
            Path(known.__file__).resolve() == path.resolve():
        return known
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fingerprint_mod = _load("doc_fingerprint", ROOT / "scripts" / "doc_fingerprint.py")
scrub_mod = _load("scrub_check", ROOT / "scripts" / "scrub_check.py")


class Redactor:
    """Every text that reaches RUN.md goes through ``__call__``: the input paths,
    their names and stems become ``<STTM>`` / ``<FRD>`` / ``<ANSWERS>``, the
    checkout / work / push dirs become ``<repo>`` / ``<work>`` / ``<push>``, a
    workspace user segment becomes ``<me>``, a local home folder ``<home>``."""

    def __init__(self, tokens: dict[str, Path], dirs: dict[str, Path]):
        pairs: list[tuple[str, str]] = []
        for token, path in {**tokens, **dirs}.items():
            for form in _forms(path):
                pairs.append((form, f"<{token}>"))
        for token, path in tokens.items():
            pairs.append((path.name, f"<{token}>"))
            if token in ("STTM", "FRD") and len(path.stem) >= 8:   # a title, not a word
                pairs.append((path.stem, f"<{token}>"))
        self.pairs = sorted(pairs, key=lambda p: -len(p[0]))

    def __call__(self, text: str) -> str:
        for raw, token in self.pairs:
            if raw:
                text = text.replace(raw, token)
        text = _WORKSPACE_USER.sub("/Workspace/Users/<me>", text)
        return _HOME_DIR.sub("<home>", text)


def _forms(path: Path) -> set[str]:
    """Every spelling a child process may print for ``path`` (8.3 / long, \\ and /)."""
    out: set[str] = set()
    for p in (path, path.absolute(), path.resolve()):
        out |= {str(p), p.as_posix()}
    return {f for f in out if len(f) > 3}


def display_path(path: Path, token: str) -> str:
    """``/Workspace/Users/<me>/…/<STTM>`` — the root it lives under, never a name."""
    posix = path.as_posix()
    if posix.startswith("/Workspace/Users/"):
        return f"/Workspace/Users/<me>/…/<{token}>"
    if posix.startswith("/Workspace/"):
        return f"/Workspace/…/<{token}>"
    return f"<local>/…/<{token}>"


def _run(cmd: list[str], env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env, cwd=str(ROOT))


def harness_env(work: Path) -> dict[str, str]:
    srcpath = _load("codegen_srcpath", ROOT / "src" / "codegen" / "_srcpath.py")
    (work / "state").mkdir(parents=True, exist_ok=True)
    (work / "out").mkdir(parents=True, exist_ok=True)
    # the round runs as the harness does: acfc_env.yaml applied, never opted out of
    base = {k: v for k, v in os.environ.items() if k != "CODEGEN_SKIP_ENV_OVERLAY"}
    return srcpath.child_env(base=base, extra={
        "PYTHONUTF8": "1",
        "CODEGEN_FORCE_MOCK_LAYOUT": "1",
        "CODEGEN_FORCE_MOCK_PROVIDER": "1",
        "CODEGEN_NOTIFICATION_EMAILS": SYNTHETIC_EMAIL,
        "CODEGEN_STORAGE_STATE": f"local:{(work / 'state').resolve().as_posix()}",
        "CODEGEN_STORAGE_OUTPUTS": f"local:{(work / 'out').resolve().as_posix()}",
    })


def answer_keys(text: str) -> list[tuple[str, str]]:
    """``(label, key)`` of every QUESTION / UNRESOLVED / NOTE answer line, the key
    up to `` — `` with a sheet part hashed."""
    out = []
    for line in text.splitlines():
        label = line.split(" ", 1)[0]
        if label in ANSWER_LABELS and " — " in line:
            out.append((label, _hide_sheet(line[LABEL_WIDTH:].split(" — ", 1)[0].strip())))
    return out


def _hide_sheet(key: str) -> str:
    if "/" not in key:
        return key
    sheet, rest = key.split("/", 1)
    return f"sheet#{hashlib.sha256(sheet.encode('utf-8')).hexdigest()[:12]}/{rest}"


def _first_line(text: str) -> str:
    return next((line for line in text.splitlines() if line.strip()), "")


class Round:
    def __init__(self, args: argparse.Namespace, sttm: Path, frd: Path):
        self.args = args
        self.sttm, self.frd = sttm, frd
        self.out: Path = args.out
        self.work: Path = args.work or args.out.with_name(args.out.name + ".work")
        tokens = {"STTM": sttm, "FRD": frd}
        if args.answers is not None:
            tokens["ANSWERS"] = args.answers
        self.redact = Redactor(tokens, {"repo": ROOT, "work": self.work, "push": self.out})
        self.stop_reason = ""
        self.sections: list[tuple[str, list[str]]] = []

    def section(self, title: str, lines: list[str]) -> None:
        self.sections.append((title, [self.redact(line) for line in lines]))

    # 1 ------------------------------------------------------------------ gate
    def gate(self) -> int:
        key = fingerprint_mod.load_key()
        if key is None:
            self.section("Document gate", [fingerprint_mod.NO_KEY, "", "exit 2 — STOP"])
            return 2
        docs = [self.sttm, self.frd]
        keyed = [fingerprint_mod.fingerprint(p, n, key) for n, p in enumerate(docs, start=1)]
        plain = [fingerprint_mod.fingerprint(p, n) for n, p in enumerate(docs, start=1)]
        (self.work / "fp_keyed.json").write_text(json.dumps(keyed, indent=2), encoding="utf-8")
        (self.out / "fingerprint_structure.json").write_text(json.dumps(plain, indent=2),
                                                             encoding="utf-8")
        self.section("Fingerprint (structure only; file#1 = <STTM>, file#2 = <FRD>)",
                     ["```", *[line for e in plain for line in fingerprint_mod.render(e)], "```"])
        errors = [e["file"] for e in keyed if "error" in e]
        reference = json.loads(self.args.reference.read_text(encoding="utf-8"))
        try:
            graded = ([] if errors else
                      fingerprint_mod.compare_graded(reference, keyed))
            lines = [f"{s} {t}" for s, t in graded] or ["identical"]
            code = 2 if errors or any(s == "HARD" for s, _ in graded) else 0
            if errors:
                lines = [f"unreadable: {', '.join(errors)}"]
        except fingerprint_mod.KeyMismatch as exc:
            lines, code = [f"REFUSED {exc}"], 2
        (self.out / "compare.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        verdict = "exit 2 — STOP" if code else "pass (WARN lines are recorded, not a stop)"
        self.section("Document gate (--compare reference vs this run's documents)",
                     [f"reference: `{self._rel(self.args.reference)}` · key id "
                      f"`{fingerprint_mod.key_id(key)}`", "", "```", *lines, "```", "", verdict])
        return code

    # 2 ------------------------------------------------------------------- CLI
    def cli(self) -> int:
        env = harness_env(self.work)
        py = [sys.executable, "-m", "codegen.cli"]
        doctor = _run([*py, "doctor"], env)
        build = next((ln for ln in doctor.stdout.splitlines() if ln.startswith("build ")),
                     _first_line(doctor.stdout))
        sha = _run(["git", "rev-parse", "--short", "HEAD"], env).stdout.strip() or "?"
        self.section("Build", [f"`{build}`", f"HEAD `{sha}`"])
        frd_json, sttm_json = self.work / "frd.json", self.work / "sttm.json"
        answers = ["--answers", str(self.args.answers)] if self.args.answers else []
        stages = [
            ("layout", [*py, "layout", "--workbook", str(self.sttm), "--frd", str(self.frd),
                        "--require-complete", "--frd-contract-out", str(frd_json), *answers]),
            ("extract-sttm", [*py, "extract-sttm", "--workbook", str(self.sttm),
                              "--frd-contract", str(frd_json), "--out", str(sttm_json),
                              *answers]),
            ("generate", [*py, "generate", "--frd-contract", str(frd_json), "--sttm-contract",
                          str(sttm_json), "--output-mode", "framework", "--profile", "acfc_prx",
                          "--iig-template", "iig_v2", "--skip-tests", "--dry-run"]),
        ]
        lines: list[str] = []
        for name, cmd in stages:
            done = _run(cmd, env)
            text = done.stdout + done.stderr
            keys = answer_keys(text)
            owed = [k for k in keys if k[0] != "NOTE"]
            lines += [f"- `{' '.join(['codegen', *cmd[3:]])}` → exit {done.returncode}",
                      f"  first line: `{_first_line(done.stdout)}`"]
            lines += [f"  {label} `{key}`" for label, key in keys]
            if name == "generate":
                verdicts: dict[str, int] = {}
                for ln in done.stdout.splitlines():
                    word = ln.split(" ", 1)[0]
                    if word in VERDICTS:
                        verdicts[word] = verdicts.get(word, 0) + 1
                lines.append("  verdicts: " + (", ".join(f"{v} ×{n}" for v, n in
                                                        sorted(verdicts.items())) or "none"))
            if owed or (name in ("layout", "extract-sttm") and done.returncode == 3):
                self.stop_reason = (f"{name} asks for {len(owed)} answer(s) — keys in the CLI "
                                    "section; no answers are given in a round")
                lines.append(f"  STOP — {self.stop_reason}")
                self.section(CLI_TITLE, lines)
                return 3
            if done.returncode:
                fail = next((ln for ln in text.splitlines()
                             if ln.startswith(("FAIL", "ERROR", "Traceback"))), "")
                # the detail quotes sheet / table names: the label only, never the text
                lines.append(f"  STOP — {name} failed; first error: "
                             f"`{fail.split(' ', 1)[0] or 'none printed'}` (detail withheld, "
                             f"{len(fail)} chars)")
                self.section(CLI_TITLE, lines)
                return 1
        self.section(CLI_TITLE, lines)
        return 0

    # 3 ---------------------------------------------------------------- golden
    def golden(self) -> Path | None:
        build_goldens = _load("build_goldens", ROOT / "tools" / "build_goldens.py")
        groups = build_goldens.PAIR_GROUPS.get(self.args.pair)
        if not groups:
            self.section("Golden", [f"no GROUP_IDs for {self.args.pair} — STOP"])
            return None
        gdir: Path = self.args.golden_dir
        round2 = gdir.with_name(gdir.name + "_round2")
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            report = build_goldens.build_one_pair(
                self.args.pair, groups, gdir / "goldens",
                round2 / "goldens" if (round2 / "goldens").is_dir() else None,
                gdir / "01_pair_group_index.csv",
                round2 / "01_pair_group_index_addendum.csv" if round2.is_dir() else None,
                None, self.work / "goldens")
        dedup = [ln.strip() for ln in captured.getvalue().splitlines()
                 if ln.strip().startswith(f"{self.args.pair}/") and ": dedup " in ln]
        golden = self.work / "goldens" / f"{self.args.pair}_iig_golden.xlsx"
        found = len(report.get("files_found") or [])
        missing = len(report.get("files_missing") or [])
        lines = [f"GROUP_ID exports found {found} of {len(groups)}",
                 *(dedup or ["(no dedup lines)"])]
        if report.get("errors"):
            lines.append(f"build errors: {len(report['errors'])}")
        if missing or not found:
            # a golden short of an export scores the agent against rows that are not there
            self.section("Golden (rebuilt on this SHA)",
                         [*lines, f"{missing} export(s) missing — STOP"])
            return None
        if not golden.is_file():
            self.section("Golden (rebuilt on this SHA)", [*lines, "no golden written — STOP"])
            return None
        self.section("Golden (rebuilt on this SHA)", lines)
        return golden

    # 4 ------------------------------------------------------------------ diff
    def diff(self, golden: Path) -> int:
        env = harness_env(self.work)
        tool = [sys.executable, str(ROOT / "tools" / "iig_diff.py")]
        structure = _run([*tool, "--golden", str(golden), "--golden-structure",
                          "--out", str(self.out)], env)
        agents = sorted(p for p in (self.work / "out").rglob("*_IIG.xlsx")
                        if not p.name.endswith("_REVIEW.xlsx"))
        if structure.returncode or not agents:
            self.section("Diff", [f"golden-structure exit {structure.returncode}; "
                                  f"agent IIG workbooks: {len(agents)} — STOP"])
            return 1
        done = _run([*tool, "--golden", str(golden), "--agent", *map(str, agents),
                     "--out", str(self.work / "diff"), "--export-scrubbed", str(self.out)], env)
        score_path = self.work / "diff" / "score.json"
        if done.returncode or not score_path.is_file():
            self.section("Diff", [f"iig_diff exit {done.returncode} — STOP",
                                  _first_line(done.stdout)])
            return 1
        score = json.loads(score_path.read_text(encoding="utf-8"))
        totals = {"totals": score["totals"], "sheets": {
            name: {k: info.get(k) for k in ("rows", "counts", "score")}
            for name, info in score["sheets"].items()}}
        (self.out / "score_totals.json").write_text(json.dumps(totals, indent=2),
                                                    encoding="utf-8")
        rows = []
        for name, info in score["sheets"].items():
            r = info.get("rows") or {}
            rows.append(f"{name}: agent {r.get('agent', '-')} rows · golden "
                        f"{r.get('golden', '-')} rows (deduped) · paired {r.get('paired', '-')}")
        t = score["totals"]
        self.section("Rows per sheet (agent vs de-duplicated golden)", rows)
        self.section("Score (key-paired, agreed ignore set)",
                     [f"TOTAL {t['score']} over {t['scored_cells']} scored cells; agent IIG "
                      f"workbooks: {len(agents)}"])
        return 0

    # 5/6 ---------------------------------------------------------- RUN.md
    def write(self, code: int) -> int:
        run_md = self.out / "RUN.md"
        run_md.write_text(self._render(code), encoding="utf-8")
        hits = scrub_mod.scan_paths([self.out])
        if not hits:
            return code
        classes: dict[str, int] = {}
        for _path, klass, _ctx in hits:
            classes[klass] = classes.get(klass, 0) + 1
        self.stop_reason = "the scrub check is not clean"
        self.sections = [("Scrub check — NOT clean", [
            f"{k}: {n}" for k, n in sorted(classes.items())] + [
            "", "Only RUN.md may be committed; every other file stays out."])]
        run_md.write_text(self._render(3), encoding="utf-8")
        return 3

    def _render(self, code: int) -> str:
        head = [f"# round {self.args.round} · {self.args.pair} — scripts/run_round.py", "",
                f"- <STTM>: `{display_path(self.sttm, 'STTM')}`",
                f"- <FRD>: `{display_path(self.frd, 'FRD')}`",
                f"- answers: {self._answer_keys()}",
                f"- **exit {code}** — {self.stop_reason if code == 3 else EXIT_MEANING[code]}",
                ""]
        body = []
        for title, lines in self.sections:
            body += [f"## {title}", "", *lines, ""]
        return "\n".join(head + body)

    def _answer_keys(self) -> str:
        if self.args.answers is None:
            return "none given (the layout resolves everything itself, or the round stops)"
        try:
            data = yaml.safe_load(self.args.answers.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return "unreadable"
        keys = list((data.get("gaps") or {}).keys())
        placed = len(data.get("answers") or [])
        return (", ".join(f"`{k}`" for k in keys) or "none") + (f" + {placed} placement(s)"
                                                               if placed else "")

    def _rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return path.name


def _inputs(args: argparse.Namespace) -> tuple[Path, Path]:
    if args.inputs:
        data = yaml.safe_load(args.inputs.read_text(encoding="utf-8")) or {}
        missing = [k for k in ("sttm", "frd") if not data.get(k)]
        if missing:
            raise SystemExit(f"--inputs names no {' / '.join(missing)}")
        return Path(data["sttm"]), Path(data["frd"])
    return args.sttm, args.frd


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--round", required=True)
    ap.add_argument("--pair", default="pair_2")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--inputs", type=Path, help="YAML: sttm: <path>, frd: <path> (gitignored)")
    src.add_argument("--sttm", type=Path)
    ap.add_argument("--frd", type=Path)
    ap.add_argument("--answers", type=Path, default=None,
                    help="optional; a validation round runs without one")
    ap.add_argument("--golden-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="push dir (everything in it is "
                                                            "committable)")
    ap.add_argument("--work", type=Path, default=None, help="never pushed; default <out>.work")
    ap.add_argument("--reference", type=Path, default=REFERENCE)
    args = ap.parse_args(argv)
    if args.sttm is not None and args.frd is None:
        ap.error("--sttm needs --frd")
    sttm, frd = _inputs(args)
    for label, path in (("STTM", sttm), ("FRD", frd), ("answers", args.answers)):
        if path is not None and not path.is_file():
            print(f"run_round: the {label} file does not exist")
            return 1
    if args.answers and "<FILL" in args.answers.read_text(encoding="utf-8"):
        print("run_round: the answers file still holds a <FILL placeholder")
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    rnd = Round(args, sttm, frd)
    rnd.work.mkdir(parents=True, exist_ok=True)
    code = rnd.gate()
    if code == 0:
        code = rnd.cli()
    if code == 0:
        golden = rnd.golden()
        code = 1 if golden is None else rnd.diff(golden)
    code = rnd.write(code)
    print(f"run_round: exit {code} — {EXIT_MEANING[code]}; RUN.md in the push dir")
    return code


if __name__ == "__main__":
    sys.exit(main())
