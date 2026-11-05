"""Split AGENTS.md: keep rules, move reference sections into a project skill.
Usage: python3 -I make_split.py <repo-or-worktree-dir>   (rewrites AGENTS.md, writes the skill)"""
import re, sys
from pathlib import Path

MOVE = ["How a run works", "Config doctrine", "Output modes and artefacts",
        "Edge seams (network stays at the edges)", "The App", "Known gaps"]
SKILL_DIR = ".claude/skills/codegen-reference"

root = Path(sys.argv[1])
text = (root / "AGENTS.md").read_text(encoding="utf-8")
# split on level-2 headings that start a line outside code fences
parts, cur, fence = [], [], False
for line in text.splitlines(keepends=True):
    if line.startswith("```"):
        fence = not fence
    if not fence and line.startswith("## "):
        parts.append("".join(cur)); cur = []
    cur.append(line)
parts.append("".join(cur))
head, sections = parts[0], parts[1:]
title = lambda s: s.splitlines()[0][3:].strip()
keep = [s for s in sections if title(s) not in MOVE]
moved = [s for s in sections if title(s) in MOVE]
assert len(moved) == len(MOVE), [title(s) for s in moved]

pointer = f"""## Reference (moved out of this file to keep it short)

Six reference sections live in `{SKILL_DIR}/SKILL.md` (Claude Code loads it as the
`codegen-reference` skill; any other agent reads the file): **How a run works**
(inputs, layout recognition, extraction rules, gap fill, answers, verdicts and outcomes,
error-line tiers, Layer 2, the one generate entry point), **Config doctrine** (knobs,
overlays, state root, the provider switch), **Output modes and artefacts** (framework /
notebook, conventions profiles, DDL rules, IIG templates, scoring, gate flags), **Edge
seams**, **The App**, **Known gaps**. They are rules too, not background: read the
matching section BEFORE changing anything under `src/codegen/`, `config/`, `ui/`, a
generated artefact, or answering how a run behaves.

"""
# put the pointer right after "Rules that never bend"
out, placed = [head], False
for s in keep:
    out.append(s)
    if title(s) == "Rules that never bend":
        out.append(pointer); placed = True
assert placed
(root / "AGENTS.md").write_text("".join(out), encoding="utf-8")

skill = f"""---
name: codegen-reference
description: The code-gen-agent repo's reference rules moved out of AGENTS.md - how a run works (extraction, layout, gap fill, answers, verdicts, error tiers, Layer 2, the one generate entry point), config doctrine, output modes and artefacts (DDL / IIG / notebook rules, conventions profiles, gate flags), edge seams, the App, known gaps. Read before changing src/codegen, config, ui, generated artefacts, or explaining run behaviour.
---

# code-gen-agent reference (moved from AGENTS.md; same authority as AGENTS.md)

""" + "".join(s.replace("## ", "## ", 1) for s in moved)
d = root / SKILL_DIR
d.mkdir(parents=True, exist_ok=True)
(d / "SKILL.md").write_text(skill, encoding="utf-8")
print(f"AGENTS.md {len(text)} -> {len(''.join(out))} chars; skill {len(skill)} chars")
