# Model comparisons for this repo's work (other vendors vs Opus 5.5)

Why this file: the 2026-11-19 GPT-6.2 Astra assessment lived only in a chat and was lost
on a container reset (one line survived in `docs/CLAUDE_HISTORY.md` §[H29]). Every
comparison goes here from now on, newest first, with its sources.

Standing rules that frame any switch (AGENTS.md): **Anthropic is the sole model vendor**
(a change is Soham's call, and likely ACFC's); compare models by **cost per ACCEPTED
task**, never per token - the real test is a replay through `tools/model_eval/` on this
repo's tasks (2026-11-03: Opus 5.5 medium 4/4 mergeable vs Haiku 5.5 xhigh 1/4), and
running another vendor's model on the repo sends repo code to that vendor (part of the
vendor decision).

## 2026-11-20 — Gemini 4 Neon (Google, released 2026-11-18) vs Claude Opus 5.5

**Verdict: stay on Opus 5.5.** A tie on coding; Neon is cheaper per coding task and far
better calibrated (hallucination), but the vendor rule blocks it. If the rule ever opens,
Neon is the one to put through a `tools/model_eval/` replay.

| What matters for us | Gemini 4 Neon | Opus 5.5 | Who ran it |
|---|---|---|---|
| AA Coding Agent Index | 59 (xhigh, Google's Antigravity CLI) | 58 (max, Claude Code) | Artificial Analysis |
| Terminal-Bench 4.1 | 65.2% | 65.8% | leaderboard |
| FrontierCode 2.0 | 46.2% (high) | 47.3% | Cognition leaderboard |
| CursorBench 4.1 | 65.4% | 58.1% | Cursor |
| SWE-sweep | 12.8% mini-SWE / 39.0% Antigravity | 3.6% mini-SWE / 10.1% Claude Code | Google |
| Cost per coding-agent task | $6.86 | $12.61 | Artificial Analysis |
| Price per 1M tokens (in / out / cache read) | $3 / $15 / $0.15 | $4 / $20 / $0.20 | list prices |
| AA-Omniscience hallucination rate (lower = better) | 13.9% (high, the default) | ~50% (aggregator figure, see caveats) | Artificial Analysis |
| Long context, GraphWalks 256k-1M | 95.2% | 66.8% | Google |
| AA Intelligence Index v5.0.1 | 61.4 (xhigh) / 59.6 (high, default) | 59 | Artificial Analysis |
| Context window | 1M | — | — |

What it means here:
- **Coding sessions on this repo:** a tie in quality (Neon ahead on CursorBench, Opus a
  hair ahead on the two independent coding boards), Neon about half the cost per task.
- **Hallucination** is Neon's real edge: when it does not know, it commits to a wrong
  answer about 1 time in 7 vs about 1 in 2 for Opus (GPT-6.2 Astra medium: 54.1% on the
  same snapshot). For the PRODUCT the risk is designed out (two-layer trust: a model never
  writes a value - Layer 1 is code, Layer 2 is off, the layout model answers a line
  number a validator checks); it matters for an assistant's claims while working on code.
- **Speed:** ~110 vs ~57 output tokens/s (Neon vs Gemini 4 Carbon), but Neon is among
  the most verbose models measured (93rd of 95 on output tokens).

Caveats:
- Two days old at the time of writing; no independent hands-on review yet.
- Google's model-card table is Google's own runs, mostly at xhigh; competitors' figures
  are self-reported. Neon's score moves a lot by thinking level (17 index points from low
  to xhigh).
- The harness matters as much as the model: SWE-sweep triples in Google's own tool.
- The Opus 5.5 hallucination figure (50.3%) is carried by an aggregator (BenchLM); Opus
  5.5 was not on the AA-Omniscience v1.1 snapshot read, so it may be an older version.

Sources: [Gemini 4 Neon model card](https://deepmind.google/models/model-cards/gemini-4-neon/) ·
[Google's announcement](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/) ·
[Artificial Analysis on Neon](https://artificialanalysis.ai/articles/gemini-4-neon-intelligence-gain) ·
[OrcaRouter, independent numbers](https://www.orcarouter.ai/blog/gemini-4-neon-benchmark-independent) ·
[AA-Omniscience v1.1 snapshot 2026-11-18](https://atlas.village.dev/benchmarks/aa-omniscience-v1-1-hallucination-rate-artificial-analysis) ·
[Ofox on Gemini 4 hallucination rates](https://ofox.ai/blog/gemini-4-hallucination-rates/) ·
[Introducing Claude Opus 5.5](https://www.anthropic.com/claude-opus-5-5) ·
[BenchLM, Opus 5.5](https://benchlm.ai/models/claude-opus-5-5) ·
[VentureBeat on pricing](https://venturebeat.com/technology/google-launches-gemini-4-neon-with-opus-5-5-level-coding-performance-at-25-lower-api-token-prices)

## 2026-11-19 — GPT-6.2 Astra (OpenAI) vs Claude Opus 5.5 (summary only - the full write-up was lost)

**Verdict: stay on Opus 5.5.** What survived (`docs/CLAUDE_HISTORY.md` §[H29]): the vendor
rule; hallucination "59% vs 50%" (on the 2026-11-18 AA-Omniscience v1.1 snapshot GPT-6.2
Astra at medium reads 54.1% - the 59% was likely another setting or version); the
coding / maintenance benchmarks favoured Opus. Rebuild it here from public benchmarks if
it is needed again.
