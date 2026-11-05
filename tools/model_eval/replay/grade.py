"""Grade every finished run: hidden test, own-test proof, full suite vs baseline, ruff, hygiene.
Usage: python3 -I /tmp/t/eval/grade.py [--no-suite] [run-name ...]   -> /tmp/t/eval/grades/<run>.json
"""
import json, os, shutil, subprocess, sys
sys.path.insert(0, "/tmp/t/eval")
from tasks import TASKS, REPO, VENV_PY

ENV = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.hooksPath",
           GIT_CONFIG_VALUE_0="/dev/null", CODEGEN_BLOCK_LIVE_MODEL="1")
G = "/tmp/t/eval/grades"

def sh(cmd, cwd, timeout=1500, extra=None):
    env = dict(ENV, **(extra or {}))
    p = subprocess.run(cmd, cwd=cwd, env=env, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout + p.stderr)

def clean_tree(path, ref):
    if os.path.isdir(path):
        sh(f"git -C {REPO} worktree remove --force {path}", REPO)
    sh(f"git -C {REPO} worktree add -q --detach {path} {ref}", REPO)

def pytest(path, args, timeout=1500):
    rc, out = sh(f"PYTHONPATH={path}/src {VENV_PY} -m pytest -q -p no:cacheprovider {args}", path,
                 timeout=timeout)
    tail = [l for l in out.strip().splitlines() if l.strip()][-1:] or [""]
    failed = sorted({l.split(" ")[1] for l in out.splitlines() if l.startswith("FAILED ") or l.startswith("ERROR ")})
    return rc, tail[0], failed

def suite(path):
    return pytest(path, "-n 4 --dist loadgroup tests", timeout=2400)

def baseline(task):
    f = f"{G}/baseline-{task}.json"
    if os.path.exists(f):
        return json.load(open(f))
    p = f"/tmp/t/eval/grade_trees/base-{task}"
    clean_tree(p, TASKS[task]["commit"] + "^")
    rc, tail, failed = suite(p)
    b = dict(rc=rc, tail=tail, failed=failed)
    json.dump(b, open(f, "w"), indent=1)
    sh(f"git -C {REPO} worktree remove --force {p}", REPO)
    return b

def grade(name, run_suite=True):
    task, arm = name.rsplit("-", 1)
    t = TASKS[task]
    run_wt = f"/tmp/t/eval/runs/{name}"
    g = dict(name=name)
    # hygiene: commits made? files changed (tracked + untracked)
    _, head = sh("git rev-parse HEAD", run_wt)
    _, parent = sh(f"git rev-parse {t['commit']}^", REPO)
    g["committed"] = head.strip() != parent.strip()
    _, st = sh("git status --porcelain", run_wt)
    files = [l[3:].strip() for l in st.splitlines() if l.strip()]
    files = [f for f in files if not f.startswith((".pytest_cache", "__pycache__")) and "__pycache__" not in f]
    g["files"] = files
    g["out_of_scope"] = [f for f in files if not f.startswith(("src/", "tests/", "config/", "CHANGELOG", "docs/"))]
    g["version_bumped"] = any(f in ("pyproject.toml", "requirements.txt") for f in files)
    sh("git add -A -N . 2>/dev/null", run_wt)                 # intent-to-add so untracked show in diff
    _, diff = sh(f"git diff {parent.strip()}", run_wt)
    sh("git reset -q", run_wt)
    os.makedirs(G, exist_ok=True)
    open(f"{G}/{name}.diff", "w").write(diff)
    g["diff_lines"] = sum(1 for l in diff.splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---"))
    # ruff on changed python files
    py = [f for f in files if f.endswith(".py") and os.path.exists(f"{run_wt}/{f}")]
    g["ruff"] = sh(f"{REPO}/.venv/bin/ruff check {' '.join(py)}", run_wt)[0] == 0 if py else True
    # tree = clean parent + the run's diff
    tree = f"/tmp/t/eval/grade_trees/{name}"
    clean_tree(tree, t["commit"] + "^")
    if diff.strip():
        open(f"{tree}/.run.diff", "w").write(diff)
        rc, out = sh("git apply --whitespace=nowarn .run.diff", tree)
        g["apply_ok"] = rc == 0
        os.remove(f"{tree}/.run.diff")
    else:
        g["apply_ok"] = None
    # hidden test (the commit's own file, replacing any same-named file the run wrote)
    own_same = os.path.exists(f"{tree}/{t['hidden']}")
    if own_same:
        shutil.copy(f"{tree}/{t['hidden']}", f"{tree}/.own_hidden_named.py")
    _, real = sh(f"git show {t['commit']}:{t['hidden']}", REPO)
    open(f"{tree}/{t['hidden']}", "w").write(real)
    rc, tail, failed = pytest(tree, t["hidden"], timeout=900)
    g["hidden"] = dict(passed=rc == 0, tail=tail, failed=failed)
    if own_same:
        shutil.move(f"{tree}/.own_hidden_named.py", f"{tree}/{t['hidden']}")
    else:
        os.remove(f"{tree}/{t['hidden']}")
    # own tests: new/changed test files of the run must fail on the unfixed code
    own = [f for f in files if f.startswith("tests/") and f.endswith(".py")]
    g["own_tests"] = own
    if own:
        rc, tail, _ = pytest(tree, " ".join(own), timeout=900)
        g["own_pass_with_fix"] = rc == 0
        unfixed = f"/tmp/t/eval/grade_trees/{name}-unfixed"
        clean_tree(unfixed, t["commit"] + "^")
        for f in own:
            os.makedirs(os.path.dirname(f"{unfixed}/{f}"), exist_ok=True)
            shutil.copy(f"{tree}/{f}", f"{unfixed}/{f}")
        rc, tail, _ = pytest(unfixed, " ".join(own), timeout=900)
        g["own_fail_without_fix"] = rc != 0
        g["own_unfixed_tail"] = tail
        sh(f"git -C {REPO} worktree remove --force {unfixed}", REPO)
    # full suite vs baseline
    if run_suite:
        b = baseline(task)
        rc, tail, failed = suite(tree)
        g["suite"] = dict(tail=tail, new_failures=sorted(set(failed) - set(b["failed"])),
                          baseline_failures=len(b["failed"]))
    sh(f"git -C {REPO} worktree remove --force {tree}", REPO)
    json.dump(g, open(f"{G}/{name}.json", "w"), indent=1)
    print(json.dumps({k: g[k] for k in ("name", "hidden", "apply_ok", "ruff", "committed",
                                        "out_of_scope") if k in g}), flush=True)
    return g

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    os.makedirs("/tmp/t/eval/grade_trees", exist_ok=True)
    names = args or sorted(os.path.basename(p)[:-5] for p in os.listdir("/tmp/t/eval/results")
                           if p.endswith(".json"))
    for n in names:
        n = n[:-5] if n.endswith(".json") else n
        grade(n, run_suite="--no-suite" not in sys.argv)
