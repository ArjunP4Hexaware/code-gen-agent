"""What a run actually did with a model, per stage — and the ONE label for it.

Every user-facing provider label (the UI badge and run panel, the API
payloads, the generation report, the CLI line) renders from a
``StageUsage`` built AFTER the stage ran, never from static copy:

* the stage had nothing for a model (``requests == 0``)
    -> "Resolved from the documents (no model call needed)"
* a mock provider answered (a lock, a fallback, a dry-run, a test)
    -> "Mock provider (reason: <why>)"
* a live provider answered
    -> "Claude Opus 5.5 (databricks-claude-opus-5-5) · N call(s)"

``calls`` counts model round-trips actually sent (schema-validation retries
included); a mock never sends one. ``mock_reason`` is set on every mock the
builders construct (``codegen.reasoning.providers.build_provider``,
``codegen.layout.model.build_layout_provider``); a mock constructed directly
reads ``"test"``.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, fields

NO_CALL_NEEDED = "Resolved from the documents (no model call needed)"
MOCK_REASON_DEFAULT = "test"
# The live providers' names; anything else that answered is not a model.
LIVE_PROVIDERS = ("databricks_fmapi", "anthropic")
# post76: Layer 2 is its own stage after emit (codegen.layer2_stage) — until it
# runs, a feed's record says where its rules are (never a call count).
NOT_RUN_LABELS = {
    "pending": "Not run yet: the Layer-2 stage runs after the run's outcome is written "
               "({n} rule(s))",
    "deferred": "Deferred (--layer2 defer): {n} rule(s), review candidates: pending; "
                "no model call",
    "skipped": "Skipped (--layer2 skip): {n} rule(s) left unmapped for review; no model call",
}


def model_display_name(model: str | None) -> str:
    """``claude-opus-5-5`` -> ``Claude Opus 5.5``; ``claude-opus-5`` ->
    ``Claude Opus 5``. Anything else is shown as written."""
    if not model:
        return "model (unnamed)"
    parts = model.split("-")
    if parts[0].lower() != "claude" or len(parts) < 2:
        return model
    words = [p for p in parts[1:] if not p.isdigit()]
    digits = [p for p in parts[1:] if p.isdigit()]
    name = " ".join(["Claude", *(w.capitalize() for w in words)])
    return f"{name} {'.'.join(digits)}" if digits else name


@dataclass(frozen=True)
class StageUsage:
    stage: str                       # "layout" | "layer2"
    provider: str                    # databricks_fmapi | anthropic | mock | replay | none
    endpoint: str | None = None
    model: str | None = None
    calls: int = 0                   # model round-trips actually sent
    requests: int = 0                # work items the stage put to a provider
    failed: int = 0                  # requests whose provider raised
    recovered: int = 0               # requests answered after a failed attempt
    mock_reason: str | None = None   # why a mock answered (set iff provider == mock)
    recorded_provider: str | None = None   # replay: who produced the recorded set
    # D1 post51 pair_03 (109 s vs ~10 s): wall-clock seconds the live calls
    # took, retries included — which stage the time went to.
    seconds: float = 0.0
    # post67: tokens the live calls reported, summed per call (the App's
    # measured cost reads them; never part of the label). input excludes
    # cache reads, as the Anthropic API counts them.
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def forced_mock(self) -> bool:
        """True when a mock answered work that a model would otherwise have done."""
        return self.provider == "mock" and self.requests > 0

    @property
    def label(self) -> str:
        if self.provider == "replay":
            return (f"Replayed recorded candidates (recorded provider: "
                    f"{self.recorded_provider or 'unknown'}) · 0 new call(s)")
        if self.requests == 0:
            return NO_CALL_NEEDED
        if self.provider in NOT_RUN_LABELS:
            return NOT_RUN_LABELS[self.provider].format(n=self.requests)
        if self.provider == "mock":
            return f"Mock provider (reason: {self.mock_reason or MOCK_REASON_DEFAULT})"
        label = (f"{model_display_name(self.model)} ({self.endpoint or self.model}) · "
                 f"{self.calls} call(s)")
        if self.seconds:
            label += f" in {self.seconds:.1f}s"
        if self.failed:
            label += f", {self.failed} failed"
        if self.recovered:
            label += f", {self.recovered} answered on retry"
        return label

    @property
    def all_failed(self) -> bool:
        """A live stage where every request failed (2026-10-14: said in the
        report header, not only in the flags)."""
        return (self.provider in LIVE_PROVIDERS and self.requests > 0
                and self.failed == self.requests)

    def as_dict(self) -> dict:
        data = asdict(self)
        data["label"] = self.label
        data["forced_mock"] = self.forced_mock
        return data

    @classmethod
    def from_dict(cls, data: dict) -> StageUsage:
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})


def usage_from_provider(stage: str, provider, *, requests: int, failed: int = 0,
                        calls: int | None = None, recovered: int = 0) -> StageUsage:
    """Read what a provider instance did. ``calls`` overrides the provider's
    own counter (a provider reused across stages)."""
    name = getattr(provider, "name", "none") if provider is not None else "none"
    is_mock = name not in LIVE_PROVIDERS
    return StageUsage(
        stage=stage,
        provider="mock" if is_mock and provider is not None else name,
        endpoint=None if is_mock else getattr(provider, "endpoint", None),
        model=None if is_mock else getattr(provider, "model", None),
        calls=0 if is_mock else (calls if calls is not None
                                 else int(getattr(provider, "calls", 0))),
        requests=requests,
        failed=failed,
        recovered=0 if is_mock else recovered,
        mock_reason=(getattr(provider, "mock_reason", None) or MOCK_REASON_DEFAULT)
        if is_mock and provider is not None else None,
        seconds=0.0 if is_mock else round(float(getattr(provider, "seconds", 0.0) or 0.0), 1),
        input_tokens=0 if is_mock else int(getattr(provider, "input_tokens", 0) or 0),
        output_tokens=0 if is_mock else int(getattr(provider, "output_tokens", 0) or 0),
        cache_read_tokens=0 if is_mock else int(getattr(provider, "cache_read_tokens", 0) or 0),
    )


def merge(stage: str, usages: list[StageUsage]) -> StageUsage:
    """One record for a stage that ran several times (Layer 2 once per feed).
    Providers that did work win over ones that had nothing to do."""
    if not usages:
        return StageUsage(stage=stage, provider="none")
    worked = [u for u in usages if u.requests] or usages
    first = worked[0]
    providers = list(dict.fromkeys(u.provider for u in worked))
    reasons = list(dict.fromkeys(u.mock_reason for u in worked if u.mock_reason))
    return StageUsage(
        stage=stage,
        provider=providers[0] if len(providers) == 1 else "+".join(providers),
        endpoint=first.endpoint,
        model=first.model,
        calls=sum(u.calls for u in usages),
        requests=sum(u.requests for u in usages),
        failed=sum(u.failed for u in usages),
        recovered=sum(u.recovered for u in usages),
        mock_reason="; ".join(reasons) or None,
        recorded_provider=first.recorded_provider,
        seconds=round(sum(u.seconds for u in usages), 1),
        input_tokens=sum(u.input_tokens for u in usages),
        output_tokens=sum(u.output_tokens for u in usages),
        cache_read_tokens=sum(u.cache_read_tokens for u in usages),
    )


def timed(owner, send):
    """``send`` with its wall-clock time added to ``owner.seconds`` (every
    live provider's round-trip; what StageUsage.seconds reads)."""
    def wrapped(*args, **kwargs):
        start = time.perf_counter()
        try:
            return send(*args, **kwargs)
        finally:
            owner.seconds = getattr(owner, "seconds", 0.0) + time.perf_counter() - start
    return wrapped


TOKEN_FIELDS = ("input_tokens", "output_tokens", "cache_read_tokens")


def add_tokens(owner, counts: dict) -> None:
    """Add one call's token counts (``TOKEN_FIELDS``) to ``owner``'s running
    totals (what StageUsage reads)."""
    for name in TOKEN_FIELDS:
        setattr(owner, name, getattr(owner, name, 0) + int(counts.get(name) or 0))


def message_tokens(message) -> dict:
    """An Anthropic-API message's ``usage`` (input_tokens / output_tokens /
    cache_read_input_tokens) in ``add_tokens``' shape."""
    counts = getattr(message, "usage", None)
    return {"input_tokens": getattr(counts, "input_tokens", 0) or 0,
            "output_tokens": getattr(counts, "output_tokens", 0) or 0,
            "cache_read_tokens": getattr(counts, "cache_read_input_tokens", 0) or 0}


def completion_tokens(response) -> dict:
    """An FM API (chat-completions shape) response's ``usage`` — prompt_tokens
    / completion_tokens, cached prompt tokens from ``prompt_tokens_details``
    when the endpoint reports them — in ``add_tokens``' shape."""
    counts = getattr(response, "usage", None)
    prompt = int(getattr(counts, "prompt_tokens", 0) or 0)
    details = getattr(counts, "prompt_tokens_details", None)
    cached = int((details.get("cached_tokens") if isinstance(details, dict)
                  else getattr(details, "cached_tokens", 0)) or 0)
    return {"input_tokens": max(prompt - cached, 0),
            "output_tokens": int(getattr(counts, "completion_tokens", 0) or 0),
            "cache_read_tokens": cached}


def layer2_usage(provider, candidates) -> StageUsage:
    """Layer 2's record for one feed: one request per unmapped rule the
    provider was asked about (review items of other kinds are not requests)."""
    asked = [c for c in candidates if getattr(c, "kind", "layer2") == "layer2"]
    failed = sum(1 for c in asked if c.response is None)
    # requests a failed first attempt did not lose (the retry answered)
    recovered = len({f.request for f in getattr(provider, "failures", []) if f.recovered})
    return usage_from_provider("layer2", provider, requests=len(asked), failed=failed,
                               recovered=recovered)


def not_run_usage(state: str, rules: int) -> StageUsage:
    """post76: Layer 2's record for a feed whose stage has not asked a model
    (``state`` = pending | deferred | skipped)."""
    return StageUsage(stage="layer2", provider=state, requests=rules)


def layout_usage(*providers) -> StageUsage:
    """The layout recognizer's record: every provider it built this run (the
    resolver's, plus any dialog-advice one). A request is a layout / advice
    request actually put to the provider — cache and synonym hits put none."""
    usages = [usage_from_provider("layout", p, requests=len(getattr(p, "requests", [])))
              for p in providers if p is not None]
    return merge("layout", usages)


def report_lines(usages: list[StageUsage]) -> list[str]:
    """The generation report's "Model usage" section — and which code
    produced the report (codegen.build_info.source_line: version, location,
    overlays; environment metadata, the one line that varies by checkout)."""
    from codegen.build_info import PRODUCED_BY_PREFIX, source_line

    titles = {"layout": "Layout recognizer", "layer2": "Layer 2 (rule reasoning)"}
    lines = ["## Model usage", ""]
    lines += [f"- {titles.get(u.stage, u.stage)}: {u.label}" for u in usages]
    lines.append(PRODUCED_BY_PREFIX + source_line())
    return [*lines, ""]


def run_usage(feed_usages: list[list[dict]], layout: StageUsage | None = None) -> list[dict]:
    """A whole run's record from its feeds' records: the layout stage (run
    once per run) and Layer 2 merged over every feed."""
    layer2 = [StageUsage.from_dict(u) for usages in feed_usages for u in usages
              if u.get("stage") == "layer2"]
    stages = [*([layout] if layout is not None else []), merge("layer2", layer2)]
    return [u.as_dict() for u in stages]


def replay_usage(candidates) -> StageUsage:
    asked = [c for c in candidates if getattr(c, "kind", "layer2") == "layer2"]
    recorded = sorted({c.provider for c in asked})
    return StageUsage(stage="layer2", provider="replay",
                      requests=len(asked), recorded_provider=", ".join(recorded) or None)


__all__ = [
    "LIVE_PROVIDERS",
    "NOT_RUN_LABELS",
    "NO_CALL_NEEDED",
    "StageUsage",
    "TOKEN_FIELDS",
    "add_tokens",
    "completion_tokens",
    "layer2_usage",
    "merge",
    "message_tokens",
    "model_display_name",
    "not_run_usage",
    "replay_usage",
    "run_usage",
    "timed",
    "usage_from_provider",
]
