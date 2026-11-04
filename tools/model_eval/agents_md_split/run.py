"""AGENTS.md split test: 6 probes x {full, split} x 2 runs, Opus 5.5 medium, $30 hard total cap.
Usage: python3 -I /tmp/t/agtest/run.py        -> /tmp/t/agtest/results/<probe>-<arm>-<n>.json"""
import json, os, re, subprocess, sys, time
sys.path.insert(0, "/tmp/t/agtest")
import importlib.util as _u
_s = _u.spec_from_file_location("pilot_run", "/tmp/t/eval/run.py"); _m = _u.module_from_spec(_s)
sys.path.insert(0, "/tmp/t/eval"); _s.loader.exec_module(_m)
cost, USD_PER_DBU = _m.cost, _m.USD_PER_DBU   # same DBU pricing / transcript reader as the pilot
from probes import PROBES, COMMON

REPO = "/app/python/source_code/projects/code-gen-agent"
PY = f"{REPO}/.venv/bin/python"
BASE = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
RUN_CAP, TOTAL_CAP, PARALLEL, WALL = 2.0, 30.0, 4, 25 * 60
R = "/tmp/t/agtest/results"
ENV_DROP = ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_EFFORT",
            "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_PID")

def jobs():
    for n in (1, 2):
        for p in PROBES:
            for arm in ("full", "split"):
                yield f"{p}-{arm}-{n}", p, arm

def start(name, probe, arm):
    wt = f"/tmp/t/agtest/runs/{name}"
    subprocess.run(["git", "-C", REPO, "worktree", "add", "-q", "--detach", wt, BASE], check=True)
    if arm == "split":
        subprocess.run([sys.executable, "-I", "/tmp/t/agtest/make_split.py", wt], check=True,
                       capture_output=True)
    env = {k: v for k, v in os.environ.items() if k not in ENV_DROP}
    env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.hooksPath", GIT_CONFIG_VALUE_0="/dev/null",
               CODEGEN_BLOCK_LIVE_MODEL="1")
    cmd = ["claude", "-p", COMMON.format(py=PY) + PROBES[probe]["brief"], "--model", "opus",
           "--effort", "medium", "--dangerously-skip-permissions", "--output-format", "json",
           "--max-budget-usd", str(RUN_CAP + 0.5)]
    out = open(f"{R}/{name}.stdout", "w")
    p = subprocess.Popen(cmd, cwd=wt, env=env, stdout=out, stderr=subprocess.STDOUT)
    proj = "/app/python/source_code/.claude/projects/" + re.sub(r"[^A-Za-z0-9]", "-", wt)
    return dict(name=name, probe=probe, arm=arm, wt=wt, p=p, t0=time.time(), proj=proj, killed=None)

def usd(r):
    return sum(v["dbu"] for v in cost(r["proj"]).values()) * USD_PER_DBU

def finish(r):
    wt = r["wt"]
    subprocess.run("git add -A -N . 2>/dev/null", cwd=wt, shell=True)
    diff = subprocess.run(["git", "diff", BASE], cwd=wt, capture_output=True, text=True).stdout
    subprocess.run(["git", "reset", "-q"], cwd=wt)
    # the split itself is part of the arm, not of the run's change
    diff = re.sub(r"diff --git a/(AGENTS\.md|\.claude/skills/codegen-reference/SKILL\.md).*?(?=^diff --git |\Z)",
                  "", diff, flags=re.S | re.M) if r["arm"] == "split" else diff
    open(f"{R}/{r['name']}.diff", "w").write(diff)
    reply = ""
    try:
        j = json.load(open(f"{R}/{r['name']}.stdout")); reply = j.get("result") or ""
    except Exception:
        pass
    verdict, detail = PROBES[r["probe"]]["check"](diff, reply)
    res = dict(name=r["name"], probe=r["probe"], arm=r["arm"], usd=round(usd(r), 2), killed=r["killed"],
               minutes=round((time.time() - r["t0"]) / 60, 1), check=verdict, detail=detail,
               read_skill="codegen-reference" in open(f"{R}/{r['name']}.stdout").read() or
                          any("codegen-reference" in open(f, errors="ignore").read()
                              for f in __import__("glob").glob(f"{r['proj']}/*.jsonl")),
               reply=reply[:3000])
    json.dump(res, open(f"{R}/{r['name']}.json", "w"), indent=1)
    print(f"DONE {r['name']}: {verdict} ({detail}) ${res['usd']} skill_seen={res['read_skill']}", flush=True)
    return res["usd"]

def main():
    os.makedirs(R, exist_ok=True)
    queue, running, spent = list(jobs()), [], 0.0
    while queue or running:
        live = spent + sum(usd(r) for r in running)
        if live >= TOTAL_CAP:
            for r in running:
                r["killed"] = "total_cap"; r["p"].kill(); r["p"].wait()
            queue = []
            print(f"TOTAL CAP reached at ${live:.2f}: stopping", flush=True)
        while queue and len(running) < PARALLEL and live < TOTAL_CAP - RUN_CAP:
            name, probe, arm = queue.pop(0)
            if os.path.exists(f"{R}/{name}.json"):
                continue
            running.append(start(name, probe, arm))
        time.sleep(15)
        for r in list(running):
            if r["p"].poll() is None and (usd(r) > RUN_CAP or time.time() - r["t0"] > WALL):
                r["killed"] = "run_cap" if usd(r) > RUN_CAP else "wall"; r["p"].kill(); r["p"].wait()
            if r["p"].poll() is not None:
                spent += finish(r); running.remove(r)
    print(f"ALL DONE: ${spent:.2f}", flush=True)

if __name__ == "__main__":
    main()
