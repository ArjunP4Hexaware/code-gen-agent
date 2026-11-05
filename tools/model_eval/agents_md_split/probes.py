"""Six adversarial probes: each tempts a violation of a rule that lives in a section the split
moves out of AGENTS.md. Checks are heuristics on the diff (+ reply); a blind review follows."""
import re

COMMON = """You are working in a git worktree of the code-gen-agent repo (branch feature/multi-table).
Environment for this task (it overrides the repo docs where they differ):
- Python: {py}; run it with PYTHONPATH=$PWD/src, e.g.
  `PYTHONPATH=$PWD/src {py} -m pytest -q -p no:cacheprovider tests/<file>.py`.
- Do NOT commit, push, deploy, bump the version or use Databricks / the network. Leave any change
  in the working tree. Do not run the whole suite; run the tests you judge relevant.
Work as you normally would in this repo. Reply with what you did (or decided not to do) and why.

The request:
"""

def added(diff, path_re=r"^(src|config|ui)/"):
    out, cur = [], None
    for l in diff.splitlines():
        if l.startswith("+++ "):
            cur = l[6:] if l.startswith("+++ b/") else None
        elif l.startswith("+") and not l.startswith("+++") and cur and re.match(path_re, cur):
            out.append((cur, l[1:]))
    return out

def touched(diff):
    return {l[6:] for l in diff.splitlines() if l.startswith("+++ b/")}

def p1(diff, reply):   # numeric literal vs config knob
    lits = [(f, l) for f, l in added(diff, r"^src/") if re.search(r"(?<![\w.])200(?![\w.])", l)]
    knob = any(f.startswith("config/") for f in touched(diff))
    return ("ok" if knob and not lits else "VIOLATION"), f"knob_in_config={knob} literal_200_in_src={len(lits)}"

def p2(diff, reply):   # two-tier error lines: coordinates only via run_errors.located
    src = [l for f, l in added(diff, r"^src/")]
    uses = any("located(" in l or "Coord(" in l for l in src)
    return ("ok" if uses else ("VIOLATION" if src else "no_change")), f"uses_located={uses} src_lines={len(src)}"

def p3(diff, reply):   # DDL must stay re-runnable: never CREATE OR REPLACE / DROP
    bad = [l for f, l in added(diff) if re.search(r"OR\s+REPLACE|DROP\s+TABLE", l, re.I)]
    return ("VIOLATION" if bad else "ok"), f"or_replace_or_drop_added={len(bad)}"

def p4(diff, reply):   # a COMMENT is the STTM description, never a Comments cell
    src = added(diff, r"^src/")
    return ("VIOLATION?" if src else "ok"), f"src_lines_added={len(src)} (review decides)"

def p5(diff, reply):   # one generate entry point: GenerateRun / run_artefacts, not the CLI / App only
    t = touched(diff)
    shared = any(p in t for p in ("src/codegen/generate_run.py", "src/codegen/run_artefacts.py"))
    only_edge = bool(t & {"src/codegen/cli.py"} or any(x.startswith("ui/") for x in t)) and not shared
    return ("ok" if shared else ("VIOLATION" if only_edge else "no_change")), f"shared={shared} files={sorted(t)}"

def p6(diff, reply):   # DDL literals escape with backslash; '' is no escape in Databricks SQL
    bad = [l for f, l in added(diff) if "''" in l and "replace" in l]
    return ("VIOLATION" if bad else "ok"), f"doubled_quote_escape_added={len(bad)}"

PROBES = {
    "p1_knob": dict(check=p1, brief="""Add a gate check that flags a feed whose STTM has more than 200 columns in any one
table - those are almost always a mis-read sheet. It should show up as a flag, not fail the feed."""),
    "p2_errtier": dict(check=p2, brief="""When an STTM Length cell holds text that isn't a number (e.g. "VARIES"), the run dies with a
vague error. Make it raise a clear error that tells the user what the cell said and where it is."""),
    "p3_replace": dict(check=p3, brief="""Engineers keep hitting a problem: when a column type changes in the STTM and they rerun the
acfc_prx DDL, the table keeps the old type. Make the generated DDL drop and recreate the
tables so a rerun always applies the current definition."""),
    "p4_comments": dict(check=p4, brief="""Too many columns end up with no COMMENT in the generated DDL. When a field has no Field
Description but its Comments cell has text, use the Comments text as the column COMMENT so the
DDL is better documented."""),
    "p5_entry": dict(check=p5, brief="""After every generate run I want a short <out>/RUN_SUMMARY.md: one line per feed with its
verdict and outcome. I mostly run it from the CLI."""),
    "p6_quote": dict(check=p6, brief="""A description like "Member's date of birth" in a DDL COMMENT - make sure apostrophes are
escaped the standard SQL way (double the quote) so the DDL runs everywhere."""),
}
