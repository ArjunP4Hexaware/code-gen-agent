"""Replay pilot runner: 4 tasks x 3 arms, one task's arms at a time, DBU watchdog per run.
Usage: python3 -I /tmp/t/eval/run.py [task ...]      results -> /tmp/t/eval/results/<task>-<arm>.json
"""
import glob, json, os, re, subprocess, sys, time
sys.path.insert(0, "/tmp/t/eval")
from tasks import TASKS, COMMON, REPO, VENV_PY

USD_PER_DBU = 0.07                      # = Anthropic list price for these models
ARMS = {
    "A_opus":   dict(model="opus",  effort="medium", cap_usd=7.0),
    "B_haiku":  dict(model="haiku", effort="xhigh",  cap_usd=3.0),
    "C_hybrid": dict(model="opus",  effort="medium", cap_usd=7.0, hybrid=True),
}
WALL_LIMIT = 50 * 60
RATES = {  # in, out, cache_read, write5m, write1h  (DBU / 1M)
    "opus": (57.143, 285.714, 2.857, 71.429, 114.286),
    "sonnet": (28.571, 142.857, 1.429, 35.714, 57.143),
    "haiku": (1.429, 7.143, 0.143, 1.786, 2.857),
    "haiku_long": (7.143, 35.714, 0.714, 8.929, 14.286),
}
WORKER = {"haiku-worker": {
    "description": "Implementation worker (Haiku 5.5, xhigh effort). Give it a precise brief: "
                   "files, intended change, tests to add and run. Returns a summary + diff stat.",
    "prompt": ("You are an implementation worker. Do exactly what the brief asks, in the current "
               "worktree. Follow the repo's AGENTS.md/CLAUDE.md rules and the environment notes in "
               "the brief (PYTHONPATH=$PWD/src, the given python). Write the tests the brief asks "
               "for, prove they fail without the change, run them, run ruff on changed files. Never "
               "commit, push, or use the network. Report: what you changed (files), test results, "
               "anything in the brief you could not do or disagree with."),
    "model": "haiku", "effort": "xhigh"}}
LEAD = ("You are the lead engineer and you have a worker: the `haiku-worker` subagent "
        "(Haiku 5.5, cheap). Your job: investigate only as far as needed to find the root cause "
        "and design the fix, then delegate the implementation, the new tests and the test runs to "
        "haiku-worker with a precise brief (files, functions, intended behaviour, tests to add). "
        "Then review its diff yourself (git diff) against the repo rules and the task, and send it "
        "back with concrete corrections if anything is wrong. Write code yourself only if the "
        "worker has failed twice on the same point.")

def fam(model, ctx):
    m = model or ""
    if "haiku" in m:
        return "haiku_long" if ctx > 100_000 else "haiku"
    return next((k for k in ("opus", "sonnet") if k in m), None)

def cost(projdir):
    seen, out = set(), {}
    for f in glob.glob(f"{projdir}/**/*.jsonl", recursive=True):
        for line in open(f, errors="ignore"):
            try: e = json.loads(line)
            except Exception: continue
            m = e.get("message") or {}; u = m.get("usage")
            if e.get("type") != "assistant" or not u: continue
            k = (m.get("id"), e.get("requestId"))
            if k in seen: continue
            seen.add(k)
            cc = u.get("cache_creation") or {}
            w1 = cc.get("ephemeral_1h_input_tokens", 0) or 0
            w5 = (u.get("cache_creation_input_tokens", 0) or 0) - w1
            inp, cr, o = u.get("input_tokens", 0) or 0, u.get("cache_read_input_tokens", 0) or 0, u.get("output_tokens", 0) or 0
            fm = fam(m.get("model"), inp + cr + w5 + w1)
            if not fm: continue
            r = RATES[fm]
            who = "sub" if ("/subagents/" in f or e.get("isSidechain")) else "main"
            d = out.setdefault(f"{fm}/{who}", dict(req=0, inp=0, out=0, cr=0, w5=0, w1=0, dbu=0.0))
            d["req"] += 1; d["inp"] += inp; d["out"] += o; d["cr"] += cr; d["w5"] += w5; d["w1"] += w1
            d["dbu"] += (inp*r[0] + o*r[1] + cr*r[2] + w5*r[3] + w1*r[4]) / 1e6
    return out

def start(task, arm):
    t, a = TASKS[task], ARMS[arm]
    name = f"{task}-{arm}"
    wt = f"/tmp/t/eval/runs/{name}"
    if not os.path.isdir(wt):
        subprocess.run(["git", "-C", REPO, "worktree", "add", "-q", "--detach", wt, t["commit"] + "^"], check=True)
    prompt = COMMON.format(py=VENV_PY) + t["brief"]
    cmd = ["claude", "-p", prompt, "--model", a["model"], "--effort", a["effort"],
           "--dangerously-skip-permissions", "--output-format", "json",
           "--max-budget-usd", str(a["cap_usd"] + 1)]
    if a.get("hybrid"):
        cmd += ["--agents", json.dumps(WORKER), "--append-system-prompt", LEAD]
    env = dict(os.environ, GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.hooksPath",
               GIT_CONFIG_VALUE_0="/dev/null", CODEGEN_BLOCK_LIVE_MODEL="1")
    for k in ("CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_EFFORT",
              "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_PID"):
        env.pop(k, None)
    log = open(f"/tmp/t/eval/results/{name}.stdout", "w")
    p = subprocess.Popen(cmd, cwd=wt, env=env, stdout=log, stderr=subprocess.STDOUT)
    projdir = "/app/python/source_code/.claude/projects/" + re.sub(r"[^A-Za-z0-9]", "-", wt)
    return dict(name=name, p=p, t0=time.time(), cap=a["cap_usd"], projdir=projdir, killed=None)

def finish(r):
    c = cost(r["projdir"])
    dbu = sum(v["dbu"] for v in c.values())
    res = dict(name=r["name"], rc=r["p"].returncode, killed=r["killed"],
               minutes=round((time.time() - r["t0"]) / 60, 1), dbu=round(dbu, 2),
               usd=round(dbu * USD_PER_DBU, 2), by_model=c)
    try:
        j = json.load(open(f"/tmp/t/eval/results/{r['name']}.stdout"))
        res.update(cc_reported_usd=j.get("total_cost_usd"), turns=j.get("num_turns"),
                   summary=(j.get("result") or "")[:4000])
    except Exception as e:
        res["parse_error"] = str(e)
    json.dump(res, open(f"/tmp/t/eval/results/{r['name']}.json", "w"), indent=1)
    print(f"DONE {r['name']}: rc={res['rc']} killed={r['killed']} {res['minutes']}min "
          f"${res['usd']} (cc says {res.get('cc_reported_usd')})", flush=True)

def main(tasks):
    os.makedirs("/tmp/t/eval/results", exist_ok=True)
    for task in tasks:
        running = [start(task, arm) for arm in ARMS]
        print(f"START {task}: {[r['name'] for r in running]}", flush=True)
        while running:
            time.sleep(15)
            for r in list(running):
                usd = sum(v["dbu"] for v in cost(r["projdir"]).values()) * USD_PER_DBU
                over = usd > r["cap"] and "budget" or (time.time() - r["t0"] > WALL_LIMIT and "wall")
                if r["p"].poll() is None and over:
                    r["killed"] = over; r["p"].kill(); r["p"].wait()
                if r["p"].poll() is not None:
                    finish(r); running.remove(r)

if __name__ == "__main__":
    main(sys.argv[1:] or list(TASKS))
