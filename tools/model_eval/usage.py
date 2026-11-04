"""Token mix + DBU estimate from local Claude Code transcripts (counts only, no content)."""
import glob, json, os, sys, collections

ROOT = "/app/python/source_code/.claude/projects"
# DBU per 1M tokens, databricks.com proprietary FM serving page (2026-11-03)
RATES = {  # input, output, cache_read, cache_write_5m, cache_write_1h
    "opus":   (57.143, 285.714, 2.857, 71.429, 114.286),
    "sonnet": (28.571, 142.857, 1.429, 35.714, 57.143),
    "haiku":  (1.429, 7.143, 0.143, 1.786, 2.857),
}
fam = lambda m: next((k for k in RATES if k in (m or "")), None)

seen = set()
tot = collections.defaultdict(lambda: collections.Counter())
files = glob.glob(f"{ROOT}/**/*.jsonl", recursive=True)
gaps = []  # seconds between consecutive main-session requests
for f in files:
    last_ts = None
    for line in open(f, errors="ignore"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        m = e.get("message") or {}
        u = m.get("usage")
        if e.get("type") != "assistant" or not u:
            continue
        key = (m.get("id"), e.get("requestId"))
        if key in seen:
            continue
        seen.add(key)
        k = fam(m.get("model"))
        if not k:
            continue
        c = tot[(k, "subagent" if "/subagents/" in f or e.get("isSidechain") else "main")]
        cc = u.get("cache_creation") or {}
        w1h = cc.get("ephemeral_1h_input_tokens", 0) or 0
        w5 = (u.get("cache_creation_input_tokens", 0) or 0) - w1h
        c.update(req=1, inp=u.get("input_tokens", 0) or 0, out=u.get("output_tokens", 0) or 0,
                 cr=u.get("cache_read_input_tokens", 0) or 0, w5=w5, w1h=w1h)
        ts = e.get("timestamp")
        if ts and "/subagents/" not in f:
            from datetime import datetime
            t = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            if last_ts:
                gaps.append(t - last_ts)
            last_ts = t

print(f"transcript files: {len(files)}")
grand = 0
for (k, who), c in sorted(tot.items()):
    r = RATES[k]
    parts = {"input": c["inp"] * r[0], "output": c["out"] * r[1], "cache_read": c["cr"] * r[2],
             "cache_write_5m": c["w5"] * r[3], "cache_write_1h": c["w1h"] * r[4]}
    dbu = sum(parts.values()) / 1e6
    grand += dbu
    print(f"\n{k}/{who}: requests={c['req']}  DBU={dbu:.1f}")
    print(f"  tokens  input={c['inp']:,} output={c['out']:,} cache_read={c['cr']:,} "
          f"write5m={c['w5']:,} write1h={c['w1h']:,}")
    print("  DBU share  " + "  ".join(f"{n}={v/1e6/dbu*100:.0f}%" for n, v in parts.items() if dbu))
    tin = c["inp"] + c["cr"] + c["w5"] + c["w1h"]
    if tin:
        print(f"  cache hit rate (read / all input) = {c['cr']/tin*100:.1f}%   "
              f"avg context per request = {tin/c['req']:,.0f} tokens")
print(f"\nTOTAL DBU = {grand:.1f}")
if gaps:
    b = collections.Counter("<5m" if g < 300 else "5-60m" if g < 3600 else ">60m" for g in gaps)
    print("gaps between main requests:", dict(b))
