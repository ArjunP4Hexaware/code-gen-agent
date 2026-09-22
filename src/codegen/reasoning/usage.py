"""What a run actually did with a model, per stage — and the ONE label for it.

Every user-facing provider label (the UI badge and run panel, the API
payloads, the generation report, the CLI line) renders from a
``StageUsage`` built AFTER the stage ran, never from static copy:

* the stage had nothing for a model (``requests == 0``)
    -> "Resolved from the documents (no model call needed)"
* a mock provider answered (a lock, a fallback, a dry-run, a test)
    -> "Mock provider (reason: <why>)"
* a live provider answered
    -> "Claude Opus 5 (databricks-claude-opus-5) · N call(s)"

``calls`` counts model round-trips actually sent (schema-validation retries
included); a mock never sends one. ``mock_reason`` is set on every mock the
builders construct (``codegen.reasoning.providers.build_provider``,
``codegen.layout.model.build_layout_provider``); a mock constructed directly
reads ``"test"``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields

NO_CALL_NEEDED = "Resolved from the documents (no model call needed)"
MOCK_REASON_DEFAULT = "test"
# The live providers' names; anything else that answered is not a model.
LIVE_PROVIDERS = ("databricks_fmapi", "anthropic")


def model_display_name(model: str | None) -> str:
    """``claude-opus-5`` -> ``Claude Opus 5``; ``claude-opus-4-8`` ->
    ``Claude Opus 4.8``. Anything else is shown as written."""
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
    mock_reason: str | None = None   # why a mock answered (set iff provider == mock)
    recorded_provider: str | None = None   # replay: who produced the recorded set

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
        if self.provider == "mock":
            return f"Mock provider (reason: {self.mock_reason or MOCK_REASON_DEFAULT})"
        label = (f"{model_display_name(self.model)} ({self.endpoint or self.model}) · "
                 f"{self.calls} call(s)")
        return f"{label}, {self.failed} failed" if self.failed else label

    def as_dict(self) -> dict:
        data = asdict(self)
        data["label"] = self.label
        data["forced_mock"] = self.forced_mock
        return data

    @classmethod
    def from_dict(cls, data: dict) -> StageUsage:
        return cls(**{f.name: data[f.name] for f in fields(cls) if f.name in data})


def usage_from_provider(stage: str, provider, *, requests: int, failed: int = 0,
                        calls: int | None = None) -> StageUsage:
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
        mock_reason=(getattr(provider, "mock_reason", None) or MOCK_REASON_DEFAULT)
        if is_mock and provider is not None else None,
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
        mock_reason="; ".join(reasons) or None,
        recorded_provider=first.recorded_provider,
    )


def layer2_usage(provider, candidates) -> StageUsage:
    """Layer 2's record for one feed: one request per unmapped rule the
    provider was asked about (review items of other kinds are not requests)."""
    asked = [c for c in candidates if getattr(c, "kind", "layer2") == "layer2"]
    failed = sum(1 for c in asked if c.response is None)
    return usage_from_provider("layer2", provider, requests=len(asked), failed=failed)


def layout_usage(*providers) -> StageUsage:
    """The layout recognizer's record: every provider it built this run (the
    resolver's, plus any dialog-advice one). A request is a layout / advice
    request actually put to the provider — cache and synonym hits put none."""
    usages = [usage_from_provider("layout", p, requests=len(getattr(p, "requests", [])))
              for p in providers if p is not None]
    return merge("layout", usages)


def report_lines(usages: list[StageUsage]) -> list[str]:
    """The generation report's "Model usage" section."""
    titles = {"layout": "Layout recognizer", "layer2": "Layer 2 (rule reasoning)"}
    lines = ["## Model usage", ""]
    lines += [f"- {titles.get(u.stage, u.stage)}: {u.label}" for u in usages]
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
    "NO_CALL_NEEDED",
    "StageUsage",
    "layer2_usage",
    "merge",
    "model_display_name",
    "replay_usage",
    "run_usage",
    "usage_from_provider",
]
