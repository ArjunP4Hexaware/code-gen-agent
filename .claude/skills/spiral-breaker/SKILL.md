---
name: spiral-breaker
description: Stops debug spirals before they eat hours. Use this whenever a fix attempt has failed twice on the same problem, the same test keeps failing, the same file has been edited repeatedly without progress, an error message changes but the failure doesn't, or the user says things like "still broken", "same error", "this isn't working", or "we've been at this for hours". Also use before extracting facts from FRD, STTM, spec, or requirements documents, and whenever you find yourself building a workaround around an access, permission, gateway, or environment restriction.
---

# Spiral Breaker

A debug spiral is a run of fix attempts that produce no new information. Each attempt
feels like progress, but if you don't know *why* the last one failed, the next one is a
guess. The way out is almost never a cleverer fix. It is a better diagnosis.

## The trigger

Two failed fixes on the same symptom means stop. Do not make attempt three. Work through
the steps below and report before writing more fix code.

## Step 1: Name the pattern

First, check references/known-causes.md for a signature matching this symptom. A
match tells you what to check first; it does not replace the check.

Most spirals are one of four patterns. Identify which one applies.

### Pattern A: Wrong layer

Signs:
- The error names something that looks fine (a repo "not found" that exists).
- A fix in one place has no effect on the symptom.
- Behavior differs between environments, accounts, or viewers.
- Something broke after an upstream change you did not make (a library, an endpoint, a model version).

What to do: list every layer between the code and the symptom, then observe each one
directly instead of inferring. Print the raw value at each boundary, run the diagnostic
command for that layer, or open the output in the real target viewer. Fix at the layer
that is actually wrong.

Typical cases: Git sending a cached credential for a different account than the CLI is
logged into; a file that renders badly only in one previewer; a model endpoint that
starts returning a list of content blocks instead of a string, so the error appears far
downstream of the adapter.

### Pattern B: No oracle

Signs:
- You cannot say in one sentence how you will know it is fixed.
- Verification is "looks right" or "run it and see".
- Each fix breaks something else.

What to do: stop fixing. Write a test or minimal reproduction that fails, confirm it
fails for the reason you think, then fix until it passes. For a rebuild or port, write
the spec and acceptance checks from the working version first. Run the full suite after
the fix.

### Pattern C: Drift from the source of truth

Signs:
- You are extracting or generating facts from a requirements document (FRD, STTM, spec).
- The output contains plausible values the document may not support: keys, conflicts,
  scopes, discriminators, layer names.
- The run has been long and unsupervised.

What to do: every extracted fact gets a citation (document, section or table, and the
short source text). Anything that cannot be cited is marked UNVERIFIED rather than filled
in. If the source says "None", the output says "None". Before reporting, re-check each
claim against the document, not against your earlier output.

### Pattern D: A permission problem disguised as an engineering problem

Signs:
- You are blocked by a mail gateway, policy, missing grant, SSO, VDI restriction, or
  firewall.
- You are on your second workaround.

What to do: stop engineering. Draft a short question for the person who owns the
constraint: what we are trying to do, what is blocked, and what the sanctioned path is.
Do not keep routing around security controls. In client environments those workarounds
can be compliance violations, not just wasted time.

## Step 2: Report before continuing

Use this format:

```
SPIRAL CHECK
Symptom:            <one line>
Attempts so far:    <one line each: what changed, what happened>
Pattern:            <A/B/C/D, and why>
Next action:        <the observation, test, citation pass, or question>
Would disprove it:  <what result would mean this diagnosis is wrong>
```

If the user is present, wait for their go-ahead. If running unattended, perform only the
diagnostic action (observe, write the failing test, run the citation pass, draft the
question) and log the check. Do not resume fix attempts until the diagnostic action has
produced new information.

## Step 3: Log it

Once the problem is resolved, append an entry to `docs/spiral-log.md` (create it if
missing):

```
## <date>: <short symptom>
- Actual cause:
- Pattern:
- Caught by skill: yes | no (noticed afterward) | false trigger
- Earliest signal that would have revealed it:
- Approx. time lost:
- Permanent fix (config, test, assertion), if any:
```

The log is the long-term payoff. When the same cause shows up twice, it needs a permanent
fix, not a faster rediscovery.

After logging:
- If the cause isn't already in references/known-causes.md, append an entry.
  If it is, add the date to its Seen line.
- Append a replay scenario for this spiral to evals/scenarios.json (format in that
  file).
- Do not edit this SKILL.md. Changes to the core (patterns, steps, description) go
  only through /spiral-retro, with replay results and the user's approval.
